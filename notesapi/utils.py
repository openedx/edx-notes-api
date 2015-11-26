"""
Paginator and Serializers.
"""

import json

from rest_framework import pagination
from rest_framework import serializers
from rest_framework.response import Response

from notesapi.v1.models import Note


class NotesPaginator(pagination.PageNumberPagination):
    """
    Student Notes Paginator.
    """
    page_size = 10
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        """
        Annotate the response with pagination information.
        """
        return Response({
            'current': self.page.number,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'num_pages': self.page.paginator.num_pages,
            'results': data
        })


class NotesSerializer(serializers.ModelSerializer):
    """
    Student Notes Model Serializer.
    """
    class Meta(object):
        """
        Model Serializer Meta Class.
        """
        model = Note
        exclude = ('user_id',)

    id = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    ranges = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    def get_id(self, note):
        """
        Return string representation of note primary key.
        """
        return str(note.pk)

    def get_user(self, note):
        """
        Return string representation of note user_id.
        """
        return str(note.user_id)

    def get_ranges(self, note):
        """
        Return note ranges.
        """
        return json.loads(note.ranges)

    def get_tags(self, note):
        """
        Return note tags.
        """
        return json.loads(note.tags)


class NotesElasticSearchSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Student Notes Elastic Search Serializer.
    """
    id = serializers.SerializerMethodField()
    created = serializers.DateTimeField()
    updated = serializers.DateTimeField()
    quote = serializers.CharField()
    user = serializers.CharField()
    course_id = serializers.CharField()
    data = serializers.CharField()
    usage_id = serializers.CharField()
    text = serializers.SerializerMethodField()
    ranges = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    def get_id(self, note):
        """
        Return string representation of note primary key.
        """
        return str(note.pk)

    def get_user(self, note):
        """
        Return string representation of note user_id.
        """
        return str(note.user_id)

    def get_text(self, note):
        """
        Return note text.
        """
        if note.highlighted:
            return note.highlighted[0].decode('unicode_escape')
        return note.text

    def get_ranges(self, note):
        """
        Return note ranges.
        """
        return json.loads(note.ranges)

    def get_tags(self, note):
        """
        Return note tags.
        """
        if note.highlighted_tags:
            return json.loads(note.highlighted_tags[0])
        return json.loads(note.tags) if note.tags else []
