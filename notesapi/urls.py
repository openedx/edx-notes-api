from django.conf.urls import patterns, url, include

urlpatterns = patterns(
    '',
    url(r'^v1/', include('notesapi.v1.urls', namespace='v1')),
)
