"""am-37 §15.3 (contract-mint-q1c, 2026-10-05): the kind half of ``_txn.proven_no_key`` is an ALLOWLIST.

RULED (``docs/design/2026-09-29-packet63c-amendment-37.md`` §15.3, at ``dde69a6``): an UNCLASSIFIED
``TxnDomainRejectionError`` is proven no-key iff ``error.kind in _PROVEN_KINDS``, where ``_PROVEN_KINDS`` is
exactly §15's proven rows — top-level ``Validation``, ``Thrown``, ``AlreadyExists``, ``NotFound``,
``Configuration`` and the Query detail ``NotExecuted``. Every other kind — one the SDK enumerates, one it does
NOT (``Transaction`` and ``Query:Aborted``, both served by the floating ``v3.2`` engine, #336), a synthetic
future kind — and a kind-less rejection is UNKNOWN. ``_OUTCOME_UNKNOWN_KINDS`` (the deny-list) is DELETED.
The classified-refusal half (§15.2) is unchanged.

Its own file so its pending-build reds are owned NARROWLY by ONE self-destructing bound
(``scripts/pending_contracts.yaml`` id ``am37-15-3-q1c-mint-contract``). Every "RED" claim in
REPORT-contract-mint-q1c.md is scoped to ``dde69a6``.

The INDEPENDENT expected values are §15.3's allowlist, WRITTEN OUT below (``_RULED_PROVEN_KINDS``), never
read from production. The SDK-enumerated domain is GENERATED from the installed SDK (so a kind the SDK adds
later is expected UNKNOWN by rule, with no edit here); the unenumerated kinds are written out. Every typed
rejection is built through the REAL seam (``_txn._raise_attempt_failure`` / ``_run_verified_transaction``
over a real SDK-parsed error), and the mint cells ride ``q1b._mint_with`` (CREATE reached, #194).

Moved here from ``test_mint_kind_carveout_q1b.py`` because the ruling changes their expectation (the q1b
file's adjudication table is in the report): the classification-axis pin (the cell ``unspecified`` ×
``NotAllowed`` flips TRUE → FALSE) and the one-decider mutation legs (they read the deleted deny-list).
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import surrealdb.errors as sdk_errors
import test_mint_kind_carveout_q1b as q1b  # module-qualified: its Test* classes are not re-collected here
from loremaster.store import _txn as _txn_module
from loremaster.store._txn import SurrealConnectionError, TxnDomainRejectionError

import loremaster

# --------------------------------------------------------------------------- #
# The independent adjudication — §15.3's allowlist, written out.
# --------------------------------------------------------------------------- #

#: §15.3 "The allowlist (§15's proven rows, nothing else)". Query detail kinds are keyed by their DETAIL
#: value — the typed ``kind`` a Query error carries is its detail kind (q1b's seam pin).
_RULED_PROVEN_KINDS: frozenset[str] = frozenset(
    {"Validation", "Thrown", "AlreadyExists", "NotFound", "Configuration", "NotExecuted"}
)

_ALLOWLIST_NAME = "_PROVEN_KINDS"
#: Built by concatenation so this file's own source never matches the retired-name scan it runs.
_RETIRED_DENY_LIST = "_OUTCOME_" + "UNKNOWN_KINDS"


@dataclass(frozen=True)
class _KindCell:
    """One engine-error shape: a top-level kind, optionally a Query DETAIL kind. ``typed`` is the kind the
    driver's typed rejection carries (the detail kind for a Query error, else the top-level kind)."""

    top: str
    detail: str | None = None

    @property
    def typed(self) -> str:
        return self.detail if self.detail is not None else self.top

    @property
    def label(self) -> str:
        return f"{self.top}:{self.detail}" if self.detail is not None else self.top


def _values_of(enum_like: type) -> set[str]:
    return {value for name, value in vars(enum_like).items() if name.isupper() and isinstance(value, str)}


