from decimal import Decimal
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from apps.customers.models import Customer
from apps.production.models import Product


def _next_bill_number():
    today = timezone.localdate()
    prefix = f"BLL-{today.strftime('%Y%m%d')}-"
    last = Bill.objects.filter(bill_number__startswith=prefix).order_by('-id').first()
    seq = 1
    if last:
        try:
            seq = int(last.bill_number.rsplit('-', 1)[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    return f"{prefix}{seq:04d}"


class Bill(models.Model):
    PENDING   = 'PENDING'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'
    STATUS_CHOICES = [
        (PENDING,   'Pending'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
    ]

    FULL_CASH     = 'FULL_CASH'
    FULL_CHEQUE   = 'FULL_CHEQUE'
    PAY_LATER     = 'PAY_LATER'
    PARTIAL_CASH  = 'PARTIAL_CASH'
    PARTIAL_CHEQUE= 'PARTIAL_CHEQUE'
    MIXED         = 'MIXED'
    METHOD_CHOICES = [
        (FULL_CASH,      'Full Cash'),
        (FULL_CHEQUE,    'Full Cheque'),
        (PAY_LATER,      'Pay Later'),
        (PARTIAL_CASH,   'Partial Cash'),
        (PARTIAL_CHEQUE, 'Partial Cheque'),
        (MIXED,          'Mixed (Cash + Cheque)'),
    ]

    bill_number    = models.CharField(max_length=30, unique=True, editable=False)
    customer       = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='bills')
    bill_date      = models.DateField(default=timezone.localdate)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING, db_index=True)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES, blank=True)

    subtotal              = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_amount       = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    bill_discount_percent = models.DecimalField(max_digits=5,  decimal_places=2, default=0)
    bill_discount_amount  = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount          = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    balance_used    = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_paid     = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_due      = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    notes      = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_bills')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-bill_date', '-id']
        verbose_name = 'Bill'
        verbose_name_plural = 'Bills'

    def save(self, *args, **kwargs):
        if not self.bill_number:
            self.bill_number = _next_bill_number()
        super().save(*args, **kwargs)

    @property
    def is_pending(self):
        return self.status == self.PENDING

    @property
    def is_completed(self):
        return self.status == self.COMPLETED

    def __str__(self):
        return f"{self.bill_number} – {self.customer.name}"


class BillItem(models.Model):
    bill            = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    product         = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='bill_items')
    quantity        = models.DecimalField(max_digits=12, decimal_places=3)
    unit_price      = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent= models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total      = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = 'Bill Item'

    def __str__(self):
        return f"{self.bill.bill_number} – {self.product.name} ×{self.quantity}"


class Payment(models.Model):
    CASH    = 'CASH'
    CHEQUE  = 'CHEQUE'
    BALANCE = 'BALANCE'
    METHOD_CHOICES = [
        (CASH,    'Cash'),
        (CHEQUE,  'Cheque'),
        (BALANCE, 'Credit Balance'),
    ]

    CHQ_PENDING = 'PENDING'
    CHQ_CLEARED = 'CLEARED'
    CHQ_BOUNCED = 'BOUNCED'
    CHQ_HOLD    = 'HOLD'
    CHQ_STATUS_CHOICES = [
        (CHQ_PENDING, 'Pending'),
        (CHQ_CLEARED, 'Cleared'),
        (CHQ_BOUNCED, 'Bounced'),
        (CHQ_HOLD,    'On Hold'),
    ]

    bill                 = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    customer             = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='direct_payments', null=True, blank=True)
    payment_date         = models.DateField(default=timezone.localdate)
    method               = models.CharField(max_length=20, choices=METHOD_CHOICES)
    amount               = models.DecimalField(max_digits=14, decimal_places=2)
    is_senovka_transfer  = models.BooleanField(default=False)
    notes                = models.TextField(blank=True)

    # Cheque fields (blank for cash/balance payments)
    customer_name  = models.CharField(max_length=255, blank=True)
    cheque_number  = models.CharField(max_length=100, blank=True)
    bank_name      = models.CharField(max_length=255, blank=True)
    branch_name    = models.CharField(max_length=255, blank=True)
    account_number = models.CharField(max_length=100, blank=True)
    received_date  = models.DateField(null=True, blank=True)
    maturity_date  = models.DateField(null=True, blank=True)
    cheque_status  = models.CharField(max_length=20, choices=CHQ_STATUS_CHOICES, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'

    def __str__(self):
        return f"{self.bill.bill_number} – {self.method} Rs.{self.amount}"


class HeldBill(models.Model):
    """A parked/in-progress bill — items chosen but not yet paid for.
    Recalling loads it back into the bill-create form; the row is then deleted."""
    customer               = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='held_bills')
    customer_name          = models.CharField(max_length=255, blank=True)
    bill_date              = models.DateField(default=timezone.localdate)
    notes                  = models.TextField(blank=True)
    bill_discount_percent  = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    items_json             = models.TextField()
    item_count             = models.PositiveIntegerField(default=0)
    total_amount           = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    held_by                = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='held_bills')
    created_at              = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Held Bill'
        verbose_name_plural = 'Held Bills'

    def __str__(self):
        return f"Hold #{self.pk} – {self.customer_name or 'Walk-in'}"
