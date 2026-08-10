"""Contract (F4 / defect-class prevention) — the shared AST-∀-scan reach helpers.

Session ``2026-08-09-fix-344-345``; design doc
``docs/plans/v2/design/2026-08-09-defect-class-prevention.md`` §3 INSTRUMENT A-SUB.
Author: ``contract-asub-b`` (Opus CONTRACT author — tests only, no production code).

THE CLASS THIS PINS (design §1)
-------------------------------
*A guard certifies only the sites it EXECUTES, and its REACH is a hidden constant
instead of a checked variable, so un-reached sites are exempt silently and forever.*

The ∀-scan family (``test_anchored_pattern_seam`` #210, ``test_backoff_seam``,
``test_secret_typing``, ``test_secret_leak_vectors``, and the two new #345 scans) each
re-hand-rolls TWO pieces of reach machinery:

* the **tree parser** — ``for root in ROOTS: for p in root.rglob("*.py"):
  trees[rel] = ast.parse(p.read_text())`` (duplicated verbatim in ≥14 files, e.g.
  ``test_anchored_pattern_seam._parse_production_trees``), and
* the **coverage assertion** — ``scanned_packages == declared_members`` re-written per
  scan (``test_anchored_pattern_seam.TestScanCoverage.
  test_the_scan_reaches_every_production_tree``).

That is the ONE-IMPLEMENTATION defect one level up (CLAUDE.md, lore #102): if the parse
or the coverage rule must change, it must be found in N files. F4's fix: ONE shared
LIBRARY of helpers in ``_logging_fixtures.py`` (already the shared test-support home —
``workspace_roots`` / ``production_sources`` live there), imported by every ∀-scan file:

* :func:`parse_production_trees` — the ONE tree parser, roots from ``workspace_roots``,
  keyed by repo-relative posix path.
* :func:`assert_scan_reached_every_member` — the ONE coverage assertion; oracle =
  declared members read INDEPENDENTLY from ``pyproject.toml`` (never ``derived ==
  derived``), FAIL-CLOSED on an empty derivation.

RED-vs-collection discipline (the ``test_link5_render_containment`` idiom): neither symbol
exists at HEAD (``641f758``). A top-level ``from _logging_fixtures import
parse_production_trees`` would be a COLLECTION error, not a behavioural RED — so both are
reached only through the lazy :func:`_parse_production_trees_fn` /
:func:`_assert_reached_fn` accessors below, which turn "the helper is absent" into a
clean, NAMED assertion failure at RUN time. Every other pin then still collects and runs,
so the discriminating controls are visible.

⚠ Present-tense dating: every "RED at HEAD" / "does not exist" claim here is dated to
``641f758`` (the branch tip when this contract was authored). A reader retrieving this
after the build must re-derive.

MUTATION / PROVE-SHARING — §12 UN-DEFEATABLE-BY-SPELLING (fable-sidecar 2026-08-09)
-----------------------------------------------------------------------------------
"Change the shared derivation → every dependent pin reddens; a caller that stays green is
a private copy wearing the shared name." Two adversary passes proved every STATIC/proxy-keyed
sharing pin defeatable one spelling at a time. The FIRST (``REPORT-adversary-asub-b``, graded
``405d321``) waved through a FIX-NOTHING build (16/0) via UNUSED imports + private ``rglob``
clones. The reviser closed those; the DELTA pass (``REPORT-delta-adversary-asub-b``) then found
a SURVIVOR the fix could not reach: a **routing-not-sharing** build whose REAL scan derives
privately via ``production_sources()``+``ast.parse`` (NO ``rglob`` — the clone detector is
blind) doing the real 113-key work, plus an **UNCONSUMED nullary decoy** that merely CALLS
``parse_production_trees`` to satisfy used-ness and the ∀-reach. Every guard passed because each
was keyed on a PROXY — the ``rglob`` SPELLING, "a call EXISTS", "the import is used" — and the
open vocabularies (ways to spell a whole-tree parse; ways to fake consumption) are unbounded.

**§12's lift: stop inspecting the open-vocabulary artifact; observe the property at the
CHOKEPOINT where the vocabulary collapses to one.** Producing an ``ast.Module`` of source
REQUIRES the builtin ``compile`` (``ast.parse`` calls ``compile(src, name, mode,
PyCF_ONLY_AST)`` — VERIFIED this cycle on this Python, see :class:`_TheRoutingVerification`),
and there is no pure-Python way around it. So the sharing property is now pinned in THREE layers
— the exact two-layer shape ``test_retry_seam`` already ships (a weak-total LINT paired with an
absolute-over-executed-code RUNTIME gate), plus the fixed ∀-mutation:

* **LAYER 1 — RUNTIME chokepoint gate (the load-bearing, spelling-AND-alias-agnostic catch).**
  :class:`TestNoPrivateParseEscapesTheSanctionedParserAtRuntime` GENERALISES
  ``test_retry_seam``'s runtime-guard scaffold (``_sdk_guard.install`` /
  ``GuardReport.require_observations`` / its pos-neg controls / the plain-``def``-walks-at-CALL-
  time lesson) from the SDK-connection primitive to the ``builtins.compile`` primitive: any
  ``PyCF_ONLY_AST`` compile made from a workspace ``.py`` SITE with NO ``parse_production_trees``
  frame above it is an ESCAPE, named file:line. Aliasing, ``os.walk``, a comprehension, a direct
  ``compile`` — all die at once, because the check never looks at code. ``require_observations``
  (#136) refuses a clean verdict the guard saw NOTHING for.
* **LAYER 2 — AST lint, REFRAMED off the ``rglob`` spelling** →
  :class:`TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist` keys on the PARSE
  PRIMITIVE (``ast.parse`` / ``compile``) co-occurring with a file-read / whole-tree source,
  outside an evidence-backed SAFE allowlist. Weak-but-total backstop for code Layer 1 does not
  execute; HONESTLY alias-defeatable (that is Layer 1's job) — deny-by-default, allowlist-the-SAFE.
* **LAYER 3 — ∀-MUTATION SHARING proof, reach + assertion FIXED** —
  :class:`TestSharingProvenByMutation` drops the shared parser (``→ {}``) via
  ``_rebind_everywhere`` (BY-IDENTITY across ``sys.modules`` so a FROM-import adopter is reached
  — the single-module ``monkeypatch`` the adversary flagged does NOT) and asserts EACH adopter's
  OWN workspace-tree derivation REFLECTS the drop. Used-ness now binds to CONSUMPTION: the reach
  is the declared adopter set with Layer 1 as the completeness CHECKED VARIABLE (retiring the
  ``_live_adopters()=="calls the helper"`` call-existence proxy the decoy defeated). The decoy
  dies at every layer — Layer 1 escape on its private scan, Layer 2 flag, Layer 3 keys-unchanged.

The member hand-lists (:class:`TestTheMemberHandListsAreRetired`) and the used-ness pin
(:class:`TestTheMigrationSetRoutesThroughTheSharedHelpers`) are unchanged (adversary: SOUND).

⚠ HONEST BOUND (stated in the instrument, per §6 / retry_seam's own scope line): the runtime
gate is absolute only over code that EXECUTES. Code that never runs is Layer 2's weak-total job,
and the un-runnable tail is INSTRUMENT 0's standing reach-attack — NOT pretended closed. This is
why BOTH layers ship, exactly as the retry seam ships both.

How to run:
    uv run pytest loremaster/tests/test_ast_reach_helpers.py -n auto -q
"""

from __future__ import annotations

import ast
import importlib
import sys
import tomllib
import types
from collections.abc import Callable
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any, NamedTuple, cast

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TESTS_DIR = Path(__file__).resolve().parent

#: The ∀-scan files F4 migrates onto the shared helpers (design §5 Wave-1 A-SUB writable
#: set). The sharing pin is scoped to exactly these — the substrate serves the ∀-scan
#: FAMILY, not every ``rglob`` file in the tree (design §3 A-SUB bound: some files parse
#: for unrelated reasons; migrating those is a flagged worklist item, out of scope).
#:
#: ⚠ ``test_comms_footer.py`` ADDED 2026-08-09 (design §10 Ruling 6, fable-designer-2):
#: ruled a ``parse_production_trees`` adopter with TWO whole-tree scans, and moved into the
#: A-SUB writable set (correcting §5's clerical omission). Its per-scan behaviour-preservation
#: + granularity + narrowing-escalation pins live in
#: :class:`TestCommsFooterScansMigrateBehaviourPreserving` /
#: :class:`TestBothCommsFooterScansMigrateWithTheirModes` below.
_MIGRATION_SET: tuple[str, ...] = (
    "test_anchored_pattern_seam.py",
    "test_backoff_seam.py",
    "test_secret_typing.py",
    "test_secret_leak_vectors.py",
    "test_comms_footer.py",
)


# ---------------------------------------------------------------------------- #
# LAZY ACCESSORS — the two symbols A-SUB mints in ``_logging_fixtures``. Reached
# through these so a HEAD run fails BEHAVIOURALLY (named, at run time), never as a
# collection error that would hide every discriminating control below.
# ---------------------------------------------------------------------------- #


def _parse_production_trees_fn() -> Callable[..., dict[str, ast.Module]]:
    import _logging_fixtures  # noqa: PLC0415

    fn = getattr(_logging_fixtures, "parse_production_trees", None)
    assert fn is not None, (
        "F4 (A-SUB): `_logging_fixtures.parse_production_trees` is not extracted. The "
        "tree parser `for root in workspace_roots(...): for p in root.rglob('*.py'): "
        "trees[rel] = ast.parse(p.read_text())` is still hand-rolled per ∀-scan file "
        "(verbatim in test_anchored_pattern_seam._parse_production_trees and ≥13 others). "
        "Add ONE `parse_production_trees(*, include_scripts=True, include_skills=False) "
        "-> dict[str, ast.Module]` to _logging_fixtures, keyed by repo-relative posix path."
    )
    return cast("Callable[..., dict[str, ast.Module]]", fn)


def _assert_reached_fn() -> Callable[..., None]:
    import _logging_fixtures  # noqa: PLC0415

    fn = getattr(_logging_fixtures, "assert_scan_reached_every_member", None)
    assert fn is not None, (
        "F4 (A-SUB): `_logging_fixtures.assert_scan_reached_every_member` is not "
        "extracted. The coverage assertion `scanned_packages == declared_members` is "
        "re-written per ∀-scan (test_anchored_pattern_seam.TestScanCoverage). Add ONE "
        "`assert_scan_reached_every_member(scanned_trees, *, extra_roots=('scripts',)) "
        "-> None` that reads declared members INDEPENDENTLY from pyproject.toml (never "
        "derived==derived) and FAILS CLOSED on an empty derivation."
    )
    return cast("Callable[..., None]", fn)


def _install_parse_guard_fn() -> Callable[..., Any]:
    """LAYER 1 accessor — the RUNTIME parse-guard the builder GENERALISES from
    ``test_retry_seam``'s ``_sdk_guard`` scaffold (design §12.3 / §12.5 REUSE flag).

    Reached lazily (the ``_parse_production_trees_fn`` discipline) so a HEAD run fails
    BEHAVIOURALLY and NAMED, never as a collection error that would hide every control below.
    Tolerates the builder's home choice: it looks in ``_logging_fixtures`` (the shared
    test-support home) FIRST, then a dedicated ``_parse_guard`` module — either is acceptable;
    §12.5 flags the retry-seam runtime-guard as a shared POLICY with ≥2 users (SDK gate + parse
    gate), a candidate to extract into ONE parametrised ``(primitive, sanctioned-frame)`` scaffold
    proven by mutation (change the shared scaffold → BOTH gates redden), exactly like
    ``_rebind_everywhere``'s promotion. That extraction is the BUILDER's call; the contract only
    requires the parse-gate to EXIST with the API below.

    REQUIRED API — ``install_parse_guard(monkeypatch, *, watched_root=None, witness=None)
    -> report`` where ``report`` carries, mirroring ``_sdk_guard.GuardReport``:
      * ``report.armed: bool`` — False (never raising) iff ``parse_production_trees`` is not yet
        built, so the whole suite does not go red for a reason that teaches nothing (retry-seam's
        pre-driver posture); the contract's gate pins name the missing helper, the honest RED.
      * ``report.escapes: list`` — one entry per ``PyCF_ONLY_AST`` compile made from a workspace
        ``.py`` SITE with NO ``parse_production_trees`` frame above it, each with ``.site`` (a
        ``"<repo-rel>.py:<lineno> in <fn>()"`` string), ``.primitive`` ("ast.parse"/"compile"),
        and ``.member`` (§12.8.3 — the workspace MEMBER the compiled SOURCE belongs to, e.g.
        "loremaster"/"lorerunes"/"scripts", or "" if the source is not a workspace file). The
        skip-coverage pin (``test_no_skip_set_file_parses_the_tree_unrouted``) needs ``.member`` to
        tell a WHOLE-WORKSPACE enumeration (a site whose escapes span >=2 members) from a
        single-PACKAGE scan (>=2 files, ONE member — a §7 non-adopter that must NOT
        false-flag). RESOLVE IT FROM THE SOURCE, not the compile ``filename`` argument: offenders
        call ``ast.parse(path.read_text())`` with no filename, so ``filename`` is ``<unknown>`` —
        map the compiled source text to its member (e.g. a ``{source: member}`` map built at arm
        time over the workspace ``.py`` files). This is the small escape-record extension §12.8.3
        authorizes; it is measured-necessary (a raw compile-COUNT proxy false-flags the lorerunes
        single-package scans — REPORT-reviser-asub-6.md §satisfiability).
      * ``report.observed: set[str]`` — the SANCTIONED sites (a workspace parse routed THROUGH
        ``parse_production_trees``): Layer 3's reach is DERIVED from this, never a call-existence
        proxy.
      * ``report.intercepted: int`` — every ``PyCF_ONLY_AST`` compile it saw (its own reach).
      * ``report.require_observations(flow: str) -> None`` — RAISE (a ``GuardCannotSubstantiate``)
        if the guard saw ZERO sanctioned-or-escaping workspace parses while driving a flow that
        provably parses: "no escapes" having seen nothing is BLINDNESS wearing cleanliness (#136).

    ⚠ THE DISCRIMINATOR IS THE CALL SITE (the caller frame's ``co_filename``), NOT the compile's
    ``filename`` ARGUMENT — because offenders call ``ast.parse(path.read_text())`` with NO
    filename (default ``<unknown>``), so a filename-argument filter would MISS the survivor.
    VERIFIED in scratch this cycle (see REPORT-reviser-asub-3.md). This refines §12.2/§12.3's
    "a workspace .py filename" to the SITE, the only robust reading."""
    for module_name in ("_logging_fixtures", "_parse_guard"):
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue  # a home the builder did not choose — try the next, then fail NAMED
        fn = getattr(module, "install_parse_guard", None)
        if fn is not None:
            return cast("Callable[..., Any]", fn)
    raise AssertionError(
        "F4/§12 (A-SUB Layer 1): the RUNTIME parse-guard `install_parse_guard` is not extracted "
        "into `_logging_fixtures` (shared test-support home) or a `_parse_guard` module. GENERALISE "
        "`test_retry_seam._sdk_guard.install` from the SDK-connection primitive to `builtins.compile`: "
        "wrap it (a PLAIN `def`, so the stack walk happens at CALL time), record every PyCF_ONLY_AST "
        "compile made from a workspace `.py` SITE with no `parse_production_trees` frame above as an "
        "escape (file:line + primitive), carry `require_observations` anti-vacuity (#136), and arm "
        "`armed=False` (not raise) before `parse_production_trees` exists. This is the un-defeatable "
        "half A-SUB was missing (§12); the spelling-keyed LINT (Layer 2) alone let the survivor through."
    )


def _declared_members() -> set[str]:
    """The workspace members, read straight from ``pyproject.toml`` — the INDEPENDENT
    oracle (never the subject-under-test's own derivation)."""
    manifest = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return set(manifest["tool"]["uv"]["workspace"]["members"])


def _expected_keys_from_disk(*, include_scripts: bool, include_skills: bool) -> set[str]:
    """An INDEPENDENT re-derivation of what ``parse_production_trees`` must key on: every
    ``*.py`` under :func:`workspace_roots`, repo-relative posix. Built here (not imported
    from the subject) so the behaviour pin is not ``derived == derived``."""
    from _logging_fixtures import workspace_roots  # noqa: PLC0415

    keys: set[str] = set()
    for _label, root in workspace_roots(include_scripts=include_scripts, include_skills=include_skills):
        for path in root.rglob("*.py"):
            keys.add(path.relative_to(_REPO_ROOT).as_posix())
    return keys


# ---------------------------------------------------------------------------- #
# COMMS-FOOTER ADOPTER ORACLES (design §10 Ruling 6, fable-designer-2).
#
# ``test_comms_footer`` has TWO whole-tree scans that migrate onto
# ``parse_production_trees`` with DIFFERENT ``include_tests``. §8 Ruling 1 requires each
# adopter's POST-migration scanned FILE SET to equal its PRE-migration set EXACTLY. These
# oracles re-derive each pre-migration set INDEPENDENTLY from disk (never the subject's own
# loop — the migration DELETES those loops, and ``derived == derived`` sees no lost member).
# Every "N @ 641f758" count below is a MEASURED receipt (dated; re-derive if the layout moves).
# ---------------------------------------------------------------------------- #

#: The comms-footer adopter file — named once so the pins below cannot drift from it.
_COMMS_FOOTER = "test_comms_footer.py"


def _is_member_test_file(rel_posix: str) -> bool:
    """True iff ``rel_posix`` is a workspace-member TEST file — i.e. ``<member>/tests/…`` for a
    declared member. Members nest tests at ``<member>/tests`` (OUTSIDE the ``<member>/<member>``
    package root ``workspace_roots`` yields), so this is exactly the set ``include_tests`` toggles
    and the set Scan B's tuple accidentally over-reaches into."""
    parts = rel_posix.split("/")
    return len(parts) >= 2 and parts[0] in _declared_members() and parts[1] == "tests"


def _member_package_files() -> set[str]:
    """PROD-ONLY reach: every ``*.py`` under each ``<member>/<member>`` package root
    (``__pycache__`` excluded), repo-relative posix. This is what ``workspace_roots`` yields
    and therefore what ``parse_production_trees(include_tests=False)`` must key on — AND it is
    Scan B's DESIGN-INTENDED (§10 R6) prod-only reach. 90 files @ 641f758."""
    keys: set[str] = set()
    for member in _declared_members():
        for path in (_REPO_ROOT / member / member).rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            keys.add(path.relative_to(_REPO_ROOT).as_posix())
    return keys


def _member_test_files() -> set[str]:
    """Every ``*.py`` under each ``<member>/tests`` (``__pycache__`` excluded), repo-relative
    posix — the member-test files ``include_tests=True`` MUST RE-ADD, because ``workspace_roots``
    yields the ``<member>/<member>`` package root which structurally EXCLUDES them (§10 R6.3
    granularity hazard). 172 files @ 641f758."""
    keys: set[str] = set()
    for member in _declared_members():
        for path in (_REPO_ROOT / member / "tests").rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            keys.add(path.relative_to(_REPO_ROOT).as_posix())
    return keys


def _comms_footer_scan_a_pre_migration() -> set[str]:
    """Scan A's TRUE pre-migration reach — ``TestTheCharsetGuardDoesNotTeachAFalseRationale
    ._scan`` @ 641f758: ``for member in _workspace_scan_roots(root): (root/member).rglob("*.py")``.
    Each member DIR includes ``<member>/<member>`` AND ``<member>/tests`` (its docstring: "prod
    AND tests"). == member packages ∪ member tests. 262 files @ 641f758."""
    keys: set[str] = set()
    for member in _declared_members():
        for path in (_REPO_ROOT / member).rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            keys.add(path.relative_to(_REPO_ROOT).as_posix())
    return keys


