from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from GestionDeUsuarios.LoginYAutenticacion.permissions import EsMedico
from IA_Blockchain.GestionDeIdentidadBlockchain.models import EventoBlockchain
from SeguridadAvanzadaYAdministracion.Auditoria.audit_utils import registrar_evento

from .models import BreakGlassSolicitud
from .serializers import BreakGlassSolicitudCreateSerializer, BreakGlassSolicitudListSerializer


def _es_auditor_director_admin(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=["Auditor", "Director", "Administrativo"]).exists()


class BreakGlassSolicitarView(APIView):
    permission_classes = [permissions.IsAuthenticated, EsMedico]

    @extend_schema(
        tags=["Break-Glass"],
        summary="Solicitar acceso Break-Glass",
        description=(
            "Crea una solicitud de acceso de emergencia a un expediente. "
            "Si la urgencia es ALTA, otorga acceso temporal inmediato por 2 horas."
        ),
        request=BreakGlassSolicitudCreateSerializer,
        responses={
            201: BreakGlassSolicitudListSerializer,
            400: OpenApiResponse(description="Datos invalidos, solicitud duplicada o justificacion insuficiente."),
            401: OpenApiResponse(description="Token JWT faltante o invalido."),
            403: OpenApiResponse(description="Solo usuarios con rol Medico pueden solicitar Break-Glass."),
        },
    )
    def post(self, request):
        serializer = BreakGlassSolicitudCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            solicitud = serializer.save()
        except DjangoValidationError as exc:
            detail = exc.message_dict if hasattr(exc, "message_dict") else {"detail": exc.messages}
            return Response(detail, status=status.HTTP_400_BAD_REQUEST)

        payload = {
            "solicitud_id": solicitud.id,
            "solicitante_id": solicitud.solicitante_id,
            "paciente_id": solicitud.paciente_id,
            "nivel_urgencia": solicitud.nivel_urgencia,
            "justificacion": solicitud.justificacion,
            "timestamp": solicitud.creado_en.isoformat(),
        }
        evento = EventoBlockchain.crear_evento(
            tipo_evento="BREAK_GLASS_SOLICITUD",
            payload=payload,
            tenant_id=solicitud.tenant_id,
            documento_tipo="BreakGlassSolicitud",
            documento_id=solicitud.id,
            firmado_por=request.user,
        )
        solicitud.evento_blockchain = evento
        solicitud.save(update_fields=["evento_blockchain", "actualizado_en"])

        registrar_evento(
            accion="CREATE",
            objeto=solicitud,
            cambios={
                "solicitante_id": solicitud.solicitante_id,
                "paciente_id": solicitud.paciente_id,
                "nivel_urgencia": solicitud.nivel_urgencia,
            },
            request=request,
        )
        out = BreakGlassSolicitudListSerializer(solicitud, context={"request": request}).data
        if solicitud.nivel_urgencia == BreakGlassSolicitud.NivelUrgencia.ALTA:
            out["advertencia"] = "Acceso temporal otorgado por emergencia"
        return Response(out, status=status.HTTP_201_CREATED)


class BreakGlassMisSolicitudesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Break-Glass"],
        summary="Listar mis solicitudes Break-Glass",
        description="Devuelve las solicitudes Break-Glass creadas por el usuario autenticado.",
        responses={200: BreakGlassSolicitudListSerializer(many=True)},
    )
    def get(self, request):
        qs = BreakGlassSolicitud.objects.filter(solicitante=request.user).select_related("paciente", "solicitante")
        return Response(BreakGlassSolicitudListSerializer(qs, many=True).data)


class BreakGlassPendientesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Break-Glass"],
        summary="Listar solicitudes Break-Glass pendientes",
        description="Devuelve solicitudes pendientes para revision por Auditor, Director o Administrativo.",
        responses={
            200: BreakGlassSolicitudListSerializer(many=True),
            403: OpenApiResponse(description="El usuario no tiene permisos para ver solicitudes pendientes."),
        },
    )
    def get(self, request):
        if not _es_auditor_director_admin(request.user):
            return Response({"detail": "No tiene permisos para ver solicitudes pendientes."}, status=status.HTTP_403_FORBIDDEN)
        BreakGlassSolicitud.expirar_vencidas()
        qs = BreakGlassSolicitud.objects.filter(estado=BreakGlassSolicitud.Estado.PENDIENTE).select_related(
            "paciente", "solicitante"
        )
        return Response(BreakGlassSolicitudListSerializer(qs, many=True).data)
