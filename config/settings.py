"""
Django settings for the Klystr control plane.

Values are read from the environment (see .env.example); a .env file in the
project root is loaded automatically in development.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in ('1', 'true', 'yes', 'on')


def env_list(name, default=''):
    return [item.strip() for item in os.environ.get(name, default).split(',') if item.strip()]


SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-i(*h28alljqepz0=at!(7=vg5@qn1r3=d54y0nx5pf=m2z@8c%',
)

DEBUG = env_bool('DJANGO_DEBUG', True)

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1')


# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
]

LOCAL_APPS = [
    'apps.cluster',
    'apps.nodes',
    'apps.workloads',
    'apps.scheduler',
    'apps.controllers',
    'apps.agents',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'


# Database
# Defaults line up with infrastructure/docker/docker-compose.yml.
# Set DB_ENGINE=sqlite for a dependency-free local run.

if os.environ.get('DB_ENGINE', 'postgres') == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'klystr'),
            'USER': os.environ.get('POSTGRES_USER', 'klystr'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'klystr'),
            'HOST': os.environ.get('POSTGRES_HOST', '127.0.0.1'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
            'CONN_MAX_AGE': int(os.environ.get('POSTGRES_CONN_MAX_AGE', '60')),
        }
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Message broker / cache used by the control loops and agent heartbeats.

REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Django REST Framework

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'common.pagination.ListPagination',
    'PAGE_SIZE': 50,
    'EXCEPTION_HANDLER': 'common.exceptions.api_exception_handler',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}


# Control plane tuning knobs

KLYSTR = {
    # How long a node may go without a heartbeat before it is marked NotReady.
    'NODE_HEARTBEAT_TIMEOUT_SECONDS': int(os.environ.get('NODE_HEARTBEAT_TIMEOUT_SECONDS', '40')),
    # Interval at which agents are expected to report in.
    'AGENT_HEARTBEAT_INTERVAL_SECONDS': int(os.environ.get('AGENT_HEARTBEAT_INTERVAL_SECONDS', '10')),
    # How often each controller reconciles desired vs. observed state.
    'RECONCILE_INTERVAL_SECONDS': int(os.environ.get('RECONCILE_INTERVAL_SECONDS', '5')),
    # Scheduler strategy: least_loaded | round_robin | random
    'SCHEDULER_STRATEGY': os.environ.get('SCHEDULER_STRATEGY', 'least_loaded'),
}


# Internationalization

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'


# Email

MAILERS = {
    'default': {
        'BACKEND': os.environ.get(
            'DJANGO_EMAIL_BACKEND',
            'django.core.mail.backends.console.EmailBackend',
        ),
    },
}


# Logging

from common.logging import build_logging_config  # noqa: E402

LOGGING = build_logging_config(
    level=os.environ.get('LOG_LEVEL', 'DEBUG' if DEBUG else 'INFO'),
    json_output=env_bool('LOG_JSON', not DEBUG),
)
