"""Public-safety pages: Chesterfield Police and Chesterfield Fire & EMS.

Builds public/police.html and public/fire.html from pipeline/safety_data.json:
who runs each department, where the stations are, what it costs and on what,
how many officers/firefighters there are, and what the work looks like (arrests
and traffic for police; calls and response for fire). Every figure traces to an
official source linked at the foot of the page.

Pure CSS/HTML, no JavaScript. Stdlib only; reuses render._shell() / _inject_og.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

from . import render
from .render import PUBLIC

DATA = Path(__file__).resolve().parents[1] / "safety_data.json"


def _load() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def _money(d) -> str:
    if not d:
        return ""
    if d >= 1_000_000_000:
        return f"${d / 1_000_000_000:.2f}B"
    if d >= 1_000_000:
        return f"${d / 1_000_000:.1f}M"
    if d >= 1_000:
        return f"${d / 1_000:.0f}K"
    return f"${d:.0f}"


def _stat_band(stats: list) -> str:
    cells = "".join(
        '<div class="ps-stat">'
        f'<div class="ps-stat__v">{html.escape(s["value"])}</div>'
        f'<div class="ps-stat__l">{html.escape(s["label"])}</div>'
        '</div>'
        for s in stats
    )
    return f'<div class="ps-stats">{cells}</div>'


def _bar(name: str, percent: float, value: str) -> str:
    width = max(0.6, min(100.0, percent))
    return (
        '<div class="ps-bar">'
        '<div class="ps-bar__head">'
        f'<span class="ps-bar__name">{html.escape(name)}</span>'
        f'<span class="ps-bar__val">{html.escape(value)}</span>'
        '</div>'
        f'<div class="ps-bar__track" role="img" aria-label="{html.escape(name)}: {html.escape(value)}">'
        f'<div class="ps-bar__fill" style="width:{width:.1f}%"></div>'
        '</div></div>'
    )


def _budget_chart(rows: list) -> str:
    out = []
    for r in rows:
        pct = float(r.get("percent") or 0)
        dollars = _money(r.get("dollars"))
        value = f"{pct:.0f}% · {dollars}" if dollars else f"{pct:.0f}%"
        out.append(_bar(r["name"], pct, value))
    return "".join(out)


def _chief_card(c: dict) -> str:
    return (
        '<section class="ps-chief">'
        f'<div class="ps-chief__role">{html.escape(c["title"])}</div>'
        f'<div class="ps-chief__name">{html.escape(c["name"])}</div>'
        f'<div class="ps-chief__since">{html.escape(c.get("since", ""))}</div>'
        + (f'<p class="ps-chief__note">{html.escape(c["note"])}</p>' if c.get("note") else "")
        + '</section>'
    )


def _work_grid(stats: list) -> str:
    cells = "".join(
        '<div class="ps-work">'
        f'<div class="ps-work__v">{html.escape(s["value"])}</div>'
        f'<div class="ps-work__l">{html.escape(s["label"])}</div>'
        '</div>'
        for s in stats
    )
    return f'<div class="ps-work-grid">{cells}</div>'


def _sources(srcs: list) -> str:
    links = " &middot; ".join(
        f'<a href="{html.escape(s["url"])}" target="_blank" rel="noopener">{html.escape(s["label"])}</a>'
        for s in srcs
    )
    return (
        '<div class="ps-source">Every figure on this page comes from official '
        f'sources: {links}. Numbers are the latest the county publishes; check the '
        'links to verify or for the most current figures.</div>'
    )


_CSS = """<style>
.ps-wrap{max-width:820px;margin:0 auto;}
.ps-lead{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);max-width:64ch;margin:.4rem 0 1rem;}
.ps-meta{font:var(--fw-medium) var(--fs-2xs)/1.4 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);margin-bottom:1.6rem;}
.ps-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:0 0 2.2rem;}
.ps-stat{border:1px solid var(--border);border-radius:var(--radius-xs);padding:.9rem 1rem;background:var(--surface-card);}
.ps-stat__v{font:var(--fw-bold) var(--fs-2xl)/1 var(--font-display);color:var(--accent);}
.ps-stat__l{font:var(--fs-3xs)/1.3 var(--font-sans);color:var(--text-secondary);margin-top:.35rem;}
.ps-sec{margin:2.4rem 0;}
.ps-sec h2{font:var(--fw-bold) var(--fs-xl)/1.15 var(--font-display);margin:0 0 .3rem;}
.ps-sec__dek{font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);margin:0 0 1.2rem;max-width:64ch;}
.ps-chief{border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:var(--radius-sm);background:var(--surface-card);padding:1.1rem 1.25rem;margin:0 0 1rem;}
.ps-chief__role{font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--accent);}
.ps-chief__name{font:var(--fw-bold) var(--fs-2xl)/1.15 var(--font-display);color:var(--text-primary);margin:.25rem 0 .1rem;}
.ps-chief__since{font:var(--fw-semibold) var(--fs-sm) var(--font-sans);color:var(--text-secondary);}
.ps-chief__note{font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);margin:.6rem 0 0;}
.ps-bar{margin:0 0 1.05rem;}
.ps-bar__head{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin-bottom:.35rem;}
.ps-bar__name{font:var(--fw-semibold) var(--fs-sm)/1.3 var(--font-sans);color:var(--text-primary);}
.ps-bar__val{font:var(--fw-bold) var(--fs-2xs)/1 var(--font-mono);color:var(--text-secondary);white-space:nowrap;}
.ps-bar__track{height:14px;background:var(--surface-sunken,rgba(128,128,128,.16));border-radius:999px;overflow:hidden;}
.ps-bar__fill{height:100%;background:var(--accent);border-radius:999px;min-width:3px;}
.ps-note{font:var(--fs-2xs)/1.55 var(--font-sans);color:var(--text-tertiary);margin:.4rem 0 0;max-width:64ch;}
.ps-work-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;}
.ps-work{border:1px solid var(--border);border-radius:var(--radius-xs);padding:.85rem .95rem;background:var(--surface-card);}
.ps-work__v{font:var(--fw-bold) var(--fs-xl)/1 var(--font-display);color:var(--text-primary);}
.ps-work__l{font:var(--fs-3xs)/1.35 var(--font-sans);color:var(--text-secondary);margin-top:.3rem;}
.ps-hq{border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface-card);padding:.9rem 1.1rem;margin:0 0 .8rem;}
.ps-hq__name{font:var(--fw-bold) var(--fs-md) var(--font-display);color:var(--text-primary);}
.ps-hq__addr{font:var(--fs-sm)/1.5 var(--font-sans);color:var(--text-secondary);margin-top:.15rem;}
.ps-hq__phone{font:var(--fs-2xs) var(--font-mono);color:var(--text-tertiary);margin-top:.2rem;}
.ps-stations{width:100%;border-collapse:collapse;margin:.4rem 0 0;}
.ps-stations th{text-align:left;font:var(--fw-bold) var(--fs-3xs)/1 var(--font-mono);letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);padding:0 .6rem .5rem 0;border-bottom:1px solid var(--border);}
.ps-stations td{padding:.55rem .6rem;border-bottom:1px solid var(--border);font:var(--fs-sm)/1.4 var(--font-sans);color:var(--text-secondary);vertical-align:top;}
.ps-stations .ps-st-n{font:var(--fw-bold) var(--fs-sm) var(--font-mono);color:var(--accent);width:2.5rem;}
.ps-stations .ps-st-name{font-weight:var(--fw-semibold);color:var(--text-primary);white-space:nowrap;}
.ps-source{margin:2.4rem 0 0;padding:1rem 1.1rem;border-left:3px solid var(--accent);background:var(--surface-card);border-radius:var(--radius-xs);font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);}
.ps-source a{color:var(--accent);font-weight:600;}
.ps-xlinks{margin:1.6rem 0 0;font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);}
.ps-xlinks a{color:var(--accent);font-weight:600;}
@media(max-width:620px){
  .ps-stats{grid-template-columns:repeat(2,1fr);}
  .ps-work-grid{grid-template-columns:repeat(2,1fr);}
  .ps-stations .ps-st-name{white-space:normal;}
}
</style>"""


def _page(d: dict, title: str, xlinks: str) -> str:
    return (
        _CSS
        + '<div class="ps-wrap">'
        + f'<h1 class="page-title">{html.escape(d["name"])}</h1>'
        + f'<div class="ps-meta">{html.escape(d["meta"])}</div>'
        + f'<p class="ps-lead">{html.escape(d["lead"])}</p>'
        + _stat_band(d["headline_stats"])
        + '<div class="ps-sec"><h2>Who runs it</h2>'
        + _chief_card(d["chief"])
        + '</div>'
        + '<div class="ps-sec"><h2>Where the money goes</h2>'
        + f'<p class="ps-sec__dek">Department budget: <strong>{html.escape(d["budget_total_label"])}</strong>. '
          'Like most public-safety agencies, the great majority is people, not equipment.</p>'
        + _budget_chart(d["budget"])
        + (f'<p class="ps-note">{html.escape(d["budget_note"])}</p>' if d.get("budget_note") else "")
        + '</div>'
        + '<div class="ps-sec"><h2>' + html.escape(d["work_title"]) + '</h2>'
        + f'<p class="ps-sec__dek">{html.escape(d["work_dek"])}</p>'
        + _work_grid(d["work_stats"])
        + (f'<p class="ps-note">{html.escape(d["current_note"])}</p>' if d.get("current_note") else "")
        + '</div>'
        + xlinks
        + (f'<p class="ps-note">{html.escape(d["staffing_note"])}</p>' if d.get("staffing_note") else "")
        + _sources(d["sources"])
        + '<div class="ps-xlinks">Related: <a href="/taxes.html">Where your taxes go</a> '
          '&middot; <a href="/board.html">Board of Supervisors</a> '
          '&middot; <a href="/topics/police.html">Public-safety coverage</a></div>'
        + '</div>'
    )


def build_police() -> Path:
    d = _load()["police"]
    s = d["stations"]
    stations_html = (
        '<div class="ps-sec"><h2>Where it is</h2>'
        '<div class="ps-hq">'
        f'<div class="ps-hq__name">{html.escape(s["hq"]["name"])}</div>'
        f'<div class="ps-hq__addr">{html.escape(s["hq"]["address"])}</div>'
        f'<div class="ps-hq__phone">{html.escape(s["hq"]["phone"])}</div>'
        '</div>'
        f'<p class="ps-note">{html.escape(s["note"])}</p>'
        '</div>'
    )
    body = _page(d, "Chesterfield County Police", stations_html)
    page = render._shell(body)
    page = render._inject_og(
        page, "Chesterfield County Police: leadership, budget, officers, and crime stats",
        "Who runs the Chesterfield County Police Department, where it is, its budget, "
        "how many officers it has, and its 2024 arrest and traffic enforcement numbers.",
        f"{render.SITE_URL}/police.html", og_type="website")
    out = PUBLIC / "police.html"
    out.write_text(page, encoding="utf-8")
    return out


def build_fire() -> Path:
    d = _load()["fire"]
    rows = "".join(
        '<tr>'
        f'<td class="ps-st-n">{html.escape(st["n"])}</td>'
        f'<td class="ps-st-name">{html.escape(st["name"])}</td>'
        f'<td>{html.escape(st["address"])}</td>'
        '</tr>'
        for st in d["stations"]
    )
    stations_html = (
        '<div class="ps-sec"><h2>Where the stations are</h2>'
        f'<p class="ps-sec__dek">{html.escape(d["stations_note"])}</p>'
        '<table class="ps-stations"><thead><tr>'
        '<th>#</th><th>Station</th><th>Address</th>'
        '</tr></thead><tbody>'
        + rows
        + '</tbody></table></div>'
    )
    body = _page(d, "Chesterfield Fire & EMS", stations_html)
    page = render._shell(body)
    page = render._inject_og(
        page, "Chesterfield Fire & EMS: leadership, stations, budget, and call volume",
        "Who runs Chesterfield Fire & EMS, where its 21 stations are, its budget, how "
        "many firefighters and medics it has, and how many emergencies it answers a year.",
        f"{render.SITE_URL}/fire.html", og_type="website")
    out = PUBLIC / "fire.html"
    out.write_text(page, encoding="utf-8")
    return out
