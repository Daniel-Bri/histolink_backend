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

    # GestionDeUsuarios — CU3: Registro y Búsqueda de Pacientes
    path("api/pacientes/", include("GestionDeUsuarios.RegistroYBusquedaDePacientes.urls")),

    # GestionDeUsuarios — CU4: Visualización del Expediente (T011)
    path("api/expediente/", include("GestionDeUsuarios.VisualizacionDelExpediente.urls")),

    # GestionDeUsuarios — CU5: Edición de Antecedentes Médicos (T008)
    path("api/antecedentes/", include("GestionDeUsuarios.EdicionDeAntecedentesMedicos.urls")),

    path("api/personal/", include("GestionDeUsuarios.GestionDePersonalDeSalud.urls")),

    # AtencionClinica — CU6: Ficha / cola
    path("api/", include("AtencionClinica.AperturaFichaYColaDeAtencion.urls")),
]