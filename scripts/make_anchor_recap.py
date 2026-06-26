"""Daily Chesterfield Report ANCHOR recap video (vertical 1080x1920).

A rotating member of the AI anchor crew reads the day's top stories to camera, via
Replicate's `prunaai/p-video-avatar` (photo + script -> talking head with built-in TTS).
We then add a light broadcast overlay (logo bug + lower-third bar + URL) and hand the
MP4 back. Reuses the day's stories gathered by post_facebook.py. Runs on the VPS.

Env (scripts/.deploy.env): REPLICATE_API_TOKEN.
Host tools: ffmpeg, ffprobe, ImageMagick (convert), rsvg-convert.

CLI:  /usr/bin/python3 scripts/make_anchor_recap.py [--date YYYY-MM-DD] [--out /tmp/anchor.mp4]
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANCHORS = Path(__file__).resolve().parent / "anchors"
LOGO_SVG = ROOT / "public" / "assets" / "logo-mark.svg"
W, H = 1080, 1920


def _font(*candidates):
    """First existing font file, else the last candidate (a family name IM can resolve)."""
    for c in candidates:
        if c.startswith("/") and Path(c).exists():
            return c
    return candidates[-1]


SERIF = _font("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
              "/System/Library/Fonts/Supplemental/Georgia.ttf", "Times-Roman")
SANS_B = _font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
               "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "Helvetica-Bold")

# Rotating crew: (portrait, built-in voice). Index = date.toordinal() % len(CREW).
CREW = [
    ("anchor_white_m_40s.png", "Charon (Male)"),
    ("anchor_black_w_30s.png", "Aoede (Female)"),
    ("anchor_white_m_50s_glasses.png", "Puck (Male)"),
    ("anchor_latina_w_40s.png", "Leda (Female)"),
    ("anchor_asian_m_30s.png", "Orus (Male)"),
]
MODEL = "prunaai/p-video-avatar"
VPROMPT = ("Professional television news anchor seated at the news desk, looking directly "
           "into camera, natural accurate lip sync, subtle natural head movement, composed.")
VOICEPROMPT = "Speak warmly, clearly and confidently, like a trusted local television news anchor."
MAX_STORIES = 3            # keep the read (and the per-clip cost) tight
SCRIPT_CAP = 850           # hard char cap on the spoken script


# ---- Replicate (self-contained; UA + 429 retry; data-URI inputs) ----
def _headers():
    return {"Authorization": f"Bearer {os.environ['REPLICATE_API_TOKEN']}",
            "Content-Type": "application/json", "User-Agent": "chesterfield-report/1.0"}


def _req(url, data=None, method="GET"):
    for attempt in range(8):
        req = urllib.request.Request(
            url, data=(json.dumps(data).encode() if data else None),
            headers=_headers(), method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 7:
                time.sleep(2.5)
                continue
            raise


def _latest_version(model):
    owner, name = model.split("/")
    return _req(f"https://api.replicate.com/v1/models/{owner}/{name}")["latest_version"]["id"]


def _data_uri(path, mime):
    return f"data:{mime};base64," + base64.b64encode(Path(path).read_bytes()).decode()


NEG = ("subtitles, captions, closed captions, on-screen text, text overlay, words on screen, "
       "lower third graphics, watermark, logo, banner, ticker, station bug")


def _avatar_clip(portrait, script, voice, out, resolution="720p"):
    body = {"version": _latest_version(MODEL), "input": {
        "image": _data_uri(portrait, "image/png"),
        "voice_script": script, "voice": voice, "voice_language": "English (US)",
        "voice_prompt": VOICEPROMPT, "video_prompt": VPROMPT,
        "negative_prompt": NEG, "strength_negative_prompt": 0.85,
        "resolution": resolution, "seed": 7}}
    p = _req("https://api.replicate.com/v1/predictions", body, "POST")
    pid = p["id"]
    while p["status"] not in ("succeeded", "failed", "canceled"):
        time.sleep(4)
        p = _req(f"https://api.replicate.com/v1/predictions/{pid}")
    if p["status"] != "succeeded":
        raise RuntimeError(f"p-video-avatar {p['status']}: {p.get('error')}")
    o = p["output"]
    url = o if isinstance(o, str) else o[0]
    urllib.request.urlretrieve(url, out)
    return out


# ---- script + overlay ----
def _first_sentence(text):
    text = (text or "").strip()
    for end in (". ", "! ", "? "):
        i = text.find(end)
        if 0 < i < 180:
            return text[:i + 1].strip()
    return text[:180].strip()


def _build_script(stories, nice):
    lead_h, _lead_url, lead_r = stories[0]
    parts = [f"Today in Chesterfield. It's {nice}, and here are today's top local stories.",
             f"Our lead story: {lead_h}. {_first_sentence(lead_r)}"]
    extra = [h for (h, _u, _r) in stories[1:MAX_STORIES]]
    if extra:
        parts.append("Also making news: " + "; ".join(extra) + ".")
    parts.append("For the full reports, visit Chesterfield Report dot com. "
                 "Follow for daily local news from The Chesterfield Report.")
    script = " ".join(p.strip() for p in parts if p.strip())
    return script[:SCRIPT_CAP]


def _sh(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _overlay_png(nice, out):
    """Static broadcast overlay: logo bug (top-left), lower-third bar (brand + date),
    URL super (bottom). One transparent PNG composited over the whole clip."""
    tmp = out + ".logo.png"
    try:
        _sh(["rsvg-convert", "-w", "150", "-h", "150", str(LOGO_SVG), "-o", tmp])
        logo_ok = True
    except Exception:
        logo_ok = False
    cmd = ["convert", "-size", f"{W}x{H}", "xc:none"]
    # lower-third bar
    cmd += ["-fill", "rgba(6,20,27,0.72)", "-draw", "roundrectangle 70,1560 1010,1700 18,18"]
    cmd += ["-fill", "#5ef0db", "-draw", "rectangle 70,1560 84,1700"]  # accent edge
    cmd += ["-font", SANS_B, "-pointsize", "40", "-fill", "#f2f8f6",
            "-gravity", "NorthWest", "-annotate", "+120+1585", "THE CHESTERFIELD REPORT"]
    cmd += ["-font", SERIF, "-pointsize", "34", "-fill", "#9fc9c2",
            "-annotate", "+120+1640", nice]
    cmd += ["-gravity", "South", "-font", SANS_B, "-pointsize", "34", "-fill", "#5ef0db",
            "-annotate", "+0+70", "chesterfieldreport.com"]
    cmd += [out]
    _sh(cmd)
    if logo_ok:
        _sh(["convert", out, tmp, "-gravity", "NorthWest", "-geometry", "+60+60",
             "-compose", "over", "-composite", out])
        try:
            os.remove(tmp)
        except OSError:
            pass
    return out


def build_anchor_recap(stories, date_str, out_path, resolution="720p"):
    """stories = [(headline, url, recap), ...]. Returns out_path, or None if no stories.
    Raises on tooling/API errors so the caller can fall back to a text post."""
    if not stories:
        return None
    try:
        nice = datetime.strptime(date_str, "%Y-%m-%d").strftime("%A, %B %-d")
    except ValueError:
        nice = date_str
    idx = datetime.strptime(date_str, "%Y-%m-%d").toordinal() % len(CREW) \
        if _is_date(date_str) else 0
    portrait, voice = CREW[idx]
    script = _build_script(stories, nice)

    raw = out_path + ".raw.mp4"
    _avatar_clip(str(ANCHORS / portrait), script, voice, raw, resolution=resolution)

    overlay = out_path + ".ov.png"
    _overlay_png(nice, overlay)
    # scale to 1080x1920, composite the static overlay, gentle in/out fades, loudnorm
    dur = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", raw]).strip())
    fo = max(0.3, dur - 0.4)
    _sh(["ffmpeg", "-y", "-i", raw, "-i", overlay,
         "-filter_complex",
         f"[0:v]scale={W}:{H}:flags=lanczos,setsar=1,fps=30[v];"
         f"[v][1:v]overlay=0:0,fade=t=in:st=0:d=0.4,fade=t=out:st={fo:.2f}:d=0.4,format=yuv420p[vo]",
         "-map", "[vo]", "-map", "0:a",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-r", "30",
         "-af", "loudnorm=I=-14:TP=-1.5", "-movflags", "+faststart", out_path])
    for f in (raw, overlay):
        try:
            os.remove(f)
        except OSError:
            pass
    return out_path


def _is_date(s):
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def main():
    import argparse
    import sys
    from datetime import timezone
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import post_facebook as pf  # reuse story gathering
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--out", default="/tmp/cr_anchor.mp4")
    ap.add_argument("--resolution", default="720p", choices=["720p", "1080p"])
    a = ap.parse_args()
    target = a.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    stories, used = pf._stories_for(target, allow_fallback=True)
    if not stories:
        print("No stories.", file=sys.stderr)
        return
    out = build_anchor_recap(stories, used, a.out, resolution=a.resolution)
    print("ANCHOR VIDEO:", out, f"({len(stories[:MAX_STORIES])} stories, {used})")


if __name__ == "__main__":
    main()
