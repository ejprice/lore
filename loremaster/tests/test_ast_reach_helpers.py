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

MUTATION / PROVE-SHARING (F4's own requirement; adversary-asub-b A-SUB-1/-2/-3/-4/-5)
------------------------------------------------------------------------------------
"Change the shared derivation → every dependent pin reddens; a caller that stays green is
a private copy wearing the shared name." The adversary (``REPORT-adversary-asub-b``, graded
``405d321``) proved the STATIC-only sharing pin waved through a FIX-NOTHING build (16/0) — 3
of 4 files "migrated" by an UNUSED ``import … as _asub_route  # noqa: F401``, ``_SCANNED_MEMBERS``
and three private ``rglob`` clones all surviving. So the sharing property is pinned in FOUR
complementary ways (design §9.5/§9.6/§9.7, IDIOM 1):

* **import-is-USED, not present** — :class:`TestTheMigrationSetRoutesThroughTheSharedHelpers`
  asserts each migration file CALLS ``parse_production_trees`` (spelling-agnostic — a bare
  ``from …import…`` unused, the A-SUB-1 build, is not consolidation);
* **a DERIVED anti-dup scan** — :class:`TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist`
  reuses the ``test_retry_seam._unseamed_sdk_call_sites`` OFFENDER shape: enumerate EVERY
  whole-tree ``rglob("*.py")+ast.parse`` clone from the tree, subtract an evidence-backed
  SAFE allowlist, NAME the rest (deny-by-default, allowlist-the-SAFE — the CORRECT pattern the
  A-SUB-2 build wrongly dropped as "enumerate-the-forbidden");
* **the member hand-lists are retired** — :class:`TestTheMemberHandListsAreRetired` asserts
  ``_SCANNED_MEMBERS`` is gone from the migrated files (A-SUB-4, the real #291-shaped
  consolidation);
