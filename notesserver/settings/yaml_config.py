from os import environ

import yaml
from django.core.exceptions import ImproperlyConfigured

from notesserver.settings.logger import build_logging_config
from path import path

from .common import *  # pylint: disable=unused-wildcard-import, wildcard-import

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

with open(CONFIG_ROOT / "edx_notes_api.yml") as yaml_file:
    config_from_yaml = yaml.safe_load(yaml_file)

vars().update(config_from_yaml)
#
# Support environment overrides for migrations
DB_OVERRIDES = dict(
    PASSWORD=environ.get('DB_MIGRATION_PASS', DATABASES['default']['PASSWORD']),
    ENGINE=environ.get('DB_MIGRATION_ENGINE', DATABASES['default']['ENGINE']),
    USER=environ.get('DB_MIGRATION_USER', DATABASES['default']['USER']),
    NAME=environ.get('DB_MIGRATION_NAME', DATABASES['default']['NAME']),
    HOST=environ.get('DB_MIGRATION_HOST', DATABASES['default']['HOST']),
    PORT=environ.get('DB_MIGRATION_PORT', DATABASES['default']['PORT']),
)

for override, value in DB_OVERRIDES.items():
    DATABASES['default'][override] = value

if ES_DISABLED:
    HAYSTACK_CONNECTIONS = {}
    INSTALLED_APPS.remove('haystack')

LOGGING = build_logging_config()
