from django.contrib import admin
from .models import Product, Category

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'quantity', 'farmer', 'category')
    list_filter = ('category', 'farmer')
    search_fields = ('name', 'description')

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)