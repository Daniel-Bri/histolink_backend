from django.conf import settings
from django.db import models


class DispositivoFCM(models.Model):
    PLATAFORMA_CHOICES = [
        ("web",     "Web"),
        ("android", "Android"),
        ("ios",     "iOS"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dispositivos_fcm",
        verbose_name="Usuario",
    )
    tenant = models.ForeignKey(
        "Tenants.Tenant",
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="dispositivos_fcm",
        verbose_name="Tenant",
    )
    token = models.TextField(verbose_name="FCM Token", unique=True)
    plataforma = models.CharField(
        max_length=10,
        choices=PLATAFORMA_CHOICES,
        default="web",
        verbose_name="Plataforma",
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")

    class Meta:
        verbose_name = "Dispositivo FCM"
        verbose_name_plural = "Dispositivos FCM"
        indexes = [
            models.Index(fields=["user", "plataforma"], name="idx_fcm_user_plat"),
            models.Index(fields=["tenant"], name="idx_fcm_tenant"),
        ]

    def __str__(self):
        return f"{self.user.username} [{self.plataforma}]"
