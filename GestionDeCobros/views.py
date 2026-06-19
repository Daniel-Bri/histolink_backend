import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from AtencionClinica.AperturaFichaYColaDeAtencion.models import Ficha
from GestionDeUsuarios.LoginYAutenticacion.permissions import EsAdmin

from .models import Cobro
from .serializers import CrearSesionCobroSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY

from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from SeguridadAvanzadaYAdministracion.Auditoria.audit_utils import registrar_evento

from .serializers import CobroSerializer
from rest_framework.generics import ListAPIView

class CrearSesionCobroView(APIView):
    permission_classes = [IsAuthenticated, EsAdmin]

    def post(self, request):
        serializer = CrearSesionCobroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        ficha = get_object_or_404(Ficha, id=data["ficha_id"])

        if ficha.estado == Ficha.Estado.CERRADA:
            return Response(
                {"detail": "No se puede generar un cobro para una ficha cerrada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.tenant is not None and ficha.paciente.tenant_id != request.tenant.id:
            return Response(
                {"detail": "No tienes acceso a esta ficha."},
                status=status.HTTP_403_FORBIDDEN,
            )

        cobro = Cobro.objects.create(
            tenant=request.tenant,
            ficha=ficha,
            paciente=ficha.paciente,
            concepto=data["concepto"],
            monto=data["monto"],
            estado=Cobro.Estado.PENDIENTE,
        )

        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": int(data["monto"] * 100),
                        "product_data": {"name": data["concepto"]},
                    },
                    "quantity": 1,
                }],
                success_url=f"{settings.FRONTEND_URL}/cobros/exito?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.FRONTEND_URL}/cobros/cancelado",
            )
        except stripe.error.StripeError as e:
            cobro.delete()
            return Response(
                {"detail": f"Error al crear la sesión de pago: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        cobro.stripe_session_id = session.id
        cobro.save(update_fields=["stripe_session_id"])

        return Response(
            {"cobro_id": cobro.id, "checkout_url": session.url},
            status=status.HTTP_201_CREATED,
        )
    

class AnularCobroView(APIView):
    permission_classes = [IsAuthenticated, EsAdmin]

    def post(self, request, pk):
        cobro = get_object_or_404(Cobro, pk=pk)

        if request.tenant is not None and cobro.tenant_id != request.tenant.id:
            return Response(
                {"detail": "No tienes acceso a este cobro."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if cobro.estado != Cobro.Estado.PENDIENTE:
            return Response(
                {"detail": f"No se puede anular un cobro en estado {cobro.estado}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cobro.estado = Cobro.Estado.ANULADO
        cobro.save(update_fields=["estado"])
        registrar_evento("ANULAR", cobro, cambios={"estado": "ANULADO"}, request=request)

        return Response(CobroSerializer(cobro).data, status=status.HTTP_200_OK)


@csrf_exempt
@require_POST
def webhook_cobro(request):
    """
    Webhook de Stripe. Sin JWT (Stripe no envía token) — por eso es una vista
    de Django normal, no un APIView de DRF (así evitamos los permisos/autenticación
    por defecto del proyecto).
    """
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return JsonResponse({"detail": "Firma de webhook inválida."}, status=400)

    event_type = event["type"]
    data_object = event["data"]["object"]
    session_id = data_object.get("id")

    if event_type == "checkout.session.completed":
        cobro = Cobro.objects.filter(stripe_session_id=session_id).first()
        if cobro and cobro.estado == Cobro.Estado.PENDIENTE:
            cobro.estado = Cobro.Estado.PAGADO
            cobro.fecha_pago = timezone.now()
            cobro.save(update_fields=["estado", "fecha_pago"])
            registrar_evento("UPDATE", cobro, cambios={"estado": "PAGADO", "origen": "webhook_stripe"})

    elif event_type == "checkout.session.expired":
        cobro = Cobro.objects.filter(stripe_session_id=session_id).first()
        if cobro and cobro.estado == Cobro.Estado.PENDIENTE:
            cobro.estado = Cobro.Estado.EXPIRADO
            cobro.save(update_fields=["estado"])
            registrar_evento("UPDATE", cobro, cambios={"estado": "EXPIRADO", "origen": "webhook_stripe"})

    return HttpResponse(status=200)


class ListarCobrosView(ListAPIView):
    serializer_class = CobroSerializer
    permission_classes = [IsAuthenticated, EsAdmin]

    def get_queryset(self):
        qs = Cobro.objects.all().order_by("-creado_en")
        ficha_id = self.request.query_params.get("ficha")
        if ficha_id:
            qs = qs.filter(ficha_id=ficha_id)
        return qs