from django.conf.urls import include, url

app_name = "notesapi.v1"

urlpatterns = [
    url(r'^v1/', include('notesapi.v1.urls', namespace='v1')),
]
