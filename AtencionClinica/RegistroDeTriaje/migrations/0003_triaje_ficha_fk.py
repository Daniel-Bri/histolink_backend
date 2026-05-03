# T003 — Añade relación Triaje ↔ Ficha (nullable hasta migración de datos).

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("AperturaFichaYColaDeAtencion", "0001_initial"),
        ("RegistroDeTriaje", "0002_alter_triaje_enfermera_alter_triaje_escala_dolor_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="triaje",
            name="ficha",
            field=models.OneToOneField(
                blank=True,
                help_text="Ficha clínica a la que pertenece este triaje.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="triaje",
                to="AperturaFichaYColaDeAtencion.ficha",
                verbose_name="Ficha",
            ),
        ),
    ]
