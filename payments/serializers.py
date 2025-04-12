from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'transaction_id', 'amount', 'status',
            'created_at', 'payment_method',
            'paypal_order_id', 'paypal_payment_id' # Include new fields
        ]
        read_only_fields = [
            'paypal_order_id', 'paypal_payment_id', # Usually set by specific PayPal views
            'transaction_id', # Often set after capture
            'status', # Usually managed internally
            'created_at'
        ]