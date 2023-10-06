from django.urls import include, path, re_path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

import notesserver.views

schema_view = get_schema_view(
   openapi.Info(
      title="Edx Notes API",
      default_version='v1',
      description="Edx Notes API docs",
   ),
   public=False,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('heartbeat/', notesserver.views.heartbeat, name='heartbeat'),
    path('selftest/', notesserver.views.selftest, name='selftest'),
    re_path(r'^robots.txt$', notesserver.views.robots, name='robots'),
    path('', notesserver.views.root, name='root'),
    path('api/', include('notesapi.urls', namespace='api')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]
