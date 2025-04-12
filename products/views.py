from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


class IsFarmer(permissions.BasePermission):
    """
    Custom permission to only allow farmers to create/update products.
    """

    def has_permission(self, request, view):
        # Allow GET requests for anyone
        if request.method in permissions.SAFE_METHODS:
            return True
        # Check if user is authenticated and is a farmer
        return request.user.is_authenticated and request.user.is_farmer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsFarmer]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        """
        This view should return a list of all products,
        but for non-GET methods, it filters by the farmer.
        """
        queryset = Product.objects.all()

        # For unsafe methods other than POST, only return user's products
        if self.request.method not in permissions.SAFE_METHODS and self.request.method != 'POST':
            queryset = queryset.filter(farmer=self.request.user)

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def perform_create(self, serializer):
        """
        Set the farmer to the current user when creating a product
        """
        serializer.save(farmer=self.request.user)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # Only farmers can create/edit categories
    permission_classes = [IsFarmer]
