# Generated manually for modelo Ficha (T003).

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("GestionDePersonalDeSalud", "0001_initial"),
        ("RegistroYBusquedaDePacientes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Ficha",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("estado", models.CharField(choices=[
                    ("ABIERTA", "Abierta"),
                    ("EN_TRIAJE", "En Triaje"),
                    ("EN_ATENCION", "En Atención"),
                    ("CERRADA", "Cerrada"),
                    ("CANCELADA", "Cancelada"),
                ], db_index=True, default="ABIERTA", max_length=20, verbose_name="Estado")),
                ("correlativo", models.CharField(blank=True, editable=False, max_length=20, unique=True, verbose_name="Correlativo")),
                ("fecha_apertura", models.DateTimeField(auto_now_add=True, verbose_name="Fecha de apertura")),
                ("fecha_inicio_atencion", models.DateTimeField(blank=True, null=True, verbose_name="Inicio de atención médica")),
                ("fecha_cierre", models.DateTimeField(blank=True, null=True, verbose_name="Fecha de cierre")),
                ("esta_activa", models.BooleanField(default=True, verbose_name="Activa (no eliminada lógicamente)")),
                ("creado_en", models.DateTimeField(auto_now_add=True, verbose_name="Creado en")),
                ("actualizado_en", models.DateTimeField(auto_now=True, verbose_name="Actualizado en")),
                ("paciente", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="fichas",
                    to="RegistroYBusquedaDePacientes.paciente",
                    verbose_name="Paciente",
                )),
                ("profesional_apertura", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="fichas_aperturadas",
                    to="GestionDePersonalDeSalud.personalsalud",
                    verbose_name="Profesional que abre la ficha",
                )),
            ],
            options={
                "verbose_name": "Ficha",
                "verbose_name_plural": "Fichas",
                "ordering": ["-fecha_apertura"],
            },
        ),
        migrations.AddIndex(model_name="ficha", index=models.Index(fields=["estado", "fecha_apertura"], name="ficha_ix_est_ap")),
        migrations.AddIndex(model_name="ficha", index=models.Index(fields=["paciente", "estado"], name="ficha_ix_pac_est")),
    ]
