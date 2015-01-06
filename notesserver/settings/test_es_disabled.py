from .test import *

ES_DISABLED = True
HAYSTACK_CONNECTIONS = {}
INSTALLED_APPS.remove('haystack')
