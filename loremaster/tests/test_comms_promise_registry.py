"""Packet 02 — the PROMISE-STRING completeness instrument (#104 "keep the class dead").

A DIAGNOSIS IS NOT AN INSTRUMENT (repo CLAUDE.md): the repo already KNEW "defects
cluster in natural-language surfaces whose consistency with code no gate checks",
and shipped ten more anyway. Every other invariant here has a mechanical guard
(types, AST pins, schema ASSERTs, query-count pins); served English had none. This
module is that guard for the comms render surface.

DESIGN — ALLOWLIST THE SAFE (repo instrument-lesson: "the forbidden set is unbounded;
the safe set is small and enumerable — so allowlist the safe"). We do NOT enumerate
"what is a promise-string". Instead: EVERY ``render_line``/``render_join`` template
literal that appears inside a comms render function (``_render_comms_*`` / ``_comms_*``)
in server.py MUST be CLASSIFIED — either

  * in :data:`_PROMISE_REGISTRY` — it carries a promise/imperative, tagged with the
    PREDICATE under which its promised mechanism actually runs (§9.7's litmus:
    *if the reader acted on this line — waited for the heartbeat, ran the taught command
    WITH ITS DEFAULTS — would the promised thing happen for THIS input?*); or
  * in :data:`_PROMISE_FREE` — it is a status report / label / separator / pure advice
    that promises NO runtime mechanism, tagged with the reason.

Default is FAIL: an UNCLASSIFIED literal fails :meth:`test_every_comms_render_literal_
is_classified`, reusing the default-FAIL discipline of ``assert_actions_covered`` /
the RenderCase battery one level up. When a builder adds a new served promise, the
guard goes RED until the author registers it WITH ITS PREDICATE — which forces them
to answer §9.7's litmus for the new line, mechanically, instead of by hope.

COVERAGE IS A CHECKED VARIABLE (repo law — "a gate is an invariant only over code it
RUNS"): :meth:`test_the_scan_reached_every_comms_render_helper` asserts the scan
observed a literal from every ``_render_comms_*`` helper that emits any, so a renamed
or added helper cannot make the guard vacuously pass by scanning nothing.

WHERE THE "EMIT IFF PREDICATE" PROOFS LIVE: the behavioural half — a served line is
emitted IFF its predicate holds — has two homes. A REPRESENTATIVE set is pinned in
``test_comms_render_architecture.py`` (``TestFirstVersionTailIsTypedNotNameDerived`` for
the register-ack promise; ``TestSkewTailIsNameConditioned`` for the three heartbeat-
surfacing tails, ∀ the (is-standing, has-unbriefed) predicate combinations). The
EXHAUSTIVE per-entry mechanization is packet 02a's ``_PROMISE_PROOFS`` below: EVERY
:data:`_PROMISE_REGISTRY` entry drives the REAL render with its predicate TRUE (the line
MUST emit) and FALSE (it MUST NOT), with ``set(_PROMISE_PROOFS) == set(_PROMISE_REGISTRY)``
a CHECKED invariant (registered ⟺ proven) — so a future author cannot register a promise
whose predicate never actually gates its emission. This module is also the STATIC
completeness half — that no promise ships UNregistered.

PACKET 02a also CLOSES the ``safe_str(f"...")`` literal-text residual (once documented in
:data:`_SAFE_STR_LITERAL_RESIDUAL`): promise/imperative text assembled via
``safe_str``/``sanitise_line`` call arguments (or concatenation, or a local variable
feeding one) rather than a ``render_line`` template is now SCANNED and classified by
``_comms_render_safe_str_literals`` (default-FAIL against :data:`_SAFE_STR_PROMISE_FREE`),
coverage-checked and self-attacked. See REPORT-pkt02-contract.md §E for the original
sizing split.

RED expectation: this module is GREEN against the correct build (every literal is
classified) — it is a completeness INVARIANT, not a fix-pin. Its self-attack tests
(``TestTheGuardActuallyCatchesViolations``) prove it is a REAL detector: a synthetic
unclassified promise is caught, and a positive control (a correctly-registered promise)
passes — so a green result here is never vacuous.
"""

from __future__ import annotations

import ast
import inspect
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import loremaster.server as server_module
import pytest
from _comms_fakes import FakeAgentRegistry, FakeBriefLedger
from loremaster.agents import Agent, AgentFleetWindow, AgentStatus
from loremaster.briefs import Brief, BriefAckResult, BriefBehindEntry, BriefPublishResult
from loremaster.server import AppContext

_SERVER_PY = Path(inspect.getfile(AppContext)).resolve().parent / "server.py"

_RENDER_VERB_NAMES: frozenset[str] = frozenset({"render_line", "render_join"})


