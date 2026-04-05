# CU3 - Registro y Búsqueda de Pacientes

from django.conf import settings
from django.db import models


class Paciente(models.Model):
    """
    Identidad civil del paciente.
    Contiene únicamente datos de quién es la persona — sin datos clínicos.
    Los datos clínicos (alergias, enfermedades, grupo sanguíneo) van en Antecedente.
    CI + ci_complemento forman la clave de negocio real (UNIQUE TOGETHER).
    """

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

    ci = models.CharField(
        max_length=15,
        db_index=True,
        verbose_name="Carnet de Identidad",
        help_text="Número de CI sin complemento. Ej: 12345678. No puede estar vacío.",
    )
    ci_complemento = models.CharField(
        max_length=5,
        blank=True,
        default="",
        verbose_name="Complemento del CI",
        help_text="Complemento del CI boliviano. Ej: 1A, 2B. Dejar vacío si no aplica.",
    )
    nombres = models.CharField(
        max_length=150,
        verbose_name="Nombres",
        help_text="Nombres de pila del paciente tal como aparecen en el CI.",
    )
    apellido_paterno = models.CharField(
        max_length=100,
        verbose_name="Apellido paterno",
        help_text="Primer apellido del paciente.",
    )
    apellido_materno = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Apellido materno",
        help_text="Segundo apellido. Puede estar vacío si el paciente tiene un solo apellido.",
    )
    fecha_nacimiento = models.DateField(
        verbose_name="Fecha de nacimiento",
        help_text="Formato YYYY-MM-DD. Se usa para calcular la edad dinámicamente.",
    )
    sexo = models.CharField(
        max_length=1,
        choices=SEXO_CHOICES,
        verbose_name="Sexo",
        help_text="Sexo biológico del paciente según normativa SNIS Bolivia: M o F.",
    )
    autoidentificacion = models.CharField(
        max_length=20,
        choices=AUTOIDENTIFICACION_CHOICES,
        default="NE",
        verbose_name="Autoidentificación étnica",
        help_text="Obligatorio por normativa Ministerio de Salud Bolivia. NE = No Especificado.",
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="Teléfono",
        help_text="Número de teléfono o celular del paciente. Opcional.",
    )
    direccion = models.TextField(
        blank=True,
        default="",
        verbose_name="Dirección",
        help_text="Dirección del domicilio del paciente. Opcional.",
    )
    nombre_responsable = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="Nombre del responsable",
        help_text="Padre, madre o tutor para menores. Contacto de emergencia para adultos.",
    )
    telefono_responsable = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="Teléfono del responsable",
        help_text="Teléfono del responsable o contacto de emergencia.",
    )
    parentesco_responsable = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Parentesco del responsable",
        help_text="Relación con el paciente. Ej: madre, padre, cónyuge, tutor, hijo/a.",
    )
    tipo_seguro = models.CharField(
        max_length=20,
        choices=TIPO_SEGURO_CHOICES,
        default="PARTICULAR",
        verbose_name="Tipo de seguro",
        help_text="Seguro de salud del paciente. PARTICULAR si no tiene seguro.",
    )
    numero_asegurado = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Número de asegurado",
        help_text="Número de afiliación en la caja de salud. Solo si no es PARTICULAR.",
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="False = soft-delete. El registro nunca se borra físicamente de la BD.",
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="pacientes_registrados",
        verbose_name="Registrado por",
        help_text="Personal de salud que registró al paciente en el sistema.",
    )
    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado en",
        help_text="Timestamp automático de cuándo se registró el paciente.",
    )
    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name="Actualizado en",
        help_text="Timestamp automático de la última modificación.",
    )

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
            models.Index(fields=["ci"],                                   name="idx_paciente_ci"),
            models.Index(fields=["apellido_paterno", "apellido_materno"], name="idx_paciente_apellidos"),
        ]

    def __str__(self):
        return f"{self.apellido_paterno} {self.apellido_materno}, {self.nombres} (CI: {self.ci})"
