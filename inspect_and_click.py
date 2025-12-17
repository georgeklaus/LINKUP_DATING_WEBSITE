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
    marker = 'My Messages'
    idx = html.find(marker)
    if idx == -1:
        return None
    a_start = html.rfind('<a', 0, idx)
    if a_start == -1:
        return None
    a_end = html.find('</a>', idx)
    if a_end == -1:
        return None
    a_end += len('</a>')
    a = html[a_start:a_end]
    # extract href
    m = re.search(r"href=['\"]([^'\"]+)['\"]", a)
    return m.group(1) if m else None

def main():
    client = Client()
    from django.conf import settings
    if 'testserver' not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS += ['testserver']

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

    resp = client.get('/dashboard/')
    html = resp.content.decode('utf-8')
    href = find_my_messages_href(html)
    print('Extracted href:', href)
    if href:
        resp2 = client.get(href)
        print('GET', href, '-> status', resp2.status_code, 'path', resp2.request.get('PATH_INFO'))
    else:
        print('Could not find My Messages link in dashboard HTML')

if __name__ == '__main__':
    main()
