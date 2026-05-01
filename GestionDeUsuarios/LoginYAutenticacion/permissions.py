"""
Clases de permisos personalizadas para Histolink.
Verifican la pertenencia a grupos específicos del sistema.
"""

from rest_framework.permissions import BasePermission


class EsMedico(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.groups.filter(name='Médico').exists()
        )


class EsEnfermera(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.groups.filter(name='Enfermera').exists()
        )


class EsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.groups.filter(name='Administrativo').exists()
        )


class EsPaciente(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.groups.filter(name='Paciente').exists()
        )


class EsFarmacia(BasePermission):
    """Permite acceso solo a usuarios del grupo 'Farmacia'."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.groups.filter(name='Farmacia').exists()
        )


class EsAdminODirector(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            (
                request.user.is_superuser or
                request.user.groups.filter(name__in=['Administrativo', 'Director']).exists()
            )
        )


class EsMedicoOEnfermera(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.groups.filter(name__in=['Médico', 'Enfermera']).exists()
        )


class EsMedicoEnfermeroOAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.groups.filter(name__in=['Médico', 'Enfermera', 'Administrativo']).exists()
        )
