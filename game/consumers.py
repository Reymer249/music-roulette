import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.auth import get_user
from .models import Parties, UsersParties, Users
from channels.db import database_sync_to_async
from django.core.cache import cache
from .tasks import game_process


class LobbyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("connected")
        # Get user from the JWT token sent in the connection request
        self.user = await get_user(self.scope)

        self.lobby_id = self.scope["url_route"]["kwargs"]["lobby_id"]
        self.lobby_group_id = "lobby_%s" % self.lobby_id

        # get the lobby object
        self.lobby = await database_sync_to_async(lambda: Parties.objects.get(pid=self.lobby_id))()

        # add channel to a group
        await self.channel_layer.group_add(self.lobby_group_id, self.channel_name)
        await self.accept()

        # update player list for everybody in the lobby
        await self.channel_layer.group_send(self.lobby_group_id, {"type": "update_lobby_info"})
        # await self.update_lobby_info()
        print(self.user)
        print(self.lobby)
        print(self.lobby_group_id)
        print(self.lobby_id)

    async def disconnect(self, close_code):
        # delete the user-lobby connection records
        await self.channel_layer.group_discard(self.lobby_group_id, self.channel_name)
        await database_sync_to_async(lambda: UsersParties.objects.filter(user=self.user).delete())()

        await self.channel_layer.group_send(self.lobby_group_id, {"type": "update_lobby_info"})

        # count players left in the lobby
        players_left = await database_sync_to_async(
            lambda: UsersParties.objects.filter(party_id=self.lobby_id).count()
        )()
        # if no players left - delete the lobby
        if not players_left:
            await database_sync_to_async(lambda: Parties.objects.get(pid=self.lobby_id).delete())()


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
                    game_process.delay(self.lobby_id, self.lobby_group_id)
            case "answer":
                # cache the answer
                cache.set(f"lobby_{self.lobby_id}_user_{self.user.id}_answer", text_data_json["answer"])

    async def get_usernames(self):
        # a function to get all the usernames of the players in the group
        user_parties = await database_sync_to_async(
            lambda: UsersParties.objects.filter(party_id=self.lobby_id)
        )()
        usernames = await database_sync_to_async(
            lambda: Users.objects.filter(
                id__in=[up.user_id.id for up in user_parties]
            ).values_list('username', flat=True)
        )()
        return await database_sync_to_async(lambda: list(usernames))()

    async def update_lobby_info(self, event):
        # send the user the updated user list
        username_list = await self.get_usernames()
        await self.send(text_data=json.dumps({"type": "update_lobby_info", "message": username_list}))
    
    async def chat_message(self, event):
        message = event["message"]
        print(message)

        await self.send(text_data=json.dumps({"type": "chat", "message": message}))

    async def new_round(self, event):
        # received new_round command - forwarding to the user
        await self.send(text_data=json.dumps(
            {"type": "new_round",
             "round_num": event["round_num"],
             "question_time": event["question_time"]},
        ))
