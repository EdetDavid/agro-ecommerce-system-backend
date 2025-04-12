from rest_framework import serializers
from .models import Product, Category
from users.serializers import UserSerializer

class ProductSerializer(serializers.ModelSerializer):
    farmer_details = UserSerializer(source='farmer', read_only=True)
    image_path = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'quantity', 'farmer', 
                 'category', 'image', 'image_url', 'image_path', 'farmer_details']
        read_only_fields = ['farmer']
        
    def get_image_path(self, obj):
        """Return the complete URL for the image"""
        if obj.image and hasattr(obj.image, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return obj.image_url or None
        
    def to_representation(self, instance):
        """Add farmer details to the response"""
        representation = super().to_representation(instance)
        return representation

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
    
    def validate_name(self, value):
        """
        Check that the category name is unique.
        """
        if Category.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return value