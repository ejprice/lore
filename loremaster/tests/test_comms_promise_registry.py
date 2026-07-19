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
import re
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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


def _scan_render_literals_over_tree(
    tree: ast.AST,
) -> tuple[list[tuple[str, int, str]], list[tuple[str, int, str]]]:
    """``(classifiable TEMPLATE literals, UNCLASSIFIABLE sites)`` for every
    ``render_line``/``render_join`` call inside a comms render/handler function of the
    given tree.

    TWO template shapes are scanned, and BOTH land in the ONE classified set:

    * a plain ``ast.Constant`` — passed through BYTE-IDENTICALLY, keeping its named
      ``{version}``-style placeholders, so every existing :data:`_PROMISE_REGISTRY` /
      :data:`_PROMISE_FREE` key matches exactly as before. (Implicit string
      concatenation is already joined by the parser into one ``ast.Constant``.)
    * an ``ast.JoinedStr`` (an f-string template) — canonicalised through item 2's
      :func:`_string_templates`, so its dynamic parts become the stable ``{}``
      placeholder. Before this, an f-string template was scanned by NEITHER scanner
      (this one required a ``Constant``; the safe_str scanner only reaches
      safe_str/sanitise_line args), so ``render_line(f"do the thing: ... {n}")``
      served a promise INVISIBLY — mypy does not enforce ``LiteralString``/PEP 675
      (see render.py's own enforcement story) and house style is "f-strings always",
      so an honest developer naturally writes the invisible form. Closing it is a
      REUSE of the existing canonicaliser, not a second policy.

    An f-string template with no literal text at all (only placeholders) carries no
    promise and is skipped — the same "nothing to classify" rule the safe_str scanner
    applies. A promise carried in a render VALUE rather than the template is a
    separate, pinned bound (see ``TestSafeStrLiteralCoverageBound``).
    """
    literals: list[tuple[str, int, str]] = []
    unclassifiable: list[tuple[str, int, str]] = []
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
                continue
            # Anything that is NOT a plain string template routes through the
            # deny-by-default canonicaliser (defined further down, in item 2's
            # section; the reference resolves at call time). A shape it cannot
            # canonicalise is REPORTED, never silently skipped — the retired
            # `elif JoinedStr` chain simply ignored every other shape.
            try:
                templates = _string_templates(template, node, frozenset())
            except _UnclassifiableShape as shape:
                unclassifiable.append((node.name, sub.lineno, shape.dump))
                continue
            for canonical in templates:
                if _has_literal_text(canonical):
                    literals.append((node.name, sub.lineno, canonical))
    return literals, unclassifiable


def _comms_render_literals() -> list[tuple[str, int, str]]:
    """The render-template scan over the SHIPPED server.py."""
    tree = ast.parse(_SERVER_PY.read_text(encoding="utf-8"), filename="server.py")
    return _scan_render_literals_over_tree(tree)[0]


