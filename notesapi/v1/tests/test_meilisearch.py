from unittest.mock import Mock, patch

from django.test import TestCase

from notesapi.v1.models import Note
from notesapi.v1.views import meilisearch


class MeilisearchTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        meilisearch.connect_signals()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        meilisearch.disconnect_signals()

    def setUp(self):
        self.enterContext(
            patch.object(meilisearch.Client, "meilisearch_client", Mock())
        )
        self.enterContext(patch.object(meilisearch.Client, "meilisearch_index", Mock()))

    @property
    def note_dict(self):
        return {
            "user": "test_user_id",
            "usage_id": "i4x://org/course/html/52aa9816425a4ce98a07625b8cb70811",
            "course_id": "org/course/run",
            "text": "test note text",
            "quote": "test note quote",
            "ranges": [
                {
                    "start": "/p[1]",
                    "end": "/p[1]",
                    "startOffset": 0,
                    "endOffset": 10,
                }
            ],
            "tags": ["apple", "pear"],
        }

    def test_save_delete_note(self):
        note = Note.create(self.note_dict)
        note.save()
        note_id = note.id

        meilisearch.Client.meilisearch_index.add_documents.assert_called_with(
            [
                {
                    "id": note_id,
                    "user_id": "test_user_id",
                    "course_id": "org/course/run",
                    "text": "test note text",
                }
            ]
        )

        note.delete()
        meilisearch.Client.meilisearch_index.delete_document.assert_called_with(note_id)

    def test_get_queryset_no_result(self):
        queryset = meilisearch.AnnotationSearchView().get_queryset()
        assert not queryset.all()

    def test_get_queryset_one_match(self):
        note1 = Note.create(self.note_dict)
        note2 = Note.create(self.note_dict)
        note1.save()
        note2.save()
        view = meilisearch.AnnotationSearchView()
        view.params = {
            "text": "dummy text",
            "user": "someuser",
            "course_id": "course/id",
            "page_size": 10,
            "page": 2,
        }
        with patch.object(
            meilisearch.Client.meilisearch_index,
            "search",
            Mock(return_value={"hits": [{"id": note2.id}]}),
        ) as mock_search:
            queryset = view.get_queryset()
            mock_search.assert_called_once_with(
                "dummy text",
                {
                    "offset": 10,
                    "limit": 10,
                    "filter": ["user_id = 'someuser'", "course_id = 'course/id'"],
                },
            )
            assert [note2.id] == [note.id for note in queryset]
