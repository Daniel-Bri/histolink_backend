# Permisos por rol para órdenes de estudio (T009)

from django.contrib.auth.models import AnonymousUser
from rest_framework.permissions import BasePermission

GROUP_MEDICO = "Médico"
GROUP_LAB = "Laboratorio"
GROUP_ENFERMERA = "Enfermera"
GROUP_ADMIN_LIKE = frozenset({"Administrativo", "Director"})


def _groups(user) -> set[str]:
    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        return set()
    return set(user.groups.values_list("name", flat=True))


def es_admin_o_super(user) -> bool:
    return bool(getattr(user, "is_superuser", False)) or bool(_groups(user) & GROUP_ADMIN_LIKE)


def es_medico(user) -> bool:
    return GROUP_MEDICO in _groups(user)


def es_laboratorio(user) -> bool:
    return GROUP_LAB in _groups(user)


def es_enfermera(user) -> bool:
    return GROUP_ENFERMERA in _groups(user)


class OrdenEstudioPermission(BasePermission):
    """
    create → Médico o admin-like / super
    list/retrieve → Médico, Laboratorio, Enfermería, admin-like
    update → objeto: médico dueño (orden no terminal), laboratorio (campos acotados en vista), admin
    destroy → admin-like / super (borrado lógico)
    cola_laboratorio / cambiar_estado → Laboratorio o admin-like
    """

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if es_admin_o_super(user):
            return True
        action = getattr(view, "action", None)

        if action == "create":
            return es_medico(user)

        if action in ("list", "retrieve"):
            return es_medico(user) or es_laboratorio(user) or es_enfermera(user)

        if action == "destroy":
            return es_admin_o_super(user)

        if action in ("cola_laboratorio", "cambiar_estado"):
            return es_laboratorio(user)

        if action in ("update", "partial_update"):
            return es_medico(user)

        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        if es_admin_o_super(user):
            return True
        action = getattr(view, "action", None)

        if action in ("retrieve",):
            return es_medico(user) or es_laboratorio(user) or es_enfermera(user)

        if action in ("update", "partial_update"):
            terminal = obj.estado in (
                obj.__class__.Estado.COMPLETADA,
                obj.__class__.Estado.ANULADA,
            )
            if es_medico(user):
                if terminal:
                    return False
                perfil = getattr(user, "perfil_personal_salud", None)
                return perfil is not None and obj.medico_solicitante_id == perfil.pk
            return False

        if action == "destroy":
            return es_admin_o_super(user)

        if action == "cambiar_estado":
            return es_laboratorio(user) or es_admin_o_super(user)

        return False
