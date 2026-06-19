from django.db import models
from Tenants.managers import TenantManager

class Cobro(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PAGADO = "PAGADO", "Pagado"
        ANULADO = "ANULADO", "Anulado"
        EXPIRADO = "EXPIRADO", "Expirado"

    tenant = models.ForeignKey(
        "Tenants.Tenant", on_delete=models.CASCADE, related_name="cobros"
    )

    objects = TenantManager()

    ficha = models.ForeignKey(
        "AperturaFichaYColaDeAtencion.Ficha", on_delete=models.PROTECT, related_name="cobros"
    )
    paciente = models.ForeignKey(
        "RegistroYBusquedaDePacientes.Paciente", on_delete=models.PROTECT, related_name="cobros"
    )
    concepto = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.PENDIENTE
    )
    stripe_session_id = models.CharField(max_length=255, null=True, blank=True)
    fecha_pago = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado_en"]

    def __str__(self):
        return f"Cobro #{self.id} - {self.concepto} - {self.estado}"