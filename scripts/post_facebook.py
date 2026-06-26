#!/usr/bin/env python3
"""Daily Facebook recap for The Chesterfield Report.

Collects the stories published on a given day, writes a one-sentence recap for
each (via the Claude CLI, same as the rest of the pipeline), and composes a
single Facebook Page post that links each item back to the site.

DRY RUN BY DEFAULT: prints the post it would make and does nothing else. Pass
--post to actually publish to the Page.

    /usr/bin/python3 scripts/post_facebook.py              # preview today
    /usr/bin/python3 scripts/post_facebook.py --date 2026-06-19
    /usr/bin/python3 scripts/post_facebook.py --post       # publish today

Reads FB_ACCESS_TOKEN from the environment (source scripts/.deploy.env first).
The token is a user token that manages the Page; the script exchanges it for
the Page access token at runtime. Stdlib + the `claude` CLI only.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

# Import the site's render helpers (records, story URLs, dek extraction).
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from chesterfield import render  # noqa: E402
from chesterfield import translate  # noqa: E402

GRAPH = "https://graph.facebook.com/v21.0"
PAGE_ID = "1153985821132272"          # The Chesterfield Report
SITE = render.SITE_URL.rstrip("/")
MODEL = "claude-haiku-4-5"
CLI_TIMEOUT = 90

# UTM tags so the daily Facebook recap's clicks show up in analytics as an exact,
# named source (utm_source=fb_page) instead of a vague "facebook" lump or "direct"
# (the FB app often strips the referrer). Works for EN and ES story links alike.
_UTM = "utm_source=fb_page&utm_medium=social&utm_campaign=daily_recap"


def _utm(url: str) -> str:
    """Append the daily-recap UTM tags to a site URL."""
    if not url or "utm_source=" in url:
        return url
    return url + ("&" if "?" in url else "?") + _UTM

# Evergreen "house" posts for quiet days (no new stories). Rotated by date so the
# feed stays active and varied: the newsletter and the most useful pages.
_EVERGREEN = [
    ("Get Chesterfield news in your inbox. The Weekly Report is a free roundup of the "
     "week's county news and what's on the civic calendar. Sign up here:", "/subscribe.html"),
    ("Know exactly what's on your 2026 ballot. Our nonpartisan Voter Guide lets you enter "
     "your address and see your races, plus how and where to vote:", "/elections.html"),
    ("Who runs the Chesterfield County Police, where it is, what it costs, and the numbers "
     "behind it: officers, arrests, and traffic enforcement.", "/police.html"),
    ("Chesterfield Fire & EMS by the numbers: all 21 stations on a map, the budget, "
     "staffing, and how many emergencies they answer a year.", "/fire.html"),
    ("Shopping local? Here is every farmers market in Chesterfield County and the Richmond "
     "area, with days, hours, and what each one sells.", "/farmers-markets.html"),
    ("Meet your Board of Supervisors: what each one does for your district, and who funds "
     "their campaigns.", "/board.html"),
    ("Looking for something to do? Concerts, shows, family events, and games around "
     "Chesterfield and the Richmond region:", "/things-to-do.html"),
    ("Where do your county tax dollars actually go? A plain-language look at the "
     "Chesterfield County budget:", "/taxes.html"),
]


def _quiet_post(date_str: str) -> str:
    """A rotating evergreen post for days with no new stories."""
    try:
        idx = datetime.strptime(date_str, "%Y-%m-%d").toordinal() % len(_EVERGREEN)
    except ValueError:
        idx = 0
    text, link = _EVERGREEN[idx]
    return f"{text}\n\n{SITE}{link}"

_RECAP_SCHEMA = {
    "type": "object",
    "properties": {"recap": {"type": "string"}},
    "required": ["recap"],
    "additionalProperties": False,
}

_BANNED = ("nestled", "vibrant", "bustling", "hidden gem", "in the heart of",
           "look no further", "something for everyone", "tapestry", "delve",
           "testament", "boasts", "elevate", "curated")


def _first_sentence(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    for i, ch in enumerate(text):
        if ch in ".!?" and i > 20:
            return text[: i + 1].strip()
    return text


def _clean(s: str) -> str:
    return (s or "").replace("—", ", ").replace("–", "-").strip().strip('"')


def _have_cli() -> bool:
    import shutil
    return shutil.which("claude") is not None


_META_STARTS = ("wrote ", "rewrote", "rewrite", "rewriting", "rewritten", "here ",
                "here's", "here is", "sure", "i wrote", "i've", "this is", "the following",
                "okay", "ok,", "certainly", "a factual", "a single", "a one", "below ")
_META_CONTAINS = ("recap sentence", "facebook", "daily-recap", "one-sentence",
                  "one sentence", "word sentence", "suitable for", "as a single",
                  "the local news summary", "local news summary", "for a chesterfield county")


def _looks_meta(s: str) -> bool:
    low = (s or "").strip().lower()
    if not low or len(low) > 240:
        return True
    if low.startswith(_META_STARTS):
        return True
    return any(p in low for p in _META_CONTAINS)


def _ai_recap(headline: str, dek: str) -> str:
    """One plain, factual sentence recapping the story for a Facebook post."""
    if not _have_cli():
        return ""
    prompt = (
        "Rewrite the following local news summary as ONE short, plain sentence (about 12 "
        "to 22 words) for a Facebook daily news recap.\n\n"
        f'Story summary: "{dek or headline}"\n\n'
        "Output requirements:\n"
        "- Return ONLY the rewritten sentence. No preamble, no quotation marks, no labels.\n"
        "- Never write phrases like \"Here is\", \"Wrote a sentence\", or describe the task.\n"
        "- Factual and neutral. No hype, no clickbait, no first person, no hashtags, no emoji.\n"
        "- Base it only on the summary; invent nothing.\n"
        "- NO em dashes or en dashes (use commas and periods). Avoid the words: "
        + ", ".join(_BANNED) + ".\n"
        "Example of the EXACT format to return: VDOT has stopped trimming roadside "
        "overgrowth near a disabled veteran's Chesterfield home, leaving upkeep the family "
        "says it cannot afford."
    )
    cmd = ["claude", "-p", prompt, "--output-format", "json",
           "--json-schema", json.dumps(_RECAP_SCHEMA), "--model", MODEL]
    for attempt in range(2):
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=CLI_TIMEOUT)
            if proc.returncode != 0:
                if attempt == 0:
                    time.sleep(4)
                    continue
                return ""
            data = json.loads(proc.stdout).get("structured_output") or {}
            recap = _clean(data.get("recap", ""))
            return "" if _looks_meta(recap) else recap
        except Exception:  # noqa: BLE001
            if attempt == 0:
                time.sleep(4)
                continue
            return ""
    return ""


STATE_FILE = ROOT / "scripts" / ".fb_posted"  # gitignored; last posted day


def _stories_for(date_str: str, allow_fallback: bool = True) -> tuple:
    """(headline, url, recap) for stories published on date_str (YYYY-MM-DD).
    With allow_fallback, uses the most recent day that has stories when date_str
    itself has none; otherwise returns an empty list for that day."""
    recs = render._published_records()
    by_day: dict[str, list] = {}
    for meta, body, name in recs:
        d = (meta.get("published") or "")[:10]
        if d:
            by_day.setdefault(d, []).append((meta, body, name))
    if date_str not in by_day:
        if allow_fallback and by_day:
            date_str = max(by_day)        # most recent day with stories
            print(f"(no stories for the requested day; using {date_str})", file=sys.stderr)
        else:
            return [], date_str
    out = []
    for meta, body, name in by_day.get(date_str, []):
        headline = (meta.get("headline") or name).strip()
        url = _utm(SITE + render.story_url(headline))
        dek = render._tldr_from_body(body) or ""
        recap = _ai_recap(headline, dek) or _first_sentence(dek) or headline
        out.append((headline, url, recap))
    return out, date_str


_DEDUPE_STOP = set(
    "the a an and or of for to in on at by with from as is are was were be been this that it its "
    "has have had will would can could not new chesterfield county report virginia local news your "
    "you who what when where after over into about more most than then they their them his her".split())


def _dedupe_sig(text: str) -> set:
    return {w for w in re.findall(r"[a-z][a-z'\-]{2,}", (text or "").lower())
            if w not in _DEDUPE_STOP and len(w) >= 4}


def _dedupe_stories(stories: list, thresh: float = 0.5) -> list:
    """Drop near-duplicate stories (e.g. three separate write-ups of the same
    appointment) so the recap doesn't say the same thing five times. Keeps the
    first (highest-ranked) of each cluster, comparing significant-word overlap of
    headline + recap."""
    kept, sets = [], []
    for h, u, r in stories:
        sig = _dedupe_sig(f"{h} {r or ''}")
        is_dup = any(
            sig and ks and len(sig & ks) >= 2
            and len(sig & ks) / min(len(sig), len(ks)) >= thresh
            for ks in sets)
        if not is_dup:
            kept.append((h, u, r))
            sets.append(sig)
    return kept


def _nice_date(date_str: str) -> str:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%A, %B %-d, %Y")
    except ValueError:
        return date_str


def _compose_block(stories: list, header: str, footer: str) -> str:
    """Build one language block from (recap, url) pairs plus a header/footer.
    Shared by the English and Spanish composers so both stay in lockstep."""
    lines = [header, ""]
    for recap, url in stories:
        lines.append(f"• {recap}")
        lines.append(url)
        lines.append("")
    lines.append(footer)
    return "\n".join(lines).strip()


def _compose(stories: list, date_str: str) -> str:
    nice = _nice_date(date_str)
    pairs = [(recap, url) for headline, url, recap in stories]
    return _compose_block(
        pairs,
        f"Today in Chesterfield, {nice}",
        f"More local news, every day, at {SITE.replace('https://', '')}",
    )


# Separator placed between the English and Spanish blocks in a bilingual post.
_BILINGUAL_SEP = "\n\n· · ·\n\nEn espanol\n\n"


def _es_url(url: str) -> str:
    """Point a story URL at its Spanish (/es/) version; leave non-story URLs as-is."""
    return url.replace(
        "chesterfieldreport.com/story/", "chesterfieldreport.com/es/story/")


def _compose_bilingual(stories: list, date_str: str) -> str:
    """English block, separator, then a Spanish block. Recap sentences are
    translated via the project translator; story URLs swap to their /es/ pages."""
    english = _compose(stories, date_str)

    recaps = [recap for headline, url, recap in stories]
    es_map = translate.translate_strings(recaps) if recaps else {}
    es_pairs = [(es_map.get(recap, recap), _es_url(url))
                for headline, url, recap in stories]

    nice = _nice_date(date_str)
    spanish = _compose_block(
        es_pairs,
        f"Hoy en Chesterfield, {nice}",
        f"Mas noticias locales, todos los dias, en {SITE.replace('https://', '')}",
    )
    return english + _BILINGUAL_SEP + spanish


def _token_ok(token: str) -> bool:
    """Cheap validity check: a valid token (user OR page) answers /me; an expired
    or missing one errors. Lets an expired token fail before the costly compose."""
    if not token:
        return False
    try:
        url = f"{GRAPH}/me?access_token={urllib.parse.quote(token)}"
        with urllib.request.urlopen(url, timeout=20) as r:
            json.load(r)
        return True
    except Exception:
        return False


def _resolve_page_token(token: str) -> str:
    """Accept either a user token (exchange it for the Page token via /me/accounts)
    or a Page token pasted directly (use it as-is). No app secret needed."""
    try:
        url = f"{GRAPH}/me/accounts?fields=id,access_token&access_token={urllib.parse.quote(token)}"
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.load(r)
        for p in data.get("data", []):
            if str(p.get("id")) == PAGE_ID and p.get("access_token"):
                return p["access_token"]
    except Exception:
        pass
    return token  # assume the token is already the Page token


def _post(message: str, page_token: str) -> dict:
    body = urllib.parse.urlencode({"message": message, "access_token": page_token}).encode()
    req = urllib.request.Request(f"{GRAPH}/{PAGE_ID}/feed", data=body, method="POST")
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


def _post_video(path: str, message: str, page_token: str) -> dict:
    """Upload the recap video to the Page with the recap text as its description.
    Uses curl for the multipart upload (simple + reliable for a small MP4)."""
    out = subprocess.check_output([
        "curl", "-s", "-X", "POST", f"{GRAPH}/{PAGE_ID}/videos",
        "-F", f"access_token={page_token}",
        "-F", f"description={message}",
        "-F", f"source=@{path}",
    ], timeout=300)
    return json.loads(out.decode("utf-8") or "{}")


def _post_video_story(path: str, page_token: str) -> dict:
    """Publish a vertical video as a Facebook Page Story (3-phase upload).
    start -> binary upload to the returned rupload URL (curl) -> finish."""
    start = subprocess.check_output([
        "curl", "-s", "-X", "POST", f"{GRAPH}/{PAGE_ID}/video_stories",
        "-F", "upload_phase=start", "-F", f"access_token={page_token}",
    ], timeout=60)
    s = json.loads(start.decode("utf-8") or "{}")
    video_id, upload_url = s.get("video_id"), s.get("upload_url")
    if not video_id or not upload_url:
        raise RuntimeError(f"story start failed: {s}")
    size = os.path.getsize(path)
    up = subprocess.check_output([
        "curl", "-s", "-X", "POST", upload_url,
        "-H", f"Authorization: OAuth {page_token}",
        "-H", "offset: 0", "-H", f"file_size: {size}",
        "--data-binary", f"@{path}",
    ], timeout=300)
    u = json.loads(up.decode("utf-8") or "{}")
    if not u.get("success", True) and "error" in u:
        raise RuntimeError(f"story upload failed: {u}")
    fin = subprocess.check_output([
        "curl", "-s", "-X", "POST", f"{GRAPH}/{PAGE_ID}/video_stories",
        "-F", "upload_phase=finish", "-F", f"video_id={video_id}",
        "-F", f"access_token={page_token}",
    ], timeout=120)
    return json.loads(fin.decode("utf-8") or "{}")


def _make_video(stories, used_date):
    """Daily video is intentionally OFF.

    We moved to an "explainer-first" video strategy (real map/satellite + data
    supers + vd2 voiceover) for the meaty, place/data-driven stories, produced a
    few times a week via scripts/make_explainer.py -- not a rote daily anchor read.
    The daily Facebook post stays text-only here; explainers are posted on their own.
    The AI anchor pipeline (make_anchor_recap.py) is kept but no longer auto-runs."""
    return None


def main() -> None:
    import os
    ap = argparse.ArgumentParser()
    ap.add_argument("--tz", default="America/New_York", help="Timezone for 'today' and --at-hour.")
    ap.add_argument("--date", default=None,
                    help="Day to recap (YYYY-MM-DD). Default: today in --tz.")
    ap.add_argument("--post", action="store_true", help="Actually publish (otherwise dry run).")
    ap.add_argument("--max", type=int, default=12, help="Cap number of stories.")
    ap.add_argument("--at-hour", type=int, default=None,
                    help="Only proceed if the current hour in --tz equals this (for cron gating).")
    ap.add_argument("--no-fallback", action="store_true",
                    help="Only post the exact target day; skip (exit 0) if it has no stories.")
    ap.add_argument("--skip-if-posted", action="store_true",
                    help="Skip (exit 0) if a recap for the target day already went out.")
    ap.add_argument("--quiet-fallback", action="store_true",
                    help="On a day with no new stories, post a rotating evergreen house "
                         "post (newsletter / a key page) instead of skipping.")
    ap.add_argument("--bilingual", action="store_true",
                    help="Append a full Spanish translation (with /es/ story links) below "
                         "the English recap, for copy-pasting to a Spanish Facebook page.")
    args = ap.parse_args()

    tz = ZoneInfo(args.tz)
    now = datetime.now(tz)
    # Cron gate: bail quietly unless it's the intended local hour.
    if args.at_hour is not None and now.hour != args.at_hour:
        return
    target = args.date or now.strftime("%Y-%m-%d")

    if args.skip_if_posted and args.post and STATE_FILE.exists():
        if STATE_FILE.read_text(encoding="utf-8").strip() == target:
            print(f"Already posted a recap for {target}; skipping.", file=sys.stderr)
            return

    # In --post mode, validate the token BEFORE the costly AI compose so an
    # expired/missing token fails cheaply. The cron auto-resumes the moment a
    # working token is dropped into scripts/.deploy.env -- no other setup.
    token = ""
    if args.post:
        token = os.environ.get("FB_ACCESS_TOKEN", "").strip()
        if not _token_ok(token):
            print("Facebook token is missing or expired; skipping post. Refresh "
                  "FB_ACCESS_TOKEN in scripts/.deploy.env (a fresh token is enough; "
                  "no app secret needed). The daily post resumes automatically once "
                  "a valid token is in place.", file=sys.stderr)
            return

    # Today's stories only when quiet-fallback is on (we post evergreen instead of
    # recapping old days). Otherwise honor --no-fallback as before.
    allow_fb = (not args.no_fallback) and (not args.quiet_fallback)
    stories, used_date = _stories_for(target, allow_fallback=allow_fb)
    if stories:
        stories = _dedupe_stories(stories)[: args.max]
        message = (_compose_bilingual(stories, used_date) if args.bilingual
                   else _compose(stories, used_date))
    elif args.quiet_fallback:
        stories = []                       # signals: evergreen post, no video
        used_date = target
        message = _quiet_post(target)
        print(f"No new stories for {target}; posting evergreen house content.", file=sys.stderr)
    else:
        print(f"No stories to recap for {target}; skipping.", file=sys.stderr)
        return

    print("=" * 60)
    print(message)
    print("=" * 60)
    print(f"[{len(stories)} stories for {used_date}]", file=sys.stderr)

    if not args.post:
        print("DRY RUN. Re-run with --post to publish to the Page.", file=sys.stderr)
        return

    page_token = _resolve_page_token(token)
    # Render the recap video and post it WITH the recap text as the description.
    # Fall back to a text-only post if the video can't be made or uploaded.
    video = _make_video(stories, used_date)
    try:
        if video and os.path.exists(video):
            result = _post_video(video, message, page_token)
            kind = "video"
        else:
            result = _post(message, page_token)
            kind = "text"
    except Exception as e:
        # If a video upload failed, try once more as a text post so the day isn't missed.
        print(f"Facebook {('video' if video else 'text')} post failed ({e}); trying text.",
              file=sys.stderr)
        try:
            result = _post(message, page_token)
            kind = "text (fallback)"
        except Exception as e2:
            print(f"Facebook post failed ({e2}); not marked as posted, will retry next run.",
                  file=sys.stderr)
            return
    pid = (result.get("id") or result.get("post_id")) if isinstance(result, dict) else None
    if not pid:
        print(f"Facebook post returned no id: {result}", file=sys.stderr)
        return
    print(f"Published ({kind}). Id:", pid, file=sys.stderr)

    # Also publish the vertical anchor video as a Page Story (best-effort; a
    # story failure never undoes the feed post or blocks marking the day done).
    if video and os.path.exists(video) and kind.startswith("video"):
        try:
            sres = _post_video_story(video, page_token)
            spid = sres.get("post_id") or sres.get("id") or sres.get("success")
            print("Story published:", spid, file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"Story post failed ({e}); feed post still stands.", file=sys.stderr)

    try:
        STATE_FILE.write_text(used_date, encoding="utf-8")
    except OSError:
        pass


if __name__ == "__main__":
    main()
