"""Contract — packet 61a-w3: the #398/#399 recurrence-prevention invariant.

Author: ``contract-61a-w3`` (Opus CONTRACT author — tests ONLY, no production code).
Ruling of record (executed verbatim, never re-transcribed): the packet-61 PDP-audit
sidecar ``docs/design/2026-08-22-packet61-pdp-audit-rulings.md`` **§Fork J**, which
executes packet-60 ``FR-1 Part 3`` (mandatory per standing law — an audit-caught defect
CLASS becomes a repo-local invariant; ledgered task ``06b195e306a34b6391174477bc7744e7``).
Findings closed: **#398** (lead-60 — packets 49 + 60) and **#399** (coldaudit-60-w1 — 5
sites). Both are the SAME class; the stale comments themselves were already retired in
``efccdc8`` / ``3077d23`` — THIS wave builds the INVARIANT that stops recurrence.

THE CLASS THIS PINS
-------------------
*A schema-slice function that EMITS DDL statements must not be able to LIE — in code
structure or in leading prose — about being empty / not-applied.* The concrete #398/#399
instance: a contract author writes a ``# ⚠⚠ RED STUBS … emit [] / emits NOTHING / NOT
folded into generate_ddl`` block above a slice fn; the builder greens the fn but LEAVES
the comment, so committed code carries a present-tense claim that contradicts the running
code. NO gate in this repo checks that a module's structure/prose agrees with what its
slices actually emit and where those statements are applied (the PKT-28 C1 /
rename-sweep "green-at-gate natural-language surface" class, CLAUDE.md).

THE SUBJECT
-----------
``loremaster/loremaster/store/surreal_schema.py`` — the ``_*_statements`` slice-fn
convention (each returns ``list[str]`` of DDL), ``generate_ddl`` (which folds slices by
CALLING them), and the standalone ``generate_*_ddl`` slices a dedicated store's
``ensure_ready`` consumes.

THE PROPERTY (§Fork J — STRUCTURAL primary, allowlist-the-safe prose backstop)
-----------------------------------------------------------------------------
* **PRIMARY — the STRUCTURAL fold-coverage check (undefeatable by rewording).** The set
  of slice fns is DERIVED by AST from the subject SOURCE (every top-level ``def`` whose
  name matches ``^_[a-z0-9_]+_statements$``), re-derived each run, never a hand-list.
  EVERY slice fn that EMITS ≥1 statement must be EITHER
    (a) **FOLDED** — REACHABLE from ``generate_ddl`` through slice-fn calls (also AST-
        derived), OR
    (b) **STANDALONE** — REACHABLE from SOME other top-level ``generate_*_ddl`` function
        (also AST-derived — the ``generate_agent_ddl`` / ``generate_graph_ddl`` / … slices
        a dedicated store's ``ensure_ready`` applies).
  ⚠ Reachability is a ROOTED TRANSITIVE closure, DIRECT or through a nested slice fn
  (packet 63a finding #452, reconciled 2026-09-03): a folded slice may itself CALL another
  ``_*_statements`` slice — the real ``_memory_statements`` → ``_governed_index_statements``
  shared-emitter shape (surreal_schema §4.1). The child's statements run wherever the parent
  runs, so it is covered; a DIRECT-only check false-flags it. The closure stays rooted at real
  entry points, so a slice reachable ONLY through an UNFOLDED parent is still uncovered (no
  false-clear) — see :meth:`TestFoldCoverageStructuralDiscrimination.
  test_a_nested_slice_whose_parent_is_unfolded_is_flagged`.
  A slice fn that EMITS statements yet is reachable from NEITHER root is DEAD DDL wearing an
  implementation — it REDS the scan. This catches the *"NOT folded into generate_ddl"*
  lie STRUCTURALLY, with **no forbidden literal**.

  ⚠ **Contract decision — DERIVED standalone set, not a literal hand-list.** §Fork J
  writes *"in an EXPLICIT allowlist of intentionally-standalone slices"*, but its own
  RIDER requires *"the derived-not-hand-list property"* (the P1c REACH ATTACK forces it),
  and CLAUDE.md's INSTRUMENT-0 / registration_sites law is *"prefer converting a
  hand-list into a derived one"*. A literal ``_STANDALONE_SLICES = {...}`` constant is a
  hidden reach constant — exactly the seventh instrument-defeat. So membership (b) is
  DERIVED from the AST as *"called by some generate_*_ddl"*. The audit that this derived
  set corresponds to REAL store consumers is in ``REPORT-contract-61a-w3.md`` §"Evidence-
  backed standalone allowlist" (each of the 12 unfolded slices → its ``generate_*_ddl``
  → the store ``ensure_ready`` that applies it). The alternative literal-allowlist reading
  is noted there for the adversary/lead.

* **BACKSTOP — the prose-lie leg (allowlist-the-safe, a NAMED KNOWN BOUND).** A slice fn
  that IS folded-or-standalone and EMITS ≥1 statement, yet whose docstring / leading
  comment asserts EMPTINESS, is a defect (the exact #398/#399 residual on an
  already-folded slice). Detecting "asserts emptiness" needs SOME literal set — the
  enumerate-the-forbidden limit — so this leg is BEST-EFFORT over a small CLOSED set of
  KNOWN phrasings (:data:`KNOWN_EMPTINESS_PHRASES`), and is **PINNED AS A KNOWN BOUND**
  (§"WHEN YOU CANNOT CLOSE A HOLE, PIN IT"): a NOVEL phrasing evades it — see
  :class:`TestStaleEmptinessProseIsAKnownBound`. **Threat model, stated in the
  instrument:** the STRUCTURAL leg (a) is the real defense; the prose leg only adds cover
  for an "emit []" comment on an ALREADY-folded slice (whose statements DO run, so the
  structural leg cannot see the lie). **Re-open trigger:** a new prose-evasion found in
  the wild → widen :data:`KNOWN_EMPTINESS_PHRASES` OR strengthen the structural check.

INSTRUMENT-0 — the guard's own reach is a CHECKED VARIABLE (§Fork J rider, the P1c REACH
ATTACK, CLAUDE.md INSTRUMENT-0)
-------------------------------------------------------------------------------------------
The slice-fn set is derived by a PREDICATE (the ``_*_statements`` name), which is itself a
reach surface: a slice renamed off the convention would be silently exempt. So the scan
carries an INDEPENDENT second derivation — the SHAPE oracle: every top-level PRIVATE
(``_``-prefixed) ``def`` annotated ``-> list[str]``. The scan FAILS CLOSED (raises
:class:`SchemaGuardReachError`) when the name-set and the shape-set DIVERGE, so a misnamed
emitter REDS the guard rather than escaping it — and when the name-set is EMPTY (a
wholesale convention rename / a mis-targeted source), so a blind scan can never return a
falsely-clean ``[]``. Measured at ``f87e774``: both derivations = 28, EQUAL (see
``REPORT-contract-61a-w3.md`` §"How the slice-fn set was derived"). ⚠ RESIDUAL BOUND: a
rename that ALSO drops the ``-> list[str]`` annotation evades BOTH derivations — pinned in
:class:`TestGuardReachIsACheckedVariable` with its re-open trigger.

WHY SOURCE-BASED (not dynamic import + call)
--------------------------------------------
The scan is a pure function of the module SOURCE TEXT (``ast.parse`` internally): every
synthetic fixture and every mutation proof below is just a string, with no import
fragility and NO static/dynamic divergence between the real module and the fixtures (one
code path grades both). Emptiness is CONSERVATIVE: a slice fn is treated as empty ONLY if
it provably ``return []`` (the literal RED-STUB shape); EVERY other body is treated as
EMITTING. That bias is deliberate — the scan may over-flag a slice that is dead-code-empty
in some exotic way (harmless: folding an empty slice is a no-op), but it can NEVER
false-clear a real emitter, which is the only dangerous direction for a coverage guard.

RED-at-HEAD discipline (the ``test_ast_reach_helpers`` / #133 idiom)
--------------------------------------------------------------------
The scan does not exist at ``f87e774`` (this contract's authoring tip). A top-level
``from _schema_fold_guard import scan_schema_fold_coverage`` would be a COLLECTION error
that hides every discriminating control, so the scan is reached ONLY through the lazy
accessors below (:func:`_scan_fold_fn` et al.), which turn "the helper is absent" into a
clean, NAMED assertion failure at RUN time. Every pin then still collects and runs, so the
positive/negative controls stay visible. Each accessor tolerates EITHER builder home:
``_logging_fixtures`` (the shared test-support home) or a dedicated ``_schema_fold_guard``
module.

⚠ Present-tense dating: every "RED at HEAD" / "= 28" / "0 findings" claim here is dated to
``f87e774``. A reader retrieving this after the build must re-derive.

Live store: NONE. This is a pure source/AST structural contract — it touches no SurrealDB
connection, so there is no ``ws://127.0.0.1:18000`` dependency and no skip marker.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

# --------------------------------------------------------------------------- #
# The subject-under-guard, imported ONLY to locate its source file (never to
# call its functions — the scan is source-based). Importing it here is safe: it
# is production code the whole suite already imports.
# --------------------------------------------------------------------------- #
import loremaster.store.surreal_schema as _subject

_SUBJECT_SOURCE: str = Path(_subject.__file__).read_text(encoding="utf-8")

#: The homes the builder may place the scan in (mirrors ``test_ast_reach_helpers``'s
#: ``_install_parse_guard_fn`` multi-home tolerance). ``_schema_fold_guard`` is the
#: dedicated home; ``_logging_fixtures`` is the shared test-support home. Either is fine.
_GUARD_HOMES = ("_schema_fold_guard", "_logging_fixtures")


def _guard_attr(name: str, contract_note: str) -> Any:
    """Reach a not-yet-built scan symbol through a home-tolerant lazy accessor.

    Fails NAMED and BEHAVIOURALLY at run time (never as a collection error) so every
    control in this file still collects and runs before the scan exists. The #133 /
    ``_parse_production_trees_fn`` idiom.
    """
    for home in _GUARD_HOMES:
        try:
            module = importlib.import_module(home)
        except ModuleNotFoundError:
            continue
        attr = getattr(module, name, None)
        if attr is not None:
            return attr
    raise AssertionError(
        f"packet 61a-w3 (§Fork J): `{name}` is not built in any of {_GUARD_HOMES}. "
        f"{contract_note}"
    )


def _scan_fold_fn() -> Callable[[str], list[Any]]:
    return cast(
        "Callable[[str], list[Any]]",
        _guard_attr(
            "scan_schema_fold_coverage",
            "Build `scan_schema_fold_coverage(source: str) -> list[FoldFinding]`: AST-parse "
            "`source`, DERIVE the slice-fn set (top-level `def` matching `^_[a-z0-9_]+_statements$`), "
            "the folded set (names called in `generate_ddl`), and the standalone set (names called "
            "in any other top-level `generate_*_ddl`); return one FoldFinding per slice fn that "
            "EMITS >=1 statement (conservative: NOT provably `return []`) and is in NEITHER set. "
            "FAIL CLOSED (raise SchemaGuardReachError) on an empty slice-fn set or a name/shape "
            "reach divergence — see the INSTRUMENT-0 note.",
        ),
    )


def _scan_prose_fn() -> Callable[[str], list[Any]]:
    return cast(
        "Callable[[str], list[Any]]",
        _guard_attr(
            "scan_stale_emptiness_prose",
            "Build `scan_stale_emptiness_prose(source: str) -> list[ProseFinding]`: for each slice "
            "fn that IS folded-or-standalone AND emits >=1 statement, flag it if its docstring or "
            "leading comment block contains any phrase in KNOWN_EMPTINESS_PHRASES (case-insensitive). "
            "This is the BEST-EFFORT prose backstop, a KNOWN BOUND — a novel phrasing evades it.",
        ),
    )


def _derive_slice_fns_fn() -> Callable[[str], set[str]]:
    return cast(
        "Callable[[str], set[str]]",
        _guard_attr(
            "derive_slice_fns",
            "Build `derive_slice_fns(source: str) -> set[str]`: the BY-NAME derivation — every "
            "top-level `def` whose name matches `^_[a-z0-9_]+_statements$`.",
        ),
    )


def _derive_statement_emitters_fn() -> Callable[[str], set[str]]:
    return cast(
        "Callable[[str], set[str]]",
        _guard_attr(
            "derive_statement_emitters",
            "Build `derive_statement_emitters(source: str) -> set[str]`: the INDEPENDENT BY-SHAPE "
            "oracle for the INSTRUMENT-0 reach cross-check — every top-level PRIVATE (`_`-prefixed) "
            "`def` annotated `-> list[str]`. Must NOT reuse derive_slice_fns' name predicate.",
        ),
    )


def _derive_folded_fn() -> Callable[[str], set[str]]:
    return cast(
        "Callable[[str], set[str]]",
        _guard_attr(
            "derive_folded_slices",
            "Build `derive_folded_slices(source: str) -> set[str]`: slice-fn names appearing as a "
            "call in the body of the top-level `generate_ddl`.",
        ),
    )


def _derive_standalone_fn() -> Callable[[str], dict[str, set[str]]]:
    return cast(
        "Callable[[str], dict[str, set[str]]]",
        _guard_attr(
            "derive_standalone_slices",
            "Build `derive_standalone_slices(source: str) -> dict[str, set[str]]`: each slice-fn "
            "name called in SOME top-level `generate_*_ddl` OTHER than `generate_ddl`, mapped to "
            "the set of `generate_*_ddl` names that call it (the evidence).",
        ),
    )


def _known_emptiness_phrases() -> frozenset[str]:
    return cast(
        "frozenset[str]",
        _guard_attr(
            "KNOWN_EMPTINESS_PHRASES",
            "Build `KNOWN_EMPTINESS_PHRASES: frozenset[str]` — the CLOSED set of known "
            "stale-emptiness phrasings the prose backstop matches (case-insensitive), e.g. "
            "'emit []', 'emits nothing', 'RED STUB', 'NOT folded', 'do not implement', "
            "'raises notimplementederror'. Pinned as a KNOWN BOUND.",
        ),
    )


def _reach_error_type() -> type[BaseException]:
    return cast(
        "type[BaseException]",
        _guard_attr(
            "SchemaGuardReachError",
            "Build `SchemaGuardReachError(Exception)` — raised by scan_schema_fold_coverage when "
            "the slice-fn set is empty (fail-closed) or when the name-set and shape-set diverge "
            "(INSTRUMENT-0 reach cross-check).",
        ),
    )


# --------------------------------------------------------------------------- #
# Synthetic-module source builders. Each returns a self-contained module SOURCE
# STRING (never imported — the scan is source-based). A "slice" is a private
# `-> list[str]` def named `_*_statements`; a `generate_ddl` / `generate_*_ddl`
# folds slices by CALLING them.
# --------------------------------------------------------------------------- #

_HELPERS = (
    "def _define_table(name: str) -> str:\n"
    '    return f"DEFINE TABLE {name}"\n\n\n'
)


def _slice_src(name: str, *, emits: bool, prose: str = "") -> str:
    """A single slice fn in the LITERAL-return idiom. ``emits`` False => the RED-STUB
    shape ``return []`` (the exact wording #398/#399 shipped)."""
    doc = f'    """{prose}"""\n' if prose else ""
    body = '    return [_define_table("x")]\n' if emits else "    return []\n"
    return f"def {name}() -> list[str]:\n{doc}{body}\n\n"


def _var_slice_src(name: str, *, prose: str = "") -> str:
    """An EMITTING slice fn in the house VARIABLE-return idiom (`statements = [...]; ... ;
    return statements`) — the shape 20 of the 28 REAL slices use (`_trace`, `_chunk`, …).

    This exists because a wrong `_emits` that recognizes ONLY a literal-list return would
    classify every real variable-returning slice as NOT emitting, blinding the fold-coverage
    leg to 20/28 slices while passing a literal-only contract. The pins that consume this
    fixture make that wrong build RED. (There is deliberately NO empty variable-returner
    fixture: the conservative rule exempts ONLY a literal `return []`, so an empty
    `statements = []; return statements` is treated as emitting — an over-flag in the SAFE
    direction that the contract must not forbid.)"""
    doc = f'    """{prose}"""\n' if prose else ""
    body = (
        "    statements: list[str] = [_define_table(\"x\")]\n"
        "    statements.append(_define_table(\"y\"))\n"
        "    return statements\n"
    )
    return f"def {name}() -> list[str]:\n{doc}{body}\n\n"


def _emitter_src(name: str) -> str:
    """A statement-emitter with the SHAPE of a slice (private, ``-> list[str]``)
    but NOT the ``_*_statements`` NAME — the INSTRUMENT-0 reach adversary."""
    return f'def {name}() -> list[str]:\n    return [_define_table("x")]\n\n\n'


def _nesting_slice_src(name: str, child: str) -> str:
    """An EMITTING slice fn that FOLDS a nested child slice — the packet-63a
    ``_memory_statements`` → ``_governed_index_statements`` shape (design §4.1): a top-level
    ``_*_statements`` slice calls ANOTHER top-level ``_*_statements`` slice. The child's
    statements run wherever the parent runs, so coverage must follow the call TRANSITIVELY."""
    return (
        f"def {name}() -> list[str]:\n"
        f'    statements: list[str] = [_define_table("x")]\n'
        f"    statements += {child}()\n"
        f"    return statements\n\n\n"
    )


def _generate_ddl_src(*folds: str) -> str:
    lines = "    statements: list[str] = []\n"
    for fn in folds:
        lines += f"    statements += {fn}()\n"
    lines += '    return ";".join(statements)\n'
    return f"def generate_ddl(*, dim: int, analyzer_name: str = 'a') -> str:\n{lines}\n\n"


def _generate_named_ddl_src(gen_name: str, *calls: str) -> str:
    lines = "    statements: list[str] = []\n"
    for fn in calls:
        lines += f"    statements += {fn}()\n"
    lines += '    return ";".join(statements)\n'
    return f"def {gen_name}() -> str:\n{lines}\n\n"


def _module(*parts: str) -> str:
    return _HELPERS + "".join(parts)


# =============================================================================== #
# 1. THE INVARIANT ON THE REAL SCHEMA — GREEN post-build (the gate itself).
# =============================================================================== #
class TestFoldCoverageOnRealSchema:
    """The invariant is GREEN on the cleaned tree at HEAD (stale comments retired in
    efccdc8/3077d23) — then it GUARDS the audit slice and every future schema-slice wave."""

    def test_the_real_schema_has_zero_fold_coverage_findings(self) -> None:
        findings = _scan_fold_fn()(_SUBJECT_SOURCE)
        assert findings == [], (
            "surreal_schema.py at HEAD must have ZERO fold-coverage findings — every "
            "statement-emitting `_*_statements` slice is either folded into generate_ddl "
            f"or consumed by a standalone generate_*_ddl. Got: {findings!r}"
        )

    def test_the_real_schema_has_zero_stale_prose_findings(self) -> None:
        findings = _scan_prose_fn()(_SUBJECT_SOURCE)
        assert findings == [], (
            "surreal_schema.py at HEAD must carry NO stale-emptiness prose on any "
            f"folded/standalone slice (#398/#399 were retired). Got: {findings!r}"
        )

    def test_the_derived_slice_fn_set_is_nonempty(self) -> None:
        # Fail-closed floor: a blind scan that derives NOTHING must never masquerade as clean.
        assert len(_derive_slice_fns_fn()(_SUBJECT_SOURCE)) >= 1

    def test_name_and_shape_derivations_agree_on_the_real_schema(self) -> None:
        # INSTRUMENT-0 positive control: the two INDEPENDENT reach derivations must
        # coincide on the real module (measured 28 == 28 at f87e774).
        by_name = _derive_slice_fns_fn()(_SUBJECT_SOURCE)
        by_shape = _derive_statement_emitters_fn()(_SUBJECT_SOURCE)
        assert by_name == by_shape, (
            "the by-name (`_*_statements`) and by-shape (private `-> list[str]`) slice-fn "
            f"derivations diverge on the real schema — name-only={sorted(by_name - by_shape)}, "
            f"shape-only={sorted(by_shape - by_name)}"
        )

    def test_every_folded_and_standalone_name_is_a_real_slice_fn(self) -> None:
        # The folded/standalone sets are drawn from real slice fns, not phantoms.
        slices = _derive_slice_fns_fn()(_SUBJECT_SOURCE)
        folded = _derive_folded_fn()(_SUBJECT_SOURCE)
        standalone = set(_derive_standalone_fn()(_SUBJECT_SOURCE))
        assert folded <= slices
        assert standalone <= slices
        # Every slice is accounted for (this is the invariant, stated as a set relation).
        assert slices <= (folded | standalone)


# =============================================================================== #
# 2. THE STRUCTURAL LEG DISCRIMINATES — synthetic fixtures (what WRONG build passes?).
# =============================================================================== #
class TestFoldCoverageStructuralDiscrimination:
    """Each fixture asks: what wrong build would this still pass? The unfolded-nonempty
    case is the #398 defect in miniature; the empty-stub case is the RED-phase legitimacy
    the gate must NOT break."""

    def test_an_unfolded_nonempty_slice_is_flagged(self) -> None:
        # THE core defect: a slice emits statements but is folded nowhere.
        src = _module(
            _slice_src("_orphan_statements", emits=True),
            _generate_ddl_src(),  # folds NOTHING
        )
        findings = _scan_fold_fn()(src)
        flagged = {getattr(f, "slice_fn", None) for f in findings}
        assert "_orphan_statements" in flagged, (
            f"an emitting slice folded nowhere must be flagged; got {findings!r}"
        )

    def test_an_unfolded_variable_returning_slice_is_flagged(self) -> None:
        # THE adversary blocker (RG-A): 20/28 real slices use `statements = [...]; return
        # statements`. A wrong `_emits` that recognizes only a literal-list return would treat
        # this as NOT emitting and NEVER flag it — so an un-folded variable-returning slice
        # would EVADE the primary defense. This pin REDS that wrong build.
        src = _module(
            _var_slice_src("_varorphan_statements"),
            _generate_ddl_src(),  # folds NOTHING
        )
        findings = _scan_fold_fn()(src)
        flagged = {getattr(f, "slice_fn", None) for f in findings}
        assert "_varorphan_statements" in flagged, (
            "an EMITTING variable-returning slice (the house `return statements` idiom) folded "
            f"nowhere MUST be flagged — a literal-only `_emits` is blind to it; got {findings!r}"
        )

    def test_a_folded_slice_is_not_flagged(self) -> None:
        src = _module(
            _slice_src("_folded_statements", emits=True),
            _generate_ddl_src("_folded_statements"),
        )
        assert _scan_fold_fn()(src) == []

    def test_a_folded_variable_returning_slice_is_not_flagged(self) -> None:
        # Negative control for the pin above: recognizing the variable idiom as emitting must
        # not degrade into "always flag" — a FOLDED variable-returner is clean.
        src = _module(
            _var_slice_src("_varfolded_statements"),
            _generate_ddl_src("_varfolded_statements"),
        )
        assert _scan_fold_fn()(src) == []

    def test_a_standalone_slice_consumed_by_a_generate_ddl_is_not_flagged(self) -> None:
        # (b): consumed by a generate_*_ddl other than generate_ddl.
        src = _module(
            _slice_src("_side_statements", emits=True),
            _generate_ddl_src(),  # NOT folded into the global generator …
            _generate_named_ddl_src("generate_side_ddl", "_side_statements"),  # … but standalone
        )
        assert _scan_fold_fn()(src) == []

    def test_a_nested_slice_folded_via_a_folded_parent_is_not_flagged(self) -> None:
        # packet 63a (finding #452): the `_memory_statements` → `_governed_index_statements`
        # shape. A `_*_statements` slice folded into generate_ddl may itself CALL another
        # `_*_statements` slice; the child's statements DO run (via the parent), so it is
        # COVERED transitively. A DIRECT-only coverage check false-flags the child as dead DDL.
        src = _module(
            _slice_src("_child_statements", emits=True),
            _nesting_slice_src("_parent_statements", "_child_statements"),
            _generate_ddl_src("_parent_statements"),  # parent folded; child nested inside parent
        )
        assert _scan_fold_fn()(src) == [], (
            "a nested slice folded via a FOLDED parent (the 63a `_governed_index_statements` "
            f"shape) must be recognized as covered, not flagged; got {_scan_fold_fn()(src)!r}"
        )

    def test_a_nested_slice_whose_parent_is_unfolded_is_flagged(self) -> None:
        # THE rooted-ness discriminator: transitive coverage must be REACHABLE FROM an entry
        # point, NOT merely "called by some slice". A child called ONLY by an UNFOLDED parent has
        # statements that never run -> BOTH must be flagged. A wrong build that treats "called by
        # any slice" as covered (an unrooted closure) would false-CLEAR the child and pass —
        # this pin REDS that wrong build, keeping the transitive broadening in the SAFE direction.
        src = _module(
            _slice_src("_lonelychild_statements", emits=True),
            _nesting_slice_src("_deadparent_statements", "_lonelychild_statements"),
            _generate_ddl_src(),  # NOTHING folded -> parent unreachable -> child unreachable
        )
        flagged = {getattr(f, "slice_fn", None) for f in _scan_fold_fn()(src)}
        assert flagged == {"_deadparent_statements", "_lonelychild_statements"}, (
            "a nested child reachable only through an UNFOLDED parent must be flagged (its "
            f"statements never run) — the transitive closure must be ROOTED; got {flagged!r}"
        )

    def test_a_genuinely_empty_stub_is_exempt(self) -> None:
        # RED-phase legitimacy: a `return []` stub that is not yet folded must NOT red the
        # gate — the gate fires at GREEN time (emits statements + unfolded), never at RED time.
        src = _module(
            _slice_src("_stub_statements", emits=False),  # return []
            _generate_ddl_src(),  # unfolded
        )
        assert _scan_fold_fn()(src) == [], (
            "a genuinely-empty (`return []`) unfolded stub is a legitimate RED-phase state "
            "and must be EXEMPT from the fold-coverage gate"
        )

    def test_a_folded_slice_that_becomes_a_stub_is_still_clean(self) -> None:
        # An empty slice that IS folded is harmless (folding [] is a no-op) — no finding.
        src = _module(
            _slice_src("_empty_statements", emits=False),
            _generate_ddl_src("_empty_statements"),
        )
        assert _scan_fold_fn()(src) == []

    def test_the_finding_names_the_offending_slice_and_its_reason(self) -> None:
        src = _module(
            _slice_src("_orphan_statements", emits=True),
            _generate_ddl_src(),
        )
        findings = _scan_fold_fn()(src)
        assert len(findings) == 1
        message = str(findings[0])
        assert "_orphan_statements" in message
        # #401 test-env-fiction: substring membership, never startswith / exact-line.
        assert "generate_ddl" in message


# =============================================================================== #
# 3. MUTATION PROOFS ON THE REAL SOURCE (safely, on a modified COPY string).
#    §Fork J: "remove a slice fn's generate_ddl call -> the fold-coverage pin reds".
# =============================================================================== #
class TestFoldCoverageMutationProofsOnRealSource:
    """The strongest discrimination: the ACTUAL module minus ONE real fold call reds the
    scan, and the unmodified source is the positive control. No real file is touched — the
    mutation is applied to a source-string copy."""

    def test_removing_a_real_fold_call_reds_the_scan(self) -> None:
        # Positive control: the unmodified real source is clean.
        assert _scan_fold_fn()(_SUBJECT_SOURCE) == []
        # Mutation: drop `_keep_statements`'s fold from generate_ddl. `_keep_statements`
        # is NOT consumed by generate_keep_ddl-only … it IS (generate_keep_ddl), so pick a
        # slice whose ONLY application is the fold: `_finding_counter_statements` is folded
        # AND standalone (generate_finding_ddl), so it would stay clean. Use a fold-ONLY
        # slice — `_snapshot_statements` (folded into generate_ddl, consumed by NO
        # standalone generate_*_ddl). Removing its fold makes it orphaned.
        assert "statements += _snapshot_statements()" in _SUBJECT_SOURCE, (
            "fixture assumption stale: `_snapshot_statements` is no longer folded into "
            "generate_ddl by that exact call spelling — re-derive the fold-only slice"
        )
        mutated = _SUBJECT_SOURCE.replace("    statements += _snapshot_statements()\n", "", 1)
        findings = _scan_fold_fn()(mutated)
        flagged = {getattr(f, "slice_fn", None) for f in findings}
        assert "_snapshot_statements" in flagged, (
            "dropping `_snapshot_statements`'s ONLY application (its generate_ddl fold) must "
            f"red the fold-coverage scan; got {findings!r}"
        )

    def test_a_fold_only_slice_is_not_also_standalone(self) -> None:
        # Guards the mutation above: `_snapshot_statements` must have NO standalone consumer,
        # or removing its fold would leave it clean and the mutation proof would be vacuous.
        standalone = _derive_standalone_fn()(_SUBJECT_SOURCE)
        assert "_snapshot_statements" not in standalone, (
            "the mutation proof needs a FOLD-ONLY slice; `_snapshot_statements` gained a "
            "standalone generate_*_ddl consumer — pick another fold-only slice"
        )

    def test_removing_a_real_variable_returning_fold_call_reds_the_scan(self) -> None:
        # §RG-A on the REAL module: `_trace_statements` is a VARIABLE-returning
        # (`statements = [...]; return statements`) FOLD-ONLY slice — the idiom `_snapshot`
        # (a literal returner) does NOT exercise. Dropping its fold must red the scan; a
        # literal-only `_emits` would leave it clean here (blind to 20/28 real slices).
        assert _scan_fold_fn()(_SUBJECT_SOURCE) == []  # positive control
        assert "statements += _trace_statements()" in _SUBJECT_SOURCE, (
            "fixture stale: `_trace_statements` is no longer folded by that exact spelling"
        )
        mutated = _SUBJECT_SOURCE.replace("    statements += _trace_statements()\n", "", 1)
        flagged = {getattr(f, "slice_fn", None) for f in _scan_fold_fn()(mutated)}
        assert "_trace_statements" in flagged, (
            "dropping the fold of the VARIABLE-returning `_trace_statements` must red the "
            "fold-coverage scan — proving `_emits` handles the house `return statements` idiom"
        )

    def test_the_variable_returner_mutation_target_is_fold_only(self) -> None:
        standalone = _derive_standalone_fn()(_SUBJECT_SOURCE)
        assert "_trace_statements" not in standalone, (
            "the variable-returner mutation proof needs a FOLD-ONLY slice; `_trace_statements` "
            "gained a standalone generate_*_ddl consumer — pick another fold-only variable returner"
        )

    def test_reintroducing_stale_prose_on_a_real_folded_slice_reds_the_prose_scan(self) -> None:
        # §Fork J RIDER, prose leg verbatim: "reintroduce an 'emits nothing' comment above a
        # folded slice -> the prose pin reds; restore -> green." Applied to the ACTUAL module
        # (`_keep_statements`, a real folded emitting slice) on a source-string COPY.
        assert _scan_prose_fn()(_SUBJECT_SOURCE) == []  # positive control: clean at HEAD
        anchor = "def _keep_statements() -> list[str]:"
        assert anchor in _SUBJECT_SOURCE, "fixture stale: `_keep_statements` def spelling moved"
        mutated = _SUBJECT_SOURCE.replace(
            anchor, "# ⚠ RED STUB: this slice emits nothing today.\n" + anchor, 1
        )
        findings = _scan_prose_fn()(mutated)
        flagged = {getattr(f, "slice_fn", None) for f in findings}
        assert "_keep_statements" in flagged, (
            "a reintroduced stale-emptiness comment above the folded `_keep_statements` must "
            f"red the prose scan (#398/#399 recurrence); got {findings!r}"
        )


# =============================================================================== #
# 4. INSTRUMENT-0 — the guard's OWN reach is a CHECKED VARIABLE (the P1c REACH ATTACK).
# =============================================================================== #
class TestGuardReachIsACheckedVariable:
    """The load-bearing anti-reach-defeat pins: a rename of the `_*_statements` convention
    must RED the guard, not silently exempt the renamed fns."""

    def test_a_misnamed_emitter_fails_the_scan_closed(self) -> None:
        # A statement-emitter with the slice SHAPE (`-> list[str]`, private) but NOT the
        # `_*_statements` NAME, folded nowhere. The by-name set misses it; the by-shape set
        # sees it; the divergence must FAIL CLOSED — not return a falsely-clean [].
        src = _module(
            _emitter_src("_orphan_ddl_parts"),  # shape of a slice, wrong name
            _generate_ddl_src(),
        )
        import pytest  # noqa: PLC0415

        with pytest.raises(_reach_error_type()):
            _scan_fold_fn()(src)

    def test_a_wholesale_convention_rename_fails_the_scan_closed(self) -> None:
        # No `_*_statements` at all, but real emitters exist -> derive_slice_fns is empty ->
        # a blind scan would return [] (falsely clean). It must fail closed instead.
        src = _module(
            _emitter_src("_alpha_ddl_parts"),
            _emitter_src("_beta_ddl_parts"),
            _generate_ddl_src(),
        )
        import pytest  # noqa: PLC0415

        with pytest.raises(_reach_error_type()):
            _scan_fold_fn()(src)

    def test_name_and_shape_derivations_are_independent(self) -> None:
        # The shape oracle must NOT be an alias of the name predicate: on a module whose
        # emitter is misnamed, the two derivations MUST differ (else the cross-check is
        # `derived == derived` theatre).
        src = _module(
            _emitter_src("_orphan_ddl_parts"),
            _slice_src("_kept_statements", emits=True),
            _generate_ddl_src("_kept_statements"),
        )
        by_name = _derive_slice_fns_fn()(src)
        by_shape = _derive_statement_emitters_fn()(src)
        assert by_name == {"_kept_statements"}
        assert "_orphan_ddl_parts" in by_shape
        assert by_name != by_shape

    def test_the_scan_is_rederived_per_call_not_cached(self) -> None:
        # A clean module then a dirty module through the SAME scan callable must give
        # DIFFERENT results — proving the slice-fn set is re-derived per call, never cached.
        clean = _module(
            _slice_src("_a_statements", emits=True),
            _generate_ddl_src("_a_statements"),
        )
        dirty = _module(
            _slice_src("_a_statements", emits=True),
            _generate_ddl_src(),  # unfolded
        )
        scan = _scan_fold_fn()
        assert scan(clean) == []
        assert {getattr(f, "slice_fn", None) for f in scan(dirty)} == {"_a_statements"}

    def test_a_rename_dropping_the_annotation_evades_both_is_a_known_bound(self) -> None:
        # PIN THE MISS (§"WHEN YOU CANNOT CLOSE A HOLE"): a slice renamed off `_*_statements`
        # AND stripped of its `-> list[str]` annotation escapes BOTH derivations. This test
        # ASSERTS the accepted bound so it cannot be silently "fixed" or inherited.
        # RE-OPEN TRIGGER: a schema slice found in the wild with neither the name nor the
        # annotation -> add a third derivation (e.g. "returns a list built from _define_*").
        src = (
            _HELPERS
            + "def _orphan(x=0):\n    return [_define_table('x')]\n\n\n"  # no name, no annotation
            + _generate_ddl_src()
        )
        by_name = _derive_slice_fns_fn()(src)
        by_shape = _derive_statement_emitters_fn()(src)
        assert "_orphan" not in by_name
        assert "_orphan" not in by_shape, (
            "KNOWN BOUND CHANGED: the by-shape oracle now catches an annotation-less emitter. "
            "If this was deliberate, delete this pin and record the strengthened derivation."
        )


# =============================================================================== #
# 5. THE PROSE BACKSTOP — discriminates, and is a KNOWN BOUND (allowlist-the-safe).
# =============================================================================== #
class TestStandaloneExemptionIsAKnownBound:
    """§"WHEN YOU CANNOT CLOSE A HOLE, PIN IT" (adversary SECONDARY). Membership (b) exempts a
    slice consumed by SOME `generate_*_ddl`. But the single-module scan cannot see whether that
    `generate_*_ddl` is ITSELF live (consumed by a store's `ensure_ready`). A slice consumed
    ONLY by a DEAD generate entry point is over-exempted — the exemption assumes generate_*_ddl
    entry points are live. Verified false-at-HEAD (every generate_*_ddl is wired — see
    REPORT-contract-61a-w3.md §"Standalone allowlist"); pinned here so it is met deliberately.
    RE-OPEN TRIGGER: a `generate_*_ddl` found unconsumed by any store `ensure_ready` -> add a
    whole-tree reachability check (a generate entry point must be called by some ensure_ready)."""

    def test_a_slice_consumed_only_by_a_generate_ddl_is_exempt_regardless_of_that_generate_being_wired(
        self,
    ) -> None:
        # `generate_lonely_ddl` calls the slice but nothing (no store) calls generate_lonely_ddl.
        # The single-module scan exempts the slice anyway — the accepted over-exemption.
        src = _module(
            _var_slice_src("_lonely_statements"),
            _generate_ddl_src(),  # not folded into the global generator …
            _generate_named_ddl_src("generate_lonely_ddl", "_lonely_statements"),  # … only a
            # possibly-dead standalone entry point calls it.
        )
        assert _scan_fold_fn()(src) == [], (
            "ACCEPTED KNOWN BOUND: a slice consumed by a generate_*_ddl is exempt even if that "
            "generate_*_ddl is dead. The scan is single-module and cannot verify ensure_ready "
            "wiring. RE-OPEN TRIGGER: a generate_*_ddl found unconsumed by any store -> close it "
            "with a whole-tree reachability check. If you closed this deliberately, delete this pin."
        )


class TestStaleEmptinessProseBackstop:
    """The prose leg only adds cover for an 'emit []' comment on an ALREADY-folded slice —
    the structural leg cannot see that lie (the statements DO run)."""

    def test_a_folded_slice_with_a_stale_emptiness_docstring_is_flagged(self) -> None:
        phrase = next(iter(_known_emptiness_phrases()))
        src = _module(
            _slice_src("_lying_statements", emits=True, prose=f"This slice {phrase} today."),
            _generate_ddl_src("_lying_statements"),  # folded -> structural leg is clean
        )
        findings = _scan_prose_fn()(src)
        flagged = {getattr(f, "slice_fn", None) for f in findings}
        assert "_lying_statements" in flagged, (
            f"a folded emitting slice whose docstring says {phrase!r} must be flagged by the "
            f"prose backstop; got {findings!r}"
        )

    def test_a_folded_slice_with_honest_prose_is_not_flagged(self) -> None:
        src = _module(
            _slice_src(
                "_honest_statements",
                emits=True,
                prose="Emits the table, its fields and the UNIQUE index.",
            ),
            _generate_ddl_src("_honest_statements"),
        )
        assert _scan_prose_fn()(src) == []

    def test_an_empty_stub_with_truthful_emptiness_prose_is_not_flagged(self) -> None:
        # A RED-phase stub whose prose HONESTLY says it emits [] is TRUE prose, not a lie —
        # the prose leg targets a MISMATCH (emits >=1 but claims empty), not the phrase alone.
        phrase = next(iter(_known_emptiness_phrases()))
        src = _module(
            _slice_src("_truthful_stub_statements", emits=False, prose=f"Currently {phrase}."),
            _generate_ddl_src(),
        )
        assert _scan_prose_fn()(src) == [], (
            "the prose leg must flag a MISMATCH (emitting body + emptiness claim), not an "
            "honest emptiness claim on a genuinely-empty stub"
        )

    def test_known_emptiness_phrases_covers_the_398_399_wording(self) -> None:
        # The set must at least catch the wordings #398/#399 actually shipped.
        phrases_lower = {p.lower() for p in _known_emptiness_phrases()}
        blob = " ".join(phrases_lower)
        for shipped in ("red stub", "not folded", "emit"):
            assert shipped in blob, (
                f"KNOWN_EMPTINESS_PHRASES omits the shipped #398/#399 wording {shipped!r}"
            )


class TestStaleEmptinessProseIsAKnownBound:
    """§"WHEN YOU CANNOT CLOSE A HOLE, PIN IT" — the prose leg is enumerate-the-forbidden by
    nature; a NOVEL phrasing evades it. This ASSERTS the accepted bound with its re-open
    trigger so it is met deliberately, never silently inherited or silently 'fixed'."""

    def test_a_novel_emptiness_phrasing_evades_the_prose_backstop(self) -> None:
        # A folded emitting slice whose docstring asserts emptiness in words NOT in the
        # known set. The structural leg is clean (it is folded); the prose leg MISSES it.
        novel = "This routine contributes no schema whatsoever to the store."
        assert not any(
            p.lower() in novel.lower() for p in _known_emptiness_phrases()
        ), "fixture stale: the 'novel' phrasing overlaps a known phrase — pick a fresher lie"
        src = _module(
            _slice_src("_novel_lie_statements", emits=True, prose=novel),
            _generate_ddl_src("_novel_lie_statements"),
        )
        findings = _scan_prose_fn()(src)
        assert findings == [], (
            "ACCEPTED KNOWN BOUND (#398/#399, §Fork J): the prose backstop is best-effort over "
            "KNOWN_EMPTINESS_PHRASES and a novel phrasing evades it. The STRUCTURAL leg is the "
            "real defense. RE-OPEN TRIGGER: a new prose-evasion found in the wild -> widen "
            "KNOWN_EMPTINESS_PHRASES OR strengthen the structural check. If you closed this hole "
            f"deliberately, delete this pin and say so. Got: {findings!r}"
        )
