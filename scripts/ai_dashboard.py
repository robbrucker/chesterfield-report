#!/usr/bin/env python3
"""Chesterfield Report — pipeline ops dashboard.

A stdlib-only web console to watch the news pipeline and control its AI:
  * AI feature toggles (on/off) + pause-all, reading/writing ai_features.json
  * AI usage: calls per day, split by model (haiku vs sonnet)
  * Pipeline health: last ingest/deploy, drafts awaiting review, published count,
    next scheduled run
  * Activity feed from the ingest cron log
  * Fact-check alerts (research/wiki/QA-ALERTS.md)
  * Recently published stories

Reads the same files the gateway (chesterfield/ai.py) uses. Auth is handled by
the reverse proxy (Caddy basic_auth) in front, so this binds to the container
network only. No external deps.

Env: DATA_DIR (/data/pipeline), LOGS_DIR (/data/logs), SCRIPTS_DIR (/data/scripts),
     CONTENT_DIR (/data/content), WIKI_DIR (/data/research/wiki), PORT (8080).
"""
import json
import os
import re
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data/pipeline"))
LOGS_DIR = Path(os.environ.get("LOGS_DIR", "/data/logs"))
SCRIPTS_DIR = Path(os.environ.get("SCRIPTS_DIR", "/data/scripts"))
CONTENT_DIR = Path(os.environ.get("CONTENT_DIR", "/data/content"))
WIKI_DIR = Path(os.environ.get("WIKI_DIR", "/data/research/wiki"))
PORT = int(os.environ.get("PORT", "8080"))

FEATURES = ["enrich", "triage", "qa", "factcheck", "translate",
            "events", "cases", "farmers", "meetings", "apartments"]
FEATURE_CONFIG = DATA_DIR / "ai_features.json"
USAGE_LOG = DATA_DIR / "ai_usage.log"
INGEST_HOURS = [0, 4, 8, 12, 16, 20]   # ingest cron cadence (UTC)


# --------------------------------------------------------------------------- #
# Data helpers
# --------------------------------------------------------------------------- #
def _load_features() -> dict:
    try:
        cfg = json.loads(FEATURE_CONFIG.read_text(encoding="utf-8"))
    except Exception:
        cfg = {}
    return {f: bool(cfg.get(f, True)) for f in FEATURES}


def _save_features(cfg: dict) -> None:
    merged = {}
    try:
        merged = json.loads(FEATURE_CONFIG.read_text(encoding="utf-8"))
    except Exception:
        pass
    merged.update({k: bool(v) for k, v in cfg.items()})
    FEATURE_CONFIG.write_text(json.dumps(merged, indent=2, sort_keys=True) + "\n",
                              encoding="utf-8")


