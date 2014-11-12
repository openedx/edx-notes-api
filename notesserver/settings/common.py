import os
import json
import sys

DEBUG = False
TEMPLATE_DEBUG = False
USE_TZ = True
TIME_ZONE = 'UTC'

# This value needs to be overriden in production.
SECRET_KEY = '*^owi*4%!%9=#h@app!l^$jz8(c*q297^)4&4yn^#_m#fq=z#l'

ROOT_URLCONF = 'notesserver.urls'

MIDDLEWARE_CLASSES = (
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
)

INSTALLED_APPS = (
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_swagger',
    'corsheaders',
    'notesapi',
    'notesapi.v1',
)

STATIC_URL = '/static/'

WSGI_APPLICATION = 'notesserver.wsgi.application'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'stream': sys.stderr,
            'formatter': 'standard',
        },
    },
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s %(process)d [%(name)s] %(filename)s:%(lineno)d - %(message)s',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'notesserver': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True
        },
        'elasticsearch.trace': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True
        },
        'elasticsearch': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': True
        },
        'annotator.elasticsearch': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': True
        },
        'urllib3': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True
        },
    },
}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ]
}

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = (
    'x-requested-with',
    'content-type',
    'accept',
    'origin',
    'authorization',
    'x-csrftoken',
    'x-annotator-auth-token',
)
