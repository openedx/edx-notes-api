import jwt
from calendar import timegm
from datetime import datetime, timedelta
from django.conf import settings

from annotator import es
from annotator.annotation import Annotation


def get_id_token(user):
    now = datetime.utcnow()
    return jwt.encode({
        'aud': settings.CLIENT_ID,
        'sub': user,
        'iat': timegm(now.utctimetuple()),
        'exp': timegm((now + timedelta(seconds=300)).utctimetuple()),
    }, settings.CLIENT_SECRET)

NOTE = {
        "user": 'test-user-id',
        "usage_id": "test-usage-id",
        "course_id": "test-course-id",
        "text": "test note text",
        "quote": "test note quote",
        "ranges": [
            {
                "start": "/p[1]",
                "end": "/p[1]",
                "startOffset": 0,
                "endOffset": 10,
            }
        ],
    }

class AnnotationFactory(object):
    """
    Multiple notes creation.
    """
    @staticmethod
    def create(number=1):
        """
        Create multiple notes directly in elasticsearch.
        """
        for i in xrange(1, number + 1):
            NOTE.update({'id': str(i), 'text': 'Text {}'.format(i)})
            _create_annotation(refresh=False, **NOTE)

        es.conn.indices.refresh(es.index)


def _create_annotation(refresh=True, **kwargs):
    """
    Create annotation directly in elasticsearch.
    """
    return Annotation(**kwargs).save(refresh=refresh)


def _get_annotation(annotation_id):
    """
    Fetch annotation directly from elasticsearch.
    """
    return Annotation.fetch(annotation_id)
