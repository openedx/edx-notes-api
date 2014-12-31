from .common import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
DISABLE_TOKEN_CHECK = False
INSTALLED_APPS += ('django_nose',)

ES_INDEXES = {'default': 'notes_index_test'}
