from django.conf import settings
from django.db import models
from Tenants.managers import TenantManager


class Especialidad(models.Model):
    tenant = models.ForeignKey(
        'Tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='especialidades',
        verbose_name='Establecimiento',
    )
    nombre = models.CharField(max_length=120)

    objects = TenantManager()

    class Meta:
        ordering = ["nombre"]
        unique_together = [("nombre", "tenant")]

    def __str__(self):
        return self.nombre


class PersonalSalud(models.Model):
    ROL_MEDICO = "medico"
    ROL_ENFERMERA = "enfermera"
    ROL_ADMIN = "admin"

    ROLES = [
        (ROL_MEDICO, "Medico"),
        (ROL_ENFERMERA, "Enfermera"),
        (ROL_ADMIN, "Admin"),
    ]

    tenant = models.ForeignKey(
        'Tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='personal_salud',
        verbose_name='Establecimiento',
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_personal_salud",
    )
    item_min_salud = models.CharField(max_length=20)
    rol = models.CharField(max_length=20, choices=ROLES)
    especialidad = models.ForeignKey(
        Especialidad,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="personal_salud",
    )
    telefono = models.CharField(max_length=30, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("item_min_salud", "tenant")]

    def __str__(self):
        return f"{self.user} - {self.item_min_salud}"
