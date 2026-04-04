# CU3 - Registro y Búsqueda de Pacientes

from django.db import models


class Paciente(models.Model):
    SEXO_CHOICES = [
        ("M", "Masculino"),
        ("F", "Femenino"),
        ("O", "Otro"),
    ]
    TIPO_SANGRE_CHOICES = [
        ("A+", "A+"), ("A-", "A-"),
        ("B+", "B+"), ("B-", "B-"),
        ("AB+", "AB+"), ("AB-", "AB-"),
        ("O+", "O+"), ("O-", "O-"),
    ]

    # Identificación
    ci = models.CharField(max_length=20, unique=True, verbose_name="Cédula de identidad")
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    tipo_sangre = models.CharField(max_length=3, choices=TIPO_SANGRE_CHOICES, blank=True, default="")

    # Contacto
    telefono = models.CharField(max_length=20, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    direccion = models.TextField(blank=True, default="")

    # Metadatos
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.apellido}, {self.nombre} (CI: {self.ci})"
