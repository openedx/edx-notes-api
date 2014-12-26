import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from notesapi.v1.models import Note, NoteMappingType, note_searcher

log = logging.getLogger(__name__)


class AnnotationSearchView(APIView):
    """
    Search annotations.
    """

    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Search annotations.
        """
        params = {}
        for k, v in self.request.QUERY_PARAMS.dict().items():
            params[k] = v.lower()
        results = NoteMappingType.process_result(
            list(note_searcher.filter(**params).order_by("-created").values_dict("_source"))
        )

        return Response({'total': len(results), 'rows': results})


class AnnotationListView(APIView):
    """
    List all annotations or create.
    """

    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Get a list of all annotations.
        """
        params = self.request.QUERY_PARAMS.dict()
        results = NoteMappingType.process_result(
            list(note_searcher.filter(**params).values_dict("_source"))
        )

        return Response(results)

    def post(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Create a new annotation.

        Returns 400 request if bad payload is sent or it was empty object.
        """
        if 'id' in self.request.DATA:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        note = Note()

        try:
            note.clean(self.request.DATA)
        except ValidationError as error:
            log.debug(error)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        note.save()

        location = reverse('api:v1:annotations_detail', kwargs={'annotation_id': note.id})

        return Response(note.as_dict(), status=status.HTTP_201_CREATED, headers={'Location': location})


class AnnotationDetailView(APIView):
    """
    Annotation detail view.
    """

    UPDATE_FILTER_FIELDS = ('updated', 'created', 'user', 'consumer')

    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Get an existing annotation.
        """
        note_id = self.kwargs.get('annotation_id')
        results = NoteMappingType.process_result(
            list(note_searcher.filter(id=note_id).values_dict("_source"))
        )

        if not results:
            return Response(False, status=status.HTTP_404_NOT_FOUND)

        return Response(results[0])

    def put(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Update an existing annotation.
        """
        note_id = self.kwargs.get('annotation_id')

        try:
            note = Note.objects.get(id=note_id)
        except Note.DoesNotExist:
            return Response('Annotation not found! No update performed.', status=status.HTTP_404_NOT_FOUND)

        # changing user_id is not permitted
        if note.user_id != self.request.DATA['user']:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            note.clean(self.request.DATA)
        except ValidationError as e:
            log.debug(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        note.save()

        return Response(note.as_dict())

    def delete(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Delete an annotation.
        """
        note_id = self.kwargs.get('annotation_id')

        try:
            note = Note.objects.get(id=note_id)
        except Note.DoesNotExist:
            return Response('Annotation not found! No update performed.', status=status.HTTP_404_NOT_FOUND)

        note.delete()
        es_note.delete()

        # FIXME

        # Annotation deleted successfully.
        return Response(status=status.HTTP_204_NO_CONTENT)


def _convert_to_int(value, default=None):
    """
    Convert given value to int.
    """
    try:
        return int(value or default)
    except ValueError:
        return default
