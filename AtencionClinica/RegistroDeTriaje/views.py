# CU7 — Registro de Triaje
# T004: API POST + GET con filtros | T005: Integración ServicioML

import logging

from rest_framework import filters, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from GestionDeUsuarios.LoginYAutenticacion.permissions import (
    EsMedicoOEnfermera,
)

from .models import Triaje
from .serializers import TriajeSerializer

logger = logging.getLogger(__name__)

_COLORES = {1: "ROJO", 2: "NARANJA", 3: "AMARILLO", 4: "VERDE", 5: "AZUL"}


class TriajePagination(PageNumberPagination):
    page_size            = 20
    page_size_query_param = "page_size"
    max_page_size        = 100


class TriajeViewSet(viewsets.ModelViewSet):
    """
    CU7 — Endpoints de Triaje.

    GET  /api/triaje/          → lista con filtros opcionales
    POST /api/triaje/          → crea triaje + clasifica con IA
    GET  /api/triaje/{id}/     → detalle de un triaje

    Filtros disponibles (query params):
        ?paciente=<id>
        ?nivel_urgencia=ROJO|NARANJA|AMARILLO|VERDE|AZUL
        ?fecha_desde=YYYY-MM-DD
        ?fecha_hasta=YYYY-MM-DD
        ?search=<texto>         (busca en motivo, CI y apellido del paciente)
    """

    serializer_class  = TriajeSerializer
    pagination_class  = TriajePagination
    filter_backends   = [filters.SearchFilter]
    search_fields     = [
        "motivo_consulta_triaje",
        "paciente__ci",
        "paciente__apellido_paterno",
    ]
    # Triaje es inmutable después de creado — no PUT/PATCH/DELETE
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action == "create":
            return [EsMedicoOEnfermera()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Triaje.objects.select_related("paciente", "enfermera").order_by("-hora_triaje")

        paciente_id = self.request.query_params.get("paciente")
        if paciente_id:
            qs = qs.filter(paciente_id=paciente_id)

        nivel = self.request.query_params.get("nivel_urgencia")
        if nivel:
            qs = qs.filter(nivel_urgencia=nivel.upper())

        fecha_desde = self.request.query_params.get("fecha_desde")
        if fecha_desde:
            qs = qs.filter(hora_triaje__date__gte=fecha_desde)

        fecha_hasta = self.request.query_params.get("fecha_hasta")
        if fecha_hasta:
            qs = qs.filter(hora_triaje__date__lte=fecha_hasta)

        return qs

    # ── POST /api/triaje/ ───────────────────────────────────────────────────
    def create(self, request, *args, **kwargs):
        nivel_manual = request.data.get("nivel_urgencia")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        triaje = serializer.save(tenant=getattr(request, "tenant", None))

        prediccion_ia = self._clasificar_con_ia(triaje, nivel_manual)

        return Response(
            {
                "triaje":        TriajeSerializer(triaje, context={"request": request}).data,
                "prediccion_ia": prediccion_ia,
            },
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(serializer.data),
        )

    # ── Integración ML (T005) ───────────────────────────────────────────────
    def _clasificar_con_ia(self, triaje: Triaje, nivel_manual: str | None) -> dict:
        """
        Llama al ServicioML para clasificar el triaje.

        Reglas:
        1. Las reglas duras del modelo (SpO2, PA, FC, Glasgow, EVA) siempre
           se aplican dentro del propio modelo — no se duplican aquí.
        2. Si la enfermera NO fijó nivel_urgencia en el body → se usa el
           nivel que devuelve la IA y se persiste.
        3. Si la enfermera SÍ lo fijó → el nivel manual prevalece; la IA
           sigue corriendo para mostrar su sugerencia pero no sobreescribe.
        """
        try:
            from ml.servicio_ml import ServicioML

            svc = ServicioML.obtener_instancia()

            signos = {
                k: v for k, v in {
                    "saturacion_oxigeno":    triaje.saturacion_oxigeno,
                    "presion_sistolica":     triaje.presion_sistolica,
                    "frecuencia_cardiaca":   triaje.frecuencia_cardiaca,
                    "escala_dolor":          triaje.escala_dolor,
                }.items() if v is not None
            }

            prediccion = svc.clasificar_triaje(
                texto_sintomas=triaje.motivo_consulta_triaje or "",
                signos_vitales=signos,
                # triaje_id omitido: el servicio solo sobreescribe si nivel_urgencia IS NULL;
                # aquí controlamos la escritura manualmente para mayor claridad.
            )

            if not nivel_manual:
                # Usar nivel sugerido por la IA
                triaje.nivel_urgencia = _COLORES.get(prediccion["nivel_predicho"], "AMARILLO")
                triaje.save(update_fields=["nivel_urgencia"])
                prediccion["asignado_por"] = "IA"
            else:
                prediccion["asignado_por"] = "enfermeria"

            return prediccion

        except Exception as exc:
            logger.warning("Error en clasificación IA triaje %s: %s", triaje.id, exc)
            return {
                "error":         str(exc),
                "asignado_por":  "manual_o_error",
                "nivel_predicho": None,
            }
