"""Exhausted contention is never a FALSE CLEAR — the repo-level FATE classifier (packet 58 amendment 10).

*Every claim in this file is scoped to the tree at ``4beb79e`` (branch ``feat/surreal-unification``),
2026-09-26, authored by ``contract-58-r3``.*

Spec: ``docs/design/2026-09-26-packet58-amendment-10.md`` @ ``5b72471`` (rules ``REPORT-contract-58-r3.md``
FK-r3-7; amends amendment 9 §3).  The property, askable: *"if exhausted contention reaches THIS catch site,
what does the caller (or the record) see — and could it mistake that for a healthy outcome?"*  Three honest
fates, one forbidden:

* **PASSTHROUGH** (derived) — every exit re-raises what was caught, unchanged;
* **TRANSLATE** (derived) — every exit re-raises unchanged or raises a FAULT class (``_exhaustion_fates.
  FAULT_CLASS_NAMES``, an exact allowlist) ``from`` the caught error;
* **NAMED-ISOLATION** (registered) — a row in ``_exhaustion_fates.REGISTERED_FATES`` naming the
  classification, the OWNER, and the AST EVIDENCE that proves the fate (a log ≥ WARNING, a stderr line, a
  failure marker …);
* **FORBIDDEN: SILENT** — anything else: an unregistered site reds BY NAME.

DOMAIN (amendment 10, Reading (i)): every catch site in the production tree — ``try`` / ``try*`` handlers
and ``contextlib.suppress`` items, through THE ONE walker/resolver (``_catch_sites``) — whose caught closure
contains ``TxnContentionExhaustedError`` (``except Exception`` and a bare ``except:`` included), with no
clause ABOVE it catching that class.  A raise under ``if isinstance(<caught>, C)`` for a class ``C``
disjoint from exhausted contention is unreachable for it and is not an exit.

HOME (amendment 10 §4): cross-packet, repo-level; LANDED by packet 58 (it built the instrument), OWNED per
row by the site's component.  GREEN at HEAD by construction: every site the tree holds today is derived or
registered (per-row verdicts: ``REPORT-contract-58-r3.md`` §FATES).  The rows whose evidence is EMPTY — a
lifecycle catch with no log line, am-10 §4's "one real hole" — are a pinned, only-shrinking set
(``UNLOGGED_SITES``), reported by name, their fix one line in their owner's module."""

from __future__ import annotations

import ast
import importlib
import types
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pytest
from _catch_sites import CatchSite, catch_sites_in, production_catch_sites, resolved_by_import
from _exhaustion_fates import (
    CLASSIFICATIONS,
    FAULT_CLASS_NAMES,
    REGISTERED_FATES,
    UNLOGGED_SITES,
    Fate,
)
from loremaster.store._txn import TxnContentionExhaustedError

if TYPE_CHECKING:
    # packet 63c-i-a a28c: the STATIC reference that owns this file's pending red in
    # scripts/pending_contracts.yaml (#461's shape). ``_exhaustion_fates.REGISTERED_FATES`` no longer
    # registers ``server.py::_comms_register``: the ruled build (amendment 32 K5/K6, deciding from this
    # not-yet-built class) removes the register compensation, so at ``169925f`` that site reds here as
    # unregistered. Runtime-inert.
    from loremaster.store._txn import TxnUniqueViolationError

    def _a28c_register_has_no_compensation() -> object:
        return TxnUniqueViolationError


EXHAUSTION = TxnContentionExhaustedError
#: The log methods at or above WARNING (a ``logger.log(level, …)`` call is not counted — stated bound).
_LOUD_LOG_METHODS = frozenset({"warning", "error", "exception", "critical"})


def fault_classes() -> tuple[type, ...]:
    """``FAULT_CLASS_NAMES`` resolved to classes (a name that does not resolve reds the pin below)."""
    resolved: list[type] = []
    for dotted in FAULT_CLASS_NAMES:
        module_name, _, attribute = dotted.rpartition(".")
        resolved.append(getattr(importlib.import_module(module_name), attribute))
    return tuple(resolved)


def in_domain(site: CatchSite) -> bool:
    """Reading (i): the site can catch exhausted contention and nothing above it catches it first."""
    reachable = any(issubclass(EXHAUSTION, cls) for cls in site.caught)
    shielded = any(issubclass(EXHAUSTION, cls) for cls in site.earlier)
    return reachable and not shielded