def _scan_render_literals_source(source: str) -> list[str]:
    """The SAME render-template scanner applied to arbitrary source — the self-attack
    surface. Shares :func:`_scan_render_literals_over_tree` rather than re-walking, so
    the self-attacks exercise the REAL scanner and can never drift from it."""
    return [text for _fn, _line, text in _scan_render_literals_over_tree(ast.parse(source))[0]]


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
        """The guard's classifier applied to arbitrary source. Delegates to the REAL
        scanner (:func:`_scan_render_literals_source`) rather than re-walking the tree
        itself — a private copy of the walk would have kept passing these self-attacks
        after the production scanner changed (routing is not sharing, repo DRY law)."""
        return _scan_render_literals_source(source)

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

    # -- f-string TEMPLATE closure (fix-wave item 2) -------------------------------
    # Before this, ``render_line(f"...")`` was scanned by NEITHER scanner: this one
    # required an ``ast.Constant`` template, and the safe_str scanner only reaches
    # safe_str/sanitise_line arguments. A promise in an f-string template served
    # invisibly.

    def test_catches_a_promise_in_an_FSTRING_render_line_template(self) -> None:
        """(iv) the invisible form: a builder writes the template as an f-string (house
        style is "f-strings always"; mypy does not enforce LiteralString/PEP 675)."""
        hostile = (
            "def _render_comms_new(n):\n"
            "    return render_line(f'do the thing: lore_comms action=teleport {n}')\n"
        )
        literals = self._scan_source(hostile)
        unclassified = [text for text in literals if text not in _classified()]
        assert unclassified == ["do the thing: lore_comms action=teleport {}"], unclassified

    def test_positive_control_a_classified_fstring_template_is_accepted(self) -> None:
        """POSITIVE control for the f-string path: an f-string template whose canonical
        form IS classified is NOT flagged — so the red above is discrimination, not
        blanket rejection of every f-string template."""
        known = "no agents registered"
        assert known in _PROMISE_FREE  # sanity: a placeholder-free classified literal
        benign = f"def _render_comms_ok(n):\n    return render_line(f{known!r})\n"
        literals = self._scan_source(benign)
        assert literals == [known], literals
        assert [text for text in literals if text not in _classified()] == []

    def test_positive_control_a_CONSTANT_template_still_passes_through_byte_identically(
        self,
    ) -> None:
        """REGRESSION control for the extension: a plain (non-f-string) template must
        still be scanned BYTE-IDENTICALLY, named ``{placeholders}`` intact — otherwise
        every existing registry/promise-free key would stop matching."""
        known = "brief 'project' v{head} is head — you acked v{acked}; catch up: lore_comms action=brief_get"
        assert known in _PROMISE_REGISTRY
        benign = f"def _render_comms_ok(x):\n    return render_line({known!r})\n"
        assert self._scan_source(benign) == [known]

    def test_ignores_an_fstring_template_outside_a_comms_function(self) -> None:
        """Different-reason negative for the f-string path too."""
        outside = (
            "def _render_finding_detail(n):\n"
            "    return render_line(f'teleport now: do it {n}')\n"
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
        # FULL rendered line, not the shared "behind on {k} more briefs:" prefix: that
        # prefix is common to BOTH collapse variants, so a build that ALWAYS renders the
        # "(+{extra} more)" variant satisfied it and passed vacuously (fix-wave item 1).
        # ``n00`` is _skew_fixture's smallest skew — the sole remainder after the cap slice.
        marker=f"behind on {_P7B_REMAINDER} more briefs: n00 {_EM_DASH} brief_get each by name",
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
        # FULL rendered line (fix-wave item 3): the bare "skew (session wave7): 2
        # non-retired agents behind head v2" prefix is ALSO satisfied by the tail-3
        # scoped variant, so it could not distinguish tail 1 from tail 3.
        marker=f"skew (session wave7): 2 non-retired agents behind head v2 {_EM_DASH} "
        "2 at v1; surfaces at their next heartbeat",
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
        # FULL rendered line (fix-wave item 3) — same reason as the scoped tail 1.
        marker=f"skew: 2 non-retired agents behind head v2 {_EM_DASH} "
        "2 at v1; surfaces at their next heartbeat",
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
        # FULL rendered line (fix-wave item 3): the bare tail-3 clause is byte-identical
        # in the SCOPED and UNSCOPED variants, so it could not distinguish them. The
        # "skew (session wave7):" head is what makes this proof scoped-specific.
        marker=f"skew (session wave7): 2 non-retired agents behind head v2 {_EM_DASH} "
        f"1 at v1, 1 unbriefed; ackers see it at next heartbeat {_EM_DASH} "
        "unbriefed agents only via brief_get name='wave9'",
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
        # FULL rendered line (fix-wave item 3, extended to this fourth tail — same class
        # as the three named: the bare clause cannot distinguish unscoped from scoped).
        marker=f"skew: 2 non-retired agents behind head v2 {_EM_DASH} "
        f"1 at v1, 1 unbriefed; ackers see it at next heartbeat {_EM_DASH} "
        "unbriefed agents only via brief_get name='wave9'",
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

# A product guard: a pathological nest of IfExp/join branches could blow up the
# canonical count. Past this, the shape is UNCLASSIFIABLE rather than silently
# truncated (truncation would be allow-by-default wearing a cap).
_MAX_CANONICALS = 64

# printf-style conversion specifiers, and str.format replacement fields — both
# normalised to _PLACEHOLDER so a %-built or .format-built string canonicalises
# into the SAME shape an f-string would produce.
_PRINTF_SPEC = re.compile(r"%(?:\([^)]*\))?[-+ #0]*[\d*]*(?:\.[\d*]+)?[hlL]?[diouxXeEfFgGcrsa%]")
_FORMAT_FIELD = re.compile(r"\{[^{}]*\}")


class _UnclassifiableShape(Exception):
    """DENY-BY-DEFAULT: a string-producing AST shape the canonicaliser does not know
    how to turn into a stable template.

    THE LAW THIS ENFORCES (repo instrument-lesson, "the forbidden set is unbounded;
    allowlist the SAFE"): an unknown shape must FAIL LOUD, never silently become a
    placeholder. The retired canonicaliser ended in ``else: [_PLACEHOLDER]``, so an
    unrecognised shape vanished into "{}" and was then discarded as textless — three
    live holes shipped behind that one line (``%``-format, ``.format``, ``str.join``
    all served promises INVISIBLY). Unknown shape = RED, naming file:line + the
    ``ast.dump``, so the next author either teaches the canonicaliser the shape or
    declares it opaque WITH evidence."""

    def __init__(self, node: ast.AST) -> None:
        self.dump = ast.dump(node)
        super().__init__(self.dump)


@dataclass(frozen=True)
class _Canon:
    """A canonicalisation outcome.

    ``templates`` are the canonical strings this expression can produce (more than
    one when an ``IfExp`` branches). ``is_string`` records whether the node is a
    STRING-BUILDING shape (a literal, an f-string, a concatenation of them...) as
    opposed to an OPAQUE RUNTIME VALUE. That distinction is the whole design: a
    string-building shape MUST canonicalise or fail; an opaque value legitimately
    carries no literal text at this site and renders as a single placeholder, so
    honest code (``sanitise_line(agent.name)``, ``row.task_id[:8] + "…"``) never
    goes red. Getting the opaque set wrong floods honest code with false positives —
    and "a gate that refuses honest code is a gate that gets SWITCHED OFF"."""

    templates: tuple[str, ...]
    is_string: bool


# Every OPAQUE exemption below is EVIDENCE-BACKED in its branch comment (why the
# shape cannot carry literal TEXT at this site), never "it looks fine".
_OPAQUE = _Canon((_PLACEHOLDER,), is_string=False)


def _printf_to_placeholders(template: str) -> str:
    """``"v%s of %d"`` -> ``"v{} of {}"``; a literal ``%%`` collapses to ``%``."""
    return _PRINTF_SPEC.sub(lambda m: "%" if m.group(0) == "%%" else _PLACEHOLDER, template)


def _format_fields_to_placeholders(template: str) -> str:
    """``"v{0} of {n}"`` -> ``"v{} of {}"``; ``{{``/``}}`` unescape to ``{``/``}``."""
    return _FORMAT_FIELD.sub(_PLACEHOLDER, template).replace("{{", "{").replace("}}", "}")


def _resolve_name_canons(
    name_id: str,
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    seen: frozenset[str],
) -> list[_Canon]:
    """Canonicalisations a NAME can hold, from same-function ``Assign``/``AnnAssign``
    bindings. Cycle-guarded via ``seen``. Reached ONLY from a scanned sink, so an
    unrelated non-rendered assignment is never swept in. A binding that is itself
    unclassifiable PROPAGATES the denial — a name is not an escape hatch."""
    results: list[_Canon] = []
    for stmt in ast.walk(func):
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == name_id:
                    results.append(_canonicalise(stmt.value, func, seen))
        elif (
            isinstance(stmt, ast.AnnAssign)
            and isinstance(stmt.target, ast.Name)
            and stmt.target.id == name_id
            and stmt.value is not None
        ):
            results.append(_canonicalise(stmt.value, func, seen))
    return results


def _param_default_canons(
    name_id: str,
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    seen: frozenset[str],
) -> list[_Canon]:
    """Canonicalisations a name can hold from THIS function's own PARAMETER DEFAULTS.

    EXECUTED, not assumed: ``def f(label="PROMISE"): return label`` returns ``'PROMISE'``.
    The retired evidence on the ``Name`` branch — *"a parameter/free name binds no literal
    HERE"* — was FALSE for exactly this case, and the text is LOCAL to the function, so it
    is emphatically NOT the pinned cross-function bound. ``_resolve_name_canons`` walks
    only ``Assign``/``AnnAssign``, so a defaulted parameter served its literal invisibly."""
    results: list[_Canon] = []
    arguments = func.args
    positional = [*arguments.posonlyargs, *arguments.args]
    # ``defaults`` aligns to the TAIL of positional parameters, never the head.
    offset = len(positional) - len(arguments.defaults)
    for index, default in enumerate(arguments.defaults):
        if positional[offset + index].arg == name_id:
            results.append(_canonicalise(default, func, seen))
    for keyword_arg, keyword_default in zip(
        arguments.kwonlyargs, arguments.kw_defaults, strict=True
    ):
        if keyword_default is not None and keyword_arg.arg == name_id:
            results.append(_canonicalise(keyword_default, func, seen))
    return results


def _canonicalise_join_parts(
    arg: ast.expr, func: ast.FunctionDef | ast.AsyncFunctionDef, seen: frozenset[str]
) -> list[tuple[str, ...]]:
    """The element-template combinations of a ``str.join`` argument. Only an
    ENUMERABLE literal sequence (or a name bound to one) can be canonicalised; a
    runtime iterable is UNCLASSIFIABLE, never silently dropped."""
    if isinstance(arg, ast.Name) and arg.id not in seen:
        for stmt in ast.walk(func):
            if isinstance(stmt, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == arg.id for t in stmt.targets
            ):
                return _canonicalise_join_parts(stmt.value, func, seen | {arg.id})
    if not isinstance(arg, ast.List | ast.Tuple):
        raise _UnclassifiableShape(arg)
    combos: list[tuple[str, ...]] = [()]
    for element in arg.elts:
        element_canon = _canonicalise(element, func, seen)
        combos = [combo + (text,) for combo in combos for text in element_canon.templates]
        if len(combos) > _MAX_CANONICALS:
            raise _UnclassifiableShape(arg)
    return combos


# TRANSPARENT-IN-POSITION calls: the named argument POSITIONS can be returned VERBATIM,
# so literal text there reaches the output — the same transparency ``BoolOp``/``IfExp``
# have in their operands, applied to argument positions. Deliberately NOT a blunt
# "recurse into every call argument" rule: that was MEASURED at 6 false positives on the
# shipped surface (it surfaces dict-lookup KEYS and similar non-output literals), and a
# gate that refuses honest code is a gate that gets switched off. This precise set
# measures ZERO (see TestCallArgumentTransparency).
_TRANSPARENT_ARG_POSITIONS: dict[str, tuple[int, ...]] = {
    "get": (1,),  # d.get(key, DEFAULT) -> DEFAULT returned verbatim on a miss
    "getattr": (2,),  # getattr(obj, name, DEFAULT)
    "next": (1,),  # next(iterator, DEFAULT)
    "str": (0,),  # str(VALUE) -> a literal argument passes straight through
}

# The KEYWORD spelling of the same transparency. EXECUTED, not assumed: `str(object="X")`
# ACCEPTS the keyword and returns 'X', while `dict.get`/`getattr`/`next` all raise
# "takes no keyword arguments" — so `str` is the ONLY one reachable this way. That is a
# measurement, not a guess; re-measure before adding an entry here.
_TRANSPARENT_ARG_KEYWORDS: dict[str, tuple[str, ...]] = {"str": ("object",)}


def _substitute_placeholders(templates: tuple[str, ...], arg_canons: list[_Canon]) -> tuple[str, ...]:
    """Fill a canonical's ``{}`` slots, left to right, with the canonicals of the
    arguments that supply them — so ``"{}".format("PROMISE")`` canonicalises to
    ``"PROMISE"`` rather than hiding the argument's literal text behind a placeholder.
    Slots with no corresponding argument stay ``{}``."""
    results: list[str] = []
    for template in templates:
        segments = template.split(_PLACEHOLDER)
        combos = [segments[0]]
        for index in range(1, len(segments)):
            canon = arg_canons[index - 1] if index - 1 < len(arg_canons) else None
            fills = canon.templates if canon is not None else (_PLACEHOLDER,)
            combos = [combo + fill + segments[index] for combo in combos for fill in fills]
            if len(combos) > _MAX_CANONICALS:
                raise _UnclassifiableShape(ast.Constant(value=template))
        results.extend(combos)
    return tuple(results)


def _canonicalise_transparent_positions(
    node: ast.Call,
    called: str,
    positions: tuple[int, ...],
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    seen: frozenset[str],
) -> _Canon:
    """A transparent-in-position call can return EITHER the looked-up/converted value
    (opaque) OR the literal at a transparent position — so both are canonical
    alternatives, exactly like the two branches of an ``IfExp``.

    BOTH spellings are read: the positional argument AND the keyword one. Reading only
    ``node.args`` let ``str(object="PROMISE")`` through invisibly."""
    templates: list[str] = [_PLACEHOLDER]
    is_string = False
    for index in positions:
        if index < len(node.args):
            canon = _canonicalise(node.args[index], func, seen)
            templates.extend(canon.templates)
            is_string = is_string or canon.is_string
    keyword_names = _TRANSPARENT_ARG_KEYWORDS.get(called, ())
    for keyword in node.keywords:
        if keyword.arg is not None and keyword.arg in keyword_names:
            canon = _canonicalise(keyword.value, func, seen)
            templates.extend(canon.templates)
            is_string = is_string or canon.is_string
    return _Canon(tuple(templates), is_string)


def _canonicalise_call(
    node: ast.Call, func: ast.FunctionDef | ast.AsyncFunctionDef, seen: frozenset[str]
) -> _Canon:
    """Calls split four ways: the render seam's own string wrappers, a string METHOD on a
    text-bearing receiver (must canonicalise or FAIL), a TRANSPARENT-IN-POSITION call
    (recurse into the position it can return verbatim), and everything else (opaque)."""
    called = _called_name(node.func)
    if isinstance(node.func, ast.Lambda):
        # An IMMEDIATELY-INVOKED lambda is transparent in its body (auditor's R3). Cheap
        # to close and it measures zero false positives, so it is closed rather than
        # pinned: production's only lambdas are ``sorted(key=...)``, never invoked here.
        return _canonicalise(node.func.body, func, seen)
    if called in _SAFE_STR_VERB_NAMES:
        if not node.args:
            return _OPAQUE
        return _Canon(_canonicalise(node.args[0], func, seen).templates, is_string=True)
    if isinstance(node.func, ast.Attribute):
        receiver = _canonicalise(node.func.value, func, seen)
        if receiver.is_string:
            return _canonicalise_string_method(node, receiver, func, seen)
        # EVIDENCE: an ordinary method on a runtime object (``AppContext._render_age(x)``,
        # ``entry.acked_version.bit_length()``) contributes no literal text HERE. Text it
        # returns from another function is the PINNED cross-function bound, not this gate.
        # A method that is transparent in a POSITION (``d.get(k, DEFAULT)``) still recurses.
    if called in _TRANSPARENT_ARG_POSITIONS:
        return _canonicalise_transparent_positions(
            node, called, _TRANSPARENT_ARG_POSITIONS[called], func, seen
        )
    # EVIDENCE: a plain function call returns a runtime value; literal text built in
    # ANOTHER function is the pinned cross-function bound (TestSafeStrLiteralCoverageBound).
    return _OPAQUE


def _canonicalise_string_method(
    node: ast.Call,
    receiver: _Canon,
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    seen: frozenset[str],
) -> _Canon:
    """A method on a text-bearing receiver: ``.format``/``.join`` canonicalise (both
    INCORPORATE their arguments' literal text), everything else denies."""
    attribute = node.func.attr if isinstance(node.func, ast.Attribute) else ""
    if attribute == "format":
        # A keyword/starred argument carrying literal text cannot be placed faithfully
        # (the field names were already normalised away) -> deny rather than guess.
        for keyword in node.keywords:
            if _canonicalise(keyword.value, func, seen).is_string:
                raise _UnclassifiableShape(node)
        base = tuple(_format_fields_to_placeholders(t) for t in receiver.templates)
        arg_canons = [_canonicalise(argument, func, seen) for argument in node.args]
        return _Canon(_substitute_placeholders(base, arg_canons), True)
    if attribute == "join":
        if len(node.args) != 1:
            raise _UnclassifiableShape(node)
        combos = _canonicalise_join_parts(node.args[0], func, seen)
        joined = tuple(sep.join(combo) for sep in receiver.templates for combo in combos)
        if len(joined) > _MAX_CANONICALS:
            raise _UnclassifiableShape(node)
        return _Canon(joined, True)
    # A string method we cannot canonicalise (.replace/.upper/.strip/...) is a
    # TEXT TRANSFORM on literal text -> deny, never guess.
    raise _UnclassifiableShape(node)


def _canonicalise(  # noqa: PLR0911, PLR0912
    node: ast.expr,
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    seen: frozenset[str],
) -> _Canon:
    """Canonicalise a string-producing expression, or raise :class:`_UnclassifiableShape`.

    The dispatch is an explicit ALLOWLIST in two halves — (a) text-building shapes,
    canonicalised; (b) opaque runtime values, each exempted WITH the evidence that it
    cannot carry literal text at this site — and it ends in ``raise``, so any shape
    outside both halves fails loud."""
    # --- (a) TEXT-BUILDING shapes -------------------------------------------------
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return _Canon((node.value,), is_string=True)
        if node.value is None or isinstance(node.value, int | float | complex):
            return _OPAQUE  # EVIDENCE: a numeric/None literal cannot carry prose.
        raise _UnclassifiableShape(node)  # bytes, Ellipsis: could decode to text.
    if isinstance(node, ast.JoinedStr):
        accumulated = [""]
        for value in node.values:
            piece = _canonicalise(value, func, seen)
            accumulated = [prefix + text for prefix in accumulated for text in piece.templates]
            if len(accumulated) > _MAX_CANONICALS:
                raise _UnclassifiableShape(node)
        return _Canon(tuple(accumulated), is_string=True)
    if isinstance(node, ast.FormattedValue):
        inner = _canonicalise(node.value, func, seen)
        return _Canon(inner.templates, inner.is_string)
    if isinstance(node, ast.BinOp):
        return _canonicalise_binop(node, func, seen)
    if isinstance(node, ast.IfExp):
        body = _canonicalise(node.body, func, seen)
        orelse = _canonicalise(node.orelse, func, seen)
        return _Canon(body.templates + orelse.templates, body.is_string or orelse.is_string)
    if isinstance(node, ast.BoolOp):
        # `or`/`and` return an OPERAND, not a bool (`"" or "prose"` -> 'prose'), so this is
        # TRANSPARENT in exactly the way ``IfExp`` above is. The honest shape this catches:
        # ``safe_str(row.last_note or "no note — run lore_comms action=... to add one")``.
        operands = [_canonicalise(value, func, seen) for value in node.values]
        return _Canon(
            tuple(text for canon in operands for text in canon.templates),
            any(canon.is_string for canon in operands),
        )
    if isinstance(node, ast.Call):
        return _canonicalise_call(node, func, seen)
    if isinstance(node, ast.Name):
        if node.id in seen:
            return _OPAQUE  # EVIDENCE: cycle guard; the binding is already in flight.
        resolved = _resolve_name_canons(node.id, func, seen | {node.id}) + _param_default_canons(
            node.id, func, seen | {node.id}
        )
        if not resolved:
            # EVIDENCE (corrected): a name with no local binding AND no parameter DEFAULT
            # binds no literal here. The retired wording said "a parameter/free name binds
            # no literal HERE", which was FALSE for a defaulted parameter — its literal is
            # bound in this function's OWN signature (see _param_default_canons).
            return _OPAQUE
        return _Canon(
            tuple(text for canon in resolved for text in canon.templates),
            any(canon.is_string for canon in resolved),
        )
    # --- (b) OPAQUE RUNTIME VALUES (each exemption evidence-backed) ---------------
    if isinstance(node, ast.Attribute):
        return _OPAQUE  # EVIDENCE: attribute access reads a runtime value, not a literal.
    if isinstance(node, ast.Subscript):
        base = _canonicalise(node.value, func, seen)
        if base.is_string:
            # Indexing/slicing a LITERAL is a text transform we will not guess.
            raise _UnclassifiableShape(node)
        return _OPAQUE  # EVIDENCE: subscripting a runtime container yields a value.
    if isinstance(node, ast.List | ast.Tuple | ast.Set):
        # EVERY element, INCLUDING a ``*unpacked`` one: skipping Starred was a real
        # hole in this design's first attempt (self-attack #26) — ``[*["do it: ..."]]``
        # walked straight past the container check.
        if any(_canonicalise(element, func, seen).is_string for element in node.elts):
            # A container of LITERAL TEXT reaching a string sink renders its repr —
            # promise text would survive into the output. Deny; do not guess a repr.
            raise _UnclassifiableShape(node)
        return _OPAQUE  # EVIDENCE: a container of runtime values carries no literal text.
    if isinstance(node, ast.Dict):
        # ``keys`` carries a None entry for each ``**unpacking``; its dict rides in values.
        if any(
            item is not None and _canonicalise(item, func, seen).is_string
            for item in [*node.keys, *node.values]
        ):
            raise _UnclassifiableShape(node)
        return _OPAQUE  # EVIDENCE: as above, for mappings.
    if isinstance(node, ast.ListComp | ast.SetComp | ast.GeneratorExp):
        # The ELEMENT *and* every ITERABLE: checking only ``elt`` was the one attack
        # of my own 25 that defeated the first attempt (self-attack #20) —
        # ``[x for x in ["do it: teleport"]]`` has an opaque element and a
        # literal-bearing iterable, so the text survived invisibly.
        if any(
            _canonicalise(part, func, seen).is_string
            for part in [node.elt, *(generator.iter for generator in node.generators)]
        ):
            raise _UnclassifiableShape(node)
        return _OPAQUE  # EVIDENCE: a comprehension over runtime values.
    if isinstance(node, ast.DictComp):
        if any(
            _canonicalise(part, func, seen).is_string
            for part in [
                node.key,
                node.value,
                *(generator.iter for generator in node.generators),
            ]
        ):
            raise _UnclassifiableShape(node)
        return _OPAQUE  # EVIDENCE: as above, for mapping comprehensions.
    if isinstance(node, ast.Starred):
        # Unpacking is TRANSPARENT: it carries whatever its operand carries.
        return _canonicalise(node.value, func, seen)
    if isinstance(node, ast.Compare | ast.UnaryOp):
        # EVIDENCE (executed, not reasoned): `"a" == "b"` -> False, `not "a"` -> False —
        # both evaluate to a bool, so neither can carry prose. ``BoolOp`` was ONCE bundled
        # into this exemption under the same claim, and that claim was FALSE: `or`/`and`
        # return an OPERAND, not a bool (`"" or "prose"` -> 'prose'), so it now lives in
        # the TEXT-BUILDING half above. Do not re-bundle them: one comment stating a
        # reason true for two node types and false for a third is how that defect was born.
        return _OPAQUE
    if isinstance(node, ast.Await):
        return _OPAQUE  # EVIDENCE: same cross-function bound as a plain call.
    raise _UnclassifiableShape(node)


def _canonicalise_binop(
    node: ast.BinOp, func: ast.FunctionDef | ast.AsyncFunctionDef, seen: frozenset[str]
) -> _Canon:
    """``+`` concatenates; ``%`` is printf-formatting when its LEFT side is text;
    every other operator over TEXT (``"-" * 20``) is denied rather than guessed."""
    left = _canonicalise(node.left, func, seen)
    if isinstance(node.op, ast.Add):
        right = _canonicalise(node.right, func, seen)
        combined = tuple(
            lhs + rhs for lhs in left.templates for rhs in right.templates
        )
        if len(combined) > _MAX_CANONICALS:
            raise _UnclassifiableShape(node)
        return _Canon(combined, left.is_string or right.is_string)
    if isinstance(node.op, ast.Mod):
        if not left.is_string:
            # The retired evidence here — "numeric modulo, not %-formatting" — was FALSE
            # whenever the LEFT side is a RUNTIME format string: `fmt % "PROMISE"` returns
            # 'PROMISE'. With an opaque template the slot structure is unknowable, so the
            # right operand's literal text cannot be placed — DENY rather than drop it,
            # matching the Add/final-branch discipline (this was the only binop path that
            # returned opaque while a string operand was present).
            if _canonicalise(node.right, func, seen).is_string:
                raise _UnclassifiableShape(node)
            return _OPAQUE  # EVIDENCE: numeric modulo over runtime values.
        base = tuple(_printf_to_placeholders(t) for t in left.templates)
        # The RIGHT operand supplies the slots — its literal text reaches the output, so
        # it is incorporated rather than dropped. A tuple/list of values is unpacked
        # positionally; anything else fills the first slot.
        if isinstance(node.right, ast.Tuple | ast.List):
            arg_canons = [_canonicalise(element, func, seen) for element in node.right.elts]
        else:
            arg_canons = [_canonicalise(node.right, func, seen)]
        return _Canon(_substitute_placeholders(base, arg_canons), True)
    right = _canonicalise(node.right, func, seen)
    if left.is_string or right.is_string:
        raise _UnclassifiableShape(node)
    return _OPAQUE  # EVIDENCE: arithmetic over runtime values yields no prose.


def _string_templates(
    node: ast.expr,
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    seen: frozenset[str],
) -> list[str]:
    """Thin compatibility wrapper over :func:`_canonicalise` for the render-template
    scanner. Raises :class:`_UnclassifiableShape` on an unknown shape."""
    return list(_canonicalise(node, func, seen).templates)


def _has_literal_text(template: str) -> bool:
    """A template carries classifiable text only if SOMETHING survives once the
    placeholders are removed and whitespace is stripped — a pure-dynamic wrap
    (``sanitise_line(x)`` -> "{}") or a whitespace-only join promises nothing."""
    return template.replace(_PLACEHOLDER, "").strip() != ""


def _scan_safe_str_over_tree(
    tree: ast.AST,
) -> tuple[list[tuple[str, int, str]], list[tuple[str, int, str]]]:
    """``(classifiable literals, UNCLASSIFIABLE sites)`` for every safe_str/
    sanitise_line call inside a comms render/handler function of the given tree.
    The second list is the deny-by-default channel: a shape we cannot canonicalise
    is REPORTED, never silently skipped."""
    literals: list[tuple[str, int, str]] = []
    unclassifiable: list[tuple[str, int, str]] = []
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
            try:
                templates = _string_templates(sub.args[0], node, frozenset())
            except _UnclassifiableShape as shape:
                unclassifiable.append((node.name, sub.lineno, shape.dump))
                continue
            for template in templates:
                if _has_literal_text(template):
                    literals.append((node.name, sub.lineno, template))
    return literals, unclassifiable


def _comms_render_safe_str_literals() -> list[tuple[str, int, str]]:
    tree = ast.parse(_SERVER_PY.read_text(encoding="utf-8"), filename="server.py")
    return _scan_safe_str_over_tree(tree)[0]


def _comms_render_unclassifiable_shapes() -> list[tuple[str, int, str]]:
    """Every UNCLASSIFIABLE string shape in the shipped comms render surface, across
    BOTH scanners — the deny-by-default channel's production reading."""
    tree = ast.parse(_SERVER_PY.read_text(encoding="utf-8"), filename="server.py")
    return _scan_render_literals_over_tree(tree)[1] + _scan_safe_str_over_tree(tree)[1]


def _scan_safe_str_source(source: str) -> list[str]:
    """The item-2 scanner applied to arbitrary source (the self-attack surface,
    mirroring the CORE's ``_scan_source``)."""
    return [text for _fn, _line, text in _scan_safe_str_over_tree(ast.parse(source))[0]]


def _scan_safe_str_source_unclassifiable(source: str) -> list[str]:
    """The DENIED shapes for arbitrary source — the self-attack surface for the
    deny-by-default branch."""
    return [dump for _fn, _line, dump in _scan_safe_str_over_tree(ast.parse(source))[1]]


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


class TestTheCanonicaliserDeniesByDefault:
    """ITEM A — DENY-BY-DEFAULT. The retired canonicaliser ended in
    ``else: [_PLACEHOLDER]``: an unknown shape silently became "{}" and was then
    discarded as textless, so ``%``-format, ``.format`` and ``str.join`` each served
    promises INVISIBLY. Unknown shape now FAILS LOUD. These tests pin both halves —
    the text-building shapes that must canonicalise, and the ones that must deny —
    plus the positive control that honest opaque code never reds."""

    def test_no_unclassifiable_shape_in_the_shipped_comms_surface(self) -> None:
        """COVERAGE IS A CHECKED VARIABLE — this is the deny branch's OWN reach check.
        Every render-verb and safe_str call site in production must canonicalise; a
        shape that denies here is either a real new smuggling surface or a
        canonicaliser gap, and either way it must be looked at, not tolerated."""
        unclassifiable = _comms_render_unclassifiable_shapes()
        assert not unclassifiable, (
            "a comms render call site uses a string shape the canonicaliser cannot turn "
            "into a stable template. Teach it the shape, or declare the shape OPAQUE with "
            "evidence that it cannot carry literal text — never leave it unclassified:\n"
            + "\n".join(f"  {fn}:{line}: {dump}" for fn, line, dump in unclassifiable)
        )

    @pytest.mark.parametrize(
        ("body", "expected"),
        [
            ('safe_str("do it: action=teleport %s" % n)', "do it: action=teleport {}"),
            ('safe_str("do it: action=teleport %(k)s" % d)', "do it: action=teleport {}"),
            ('safe_str("do it: action=teleport {}".format(n))', "do it: action=teleport {}"),
            ('safe_str("".join(["do it: ", "action=teleport"]))', "do it: action=teleport"),
            ('safe_str("do" + " it: " + "action=teleport")', "do it: action=teleport"),
            ('safe_str(("do it: action=teleport %s" % n) + "!")', "do it: action=teleport {}!"),
        ],
        ids=["printf", "printf-mapping", "format", "join", "concat-chain", "printf-then-concat"],
    )
    def test_a_text_building_shape_is_canonicalised_not_invisible(
        self, body: str, expected: str
    ) -> None:
        """The three shapes the audit found live, plus their compositions: each must
        surface its literal text so the classification check can red on it."""
        source = f"def _render_comms_new(n, d):\n    return {body}\n"
        found = _scan_safe_str_source(source)
        assert found == [expected], found
        assert expected not in _safe_str_classified()  # ...and therefore UNCLASSIFIED -> RED

    @pytest.mark.parametrize(
        "body",
        [
            'safe_str("do it: action=teleport".upper())',
            'safe_str("do it: XX".replace("XX", "action=teleport"))',
            'safe_str("do it: action=teleport!!"[:-2])',
            'safe_str("do it: action=teleport" * 2)',
            'safe_str(["do it: action=teleport"])',
            'safe_str({"k": "do it: action=teleport"})',
            'safe_str([*["do it: action=teleport"]])',
            'safe_str([x for x in ["do it: action=teleport"]])',
            'safe_str("".join(x for x in ["do it: action=teleport"]))',
            'safe_str(b"do it".decode())',
        ],
        ids=[
            "str-upper",
            "str-replace",
            "slice-of-literal",
            "literal-times-n",
            "list-to-sink",
            "dict-to-sink",
            "starred-unpack",
            "comprehension-iterable",
            "join-over-genexp",
            "bytes-constant",
        ],
    )
    def test_an_uncanonicalisable_text_shape_is_DENIED_not_silently_dropped(
        self, body: str
    ) -> None:
        """Every one of these carries literal text through a shape we will not guess.
        Deny-by-default means they surface as UNCLASSIFIABLE (RED), never vanish.
        ``starred-unpack`` and ``comprehension-iterable`` are here because they broke
        this design's FIRST attempt — see REPORT-pkt02a-finalwave.md's attack table."""
        source = f"def _render_comms_new(x):\n    return {body}\n"
        denied = _scan_safe_str_source_unclassifiable(source)
        assert denied, f"shape was silently dropped instead of denied: {body}"
        assert _scan_safe_str_source(source) == []

    def test_positive_control_honest_opaque_production_shapes_never_deny(self) -> None:
        """THE false-positive control (repo law: "a gate that refuses honest code is a
        gate that gets SWITCHED OFF"). Every opaque shape production actually uses —
        attribute reads, slices of runtime values, ordinary calls, containers of
        runtime values, comprehensions — must canonicalise quietly, not red."""
        benign = (
            "def _render_comms_ok(entry, row, agent, versions):\n"
            "    name = sanitise_line(entry.agent_name)\n"
            "    suffix = '(unbriefed)' if entry.acked_version is None else f'(v{entry.acked_version})'\n"
            "    counts = {}\n"
            "    cells = [render_join(' ', [safe_str('role'), sanitise_line(row.role)])]\n"
            "    ranked = [v for v in versions if v > 0]\n"
            "    _ = safe_str(row.task_id[:8] + '…')\n"
            "    _ = safe_str(AppContext._render_age(5))\n"
            "    _ = sanitise_line(agent.name)\n"
            "    _ = safe_str(f'{counts[1]} at v{1}')\n"
            "    return safe_str(f'{name} {suffix}')\n"
        )
        denied = _scan_safe_str_source_unclassifiable(benign)
        assert denied == [], f"honest opaque code was falsely denied: {denied}"

    @pytest.mark.parametrize(
        "body",
        [
            'safe_str(x or "do it: action=teleport")',
            'safe_str(x and "do it: action=teleport")',
            'safe_str(row.last_note or "no note — run lore_comms action=heartbeat note=… to add one")',
        ],
        ids=["or-default", "and-default", "honest-or-default-render"],
    )
    def test_a_BoolOp_operand_is_transparent_not_a_bool(self, body: str) -> None:
        """R1 REGRESSION PIN. ``BoolOp`` was once exempted as opaque under the evidence
        "these evaluate to bools/numbers, never to prose". EXECUTED, that claim is FALSE:
        `or`/`and` return an OPERAND (`"" or "prose"` -> 'prose'), so the ``x or "…"``
        default idiom — an HONEST render shape — served its literal fully INVISIBLY.
        ``Compare``/``UnaryOp`` keep the exemption because for them the claim is true."""
        source = f"def _render_comms_new(x, row):\n    return {body}\n"
        found = _scan_safe_str_source(source)
        assert found, f"BoolOp operand text went invisible again: {body}"
        assert any("action=" in text for text in found), found

    def test_the_retired_BoolOp_evidence_claim_is_false_by_execution(self) -> None:
        """The measurement that condemns the retired exemption, kept executable so the
        claim can never be re-asserted from memory: two of the three bundled node types
        yield a bool; ``BoolOp`` yields an operand."""
        assert isinstance(eval('"a" == "b"'), bool)  # noqa: S307 - literal, no input
        assert isinstance(eval('not "a"'), bool)  # noqa: S307 - literal, no input
        assert eval('"" or "prose"') == "prose"  # noqa: S307 - literal, no input

    @pytest.mark.parametrize(
        "body",
        [
            'safe_str(d.get(k, "do it: action=teleport"))',
            'safe_str(getattr(o, n, "do it: action=teleport"))',
            'safe_str(next(it, "do it: action=teleport"))',
            'safe_str(str("do it: action=teleport"))',
            'safe_str("{}".format("do it: action=teleport"))',
            'safe_str("%s" % ("do it: action=teleport",))',
            'safe_str((lambda: "do it: action=teleport")())',
        ],
        ids=[
            "dict-get-default",
            "getattr-default",
            "next-default",
            "str-of-literal",
            "format-argument",
            "printf-argument",
            "immediately-invoked-lambda",
        ],
    )
    def test_literal_text_in_a_transparent_ARGUMENT_position_is_reached(self, body: str) -> None:
        """R2. Text-building calls (``.format``/``%``/``.join``) INCORPORATE their
        arguments; transparent-in-position calls (``d.get(k, DEFAULT)``, ``getattr``,
        ``next``, ``str``) can return a position VERBATIM. Both recurse — the same
        transparency ``BoolOp``/``IfExp`` have, applied to argument positions. The
        ``d.get(k, "…")`` default-lookup idiom is the high-realism one."""
        source = f"def _render_comms_new(d, k, o, n, it):\n    return {body}\n"
        found = _scan_safe_str_source(source)
        assert any("action=" in text for text in found), found

    @pytest.mark.parametrize(
        "source",
        [
            'def _render_comms_cell(label="do it: action=teleport"):\n    return safe_str(label)\n',
            'def _render_comms_cell(*, label="do it: action=teleport"):\n    return safe_str(label)\n',
            'def _render_comms_cell(a, b=1, label="do it: action=teleport"):\n    return safe_str(label)\n',
        ],
        ids=["positional-default", "keyword-only-default", "default-in-tail-position"],
    )
    def test_O1_a_parameter_DEFAULT_binds_a_literal_locally(self, source: str) -> None:
        """O1 REGRESSION PIN. The retired evidence *"a parameter/free name binds no
        literal HERE"* was FALSE: a defaulted parameter binds its literal in THIS
        function's own signature and serves it. Not the cross-function bound — the text
        is local, so it is in scope."""
        found = _scan_safe_str_source(source)
        assert any("action=" in text for text in found), found

    def test_O1_the_retired_claim_is_false_by_execution(self) -> None:
        """Keep the condemning measurement EXECUTABLE (the BoolOp lesson): a parameter
        default is a local literal binding, whatever a comment may claim."""

        def positional(label: str = "PROMISE") -> str:
            return label

        def keyword_only(*, label: str = "KWPROMISE") -> str:
            return label

        assert positional() == "PROMISE"
        assert keyword_only() == "KWPROMISE"

    def test_O2_percent_with_a_runtime_left_operand_is_denied_not_dropped(self) -> None:
        """O2 REGRESSION PIN. The retired evidence *"numeric modulo, not %-formatting"*
        was FALSE when the LEFT side is a runtime format string. With an opaque template
        the slot structure is unknowable, so this DENIES rather than dropping the right
        operand — the only binop path that used to return opaque with a string present."""
        source = (
            'def _render_comms_cell(fmt):\n    return safe_str(fmt % "do it: action=teleport")\n'
        )
        assert _scan_safe_str_source_unclassifiable(source), "the right operand was dropped again"
        assert _scan_safe_str_source(source) == []

    def test_O2_numeric_modulo_still_does_not_deny(self) -> None:
        """The false-positive control for O2: ordinary arithmetic modulo over runtime
        values must stay opaque, or honest math would red."""
        source = "def _render_comms_cell(a, b):\n    return safe_str(a % b)\n"
        assert _scan_safe_str_source_unclassifiable(source) == []

    def test_O2_the_retired_claim_is_false_by_execution(self) -> None:
        format_string = "%s"
        assert format_string % "PROMISE" == "PROMISE"

    def test_O3_the_keyword_spelling_of_a_transparent_position_is_read(self) -> None:
        """O3 REGRESSION PIN. ``_canonicalise_transparent_positions`` read only
        ``node.args``, so the keyword spelling slipped through."""
        source = (
            'def _render_comms_cell():\n    return safe_str(str(object="do it: action=teleport"))\n'
        )
        found = _scan_safe_str_source(source)
        assert any("action=" in text for text in found), found

    def test_O3_str_is_the_only_kwarg_reachable_transparent_builtin(self) -> None:
        """The EVIDENCE behind the one-entry keyword table, kept executable: the other
        three transparent-in-position builtins reject keywords outright, so they cannot be
        reached this way. Re-measure before adding an entry."""
        # Bound through ``Any`` on purpose: mypy/ruff reject these calls STATICALLY, but
        # what this test measures is what CPython does at RUNTIME — which is precisely the
        # kind of claim that must be executed rather than reasoned about.
        string_builtin: Any = str
        assert string_builtin(object="PROMISE") == "PROMISE"
        mapping_get: Any = {}.get
        getattr_builtin: Any = getattr
        next_builtin: Any = next
        rejecting: list[tuple[Any, tuple[Any, ...]]] = [
            (mapping_get, ("k",)),
            (getattr_builtin, (object(), "x")),
            (next_builtin, (iter([]),)),
        ]
        for call, arguments in rejecting:
            with pytest.raises(TypeError, match="takes no keyword arguments"):
                call(*arguments, default="X")

    def test_the_precise_argument_rule_has_ZERO_false_positives(self) -> None:
        """THE control that keeps R2 honest. A BLUNT "recurse into every call argument"
        rule was measured at SIX false positives on the shipped surface (it surfaces
        dict-lookup KEYS and other literals that never reach output). The precise rule —
        text-building calls plus a named transparent-position set — measures ZERO. If this
        ever fires, REPORT the honest shape that tripped it; do NOT widen the opaque set
        to silence it."""
        assert _comms_render_unclassifiable_shapes() == []
        for _fn, _line, text in _comms_render_safe_str_literals():
            assert text in _safe_str_classified(), (
                f"argument-position recursion surfaced an unclassified literal {text!r} — "
                "if this is honest production code, the rule is too blunt: report it"
            )

    def test_the_denial_names_the_shape_it_could_not_canonicalise(self) -> None:
        """A denial must be ACTIONABLE: it carries the ``ast.dump`` so the next author
        can see exactly which shape to teach or exempt."""
        source = "def _render_comms_new(x):\n    return safe_str('do it'.upper())\n"
        denied = _scan_safe_str_source_unclassifiable(source)
        assert len(denied) == 1, denied
        assert "Call" in denied[0] and "upper" in denied[0], denied[0]


# =========================================================================== #
# ITEM B — MARKER CROSS-SATISFACTION META-TEST.
#
# The cold audit found 6/16 non-discriminating markers BY HAND. This mechanizes
# that review permanently: for every proof P and every OTHER proof Q, P's marker
# must NOT appear in Q's emit render — otherwise P's marker is not specific to the
# line it claims to prove, and P could pass while its own line never rendered.
# An exemption is a DECLARATION WITH A REASON, never a way to silence a red.
# =========================================================================== #


def _proof_literal_containing(fragment: str) -> str:
    """The single registry literal containing ``fragment`` — self-validating, so the
    exemption set below can never silently bind to the wrong (or an ambiguous) proof."""
    matches = sorted(literal for literal in _PROMISE_PROOFS if fragment in literal)
    assert len(matches) == 1, f"{fragment!r} matched {len(matches)} literals: {matches!r}"
    return matches[0]


_REGISTER_ACK_LINE = _proof_literal_containing("ack recorded (via register)")
_REGISTER_ECHO_LINE = _proof_literal_containing("echo in your report")

# The ONLY sanctioned co-emission: both lines are rendered by the SAME
# ``_render_comms_register`` call under ONE structural gate (``brief is not None``),
# so each necessarily appears in the other's emit render. That is correct behaviour,
# not a weak marker — and each still has a NO-EMIT leg (brief=None) that gates it.
_MARKER_CO_EMISSION_EXEMPTIONS: dict[tuple[str, str], str] = {
    (_REGISTER_ACK_LINE, _REGISTER_ECHO_LINE): (
        "same register render, one structural gate (brief is not None) — co-emission is "
        "the specified behaviour; both are still gated by the brief=None NO-EMIT leg"
    ),
    (_REGISTER_ECHO_LINE, _REGISTER_ACK_LINE): (
        "the mirror of the above — same render, same single gate"
    ),
}


def _cross_satisfied_markers(
    proofs: dict[str, PromiseProof], exemptions: dict[tuple[str, str], str]
) -> list[tuple[str, str]]:
    """Every ``(marker_owner, other_proof)`` pair where the owner's marker is ALSO
    satisfied by the other proof's emit render, minus declared exemptions."""
    renders = {literal: proof.render_emit() for literal, proof in proofs.items()}
    violations: list[tuple[str, str]] = []
    for owner, proof in proofs.items():
        for other in proofs:
            if owner == other:
                continue
            if proof.marker in renders[other] and (owner, other) not in exemptions:
                violations.append((owner, other))
    return violations


class TestNoMarkerIsCrossSatisfiedByAnotherProof:
    """Mechanized replacement for the audit's by-hand marker review."""

    def test_no_marker_is_cross_satisfied(self) -> None:
        violations = _cross_satisfied_markers(_PROMISE_PROOFS, _MARKER_CO_EMISSION_EXEMPTIONS)
        assert not violations, (
            "a proof's marker is ALSO satisfied by another proof's emit render, so it is "
            "not specific to the line it claims to prove — strengthen it to the FULL "
            "rendered line, or declare a co-emission exemption WITH A REASON (never to "
            "silence a red):\n"
            + "\n".join(
                f"  marker of {owner!r}\n    also emitted by {other!r}"
                for owner, other in violations
            )
        )

    def test_every_exemption_is_declared_with_a_reason(self) -> None:
        blank = [pair for pair, reason in _MARKER_CO_EMISSION_EXEMPTIONS.items() if not reason.strip()]
        assert not blank, f"exemption(s) without a reason: {blank!r}"

    def test_every_exemption_names_registered_proofs(self) -> None:
        """A stale exemption (naming a literal no longer registered) would silently
        widen the allowance — the same dead-entry rot the registry scanners forbid."""
        stale = [
            pair
            for pair in _MARKER_CO_EMISSION_EXEMPTIONS
            if pair[0] not in _PROMISE_PROOFS or pair[1] not in _PROMISE_PROOFS
        ]
        assert not stale, f"exemption(s) naming unregistered literals: {stale!r}"

    def test_the_meta_test_catches_a_reintroduced_weak_marker(self) -> None:
        """SELF-ATTACK: shorten the 7b collapse marker back to the suffix it SHARES with
        the 7a variant. The meta-test must go RED — with the correct marker set green as
        the positive control (the sibling test above)."""
        weak_target = _proof_literal_containing("more briefs: {names} — brief_get")
        weakened = dict(_PROMISE_PROOFS)
        weakened[weak_target] = replace(
            _PROMISE_PROOFS[weak_target], marker=f"{_EM_DASH} brief_get each by name"
        )
        violations = _cross_satisfied_markers(weakened, _MARKER_CO_EMISSION_EXEMPTIONS)
        assert violations, (
            "the cross-satisfaction meta-test did NOT catch a marker weakened to a "
            "shared suffix — the instrument is not discriminating"
        )

    def test_an_undeclared_exemption_does_not_hide_a_violation(self) -> None:
        """The exemption set must be the ONLY escape: with exemptions emptied, the one
        sanctioned co-emission pair reappears as a violation (proving the set is load-
        bearing and not decorative)."""
        violations = _cross_satisfied_markers(_PROMISE_PROOFS, {})
        assert (_REGISTER_ACK_LINE, _REGISTER_ECHO_LINE) in violations, violations


class TestMarkerCrossSatisfactionBound:
    """PIN THE MISS (repo law: "an unpinned known limitation is indistinguishable from an
    unknown one"). The cross-satisfaction meta-test above compares proofs against EACH
    OTHER — it fires only when one proof's marker is satisfied by ANOTHER proof's render.
    It therefore CANNOT see a marker that is weak against a BROKEN BUILD but happens to be
    textually absent from every sibling render.

    The measured instance is the very weakness the cold audit found by hand: 7b's marker
    shortened to the k-specific prefix ``"behind on 1 more briefs:"``. No other proof's
    render contains it (7a's fixture renders ``k=6``, so the two renders are textually
    disjoint) — yet it is still a bad marker, because a build that ALWAYS renders the
    ``(+{extra} more)`` variant satisfies it. That build is caught by the emit/no-emit
    MUTATION proof, not by this meta-test.

    THE POINT, for whoever reads a green suite next: **a green cross-satisfaction run does
    NOT mean "my markers are proven strong."** Item B does not retire the mutation
    discipline; the two instruments answer different questions (proof-vs-proof, and
    proof-vs-broken-implementation) and a marker needs both.

    NAMED RE-OPEN TRIGGER: the day a per-proof "marker must not survive a SIBLING-BRANCH
    render of the SAME helper" check lands (the instrument shape proposed in
    REPORT-pkt02a-finalwave.md §F, ledgered as its own item), this bound is CLOSED —
    delete this pin and say so."""

    def test_KNOWN_BOUND_a_k_specific_prefix_weakening_is_not_caught(self) -> None:
        target = _proof_literal_containing("more briefs: {names} — brief_get")
        prefix_marker = f"behind on {_P7B_REMAINDER} more briefs:"

        # THE MECHANISM of the bound, pinned explicitly: the sibling (7a) fixture renders a
        # DIFFERENT k, so its render cannot contain 7b's k-specific prefix. This is WHY
        # proof-vs-proof comparison is blind here.
        seven_a = _proof_literal_containing("(+{extra} more)")
        assert prefix_marker not in _PROMISE_PROOFS[seven_a].render_emit(), (
            "the 7a fixture now renders the same k as 7b — the mechanism behind this known "
            "bound has changed; re-derive the bound before trusting this pin"
        )

        # THE BOUND ITSELF: a k-specific prefix weakening slips through cross-satisfaction.
        prefix_weakened = dict(_PROMISE_PROOFS)
        prefix_weakened[target] = replace(_PROMISE_PROOFS[target], marker=prefix_marker)
        assert _cross_satisfied_markers(prefix_weakened, _MARKER_CO_EMISSION_EXEMPTIONS) == [], (
            "the cross-satisfaction meta-test NOW catches a k-specific prefix weakening — "
            "this KNOWN BOUND is closed. If you closed it deliberately (e.g. the "
            "sibling-branch render check landed), delete this pin and say so — or the "
            "production renders changed — check the other failures first."
        )

        # POSITIVE CONTROL: the meta-test is not simply dead — the shared-SUFFIX weakening,
        # which IS textually present in 7a's render, is caught.
        suffix_weakened = dict(_PROMISE_PROOFS)
        suffix_weakened[target] = replace(
            _PROMISE_PROOFS[target], marker=f"{_EM_DASH} brief_get each by name"
        )
        assert _cross_satisfied_markers(suffix_weakened, _MARKER_CO_EMISSION_EXEMPTIONS), (
            "the meta-test failed to catch even a shared-SUFFIX weakening — the instrument "
            "is broken, not merely bounded"
        )


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

    def test_KNOWN_BOUND_a_promise_carried_in_a_render_VALUE_is_not_inspected(self) -> None:
        """PIN THE MISS #2 (fix-wave item 4): neither scanner inspects the VALUE kwargs of
        ``render_line`` — only the TEMPLATE. A promise passed as a value, e.g.
        ``render_line("{msg}", msg=...)``, is caught TODAY only incidentally, because the
        structural template ``"{msg}"`` is itself UNCLASSIFIED and so fails the default-FAIL
        classification check.

        RE-OPEN TRIGGER — read this before classifying anything: the day a
        placeholder-only, structural-LOOKING template (``"{msg}"``, ``"{line}"``, ``"{cells}"``)
        is added to :data:`_PROMISE_FREE`, this bound MUST be closed first (extend the scan to
        literal kwarg VALUES), because that classification is exactly what would make a
        value-carried promise invisible. Classifying such a template without closing the bound
        silently disarms the guard for that call site."""
        source = (
            "def _render_comms_x():\n"
            '    return render_line("{msg}", msg="do the thing: lore_comms action=teleport now")\n'
        )
        templates = _scan_render_literals_source(source)
        # The TEMPLATE is all that is seen — and it is unclassified, which is the ONLY
        # reason this shape fails today.
        assert templates == ["{msg}"], templates
        assert "{msg}" not in _classified(), (
            "'{msg}' has been classified as promise-free — the value-carried promise bound "
            "documented here is now OPEN. Close it (scan literal kwarg values) or revert."
        )
        # The promise TEXT itself is invisible to BOTH scanners.
        assert not any("teleport" in text for text in templates), templates
        assert _scan_safe_str_source(source) == []
