from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0005_customerledger'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customerledger',
            name='transaction_type',
            field=models.CharField(
                choices=[
                    ('SALE', 'Sale (Credit)'),
                    ('SALE_CASH', 'Sale (Cash/Cheque)'),
                    ('SALE_PARTIAL', 'Sale (Partial Payment)'),
                    ('PAYMENT_CASH', 'Cash Payment'),
                    ('PAYMENT_CHEQUE', 'Cheque Payment'),
                    ('BALANCE_USED', 'Credit Balance Used'),
                    ('OVERPAYMENT', 'Overpayment Credited'),
                    ('BILL_CANCELLED', 'Bill Cancelled'),
                    ('CHEQUE_BOUNCED', 'Cheque Bounced'),
                    ('CHEQUE_CLEARED', 'Cheque Cleared'),
                    ('MANUAL_ADJUSTMENT', 'Manual Adjustment'),
                    ('PURCHASE_OFFSET', 'Purchase Offset'),
                ],
                max_length=25,
            ),
        ),
    ]
