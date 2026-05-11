# CU20 - Panel de Auditoría y Reportes SNIS

from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination

from .models import RegistroAuditoria
from .serializers import RegistroAuditoriaSerializer

_ROLES_PERMITIDOS = {'Auditor', 'Director', 'Administrativo'}

_ACCION_TO_METODOS = {
    'CREAR':      ['POST'],
    'ACTUALIZAR': ['PUT', 'PATCH'],
    'ELIMINAR':   ['DELETE'],
}

_MODULO_TO_PREFIXES = {
    'PACIENTES':       ['/api/pacientes'],
    'USUARIOS':        ['/api/auth', '/api/personal'],
    'ATENCION_CLINICA': ['/api/triaje', '/api/consultas', '/api/clinica', '/api/ordenes'],
    'APERTURA_FICHA':  ['/api/fichas'],
    'REPORTES':        ['/api/reportes', '/api/auditoria'],
    'CONFIGURACION':   ['/api/admin/backup', '/api/tenants'],
}

_ORDERING_MAP = {
    '-timestamp':        '-creado_en',
    'timestamp':         'creado_en',
    '-usuario_username': '-username',
    'usuario_username':  'username',
}


class AuditoriaPagination(PageNumberPagination):
    page_size            = 20
    page_size_query_param = 'page_size'
    max_page_size        = 200


class RegistroAuditoriaListView(generics.ListAPIView):
    """
    GET /api/auditoria/
    Filtros: ?usuario=&accion=&modulo=&fecha_desde=&fecha_hasta=&ordering=
    Roles permitidos: Auditor, Director, Administrativo, superadmin.
    """
    serializer_class  = RegistroAuditoriaSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class  = AuditoriaPagination

    def get_queryset(self):
        user = self.request.user
        grupos = set(user.groups.values_list('name', flat=True))
        if not (user.is_superuser or grupos & _ROLES_PERMITIDOS):
            raise PermissionDenied('Solo Auditor, Director o Administrativo pueden ver la auditoría.')

        qs     = RegistroAuditoria.objects.all()
        params = self.request.query_params

        usuario = params.get('usuario')
        if usuario:
            qs = qs.filter(username__icontains=usuario)

        accion = params.get('accion', '').upper()
        if accion in _ACCION_TO_METODOS:
            qs = qs.filter(metodo__in=_ACCION_TO_METODOS[accion])

        modulo = params.get('modulo', '').upper()
        if modulo in _MODULO_TO_PREFIXES:
            q = Q()
            for p in _MODULO_TO_PREFIXES[modulo]:
                q |= Q(path__startswith=p)
            qs = qs.filter(q)

        fecha_desde = params.get('fecha_desde')
        if fecha_desde:
            qs = qs.filter(creado_en__gte=fecha_desde)

        fecha_hasta = params.get('fecha_hasta')
        if fecha_hasta:
            qs = qs.filter(creado_en__lte=fecha_hasta)

        ordering_param = params.get('ordering', '-creado_en')
        ordering = _ORDERING_MAP.get(ordering_param, ordering_param)
        safe_fields = {'creado_en', '-creado_en', 'username', '-username'}
        if ordering not in safe_fields:
            ordering = '-creado_en'
        qs = qs.order_by(ordering)

        return qs
