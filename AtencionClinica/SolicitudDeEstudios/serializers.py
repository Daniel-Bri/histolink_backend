# CU10 — Serializers T009 OrdenEstudio

from django.contrib.auth import get_user_model
from rest_framework import serializers

from AtencionClinica.ConsultaMedicaSOAP.models import Consulta
from GestionDeUsuarios.GestionDePersonalDeSalud.models import PersonalSalud

from .models import OrdenEstudio

User = get_user_model()


def _nombre_personal(ps: PersonalSalud | None) -> str:
    if not ps:
        return ""
    u = ps.user
    full = (u.get_full_name() or "").strip()
    return full if full else u.get_username()


def personal_desde_usuario(user) -> PersonalSalud:
    if not getattr(user, "is_authenticated", False):
        raise serializers.ValidationError("Autenticación requerida.")
    try:
        return user.perfil_personal_salud
    except PersonalSalud.DoesNotExist as exc:
        raise serializers.ValidationError(
            {"detail": "El usuario no tiene perfil de personal de salud."}
        ) from exc


class OrdenEstudioListSerializer(serializers.ModelSerializer):
    """Listados compactos."""

    paciente_nombre = serializers.SerializerMethodField()
    tipo_label = serializers.CharField(source="get_tipo_display", read_only=True)
    estado_label = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = OrdenEstudio
        fields = (
            "id",
            "correlativo_orden",
            "tipo",
            "tipo_label",
            "urgente",
            "estado",
            "estado_label",
            "fecha_solicitud",
            "paciente_nombre",
        )

    def get_paciente_nombre(self, obj: OrdenEstudio) -> str:
        try:
            p = obj.consulta.ficha.paciente
            partes = [p.nombres, p.apellido_paterno, p.apellido_materno]
            return " ".join(x for x in partes if x).strip()
        except Exception:
            return ""


class OrdenEstudioDetailSerializer(serializers.ModelSerializer):
    """Detalle completo con datos de consulta y paciente."""

    tipo_label = serializers.CharField(source="get_tipo_display", read_only=True)
    estado_label = serializers.CharField(source="get_estado_display", read_only=True)
    medico_solicitante_nombre = serializers.SerializerMethodField()
    tecnico_responsable_nombre = serializers.SerializerMethodField()
    paciente_nombre = serializers.SerializerMethodField()

    class Meta:
        model = OrdenEstudio
        fields = (
            "id",
            "correlativo_orden",
            "consulta_id",
            "paciente_nombre",
            "tipo",
            "tipo_label",
            "descripcion",
            "indicacion_clinica",
            "urgente",
            "motivo_urgencia",
            "estado",
            "estado_label",
            "fecha_solicitud",
            "fecha_inicio_proceso",
            "fecha_completada",
            "medico_solicitante",
            "medico_solicitante_nombre",
            "tecnico_responsable",
            "tecnico_responsable_nombre",
            "resultado_texto",
            "resultado_archivo",
            "esta_activa",
            "creado_en",
            "actualizado_en",
        )

    def get_medico_solicitante_nombre(self, obj: OrdenEstudio) -> str:
        return _nombre_personal(obj.medico_solicitante)

    def get_tecnico_responsable_nombre(self, obj: OrdenEstudio) -> str:
        return _nombre_personal(obj.tecnico_responsable)

    def get_paciente_nombre(self, obj: OrdenEstudio) -> str:
        try:
            p = obj.consulta.ficha.paciente
            partes = [p.nombres, p.apellido_paterno, p.apellido_materno]
            return " ".join(x for x in partes if x).strip()
        except Exception:
            return ""


class OrdenEstudioCreateSerializer(serializers.ModelSerializer):
    consulta_id = serializers.PrimaryKeyRelatedField(
        queryset=Consulta.objects.select_related("ficha__paciente"),
        source="consulta",
        write_only=True,
    )

    class Meta:
        model = OrdenEstudio
        fields = (
            "consulta_id",
            "tipo",
            "descripcion",
            "indicacion_clinica",
            "urgente",
            "motivo_urgencia",
        )

    def validate(self, attrs):
        if attrs.get("urgente") and not (attrs.get("motivo_urgencia") or "").strip():
            raise serializers.ValidationError(
                {"motivo_urgencia": "Debe especificar el motivo de urgencia."}
            )
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        ps = personal_desde_usuario(request.user)
        orden = OrdenEstudio(medico_solicitante=ps, **validated_data)
        orden.save()
        return orden


class OrdenEstudioUpdateMedicoSerializer(serializers.ModelSerializer):
    """Actualización por médico (sin estado terminal)."""

    class Meta:
        model = OrdenEstudio
        fields = (
            "tipo",
            "descripcion",
            "indicacion_clinica",
            "urgente",
            "motivo_urgencia",
        )


class OrdenEstudioAdminUpdateSerializer(serializers.ModelSerializer):
    """Administración: más campos editables (validación en modelo)."""

    class Meta:
        model = OrdenEstudio
        fields = (
            "tipo",
            "descripcion",
            "indicacion_clinica",
            "urgente",
            "motivo_urgencia",
            "estado",
            "resultado_texto",
            "resultado_archivo",
            "tecnico_responsable",
            "fecha_inicio_proceso",
            "fecha_completada",
            "esta_activa",
        )


class OrdenEstudioCambiarEstadoSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=OrdenEstudio.Estado.choices)
    resultado_texto = serializers.CharField(required=False, allow_blank=True)
    resultado_archivo = serializers.FileField(required=False, allow_null=True)
    tecnico_responsable_id = serializers.PrimaryKeyRelatedField(
        queryset=PersonalSalud.objects.all(),
        required=False,
        allow_null=True,
    )


class OrdenEstudioCreateResponseSerializer(serializers.ModelSerializer):
    """Respuesta POST enriquecida (similar al ejemplo del prompt)."""

    consulta = serializers.IntegerField(source="consulta_id", read_only=True)
    paciente = serializers.SerializerMethodField()
    medico_solicitante = serializers.SerializerMethodField()

    class Meta:
        model = OrdenEstudio
        fields = (
            "id",
            "correlativo_orden",
            "consulta",
            "paciente",
            "tipo",
            "descripcion",
            "urgente",
            "estado",
            "fecha_solicitud",
            "medico_solicitante",
        )

    def get_paciente(self, obj: OrdenEstudio) -> str:
        try:
            p = obj.consulta.ficha.paciente
            partes = [p.nombres, p.apellido_paterno, p.apellido_materno]
            return " ".join(x for x in partes if x).strip()
        except Exception:
            return ""

    def get_medico_solicitante(self, obj: OrdenEstudio) -> str:
        return _nombre_personal(obj.medico_solicitante)
