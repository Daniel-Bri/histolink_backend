# CU10 — API órdenes de estudio (T009)

from typing import Optional

from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import OrdenEstudio
from .permissions import OrdenEstudioPermission, es_admin_o_super, es_medico
from .serializers import (
    OrdenEstudioAdminUpdateSerializer,
    OrdenEstudioCambiarEstadoSerializer,
    OrdenEstudioCreateResponseSerializer,
    OrdenEstudioCreateSerializer,
    OrdenEstudioDetailSerializer,
    OrdenEstudioListSerializer,
    OrdenEstudioUpdateMedicoSerializer,
    personal_desde_usuario,
)


class OrdenEstudioViewSet(viewsets.ModelViewSet):
    queryset = OrdenEstudio.objects.select_related(
        "consulta__ficha__paciente",
        "medico_solicitante__user",
        "tecnico_responsable__user",
    )
    permission_classes = [IsAuthenticated, OrdenEstudioPermission]

    def get_serializer_class(self):
        if self.action == "create":
            return OrdenEstudioCreateSerializer
        if self.action == "list":
            return OrdenEstudioListSerializer
        if self.action == "retrieve":
            return OrdenEstudioDetailSerializer
        if self.action in ("update", "partial_update"):
            if es_admin_o_super(self.request.user):
                return OrdenEstudioAdminUpdateSerializer
            return OrdenEstudioUpdateMedicoSerializer
        if self.action == "cambiar_estado":
            return OrdenEstudioCambiarEstadoSerializer
        return OrdenEstudioDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("incluir_inactivas", "").lower() not in ("1", "true", "yes"):
            qs = qs.filter(esta_activa=True)

        def _truthy(val: str) -> Optional[bool]:
            v = (val or "").lower()
            if v in ("1", "true", "yes"):
                return True
            if v in ("0", "false", "no"):
                return False
            return None

        p = self.request.query_params
        est = p.get("estado")
        if est:
            qs = qs.filter(estado=est.upper())

        if _truthy(p.get("solo_urgentes")) is True:
            qs = qs.filter(urgente=True)
        elif (u := _truthy(p.get("urgente"))) is True:
            qs = qs.filter(urgente=True)
        elif u is False:
            qs = qs.filter(urgente=False)

        tipo = p.get("tipo")
        if tipo:
            qs = qs.filter(tipo=tipo.upper())

        cid = p.get("consulta")
        if cid:
            qs = qs.filter(consulta_id=cid)

        if p.get("pendientes", "").lower() in ("1", "true", "yes"):
            qs = qs.exclude(
                estado__in=[OrdenEstudio.Estado.COMPLETADA, OrdenEstudio.Estado.ANULADA]
            )

        fd = p.get("fecha_desde")
        fh = p.get("fecha_hasta")
        if fd:
            d = parse_date(fd)
            if d:
                qs = qs.filter(fecha_solicitud__date__gte=d)
            else:
                dt = parse_datetime(fd)
                if dt:
                    qs = qs.filter(fecha_solicitud__gte=dt)
        if fh:
            d = parse_date(fh)
            if d:
                qs = qs.filter(fecha_solicitud__date__lte=d)
            else:
                dt = parse_datetime(fh)
                if dt:
                    qs = qs.filter(fecha_solicitud__lte=dt)

        if es_medico(self.request.user) and not es_admin_o_super(self.request.user):
            try:
                perfil = self.request.user.perfil_personal_salud
                qs = qs.filter(medico_solicitante_id=perfil.pk)
            except Exception:
                qs = qs.none()

        return qs.order_by("-urgente", "-fecha_solicitud")

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        orden = ser.save()
        out = OrdenEstudioCreateResponseSerializer(orden, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        instance.esta_activa = False
        instance.save(update_fields=["esta_activa"])

    @action(detail=False, methods=["get"], url_path="cola-laboratorio")
    def cola_laboratorio(self, request):
        pendientes = OrdenEstudio.objects.filter(esta_activa=True).exclude(
            estado__in=[OrdenEstudio.Estado.COMPLETADA, OrdenEstudio.Estado.ANULADA]
        ).select_related(
            "consulta__ficha__paciente",
            "medico_solicitante__user",
            "tecnico_responsable__user",
        )
        ordenadas = pendientes.order_by("-urgente", "fecha_solicitud")
        urgentes = ordenadas.filter(urgente=True)
        normales = ordenadas.filter(urgente=False)
        en_proceso = pendientes.filter(estado=OrdenEstudio.Estado.EN_PROCESO).order_by(
            "-urgente", "fecha_solicitud"
        )

        ls = OrdenEstudioListSerializer
        return Response(
            {
                "urgentes": ls(urgentes, many=True).data,
                "normales": ls(normales, many=True).data,
                "en_proceso": ls(en_proceso, many=True).data,
                "total_pendientes": pendientes.count(),
            }
        )

    @action(detail=True, methods=["patch"], url_path="cambiar-estado")
    def cambiar_estado(self, request, pk=None):
        orden = self.get_object()
        ser = OrdenEstudioCambiarEstadoSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        nuevo = ser.validated_data["estado"]
        orden.estado = nuevo
        tec_manual = ser.validated_data.get("tecnico_responsable_id")
        if nuevo == OrdenEstudio.Estado.EN_PROCESO:
            if tec_manual is not None:
                orden.tecnico_responsable = tec_manual
            else:
                try:
                    orden.tecnico_responsable = personal_desde_usuario(request.user)
                except Exception:
                    pass
        elif tec_manual is not None:
            orden.tecnico_responsable = tec_manual
        if "resultado_texto" in ser.validated_data:
            orden.resultado_texto = ser.validated_data.get("resultado_texto") or orden.resultado_texto
        if "resultado_archivo" in ser.validated_data and ser.validated_data["resultado_archivo"]:
            orden.resultado_archivo = ser.validated_data["resultado_archivo"]
        orden.save()
        return Response(OrdenEstudioDetailSerializer(orden).data, status=status.HTTP_200_OK)
