<<<<<<< HEAD
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
    timestamp_bloque = models.CharField(max_length=50, blank=True, default='')

    class Meta:
        default_permissions = ('add', 'view')
        ordering = ['numero_bloque']

    def __str__(self):
        return f"Bloque #{self.numero_bloque} — {self.tipo_evento} ({self.documento_tipo} {self.documento_id})"
=======
from __future__ import annotations

import hashlib
import json
from django.db import models
from django.utils import timezone


class EventoBlockchain(models.Model):
    """
    Registro mínimo de eventos "anclados" para trazabilidad.
    No depende de infraestructura blockchain externa para funcionar.
    """

    tipo_evento = models.CharField(max_length=80, db_index=True)
    payload = models.JSONField(default=dict)
    tenant_id = models.IntegerField(null=True, blank=True, db_index=True)
    hash_previo = models.CharField(max_length=64, blank=True, default="")
    hash_actual = models.CharField(max_length=64, db_index=True)
    creado_en = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-creado_en"]
        verbose_name = "Evento Blockchain"
        verbose_name_plural = "Eventos Blockchain"

    def __str__(self) -> str:
        return f"{self.tipo_evento} @ {self.creado_en:%Y-%m-%d %H:%M:%S}"

    @classmethod
    def crear_evento(
        cls,
        *,
        tipo_evento: str,
        payload: dict,
        tenant_id: int | None = None,
    ) -> "EventoBlockchain":
        ultimo = cls.objects.order_by("-id").first()
        hash_previo = ultimo.hash_actual if ultimo else ""
        cuerpo = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        base = f"{tipo_evento}|{tenant_id or ''}|{hash_previo}|{cuerpo}|{timezone.now().isoformat()}"
        hash_actual = hashlib.sha256(base.encode("utf-8")).hexdigest()
        return cls.objects.create(
            tipo_evento=tipo_evento,
            payload=payload,
            tenant_id=tenant_id,
            hash_previo=hash_previo,
            hash_actual=hash_actual,
        )
>>>>>>> origin/alejandra
