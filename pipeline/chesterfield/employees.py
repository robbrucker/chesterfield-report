"""Chesterfield County employee salary lookup — builder.

RESEARCH OUTCOME (2026-06-09): there is **no clean, keyless, fetchable** salary
dataset for Chesterfield County (or CCPS) employees. The records are public, but
a machine-readable file requires a FOIA request to the county. Statewide VA
databases (Data Point, RTD, OpenTheBooks, data.virginia.gov) are STATE employees
only; the county's open-data portals are GIS-only; aggregators (GovSalaries,
OpenGovPay) have the data but are HTTP-403 bot-walled with no public CSV/JSON/API.
See ``docs/salary-research.md`` for the full write-up and source URLs.

Per the task constraints we therefore do **not** ship a fragile scraper. This
module instead:

* renders a themed "coming soon — here's how to get the data" placeholder, OR
* if/when a real, FOIA-released dataset is dropped at ``pipeline/salary_data.json``
  (or a sibling CSV), renders a full client-side salary-lookup page from it.

So the nav link never 404s, and the page upgrades to real data automatically with
no code change. Stdlib only; keyless. pyexpat is broken in this environment, so we
avoid any XML parsing (we only ever read CSV/JSON, which are fine).
"""
from __future__ import annotations

import csv
import html
import json
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve()
PIPELINE_DIR = _HERE.parent.parent            # .../pipeline
PROJECT_ROOT = PIPELINE_DIR.parent            # repo root
PUBLIC = PROJECT_ROOT / "public"

# Where a FOIA-released dataset should be dropped to light up the real page.
DATA_JSON = PIPELINE_DIR / "salary_data.json"
# Optional CSV the FOIA office might hand back; first match wins, newest-ish.
_CSV_CANDIDATES = [
    PIPELINE_DIR / "salary_data.csv",
    PIPELINE_DIR / "chesterfield_salaries.csv",
]

# Source attribution shown on the page (kept accurate to how data was obtained).
SOURCE_LABEL = "Chesterfield County, Virginia (public record, FOIA payroll extract)"

# Embed cap: render at most this many rows into the page; the rest stay searchable
# via the embedded JSON but are not painted until matched/scrolled.
_VISIBLE_CAP = 200

