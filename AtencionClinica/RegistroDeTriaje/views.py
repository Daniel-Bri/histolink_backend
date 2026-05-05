# CU7 — Registro de Triaje
# T004: API POST + GET con filtros | T005: Integración ServicioML (flujo dos pasos)

import logging

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from GestionDeUsuarios.LoginYAutenticacion.permissions import EsMedicoOEnfermera

from .models import Triaje
from .serializers import ClasificarTriajeInputSerializer, TriajeSerializer

logger = logging.getLogger(__name__)

_COLORES = {1: "ROJO", 2: "NARANJA", 3: "AMARILLO", 4: "VERDE", 5: "AZUL"}


class TriajePagination(PageNumberPagination):
    page_size             = 20
    page_size_query_param = "page_size"
    max_page_size         = 100


class TriajeViewSet(viewsets.ModelViewSet):
    """
    CU7 — Endpoints de Triaje. Flujo de dos pasos:

    Paso 1 — clasificar sin guardar:
        POST /api/triaje/clasificar/   → recibe signos vitales + síntomas
                                       → devuelve nivel_sugerido + reglas_duras_aplicadas
                                       → NO toca la BD

    Paso 2 — guardar triaje confirmado:
        POST /api/triaje/              → recibe todo + nivel confirmado por enfermería
                                       → guarda registro completo y definitivo en BD

    Consultas:
        GET  /api/triaje/              → lista con filtros opcionales
        GET  /api/triaje/{id}/         → detalle de un triaje

    Filtros disponibles (query params):
        ?paciente=<id>
        ?nivel_urgencia=ROJO|NARANJA|AMARILLO|VERDE|AZUL
        ?fecha_desde=YYYY-MM-DD
        ?fecha_hasta=YYYY-MM-DD
        ?search=<texto>   (busca en motivo, CI y apellido del paciente)
    """

    serializer_class  = TriajeSerializer
    pagination_class  = TriajePagination
    filter_backends   = [filters.SearchFilter]
    search_fields     = [
        "motivo_consulta_triaje",
        "ficha__paciente__ci",
        "ficha__paciente__apellido_paterno",
    ]
    # Triaje es inmutable después de creado — no PUT/PATCH/DELETE
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action in ("create", "clasificar"):
            return [EsMedicoOEnfermera()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Triaje.objects.select_related("ficha__paciente", "enfermera").order_by("-hora_triaje")

        paciente_id = self.request.query_params.get("paciente")
        if paciente_id:
            qs = qs.filter(ficha__paciente_id=paciente_id)

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

    # ── Paso 1: POST /api/triaje/clasificar/ ───────────────────────────────
    @action(detail=False, methods=["post"], url_path="clasificar")
    def clasificar(self, request):
        """
        Clasifica con IA sin guardar en BD.
        El frontend muestra el nivel sugerido a la enfermera para que confirme o cambie.
        """
        serializer = ClasificarTriajeInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        signos = {k: v for k, v in {
            "saturacion_oxigeno":  data.get("saturacion_oxigeno"),
            "presion_sistolica":   data.get("presion_sistolica"),
            "frecuencia_cardiaca": data.get("frecuencia_cardiaca"),
            "escala_dolor":        data.get("escala_dolor"),
            "glasgow":             data.get("glasgow"),
        }.items() if v is not None}

        reglas_duras = _evaluar_reglas_duras(signos)

        try:
            from ml.servicio_ml import ServicioML
            svc      = ServicioML.obtener_instancia()
            resultado = svc.clasificar_triaje(
                texto_sintomas=data.get("motivo_consulta_triaje", ""),
                signos_vitales=signos,
                # triaje_id omitido: no queremos que el servicio escriba en BD
            )
            nivel_sugerido = _COLORES.get(resultado.get("nivel_predicho"), "AMARILLO")

            return Response({
                "nivel_sugerido":        nivel_sugerido,
                "nivel_numerico":        resultado.get("nivel_predicho"),
                "reglas_duras_aplicadas": reglas_duras,
                "confianza_pct":         resultado.get("confianza_pct", ""),
                "ajuste_signos":         resultado.get("ajuste_signos", ""),
                "probabilidades":        resultado.get("probabilidades", {}),
            }, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.warning("Error en clasificación IA (sin guardar): %s", exc)
            return Response({
                "nivel_sugerido":        "AMARILLO",
                "nivel_numerico":        3,
                "reglas_duras_aplicadas": reglas_duras,
                "error":                 str(exc),
            }, status=status.HTTP_200_OK)

    # ── Paso 2: POST /api/triaje/ ───────────────────────────────────────────
    def create(self, request, *args, **kwargs):
        """
        Guarda el triaje completo y definitivo en BD.
        Recibe el nivel ya confirmado por enfermería (nivel_urgencia)
        junto con nivel_sugerido_ia, fue_sobreescrito y justificacion_override.
        El registro nace completo — un solo evento en auditoría, hash válido para blockchain.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        triaje = serializer.save(tenant=getattr(request, "tenant", None))

        return Response(
            TriajeSerializer(triaje, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(serializer.data),
        )


# ── Helpers ────────────────────────────────────────────────────────────────

def _evaluar_reglas_duras(signos: dict) -> bool:
    """
    Retorna True si algún signo vital activa una regla dura clínica.
    Espejo de las reglas del modelo ML — usado para informar al frontend
    que la enfermera NO puede bajar el nivel por debajo del forzado.
    """
    spo2  = signos.get("saturacion_oxigeno")
    pas   = signos.get("presion_sistolica")
    gcs   = signos.get("glasgow")
    eva   = signos.get("escala_dolor")

    if spo2 is not None and spo2 < 90:
        return True
    if pas is not None and (pas < 80 or pas > 200):
        return True
    if gcs is not None and gcs <= 8:
        return True
    if spo2 is not None and spo2 < 94:
        return True
    if eva is not None and eva >= 9:
        return True
    return False
