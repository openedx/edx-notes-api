import yaml

from .common import *  # pylint: disable=unused-wildcard-import, wildcard-import

###############################################################################
# Explicitly declare here in case someone changes common.py.
###############################################################################
DEBUG = False
TEMPLATE_DEBUG = False
DISABLE_TOKEN_CHECK = False
###############################################################################

CONFIG_ROOT = os.environ.get('EDXNOTES_CONFIG_ROOT')

with open(CONFIG_ROOT / "edx-notes-api.yml") as yaml_file:
    config_from_yaml = yaml.load(yaml_file)

vars().update(config_from_yaml)
