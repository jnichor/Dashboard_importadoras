import os
from pathlib import Path
from pydantic import BaseModel, Field
import yaml
from dotenv import load_dotenv

# Cargar variables del archivo .env (en la raiz del proyecto) si existe.
# Esto debe correr ANTES de leer os.environ.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=_PROJECT_ROOT / ".env")


class RateLimitingConfig(BaseModel):
    scroll_delay_min: int = 2
    scroll_delay_max: int = 5
    listing_delay_min: int = 1
    listing_delay_max: int = 3
    district_delay_min: int = 30
    district_delay_max: int = 60
    retry_backoff_start: int = 5
    retry_backoff_max: int = 60
    long_break_every_n_districts: int = 5
    long_break_min: int = 600
    long_break_max: int = 900


LIMA_DISTRICTS = [
    "Ancón", "Ate", "Barranco", "Breña", "Carabayllo", "Cercado de Lima",
    "Chaclacayo", "Chorrillos", "Cieneguilla", "Comas", "El Agustino",
    "Independencia", "Jesús María", "La Molina", "La Victoria", "Lince",
    "Los Olivos", "Lurigancho", "Lurín", "Magdalena del Mar", "Miraflores",
    "Pachacámac", "Pucusana", "Pueblo Libre", "Puente Piedra", "Punta Hermosa",
    "Punta Negra", "Rímac", "San Bartolo", "San Borja", "San Isidro",
    "San Juan de Lurigancho", "San Juan de Miraflores", "San Luis",
    "San Martín de Porres", "San Miguel", "Santa Anita", "Santa María del Mar",
    "Santa Rosa", "Santiago de Surco", "Surquillo", "Villa El Salvador",
    "Villa María del Triunfo", "Callao",
]


class ScraperConfig(BaseModel):
    keywords: list[str] = ["importadora", "importaciones", "import"]
    districts: list[str] = Field(default_factory=lambda: LIMA_DISTRICTS)
    rate_limiting: RateLimitingConfig = Field(default_factory=RateLimitingConfig)
    max_listings_per_query: int = 120
    max_retries: int = 2
    smoke_test_place_id: str = "ChIJN1t_tDeuEmsRUsoyG83frY4"  # Google Sydney (stable)


class EnrichmentConfig(BaseModel):
    request_timeout: int = 10
    max_redirects: int = 3
    wayback_timeout: int = 15
    outdated_threshold_years: int = 5


class QualifierConfig(BaseModel):
    min_rating: float = 3.5
    max_review_count: int = 49
    antigüedad_years: int = 5


class DatabaseConfig(BaseModel):
    path: str = "data/lima_importadores.db"
    url: str | None = None  # Si esta presente, sobrescribe `path` y usa Postgres.


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "logs/scraper.log"


class Config(BaseModel):
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    scraper: ScraperConfig = Field(default_factory=ScraperConfig)
    enrichment: EnrichmentConfig = Field(default_factory=EnrichmentConfig)
    qualifier: QualifierConfig = Field(default_factory=QualifierConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_config(path: str = "config.yaml") -> Config:
    data = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    config = Config(**data)
    env_db = os.environ.get("LIMA_DB_PATH")
    if env_db:
        config.database.path = env_db
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        config.database.url = env_url
    return config


CONFIG = load_config()
