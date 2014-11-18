from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from annotator import annotation, es, auth
from annotator.annotation import Annotation
from .helpers import MockUser

class AnnotationListViewTests(APITestCase):

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
        opts = {
            'user': self.user.id,
            'consumer': self.user.consumer.key
        }
        opts.update(kwargs)
        annotation = Annotation(**opts)
        annotation.save(refresh=refresh)
        return annotation

    def _get_annotation(self, id_):
        return Annotation.fetch(id_)

    def test_add_note(self):
        """
        Ensure we can create a new note.
        """
        url = reverse('api:v0:annotations')
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
        kwargs = dict(text=u"Foo", id='123')
        self._create_annotation(**kwargs)
        url = reverse('api:v0:annotations_detail', kwargs={'annotation_id': 123})
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.data['id'], '123', "annotation id should be returned in response")
        self.assertEqual(response.data['text'], "Foo", "annotation text should be returned in response")

    def test_read_notfound(self):
        url = reverse('api:v0:annotations_detail', kwargs={'annotation_id': 123})
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, "response should be 404 NOT FOUND")

    def test_update(self):
        self._create_annotation(text=u"Foo", id='123', created='2014-10-10')
        payload = {'id': '123', 'text': 'Bar'}
        url = reverse('api:v0:annotations_detail', kwargs={'annotation_id': 123})
        response = self.client.put(url, payload, format='json')
        annotation = self._get_annotation('123')

        self.assertEqual(annotation['text'], "Bar", "annotation wasn't updated in db")
        self.assertEqual(response.data['text'], "Bar", "update annotation should be returned in response")

    def test_delete(self):
        kwargs = dict(text=u"Bar", id='456')
        self._create_annotation(**kwargs)
        url = reverse('api:v0:annotations_detail', kwargs={'annotation_id': 456})
        response = self.client.delete(url, **self.headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, "response should be 204 NO CONTENT")
        self.assertEqual(self._get_annotation('456'), None, "annotation wasn't deleted in db")

    def test_delete_notfound(self):
        url = reverse('api:v0:annotations_detail', kwargs={'annotation_id': 123})
        response = self.client.delete(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, "response should be 404 NOT FOUND")
