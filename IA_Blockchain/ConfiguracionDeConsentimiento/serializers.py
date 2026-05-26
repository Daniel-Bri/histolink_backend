from rest_framework import serializers
from django.utils import timezone
from django.db.models import Q
from .models import TipoConsentimiento, Consentimiento
from Tenants.context import get_current_tenant


class TipoConsentimientoSerializer(serializers.ModelSerializer):
    """
    Serializer para la configuración de tipos de consentimiento.
    """
    class Meta:
        model = TipoConsentimiento
        fields = [
            'id', 'nombre', 'descripcion', 'requiere_testigo', 
            'activo', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['tenant'] = get_current_tenant()
        return super().create(validated_data)


class ConsentimientoSerializer(serializers.ModelSerializer):
    """
    Serializer para el registro de consentimientos de pacientes.
    Incluye validaciones de negocio críticas.
    """
    paciente_nombre = serializers.ReadOnlyField(source='paciente.__str__')
    tipo_nombre = serializers.ReadOnlyField(source='tipo.nombre')
    registrado_por_nombre = serializers.ReadOnlyField(source='registrado_por.get_full_name')
    es_vigente = serializers.BooleanField(read_only=True)

    class Meta:
        model = Consentimiento
        fields = [
            'id', 'paciente', 'paciente_nombre', 'tipo', 'tipo_nombre',
            'estado', 'otorgado_en', 'vigente_hasta', 'registrado_por',
            'registrado_por_nombre', 'testigo_nombre', 'observaciones',
            'es_vigente'
        ]
        read_only_fields = [
            'id', 'otorgado_en', 'registrado_por', 'es_vigente'
        ]

    def validate(self, attrs):
        # 1. Obtener valores actuales o nuevos
        tipo = attrs.get('tipo', getattr(self.instance, 'tipo', None))
        paciente = attrs.get('paciente', getattr(self.instance, 'paciente', None))
        estado = attrs.get('estado', getattr(self.instance, 'estado', 'OTORGADO'))
        vigente_hasta = attrs.get('vigente_hasta', getattr(self.instance, 'vigente_hasta', None))
        testigo_nombre = attrs.get('testigo_nombre', getattr(self.instance, 'testigo_nombre', ""))

        # 2. Validación: Coherencia de fecha de vigencia
        # Solo validamos si se está estableciendo una nueva fecha de vigencia
        if 'vigente_hasta' in attrs and attrs['vigente_hasta']:
            if attrs['vigente_hasta'] < timezone.now():
                raise serializers.ValidationError(
                    {"vigente_hasta": "La fecha de vigencia no puede ser pasada."}
                )

        # 3. Validación: Testigo obligatorio
        if tipo and tipo.requiere_testigo:
            if not testigo_nombre or not testigo_nombre.strip():
                raise serializers.ValidationError(
                    {"testigo_nombre": f"El tipo de consentimiento '{tipo.nombre}' requiere un testigo."}
                )

        # 4. Validación: Unicidad activa (Regla de negocio principal)
        # Solo se valida si el estado es OTORGADO y estamos creando o cambiando a este estado
        if estado == Consentimiento.Estado.OTORGADO:
            # Buscamos consentimientos del mismo tipo y paciente que estén OTORGADOS y vigentes
            qs = Consentimiento.objects.filter(
                paciente=paciente,
                tipo=tipo,
                estado=Consentimiento.Estado.OTORGADO
            )
            
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            
            # Consideramos vigente si vigente_hasta es nulo o futuro
            active_consent = qs.filter(
                Q(vigente_hasta__isnull=True) | Q(vigente_hasta__gt=timezone.now())
            ).exists()

            if active_consent:
                raise serializers.ValidationError(
                    "El paciente ya tiene un consentimiento activo para este tipo. Debe revocarlo primero."
                )

        # 5. Validación: Transición de estado (REVOCADO es final)
        if self.instance and self.instance.estado == Consentimiento.Estado.REVOCADO:
            if estado != Consentimiento.Estado.REVOCADO:
                raise serializers.ValidationError(
                    {"estado": "Un consentimiento REVOCADO no puede cambiar de estado. Debe registrar uno nuevo."}
                )

        return attrs

    def create(self, validated_data):
        validated_data['tenant'] = get_current_tenant()
        validated_data['registrado_por'] = self.context['request'].user
        return super().create(validated_data)


class RevocacionSerializer(serializers.Serializer):
    """
    Serializer simple para la acción de revocar un consentimiento.
    """
    observaciones = serializers.CharField(required=False, allow_blank=True)

    def update(self, instance, validated_data):
        instance.estado = Consentimiento.Estado.REVOCADO
        instance.observaciones = validated_data.get('observaciones', instance.observaciones)
        # Podríamos registrar quién lo revocó en un campo extra si fuera necesario, 
        # pero el modelo original usa registrado_por para la creación.
        instance.save()
        return instance
