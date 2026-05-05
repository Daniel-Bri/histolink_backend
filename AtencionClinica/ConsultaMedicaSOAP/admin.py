from django.contrib import admin

from .models import Consulta


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ['id', 'codigo_cie10_principal', 'estado', 'medico', 'paciente', 'creado_en']
    list_filter = ['estado', 'creado_en']
    search_fields = ['codigo_cie10_principal', 'motivo_consulta', 'impresion_diagnostica']
    readonly_fields = ['creado_en', 'actualizado_en', 'hash_documento', 'firmada_en']
