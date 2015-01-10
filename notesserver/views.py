import traceback
import datetime

from django.db import connection
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from elasticsearch.exceptions import TransportError

if not settings.ES_DISABLED:
    from haystack import connections

    def get_es():
        return connections['default'].get_backend().conn
else:
    from mock import Mock

    def get_es():
        return Mock(
            ping=lambda: None,
            info=lambda: {
                'ok': None,
                'status': 203,  # request processed, information may be from another source
            },
        )


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
    ElasticSearch and database are reachable and ready to handle requests.
    """
    try:
        db_status()
    except Exception:
        return Response({"OK": False, "check": "db"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if not get_es().ping():
        return Response({"OK": False, "check": "es"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"OK": True})


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

    try:
        db_status()
        database = "OK"
    except Exception:
        return Response(
            {"db_error": traceback.format_exc()},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    end = datetime.datetime.now()
    delta = end - start

    return Response({
        "es": es_status,
        "db": database,
        "time_elapsed": int(delta.total_seconds() * 1000)  # In milliseconds.
    })


def db_status():
    """
    Return database status.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
