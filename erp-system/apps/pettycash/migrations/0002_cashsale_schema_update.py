from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pettycash', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='PettyCashTransfer',
            new_name='CashSale',
        ),
        migrations.RenameField(
            model_name='cashsale',
            old_name='transfer_type',
            new_name='sale_type',
        ),
        migrations.RemoveField(
            model_name='cashsale',
            name='from_account',
        ),
        migrations.RemoveField(
            model_name='cashsale',
            name='to_account',
        ),
        migrations.AddField(
            model_name='cashsale',
            name='bill_image',
            field=models.ImageField(blank=True, null=True, upload_to='cash_sales/bills/'),
        ),
        migrations.AlterField(
            model_name='cashsale',
            name='sale_type',
            field=models.CharField(choices=[('cash_in', 'Cash In'), ('cash_out', 'Cash Out')], max_length=10),
        ),
    ]
