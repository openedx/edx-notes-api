"""
Paginator for Notes where storage is mysql database.
"""

from rest_framework import pagination

from .utils import NotesPaginatorMixin


class NotesPaginator(NotesPaginatorMixin, pagination.PageNumberPagination):
    """
    Student Notes Paginator.
    """
