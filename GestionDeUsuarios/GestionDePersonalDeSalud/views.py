from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import PersonalSalud
from .serializers import PersonalSaludSerializer


class PersonalSaludViewSet(ModelViewSet):
    serializer_class = PersonalSaludSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PersonalSalud.objects.select_related("user", "especialidad")
        if self.action == "list":
            queryset = queryset.filter(is_active=True)
        return queryset

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])
