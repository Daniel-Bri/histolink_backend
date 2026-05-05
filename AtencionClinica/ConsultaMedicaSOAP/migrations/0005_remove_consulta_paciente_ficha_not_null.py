# T003 — Elimina Consulta.paciente y obliga Consulta.ficha.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ConsultaMedicaSOAP", "0004_migrate_ficha_datos"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="consulta",
            name="paciente",
        ),
        migrations.AlterField(
            model_name="consulta",
            name="ficha",
            field=models.ForeignKey(
                db_index=True,
                help_text="Ficha clínica bajo la cual se registra esta consulta.",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="consultas",
                to="AperturaFichaYColaDeAtencion.ficha",
                verbose_name="Ficha",
            ),
        ),
    ]
