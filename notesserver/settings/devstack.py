from __future__ import absolute_import

from notesserver.settings.logger import get_logger_config

from .common import *

DEBUG = True

ALLOWED_HOSTS = ['*']

LOGGING = get_logger_config(debug=DEBUG, dev_env=True, local_loglevel='DEBUG')
del LOGGING['handlers']['local']

# These values are derived from provision-ida-user.sh in the edx/devstack repo.
CLIENT_ID = 'edx_notes_api-key'
CLIENT_SECRET = 'edx_notes_api-secret'

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
