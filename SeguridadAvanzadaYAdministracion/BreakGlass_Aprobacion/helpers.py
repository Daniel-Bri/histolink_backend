from django.utils import timezone


def construir_notificacion_rechazo(solicitud, motivo_rechazo: str) -> dict:
    return {
        "destinatario_id": solicitud.solicitante_id,
        "destinatario_username": solicitud.solicitante.username,
        "paciente_id": solicitud.paciente_id,
        "solicitud_id": solicitud.id,
        "tipo": "BREAK_GLASS_RECHAZO",
        "mensaje": f"Tu solicitud Break-Glass fue rechazada. Motivo: {motivo_rechazo}",
        "creado_en": timezone.now().isoformat(),
    }
