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

ELASTICSEARCH_INDEX = 'edx-notes-test'

###############################################################################
# Override default annotator-store elasticsearch settings.
###############################################################################
es.host = ELASTICSEARCH_URL
es.index = ELASTICSEARCH_INDEX
annotator.elasticsearch.RESULTS_MAX_SIZE = RESULTS_MAX_SIZE
###############################################################################


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
    },
}