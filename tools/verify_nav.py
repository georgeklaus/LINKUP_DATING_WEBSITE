import os, django, requests
from bs4 import BeautifulSoup
os.environ.setdefault('DJANGO_SETTINGS_MODULE','luchat.settings')
django.setup()

s=requests.Session()
login='http://127.0.0.1:8000/users/login/'
# fetch login page
r=s.get(login)
csrftoken=s.cookies.get('csrftoken','')
resp=s.post(login, data={'username':'alice','password':'alicepass','csrfmiddlewaretoken':csrftoken}, headers={'Referer':login})
print('login status', resp.status_code)
# get dashboard
r2=s.get('http://127.0.0.1:8000/dashboard/')
print('dashboard status', r2.status_code)
soup=BeautifulSoup(r2.text,'html.parser')
nav = soup.find('a', href=True, string=lambda t: 'Messages' in t if t else False)
print('navbar messages href', nav.get('href') if nav else 'no-nav')
# follow the navbar link
if nav:
    target = 'http://127.0.0.1:8000' + nav.get('href')
    r3 = s.get(target)
    print('follow status', r3.status_code, 'url=', r3.url)
    print('len content', len(r3.text))
