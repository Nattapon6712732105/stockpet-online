from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Branch


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active']
    list_editable = ['is_active']
    search_fields = ['name', 'code']


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'get_full_name', 'role', 'branch', 'is_active']
    list_filter = ['role', 'branch', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('ข้อมูลระบบ', {'fields': ('role', 'branch')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('ข้อมูลระบบ', {'fields': ('role', 'branch')}),
    )
