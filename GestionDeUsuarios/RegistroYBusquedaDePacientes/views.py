from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from .models import Paciente
from .serializers import PacienteSerializer
from GestionDeUsuarios.LoginYAutenticacion.permissions import (
    EsMedicoEnfermeroOAdmin,
    EsAdminODirector,
)


class PacientePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class PacienteViewSet(viewsets.ModelViewSet):
    serializer_class = PacienteSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['ci', 'apellido_paterno', 'apellido_materno']
    pagination_class = PacientePagination

    def get_queryset(self):
        return Paciente.objects.all().order_by('-creado_en')

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        if self.action in ['create', 'update', 'partial_update']:
            return [EsMedicoEnfermeroOAdmin()]
        if self.action == 'destroy':
            return [EsAdminODirector()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant, creado_por=self.request.user)
