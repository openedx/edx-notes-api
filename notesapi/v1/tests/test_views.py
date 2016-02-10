# -*- coding: utf-8 -*-
import jwt
import unittest
import ddt
from calendar import timegm
from datetime import datetime, timedelta
from mock import patch

from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import QueryDict
from django.test.utils import override_settings

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

    def _create_annotation(self, **kwargs):
        """
        Create annotation
        """
        opts = self.payload.copy()
        opts.update(kwargs)
        url = reverse('api:v1:annotations')
        response = self.client.post(url, opts, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data.copy()

    def _create_annotation_without_assert(self, **kwargs):
        """
        Create annotation but do not check for 201
        """
        opts = self.payload.copy()
        opts.update(kwargs)
        url = reverse('api:v1:annotations')
        response = self.client.post(url, opts, format='json')
        return response

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

    @ddt.data(
        (6, False),
        (4, True)
    )
    @ddt.unpack
    def test_create_maximum_allowed(self, num_notes, should_create):
        """
        Tests user can not create more than allowed notes/annotations per course
        """
        for i in xrange(num_notes - 1):
            kwargs = {'text': 'Foo_{}'.format(i)}
            self._create_annotation(**kwargs)

        # Creating more notes should result in 400 error
        kwargs = {'text': 'Foo_{}'.format(num_notes)}
        response = self._create_annotation_without_assert(**kwargs)

        if not should_create:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, 'Creating more than allowed notes')
            self.assertEqual(
                response.data['error_msg'],
                u'You can create up to {0} notes.'
                u' You must remove some notes before you can add new ones.'.format(settings.MAX_ANNOTATIONS_PER_COURSE)
            )
        else:
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_maximum_allowed_other(self):
        # if user tries to create notes in another course it should succeed
        for i in xrange(5):
            kwargs = {'text': 'Foo_{}'.format(i)}
            self._create_annotation(**kwargs)

        # Creating more notes should result in 400 error
        kwargs = {'text': 'Foo_{}'.format(6)}
        response = self._create_annotation_without_assert(**kwargs)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, 'Creating more than allowed notes')
        self.assertEqual(
            response.data['error_msg'],
            u'You can create up to {0} notes.'
            u' You must remove some notes before you can add new ones.'.format(settings.MAX_ANNOTATIONS_PER_COURSE)
        )

        # if user tries to create note in a different course it should succeed
        kwargs = {'course_id': 'test-course-id-2'}
        response = self._create_annotation(**kwargs)
        self.assertFalse(hasattr(response, 'data'))

        # if another user to tries to create note in first course it should succeed
        token = get_id_token(TEST_OTHER_USER)
        self.client.credentials(HTTP_X_ANNOTATOR_AUTH_TOKEN=token)
        self.headers = {'user': TEST_OTHER_USER}
        kwargs = {'user': TEST_OTHER_USER}
        response = self._create_annotation(**kwargs)
        self.assertFalse(hasattr(response, 'data'))

    def test_read_all_no_annotations(self):
        """
        Tests list all annotations endpoint when no annotations are present in database.
        """
        headers = self.headers.copy()
        headers["course_id"] = "a/b/c"
        response = self.client.get(reverse('api:v1:annotations'), headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0, "no annotation should be returned in response")

    def test_read_all(self):
        """
        Tests list all annotations.
        """
        for i in xrange(5):
            kwargs = {'text': 'Foo_{}'.format(i)}
            self._create_annotation(**kwargs)

        headers = self.headers.copy()
        headers["course_id"] = "test-course-id"
        response = self.client.get(reverse('api:v1:annotations'), headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5, "five annotations should be returned in response")

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

        self.assertEqual(results[0]['text'], 'Third note')
        self.assertEqual(results[1]['text'], 'Second note')
        self.assertEqual(results[2]['text'], 'First one')

    def test_read_all_no_query_param(self):
        """
        Tests list all annotations when course_id query param is not present.
        """
        response = self.client.get(reverse('api:v1:annotations'), self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


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


class AnnotationSearchViewTests(BaseAnnotationViewTests):
    """
    Test annotation searching by user, course_id, usage_id and text
    """

    def test_search(self):
        """
        Tests for search method.
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

        def search_and_verify(searchText, expectedText, expectedTags):
            """ Test the results from a specific text search operation """
            results = self._get_search_results(text=searchText)
            self.assertEqual(results['total'], 1)
            self.assertEqual(len(results['rows']), 1)
            self.assertEqual(results['rows'][0]['text'], expectedText)
            self.assertEqual(results['rows'][0]['tags'], expectedTags)

        search_and_verify("First", "First one", [])
        search_and_verify("Second", "Second note", ["tag1", "tag2"])

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
        self.assertEqual(results['rows'][0]['text'], '<em>First</em> note')

        results = self._get_search_results(text="first", highlight=True, highlight_tag='tag')
        self.assertEqual(results['rows'][0]['text'], '<tag>First</tag> note')

        results = self._get_search_results(text="first", highlight=True, highlight_tag='tag', highlight_class='klass')
        self.assertEqual(results['rows'][0]['text'], '<tag class="klass">First</tag> note')


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
        self.assertEquals(results['total'], 2)
        self._has_text(results['rows'], ['Another comment', 'Not as good'])

        results = self._get_search_results(text='comment')
        self.assertEquals(results['total'], 3)
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
        self.assertEqual(results['rows'][0]['tags'], ['foo', '<em>bar</em>'])

        results = self._get_search_results(text="bar", highlight=True, highlight_tag='tag')
        self.assertEqual(results['rows'][0]['tags'], ['foo', '<tag>bar</tag>'])

        results = self._get_search_results(text="bar", highlight=True, highlight_tag='tag', highlight_class='klass')
        self.assertEqual(results['rows'][0]['tags'], ['foo', '<tag class="klass">bar</tag>'])


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
