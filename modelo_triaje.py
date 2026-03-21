"""
ml/modelo_triaje.py

MODELO 2 — Clasificación de Prioridad de Triaje (NLP)
──────────────────────────────────────────────────────
Usa TF-IDF + Naive Bayes Multinomial para clasificar el nivel
de urgencia de un paciente a partir de la descripción en texto libre
de sus síntomas al momento de llegada.

Escala de triaje (Manchester / ESI adaptada):
    1 = ROJO     → Emergencia inmediata (riesgo de vida)
    2 = NARANJA  → Muy urgente (≤ 15 min)
    3 = AMARILLO → Urgente (≤ 60 min)
    4 = VERDE    → Poco urgente (≤ 120 min)
    5 = AZUL     → No urgente

Fórmula matemática (Naive Bayes Multinomial):
    P(Ck | x) ∝ P(Ck) × ∏ P(xi | Ck)

TF-IDF penaliza palabras comunes y da más peso a términos médicos
específicos de cada nivel de urgencia.

Uso:
    from ml.modelo_triaje import ModeloTriaje
    modelo = ModeloTriaje()
    modelo.entrenar(textos, etiquetas)
    resultado = modelo.predecir("dolor en el pecho fuerte, dificultad para respirar")
"""

import re
import unicodedata
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.calibration import CalibratedClassifierCV


# ── Configuración de niveles de triaje ──────────────────────────────────
NIVELES_TRIAJE = {
    1: {"color": "ROJO",     "nombre": "Emergencia inmediata",   "max_espera": "0 min",   "alerta": "CRITICO"},
    2: {"color": "NARANJA",  "nombre": "Muy urgente",            "max_espera": "15 min",  "alerta": "CRITICO"},
    3: {"color": "AMARILLO", "nombre": "Urgente",                "max_espera": "60 min",  "alerta": "ADVERTENCIA"},
    4: {"color": "VERDE",    "nombre": "Poco urgente",           "max_espera": "120 min", "alerta": "NORMAL"},
    5: {"color": "AZUL",     "nombre": "No urgente",             "max_espera": "240 min", "alerta": "NORMAL"},
}

# ── Stopwords en español (embebidas — no requiere NLTK ni internet) ─────
# Lista curada para texto clínico: preserva negaciones y palabras médicas
STOPWORDS_ES = {
    "a","al","algo","algunas","algunos","ante","antes","como","con","contra",
    "cual","cuando","de","del","desde","donde","durante","e","el","ella",
    "ellas","ellos","en","entre","era","es","esa","esas","ese","eso","esos",
    "esta","estas","este","esto","estos","fue","han","has","hay","he","i",
    "la","las","le","les","lo","los","me","mi","mia","mis","muy","na","ni",
    "nos","o","para","pero","por","que","se","si","sobre","su","sus","tal",
    "te","ti","tus","un","una","unas","uno","unos","ya","yo",
    # Palabras clínicas muy comunes que no aportan discriminación
    "paciente","consulta","refiere","acude","presenta","manifiesta","indica",
    "comenta","dice","menciona","señala","motivo","atencion","dia","dias",
    "hace","desde","ayer","hoy","semana","semanas","mes","meses","horas",
}


# ── Preprocesamiento de texto clínico ───────────────────────────────────

def preprocesar_texto(texto: str) -> str:
    """
    Limpia y normaliza texto clínico en español.

    Pasos:
        1. Minúsculas
        2. Eliminar tildes (unicodedata)
        3. Eliminar puntuación y números sueltos
        4. Eliminar stopwords (preservando palabras médicas)
        5. Eliminar espacios extra
    """
    if not texto or not isinstance(texto, str):
        return ""

    # 1. Minúsculas
    texto = texto.lower().strip()

    # 2. Quitar tildes y caracteres especiales del español
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))

    # 3. Eliminar puntuación pero preservar espacios entre palabras
    texto = re.sub(r"[^\w\s]", " ", texto)

    # 4. Eliminar números standalone (ej: "3 dias" → "dias")
    texto = re.sub(r"\b\d+\b", "", texto)

    # 5. Eliminar stopwords
    tokens = texto.split()
    tokens = [t for t in tokens if t not in STOPWORDS_ES and len(t) > 2]

    return " ".join(tokens)


# ── Modelo principal ─────────────────────────────────────────────────────

