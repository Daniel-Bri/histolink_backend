from django.contrib import admin
from .models import SuscripcionTenant


@admin.register(SuscripcionTenant)
class SuscripcionTenantAdmin(admin.ModelAdmin):
    list_display  = ['tenant', 'plan', 'estado', 'monto_mensual', 'fecha_vencimiento', 'fecha_ultimo_pago']
    list_filter   = ['plan', 'estado']
    search_fields = ['tenant__nombre']
    readonly_fields = ['creado_en', 'actualizado_en', 'fecha_ultimo_pago']
