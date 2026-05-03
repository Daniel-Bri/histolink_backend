# T003 — Elimina Triaje.paciente y obliga Triaje.ficha.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("RegistroDeTriaje", "0003_triaje_ficha_fk"),
        ("ConsultaMedicaSOAP", "0004_migrate_ficha_datos"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="triaje",
            name="paciente",
        ),
        migrations.AlterField(
            model_name="triaje",
            name="ficha",
            field=models.OneToOneField(
                help_text="Ficha clínica a la que pertenece este triaje.",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="triaje",
                to="AperturaFichaYColaDeAtencion.ficha",
                verbose_name="Ficha",
            ),
        ),
    ]
