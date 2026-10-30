from rest_framework.routers import DefaultRouter
from .views import ClientViewSet, OrderViewSet, AnalyticsViewSet

router = DefaultRouter()
router.register("clients", ClientViewSet, basename="client")
router.register("orders", OrderViewSet, basename="order")
router.register("analytics", AnalyticsViewSet, basename="analytics")
urlpatterns = router.urls