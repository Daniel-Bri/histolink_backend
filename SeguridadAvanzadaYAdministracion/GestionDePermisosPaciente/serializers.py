from django.contrib.auth import get_user_model
from rest_framework import serializers

from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from Tenants.models import Tenant
from .models import PermisoPaciente

User = get_user_model()


class PermisoPacienteSerializer(serializers.ModelSerializer):
    paciente_ci = serializers.CharField(source="paciente.ci", read_only=True)
    paciente_nombre = serializers.SerializerMethodField()
    medico_username = serializers.CharField(source="medico.username", read_only=True)
    medico_nombre = serializers.SerializerMethodField()
    otorgado_por_username = serializers.CharField(source="otorgado_por.username", read_only=True)

    class Meta:
        model = PermisoPaciente
        fields = (
            "id",
            "paciente_id",
            "paciente_ci",
            "paciente_nombre",
            "medico_id",
            "medico_username",
            "medico_nombre",
            "otorgado_por_id",
            "otorgado_por_username",
            "fecha_otorgamiento",
            "fecha_revocacion",
            "activo",
            "tenant_id",
        )
        read_only_fields = (
            "id",
            "fecha_otorgamiento",
            "fecha_revocacion",
            "activo",
            "tenant_id",
            "otorgado_por_id",
        )

    def get_paciente_nombre(self, obj: PermisoPaciente) -> str:
        p = obj.paciente
        return f"{p.nombres} {p.apellido_paterno} {p.apellido_materno}".strip()

    def get_medico_nombre(self, obj: PermisoPaciente) -> str:
        m = obj.medico
        return f"{m.first_name} {m.last_name}".strip() or m.username


class OtorgarPermisoSerializer(serializers.Serializer):
    paciente_id = serializers.PrimaryKeyRelatedField(
        source="paciente",
        queryset=Paciente.objects.all(),
    )
    medico_id = serializers.PrimaryKeyRelatedField(
        source="medico",
        queryset=User.objects.all(),
    )

    def validate(self, attrs):
        paciente = attrs["paciente"]
        medico = attrs["medico"]
        request = self.context.get("request")
        tenant = getattr(request, "tenant", None) if request else None

        # Verificar que el paciente pertenece al tenant
        if tenant and paciente.tenant_id and paciente.tenant_id != tenant.id:
            raise serializers.ValidationError({"paciente_id": "El paciente no pertenece al establecimiento (tenant) actual."})

        # Validar si ya existe un permiso activo
        active_permiso = PermisoPaciente.objects.filter(
            paciente=paciente,
            medico=medico,
            activo=True
        )
        if active_permiso.exists():
            raise serializers.ValidationError("Ya existe un permiso activo para este paciente y médico.")

        return attrs

    def create(self, validated_data):
        paciente = validated_data["paciente"]
        medico = validated_data["medico"]
        request = self.context["request"]
        tenant = getattr(request, "tenant", None) or paciente.tenant

        # Buscar si ya existe un registro inactivo para reactivarlo
        permiso_existente = PermisoPaciente.objects.filter(
            paciente=paciente,
            medico=medico,
            activo=False
        ).first()

        if permiso_existente:
            permiso_existente.reactivar(otorgado_por=request.user)
            return permiso_existente
        else:
            obj = PermisoPaciente.objects.create(
                paciente=paciente,
                medico=medico,
                otorgado_por=request.user,
                tenant=tenant,
                activo=True
            )
            return obj


class RevocarPermisoSerializer(serializers.Serializer):
    paciente_id = serializers.PrimaryKeyRelatedField(
        source="paciente",
        queryset=Paciente.objects.all(),
    )
    medico_id = serializers.PrimaryKeyRelatedField(
        source="medico",
        queryset=User.objects.all(),
    )

    def validate(self, attrs):
        paciente = attrs["paciente"]
        medico = attrs["medico"]
        request = self.context.get("request")
        tenant = getattr(request, "tenant", None) if request else None

        # Verificar que el paciente pertenece al tenant
        if tenant and paciente.tenant_id and paciente.tenant_id != tenant.id:
            raise serializers.ValidationError({"paciente_id": "El paciente no pertenece al establecimiento (tenant) actual."})

        # Buscar el permiso activo
        permiso = PermisoPaciente.objects.filter(
            paciente=paciente,
            medico=medico,
            activo=True
        ).first()

        if not permiso:
            raise serializers.ValidationError("No existe un permiso activo para este paciente y médico.")

        attrs["permiso"] = permiso
        return attrs

    def save(self):
        permiso = self.validated_data["permiso"]
        permiso.revocar()
        return permiso
