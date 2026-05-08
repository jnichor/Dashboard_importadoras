import io
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

# Ensure the project root is on sys.path so `lima_importadores` is importable
# whether we run via `python -m lima_importadores dashboard` or via Streamlit
# Cloud's `streamlit run lima_importadores/dashboard/app.py`.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Page config + styling
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Lima Importadores — Inteligencia Comercial",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    html, body, [class*="css"], .stApp, .stMarkdown, p, span, div, h1, h2, h3, h4, h5, h6, button, input, select, textarea, label {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* ── ANIMATED BACKGROUND ────────────────────────────────────── */
    .stApp {
        background:
            radial-gradient(circle at 15% 20%, rgba(30, 64, 175, 0.22) 0%, transparent 45%),
            radial-gradient(circle at 85% 60%, rgba(8, 145, 178, 0.20) 0%, transparent 50%),
            radial-gradient(circle at 50% 90%, rgba(15, 23, 42, 0.16) 0%, transparent 55%),
            radial-gradient(circle at 30% 70%, rgba(180, 83, 9, 0.10) 0%, transparent 45%),
            linear-gradient(180deg, #f1f5f9 0%, #e0f2fe 50%, #f1f5f9 100%);
        background-attachment: fixed;
    }
    .stApp::before {
        content: "";
        position: fixed;
        top: -200px; left: -200px;
        width: 700px; height: 700px;
        background: radial-gradient(circle, rgba(30, 64, 175, 0.32), transparent 70%);
        border-radius: 50%;
        filter: blur(80px);
        animation: float1 22s ease-in-out infinite;
        pointer-events: none;
        z-index: 0;
    }
    .stApp::after {
        content: "";
        position: fixed;
        bottom: -250px; right: -200px;
        width: 800px; height: 800px;
        background: radial-gradient(circle, rgba(8, 145, 178, 0.26), transparent 70%);
        border-radius: 50%;
        filter: blur(90px);
        animation: float2 28s ease-in-out infinite;
        pointer-events: none;
        z-index: 0;
    }
    @keyframes float1 {
        0%, 100% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(120px, 100px) scale(1.15); }
    }
    @keyframes float2 {
        0%, 100% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(-100px, -120px) scale(1.1); }
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 1380px;
        position: relative;
        z-index: 1;
    }
    #MainMenu, footer, header { visibility: hidden; }

    /* ── ENTRY ANIMATIONS ───────────────────────────────────────── */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.08); }
    }
    @keyframes shimmer {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* ── HERO ───────────────────────────────────────────────────── */
    .hero {
        position: relative;
        margin-bottom: 2.5rem;
        padding: 2.25rem 2.5rem;
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 30%, #1e40af 55%, #0e7490 80%, #0f172a 100%);
        background-size: 300% 300%;
        animation: shimmer 22s ease infinite, fadeInUp 0.7s ease-out;
        border-radius: 24px;
        overflow: hidden;
        color: white;
        box-shadow: 0 20px 60px -20px rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .hero::before {
        content: "";
        position: absolute;
        top: -60px; right: -60px;
        width: 280px; height: 280px;
        background: radial-gradient(circle, rgba(56, 189, 248, 0.35), transparent 70%);
        border-radius: 50%;
        filter: blur(20px);
    }
    .hero::after {
        content: "";
        position: absolute;
        bottom: -80px; left: 30%;
        width: 220px; height: 220px;
        background: radial-gradient(circle, rgba(180, 83, 9, 0.30), transparent 70%);
        border-radius: 50%;
        filter: blur(30px);
    }
    .hero-content { position: relative; z-index: 2; }
    .hero-badge {
        display: inline-block;
        background: rgba(255,255,255,0.18);
        backdrop-filter: blur(8px);
        color: white;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        padding: 0.4rem 0.85rem;
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.25);
        margin-bottom: 1rem;
    }
    .hero-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: white;
        letter-spacing: -0.03em;
        line-height: 1.05;
        margin: 0;
    }
    .hero-subtitle {
        color: rgba(255,255,255,0.88);
        font-size: 1.05rem;
        margin: 0.75rem 0 0 0;
        font-weight: 400;
        max-width: 680px;
        line-height: 1.55;
    }

    /* ── KPI CARDS — Custom HTML ─────────────────────────────────── */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .kpi-card {
        position: relative;
        background: white;
        padding: 1.5rem 1.4rem;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        overflow: hidden;
        opacity: 0;
        animation: fadeInUp 0.6s ease-out forwards;
    }
    .kpi-card:nth-child(1) { animation-delay: 0.05s; }
    .kpi-card:nth-child(2) { animation-delay: 0.15s; }
    .kpi-card:nth-child(3) { animation-delay: 0.25s; }
    .kpi-card:nth-child(4) { animation-delay: 0.35s; }
    .kpi-card:nth-child(5) { animation-delay: 0.45s; }
    .kpi-card::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 4px;
        background: var(--accent);
        transition: height 0.25s ease;
    }
    .kpi-card::after {
        content: "";
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at 50% 0%, var(--accent-bg), transparent 60%);
        opacity: 0;
        transition: opacity 0.3s ease;
        pointer-events: none;
    }
    .kpi-card:hover {
        transform: translateY(-6px) scale(1.02);
        box-shadow: 0 20px 40px -12px rgba(15, 23, 42, 0.18);
        border-color: transparent;
    }
    .kpi-card:hover::before { height: 6px; }
    .kpi-card:hover::after { opacity: 0.4; }
    .kpi-card:hover .kpi-icon { animation: pulse 1.2s ease-in-out infinite; }
    .kpi-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 42px; height: 42px;
        background: var(--accent-bg);
        border-radius: 12px;
        font-size: 1.25rem;
        margin-bottom: 0.85rem;
        box-shadow: 0 4px 12px -2px var(--accent-bg);
        transition: transform 0.25s ease;
    }
    .kpi-label {
        font-size: 0.72rem;
        font-weight: 600;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 0;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.035em;
        line-height: 1.1;
        margin: 0.4rem 0 0 0;
    }
    .kpi-delta {
        font-size: 0.8rem;
        font-weight: 600;
        margin-top: 0.4rem;
        color: var(--accent);
    }

    /* ── SIDEBAR — Dark premium ─────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background:
            radial-gradient(circle at 20% 10%, rgba(30, 64, 175, 0.4) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(8, 145, 178, 0.25) 0%, transparent 50%),
            linear-gradient(180deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 4px 0 24px rgba(15, 23, 42, 0.25);
    }
    section[data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem; }
    section[data-testid="stSidebar"] h3 {
        font-size: 0.72rem;
        font-weight: 700;
        color: #93c5fd;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 1.5rem;
    }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] label {
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        text-transform: none !important;
    }
    /* Sidebar inputs — glassmorphism */
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] [data-baseweb="select"] > div,
    section[data-testid="stSidebar"] [data-baseweb="input"] {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        color: white !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] input::placeholder { color: rgba(255,255,255,0.4) !important; }
    /* Sidebar multiselect tags */
    section[data-testid="stSidebar"] [data-baseweb="tag"] {
        background: rgba(37, 99, 235, 0.4) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    /* Sidebar slider */
    section[data-testid="stSidebar"] [data-baseweb="slider"] [role="slider"] {
        background: #2563eb !important;
    }
    /* Sidebar caption */
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: rgba(226, 232, 240, 0.6) !important;
    }
    /* Sidebar "Mostrar todo" button */
    section[data-testid="stSidebar"] .stButton button {
        background: linear-gradient(135deg, #1e40af 0%, #0e7490 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(30, 64, 175, 0.4) !important;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(30, 64, 175, 0.5) !important;
    }
    /* Sidebar separator */
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.1) !important;
    }

    /* ── TABS ───────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 1px solid #e5e7eb;
        padding: 0;
        margin-bottom: 1.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        font-size: 0.95rem;
        padding: 0.85rem 1.4rem;
        color: #64748b;
        background: transparent;
        border-radius: 0;
        margin-right: 0.5rem;
    }
    .stTabs [aria-selected="true"] {
        color: #0f172a !important;
        background: transparent !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background: #1e40af !important;
        height: 2px !important;
    }

    /* ── DATAFRAME ──────────────────────────────────────────────── */
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
    }

    /* ── BUTTONS ────────────────────────────────────────────────── */
    .stDownloadButton button, .stButton button {
        background: #0f172a;
        color: white;
        border: none;
        font-weight: 600;
        font-size: 0.9rem;
        padding: 0.7rem 1.5rem;
        border-radius: 10px;
        transition: all 0.15s ease;
        letter-spacing: -0.005em;
    }
    .stDownloadButton button:hover, .stButton button:hover {
        background: #1e293b;
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.18);
    }

    /* ── SECTION HEADERS ────────────────────────────────────────── */
    .section-label {
        font-size: 0.72rem;
        font-weight: 700;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 2.5rem 0 1.25rem 0;
    }
    .section-divider {
        border: none;
        border-top: 1px solid #e5e7eb;
        margin: 2rem 0 1.5rem 0;
    }

    /* ── FOOTER ─────────────────────────────────────────────────── */
    .footer-note {
        color: #94a3b8;
        font-size: 0.82rem;
        text-align: center;
        padding: 2rem 0 0 0;
        border-top: 1px solid #f1f5f9;
        margin-top: 3.5rem;
        font-weight: 400;
    }

    /* ── CHART CONTAINERS ───────────────────────────────────────── */
    div[data-testid="stArrowVegaLiteChart"], div[data-testid="stVegaLiteChart"] {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
    }
    .chart-title {
        font-size: 0.92rem;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 0.75rem;
        letter-spacing: -0.01em;
    }

    /* ── CAPTIONS ───────────────────────────────────────────────── */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #64748b !important;
        font-size: 0.85rem !important;
    }

    /* ── ALERTS ─────────────────────────────────────────────────── */
    div[data-testid="stAlert"] {
        border-radius: 10px;
        border: 1px solid #e5e7eb;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    """Carga los negocios desde la DB (Postgres si DATABASE_URL esta seteada,
    SQLite local en caso contrario). Usa el engine centralizado del paquete.
    Incluye el outcome de la ultima llamada via LEFT JOIN a call_outcomes."""
    from sqlalchemy import text
    from lima_importadores.storage import engine

    query = text("""
        SELECT
            b.place_id,
            b.name                  AS "Nombre",
            b.district              AS "Distrito",
            b.category              AS "Categoría",
            b.review_count          AS "Reseñas",
            b.rating                AS "Calificación",
            b.phone                 AS "Teléfono",
            b.website_url           AS "Sitio web",
            b.has_website,
            b.antiguedad_flag,
            b.prospect_qualifies,
            b.disqualify_reason,
            b.address               AS "Dirección",
            b.latitude,
            b.longitude,
            b.oldest_review_date,
            COALESCE(
                w.verdict,
                CASE WHEN b.has_website = FALSE THEN 'no_site' ELSE 'unknown' END
            ) AS verdict,
            co.contacted            AS contacted_db,
            co.response             AS response_db
        FROM businesses b
        LEFT JOIN website_checks w ON b.place_id = w.place_id
        LEFT JOIN call_outcomes  co ON b.place_id = co.place_id
    """)
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Error al cargar datos de la base: {e}")
        return pd.DataFrame()


def _verdict_badge(verdict: str) -> str:
    return {
        "outdated": "🔴 Desactualizado",
        "no_site":  "⚫ Sin sitio",
        "current":  "🟢 Actual",
        "unknown":  "⚪ Desconocido",
    }.get(verdict, "⚪ Desconocido")


def _antiguedad_badge(flag: str) -> str:
    return {
        "califica":       "✅ Califica",
        "no_determinada": "⚠️ No determinada",
        "no_califica":    "❌ No califica",
    }.get(flag, flag)


# ---------------------------------------------------------------------------
# Mapeos de outcomes de llamada (DB <-> UI)
# ---------------------------------------------------------------------------

CONTACTO_DB_TO_DISPLAY = {
    "no_llamado":    "⚪ No llamado",
    "contesto":      "✅ Contestó",
    "no_contesto":   "❌ No contestó",
}
CONTACTO_DISPLAY_TO_DB = {v: k for k, v in CONTACTO_DB_TO_DISPLAY.items()}
CONTACTO_OPTIONS = list(CONTACTO_DB_TO_DISPLAY.values())

RESULTADO_NONE_DISPLAY = "—"
RESULTADO_DB_TO_DISPLAY = {
    "acepto":    "🎉 Aceptó",
    "rechazo":   "🚫 Rechazó",
    "pendiente": "⏳ Pendiente",
}
RESULTADO_DISPLAY_TO_DB = {v: k for k, v in RESULTADO_DB_TO_DISPLAY.items()}
RESULTADO_DISPLAY_TO_DB[RESULTADO_NONE_DISPLAY] = None
RESULTADO_OPTIONS = [RESULTADO_NONE_DISPLAY] + list(RESULTADO_DB_TO_DISPLAY.values())


# ---------------------------------------------------------------------------
# WhatsApp helpers
# ---------------------------------------------------------------------------

def _format_phone_for_whatsapp(phone) -> str | None:
    """Convert a Peruvian phone number to wa.me-compatible format (no + sign)."""
    if not phone or pd.isna(phone):
        return None
    digits = "".join(c for c in str(phone) if c.isdigit())
    if not digits:
        return None
    # Already international (starts with 51 and at least 11 digits)
    if digits.startswith("51") and len(digits) >= 11:
        return digits
    # Strip leading 0 (national prefix in Peru)
    if digits.startswith("0"):
        digits = digits[1:]
    # Prepend Peru country code
    return "51" + digits


def _saludo_lima() -> str:
    """Devuelve un saludo apropiado segun la hora local de Lima."""
    hora = datetime.now(ZoneInfo("America/Lima")).hour
    if 5 <= hora < 12:
        return "Buenos días"
    if 12 <= hora < 19:
        return "Buenas tardes"
    return "Buenas noches"


def _whatsapp_url(phone, name, district) -> str | None:
    """Genera una URL wa.me con un mensaje de outreach pre-cargado.
    El saludo se adapta a la hora local de Lima (Peru)."""
    digits = _format_phone_for_whatsapp(phone)
    if not digits:
        return None
    name_part = str(name).strip() if name and not pd.isna(name) else "equipo"
    district_part = str(district).strip() if district and not pd.isna(district) else "Lima"

    msg = (
        f"{_saludo_lima()} 😊\n"
        f"Somos *Causal AI Digital*, empresa de inteligencia artificial y "
        f"soluciones digitales.\n\n"
        f"Vimos su negocio *{name_part}* en Google Maps ({district_part}) y "
        f"creemos que podrían beneficiarse de una página web profesional "
        f"para mostrar sus productos, captar clientes y organizar mejor sus "
        f"consultas.\n\n"
        f"¿Tendría unos minutos para conversar?"
    )
    return f"https://wa.me/{digits}?text={quote(msg)}"


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    result = df.copy()

    mode = filters["qualification"]
    if mode == "solo_calificados":
        result = result[result["prospect_qualifies"] == 1]
    elif mode == "incluir_no_determinada":
        result = result[
            (result["prospect_qualifies"] == 1) |
            (result["antiguedad_flag"] == "no_determinada")
        ]

    if filters["districts"]:
        result = result[result["Distrito"].isin(filters["districts"])]

    result = result[result["Reseñas"] <= filters["max_reviews"]]

    if filters["web_presence"]:
        result = result[result["verdict"].isin(filters["web_presence"])]

    if filters["name_search"]:
        mask = result["Nombre"].str.contains(filters["name_search"], case=False, na=False)
        result = result[mask]

    return result


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

EXPORT_COLS = [
    "Nombre", "Distrito", "Dirección", "Categoría", "Reseñas", "Calificación",
    "Teléfono", "Sitio web", "Estado web", "Antigüedad",
]


def _prepare_export_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Estado web"] = out["verdict"].apply(_verdict_badge)
    out["Antigüedad"] = out["antiguedad_flag"].apply(_antiguedad_badge)
    cols = [c for c in EXPORT_COLS if c in out.columns]
    return out[cols]


def build_csv(df: pd.DataFrame) -> bytes:
    return _prepare_export_df(df).to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


def build_excel(df: pd.DataFrame, districts: list[str]) -> bytes:
    export_df = _prepare_export_df(df)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        sheets_written = 0
        for district in districts:
            sheet_df = export_df[export_df["Distrito"] == district]
            if not sheet_df.empty:
                sheet_df.to_excel(writer, sheet_name=district[:31], index=False)
                sheets_written += 1
        if sheets_written == 0:
            pd.DataFrame({"Info": ["Sin datos para los filtros seleccionados"]}).to_excel(
                writer, sheet_name="Sin datos", index=False
            )
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Visualizations
# ---------------------------------------------------------------------------

def render_kpis(filtered: pd.DataFrame, total: int) -> None:
    qualified = int((filtered["prospect_qualifies"] == 1).sum())
    no_site = int((filtered["verdict"] == "no_site").sum())
    districts_count = filtered["Distrito"].nunique()
    pct_view = f"{len(filtered)/total*100:.0f}% del total" if total else ""

    cards = [
        ("📊", "Negocios totales", f"{total:,}", "", "#1e40af", "#dbeafe"),
        ("🔍", "En vista actual", f"{len(filtered):,}", pct_view, "#0e7490", "#cffafe"),
        ("✅", "Calificados", f"{qualified:,}", "Listos para outreach", "#047857", "#d1fae5"),
        ("🌐", "Sin sitio web", f"{no_site:,}", "Oportunidad directa", "#b45309", "#fef3c7"),
        ("📍", "Distritos", f"{districts_count}", "Cobertura geográfica", "#334155", "#e2e8f0"),
    ]

    cards_html = '<div class="kpi-grid">'
    for icon, label, value, delta, accent, accent_bg in cards:
        cards_html += (
            f'<div class="kpi-card" style="--accent: {accent}; --accent-bg: {accent_bg};">'
            f'  <div class="kpi-icon">{icon}</div>'
            f'  <p class="kpi-label">{label}</p>'
            f'  <p class="kpi-value">{value}</p>'
            f'  <p class="kpi-delta">{delta}</p>'
            f'</div>'
        )
    cards_html += '</div>'

    st.markdown(cards_html, unsafe_allow_html=True)


def render_table(filtered: pd.DataFrame) -> None:
    display = filtered.copy()
    display["Estado web"] = display["verdict"].apply(_verdict_badge)
    display["Antigüedad"] = display["antiguedad_flag"].apply(_antiguedad_badge)
    display["WhatsApp"] = display.apply(
        lambda r: _whatsapp_url(
            r.get("Teléfono"),
            r.get("Nombre"),
            r.get("Distrito"),
        ),
        axis=1,
    )

    # Outcomes: convertir valores de DB a etiquetas legibles para los dropdowns.
    if "contacted_db" in display.columns:
        display["Contacto"] = (
            display["contacted_db"]
            .fillna("no_llamado")
            .map(lambda v: CONTACTO_DB_TO_DISPLAY.get(v, "⚪ No llamado"))
        )
    else:
        display["Contacto"] = "⚪ No llamado"

    if "response_db" in display.columns:
        display["Resultado"] = display["response_db"].map(
            lambda v: RESULTADO_DB_TO_DISPLAY.get(v, RESULTADO_NONE_DISPLAY)
            if pd.notna(v) else RESULTADO_NONE_DISPLAY
        )
    else:
        display["Resultado"] = RESULTADO_NONE_DISPLAY

    show_cols = [
        "Nombre", "Distrito", "Teléfono", "WhatsApp",
        "Contacto", "Resultado",
        "Sitio web", "Estado web", "Antigüedad",
        "Categoría", "Reseñas", "Calificación", "Dirección",
    ]
    show_cols = [c for c in show_cols if c in display.columns]

    editor_key = "prospects_editor"

    st.data_editor(
        display[show_cols],
        use_container_width=True,
        height=560,
        column_config={
            "Sitio web": st.column_config.LinkColumn("Sitio web", display_text="🔗 abrir"),
            "WhatsApp": st.column_config.LinkColumn("WhatsApp", display_text="💬 Enviar"),
            "Calificación": st.column_config.NumberColumn("⭐", format="%.1f"),
            "Reseñas": st.column_config.NumberColumn("Reseñas", format="%d"),
            "Contacto": st.column_config.SelectboxColumn(
                "📞 Contacto",
                help="Estado de la llamada al negocio",
                options=CONTACTO_OPTIONS,
                required=True,
                width="small",
            ),
            "Resultado": st.column_config.SelectboxColumn(
                "🎯 Resultado",
                help="Si contestó, ¿aceptó la propuesta?",
                options=RESULTADO_OPTIONS,
                width="small",
            ),
        },
        disabled=[c for c in show_cols if c not in ("Contacto", "Resultado")],
        key=editor_key,
        hide_index=True,
    )

    # Persistir cambios: cualquier edicion en Contacto/Resultado se guarda en
    # call_outcomes via UPSERT, se invalida la cache y se rerendera.
    edits = st.session_state.get(editor_key, {}).get("edited_rows", {})
    if edits:
        from lima_importadores.storage import get_session
        from lima_importadores.storage.repository import upsert_call_outcome

        try:
            with get_session() as session:
                for row_idx, changes in edits.items():
                    place_id = display.iloc[row_idx]["place_id"]
                    current_contacto = display.iloc[row_idx]["Contacto"]
                    current_resultado = display.iloc[row_idx]["Resultado"]

                    new_contacto_display = changes.get("Contacto", current_contacto)
                    new_resultado_display = changes.get("Resultado", current_resultado)

                    contacted_db = CONTACTO_DISPLAY_TO_DB.get(
                        new_contacto_display, "no_llamado"
                    )
                    response_db = RESULTADO_DISPLAY_TO_DB.get(
                        new_resultado_display, None
                    )

                    upsert_call_outcome(
                        session=session,
                        place_id=place_id,
                        contacted=contacted_db,
                        response=response_db,
                    )
                session.commit()

            # Resetear el estado del editor para que no reprocese los mismos edits
            # despues del rerun.
            if editor_key in st.session_state:
                del st.session_state[editor_key]
            load_data.clear()
            st.toast(f"✅ {len(edits)} cambio(s) guardado(s)", icon="💾")
            st.rerun()
        except Exception as e:
            st.error(f"Error al guardar cambios: {e}")


def render_map(filtered: pd.DataFrame) -> None:
    tooltip_cols = [
        "latitude", "longitude", "Nombre", "Distrito", "Dirección",
        "Teléfono", "Sitio web", "Categoría", "Reseñas", "Calificación",
    ]
    available_cols = [c for c in tooltip_cols if c in filtered.columns]
    map_df = filtered[available_cols].dropna(subset=["latitude", "longitude"]).copy()
    if map_df.empty:
        st.info("Sin datos de ubicación para los filtros actuales.")
        return

    map_df["Estado web"] = filtered.loc[map_df.index, "verdict"].apply(_verdict_badge)
    map_df = map_df.fillna("—")

    import pydeck as pdk
    center_lat = map_df["latitude"].mean()
    center_lon = map_df["longitude"].mean()

    hex_layer = pdk.Layer(
        "HexagonLayer",
        data=map_df,
        get_position=["longitude", "latitude"],
        radius=200,
        elevation_scale=15,
        elevation_range=[0, 1000],
        extruded=True,
        coverage=0.9,
        pickable=False,
    )
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position=["longitude", "latitude"],
        get_radius=40,
        get_fill_color=[37, 99, 235, 200],
        pickable=True,
        auto_highlight=True,
    )
    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=11,
        pitch=45,
    )
    tooltip_html = (
        "<div style='font-family: sans-serif; max-width: 260px;'>"
        "<b style='font-size: 13px; color: #60a5fa;'>{Nombre}</b><br/>"
        "<span style='color: #cbd5e1;'>{Distrito}</span><br/>"
        "<hr style='margin: 4px 0; border-color: #334155;' />"
        "📍 {Dirección}<br/>"
        "📞 {Teléfono}<br/>"
        "🏷️ {Categoría}<br/>"
        "⭐ {Calificación} · {Reseñas} reseñas<br/>"
        "🌐 {Estado web}"
        "</div>"
    )
    st.pydeck_chart(
        pdk.Deck(
            layers=[hex_layer, scatter_layer],
            initial_view_state=view_state,
            tooltip={
                "html": tooltip_html,
                "style": {"backgroundColor": "#1e293b", "color": "white", "fontSize": "12px",
                          "padding": "10px", "borderRadius": "8px"},
            },
        )
    )
    st.caption("🔵 Cada punto es un negocio · Las barras 3D muestran zonas de mayor concentración · Pasá el mouse sobre los puntos para ver detalles")


def render_analytics(filtered: pd.DataFrame) -> None:
    if filtered.empty:
        st.info("Sin datos para analizar.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="chart-title">Distribución por distrito</div>', unsafe_allow_html=True)
        dist_counts = filtered["Distrito"].value_counts().head(15)
        st.bar_chart(dist_counts, use_container_width=True, color="#1e40af", height=320)

    with col2:
        st.markdown('<div class="chart-title">Estado del sitio web</div>', unsafe_allow_html=True)
        verdict_labels = filtered["verdict"].apply(_verdict_badge).value_counts()
        st.bar_chart(verdict_labels, use_container_width=True, color="#0e7490", height=320)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown('<div class="chart-title">Distribución de reseñas</div>', unsafe_allow_html=True)
        review_bins = pd.cut(
            filtered["Reseñas"],
            bins=[-1, 0, 5, 10, 20, 50, 1000],
            labels=["0", "1-5", "6-10", "11-20", "21-50", "50+"],
        )
        review_counts = review_bins.value_counts().sort_index()
        st.bar_chart(review_counts, use_container_width=True, color="#334155", height=320)

    with col4:
        st.markdown('<div class="chart-title">Calificación de Google</div>', unsafe_allow_html=True)
        rating_data = filtered["Calificación"].dropna()
        if not rating_data.empty:
            rating_bins = pd.cut(
                rating_data,
                bins=[0, 2, 3, 3.5, 4, 4.5, 5],
                labels=["0-2", "2-3", "3-3.5", "3.5-4", "4-4.5", "4.5-5"],
            )
            rating_counts = rating_bins.value_counts().sort_index()
            st.bar_chart(rating_counts, use_container_width=True, color="#b45309", height=320)
        else:
            st.info("Sin datos de calificación.")


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def check_password() -> bool:
    """Password gate. Returns True if authenticated.
    Uses st.secrets["dashboard_password"]; if no secret is set, allows access (local dev)."""
    if st.session_state.get("authenticated", False):
        return True

    correct_pw = None
    try:
        correct_pw = st.secrets["dashboard_password"]
    except (FileNotFoundError, KeyError, Exception):
        return True  # No secret configured — local dev mode

    st.markdown(
        """
        <div class="hero" style="margin-top: 4rem;">
            <div class="hero-content">
                <span class="hero-badge">🔒 Acceso restringido</span>
                <h1 class="hero-title">Lima Importadores</h1>
                <p class="hero-subtitle">Ingresá la contraseña para acceder al dashboard.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
        pw = st.text_input("Contraseña", type="password", placeholder="••••••••", label_visibility="collapsed")
        submitted = st.form_submit_button("Ingresar", use_container_width=True)
        if submitted:
            if pw == correct_pw:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
    return False


