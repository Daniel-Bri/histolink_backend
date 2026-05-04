# Generated manually for T010.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("SolicitudDeEstudios", "0005_rename_index_estado_urgente"),
    ]

    operations = [
        migrations.AlterField(
            model_name="resultadoestudio",
            name="archivo_adjunto",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="resultados_estudios_adjuntos/%Y/%m/",
                verbose_name="Archivo adjunto",
            ),
        ),
        migrations.RenameField(
            model_name="resultadoestudio",
            old_name="hash_archivo",
            new_name="hash_sha256",
        ),
        migrations.AlterField(
            model_name="resultadoestudio",
            name="hash_sha256",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                max_length=64,
                verbose_name="Hash SHA-256",
            ),
        ),
    ]
