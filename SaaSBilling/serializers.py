from rest_framework import serializers
from .models import SuscripcionTenant


class SuscripcionTenantSerializer(serializers.ModelSerializer):
    tenant_nombre = serializers.CharField(source='tenant.nombre', read_only=True)
    tenant_slug   = serializers.CharField(source='tenant.slug',   read_only=True)
    tenant_activo = serializers.BooleanField(source='tenant.activo', read_only=True)

    class Meta:
        model  = SuscripcionTenant
        fields = [
            'id', 'tenant', 'tenant_nombre', 'tenant_slug', 'tenant_activo',
            'plan', 'estado', 'monto_mensual',
            'fecha_inicio', 'fecha_vencimiento',
            'fecha_ultimo_pago', 'creado_en', 'actualizado_en',
        ]
        read_only_fields = ['tenant', 'fecha_ultimo_pago', 'creado_en', 'actualizado_en']
