import logging
import json

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from notesapi.v1.models import Note

if not settings.ES_DISABLED:
    from haystack.query import SearchQuerySet

log = logging.getLogger(__name__)


class AnnotationSearchView(APIView):
    """
    Search annotations.
    """
    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        if settings.ES_DISABLED:
            results = self.get_from_db(*args, **kwargs)
        else:
            results = self.get_from_es(*args, **kwargs)
        return Response({'total': len(results), 'rows': results})

    def get_from_db(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Search annotations in database
        """
        params = self.request.QUERY_PARAMS.dict()
        query = Note.objects.filter(
            **{f: v for (f, v) in params.items() if f in ('course_id', 'usage_id')}
        ).order_by('-updated')

        if 'user' in params:
            query = query.filter(user_id=params['user'])

        if 'text' in params:
            query = query.filter(text__icontains=params['text'])

        return [note.as_dict() for note in query]

    def get_from_es(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Search annotations in ElasticSearch
        """
        params = self.request.QUERY_PARAMS.dict()
        query = SearchQuerySet().models(Note).filter(
            **{f: v for (f, v) in params.items() if f in ('user', 'course_id', 'usage_id', 'text')}
        ).order_by('-updated')

        if params.get('highlight'):
            query = query.highlight()

        results = []
        for item in query:
            note_dict = item.get_stored_fields()
            note_dict['ranges'] = json.loads(item.ranges)
            note_dict['id'] = int(item.pk)
            if params.get('highlight'):
                note_dict['text'] = item.highlighted[0]
            results.append(note_dict)

        return results


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
