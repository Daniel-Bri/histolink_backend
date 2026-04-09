"""
ml/servicio_ml.py

SERVICIO ML PARA DJANGO
────────────────────────
Capa de integración entre Django y los modelos de Machine Learning.
Las vistas y serializers de Django NUNCA importan directamente los modelos ML —
siempre pasan por este servicio.

Patrón Singleton: los modelos se cargan una sola vez en memoria al
arrancar Django (AppConfig.ready()) y se reutilizan en cada request.

Uso desde una vista Django:
    from ml.servicio_ml import ServicioML
    svc = ServicioML.obtener_instancia()

    # Predecir riesgo clínico
    resultado = svc.predecir_riesgo(paciente_id=42, tipo_riesgo="diabetes_tipo2")

    # Clasificar triaje
    resultado = svc.clasificar_triaje(
        texto_sintomas="dolor de pecho fuerte",
        triaje_id=15
    )
"""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("ml.servicio")

# Ruta base donde viven los modelos guardados
# En producción: settings.ML_MODELS_PATH (configurable en .env)
MODELS_DIR = Path(os.environ.get("ML_MODELS_PATH", "ml/modelos_guardados"))

# Nombres de archivo de los modelos entrenados
RUTA_MODELO_TRIAJE         = MODELS_DIR / "triaje_v1.joblib"
RUTAS_MODELOS_RIESGO = {
    "diabetes_tipo2":        MODELS_DIR / "riesgo_diabetes_tipo2_v1.joblib",
    "hipertension":          MODELS_DIR / "riesgo_hipertension_v1.joblib",
    "enfermedad_renal":      MODELS_DIR / "riesgo_enfermedad_renal_v1.joblib",
    "evento_cardiovascular": MODELS_DIR / "riesgo_evento_cardiovascular_v1.joblib",
}


