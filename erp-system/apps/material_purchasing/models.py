from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class MaterialPurchase(models.Model):
    KG = 'KG'
    G = 'G'
    UNIT_CHOICES = [(KG, 'KG'), (G, 'G')]

    supplier_name   = models.CharField(max_length=255)
    invoice_number  = models.CharField(max_length=100, unique=True)
    received_date   = models.DateField(default=timezone.localdate)
    material_name   = models.CharField(max_length=255)
    quantity        = models.DecimalField(max_digits=12, decimal_places=3)
    unit_type       = models.CharField(max_length=2, choices=UNIT_CHOICES, default=KG)
    unit_price      = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount    = models.DecimalField(max_digits=14, decimal_places=2, editable=False)

    # Scale verification
    scale_weight    = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    weight_verified = models.BooleanField(default=False)

    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-received_date', '-id']
        verbose_name = 'Material Purchase'
        verbose_name_plural = 'Material Purchases'

    def save(self, *args, **kwargs):
        self.total_amount = (self.quantity or Decimal('0')) * (self.unit_price or Decimal('0'))
        super().save(*args, **kwargs)

    def clean(self):
        errors = {}
        if self.quantity is not None and self.quantity <= 0:
            errors['quantity'] = 'Quantity must be greater than zero.'
        if self.unit_price is not None and self.unit_price < 0:
            errors['unit_price'] = 'Unit price cannot be negative.'
        if self.scale_weight is not None and self.scale_weight < 0:
            errors['scale_weight'] = 'Scale weight cannot be negative.'
        if errors:
            raise ValidationError(errors)

    @property
    def weight_discrepancy(self):
        if self.scale_weight is not None:
            return self.scale_weight - self.quantity
        return None

    @property
    def discrepancy_percent(self):
        if self.scale_weight is not None and self.quantity:
            return ((self.scale_weight - self.quantity) / self.quantity) * 100
        return None

    def __str__(self):
        return f"{self.invoice_number} — {self.supplier_name} ({self.received_date})"
