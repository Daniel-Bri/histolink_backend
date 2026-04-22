from rest_framework import serializers
from .models import Tenant


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ('id', 'nombre', 'slug', 'nit', 'direccion', 'telefono', 'activo', 'creado_en')
        read_only_fields = ('id', 'creado_en')
