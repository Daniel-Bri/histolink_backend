# CU7 — Serializers de Triaje con validaciones fisiológicas

from rest_framework import serializers
from .models import Triaje


class ClasificarTriajeInputSerializer(serializers.Serializer):
    """
    Paso 1 del flujo de dos pasos.
    Solo recibe los datos necesarios para clasificar — no guarda nada en BD.
    """
    motivo_consulta_triaje  = serializers.CharField(required=False, default="", allow_blank=True)
    saturacion_oxigeno      = serializers.IntegerField(required=False, min_value=50,  max_value=100)
    presion_sistolica       = serializers.IntegerField(required=False, min_value=40,  max_value=300)
    frecuencia_cardiaca     = serializers.IntegerField(required=False, min_value=20,  max_value=300)
    escala_dolor            = serializers.IntegerField(required=False, min_value=0,   max_value=10)
    glasgow                 = serializers.IntegerField(required=False, min_value=3,   max_value=15)


class TriajeSerializer(serializers.ModelSerializer):
    """
    Paso 2 del flujo de dos pasos.
    Recibe el triaje completo con el nivel ya confirmado por enfermería.
    """

    imc              = serializers.SerializerMethodField()
    presion_arterial = serializers.SerializerMethodField()

    class Meta:
        model  = Triaje
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
            'glasgow',
            'motivo_consulta_triaje',
            'observaciones',
            'nivel_sugerido_ia',
            'nivel_urgencia',
            'fue_sobreescrito',
            'justificacion_override',
            'reglas_duras_aplicadas',
            'hora_triaje',
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

    def validate_glasgow(self, value):
        if value is not None and not (3 <= value <= 15):
            raise serializers.ValidationError("La escala de Glasgow debe estar entre 3 y 15.")
        return value

    def validate(self, attrs):
        sistolica  = attrs.get('presion_sistolica')
        diastolica = attrs.get('presion_diastolica')
        if sistolica and diastolica and sistolica <= diastolica:
            raise serializers.ValidationError(
                "La presión sistólica debe ser mayor que la diastólica."
            )

        if attrs.get('fue_sobreescrito') and not attrs.get('justificacion_override', '').strip():
            raise serializers.ValidationError(
                {"justificacion_override": "Requerida cuando se sobreescribe el nivel sugerido por la IA."}
            )
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['enfermera'] = request.user
        return super().create(validated_data)