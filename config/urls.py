"""Root URL configuration for the Klystr control plane."""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def healthz(_request):
    """Liveness probe for the API server itself."""
    return JsonResponse({'status': 'ok'})


api_v1 = [
    path('cluster/', include('apps.cluster.urls')),
    path('nodes/', include('apps.nodes.urls')),
    path('workloads/', include('apps.workloads.urls')),
    path('scheduler/', include('apps.scheduler.urls')),
    path('controllers/', include('apps.controllers.urls')),
    path('agents/', include('apps.agents.urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('healthz', healthz, name='healthz'),
    path('api/v1/', include((api_v1, 'v1'), namespace='v1')),
]
