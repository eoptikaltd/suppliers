"""
Atlas Tool Dev Kit — seed for any eOptika internal tool.  v1.2
Default theme = gymove; pass theme="brand" to override. English is the i18n source.
Shell + shared nav come free; you write the {% block content %} using an archetype.

Run:  pip install -r requirements.txt  &&  python app.py   ->  http://localhost:8080
"""
import os, json, glob
from flask import Flask, render_template, request, redirect, make_response, url_for, abort
import atlas_menu

app = Flask(__name__)
APP_NAME = "Atlas — eOptika MIS"
HERE = os.path.dirname(__file__)

# --- Atlas menu: the same menu in every tool (how-to at the top of atlas_menu/__init__.py).
# Its content is atlas-mis/nav.json, published to gs://eoptika-atlas-menu; this tool
# serves it under /_atlas/ and the Atlas button (top-left) opens it.
atlas_menu.attach(app)
NAV = json.loads(atlas_menu.bundled("menu.json"))   # kept for templates that read `nav`

# --- i18n -----------------------------------------------------------------
# Languages offered (Atlas ruling 2026-11-12): English, Hungarian, Romanian (de/fi files
# stay). The choice is the cookie atlas_lang, shared by every eoptika.com tool and set by
# the Atlas language menu (/_atlas/menu.js); the older "lang" cookie is read when missing.
LANGUAGES = [("en","English"),("hu","Magyar"),("ro","Română")]
CATALOG = {}
for _f in glob.glob(os.path.join(HERE, "translations", "*.json")):
    with open(_f, encoding="utf-8") as fh:
        CATALOG[os.path.splitext(os.path.basename(_f))[0]] = json.load(fh)

DENSITIES = ("comfortable", "compact", "control")

def _cookie(name, allowed, default):
    v = request.cookies.get(name, default)
    return v if v in allowed else default

def current_lang():
    """atlas_lang (shared by every eoptika.com tool) first, then the older lang cookie."""
    for name in ("atlas_lang", "lang"):
        v = request.cookies.get(name)
        if v in dict(LANGUAGES):
            return v
    return "en"

@app.context_processor
def inject_globals():
    lang = current_lang()
    def t(key, **kw):
        s = CATALOG.get(lang, {}).get(key) or CATALOG.get("en", {}).get(key, key)
        return s.format(**kw) if kw else s
    return dict(t=t, app_name=APP_NAME, lang=lang, languages=LANGUAGES,
                density=_cookie("density", DENSITIES, "comfortable"), nav=NAV)

@app.route("/set-lang")
def set_lang():
    resp = make_response(redirect(request.args.get("next") or "/"))
    lang = request.args.get("lang", "en")
    if lang in dict(LANGUAGES): resp.set_cookie("lang", lang, max_age=31536000, samesite="Lax")
    return resp

@app.route("/set-density")
def set_density():
    resp = make_response(redirect(request.args.get("next") or "/"))
    d = request.args.get("d", "comfortable")
    if d in DENSITIES: resp.set_cookie("density", d, max_age=31536000, samesite="Lax")
    return resp

# --- pages ----------------------------------------------------------------
# THIS tool's identity in the shared nav (set to your tool's id from nav.json):
TOOL_ID = "suppliers"

ARCHETYPES = {
    "control_room":  "Parcel Control Room",
    "list_monitor":  "Blue-Berry Sourcing Monitor",
    "status_hub":    "Data Warehouse",
    "dashboard_grid":"Moneyprint",
    "form_view":     "Radar · New rule",
    "detail_view":   "WIMO · Parcel",
    "hub":           "Suppliers",
}

SUPPLIERS_CARDS = [
    {"name": "Blue-Berry", "icon": "suppliers", "desc": "Sourcing monitor — Blue-Berry channel",
     "url": "https://blue-berry-sourcing-monitor-thrl3bt5ya-ew.a.run.app", "status": "live"},
    {"name": "MrSonder", "icon": "suppliers", "desc": "Sourcing monitor — MrSonder channel",
     "url": "https://mrsonder-sourcing-monitor-thrl3bt5ya-ew.a.run.app", "status": "live"},
]

@app.route("/")
def index():
    return render_template(
        "suppliers.html", page_title="Suppliers", nav_active=TOOL_ID,
        hub_subtitle="Sourcing tools — click through to open.",
        cards=SUPPLIERS_CARDS,
    )

@app.route("/a/<name>")
def archetype(name):
    if name not in ARCHETYPES: abort(404)
    return render_template(f"archetypes/{name}.html",
                           page_title=ARCHETYPES[name], nav_active=TOOL_ID)

@app.route("/healthz")
def healthz():
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
