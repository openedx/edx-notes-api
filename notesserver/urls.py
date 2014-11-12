from django.conf.urls import patterns, url, include
from notesserver.views import StatusView

urlpatterns = patterns(
    '',
    url(r'^status/$', StatusView.as_view(), name='status'),
    url(r'^$', 'notesserver.views.root', name='root'),
    url(r'^api/', include('notesapi.urls', namespace='api')),
)
