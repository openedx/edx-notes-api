from notesserver.settings.logger import build_logging_config

from .common import *

DEBUG = True
LOG_SETTINGS_DEBUG = True
LOG_SETTINGS_DEV_ENV = True

ALLOWED_HOSTS = ['*']

# These values are derived from provision-ida-user.sh in the edx/devstack repo.
CLIENT_ID = 'edx_notes_api-backend-service-key'
CLIENT_SECRET = 'edx_notes_api-backend-service-secret'

ES_INDEXES = {'default': 'notes_index'}
HAYSTACK_CONNECTIONS['default']['URL'] = 'http://edx.devstack.elasticsearch:9200/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'notes'),
        'USER': os.environ.get('DB_USER', 'notes001'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'password'),
        'HOST': os.environ.get('DB_HOST', 'edx.devstack.mysql'),
        'PORT': os.environ.get('DB_PORT', 3306),
        'CONN_MAX_AGE': 60,
    }
}

JWT_AUTH = {}

LOGGING = build_logging_config()
