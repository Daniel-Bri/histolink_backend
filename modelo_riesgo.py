"""
ml/modelo_riesgo.py

MODELO 1 — Predicción de Riesgos Clínicos a Largo Plazo
────────────────────────────────────────────────────────
Usa Regresión Logística para estimar la probabilidad de que
un paciente desarrolle patologías crónicas o complicaciones futuras
a partir de sus datos clínicos actuales (vitales, antecedentes, laboratorio).

Fórmula matemática:
    P(Y=1|X) = 1 / (1 + e^-(β₀ + β₁X₁ + ... + βₙXₙ))

Uso:
    # Entrenar
    from ml.modelo_riesgo import ModeloRiesgoClinico
    modelo = ModeloRiesgoClinico()
    modelo.entrenar(df)
    modelo.guardar("ml/modelos_guardados/riesgo_v1.joblib")

    # Inferencia en producción
    modelo = ModeloRiesgoClinico.cargar("ml/modelos_guardados/riesgo_v1.joblib")
    resultado = modelo.predecir(datos_paciente)
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    classification_report, roc_auc_score,
    confusion_matrix, brier_score_loss
)
from sklearn.calibration import CalibratedClassifierCV
from sklearn.impute import SimpleImputer


# ── Tipos de riesgo que puede predecir el modelo ────────────────────────
TIPOS_RIESGO = {
    "diabetes_tipo2":     "Riesgo de desarrollar Diabetes Tipo 2",
    "hipertension":       "Riesgo de desarrollar Hipertensión Arterial",
    "enfermedad_renal":   "Riesgo de Enfermedad Renal Crónica",
    "evento_cardiovascular": "Riesgo de Evento Cardiovascular (infarto/ACV)",
}

# ── Variables clínicas de entrada (features) ───────────────────────────
# Deben existir en los datos de entrenamiento y en la inferencia.
# Valores None/NaN son imputados automáticamente por el pipeline.
FEATURES = [
    # Demográficas
    "edad",                      # años (int)
    "sexo_numerico",              # 0=Femenino, 1=Masculino
    "imc",                        # kg/m² (float) — calculado en triaje

    # Signos vitales (del triaje más reciente)
    "presion_sistolica",          # mmHg
    "presion_diastolica",         # mmHg
    "frecuencia_cardiaca",        # lpm
    "saturacion_oxigeno",         # %
    "glucemia",                   # mg/dL

    # Antecedentes (binarios: 0=No, 1=Sí)
    "tiene_diabetes",
    "tiene_hipertension",
    "tiene_cardiopatia",
    "tiene_enfermedad_renal",
    "fuma",                        # tabaquismo
    "consume_alcohol",             # alcoholismo
    "sedentario",

    # Antecedentes familiares (binarios)
    "familiar_diabetes",
    "familiar_hipertension",
    "familiar_cardiopatia",

    # Historial de consultas
    "num_consultas_ultimo_anio",   # int
    "num_hospitalizaciones",       # int
]


class ModeloRiesgoClinico:
    """
    Modelo de regresión logística para predicción de riesgos clínicos.

    Parámetros del constructor:
        tipo_riesgo: clave de TIPOS_RIESGO (default: 'diabetes_tipo2')
        umbral:      probabilidad mínima para clasificar como riesgo alto (default: 0.5)
    """

    def __init__(self, tipo_riesgo: str = "diabetes_tipo2", umbral: float = 0.5):
        if tipo_riesgo not in TIPOS_RIESGO:
            raise ValueError(f"tipo_riesgo debe ser uno de: {list(TIPOS_RIESGO.keys())}")

        self.tipo_riesgo = tipo_riesgo
        self.umbral = umbral
        self.pipeline = None
        self.version = "1.0"
        self.metricas_entrenamiento = {}

        self._construir_pipeline()

    # ── Construcción del pipeline ───────────────────────────────────────

    def _construir_pipeline(self):
        """
        Pipeline completo:
            1. SimpleImputer   → reemplaza NaN con la mediana (datos médicos tienen faltantes)
            2. StandardScaler  → normaliza los features (μ=0, σ=1)
            3. LogisticRegression calibrada → modelo final con probabilidades bien calibradas
        """
        lr = LogisticRegression(
            max_iter=1000,
            solver="lbfgs",
            class_weight="balanced",   # compensa desbalance: pocos pacientes con riesgo vs muchos sanos
            random_state=42,
            C=1.0,                     # regularización L2 (ajustar con GridSearchCV)
        )

        # CalibratedClassifierCV convierte los scores en probabilidades reales
        # (importante en medicina: un 70% de riesgo debe significar 70%, no más ni menos)
        lr_calibrado = CalibratedClassifierCV(lr, cv=5, method="sigmoid")

        self.pipeline = Pipeline([
            ("imputador",  SimpleImputer(strategy="median")),
            ("escalador",  StandardScaler()),
            ("modelo",     lr_calibrado),
        ])

    # ── Entrenamiento ───────────────────────────────────────────────────

    def entrenar(self, df: pd.DataFrame, columna_objetivo: str = "tiene_riesgo") -> dict:
        """
        Entrena el modelo con un DataFrame de pacientes.

        Args:
            df:               DataFrame con las columnas de FEATURES + columna_objetivo.
            columna_objetivo: nombre de la columna target (0=sin riesgo, 1=con riesgo).

        Returns:
            dict con métricas del entrenamiento.
        """
        # Validar que existan las columnas necesarias
        faltantes = [f for f in FEATURES if f not in df.columns]
        if faltantes:
            raise ValueError(f"Faltan columnas en el DataFrame: {faltantes}")
        if columna_objetivo not in df.columns:
            raise ValueError(f"No existe la columna objetivo: '{columna_objetivo}'")

        X = df[FEATURES].copy()
        y = df[columna_objetivo].copy()

        print(f"\n{'='*60}")
        print(f"ENTRENANDO: {TIPOS_RIESGO[self.tipo_riesgo]}")
        print(f"{'='*60}")
        print(f"Total muestras:    {len(df)}")
        print(f"Casos con riesgo:  {y.sum()} ({y.mean()*100:.1f}%)")
        print(f"Casos sin riesgo:  {(1-y).sum()} ({(1-y.mean())*100:.1f}%)")

        # Dividir en train / test (80/20, estratificado)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Entrenar
        self.pipeline.fit(X_train, y_train)

        # Evaluar
        y_pred       = self.pipeline.predict(X_test)
        y_prob       = self.pipeline.predict_proba(X_test)[:, 1]

        # Cross-validation 5-fold
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_auc = cross_val_score(self.pipeline, X, y, cv=cv, scoring="roc_auc")

        self.metricas_entrenamiento = {
            "tipo_riesgo":    self.tipo_riesgo,
            "n_muestras":     len(df),
            "n_features":     len(FEATURES),
            "auc_roc_test":   round(roc_auc_score(y_test, y_prob), 4),
            "auc_roc_cv_mean":round(cv_auc.mean(), 4),
            "auc_roc_cv_std": round(cv_auc.std(), 4),
            "brier_score":    round(brier_score_loss(y_test, y_prob), 4),
            "reporte":        classification_report(y_test, y_pred, output_dict=True),
        }

        print(f"\nRESULTADOS:")
        print(f"  AUC-ROC (test):     {self.metricas_entrenamiento['auc_roc_test']}")
        print(f"  AUC-ROC (CV 5fold): {self.metricas_entrenamiento['auc_roc_cv_mean']} ± {self.metricas_entrenamiento['auc_roc_cv_std']}")
        print(f"  Brier Score:        {self.metricas_entrenamiento['brier_score']} (0=perfecto, 0.25=random)")
        print(f"\n{classification_report(y_test, y_pred, target_names=['Sin riesgo','Con riesgo'])}")

        # Coeficientes (interpretabilidad — qué factor influye más)
        self._mostrar_interpretabilidad()

        return self.metricas_entrenamiento

    def _mostrar_interpretabilidad(self):
        """Muestra los coeficientes del modelo para interpretación médica."""
        try:
            # Acceder al LR dentro del pipeline calibrado
            lr_base = self.pipeline.named_steps["modelo"].calibrated_classifiers_[0].estimator
            coef = lr_base.coef_[0]
            importancias = sorted(
                zip(FEATURES, coef), key=lambda x: abs(x[1]), reverse=True
            )
            print("\nINTERPRETABILIDAD — Top 10 factores más influyentes:")
            print(f"{'Factor':<35} {'Coeficiente β':>14}  {'Dirección'}")
            print("-" * 65)
            for feat, coef_val in importancias[:10]:
                direccion = "↑ AUMENTA riesgo" if coef_val > 0 else "↓ REDUCE riesgo"
                print(f"  {feat:<33} {coef_val:>+12.4f}  {direccion}")
        except Exception:
            pass  # Si el modelo no expone coeficientes directamente

    # ── Inferencia ──────────────────────────────────────────────────────

    def predecir(self, datos: dict) -> dict:
        """
        Realiza una predicción de riesgo para un paciente.

        Args:
            datos: dict con los valores de los FEATURES.
                   Los campos faltantes se imputarán con la mediana del entrenamiento.

        Returns:
            dict con:
                probabilidad_riesgo: float 0.0–1.0
                clasificacion:       'ALTO' | 'MODERADO' | 'BAJO'
                nivel_alerta:        'CRITICO' | 'ADVERTENCIA' | 'NORMAL'
                factores_riesgo:     list de factores que más contribuyen
                recomendacion:       str con acción clínica sugerida
                interpretabilidad:   dict con contribución de cada factor
        """
        if self.pipeline is None:
            raise RuntimeError("El modelo no está entrenado. Llama a entrenar() o cargar().")

        # Construir el vector de features
        fila = {f: datos.get(f, np.nan) for f in FEATURES}
        X = pd.DataFrame([fila])[FEATURES]

        # Predicción
        prob = float(self.pipeline.predict_proba(X)[0, 1])

        # Clasificación por umbrales
        if prob >= 0.70:
            clasificacion = "ALTO"
            nivel_alerta  = "CRITICO"
            recomendacion = (
                "Derivar a especialista. Iniciar protocolo de prevención inmediata. "
                "Solicitar estudios de laboratorio completos."
            )
        elif prob >= 0.40:
            clasificacion = "MODERADO"
            nivel_alerta  = "ADVERTENCIA"
            recomendacion = (
                "Programar seguimiento en 3 meses. Educación al paciente sobre "
                "factores modificables (dieta, actividad física). Monitoreo de signos vitales."
            )
        else:
            clasificacion = "BAJO"
            nivel_alerta  = "NORMAL"
            recomendacion = (
                "Continuar controles anuales de rutina. "
                "Reforzar hábitos saludables preventivos."
            )

        # Factores de riesgo presentes en este paciente
        factores_presentes = self._extraer_factores_riesgo(datos)

        # Contribución de cada feature a esta predicción (interpretabilidad)
        interpretabilidad = self._calcular_contribuciones(X, datos)

        return {
            "tipo_riesgo":          self.tipo_riesgo,
            "descripcion_riesgo":   TIPOS_RIESGO[self.tipo_riesgo],
            "probabilidad_riesgo":  round(prob, 4),
            "porcentaje_riesgo":    f"{prob*100:.1f}%",
            "clasificacion":        clasificacion,
            "nivel_alerta":         nivel_alerta,
            "recomendacion":        recomendacion,
            "factores_riesgo":      factores_presentes,
            "interpretabilidad":    interpretabilidad,
            "umbral_usado":         self.umbral,
            "version_modelo":       self.version,
        }

    def _extraer_factores_riesgo(self, datos: dict) -> list:
        """Identifica qué factores de riesgo están presentes en este paciente."""
        factores = []
        mapeo = {
            "tiene_diabetes":       "Diabetes preexistente",
            "tiene_hipertension":   "Hipertensión preexistente",
            "tiene_cardiopatia":    "Cardiopatía preexistente",
            "fuma":                 "Tabaquismo",
            "consume_alcohol":      "Consumo de alcohol",
            "sedentario":           "Sedentarismo",
            "familiar_diabetes":    "Antecedente familiar de diabetes",
            "familiar_hipertension":"Antecedente familiar de hipertensión",
            "familiar_cardiopatia": "Antecedente familiar de cardiopatía",
        }
        for campo, descripcion in mapeo.items():
            if datos.get(campo, 0) == 1:
                factores.append(descripcion)

        # Factores numéricos fuera de rango normal
        imc = datos.get("imc", None)
        if imc and imc >= 30:
            factores.append(f"Obesidad (IMC: {imc:.1f})")
        elif imc and imc >= 25:
            factores.append(f"Sobrepeso (IMC: {imc:.1f})")

        glucemia = datos.get("glucemia", None)
        if glucemia and glucemia >= 126:
            factores.append(f"Glucemia elevada ({glucemia} mg/dL)")
        elif glucemia and glucemia >= 100:
            factores.append(f"Glucemia en rango prediabético ({glucemia} mg/dL)")

        ps = datos.get("presion_sistolica", None)
        if ps and ps >= 140:
            factores.append(f"Hipertensión sistólica ({ps} mmHg)")

        edad = datos.get("edad", None)
        if edad and edad >= 45:
            factores.append(f"Edad de riesgo ({edad} años)")

        return factores

    def _calcular_contribuciones(self, X: pd.DataFrame, datos: dict) -> dict:
        """
        Calcula la contribución de cada feature a esta predicción específica.
        Método: multiplicación coeficiente × valor escalado.
        """
        try:
            # Transformar con el escalador
            X_scaled = self.pipeline.named_steps["escalador"].transform(
                self.pipeline.named_steps["imputador"].transform(X)
            )
            lr_base = self.pipeline.named_steps["modelo"].calibrated_classifiers_[0].estimator
            coef = lr_base.coef_[0]

            contribuciones = {}
            for i, feat in enumerate(FEATURES):
                contrib = float(coef[i] * X_scaled[0][i])
                if abs(contrib) > 0.01:  # solo mostrar las significativas
                    contribuciones[feat] = round(contrib, 4)

            # Ordenar por contribución absoluta
            contribuciones = dict(
                sorted(contribuciones.items(), key=lambda x: abs(x[1]), reverse=True)
            )
            return contribuciones
        except Exception:
            return {}

    # ── Persistencia ────────────────────────────────────────────────────

    def guardar(self, ruta: str):
        """Guarda el modelo entrenado en disco."""
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "pipeline":   self.pipeline,
            "tipo_riesgo": self.tipo_riesgo,
            "umbral":     self.umbral,
            "version":    self.version,
            "metricas":   self.metricas_entrenamiento,
            "features":   FEATURES,
        }, ruta, compress=3)
        print(f"✓ Modelo guardado en: {ruta}")

    @classmethod
    def cargar(cls, ruta: str) -> "ModeloRiesgoClinico":
        """Carga un modelo previamente guardado."""
        datos = joblib.load(ruta)
        instancia = cls(tipo_riesgo=datos["tipo_riesgo"], umbral=datos["umbral"])
        instancia.pipeline = datos["pipeline"]
        instancia.version  = datos["version"]
        instancia.metricas_entrenamiento = datos.get("metricas", {})
        print(f"✓ Modelo cargado desde: {ruta}")
        return instancia


# ── Script de entrenamiento con datos sintéticos ────────────────────────

def generar_datos_sinteticos(n: int = 2000, seed: int = 42) -> pd.DataFrame:
    """
    Genera datos sintéticos para entrenamiento en ausencia de datos reales.
    En producción reemplazar con datos reales de las tablas:
        - pacientes (edad, sexo, imc via triaje)
        - antecedentes (factores de riesgo binarios)
        - triaje (signos vitales)
        - consultas (diagnósticos CIE-10)

    Query Django equivalente:
        from core.models import Paciente, Antecedente, Triaje
        # Construir DataFrame con los campos de FEATURES
    """
    rng = np.random.default_rng(seed)
    n_riesgo = int(n * 0.30)  # 30% tiene riesgo (desbalanceado, como en la realidad)

    def paciente_riesgo():
        return {
            "edad":                      rng.integers(45, 80),
            "sexo_numerico":             rng.integers(0, 2),
            "imc":                       rng.uniform(28, 42),
            "presion_sistolica":         rng.integers(130, 180),
            "presion_diastolica":        rng.integers(85, 120),
            "frecuencia_cardiaca":       rng.integers(70, 110),
            "saturacion_oxigeno":        rng.uniform(92, 99),
            "glucemia":                  rng.uniform(110, 250),
            "tiene_diabetes":            rng.choice([0, 1], p=[0.4, 0.6]),
            "tiene_hipertension":        rng.choice([0, 1], p=[0.3, 0.7]),
            "tiene_cardiopatia":         rng.choice([0, 1], p=[0.6, 0.4]),
            "tiene_enfermedad_renal":    rng.choice([0, 1], p=[0.7, 0.3]),
            "fuma":                      rng.choice([0, 1], p=[0.4, 0.6]),
            "consume_alcohol":           rng.choice([0, 1], p=[0.5, 0.5]),
            "sedentario":                rng.choice([0, 1], p=[0.3, 0.7]),
            "familiar_diabetes":         rng.choice([0, 1], p=[0.3, 0.7]),
            "familiar_hipertension":     rng.choice([0, 1], p=[0.3, 0.7]),
            "familiar_cardiopatia":      rng.choice([0, 1], p=[0.5, 0.5]),
            "num_consultas_ultimo_anio": rng.integers(3, 15),
            "num_hospitalizaciones":     rng.integers(1, 8),
            "tiene_riesgo":              1,
        }

    def paciente_sano():
        return {
            "edad":                      rng.integers(18, 50),
            "sexo_numerico":             rng.integers(0, 2),
            "imc":                       rng.uniform(18, 27),
            "presion_sistolica":         rng.integers(100, 130),
            "presion_diastolica":        rng.integers(60, 85),
            "frecuencia_cardiaca":       rng.integers(55, 80),
            "saturacion_oxigeno":        rng.uniform(96, 100),
            "glucemia":                  rng.uniform(70, 100),
            "tiene_diabetes":            0,
            "tiene_hipertension":        0,
            "tiene_cardiopatia":         0,
            "tiene_enfermedad_renal":    0,
            "fuma":                      rng.choice([0, 1], p=[0.8, 0.2]),
            "consume_alcohol":           rng.choice([0, 1], p=[0.7, 0.3]),
            "sedentario":                rng.choice([0, 1], p=[0.6, 0.4]),
            "familiar_diabetes":         rng.choice([0, 1], p=[0.7, 0.3]),
            "familiar_hipertension":     rng.choice([0, 1], p=[0.7, 0.3]),
            "familiar_cardiopatia":      rng.choice([0, 1], p=[0.8, 0.2]),
            "num_consultas_ultimo_anio": rng.integers(0, 3),
            "num_hospitalizaciones":     0,
            "tiene_riesgo":              0,
        }

    datos = [paciente_riesgo() for _ in range(n_riesgo)]
    datos += [paciente_sano() for _ in range(n - n_riesgo)]
    rng.shuffle(datos)
    return pd.DataFrame(datos)


if __name__ == "__main__":
    print("Generando datos sintéticos...")
    df = generar_datos_sinteticos(n=2000)

    # Entrenar un modelo por cada tipo de riesgo
    for tipo in TIPOS_RIESGO:
        print(f"\n{'#'*60}")
        modelo = ModeloRiesgoClinico(tipo_riesgo=tipo, umbral=0.5)
        modelo.entrenar(df, columna_objetivo="tiene_riesgo")
        modelo.guardar(f"ml/modelos_guardados/riesgo_{tipo}_v1.joblib")

    # Demo de inferencia
    print("\n" + "="*60)
    print("DEMO DE INFERENCIA")
    print("="*60)
    modelo_demo = ModeloRiesgoClinico.cargar("ml/modelos_guardados/riesgo_diabetes_tipo2_v1.joblib")

    paciente_alto_riesgo = {
        "edad": 62, "sexo_numerico": 1, "imc": 34.2,
        "presion_sistolica": 155, "presion_diastolica": 95,
        "frecuencia_cardiaca": 88, "saturacion_oxigeno": 96,
        "glucemia": 148,
        "tiene_diabetes": 0, "tiene_hipertension": 1, "tiene_cardiopatia": 0,
        "tiene_enfermedad_renal": 0, "fuma": 1, "consume_alcohol": 1, "sedentario": 1,
        "familiar_diabetes": 1, "familiar_hipertension": 1, "familiar_cardiopatia": 0,
        "num_consultas_ultimo_anio": 6, "num_hospitalizaciones": 1,
    }

    resultado = modelo_demo.predecir(paciente_alto_riesgo)
    print(f"\nPaciente: Hombre, 62 años, obeso, hipertenso, fumador")
    print(f"  Probabilidad de riesgo: {resultado['porcentaje_riesgo']}")
    print(f"  Clasificación:          {resultado['clasificacion']}")
    print(f"  Alerta:                 {resultado['nivel_alerta']}")
    print(f"  Factores identificados: {resultado['factores_riesgo']}")
    print(f"  Recomendación:          {resultado['recomendacion']}")
