from django.contrib import admin
from .models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    """Configuración del panel administrativo para el registro de auditoría."""
    list_display = (
        'timestamp', 
        'accion', 
        'modelo', 
        'objeto_id', 
        'usuario_nombre', 
        'usuario_rol', 
        'tenant_nombre'
    )
    list_filter = ('accion', 'modelo', 'usuario_rol', 'timestamp')
    search_fields = (
        'objeto_id', 
        'objeto_repr', 
        'usuario_nombre', 
        'tenant_nombre', 
        'hash_evento'
    )
    readonly_fields = (
        'accion', 
        'modelo', 
        'objeto_id', 
        'objeto_repr', 
        'usuario_id', 
        'usuario_nombre', 
        'usuario_rol', 
        'tenant_id', 
        'tenant_nombre', 
        'cambios', 
        'ip_origen', 
        'user_agent', 
        'endpoint', 
        'hash_evento', 
        'timestamp'
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
