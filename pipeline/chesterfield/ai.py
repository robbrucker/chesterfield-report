"""Single gateway for every Claude Code CLI (`claude -p`) call in the pipeline.

Before this module, each feature (enrich, triage, qa, factcheck, translate,
events, cases, farmers, meetings) shelled out to `claude -p` on its own. There
was no way to cap total spend per run, turn one misbehaving feature off, or kill
all AI at once. A single runaway (e.g. a translation storm) could fire a thousand
calls before anyone noticed. This centralizes all three controls.

Controls, highest precedence first:
  * CR_AI_OFF=1                 -> kill switch: disable ALL AI calls.
  * CR_AI_<FEATURE>=0/1         -> env toggle for one feature (e.g. CR_AI_TRANSLATE=0).
  * ai_features.json            -> {"translate": false, ...} persistent per-feature
                                   toggles (edit the file to flip a feature; no
                                   redeploy needed). Env wins over the file.
  * CR_AI_BUDGET=<n>            -> max claude -p calls per pipeline PROCESS
                                   (one `run.py <cmd>` invocation). Default 400.

A disabled feature or a tripped budget makes run() raise AIDisabled /
AIBudgetExceeded. Every caller already wraps its CLI call in try/except and
degrades gracefully (extractive enrich, English fallback, skip QA), so the build
never breaks, it just does less AI.

The budget counter is per-process on purpose: the cron runs ingest, triage, qa,
build and factcheck as SEPARATE `run.py` processes, and the worst-case storm
(translation) happens inside a single `run.py build`, so a per-process cap is
exactly the right blast radius.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "ai_features.json"
# Append-only usage ledger: one line per AI call, "<iso_utc>\t<feature>\t<model>".
# The `ai status`/`ai usage` commands and the dashboard aggregate it.
USAGE_LOG = ROOT / "ai_usage.log"

# Features that route through this gateway. Used for the toggle UI/docs and to
# validate ai_features.json keys.
KNOWN_FEATURES = (
    "enrich", "triage", "qa", "factcheck", "translate",
    "events", "cases", "farmers", "meetings", "apartments",
)

DEFAULT_BUDGET = 400

_TRUE = {"1", "true", "TRUE", "yes", "on"}
_FALSE = {"0", "false", "FALSE", "no", "off", ""}


class AIDisabled(RuntimeError):
    """A feature (or all AI) is turned off."""


class AIBudgetExceeded(RuntimeError):
    """The per-process AI call budget is used up."""


# Per-process call counter (one pipeline command = one process).
_calls = 0


def _budget() -> int:
    try:
        return int(os.environ.get("CR_AI_BUDGET", str(DEFAULT_BUDGET)))
    except ValueError:
        return DEFAULT_BUDGET


def _load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def is_off() -> bool:
    """Global kill switch."""
    return os.environ.get("CR_AI_OFF", "") in _TRUE


def feature_enabled(feature: str) -> bool:
    """Is this feature allowed to make AI calls right now?

    Precedence: global kill switch -> env toggle -> ai_features.json -> default on.
    """
    if is_off():
        return False
    env = os.environ.get(f"CR_AI_{feature.upper()}")
    if env is not None:
        return env not in _FALSE
    cfg = _load_config()
    if feature in cfg:
        return bool(cfg[feature])
    return True


def calls_made() -> int:
    return _calls


def _model_of(cmd: list) -> str:
    """Pull the --model value out of a claude CLI argv, for usage accounting."""
    try:
        return cmd[cmd.index("--model") + 1]
    except (ValueError, IndexError):
        return "?"


def _log_usage(feature: str, model: str) -> None:
    """Append one line to the usage ledger. Best-effort: never break a call."""
    try:
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(USAGE_LOG, "a", encoding="utf-8") as f:
            f.write(f"{ts}\t{feature}\t{model}\n")
    except Exception:
        pass


def usage_by_day(days: int = 7) -> dict:
    """Aggregate the usage ledger into {date: {feature: count}} for the last N
    days (UTC). Reads the whole file; it is small (one short line per call)."""
    from datetime import datetime, timezone, timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    out: dict = {}
    try:
        for line in USAGE_LOG.read_text(encoding="utf-8").splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            day = parts[0][:10]
            if day < cutoff:
                continue
            feat = parts[1]
            out.setdefault(day, {}).setdefault(feat, 0)
            out[day][feat] += 1
    except Exception:
        pass
    return out


def status() -> dict:
    """Snapshot for the CLI / dashboard: per-feature on/off, budget, and today's
    call counts by feature."""
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_counts = usage_by_day(days=1).get(today, {})
    return {
        "all_off": is_off(),
        "budget": _budget(),
        "features": {f: feature_enabled(f) for f in KNOWN_FEATURES},
        "today": today_counts,
        "today_total": sum(today_counts.values()),
    }


def set_feature(feature: str, on: bool) -> None:
    """Persist a per-feature toggle into ai_features.json (create/merge)."""
    if feature not in KNOWN_FEATURES:
        raise ValueError(f"unknown feature '{feature}'; known: {', '.join(KNOWN_FEATURES)}")
    cfg = _load_config()
    cfg[feature] = bool(on)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")


def remaining() -> int:
    return max(0, _budget() - _calls)


def run(feature: str, cmd: list, timeout: int, **kw):
    """Guarded `subprocess.run` for a `claude -p ...` command.

    Raises AIDisabled if the feature (or all AI) is off, AIBudgetExceeded if the
    per-process cap is hit. Otherwise runs the command, counts it, and returns
    the CompletedProcess unchanged so callers keep their existing parsing.
    """
    global _calls
    if not feature_enabled(feature):
        raise AIDisabled(f"AI feature '{feature}' is disabled "
                         f"(CR_AI_OFF / CR_AI_{feature.upper()} / ai_features.json)")
    if _calls >= _budget():
        # Log once-ish so a tripped budget is visible in the cron log.
        print(f"  ! AI budget {_budget()} reached; skipping '{feature}' call "
              f"(raise CR_AI_BUDGET for intentional backfills)", file=sys.stderr)
        raise AIBudgetExceeded(f"per-process AI budget {_budget()} reached "
                               f"(feature={feature})")
    _calls += 1
    _log_usage(feature, _model_of(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **kw)
