"""
URL configuration for Histolink project.

Rutas principales del sistema clínico.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # Autenticación (register, login, logout, profile, change-password, token refresh/verify)
    path("api/auth/", include("authentication.urls")),
]
