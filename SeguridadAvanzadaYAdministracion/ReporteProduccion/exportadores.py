"""
Reportes/ReporteProduccion/exportadores.py

T038 — Generadores de archivos exportables: Excel, CSV, PDF.

Cada función recibe el dict `datos` que devuelve la vista
y retorna un HttpResponse listo para servir al cliente.
"""

import csv
import io
from datetime import date

from django.http import HttpResponse


# ── Excel ─────────────────────────────────────────────────────────────────────

def exportar_excel(datos: dict) -> HttpResponse:
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # quitar hoja por defecto

    periodo   = datos["periodo"]
    nombre_archivo = f"reporte_produccion_{periodo['desde']}_{periodo['hasta']}.xlsx"

    # ── Estilos ───────────────────────────────────────────────────────────────
    estilo_titulo  = Font(bold=True, size=13, color="FFFFFF")
    estilo_header  = Font(bold=True, size=10, color="FFFFFF")
    fill_titulo    = PatternFill("solid", fgColor="1F4E79")
    fill_header    = PatternFill("solid", fgColor="2E75B6")
    fill_subtitulo = PatternFill("solid", fgColor="D6E4F0")
    centro         = Alignment(horizontal="center", vertical="center")

    def _hoja_tabla(nombre_hoja, titulo, encabezados, filas):
        ws = wb.create_sheet(title=nombre_hoja)

        # Título
        ws.merge_cells(f"A1:{get_column_letter(len(encabezados))}1")
        celda = ws["A1"]
        celda.value    = titulo
        celda.font     = estilo_titulo
        celda.fill     = fill_titulo
        celda.alignment = centro
        ws.row_dimensions[1].height = 22

        # Periodo
        ws.merge_cells(f"A2:{get_column_letter(len(encabezados))}2")
        celda2 = ws["A2"]
        celda2.value    = f"Periodo: {periodo['desde']} — {periodo['hasta']}"
        celda2.fill     = fill_subtitulo
        celda2.alignment = centro

        # Encabezados
        for col, texto in enumerate(encabezados, start=1):
            c = ws.cell(row=3, column=col, value=texto)
            c.font      = estilo_header
            c.fill      = fill_header
            c.alignment = centro

        # Datos
        for fila_idx, fila in enumerate(filas, start=4):
            for col_idx, valor in enumerate(fila, start=1):
                ws.cell(row=fila_idx, column=col_idx, value=valor)

        # Ajustar ancho de columnas
        for col in range(1, len(encabezados) + 1):
            ws.column_dimensions[get_column_letter(col)].width = 22

        return ws

    # ── Hoja 1: Resumen ───────────────────────────────────────────────────────
    resumen = datos["resumen"]
    _hoja_tabla(
        "Resumen",
        "Resumen del Periodo",
        ["Indicador", "Valor"],
        [
            ["Total consultas",              resumen["total_consultas"]],
            ["Total triajes",                resumen["total_triajes"]],
            ["Recetas emitidas",             resumen["total_recetas_emitidas"]],
            ["Recetas dispensadas",          resumen["total_recetas_dispensadas"]],
            ["Recetas anuladas",             resumen["total_recetas_anuladas"]],
            ["Tasa de derivación (%)",       resumen["tasa_derivacion_pct"]],
        ],
    )

    # ── Hoja 2: Triajes por nivel ─────────────────────────────────────────────
    _hoja_tabla(
        "Triajes por Nivel",
        "Distribucion de Triajes por Nivel de Urgencia",
        ["Nivel", "Total", "Porcentaje (%)"],
        [
            [r["nivel_urgencia"], r["total"], r["porcentaje"]]
            for r in datos["triajes_por_nivel"]
        ],
    )

    # ── Hoja 3: Producción por médico ─────────────────────────────────────────
    _hoja_tabla(
        "Produccion Medicos",
        "Produccion por Medico",
        ["Médico", "Consultas", "Recetas emitidas", "Derivaciones"],
        [
            [r["medico"], r["consultas"], r["recetas"], r["derivaciones"]]
            for r in datos["produccion_por_medico"]
        ],
    )

    # ── Hoja 4: Top diagnósticos ──────────────────────────────────────────────
    _hoja_tabla(
        "Top Diagnosticos",
        "Top 10 Diagnosticos CIE-10",
        ["Código CIE-10", "Descripción", "Total consultas"],
        [
            [r["codigo"], r["descripcion"], r["total"]]
            for r in datos["top_diagnosticos"]
        ],
    )

    # ── Hoja 5: Consultas por día ─────────────────────────────────────────────
    _hoja_tabla(
        "Consultas por Dia",
        "Volumen de Consultas por Dia",
        ["Fecha", "Total"],
        [[r["fecha"], r["total"]] for r in datos["consultas_por_dia"]],
    )

    # ── Respuesta HTTP ────────────────────────────────────────────────────────
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'
    return response


