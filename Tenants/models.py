from django.db import models


MODULOS_SISTEMA = [
    ('CU2',  'Gestión de Personal de Salud'),
    ('CU3',  'Registro y Búsqueda de Pacientes'),
    ('CU4',  'Visualización de Expediente'),
    ('CU5',  'Antecedentes Médicos'),
    ('CU6',  'Apertura de Ficha / Cola'),
    ('CU7',  'Triaje'),
    ('CU8',  'Consulta Médica SOAP'),
    ('CU9',  'Recetas Médicas'),
    ('CU10', 'Estudios y Laboratorio'),
    ('CU11', 'Firma Digital'),
    ('CU12', 'Clasificación IA'),
    ('CU13', 'Predicción de Riesgos'),
    ('CU14', 'Blockchain'),
    ('CU20', 'Reportes SNIS'),
    ('CU21', 'Auditoría'),
]

IDIOMAS = [('es', 'Español'), ('en', 'English'), ('pt', 'Português')]


class Tenant(models.Model):
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre del establecimiento",
        help_text="Nombre oficial del establecimiento de salud. Ej: Hospital San Juan de Dios",
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="Identificador único",
        help_text="Identificador URL-friendly del establecimiento. Ej: hospital-san-juan. Se usa internamente.",
    )
    nit = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="NIT",
        help_text="Número de Identificación Tributaria del establecimiento.",
    )
    direccion = models.TextField(
        blank=True,
        default="",
        verbose_name="Dirección",
    )
    telefono = models.CharField(
        max_length=30,
        blank=True,
        default="",
        verbose_name="Teléfono",
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Desactivar para suspender acceso al establecimiento sin eliminar sus datos.",
    )
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

    class Meta:
        verbose_name = "Establecimiento"
        verbose_name_plural = "Establecimientos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    def get_configuracion(self):
        """Devuelve (o crea) la configuración asociada al tenant."""
        config, _ = ConfiguracionTenant.objects.get_or_create(tenant=self)
        return config


class ConfiguracionTenant(models.Model):
    """
    Configuración personalizable por establecimiento.
    Se crea automáticamente al primer acceso mediante get_configuracion().
    """

    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name="configuracion",
        verbose_name="Establecimiento",
    )

    # ── Identidad ─────────────────────────────────────────────────────────
    email_contacto = models.EmailField(blank=True, default="", verbose_name="Email de contacto")
    sitio_web      = models.CharField(max_length=200, blank=True, default="", verbose_name="Sitio web")

    # ── Localización ──────────────────────────────────────────────────────
    idioma = models.CharField(
        max_length=5, choices=IDIOMAS, default="es", verbose_name="Idioma",
    )
    moneda = models.CharField(
        max_length=10, default="BOB",
        verbose_name="Moneda", help_text="Código ISO 4217. Ej: BOB, USD, PEN, ARS.",
    )
    zona_horaria = models.CharField(
        max_length=60, default="America/La_Paz", verbose_name="Zona horaria",
    )

    # ── Feature flags ─────────────────────────────────────────────────────
    modulos_habilitados = models.JSONField(
        default=list,
        verbose_name="Módulos habilitados",
        help_text=(
            "Lista de códigos de módulo activos (ej: ['CU7','CU8']). "
            "Lista vacía = todos los módulos habilitados."
        ),
    )

    # ── Campos extra para Paciente ────────────────────────────────────────
    campos_extra_paciente = models.JSONField(
        default=list,
        verbose_name="Campos extra en Paciente",
        help_text=(
            "Lista de objetos {nombre, etiqueta, tipo, requerido} "
            "para campos adicionales en el formulario de paciente."
        ),
    )

    creado_en     = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Configuración de establecimiento"
        verbose_name_plural = "Configuraciones de establecimientos"

    def __str__(self):
        return f"Config — {self.tenant.nombre}"

    def modulo_habilitado(self, codigo: str) -> bool:
        """Devuelve True si el módulo está habilitado (lista vacía = todos activos)."""
        if not self.modulos_habilitados:
            return True
        return codigo in self.modulos_habilitados
