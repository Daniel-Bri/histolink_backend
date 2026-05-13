# CU20 - Panel de Auditoría
# Lee desde Auditoria.RegistroAuditoria (el modelo real que registra eventos)

from rest_framework import serializers
from SeguridadAvanzadaYAdministracion.Auditoria.models import RegistroAuditoria

_ACCION_MAP = {
    'CREATE':    'CREAR',
    'UPDATE':    'ACTUALIZAR',
    'DELETE':    'ELIMINAR',
    'FIRMAR':    'ACTUALIZAR',
    'COMPLETAR': 'ACTUALIZAR',
    'DISPENSAR': 'ACTUALIZAR',
    'ANULAR':    'ELIMINAR',
    'LOGIN':     'LOGIN',
    'LOGOUT':    'LOGOUT',
}

_PATH_MODULO = [
    ('/api/pacientes',    'PACIENTES'),
    ('/api/auth/login',  'USUARIOS'),
    ('/api/auth/logout', 'USUARIOS'),
    ('/api/auth',        'USUARIOS'),
    ('/api/personal',    'USUARIOS'),
    ('/api/triaje',      'ATENCION_CLINICA'),
    ('/api/consultas',   'ATENCION_CLINICA'),
    ('/api/clinica',     'ATENCION_CLINICA'),
    ('/api/ordenes',     'ATENCION_CLINICA'),
    ('/api/fichas',      'APERTURA_FICHA'),
    ('/api/reportes',    'REPORTES'),
    ('/api/auditoria',   'REPORTES'),
    ('/api/admin',       'CONFIGURACION'),
    ('/api/tenants',     'CONFIGURACION'),
]

_MODELO_MODULO = {
    'Paciente':      'PACIENTES',
    'User':          'USUARIOS',
    'PersonalSalud': 'USUARIOS',
    'Ficha':         'APERTURA_FICHA',
    'Triaje':        'ATENCION_CLINICA',
    'Consulta':      'ATENCION_CLINICA',
    'RecetaMedica':  'ATENCION_CLINICA',
    'OrdenEstudio':  'ATENCION_CLINICA',
    'Antecedente':   'PACIENTES',
}


def _derive_modulo(obj) -> str:
    # Primero por modelo Django
    m = _MODELO_MODULO.get(obj.modelo)
    if m:
        return m
    # Luego por endpoint URL
    path = obj.endpoint or ''
    for prefix, modulo in _PATH_MODULO:
        if path.startswith(prefix):
            return modulo
    return 'CONFIGURACION'


class RegistroAuditoriaSerializer(serializers.ModelSerializer):
    timestamp        = serializers.DateTimeField()
    usuario_username = serializers.CharField(source='usuario_nombre')
    accion           = serializers.SerializerMethodField()
    modulo           = serializers.SerializerMethodField()
    ip_address       = serializers.CharField(source='ip_origen', allow_null=True)
    detalles         = serializers.SerializerMethodField()

    class Meta:
        model  = RegistroAuditoria
        fields = ['id', 'timestamp', 'usuario_username', 'accion', 'modulo', 'ip_address', 'detalles']

    def get_accion(self, obj):
        return _ACCION_MAP.get(obj.accion, obj.accion)

    def get_modulo(self, obj):
        return _derive_modulo(obj)

    def get_detalles(self, obj):
        partes = [obj.accion, obj.modelo]
        if obj.objeto_repr:
            partes.append(f'"{obj.objeto_repr}"')
        if obj.endpoint:
            partes.append(f'[{obj.endpoint}]')
        return ' '.join(partes)
