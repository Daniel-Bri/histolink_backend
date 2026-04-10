from rest_framework import serializers
from .models import Paciente


class PacienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paciente
        fields = '__all__'

    def validate(self, data):
        ci = data.get('ci')
        ci_complemento = data.get('ci_complemento', '')
        instance = self.instance

        qs = Paciente.objects.filter(ci=ci, ci_complemento=ci_complemento)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                {'ci': 'Ya existe un paciente con este CI y complemento.'}
            )
        return data