class ModeloTriaje:
    """
    Clasificador de prioridad de triaje usando TF-IDF + Naive Bayes Multinomial.

    El pipeline es:
        texto_raw → preprocesar_texto() → TfidfVectorizer → MultinomialNB → prioridad 1–5
    """

    def __init__(self):
        self.pipeline   = None
        self.version    = "1.0"
        self.metricas   = {}
        self.clases     = None
        self._construir_pipeline()

    def _construir_pipeline(self):
        """
        TF-IDF configurado para texto médico corto (síntomas del paciente):
            - ngram_range (1,2): captura bigramas como "dolor_pecho", "sin_aire"
            - max_features 5000: vocabulario suficiente para terminología médica
            - sublinear_tf: aplica log(tf) para no penalizar demasiado términos frecuentes
            - min_df 2: ignora términos que aparecen en menos de 2 documentos (ruido)
        """
        tfidf = TfidfVectorizer(
            preprocessor=preprocesar_texto,
            ngram_range=(1, 2),
            max_features=5000,
            sublinear_tf=True,
            min_df=2,
            max_df=0.95,
        )

        # MultinomialNB con alpha=0.5 (suavizado de Laplace moderado)
        # Calibrado para obtener probabilidades bien escaladas por nivel
        nb = MultinomialNB(alpha=0.5)
        nb_calibrado = CalibratedClassifierCV(nb, cv=5, method="isotonic")

        self.pipeline = Pipeline([
            ("tfidf",   tfidf),
            ("modelo",  nb_calibrado),
        ])

    # ── Entrenamiento ───────────────────────────────────────────────────

    def entrenar(self, textos: list, etiquetas: list) -> dict:
        """
        Entrena el modelo con textos de síntomas y sus niveles de triaje.

        Args:
            textos:    lista de strings con la descripción de síntomas del paciente.
            etiquetas: lista de enteros 1–5 (nivel de triaje correspondiente).

        Returns:
            dict con métricas del entrenamiento.
        """
        textos   = list(textos)
        etiquetas = list(etiquetas)

        assert len(textos) == len(etiquetas), "textos y etiquetas deben tener el mismo largo"
        assert all(e in NIVELES_TRIAJE for e in etiquetas), "Las etiquetas deben ser 1–5"

        print(f"\n{'='*60}")
        print("ENTRENANDO: Clasificador de Triaje (NLP)")
        print(f"{'='*60}")
        print(f"Total muestras: {len(textos)}")

        # Distribución de clases
        from collections import Counter
        dist = Counter(etiquetas)
        for nivel in sorted(dist):
            info = NIVELES_TRIAJE[nivel]
            print(f"  Nivel {nivel} ({info['color']:8}): {dist[nivel]:4} muestras")

        # Split 80/20 estratificado
        X_train, X_test, y_train, y_test = train_test_split(
            textos, etiquetas, test_size=0.2, random_state=42, stratify=etiquetas
        )

        # Entrenar
        self.pipeline.fit(X_train, y_train)
        self.clases = self.pipeline.classes_

        # Evaluar
        y_pred = self.pipeline.predict(X_test)

        # Cross-validation
        cv    = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_acc = cross_val_score(self.pipeline, textos, etiquetas, cv=cv, scoring="accuracy")

        nombres_clases = [f"{i}-{NIVELES_TRIAJE[i]['color']}" for i in sorted(NIVELES_TRIAJE)]
        reporte = classification_report(
            y_test, y_pred,
            target_names=nombres_clases,
            output_dict=True
        )

        self.metricas = {
            "n_muestras":    len(textos),
            "accuracy_cv_mean": round(cv_acc.mean(), 4),
            "accuracy_cv_std":  round(cv_acc.std(), 4),
            "reporte":       reporte,
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        }

        print(f"\nRESULTADOS:")
        print(f"  Accuracy (CV 5fold): {self.metricas['accuracy_cv_mean']} ± {self.metricas['accuracy_cv_std']}")
        print(f"\n{classification_report(y_test, y_pred, target_names=nombres_clases)}")

        # Vocabulario más importante por nivel
        self._mostrar_vocabulario_clave()

        return self.metricas

    def _mostrar_vocabulario_clave(self, top_n: int = 8):
        """Muestra las palabras más discriminativas por nivel de triaje."""
        try:
            tfidf = self.pipeline.named_steps["tfidf"]
            vocab = np.array(tfidf.get_feature_names_out())
            # Extraer NB base del calibrador
            nb_base = self.pipeline.named_steps["modelo"].calibrated_classifiers_[0].estimator
            log_probs = nb_base.feature_log_prob_

            print("\nVOCABULARIO CLAVE POR NIVEL:")
            for i, clase in enumerate(nb_base.classes_):
                top_idx  = np.argsort(log_probs[i])[-top_n:][::-1]
                keywords = vocab[top_idx]
                info     = NIVELES_TRIAJE[int(clase)]
                print(f"  {clase}-{info['color']:8}: {', '.join(keywords)}")
        except Exception:
            pass

    # ── Inferencia ──────────────────────────────────────────────────────

    def predecir(self, texto_sintomas: str,
                 signos_vitales: dict = None) -> dict:
        """
        Predice el nivel de triaje a partir del texto de síntomas.

        Args:
            texto_sintomas: descripción libre de síntomas (lo que dice el paciente
                            o lo que anota la enfermera en motivo_consulta_triaje).
            signos_vitales: dict opcional con valores del triaje para ajuste de urgencia.
                            Si los signos vitales son críticos, se puede elevar la prioridad.

        Returns:
            dict con:
                nivel_predicho:       int 1–5
                color:                str (ROJO/NARANJA/AMARILLO/VERDE/AZUL)
                nombre:               str descripción del nivel
                max_espera:           str tiempo máximo de espera
                nivel_alerta:         str
                confianza:            float 0–1
                probabilidades:       dict con P de cada nivel
                texto_procesado:      str texto después del preprocesamiento
                ajuste_signos:        str nota si los signos vitales modificaron la predicción
        """
        if self.pipeline is None:
            raise RuntimeError("El modelo no está entrenado.")

        texto_procesado = preprocesar_texto(texto_sintomas)
        if not texto_procesado:
            # Texto vacío o sin información → nivel de espera por defecto
            return self._respuesta_sin_texto()

        # Predicción NLP
        probs_array = self.pipeline.predict_proba([texto_sintomas])[0]
        clases      = self.pipeline.classes_

        probs_dict = {int(c): round(float(p), 4) for c, p in zip(clases, probs_array)}
        nivel_nlp  = int(clases[np.argmax(probs_array)])
        confianza  = float(np.max(probs_array))

        # Ajuste por signos vitales críticos (reglas clínicas duras)
        nivel_final, nota_ajuste = self._ajustar_por_signos(nivel_nlp, signos_vitales)

        info = NIVELES_TRIAJE[nivel_final]

        return {
            "nivel_predicho":    nivel_final,
            "nivel_nlp":         nivel_nlp,
            "color":             info["color"],
            "nombre":            info["nombre"],
            "max_espera":        info["max_espera"],
            "nivel_alerta":      info["alerta"],
            "confianza":         round(confianza, 4),
            "confianza_pct":     f"{confianza*100:.1f}%",
            "probabilidades":    probs_dict,
            "texto_procesado":   texto_procesado,
            "ajuste_signos":     nota_ajuste,
            "version_modelo":    self.version,
        }

    def _ajustar_por_signos(self, nivel_nlp: int,
                             signos: dict) -> tuple[int, str]:
        """
        Aplica reglas clínicas duras basadas en signos vitales.
        Si los signos son críticos, el nivel no puede ser mayor a 2 (NARANJA).
        Si los signos son estables, no se sube la prioridad artificialmente.
        """
        if not signos:
            return nivel_nlp, ""

        notas = []
        nivel = nivel_nlp

        spo2 = signos.get("saturacion_oxigeno")
        if spo2 is not None:
            if spo2 < 90:
                nivel = min(nivel, 1)
                notas.append(f"SpO2 crítica ({spo2}%) → ROJO")
            elif spo2 < 94:
                nivel = min(nivel, 2)
                notas.append(f"SpO2 baja ({spo2}%) → mínimo NARANJA")

        ps = signos.get("presion_sistolica")
        if ps is not None:
            if ps < 80 or ps > 200:
                nivel = min(nivel, 1)
                notas.append(f"Presión sistólica extrema ({ps} mmHg) → ROJO")
            elif ps < 90 or ps > 180:
                nivel = min(nivel, 2)
                notas.append(f"Presión sistólica crítica ({ps} mmHg) → mínimo NARANJA")

        fc = signos.get("frecuencia_cardiaca")
        if fc is not None:
            if fc < 40 or fc > 150:
                nivel = min(nivel, 1)
                notas.append(f"Frecuencia cardíaca extrema ({fc} lpm) → ROJO")
            elif fc < 50 or fc > 130:
                nivel = min(nivel, 2)
                notas.append(f"Frecuencia cardíaca crítica ({fc} lpm) → mínimo NARANJA")

        dolor = signos.get("escala_dolor")
        if dolor is not None and dolor >= 9:
            nivel = min(nivel, 2)
            notas.append(f"Dolor extremo (EVA {dolor}/10) → mínimo NARANJA")

        glasgow = signos.get("glasgow_score")
        if glasgow is not None:
            if glasgow <= 8:
                nivel = 1
                notas.append(f"Glasgow crítico ({glasgow}) → ROJO inmediato")
            elif glasgow < 13:
                nivel = min(nivel, 2)
                notas.append(f"Glasgow comprometido ({glasgow}) → mínimo NARANJA")

        nota = " | ".join(notas) if notas else "Sin ajuste por signos vitales"
        return nivel, nota

    def _respuesta_sin_texto(self) -> dict:
        return {
            "nivel_predicho": 3, "nivel_nlp": 3,
            "color": "AMARILLO", "nombre": "Urgente (sin texto disponible)",
            "max_espera": "60 min", "nivel_alerta": "ADVERTENCIA",
            "confianza": 0.0, "confianza_pct": "0.0%",
            "probabilidades": {1:0,2:0,3:1,4:0,5:0},
            "texto_procesado": "",
            "ajuste_signos": "Texto vacío — asignado AMARILLO por defecto",
            "version_modelo": self.version,
        }

    # ── Persistencia ────────────────────────────────────────────────────

    def guardar(self, ruta: str):
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "pipeline": self.pipeline,
            "version":  self.version,
            "metricas": self.metricas,
            "clases":   self.clases,
        }, ruta, compress=3)
        print(f"✓ Modelo triaje guardado en: {ruta}")

    @classmethod
    def cargar(cls, ruta: str) -> "ModeloTriaje":
        datos = joblib.load(ruta)
        instancia = cls()
        instancia.pipeline = datos["pipeline"]
        instancia.version  = datos["version"]
        instancia.metricas = datos.get("metricas", {})
        instancia.clases   = datos.get("clases")
        print(f"✓ Modelo triaje cargado desde: {ruta}")
        return instancia


