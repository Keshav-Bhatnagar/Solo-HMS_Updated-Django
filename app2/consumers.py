import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import DiscussionMessage
from django.contrib.auth import get_user_model

User = get_user_model()

class DiscussionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
            return
            
        self.room_group_name = 'discussion_global'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if not self.scope["user"].is_anonymous:
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        user = self.scope["user"]

        # Save message to database
        saved_msg = await self.save_message(user, message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': saved_msg.message,
                'user': user.get_full_name() or user.email,
                'user_id': user.id,
                'is_notification': saved_msg.is_notification,
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        user_name = event['user']
        user_id = event['user_id']
        is_notification = event['is_notification']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'user': user_name,
            'user_id': user_id,
            'is_notification': is_notification,
        }))

    @sync_to_async
    def save_message(self, user, message_text):
        return DiscussionMessage.objects.create(
            user=user,
            message=message_text,
            is_notification=False
        )
