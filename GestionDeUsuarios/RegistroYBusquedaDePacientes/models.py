from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Paciente(models.Model):
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]

    ci = models.CharField(max_length=20)
    ci_complemento = models.CharField(max_length=10, blank=True, default='')
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100, blank=True, default='')
    fecha_nacimiento = models.DateField()
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    telefono = models.CharField(max_length=20, blank=True, default='')
    direccion = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'RegistroYBusquedaDePacientes'
        unique_together = [('ci', 'ci_complemento')]

    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} - CI: {self.ci}"


class AntecedentesMedicos(models.Model):
    paciente = models.OneToOneField(
        Paciente,
        on_delete=models.CASCADE,
        related_name='antecedentes'
    )
    alergias = models.TextField(blank=True, default='')
    enfermedades_cronicas = models.TextField(blank=True, default='')
    cirugias_previas = models.TextField(blank=True, default='')
    medicamentos_actuales = models.TextField(blank=True, default='')
    antecedentes_familiares = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'RegistroYBusquedaDePacientes'

    def __str__(self):
        return f"Antecedentes de {self.paciente}"


# Signal: crea antecedentes automáticamente al registrar un paciente
@receiver(post_save, sender=Paciente)
def crear_antecedentes(sender, instance, created, **kwargs):
    if created:
        AntecedentesMedicos.objects.create(paciente=instance)