"""Spanish translation for The Chesterfield Report.

Translates a story's headline + markdown body into natural Spanish via the
Claude Code `claude` CLI (no API key needed), the same way `enrich._enrich_cli`
shells out. Output is structured via `--json-schema`.

Translations are cached by a sha256 content hash of (headline + body_md) in
`pipeline/es_cache.json`, so an unchanged story is never re-translated — only
new or edited stories hit the CLI, keeping cost sane on re-runs.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

MODEL = "claude-haiku-4-5"
CLI_TIMEOUT = 240  # seconds; translation of a long body can take a while

# pipeline/ is parents[1] of this file (chesterfield/translate.py).
CACHE_PATH = Path(__file__).resolve().parents[1] / "es_cache.json"

_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "body_md": {"type": "string"},
    },
    "required": ["headline", "body_md"],
    "additionalProperties": False,
}

_SYSTEM = (
    "You are a professional translator for a hyperlocal news site covering "
    "Chesterfield County, Virginia, USA. Translate English news content into "
    "natural, fluent Latin American Spanish suitable for local residents. "
    "Be faithful and neutral; do not editorialize or add content."
)

_PROMPT = (
    "Translate the following news story headline and Markdown body from English "
    "into natural Spanish.\n\n"
    "STRICT RULES:\n"
    "- PRESERVE the Markdown structure EXACTLY: keep every heading (#, ##), list "
    "marker (-), link syntax [text](url), **bold**, _italics_, and blank lines.\n"
    "- Translate ONLY the prose / human-readable text. Translate link anchor text "
    "but NEVER change a URL inside parentheses.\n"
    "- Do NOT translate proper nouns: names of people, place/street/road names, "
    "venues, organizations, county/agency names, or source/outlet names. Leave "
    "them in their original form (e.g. 'Salem Church Road', 'VDOT', "
    "'Chesterfield County', 'Richmond Times-Dispatch').\n"
    "- You MAY translate common label words inside bold list prefixes "
    "(e.g. '**Who:**' -> '**Quién:**', '**When:**' -> '**Cuándo:**', "
    "'**TL;DR:**' -> '**En resumen:**', '**Why it matters:**' -> "
    "'**Por qué importa:**').\n"
    "- Translate generic 'Read the original at <Source> ' / 'Read the source "
    "at <Source> ' link text to 'Lee el original en <Source> ', keeping the "
    "source name and URL unchanged.\n"
    "- Return ONLY the structured fields: the translated headline and the "
    "translated Markdown body.\n\n"
    "HEADLINE:\n{headline}\n\nBODY (Markdown):\n{body}\n"
)


def _content_hash(headline: str, body_md: str) -> str:
    h = hashlib.sha256()
    h.update((headline or "").encode("utf-8"))
    h.update(b"\x00")
    h.update((body_md or "").encode("utf-8"))
    return h.hexdigest()


def _load_cache() -> dict:
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def cli_available() -> bool:
    return shutil.which("claude") is not None


def _translate_cli(headline: str, body_md: str, model: str) -> dict:
    cmd = [
        "claude", "-p", _PROMPT.format(headline=headline, body=body_md),
        "--output-format", "json",
        "--json-schema", json.dumps(_SCHEMA),
        "--append-system-prompt", _SYSTEM,
        "--model", model,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=CLI_TIMEOUT)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[:300] or "claude CLI failed")
    envelope = json.loads(proc.stdout)
    if envelope.get("is_error"):
        raise RuntimeError(envelope.get("result", "CLI returned is_error"))
    data = envelope.get("structured_output")
    if not data:
        raise RuntimeError("CLI returned no structured_output")
    out = {
        "headline": (data.get("headline") or "").strip() or headline,
        "body_md": data.get("body_md") or body_md,
    }
    return out


def translate_story(headline: str, body_md: str, model: str = MODEL) -> dict:
    """Translate a story to Spanish, returning {"headline", "body_md"}.

    Cached by sha256(headline+body_md) in pipeline/es_cache.json. An unchanged
    story is served from cache (no CLI call); new/changed ones hit the CLI and
    are written back to the cache.
    """
    key = _content_hash(headline, body_md)
    cache = _load_cache()
    hit = cache.get(key)
    if isinstance(hit, dict) and "headline" in hit and "body_md" in hit:
        return {"headline": hit["headline"], "body_md": hit["body_md"]}

    result = _translate_cli(headline, body_md, model)
    cache[key] = result
    _save_cache(cache)
    return result


# --- Batched UI / page-text translation (for section pages) ----------------
# Section pages are HTML, not Markdown. We translate their visible text strings
# in batches and cache each string by hash in a separate file so repeated UI
# labels are translated once and re-runs (the 2-hourly cron) stay cheap.

UI_CACHE_PATH = Path(__file__).resolve().parents[1] / "es_ui_cache.json"

_UI_SCHEMA = {
    "type": "object",
    "properties": {"translations": {"type": "array", "items": {"type": "string"}}},
    "required": ["translations"],
    "additionalProperties": False,
}

_UI_SYSTEM = (
    "You translate UI labels and prose for a hyperlocal news site covering "
    "Chesterfield County, Virginia into natural, fluent Latin American Spanish."
)

_UI_PROMPT = (
    "Translate each English string in this JSON array into natural Latin American "
    "Spanish.\n\nSTRICT RULES:\n"
    "- Return a JSON object {{\"translations\": [...]}} whose array has the SAME length "
    "and SAME order as the input.\n"
    "- PRESERVE exactly (do not translate): proper nouns; names of people, streets, "
    "roads, places, schools, agencies and organizations; numbers, dates, times, money, "
    "phone numbers, addresses; and URLs/emails.\n"
    "- Translate UI labels, headings, and prose. Keep it concise and natural.\n"
    "- If a string is only a proper noun, number, or symbol, return it unchanged.\n\n"
    "STRINGS:\n{arr}"
)


def _ui_hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _load_ui_cache() -> dict:
    try:
        return json.loads(UI_CACHE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def _save_ui_cache(cache: dict) -> None:
    """Merge our entries into the on-disk cache under an exclusive lock, so several
    translator processes can run in parallel (sharded over different pages) without
    losing each other's entries or tearing the file."""
    UI_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        import fcntl
        with open(UI_CACHE_PATH, "a+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.seek(0)
            raw = f.read()
            try:
                disk = json.loads(raw) if raw.strip() else {}
            except ValueError:
                disk = {}
            disk.update(cache)
            f.seek(0)
            f.truncate()
            f.write(json.dumps(disk, ensure_ascii=False, indent=2, sort_keys=True))
            fcntl.flock(f, fcntl.LOCK_UN)
    except ImportError:  # non-POSIX fallback (no concurrent runs there)
        UI_CACHE_PATH.write_text(
            json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _translate_batch_cli(batch: list, model: str) -> list:
    cmd = [
        "claude", "-p", _UI_PROMPT.format(arr=json.dumps(batch, ensure_ascii=False)),
        "--output-format", "json", "--json-schema", json.dumps(_UI_SCHEMA),
        "--append-system-prompt", _UI_SYSTEM, "--model", model,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=CLI_TIMEOUT)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[:300] or "claude CLI failed")
    envelope = json.loads(proc.stdout)
    if envelope.get("is_error"):
        raise RuntimeError(envelope.get("result", "CLI returned is_error"))
    data = envelope.get("structured_output") or {}
    out = data.get("translations")
    if not isinstance(out, list) or len(out) != len(batch):
        raise RuntimeError("batch translation length mismatch")
    return [str(x) for x in out]


def _translate_split(batch: list, model: str) -> dict:
    """Translate a batch, recursively splitting on failure (CLI error or a
    length mismatch) down to single strings so it always resolves. A string that
    still can't be translated is dropped (left English)."""
    try:
        trans = _translate_batch_cli(batch, model)
        return dict(zip(batch, trans))
    except Exception:
        if len(batch) <= 1:
            return {}
        mid = len(batch) // 2
        out = _translate_split(batch[:mid], model)
        out.update(_translate_split(batch[mid:], model))
        return out


def translate_strings(strings, model: str = MODEL, batch_size: int = 25) -> dict:
    """Translate a list of English UI/prose strings to Spanish.

    Returns {original: translated}. Cached per-string (es_ui_cache.json) so repeat
    labels and re-runs are free. A string that can't be translated falls back to
    its English original (the page still builds)."""
    uniq = list(dict.fromkeys(s for s in strings if s and s.strip()))
    if not uniq or not cli_available():
        return {s: s for s in uniq}
    cache = _load_ui_cache()
    todo = [s for s in uniq if _ui_hash(s) not in cache]
    changed = False
    for i in range(0, len(todo), batch_size):
        res = _translate_split(todo[i:i + batch_size], model)
        for src, dst in res.items():
            cache[_ui_hash(src)] = dst
            changed = True
    if changed:
        _save_ui_cache(cache)
    return {s: cache.get(_ui_hash(s), s) for s in uniq}
