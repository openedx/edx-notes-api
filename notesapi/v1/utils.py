"""
Utilities for notes api application
"""

from django.conf import settings
from django.http import QueryDict
from rest_framework.response import Response


class NotesPaginatorMixin:
    """
    Student Notes Paginator Mixin
    """

    page_size = settings.DEFAULT_NOTES_PAGE_SIZE
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        """
        Annotate the response with pagination information.
        """
        return Response(
            {
                'start': (self.page.number - 1) * self.get_page_size(self.request),
                'current_page': self.page.number,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'total': self.page.paginator.count,
                'num_pages': self.page.paginator.num_pages,
                'rows': data,
            }
        )


def dict_to_querydict(dict_):
    """
    Converts a dict value into a Django's QueryDict object.
    """
    query_dict = QueryDict("", mutable=True)
    for name, value in dict_.items():
        if isinstance(name, list):
            query_dict.setlist(name, value)
        else:
            query_dict.appendlist(name, value)
    query_dict._mutable = False
    return query_dict


class Request:
    """
    Specifies custom behavior of the standard Django request class.

    Implementation of the `duck typing` pattern.
    Using an object of class `Request` allows you to define the desired logic,
    which will be different from Django's Request.
    Those program components that are expecting a Django request,
    but they will use `Request` - will not notice the substitution at all.
    """

    def __init__(self, query_params):
        self._query_params = query_params

    @property
    def query_params(self):
        """
        Returns the Django's QueryDict object, which presents request's query params.
        """
        return dict_to_querydict(self._query_params)