# ── CSV ───────────────────────────────────────────────────────────────────────

def exportar_csv(datos: dict) -> HttpResponse:
    periodo        = datos["periodo"]
    nombre_archivo = f"reporte_produccion_{periodo['desde']}_{periodo['hasta']}.csv"

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'
    response.write("﻿")  # BOM para Excel en Windows

    writer = csv.writer(response)
    resumen = datos["resumen"]

    # Encabezado del archivo
    writer.writerow(["REPORTE DE PRODUCCIÓN Y FLUJO DE ATENCIÓN — HISTOLINK"])
    writer.writerow([f"Periodo: {periodo['desde']} — {periodo['hasta']}"])
    writer.writerow([])

    # Resumen
    writer.writerow(["=== RESUMEN ==="])
    writer.writerow(["Indicador", "Valor"])
    writer.writerow(["Total consultas",         resumen["total_consultas"]])
    writer.writerow(["Total triajes",            resumen["total_triajes"]])
    writer.writerow(["Recetas emitidas",         resumen["total_recetas_emitidas"]])
    writer.writerow(["Recetas dispensadas",      resumen["total_recetas_dispensadas"]])
    writer.writerow(["Recetas anuladas",         resumen["total_recetas_anuladas"]])
    writer.writerow(["Tasa de derivacion (%)",   resumen["tasa_derivacion_pct"]])
    writer.writerow([])

    # Triajes
    writer.writerow(["=== TRIAJES POR NIVEL ==="])
    writer.writerow(["Nivel", "Total", "Porcentaje (%)"])
    for r in datos["triajes_por_nivel"]:
        writer.writerow([r["nivel_urgencia"], r["total"], r["porcentaje"]])
    writer.writerow([])

    # Producción
    writer.writerow(["=== PRODUCCION POR MEDICO ==="])
    writer.writerow(["Medico", "Consultas", "Recetas emitidas", "Derivaciones"])
    for r in datos["produccion_por_medico"]:
        writer.writerow([r["medico"], r["consultas"], r["recetas"], r["derivaciones"]])
    writer.writerow([])

    # Diagnósticos
    writer.writerow(["=== TOP 10 DIAGNOSTICOS ==="])
    writer.writerow(["Codigo CIE-10", "Descripcion", "Total"])
    for r in datos["top_diagnosticos"]:
        writer.writerow([r["codigo"], r["descripcion"], r["total"]])
    writer.writerow([])

    # Consultas por día
    writer.writerow(["=== CONSULTAS POR DIA ==="])
    writer.writerow(["Fecha", "Total"])
    for r in datos["consultas_por_dia"]:
        writer.writerow([r["fecha"], r["total"]])

    return response


# ── PDF ───────────────────────────────────────────────────────────────────────

