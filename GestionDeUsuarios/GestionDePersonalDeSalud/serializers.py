import re

from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Especialidad, PersonalSalud


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email"]


class EspecialidadSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(max_length=120, required=True)

    class Meta:
        model = Especialidad
        fields = ["id", "nombre"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Especialidad.objects.all()
        if self.instance is not None and hasattr(self.instance, 'pk'):
            qs = qs.exclude(pk=self.instance.pk)
        self.fields["nombre"].validators = [
            v
            for v in self.fields["nombre"].validators
            if not isinstance(v, UniqueValidator)
        ]
        self.fields["nombre"].validators.append(
            UniqueValidator(
                queryset=qs,
                message="Ya existe una especialidad con ese nombre.",
            )
        )

    def validate_nombre(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("El nombre es obligatorio.")
        if not re.match(r"^[a-zA-ZáéíóúñÑ\s]+$", value):
            raise serializers.ValidationError(
                "El nombre solo puede contener letras y espacios."
            )
        return value


class PersonalSaludCreateSerializer(serializers.Serializer):
    """Crea usuario Django + perfil PersonalSalud en una sola operación."""

    # Datos del usuario
    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    password = serializers.CharField(write_only=True, min_length=6)

    # Datos del perfil
    item_min_salud = serializers.CharField(max_length=20)
    rol = serializers.ChoiceField(choices=PersonalSalud.ROLES)
    especialidad = serializers.PrimaryKeyRelatedField(
        queryset=Especialidad.objects.all(), required=False, allow_null=True, default=None
    )
    telefono = serializers.CharField(
        max_length=30, required=False, allow_blank=True, default=""
    )

    def validate_username(self, value):
        value = value.strip()
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("El nombre de usuario ya está en uso.")
        return value

    def validate_item_min_salud(self, value):
        value = value.strip().upper()
        if not re.match(r"^[A-Z]{3}-\d{3}$", value):
            raise serializers.ValidationError("Formato requerido: 3 letras, guión, 3 números (ej. MED-001).")
        if PersonalSalud.objects.filter(item_min_salud=value).exists():
            raise serializers.ValidationError("El Ítem MIN Salud ya está registrado.")
        return value

    def validate(self, attrs):
        if attrs.get("rol") == PersonalSalud.ROL_MEDICO and not attrs.get("especialidad"):
            raise serializers.ValidationError(
                {"especialidad": "La especialidad es obligatoria para rol 'medico'."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            first_name=validated_data["first_name"].strip(),
            last_name=validated_data["last_name"].strip(),
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )
        telefono = validated_data.get("telefono", "").strip() or None
        personal = PersonalSalud.objects.create(
            user=user,
            item_min_salud=validated_data["item_min_salud"],
            rol=validated_data["rol"],
            especialidad=validated_data.get("especialidad"),
            telefono=telefono,
        )
        return personal

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "user": {
                "id": instance.user.id,
                "username": instance.user.username,
                "first_name": instance.user.first_name,
                "last_name": instance.user.last_name,
                "email": instance.user.email,
            },
            "item_min_salud": instance.item_min_salud,
            "rol": instance.rol,
            "especialidad": {"id": instance.especialidad.id, "nombre": instance.especialidad.nombre}
            if instance.especialidad else None,
            "telefono": instance.telefono,
            "is_active": instance.is_active,
        }


class PersonalSaludUpdateSerializer(serializers.ModelSerializer):
    """Solo campos editables post-creación (el usuario no se puede cambiar)."""

    class Meta:
        model = PersonalSalud
        fields = ["id", "user", "item_min_salud", "rol", "especialidad", "telefono", "is_active"]
        read_only_fields = ["id", "user", "is_active"]

    def validate_item_min_salud(self, value):
        value = value.strip().upper()
        if not re.match(r"^[A-Z]{3}-\d{3}$", value):
            raise serializers.ValidationError("Formato requerido: 3 letras, guión, 3 números (ej. MED-001).")
        qs = PersonalSalud.objects.filter(item_min_salud=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("El Ítem MIN Salud ya está registrado.")
        return value

    def validate(self, attrs):
        rol = attrs.get("rol", getattr(self.instance, "rol", None))
        especialidad = attrs.get("especialidad", getattr(self.instance, "especialidad", None))
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
            "first_name": instance.user.first_name,
            "last_name": instance.user.last_name,
        }
        data["especialidad"] = (
            {"id": instance.especialidad.id, "nombre": instance.especialidad.nombre}
            if instance.especialidad else None
        )
        return data


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
            "first_name": instance.user.first_name,
            "last_name": instance.user.last_name,
        }
        data["especialidad"] = (
            {"id": instance.especialidad.id, "nombre": instance.especialidad.nombre}
            if instance.especialidad else None
        )
        return data
