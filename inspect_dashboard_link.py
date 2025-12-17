#!/usr/bin/env python3
import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'luchat.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

def find_my_messages_href(html):
    # Try to find the anchor tag that contains 'My Messages' and return the full anchor HTML
    marker = 'My Messages'
    idx = html.find(marker)
    if idx == -1:
        return None

    # find the nearest '<a' before the marker
    a_start = html.rfind('<a', 0, idx)
    if a_start == -1:
        return None
    a_end = html.find('</a>', idx)
    if a_end == -1:
        return None
    a_end += len('</a>')
    return html[a_start:a_end]

def main():
    client = Client()
    # Ensure we have a test user; create if not exists
    user, created = User.objects.get_or_create(username='inspect_user')
    if created:
        user.set_password('testpass')
        user.gender = 'M'
        user.orientation = 'straight'
        user.save()

    logged = client.login(username='inspect_user', password='testpass')
    if not logged:
        print('Login failed')
        return

    # Allow test client host
    from django.conf import settings
    if 'testserver' not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS += ['testserver']

    resp = client.get('/dashboard/')
    html = resp.content.decode('utf-8')
    fragment = find_my_messages_href(html)
    if fragment:
        print('My Messages anchor fragment:\n')
        print(fragment)
    else:
        print('My Messages anchor not found')

if __name__ == '__main__':
    main()
