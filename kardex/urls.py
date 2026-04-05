"""
URL configuration for Histolink project.

Rutas principales del sistema clínico.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # GestionDeUsuarios — CU1: Login y Autenticación
    path("api/auth/", include("GestionDeUsuarios.LoginYAutenticacion.urls")),

    # GestionDeUsuarios — CU4: Visualización del Expediente (T011)
    path("api/pacientes/", include("GestionDeUsuarios.VisualizacionDelExpediente.urls")),
]
