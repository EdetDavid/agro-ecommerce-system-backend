from rest_framework import serializers
from .models import Order, OrderItem
from products.models import Product  # Import Product
from logistics.models import Delivery  # Import Delivery
from payments.models import Payment  # Import Payment
# You might need serializers for these related models too
from products.serializers import ProductSerializer  # Assuming you have this
from logistics.serializers import DeliverySerializer  # Create this if needed
from payments.serializers import PaymentSerializer  # Create this if needed
from users.serializers import UserSerializer  # For buyer details


class OrderItemSerializer(serializers.ModelSerializer):
    # Make product field read-only when nested in Order retrieval
    # but allow writing the product ID during order creation
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    # Include product details for reading
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        # Include 'product' for reading, 'product_id' for writing
        fields = ['id', 'product', 'product_id', 'quantity', 'price']
        # Make price read_only if it's set based on the Product during creation
        # Price should be set based on Product at time of order creation
        read_only_fields = ['price']


class OrderSerializer(serializers.ModelSerializer):
    # Nested Serializer for reading items related to this order
    # source='orderitem_set' is the default related_name Django creates
    items = OrderItemSerializer(
        many=True, read_only=True, source='orderitem_set')

    # --- For Order Creation ---
    # Accept a list of item data when creating an order
    order_items = OrderItemSerializer(many=True, write_only=True)

    # --- For Reading Related Data ---
    # Assuming OneToOneFields named 'delivery' and 'payment' exist pointing TO Order
    # If they point FROM Order, the source might just be 'delivery'/'payment'
    # Check your Delivery/Payment models for related_name if needed
    delivery = DeliverySerializer(
        read_only=True, required=False)  # Make optional
    payment = PaymentSerializer(
        read_only=True, required=False)  # Make optional
    buyer_details = UserSerializer(
        source='buyer', read_only=True)  # Show buyer info

    # --- Field for accepting delivery address during creation ---
    # This assumes you want to create the Delivery object along with the Order
    delivery_address = serializers.CharField(write_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'buyer', 'buyer_details', 'total_price', 'status', 'created_at',
            'items',  # For reading order details
            'order_items',  # For writing/creating order
            'delivery',  # For reading related delivery
            'payment',  # For reading related payment
            'delivery_address'  # For writing delivery address during creation
        ]
        # Let backend calculate total, set buyer/status
        read_only_fields = ['buyer', 'status', 'total_price']

    def create(self, validated_data):
        # 1. Extract nested item data and delivery address
        order_items_data = validated_data.pop('order_items')
        delivery_address_data = validated_data.pop('delivery_address')
        # Get buyer from request context
        buyer = self.context['request'].user

        # 2. Calculate total_price based on items received
        calculated_total = 0
        for item_data in order_items_data:
            # Product instance from product_id field
            product = item_data['product']
            quantity = item_data['quantity']
            # Use the *current* product price for the order item
            # Or you could pass price from frontend if prices can change
            price = product.price
            calculated_total += (price * quantity)
            # Add the calculated price back to item_data for OrderItem creation
            item_data['price'] = price

            # Optional: Stock check
            if product.quantity < quantity:
                raise serializers.ValidationError(
                    f"Not enough stock for {product.name}. Available: {product.quantity}")

        # 3. Create the Order instance
        order = Order.objects.create(
            buyer=buyer,
            total_price=calculated_total,
            status='Pending',  # Default status
            **validated_data  # Other validated fields if any
        )

        # 4. Create OrderItem instances
        order_items_to_create = []
        for item_data in order_items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            price = item_data['price']  # Use price calculated above

            order_items_to_create.append(
                OrderItem(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=price
                )
            )
            # Optional: Decrease product stock
            product.quantity -= quantity
            product.save()

        OrderItem.objects.bulk_create(order_items_to_create)

        # 5. Create the related Delivery instance
        Delivery.objects.create(
            order=order,
            delivery_address=delivery_address_data,
            status='Pending'  # Default status
        )

        # 6. Optionally create a pending Payment instance (or handle payment separately)
        Payment.objects.create(
            order=order,
            amount=calculated_total,
            status='Pending'  # Default status
            # transaction_id might be added later after actual payment
        )

        return order

    def to_representation(self, instance):
        """ Ensure related objects are fetched efficiently and included """
        representation = super().to_representation(instance)
        # Ensure buyer details are included correctly if needed beyond just ID
        # representation['buyer_details'] = UserSerializer(instance.buyer).data
        # Ensure items are present
        representation['items'] = OrderItemSerializer(
            instance.orderitem_set.all(), many=True).data

        # Add related delivery and payment if they exist
        try:
            representation['delivery'] = DeliverySerializer(
                instance.delivery).data
        except Delivery.DoesNotExist:
            representation['delivery'] = None
        try:
            representation['payment'] = PaymentSerializer(
                instance.payment).data
        except Payment.DoesNotExist:
            representation['payment'] = None

        return representation
