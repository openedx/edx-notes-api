import requests
import json
from django.http import HttpResponse
from django.conf import settings
from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes


@api_view(['GET'])
@permission_classes([AllowAny])
def root(request):
    """
    Root view.
    """
    return Response({
        "name": "edX Notes API",
        "version": "1"
    })


class StatusView(APIView):
    """
    Determine if server is alive.
    """
    permission_classes = (AllowAny,)

    def get(self, request):
        """
        Service status.
        """
        return Response()
