import time

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = "Espera a que PostgreSQL esté listo antes de continuar."

    def add_arguments(self, parser):
        parser.add_argument("--retries", type=int, default=30)
        parser.add_argument("--delay",   type=float, default=2.0)

    def handle(self, *args, **options):
        retries = options["retries"]
        delay   = options["delay"]
        for attempt in range(1, retries + 1):
            try:
                conn = connections["default"]
                conn.ensure_connection()
                self.stdout.write(self.style.SUCCESS("Base de datos disponible."))
                return
            except OperationalError:
                self.stdout.write(f"  [{attempt}/{retries}] PostgreSQL no disponible, reintentando en {delay}s...")
                time.sleep(delay)
        self.stderr.write(self.style.ERROR("No se pudo conectar a la base de datos tras todos los intentos."))
        raise SystemExit(1)
