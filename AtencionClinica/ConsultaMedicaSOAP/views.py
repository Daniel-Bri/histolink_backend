# CU8 - Consulta Médica SOAP

from django.utils.dateparse import parse_date
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from GestionDeUsuarios.LoginYAutenticacion.permissions import EsMedico
from .models import Consulta
from .permissions import PuedeModificarConsulta
from .serializers import ConsultaSerializer


class ConsultaViewSet(viewsets.ModelViewSet):
    serializer_class = ConsultaSerializer

    def get_queryset(self):
        qs = Consulta.objects.select_related('paciente', 'medico', 'firmada_por').order_by('-creado_en')

        user = self.request.user
        if not user.is_authenticated:
            return qs.none()

        if user.is_superuser or user.groups.filter(name__in=['Administrativo', 'Director']).exists():
            return self._apply_filters(qs)

        if user.groups.filter(name='Médico').exists():
            return self._apply_filters(qs.filter(medico=user))

        return qs.none()

    def _apply_filters(self, qs):
        params = self.request.query_params

        paciente_id = params.get('paciente')
        if paciente_id:
            qs = qs.filter(paciente_id=paciente_id)

        estado = params.get('estado')
        if estado:
            qs = qs.filter(estado=estado)

        cie10 = params.get('cie10')
        if cie10:
            qs = qs.filter(codigo_cie10_principal__iexact=cie10.strip().upper())

        desde = parse_date(params.get('desde') or '')
        if desde:
            qs = qs.filter(creado_en__date__gte=desde)

        hasta = parse_date(params.get('hasta') or '')
        if hasta:
            qs = qs.filter(creado_en__date__lte=hasta)

        return qs

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]

        if self.action in ['create', 'update', 'partial_update', 'destroy', 'completar']:
            return [EsMedico(), PuedeModificarConsulta()]

        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant, medico=self.request.user)

    def perform_update(self, serializer):
        consulta = self.get_object()
        if consulta.estado == 'FIRMADA':
            raise permissions.PermissionDenied('No se puede modificar una consulta FIRMADA.')
        serializer.save()

    @action(detail=True, methods=['patch'])
    def completar(self, request, pk=None):
        consulta = self.get_object()

        if consulta.estado != 'BORRADOR':
            return Response(
                {'error': 'Solo se puede completar una consulta en estado BORRADOR.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        campos_obligatorios = {
            'motivo_consulta': consulta.motivo_consulta,
            'historia_enfermedad_actual': consulta.historia_enfermedad_actual,
            'impresion_diagnostica': consulta.impresion_diagnostica,
            'codigo_cie10_principal': consulta.codigo_cie10_principal,
        }
        faltantes = [k for k, v in campos_obligatorios.items() if not (v or '').strip()]
        if faltantes:
            return Response(
                {'error': 'Faltan campos obligatorios para completar la consulta.', 'campos': faltantes},
                status=status.HTTP_400_BAD_REQUEST,
            )

        consulta.estado = 'COMPLETADA'
        consulta.save(update_fields=['estado', 'actualizado_en'])
        return Response(ConsultaSerializer(consulta, context={'request': request}).data)
