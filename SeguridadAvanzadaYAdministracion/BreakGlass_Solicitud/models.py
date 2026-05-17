from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class BreakGlassSolicitud(models.Model):
    class NivelUrgencia(models.TextChoices):
        ALTA = "ALTA", "Alta"
        MEDIA = "MEDIA", "Media"
        BAJA = "BAJA", "Baja"

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        APROBADA = "APROBADA", "Aprobada"
        RECHAZADA = "RECHAZADA", "Rechazada"
        EXPIRADA = "EXPIRADA", "Expirada"

    tenant = models.ForeignKey(
        "Tenants.Tenant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="break_glass_solicitudes",
    )
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="break_glass_solicitudes",
    )
    paciente = models.ForeignKey(
        "RegistroYBusquedaDePacientes.Paciente",
        on_delete=models.PROTECT,
        related_name="break_glass_solicitudes",
    )
    justificacion = models.TextField()
    nivel_urgencia = models.CharField(max_length=10, choices=NivelUrgencia.choices)
    estado = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        db_index=True,
    )
    aprobado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="break_glass_aprobaciones",
    )
    acceso_desde = models.DateTimeField(null=True, blank=True)
    acceso_hasta = models.DateTimeField(null=True, blank=True)
    evento_blockchain = models.ForeignKey(
        "GestionDeIdentidadBlockchain.EventoBlockchain",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="break_glass_solicitudes",
    )
    creado_en = models.DateTimeField(auto_now_add=True, db_index=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado_en"]
        verbose_name = "Solicitud Break-Glass"
        verbose_name_plural = "Solicitudes Break-Glass"
        indexes = [
            models.Index(fields=["solicitante", "paciente", "estado"], name="bg_sol_pac_est_idx"),
            models.Index(fields=["acceso_hasta"], name="bg_acc_hasta_idx"),
        ]

    def __str__(self) -> str:
        return f"BG#{self.id or 'new'} {self.solicitante_id}->{self.paciente_id} {self.estado}"

    @property
    def acceso_activo(self) -> bool:
        now = timezone.now()
        return bool(
            self.acceso_desde
            and self.acceso_hasta
            and self.acceso_desde <= now <= self.acceso_hasta
            and self.estado in {self.Estado.PENDIENTE, self.Estado.APROBADA}
        )

    @property
    def acceso_expirado(self) -> bool:
        return bool(self.acceso_hasta and self.acceso_hasta < timezone.now())

    def aplicar_urgencia_alta_si_corresponde(self) -> None:
        if self.nivel_urgencia == self.NivelUrgencia.ALTA and not self.acceso_desde:
            now = timezone.now()
            self.acceso_desde = now
            self.acceso_hasta = now + timedelta(hours=2)
            self.estado = self.Estado.PENDIENTE

    def clean(self):
        super().clean()
        just = (self.justificacion or "").strip()
        if len(just) < 20:
            raise ValidationError({"justificacion": "La justificación debe tener al menos 20 caracteres."})

        if self.aprobado_por_id and self.aprobado_por_id == self.solicitante_id:
            raise ValidationError("Un médico no puede aprobar su propia solicitud Break-Glass")

        conflicto = BreakGlassSolicitud.objects.filter(
            solicitante_id=self.solicitante_id,
            paciente_id=self.paciente_id,
        ).exclude(pk=self.pk).filter(
            Q(estado=self.Estado.PENDIENTE) |
            Q(acceso_hasta__gt=timezone.now(), acceso_desde__isnull=False)
        )
        if conflicto.exists():
            raise ValidationError(
                "Ya existe una solicitud pendiente o con acceso activo para este paciente."
            )

    def save(self, *args, **kwargs):
        self.aplicar_urgencia_alta_si_corresponde()
        self.full_clean()
        super().save(*args, **kwargs)
