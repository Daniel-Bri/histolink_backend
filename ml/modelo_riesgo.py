"""
ml/modelo_riesgo.py

MODELO 1 — Predicción de Riesgos Clínicos a Largo Plazo
────────────────────────────────────────────────────────
Usa Regresión Logística para estimar la probabilidad de que
un paciente desarrolle patologías crónicas o complicaciones futuras.

T003: Script de entrenamiento para 4 modelos de riesgo crónico.
"""

import joblib
import numpy as np
import pandas as pd
import os
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    classification_report, roc_auc_score,
    brier_score_loss
)
from sklearn.impute import SimpleImputer

# Configuración de rutas
ML_MODELS_PATH = os.environ.get("ML_MODELS_PATH", "ml/modelos_guardados")

# ── Tipos de riesgo ──────────────────────────────────────────────────
TIPOS_RIESGO = {
    "diabetes_tipo2":     "Riesgo de desarrollar Diabetes Tipo 2",
    "hipertension":       "Riesgo de desarrollar Hipertensión Arterial",
    "enfermedad_renal":   "Riesgo de Enfermedad Renal Crónica",
    "evento_cardiovascular": "Riesgo de Evento Cardiovascular (infarto/ACV)",
}

# ── Variables clínicas (FEATURES) ──────────────────────────────────────
FEATURES = [
    'edad', 'sexo_numerico', 'imc', 'presion_sistolica', 'presion_diastolica',
    'frecuencia_cardiaca', 'saturacion_oxigeno', 'glucemia', 'tiene_diabetes',
    'tiene_hipertension', 'tiene_cardiopatia', 'tiene_enfermedad_renal',
    'fuma', 'consume_alcohol', 'sedentario', 'familiar_diabetes',
    'familiar_hipertension', 'familiar_cardiopatia',
    'num_consultas_ultimo_anio', 'num_hospitalizaciones'
]

class ModeloRiesgoClinico:
    """
    Clase para entrenamiento e inferencia de riesgos clínicos.
    """

    def __init__(self, tipo_riesgo: str = "diabetes_tipo2"):
        if tipo_riesgo not in TIPOS_RIESGO:
            raise ValueError(f"Tipo de riesgo no válido: {tipo_riesgo}")
        self.tipo_riesgo = tipo_riesgo
        self.pipeline = self._construir_pipeline()
        self.version = "1.0"

    def _construir_pipeline(self):
        """Pipeline según directrices T003."""
        return Pipeline([
            ("imputador", SimpleImputer(strategy="median")),
            ("escalador", StandardScaler()),
            ("modelo", LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
                random_state=42,
                solver="lbfgs"
            )),
        ])

    def entrenar(self, df: pd.DataFrame, target: str = "tiene_riesgo"):
        """Entrena y evalúa el modelo."""
        X = df[FEATURES]
        y = df[target]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        self.pipeline.fit(X_train, y_train)
        
        # Evaluación básica
        y_prob = self.pipeline.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_prob)
        print(f"[{self.tipo_riesgo}] AUC-ROC: {auc:.4f}")
        return auc

    def predecir(self, datos: dict) -> dict:
        """Realiza predicción y clasifica según umbrales de negocio."""
        df_input = pd.DataFrame([datos])[FEATURES]
        prob = float(self.pipeline.predict_proba(df_input)[0, 1])

        # Lógica de clasificación T003
        if prob >= 0.70:
            clasificacion = "ALTO"
            nivel_alerta = "CRÍTICO"
            recomendacion = "Control clínico inmediato."
        elif prob >= 0.35:
            clasificacion = "MODERADO"
            nivel_alerta = "ADVERTENCIA"
            recomendacion = "Seguimiento periódico."
        else:
            clasificacion = "BAJO"
            nivel_alerta = "NORMAL"
            recomendacion = "Controles rutinarios anuales."

        return {
            "probabilidad": round(prob, 4),
            "clasificacion": clasificacion,
            "nivel_alerta": nivel_alerta,
            "recomendacion": recomendacion
        }

    def guardar(self, ruta: str):
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, ruta, compress=3)

    @classmethod
    def cargar(cls, ruta: str):
        return joblib.load(ruta)

def generar_datos_sinteticos(n=1000):
    """Genera datos para el script de entrenamiento."""
    rng = np.random.default_rng(42)
    data = []
    for _ in range(n):
        # Paciente con riesgo
        es_riesgo = rng.choice([0, 1], p=[0.7, 0.3])
        if es_riesgo:
            row = {
                'edad': rng.integers(50, 90),
                'sexo_numerico': rng.integers(0, 2),
                'imc': rng.uniform(28, 45),
                'presion_sistolica': rng.integers(140, 190),
                'presion_diastolica': rng.integers(90, 110),
                'frecuencia_cardiaca': rng.integers(80, 110),
                'saturacion_oxigeno': rng.uniform(90, 95),
                'glucemia': rng.uniform(126, 250),
                'tiene_diabetes': rng.choice([0, 1]),
                'tiene_hipertension': 1,
                'tiene_cardiopatia': rng.choice([0, 1]),
                'tiene_enfermedad_renal': rng.choice([0, 1]),
                'fuma': 1, 'consume_alcohol': rng.choice([0, 1]),
                'sedentario': 1, 'familiar_diabetes': 1,
                'familiar_hipertension': 1, 'familiar_cardiopatia': 1,
                'num_consultas_ultimo_anio': rng.integers(5, 15),
                'num_hospitalizaciones': rng.integers(1, 5),
                'tiene_riesgo': 1
            }
        else:
            row = {
                'edad': rng.integers(18, 45),
                'sexo_numerico': rng.integers(0, 2),
                'imc': rng.uniform(18, 25),
                'presion_sistolica': rng.integers(110, 130),
                'presion_diastolica': rng.integers(70, 85),
                'frecuencia_cardiaca': rng.integers(60, 80),
                'saturacion_oxigeno': rng.uniform(96, 99),
                'glucemia': rng.uniform(70, 100),
                'tiene_diabetes': 0, 'tiene_hipertension': 0,
                'tiene_cardiopatia': 0, 'tiene_enfermedad_renal': 0,
                'fuma': 0, 'consume_alcohol': 0, 'sedentario': 0,
                'familiar_diabetes': 0, 'familiar_hipertension': 0,
                'familiar_cardiopatia': 0,
                'num_consultas_ultimo_anio': rng.integers(0, 2),
                'num_hospitalizaciones': 0,
                'tiene_riesgo': 0
            }
        data.append(row)
    return pd.DataFrame(data)

if __name__ == "__main__":
    print(f"Iniciando entrenamiento en: {ML_MODELS_PATH}")
    df = generar_datos_sinteticos(2000)
    
    for tipo in TIPOS_RIESGO:
        modelo = ModeloRiesgoClinico(tipo_riesgo=tipo)
        modelo.entrenar(df)
        ruta = os.path.join(ML_MODELS_PATH, f"riesgo_{tipo}_v1.joblib")
        modelo.guardar(ruta)
        print(f"Modelo {tipo} guardado en {ruta}")
