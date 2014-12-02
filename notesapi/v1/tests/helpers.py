import jwt
from calendar import timegm
from datetime import datetime, timedelta
from django.conf import settings


class MockConsumer(object):
    def __init__(self, key='mockconsumer'):
        self.key = key
        self.secret = 'top-secret'
        self.ttl = 86400


class MockUser(object):
    def __init__(self, id='alice', consumer=None):
        self.id = id
        self.consumer = MockConsumer(consumer if consumer is not None else 'mockconsumer')
        self.is_admin = False


class MockAuthenticator(object):
    def request_user(self, request):
        return MockUser()


def mock_authorizer(*args, **kwargs):
    return True

def get_id_token(user):
    now = datetime.utcnow()
    return jwt.encode({
        'aud': settings.CLIENT_ID,
        'sub': user,
        'iat': timegm(now.utctimetuple()),
        'exp': timegm((now + timedelta(seconds=300)).utctimetuple()),
        }, settings.CLIENT_SECRET)