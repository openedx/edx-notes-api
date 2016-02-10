import logging
import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import ugettext_noop

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from haystack.query import SQ

from notesapi.v1.models import Note

if not settings.ES_DISABLED:
    from notesserver.highlight import SearchQuerySet

log = logging.getLogger(__name__)


class AnnotationsLimitReachedError(Exception):
    """
    Exception when trying to create more than allowed annotations
    """
    pass


class AnnotationSearchView(APIView):
    """
    Search annotations.
    """
    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Search annotations in most appropriate storage
        """
        # search in DB when ES is not available or there is no need to bother it
        if settings.ES_DISABLED or 'text' not in self.request.query_params.dict():
            results = self.get_from_db(*args, **kwargs)
        else:
            results = self.get_from_es(*args, **kwargs)
        return Response({'total': len(results), 'rows': results})

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

        return [note.as_dict() for note in query]

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

        results = []
        for item in query:
            note_dict = item.get_stored_fields()
            note_dict['ranges'] = json.loads(item.ranges)
            # If ./manage.py rebuild_index has not been run after tags were added, item.tags will be None.
            note_dict['tags'] = json.loads(item.tags) if item.tags else []
            note_dict['id'] = str(item.pk)
            if item.highlighted:
                note_dict['text'] = item.highlighted[0].decode('unicode_escape')
            if item.highlighted_tags:
                note_dict['tags'] = json.loads(item.highlighted_tags[0])
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
        params = self.request.query_params.dict()

        if 'course_id' not in params:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        results = Note.objects.filter(course_id=params['course_id'], user_id=params['user']).order_by('-updated')

        return Response([result.as_dict() for result in results])

    def post(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Create a new annotation.

        Returns 400 request if bad payload is sent or it was empty object.
        """
        if not self.request.data or 'id' in self.request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            if Note.objects.filter(
                    user_id=self.request.data['user'], course_id=self.request.data['course_id']
            ).count() >= settings.MAX_ANNOTATIONS_PER_COURSE:
                raise AnnotationsLimitReachedError

            note = Note.create(self.request.data)
            note.full_clean()
        except ValidationError as error:
            log.debug(error, exc_info=True)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except AnnotationsLimitReachedError:
            error_message = ugettext_noop(
                u'You can create up to {max_num_annotations_per_course} notes.'
                u' You must remove some notes before you can add new ones.'
            ).format(max_num_annotations_per_course=settings.MAX_ANNOTATIONS_PER_COURSE)
            log.info(
                u'Attempted to create more than %s annotations',
                settings.MAX_ANNOTATIONS_PER_COURSE
            )
            return Response({
                'error_msg': error_message
            }, status=status.HTTP_400_BAD_REQUEST)

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
