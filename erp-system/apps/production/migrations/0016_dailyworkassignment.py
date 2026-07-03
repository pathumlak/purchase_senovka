from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0015_shiftlog_add_point_field'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyWorkAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('production_date', models.DateField(db_index=True, unique=True)),
                ('crusher_operator', models.CharField(blank=True, max_length=255)),
                ('material_mixer', models.CharField(blank=True, max_length=255)),
                ('extra_work_employee', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Daily Work Assignment',
                'verbose_name_plural': 'Daily Work Assignments',
                'ordering': ['-production_date'],
            },
        ),
    ]
