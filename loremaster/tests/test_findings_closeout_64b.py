"""Contract r2 — packet 64b-i: the MP-9 ALIAS pin, ISOLATED in its own file (packet-64 amendment 10 FK-r2-10 +
REPORT-contract-64b-r2 §FORKS FK-r2-10). Authored by ``contract-64b-r2`` (Opus 5.5 — contract tests ONLY).

WHAT IT PINS (amendment 8 §5, MP-9): the runtime ``Any`` reach-arounds the 64b-i contract files make to
production symbols (``x: Any = mod.sym``, ``vars(mod).get("sym")`` / ``vars(mod)["sym"]``,
``getattr(mod, "sym")``) are a SELF-DESTRUCTING alias set: while bound ``packet-64b-i-contract`` stands, every
alias names a symbol the bound owns as UNBUILT; once the bound is deleted (with the 64b-i build), the alias
set must be EMPTY — each reach-around rewritten as a TYPED CALL, so mypy checks its shape.

WHY ITS OWN FILE (REPORT §FORKS FK-r2-10, RULED by packet-64 amendment 10 ``46340ef``): the currency gate
adjudicates a pytest red only as a side effect of a file's MYPY claim (``partition_pytest``;
``transcript_self_destruct_findings`` leg 2), and this pin's red exists only AFTER the build, in a mypy-clean
file — #461's class, so NO bound can hold it and none is minted. The isolation is CONFIRMED (am-10 §0 (1)):
this file holds ONLY the alias pin. The close-out — every ``Any`` reach-around rewritten as a typed call and
bound ``packet-64b-i-contract`` deleted — is ONE SEQUENCED COMMIT INSIDE the 64b-i build wave (builder commit
→ close-out commit by a contract-author-class agent → the wave's currency run → cold audit), so this pin is
red only between two commits of one wave and never meets a gate (am-10 §1).

OWNER of that step: the lead's CLOSE-OUT agent (BC-r2-9); TRIGGER: the 64b-i builder's commit.
"""

from __future__ import annotations

import ast
from pathlib import Path

import yaml

_TESTS = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS.parents[1]
_BOUND_ID = "packet-64b-i-contract"
_CONTRACT_FILE_GLOB = "test_*_64b.py"


def contract_files() -> tuple[str, ...]:
    """The 64b-i contract files MP-9 governs — DERIVED (every ``test_*_64b.py`` in this directory; DUAL r2 →
    am-9: r2's hand-kept tuple had already missed ``test_findings_cas_seam_64b.py``). Completeness against the
    bound's registered 64b files is pinned below."""
    return tuple(sorted(path.name for path in _TESTS.glob(_CONTRACT_FILE_GLOB)))


#: Pre-existing production symbols a contract file reads through ``vars()`` because the RULED TYPE differs
#: from
#: HEAD's (``_FINDING_ACTIONS`` is a tuple at HEAD, a ``dict[str, GovernedVerbSpec]`` when built). Permitted
#: only
#: WHILE the bound stands (they expire with it, exactly like the unbuilt symbols).
TYPE_CHANGING_READS = frozenset(
    {"_FINDING_ACTIONS", "_MIGRATE_VALID_TABLES", "_GOVERNED_VERBS_ROUTED", "_GOVERNED_VERBS_PENDING_ROUTING"}
)


_PRODUCTION_PACKAGES = ("loremaster", "lorerunes", "loresigil", "lorescribe")


def _production_receivers(tree: ast.AST) -> set[str]:
    """The local names a contract file binds to a PRODUCTION module or class (``from loremaster import
    governed``, ``import lorerunes as pdp``, ``from loremaster.findings import FindingLedger`` — anywhere in
    the file, local imports included). ⚠ BOUND, stated: a reach-around through an INSTANCE (``getattr(plan,
    "guard")``, ``getattr(spec, "requires_capability")``) is NOT in the set — its owner is unknowable
    statically; the typed declarations still pin those shapes for mypy."""
    receivers: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in _PRODUCTION_PACKAGES:
                    receivers.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] in _PRODUCTION_PACKAGES:
            for alias in node.names:
                receivers.add(alias.asname or alias.name)
    return receivers


