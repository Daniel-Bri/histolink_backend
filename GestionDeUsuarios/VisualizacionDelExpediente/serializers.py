# CU4 - Visualización del Expediente del Paciente — Serializers

from rest_framework import serializers
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from GestionDeUsuarios.EdicionDeAntecedentesMedicos.models import AntecedentesMedicos
from AtencionClinica.RegistroDeTriaje.models import Triaje
from AtencionClinica.ConsultaMedicaSOAP.models import ConsultaSOAP
from AtencionClinica.EmisionDeRecetaMedica.models import Receta, ItemReceta
from AtencionClinica.SolicitudDeEstudios.models import SolicitudEstudio


class AntecedentesMedicosSerializer(serializers.ModelSerializer):
    class Meta:
        model = AntecedentesMedicos
        exclude = ("paciente",)


class TriajeSerializer(serializers.ModelSerializer):
    enfermera_nombre = serializers.SerializerMethodField()
    prioridad_label = serializers.CharField(source="get_prioridad_display", read_only=True)

    class Meta:
        model = Triaje
        exclude = ("paciente",)

    def get_enfermera_nombre(self, obj):
        if obj.enfermera:
            return f"{obj.enfermera.first_name} {obj.enfermera.last_name}".strip() or obj.enfermera.username
        return None


class ItemRecetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemReceta
        exclude = ("receta",)


class RecetaSerializer(serializers.ModelSerializer):
    items = ItemRecetaSerializer(many=True, read_only=True)
    medico_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Receta
        exclude = ("paciente",)

    def get_medico_nombre(self, obj):
        if obj.medico:
            return f"{obj.medico.first_name} {obj.medico.last_name}".strip() or obj.medico.username
        return None


class SolicitudEstudioSerializer(serializers.ModelSerializer):
    solicitante_nombre = serializers.SerializerMethodField()

    class Meta:
        model = SolicitudEstudio
        exclude = ("paciente",)

    def get_solicitante_nombre(self, obj):
        if obj.solicitante:
            return f"{obj.solicitante.first_name} {obj.solicitante.last_name}".strip() or obj.solicitante.username
        return None


class ConsultaSOAPSerializer(serializers.ModelSerializer):
    medico_nombre = serializers.SerializerMethodField()
    recetas = RecetaSerializer(many=True, read_only=True)
    estudios = SolicitudEstudioSerializer(many=True, read_only=True)

    class Meta:
        model = ConsultaSOAP
        exclude = ("paciente",)

    def get_medico_nombre(self, obj):
        if obj.medico:
            return f"{obj.medico.first_name} {obj.medico.last_name}".strip() or obj.medico.username
        return None


class PacienteSerializer(serializers.ModelSerializer):
    sexo_label = serializers.CharField(source="get_sexo_display", read_only=True)

    class Meta:
        model = Paciente
        fields = "__all__"


class ExpedienteSerializer(serializers.ModelSerializer):
    """
    Serializer completo del expediente clínico de un paciente.
    Agrupa toda la información clínica en un único objeto.
    """
    sexo_label = serializers.CharField(source="get_sexo_display", read_only=True)
    antecedentes = AntecedentesMedicosSerializer(read_only=True)
    triajes = TriajeSerializer(many=True, read_only=True)
    consultas = ConsultaSOAPSerializer(many=True, read_only=True)
    recetas = RecetaSerializer(many=True, read_only=True)
    estudios = SolicitudEstudioSerializer(many=True, read_only=True)

    class Meta:
        model = Paciente
        fields = [
            "id",
            "ci",
            "nombre",
            "apellido",
            "fecha_nacimiento",
            "sexo",
            "sexo_label",
            "tipo_sangre",
            "telefono",
            "email",
            "direccion",
            "fecha_registro",
            "activo",
            "antecedentes",
            "triajes",
            "consultas",
            "recetas",
            "estudios",
        ]
