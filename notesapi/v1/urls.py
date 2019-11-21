from django.conf.urls import url

from notesapi.v1.views import (AnnotationDetailView, AnnotationListView,
                               AnnotationRetireView, AnnotationSearchView)
app_name = "notesapi.v1"
urlpatterns = [
    url(r'^annotations/$', AnnotationListView.as_view(), name='annotations'),
    url(r'^retire_annotations/$', AnnotationRetireView.as_view(), name='annotations_retire'),
    url(
        r'^annotations/(?P<annotation_id>[a-zA-Z0-9_-]+)/?$',
        AnnotationDetailView.as_view(),
        name='annotations_detail'
    ),
    url(r'^search/$', AnnotationSearchView.as_view(), name='annotations_search'),
]
