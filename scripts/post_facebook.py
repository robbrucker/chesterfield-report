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


def _stories_for(date_str: str) -> list:
    """(headline, url, recap) for stories published on date_str (YYYY-MM-DD).
    Falls back to the most recent day that has stories if date_str has none."""
    recs = render._published_records()
    by_day: dict[str, list] = {}
    for meta, body, name in recs:
        d = (meta.get("published") or "")[:10]
        if d:
            by_day.setdefault(d, []).append((meta, body, name))
    if date_str not in by_day and by_day:
        date_str = max(by_day)            # most recent day with stories
        print(f"(no stories for the requested day; using {date_str})", file=sys.stderr)
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


def _page_token(user_token: str) -> str:
    url = f"{GRAPH}/me/accounts?fields=id,access_token&access_token={urllib.parse.quote(user_token)}"
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.load(r)
    for p in data.get("data", []):
        if str(p.get("id")) == PAGE_ID:
            return p.get("access_token", "")
    raise SystemExit("Could not find the Chesterfield Report page token for this user token.")


def _post(message: str, page_token: str) -> dict:
    body = urllib.parse.urlencode({"message": message, "access_token": page_token}).encode()
    req = urllib.request.Request(f"{GRAPH}/{PAGE_ID}/feed", data=body, method="POST")
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


def main() -> None:
    import os
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    help="Day to recap (YYYY-MM-DD). Default: today (UTC).")
    ap.add_argument("--post", action="store_true", help="Actually publish (otherwise dry run).")
    ap.add_argument("--max", type=int, default=12, help="Cap number of stories.")
    args = ap.parse_args()

    stories, used_date = _stories_for(args.date)
    if not stories:
        print("No stories to recap.", file=sys.stderr)
        sys.exit(1)
    stories = stories[: args.max]
    message = _compose(stories, used_date)

    print("=" * 60)
    print(message)
    print("=" * 60)
    print(f"[{len(stories)} stories for {used_date}]", file=sys.stderr)

    if not args.post:
        print("DRY RUN. Re-run with --post to publish to the Page.", file=sys.stderr)
        return

    token = os.environ.get("FB_ACCESS_TOKEN", "").strip()
    if not token:
        sys.exit("FB_ACCESS_TOKEN not set (source scripts/.deploy.env).")
    result = _post(message, _page_token(token))
    print("Published. Post id:", result.get("id"), file=sys.stderr)


if __name__ == "__main__":
    main()
