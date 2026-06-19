from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DispositivoFCM


class RegistrarTokenFCMView(APIView):
    """
    POST /api/notificaciones/token/
    Registra o actualiza el token FCM del dispositivo del usuario autenticado.

    Body: { "token": "...", "plataforma": "web" | "android" | "ios" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token      = request.data.get("token", "").strip()
        plataforma = request.data.get("plataforma", "web").strip().lower()

        if not token:
            return Response({"detail": "El token es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        if plataforma not in ("web", "android", "ios"):
            return Response({"detail": "Plataforma inválida. Use web, android o ios."}, status=status.HTTP_400_BAD_REQUEST)

        tenant = getattr(request, "tenant", None)

        # Upsert: si el token ya existe lo reactiva y actualiza usuario/tenant
        dispositivo, created = DispositivoFCM.objects.update_or_create(
            token=token,
            defaults={
                "user":       request.user,
                "tenant":     tenant,
                "plataforma": plataforma,
                "activo":     True,
            },
        )

        return Response(
            {"detail": "Token registrado correctamente.", "created": created},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class EliminarTokenFCMView(APIView):
    """
    DELETE /api/notificaciones/token/
    Desactiva el token FCM del dispositivo (al hacer logout).

    Body: { "token": "..." }
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        token = request.data.get("token", "").strip()
        if not token:
            return Response({"detail": "El token es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        updated = DispositivoFCM.objects.filter(
            token=token,
            user=request.user,
        ).update(activo=False)

        if updated:
            return Response({"detail": "Token desactivado."})
        return Response({"detail": "Token no encontrado."}, status=status.HTTP_404_NOT_FOUND)
