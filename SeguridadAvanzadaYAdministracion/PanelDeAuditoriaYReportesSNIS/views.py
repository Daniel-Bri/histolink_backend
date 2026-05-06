# CU20 - Panel de Auditoría y Reportes SNIS

from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .models import RegistroAuditoria
from .serializers import RegistroAuditoriaSerializer


class RegistroAuditoriaListView(generics.ListAPIView):
    """
    GET /api/auditoria/
    Filtros: ?usuario=&accion=&recurso=&fecha_inicio=&fecha_fin=
    Solo accesible por Auditor, Director o superuser.
    """
    serializer_class = RegistroAuditoriaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not (
            user.is_superuser or
            user.groups.filter(name__in=['Auditor', 'Director']).exists()
        ):
            raise PermissionDenied('Solo Auditor o Director pueden ver la auditoría.')

        qs = RegistroAuditoria.objects.all()
        params = self.request.query_params

        usuario = params.get('usuario')
        if usuario:
            qs = qs.filter(username__icontains=usuario)

        accion = params.get('accion')
        if accion:
            qs = qs.filter(metodo=accion.upper())

        recurso = params.get('recurso')
        if recurso:
            qs = qs.filter(path__icontains=recurso)

        fecha_inicio = params.get('fecha_inicio')
        if fecha_inicio:
            qs = qs.filter(creado_en__date__gte=fecha_inicio)

        fecha_fin = params.get('fecha_fin')
        if fecha_fin:
            qs = qs.filter(creado_en__date__lte=fecha_fin)

        return qs