_SDK_TOP_KINDS: frozenset[str] = frozenset(_values_of(sdk_errors.ErrorKind) | set(sdk_errors.KIND_TO_CLASS))
_SDK_DETAIL_KINDS: frozenset[str] = frozenset(_values_of(sdk_errors.QueryDetailKind))

#: GENERATED from the installed SDK: every top-level kind (bare ``Query`` included — FORK-2's detail-less
#: Query) and every Query detail kind. A member the SDK adds later joins this list and is expected UNKNOWN
#: by rule (§15.3: "any member the installed SDK adds later").
_SDK_CELLS: list[_KindCell] = [
    *(_KindCell(top) for top in sorted(_SDK_TOP_KINDS)),
    *(_KindCell("Query", detail) for detail in sorted(_SDK_DETAIL_KINDS)),
]

#: §15.3: kinds the SDK does NOT enumerate. ``Transaction`` and ``Query:Aborted`` are served by the engine
#: today (§15.3 "Why (a)"); the two ``Future*`` cells are synthetic — a kind no engine has served yet.
_UNENUMERATED_CELLS: list[_KindCell] = [
    _KindCell("Transaction"),
    _KindCell("Query", "Aborted"),
    _KindCell("FutureKind"),
    _KindCell("Query", "FutureDetailKind"),
]


def _engine_text(cell: _KindCell) -> str:
    """A neutral engine text the classifier does NOT recognise (the ``unspecified rejection`` residue)."""
    return f"injected q1c: the engine reported a {cell.label} error"


def _sdk_error(cell: _KindCell) -> sdk_errors.ServerError:
    """A REAL SDK error for ``cell``, built by the SDK's own query-error parser."""
    payload: dict[str, Any] = {"kind": cell.top, "result": _engine_text(cell)}
    if cell.detail is not None:
        payload["details"] = {"kind": cell.detail}
    return sdk_errors.parse_query_error(payload)


def _expected_proven(typed_kind: str | None) -> bool:
    """§15.3: an UNCLASSIFIED rejection is proven iff its typed kind is on the allowlist (kind-less: no)."""
    return typed_kind is not None and typed_kind in _RULED_PROVEN_KINDS


def _production_allowlist() -> Any:
    """STUB EXPECTATION: ``_txn._PROVEN_KINDS`` does not exist before the build — red by name until then."""
    return getattr(_txn_module, _ALLOWLIST_NAME)


# --------------------------------------------------------------------------- #
# fixture validity — the cells mean what they claim
# --------------------------------------------------------------------------- #


class TestTheFixturesDiscriminate:
    """The written-out allowlist names real SDK constants; the unenumerated cells are really unenumerated;
    the generated domain is not vacuous and carries members on BOTH sides of the allowlist."""

    def test_every_ruled_kind_is_an_sdk_constant(self) -> None:
        missing = _RULED_PROVEN_KINDS - (_SDK_TOP_KINDS | _SDK_DETAIL_KINDS)
        assert not missing, f"§15.3 names SDK constants; the installed SDK lacks: {sorted(missing)}"

    def test_the_unenumerated_cells_are_unenumerated(self) -> None:
        enumerated = _SDK_TOP_KINDS | _SDK_DETAIL_KINDS
        assert not {cell.typed for cell in _UNENUMERATED_CELLS} & enumerated

    def test_the_generated_domain_straddles_the_allowlist(self) -> None:
        typed = {cell.typed for cell in _SDK_CELLS}
        assert _RULED_PROVEN_KINDS <= typed
        assert {"Internal", "Serialization", "TimedOut", "Cancelled", "NotAllowed", "Query"} <= typed - (
            _RULED_PROVEN_KINDS
        )


# --------------------------------------------------------------------------- #
# the allowlist is the ruling, and only grows by adjudication
# --------------------------------------------------------------------------- #


