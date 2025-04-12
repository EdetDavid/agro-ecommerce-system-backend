from django.db import models
from users.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    farmer = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    # Add image field
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    # Add a field for image URL as an alternative to uploaded images
    image_url = models.URLField(max_length=1000, blank=True, null=True)
    
    def __str__(self):
        return self.name