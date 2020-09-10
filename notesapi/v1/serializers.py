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
