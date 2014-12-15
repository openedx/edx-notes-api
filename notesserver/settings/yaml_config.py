import yaml

from .common import *

DEBUG = False
TEMPLATE_DEBUG = False

ALLOWED_HOSTS = ['*']

DISABLE_TOKEN_CHECK = False

CONFIG_ROOT = os.environ.get('CONFIG_ROOT')

with open(CONFIG_ROOT / "edx-notes-api.yml") as yaml_file:
    config_from_yaml = yaml.load(yaml_file)

vars().update(config_from_yaml)

###############################################################################
# Override default annotator-store elasticsearch settings.
###############################################################################
es.host = ELASTICSEARCH_URL
es.index = ELASTICSEARCH_INDEX
annotator.elasticsearch.RESULTS_MAX_SIZE = RESULTS_MAX_SIZE
###############################################################################
