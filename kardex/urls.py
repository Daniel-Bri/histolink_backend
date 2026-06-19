"""
URL configuration for Histolink project.
Rutas principales del sistema clínico.
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from SeguridadAvanzadaYAdministracion.BreakGlass_Aprobacion import urls as breakglass_aprobacion_urls
from GestionDeUsuarios.GestionDePersonalDeSalud.urls import especialidades_urlpatterns
from GestionDeUsuarios.GestionDePersonalDeSalud.views import usuarios_sin_perfil

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

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

    # AtencionClinica — CU8: Consulta Médica SOAP
    path("api/consultas/", include("AtencionClinica.ConsultaMedicaSOAP.urls")),

    path("api/clinica/", include("AtencionClinica.EmisionDeRecetaMedica.urls")),

    # AtencionClinica — CU6: Ficha / cola
    path("api/", include("AtencionClinica.AperturaFichaYColaDeAtencion.urls")),

    # AtencionClinica — CU7: Registro de Triaje (T004 / T005)
    path("api/triaje/", include("AtencionClinica.RegistroDeTriaje.urls")),

    # AtencionClinica — CU10: órdenes de estudio (T009)
    path("api/", include("AtencionClinica.SolicitudDeEstudios.urls")),

    # Reportes — CU22: Producción y Flujo de Atención (T037/T038/T039)
    path("api/reportes/", include("SeguridadAvanzadaYAdministracion.ReporteProduccion.urls")),

    # SeguridadAvanzadaYAdministracion — CU20: Panel de Auditoría y Reportes SNIS (T036)
    path("api/auditoria/", include("SeguridadAvanzadaYAdministracion.PanelDeAuditoriaYReportesSNIS.urls")),

    # SeguridadAvanzadaYAdministracion — Backup / Restore / Gestiones Anuales
    path("api/admin/backup/", include("SeguridadAvanzadaYAdministracion.BackupRestore.urls")),

    # IA_Blockchain — CU16: Configuración de Consentimiento (T09)
    path("api/consentimientos/", include("IA_Blockchain.ConfiguracionDeConsentimiento.urls")),
    # IA_Blockchain — CU13: Predicción de Riesgos Clínicos (T004)
    path("api/ia/", include("IA_Blockchain.PrediccionDeRiesgosClinicos.urls")),
    # GestionDeIdentidadBlockchain — CU14: Gestión de Identidad Blockchain
    path('api/blockchain/', include('IA_Blockchain.GestionDeIdentidadBlockchain.urls')),
    # VerificacionDeIntegridadDocumentos — CU15: T007 verificar hash vs blockchain
    path('api/blockchain/', include('IA_Blockchain.VerificacionDeIntegridadDocumentos.urls')),
    # FirmaDigitalDeConsulta — CU11: T008 firmar consulta con SHA-256 + RSA
    path('api/', include('AtencionClinica.FirmaDigitalDeConsulta.urls')),
    # SeguridadAvanzadaYAdministracion — CU16: Break-Glass Solicitud
    path("api/seguridad/break-glass/", include("SeguridadAvanzadaYAdministracion.BreakGlass_Solicitud.urls")),

    # GestionDeCobros — CU23: Generación de Sesión de Cobro (T040)
    path("api/cobros/", include("GestionDeCobros.urls")),
    # SeguridadAvanzadaYAdministracion — CU17: Break-Glass Aprobación / Rechazo
    path(
        "api/emergencia/",
        include((breakglass_aprobacion_urls.urlpatterns, breakglass_aprobacion_urls.app_name), namespace="breakglass_emergencia"),
    ),
    path(
        "api/seguridad/break-glass/",
        include((breakglass_aprobacion_urls.urlpatterns, breakglass_aprobacion_urls.app_name), namespace="breakglass_aprobacion"),
    ),

    # Notificaciones Push — FCM token registro/eliminación
    path("api/notificaciones/", include("Notificaciones.urls")),

    # SaaS Billing — suscripciones de clínicas
    path("api/saas/", include("SaaSBilling.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
