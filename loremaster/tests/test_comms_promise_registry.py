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
emitted IFF its predicate holds — is pinned in ``test_comms_render_architecture.py``
(``TestFirstVersionTailIsTypedNotNameDerived`` for the register-ack promise;
``TestSkewTailIsNameConditioned`` for the three heartbeat-surfacing tails, ∀ the
(is-standing, has-unbriefed) predicate combinations). This module is the STATIC
completeness half — that no promise ships UNregistered. See REPORT-pkt02-contract.md §E
for the sizing split (the residual — promises smuggled through ``safe_str(f"...")``
literal text rather than a render_line template — is the 02a extension, documented in
:data:`_SAFE_STR_LITERAL_RESIDUAL`).

RED expectation: this module is GREEN against the correct build (every literal is
classified) — it is a completeness INVARIANT, not a fix-pin. Its self-attack tests
(``TestTheGuardActuallyCatchesViolations``) prove it is a REAL detector: a synthetic
unclassified promise is caught, and a positive control (a correctly-registered promise)
passes — so a green result here is never vacuous.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

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

# The known residual (03a / 02a): a promise could in principle be smuggled through
# ``safe_str(f"...")`` LITERAL TEXT rather than a render_line/render_join template — the
# fleet cell's ``safe_str(f"project v{n}")`` is the shape (there it is a label, not a
# promise, but the scanner below does NOT cover that surface). Closing it means scanning
# JoinedStr literal segments inside safe_str/sanitise_line calls in comms render funcs and
# classifying those too — a bounded but real extension, recommended as the 02a split.
_SAFE_STR_LITERAL_RESIDUAL = (
    "safe_str(f'...') literal text in comms render funcs is NOT scanned here — 02a extension"
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
            f"registry/free entry:\n" + "\n".join(f"  {text!r}" for text in dead)
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
