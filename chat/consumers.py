import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from datetime import timedelta
from .models import ChatRoom, Message, ChatCharge
from django.conf import settings
from .models import VideoCall

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Update user online status
        await self.update_user_online_status(True)

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Update user online status
        await self.update_user_online_status(False)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json['message']
        message_type = text_data_json.get('type', 'chat_message')

        if message_type == 'chat_message':
            # Charge for message if it's the first message in this session
            can_send = await self.charge_for_message()
            
            if can_send:
                # Save message to database
                message = await self.save_message(message_content)
                
                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message_content,
                        'sender': self.user.username,
                        'sender_id': self.user.id,
                        'timestamp': message.timestamp.isoformat(),
                        'message_id': message.id
                    }
                )
            else:
                # Notify user about insufficient coins
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Insufficient coins to send message'
                }))

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender': event['sender'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id']
        }))

    async def video_invite(self, event):
        # Relay a video call invite to connected chat clients
        await self.send(text_data=json.dumps({
            'type': 'video_invite',
            'room_name': event.get('room_name'),
            'from': event.get('from')
        }))

    @database_sync_to_async
    def save_message(self, content):
        room = ChatRoom.objects.get(name=self.room_name)
        message = Message.objects.create(
            room=room,
            sender=self.user,
            content=content
        )
        return message

    @database_sync_to_async
    def charge_for_message(self):
        """Charge user for sending message"""
        room = ChatRoom.objects.get(name=self.room_name)
        
        # Check if user was already charged in this session
        recent_charge = ChatCharge.objects.filter(
            chat_room=room,
            user=self.user,
            charged_at__gte=timezone.now() - timedelta(minutes=30)
        ).exists()
        
        if not recent_charge:
            if self.user.coins >= settings.CHAT_COST:
                self.user.deduct_coins(settings.CHAT_COST)
                ChatCharge.objects.create(
                    chat_room=room,
                    user=self.user,
                    amount=settings.CHAT_COST
                )
                return True
            else:
                return False
        return True

    @database_sync_to_async
    def update_user_online_status(self, online):
        self.user.is_online = online
        self.user.last_activity = timezone.now()
        self.user.save()


class SignalingConsumer(AsyncWebsocketConsumer):
    """Simple signaling channel for video calls.

    Clients should connect to: /ws/signaling/<room_name>/
    and exchange JSON messages with types: 'offer', 'answer', 'candidate'.
    This consumer relays messages to the signaling group for the room.
    It also enforces that the connecting user is either caller or receiver for the VideoCall.
    """

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.group_name = f'signaling_{self.room_name}'
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()
            return

        # Verify VideoCall exists and user is participant when possible
        try:
            vc = await database_sync_to_async(VideoCall.objects.get)(room_name=self.room_name)
            if not (vc.caller_id == self.user.id or vc.receiver_id == self.user.id):
                await self.close()
                return
        except Exception:
            # allow in DEBUG if VideoCall absent? better to reject
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # Relay incoming JSON to group; include sender username
        try:
            payload = json.loads(text_data)
        except Exception:
            return

        # Add sender metadata
        payload.setdefault('sender', self.user.username)

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'signal.message',
                'message': payload
            }
        )

    async def signal_message(self, event):
        # send the message payload to WS clients
        await self.send(text_data=json.dumps(event['message']))