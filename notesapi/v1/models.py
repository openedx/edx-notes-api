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
    # no indexes here because retrieval is taken care of by ElasticSearch
    user_id = models.CharField(max_length=255, help_text="Anonymized user id, not course specific")
    course_id = models.CharField(max_length=255)
    usage_id = models.CharField(max_length=255, help_text="ID of XBlock where the text comes from")
    quote = models.TextField(default="")
    text = models.TextField(default="", help_text="Student's thoughts on the quote")
    ranges = models.TextField(help_text="JSON, describes position of quote in the source text")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @classmethod
    def create(cls, note_dict):
        """
        Create the note object.
        """
        if not isinstance(note_dict, dict):
            raise ValidationError('Note must be a dictionary.')

        if len(note_dict) == 0:
            raise ValidationError('Note must have a body.')

        ranges = note_dict.get('ranges', list())

        if len(ranges) < 1:
            raise ValidationError('Note must contain at least one range.')

        note_dict['ranges'] = json.dumps(ranges)
        note_dict['user_id'] = note_dict.pop('user', None)

        return cls(**note_dict)

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
        Unlistifies the result and replaces `text` with highlihted one

        Unlistification: ElasticUtils returns data as [{field:value,..}..] which is not what needed.
        this function reverses the effect to get the original value.
        Also filed https://github.com/mozilla/elasticutils/pull/285 to make it unnecessary.
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
