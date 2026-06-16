"""One-time (periodic) amenity/bed-type enrichment for the apartment directory.

Most community leasing sites are JavaScript SPAs, so we render each with headless
Chrome, strip the text, and have the Claude CLI extract bed types and key
amenities. Results are written back into apartments_data.json (committed data),
so the build just reads them. Re-run periodically to refresh. Graceful: a site
that blocks/times out is left without amenity data.

Run from pipeline/: python3 enrich_apartments.py
"""
from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path

DATA = Path(__file__).resolve().parent / "apartments_data.json"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
MODEL = "claude-haiku-4-5"

SCHEMA = {
    "type": "object",
    "properties": {
        "bed_types": {"type": "array", "items": {"type": "string"}},
        "pet_friendly": {"type": "boolean"},
        "pool": {"type": "boolean"},
        "fitness": {"type": "boolean"},
        "in_unit_laundry": {"type": "boolean"},
        "amenities": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["bed_types"],
}


def render_text(url: str) -> str:
    try:
        out = subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--dump-dom",
             "--virtual-time-budget=8000", url],
            capture_output=True, text=True, timeout=40).stdout
    except Exception:
        return ""
    out = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", out, flags=re.DOTALL | re.I)
    out = re.sub(r"<[^>]+>", " ", out)
    import html as _h
    return re.sub(r"\s+", " ", _h.unescape(out)).strip()[:7000]


def extract(name: str, text: str) -> dict | None:
    if len(text) < 200:
        return None
    prompt = (
        f"From this apartment community's website text, extract its offerings for "
        f"'{name}'. Fill the schema using ONLY the text.\n\n\"\"\"\n{text}\n\"\"\"\n\n"
        "bed_types: which of Studio, 1 BR, 2 BR, 3 BR, 4 BR are offered (array; empty "
        "if not stated). pet_friendly/pool/fitness/in_unit_laundry: true only if the "
        "text clearly indicates it. amenities: up to 6 short amenity phrases actually "
        "listed (e.g. 'Clubhouse', 'Dog park', 'Garage parking'). Never invent."
    )
    try:
        proc = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json",
             "--json-schema", json.dumps(SCHEMA), "--model", MODEL],
            capture_output=True, text=True, timeout=150)
        if proc.returncode != 0:
            return None
        return json.loads(proc.stdout).get("structured_output")
    except Exception:
        return None


def main():
    d = json.loads(DATA.read_text())
    comms = d["communities"]
    done = 0
    for i, c in enumerate(comms, 1):
        if c.get("amenities_done"):
            continue
        if not c.get("website"):
            c["amenities_done"] = True
            continue
        text = render_text(c["website"])
        data = extract(c["name"], text)
        c["amenities_done"] = True
        if data:
            c["beds"] = data.get("bed_types") or []
            c["pet"] = bool(data.get("pet_friendly"))
            c["pool"] = bool(data.get("pool"))
            c["fitness"] = bool(data.get("fitness"))
            c["laundry"] = bool(data.get("in_unit_laundry"))
            c["amenities"] = (data.get("amenities") or [])[:6]
            done += 1
            print(f"[{i}/{len(comms)}] ok {c['name']}: beds={c['beds']} "
                  f"pet={c['pet']} pool={c['pool']} fit={c['fitness']}", flush=True)
        else:
            print(f"[{i}/{len(comms)}] -- {c['name']} (no data)", flush=True)
        DATA.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
        time.sleep(0.5)
    print(f"\nenriched {done}/{len(comms)} with amenity data")


if __name__ == "__main__":
    main()
