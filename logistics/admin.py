from django.contrib import admin
from .models import Delivery

class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('order', 'delivery_address', 'status', 'delivery_agent')
    list_filter = ('status',)
    search_fields = ('order__id', 'delivery_agent')

admin.site.register(Delivery, DeliveryAdmin)