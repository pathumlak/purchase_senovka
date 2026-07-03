from django.db import migrations


def fix_schema_if_needed(apps, schema_editor):
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("PRAGMA table_info(production_productionentry)")
    columns = {row[1] for row in cursor.fetchall()}

    if 'entry_date' in columns:
        cursor.execute("ALTER TABLE production_productionentry RENAME COLUMN entry_date TO date")

    if 'qty_before' not in columns:
        cursor.execute(
            "ALTER TABLE production_productionentry ADD COLUMN qty_before DECIMAL(12,2) NOT NULL DEFAULT 0"
        )

    if 'qty_after' not in columns:
        cursor.execute(
            "ALTER TABLE production_productionentry ADD COLUMN qty_after DECIMAL(12,2) NOT NULL DEFAULT 0"
        )

    if 'created_by_id' not in columns:
        cursor.execute(
            "ALTER TABLE production_productionentry ADD COLUMN created_by_id BIGINT REFERENCES auth_user(id)"
        )


class Migration(migrations.Migration):
    """
    Conditionally fixes production_productionentry schema for instances where
    the table was created with an older schema (entry_date instead of date,
    missing qty_before/qty_after/created_by_id). On clean installs where
    0011 ran correctly this is a no-op.
    """

    dependencies = [
        ('production', '0011_productionentry'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[],
            database_operations=[
                migrations.RunPython(fix_schema_if_needed, migrations.RunPython.noop),
            ],
        ),
    ]