def _disjoint_isinstance(test: ast.expr, caught_name: str | None, module: Any) -> bool:
    """``isinstance(<caught>, C)`` (or a conjunction led by it) for a ``C`` disjoint from exhausted "
    "contention."""
    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.And):
        return _disjoint_isinstance(test.values[0], caught_name, module)
    if not (
        isinstance(test, ast.Call)
        and isinstance(test.func, ast.Name)
        and test.func.id == "isinstance"
        and len(test.args) == 2
        and isinstance(test.args[0], ast.Name)
        and test.args[0].id == caught_name
    ):
        return False
    target = test.args[1]
    elements = list(target.elts) if isinstance(target, ast.Tuple) else [target]
    classes = [resolved_by_import(element, module) for element in elements]
    return all(
        isinstance(cls, type) and not issubclass(EXHAUSTION, cls) and not issubclass(cls, EXHAUSTION)
        for cls in classes
    )


def _exits(handler: ast.ExceptHandler, module: Any) -> list[ast.stmt]:
    """Every exit statement (``raise`` / ``return`` / ``continue`` / ``break``) reachable for exhausted
    contention,
    nested defs excluded, disjoint-``isinstance`` branches pruned."""
    exits: list[ast.stmt] = []
    pending: list[ast.AST] = list(handler.body)
    while pending:
        node = pending.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        if isinstance(node, ast.If) and _disjoint_isinstance(node.test, handler.name, module):
            pending.extend(node.orelse)
            continue
        if isinstance(node, (ast.Raise, ast.Return, ast.Continue, ast.Break)):
            exits.append(node)
        pending.extend(ast.iter_child_nodes(node))
    return exits


def derived_fate(site: CatchSite) -> str | None:
    """``"passthrough"`` / ``"translate"`` when the fate is DERIVABLE from the handler, else ``None`` (a
    row is due).
    A ``suppress`` is never derivable (it has no exit: it swallows)."""
    handler = site.handler
    if handler is None or not handler.body:
        return None
    if not isinstance(handler.body[-1], ast.Raise):
        return None  # the handler can fall through: something other than a re-raise is served
    faults = fault_classes()
    translated = False
    for exit_node in _exits(handler, site.module):
        if not isinstance(exit_node, ast.Raise):
            return None
        if exit_node.exc is None or (
            isinstance(exit_node.exc, ast.Name) and exit_node.exc.id == handler.name
        ):
            continue
        target = exit_node.exc.func if isinstance(exit_node.exc, ast.Call) else exit_node.exc
        cls = resolved_by_import(target, site.module)
        chained = isinstance(exit_node.cause, ast.Name) and exit_node.cause.id == handler.name
        if not (isinstance(cls, type) and cls in faults and chained):
            return None
        translated = True
    return "translate" if translated else "passthrough"


# --------------------------------------------------------------------------- #
# the EVIDENCE predicates a registered row may name — each an AST fact about the site
# --------------------------------------------------------------------------- #


def _calls(handler: ast.ExceptHandler) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(ast.Module(body=handler.body, type_ignores=[]))
        if isinstance(node, ast.Call)
    ]


def _logs_loud(handler: ast.ExceptHandler) -> bool:
    return any(
        isinstance(call.func, ast.Attribute) and call.func.attr in _LOUD_LOG_METHODS
        for call in _calls(handler)
    )


def _logs_exc_info(handler: ast.ExceptHandler) -> bool:
    return any(
        isinstance(call.func, ast.Attribute)
        and call.func.attr in _LOUD_LOG_METHODS
        and (
            call.func.attr == "exception"
            or any(
                keyword.arg == "exc_info"
                and not (isinstance(keyword.value, ast.Constant) and keyword.value.value in (False, None))
                for keyword in call.keywords
            )
        )
        for call in _calls(handler)
    )


def _stderr(handler: ast.ExceptHandler) -> bool:
    return any(
        isinstance(call.func, ast.Name)
        and call.func.id == "print"
        and any(
            keyword.arg == "file" and ast.unparse(keyword.value) == "sys.stderr" for keyword in call.keywords
        )
        for call in _calls(handler)
    )


def _marks_failed(handler: ast.ExceptHandler) -> bool:
    return any(
        "fail"
        in (call.func.attr if isinstance(call.func, ast.Attribute) else getattr(call.func, "id", "")).lower()
        or any("FAILED" in ast.unparse(argument) for argument in call.args)
        for call in _calls(handler)
    )


