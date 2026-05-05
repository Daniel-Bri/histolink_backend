from .thread_local import set_current_request


class AuditMiddleware:
    """Middleware para capturar el request en cada hilo de ejecución."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Antes de la vista: guardar el request
        set_current_request(request)
        
        response = self.get_response(request)
        
        # Después de la vista: limpiar el request
        set_current_request(None)
        
        return response
