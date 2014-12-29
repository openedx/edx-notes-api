# -*- coding: utf-8 -*-
import jwt
from calendar import timegm
from datetime import datetime, timedelta
from mock import patch
import unittest

from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import QueryDict

from rest_framework import status
from rest_framework.test import APITestCase

from elasticutils.contrib.django import get_es
from .helpers import get_id_token
from notesapi.v1.models import NoteMappingType, note_searcher

TEST_USER = "test_user_id"


class BaseAnnotationViewTests(APITestCase):
    """
    Abstract class for testing annotation views.
    """
    def setUp(self):
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
            # "created": "2014-11-26T00:00:00+00:00",
            # "updated": "2014-11-26T00:00:00+00:00",
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

    def tearDown(self):
        for note_id in note_searcher.all().values_list('id'):
            get_es().delete(
                index=settings.ES_INDEXES['default'],
                doc_type=NoteMappingType.get_mapping_type_name(),
                id=note_id[0][0]
            )
        get_es().indices.refresh()

    @classmethod
    def setUpClass(cls):
        get_es().indices.create(index=settings.ES_INDEXES['default'], ignore=400)
        get_es().indices.refresh()
        get_es().cluster.health(wait_for_status='yellow')

    @classmethod
    def tearDownClass(cls):
        """
        * deletes the test index
        """
        get_es().indices.delete(index=settings.ES_INDEXES['default'])
        get_es().indices.refresh()

    def _create_annotation(self, refresh=True, **kwargs):
        """
        Create annotation
        """
        opts = self.payload.copy()
        opts.update(kwargs)
        url = reverse('api:v1:annotations')
        response = self.client.post(url, opts, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        get_es().indices.refresh()
        return response.data.copy()

    def _get_annotation(self, annotation_id):
        """
        Fetch annotation directly from elasticsearch.
        """
        get_es().indices.refresh()
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': annotation_id})
        response = self.client.get(url, self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data

    def _get_search_results(self, **kwargs):
        """
        Helper for search method. All keyword parameters are passed in GET
        """
        q = QueryDict("user=" + TEST_USER, mutable=True)
        q.update(kwargs)
        url = reverse('api:v1:annotations_search') + '?{}'.format(q.urlencode())
        result = self.client.get(url)
        return result.data


class AnnotationViewTests(BaseAnnotationViewTests):
    """
    Test annotation views, checking permissions
    """

    def test_create_note(self):
        """
        Ensure we can create a new note.
        """

        url = reverse('api:v1:annotations')
        response = self.client.post(url, self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        annotation = response.data.copy()
        self.assertIn('id', annotation)
        del annotation['id']
        del annotation['updated']
        del annotation['created']

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
        response = self.client.post(reverse('api:v1:annotations'), self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        annotation = self._get_annotation(response.data['id'])
        self.assertNotEqual(annotation['updated'], 'abc', "annotation 'updated' field should not be used by API")

    def test_create_must_not_update(self):
        """
        Create must not update annotations.
        """
        note = self._create_annotation(**self.payload)

        # Try to update the annotation using the create API.
        update_payload = note
        update_payload.update({'text': 'baz'})
        response = self.client.post(reverse('api:v1:annotations'), update_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check if annotation was not updated.
        annotation = self._get_annotation(note['id'])
        self.assertEqual(annotation['text'], 'test note text')

    def test_read(self):
        """
        Ensure we can get an existing annotation.
        """
        note = self.payload
        note_id = self._create_annotation(**note)['id']

        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': note_id})
        response = self.client.get(url, self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.expected_note['id'] = note_id
        annotation = response.data
        del annotation['updated']
        del annotation['created']
        self.assertEqual(annotation, self.expected_note)

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
        data = self._create_annotation(text=u"Foo")
        payload = self.payload.copy()
        payload.update({'id': data['id'], 'text': 'Bar'})
        payload.update(self.headers)
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': data['id']})
        print payload
        response = self.client.put(url, payload, format='json')
        get_es().indices.refresh()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        annotation = self._get_annotation(data['id'])
        self.assertEqual(annotation['text'], "Bar", "annotation wasn't updated in db")
        self.assertEqual(response.data['text'], "Bar", "update annotation should be returned in response")

    def test_update_without_payload_id(self):
        """
        Test if update will be performed when there is no id in payload.

        Tests if id is used from URL, regardless of what arrives in JSON payload.
        """
        note = self._create_annotation(text=u"Foo")
        payload = self.payload.copy()
        payload.update({'text': 'Bar'})
        payload.update(self.headers)
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': note['id']})
        response = self.client.put(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_note = self._get_annotation(note['id'])
        self.assertEqual(updated_note['text'], "Bar", "annotation wasn't updated in db")

    def test_update_with_wrong_payload_id(self):
        """
        Test if update will be performed when there is wrong id in payload.

        Tests if id is used from URL, regardless of what arrives in JSON payload.
        """
        note = self._create_annotation(text=u"Foo")
        payload = self.payload.copy()
        payload.update({'text': 'Bar', 'id': 'xxx'})
        payload.update(self.headers)
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': note['id']})
        response = self.client.put(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_note = self._get_annotation(note['id'])
        self.assertEqual(updated_note['text'], "Bar", "annotation wasn't updated in db")

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
        note = self._create_annotation()
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': note['id']})

        response = self.client.delete(url, self.headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, "response should be 204 NO CONTENT")

        get_es().indices.refresh()
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': note['id']})
        response = self.client.get(url, self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

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

        results = self._get_search_results(text="Second")
        self.assertEqual(results['total'], 1)
        self.assertEqual(len(results['rows']), 1)
        self.assertEqual(results['rows'][0]['text'], 'Second note')

    def test_search_ordering(self):
        """
        Tests ordering of search results.

        Sorting is by descending order (most recent first).
        """
        self._create_annotation(text=u'First one')
        self._create_annotation(text=u'Second note')
        self._create_annotation(text=u'Third note')

        results = self._get_search_results()
        self.assertEqual(results['rows'][0]['text'], 'Third note')
        self.assertEqual(results['rows'][1]['text'], 'Second note')
        self.assertEqual(results['rows'][2]['text'], 'First one')

    def test_search_unicode(self):
        """
        Tests searching of unicode strings.
        """
        self._create_annotation(text=u'Веселих свят')

        results = self._get_search_results(text=u"веселих")
        self.assertEqual(results['total'], 1)
        self.assertEqual(results['rows'][0]['text'], u'Веселих свят')

        results = self._get_search_results(text=u"Свят")
        self.assertEqual(results['rows'][0]['text'], u'Веселих свят')

    def test_search_course(self):
        """
        Tests searching with course_id provided
        """
        self._create_annotation(text=u'First one', course_id="a")
        self._create_annotation(text=u'Second note', course_id="a")
        self._create_annotation(text=u'Third note', course_id="b")
        self._create_annotation(text=u'Fourth note', course_id="c")

        results = self._get_search_results(course_id="a")
        self.assertEqual(results['total'], 2)

        results = self._get_search_results(course_id="b")
        self.assertEqual(results['total'], 1)
        self.assertEqual(results['rows'][0]['text'], u'Third note')

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
            kwargs = {'text': 'Foo_{}'.format(i)}
            self._create_annotation(refresh=False, **kwargs)

        url = reverse('api:v1:annotations')
        response = self.client.get(url, self.headers)
        print response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5, "five annotations should be returned in response")


@patch('django.conf.settings.DISABLE_TOKEN_CHECK', True)
class AllowAllAnnotationViewTests(BaseAnnotationViewTests):
    """
    Test service behavior when authorization is not enforced.
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
