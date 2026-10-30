from rest_framework.routers import DefaultRouter
from .views import ClientViewSet, OrderViewSet, AnalyticsViewSet, PaymentViewSet, MilestoneViewSet

router = DefaultRouter()
router.register("clients", ClientViewSet, basename="client")
router.register("orders", OrderViewSet, basename="order")
router.register("analytics", AnalyticsViewSet, basename="analytics")
router.register("payments", PaymentViewSet, basename="payment")
router.register("milestones", MilestoneViewSet, basename="milestone")
urlpatterns = router.urls