* **∀-MUTATION over the LIVE-DERIVED adopter set** — :class:`TestSharingProvenByMutation`
  drops the shared parser (returns ``{}``) via ``_rebind_everywhere`` (reused from
  ``test_store_seam_one_derivation`` per §9.6; rebinds BY IDENTITY across ``sys.modules`` so it
  reaches a FROM-import adopter — the single-module ``monkeypatch`` the adversary flagged
  (A-SUB-3/-5) does NOT, *verified empirically this cycle*) and asserts EVERY live adopter's
  OWN coverage reddens FOR EACH. The adopter set is re-derived LIVE each run (§9.1
  meta-recursion: the ∀'s reach is a CHECKED VARIABLE, never a fixture constant), guarded
  fail-closed against a vacuous empty parametrization.

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
from typing import cast

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TESTS_DIR = Path(__file__).resolve().parent

#: The ∀-scan files F4 migrates onto the shared helpers (design §5 Wave-1 A-SUB writable
#: set). The sharing pin is scoped to exactly these — the substrate serves the ∀-scan
#: FAMILY, not every ``rglob`` file in the tree (design §3 A-SUB bound: some files parse
#: for unrelated reasons; migrating those is a flagged worklist item, out of scope).
_MIGRATION_SET: tuple[str, ...] = (
    "test_anchored_pattern_seam.py",
    "test_backoff_seam.py",
    "test_secret_typing.py",
    "test_secret_leak_vectors.py",
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


def _has_tree_parser_clone(tree: ast.Module) -> list[str]:
    """Names of functions in ``tree`` that hand-roll the production-tree parse loop —
    the clone signature is a body that calls BOTH ``.rglob(...)`` AND ``ast.parse(...)``
    AND ``.read_text(...)`` (a synthetic-source ``ast.parse('...')`` control carries none
    of the file-walk calls, so it is not flagged)."""
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        calls = {
            (n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", None))
            for n in ast.walk(node)
            if isinstance(n, ast.Call)
        }
        if {"rglob", "parse", "read_text"} <= calls:
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


def _live_adopters() -> list[str]:
    """LIVE-DERIVED: every ``test_*.py`` in this tree that CALLS ``parse_production_trees``.

    ⚠ THE META-RECURSION GUARD (design §9.1): the ∀-mutation's reach IS this set, and it is
    RE-DERIVED from the tree every run — never a fixture constant or a hand-list, or the ∀
    would be the trap it exists to catch, one level up. EMPTY at HEAD (``641f758``): no file
    calls the (unbuilt) helper, so :class:`TestSharingProvenByMutation`'s non-emptiness guard
    is RED, and the parametrized ∀ cannot pass vacuously."""
    adopters: list[str] = []
    for path in sorted(_TESTS_DIR.glob("test_*.py")):
        if _calls_shared_parser(ast.parse(path.read_text(encoding="utf-8"))):
            adopters.append(path.name)
    return adopters


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


def _shared_parser_derivations(filename: str) -> list[tuple[str, Callable[[], object]]]:
    """``[(name, callable)]`` — every NULLARY callable in ``filename`` whose body CALLS
    ``parse_production_trees``: the adopter's OWN tree derivation (a ``def _parse…()`` helper, a
    zero-arg ``@pytest.fixture``, a ``self``-only method). AST-DERIVED, never a hand-list of
    names, resolved to a LIVE callable so the ∀-mutation drives the adopter's REAL derivation
    and watches it reflect the shared-parser drop.

    Driving the DERIVATION (not the coverage TEST) is deliberate and robust: anchored's coverage
    node takes a ``production_trees`` FIXTURE, so it is not nullary — but the derivation feeding
    that fixture IS. A routing-not-sharing adopter (derives via a private
    ``production_sources``+``ast.parse`` loop, imports the helper unused) exposes NO derivation
    that calls ``parse_production_trees`` → the ∀ fails LOUD, never silent (the A-SUB-3 RED
    home). BOUND: only nullary sync derivations are drivable in-process; an adopter whose only
    shared-parser call sits inside a fixture-taking node uses the ``scripts/mutation_proof.py``
    receipt route (design §9.7 OR-clause) — and the loud failure names that, so it is never a
    false clear."""
    module = importlib.import_module(filename[:-3])
    tree = ast.parse((_TESTS_DIR / filename).read_text(encoding="utf-8"))

    def is_nullary(fn_node: ast.FunctionDef, *, is_method: bool) -> bool:
        args = fn_node.args
        if args.vararg or args.kwonlyargs or args.kwarg:
            return False
        return len(args.posonlyargs) + len(args.args) == (1 if is_method else 0)

    def is_fixture(fn_node: ast.FunctionDef) -> bool:
        """A ``@pytest.fixture`` node is NOT directly callable (pytest forbids it), so it cannot
        be driven in-process — the underlying plain derivation it wraps is what we drive."""
        for decorator in fn_node.decorator_list:
            target = decorator.func if isinstance(decorator, ast.Call) else decorator
            name = target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", None)
            if name == "fixture":
                return True
        return False

    derivations: list[tuple[str, Callable[[], object]]] = []
    for node in tree.body:
        if (
            isinstance(node, ast.FunctionDef)
            and not is_fixture(node)
            and _calls_named(node, "parse_production_trees")
            and is_nullary(node, is_method=False)
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
                    and _calls_named(sub, "parse_production_trees")
                    and is_nullary(sub, is_method=True)
                ):
                    bound = getattr(cls(), sub.name, None)
                    if callable(bound):
                        derivations.append((f"{node.name}.{sub.name}", bound))
    return derivations


# ---------------------------------------------------------------------------- #
# THE ANTI-DUP ALLOWLIST — evidence-backed SAFE non-adopters (allowlist-the-safe).
# Keyed by FILE (design §7 allowlists non-adopter FILES). Each single-package /
# non-workspace-.py scan legitimately hand-rolls a tree walk for an UNRELATED reason;
# widening any of them to whole-tree is a SCOPE CHANGE that could widen a gap (§7,
# priority #3), NOT consolidation. Deny-by-default: a clone in any OTHER file is an
# offender that must migrate onto `parse_production_trees`.
# ---------------------------------------------------------------------------- #

_ALLOWED_WHOLE_TREE_CLONE_FILES: dict[str, str] = {
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
        "non-adopters (design §3 A-SUB bound). Its whole-tree `_python_sources` adopter migrates "
        "separately (pinned by TestTheMemberHandListsAreRetired + the used-ness pin), and does "
        "not carry the rglob+parse+read_text clone signature at HEAD."
    ),
    # PROVISIONAL — see DECISION-NEEDED #1 in REPORT-reviser-asub-b.md.
    "test_comms_footer.py": (
        "PROVISIONAL (DECISION-NEEDED #1): design §7/§9.6 name test_comms_footer._scan a "
        "parse_production_trees adopter to MIGRATE, but the §5 A-SUB writable set OMITS this "
        "file — so a builder confined to §5 cannot consolidate it, and an unallowlisted clone "
        "here would make the contract UNSATISFIABLE (a C-DEF trap). Allowlisted so the contract "
        "is satisfiable at the §5 writable set. RE-OPEN TRIGGER: the operator rules the §5/§7 "
        "fork — if 'migrate', DELETE this entry AND add test_comms_footer.py to the builder's "
        "writable set (the anti-dup scan then demands its consolidation)."
    ),
}


def _whole_tree_clone_offenders() -> dict[str, list[str]]:
    """``{filename: [clone function names]}`` for every ``test_*.py`` that hand-rolls a
    whole-tree ``rglob("*.py")+ast.parse+read_text`` loop OUTSIDE the evidence-backed
    :data:`_ALLOWED_WHOLE_TREE_CLONE_FILES` allowlist.

    DERIVED from the tree (the ``test_retry_seam._unseamed_sdk_call_sites`` OFFENDER shape,
    §9.6): enumerate ALL clone sites from truth, subtract the SAFE allowlist, NAME the rest.
    Deny-by-default — a new whole-tree clone in a not-allowlisted file is an offender the day
    it lands (this is the A-SUB-2 miss the adversary planted a file to expose)."""
    offenders: dict[str, list[str]] = {}
    for path in sorted(_TESTS_DIR.glob("test_*.py")):
        if path.name in _ALLOWED_WHOLE_TREE_CLONE_FILES:
            continue
        clones = _has_tree_parser_clone(ast.parse(path.read_text(encoding="utf-8")))
        if clones:
            offenders[path.name] = clones
    return offenders


def _all_clone_files() -> dict[str, list[str]]:
    """``{filename: [clone function names]}`` for EVERY ``test_*.py`` with a whole-tree clone —
    allowlisted or not. The anti-vacuity + dead-entry checks read this."""
    found: dict[str, list[str]] = {}
    for path in sorted(_TESTS_DIR.glob("test_*.py")):
        clones = _has_tree_parser_clone(ast.parse(path.read_text(encoding="utf-8")))
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
        (rglob + ast.parse + read_text) must be GONE — routed through the shared helper. At
        HEAD it is present → RED. (The general case is
        :class:`TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist`; this is the named
        instance kept as a focused regression pin.)"""
        anchored = _TESTS_DIR / "test_anchored_pattern_seam.py"
        clones = _has_tree_parser_clone(ast.parse(anchored.read_text(encoding="utf-8")))
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
        assert _has_tree_parser_clone(ast.parse(source)) == ["_parse"]

    def test_the_clone_detector_does_not_fire_on_a_synthetic_source_parse(self) -> None:
        """NEGATIVE control: an ``ast.parse('<source string>')`` on a synthetic control
        (the shape every scanner's positive-control tests use) is NOT a tree-parser clone,
        so the detector must not flag it — else the pin refuses honest code and gets
        switched off."""
        source = "import ast\ndef _uses(src):\n    return ast.parse(src)\n"
        assert _has_tree_parser_clone(ast.parse(source)) == []


# ---------------------------------------------------------------------------- #
# THE DERIVED ANTI-DUP SCAN (A-SUB-2) — no whole-tree parser clone outside the
# SAFE allowlist. "migrated" is a CHECKED VARIABLE, not the files someone remembered.
# ---------------------------------------------------------------------------- #


class TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist:
    """⛔ THE A-SUB-2 MISS (adversary planted a new whole-tree clone; 0 new failures). Design
    §7 required a DERIVED anti-dup structural pin — *no test file hand-rolls a whole-tree
    ``rglob("*.py")+ast.parse`` outside an evidence-backed non-adopter allowlist*. This is
    ALLOWLIST-THE-SAFE (the CORRECT pattern the contract wrongly dropped as
    "enumerate-the-forbidden"): the SAFE set is small and enumerable; the offender set is
    DERIVED from the whole tree. Reuses the ``test_retry_seam._unseamed_sdk_call_sites``
    OFFENDER shape (§9.6)."""

    def test_no_unallowlisted_whole_tree_parser_clone_survives(self) -> None:
        """RED at HEAD (``641f758``): ``test_anchored_pattern_seam._parse_production_trees`` is
        an un-migrated whole-tree clone and is NOT allowlisted. After A-SUB it routes through
        the shared parser and this passes; a NEW clone in a not-allowlisted file reddens it the
        day it lands (the checked-variable property)."""
        offenders = _whole_tree_clone_offenders()
        assert offenders == {}, (
            "these test files hand-roll a whole-tree rglob('*.py')+ast.parse+read_text loop "
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
            "the whole-tree clone detector found NO rglob+parse+read_text loop in ANY test "
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
        assert _has_tree_parser_clone(ast.parse(clone_source)) == ["_scan"], (
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
# ∀-MUTATION over the LIVE-DERIVED adopter set (A-SUB-3) — the load-bearing proof.
# ---------------------------------------------------------------------------- #


class TestSharingProvenByMutation:
    """⛔ IDIOM 1 / LEG B (design §9.1, §9.7 A-SUB-3): drop the shared parser and prove EVERY
    live adopter's OWN coverage reddens FOR EACH — the RED home the static-only contract
    lacked (a routing-not-sharing adopter that imports the helper but derives privately
    survives the static pins; the runtime drop names it). The mutation reaches a FROM-import
    adopter because ``_rebind_everywhere`` rebinds BY IDENTITY across ``sys.modules`` (a
    single-module ``monkeypatch`` does not — A-SUB-3/-5).

    The ∀'s reach is :func:`_live_adopters`, RE-DERIVED LIVE each run (§9.1 meta-recursion),
    guarded fail-closed by :meth:`test_the_live_adopter_surface_is_non_empty` so the
    parametrization can never pass vacuously."""

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

    def test_the_live_adopter_surface_is_non_empty(self) -> None:
        """⛔ ANTI-VACUITY for the parametrized ∀ (§9.1): the live adopter surface must be
        NON-EMPTY, or the ∀ below has zero cases and 'passes' by measuring nothing. RED at HEAD
        (no file calls the unbuilt shared parser) — the right reason."""
        adopters = _live_adopters()
        assert adopters, (
            "no test file CALLS parse_production_trees — the shared parser is not extracted / "
            "adopted yet (RED at HEAD, expected), so the ∀-mutation below is vacuous. This "
            "fail-closed guard is the anti-vacuity for the parametrized adopter surface."
        )

    @pytest.mark.parametrize("adopter", _live_adopters())
    def test_dropping_the_shared_parser_reddens_the_adopter_derivation(self, adopter: str) -> None:
        """⛔ FOR EACH live adopter: its OWN nullary tree derivation yields real trees un-mutated
        (positive control) and REFLECTS the drop when the shared parser is rebound to ``{}`` (the
        keys it returns CHANGE). A routing-not-sharing adopter — imports the helper, derives via
        a private ``production_sources``+``ast.parse`` loop — either exposes NO shared-parser
        derivation (loud fail) or its private derivation does NOT change under the drop (this pin
        fails it). The adopter's coverage feeds this derivation (its file also calls
        ``assert_scan_reached_every_member`` — the used-ness pins), so a derivation that reflects
        the drop reddens that coverage. Empty at HEAD; non-vacuity guaranteed by
        :meth:`test_the_live_adopter_surface_is_non_empty`."""
        rebind = _rebind_everywhere_fn()
        real_parse = _parse_production_trees_fn()

        def dropped(*_args: object, **_kwargs: object) -> dict[str, ast.Module]:
            return {}

        derivations = _shared_parser_derivations(adopter)
        assert derivations, (
            f"{adopter} CALLS parse_production_trees but exposes NO in-process (nullary, "
            "non-fixture) derivation that calls it — its sharing has no runtime RED home here. "
            "Expose the tree derivation as a nullary helper (a `def _parse…()` the fixture/tests "
            "consume), OR supply a scripts/mutation_proof.py receipt declaring its coverage "
            "node-id expected-RED under parse_production_trees→{} (design §9.7 OR-clause). This "
            "fails LOUD so the bound is never a silent false clear."
        )
        # NOTE: not every adopter routes its COVERAGE through assert_scan_reached_every_member —
        # only the tree-scan-reach files do (anchored, secret_typing); backoff / secret_leak adopt
        # the PARSER for domain scans. Proving the DERIVATION reflects the drop IS the sharing
        # proof (a private copy does not reflect it); a reflected drop reddens whatever the adopter
        # scans, coverage-helper or not. Requiring the coverage helper here would over-constrain.
        for name, derive in derivations:
            healthy_keys = set(cast("dict[str, object]", derive()))
            assert healthy_keys, (
                f"{adopter}'s derivation {name!r} produced NO trees un-mutated — the positive "
                "control is broken, so a reflected drop would prove nothing."
            )
            with rebind(real_parse, dropped):
                dropped_keys = set(cast("dict[str, object]", derive()))
            assert dropped_keys != healthy_keys, (
                f"{adopter}'s derivation {name!r} did NOT reflect the shared-parser drop "
                f"(keys unchanged: {len(healthy_keys)}) — it does not READ parse_production_trees "
                "(routing-not-sharing: a private production_sources+ast.parse copy wearing the "
                "shared name). A-SUB-3."
            )
