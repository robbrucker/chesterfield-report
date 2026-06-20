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

GRAPH = "https://graph.facebook.com/v21.0"
PAGE_ID = "1153985821132272"          # The Chesterfield Report
SITE = render.SITE_URL.rstrip("/")
MODEL = "claude-haiku-4-5"
CLI_TIMEOUT = 90

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
        url = SITE + render.story_url(headline)
        dek = render._tldr_from_body(body) or ""
        recap = _ai_recap(headline, dek) or _first_sentence(dek) or headline
        out.append((headline, url, recap))
    return out, date_str


def _compose(stories: list, date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        nice = dt.strftime("%A, %B %-d, %Y")
    except ValueError:
        nice = date_str
    lines = [f"Today in Chesterfield, {nice}", ""]
    for headline, url, recap in stories:
        lines.append(f"• {recap}")
        lines.append(url)
        lines.append("")
    lines.append(f"More local news, every day, at {SITE.replace('https://', '')}")
    return "\n".join(lines).strip()


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

    stories, used_date = _stories_for(target, allow_fallback=not args.no_fallback)
    if not stories:
        print(f"No stories to recap for {target}; skipping.", file=sys.stderr)
        return
    stories = stories[: args.max]
    message = _compose(stories, used_date)

    print("=" * 60)
    print(message)
    print("=" * 60)
    print(f"[{len(stories)} stories for {used_date}]", file=sys.stderr)

    if not args.post:
        print("DRY RUN. Re-run with --post to publish to the Page.", file=sys.stderr)
        return

    try:
        result = _post(message, _resolve_page_token(token))
    except Exception as e:
        print(f"Facebook post failed ({e}); not marked as posted, will retry next run.",
              file=sys.stderr)
        return
    pid = result.get("id") if isinstance(result, dict) else None
    if not pid:
        print(f"Facebook post returned no post id: {result}", file=sys.stderr)
        return
    print("Published. Post id:", pid, file=sys.stderr)
    try:
        STATE_FILE.write_text(used_date, encoding="utf-8")
    except OSError:
        pass


if __name__ == "__main__":
    main()
