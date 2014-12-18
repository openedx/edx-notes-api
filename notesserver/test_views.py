import datetime
import base64
from mock import patch, Mock
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from elasticsearch.exceptions import TransportError

class OperationalEndpointsTest(APITestCase):
    """
    Tests for operational endpoints.
    """
    def test_heartbeat(self):
        """
        Heartbeat endpoint success.
        """
        response = self.client.get(reverse('heartbeat'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.data, {"OK": True})

    @patch('annotator.elasticsearch.ElasticSearch.conn')
    def test_heartbeat_failure(self, mocked_conn):
        """
        Elasticsearch is not reachable.
        """
        mocked_conn.ping.return_value = False
        response = self.client.get(reverse('heartbeat'))
        self.assertEquals(response.status_code, 500)
        self.assertEquals(response.data, {"OK": False, "check": "es"})

    def test_root(self):
        """
        Test root endpoint.
        """
        response = self.client.get(reverse('root'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(
            response.data,
            {
                "name": "edX Notes API",
                "version": "1"
            }
        )

class OperationalAuthEndpointsTest(APITestCase):
    """
    Tests for operational authenticated endpoints.
    """

    def test_selftest_status(self):
        """
        Test status on authorization success.
        """
        response = self.client.get(reverse('selftest'))
        self.assertEquals(response.status_code, 200)

    @patch('notesserver.views.datetime', datetime=Mock(wraps=datetime.datetime))
    @patch('annotator.elasticsearch.ElasticSearch.conn')
    def test_selftest_data(self, mocked_conn, mocked_datetime):
        """
        Test returned data on success.
        """
        mocked_datetime.datetime.now.return_value = datetime.datetime(2014, 12, 11)
        mocked_conn.info.return_value = {}
        response = self.client.get(reverse('selftest'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(
            response.data,
            {
                "es": {},
                "time_elapsed": 0.0
            }
        )

    @patch('annotator.elasticsearch.ElasticSearch.conn')
    def test_selftest_failure(self, mocked_conn):
        """
        Elasticsearch is not reachable on selftest.
        """
        mocked_conn.info.side_effect = TransportError()
        response = self.client.get(reverse('selftest'))
        self.assertEquals(response.status_code, 500)
