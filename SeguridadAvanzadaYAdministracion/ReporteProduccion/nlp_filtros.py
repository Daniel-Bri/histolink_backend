"""
Reportes/ReporteProduccion/nlp_filtros.py

T039 — Módulo NLP: texto libre → filtros del endpoint de reportes.

Convierte una consulta en lenguaje natural al mismo dict de filtros
que usaría un usuario seleccionando opciones en la UI.

Ejemplos:
    "consultas de diabetes en abril"
    → {"fecha_desde": "2026-04-01", "fecha_hasta": "2026-04-30",
       "codigo_cie10": "E11"}

    "triajes rojos de la semana pasada"
    → {"fecha_desde": "2026-04-21", "fecha_hasta": "2026-04-27",
       "nivel_urgencia": "ROJO"}

    "producción del médico Vidal en marzo 2026"
    → {"fecha_desde": "2026-03-01", "fecha_hasta": "2026-03-31",
       "medico_nombre": "Vidal"}
"""

import calendar
import re
import unicodedata
from datetime import date, timedelta
from typing import Optional


# ── Normalización ─────────────────────────────────────────────────────────────

def _normalizar(texto: str) -> str:
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).strip()


# ── Mapas de conocimiento ────────────────────────────────────────────────────

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    # abreviados
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}

NIVELES_URGENCIA = {
    "rojo":      "ROJO",
    "rojos":     "ROJO",
    "emergencia": "ROJO",
    "critico":   "ROJO",
    "critica":   "ROJO",
    "naranja":   "NARANJA",
    "muy urgente": "NARANJA",
    "amarillo":  "AMARILLO",
    "urgente":   "AMARILLO",
    "verde":     "VERDE",
    "poco urgente": "VERDE",
    "azul":      "AZUL",
    "no urgente": "AZUL",
}

# Palabras clave de síntomas/enfermedades → código CIE-10 más probable
CIE10_KEYWORDS = {
    "diabetes tipo 2":      "E11",
    "diabetes tipo2":       "E11",
    "diabetes":             "E11",
    "diabetico":            "E11",
    "diabeticos":           "E11",
    "diabetica":            "E11",
    "diabeticas":           "E11",
    "hipertension":         "I10",
    "presion alta":         "I10",
    "neumonia":             "J18.9",
    "asma":                 "J45",
    "infeccion urinaria":   "N39.0",
    "itu":                  "N39.0",
    "lumbalgia":            "M54.5",
    "dolor lumbar":         "M54.5",
    "resfriado":            "J00",
    "rinofaringitis":       "J00",
    "faringitis":           "J02.0",
    "amigdalitis":          "J03.9",
    "gastroenteritis":      "A09",
    "diarrea":              "A09",
    "anemia":               "D64.9",
    "insuficiencia cardiaca": "I50.9",
    "infarto":              "I21.9",
    "fractura":             "S00",
    "dengue":               "A90",
    "covid":                "U07.1",
    "hipotiroidismo":       "E03.9",
    "obesidad":             "E66.9",
}

MEDICO_STOPWORDS = {
    "todo", "el", "la", "los", "las", "mes", "reporte", "general", "resumen",
    "de", "del", "al", "en", "este", "esta", "mayo", "abril", "marzo",
}

PALABRAS_REPORTE = {
    "consulta", "consultas", "triaje", "triajes", "receta", "recetas",
    "reporte", "reportes", "resumen", "general", "emitidas", "emitida",
    "dispensadas", "dispensada", "anuladas", "anulada",
}

TIPOS_REPORTE_KEYWORDS = [
    ("recetas_emitidas", ["recetas emitidas", "receta emitida", "emitidas"]),
    ("recetas_dispensadas", ["recetas dispensadas", "receta dispensada", "dispensadas"]),
    ("recetas_anuladas", ["recetas anuladas", "receta anulada", "anuladas"]),
    ("triajes", ["triajes", "triaje"]),
    ("consultas", ["consultas", "consulta"]),
    ("recetas", ["recetas", "receta"]),
    ("resumen_general", ["reporte general", "resumen general", "general"]),
]

DIA_PALABRA = {
    "uno": 1, "un": 1, "primero": 1,
    "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9,
    "diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15, "dieciseis": 16,
    "diecisiete": 17, "dieciocho": 18, "diecinueve": 19, "veinte": 20, "veintiuno": 21, "veintidos": 22,
    "veintitres": 23, "veinticuatro": 24, "veinticinco": 25, "veintiseis": 26, "veintisiete": 27,
    "veintiocho": 28, "veintinueve": 29, "treinta": 30, "treinta y uno": 31,
}


