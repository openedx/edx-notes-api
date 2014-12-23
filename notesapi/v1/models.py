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


    def clean(self, json_body):
        """
        Clean the note object or raises a ValidationError.
        """
        if json_body is None:
            raise ValidationError('Note must have a body.')

        try:
            body = json.loads(json_body)
        except (ValueError, TypeError) as error:
            raise ValidationError('Note must have a valid json.')

        if not type(body) is dict:
            raise ValidationError('Note body must be a dictionary.')

        self.text = body.get('text', '')
        self.quote = body.get('quote', '')

        try:
            self.course_id = body['course_id']
            self.usage_id = body['usage_id']
            self.user_id = body['user']
        except KeyError as error:
            raise ValidationError('Note must have a course_id and usage_id and user_id.')

        ranges = body.get('ranges')
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
            'created': self.created,
            'updated': self.updated
        }