# --------------------------------------------------------------------------- #
# THE REGISTRY — every promise/imperative comms render literal + its predicate.
# The predicate is §9.7's litmus made explicit: under exactly what input does the
# promised mechanism run? A new served promise MUST be added here (RED until it is),
# which forces its author to answer that question mechanically.
# --------------------------------------------------------------------------- #
_PROMISE_REGISTRY: dict[str, str] = {
    "brief '{name}' v{version} (published {age} ago by {author}) — ack recorded (via register)": (
        "register auto-ack — rendered ONLY for the standing brief at register, which "
        "register just acked (§9.7 #1)"
    ),
    "echo in your report: brief project v{version} read": (
        "report-echo imperative — always available to the addressed agent (§9.7 #3)"
    ),
    "no 'project' brief published yet — work from your spawn brief; "
    "re-check with lore_comms action=brief_get": (
        "brief_get default='project' — the line is ABOUT 'project'; the default resolves "
        "to it (§9.7 #2)"
    ),
    "brief 'project' v{head} is head — you acked v{acked}; "
    "catch up: lore_comms action=brief_get": (
        "brief_get default='project' — project-only skew line, default correct, byte-stable "
        "(§9.7 #4)"
    ),
    "you have not acked brief 'project' (head v{head}) — lore_comms action=brief_get": (
        "brief_get default='project' — project unbriefed notice (§9.7 #5)"
    ),
    "brief '{name}' v{head} is head — you acked v{acked}; "
    "catch up: lore_comms action=brief_get name='{name}'": (
        "brief_get BY NAME — the subscribed-name skew line carries an EXPLICIT name= "
        "teach (a bare brief_get would read 'project'); the name's head was just read, so "
        "it exists (§9.7 #6, v8)"
    ),
    "behind on {k} more briefs: {names} (+{extra} more) — brief_get each by name": (
        "brief_get by name — the collapsed remainder names subscribed+published names (§9.7 #7)"
    ),
    "behind on {k} more briefs: {names} — brief_get each by name": (
        "brief_get by name — the collapsed remainder names subscribed+published names (§9.7 #7)"
    ),
    "brief '{name}' v{version} published by {publisher} — first version; "
    "agents ack at register": (
        "register auto-ack — emitted IFF auto_ack_at_register is True (the standing role); "
        "pinned emit-IFF in TestFirstVersionTailIsTypedNotNameDerived (§9.7 #8, v8)"
    ),
    "brief '{name}' v{version} published by {publisher} — first version; "
    "agents ack with lore_comms action=brief_ack": (
        "brief_ack — emitted IFF auto_ack_at_register is False; brief_ack runs for any "
        "existing (name, version) (§9.7 #9, v8)"
    ),
    "skew (session {session}): {behind} non-retired agents behind head v{head} — "
    "{breakdown}; surfaces at their next heartbeat": (
        "heartbeat skew surfacing — tail 1/2: emitted IFF standing OR the unbriefed group is "
        "empty (every behind agent then a subscriber); pinned in TestSkewTailIsNameConditioned "
        "(§9.7 #10, v8)"
    ),
    "skew: {behind} non-retired agents behind head v{head} — "
    "{breakdown}; surfaces at their next heartbeat": (
        "heartbeat skew surfacing — tail 1/2, unscoped variant (§9.7 #10, v8)"
    ),
    "skew (session {session}): {behind} non-retired agents behind head v{head} — "
    "{breakdown}; ackers see it at next heartbeat — unbriefed agents only via "
    "brief_get name='{name}'": (
        "heartbeat surfacing for ackers + brief_get name= for unbriefed — tail 3: emitted IFF "
        "non-standing AND the unbriefed group is non-empty (unbriefed non-project agents are "
        "never nagged) (§9.7 #10, v8)"
    ),
    "skew: {behind} non-retired agents behind head v{head} — "
    "{breakdown}; ackers see it at next heartbeat — unbriefed agents only via "
    "brief_get name='{name}'": (
        "heartbeat surfacing for ackers + brief_get name= for unbriefed — tail 3, unscoped "
        "variant (§9.7 #10, v8)"
    ),
    "acked brief '{name}' v{version} — head is v{head}; "
    "catch up: lore_comms action=brief_get name='{name}'": (
        "brief_get BY NAME — the behind-ack teach carries explicit name= for EVERY name so a "
        "non-'project' reader is not sent to the wrong brief (§9.7 #11, v8/instance 10)"
    ),
    "+{more} more — re-run with limit={next_limit}": (
        "fleet limit= re-ask — actionable IFF shown < display cap; the cap-disclosure variant "
        "handles the dead-end case (§9.7 #12, sound since v4)"
    ),
}

# --------------------------------------------------------------------------- #
# THE PROMISE-FREE SET — status reports, labels, separators, pure advice. Each
# carries a reason. Being here is a POSITIVE declaration "this promises nothing",
# not silence — the default is still FAIL.
# --------------------------------------------------------------------------- #
_PROMISE_FREE: dict[str, str] = {
    "registered {name} (session {session}, role {role}) — status active": "status report",
    "re-registered {name} (session {session}, role {role}) — status active "
    "(first registered {age} ago)": "status report",
    "heartbeat {name} — status {status}": "status report",
    "coverage: {current}/{total} non-retired agents at v{version}; behind: {behind}": "status report",
    "coverage: all {n} non-retired agents at v{version}": "status report",
    "coverage: {current}/{total} non-retired agents at v{version}; behind: {behind} (+{more} more)": (
        "status report"
    ),
    "coverage (session {session}): {current}/{total} non-retired agents at v{version}; "
    "behind: {behind}": "status report",
    "coverage (session {session}): all {n} non-retired agents at v{version}": "status report",
    "coverage (session {session}): {current}/{total} non-retired agents at v{version}; "
    "behind: {behind} (+{more} more)": "status report",
    "brief '{name}' v{version} (published {age} ago by {author})": "status report (brief_get header)",
    "brief '{name}' v{version} published by {publisher}": "status report (publish line)",
    "⚠ body {chars} chars exceeds the {threshold}-char warn threshold — briefs are "
    "standing instructions; prefer a doc + pointer": "advice, promises no runtime mechanism (§9.7 #19)",
    "already acked brief '{name}' v{version} — no new edge": "status report (idempotent ack)",
    "acked brief '{name}' v{version} (head)": "status report (head ack)",
    "- {name} [{status}] hb {age} · {cells}": "fleet row structural template",
    "- {name} [{status} ⚠ STALE] hb {age} · {cells}": "fleet row structural template (stale variant)",
    "fleet (session {session}): {total} non-retired agents — {parked} input_required, "
    "{active} active, {idle} idle": "status report (fleet header)",
    "fleet: {total} non-retired agents — {parked} input_required, {active} active, {idle} idle": (
        "status report (fleet header, unscoped)"
    ),
    "no agents registered": "status report (empty fleet)",
    "no agents registered (session {session})": "status report (empty fleet, scoped)",
    "+{count} retired": "status report (retired trailer)",
    "session {session}:": "label (per-session group header)",
    "+{more} more beyond the display cap ({cap})": "discloses the cap, promises nothing (§9.7 #13)",
    ", ": "join separator",
    " ": "join separator",
    " · ": "join separator",
}

# CLOSED by packet 02a. The residual once documented here — a promise smuggled through
# ``safe_str(f"...")`` / ``sanitise_line(...)`` LITERAL TEXT (or string concatenation, or
# a local variable feeding one) rather than a render_line/render_join template — is now
# SCANNED and classified by ``_comms_render_safe_str_literals`` below (default-FAIL against
# :data:`_SAFE_STR_PROMISE_FREE` / :data:`_PROMISE_REGISTRY`), coverage-checked in
# ``TestTheSafeStrScanReachedEveryHelper`` and self-attacked in
# ``TestTheSafeStrGuardCatchesViolations``. The one REMAINING bound — a promise assembled
# in a NON-comms helper and passed in via a call (cross-FUNCTION flow, which this AST-local
# scanner does not follow) — is PINNED as a known bound in ``TestSafeStrLiteralCoverageBound``.
_SAFE_STR_LITERAL_RESIDUAL = (
    "CLOSED (02a): safe_str/sanitise_line literal text in comms render funcs is scanned by "
    "_comms_render_safe_str_literals(); only cross-function flow remains, a pinned known bound"
)


