"""
GestionDeUsuarios/LoginYAutenticacion/urls.py

Endpoints de autenticación de Histolink.
Incluidos en kardex/urls.py bajo el prefijo 'api/auth/'.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenBlacklistView

from . import views

app_name = "LoginYAutenticacion"

urlpatterns = [
    # Registro
    path("register/", views.RegisterView.as_view(), name="register"),

    # Login — retorna access + refresh + datos del usuario
    path("login/", views.CustomTokenObtainPairView.as_view(), name="login"),

    # Logout — blacklist del refresh token
    path("logout/", views.LogoutView.as_view(), name="logout"),

    # Token estándar de simplejwt (endpoint puro) 
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),

    # Refresh — obtener nuevo access token usando el refresh token
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Blacklist — invalidar refresh token
    path("token/blacklist/", TokenBlacklistView.as_view(), name="token_blacklist"),

    # Verify — verificar si un token es válido
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),

    # Cambio de contraseña
    path("change-password/", views.ChangePasswordView.as_view(), name="change_password"),

    # Perfil del usuario autenticado
    path("profile/", views.UserProfileView.as_view(), name="profile"),
]
