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