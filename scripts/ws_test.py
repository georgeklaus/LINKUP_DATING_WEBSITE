#!/usr/bin/env python3
import json
import time
import sys
import requests

LOGIN_URL = 'http://127.0.0.1:8000/users/login/'
WS_URL_TEMPLATE = 'ws://127.0.0.1:8000/ws/chat/{room_name}/'

USERNAME = 'alice'
PASSWORD = 'alicepass'
ROOM_NAME = 'chat_14_15'

try:
    from websocket import create_connection
except Exception as e:
    print('websocket-client not installed. Install with: pip install websocket-client')
    sys.exit(1)

s = requests.Session()
print('GET', LOGIN_URL)
r = s.get(LOGIN_URL)
if r.status_code != 200:
    print('Failed to GET login page:', r.status_code)
    print(r.text[:500])
    sys.exit(1)

csrftoken = s.cookies.get('csrftoken', '')
print('CSRF token from cookie:', csrftoken)

login_data = {
    'username': USERNAME,
    'password': PASSWORD,
    'csrfmiddlewaretoken': csrftoken,
}
headers = {'Referer': LOGIN_URL}
print('POST', LOGIN_URL)
resp = s.post(LOGIN_URL, data=login_data, headers=headers)
print('Login POST status:', resp.status_code)
if resp.status_code not in (200, 302):
    print('Login failed, response snippet:')
    print(resp.text[:1000])
    sys.exit(1)

sessionid = s.cookies.get('sessionid')
if not sessionid:
    print('No sessionid cookie after login; login may have failed.')
    print('Cookies:', s.cookies)
    sys.exit(1)
print('Obtained sessionid:', sessionid[:8])

ws_url = WS_URL_TEMPLATE.format(room_name=ROOM_NAME)
print('Connecting to', ws_url)
cookie_header = f'sessionid={sessionid}; csrftoken={csrftoken}'
try:
    ws = create_connection(ws_url, header=[f'Cookie: {cookie_header}'])
except Exception as e:
    print('WebSocket connect failed:', e)
    sys.exit(1)

print('WebSocket connected; sending test message')
msg = {'message': 'Hello from ws_test.py'}
ws.send(json.dumps(msg))

# Listen for responses for a few seconds
start = time.time()
while time.time() - start < 5:
    try:
        result = ws.recv()
        print('Received:', result)
    except Exception:
        time.sleep(0.1)

ws.close()
print('Done')
