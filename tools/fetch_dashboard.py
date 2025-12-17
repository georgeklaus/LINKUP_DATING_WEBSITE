import requests
from bs4 import BeautifulSoup

LOGIN = 'http://127.0.0.1:7000/users/login/'
DASH = 'http://127.0.0.1:7000/dashboard/'
USERNAME = 'alice'
PASSWORD = 'alicepass'

s = requests.Session()
r = s.get(LOGIN)
if r.status_code != 200:
    print('login page failed', r.status_code)
    raise SystemExit(1)

csrftoken = s.cookies.get('csrftoken', '')
# perform login (include CSRF token)
payload = {'username': USERNAME, 'password': PASSWORD, 'csrfmiddlewaretoken': csrftoken}
headers = {'Referer': LOGIN}
r = s.post(LOGIN, data=payload, headers=headers)
if r.status_code not in (200,302):
    print('login failed', r.status_code)
    raise SystemExit(1)

r = s.get(DASH)
if r.status_code != 200:
    print('dashboard fetch failed', r.status_code)
    raise SystemExit(1)

soup = BeautifulSoup(r.text, 'html.parser')
btn = soup.find(id='my-messages-btn')
if btn:
    print('my-messages href=', btn.get('href'))
    print('anchor text=', btn.get_text(strip=True))
else:
    print('my-messages button not found')
