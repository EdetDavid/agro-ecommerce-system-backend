from django.db import models
from orders.models import Order

class Delivery(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    delivery_address = models.TextField()
    status = models.CharField(max_length=50, default='Pending')
    delivery_agent = models.CharField(max_length=100, blank=True, null=True)