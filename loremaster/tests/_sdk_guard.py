"""THE RUNTIME SDK GUARD — the invariant, and the only instrument in this wave that is
not keyed on a name.

    No call on a live SurrealDB connection may escape the retry driver.

WHY IT LIVES HERE AND NOT IN THE CONTRACT FILE. Six rounds of this session, six
instruments, six defeats — and every one was the same mistake in a new coat:

    the retry gate      keyed on a label's LITERAL        -> a substring of it
    the retired pin     keyed on a symbol's NAME          -> a numeric claim naming nothing
    the seam enumerator keyed on `async def _query`       -> scout.py
    the SDK gate v2     keyed on 3 METHOD names           -> the other 30 (`upsert`)
    the SDK gate v3     keyed on 2 RECEIVER names         -> six doors
    the SDK gate v4     RUNTIME, but armed in 4 TESTS     -> `_drain_pending`, never executed

The last one is the sharpest, because it looked like the fix. **A runtime gate is an
invariant only over code it actually RUNS.** Arming it inside four tests made COVERAGE the
new name-list: scout's pending-command drain simply never executed under it, so an
unretried SELECT there scored 932 passed / 0 failed and shipped finding #120 alive in the
tree certified as having fixed it.

So the guard is AUTOUSE, from conftest, for EVERY test in the suite. Any production path a
test drives is watched — by nobody's memory.

------------------------------------------------------------------------------
TWO MECHANISMS, AND BOTH WERE WRONG BEFORE THEY WERE RIGHT:

1. **The stack is walked at CALL time, not AWAIT time.** The wrapper is a plain ``def``
   that inspects the stack and then returns the SDK's coroutine unawaited. A wrapper that
   was ``async def`` did its walk when the event loop resumed the body — by which time the
   caller's frame is long gone. So::

       await connection.query(...)                      # caught
       await asyncio.gather(connection.query(...))      # INVISIBLE

   An ordinary, awaited gather — not even fire-and-forget — evaded it. The docstring
   claiming it "cannot be evaded by spelling" was FALSE, and one keyword fixed it.

2. **Attribution is by the IMMEDIATE caller, never "the nearest production frame".**
   A test that injects a ``connect`` callable runs test code with production frames still
   below it; the nearest-production rule blamed production for the test's own call and
   reported phantom escapes. A gate that cries wolf is deleted by the first engineer it
   blocks, and then we have nothing.

------------------------------------------------------------------------------
THE HONEST LIMIT, STATED BECAUSE A GATE THAT OVERSTATES ITS REACH IS THE THING WE POLICE:

**This is an invariant over EXECUTED paths.** A production call site that no test in the
suite ever runs is not watched by it. Two things cover that gap, and neither is silent
about being weaker:

  * :func:`observed_call_sites` — the guard records every call site it SEES, and the
    contract cross-checks that against the AST lint's enumeration. **A call site no test
    executes is NAMED, not silently unwatched.** Coverage stops being a hidden variable.
  * the AST lint (``TestNoProductionCodeCallsTheSdkOutsideTheSeam``) — keyed on names,
    therefore defeatable, and labelled as a lint in its own docstring. It sees code that
    never runs, which is precisely this guard's blind spot.

Between them: the lint covers all code weakly; the guard covers executed code absolutely;
and the coverage cross-check makes the seam between them visible instead of assumed.

------------------------------------------------------------------------------
THE KNOWN BLIND SPOT, ADJUDICATED RATHER THAN LEFT LYING AROUND:

**A callable captured BEFORE the guard arms** — a bound method, an unbound class function,
or a ``functools.partial`` stashed at import time or in a session-scoped fixture — bypasses
the instance attribute lookup the guard patches, and is invisible to it.

**Verdict: REAL, UNREACHABLE TODAY, LATENT — and verified, not assumed.** To exploit it,
production must capture the callable before a function-scoped autouse fixture runs, i.e. at
import or from session/module scope. Neither exists: there is no module-level connection
object and no session- or module-scoped fixture that builds one (grepped, both trees). The
attack was BUILT (``WB-CAPTURE``: capture ``AsyncWsSurrealConnection.query`` at import and
call through it) and it **died** — the behavioural pins inject FAKE connections, so any
build that bypasses instance attribute lookup breaks on them instead.

**It arms itself the day someone adds a module-level connection singleton, or caches a
bound SDK method at import.** If you are that person: this paragraph is for you.

(Threads are NOT a blind spot: the guard patches the CLASS, so the walk runs in the calling
thread whichever thread that is. Production makes no threaded SDK calls — no
``run_in_executor``, no ``to_thread`` — verified by grep.)
"""

from __future__ import annotations

import inspect
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from surrealdb import (
    AsyncEmbeddedSurrealConnection,
    AsyncHttpSurrealConnection,
    AsyncWsSurrealConnection,
)

