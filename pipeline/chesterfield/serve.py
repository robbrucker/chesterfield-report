"""Local review server — an interactive newsroom for the draft queue.

Stdlib only (http.server). Gives you working buttons that act on the markdown
files: Approve (promote + rebuild the live site), Reject (delete), View full
(read the rendered article), and Edit (per-section textareas -> save).

Run:  python run.py serve        # then open http://localhost:8787
This is a LOCAL, single-user tool — no auth. Don't expose it to the network.
"""
from __future__ import annotations

import datetime
import html
import json
import queue
import re
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import enrich, geo, render
from .render import DRAFTS, PUBLISHED, _md_to_html, _parse_frontmatter, _resolve_map

EDITABLE = {"tldr", "summary", "section", "why"}


# --------------------------------------------------------------------------
# Markdown <-> editable sections
# --------------------------------------------------------------------------

def split_segments(body: str) -> list[dict]:
    """Break a story body into ordered, labeled segments for editing."""
    lines = body.split("\n")
    segs: list[dict] = []
    prose: list[str] = []

    def flush():
        text = "\n".join(prose).strip()
        prose.clear()
        if text:
            segs.append({"kind": "summary", "label": "Summary", "text": text})

    i, n = 0, len(lines)
    while i < n:
        s = lines[i].strip()
        if s.startswith("# "):                      # headline (edited separately)
            i += 1
            continue
        if s.startswith("## "):
            flush()
            label = s[3:].strip()
            j, content = i + 1, []
            while j < n:
                sj = lines[j].strip()
                if (sj.startswith(("## ", "# ", "**Why it matters:**"))
                        or re.match(r"\[Read .*\]\(.*\)", sj)):
                    break                            # let these be their own segments
                content.append(lines[j])
                j += 1
            segs.append({"kind": "section", "label": label,
                         "text": "\n".join(content).strip()})
            i = j
            continue
        if s.startswith("**TL;DR:**"):
            flush()
            segs.append({"kind": "tldr", "label": "TL;DR",
                         "text": s[len("**TL;DR:**"):].strip()})
            i += 1
            continue
        if s.startswith("**Why it matters:**"):
            flush()
            segs.append({"kind": "why", "label": "Why it matters",
                         "text": s[len("**Why it matters:**"):].strip()})
            i += 1
            continue
        if re.match(r"\[Read .*\]\(.*\)", s):
            flush()
            segs.append({"kind": "source", "label": "Source link", "text": s})
            i += 1
            continue
        prose.append(lines[i])
        i += 1
    flush()
    return segs


def join_segments(headline: str, segs: list[dict]) -> str:
    out = [f"# {headline}", ""]
    for seg in segs:
        t, k = seg["text"].strip(), seg["kind"]
        if k == "tldr":
            out += [f"**TL;DR:** {t}", ""]
        elif k == "why":
            out += [f"**Why it matters:** {t}", ""]
        elif k == "section":
            out += [f"## {seg['label']}", "", t, ""]
        else:                                       # summary / source
            out += [t, ""]
    return "\n".join(out).strip() + "\n"


# --------------------------------------------------------------------------
# File helpers
# --------------------------------------------------------------------------

def _safe(name: str) -> Path | None:
    """Resolve a draft filename safely (no path traversal)."""
    p = (DRAFTS / Path(name).name)
    return p if p.exists() and p.suffix == ".md" else None


def _q(s: str) -> str:
    return '"' + (s or "").replace('"', '\\"') + '"'


def _draft_count() -> int:
    return len(list(DRAFTS.glob("*.md")))


# Rejected drafts move here (reversible) instead of being deleted; every review
# decision is logged so the AI editor can be tuned to the human's actual taste.
REMOVED = DRAFTS.parent / "removed"
FEEDBACK_LOG = DRAFTS.parent.parent / "pipeline" / "review_feedback.jsonl"

# Reject reasons surfaced as buttons. Key -> button label. These are the signal
# the human "teaches" us with; the editor rubric can learn from review_feedback.
REJECT_REASONS = [
    ("duplicate", "⧉ Dup"),
    ("boring", "😴 Boring"),
    ("sensitive", "⚠ Sensitive"),
    ("other", "✕ Other"),
]
_REASON_KEYS = {k for k, _ in REJECT_REASONS}


def _log_feedback(meta: dict, action: str, reason: str = "") -> None:
    """Append one review decision to review_feedback.jsonl (best effort)."""
    try:
        rec = {
            "ts": datetime.datetime.now().isoformat(timespec="seconds"),
            "action": action,
            "reason": reason,
            "headline": meta.get("headline", ""),
            "focus": meta.get("focus", ""),
            "source": meta.get("source", ""),
            "license": meta.get("license", ""),
            "ai_verdict": meta.get("ai_verdict", ""),
            "ai_sensitive": meta.get("ai_sensitive", ""),
        }
        FEEDBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
        with FEEDBACK_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:                                # pragma: no cover - best effort
        pass


