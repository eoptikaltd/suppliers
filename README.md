# Atlas Tool Dev Kit — v1.2

Everything needed to build an on-brand eOptika internal tool inside **Atlas**.
Attach this whole folder to a new tool-development chat and point it at `CLAUDE.md`.

## Inside
- `CLAUDE.md` — paste-and-go instructions for the build chat
- `ATLAS-UI-CONTRACT.md` — binding UI rules + archetype chooser + class list
- `templates/base.html` — shared shell (sidebar from `nav.json`, topbar, language + 3 density tiers)
- `templates/archetypes/` — six page archetypes (copy one, swap the data)
- `templates/_macros.html` — `kpi` / `pill` / `icon` / `sidebar` macros · `_sprite.html` — icon sprite
- `static/admin-tokens.css` — the design system (v1.1 + archetype layer)
- `static/atlas-icons.svg` — icon set · `static/fonts/` — self-hosted DM Sans + Cormorant (GDPR-clean)
- `translations/` — en (source) + hu/de/ro/fi · `scripts/translate_catalog.py`
- `nav.json` — the shared Atlas menu (all tools)
- `Dockerfile`, `requirements.txt` — Cloud Run ready (non-root, gunicorn `--preload`)
- `.github/workflows/deploy.yml` — build + deploy via Workload Identity Federation

## Run it
```
pip install -r requirements.txt && python app.py     # http://localhost:8080
```
`/` lists the archetypes; `/a/<name>` renders each. Toggle language + density in the topbar.

## Build a tool
1. Set `TOOL_ID` in `app.py` (this tool's id in `nav.json`).
2. Copy the archetype that fits → `templates/<page>.html`.
3. Swap the `{# DATA #}` blocks for your BigQuery query; wire the route in `app.py`.
4. Deploy — see `CLAUDE.md`.

Don't freehand UI — pick an archetype. Full rules in `ATLAS-UI-CONTRACT.md`.
