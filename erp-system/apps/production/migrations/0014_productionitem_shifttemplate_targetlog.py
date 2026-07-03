from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0013_employee_shiftproductionlog'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductionItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('hourly_qty', models.DecimalField(decimal_places=2, help_text='Target quantity per 1 hour', max_digits=8)),
                ('description', models.TextField(blank=True, default='')),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Production Item',
                'verbose_name_plural': 'Production Items',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ShiftTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('crosses_midnight', models.BooleanField(default=False, help_text='End time is on the next day')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Shift Template',
                'verbose_name_plural': 'Shift Templates',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='TargetLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True)),
                ('machine_name', models.CharField(max_length=255)),
                ('cavity', models.PositiveIntegerField(default=1)),
                ('cycle_time_seconds', models.PositiveIntegerField(blank=True, null=True)),
                ('target_qty', models.IntegerField()),
                ('actual_qty', models.IntegerField()),
                ('downtime_minutes', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('downtime_reason', models.TextField(blank=True, default='')),
                ('point', models.IntegerField(choices=[(0, '0 – Not Achieved'), (1, '1 – Achieved')], default=1)),
                ('remarks', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('employee', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='target_logs',
                    to='production.employee',
                )),
                ('item', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='target_logs',
                    to='production.productionitem',
                )),
                ('shift_template', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='target_logs',
                    to='production.shifttemplate',
                )),
            ],
            options={
                'verbose_name': 'Target Log',
                'verbose_name_plural': 'Target Logs',
                'ordering': ['-date', '-created_at'],
            },
        ),
    ]