def _comms_footer_scan_b_pre_migration() -> set[str]:
    """Scan B's TRUE pre-migration reach — ``TestNoCommsIdentityReachesQueryTEXT._scan`` @
    641f758: the HARDCODED tuple ``("loremaster/loremaster", "lorerunes", "loresigil",
    "lorescribe")`` × ``rglob("*.py")`` (``__pycache__`` excluded).

    ⚠ FROZEN historical reference (the migration deletes the tuple, so it is transcribed here,
    dated). ⚠ It is NOT prod-only, contradicting §10 R6's "PRODUCTION ONLY" characterization:
    ``loremaster`` is scanned via its PACKAGE root (prod only) but the 3 flat members via their
    MEMBER dir, so ``lorerunes/tests`` + ``loresigil/tests`` + ``lorescribe/tests`` LEAK IN.
    131 files @ 641f758 = 90 prod + 41 non-loremaster test files. See the DECISION-NEEDED in
    REPORT-reviser-asub-2.md."""
    keys: set[str] = set()
    for member in ("loremaster/loremaster", "lorerunes", "loresigil", "lorescribe"):
        for path in (_REPO_ROOT / member).rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            keys.add(path.relative_to(_REPO_ROOT).as_posix())
    return keys


def _parse_prod_trees_modes_in(source: str) -> list[object]:
    """Every ``parse_production_trees(...)`` call's ``include_tests`` value in ``source``, as an
    AST-derived list: the literal ``True``/``False`` where a constant is passed, the sentinel
    ``"DEFAULT"`` where the kwarg is omitted, ``"NON_LITERAL"`` where it is a non-constant. Used
    to prove BOTH comms-footer scans migrate, one in each mode (file-level; see the pin's bound)."""
    modes: list[object] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name != "parse_production_trees":
            continue
        mode: object = "DEFAULT"
        for keyword in node.keywords:
            if keyword.arg == "include_tests":
                mode = keyword.value.value if isinstance(keyword.value, ast.Constant) else "NON_LITERAL"
        modes.append(mode)
    return modes


# ---------------------------------------------------------------------------- #
# parse_production_trees — API + behaviour
# ---------------------------------------------------------------------------- #


class TestParseProductionTrees:
    """The ONE tree parser: a ``dict[str, ast.Module]`` keyed by repo-relative posix
    path, covering every workspace member's production tree."""

    def test_returns_a_dict_of_ast_modules_keyed_by_posix_path(self) -> None:
        trees = _parse_production_trees_fn()()
        assert isinstance(trees, dict) and trees, "parse_production_trees returned nothing"
        for key, module in trees.items():
            assert isinstance(key, str) and not key.startswith("/") and "\\" not in key, (
                f"key {key!r} is not a repo-relative posix path"
            )
            assert isinstance(module, ast.Module), f"{key!r} is not an ast.Module"

    def test_keys_are_exactly_the_python_files_under_the_workspace_roots(self) -> None:
        """Behaviour-preservation + non-vacuity: the parser's key set is EXACTLY the
        ``*.py`` files an independent rglob over ``workspace_roots`` finds. Pins the
        migration is behaviour-preserving (the removed-behaviour/dual rule) and that the
        parser did not silently parse a narrower tree than it claims."""
        trees = _parse_production_trees_fn()(include_scripts=True, include_skills=False)
        expected = _expected_keys_from_disk(include_scripts=True, include_skills=False)
        assert set(trees) == expected, (
            "parse_production_trees keys diverge from an independent rglob of the "
            "workspace roots — the shared parser is narrower/wider than the trees it "
            f"claims to parse.\n  parsed-not-expected: {sorted(set(trees) - expected)[:5]}\n"
            f"  expected-not-parsed: {sorted(expected - set(trees))[:5]}"
        )

    def test_covers_every_declared_workspace_member(self) -> None:
        """Reach: every DECLARED member (read independently from pyproject) has at least
        one parsed tree. A member silently absent is exempt from every ∀ scan built on
        this parser — the #251/lore lesson, one level up."""
        trees = _parse_production_trees_fn()(include_scripts=True, include_skills=False)
        parsed_packages = {key.split("/", 1)[0] for key in trees}
        missing = sorted(_declared_members() - parsed_packages)
        assert not missing, (
            f"declared workspace members with NO parsed tree: {missing} — the shared "
            "parser's reach is narrower than the workspace it claims to govern."
        )

    def test_the_include_scripts_toggle_is_honoured(self) -> None:
        """The toggle is a REAL switch, not documentation: ``scripts`` keys appear iff
        ``include_scripts=True``. A build that ignores the toggle (always includes, or
        never includes) fails one leg."""
        with_scripts = _parse_production_trees_fn()(include_scripts=True, include_skills=False)
        without_scripts = _parse_production_trees_fn()(include_scripts=False, include_skills=False)
        assert any(key.startswith("scripts/") for key in with_scripts), (
            "include_scripts=True produced no scripts/ tree"
        )
        assert not any(key.startswith("scripts/") for key in without_scripts), (
            "include_scripts=False still parsed scripts/ trees — the toggle is ignored"
        )


# ---------------------------------------------------------------------------- #
# assert_scan_reached_every_member — coverage as a CHECKED variable
# ---------------------------------------------------------------------------- #


class TestAssertScanReachedEveryMember:
    """The ONE coverage assertion. Its job is to make a scan's REACH a checked variable:
    ``scanned_packages == declared_members ∪ extra_roots``, FAIL-CLOSED on empty, with the
    oracle read INDEPENDENTLY of the subject."""

    def _real_scan(self) -> dict[str, ast.Module]:
        return _parse_production_trees_fn()(include_scripts=True, include_skills=False)

    def test_a_real_full_scan_passes(self) -> None:
        """POSITIVE control: the genuine full scan (every member + scripts) does not
        raise. Without this, every negative below could be satisfied by a helper that
        raises unconditionally."""
        _assert_reached_fn()(self._real_scan())  # must not raise

    def test_a_missing_member_raises_and_names_it(self) -> None:
        """Coverage-as-checked-variable: drop one declared member's trees and the
        assertion must FAIL, naming the missing member. A build that only checks
        ``len(scanned) > 0`` passes this reduced dict — and is the exact bug the helper
        exists to prevent."""
        assert_reached = _assert_reached_fn()
        member = sorted(_declared_members())[0]
        reduced = {k: v for k, v in self._real_scan().items() if k.split("/", 1)[0] != member}
        with pytest.raises(AssertionError) as exc:
            assert_reached(reduced)
        assert member in str(exc.value), (
            f"the coverage failure did not name the dropped member {member!r} — it cannot "
            "tell WHICH reach was lost."
        )

    def test_it_fails_closed_on_an_empty_derivation(self) -> None:
        """⛔ THE LOAD-BEARING PIN (#290 class): an EMPTY scanned set must RAISE, never
        pass vacuously. A guard that green-lights ``{}`` certifies nothing and does it
        silently forever (registration_sites.py's anti-vacuity guard: 'zero sites means
        this tool is broken, not the tree').

        ⚠ The accessor is resolved OUTSIDE ``pytest.raises`` on purpose: at HEAD the
        helper is absent and the accessor's OWN ``AssertionError`` would be swallowed by
        the ``raises`` block — a false PASS for the wrong reason. Resolving first makes
        this RED-by-missing-helper at HEAD and RED-by-vacuous-pass after a wrong build."""
        assert_reached = _assert_reached_fn()
        with pytest.raises(AssertionError):
            assert_reached({})

    def test_the_oracle_is_independent_of_the_subject(self) -> None:
        """⛔ NOT ``derived == derived``: pass a dict claiming to cover ONLY the first
        member; the assertion must still raise, about the OTHER declared members — proving
        it reads pyproject.toml INDEPENDENTLY, not the scanned dict it was handed. A build
        that computed ``expected`` from the SAME keys it checks passes this and is green
        forever, including the day a member stops being scanned (the #251 failure)."""
        assert_reached = _assert_reached_fn()
        member = sorted(_declared_members())[0]
        one_member_only = {
            k: v for k, v in self._real_scan().items() if k.split("/", 1)[0] == member
        }
        with pytest.raises(AssertionError) as exc:
            assert_reached(one_member_only)
        others = sorted(_declared_members() - {member})
        assert any(other in str(exc.value) for other in others), (
            "the failure named none of the un-scanned members — the oracle is not "
            "independent of the subject (derived==derived), so it cannot see a lost member."
        )

    def test_an_undeclared_extra_package_raises(self) -> None:
        """Symmetric completeness: a scanned key under a package that is neither a declared
        member nor an extra_root must FAIL (equality, not subset) — a stale/renamed root
        is caught, not silently accepted."""
        assert_reached = _assert_reached_fn()
        scan = dict(self._real_scan())
        scan["not_a_member_pkg/foo.py"] = ast.parse("")
        with pytest.raises(AssertionError):
            assert_reached(scan)


# ---------------------------------------------------------------------------- #
# PROVE SHARING (static half) — no migration file keeps a private parser clone.
# ---------------------------------------------------------------------------- #


#: LAYER 2's signature, REFRAMED off the ``rglob`` spelling (§12.3). A hand-rolled
#: whole-tree parse is a PARSE PRIMITIVE + a FILE READ + a DIRECTORY SOURCE, all in one
#: function — the OLD ``{rglob, parse, read_text}`` three-leg shape with ONLY the directory
#: leg BROADENED (rglob → also ``production_sources``/``workspace_roots``/glob/iterdir), the
#: exact leg the delta-adversary's survivor evaded by moving ``rglob`` inside ``production_sources``.
_PARSE_PRIMITIVE_CALL_NAMES = frozenset({"parse", "compile"})  # ``ast.parse`` / ``compile(...)``
_FILE_READ_CALL_NAMES = frozenset({"read_text", "read_bytes"})
#: ⚠ ``walk`` is DELIBERATELY EXCLUDED — ``ast.walk`` (AST traversal, ubiquitous) shares the
#: call name with ``os.walk`` (a directory walk), and including it made EVERY AST-scanning test
#: file a false offender (measured this cycle). The directory sources below do NOT collide.
_DIRECTORY_SOURCE_CALL_NAMES = frozenset(
    {"production_sources", "workspace_roots", "rglob", "glob", "iglob", "iterdir"}
)


def _call_names_in(node: ast.AST) -> set[str | None]:
    """Every function-call NAME (``Name.id`` or ``Attribute.attr``) reachable within ``node``."""
    return {
        (call.func.attr if isinstance(call.func, ast.Attribute) else getattr(call.func, "id", None))
        for call in ast.walk(node)
        if isinstance(call, ast.Call)
    }


def _whole_tree_parse_offenders_in(tree: ast.Module) -> list[str]:
    """Names of functions in ``tree`` that hand-roll a whole-tree parse — the REFRAMED
    Layer-2 signature (§12.3, replacing the defeated ``rglob``-spelling detector).

    A hand-rolled whole-tree parse is a **PARSE PRIMITIVE** (``ast.parse`` → call name
    ``parse``, or ``compile``) co-occurring in ONE function with BOTH a **file read**
    (``read_text``/``read_bytes``) AND a **directory source** (``production_sources``/
    ``workspace_roots``/``rglob``/``glob``/``iglob``/``iterdir``).

    ⚠ WHY THIS SHAPE: the OLD detector required ``{rglob, parse, read_text}`` (all three); the
    delta-adversary's SURVIVOR moved ``rglob`` INTO ``production_sources`` and parsed via
    ``production_sources()``+``ast.parse(path.read_text())``, so the ``rglob`` leg went blind.
    The fix is minimal: keep all three legs (so single-FILE scanners that ``read_text`` one path
    are NOT flagged, and pure ``ast.walk`` traversals are NOT flagged), but BROADEN the directory
    leg to the whole-tree source functions ``production_sources``/``workspace_roots`` the survivor
    hid behind. Verified this cycle: this yields the same narrow offender set as the old detector
    PLUS the survivor's ``production_sources`` shape, and false-flags no honest single-file scanner.

    ⚠ HONEST BOUND (this is a LINT, not the invariant — Layer 1 is): keyed on call NAMES, it is
    ALIAS-defeatable (``ap = ast.parse; ap(p.read_text())`` hides the ``parse`` name) and
    ``open().read()``-defeatable (no ``read_text``). That un-executed / aliased tail is Layer 1's
    job (the runtime gate is alias-agnostic by construction) and INSTRUMENT 0's reach-attack —
    stated, not pretended closed. A synthetic-source ``ast.parse('<string>')`` control carries no
    read and no directory source, so honest controls are SPARED (the false-positive tax that
    switches a gate off)."""
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        calls = _call_names_in(node)
        if (
            (calls & _PARSE_PRIMITIVE_CALL_NAMES)
            and (calls & _FILE_READ_CALL_NAMES)
            and (calls & _DIRECTORY_SOURCE_CALL_NAMES)
        ):
            offenders.append(node.name)
    return offenders


