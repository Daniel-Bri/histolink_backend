"""
kardex/middleware.py

Middleware de auditoría para Histolink.
Registra toda operación de escritura (POST, PATCH, PUT, DELETE) en el log
de auditoría con: timestamp, usuario, método, path, status HTTP y body.

Configurar en settings.MIDDLEWARE y settings.LOGGING.
"""

import json
import logging
import time

logger = logging.getLogger("histolink.auditoria")

# Métodos que modifican estado — los únicos que se auditan
_WRITE_METHODS = {"POST", "PATCH", "PUT", "DELETE"}

# Campos que nunca se loguean aunque lleguen en el body
_CAMPOS_SENSIBLES = {"password", "password_confirm", "old_password", "new_password",
                     "new_password_confirm", "refresh", "access", "token"}


def _sanitizar_body(body_bytes: bytes) -> dict:
    """
    Parsea el body JSON y oculta campos sensibles.
    Retorna un dict listo para loguear.
    """
    if not body_bytes:
        return {}
    try:
        data = json.loads(body_bytes.decode("utf-8", errors="replace"))
        if isinstance(data, dict):
            return {k: ("***" if k in _CAMPOS_SENSIBLES else v) for k, v in data.items()}
        return data
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {"_raw": "<body no-JSON>"}


class AuditoriaMiddleware:
    """
    Middleware de auditoría de escrituras.

    Registra una línea estructurada por cada request de escritura, incluyendo:
    - ts          : timestamp Unix de inicio del request
    - duracion_ms : tiempo de procesamiento en milisegundos
    - user        : username del usuario autenticado (o "anon")
    - method      : método HTTP
    - path        : ruta de la URL
    - status      : código de respuesta HTTP
    - body        : body del request (campos sensibles enmascarados)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method not in _WRITE_METHODS:
            return self.get_response(request)

        # Leer body antes de que Django lo consuma
        body_bytes = request.body
        inicio = time.monotonic()

        response = self.get_response(request)

        duracion_ms = round((time.monotonic() - inicio) * 1000, 1)

        user = (
            request.user.username
            if hasattr(request, "user") and request.user.is_authenticated
            else "anon"
        )

        logger.info(
            "AUDITORIA",
            extra={
                "ts": time.time(),
                "duracion_ms": duracion_ms,
                "user": user,
                "method": request.method,
                "path": request.get_full_path(),
                "status": response.status_code,
                "body": _sanitizar_body(body_bytes),
            },
        )

        return response