# The REAL SDK connection classes, and EVERY public coroutine on each (33 today) —
# enumerated FROM the classes, so an SDK release adds methods without anyone editing a
# list. That is the whole point: the dangerous surface is the SDK's and grows without
# asking us; the safe surface is ours and is enumerable.
SDK_CONNECTION_CLASSES = (
    AsyncWsSurrealConnection,
    AsyncHttpSurrealConnection,
    AsyncEmbeddedSurrealConnection,
)

# THE SAFE SET — two methods, and the burden of proof sits on the ALLOWANCE, not the gate.
#   * ``signin`` — PROBED across 256 concurrent virgin connects: zero conflicts. It
#     authenticates a socket; it touches no row.
#   * ``close``  — tears the socket down. No statement, nothing left to contend for.
# ``kill`` was in this set once, on the reasoning that "cancelling a subscription writes no
# row". That is an OPINION — the identical move that blessed the bootstrap DDL, which then
# failed **6.2%–34.4%** of concurrent virgin first-connects on ``use()``, a call nobody
# suspected.
#
# THAT IS A RANGE, AND IT IS A RANGE ON PURPOSE (audit-fix-1 A4). This figure used to be
# carried as TWO different flat point-estimates across four sites — one of them here — and
# **neither was reproducible as stated**. The retired numerals are deliberately not re-typed
# even to narrate them: a retired number quoted in prose is still a number the next reader
# can copy, which is exactly how eight of them outlived their own retirement from production
# and standing law. Re-measured under the protocol below (16 racers x 10 rounds = 160 virgin
# first-connects, bootstrap UNRETRIED — HEAD's code path), three
# independent runs gave **55/160 (34.4%) · 43/160 (26.9%) · 10/160 (6.2%)**. The contention is
# real, common, and it swamps its own mean: quoting any single run as a measured constant is
# how a noisy sample becomes standing law. The DIRECTION is what is load-bearing here — an
# unretried bootstrap loses first-connects, often — and a range with its protocol says that
# honestly where a point estimate lies precisely.
# Receipt: NONE THAT CAN BE FOLLOWED. The probe named here was
# ``scratchpad/blindreader2/probe_bootstrap.py``, a scratch file that was never
# tracked and is gone from disk — so neither the three runs above nor
# ``signin``'s 256-connect clean bill can be re-checked against their
# instrument. The protocol IS stated in full above and is re-runnable, but
# until someone re-runs it, treat both as UNVERIFIED — and note that this is a
# deny-by-default safe set, where repo law requires every exemption to be
# evidence-backed. Re-measuring and archiving the probe under
# ``docs/plans/v2/receipts/`` is the standing fix.
SAFE_CONNECTION_METHODS = frozenset({"signin", "close"})


class GuardCannotSubstantiate(RuntimeError):
    """The guard was asked for a verdict it has no evidence for. (finding #136)

    A gate must never return a verdict it cannot back. Two ways it could:

    * **It watches a root no code executes from.** Then no frame is ever classified as
      production, it observes NOTHING, and "no escapes" is TRUE the way "no unicorns
      escaped" is true. That state was REACHABLE and REACHED: in an out-of-tree copy of
      the repo, the watched root was derived from the TEST FILE's path while ``loremaster``
      imported from the original checkout (an editable install's ``.pth`` names an absolute
      path). The three positive controls went RED — and every "no escapes" assertion beside
      them stayed GREEN, which is the whole disease in one line.
    * **It reports clean having seen nothing at all**, in a flow that provably calls the SDK.
      That is BLINDNESS wearing cleanliness. :meth:`GuardReport.require_observations` is how
      a caller refuses it.

    Both now RAISE. A green this guard reports is a green it can substantiate, or it is not
    a green at all.
    """


@dataclass(frozen=True)
class SdkEscape:
    """One production call on a live connection that the driver did not run."""

    method: str
    site: str

    def __str__(self) -> str:
        return f"{self.site} -> connection.{self.method}()"