def _appends_failed(handler: ast.ExceptHandler) -> bool:
    return any(
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "append"
        and (
            "failed" in ast.unparse(call.func.value).lower()
            or any("FAILED" in ast.unparse(a) for a in call.args)
        )
        for call in _calls(handler)
    )


def _returns_named_outcome(handler: ast.ExceptHandler) -> bool:
    """A ``return`` of a value that NAMES the failure (a ``*_failed``/``UNAVAILABLE``/``failed`` marker, an
    ``error`` object for the caller to raise, or a non-zero exit code) — never a bare
    ``return``/``None``/``[]``."""
    for node in ast.walk(ast.Module(body=handler.body, type_ignores=[])):
        if isinstance(node, ast.Return) and node.value is not None:
            text = ast.unparse(node.value)
            if any(marker in text.lower() for marker in ("fail", "unavailable", "error")) or text == "1":
                return True
    return False


def _adds_note(handler: ast.ExceptHandler) -> bool:
    return any(
        isinstance(call.func, ast.Attribute) and call.func.attr == "add_note" for call in _calls(handler)
    )


def _records_on_self(handler: ast.ExceptHandler) -> bool:
    return any(
        isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Attribute) and ast.unparse(target).startswith("self.")
            for target in node.targets
        )
        and isinstance(node.value, ast.Name)
        and node.value.id == handler.name
        for node in ast.walk(ast.Module(body=handler.body, type_ignores=[]))
    )


def _raises_chained(handler: ast.ExceptHandler) -> bool:
    """A ``raise <C>(…) from <the caught error>`` — a LOUD translation to a class outside the fault
    allowlist (the
    row, not the classifier, adjudicates whether ``C`` is honest for this caller)."""
    return any(
        isinstance(node, ast.Raise)
        and node.exc is not None
        and isinstance(node.cause, ast.Name)
        and node.cause.id == handler.name
        for node in ast.walk(ast.Module(body=handler.body, type_ignores=[]))
    )


EVIDENCE: dict[str, Any] = {
    "raises-chained": _raises_chained,
    "logs>=warning": _logs_loud,
    "logs-exc_info": _logs_exc_info,
    "stderr": _stderr,
    "marks-failed": _marks_failed,
    "appends-failed": _appends_failed,
    "returns-named-outcome": _returns_named_outcome,
    "adds-note": _adds_note,
    "records-on-self": _records_on_self,
}


@dataclass(frozen=True)
class Verdict:
    site: CatchSite
    fate: str | None
    ordinal: int


def classify(sites: list[CatchSite]) -> tuple[list[Verdict], dict[str, list[CatchSite]]]:
    """``(every domain site's verdict, {key: [its NON-derived sites in source order]})``."""
    verdicts: list[Verdict] = []
    undecided: dict[str, list[CatchSite]] = {}
    for site in sites:
        if not in_domain(site):
            continue
        fate = derived_fate(site)
        ordinal = len(undecided.get(site.key, [])) if fate is None else -1
        verdicts.append(Verdict(site, fate, ordinal))
        if fate is None:
            undecided.setdefault(site.key, []).append(site)
    return verdicts, undecided


def evidence_holds(site: CatchSite, evidence: tuple[str, ...]) -> list[str]:
    """The named evidence predicates that do NOT hold on ``site`` (a ``suppress`` has no body: none can "
    "hold)."""
    if site.handler is None:
        return list(evidence)
    return [name for name in evidence if not EVIDENCE[name](site.handler)]


