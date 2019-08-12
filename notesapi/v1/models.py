import json

from django.core.exceptions import ValidationError
from django.db import models


class Note(models.Model):
    """
    Annotation model.

    .. pii:: Stores 'text' and 'tags' about a particular course quote.
    .. pii_types:: other
    .. pii_retirement:: local_api, consumer_api
   """
    user_id = models.CharField(max_length=255, db_index=True, help_text="Anonymized user id, not course specific")
    course_id = models.CharField(max_length=255, db_index=True)
    usage_id = models.CharField(max_length=255, help_text="ID of XBlock where the text comes from")
    quote = models.TextField(default="")
    text = models.TextField(default="", blank=True, help_text="Student's thoughts on the quote")
    ranges = models.TextField(help_text="JSON, describes position of quote in the source text")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    tags = models.TextField(help_text="JSON, list of comma-separated tags", default="[]")

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
        note_dict['tags'] = json.dumps(note_dict.get('tags', list()), ensure_ascii=False)

        return cls(**note_dict)
