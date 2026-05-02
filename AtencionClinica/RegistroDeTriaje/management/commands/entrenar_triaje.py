"""
AtencionClinica/RegistroDeTriaje/management/commands/entrenar_triaje.py

Entrena el modelo NLP de triaje y lo guarda como triaje_v1.joblib.

Uso:
    python manage.py entrenar_triaje
    python manage.py entrenar_triaje --multiplicador 20
    python manage.py entrenar_triaje --salida ml/modelos_guardados/triaje_dev.joblib
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Entrena el modelo NLP de triaje (TF-IDF + Naive Bayes) y guarda el archivo .joblib"

    def add_arguments(self, parser):
        parser.add_argument(
            "--multiplicador",
            type=int,
            default=15,
            help="Factor de multiplicación del dataset sintético (default: 15).",
        )
        parser.add_argument(
            "--salida",
            type=str,
            default="ml/modelos_guardados/triaje_v1.joblib",
            help="Ruta de salida del modelo entrenado.",
        )

    def handle(self, *args, **options):
        from ml.modelo_triaje import ModeloTriaje, generar_dataset_triaje

        multiplicador = options["multiplicador"]
        salida        = options["salida"]

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("Histolink — Entrenamiento Modelo Triaje NLP")
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"  Multiplicador de dataset : {multiplicador}")
        self.stdout.write(f"  Archivo de salida        : {salida}")
        self.stdout.write("")

        self.stdout.write("Generando dataset sintético...")
        textos, etiquetas = generar_dataset_triaje(multiplicador=multiplicador)
        self.stdout.write(f"  Total de ejemplos generados: {len(textos)}")

        self.stdout.write("\nEntrenando modelo...")
        modelo   = ModeloTriaje()
        metricas = modelo.entrenar(textos, etiquetas)

        self.stdout.write(
            f"\nAccuracy CV (5-fold): "
            f"{metricas['accuracy_cv_mean']} ± {metricas['accuracy_cv_std']}"
        )

        modelo.guardar(salida)
        self.stdout.write(self.style.SUCCESS(f"\n✓ Modelo guardado en: {salida}"))
        self.stdout.write(
            "\nPara que Django use el nuevo modelo reinicia el servidor "
            "(el Singleton lo recarga al arrancar).\n"
        )
