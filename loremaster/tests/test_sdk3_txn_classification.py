"""Packet SDK3 contract — TRANSACTION and CONFLICT CLASSIFICATION on a live store.

Contract index and expected state at HEAD: ``docs/plans/v2/sdk3-python-sdk-3-migration.md`` §3.
Behaviour only, through the production drivers (``execute_transaction`` / ``run_query``) on a real
production owner's connection, so whatever the owner's SDK connection does on the wire — SDK 3.0
STREAMS ``query_raw`` on a >=3.3 server and rebuilds the per-statement shape; it RAISES from
``query()`` on a later failed statement; it types conflicts in ``details`` — is what is graded:

* a RETRYABLE write-write conflict is retried, and no update is lost, on BOTH paths (a transaction
  and a single statement), at 16-way contention;
* a DOMAIN refusal (a ``THROW``) is never retried, even when its text imitates the conflict text;
* the ROOT CAUSE surfaces — the typed kind of the statement that failed, wherever it sits in the
  transaction — never the ``NotExecuted`` / ``Cancelled`` cascade notices around it, and nothing
  the transaction wrote survives.

Attempts are COUNTED, not inferred: every driver attempt calls ``acquire`` exactly once, so a
counting ``acquire`` shows whether a retry happened (a positive control — a contention pin whose
racers never actually collided would pass for the wrong reason).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    unique_database,
)
from loremaster.store._txn import (
    TxnContentionExhaustedError,
    TxnDomainRejectionError,
    execute_transaction,
    run_query,
)
from loremaster.store.lease import SurrealLeaseStore

logger = logging.getLogger(__name__)

# Contention degree (concurrency law: >= 8; 16 is where the research doc measured 43-50% in-txn
# conflicts on 3.3.5, research §D-1) and rounds, so the conflict premise holds with margin.
_RACERS = 16
_ROUNDS = 2

# The engine's typed kind for a THROW (SDK ``ErrorKind.THROWN``'s value) — what a domain refusal
# must surface as. Written as the engine's word, not imported, so an SDK that renamed its constant
# could not move the expectation with it.
_THROWN_KIND = "Thrown"

# The cascade detail kinds that must NEVER be reported as a root cause.
_CASCADE_KINDS = frozenset({"NotExecuted", "Cancelled"})

# The live conflict text on 3.3.5 RocksDB (research §A.3) — used only as a THROW payload, to prove
# text never buys a retry.
_CONFLICT_LOOKALIKE_TEXT = "Transaction conflict: Resource busy. This transaction can be retried"


class _CountingOwner:
    """A production owner whose ``acquire`` is counted (one call per driver attempt)."""

    def __init__(self, owner: SurrealLeaseStore) -> None:
        self.owner = owner
        self.attempts = 0

    async def acquire(self) -> Any:
        self.attempts += 1
        return await self.owner._ensure_connection()

    async def drop(self, connection: Any) -> None:
        await self.owner._drop_connection(connection)

    @property
    def url(self) -> str:
        return self.owner._url


@pytest_asyncio.fixture()
async def store_env() -> AsyncIterator[SurrealEnv]:
    """A fresh database on the TEST store."""
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup_connection = await connect_admin(env)
    await setup_connection.close()
    try:
        yield env
    finally:
        await drop_database(env)


def _lease_owner(env: SurrealEnv) -> SurrealLeaseStore:
    return SurrealLeaseStore(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )


@pytest_asyncio.fixture()
async def owners(store_env: SurrealEnv) -> AsyncIterator[list[_CountingOwner]]:
    """``_RACERS`` independent production owners — one connection each, so the racers really race."""
    counted = [_CountingOwner(_lease_owner(store_env)) for _ in range(_RACERS)]
    try:
        yield counted
    finally:
        for item in counted:
            await item.owner.close()


async def _query(owner: _CountingOwner, statement: str, params: dict[str, Any] | None = None) -> Any:
    return await run_query(
        acquire=owner.acquire,
        drop=owner.drop,
        url=owner.url,
        noun="sdk3 classification probe",
        label="sdk3.classification.probe",
        statement=statement,
        params=params,
        logger=logger,
    )


async def _transact(owner: _CountingOwner, statement: str, params: dict[str, Any] | None = None) -> None:
    await execute_transaction(statement, params or {}, acquire=owner.acquire, drop=owner.drop, url=owner.url)


async def _counter_value(owner: _CountingOwner) -> Any:
    """The hot counter's value list, as the single-statement driver returns a ``SELECT VALUE``."""
    return await _query(owner, "SELECT VALUE n FROM counter:hot")