# --- Debounced background site build ---------------------------------------
# Approving used to rebuild the whole site on every click (slow). Now the click
# just moves the file and returns instantly; the local site is rebuilt once, a
# few seconds after your LAST action, on a background thread — so a fast triage
# session never blocks on rendering. (Deploy still happens via the cron.)
_build_lock = threading.Lock()
_build_timer: threading.Timer | None = None


def _do_build() -> None:
    try:
        render.build_site()
    except Exception as e:                           # pragma: no cover - best effort
        print(f"[serve] background build failed: {e}")


def _schedule_build(delay: float = 3.0) -> None:
    """(Re)arm a single debounced rebuild `delay` seconds from now."""
    global _build_timer
    with _build_lock:
        if _build_timer is not None:
            _build_timer.cancel()
        _build_timer = threading.Timer(delay, _do_build)
        _build_timer.daemon = True
        _build_timer.start()


# --- Background "deepen on approve" worker ---------------------------------
# Many drafts are thin: linkqueue "Candidate" placeholders (no body at all) or
# quick TL;DR+blurb stubs. Publishing one raw puts a near-empty story on the
# live site. So when you approve a thin story we publish it instantly (the card
# flies away) and hand it to a single background worker that web-researches it
# into a full article, then triggers a rebuild. One worker, sequential, so we
# never hammer the CLI even if you approve a whole batch at once.
_deepen_q: "queue.Queue[Path]" = queue.Queue()
_deepen_started = False
_deepen_started_lock = threading.Lock()


def _is_stub(path: Path) -> bool:
    """A published file with no long-form body yet (needs deepening)."""
    try:
        _, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
    except OSError:
        return False
    return "## The story" not in body


def _deepen_published(path: Path) -> None:
    """Web-research a published stub into a full article, in place."""
    meta, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
    headline = meta.get("headline") or path.stem
    summary = next((ln for ln in body.splitlines()
                    if ln and not ln.startswith(("#", "*", "["))), "")
    topic = f"{headline}\n\nContext: {summary}\nSource: {meta.get('source_url','')}"
    data = enrich.write_article(topic, model="claude-haiku-4-5")
    render.write_full_article(path, data)
    loc = (data.get("location") or "").strip()
    if loc:
        upd = {"location": _q(loc)}
        g = geo.geocode(loc)
        if g:
            upd["lat"], upd["lon"] = g["lat"], g["lon"]
        render.update_frontmatter(path, upd)


def _deepen_loop() -> None:
    while True:
        path = _deepen_q.get()
        try:
            if path.exists() and _is_stub(path):
                print(f"[serve] deepening {path.name} …")
                _deepen_published(path)
                print(f"[serve] deepened {path.name}")
        except Exception as e:                       # pragma: no cover - best effort
            print(f"[serve] deepen failed for {path.name}: {e}")
        finally:
            _schedule_build()                        # rebuild whether it worked or not
            _deepen_q.task_done()


def _ensure_deepen_worker() -> None:
    global _deepen_started
    with _deepen_started_lock:
        if not _deepen_started:
            threading.Thread(target=_deepen_loop, daemon=True).start()
            _deepen_started = True


def do_approve(name: str) -> bool:
    """Publish a draft. If it's a thin stub, queue it for background deepening.
    Returns True when a background deepen was queued (so the UI can say so)."""
    p = _safe(name)
    if not p:
        return False
    raw = p.read_text(encoding="utf-8")
    meta, _ = _parse_frontmatter(raw)
    _log_feedback(meta, "approve")
    text = raw.replace("status: draft", "status: published", 1)
    PUBLISHED.mkdir(parents=True, exist_ok=True)
    dest = PUBLISHED / p.name
    dest.write_text(text, encoding="utf-8")
    p.unlink()
    if _is_stub(dest):
        _ensure_deepen_worker()
        _deepen_q.put(dest)                          # worker deepens, then rebuilds
        return True
    _schedule_build()                                # already a full article — just rebuild
    return False


def do_reject(name: str, reason: str = "other") -> None:
    p = _safe(name)
    if not p:
        return
    reason = reason if reason in _REASON_KEYS else "other"
    meta, _ = _parse_frontmatter(p.read_text(encoding="utf-8"))
    _log_feedback(meta, "reject", reason)
    REMOVED.mkdir(parents=True, exist_ok=True)
    p.rename(REMOVED / p.name)                       # reversible; stays "seen" in the DB


