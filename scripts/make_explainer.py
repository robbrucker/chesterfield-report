"""Chesterfield Report place/data EXPLAINER video (vertical 1080x1920).

The signature short-form format: a real satellite/street map of where a story is
happening (pin on the spot), animated data supers, and a vd2 voiceover. Owned/open
imagery only (Esri World Imagery + CARTO/OSM, attributed). No AI humans, no scraped
photos. Driven by a per-story "brief" (JSON) so any place/data story can be rendered.

Env (scripts/.deploy.env): ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID.
Host tools: ffmpeg, ffprobe, ImageMagick (magick/convert), rsvg-convert.

Brief schema (JSON):
{
  "headline": "Shoosmith Landfill files for bankruptcy",
  "kicker": "WHAT'S HAPPENING IN CHESTERFIELD",
  "address": "11800 Lewis Road, Chester, VA 23831",      # or "lat"/"lon"
  "place_label": "SHOOSMITH LANDFILL",
  "context_label": "CHESTER, CHESTERFIELD CO.",
  "scenes": [
    {"type":"title",   "vo":"..."},
    {"type":"context", "vo":"...", "line":"Lewis Road, Chester", "sub":"Closed since 2022"},
    {"type":"data",    "vo":"...", "supers":[["$173 MILLION","estimated cleanup burden"], ...]},
    {"type":"cta",     "vo":"...", "question":"So who pays to clean it up?"}
  ]
}

CLI:  /usr/bin/python3 scripts/make_explainer.py --brief brief.json --out /tmp/ex.mp4
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGO_SVG = ROOT / "public" / "assets" / "logo-mark.svg"
W, H = 1080, 1920
DARK = "#06141b"
TEAL = "#5ef0db"
WHITE = "#f2f8f6"
MUTED = "#9fc9c2"
EL_MODEL = "eleven_turbo_v2_5"
UA = "chesterfield-report/1.0"


def _font(*cands):
    for c in cands:
        if c.startswith("/") and Path(c).exists():
            return c
    return cands[-1]


SERIF = _font("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
              "/System/Library/Fonts/Supplemental/Georgia.ttf", "Times-Roman")
SANS_B = _font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
               "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "Helvetica-Bold")


def _sh(c):
    subprocess.run(c, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _dur(f):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]).strip())


def _size(f):
    o = subprocess.check_output(["magick", "identify", "-format", "%w %h", f]).split()
    return int(o[0]), int(o[1])


# ---- geocode ----
def _geocode(address):
    u = ("https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?"
         + urllib.parse.urlencode({"address": address, "benchmark": "Public_AR_Current",
                                   "format": "json"}))
    try:
        d = json.load(urllib.request.urlopen(u, timeout=30))
        m = d["result"]["addressMatches"]
        if m:
            return m[0]["coordinates"]["y"], m[0]["coordinates"]["x"]
    except Exception:
        pass
    req = urllib.request.Request(
        "https://nominatim.openstreetmap.org/search?"
        + urllib.parse.urlencode({"q": address, "format": "json", "limit": "1"}),
        headers={"User-Agent": UA})
    d = json.load(urllib.request.urlopen(req, timeout=30))
    if not d:
        raise RuntimeError(f"could not geocode: {address}")
    return float(d[0]["lat"]), float(d[0]["lon"])


# ---- tile stitch ----
def _deg2px(lat, lon, z, tile):
    n = 2 ** z
    x = (lon + 180.0) / 360.0 * n * tile
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n * tile
    return x, y


def _stitch(url_tmpl, z, lat, lon, out_w, out_h, out, t, tile=256, yx=False):
    cx, cy = _deg2px(lat, lon, z, tile)
    left, top = cx - out_w / 2, cy - out_h / 2
    x0, x1 = int(left // tile), int((left + out_w) // tile)
    y0, y1 = int(top // tile), int((top + out_h) // tile)
    files = []
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            u = url_tmpl.format(z=z, y=ty, x=tx)
            f = f"{t}/_t_{z}_{tx}_{ty}.png"
            if not os.path.exists(f):
                req = urllib.request.Request(u, headers={"User-Agent": UA})
                open(f, "wb").write(urllib.request.urlopen(req, timeout=30).read())
            files.append(f)
    cols, rows = x1 - x0 + 1, y1 - y0 + 1
    mosaic = f"{t}/_mosaic_{z}.png"
    _sh(["magick", "montage", *files, "-tile", f"{cols}x{rows}", "-geometry", "+0+0",
         "-background", "black", mosaic])
    cropx, cropy = int(left - x0 * tile), int(top - y0 * tile)
    _sh(["magick", mosaic, "-crop", f"{out_w}x{out_h}+{cropx}+{cropy}", "+repage", out])
    return out


SAT = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
CARTO = "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"


# ---- card baking ----
def _card(t, mapimg, out, label=None, darken=0.0):
    _sh(["magick", "-size", "1080x650", f"gradient:none-{DARK}", f"{t}/_fade.png"])
    cmd = ["magick", "-size", f"{W}x{H}", f"xc:{DARK}",
           "(", mapimg, ")", "-gravity", "North", "-geometry", "+0+0", "-composite",
           "(", f"{t}/_fade.png", ")", "-gravity", "North", "-geometry", "+0+760", "-composite"]
    if darken > 0:
        cmd += ["(", "-size", "1080x1350", f"xc:rgba(6,20,27,{darken:.2f})", ")",
                "-gravity", "North", "-geometry", "+0+0", "-composite"]
    cmd += ["-fill", "rgba(94,240,219,0.25)", "-draw", "circle 540,675 540,706",
            "-stroke", "white", "-strokewidth", "5", "-fill", "#16b89f",
            "-draw", "circle 540,675 540,692", "-stroke", "none"]
    if label:
        cmd += ["-gravity", "North", "-font", SANS_B, "-pointsize", "40", "-fill", WHITE,
                "-undercolor", "#06141bcc", "-annotate", "+0+726", f" {label} "]
    cmd += ["-gravity", "SouthEast", "-font", SANS_B, "-pointsize", "20", "-fill", MUTED,
            "-undercolor", "#06141b99", "-annotate", "+18+590", " Imagery: Esri / CARTO / OSM "]
    cmd += [out]
    _sh(cmd)
    return out


def _text(out, text, font, pt, fill, boxw=None):
    c = ["magick", "-background", "none", "-fill", fill, "-font", font,
         "-pointsize", str(pt), "-gravity", "center"]
    c += (["-size", f"{boxw}x", f"caption:{text}"] if boxw else [f"label:{text}"])
    c += [out]
    _sh(c)
    return out, _size(out)


# ---- vd2 voiceover ----
def _tts(text, out):
    key = os.environ["ELEVENLABS_API_KEY"]
    voice = os.environ["ELEVENLABS_VOICE_ID"]
    body = json.dumps({"text": text, "model_id": EL_MODEL,
                       "voice_settings": {"stability": 0.5, "similarity_boost": 0.8,
                                          "style": 0.2}}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
        data=body, headers={"xi-api-key": key, "Content-Type": "application/json",
                            "Accept": "audio/mpeg"})
    open(out, "wb").write(urllib.request.urlopen(req, timeout=90).read())


# ---- scene -> clip ----
def _elements(t, scene, brief):
    """Return [(png, y_center, start_delay)] for a scene."""
    els = []
    typ = scene["type"]
    if typ == "title":
        p, _ = _text(f"{t}/e_k.png", brief.get("kicker", "CHESTERFIELD REPORT"), SANS_B, 38, TEAL)
        els.append((p, 1455, 0.3))
        p, _ = _text(f"{t}/e_h.png", brief["headline"], SERIF, 70, WHITE, 980)
        els.append((p, 1610, 0.7))
    elif typ == "context":
        if scene.get("line"):
            p, _ = _text(f"{t}/e_c1.png", scene["line"], SERIF, 66, WHITE)
            els.append((p, 1480, 0.3))
        if scene.get("sub"):
            p, _ = _text(f"{t}/e_c2.png", scene["sub"], SANS_B, 40, MUTED)
            els.append((p, 1600, 0.9))
    elif typ == "data":
        y = 760
        st = 0.4
        for i, pair in enumerate(scene["supers"]):
            big = pair[0] if isinstance(pair, (list, tuple)) else pair
            small = pair[1] if isinstance(pair, (list, tuple)) and len(pair) > 1 else ""
            p, _ = _text(f"{t}/e_d{i}a.png", big, SANS_B, 92, WHITE, 1000)
            els.append((p, y, st))
            y += 110
            if small:
                p, _ = _text(f"{t}/e_d{i}b.png", small, SANS_B, 38, TEAL)
                els.append((p, y, st + 0.35))
                y += 130
            else:
                y += 60
            st += 3.4
    elif typ == "cta":
        if scene.get("question"):
            p, _ = _text(f"{t}/e_q.png", scene["question"], SERIF, 62, WHITE, 980)
            els.append((p, 1470, 0.3))
        p, _ = _text(f"{t}/e_u.png", brief.get("url", "chesterfieldreport.com"), SANS_B, 52, TEAL)
        els.append((p, 1620, 1.0))
    return els


def build_from_brief(brief, out_path):
    """Render an explainer MP4 from a brief dict. Returns out_path."""
    lat = brief.get("lat")
    lon = brief.get("lon")
    if lat is None or lon is None:
        lat, lon = _geocode(brief["address"])
    with tempfile.TemporaryDirectory() as t:
        # maps + cards
        _stitch(SAT, 16, lat, lon, 1080, 1350, f"{t}/sat16.png", t, yx=True)
        _stitch(SAT, 17, lat, lon, 1080, 1350, f"{t}/sat17.png", t, yx=True)
        _stitch(CARTO, 12, lat, lon, 1080, 1350, f"{t}/map12.png", t)
        _card(t, f"{t}/sat16.png", f"{t}/c_title.png", label=brief.get("place_label"), darken=0.18)
        _card(t, f"{t}/map12.png", f"{t}/c_ctx.png", label=brief.get("context_label"), darken=0.10)
        _card(t, f"{t}/sat17.png", f"{t}/c_data.png", label=None, darken=0.42)
        cards = {"title": f"{t}/c_title.png", "context": f"{t}/c_ctx.png",
                 "data": f"{t}/c_data.png", "cta": f"{t}/c_title.png"}
        zoom_in = {"title": True, "context": True, "data": False, "cta": True}
        # logo bug
        try:
            _sh(["rsvg-convert", "-w", "120", "-h", "120", str(LOGO_SVG), "-o", f"{t}/bug.png"])
            have_bug = True
        except Exception:
            have_bug = False

        parts = []
        scenes = brief["scenes"]
        for ci, scene in enumerate(scenes):
            vo = f"{t}/vo{ci}.mp3"
            _tts(scene["vo"], vo)
            T = round(_dur(vo) + 0.7, 2)
            frames = int(T * 30)
            card = cards[scene["type"]]
            z = "min(zoom+0.00035,1.06)" if zoom_in[scene["type"]] \
                else "if(eq(on,1),1.06,max(zoom-0.00022,1.0))"
            els = _elements(t, scene, brief)
            inputs = ["-loop", "1", "-framerate", "30", "-i", card, "-i", vo]
            for png, _, _ in els:
                inputs += ["-loop", "1", "-framerate", "30", "-i", png]
            bug = have_bug and scene["type"] == "cta"
            if bug:
                inputs += ["-loop", "1", "-framerate", "30", "-i", f"{t}/bug.png"]
            fg = [f"[0:v]scale={W}:{H},zoompan=z='{z}':d={frames}:s={W}x{H}:fps=30,format=rgba[bg]"]
            prev = "bg"
            for k, (png, yc, st) in enumerate(els):
                inp = k + 2
                fg.append(f"[{inp}:v]format=rgba,fade=t=in:st={st}:d=0.5:alpha=1[e{k}]")
                fg.append(f"[{prev}][e{k}]overlay=x='(main_w-overlay_w)/2':"
                          f"y='{yc}-overlay_h/2 + 30*clip(1-(t-{st})/0.5,0,1)':eval=frame[o{k}]")
                prev = f"o{k}"
            if bug:
                bi = len(els) + 2
                fg.append(f"[{bi}:v]format=rgba,fade=t=in:st=0.2:d=0.5:alpha=1[bug]")
                fg.append(f"[{prev}][bug]overlay=x=60:y=70[ob]")
                prev = "ob"
            fo = round(T - 0.45, 2)
            fin = "fade=t=in:st=0:d=0.4," if ci == 0 else "fade=t=in:st=0:d=0.2,"
            fg.append(f"[{prev}]{fin}fade=t=out:st={fo}:d=0.35,format=yuv420p[v]")
            part = f"{t}/p{ci}.mp4"
            _sh(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fg),
                 "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "medium",
                 "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                 "-r", "30", "-t", str(T), part])
            parts.append(part)

        listf = f"{t}/list.txt"
        with open(listf, "w") as f:
            for p in parts:
                f.write(f"file '{p}'\n")
        _sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listf,
             "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
             "-r", "30", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
             "-af", "loudnorm=I=-14:TP=-1.5", "-movflags", "+faststart", out_path])
    return out_path


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", required=True, help="Path to a brief JSON file.")
    ap.add_argument("--out", default="/tmp/cr_explainer.mp4")
    a = ap.parse_args()
    brief = json.loads(Path(a.brief).read_text(encoding="utf-8"))
    out = build_from_brief(brief, a.out)
    print("EXPLAINER:", out, f"({_dur(out):.1f}s)")


if __name__ == "__main__":
    main()
