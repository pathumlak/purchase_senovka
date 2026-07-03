from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0002_alter_payment_cheque_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='is_senovka_transfer',
            field=models.BooleanField(default=False),
        ),
    ]
