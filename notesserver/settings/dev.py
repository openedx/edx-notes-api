import annotator
from annotator import es
from .common import *

DEBUG = True

ELASTICSEARCH_URL = 'http://127.0.0.1:9200'
ELASTICSEARCH_INDEX = 'edx-notes-dev'

# Overwrite default annotator-store elasticsearch settings.
es.host = ELASTICSEARCH_URL
es.index = ELASTICSEARCH_INDEX

# Number of rows to return by default in result.
RESULTS_DEFAULT_SIZE = 1000

# Max number of rows to return in result.
RESULTS_MAX_SIZE = 1100

# Override default annotator-store elasticsearch settings.
es.host = ELASTICSEARCH_URL
es.index = ELASTICSEARCH_INDEX
annotator.elasticsearch.RESULTS_MAX_SIZE = RESULTS_MAX_SIZE
