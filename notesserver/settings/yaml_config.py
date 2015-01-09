import yaml

from .common import *  # pylint: disable=unused-wildcard-import, wildcard-import
from path import path
from django.core.exceptions import ImproperlyConfigured

###############################################################################
# Explicitly declare here in case someone changes common.py.
###############################################################################
DEBUG = False
TEMPLATE_DEBUG = False
DISABLE_TOKEN_CHECK = False
###############################################################################

EDXNOTES_CONFIG_ROOT = os.environ.get('EDXNOTES_CONFIG_ROOT')

if not EDXNOTES_CONFIG_ROOT:
    raise ImproperlyConfigured("EDXNOTES_CONFIG_ROOT must be defined in the environment.")

CONFIG_ROOT = path(EDXNOTES_CONFIG_ROOT)

with open(CONFIG_ROOT / "edx-notes-api.yml") as yaml_file:
    config_from_yaml = yaml.load(yaml_file)

vars().update(config_from_yaml)

if ES_DISABLED:
    HAYSTACK_CONNECTIONS = {}
    INSTALLED_APPS.remove('haystack')