class TestTheRegistryIsTheAdjudicationBothWays:
    """am-10 §2: allowlist-the-safe — derived fates need no row; every other domain site has EXACTLY its "
    "row."""

    def test_every_non_derived_site_has_a_row_and_every_row_a_site(self) -> None:
        _verdicts, undecided = classify(production_catch_sites())
        counts = {key: len(sites) for key, sites in undecided.items()}
        rows = {key: len(fates) for key, fates in REGISTERED_FATES.items()}
        unregistered = {key: counts[key] for key in counts if counts[key] != rows.get(key)}
        stale = {key: rows[key] for key in rows if key not in counts}
        assert not unregistered and not stale, (
            f"SILENT-FATE sites with no (or a mis-counted) row — exhausted contention can reach them and "
            f"nothing "
            f"proves the caller cannot mistake the outcome for a healthy one (am-10 §1): {unregistered}.  "
            f"Rows "
            f"whose sites became PASSTHROUGH/TRANSLATE or vanished — DELETE them: {stale}"
        )

    def test_every_row_names_a_ruled_classification_an_owner_and_evidence_that_HOLDS(self) -> None:
        _verdicts, undecided = classify(production_catch_sites())
        problems: list[str] = []
        for key, fates in REGISTERED_FATES.items():
            for index, fate in enumerate(fates):
                if fate.classification not in CLASSIFICATIONS:
                    problems.append(f"{key}#{index}: classification {fate.classification!r} is not ruled")
                if not fate.owner:
                    problems.append(f"{key}#{index}: no owner")
                unknown = [name for name in fate.evidence if name not in EVIDENCE]
                if unknown:
                    problems.append(f"{key}#{index}: unknown evidence {unknown}")
                sites = undecided.get(key, [])
                if index < len(sites) and not fate.evidence and sites[index].handler is not None:
                    gained = [name for name, holds in EVIDENCE.items() if holds(sites[index].handler)]
                    if gained:
                        problems.append(
                            f"{key}#{index} (line {sites[index].lineno}): a pinned HOLE now carries evidence "
                            f"{gained} — declare it on the row and drop the key from UNLOGGED_SITES"
                        )
                if index < len(sites):
                    failing = evidence_holds(sites[index], fate.evidence)
                    if failing:
                        problems.append(
                            f"{key}#{index} (line {sites[index].lineno}): the FATE CHANGED — {failing}"
                        )
        assert not problems, problems

    def test_the_UNLOGGED_rows_are_exactly_the_pinned_hole_set(self) -> None:
        """am-10 §4: a catch with NO proving evidence is the one real hole Reading (i) finds — pinned,
        reported by
        name, only-shrinking.  A NEW evidence-less row reds; a FIXED one reds until removed from both sets."""
        empty = {key for key, fates in REGISTERED_FATES.items() if any(not fate.evidence for fate in fates)}
        assert empty == set(UNLOGGED_SITES), (
            f"evidence-less rows not in the pinned hole set: {sorted(empty - set(UNLOGGED_SITES))}; pinned "
            f"holes "
            f"that now carry evidence (remove them from UNLOGGED_SITES): "
            f"{sorted(set(UNLOGGED_SITES) - empty)}"
        )


class TestTheFaultAllowlistIsExact:
    def test_every_fault_class_resolves_and_none_is_a_domain_verdict(self) -> None:
        """am-10 §2: an EXACT allowlist of fault classes — each resolves, and none is a lost-race / not-found
        verdict (a translation into one of those is #102's lie by construction)."""
        faults = fault_classes()
        assert len(faults) == len(FAULT_CLASS_NAMES)
        verdict_words = ("illegaltransition", "notfound", "unknown", "lost", "conflict")
        assert not [
            cls.__name__ for cls in faults if any(word in cls.__name__.lower() for word in verdict_words)
        ]


_SYNTHETIC = """
import contextlib
from loremaster.store._txn import SurrealConnectionError, SurrealStoreError, TxnContentionExhaustedError
from loremaster.tasks import IllegalTransitionError


class GovernedConflict(Exception):
    pass


async def swallows():
    try:
        await work()
    except SurrealStoreError:
        pass


async def suppresses():
    with contextlib.suppress(SurrealStoreError):
        await work()


async def translates_to_a_verdict():
    try:
        await work()
    except SurrealStoreError as error:
        raise IllegalTransitionError("lost") from error


async def translates_unchained():
    try:
        await work()
    except SurrealStoreError:
        raise SurrealConnectionError("gone")


async def passes_through():
    try:
        await work()
    except SurrealStoreError:
        await cleanup()
        raise


async def translates_to_a_fault():
    try:
        await work()
    except TxnContentionExhaustedError as error:
        raise SurrealConnectionError("the bootstrap exhausted its retry budget") from error


async def guarded_then_broad():
    try:
        await work()
    except TxnContentionExhaustedError:
        raise
    except SurrealStoreError:
        return None


async def isinstance_pruned(plan):
    try:
        await work()
    except Exception as error:
        if isinstance(error, GovernedConflict):
            raise ValueError("a disjoint class's translation") from error
        raise


async def conditional_reraise(flag):
    try:
        await work()
    except SurrealStoreError:
        if flag:
            raise
        return None
"""


def _synthetic_sites() -> list[CatchSite]:
    module = types.ModuleType("synthetic_exhaustion_fates")
    exec(compile(_SYNTHETIC, "<synthetic>", "exec"), vars(module))  # noqa: S102
    return catch_sites_in("synthetic.py", ast.parse(_SYNTHETIC), module)


