from calendar import timegm
from datetime import UTC, datetime, timedelta

import jwt
from django.conf import settings


def get_id_token(user):
    now = datetime.now(UTC)
    return jwt.encode({
        'aud': settings.CLIENT_ID,
        'sub': user,
        'iat': timegm(now.utctimetuple()),
        'exp': timegm((now + timedelta(seconds=300)).utctimetuple()),
    }, settings.CLIENT_SECRET)