class ServicioML:
    """
    Singleton que gestiona la carga y uso de los modelos ML.
    Se inicializa una sola vez en apps.py de la app Django.
    """
    _instancia: Optional["ServicioML"] = None

    def __init__(self):
        self._modelo_triaje  = None
        self._modelos_riesgo = {}
        self._cargado        = False

    @classmethod
    def obtener_instancia(cls) -> "ServicioML":
        if cls._instancia is None:
            cls._instancia = cls()
            cls._instancia._cargar_modelos()
        return cls._instancia

    def _cargar_modelos(self):
        """Carga todos los modelos al iniciar. Llamado desde AppConfig.ready()."""
        logger.info("Iniciando carga de modelos ML...")

        # Modelo de triaje
        try:
            from ml.modelo_triaje import ModeloTriaje
            if RUTA_MODELO_TRIAJE.exists():
                self._modelo_triaje = ModeloTriaje.cargar(str(RUTA_MODELO_TRIAJE))
                logger.info(f"✓ Modelo triaje cargado: {RUTA_MODELO_TRIAJE}")
            else:
                logger.warning(
                    f"Modelo triaje no encontrado en {RUTA_MODELO_TRIAJE}. "
                    f"Ejecutar: python ml/modelo_triaje.py para entrenar."
                )
        except Exception as e:
            logger.error(f"Error cargando modelo triaje: {e}")

        # Modelos de riesgo
        try:
            from ml.modelo_riesgo import ModeloRiesgoClinico
            for tipo, ruta in RUTAS_MODELOS_RIESGO.items():
                if ruta.exists():
                    self._modelos_riesgo[tipo] = ModeloRiesgoClinico.cargar(str(ruta))
                    logger.info(f"✓ Modelo riesgo '{tipo}' cargado")
                else:
                    logger.warning(f"Modelo riesgo '{tipo}' no encontrado en {ruta}")
        except Exception as e:
            logger.error(f"Error cargando modelos de riesgo: {e}")

        self._cargado = True
        logger.info("Carga de modelos ML completada.")

    # ── Clasificación de Triaje ─────────────────────────────────────────

    def clasificar_triaje(self,
                          texto_sintomas: str,
                          triaje_id: int = None,
                          signos_vitales: dict = None) -> dict:
        """
        Clasifica la prioridad de triaje a partir del texto de síntomas.

        Args:
            texto_sintomas: texto libre del motivo de consulta (motivo_consulta_triaje).
            triaje_id:      ID del registro Triaje en PostgreSQL (para guardar resultado).
            signos_vitales: dict con los campos del modelo Triaje de Django.
                            Ej: {"saturacion_oxigeno": 95, "presion_sistolica": 130, ...}

        Returns:
            dict con la predicción completa.
            Si el modelo no está disponible, retorna un dict con nivel por defecto y aviso.
        """
        if self._modelo_triaje is None:
            logger.warning("Modelo triaje no disponible — retornando nivel por defecto")
            return {
                "nivel_predicho": 3,
                "color": "AMARILLO",
                "nombre": "Urgente (modelo no disponible)",
                "max_espera": "60 min",
                "nivel_alerta": "ADVERTENCIA",
                "confianza": 0.0,
                "confianza_pct": "0.0%",
                "probabilidades": {},
                "texto_procesado": "",
                "ajuste_signos": "",
                "error": "Modelo no cargado. Ejecutar entrenamiento.",
                "version_modelo": "N/A",
            }

        try:
            resultado = self._modelo_triaje.predecir(
                texto_sintomas=texto_sintomas,
                signos_vitales=signos_vitales,
            )
            resultado["triaje_id"] = triaje_id

            # Guardar la predicción en PostgreSQL si se proporcionó el triaje_id
            if triaje_id is not None:
                self._guardar_prediccion_triaje(triaje_id, resultado)

            return resultado

        except Exception as e:
            logger.error(f"Error en clasificar_triaje (triaje_id={triaje_id}): {e}")
            return {
                "nivel_predicho": 3, "color": "AMARILLO",
                "error": str(e), "version_modelo": "ERROR"
            }

    def _guardar_prediccion_triaje(self, triaje_id: int, resultado: dict):
        """
        Guarda el nivel predicho en el registro Triaje de PostgreSQL.
        Usa Django ORM — solo disponible cuando Django está activo.
        """
        try:
            from AtencionClinica.RegistroDeTriaje.models import Triaje
            triaje = Triaje.objects.filter(pk=triaje_id).first()
            if triaje and triaje.nivel_urgencia is None:
                # Solo actualizar si la enfermera no asignó uno manualmente
                colores = {1:"ROJO",2:"NARANJA",3:"AMARILLO",4:"VERDE",5:"AZUL"}
                triaje.nivel_urgencia = colores.get(resultado["nivel_predicho"], "AMARILLO")
                triaje.save(update_fields=["nivel_urgencia"])
                logger.info(f"Triaje {triaje_id}: nivel_urgencia actualizado a {triaje.nivel_urgencia} por IA")
        except Exception as e:
            logger.warning(f"No se pudo guardar predicción triaje en BD: {e}")

    # ── Predicción de Riesgo Clínico ────────────────────────────────────

    def predecir_riesgo(self,
                        paciente_id: int,
                        tipo_riesgo: str = "diabetes_tipo2") -> dict:
        """
        Predice el riesgo clínico de un paciente a partir de sus datos en BD.

        Args:
            paciente_id: ID del registro Paciente en PostgreSQL.
            tipo_riesgo: tipo de riesgo a evaluar (ver TIPOS_RIESGO en modelo_riesgo.py).

        Returns:
            dict con la predicción completa de riesgo.
        """
        modelo = self._modelos_riesgo.get(tipo_riesgo)
        if modelo is None:
            return {
                "error": f"Modelo de riesgo '{tipo_riesgo}' no disponible.",
                "probabilidad_riesgo": None,
                "clasificacion": "NO_DISPONIBLE",
            }

        try:
            datos = self._extraer_features_paciente(paciente_id)
            if datos is None:
                return {"error": f"Paciente {paciente_id} no encontrado o sin datos suficientes."}

            return modelo.predecir(datos)

        except Exception as e:
            logger.error(f"Error en predecir_riesgo (paciente={paciente_id}, tipo={tipo_riesgo}): {e}")
            return {"error": str(e), "probabilidad_riesgo": None}

    def predecir_todos_los_riesgos(self, paciente_id: int) -> dict:
        """
        Ejecuta todos los modelos de riesgo para un paciente y retorna el resumen.
        Útil para mostrar en el perfil clínico completo del paciente.
        """
        resultados = {}
        for tipo_riesgo in RUTAS_MODELOS_RIESGO:
            resultados[tipo_riesgo] = self.predecir_riesgo(paciente_id, tipo_riesgo)
        return resultados

    def _extraer_features_paciente(self, paciente_id: int) -> Optional[dict]:
        """
        Consulta PostgreSQL para obtener los datos del paciente en el formato
        que esperan los modelos de riesgo.

        Combina datos de: pacientes, antecedentes, triaje (más reciente).
        """
        try:
            from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
            from GestionDeUsuarios.EdicionDeAntecedentesMedicos.models import Antecedente
            from AtencionClinica.RegistroDeTriaje.models import Triaje
            from datetime import date

            paciente = Paciente.objects.select_related("antecedentes").filter(
                pk=paciente_id, activo=True
            ).first()

            if paciente is None:
                return None

            # Calcular edad
            hoy  = date.today()
            edad = (hoy - paciente.fecha_nacimiento).days // 365

            # Antecedentes
            try:
                ant = paciente.antecedentes
            except Antecedente.DoesNotExist:
                ant = None

            def tiene(texto: str, keyword: str) -> int:
                if not texto:
                    return 0
                return 1 if keyword.lower() in texto.lower() else 0

            # Triaje más reciente para signos vitales
            ultimo_triaje = (
                Triaje.objects.filter(paciente=paciente)
                .order_by("-hora_triaje")
                .first()
            )

            datos = {
                # Demográficas
                "edad":                       edad,
                "sexo_numerico":              1 if paciente.sexo == "M" else 0,
                "imc":                        float(ultimo_triaje.imc) if ultimo_triaje and ultimo_triaje.imc else None,

                # Signos vitales
                "presion_sistolica":          int(ultimo_triaje.presion_sistolica) if ultimo_triaje and ultimo_triaje.presion_sistolica else None,
                "presion_diastolica":         int(ultimo_triaje.presion_diastolica) if ultimo_triaje and ultimo_triaje.presion_diastolica else None,
                "frecuencia_cardiaca":        int(ultimo_triaje.frecuencia_cardiaca) if ultimo_triaje and ultimo_triaje.frecuencia_cardiaca else None,
                "saturacion_oxigeno":         int(ultimo_triaje.saturacion_oxigeno) if ultimo_triaje and ultimo_triaje.saturacion_oxigeno else None,
                "glucemia":                   float(ultimo_triaje.glucemia) if ultimo_triaje and ultimo_triaje.glucemia else None,

                # Antecedentes (binarios)
                "tiene_diabetes":             tiene(ant.ant_patologicos if ant else "", "diabetes"),
                "tiene_hipertension":         tiene(ant.ant_patologicos if ant else "", "hipert"),
                "tiene_cardiopatia":          tiene(ant.ant_patologicos if ant else "", "cardio"),
                "tiene_enfermedad_renal":     tiene(ant.ant_patologicos if ant else "", "renal"),
                "fuma":                       tiene(ant.ant_no_patologicos if ant else "", "tabaq"),
                "consume_alcohol":            tiene(ant.ant_no_patologicos if ant else "", "alcohol"),
                "sedentario":                 tiene(ant.ant_no_patologicos if ant else "", "sedent"),
                "familiar_diabetes":          tiene(ant.ant_familiares if ant else "", "diabetes"),
                "familiar_hipertension":      tiene(ant.ant_familiares if ant else "", "hipert"),
                "familiar_cardiopatia":       tiene(ant.ant_familiares if ant else "", "cardio"),

                # Historial
                "num_consultas_ultimo_anio":  self._contar_consultas_anio(paciente_id),
                "num_hospitalizaciones":      int(ant.ant_quirurgicos.count("\n")) if ant and ant.ant_quirurgicos else 0,
            }
            return datos

        except Exception as e:
            logger.error(f"Error extrayendo features del paciente {paciente_id}: {e}")
            return None

    def _contar_consultas_anio(self, paciente_id: int) -> int:
        try:
            from AtencionClinica.ConsultaMedicaSOAP.models import Consulta
            from datetime import date, timedelta
            hace_un_anio = date.today() - timedelta(days=365)
            return Consulta.objects.filter(
                paciente_id=paciente_id,
                creado_en__date__gte=hace_un_anio
            ).count()
        except Exception:
            return 0

    # ── Estado del servicio ─────────────────────────────────────────────

    def estado(self) -> dict:
        """Retorna el estado de carga de todos los modelos. Útil para /api/ml/estado/"""
        return {
            "cargado": self._cargado,
            "modelo_triaje": {
                "disponible": self._modelo_triaje is not None,
                "version": self._modelo_triaje.version if self._modelo_triaje else None,
            },
            "modelos_riesgo": {
                tipo: {
                    "disponible": modelo is not None,
                    "version": modelo.version if modelo else None,
                }
                for tipo, modelo in self._modelos_riesgo.items()
            },
        }
