import datetime

import stripe
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from Tenants.models import Tenant
from .models import SuscripcionTenant
from .serializers import SuscripcionTenantSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY

_PLAN_LABEL = {
    'BASICO':      'Plan Básico Histolink',
    'PROFESIONAL': 'Plan Profesional Histolink',
    'ENTERPRISE':  'Plan Enterprise Histolink',
}


# ── Superadmin: lista todas las suscripciones ─────────────────────────────────

class ListarSuscripcionesView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        # Garantiza que cada tenant tenga su registro de suscripción
        tenants = Tenant.objects.all().order_by('nombre')
        subs = []
        for tenant in tenants:
            sub, _ = SuscripcionTenant.objects.get_or_create(tenant=tenant)
            subs.append(sub)
        return Response(SuscripcionTenantSerializer(subs, many=True).data)


# ── Superadmin: detalle / edición de una suscripción ─────────────────────────

class DetalleSuscripcionView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def _get_o_crear(self, tenant_id):
        tenant = Tenant.objects.get(pk=tenant_id)
        sub, _ = SuscripcionTenant.objects.get_or_create(tenant=tenant)
        return sub

    def get(self, request, tenant_id):
        try:
            sub = self._get_o_crear(tenant_id)
        except Tenant.DoesNotExist:
            return Response({'detail': 'Tenant no encontrado.'}, status=404)
        return Response(SuscripcionTenantSerializer(sub).data)

    def patch(self, request, tenant_id):
        try:
            sub = self._get_o_crear(tenant_id)
        except Tenant.DoesNotExist:
            return Response({'detail': 'Tenant no encontrado.'}, status=404)
        ser = SuscripcionTenantSerializer(sub, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)


# ── Superadmin: genera link de pago Stripe para la mensualidad de un tenant ──

class CrearPagoSaaSView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, tenant_id):
        try:
            tenant = Tenant.objects.get(pk=tenant_id)
        except Tenant.DoesNotExist:
            return Response({'detail': 'Tenant no encontrado.'}, status=404)

        sub, _ = SuscripcionTenant.objects.get_or_create(tenant=tenant)

        descripcion = f"{_PLAN_LABEL.get(sub.plan, 'Plan Histolink')} — {tenant.nombre}"

        try:
            session = stripe.checkout.Session.create(
                mode='payment',
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': int(sub.monto_mensual * 100),
                        'product_data': {'name': descripcion},
                    },
                    'quantity': 1,
                }],
                metadata={
                    'tipo':            'saas_suscripcion',
                    'tenant_id':       str(tenant_id),
                    'suscripcion_id':  str(sub.id),
                },
                success_url=f"{settings.FRONTEND_URL}/saas/pago/exito?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.FRONTEND_URL}/saas/pago/cancelado",
            )
        except stripe.error.StripeError as e:
            return Response(
                {'detail': f'Error al crear sesión de pago: {str(e)}'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        sub.stripe_session_id = session.id
        sub.save(update_fields=['stripe_session_id'])

        return Response({'checkout_url': session.url, 'session_id': session.id}, status=201)


# ── Webhook Stripe ─────────────────────────────────────────────────────────────

@csrf_exempt
@require_POST
def webhook_saas(request):
    payload    = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        return JsonResponse({'detail': 'Firma de webhook inválida.'}, status=400)

    if event['type'] == 'checkout.session.completed':
        data_obj = event['data']['object']
        metadata = data_obj.get('metadata', {})

        if metadata.get('tipo') != 'saas_suscripcion':
            return HttpResponse(status=200)

        try:
            sub = SuscripcionTenant.objects.get(pk=metadata.get('suscripcion_id'))
        except SuscripcionTenant.DoesNotExist:
            return HttpResponse(status=200)

        hoy = timezone.now().date()
        sub.estado            = SuscripcionTenant.Estado.ACTIVA
        sub.fecha_ultimo_pago = timezone.now()
        sub.fecha_inicio      = sub.fecha_inicio or hoy
        sub.fecha_vencimiento = hoy + datetime.timedelta(days=30)
        sub.stripe_session_id = data_obj.get('id', '')
        sub.save()

    return HttpResponse(status=200)


# ── Vista para el propio tenant (Director/Admin) ──────────────────────────────

class MiSuscripcionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request, 'tenant') or request.tenant is None:
            return Response({'detail': 'No hay tenant asociado a este usuario.'}, status=400)
        sub, _ = SuscripcionTenant.objects.get_or_create(tenant=request.tenant)
        return Response(SuscripcionTenantSerializer(sub).data)
