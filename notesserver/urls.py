from django.conf.urls import include, url

import notesserver.views

urlpatterns = [
    url(r'^heartbeat/$', notesserver.views.heartbeat, name='heartbeat'),
    url(r'^selftest/$', notesserver.views.selftest, name='selftest'),
    url(r'^$', notesserver.views.root, name='root'),
    url(r'^api/', include('notesapi.urls', namespace='api')),
]
