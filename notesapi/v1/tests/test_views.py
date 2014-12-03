import jwt
from calendar import timegm
from datetime import datetime, timedelta
from mock import patch
import unittest

from django.core.urlresolvers import reverse
from django.conf import settings

from rest_framework import status
from rest_framework.test import APITestCase

from annotator import annotation, es, auth
from annotator.annotation import Annotation
from .helpers import get_id_token

TEST_USER = "test-user-id"

class BaseAnnotationViewTests(APITestCase):
    """
    Abstract class for testing annotation views.
    """
    def setUp(self):
        assert Annotation.es.host == settings.ELASTICSEARCH_URL
        assert Annotation.es.index == settings.ELASTICSEARCH_INDEX

        annotation.Annotation.create_all()
        es.conn.cluster.health(wait_for_status='yellow')

        token = get_id_token(TEST_USER)
        self.client.credentials(HTTP_X_ANNOTATOR_AUTH_TOKEN=token)
        self.headers = {"user": TEST_USER}

        self.payload = {
            "user": TEST_USER,
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

        self.expected_note = {
            "created": "2014-11-26T00:00:00+00:00",
            "updated": "2014-11-26T00:00:00+00:00",
            "user": TEST_USER,
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
            "permissions": {"read": ["group:__consumer__"]},
        }

    def tearDown(self):
        annotation.Annotation.drop_all()

    def _create_annotation(self, refresh=True, **kwargs):
        """
        Create annotation directly in elasticsearch.
        """
        opts = {
            'user': TEST_USER,
        }
        opts.update(kwargs)
        annotation = Annotation(**opts)
        annotation.save(refresh=refresh)
        return annotation

    def _get_annotation(self, annotation_id):
        """
        Fetch annotation directly from elasticsearch.
        """
        return Annotation.fetch(annotation_id)

    def _get_search_results(self, qs=''):
        """
        Helper for search method.
        """
        url = reverse('api:v1:annotations_search') + '?user=' + TEST_USER + '&{}'.format(qs)
        result = self.client.get(url)
        return result.data


class AnnotationViewTests(BaseAnnotationViewTests):
    """
    Test annotation views, checking permissions
    """

    @patch('annotator.elasticsearch.datetime')
    def test_create_note(self, mock_datetime):
        """
        Ensure we can create a new note.
        """
        mock_datetime.datetime.now.return_value.isoformat.return_value = "2014-11-26T00:00:00+00:00"

        url = reverse('api:v1:annotations')
        response = self.client.post(url, self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        annotation = response.data.copy()
        self.assertIn('id', annotation)
        annotation.pop('id')
        self.assertEqual(annotation, self.expected_note)

        expected_location = '/api/v1/annotations/{0}'.format(response.data['id'])
        self.assertTrue(
            response['Location'].endswith(expected_location),
            "the response should have a Location header with the URL to read the annotation that was created"
        )

        self.assertEqual(response.data['user'], TEST_USER)

    def test_create_ignore_created(self):
        """
        Test if annotation 'created' field is not used by API.
        """
        self.payload['created'] = 'abc'
        response = self.client.post(reverse('api:v1:annotations'), self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        annotation = self._get_annotation(response.data['id'])
        self.assertNotEqual(annotation['created'], 'abc', "annotation 'created' field should not be used by API")

    def test_create_ignore_updated(self):
        """
        Test if annotation 'updated' field is not used by API.
        """
        self.payload['updated'] = 'abc'
        payload = self.payload
        payload.update(self.headers)
        response = self.client.post(reverse('api:v1:annotations'), self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        annotation = self._get_annotation(response.data['id'])
        self.assertNotEqual(annotation['updated'], 'abc', "annotation 'updated' field should not be used by API")

    def test_create_must_not_update(self):
        """
        Create must not update annotations.
        """
        payload = {'name': 'foo'}
        payload.update(self.headers)
        response = self.client.post(reverse('api:v1:annotations'), payload, format='json')
        annotation_id = response.data['id']

        # Try to update the annotation using the create API.
        update_payload = {'name': 'bar', 'id': annotation_id}
        update_payload.update(self.headers)
        response = self.client.post(reverse('api:v1:annotations'), update_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check if annotation was not updated.
        annotation = self._get_annotation(annotation_id)
        self.assertEqual(annotation['name'], 'foo')

    @patch('annotator.elasticsearch.datetime')
    def test_read(self, mock_datetime):
        """
        Ensure we can get an existing annotation.
        """
        mock_datetime.datetime.now.return_value.isoformat.return_value = "2014-11-26T00:00:00+00:00"
        note = self.payload
        note['id'] = "test_id"
        self._create_annotation(**note)

        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': "test_id"})
        response = self.client.get(url, self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.expected_note['id'] = 'test_id'
        self.assertEqual(response.data, self.expected_note)

    def test_read_notfound(self):
        """
        Case when no annotation is present with specific id.
        """
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': 123})
        response = self.client.get(url, self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, "response should be 404 NOT FOUND")

    def test_update(self):
        """
        Ensure we can update an existing annotation.
        """
        self._create_annotation(text=u"Foo", id='123', created='2014-10-10')
        payload = {'id': '123', 'text': 'Bar'}
        payload.update(self.headers)
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': 123})
        response = self.client.put(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        annotation = self._get_annotation('123')
        self.assertEqual(annotation['text'], "Bar", "annotation wasn't updated in db")
        self.assertEqual(response.data['text'], "Bar", "update annotation should be returned in response")

    def test_update_without_payload_id(self):
        """
        Test if update will be performed when there is no id in payload.

        Tests if id is used from URL, regardless of what arrives in JSON payload.
        """
        self._create_annotation(text=u"Foo", id='123')

        payload = {'text': 'Bar'}
        payload.update(self.headers)
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': 123})
        response = self.client.put(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        annotation = self._get_annotation('123')
        self.assertEqual(annotation['text'], "Bar", "annotation wasn't updated in db")

    def test_update_with_wrong_payload_id(self):
        """
        Test if update will be performed when there is wrong id in payload.

        Tests if id is used from URL, regardless of what arrives in JSON payload.
        """
        self._create_annotation(text=u"Foo", id='123')

        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': 123})
        payload = {'text': 'Bar', 'id': 'abc'}
        payload.update(self.headers)
        response = self.client.put(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        annotation = self._get_annotation('123')
        self.assertEqual(annotation['text'], "Bar", "annotation wasn't updated in db")

    def test_update_notfound(self):
        """
        Test if annotation not exists with specified id and update was attempted on it.
        """
        payload = {'id': '123', 'text': 'Bar'}
        payload.update(self.headers)
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': 123})
        response = self.client.put(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete(self):
        """
        Ensure we can delete an existing annotation.
        """
        kwargs = dict(text=u"Bar", id='456')
        self._create_annotation(**kwargs)
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': 456})
        response = self.client.delete(url, self.headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, "response should be 204 NO CONTENT")
        self.assertEqual(self._get_annotation('456'), None, "annotation wasn't deleted in db")

    def test_delete_notfound(self):
        """
        Case when no annotation is present with specific id when trying to delete.
        """
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': 123})
        response = self.client.delete(url, self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, "response should be 404 NOT FOUND")

    def test_search(self):
        """
        Tests for search method.
        """
        note_1 = self._create_annotation(text=u'First one')
        note_2 = self._create_annotation(text=u'Second note')
        note_3 = self._create_annotation(text=u'Third note')

        results = self._get_search_results()
        self.assertEqual(results['total'], 3)

        results = self._get_search_results("text=Second")
        self.assertEqual(results['total'], 1)
        self.assertEqual(len(results['rows']), 1)
        self.assertEqual(results['rows'][0]['text'], 'Second note')

        results = self._get_search_results('limit=1')
        self.assertEqual(results['total'], 3)
        self.assertEqual(len(results['rows']), 1)

    def test_search_ordering(self):
        """
        Tests ordering of search results.

        Sorting is by descending order (most recent first).
        """
        note_1 = self._create_annotation(text=u'First one')
        note_2 = self._create_annotation(text=u'Second note')
        note_3 = self._create_annotation(text=u'Third note')

        results = self._get_search_results()
        self.assertEqual(results['rows'][0]['text'], 'Third note')
        self.assertEqual(results['rows'][1]['text'], 'Second note')
        self.assertEqual(results['rows'][2]['text'], 'First one')

    def test_search_limit(self):
        """
        Tests for limit query parameter for paging through results.
        """
        for i in xrange(300):
            self._create_annotation(refresh=False)

        es.conn.indices.refresh(es.index)

        # By default return 25. See RESULTS_DEFAULT_SIZE in settings.
        result = self._get_search_results()
        self.assertEqual(len(result['rows']), 25)

        # Return maximum 250. See RESULTS_MAX_SIZE in settings.
        result = self._get_search_results('limit=300')
        self.assertEqual(len(result['rows']), 250)

        # Return minimum 0.
        result = self._get_search_results('limit=-10')
        self.assertEqual(len(result['rows']), 0)

        # Ignore bogus values.
        result = self._get_search_results('limit=foobar')
        self.assertEqual(len(result['rows']), 25)

    def test_search_offset(self):
        """
        Tests for offset query parameter for paging through results.
        """
        for i in xrange(250):
            self._create_annotation(refresh=False)

        es.conn.indices.refresh(es.index)

        result = self._get_search_results()
        self.assertEqual(len(result['rows']), 25)
        first = result['rows'][0]

        result = self._get_search_results('offset=240')
        self.assertEqual(len(result['rows']), 10)

        # ignore negative values
        result = self._get_search_results('offset=-10')
        self.assertEqual(len(result['rows']), 25)
        self.assertEqual(result['rows'][0], first)

        # ignore bogus values
        result = self._get_search_results('offset=foobar')
        self.assertEqual(len(result['rows']), 25)
        self.assertEqual(result['rows'][0], first)

    def test_read_all_no_annotations(self):
        """
        Tests list all annotations endpoint when no annotations are present in elasticsearch.
        """
        url = reverse('api:v1:annotations')
        response = self.client.get(url, self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0, "no annotation should be returned in response")

    def test_read_all(self):
        """
        Tests list all annotations.
        """
        for i in xrange(5):
            kwargs = {'text': 'Foo_{}'.format(i), 'id': str(i)}
            self._create_annotation(refresh=False, **kwargs)

        es.conn.indices.refresh(es.index)

        url = reverse('api:v1:annotations')
        response = self.client.get(url, self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5, "five annotations should be returned in response")


@patch('django.conf.settings.DISABLE_TOKEN_CHECK', True)
class AllowAllAnnotationViewTests(BaseAnnotationViewTests):
    """
    Test annotator behavior when authorization is not enforced
    """

    def test_create_no_payload(self):
        """
        Test if no payload is sent when creating a note.
        """
        url = reverse('api:v1:annotations')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TokenTests(BaseAnnotationViewTests):
    """
    Test token interactions
    """
    url = reverse('api:v1:annotations')
    token_data = {
        'aud': settings.CLIENT_ID,
        'sub': TEST_USER,
        'iat': timegm(datetime.utcnow().utctimetuple()),
        'exp': timegm((datetime.utcnow() + timedelta(seconds=300)).utctimetuple()),
    }

    def _assert_403(self, token):
        """
        Asserts that request with this token will fail
        """
        self.client.credentials(HTTP_X_ANNOTATOR_AUTH_TOKEN=token)
        response = self.client.get(self.url, self.headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_200(self):
        """
        Ensure we can read list of annotations
        """
        response = self.client.get(self.url, self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_no_token(self):
        """
        403 when no token is provided
        """
        self.client._credentials = {}
        response = self.client.get(self.url, self.headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_malformed_token(self):
        """
        403 when token can not be decoded
        """
        self._assert_403("kuku")

    def test_expired_token(self):
        """
        403 when token is expired
        """
        token = self.token_data.copy()
        token['exp'] = 1
        token = jwt.encode(token, settings.CLIENT_SECRET)
        self._assert_403(token)

    def test_wrong_issuer(self):
        """
        403 when token's issuer is wrong
        """
        token = self.token_data.copy()
        token['aud'] = 'not Edx-notes'
        token = jwt.encode(token, settings.CLIENT_SECRET)
        self._assert_403(token)

    def test_wrong_user(self):
        """
        403 when token's user is wrong
        """
        token = self.token_data.copy()
        token['sub'] = 'joe'
        token = jwt.encode(token, settings.CLIENT_SECRET)
        self._assert_403(token)

    def test_wrong_secret(self):
        """
        403 when token is signed by wrong secret
        """
        token = jwt.encode(self.token_data, "some secret")
        self._assert_403(token)
