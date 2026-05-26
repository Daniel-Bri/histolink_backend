from rest_framework import serializers

class PrediccionRiesgoItemSerializer(serializers.Serializer):
    """Estructura de salida para un riesgo individual."""
    probabilidad = serializers.FloatField()
    clasificacion = serializers.CharField()
    nivel_alerta = serializers.CharField()
    recomendacion = serializers.CharField()

class PrediccionRiesgosResponseSerializer(serializers.Serializer):
    """Respuesta completa con los 4 tipos de riesgo."""
    diabetes_tipo2 = PrediccionRiesgoItemSerializer()
    hipertension = PrediccionRiesgoItemSerializer()
    enfermedad_renal = PrediccionRiesgoItemSerializer()
    evento_cardiovascular = PrediccionRiesgoItemSerializer()
    paciente_id = serializers.IntegerField()
    fecha_calculo = serializers.DateTimeField()
