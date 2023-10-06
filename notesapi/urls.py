from django.urls import include, path

app_name = "notesapi.v1"

urlpatterns = [
    path('v1/', include('notesapi.v1.urls', namespace='v1')),
]
