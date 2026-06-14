from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import permissions, status
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from IA_Blockchain.GestionDeIdentidadBlockchain.models import EventoBlockchain
from SeguridadAvanzadaYAdministracion.Auditoria.audit_utils import registrar_evento
from SeguridadAvanzadaYAdministracion.BreakGlass_Solicitud.models import BreakGlassSolicitud

from .helpers import construir_notificacion_rechazo
from .permissions import EsAuditorODirector
from .serializers import BreakGlassSolicitudRechazoSerializer


AprobarBreakGlassResponseSerializer = inline_serializer(
    name="AprobarBreakGlassResponse",
    fields={
        "mensaje": serializers.CharField(),
        "estado": serializers.CharField(),
        "acceso_desde": serializers.DateTimeField(allow_null=True),
        "acceso_hasta": serializers.DateTimeField(allow_null=True),
    },
)

RechazarBreakGlassResponseSerializer = inline_serializer(
    name="RechazarBreakGlassResponse",
    fields={
        "mensaje": serializers.CharField(),
        "estado": serializers.CharField(),
        "motivo_rechazo": serializers.CharField(),
        "notificacion": serializers.DictField(),
    },
)


def _obtener_solicitud(pk: int) -> BreakGlassSolicitud:
    return get_object_or_404(
        BreakGlassSolicitud.objects.select_related("solicitante", "paciente", "tenant", "aprobado_por"),
        pk=pk,
    )


