from django.contrib import admin
from .models import Bill, BillItem, Payment


class BillItemInline(admin.TabularInline):
    model = BillItem
    extra = 0
    readonly_fields = ('line_total',)


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display  = ('bill_number', 'customer', 'bill_date', 'status', 'payment_method', 'total_amount', 'amount_due')
    list_filter   = ('status', 'payment_method', 'bill_date')
    search_fields = ('bill_number', 'customer__name')
    readonly_fields = ('bill_number', 'created_at', 'updated_at')
    inlines = [BillItemInline, PaymentInline]
    date_hierarchy = 'bill_date'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ('bill', 'method', 'amount', 'payment_date', 'cheque_status')
    list_filter   = ('method', 'cheque_status')
    search_fields = ('bill__bill_number', 'cheque_number', 'bank_name')
