from django.contrib import admin
from .models import MaterialPurchase

@admin.register(MaterialPurchase)
class MaterialPurchaseAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'supplier_name', 'material_name', 'received_date', 'quantity', 'unit_type', 'unit_price', 'total_amount', 'weight_verified')
    list_filter = ('unit_type', 'weight_verified', 'received_date')
    search_fields = ('invoice_number', 'supplier_name', 'material_name')
    readonly_fields = ('total_amount', 'created_at', 'updated_at')
    date_hierarchy = 'received_date'
