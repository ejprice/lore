"""Contract r2 — packet 64b-i: the ledger SIGNATURES (packet-64 amendment 7 ``6e42ed1`` §2 FK-1) and the
contract's own DECLARATIONS (amendment 8 ``53563e7`` §5 FK-9 → MP-9). Authored by ``contract-64b-r2`` (Opus
5.5 — contract tests ONLY).

FK-1 (RULED): ``subject=`` is THE one identity kwarg ∀ ledgers (memory 63a, findings 64b, tasks 64a) —
``caller=`` REJECTED. The colliding finding TITLE is renamed ``title`` at the Python seam only; served
params, columns and models keep ``subject``. Pins: ``LEDGER_IDENTITY_KWARG == "subject"`` AND it equals the
memory seam's kwarg DERIVED by ``inspect.signature`` (never a second literal); ∀ ``FindingLedger`` write
method the findings dispatcher calls (DERIVED by AST) the ``subject`` parameter is keyword-only and annotated
``Subject``; the report's title is ``title``; no production function anywhere carries a ``caller`` parameter
except the per-hit-adjudicated allowlist (a BARE-name sweep — CLAUDE.md rename law).

MP-9 (RULED, amendment 8 §5): the r1 declarations were name-only tuples — mypy saw a renamed kwarg nowhere
(the adversary's coherent wrong-shape build was mypy-IDENTICAL to the reference). Every 64b-i contract file
now declares its ruled symbols as TYPED CALLS (the mypy ``[call-arg]`` check sees a renamed or missing kwarg)
— kept PERMANENTLY as signature pins. The runtime ``Any`` reach-arounds (``x: Any = mod.sym``,
``vars(mod).get("sym")``, ``getattr(mod, "sym")``) get the self-destruct they lacked: the alias set, DERIVED
from the contract files' AST, must stay ⊆ the bound's UNBUILT symbols (read from
``scripts/pending_contracts.yaml``); when the bound is deleted the alias set must be EMPTY. ⚠ That last leg
reds AFTER the build by design until the aliases are rewritten as typed calls — a TEST edit, so it is the
close-out step of whoever deletes the bound (REPORT §BUILDER CONSTRAINTS BC-r2-9), never the builder's.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import TYPE_CHECKING

from _governed_contract_64 import LEDGER_IDENTITY_KWARG, LEDGER_TITLE_KWARG
from loremaster.findings import FindingLedger
from loremaster.memory.local import LocalMemoryBackend
from test_findings_closeout_64b import contract_files

from loremaster import server

if TYPE_CHECKING:
    import lorerunes

    # 64b-i's RULED, not-yet-built signatures this file pins — TYPED CALLS (amendment 8 §5 MP-9; permanent
    # signature pins). Until the build lands them, mypy errors OWNED by bound ``packet-64b-i-contract``
    # (#461) — which is also what REGISTERS this file's RED@HEAD pytest legs with the currency gate.
    async def _ruled_64b_i_ledger_identity_kwarg(ledger: FindingLedger, subject: lorerunes.Subject) -> None:
        """amendment 7 §2 (FK-1): ``title`` is the title, ``subject=`` the identity, ∀ write verbs."""
        await ledger.report(title="t", body="b", area="a", category="c", created_by="c", subject=subject)
        await ledger.resolve(7, "actor", None, subject=subject)
        await ledger.wontfix(7, "actor", None, subject=subject)


_TESTS = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS.parents[1]
_SERVER_PY = Path(server.__file__)
_BOUND_ID = "packet-64b-i-contract"
_FINDING_READ_METHODS = frozenset({"get", "query", "chain_head", "filed_since"})

#: Every production file whose function takes a parameter literally named ``caller`` that is NOT the rejected
#: identity spelling — one verdict per hit (CLAUDE.md: "all remaining hits are X" is banned output). Measured
#: at ``4beb79e`` by this very sweep: exactly one.
CALLER_PARAMETER_VERDICTS: dict[str, str] = {
    "loremaster/loremaster/graph.py": "``_call_edges(caller, …)`` — the code graph's CALLER node (a "
    "call-edge "
    "endpoint in the symbol graph), not an identity",
}


def _annotation_text(parameter: inspect.Parameter) -> str:
    return str(parameter.annotation)


# =========================================================================== #
# FK-1 — ``subject=`` on every ledger; the title is ``title``.
# =========================================================================== #


def _dispatcher_ledger_methods() -> set[str]:
    """Every ``FindingLedger`` method the findings dispatcher calls (``self.finding_ledger.<m>(`` inside
    ``AppContext.findings`` and the batch helper) — DERIVED by AST, never a hand-list."""
    tree = ast.parse(_SERVER_PY.read_text(encoding="utf-8"))
    methods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name in (
            "findings",
            "_resolve_or_acknowledge_many",
        ):
            for call in ast.walk(node):
                if (
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and isinstance(call.func.value, ast.Attribute)
                    and call.func.value.attr == "finding_ledger"
                ):
                    methods.add(call.func.attr)
    return methods


class TestTheIdentityKwargIsSubjectOnEveryLedger:
    """amendment 7 §2 (FK-1): ONE name for the governing concept across the ledgers."""

    def test_the_constant_is_the_memory_seams_derived_kwarg(self) -> None:
        """GREEN at HEAD AND after (memory's seam is 63a's, shipped): the contract's constant equals the name
        of the ``Subject``-annotated parameter of ``LocalMemoryBackend.remember`` — DERIVED, never a second
        literal; a memory rename or a constant drift reds here."""
        params = inspect.signature(LocalMemoryBackend.remember).parameters
        derived = [name for name, param in params.items() if "Subject" in _annotation_text(param)]
        assert derived == [LEDGER_IDENTITY_KWARG] == ["subject"], (derived, LEDGER_IDENTITY_KWARG)

    def test_every_dispatcher_called_write_method_takes_a_keyword_only_Subject(self) -> None:
        """⚠ RED at HEAD (``report``'s ``subject`` is the TITLE, positional; the status verbs take no "
        "Subject)."""
        writes = _dispatcher_ledger_methods() - _FINDING_READ_METHODS
        assert writes >= {"report", "acknowledge", "resolve", "wontfix", "annotate"}, (
            f"the dispatcher's ledger-method derivation found {sorted(writes)} — vacuous"
        )
        wrong = {}
        for method in sorted(writes):
            params = inspect.signature(getattr(FindingLedger, method)).parameters
            param = params.get(LEDGER_IDENTITY_KWARG)
            if (
                param is None
                or param.kind is not inspect.Parameter.KEYWORD_ONLY
                or "Subject" not in _annotation_text(param)
            ):
                wrong[method] = str(inspect.signature(getattr(FindingLedger, method)))
        assert not wrong, f"FindingLedger write methods without a keyword-only `subject: Subject`: {wrong}"

    def test_the_report_title_is_title(self) -> None:
        """⚠ RED at HEAD (the title parameter is ``subject``)."""
        params = list(inspect.signature(FindingLedger.report).parameters)
        assert params[:3] == ["self", LEDGER_TITLE_KWARG, "body"], (
            f"UNBUILT (amendment 7 §2 FK-1): FindingLedger.report's title parameter is not `title`: {params}"
        )

    def test_no_production_function_takes_a_caller_parameter(self) -> None:
        """⚠ RED on the r1 reference (``caller=`` on every ledger write). A BARE-name sweep over EVERY
        production function parameter (THE shared production parse): a parameter literally named ``caller``
        is the rejected spelling. Every hit gets a verdict (``CALLER_PARAMETER_VERDICTS`` — ONE at
        ``4beb79e``, the code graph's caller node)."""
        from _logging_fixtures import parse_production_trees  # noqa: PLC0415

        hits = []
        for relative, tree in parse_production_trees(include_scripts=True).items():
            if relative in CALLER_PARAMETER_VERDICTS:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    arguments = node.args
                    names = [
                        arg.arg for arg in (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs)
                    ]
                    if "caller" in names:
                        hits.append(f"{relative}::{node.name}")
        stale = sorted(set(CALLER_PARAMETER_VERDICTS) - set(parse_production_trees(include_scripts=True)))
        assert not stale, f"stale caller= verdicts (the file is gone): {stale}"
        assert not hits, f"production functions still take the REJECTED `caller=` spelling (am-7 §2): {hits}"


# =========================================================================== #
# MP-9 — the declarations certify SHAPE; the Any reach-arounds self-destruct.
# =========================================================================== #


class TestTheDeclarationsAreTypedCalls:
    """amendment 8 §5 (MP-9) — the typed-call half (the alias half lives ALONE in
    ``test_findings_closeout_64b.py``, REPORT §FORKS FK-r2-10)."""

    def test_the_declarations_are_typed_calls(self) -> None:
        """⚠ RED on r1's files (name-only tuples ``_RULED_64B_I = (…)``). ∀ contract file with a
        ``TYPE_CHECKING`` block: the block holds NO bare tuple-of-names declaration — each ruled symbol is
        USED (a call, an attribute read on a typed receiver), so mypy checks its SHAPE."""
        offenders = []
        for name in contract_files():
            path = _TESTS / name
            if not path.exists():
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.If) and getattr(node.test, "id", None) == "TYPE_CHECKING":
                    for child in ast.walk(node):
                        if isinstance(child, ast.AnnAssign | ast.Assign) and isinstance(
                            getattr(child, "value", None), ast.Tuple
                        ):
                            offenders.append(f"{name}:{child.lineno}")
        assert not offenders, f"name-only (shape-blind) TYPE_CHECKING declarations remain: {offenders}"


# =========================================================================== #
# FK-r2-8 (packet-64 amendment 9): the retired harness plugin is loaded by NOTHING — in both worlds.
# =========================================================================== #

#: the module name, spelled by concatenation so THIS file never matches its own sweep.
_RETIRED_PLUGIN = "c3_harness" + "_repair"
#: config/code suffixes through which a module can be imported or a pytest plugin loaded (``-p <name>``,
#: ``pytest_plugins``, an ``import``, a shell ``python -m``/``PYTHONPATH`` line).
_LOADING_SUFFIXES = frozenset({".py", ".sh", ".toml", ".yaml", ".yml", ".ini", ".cfg", ".json"})


class TestTheRetiredHarnessPluginIsLoadedByNothing:
    """amendment 9 FK-r2-8: ``scripts/c3_harness_repair.py`` (2026-08-03, a rescued ``-p`` pytest plugin)
    still passes the retired served ``actor=``/``created_by=`` args AND the title as ``subject=`` — it fails
    at first use after 64b-i. The operator rules DELETE vs KEEP (not yet ruled; REPORT §HELD carries both).
    This pin holds in BOTH worlds: no code or config file in the workspace members, ``scripts/`` or the repo
    root mentions the module (so a kept corpse's rot is DELIBERATE — nothing can load it — and a deleted one
    leaves no dangling ``-p``). Archived prose (``docs/``) is not a loader and is not swept."""

    @staticmethod
    def _mentions(swept: list[Path], exempt: set[Path], root: Path) -> list[str]:
        return sorted(
            str(path.relative_to(root))
            for path in swept
            if path.resolve() not in exempt
            and _RETIRED_PLUGIN in path.read_text(encoding="utf-8", errors="ignore")
        )

    def test_no_code_or_config_file_mentions_the_plugin(self) -> None:
        from _governed_contract import declared_workspace_members  # noqa: PLC0415

        roots = [_REPO_ROOT / member for member in declared_workspace_members()] + [_REPO_ROOT / "scripts"]
        candidates = [path for path in _REPO_ROOT.iterdir() if path.is_file()]
        for root in roots:
            candidates += [path for path in root.rglob("*") if ".venv" not in path.parts and path.is_file()]
        swept = [path for path in candidates if path.suffix in _LOADING_SUFFIXES]
        assert any(path.name == "pyproject.toml" for path in swept), "non-vacuity: the sweep missed the root"
        own = {(_REPO_ROOT / "scripts" / f"{_RETIRED_PLUGIN}.py").resolve(), Path(__file__).resolve()}
        mentions = self._mentions(swept, own, _REPO_ROOT)
        assert not mentions, (
            f"{_RETIRED_PLUGIN} is referenced by a loader-capable file (amendment 9 FK-r2-8 — delete the "
            f"reference, or the plugin, never leave it half-alive): {mentions}"
        )

    def test_CONTROL_the_scan_sees_a_mention(self, tmp_path: Path) -> None:
        """CONTROL: the scan FLAGS a loader line naming the plugin and passes a clean one."""
        loader = tmp_path / "conftest.py"
        loader.write_text(f'pytest_plugins = ["{_RETIRED_PLUGIN}"]\n', encoding="utf-8")
        clean = tmp_path / "clean.py"
        clean.write_text("x = 1\n", encoding="utf-8")
        assert self._mentions([loader, clean], set(), tmp_path) == ["conftest.py"]
