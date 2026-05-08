"""
Migra los datos de SQLite (data/lima_importadores.db) a Postgres (Supabase).

Uso (corre una vez, despues de configurar DATABASE_URL en .env):
    python scripts/migrate_sqlite_to_postgres.py

Es idempotente: lo podes correr varias veces sin generar duplicados
(usa MERGE/UPSERT por la primary key).
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from lima_importadores.storage.models import (
    Base, Business, WebsiteCheck, ScrapeRun, CallOutcome,
)


SQLITE_PATH = PROJECT_ROOT / "data" / "lima_importadores.db"
DATABASE_URL = os.environ.get("DATABASE_URL")


def fail(msg: str) -> None:
    print(f"\n[ERROR] {msg}\n")
    sys.exit(1)


if not DATABASE_URL:
    fail("DATABASE_URL no esta definida en .env")

if not SQLITE_PATH.exists():
    fail(
        f"No existe la base SQLite en: {SQLITE_PATH}\n"
        f"Si ya migraste antes, este script no es necesario."
    )

print(f"Origen : {SQLITE_PATH}")
print(f"Destino: {DATABASE_URL.split('@')[-1]}")
print()

sqlite_engine = create_engine(f"sqlite:///{SQLITE_PATH}")
pg_engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 1) Crear todas las tablas en Postgres si no existen
print("[1/5] Creando schema en Postgres (idempotente)...")
Base.metadata.create_all(pg_engine)
print("      OK\n")

SrcSession = sessionmaker(bind=sqlite_engine)
DstSession = sessionmaker(bind=pg_engine)


def migrate_table(model_class, label):
    print(f"      Leyendo {label} desde SQLite...")
    with SrcSession() as src:
        rows = src.query(model_class).all()
        # Capturar datos antes de cerrar la sesion source
        cols = [c.name for c in model_class.__table__.columns]
        data_list = [{c: getattr(r, c) for c in cols} for r in rows]
    print(f"      {len(data_list)} registros encontrados")

    if not data_list:
        print(f"      (nada que migrar)\n")
        return

    print(f"      Insertando en Postgres con MERGE...")
    with DstSession() as dst:
        # Usar merge() para idempotencia: inserta si no existe, actualiza si existe.
        # Reconstruye instancias del modelo a partir de los dicts.
        for data in data_list:
            instance = model_class(**data)
            dst.merge(instance)
        dst.commit()
    print(f"      OK\n")


print("[2/5] Migrando tabla businesses...")
migrate_table(Business, "businesses")

print("[3/5] Migrando tabla website_checks...")
migrate_table(WebsiteCheck, "website_checks")

print("[4/5] Migrando tabla scrape_runs...")
migrate_table(ScrapeRun, "scrape_runs")

# 5) Actualizar las sequences de Postgres para que el proximo INSERT
#    no colisione con los IDs migrados desde SQLite.
print("[5/5] Sincronizando sequences de Postgres...")
sequences = [
    ("businesses_id_seq", "businesses"),
    ("website_checks_id_seq", "website_checks"),
    ("scrape_runs_id_seq", "scrape_runs"),
    ("call_outcomes_id_seq", "call_outcomes"),
]
with DstSession() as dst:
    for seq_name, table_name in sequences:
        try:
            dst.execute(text(
                f"SELECT setval('{seq_name}', "
                f"COALESCE((SELECT MAX(id) FROM {table_name}), 1), "
                f"COALESCE((SELECT MAX(id) FROM {table_name}) IS NOT NULL, false))"
            ))
            print(f"      OK: {seq_name}")
        except Exception as e:
            print(f"      WARN ({seq_name}): {e}")
    dst.commit()

print()
print("=" * 60)
print("Migracion completa")
print("=" * 60)
print()
print("Proximos pasos:")
print("  1. Verifica los datos en Supabase Studio:")
print("     https://supabase.com/dashboard -> tu proyecto -> Table editor")
print("  2. Si todo se ve bien, abri el dashboard local:")
print("     streamlit run lima_importadores/dashboard/app.py")
print(f"  3. Cuando confirmes que el dashboard lee desde Postgres, podes")
print(f"     borrar el SQLite local (opcional): {SQLITE_PATH}")
print()
