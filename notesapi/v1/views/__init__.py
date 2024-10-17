from django.conf import settings

from .common import (
    AnnotationDetailView,
    AnnotationListView,
    AnnotationRetireView,
)

from .exceptions import SearchViewRuntimeError

def get_views_module():
    """
    Import views from either mysql or elasticsearch backend
    """
    if settings.ES_DISABLED:
        from . import common as backend_module
    else:
        from . import elasticsearch as backend_module
    return backend_module
