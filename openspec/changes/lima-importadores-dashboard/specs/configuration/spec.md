# Spec — Configuration

**Domain**: configuration
**Change**: lima-importadores-dashboard
**Date**: 2026-05-06

---

## Config File

The application MUST load configuration from a `config.yaml` file at the project root. The config MUST be validated with a Pydantic model at startup. If required fields are missing or invalid, the application MUST exit with a descriptive error message.

---

## Config Format

```yaml
# config.yaml

database:
  path: "data/lima_importadores.db"   # Path to SQLite file

scraper:
  keywords:
    - "importadora"
    - "importaciones"
    - "import"
  districts:
    - "Miraflores"
    - "San Isidro"
    - "La Victoria"
    - "Breña"
    - "Lince"
    - "Jesús María"
    - "San Borja"
    - "Surco"
    - "Ate"
    - "Santa Anita"
    - "El Agustino"
    - "San Luis"
    - "Cercado de Lima"
    - "Rímac"
    - "San Martín de Porres"
    - "Los Olivos"
    - "Independencia"
    - "Comas"
    - "Carabayllo"
    - "Puente Piedra"
    - "Callao"
    # ... (all 43 Lima districts + Callao included by default)
  rate_limiting:
    scroll_delay_min: 2       # seconds
    scroll_delay_max: 5
    listing_delay_min: 1
    listing_delay_max: 3
    district_delay_min: 30
    district_delay_max: 60
    retry_backoff_start: 5    # seconds
    retry_backoff_max: 60
  max_listings_per_query: 120
  max_retries: 2

enrichment:
  request_timeout: 10         # seconds
  max_redirects: 3
  wayback_timeout: 15         # seconds
  outdated_threshold_years: 5 # copyright year older than this = outdated

qualifier:
  min_rating: 3.5
  max_review_count: 49        # inclusive upper bound (< 50)
  antigüedad_years: 5         # oldest review must be at least this many years ago

logging:
  level: "INFO"               # DEBUG | INFO | WARNING | ERROR
  file: "logs/scraper.log"
```

---

## Pydantic Model (required fields and types)

| Field | Type | Default | Required |
|-------|------|---------|----------|
| `database.path` | str | `"data/lima_importadores.db"` | No |
| `scraper.keywords` | list[str] | See above | No |
| `scraper.districts` | list[str] | Full Lima list | No |
| `scraper.rate_limiting.*` | int | See above | No |
| `scraper.max_listings_per_query` | int | 120 | No |
| `scraper.max_retries` | int | 2 | No |
| `enrichment.request_timeout` | int | 10 | No |
| `enrichment.max_redirects` | int | 3 | No |
| `enrichment.wayback_timeout` | int | 15 | No |
| `enrichment.outdated_threshold_years` | int | 5 | No |
| `qualifier.min_rating` | float | 3.5 | No |
| `qualifier.max_review_count` | int | 49 | No |
| `qualifier.antigüedad_years` | int | 5 | No |
| `logging.level` | str | `"INFO"` | No |
| `logging.file` | str | `"logs/scraper.log"` | No |

All fields have defaults — the application MUST run with an empty or absent `config.yaml` using the defaults above.

---

## Environment Variables

The `database.path` MUST also be overridable via the `LIMA_DB_PATH` environment variable. Environment variable takes precedence over config file.

---

## Scenarios

**Given** no `config.yaml` exists,
**When** the application starts,
**Then** it MUST load all defaults without error.

**Given** `config.yaml` sets `enrichment.outdated_threshold_years: 3`,
**When** the enrichment step runs,
**Then** websites with copyright year < current_year - 3 MUST be flagged as outdated.

**Given** `LIMA_DB_PATH=/tmp/test.db` is set as an environment variable,
**When** the application starts,
**Then** it MUST use `/tmp/test.db` as the database path, ignoring `config.yaml`'s `database.path`.

**Given** `config.yaml` contains `scraper.keywords: ["importacion"]` (only one keyword),
**When** the scraper runs,
**Then** only searches using "importacion" SHALL be executed.
