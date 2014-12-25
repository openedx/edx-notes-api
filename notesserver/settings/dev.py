import annotator
from annotator import es
from .common import *

DEBUG = True

ELASTICSEARCH_INDEX = 'edx-notes-dev'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'default.db',
    }
}

###############################################################################
# Override default annotator-store elasticsearch settings.
###############################################################################
es.host = ELASTICSEARCH_URL
es.index = ELASTICSEARCH_INDEX
annotator.elasticsearch.RESULTS_MAX_SIZE = RESULTS_MAX_SIZE

ES_URLS = ['http://localhost:9200']
ES_INDEXES = {'default': 'main_index'}
ES_DISABLED = False
###############################################################################
