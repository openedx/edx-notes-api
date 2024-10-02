import os
import sys

DEBUG = False
TEMPLATE_DEBUG = False
DISABLE_TOKEN_CHECK = False
USE_TZ = True
TIME_ZONE = 'UTC'
AUTH_USER_MODEL = 'auth.User'

# This value needs to be overriden in production.
SECRET_KEY = 'CHANGEME'
ALLOWED_HOSTS = ['*']

# ID and Secret used for authenticating JWT Auth Tokens
# should match those configured for `edx-notes` Client in EdX's /admin/oauth2/client/
CLIENT_ID = 'CHANGEME'
CLIENT_SECRET = 'CHANGEME'

ES_DISABLED = False

ELASTICSEARCH_DSL = {'default': {'hosts': '127.0.0.1:9200'}}

ELASTICSEARCH_DSL_INDEX_SETTINGS = {'number_of_shards': 1, 'number_of_replicas': 0}

# Name of the Elasticsearch index
ELASTICSEARCH_INDEX_NAMES = {'notesapi.v1.search_indexes.documents.note': 'edx_notes_api'}
ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = 'django_elasticsearch_dsl.signals.RealTimeSignalProcessor'

# Number of rows to return by default in result.
RESULTS_DEFAULT_SIZE = 25

# Max number of rows to return in result.
RESULTS_MAX_SIZE = 250

ROOT_URLCONF = 'notesserver.urls'

DEFAULT_HASHING_ALGORITHM = "sha1"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"


MIDDLEWARE = (
    'edx_django_utils.monitoring.CookieMonitoringMiddleware',
    'edx_django_utils.monitoring.DeploymentMonitoringMiddleware',
    'edx_django_utils.cache.middleware.RequestCacheMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'edx_rest_framework_extensions.middleware.RequestMetricsMiddleware',
    'edx_rest_framework_extensions.auth.jwt.middleware.EnsureJWTAuthSettingsMiddleware',
)

ES_APPS = ('elasticsearch_dsl', 'django_elasticsearch_dsl', 'django_elasticsearch_dsl_drf',)

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'notesapi.v1',
    # additional release utilities to ease automation
    'release_util',
    'drf_spectacular',
]
if not ES_DISABLED:
    INSTALLED_APPS.extend(ES_APPS)

STATIC_URL = '/static/'

WSGI_APPLICATION = 'notesserver.wsgi.application'

LOG_SETTINGS_LOG_DIR = '/var/tmp'
LOG_SETTINGS_LOGGING_ENV = 'no_env'
LOG_SETTINGS_DEV_ENV = False
LOG_SETTINGS_DEBUG = False
LOG_SETTINGS_LOCAL_LOGLEVEL = 'INFO'
LOG_SETTINGS_EDX_FILENAME = "edx.log"
LOG_SETTINGS_SERVICE_VARIANT = 'edx-notes-api'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.SessionAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['notesapi.v1.permissions.HasAccessToken'],
    'DEFAULT_PAGINATION_CLASS': 'notesapi.v1.paginators.NotesPaginator',
    'DEFAULT_RENDERER_CLASSES': ('rest_framework.renderers.JSONRenderer',),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'edx-notes-api',
    'DESCRIPTION': 'API documentation for edx-notes-api',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/'
}

# CORS is configured to allow all origins because requests to the
# Notes API do not rely on ambient authority; instead, they are
# authorized explicitly via an X-Annotator-Auth-Token header. (The
# default permission class is HasAccessToken, which checks it.)
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = (
    'x-requested-with',
    'content-type',
    'accept',
    'origin',
    'authorization',
    'x-csrftoken',
    'x-annotator-auth-token',
)

# Base project path, where manage.py lives.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,  # This ensures app templates are loadable, e.g. DRF views.
        'DIRS': [
            # The EdxNotes templates directory is not actually under any app
            # directory, so specify its absolute path.
            os.path.join(BASE_DIR, 'templates'),
        ],
    }
]

DEFAULT_NOTES_PAGE_SIZE = 25

### Maximum number of allowed notes for each student per course ###
MAX_NOTES_PER_COURSE = 500

ELASTICSEARCH_URL = 'localhost:9200'
ELASTICSEARCH_INDEX = 'edx_notes'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'NAME': 'edx_notes_api',
        'OPTIONS': {'connect_timeout': 10},
        'PASSWORD': 'secret',
        'PORT': 3306,
        'USER': 'notes001',
    }
}

USERNAME_REPLACEMENT_WORKER = 'OVERRIDE THIS WITH A VALID USERNAME'

JWT_AUTH = {
    'JWT_AUTH_HEADER_PREFIX': 'JWT',
    'JWT_ISSUER': [
        {'AUDIENCE': 'SET-ME-PLEASE', 'ISSUER': 'http://127.0.0.1:8000/oauth2', 'SECRET_KEY': 'SET-ME-PLEASE'},
    ],
    'JWT_PUBLIC_SIGNING_JWK_SET': None,
    'JWT_AUTH_COOKIE_HEADER_PAYLOAD': 'edx-jwt-cookie-header-payload',
    'JWT_AUTH_COOKIE_SIGNATURE': 'edx-jwt-cookie-signature',
    'JWT_ALGORITHM': 'HS256',
}

CSRF_TRUSTED_ORIGINS = []

# Django 4.0+ uses zoneinfo if this is not set. We can remove this and
# migrate to zoneinfo after Django 4.2 upgrade. See more on following url
# https://docs.djangoproject.com/en/4.2/releases/4.0/#zoneinfo-default-timezone-implementation
USE_DEPRECATED_PYTZ = True
