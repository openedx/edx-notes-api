from .common import *
from path import path

TEST_ROOT = path("test_root")

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': TEST_ROOT / "db" / "notesserver.db",
    }
}

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

INSTALLED_APPS = ('django_nose',)

ELASTICSEARCH_URL = 'http://127.0.0.1:9200'
ELASTICSEARCH_INDEX = 'edx-notes-test'
