import os
import sys

import dj_database_url
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
RUNNING_TESTS = 'test' in sys.argv
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-key-change-me')
DEBUG = os.getenv('DEBUG', '1') == '1'
if not DEBUG and SECRET_KEY == 'dev-key-change-me':
    raise ImproperlyConfigured('Configura DJANGO_SECRET_KEY para producción.')
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]
CSRF_TRUSTED_ORIGINS = [x.strip() for x in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if x.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'apps.catalog',
    'apps.inventory.apps.InventoryConfig',
    'apps.customers',
    'apps.orders',
    'apps.checkout',
    'apps.dashboard',
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

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.brand_globals',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

DATABASE_URL = os.getenv('DATABASE_URL', '').strip()
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=int(os.getenv('DB_CONN_MAX_AGE', '600')),
            ssl_require=os.getenv('DB_SSL_REQUIRE', '1') == '1',
        )
    }
else:
    if not DEBUG and os.getenv('DB_ENGINE', 'django.db.backends.sqlite3') == 'django.db.backends.sqlite3':
        raise ImproperlyConfigured('En producción debes configurar DATABASE_URL o DB_ENGINE no-SQLite.')
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
            'NAME': os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3'),
            'USER': os.getenv('DB_USER', ''),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', ''),
            'PORT': os.getenv('DB_PORT', ''),
            'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '600')),
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 9}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

WHATSAPP_PHONE = os.getenv('WHATSAPP_PHONE', '')
CURRENCY_USD_RATE = float(os.getenv('CURRENCY_USD_RATE', '0.00026'))

REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'checkout': '20/hour',
        'sensitive': '60/hour',
    }
}

STATICFILES_STORAGE_BACKEND = (
    'django.contrib.staticfiles.storage.StaticFilesStorage'
    if RUNNING_TESTS
    else 'whitenoise.storage.CompressedManifestStaticFilesStorage'
)
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': STATICFILES_STORAGE_BACKEND},
}

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', '1') == '1'
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '300'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', '1') == '1'
    SECURE_HSTS_PRELOAD = os.getenv('SECURE_HSTS_PRELOAD', '0') == '1'


SECURE_REFERRER_POLICY = os.getenv('SECURE_REFERRER_POLICY', 'strict-origin-when-cross-origin')
SECURE_CROSS_ORIGIN_OPENER_POLICY = os.getenv('SECURE_CROSS_ORIGIN_OPENER_POLICY', 'same-origin')
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = os.getenv('CSRF_COOKIE_HTTPONLY', '0') == '1'
SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
CSRF_COOKIE_SAMESITE = os.getenv('CSRF_COOKIE_SAMESITE', 'Lax')
