# T003 — Poblado de Ficha y enlaces FK para registros legacy.

from django.apps.registry import Apps
from django.db import migrations


def forwards(apps: Apps, schema_editor):
    TriajeHist = apps.get_model("RegistroDeTriaje", "Triaje")
    ConsultaHist = apps.get_model("ConsultaMedicaSOAP", "Consulta")
    FichaHist = apps.get_model("AperturaFichaYColaDeAtencion", "Ficha")
    PersonalSaludHist = apps.get_model("GestionDePersonalDeSalud", "PersonalSalud")

    if not TriajeHist.objects.exists() and not ConsultaHist.objects.exists():
        return

    ps = PersonalSaludHist.objects.order_by("pk").first()
    if ps is None:
        raise RuntimeError(
            "Migración T003: hay Triajes o Consultas en BD pero ningún PersonalSalud para "
            "asignar como profesional_apertura en Fichas generadas retroactivamente. "
            "Cargue datos de PersonalSalud antes de ejecutar migrate."
        )

    counters = {}

    def siguiente_correlativo(fecha_ts):
        y = fecha_ts.year
        counters[y] = counters.get(y, 0) + 1
        return f"FICHA-{y}-{counters[y]:05d}"

    for tri in TriajeHist.objects.order_by("pk"):
        if tri.ficha_id:
            continue
        cod = siguiente_correlativo(tri.hora_triaje)
        fh = FichaHist.objects.create(
            paciente_id=tri.paciente_id,
            profesional_apertura_id=ps.pk,
            estado="CERRADA",
            correlativo=cod,
            fecha_apertura=tri.hora_triaje,
            fecha_cierre=tri.hora_triaje,
            esta_activa=True,
        )
        TriajeHist.objects.filter(pk=tri.pk).update(ficha_id=fh.pk)

    for cons in ConsultaHist.objects.order_by("pk"):
        if cons.ficha_id:
            continue
        if cons.triaje_id:
            tr = TriajeHist.objects.only("ficha_id").get(pk=cons.triaje_id)
            if not tr.ficha_id:
                raise RuntimeError(
                    f"Migración T003: Consulta {cons.pk} apunta a Triaje sin ficha tras el paso de triajes."
                )
            ConsultaHist.objects.filter(pk=cons.pk).update(ficha_id=tr.ficha_id)
            continue

        cod = siguiente_correlativo(cons.creado_en)
        fh = FichaHist.objects.create(
            paciente_id=cons.paciente_id,
            profesional_apertura_id=ps.pk,
            estado="CERRADA",
            correlativo=cod,
            fecha_apertura=cons.creado_en,
            fecha_cierre=cons.creado_en,
            esta_activa=True,
        )
        ConsultaHist.objects.filter(pk=cons.pk).update(ficha_id=fh.pk)


def backwards_nada(apps, schema_editor):
    """No reversible de forma segura (no borramos Fichas ni desenlazamos)."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("ConsultaMedicaSOAP", "0003_consulta_ficha_fk"),
        ("RegistroDeTriaje", "0003_triaje_ficha_fk"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards_nada),
    ]
