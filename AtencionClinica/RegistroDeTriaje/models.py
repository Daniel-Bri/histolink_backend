# CU7 - Registro de Triaje

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente


class Triaje(models.Model):
    NIVEL_URGENCIA_CHOICES = [
        ("ROJO",     "Rojo - Inmediato"),
        ("NARANJA",  "Naranja - Muy urgente"),
        ("AMARILLO", "Amarillo - Urgente"),
        ("VERDE",    "Verde - Poco urgente"),
        ("AZUL",     "Azul - No urgente"),
    ]

    # TODO: cuando AperturaFichaYColaDeAtencion implemente Ficha,
    # paciente se reemplaza por ficha (OneToOneField → Ficha).
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="triajes",
    )
    # FK a PersonalSalud — usa AUTH_USER_MODEL como placeholder
    enfermera = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="triajes_registrados",
    )

    # Signos vitales — con CHECK CONSTRAINTS en PostgreSQL
    peso_kg                = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                                  validators=[MinValueValidator(0.5), MaxValueValidator(500)])
    talla_cm               = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True,
                                                  validators=[MinValueValidator(20), MaxValueValidator(250)])
    frecuencia_cardiaca    = models.PositiveSmallIntegerField(null=True, blank=True,
                                                              validators=[MinValueValidator(20), MaxValueValidator(300)])
    frecuencia_respiratoria = models.PositiveSmallIntegerField(null=True, blank=True,
                                                               validators=[MinValueValidator(5), MaxValueValidator(80)])
    presion_sistolica      = models.PositiveSmallIntegerField(null=True, blank=True,
                                                              validators=[MinValueValidator(40), MaxValueValidator(300)])
    presion_diastolica     = models.PositiveSmallIntegerField(null=True, blank=True,
                                                              validators=[MinValueValidator(20), MaxValueValidator(200)])
    temperatura_celsius    = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,
                                                  validators=[MinValueValidator(25), MaxValueValidator(45)])
    saturacion_oxigeno     = models.PositiveSmallIntegerField(null=True, blank=True,
                                                              validators=[MinValueValidator(50), MaxValueValidator(100)])
    glucemia               = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    escala_dolor           = models.PositiveSmallIntegerField(null=True, blank=True,
                                                              validators=[MinValueValidator(0), MaxValueValidator(10)])

    # Nivel de urgencia — puede ser asignado por IA o manualmente
    nivel_urgencia         = models.CharField(max_length=10, choices=NIVEL_URGENCIA_CHOICES,
                                              null=True, blank=True, db_index=True)
    motivo_consulta_triaje = models.TextField(blank=True, default="")
    observaciones          = models.TextField(blank=True, default="")

    hora_triaje = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Triaje"
        verbose_name_plural = "Triajes"
        ordering            = ["-hora_triaje"]
        constraints = [
            models.CheckConstraint(check=models.Q(peso_kg__gte=0.5)   & models.Q(peso_kg__lte=500),   name="triaje_peso_rango"),
            models.CheckConstraint(check=models.Q(talla_cm__gte=20)   & models.Q(talla_cm__lte=250),  name="triaje_talla_rango"),
            models.CheckConstraint(check=models.Q(frecuencia_cardiaca__gte=20) & models.Q(frecuencia_cardiaca__lte=300), name="triaje_fc_rango"),
            models.CheckConstraint(check=models.Q(frecuencia_respiratoria__gte=5) & models.Q(frecuencia_respiratoria__lte=80), name="triaje_fr_rango"),
            models.CheckConstraint(check=models.Q(presion_sistolica__gte=40) & models.Q(presion_sistolica__lte=300), name="triaje_ps_rango"),
            models.CheckConstraint(check=models.Q(presion_diastolica__gte=20) & models.Q(presion_diastolica__lte=200), name="triaje_pd_rango"),
            models.CheckConstraint(check=models.Q(temperatura_celsius__gte=25) & models.Q(temperatura_celsius__lte=45), name="triaje_temp_rango"),
            models.CheckConstraint(check=models.Q(saturacion_oxigeno__gte=50) & models.Q(saturacion_oxigeno__lte=100), name="triaje_spo2_rango"),
            models.CheckConstraint(check=models.Q(escala_dolor__gte=0) & models.Q(escala_dolor__lte=10), name="triaje_dolor_rango"),
        ]

    def __str__(self):
        return f"Triaje {self.id} - {self.paciente} ({self.hora_triaje.date()})"

    @property
    def imc(self):
        if self.peso_kg and self.talla_cm and self.talla_cm > 0:
            talla_m = float(self.talla_cm) / 100
            return round(float(self.peso_kg) / (talla_m ** 2), 2)
        return None

    @property
    def presion_arterial(self):
        if self.presion_sistolica and self.presion_diastolica:
            return f"{self.presion_sistolica}/{self.presion_diastolica}"
        return None
