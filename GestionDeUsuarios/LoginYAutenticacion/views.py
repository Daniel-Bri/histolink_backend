"""
GestionDeUsuarios/LoginYAutenticacion/views.py

Vistas del sistema de autenticación de Histolink.
Todos los endpoints bajo /api/auth/.
"""

from rest_framework import generics, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.cache import caches
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.conf import settings

try:
    from SeguridadAvanzadaYAdministracion.Auditoria.audit_utils import registrar_acceso as _registrar_acceso
    _AUDIT_DISPONIBLE = True
except Exception:
    _AUDIT_DISPONIBLE = False

from .serializers import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    LogoutSerializer,
    ChangePasswordSerializer,
    UserSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)
from .models import PasswordResetToken

# Ventana de bloqueo por IP tras superar intentos fallidos de login (debe coincidir con el TTL de la caché).
LOGIN_RATE_LIMIT_WINDOW_SEC = 60


def _bump_login_failure_count(cache, cache_key, timeout=LOGIN_RATE_LIMIT_WINDOW_SEC):
    """Incrementa intentos fallidos de forma atómica (evita condiciones de carrera)."""
    if not cache.add(cache_key, 1, timeout=timeout):
        cache.incr(cache_key)


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

    Response 429 (demasiados intentos fallidos desde esta IP):
        { detail, retry_after }; cabecera Retry-After (segundos).
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        # 1. Obtener la IP del request
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        ip = ip or "unknown"

        # 2. Construir la clave Redis
        cache_key = f"login_attempts:{ip}"
        cache = caches["rate_limit"]

        # 3. Consultar el contador
        attempts = cache.get(cache_key, 0) or 0

        # 4. Si el contador >= 10, retornar Response
        if attempts >= 10:
            wait = LOGIN_RATE_LIMIT_WINDOW_SEC
            return Response(
                {
                    "detail": (
                        "Se superó el número máximo de intentos de inicio de sesión "
                        "desde esta dirección. Espera antes de volver a intentarlo."
                    ),
                    "retry_after": wait,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": str(wait)},
            )

        try:
            response = super().post(request, *args, **kwargs)
        except APIException as exc:
            # SimpleJWT lanza AuthenticationFailed (401) por credenciales inválidas/inactivas.
            # No incrementar por ValidationError u otros 4xx (p. ej. body mal formado → 400).
            if exc.status_code == status.HTTP_401_UNAUTHORIZED:
                _bump_login_failure_count(cache, cache_key)
            raise

        if response.status_code == status.HTTP_200_OK:
            cache.delete(cache_key)
            if _AUDIT_DISPONIBLE:
                try:
                    user = User.objects.get(username=request.data.get('username', ''))
                    _registrar_acceso('LOGIN', user, request)
                except Exception:
                    pass

        return response



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
        if _AUDIT_DISPONIBLE:
            try:
                _registrar_acceso('LOGOUT', request.user, request)
            except Exception:
                pass
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


# ── Recuperación de Contraseña (Forgot / Reset) ─────────────────────────

_FORGOT_RESPONSE = {'detail': 'Si el correo está registrado, recibirás un código de 6 dígitos en tu email.'}


class ForgotPasswordView(APIView):
    """
    POST /api/auth/forgot-password/

    Genera un código de 6 dígitos y lo envía al email del usuario.
    La respuesta es siempre la misma (no revela si el email existe).

    Body:
        email (string)

    Response 200:
        { detail: "Si el correo..." }
    """
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].strip().lower()

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(_FORGOT_RESPONSE, status=status.HTTP_200_OK)

        try:
            token = PasswordResetToken.create_for_user(user)
        except Exception:
            return Response(
                {'error': 'Error interno al generar el código. La tabla de tokens puede no existir — ejecuta las migraciones.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            send_mail(
                subject='Código de recuperación — Histolink',
                message=(
                    f'Hola {user.first_name or user.username},\n\n'
                    f'Tu código de recuperación de contraseña es:\n\n'
                    f'        {token.code}\n\n'
                    f'Este código es válido por 15 minutos.\n'
                    f'Si no solicitaste este código, ignora este correo.\n\n'
                    f'— Equipo Histolink'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as smtp_exc:
            return Response(
                {'error': f'SMTP error: {type(smtp_exc).__name__}: {smtp_exc}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(_FORGOT_RESPONSE, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    """
    POST /api/auth/reset-password/

    Valida el código enviado por email y cambia la contraseña.

    Body:
        email, code (6 dígitos), new_password, new_password_confirm

    Response 200:
        { detail: "Contraseña actualizada exitosamente." }

    Response 400:
        { error: "Código inválido o expirado." }
    """
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email'].strip().lower()
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']

        _ERROR = {'error': 'Código inválido o expirado.'}

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(_ERROR, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = PasswordResetToken.objects.get(user=user, code=code, used=False)
        except PasswordResetToken.DoesNotExist:
            return Response(_ERROR, status=status.HTTP_400_BAD_REQUEST)

        if not token.is_valid():
            return Response(_ERROR, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        token.used = True
        token.save()

        return Response(
            {'detail': 'Contraseña actualizada exitosamente.'},
            status=status.HTTP_200_OK,
        )


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
