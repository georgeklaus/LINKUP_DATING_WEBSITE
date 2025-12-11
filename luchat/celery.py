import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dating_app.settings')

app = Celery('dating_app')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()