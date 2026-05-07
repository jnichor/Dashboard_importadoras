import asyncio
import logging
import sys
import time
from datetime import datetime

from lima_importadores.config import CONFIG
from lima_importadores.storage import init_db, get_session
from lima_importadores.storage.repository import create_scrape_run, complete_scrape_run


def _setup_logging():
    import os
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    os.makedirs("logs", exist_ok=True)
    level = getattr(logging, CONFIG.logging.level.upper(), logging.INFO)
    fmt = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
    handlers = [
        logging.StreamHandler(sys.stderr),
        logging.FileHandler(CONFIG.logging.file, encoding="utf-8"),
    ]
    logging.basicConfig(level=level, format=fmt, handlers=handlers)


def cmd_scrape():
    from lima_importadores.scraper import create_browser_context, run_smoke_test, scrape_query
    from lima_importadores.storage.repository import upsert_business

    async def _run():
        init_db()
        session = get_session()
        run = create_scrape_run(session, CONFIG.scraper.districts, CONFIG.scraper.keywords)
        session.commit()

        total = 0
        errors = 0
        start = time.time()

        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            context = await create_browser_context(pw)

            ok = await run_smoke_test(context)
            if not ok:
                logging.warning("Smoke test failed — continuing anyway (selectors may be stale)")

            import asyncio as _asyncio
            rl = CONFIG.scraper.rate_limiting

            import random
            for idx, district in enumerate(CONFIG.scraper.districts, start=1):
                for keyword in CONFIG.scraper.keywords:
                    try:
                        results = await scrape_query(context, district, keyword, CONFIG.scraper)
                        for data in results:
                            upsert_business(session, data)
                            total += 1
                        session.commit()
                    except RuntimeError as exc:
                        if "CAPTCHA_BLOCKED" in str(exc):
                            logging.error("Run stopped — CAPTCHA block")
                            complete_scrape_run(session, run, total, errors)
                            session.commit()
                            sys.exit(1)
                        errors += 1

                # Long break every N districts to mimic human behavior
                if idx % rl.long_break_every_n_districts == 0 and idx < len(CONFIG.scraper.districts):
                    long_delay = random.uniform(rl.long_break_min, rl.long_break_max)
                    logging.info("Long break after %d districts — pausing %.0fs (%.1fmin)", idx, long_delay, long_delay / 60)
                    await _asyncio.sleep(long_delay)
                else:
                    delay = random.uniform(rl.district_delay_min, rl.district_delay_max)
                    logging.info("District %d/%d done — waiting %.0fs before next", idx, len(CONFIG.scraper.districts), delay)
                    await _asyncio.sleep(delay)

            await context.browser.close()

        complete_scrape_run(session, run, total, errors)
        session.commit()
        elapsed = time.time() - start
        print(f"\n✅ Scraping completo — {total} negocios, {errors} errores, {elapsed:.0f}s")

    asyncio.run(_run())


def cmd_enrich():
    from lima_importadores.enrichment import run_enrichment
    init_db()
    session = get_session()
    start = time.time()
    count = run_enrichment(session, CONFIG.enrichment)
    elapsed = time.time() - start
    print(f"\n✅ Enriquecimiento completo — {count} negocios procesados, {elapsed:.0f}s")


def cmd_qualify():
    from lima_importadores.qualifier import apply_qualifier_to_all
    init_db()
    session = get_session()
    start = time.time()
    qualified = apply_qualifier_to_all(
        session, CONFIG.qualifier, CONFIG.scraper.districts, CONFIG.scraper.keywords
    )
    elapsed = time.time() - start
    print(f"\n✅ Calificación completa — {qualified} prospectos calificados, {elapsed:.0f}s")


def cmd_run():
    print("🔍 Paso 1/3 — Scraping...")
    cmd_scrape()
    print("\n🌐 Paso 2/3 — Enriquecimiento de sitios web...")
    cmd_enrich()
    print("\n🎯 Paso 3/3 — Calificación de prospectos...")
    cmd_qualify()
    print("\n🚀 Pipeline completo. Lanza el dashboard con: python -m lima_importadores dashboard")


def cmd_dashboard():
    import subprocess
    dashboard_path = "lima_importadores/dashboard/app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", dashboard_path], check=True)


COMMANDS = {
    "scrape": cmd_scrape,
    "enrich": cmd_enrich,
    "qualify": cmd_qualify,
    "run": cmd_run,
    "dashboard": cmd_dashboard,
}

USAGE = """
Uso: python -m lima_importadores <comando>

Comandos:
  run        Ejecuta el pipeline completo (scrape → enrich → qualify)
  scrape     Solo scraping de Google Maps
  enrich     Solo enriquecimiento de sitios web
  qualify    Solo calificación de prospectos
  dashboard  Lanza el dashboard Streamlit
"""

if __name__ == "__main__":
    _setup_logging()

    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(USAGE)
        sys.exit(1)

    COMMANDS[sys.argv[1]]()
