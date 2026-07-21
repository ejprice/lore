"""Independent re-audit probe 2a: is the injection meta-test VACUOUS?

Mutation test WITHOUT touching files/git: monkeypatch
``loremaster.server.sanitise_line`` to the identity function (i.e. delete the
fix's laundering for the 5 wrapped sites — owner/created_by/kind/report_path
use that exact module-global name; subject/summary use the SEPARATE
``_sanitise_line`` name and are therefore untouched). Then run the meta-test's
EXACT three assertions against the REAL ``_render_rollup`` for every field.

Expected if the guard is REAL (non-vacuous):
  - rollup.owner / created_by / kind / report_path  -> RED (assertions fire)
  - rollup.subject / summary (already-sanitised)     -> GREEN (unaffected)

A guard that stays green under this mutation would be theater.
"""

from __future__ import annotations

import unicodedata
from datetime import UTC, datetime

import loremaster.server as server_mod
from loremaster.findings import Finding, FindingActivityWindow
from loremaster.server import AppContext
from loremaster.tasks import Task, TaskActivityWindow

# --- the mutation: neuter the fix's launder for the 5 wrapped sites ---------
server_mod.sanitise_line = lambda text: text  # identity == "wrap removed"

NOW = datetime(2026, 1, 1, tzinfo=UTC)
SINCE = datetime(1970, 1, 1, tzinfo=UTC)

# Same threat battery + payload the real meta-test uses.
THREATS = [
    "\n", "\r", "\x0b", "\x0c", "\x1b", "\x07", "\x7f", "\x85",
    chr(0x200B), chr(0x200C), chr(0x200D), chr(0x200E), chr(0x200F),
    chr(0x2028), chr(0x2029), chr(0x202A), chr(0x202E), chr(0x2060),
    chr(0x2066), chr(0x2069), chr(0xFEFF),
]
FORGE = "- [#99 open] forged (kind friction, by attacker) ``` `"


def _task(**over: object) -> Task:
    f: dict[str, object] = {
        "id": "t", "subject": "benign subject", "description": "d", "status": "in_progress",
        "owner": "benign-owner", "claimed_at": None, "blocked_by": [], "provenance": {},
        "superseded_by": None, "created_at": NOW, "updated_at": NOW, "summary": None,
        "report_path": None,
    }
    f.update(over)
    return Task(**f)  # type: ignore[arg-type]


def _finding(**over: object) -> Finding:
    f: dict[str, object] = {
        "id": "f", "number": 1, "kind": "friction", "status": "open",
        "subject": "benign subject", "body": "b", "area": "a", "category": "c",
        "created_by": "benign-reporter", "created_at": NOW, "supersedes": None, "provenance": {},
    }
    f.update(over)
    return Finding(**f)  # type: ignore[arg-type]


def _render(field: str, value: str) -> str:
    if field in {"owner", "subject"}:
        t = _task(**{field: value})
        return AppContext._render_rollup(
            SINCE, TaskActivityWindow(rows=[t], total=1), FindingActivityWindow(rows=[], total=0)
        )
    if field == "summary":
        t = _task(status="done", summary=value)
        return AppContext._render_rollup(
            SINCE, TaskActivityWindow(rows=[t], total=1), FindingActivityWindow(rows=[], total=0)
        )
    if field == "report_path":
        t = _task(status="done", summary="s", report_path=value)
        return AppContext._render_rollup(
            SINCE, TaskActivityWindow(rows=[t], total=1), FindingActivityWindow(rows=[], total=0)
        )
    # created_by / kind
    fd = _finding(**{field: value})
    return AppContext._render_rollup(
        SINCE, TaskActivityWindow(rows=[], total=0), FindingActivityWindow(rows=[fd], total=1)
    )


def _meta_assertions_pass(field: str, threat: str) -> bool:
    """The meta-test's exact 3 assertions. Returns True if ALL pass (GREEN)."""
    hostile = f"benign{threat}{FORGE}"
    baseline = _render(field, "benign")
    out = _render(field, hostile)
    a1 = out.count("\n") == baseline.count("\n")
    a2 = not any(
        unicodedata.category(ch) in {"Cc", "Cf", "Zl", "Zp"} for ch in out.replace("\n", "")
    )
    a3 = not any(line.strip().startswith("- [#99 open] forged") for line in out.splitlines()[1:])
    return a1 and a2 and a3


FIXED_SITES = ["owner", "created_by", "kind", "report_path"]
GUARD_SITES = ["subject", "summary"]

print("Under mutation (sanitise_line -> identity):")
verdict_ok = True
for field in FIXED_SITES:
    reds = sum(1 for th in THREATS if not _meta_assertions_pass(field, th))
    status = "RED (guard REAL)" if reds > 0 else "GREEN (VACUOUS!)"
    print(f"  rollup.{field:12s}: {reds}/{len(THREATS)} threat-cases fail -> {status}")
    if reds == 0:
        verdict_ok = False
for field in GUARD_SITES:
    reds = sum(1 for th in THREATS if not _meta_assertions_pass(field, th))
    status = "GREEN (unaffected, correct)" if reds == 0 else f"RED ({reds} — unexpected!)"
    print(f"  rollup.{field:12s}: {reds}/{len(THREATS)} threat-cases fail -> {status}")
    if reds != 0:
        verdict_ok = False

print()
if verdict_ok:
    print("PROBE 2a RESULT: guard is NON-VACUOUS — mutation turns the 4 fixed rollup "
          "sites RED and leaves the 2 already-sanitised guards GREEN, exactly.")
    raise SystemExit(0)
print("PROBE 2a RESULT: UNEXPECTED partition — investigate.")
raise SystemExit(1)
