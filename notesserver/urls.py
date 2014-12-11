from django.conf.urls import patterns, url, include

urlpatterns = patterns(
    '',
    url(r'^heartbeat/$', 'notesserver.views.heartbeat', name='heartbeat'),
    url(r'^selftest/$', 'notesserver.views.selftest', name='selftest'),
    url(r'^$', 'notesserver.views.root', name='root'),
    url(r'^api/', include('notesapi.urls', namespace='api')),
)