def do_save(name: str, form: dict) -> None:
    p = _safe(name)
    if not p:
        return
    text = p.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(text)
    segs = split_segments(body)
    for i, seg in enumerate(segs):
        key = f"seg_{i}"
        if seg["kind"] in EDITABLE and key in form:
            seg["text"] = form[key]
    headline = form.get("headline", meta.get("headline", ""))
    new_body = join_segments(headline, segs)
    fm_block = text.split("---", 2)[1] if text.startswith("---") else ""
    p.write_text(f"---{fm_block}---\n\n{new_body}", encoding="utf-8")
    render.update_frontmatter(p, {
        "headline": _q(headline),
        "location": _q(form.get("location", meta.get("location", ""))),
        "focus": f"[{form.get('focus', '')}]",
    })


def do_deepen(name: str) -> str:
    """Run the web-grounded full-article generation. Returns a status note."""
    p = _safe(name)
    if not p:
        return "not found"
    meta, body = _parse_frontmatter(p.read_text(encoding="utf-8"))
    headline = meta.get("headline") or p.stem
    summary = next((ln for ln in body.splitlines()
                    if ln and not ln.startswith(("#", "*", "["))), "")
    topic = f"{headline}\n\nContext: {summary}\nSource: {meta.get('source_url','')}"
    data = enrich.write_article(topic, model="claude-haiku-4-5")
    render.write_full_article(p, data)
    loc = (data.get("location") or "").strip()
    if loc:
        upd = {"location": _q(loc)}
        g = geo.geocode(loc)
        if g:
            upd["lat"], upd["lon"] = g["lat"], g["lon"]
        render.update_frontmatter(p, upd)
    return "ok"


# --------------------------------------------------------------------------
# HTML
# --------------------------------------------------------------------------

