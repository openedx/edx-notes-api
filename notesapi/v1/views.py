import logging

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
        params = self.request.QUERY_PARAMS.dict()
        for field in ('text', 'quote'):
            if field in params:
                params[field + "__match"] = params[field]
                del params[field]

        if params.get('highlight'):

            # Currently we do not use highlight_class and highlight_tag in service.
            for param in ['highlight', 'highlight_class', 'highlight_tag']:
                params.pop(param, None)

            results = NoteMappingType.process_result(
                list(
                    note_searcher.query(**params).order_by("-created").values_dict("_source")
                    .highlight("text", pre_tags=['<span>'], post_tags=['</span>'])
                )
            )
        else:
            results = NoteMappingType.process_result(
                list(note_searcher.query(**params).order_by("-created").values_dict("_source"))
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

        if 'course_id' not in params:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            results = Note.objects.filter(course_id=params['course_id'], user_id=params['user'])
        except Note.DoesNotExist:
            pass

        return Response([result.as_dict() for result in results])

    def post(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Create a new annotation.

        Returns 400 request if bad payload is sent or it was empty object.
        """
        if 'id' in self.request.DATA:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            note = Note.create(self.request.DATA)
            note.full_clean()
        except ValidationError as error:
            log.debug(error, exc_info=True)
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

        try:
            note = Note.objects.get(id=note_id)
        except Note.DoesNotExist:
            return Response('Annotation not found!', status=status.HTTP_404_NOT_FOUND)

        return Response(note.as_dict())

    def put(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Update an existing annotation.
        """
        note_id = self.kwargs.get('annotation_id')

        try:
            note = Note.objects.get(id=note_id)
        except Note.DoesNotExist:
            return Response('Annotation not found! No update performed.', status=status.HTTP_404_NOT_FOUND)

        try:
            note.text = self.request.data['text']
            note.full_clean()
        except KeyError as error:
            log.debug(error, exc_info=True)
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

        # Annotation deleted successfully.
        return Response(status=status.HTTP_204_NO_CONTENT)
