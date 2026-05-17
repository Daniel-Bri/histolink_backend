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
