"""
Paginator for Notes.
"""

from rest_framework import pagination
from rest_framework.response import Response


class NotesPaginator(pagination.PageNumberPagination):
    """
    Student Notes Paginator.
    """
    page_size = 10
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        """
        Annotate the response with pagination information.
        """
        return Response({
            'start': (self.page.number - 1) * self.get_page_size(self.request),
            'current_page': self.page.number,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'total': self.page.paginator.count,
            'num_pages': self.page.paginator.num_pages,
            'rows': data
        })
