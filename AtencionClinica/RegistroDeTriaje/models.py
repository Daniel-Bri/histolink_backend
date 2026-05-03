# CU7 - Registro de Triaje

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Triaje(models.Model):
    """
    Signos vitales y nivel de urgencia del paciente al llegar al establecimiento.
    Registrado por enfermería antes de la consulta médica.
    IMC y presion_arterial se calculan como @property — no se guardan en BD.
    Todos los rangos tienen CHECK CONSTRAINT en PostgreSQL como segunda línea de defensa.
    Una ficha de atención tiene como mucho un triaje asociado (OneToOne inverso desde Ficha.triaje).
    """

    NIVEL_URGENCIA_CHOICES = [
        ("ROJO",     "Rojo - Inmediato"),
        ("NARANJA",  "Naranja - Muy urgente"),
        ("AMARILLO", "Amarillo - Urgente"),
        ("VERDE",    "Verde - Poco urgente"),
        ("AZUL",     "Azul - No urgente"),
    ]

    ficha = models.OneToOneField(
        "AperturaFichaYColaDeAtencion.Ficha",
        on_delete=models.CASCADE,
        related_name="triaje",
        verbose_name="Ficha",
        help_text="Ficha clínica a la que pertenece este triaje.",
    )
    enfermera = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="triajes_registrados",
        verbose_name="Enfermera/o",
        help_text="Personal de enfermería que realizó el triaje.",
    )
    peso_kg = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0.5), MaxValueValidator(500)],
        verbose_name="Peso (kg)",
        help_text="Peso del paciente en kilogramos. Rango válido: 0.5 – 500 kg.",
    )
    talla_cm = models.DecimalField(
        max_digits=5, decimal_places=1,
        null=True, blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(250)],
        verbose_name="Talla (cm)",
        help_text="Talla del paciente en centímetros. Rango válido: 20 – 250 cm.",
    )
    frecuencia_cardiaca = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(300)],
        verbose_name="Frecuencia cardíaca (lpm)",
        help_text="Latidos por minuto. Rango válido: 20 – 300 lpm.",
    )
    frecuencia_respiratoria = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(5), MaxValueValidator(80)],
        verbose_name="Frecuencia respiratoria (rpm)",
        help_text="Respiraciones por minuto. Rango válido: 5 – 80 rpm.",
    )
    presion_sistolica = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(300)],
        verbose_name="Presión sistólica (mmHg)",
        help_text="Número de arriba en la presión arterial. Rango válido: 40 – 300 mmHg.",
    )
    presion_diastolica = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(200)],
        verbose_name="Presión diastólica (mmHg)",
        help_text="Número de abajo en la presión arterial. Rango válido: 20 – 200 mmHg.",
    )
    temperatura_celsius = models.DecimalField(
        max_digits=4, decimal_places=1,
        null=True, blank=True,
        validators=[MinValueValidator(25), MaxValueValidator(45)],
        verbose_name="Temperatura (°C)",
        help_text="Temperatura corporal en grados Celsius. Rango válido: 25 – 45 °C.",
    )
    saturacion_oxigeno = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(100)],
        verbose_name="Saturación de oxígeno (SpO2 %)",
        help_text="Saturación de oxígeno en sangre. Rango válido: 50 – 100 %. Normal > 95%.",
    )
    glucemia = models.DecimalField(
        max_digits=6, decimal_places=1,
        null=True, blank=True,
        verbose_name="Glucemia capilar (mg/dL)",
        help_text="Glucosa en sangre capilar en mg/dL. Solo si aplica clínicamente.",
    )
    escala_dolor = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Escala de dolor EVA",
        help_text="Escala Visual Analógica: 0 = sin dolor, 10 = dolor máximo insoportable.",
    )
    nivel_urgencia = models.CharField(
        max_length=10,
        choices=NIVEL_URGENCIA_CHOICES,
        null=True, blank=True,
        db_index=True,
        verbose_name="Nivel de urgencia",
        help_text="Clasificación de urgencia. Puede ser asignada por el modelo IA o manualmente por enfermería.",
    )
    motivo_consulta_triaje = models.TextField(
        blank=True,
        default="",
        verbose_name="Motivo de consulta (triaje)",
        help_text="Resumen del motivo de consulta anotado por enfermería. Este texto es procesado por el modelo NLP de triaje.",
    )
    observaciones = models.TextField(
        blank=True,
        default="",
        verbose_name="Observaciones",
        help_text="Observaciones adicionales de enfermería durante el triaje.",
    )
    hora_triaje = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Hora de triaje",
        help_text="Timestamp automático de cuándo se realizó el triaje.",
    )

    class Meta:
        verbose_name        = "Triaje"
        verbose_name_plural = "Triajes"
        ordering            = ["-hora_triaje"]
        constraints = [
            models.CheckConstraint(check=models.Q(peso_kg__gte=0.5)              & models.Q(peso_kg__lte=500),   name="triaje_peso_rango"),
            models.CheckConstraint(check=models.Q(talla_cm__gte=20)              & models.Q(talla_cm__lte=250),  name="triaje_talla_rango"),
            models.CheckConstraint(check=models.Q(frecuencia_cardiaca__gte=20)   & models.Q(frecuencia_cardiaca__lte=300),    name="triaje_fc_rango"),
            models.CheckConstraint(check=models.Q(frecuencia_respiratoria__gte=5)& models.Q(frecuencia_respiratoria__lte=80), name="triaje_fr_rango"),
            models.CheckConstraint(check=models.Q(presion_sistolica__gte=40)     & models.Q(presion_sistolica__lte=300),      name="triaje_ps_rango"),
            models.CheckConstraint(check=models.Q(presion_diastolica__gte=20)    & models.Q(presion_diastolica__lte=200),     name="triaje_pd_rango"),
            models.CheckConstraint(check=models.Q(temperatura_celsius__gte=25)   & models.Q(temperatura_celsius__lte=45),     name="triaje_temp_rango"),
            models.CheckConstraint(check=models.Q(saturacion_oxigeno__gte=50)    & models.Q(saturacion_oxigeno__lte=100),     name="triaje_spo2_rango"),
            models.CheckConstraint(check=models.Q(escala_dolor__gte=0)           & models.Q(escala_dolor__lte=10),            name="triaje_dolor_rango"),
        ]

    def __str__(self):
        pac = self.ficha.paciente if getattr(self, "ficha_id", None) else "—"
        return f"Triaje {self.id} - {pac} ({self.hora_triaje.date()})"

    @property
    def imc(self):
        """Índice de Masa Corporal calculado. No se persiste en BD."""
        if self.peso_kg and self.talla_cm and self.talla_cm > 0:
            talla_m = float(self.talla_cm) / 100
            return round(float(self.peso_kg) / (talla_m ** 2), 2)
        return None

    @property
    def presion_arterial(self):
        """Presión arterial formateada como sistólica/diastólica. No se persiste en BD."""
        if self.presion_sistolica and self.presion_diastolica:
            return f"{self.presion_sistolica}/{self.presion_diastolica}"
        return None
