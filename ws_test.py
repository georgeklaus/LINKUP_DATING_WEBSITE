#!/usr/bin/env python3
import os
import django
import asyncio
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'luchat.settings')
django.setup()

from django.contrib.auth import get_user_model
from chat.models import ChatRoom
from channels.testing import WebsocketCommunicator
from chat.consumers import ChatConsumer

User = get_user_model()

async def run_test(sender, room_name):
    # Use the ChatConsumer ASGI app directly so we can inject the user
    app = ChatConsumer.as_asgi()
    communicator = WebsocketCommunicator(app, f"/ws/chat/{room_name}/")

    # Inject an authenticated user into the scope before connecting
    communicator.scope['user'] = sender
    communicator.scope['url_route'] = {'kwargs': {'room_name': room_name}}
    connected, subproto = await communicator.connect()
    print('Connected:', connected)

    # Send a chat message
    await communicator.send_to(text_data=json.dumps({'message': 'hello from ws test'}))

    # Receive broadcast from consumer
    response = await communicator.receive_from()
    print('Received:', response)

    await communicator.disconnect()

if __name__ == '__main__':
    # Create users and chat room synchronously (avoid DB calls in async code)
    sender, _ = User.objects.get_or_create(username='ws_sender')
    sender.set_password('pass')
    sender.coins = 100
    sender.save()

    receiver, _ = User.objects.get_or_create(username='ws_receiver')
    receiver.set_password('pass')
    receiver.save()

    room_name = f"room_{sender.id}_{receiver.id}"
    room, _ = ChatRoom.objects.get_or_create(name=room_name)
    room.participants.add(sender, receiver)

    asyncio.run(run_test(sender, room_name))
