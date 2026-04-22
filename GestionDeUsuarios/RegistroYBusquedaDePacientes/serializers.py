import re
from datetime import date

from django.core.validators import RegexValidator
from rest_framework import serializers
from .models import Paciente


_LETRAS_ESPACIOS_RE = re.compile(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$")


class PacienteSerializer(serializers.ModelSerializer):
    """API T010: nombre/apellido/genero mapean a nombres/apellido_paterno/sexo."""

    nombre = serializers.CharField(source="nombres", max_length=100, required=True)
    apellido = serializers.CharField(source="apellido_paterno", max_length=100, required=True)
    genero = serializers.ChoiceField(
        source="sexo",
        choices=["M", "F", "O"],
        required=True,
    )
    establecimiento = serializers.SerializerMethodField(read_only=True)
    ci = serializers.CharField(
        max_length=10,
        min_length=4,
        required=True,
        validators=[
            RegexValidator(
                regex=r"^\d+$",
                message="El CI solo puede contener dígitos.",
            )
        ],
    )
    ci_complemento = serializers.CharField(
        max_length=2,
        required=False,
        allow_blank=True,
        default="",
    )
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        max_length=254,
    )
    telefono = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=15,
    )
    direccion = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=200,
    )

    class Meta:
        model = Paciente
        fields = [
            "id",
            "ci",
            "ci_complemento",
            "nombre",
            "apellido",
            "apellido_materno",
            "fecha_nacimiento",
            "genero",
            "email",
            "telefono",
            "direccion",
            "activo",
            "establecimiento",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = ["id", "activo", "establecimiento", "creado_en", "actualizado_en"]

    def get_establecimiento(self, obj):
        if obj.tenant:
            return {"id": obj.tenant.id, "nombre": obj.tenant.nombre}
        return None

    def validate_ci_complemento(self, value):
        value = (value or "").strip().upper()
        if not value:
            return ""
        if not re.match(r"^[A-Z0-9]{1,2}$", value):
            raise serializers.ValidationError(
                "El complemento solo puede tener letras mayúsculas o números (máx. 2 caracteres)."
            )
        return value

    def validate_nombre(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("El nombre es obligatorio.")
        if not _LETRAS_ESPACIOS_RE.match(value):
            raise serializers.ValidationError(
                "El nombre solo puede contener letras y espacios."
            )
        return value

    def validate_apellido(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("El apellido es obligatorio.")
        if not _LETRAS_ESPACIOS_RE.match(value):
            raise serializers.ValidationError(
                "El apellido solo puede contener letras y espacios."
            )
        return value

    def validate_fecha_nacimiento(self, value):
        if value > date.today():
            raise serializers.ValidationError("La fecha de nacimiento no puede ser futura.")
        return value

    def validate(self, attrs):
        if self.instance:
            ci = attrs.get("ci", self.instance.ci)
            ci_complemento = attrs.get("ci_complemento", self.instance.ci_complemento)
        else:
            ci = attrs.get("ci")
            ci_complemento = attrs.get("ci_complemento", "") or ""
        ci_complemento = (ci_complemento or "").strip()

        qs = Paciente.objects.filter(ci=ci, ci_complemento=ci_complemento)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                {"ci": "Ya existe un paciente con este CI y complemento."}
            )
        return attrs

    def validate_telefono(self, value):
        if not value or not str(value).strip():
            return ""
        s = str(value).strip()
        if not re.match(r"^\d{7,15}$", s):
            raise serializers.ValidationError(
                "El teléfono debe contener solo dígitos y tener entre 7 y 15 caracteres."
            )
        return s

    def create(self, validated_data):
        validated_data.setdefault("apellido_materno", "")
        validated_data.setdefault("autoidentificacion", "NE")
        validated_data.setdefault("tipo_seguro", "PARTICULAR")
        return super().create(validated_data)
