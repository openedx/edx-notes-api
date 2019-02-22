from django.conf.urls import url
from notesapi.v1.views import AnnotationListView, AnnotationDetailView, AnnotationSearchView, UsernameReplacementView

urlpatterns = [
    url(r'^annotations/$', AnnotationListView.as_view(), name='annotations'),
    url(
        r'^annotations/(?P<annotation_id>[a-zA-Z0-9_-]+)/?$',
        AnnotationDetailView.as_view(),
        name='annotations_detail'
    ),
    url(r'^search/$', AnnotationSearchView.as_view(), name='annotations_search'),
    url(r'replace_usernames/$', UsernameReplacementView.as_view(), name="replace_usernames")
]
