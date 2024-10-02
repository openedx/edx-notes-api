from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

import notesserver.views

urlpatterns = [
    path('heartbeat/', notesserver.views.heartbeat, name='heartbeat'),
    path('selftest/', notesserver.views.selftest, name='selftest'),
    re_path(r'^robots.txt$', notesserver.views.robots, name='robots'),
    path('', notesserver.views.root, name='root'),
    path('api/', include('notesapi.urls', namespace='api')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
