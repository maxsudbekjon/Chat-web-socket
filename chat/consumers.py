import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    active_users = {}  # {channel_name: username}
    active_chats = {}  # {user1: user2, user2: user1}

    async def connect(self):
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "set_username":
            username = data["username"]
            self.active_users[self.channel_name] = username
            await self.send_users_list()

        elif action == "start_chat":
            target_user = data["target_user"]
            sender = self.active_users.get(self.channel_name)
            if sender == target_user or target_user not in self.active_users.values():
                return
            self.active_chats[sender] = target_user
            self.active_chats[target_user] = sender
            await self.send(text_data=json.dumps({"action": "chat_started", "target_user": target_user}))

        elif action == "send_message":
            sender = self.active_users.get(self.channel_name)
            receiver = self.active_chats.get(sender)
            if receiver:
                receiver_channel = next((ch for ch, user in self.active_users.items() if user == receiver), None)
                if receiver_channel:
                    await self.channel_layer.send(
                        receiver_channel,
                        {
                            "type": "chat_message",
                            "message": data["message"],
                            "sender": sender,
                        },
                    )
                    await self.send(text_data=json.dumps({
                        "message": data["message"],
                        "sender": sender,
                        "self": True
                    }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "sender": event["sender"],
            "self": False
        }))

    async def disconnect(self, close_code):
        username = self.active_users.pop(self.channel_name, None)
        if username and username in self.active_chats:
            partner = self.active_chats.pop(username, None)
            if partner in self.active_chats:
                del self.active_chats[partner]
        await self.send_users_list()

    async def send_users_list(self):
        users_list = list(self.active_users.values())
        for channel in self.active_users.keys():
            await self.channel_layer.send(
                channel,
                {
                    "type": "update_users_list",
                    "users": users_list,
                },
            )

    async def update_users_list(self, event):
        await self.send(text_data=json.dumps({"users": event["users"]}))
