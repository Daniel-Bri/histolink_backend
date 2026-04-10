from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import Paciente
from .serializers import PacienteSerializer


class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.all().order_by('-created_at')
    serializer_class = PacienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['ci', 'apellido_paterno', 'apellido_materno']