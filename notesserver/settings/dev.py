from .common import *
from notesserver.settings.logger import get_logger_config

DEBUG = True

ES_INDEXES = {'default': 'notes_index_dev'}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'default.db',
    }
}

LOGGING = get_logger_config(debug=DEBUG)
