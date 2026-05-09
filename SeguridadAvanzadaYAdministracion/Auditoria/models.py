import hashlib
import json
from django.db import models


class RegistroAuditoria(models.Model):
    """
    Modelo para el registro de auditoría del sistema.
    Almacena información detallada sobre acciones realizadas por los usuarios.
    """
    ACCION_CHOICES = [
        ('CREATE',    'Creación'),
        ('UPDATE',    'Modificación'),
        ('DELETE',    'Eliminación'),
        ('FIRMAR',    'Firma digital'),
        ('COMPLETAR', 'Completar'),
        ('DISPENSAR', 'Dispensar'),
        ('ANULAR',    'Anular'),
        ('LOGIN',     'Inicio de sesión'),
        ('LOGOUT',    'Cierre de sesión'),
    ]

    accion = models.CharField(max_length=20, choices=ACCION_CHOICES, db_index=True)
    modelo = models.CharField(max_length=100, db_index=True)
    objeto_id = models.CharField(max_length=50, db_index=True)
    objeto_repr = models.CharField(max_length=200, blank=True)

    usuario_id = models.IntegerField(db_index=True)
    usuario_nombre = models.CharField(max_length=150)
    usuario_rol = models.CharField(max_length=50)

    tenant_id = models.IntegerField(null=True, blank=True, db_index=True)
    tenant_nombre = models.CharField(max_length=200, blank=True)

    cambios = models.JSONField(default=dict, blank=True)

    ip_origen = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    endpoint = models.CharField(max_length=500, blank=True)

    hash_evento = models.CharField(max_length=64, blank=True, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['modelo', 'objeto_id']),
            models.Index(fields=['usuario_id', 'timestamp']),
            models.Index(fields=['accion', 'timestamp']),
        ]
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Registros de Auditoría"

    def __str__(self):
        return f"{self.accion} - {self.modelo} ({self.objeto_id}) por {self.usuario_nombre}"

    def save(self, *args, **kwargs):
        if not self.hash_evento:
            self.hash_evento = self.calcular_hash_evento()
        super().save(*args, **kwargs)

    def calcular_hash_evento(self):
        """Calcula un hash SHA-256 para asegurar la integridad del registro."""
        data = f"{self.accion}{self.modelo}{self.objeto_id}{self.usuario_id}{self.timestamp}{json.dumps(self.cambios, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()
