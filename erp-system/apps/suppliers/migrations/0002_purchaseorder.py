from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('suppliers', '0001_initial'),
        ('production', '0016_dailyworkassignment'),
    ]

    operations = [
        migrations.CreateModel(
            name='PurchaseOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_number', models.CharField(editable=False, max_length=20, unique=True)),
                ('order_date', models.DateField()),
                ('expected_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('received', 'Received'), ('cancelled', 'Cancelled')],
                    default='pending', max_length=15,
                )),
                ('notes', models.TextField(blank=True)),
                ('total_cost', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('received_date', models.DateField(blank=True, null=True)),
                ('balance_deducted', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('supplier', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='purchase_orders',
                    to='suppliers.supplier',
                )),
            ],
            options={
                'verbose_name': 'Purchase Order',
                'verbose_name_plural': 'Purchase Orders',
                'ordering': ['-order_date', '-id'],
            },
        ),
        migrations.CreateModel(
            name='PurchaseOrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=12)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('line_total', models.DecimalField(decimal_places=2, max_digits=14)),
                ('order', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='items',
                    to='suppliers.purchaseorder',
                )),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='purchase_order_items',
                    to='production.product',
                )),
            ],
        ),
    ]
