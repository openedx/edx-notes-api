from rest_framework.permissions import BasePermission
from provider.oauth2.models import AccessToken

class HasAccessToken(BasePermission):
    """
    Allow requests having valid AccessToken.
    """
    def has_permission(self, request, view):
        try:
            # expected HTTP Header "Authorization: Bearer TOKEN"
            AccessToken.objects.get_token(request.META["HTTP_AUTHORIZATION"].split()[1])
            return True
        except AccessToken.DoesNotExist:
            return False
