# T009 — OrdenEstudio: PersonalSalud, estados T009, correlativo ORD-, related_name ordenes_estudio.

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def forwards_migrar_ordenes(apps, schema_editor):
    OrdenEstudio = apps.get_model("SolicitudDeEstudios", "OrdenEstudio")
    PersonalSalud = apps.get_model("GestionDePersonalDeSalud", "PersonalSalud")

    EST_MAP = {
        "PENDIENTE": "SOLICITADA",
        "EN_PROCESO": "EN_PROCESO",
        "DISPONIBLE": "COMPLETADA",
        "ENTREGADO": "COMPLETADA",
        "CANCELADO": "ANULADA",
    }
    TIPO_MAP = {"TAC": "TC", "OTR": "OTRO", "BIO": "OTRO"}

    ps_fallback = PersonalSalud.objects.order_by("pk").first()

    counters = {}

    for orden in OrdenEstudio.objects.order_by("pk"):
        orden.estado = EST_MAP.get(orden.estado, "SOLICITADA")

        t = getattr(orden, "tipo", None) or ""
        orden.tipo = TIPO_MAP.get(t, t)
        if orden.tipo == "OTR":
            orden.tipo = "OTRO"

        uid = orden.medico_legacy_user_id
        ps = PersonalSalud.objects.filter(user_id=uid).first() if uid else None
        if ps is None:
            ps = ps_fallback
        if ps is None:
            raise RuntimeError(
                "T009: no hay PersonalSalud en la base; cree al menos un registro antes de migrar."
            )
        orden.medico_solicitante_id = ps.pk

        fs = orden.fecha_solicitud
        y = fs.year if fs else django.utils.timezone.now().year
        counters[y] = counters.get(y, 0) + 1
        orden.correlativo_orden = f"ORD-{y}-{counters[y]:05d}"

        if orden.estado == "EN_PROCESO" and orden.fecha_inicio_proceso is None:
            orden.fecha_inicio_proceso = fs or django.utils.timezone.now()
        if orden.estado == "COMPLETADA":
            if orden.fecha_completada is None:
                orden.fecha_completada = fs or django.utils.timezone.now()
            if not orden.resultado_texto:
                orden.resultado_texto = "Migrado desde versión anterior del sistema."

        orden.save()


