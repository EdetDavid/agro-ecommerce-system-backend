from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('buyer__username', 'id')
    inlines = [OrderItemInline]

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    search_fields = ('order__id', 'product__name')

admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)