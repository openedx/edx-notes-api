ROOT_URLCONF = 'notesserver.urls'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware'
)

INSTALLED_APPS = (
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_swagger',
)

STATIC_URL = '/static/'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ]
}

WSGI_APPLICATION = 'notesserver.wsgi.application'
