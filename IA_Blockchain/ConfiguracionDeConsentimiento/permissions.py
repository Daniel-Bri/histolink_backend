from rest_framework import permissions


class EsDirectorOAdmin(permissions.BasePermission):
    """
    Permite acceso completo a Directores/Admin. 
    Permite solo lectura a Médicos/Enfermeras.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_groups = request.user.groups.values_list('name', flat=True)
        
        if request.user.is_superuser or 'Director' in user_groups or 'Administrativo' in user_groups:
            return True
            
        if request.method in permissions.SAFE_METHODS:
            return 'Médico' in user_groups or 'Enfermera' in user_groups
            
        return False


class EsPersonalSalud(permissions.BasePermission):
    """
    Permite lectura y creación a personal médico/enfermería.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.groups.filter(name__in=['Médico', 'Enfermera']).exists()


class EsPaciente(permissions.BasePermission):
    """
    Permite solo lectura a pacientes.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.groups.filter(name='Paciente').exists()


class ConsentimientoPermission(permissions.BasePermission):
    """
    Permiso unificado para la gestión de consentimientos:
    - Admin/Director: CRUD completo.
    - Médico/Enfermera: Lectura, Creación y Revocación.
    - Recepcionista/Administrativo: Solo lectura.
    - Paciente: Solo lectura (y solo de sus propios registros, filtrado en queryset).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Grupos con acceso total (o parcial)
        user_groups = request.user.groups.values_list('name', flat=True)
        
        if request.user.is_superuser or 'Director' in user_groups or 'Administrativo' in user_groups:
            return True
            
        if 'Médico' in user_groups or 'Enfermera' in user_groups:
            # Pueden leer (GET), crear (POST) y usar acciones como 'revocar' (POST)
            # No pueden borrar (DELETE) ni editar arbitrariamente (PATCH/PUT) a menos que se defina lo contrario
            if request.method in permissions.SAFE_METHODS or request.method == 'POST':
                return True
            # Permitir PATCH solo para campos específicos podría hacerse aquí o en el serializer
            return request.method == 'PATCH'

        if 'Paciente' in user_groups:
            return request.method in permissions.SAFE_METHODS
            
        return False

    def has_object_permission(self, request, view, obj):
        user_groups = request.user.groups.values_list('name', flat=True)
        
        if request.user.is_superuser or 'Director' in user_groups or 'Administrativo' in user_groups:
            return True
            
        if 'Médico' in user_groups or 'Enfermera' in user_groups:
            return True
            
        if 'Paciente' in user_groups:
            # El paciente solo puede ver sus propios consentimientos.
            # Se asume que el email del User coincide con el email del Paciente.
            # En un sistema real, se usaría una relación OneToOne o el ID del paciente en el token JWT.
            return obj.paciente.email == request.user.email
            
        return False
