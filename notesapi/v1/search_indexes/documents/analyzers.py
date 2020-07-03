"""
Elasticsearch fields custom analyzers
"""
from elasticsearch_dsl import analyzer

__all__ = ("html_strip", "case_insensitive_keyword")

html_strip = analyzer(
    "html_strip",
    tokenizer="standard",
    filter=["lowercase", "stop", "snowball"],
    char_filter=["html_strip"]
)

case_insensitive_keyword = analyzer(
    "case_insensitive_keyword",
    tokenizer="keyword",
    filter=["lowercase"]
)