def _texto_a_dia(valor: str) -> Optional[int]:
    valor = valor.strip()
    if valor.isdigit():
        n = int(valor)
        return n if 1 <= n <= 31 else None
    return DIA_PALABRA.get(valor)


def _ultimo_dia_mes(anio: int, mes: int) -> int:
    return calendar.monthrange(anio, mes)[1]


# ── Extractores individuales ──────────────────────────────────────────────────

def _extraer_periodo(texto: str, hoy: date) -> dict:
    """Detecta fechas y periodos en el texto. Retorna fecha_desde/fecha_hasta."""
    resultado = {}

    # Rango explícito con "fecha": "de la fecha primero de mayo al 5 de mayo"
    patron_fecha_explicita = (
        r"(?:de\s+la\s+fecha\s+|fecha\s+)?([a-z0-9]+)\s+de\s+([a-z]+)"
        r"(?:\s+de\s+(20\d{2}))?\s+"
        r"(?:al|hasta)\s+([a-z0-9]+)\s+de\s+([a-z]+)"
        r"(?:\s+de\s+(20\d{2}))?"
    )
    for m in re.finditer(patron_fecha_explicita, texto):
        d1_txt, mes1_txt, anio1_txt, d2_txt, mes2_txt, anio2_txt = m.groups()
        d1 = _texto_a_dia(d1_txt)
        d2 = _texto_a_dia(d2_txt)
        mes1 = MESES.get(mes1_txt)
        mes2 = MESES.get(mes2_txt)
        anio1 = int(anio1_txt) if anio1_txt else hoy.year
        anio2 = int(anio2_txt) if anio2_txt else anio1
        if not (d1 and d2 and mes1 and mes2):
            continue
        try:
            f1 = date(anio1, mes1, d1)
            f2 = date(anio2, mes2, d2)
            if f1 <= f2:
                return {"fecha_desde": f1.isoformat(), "fecha_hasta": f2.isoformat()}
        except ValueError:
            continue

    # Periodos relativos
    if re.search(r"\bhoy\b", texto):
        resultado = {"fecha_desde": hoy.isoformat(), "fecha_hasta": hoy.isoformat()}

    elif re.search(r"\bayer\b", texto):
        ayer = hoy - timedelta(days=1)
        resultado = {"fecha_desde": ayer.isoformat(), "fecha_hasta": ayer.isoformat()}

    elif re.search(r"\besta semana\b", texto):
        lunes = hoy - timedelta(days=hoy.weekday())
        resultado = {"fecha_desde": lunes.isoformat(), "fecha_hasta": hoy.isoformat()}

    elif re.search(r"\bsemana pasada\b", texto):
        lunes_pasado = hoy - timedelta(days=hoy.weekday() + 7)
        domingo_pasado = lunes_pasado + timedelta(days=6)
        resultado = {"fecha_desde": lunes_pasado.isoformat(), "fecha_hasta": domingo_pasado.isoformat()}

    elif re.search(r"\beste mes\b", texto):
        primero = hoy.replace(day=1)
        resultado = {"fecha_desde": primero.isoformat(), "fecha_hasta": hoy.isoformat()}

    elif re.search(r"\bmes pasado\b", texto):
        ultimo_mes = (hoy.replace(day=1) - timedelta(days=1))
        primero_mes = ultimo_mes.replace(day=1)
        resultado = {"fecha_desde": primero_mes.isoformat(), "fecha_hasta": ultimo_mes.isoformat()}

    elif re.search(r"\beste año\b|\bel año\b", texto):
        resultado = {
            "fecha_desde": hoy.replace(month=1, day=1).isoformat(),
            "fecha_hasta": hoy.isoformat(),
        }

    # Rango natural: "del 1 de mayo al 5 de mayo (de 2026)"
    if not resultado:
        patron_rango = (
            r"(?:del|desde)\s+([a-z0-9 ]+?)\s+de\s+([a-z]+)"
            r"(?:\s+de\s+(20\d{2}))?\s+"
            r"(?:al|hasta)\s+([a-z0-9 ]+?)\s+de\s+([a-z]+)"
            r"(?:\s+de\s+(20\d{2}))?"
        )
        for m in re.finditer(patron_rango, texto):
            d1_txt, mes1_txt, anio1_txt, d2_txt, mes2_txt, anio2_txt = m.groups()
            d1 = _texto_a_dia(d1_txt)
            d2 = _texto_a_dia(d2_txt)
            mes1 = MESES.get(mes1_txt)
            mes2 = MESES.get(mes2_txt)
            anio1 = int(anio1_txt) if anio1_txt else hoy.year
            anio2 = int(anio2_txt) if anio2_txt else anio1
            if not (d1 and d2 and mes1 and mes2):
                continue
            try:
                f1 = date(anio1, mes1, d1)
                f2 = date(anio2, mes2, d2)
                if f1 <= f2:
                    return {"fecha_desde": f1.isoformat(), "fecha_hasta": f2.isoformat()}
            except ValueError:
                continue

    # Rango natural compacto: "del primero al 9 de mayo" / "del 1 al 9 de mayo"
    if not resultado:
        patron_rango_mes_final = (
            r"(?:del|desde)\s+(?:el\s+)?([a-z0-9]+)\s+"
            r"(?:al|hasta)\s+(?:el\s+)?([a-z0-9]+)\s+de\s+([a-z]+)"
            r"(?:\s+de\s+(20\d{2}))?"
        )
        for m in re.finditer(patron_rango_mes_final, texto):
            d1_txt, d2_txt, mes_txt, anio_txt = m.groups()
            d1 = _texto_a_dia(d1_txt)
            d2 = _texto_a_dia(d2_txt)
            mes = MESES.get(mes_txt)
            anio = int(anio_txt) if anio_txt else hoy.year
            if not (d1 and d2 and mes):
                continue
            try:
                f1 = date(anio, mes, d1)
                f2 = date(anio, mes, d2)
                if f1 <= f2:
                    return {"fecha_desde": f1.isoformat(), "fecha_hasta": f2.isoformat()}
            except ValueError:
                continue

    # Día único explícito: "del primero de mayo", "el 1 de mayo", "primero de mayo"
    if not resultado:
        patron_dia_unico = r"(?:\bdel?\b|\bel\b)?\s*([a-z0-9]+)\s+de\s+([a-z]+)(?:\s+de\s+(20\d{2}))?"
        for m in re.finditer(patron_dia_unico, texto):
            d_txt, mes_txt, anio_txt = m.groups()
            d = _texto_a_dia(d_txt)
            mes = MESES.get(mes_txt)
            anio = int(anio_txt) if anio_txt else hoy.year
            if not (d and mes):
                continue
            try:
                f = date(anio, mes, d)
                return {"fecha_desde": f.isoformat(), "fecha_hasta": f.isoformat()}
            except ValueError:
                continue

    # Mes + año explícito: "abril 2026" / "en abril de 2026"
    if not resultado:
        anio_match = re.search(r"\b(20\d{2})\b", texto)
        anio = int(anio_match.group(1)) if anio_match else hoy.year

        for nombre_mes, num_mes in MESES.items():
            if re.search(rf"\b{nombre_mes}\b", texto):
                ultimo_dia = _ultimo_dia_mes(anio, num_mes)
                resultado = {
                    "fecha_desde": date(anio, num_mes, 1).isoformat(),
                    "fecha_hasta": date(anio, num_mes, ultimo_dia).isoformat(),
                }
                break

    # Año solo: "2026" sin mes
    if not resultado:
        anio_match = re.search(r"\b(20\d{2})\b", texto)
        if anio_match:
            anio = int(anio_match.group(1))
            resultado = {
                "fecha_desde": date(anio, 1, 1).isoformat(),
                "fecha_hasta": date(anio, 12, 31).isoformat(),
            }

    return resultado


