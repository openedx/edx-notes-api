import json
from django.http import HttpResponse
from django.conf import settings
from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes

from annotator.annotation import Annotation
from annotator.atoi import atoi

CREATE_FILTER_FIELDS = ('updated', 'created', 'consumer', 'id')
UPDATE_FILTER_FIELDS = ('updated', 'created', 'user', 'consumer')


class AnnotationSearchView(APIView):
    """
    Search annotations.
    """
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        """
        Search annotations.

        This method supports the limit and offset query parameters for paging through results.
        """
        params = request.QUERY_PARAMS.dict()

        if 'offset' in params:
            kwargs['offset'] = atoi(params.pop('offset'), default=None)
        if 'limit' in params:
            kwargs['limit'] = atoi(params.pop('limit'), default=None)

        # All remaining parameters are considered searched fields.
        kwargs['query'] = params

        results = Annotation.search(**kwargs)
        total = Annotation.count(**kwargs)

        return Response({'total': total, 'rows': results})


class AnnotationListView(APIView):
    """
    List all annotations or create.
    """
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        """
        Get a list of all annotations.
        """
        # TODO: get user when auth will be done.
        user = None

        annotations = Annotation.search(user)

        return Response(annotations)

    def post(self, request, *args, **kwargs):
        """
        Create a new annotation.
        """
        annotation = Annotation(_filter_input(request.DATA, CREATE_FILTER_FIELDS))

        refresh = request.QUERY_PARAMS.get('refresh') != u'false'
        annotation.save(refresh=refresh)


        location = reverse('api:v1:annotations_detail', kwargs={'annotation_id': annotation['id']})

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

def _convert_str(value, default=0):
    try:
        return int(v or default)
    except ValueError:
        return default
