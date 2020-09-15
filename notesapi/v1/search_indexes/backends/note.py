from itertools import chain

from django_elasticsearch_dsl_drf.filter_backends import (
    CompoundSearchFilterBackend as CompoundSearchFilterBackendOrigin,
    FilteringFilterBackend as FilteringFilterBackendOrigin,
)
from notesapi.v1.utils import Request

__all__ = ('CompoundSearchFilterBackend', 'FilteringFilterBackend')


class CompoundSearchFilterBackend(CompoundSearchFilterBackendOrigin):
    """
    Extends compound search backend.
    """

    search_fields = (
        'text',
        'tags',
    )

    def get_search_query_params(self, request):
        """
        Get search query params.

        :param request: Django REST framework request.
        :type request: rest_framework.request.Request
        :return: List of search query params.
        :rtype: list
        """
        query_params = request.query_params.copy()
        return list(chain.from_iterable(query_params.getlist(search_param, []) for search_param in self.search_fields))


class FilteringFilterBackend(FilteringFilterBackendOrigin):
    """
    Extends filtering filter backend.
    """

    def get_filter_query_params(self, request, view):
        """
        Get query params to be filtered on.

        Extends the standard behavior of the parent class method to pass
        a simulated (not real) request to this method.
        Since we need to use the dict `query_params` defined in the view
        and present it as `request.query_params`.
        """
        simulated_request = Request(view.query_params)

        return super().get_filter_query_params(simulated_request, view)
