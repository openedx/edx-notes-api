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
        response = self.client.get(reverse('status'))
        self.assertEquals(response.status_code, 200)

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
