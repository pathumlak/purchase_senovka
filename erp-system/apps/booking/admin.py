from django.contrib import admin
from .models import BookingOrder, BookingItem


class BookingItemInline(admin.TabularInline):
    model = BookingItem
    extra = 0
    readonly_fields = ('discount_amount', 'line_total')


@admin.register(BookingOrder)
class BookingOrderAdmin(admin.ModelAdmin):
    list_display = ('booking_number', 'customer', 'booking_date', 'order_sending_date', 'status', 'total_amount')
    list_filter = ('status', 'booking_date')
    search_fields = ('booking_number', 'customer__name')
    readonly_fields = ('booking_number', 'created_at', 'updated_at', 'subtotal', 'discount_amount', 'total_amount')
    inlines = [BookingItemInline]
    date_hierarchy = 'booking_date'
