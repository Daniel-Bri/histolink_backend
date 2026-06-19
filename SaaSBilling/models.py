from decimal import Decimal
from django.db import models


class SuscripcionTenant(models.Model):
    class Estado(models.TextChoices):
        ACTIVA     = 'ACTIVA',     'Activa'
        PENDIENTE  = 'PENDIENTE',  'Pendiente de pago'
        EXPIRADA   = 'EXPIRADA',   'Expirada'
        SUSPENDIDA = 'SUSPENDIDA', 'Suspendida'

    class Plan(models.TextChoices):
        BASICO      = 'BASICO',      'Básico'
        PROFESIONAL = 'PROFESIONAL', 'Profesional'
        ENTERPRISE  = 'ENTERPRISE',  'Enterprise'

    tenant = models.OneToOneField(
        'Tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='suscripcion',
    )
    plan              = models.CharField(max_length=20, choices=Plan.choices, default=Plan.BASICO)
    estado            = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    monto_mensual     = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('50.00'))
    fecha_inicio      = models.DateField(null=True, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    stripe_session_id = models.CharField(max_length=200, blank=True, default='')
    fecha_ultimo_pago = models.DateTimeField(null=True, blank=True)
    creado_en         = models.DateTimeField(auto_now_add=True)
    actualizado_en    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Suscripción'
        verbose_name_plural = 'Suscripciones'
        ordering            = ['tenant__nombre']

    def __str__(self):
        return f'{self.tenant.nombre} — {self.plan} ({self.estado})'
