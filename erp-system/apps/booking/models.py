from decimal import Decimal
from django.db import models
from django.utils import timezone
from apps.customers.models import Customer
from apps.production.models import Product
from django.contrib.auth.models import User


def _next_booking_number():
    today = timezone.localdate()
    prefix = f"BOK-{today.strftime('%Y%m%d')}-"
    last = BookingOrder.objects.filter(booking_number__startswith=prefix).order_by('-id').first()
    seq = int(last.booking_number.rsplit('-', 1)[-1]) + 1 if last else 1
    return f"{prefix}{seq:04d}"


class BookingOrder(models.Model):
    PENDING   = 'PENDING'
    CONFIRMED = 'CONFIRMED'
    CANCELLED = 'CANCELLED'
    STATUS_CHOICES = [
        (PENDING,   'Pending'),
        (CONFIRMED, 'Confirmed'),
        (CANCELLED, 'Cancelled'),
    ]

    booking_number     = models.CharField(max_length=30, unique=True, editable=False)
    customer           = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='bookings')
    booking_date       = models.DateField(default=timezone.localdate)
    order_sending_date = models.DateField(null=True, blank=True)
    status             = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING, db_index=True)
    subtotal           = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_amount    = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount       = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes              = models.TextField(blank=True)
    bill               = models.OneToOneField(
        'billing.Bill',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='booking',
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-booking_date', '-id']
        verbose_name = 'Booking Order'
        verbose_name_plural = 'Booking Orders'

    def save(self, *args, **kwargs):
        if not self.booking_number:
            self.booking_number = _next_booking_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.booking_number


class BookingItem(models.Model):
    booking          = models.ForeignKey(BookingOrder, on_delete=models.CASCADE, related_name='items')
    product          = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity         = models.DecimalField(max_digits=12, decimal_places=3)
    unit_price       = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total       = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = 'Booking Item'

    def __str__(self):
        return f"{self.booking.booking_number} – {self.product.name} ×{self.quantity}"
