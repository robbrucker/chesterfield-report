"""Email newsletter generator for *The Chesterfield Report*.

Builds an email-client-safe HTML newsletter (tables + inline styles only, no
external CSS/JS) plus a plaintext version from the weekly digest on disk, and
optionally sends it via Resend or SMTP.

This module is intentionally self-contained: it reads ``public/digest.md`` (and
optionally ``content/published/*.md``) directly from disk and does **not**
import any other module in the package (``render``, ``enrich``, …) so it can run
safely alongside other tools editing those files.

Stdlib only.

Public API
----------
- ``build(out="public/newsletter.html") -> Path``
- ``send(to_addrs, subject=None) -> None``
"""

from __future__ import annotations

import json
import os
import re
import smtplib
import sys
import urllib.error
import urllib.request
from datetime import date, datetime
from email.message import EmailMessage
from html import escape
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths & constants
# --------------------------------------------------------------------------- #

# Project root is two levels up from this file: pipeline/chesterfield/newsletter.py
ROOT = Path(__file__).resolve().parents[2]
DIGEST_PATH = ROOT / "public" / "digest.md"
PUBLISHED_DIR = ROOT / "content" / "published"

SITE = "https://chesterfieldreport.com"
BRAND = "The Chesterfield Report"
TAGLINE = "Hyperlocal news for Chesterfield County, Virginia"

FROM_ADDR = os.environ.get("NEWSLETTER_FROM", "news@chesterfieldreport.com")
FROM_NAME = "The Chesterfield Report"

# Palette
TEAL = "#003e51"
TEAL_DARK = "#002b39"
INK = "#1d2733"
MUTED = "#5b6b78"
RULE = "#e2e7ea"
BG = "#eef1f3"
ACCENT = "#0d7b8a"


# --------------------------------------------------------------------------- #
# Slug — mirrors render.slugify so links match homepage anchors exactly.
# (Copied, not imported, on purpose.)
# --------------------------------------------------------------------------- #

def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-") or "x"


def story_url(headline: str) -> str:
    return f"{SITE}/story/{slugify(headline)}.html"


# --------------------------------------------------------------------------- #
# Parsing the digest
# --------------------------------------------------------------------------- #

class Item:
    __slots__ = ("headline", "tldr")

    def __init__(self, headline: str, tldr: str):
        self.headline = headline
        self.tldr = tldr


class Section:
    __slots__ = ("title", "items")

    def __init__(self, title: str):
        self.title = title
        self.items = []  # list[Item]


# matches:  - **Headline** — TL;DR   (em dash, en dash, or hyphen separators)
_BULLET_RE = re.compile(
    r"^\s*[-*]\s+\*\*(?P<head>.+?)\*\*\s*(?:[—–-]\s*(?P<tldr>.*))?$"
)
_COUNT_RE = re.compile(r"_(?P<n>\d+)\s+stor", re.IGNORECASE)
_GEN_RE = re.compile(r"generated\s+(?P<date>\d{4}-\d{2}-\d{2})", re.IGNORECASE)


def parse_digest(text: str):
    """Parse the digest markdown.

    Returns ``(title, meta, sections)`` where ``meta`` carries ``count`` and
    ``generated`` (a ``date`` or ``None``) and ``sections`` is a list of
    :class:`Section`.
    """
    title = "This Week in Chesterfield"
    meta = {"count": None, "generated": None}
    sections: list[Section] = []
    current: Section | None = None

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("# "):
            title = line[2:].strip()
            continue
        if line.startswith("## "):
            current = Section(line[3:].strip())
            sections.append(current)
            continue

        if meta["count"] is None:
            m = _COUNT_RE.search(line)
            if m:
                meta["count"] = int(m.group("n"))
        if meta["generated"] is None:
            m = _GEN_RE.search(line)
            if m:
                try:
                    meta["generated"] = datetime.strptime(
                        m.group("date"), "%Y-%m-%d"
                    ).date()
                except ValueError:
                    pass

        m = _BULLET_RE.match(line)
        if m:
            if current is None:
                current = Section("This Week")
                sections.append(current)
            head = m.group("head").strip()
            tldr = (m.group("tldr") or "").strip()
            current.items.append(Item(head, tldr))

    # Drop any empty sections.
    sections = [s for s in sections if s.items]
    return title, meta, sections


