"""Email the editor a digest of drafts the AI flagged for review.

Called after triage (in the cron). Sends via Resend (RESEND_API_KEY) or SMTP
(SMTP_HOST/SMTP_USER/SMTP_PASS), else prints what it would have sent. No secrets
in code — everything comes from environment variables.
"""
from __future__ import annotations

import html as _htmllib
import json
import os
import smtplib
import urllib.request
from email.message import EmailMessage

from . import render

REVIEW_URL = "http://localhost:8787"
DEFAULT_TO = "brucker.rob@gmail.com"


def _esc(s: str) -> str:
    return _htmllib.escape(s or "")


def flagged() -> list[dict]:
    """Drafts the AI editor flagged for human review (verdict == 'review')."""
    out = []
    for p in sorted(render.DRAFTS.glob("*.md")):
        meta, _ = render._parse_frontmatter(p.read_text(encoding="utf-8"))
        if (meta.get("ai_verdict") or "").strip().lower() == "review":
            out.append({
                "name": p.name,
                "headline": meta.get("headline", ""),
                "reason": meta.get("ai_verdict_reason", ""),
                "sensitive": (meta.get("ai_sensitive", "") or "").strip().lower()
                              in ("true", "1", "yes"),
                "source": meta.get("source", ""),
            })
    return out


def _html(items: list[dict]) -> str:
    rows = "".join(
        '<tr><td style="padding:11px 0;border-bottom:1px solid #e2e8e7">'
        f'<div style="font:600 16px Georgia,serif;color:#003e51">{_esc(i["headline"])}</div>'
        f'<div style="font:13px Arial,sans-serif;color:#5c6b6e;margin-top:3px">{_esc(i["reason"])}'
        + (' &middot; <b style="color:#b8860b">sensitive</b>' if i["sensitive"] else "")
        + (f' &middot; {_esc(i["source"])}' if i["source"] else "")
        + "</div></td></tr>"
        for i in items
    )
    n = len(items)
    return (
        '<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif">'
        '<div style="background:#003e51;color:#fff;padding:16px 20px">'
        '<span style="font:700 18px Georgia,serif">The Chesterfield Report</span>'
        '<span style="color:#8cf06a;font:600 12px Arial;letter-spacing:.1em">&nbsp;&nbsp;EDITOR QUEUE</span></div>'
        '<div style="padding:18px 20px;color:#222">'
        f'<p style="font-size:15px">{n} stor{"y needs" if n == 1 else "ies need"} your review before publishing:</p>'
        f'<table style="width:100%;border-collapse:collapse">{rows}</table>'
        f'<p style="margin:20px 0"><a href="{REVIEW_URL}" '
        'style="background:#1f6b53;color:#fff;padding:11px 18px;border-radius:8px;'
        'text-decoration:none;font-weight:700">Open the review console &rarr;</a></p>'
        f'<p style="color:#8a97a0;font-size:12px">Approve/reject at {REVIEW_URL} '
        '(run <code>python3 run.py serve</code> if it isn\'t open). Everything else '
        'auto-publishes; these were held for your judgment.</p></div></div>'
    )


def _text(items: list[dict]) -> str:
    lines = [f"{len(items)} stories need your review before publishing:", ""]
    for i in items:
        lines.append(f"- {i['headline']} — {i['reason']}"
                     + (" [SENSITIVE]" if i["sensitive"] else ""))
    lines += ["", f"Review: {REVIEW_URL}"]
    return "\n".join(lines)


def _send(to: str, subject: str, html_body: str, text_body: str) -> str:
    frm = (os.environ.get("ALERT_FROM") or os.environ.get("NEWSLETTER_FROM")
           or "alerts@chesterfieldreport.com")
    key = os.environ.get("RESEND_API_KEY")
    if key:
        data = json.dumps({"from": frm, "to": [to], "subject": subject,
                           "html": html_body, "text": text_body}).encode()
        req = urllib.request.Request("https://api.resend.com/emails", data=data,
                                     headers={"Authorization": f"Bearer {key}",
                                              "Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=20)
            return "sent via Resend"
        except Exception as e:
            return f"Resend failed: {e}"
    if os.environ.get("SMTP_HOST"):
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = frm, to, subject
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")
        try:
            host, port = os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", "587"))
            if os.environ.get("SMTP_SSL") == "1":
                s = smtplib.SMTP_SSL(host, port, timeout=20)
            else:
                s = smtplib.SMTP(host, port, timeout=20)
                s.starttls()
            s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
            s.send_message(msg)
            s.quit()
            return "sent via SMTP"
        except Exception as e:
            return f"SMTP failed: {e}"
    return ("NOT SENT — no email provider configured. Set RESEND_API_KEY, or "
            "SMTP_HOST/SMTP_USER/SMTP_PASS (e.g. Gmail app password), in "
            "scripts/.deploy.env.")


def email_flagged(to: str = DEFAULT_TO) -> str:
    items = flagged()
    if not items:
        print("No flagged items awaiting review — nothing to email.")
        return "none"
    subject = f"[Chesterfield Report] {len(items)} stories need your review"
    result = _send(to, subject, _html(items), _text(items))
    print(f"Flagged-items email ({len(items)} items) -> {to}: {result}")
    return result
