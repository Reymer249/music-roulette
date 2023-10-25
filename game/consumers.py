import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from urllib.parse import urlparse, parse_qs


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_id = "room_%s" % self.room_id

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_id, self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_id, self.channel_name
        )

    def receive(self, text_data=None, **kwargs):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_id,
            {
                "type": "chat_message",
                "message": message
            }
        )

    def chat_message(self, event):
        message = event["message"]

        self.send(text_data=json.dumps({
            "type": "chat",
            "message": message
        }))
