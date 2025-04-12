from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_farmer', 'is_buyer', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('email', 'first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_farmer', 'is_buyer', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_farmer', 'is_buyer'),
        }),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile)