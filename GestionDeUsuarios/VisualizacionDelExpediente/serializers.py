# CU4 - Visualización del Expediente del Paciente — Serializers

from rest_framework import serializers
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from GestionDeUsuarios.EdicionDeAntecedentesMedicos.models import Antecedente
from AtencionClinica.RegistroDeTriaje.models import Triaje
from AtencionClinica.ConsultaMedicaSOAP.models import Consulta
from AtencionClinica.EmisionDeRecetaMedica.models import Receta, DetalleReceta
from AtencionClinica.SolicitudDeEstudios.models import OrdenEstudio, ResultadoEstudio


class AntecedenteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Antecedente
        exclude = ("paciente",)


class TriajeSerializer(serializers.ModelSerializer):
    enfermera_nombre  = serializers.SerializerMethodField()
    nivel_urgencia_label = serializers.CharField(source="get_nivel_urgencia_display", read_only=True)
    imc              = serializers.FloatField(read_only=True)
    presion_arterial = serializers.CharField(read_only=True)

    class Meta:
        model  = Triaje
        exclude = ("ficha",)

    def get_enfermera_nombre(self, obj):
        u = obj.enfermera
        return f"{u.first_name} {u.last_name}".strip() or u.username if u else None


class DetalleRecetaSerializer(serializers.ModelSerializer):
    via_label = serializers.CharField(source="get_via_administracion_display", read_only=True)

    class Meta:
        model  = DetalleReceta
        exclude = ("receta",)


class RecetaSerializer(serializers.ModelSerializer):
    detalles      = DetalleRecetaSerializer(many=True, read_only=True)
    medico_nombre = serializers.SerializerMethodField()
    estado_label  = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model  = Receta
        fields = "__all__"

    def get_medico_nombre(self, obj):
        u = obj.medico
        return f"{u.first_name} {u.last_name}".strip() or u.username if u else None


class ResultadoEstudioSerializer(serializers.ModelSerializer):
    ingresado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model  = ResultadoEstudio
        exclude = ("orden",)

    def get_ingresado_por_nombre(self, obj):
        u = obj.ingresado_por
        return f"{u.first_name} {u.last_name}".strip() or u.username if u else None


class OrdenEstudioSerializer(serializers.ModelSerializer):
    tipo_label             = serializers.CharField(source="get_tipo_estudio_display", read_only=True)
    estado_label           = serializers.CharField(source="get_estado_display", read_only=True)
    solicitante_nombre     = serializers.SerializerMethodField()
    resultado              = ResultadoEstudioSerializer(read_only=True)

    class Meta:
        model  = OrdenEstudio
        exclude = ("consulta",)

    def get_solicitante_nombre(self, obj):
        u = obj.medico_solicitante
        return f"{u.first_name} {u.last_name}".strip() or u.username if u else None


class ConsultaSerializer(serializers.ModelSerializer):
    medico_nombre = serializers.SerializerMethodField()
    estado_label  = serializers.CharField(source="get_estado_display", read_only=True)
    recetas       = RecetaSerializer(many=True, read_only=True)
    ordenes       = OrdenEstudioSerializer(many=True, read_only=True)

    class Meta:
        model  = Consulta
        exclude = ("ficha",)

    def get_medico_nombre(self, obj):
        u = obj.medico
        return f"{u.first_name} {u.last_name}".strip() or u.username if u else None


class ExpedienteSerializer(serializers.ModelSerializer):
    """
    Expediente clínico completo del paciente.
    Recetas y órdenes están anidadas dentro de cada consulta.
    """
    sexo_label           = serializers.CharField(source="get_sexo_display", read_only=True)
    autoidentificacion_label = serializers.CharField(source="get_autoidentificacion_display", read_only=True)
    tipo_seguro_label    = serializers.CharField(source="get_tipo_seguro_display", read_only=True)
    antecedentes         = AntecedenteSerializer(read_only=True)
    triajes              = serializers.SerializerMethodField()
    consultas            = serializers.SerializerMethodField()

    class Meta:
        model  = Paciente
        fields = [
            "id",
            "ci", "ci_complemento",
            "nombres", "apellido_paterno", "apellido_materno",
            "fecha_nacimiento",
            "sexo", "sexo_label",
            "autoidentificacion", "autoidentificacion_label",
            "telefono", "direccion",
            "nombre_responsable", "telefono_responsable", "parentesco_responsable",
            "tipo_seguro", "tipo_seguro_label", "numero_asegurado",
            "activo", "creado_en",
            "antecedentes",
            "triajes",
            "consultas",
        ]

    def get_triajes(self, obj: Paciente):
        qs = (
            Triaje.objects.filter(ficha__paciente=obj)
            .select_related("enfermera", "ficha")
            .order_by("-hora_triaje")
        )
        return TriajeSerializer(qs, many=True).data

    def get_consultas(self, obj: Paciente):
        qs = (
            Consulta.objects.filter(ficha__paciente=obj)
            .select_related("medico", "triaje", "ficha")
            .prefetch_related(
                "recetas__medico",
                "recetas__detalles",
                "ordenes__medico_solicitante",
                "ordenes__resultado__ingresado_por",
            )
            .order_by("-creado_en")
        )
        return ConsultaSerializer(qs, many=True).data
