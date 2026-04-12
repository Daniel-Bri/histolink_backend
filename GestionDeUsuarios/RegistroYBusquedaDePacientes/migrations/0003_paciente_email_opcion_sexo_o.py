# Generated manually for T010 — email opcional y sexo "Otro"

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("RegistroYBusquedaDePacientes", "0002_alter_paciente_activo_alter_paciente_actualizado_en_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="paciente",
            name="email",
            field=models.EmailField(
                blank=True,
                default="",
                max_length=254,
                verbose_name="Correo electrónico",
            ),
        ),
        migrations.AlterField(
            model_name="paciente",
            name="sexo",
            field=models.CharField(
                choices=[
                    ("M", "Masculino"),
                    ("F", "Femenino"),
                    ("O", "Otro"),
                ],
                help_text="Sexo registrado: M, F u O (otro / no binario / prefiero no indicar).",
                max_length=1,
                verbose_name="Sexo",
            ),
        ),
    ]
