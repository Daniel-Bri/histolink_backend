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
import logging

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from AtencionClinica.ConsultaMedicaSOAP.models import Consulta
from AtencionClinica.EmisionDeRecetaMedica.models import Receta
from AtencionClinica.RegistroDeTriaje.models import Triaje

from .exportadores import exportar_csv, exportar_excel, exportar_pdf
from .nlp_filtros import parsear_texto

NIVELES_ORDEN = ["ROJO", "NARANJA", "AMARILLO", "VERDE", "AZUL"]
User = get_user_model()
logger = logging.getLogger(__name__)


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
        params_or_response = self._resolver_params(request)
        if isinstance(params_or_response, Response):
            return params_or_response
        params = params_or_response
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
        if q:
            logger.info("[ReporteProduccion] q recibido=%s", q)
            logger.info("[ReporteProduccion] filtros NLP inferidos=%s", params)

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
        if request.query_params.get("tipo_reporte"):
            params["tipo_reporte"] = request.query_params["tipo_reporte"].lower()
        if q:
            params["q"] = q

        # 3. Defaults de fecha si no se infirió nada
        if "fecha_desde" not in params:
            params["fecha_desde"] = hoy.replace(day=1).isoformat()
        if "fecha_hasta" not in params:
            params["fecha_hasta"] = hoy.isoformat()

        # 4. Validación de rango de fechas
        try:
            d1 = date.fromisoformat(params["fecha_desde"])
            d2 = date.fromisoformat(params["fecha_hasta"])
        except ValueError:
            return Response(
                {"detail": "Formato de fecha inválido. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if d1 > d2:
            return Response(
                {"detail": "fecha_desde no puede ser mayor que fecha_hasta."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        logger.info(
            "[ReporteProduccion] fecha_desde final=%s fecha_hasta final=%s",
            params["fecha_desde"],
            params["fecha_hasta"],
        )

        return params

    def _filtro_medico_q(self, medico_nombre: str) -> Q:
        texto = (medico_nombre or "").strip()
        if not texto:
            return Q()
        tokens = [t for t in texto.split() if t]
        q = Q(first_name__icontains=texto) | Q(last_name__icontains=texto) | Q(username__icontains=texto)
        if len(tokens) > 1:
            q |= Q(first_name__icontains=tokens[0], last_name__icontains=tokens[-1])
        for t in tokens:
            q |= Q(first_name__icontains=t) | Q(last_name__icontains=t) | Q(username__icontains=t)
        return q

    def _usuarios_medico_ids(self, medico_nombre: str):
        q = self._filtro_medico_q(medico_nombre)
        return list(User.objects.filter(q).values_list("id", flat=True).distinct())

    # ── Aggregaciones principales (T037) ─────────────────────────────────────

    def _agregar(self, params: dict) -> dict:
        fecha_desde    = params["fecha_desde"]
        fecha_hasta    = params["fecha_hasta"]
        medico_id      = params.get("medico_id")
        medico_nombre  = params.get("medico_nombre")
        nivel_urgencia = params.get("nivel_urgencia")
        codigo_cie10   = params.get("codigo_cie10")
        tipo_reporte   = params.get("tipo_reporte", "resumen_general")
        advertencias: list[str] = []

        medico_ids_por_nombre = []
        medico_nombre_no_encontrado = False
        if medico_nombre:
            medico_ids_por_nombre = self._usuarios_medico_ids(medico_nombre)
            if not medico_ids_por_nombre:
                medico_nombre_no_encontrado = True
                advertencias.append(
                    f"No se encontró ningún médico que coincida con '{medico_nombre}'."
                )

        # ── Consultas ─────────────────────────────────────────────────────────
        qs_consultas = Consulta.objects.filter(
            creado_en__date__gte=fecha_desde,
            creado_en__date__lte=fecha_hasta,
            estado__in=["COMPLETADA", "FIRMADA"],
        )
        if medico_id:
            qs_consultas = qs_consultas.filter(medico_id=medico_id)
        elif medico_ids_por_nombre:
            qs_consultas = qs_consultas.filter(medico_id__in=medico_ids_por_nombre)
        elif medico_nombre_no_encontrado:
            qs_consultas = qs_consultas.none()
        if codigo_cie10:
            qs_consultas = qs_consultas.filter(
                codigo_cie10_principal__icontains=codigo_cie10
            )
        if nivel_urgencia:
            qs_consultas = qs_consultas.filter(triaje__nivel_urgencia=nivel_urgencia)

        total_consultas    = qs_consultas.count()
        total_derivaciones = qs_consultas.filter(requiere_derivacion=True).count()

        # ── Triajes ───────────────────────────────────────────────────────────
        qs_triajes = Triaje.objects.filter(
            hora_triaje__date__gte=fecha_desde,
            hora_triaje__date__lte=fecha_hasta,
        )
        if medico_id:
            qs_triajes = qs_triajes.filter(ficha__consultas__medico_id=medico_id).distinct()
        elif medico_ids_por_nombre:
            qs_triajes = qs_triajes.filter(ficha__consultas__medico_id__in=medico_ids_por_nombre).distinct()
        elif medico_nombre_no_encontrado:
            qs_triajes = qs_triajes.none()
        if nivel_urgencia:
            qs_triajes = qs_triajes.filter(nivel_urgencia=nivel_urgencia)

        total_triajes = qs_triajes.count()

        # ── Recetas ───────────────────────────────────────────────────────────
        qs_recetas_base = Receta.objects.all()
        logger.info("[ReporteProduccion] recetas antes del filtro=%s", qs_recetas_base.count())
        qs_recetas = qs_recetas_base.filter(
            fecha_emision__date__gte=fecha_desde,
            fecha_emision__date__lte=fecha_hasta,
        )
        if medico_id:
            qs_recetas = qs_recetas.filter(medico_id=medico_id)
        elif medico_ids_por_nombre:
            qs_recetas = qs_recetas.filter(medico_id__in=medico_ids_por_nombre)
        elif medico_nombre_no_encontrado:
            qs_recetas = qs_recetas.none()
        if nivel_urgencia:
            qs_recetas = qs_recetas.filter(consulta__triaje__nivel_urgencia=nivel_urgencia)
        logger.info("[ReporteProduccion] recetas despues del filtro=%s", qs_recetas.count())

        # ── Ajuste por intención/tipo de reporte ─────────────────────────────
        if tipo_reporte == "consultas":
            qs_triajes = Triaje.objects.none()
            qs_recetas = Receta.objects.none()
        elif tipo_reporte == "triajes":
            qs_consultas = Consulta.objects.none()
            qs_recetas = Receta.objects.none()
        elif tipo_reporte in {"recetas", "recetas_emitidas", "recetas_dispensadas", "recetas_anuladas"}:
            qs_consultas = Consulta.objects.none()
            qs_triajes = Triaje.objects.none()
            if tipo_reporte == "recetas_emitidas":
                qs_recetas = qs_recetas.filter(estado="EMITIDA")
            elif tipo_reporte == "recetas_dispensadas":
                qs_recetas = qs_recetas.filter(estado="DISPENSADA")
            elif tipo_reporte == "recetas_anuladas":
                qs_recetas = qs_recetas.filter(estado="ANULADA")

        recetas_emitidas    = qs_recetas.filter(estado="EMITIDA").count()
        recetas_dispensadas = qs_recetas.filter(estado="DISPENSADA").count()
        recetas_anuladas    = qs_recetas.filter(estado="ANULADA").count()

        if codigo_cie10 and total_consultas == 0:
            advertencias.append("No hay registros con el código CIE-10 indicado.")

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

        # ── Detalles completos (base para resumen_general y exportaciones) ───
        detalle_consultas = list(
            qs_consultas.values(
                "ficha__paciente__nombres",
                "ficha__paciente__apellido_paterno",
                "ficha__paciente__apellido_materno",
                "ficha__paciente__ci",
                "ficha__correlativo",
                "creado_en",
                "medico__first_name",
                "medico__last_name",
                "motivo_consulta",
                "codigo_cie10_principal",
                "descripcion_cie10",
                "impresion_diagnostica",
                "estado",
                "triaje__nivel_urgencia",
            ).order_by("-creado_en")[:200]
        )
        detalle_consultas = [
            {
                "paciente": " ".join(
                    p for p in [
                        r.get("ficha__paciente__nombres", ""),
                        r.get("ficha__paciente__apellido_paterno", ""),
                        r.get("ficha__paciente__apellido_materno", ""),
                    ] if p
                ).strip(),
                "ci": r.get("ficha__paciente__ci", ""),
                "numero_ficha": r.get("ficha__correlativo", ""),
                "fecha_consulta": str(r.get("creado_en", "")),
                "medico": " ".join(
                    p for p in [r.get("medico__first_name", ""), r.get("medico__last_name", "")] if p
                ).strip(),
                "motivo_consulta": r.get("motivo_consulta", ""),
                "codigo_cie10": r.get("codigo_cie10_principal", ""),
                "diagnostico": r.get("impresion_diagnostica", "") or r.get("descripcion_cie10", ""),
                "estado": r.get("estado", ""),
                "nivel_urgencia": r.get("triaje__nivel_urgencia", "") or "",
            }
            for r in detalle_consultas
        ]

        detalle_triajes = list(
            qs_triajes.values(
                "ficha__paciente__nombres",
                "ficha__paciente__apellido_paterno",
                "ficha__paciente__apellido_materno",
                "hora_triaje",
                "nivel_urgencia",
                "frecuencia_cardiaca",
                "frecuencia_respiratoria",
                "temperatura_celsius",
                "saturacion_oxigeno",
                "escala_dolor",
                "ficha__estado",
            ).order_by("-hora_triaje")[:200]
        )
        detalle_triajes = [
            {
                "paciente": " ".join(
                    p for p in [
                        r.get("ficha__paciente__nombres", ""),
                        r.get("ficha__paciente__apellido_paterno", ""),
                        r.get("ficha__paciente__apellido_materno", ""),
                    ] if p
                ).strip(),
                "fecha": str(r.get("hora_triaje", "")),
                "nivel_urgencia": r.get("nivel_urgencia", ""),
                "fc": r.get("frecuencia_cardiaca"),
                "fr": r.get("frecuencia_respiratoria"),
                "temperatura": r.get("temperatura_celsius"),
                "saturacion": r.get("saturacion_oxigeno"),
                "eva": r.get("escala_dolor"),
                "estado": r.get("ficha__estado", ""),
            }
            for r in detalle_triajes
        ]

        detalle_recetas = list(
            qs_recetas.values(
                "numero_receta",
                "estado",
                "fecha_emision",
                "fecha_dispensacion",
                "dispensada_por__first_name",
                "dispensada_por__last_name",
                "observaciones",
                "medico__first_name",
                "medico__last_name",
                "consulta__ficha__paciente__nombres",
                "consulta__ficha__paciente__apellido_paterno",
                "consulta__ficha__paciente__apellido_materno",
            ).order_by("-fecha_emision")[:200]
        )
        detalle_recetas = [
            {
                "numero_receta": r.get("numero_receta", ""),
                "fecha_emision": str(r.get("fecha_emision", "")),
                "fecha_dispensacion": str(r.get("fecha_dispensacion", "")) if r.get("fecha_dispensacion") else "",
                "paciente": " ".join(
                    p for p in [
                        r.get("consulta__ficha__paciente__nombres", ""),
                        r.get("consulta__ficha__paciente__apellido_paterno", ""),
                        r.get("consulta__ficha__paciente__apellido_materno", ""),
                    ] if p
                ).strip(),
                "medico": " ".join(
                    p for p in [r.get("medico__first_name", ""), r.get("medico__last_name", "")] if p
                ).strip(),
                "dispensada_por": " ".join(
                    p for p in [r.get("dispensada_por__first_name", ""), r.get("dispensada_por__last_name", "")] if p
                ).strip(),
                "estado": r.get("estado", ""),
                "observaciones": r.get("observaciones", ""),
                "motivo_anulacion": r.get("observaciones", ""),
            }
            for r in detalle_recetas
        ]

        # ── Detalle dinámico según tipo_reporte ──────────────────────────────
        if tipo_reporte in {"resumen_general", "consultas"}:
            detalle = detalle_consultas
        elif tipo_reporte == "triajes":
            detalle = detalle_triajes
        elif tipo_reporte in {"recetas", "recetas_emitidas", "recetas_dispensadas", "recetas_anuladas"}:
            detalle = detalle_recetas
        else:
            detalle = []

        # ── Tasa de derivación ────────────────────────────────────────────────
        tasa_derivacion = (
            round(total_derivaciones * 100 / total_consultas, 1)
            if total_consultas else 0.0
        )

        if total_consultas == 0 and total_triajes == 0 and recetas_emitidas == 0 and recetas_dispensadas == 0 and recetas_anuladas == 0:
            advertencias.append("No se encontraron registros para los filtros aplicados.")

        response = {
            "tipo_reporte": tipo_reporte,
            "periodo": {
                "desde":  fecha_desde,
                "hasta":  fecha_hasta,
                "fecha_desde": fecha_desde,
                "fecha_hasta": fecha_hasta,
            },
            "filtros_aplicados": {
                k: v for k, v in {
                    "fecha_desde":    fecha_desde,
                    "fecha_hasta":    fecha_hasta,
                    "medico_id":      medico_id,
                    "medico_nombre":  medico_nombre,
                    "nivel_urgencia": nivel_urgencia,
                    "codigo_cie10":   codigo_cie10,
                    "tipo_reporte":   tipo_reporte,
                    "q":              params.get("q"),
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
            "advertencias": advertencias,
            "detalle": detalle,
            "produccion_por_medico": produccion_por_medico,
            "top_diagnosticos": top_diagnosticos,
            "consultas_por_dia": consultas_por_dia,
        }

        if tipo_reporte == "resumen_general":
            response["detalle_consultas"] = detalle_consultas
            response["detalle_triajes"] = detalle_triajes
            response["detalle_recetas"] = detalle_recetas
            response["triajes_por_nivel"] = triajes_por_nivel
        elif tipo_reporte == "consultas":
            response["detalle_consultas"] = detalle_consultas
        elif tipo_reporte == "triajes":
            response["detalle_triajes"] = detalle_triajes
            response["triajes_por_nivel"] = triajes_por_nivel
        elif tipo_reporte in {"recetas", "recetas_emitidas", "recetas_dispensadas", "recetas_anuladas"}:
            response["detalle_recetas"] = detalle_recetas

        return response
