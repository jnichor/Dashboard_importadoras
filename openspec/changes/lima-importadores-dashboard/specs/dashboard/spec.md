# Spec — Dashboard

**Domain**: dashboard
**Change**: lima-importadores-dashboard
**Date**: 2026-05-06

---

## Purpose

A Streamlit web application that reads from the SQLite database and lets the user explore, filter, and export qualifying prospects.

---

## Layout

```
+------------------+--------------------------------------------+
|                  |  Lima Importadores — Prospectos            |
|  SIDEBAR         |                                            |
|                  |  [Tabla de prospectos]                     |
|  Filtros         |                                            |
|  -------         |  [Export CSV]  [Export Excel]              |
|  Distritos       |                                            |
|  Calificación    +--------------------------------------------+
|  Reseñas         |
|  Web presence    |
|  Antigüedad      |
|  Buscar nombre   |
+------------------+
```

---

## Sidebar Controls

### District Filter
- Control: `st.multiselect`
- Label: "Distritos"
- Options: all distinct `district` values present in the database
- Default: all districts selected
- Behavior: filters the main table to show only businesses in selected districts

### Qualification Filter
- Control: `st.radio`
- Label: "Mostrar"
- Options:
  - "Solo prospectos calificados" (default)
  - "Incluir antigüedad no determinada"
  - "Todos los negocios"
- Behavior:
  - "Solo calificados" → `prospect_qualifies = 1`
  - "Incluir no determinada" → `prospect_qualifies = 1 OR antigüedad_flag = 'no_determinada'`
  - "Todos" → no filter on `prospect_qualifies`

### Max Reviews Filter
- Control: `st.slider`
- Label: "Máximo de reseñas"
- Range: 0 to 200, step 5
- Default: 50
- Behavior: filters `review_count <= selected_value`

### Web Presence Filter
- Control: `st.multiselect`
- Label: "Presencia web"
- Options: "Sin sitio web", "Sitio desactualizado", "Sitio actual", "Desconocido"
- Default: "Sin sitio web" and "Sitio desactualizado" selected
- Maps to `website_checks.verdict`: `no_site`, `outdated`, `current`, `unknown`

### Name Search
- Control: `st.text_input`
- Label: "Buscar por nombre"
- Behavior: case-insensitive substring filter on `businesses.name`

---

## Main Table

### Columns (in order)

| Column header | Source field | Notes |
|---------------|-------------|-------|
| Nombre | `businesses.name` | |
| Distrito | `businesses.district` | |
| Categoría | `businesses.category` | |
| Reseñas | `businesses.review_count` | |
| Calificación | `businesses.rating` | Show "—" if null |
| Teléfono | `businesses.phone` | Show "—" if null |
| Sitio web | `businesses.website_url` | Clickable link if present, "Sin sitio" if null |
| Estado web | `website_checks.verdict` | Display as badge: 🔴 Desactualizado / ⚫ Sin sitio / 🟢 Actual / ⚪ Desconocido |
| Antigüedad | `businesses.antigüedad_flag` | Display as: ✅ Califica / ⚠️ No determinada |

### Default Sort
- Primary: `prospect_qualifies DESC`
- Secondary: `review_count ASC`

### Pagination
- MUST use `st.dataframe` with `height` parameter to limit visible rows.
- Show row count: "Mostrando X de Y negocios"

---

## Export — CSV

- Control: `st.download_button`, label "Descargar CSV"
- Content: current filtered view (all rows matching active filters), all columns from main table plus `address`, `latitude`, `longitude`, `oldest_review_date`, `disqualify_reason`
- File name: `prospectos_{YYYY-MM-DD}.csv`
- Encoding: UTF-8 with BOM (for Excel compatibility)
- Behavior: single file regardless of district selection

---

## Export — Excel

- Control: `st.download_button`, label "Descargar Excel"
- Content: one sheet per selected district
- Each sheet name: the district name (truncated to 31 chars — Excel limit)
- Each sheet contains: same columns as CSV export, filtered to that district
- File name: `prospectos_{YYYY-MM-DD}.xlsx`
- Implementation: `pandas.ExcelWriter` with `openpyxl` engine, one `df.to_excel(writer, sheet_name=district)` call per district
- If only one district is selected: Excel file has one sheet
- If no district filter is active (all selected): one sheet per district that has at least one matching business

---

## State Persistence

- All sidebar filter values MUST persist in `st.session_state` across Streamlit reruns triggered by user interaction.
- The district multiselect MUST be initialized from the database on first load.

---

## Scenarios

**Given** the user selects districts "Miraflores" and "San Isidro" and clicks "Descargar Excel",
**When** the file is generated,
**Then** the Excel file MUST contain exactly 2 sheets named "Miraflores" and "San Isidro", each containing only businesses from that district matching the current filters.

**Given** the user sets Max Reviews to 30 and the table shows 15 businesses,
**When** the user clicks "Descargar CSV",
**Then** the CSV MUST contain exactly those 15 businesses.

**Given** the database contains no businesses yet,
**When** the dashboard loads,
**Then** it MUST display an empty table with a message "No hay datos. Ejecuta el scraper primero."

**Given** a business has `website_checks.verdict = 'outdated'`,
**When** it appears in the table,
**Then** the "Estado web" cell MUST display "🔴 Desactualizado".

**Given** the user types "chen" in the name search box,
**When** the filter applies,
**Then** only businesses whose `name` contains "chen" (case-insensitive) MUST appear.