class TestTheAllowlistIsExactlyTheRuling:
    """§15.3: ``_PROVEN_KINDS`` is exactly §15's proven rows. A kind added without a row in this table reds
    BY NAME (the allowlist can only grow by adjudication); a ruled kind dropped reds by name too."""

    def test_the_allowlist_is_the_ruled_set(self) -> None:
        production = {str(kind) for kind in _production_allowlist()}
        unadjudicated = production - _RULED_PROVEN_KINDS
        dropped = _RULED_PROVEN_KINDS - production
        assert not unadjudicated, (
            f"kind(s) on _PROVEN_KINDS nobody adjudicated (am-37 §15.3): {sorted(unadjudicated)}"
        )
        assert not dropped, f"ruled proven kind(s) missing from _PROVEN_KINDS: {sorted(dropped)}"


class TestTheDenyListIsGone:
    """§15.3: ``_OUTCOME_UNKNOWN_KINDS`` is DELETED — a bare, anchor-free scan of every workspace member's
    production sources (code AND prose) finds no mention, and ``_txn`` binds no such name. The member set is
    DERIVED from ``[tool.uv.workspace] members``. Positive control: the scan sees the name in a synthetic
    text."""

    @staticmethod
    def _hits(text: str) -> list[int]:
        return [number for number, line in enumerate(text.splitlines(), 1) if _RETIRED_DENY_LIST in line]

    @staticmethod
    def _production_sources() -> list[Path]:
        repo = Path(loremaster.__file__).resolve().parents[2]
        members = tomllib.loads((repo / "pyproject.toml").read_text())["tool"]["uv"]["workspace"]["members"]
        assert "loremaster" in members and "lorerunes" in members, members
        sources: list[Path] = []
        for member in members:
            sources += [
                path
                for path in (repo / member).rglob("*.py")
                if "tests" not in path.parts and ".venv" not in path.parts
            ]
        return sorted(sources)

    def test_CONTROL_the_scan_sees_the_name(self) -> None:
        assert self._hits(f"x = 1\n# see {_RETIRED_DENY_LIST} here\n") == [2]

    def test_no_production_source_mentions_it(self) -> None:
        sources = self._production_sources()
        assert len(sources) > 20, "the scan's population is vacuous"
        found = {str(path): self._hits(path.read_text()) for path in sources}
        assert not {path: lines for path, lines in found.items() if lines}, found

    def test_the_store_layer_binds_no_such_name(self) -> None:
        assert not hasattr(_txn_module, _RETIRED_DENY_LIST)


# --------------------------------------------------------------------------- #
# the predicate, through the REAL seams, ∀ kind (enumerated or not)
# --------------------------------------------------------------------------- #

_ALL_CELLS: list[_KindCell] = [*_SDK_CELLS, *_UNENUMERATED_CELLS]


class TestEveryKindOffTheAllowlistIsUnknown:
    """§15.3, GENERATED over the SDK's enumerations ∪ the unenumerated cells, through the single-statement
    seam: ``proven_no_key`` answers exactly ``typed kind ∈ allowlist``. A transport kind is a
    ``SurrealConnectionError`` (never proven, and never on the allowlist); every other kind is a
    ``TxnDomainRejectionError`` carrying its typed kind and the ``unspecified`` label."""

    @pytest.mark.parametrize("cell", _ALL_CELLS, ids=lambda cell: cell.label)
    async def test_the_single_statement_seam(self, cell: _KindCell) -> None:
        raised = await q1b._through_the_seam(_sdk_error(cell))  # noqa: SLF001
        if isinstance(raised, SurrealConnectionError):
            assert cell.typed not in _RULED_PROVEN_KINDS
        else:
            assert isinstance(raised, TxnDomainRejectionError), type(raised)
            assert getattr(raised, "kind") == cell.typed  # noqa: B009
            assert getattr(raised, "error_class") == q1b._RULED_UNSPECIFIED_LABEL  # noqa: B009, SLF001
        assert q1b._proven_no_key()(raised) is _expected_proven(cell.typed), cell.label  # noqa: SLF001

    @pytest.mark.parametrize("cell", _UNENUMERATED_CELLS, ids=lambda cell: cell.label)
    async def test_the_transactional_seam(self, cell: _KindCell) -> None:
        raised = await _through_the_transaction(cell)
        assert isinstance(raised, TxnDomainRejectionError), type(raised)
        assert getattr(raised, "kind") == cell.typed  # noqa: B009
        assert q1b._proven_no_key()(raised) is False, cell.label  # noqa: SLF001


