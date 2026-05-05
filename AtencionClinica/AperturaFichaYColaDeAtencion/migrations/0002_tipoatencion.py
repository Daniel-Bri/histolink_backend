# Generated manually for T014.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("AperturaFichaYColaDeAtencion", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TipoAtencion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=60, unique=True, verbose_name="Tipo de atención")),
                ("descripcion", models.CharField(blank=True, default="", max_length=200, verbose_name="Descripción")),
                ("activo", models.BooleanField(default=True, verbose_name="Activo")),
                ("creado_en", models.DateTimeField(auto_now_add=True, verbose_name="Creado en")),
                ("actualizado_en", models.DateTimeField(auto_now=True, verbose_name="Actualizado en")),
            ],
            options={
                "verbose_name": "Tipo de atención",
                "verbose_name_plural": "Tipos de atención",
                "ordering": ["nombre"],
            },
        ),
    ]
