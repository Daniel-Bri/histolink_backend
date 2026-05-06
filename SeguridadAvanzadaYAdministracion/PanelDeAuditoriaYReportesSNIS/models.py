# CU20 - Panel de Auditoría y Reportes SNIS

from django.conf import settings
from django.db import models


class RegistroAuditoria(models.Model):
    """
    Registro de auditoría de operaciones de escritura en el sistema.
    Se crea automáticamente por el middleware de auditoría.
    """

    METODO_CHOICES = [
        ("POST",   "POST"),
        ("PUT",    "PUT"),
        ("PATCH",  "PATCH"),
        ("DELETE", "DELETE"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="registros_auditoria",
        verbose_name="Usuario",
    )
    username = models.CharField(
        max_length=150,
        verbose_name="Username",
        help_text="Username en el momento de la acción, guardado por si el usuario se elimina.",
    )
    metodo = models.CharField(
        max_length=10,
        choices=METODO_CHOICES,
        verbose_name="Método HTTP",
    )
    path = models.CharField(
        max_length=500,
        verbose_name="Ruta",
        db_index=True,
    )
    status_code = models.PositiveSmallIntegerField(
        verbose_name="Código de respuesta",
    )
    duracion_ms = models.FloatField(
        verbose_name="Duración (ms)",
    )
    body = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Body del request",
    )
    ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        verbose_name="Dirección IP",
    )
    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y hora",
        db_index=True,
    )

    class Meta:
        verbose_name        = "Registro de Auditoría"
        verbose_name_plural = "Registros de Auditoría"
        ordering            = ["-creado_en"]
        indexes = [
            models.Index(fields=["username", "creado_en"], name="idx_auditoria_user_fecha"),
            models.Index(fields=["metodo", "creado_en"],   name="idx_auditoria_metodo_fecha"),
        ]

    def __str__(self):
        return f"[{self.creado_en:%Y-%m-%d %H:%M}] {self.username} {self.metodo} {self.path} → {self.status_code}"