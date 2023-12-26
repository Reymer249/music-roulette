import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.auth import get_user
from .models import Parties, UsersParties, Users
from channels.db import database_sync_to_async
from django.core.cache import cache
from .tasks import game_process


class LobbyConsumer(AsyncWebsocketConsumer):
    """
    This is the consumer for the lobby. It handles the websocket connections for the lobby page.
    It manages the connections of the users, sends updates to the lobby when a user connects or disconnects,
    and forwards chat messages to all users in the lobby.

    Attributes:
        user: The user who is connected to the websocket.
        lobby_id: The id of the lobby.
        lobby_group_id: The group id of the lobby, used for sending messages to all users in the lobby.
        game_group_id: The group id of the game, used for sending messages to all users in the game.
        lobby: The lobby object.
        game_started: A boolean indicating whether the game has started or not.
    """
    async def connect(self):
        """
        This is an asynchronous method that is called when the WebSocket is handshaking as part of the connection process.

        It initializes the user, lobby_id, lobby_group_id, game_group_id, lobby, and game_started attributes.
        It also adds the channel to a group, accepts the WebSocket connection, and sends an update to the lobby.

        Raises:
            ChannelsFull: If the maximum amount of channels for the group has been exceeded.
            StopConsumer: If the connection should be closed and the consumer instance should be discarded.
        """
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
        """
        This is an asynchronous method that is called when the WebSocket is disconnecting.

        It removes the channel from the group, deletes the user-lobby connection records if the game has not started,
        updates the player list for everyone in the lobby, and deletes the lobby if no players are left.

        Args:
            close_code (int): An integer that represents the status code indicating why the connection is being closed.

        Raises:
            ChannelsFull: If the maximum amount of channels for the group has been exceeded.
            StopConsumer: If the connection should be closed and the consumer instance should be discarded.
        """
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
        """
        This is an asynchronous method that is called when the WebSocket receives a message.

        It parses the received data and determines the type of the message. Depending on the message type,
        it either forwards a chat message to the group, starts the game if the user is an admin in the lobby,
        or updates the lobby info.

        Args:
            text_data (str): A string that represents the received message.
            **kwargs: Arbitrary keyword arguments.

        Raises:
            ChannelsFull: If the maximum amount of channels for the group has been exceeded.
            StopConsumer: If the connection should be closed and the consumer instance should be discarded.
        """
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
        """
        This is an asynchronous method that updates the lobby information.

        It retrieves the list of players in the lobby and their respective levels. This information is then sent to the user.

        Args:
            event: An event that triggers the update of the lobby information.

        """
        # get all the names of the players in the group
        user_parties = await database_sync_to_async(
            lambda: UsersParties.objects.filter(party_id=self.lobby_id)
        )()
        players = await database_sync_to_async(
            lambda: list(Users.objects.filter(
                id__in=[up.user_id for up in user_parties]
            ).values_list('name', 'level'))
        )()
        names = [{"name": p[0], "level": p[1]} for p in players]

        # send the user the updated user list
        await self.send(text_data=json.dumps({"type": "update_lobby_info", "player_names": names}))

    async def chat_message(self, event):
        """
        This is an asynchronous method that handles chat messages.

        It receives an event containing a chat message. The message is then printed to the console and sent back to the client.

        Args:
            event: An event that contains the chat message.
        """
        message = event["message"]
        print(f"chat: {message}")
        await self.send(text_data=json.dumps({"type": "chat", "message": message}))

    async def start_game(self, event):
        """
        This is an asynchronous method that starts the game.

        It sets the game_started attribute to True and sends a start_game message to the client.

        Args:
            event: An event that triggers the start of the game.
        """
        self.game_started = True
        await self.send(text_data=json.dumps({"type": "start_game"}))


