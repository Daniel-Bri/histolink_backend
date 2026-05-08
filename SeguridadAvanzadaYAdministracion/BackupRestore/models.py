from django.db import models
from django.utils import timezone


class GestionAnual(models.Model):
    """
    Representa una gestión anual (ejercicio) de un tenant.
    Permite congelar el acceso de escritura a los datos de un año específico.
    """

    tenant = models.ForeignKey(
        'Tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='gestiones',
        verbose_name='Establecimiento',
    )
    año = models.PositiveIntegerField(verbose_name='Año')
    congelada = models.BooleanField(
        default=False,
        verbose_name='Congelada',
        help_text='Si está congelada, los datos de este año son de solo lectura.',
    )
    fecha_congelamiento = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Fecha de congelamiento',
    )
    descripcion = models.CharField(
        max_length=200, blank=True, default='',
        verbose_name='Descripción',
        help_text='Nota opcional sobre esta gestión.',
    )
    creado_en     = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together     = ('tenant', 'año')
        ordering            = ['-año']
        verbose_name        = 'Gestión anual'
        verbose_name_plural = 'Gestiones anuales'

    def __str__(self):
        estado = 'Congelada' if self.congelada else 'Activa'
        return f"Gestión {self.año} — {self.tenant.nombre} ({estado})"

    def congelar(self):
        if not self.congelada:
            self.congelada          = True
            self.fecha_congelamiento = timezone.now()
            self.save(update_fields=['congelada', 'fecha_congelamiento', 'actualizado_en'])

    def descongelar(self):
        if self.congelada:
            self.congelada          = False
            self.fecha_congelamiento = None
            self.save(update_fields=['congelada', 'fecha_congelamiento', 'actualizado_en'])
