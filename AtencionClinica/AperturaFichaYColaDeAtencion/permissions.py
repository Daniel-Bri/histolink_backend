from django.contrib.auth.models import AnonymousUser
from rest_framework.permissions import BasePermission

GROUP_ADMIN_LIKE = frozenset({"Administrativo", "Director"})


def _groups(user) -> set[str]:
    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        return set()
    return set(user.groups.values_list("name", flat=True))


def es_admin_o_super(user) -> bool:
    return bool(getattr(user, "is_superuser", False)) or bool(_groups(user) & GROUP_ADMIN_LIKE)


class FichaPermission(BasePermission):
    """
    Restringe CU6 al actor de apertura de ficha:
    Administrativo / Director (y superusuario).
    """

    def has_permission(self, request, view):
        return es_admin_o_super(request.user)
