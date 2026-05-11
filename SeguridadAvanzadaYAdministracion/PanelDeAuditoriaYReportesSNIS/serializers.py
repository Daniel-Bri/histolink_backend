# CU20 - Panel de Auditoría

from rest_framework import serializers
from .models import RegistroAuditoria

METODO_TO_ACCION = {
    'POST':   'CREAR',
    'PUT':    'ACTUALIZAR',
    'PATCH':  'ACTUALIZAR',
    'DELETE': 'ELIMINAR',
}

# Orden importa: más específico primero
_PATH_MODULO = [
    ('/api/pacientes',       'PACIENTES'),
    ('/api/auth/login',      'USUARIOS'),
    ('/api/auth/logout',     'USUARIOS'),
    ('/api/auth',            'USUARIOS'),
    ('/api/personal',        'USUARIOS'),
    ('/api/triaje',          'ATENCION_CLINICA'),
    ('/api/consultas',       'ATENCION_CLINICA'),
    ('/api/clinica',         'ATENCION_CLINICA'),
    ('/api/ordenes',         'ATENCION_CLINICA'),
    ('/api/fichas',          'APERTURA_FICHA'),
    ('/api/reportes',        'REPORTES'),
    ('/api/auditoria',       'REPORTES'),
    ('/api/admin/backup',    'CONFIGURACION'),
    ('/api/tenants',         'CONFIGURACION'),
]


def _path_to_modulo(path: str) -> str:
    for prefix, modulo in _PATH_MODULO:
        if path.startswith(prefix):
            return modulo
    return 'CONFIGURACION'


class RegistroAuditoriaSerializer(serializers.ModelSerializer):
    timestamp       = serializers.DateTimeField(source='creado_en')
    usuario_username = serializers.CharField(source='username')
    accion          = serializers.SerializerMethodField()
    modulo          = serializers.SerializerMethodField()
    detalles        = serializers.SerializerMethodField()

    class Meta:
        model  = RegistroAuditoria
        fields = ['id', 'timestamp', 'usuario_username', 'accion', 'modulo', 'ip_address', 'detalles']

    def get_accion(self, obj):
        return METODO_TO_ACCION.get(obj.metodo, obj.metodo)

    def get_modulo(self, obj):
        return _path_to_modulo(obj.path)

    def get_detalles(self, obj):
        return f"{obj.metodo} {obj.path} [{obj.status_code}]"
