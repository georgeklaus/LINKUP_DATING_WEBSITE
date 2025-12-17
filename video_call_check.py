#!/usr/bin/env python3
import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'luchat.settings')
django.setup()

# Ensure test client host is allowed
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS += ['testserver']

from django.test import Client
from django.contrib.auth import get_user_model
from chat.models import VideoCall
from django.conf import settings as dj_settings

User = get_user_model()

caller_name = f"video_caller_{uuid.uuid4().hex[:8]}"
receiver_name = f"video_recv_{uuid.uuid4().hex[:8]}"

# Create users
caller, _ = User.objects.get_or_create(username=caller_name)
caller.set_password('testpass')
caller.coins = dj_settings.VIDEO_CALL_COST_PER_MIN
caller.save()

receiver, _ = User.objects.get_or_create(username=receiver_name)
receiver.set_password('testpass')
receiver.save()

client = Client()
logged = client.login(username=caller_name, password='testpass')
print('Logged in as caller:', logged)

resp = client.post(f'/chat/video-call/{receiver.username}/')
print('Response status:', resp.status_code)
try:
    print('Response JSON:', resp.json())
except Exception:
    print('Response content:', resp.content)

if resp.status_code == 200:
    data = resp.json()
    call_id = data.get('call_id')
    if call_id:
        vc = VideoCall.objects.filter(id=call_id).first()
        print('VideoCall created:', vc is not None, 'room:', getattr(vc, 'room_name', None))
