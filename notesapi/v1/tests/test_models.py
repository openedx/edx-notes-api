import json
from unittest import TestCase
from notesapi.v1.models import Note
from django.core.exceptions import ValidationError

class NoteTest(TestCase):
    def setUp(self):
        self.course_id = "test_course_id"
        self.user_id = "test_user_id"
        #self.usage = BlockUsageLocator.from_string("i4x://org/course/category/name")
        self.usage = "test_usage_id"

        self.note = {
            "user": u"test_user_id",
            "usage_id": u"test-usage-id",
            "course_id": u"test-course-id",
            "text": u"test note text",
            "quote": u"test note quote",
            "ranges": [
                {
                    "start": u"/p[1]",
                    "end": u"/p[1]",
                    "startOffset": 0,
                    "endOffset": 10,
                }
            ],
        }

    def test_clean_valid_note(self):
        note = Note()
        note.clean(json.dumps(self.note))

        self.note.update({
            'id': None,
            'created': None,
            'updated': None,
        })
        self.assertEqual(note.as_dict(), self.note)

    def test_clean_invalid_note(self):
        note = Note()
        for empty_type in (None, '', 0, []):
            with self.assertRaises(ValidationError):
                note.clean(empty_type)

    def test_must_have_fields(self):
        note = Note()
        for field in ['user', 'usage_id', 'course_id']:
            payload = self.note.copy()
            payload.pop(field)

            with self.assertRaises(ValidationError):
                note.clean(json.dumps(payload))

    def test_clean_many_ranges(self):
        note = Note()

        with self.assertRaises(ValidationError):
            note.clean(json.dumps({
                'text': 'foo',
                'quote': 'bar',
                'ranges': [{} for i in range(10)]  # too many ranges
            }))

    def test_save(self):
        note = Note()
        note.clean(json.dumps(self.note))
        note.save()
