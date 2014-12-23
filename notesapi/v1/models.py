import json
from django.db import models
from django.core.exceptions import ValidationError
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locations import BlockUsageLocator


def _strip_object(key):
    """
    Strips branch and version info if the given key supports those attributes.
    """
    if hasattr(key, 'version_agnostic') and hasattr(key, 'for_branch'):
        return key.for_branch(None).version_agnostic()
    else:
        return key


def _strip_value(value, lookup='exact'):
    """
    Helper function to remove the branch and version information from the given value,
    which could be a single object or a list.
    """
    if lookup == 'in':
        stripped_value = [_strip_object(el) for el in value]
    else:
        stripped_value = _strip_object(value)
    return stripped_value


class OpaqueKeyField(models.CharField):
    """
    A django field for storing OpaqueKeys.

    The baseclass will return the value from the database as a string, rather than an instance
    of an OpaqueKey, leaving the application to determine which key subtype to parse the string
    as.

    Subclasses must specify a KEY_CLASS attribute, in which case the field will use :meth:`from_string`
    to parse the key string, and will return an instance of KEY_CLASS.
    """
    description = "An OpaqueKey object, saved to the DB in the form of a string."

    __metaclass__ = models.SubfieldBase

    Empty = object()
    KEY_CLASS = None

    def __init__(self, *args, **kwargs):
        if self.KEY_CLASS is None:
            raise ValueError('Must specify KEY_CLASS in OpaqueKeyField subclasses')

        super(OpaqueKeyField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if value is self.Empty or value is None:
            return None

        assert isinstance(value, (basestring, self.KEY_CLASS))
        if value == '':
            # handle empty string for models being created w/o fields populated
            return None

        if isinstance(value, basestring):
            return self.KEY_CLASS.from_string(value)
        else:
            return value

    def get_prep_lookup(self, lookup, value):
        if lookup == 'isnull':
            raise TypeError('Use {0}.Empty rather than None to query for a missing {0}'.format(self.__class__.__name__))

        return super(OpaqueKeyField, self).get_prep_lookup(
            lookup,
            # strip key before comparing
            _strip_value(value, lookup)
        )

    def get_prep_value(self, value):
        if value is self.Empty or value is None:
            return ''  # CharFields should use '' as their empty value, rather than None

        assert isinstance(value, self.KEY_CLASS)
        return unicode(_strip_value(value))

    def validate(self, value, model_instance):
        """Validate Empty values, otherwise defer to the parent"""
        # raise validation error if the use of this field says it can't be blank but it is
        if not self.blank and value is self.Empty:
            raise ValidationError(self.error_messages['blank'])
        else:
            return super(OpaqueKeyField, self).validate(value, model_instance)

    def run_validators(self, value):
        """Validate Empty values, otherwise defer to the parent"""
        if value is self.Empty:
            return

        return super(OpaqueKeyField, self).run_validators(value)


class CourseKeyField(OpaqueKeyField):
    """
    A django Field that stores a CourseKey object as a string.
    """
    description = "A CourseKey object, saved to the DB in the form of a string"
    KEY_CLASS = CourseKey


class UsageKeyField(OpaqueKeyField):
    """
    A django Field that stores a UsageKey object as a string.
    """
    description = "A Location object, saved to the DB in the form of a string"
    KEY_CLASS = UsageKey


class Note(models.Model):
    user_id = models.CharField(max_length=255)
    course_id = models.CharField(max_length=255)
    usage_id = UsageKeyField(max_length=255)
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
            self.usage_id = BlockUsageLocator.from_string(body['usage_id'])
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
        created = self.created.isoformat() if self.created else None
        updated = self.updated.isoformat() if self.updated else None

        return {
            'id': self.pk,
            'user': self.user_id,
            'course_id': self.course_id,
            'usage_id': self.usage_id.to_deprecated_string(),
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
