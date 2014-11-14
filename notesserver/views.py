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

from annotator.elasticsearch import ElasticSearch
from annotator.annotation import Annotation

CREATE_FILTER_FIELDS = ('updated', 'created', 'consumer', 'id')
UPDATE_FILTER_FIELDS = ('updated', 'created', 'user', 'consumer')

@api_view(['GET'])
@permission_classes([AllowAny])
def root(request):
    """
    Root view.
    """
    return Response({})


class StatusView(APIView):
    """
    Determine if server is alive.
    """
    permission_classes = (AllowAny,)

    def get(self, request):
        """
        Service status.
        """
        return Response({})


class AnnotationListView(APIView):
    """
    List all annotations or create.
    """
    permission_classes = (AllowAny,)

    def get(self, request):
        """
        """
        # TODO: get user.
        user = None

        conn = ElasticSearch()
        annotations = Annotation.search(user)

        return Response(annotations)

    def post(self, request, *args, **kwargs):
        """
        Create a new annotation.
        """
        conn = ElasticSearch()

        if request.DATA is not None:
            annotation = Annotation(_filter_input(request.DATA, CREATE_FILTER_FIELDS))

        refresh = self.kwargs.get('refresh') != 'false'
        annotation.save(refresh=refresh)

        location = reverse('annotations_detail', kwargs={'annotation_id': annotation['id']})

        return Response(annotation, status=status.HTTP_201_CREATED, headers={'Location': location})


class AnnotationDetailView(APIView):
    """
    Annotation detail view.
    """
    permission_classes = (AllowAny,)

    UPDATE_FILTER_FIELDS = ('updated', 'created', 'user', 'consumer')

    def get(self, request, *args, **kwargs):
        """
        Get an existing annotation.
        """
        annotation_id = self.kwargs.get('annotation_id')
        annotation = Annotation.fetch(annotation_id)

        if not annotation:
            return Response(annotation, status=status.HTTP_404_NOT_FOUND)

        return Response(annotation)

    def put(self, request, *args, **kwargs):
        """
        Update an existing annotation.
        """
        annotation_id = self.kwargs.get('annotation_id')
        annotation = Annotation.fetch(annotation_id)

        if not annotation:
            return Response('Annotation not found! No update performed.', status=status.HTTP_404_NOT_FOUND)

        if request.DATA is not None:
            updated = _filter_input(request.DATA, UPDATE_FILTER_FIELDS)
            updated['id'] = annotation_id  # use id from URL, regardless of what arrives in JSON payload.

            annotation.update(updated)

            refresh = self.kwargs.get('refresh') != 'false'
            annotation.save(refresh=refresh)

        return Response(annotation)


    def delete(self, request, *args, **kwargs):
        """
        Delete an annotation.
        """
        annotation_id = self.kwargs.get('annotation_id')
        annotation = Annotation.fetch(annotation_id)

        if not annotation:
            return Response('Annotation not found! No delete performed.', status=status.HTTP_404_NOT_FOUND)

        annotation.delete()

        # Annotation deleted successfully.
        return Response(status=status.HTTP_204_NO_CONTENT)


def _filter_input(annotation, fields):
    for field in fields:
        annotation.pop(field, None)

    return annotation