@dataclass
class GuardReport:
    """What the guard saw during one test."""

    escapes: list[SdkEscape]
    observed: set[str]
    armed: bool
    watched_root: Path | None = None
    intercepted: int = 0
    # Bare ``.query()`` calls (NEVER ``.query_raw()``) that carried MORE THAN ONE
    # top-level statement — the #144 posture. ``.query()`` validates statement[0]
    # ONLY (store reference §3), so a later statement can fail and roll the whole
    # transaction back while ``.query()`` raises nothing; multi-statement SurrealQL
    # must ride ``execute_transaction`` (``query_raw``). Filled ORTHOGONALLY to
    # ``escapes``: a driver-wrapped multi-statement call is not a retry-escape, but it
    # IS a statement-count violation. The verdict comes from the SHARED
    # ``_txn._assert_envelope_integrity`` (see :func:`_is_multi_statement_query`).
    multi_statement_violations: list[SdkEscape] = field(default_factory=list)

    def require_observations(self, flow: str) -> None:
        """Refuse a "no escapes" verdict this report cannot substantiate. (#136)

        Call this before asserting cleanliness on a flow that PROVABLY calls the SDK.
        Zero production observations there does not mean the code was clean — it means the
        guard never saw the code at all, and its silence is worth nothing.
        """
        if self.observed:
            return
        raise GuardCannotSubstantiate(
            f"the guard observed ZERO production SDK calls while {flow} — a flow that "
            f"provably makes them. It intercepted {self.intercepted} SDK call(s) in total "
            f"and attributed NONE of them to production code under the watched root "
            f"{self.watched_root}. A 'no escapes' verdict here is BLINDNESS, not "
            "cleanliness, and a gate must never return a verdict it cannot substantiate "
            "(finding #136)."
        )


def _driver() -> Any:
    """``_txn.retry_on_conflict`` — or ``None`` before it exists."""
    from loremaster.store import _txn

    return getattr(_txn, "retry_on_conflict", None)


def _is_multi_statement_query(args: tuple[Any, ...]) -> bool:
    """Does this ``.query()`` call carry MORE THAN ONE top-level statement?

    The single-statement verdict is the SHARED ``_txn._assert_envelope_integrity`` — the
    SAME predicate ``compose()`` enforces on every fragment (ONE IMPLEMENTATION: this leg
    ROUTES to it, it does not re-derive the ``;``-counting policy). It raises on an
    internal statement separator or a bare ``BEGIN``/``COMMIT`` keyword; a single trailing
    ``;`` is peeled first, so the ordinary one-statement shape is never flagged.

    ⚠ The predicate is looked up on the MODULE at CALL time (``_txn._assert_envelope_
    integrity``), never captured at import — so a test that monkeypatches the module
    attribute is OBSERVED, which is exactly how the mutation-share pin proves this leg
    reads the shared predicate rather than a private clone (adversary-07 F0). An
    import-captured reference would silently pass every other pin and still be a clone in
    the dimension the ``;``-in-literal re-open trigger depends on.

    Only the FIRST positional arg is inspected (the SurrealQL string); a non-string or
    absent first arg is not a query string and is never a violation.
    """
    if not args:
        return False
    query_text = args[0]
    if not isinstance(query_text, str):
        return False
    from loremaster.store import _txn

    try:
        _txn._assert_envelope_integrity(query_text)
    except _txn.TxnEnvelopeViolationError:
        return True
    return False


def artifact_root() -> Path:
    """The directory ``loremaster`` ACTUALLY EXECUTES FROM — asked of the IMPORTED module.

    Never derived from this file's path. The guard judges a frame by its
    ``co_filename``, so the root it compares against must come from the same place the
    interpreter gets that string: the module it imported. Those two answers are identical
    in the checkout and DIFFERENT in an out-of-tree copy, where the tests are collected
    from the copy while an editable install's ``.pth`` imports ``loremaster`` from the
    original tree (finding #136). Deriving the root from ``__file__`` there aimed the guard
    at a directory nothing executes from — and it reported "no escapes" about it.
    """
    import loremaster

    location = loremaster.__file__
    if location is None:  # a namespace package: no __init__, nothing to execute
        raise GuardCannotSubstantiate(
            "the imported `loremaster` package has no __file__, so the guard cannot know "
            "where production code executes from and cannot judge a single frame."
        )
    return Path(location).resolve().parent


def _witness_file(witness: Any) -> Path:
    """The file the witness EXECUTES from, as a stack frame would report it."""
    code = getattr(witness, "__code__", witness)
    return Path(code.co_filename).resolve()


def _require_a_root_the_code_runs_from(production_root: Path, witness: Any) -> None:
    """The guard's arm-time precondition: the code it must judge lives under the root it
    watches. If it does not, no frame can EVER match and every verdict is vacuous — so it
    raises here instead of certifying nothing at all. (finding #136)
    """
    executes_from = _witness_file(witness)
    if executes_from.is_relative_to(production_root):
        return
    name = getattr(witness, "__qualname__", repr(witness))
    raise GuardCannotSubstantiate(
        f"the runtime SDK guard is watching {production_root}, but `{name}` — code it must "
        f"be able to see — executes from {executes_from}. No frame of it can ever match the "
        "watched root, so the guard would observe ZERO calls and report 'no escapes' for a "
        "reason that has nothing to do with the code being correct.\n\n"
        "That verdict would be VACUOUS, and a gate must never return a verdict it cannot "
        "substantiate (finding #136).\n\n"
        "USUAL CAUSE: the suite is running from an OUT-OF-TREE COPY whose `.venv` still "
        "carries an editable install pointing at the original checkout, so `loremaster` "
        "imports from there and NOT from the tree you are editing. Re-sync the copy's venv "
        "(`uv sync --reinstall-package loremaster`), or run the suite in the tree the venv "
        "points at."
    )


