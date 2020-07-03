from .test import *

ES_DISABLED = True
ELASTICSEARCH_DSL = {'default': {}}
INSTALLED_APPS = [i for i in INSTALLED_APPS if i not in ES_APPS]
