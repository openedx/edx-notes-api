from annotator import es
from .common import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

INSTALLED_APPS += ('django_nose',)

ELASTICSEARCH_URL = 'http://127.0.0.1:9200'
ELASTICSEARCH_INDEX = 'edx-notes-test'

# Overwrite default annotator-store elasticsearch settings.
es.host = ELASTICSEARCH_URL
es.index = ELASTICSEARCH_INDEX