class TestARetryableConflictIsRetriedAndLosesNothing:
    """A write-write conflict is the engine saying "try again". Lost updates and spurious failures
    are both wrong; the only right outcome is every racer committing exactly once."""

    async def test_sixteen_way_read_modify_write_transactions_all_commit_once(
        self, owners: list[_CountingOwner]
    ) -> None:
        await _query(owners[0], "CREATE counter:hot SET n = 0")
        for item in owners:
            item.attempts = 0
        statement = (
            "BEGIN;\n"
            "LET $current = (SELECT VALUE n FROM ONLY counter:hot);\n"
            "UPDATE counter:hot SET n = $current + 1;\n"
            "COMMIT;"
        )
        for _ in range(_ROUNDS):
            outcomes = await asyncio.gather(
                *(_transact(item, statement) for item in owners), return_exceptions=True
            )
            failures = [outcome for outcome in outcomes if isinstance(outcome, BaseException)]
            assert not failures, (
                f"{len(failures)} of {_RACERS} racing transactions FAILED instead of retrying a "
                f"write-write conflict: {[f'{type(error).__name__}: {error}' for error in failures]!r}"
            )

        attempts = sum(item.attempts for item in owners)
        assert attempts > _RACERS * _ROUNDS, (
            f"premise: {_RACERS * _ROUNDS} transactions took {attempts} attempts, so no conflict was "
            f"ever retried — this pin saw no contention and proves nothing"
        )
        assert await _counter_value(owners[0]) == [_RACERS * _ROUNDS], (
            "a lost update: the counter does not equal the number of committed increments"
        )

    async def test_sixteen_way_single_statement_updates_all_commit_once(
        self, owners: list[_CountingOwner]
    ) -> None:
        await _query(owners[0], "CREATE counter:hot SET n = 0")
        for item in owners:
            item.attempts = 0
        for _ in range(_ROUNDS):
            outcomes = await asyncio.gather(
                *(_query(item, "UPDATE counter:hot SET n += 1") for item in owners), return_exceptions=True
            )
            failures = [outcome for outcome in outcomes if isinstance(outcome, BaseException)]
            assert not failures, (
                f"{len(failures)} of {_RACERS} racing single-statement updates FAILED instead of "
                f"retrying: {[f'{type(error).__name__}: {error}' for error in failures]!r}"
            )
        attempts = sum(item.attempts for item in owners)
        assert attempts > _RACERS * _ROUNDS, (
            f"premise: {_RACERS * _ROUNDS} updates took {attempts} attempts — no conflict was retried"
        )
        assert await _counter_value(owners[0]) == [_RACERS * _ROUNDS]


# The domain-refusal shapes: the THROW at the FIRST statement after BEGIN, in the MIDDLE, and LAST
# before COMMIT — so a positional selector ([0] = a cascade notice before the offender, [-1] = the
# refused COMMIT) is wrong on at least two of the three, and only a semantic one passes all.
_THROW_POSITIONS = {
    "first": "BEGIN;\nTHROW 'sdk3 domain refusal';\nCREATE probe:a;\nCREATE probe:b;\nCOMMIT;",
    "middle": "BEGIN;\nCREATE probe:a;\nTHROW 'sdk3 domain refusal';\nCREATE probe:b;\nCOMMIT;",
    "last": "BEGIN;\nCREATE probe:a;\nCREATE probe:b;\nTHROW 'sdk3 domain refusal';\nCOMMIT;",
}


class TestADomainRefusalIsNotRetriedAndItsRootCauseSurfaces:
    """A THROW is the engine (or our own guard) saying "never": one attempt, the THROW's own kind on
    the raised error, and the whole transaction rolled back."""

    @pytest.mark.parametrize("position", sorted(_THROW_POSITIONS))
    async def test_a_throw_anywhere_raises_its_own_kind_once_and_commits_nothing(
        self, owners: list[_CountingOwner], position: str
    ) -> None:
        owner = owners[0]
        # Declared up front, so the rolled-back check below reads an EMPTY table rather than tripping
        # over a missing one (an undeclared table is a NotFound error on 3.x).
        await _query(owner, "DEFINE TABLE probe SCHEMALESS")
        owner.attempts = 0
        with pytest.raises(TxnDomainRejectionError) as caught:
            await _transact(owner, _THROW_POSITIONS[position])

        error = caught.value
        assert not isinstance(error, TxnContentionExhaustedError)
        assert owner.attempts == 1, (
            f"a domain THROW was attempted {owner.attempts} times — a refusal must never be retried"
        )
        assert error.kind not in _CASCADE_KINDS, (
            f"the raised error names the CASCADE notice ({error.kind!r}) — the statement the "
            f"rollback stopped — instead of the THROW that caused it"
        )
        assert error.kind == _THROWN_KIND, (
            f"the root cause of a THROW at the {position} statement surfaced as kind {error.kind!r}"
        )
        assert await _query(owner, "SELECT VALUE id FROM probe") == [], (
            "a rolled-back transaction left rows behind"
        )

    async def test_a_throw_quoting_the_conflict_text_is_still_not_retried(
        self, owners: list[_CountingOwner]
    ) -> None:
        """Text never buys a retry: only the engine's TYPED conflict kind does."""
        owner = owners[0]
        owner.attempts = 0
        statement = f"BEGIN;\nCREATE probe:a;\nTHROW '{_CONFLICT_LOOKALIKE_TEXT}';\nCOMMIT;"
        with pytest.raises(TxnDomainRejectionError) as caught:
            await _transact(owner, statement)
        assert not isinstance(caught.value, TxnContentionExhaustedError)
        assert owner.attempts == 1, (
            f"a THROW quoting the conflict text was retried ({owner.attempts} attempts)"
        )

    async def test_a_single_statement_throw_is_not_retried(self, owners: list[_CountingOwner]) -> None:
        """The single-statement path: the same refusal, raised by the SDK call itself."""
        owner = owners[0]
        owner.attempts = 0
        with pytest.raises(TxnDomainRejectionError) as caught:
            await _query(owner, f"THROW '{_CONFLICT_LOOKALIKE_TEXT}'")
        assert caught.value.kind == _THROWN_KIND
        assert owner.attempts == 1