def _reach_arounds(source: str) -> set[str]:
    """Every production symbol NAME a contract file reaches through ``Any`` on a PRODUCTION receiver: ``x:
    Any = <recv>.<name>``, ``vars(<recv>).get("<name>")`` / ``vars(<recv>)["<name>"]`` and ``getattr(<recv>,
    "<name>", …)``."""
    tree = ast.parse(source)
    receivers = _production_receivers(tree)
    names: set[str] = set()

    def _is_receiver(node: ast.AST) -> bool:
        return isinstance(node, ast.Name) and node.id in receivers

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.annotation, ast.Name)
            and node.annotation.id == "Any"
            and isinstance(node.value, ast.Attribute)
            and _is_receiver(node.value.value)
        ):
            names.add(node.value.attr)
        if isinstance(node, ast.Call):
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "get"
                and isinstance(func.value, ast.Call)
                and getattr(func.value.func, "id", None) == "vars"
                and func.value.args
                and _is_receiver(func.value.args[0])
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                names.add(node.args[0].value)
            if (
                isinstance(func, ast.Name)
                and func.id == "getattr"
                and len(node.args) >= 2
                and _is_receiver(node.args[0])
                and isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[1].value, str)
            ):
                names.add(node.args[1].value)
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Call)
            and getattr(node.value.func, "id", None) == "vars"
            and node.value.args
            and _is_receiver(node.value.args[0])
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, str)
        ):
            names.add(node.slice.value)
    return names


def _bound_symbol_names() -> set[str] | None:
    """The NAMES the bound's ``missing_symbols`` mention (every dotted / ``type[…]`` / call-arg component),
    or ``None`` when the bound is gone from ``scripts/pending_contracts.yaml``."""
    registry = yaml.safe_load((_REPO_ROOT / "scripts" / "pending_contracts.yaml").read_text(encoding="utf-8"))
    entries = registry.get("bounds", []) if isinstance(registry, dict) else []
    bound = next((entry for entry in entries if entry.get("id") == _BOUND_ID), None)
    if bound is None:
        return None
    names: set[str] = set()
    for file_entry in bound.get("files", []):
        for symbol in file_entry.get("missing_symbols", []) or []:
            for part in str(symbol).replace("type[", "").replace("]", "").split("."):
                names.add(part)
    return names


class TestTheReachAroundsSelfDestruct:
    """amendment 8 §5 (MP-9) — the alias pin, alone in this file (FK-r2-10)."""

    def test_every_reach_around_names_an_unbuilt_symbol_while_the_bound_stands(self) -> None:
        """GREEN at HEAD (every reach-around targets an unbuilt symbol the bound names). RED the day a symbol
        LANDS yet is still reached through ``Any`` (its typed use would now check) — and, once the bound is
        deleted, RED until the alias set is EMPTY (the aliases become typed calls — a close-out TEST edit)."""
        aliases: dict[str, set[str]] = {}
        for name in contract_files():
            path = _TESTS / name
            if path.exists():
                for symbol in _reach_arounds(path.read_text(encoding="utf-8")):
                    aliases.setdefault(symbol, set()).add(name)
        assert aliases, (
            "non-vacuity: no reach-around found — the scan is blind (it must see r1's vars(server))"
        )
        bound_names = _bound_symbol_names()
        if bound_names is None:
            assert not aliases, (
                f"bound {_BOUND_ID} is deleted but these symbols are still reached through Any (rewrite them "
                f"as typed calls — amendment 8 §5): {sorted(aliases)}. OWNER: the lead's 64b-i CLOSE-OUT "
                "agent (BC-r2-9; amendment 10 FK-r2-10) — TRIGGER: the 64b-i build commit. Not a builder "
                "defect."
            )
            return
        stale = {
            symbol: sorted(files)
            for symbol, files in aliases.items()
            if symbol not in bound_names and symbol not in TYPE_CHANGING_READS
        }
        assert not stale, (
            "reach-arounds to production symbols the bound does NOT own as unbuilt (they landed, or were "
            "never "
            f"ruled — reach them TYPED): {stale}"
        )

    def test_the_derived_contract_files_cover_the_bounds_registered_64b_files(self) -> None:
        """COMPLETENESS of the derivation: every ``*_64b.py`` test file bound ``packet-64b-i-contract``
        registers is a derived contract file (so a registered file the glob misses reds here, not
        silently)."""
        registry = yaml.safe_load(
            (_REPO_ROOT / "scripts" / "pending_contracts.yaml").read_text(encoding="utf-8")
        )
        entries = registry.get("bounds", []) if isinstance(registry, dict) else []
        bound = next((entry for entry in entries if entry.get("id") == _BOUND_ID), None)
        registered = {
            Path(str(entry.get("path"))).name
            for entry in (bound or {}).get("files", [])
            if str(entry.get("path")).endswith("_64b.py")
        }
        assert registered <= set(contract_files()), sorted(registered - set(contract_files()))
