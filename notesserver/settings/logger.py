"""
Logging configuration
"""

import os
import platform
import sys
from logging.handlers import SysLogHandler

from django.conf import settings


def build_logging_config():

    """
    Return the appropriate logging config dictionary. You should assign the
    result of this to the LOGGING var in your settings.
    """
    # Revert to INFO if an invalid string is passed in

    log_dir = settings.LOG_SETTINGS_LOG_DIR
    logging_env = settings.LOG_SETTINGS_LOGGING_ENV
    edx_filename = settings.LOG_SETTINGS_EDX_FILENAME
    dev_env = settings.LOG_SETTINGS_DEV_ENV
    debug = settings.LOG_SETTINGS_DEBUG
    local_loglevel = settings.LOG_SETTINGS_LOCAL_LOGLEVEL
    service_variant = settings.LOG_SETTINGS_SERVICE_VARIANT

    if local_loglevel not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        local_loglevel = 'INFO'

    hostname = platform.node().split(".")[0]
    syslog_format = (
        "[service_variant={service_variant}]"
        "[%(name)s][env:{logging_env}] %(levelname)s "
        "[{hostname} %(process)d] [%(filename)s:%(lineno)d] "
        "- %(message)s"
    ).format(service_variant=service_variant, logging_env=logging_env, hostname=hostname)

    handlers = ['console']

    logger_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s,%(msecs)03d %(levelname)s [%(name)s] [%(process)d] - %(message)s',
                'datefmt': '%Y-%m-%dT%H:%M:%S',
            },
            'syslog_format': {'format': syslog_format},
            'raw': {'format': '%(message)s'},
        },
        'handlers': {
            'console': {
                'level': 'DEBUG' if debug else 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'stream': sys.stdout,
            },
        },
        'loggers': {
            'django': {'handlers': handlers, 'propagate': True, 'level': 'INFO', 'formatter': 'standard'},
            "elasticsearch.trace": {'handlers': handlers, 'level': 'WARNING', 'propagate': False, 'formatter': 'standard'},
            '': {'handlers': handlers, 'level': 'DEBUG', 'propagate': False, 'formatter': 'standard'},
        },
    }

    return logger_config
