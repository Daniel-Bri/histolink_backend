from __future__ import annotations

from rest_framework import serializers

from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente

from .models import BreakGlassSolicitud


class BreakGlassSolicitudCreateSerializer(serializers.ModelSerializer):
    paciente_id = serializers.PrimaryKeyRelatedField(
        source="paciente",
        queryset=Paciente.objects.all(),
        write_only=True,
    )
    advertencia = serializers.CharField(read_only=True)

    class Meta:
        model = BreakGlassSolicitud
        fields = (
            "id",
            "paciente_id",
            "justificacion",
            "nivel_urgencia",
            "estado",
            "acceso_desde",
            "acceso_hasta",
            "advertencia",
            "creado_en",
        )
        read_only_fields = ("id", "estado", "acceso_desde", "acceso_hasta", "creado_en", "advertencia")

    def validate_justificacion(self, value: str):
        if len((value or "").strip()) < 20:
            raise serializers.ValidationError("La justificación debe tener al menos 20 caracteres.")
        return value

    def validate(self, attrs):
        paciente = attrs["paciente"]
        request = self.context.get("request")
        tenant = getattr(request, "tenant", None) if request else None
        if tenant and paciente.tenant_id and paciente.tenant_id != tenant.id:
            raise serializers.ValidationError({"paciente_id": "El paciente no pertenece al tenant actual."})
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        tenant = getattr(request, "tenant", None) or validated_data["paciente"].tenant
        obj = BreakGlassSolicitud(
            tenant=tenant,
            solicitante=request.user,
            **validated_data,
        )
        obj.save()
        self.context["advertencia"] = (
            "Acceso temporal otorgado por emergencia"
            if obj.nivel_urgencia == BreakGlassSolicitud.NivelUrgencia.ALTA
            else None
        )
        return obj

    def to_representation(self, instance):
        data = super().to_representation(instance)
        advertencia = self.context.get("advertencia")
        if advertencia:
            data["advertencia"] = advertencia
        return data


class BreakGlassSolicitudListSerializer(serializers.ModelSerializer):
    solicitante_username = serializers.CharField(source="solicitante.username", read_only=True)
    paciente_ci = serializers.CharField(source="paciente.ci", read_only=True)
    paciente_nombre = serializers.SerializerMethodField()
    acceso_activo = serializers.BooleanField(read_only=True)
    acceso_expirado = serializers.BooleanField(read_only=True)

    class Meta:
        model = BreakGlassSolicitud
        fields = (
            "id",
            "tenant_id",
            "solicitante_id",
            "solicitante_username",
            "paciente_id",
            "paciente_ci",
            "paciente_nombre",
            "justificacion",
            "nivel_urgencia",
            "estado",
            "aprobado_por_id",
            "acceso_desde",
            "acceso_hasta",
            "acceso_activo",
            "acceso_expirado",
            "evento_blockchain_id",
            "creado_en",
            "actualizado_en",
        )

    def get_paciente_nombre(self, obj: BreakGlassSolicitud) -> str:
        p = obj.paciente
        return " ".join(x for x in [p.nombres, p.apellido_paterno, p.apellido_materno] if x).strip()
