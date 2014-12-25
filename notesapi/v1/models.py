import json
from django.db import models
from django.core.exceptions import ValidationError


class Note(models.Model):
    user_id = models.CharField(max_length=255)
    course_id = models.CharField(max_length=255)
    usage_id = models.CharField(max_length=255)
    text = models.TextField(default="")
    quote = models.TextField(default="")
    range_start = models.CharField(max_length=2048)
    range_start_offset = models.IntegerField()
    range_end = models.CharField(max_length=2048)
    range_end_offset = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


    def clean(self, note):
        """
        Clean the note object or raises a ValidationError.
        """
        if note is None:
            raise ValidationError('Note must have a body.')

        if type(note) is not dict:
            raise ValidationError('Note must be a dictionary.')

        self.text = note.get('text', '')
        self.quote = note.get('quote', '')

        try:
            self.course_id = note['course_id']
            self.usage_id = note['usage_id']
            self.user_id = note['user']
        except KeyError as error:
            raise ValidationError('Note must have a course_id and usage_id and user_id.')

        ranges = note.get('ranges')
        if ranges is None or len(ranges) != 1:
            raise ValidationError('Note must contain exactly one range.')

        self.range_start = ranges[0]['start']
        self.range_start_offset = ranges[0]['startOffset']
        self.range_end = ranges[0]['end']
        self.range_end_offset = ranges[0]['endOffset']

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
            'ranges': [{
                'start': self.range_start,
                'startOffset': self.range_start_offset,
                'end': self.range_end,
                'endOffset': self.range_end_offset
            }],
            'created': created,
            'updated': updated,
        }
