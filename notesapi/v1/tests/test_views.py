# -*- coding: utf-8 -*-
import unittest
from calendar import timegm
from datetime import datetime, timedelta
from urllib import parse

from django.conf import settings
from django.core.management import call_command
from django.test.utils import override_settings
from django.urls import reverse
from mock import patch

import ddt
import jwt
from rest_framework import status
from rest_framework.test import APITestCase

from .helpers import get_id_token

TEST_USER = "test_user_id"
TEST_OTHER_USER = "test_other_user_id"

if not settings.ES_DISABLED:
    import haystack
else:
    def call_command(*args, **kwargs):
        pass


class BaseAnnotationViewTests(APITestCase):
    """
    Abstract class for testing annotation views.
    """
    def setUp(self):
        call_command('clear_index', interactive=False)

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
            "tags": ["pink", "lady"]
        }

    def _create_annotation(self, expected_status=status.HTTP_201_CREATED, **kwargs):
        """
        Create annotation
        """
        opts = self.payload.copy()
        opts.update(kwargs)
        url = reverse('api:v1:annotations')
        response = self.client.post(url, opts, format='json')
        self.assertEqual(response.status_code, expected_status)
        return response.data.copy()

    def _do_annotation_update(self, data, updated_fields):
        """
        Helper method for updating an annotation.

        Returns the response and the updated annotation.
        """
        payload = self.payload.copy()
        payload.update(updated_fields)
        payload.update(self.headers)
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': data['id']})
        response = self.client.put(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response, self._get_annotation(data['id'])

    def _get_annotation(self, annotation_id):
        """
        Fetch annotation
        """
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': annotation_id})
        response = self.client.get(url, self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data

    def _get_search_results(self, **kwargs):
        """
        Helper for search method. All keyword parameters are passed in GET
        """
        data = {"user": TEST_USER}
        data.update(kwargs)
        url = reverse('api:v1:annotations_search')
        result = self.client.get(url, data=data)
        return result.data

    def get_annotations(self, query_parameters=None, expected_status=200):
        """
        Helper method for sending a GET to the server. Verifies the expected status and returns the response.
        """
        data = {"user": TEST_USER, 'course_id': 'test-course-id'}
        if query_parameters:
            data.update(query_parameters)
        response = self.client.get(reverse('api:v1:annotations'), data=data)
        self.assertEqual(expected_status, response.status_code)
        return response.data

    # pylint: disable=too-many-arguments
    def verify_pagination_info(
            self, response,
            total_annotations,
            num_pages,
            annotations_per_page,
            current_page,
            previous_page,
            next_page,
            start
    ):
        """
        Verify the pagination information.

        Argument:
            response: response from api
            total_annotations: total annotations in the response
            num_pages: total number of pages in response
            annotations_per_page: annotations on current page
            current_page: current page number
            previous_page: previous page number
            next_page: next page number
            start: start of the current page
        """
        def get_page_value(url, current_page):
            """
            Return page value extracted from url.
            """
            if url is None:
                return None

            parsed = parse.urlparse(url)
            query_params = parse.parse_qs(parsed.query)

            # If current_page is 2 then DRF will not include `page` query param in previous url.
            # So return page 1 if current page equals to 2 and `page` key is missing from url.
            if 'page' not in query_params and current_page == 2:
                return 1

            page = query_params['page'][0]
            return page if page is None else int(page)

        self.assertEqual(response['total'], total_annotations)
        self.assertEqual(response['num_pages'], num_pages)
        self.assertEqual(len(response['rows']), annotations_per_page)
        self.assertEqual(response['current_page'], current_page)
        self.assertEqual(get_page_value(response['previous'], response['current_page']), previous_page)
        self.assertEqual(get_page_value(response['next'], response['current_page']), next_page)
        self.assertEqual(response['start'], start)

    # pylint: disable=too-many-arguments
    def verify_list_view_pagination(
            self,
            query_parameters,
            total_annotations,
            num_pages,
            annotations_per_page,
            current_page,
            previous_page,
            next_page,
            start
    ):
        """
        Verify pagination information for AnnotationListView
        """
        total_annotations = total_annotations
        for i in range(total_annotations):
            self._create_annotation(text=u'annotation {}'.format(i))

        response = self.get_annotations(query_parameters=query_parameters)
        self.verify_pagination_info(
            response,
            total_annotations=total_annotations,
            num_pages=num_pages,
            annotations_per_page=annotations_per_page,
            current_page=current_page,
            previous_page=previous_page,
            next_page=next_page,
            start=start
        )

    # pylint: disable=too-many-arguments
    def verify_search_view_pagination(
            self,
            query_parameters,
            total_annotations,
            num_pages,
            annotations_per_page,
            current_page,
            previous_page,
            next_page,
            start
    ):
        """
        Verify pagination information for AnnotationSearchView
        """
        total_annotations = total_annotations
        for i in range(total_annotations):
            self._create_annotation(text=u'annotation {}'.format(i))

        response = self._get_search_results(**query_parameters)
        self.verify_pagination_info(
            response,
            total_annotations=total_annotations,
            num_pages=num_pages,
            annotations_per_page=annotations_per_page,
            current_page=current_page,
            previous_page=previous_page,
            next_page=next_page,
            start=start
        )


@ddt.ddt
class AnnotationListViewTests(BaseAnnotationViewTests):
    """
    Test annotation creation and listing by user and course
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
        self.assertEqual(type(annotation['id']), str)
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

    def test_create_blank_text(self):
        """
        Ensure we can create a new note with empty text field.
        """
        url = reverse('api:v1:annotations')
        self.payload['text'] = ''
        response = self.client.post(url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['text'], '')

    def test_create_no_tags(self):
        """
        Ensure we can create a new note with empty list of tags.
        """
        url = reverse('api:v1:annotations')
        self.payload['tags'] = []
        response = self.client.post(url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['tags'], [])

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

    @patch('django.conf.settings.MAX_NOTES_PER_COURSE', 5)
    def test_create_maximum_allowed(self):
        """
        Tests if user can create more than maximum allowed notes per course
        Also test if other user can create notes and Same user can create notes in other course
        """
        for i in range(5):
            kwargs = {'text': 'Foo_{}'.format(i)}
            self._create_annotation(**kwargs)

        # Creating more notes should result in 400 error
        kwargs = {'text': 'Foo_{}'.format(6)}
        response = self._create_annotation(expected_status=status.HTTP_400_BAD_REQUEST, **kwargs)
        self.assertEqual(
            response['error_msg'],
            u'You can create up to {0} notes.'
            u' You must remove some notes before you can add new ones.'.format(settings.MAX_NOTES_PER_COURSE)
        )

        # if user tries to create note in a different course it should succeed
        kwargs = {'course_id': 'test-course-id-2'}
        response = self._create_annotation(**kwargs)
        self.assertTrue('id' in response)

        # if another user to tries to create note in first course it should succeed
        token = get_id_token(TEST_OTHER_USER)
        self.client.credentials(HTTP_X_ANNOTATOR_AUTH_TOKEN=token)
        self.headers = {'user': TEST_OTHER_USER}
        kwargs = {'user': TEST_OTHER_USER}
        response = self._create_annotation(**kwargs)
        self.assertTrue('id' in response)

    def test_read_all_no_annotations(self):
        """
        Tests list all annotations endpoint when no annotations are present in database.
        """
        headers = self.headers.copy()
        headers["course_id"] = "a/b/c"
        response = self.client.get(reverse('api:v1:annotations'), headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictContainsSubset(
            {'total': 0, 'rows': []}, response.data, "no annotation should be returned in response"
        )

    def test_read_all(self):
        """
        Tests list all annotations.
        """
        for i in range(5):
            kwargs = {'text': 'Foo_{}'.format(i)}
            self._create_annotation(**kwargs)

        headers = self.headers.copy()
        headers["course_id"] = "test-course-id"
        response = self.client.get(reverse('api:v1:annotations'), headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 5, "five annotations should be returned in response")

    def test_read_all_ordering(self):
        """
        Tests ordering of listing of all notes.

        Sorting is by descending order (most recent first).
        """
        self._create_annotation(text=u'First one')
        self._create_annotation(text=u'Second note')
        self._create_annotation(text=u'Third note')

        headers = self.headers.copy()
        headers["course_id"] = "test-course-id"
        results = self.client.get(reverse('api:v1:annotations'), headers).data

        self.assertEqual(results['rows'][0]['text'], 'Third note')
        self.assertEqual(results['rows'][1]['text'], 'Second note')
        self.assertEqual(results['rows'][2]['text'], 'First one')

    def test_read_all_no_query_param(self):
        """
        Tests list all annotations when course_id query param is not present.
        """
        response = self.client.get(reverse('api:v1:annotations'), self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @ddt.unpack
    @ddt.data(
        {'page': 1, 'annotations_per_page': 10, 'previous_page': None, 'next_page': 2, 'start': 0},
        {'page': 2, 'annotations_per_page': 10, 'previous_page': 1, 'next_page': 3, 'start': 10},
        {'page': 3, 'annotations_per_page': 3, 'previous_page': 2, 'next_page': None, 'start': 20}
    )
    # pylint: disable=too-many-arguments
    def test_pagination_multiple_pages(self, page, annotations_per_page, previous_page, next_page, start):
        """
        Verify that pagination info is correct when we have data spanned on multiple pages.
        """
        self.verify_list_view_pagination(
            query_parameters={'page': page},
            total_annotations=23,
            num_pages=3,
            annotations_per_page=annotations_per_page,
            current_page=page,
            previous_page=previous_page,
            next_page=next_page,
            start=start
        )

    def test_pagination_single_page(self):
        """
        Verify that pagination info is correct when we have a single page of data.
        """
        self.verify_list_view_pagination(
            query_parameters=None,
            total_annotations=6,
            num_pages=1,
            annotations_per_page=6,
            current_page=1,
            previous_page=None,
            next_page=None,
            start=0
        )

    @ddt.unpack
    @ddt.data(
        {'page_size': 2, 'annotations_per_page': 2, 'num_pages': 8, 'next_page': 2},
        {'page_size': 15, 'annotations_per_page': 15, 'num_pages': 1, 'next_page': None},
    )
    def test_pagination_page_size(self, page_size, annotations_per_page, num_pages, next_page):
        """
        Verify that requests for different page_size returns correct pagination info.
        """
        self.verify_list_view_pagination(
            query_parameters={'page_size': page_size},
            total_annotations=15,
            num_pages=num_pages,
            annotations_per_page=annotations_per_page,
            current_page=1,
            previous_page=None,
            next_page=next_page,
            start=0
        )

    @ddt.unpack
    @ddt.data(
        {'page': 1, 'start': 0, 'previous_page': None, 'next_page': 2},
        {'page': 2, 'start': 5, 'previous_page': 1, 'next_page': 3},
        {'page': 3, 'start': 10, 'previous_page': 2, 'next_page': None},
    )
    def test_pagination_page_start(self, page, start, previous_page, next_page):
        """
        Verify that start value is correct for different pages.
        """
        self.verify_list_view_pagination(
            query_parameters={'page': page, 'page_size': 5},
            total_annotations=15,
            num_pages=3,
            annotations_per_page=5,
            current_page=page,
            previous_page=previous_page,
            next_page=next_page,
            start=start
        )

    def test_delete_all_user_annotations(self, user_id=TEST_USER):
        """
        Verify that deleting all user annotations works
        """
        self._create_annotation(text=u'Comment with foo', tags=[u'bar'])
        self._create_annotation(text=u'Another comment', tags=[u'foo'])
        self._create_annotation(text=u'A longer comment with bar', tags=[u'foo'])
        response = self._get_search_results()
        self.assertEqual(response["total"], 3)

        url = reverse('api:v1:annotations_retire')
        self.payload["user"] = user_id
        # Delete all notes for User 1
        response = self.client.post(url, headers=self.headers, data=self.payload)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify notes are deleted for User 1
        response = self._get_search_results()
        self.assertEqual(response["total"], 0)

        # Reattempt delete for User 1
        response = self.client.post(url, headers=self.headers, data=self.payload)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_all_user_annotations_no_user(self):
        """
        Test case where no user is specified when user deletion is requested.

        The result should be a 403 response, with the following logging:

            notesapi.v1.permissions: INFO: No user was present to compare in GET, POST or DATA
        """
        self._create_annotation(text=u'Comment with foo', tags=[u'bar'])
        self._create_annotation(text=u'Another comment', tags=[u'foo'])
        self._create_annotation(text=u'A longer comment with bar', tags=[u'foo'])
        response = self._get_search_results()
        self.assertEqual(response["total"], 3)

        url = reverse('api:v1:annotations_retire')
        del self.payload['user']
        response = self.client.post(url, headers=self.headers, data=self.payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Verify no notes are deleted
        response = self._get_search_results()
        self.assertEqual(response["total"], 3)

    def test_delete_all_user_annotations_other_user(self):
        """
        Test the case where the user specified in params doesn't appear to match the one in the token.

        In this case, the response should be 403 and logging should indicate some sort of token user mismatch failure:

            notesapi.v1.permissions: DEBUG: Token user test_user_id did not match data user test_other_user_id
        """
        self._create_annotation(text=u'Comment with foo', tags=[u'bar'])
        self._create_annotation(text=u'Another comment', tags=[u'foo'])
        self._create_annotation(text=u'A longer comment with bar', tags=[u'foo'])
        response = self._get_search_results()
        self.assertEqual(response["total"], 3)

        url = reverse('api:v1:annotations_retire')
        self.payload["user"] = TEST_OTHER_USER
        response = self.client.post(url, headers=self.headers, data=self.payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Verify no notes are deleted
        response = self._get_search_results()
        self.assertEqual(response["total"], 3)


@ddt.ddt
class AnnotationDetailViewTests(BaseAnnotationViewTests):
    """
    Test one annotation updating, reading and deleting
    """
    def test_read(self):
        """
        Ensure we can get an existing annotation.
        """
        note_id = self._create_annotation(**self.payload)['id']

        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': note_id})
        response = self.client.get(url, self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        annotation = response.data
        self.assertEqual(type(annotation['id']), str)
        del annotation['id']
        del annotation['updated']
        del annotation['created']
        self.assertEqual(annotation, self.payload)

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
        response, annotation = self._do_annotation_update(data, {'id': data['id'], 'text': 'Bar'})
        self.assertEqual(annotation['text'], "Bar", "annotation wasn't updated in db")
        self.assertEqual(response.data['text'], "Bar", "update annotation should be returned in response")

    @ddt.data(
        (["new", "tags"], ["new", "tags"]),
        ([], []),
        (None, [u"pink", u"lady"]),
    )
    @ddt.unpack
    def test_update_tags(self, updated_tags, expected_tags):
        """
        Test that we can update tags on an existing annotation.
        """
        data = self._create_annotation()
        # If no tags are sent in the update, previously present tags should remain.
        if updated_tags is None:
            response, annotation = self._do_annotation_update(data, {'id': data['id']})
        else:
            response, annotation = self._do_annotation_update(data, {'id': data['id'], 'tags': updated_tags})
        self.assertEqual(annotation["tags"], expected_tags)
        self.assertEqual(response.data["tags"], expected_tags)

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


@ddt.ddt
class AnnotationSearchViewTests(BaseAnnotationViewTests):
    """
    Test annotation searching by user, course_id, usage_id and text
    """

    def test_search(self):
        """
        Tests for search method with case insensitivity for text param.
        """
        self._create_annotation(text=u'First one', tags=[])
        self._create_annotation(text=u'Second note', tags=[u'tag1', u'tag2'])
        note = self._create_annotation(text=u'Third note')
        del note['created']
        del note['updated']

        results = self._get_search_results()
        last_note = results['rows'][0]
        del last_note['created']
        del last_note['updated']
        self.assertEqual(last_note, note)
        self.assertEqual(results['total'], 3)

        def search_and_verify(search_text, expected_text, expected_tags):
            """ Test the results from a specific text search operation """
            results = self._get_search_results(text=search_text)
            self.assertEqual(results['total'], 1)
            self.assertEqual(len(results['rows']), 1)
            self.assertEqual(results['rows'][0]['text'], expected_text)
            self.assertEqual(results['rows'][0]['tags'], expected_tags)

        search_and_verify(search_text="First", expected_text="First one", expected_tags=[])
        search_and_verify(search_text="first", expected_text="First one", expected_tags=[])
        search_and_verify(search_text="Second", expected_text="Second note", expected_tags=["tag1", "tag2"])

    @ddt.data(True, False)
    def test_usage_id_search(self, is_es_disabled):
        """
        Verifies the search with usage id.
        """
        self._create_annotation(text=u'First one', usage_id='test-1')
        self._create_annotation(text=u'Second note', usage_id='test-2')
        self._create_annotation(text=u'Third note', usage_id='test-3')

        @patch('django.conf.settings.ES_DISABLED', is_es_disabled)
        def verify_usage_id_search(usage_ids):
            """
            Verify search results based on usage id operation.

            Arguments:
                usage_ids: List. The identifier string of the annotations XBlock(s).
            """
            results = self._get_search_results(usage_id=usage_ids)
            self.assertEqual(len(results), len(usage_ids))
            # Here we are reverse-traversing usage_ids because response has descending ordered rows.
            for index, u_id in enumerate(usage_ids[::-1]):
                self.assertEqual(results[index]['usage_id'], u_id)

        verify_usage_id_search(usage_ids=['test-1'])
        verify_usage_id_search(usage_ids=['test-1', 'test-2', 'test-3'])

    def test_search_deleted(self):
        """
        Tests for search method to not return deleted notes.
        """
        note = self._create_annotation(text=u'To-be-deleted one')
        self._create_annotation(text=u'Second one')

        results = self._get_search_results()
        self.assertEqual(results['total'], 2)

        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': note['id']})
        response = self.client.delete(url, self.headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, "response should be 204 NO CONTENT")

        results = self._get_search_results()
        self.assertEqual(results['total'], 1)
        self.assertEqual(results['rows'][0]['text'], 'Second one')

    @unittest.skipIf(settings.ES_DISABLED, "MySQL does not do highlighing")
    def test_search_highlight(self):
        """
        Tests highlighting.
        """
        self._create_annotation(text=u'First note')
        self._create_annotation(text=u'Second note')

        results = self._get_search_results()
        self.assertEqual(results['total'], 2)

        results = self._get_search_results(text="first", highlight=True)
        self.assertEqual(results['total'], 1)
        self.assertEqual(len(results['rows']), 1)
        self.assertEqual(
            results['rows'][0]['text'],
            '{elasticsearch_highlight_start}First{elasticsearch_highlight_end} note'
        )

    @unittest.skipIf(settings.ES_DISABLED, "MySQL does not do highlighing")
    def test_search_highlight_with_long_text(self):
        """
        Tests highlighting with long text.
        """
        text = "Lorem " + "word " * 100 + " Lorem"

        start_tag = "{elasticsearch_highlight_start}"
        end_tag = "{elasticsearch_highlight_end}"

        expected_text = "{start_tag}Lorem{end_tag} {word} {start_tag}Lorem{end_tag}".format(
            start_tag=start_tag,
            end_tag=end_tag,
            word="word " * 100
        )

        self._create_annotation(text=text)
        self._create_annotation(text=u'Second note')

        results = self._get_search_results()
        self.assertEqual(results['total'], 2)

        results = self._get_search_results(text="Lorem", highlight=True)
        self.assertEqual(results['total'], 1)
        self.assertEqual(len(results['rows']), 1)
        self.assertEqual(
            results['rows'][0]['text'],
            expected_text
        )

    @override_settings(ES_DISABLED=True)
    def test_search_ordering_in_db(self):
        """
        Tests ordering of search results from MySQL.

        MySQL sorting is by descending order by updated field (most recent first).
        """
        self._create_annotation(text=u'First one')
        note = self._create_annotation(text=u'Second note')
        self._create_annotation(text=u'Third note')

        payload = self.payload.copy()
        payload.update({'id': note['id'], 'text': 'Updated Second Note'})
        payload.update(self.headers)
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': note['id']})
        self.client.put(url, payload, format='json')

        results = self._get_search_results()
        self.assertEqual(results['rows'][0]['text'], 'Updated Second Note')
        self.assertEqual(results['rows'][1]['text'], 'Third note')
        self.assertEqual(results['rows'][2]['text'], 'First one')

    @unittest.skipIf(settings.ES_DISABLED, "MySQL does not do relevance ordering")
    def test_search_ordering_in_es(self):
        """
        Tests order of search results from ElasticSearch.

        ElasticSearch sorting is based on the computed relevance of each hit.
        """
        self._create_annotation(text=u'fox of the foxes')
        self._create_annotation(text=u'a very long entry that contains the word fox')
        self._create_annotation(text=u'the lead fox')
        self._create_annotation(text=u'does not mention the word')

        results = self._get_search_results(text='fox')
        self.assertEqual(results['total'], 3)
        self.assertEqual(results['rows'][0]['text'], 'fox of the foxes')
        self.assertEqual(results['rows'][1]['text'], 'the lead fox')
        self.assertEqual(results['rows'][2]['text'], 'a very long entry that contains the word fox')

    @unittest.skipIf(settings.ES_DISABLED, "Unicode support in MySQL is limited")
    def test_search_unicode(self):
        """
        Tests searching of unicode strings.
        """
        self._create_annotation(text=u'Веселих свят')

        response = self._get_search_results(text=u"веселих")
        self.assertEqual(response['total'], 1)
        self.assertEqual(response['rows'][0]['text'], u'Веселих свят')

        response = self._get_search_results(text=u"Свят")
        self.assertEqual(response['rows'][0]['text'], u'Веселих свят')

    @ddt.unpack
    @ddt.data(
        {"text": u"Веселих свят", 'text_to_search': u"веселих", 'result': u"{}Веселих{} свят"},
        {"text": "The Hunger games", 'text_to_search': "Hunger", 'result': "The {}Hunger{} games"}
    )
    @unittest.skipIf(settings.ES_DISABLED, "MySQL cannot do highlighting")
    def test_search_with_highlighting(self, text, text_to_search, result):
        """
        Tests searching of unicode and non-unicode text with highlighting enabled.
        """
        start_tag = "{elasticsearch_highlight_start}"
        end_tag = "{elasticsearch_highlight_end}"

        self._create_annotation(text=text)

        response = self._get_search_results(text=text_to_search, highlight=True)
        self.assertEqual(response['total'], 1)
        self.assertEqual(response['rows'][0]['text'], result.format(start_tag, end_tag))

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

    def test_search_by_course_id(self):
        """
        Tests searching with course_id provided
        """
        self._create_annotation(text=u'First one', course_id="u'edX/DemoX/Demo_Course'")
        self._create_annotation(text=u'Second note', course_id="u'edX/DemoX/Demo_Course'")
        self._create_annotation(text=u'Third note', course_id="b")
        self._create_annotation(text=u'Fourth note', course_id="c")

        results = self._get_search_results(course_id="u'edX/DemoX/Demo_Course'")
        self.assertEqual(results['total'], 2)

        results = self._get_search_results(course_id="b")
        self.assertEqual(results['total'], 1)
        self.assertEqual(results['rows'][0]['text'], u'Third note')

    def test_search_tag(self):
        """
        Tests searching for tags
        """
        self._create_annotation(text=u'First note', tags=[u'foo', u'bar'])
        self._create_annotation(text=u'Another one', tags=[u'bar'])
        self._create_annotation(text=u'A third note', tags=[u'bar', u'baz'])
        self._create_annotation(text=u'One final note', tags=[])

        results = self._get_search_results(text='Foo')
        self.assertEqual(results['total'], 1)
        self.assertEqual(results['rows'][0]['text'], 'First note')

        results = self._get_search_results(text='bar')
        self.assertEqual(results['total'], 3)
        self._has_text(results['rows'], ['First note', 'Another one', 'A third note'])

        results = self._get_search_results(text='baz')
        self.assertEqual(results['total'], 1)
        self.assertEqual(results['rows'][0]['text'], 'A third note')

    def test_search_tag_or_text(self):
        """
        Tests that searches can match against tags or text
        """
        self._search_tag_or_text()

    @override_settings(ES_DISABLED=True)
    def test_search_tag_or_text_in_db(self):
        """
        Tests that searches can match against tags or text without ElasticSearch
        """
        self._search_tag_or_text()

    def _search_tag_or_text(self):
        """
        Tests that searches can match against tags or text
        """
        self._create_annotation(text=u'A great comment', tags=[])
        self._create_annotation(text=u'Another comment', tags=['good'])
        self._create_annotation(text=u'Not as good', tags=['comment'])
        self._create_annotation(text=u'Last note', tags=[])

        results = self._get_search_results(text='note')
        self.assertEqual(results['total'], 1)
        self._has_text(results['rows'], ['Last note'])

        results = self._get_search_results(text='good')
        self.assertEqual(results['total'], 2)
        self._has_text(results['rows'], ['Another comment', 'Not as good'])

        results = self._get_search_results(text='comment')
        self.assertEqual(results['total'], 3)
        self._has_text(results['rows'], ['A great comment', 'Another comment', 'Not as good'])

    def _has_text(self, rows, expected):
        """
        Tests that the set of expected text is exactly the text in rows, ignoring order.
        """
        self.assertEqual(set(row['text'] for row in rows), set(expected))

    @unittest.skipIf(settings.ES_DISABLED, "MySQL does not do data templating")
    def test_search_across_tag_and_text(self):
        """
        Tests that searches can match if some terms are in the text and the rest are in the tags.
        """
        self._create_annotation(text=u'Comment with foo', tags=[u'bar'])
        self._create_annotation(text=u'Another comment', tags=[u'foo'])
        self._create_annotation(text=u'A longer comment with bar', tags=[u'foo'])

        results = self._get_search_results(text='foo bar')
        self.assertEqual(results['total'], 2)
        self.assertEqual(results['rows'][0]['text'], 'Comment with foo')
        self.assertEqual(results['rows'][1]['text'], 'A longer comment with bar')

    @unittest.skipIf(settings.ES_DISABLED, "MySQL does not do highlighing")
    def test_search_highlight_tag(self):
        """
        Tests highlighting in tags
        """
        self._create_annotation(text=u'First note', tags=[u'foo', u'bar'])
        self._create_annotation(text=u'Second note', tags=[u'baz'])

        results = self._get_search_results()
        self.assertEqual(results['total'], 2)

        results = self._get_search_results(text="bar", highlight=True)
        self.assertEqual(results['total'], 1)
        self.assertEqual(len(results['rows']), 1)
        self.assertEqual(
            results['rows'][0]['tags'],
            ['foo', '{elasticsearch_highlight_start}bar{elasticsearch_highlight_end}']
        )

    @ddt.unpack
    @ddt.data(
        {'page': 1, 'annotations_per_page': 10, 'previous_page': None, 'next_page': 2, 'start': 0},
        {'page': 2, 'annotations_per_page': 10, 'previous_page': 1, 'next_page': 3, 'start': 10},
        {'page': 3, 'annotations_per_page': 3, 'previous_page': 2, 'next_page': None, 'start': 20}
    )
    # pylint: disable=too-many-arguments
    def test_pagination_multiple_pages(self, page, annotations_per_page, previous_page, next_page, start):
        """
        Verify that pagination info is correct when we have data spanned on multiple pages.
        """
        self.verify_search_view_pagination(
            query_parameters={'page': page},
            total_annotations=23,
            num_pages=3,
            annotations_per_page=annotations_per_page,
            current_page=page,
            previous_page=previous_page,
            next_page=next_page,
            start=start
        )

    def test_pagination_single_page(self):
        """
        Verify that pagination info is correct when we have a single page of data.
        """
        self.verify_search_view_pagination(
            query_parameters={},
            total_annotations=6,
            num_pages=1,
            annotations_per_page=6,
            current_page=1,
            previous_page=None,
            next_page=None,
            start=0
        )

    @ddt.unpack
    @ddt.data(
        {'page_size': 2, 'annotations_per_page': 2, 'num_pages': 8, 'next_page': 2},
        {'page_size': 15, 'annotations_per_page': 15, 'num_pages': 1, 'next_page': None},
    )
    def test_pagination_page_size(self, page_size, annotations_per_page, num_pages, next_page):
        """
        Verify that requests for different page_size returns correct pagination info.
        """
        self.verify_search_view_pagination(
            query_parameters={'page_size': page_size},
            total_annotations=15,
            num_pages=num_pages,
            annotations_per_page=annotations_per_page,
            current_page=1,
            previous_page=None,
            next_page=next_page,
            start=0
        )

    @ddt.unpack
    @ddt.data(
        {'page': 1, 'start': 0, 'previous_page': None, 'next_page': 2},
        {'page': 2, 'start': 5, 'previous_page': 1, 'next_page': 3},
        {'page': 3, 'start': 10, 'previous_page': 2, 'next_page': None},
    )
    def test_pagination_page_start(self, page, start, previous_page, next_page):
        """
        Verify that start value is correct for different pages.
        """
        self.verify_search_view_pagination(
            query_parameters={'page': page, 'page_size': 5},
            total_annotations=15,
            num_pages=3,
            annotations_per_page=5,
            current_page=page,
            previous_page=previous_page,
            next_page=next_page,
            start=start
        )

    @ddt.unpack
    @ddt.data(
        {"text": u"Ammar محمد عمار Muhammad", "search": u"محمد عمار", "tags": [u"عمار", u"Muhammad", u"محمد"]},
        {"text": u"Ammar محمد عمار Muhammad", "search": u"محمد", "tags": [u"محمد", u"Muhammad"]},
        {"text": u"Ammar محمد عمار Muhammad", "search": u"عمار", "tags": [u"ammar", u"عمار"]},
        {"text": u"Muhammad Ammar", "search": u"عمار", "tags": [u"ammar", u"عمار"]},
        {"text": u"محمد عمار", "search": u"Muhammad", "tags": [u"Muhammad", u"عمار"]}
    )
    @unittest.skipIf(settings.ES_DISABLED, "MySQL cannot do highlighting")
    def test_search_unicode_text_and_tags(self, text, search, tags):
        """
        Verify that search works as expected with unicode and non-unicode text and tags.
        """
        self._create_annotation(text=text, tags=tags)

        response = self._get_search_results(text=search)
        self.assertEqual(response["total"], 1)
        self.assertEqual(response["rows"][0]["text"], text)
        self.assertEqual(response["rows"][0]["tags"], tags)


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
        403 when token's intended audience is wrong
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

    def test_no_user(self):
        """
        403 when user is not present in request
        """
        del self.headers['user']
        self._assert_403(jwt.encode(self.token_data, settings.CLIENT_SECRET))

    def test_wrong_secret(self):
        """
        403 when token is signed by wrong secret
        """
        token = jwt.encode(self.token_data, "some secret")
        self._assert_403(token)

    def test_multifield_user(self):
        """
        403 when user in GET matches token, but in POST does not
        """
        url = reverse('api:v1:annotations')
        self.payload['user'] = 'other-user'
        response = self.client.post(url + "?user=" + TEST_USER, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