def _extraer_nivel_urgencia(texto: str) -> Optional[str]:
    for keyword, nivel in NIVELES_URGENCIA.items():
        if keyword in texto:
            return nivel
    return None


def _extraer_cie10(texto: str) -> Optional[str]:
    # Código CIE-10 explícito: J18.9, E11, I10, etc.
    match = re.search(r"\b([A-Za-z]\d{2}(?:\.\d{1,2})?)\b", texto)
    if match:
        return match.group(1).upper()

    # Keyword de enfermedad (busca el match más largo primero)
    for keyword in sorted(CIE10_KEYWORDS, key=len, reverse=True):
        if keyword in texto:
            return CIE10_KEYWORDS[keyword]

    return None


def _extraer_medico(texto: str) -> Optional[str]:
    """
    Extrae el apellido/nombre del médico si aparece después de
    "médico", "doctor", "dr.", "dra.", "del doctor", etc.
    """
    # No inferir médico en frases genéricas de resumen
    frases_generales = [
        "todo el mes", "todo mayo", "reporte de todo", "todo el reporte",
        "resumen general", "reporte general",
    ]
    if any(f in texto for f in frases_generales):
        return None

    tiene_marcador_medico = bool(
        re.search(r"\b(medico|doctor|doctora|dr\.?|dra\.?)\b", texto, re.IGNORECASE)
    )

    patrones = [
        r"(?:del?\s+)?(?:medico|doctor|doctora|dr\.?|dra\.?)\s+([a-z]+(?:\s+[a-z]+)?)",
    ]
    for patron in patrones:
        m = re.search(patron, texto, re.IGNORECASE)
        if not m:
            continue
        nombre = m.group(1).strip()
        # Corta conectores si quedaron al final por frases tipo "doctor mamani en abril"
        nombre = re.split(r"\b(?:en|con|del|de|al|este|esta|para)\b", nombre, maxsplit=1)[0].strip()
        # Evita capturar ruido frecuente de periodos
        tokens = [t for t in nombre.split() if t]
        if not tokens:
            continue
        if all(t in MEDICO_STOPWORDS for t in tokens):
            continue
        if nombre in {"la semana", "este mes", "abril", "mayo"}:
            continue
        return " ".join(p.capitalize() for p in nombre.split())

    # Caso lenguaje natural sin marcador explícito:
    # "reporte de Tati de sus consultas"
    # "consultas de Mario del 1 al 9 de mayo"
    if not tiene_marcador_medico:
        m = re.search(
            r"\b(?:reporte|consultas|consulta|recetas|receta|triajes|triaje)"
            r"(?:\s+(?:emitidas?|dispensadas?|anuladas?|general))?\s+de\s+([a-z]+(?:\s+[a-z]+)?)\b",
            texto,
            re.IGNORECASE,
        )
        if m:
            nombre = m.group(1).strip()
            nombre = re.split(r"\b(?:de|del|al|en|con|desde|hasta|sus|este|esta)\b", nombre, maxsplit=1)[0].strip()
            tokens = [t for t in nombre.split() if t]
            if tokens and not all(t in MEDICO_STOPWORDS for t in tokens) and not any(t in PALABRAS_REPORTE for t in tokens):
                return " ".join(p.capitalize() for p in tokens)

    return None


