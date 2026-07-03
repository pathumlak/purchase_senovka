from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0004_bill_discount_fields'),
        ('customers', '0006_customerledger_purchase_offset'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='bill',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='payments',
                to='billing.bill',
            ),
        ),
        migrations.AddField(
            model_name='payment',
            name='customer',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='direct_payments',
                to='customers.customer',
            ),
        ),
    ]
