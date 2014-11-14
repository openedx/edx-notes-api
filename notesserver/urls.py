from django.conf.urls import patterns, url
from notesserver.views import StatusView, AnnotationListView, AnnotationDetailView

urlpatterns = patterns('',  # nopep8
    url(r'^status/$', StatusView.as_view(), name='status'),
    url(r'^$', 'notesserver.views.root', name='root'),
    url(r'^annotations/$', AnnotationListView.as_view(), name='annotations'),
    url(r'^annotations/(?P<annotation_id>[a-zA-Z0-9_-]+)$', AnnotationDetailView.as_view(), name='annotations_detail')
)