CSS = """
:root{
  --teal-deep:#003e51; --teal:#23978a; --green:#6fae34; --indigo:#4e5b94;
  --gold:#d8a23a; --red:#c0492b;
  --bg:#f5f7f6; --card:#ffffff; --ink:#102a33; --muted:#5a6a70;
  --line:#e2e8e7; --line-soft:#eef2f1;
  --serif:'Fraunces',Georgia,'Times New Roman',serif;
  --sans:'Source Sans 3',system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
  --shadow:0 1px 2px rgba(16,42,51,.05),0 6px 20px rgba(16,42,51,.06);
  --shadow-hover:0 4px 8px rgba(16,42,51,.08),0 14px 34px rgba(16,42,51,.12);
  --radius:16px; --wrap:1100px;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.65 var(--sans);-webkit-font-smoothing:antialiased}
a{color:var(--teal)}
:focus-visible{outline:3px solid var(--teal);outline-offset:2px;border-radius:6px}

/* ---- App bar ---- */
.appbar{position:sticky;top:0;z-index:50;background:var(--teal-deep);color:#fff;
  box-shadow:0 2px 12px rgba(0,62,81,.25)}
.appbar-in{max-width:var(--wrap);margin:0 auto;padding:.85rem 1.25rem;
  display:flex;align-items:center;gap:1.25rem;flex-wrap:wrap}
.brand{display:flex;flex-direction:column;line-height:1.15}
.brand .wordmark{font-family:var(--serif);font-weight:700;font-size:1.45rem;letter-spacing:-.01em}
.brand .wordmark .now{color:var(--green)}
.brand .tag{font-size:.66rem;color:#bcd3d9;font-weight:500;letter-spacing:.01em;margin-top:.1rem}
.count{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);
  color:#eaf4f3;font-weight:700;font-size:.78rem;padding:.25rem .7rem;border-radius:999px;white-space:nowrap}
.appbar nav{margin-left:auto;display:flex;gap:1.1rem;align-items:center;flex-wrap:wrap}
.appbar nav a{color:#d5e7ea;font-weight:600;font-size:.9rem;text-decoration:none;padding:.3rem .1rem;
  border-bottom:2px solid transparent;transition:color .15s,border-color .15s}
.appbar nav a:hover{color:#fff;border-color:var(--green)}

/* ---- Layout ---- */
main{max-width:var(--wrap);margin:0 auto;padding:1.5rem 1.25rem 4rem}
.bar{display:flex;align-items:baseline;gap:.6rem;margin:.25rem 0 1.4rem;
  font-family:var(--serif);font-size:1.5rem;font-weight:600;color:var(--teal-deep)}
.bar small{font-family:var(--sans);font-size:.85rem;font-weight:500;color:var(--muted);letter-spacing:0}
.empty{background:var(--card);border:1px dashed var(--line);border-radius:var(--radius);
  padding:3rem 1.5rem;text-align:center;color:var(--muted);box-shadow:var(--shadow)}

/* ---- Grid + cards ---- */
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1.25rem}
@media(max-width:760px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
  overflow:hidden;box-shadow:var(--shadow);display:flex;flex-direction:column;
  transition:box-shadow .2s,transform .2s}
.card:hover{box-shadow:var(--shadow-hover);transform:translateY(-2px)}
.card-body{padding:1.1rem 1.25rem 1.25rem;display:flex;flex-direction:column;flex:1}
.fname{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.7rem;
  color:var(--muted);margin-bottom:.55rem;letter-spacing:.01em}
.meta{color:var(--muted);font-size:.76rem;text-transform:uppercase;letter-spacing:.05em;
  font-weight:700;margin:.15rem 0 .4rem}
.card h2{font-family:var(--serif);font-size:1.32rem;line-height:1.2;margin:.15rem 0 .55rem;color:var(--teal-deep)}
.card h2 a{color:inherit;text-decoration:none}
.card h2 a:hover{color:var(--teal)}
.chips{display:flex;flex-wrap:wrap;gap:.35rem;margin:.1rem 0 .6rem}
.tldr{color:#33484f;font-size:.95rem;margin:.2rem 0 .9rem;flex:1}
.tldr .lab{font-weight:800;color:var(--teal);font-size:.72rem;text-transform:uppercase;
  letter-spacing:.06em;margin-right:.35rem}

/* ---- Chips ---- */
.chip{display:inline-flex;align-items:center;font-size:.68rem;font-weight:700;
  padding:.2rem .6rem;border-radius:999px;text-transform:uppercase;letter-spacing:.04em;
  background:#eef2f1;color:#3a4a4f;border:1px solid rgba(0,0,0,.04)}
.chip[data-f="growth"]{background:#e7f1ee;color:#1c6e60}
.chip[data-f="schools"]{background:#eef0f8;color:#3b477b}
.chip[data-f="police"]{background:#e6eef2;color:#1f5468}
.chip[data-f="fire"]{background:#fbeae2;color:#a3401f}
.chip[data-f="business"]{background:#f6efdc;color:#8a6a16}
.chip[data-f="government"]{background:#eceef6;color:#404d80}
.chip[data-f="community"]{background:#eaf3df;color:#4d7521}
.chip[data-f="weather"]{background:#fbf0e0;color:#9a6a12}
.chip.video{background:var(--teal-deep);color:#fff;border-color:transparent}

/* ---- Media / hero ---- */
.media{display:block;margin:0;background:#dfe7e6;position:relative;width:100%;
  aspect-ratio:16/9;overflow:hidden}
.media.hero{aspect-ratio:16/9}
.media img{width:100%;height:100%;object-fit:cover;display:block}
.card .media{border-radius:0}
.view-hero .media,.view-hero{border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow);margin-bottom:1.25rem}
.media.is-video{cursor:pointer;text-decoration:none}
.media.is-video::after{content:"";position:absolute;inset:0;
  background:linear-gradient(180deg,rgba(0,62,81,0) 40%,rgba(0,62,81,.35));transition:background .2s}
.media.is-video:hover::after{background:linear-gradient(180deg,rgba(0,62,81,.05) 30%,rgba(0,62,81,.5))}
.playbadge{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
  width:64px;height:64px;border-radius:50%;background:rgba(255,255,255,.92);color:var(--teal-deep);
  display:flex;align-items:center;justify-content:center;font-size:1.5rem;padding-left:.18rem;
  box-shadow:0 6px 18px rgba(0,0,0,.3);z-index:2;transition:transform .15s}
.media.is-video:hover .playbadge{transform:translate(-50%,-50%) scale(1.08)}
.media-empty{width:100%;aspect-ratio:16/9;background:
  linear-gradient(135deg,#eef3f2,#e1ebe9);display:flex;align-items:center;justify-content:center;
  color:#9fb2b1;font-family:var(--serif);font-size:1.4rem;letter-spacing:.02em}
.media-empty span{opacity:.7}

/* ---- Action row ---- */
.actions{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin-top:auto;padding-top:.4rem}
button,.btn{font:inherit;font-weight:600;font-size:.86rem;border:1px solid var(--line);
  border-radius:10px;padding:.5rem .9rem;cursor:pointer;background:#fff;color:var(--teal-deep);
  text-decoration:none;display:inline-flex;align-items:center;gap:.35rem;
  transition:background .15s,box-shadow .15s,transform .05s,border-color .15s}
.btn:hover,button:hover{background:var(--line-soft);border-color:#cfdad8}
.btn:active,button:active{transform:translateY(1px)}
.btn-approve{background:var(--green);color:#fff;border-color:var(--green)}
.btn-approve:hover{background:#62a02b;border-color:#62a02b}
.btn-reject{background:#fff;color:var(--red);border-color:#e6c4bb}
.btn-reject:hover{background:var(--red);color:#fff;border-color:var(--red)}
.btn-sm{font-size:.76rem;padding:.4rem .6rem;border-radius:8px}
.rgroup{display:inline-flex;gap:.3rem;flex-wrap:wrap;padding:.15rem .35rem;
  border:1px dashed var(--line);border-radius:12px;background:#fcfaf9}
.btn-deepen{background:var(--gold);color:#3a2a00;border-color:var(--gold)}
.btn-deepen:hover{background:#c9941f;border-color:#c9941f}
.btn-link{background:transparent;border-color:transparent;color:var(--teal);padding-left:.5rem;padding-right:.5rem}
.btn-link:hover{background:var(--line-soft);color:var(--teal-deep)}
form.inline{display:inline-flex;margin:0}

/* ---- View page ---- */
.view-wrap{max-width:780px;margin:0 auto}
.actionbar{position:sticky;top:64px;z-index:20;background:rgba(245,247,246,.9);
  backdrop-filter:blur(6px);border:1px solid var(--line);border-radius:14px;
  padding:.55rem .7rem;margin-bottom:1.25rem;box-shadow:var(--shadow)}
.article{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
  padding:1.75rem 1.9rem;box-shadow:var(--shadow)}
.article h1{font-family:var(--serif);color:var(--teal-deep);font-size:2rem;line-height:1.15;margin:.2rem 0 .8rem}
.article h2{font-family:var(--serif);color:var(--teal-deep);font-size:1.45rem;margin:1.6rem 0 .5rem}
.article h3{font-family:var(--serif);color:var(--teal);font-size:1.15rem;margin:1.3rem 0 .4rem}
.article p{margin:.7rem 0}
.article a{color:var(--teal);text-underline-offset:2px}
.article blockquote{border-left:4px solid var(--teal);background:#eef6f4;
  margin:1rem 0;padding:.6rem 1rem;border-radius:0 8px 8px 0;color:#2c4147}
.article img{max-width:100%;border-radius:10px}
.case{padding:.85rem 1.1rem;border-radius:10px;border-left:4px solid;margin:.7rem 0}
.case.for{background:rgba(111,174,52,.09);border-color:var(--green)}
.case.against{background:rgba(192,73,43,.07);border-color:var(--red)}
.map-embed{margin:1.1rem 0}
.map-embed iframe{width:100%;aspect-ratio:16/9;border:1px solid var(--line);border-radius:12px}

/* ---- Edit form ---- */
.editform{max-width:760px;margin:0 auto}
.field{background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:1rem 1.15rem;margin-bottom:.9rem;box-shadow:var(--shadow)}
label{display:block;font-weight:700;font-size:.74rem;text-transform:uppercase;letter-spacing:.05em;
  color:var(--teal);margin:0 0 .45rem}
input[type=text],textarea{width:100%;font:inherit;padding:.6rem .75rem;border:1px solid var(--line);
  border-radius:9px;background:#fbfdfc;color:var(--ink);transition:border-color .15s,box-shadow .15s}
input[type=text]:focus,textarea:focus{outline:none;border-color:var(--teal);
  box-shadow:0 0 0 3px rgba(35,151,138,.15)}
textarea{min-height:5rem;resize:vertical;line-height:1.55}
.savebar{position:sticky;bottom:0;background:rgba(245,247,246,.92);backdrop-filter:blur(6px);
  border-top:1px solid var(--line);margin:1.2rem -1.25rem -4rem;padding:1rem 1.25rem;
  display:flex;gap:.6rem;align-items:center}
.savebar .editing{margin-right:auto;color:var(--muted);font-size:.82rem;font-family:ui-monospace,monospace}

/* ---- Toast ---- */
.toast{position:fixed;left:50%;bottom:1.5rem;transform:translateX(-50%) translateY(1rem);
  background:var(--teal-deep);color:#fff;font-weight:600;font-size:.9rem;
  padding:.6rem 1.1rem;border-radius:999px;box-shadow:0 8px 28px rgba(0,62,81,.35);
  opacity:0;pointer-events:none;transition:opacity .2s,transform .2s;z-index:200}
.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
"""