# ── Datos sintéticos para entrenamiento ─────────────────────────────────

EJEMPLOS_TRIAJE = {
    1: [  # ROJO — Emergencia inmediata
        "dolor pecho intenso irradiacion brazo izquierdo sudoracion fria desmayo",
        "no respira perdida conciencia inconsciente sin pulso",
        "trauma craneal severo sangrado abundante cabeza accidente",
        "dificultad respiratoria extrema labios morados no puede hablar",
        "convulsiones generalizadas no cede fiebre muy alta",
        "herida arma blanca abdomen profusa hemorragia",
        "quemaduras extensas cara cuello cuerpo",
        "reaccion alergica severa cara hinchada garganta cerrada anafilaxia",
        "paro respiratorio boca a boca reanimacion",
        "ictus facial paralisis arm derecho afasia",
        "presion muy baja desmayo palido sudoroso frio",
        "aplastamiento extremidad sangre no para torniquete",
        "sepsis fiebre alta confusion hipotension taquicardia",
        "intoxicacion medicamentos muchas pastillas inconsciencia",
        "parto obstruido bebe no sale urgencia obstetrica",
        "cuerpo extraño via aerea asfixia cianosis",
    ],
    2: [  # NARANJA — Muy urgente
        "dolor pecho moderado presion opresion sin irradiacion sudoracion leve",
        "dificultad respiratoria moderada puede hablar frases cortas",
        "glucemia muy alta 400 mg diabetes descontrolada vomitos",
        "crisis hipertensiva cefalea intensa vision borrosa",
        "fractura expuesta hueso visible sin hemorragia mayor",
        "dolor abdominal severo rigidez vientre fiebre",
        "trauma ocular golpe ojo vision afectada",
        "quemadura segundo grado manos brazos",
        "convulsion febril primera vez menor dos años",
        "deshidratacion severa vomitos diarrea ojos hundidos",
        "pensamiento suicida plan concreto intento reciente",
        "retencion urinaria aguda dolor intenso no orina",
        "epistaxis abundante no cede 30 minutos",
        "dolor lumbar severo irradiacion pierna entumecimiento",
        "fiebre 40 grados rigidez nuca fotofobia adulto",
    ],
    3: [  # AMARILLO — Urgente
        "dolor abdominal moderado varios dias vomitos ocasionales",
        "fiebre 38 grados tos seca tres dias malestar general",
        "herida cortante mano profunda necesita puntos no sangra activamente",
        "cefalea moderada sin signos alarma desde ayer analgesicos no funcionan",
        "infeccion urinaria ardor al orinar frecuencia aumento",
        "esguince tobillo caida caminando dolor moderado hinchado",
        "dolor toracico atipico sin irradiacion leve jovencito",
        "vomitos repetidos cinco veces sin sangre sin fiebre",
        "reaccion alergica leve urticaria sin dificultad respiratoria",
        "dolor en muela intenso cara hinchada absceso dental",
        "conjuntivitis ojo rojo secrecion amarilla ambos ojos",
        "contusion cabeza sin perdida conciencia dolor leve",
        "dolor pelvico mujer embarazada primer trimestre sin sangrado",
        "hiperglucemia leve 200 mg sin signos descompensacion",
        "tension arterial alta 160 sin sintomas neurologicos",
    ],
    4: [  # VERDE — Poco urgente
        "resfrio comun estornudos congestion nasal sin fiebre",
        "tos seca leve sin fiebre una semana",
        "erupciones piel leve picazon sin fiebre estables",
        "dolor garganta leve sin fiebre puede comer",
        "molestia leve espalda baja cronica",
        "control cita seguimiento diabetes hipertension estables",
        "renovacion receta medicamentos cronicos",
        "herida superficial arañazo leve limpia sin profundidad",
        "dolor rodilla cronica leve sin trauma reciente",
        "fatiga leve sin otros sintomas semanas estudio",
    ],
    5: [  # AZUL — No urgente
        "certificado medico trabajo escuela sin enfermedad actual",
        "solicitud resultado laboratorio viejo",
        "consulta nutricional obesidad sin urgencia",
        "revision preventiva anual sin molestias",
        "solicitud derivacion especialista ya coordinada",
        "pregunta sobre medicamento indicacion anterior",
        "seguimiento postoperatorio cicatriza bien sin complicaciones",
    ],
}


