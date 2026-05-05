# CU6 — Serializers para Ficha de atención

from django.contrib.auth import get_user_model
from rest_framework import serializers

from GestionDeUsuarios.GestionDePersonalDeSalud.models import PersonalSalud
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente

from .models import Ficha

User = get_user_model()


def personal_salud_desde_usuario(user) -> PersonalSalud:
    """
    Obtiene el perfil PersonalSalud ligado al usuario autenticado.
    Raises:
        serializers.ValidationError: si el usuario no tiene perfil de salud.
    """
    if not getattr(user, "is_authenticated", False):
        raise serializers.ValidationError("Se requiere un usuario autenticado.")
    try:
        return user.perfil_personal_salud
    except PersonalSalud.DoesNotExist as exc:
        raise serializers.ValidationError(
            {"detail": "El usuario autenticado no tiene perfil de personal de salud asociado."}
        ) from exc


class PacienteFichaBriefSerializer(serializers.ModelSerializer):
    """Datos compactos del paciente en respuestas de ficha."""

    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Paciente
        fields = ("id", "nombre_completo", "ci")

    def get_nombre_completo(self, obj: Paciente) -> str:
        partes = [obj.nombres, obj.apellido_paterno, obj.apellido_materno]
        return " ".join(p for p in partes if p).strip()


class ProfesionalFichaBriefSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()

    class Meta:
        model = PersonalSalud
        fields = ("id", "nombre")

    def get_nombre(self, obj: PersonalSalud) -> str:
        u: User = obj.user
        full = (u.get_full_name() or "").strip()
        return full if full else u.get_username()


class TriajeResumenSerializer(serializers.Serializer):
    """Datos compactos del triaje para incluir en respuestas de Ficha."""
    id                    = serializers.IntegerField()
    nivel_urgencia        = serializers.CharField()
    nivel_sugerido_ia     = serializers.CharField(allow_null=True)
    fue_sobreescrito      = serializers.BooleanField()
    reglas_duras_aplicadas = serializers.BooleanField()
    motivo_consulta_triaje = serializers.CharField()
    hora_triaje           = serializers.DateTimeField()
    peso_kg               = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    talla_cm              = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    frecuencia_cardiaca   = serializers.IntegerField(allow_null=True)
    frecuencia_respiratoria = serializers.IntegerField(allow_null=True)
    presion_sistolica     = serializers.IntegerField(allow_null=True)
    presion_diastolica    = serializers.IntegerField(allow_null=True)
    temperatura_celsius   = serializers.DecimalField(max_digits=4, decimal_places=1, allow_null=True)
    saturacion_oxigeno    = serializers.IntegerField(allow_null=True)
    escala_dolor          = serializers.IntegerField(allow_null=True)
    glasgow               = serializers.IntegerField(allow_null=True)
    glucemia              = serializers.DecimalField(max_digits=6, decimal_places=1, allow_null=True)
    observaciones         = serializers.CharField(allow_null=True, allow_blank=True)
    justificacion_override = serializers.CharField(allow_null=True, allow_blank=True)


class FichaSerializer(serializers.ModelSerializer):
    """
    CRUD principal: alta con paciente_id; lectura enriquecida con paciente y profesional_apertura.
    """

    paciente = PacienteFichaBriefSerializer(read_only=True)
    paciente_id = serializers.PrimaryKeyRelatedField(
        queryset=Paciente.objects.filter(activo=True),
        write_only=True,
        source="paciente",
        help_text="ID del paciente activo.",
    )
    profesional_apertura = ProfesionalFichaBriefSerializer(read_only=True)
    triaje_resumen = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Ficha
        fields = (
            "id",
            "correlativo",
            "paciente",
            "paciente_id",
            "profesional_apertura",
            "estado",
            "fecha_apertura",
            "fecha_inicio_atencion",
            "fecha_cierre",
            "esta_activa",
            "triaje_resumen",
            "creado_en",
            "actualizado_en",
        )

    def get_triaje_resumen(self, obj: Ficha):
        try:
            t = obj.triaje
        except Exception:
            return None
        return TriajeResumenSerializer(t).data
        read_only_fields = (
            "id",
            "correlativo",
            "paciente",
            "profesional_apertura",
            "fecha_apertura",
            "fecha_inicio_atencion",
            "fecha_cierre",
            "esta_activa",
            "creado_en",
            "actualizado_en",
        )

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        ps = personal_salud_desde_usuario(user)
        ficha = Ficha(**validated_data, profesional_apertura=ps)
        ficha.full_clean()
        ficha.save()
        return ficha

    def update(self, instance: Ficha, validated_data):
        validated_data.pop("paciente", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.full_clean()
        instance.save()
        return instance


class FichaEstadoSerializer(serializers.ModelSerializer):
    """Solo transición de estado (validaciones en modelo Ficha.save / clean)."""

    class Meta:
        model = Ficha
        fields = ("estado",)