# --------------------------------------------------------------------------- #
# Fallback: build sections from content/published/*.md frontmatter
# --------------------------------------------------------------------------- #

def _parse_frontmatter(text: str) -> dict:
    """Minimal YAML-ish frontmatter parser (key: value, simple lists)."""
    out: dict = {}
    if not text.startswith("---"):
        return out
    end = text.find("\n---", 3)
    if end == -1:
        return out
    block = text[3:end]
    for line in block.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1]
            out[key] = [v.strip().strip('"\'') for v in inner.split(",") if v.strip()]
        else:
            out[key] = val.strip('"\'')
    return out


def sections_from_published(limit_days: int = 9):
    """Build sections grouped by focus area from recently published stories.

    Used only when ``public/digest.md`` is missing. Returns
    ``(meta, sections)`` shaped like :func:`parse_digest` output.
    """
    sections: dict[str, Section] = {}
    order: list[str] = []
    dates: list[date] = []
    count = 0

    if not PUBLISHED_DIR.is_dir():
        return {"count": 0, "generated": None, "range": None}, []

    files = sorted(PUBLISHED_DIR.glob("*.md"), reverse=True)
    for fp in files:
        try:
            text = fp.read_text(encoding="utf-8")
        except OSError:
            continue
        fm = _parse_frontmatter(text)
        headline = fm.get("headline") or ""
        if not headline:
            continue

        # Derive a TL;DR: first non-heading, non-empty body paragraph.
        body = text.split("\n---", 1)[-1]
        tldr = ""
        for para in body.split("\n\n"):
            p = para.strip()
            if not p or p.startswith("#") or p.startswith("!["):
                continue
            tldr = re.sub(r"\s+", " ", p)[:280]
            break

        focus = fm.get("focus")
        if isinstance(focus, list) and focus:
            label = focus[0]
        elif isinstance(focus, str) and focus:
            label = focus.strip("[]").split(",")[0].strip()
        else:
            label = "Local News"

        pub = fm.get("published", "")
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", pub or "")
        if not m:
            m = re.match(r"(\d{4})-(\d{2})-(\d{2})", fp.name)
        if m:
            try:
                dates.append(date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
            except ValueError:
                pass

        if label not in sections:
            sections[label] = Section(label)
            order.append(label)
        sections[label].items.append(Item(headline, tldr))
        count += 1

    rng = None
    gen = None
    if dates:
        dates.sort()
        rng = (dates[0], dates[-1])
        gen = dates[-1]

    ordered = [sections[k] for k in order if sections[k].items]
    return {"count": count, "generated": gen, "range": rng}, ordered


# --------------------------------------------------------------------------- #
# Date range helpers
# --------------------------------------------------------------------------- #

def _date_range(meta: dict):
    """Return (start_date, end_date) best-effort for the issue header."""
    rng = meta.get("range")
    if rng:
        return rng
    gen = meta.get("generated") or date.today()
    # Treat the digest as covering the trailing week ending on the gen date.
    from datetime import timedelta
    return gen - timedelta(days=6), gen


def _fmt_range(start: date, end: date) -> str:
    if start == end:
        return start.strftime("%B %-d, %Y") if _supports_dash() else start.strftime("%B %d, %Y").replace(" 0", " ")
    if start.year == end.year and start.month == end.month:
        s = start.strftime("%B %d").replace(" 0", " ")
        e = end.strftime("%d, %Y").lstrip("0")
        return f"{s}–{e}"
    s = start.strftime("%B %d").replace(" 0", " ")
    e = end.strftime("%B %d, %Y").replace(" 0", " ")
    return f"{s} – {e}"


def _supports_dash() -> bool:
    try:
        date.today().strftime("%-d")
        return True
    except ValueError:
        return False


# --------------------------------------------------------------------------- #
# HTML rendering (email-client-safe: tables + inline styles only)
# --------------------------------------------------------------------------- #

def _render_html(title: str, meta: dict, sections, range_label: str) -> str:
    count = meta.get("count")
    if count is None:
        count = sum(len(s.items) for s in sections)
    count_label = f"{count} {'story' if count == 1 else 'stories'} this week"

    # Section blocks
    body_rows = []
    if not sections:
        body_rows.append(
            f'<tr><td style="padding:28px 32px;font-family:Arial,Helvetica,sans-serif;'
            f'font-size:15px;line-height:1.6;color:{MUTED};">'
            f"No stories to report this week. Check back soon, or visit "
            f'<a href="{SITE}" style="color:{ACCENT};text-decoration:none;font-weight:bold;">'
            f"chesterfieldreport.com</a> for the latest.</td></tr>"
        )
    else:
        for sec in sections:
            body_rows.append(_render_section(sec))

    sections_html = "\n".join(body_rows)
    year = date.today().year

    return f"""<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="x-apple-disable-message-reformatting">
<title>{escape(BRAND)} — {escape(range_label)}</title>
<!--[if mso]><style>table,td,div,p,a{{font-family:Arial,Helvetica,sans-serif !important;}}</style><![endif]-->
</head>
<body style="margin:0;padding:0;background-color:{BG};-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;">
<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;font-size:1px;line-height:1px;color:{BG};">
{escape(TAGLINE)} — {escape(range_label)}: {escape(count_label)}.
</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:{BG};">
<tr><td align="center" style="padding:24px 12px;">

<table role="presentation" width="640" cellpadding="0" cellspacing="0" border="0" style="width:640px;max-width:640px;background-color:#ffffff;border-radius:10px;overflow:hidden;border:1px solid {RULE};">

  <!-- Header bar -->
  <tr>
    <td style="background-color:{TEAL};padding:30px 32px 26px 32px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr><td style="font-family:Georgia,'Times New Roman',Times,serif;font-size:30px;line-height:1.15;font-weight:bold;color:#ffffff;letter-spacing:0.3px;">{escape(BRAND)}</td></tr>
        <tr><td style="padding-top:8px;font-family:Arial,Helvetica,sans-serif;font-size:13px;line-height:1.5;color:#bcd6dd;">{escape(TAGLINE)}</td></tr>
      </table>
    </td>
  </tr>

  <!-- Issue meta strip -->
  <tr>
    <td style="background-color:{TEAL_DARK};padding:11px 32px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="font-family:Arial,Helvetica,sans-serif;font-size:12px;line-height:1.4;color:#9fc2cb;text-transform:uppercase;letter-spacing:1px;">{escape(range_label)}</td>
          <td align="right" style="font-family:Arial,Helvetica,sans-serif;font-size:12px;line-height:1.4;color:#9fc2cb;text-transform:uppercase;letter-spacing:1px;">{escape(count_label)}</td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- Intro -->
  <tr>
    <td style="padding:26px 32px 4px 32px;">
      <p style="margin:0;font-family:Georgia,'Times New Roman',Times,serif;font-size:20px;line-height:1.35;color:{INK};font-weight:bold;">{escape(title)}</p>
      <p style="margin:8px 0 0 0;font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.6;color:{MUTED};">Here's what mattered in Chesterfield County this week — the headlines, in brief. Tap any story to read the full report.</p>
    </td>
  </tr>

  <!-- Sections -->
{sections_html}

  <!-- CTA -->
  <tr>
    <td style="padding:8px 32px 30px 32px;">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="margin:0 auto;">
        <tr><td align="center" bgcolor="{ACCENT}" style="border-radius:6px;">
          <a href="{SITE}" style="display:inline-block;padding:13px 30px;font-family:Arial,Helvetica,sans-serif;font-size:15px;font-weight:bold;color:#ffffff;text-decoration:none;border-radius:6px;">Read all the news &rarr;</a>
        </td></tr>
      </table>
    </td>
  </tr>

  <!-- Footer -->
  <tr>
    <td style="background-color:#f5f7f8;border-top:1px solid {RULE};padding:24px 32px;">
      <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:12px;line-height:1.6;color:{MUTED};">
        <strong style="color:{INK};">{escape(BRAND)}</strong><br>
        {escape(TAGLINE)}<br>
        <a href="{SITE}" style="color:{ACCENT};text-decoration:none;">{escape(SITE.replace('https://', ''))}</a>
      </p>
      <p style="margin:14px 0 0 0;font-family:Arial,Helvetica,sans-serif;font-size:11px;line-height:1.6;color:#8a99a4;">
        You're receiving this because you subscribed to {escape(BRAND)}.<br>
        <a href="{{{{unsubscribe_url}}}}" style="color:#8a99a4;text-decoration:underline;">Unsubscribe</a>
        &nbsp;&middot;&nbsp;
        <a href="{SITE}" style="color:#8a99a4;text-decoration:underline;">View on the web</a>
      </p>
      <p style="margin:12px 0 0 0;font-family:Arial,Helvetica,sans-serif;font-size:11px;line-height:1.5;color:#b3bdc4;">&copy; {year} {escape(BRAND)}</p>
    </td>
  </tr>

</table>

</td></tr>
</table>
</body>
</html>"""


def _render_section(sec: Section) -> str:
    item_rows = []
    for it in sec.items:
        url = story_url(it.headline)
        tldr_html = ""
        if it.tldr:
            tldr_html = (
                f'<p style="margin:5px 0 0 0;font-family:Arial,Helvetica,sans-serif;'
                f'font-size:14px;line-height:1.6;color:{MUTED};">{escape(it.tldr)}</p>'
            )
        item_rows.append(
            f'<tr><td style="padding:14px 0;border-bottom:1px solid {RULE};">'
            f'<a href="{escape(url)}" style="font-family:Georgia,\'Times New Roman\',Times,serif;'
            f'font-size:17px;line-height:1.35;font-weight:bold;color:{INK};text-decoration:none;">'
            f"{escape(it.headline)}</a>"
            f"{tldr_html}"
            f"</td></tr>"
        )
    items_html = "\n".join(item_rows)

    return f"""  <tr>
    <td style="padding:22px 32px 0 32px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr><td style="padding-bottom:2px;">
          <span style="display:inline-block;font-family:Arial,Helvetica,sans-serif;font-size:12px;font-weight:bold;letter-spacing:1.5px;text-transform:uppercase;color:#ffffff;background-color:{TEAL};padding:5px 12px;border-radius:3px;">{escape(sec.title)}</span>
        </td></tr>
        <tr><td>
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:6px;">
{items_html}
          </table>
        </td></tr>
      </table>
    </td>
  </tr>"""


# --------------------------------------------------------------------------- #
# Plaintext rendering
# --------------------------------------------------------------------------- #

def _render_text(title: str, meta: dict, sections, range_label: str) -> str:
    count = meta.get("count")
    if count is None:
        count = sum(len(s.items) for s in sections)
    lines = []
    lines.append(BRAND.upper())
    lines.append(TAGLINE)
    lines.append("=" * 60)
    lines.append(f"{range_label}  |  {count} {'story' if count == 1 else 'stories'}")
    lines.append("")
    lines.append(title)
    lines.append("")

    if not sections:
        lines.append("No stories to report this week.")
        lines.append(f"Visit {SITE} for the latest.")
    else:
        for sec in sections:
            lines.append(f"## {sec.title.upper()}")
            lines.append("-" * 60)
            for it in sec.items:
                lines.append(f"* {it.headline}")
                if it.tldr:
                    lines.append(f"  {it.tldr}")
                lines.append(f"  {story_url(it.headline)}")
                lines.append("")
            lines.append("")

    lines.append("-" * 60)
    lines.append(f"Read all the news: {SITE}")
    lines.append("")
    lines.append(f"You're receiving this because you subscribed to {BRAND}.")
    lines.append("Unsubscribe: {{unsubscribe_url}}")
    lines.append(f"(c) {date.today().year} {BRAND}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Public: build
# --------------------------------------------------------------------------- #

def build(out: str | Path = "public/newsletter.html") -> Path:
    """Generate the HTML newsletter (+ a sibling ``.txt``) and return its path.

    Reads ``public/digest.md`` from disk. Falls back to
    ``content/published/*.md`` if the digest is missing, and to a friendly
    empty state if neither is available. Never imports other package modules.
    """
    out_path = Path(out)
    if not out_path.is_absolute():
        out_path = ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    title = "This Week in Chesterfield"
    meta: dict = {"count": None, "generated": None, "range": None}
    sections = []

    if DIGEST_PATH.is_file():
        try:
            text = DIGEST_PATH.read_text(encoding="utf-8")
            title, meta, sections = parse_digest(text)
        except OSError as exc:
            print(f"[newsletter] warning: could not read digest: {exc}", file=sys.stderr)

    if not sections:
        # Digest missing/empty — try published stories.
        fb_meta, fb_sections = sections_from_published()
        if fb_sections:
            meta = {
                "count": fb_meta["count"],
                "generated": fb_meta["generated"],
                "range": fb_meta["range"],
            }
            sections = fb_sections
            print(
                "[newsletter] digest.md unavailable; built from "
                "content/published/*.md",
                file=sys.stderr,
            )

    start, end = _date_range(meta)
    range_label = _fmt_range(start, end)

    html = _render_html(title, meta, sections, range_label)
    txt = _render_text(title, meta, sections, range_label)

    out_path.write_text(html, encoding="utf-8")
    txt_path = out_path.with_suffix(".txt")
    txt_path.write_text(txt, encoding="utf-8")

    return out_path


def _default_subject() -> str:
    gen = None
    if DIGEST_PATH.is_file():
        try:
            _, meta, _ = parse_digest(DIGEST_PATH.read_text(encoding="utf-8"))
            start, end = _date_range(meta)
            return f"{BRAND}: This Week in Chesterfield — {_fmt_range(start, end)}"
        except OSError:
            pass
    return f"{BRAND}: This Week in Chesterfield"


# --------------------------------------------------------------------------- #
# Public: send
# --------------------------------------------------------------------------- #

_SETUP_MSG = (
    "No email provider configured. Set RESEND_API_KEY (or "
    "SMTP_HOST/USER/PASS) to send. Newsletter HTML is at "
    "public/newsletter.html — you can also paste it into "
    "Buttondown/Substack/Mailchimp."
)


def send(to_addrs: list[str], subject: str | None = None) -> None:
    """Send the generated newsletter.

    Uses Resend if ``RESEND_API_KEY`` is set, else SMTP if ``SMTP_HOST`` /
    ``SMTP_USER`` / ``SMTP_PASS`` are set, else prints setup instructions.
    Never raises on missing configuration. Secrets are read from the
    environment only.
    """
    if not to_addrs:
        print("[newsletter] send: no recipients provided; nothing to do.")
        return

    html_path = ROOT / "public" / "newsletter.html"
    txt_path = ROOT / "public" / "newsletter.txt"
    if not html_path.is_file():
        build()  # ensure artifacts exist

    html = html_path.read_text(encoding="utf-8") if html_path.is_file() else ""
    text = txt_path.read_text(encoding="utf-8") if txt_path.is_file() else None
    subject = subject or _default_subject()

    resend_key = os.environ.get("RESEND_API_KEY")
    if resend_key:
        _send_resend(resend_key, to_addrs, subject, html, text)
        return

    if all(os.environ.get(k) for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASS")):
        _send_smtp(to_addrs, subject, html, text)
        return

    print(_SETUP_MSG)


def _send_resend(api_key: str, to_addrs, subject, html, text) -> None:
    payload = {
        "from": f"{FROM_NAME} <{FROM_ADDR}>",
        "to": list(to_addrs),
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", "replace")
            print(f"[newsletter] Resend accepted ({resp.status}): {body}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace") if hasattr(exc, "read") else ""
        print(
            f"[newsletter] Resend send failed ({exc.code}): {detail}",
            file=sys.stderr,
        )
    except urllib.error.URLError as exc:
        print(f"[newsletter] Resend network error: {exc.reason}", file=sys.stderr)


def _send_smtp(to_addrs, subject, html, text) -> None:
    host = os.environ["SMTP_HOST"]
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASS"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    use_ssl = os.environ.get("SMTP_SSL", "").lower() in ("1", "true", "yes")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{FROM_NAME} <{FROM_ADDR}>"
    msg["To"] = ", ".join(to_addrs)
    msg.set_content(text or "View this newsletter in an HTML-capable client.")
    msg.add_alternative(html, subtype="html")

    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=30)
        else:
            server = smtplib.SMTP(host, port, timeout=30)
        with server:
            if not use_ssl:
                server.starttls()
            server.login(user, password)
            server.send_message(msg, to_addrs=list(to_addrs))
        print(f"[newsletter] Sent via SMTP ({host}) to {len(to_addrs)} recipient(s).")
    except (smtplib.SMTPException, OSError) as exc:
        print(f"[newsletter] SMTP send failed: {exc}", file=sys.stderr)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    path = build()
    print(f"wrote {path}")
    recips = sys.argv[1:]
    if recips:
        send(recips)
    else:
        print("(no recipients given; skipping send. Pass addresses as args to send.)")