def _calls_shared_parser(tree: ast.Module) -> bool:
    """True iff ``tree`` CALLS ``parse_production_trees`` — a CALL, not an import (A-SUB-1: an
    unused ``from _logging_fixtures import parse_production_trees  # noqa: F401`` is not
    consolidation). SPELLING-AGNOSTIC by design (A-SUB-5, the six-defeats shape one level
    down): it matches the call's function NAME, so a ``from`` import
    (``parse_production_trees(...)``) AND a module-attribute call
    (``_logging_fixtures.parse_production_trees(...)``) both count — the routing pin no longer
    mandates one import spelling (§9.7)."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            if name == "parse_production_trees":
                return True
    return False


def _rebind_everywhere_fn() -> Callable[..., AbstractContextManager[None]]:
    """The ``_rebind_everywhere`` context manager, REUSED (design §9.6) — it rebinds every
    module attribute that IS the target object, BY IDENTITY across ``sys.modules``, so the
    mutation reaches a FROM-import adopter (which binds the function object locally) as well as
    a module-attribute one. A single-module ``monkeypatch.setattr(_logging_fixtures, …)`` does
    NOT (A-SUB-3/-5) — verified empirically this cycle.

    Its current home is ``test_store_seam_one_derivation`` (finding #279's contract). This
    accessor checks ``_logging_fixtures`` FIRST so it tolerates the builder PROMOTING it to
    shared test-support — the design's ≥2-reuser promotion decision (F + A-SUB), which this
    contract does not force but does not break."""
    for module_name in ("_logging_fixtures", "test_store_seam_one_derivation"):
        module = importlib.import_module(module_name)
        fn = getattr(module, "_rebind_everywhere", None)
        if fn is not None:
            return cast("Callable[..., AbstractContextManager[None]]", fn)
    raise AssertionError(
        "`_rebind_everywhere` was not found in `_logging_fixtures` (promoted home) or "
        "`test_store_seam_one_derivation` (current home) — the ∀-mutation proof (§9.6) has no "
        "identity-rebinding tool, so a from-import adopter cannot be reached."
    )


def _calls_named(fn_node: ast.AST, wanted: str) -> bool:
    """True iff ``fn_node``'s body CALLS a function named ``wanted`` (Name or Attribute)."""
    for node in ast.walk(fn_node):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            if name == wanted:
                return True
    return False


#: LAYER 1's BROAD driving finder: a scan is a candidate to DRIVE iff it calls the helper OR
#: reaches the workspace by a DIRECTORY source or a FILE read. Deliberately spelling-agnostic on
#: the PARSE (which an alias hides) — the runtime guard catches the parse however it is spelled;
#: the finder only needs to recognise the SCAN so it gets driven. ``walk`` IS included here (unlike
#: the Layer-2 LINT, which excludes it to avoid false OFFENDERS): the OUTPUT classifier
#: (:func:`_is_workspace_tree_result`) filters an ``ast.walk`` helper whose output is not a tree, so
#: over-driving is harmless, while an ``os.walk`` scan gets driven and its aliased parse caught.
_REACH_SCAN_SIGNAL_CALL_NAMES = _DIRECTORY_SOURCE_CALL_NAMES | _FILE_READ_CALL_NAMES | {"walk", "open"}


def _is_scan_candidate(fn_node: ast.AST) -> bool:
    """True iff ``fn_node`` is a candidate to DRIVE under Layer 1's runtime guard — it calls the
    helper OR reaches the workspace by a directory source / file read (§12.3). Deliberately
    parse-spelling-agnostic: the parse spelling is irrelevant (the guard catches it however it is
    spelled); only the source/read must be recognised so the scan is driven. The OUTPUT classifier then
    decides which driven results are subject to the no-escape law, so driving extra file-readers is
    harmless. HONEST BOUND: a scan reaching files by NONE of these signals (e.g. ``os.scandir``, a
    hardcoded path list) is not driven here — that extreme tail is the session-wide-autouse form's
    job and INSTRUMENT 0's reach-attack, stated not pretended closed."""
    if _calls_named(fn_node, "parse_production_trees"):
        return True
    return bool(_call_names_in(fn_node) & _REACH_SCAN_SIGNAL_CALL_NAMES)


def _is_pytest_fixture_node(fn_node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """True iff ``fn_node`` carries an ``@pytest.fixture`` decorator. A fixture is NOT directly
    callable (pytest forbids it), so its underlying plain function is reached via ``__wrapped__``
    (:func:`_workspace_tree_fixtures`). Module-level so the L1 nullary enumerator and the L3
    fixture enumerator share ONE fixture-detector (DRY — a caller that hand-rolled this would
    drift the moment pytest's decorator spelling changed)."""
    for decorator in fn_node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        name = target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", None)
        if name == "fixture":
            return True
    return False


def _is_nullary_def(fn_node: ast.FunctionDef | ast.AsyncFunctionDef, *, is_method: bool) -> bool:
    """True iff ``fn_node`` takes no arguments (or only ``self`` for a method) — the shape that is
    drivable in-process. Module-level: shared by the L1 nullary enumerator and the L3 fixture
    enumerator (ONE definition of 'drivable in-process')."""
    args = fn_node.args
    if args.vararg or args.kwonlyargs or args.kwarg:
        return False
    return len(args.posonlyargs) + len(args.args) == (1 if is_method else 0)


def _nullary_derivations(
    filename: str, predicate: Callable[[ast.AST], bool]
) -> list[tuple[str, Callable[[], object]]]:
    """``[(name, callable)]`` — every NULLARY NON-FIXTURE callable in ``filename`` whose AST matches
    ``predicate``: a module-level ``def _x()`` or a ``self``-only non-fixture method, resolved to a
    LIVE callable. AST-DERIVED, never a hand-list of names. Layer 1's driving-enumerator: it passes
    :func:`_is_scan_candidate` (broad — anything that reaches the workspace, so an aliased parse is
    driven and caught by the runtime guard).

    ``@pytest.fixture`` nodes are EXCLUDED here (pytest forbids calling them directly). The REAL
    fixture the adopter's tests consume — the survivor's hiding place, which this enumerator by
    design cannot see — is driven through its ``__wrapped__`` by :func:`_workspace_tree_fixtures`
    (Layer 3, the restored §12.3 both-direction rider)."""
    module = importlib.import_module(filename[:-3])
    tree = ast.parse((_TESTS_DIR / filename).read_text(encoding="utf-8"))

    derivations: list[tuple[str, Callable[[], object]]] = []
    for node in tree.body:
        if (
            isinstance(node, ast.FunctionDef)
            and not _is_pytest_fixture_node(node)
            and predicate(node)
            and _is_nullary_def(node, is_method=False)
        ):
            fn = getattr(module, node.name, None)
            if callable(fn):
                derivations.append((node.name, fn))
        elif isinstance(node, ast.ClassDef):
            cls = getattr(module, node.name, None)
            if cls is None:
                continue
            for sub in node.body:
                if (
                    isinstance(sub, ast.FunctionDef)
                    and not _is_pytest_fixture_node(sub)
                    and predicate(sub)
                    and _is_nullary_def(sub, is_method=True)
                ):
                    bound = getattr(cls(), sub.name, None)
                    if callable(bound):
                        derivations.append((f"{node.name}.{sub.name}", bound))
    return derivations


def _drivable_scan_candidates(filename: str) -> list[tuple[str, Callable[[], object]]]:
    """BROAD driving set for Layer 1 (the runtime gate): nullary derivations that REACH the
    workspace by any recognisable source/read (:func:`_is_scan_candidate`), so an aliased-parse
    scan is driven and its escape caught by the guard. The OUTPUT classifier
    (:func:`_is_workspace_tree_result`) then decides which driven results are subject to the
    no-escape law."""
    return _nullary_derivations(filename, _is_scan_candidate)


def _members_spanned_by_keys(out: dict[object, object]) -> set[str]:
    """The DISTINCT workspace members whose files appear as keys in ``out`` — robust to a key that
    is repo-relative (``loremaster/loremaster/x.py``) OR absolute (``/…/loremaster/loremaster/x.py``),
    so an ``os.walk`` scan keyed by absolute path is classified the same as a repo-relative one."""
    members = _declared_members()
    found: set[str] = set()
    for key in out:
        if not isinstance(key, str):
            continue
        candidate = Path(key)
        try:
            relative = candidate.relative_to(_REPO_ROOT) if candidate.is_absolute() else candidate
            first = relative.as_posix().split("/", 1)[0]
        except ValueError:
            first = key.split("/", 1)[0]
        if first in members:
            found.add(first)
    return found


def _is_workspace_tree_result(out: object) -> bool:
    """True iff ``out`` is a WHOLE-WORKSPACE parse result — a ``dict`` of ``ast.Module`` spanning
    ≥2 DISTINCT workspace members (the ``parse_production_trees`` output shape a real scan and the
    survivor's private clone BOTH produce). This is the runtime classifier that lets Layer 1 assert
    "no escape" ONLY over derivations that scan the WHOLE workspace:
    - a single-file / synthetic-string parse returns a lone ``ast.Module`` → excluded;
    - a legitimate SINGLE-PACKAGE scan (the §7 allowlisted non-adopters) spans ONE member → excluded,
      so Layer 1 does not false-flag it (the false-positive tax that switches a gate off);
    - the survivor (repo-relative OR ``os.walk``-absolute keys across members) spans ≥2 → SUBJECT to
      the no-escape law.
    Output-shape (spans-the-workspace), not spelling — the discriminator §7 (single-package OK) and
    §12 (a whole-workspace private scan is the survivor) BOTH require."""
    if not isinstance(out, dict) or len(out) < 2:
        return False
    if not all(isinstance(value, ast.Module) for value in out.values()):
        return False
    return len(_members_spanned_by_keys(out)) >= 2


#: A WHOLE-WORKSPACE parse SOURCE — the sources that reach every member (vs a bare ``rglob`` over a
#: single package). A parse-primitive co-occurring with one of these is a whole-workspace parse SITE.
_WHOLE_WORKSPACE_SOURCE_CALL_NAMES = frozenset(
    {"production_sources", "workspace_roots", "parse_production_trees"}
)


def _parses_whole_workspace(fn_node: ast.AST) -> bool:
    """True iff ``fn_node`` DIRECTLY parses the whole workspace — a parse primitive
    (``ast.parse``/``compile``) co-occurring with a whole-workspace SOURCE. This is the
    parse-primitive TRUTH the ALL-set is derived from. A migrated adopter that ``return
    parse_production_trees(...)`` has the source but NO parse-primitive → NOT a site (its parse
    lives inside ``parse_production_trees``). A single-package ``rglob``+``ast.parse`` scan has the
    primitive but no whole-workspace source → NOT a site (legitimately single-package, §7)."""
    calls = _call_names_in(fn_node)
    return bool(calls & _PARSE_PRIMITIVE_CALL_NAMES) and bool(calls & _WHOLE_WORKSPACE_SOURCE_CALL_NAMES)


def _all_workspace_parse_sites() -> dict[str, str]:
    """⛔ THE ALL-SET (§12.3 / §12.5) — ``{"<file>::<funcname>": "<file>"}`` for every function that
    DIRECTLY parses a whole workspace tree (:func:`_parses_whole_workspace`), across the SANCTIONED
    parser's home (``_logging_fixtures``) AND the declared adopters.

    ⚠ DERIVED FROM THE PARSE-PRIMITIVE TRUTH — **NOT the offenders set and NOT a module name-list.**
    ``_all_sdk_call_sites``'s docstring records the exact v5 trap this avoids: a coverage pin built
    from the OFFENDERS set (``_unseamed_sdk_call_sites``) is *empty-on-clean → strictly dominated by
    the lint → CANNOT FIRE* (``WB-ROUTED-UNDRIVEN`` walked through, "#120 alive one altitude up").
    The ALL set is NON-EMPTY on a clean build — ``parse_production_trees`` itself is always a
    whole-workspace parse site — so the coverage pin CAN fire; a private parse site added anywhere in
    this set is then required to be OBSERVED executing (watched ≠ well-formed ≠ unexamined).

    Scoped to ``_logging_fixtures`` + the adopters (the set the coverage pin DRIVES); a whole-workspace
    parse in a non-adopter file is Layer 2's offender lint. The AST enumeration is alias-imperfect on
    the parse primitive (identical to the retry seam's bound) — the runtime gate catches aliased
    escapes absolutely, this ALL-set-observed pin bounds reach over sites it CAN see, the tail is
    Layer 2 + INSTRUMENT 0."""
    sites: dict[str, str] = {}
    for fname in ("_logging_fixtures.py", *_MIGRATION_SET):
        path = _TESTS_DIR / fname
        if not path.exists():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and _parses_whole_workspace(node):
                sites[f"{fname}::{node.name}"] = fname
    return sites


def _site_to_key(site: str) -> str:
    """``<basename>::<funcname>`` from a guard site string ``'<relfile>:<line> in <funcname>() [prim]'``
    — the join between the runtime OBSERVED/escape sites and the static :func:`_all_workspace_parse_sites`
    keys."""
    relfile = site.split(":", 1)[0]
    basename = relfile.rsplit("/", 1)[-1]
    funcname = site.split(" in ", 1)[1].split("(", 1)[0] if " in " in site else "?"
    return f"{basename}::{funcname}"


# ---------------------------------------------------------------------------- #
# THE ANTI-DUP ALLOWLIST — evidence-backed SAFE non-adopters (allowlist-the-safe).
# Keyed by FILE (design §7 allowlists non-adopter FILES). Each single-package /
# non-workspace-.py scan legitimately hand-rolls a tree walk for an UNRELATED reason;
# widening any of them to whole-tree is a SCOPE CHANGE that could widen a gap (§7,
# priority #3), NOT consolidation. Deny-by-default: a clone in any OTHER file is an
# offender that must migrate onto `parse_production_trees`.
# ---------------------------------------------------------------------------- #

_ALLOWED_WHOLE_TREE_CLONE_FILES: dict[str, str] = {
    "test_ast_reach_helpers.py": (
        "THIS FILE — the A-SUB substrate contract. Its META-scanners "
        "(_whole_tree_clone_offenders, _all_clone_files, _workspace_tree_fixtures) glob/import the "
        "TEST dir and ast.parse each test file to ENUMERATE "
        "clones/adopters — that IS the offender scan's own machinery, not a whole-tree PRODUCTION "
        "parse. Exempting the meta-scanner from itself is not a gap: it scans no workspace domain."
    ),
    "test_link5_render_containment.py": (
        "single-package loremaster error/render scans (_served_error_door_sites, "
        "_modules_constructing_a_domain_error) — server.py-scoped by design (§7); widening is a "
        "scope change, not consolidation."
    ),
    "test_render_seam_pins.py": (
        "single-package loremaster mint/template scans — loremaster-scoped (§7); a `root` arg "
        "exists but is called with the loremaster package TODAY (widening = scope change)."
    ),
    "test_task_read_surface.py": "single-package loremaster fence-site scan — loremaster-scoped (§7).",
    "test_text_hygiene.py": (
        "whole-repo GIT-TRACKED-TEXT NUL scan (_scan_package/_tracked_text_files), not a "
        "workspace-.py AST scan — a DIFFERENT primitive (§7)."
    ),
    "test_retry_seam.py": (
        "single-package loremaster SDK-seam discovery scans (_discover_query_seams, "
        "_all_sdk_call_sites, _unseamed_sdk_call_sites, _discover_*) — loremaster-scoped (§7)."
    ),
    "test_retired_symbols.py": (
        ".py+.md retired-name sweep across pkg+tests+docs — a candidate for a DIFFERENT shared "
        "retired-name primitive, not parse_production_trees (§7)."
    ),
    "test_secret_typing.py": (
        "its lorerunes-only stdlib/secret single-package scans "
        "(test_the_shared_package_depends_on_nothing_but_the_stdlib / "
        "test_the_shared_package_does_NOT_resolve_secrets) are legitimate single-package "
        "non-adopters (design §3 A-SUB bound) that legitimately carry the parse+read+directory "
        "clone signature over the lorerunes package ONLY. Its whole-tree `_python_sources` adopter "
        "migrates separately (pinned by TestTheMemberHandListsAreRetired + the used-ness pin); this "
        "allowlist entry covers only the single-package scans, and the dead-entry pin keeps it live."
    ),
    # ⚠ ``test_comms_footer.py`` was PROVISIONALLY allowlisted here (reviser-asub-b
    # DECISION-NEEDED #1). RULED 2026-08-09 (design §10 Ruling 6, fable-designer-2): it IS a
    # ``parse_production_trees`` adopter and moves into the A-SUB writable set → the provisional
    # entry is DELETED, so the offender scan below FLAGS its un-migrated Scan clones
    # (``_scan``/``_scan_source``, parse+read+directory) as a RED that forces migration, and the
    # dead-entry pin can never re-exempt it. Do NOT re-add it.
}


# ---------------------------------------------------------------------------- #
# THE PARSE-ADOPTER SKIP SET (§12.7.2 / §12.8, finding #349) — Layer 3's SILENT skip,
# promoted to a CHECKED VARIABLE (allowlist-the-safe, evidence-backed reasons + a
# per-file unrouted-whole-workspace-parse BUDGET, §12.8.3).
#
# THREAT MODEL, stated IN the instrument (§12.7.1): A-SUB's anti-dup guards ONE
# policy — the PARSE of the workspace trees, consolidated in
# ``parse_production_trees``; its chokepoint is ``compile`` (§12.2). It catches the
# HONEST developer who hand-rolls that parse (a private whole-tree ``ast.parse``/
# ``compile`` derivation drifts a new member silently, #291-shape). It is NOT a
# security boundary (small user base) and NOT a guard against every private
# tree-access — a NON-parsing tree-walk produces no AST, so it is OUT OF SCOPE by
# definition (pinned as a KNOWN BOUND, §12.7.3 / :class:`TestAsubNonParsingTreeWalkKnownBound349`).
#
# WHAT THIS SET IS: the ``_MIGRATION_SET`` adopters that Layer 3's fixture-consumer
# rider (``TestSharingProvenByMutation.test_each_real_fixture_consumer_reddens_when_
# the_shared_parser_is_dropped``)
# SKIPS because they expose no nullary workspace-tree ``@pytest.fixture`` (the delta-
# adversary-asub-4 "4 adopters SKIP" set). Each still ROUTES its whole-workspace parse
# through ``parse_production_trees`` (forced by
# :meth:`TestTheMigrationSetRoutesThroughTheSharedHelpers.test_the_file_calls_the_shared_parser`);
# it simply has no drivable in-process FIXTURE, so its sharing is proven by L1's runtime
# escape gate + :meth:`TestTheParseSkipSetIsACheckedVariable.test_no_skip_set_file_parses_the_tree_unrouted`
# below, not by the fixture-consumer pin. The reason per entry is EVIDENCE for that.
#
# ⚠ §12.8 RE-SOURCING (reviser-asub-6, 2026-08-10, finding #349 continued): the
# skip-coverage checked variable no longer keys on the STATIC ``_all_workspace_parse_sites``
# detector (a 3-name whole-workspace-source hand-list in ONE function) — delta-adversary-asub-5
# defeated that with a SPLIT-LEG private parse (source in a nullary helper, ``ast.parse`` loop
# in the consumer) that produces an AST but names no source in one function. It is re-sourced
# to L1's RUNTIME ``report.escapes`` (the ``builtins.compile`` chokepoint — un-defeatable by
# spelling), with a per-file DECLARED budget of unrouted whole-workspace parse SITES (default 0:
# the file ROUTES). A split-leg / comprehension / ``os.walk``+parse TEXT-source survivor now reddens
# (its private ``compile`` is an escape L1 records, and its str source resolves to a member) — but a
# bytes/normalized source resolves to ``member=""`` and is KNOWN BOUND #351 (§13 operator ruling,
# :class:`TestAsubBytesNormalizedSourceParseIsAKnownBound351`).
#
# ⚠ HONESTY CORRECTION (reviser-asub-5, ground-truthed 2026-08-09): design §12.7.2's
# EXAMPLE reason for backoff — *"does not parse the tree — it is a runtime-site reach
# check"* — is FACTUALLY WRONG. ``test_backoff_seam.py`` has TWO instruments: a
# non-parsing runtime-site reach check (``TestEveryBackoffSharesTheOnePolicy``) AND a
# whole-workspace AST parse (``TestNoNewHandRolledBackoff.test_no_production_module_
# outside_the_allowlist_exponentiates_by_a_variable`` → ``_production_python_files()`` →
# ``production_sources()`` + ``ast.parse``). The reasons below state the TRUE
# classification. The skip-coverage pin ENFORCES it at RUNTIME: a skip file the guard
# observes parsing the WORKSPACE unrouted (a site with >=2 compiles) beyond its budget
# reddens, so "confirmed routed, no fixture" is CHECKED, never "the reviser decided."


class _ParseSkip(NamedTuple):
    """One evidence-backed parse-adopter skip (§12.7.2 / §12.8.3).

    ``unrouted_whole_workspace_budget`` — the count of unrouted WHOLE-WORKSPACE parse SITES this
    file is permitted (§12.8.3, allowlist-the-safe). DEFAULT 0: the file ROUTES every whole-workspace
    parse through ``parse_production_trees``, so L1's runtime guard records ZERO unrouted
    whole-workspace compile sites for it. A genuine, evidence-backed unrouted whole-workspace parse —
    NONE exist today — would raise this above 0 WITH the ``reason`` naming the site. A SINGLE-PACKAGE
    scan (many files, but ONE member — a §7-allowlisted non-adopter) and a SINGLE-FILE parse need NO
    budget: the §12.8.3 discriminator counts a site as whole-workspace only when its escapes span
    >=2 MEMBERS (a tree enumeration), so a one-member scan is never charged.

    ``reason`` — the EVIDENCE: why this file exposes no drivable nullary workspace-tree fixture (so
    Layer 3 skips it) and how its whole-workspace parse is instead routed and runtime-checked by
    :meth:`TestTheParseSkipSetIsACheckedVariable.test_no_skip_set_file_parses_the_tree_unrouted`.
    """

    unrouted_whole_workspace_budget: int
    reason: str


_ASUB_PARSE_SKIP: dict[str, _ParseSkip] = {
    "test_backoff_seam.py": _ParseSkip(
        0,
        "ROUTES its whole-workspace parse through parse_production_trees (the perimeter scan "
        "TestNoNewHandRolledBackoff.test_no_production_module_outside_the_allowlist_exponentiates_"
        "by_a_variable, ast.parse over _production_python_files()→production_sources()). Exposes NO "
        "nullary workspace-tree @pytest.fixture (its scan is a self-only test method, not a fixture), "
        "so Layer 3's fixture-consumer pin cannot drive it. Sharing proven at RUNTIME: L1's "
        "compile-chokepoint guard sees its driven scan route SANCTIONED (budget 0 = zero unrouted "
        "whole-workspace parse sites). If it ever parses the workspace UNROUTED (the "
        "delta-adversary-asub-5 split-leg survivor at test_backoff_seam.py:780), L1 records the escape "
        "and the skip-coverage pin reddens for any ATTRIBUTABLE-source spelling (rglob / "
        "production_sources / split-leg text; a bytes/normalized source is KNOWN BOUND #351). Its "
        "OTHER instrument, "
        "TestEveryBackoffSharesTheOnePolicy, is a NON-parsing runtime reach check with its own mutation "
        "proof in that file — NOT part of A-SUB's parse policy. ⚠ §12.7.2's 'does not parse the tree' "
        "example was an incomplete read; backoff DOES parse."
    ),
    "test_secret_typing.py": _ParseSkip(
        0,
        "ROUTES its whole-workspace parse through parse_production_trees after retiring the "
        "_SCANNED_MEMBERS hand-list (design §A-SUB): its secret/typing scans (_secret_parameters, "
        "_unwrap_sites, _auth_construction_offenders, _secretstr_mint_sites) ast.parse the trees "
        "fed by _python_sources(). Exposes no nullary workspace-tree @pytest.fixture. Its "
        "lorerunes-ONLY single-package scans are separately allowlisted in "
        "_ALLOWED_WHOLE_TREE_CLONE_FILES (legitimate single-package non-adopters, §7) and are NOT "
        "whole-workspace parses. Sharing proven at RUNTIME by L1 + the skip-coverage pin (budget 0 = "
        "zero unrouted whole-workspace parse sites)."
    ),
    "test_secret_leak_vectors.py": _ParseSkip(
        0,
        "ROUTES its whole-workspace parse through parse_production_trees (design §A-SUB — already on "
        "production_sources): _production_function_names (production_sources()+ast.parse, a "
        "single-function whole-workspace parse) and the _workspace_python_sources()→production_sources() "
        "fed scans. Exposes no nullary workspace-tree @pytest.fixture. Sharing proven at RUNTIME by L1 + "
        "the skip-coverage pin (budget 0): while it is un-routed the guard records its whole-workspace "
        "compile as an escape and the pin reddens."
    ),
    "test_comms_footer.py": _ParseSkip(
        0,
        "A TWO-scan parse_production_trees adopter (design §10 Ruling 6): Scan A "
        "(include_tests=True) + Scan B (include_tests=False). Its migration + per-scan "
        "behaviour-preservation + mode binding are pinned by "
        "TestCommsFooterScansMigrateBehaviourPreserving / TestBothCommsFooterScansMigrateWithTheirModes. "
        "Exposes no nullary workspace-tree @pytest.fixture, so Layer 3's fixture-consumer pin skips "
        "it; sharing proven by those comms-footer pins + L1 + the skip-coverage pin (budget 0 = zero "
        "unrouted whole-workspace parse sites). RESIDUAL (§12.4): the A↔B purpose-swap is the named "
        "A-SUB cold-audit hand-check, not closable from this file."
    ),
}


def _whole_workspace_escape_sites(escapes: object) -> set[str]:
    """The guard call-sites whose escaped compiles span >=2 DISTINCT workspace MEMBERS — a
    whole-workspace ENUMERATION (§12.8.3, "spans >=2 members"). This is the SAME discriminator
    :func:`_is_workspace_tree_result` applies to a RETURN dict (members via keys), here applied to
    ESCAPES — because the delta-adversary split-leg survivor parses in a test method that returns
    None (no dict to inspect), so the return-value discrimination the escape invariant used could
    not see it (delta-adversary-asub-5 §2).

    ⚠ MEMBERS-SPANNED, not raw COUNT-per-site — a reviser-asub-6 refinement MEASURED against real
    data (REPORT-reviser-asub-6.md §satisfiability): ``test_secret_typing``'s lorerunes single-package
    scans parse >=2 lorerunes FILES at one site, so a ``count >= 2`` proxy would false-flag them as
    whole-workspace on a CORRECT migrated build (they stay un-routed, §7-allowlisted non-adopters)
    — a C-DEF. A single-PACKAGE scan spans ONE member and is correctly EXCLUDED; the whole-workspace
    survivor spans every member.

    The member is read from each escape's ``.member`` (the workspace member the compiled SOURCE
    belongs to). This IS the escape-record extension §12.8.3 authorizes, in its only useful form:
    the survivor calls ``ast.parse(path.read_text())`` with NO ``filename``, so the compiled target
    is ``<unknown>`` and the member must be resolved from the SOURCE content, NOT the compile
    filename argument (the same reason L1 keys the SITE off the caller frame, not the filename —
    see :func:`_install_parse_guard_fn`)."""
    members_by_site: dict[str, set[str]] = {}
    for escape in cast("list[object]", escapes):
        member = str(getattr(escape, "member", "") or "")
        if member:
            members_by_site.setdefault(str(getattr(escape, "site", "")), set()).add(member)
    return {site for site, members in members_by_site.items() if len(members) >= 2}


def _skip_files_parsing_whole_workspace(escapes: object) -> dict[str, set[str]]:
    """``{skip_file: {whole-workspace escape site, ...}}`` — the whole-workspace escape sites
    (:func:`_whole_workspace_escape_sites`) whose OWN call-site file is an ``_ASUB_PARSE_SKIP``
    entry. PURE over the escape list, so the §12.8.3 discrimination is exercised build-independently
    by synthetic escapes (the ``test_the_skip_coverage_discrimination_fires_and_discriminates`` control)."""
    result: dict[str, set[str]] = {}
    for site in _whole_workspace_escape_sites(escapes):
        relfile = site.split(":", 1)[0]
        basename = relfile.rsplit("/", 1)[-1]
        if basename in _ASUB_PARSE_SKIP:
            result.setdefault(basename, set()).add(site)
    return result


def _skip_budget_verdict(observed_count: int, budget: int) -> str | None:
    """The per-skip-file budget adjudication (§12.8.3, checked BOTH ways): ``"over"`` if the guard
    observed MORE unrouted whole-workspace parse sites than declared (the split-leg survivor);
    ``"dead"`` if FEWER (an over-declaration — the ``_ALLOWED_*`` dead-entry idiom, a stale budget
    silently exempts a future unrouted parse up to the declared count); else ``None`` (OK)."""
    if observed_count > budget:
        return "over"
    if observed_count < budget:
        return "dead"
    return None


def _whole_tree_clone_offenders() -> dict[str, list[str]]:
    """``{filename: [clone function names]}`` for every ``test_*.py`` that hand-rolls a
    whole-tree parse (parse-primitive + file-read + directory-source, :func:`_whole_tree_parse_offenders_in`)
    OUTSIDE the evidence-backed :data:`_ALLOWED_WHOLE_TREE_CLONE_FILES` allowlist.

    DERIVED from the tree (the ``test_retry_seam._unseamed_sdk_call_sites`` OFFENDER shape,
    §9.6): enumerate ALL clone sites from truth, subtract the SAFE allowlist, NAME the rest.
    Deny-by-default — a new whole-tree clone in a not-allowlisted file is an offender the day
    it lands (this is the A-SUB-2 miss the adversary planted a file to expose)."""
    offenders: dict[str, list[str]] = {}
    for path in sorted(_TESTS_DIR.glob("test_*.py")):
        if path.name in _ALLOWED_WHOLE_TREE_CLONE_FILES:
            continue
        clones = _whole_tree_parse_offenders_in(ast.parse(path.read_text(encoding="utf-8")))
        if clones:
            offenders[path.name] = clones
    return offenders


def _all_clone_files() -> dict[str, list[str]]:
    """``{filename: [clone function names]}`` for EVERY ``test_*.py`` with a whole-tree clone —
    allowlisted or not. The anti-vacuity + dead-entry checks read this."""
    found: dict[str, list[str]] = {}
    for path in sorted(_TESTS_DIR.glob("test_*.py")):
        clones = _whole_tree_parse_offenders_in(ast.parse(path.read_text(encoding="utf-8")))
        if clones:
            found[path.name] = clones
    return found


def _member_hand_lists_in(tree: ast.Module) -> list[str]:
    """Module-level assignments named ``_SCANNED_MEMBERS`` — the per-file member hand-list the
    migration retires (design §9.7 A-SUB-4, the real #291-shaped consolidation).

    ⚠ BOUND: keyed on the NAME ``_SCANNED_MEMBERS`` (the design's named instance). A DIFFERENTLY
    NAMED per-file member hand-list is not structurally distinguishable from any other tuple of
    string pairs, so it is INSTRUMENT 0's standing guard, not this pin — stated, not pretended
    closed."""
    names: list[str] = []
    for node in tree.body:
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        for target in targets:
            if isinstance(target, ast.Name) and target.id == "_SCANNED_MEMBERS":
                names.append(target.id)
    return names


class TestTheMigrationSetRoutesThroughTheSharedHelpers:
    """⛔ PROVE SHARING (used-ness half): after A-SUB, each ∀-scan file CALLS
    ``parse_production_trees`` rather than keeping a private clone. The adversary's
    fix-nothing build (A-SUB-1) passed the old import-PRESENCE pin with three UNUSED imports;
    this pin requires a CALL, which that build cannot supply."""

    @pytest.mark.parametrize("filename", _MIGRATION_SET)
    def test_the_file_calls_the_shared_parser(self, filename: str) -> None:
        """Each migration-set file CALLS ``parse_production_trees`` (not merely imports it).
        At HEAD the helper does not exist and nothing calls it → RED; the builder routes each
        file's whole-workspace parse through the shared helper to go green. Spelling-agnostic
        (A-SUB-5): a ``from``-import call and a module-attribute call both satisfy it, so the
        pin no longer pushes builders toward one import form."""
        path = _TESTS_DIR / filename
        assert path.exists(), f"migration-set file {filename} not found at {path}"
        assert _calls_shared_parser(ast.parse(path.read_text(encoding="utf-8"))), (
            f"{filename} does not CALL parse_production_trees — it has not been migrated onto "
            "the shared reach substrate (F4), OR it imports the helper but never uses it (the "
            "unused-import 'consolidation' A-SUB-1 caught). If this file genuinely needs "
            "neither (a single-package scan that parses for an unrelated reason), that is a "
            "design call to raise with the lead — and to add to _ALLOWED_WHOLE_TREE_CLONE_FILES "
            "/ drop from _MIGRATION_SET — not a silent skip."
        )

    def test_the_canonical_clone_is_removed_from_the_anchored_scan(self) -> None:
        """⛔ The design names ``test_anchored_pattern_seam._parse_production_trees`` as the
        parser cloned "verbatim". After A-SUB that private whole-workspace parse loop
        (parse-primitive + file-read + directory-source) must be GONE — routed through the shared
        helper. At HEAD it is present → RED. (The general case is
        :class:`TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist`; this is the named
        instance kept as a focused regression pin.)"""
        anchored = _TESTS_DIR / "test_anchored_pattern_seam.py"
        clones = _whole_tree_parse_offenders_in(ast.parse(anchored.read_text(encoding="utf-8")))
        assert clones == [], (
            f"test_anchored_pattern_seam.py still hand-rolls a production-tree parse loop "
            f"in {clones} — the canonical clone the substrate exists to absorb. Route it "
            "through `_logging_fixtures.parse_production_trees`."
        )

    def test_the_clone_detector_actually_fires_on_a_clone(self) -> None:
        """POSITIVE control: the detector SEES a hand-rolled parse loop. Without this, a
        green suite is indistinguishable from a detector that never matches anything."""
        source = (
            "import ast\n"
            "def _parse(roots):\n"
            "    trees = {}\n"
            "    for root in roots:\n"
            "        for p in root.rglob('*.py'):\n"
            "            trees[p] = ast.parse(p.read_text())\n"
            "    return trees\n"
        )
        assert _whole_tree_parse_offenders_in(ast.parse(source)) == ["_parse"]

    def test_the_reframed_detector_fires_on_the_rglob_LESS_survivor_shape(self) -> None:
        """⛔ THE DELTA-ADVERSARY SURVIVOR, as a synthetic control. The routing-not-sharing
        survivor derives via ``production_sources()`` + ``ast.parse(path.read_text())`` — NO
        ``rglob`` in-function (it moved inside ``production_sources``). The OLD ``{rglob, parse,
        read_text}`` detector was BLIND to this (the exact hole §12 closes); the reframed
        directory-source leg (``production_sources`` ∈ the set) MUST flag it."""
        survivor = (
            "import ast\n"
            "from _logging_fixtures import production_sources\n"
            "def _parse_production_trees():\n"
            "    trees = {}\n"
            "    for _label, path in production_sources():\n"
            "        trees[path.as_posix()] = ast.parse(path.read_text())\n"
            "    return trees\n"
        )
        assert _whole_tree_parse_offenders_in(ast.parse(survivor)) == ["_parse_production_trees"], (
            "the reframed detector is BLIND to the production_sources()+ast.parse survivor — the "
            "directory-source leg must include production_sources/workspace_roots, not just rglob."
        )

    def test_the_clone_detector_does_not_fire_on_a_synthetic_source_parse(self) -> None:
        """NEGATIVE control: an ``ast.parse('<source string>')`` on a synthetic control
        (the shape every scanner's positive-control tests use) is NOT a tree-parser clone,
        so the detector must not flag it — else the pin refuses honest code and gets
        switched off."""
        source = "import ast\ndef _uses(src):\n    return ast.parse(src)\n"
        assert _whole_tree_parse_offenders_in(ast.parse(source)) == []

    def test_the_clone_detector_does_not_fire_on_a_single_file_parser(self) -> None:
        """⛔ NEGATIVE control — the FALSE-POSITIVE that would switch this gate off. A scanner
        that ``ast.parse``s the contents of ONE named file (``read_text`` but NO directory walk)
        is a single-package/single-file scan, NOT a whole-tree clone. Requiring ALL THREE legs
        (parse + read + DIRECTORY-source) spares it — dropping the directory leg flagged every
        single-file AST scanner in the tree (measured this cycle), the false-positive tax that
        gets an instrument deleted."""
        source = (
            "import ast\n"
            "from pathlib import Path\n"
            "def _scan_one_file():\n"
            "    return ast.parse(Path('loremaster/loremaster/server.py').read_text())\n"
        )
        assert _whole_tree_parse_offenders_in(ast.parse(source)) == [], (
            "a single-FILE parser (read_text without a directory walk) was flagged as a whole-tree "
            "clone — the detector's directory-source leg is missing, and it will be switched off."
        )


# ---------------------------------------------------------------------------- #
# THE DERIVED ANTI-DUP SCAN (A-SUB-2) — no whole-tree parser clone outside the
# SAFE allowlist. "migrated" is a CHECKED VARIABLE, not the files someone remembered.
# ---------------------------------------------------------------------------- #


class TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist:
    """⛔ THE A-SUB-2 MISS (adversary planted a new whole-tree clone; 0 new failures). Design
    §7 required a DERIVED anti-dup structural pin — *no test file hand-rolls a whole-tree parse
    (parse-primitive + file-read + directory-source) outside an evidence-backed non-adopter
    allowlist*. This is ALLOWLIST-THE-SAFE (the CORRECT pattern the contract wrongly dropped as
    "enumerate-the-forbidden"): the SAFE set is small and enumerable; the offender set is
    DERIVED from the whole tree. Reuses the ``test_retry_seam._unseamed_sdk_call_sites``
    OFFENDER shape (§9.6).

    ⚠ LAYER 2, HONEST: this is the WEAK-BUT-TOTAL backstop, alias-defeatable by construction (a
    ``parse``-name alias or ``open().read()`` hides from a name-keyed AST scan). The un-defeatable
    catch is LAYER 1 (:class:`TestNoPrivateParseEscapesTheSanctionedParserAtRuntime`) — the runtime
    ``builtins.compile`` chokepoint. Both ship, exactly as ``test_retry_seam`` ships lint + runtime
    gate; this one covers code Layer 1 does not execute, and says so."""

    def test_no_unallowlisted_whole_tree_parser_clone_survives(self) -> None:
        """RED at HEAD (``641f758``): ``test_anchored_pattern_seam._parse_production_trees`` is
        an un-migrated whole-tree clone and is NOT allowlisted. After A-SUB it routes through
        the shared parser and this passes; a NEW clone in a not-allowlisted file reddens it the
        day it lands (the checked-variable property)."""
        offenders = _whole_tree_clone_offenders()
        assert offenders == {}, (
            "these test files hand-roll a whole-tree parse (parse-primitive + file-read + "
            "directory-source) "
            f"OUTSIDE the evidence-backed allowlist (finding #279/F4 — 'migrated' is not a "
            f"checked variable for them):\n  {offenders}\n"
            "MIGRATE each onto `_logging_fixtures.parse_production_trees`, OR (if it is a "
            "legitimate single-package / non-workspace-.py scan) add the FILE to "
            "_ALLOWED_WHOLE_TREE_CLONE_FILES with an evidence-backed reason + a re-open trigger. "
            "Do NOT widen a single-package scanner to whole-tree — that is a scope change, not "
            "consolidation (§7)."
        )

    def test_the_scan_is_not_vacuous(self) -> None:
        """⛔ ANTI-VACUITY / positive control (registration_sites.py's guard): the clone
        detector must FIND clones across the real tree — the allowlisted single-package scans
        are living proof it runs over real files. Zero clones anywhere means the detector is
        broken, not that the tree is clean."""
        all_clones = _all_clone_files()
        assert all_clones, (
            "the whole-tree clone detector found NO parse+read+directory loop in ANY test "
            "file — it is broken (the allowlisted single-package scans should register), so a "
            "green offender check certifies nothing."
        )

    def test_the_allowlist_carries_no_dead_entries(self) -> None:
        """⛔ DEAD-ENTRY pin (``_ALLOWED_ANCHORED_MATCH`` idiom): every allowlisted file must
        ACTUALLY contain a whole-tree clone today. A stale allowlist entry (the file no longer
        has a clone, e.g. it was migrated) is a silent exemption for whatever lands there next
        — self-cleaning: the day ``test_comms_footer`` is migrated, its provisional entry goes
        dead and this pin forces its removal."""
        all_clones = _all_clone_files()
        dead = sorted(name for name in _ALLOWED_WHOLE_TREE_CLONE_FILES if name not in all_clones)
        assert dead == [], (
            f"these _ALLOWED_WHOLE_TREE_CLONE_FILES entries no longer match a real whole-tree "
            f"clone (dead exemptions): {dead}. Delete each — an allowlist entry with no live "
            "offender silently exempts the next clone added to that file."
        )

    def test_a_planted_clone_in_a_fresh_file_would_be_caught(self) -> None:
        """POSITIVE control on the DERIVED reach (the A-SUB-2 reproduction): a whole-tree clone
        in a file that is neither allowlisted nor named anywhere is an offender. Proven on
        synthetic AST (not a real planted file) so the control leaves no residue."""
        clone_source = (
            "import ast\n"
            "def _scan():\n"
            "    trees = {}\n"
            "    for root in ROOTS:\n"
            "        for p in root.rglob('*.py'):\n"
            "            trees[p] = ast.parse(p.read_text())\n"
            "    return trees\n"
        )
        fresh_filename = "test_zzz_a_brand_new_scanner.py"
        assert fresh_filename not in _ALLOWED_WHOLE_TREE_CLONE_FILES, "control mis-built"
        assert _whole_tree_parse_offenders_in(ast.parse(clone_source)) == ["_scan"], (
            "a fresh whole-tree clone is invisible to the detector — the A-SUB-2 hand-list gap."
        )


# ---------------------------------------------------------------------------- #
# THE MEMBER HAND-LISTS ARE RETIRED (A-SUB-4) — the real #291-shaped consolidation.
# ---------------------------------------------------------------------------- #


class TestTheMemberHandListsAreRetired:
    """⛔ A-SUB-4 (design §9.7): the migration's REAL consolidation is retiring the per-file
    ``_SCANNED_MEMBERS`` hand-list (a #291-shaped drift: a private copy of "which members
    exist" that ``parse_production_trees`` / ``assert_scan_reached_every_member`` now own). No
    A-SUB pin asserted it gone; the adversary showed it surviving green."""

    @pytest.mark.parametrize("filename", _MIGRATION_SET)
    def test_no_migration_file_keeps_a_scanned_members_hand_list(self, filename: str) -> None:
        """RED at HEAD: ``test_secret_typing._SCANNED_MEMBERS`` (a tuple of ``(member, path)``
        pairs) still stands. After A-SUB it is gone — the member set comes from the shared
        derivation, not a per-file copy."""
        path = _TESTS_DIR / filename
        assert path.exists(), f"migration-set file {filename} not found at {path}"
        hand_lists = _member_hand_lists_in(ast.parse(path.read_text(encoding="utf-8")))
        assert hand_lists == [], (
            f"{filename} still declares a member hand-list {hand_lists} (`_SCANNED_MEMBERS`) — "
            "the per-file copy of 'which workspace members exist' the migration retires. Read "
            "the members from the shared derivation (pyproject via "
            "`assert_scan_reached_every_member`), not a private tuple."
        )


# ---------------------------------------------------------------------------- #
# LAYER 1 — the RUNTIME chokepoint gate (§12.3). The un-defeatable catch: a private
# whole-tree parse escapes the sanctioned parser at the `builtins.compile` primitive,
# spelling- AND alias-agnostic. GENERALISES test_retry_seam's runtime SDK guard from the
# SDK-connection primitive to `builtins.compile`. RED at HEAD (the guard is unbuilt — the
# accessor raises a NAMED failure); GREEN on a reference build; CATCHES the survivor.
# ---------------------------------------------------------------------------- #


class TestNoPrivateParseEscapesTheSanctionedParserAtRuntime:
    """⛔ LAYER 1 — the property checked where it LIVES: at RUNTIME, on the `builtins.compile`
    primitive, so it cannot be evaded by spelling OR alias (the exact lesson
    ``test_retry_seam.TestNoSdkCallEscapesTheDriverAtRuntime`` teaches, one primitive over).

    Producing an ``ast.Module`` of source REQUIRES ``builtins.compile`` (``ast.parse`` calls
    ``compile(src, name, mode, PyCF_ONLY_AST)`` — VERIFIED this cycle, see
    :meth:`test_the_routing_verification_compile_AND_ast_parse_both_register`). The guard wraps it
    (a PLAIN ``def``, so the stack walk happens at CALL time) and records any ``PyCF_ONLY_AST``
    compile made from a workspace ``.py`` SITE with NO ``parse_production_trees`` frame above it as
    an ESCAPE, named file:line. ``os.walk``, a comprehension, a direct ``compile``, an alias
    ``ap = ast.parse`` — all die at once, because the check never looks at code.

    SCOPE, stated honestly (a gate that overstates its reach is the thing we police): the runtime
    gate sees the code the DRIVEN derivations EXECUTE (the §12.3 '(or drives the derived adopter
    scans)' form). A private parse in a non-nullary test method, or in a non-declared file, is
    Layer 2's / the session-wide-autouse form's job — stated, not pretended closed. The
    SESSION-WIDE autouse form (the guard armed from conftest for every test, retry-seam's shape) is
    the STRONGER completeness mechanism §12.3 names first; the builder should ALSO wire it, and this
    contract's reach pin is the self-contained mechanical check that does not depend on that wiring.

    ⚠ ACCESSOR/AST BEFORE ARM: every pin resolves its accessors and does its AST analysis BEFORE
    arming the guard — the guard wraps ``builtins.compile``, so the contract's OWN ``ast.parse``
    calls (to enumerate derivations) would otherwise be recorded as escapes."""

    def test_the_routing_verification_compile_AND_ast_parse_both_register(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⛔ THE LOAD-BEARING POS CONTROL — and the routing proof the reviser OWES (§12.6). Arm
        the guard, then from THIS file (a workspace ``.py`` site, no ``parse_production_trees`` frame)
        make a DIRECT ``compile(..., PyCF_ONLY_AST)`` AND an ``ast.parse(...)``. The guard must
        record BOTH as escapes, with primitives ``{"compile", "ast.parse"}`` — demonstrating
        ``ast.parse`` routes through the wrapped ``builtins.compile``.

        If ``"ast.parse"`` is MISSING, ``ast.parse`` does NOT route through the wrapped
        ``builtins.compile`` on this Python and the guard must ALSO wrap ``ast.parse``. VERIFIED
        routing on Python 3.14.6 this cycle (probe receipt in REPORT-reviser-asub-3.md); this pin
        enshrines it so a future Python — or a build that fumbles the ``PyCF_ONLY_AST`` filter —
        cannot silently drop half the primitive. RED at HEAD (the guard is unbuilt)."""
        install = _install_parse_guard_fn()
        report = install(monkeypatch)
        assert getattr(report, "armed", False), (
            "the parse-guard did not ARM — build parse_production_trees (its sanctioned frame) and "
            "the guard first. `armed=False` is the honest pre-build posture, but the routing proof "
            "needs a live guard."
        )
        source = "x = 1\ndef _probe():\n    return 2\n"
        before = len(report.escapes)
        compile(source, "<asub-routing-probe>", "exec", ast.PyCF_ONLY_AST)  # noqa: F841 (side effect is the point)
        ast.parse(source)
        new_escapes = report.escapes[before:]
        primitives = {getattr(escape, "primitive", None) for escape in new_escapes}
        assert primitives == {"compile", "ast.parse"}, (
            f"the runtime guard recorded primitives {primitives}, not both. If 'ast.parse' is "
            "MISSING, ast.parse does NOT route through the wrapped builtins.compile on this Python "
            "— the guard MUST also wrap ast.parse (routing VERIFIED on 3.14.6 this cycle; the pin "
            "exists precisely to catch a regression here). If 'compile' is missing, the PyCF_ONLY_AST "
            "filter is wrong."
        )

    def test_a_private_production_sources_scan_is_an_escape_named(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⛔ POS CONTROL — the delta-adversary SURVIVOR's exact shape. A private
        ``production_sources()`` + ``ast.parse(path.read_text())`` scan from a test, with NO
        ``parse_production_trees`` frame, is an ESCAPE named file:line. This is the routing-not-
        sharing derivation the offender LINT (Layer 2) can be aliased past — here it is caught at
        runtime, absolutely."""
        from _logging_fixtures import production_sources  # noqa: PLC0415

        one_source = production_sources(include_scripts=False, include_skills=False)[0][1]
        text = one_source.read_text(encoding="utf-8")  # read BEFORE arming (read is not a parse)
        install = _install_parse_guard_fn()
        report = install(monkeypatch)
        assert getattr(report, "armed", False), "the parse-guard did not arm"
        before = len(report.escapes)
        ast.parse(text)  # the private parse, no sanctioned frame
        new_escapes = report.escapes[before:]
        assert new_escapes, (
            "a private ast.parse of a workspace source, with no parse_production_trees frame above "
            "it, was NOT recorded as an escape — the runtime gate is blind to the exact survivor "
            "§12 exists to close."
        )
        sites = [str(getattr(escape, "site", "")) for escape in new_escapes]
        assert any("test_ast_reach_helpers.py" in site for site in sites), (
            f"the escape did not NAME this file:line as the site: {sites}. "
            "A gate that cannot name the offender site is not actionable."
        )

    def test_a_parse_routed_through_the_sanctioned_parser_is_allowed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⛔ NEG CONTROL — the correct idiom must be ALLOWED, or the builder deletes the gate.
        ``parse_production_trees``'s OWN parses carry a ``parse_production_trees`` frame → they are
        SANCTIONED (observed), never escapes. A gate that flags the sanctioned parser cries wolf
        and gets switched off (retry-seam's own lesson)."""
        parse = _parse_production_trees_fn()
        install = _install_parse_guard_fn()
        report = install(monkeypatch)
        assert getattr(report, "armed", False), "the parse-guard did not arm"
        before = len(report.escapes)
        trees = parse(include_scripts=True, include_skills=False)
        assert trees, "parse_production_trees produced nothing — the neg control cannot run"
        new_escapes = report.escapes[before:]
        assert not new_escapes, (
            "parse_production_trees's OWN parses were flagged as escapes: "
            f"{[str(getattr(e, 'site', '')) for e in new_escapes][:5]} — the guard flags the "
            "sanctioned parser (a false positive on the correct idiom), so the builder deletes it. "
            "The sanctioned frame check must treat a parse_production_trees frame as allowed."
        )
        report.require_observations("driving parse_production_trees against the real workspace")

    def test_the_guard_refuses_a_clean_verdict_it_saw_nothing_for(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⛔ ANTI-VACUITY (#136 / ``require_observations``): 'no escapes' having seen NOTHING is
        BLINDNESS wearing cleanliness. Arm the guard, drive NO parse, and ``require_observations``
        MUST raise — naming the zero-observation condition. Then a POSITIVE control: after a real
        sanctioned parse it does NOT raise (or the check is an unconditional raise, discriminating
        nothing). The accessor is resolved OUTSIDE ``pytest.raises`` so its own HEAD AssertionError
        is not swallowed into a false pass (the ``test_it_fails_closed_on_an_empty_derivation``
        idiom)."""
        parse = _parse_production_trees_fn()
        install = _install_parse_guard_fn()
        report = install(monkeypatch)
        assert getattr(report, "armed", False), "the parse-guard did not arm"
        with pytest.raises(Exception) as blind:  # noqa: PT011,B017 — a GuardCannotSubstantiate-shaped refusal
            report.require_observations("a flow that provably parses (but none was driven)")
        message = str(blind.value).lower()
        assert "observ" in message or "blind" in message, (
            "require_observations raised, but not about blindness / zero observations — a gate must "
            "name WHY it cannot substantiate a verdict (#136), not raise opaquely."
        )
        parse(include_scripts=False, include_skills=False)  # a real sanctioned parse
        report.require_observations("driving a real sanctioned parse")  # must NOT raise now

    def test_no_declared_adopter_parses_privately(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⛔ THE ESCAPE INVARIANT (§12.3, the spelling-agnostic catch). For EACH declared adopter,
        drive its scan candidates under the armed guard; every WORKSPACE-SCANNER derivation (output =
        a dict spanning ≥2 members) must route SANCTIONED (no escape). A routing-not-sharing adopter
        — real scan via ``production_sources()``+``ast.parse``, decoy calls the helper — ESCAPES here,
        named file:line: the exact survivor (the decoy's sanctioned call cannot hide the real private
        derivation, because BOTH are driven; the broad :func:`_drivable_scan_candidates` finder reaches
        an aliased-parse scan by its SOURCE, so the parse spelling is irrelevant).

        ⚠ This is the ESCAPE INVARIANT, NOT the coverage — the offenders/escapes set is used HERE
        (the invariant), and the ALL-set is used by
        :meth:`test_every_whole_workspace_parse_site_was_watched_executing` (the coverage). Splitting
        them is deliberate: coverage built from escapes is empty-on-clean and cannot fire (the v5 trap).

        HONEST BOUND: this DRIVES the derived adopter scans; a private parse hidden in a NON-nullary
        test method is not driven here (→ Layer 2 static + the coverage pin + the session-wide-autouse
        form catch it). ``require_observations`` (#136) refuses a clean verdict the guard saw nothing for."""
        # Enumerate candidates BEFORE arming — the AST analysis parses adopter sources, which must not
        # be recorded as escapes.
        candidates_by_adopter = {adopter: _drivable_scan_candidates(adopter) for adopter in _MIGRATION_SET}
        install = _install_parse_guard_fn()
        report = install(monkeypatch)
        assert getattr(report, "armed", False), (
            "the parse-guard did not arm — the escape invariant cannot certify anything. Build "
            "parse_production_trees + the guard."
        )
        escapes_named: list[str] = []
        for adopter, candidates in candidates_by_adopter.items():
            for name, derive in candidates:
                before = len(report.escapes)
                try:
                    out = derive()
                except Exception:  # noqa: BLE001 — a candidate that raises is not a clean workspace scanner
                    continue
                if not _is_workspace_tree_result(out):
                    continue  # a control / non-workspace derivation — not subject to the no-escape law
                new_escapes = report.escapes[before:]
                if new_escapes:
                    sites = [str(getattr(escape, "site", "")) for escape in new_escapes][:3]
                    escapes_named.append(f"{adopter}::{name} parsed PRIVATELY at {sites}")
        assert not escapes_named, (
            "these adopters' REAL workspace scans parsed PRIVATELY (a production_sources()+ast.parse "
            "copy with NO parse_production_trees frame) — routing-not-sharing, the survivor §12 "
            "closes; a decoy calling the helper does not save them:\n  " + "\n  ".join(escapes_named)
        )
        report.require_observations("driving every declared adopter's workspace scan")

    def test_every_whole_workspace_parse_site_was_watched_executing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⛔ THE REACH-CHECKED-VARIABLE / COVERAGE pin (§12.3 / §12.5, reusing ``_all_sdk_call_sites``'s
        SHAPE **and its documented v5 trap**). Every whole-workspace parse SITE
        (:func:`_all_workspace_parse_sites` — the ALL set, derived from the parse-primitive TRUTH, NOT
        the offenders set and NOT a name-list) must be OBSERVED EXECUTING under the guard when the
        adopters are driven. A site never watched is a reach gap, NAMED: **"watched is not the same as
        well-formed, and neither is the same as unexamined."**

        WHY THE ALL SET, NOT THE OFFENDERS SET (the crux): ``_all_sdk_call_sites``'s docstring is the
        receipt — its v5 coverage built the enumeration from the OFFENDERS set (empty by construction on
        a lint-clean build) → strictly dominated by the lint → could not fire → ``WB-ROUTED-UNDRIVEN``
        walked straight through (#120 alive one altitude up). The ALL set is NON-EMPTY on a clean build
        (``parse_production_trees`` itself is always a whole-workspace parse site), so this pin CAN fire,
        and a routed-but-undriven parse site turns it RED the day it is written.

        ⚠ Sites enumerated + candidates found BEFORE arming (the AST analysis must not parse under the
        guard). HONEST BOUND: the ALL-set AST enumeration is alias-imperfect on the parse primitive
        (identical to the retry-seam bound); the runtime gate catches aliased escapes absolutely, this
        pin bounds reach over sites it CAN see, and the un-enumerable tail is Layer 2 + INSTRUMENT 0."""
        all_sites = _all_workspace_parse_sites()
        candidates_by_adopter = {adopter: _drivable_scan_candidates(adopter) for adopter in _MIGRATION_SET}
        install = _install_parse_guard_fn()
        report = install(monkeypatch)
        assert getattr(report, "armed", False), (
            "the parse-guard did not arm — the coverage pin cannot certify anything. Build "
            "parse_production_trees + the guard."
        )
        assert all_sites, (
            "the ALL-set enumeration (_all_workspace_parse_sites) found NO whole-workspace parse site "
            "— the scanner is broken (parse_production_trees itself should always register), so a green "
            "coverage check certifies nothing (anti-vacuity)."
        )
        for _adopter, candidates in candidates_by_adopter.items():
            for _name, derive in candidates:
                try:
                    derive()
                except Exception:  # noqa: BLE001 — a candidate that raises is not a clean workspace scanner
                    continue
        watched = {
            _site_to_key(site)
            for site in ([*report.observed] + [str(getattr(escape, "site", "")) for escape in report.escapes])
        }
        unobserved = sorted(key for key in all_sites if key not in watched)
        assert not unobserved, (
            f"the runtime guard never OBSERVED {len(unobserved)} of {len(all_sites)} whole-workspace "
            f"parse sites EXECUTE, so it certifies NOTHING about them:\n  " + "\n  ".join(unobserved)
            + "\n\nA runtime gate is an invariant only over code it RUNS. An unwatched parse site is a "
            "reach gap — expose it as a nullary derivation the coverage drives (a `def _parse…()` the "
            "fixture/tests consume), route it through parse_production_trees, OR supply a "
            "scripts/mutation_proof.py receipt. 'watched ≠ well-formed ≠ unexamined' (§12.3)."
        )


# ---------------------------------------------------------------------------- #
# ∀-MUTATION over the LIVE-DERIVED adopter set (A-SUB-3) — the load-bearing proof.
#
# The nullary enumerator above is Layer 1's driving set. Layer 3 (§12.3's restored
# both-direction rider) additionally drives the REAL FIXTURE each adopter's tests CONSUME —
# the survivor's hiding place, which the nullary enumerator by design cannot see — through its
# ``__wrapped__``, and requires the fixture's real coverage CONSUMERS to REDDEN under the drop.
# ---------------------------------------------------------------------------- #


def _workspace_tree_fixtures(filename: str) -> list[tuple[str, Callable[[], object]]]:
    """``[(fixture_name, underlying_callable)]`` — every module-level NULLARY ``@pytest.fixture``
    in ``filename`` whose OUTPUT is a whole-workspace tree (:func:`_is_workspace_tree_result`),
    resolved to the plain function pytest wraps (``__wrapped__``).

    ⚠ OUTPUT-classified, NEVER AST-call-name: the REAL fixture body is ``return
    _parse_production_trees()`` — it calls a DECOY helper, not ``parse_production_trees`` directly,
    and carries no parse primitive of its own — so a call-name/parse-primitive predicate would MISS
    it. That miss is the delta-adversary-asub-3 survivor (REPORT-delta-adversary-asub-3): the real
    ``production_trees`` fixture scans PRIVATELY via ``os.walk`` while a correctly-migrated
    ``_parse_production_trees`` decoy satisfies every NULLARY-driven pin. Classifying by the runtime
    OUTPUT (a dict of ``ast.Module`` spanning ≥2 members) reaches the fixture however it derives.

    This is exactly the surface :func:`_nullary_derivations` EXCLUDES (``@pytest.fixture`` nodes are
    not directly callable). BOUND (stated, per §6): only a NULLARY module-level fixture is drivable
    through ``__wrapped__``; a fixture that takes other fixtures, or a class-scoped one, is not driven
    here — Layer 1's escape gate (its session-wide-autouse form) + INSTRUMENT 0 own that tail. The
    survivor's OWN target staying drivable is a CHECKED VARIABLE
    (:meth:`TestSharingProvenByMutation.test_the_survivor_target_fixture_is_a_checked_variable`)."""
    module = importlib.import_module(filename[:-3])
    tree = ast.parse((_TESTS_DIR / filename).read_text(encoding="utf-8"))
    found: list[tuple[str, Callable[[], object]]] = []
    for node in tree.body:
        if not (isinstance(node, ast.FunctionDef) and _is_pytest_fixture_node(node)):
            continue
        if not _is_nullary_def(node, is_method=False):
            continue
        fixture_obj = getattr(module, node.name, None)
        underlying = getattr(fixture_obj, "__wrapped__", fixture_obj)
        if not callable(underlying):
            continue
        try:
            out = underlying()
        except Exception:  # noqa: BLE001 — a fixture that raises un-driven is not a workspace scanner
            continue
        if _is_workspace_tree_result(out):
            found.append((node.name, cast("Callable[[], object]", underlying)))
    return found


def _fixture_consumer_nodes(
    filename: str, fixture_name: str
) -> list[tuple[str, Callable[[object], object]]]:
    """``[(qualname, bound_method)]`` — every ``test_*`` method in ``filename`` taking EXACTLY
    ``(self, <fixture_name>)``, resolved to a bound callable that accepts the fixture VALUE. These
    are the REAL consumers §12.3 requires to go RED when the shared parser is dropped: they read
    their observed set FROM the fixture, which (in a correct build) reads FROM the shared parser.

    BOUND (stated, per §6): a consumer taking OTHER fixtures too (e.g. ``monkeypatch``) is not
    drivable in-process and is skipped — Layer 1 + INSTRUMENT 0 own that tail. The coverage
    consumer the survivor must defeat (anchored's reach pin) takes only ``(self, production_trees)``."""
    module = importlib.import_module(filename[:-3])
    tree = ast.parse((_TESTS_DIR / filename).read_text(encoding="utf-8"))
    consumers: list[tuple[str, Callable[[object], object]]] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        cls = getattr(module, node.name, None)
        if cls is None:
            continue
        for sub in node.body:
            if not (isinstance(sub, ast.FunctionDef) and sub.name.startswith("test")):
                continue
            params = [param.arg for param in (sub.args.posonlyargs + sub.args.args)]
            if params == ["self", fixture_name]:
                bound = getattr(cls(), sub.name, None)
                if callable(bound):
                    consumers.append(
                        (f"{node.name}.{sub.name}", cast("Callable[[object], object]", bound))
                    )
    return consumers


def _consumers_that_redden(
    consumers: list[tuple[str, Callable[[object], object]]], tree_value: object
) -> set[str]:
    """The qualnames of ``consumers`` that RAISE when fed ``tree_value`` — 'redden' in pytest's
    sense (any exception is a failure). Used both ways in the #194 both-direction diff: fed a literal
    ``{}`` it yields the DECLARED-RED set (the drop's genuine tree effect, computed independently
    BEFORE the drop); fed the fixture's OUTPUT-under-drop it yields the OBSERVED-RED set. A
    declared-RED consumer absent from the observed set = it stayed GREEN under the drop = the fixture
    fed it from a private scan (routing-not-sharing)."""
    reds: set[str] = set()
    for name, run_consumer in consumers:
        try:
            run_consumer(tree_value)
        except Exception:  # noqa: BLE001 — any raise is a RED (pytest treats every exception as failure)
            reds.add(name)
    return reds


class TestSharingProvenByMutation:
    """⛔ IDIOM 1 / LEG B (design §9.1, §9.7 A-SUB-3) + §12.3's BOTH-DIRECTION-DIFF RIDER, RESTORED.
    Drop the shared parser and prove each adopter's REAL consumer output DEPENDS on it — the RED
    home the static pins lack (a routing-not-sharing adopter that imports the helper but derives
    privately survives them; the runtime drop names it). The mutation reaches a FROM-import adopter
    because ``_rebind_everywhere`` rebinds BY IDENTITY across ``sys.modules`` (a single-module
    ``monkeypatch`` does not — A-SUB-3/-5).

    ⚠ THE RESTORED RIDER (delta-adversary-asub-3 proved it LOAD-BEARING with a positive control;
    REPORT-delta-adversary-asub-3). reviser-asub-3 DROPPED §12.3's both-direction diff and bound the
    ∀ to a NULLARY derivation's key-reflection instead. The delta-adversary showed a
    routing-not-sharing build that passes the WHOLE contract 47/0: ``_parse_production_trees`` is
    migrated correctly (a DECOY that satisfies every NULLARY-driven pin) while the REAL
    ``production_trees`` @pytest.fixture that feeds anchored's tests scans PRIVATELY via ``os.walk``.
    The nullary enumerator never sees the fixture (pytest forbids calling it), so key-reflection on
    the decoy passed and the survivor walked. §12.3's SPECIFIED fix — restored here — binds the ∀ to
    the adopter's REAL FIXTURE the tests CONSUME (driven through ``__wrapped__`` by
    :func:`_workspace_tree_fixtures`), and requires that fixture's real coverage CONSUMERS to go RED
    under ``parse_production_trees → {}`` — the #194 both-direction diff (declared-RED must actually
    redden; a declared-RED that STAYS GREEN = a private copy = FAIL). The decoy cannot make the real
    coverage consumer redden (its result feeds nothing) → it is worthless; the private fixture scan
    stays green under the drop → CAUGHT.

    ⚠ NOT an OR-clause a decoy defeats: the fixture drive is REQUIRED wherever a nullary
    workspace-tree fixture exists, and the survivor's OWN target (anchored's ``production_trees``)
    being drivable is a CHECKED VARIABLE
    (:meth:`test_the_survivor_target_fixture_is_a_checked_variable`), not an assumption. Nullary
    private scans (no fixture) are Layer 1's escape gate. The ``_live_adopters()=="calls the helper"``
    call-existence proxy the decoy defeated is RETIRED, and reviser-asub-3's nullary key-reflection
    substitute (``test_dropping_the_shared_parser_reddens_the_adopter_derivation``) is RETIRED with
    it. DRY: reuses ``_rebind_everywhere`` (the shared by-identity drop) and mutation_proof.py's #194
    both-direction diff principle — see §12.5 / the satisfiability receipt in REPORT-reviser-asub-4.md.

    BOUND (stated, per §6): the fixture drive reaches NULLARY module-level fixtures + consumers taking
    exactly ``(self, <fixture>)``. A non-nullary fixture, or a consumer taking other fixtures, is not
    drivable in-process — Layer 1's session-wide-autouse form + INSTRUMENT 0's reach-attack own that
    tail, not pretended closed."""

    def test_the_rebind_mutation_reaches_a_from_import_binding(self) -> None:
        """⛔ MECHANISM positive control (GREEN now AND after — independent of the build, like
        ``test_store_seam_one_derivation.TestTheMutationProofDiscriminates``). Proves the
        ∀-mutation's tool discriminates a router from a private clone AND reaches a from-import
        binding — the exact reach the single-module monkeypatch (A-SUB-3/-5) could not. If this
        control ever fails, the ∀ below is measuring nothing."""
        rebind = _rebind_everywhere_fn()

        shared = types.ModuleType("_asub_probe_shared_helper")

        def real_parse() -> dict[str, str]:
            return {"loremaster/x.py": "TREE"}

        shared.parse = real_parse  # type: ignore[attr-defined]
        sys.modules[shared.__name__] = shared
        try:
            # a FROM-import adopter binds the function object LOCALLY (the shape the
            # single-module monkeypatch cannot reach):
            adopter = types.ModuleType("_asub_probe_from_import_adopter")
            exec("from _asub_probe_shared_helper import parse\n", adopter.__dict__)  # noqa: S102
            sys.modules[adopter.__name__] = adopter

            def router() -> dict[str, str]:
                # the local from-import binding (dynamically set on the probe module)
                return cast("dict[str, str]", getattr(adopter, "parse")())  # noqa: B009

            frozen = dict(real_parse())

            def private_clone() -> dict[str, str]:
                return dict(frozen)  # never re-reads the shared helper

            assert router() == private_clone(), "baseline: both agree before the mutation"

            def dropped() -> dict[str, str]:
                return {}

            with rebind(real_parse, dropped):
                assert router() == {}, (
                    "the from-import binding did NOT reflect the identity rebind — the "
                    "∀-mutation cannot reach a from-import adopter, so its RED home is a lie."
                )
                assert private_clone() != {}, (
                    "the private clone reflected the mutation — the technique cannot tell a "
                    "router from a private copy, so it cannot fail routing-not-sharing."
                )
        finally:
            sys.modules.pop("_asub_probe_from_import_adopter", None)
            sys.modules.pop(shared.__name__, None)

    def test_the_declared_adopter_surface_is_non_empty(self) -> None:
        """⛔ ANTI-VACUITY for the parametrized ∀: the declared adopter set must be NON-EMPTY, or
        the ∀ below has zero cases and 'passes' by measuring nothing. The reach is now the DECLARED
        :data:`_MIGRATION_SET` (not the retired ``_live_adopters()`` proxy), and Layer 1
        (:class:`TestNoPrivateParseEscapesTheSanctionedParserAtRuntime`) is the COMPLETENESS checked
        variable — a private parse in ANY driven derivation escapes there, so the declared set being
        a small known set is acceptable (§12.3)."""
        assert _MIGRATION_SET, (
            "the declared adopter surface _MIGRATION_SET is empty — the ∀-mutation below has zero "
            "cases and certifies nothing. This fail-closed guard is its anti-vacuity."
        )

    def test_the_survivor_target_fixture_is_a_checked_variable(self) -> None:
        """⛔ ANTI-VACUITY / CHECKED-VARIABLE for the fixture reach (GREEN now AND after — a
        BUILD-INDEPENDENT mechanism control, like ``test_the_rebind_mutation_reaches_a_from_import_binding``).
        The delta-adversary-asub-3 survivor hides its private scan in anchored's ``production_trees``
        fixture; the per-adopter pin below can only catch it if the discovery actually DRIVES that
        fixture. So make 'the survivor's own target is reached' a checked variable: anchored MUST
        expose a nullary workspace-tree fixture named ``production_trees``.

        A build that hides the fixture behind a fixture-arg (non-nullary → undiscoverable → the
        per-adopter pin silently drives zero fixtures for anchored) reddens HERE; a build that removes
        the fixture breaks anchored's own tests at collection (five of them take ``production_trees``).
        Naming anchored is a POSITIVE CONTROL on the KNOWN target (the
        ``test_the_scan_resolves_the_known_anchored_constants`` idiom), NOT the ∀'s reach — the reach
        is LIVE-derived by :func:`_workspace_tree_fixtures`."""
        names = {name for name, _ in _workspace_tree_fixtures("test_anchored_pattern_seam.py")}
        assert "production_trees" in names, (
            "anchored's `production_trees` fixture is not discovered as a nullary workspace-tree "
            f"fixture (found {sorted(names)}). It is the delta-adversary-asub-3 survivor target; if "
            "the discovery cannot reach it, the per-adopter sharing pin drives nothing for anchored "
            "and the routing-not-sharing survivor walks. A non-nullary production_trees (taking a "
            "fixture arg) is the evasion this catches — Layer 1 + INSTRUMENT 0 own the non-nullary "
            "tail, but the survivor's OWN target must stay a checked variable, not an assumption."
        )

    @pytest.mark.parametrize("adopter", _MIGRATION_SET)
    def test_each_real_fixture_consumer_reddens_when_the_shared_parser_is_dropped(
        self, adopter: str
    ) -> None:
        """⛔ §12.3's BOTH-DIRECTION-DIFF RIDER, RESTORED (the delta-adversary-asub-3 BLOCKER). For
        each of the adopter's LIVE workspace-tree FIXTURES (:func:`_workspace_tree_fixtures` — the
        REAL fixture the tests consume, the survivor's hiding place the nullary enumerator cannot
        see), drop the shared parser (``_rebind_everywhere`` by-identity) and require the fixture's
        real coverage CONSUMERS to go RED — the #194 both-direction diff:

          declared-RED = consumers that redden when fed a literal ``{}`` (the drop's genuine tree
                         effect), computed INDEPENDENTLY, BEFORE the drop;
          observed-RED = consumers that redden when fed the fixture's output UNDER the drop.

        A declared-RED consumer that STAYS GREEN under the drop = the fixture fed it from a PRIVATE
        scan that ignores ``parse_production_trees`` (routing-not-sharing: a decoy migrates
        ``_parse_production_trees`` while the real ``production_trees`` fixture scans via
        ``os.walk``/``production_sources``) = FAIL. §12.3 / #194: a declared-RED that stays GREEN =
        a private copy.

        RED at HEAD (helper unbuilt): the accessor raises, resolved FIRST — the honest RED, before
        any discovery runs. On a correct build the fixture returns ``{}`` under the drop → its
        consumers redden → observed == declared → GREEN. On the survivor the fixture returns the
        real tree under the drop → its consumers stay GREEN → observed ⊊ declared → CAUGHT.

        Adopters with NO nullary workspace-tree fixture (their reach is a nullary domain scan or a
        single-package scan) are covered by Layer 1's escape gate + Layer 2, not this pin — a SKIP
        names that. It is NOT a decoy-defeatable OR-clause: the survivor's target IS a nullary
        workspace-tree fixture (checked above), so anchored is never skipped."""
        real_parse = _parse_production_trees_fn()  # RED at HEAD (helper unbuilt) — resolved FIRST
        rebind = _rebind_everywhere_fn()

        def dropped(*_args: object, **_kwargs: object) -> dict[str, ast.Module]:
            return {}

        fixtures = _workspace_tree_fixtures(adopter)
        if not fixtures:
            # §12.7.2: the SKIP is no longer SILENT — it is a CHECKED VARIABLE. An adopter may
            # be skipped by this fixture-consumer pin ONLY when it is on the evidence-backed
            # _ASUB_PARSE_SKIP allowlist. A NEW fixtureless adopter (or a build that hid a
            # private scan behind a non-fixture derivation, the delta-adversary-asub-4 hole)
            # can no longer skip silently — it reddens HERE, forcing an explicit disposition:
            # give it a nullary workspace-tree fixture (so this pin covers it), OR add it to
            # _ASUB_PARSE_SKIP with an evidence reason (then the skip-coverage pin checks the
            # skip is honest — it does not parse the tree UNROUTED).
            assert adopter in _ASUB_PARSE_SKIP, (
                f"{adopter} exposes no nullary workspace-tree @pytest.fixture, so this "
                "fixture-consumer sharing pin cannot drive it — but it is NOT on the "
                "_ASUB_PARSE_SKIP allowlist, so this would be a SILENT exemption (the "
                "delta-adversary-asub-4 hole: a fixtureless adopter whose private scan no layer "
                "asserts on). Either give it a nullary workspace-tree @pytest.fixture its tests "
                "consume, OR add it to _ASUB_PARSE_SKIP with an evidence reason for why its "
                "sharing is proven elsewhere (L1's escape gate + the skip-coverage pin). A skip "
                "without a reason is exactly the silent exemption §12.7 exists to close."
            )
            pytest.skip(
                f"{adopter} exposes no nullary workspace-tree @pytest.fixture — it is an "
                "_ASUB_PARSE_SKIP adopter (checked variable, §12.7.2): its sharing is proven by "
                "Layer 1 (the runtime escape gate) + test_no_skip_set_file_parses_the_tree_unrouted, "
                "not this fixture-consumer pin. (The survivor's target, anchored's production_trees, "
                "is a checked variable in test_the_survivor_target_fixture_is_a_checked_variable, so "
                "this SKIP cannot hide it.)"
            )
        for fixture_name, derive_fixture in fixtures:
            consumers = _fixture_consumer_nodes(adopter, fixture_name)
            assert consumers, (
                f"{adopter}:{fixture_name} is a workspace-tree fixture with NO drivable consumer (a "
                f"test taking exactly (self, {fixture_name})) — its sharing has no coverage RED home "
                "here, so a private scan behind it would be invisible. Give it a coverage consumer, "
                "or route it through parse_production_trees so Layer 1 covers it."
            )
            healthy_tree = derive_fixture()
            assert _is_workspace_tree_result(healthy_tree), (
                f"{adopter}:{fixture_name} did not produce a workspace tree healthy — the positive "
                "control is broken, so its reddening under the drop would mean nothing."
            )
            # POSITIVE control: every consumer PASSES on the real tree (so reddening MEANS the drop).
            red_on_real = _consumers_that_redden(consumers, healthy_tree)
            assert not red_on_real, (
                f"{adopter}:{fixture_name} consumers {sorted(red_on_real)} FAIL on the real tree — "
                "they are broken independent of sharing; fix them before this pin can certify sharing."
            )
            # DECLARED-RED = consumers reddening on a literal {} (the drop's genuine tree effect),
            # computed BEFORE the drop (never transcribed from the observed run — #194's own bound).
            declared_red = _consumers_that_redden(consumers, {})
            assert declared_red, (
                f"{adopter}:{fixture_name} has NO consumer that reddens on an EMPTY tree — the "
                "both-direction diff has nothing to require RED, so it cannot prove the fixture reads "
                f"from the shared parser. Route a reach/coverage consumer (a test taking (self, "
                f"{fixture_name}) that fails on an empty tree) through this fixture."
            )
            # OBSERVED-RED = consumers reddening when the fixture is DRIVEN under the drop.
            with rebind(real_parse, dropped):
                dropped_tree = derive_fixture()
                observed_red = _consumers_that_redden(consumers, dropped_tree)
            stayed_green = sorted(declared_red - observed_red)
            assert not stayed_green, (
                f"{adopter}:{fixture_name} — these coverage consumers were DECLARED-RED (they redden "
                f"on an empty tree) but STAYED GREEN when the shared parser was dropped: {stayed_green}. "
                "The fixture fed them from a PRIVATE scan that ignores parse_production_trees "
                "(routing-not-sharing: a decoy migrates _parse_production_trees while the real fixture "
                "scans via os.walk/production_sources — the delta-adversary-asub-3 survivor). §12.3 / "
                "#194: a declared-RED that stays GREEN is a private copy. Route the fixture through "
                "parse_production_trees."
            )
            unexpected_red = sorted(observed_red - declared_red)
            assert not unexpected_red, (
                f"{adopter}:{fixture_name} — dropping the shared parser reddened consumers NOT "
                f"declared-RED on an empty tree: {unexpected_red}. The drop broke something other than "
                "the reach the diff targets (a bare pass/fail tail cannot see this — #194 "
                "both-direction). Investigate before trusting the sharing verdict."
            )


# ---------------------------------------------------------------------------- #
# COMMS-FOOTER: per-scan BEHAVIOUR-PRESERVATION + the granularity hazard + the
# Scan-B narrowing escalation (design §10 Ruling 6, fable-designer-2).
# ---------------------------------------------------------------------------- #


class TestCommsFooterScansMigrateBehaviourPreserving:
    """⛔ §10 Ruling 6: ``test_comms_footer`` is a ``parse_production_trees`` adopter with TWO
    whole-tree scans; each migrates BEHAVIOUR-PRESERVINGLY (§8 Ruling 1: post-migration scanned
    FILE SET == pre-migration set EXACTLY, per adopter) with DIFFERENT ``include_tests``.

    The oracle is each scan's PRE-migration file set, re-derived INDEPENDENTLY from disk
    (:func:`_comms_footer_scan_a_pre_migration` / :func:`_member_package_files`), never the
    subject's own loop — so it is not ``derived == derived`` and can SEE a member the migration
    drops. RED at HEAD (641f758): ``parse_production_trees`` is unbuilt (the accessor raises a
    NAMED failure) AND comms_footer is un-migrated.

    ⚠ These pins assert the SHARED HELPER produces each scan's file set for the mode that scan
    adopts (Scan A → ``include_tests=True``; Scan B → ``include_tests=False``). Which scan uses
    which mode is pinned at file granularity by
    :class:`TestBothCommsFooterScansMigrateWithTheirModes` (with its stated bound); the file-set
    truth per mode is here.
    """

    def _members_only(self, trees: dict[str, ast.Module]) -> set[str]:
        """The member-file keys of a ``parse_production_trees`` result (``scripts``/``skills``
        stripped), so the comparison is against the workspace-member reach the scans govern."""
        return {key for key in trees if key.split("/", 1)[0] in _declared_members()}

    def test_include_tests_true_readds_exactly_the_member_tests(self) -> None:
        """⛔ THE GRANULARITY HAZARD (§10 R6.3) — the pin that catches Scan A NARROWING.

        ``workspace_roots`` yields the ``<member>/<member>`` PACKAGE root, which structurally
        EXCLUDES ``<member>/tests``. So ``parse_production_trees(include_tests=True)`` MUST RE-ADD
        ``<member>/tests`` for member roots, or Scan A (which scans prod AND member tests today)
        silently drops every member-test file — a widened gap (priority #3) wearing
        consolidation's clothes. This asserts the re-added set is EXACTLY ``<member>/tests``:
        not less (narrowing) and not more (a stray root)."""
        parse = _parse_production_trees_fn()
        without_tests = self._members_only(parse(include_scripts=False, include_tests=False))
        with_tests = self._members_only(parse(include_scripts=False, include_tests=True))
        member_tests = _member_test_files()
        assert member_tests, (
            "anti-vacuity: no <member>/tests files found on disk — the oracle is broken, so a "
            "green re-add check would certify nothing."
        )
        assert not (without_tests & member_tests), (
            "parse_production_trees(include_tests=False) ALREADY yields member-test files — but "
            "workspace_roots yields <member>/<member> which excludes <member>/tests. A leak here "
            f"means the root derivation changed: {sorted(without_tests & member_tests)[:5]}"
        )
        readded = with_tests - without_tests
        assert readded == member_tests, (
            "include_tests=True did NOT re-add EXACTLY <member>/tests (§10 R6.3 granularity "
            "hazard). If it re-adds LESS, Scan A narrows (drops member-test files it scans "
            "today); if MORE, a stray root crept in.\n"
            f"  re-added-not-member-tests: {sorted(readded - member_tests)[:5]}\n"
            f"  member-tests-NOT-re-added (the narrowing): {sorted(member_tests - readded)[:5]}"
        )

    def test_scan_A_reach_is_behaviour_preserving_under_include_tests_true(self) -> None:
        """⛔ (b) Scan A (prod AND tests): post-migration file set under
        ``parse_production_trees(include_tests=True)`` == its pre-migration set EXACTLY (262 @
        641f758). ``pre - post`` is a NARROWED reach (a widened gap); ``post - pre`` a widened
        scan (possible new REDs). Both are §8-R1 violations."""
        parse = _parse_production_trees_fn()
        post = self._members_only(parse(include_scripts=False, include_tests=True))
        pre = _comms_footer_scan_a_pre_migration()
        assert pre, "anti-vacuity: Scan A pre-migration oracle is empty — cannot certify equality."
        assert post == pre, (
            "Scan A does not reproduce its pre-migration reach under include_tests=True (§8 R1 "
            "requires EXACT per-adopter behaviour preservation).\n"
            f"  pre-not-post (NARROWED — a widened gap): {sorted(pre - post)[:5]}\n"
            f"  post-not-pre (widened): {sorted(post - pre)[:5]}"
        )

    def test_scan_B_reach_is_the_design_intended_prod_only_set(self) -> None:
        """⛔ (b) Scan B, migrated to ``parse_production_trees(include_tests=False)``, keys ==
        the prod-only member-package set (90 @ 641f758).

        ⚠⚠ **DECISION-NEEDED — the oracle here is the DESIGN-INTENDED post-migration set, NOT the
        literal pre-migration set, and that is a deliberate, escalated deviation** (see
        REPORT-reviser-asub-2.md). §10 R6 calls Scan B "PRODUCTION ONLY" and migrates it to
        ``include_tests=False`` — but Scan B's TRUE pre-migration reach is **131** files (90 prod
        + **41** lorerunes/loresigil/lorescribe TEST files), because its hardcoded tuple mixes
        loremaster's NESTED package path with 3 FLAT member dirs, so those 3 members' tests leak
        into a production-query-door scan while loremaster's do not. **No single
        ``parse_production_trees`` mode reproduces 131** (False=90, True=262), so an EXACT §8-R1
        preservation via one helper call is IMPOSSIBLE. Recommended reading (b): migrate to
        ``include_tests=False`` (prod-only, 90); the 41 test files are an OLD BUG (accidental
        over-reach) dropped-deliberately — Scan B hunts PRODUCTION doors and test files are not
        production surfaces. The drop is adjudicated safe by
        :meth:`test_scan_B_narrowing_drops_only_accidental_test_over_reach`. If the operator
        instead rules PRESERVE-131, this pin and that sibling change (the builder keeps bespoke
        roots — not a clean single-helper consolidation)."""
        parse = _parse_production_trees_fn()
        post = self._members_only(parse(include_scripts=False, include_tests=False))
        intended = _member_package_files()
        assert intended, "anti-vacuity: Scan B intended prod-only oracle is empty."
        assert post == intended, (
            "Scan B (migrated to include_tests=False) does not equal the prod-only member-package "
            "set the design intends.\n"
            f"  intended-not-post: {sorted(intended - post)[:5]}\n"
            f"  post-not-intended: {sorted(post - intended)[:5]}"
        )

    def test_scan_B_narrowing_drops_only_accidental_test_over_reach(self) -> None:
        """⛔ REMOVED-BEHAVIOUR INVENTORY, made mechanical (CLAUDE.md dual rule): the Scan B
        migration (131 → 90 under reading b) drops EXACTLY the accidental member-test over-reach
        — never a PRODUCTION file. If a production file would be dropped, the "narrowing" is a
        real widened gap (priority #3) and this reddens, naming it.

        GREEN at HEAD and after migration: it guards the SHAPE of the adjudicated drop (a pure
        disk fact), not the migration state. If Scan B ever becomes genuinely prod-only, ``pre ==
        intended`` and this fires with 'delete the escalation' — self-cleaning."""
        pre = _comms_footer_scan_b_pre_migration()
        intended = _member_package_files()
        dropped = pre - intended
        assert dropped, (
            "Scan B's pre-migration reach == the intended prod-only set: §10 R6's 'PRODUCTION "
            "ONLY' was correct after all. Delete this escalation pin and the DECISION-NEEDED note "
            "in REPORT-reviser-asub-2.md; the Scan B migration is a plain behaviour-preserving one."
        )
        production_dropped = sorted(path for path in dropped if not _is_member_test_file(path))
        assert not production_dropped, (
            "the Scan B narrowing would drop PRODUCTION files, not just the accidental member-test "
            f"over-reach — a REAL widened gap (priority #3), NOT an old-bug drop: {production_dropped}"
        )
        loremaster_dropped = sorted(path for path in dropped if path.startswith("loremaster/"))
        assert not loremaster_dropped, (
            "unexpected loremaster files in the Scan B drop. Scan B scans loremaster via its "
            "package root (prod only), so loremaster tests were NEVER in Scan B — that asymmetry "
            f"is WHY the drop is an accidental over-reach of the 3 flat members: {loremaster_dropped[:5]}"
        )


def _comms_footer_scan_modes_by_scope() -> dict[str, list[object]]:
    """``{enclosing_scope: [include_tests modes]}`` for every ``parse_production_trees`` call in
    ``test_comms_footer``, keyed by the TOP-LEVEL function or ``Class.method`` that contains it.

    The scan↔mode BINDING instrument (§12.4): binds each ``include_tests`` mode to the DISTINCT
    SCAN SCOPE that consumes it, so Scan A (prod+tests, ``include_tests=True``) and Scan B
    (prod-only, ``include_tests=False``) cannot be collapsed into one migration or given the wrong
    mode without a distinct scope for each surviving."""
    tree = ast.parse((_TESTS_DIR / _COMMS_FOOTER).read_text(encoding="utf-8"))
    scopes: dict[str, list[object]] = {}

    def record(scope_name: str, node: ast.AST) -> None:
        modes = _parse_prod_trees_modes_in(ast.unparse(node))
        if modes:
            scopes.setdefault(scope_name, []).extend(modes)

    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            record(node.name, node)
        elif isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, ast.FunctionDef | ast.AsyncFunctionDef):
                    record(f"{node.name}.{sub.name}", sub)
    return scopes


class TestBothCommsFooterScansMigrateWithTheirModes:
    """⛔ §12.4 — the scan↔mode BINDING, PINNED (not hand-checked). Both comms-footer scans migrate
    onto ``parse_production_trees``, in BOTH modes, EACH mode bound to a DISTINCT scan scope — so
    Scan A (prod+tests → ``include_tests=True``) and Scan B (prod-only → ``include_tests=False``)
    cannot be collapsed into one migration nor left un-migrated, and the equality pins in
    :class:`TestCommsFooterScansMigrateBehaviourPreserving` prove each MODE yields the right file
    set (a narrowing helper reddens them). Together: each scan's mode is bound to a distinct scope
    AND each mode's file set is pinned to its pre-migration oracle.

    ⚠ HONEST RESIDUAL (§12.4's own fallback, stated not glossed): the ONE case this cannot catch
    mechanically from this file is a pure A↔B PURPOSE swap — BOTH modes present, in TWO distinct
    scopes, but the prod+tests-PURPOSE scan given ``include_tests=False`` while the prod-only-PURPOSE
    scan is given ``True``. Distinguishing "which scope is Scan-A-by-PURPOSE" needs knowledge this
    file does not have (it would require name-keying comms_footer's internals — the enumerate-the-
    forbidden trap one level up). That specific swap is the NAMED A-SUB cold-audit hand-check
    (§12.4), OR — the stronger fix — the builder routes each scan through a distinctly-named nullary
    helper whose name a future pin binds to its mode. Default is these pins; the hand-check is the
    escape hatch, not the plan."""

    def test_comms_footer_migrates_both_scans_in_both_modes(self) -> None:
        """RED at HEAD (641f758): comms_footer calls ``parse_production_trees`` zero times (it
        hand-rolls both scans). After migration BOTH literal modes are present — Scan A with
        ``include_tests=True`` (re-adding <member>/tests), Scan B with ``include_tests=False``
        (prod-only, §10 R6 reading b)."""
        source = (_TESTS_DIR / _COMMS_FOOTER).read_text(encoding="utf-8")
        modes = _parse_prod_trees_modes_in(source)
        found = modes if modes else "NONE (un-migrated — the RIGHT reason to be RED at HEAD)"
        assert True in modes and False in modes, (
            "test_comms_footer must migrate BOTH scans onto parse_production_trees — Scan A with "
            "include_tests=True and Scan B with include_tests=False (§10 R6). Found include_tests "
            f"literals across its parse_production_trees calls: {found}. A 'DEFAULT'/'NON_LITERAL' "
            "where a literal is needed means the mode is not pinnable — pass the literal True/False "
            "the design specifies, or raise the call-placement with the lead."
        )

    def test_each_include_tests_mode_binds_to_a_DISTINCT_scan_scope(self) -> None:
        """⛔ §12.4 THE BINDING (the delta-adversary residual, now PINNED not hand-checked): the two
        modes must live in TWO DISTINCT scan scopes, so a mode-swap that NARROWS Scan A (giving it
        ``include_tests=False``) cannot hide by collapsing both scans into one migration. RED at HEAD
        (no calls → no scopes). Catches: both scans collapsed into one scope, a mode dropped, a mode
        appearing only where the other already is. Does NOT catch the pure A↔B purpose swap (stated
        bound in the class docstring — the cold-audit hand-check)."""
        scopes = _comms_footer_scan_modes_by_scope()
        scopes_with_true = {scope for scope, modes in scopes.items() if True in modes}
        scopes_with_false = {scope for scope, modes in scopes.items() if False in modes}
        assert scopes_with_true and scopes_with_false, (
            "comms_footer does not carry BOTH include_tests modes across its parse_production_trees "
            f"call scopes (True in {sorted(scopes_with_true)}, False in {sorted(scopes_with_false)}). "
            "RED at HEAD (un-migrated); after migration Scan A must consume True and Scan B False."
        )
        bindable = any(
            scope_true != scope_false
            for scope_true in scopes_with_true
            for scope_false in scopes_with_false
        )
        assert bindable, (
            "both include_tests modes live in the SAME single scan scope "
            f"({sorted(scopes_with_true & scopes_with_false)}) — the two comms_footer scans (A: "
            "prod+tests, B: prod-only) were collapsed into ONE migration, so a mode-swap in either "
            "is invisible. Each scan must consume its own mode in its OWN scope (§12.4). Prefer a "
            "distinctly-named nullary helper per scan so a pin can bind the mode to the scan by name."
        )


# ---------------------------------------------------------------------------- #
# §12.7.2 / §12.8 — THE PARSE-ADOPTER SKIP SET IS A CHECKED VARIABLE (finding #349).
#
# Layer 3's fixture-consumer pin (TestSharingProvenByMutation) SKIPS adopters with no
# nullary workspace-tree @pytest.fixture. Before §12.7 that skip was SILENT — the exact
# hole delta-adversary-asub-4 found: a fixtureless adopter (backoff) whose private
# whole-workspace scan NO layer asserts on passed the whole contract 44/4-skip,
# byte-identical to correct. These pins promote the skip to allowlist-the-safe: the skip
# is legal ONLY for an _ASUB_PARSE_SKIP entry, each skip is proven not to parse the tree
# UNROUTED, and a dead entry self-cleans.
#
# ⚠ §12.8 RE-SOURCING (reviser-asub-6): the "does not parse UNROUTED" check runs on L1's
# RUNTIME observation (report.escapes at the builtins.compile chokepoint), NOT the static
# _all_workspace_parse_sites detector. delta-adversary-asub-5 defeated the static detector
# with a SPLIT-LEG private parse (source in a nullary helper, ast.parse loop in the
# consumer) that produces an AST but names no whole-workspace source in one function. L1 is
# at the compile chokepoint, so it records the escape regardless of spelling (split-leg,
# comprehension, os.walk+parse, an alias). Reuses L1's install_parse_guard / report.escapes /
# report.require_observations (§12.3), the per-file budget (§12.8.3), _workspace_tree_fixtures,
# and the _ALLOWED_WHOLE_TREE_CLONE_FILES dead-entry idiom — no new scanner (operator: REUSE
# > REINVENT). _all_workspace_parse_sites STAYS as L1's OWN coverage instrument
# (test_every_whole_workspace_parse_site_was_watched_executing) — just not the skip-coverage source.
# ---------------------------------------------------------------------------- #


class TestTheParseSkipSetIsACheckedVariable:
    """⛔ §12.7.2 / §12.8 — the SKIP is a CHECKED VARIABLE, not a silent exemption. Four coupled
    guards partition the ``_MIGRATION_SET`` universe with no silent third category:

      ADOPTERS-WITH-A-FIXTURE (Layer 3 drives them) ∪ _ASUB_PARSE_SKIP (this class checks each is
      a real, fixtureless adopter the RUNTIME guard OBSERVES routing — no unrouted whole-workspace
      parse beyond its declared budget) ∪ (anything else that parses → an L1 escape).

    THREAT MODEL (§12.7.1, stated so the verdicts follow mechanically): A-SUB guards the
    PARSE (``parse_production_trees``); a file the guard OBSERVES parsing the whole workspace
    UNROUTED (a site whose escapes span >=2 MEMBERS, §12.8.3) is either a mis-classified adopter or a
    false "no private parse" claim — RED for every spelling whose source the discriminator can
    ATTRIBUTE (L1 is at the ``compile`` chokepoint; the members-spanned discriminator keys on each
    escape's resolved ``.member``). TWO spellings are OUT OF SCOPE, pinned honestly as KNOWN BOUNDS
    (not closed here): a NON-parsing tree-walk (#349, :class:`TestAsubNonParsingTreeWalkKnownBound349`)
    and a bytes/normalized-source whole-workspace parse whose source resolves to ``member=""`` (#351,
    :class:`TestAsubBytesNormalizedSourceParseIsAKnownBound351`; §13 operator ruling)."""

    def test_the_skip_set_is_non_empty_and_scoped_to_the_migration_set(self) -> None:
        """⛔ ANTI-VACUITY + SCOPING: the skip set must be NON-EMPTY (else the checked-variable
        pins below iterate zero entries and 'pass' by measuring nothing), and every entry must
        be a declared adopter (``_MIGRATION_SET``) — Layer 3 only iterates ``_MIGRATION_SET``, so
        a skip entry outside it governs nothing and is a mistake, not a checked variable."""
        assert _ASUB_PARSE_SKIP, (
            "_ASUB_PARSE_SKIP is empty — the skip-set checked-variable pins have zero cases and "
            "certify nothing. If Layer 3 skips an adopter, it MUST be an evidence-backed entry here."
        )
        stray = sorted(name for name in _ASUB_PARSE_SKIP if name not in _MIGRATION_SET)
        assert not stray, (
            f"these _ASUB_PARSE_SKIP entries are not in _MIGRATION_SET (so Layer 3 never reaches a "
            f"skip decision for them — the entry governs nothing): {stray}. The skip set is the "
            "SUBSET of declared adopters that expose no nullary workspace-tree fixture."
        )

    def test_no_skip_set_file_parses_the_tree_unrouted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """⛔ THE CHECKED VARIABLE (§12.8, re-sourced from the STATIC detector to L1's RUNTIME
        observation). For EACH ``_ASUB_PARSE_SKIP`` file, drive its scan candidates
        (:func:`_drivable_scan_candidates`) under the armed parse-guard and require, per file:
        (1) the guard OBSERVED the file parse at all (anti-vacuity #136 — an un-run skip is a silent
        false clear, §12.8.2), and (2) the file produced NO unrouted WHOLE-WORKSPACE parse beyond
        its declared budget (default 0: it ROUTES through ``parse_production_trees``).

        WHY RUNTIME, NOT THE STATIC ``_all_workspace_parse_sites`` (§12.8, finding #349 continued):
        the static detector keys on a parse-primitive co-occurring with a whole-workspace SOURCE
        NAME in ONE function — a 3-name hand-list. delta-adversary-asub-5 defeated it with a
        SPLIT-LEG private parse (``_production_python_files()`` → ``production_sources()`` in one
        nullary helper, the ``ast.parse`` loop in a consumer at ``test_backoff_seam.py:780``): an
        IN-SCOPE parse (it produces an AST) that names no whole-workspace source in one function,
        so the static shape is blind. L1's guard is at the ``builtins.compile`` chokepoint, so it
        records the escape regardless of spelling — split-leg, comprehension, ``os.walk``+parse, an
        alias ``ap = ast.parse``. The skip now means "confirmed ROUTED, CHECKED at runtime", never
        "the reviser decided".

        THE WHOLE-WORKSPACE vs SINGLE-PACKAGE DISCRIMINATOR (§12.8.3) is MEMBERS-SPANNED
        (:func:`_whole_workspace_escape_sites`): a site whose escapes span >=2 DISTINCT workspace
        MEMBERS is a tree ENUMERATION; a single-PACKAGE scan (many files, ONE member — a §7
        non-adopter) or a single-file parse spans ONE and is EXCLUDED. ⚠ MEASURED, not a raw
        compile-COUNT (a reviser-asub-6 refinement of §12.8.3, REPORT-reviser-asub-6.md
        §satisfiability): ``test_secret_typing``'s lorerunes single-package scans compile >=2
        lorerunes FILES at one site, so a count>=2 proxy would false-flag them as whole-workspace on
        a CORRECT migrated build — a C-DEF. The member is read from each escape's ``.member`` (the
        member of the compiled SOURCE, resolved from source content since the survivor's
        ``ast.parse(path.read_text())`` names no ``filename`` — the escape-record extension §12.8.3
        authorizes, in its useful form).

        THE BOUND, stated so it is NOT a false clear (§12.8.4 / §13 operator ruling 2026-08-10): L1's
        runtime observation + the members-spanned discriminator CLOSE every HONEST parsing spelling
        whose compiled SOURCE the discriminator can ATTRIBUTE to a member — ``rglob`` /
        ``production_sources`` / the delta-adversary-asub-5 split-leg TEXT source (a str
        byte-identical to a stored workspace ``.py`` → resolves to its member → RED). TWO spellings
        are pinned honestly as KNOWN BOUNDS, NOT closed here: (1) a NON-parsing tree-walk (no AST, no
        ``compile`` chokepoint), #349, :class:`TestAsubNonParsingTreeWalkKnownBound349`; and (2) a
        bytes/normalized-source whole-workspace parse whose compiled source the member-resolution
        cannot key (``member=""``, dropped fail-open by :func:`_whole_workspace_escape_sites`), #351,
        :class:`TestAsubBytesNormalizedSourceParseIsAKnownBound351` — an adversarial-only,
        trivial-importance test-infra bound the operator ACCEPTED (§13). A split-leg TEXT-source
        PARSE is NOT a bound (L1 observes it, the discriminator attributes it → RED).

        RED at HEAD: the guard is unbuilt → the accessor raises the honest "build the guard" RED;
        once built, on an un-migrated tree the skip files parse UNROUTED → RED naming them. GREEN on
        a migrated build (each skip file routes → 0 unrouted whole-workspace sites, observed). The
        ``ACCESSOR/AST BEFORE ARM`` discipline holds: candidates are enumerated (which parses their
        sources) BEFORE the guard wraps ``builtins.compile``."""
        # Enumerate BEFORE arming — the AST parse of each skip file's source (and its import) must
        # not be recorded as an escape (the class-level ACCESSOR/AST-BEFORE-ARM discipline).
        candidates_by_skip = {
            skip_file: _drivable_scan_candidates(skip_file) for skip_file in _ASUB_PARSE_SKIP
        }
        install = _install_parse_guard_fn()
        report = install(monkeypatch)
        assert getattr(report, "armed", False), (
            "the parse-guard did not ARM — the skip-coverage checked variable cannot certify "
            "anything. Build parse_production_trees (its sanctioned frame) + the runtime guard (§12.3)."
        )
        unobserved: list[str] = []
        over_budget: list[str] = []
        dead_declarations: list[str] = []
        for skip_file, candidates in candidates_by_skip.items():
            budget = _ASUB_PARSE_SKIP[skip_file].unrouted_whole_workspace_budget
            intercepted_before = report.intercepted
            escapes_before = len(report.escapes)
            for _name, derive in candidates:
                try:
                    derive()
                except Exception:  # noqa: BLE001 — a candidate that raises still parsed BEFORE it raised
                    continue
            file_escapes = report.escapes[escapes_before:]
            if report.intercepted == intercepted_before:
                # The guard saw NO compile at all while driving this file — its "no unrouted parse"
                # verdict is BLINDNESS, not cleanliness (#136 / §12.8.2). Per-file anti-vacuity.
                unobserved.append(skip_file)
                continue
            observed_sites = _skip_files_parsing_whole_workspace(file_escapes).get(skip_file, set())
            verdict = _skip_budget_verdict(len(observed_sites), budget)
            if verdict == "over":
                over_budget.append(
                    f"{skip_file}: {len(observed_sites)} unrouted whole-workspace parse site(s) "
                    f"{sorted(observed_sites)} > declared budget {budget}"
                )
            elif verdict == "dead":
                dead_declarations.append(
                    f"{skip_file}: declared budget {budget} but the guard observed only "
                    f"{len(observed_sites)} unrouted whole-workspace parse site(s)"
                )
        assert not unobserved, (
            "per-file ANTI-VACUITY (#136 / §12.8.2): the guard OBSERVED NO compile at all while "
            "driving these _ASUB_PARSE_SKIP files' scan candidates, so its 'no unrouted parse' "
            f"verdict for them is BLINDNESS, not cleanliness:\n  {unobserved}\n"
            "Each skip file must expose its ROUTED whole-workspace parse as a drivable nullary "
            "candidate (a module-level `def _scan()` or a self-only `test_...` method that calls "
            "parse_production_trees), so the guard can watch it route — else the skip is an "
            "unverified false clear (the #349 hole one level down)."
        )
        assert not over_budget, (
            "these _ASUB_PARSE_SKIP files parsed the WHOLE WORKSPACE UNROUTED beyond their declared "
            "budget (a private production_sources()/os.walk/comprehension + ast.parse/compile with "
            "NO parse_production_trees frame — the delta-adversary-asub-5 split-leg survivor, ANY "
            "spelling):\n  " + "\n  ".join(over_budget) + "\n"
            "Route each through parse_production_trees (then L1 records SANCTIONED, not an escape, and "
            "the budget-0 skip passes), OR — if a whole-workspace unrouted parse is genuinely "
            "justified — raise that file's _ParseSkip.unrouted_whole_workspace_budget WITH an "
            "evidence reason naming the site."
        )
        assert not dead_declarations, (
            "these _ASUB_PARSE_SKIP files declare a whole-workspace unrouted-parse budget the guard "
            "never substantiates (a DEAD declaration — the _ALLOWED_* dead-entry idiom, §12.8.3):\n  "
            + "\n  ".join(dead_declarations) + "\n"
            "Lower the budget to what L1 actually observes (0 if the file now routes) — a stale "
            "over-budget silently exempts a future unrouted parse up to the declared count."
        )
        report.require_observations("driving every _ASUB_PARSE_SKIP file's scan under the parse guard")

    def test_the_skip_coverage_discrimination_fires_and_discriminates(self) -> None:
        """⛔ BUILD-INDEPENDENT CONTROLS on the §12.8.3 RUNTIME discrimination logic — the exact
        primitives the main pin runs (:func:`_skip_files_parsing_whole_workspace` and
        :func:`_skip_budget_verdict`), driven by SYNTHETIC escapes so a GREEN main pin on a migrated
        build is never a "filter matches nothing" false pass (the C1 'passed for the wrong reason').
        A synthetic escape is any object carrying ``.site`` + ``.member``, so no guard is needed.

        NEGATIVE 1 is the C-DEF this refinement fixes (REPORT-reviser-asub-6.md §satisfiability): a
        single-PACKAGE scan compiles MANY files at one site but spans ONE member — a raw count>=2
        proxy would false-flag it; the members-spanned discriminator must EXCLUDE it."""

        class _Escape:
            def __init__(self, site: str, member: str) -> None:
                self.site = site
                self.member = member

        a_skip = next(iter(_ASUB_PARSE_SKIP))
        ws_site = f"loremaster/tests/{a_skip}:780 in _evil_private_scan()"

        # POSITIVE — a site whose escapes span >=2 MEMBERS is a whole-workspace ENUMERATION → flagged.
        flagged = _skip_files_parsing_whole_workspace(
            [_Escape(ws_site, "loremaster"), _Escape(ws_site, "lorerunes"), _Escape(ws_site, "loresigil")]
        )
        assert flagged.get(a_skip) == {ws_site}, (
            "a skip file whose escapes at ONE call-site span >=2 members (a tree enumeration, the "
            f"split-leg survivor) was NOT flagged as whole-workspace — the discriminator is blind: {flagged}."
        )

        # NEGATIVE 1 — a single-PACKAGE scan (MANY compiles at a site, ALL ONE member) is NOT
        # whole-workspace (the lorerunes-scan C-DEF a count>=2 proxy would have false-flagged).
        pkg_site = f"loremaster/tests/{a_skip}:1313 in _lorerunes_only_scan()"
        single_pkg = _skip_files_parsing_whole_workspace(
            [_Escape(pkg_site, "lorerunes"), _Escape(pkg_site, "lorerunes"), _Escape(pkg_site, "lorerunes")]
        )
        assert not single_pkg, (
            "a single-PACKAGE scan (many files, ONE member) was charged as a whole-workspace enumeration "
            f"— the members-spanned discriminator must require >=2 DISTINCT members: {single_pkg}."
        )

        # NEGATIVE 2 — >=2 members whose call-site is NOT a skip file are not attributed to the skip set.
        outsider = _skip_files_parsing_whole_workspace(
            [
                _Escape("loremaster/tests/_logging_fixtures.py:1 in parse_production_trees()", "loremaster"),
                _Escape("loremaster/tests/_logging_fixtures.py:1 in parse_production_trees()", "lorerunes"),
            ]
        )
        assert not outsider, (
            "an escape whose call-site is NOT an _ASUB_PARSE_SKIP file was attributed to the skip set "
            f"— the filter keys on the wrong thing (must match _ASUB_PARSE_SKIP membership): {outsider}."
        )

        # BOTH-WAYS budget adjudication (§12.8.3), the exact verdict fn the main pin branches on:
        assert _skip_budget_verdict(1, 0) == "over", "1 unrouted whole-workspace site vs budget 0 -> OVER."
        assert _skip_budget_verdict(0, 1) == "dead", "budget 1 with 0 observed -> DEAD over-declaration."
        assert _skip_budget_verdict(0, 0) is None, "0 observed against budget 0 (a routed skip) must be OK."
        assert _skip_budget_verdict(2, 2) is None, "an exact-budget declaration must be OK."

    def test_the_parse_skip_allowlist_carries_no_dead_entries(self) -> None:
        """⛔ DEAD-ENTRY pin (the ``_ALLOWED_WHOLE_TREE_CLONE_FILES`` /
        ``test_the_allowlist_carries_no_dead_entries`` idiom): every ``_ASUB_PARSE_SKIP`` entry
        must still EARN its exemption today. An entry is DEAD — a silent exemption for whatever
        lands there next — if the file no longer exists, OR it left ``_MIGRATION_SET`` (no longer a
        declared adopter), OR it now exposes a nullary workspace-tree ``@pytest.fixture`` (Layer 3
        would then DRIVE it, so the skip exemption is unused). Each dead entry → RED, forcing its
        removal. Self-cleaning: the day a skip file gains a fixture, its entry goes dead here."""
        dead: list[str] = []
        for name in sorted(_ASUB_PARSE_SKIP):
            if not (_TESTS_DIR / name).exists():
                dead.append(f"{name}: file no longer exists")
            elif name not in _MIGRATION_SET:
                dead.append(f"{name}: no longer a declared adopter (_MIGRATION_SET)")
            elif _workspace_tree_fixtures(name):
                fixtures = sorted(fn for fn, _ in _workspace_tree_fixtures(name))
                dead.append(
                    f"{name}: now exposes nullary workspace-tree fixture(s) {fixtures} — Layer 3 "
                    "drives it, so the skip exemption is unused"
                )
        assert dead == [], (
            "these _ASUB_PARSE_SKIP entries no longer earn their exemption (dead exemptions):\n  "
            + "\n  ".join(dead)
            + "\nDelete each — a stale skip entry silently exempts whatever is added to that file "
            "next (the same self-cleaning discipline as _ALLOWED_WHOLE_TREE_CLONE_FILES)."
        )


# ---------------------------------------------------------------------------- #
# §12.7.3 — THE NON-PARSING TREE-WALK IS A KNOWN BOUND (finding #349).
# Per CLAUDE.md "WHEN YOU CANNOT CLOSE A HOLE, PIN IT" (#137/#138 pin-the-miss idiom).
# ---------------------------------------------------------------------------- #


class TestAsubNonParsingTreeWalkKnownBound349:
    """⛔ PIN THE MISS (§12.7.3, finding #349; the ``test_backoff_seam.TestKnownBoundsOfThisInstrument``
    / #137 / #138 idiom). A-SUB consolidates the PARSER (``parse_production_trees``) at the ``compile``
    chokepoint (§12.2). A NON-parsing tree-walk — one that walks directory entries / checks FILENAMES
    and NEVER calls ``ast.parse``/``compile`` — produces no AST and reaches no chokepoint, so it is OUT
    OF SCOPE by definition (§12.7.1), not an undetected defect.

    Unlike ``compile`` (the ONE primitive every AST production funnels through), tree-walking has NO
    single chokepoint (``os.walk`` / ``os.scandir`` / ``os.listdir`` / ``Path.iterdir`` / ``glob`` /
    ``rglob`` / a hardcoded file list needs no iteration at all). Enumerating walk spellings IS the
    enumerate-the-forbidden pattern this whole file exists to kill — it is round 6. So the hole is
    PINNED, not chased.

    RESIDUAL harm is DRIFT and is already mostly mitigated: a non-parsing walk only drifts (misses a new
    workspace member) if it HARDCODES its roots; a walk taking roots from
    ``workspace_roots``/``production_sources`` (already ONE implementation, §7) does not drift. The one
    known hardcoded-root instance (comms_footer Scan B's 4-tuple) is being migrated (§10 Ruling 6).

    RE-OPEN TRIGGERS (§12.7.3, the deferral law): (a) a hardcoded-root non-parsing walk is found to have
    caused a REAL drift (a member silently missed); (b) the threat model changes — untrusted contributors
    / a hosted deployment (security enters scope, the #138 trigger); (c) the repo gains CI + a
    root-enumeration audit (#285). At a trigger, the cheapest honest candidate is a NARROW
    member-root-path-literal scan, NOT an ``os.scandir`` chokepoint.

    IF YOU CLOSED THIS HOLE DELIBERATELY, delete this pin and say so in the commit."""

    #: A NON-parsing whole-tree walk: os.walk over roots, .py FILENAME check, NEVER ast.parse/compile.
    _NONPARSING_WALK = (
        "import os\n"
        "def _scan():\n"
        "    hits = []\n"
        "    for base in ROOTS:\n"
        "        for dirpath, _dirs, files in os.walk(base):\n"
        "            for name in files:\n"
        "                if name.endswith('.py'):\n"
        "                    hits.append(name)\n"
        "    return hits\n"
    )

    def test_asub_nonparsing_tree_walk_is_a_KNOWN_BOUND_349(self) -> None:
        """⛔ KNOWN BOUND #349: A-SUB's PARSE-keyed detectors do NOT flag a non-parsing tree-walk,
        and MUST NOT be expected to. Reddens the day someone teaches them to (then delete the pin)."""
        walk_tree = ast.parse(self._NONPARSING_WALK)
        call_names = _call_names_in(walk_tree)

        # It IS genuinely a whole-tree walk (positive anti-triviality): it walks the tree...
        assert "walk" in call_names, "the KNOWN-BOUND fixture is not a tree walk — control mis-built"
        # ...and it is genuinely NON-parsing: it reaches NO parse primitive, so it is structurally
        # invisible to L1's `builtins.compile` chokepoint (no AST is ever produced from it).
        assert not (call_names & _PARSE_PRIMITIVE_CALL_NAMES), (
            "the KNOWN-BOUND fixture calls a parse primitive — it is NOT the non-parsing walk the "
            "bound is about (a PARSING walk is IN scope, §12.7.1). Control mis-built."
        )

        # (1) L2's offender lint (the whole-tree PARSE-clone detector) does NOT flag it — a
        # non-parsing walk is not a whole-tree PARSE. This is the KNOWN BOUND: it goes RED if a
        # future author broadens L2 to catch non-parsing walks (closing the hole → delete this pin).
        assert _whole_tree_parse_offenders_in(walk_tree) == [], (
            "A-SUB's L2 offender lint now FLAGS a NON-parsing os.walk tree-walk. KNOWN BOUND #349 — "
            "A-SUB consolidates the PARSER (parse_production_trees); a non-parsing tree-walk has no "
            "chokepoint analogous to `compile`, and enumerating walk spellings is the defeated "
            "enumerate-the-forbidden pattern. This is out of the parser policy's scope (§12.7.1), not "
            "an undetected defect. If you added detection deliberately, DELETE this pin and say so "
            "(re-open triggers: real drift found / threat model changed / CI + root-audit #285)."
        )

        # POSITIVE CONTROL — the detector is NOT simply broken: the PARSING variant of the same
        # whole-tree walk (rglob directory source + read_text + ast.parse) IS flagged by L2. So the
        # bound is precisely 'NON-parsing', not 'the detector never fires'.
        parsing_variant = (
            "import ast\n"
            "def _scan():\n"
            "    trees = {}\n"
            "    for base in ROOTS:\n"
            "        for p in base.rglob('*.py'):\n"
            "            trees[p] = ast.parse(p.read_text())\n"
            "    return trees\n"
        )
        assert _whole_tree_parse_offenders_in(ast.parse(parsing_variant)) == ["_scan"], (
            "the PARSING whole-tree walk was NOT flagged by L2 — the detector is broken, so the "
            "KNOWN-BOUND assertion above certifies nothing (it would pass on any input). The bound "
            "must be 'non-parsing escapes', not 'the detector never fires'."
        )


# ---------------------------------------------------------------------------- #
# §13 OPERATOR RULING (2026-08-10) — THE BYTES/NORMALIZED-SOURCE WHOLE-WORKSPACE
# PARSE IS A KNOWN BOUND (finding #351). Per CLAUDE.md "WHEN YOU CANNOT CLOSE A HOLE,
# PIN IT" (#137/#138 pin-the-miss idiom). DISTINCT from #349 (a non-parsing walk).
# ---------------------------------------------------------------------------- #


class TestAsubBytesNormalizedSourceParseIsAKnownBound351:
    """⛔ PIN THE MISS (§13 operator ruling 2026-08-10, finding #351; the #137/#138 /
    :class:`TestAsubNonParsingTreeWalkKnownBound349` idiom). A-SUB's skip-coverage discriminator
    (:func:`_whole_workspace_escape_sites`) tells a WHOLE-WORKSPACE enumeration from a legit
    single-package scan by the MEMBER each escaped compile belongs to, resolved from the compiled
    SOURCE TEXT (the survivor's ``ast.parse(path.read_text())`` names no ``filename``, §12.8.3). A
    routed-but-private whole-workspace parse whose source the resolution CANNOT key —
    ``ast.parse(path.read_bytes())`` (a bytes source is not a str map key) or
    ``ast.parse(read_text()+normalize)`` (a transformed str byte-mismatches the stored file text) —
    yields ``member=""`` for EVERY escape, and :func:`_whole_workspace_escape_sites` drops
    empty-member escapes (``if member:`` — fail-OPEN), so the site never spans >=2 members and is
    NOT flagged. Such a parse is IN-SCOPE (it produces ASTs, so L1 records it) — but the
    discriminator's reach over the ATTRIBUTION is a hidden constant, and this spelling escapes it
    (delta-adversary-asub-6: 117 compiles recorded, all ``member=""`` → 0 flagged → GREEN).

    THE OPERATOR ACCEPTED THIS AS A BOUND (design §13 "OPERATOR SIMPLIFICATION"): trivial-importance
    test-infra (the anti-dup pins), an ADVERSARIAL-ONLY survivor, OUTSIDE the honest-developer threat
    model — L1 + the discriminator CLOSE every HONEST parsing spelling whose source is attributable:
    ``rglob`` / ``production_sources`` / the delta-adversary-asub-5 split-leg TEXT source (a str
    byte-identical to a stored workspace ``.py`` → resolves to its member → RED). It is NOT chased: a
    fail-CLOSED member-attribution (flagging any unattributable workspace-.py-site escape) could
    re-open the single-package lorerunes C-DEF the §12.8.3 members-spanned discriminator exists to
    avoid, so closing it is a DESIGN question, not a patch.

    RE-OPEN TRIGGERS (§13 / the deferral law): (a) a REAL drift is found caused by an
    unattributable-source whole-workspace parse (a member silently missed); (b) the threat model
    changes — untrusted contributors / a hosted deployment (security enters scope, the #138 trigger);
    (c) the repo gains CI + a root-enumeration audit (#285). At a trigger the honest candidate is a
    SOURCE-CONTENT member-resolver (decode bytes before the source-map lookup; fail-closed on an
    unattributable workspace-.py-site escape, routed through CONTRACT/design) — NOT an enumeration of
    source spellings (that is the defeated enumerate-the-forbidden pattern this whole file kills).

    ⚠ BOUND OF THIS PIN ITSELF (#137/#138 discipline — state the instrument's own reach): it pins
    the DISCRIMINATOR's fail-open disposition build-independently (synthetic escapes, no guard), so
    it reddens if the bound is closed AT THE DISCRIMINATOR (made fail-closed on empty-member escapes
    at a workspace site). A closure at the GUARD instead (a robust member-resolution that decodes a
    bytes/transformed workspace source so it never emits an empty-member escape) leaves this synthetic
    pin GREEN — at that closure, replace this with a guard-driven end-to-end pin and say so.

    IF YOU CLOSED THIS HOLE DELIBERATELY, delete this pin and say so in the commit."""

    def test_asub_bytes_normalized_whole_workspace_parse_is_a_KNOWN_BOUND_351(self) -> None:
        """⛔ KNOWN BOUND #351: a bytes/normalized-source whole-workspace parse in a skip file is out
        of the members-spanned discriminator's reach (``member=""`` for every escape → dropped
        fail-open) → NOT flagged. Reddens the day the discriminator is made fail-closed on
        unattributable escapes (then delete this pin). Build-independent (synthetic escapes on the
        CONTRACT's own :func:`_whole_workspace_escape_sites` / :func:`_skip_files_parsing_whole_workspace`
        helpers, the ``test_the_skip_coverage_discrimination_fires_and_discriminates`` idiom), so it
        is GREEN today: it pins the ACCEPTED disposition, not a build."""

        class _Escape:
            """A synthetic guard escape carrying only ``.site`` + ``.member`` — the shape
            :func:`_whole_workspace_escape_sites` reads (no guard build needed)."""

            def __init__(self, site: str, member: str) -> None:
                self.site = site
                self.member = member

        message = (
            "KNOWN BOUND #351: a bytes/normalized-source whole-workspace parse in a skip file is out "
            "of the members-spanned discriminator's reach; L1 catches every HONEST parsing spelling "
            "(rglob/production_sources/split-leg text); if you closed this deliberately, delete this "
            "pin and say so"
        )
        skip_file = next(iter(_ASUB_PARSE_SKIP))
        ws_site = f"loremaster/tests/{skip_file}:780 in _bytes_source_whole_workspace_scan()"

        # (1) THE BOUND — a whole-workspace parse via a bytes/normalized source spans the whole
        # workspace in REALITY, but every escape carries member="" (unattributable source), so
        # _whole_workspace_escape_sites DROPS them all (fail-open) → the site is NOT flagged → the
        # per-file verdict is GREEN, indistinguishable from a correctly routed build.
        unattributable = [_Escape(ws_site, "") for _ in range(6)]  # 6 compiles, ALL member=""
        assert _whole_workspace_escape_sites(unattributable) == set(), message
        skip_flagged = _skip_files_parsing_whole_workspace(unattributable)
        assert skip_flagged == {}, message
        assert _skip_budget_verdict(len(skip_flagged.get(skip_file, set())), 0) is None, message

        # (2) POSITIVE CONTROL (anti-triviality) — the discriminator is NOT simply broken: the SAME
        # site with ATTRIBUTED members (an honest rglob/read_text spelling L1's source map keys) IS
        # flagged. So the bound is precisely "member='' (unattributable source)", not "the
        # discriminator never fires" — the #349 pin's positive-control discipline.
        attributed = [_Escape(ws_site, "loremaster"), _Escape(ws_site, "lorerunes")]
        assert _whole_workspace_escape_sites(attributed) == {ws_site}, (
            "the members-spanned discriminator did NOT flag a whole-workspace site whose escapes span "
            ">=2 ATTRIBUTED members — it is broken, so the KNOWN-BOUND assertion above certifies "
            "nothing (it would pass on any input)."
        )
        assert _skip_files_parsing_whole_workspace(attributed).get(skip_file) == {ws_site}, (
            "an attributed whole-workspace escape at a skip-file site was NOT attributed to the skip "
            "set — the positive control is broken, so the bound assertion certifies nothing."
        )

        # (3) POSITIVE CONTROL — the bound is REAL: a bytes source and a normalized source are each
        # an IN-SCOPE parse (produce an ast.Module), yet the §12.8.3 source-text member resolution (a
        # str-keyed {source: member} map, per _install_parse_guard_fn's REQUIRED API) returns "" for
        # both — which is exactly WHY their escapes carry member="".
        def resolve_member(source: object, source_to_member: dict[str, str]) -> str:
            """The §12.8.3 resolution in its specified form: key the compiled SOURCE against a
            str-keyed ``{source: member}`` map built at arm time; a non-str (bytes) source, or a str
            source byte-mismatching the stored text, keys nothing → "". Mirrors the guard's
            ``if not member and isinstance(source, str): member = source_map.get(source, "")``."""
            return source_to_member.get(source, "") if isinstance(source, str) else ""

        stored_text = "x = 1\r\n"  # a workspace .py file's text AS STORED (CRLF), keyed at arm time
        source_to_member = {stored_text: "loremaster"}

        bytes_source = stored_text.encode("utf-8")  # read_bytes() — a bytes source
        assert isinstance(ast.parse(bytes_source), ast.Module), (
            "ast.parse(bytes) did NOT produce an AST — the bound's premise (bytes IS an in-scope "
            "parse) is false; re-derive."
        )
        assert resolve_member(bytes_source, source_to_member) == "", message

        normalized_source = stored_text.replace("\r\n", "\n")  # read_text()+normalize (strip CRLF)
        assert isinstance(ast.parse(normalized_source), ast.Module), (
            "ast.parse(normalized) did NOT produce an AST — the bound's premise is false; re-derive."
        )
        assert resolve_member(normalized_source, source_to_member) == "", message

        # ...and the ATTRIBUTABLE source (str, byte-identical to the stored text) DOES resolve — so
        # resolve_member is not a stub that always returns "" (the positive control's own control).
        assert resolve_member(stored_text, source_to_member) == "loremaster", (
            "the source-text resolver returned '' for a str source byte-identical to the stored file "
            "— it is broken, so the member='' assertions above certify nothing."
        )

