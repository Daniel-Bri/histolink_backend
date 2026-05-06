# CU20 - Panel de Auditoría

from rest_framework import serializers
from .models import RegistroAuditoria


class RegistroAuditoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroAuditoria
        fields = [
            'id',
            'username',
            'metodo',
            'path',
            'status_code',
            'duracion_ms',
            'body',
            'ip_address',
            'creado_en',
        ]