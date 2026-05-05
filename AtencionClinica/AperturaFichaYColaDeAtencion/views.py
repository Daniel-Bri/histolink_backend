# CU6 — API REST fichas de atención

from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Ficha
from .serializers import FichaEstadoSerializer, FichaSerializer


class FichaViewSet(viewsets.ModelViewSet):
    """
    ViewSet con CRUD sobre Ficha.

    DELETE realiza borrado lógico (esta_activa=False).

    Extra: PATCH `/api/fichas/{pk}/cambiar-estado/`
    """

    permission_classes = [IsAuthenticated]

    serializer_class = FichaSerializer
    queryset = Ficha.objects.select_related(
        "paciente",
        "profesional_apertura",
        "profesional_apertura__user",
    )

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params

        if p.get("incluir_inactivas", "").lower() not in ("1", "true", "yes"):
            qs = qs.filter(esta_activa=True)

        est = p.get("estado")
        if est:
            qs = qs.filter(estado=est.upper())

        pid = p.get("paciente")
        if pid:
            qs = qs.filter(paciente_id=pid)

        if p.get("en_curso", "").lower() in ("1", "true", "yes"):
            qs = qs.filter(
                estado__in=[
                    Ficha.Estado.ABIERTA,
                    Ficha.Estado.EN_TRIAJE,
                    Ficha.Estado.EN_ATENCION,
                ]
            )

        fd = p.get("fecha_desde")
        fh = p.get("fecha_hasta")
        if fd:
            d = parse_date(fd)
            if d:
                qs = qs.filter(fecha_apertura__date__gte=d)
            else:
                dt = parse_datetime(fd)
                if dt:
                    qs = qs.filter(fecha_apertura__gte=dt)
        if fh:
            d = parse_date(fh)
            if d:
                qs = qs.filter(fecha_apertura__date__lte=d)
            else:
                dt = parse_datetime(fh)
                if dt:
                    qs = qs.filter(fecha_apertura__lte=dt)

        return qs.order_by("-fecha_apertura")

    def perform_destroy(self, instance: Ficha):
        """Borrado lógico opcional."""
        instance.esta_activa = False
        instance.save(update_fields=("esta_activa",))

    @action(detail=True, methods=["patch"], url_path="cambiar-estado")
    def cambiar_estado(self, request, pk=None):
        qs = (
            Ficha.objects.select_related(
                "paciente",
                "profesional_apertura",
                "profesional_apertura__user",
            )
            .filter(pk=pk)
        )
        if self.request.query_params.get("incluir_inactivas", "").lower() not in ("1", "true", "yes"):
            qs = qs.filter(esta_activa=True)
        ficha = get_object_or_404(qs)
        ser = FichaEstadoSerializer(ficha, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ficha.estado = ser.validated_data["estado"]
        ficha.full_clean()
        ficha.save()
        return Response(FichaSerializer(ficha).data, status=status.HTTP_200_OK)
