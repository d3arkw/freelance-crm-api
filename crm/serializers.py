from rest_framework import serializers
from .models import Client, Order, Payment, Milestone
from django.utils import timezone


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['owner', 'name', 'email', 'company', 'created_at']
        read_only_fields = ('owner',)


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['owner', 'client', 'title', 'status', 'deadline', 'budget', 'created_at']
        read_only_fields = ('owner',)

    def validate_budget(self, budget):
        if budget <= 0:
            raise serializers.ValidationError('budget must be greater than zero')
        return budget

    def validate(self, data):
        deadline = data.get("deadline")
        if deadline and deadline < timezone.now():
            raise serializers.ValidationError('deadline cannot be less than today')
        return data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")

        if request and request.user.is_authenticated:
            self.fields['client'].queryset = Client.objects.filter(owner=request.user)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'order', 'amount', 'paid_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")

        if request and request.user.is_authenticated:
            self.fields['order'].queryset = Order.objects.filter(owner=request.user)

class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = ['id', 'order', 'title', 'due_date', 'is_done']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")

        if request and request.user.is_authenticated:
            self.fields['order'].queryset = Order.objects.filter(owner=request.user)

