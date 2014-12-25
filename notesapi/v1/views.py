import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from annotator.annotation import Annotation
from notesapi.v1.models import Note

CREATE_FILTER_FIELDS = ('updated', 'created', 'consumer', 'id')
UPDATE_FILTER_FIELDS = ('updated', 'created', 'user', 'consumer')

log = logging.getLogger(__name__)


class AnnotationSearchView(APIView):
    """
    Search annotations.
    """

    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
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


class AnnotationListView(APIView):
    """
    List all annotations or create.
    """

    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Get a list of all annotations.
        """
        self.kwargs['query'] = self.request.QUERY_PARAMS.dict()

        annotations = Annotation.search(**kwargs)

        return Response(annotations)

    def post(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Create a new annotation.

        Returns 400 request if bad payload is sent or it was empty object.
        """
        if 'id' in self.request.DATA:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        filtered_payload = _filter_input(self.request.DATA, CREATE_FILTER_FIELDS)

        if len(filtered_payload) == 0:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        note = Note()

        try:
            note.clean(filtered_payload)
        except ValidationError as error:
            log.debug(error)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        note.save()

        annotation = Annotation(filtered_payload)
        annotation.save(refresh=True)

        location = reverse('api:v1:annotations_detail', kwargs={'annotation_id': annotation['id']})

        return Response(annotation, status=status.HTTP_201_CREATED, headers={'Location': location})


class AnnotationDetailView(APIView):
    """
    Annotation detail view.
    """

    UPDATE_FILTER_FIELDS = ('updated', 'created', 'user', 'consumer')

    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Get an existing annotation.
        """
        annotation_id = self.kwargs.get('annotation_id')
        annotation = Annotation.fetch(annotation_id)

        if not annotation:
            return Response(annotation, status=status.HTTP_404_NOT_FOUND)

        return Response(annotation)

    def put(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Update an existing annotation.
        """
        note_id = self.kwargs.get('annotation_id')

        try:
            note = Note.objects.get(id=note_id)
        except Note.DoesNotExist:
            return Response('Annotation not found! No update performed.', status=status.HTTP_404_NOT_FOUND)

        es_note = Annotation.fetch(note_id)

        if not es_note:
            return Response('Annotation not found! No update performed.', status=status.HTTP_404_NOT_FOUND)

        if note.user_id != es_note['user_id']:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        filtered_payload = _filter_input(self.request.DATA, UPDATE_FILTER_FIELDS)

        # use id from URL, regardless of what arrives in JSON payload.
        filtered_payload['id'] = note_id
        es_note.update(updated)

        try:
            note.clean(filtered_payload)
        except ValidationError as e:
            log.debug(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        note.save()

        refresh = self.kwargs.get('refresh') != 'false'
        es_note.save(refresh=refresh)

        return Response(es_note)

    def delete(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Delete an annotation.
        """
        note_id = self.kwargs.get('annotation_id')

        try:
            note = Note.objects.get(id=note_id)
        except Note.DoesNotExist:
            return Response('Annotation not found! No update performed.', status=status.HTTP_404_NOT_FOUND)

        es_note = Annotation.fetch(note_id)

        if not es_note:
            return Response('Annotation not found! No delete performed.', status=status.HTTP_404_NOT_FOUND)

        note.delete()
        es_note.delete()

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
