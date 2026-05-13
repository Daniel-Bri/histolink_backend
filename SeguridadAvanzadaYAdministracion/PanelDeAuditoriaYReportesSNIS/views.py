# CU20 - Panel de Auditoría y Reportes SNIS

from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination

from SeguridadAvanzadaYAdministracion.Auditoria.models import RegistroAuditoria
from .serializers import RegistroAuditoriaSerializer

_ROLES_PERMITIDOS = {'Auditor', 'Director', 'Administrativo'}

# Mapeo frontend (CREAR/ACTUALIZAR/ELIMINAR/LOGIN/LOGOUT) → acciones reales del modelo
_FILTRO_ACCION = {
    'CREAR':      ['CREATE'],
    'ACTUALIZAR': ['UPDATE', 'FIRMAR', 'COMPLETAR', 'DISPENSAR'],
    'ELIMINAR':   ['DELETE', 'ANULAR'],
    'LOGIN':      ['LOGIN'],
    'LOGOUT':     ['LOGOUT'],
}

_FILTRO_MODULO_MODELOS = {
    'PACIENTES':       ['Paciente', 'Antecedente'],
    'USUARIOS':        ['User', 'PersonalSalud'],
    'ATENCION_CLINICA': ['Triaje', 'Consulta', 'RecetaMedica', 'OrdenEstudio'],
    'APERTURA_FICHA':  ['Ficha'],
}

_FILTRO_MODULO_PREFIXES = {
    'REPORTES':    ['/api/reportes', '/api/auditoria'],
    'CONFIGURACION': ['/api/admin', '/api/tenants'],
}


class AuditoriaPagination(PageNumberPagination):
    page_size             = 20
    page_size_query_param = 'page_size'
    max_page_size         = 200


class RegistroAuditoriaListView(generics.ListAPIView):
    """
    GET /api/auditoria/
    Filtros: ?usuario=&accion=&modulo=&fecha_desde=&fecha_hasta=&ordering=
    Roles: Auditor, Director, Administrativo, superadmin.
    """
    serializer_class   = RegistroAuditoriaSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class   = AuditoriaPagination

    def get_queryset(self):
        user   = self.request.user
        grupos = set(user.groups.values_list('name', flat=True))
        if not (user.is_superuser or grupos & _ROLES_PERMITIDOS):
            raise PermissionDenied('Solo Auditor, Director o Administrativo pueden ver la auditoría.')

        qs     = RegistroAuditoria.objects.all()
        params = self.request.query_params

        usuario = params.get('usuario')
        if usuario:
            qs = qs.filter(usuario_nombre__icontains=usuario)

        accion = params.get('accion', '').upper()
        if accion in _FILTRO_ACCION:
            qs = qs.filter(accion__in=_FILTRO_ACCION[accion])

        modulo = params.get('modulo', '').upper()
        if modulo in _FILTRO_MODULO_MODELOS:
            qs = qs.filter(modelo__in=_FILTRO_MODULO_MODELOS[modulo])
        elif modulo in _FILTRO_MODULO_PREFIXES:
            q = Q()
            for p in _FILTRO_MODULO_PREFIXES[modulo]:
                q |= Q(endpoint__startswith=p)
            qs = qs.filter(q)

        fecha_desde = params.get('fecha_desde')
        if fecha_desde:
            qs = qs.filter(timestamp__gte=fecha_desde)

        fecha_hasta = params.get('fecha_hasta')
        if fecha_hasta:
            qs = qs.filter(timestamp__lte=fecha_hasta)

        ordering_param = params.get('ordering', '-timestamp')
        safe = {'-timestamp', 'timestamp', '-usuario_nombre', 'usuario_nombre'}
        ordering = ordering_param if ordering_param in safe else '-timestamp'
        qs = qs.order_by(ordering)

        return qs