def generar_dataset_triaje(multiplicador: int = 15) -> tuple:
    """
    Genera dataset de entrenamiento a partir de los ejemplos base.
    multiplicador: veces que se repite cada ejemplo (con variaciones leves).
    """
    import random
    random.seed(42)

    textos, etiquetas = [], []

    # Variaciones de palabras para aumentar el dataset
    variaciones = {
        "dolor": ["molestia", "dolor fuerte", "duele", "duele mucho"],
        "fiebre": ["temperatura alta", "calentura", "febricula"],
        "vomitos": ["nauseas con vomito", "vomitando", "arcadas"],
        "sangrado": ["hemorragia", "sangre", "sangra"],
        "dificultad": ["problemas", "no puede", "cuesta trabajo"],
    }

    for nivel, ejemplos in EJEMPLOS_TRIAJE.items():
        for ejemplo in ejemplos:
            textos.append(ejemplo)
            etiquetas.append(nivel)
            # Generar variaciones
            for _ in range(multiplicador - 1):
                texto_var = ejemplo
                for original, alts in variaciones.items():
                    if original in texto_var and random.random() < 0.3:
                        texto_var = texto_var.replace(
                            original, random.choice(alts), 1
                        )
                textos.append(texto_var)
                etiquetas.append(nivel)

    # Mezclar
    combined = list(zip(textos, etiquetas))
    random.shuffle(combined)
    textos, etiquetas = zip(*combined)
    return list(textos), list(etiquetas)


