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


# 🔹 Opcional (muy útil)
class EsAdminODirector(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            (
                request.user.groups.filter(name='Administrativo').exists() or
                request.user.groups.filter(name='Director').exists()
            )
        )