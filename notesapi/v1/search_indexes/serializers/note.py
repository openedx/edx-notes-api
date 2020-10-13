import json

from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from rest_framework import serializers

from ..documents import NoteDocument

__all__ = (
    'NoteDocumentSerializer',
)


class NoteDocumentSerializer(DocumentSerializer):
    """
    Serializer for the Note document.
    """

    text = serializers.SerializerMethodField()
    ranges = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        """
        Meta options.
        """

        document = NoteDocument
        fields = (
            'id',
            'user',
            'course_id',
            'usage_id',
            'quote',
            'created',
            'updated',
        )

    def get_text(self, note):
        """
        Return note text.
        """
        if hasattr(note.meta, 'highlight') and hasattr(note.meta.highlight, 'text'):
            return note.meta.highlight.text[0]
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
        if hasattr(note.meta, 'highlight') and hasattr(note.meta.highlight, 'tags'):
            return [i for i in note.meta.highlight.tags]

        return [i for i in note.tags] if note.tags else []
