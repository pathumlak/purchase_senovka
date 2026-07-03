from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('customers', '0003_customer_outstanding_balance'),
        ('production', '0008_machine'),
    ]

    operations = [
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('phone', models.CharField(blank=True, max_length=50)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('address', models.TextField(blank=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.OneToOneField(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='as_supplier',
                    to='customers.customer',
                )),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='SupplyReceipt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('notes', models.TextField(blank=True)),
                ('total_cost', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('credit_applied', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('supplier', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='receipts',
                    to='suppliers.supplier',
                )),
            ],
            options={'ordering': ['-date', '-created_at']},
        ),
        migrations.CreateModel(
            name='SupplyReceiptItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=12)),
                ('cost_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('line_total', models.DecimalField(decimal_places=2, max_digits=14)),
                ('receipt', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='items',
                    to='suppliers.supplyreceipt',
                )),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='supply_items',
                    to='production.product',
                )),
            ],
        ),
    ]
