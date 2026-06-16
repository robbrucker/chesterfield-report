"""Where your taxes go — a plain-language Chesterfield County budget page.

Builds public/taxes.html from pipeline/budget_data.json: a summary stat band,
two horizontal bar charts (revenue by source, spending by function), and a tax-
rate table. Every figure traces to the county's official Adopted Budget book,
which is linked at the foot of the page (trust but verify).

Charts are pure CSS/HTML bars rendered at build time: no JavaScript, instant
load, theme-aware (they use the same design tokens as the rest of the site), and
readable by screen readers. The bar width equals the category's literal share of
the budget, so the picture is honest, not rescaled for drama.

Stdlib-only; reuses render._shell() for the page chrome.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

from . import render
from .render import PUBLIC

DATA = Path(__file__).resolve().parents[1] / "budget_data.json"


def _load() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def _money(d: int | float | None) -> str:
    """Compact dollar label: $1.04B, $593.7M, $42.2M."""
    if not d:
        return ""
    if d >= 1_000_000_000:
        return f"${d / 1_000_000_000:.2f}B"
    if d >= 1_000_000:
        return f"${d / 1_000_000:.1f}M"
    return f"${d / 1_000:.0f}K"


def _bar(name: str, percent: float, value: str, note: str = "") -> str:
    """One horizontal bar row. Width is the literal percent of the budget."""
    note_html = (
        f'<div class="tax-bar__note">{html.escape(note)}</div>' if note else ""
    )
    # Clamp the visual width but keep a sliver visible for tiny categories.
    width = max(0.6, min(100.0, percent))
    return (
        '<div class="tax-bar">'
        '<div class="tax-bar__head">'
        f'<span class="tax-bar__name">{html.escape(name)}</span>'
        f'<span class="tax-bar__val">{html.escape(value)}</span>'
        '</div>'
        '<div class="tax-bar__track" role="img" '
        f'aria-label="{html.escape(name)}: {value}">'
        f'<div class="tax-bar__fill" style="width:{width:.1f}%"></div>'
        '</div>'
        f'{note_html}'
        '</div>'
    )


def _chart(rows: list[dict]) -> str:
    out = []
    for r in rows:
        pct = float(r.get("percent") or 0)
        dollars = _money(r.get("dollars"))
        value = f"{pct:.1f}% · {dollars}" if dollars else f"{pct:.1f}%"
        out.append(_bar(r["name"], pct, value, r.get("note", "")))
    return "".join(out)


def _stat_band(stats: list[dict]) -> str:
    cells = "".join(
        '<div class="tax-stat">'
        f'<div class="tax-stat__v">{html.escape(s["value"])}</div>'
        f'<div class="tax-stat__l">{html.escape(s["label"])}</div>'
        '</div>'
        for s in stats
    )
    return f'<div class="tax-stats">{cells}</div>'


def _rate_rows(rates: list[dict]) -> str:
    out = []
    for r in rates:
        out.append(
            '<tr>'
            f'<th scope="row">{html.escape(r["name"])}</th>'
            f'<td class="tax-rate__rate">{html.escape(r["rate"])}</td>'
            f'<td class="tax-rate__note">{html.escape(r.get("note", ""))}</td>'
            '</tr>'
        )
    return "".join(out)


_CSS = """<style>
.tax-wrap{max-width:820px;margin:0 auto;}
.tax-lead{font:var(--fs-lg)/var(--lh-relaxed) var(--font-sans);
  color:var(--text-secondary);max-width:64ch;margin:.4rem 0 1.2rem;}
.tax-meta{font:var(--fw-medium) var(--fs-2xs)/1.4 var(--font-mono);
  letter-spacing:var(--ls-wide);text-transform:uppercase;color:var(--text-tertiary);
  margin-bottom:1.6rem;}
.tax-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:0 0 2.2rem;}
.tax-stat{border:1px solid var(--border);border-radius:var(--radius-xs);
  padding:.9rem 1rem;background:var(--surface-card);}
.tax-stat__v{font:var(--fw-bold) var(--fs-2xl)/1 var(--font-display);color:var(--accent);}
.tax-stat__l{font:var(--fs-2xs)/1.3 var(--font-sans);color:var(--text-secondary);
  margin-top:.35rem;}
.tax-sec{margin:2.4rem 0;}
.tax-sec h2{font:var(--fw-bold) var(--fs-xl)/1.15 var(--font-display);margin:0 0 .3rem;}
.tax-sec__dek{font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);
  color:var(--text-secondary);margin:0 0 1.2rem;}
.tax-bar{margin:0 0 1.05rem;}
.tax-bar__head{display:flex;justify-content:space-between;align-items:baseline;
  gap:12px;margin-bottom:.35rem;}
