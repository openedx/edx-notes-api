import yaml

from .common import *

DEBUG = False
TEMPLATE_DEBUG = False

ALLOWED_HOSTS = ['*']

DISABLE_TOKEN_CHECK = False

CONFIG_ROOT = os.environ.get('CONFIG_ROOT')

with open(CONFIG_ROOT / "edx-notes-api.yml") as env_file:
    ENV_TOKENS = yaml.load(env_file)

SECRET_KEY = ENV_TOKENS.get('SECRET_KEY')

# ID and Secret used for authenticating JWT Auth Tokens
# should match those configured for `edx-notes` Client in EdX's /admin/oauth2/client/
CLIENT_ID =  ENV_TOKENS.get('CLIENT_ID')
CLIENT_SECRET =  ENV_TOKENS.get('CLIENT_SECRET')

ELASTICSEARCH_URL = ENV_TOKENS.get('ELASTICSEARCH_URL')
ELASTICSEARCH_INDEX = ENV_TOKENS.get('ELASTICSEARCH_INDEX')

# Number of rows to return by default in result.
RESULTS_DEFAULT_SIZE = ENV_TOKENS.get('RESULTS_DEFAULT_SIZE')

# Max number of rows to return in result.
RESULTS_MAX_SIZE = ENV_TOKENS.get('RESULTS_MAX_SIZE')

###############################################################################
# Override default annotator-store elasticsearch settings.
###############################################################################
es.host = ELASTICSEARCH_URL
es.index = ELASTICSEARCH_INDEX
annotator.elasticsearch.RESULTS_MAX_SIZE = RESULTS_MAX_SIZE
###############################################################################