async def _through_the_transaction(cell: _KindCell) -> BaseException:
    """``_run_verified_transaction`` over ONE rolled-back ERR entry of ``cell`` (q1b's fake connection)."""
    entry: dict[str, Any] = {"status": "ERR", "result": _engine_text(cell), "kind": cell.top}
    if cell.detail is not None:
        entry["details"] = {"kind": cell.detail}

    async def acquire() -> Any:
        return q1b._FakeTransactionConnection(entry)  # noqa: SLF001

    async def drop(_connection: object) -> None:
        return None

    try:
        await _txn_module._run_verified_transaction(  # noqa: SLF001
            "BEGIN; CREATE principal_key CONTENT {}; COMMIT;",
            {},
            acquire=acquire,
            drop=drop,
            url="ws://127.0.0.1:1/rpc",
            deadline_seconds=1.0,
        )
    except BaseException as raised:  # noqa: BLE001 - the raise IS the observation
        return raised
    raise AssertionError("unreachable: a rolled-back transaction returned")  # pragma: no cover


#: The classification axis: ``KIND_TO_CLASS`` ∪ ``QueryDetailKind`` ∪ {None} (§15.2) ∪ the unenumerated
#: typed kinds (§15.3).
_AXIS_KINDS: list[str | None] = [
    *sorted(set(sdk_errors.KIND_TO_CLASS) | _SDK_DETAIL_KINDS | {cell.typed for cell in _UNENUMERATED_CELLS}),
    None,
]


class TestTheClassificationAxisIsAllowlistDriven:
    """§15.2 + §15.3 (moved from q1b, re-keyed): ∀ (error_class, kind): a RECOGNISED refusal is PROVEN
    whatever its kind (§15.2 unchanged — including a kind nobody enumerated); the ``unspecified`` residue is
    proven iff its kind is on the allowlist. Re-keyed cell vs q1b: ``unspecified`` × ``NotAllowed`` TRUE →
    FALSE."""

    def test_every_classifier_label_is_ruled(self) -> None:
        labels = q1b._error_class_labels()  # noqa: SLF001
        assert labels.get("_ERROR_CLASS_UNSPECIFIED") == q1b._RULED_UNSPECIFIED_LABEL, labels  # noqa: SLF001
        ruled = q1b._RULED_CLASSIFIED_LABEL_NAMES | {"_ERROR_CLASS_UNSPECIFIED"}  # noqa: SLF001
        assert set(labels) == ruled, (
            f"unruled: {sorted(set(labels) - ruled)} · retired: {sorted(ruled - set(labels))}"
        )

    @pytest.mark.parametrize("kind", _AXIS_KINDS, ids=str)
    @pytest.mark.parametrize("label_name", sorted(q1b._error_class_labels()))  # noqa: SLF001
    def test_the_predicate_over_label_and_kind(self, label_name: str, kind: str | None) -> None:
        error_class = q1b._error_class_labels()[label_name]  # noqa: SLF001
        rejection = _txn_module._domain_rejection_error(  # noqa: SLF001
            error_class, f"injected q1c: ({error_class})", kind=kind
        )
        assert isinstance(rejection, TxnDomainRejectionError), type(rejection)
        assert getattr(rejection, "error_class") == error_class  # noqa: B009 - §15.2: a typed attribute
        assert getattr(rejection, "kind") == kind  # noqa: B009 - §15.2: a typed attribute
        if label_name in q1b._RULED_CLASSIFIED_LABEL_NAMES:  # noqa: SLF001
            expected = True
        else:
            expected = _expected_proven(kind)
        assert q1b._proven_no_key()(rejection) is expected, (label_name, kind)  # noqa: SLF001


# --------------------------------------------------------------------------- #
# the mint, for a kind nobody enumerated
# --------------------------------------------------------------------------- #


