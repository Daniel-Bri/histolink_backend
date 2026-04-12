# CU5 - Edición de Antecedentes Médicos

from rest_framework import serializers

from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente

from .models import Antecedente, RegistroAntecedente


class AntecedenteSerializer(serializers.ModelSerializer):
    """
    Lectura completa del antecedente.
    Usado en GET y como respuesta tras PATCH.
    """
    ultima_actualizacion_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Antecedente
        fields = [
            "id",
            "paciente",
            "grupo_sanguineo",
            "alergias",
            "ant_patologicos",
            "ant_no_patologicos",
            "ant_quirurgicos",
            "ant_familiares",
            "ant_gineco_obstetricos",
            "medicacion_actual",
            "esquema_vacunacion",
            "ultima_actualizacion_por",
            "ultima_actualizacion_por_nombre",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = [
            "id", "paciente",
            "ultima_actualizacion_por",
            "ultima_actualizacion_por_nombre",
            "creado_en", "actualizado_en",
        ]

    def get_ultima_actualizacion_por_nombre(self, obj):
        u = obj.ultima_actualizacion_por
        if not u:
            return None
        return f"{u.first_name} {u.last_name}".strip() or u.username


class AntecedenteUpdateSerializer(serializers.ModelSerializer):
    """
    Escritura parcial del antecedente (PATCH).
    Todos los campos son opcionales — solo se actualizan los enviados.
    ultima_actualizacion_por se inyecta desde la vista, no desde el request body.
    """

    class Meta:
        model = Antecedente
        fields = [
            "grupo_sanguineo",
            "alergias",
            "ant_patologicos",
            "ant_no_patologicos",
            "ant_quirurgicos",
            "ant_familiares",
            "ant_gineco_obstetricos",
            "medicacion_actual",
            "esquema_vacunacion",
        ]

    def update(self, instance, validated_data):
        # Inyectar el usuario que hizo el cambio (pasado desde la vista)
        usuario = self.context.get("request").user
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.ultima_actualizacion_por = usuario
        instance.save()
        return instance


class RegistroAntecedenteSerializer(serializers.ModelSerializer):
    """
    Alta de un registro puntual de antecedente (T010).
    fecha_registro lo asigna el modelo (auto_now_add); no se envía en POST.
    """

    paciente = serializers.PrimaryKeyRelatedField(
        queryset=Paciente.objects.all(),
        required=True,
    )
    tipo = serializers.ChoiceField(
        choices=RegistroAntecedente.TIPO_CHOICES,
        required=True,
    )
    descripcion = serializers.CharField(max_length=500, required=True)

    class Meta:
        model = RegistroAntecedente
        fields = ["id", "paciente", "tipo", "descripcion", "fecha_registro"]
        read_only_fields = ["id", "fecha_registro"]

    def validate_descripcion(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("La descripción es obligatoria.")
        return value
