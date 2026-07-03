from decimal import Decimal
from django.db import migrations, models


def merge_balances(apps, schema_editor):
    Customer = apps.get_model('customers', 'Customer')
    for c in Customer.objects.all():
        # net position: credit minus what they owe from pending bills
        c.balance = c.balance - c.outstanding_balance
        c.save(update_fields=['balance'])


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0003_customer_outstanding_balance'),
    ]

    operations = [
        migrations.RunPython(merge_balances, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='customer',
            name='outstanding_balance',
        ),
        migrations.AddField(
            model_name='customer',
            name='max_outstanding_limit',
            field=models.DecimalField(decimal_places=2, max_digits=12, null=True, blank=True),
        ),
    ]
