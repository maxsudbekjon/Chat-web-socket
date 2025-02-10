import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "chat_room"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]

        # Xabarni barcha foydalanuvchilarga (lekin jo‘natuvchiga emas) jo‘natamiz
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "sender_channel": self.channel_name,  # Jo‘natuvchini tekshirish uchun
            }
        )

    async def chat_message(self, event):
        sender_channel = event["sender_channel"]

        # Agar jo‘natuvchi o‘zi bo‘lsa, xabarni yubormaymiz
        if self.channel_name != sender_channel:
            await self.send(text_data=json.dumps({"message": event["message"]}))
