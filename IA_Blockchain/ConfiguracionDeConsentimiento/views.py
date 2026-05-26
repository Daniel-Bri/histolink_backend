import csv
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, status, decorators, permissions
from rest_framework.response import Response

from .models import TipoConsentimiento, Consentimiento
from .serializers import (
    TipoConsentimientoSerializer, 
    ConsentimientoSerializer, 
    RevocacionSerializer
)
from .permissions import EsDirectorOAdmin, ConsentimientoPermission


class TipoConsentimientoViewSet(viewsets.ModelViewSet):
    """
    API para la configuración de tipos de consentimiento.
    Solo accesible por Directores o Administradores.
    """
    queryset = TipoConsentimiento.objects.all()
    serializer_class = TipoConsentimientoSerializer
    permission_classes = [EsDirectorOAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        
        # Filtro por nombre
        nombre = params.get('nombre')
        if nombre:
            qs = qs.filter(nombre__icontains=nombre)
            
        # Filtro por activo (por defecto True en list)
        activo = params.get('activo')
        if activo:
            qs = qs.filter(activo=activo.lower() in ('1', 'true', 'yes'))
        elif self.action == 'list':
            qs = qs.filter(activo=True)
            
        return qs

    def perform_destroy(self, instance):
        """Borrado lógico por defecto."""
        instance.activo = False
        instance.save()


class ConsentimientoViewSet(viewsets.ModelViewSet):
    """
    API para el registro y consulta de consentimientos informados.
    """
    queryset = Consentimiento.objects.all()
    serializer_class = ConsentimientoSerializer
    permission_classes = [ConsentimientoPermission]

    def get_queryset(self):
        qs = super().get_queryset().select_related('paciente', 'tipo', 'registrado_por')
        user = self.request.user
        params = self.request.query_params
        
        # 1. Filtro de seguridad: Pacientes solo ven sus propios consentimientos
        if user.groups.filter(name='Paciente').exists():
            qs = qs.filter(paciente__email=user.email)
        else:
            # Filtro por paciente_id para médicos/admins
            paciente_id = params.get('paciente_id')
            if paciente_id:
                qs = qs.filter(paciente_id=paciente_id)
        
        # 2. Filtro por tipo
        tipo_id = params.get('tipo_id')
        if tipo_id:
            qs = qs.filter(tipo_id=tipo_id)
            
        # 3. Filtro por estado
        estado = params.get('estado')
        if estado:
            qs = qs.filter(estado=estado.upper())
            
        # 4. Filtro por vigencia (shortcut)
        if params.get('vigente', '').lower() in ('1', 'true', 'yes'):
            qs = qs.filter(
                estado=Consentimiento.Estado.OTORGADO
            ).filter(
                Q(vigente_hasta__isnull=True) | Q(vigente_hasta__gt=timezone.now())
            )
            
        # 5. Rango de fechas
        desde = params.get('otorgado_en_desde')
        hasta = params.get('otorgado_en_hasta')
        if desde:
            qs = qs.filter(otorgado_en__gte=desde)
        if hasta:
            qs = qs.filter(otorgado_en__lte=hasta)
            
        # 6. Búsqueda de texto libre
        search = params.get('search')
        if search:
            qs = qs.filter(
                Q(testigo_nombre__icontains=search) | 
                Q(observaciones__icontains=search) |
                Q(paciente__nombres__icontains=search) |
                Q(paciente__apellido_paterno__icontains=search)
            )
            
        return qs.order_by('-otorgado_en')

    @decorators.action(detail=True, methods=['post'], url_path='revocar')
    def revocar(self, request, pk=None):
        """
        Endpoint específico para la revocación de un consentimiento.
        """
        consentimiento = self.get_object()
        
        if consentimiento.estado == Consentimiento.Estado.REVOCADO:
            return Response(
                {"detail": "Este consentimiento ya ha sido revocado."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer = RevocacionSerializer(consentimiento, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(ConsentimientoSerializer(consentimiento).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @decorators.action(detail=False, methods=['get'])
    def exportar(self, request):
        """
        Exporta el listado actual (respetando filtros) a un archivo CSV.
        """
        queryset = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv')
        filename = f"consentimientos_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Establecimiento', 'Paciente', 'CI Paciente', 'Tipo', 
            'Estado', 'Otorgado En', 'Vigente Hasta', 'Registrado Por', 
            'Testigo', 'Observaciones'
        ])
        
        for c in queryset:
            writer.writerow([
                c.id,
                c.tenant.nombre,
                str(c.paciente),
                f"{c.paciente.ci}-{c.paciente.ci_complemento}" if c.paciente.ci_complemento else c.paciente.ci,
                c.tipo.nombre,
                c.get_estado_display(),
                c.otorgado_en.strftime('%Y-%m-%d %H:%M'),
                c.vigente_hasta.strftime('%Y-%m-%d %H:%M') if c.vigente_hasta else 'Indefinida',
                c.registrado_por.get_full_name() or c.registrado_por.username,
                c.testigo_nombre,
                c.observaciones
            ])
            
        return response
