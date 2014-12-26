import traceback
import datetime
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, authentication_classes

from elasticsearch.exceptions import TransportError
from elasticutils import get_es


@api_view(['GET'])
@permission_classes([AllowAny])
def root(request):  # pylint: disable=unused-argument
    """
    Root view.
    """
    return Response({
        "name": "edX Notes API",
        "version": "1"
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def heartbeat(request):  # pylint: disable=unused-argument
    """
    ElasticSearch is reachable and ready to handle requests.
    """
    if get_es().ping():
        return Response({"OK": True})
    else:
        return Response({"OK": False, "check": "es"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def selftest(request):  # pylint: disable=unused-argument
    """
    Manual test endpoint.
    """
    start = datetime.datetime.now()
    try:
        es_status = get_es().info()
    except TransportError:
        return Response(
            {"es_error": traceback.format_exc()},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    end = datetime.datetime.now()
    delta = end - start

    return Response({
        "es": es_status,
        "time_elapsed": int(delta.total_seconds() * 1000)  # In milliseconds.
    })