def main():
    if not check_password():
        return

    df = load_data()

    # Hero
    st.markdown(
        """
        <div class="hero">
            <div class="hero-content">
                <span class="hero-badge">📦 Inteligencia comercial</span>
                <h1 class="hero-title">Lima Importadores</h1>
                <p class="hero-subtitle">Identificá negocios importadores en Perú sin presencia web sólida — listos para tu propuesta de servicios web.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df.empty:
        st.warning("⚠️ No hay datos. Ejecutá el scraper primero: `python -m lima_importadores run`")
        return

    all_districts = sorted(df["Distrito"].dropna().unique().tolist())

    # --- Sidebar ---
    with st.sidebar:
        st.markdown("### 🔎 Filtros")

        if st.button("↻ Mostrar todo", use_container_width=True):
            st.session_state["filter_districts"] = all_districts
            st.session_state["filter_qualification"] = "todos"
            st.session_state["filter_max_reviews"] = 500
            st.session_state["filter_web_presence"] = ["no_site", "outdated", "current", "unknown"]
            st.session_state["filter_name"] = ""
            st.rerun()

        districts = st.multiselect(
            "Distritos",
            options=all_districts,
            default=all_districts,
            key="filter_districts",
        )

        qualification = st.radio(
            "Calificación",
            options=["solo_calificados", "incluir_no_determinada", "todos"],
            format_func=lambda x: {
                "solo_calificados": "✅ Solo calificados",
                "incluir_no_determinada": "⚠️ Incluir antigüedad incierta",
                "todos": "📋 Todos los negocios",
            }[x],
            key="filter_qualification",
        )

        max_reviews = st.slider(
            "Máximo de reseñas",
            min_value=0, max_value=500, value=500, step=10,
            key="filter_max_reviews",
        )

        web_presence = st.multiselect(
            "Presencia web",
            options=["no_site", "outdated", "current", "unknown"],
            default=["no_site", "outdated", "current", "unknown"],
            format_func=lambda x: {
                "no_site": "⚫ Sin sitio web",
                "outdated": "🔴 Sitio desactualizado",
                "current": "🟢 Sitio actual",
                "unknown": "⚪ Desconocido",
            }[x],
            key="filter_web_presence",
        )

        name_search = st.text_input("🔍 Buscar por nombre", key="filter_name")

        st.markdown("---")
        st.caption(f"Última actualización: {date.today().isoformat()}")

    filters = {
        "districts": districts,
        "qualification": qualification,
        "max_reviews": max_reviews,
        "web_presence": web_presence,
        "name_search": name_search,
    }
    filtered = apply_filters(df, filters)

    # --- KPIs ---
    render_kpis(filtered, len(df))

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # --- Tabs ---
    tab_table, tab_analytics = st.tabs(["📋 Prospectos", "📊 Analytics"])

    with tab_table:
        render_table(filtered)

    with tab_analytics:
        render_analytics(filtered)

    # --- Export ---
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("##### 📥 Exportar resultados")

    today = date.today().isoformat()
    col1, col2, _ = st.columns([1, 1, 3])

    with col1:
        st.download_button(
            label="⬇️ CSV",
            data=build_csv(filtered),
            file_name=f"prospectos_{today}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col2:
        selected_districts = districts if districts else all_districts
        st.download_button(
            label="⬇️ Excel (1 hoja por distrito)",
            data=build_excel(filtered, selected_districts),
            file_name=f"prospectos_{today}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    st.markdown(
        f'<div class="footer-note">{len(filtered):,} prospectos en vista · {len(df):,} negocios totales en la base</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
