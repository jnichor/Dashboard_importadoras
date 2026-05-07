# Tasks — Lima Importadores Dashboard

**Change**: lima-importadores-dashboard
**Date**: 2026-05-06
**Delivery strategy**: ask-on-risk

---

## Review Workload Forecast

- Estimated changed lines: ~800-1200 (new greenfield project)
- Chained PRs recommended: Yes (split by phase)
- Suggested slices: Setup+Storage → Scraper → Enrichment+Qualifier → Dashboard

---

## Phase 1 — Project Setup

- [x] 1.1 Crear estructura de directorios del proyecto (`lima_importadores/scraper/`, `storage/`, `enrichment/`, `qualifier/`, `dashboard/`, `data/`, `logs/`)
- [x] 1.2 Crear `requirements.txt` con dependencias: `playwright`, `playwright-stealth`, `sqlalchemy`, `streamlit`, `requests`, `beautifulsoup4`, `pydantic`, `pyyaml`, `pandas`, `openpyxl`
- [x] 1.3 Crear `config.yaml` con todos los valores default (ver spec de configuración)
- [x] 1.4 Crear todos los `__init__.py` vacíos en cada subpaquete
- [x] 1.5 Crear `data/.gitkeep` y `logs/.gitkeep`

---

## Phase 2 — Configuration (`config.py`)

- [x] 2.1 Definir modelos Pydantic: `DatabaseConfig`, `ScraperConfig`, `RateLimitingConfig`, `EnrichmentConfig`, `QualifierConfig`, `LoggingConfig`, `Config`
- [x] 2.2 Implementar `load_config(path: str = "config.yaml") -> Config` con fallback a defaults si el archivo no existe
- [x] 2.3 Implementar override de `database.path` via variable de entorno `LIMA_DB_PATH`
- [x] 2.4 Exportar `CONFIG = load_config()` como singleton del módulo

---

## Phase 3 — Storage (`storage/`)

- [x] 3.1 Definir modelos SQLAlchemy en `storage/models.py`: tablas `businesses`, `website_checks`, `scrape_runs` con todas las columnas, tipos y constraints según spec
- [x] 3.2 Implementar `create_engine` con WAL mode activado en `storage/__init__.py`
- [x] 3.3 Implementar `init_db()` que crea las tablas e índices si no existen
- [x] 3.4 Implementar `repository.upsert_business(session, data: dict) -> Business` — upsert por `place_id`
- [x] 3.5 Implementar `repository.upsert_website_check(session, data: dict) -> WebsiteCheck`
- [x] 3.6 Implementar `repository.create_scrape_run(session, ...) -> ScrapeRun` y `repository.complete_scrape_run(session, run_id, ...)`
- [x] 3.7 Implementar `repository.get_unenriched_businesses(session) -> list[Business]` — businesses con `has_website=1` sin `website_checks` row

---

## Phase 4 — Scraper (`scraper/`)

- [x] 4.1 Definir todos los selectores en `scraper/selectors.py` (ver diseño §3): results panel, listing items, detail panel fields, review timestamps
- [x] 4.2 Implementar `scraper/browser.py`: función `create_browser_context(playwright)` que lanza Chromium headless, aplica playwright-stealth, setea User-Agent realista
- [x] 4.3 Implementar smoke test en `browser.py`: verificar selectores contra un Place ID hardcodeado conocido; loguear `SELECTOR_STALE` y salir si falla
- [x] 4.4 Implementar `scraper/maps.py` — función `scrape_query(context, district, keyword, config) -> list[dict]`:
  - Navegar a URL de búsqueda de Maps con query encodeado
  - Esperar panel de resultados
  - Loop de scroll con delays aleatorios (2-5s) hasta sin nuevos resultados o límite 120
  - Recolectar elementos de listings
- [x] 4.5 Implementar extracción por listing en `maps.py` — función `extract_listing(page, element) -> dict`:
  - Click en listing para abrir panel de detalle
  - Extraer todos los campos: name, address, phone, website_url, rating, review_count, category, opening_hours, latitude, longitude, place_id
  - Delay aleatorio (1-3s) antes del siguiente listing
- [x] 4.6 Implementar extracción de `oldest_review_date` en `maps.py`:
  - Leer timestamps del primer batch de reseñas visible (sin scroll)
  - Parsear relativos ("hace 7 años") y absolutos ("mayo de 2018") a fecha ISO
  - Guardar la más antigua; null si no hay reseñas o no parseable
- [x] 4.7 Implementar parsing de distrito desde `address` usando lista de distritos de config; fallback al district seed del query
- [x] 4.8 Implementar manejo de errores en `maps.py`:
  - Retry con backoff exponencial (start 5s, max 60s) en errores de red
  - Detección de CAPTCHA (selectores conocidos): esperar 120s, reintentar una vez, parar si persiste
  - Skip de listing tras 2 retries fallidos; loguear y continuar

