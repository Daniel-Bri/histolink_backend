"""
Reportes/ReporteProduccion/views.py

T037 — GET /api/reportes/produccion/
T038 — Exportar Excel / CSV / PDF (despachado desde la misma vista)

Filtros disponibles (query params):
    fecha_desde     YYYY-MM-DD  (default: primer día del mes actual)
    fecha_hasta     YYYY-MM-DD  (default: hoy)
    medico_id       int         (opcional)
    medico_nombre   string      (opcional, búsqueda parcial apellido)
    nivel_urgencia  ROJO|NARANJA|AMARILLO|VERDE|AZUL  (opcional)
    codigo_cie10    string      (opcional)
    formato         json|excel|csv|pdf  (default: json)
    q               string      (texto libre → procesado por nlp_filtros.py)
"""

from datetime import date

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from AtencionClinica.ConsultaMedicaSOAP.models import Consulta
from AtencionClinica.EmisionDeRecetaMedica.models import Receta
from AtencionClinica.RegistroDeTriaje.models import Triaje

from .exportadores import exportar_csv, exportar_excel, exportar_pdf
from .nlp_filtros import parsear_texto

NIVELES_ORDEN = ["ROJO", "NARANJA", "AMARILLO", "VERDE", "AZUL"]


class ReporteProduccionView(APIView):
    """
    GET /api/reportes/produccion/

    Si formato=json  → devuelve JSON con todos los indicadores.
    Si formato=excel → descarga .xlsx
    Si formato=csv   → descarga .csv
    Si formato=pdf   → descarga .pdf

    Cuando se envía ?q=<texto>, primero se parsea con el módulo NLP
    y los filtros inferidos se fusionan con los query params explícitos
    (los explícitos tienen prioridad).
    """

    permission_classes = [IsAuthenticated]

    # ── Entrada ───────────────────────────────────────────────────────────────

    def get(self, request):
        params  = self._resolver_params(request)
        datos   = self._agregar(params)
        formato = params.get("formato", "json")

        if formato == "excel":
            return exportar_excel(datos)
        if formato == "csv":
            return exportar_csv(datos)
        if formato == "pdf":
            return exportar_pdf(datos)

        return Response(datos)

    # ── Resolución de parámetros (NLP + explícitos) ───────────────────────────

    def _resolver_params(self, request) -> dict:
        hoy = date.today()

        # 1. Parsear texto libre si viene en ?q=
        q = request.query_params.get("q", "").strip()
        params = parsear_texto(q, hoy) if q else {}

        # 2. Los query params explícitos sobreescriben lo inferido por NLP
        if request.query_params.get("fecha_desde"):
            params["fecha_desde"] = request.query_params["fecha_desde"]
        if request.query_params.get("fecha_hasta"):
            params["fecha_hasta"] = request.query_params["fecha_hasta"]
        if request.query_params.get("medico_id"):
            params["medico_id"] = request.query_params["medico_id"]
        if request.query_params.get("medico_nombre"):
            params["medico_nombre"] = request.query_params["medico_nombre"]
        if request.query_params.get("nivel_urgencia"):
            params["nivel_urgencia"] = request.query_params["nivel_urgencia"].upper()
        if request.query_params.get("codigo_cie10"):
            params["codigo_cie10"] = request.query_params["codigo_cie10"].upper()
        if request.query_params.get("formato"):
            params["formato"] = request.query_params["formato"].lower()

        # 3. Defaults de fecha si no se infirió nada
        if "fecha_desde" not in params:
            params["fecha_desde"] = hoy.replace(day=1).isoformat()
        if "fecha_hasta" not in params:
            params["fecha_hasta"] = hoy.isoformat()

        return params

    # ── Aggregaciones principales (T037) ─────────────────────────────────────

    def _agregar(self, params: dict) -> dict:
        fecha_desde    = params["fecha_desde"]
        fecha_hasta    = params["fecha_hasta"]
        medico_id      = params.get("medico_id")
        medico_nombre  = params.get("medico_nombre")
        nivel_urgencia = params.get("nivel_urgencia")
        codigo_cie10   = params.get("codigo_cie10")

        # ── Consultas ─────────────────────────────────────────────────────────
        qs_consultas = Consulta.objects.filter(
            creado_en__date__gte=fecha_desde,
            creado_en__date__lte=fecha_hasta,
            estado__in=["COMPLETADA", "FIRMADA"],
        )
        if medico_id:
            qs_consultas = qs_consultas.filter(medico_id=medico_id)
        if medico_nombre:
            qs_consultas = qs_consultas.filter(
                Q(medico__last_name__icontains=medico_nombre) |
                Q(medico__first_name__icontains=medico_nombre)
            )
        if codigo_cie10:
            qs_consultas = qs_consultas.filter(
                codigo_cie10_principal__icontains=codigo_cie10
            )

        total_consultas    = qs_consultas.count()
        total_derivaciones = qs_consultas.filter(requiere_derivacion=True).count()

        # ── Triajes ───────────────────────────────────────────────────────────
        qs_triajes = Triaje.objects.filter(
            hora_triaje__date__gte=fecha_desde,
            hora_triaje__date__lte=fecha_hasta,
        )
        if nivel_urgencia:
            qs_triajes = qs_triajes.filter(nivel_urgencia=nivel_urgencia)

        total_triajes = qs_triajes.count()

        # ── Recetas ───────────────────────────────────────────────────────────
        qs_recetas = Receta.objects.filter(
            fecha_emision__date__gte=fecha_desde,
            fecha_emision__date__lte=fecha_hasta,
        )
        if medico_id:
            qs_recetas = qs_recetas.filter(medico_id=medico_id)
        if medico_nombre:
            qs_recetas = qs_recetas.filter(
                Q(medico__last_name__icontains=medico_nombre) |
                Q(medico__first_name__icontains=medico_nombre)
            )

        recetas_emitidas    = qs_recetas.filter(estado="EMITIDA").count()
        recetas_dispensadas = qs_recetas.filter(estado="DISPENSADA").count()
        recetas_anuladas    = qs_recetas.filter(estado="ANULADA").count()

        # ── Triajes por nivel ─────────────────────────────────────────────────
        conteo_niveles = dict(
            qs_triajes.values_list("nivel_urgencia")
                      .annotate(total=Count("id"))
        )
        triajes_por_nivel = []
        for nivel in NIVELES_ORDEN:
            total_n = conteo_niveles.get(nivel, 0)
            pct     = round(total_n * 100 / total_triajes, 1) if total_triajes else 0.0
            triajes_por_nivel.append({
                "nivel_urgencia": nivel,
                "total":          total_n,
                "porcentaje":     pct,
            })

        # ── Producción por médico ─────────────────────────────────────────────
        produccion_raw = (
            qs_consultas
            .values("medico__id", "medico__first_name", "medico__last_name")
            .annotate(
                consultas=Count("id"),
                derivaciones=Count("id", filter=Q(requiere_derivacion=True)),
            )
            .order_by("-consultas")
        )
        ids_medicos = [r["medico__id"] for r in produccion_raw]
        recetas_por_medico = dict(
            Receta.objects.filter(
                medico_id__in=ids_medicos,
                fecha_emision__date__gte=fecha_desde,
                fecha_emision__date__lte=fecha_hasta,
            )
            .values_list("medico_id")
            .annotate(total=Count("id"))
        )

        produccion_por_medico = [
            {
                "medico":       f"{r['medico__first_name']} {r['medico__last_name']}".strip(),
                "medico_id":    r["medico__id"],
                "consultas":    r["consultas"],
                "recetas":      recetas_por_medico.get(r["medico__id"], 0),
                "derivaciones": r["derivaciones"],
            }
            for r in produccion_raw
        ]

        # ── Top 10 diagnósticos ───────────────────────────────────────────────
        top_diagnosticos = list(
            qs_consultas
            .values("codigo_cie10_principal", "descripcion_cie10")
            .annotate(total=Count("id"))
            .order_by("-total")[:10]
        )
        top_diagnosticos = [
            {
                "codigo":      r["codigo_cie10_principal"],
                "descripcion": r["descripcion_cie10"] or "",
                "total":       r["total"],
            }
            for r in top_diagnosticos
        ]

        # ── Consultas por día ─────────────────────────────────────────────────
        consultas_por_dia = list(
            qs_consultas
            .annotate(fecha=TruncDate("creado_en"))
            .values("fecha")
            .annotate(total=Count("id"))
            .order_by("fecha")
        )
        consultas_por_dia = [
            {"fecha": str(r["fecha"]), "total": r["total"]}
            for r in consultas_por_dia
        ]

        # ── Tasa de derivación ────────────────────────────────────────────────
        tasa_derivacion = (
            round(total_derivaciones * 100 / total_consultas, 1)
            if total_consultas else 0.0
        )

        return {
            "periodo": {
                "desde":  fecha_desde,
                "hasta":  fecha_hasta,
            },
            "filtros_aplicados": {
                k: v for k, v in {
                    "medico_id":      medico_id,
                    "medico_nombre":  medico_nombre,
                    "nivel_urgencia": nivel_urgencia,
                    "codigo_cie10":   codigo_cie10,
                }.items() if v
            },
            "resumen": {
                "total_consultas":          total_consultas,
                "total_triajes":            total_triajes,
                "total_recetas_emitidas":   recetas_emitidas,
                "total_recetas_dispensadas": recetas_dispensadas,
                "total_recetas_anuladas":   recetas_anuladas,
                "tasa_derivacion_pct":      tasa_derivacion,
            },
            "triajes_por_nivel":    triajes_por_nivel,
            "produccion_por_medico": produccion_por_medico,
            "top_diagnosticos":     top_diagnosticos,
            "consultas_por_dia":    consultas_por_dia,
        }
