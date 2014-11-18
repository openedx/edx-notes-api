from .common import *
from path import path

TEST_ROOT = path("test_root")

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': TEST_ROOT / "db" / "notesserver.db",
    }
}
