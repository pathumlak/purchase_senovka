from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class CashSale(models.Model):
    CASH_IN = 'cash_in'
    CASH_OUT = 'cash_out'

    SALE_TYPE_CHOICES = [
        (CASH_IN, 'Cash In'),
        (CASH_OUT, 'Cash Out'),
    ]

    date = models.DateField(default=timezone.localdate)
    reference_number = models.CharField(max_length=80, blank=True)
    sale_type = models.CharField(max_length=10, choices=SALE_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    purpose = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    bill_image = models.ImageField(upload_to='cash_sales/bills/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']

    def clean(self):
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({'amount': 'Amount must be greater than zero.'})

    def __str__(self):
        return f"{self.get_sale_type_display()} - {self.amount} ({self.date})"