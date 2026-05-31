from rest_framework.permissions import BasePermission


class PuedeModificarConsulta(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if not request.user.is_authenticated:
            return False
        if not request.user.groups.filter(name='Médico').exists():
            return False
        if obj.medico_id != request.user.id:
            return False
        accion = getattr(view, 'action', None)
        if accion == 'firmar':
            return obj.estado == 'COMPLETADA'
        return obj.estado == 'BORRADOR'