def _usage(days: int):
    """Return (by_day{date:{feature:n}}, by_day_model{date:{model:n}})."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    by_feat, by_model = {}, {}
    try:
        for line in USAGE_LOG.read_text(encoding="utf-8").splitlines():
            p = line.split("\t")
            if len(p) < 2:
                continue
            day = p[0][:10]
            if day < cutoff:
                continue
            feat = p[1]
            model = p[2] if len(p) > 2 else "?"
            by_feat.setdefault(day, {}).setdefault(feat, 0)
            by_feat[day][feat] += 1
            tier = "sonnet" if "sonnet" in model else ("haiku" if "haiku" in model else "other")
            by_model.setdefault(day, {}).setdefault(tier, 0)
            by_model[day][tier] += 1
    except Exception:
        pass
    return by_feat, by_model


def _fm(path: Path) -> dict:
    """Minimal frontmatter parse: key: value pairs between the first --- fences."""
    out = {}
    try:
        txt = path.read_text(encoding="utf-8")
    except Exception:
        return out
    if not txt.startswith("---"):
        return out
    end = txt.find("\n---", 3)
    block = txt[3:end] if end > 0 else ""
    for line in block.splitlines():
        m = re.match(r"^([a-z_]+):\s*(.*)$", line.strip())
        if m:
            out[m.group(1)] = m.group(2).strip().strip('"')
    return out


def _health() -> dict:
    drafts = list((CONTENT_DIR / "drafts").glob("*.md")) if (CONTENT_DIR / "drafts").exists() else []
    awaiting = 0
    for d in drafts:
        fm = _fm(d)
        if fm.get("ai_verdict", "") in ("review", ""):
            awaiting += 1
    pub = list((CONTENT_DIR / "published").glob("*.md")) if (CONTENT_DIR / "published").exists() else []

    log = _tail(LOGS_DIR / "ingest.log", 20000)
    last_start = last_deploy = ""
    for line in log.splitlines():
        if "pipeline start" in line:
            last_start = line.split(" =====")[0].strip()
        if "deploy OK" in line or "deploy FAILED" in line:
            last_deploy = line.strip()

    now = datetime.now(timezone.utc)
    nxt = None
    for h in INGEST_HOURS:
        cand = now.replace(hour=h, minute=0, second=0, microsecond=0)
        if cand > now:
            nxt = cand
            break
    if nxt is None:
        nxt = (now + timedelta(days=1)).replace(hour=INGEST_HOURS[0], minute=0, second=0, microsecond=0)
    mins = int((nxt - now).total_seconds() // 60)

    return {
        "drafts_awaiting": awaiting,
        "drafts_total": len(drafts),
        "published": len(pub),
        "last_ingest": last_start or "—",
        "last_deploy": last_deploy or "—",
        "next_run": nxt.strftime("%H:%M UTC") + f" (in {mins//60}h {mins%60}m)",
    }


def _tail(path: Path, n: int = 6000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[-n:]
    except Exception:
        return ""


def _activity(n: int = 12) -> list:
    out = []
    for line in _tail(LOGS_DIR / "ingest.log", 20000).splitlines():
        if any(k in line for k in ("pipeline start", "building (", "no-op", "deploy OK",
                                    "deploy FAILED", "no published changes",
                                    "STORM GUARD", "budget", "reached")):
            out.append(line.strip())
    return out[-n:][::-1]


def _fb_status() -> str:
    try:
        day = (SCRIPTS_DIR / ".fb_posted").read_text(encoding="utf-8").strip()
    except Exception:
        return "unknown"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return ("posted today ✓" if day == today else f"last {day}")


def _alerts() -> dict:
    txt = _tail(WIKI_DIR / "QA-ALERTS.md", 12000)
    if not txt:
        return {"count": 0, "items": [], "updated": ""}
    m = re.search(r"(\d+)\s+stories need review", txt)
    count = int(m.group(1)) if m else 0
    mu = re.search(r"_Updated ([^._]+)", txt)
    items = re.findall(r"^##\s+(.+)$", txt, re.M)[:8]
    return {"count": count, "items": items, "updated": (mu.group(1).strip() if mu else "")}


def _recent_stories(n: int = 8) -> list:
    pdir = CONTENT_DIR / "published"
    if not pdir.exists():
        return []
    files = sorted(pdir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:n]
    out = []
    for f in files:
        fm = _fm(f)
        out.append({
            "headline": fm.get("headline", f.stem),
            "date": (fm.get("published", "") or "")[:10],
            "focus": fm.get("focus", ""),
        })
    return out


def _status() -> dict:
    feats = _load_features()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    by_feat, by_model = _usage(14)
    return {
        "features": feats,
        "all_off": not any(feats.values()),
        "budget": int(os.environ.get("CR_AI_BUDGET", "400")),
        "usage": by_feat,
        "usage_model": by_model,
        "today_total": sum(by_feat.get(today, {}).values()),
        "health": _health(),
        "activity": _activity(),
        "alerts": _alerts(),
        "recent": _recent_stories(),
        "fb": _fb_status(),
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


# --------------------------------------------------------------------------- #
# Page
# --------------------------------------------------------------------------- #
PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Chesterfield Report — Ops</title>
<style>
  :root{--bg:#0d1117;--card:#161b22;--card2:#1c232c;--line:#2a323c;--tx:#e6edf3;
        --dim:#8b98a5;--on:#2ea043;--off:#6e7681;--accent:#3b82f6;--warn:#d29922;--bad:#f85149}
  *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);
    font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:1.1rem}
  a{color:var(--accent);text-decoration:none}
  .wrap{max-width:960px;margin:0 auto}
  h1{font-size:1.2rem;margin:.1rem 0 1rem;display:flex;align-items:center;gap:.5rem;flex-wrap:wrap}
  h2{font-size:.82rem;color:var(--dim);text-transform:uppercase;letter-spacing:.06em;margin:1.5rem 0 .55rem}
  .pill{font-size:.7rem;padding:.12rem .5rem;border-radius:20px;border:1px solid var(--line);color:var(--dim)}
  .pill.ok{color:var(--on);border-color:#1c3a24}.pill.bad{color:var(--bad);border-color:#5c2323}
  .grid{display:grid;gap:.7rem}
  .cards{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}
  .card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:.7rem .9rem}
  .card .k{color:var(--dim);font-size:.74rem}.card .v{font-size:1.15rem;margin-top:.15rem;font-weight:600}
  .card .s{color:var(--dim);font-size:.72rem;margin-top:.1rem}
  .two{grid-template-columns:1fr 1fr}@media(max-width:680px){.two{grid-template-columns:1fr}}
  .feat{display:flex;align-items:center;justify-content:space-between;background:var(--card);
    border:1px solid var(--line);border-radius:9px;padding:.5rem .8rem;margin-bottom:.4rem}
  .feat .n{font-weight:600}.feat .c{color:var(--dim);font-size:.78rem;margin-left:.5rem}
  .sw{position:relative;width:44px;height:25px;flex:none}.sw input{opacity:0;width:0;height:0}
  .sl{position:absolute;inset:0;background:var(--off);border-radius:25px;cursor:pointer;transition:.2s}
  .sl:before{content:"";position:absolute;height:19px;width:19px;left:3px;top:3px;background:#fff;border-radius:50%;transition:.2s}
  input:checked+.sl{background:var(--on)}input:checked+.sl:before{transform:translateX(19px)}
  .panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:.8rem 1rem}
  .feed{font-size:.82rem;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--dim);
    max-height:220px;overflow:auto}.feed div{padding:.12rem 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .feed .b{color:var(--tx)}.feed .g{color:var(--on)}.feed .r{color:var(--bad)}.feed .y{color:var(--warn)}
  .story{padding:.4rem 0;border-bottom:1px solid var(--line);font-size:.9rem}
  .story:last-child{border:0}.story .d{color:var(--dim);font-size:.75rem}
  .btn{background:var(--card2);color:var(--tx);border:1px solid var(--line);border-radius:8px;
    padding:.5rem .9rem;font-size:.9rem;cursor:pointer;margin-right:.5rem}
  .btn.danger{border-color:#7d2b2b;color:#ff9d9d}.btn:hover{border-color:var(--accent)}
  .muted{color:var(--dim);font-size:.8rem}
  .banner{background:#3d1d1d;border:1px solid #7d2b2b;color:#ffb4b4;padding:.55rem .9rem;border-radius:8px;margin-bottom:1rem;display:none}
  svg .bar{fill:var(--accent)}svg .barh{fill:#2ea043}svg .bars{fill:#a371f7}svg text{fill:var(--dim);font-size:10px}
  table{width:100%;border-collapse:collapse;font-size:.82rem}th,td{padding:.35rem .5rem;text-align:left;border-bottom:1px solid var(--line)}
  th{color:var(--dim)}td.num{text-align:right;font-variant-numeric:tabular-nums}
</style></head><body><div class="wrap">
  <h1>🗞️ Chesterfield Report — Ops <span id="hpill" class="pill">loading…</span></h1>
  <div id="banner" class="banner"></div>

  <div class="grid cards" id="health"></div>

  <div class="grid two" style="margin-top:1rem">
    <div>
      <h2>AI features</h2>
      <div style="margin-bottom:.6rem">
        <button class="btn danger" onclick="pauseAll()">⏸ Pause ALL</button>
        <button class="btn" onclick="resumeAll()">▶ Resume all</button>
        <span class="muted" id="saved"></span>
      </div>
      <div id="feats"></div>
    </div>
    <div>
      <h2>AI calls — 14 days</h2>
      <div class="panel"><div id="chart"></div>
        <div class="muted" style="margin-top:.4rem"><span style="color:#2ea043">■</span> haiku
          &nbsp;<span style="color:#a371f7">■</span> sonnet</div></div>
      <h2>Fact-check alerts</h2>
      <div class="panel" id="alerts"></div>
    </div>
  </div>

  <div class="grid two" style="margin-top:.4rem">
    <div><h2>Recent activity</h2><div class="panel feed" id="feed"></div></div>
    <div><h2>Recently published</h2><div class="panel" id="recent"></div></div>
  </div>
  <p class="muted" id="gen" style="margin-top:1rem"></p>
</div>
<script>
async function api(path, body){
  path=path.replace(/^\//,"");
  const o={headers:{"Content-Type":"application/json"}};
  if(body){o.method="POST";o.body=JSON.stringify(body)}
  return (await fetch(path,o)).json();
}
function esc(s){return (s||"").replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]))}
function cls(l){if(l.includes("FAILED")||l.includes("STORM GUARD"))return"r";if(l.includes("deploy OK"))return"g";
  if(l.includes("no-op")||l.includes("no published")||l.includes("budget"))return"y";if(l.includes("building"))return"b";return""}
function chart(model){
  const days=Object.keys(model).sort().slice(-14);
  if(!days.length)return '<div class="muted">No AI calls recorded yet.</div>';
  const tot=d=>Object.values(model[d]||{}).reduce((a,b)=>a+b,0);
  const max=Math.max(1,...days.map(tot));const W=Math.max(300,days.length*26),H=90,bw=18;
  let s=`<svg viewBox="0 0 ${W} ${H+18}" width="100%">`;
  days.forEach((d,i)=>{const x=i*26+6;const h=model[d]||{};
    const hh=(h.haiku||0)/max*H, sh=(h.sonnet||0)/max*H, oh=(h.other||0)/max*H;
    let y=H;
    s+=`<rect class="barh" x="${x}" y="${y-hh}" width="${bw}" height="${hh}"><title>${d} haiku ${h.haiku||0}</title></rect>`;y-=hh;
    s+=`<rect class="bars" x="${x}" y="${y-sh}" width="${bw}" height="${sh}"><title>${d} sonnet ${h.sonnet||0}</title></rect>`;y-=sh;
    s+=`<rect class="bar" x="${x}" y="${y-oh}" width="${bw}" height="${oh}"></rect>`;
    if(i%2==0||days.length<9)s+=`<text x="${x}" y="${H+14}">${d.slice(5)}</text>`;});
  return s+"</svg>";
}
function render(s){
  document.getElementById("banner").style.display=s.all_off?"block":"none";
  document.getElementById("banner").textContent="⚠ ALL AI features are OFF — the pipeline is running without AI enrichment.";
  const hp=document.getElementById("hpill");
  hp.textContent=s.all_off?"AI paused":"AI on";hp.className="pill "+(s.all_off?"bad":"ok");
  const h=s.health;
  document.getElementById("health").innerHTML=[
    ["AI calls today",s.today_total,`budget ${s.budget}/run`],
    ["Drafts awaiting review",h.drafts_awaiting,`${h.drafts_total} in queue`],
    ["Published stories",h.published,""],
    ["Next ingest",h.next_run,""],
    ["Last deploy",(h.last_deploy.match(/deploy (OK|FAILED)/)||["—"])[0],h.last_deploy.slice(0,19)],
    ["Facebook",s.fb,""],
  ].map(([k,v,sub])=>`<div class="card"><div class="k">${k}</div><div class="v">${esc(String(v))}</div>${sub?`<div class="s">${esc(sub)}</div>`:""}</div>`).join("");
  const today=new Date().toISOString().slice(0,10),tc=(s.usage[today]||{});
  document.getElementById("feats").innerHTML=Object.entries(s.features).map(([f,on])=>
    `<div class="feat"><div><span class="n">${f}</span><span class="c">${tc[f]||0} today</span></div>
     <label class="sw"><input type="checkbox" ${on?"checked":""} onchange="toggle('${f}',this.checked)"><span class="sl"></span></label></div>`).join("");
  document.getElementById("chart").innerHTML=chart(s.usage_model);
  const a=s.alerts;
  document.getElementById("alerts").innerHTML=a.count?
    `<div style="font-weight:600;color:var(--warn)">${a.count} stories need review</div>
     <div class="muted" style="margin:.2rem 0 .4rem">updated ${esc(a.updated)}</div>`+
     a.items.map(i=>`<div class="story">${esc(i)}</div>`).join(""):
    `<div style="color:var(--on)">✓ No open fact-check alerts</div>`;
  document.getElementById("feed").innerHTML=s.activity.map(l=>`<div class="${cls(l)}">${esc(l)}</div>`).join("")||'<div class="muted">no activity</div>';
  document.getElementById("recent").innerHTML=s.recent.map(r=>
    `<div class="story"><div>${esc(r.headline)}</div><div class="d">${esc(r.date)} ${esc(r.focus)}</div></div>`).join("")||'<div class="muted">none</div>';
  document.getElementById("gen").textContent="updated "+s.generated+" · auto-refreshes every 30s";
}
async function toggle(f,on){await api("/api/toggle",{feature:f,on});flash(`${f} → ${on?"ON":"OFF"}`);load();}
async function pauseAll(){if(confirm("Turn OFF all AI features?")){await api("/api/pause-all",{});flash("all AI paused");load();}}
async function resumeAll(){await api("/api/resume-all",{});flash("all AI resumed");load();}
function flash(m){const e=document.getElementById("saved");e.textContent="✓ "+m;setTimeout(()=>e.textContent="",2500);}
async function load(){try{render(await api("/api/status"))}catch(e){document.getElementById("hpill").textContent="error"}}
load();setInterval(load,30000);
</script></body></html>"""


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _body_json(self) -> dict:
        try:
            n = int(self.headers.get("Content-Length", "0"))
            return json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return {}

    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path == "/" or self.path.rstrip("/") in ("", "/index.html"):
            self._send(200, PAGE, "text/html; charset=utf-8")
        elif self.path.startswith("/api/status"):
            self._send(200, json.dumps(_status()))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        body = self._body_json()
        if self.path == "/api/toggle" and body.get("feature") in FEATURES:
            _save_features({body["feature"]: bool(body.get("on"))})
            self._send(200, json.dumps({"ok": True}))
        elif self.path == "/api/pause-all":
            _save_features({f: False for f in FEATURES})
            self._send(200, json.dumps({"ok": True}))
        elif self.path == "/api/resume-all":
            _save_features({f: True for f in FEATURES})
            self._send(200, json.dumps({"ok": True}))
        else:
            self._send(404, json.dumps({"error": "not found"}))


if __name__ == "__main__":
    print(f"AI ops dashboard on :{PORT} (DATA_DIR={DATA_DIR})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
