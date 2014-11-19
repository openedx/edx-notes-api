from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

class OperationalEndpointsTest(APITestCase):
    """
    Tests for operational endpoints.
    """
    def test_status(self):
        """
        Test if server is alive.
        """
        response = self.client.get('/status', follow=True)
        self.assertEquals(response.status_code, 200)