class TestAnUnenumeratedKindAtTheMint:
    """§15.3 mint cells: a rejection of a kind the SDK does not enumerate, raised during the CREATE through
    the real seam, is the UNKNOWN fate — ``PrincipalKeyStoreError`` (the OUTER wrap, #400), the CONDITIONAL
    revoke note, a cause-neutral message, and "could not mint" NOWHERE lore-adm prints (q1b's
    ``_assert_unknown_fate``)."""

    @pytest.mark.parametrize("cell", _UNENUMERATED_CELLS, ids=lambda cell: cell.label)
    async def test_an_unenumerated_kind_during_the_CREATE(
        self, monkeypatch: pytest.MonkeyPatch, cell: _KindCell
    ) -> None:
        injected = await q1b._through_the_seam(_sdk_error(cell))  # noqa: SLF001
        assert isinstance(injected, TxnDomainRejectionError), type(injected)
        q1b._assert_unknown_fate(await q1b._mint_with(monkeypatch, injected), injected)  # noqa: SLF001


# --------------------------------------------------------------------------- #
# ONE allowlist decides catch, message AND note — by MUTATION
# --------------------------------------------------------------------------- #


def _rebind_allowlist(monkeypatch: pytest.MonkeyPatch, change: Any) -> int:
    """Replace EVERY loremaster binding of the production allowlist (identity-found) by ``change(members)``,
    rebuilt in the allowlist's own container type."""
    allowlist = _production_allowlist()
    replacement = type(allowlist)(change(set(allowlist)))
    return q1b._rebind_all(monkeypatch, allowlist, replacement)  # noqa: SLF001


class TestTheAllowlistIsTheOneDecider:
    """§15.3 + §15.1: moving one kind across the allowlist moves BOTH the message and the note of its mint
    cell. A private copy of the allowlist, a second decider for the catch, or a residual deny-list keeps one
    of the two and reds here. Each leg runs its unmutated CONTROL first."""

    async def _served(
        self, monkeypatch: pytest.MonkeyPatch, cell: _KindCell
    ) -> tuple[BaseException, BaseException]:
        injected = await q1b._through_the_seam(_sdk_error(cell))  # noqa: SLF001
        return await q1b._mint_with(monkeypatch, injected), injected  # noqa: SLF001

    async def test_adding_Transaction_flips_message_and_note(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cell = _KindCell("Transaction")
        q1b._assert_unknown_fate(*await self._served(monkeypatch, cell))  # noqa: SLF001 - CONTROL
        assert _rebind_allowlist(monkeypatch, lambda members: members | {"Transaction"}) >= 1
        q1b._assert_proven_fate(*await self._served(monkeypatch, cell))  # noqa: SLF001

    async def test_adding_Internal_flips_message_and_note(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cell = _KindCell("Internal")
        q1b._assert_unknown_fate(*await self._served(monkeypatch, cell))  # noqa: SLF001 - CONTROL
        assert _rebind_allowlist(monkeypatch, lambda members: members | {"Internal"}) >= 1
        q1b._assert_proven_fate(*await self._served(monkeypatch, cell))  # noqa: SLF001

    async def test_removing_Validation_flips_message_and_note(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cell = _KindCell("Validation")
        q1b._assert_proven_fate(*await self._served(monkeypatch, cell))  # noqa: SLF001 - CONTROL
        assert _rebind_allowlist(monkeypatch, lambda members: members - {"Validation"}) >= 1
        q1b._assert_unknown_fate(*await self._served(monkeypatch, cell))  # noqa: SLF001

    async def test_removing_NotExecuted_flips_message_and_note(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The Query-DETAIL member: the allowlist is matched on the typed (detail) kind."""
        cell = _KindCell("Query", "NotExecuted")
        q1b._assert_proven_fate(*await self._served(monkeypatch, cell))  # noqa: SLF001 - CONTROL
        assert _rebind_allowlist(monkeypatch, lambda members: members - {"NotExecuted"}) >= 1
        q1b._assert_unknown_fate(*await self._served(monkeypatch, cell))  # noqa: SLF001
