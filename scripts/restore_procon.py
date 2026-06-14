#!/usr/bin/env python3
"""One-off: restore '## The case for' / '## The case against' on the non-tragedy
published stories that were over-stripped earlier. Generates a fair pro/con from
the existing article body via the Claude CLI (Haiku) and inserts it right before
the '**Why it matters:**' line. Idempotent: skips stories that already have it."""
import json
import subprocess
import sys
from pathlib import Path

PUB = Path(__file__).resolve().parent.parent / "content" / "published"

# Tragedies — pro/con stays OFF (user's explicit request).
SKIP = {
    "2026-06-06-chesterfield-woman-missing-since-saturday-morning.md",
    "2026-06-06-fatal-two-vehicle-crash-in-chesterfield-kills-one.md",
    "2026-06-06-gofundme-launched-for-officers-shot-on-domestic-call.md",
}

MODEL = "claude-haiku-4-5"

SCHEMA = {
    "type": "object",
    "properties": {
        "case_for": {"type": "string"},
        "case_against": {"type": "string"},
    },
    "required": ["case_for", "case_against"],
    "additionalProperties": False,
}

SYSTEM = (
    "You are a fair, balanced local-news editor for Chesterfield County, Virginia. "
    "Given a news article, write a brief, good-faith 'case for' and 'case against' "
    "the policy/development/decision it covers — the kind of even-handed pro/con "
    "mainstream news rarely provides. Each side: 2-4 sentences, concrete, fair, "
    "non-partisan, grounded ONLY in the article's substance. Argue the strongest "
    "honest version of each side. Do NOT invent facts. No hedging like 'some say'."
)


def gen(body: str) -> dict:
    prompt = (
        "Write a balanced case_for and case_against for the subject of this "
        "Chesterfield County news article:\n\n" + body
    )
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "json",
        "--json-schema", json.dumps(SCHEMA),
        "--append-system-prompt", SYSTEM,
        "--model", MODEL,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[:200] or "claude CLI failed")
    env = json.loads(proc.stdout)
    if env.get("is_error"):
        raise RuntimeError(env.get("result", "is_error"))
    data = env.get("structured_output")
    if not data:
        raise RuntimeError("no structured_output")
    return data


def main():
    files = sorted(PUB.glob("*.md"))
    for f in files:
        if f.name in SKIP:
            print(f"skip (tragedy)  {f.name}")
            continue
        text = f.read_text()
        if "## The case for" in text:
            print(f"skip (has)      {f.name}")
            continue
        if "**Why it matters:**" not in text:
            print(f"skip (no anchor){f.name}")
            continue
        try:
            data = gen(text)
        except Exception as e:
            print(f"FAIL            {f.name}: {e}")
            continue
        cf = data["case_for"].strip()
        ca = data["case_against"].strip()
        block = f"## The case for\n\n{cf}\n\n## The case against\n\n{ca}\n\n"
        new = text.replace("**Why it matters:**", block + "**Why it matters:**", 1)
        f.write_text(new)
        print(f"restored        {f.name}")


if __name__ == "__main__":
    main()
