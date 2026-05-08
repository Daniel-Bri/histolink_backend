from rest_framework import serializers
from .models import ConfiguracionTenant, MODULOS_SISTEMA, Tenant


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Tenant
        fields = ('id', 'nombre', 'slug', 'nit', 'direccion', 'telefono', 'activo', 'creado_en')
        read_only_fields = ('id', 'creado_en')


class ConfiguracionTenantSerializer(serializers.ModelSerializer):
    modulos_disponibles = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = ConfiguracionTenant
        fields = (
            'id',
            'email_contacto',
            'sitio_web',
            'idioma',
            'moneda',
            'zona_horaria',
            'modulos_habilitados',
            'campos_extra_paciente',
            'modulos_disponibles',
            'actualizado_en',
        )
        read_only_fields = ('id', 'actualizado_en', 'modulos_disponibles')

    def get_modulos_disponibles(self, obj):
        return [{'codigo': c, 'nombre': n} for c, n in MODULOS_SISTEMA]


class TenantConConfigSerializer(serializers.ModelSerializer):
    """Usado por MiTenantView — incluye datos del tenant + configuración."""
    configuracion = ConfiguracionTenantSerializer(read_only=True)

    class Meta:
        model  = Tenant
        fields = ('id', 'nombre', 'slug', 'nit', 'direccion', 'telefono', 'activo', 'creado_en', 'configuracion')
        read_only_fields = ('id', 'creado_en')
