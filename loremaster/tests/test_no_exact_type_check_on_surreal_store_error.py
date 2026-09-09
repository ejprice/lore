"""Contract (defect-class invariant, close-out rulings §B1.3-3) — NO test EXACT-TYPE-checks
``SurrealStoreError`` on a domain rejection.

Session ``63b-session2-20260908``; ruling
``docs/design/2026-09-08-packet63b-ib-closeout-rulings.md`` §"FORK 2 — ADVERSARY BLOCKER B1" (B1.3
item 3). Author: ``contract-63b-ib-fork2-r3`` (Opus CONTRACT reviser — TESTS ONLY, no production).

THE CLASS THIS PINS (why it must exist forever, not just for this wave)
----------------------------------------------------------------------
FORK 2 §2.4-1 makes ``SurrealStoreError`` a NON-LEAF: ``TxnDomainRejectionError`` subclasses it, and
``TxnGovernedConflictError`` subclasses THAT. A test that pins a domain rejection with
``assert type(exc.value) is SurrealStoreError`` therefore certifies the RETIRED world (the base WAS
the leaf that ``_domain_rejection_error`` minted) and goes RED on the correct build — the 21-site
corpse class the reviser rewrote (see ``REPORT-contract-63b-ib-fork2-r3.md`` M/I/P inventory). Every
corpse was GREEN at HEAD ``98cf52c`` and RED only on the reference build, so NO builder gate could see
them — only a whole-suite run did. This pin is that gate, made permanent: the NEXT domain-error
subclass (a future ``TxnAssertViolationError``) silently re-opens the class the moment someone writes
``type(x) is SurrealStoreError`` again. "Every audit-caught defect CLASS becomes a repo-local
invariant test" (CLAUDE.md) — a fix without an invariant is half a fix.

The subclass-AWARE spellings stay legal — ``isinstance(x, SurrealStoreError)`` / ``except
SurrealStoreError`` / ``pytest.raises(SurrealStoreError)`` / ``match … case SurrealStoreError()`` — as
does the exact-type check against a *leaf* the code MINTS (``type(x) is TxnDomainRejectionError``, the
M-class mint contract). What is BANNED is the exact-type IDENTITY/EQUALITY check against the now-NON-LEAF
base: ``type(x) is|== SurrealStoreError``, ``x.__class__ is|== SurrealStoreError``,
``excinfo.type is|== SurrealStoreError`` — either operand order.

REACH IS A CHECKED VARIABLE (INSTRUMENT 0 / the ruling's item 3)
---------------------------------------------------------------
The scan routes the tree parse through the SHARED ``parse_production_trees(include_tests=True)`` and the
coverage through ``assert_scan_reached_every_member`` (both in ``_logging_fixtures``): the ONE tree
parser (so this file hand-rolls NO whole-tree parse → ``test_ast_reach_helpers.py``'s clone/parse-skip
detectors do not flag it — run green as a receipt) whose roots are DERIVED from ``[tool.uv.workspace]
members`` (not ``loremaster/tests`` only), and the ONE coverage assertion (fail-CLOSED on an empty scan).
The ban is applied to the TEST tree only (keys under ``<member>/tests/``); production is swept
separately (the reviser's M10 production sweep — count 0 at ``98cf52c``).

⚠ Present-tense dating: "RED at HEAD" / "21 corpses" is dated to ``98cf52c`` (before the FORK-2 build
and the corpse rewrites). A reader retrieving this after the build must re-derive — on a rewritten tree
the offender set is EMPTY, which is the pin doing its job.
"""

from __future__ import annotations

import ast

from _logging_fixtures import assert_scan_reached_every_member, parse_production_trees

# The base exception whose EXACT-TYPE identity check FORK 2 §2.4-1 retires (it is now a non-leaf).
_BANNED_BASE = "SurrealStoreError"
# The comparison operators that make an EXACT-TYPE check (identity or equality, either polarity).
_EXACT_TYPE_OPS = (ast.Is, ast.IsNot, ast.Eq, ast.NotEq)


