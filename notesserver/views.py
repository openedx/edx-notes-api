import requests
import json
from django.http import HttpResponse
from django.conf import settings


from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class StatusView(APIView):
    """
    Determine if server is alive.
    """
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response({})


class AnnotationListView(APIView):
    """
    List all annotations or create.
    """
    permission_classes = (AllowAny,)

    def get(self, request):
        url = '{}annotations'.format(settings.ANNOTATOR_STORE)
        ann_store = requests.get(url)
        return Response(ann_store.json())

    def post(self, request):
        """
        Create a new annotation.
        """

        url = '{}annotations'.format(settings.ANNOTATOR_STORE)
        headers = {'Content-type': 'application/json'}
        annotation = requests.post(url, data=json.dumps(request.DATA), headers=headers)

        return Response(annotation.json(), status=status.HTTP_201_CREATED)

class AnnotationDetailView(APIView):
    """
    Annotation detail view.
    """
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        """
        Get an existing annotation.
        """
        annotation_id = self.kwargs.get('annotation_id')

        # TODO: get annotation from elasticsearch
        url = '{}annotations/{}'.format(settings.ANNOTATOR_STORE, annotation_id)
        annotation = requests.get(url)

        return Response(annotation.json(), status=status.HTTP_404_NOT_FOUND)

    def put(self, request, *args, **kwargs):
        """
        Update an existing annotation.
        """
        annotation_id = self.kwargs.get('annotation_id')

        # TODO: update annotation from elasticsearch
        headers = {'Content-type': 'application/json'}
        url = '{}annotations/{}'.format(settings.ANNOTATOR_STORE, annotation_id)
        annotation = requests.put(url, data=json.dumps(request.DATA), headers=headers)

        return Response(annotation.json(), status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, *args, **kwargs):
        """
        Delete an annotation.
        """
        annotation_id = self.kwargs.get('annotation_id')

        # TODO: delete annotation from elasticsearch
        url = '{}annotations/{}'.format(settings.ANNOTATOR_STORE, annotation_id)
        annotation = requests.delete(url)

        return Response(annotation, status=status.HTTP_404_NOT_FOUND)


