# CU8 - Consulta Médica SOAP
import hashlib
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from GestionDeUsuarios.LoginYAutenticacion.permissions import EsMedico
from SeguridadAvanzadaYAdministracion.Auditoria.audit_utils import registrar_evento
from .models import Consulta
from .permissions import PuedeModificarConsulta
from .serializers import ConsultaSerializer


class ConsultaViewSet(viewsets.ModelViewSet):
    serializer_class = ConsultaSerializer

    def get_queryset(self):
        qs = Consulta.objects.select_related(
            'tenant',
            'ficha',
            'ficha__paciente',
            'medico',
            'triaje',
            'firmada_por',
        ).order_by('-creado_en')
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
            qs = qs.filter(ficha__paciente_id=paciente_id)
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
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'completar', 'firmar']:
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
        
        # Auditoría manual para acción clínica
        registrar_evento('COMPLETAR', consulta, request=request)
        
        return Response(ConsultaSerializer(consulta, context={'request': request}).data)

    @action(detail=True, methods=['patch'])
    def firmar(self, request, pk=None):
        consulta = self.get_object()

        # Solo se puede firmar una consulta COMPLETADA
        if consulta.estado != 'COMPLETADA':
            return Response(
                {'error': f'Solo se puede firmar una consulta COMPLETADA. Estado actual: {consulta.estado}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generar SHA-256 del contenido de la consulta
        contenido = (
            f"{consulta.id}"
            f"{consulta.motivo_consulta}"
            f"{consulta.historia_enfermedad_actual}"
            f"{consulta.examen_fisico}"
            f"{consulta.impresion_diagnostica}"
            f"{consulta.codigo_cie10_principal}"
            f"{consulta.plan_tratamiento}"
            f"{consulta.creado_en.isoformat()}"
        )
        hash_sha256 = hashlib.sha256(contenido.encode('utf-8')).hexdigest()

        # Transición COMPLETADA → FIRMADA
        consulta.estado = 'FIRMADA'
        consulta.hash_documento = hash_sha256
        consulta.firmada_por = request.user
        consulta.firmada_en = timezone.now()
        consulta.save(update_fields=[
            'estado', 'hash_documento', 'firmada_por', 'firmada_en', 'actualizado_en'
        ])

        return Response(ConsultaSerializer(consulta, context={'request': request}).data)