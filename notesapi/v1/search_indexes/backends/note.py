from itertools import chain

from django_elasticsearch_dsl_drf.filter_backends import (
    CompoundSearchFilterBackend as CompoundSearchFilterBackendOrigin,
)

__all__ = ('CompoundSearchFilterBackend',)


class CompoundSearchFilterBackend(CompoundSearchFilterBackendOrigin):
    """
    Customized compound search backend.
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
        return list(
            chain.from_iterable(
                query_params.getlist(search_param, [])
                for search_param in self.search_fields
            )
        )
