from rest_framework.permissions import BasePermission
from provider.oauth2.models import AccessToken

class HasAccessToken(BasePermission):
    """
    Allow requests having valid AccessToken.
    """
    def has_permission(self, request, view):
        try:
            # expected HTTP Header "X-Annotator-Auth-Token: TOKEN"
            AccessToken.objects.get_token(request.META["HTTP-X-ANNOTATOR-AUTH-TOKEN"].strip())
            return True
        except AccessToken.DoesNotExist:
            return False
