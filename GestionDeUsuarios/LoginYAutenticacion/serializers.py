"""
GestionDeUsuarios/LoginYAutenticacion/serializers.py

Serializers para el sistema de autenticación de Histolink.
Usa auth_user de Django + JWT de simplejwt.
"""

from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken


# ── Serializer de Grupo ─────────────────────────────────────────────────

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("id", "name")


# ── Serializer de Usuario (lectura) ─────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    """Serializa auth_user para perfil y respuestas."""
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "date_joined",
            "last_login",
            "groups",
        )
        read_only_fields = fields


# ── Registro ────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.Serializer):
    """
    Registro de usuario nuevo.
    Crea la entrada en auth_user con contraseña hasheada (PBKDF2+SHA256).
    """
    username = serializers.CharField(
        max_length=150,
        help_text="Nombre de usuario único para login.",
    )
    email = serializers.EmailField(
        help_text="Correo electrónico del usuario.",
    )
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Contraseña (mínimo 8 caracteres).",
    )
    password_confirm = serializers.CharField(
        write_only=True,
        help_text="Confirmación de contraseña.",
    )
    first_name = serializers.CharField(
        max_length=150,
        required=False,
        default="",
        help_text="Nombre (opcional, se usa personal_salud en el sistema clínico).",
    )
    last_name = serializers.CharField(
        max_length=150,
        required=False,
        default="",
        help_text="Apellido (opcional).",
    )

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Ya existe un usuario con este nombre de usuario."
            )
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Ya existe un usuario con este correo electrónico."
            )
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Las contraseñas no coinciden."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        return user


# ── Login (JWT personalizado) ───────────────────────────────────────────

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extiende el login JWT para incluir datos del usuario en la respuesta.
    Retorna: access, refresh, user (id, username, email, groups).
    """

    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user
        groups = list(user.groups.values_list("name", flat=True))

        data["user"] = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "groups": groups,
        }
        return data


# ── Logout ──────────────────────────────────────────────────────────────

class LogoutSerializer(serializers.Serializer):
    """
    Recibe el refresh token y lo agrega a token_blacklist_blacklistedtoken.
    Esto invalida el refresh token — el access token sigue valido hasta que expire.
    """
    refresh = serializers.CharField(
        help_text="Refresh token JWT a invalidar.",
    )

    def validate_refresh(self, value):
        try:
            self.token = RefreshToken(value)
        except Exception:
            raise serializers.ValidationError(
                "Token de refresh inválido o ya expirado."
            )
        return value

    def save(self, **kwargs):
        self.token.blacklist()


# ── Cambio de Contraseña ────────────────────────────────────────────────

class ChangePasswordSerializer(serializers.Serializer):
    """Cambiar contraseña del usuario autenticado."""
    old_password = serializers.CharField(
        write_only=True,
        help_text="Contraseña actual.",
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Nueva contraseña (mínimo 8 caracteres).",
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        help_text="Confirmación de la nueva contraseña.",
    )

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual es incorrecta.")
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Las contraseñas nuevas no coinciden."}
            )
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user
