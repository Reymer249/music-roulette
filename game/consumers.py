import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from urllib.parse import urlparse, parse_qs


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        encoded_url = self.scope.get('query_string', b'').decode('utf-8')
        url = parse_qs(encoded_url).get('url', [''])[0]
        self.room_group_id = url.split("/")[-2]
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_id,
            self.channel_name
        )
        self.accept()

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