.tax-bar__name{font:var(--fw-semibold) var(--fs-sm)/1.3 var(--font-sans);color:var(--text-primary);}
.tax-bar__val{font:var(--fw-bold) var(--fs-2xs)/1 var(--font-mono);color:var(--text-secondary);
  white-space:nowrap;}
.tax-bar__track{height:14px;background:var(--surface-sunken,rgba(128,128,128,.16));
  border-radius:999px;overflow:hidden;}
.tax-bar__fill{height:100%;background:var(--accent);border-radius:999px;min-width:3px;}
.tax-bar__note{font:var(--fs-2xs)/1.4 var(--font-sans);color:var(--text-tertiary);margin-top:.3rem;}
.tax-rates{width:100%;border-collapse:collapse;margin:.4rem 0 0;font-size:.9rem;}
.tax-rates th[scope=row]{text-align:left;font:var(--fw-semibold) .92rem/1.3 var(--font-sans);
  padding:.65rem .8rem .65rem 0;vertical-align:top;color:var(--text-primary);
  border-top:1px solid var(--border);width:38%;}
.tax-rates td{padding:.65rem .8rem;border-top:1px solid var(--border);
  vertical-align:top;color:var(--text-secondary);}
.tax-rate__rate{font:var(--fw-bold) .92rem/1.3 var(--font-mono);color:var(--accent);
  white-space:nowrap;width:22%;}
.tax-source{margin:2.4rem 0 0;padding:1rem 1.1rem;border-left:3px solid var(--accent);
  background:var(--surface-card);border-radius:var(--radius-xs);
  font:var(--fs-sm)/var(--lh-relaxed) var(--font-sans);color:var(--text-secondary);}
.tax-source a{color:var(--accent);font-weight:600;}
.tax-xlinks{margin:1.6rem 0 0;font:var(--fs-sm)/1.6 var(--font-sans);color:var(--text-secondary);}
.tax-xlinks a{color:var(--accent);font-weight:600;}
@media(max-width:620px){
  .tax-stats{grid-template-columns:repeat(2,1fr);}
  .tax-rates th[scope=row]{width:auto;}
}
</style>"""


def build_taxes() -> Path:
    """Render public/taxes.html from the verified county budget data."""
    d = _load()

    body = (
        _CSS
        + '<div class="tax-wrap">'
        + '<h1 class="page-title">Where Your Taxes Go</h1>'
        + f'<div class="tax-meta">Chesterfield County · {html.escape(d["fiscal_year_label"])}</div>'
        + '<p class="tax-lead">A plain-language look at the county’s budget: '
          'where the money comes from, where it goes, and what you pay. '
          'Figures are from the county’s official adopted budget, linked at the '
          'bottom so you can check the math yourself.</p>'
        + _stat_band(d["headline_stats"])

        + '<div class="tax-sec">'
          '<h2>Where the money comes from</h2>'
          '<p class="tax-sec__dek">General Fund revenue, the county’s main '
          f'local operating budget ({_money(d["general_fund_total"])} in '
          f'{html.escape(d["fiscal_year"])}). Most of it is the property taxes you pay.</p>'
        + _chart(d["revenue"])
        + '</div>'

        + '<div class="tax-sec">'
          '<h2>Where it goes</h2>'
          '<p class="tax-sec__dek">General Fund spending by function. Two of every '
          'three dollars go to schools and public safety.</p>'
        + _chart(d["spending"])
        + '</div>'

        + '<div class="tax-sec">'
          '<h2>What you pay: tax rates</h2>'
          '<p class="tax-sec__dek">Current Chesterfield County tax rates.</p>'
          '<table class="tax-rates"><tbody>'
        + _rate_rows(d["tax_rates"])
        + '</tbody></table></div>'

        + '<div class="tax-source">'
          'Every figure on this page comes from the '
          f'<a href="{html.escape(d["source_url"])}" target="_blank" rel="noopener">'
          f'{html.escape(d["source_title"])}</a>. '
          f'{html.escape(d["adopted"])}. '
          f'More county budget documents are at the '
          f'<a href="{html.escape(d["index_url"])}" target="_blank" rel="noopener">'
          'county Budget &amp; Management department</a>. '
          'The full county budget across all funds (including schools’ state '
          f'money and ratepayer-funded utilities) is {_money(d["all_funds_total"])}; '
          'the General Fund shown here is the local operating portion.'
          '</div>'

        + '<div class="tax-xlinks">'
          'Related: <a href="/board.html">Board of Supervisors</a> '
          '(who sets the budget and tax rates) · '
          '<a href="/meetings.html">Meetings</a> · '
          '<a href="/topics/government.html">Government coverage</a>'
          '</div>'
        + '</div>'
    )

    out = PUBLIC / "taxes.html"
    out.write_text(render._shell(body), encoding="utf-8")
    return out
