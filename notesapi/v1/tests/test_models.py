from unittest import TestCase
from notesapi.v1.models import Note, NoteMappingType
from django.core.exceptions import ValidationError


class NoteTest(TestCase):
    def setUp(self):

        self.note = {
            "user": u"test_user_id",
            "usage_id": u"i4x://org/course/html/52aa9816425a4ce98a07625b8cb70811",
            "course_id": u"org/course/run",
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
        note.clean(self.note)

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
        for field in ['user', 'usage_id', 'course_id', 'ranges']:
            payload = self.note.copy()
            payload.pop(field)

            with self.assertRaises(ValidationError):
                note.clean(payload)

    def test_save(self):
        note = Note()
        note.clean(self.note)
        note.save()

    def test_extract_document(self):
        note = Note()
        note.clean(self.note)
        note.save()
        self.assertEqual(NoteMappingType.extract_document(note.id), note.as_dict())
