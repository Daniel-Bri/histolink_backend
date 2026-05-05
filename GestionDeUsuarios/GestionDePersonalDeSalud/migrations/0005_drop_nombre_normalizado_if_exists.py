from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("GestionDePersonalDeSalud", "0004_especialidad_nombre_normalizado"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE \"GestionDePersonalDeSalud_especialidad\" "
                "DROP COLUMN IF EXISTS \"nombre_normalizado\";"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
