"""Contract — ``.claude/hooks/teammate-idle-gate.sh`` idle-gate **v2** (packet 05b).

This is the FIRST automated instrument for the idle-gate hook. Until now the hook was
guarded only by "pipe-test all four branches before registering" run by hand — a habit,
not a gate (CLAUDE.md: *"a guard nobody runs is a hope with a filename"*). This file makes
the hook's behaviour a checked variable.

WHO GRADES WHOM. This is the RED contract for idle-gate v2. A **separate builder**
implements the hook to green; the contract author (this file) does NOT touch
``.claude/hooks/teammate-idle-gate.sh``. Written against the design of record —
``REPORT-fable-design-05b.md`` §Q2 (archived to
``docs/plans/v2/receipts/<date>-packet05b/`` at close-out) — whose mechanism is RULED, not
re-invented here: **the hook keys on a declared-artifact-contract FILE, fail-open to v1
behaviour when the file is absent or unparseable.**

────────────────────────────────────────────────────────────────────────────────
THE DECLARED-ARTIFACT-CONTRACT FILE FORMAT — this contract OWNS and PINS it (→ packet 06)
────────────────────────────────────────────────────────────────────────────────
  Path:     /tmp/claude-idle-gate-$(basename "$repo_root")/${session_id}-${teammate_name}.contract
            (the SAME dir family the hook already mkdir -p's for its ``.nudged`` markers).
  Content:  jq-readable JSON, one key ``artifact``:
              {"artifact": "REPORT-<name>.md"}   -> owes THAT path
              {"artifact": null}                 -> owes NOTHING          (idle always allowed)
              {"artifact": "docs/design/FOO.md"} -> owes a custom path
  Semantics (hook logic, all fail-open — §Q2):
    1. contract absent / unparseable / no ``artifact`` key -> V1 DEFAULT (REPORT-<name>.md,
       resolved across root + archive + worktrees, then the existing one-shot nudge).
    2. artifact == null                                     -> exit 0 (owes nothing).
    3. artifact == "<path>"                                 -> resolve <path> (root/archive/
       worktree per the existing #121/#149 logic) -> exit 0 if found else the one-shot nudge.
  The tests below encode this path + key BEHAVIOURALLY: a builder that reads a different
  path or key leaves the RED pins (null / custom / reach) RED. This file is the spec.
  Packet 06 inherits it for the WRITE side (making every agent write its own contract as a
  standing brief-base first action); 05b ships only the READ side + this format.

────────────────────────────────────────────────────────────────────────────────
CURRENT-HOOK (v1) BRANCH INVENTORY — the removed-behavior inventory v2 must PRESERVE
────────────────────────────────────────────────────────────────────────────────
Read @ HEAD (299e69a) from ``.claude/hooks/teammate-idle-gate.sh``. v2 is a PURE WIDENING:
it may only prepend contract-reading in front of these; it may drop none of them.

Pinned by TestRegressionBranchInventory (the test named after each branch):

  B1  line 33  empty teammate_name (unidentifiable payload)     -> exit 0   test_unidentifiable_payload…
  B2  line 39  REPORT-<name>.md at repo root                    -> exit 0   test_report_at_root_is_allowed
  B3  line 54  archived REPORT under receipts/*/ (compgen -G)   -> exit 0   test_archived_report_is_allowed
  B4  line 63  REPORT in ANY registered worktree               -> exit 0   test_worktree_report_is_allowed
  B5  line 72  ``.nudged`` marker present (already nudged once) -> exit 0   test_one_shot… (2nd idle)
  B6  line 78  else: write marker + nudge                       -> exit 2   test_one_shot… (1st idle)

────────────────────────────────────────────────────────────────────────────────
PIN MAP (design §Q2 pins 1–6) and RED-vs-GREEN against the CURRENT v1 hook
────────────────────────────────────────────────────────────────────────────────
v1 never reads the contract file, so every WIDENING pin is RED today; the regression /
positive-control / fail-open pins are GREEN today (they guard the v2 *rewrite* against
dropping a branch or crashing).

  pin 1  owes-nothing exempt        TestOwesNothingExemption
         - null artifact, reportless           -> exit 0   RED-on-v1   (widening)
         - null artifact, repeated idle         -> exit 0   RED-on-v1   (widening; + no marker consumed)
         - POSITIVE CONTROL owed-report missing -> exit 2   GREEN-on-v1 (exemption is VALUE-keyed)
  pin 2  custom artifact path        TestCustomArtifactPath
         - custom path present                  -> exit 0   RED-on-v1   (widening; kills hardcoded name)
         - custom path absent                   -> exit 2   GREEN-on-v1 (control)
  pin 3  absent contract fail-open   TestAbsentContractFailsOpenToV1   (#131 leg: set -u, no crash)
  pin 4  malformed contract fail-open TestMalformedContractFailsOpen   (guards a crashing v2)
  pin 5  #121/#149 regressions       TestRegressionBranchInventory     (B1–B6 must stay green)
  pin 6  reach = CHECKED VARIABLE    TestReachIsCheckedVariable        RED-on-v1 (INSTRUMENT-0:
         the checked path is READ from the contract, not a hidden constant)

ADVERSARY-ADDED PINS (round 2 — 4 wrong builds passed all 18 original pins; see
`REPORT-adversary-idlegate-05b.md`). Operator RULED reading (x): a custom declared path
resolves at root + WORKTREES only — NO archive glob for a custom path. Each new pin is
proven to pass the correct v2 reference build AND fail its wrong build (discrimination
receipts in `REPORT-contract-idlegate-05b.md` §Discrimination).
  MP-1  custom artifact at WORKTREE root -> exit 0   RED-on-v1   (kills WB5 root-only)
  MP-2  custom under archive-basename -> exit 2      GREEN-on-v1 (kills WB6; control = wb6, not v1)
  MP-3  missing `artifact` key + reportless -> 2     GREEN-on-v1 (kills WB7 missing-key→owes-nothing)
  MP-4  custom absent, idle twice -> 2 then 0        GREEN-on-v1 (kills WB10 custom wake-loop)
  N1    assert_no_shell_error broadened + relabelled (case-insensitive; +command not found/jq:;
        honest that the EXIT CODE is the real crash guard and this is a stderr-leak supplement)
  N2    nudge keeps the anti-cry-wolf softener       GREEN-on-v1 (single substring "continue as you were")

Against the CURRENT v1 hook: 5 RED (null×2, custom-present, MP-1, reach) / 18 GREEN.

DISCRIMINATION HARNESS: set env ``IDLE_GATE_HOOK=<path>`` to run this SAME contract against
an alternative hook build. Correct reference build -> 23 passed (satisfiability); each wrong
build -> its target MP reddens. Unset in the repo gate -> the real hook.

Each test's docstring names the WRONG BUILD it kills (CLAUDE.md: *"what wrong build would
still pass this?"*).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

# ``scripts/`` file -> repo root is two parents up (matches scripts/test_scratch_copy.py).
REPO_ROOT = Path(__file__).resolve().parent.parent

# The hook under test. Defaults to the REAL committed hook; overridable via the
# ``IDLE_GATE_HOOK`` env var so the SAME contract can be run against an alternative build
# (the correct v2 reference and each wrong build) to PROVE every pin discriminates —
# CLAUDE.md's "prove sharing/behaviour by mutation" + the contract-adversary's P2. In the
# repo gate the var is unset, so the committed run always targets the real hook.
HOOK_SOURCE = Path(
    os.environ.get("IDLE_GATE_HOOK", str(REPO_ROOT / ".claude" / "hooks" / "teammate-idle-gate.sh"))
).resolve()

# An arbitrary archive-shaped subdir; the hook globs receipts/*/REPORT-<name>.md, so the
# exact name is irrelevant — only the receipts/<something>/ shape matters.
ARCHIVE_SUBDIR = Path("docs/plans/v2/receipts/2026-08-11-packet05b")

# The hook is always installed under its canonical basename in the sandbox, regardless of
# what HOOK_SOURCE is named (an override build like ``v2-correct.sh`` still lands here).
HOOK_BASENAME = "teammate-idle-gate.sh"
CONTRACT_SUFFIX = ".contract"
NUDGE_MARKER_SUFFIX = ".nudged"
NUDGE_STDERR_TOKEN = "idle-gate:"
# Anti-cry-wolf softener that MUST survive the v2 rewrite (#149: a gate that alarms a
# mid-work agent gets switched off). Pinned as a single substring, not the full wording.
NUDGE_SOFTENER_TOKEN = "continue as you were"
# Printed shell/tool failure signatures. This is a SUPPLEMENT to the exit-code assertion —
# the exit code is the real crash guard (a ``set -e`` abort just exits non-zero); this
# catches a build that fails-open with the RIGHT exit code but LEAKS a diagnostic to stderr
# (a sloppy jq/binary failure). Matched case-insensitively. Does NOT include bare "error"
# (too broad — a legitimate message could contain it); jq's own failures print "jq:".
SHELL_ERROR_TOKENS = ("unbound variable", "syntax error", "command not found", "jq:")


@dataclass
class Gate:
    """A hermetic sandbox around a byte-exact copy of the REAL committed hook.

    repo_root is the sandbox (tmp_path), so the hook's ``BASH_SOURCE``-derived root, its
    ``/tmp/claude-idle-gate-<basename>`` marker dir, and every report path resolve INSIDE
    the sandbox — the real repo root and the real ``/tmp/claude-idle-gate-lore`` marker dir
    are never touched. ``session``/``teammate`` are per-test uuids, so markers/contracts are
    collision-free across runs and across xdist workers.
    """

    root: Path
    session: str
    teammate: str

    @property
    def hook(self) -> Path:
        return self.root / ".claude" / "hooks" / HOOK_BASENAME

    @property
    def marker_dir(self) -> Path:
        # Mirrors the hook: marker_dir="/tmp/claude-idle-gate-$(basename "${repo_root}")".
        return Path("/tmp") / f"claude-idle-gate-{self.root.name}"

    def contract_path(self, teammate: str | None = None) -> Path:
        who = teammate or self.teammate
        return self.marker_dir / f"{self.session}-{who}{CONTRACT_SUFFIX}"

    def nudge_marker(self, teammate: str | None = None) -> Path:
        who = teammate or self.teammate
        return self.marker_dir / f"{self.session}-{who}{NUDGE_MARKER_SUFFIX}"

    def write_contract(self, artifact: str | None, teammate: str | None = None) -> None:
        """Write a well-formed contract declaring ``artifact`` (may be a path or ``None``)."""
        self.marker_dir.mkdir(parents=True, exist_ok=True)
        self.contract_path(teammate).write_text(json.dumps({"artifact": artifact}))

    def write_raw_contract(self, text: str, teammate: str | None = None) -> None:
        """Write arbitrary bytes as the contract (for the malformed / missing-key cases)."""
        self.marker_dir.mkdir(parents=True, exist_ok=True)
        self.contract_path(teammate).write_text(text)

    def place(self, relpath: Path | str) -> Path:
        target = self.root / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# report\n")
        return target

    def place_root_report(self, teammate: str | None = None) -> Path:
        return self.place(f"REPORT-{teammate or self.teammate}.md")

    def place_archived_report(self, teammate: str | None = None) -> Path:
        return self.place(ARCHIVE_SUBDIR / f"REPORT-{teammate or self.teammate}.md")

    def run(
        self,
        teammate: str | None = None,
        session: str | None = None,
        payload: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        who = self.teammate if teammate is None else teammate
        sess = self.session if session is None else session
        if payload is None:
            payload = {"teammate_name": who, "session_id": sess}
        return subprocess.run(
            ["bash", str(self.hook)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,  # the exit code IS the assertion target — never raise on it
        )


@pytest.fixture
def gate(tmp_path: Path) -> Iterator[Gate]:
    hooks_dir = tmp_path / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True)
    # copy2 preserves bytes; invocation is ``bash <path>`` so the +x bit is irrelevant.
    # Always install under the canonical basename so an override build lands where gate.hook
    # (and the real settings.json registration) looks for it.
    shutil.copy2(HOOK_SOURCE, hooks_dir / HOOK_BASENAME)
    sandbox = Gate(
        root=tmp_path,
        session=uuid.uuid4().hex[:12],
        teammate=uuid.uuid4().hex[:12],
    )
    yield sandbox
    # marker_dir is uniquely named after the per-test tmp dir — safe to remove wholesale.
    shutil.rmtree(sandbox.marker_dir, ignore_errors=True)


# ── assertion helpers ──────────────────────────────────────────────────────────


def assert_allowed(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, (
        f"expected ALLOW (exit 0), got {result.returncode}; stderr={result.stderr!r}"
    )
    assert NUDGE_STDERR_TOKEN not in result.stderr, (
        f"an allowed idle must not emit a nudge; stderr={result.stderr!r}"
    )


def assert_nudged(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 2, (
        f"expected NUDGE (exit 2), got {result.returncode}; stderr={result.stderr!r}"
    )
    assert NUDGE_STDERR_TOKEN in result.stderr, (
        f"a nudge must name itself on stderr; stderr={result.stderr!r}"
    )


def assert_no_shell_error(result: subprocess.CompletedProcess[str]) -> None:
    """Supplementary crash check (N1). The EXIT-CODE assertion is the real crash guard —
    a ``set -e`` abort exits non-zero and is caught by ``assert_allowed``/``assert_nudged``.
    This additionally rejects a build that returns the right exit code but LEAKS a shell/tool
    diagnostic to stderr. Case-insensitive; deliberately NOT keyed on bare "error"."""
    haystack = result.stderr.lower()
    for token in SHELL_ERROR_TOKENS:
        assert token not in haystack, (
            f"hook leaked a shell/tool error ({token!r}); stderr={result.stderr!r}"
        )


def make_git_worktree(gate: Gate, tmp_path: Path) -> Path:
    """Turn the sandbox into a git repo with one linked worktree; return the worktree root.

    Shared by the DEFAULT-path worktree regression (B4) and the CUSTOM-path worktree pin
    (MP-1) — ONE IMPLEMENTATION, not a clone, so the two worktree pins cannot drift.
    """
    base = ["git", "-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false"]

    def git(*args: str) -> None:
        subprocess.run([*base, "-C", str(gate.root), *args], check=True, capture_output=True)

    subprocess.run(["git", "init", "-q", str(gate.root)], check=True, capture_output=True)
    (gate.root / "seed").write_text("x")
    git("add", "-A")
    git("commit", "-q", "-m", "init")
    worktree = tmp_path.parent / f"{tmp_path.name}-wt"
    git("worktree", "add", "-q", "-b", "wt", str(worktree))
    return worktree


# ── harness provenance (prove which tree) ──────────────────────────────────────


class TestHarnessProvenance:
    def test_harness_exercises_the_committed_hook_bytes(self, gate: Gate) -> None:
        """The sandbox copy is byte-identical to the committed hook.

        Bash has no ``.pth``/``__pycache__`` poison, so a byte-exact copy IS the hook — but
        pinning it means that when the builder edits the real hook, these tests exercise the
        NEW bytes automatically. WRONG BUILD KILLED: a test that quietly graded a stale or
        stub hook (the #140 "which tree am I testing?" class, in miniature).
        """
        assert gate.hook.read_bytes() == HOOK_SOURCE.read_bytes()


# ── pin 5: #121/#149 regression / removed-behavior inventory (B1–B6, GREEN on v1) ──


class TestRegressionBranchInventory:
    """v2 is a PURE WIDENING. Every branch the v1 hook has today must survive the rewrite.
    All GREEN today; each goes RED the day v2 drops the branch it pins."""

    def test_unidentifiable_payload_is_allowed(self, gate: Gate) -> None:
        """B1: no teammate name in the payload -> exit 0 (never block an unidentifiable idle).
        WRONG BUILD KILLED: a v2 that reads the contract path BEFORE the empty-name guard
        and dereferences an empty ``${teammate_name}`` under ``set -u``."""
        result = gate.run(payload={"session_id": gate.session})  # no teammate_name key
        assert_allowed(result)
        assert_no_shell_error(result)

    def test_report_at_root_is_allowed(self, gate: Gate) -> None:
        """B2 (== pin 3 default path): no contract + REPORT at root -> exit 0."""
        gate.place_root_report()
        result = gate.run()
        assert_allowed(result)

    def test_archived_report_is_allowed(self, gate: Gate) -> None:
        """B3 (#149): no contract + report archived under receipts/*/ -> exit 0.
        WRONG BUILD KILLED: a v2 whose contract-default path forgets the archive glob and
        re-opens the "green on its own target" hole #149 closed."""
        gate.place_archived_report()
        result = gate.run()
        assert_allowed(result)

    def test_worktree_report_is_allowed(self, gate: Gate, tmp_path: Path) -> None:
        """B4 (#121): no contract + report committed at a registered WORKTREE root -> exit 0.
        WRONG BUILD KILLED: a v2 that resolves the declared/default path only at the main
        root and re-breaks every worktree-assigned agent (the original #121 defect)."""
        # Place the report ONLY in the worktree so exit 0 can come only from the worktree branch.
        worktree = make_git_worktree(gate, tmp_path)
        (worktree / f"REPORT-{gate.teammate}.md").write_text("# report\n")
        try:
            assert_allowed(gate.run())
        finally:
            shutil.rmtree(worktree, ignore_errors=True)

    def test_nudge_message_carries_anti_crywolf_softener(self, gate: Gate) -> None:
        """N2 (GREEN on v1): a nudge preserves #149's anti-cry-wolf softener — the message
        tells a mid-work agent to "continue as you were", so a legitimately-waiting agent is
        not alarmed into disabling the gate (CLAUDE.md: a gate that cries wolf gets switched
        off). Single-substring pin, NOT the full wording — the builder may reword freely.
        WRONG BUILD KILLED: a v2 rewrite that keeps the terse ``idle-gate:`` line but drops
        the helpful softening body."""
        result = gate.run()  # no contract, no report -> default nudge
        assert_nudged(result)
        assert NUDGE_SOFTENER_TOKEN in result.stderr, (
            f"nudge must keep the softener {NUDGE_SOFTENER_TOKEN!r}; stderr={result.stderr!r}"
        )

    def test_one_shot_nudge_then_allowed(self, gate: Gate) -> None:
        """B5+B6: no contract + no report -> FIRST idle nudges (exit 2, writes marker),
        SECOND idle is allowed (exit 0, marker present). The one-shot semantics that stop a
        genuinely-stalled agent from being wake-looped.
        WRONG BUILD KILLED: a v2 that either never writes the marker (nudges forever) or
        writes it on an ALLOWED path (silently disarms the gate for a real stall)."""
        first = gate.run()
        assert_nudged(first)
        assert gate.nudge_marker().is_file(), "first nudge must record the one-shot marker"
        second = gate.run()
        assert_allowed(second)


# ── pin 1: owes-nothing exemption (the await / sidecar / drill case) ────────────


class TestOwesNothingExemption:
    def test_null_artifact_never_nudges_even_reportless(self, gate: Gate) -> None:
        """pin 1 (RED on v1): contract {"artifact": null} + NO report anywhere -> exit 0.
        This is the whole point of v2 — an agent that owes no artifact is never nudged.
        WRONG BUILD KILLED: v1 itself (ignores the contract, nudges); and any v2 that keys
        the exemption on report-existence rather than on the declared ``null``."""
        gate.write_contract(artifact=None)
        result = gate.run()
        assert_allowed(result)
        assert_no_shell_error(result)

    def test_null_artifact_allowed_on_repeated_idle_without_consuming_one_shot(
        self, gate: Gate
    ) -> None:
        """pin 1 (RED on v1): {"artifact": null} allowed on EVERY idle (first, repeat), and
        the exemption must NOT be implemented by burning the one-shot marker.
        WRONG BUILD KILLED: a v2 that treats ``null`` as "nudge once then allow" — its first
        idle would nudge (caught here) — or that writes a ``.nudged`` marker on the exempt
        path (caught by the marker assertion)."""
        gate.write_contract(artifact=None)
        first = gate.run()
        assert_allowed(first)
        second = gate.run()
        assert_allowed(second)
        assert not gate.nudge_marker().exists(), (
            "an owes-nothing exemption must not consume the one-shot nudge marker"
        )

    def test_positive_control_owed_report_missing_still_nudges(self, gate: Gate) -> None:
        """pin 1 POSITIVE CONTROL (GREEN on v1, load-bearing): contract declaring an OWED
        report that is absent -> exit 2, still nudges. Proves the ``null`` exemption above is
        keyed on the VALUE, not a blanket "contract present -> allow".
        WRONG BUILD KILLED: a v2 that exits 0 whenever a contract file exists (which would
        pass every null test while disabling the gate entirely)."""
        gate.write_contract(artifact=f"REPORT-{gate.teammate}.md")
        result = gate.run()
        assert_nudged(result)


# ── pin 2: custom artifact path (kills the hardcoded REPORT-<name>.md) ──────────


class TestCustomArtifactPath:
    def test_custom_artifact_present_is_allowed(self, gate: Gate) -> None:
        """pin 2 (RED on v1): contract {"artifact": "docs/design/FOO.md"} + that file present
        (and NO REPORT-<name>.md) -> exit 0.
        WRONG BUILD KILLED: v1 and any v2 that still checks the hardcoded REPORT-<name>.md
        instead of the declared path."""
        gate.write_contract(artifact="docs/design/FOO.md")
        gate.place("docs/design/FOO.md")
        result = gate.run()
        assert_allowed(result)

    def test_custom_artifact_absent_nudges(self, gate: Gate) -> None:
        """pin 2 control (GREEN on v1): custom path declared but absent everywhere -> exit 2.
        WRONG BUILD KILLED: a v2 that exits 0 for any non-null artifact without checking the
        filesystem."""
        gate.write_contract(artifact="docs/design/FOO.md")
        result = gate.run()
        assert_nudged(result)

    def test_mp1_custom_artifact_at_worktree_root_is_allowed(
        self, gate: Gate, tmp_path: Path
    ) -> None:
        """MP-1 (RED on v1; kills WB5 root-only). Operator reading (x): a custom declared path
        resolves at root + WORKTREES. A custom artifact committed ONLY at a linked worktree
        root -> exit 0. This is #121 re-opened for the custom path — a v2 that applies the
        worktree walk only to the default REPORT-<name>.md falsely nudges a worktree-assigned
        agent that declared a custom artifact.
        DISCRIMINATION (proven in the report §Discrimination): v2-correct -> 0, wb5 -> 2."""
        gate.write_contract(artifact="docs/design/FOO.md")
        worktree = make_git_worktree(gate, tmp_path)
        (worktree / "docs" / "design").mkdir(parents=True)
        (worktree / "docs" / "design" / "FOO.md").write_text("# report\n")
        try:
            assert_allowed(gate.run())
        finally:
            shutil.rmtree(worktree, ignore_errors=True)

    def test_mp2_custom_artifact_under_archive_basename_still_nudges(self, gate: Gate) -> None:
        """MP-2 (GREEN on v1; kills WB6 basename-glob AND ND-1 wb-r2-fullpath-archive).
        Operator reading (x): the receipts/*/ archive glob stays scoped to the REPORT-<name>.md
        default — there is NO archive glob for a custom path. The declared path
        ``docs/design/FOO.md`` is absent at root/worktree, but a matching file sits under
        receipts/*/ in BOTH natural archive layouts — its BASENAME (``FOO.md``) and its FULL
        declared path (``docs/design/FOO.md``). Correct v2 ignores both (no custom archive
        glob) -> exit 2. GREEN on v1 (v1's archive glob targets REPORT-<name>.md, also absent)
        — its discrimination is vs the two archive-glob wrong builds, NOT vs v1.
        DISCRIMINATION (proven in the report §Discrimination): v2-correct -> 2, wb6 -> 0,
        wb-r2-fullpath-archive -> 0.
        ⚠ STOP-RULE (reach-attack rule): the two NATURAL archive readings (basename, full path)
        are both closed here; deeper globs are adversarial-only. This IS the pinned bound — do
        NOT chase further readings."""
        gate.write_contract(artifact="docs/design/FOO.md")
        gate.place(ARCHIVE_SUBDIR / "FOO.md")  # reading (y): declared path's BASENAME under receipts/*/
        gate.place(ARCHIVE_SUBDIR / "docs" / "design" / "FOO.md")  # ND-1: FULL declared path in archive
        result = gate.run()
        assert_nudged(result)

    def test_mp4_custom_absent_one_shot_then_allowed(self, gate: Gate) -> None:
        """MP-4 (GREEN on v1; kills WB10 wake-loop): a custom-declared artifact absent
        everywhere, idle TWICE -> first exit 2 (nudge + marker), second exit 0 (marker
        consumed). The one-shot must protect the CUSTOM nudge path too, not just the default —
        else a custom-owing reportless agent is wake-looped on every idle.
        DISCRIMINATION (proven in the report §Discrimination): v2-correct -> (2, 0),
        wb10 -> (2, 2)."""
        gate.write_contract(artifact="docs/design/FOO.md")
        first = gate.run()
        assert_nudged(first)
        assert gate.nudge_marker().is_file(), "first custom-path nudge must record the marker"
        second = gate.run()
        assert_allowed(second)


# ── pin 3: absent contract -> fail-open to v1 (the #131 no-crash leg) ───────────


class TestAbsentContractFailsOpenToV1:
    def test_absent_contract_with_root_report_is_allowed(self, gate: Gate) -> None:
        """pin 3 (GREEN on v1): NO contract file + REPORT at root -> exit 0 (v1 default).
        This is why v2 is shippable standalone: with no contract written, it is v1."""
        gate.place_root_report()
        result = gate.run()
        assert_allowed(result)
        assert_no_shell_error(result)

    def test_absent_contract_reportless_nudges_without_crashing(self, gate: Gate) -> None:
        """pin 3 / #131 leg (GREEN on v1): NO contract + no report -> exit 2 with NO
        ``set -u`` crash. A missing contract must never abort the hook.
        WRONG BUILD KILLED: a v2 that dereferences an unset contract variable (unbound
        variable) or ``exit 1``s when the contract file is absent."""
        result = gate.run()
        assert_nudged(result)
        assert_no_shell_error(result)


# ── pin 4: malformed contract -> fail-open to v1 (guards a crashing v2) ─────────


class TestMalformedContractFailsOpen:
    def test_garbage_json_with_root_report_is_allowed(self, gate: Gate) -> None:
        """pin 4 (GREEN on v1, guards v2): unparseable contract + REPORT at root -> exit 0.
        WRONG BUILD KILLED: a v2 that lets a jq parse error abort under ``set -e``/``set -u``
        instead of falling open to the v1 default."""
        gate.write_raw_contract("this is not json {{{ ]]]")
        gate.place_root_report()
        result = gate.run()
        assert_allowed(result)
        assert_no_shell_error(result)

    def test_garbage_json_reportless_nudges_without_crashing(self, gate: Gate) -> None:
        """pin 4 (GREEN on v1, guards v2): unparseable contract + no report -> exit 2, no crash."""
        gate.write_raw_contract("}{ not json")
        result = gate.run()
        assert_nudged(result)
        assert_no_shell_error(result)

    def test_contract_missing_artifact_key_report_present_falls_open(self, gate: Gate) -> None:
        """pin 4 (GREEN on v1): well-formed JSON lacking ``artifact`` + REPORT at root -> exit
        0 (missing-key -> v1 default, report present). ⚠ This is the report-PRESENT half and
        CANNOT discriminate WB7 (missing-key-treated-as-owes-nothing): both correct-v2 and WB7
        exit 0 here because the owed report exists. Its discriminating twin is MP-3 below
        (reportless). Kept as the fail-open positive case; MP-3 supplies the kill."""
        gate.write_raw_contract(json.dumps({"unrelated": 1}))
        gate.place_root_report()
        result = gate.run()
        assert_allowed(result)
        assert_no_shell_error(result)

    def test_mp3_missing_artifact_key_reportless_nudges(self, gate: Gate) -> None:
        """MP-3 (GREEN on v1; kills WB7): a well-formed contract lacking the ``artifact`` key
        (``{"unrelated": 1}``) with NO report anywhere -> exit 2. Spec: missing-key -> v1
        default -> reportless -> nudge. The natural naive parse ``jq -r '.artifact'`` yields
        the string ``"null"`` for BOTH ``{"artifact":null}`` AND a missing key, so a build
        that treats ``"null"`` as owes-nothing silently exempts an agent whose contract is
        malformed by a typo'd/absent key even though it OWES a report. The report-present twin
        above cannot see this; the reportless fixture is what discriminates.
        DISCRIMINATION (proven in the report §Discrimination): v2-correct -> 2, wb7 -> 0."""
        gate.write_raw_contract(json.dumps({"unrelated": 1}))
        result = gate.run()
        assert_nudged(result)
        assert_no_shell_error(result)

    def test_empty_contract_file_falls_open(self, gate: Gate) -> None:
        """pin 4 (GREEN on v1, guards v2): a zero-byte contract file + no report -> exit 2
        (treated as absent -> v1 default), no crash."""
        gate.write_raw_contract("")
        result = gate.run()
        assert_nudged(result)
        assert_no_shell_error(result)


# ── pin 6: reach is a CHECKED VARIABLE (INSTRUMENT-0) ───────────────────────────


class TestReachIsCheckedVariable:
    def test_checked_path_tracks_the_contract_value(self, gate: Gate) -> None:
        """pin 6 (RED on v1): the path the hook checks is READ FROM the contract, not a
        hidden constant. With ``A.md`` present at root the whole time:
          - agent whose contract declares ``A.md`` -> exit 0 (found)
          - agent whose contract declares ``B.md`` (absent) -> exit 2 (nudged)
        Same filesystem, different declared value, different outcome => the hook consults the
        contract. This is the pin that stops v2 from becoming another hardcoded-name guard —
        the exact defeat class in CLAUDE.md's instrument-lesson table.
        WRONG BUILD KILLED: v1 (ignores the contract: both -> exit 2, so the A assertion
        fails RED today) AND any v2 that hardcodes one path and ignores the declared value."""
        gate.place("A.md")
        who_a = uuid.uuid4().hex[:12]
        who_b = uuid.uuid4().hex[:12]
        gate.write_contract(artifact="A.md", teammate=who_a)
        gate.write_contract(artifact="B.md", teammate=who_b)  # B.md is never placed
        result_a = gate.run(teammate=who_a)
        result_b = gate.run(teammate=who_b)
        assert_allowed(result_a)  # declared A.md, present -> allowed
        assert_nudged(result_b)   # declared B.md, absent  -> nudged
