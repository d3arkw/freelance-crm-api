from django.utils.timezone import now
from rest_framework import serializers
from .models import Client, Order


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
            raise serializers.ValidationError('budget cannot be zero')
        return budget

    def validate(self, data):
        deadline = data.get("deadline")
        if deadline and deadline < now():
            raise serializers.ValidationError('deadline cannot be less than today')
        return data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")

        if request and request.user.is_authenticated:
            self.fields['client'].queryset = Client.objects.filter(owner=request.user)