if __name__ == "__main__":
    print("Generando dataset de triaje...")
    textos, etiquetas = generar_dataset_triaje(multiplicador=15)
    print(f"Total ejemplos: {len(textos)}")

    modelo = ModeloTriaje()
    modelo.entrenar(textos, etiquetas)
    modelo.guardar("ml/modelos_guardados/triaje_v1.joblib")

    # ── Demo de inferencia ───────────────────────────────────────────────
    print("\n" + "="*60)
    print("DEMO DE INFERENCIA")
    print("="*60)

    modelo_demo = ModeloTriaje.cargar("ml/modelos_guardados/triaje_v1.joblib")

    casos = [
        ("dolor en el pecho muy fuerte, me cuesta respirar, siento el brazo izquierdo dormido",
         {"saturacion_oxigeno": 91, "presion_sistolica": 85, "frecuencia_cardiaca": 130}),
        ("tengo fiebre hace tres días, tos, me duele la garganta pero puedo comer",
         {"saturacion_oxigeno": 97, "presion_sistolica": 115, "frecuencia_cardiaca": 88}),
        ("vengo a renovar mi receta de metformina, me siento bien",
         None),
    ]

    for texto, signos in casos:
        res = modelo_demo.predecir(texto, signos_vitales=signos)
        print(f"\nTexto: '{texto[:60]}...'")
        print(f"  → Nivel: {res['nivel_predicho']} {res['color']} — {res['nombre']}")
        print(f"  → Confianza: {res['confianza_pct']}")
        print(f"  → Max espera: {res['max_espera']}")
        if res["ajuste_signos"] and "Sin ajuste" not in res["ajuste_signos"]:
            print(f"  → Ajuste signos: {res['ajuste_signos']}")
