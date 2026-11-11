# Atlas UI Contract — v1.2

The short, binding version of the design system. If it's not here, don't use it; ask the design chat to add it. Full spec: *eOptika Admin Design System v1.1*.

## Principles
One shell, two themes (gymove default, brand override), token-driven, dense-capable. Tools compose from **archetypes** — they don't design.

## Archetype chooser
| If your tool is… | Use archetype | Example |
|---|---|---|
| A live thing you watch all day (statuses, exceptions) | `control_room` | Parcel Control Room |
| A list/table of records you monitor & act on | `list_monitor` | Blue-Berry, Price Watch, Orders |
| Freshness/health of feeds + links out | `status_hub` | Data Warehouse, DevOps |
| KPIs + charts (analytics) | `dashboard_grid` | Moneyprint, Cockpit |
| Create / edit / settings / run-a-job | `form_view` | Radar rule, config |
| One record in depth (+ timeline) | `detail_view` | WIMO parcel, an order |

Most tools are one archetype. A big tool = a few pages, each its own archetype.

## Class vocabulary (the only classes you write)
- **Layout:** `.app .content .card .card__header .card__title .card__subtitle` · grids `.cols-2 .cols-3 .cols-main .kpis .stages .meta-grid` · `.toolbar .eyebrow`
- **Macros** (`{% import '_macros.html' as ui %}`): `ui.kpi(label,value,foot,tone,flag)` · `ui.pill(text,tone)` · `ui.icon(name)` · `ui.sidebar(nav,active)` (already in base)
- **Status/labels:** `.status.status--{success|danger|warning|info|muted}` · dots `.dot.dot--{tone}` · `.health .health-chip`
- **Buttons:** `.btn.btn--{primary|accent|success|danger|soft|ghost}` (+ `.btn--sm .btn--icon`)
- **Data:** `.table` (+ `.sub`) · `.frow .frow__main .frow__title .frow__meta` · `.stage .stage__n .stage__l .stage__bar` · `.chart-ph` · `.tnum` (figures) · `.code` (SKUs/IDs)
- **Nav/chrome:** `.segmented .chip .chip-link .pagination .menu .banner .fab`
- **Forms:** `.field .label .input .select .checkbox .switch .hint .field--error`
- **Detail:** `.detail-head .meta-grid .tab-row .tab .timeline`

## Buttons & colour doctrine (two axes)
- **Emphasis** (loudness, neutral intent): `primary → soft → ghost`. Say "click to proceed," never "beware." `accent` = the one featured proceed CTA.
- **Semantic** (consequence, only when real): `success` = finalize, `danger` = destructive.
- **`warning` and `info` are labels only — never buttons.**
- Rule: *if the colour tells you the action's consequence it's semantic; otherwise it's just emphasis.*

## Density
Three tiers via `data-density` on `<html>` (switch in the topbar): `comfortable` (default) · `compact` · `control` (control-room: 11–12px, tight gaps). Everything is token-scaled, so you get density free — never hand-shrink a screen.

## i18n
English is the source of truth. Wrap UI strings in `t('…')`; missing keys fall back to English. Add languages by extending `LANGUAGES` and running `scripts/translate_catalog.py`. `<html lang>` follows the choice.

## Do / Don't
- ✅ Extend `base.html`; use documented classes; keep figures in `.tnum`.
- ✅ Put money/date formatting in Python; keep colours semantic.
- ❌ No inline styles for anything the tokens cover; no new colours/fonts; no editing the shared files; no status colour on a button; no bespoke component without adding it to the system first.

*ds-version 1.2 — v1.1 base + archetype layer.*
