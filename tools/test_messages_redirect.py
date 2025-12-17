import requests

LOGIN = 'http://127.0.0.1:8000/users/login/'
TARGET = 'http://127.0.0.1:8000/chat/messages/'
USERNAME = 'alice'
PASSWORD = 'alicepass'

s = requests.Session()
r = s.get(LOGIN)
csrftoken = s.cookies.get('csrftoken','')
resp = s.post(LOGIN, data={'username': USERNAME, 'password': PASSWORD, 'csrfmiddlewaretoken': csrftoken}, headers={'Referer': LOGIN})
print('login status', resp.status_code)
rr = s.get(TARGET, allow_redirects=True)
print('final url', rr.url)
print('status', rr.status_code)
print(rr.text[:400])
