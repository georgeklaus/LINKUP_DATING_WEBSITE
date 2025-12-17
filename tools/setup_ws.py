import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'luchat.settings')
import django
django.setup()

from users.models import CustomUser
from chat.views import get_chat_room_name
from chat.models import ChatRoom

ws_name = 'ws_tester'
if not CustomUser.objects.filter(username=ws_name).exists():
    CustomUser.objects.create_user(username=ws_name, password='testerpass')
    print('created ws_tester')
else:
    print('ws_tester exists')

if not CustomUser.objects.filter(username='alice').exists():
    print('alice missing; create alice first')
    raise SystemExit(0)

alice = CustomUser.objects.get(username='alice')
ws = CustomUser.objects.get(username=ws_name)

rn = get_chat_room_name(alice, ws)
r, created = ChatRoom.objects.get_or_create(name=rn)
r.participants.add(alice, ws)
print('room:', rn)