class GameConsumer(AsyncWebsocketConsumer):
    """
    This is the main consumer for the game. It handles the WebSocket connections for the game.

    Attributes:
        user: The user who is connected to the WebSocket.
        lobby_id: The ID of the lobby that the user is in.
        game_group_id: The ID of the game group that the user is in.
        lobby: The lobby object that the user is in.
        game_started: A boolean indicating whether the game has started or not.

    Methods:
        connect: Initializes the user, lobby_id, game_group_id, and lobby attributes. Adds the channel to a group and accepts the WebSocket connection.
        disconnect: Removes the channel from the group and deletes the user-lobby connection records unless the game has started.
        receive: Handles the received data and performs actions based on the type of the message.
        init: Sends an init message to the client with the player IDs, names, levels, and round number.
        start_countdown: Sends a start_countdown message to the client.
        new_round: To be implemented.
    """
    async def connect(self):
        """
        This is an asynchronous method that handles the connection of a new user.

        It retrieves the user from the JWT token sent in the connection request, assigns the lobby_id and game_group_id based on the URL route,
        retrieves the lobby object associated with the lobby_id, adds the channel to a group, and accepts the WebSocket connection.

        Raises:
            ChannelsFull: If the maximum amount of channels for the group has been exceeded.
            StopConsumer: If the connection should be closed and the consumer instance should be discarded.
        """
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
        """
        This is an asynchronous method that handles the disconnection of a user.

        It removes the channel from the group and deletes the user-lobby connection records unless the game has started.

        Args:
            close_code (int): An integer that represents the status code indicating why the connection is being closed.

        Raises:
            ChannelsFull: If the maximum amount of channels for the group has been exceeded.
            StopConsumer: If the connection should be closed and the consumer instance should be discarded.
        """
        # remove this channel from the group
        await self.channel_layer.group_discard(self.game_group_id, self.channel_name)

    async def receive(self, text_data=None, **kwargs):
        """
        This is an asynchronous method that handles the reception of data from the client.

        It parses the received data and performs actions based on the type of the message. The message type can be "answer" or "ready".
        If the message type is "answer", it caches the answer. If the message type is "ready", it sets the user's status to ready.

        Args:
            text_data (str): A string that represents the received message.
            **kwargs: Arbitrary keyword arguments.

        Raises:
            ChannelsFull: If the maximum amount of channels for the group has been exceeded.
            StopConsumer: If the connection should be closed and the consumer instance should be discarded.
        """
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
        """
        This is an asynchronous method that initializes the game.

        It retrieves the player IDs, player names, round number, and player levels from the event argument.
        Then, it sends this information to the client in a JSON format.

        Args:
            event (dict): A dictionary that contains the player IDs, player names, round number, and player levels.

        Raises:
            ChannelsFull: If the maximum amount of channels for the group has been exceeded.
            StopConsumer: If the connection should be closed and the consumer instance should be discarded.
        """
        player_ids = event["player_ids"]
        player_names = event["player_names"]
        round_num = event["round_num"]
        player_levels = event["player_levels"]
        await self.send(text_data=json.dumps({"type": "init",
                                              "round_num": round_num,
                                              "player_ids": player_ids,
                                              "player_names": player_names,
                                              "player_levels": player_levels}))

    async def start_countdown(self, event):
        """
        This is an asynchronous method that starts the countdown for the game.

        It takes an event as an argument and sends a message to the client to start the countdown.

        Args:
            event (dict): A dictionary that contains the event details.

        Raises:
            ChannelsFull: If the maximum amount of channels for the group has been exceeded.
            StopConsumer: If the connection should be closed and the consumer instance should be discarded.
        """
        await self.send(text_data=json.dumps({"type": "start_countdown"}))

    async def new_round(self, event):
        """
        This is an asynchronous method that initiates a new round in the game.

        It retrieves the question time, answer time, and Spotify link from the event argument.
        Then, it sends this information to the client in a JSON format.

        Args:
            event (dict): A dictionary that contains the question time, answer time, and Spotify link.

        Raises:
            ChannelsFull: If the maximum amount of channels for the group has been exceeded.
            StopConsumer: If the connection should be closed and the consumer instance should be discarded.
        """
        question_time = event["question_time"]
        answer_time = event["answer_time"]
        spotify_link = event["spotify_link"]
        await self.send(text_data=json.dumps({"type": "new_round",
                                              "question_time": question_time,
                                              "answer_time": answer_time,
                                              "spotify_link": spotify_link}))

    async def correct_ans(self, event):
        """
        This is an asynchronous method that sends the correct answer to the client.

        It retrieves the correct answer from the event argument and sends this information to the client in a JSON format.

        Args:
            event (dict): A dictionary that contains the correct answer.

        Raises:
            ChannelsFull: If the maximum amount of channels for the group has been exceeded.
            StopConsumer: If the connection should be closed and the consumer instance should be discarded.
        """
        answer = event["correct_ans"]
        await self.send(text_data=json.dumps({"type": "correct_ans", "correct_ans": answer}))

    async def game_results(self, event):
        """
        This is an asynchronous method that sends the game results to the client.

        It retrieves the game results from the event argument and sends this information to the client in a JSON format.

        Args:
            event (dict): A dictionary that contains the game results.

        Raises:
            ChannelsFull: If the maximum amount of channels for the group has been exceeded.
            StopConsumer: If the connection should be closed and the consumer instance should be discarded.
        """
        await self.send(text_data=json.dumps({"type": "game_results"}))
