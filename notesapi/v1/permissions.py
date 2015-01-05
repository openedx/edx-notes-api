import jwt
import logging
from django.conf import settings
from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


class TokenWrongIssuer(Exception):
    pass


class HasAccessToken(BasePermission):
    """
    Allow requests having valid ID Token.

    https://tools.ietf.org/html/draft-ietf-oauth-json-web-token-31
    Expected Token:
    Header {
        "alg": "HS256",
        "typ": "JWT"
    }
    Claims {
        "sub": "<USER_ID>",
        "exp": <EXPIRATION TIMESTAMP>,
        "iat": <ISSUED TIMESTAMP>,
        "aud": "<CLIENT ID"
    }
    Should be signed with CLIENT_SECRET
    """
    def has_permission(self, request, view):
        if getattr(settings, 'DISABLE_TOKEN_CHECK', False):
            return True
        token = request.META.get('HTTP_X_ANNOTATOR_AUTH_TOKEN', '')
        if not token:
            logger.debug("No token found in headers")
            return False
        try:
            data = jwt.decode(token, settings.CLIENT_SECRET)
            auth_user = data['sub']
            if data['aud'] != settings.CLIENT_ID:
                raise TokenWrongIssuer
            for request_field in ('GET', 'POST', 'DATA'):
                if 'user' in getattr(request, request_field):
                    req_user = getattr(request, request_field)['user']
                    if req_user == auth_user:
                        return True
                    else:
                        logger.debug("Token user %s did not match %s user %s", auth_user, request_field, req_user)
                        return False
            logger.info("No user was present to compare in GET, POST or DATA")
        except jwt.ExpiredSignature:
            logger.debug("Token was expired: %s", token)
        except jwt.DecodeError:
            logger.debug("Could not decode token %s", token)
        except TokenWrongIssuer:
            logger.debug("Token has wrong issuer %s", token)
        return False
