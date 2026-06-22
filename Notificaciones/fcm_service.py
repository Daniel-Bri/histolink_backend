"""
Notificaciones/fcm_service.py

Servicio singleton para enviar notificaciones push via Firebase Cloud Messaging.
Carga las credenciales una sola vez al startup.
"""
import json
import logging
import os

logger = logging.getLogger(__name__)

_app = None


def _get_app():
    global _app
    if _app is not None:
        return _app
    try:
        import firebase_admin # type: ignore
        from firebase_admin import credentials # type: ignore

        cred_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "kardex",
            "firebase_credentials.json",
        )
        if not os.path.exists(cred_path):
            logger.warning("[FCM] Archivo de credenciales no encontrado en %s", cred_path)
            return None

        cred = credentials.Certificate(cred_path)
        _app = firebase_admin.initialize_app(cred)
        logger.info("[FCM] Firebase Admin SDK inicializado correctamente")
    except Exception as exc:
        logger.exception("[FCM] Error al inicializar Firebase Admin SDK: %s", exc)
        _app = None
    return _app


def enviar_notificacion(tokens: list[str], titulo: str, cuerpo: str, datos: dict | None = None) -> int:
    """
    Envía una notificación push a una lista de tokens FCM.
    Retorna el número de mensajes enviados con éxito.
    Tokens inválidos se desactivan automáticamente en la BD.
    """
    if not tokens:
        return 0

    app = _get_app()
    if app is None:
        logger.warning("[FCM] SDK no inicializado, notificación omitida.")
        return 0

    try:
        from firebase_admin import messaging # type: ignore

        messages = [
            messaging.Message(
                notification=messaging.Notification(title=titulo, body=cuerpo),
                data={k: str(v) for k, v in (datos or {}).items()},
                token=token,
                android=messaging.AndroidConfig(priority="high"),
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        title=titulo,
                        body=cuerpo,
                        icon="/favicon.ico",
                    ),
                    headers={"Urgency": "high"},
                ),
            )
            for token in tokens
        ]

        response = messaging.send_each(messages)
        exitosos = response.success_count
        fallidos  = response.failure_count

        if fallidos:
            _desactivar_tokens_invalidos(tokens, response.responses)
            logger.warning("[FCM] %d tokens fallaron al enviar", fallidos)

        logger.info("[FCM] Notificación enviada: %d éxitos, %d fallos", exitosos, fallidos)
        return exitosos

    except Exception as exc:
        logger.exception("[FCM] Error inesperado al enviar notificación: %s", exc)
        return 0


def notificar_medicos_tenant(tenant_id, titulo: str, cuerpo: str, datos: dict | None = None) -> int:
    """
    Envía una notificación push a todos los médicos activos del tenant.
    """
    from django.contrib.auth import get_user_model
    from .models import DispositivoFCM

    User = get_user_model()
    medicos_ids = list(
        User.objects.filter(
            groups__name="Médico",
            is_active=True,
            dispositivos_fcm__tenant_id=tenant_id,
            dispositivos_fcm__activo=True,
        ).values_list("id", flat=True).distinct()
    )

    if not medicos_ids:
        logger.info("[FCM] Sin médicos con token registrado en tenant %s", tenant_id)
        return 0

    tokens = list(
        DispositivoFCM.objects.filter(
            user_id__in=medicos_ids,
            tenant_id=tenant_id,
            activo=True,
        ).values_list("token", flat=True)
    )

    return enviar_notificacion(tokens, titulo, cuerpo, datos)


def _desactivar_tokens_invalidos(tokens: list[str], responses):
    """Marca como inactivos los tokens que FCM rechazó."""
    from .models import DispositivoFCM

    invalidos = [
        token for token, resp in zip(tokens, responses)
        if not resp.success
    ]
    if invalidos:
        DispositivoFCM.objects.filter(token__in=invalidos).update(activo=False)
        logger.info("[FCM] %d tokens marcados como inactivos", len(invalidos))
