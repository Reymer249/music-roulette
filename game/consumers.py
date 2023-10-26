import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.auth import get_user
from channels.layers import get_channel_layer


class LobbyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.lobby_id = self.scope["url_route"]["kwargs"]["lobby_id"]
        self.lobby_group_id = "lobby_%s" % self.lobby_id

        # Get user from the JWT token sent in the connection request
        self.user = await get_user(self.scope)

        await self.channel_layer.group_add(self.lobby_group_id, self.channel_name)
        await self.accept()

        # await self.update_lobby_info()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.lobby_group_id, self.channel_name)

    async def receive(self, text_data=None, **kwargs):
        text_data_json = json.loads(text_data)
        message_type = text_data_json["type"]

        match message_type:
            case "chat":
                await self.channel_layer.group_send(
                    self.lobby_group_id, {"type": "chat_message", "message": text_data_json["message"]}
                )
            case "start_game":
                pass
            case "answer":
                # # TODO: check answer, change self.scores
                #
                # if True:  # TODO: if everybody answered - show_result
                #     channels_in_group = await self.channel_layer.group_channels(self.lobby_id)
                #
                #     for channel_name in channels_in_group:
                #         await self.channel_layer.send(
                #             channel_name, {'type': 'show_result', 'user_name': True, 'scores': self.scores}
                #         )
                #
                #     # TODO: if game is not finished - next_round
                pass

    # async def start_game(self):
    #     self.score = 0

    # async def next_round(self, event):
    #     message = event["message"]
    #
    #     await self.send(text_data=json.dumps({"type": "chat", "message": message}))

    async def update_lobby_info(self):
        channel_layer = get_channel_layer()
        channels_in_group = await channel_layer.group_channels(self.lobby_id)

        username_list = [channel.user.username for channel in channels_in_group]

        for channel_name in channels_in_group:
            await self.channel_layer.send(
                channel_name, {'type': 'update_lobby_info', 'players': username_list}
            )
    
    async def chat_message(self, event):
        message = event["message"]

        await self.send(text_data=json.dumps({"type": "chat", "message": message}))
