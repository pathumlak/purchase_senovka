from django.db import models
from decimal import Decimal


class Supplier(models.Model):
    name = models.CharField(max_length=255, unique=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    customer = models.OneToOneField(
        'customers.Customer',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='as_supplier',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def total_supplied_value(self):
        from django.db.models import Sum
        return self.receipts.aggregate(s=Sum('total_cost'))['s'] or Decimal('0')


class SupplyReceipt(models.Model):
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name='receipts'
    )
    date = models.DateField()
    notes = models.TextField(blank=True)
    total_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit_applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"Supply #{self.pk} — {self.supplier.name} on {self.date}"


class SupplyReceiptItem(models.Model):
    receipt = models.ForeignKey(
        SupplyReceipt, on_delete=models.CASCADE, related_name='items'
    )
    product = models.ForeignKey(
        'production.Product', on_delete=models.PROTECT, related_name='supply_items'
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.cost_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} × {self.quantity}"


class PurchaseOrder(models.Model):
    PENDING = 'pending'
    RECEIVED = 'received'
    CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (RECEIVED, 'Received'),
        (CANCELLED, 'Cancelled'),
    ]

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    order_date = models.DateField()
    expected_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=PENDING)
    notes = models.TextField(blank=True)
    total_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    received_date = models.DateField(null=True, blank=True)
    balance_deducted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-order_date', '-id']
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'

    def save(self, *args, **kwargs):
        if not self.order_number:
            from django.utils import timezone
            year = timezone.localdate().year
            count = PurchaseOrder.objects.filter(order_date__year=year).count() + 1
            self.order_number = f"PO-{year}-{count:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} — {self.supplier.name}"


class PurchaseOrderItem(models.Model):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        'production.Product', on_delete=models.PROTECT, related_name='purchase_order_items'
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order.order_number} — {self.product.name} × {self.quantity}"
