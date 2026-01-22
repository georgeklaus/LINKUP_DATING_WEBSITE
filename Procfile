web: daphne -b 0.0.0.0 -p $PORT luchat.asgi:application
worker: celery -A luchat worker -l info
beat: celery -A luchat beat -l info
