import logging
import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.db.models import Q

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from haystack.query import SQ

from notesapi.v1.models import Note
from notesapi.utils import NotesSerializer, NotesElasticSearchSerializer

if not settings.ES_DISABLED:
    from notesserver.highlight import SearchQuerySet

log = logging.getLogger(__name__)


class AnnotationSearchView(GenericAPIView):
    """
    Search annotations.
    """

    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Search annotations in most appropriate storage
        """
        # search in DB when ES is not available or there is no need to bother it
        if settings.ES_DISABLED or 'text' not in self.request.query_params.dict():
            return self.get_from_db(*args, **kwargs)
        else:
            return self.get_from_es(*args, **kwargs)

    def get_from_db(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Search annotations in database
        """
        params = self.request.query_params.dict()
        query = Note.objects.filter(
            **{f: v for (f, v) in params.items() if f in ('course_id', 'usage_id')}
        ).order_by('-updated')

        if 'user' in params:
            query = query.filter(user_id=params['user'])

        if 'text' in params:
            query = query.filter(Q(text__icontains=params['text']) | Q(tags__icontains=params['text']))

        page = self.paginate_queryset(query)
        serializer = NotesSerializer(page, many=True)
        response = self.get_paginated_response(serializer.data)
        return response

    def get_from_es(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Search annotations in ElasticSearch
        """
        params = self.request.query_params.dict()
        query = SearchQuerySet().models(Note).filter(
            **{f: v for (f, v) in params.items() if f in ('user', 'course_id', 'usage_id')}
        )

        if 'text' in params:
            clean_text = query.query.clean(params['text'])
            query = query.filter(SQ(data=clean_text))

        if params.get('highlight'):
            tag = params.get('highlight_tag', 'em')
            klass = params.get('highlight_class')
            opts = {
                'pre_tags': ['<{tag}{klass_str}>'.format(
                    tag=tag,
                    klass_str=' class=\\"{}\\"'.format(klass) if klass else ''
                )],
                'post_tags': ['</{tag}>'.format(tag=tag)],
            }
            query = query.highlight(**opts)

        page = self.paginate_queryset(query)
        serializer = NotesElasticSearchSerializer(page, many=True)
        response = self.get_paginated_response(serializer.data)
        return response


class AnnotationListView(GenericAPIView):
    """
    List all annotations or create.
    """
    serializer_class = NotesSerializer

    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Get a list of all annotations.
        """
        params = self.request.query_params.dict()

        if 'course_id' not in params:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        notes = Note.objects.filter(course_id=params['course_id'], user_id=params['user']).order_by('-updated')
        page = self.paginate_queryset(notes)
        serializer = self.get_serializer(page, many=True)
        response = self.get_paginated_response(serializer.data)
        return response

    def post(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Create a new annotation.

        Returns 400 request if bad payload is sent or it was empty object.
        """
        if 'id' in self.request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            note = Note.create(self.request.data)
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
            note.tags = json.dumps(self.request.data['tags'])
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
