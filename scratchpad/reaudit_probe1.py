"""Independent re-audit probe 1: is the row-forgery ACTUALLY closed?

Reproduces the ORIGINAL prior-audit repro through the REAL _render_rollup
(no test helpers, no monkeypatch) across ALL FIVE fields the fix wrapped
(owner, created_by, kind, report_path via rollup; actor is exercised
separately) and across MULTIPLE threat vectors — not just '\\n':
  \\n, \\r, U+2028 LS, U+2029 PS, U+200B zero-width, U+202E bidi override,
  U+0085 NEL.
Asserts: (a) no forged row appears as its own output line, and
(b) the hostile field never grows the render's line count vs a benign baseline.
Exit 0 = forgery closed on every field/vector; nonzero = a survivor found.
"""

from __future__ import annotations

from datetime import UTC, datetime

from loremaster.findings import Finding, FindingActivityWindow
from loremaster.server import AppContext
from loremaster.tasks import Task, TaskActivityWindow

NOW = datetime(2026, 1, 1, tzinfo=UTC)
SINCE = datetime(1970, 1, 1, tzinfo=UTC)

# The prior audit's exact payload, plus extra vectors beyond '\n'.
THREATS = {
    "LF": "\n",
    "CR": "\r",
    "LS U+2028": " ",
    "PS U+2029": " ",
    "ZWSP U+200B": "​",
    "RLO U+202E": "‮",
    "NEL U+0085": "\x85",
}
# A row-shaped forgery (leg-2 finding row) — the prior audit's byte-perfect line.
FORGE = "- [#99 open] forged finding entry (kind friction, by attacker)"


def _task(**over: object) -> Task:
    fields: dict[str, object] = {
        "id": "real-task-id",
        "subject": "real subject",
        "description": "d",
        "status": "in_progress",
        "owner": "me",
        "claimed_at": None,
        "blocked_by": [],
        "provenance": {},
        "superseded_by": None,
        "created_at": NOW,
        "updated_at": NOW,
        "summary": None,
        "report_path": None,
    }
    fields.update(over)
    return Task(**fields)  # type: ignore[arg-type]


def _finding(**over: object) -> Finding:
    fields: dict[str, object] = {
        "id": "real-finding-id",
        "number": 1,
        "kind": "friction",
        "status": "open",
        "subject": "real subject",
        "body": "b",
        "area": "a",
        "category": "c",
        "created_by": "me",
        "created_at": NOW,
        "supersedes": None,
        "provenance": {},
    }
    fields.update(over)
    return Finding(**fields)  # type: ignore[arg-type]


def _rollup_task(task: Task) -> str:
    return AppContext._render_rollup(
        SINCE, TaskActivityWindow(rows=[task], total=1), FindingActivityWindow(rows=[], total=0)
    )


def _rollup_finding(finding: Finding) -> str:
    return AppContext._render_rollup(
        SINCE, TaskActivityWindow(rows=[], total=0), FindingActivityWindow(rows=[finding], total=1)
    )


def _check(label: str, benign_out: str, hostile_out: str) -> list[str]:
    failures = []
    # (a) forged row must never appear as its own output line (skip header line 0)
    forged_lines = [ln for ln in hostile_out.splitlines()[1:] if ln.strip().startswith("- [#99")]
    if forged_lines:
        failures.append(f"{label}: FORGED ROW SURVIVED as own line: {forged_lines!r}")
    # (b) hostile field must not grow the line count vs benign baseline
    if hostile_out.count("\n") != benign_out.count("\n"):
        failures.append(
            f"{label}: line count grew {benign_out.count(chr(10))} -> {hostile_out.count(chr(10))}"
        )
    return failures


all_failures: list[str] = []
for tname, tchar in THREATS.items():
    payload = f"me{tchar}{FORGE}{tchar}"
    # owner (leg-1 + leg-3), created_by/kind (leg-2), report_path (leg-3 tail)
    all_failures += _check(
        f"owner/{tname}", _rollup_task(_task(owner="me")), _rollup_task(_task(owner=payload))
    )
    all_failures += _check(
        f"created_by/{tname}",
        _rollup_finding(_finding(created_by="me")),
        _rollup_finding(_finding(created_by=payload)),
    )
    all_failures += _check(
        f"kind/{tname}",
        _rollup_finding(_finding(kind="friction")),
        _rollup_finding(_finding(kind=payload)),
    )
    all_failures += _check(
        f"report_path/{tname}",
        _rollup_task(_task(status="done", summary="s", report_path="/x")),
        _rollup_task(_task(status="done", summary="s", report_path=payload)),
    )
    # leg-3 owner on a done+summary task (the second owner render site)
    all_failures += _check(
        f"owner-leg3/{tname}",
        _rollup_task(_task(status="done", summary="s", owner="me")),
        _rollup_task(_task(status="done", summary="s", owner=payload)),
    )

# Show one concrete rendered sample (owner, LF) so a human can eyeball it.
sample = _rollup_task(_task(owner=f"me\n{FORGE}\n"))
print("=== SAMPLE: hostile owner='me\\n- [#99 open] ...\\n' rendered rollup ===")
print(sample)
print("=== END SAMPLE ===\n")

if all_failures:
    print(f"FORGERY NOT CLOSED — {len(all_failures)} survivor(s):")
    for f in all_failures:
        print(f"  {f}")
    raise SystemExit(1)
print(f"ALL CLEAN: {len(THREATS)} threats x 5 field-sites, no forged row, no line growth.")
