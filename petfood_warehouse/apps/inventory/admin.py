from django.contrib import admin
from .models import Category, Product, CentralStock, BranchStock, StockMovement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'category', 'unit', 'min_stock', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['sku', 'name']


@admin.register(CentralStock)
class CentralStockAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'get_status']
    search_fields = ['product__name', 'product__sku']

    def get_status(self, obj):
        return obj.status_display
    get_status.short_description = 'สถานะ'


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'qty_change', 'balance_after', 'by_user', 'created_at']
    list_filter = ['movement_type']
    readonly_fields = ['created_at']