def backwards_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("GestionDePersonalDeSalud", "0001_initial"),
        ("SolicitudDeEstudios", "0002_alter_ordenestudio_consulta_and_more"),
    ]

    operations = [
        migrations.RemoveIndex(model_name="ordenestudio", name="idx_orden_estado_urgente"),
        migrations.RenameField(
            model_name="ordenestudio",
            old_name="tipo_estudio",
            new_name="tipo",
        ),
        migrations.AlterField(
            model_name="ordenestudio",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("LAB", "Laboratorio"),
                    ("RX", "Radiografía"),
                    ("ECO", "Ecografía"),
                    ("TC", "Tomografía Computarizada"),
                    ("RMN", "Resonancia Magnética"),
                    ("ECG", "Electrocardiograma"),
                    ("END", "Endoscopía"),
                    ("OTRO", "Otro"),
                ],
                db_index=True,
                max_length=20,
                verbose_name="Tipo",
            ),
        ),
        migrations.RenameField(
            model_name="ordenestudio",
            old_name="descripcion_estudio",
            new_name="descripcion",
        ),
        migrations.AlterField(
            model_name="ordenestudio",
            name="descripcion",
            field=models.TextField(
                help_text="Descripción detallada del estudio solicitado.",
                verbose_name="Descripción del estudio",
            ),
        ),
        migrations.RemoveField(model_name="ordenestudio", name="observaciones"),
        migrations.RemoveField(model_name="ordenestudio", name="fecha_limite"),
        migrations.RenameField(
            model_name="ordenestudio",
            old_name="medico_solicitante",
            new_name="medico_legacy_user",
        ),
        migrations.AlterField(
            model_name="ordenestudio",
            name="consulta",
            field=models.ForeignKey(
                help_text="Consulta médica en la que se solicitó este estudio.",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="ordenes_estudio",
                to="ConsultaMedicaSOAP.consulta",
                verbose_name="Consulta",
            ),
        ),
        migrations.AddField(
            model_name="ordenestudio",
            name="medico_solicitante",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="ordenes_solicitadas_tmp",
                to="GestionDePersonalDeSalud.personalsalud",
                verbose_name="Médico solicitante",
            ),
        ),
        migrations.AddField(
            model_name="ordenestudio",
            name="correlativo_orden",
            field=models.CharField(blank=True, editable=False, max_length=24, null=True, verbose_name="Correlativo"),
        ),
        migrations.AddField(
            model_name="ordenestudio",
            name="tecnico_responsable",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="ordenes_procesadas_tmp",
                to="GestionDePersonalDeSalud.personalsalud",
                verbose_name="Técnico responsable",
            ),
        ),
        migrations.AddField(
            model_name="ordenestudio",
            name="motivo_urgencia",
            field=models.TextField(blank=True, help_text="Obligatorio si urgente=True.", null=True, verbose_name="Motivo de urgencia"),
        ),
        migrations.AddField(
            model_name="ordenestudio",
            name="fecha_inicio_proceso",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Inicio en laboratorio"),
        ),
        migrations.AddField(
            model_name="ordenestudio",
            name="fecha_completada",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Completada"),
        ),
        migrations.AddField(
            model_name="ordenestudio",
            name="resultado_texto",
            field=models.TextField(blank=True, null=True, verbose_name="Resultado (texto)"),
        ),
        migrations.AddField(
            model_name="ordenestudio",
            name="resultado_archivo",
            field=models.FileField(blank=True, null=True, upload_to="resultados_estudios/%Y/%m/", verbose_name="Resultado (archivo)"),
        ),
        migrations.AddField(
            model_name="ordenestudio",
            name="esta_activa",
            field=models.BooleanField(default=True, verbose_name="Activa"),
        ),
        migrations.AddField(
            model_name="ordenestudio",
            name="creado_en",
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name="Creado en"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="ordenestudio",
            name="actualizado_en",
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name="Actualizado en"),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="ordenestudio",
            name="estado",
            field=models.CharField(
                choices=[
                    ("SOLICITADA", "Solicitada"),
                    ("EN_PROCESO", "En Proceso"),
                    ("COMPLETADA", "Completada"),
                    ("ANULADA", "Anulada"),
                ],
                db_index=True,
                default="SOLICITADA",
                max_length=20,
                verbose_name="Estado",
            ),
        ),
        migrations.RunPython(forwards_migrar_ordenes, backwards_noop),
        migrations.AlterField(
            model_name="ordenestudio",
            name="correlativo_orden",
            field=models.CharField(blank=True, editable=False, max_length=24, unique=True, verbose_name="Correlativo"),
        ),
        migrations.RemoveField(model_name="ordenestudio", name="medico_legacy_user"),
        migrations.AlterField(
            model_name="ordenestudio",
            name="medico_solicitante",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="ordenes_solicitadas",
                to="GestionDePersonalDeSalud.personalsalud",
                verbose_name="Médico solicitante",
            ),
        ),
        migrations.AlterField(
            model_name="ordenestudio",
            name="tecnico_responsable",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="ordenes_procesadas",
                to="GestionDePersonalDeSalud.personalsalud",
                verbose_name="Técnico responsable",
            ),
        ),
        migrations.AlterField(
            model_name="ordenestudio",
            name="actualizado_en",
            field=models.DateTimeField(auto_now=True, verbose_name="Actualizado en"),
        ),
        migrations.AddIndex(
            model_name="ordenestudio",
            index=models.Index(fields=["estado", "urgente"], name="orden_est_ix_est_urg"),
        ),
        migrations.AddIndex(
            model_name="ordenestudio",
            index=models.Index(fields=["consulta", "estado"], name="orden_est_ix_cons_est"),
        ),
        migrations.AddIndex(
            model_name="ordenestudio",
            index=models.Index(fields=["fecha_solicitud"], name="orden_est_ix_fecha_sol"),
        ),
    ]
