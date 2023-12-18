import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.auth import get_user
from .models import Parties, UsersParties, Users
from channels.db import database_sync_to_async
from django.core.cache import cache
from .tasks import game_process


class LobbyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get user from the JWT token sent in the connection request
        self.user = await get_user(self.scope)

        self.lobby_id = self.scope["url_route"]["kwargs"]["lobby_id"]
        self.lobby_group_id = "lobby_%s" % self.lobby_id
        self.game_group_id = "game_%s" % self.lobby_id

        # get the lobby object
        self.lobby = await database_sync_to_async(lambda: Parties.objects.get(id=self.lobby_id))()

        self.game_started = False

        # add channel to a group
        await self.channel_layer.group_add(self.lobby_group_id, self.channel_name)
        await self.accept()

        # update player list for everybody in the lobby
        await self.channel_layer.group_send(self.lobby_group_id, {"type": "update_lobby_info"})

    async def disconnect(self, close_code):
        # remove this channel from the group
        await self.channel_layer.group_discard(self.lobby_group_id, self.channel_name)

        # delete the user-lobby connection records unless game started
        if not self.game_started:
            await database_sync_to_async(lambda: UsersParties.objects.filter(user=self.user).delete())()

            # update player list for everyone in the lobby
            await self.channel_layer.group_send(self.lobby_group_id, {"type": "update_lobby_info"})

            # count players left in the lobby
            players_left = await database_sync_to_async(
                lambda: UsersParties.objects.filter(party_id=self.lobby_id).count()
            )()
            # if no players left - delete the lobby
            if not players_left:
                await database_sync_to_async(lambda: Parties.objects.get(id=self.lobby_id).delete())()

    async def receive(self, text_data=None, **kwargs):
        # parce the received data
        text_data_json = json.loads(text_data)
        message_type = text_data_json["type"]

        match message_type:
            case "chat":
                # received a chat message - forwarding it to the group
                await self.channel_layer.group_send(
                    self.lobby_group_id, {"type": "chat_message", "message": text_data_json["message"]}
                )
            case "start_game":
                # check if the user is admin in this lobby
                if await database_sync_to_async(
                    lambda: UsersParties.objects.filter(
                        party_id=self.lobby, user_id=self.user, is_admin=True
                    ).count()
                )():
                    print("STARTING GAME")

                    # send users to the game page
                    await self.channel_layer.group_send(self.lobby_group_id, {"type": "start_game"})

                    # start the game process task in celery
                    game_process.delay(self.lobby_id, self.game_group_id)

    async def update_lobby_info(self, event):
        # get all the names of the players in the group
        user_parties = await database_sync_to_async(
            lambda: UsersParties.objects.filter(party_id=self.lobby_id)
        )()
        names = await database_sync_to_async(
            lambda: list(Users.objects.filter(
                id__in=[up.user_id for up in user_parties]
            ).values_list('name', flat=True))
        )()

        # send the user the updated user list
        await self.send(text_data=json.dumps({"type": "update_lobby_info", "player_names": names}))
    
    async def chat_message(self, event):
        message = event["message"]
        print(f"chat: {message}")
        await self.send(text_data=json.dumps({"type": "chat", "message": message}))

    async def start_game(self, event):
        self.game_started = True
        await self.send(text_data=json.dumps({"type": "start_game"}))


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get user from the JWT token sent in the connection request
        self.user = await get_user(self.scope)

        self.lobby_id = self.scope["url_route"]["kwargs"]["lobby_id"]
        self.game_group_id = "game_%s" % self.lobby_id

        # get the lobby object
        self.lobby = await database_sync_to_async(lambda: Parties.objects.get(id=self.lobby_id))()

        # add channel to a group
        await self.channel_layer.group_add(self.game_group_id, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # remove this channel from the group
        await self.channel_layer.group_discard(self.game_group_id, self.channel_name)

    async def receive(self, text_data=None, **kwargs):
        # parce the received data
        text_data_json = json.loads(text_data)
        message_type = text_data_json["type"]

        match message_type:
            case "answer":
                # cache the answer
                await database_sync_to_async(
                    lambda: cache.set(f"lobby_{self.lobby_id}_user_{self.user.id}_answer", text_data_json["answer"])
                )()
            case "ready":
                # user ready to start
                await database_sync_to_async(
                    lambda: cache.set(f"lobby_{self.lobby_id}_user_{self.user.id}_ready", True)
                )()

    async def init(self, event):
        player_ids = event["player_ids"]
        player_names = event["player_names"]
        round_num = event["round_num"]
        await self.send(text_data=json.dumps({"type": "init",
                                              "round_num": round_num,
                                              "player_ids": player_ids,
                                              "player_names": player_names}))

    async def start_countdown(self, event):
        await self.send(text_data=json.dumps({"type": "start_countdown"}))

    async def new_round(self, event):
        question_time = event["question_time"]
        answer_time = event["answer_time"]
        spotify_link = event["spotify_link"]
        await self.send(text_data=json.dumps({"type": "new_round",
                                              "question_time": question_time,
                                              "answer_time": answer_time,
                                              "spotify_link": spotify_link}))

    async def correct_ans(self, event):
        answer = event["correct_ans"]
        await self.send(text_data=json.dumps({"type": "correct_ans", "correct_ans": answer}))

    async def game_results(self, event):
        await self.send(text_data=json.dumps({"type": "game_results"}))
