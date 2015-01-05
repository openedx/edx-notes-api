# -*- coding: utf-8 -*-
import jwt
from calendar import timegm
from datetime import datetime, timedelta
from mock import patch

from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import QueryDict

from rest_framework import status
from rest_framework.test import APITestCase

from .helpers import get_id_token
from notesapi.v1.models import Note


TEST_USER = "test_user_id"


class BaseAnnotationViewTests(APITestCase):
    """
    Abstract class for testing annotation views.
    """
    def setUp(self):
        call_command('clear_index', interactive=False)
        call_command('update_index')

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

    def _create_annotation(self, **kwargs):
        """
        Create annotation
        """
        opts = self.payload.copy()
        opts.update(kwargs)
        url = reverse('api:v1:annotations')
        response = self.client.post(url, opts, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        call_command('update_index')
        return response.data.copy()

    def _get_annotation(self, annotation_id):
        """
        Fetch annotation directly from elasticsearch.
        """
        call_command('update_index')
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

        self.assertEqual(annotation, self.payload)

        expected_location = '/api/v1/annotations/{0}'.format(response.data['id'])
        self.assertTrue(
            response['Location'].endswith(expected_location),
            "the response should have a Location header with the URL to read the annotation that was created"
        )

        self.assertEqual(response.data['user'], TEST_USER)

    # @patch('django.conf.settings.ES_DISABLED', True)
    # def test_create_es_disabled(self):
    #     """
    #     Ensure we can create note in database when elasticsearch is disabled.
    #     """
    #     url = reverse('api:v1:annotations')
    #     response = self.client.post(url, self.payload, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     Note.objects.get(id=response.data['id'])
    #     self.assertEqual(note_searcher.filter(id=response.data['id']).count(), 0)

    # def test_delete_es_disabled(self):
    #     """
    #     Ensure we can delete note in database when elasticsearch is disabled.
    #     """
    #     url = reverse('api:v1:annotations')
    #     response = self.client.post(url, self.payload, format='json')
    #     call_command('update_index')
    #     self.assertEqual(note_searcher.filter(id=response.data['id']).count(), 1)

    #     with patch('django.conf.settings.ES_DISABLED', True):
    #         Note.objects.get(id=response.data['id']).delete()

    #     self.assertEqual(note_searcher.filter(id=response.data['id']).count(), 1)

    def test_create_ignore_created(self):
        """
        Test if annotation 'created' field is not used by API.
        """
        self.payload['created'] = '2015-01-05T11:46:58.837059+00:00'
        response = self.client.post(reverse('api:v1:annotations'), self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        annotation = self._get_annotation(response.data['id'])
        self.assertNotEqual(annotation['created'], 'abc', "annotation 'created' field should not be used by API")

    def test_create_ignore_updated(self):
        """
        Test if annotation 'updated' field is not used by API.
        """
        self.payload['updated'] = '2015-01-05T11:46:58.837059+00:00'
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
        note_id = self._create_annotation(**self.payload)['id']

        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': note_id})
        response = self.client.get(url, self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        annotation = response.data
        del annotation['id']
        del annotation['updated']
        del annotation['created']
        self.assertEqual(annotation, self.payload)

    def test_create_multirange(self):
        """
        Create a note that has several ranges and read it
        """
        note = self.payload.copy()
        ranges = [
            {
                "start": "/p[1]",
                "end": "/p[1]",
                "startOffset": 0,
                "endOffset": 10,
            },
            {
                "start": "/p[2]",
                "end": "/p[2]",
                "startOffset": 20,
                "endOffset": 22,
            }
        ]

        note['ranges'] = ranges
        note_id = self._create_annotation(**note)['id']

        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': note_id})
        response = self.client.get(url, self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        annotation = response.data
        del annotation['id']
        del annotation['updated']
        del annotation['created']
        self.assertEqual(annotation, note)

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
        response = self.client.put(url, payload, format='json')
        call_command('update_index')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        annotation = self._get_annotation(data['id'])
        self.assertEqual(annotation['text'], "Bar", "annotation wasn't updated in db")
        self.assertEqual(response.data['text'], "Bar", "update annotation should be returned in response")

    def test_update_fail(self):
        """
        Ensure can not update an existing annotation with bad note.
        """
        data = self._create_annotation(text=u"Foo")

        # Bad note. Only id and user is present.
        payload = {'id': data['id'], 'user': TEST_USER}

        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': data['id']})
        response = self.client.put(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

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

        call_command('update_index')
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
        self._create_annotation(text=u'First one')
        self._create_annotation(text=u'Second note')
        self._create_annotation(text=u'Third note')

        results = self._get_search_results()
        self.assertEqual(results['total'], 3)

        results = self._get_search_results(text="Second")
        self.assertEqual(results['total'], 1)
        self.assertEqual(len(results['rows']), 1)
        self.assertEqual(results['rows'][0]['text'], 'Second note')

    def test_search_highlight(self):
        """
        Tests highlighting.
        """
        self._create_annotation(text=u'First note')
        self._create_annotation(text=u'Second note')

        results = self._get_search_results()
        self.assertEqual(results['total'], 2)

        # FIXME class and tag
        results = self._get_search_results(text="first", highlight=True, highlight_class='class', highlight_tag='tag')
        self.assertEqual(results['total'], 1)
        self.assertEqual(len(results['rows']), 1)
        self.assertEqual(results['rows'][0]['text'], '<em>First</em> note')

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

    def test_search_multiword(self):
        """
        Tests searching of complex words and word combinations
        """
        self._create_annotation(text=u'Totally different something')
        self.assertEqual(self._get_search_results(text=u"TOTALLY")['total'], 1)
        self.assertEqual(self._get_search_results(text=u"different")['total'], 1)
        self.assertEqual(self._get_search_results(text=u"differ")['total'], 1)
        self.assertEqual(self._get_search_results(text=u"total")['total'], 1)
        self.assertEqual(self._get_search_results(text=u"totil")['total'], 0)
        self.assertEqual(self._get_search_results(text=u"something")['total'], 1)
        self.assertEqual(self._get_search_results(text=u"totally different")['total'], 1)

    def test_search_course(self):
        """
        Tests searching with course_id provided
        """
        self._create_annotation(text=u'First one', course_id="u'edX/DemoX/Demo_Course'")
        self._create_annotation(text=u'Not shown', course_id="u'edx/demox/demo_course'")  # wrong case
        self._create_annotation(text=u'Second note', course_id="u'edX/DemoX/Demo_Course'")
        self._create_annotation(text=u'Third note', course_id="b")
        self._create_annotation(text=u'Fourth note', course_id="c")

        results = self._get_search_results(course_id="u'edX/DemoX/Demo_Course'")
        self.assertEqual(results['total'], 2)

        results = self._get_search_results(course_id="b")
        self.assertEqual(results['total'], 1)
        self.assertEqual(results['rows'][0]['text'], u'Third note')

    def test_read_all_no_annotations(self):
        """
        Tests list all annotations endpoint when no annotations are present in database.
        """
        url = reverse('api:v1:annotations')
        self.headers["course_id"] = "a/b/c"
        response = self.client.get(url, self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0, "no annotation should be returned in response")

    def test_read_all(self):
        """
        Tests list all annotations.
        """
        for i in xrange(5):
            kwargs = {'text': 'Foo_{}'.format(i),

            }
            self._create_annotation(**kwargs)

        url = reverse('api:v1:annotations')
        self.headers["course_id"] = "test-course-id"
        response = self.client.get(url, self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5, "five annotations should be returned in response")

    def test_read_all_no_query_param(self):
        """
        Tests list all annotations when course_id query param is not present.
        """
        url = reverse('api:v1:annotations')
        response = self.client.get(url, self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


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
        self.headers["course_id"] = "test-course-id"
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
