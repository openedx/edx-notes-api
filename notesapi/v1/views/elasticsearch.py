import logging
import traceback

from django_elasticsearch_dsl_drf.constants import (
    LOOKUP_FILTER_TERM,
    LOOKUP_QUERY_IN,
    SEPARATOR_LOOKUP_COMPLEX_VALUE,
)
from django_elasticsearch_dsl_drf.filter_backends import (
    DefaultOrderingFilterBackend,
    HighlightBackend,
)
from elasticsearch.exceptions import TransportError
from elasticsearch_dsl import Search
from elasticsearch_dsl.connections import connections

from notesapi.v1.search_indexes.backends import (
    CompoundSearchFilterBackend,
    FilteringFilterBackend,
)
from notesapi.v1.search_indexes.documents import NoteDocument
from notesapi.v1.search_indexes.paginators import NotesPagination as ESNotesPagination
from notesapi.v1.search_indexes.serializers import (
    NoteDocumentSerializer as NotesElasticSearchSerializer,
)

from .common import AnnotationSearchView as BaseAnnotationSearchView
from .exceptions import SearchViewRuntimeError

logger = logging.getLogger(__name__)


class AnnotationSearchView(BaseAnnotationSearchView):

    # https://django-elasticsearch-dsl-drf.readthedocs.io/en/latest/advanced_usage_examples.html
    filter_fields = {
        "course_id": "course_id",
        "user": "user",
        "usage_id": {
            "field": "usage_id",
            "lookups": [
                LOOKUP_QUERY_IN,
                LOOKUP_FILTER_TERM,
            ],
        },
    }
    highlight_fields = {
        "text": {
            "enabled": True,
            "options": {
                "pre_tags": ["{elasticsearch_highlight_start}"],
                "post_tags": ["{elasticsearch_highlight_end}"],
                "number_of_fragments": 0,
            },
        },
        "tags": {
            "enabled": True,
            "options": {
                "pre_tags": ["{elasticsearch_highlight_start}"],
                "post_tags": ["{elasticsearch_highlight_end}"],
                "number_of_fragments": 0,
            },
        },
    }

    def __init__(self, *args, **kwargs):
        self.client = connections.get_connection(
            NoteDocument._get_using()
        )  # pylint: disable=protected-access
        self.index = NoteDocument._index._name  # pylint: disable=protected-access
        self.mapping = (
            NoteDocument._doc_type.mapping.properties.name
        )  # pylint: disable=protected-access
        # pylint: disable=protected-access
        self.search = Search(
            using=self.client, index=self.index, doc_type=NoteDocument._doc_type.name
        )
        super().__init__(*args, **kwargs)

    def get_serializer_class(self):
        """
        Use Elasticsearch-specific serializer.
        """
        if not self.is_text_search:
            return super().get_serializer_class()
        return NotesElasticSearchSerializer

    def get_queryset(self):
        """
        Hackish method that doesn't quite return a Django queryset.
        """
        if not self.is_text_search:
            return super().get_queryset()
        queryset = self.search.query()
        queryset.model = NoteDocument.Django.model
        return queryset

    def get_filter_backends(self):
        if not self.is_text_search:
            return super().get_filter_backends()
        filter_backends = [
            FilteringFilterBackend,
            CompoundSearchFilterBackend,
            DefaultOrderingFilterBackend,
        ]
        if self.params.get("highlight"):
            filter_backends.append(HighlightBackend)
        return filter_backends

    @property
    def pagination_class(self):
        if not self.is_text_search:
            return super().pagination_class
        return ESNotesPagination

    def build_query_params_state(self):
        super().build_query_params_state()
        if not self.is_text_search:
            return
        if "usage_id__in" in self.query_params:
            usage_ids = self.query_params["usage_id__in"]
            usage_ids = SEPARATOR_LOOKUP_COMPLEX_VALUE.join(usage_ids)
            self.query_params["usage_id__in"] = usage_ids

        if "user" in self.params:
            self.query_params["user"] = self.query_params.pop("user_id")

    @classmethod
    def heartbeat(cls):
        if not get_es().ping():
            raise SearchViewRuntimeError("es")

    @classmethod
    def selftest(cls):
        try:
            return {"es": get_es().info()}
        except TransportError as e:
            raise SearchViewRuntimeError({"es_error": traceback.format_exc()}) from e


def get_es():
    return connections.get_connection()
