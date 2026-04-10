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

    ci = models.CharField(max_length=15, db_index=True, verbose_name="Carnet de Identidad")
    ci_complemento = models.CharField(max_length=5, blank=True, default="", verbose_name="Complemento del CI")
    nombres = models.CharField(max_length=150, verbose_name="Nombres")
    apellido_paterno = models.CharField(max_length=100, verbose_name="Apellido paterno")
    apellido_materno = models.CharField(max_length=100, blank=True, default="", verbose_name="Apellido materno")
    fecha_nacimiento = models.DateField(verbose_name="Fecha de nacimiento")
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, verbose_name="Sexo")
    autoidentificacion = models.CharField(max_length=20, choices=AUTOIDENTIFICACION_CHOICES, default="NE", verbose_name="Autoidentificación étnica")
    telefono = models.CharField(max_length=20, blank=True, default="", verbose_name="Teléfono")
    direccion = models.TextField(blank=True, default="", verbose_name="Dirección")
    nombre_responsable = models.CharField(max_length=200, blank=True, default="", verbose_name="Nombre del responsable")
    telefono_responsable = models.CharField(max_length=20, blank=True, default="", verbose_name="Teléfono del responsable")
    parentesco_responsable = models.CharField(max_length=50, blank=True, default="", verbose_name="Parentesco del responsable")
    tipo_seguro = models.CharField(max_length=20, choices=TIPO_SEGURO_CHOICES, default="PARTICULAR", verbose_name="Tipo de seguro")
    numero_asegurado = models.CharField(max_length=50, blank=True, default="", verbose_name="Número de asegurado")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="pacientes_registrados",
        verbose_name="Registrado por"
    )
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

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
            models.Index(fields=["ci"], name="idx_paciente_ci"),
            models.Index(fields=["apellido_paterno", "apellido_materno"], name="idx_paciente_apellidos"),
        ]

    def __str__(self):
        return f"{self.apellido_paterno} {self.apellido_materno}, {self.nombres} (CI: {self.ci})"