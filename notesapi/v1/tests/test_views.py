from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from annotator import annotation, es, auth
from annotator.annotation import Annotation
from .helpers import MockUser


class AnnotationViewTests(APITestCase):
    """
    Tests for annotation views.
    """
    def setUp(self):
        annotation.Annotation.create_all()
        es.conn.cluster.health(wait_for_status='yellow')

        self.user = MockUser()
        payload = {'consumerKey': self.user.consumer.key, 'userId': self.user.id}
        token = auth.encode_token(payload, self.user.consumer.secret)
        self.headers = {'x-annotator-auth-token': token}

    def tearDown(self):
        annotation.Annotation.drop_all()

    def _create_annotation(self, refresh=True, **kwargs):
        """
        Create annotation directly in elasticsearch.
        """
        opts = {
            'user': self.user.id,
            'consumer': self.user.consumer.key
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

    def test_add_note(self):
        """
        Ensure we can create a new note.
        """
        url = reverse('api:v1:annotations')
        payload = {'text': 'testing notes'}
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data, "annotation id should be returned in response")

        expected_location = '/api/v1/annotations/{0}'.format(response.data['id'])
        self.assertTrue(response['Location'].endswith(expected_location), "The response should have a Location header "
            "with the URL to read the annotation that was created")

        #self.assertEqual(self.user.id, response.data['user'])
        #self.assertEqual(self.user.consumer.key, response.data['consumer'])

    def test_read(self):
        """
        Ensure we can get an existing annotation.
        """
        kwargs = dict(text=u"Foo", id='123')
        self._create_annotation(**kwargs)
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': 123})
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.data['id'], '123', "annotation id should be returned in response")
        self.assertEqual(response.data['text'], "Foo", "annotation text should be returned in response")

    def test_read_notfound(self):
        """
        Case when no annotation is present with specific id.
        """
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': 123})
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, "response should be 404 NOT FOUND")

    def test_update(self):
        """
        Ensure we can update an existing annotation.
        """
        self._create_annotation(text=u"Foo", id='123', created='2014-10-10')
        payload = {'id': '123', 'text': 'Bar'}
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': 123})
        response = self.client.put(url, payload, format='json')
        annotation = self._get_annotation('123')

        self.assertEqual(annotation['text'], "Bar", "annotation wasn't updated in db")
        self.assertEqual(response.data['text'], "Bar", "update annotation should be returned in response")

    def test_delete(self):
        """
        Ensure we can delete an existing annotation.
        """
        kwargs = dict(text=u"Bar", id='456')
        self._create_annotation(**kwargs)
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': 456})
        response = self.client.delete(url, **self.headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, "response should be 204 NO CONTENT")
        self.assertEqual(self._get_annotation('456'), None, "annotation wasn't deleted in db")

    def test_delete_notfound(self):
        """
        Case when no annotation is present with specific id when trying to delete.
        """
        url = reverse('api:v1:annotations_detail', kwargs={'annotation_id': 123})
        response = self.client.delete(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, "response should be 404 NOT FOUND")

    def test_search(self):
        """
        Tests for search method.
        """
        note_1 = self._create_annotation(text=u'Note 1', user=u'user_3')
        note_2 = self._create_annotation(text=u'Note 2', user=u'user_2')
        note_3 = self._create_annotation(text=u'Note 3', user=u'user_3')

        results = self._get_search_results()
        self.assertEqual(results['total'], 3)

        results = self._get_search_results('limit=1')
        self.assertEqual(results['total'], 3)
        self.assertEqual(len(results['rows']), 1)

    def test_search_limit(self):
        """
        Tests for limit query parameter for paging through results.
        """
        for i in xrange(250):
            self._create_annotation(refresh=False)

        es.conn.indices.refresh(es.index)

        # By default return 20. See RESULTS_DEFAULT_SIZE in annotator.
        result = self._get_search_results()
        self.assertEqual(len(result['rows']), 20)

        # Return maximum 200. See RESULTS_MAX_SIZE in annotator.
        result = self._get_search_results('limit=250')
        self.assertEqual(len(result['rows']), 200)

        # Return minimum 0.
        result = self._get_search_results('limit=-10')
        self.assertEqual(len(result['rows']), 0)

        # Ignore bogus values.
        result = self._get_search_results('limit=foobar')
        self.assertEqual(len(result['rows']), 20)

    def test_search_offset(self):
        """
        Tests for offset query parameter for paging through results.
        """
        for i in xrange(250):
            self._create_annotation(refresh=False)

        es.conn.indices.refresh(es.index)

        result = self._get_search_results()
        self.assertEqual(len(result['rows']), 20)
        first = result['rows'][0]

        result = self._get_search_results('offset=240')
        self.assertEqual(len(result['rows']), 10)

        # ignore negative values
        result = self._get_search_results('offset=-10')
        self.assertEqual(len(result['rows']), 20)
        self.assertEqual(result['rows'][0], first)

        # ignore bogus values
        result = self._get_search_results('offset=foobar')
        self.assertEqual(len(result['rows']), 20)
        self.assertEqual(result['rows'][0], first)

    def _get_search_results(self, qs=''):
        """
        Helper for search method.
        """
        url = reverse('api:v1:annotations_search') + '?{}'.format(qs)
        result = self.client.get(url, **self.headers)
        return result.data
