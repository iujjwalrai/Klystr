from rest_framework.routers import SimpleRouter

from .views import NodeViewSet

app_name = 'nodes'

router = SimpleRouter()
router.register('', NodeViewSet, basename='node')

urlpatterns = router.urls
