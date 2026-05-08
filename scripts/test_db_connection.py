"""
Verifica la conectividad con la base de datos Postgres en Supabase.

Uso (desde la raíz del proyecto):
    python scripts/test_db_connection.py

Resultado esperado:
    OK: Conexion exitosa
    OK: Postgres version: PostgreSQL 15.x ...
"""

import os
import sys
from pathlib import Path

# Asegurar que el .env de la raiz se cargue aunque corramos desde otra carpeta
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(dotenv_path=ENV_PATH)

DATABASE_URL = os.environ.get("DATABASE_URL")


def fail(msg: str) -> None:
    print(f"\n[ERROR] {msg}\n")
    sys.exit(1)


if not DATABASE_URL:
    fail(
        "La variable DATABASE_URL no esta definida.\n"
        f"Verifica que exista el archivo .env en: {ENV_PATH}\n"
        "Y que adentro tenga: DATABASE_URL=postgresql://..."
    )

if "[" in DATABASE_URL or "]" in DATABASE_URL:
    fail(
        "DATABASE_URL contiene corchetes [ ].\n"
        "Reemplaza [YOUR-PASSWORD] por tu contrasena real (sin corchetes)."
    )

if "TU-PASSWORD" in DATABASE_URL or "TU-PROYECTO-REF" in DATABASE_URL:
    fail(
        "DATABASE_URL todavia tiene los placeholders del template.\n"
        "Reemplaza TU-PROYECTO-REF y TU-PASSWORD por los valores reales."
    )

# Ocultar contrasena al imprimir host
host_part = DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "?"
print(f"Conectando a: {host_part}\n")

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version()")).scalar()
        current_db = conn.execute(text("SELECT current_database()")).scalar()
        current_user = conn.execute(text("SELECT current_user")).scalar()

    print("=" * 60)
    print("OK: Conexion exitosa a Supabase")
    print("=" * 60)
    print(f"  Database : {current_db}")
    print(f"  User     : {current_user}")
    print(f"  Version  : {str(version)[:60]}...")
    print("=" * 60)
    print("\nTu PC se conecta a Supabase correctamente. Listo para el siguiente paso.\n")

except Exception as e:
    print("=" * 60)
    print("ERROR al conectar a Supabase")
    print("=" * 60)
    print(f"\nDetalle del error:\n{e}\n")
    print("Cosas para verificar:")
    print("  1. Que la URL en .env sea exactamente la del Session pooler (puerto 5432)")
    print("  2. Que la contrasena en la URL sea la nueva (sin corchetes ni placeholders)")
    print("  3. Que tu proyecto de Supabase este 'Healthy' en el dashboard")
    print("  4. Que tengas conexion a internet")
    sys.exit(1)