def _validar_autoria(solicitud: BreakGlassSolicitud, user) -> Response | None:
    if solicitud.solicitante_id == user.id:
        return Response(
            {"detail": "No puedes aprobar tu propia solicitud Break-Glass."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


class BreakGlassAprobarView(APIView):
    permission_classes = [permissions.IsAuthenticated, EsAuditorODirector]

    @extend_schema(
        tags=["Break-Glass"],
        summary="Aprobar solicitud Break-Glass",
        description=(
            "Permite a un Auditor o Director aprobar una solicitud Break-Glass pendiente. "
            "Aplica anti-autoaprobacion, activa acceso temporal y registra auditoria/blockchain."
        ),
        request=None,
        responses={
            200: AprobarBreakGlassResponseSerializer,
            400: OpenApiResponse(description="Solicitud expirada o datos invalidos."),
            403: OpenApiResponse(description="Rol no autorizado o intento de autoaprobacion."),
            404: OpenApiResponse(description="Solicitud Break-Glass no encontrada."),
            409: OpenApiResponse(description="La solicitud ya no esta pendiente."),
        },
    )
    def post(self, request, pk: int):
        solicitud = _obtener_solicitud(pk)

        if solicitud.estado != BreakGlassSolicitud.Estado.PENDIENTE:
            return Response(
                {"detail": f"La solicitud no puede aprobarse porque está en estado {solicitud.estado}."},
                status=status.HTTP_409_CONFLICT,
            )

        if solicitud.acceso_expirado:
            return Response(
                {"detail": "La solicitud está expirada y no puede aprobarse."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        denial = _validar_autoria(solicitud, request.user)
        if denial:
            return denial

        now = timezone.now()
        acceso_desde = solicitud.acceso_desde or now
        acceso_hasta = solicitud.acceso_hasta or (now + timedelta(hours=2))
        if acceso_hasta <= now:
            acceso_desde = now
            acceso_hasta = now + timedelta(hours=2)

        with transaction.atomic():
            BreakGlassSolicitud.objects.filter(pk=solicitud.pk).update(
                estado=BreakGlassSolicitud.Estado.APROBADA,
                aprobado_por_id=request.user.id,
                acceso_desde=acceso_desde,
                acceso_hasta=acceso_hasta,
                actualizado_en=now,
            )
            solicitud.refresh_from_db()

            payload = {
                "solicitud_id": solicitud.id,
                "aprobado_por": request.user.id,
                "solicitante": solicitud.solicitante_id,
                "paciente": solicitud.paciente_id,
                "estado": solicitud.estado,
                "timestamp": now.isoformat(),
            }
            evento = EventoBlockchain.crear_evento(
                tipo_evento="APROBACION_BREAK_GLASS",
                payload=payload,
                tenant_id=solicitud.tenant_id,
                documento_tipo="BreakGlassSolicitud",
                documento_id=solicitud.id,
                firmado_por=request.user,
            )
            BreakGlassSolicitud.objects.filter(pk=solicitud.pk).update(
                evento_blockchain_id=evento.id,
                actualizado_en=timezone.now(),
            )
            solicitud.refresh_from_db()

            registrar_evento(
                accion="UPDATE",
                objeto=solicitud,
                cambios={
                    "estado": solicitud.estado,
                    "aprobado_por_id": solicitud.aprobado_por_id,
                    "acceso_desde": solicitud.acceso_desde.isoformat() if solicitud.acceso_desde else None,
                    "acceso_hasta": solicitud.acceso_hasta.isoformat() if solicitud.acceso_hasta else None,
                    "evento_blockchain_id": solicitud.evento_blockchain_id,
                },
                request=request,
            )

        return Response(
            {
                "mensaje": "Solicitud Break-Glass aprobada correctamente.",
                "estado": solicitud.estado,
                "acceso_desde": solicitud.acceso_desde.isoformat() if solicitud.acceso_desde else None,
                "acceso_hasta": solicitud.acceso_hasta.isoformat() if solicitud.acceso_hasta else None,
            },
            status=status.HTTP_200_OK,
        )


class BreakGlassRechazarView(APIView):
    permission_classes = [permissions.IsAuthenticated, EsAuditorODirector]

    @extend_schema(
        tags=["Break-Glass"],
        summary="Rechazar solicitud Break-Glass",
        description=(
            "Permite a un Auditor o Director rechazar una solicitud Break-Glass pendiente "
            "indicando un motivo. Registra auditoria, blockchain y notificacion al solicitante."
        ),
        request=BreakGlassSolicitudRechazoSerializer,
        responses={
            200: RechazarBreakGlassResponseSerializer,
            400: OpenApiResponse(description="Motivo de rechazo invalido o solicitud expirada."),
            403: OpenApiResponse(description="Rol no autorizado o intento de autorevision."),
            404: OpenApiResponse(description="Solicitud Break-Glass no encontrada."),
            409: OpenApiResponse(description="La solicitud ya no esta pendiente."),
        },
    )
    def post(self, request, pk: int):
        solicitud = _obtener_solicitud(pk)

        if solicitud.estado != BreakGlassSolicitud.Estado.PENDIENTE:
            return Response(
                {"detail": f"La solicitud no puede rechazarse porque está en estado {solicitud.estado}."},
                status=status.HTTP_409_CONFLICT,
            )

        if solicitud.acceso_expirado:
            return Response(
                {"detail": "La solicitud está expirada y no puede rechazarse."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        denial = _validar_autoria(solicitud, request.user)
        if denial:
            return denial

        serializer = BreakGlassSolicitudRechazoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        motivo_rechazo = serializer.validated_data["motivo_rechazo"]
        now = timezone.now()

        with transaction.atomic():
            BreakGlassSolicitud.objects.filter(pk=solicitud.pk).update(
                estado=BreakGlassSolicitud.Estado.RECHAZADA,
                aprobado_por_id=request.user.id,
                motivo_rechazo=motivo_rechazo,
                acceso_desde=None,
                acceso_hasta=None,
                actualizado_en=now,
            )
            solicitud.refresh_from_db()

            payload = {
                "solicitud_id": solicitud.id,
                "aprobado_por": request.user.id,
                "solicitante": solicitud.solicitante_id,
                "paciente": solicitud.paciente_id,
                "estado": solicitud.estado,
                "motivo_rechazo": motivo_rechazo,
                "timestamp": now.isoformat(),
            }
            evento = EventoBlockchain.crear_evento(
                tipo_evento="RECHAZO_BREAK_GLASS",
                payload=payload,
                tenant_id=solicitud.tenant_id,
                documento_tipo="BreakGlassSolicitud",
                documento_id=solicitud.id,
                firmado_por=request.user,
            )
            BreakGlassSolicitud.objects.filter(pk=solicitud.pk).update(
                evento_blockchain_id=evento.id,
                actualizado_en=timezone.now(),
            )
            solicitud.refresh_from_db()

            registrar_evento(
                accion="UPDATE",
                objeto=solicitud,
                cambios={
                    "estado": solicitud.estado,
                    "motivo_rechazo": solicitud.motivo_rechazo,
                    "aprobado_por_id": solicitud.aprobado_por_id,
                    "evento_blockchain_id": solicitud.evento_blockchain_id,
                },
                request=request,
            )

        notificacion = construir_notificacion_rechazo(solicitud, motivo_rechazo)

        return Response(
            {
                "mensaje": "Solicitud Break-Glass rechazada correctamente.",
                "estado": solicitud.estado,
                "motivo_rechazo": motivo_rechazo,
                "notificacion": notificacion,
            },
            status=status.HTTP_200_OK,
        )
