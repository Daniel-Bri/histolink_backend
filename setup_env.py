"""
setup_env.py — Script de configuración automática de Histolink

Crea el entorno virtual, instala dependencias, configura la base de datos
y deja el proyecto listo para ejecutar.

Uso:
    python setup_env.py
"""

import subprocess
import sys
import os
import venv
from pathlib import Path


# ── Configuración ───────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
VENV_DIR = BASE_DIR / "venv"
REQUIREMENTS = BASE_DIR / "requirements.txt"

# Detectar el ejecutable de Python dentro del venv según el SO
if sys.platform == "win32":
    PYTHON = VENV_DIR / "Scripts" / "python.exe"
    PIP = VENV_DIR / "Scripts" / "pip.exe"
else:
    PYTHON = VENV_DIR / "bin" / "python"
    PIP = VENV_DIR / "bin" / "pip"


def print_header(msg: str):
    print(f"\n{'═' * 60}")
    print(f"  {msg}")
    print(f"{'═' * 60}")


def print_step(msg: str):
    print(f"  → {msg}")


def run(cmd: list, **kwargs):
    """Ejecuta un comando y muestra el output."""
    result = subprocess.run(
        cmd,
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
        **kwargs,
    )
    if result.returncode != 0:
        print(f"  ✗ Error ejecutando: {' '.join(str(c) for c in cmd)}")
        print(result.stderr)
        sys.exit(1)
    return result


def main():
    print_header("HISTOLINK — Configuración del Entorno")

    # ── 1. Crear entorno virtual ────────────────────────────────────────
    if VENV_DIR.exists():
        print_step("Entorno virtual ya existe en ./venv — omitiendo creación.")
    else:
        print_step("Creando entorno virtual en ./venv ...")
        venv.create(str(VENV_DIR), with_pip=True)
        print_step("✓ Entorno virtual creado.")

    # ── 2. Actualizar pip ───────────────────────────────────────────────
    print_step("Actualizando pip...")
    run([str(PYTHON), "-m", "pip", "install", "--upgrade", "pip"])
    print_step("✓ pip actualizado.")

    # ── 3. Instalar dependencias ────────────────────────────────────────
    print_step(f"Instalando dependencias desde {REQUIREMENTS.name}...")
    run([str(PIP), "install", "-r", str(REQUIREMENTS)])
    print_step("✓ Dependencias instaladas.")

    # ── 4. Crear base de datos PostgreSQL (si no existe) ────────────────
    print_step("Verificando base de datos PostgreSQL 'histolink'...")
    try:
        check_db = subprocess.run(
            [
                str(PYTHON), "-c",
                "import psycopg2; "
                "conn = psycopg2.connect(dbname='postgres', user='postgres', "
                "password='12345678', host='localhost', port='5432'); "
                "conn.autocommit = True; cur = conn.cursor(); "
                "cur.execute(\"SELECT 1 FROM pg_database WHERE datname = 'histolink'\"); "
                "exists = cur.fetchone(); "
                "print('EXISTS' if exists else 'NOT_FOUND'); "
                "cur.close(); conn.close()"
            ],
            capture_output=True, text=True, cwd=str(BASE_DIR),
        )
        if "NOT_FOUND" in check_db.stdout:
            print_step("Base de datos no encontrada. Creando 'histolink'...")
            run([
                str(PYTHON), "-c",
                "import psycopg2; "
                "conn = psycopg2.connect(dbname='postgres', user='postgres', "
                "password='12345678', host='localhost', port='5432'); "
                "conn.autocommit = True; cur = conn.cursor(); "
                "cur.execute('CREATE DATABASE histolink'); "
                "cur.close(); conn.close()"
            ])
            print_step("✓ Base de datos 'histolink' creada.")
        else:
            print_step("✓ Base de datos 'histolink' ya existe.")
    except Exception as e:
        print_step(f"⚠ No se pudo verificar la BD: {e}")
        print_step("  Asegúrate de que PostgreSQL esté corriendo y crea la BD manualmente:")
        print_step("  CREATE DATABASE histolink;")

    # ── 5. Migraciones ──────────────────────────────────────────────────
    print_step("Ejecutando migraciones de Django...")
    run([str(PYTHON), "manage.py", "migrate"])
    print_step("✓ Migraciones aplicadas.")

    # ── 6. Crear roles del sistema ──────────────────────────────────────
    print_step("Creando roles clínicos (auth_group)...")
    run([str(PYTHON), "manage.py", "create_groups"])
    print_step("✓ Roles creados (Médico, Enfermera, Administrativo, etc.).")

    # ── Resumen final ───────────────────────────────────────────────────
    print_header("✓ HISTOLINK LISTO PARA USAR")

    if sys.platform == "win32":
        activate = ".\\venv\\Scripts\\activate"
    else:
        activate = "source venv/bin/activate"

    print(f"""
  Para iniciar el servidor:

    1. Activar el entorno virtual:
       {activate}

    2. Ejecutar el servidor de desarrollo:
       python manage.py runserver

    3. Abrir en el navegador:
       http://127.0.0.1:8000/api/auth/login/

  Documentación de endpoints:
    Ver README.md
""")


if __name__ == "__main__":
    main()
