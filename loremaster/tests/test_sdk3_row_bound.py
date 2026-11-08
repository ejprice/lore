"""Packet SDK3 contract, round 4 — operator ruling R8 F12 (and its rider) + lead decision R9 D2: the composed
transaction has ONE strain bound, ROWS, for every composer — and its WARN is a row warn.

``docs/plans/v2/sdk3-rulings.md`` R4 ("the cap is re-expressed as a bound on what strains the shared server
(rows or bytes), not statement count"), R8 F12 ("the row bound REPLACES the statement cap everywhere:
``TXN_ROW_HARD_CAP`` is the one bound … and pin it: a build that keeps the statement cap anywhere goes RED"),
R9 D2 ("``TXN_STATEMENT_WARN_THRESHOLD`` (800) becomes a ROW warn … a statement-count warn beside it is a
second source of truth").

Why round 4 exists (adversary round 1, MP1): the round-3 reference kept the 5,000-statement cap live in
``_txn.compose`` beside the row cap, and counted a fragment's rows as its statements, so for every composer
except the indexer the statement cap bound first and the row cap was dead code — and every round-3 pin passed.

The pins here drive ``compose`` and ``SurrealStore.apply`` (the chokepoint and its one production caller) with
NO socket (``execute_transaction`` is replaced by a capturing no-op, as ``test_surreal_apply`` does), using
production fragment builders wherever a fragment's ROW count must differ from its STATEMENT count (a batched
chunk write: one ``DELETE`` + one ``INSERT`` carrying N rows). The ``rows`` attribute a build may carry on a
fragment is NOT part of this contract; only the effect is.

Names this contract FIXES (read with ``getattr``, so a build lacking one fails its own pin, not the module):
``store._txn.TXN_ROW_HARD_CAP`` (round 3) and ``store._txn.TXN_ROW_WARN_THRESHOLD`` (round 4, D2).
Satisfiability: the statement cap's surviving consumers are rewritten in round 4 (``test_surreal_apply``,
``test_ingest_entity_seam``, ``_surreal_fakes``); packet 58's packer/accessor pins are dormant (packet doc
§R4 bound).
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

import pytest
from _surreal_harness import PRODUCTION_DIM, make_env, unique_database
from loremaster.index.records import Record
from loremaster.store import _txn
from loremaster.store._txn import SurrealStoreError, TxnFragment, compose
from loremaster.store.surreal import SurrealStore

# The retired per-transaction STATEMENT cap (R3) — a yardstick only: a build that still refuses one
# statement past it keeps the statement cap.
_RETIRED_STATEMENT_CAP = 5000

# The retired statement WARN threshold (R9 D2) — a yardstick only.
_RETIRED_STATEMENT_WARN = 800

# A row cap shrunk far below the fixtures, distinctive enough that its appearance in an error is the bound
# being named, not a coincidence.
_SHRUNK_ROW_CAP = 7

# A batched chunk write well over / safely under the shrunk cap — the DELETE's own row accounting cannot
# move either side across it (20 rows refused whatever the DELETE counts; 3 rows accepted even if it
# counts 1).
_ROWS_OVER_SHRUNK_CAP = 20
_ROWS_UNDER_SHRUNK_CAP = 3

_TIER = "custom"
_PATH = "pkg/row_bound.py"
_VECTOR_DIM = 4


def _required(name: str) -> Any:
    value = getattr(_txn, name, None)
    assert value is not None, f"store._txn.{name} does not exist — packet doc §R4 fixes it (R8 F12 / R9 D2)"
    return value


def _single_row_statements(count: int) -> TxnFragment:
    """``count`` statements, each writing ONE row (never sent: compose / an offline apply only)."""
    return TxnFragment(
        statements=[f"CREATE probe SET n = $rb_p{index}" for index in range(count)],
        params={f"rb_p{index}": index for index in range(count)},
    )


def _offline_store(monkeypatch: pytest.MonkeyPatch) -> tuple[SurrealStore, dict[str, Any]]:
    """A store whose ``execute_transaction`` is a capturing no-op: ``apply`` composes, logs and 'sends'."""
    captured: dict[str, Any] = {}

    async def _capture(statement: str, params: dict[str, Any], **_kwargs: Any) -> None:
        captured["statement"] = statement
        captured["params"] = params

    monkeypatch.setattr("loremaster.store.surreal.execute_transaction", _capture)
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    store = SurrealStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        dim=_VECTOR_DIM,
        user=env.user,
        password=env.password,
    )
    return store, captured


def _batched_chunk_fragment(store: SurrealStore, rows: int) -> TxnFragment:
    """The PRODUCTION chunk-replace fragment for ``rows`` records: few statements, ``rows`` rows."""
    records = [
        (
            Record(
                point_id=str(uuid.uuid4()),
                embedding_text=f"fn_{index}",
                payload={
                    "tier": _TIER,
                    "file_path": _PATH,
                    "identity": f"fn_{index}",
                    "chunk_type": "function",
                },
            ),
            [0.0] * _VECTOR_DIM,
        )
        for index in range(rows)
    ]
    fragment: TxnFragment = store.replace_file_fragment(_TIER, _PATH, records)
    return fragment


class TestNoStatementCapSurvives:
    """F12's rider, by effect: more single-row statements than the retired cap compose AND reach the
    transport, while rows stay under the row cap. RED on any build that keeps a statement cap in
    ``compose`` or in ``SurrealStore.apply``."""

    def test_compose_accepts_more_than_the_retired_statement_cap_of_single_row_statements(self) -> None:
        row_cap = _required("TXN_ROW_HARD_CAP")
        count = _RETIRED_STATEMENT_CAP + 1
        assert row_cap > count, f"premise: {count} rows sit under the row cap ({row_cap})"
        try:
            statement_text, params = compose(_single_row_statements(count))
        except SurrealStoreError as error:
            pytest.fail(
                f"compose refused {count} single-row statements ({count} rows, row cap {row_cap}): {error} — "
                f"a statement cap survives (R8 F12: the row bound REPLACES it everywhere)"
            )
        assert len(params) == count and statement_text.count("BEGIN") == 1

    async def test_apply_sends_more_than_the_retired_statement_cap_of_single_row_statements(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _required("TXN_ROW_HARD_CAP")
        store, captured = _offline_store(monkeypatch)
        count = _RETIRED_STATEMENT_CAP + 1
        try:
            await store.apply([_single_row_statements(count)])
        except SurrealStoreError as error:
            pytest.fail(f"SurrealStore.apply refused {count} single-row statements: {error} (R8 F12)")
        assert len(captured.get("params", {})) == count, "the transaction never reached the transport"


class TestTheRowCapIsTheOneBound:
    """F12: ``TXN_ROW_HARD_CAP`` bounds ROWS whatever the statement count — a batched fragment of two
    statements over the cap is refused at build time (nothing sent), naming the cap; single-row statements
    count one row each, so a composer that writes row-per-statement is bounded by the SAME cap (the row cap
    is not dead code outside the indexer). Shrinking the ONE module value must reach compose AND apply."""

    def test_a_two_statement_batched_fragment_over_the_row_cap_is_refused_naming_the_cap(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _required("TXN_ROW_HARD_CAP")
        store, _captured = _offline_store(monkeypatch)
        over = _batched_chunk_fragment(store, _ROWS_OVER_SHRUNK_CAP)
        under = _batched_chunk_fragment(store, _ROWS_UNDER_SHRUNK_CAP)
        assert len(over.statements) <= 3 and len(under.statements) <= 3, (
            f"premise: the production chunk fragment is BATCHED (few statements, many rows) — "
            f"got {len(over.statements)} statements for {_ROWS_OVER_SHRUNK_CAP} rows"
        )
        monkeypatch.setattr(_txn, "TXN_ROW_HARD_CAP", _SHRUNK_ROW_CAP)
        compose(under)  # control: rows under the cap compose
        with pytest.raises(SurrealStoreError) as refused:
            compose(over)
        assert str(_SHRUNK_ROW_CAP) in str(refused.value), (
            f"the refusal does not name the row cap ({_SHRUNK_ROW_CAP}): {refused.value}"
        )

    def test_single_row_statements_count_one_row_each_against_the_cap(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _required("TXN_ROW_HARD_CAP")
        monkeypatch.setattr(_txn, "TXN_ROW_HARD_CAP", _SHRUNK_ROW_CAP)
        compose(_single_row_statements(_SHRUNK_ROW_CAP))  # at the cap: a ceiling, not an off-by-one trap
        with pytest.raises(SurrealStoreError):
            compose(_single_row_statements(_SHRUNK_ROW_CAP + 1))

    async def test_apply_refuses_over_the_row_cap_before_anything_is_sent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _required("TXN_ROW_HARD_CAP")
        store, captured = _offline_store(monkeypatch)
        over = _batched_chunk_fragment(store, _ROWS_OVER_SHRUNK_CAP)
        monkeypatch.setattr(_txn, "TXN_ROW_HARD_CAP", _SHRUNK_ROW_CAP)
        with pytest.raises(SurrealStoreError):
            await store.apply([over])
        assert captured == {}, "an over-cap transaction reached the transport"


def _store_warnings(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [
        record
        for record in caplog.records
        if record.name.startswith("loremaster.store") and record.levelno >= logging.WARNING
    ]


class TestTheSizeWarnFiresOnRows:
    """R9 D2: ``SurrealStore.apply``'s large-transaction WARNING fires on ROWS. A batched fragment of two
    statements whose rows cross ``TXN_ROW_WARN_THRESHOLD`` warns (a statement-count warn stays silent on two
    statements); more statements than the retired 800-statement warn, with rows under the row threshold,
    does NOT (a build warning on statements beside rows — D2's "second source of truth" — fires here)."""

    async def test_rows_over_the_threshold_in_two_statements_warn(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        _required("TXN_ROW_WARN_THRESHOLD")
        store, _captured = _offline_store(monkeypatch)
        fragment = _batched_chunk_fragment(store, _ROWS_OVER_SHRUNK_CAP)
        monkeypatch.setattr(_txn, "TXN_ROW_WARN_THRESHOLD", _SHRUNK_ROW_CAP)
        with caplog.at_level(logging.DEBUG, logger="loremaster.store"):
            await store.apply([fragment])
        assert _store_warnings(caplog), (
            f"a {len(fragment.statements)}-statement transaction writing {_ROWS_OVER_SHRUNK_CAP} rows "
            f"(row warn "
            f"threshold {_SHRUNK_ROW_CAP}) did not WARN — the size warn still counts statements (R9 D2)"
        )

    async def test_many_single_row_statements_under_the_row_threshold_stay_quiet(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        _required("TXN_ROW_WARN_THRESHOLD")
        store, _captured = _offline_store(monkeypatch)
        count = _RETIRED_STATEMENT_WARN + 1
        monkeypatch.setattr(_txn, "TXN_ROW_WARN_THRESHOLD", count + 1)
        with caplog.at_level(logging.DEBUG, logger="loremaster.store"):
            await store.apply([_single_row_statements(count)])
        assert _store_warnings(caplog) == [], (
            f"{count} single-row statements ({count} rows, row warn threshold {count + 1}) WARNED: a "
            f"statement-"
            f"count warn survives beside the row warn (R9 D2: one strain measure)"
        )
