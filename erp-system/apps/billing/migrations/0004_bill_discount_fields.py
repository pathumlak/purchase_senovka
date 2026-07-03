from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0003_payment_is_senovka_transfer'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='bill_discount_percent',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='bill',
            name='bill_discount_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
    ]
