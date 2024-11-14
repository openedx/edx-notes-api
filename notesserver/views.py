import datetime
import traceback

from django.db import connection
from django.http import JsonResponse
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

try:
    import newrelic.agent
except ImportError:  # pragma: no cover
    newrelic = None  # pylint: disable=invalid-name

from notesapi.v1.views import get_annotation_search_view_class
from notesapi.v1.views import SearchViewRuntimeError


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


@api_view(['GET'])
@permission_classes([AllowAny])
def robots(request):
    """
    robots.txt
    """
    return HttpResponse("User-agent: * Disallow: /", content_type="text/plain")


@api_view(['GET'])
@permission_classes([AllowAny])
def heartbeat(request):
    """
    ElasticSearch and database are reachable and ready to handle requests.
    """
    if newrelic:  # pragma: no cover
        newrelic.agent.ignore_transaction()
    try:
        db_status()
    except Exception:  # pylint: disable=broad-exception-caught
        return JsonResponse({"OK": False, "check": "db"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        get_annotation_search_view_class().heartbeat()
    except SearchViewRuntimeError as e:
        return JsonResponse({"OK": False, "check": e.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JsonResponse({"OK": True}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def selftest(request):
    """
    Manual test endpoint.
    """
    start = datetime.datetime.now()

    response = {}
    try:
        response.update(get_annotation_search_view_class().selftest())
    except SearchViewRuntimeError as e:
        return Response(
            e.args[0],
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    try:
        db_status()
        response["db"] = "OK"
    except Exception:  # pylint: disable=broad-exception-caught
        return Response(
            {"db_error": traceback.format_exc()},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    end = datetime.datetime.now()
    delta = end - start
    response["time_elapsed"] = int(delta.total_seconds() * 1000)  # In milliseconds.

    return Response(response)


def db_status():
    """
    Return database status.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