---

## Phase 5 — Enrichment (`enrichment/`)

- [x] 5.1 Implementar `enrichment/fetcher.py` — función `fetch_url(url: str, config) -> tuple[int | None, str | None]`: HTTP GET con timeout 10s, max 3 redirects, User-Agent realista; retornar (status_code, html) o (None, None) en error
- [x] 5.2 Implementar `enrichment/parser.py` — función `extract_copyright_year(html: str) -> int | None`:
  - Parsear con BeautifulSoup
  - Buscar en footer → elementos con clase "footer/copyright/copy" → body
  - Aplicar 4 patrones regex en orden (ver spec)
  - Retornar el año más reciente encontrado, o None
- [x] 5.3 Implementar `enrichment/wayback.py` — función `get_last_capture(url: str, config) -> date | None`:
  - Llamar CDX API con parámetros de spec
  - Timeout 15s; retornar None en cualquier error
  - Parsear timestamp `YYYYMMDDHHmmss` → date
- [x] 5.4 Implementar `enrichment/__init__.py` — función `enrich_business(business: Business, config) -> dict` que orquesta la máquina de estados de veredictos completa (ver spec enrichment §Verdict State Machine)
- [x] 5.5 Implementar loop principal de enriquecimiento: iterar businesses no enriquecidos, llamar `enrich_business`, upsert `website_check`, loguear progreso

---

## Phase 6 — Qualifier (`qualifier/`)

- [x] 6.1 Implementar `qualifier/rules.py` — función `evaluate(business, website_check, config) -> QualifierResult` con las 6 reglas exactas de la spec (sector, location, antigüedad, review count, rating, web presence)
- [x] 6.2 Definir dataclass `QualifierResult` con campos: `qualifies: bool | None`, `antigüedad_flag: str`, `disqualify_reasons: list[str]`
- [x] 6.3 Implementar función `apply_qualifier_to_all(session, config)` que itera todos los businesses, llama `evaluate`, y actualiza `prospect_qualifies`, `antigüedad_flag`, `disqualify_reason` en la DB

---

## Phase 7 — Dashboard (`dashboard/app.py`)

- [x] 7.1 Implementar `load_data(db_path: str) -> pd.DataFrame` con `@st.cache_data(ttl=300)` — JOIN businesses + website_checks, aplicar lógica de qualifier en pandas
- [x] 7.2 Implementar sidebar: district multiselect, qualification radio, max reviews slider, web presence multiselect, name search text input — todos con `st.session_state`
- [x] 7.3 Implementar función `apply_filters(df, filters) -> pd.DataFrame` que aplica todos los filtros activos
- [x] 7.4 Implementar tabla principal con `st.dataframe`: columnas según spec (nombre, distrito, categoría, reseñas, calificación, teléfono, sitio web, estado web con badges emoji, antigüedad con badges)
- [x] 7.5 Implementar export CSV: `st.download_button` con `df.to_csv(encoding='utf-8-sig')`, filename `prospectos_{fecha}.csv`
- [x] 7.6 Implementar export Excel: función `build_excel(df, districts) -> bytes` con `pd.ExcelWriter` + openpyxl, una hoja por distrito seleccionado; `st.download_button` con el resultado
- [x] 7.7 Manejar estado vacío: mostrar mensaje "No hay datos. Ejecuta el scraper primero." si el DB no existe o está vacío

---

## Phase 8 — CLI Entrypoint (`__main__.py`)

- [x] 8.1 Implementar `__main__.py` con subcomandos:
  - `python -m lima_importadores scrape` — ejecuta solo el scraper
  - `python -m lima_importadores enrich` — ejecuta solo el enriquecimiento
  - `python -m lima_importadores qualify` — ejecuta solo el qualifier
  - `python -m lima_importadores run` — ejecuta scrape → enrich → qualify en secuencia
  - `python -m lima_importadores dashboard` — lanza `streamlit run dashboard/app.py`
- [x] 8.2 Configurar logging al inicio: nivel y archivo desde config, formato estructurado con timestamp
- [x] 8.3 Llamar `init_db()` al inicio de cualquier subcomando que acceda a la DB
- [x] 8.4 Imprimir resumen al final de cada run: businesses encontrados, errores, tiempo total

---

## Review Workload — Slices sugeridos

| PR | Contenido | Líneas estimadas |
|----|-----------|-----------------|
| PR #1 | Setup + Config + Storage (phases 1-3) | ~200 |
| PR #2 | Scraper completo (phase 4) | ~300 |
| PR #3 | Enrichment + Qualifier (phases 5-6) | ~200 |
| PR #4 | Dashboard + CLI (phases 7-8) | ~250 |
