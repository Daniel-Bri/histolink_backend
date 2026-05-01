"""
URL configuration for Histolink project.
Rutas principales del sistema clínico.
"""
from django.contrib import admin
from django.urls import include, path

from GestionDeUsuarios.GestionDePersonalDeSalud.urls import especialidades_urlpatterns
from GestionDeUsuarios.GestionDePersonalDeSalud.views import usuarios_sin_perfil

urlpatterns = [
    path("admin/", admin.site.urls),

    # Multitenant — establecimientos
    path("api/tenants/", include("Tenants.urls")),

    # GestionDeUsuarios — CU1: Login y Autenticación
    path("api/auth/", include("GestionDeUsuarios.LoginYAutenticacion.urls")),

    # GestionDeUsuarios — CU3: Registro y Búsqueda de Pacientes
    path("api/pacientes/", include("GestionDeUsuarios.RegistroYBusquedaDePacientes.urls")),

    # GestionDeUsuarios — CU4: Visualización del Expediente (T011)
    path("api/expediente/", include("GestionDeUsuarios.VisualizacionDelExpediente.urls")),

    # GestionDeUsuarios — CU5: Edición de Antecedentes Médicos (T008)
    path("api/antecedentes/", include("GestionDeUsuarios.EdicionDeAntecedentesMedicos.urls")),

    path("api/personal/", include("GestionDeUsuarios.GestionDePersonalDeSalud.urls")),

    path("api/especialidades/", include(especialidades_urlpatterns)),

    path("api/usuarios-sin-perfil/", usuarios_sin_perfil),

    path("api/clinica/", include("AtencionClinica.EmisionDeRecetaMedica.urls")),

    # AtencionClinica — CU7: Registro de Triaje (T004 / T005)
    path("api/triaje/", include("AtencionClinica.RegistroDeTriaje.urls")),
]