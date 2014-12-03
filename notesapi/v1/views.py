import json
from django.http import HttpResponse
from django.conf import settings
from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes

from annotator.annotation import Annotation

from .permissions import HasAccessToken

CREATE_FILTER_FIELDS = ('updated', 'created', 'consumer', 'id')
UPDATE_FILTER_FIELDS = ('updated', 'created', 'user', 'consumer')


@permission_classes((HasAccessToken,))
class AnnotationSearchView(APIView):
    """
    Search annotations.
    """

    def get(self, *args, **kwargs):
        """
        Search annotations.

        This method supports the limit and offset query parameters for paging
        through results.
        """
        params = self.request.QUERY_PARAMS.dict()

        if 'offset' in params:
            kwargs['offset'] = _convert_to_int(params.pop('offset'))

        if 'limit' in params and _convert_to_int(params['limit']) is not None:
            kwargs['limit'] = _convert_to_int(params.pop('limit'))
        elif 'limit' in params and _convert_to_int(params['limit']) is None:  # bad value
            params.pop('limit')
            kwargs['limit'] = settings.RESULTS_DEFAULT_SIZE
        else:
            # default
            kwargs['limit'] = settings.RESULTS_DEFAULT_SIZE

        # All remaining parameters are considered searched fields.
        kwargs['query'] = params

        results = Annotation.search(**kwargs)
        total = Annotation.count(**kwargs)

        return Response({'total': total, 'rows': results})


@permission_classes((HasAccessToken,))
class AnnotationListView(APIView):
    """
    List all annotations or create.
    """

    def get(self, *args, **kwargs):
        """
        Get a list of all annotations.
        """
        self.kwargs['query'] = self.request.QUERY_PARAMS.dict()

        annotations = Annotation.search(**kwargs)

        return Response(annotations)

    def post(self, *args, **kwargs):
        """
        Create a new annotation.

        Returns 400 request if bad payload is sent or it was empty object.
        """
        if 'id' in self.request.DATA:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        filtered_payload = _filter_input(self.request.DATA, CREATE_FILTER_FIELDS)

        if len(filtered_payload) == 0:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        annotation = Annotation(filtered_payload)
        annotation.save(refresh=True)

        location = reverse('api:v1:annotations_detail', kwargs={'annotation_id': annotation['id']})

        return Response(annotation, status=status.HTTP_201_CREATED, headers={'Location': location})


@permission_classes((HasAccessToken,))
class AnnotationDetailView(APIView):
    """
    Annotation detail view.
    """

    UPDATE_FILTER_FIELDS = ('updated', 'created', 'user', 'consumer')

    def get(self, *args, **kwargs):
        """
        Get an existing annotation.
        """
        annotation_id = self.kwargs.get('annotation_id')
        annotation = Annotation.fetch(annotation_id)

        if not annotation:
            return Response(annotation, status=status.HTTP_404_NOT_FOUND)

        return Response(annotation)

    def put(self, *args, **kwargs):
        """
        Update an existing annotation.
        """
        annotation_id = self.kwargs.get('annotation_id')
        annotation = Annotation.fetch(annotation_id)

        if not annotation:
            return Response('Annotation not found! No update performed.', status=status.HTTP_404_NOT_FOUND)

        if self.request.DATA is not None:
            updated = _filter_input(self.request.DATA, UPDATE_FILTER_FIELDS)
            updated['id'] = annotation_id  # use id from URL, regardless of what arrives in JSON payload.

            annotation.update(updated)

            refresh = self.kwargs.get('refresh') != 'false'
            annotation.save(refresh=refresh)

        return Response(annotation)

    def delete(self, *args, **kwargs):
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
    """
    Pop given fields from annotation.
    """
    for field in fields:
        annotation.pop(field, None)

    return annotation


def _convert_to_int(value, default=None):
    """
    Convert given value to int.
    """
    try:
        return int(value or default)
    except ValueError:
        return default
