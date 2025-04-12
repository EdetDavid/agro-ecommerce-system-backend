from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, CreatePayPalOrderView, CapturePayPalOrderView # Import new views

router = DefaultRouter()
# Only include router if you need general CRUD for admins, otherwise remove
router.register(r'payments', PaymentViewSet, basename='payment') # Explicit basename

urlpatterns = [
    path('', include(router.urls)), # Include router URLs if needed
    # Add PayPal specific endpoints
    path('paypal/create-order/', CreatePayPalOrderView.as_view(), name='paypal-create-order'),
    path('paypal/capture-order/', CapturePayPalOrderView.as_view(), name='paypal-capture-order'),
]
