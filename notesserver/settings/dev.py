from notesserver.settings.logger import build_logging_config

from .common import *

DEBUG = True
LOG_SETTINGS_DEBUG = True
LOG_SETTINGS_DEV_ENV = True

ELASTICSEARCH_INDEX_NAMES = {'notesapi.v1.search_indexes.documents.note': 'notes_index_dev'}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'default.db',
    }
}

LOGGING = build_logging_config()
