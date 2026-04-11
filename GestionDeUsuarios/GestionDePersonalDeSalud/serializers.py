from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
from rest_framework import serializers

from .models import Especialidad, PersonalSalud

User = get_user_model()


class EspecialidadSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(
        max_length=120,
        required=True,
        validators=[
            UniqueValidator(
                queryset=Especialidad.objects.all(),
                message="Ya existe una especialidad con ese nombre.",
            )
        ],
    )

    class Meta:
        model = Especialidad
        fields = ["id", "nombre"]

    def validate_nombre(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("El nombre es obligatorio.")

        import re

        if not re.match(r"^[a-zA-ZáéíóúñÑ\s]+$", value):
            raise serializers.ValidationError(
                "El nombre solo puede contener letras y espacios."
            )
        return value


class PersonalSaludSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        source="user",
        queryset=User.objects.all(),
        write_only=True,
    )

    class Meta:
        model = PersonalSalud
        fields = [
            "id",
            "user_id",
            "user",
            "item_min_salud",
            "rol",
            "especialidad",
            "telefono",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "is_active", "created_at", "updated_at"]

    def validate_item_min_salud(self, value):
        import re

        if not value:
            raise serializers.ValidationError("item_min_salud es obligatorio.")
        if not re.match(r"^[A-Z]{3}-\d{3}$", value):
            raise serializers.ValidationError(
                "item_min_salud debe tener formato AAA-123."
            )

        queryset = PersonalSalud.objects.filter(item_min_salud=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("item_min_salud ya está registrado.")

        return value

    def validate(self, attrs):
        user = attrs.get("user", getattr(self.instance, "user", None))
        rol = attrs.get("rol", getattr(self.instance, "rol", None))
        especialidad = attrs.get("especialidad", getattr(self.instance, "especialidad", None))

        if user:
            queryset = PersonalSalud.objects.filter(user=user)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError(
                    {"user_id": "Este usuario ya tiene un perfil PersonalSalud."}
                )

        if rol == PersonalSalud.ROL_MEDICO and not especialidad:
            raise serializers.ValidationError(
                {"especialidad": "La especialidad es obligatoria para rol 'medico'."}
            )

        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["user"] = {
            "id": instance.user.id,
            "username": instance.user.username,
            "email": instance.user.email,
        }
        return data
