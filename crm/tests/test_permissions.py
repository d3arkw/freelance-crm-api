import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone

from crm.models import Client, Order

User = get_user_model()


@pytest.mark.django_db
def test_user_cannot_see_other_users_orders():
    user_a = User.objects.create_user(username="user_a", password="test12345")
    user_b = User.objects.create_user(username="user_b", password="test12345")

    client_a = Client.objects.create(
        owner=user_a,
        name="Client A",
        email="a@example.com",
    )

    order_a = Order.objects.create(
        owner=user_a,
        client=client_a,
        title="Private order",
        budget=1000,
    )

    api_client = APIClient()
    api_client.force_authenticate(user=user_b)

    response = api_client.get("/api/orders/")

    assert response.status_code == 200
    assert response.data["results"] == []

@pytest.mark.django_db
def test_user_cannot_create_order_for_other_client():
    user_a = User.objects.create_user(username="owner_a", password="test12345")
    user_b = User.objects.create_user(username="owner_b", password="test12345")

    client_a = Client.objects.create(owner=user_a, name="Client A", email="a@example.com")
    api_client = APIClient()
    api_client.force_authenticate(user=user_b)

    response = api_client.post("/api/orders/",
                               {
                                   "client": client_a.id,
                                   "title": "Unauthorized order",
                                   "status": "new",
                                   "budget": 1000.00,
                               })
    assert response.status_code == 400

@pytest.mark.django_db
def test_overdue_orders_use_single_query_for_clients(django_assert_num_queries):
    user = User.objects.create_user(
        username="manager",
        password="test12345",
    )

    client = Client.objects.create(
        owner=user,
        name="Client",
        email="client@example.com",
    )

    for i in range(3):
        Order.objects.create(
            owner=user,
            client=client,
            title=f"Order {i}",
            budget=1000,
            deadline=timezone.now() - timedelta(days=1),
        )

    api_client = APIClient()
    api_client.force_authenticate(user=user)

    with django_assert_num_queries(1):
        response = api_client.get("/api/analytics/overdue/")

    assert response.status_code == 200
    assert len(response.data) == 3