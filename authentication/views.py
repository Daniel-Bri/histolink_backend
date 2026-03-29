"""
authentication/views.py

Vistas del sistema de autenticación de Histolink.
Todos los endpoints bajo /api/auth/.
"""

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    LogoutSerializer,
    ChangePasswordSerializer,
    UserSerializer,
)


# ── Registro ────────────────────────────────────────────────────────────

class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/

    Registra un nuevo usuario en auth_user.
    No requiere autenticación (AllowAny).

    Body:
        username, email, password, password_confirm
        first_name (optional), last_name (optional)

    Response 201:
        { message, user: { id, username, email, ... } }
    """
    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        user_data = UserSerializer(user).data
        return Response(
            {
                "message": "Usuario registrado exitosamente.",
                "user": user_data,
            },
            status=status.HTTP_201_CREATED,
        )


# ── Login (JWT con datos de usuario) ────────────────────────────────────

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/auth/login/

    Autenticación con username + password.
    Retorna access token, refresh token, y datos del usuario.

    Body:
        username, password

    Response 200:
        { access, refresh, user: { id, username, email, groups, ... } }
    """
    serializer_class = CustomTokenObtainPairSerializer


# ── Logout (Blacklist del Refresh Token) ────────────────────────────────

class LogoutView(APIView):
    """
    POST /api/auth/logout/

    Invalida el refresh token (lo agrega a token_blacklist_blacklistedtoken).
    El access token sigue válido hasta su expiración natural (15 min).

    Body:
        refresh (string — el refresh token JWT)

    Response 200:
        { message: "Sesión cerrada exitosamente." }
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Sesión cerrada exitosamente."},
            status=status.HTTP_200_OK,
        )


# ── Perfil del usuario autenticado ──────────────────────────────────────

class UserProfileView(APIView):
    """
    GET /api/auth/profile/

    Retorna el perfil del usuario autenticado.
    Requiere Bearer token en el header Authorization.

    Response 200:
        { id, username, email, first_name, last_name, is_active,
          is_staff, date_joined, last_login, groups: [...] }
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ── Cambio de Contraseña ────────────────────────────────────────────────

class ChangePasswordView(APIView):
    """
    PUT /api/auth/change-password/

    Cambia la contraseña del usuario autenticado.
    Requiere Bearer token.

    Body:
        old_password, new_password, new_password_confirm

    Response 200:
        { message: "Contraseña actualizada exitosamente." }
    """
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Contraseña actualizada exitosamente."},
            status=status.HTTP_200_OK,
        )
