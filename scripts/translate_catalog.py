#!/usr/bin/env python3
"""
Auto-translate the UI catalog from the English source (translations/en.json)
into every other locale. English is always the source of truth.

Backends (pick one via env — the script never stores a key):
  DeepL:  export DEEPL_API_KEY=...        # https://www.deepl.com/pro-api
  n8n:    export N8N_TRANSLATE_URL=...    # a webhook that accepts {text,target} -> {translation}
          (matches the eOptika n8n-first orchestration convention)

Usage:
  python scripts/translate_catalog.py            # fill only missing keys
  python scripts/translate_catalog.py --all      # re-translate everything
Placeholders like {n} / {a} / {b} are preserved and never sent for translation.
"""
import os, re, sys, json, glob, urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LDIR = os.path.join(HERE, "translations")
TARGETS = ["hu", "de", "ro", "fi"]          # extend as storefronts grow
PLACEHOLDER = re.compile(r"\{[a-zA-Z0-9_]+\}")

def deepl(text, target):
    key = os.environ["DEEPL_API_KEY"]
    host = "api-free.deepl.com" if key.endswith(":fx") else "api.deepl.com"
    data = urllib.parse.urlencode(
        {"text": text, "target_lang": target.upper(), "source_lang": "EN"}).encode()
    req = urllib.request.Request(f"https://{host}/v2/translate", data=data,
                                 headers={"Authorization": f"DeepL-Auth-Key {key}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["translations"][0]["text"]

def n8n(text, target):
    url = os.environ["N8N_TRANSLATE_URL"]
    body = json.dumps({"text": text, "target": target}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["translation"]

def backend():
    if os.environ.get("DEEPL_API_KEY"): return deepl
    if os.environ.get("N8N_TRANSLATE_URL"): return n8n
    sys.exit("Set DEEPL_API_KEY or N8N_TRANSLATE_URL first (see file header).")

def translate(text, target, fn):
    # protect placeholders so the backend never mangles them
    slots = {}
    def stash(m):
        k = f"__{len(slots)}__"; slots[k] = m.group(0); return k
    protected = PLACEHOLDER.sub(stash, text)
    out = fn(protected, target)
    for k, v in slots.items():
        out = out.replace(k, v)
    return out

def main():
    do_all = "--all" in sys.argv
    fn = backend()
    src = json.load(open(os.path.join(LDIR, "en.json"), encoding="utf-8"))
    for loc in TARGETS:
        path = os.path.join(LDIR, f"{loc}.json")
        cur = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
        n = 0
        for key, en in src.items():
            if do_all or key not in cur:
                cur[key] = translate(en, loc, fn); n += 1
        json.dump(cur, open(path, "w", encoding="utf-8"), ensure_ascii=False,
                  indent=2, sort_keys=False)
        print(f"{loc}: wrote {len(cur)} keys ({n} translated)")

if __name__ == "__main__":
    main()
