from django.db import models
from orders.models import Order

class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    # transaction_id will store the *final* captured PayPal payment ID
    transaction_id = models.CharField(max_length=100, blank=True, null=True) # Make blank/null initially
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=50,
        default='Pending',
        choices=[ # Add more specific statuses
            ('Pending', 'Pending'), # Initial state
            ('Pending PayPal', 'Pending PayPal Confirmation'), # Waiting for PayPal interaction
            ('Completed', 'Completed'),
            ('Failed', 'Failed'),
            ('Refunded', 'Refunded'),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, default='N/A') # Track method used

    # PayPal Specific Fields
    paypal_order_id = models.CharField(max_length=100, blank=True, null=True) # ID from PayPal create order call
    paypal_payment_id = models.CharField(max_length=100, blank=True, null=True) # ID from PayPal capture call (can be same as transaction_id)

    def __str__(self):
        return f"Payment for Order {self.order.id} - {self.status}"

