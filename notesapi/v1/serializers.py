"""
Serializers for Notes API.
"""

import json

from rest_framework import serializers

from notesapi.v1.models import Note


class NoteSerializer(serializers.ModelSerializer):
    """
    Student Notes Model Serializer.
    """
    class Meta(object):
        """
        Model Serializer Meta Class.
        """
        model = Note
        exclude = ('user_id',)

    id = serializers.CharField(source='pk')
    user = serializers.CharField(source='user_id')
    ranges = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

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
    id = serializers.CharField(source='pk')
    user = serializers.CharField()
    created = serializers.DateTimeField()
    updated = serializers.DateTimeField()
    quote = serializers.CharField()
    course_id = serializers.CharField()
    usage_id = serializers.CharField()
    text = serializers.SerializerMethodField()
    ranges = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    def get_text(self, note):
        """
        Return note text.
        """
        if note.highlighted:
            return note.highlighted[0]
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
