"""Daily Chesterfield Report recap VIDEO (vertical 1080x1920, for Facebook/Reels/TikTok).

Builds branded cards (heron logo on the brand gradient) + an ElevenLabs voiceover
(the "Chesterfield Piedmont Anchor" voice) and assembles them into an MP4 with ffmpeg.
Reuses the day's stories gathered by post_facebook.py. Runs on the VPS.

Env (from scripts/.deploy.env): ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID.
Tools required on the host: ffmpeg, ffprobe, ImageMagick (convert), rsvg-convert.

CLI:  /usr/bin/python3 scripts/make_recap_video.py [--date YYYY-MM-DD] [--out /tmp/recap.mp4]
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGO_SVG = ROOT / "public" / "assets" / "logo-mark.svg"
# DejaVu ships with fonts-dejavu-core on Debian/Ubuntu.
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
W, H = 1080, 1920
EL_MODEL = "eleven_turbo_v2_5"
GRAD = "gradient:#0f3a47-#06141b"


def _sh(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _prep(t):
    _sh(["convert", "-size", f"{W}x{H}", GRAD, f"{t}/bg.png"])
    _sh(["rsvg-convert", "-w", "420", "-h", "420", str(LOGO_SVG), "-o", f"{t}/logo.png"])


def _card_story(t, out, kicker, headline):
    _sh(["convert", f"{t}/bg.png",
         "(", f"{t}/logo.png", "-resize", "150x150", ")", "-gravity", "North", "-geometry", "+0+130", "-composite",
         "-gravity", "North", "-font", SANS_B, "-pointsize", "42", "-fill", "#5ef0db", "-annotate", "+0+322", kicker,
         "(", "-size", "880x650", "-background", "none", "-fill", "#eef6f4", "-font", SERIF, "-gravity", "center",
         f"caption:{headline}", ")", "-gravity", "Center", "-geometry", "+0+10", "-composite",
         "-gravity", "South", "-font", SERIF, "-pointsize", "44", "-fill", "#9fc9c2", "-annotate", "+0+140",
         "chesterfieldreport.com", out])


def _card_bookend(t, out, big, small):
    _sh(["convert", f"{t}/bg.png",
         "(", f"{t}/logo.png", "-resize", "300x300", ")", "-gravity", "Center", "-geometry", "+0-260", "-composite",
         "(", "-size", "900x300", "-background", "none", "-fill", "#eef6f4", "-font", SERIF, "-gravity", "center",
         f"caption:{big}", ")", "-gravity", "Center", "-geometry", "+0+60", "-composite",
         "-gravity", "Center", "-font", SANS_B, "-pointsize", "44", "-fill", "#9fc9c2", "-annotate", "+0+190", small,
         out])


def _tts(text, out):
    key = os.environ["ELEVENLABS_API_KEY"]
    voice = os.environ.get("ELEVENLABS_VOICE_ID", "")
    body = json.dumps({"text": text, "model_id": EL_MODEL,
                       "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "style": 0.2}}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
        data=body, headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    with urllib.request.urlopen(req, timeout=90) as r:
        open(out, "wb").write(r.read())


def _dur(f):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]).strip())


def build_recap_video(stories, date_str, out_path, max_stories=5):
    """stories = [(headline, url, recap), ...]. Returns out_path, or None on no stories.
    Raises on tooling/API errors so the caller can fall back to a text post."""
    if not stories:
        return None
    stories = stories[:max_stories]
    try:
        nice = datetime.strptime(date_str, "%Y-%m-%d").strftime("%A, %B %-d")
    except ValueError:
        nice = date_str
    with tempfile.TemporaryDirectory() as t:
        _prep(t)
        segs = []  # (card_png, voiceover_text)
        _card_bookend(t, f"{t}/sin.png", "The Chesterfield Report", f"Daily recap · {nice}")
        segs.append((f"{t}/sin.png", f"Today in Chesterfield. Your local news recap for {nice}."))
        for i, (headline, _url, recap) in enumerate(stories):
            _card_story(t, f"{t}/s{i}.png", "TODAY IN CHESTERFIELD", headline)
            segs.append((f"{t}/s{i}.png", recap))
        _card_bookend(t, f"{t}/sout.png", "Follow us", "chesterfieldreport.com")
        segs.append((f"{t}/sout.png",
                     "Get more local news every day at Chesterfield Report dot com. Follow us for the latest."))
        listf = f"{t}/list.txt"
        open(listf, "w").close()
        for j, (card, text) in enumerate(segs):
            _tts(text, f"{t}/a{j}.mp3")
            T = f"{_dur(f'{t}/a{j}.mp3') + 0.6:.2f}"
            _sh(["ffmpeg", "-y", "-loop", "1", "-i", card, "-i", f"{t}/a{j}.mp3",
                 "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k",
                 "-pix_fmt", "yuv420p", "-r", "30", "-vf", f"scale={W}:{H}", "-t", T, f"{t}/c{j}.mp4"])
            open(listf, "a").write(f"file '{t}/c{j}.mp4'\n")
        _sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listf,
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
             "-af", "loudnorm=I=-14:TP=-1.5", "-movflags", "+faststart", out_path])
    return out_path


def main():
    import argparse
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import post_facebook as pf  # reuse story gathering
    from datetime import timezone
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--out", default="/tmp/recap.mp4")
    a = ap.parse_args()
    target = a.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    stories, used = pf._stories_for(target, allow_fallback=True)
    if not stories:
        print("No stories.", file=sys.stderr)
        return
    out = build_recap_video(stories, used, a.out)
    print("VIDEO:", out, f"({len(stories[:5])} stories, {used})")


if __name__ == "__main__":
    main()