def exportar_pdf(datos: dict) -> HttpResponse:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    )

    periodo        = datos["periodo"]
    nombre_archivo = f"reporte_produccion_{periodo['desde']}_{periodo['hasta']}.pdf"
    resumen        = datos["resumen"]

    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=1.5 * cm,
    )

    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "titulo", parent=estilos["Title"],
        fontSize=16, textColor=colors.HexColor("#1F4E79"), spaceAfter=4,
    )
    estilo_seccion = ParagraphStyle(
        "seccion", parent=estilos["Heading2"],
        fontSize=11, textColor=colors.HexColor("#2E75B6"), spaceBefore=12, spaceAfter=4,
    )

    COLOR_HEADER = colors.HexColor("#2E75B6")
    COLOR_FILA   = colors.HexColor("#EBF3FA")

    def _estilo_tabla(n_cols):
        return TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0),  COLOR_HEADER),
            ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, 0),  9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_FILA]),
            ("FONTSIZE",    (0, 1), (-1, -1), 8),
            ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",  (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])

    elementos = []

    # Título
    elementos.append(Paragraph(
        "Reporte de Producción y Flujo de Atención", estilo_titulo,
    ))
    elementos.append(Paragraph(
        f"Establecimiento: Histolink &nbsp;|&nbsp; Periodo: {periodo['desde']} — {periodo['hasta']}",
        estilos["Normal"],
    ))
    elementos.append(Spacer(1, 0.5 * cm))

    # Resumen
    elementos.append(Paragraph("Resumen del Periodo", estilo_seccion))
    tabla_resumen = Table(
        [
            ["Indicador", "Valor"],
            ["Total consultas",          resumen["total_consultas"]],
            ["Total triajes",             resumen["total_triajes"]],
            ["Recetas emitidas",          resumen["total_recetas_emitidas"]],
            ["Recetas dispensadas",       resumen["total_recetas_dispensadas"]],
            ["Recetas anuladas",          resumen["total_recetas_anuladas"]],
            ["Tasa de derivación (%)",    resumen["tasa_derivacion_pct"]],
        ],
        colWidths=[12 * cm, 5 * cm],
    )
    tabla_resumen.setStyle(_estilo_tabla(2))
    elementos.append(tabla_resumen)
    elementos.append(Spacer(1, 0.4 * cm))

    # Triajes por nivel
    elementos.append(Paragraph("Distribución de Triajes por Nivel", estilo_seccion))
    filas_triaje = [["Nivel", "Total", "Porcentaje (%)"]] + [
        [r["nivel_urgencia"], r["total"], r["porcentaje"]]
        for r in datos["triajes_por_nivel"]
    ]
    tabla_triaje = Table(filas_triaje, colWidths=[8 * cm, 5 * cm, 5 * cm])
    tabla_triaje.setStyle(_estilo_tabla(3))
    elementos.append(tabla_triaje)
    elementos.append(Spacer(1, 0.4 * cm))

    # Producción por médico
    elementos.append(Paragraph("Producción por Médico", estilo_seccion))
    filas_medico = [["Médico", "Consultas", "Recetas", "Derivaciones"]] + [
        [r["medico"], r["consultas"], r["recetas"], r["derivaciones"]]
        for r in datos["produccion_por_medico"]
    ]
    tabla_medico = Table(filas_medico, colWidths=[11 * cm, 5 * cm, 5 * cm, 5 * cm])
    tabla_medico.setStyle(_estilo_tabla(4))
    elementos.append(tabla_medico)
    elementos.append(Spacer(1, 0.4 * cm))

    # Top diagnósticos
    elementos.append(Paragraph("Top 10 Diagnósticos CIE-10", estilo_seccion))
    filas_cie = [["Código CIE-10", "Descripción", "Total"]] + [
        [r["codigo"], r["descripcion"] or "—", r["total"]]
        for r in datos["top_diagnosticos"]
    ]
    tabla_cie = Table(filas_cie, colWidths=[5 * cm, 18 * cm, 4 * cm])
    tabla_cie.setStyle(_estilo_tabla(3))
    elementos.append(tabla_cie)

    doc.build(elementos)
    buffer.seek(0)

    response = HttpResponse(buffer.read(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'
    return response
