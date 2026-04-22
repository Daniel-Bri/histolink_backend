from django.db import models
from .context import get_current_tenant


class TenantManager(models.Manager):
    """
    Manager que filtra automáticamente por el tenant activo en el hilo actual.
    Si no hay tenant activo (superadmin, management commands), devuelve todos los registros.
    Usado como manager por defecto en todos los modelos clínicos con campo 'tenant'.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = get_current_tenant()
        if tenant is not None:
            return qs.filter(tenant=tenant)
        return qs
