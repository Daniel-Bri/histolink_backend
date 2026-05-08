from rest_framework import serializers
from .models import GestionAnual


class GestionAnualSerializer(serializers.ModelSerializer):
    tenant_nombre = serializers.CharField(source='tenant.nombre', read_only=True)

    class Meta:
        model  = GestionAnual
        fields = (
            'id', 'tenant', 'tenant_nombre', 'año',
            'congelada', 'fecha_congelamiento', 'descripcion',
            'creado_en', 'actualizado_en',
        )
        read_only_fields = ('id', 'tenant', 'tenant_nombre', 'congelada', 'fecha_congelamiento', 'creado_en', 'actualizado_en')
