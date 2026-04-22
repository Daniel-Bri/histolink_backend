# CU9 - Emisión de Receta Médica — Serializers

from django.utils import timezone
from rest_framework import serializers
from .models import Receta, DetalleReceta


class DetalleRecetaSerializer(serializers.ModelSerializer):
    """Serializer para cada medicamento de la receta."""

    class Meta:
        model = DetalleReceta
        fields = [
            'id',
            'medicamento',
            'concentracion',
            'forma_farmaceutica',
            'via_administracion',
            'dosis',
            'frecuencia',
            'duracion',
            'cantidad_total',
            'instrucciones',
            'orden',
        ]

    def validate_medicamento(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError("El nombre del medicamento es obligatorio.")
        return value

    def validate_dosis(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError("La dosis es obligatoria.")
        return value

    def validate_frecuencia(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError("La frecuencia es obligatoria.")
        return value

    def validate_duracion(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError("La duración es obligatoria.")
        return value


class RecetaSerializer(serializers.ModelSerializer):
    """Serializer anidado de Receta con sus detalles (medicamentos)."""

    # Serializer anidado — permite crear detalles junto con la receta
    detalles = DetalleRecetaSerializer(many=True)

    class Meta:
        model = Receta
        fields = [
            'id',
            'consulta',
            'medico',
            'numero_receta',
            'fecha_emision',
            'estado',
            'dispensada_por',
            'fecha_dispensacion',
            'observaciones',
            'detalles',
        ]
        read_only_fields = [
            'id', 'medico', 'numero_receta',
            'fecha_emision', 'estado',
            'dispensada_por', 'fecha_dispensacion',
        ]

    def validate_detalles(self, value):
        if not value:
            raise serializers.ValidationError(
                "La receta debe tener al menos un medicamento."
            )
        return value

    def _generar_correlativo(self):
        """Genera el número de receta automático: REC-YYYY-NNNNN."""
        año = timezone.now().year
        # Contamos recetas del año actual
        ultimo = Receta.objects.filter(
            numero_receta__startswith=f"REC-{año}-"
        ).count()
        return f"REC-{año}-{str(ultimo + 1).zfill(5)}"

    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles')
        request = self.context.get('request')

        # Auto-asignar médico y correlativo
        if request and request.user:
            validated_data['medico'] = request.user
        validated_data['numero_receta'] = self._generar_correlativo()

        # Crear receta
        receta = Receta.objects.create(**validated_data)

        # Crear detalles anidados
        for i, detalle_data in enumerate(detalles_data, start=1):
            detalle_data.setdefault('orden', i)
            DetalleReceta.objects.create(receta=receta, **detalle_data)

        return receta

    def update(self, instance, validated_data):
        detalles_data = validated_data.pop('detalles', None)

        # Actualizar campos de la receta
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Si se mandaron detalles, reemplazarlos
        if detalles_data is not None:
            instance.detalles.all().delete()
            for i, detalle_data in enumerate(detalles_data, start=1):
                detalle_data.setdefault('orden', i)
                DetalleReceta.objects.create(receta=instance, **detalle_data)

        return instance