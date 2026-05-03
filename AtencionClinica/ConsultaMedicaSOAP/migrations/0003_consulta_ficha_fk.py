# T003 — Añade Consulta ↔ Ficha (nullable hasta migración de datos).

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("AperturaFichaYColaDeAtencion", "0001_initial"),
        ("ConsultaMedicaSOAP", "0002_alter_consulta_actualizado_en_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="consulta",
            name="ficha",
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                help_text="Ficha clínica bajo la cual se registra esta consulta.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="consultas",
                to="AperturaFichaYColaDeAtencion.ficha",
                verbose_name="Ficha",
            ),
        ),
    ]
