import threading

_thread_local = threading.local()


def get_current_request():
    """Obtiene el objeto request del hilo actual."""
    return getattr(_thread_local, 'request', None)


def set_current_request(request):
    """Almacena el objeto request en el hilo actual."""
    _thread_local.request = request
