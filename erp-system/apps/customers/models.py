from decimal import Decimal

from django.db import models

from apps.production.models import Product


class Customer(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.TextField(blank=True, null=True)
    # Positive = customer has credit (we owe them); Negative = customer owes us
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # SuperAdmin-only: block PAY_LATER bills if outstanding would exceed this
    max_outstanding_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class CustomerProductPrice(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='product_prices'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='customer_prices'
    )
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('customer', 'product')
        verbose_name = "Customer Product Price"
        verbose_name_plural = "Customer Product Prices"

    def __str__(self):
        return f"{self.customer.name} - {self.product.name}: {self.unit_price}"

    @staticmethod
    def get_price_for_customer(customer, product):
        """Return customer-specific price if exists, otherwise None."""
        try:
            cpp = CustomerProductPrice.objects.get(customer=customer, product=product)
            return cpp.unit_price
        except CustomerProductPrice.DoesNotExist:
            return None


class CustomerLedger(models.Model):
    SALE = 'SALE'
    SALE_CASH = 'SALE_CASH'
    SALE_PARTIAL = 'SALE_PARTIAL'
    PAYMENT_CASH = 'PAYMENT_CASH'
    PAYMENT_CHEQUE = 'PAYMENT_CHEQUE'
    BALANCE_USED = 'BALANCE_USED'
    OVERPAYMENT = 'OVERPAYMENT'
    BILL_CANCELLED = 'BILL_CANCELLED'
    CHEQUE_BOUNCED = 'CHEQUE_BOUNCED'
    CHEQUE_CLEARED = 'CHEQUE_CLEARED'
    MANUAL_ADJUSTMENT = 'MANUAL_ADJUSTMENT'
    PURCHASE_OFFSET = 'PURCHASE_OFFSET'
    SUPPLY_CREDIT = 'SUPPLY_CREDIT'
    SUPPLY_CREDIT_REVERSAL = 'SUPPLY_CREDIT_REVERSAL'

    TRANSACTION_TYPES = [
        (SALE, 'Sale (Credit)'),
        (SALE_CASH, 'Sale (Cash/Cheque)'),
        (SALE_PARTIAL, 'Sale (Partial Payment)'),
        (PAYMENT_CASH, 'Cash Payment'),
        (PAYMENT_CHEQUE, 'Cheque Payment'),
        (BALANCE_USED, 'Credit Balance Used'),
        (OVERPAYMENT, 'Overpayment Credited'),
        (BILL_CANCELLED, 'Bill Cancelled'),
        (CHEQUE_BOUNCED, 'Cheque Bounced'),
        (CHEQUE_CLEARED, 'Cheque Cleared'),
        (MANUAL_ADJUSTMENT, 'Manual Adjustment'),
        (PURCHASE_OFFSET, 'Purchase Offset'),
        (SUPPLY_CREDIT, 'Supply Received (Credit)'),
        (SUPPLY_CREDIT_REVERSAL, 'Supply Reversed'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='ledger_entries')
    date = models.DateField()
    bill_number = models.CharField(max_length=50, blank=True, default='')
    description = models.CharField(max_length=255)
    transaction_type = models.CharField(max_length=25, choices=TRANSACTION_TYPES)
    # debit = amount that decreased customer.balance (they owe us more / their credit shrank)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # credit = amount that increased customer.balance (they owe us less / their credit grew)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # actual customer.balance after this entry (authoritative — do not compute from debit/credit)
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    bill = models.ForeignKey(
        'billing.Bill', on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'created_at']
        verbose_name = 'Customer Ledger Entry'
        verbose_name_plural = 'Customer Ledger Entries'

    def __str__(self):
        return f"{self.customer.name} | {self.date} | {self.description}"


def add_ledger_entry(customer, *, date, description, transaction_type,
                     debit=0, credit=0, balance=None, bill=None):
    """Create a CustomerLedger row. Call AFTER customer.balance has been saved."""
    CustomerLedger.objects.create(
        customer=customer,
        date=date,
        bill_number=bill.bill_number if bill else '',
        description=description,
        transaction_type=transaction_type,
        debit=Decimal(str(debit)),
        credit=Decimal(str(credit)),
        balance=customer.balance if balance is None else balance,
        bill=bill,
    )
