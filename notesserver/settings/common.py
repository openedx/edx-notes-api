DEBUG = False
TEMPLATE_DEBUG = False
USE_TZ = True
TIME_ZONE = 'UTC'

SECRET_KEY = '*^owi*4%!%9=#h@app!l^$jz8(c*q297^)4&4yn^#_m#fq=z#l'

ROOT_URLCONF = 'notesserver.urls'

MIDDLEWARE_CLASSES = (
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
)

INSTALLED_APPS = (
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_swagger',
    'corsheaders',
    'django_nose',
)

STATIC_URL = '/static/'

WSGI_APPLICATION = 'notesserver.wsgi.application'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ]
}

CORS_ORIGIN_ALLOW_ALL = True
