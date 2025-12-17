import requests

LOGIN='http://127.0.0.1:8000/users/login/'
URL='http://127.0.0.1:8000/chat/room/mzee/'
USERNAME='alice'
PASSWORD='alicepass'

s=requests.Session()
r=s.get(LOGIN)
csrftoken=s.cookies.get('csrftoken','')
resp=s.post(LOGIN, data={'username':USERNAME,'password':PASSWORD,'csrfmiddlewaretoken':csrftoken}, headers={'Referer':LOGIN})
print('login status', resp.status_code)
resp2=s.get(URL)
print('GET', URL, 'status', resp2.status_code)
print(resp2.text[:400])
