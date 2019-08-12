"""
django-haystack does not support passing additional highlighting parameters
to backends, so we use our subclassed SearchQuerySet which does,
and subclassed ElasticsearchSearchBackend which passes them to ES
"""

import haystack
from haystack.backends.elasticsearch_backend import \
    ElasticsearchSearchBackend as OrigElasticsearchSearchBackend
from haystack.backends.elasticsearch_backend import \
    ElasticsearchSearchEngine as OrigElasticsearchSearchEngine
from haystack.backends.elasticsearch_backend import \
    ElasticsearchSearchQuery as OrigElasticsearchSearchQuery
from haystack.query import SearchQuerySet as OrigSearchQuerySet


class SearchQuerySet(OrigSearchQuerySet):
    def highlight(self, **kwargs):
        """Adds highlighting to the results."""
        clone = self._clone()
        clone.query.add_highlight(**kwargs)
        return clone


class ElasticsearchSearchQuery(OrigElasticsearchSearchQuery):
    def add_highlight(self, **kwargs):
        """Adds highlighting to the search results."""
        self.highlight = kwargs or True


class ElasticsearchSearchBackend(OrigElasticsearchSearchBackend):
    """
    Subclassed backend that lets user modify highlighting options
    """
    def build_search_kwargs(self, *args, **kwargs):
        res = super(ElasticsearchSearchBackend, self).build_search_kwargs(*args, **kwargs)
        index = haystack.connections[self.connection_alias].get_unified_index()
        content_field = index.document_field
        highlight = kwargs.get('highlight')
        if highlight:
            highlight_options = {
                'fields': {
                    content_field: {'store': 'yes'},
                    'tags': {'store': 'yes'},
                },
            }
            if isinstance(highlight, dict):
                highlight_options.update(highlight)
            res['highlight'] = highlight_options
        return res

    def _process_results(
            self, raw_results, highlight=False, result_class=None, distance_point=None, geo_sort=False
    ):
        """
        Overrides _process_results from Haystack's ElasticsearchSearchBackend to add highlighted tags to the result
        """
        result = super(ElasticsearchSearchBackend, self)._process_results(
            raw_results, highlight, result_class, distance_point, geo_sort
        )

        for i, raw_result in enumerate(raw_results.get('hits', {}).get('hits', [])):
            if 'highlight' in raw_result:
                result['results'][i].highlighted_tags = raw_result['highlight'].get('tags', '')

        return result


class ElasticsearchSearchEngine(OrigElasticsearchSearchEngine):
    backend = ElasticsearchSearchBackend
    query = ElasticsearchSearchQuery
