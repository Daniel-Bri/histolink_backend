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

import re
import unicodedata
from datetime import date, timedelta
from typing import Optional


# ── Normalización ─────────────────────────────────────────────────────────────

def _normalizar(texto: str) -> str:
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


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
    "emergencia": "ROJO",
    "critico":   "ROJO",
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
    "hipertension":         "I10",
    "presion alta":         "I10",
    "neumonia":             "J18.9",
    "asma":                 "J45",
    "infeccion urinaria":   "N39.0",
    "itu":                  "N39.0",
    "lumbalgia":            "M54.5",
    "dolor lumbar":         "M54.5",
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


# ── Extractores individuales ──────────────────────────────────────────────────

def _extraer_periodo(texto: str, hoy: date) -> dict:
    """Detecta fechas y periodos en el texto. Retorna fecha_desde/fecha_hasta."""
    resultado = {}

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

    # Mes + año explícito: "abril 2026" / "en abril de 2026"
    if not resultado:
        anio_match = re.search(r"\b(20\d{2})\b", texto)
        anio = int(anio_match.group(1)) if anio_match else hoy.year

        for nombre_mes, num_mes in MESES.items():
            if re.search(rf"\b{nombre_mes}\b", texto):
                import calendar
                ultimo_dia = calendar.monthrange(anio, num_mes)[1]
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
    patron = r"(?:medico|doctor|doctora|dr\.?|dra\.?)\s+([A-Za-záéíóúüñÁÉÍÓÚÜÑ]+)"
    match = re.search(patron, texto, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


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
        filtros["medico_nombre"] = medico.capitalize()

    return filtros