# ---------------------------------------------------------------------------
# Theme shell (matches public/map.html — dark editorial-cyberpunk)
# ---------------------------------------------------------------------------
_HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Employee Salaries &mdash; The Chesterfield Report</title>
<meta name="description" content="Look up Chesterfield County, Virginia public employee salaries by name, job title, or department. Figures are public record.">
<meta name="theme-color" content="#06141a">
<link rel="icon" href="/assets/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700;9..144,900&family=Source+Sans+3:wght@400;500;600;700&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:#06141a; --bg2:#0a1f28; --surface:#0e2730; --line:#1c4a58;
    --ink:#e6f7f2; --muted:#8fb4af;
    --neon:#27e6c6; --neon2:#8cf06a; --magenta:#ff479e;
    --gold:#ffc94a; --danger:#ff5d72;
    --serif:'Fraunces',Georgia,'Times New Roman',serif;
    --mono:'Space Mono',ui-monospace,SFMono-Regular,Menlo,monospace;
    --sans:'Source Sans 3',system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
    --wrap:980px;
  }
  * { box-sizing:border-box; }
  html { scroll-behavior:smooth; }
  body {
    margin:0; color:var(--ink); background-color:var(--bg);
    background-image:
      radial-gradient(circle at 15% -8%, rgba(39,230,198,.10), transparent 45%),
      radial-gradient(circle at 92% 4%, rgba(255,71,158,.07), transparent 40%),
      linear-gradient(rgba(28,74,88,.16) 1px, transparent 1px),
      linear-gradient(90deg, rgba(28,74,88,.16) 1px, transparent 1px);
    background-size:auto, auto, 46px 46px, 46px 46px;
    background-attachment:fixed;
    font-family:var(--sans); font-size:17px; line-height:1.65;
    -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility;
  }
  a { color:var(--neon); text-decoration:none; }
  a:hover { text-decoration:underline; text-decoration-color:var(--magenta);
    text-shadow:0 0 8px rgba(39,230,198,.45); }
  :focus-visible { outline:2px solid var(--neon); outline-offset:2px; border-radius:4px;
    box-shadow:0 0 0 4px rgba(39,230,198,.25); }
  .masthead {
    background:linear-gradient(180deg,#081b22,#06141a); color:#fff; position:relative;
    border-bottom:1px solid var(--line);
    box-shadow:0 0 24px rgba(39,230,198,.12), inset 0 -1px 0 rgba(39,230,198,.35);
  }
  .masthead::after {
    content:""; position:absolute; left:0; right:0; bottom:-1px; height:2px;
    background:linear-gradient(90deg,transparent,var(--neon),var(--neon2),transparent);
    box-shadow:0 0 14px var(--neon); opacity:.85;
  }
  .masthead-inner {
    max-width:var(--wrap); margin:0 auto; padding:1.4rem 1.25rem 1.5rem;
    display:flex; flex-wrap:wrap; align-items:center; gap:1rem 1.5rem;
  }
  .brand { display:flex; align-items:center; gap:.85rem; min-width:0; }
  .brand img { height:52px; width:auto; display:block; filter:drop-shadow(0 0 6px rgba(39,230,198,.5)); }
  .brand .wordmark {
    font-family:var(--serif); font-weight:900; font-size:1.7rem;
    letter-spacing:-.01em; line-height:1; color:#fff; white-space:nowrap;
    text-shadow:0 0 18px rgba(39,230,198,.35);
  }
  .brand .wordmark .now { color:var(--neon); text-shadow:0 0 16px rgba(39,230,198,.8); }
  .tagline {
    margin:0; flex:1 1 240px; min-width:200px; color:var(--muted);
    font-size:1.02rem; line-height:1.4; border-left:1px solid var(--line);
    padding-left:1.25rem; font-family:var(--serif); font-style:italic; font-weight:400;
  }
  .topnav { max-width:var(--wrap); margin:0 auto; padding:.5rem 1.25rem;
    display:flex; flex-wrap:wrap; gap:.25rem 1.1rem; font-family:var(--mono);
    font-size:.78rem; letter-spacing:.04em; border-top:1px solid rgba(39,230,198,.1); }
  .topnav a { color:var(--muted); text-transform:uppercase; }
  .topnav a:hover { color:var(--neon); }
  .dateline { width:100%; max-width:var(--wrap); margin:0 auto; padding:.4rem 1.25rem;
    display:flex; justify-content:space-between; flex-wrap:wrap; gap:.5rem;
    font-family:var(--mono); font-size:.7rem; letter-spacing:.06em; color:var(--muted);
    border-top:1px solid rgba(39,230,198,.1); }
  .dateline .place { color:var(--neon2); }
  main { max-width:var(--wrap); margin:0 auto; padding:2rem 1.25rem 3rem; }
  h1 { font-family:var(--serif); font-weight:900; font-size:2.1rem; line-height:1.1;
    margin:.2rem 0 .4rem; text-shadow:0 0 22px rgba(39,230,198,.25); }
  h1 .now { color:var(--neon); }
  .lede { color:var(--muted); font-size:1.05rem; max-width:46rem; margin:.2rem 0 1.4rem; }
  .meta-line { font-family:var(--mono); font-size:.72rem; letter-spacing:.06em;
    color:var(--neon2); text-transform:uppercase; margin:0 0 1.6rem; }
  .note { font-size:.86rem; color:var(--muted); }
  .panel { background:var(--surface); border:1px solid var(--line); border-radius:12px;
    padding:1.4rem 1.5rem; box-shadow:0 0 24px rgba(39,230,198,.06); margin:1.2rem 0; }
  .panel h2 { font-family:var(--serif); font-size:1.25rem; margin:.1rem 0 .6rem; }
  /* search + table */
  .searchbar { display:flex; gap:.6rem; flex-wrap:wrap; align-items:center; margin:0 0 .6rem; }
  .searchbar input {
    flex:1 1 320px; min-width:0; font-family:var(--sans); font-size:1rem;
    color:var(--ink); background:#08222b; border:1px solid var(--line);
    border-radius:10px; padding:.7rem .9rem;
  }
  .searchbar input::placeholder { color:#5e8a85; }
  .searchbar input:focus { outline:none; border-color:var(--neon);
    box-shadow:0 0 0 3px rgba(39,230,198,.25); }
  .count { font-family:var(--mono); font-size:.74rem; color:var(--muted); white-space:nowrap; }
  table { width:100%; border-collapse:collapse; font-size:.95rem; }
  thead th { text-align:left; font-family:var(--mono); font-size:.7rem; letter-spacing:.06em;
    text-transform:uppercase; color:var(--neon2); border-bottom:1px solid var(--line);
    padding:.5rem .6rem; }
  tbody td { padding:.55rem .6rem; border-bottom:1px solid rgba(28,74,88,.5); vertical-align:top; }
  tbody tr:hover td { background:rgba(39,230,198,.05); }
  td.salary { font-family:var(--mono); color:var(--gold); white-space:nowrap; text-align:right; }
  .empty { padding:1.2rem .6rem; color:var(--muted); font-style:italic; }
  .more { font-family:var(--mono); font-size:.74rem; color:var(--muted); margin:.8rem 0 0; }
  .btn { display:inline-block; font-family:var(--mono); font-size:.74rem; letter-spacing:.06em;
    text-transform:uppercase; color:var(--bg); background:var(--neon); border-radius:8px;
    padding:.55rem .9rem; margin:.3rem .4rem .3rem 0; font-weight:700; }
  .btn:hover { background:var(--neon2); text-decoration:none; }
  footer { position:relative; border-top:1px solid var(--line); margin-top:2.5rem;
    background:linear-gradient(180deg,#06141a,#081b22); }
  .footer-inner { max-width:var(--wrap); margin:0 auto; padding:2rem 1.25rem 2.5rem; }
  .footer-brand { font-family:var(--serif); font-weight:900; font-size:1.3rem; }
  .footer-brand .now { color:var(--neon); text-shadow:0 0 14px rgba(39,230,198,.7); }
  .footer-inner p { margin:.5rem 0; font-size:.9rem; max-width:46rem; color:var(--muted); }
  .footer-meta { font-family:var(--mono); font-size:.72rem; color:var(--muted); margin-top:1rem; }
  .footer-domain { color:var(--neon); font-weight:700; text-shadow:0 0 10px rgba(39,230,198,.5); }
  @media (max-width:640px){ .brand .wordmark{font-size:1.6rem;} .brand img{height:42px;}
    .tagline{border-left:0;padding-left:0;font-size:.95rem;} h1{font-size:1.7rem;} }
</style></head>
<body>
<header class="masthead">
  <div class="masthead-inner">
    <a class="brand" href="/" aria-label="The Chesterfield Report home">
      <img src="/assets/logo-mark.svg" alt="The Chesterfield Report heron emblem">
      <span class="wordmark">The Chesterfield<span class="now"> Report</span></span>
    </a>
    <p class="tagline">Hyperlocal news for Chesterfield County, Virginia.</p>
  </div>
  <nav class="topnav">
    <a href="/">Home</a><a href="/topics/">Topics</a><a href="/digest.html">This Week</a><a href="/map.html">Map</a><a href="/board.html">Board</a><a href="/salaries.html">Salaries</a><a href="/tip.html">Send a tip</a>
  </nav>
  <div class="dateline">
    <span class="place">Chesterfield County &middot; Virginia</span>
    <span>__UPDATED__</span>
  </div>
</header>
<main>
"""

_FOOT = """</main>
<footer>
  <div class="footer-inner">
    <div class="footer-brand">The Chesterfield<span class="now"> Report</span></div>
    <p>Salary figures published here are <strong>public record</strong> under the
       Virginia Freedom of Information Act. Names, titles and pay are routinely
       released by public bodies; this lookup is informational, not an HR system.</p>
    <div class="footer-meta">
      __UPDATED__ &middot; <span class="footer-domain">chesterfieldreport.com</span>
    </div>
  </div>
</footer>
</body></html>
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _esc(s) -> str:
    return html.escape("" if s is None else str(s))


def _money(v) -> str:
    """Format a number as USD; pass through non-numeric strings unchanged."""
    try:
        n = float(str(v).replace("$", "").replace(",", "").strip())
    except (TypeError, ValueError):
        return _esc(v)
    return "$" + format(int(round(n)), ",")


# ---------------------------------------------------------------------------
# Data loading (only reads if a real, FOIA-released file is present)
# ---------------------------------------------------------------------------
_FIELD_ALIASES = {
    "name": ("name", "employee", "employee_name", "full_name"),
    "title": ("title", "job_title", "position", "position_title", "role", "class"),
    "dept": ("dept", "department", "agency", "division", "department_division"),
    "salary": ("salary", "annual_salary", "pay", "compensation", "total_pay",
               "base_pay", "gross_pay", "rate"),
}


def _pick(row: dict, key: str) -> str:
    low = {k.lower().strip(): v for k, v in row.items()}
    for alias in _FIELD_ALIASES[key]:
        if alias in low and str(low[alias]).strip():
            return str(low[alias]).strip()
    return ""


def _normalize(rows: list) -> list:
    """Map arbitrary FOIA columns onto our 4 canonical fields. Drops empties."""
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        rec = {
            "name": _pick(r, "name"),
            "title": _pick(r, "title"),
            "dept": _pick(r, "dept"),
            "salary": _pick(r, "salary"),
        }
        if rec["name"] or rec["title"]:
            out.append(rec)
    return out


def _load_dataset():
    """Return (records, meta) if a real dataset exists, else (None, None).

    meta carries provenance: {'source', 'as_of', 'count'}. Supports two shapes:
      * JSON: a bare list of row dicts, OR {'as_of':..,'source':..,'records':[...]}
      * CSV: header row + data rows (column names matched fuzzily)
    """
    # Prefer the cached JSON (this is also what the real branch would write).
    if DATA_JSON.exists():
        try:
            raw = json.loads(DATA_JSON.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            raw = None
        if isinstance(raw, dict):
            rows = raw.get("records") or raw.get("data") or []
            recs = _normalize(rows)
            if recs:
                return recs, {
                    "source": raw.get("source") or SOURCE_LABEL,
                    "as_of": raw.get("as_of") or _today(),
                    "count": len(recs),
                }
        elif isinstance(raw, list):
            recs = _normalize(raw)
            if recs:
                return recs, {"source": SOURCE_LABEL, "as_of": _today(), "count": len(recs)}

    # Otherwise accept a FOIA-handed CSV and cache it to JSON for next time.
    for csv_path in _CSV_CANDIDATES:
        if csv_path.exists():
            try:
                with csv_path.open(newline="", encoding="utf-8-sig") as fh:
                    rows = list(csv.DictReader(fh))
            except OSError:
                continue
            recs = _normalize(rows)
            if recs:
                meta = {"source": SOURCE_LABEL, "as_of": _today(), "count": len(recs)}
                try:
                    DATA_JSON.write_text(
                        json.dumps({"source": meta["source"], "as_of": meta["as_of"],
                                    "records": recs}, ensure_ascii=False),
                        encoding="utf-8")
                except OSError:
                    pass
                return recs, meta
    return None, None


# ---------------------------------------------------------------------------
# Page builders
# ---------------------------------------------------------------------------
def _render_lookup(records: list, meta: dict) -> str:
    """Full client-side salary-lookup page from real data."""
    payload = json.dumps(records, ensure_ascii=False, separators=(",", ":"))
    visible = records[:_VISIBLE_CAP]
    rows_html = "\n".join(
        '<tr><td>{n}</td><td>{t}</td><td>{d}</td><td class="salary">{s}</td></tr>'.format(
            n=_esc(r["name"]), t=_esc(r["title"]), d=_esc(r["dept"]),
            s=_money(r["salary"]))
        for r in visible)
    more = (f'<p class="more" id="moreNote">Showing first {len(visible):,} of '
            f'{len(records):,} records &mdash; type to search the rest.</p>'
            if len(records) > len(visible) else "")

    body = f"""<h1>Employee <span class="now">Salaries</span></h1>
<p class="lede">Search Chesterfield County public-employee pay by name, job title,
or department. Figures are public record.</p>
<p class="meta-line">Source &middot; {_esc(meta['source'])} &middot; as of {_esc(meta['as_of'])} &middot; {meta['count']:,} records</p>

<div class="panel">
  <div class="searchbar">
    <input id="q" type="search" autocomplete="off" placeholder="Search name, title, or department&hellip;" aria-label="Search salaries">
    <span class="count" id="count">{meta['count']:,} records</span>
  </div>
  <table>
    <thead><tr><th>Name</th><th>Title</th><th>Department</th><th style="text-align:right">Salary</th></tr></thead>
    <tbody id="rows">
{rows_html}
    </tbody>
  </table>
  {more}
  <p class="empty" id="empty" hidden>No matching employees.</p>
</div>
<p class="note">Figures reflect annual salary/compensation as released by the
county and are provided for transparency. Spellings and titles follow the source
file. Found an error? <a href="/tip.html">Send a tip</a>.</p>

<script id="data" type="application/json">{payload}</script>
<script>
(function(){{
  var DATA = JSON.parse(document.getElementById('data').textContent);
  var CAP = {_VISIBLE_CAP};
  var q = document.getElementById('q');
  var tbody = document.getElementById('rows');
  var countEl = document.getElementById('count');
  var emptyEl = document.getElementById('empty');
  var moreEl = document.getElementById('moreNote');
  function money(v){{
    var n = parseFloat(String(v).replace(/[$,]/g,''));
    if (isNaN(n)) return v == null ? '' : String(v);
    return '$' + Math.round(n).toLocaleString('en-US');
  }}
  function esc(s){{ var d=document.createElement('div'); d.textContent = s==null?'':String(s); return d.innerHTML; }}
  function render(list){{
    var slice = list.slice(0, CAP);
    tbody.innerHTML = slice.map(function(r){{
      return '<tr><td>'+esc(r.name)+'</td><td>'+esc(r.title)+'</td><td>'+esc(r.dept)+
             '</td><td class="salary">'+esc(money(r.salary))+'</td></tr>';
    }}).join('');
    emptyEl.hidden = list.length !== 0;
    countEl.textContent = list.length.toLocaleString('en-US') + ' records';
    if (moreEl) moreEl.hidden = list.length <= CAP ? true : false;
    if (moreEl && list.length > CAP) moreEl.textContent =
      'Showing first ' + CAP.toLocaleString('en-US') + ' of ' +
      list.length.toLocaleString('en-US') + ' matches — refine your search to narrow down.';
  }}
  var timer;
  q.addEventListener('input', function(){{
    clearTimeout(timer);
    timer = setTimeout(function(){{
      var term = q.value.trim().toLowerCase();
      if (!term) {{ render(DATA); return; }}
      var parts = term.split(/\\s+/);
      var out = DATA.filter(function(r){{
        var hay = ((r.name||'')+' '+(r.title||'')+' '+(r.dept||'')).toLowerCase();
        return parts.every(function(p){{ return hay.indexOf(p) !== -1; }});
      }});
      render(out);
    }}, 90);
  }});
}})();
</script>
"""
    return body


def _render_placeholder() -> str:
    """'Coming soon — here's how to get the data' page (no clean source exists)."""
    return f"""<h1>Employee <span class="now">Salaries</span></h1>
<p class="lede">A searchable lookup of Chesterfield County public-employee pay is
<strong>coming soon</strong>. Salaries are public record &mdash; here's the honest
status and how we'll get the data.</p>
<p class="meta-line">Status &middot; researched {_today()} &middot; no open dataset yet</p>

<div class="panel">
  <h2>Why it's not live yet</h2>
  <p class="note">We checked the obvious sources for a clean, downloadable file of
  individual Chesterfield County employee salaries and came up short:</p>
  <ul class="note">
    <li><strong>Virginia Open Data Portal</strong> &mdash; Chesterfield publishes
      ~70 datasets, but they're all <em>GIS</em> (parcels, zoning, Fire/EMS). No payroll.</li>
    <li><strong>State salary databases</strong> (Auditor of Public Accounts
      &ldquo;Data Point,&rdquo; Richmond Times-Dispatch, OpenTheBooks) cover
      <em>state</em> employees only &mdash; not county or school-division staff.</li>
    <li><strong>County GIS / transparency portals</strong> &mdash; GIS layers only;
      no &ldquo;checkbook&rdquo; or salary-transparency feed.</li>
    <li><strong>Aggregators</strong> (GovSalaries, OpenGovPay) list ~4,375 county
      employees for 2025, but every page and endpoint is bot-walled (HTTP&nbsp;403)
      with no public CSV/JSON/API &mdash; not a stable, license-safe source.</li>
  </ul>
</div>

<div class="panel">
  <h2>How we'll get it (and how you can too)</h2>
  <p class="note">The clean, authoritative path is a <strong>Virginia FOIA
  request</strong> to Chesterfield County for the current payroll extract &mdash;
  employee <em>name, position title, department,</em> and <em>annual salary</em>.
  Any Virginia resident can request it; you don't have to cite the statute.</p>
  <p class="note">Once the county returns a CSV/XLSX, it drops straight into this
  page &mdash; no scraper, no API key &mdash; and this placeholder becomes a live,
  client-side search box over all ~4,000+ records.</p>
  <p>
    <a class="btn" href="https://www.chesterfield.gov/175/Accounting">County Accounting / FOIA</a>
    <a class="btn" href="/tip.html">Have the file? Send it</a>
  </p>
</div>

<p class="note">Figures, when published, will be <strong>public record</strong>
and shown for transparency only.</p>
"""


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def build(out: str = "public/salaries.html") -> Path:
    """Build the salary-lookup page and return its path.

    Renders real data if a FOIA-released dataset is present at
    ``pipeline/salary_data.json`` (or a sibling CSV, which is cached to JSON);
    otherwise renders the documented placeholder. Stdlib-only, keyless.
    """
    out_path = Path(out)
    if not out_path.is_absolute():
        out_path = PROJECT_ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    records, meta = _load_dataset()
    body = _render_lookup(records, meta) if records else _render_placeholder()

    page = _HEAD.replace("__UPDATED__", "Updated " + _now()) + body + \
        _FOOT.replace("__UPDATED__", "Updated " + _now())
    out_path.write_text(page, encoding="utf-8")
    return out_path


if __name__ == "__main__":  # pragma: no cover
    print(build())
