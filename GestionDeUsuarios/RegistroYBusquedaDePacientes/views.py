from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from .models import Paciente
from .serializers import PacienteSerializer
from AtencionClinica.ConsultaMedicaSOAP.models import Consulta
from AtencionClinica.RegistroDeTriaje.models import Triaje
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
        qs = Paciente.objects.all().order_by('-creado_en')
        mis_pacientes = (self.request.query_params.get('mis_pacientes') or '').lower() in ('1', 'true', 'si', 'yes')
        if not mis_pacientes:
            return qs

        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        if user.is_superuser or user.groups.filter(name__in=['Director', 'Administrativo', 'Auditor']).exists():
            return qs

        if user.groups.filter(name='Médico').exists():
            paciente_ids = set(
                Consulta.objects.filter(medico=user).values_list('ficha__paciente_id', flat=True)
            )
            paciente_ids.update(
                Paciente.objects.filter(creado_por=user).values_list('id', flat=True)
            )
            return qs.filter(id__in=paciente_ids)

        if user.groups.filter(name='Enfermera').exists():
            paciente_ids = set(
                Triaje.objects.filter(enfermera=user).values_list('ficha__paciente_id', flat=True)
            )
            return qs.filter(id__in=paciente_ids)

        return qs.none()

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
