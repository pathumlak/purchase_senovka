from decimal import Decimal
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='VehicleLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True, default=django.utils.timezone.localdate)),
                ('driver_name', models.CharField(max_length=100)),
                ('from_location', models.CharField(max_length=200)),
                ('to_location', models.CharField(max_length=200)),
                ('start_km', models.DecimalField(decimal_places=1, max_digits=10)),
                ('end_km', models.DecimalField(decimal_places=1, max_digits=10)),
                ('total_km', models.DecimalField(decimal_places=1, default=0, max_digits=10)),
                ('purpose', models.CharField(max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='vehicle_logs',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Vehicle Log',
                'verbose_name_plural': 'Vehicle Logs',
                'ordering': ['-date', '-id'],
            },
        ),
    ]
