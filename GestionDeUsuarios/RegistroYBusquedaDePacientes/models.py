# CU3 - Registro y Búsqueda de Pacientes

from django.conf import settings
from django.db import models


class Paciente(models.Model):
    SEXO_CHOICES = [
        ("M", "Masculino"),
        ("F", "Femenino"),
    ]
    AUTOIDENTIFICACION_CHOICES = [
        ("QUECHUA",    "Quechua"),
        ("AYMARA",     "Aymara"),
        ("GUARANI",    "Guaraní"),
        ("CHIQUITANO", "Chiquitano"),
        ("MOJENO",     "Mojeno"),
        ("MESTIZO",    "Mestizo"),
        ("BLANCO",     "Blanco"),
        ("AFRO",       "Afroboliviano"),
        ("OTRO",       "Otro"),
        ("NE",         "No Especificado"),
    ]
    TIPO_SEGURO_CHOICES = [
        ("SUS",        "SUS"),
        ("CNS",        "CNS"),
        ("COSSMIL",    "COSSMIL"),
        ("BANCARIA",   "Bancaria"),
        ("PETROLERA",  "Petrolera"),
        ("PRIVADO",    "Privado"),
        ("PARTICULAR", "Particular"),
    ]

    # Identificación — CI + complemento forman la clave de negocio (UNIQUE TOGETHER)
    ci               = models.CharField(max_length=15, db_index=True, verbose_name="Carnet de Identidad")
    ci_complemento   = models.CharField(max_length=5, blank=True, default="", verbose_name="Complemento CI")

    nombres          = models.CharField(max_length=150)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100, blank=True, default="")
    fecha_nacimiento = models.DateField()
    sexo             = models.CharField(max_length=1, choices=SEXO_CHOICES)

    # Obligatorio por normativa MINSALUD Bolivia
    autoidentificacion = models.CharField(
        max_length=20, choices=AUTOIDENTIFICACION_CHOICES, default="NE"
    )

    # Contacto
    telefono  = models.CharField(max_length=20, blank=True, default="")
    direccion = models.TextField(blank=True, default="")

    # Contacto de emergencia / responsable (para menores o adultos)
    nombre_responsable    = models.CharField(max_length=200, blank=True, default="")
    telefono_responsable  = models.CharField(max_length=20, blank=True, default="")
    parentesco_responsable = models.CharField(max_length=50, blank=True, default="")

    # Seguro de salud
    tipo_seguro      = models.CharField(max_length=20, choices=TIPO_SEGURO_CHOICES, default="PARTICULAR")
    numero_asegurado = models.CharField(max_length=50, blank=True, default="")

    # Metadatos
    activo       = models.BooleanField(default=True)
    # FK a PersonalSalud — usa AUTH_USER_MODEL como placeholder hasta que PersonalSalud esté implementado
    creado_por   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="pacientes_registrados",
    )
    creado_en    = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Paciente"
        verbose_name_plural = "Pacientes"
        ordering            = ["apellido_paterno", "apellido_materno", "nombres"]
        unique_together     = [("ci", "ci_complemento")]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(ci=""),
                name="paciente_ci_no_vacio",
            ),
        ]
        indexes = [
            models.Index(fields=["ci"],                                  name="idx_paciente_ci"),
            models.Index(fields=["apellido_paterno", "apellido_materno"], name="idx_paciente_apellidos"),
        ]

    def __str__(self):
        return f"{self.apellido_paterno} {self.apellido_materno}, {self.nombres} (CI: {self.ci})"
