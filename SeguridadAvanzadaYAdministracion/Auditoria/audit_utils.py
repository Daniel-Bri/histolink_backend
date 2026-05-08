from .models import RegistroAuditoria
from .thread_local import get_current_request


def registrar_evento(accion, objeto, cambios=None, request=None):
    """
    Función utilitaria para registrar un evento de auditoría.
    Captura automáticamente el usuario, tenant e información de red si están disponibles.
    """
    if request is None:
        request = get_current_request()

    usuario_id = 0
    usuario_nombre = 'Sistema/Anónimo'
    usuario_rol = 'N/A'

    if request and hasattr(request, 'user') and request.user.is_authenticated:
        usuario_id = request.user.id
        usuario_nombre = request.user.username
        # Intentar obtener el rol del grupo
        groups = request.user.groups.all()
        usuario_rol = groups[0].name if groups.exists() else 'Sin Rol'
    elif hasattr(objeto, 'medico') and objeto.medico:
        # Fallback si es una señal y no hay request (ej: Celery o Shell)
        usuario_id = objeto.medico.id
        usuario_nombre = objeto.medico.username
        usuario_rol = 'Médico'

    tenant_id = None
    tenant_nombre = ''
    if request and hasattr(request, 'tenant') and request.tenant:
        tenant_id = request.tenant.id
        tenant_nombre = request.tenant.nombre
    elif hasattr(objeto, 'tenant') and objeto.tenant:
        tenant_id = objeto.tenant.id
        tenant_nombre = objeto.tenant.nombre

    # Registrar el evento
    return RegistroAuditoria.objects.create(
        accion=accion,
        modelo=objeto.__class__.__name__,
        objeto_id=str(objeto.id) if hasattr(objeto, 'id') else 'N/A',
        objeto_repr=str(objeto)[:200],
        usuario_id=usuario_id,
        usuario_nombre=usuario_nombre,
        usuario_rol=usuario_rol,
        tenant_id=tenant_id,
        tenant_nombre=tenant_nombre,
        cambios=cambios or {},
        ip_origen=request.META.get('REMOTE_ADDR') if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else '',
        endpoint=request.path if request else '',
    )
