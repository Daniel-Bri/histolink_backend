# T012 — Serializers clínico y tratamiento + validaciones + campos ML triaje

from rest_framework import serializers
from .models import Triaje


class TriajeSerializer(serializers.ModelSerializer):
    """Serializer completo para registro y lectura de triaje."""

    # Campos calculados (read-only)
    imc = serializers.SerializerMethodField()
    presion_arterial = serializers.SerializerMethodField()

    # Campos ML (read-only, asignados por el modelo IA)
    nivel_urgencia_ia = serializers.CharField(
        source='nivel_urgencia',
        read_only=True,
    )

    class Meta:
        model = Triaje
        fields = [
            'id',
            'paciente',
            'enfermera',
            'peso_kg',
            'talla_cm',
            'frecuencia_cardiaca',
            'frecuencia_respiratoria',
            'presion_sistolica',
            'presion_diastolica',
            'temperatura_celsius',
            'saturacion_oxigeno',
            'glucemia',
            'escala_dolor',
            'nivel_urgencia',
            'nivel_urgencia_ia',
            'motivo_consulta_triaje',
            'observaciones',
            'hora_triaje',
            # Calculados
            'imc',
            'presion_arterial',
        ]
        read_only_fields = ['id', 'hora_triaje', 'enfermera']

    def get_imc(self, obj):
        return obj.imc

    def get_presion_arterial(self, obj):
        return obj.presion_arterial

    def validate_escala_dolor(self, value):
        if value is not None and not (0 <= value <= 10):
            raise serializers.ValidationError("La escala de dolor debe estar entre 0 y 10.")
        return value

    def validate_saturacion_oxigeno(self, value):
        if value is not None and not (50 <= value <= 100):
            raise serializers.ValidationError("La saturación de oxígeno debe estar entre 50 y 100.")
        return value

    def validate_temperatura_celsius(self, value):
        if value is not None and not (25 <= float(value) <= 45):
            raise serializers.ValidationError("La temperatura debe estar entre 25 y 45 °C.")
        return value

    def validate_presion_sistolica(self, value):
        if value is not None and not (40 <= value <= 300):
            raise serializers.ValidationError("La presión sistólica debe estar entre 40 y 300 mmHg.")
        return value

    def validate_presion_diastolica(self, value):
        if value is not None and not (20 <= value <= 200):
            raise serializers.ValidationError("La presión diastólica debe estar entre 20 y 200 mmHg.")
        return value

    def validate(self, attrs):
        sistolica = attrs.get('presion_sistolica')
        diastolica = attrs.get('presion_diastolica')
        if sistolica and diastolica and sistolica <= diastolica:
            raise serializers.ValidationError(
                "La presión sistólica debe ser mayor que la diastólica."
            )
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['enfermera'] = request.user
        return super().create(validated_data)