# CU16 - Configuración de Consentimiento de Emergencia

from django.db import models
from django.conf import settings
from django.utils import timezone
from Tenants.managers import TenantManager
from Tenants.models import Tenant
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente


class TipoConsentimiento(models.Model):
    """
    Define los tipos de consentimientos informados configurables por el establecimiento.
    Ejemplo: "Consentimiento quirúrgico", "Uso de datos".
    """
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE,
        related_name='tipos_consentimiento',
        verbose_name="Establecimiento"
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    descripcion = models.TextField(verbose_name="Descripción (Texto legal)")
    requiere_testigo = models.BooleanField(default=False, verbose_name="Requiere testigo")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

    objects = TenantManager()

    class Meta:
        unique_together = ['tenant', 'nombre']
        verbose_name = "Tipo de Consentimiento"
        verbose_name_plural = "Tipos de Consentimiento"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Consentimiento(models.Model):
    """
    Registro individual de un consentimiento otorgado, rechazado o revocado por un paciente.
    """
    class Estado(models.TextChoices):
        OTORGADO = 'OTORGADO', 'Otorgado'
        RECHAZADO = 'RECHAZADO', 'Rechazado'
        REVOCADO = 'REVOCADO', 'Revocado'

    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE,
        related_name='consentimientos',
        verbose_name="Establecimiento"
    )
    paciente = models.ForeignKey(
        Paciente, 
        on_delete=models.CASCADE, 
        related_name='consentimientos',
        verbose_name="Paciente"
    )
    tipo = models.ForeignKey(
        TipoConsentimiento, 
        on_delete=models.PROTECT,
        related_name='registros',
        verbose_name="Tipo de consentimiento"
    )
    estado = models.CharField(
        max_length=20, 
        choices=Estado.choices, 
        default=Estado.OTORGADO,
        verbose_name="Estado"
    )
    otorgado_en = models.DateTimeField(auto_now_add=True, verbose_name="Otorgado en")
    vigente_hasta = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Vigente hasta",
        help_text="Fecha de expiración. Dejar en blanco para vigencia indefinida."
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        verbose_name="Registrado por"
    )
    testigo_nombre = models.CharField(
        max_length=200, 
        blank=True, 
        default="",
        verbose_name="Nombre del testigo"
    )
    observaciones = models.TextField(blank=True, default="", verbose_name="Observaciones")

    objects = TenantManager()

    class Meta:
        ordering = ['-otorgado_en']
        verbose_name = "Consentimiento"
        verbose_name_plural = "Consentimientos"
        indexes = [
            models.Index(fields=['paciente', 'tipo', 'estado']),
            models.Index(fields=['otorgado_en']),
        ]

    def __str__(self):
        return f"{self.tipo.nombre} — {self.paciente} ({self.estado})"

    @property
    def es_vigente(self) -> bool:
        """Determina si el consentimiento sigue siendo válido."""
        if self.estado != self.Estado.OTORGADO:
            return False
        if self.vigente_hasta and self.vigente_hasta < timezone.now():
            return False
        return True
