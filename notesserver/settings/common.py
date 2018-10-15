import os
import json
import sys

from notesserver.settings.logger import get_logger_config

DEBUG = False
TEMPLATE_DEBUG = False
DISABLE_TOKEN_CHECK = False
USE_TZ = True
TIME_ZONE = 'UTC'

# This value needs to be overriden in production.
SECRET_KEY = '*^owi*4%!%9=#h@app!l^$jz8(c*q297^)4&4yn^#_m#fq=z#l'
ALLOWED_HOSTS = ['localhost', '*.edx.org']

# ID and Secret used for authenticating JWT Auth Tokens
# should match those configured for `edx-notes` Client in EdX's /admin/oauth2/client/
CLIENT_ID = 'edx-notes-id'
CLIENT_SECRET = 'edx-notes-secret'

ES_DISABLED = False
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'notesserver.highlight.ElasticsearchSearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'notes_index',
    },
}
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

# Number of rows to return by default in result.
RESULTS_DEFAULT_SIZE = 25

# Max number of rows to return in result.
RESULTS_MAX_SIZE = 250

ROOT_URLCONF = 'notesserver.urls'

MIDDLEWARE_CLASSES = (
    'edx_django_utils.cache.middleware.RequestCacheMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'edx_rest_framework_extensions.middleware.RequestMetricsMiddleware',
    'edx_rest_framework_extensions.auth.jwt.middleware.EnsureJWTAuthSettingsMiddleware',
    'edx_rest_framework_extensions.auth.jwt.middleware.JwtAuthCookieMiddleware',
)

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_swagger',
    'corsheaders',
    'haystack',
    'notesapi.v1',
    # additional release utilities to ease automation
    'release_util',
]

STATIC_URL = '/static/'

WSGI_APPLICATION = 'notesserver.wsgi.application'

LOGGING = get_logger_config()

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'notesapi.v1.permissions.HasAccessToken'
    ],
    'DEFAULT_PAGINATION_CLASS': 'notesapi.v1.paginators.NotesPaginator',
}

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
        ]
    }
]

DEFAULT_NOTES_PAGE_SIZE = 25

### Maximum number of allowed notes for each student per course ###
MAX_NOTES_PER_COURSE = 500
