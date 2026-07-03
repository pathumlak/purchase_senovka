from django.contrib import admin
from .models import Supplier, SupplyReceipt, SupplyReceiptItem


class SupplyReceiptItemInline(admin.TabularInline):
    model = SupplyReceiptItem
    extra = 0
    readonly_fields = ('line_total',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'customer', 'created_at')
    search_fields = ('name', 'phone', 'email')
    list_filter = ('created_at',)


@admin.register(SupplyReceipt)
class SupplyReceiptAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'date', 'total_cost', 'credit_applied')
    list_filter = ('credit_applied', 'date')
    inlines = [SupplyReceiptItemInline]
