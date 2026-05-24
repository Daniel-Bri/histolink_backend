from django.db import models
from django.conf import settings
from Tenants.models import Tenant


class IdentidadBlockchain(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='identidades_blockchain')
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='identidad_blockchain')
    clave_publica_pem = models.TextField()
    clave_privada_pem = models.TextField()
    did_simulado = models.CharField(max_length=100)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.did_simulado} — {self.usuario.get_full_name()}"


class EventoBlockchain(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='eventos_blockchain')
    numero_bloque = models.PositiveIntegerField()
    anterior_hash = models.CharField(max_length=64)
    tipo_evento = models.CharField(max_length=50)
    documento_tipo = models.CharField(max_length=50)
    documento_id = models.PositiveIntegerField()
    hash_documento = models.CharField(max_length=64)
    firma_rsa = models.TextField()
    firmado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='eventos_blockchain')
    timestamp = models.DateTimeField(auto_now_add=True)
    bloque_hash = models.CharField(max_length=64)

    class Meta:
        default_permissions = ('add', 'view')
        ordering = ['numero_bloque']

    def __str__(self):
        return f"Bloque #{self.numero_bloque} — {self.tipo_evento} ({self.documento_tipo} {self.documento_id})"
