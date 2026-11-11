# Atlas tool — build instructions for Claude Code

You are building an internal **eOptika** tool inside the **Atlas** admin toolkit. The UI is already designed and decided. Your job is **content and data, not design.** Follow this exactly; read `ATLAS-UI-CONTRACT.md` before writing any template.

## Non-negotiable
- Do **not** invent styles, colours, fonts, spacing, or layout. Use **only** the classes listed in `ATLAS-UI-CONTRACT.md`.
- Do **not** edit `static/admin-tokens.css`, `static/atlas-icons.svg`, `templates/_macros.html`, or `templates/base.html`. They are the shared design system.
- Every page `{% extends "base.html" %}` and fills `{% block content %}`. The sidebar, topbar, search, language selector, and density switch come from the shell — never rebuild them.
- Default theme is **gymove**. Only render `theme="brand"` if explicitly asked.

## Steps
1. **Claim your slot.** Set `TOOL_ID` in `app.py` to this tool's `id` in `nav.json` so the sidebar highlights it. If the tool isn't in `nav.json`, add it: `{id, label, icon, url, status}` (icon = a sprite id, e.g. `wimo`).
2. **Pick ONE archetype** from `templates/archetypes/` that matches the tool (chooser in the contract). Copy it to `templates/<page>.html`.
3. **Swap the data.** Replace every `{# DATA #}` / demo `{% set %}` block with real values from BigQuery (`natural-caster-496309-j3`, EU, HUF) or your backend. Keep the class names.
4. **Wire routes** in `app.py` that query data and render your template(s).
5. **Formatting:** numbers get `.tnum`; SKUs / PO numbers / IDs get `.code`. Format money & dates in Python (`hu-HU`, HUF, thousands separators) — CSS only aligns them.
6. **Buttons follow the doctrine** (contract → Buttons): `primary` = proceed, `success` = finalize, `danger` = destructive. `warning`/`info` are **labels, never buttons**.
7. **New UI no archetype covers?** STOP. Ask the design chat to add the component to the system. Do not freehand it here — that is how 19 tools drift apart.

## Assets — production uses the shared bucket (lockstep)
Locally, CSS/fonts/sprite are bundled in `static/`. In production, point `base.html`'s stylesheet, font preloads, and the sprite include at the bucket so a design bump reaches every tool at once:
```
https://assets.atlas.eoptika.hu/admin-tokens.1.2.css
https://assets.atlas.eoptika.hu/atlas-icons.svg
https://assets.atlas.eoptika.hu/fonts/...
```

## Deploy (run on the laptop, authed as hello@eoptika.com)

These steps encode lessons from the first live deploy (Data Warehouse). Follow them in order.

**0. Runtime & build prerequisites (once per project — already done for `natural-caster-496309-j3`, listed for reference/new projects).**
- gunicorn timeout must cover a cold BigQuery load (~100s). The kit `Dockerfile` uses `--timeout 180`; do **not** lower it, or the first request is killed mid-query.
- First `--source` deploy in a project 403s because the Cloud Build identity can't read the upload bucket. Fix once:
  ```
  gsutil iam ch serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com:roles/storage.objectViewer \
    gs://run-sources-PROJECT_ID-europe-west1
  ```
  (PROJECT_NUMBER for this project = 969393182764.)

**1. Deploy — always with IAP and the Atlas runtime identity:**
```
gcloud run deploy <tool-id> --source . \
  --project natural-caster-496309-j3 --region europe-west1 \
  --no-allow-unauthenticated --iap \
  --service-account=sa-atlas@natural-caster-496309-j3.iam.gserviceaccount.com
```
`--iap` gates the service; `sa-atlas` is the tool runtime identity (not the compute default). If `--iap` errors that IAP isn't configured, deploy without it, enable IAP once in the Cloud Console, then redeploy.

**2. Grant the runtime SA its BigQuery roles** (if the tool reads BQ — the page 500s on data without these; the build still succeeds, so this is easy to miss):
```
for R in roles/bigquery.jobUser roles/bigquery.user roles/bigquery.metadataViewer; do
  gcloud projects add-iam-policy-binding natural-caster-496309-j3 \
    --member="serviceAccount:sa-atlas@natural-caster-496309-j3.iam.gserviceaccount.com" \
    --role="$R" --condition=None -q
done
```
`bigquery.user` (not `dataViewer`) is what grants `bigquery.transfers.get` — a tool reading Data Transfer configs 500s with `dataViewer` alone; there is no standalone transfer-viewer role. NOTE: `metadataViewer` covers table metadata but **not** region-wide `INFORMATION_SCHEMA.TABLE_STORAGE` — storage-total queries need their own handling/fallback in the data layer.

**3. Grant access through IAP** — enabling IAP does **not** grant anyone access; even the owner is blocked until bound. Add each user (or a Workspace group if one exists):
```
gcloud beta iap web add-iam-policy-binding \
  --resource-type=cloud-run --service=<tool-id> --region=europe-west1 \
  --member="user:hello@eoptika.com" --role="roles/iap.httpsResourceAccessor" \
  --project natural-caster-496309-j3
```
Repeat per user. (If/when a Workspace admin creates `atlas-staff@eoptika.com`, bind `group:atlas-staff@eoptika.com` once instead and skip per-user grants.)

**4. Verify** — a browser hits IAP login (correct); curl can't complete IAP's OAuth handshake, so a bearer-token curl returns 401 (that is IAP working, not a failure). Confirm in a **browser** signed in as a bound user; first load is slow (cold BQ).

**5. Custom domain (per tool).**
- One-time: `eoptika.com` must be verified via **Google Site Verification** (`gcloud domains verify eoptika.com` → add the TXT in Route 53 → confirm with `gcloud domains list-user-verified`). This is separate from Search Console verification — a Search Console "auto verified" does **not** satisfy Cloud Run mappings.
- Then per tool:
  ```
  gcloud beta run domain-mappings create --service=<tool-id> \
    --domain=<tool-id>.eoptika.com --region=europe-west1 --project natural-caster-496309-j3
  ```
  It prints a record — for a subdomain this is a **CNAME → ghs.googlehosted.com** (never an A record / IP). Add it in Route 53 (name = `<tool-id>`, type CNAME, value from the command, TTL 300). Cert auto-provisions in 15–60 min.
- IAP cookies are per-domain, so sign in once more on the `.com` hostname.

## Done when
- The sidebar shows the whole Atlas menu and highlights this tool.
- The page uses exactly one archetype, real data, documented classes only.
- Language selector + all three density tiers work (they come from the shell — untouched).
- `GET /healthz` returns 200 **locally / before IAP**. NOTE: once `--iap` is on, `/healthz` is intercepted by the Google frontend and returns a generic 404 externally — this is expected and does not affect Cloud Run's internal container health checks. Do not rely on an external `/healthz` 200 as a post-deploy check.
- Signed-in browser renders the real dashboard on both the `run.app` URL and (once mapped) `<tool-id>.eoptika.com`.
