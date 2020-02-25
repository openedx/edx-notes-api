from .common import *

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DB_NAME', 'default.db'),
        'USER': os.environ.get('DB_USER', ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', ''),
        'PORT': os.environ.get('DB_PORT', ''),
        'CONN_MAX_AGE': int(os.environ.get('CONN_MAX_AGE', 0))
    }
}

DISABLE_TOKEN_CHECK = False

JWT_AUTH = {}

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'notesserver.highlight.ElasticsearchSearchEngine',
        'URL': os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200/'),
        'INDEX_NAME': 'notes_index_test',
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'stream': sys.stderr,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'elasticsearch.trace': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False
        }
    },
}

DEFAULT_NOTES_PAGE_SIZE = 10
