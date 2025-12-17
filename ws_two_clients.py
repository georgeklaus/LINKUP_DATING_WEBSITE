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

async def run_two_clients(sender, receiver, room_name):
    app = ChatConsumer.as_asgi()

    comm_a = WebsocketCommunicator(app, f"/ws/chat/{room_name}/")
    comm_b = WebsocketCommunicator(app, f"/ws/chat/{room_name}/")

    # inject scope data
    comm_a.scope['user'] = sender
    comm_a.scope['url_route'] = {'kwargs': {'room_name': room_name}}

    comm_b.scope['user'] = receiver
    comm_b.scope['url_route'] = {'kwargs': {'room_name': room_name}}

    connected_a, _ = await comm_a.connect()
    connected_b, _ = await comm_b.connect()
    print('A connected:', connected_a, 'B connected:', connected_b)

    # A sends a message
    await comm_a.send_to(text_data=json.dumps({'message': 'hello from A'}))

    # B should receive a broadcasted chat_message
    try:
        msg = await comm_b.receive_from()
        print('B received:', msg)
    except Exception as e:
        print('B did not receive message:', e)

    await comm_a.disconnect()
    await comm_b.disconnect()

if __name__ == '__main__':
    # synchronous DB setup
    sender, _ = User.objects.get_or_create(username='ws_a')
    sender.set_password('pass')
    sender.coins = 100
    sender.save()

    receiver, _ = User.objects.get_or_create(username='ws_b')
    receiver.set_password('pass')
    receiver.save()

    room_name = f"room_{sender.id}_{receiver.id}"
    room, _ = ChatRoom.objects.get_or_create(name=room_name)
    room.participants.add(sender, receiver)

    asyncio.run(run_two_clients(sender, receiver, room_name))
