from .common import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
DISABLE_TOKEN_CHECK = False
INSTALLED_APPS += ('django_nose',)

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://127.0.0.1:9200/',
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
