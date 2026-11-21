from django.contrib import admin
from .models import RequisitionRequest, RequisitionItem


class RequisitionItemInline(admin.TabularInline):
    model = RequisitionItem
    extra = 0
    readonly_fields = ['qty_approved']


@admin.register(RequisitionRequest)
class RequisitionRequestAdmin(admin.ModelAdmin):
    list_display = ['code', 'branch', 'requested_by', 'status', 'created_at']
    list_filter = ['status', 'branch']
    inlines = [RequisitionItemInline]
    readonly_fields = ['code', 'created_at']
