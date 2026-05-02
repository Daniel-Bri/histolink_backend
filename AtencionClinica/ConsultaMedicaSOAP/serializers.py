# CU8 - Consulta Médica SOAP — Serializers

import re
from rest_framework import serializers
from .models import Consulta


_CIE10_RE = re.compile(r'^[A-Z]\d{2}(\.\d{1,4})?$')


class ConsultaSerializer(serializers.ModelSerializer):
    """Serializer clínico completo para consulta SOAP."""

    class Meta:
        model = Consulta
        fields = [
            'id',
            'paciente',
            'medico',
            'triaje',
            'estado',
            # SOAP-S
            'motivo_consulta',
            'historia_enfermedad_actual',
            # SOAP-O
            'examen_fisico',
            # SOAP-A
            'impresion_diagnostica',
            'codigo_cie10_principal',
            'codigo_cie10_secundario',
            'descripcion_cie10',
            # SOAP-P
            'plan_tratamiento',
            'indicaciones_alta',
            # Derivación
            'requiere_derivacion',
            'derivacion_destino',
            'derivacion_motivo',
            # Firma
            'hash_documento',
            'firmada_por',
            'firmada_en',
            'creado_en',
            'actualizado_en',
        ]
        read_only_fields = [
            'id', 'medico', 'estado', 'hash_documento',
            'firmada_por', 'firmada_en', 'creado_en', 'actualizado_en'
        ]

    def validate_codigo_cie10_principal(self, value):
        value = (value or '').strip().upper()
        if not value:
            raise serializers.ValidationError("El código CIE-10 principal es obligatorio.")
        if not _CIE10_RE.match(value):
            raise serializers.ValidationError(
                "Formato CIE-10 inválido. Ejemplos válidos: J18.9, E11, A00.0"
            )
        return value

    def validate_codigo_cie10_secundario(self, value):
        value = (value or '').strip().upper()
        if value and not _CIE10_RE.match(value):
            raise serializers.ValidationError(
                "Formato CIE-10 secundario inválido. Ejemplos válidos: J18.9, E11, A00.0"
            )
        return value

    def validate_estado(self, value):
        if self.instance:
            estados_validos = {
                'BORRADOR': ['COMPLETADA'],
                'COMPLETADA': ['FIRMADA'],
                'FIRMADA': [],
            }
            estado_actual = self.instance.estado
            if value != estado_actual and value not in estados_validos.get(estado_actual, []):
                raise serializers.ValidationError(
                    f"Transición de estado inválida: {estado_actual} → {value}. "
                    f"Solo se permite: {estado_actual} → {estados_validos.get(estado_actual, [])}"
                )
        return value

    def validate(self, attrs):
        requiere_derivacion = attrs.get('requiere_derivacion', False)
        derivacion_destino = attrs.get('derivacion_destino', '')
        if requiere_derivacion and not derivacion_destino:
            raise serializers.ValidationError(
                {'derivacion_destino': 'Si requiere derivación, debe especificar el destino.'}
            )
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['medico'] = request.user
        return super().create(validated_data)