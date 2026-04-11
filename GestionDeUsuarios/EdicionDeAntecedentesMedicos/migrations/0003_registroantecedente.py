# Generated manually for T010 — registros puntuales de antecedentes

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("RegistroYBusquedaDePacientes", "0003_paciente_email_opcion_sexo_o"),
        ("EdicionDeAntecedentesMedicos", "0002_alter_antecedente_actualizado_en_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="RegistroAntecedente",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("familiar", "Familiar"),
                            ("personal", "Personal"),
                            ("alergia", "Alergia"),
                            ("medicamento", "Medicamento"),
                            ("quirurgico", "Quirúrgico"),
                        ],
                        max_length=20,
                        verbose_name="Tipo",
                    ),
                ),
                (
                    "descripcion",
                    models.CharField(max_length=500, verbose_name="Descripción"),
                ),
                (
                    "fecha_registro",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Fecha de registro",
                    ),
                ),
                (
                    "paciente",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="registros_antecedentes",
                        to="RegistroYBusquedaDePacientes.paciente",
                        verbose_name="Paciente",
                    ),
                ),
            ],
            options={
                "verbose_name": "Registro de antecedente",
                "verbose_name_plural": "Registros de antecedentes",
                "ordering": ["-fecha_registro"],
            },
        ),
    ]