PAGE = """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>{title}</title>
<link rel=preconnect href="https://fonts.googleapis.com">
<link rel=preconnect href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Source+Sans+3:wght@400;500;600;700;800&display=swap" rel=stylesheet>
<style>{css}</style></head><body>
<div class=appbar><div class=appbar-in>
<div class=brand><span class=wordmark>The Chesterfield<span class=now> Report</span></span>
<span class=tag>Independent local news · not affiliated with Chesterfield County government.</span></div>
{count}
<nav><a href="/">All drafts</a><a href="http://localhost:8000/" target=_blank rel=noopener>Live site ↗</a></nav>
</div></div><main>{body}</main><div id=toast class=toast></div><script>{script}</script></body></html>"""


# Progressive-enhancement script: turn Approve/Reject into instant fetch() calls
# so the card animates away with no full-page reload (and no site rebuild on the
# click path). Forms keep working as plain POSTs if JS is disabled.
SCRIPT = r"""
function toast(msg){var t=document.getElementById('toast');if(!t)return;
 t.textContent=msg;t.classList.add('show');clearTimeout(t._h);
 t._h=setTimeout(function(){t.classList.remove('show')},1600);}
function setCount(n){
 document.querySelectorAll('.count').forEach(function(e){e.textContent=n+' in queue';});
 var s=document.querySelector('.bar small');
 if(s)s.textContent=n+(n===1?' story':' stories')+' awaiting review';
 if(n===0){var g=document.querySelector('.grid');
  if(g)g.outerHTML='<div class=empty><p style="font-family:var(--serif);font-size:1.3rem;color:var(--teal-deep)">All clear ✓</p><p>Queue empty. New stories appear here as the pipeline runs.</p></div>';}}
document.addEventListener('submit',function(e){
 var form=e.target;if(!form.classList||!form.classList.contains('act'))return;
 e.preventDefault();
 var c=form.getAttribute('data-confirm');if(c&&!confirm(c.replace(/&amp;/g,'&')))return;
 var card=form.closest('article.card');
 if(card){card.style.pointerEvents='none';card.style.opacity='.45';}
 fetch(form.getAttribute('action'),{method:'POST',
   headers:{'X-Requested-With':'fetch','Content-Type':'application/x-www-form-urlencoded'},
   body:new URLSearchParams(new FormData(form))})
 .then(function(r){return r.json();})
 .then(function(j){
   if(!j||!j.ok)throw new Error('failed');
   var approved=form.getAttribute('action').indexOf('approve')>=0;
   var rsn=form.getAttribute('data-reason');
   var msg=approved?(j.deepening?'✓ Approved — writing full article…':'✓ Approved — publishing')
     :('✕ Rejected'+(rsn&&rsn!=='other'?' · '+rsn:''));
   if(card){card.style.transition='opacity .25s,transform .25s';
     card.style.opacity='0';card.style.transform='scale(.96)';
     setTimeout(function(){card.remove();},240);
     setCount(j.remaining);toast(msg);}
   else{window.location='/';}                 // view page: go back to the queue
 })
 .catch(function(){if(card){card.style.pointerEvents='';card.style.opacity='1';}
   toast('⚠ Action failed');});
});
"""


