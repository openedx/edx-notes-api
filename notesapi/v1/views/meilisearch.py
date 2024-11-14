"""
Meilisearch views to search for annotations.

To enable this backend, define the following settings:

ES_DISABLED = True
MEILISEARCH_ENABLED = True

Then check the Client class for more information about Meilisearch credential settings.

When you start using this backend, you might want to re-index all your content. To do that, run:

    ./manage.py shell -c "from notesapi.v1.views.meilisearch import reindex; reindex()"
"""

import traceback

import meilisearch
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import signals

from notesapi.v1.models import Note

from .common import AnnotationSearchView as BaseAnnotationSearchView
from .exceptions import SearchViewRuntimeError


class Client:
    """
    Simple Meilisearch client class

    It depends on the following Django settings:

    - MEILISEARCH_URL
    - MEILISEARCH_API_KEY
    - MEILISEARCH_INDEX
    """

    _CLIENT = None
    _INDEX = None
    FILTERABLES = ["user_id", "course_id"]

    @property
    def meilisearch_client(self) -> meilisearch.Client:
        """
        Return a meilisearch client.
        """
        if self._CLIENT is None:
            self._CLIENT = meilisearch.Client(
                getattr(settings, "MEILISEARCH_URL", "http://meilisearch:7700"),
                getattr(settings, "MEILISEARCH_API_KEY", ""),
            )
        return self._CLIENT

    @property
    def meilisearch_index(self) -> meilisearch.index.Index:
        """
        Return the meilisearch index used to store annotations.

        If the index does not exist, it is created. And if it does not have the right
        filterable fields, then it is updated.
        """
        if self._INDEX is None:
            index_name = getattr(settings, "MEILISEARCH_INDEX", "student_notes")
            try:
                self._INDEX = self.meilisearch_client.get_index(index_name)
            except meilisearch.errors.MeilisearchApiError:
                task = self.meilisearch_client.create_index(
                    index_name, {"primaryKey": "id"}
                )
                self.meilisearch_client.wait_for_task(task.task_uid, timeout_in_ms=2000)
                self._INDEX = self.meilisearch_client.get_index(index_name)

            # Checking filterable attributes
            existing_filterables = set(self._INDEX.get_filterable_attributes())
            if not set(self.FILTERABLES).issubset(existing_filterables):
                all_filterables = list(existing_filterables.union(self.FILTERABLES))
                self._INDEX.update_filterable_attributes(all_filterables)

        return self._INDEX


class AnnotationSearchView(BaseAnnotationSearchView):
    def get_queryset(self):
        """
        Simple result filtering method based on test search.

        We simply include in the query only those that match the text search query. Note
        that this backend does not support highlighting (yet).
        """
        if not self.is_text_search:
            return super().get_queryset()

        queryset = Note.objects.filter(**self.query_params).order_by("-updated")

        # Define meilisearch params
        filters = [
            f"user_id = '{self.params['user']}'",
            f"course_id = '{self.params['course_id']}'",
        ]
        page_size = int(self.params["page_size"])
        offset = (int(self.params["page"]) - 1) * page_size

        # Perform search
        search_results = Client().meilisearch_index.search(
            self.params["text"],
            {"offset": offset, "limit": page_size, "filter": filters},
        )

        # Limit to these ID
        queryset = queryset.filter(id__in=[r["id"] for r in search_results["hits"]])
        return queryset

    @classmethod
    def heartbeat(cls):
        """
        Check that the meilisearch client is healthy.
        """
        if not Client().meilisearch_client.is_healthy():
            raise SearchViewRuntimeError("meilisearch")

    @classmethod
    def selftest(cls):
        """
        Check that we can access the meilisearch index.
        """
        try:
            return {"meilisearch": Client().meilisearch_index.created_at}
        except meilisearch.errors.MeilisearchError as e:
            raise SearchViewRuntimeError(
                {"meilisearch_error": traceback.format_exc()}
            ) from e


def on_note_save(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Create or update a document.
    """
    add_documents([instance])


def on_note_delete(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Delete a document.
    """
    Client().meilisearch_index.delete_document(instance.id)


def connect_signals() -> None:
    """
    Connect Django signal to meilisearch indexing.
    """
    signals.post_save.connect(on_note_save, sender=Note)
    signals.post_delete.connect(on_note_delete, sender=Note)


def disconnect_signals() -> None:
    """
    Disconnect Django signals: this is necessary in unit tests.
    """
    signals.post_save.disconnect(on_note_save, sender=Note)
    signals.post_delete.disconnect(on_note_delete, sender=Note)


connect_signals()


def reindex():
    """
    Re-index all notes, in batches of 100.
    """
    paginator = Paginator(Note.objects.all(), 100)
    for page_number in paginator.page_range:
        page = paginator.page(page_number)
        add_documents(page.object_list)


def add_documents(notes):
    """
    Convert some Note objects and insert them in the index.
    """
    documents_to_add = [
        {
            "id": note.id,
            "user_id": note.user_id,
            "course_id": note.course_id,
            "text": note.text,
        }
        for note in notes
    ]
    if documents_to_add:
        Client().meilisearch_index.add_documents(documents_to_add)
