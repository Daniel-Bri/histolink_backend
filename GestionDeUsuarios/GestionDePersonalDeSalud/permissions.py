from rest_framework.permissions import BasePermission

from .models import PersonalSalud


class IsStaffOrAdminRole(BasePermission):
    """
    Escritura permitida si is_staff=True o el perfil PersonalSalud tiene rol admin.
    """

    message = "Solo personal administrativo (staff o rol admin) puede realizar esta acción."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        perfil = getattr(user, "perfil_personal_salud", None)
        if perfil is not None and perfil.rol == PersonalSalud.ROL_ADMIN:
            return True
        return False
