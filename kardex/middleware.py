"""
kardex/middleware.py

Middleware de auditoría para Histolink.
Registra toda operación de escritura (POST, PATCH, PUT, DELETE) en BD
y en el log de auditoría.
"""

import json
import logging
import time

logger = logging.getLogger("histolink.auditoria")

_WRITE_METHODS = {"POST", "PATCH", "PUT", "DELETE"}

_CAMPOS_SENSIBLES = {"password", "password_confirm", "old_password", "new_password",
                     "new_password_confirm", "refresh", "access", "token"}


def _sanitizar_body(body_bytes: bytes) -> dict:
    if not body_bytes:
        return {}
    try:
        data = json.loads(body_bytes.decode("utf-8", errors="replace"))
        if isinstance(data, dict):
            return {k: ("***" if k in _CAMPOS_SENSIBLES else v) for k, v in data.items()}
        return data
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {"_raw": "<body no-JSON>"}


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class AuditoriaMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method not in _WRITE_METHODS:
            return self.get_response(request)

        body_bytes = request.body
        inicio = time.monotonic()

        response = self.get_response(request)

        duracion_ms = round((time.monotonic() - inicio) * 1000, 1)

        user = None
        username = "anon"
        if hasattr(request, "user") and request.user.is_authenticated:
            user = request.user
            username = request.user.username

        body = _sanitizar_body(body_bytes)

        # Guardar en BD
        try:
            from SeguridadAvanzadaYAdministracion.PanelDeAuditoriaYReportesSNIS.models import RegistroAuditoria
            RegistroAuditoria.objects.create(
                usuario=user,
                username=username,
                metodo=request.method,
                path=request.get_full_path(),
                status_code=response.status_code,
                duracion_ms=duracion_ms,
                body=body,
                ip_address=_get_client_ip(request),
            )
        except Exception as e:
            logger.warning(f"No se pudo guardar registro de auditoría: {e}")

        # Log en consola
        logger.info(
            "AUDITORIA",
            extra={
                "ts": time.time(),
                "duracion_ms": duracion_ms,
                "user": username,
                "method": request.method,
                "path": request.get_full_path(),
                "status": response.status_code,
                "body": body,
            },
        )

        return response