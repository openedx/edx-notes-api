from django.conf import settings

from annotator import es

def set_es_settings():
    """
    Overwrite default annotator-store elasticsearch settings.
    """
    es.host = getattr(settings, 'ELASTICSEARCH_URL', 'http://localhost:9200')
    es.index = getattr(settings, 'ELASTICSEARCH_INDEX', 'edx-notes-dev')
