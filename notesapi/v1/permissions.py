import logging

import jwt
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
        "sub": "<USER ANONYMOUS ID>",
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
            data = jwt.decode(token, settings.CLIENT_SECRET, audience=settings.CLIENT_ID)
            auth_user = data['sub']
            user_found = False
            for request_field in ('GET', 'POST', 'data'):
                if 'user' in getattr(request, request_field):
                    req_user = getattr(request, request_field)['user']
                    if req_user == auth_user:
                        user_found = True
                        # but we do not break or return here,
                        # because `user` may be present in more than one field (GET, POST)
                        # and we must make sure that all of them are correct
                    else:
                        logger.debug("Token user %s did not match %s user %s", auth_user, request_field, req_user)
                        return False
            if user_found:
                return True
            else:
                logger.info("No user was present to compare in GET, POST or DATA")
        except jwt.ExpiredSignature:
            logger.debug("Token was expired: %s", token)
        except jwt.DecodeError:
            logger.debug("Could not decode token %s", token)
        except jwt.InvalidAudienceError:
            logger.debug("Token has wrong issuer %s", token)
        return False
