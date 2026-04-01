"""
GestionDeUsuarios/LoginYAutenticacion/urls.py

Endpoints de autenticación de Histolink.
Incluidos en kardex/urls.py bajo el prefijo 'api/auth/'.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from . import views

app_name = "LoginYAutenticacion"

urlpatterns = [
    # Registro
    path("register/", views.RegisterView.as_view(), name="register"),

    # Login — retorna access + refresh + datos del usuario
    path("login/", views.CustomTokenObtainPairView.as_view(), name="login"),

    # Logout — blacklist del refresh token
    path("logout/", views.LogoutView.as_view(), name="logout"),

    # Refresh — obtener nuevo access token usando el refresh token
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Verify — verificar si un token es válido
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),

    # Cambio de contraseña
    path("change-password/", views.ChangePasswordView.as_view(), name="change_password"),

    # Perfil del usuario autenticado
    path("profile/", views.UserProfileView.as_view(), name="profile"),
]
