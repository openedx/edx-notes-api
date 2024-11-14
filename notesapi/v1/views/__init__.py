import typing as t
from django.conf import settings

from .common import (
    AnnotationDetailView,
    AnnotationListView,
    AnnotationRetireView,
    AnnotationSearchView
)

from .exceptions import SearchViewRuntimeError


# pylint: disable=import-outside-toplevel
def get_annotation_search_view_class() -> t.Type[AnnotationSearchView]:
    """
    Import views from either mysql, elasticsearch or meilisearch backend
    """
    if settings.ES_DISABLED:
        if getattr(settings, "MEILISEARCH_ENABLED", False):
            from . import meilisearch
            return meilisearch.AnnotationSearchView
        else:
            return AnnotationSearchView
    from . import elasticsearch
    return elasticsearch.AnnotationSearchView
