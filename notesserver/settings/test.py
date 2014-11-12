from annotator import es
import annotator
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

# Number of rows to return by default in result.
RESULTS_DEFAULT_SIZE = 25

# Max number of rows to return in result.
RESULTS_MAX_SIZE = 250

# Override default annotator-store elasticsearch settings.
es.host = ELASTICSEARCH_URL
es.index = ELASTICSEARCH_INDEX
annotator.elasticsearch.RESULTS_MAX_SIZE = RESULTS_MAX_SIZE