def _esc(s: str) -> str:
    return html.escape(s or "")


def page(title: str, body: str, count: int | None = None) -> bytes:
    badge = f'<span class=count>{count} in queue</span>' if count is not None else ""
    return PAGE.format(title=title, css=CSS, body=body, count=badge,
                       script=SCRIPT).encode("utf-8")


# Map each focus area to a chip color key (used as data-f="...").
_FOCUS_KEYS = {
    "growth & development": "growth", "growth and development": "growth",
    "schools": "schools", "police": "police",
    "fire & ems": "fire", "fire and ems": "fire",
    "local business": "business", "business": "business",
    "government": "government", "community": "community",
    "weather & safety": "weather", "weather and safety": "weather",
}


def _focus_key(label: str) -> str:
    return _FOCUS_KEYS.get(label.strip().lower(), "")


def _chips(meta: dict) -> str:
    """Category color chips plus a small video badge for video items."""
    focus = meta.get("focus", "").strip("[]")
    out = []
    if (meta.get("media_kind") or "").strip() == "video" or (meta.get("video_url") or "").strip():
        out.append('<span class="chip video">▶ Video</span>')
    for l in focus.split(","):
        label = l.strip()
        if not label:
            continue
        key = _focus_key(label)
        attr = f' data-f="{key}"' if key else ""
        out.append(f'<span class="chip"{attr}>{_esc(label)}</span>')
    return "".join(out)


def _tldr_of(body: str) -> str:
    m = re.search(r"\*\*TL;DR:\*\*\s*(.+)", body)
    return m.group(1).strip() if m else ""


