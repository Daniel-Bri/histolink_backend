from django.contrib.auth.models import AnonymousUser
from rest_framework.permissions import BasePermission, SAFE_METHODS

GROUP_ADMIN_LIKE  = frozenset({"Administrativo", "Director"})
GROUP_CLINICO     = frozenset({"Médico", "Enfermera", "Laboratorio", "Farmacia", "Auditor"})
GROUP_PUEDE_LEER  = GROUP_ADMIN_LIKE | GROUP_CLINICO


def _groups(user) -> set[str]:
    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        return set()
    return set(user.groups.values_list("name", flat=True))


def es_admin_o_super(user) -> bool:
    return bool(getattr(user, "is_superuser", False)) or bool(_groups(user) & GROUP_ADMIN_LIKE)


class FichaPermission(BasePermission):
    """
    Lectura (GET/HEAD/OPTIONS): cualquier rol clínico autenticado.
    Escritura (POST/PATCH/PUT/DELETE) y cambiar-estado: solo Administrativo, Director o superusuario.
    """

    def has_permission(self, request, view):
        user = request.user
        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            return False
        grupos = _groups(user)
        if request.method in SAFE_METHODS:
            return bool(grupos & GROUP_PUEDE_LEER) or bool(getattr(user, "is_superuser", False))
        # cambiar-estado también lo pueden hacer Médico/Enfermera (lo llama el triaje)
        if view.action == "cambiar_estado":
            return bool(grupos & GROUP_PUEDE_LEER) or bool(getattr(user, "is_superuser", False))
        return es_admin_o_super(user)
