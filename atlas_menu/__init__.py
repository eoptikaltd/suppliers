"""Atlas menu — one shared menu for every eOptika tool.  v2 · 2026-11-12 (files: language menu, sign-in-again)

What it does
    Adds four small files to the tool, all under /_atlas/ on the tool's own address:
        /_atlas/menu.js         draws the menu (the Atlas button, top-left, opens it)
        /_atlas/menu.css        its look
        /_atlas/menu-icons.svg  the menu's icons
        /_atlas/menu.json       what is in the menu (groups, tools, status, links)
    Each file is read from the private Cloud Storage folder gs://eoptika-atlas-menu
    (kept for 5 minutes), so a menu change published there reaches every tool
    without redeploying it. If the folder cannot be read, the copy bundled in
    atlas_menu/files/ is used instead, so the menu never disappears.

Who publishes the folder
    menu.json            the atlas-mis build (its nav.json), when Sabie approves it
    menu.js/.css/-icons  the atlas-tool-dev-kit build, when Sabie approves it

Add it to a tool (copy this whole atlas_menu/ folder into the tool first)
    Flask:  import atlas_menu; atlas_menu.attach(app)
    Dash:   import atlas_menu; atlas_menu.attach(app.server)
    Page:   <script src="/_atlas/menu.js?tool=<tool id>" defer></script>
            optional  &mount=<css selector>  puts the Atlas button at the start of
            that element (e.g. the tool's top bar) instead of floating top-left.

Who sees which tools
    attach(app, allowed=fn): fn(request) returns the set of tool ids this person
    may open, or None for "all". Tools and groups outside it are left out of
    menu.json. Today every tool passes nothing (everyone sees everything): the
    per-person list arrives when Gateway hands it over. A tool that sits behind
    Gateway can have Gateway answer /_atlas/menu.json itself.

Needs only what every eOptika tool already has: Flask and google-auth.
"""
import json
import logging
import os
import threading
import time

from flask import Blueprint, Response, abort, request

BUCKET = os.environ.get("ATLAS_MENU_BUCKET", "eoptika-atlas-menu")
# "local" = never read the bucket (tests, laptops); anything else = bucket first
SOURCE = os.environ.get("ATLAS_MENU_SOURCE", "bucket")
KEEP_SECONDS = 300          # how long a file read from the bucket is reused
WAIT_SECONDS = 3            # never hold a page longer than this for the bucket

FILES = {
    "menu.js": "text/javascript; charset=utf-8",
    "menu.css": "text/css; charset=utf-8",
    "menu-icons.svg": "image/svg+xml",
    "menu.json": "application/json; charset=utf-8",
}
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "files")
log = logging.getLogger("atlas_menu")

_kept = {}                  # name -> (read_at, bytes)   last good copy from the bucket
_tried = {}                 # name -> time of the last attempt (good or bad)
_lock = threading.Lock()
_session = None


def bundled(name):
    """The copy shipped inside the tool (used when the bucket cannot be read)."""
    with open(os.path.join(HERE, name), "rb") as fh:
        return fh.read()


def _bucket_session():
    global _session
    if _session is None:
        import google.auth
        from google.auth.transport.requests import AuthorizedSession
        creds, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/devstorage.read_only"])
        _session = AuthorizedSession(creds)
    return _session


def _read_bucket(name):
    url = f"https://storage.googleapis.com/storage/v1/b/{BUCKET}/o/{name}?alt=media"
    try:
        r = _bucket_session().get(url, timeout=WAIT_SECONDS)
        if r.status_code == 200 and r.content:
            return r.content
        log.warning("atlas_menu: %s from gs://%s answered %s; keeping the copy it has",
                    name, BUCKET, r.status_code)
    except Exception as e:  # no credentials, no network, ... -> fall back quietly
        log.warning("atlas_menu: cannot read %s from gs://%s (%s); keeping the copy it has",
                    name, BUCKET, type(e).__name__)
    return None


def current(name):
    """Newest copy of a menu file: the bucket (kept 5 min), else last good, else bundled."""
    if SOURCE == "local":
        return bundled(name)
    now = time.time()
    with _lock:
        due = now - _tried.get(name, 0) >= KEEP_SECONDS
        if due:
            _tried[name] = now          # one reader at a time; failures also wait 5 min
    if due:
        data = _read_bucket(name)
        if data is not None:
            with _lock:
                _kept[name] = (now, data)
    kept = _kept.get(name)
    return kept[1] if kept else bundled(name)


def menu_for(menu, allowed):
    """Leave out tools outside `allowed` (a set of ids; None = all), then empty groups."""
    if allowed is None:
        return menu
    groups = []
    for g in menu.get("groups", []):
        items = [it for it in g.get("items", []) if it.get("id") in allowed]
        if items:
            groups.append(dict(g, items=items))
    return dict(menu, groups=groups)


def attach(app, allowed=None):
    """Serve /_atlas/<file> from this Flask app (for Dash: pass app.server)."""
    bp = Blueprint("atlas_menu", __name__)

    @bp.route("/_atlas/<name>")
    def atlas_menu_file(name):
        if name not in FILES:
            abort(404)
        data = current(name)
        if name == "menu.json":
            who = allowed(request) if allowed else None
            if who is not None:
                data = json.dumps(menu_for(json.loads(data), set(who)),
                                  ensure_ascii=False).encode("utf-8")
        resp = Response(data, mimetype=None, content_type=FILES[name])
        resp.headers["Cache-Control"] = "private, max-age=300"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        return resp

    app.register_blueprint(bp)
    return app
