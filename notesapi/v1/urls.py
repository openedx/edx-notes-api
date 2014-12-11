from django.conf.urls import patterns, url
from django.views.generic import RedirectView
from django.core.urlresolvers import reverse_lazy
from notesapi.v1.views import AnnotationListView, AnnotationDetailView, AnnotationSearchView

urlpatterns = patterns(
    '',
    url(r'^annotations/$', AnnotationListView.as_view(), name='annotations'),
    url(r'^annotations/(?P<annotation_id>[a-zA-Z0-9_-]+)/?$', AnnotationDetailView.as_view(), name='annotations_detail'),
    url(r'^search/$', AnnotationSearchView.as_view(), name='annotations_search'),
)
