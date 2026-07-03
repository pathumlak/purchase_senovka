from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0012_fix_productionentry_schema'),
    ]

    operations = [
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Employees',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ShiftProductionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shift_start', models.DateTimeField(db_index=True)),
                ('shift_end', models.DateTimeField()),
                ('machine_no', models.CharField(max_length=255)),
                ('item_name', models.CharField(max_length=255)),
                ('cavity', models.PositiveIntegerField()),
                ('cycle_time_seconds', models.PositiveIntegerField()),
                ('target_qty', models.IntegerField()),
                ('actual_qty', models.IntegerField()),
                ('downtime_minutes', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('downtime_reason', models.TextField(blank=True, default='')),
                ('remarks', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('employee', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='shift_logs',
                    to='production.employee',
                )),
            ],
            options={
                'verbose_name': 'Shift Production Log',
                'verbose_name_plural': 'Shift Production Logs',
                'ordering': ['-shift_start', '-id'],
            },
        ),
    ]
