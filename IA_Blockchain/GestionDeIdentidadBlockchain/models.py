import hashlib
import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
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

    @classmethod
    def crear_evento(
        cls,
        *,
        tipo_evento: str,
        payload: dict,
        tenant_id: int,
        documento_tipo: str = "BreakGlassSolicitud",
        documento_id: int | None = None,
        firmado_por=None,
    ):
        """
        Crea un evento de blockchain reutilizando la cadena simulada existente.
        Si no existe clave privada del firmante, usa una firma determinista
        basada en el contenido para no romper el flujo clínico demo.
        """
        from .service import agregar_evento_blockchain

        User = get_user_model()
        payload = payload or {}

        if firmado_por is None:
            usuario_id = (
                payload.get("aprobado_por")
                or payload.get("aprobado_por_id")
                or payload.get("solicitante_id")
                or payload.get("firmado_por_id")
            )
            if usuario_id is None:
                raise ValueError("Se requiere un firmante para registrar el evento de blockchain.")
            firmado_por = User.objects.get(id=usuario_id)

        if documento_id is None:
            documento_id = (
                payload.get("solicitud_id")
                or payload.get("id")
                or payload.get("documento_id")
            )
        if documento_id is None:
            raise ValueError("Se requiere documento_id o solicitud_id para registrar el evento de blockchain.")

        contenido = json.dumps(
            {
                "tipo_evento": tipo_evento,
                "documento_tipo": documento_tipo,
                "documento_id": documento_id,
                "datos_evento_hash": hashlib.sha256(
                    json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
                ).hexdigest(),
            },
            sort_keys=True,
            ensure_ascii=False,
            default=str,
        )

        identidad = getattr(firmado_por, "identidad_blockchain", None)
        clave_privada_pem = getattr(identidad, "clave_privada_pem", None)

        return agregar_evento_blockchain(
            tenant=Tenant.objects.get(id=tenant_id),
            tipo_evento=tipo_evento,
            documento_tipo=documento_tipo,
            documento_id=documento_id,
            hash_documento=hashlib.sha256(contenido.encode("utf-8")).hexdigest(),
            firmado_por=firmado_por,
            clave_privada_pem=clave_privada_pem,
        )