def install(
    monkeypatch: Any,
    *,
    production_root: Path | None = None,
    witness: Any = None,
) -> GuardReport:
    """Arm the guard for the current test. Returns the (live) report it fills in.

    ``production_root`` defaults to :func:`artifact_root` — where the imported package
    executes from, never where this file happens to sit on disk.

    ``witness`` is the code the guard must be able to SEE under that root; it defaults to
    the retry driver, which is production code by definition. Aiming the guard somewhere
    else (the controls aim it at their own test file) therefore REQUIRES naming the code
    you expect it to watch — and if that code does not execute from there, arming RAISES.
    You cannot ask this guard to watch a directory and then be told nothing happened there.

    ``armed=False`` when the shared driver does not exist yet: pre-build there is nothing
    to be "inside", so every call would be an escape and the whole suite would go red for
    a reason that teaches a builder nothing. The contract's OWN gate pins are red in that
    state (they name the missing driver), which is the honest RED. The moment the driver
    exists, this arms across every test in the suite.
    """
    report = GuardReport(escapes=[], observed=set(), armed=False)
    driver = _driver()
    if driver is None:
        return report

    watched = (artifact_root() if production_root is None else production_root).resolve()
    _require_a_root_the_code_runs_from(watched, driver if witness is None else witness)
    report.watched_root = watched

    driver_code = driver.__code__
    root = str(watched)

    def _judge() -> tuple[bool, str | None]:
        """``(allowed, site)`` for the call happening RIGHT NOW.

        ``site`` is the IMMEDIATE caller and only the immediate caller: the frame that
        actually made this call. If that frame is not production, this is not a production
        call — not the SDK calling itself, not a test driving the engine, not a harness
        fixture. ``allowed`` needs the whole stack, because the driver may be several
        frames up.
        """
        immediate: Any = sys._getframe(2)
        if immediate is None:
            return True, None
        filename = immediate.f_code.co_filename
        if not filename.startswith(root):
            return True, None
        site = (
            f"{Path(filename).relative_to(watched).as_posix()}"
            f":{immediate.f_lineno} in {immediate.f_code.co_name}()"
        )

        frame: Any = immediate
        while frame is not None:
            if frame.f_code is driver_code:
                return True, site
            frame = frame.f_back
        return False, site

    def _guard(method_name: str, original: Any) -> Any:
        # A PLAIN ``def``: the walk happens when the call is MADE. An ``async def`` wrapper
        # walks the stack when the loop resumes its body, by which time the caller's frame
        # is gone — so `asyncio.gather(connection.query(...))` was invisible while the
        # identical direct call was caught. One keyword.
        def _guarded(self: Any, *args: Any, **kwargs: Any) -> Any:
            report.intercepted += 1  # EVERY call, whoever made it: the guard's own reach
            allowed, site = _judge()
            if site is not None:
                report.observed.add(site)
                if not allowed:
                    report.escapes.append(SdkEscape(method=method_name, site=site))
                # ORTHOGONAL to the escape check (#144 posture): a bare ``.query()`` may
                # carry exactly ONE statement, whether or not it rode the driver. Scoped
                # to ``query`` by METHOD NAME — ``query_raw`` validates every statement and
                # is the safe multi-statement path. Receiver-BLIND (the class is patched),
                # which is the keystone letting the offline leg's receiver-name limit stand.
                if method_name == "query" and _is_multi_statement_query(args):
                    report.multi_statement_violations.append(
                        SdkEscape(method=method_name, site=site)
                    )
            return original(self, *args, **kwargs)  # the coroutine; the caller awaits it

        _guarded._sdk_guarded = True  # type: ignore[attr-defined]
        return _guarded

    for connection_class in SDK_CONNECTION_CLASSES:
        for name, function in inspect.getmembers(connection_class, inspect.isfunction):
            if name.startswith("_") or name in SAFE_CONNECTION_METHODS:
                continue
            # ``_sdk_guarded`` matters: the guard is AUTOUSE (conftest), so a test that
            # arms it a second time (the controls, which aim "production" at the test file)
            # would otherwise find every method already replaced by a plain ``def`` wrapper,
            # decide it is not a coroutine function, and silently wrap NOTHING. That is
            # exactly what happened, and the CONTROLS caught it — reporting `observed=set()`
            # rather than passing quietly. A control that cannot see its own instrument fail
            # is not a control.
            if not (
                inspect.iscoroutinefunction(function)
                or getattr(function, "_sdk_guarded", False)
            ):
                continue
            monkeypatch.setattr(connection_class, name, _guard(name, function))

    report.armed = True
    return report
