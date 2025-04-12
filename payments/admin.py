from django.contrib import admin
from .models import Payment

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'transaction_id', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__id', 'transaction_id')

admin.site.register(Payment, PaymentAdmin)