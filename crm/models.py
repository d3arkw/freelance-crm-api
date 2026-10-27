from django.db import models
from django.conf import settings
from django.utils.timezone import now

STATUS_CHOICES = [("new","New"), ("in_progress","In Progress"), ("done","Done"), ("overdue","Overdue")]


class Client(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='clients')
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    company = models.CharField(blank=True, max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['owner', 'email'], name='unique_client')]

    def __str__(self):
        return f"{self.name} ({self.email})"


class Order(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='orders')
    title = models.CharField(max_length=256)
    status = models.CharField(choices=STATUS_CHOICES, db_index=True, default=STATUS_CHOICES[0][0], max_length=20)
    deadline = models.DateTimeField(null=True, db_index=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)


class Milestone(models.Model):
    order = models.ForeignKey(Order, related_name="milestones", on_delete=models.CASCADE)
    title = models.CharField(max_length=256)
    due_date = models.DateTimeField(null=True)
    is_done = models.BooleanField(default=False)


class Payment(models.Model):
    order = models.ForeignKey(Order, related_name="payments", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(default=now)

