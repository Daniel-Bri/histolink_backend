# Renombra índice compuesto estado+urgente a nombre estable y ≤30 chars (Django E034).

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("SolicitudDeEstudios", "0004_t009_orden_estudio"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="ordenestudio",
            new_name="ordenestudio_esturg_idx",
            old_name="SolicitudDe_estado_b95307_idx",
        ),
    ]
