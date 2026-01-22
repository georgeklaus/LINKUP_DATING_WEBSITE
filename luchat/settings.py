import os
from pathlib import Path
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production-!')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,192.168.1.7,*', cast=lambda v: [s.strip() for s in v.split(',')])


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'channels',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_filters',

    'users',
    'posts', 
    'chat',
    'payments',
    'matching',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'luchat.urls'  # Changed from 'dating_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'luchat.context_processors.global_unread_count',
            ],
        },
    },
]


# Database Configuration
# Supports DATABASE_URL (for Koyeb/Render/Heroku) or individual settings
DATABASE_URL = config('DATABASE_URL', default='')

if DATABASE_URL and DATABASE_URL.strip():
    # Use DATABASE_URL for production (Neon, Heroku, etc.)
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL.strip(), conn_max_age=600)
    }
else:
    # Fallback to individual settings or SQLite
    DATABASES = {
        'default': {
            'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
            'NAME': config('DB_NAME', default=str(BASE_DIR / 'db.sqlite3')),
            'USER': config('DB_USER', default=''),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default=''),
            'OPTIONS': {
                'charset': 'utf8mb4',
            } if 'mysql' in config('DB_ENGINE', default='') else {},
        }
    }

# ASGI Configuration for Channels
ASGI_APPLICATION = 'luchat.asgi.application'  # Changed from 'dating_app.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            # Default: local Redis on port 6379
            'hosts': [config('REDIS_URL', default='redis://127.0.0.1:6379')],
        },
    },
}

# Custom User Model
AUTH_USER_MODEL = 'users.CustomUser'

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Use WhiteNoise for serving static files when using Daphne in development/production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Authentication URLs
LOGIN_REDIRECT_URL = 'dashboard'
LOGIN_URL = 'users:login'
LOGOUT_REDIRECT_URL = 'home'

# Coin Packages
COIN_PACKAGES = {
    100: 100,
    250: 250, 
    500: 700,
    1000: 1500,
    5000: 8000,
    10000: 25000,
}

# Service Costs
CHAT_COST = 3
PROFILE_VIEW_COST = 2
VIDEO_CALL_COST_PER_MIN = 20

# Registration bonuses
FEMALE_REGISTRATION_BONUS = 100
MALE_REGISTRATION_BONUS = 30

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# MegaPay settings (loaded from .env via python-decouple)
MEGAPAY_API_KEY = config('MEGAPAY_API_KEY', default='')
MEGAPAY_EMAIL = config('MEGAPAY_EMAIL', default='')
MEGAPAY_BASE_URL = config('MEGAPAY_BASE_URL', default='')

# Webhook verification: set a shared secret provided by the payment gateway
# and optionally enforce that incoming callbacks include a valid HMAC signature.
MEGAPAY_WEBHOOK_SECRET = config('MEGAPAY_WEBHOOK_SECRET', default='')
MEGAPAY_ENFORCE_WEBHOOK_SIGNATURE = config('MEGAPAY_ENFORCE_WEBHOOK_SIGNATURE', default=False, cast=bool)

# Local stub behavior: control whether the dev /mpesa/stk-push stub auto-posts
# a successful callback. For a realistic dev flow where users must be prompted
# for a PIN and manual simulation is used, set this to False.
MEGAPAY_STUB_AUTO_CALLBACK = config('MEGAPAY_STUB_AUTO_CALLBACK', default=False, cast=bool)

# During local development you may want to use the built-in MegaPay stub.
USE_LOCAL_MEGAPAY_STUB = config('USE_LOCAL_MEGAPAY_STUB', default=True, cast=bool)
if DEBUG and USE_LOCAL_MEGAPAY_STUB:
    MEGAPAY_BASE_URL = config('LOCAL_MEGAPAY_STUB_URL', default='http://127.0.0.1:8000/payments/_megapay_stub')

# Celery beat schedule: periodically reconcile pending payments
CELERY_BEAT_SCHEDULE = {
    'reconcile-payments-every-5-mins': {
        'task': 'payments.tasks.reconcile_pending_transactions',
        'schedule': 300.0,
        'args': (10, 100),
    },
}

# ============================================
# PRODUCTION SECURITY SETTINGS
# ============================================
if not DEBUG:
    # HTTPS/SSL Settings
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # HSTS Settings
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Other security settings
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    
    # CSRF trusted origins (add your domain)
    CSRF_TRUSTED_ORIGINS = config(
        'CSRF_TRUSTED_ORIGINS', 
        default='', 
        cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]
    )