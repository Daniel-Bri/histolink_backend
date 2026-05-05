from django.apps import AppConfig


class AuditoriaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'SeguridadAvanzadaYAdministracion.Auditoria'
    verbose_name = 'Auditoría de Seguridad'

    def ready(self):
        import SeguridadAvanzadaYAdministracion.Auditoria.signals
