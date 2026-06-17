from decimal import Decimal
from rest_framework import serializers
from .models import Cobro


class CrearSesionCobroSerializer(serializers.Serializer):
    ficha_id = serializers.IntegerField()
    concepto = serializers.CharField(max_length=255)
    monto = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))


class CobroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cobro
        fields = [
            "id", "ficha", "paciente", "concepto", "monto",
            "estado", "stripe_session_id", "fecha_pago",
            "creado_en", "actualizado_en",
        ]
        read_only_fields = fields