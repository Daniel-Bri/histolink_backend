from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from Tenants.managers import TenantManager


class PermisoPaciente(models.Model):
    paciente = models.ForeignKey(
        "RegistroYBusquedaDePacientes.Paciente",
        on_delete=models.CASCADE,
        related_name="permisos",
        verbose_name="Paciente",
    )
    medico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="permisos_recibidos",
        verbose_name="Médico",
    )
    otorgado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="permisos_otorgados",
        verbose_name="Otorgado por",
    )
    fecha_otorgamiento = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de otorgamiento")
    fecha_revocacion = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
        verbose_name="Fecha de revocación",
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    tenant = models.ForeignKey(
        "Tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="permisos_paciente",
        verbose_name="Establecimiento",
    )

    objects = TenantManager()

    class Meta:
        verbose_name = "Permiso de Paciente"
        verbose_name_plural = "Permisos de Pacientes"
        ordering = ["-fecha_otorgamiento"]
        constraints = [
            models.UniqueConstraint(
                fields=["paciente", "medico"],
                condition=models.Q(activo=True),
                name="unique_active_permiso_paciente_medico",
            )
        ]

    def __str__(self):
        estado = "Activo" if self.activo else "Inactivo"
        return f"Permiso Paciente: {self.paciente.ci} -> Médico: {self.medico.username} ({estado})"

    def clean(self):
        super().clean()
        if self.activo:
            # Validar que no haya otro permiso activo para el mismo paciente y médico
            qs = PermisoPaciente.objects.filter(
                paciente=self.paciente,
                medico=self.medico,
                activo=True
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("Ya existe un permiso activo para este paciente y médico.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def revocar(self):
        self.activo = False
        self.fecha_revocacion = timezone.now()
        self.save()

    def reactivar(self, otorgado_por=None):
        self.activo = True
        self.fecha_revocacion = None
        if otorgado_por:
            self.otorgado_por = otorgado_por
        self.save()
