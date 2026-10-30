from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Q, F, Value, DecimalField
from django.db.models.functions import TruncMonth, Coalesce
from django.utils import timezone
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Client, Order, Payment, Milestone
from .serializers import ClientSerializer, OrderSerializer, PaymentSerializer, MilestoneSerializer
from rest_framework.decorators import action
from rest_framework.response import Response


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['company']
    search_fields = ['name', 'email']
    ordering_fields = ["created_at"]

    def get_queryset(self):
        return Client.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['client']
    search_fields = ['title']
    ordering_fields = ["created_at"]

    def get_queryset(self):
        return Order.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_queryset(self):
        return Payment.objects.filter(order__owner=self.request.user)


class MilestoneViewSet(viewsets.ModelViewSet):
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_queryset(self):
        return Milestone.objects.filter(order__owner=self.request.user)


class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="revenue-by-month")
    def revenue_by_month(self, request):
        revenue = (
            Payment.objects.filter(order__owner=request.user).annotate(month=TruncMonth("paid_at"))
            .values("month")
            .annotate(revenue=Sum("amount"))
            .order_by("month"))
        return Response(list(revenue))

    @action(detail=False, methods=["get"], url_path="overdue")
    def overdue(self, request):
        orders = Order.objects.filter(Q(deadline__lt=timezone.now()), ~Q(status="done"),
                                      owner=request.user).select_related("client")
        data = [
            {
                "id": order.id,
                "title": order.title,
                "client": order.client.name,
                "deadline": order.deadline,
            }
            for order in orders
        ]
        return Response(data)

    @action(detail=False, methods=["get"], url_path="payments")
    def debts(self, request):
        orders = (Order.objects.filter(owner=request.user).annotate(
            paid=Coalesce(
                Sum("payments__amount"),
                Value(0),
                output_field=DecimalField(max_digits=10, decimal_places=2))
        ).annotate(debt=F("budget") - F("paid")).values("id", "title", "budget", "paid", "debt").order_by("-debt"))
        return Response(list(orders))
