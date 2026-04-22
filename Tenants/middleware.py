from .context import set_current_tenant, clear_current_tenant


class TenantMiddleware:
    """
    Lee el tenant_id del payload JWT en cada request y lo expone como:
      - request.tenant  (objeto Tenant o None)
      - threading.local (para acceso desde TenantManager sin pasar request)

    Se ubica después de AuthenticationMiddleware en MIDDLEWARE.
    Si el usuario no tiene tenant (superuser, anónimo), request.tenant = None
    y TenantManager devuelve registros sin filtrar (acceso total).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = self._resolve_tenant(request)
        request.tenant = tenant
        set_current_tenant(tenant)

        try:
            response = self.get_response(request)
        finally:
            clear_current_tenant()

        return response

    def _resolve_tenant(self, request):
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError
        from .models import Tenant

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None

        token_str = auth_header[7:]
        try:
            token = AccessToken(token_str)
            tenant_id = token.get('tenant_id')
            if not tenant_id:
                return None
            return Tenant.objects.filter(id=tenant_id, activo=True).first()
        except TokenError:
            return None
