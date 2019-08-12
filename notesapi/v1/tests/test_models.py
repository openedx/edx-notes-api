from unittest import TestCase

from django.core.exceptions import ValidationError

from notesapi.v1.models import Note
from notesapi.v1.serializers import NoteSerializer


class NoteTest(TestCase):
    def setUp(self):

        self.note_dict = {
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
            "tags": [u"apple", u"pear"],
        }

    def test_create_valid_note(self):
        note = Note.create(self.note_dict.copy())
        note.save()

        serializer = NoteSerializer(note)
        result_note = serializer.data
        del result_note['id']
        del result_note['created']
        del result_note['updated']

        self.assertEqual(result_note, self.note_dict)

    def test_create_invalid_note(self):
        note = Note()
        for empty_type in (None, '', []):
            with self.assertRaises(ValidationError):
                note.create(empty_type)

    def test_must_have_fields_create(self):
        for field in ['user', 'usage_id', 'course_id', 'ranges']:
            payload = self.note_dict.copy()
            payload.pop(field)

            with self.assertRaises(ValidationError):
                note = Note.create(payload)
                note.full_clean()

    def test_default_tags_value(self):
        """ Test that a note without explicit tags has an empty list for the tags value """
        payload = self.note_dict.copy()
        payload.pop("tags")
        note = Note.create(payload)
        note.full_clean()
        note.save()

        self.assertEqual("[]", note.tags)
        self.assertEqual([], NoteSerializer(note).data["tags"])
