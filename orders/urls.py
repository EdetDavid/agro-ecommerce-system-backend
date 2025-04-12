from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Make sure the views are imported correctly
from .views import OrderViewSet, OrderItemViewSet

router = DefaultRouter()

# Provide the basename explicitly
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet, basename='orderitem') # Use 'orderitem' (singular)

urlpatterns = [
    path('', include(router.urls)),
]