def _extraer_tipo_reporte(texto: str) -> str:
    if any(x in texto for x in ["todo el mes", "todo mayo", "reporte general", "resumen general", "reporte de todo"]):
        return "resumen_general"
    for tipo, keywords in TIPOS_REPORTE_KEYWORDS:
        for k in keywords:
            if k in texto:
                return tipo
    return "resumen_general"


# ── Parser principal ──────────────────────────────────────────────────────────

def parsear_texto(texto: str, hoy: date = None) -> dict:
    """
    Convierte texto libre en un dict de filtros compatible con el endpoint
    GET /api/reportes/produccion/.

    Args:
        texto: consulta en lenguaje natural del usuario.
        hoy:   fecha de referencia (default: date.today()).

    Returns:
        dict con las claves que aplican:
            fecha_desde, fecha_hasta, nivel_urgencia,
            codigo_cie10, medico_nombre
        Solo se incluyen las claves que se pudieron inferir.
    """
    if not texto or not texto.strip():
        return {}

    if hoy is None:
        hoy = date.today()

    texto_norm = _normalizar(texto)
    filtros = {}

    # Periodo
    periodo = _extraer_periodo(texto_norm, hoy)
    filtros.update(periodo)

    # Nivel de urgencia
    nivel = _extraer_nivel_urgencia(texto_norm)
    if nivel:
        filtros["nivel_urgencia"] = nivel

    # CIE-10
    cie10 = _extraer_cie10(texto_norm)
    if cie10:
        filtros["codigo_cie10"] = cie10

    # Médico
    medico = _extraer_medico(texto_norm)
    if medico:
        filtros["medico_nombre"] = medico

    # Tipo de reporte/intención
    filtros["tipo_reporte"] = _extraer_tipo_reporte(texto_norm)

    return filtros