class TestTheClassifierDiscriminates:
    """am-10 §2's positive controls, and the derived fates each must grant."""

    @pytest.mark.parametrize(
        ("function", "expected"),
        [
            ("swallows", None),
            ("suppresses", None),
            ("translates_to_a_verdict", None),
            ("translates_unchained", None),
            ("conditional_reraise", None),
            ("passes_through", "passthrough"),
            ("translates_to_a_fault", "translate"),
            ("isinstance_pruned", "passthrough"),
        ],
    )
    def test_each_shape_gets_its_fate(self, function: str, expected: str | None) -> None:
        sites = [
            site for site in _synthetic_sites() if site.key == f"synthetic.py::{function}" and in_domain(site)
        ]
        assert len(sites) == 1, [(site.key, site.lineno) for site in sites]
        assert derived_fate(sites[0]) == expected

    def test_a_clause_ABOVE_that_catches_exhaustion_takes_the_broad_one_out_of_the_domain(self) -> None:
        sites = [site for site in _synthetic_sites() if site.key == "synthetic.py::guarded_then_broad"]
        assert [in_domain(site) for site in sites] == [True, False]
        assert derived_fate(sites[0]) == "passthrough"

    def test_the_production_domain_is_not_vacuous(self) -> None:
        verdicts, undecided = classify(production_catch_sites())
        fates = {verdict.fate for verdict in verdicts}
        assert {"passthrough", "translate", None} <= fates, fates
        assert undecided, "no registered site at all — the registry leg would be vacuous"


# --------------------------------------------------------------------------- #
# am-10 §3's SIBLING, pinned as a KNOWN BOUND (CLAUDE.md "WHEN YOU CANNOT CLOSE A HOLE, PIN IT")
# --------------------------------------------------------------------------- #


class TestTheIndexerStoreFailureReasonIsOneReasonForTwoCauses:
    """KNOWN BOUND (packet 58 amendment 10 §3, the indexer SIBLING): ``index/indexer.py``'s per-file store
    handlers catch the BROAD ``SurrealStoreError`` and record ONE reason, ``_FAILED_STORE_REASON``, for both a
    RETRYABLE exhausted contention and a PERMANENT statement-cap overflow.  Not a defect today (the file is
    recorded ``failed`` and the sweep continues) — it becomes one the day a retry policy branches on the
    reason.
    RE-OPEN TRIGGER: *"the day the reconcile retry policy reads ``reason``"*.  This pin goes RED when either
    half moves: if you split the reason (closed the bound) or started reading it elsewhere (armed the
    trigger),
    delete or re-rule this pin DELIBERATELY and say so."""

    def test_both_store_handlers_record_the_ONE_reason_for_both_causes(self) -> None:
        sites = [
            site
            for site in production_catch_sites()
            if site.file == "index/indexer.py"
            and site.handler is not None
            and in_domain(site)
            and any(cls.__name__ == "SurrealStoreError" for cls in site.caught)
            and "_FAILED_STORE_REASON" in ast.unparse(ast.Module(body=site.handler.body, type_ignores=[]))
        ]
        assert sorted(site.key for site in sites) == [
            "index/indexer.py::_commit_batch_file",
            "index/indexer.py::_index_chunks",
        ], "KNOWN BOUND (am-10 §3 sibling) moved — the per-file store handlers changed; re-rule deliberately"

    def test_nothing_outside_the_indexer_reads_the_reason(self) -> None:
        """The trigger's proxy: the constant's NAME and VALUE occur in no production module but the indexer (a
        reader comparing against the recorded reason would introduce one).  Bound: a reader that branches
        on the
        manifest's reason COLUMN generically, without naming this value, is not seen."""
        indexer = importlib.import_module("loremaster.index.indexer")
        value = indexer._FAILED_STORE_REASON  # noqa: SLF001
        from _logging_fixtures import parse_production_trees

        holders = sorted(
            relative
            for relative, tree in parse_production_trees(include_scripts=False).items()
            if any(
                (isinstance(node, ast.Constant) and node.value == value)
                or (isinstance(node, ast.Name) and node.id == "_FAILED_STORE_REASON")
                for node in ast.walk(tree)
            )
        )
        assert [path.rsplit("/", 1)[-1] for path in holders] == ["indexer.py"], holders


_UNUSED: tuple[object, ...] = (Fate,)