def _hero(meta: dict, big: bool = True) -> str:
    """Hero media block, with a graceful placeholder when there's no media."""
    h = render.media_html(meta, big=big)
    if h:
        return h
    return '<div class="media media-empty" aria-hidden="true"><span>The Chesterfield Report</span></div>'


def _verdict_badge(meta: dict) -> str:
    """Show the AI editor's verdict (review/reject) + reason on a draft card."""
    v = (meta.get("ai_verdict") or "").strip().lower()
    if v not in ("review", "reject", "approve"):
        return ""
    reason = _esc(meta.get("ai_verdict_reason", ""))
    sens = (meta.get("ai_sensitive", "") or "").strip().lower() in ("true", "1", "yes")
    styles = {
        "review": ("#b8860b", "rgba(216,162,58,.14)",
                   "⚑ Flagged for review" + (" · sensitive" if sens else "")),
        "reject": ("#c0492b", "rgba(192,73,43,.12)", "✕ AI suggests reject"),
        "approve": ("#1f6b53", "rgba(31,107,83,.12)", "✓ AI approved"),
    }
    color, bg, label = styles[v]
    tail = f' <span style="font-weight:400;opacity:.85">— {reason}</span>' if reason else ""
    return (f'<div style="background:{bg};color:{color};border:1px solid {color}33;'
            f'border-radius:8px;padding:.35rem .6rem;font-size:.78rem;font-weight:700;'
            f'margin:.1rem 0 .55rem">{label}{tail}</div>')


def _reject_buttons(n: str) -> str:
    """The reason-tagged reject buttons (the human's teaching signal)."""
    out = []
    for key, label in REJECT_REASONS:
        out.append(
            f'<form class="inline act" data-reason="{key}" method=post action="/reject">'
            f'<input type=hidden name=f value="{n}">'
            f'<input type=hidden name=reason value="{key}">'
            f'<button class="btn-reject btn-sm" type=submit>{label}</button></form>'
        )
    return f'<span class=rgroup>{"".join(out)}</span>'


def list_page() -> bytes:
    drafts = sorted(DRAFTS.glob("*.md"), reverse=True)
    n_drafts = len(drafts)
    head = (f'<div class=bar>Draft queue '
            f'<small>{n_drafts} {"story" if n_drafts == 1 else "stories"} awaiting review</small></div>')
    if not drafts:
        body = (head + '<div class=empty><p style="font-family:var(--serif);font-size:1.3rem;'
                'color:var(--teal-deep)">All clear ✓</p>'
                '<p>No drafts are waiting. New stories will appear here as the pipeline runs.</p></div>')
        return page("Review drafts", body, count=0)

    cards = []
    for p in drafts:
        meta, body = _parse_frontmatter(p.read_text(encoding="utf-8"))
        n = _esc(p.name)
        tldr = _esc(_tldr_of(body))
        tldr_html = (f'<p class=tldr><span class=lab>TL;DR</span>{tldr}</p>'
                     if tldr else '<p class=tldr></p>')
        cards.append(
            f'<article class=card>{_hero(meta)}'
            f'<div class=card-body>'
            f'<div class=fname>{n}</div>'
            f'<div class=chips>{_chips(meta)}</div>'
            f'{_verdict_badge(meta)}'
            f'<h2><a href="/view?f={n}">{_esc(meta.get("headline",""))}</a></h2>'
            f'<div class=meta>{_esc(meta.get("source",""))} · {_esc(meta.get("published","")[:10])}</div>'
            f'{tldr_html}'
            f'<div class=actions>'
            f'<form class="inline act" method=post action="/approve"><input type=hidden name=f value="{n}">'
            f'<button class=btn-approve type=submit>✓ Approve</button></form>'
            f'{_reject_buttons(n)}'
            f'<a class="btn btn-link" href="/view?f={n}">View</a>'
            f'<a class="btn btn-link" href="/edit?f={n}">Edit</a>'
            f'</div></div></article>'
        )
    return page("Review drafts", head + f'<div class=grid>{"".join(cards)}</div>', count=n_drafts)


