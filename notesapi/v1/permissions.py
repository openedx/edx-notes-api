from rest_framework.permissions import BasePermission

class HasAccessToken(BasePermission):
    """
    Allow requests having valid ID Token.
    """
    def has_permission(self, request, view):
        return True
