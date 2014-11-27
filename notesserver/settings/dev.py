from annotator import es
from .common import *

DEBUG = True

ELASTICSEARCH_URL = 'http://127.0.0.1:9200'
ELASTICSEARCH_INDEX = 'edx-notes-dev'

# Overwrite default annotator-store elasticsearch settings.
es.host = ELASTICSEARCH_URL
es.index = ELASTICSEARCH_INDEX
