import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','luchat.settings')
import sys
# ensure repo root on path so "luchat" package imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../')
import django
django.setup()
from users.models import CustomUser
from chat.models import ChatRoom
from matching.utils import MatchFinder

try:
    u = CustomUser.objects.get(username='alice')
except CustomUser.DoesNotExist:
    print('alice not found')
    raise SystemExit(1)
print('Alice id:', u.id, 'gender:', getattr(u,'gender',None), 'orientation:', getattr(u,'orientation',None))
rooms = ChatRoom.objects.filter(participants=u, is_active=True)
print('Found', rooms.count(), 'rooms for alice')
for r in rooms:
    last = r.messages.last()
    other = r.participants.exclude(id=u.id).first()
    last_ts = last.timestamp if last else None
    compatible = other in MatchFinder.get_compatible_users(u)
    print('room:', r.name, 'other:', other.username if other else None, 'last_msg:', last_ts, 'compatible:', compatible)

comp_qs = MatchFinder.get_compatible_users(u)
print('Compatible users count:', comp_qs.count())
print('Compatible sample:', list(comp_qs.values_list('username', flat=True)[:10]))
