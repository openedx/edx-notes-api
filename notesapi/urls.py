from django.conf.urls import include, url

urlpatterns = [
    url(r'^v1/', include('notesapi.v1.urls', namespace='v1')),
]
