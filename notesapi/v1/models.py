import json
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db.models import signals
from django.dispatch import receiver
from elasticutils.contrib.django import Indexable, MappingType


class Note(models.Model):
    """
    Annotation model.
    """
    user_id = models.CharField(max_length=255, help_text="Anonymized user id, not course specific")
    course_id = models.CharField(max_length=255)
    usage_id = models.CharField(max_length=255, help_text="ID of XBlock where the text comes from")
    quote = models.TextField(default="")
    text = models.TextField(default="", help_text="Student's thoughts on the quote")
    ranges = models.TextField(default="", help_text="JSON, describes position of quote in the source text")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def clean(self, note):
        """
        Clean the note object or raises a ValidationError.
        """
        if not isinstance(note, dict):
            raise ValidationError('Note must be a dictionary.')

        if len(note) == 0:
            raise ValidationError('Note must have a body.')

        self.text = note.get('text', '')
        self.quote = note.get('quote', '')

        try:
            self.course_id = note['course_id']
            self.usage_id = note['usage_id']
            if not self.user_id:
                self.user_id = note['user']
        except KeyError as error:
            raise ValidationError('Note must have a course_id and usage_id and user_id.')

        ranges = note.get('ranges')
        if not ranges:
            raise ValidationError('Note must contain at least one range.')

        self.ranges = json.dumps(ranges)

    def as_dict(self):
        """
        Returns the note object as a dictionary.
        """
        created = self.created.isoformat() if self.created else None
        updated = self.updated.isoformat() if self.updated else None

        return {
            'id': self.pk,
            'user': self.user_id,
            'course_id': self.course_id,
            'usage_id': self.usage_id,
            'text': self.text,
            'quote': self.quote,
            'ranges': json.loads(self.ranges),
            'created': created,
            'updated': updated,
        }


@receiver(signals.post_save, sender=Note)
def update_in_index(sender, instance, **kwargs):
    if settings.ES_DISABLED:
        return
    NoteMappingType.index(instance.as_dict(), id_=instance.id, overwrite_existing=True)


@receiver(signals.post_delete, sender=Note)
def delete_in_index(sender, instance, **kwargs):
    if settings.ES_DISABLED:
        return
    NoteMappingType.unindex(id_=instance.id)


class NoteMappingType(MappingType, Indexable):
    """
    Mapping type for Note.
    """

    @classmethod
    def get_model(cls):
        return Note

    @classmethod
    def get_mapping(cls):
        """
        Returns an Elasticsearch mapping for Note MappingType
        """
        charfield = {'type': 'string', 'index': 'not_analyzed', 'store': True}
        return {
            'properties': {
                'id': charfield,
                'user': charfield,
                'course_id': charfield,
                'usage_id': charfield,
                'text': {'type': 'string', 'analyzer': 'snowball', 'store': True},
                'quote': {'type': 'string', 'analyzer': 'snowball', 'store': True},
                'created': {'type': 'date', 'store': True},
                'updated': {'type': 'date', 'store': True},
            }
        }

    @classmethod
    def extract_document(cls, obj_id, obj=None):
        """
        Converts this instance into an Elasticsearch document.
        """
        if obj is None:
            obj = cls.get_model().objects.get(pk=obj_id)

        return obj.as_dict()

    @staticmethod
    def process_result(data):
        """
<<<<<<< HEAD
        Prepares result for response.

        Also prepares ranges field and highlighting.
=======
        Unlistifies the result and replaces `text` with highlihted one

        Unlistification: ElasticUtils returns data as [{field:value,..}..] which is not what needed.
        this function reverses the effect to get the original value.
        Also filed https://github.com/mozilla/elasticutils/pull/285 to make it unnecessary.
>>>>>>> specify ElastiUtils more precisely, add docstrings
        """
        for i, item in enumerate(data):
            if isinstance(item, dict):
                for k, v in item.items():
                    if k != 'ranges' and isinstance(v, list) and len(v) > 0:
                        data[i][k] = v[0]

                    # Substitute the value of text field by highlighted result.
                    if len(item.es_meta.highlight) and k == 'text':
                        data[i][k] = item.es_meta.highlight['text'][0]

        return data

note_searcher = NoteMappingType.search()
