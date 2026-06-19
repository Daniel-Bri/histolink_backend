from rest_framework import serializers


class BreakGlassSolicitudRechazoSerializer(serializers.Serializer):
    motivo_rechazo = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        min_length=10,
    )

    def validate_motivo_rechazo(self, value: str) -> str:
        valor = (value or "").strip()
        if len(valor) < 10:
            raise serializers.ValidationError("El motivo de rechazo debe tener al menos 10 caracteres.")
        return valor
