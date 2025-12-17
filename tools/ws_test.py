#!/usr/bin/env python3
import json
import time
import sys
import requests
from websocket import create_connection

BASE = 'http://127.0.0.1:8000'
LOGIN = BASE + '/users/login/'

# Usage: ws_test.py <room_name> [username] [password]
if len(sys.argv) < 2:
    print('Usage: ws_test.py <room_name> [username] [password]')
    sys.exit(2)

room = sys.argv[1]
USERNAME = sys.argv[2] if len(sys.argv) > 2 else 'alice'
PASSWORD = sys.argv[3] if len(sys.argv) > 3 else 'alicepass'

session = requests.Session()
# fetch login page to get CSRF cookie
r = session.get(LOGIN)
if r.status_code != 200:
    print('Failed to fetch login page', r.status_code)
    sys.exit(1)

csrftoken = session.cookies.get('csrftoken', '')

payload = {
    'username': USERNAME,
    'password': PASSWORD,
    'csrfmiddlewaretoken': csrftoken,
}
headers = {'Referer': LOGIN}

# perform login
r = session.post(LOGIN, data=payload, headers=headers)
if r.status_code not in (200, 302):
    print('Login failed', r.status_code, r.text)
    sys.exit(1)

if 'sessionid' not in session.cookies:
    print('No sessionid after login; cookies:', session.cookies.get_dict())
    sys.exit(1)

sess = session.cookies.get('sessionid')
print('Got sessionid:', sess[:8] + '...')

ws_url = f"ws://127.0.0.1:8000/ws/chat/{room}/"
print('Connecting to', ws_url)
cookie = f"sessionid={sess}; csrftoken={session.cookies.get('csrftoken','')}"

ws = create_connection(ws_url, header=[f'Cookie: {cookie}'])
print('Connected. Sending test message...')
msg = {'message': 'hello from ws_tester'}
ws.send(json.dumps(msg))
print('Sent; waiting for response...')
try:
    res = ws.recv()
    print('Received:', res)
except Exception as e:
    print('Receive error:', e)

ws.close()
print('Done')
