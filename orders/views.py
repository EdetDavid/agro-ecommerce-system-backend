from rest_framework import viewsets, permissions # Add permissions
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction # Import transaction
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated] # Require login

    def get_queryset(self):
        """ Filter orders to only show the logged-in user's orders """
        # Allow staff/admin to see all (optional)
        if self.request.user.is_staff:
            return Order.objects.all().select_related('buyer', 'delivery', 'payment').prefetch_related('orderitem_set__product')
        return Order.objects.filter(buyer=self.request.user).select_related('buyer', 'delivery', 'payment').prefetch_related('orderitem_set__product') # Efficiently fetch related data

    def get_serializer_context(self):
        """ Add request to the serializer context """
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    # The default create/perform_create is now handled by the serializer's create method
    # But you could wrap it in a transaction here if preferred
    @transaction.atomic # Ensure all creations succeed or fail together
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer) # Calls serializer.save() which calls serializer.create()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    # perform_create now just calls save, which triggers the serializer's create
    def perform_create(self, serializer):
        # Buyer is set in the serializer's create method using context
        serializer.save() # No need to pass buyer here anymore


class OrderItemViewSet(viewsets.ModelViewSet):
    # This endpoint is less critical if items are handled via nested OrderSerializer
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated] # Adjust permissions as needed

    def get_queryset(self):
        """ Optionally filter items based on user's orders """
        user = self.request.user
        if user.is_staff:
            return OrderItem.objects.all().select_related('order', 'product')
        # Filter items belonging to orders owned by the current user
        return OrderItem.objects.filter(order__buyer=user).select_related('order', 'product')