def view_page(name: str) -> bytes:
    p = _safe(name)
    if not p:
        return page("Not found", "<p>Draft not found. <a href=/>Back</a></p>")
    meta, body = _parse_frontmatter(p.read_text(encoding="utf-8"))
    story = _md_to_html(body)
    m = _resolve_map(meta)
    if m and "</h2>" in story:
        story = story.replace("</h2>", "</h2>" + m, 1)
    elif m:
        story += m
    n = _esc(p.name)
    actions = (
        f'<div class=actions>'
        f'<form class="inline act" method=post action="/approve"><input type=hidden name=f value="{n}">'
        f'<button class=btn-approve type=submit>✓ Approve</button></form>'
        f'{_reject_buttons(n)}'
        f'<form class=inline method=post action="/deepen"><input type=hidden name=f value="{n}">'
        f'<button class=btn-deepen type=submit>★ Generate full article (web research)</button></form>'
        f'<a class="btn btn-link" href="/edit?f={n}">Edit sections</a>'
        f'</div>'
    )
    body = (
        f'<div class=view-wrap>'
        f'<div class=fname>{n}</div>'
        f'<div class=chips style="margin:.2rem 0 .9rem">{_chips(meta)}</div>'
        f'<div class=view-hero>{_hero(meta)}</div>'
        f'<div class=actionbar>{actions}</div>'
        f'<article class=article>{story}</article>'
        f'<div style="margin-top:1.25rem">{actions}</div>'
        f'</div>'
    )
    return page(meta.get("headline", "Draft"), body)


def edit_page(name: str) -> bytes:
    p = _safe(name)
    if not p:
        return page("Not found", "<p>Draft not found. <a href=/>Back</a></p>")
    meta, body = _parse_frontmatter(p.read_text(encoding="utf-8"))
    segs = split_segments(body)
    fields = [
        f'<div class=field><label>Headline</label>'
        f'<input type=text name=headline value="{_esc(meta.get("headline",""))}"></div>',
        f'<div class=field><label>Location (for the map)</label>'
        f'<input type=text name=location value="{_esc(meta.get("location",""))}"></div>',
        f'<div class=field><label>Focus (comma-separated)</label>'
        f'<input type=text name=focus value="{_esc(meta.get("focus","").strip("[]"))}"></div>',
    ]
    for i, seg in enumerate(segs):
        if seg["kind"] not in EDITABLE:
            continue
        rows = 2 if seg["kind"] in ("tldr", "why") else 6
        fields.append(
            f'<div class=field><label>{_esc(seg["label"])}</label>'
            f'<textarea name=seg_{i} rows={rows}>{_esc(seg["text"])}</textarea></div>'
        )
    n = _esc(p.name)
    form = (
        f'<div class=editform>'
        f'<div class=bar>Edit sections '
        f'<small>{_esc(meta.get("headline",""))}</small></div>'
        f'<form method=post action="/save"><input type=hidden name=f value="{n}">'
        + "".join(fields)
        + f'<div class=savebar><span class=editing>{n}</span>'
          '<a class="btn btn-link" href="/view?f=' + n + '">Cancel</a>'
          '<button class=btn-approve type=submit>✓ Save changes</button></div></form>'
        f'</div>'
    )
    return page("Edit · " + meta.get("headline", ""), form)


# --------------------------------------------------------------------------
# HTTP handler
# --------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):           # quieter console
        pass

    def _send(self, body: bytes, code: int = 200, ctype: str = "text/html; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, to: str):
        self.send_response(303)
        self.send_header("Location", to)
        self.end_headers()

    def _json(self, obj: dict, code: int = 200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _is_ajax(self) -> bool:
        return self.headers.get("X-Requested-With", "") == "fetch"

    def _form(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8")
        return {k: v[0] for k, v in urllib.parse.parse_qs(raw).items()}

    def _query(self) -> dict:
        q = urllib.parse.urlparse(self.path).query
        return {k: v[0] for k, v in urllib.parse.parse_qs(q).items()}

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/":
            self._send(list_page())
        elif path == "/view":
            self._send(view_page(self._query().get("f", "")))
        elif path == "/edit":
            self._send(edit_page(self._query().get("f", "")))
        else:
            self._send(b"Not found", 404, "text/plain")

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        form = self._form()
        name = form.get("f", "")
        if path == "/approve":
            deepening = do_approve(name)
            if self._is_ajax():
                self._json({"ok": True, "remaining": _draft_count(),
                            "deepening": deepening})
            else:
                self._redirect("/")
        elif path == "/reject":
            do_reject(name, form.get("reason", "other"))
            if self._is_ajax():
                self._json({"ok": True, "remaining": _draft_count()})
            else:
                self._redirect("/")
        elif path == "/save":
            do_save(name, form)
            self._redirect(f"/view?f={urllib.parse.quote(name)}")
        elif path == "/deepen":
            try:
                do_deepen(name)
            except Exception as e:
                self._send(page("Error", f"<p>Full-article generation failed: {_esc(str(e))}</p>"
                                         f"<p><a href=/>Back</a></p>"), 500)
                return
            self._redirect(f"/view?f={urllib.parse.quote(name)}")
        else:
            self._send(b"Not found", 404, "text/plain")


def serve(port: int = 8787) -> None:
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Review server: http://localhost:{port}   (Ctrl-C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
