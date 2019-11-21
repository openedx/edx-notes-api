import json
import logging

import newrelic.agent
from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.db.models import Q
from django.utils.translation import ugettext as _
from haystack.query import SQ
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from notesapi.v1.models import Note
from notesapi.v1.serializers import (NotesElasticSearchSerializer,
                                     NoteSerializer)

if not settings.ES_DISABLED:
    from notesserver.highlight import SearchQuerySet

log = logging.getLogger(__name__)


class AnnotationsLimitReachedError(Exception):
    """
    Exception when trying to create more than allowed annotations
    """
    pass


class AnnotationSearchView(GenericAPIView):
    """
    **Use Case**

        * Search and return a list of annotations for a user.

            The annotations are always sorted in descending order by updated date.

            Response is paginated by default except usage_id based search.

            Each page in the list contains 25 annotations by default. The page
            size can be altered by passing parameter "page_size=<page_size>".

            Http400 is returned if the format of the request is not correct.

    **Search Types**

        * There are two types of searches one can perform

            * Database

                If ElasticSearch is disabled or text query param is not present.

            * ElasticSearch

    **Example Requests**

        GET /api/v1/search/
        GET /api/v1/search/?course_id={course_id}&user={user_id}
        GET /api/v1/search/?course_id={course_id}&user={user_id}&usage_id={usage_id}
        GET /api/v1/search/?course_id={course_id}&user={user_id}&usage_id={usage_id}&usage_id={usage_id} ...

    **Query Parameters for GET**

        All the parameters are optional.

        * course_id: Id of the course.

        * user: Anonymized user id.

        * usage_id: The identifier string of the annotations XBlock.

        * text: Student's thoughts on the quote

        * highlight: dict. Only used when search from ElasticSearch. It contains two keys:

            * highlight_tag: String. HTML tag to be used for highlighting the text. Default is "em"

            * highlight_class: String. CSS class to be used for highlighting the text.

    **Response Values for GET**

        * count: The number of annotations in a course.

        * next: The URI to the next page of annotations.

        * previous: The URI to the previous page of annotations.

        * current: Current page number.

        * num_pages: The number of pages listing annotations.

        * results: A list of annotations returned. Each collection in the list contains these fields.

            * id: String. The primary key of the note.

            * user: String. Anonymized id of the user.

            * course_id: String. The identifier string of the annotations course.

            * usage_id: String. The identifier string of the annotations XBlock.

            * quote: String. Quoted text.

            * text: String. Student's thoughts on the quote.

            * ranges: List. Describes position of quote.

            * tags: List. Comma separated tags.

            * created: DateTime. Creation datetime of annotation.

            * updated: DateTime. When was the last time annotation was updated.
    """
    params = {}
    query_params = {}
    search_with_usage_id = False

    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Search annotations in most appropriate storage
        """
        self.query_params = {}
        self.search_with_usage_id = False
        self.params = self.request.query_params.dict()

        usage_ids = self.request.query_params.getlist('usage_id')
        if len(usage_ids) > 0:
            self.search_with_usage_id = True
            self.query_params['usage_id__in'] = usage_ids

        if 'course_id' in self.params:
            self.query_params['course_id'] = self.params['course_id']

        # search in DB when ES is not available or there is no need to bother it
        if settings.ES_DISABLED or 'text' not in self.params:
            if 'user' in self.params:
                self.query_params['user_id'] = self.params['user']
            return self.get_from_db(*args, **kwargs)
        else:
            if 'user' in self.params:
                self.query_params['user'] = self.params['user']
            return self.get_from_es(*args, **kwargs)

    def get_from_db(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Search annotations in database.
        """
        query = Note.objects.filter(**self.query_params).order_by('-updated')

        if 'text' in self.params:
            query = query.filter(Q(text__icontains=self.params['text']) | Q(tags__icontains=self.params['text']))

        # Do not send paginated result if usage id based search.
        if self.search_with_usage_id:
            serializer = NoteSerializer(query, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        page = self.paginate_queryset(query)
        serializer = NoteSerializer(page, many=True)
        response = self.get_paginated_response(serializer.data)
        return response

    def get_from_es(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Search annotations in ElasticSearch.
        """
        query = SearchQuerySet().models(Note).filter(**self.query_params)

        if 'text' in self.params:
            clean_text = query.query.clean(self.params['text'])
            query = query.filter(SQ(data=clean_text))

        if self.params.get('highlight'):
            opts = {
                'pre_tags': ['{elasticsearch_highlight_start}'],
                'post_tags': ['{elasticsearch_highlight_end}'],
                'number_of_fragments': 0
            }
            query = query.highlight(**opts)

        # Do not send paginated result if usage id based search.
        if self.search_with_usage_id:
            serializer = NotesElasticSearchSerializer(query, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        page = self.paginate_queryset(query)
        serializer = NotesElasticSearchSerializer(page, many=True)
        response = self.get_paginated_response(serializer.data)
        return response


class AnnotationRetireView(GenericAPIView):
    """
    Administrative functions for the notes service.
    """

    def post(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Delete all annotations for a user.
        """
        params = self.request.data
        if 'user' not in params:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        Note.objects.filter(user_id=params['user']).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnnotationListView(GenericAPIView):
    """
        **Use Case**

            * Get a paginated list of annotations for a user.

                The annotations are always sorted in descending order by updated date.

                Each page in the list contains 25 annotations by default. The page
                size can be altered by passing parameter "page_size=<page_size>".

                HTTP 400 Bad Request: The format of the request is not correct.

            * Create a new annotation for a user.

                HTTP 400 Bad Request: The format of the request is not correct, or the maximum number of notes for a
                user has been reached.

                HTTP 201 Created: Success.

            * Delete all annotations for a user.

                HTTP 400 Bad Request: The format of the request is not correct.

                HTTP 200 OK: Either annotations from the user were deleted, or no annotations for the user were found.

        **Example Requests**

            GET /api/v1/annotations/?course_id={course_id}&user={user_id}

            POST /api/v1/annotations/
            user={user_id}&course_id={course_id}&usage_id={usage_id}&ranges={ranges}&quote={quote}

            DELETE /api/v1/annotations/
            user={user_id}

        **Query Parameters for GET**

            Both the course_id and user must be provided.

            * course_id: Id of the course.

            * user: Anonymized user id.

        **Response Values for GET**

            * count: The number of annotations in a course.

            * next: The URI to the next page of annotations.

            * previous: The URI to the previous page of annotations.

            * current: Current page number.

            * num_pages: The number of pages listing annotations.

            * results:  A list of annotations returned. Each collection in the list contains these fields.

                * id: String. The primary key of the note.

                * user: String. Anonymized id of the user.

                * course_id: String. The identifier string of the annotations course.

                * usage_id: String. The identifier string of the annotations XBlock.

                * quote: String. Quoted text.

                * text: String. Student's thoughts on the quote.

                * ranges: List. Describes position of quote.

                * tags: List. Comma separated tags.

                * created: DateTime. Creation datetime of annotation.

                * updated: DateTime. When was the last time annotation was updated.

        **Form-encoded data for POST**

            user, course_id, usage_id, ranges and quote fields must be provided.

        **Response Values for POST**

            * id: String. The primary key of the note.

            * user: String. Anonymized id of the user.

            * course_id: String. The identifier string of the annotations course.

            * usage_id: String. The identifier string of the annotations XBlock.

            * quote: String. Quoted text.

            * text: String. Student's thoughts on the quote.

            * ranges: List. Describes position of quote in the source text.

            * tags: List. Comma separated tags.

            * created: DateTime. Creation datetime of annotation.

            * updated: DateTime. When was the last time annotation was updated.

        **Form-encoded data for DELETE**

            * user: Anonymized user id.

        **Response Values for DELETE**

            * no content.

    """

    serializer_class = NoteSerializer

    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Get paginated list of all annotations.
        """
        params = self.request.query_params.dict()

        if 'course_id' not in params:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if 'user' not in params:
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
        if not self.request.data or 'id' in self.request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            total_notes = Note.objects.filter(
                    user_id=self.request.data['user'], course_id=self.request.data['course_id']
            ).count()
            if total_notes >= settings.MAX_NOTES_PER_COURSE:
                raise AnnotationsLimitReachedError

            note = Note.create(self.request.data)
            note.full_clean()

            # Gather metrics for New Relic so we can slice data in New Relic Insights
            newrelic.agent.add_custom_parameter('notes.count', total_notes)
        except ValidationError as error:
            log.debug(error, exc_info=True)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except AnnotationsLimitReachedError:
            error_message = _(
                u'You can create up to {max_num_annotations_per_course} notes.'
                u' You must remove some notes before you can add new ones.'
            ).format(max_num_annotations_per_course=settings.MAX_NOTES_PER_COURSE)
            log.info(
                u'Attempted to create more than %s annotations',
                settings.MAX_NOTES_PER_COURSE
            )

            return Response({
                'error_msg': error_message
            }, status=status.HTTP_400_BAD_REQUEST)

        note.save()

        location = reverse('api:v1:annotations_detail', kwargs={'annotation_id': note.id})
        serializer = NoteSerializer(note)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers={'Location': location})


class AnnotationDetailView(APIView):
    """
        **Use Case**

            * Get a single annotation.

            * Update an annotation.

            * Delete an annotation.

        **Example Requests**

            GET /api/v1/annotations/<annotation_id>
            PUT /api/v1/annotations/<annotation_id>
            DELETE /api/v1/annotations/<annotation_id>

        **Query Parameters for GET**

            HTTP404 is returned if annotation_id is missing.

            * annotation_id: Annotation id

        **Query Parameters for PUT**

            HTTP404 is returned if annotation_id is missing and HTTP400 is returned if text and tags are missing.

            * annotation_id: String. Annotation id

            * text: String. Text to be updated

            * tags: List. Tags to be updated

        **Query Parameters for DELETE**

            HTTP404 is returned if annotation_id is missing.

            * annotation_id: Annotation id

        **Response Values for GET**

            * id: String. The primary key of the note.

            * user: String. Anonymized id of the user.

            * course_id: String. The identifier string of the annotations course.

            * usage_id: String. The identifier string of the annotations XBlock.

            * quote: String. Quoted text.

            * text: String. Student's thoughts on the quote.

            * ranges: List. Describes position of quote.

            * tags: List. Comma separated tags.

            * created: DateTime. Creation datetime of annotation.

            * updated: DateTime. When was the last time annotation was updated.

        **Response Values for PUT**

            * same as GET with updated values

        **Response Values for DELETE**

            * HTTP_204_NO_CONTENT is returned
    """

    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Get an existing annotation.
        """
        note_id = self.kwargs.get('annotation_id')

        try:
            note = Note.objects.get(id=note_id)
        except Note.DoesNotExist:
            return Response('Annotation not found!', status=status.HTTP_404_NOT_FOUND)

        serializer = NoteSerializer(note)
        return Response(serializer.data)

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

        serializer = NoteSerializer(note)
        return Response(serializer.data)

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