def _called_name(func: ast.expr) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _comms_render_literals() -> list[tuple[str, int, str]]:
    """Every ``render_line``/``render_join`` template LITERAL (function, lineno, text)
    that appears inside a comms render/handler function in server.py. Implicit string
    concatenation is already joined by the parser into one ``ast.Constant``."""
    tree = ast.parse(_SERVER_PY.read_text(encoding="utf-8"), filename="server.py")
    literals: list[tuple[str, int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if not (node.name.startswith("_render_comms") or node.name.startswith("_comms_")):
            continue
        for sub in ast.walk(node):
            if not (isinstance(sub, ast.Call) and _called_name(sub.func) in _RENDER_VERB_NAMES):
                continue
            if not sub.args:
                continue
            template = sub.args[0]
            if isinstance(template, ast.Constant) and isinstance(template.value, str):
                literals.append((node.name, sub.lineno, template.value))
    return literals


def _classified() -> frozenset[str]:
    return frozenset(_PROMISE_REGISTRY) | frozenset(_PROMISE_FREE)


class TestEveryCommsRenderLiteralIsClassified:
    """Allowlist-the-safe, default-FAIL: an unregistered promise cannot ship."""

    def test_every_comms_render_literal_is_classified(self) -> None:
        classified = _classified()
        unclassified = [
            (fn, line, text)
            for fn, line, text in _comms_render_literals()
            if text not in classified
        ]
        assert not unclassified, (
            "a comms render template literal is UNCLASSIFIED — every served line must be "
            "registered WITH ITS PREDICATE (_PROMISE_REGISTRY) or declared promise-free "
            "(_PROMISE_FREE). Answer §9.7's litmus for each and register it (#104):\n"
            + "\n".join(f"  {fn}:{line}: {text!r}" for fn, line, text in unclassified)
        )

    def test_registry_and_free_sets_are_disjoint(self) -> None:
        overlap = frozenset(_PROMISE_REGISTRY) & frozenset(_PROMISE_FREE)
        assert not overlap, f"a literal is BOTH a promise and promise-free: {sorted(overlap)!r}"

    def test_no_dead_registry_entries(self) -> None:
        """Every classified literal must actually be EMITTED by a comms render — a
        registry that outlives its literal is prose rotting beside code (the class this
        instrument exists to kill), and it would let a real promise hide behind a stale
        key that merely LOOKS covered."""
        live = {text for _fn, _line, text in _comms_render_literals()}
        dead = sorted(text for text in _classified() if text not in live)
        assert not dead, (
            "classified literal(s) no longer emitted by any comms render — remove the stale "
            "registry/free entry:\n" + "\n".join(f"  {text!r}" for text in dead)
        )


class TestTheScanReachedEveryCommsRenderHelper:
    """Coverage is a CHECKED variable: prove the scan is not vacuously passing."""

    def test_the_scan_reached_every_comms_render_helper_that_emits(self) -> None:
        observed_functions = {fn for fn, _line, _text in _comms_render_literals()}
        # Every render helper that composes served lines must have contributed at least
        # one scanned literal; a helper renamed out of the `_render_comms`/`_comms_`
        # prefix, or one that started emitting via an unscanned path, drops out here.
        expected = {
            "_render_comms_register",
            "_render_comms_heartbeat",
            "_render_comms_brief_coverage_line",
            "_render_comms_brief_get",
            "_render_comms_brief_publish",
            "_render_comms_brief_ack",
            "_render_comms_fleet_row",
            "_render_comms_fleet",
        }
        missing = expected - observed_functions
        assert not missing, (
            "the promise scan did not observe a render literal from every known comms "
            f"render helper — it may be scanning nothing (coverage hole): {sorted(missing)!r}"
        )

    def test_at_least_the_known_promise_count_is_present(self) -> None:
        # A blunt non-vacuity floor: the surface has many promise/imperative lines; if the
        # scan suddenly sees a handful, something narrowed the scan, not the surface.
        assert len(_comms_render_literals()) >= 30, len(_comms_render_literals())


class TestTheGuardActuallyCatchesViolations:
    """SELF-ATTACK (repo law: a probe needs a control). Prove the guard is a REAL
    detector — it catches an unclassified promise AND a promise-emitted shape — with a
    POSITIVE control (a correctly-registered literal passes). Built on synthetic inputs
    so the attack never depends on mutating the production tree."""

    @staticmethod
    def _scan_source(source: str) -> list[str]:
        """The guard's classifier applied to arbitrary source — the same walk as
        :func:`_comms_render_literals`, over a synthetic module string."""
        tree = ast.parse(source)
        found: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            if not (node.name.startswith("_render_comms") or node.name.startswith("_comms_")):
                continue
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call) and _called_name(sub.func) in _RENDER_VERB_NAMES and sub.args:
                    template = sub.args[0]
                    if isinstance(template, ast.Constant) and isinstance(template.value, str):
                        found.append(template.value)
        return found

    def test_catches_a_new_unclassified_promise_literal(self) -> None:
        """(i) a builder adds a NEW promise-bearing line and forgets to register it."""
        hostile = (
            "def _render_comms_new(x):\n"
            "    return render_line('do the thing: lore_comms action=teleport now')\n"
        )
        literals = self._scan_source(hostile)
        unclassified = [text for text in literals if text not in _classified()]
        assert unclassified == ["do the thing: lore_comms action=teleport now"], unclassified

    def test_positive_control_a_registered_literal_is_accepted(self) -> None:
        """POSITIVE control: an EXISTING registered promise literal, in a synthetic comms
        render func, is NOT flagged — so the guard accepts the good case, and its red on
        the hostile case above is discrimination, not blanket rejection."""
        known = "brief 'project' v{head} is head — you acked v{acked}; catch up: lore_comms action=brief_get"
        assert known in _PROMISE_REGISTRY  # sanity: it is registered
        benign = f"def _render_comms_ok(x):\n    return render_line({known!r})\n"
        literals = self._scan_source(benign)
        unclassified = [text for text in literals if text not in _classified()]
        assert unclassified == [], unclassified

    def test_ignores_a_render_call_outside_a_comms_function(self) -> None:
        """A different-reason negative: a render_line in a NON-comms function is not the
        comms surface and must not be scanned (so a hit is never for the wrong reason)."""
        outside = (
            "def _render_finding_detail(x):\n"
            "    return render_line('some other surface: action=whatever')\n"
        )
        assert self._scan_source(outside) == []


# =========================================================================== #
# PACKET 02a — ITEM 1: per-entry EXECUTABLE-predicate emission proofs.
#
# For EACH _PROMISE_REGISTRY literal, drive the REAL render with the predicate
# TRUE (the promise line MUST emit) and FALSE (it MUST NOT). This MECHANIZES
# §9.7's mechanism-promise sweep so a future author cannot register a promise
# whose predicate never actually gates its emission. Design B2 (see
# REPORT-pkt02a-builder.md): a PARALLEL _PROMISE_PROOFS map keyed by the SAME
# literals, with ``set(_PROMISE_PROOFS) == set(_PROMISE_REGISTRY)`` a checked
# invariant — registered ⟺ proven. B2 leaves the shipped _PROMISE_REGISTRY (and
# its §9.7 predicate prose) untouched (minimal blast radius on deployed code)
# while making the completeness link one direct set-equality.
#
# A PROBE NEEDS A CONTROL (repo law): each proof's EMIT leg is the positive
# control (the marker CAN appear) and the NO-EMIT leg is the discrimination (the
# predicate GATES it) — together they distinguish the correct render from one
# that emits the line regardless of predicate. Byte-exact markers (U+2014 "—"
# via ``_EM_DASH``) are validated by the EMIT leg: a transcription slip fails to
# be found and goes RED at authoring time.
# =========================================================================== #

# The em-dash the render templates use verbatim (U+2014) — mirrors
# ``test_comms_render_architecture.py``'s ``_EM_DASH`` discipline so a marker
# transcription slip fails loudly rather than silently weakening a match.
_EM_DASH = "—"


# --- value-object builders (trivial constructors, not policy — the DRY law's
# "duplicating trivia is cheap" side; id RECIPES are REUSED from the shared
# ``_comms_fakes`` fakes rather than re-derived, per the ONE-implementation law).
def _agent(
    name: str = "fixer-b",
    *,
    session: str = "wave7",
    role: str = "builder",
    status: AgentStatus = "active",
    model: str | None = None,
    task_id: str | None = None,
    last_note: str | None = None,
) -> Agent:
    now = datetime.now(UTC)
    return Agent(
        id=FakeAgentRegistry._agent_id(session, name),
        name=name,
        session=session,
        role=role,
        model=model,
        status=status,
        spawned_by=None,
        task_id=task_id,
        checkpoint=None,
        last_note=last_note,
        registered_at=now,
        heartbeat_at=now,
    )


def _brief(*, name: str, version: int, created_by: str = "lead", body: str = "the body") -> Brief:
    return Brief(
        id=FakeBriefLedger._brief_id(name, version),
        name=name,
        version=version,
        body=body,
        created_by=created_by,
        note=None,
        created_at=datetime.now(UTC),
    )


def _publish_result(*, name: str, version: int, first_version: bool) -> BriefPublishResult:
    return BriefPublishResult(brief=_brief(name=name, version=version), first_version=first_version)


def _ack_result(*, name: str, version: int, head: int, already: bool = False) -> BriefAckResult:
    return BriefAckResult(
        name=name, version=version, head_version=head, already_acked=already, via="explicit"
    )


def _behind(name: str, acked: int | None) -> BriefBehindEntry:
    return BriefBehindEntry(agent_name=name, acked_version=acked)


def _skew_fixture(count: int) -> list[tuple[str, int, int]]:
    """``count`` subscribed-skew ``(name, head, acked)`` tuples with DISTINCT
    skews (magnitude ``i+1``), so the render's skew-descending sort is total and
    the cap/collapse arithmetic is unambiguous."""
    return [(f"n{i:02d}", 100, 100 - (i + 1)) for i in range(count)]


# --- render drivers: each wraps the REAL AppContext render helper so the proofs
# below vary only the predicate inputs (the TestSkewTailIsNameConditioned idiom).
def _render_register(*, brief: Brief | None) -> str:
    return str(
        AppContext._render_comms_register(
            _agent(), re_registered=False, registered_age_s=5, brief=brief, brief_age_s=10
        )
    )


def _render_heartbeat(
    *, project_head: int | None, project_acked: int | None, subscribed: list[tuple[str, int, int]]
) -> str:
    return str(
        AppContext._render_comms_heartbeat(
            _agent(),
            project_head_version=project_head,
            project_acked_version=project_acked,
            subscribed_skew=subscribed,
        )
    )


def _render_publish(
    *,
    name: str,
    version: int,
    first_version: bool,
    session: str | None,
    behind: list[BriefBehindEntry],
    auto_ack: bool,
) -> str:
    return str(
        AppContext._render_comms_brief_publish(
            _publish_result(name=name, version=version, first_version=first_version),
            session=session,
            behind=behind,
            body_chars=10,
            warn_threshold_chars=4000,
            auto_ack_at_register=auto_ack,
        )
    )


def _render_ack(*, name: str, version: int, head: int) -> str:
    return str(AppContext._render_comms_brief_ack(_ack_result(name=name, version=version, head=head)))


def _render_fleet(*, rows: list[Agent], total_active: int, limit: int, session: str | None = "wave7") -> str:
    window = AgentFleetWindow(rows=rows, retired_count=0, total_non_retired=total_active)
    status_counts = {"active": total_active, "idle": 0, "input_required": 0, "retired": 0}
    return str(
        AppContext._render_comms_fleet(
            window,
            session=session,
            limit=limit,
            stale_after_s=600,
            project_head_version=None,
            acked_versions={},
            heartbeat_age_seconds={},
            status_counts=status_counts,
        )
    )


# The two collapse-cap proofs (7a/7b) size their fixtures RELATIVE to the caps
# the render reads (repo law: derive from the constant, never hardcode a value
# the code owns), so a cap change re-derives the fixture instead of silently
# unbinding the branch.
_SKEW_CAP = server_module._HEARTBEAT_SKEW_NAMES_CAP
_COV_CAP = server_module._COVERAGE_NAMES_CAP
# 7a: len > cap AND remainder(=len-cap) > cov_cap  ->  the "(+{over} more)" variant.
_P7A_LEN = _SKEW_CAP + _COV_CAP + 1
_P7A_OVER = (_P7A_LEN - _SKEW_CAP) - _COV_CAP
_P7A_MARKER = f" (+{_P7A_OVER} more) {_EM_DASH} brief_get each by name"
# 7b: len > cap AND remainder <= cov_cap  ->  the no-"+extra" variant.
_P7B_LEN = _SKEW_CAP + 1
_P7B_REMAINDER = _P7B_LEN - _SKEW_CAP


@dataclass(frozen=True)
class PromiseProof:
    """An executable proof that a registered promise's predicate GATES its
    emission at the REAL render. ``marker`` is a byte-exact substring the line
    emits; ``render_emit``/``render_no_emit`` drive the render with the predicate
    TRUE / FALSE respectively."""

    literal: str
    marker: str
    render_emit: Callable[[], str]
    render_no_emit: Callable[[], str]


def _assert_predicate_gates(proof: PromiseProof) -> None:
    """Both proof legs (a probe needs a control): the EMIT leg proves the marker
    CAN appear (positive control), the NO-EMIT leg proves the predicate GATES it
    (discrimination). A render that emits regardless of predicate fails NO-EMIT;
    one that never emits fails EMIT."""
    emitted = proof.render_emit()
    assert proof.marker in emitted, (
        f"EMIT leg: predicate TRUE did not render {proof.marker!r} for "
        f"{proof.literal!r} — the marker cannot appear (byte-exact/transcription "
        f"check too): {emitted!r}"
    )
    withheld = proof.render_no_emit()
    assert proof.marker not in withheld, (
        f"NO-EMIT leg: predicate FALSE still rendered {proof.marker!r} for "
        f"{proof.literal!r} — the predicate does NOT gate emission (a render that "
        f"emits the line regardless would pass every other pin): {withheld!r}"
    )


_PROOF_LIST: list[PromiseProof] = [
    # --- register (§9.7 #1/#2/#3): brief present vs the bootstrap path. -------
    PromiseProof(
        literal="brief '{name}' v{version} (published {age} ago by {author}) — "
        "ack recorded (via register)",
        marker=f"{_EM_DASH} ack recorded (via register)",
        render_emit=lambda: _render_register(brief=_brief(name="project", version=1)),
        render_no_emit=lambda: _render_register(brief=None),
    ),
    PromiseProof(
        literal="echo in your report: brief project v{version} read",
        marker="echo in your report: brief project v1 read",
        render_emit=lambda: _render_register(brief=_brief(name="project", version=1)),
        render_no_emit=lambda: _render_register(brief=None),
    ),
    PromiseProof(
        literal="no 'project' brief published yet — work from your spawn brief; "
        "re-check with lore_comms action=brief_get",
        marker="no 'project' brief published yet",
        render_emit=lambda: _render_register(brief=None),
        render_no_emit=lambda: _render_register(brief=_brief(name="project", version=1)),
    ),
    # --- heartbeat (§9.7 #4/#5/#6/#7): project skew, unbriefed, subscribed. ---
    PromiseProof(
        literal="brief 'project' v{head} is head — you acked v{acked}; "
        "catch up: lore_comms action=brief_get",
        marker=f"brief 'project' v2 is head {_EM_DASH} you acked v1; "
        "catch up: lore_comms action=brief_get",
        render_emit=lambda: _render_heartbeat(project_head=2, project_acked=1, subscribed=[]),
        render_no_emit=lambda: _render_heartbeat(project_head=2, project_acked=2, subscribed=[]),
    ),
    PromiseProof(
        literal="you have not acked brief 'project' (head v{head}) — lore_comms action=brief_get",
        marker=f"you have not acked brief 'project' (head v2) {_EM_DASH} lore_comms action=brief_get",
        render_emit=lambda: _render_heartbeat(project_head=2, project_acked=None, subscribed=[]),
        render_no_emit=lambda: _render_heartbeat(project_head=2, project_acked=1, subscribed=[]),
    ),
    PromiseProof(
        literal="brief '{name}' v{head} is head — you acked v{acked}; "
        "catch up: lore_comms action=brief_get name='{name}'",
        marker=f"brief 'wave9' v3 is head {_EM_DASH} you acked v1; "
        "catch up: lore_comms action=brief_get name='wave9'",
        render_emit=lambda: _render_heartbeat(
            project_head=None, project_acked=None, subscribed=[("wave9", 3, 1)]
        ),
        render_no_emit=lambda: _render_heartbeat(
            project_head=None, project_acked=None, subscribed=[]
        ),
    ),
    PromiseProof(
        literal="behind on {k} more briefs: {names} (+{extra} more) — brief_get each by name",
        marker=_P7A_MARKER,
        render_emit=lambda: _render_heartbeat(
            project_head=None, project_acked=None, subscribed=_skew_fixture(_P7A_LEN)
        ),
        render_no_emit=lambda: _render_heartbeat(
            project_head=None, project_acked=None, subscribed=[]
        ),
    ),
    PromiseProof(
        literal="behind on {k} more briefs: {names} — brief_get each by name",
        marker=f"behind on {_P7B_REMAINDER} more briefs:",
        render_emit=lambda: _render_heartbeat(
            project_head=None, project_acked=None, subscribed=_skew_fixture(_P7B_LEN)
        ),
        render_no_emit=lambda: _render_heartbeat(
            project_head=None, project_acked=None, subscribed=[]
        ),
    ),
    # --- brief_publish first-version tail (§9.7 #8/#9): typed applicability. ---
    PromiseProof(
        literal="brief '{name}' v{version} published by {publisher} — first version; "
        "agents ack at register",
        marker="first version; agents ack at register",
        render_emit=lambda: _render_publish(
            name="wave9", version=1, first_version=True, session=None, behind=[], auto_ack=True
        ),
        render_no_emit=lambda: _render_publish(
            name="wave9", version=1, first_version=True, session=None, behind=[], auto_ack=False
        ),
    ),
    PromiseProof(
        literal="brief '{name}' v{version} published by {publisher} — first version; "
        "agents ack with lore_comms action=brief_ack",
        marker="first version; agents ack with lore_comms action=brief_ack",
        render_emit=lambda: _render_publish(
            name="wave9", version=1, first_version=True, session=None, behind=[], auto_ack=False
        ),
        render_no_emit=lambda: _render_publish(
            name="wave9", version=1, first_version=True, session=None, behind=[], auto_ack=True
        ),
    ),
    # --- brief_publish skew tails (§9.7 #10): four name-conditioned variants. --
    PromiseProof(
        literal="skew (session {session}): {behind} non-retired agents behind head v{head} — "
        "{breakdown}; surfaces at their next heartbeat",
        marker="skew (session wave7): 2 non-retired agents behind head v2",
        render_emit=lambda: _render_publish(
            name="wave9",
            version=2,
            first_version=False,
            session="wave7",
            behind=[_behind("a", 1), _behind("b", 1)],
            auto_ack=True,
        ),
        render_no_emit=lambda: _render_publish(
            name="wave9", version=2, first_version=False, session="wave7", behind=[], auto_ack=True
        ),
    ),
    PromiseProof(
        literal="skew: {behind} non-retired agents behind head v{head} — "
        "{breakdown}; surfaces at their next heartbeat",
        marker="skew: 2 non-retired agents behind head v2",
        render_emit=lambda: _render_publish(
            name="wave9",
            version=2,
            first_version=False,
            session=None,
            behind=[_behind("a", 1), _behind("b", 1)],
            auto_ack=True,
        ),
        render_no_emit=lambda: _render_publish(
            name="wave9", version=2, first_version=False, session=None, behind=[], auto_ack=True
        ),
    ),
    PromiseProof(
        literal="skew (session {session}): {behind} non-retired agents behind head v{head} — "
        "{breakdown}; ackers see it at next heartbeat — unbriefed agents only via "
        "brief_get name='{name}'",
        marker=f"ackers see it at next heartbeat {_EM_DASH} unbriefed agents only via "
        "brief_get name='wave9'",
        render_emit=lambda: _render_publish(
            name="wave9",
            version=2,
            first_version=False,
            session="wave7",
            behind=[_behind("a", 1), _behind("c", None)],
            auto_ack=False,
        ),
        # auto_ack True flips the SAME skew to tail 1 (surfaces universally) —
        # so the marker's absence proves the standing predicate gates tail 3.
        render_no_emit=lambda: _render_publish(
            name="wave9",
            version=2,
            first_version=False,
            session="wave7",
            behind=[_behind("a", 1), _behind("c", None)],
            auto_ack=True,
        ),
    ),
    PromiseProof(
        literal="skew: {behind} non-retired agents behind head v{head} — "
        "{breakdown}; ackers see it at next heartbeat — unbriefed agents only via "
        "brief_get name='{name}'",
        marker=f"{_EM_DASH} unbriefed agents only via brief_get name='wave9'",
        render_emit=lambda: _render_publish(
            name="wave9",
            version=2,
            first_version=False,
            session=None,
            behind=[_behind("a", 1), _behind("c", None)],
            auto_ack=False,
        ),
        render_no_emit=lambda: _render_publish(
            name="wave9",
            version=2,
            first_version=False,
            session=None,
            behind=[_behind("a", 1), _behind("c", None)],
            auto_ack=True,
        ),
    ),
    # --- brief_ack behind teach (§9.7 #11): version < head vs at head. --------
    PromiseProof(
        literal="acked brief '{name}' v{version} — head is v{head}; "
        "catch up: lore_comms action=brief_get name='{name}'",
        marker=f"acked brief 'wave9' v1 {_EM_DASH} head is v2; "
        "catch up: lore_comms action=brief_get name='wave9'",
        render_emit=lambda: _render_ack(name="wave9", version=1, head=2),
        render_no_emit=lambda: _render_ack(name="wave9", version=2, head=2),
    ),
    # --- fleet elision re-ask (§9.7 #12): remainder present vs none. ----------
    PromiseProof(
        literal="+{more} more — re-run with limit={next_limit}",
        marker=f"{_EM_DASH} re-run with limit=5",
        render_emit=lambda: _render_fleet(
            rows=[_agent("a"), _agent("b")], total_active=5, limit=2
        ),
        render_no_emit=lambda: _render_fleet(
            rows=[_agent("a"), _agent("b")], total_active=2, limit=2
        ),
    ),
]

_PROMISE_PROOFS: dict[str, PromiseProof] = {proof.literal: proof for proof in _PROOF_LIST}


class TestEveryRegisteredPromisePredicateGatesEmission:
    """ITEM 1: every registered promise's predicate GATES its emission at the
    REAL render — the executable mechanization of §9.7's sweep."""

    @pytest.mark.parametrize("literal", sorted(_PROMISE_PROOFS))
    def test_predicate_gates_emission(self, literal: str) -> None:
        _assert_predicate_gates(_PROMISE_PROOFS[literal])

    def test_registered_iff_proven(self) -> None:
        """The load-bearing COMPLETENESS link (repo law: coverage is a CHECKED
        variable): a registered promise with no executable proof, OR a proof for
        a literal no longer registered, goes RED here."""
        registered = frozenset(_PROMISE_REGISTRY)
        proven = frozenset(_PROMISE_PROOFS)
        assert proven == registered, (
            "registered ⟺ proven is broken — every _PROMISE_REGISTRY literal needs an "
            "executable emit/no-emit proof and vice-versa (§9.7 mechanization):\n"
            f"  registered but UNPROVEN: {sorted(registered - proven)!r}\n"
            f"  proven but UNREGISTERED: {sorted(proven - registered)!r}"
        )

    def test_no_duplicate_proof_literals(self) -> None:
        """A duplicate ``.literal`` would silently collapse in the dict and make
        the count lie — so the list and the map must agree."""
        assert len(_PROMISE_PROOFS) == len(_PROOF_LIST), (
            f"duplicate proof literal(s): {len(_PROOF_LIST)} proofs, "
            f"{len(_PROMISE_PROOFS)} distinct literals"
        )


class TestItem1ProofHarnessDiscriminates:
    """SELF-ATTACK on the proof harness itself (a probe needs a control): prove
    ``_assert_predicate_gates`` REJECTS a predicate-ignoring render AND a
    never-emitting one, and ACCEPTS a correct synthetic proof."""

    def test_a_predicate_ignoring_render_is_caught(self) -> None:
        marker = "PROMISE-MARKER"
        leaky = PromiseProof(
            literal="synthetic",
            marker=marker,
            render_emit=lambda: f"line with {marker} here",
            # LEAKS the marker regardless of the predicate — a render that emits
            # the promise unconditionally. The NO-EMIT leg must catch it.
            render_no_emit=lambda: f"line with {marker} STILL here",
        )
        with pytest.raises(AssertionError, match="NO-EMIT leg"):
            _assert_predicate_gates(leaky)

    def test_a_never_emitting_render_is_caught(self) -> None:
        marker = "PROMISE-MARKER"
        dead = PromiseProof(
            literal="synthetic",
            marker=marker,
            render_emit=lambda: "nothing to see",
            render_no_emit=lambda: "nothing to see",
        )
        with pytest.raises(AssertionError, match="EMIT leg"):
            _assert_predicate_gates(dead)

    def test_positive_control_a_correct_synthetic_proof_passes(self) -> None:
        marker = "PROMISE-MARKER"
        good = PromiseProof(
            literal="synthetic",
            marker=marker,
            render_emit=lambda: f"line with {marker} here",
            render_no_emit=lambda: "line without it",
        )
        _assert_predicate_gates(good)  # must NOT raise


# =========================================================================== #
# PACKET 02a — ITEM 2: the safe_str / sanitise_line / concatenation literal
# coverage closure (the residual _SAFE_STR_LITERAL_RESIDUAL documented).
#
# The CORE scanner (`_comms_render_literals`) only reaches render_line/render_join
# TEMPLATE args. A promise could be smuggled through the LITERAL TEXT of a
# ``safe_str(f"...")`` / ``sanitise_line(...)`` argument (or a "..." + expr
# concatenation, or a local variable feeding one) and escape classification.
# This scanner canonicalises every such literal and requires each be CLASSIFIED
# (default-FAIL), exactly like the CORE.
#
# CANONICAL FORM: every dynamic sub-expression (a ``{expr}`` in an f-string, a
# non-literal concatenation operand, an unresolvable name) collapses to the
# STABLE placeholder ``"{}"`` — chosen over the unparsed expression because it is
# IMMUNE to variable renames and expression edits (``f"project v{n}"`` and
# ``f"project v{head_version}"`` share one canonical "project v{}"), so the
# classified set churns only when the LITERAL TEXT changes, never when a variable
# is renamed. A ``{name}``-bearing FORMATTED value whose inner expression
# resolves (within the same function, cycle-guarded) to a string literal is
# expanded to that literal, so a promise hidden one hop behind a local variable
# (the ``suffix`` pattern in ``_render_comms_behind_entry``) is still reached.
# A template with NO literal text (only placeholders/whitespace) carries no
# promise and is skipped — there is nothing to classify.
# =========================================================================== #

_SAFE_STR_VERB_NAMES: frozenset[str] = frozenset({"safe_str", "sanitise_line"})
_PLACEHOLDER = "{}"


def _resolve_name_literals(
    name_id: str,
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    seen: frozenset[str],
) -> list[str]:
    """String-literal templates a NAME can hold, from same-function assignments
    (``Assign``/``AnnAssign``). Cycle-guarded via ``seen``. Only assignments that
    FLOW INTO a scanned sink are ever resolved (this is called only from within
    ``_string_templates`` reached from a safe_str/sanitise_line arg), so an
    unrelated non-rendered assignment is never swept in."""
    results: list[str] = []
    for stmt in ast.walk(func):
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == name_id:
                    results.extend(_string_templates(stmt.value, func, seen))
        elif (
            isinstance(stmt, ast.AnnAssign)
            and isinstance(stmt.target, ast.Name)
            and stmt.target.id == name_id
            and stmt.value is not None
        ):
            results.extend(_string_templates(stmt.value, func, seen))
    return results


def _string_templates(
    node: ast.expr,
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    seen: frozenset[str],
) -> list[str]:
    """Canonical string template(s) an expression can produce, with every dynamic
    sub-expression rendered as ``_PLACEHOLDER``. Returns a LIST because an
    ``IfExp`` (two branches) or a reassigned name can yield more than one. One
    exit point (an if/elif/else assigning ``result``) keeps the branch dispatch
    below ruff's return-count ceiling."""
    result: list[str]
    if isinstance(node, ast.Constant):
        result = [node.value] if isinstance(node.value, str) else [_PLACEHOLDER]
    elif isinstance(node, ast.JoinedStr):
        result = [""]
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                pieces = [value.value]
            elif isinstance(value, ast.FormattedValue):
                pieces = _string_templates(value.value, func, seen)
            else:
                pieces = [_PLACEHOLDER]
            result = [prefix + piece for prefix in result for piece in pieces]
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        result = [
            lhs + rhs
            for lhs in _string_templates(node.left, func, seen)
            for rhs in _string_templates(node.right, func, seen)
        ]
    elif isinstance(node, ast.IfExp):
        result = _string_templates(node.body, func, seen) + _string_templates(node.orelse, func, seen)
    elif isinstance(node, ast.Name):
        resolved = (
            [] if node.id in seen else _resolve_name_literals(node.id, func, seen | {node.id})
        )
        result = resolved or [_PLACEHOLDER]
    elif isinstance(node, ast.Call) and _called_name(node.func) in _SAFE_STR_VERB_NAMES and node.args:
        result = _string_templates(node.args[0], func, seen)
    else:
        result = [_PLACEHOLDER]
    return result


def _has_literal_text(template: str) -> bool:
    """A template carries classifiable text only if SOMETHING survives once the
    placeholders are removed and whitespace is stripped — a pure-dynamic wrap
    (``sanitise_line(x)`` -> "{}") or a whitespace-only join promises nothing."""
    return template.replace(_PLACEHOLDER, "").strip() != ""


def _scan_safe_str_over_tree(tree: ast.AST) -> list[tuple[str, int, str]]:
    """Every classifiable safe_str/sanitise_line literal (function, lineno,
    canonical) inside a comms render/handler function of the given tree."""
    literals: list[tuple[str, int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if not (node.name.startswith("_render_comms") or node.name.startswith("_comms_")):
            continue
        for sub in ast.walk(node):
            if not (
                isinstance(sub, ast.Call)
                and _called_name(sub.func) in _SAFE_STR_VERB_NAMES
                and sub.args
            ):
                continue
            for template in _string_templates(sub.args[0], node, frozenset()):
                if _has_literal_text(template):
                    literals.append((node.name, sub.lineno, template))
    return literals


def _comms_render_safe_str_literals() -> list[tuple[str, int, str]]:
    tree = ast.parse(_SERVER_PY.read_text(encoding="utf-8"), filename="server.py")
    return _scan_safe_str_over_tree(tree)


def _scan_safe_str_source(source: str) -> list[str]:
    """The item-2 scanner applied to arbitrary source (the self-attack surface,
    mirroring the CORE's ``_scan_source``)."""
    return [text for _fn, _line, text in _scan_safe_str_over_tree(ast.parse(source))]


# --------------------------------------------------------------------------- #
# The PROMISE-FREE safe_str/sanitise_line literals — labels/status only. Each
# carries a reason; being here is a POSITIVE "this promises nothing" declaration,
# default still FAIL. A canonical carrying a REAL promise/imperative is a
# STOP-AND-SURFACE (a production render change -> packet 02 scope), never a
# silent addition here (packet 02a §2).
# --------------------------------------------------------------------------- #
_SAFE_STR_PROMISE_FREE: dict[str, str] = {
    "{} (unbriefed)": "behind-entry acked-version label (unbriefed agent)",
    "{} (v{})": "behind-entry acked-version label (acked version)",
    "{} at v{}": "skew-breakdown named version-group count label",
    "{} at older versions": "skew-breakdown collapsed-older-versions count label",
    "{} unbriefed": "skew-breakdown never-acked group count label",
    "project unbriefed": "fleet project-cell label (agent unbriefed on the standing brief)",
    "project v{}": "fleet project-cell label (agent at head)",
    "project v{} (head v{})": "fleet project-cell label (agent behind head)",
    "role": "fleet-row cell label",
    "model": "fleet-row cell label",
    "task": "fleet-row cell label",
    "note:": "fleet-row note cell label",
    "{}…": "fleet-row truncated task-id ellipsis (display marker, no mechanism)",
}


def _safe_str_classified() -> frozenset[str]:
    return frozenset(_SAFE_STR_PROMISE_FREE)


class TestEveryCommsSafeStrLiteralIsClassified:
    """ITEM 2 default-FAIL: every safe_str/sanitise_line literal in a comms
    render func must be declared promise-free (or, if a REAL promise, STOPPED and
    surfaced — never silently classified)."""

    def test_every_comms_safe_str_literal_is_classified(self) -> None:
        classified = _safe_str_classified()
        unclassified = [
            (fn, line, text)
            for fn, line, text in _comms_render_safe_str_literals()
            if text not in classified
        ]
        assert not unclassified, (
            "a safe_str/sanitise_line literal in a comms render func is UNCLASSIFIED. If it "
            "is a label/status, declare it in _SAFE_STR_PROMISE_FREE with a reason; if it "
            "carries a mechanism promise, STOP — that is a render-honesty defect for packet "
            "02, not a classification you add here (02a §2):\n"
            + "\n".join(f"  {fn}:{line}: {text!r}" for fn, line, text in unclassified)
        )

    def test_no_dead_safe_str_free_entries(self) -> None:
        """A promise-free entry that no comms render still emits is stale prose —
        remove it (mirrors the CORE's ``test_no_dead_registry_entries``)."""
        live = {text for _fn, _line, text in _comms_render_safe_str_literals()}
        dead = sorted(text for text in _SAFE_STR_PROMISE_FREE if text not in live)
        assert not dead, (
            "promise-free safe_str literal(s) no longer emitted by any comms render — remove "
            "the stale entry:\n" + "\n".join(f"  {text!r}" for text in dead)
        )

    def test_safe_str_free_is_disjoint_from_the_render_line_registry(self) -> None:
        """A canonical must not be BOTH a safe_str label and a render_line
        promise/free literal — the two scanners cover different surfaces and a
        collision would hide a reclassification."""
        overlap = frozenset(_SAFE_STR_PROMISE_FREE) & _classified()
        assert not overlap, f"a literal is classified by BOTH scanners: {sorted(overlap)!r}"


class TestTheSafeStrScanReachedEveryHelper:
    """Coverage is a CHECKED variable: prove the safe_str scan is not vacuously
    passing by scanning nothing (mirrors the CORE's reach check)."""

    def test_scan_reached_every_safe_str_emitting_comms_helper(self) -> None:
        observed = {fn for fn, _line, _text in _comms_render_safe_str_literals()}
        # Every comms helper that composes served text via safe_str/sanitise_line
        # literal content must contribute at least one scanned literal.
        expected = {
            "_render_comms_behind_entry",
            "_render_comms_skew_breakdown",
            "_render_comms_fleet_brief_cell",
            "_render_comms_fleet_row",
        }
        missing = expected - observed
        assert not missing, (
            "the safe_str scan did not observe a literal from every known safe_str-emitting "
            f"comms helper — it may be scanning nothing (coverage hole): {sorted(missing)!r}"
        )

    def test_non_vacuity_floor(self) -> None:
        # A blunt floor: 13 classifiable safe_str literals ship today; a sudden
        # drop to a handful means the scan narrowed, not the surface.
        count = len(_comms_render_safe_str_literals())
        assert count >= 10, count


class TestTheSafeStrGuardCatchesViolations:
    """SELF-ATTACK (a probe needs a control): the safe_str scanner catches a
    promise smuggled through an f-string literal, a local variable, AND a
    concatenation — with a POSITIVE control (a registered label passes) and a
    different-reason negative (a NON-comms function is ignored)."""

    def test_catches_a_promise_in_a_safe_str_fstring(self) -> None:
        hostile = (
            "def _render_comms_new(a):\n"
            "    return safe_str(f'do the thing: lore_comms action=teleport {a}')\n"
        )
        found = _scan_safe_str_source(hostile)
        unclassified = [text for text in found if text not in _safe_str_classified()]
        assert unclassified == ["do the thing: lore_comms action=teleport {}"], unclassified

    def test_catches_a_promise_smuggled_through_a_local_variable(self) -> None:
        """The var-indirection close: a promise assigned to a local and then
        interpolated (the ``suffix`` shape) is still reached and flagged."""
        hostile = (
            "def _render_comms_new(a):\n"
            "    msg = 'do the thing: teleport now'\n"
            "    return safe_str(f'{msg} {a}')\n"
        )
        found = _scan_safe_str_source(hostile)
        assert "do the thing: teleport now {}" in found, found
        assert "do the thing: teleport now {}" not in _safe_str_classified()

    def test_catches_a_promise_smuggled_through_concatenation(self) -> None:
        hostile = "def _render_comms_new(a):\n    return safe_str('act now: run it' + a)\n"
        found = _scan_safe_str_source(hostile)
        assert "act now: run it{}" in found, found
        assert "act now: run it{}" not in _safe_str_classified()

    def test_positive_control_a_registered_label_is_accepted(self) -> None:
        """A correctly-classified safe_str label, in a synthetic comms render
        func, is NOT flagged — so the red on the hostile cases is discrimination,
        not blanket rejection."""
        benign = "def _render_comms_ok(a):\n    return safe_str('project unbriefed')\n"
        found = _scan_safe_str_source(benign)
        unclassified = [text for text in found if text not in _safe_str_classified()]
        assert unclassified == [], unclassified

    def test_ignores_a_safe_str_outside_a_comms_function(self) -> None:
        """Different-reason negative: a safe_str in a NON-comms function is not
        the comms surface and must not be scanned."""
        outside = "def _render_finding_detail(a):\n    return safe_str('teleport now: do it')\n"
        assert _scan_safe_str_source(outside) == []


class TestSafeStrLiteralCoverageBound:
    """PIN THE MISS (repo law: an unpinned known limitation is indistinguishable
    from an unknown one). The safe_str scanner is AST-LOCAL: a promise assembled
    in a NON-comms helper and passed into a comms safe_str via a call is NOT
    reached. This is a KNOWN BOUND, not an oversight — the threat model is the
    HONEST DEVELOPER writing served text directly inside a render func, who is
    caught. RE-OPEN TRIGGER: if a comms render legitimately composes served text
    in a separate helper, that helper must itself carry the
    ``_render_comms``/``_comms_`` prefix (so it is scanned), or this bound is
    closed — in which case delete this pin and say so."""

    def test_KNOWN_BOUND_cross_function_flow_is_not_reached(self) -> None:
        source = (
            "def _promise_source():\n"
            "    return 'do the thing: teleport'\n"
            "def _render_comms_x():\n"
            "    return safe_str(_promise_source())\n"
        )
        found = _scan_safe_str_source(source)
        assert found == [], (
            "the safe_str scanner unexpectedly reached ACROSS a function boundary — if you "
            f"CLOSED this known bound deliberately, delete this pin and say so: {found!r}"
        )
