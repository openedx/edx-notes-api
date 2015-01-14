from .test import *

ES_DISABLED = True
HAYSTACK_CONNECTIONS = {'default':{}}
INSTALLED_APPS.remove('haystack')
