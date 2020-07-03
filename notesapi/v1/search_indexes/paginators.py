"""
Paginator for Document Notes where storage is elasticsearch database.
"""

from django_elasticsearch_dsl_drf.pagination import PageNumberPagination

from ..utils import NotesPaginatorMixin

__all__ = ('NotesPagination',)


class NotesPagination(NotesPaginatorMixin, PageNumberPagination):
    """
    Student Document Notes Paginator.
    """
