import json

from django.conf import settings
from django_elasticsearch_dsl import Document, fields, Index

from notesapi.v1.models import Note
from .analyzers import case_insensitive_keyword, html_strip

__all__ = ('NoteDocument',)

NOTE_INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES[__name__])


@NOTE_INDEX.doc_type
class NoteDocument(Document):
    id = fields.IntegerField(attr='id')
    user = fields.KeywordField(attr='user_id')
    course_id = fields.KeywordField()
    usage_id = fields.KeywordField()
    quote = fields.TextField(analyzer=html_strip)
    text = fields.TextField(analyzer=html_strip)
    ranges = fields.KeywordField()
    created = fields.DateField()
    updated = fields.DateField()
    tags = fields.TextField(multi=True, analyzer=case_insensitive_keyword)

    def prepare_data(self, instance):
        """
        Prepare data.
        """
        return '{0}{1}'.format(instance.text, instance.tags)

    def prepare_tags(self, instance):
        return json.loads(instance.tags)

    class Django:
        model = Note

    class Meta:
        parallel_indexing = True
        queryset_pagination = 50
