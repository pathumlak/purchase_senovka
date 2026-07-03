from django.contrib import admin

from .models import CashSale


@admin.register(CashSale)
class CashSaleAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'sale_type',
        'amount',
        'purpose',
        'reference_number',
    )
    list_filter = ('sale_type', 'date')
    search_fields = ('reference_number', 'purpose', 'notes')
