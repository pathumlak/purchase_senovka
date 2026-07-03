from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='PettyCashTransfer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.localdate)),
                ('reference_number', models.CharField(blank=True, max_length=80)),
                ('transfer_type', models.CharField(choices=[('cash_in', 'Cash In'), ('cash_out', 'Cash Out'), ('transfer', 'Transfer')], max_length=12)),
                ('from_account', models.CharField(blank=True, max_length=120)),
                ('to_account', models.CharField(blank=True, max_length=120)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=14)),
                ('purpose', models.CharField(max_length=255)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-date', '-id'],
            },
        ),
    ]
