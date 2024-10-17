from django.urls import path, re_path

from notesapi.v1.views import (AnnotationDetailView, AnnotationListView,
                               AnnotationRetireView, get_annotation_search_view_class)
app_name = "notesapi.v1"
urlpatterns = [
    path('annotations/', AnnotationListView.as_view(), name='annotations'),
    path('retire_annotations/', AnnotationRetireView.as_view(), name='annotations_retire'),
    re_path(
        r'^annotations/(?P<annotation_id>[a-zA-Z0-9_-]+)/?$',
        AnnotationDetailView.as_view(),
        name='annotations_detail'
    ),
    path(
        'search/',
        get_annotation_search_view_class().as_view(),
        name='annotations_search'
    ),
]
