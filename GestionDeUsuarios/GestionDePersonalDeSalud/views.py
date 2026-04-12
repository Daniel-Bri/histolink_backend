from django.contrib.auth.models import User
from django.core.cache import caches
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from GestionDeUsuarios.LoginYAutenticacion.permissions import EsAdminODirector
from .models import Especialidad, PersonalSalud
from .permissions import IsStaffOrAdminRole
from .serializers import EspecialidadSerializer, PersonalSaludSerializer, UserSerializer

ESPECIALIDAD_LIST_CACHE_KEY = "especialidades:list:v1"
ESPECIALIDAD_CACHE_TIMEOUT = 3600


def _invalidate_especialidad_list_cache() -> None:
    caches["especialidad_cache"].delete(ESPECIALIDAD_LIST_CACHE_KEY)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def usuarios_sin_perfil(request):
    qs = User.objects.filter(
        is_active=True,
        perfil_personal_salud__isnull=True,
    ).order_by("username")
    serializer = UserSerializer(qs, many=True)
    return Response(serializer.data)


class PersonalSaludViewSet(ModelViewSet):
    serializer_class = PersonalSaludSerializer
    # Gestión de personal: solo Administrativo y Director
    permission_classes = [EsAdminODirector]

    def get_queryset(self):
        queryset = PersonalSalud.objects.select_related("user", "especialidad")
        if self.action == "list":
            queryset = queryset.filter(is_active=True)
        return queryset

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])


class EspecialidadViewSet(ModelViewSet):
    queryset = Especialidad.objects.all()
    serializer_class = EspecialidadSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsStaffOrAdminRole()]

    def list(self, request, *args, **kwargs):
        cache = caches["especialidad_cache"]
        cached = cache.get(ESPECIALIDAD_LIST_CACHE_KEY)
        if cached is not None:
            return Response(cached)
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        cache.set(ESPECIALIDAD_LIST_CACHE_KEY, data, timeout=ESPECIALIDAD_CACHE_TIMEOUT)
        return Response(data)

    def perform_create(self, serializer):
        super().perform_create(serializer)
        _invalidate_especialidad_list_cache()

    def perform_update(self, serializer):
        super().perform_update(serializer)
        _invalidate_especialidad_list_cache()

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        _invalidate_especialidad_list_cache()
