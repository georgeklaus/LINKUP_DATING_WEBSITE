#!/usr/bin/env python3
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'luchat.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from posts.models import Post

User = get_user_model()

TEST_USER = 'smoke_user'
TEST_PASS = 'password123'
TARGET_USER = 'smoke_target'

# Create users
user, created = User.objects.get_or_create(username=TEST_USER)
if created:
    user.set_password(TEST_PASS)
    user.gender = 'M'
    user.orientation = 'straight'
    user.coins = 1000
    user.save()
else:
    user.coins = 1000
    user.set_password(TEST_PASS)
    user.save()

 target, created = User.objects.get_or_create(username=TARGET_USER)
if created:
    target.set_password('password123')
    target.gender = 'F'
    target.orientation = 'straight'
    target.coins = 100
    target.save()

# Create a sample post by target so it appears in feed
Post.objects.create(user=target, content='Hello from target user for smoke test')

c = Client()
logged_in = c.login(username=TEST_USER, password=TEST_PASS)
print('Logged in:', logged_in)

paths = [
    '/',
    '/dashboard/',
    '/chat/',
    f'/chat/room/{TARGET_USER}/',
    '/matching/discover/',
    f'/users/profile/{TARGET_USER}/',
    '/posts/create/',
    '/payments/buy-coins/',
    '/users/settings/',
]

for p in paths:
    resp = c.get(p)
    print(p, resp.status_code, len(resp.content))

# Try liking the target
like_resp = c.post(f'/matching/like/{TARGET_USER}/')
print('Like POST status:', like_resp.status_code, like_resp.content)

# Try starting a video call (POST)
call_resp = c.post(f'/chat/video-call/{TARGET_USER}/')
print('Video call POST status:', call_resp.status_code, call_resp.content)

print('Smoke test complete')
