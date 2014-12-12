import annotator
from annotator import es
from .common import *

DEBUG = True

ELASTICSEARCH_INDEX = 'edx-notes-dev'

###############################################################################
# Override default annotator-store elasticsearch settings.
###############################################################################
es.host = ELASTICSEARCH_URL
es.index = ELASTICSEARCH_INDEX
annotator.elasticsearch.RESULTS_MAX_SIZE = RESULTS_MAX_SIZE
###############################################################################