def _is_type_expr(node: ast.expr) -> bool:
    """``node`` extracts a value's RUNTIME TYPE the exact-type way — ``type(x)`` / ``x.__class__`` /
    ``excinfo.type`` — the three spellings the corpse class used (the ruling names all three)."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "type":
        return True
    if isinstance(node, ast.Attribute) and node.attr in {"__class__", "type"}:
        return True
    return False


def _is_banned_base_ref(node: ast.expr) -> bool:
    """``node`` names the banned base class — bare ``SurrealStoreError`` or a dotted
    ``….SurrealStoreError`` (a re-export / module-qualified reference)."""
    if isinstance(node, ast.Name) and node.id == _BANNED_BASE:
        return True
    if isinstance(node, ast.Attribute) and node.attr == _BANNED_BASE:
        return True
    return False


def exact_type_ban_offenders(tree: ast.Module, path: str) -> list[tuple[str, int]]:
    """Every ``(path, lineno)`` in ``tree`` that EXACT-TYPE-checks the banned base
    (``type(x)``/``x.__class__``/``excinfo.type`` ``is|==|is not|!=`` ``SurrealStoreError``, either
    operand order). ``isinstance`` / ``except`` / ``pytest.raises`` / ``match case`` / an exact-type
    check against a *leaf* subclass are all structurally different AST and are NOT flagged."""
    offenders: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        operands = [node.left, *node.comparators]
        for op, left, right in zip(node.ops, operands, operands[1:]):
            if not isinstance(op, _EXACT_TYPE_OPS):
                continue
            hit = (_is_type_expr(left) and _is_banned_base_ref(right)) or (
                _is_type_expr(right) and _is_banned_base_ref(left)
            )
            if hit:
                offenders.append((path, node.lineno))
    return offenders


def _test_trees() -> dict[str, ast.Module]:
    """The parsed TEST tree — the shared whole-workspace parser (roots derived from the workspace
    members), FILTERED to ``<member>/tests/`` files. Uses the sanctioned parser, so this file is not a
    whole-tree-clone offender."""
    trees = parse_production_trees(include_tests=True)
    # Coverage / anti-vacuity: the shared parser's reach is a CHECKED VARIABLE — every declared
    # workspace member (∪ scripts) is present, and an empty scan FAILS CLOSED.
    assert_scan_reached_every_member(trees)
    return {path: tree for path, tree in trees.items() if "/tests/" in path}


def _count_calls(trees: dict[str, ast.Module], func_name: str) -> int:
    """How many ``func_name(...)`` calls appear across ``trees`` (a ``Call`` on a bare ``Name``)."""
    total = 0
    for tree in trees.values():
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == func_name
            ):
                total += 1
    return total


class TestNoExactTypeCheckOnSurrealStoreError:
    """The tree-wide invariant: no test EXACT-TYPE-checks the now-non-leaf ``SurrealStoreError`` base.

    RED at HEAD ``98cf52c`` (the 21 corpses violate it, NAMED file:line); GREEN after the reviser's
    corpse rewrites. Its discrimination control + non-vacuity guard prove it is not a scanner that
    green-lights an empty or blind tree.
    """

    def test_no_test_exact_type_checks_the_surreal_store_error_base(self) -> None:
        """⛔ THE INVARIANT. Deny-by-default over the WHOLE test tree: not one
        ``type(x)``/``x.__class__``/``excinfo.type`` ``is|==|is not|!=`` ``SurrealStoreError`` survives.
        At HEAD the 21 corpses (M/I inventory) red this, each NAMED; after the rewrites it is GREEN."""
        trees = _test_trees()
        offenders: list[str] = []
        for path, tree in sorted(trees.items()):
            for hit_path, lineno in exact_type_ban_offenders(tree, path):
                offenders.append(f"{hit_path}:{lineno}")
        assert not offenders, (
            "these TEST assertions EXACT-TYPE-check the now-NON-LEAF `SurrealStoreError` base — a "
            "domain rejection is `TxnDomainRejectionError` (a subclass) since FORK 2 §2.4-1, so "
            "`type(x) is SurrealStoreError` certifies the retired world and reds on the correct build "
            "(close-out rulings §B1.3-3). Use `assert_domain_rejection(x)` for a domain rejection, or "
            "`isinstance(x, SurrealStoreError)` / `type(x) is <the leaf the code MINTS>`:\n  "
            + "\n  ".join(offenders)
        )

    def test_the_scan_discriminates_a_planted_offender(self) -> None:
        """⛔ DISCRIMINATION CONTROL (a probe needs a positive control, PKT-28 C1). A SYNTHETIC source
        carrying each banned spelling — bare, ``.__class__``, ``excinfo.type``, and the REVERSED
        operand order — is FLAGGED, naming its line; the SUBCLASS-aware spellings and an exact-type
        check on a *leaf* are NOT. A scanner that flags nothing (or everything) certifies nothing."""
        planted = (
            "assert type(exc.value) is SurrealStoreError\n"  # line 1 — bare, the corpse shape
            "assert exc.value.__class__ == SurrealStoreError\n"  # line 2 — __class__
            "assert excinfo.type is not SurrealStoreError\n"  # line 3 — excinfo.type, is not
            "assert SurrealStoreError == type(exc.value)\n"  # line 4 — REVERSED operand order
        )
        planted_offenders = exact_type_ban_offenders(ast.parse(planted), "PLANTED.py")
        flagged_lines = sorted(lineno for _p, lineno in planted_offenders)
        assert flagged_lines == [1, 2, 3, 4], (
            "the scan did not flag every planted banned spelling (bare / __class__ / excinfo.type / "
            f"reversed order) — a blind leg lets that corpse spelling survive. flagged: {flagged_lines}"
        )
        # NEGATIVE control: the legal spellings must NOT be flagged (else the ban is over-broad and
        # bans subclass-aware checks / the M-class mint contract, and gets switched off).
        legal = (
            "assert isinstance(exc.value, SurrealStoreError)\n"
            "assert type(exc.value) is TxnDomainRejectionError\n"
            "with pytest.raises(SurrealStoreError):\n"
            "    pass\n"
            "try:\n"
            "    pass\n"
            "except SurrealStoreError:\n"
            "    pass\n"
        )
        assert exact_type_ban_offenders(ast.parse(legal), "LEGAL.py") == [], (
            "the ban flagged a SUBCLASS-aware spelling or the M-class mint contract "
            "(`type(x) is TxnDomainRejectionError`) — it is over-broad and will be switched off"
        )

    def test_the_scan_is_not_vacuous(self) -> None:
        """⛔ NON-VACUITY (registration_sites.py's anti-vacuity + the ruling's item 3). The scan SAW a
        real test tree (≥ a floor of test files across ≥1 member) AND the shared ``assert_domain_rejection``
        helper is actually ADOPTED (≥1 call site) — else a green invariant certifies an empty scan."""
        trees = _test_trees()
        test_files = [path for path in trees if "/tests/" in path]
        # A conservative FLOOR far below the real count (~100s of test files) — proves the parser ran.
        assert len(test_files) >= 40, (
            f"the invariant scanned only {len(test_files)} test files — the shared parser did not reach "
            "the test tree, so a green ban certifies nothing (fail-closed anti-vacuity)"
        )
        adoptions = _count_calls(trees, "assert_domain_rejection")
        assert adoptions >= 1, (
            "the shared `assert_domain_rejection` helper has ZERO call sites in the test tree — the "
            "I-class corpses were not rewritten to route through it (or the helper is unused), so the "
            "invariant is guarding a tree that never adopted the safe spelling"
        )
