"""Packet SDK3 contract, round 3 — operator ruling R2: ONE single-statement seam, and it SELECTS.

``docs/plans/v2/sdk3-rulings.md`` R2: ``_txn.run_query`` is lore's single-statement seam. Under SDK 3.0
``query()`` answers one entry PER STATEMENT, so the seam selects its ONE statement's result itself and
RAISES when the SDK answers with anything other than exactly one — never a silent ``[0]``. Rider: scout's
``_scout_query_once`` and the inbox awaiter's ``_live_query`` ride the SAME seam, so the selection rule
lives in exactly one place. Pinned like the ruling says:

* a lost compare-and-set reads as LOST — at the seam (``test_sdk3_result_shapes`` R3/R4) and through
  scout's own command claim (here): the measured SDK 3.0 failure was a truthy ``[[]]``, 8 of 8 racers
  "winning" one claim;
* a counter reads its scalar (``test_sdk3_result_shapes`` R2);
* a ``LIVE SELECT`` yields its bare id — the awaiter wakes on a notification
  (``test_sdk3_result_shapes`` R10, with its no-notification control);
* a two-statement call RAISES (here) — and it is refused BEFORE it reaches the wire: the runtime SDK guard's
  standing #144 posture (``tests/_sdk_guard.py``, autouse) already forbids a multi-statement ``.query()``
  even inside the driver, judged by the shared ``_txn._assert_envelope_integrity`` split. A seam that
  sent the text and refused the SDK's two-entry answer afterwards would have run BOTH statements (two
  writes landed, then an error) and trips the guard; the write leg below pins "nothing ran".

Sharing is proved by MUTATION, not by a standing test (packet doc §4.R2, mutation M-R2): break the
selection inside the seam and the seam's own pins, scout's claim pin and the awaiter's wake pin redden
TOGETHER. A scout or awaiter that kept a private selection would stay green under that mutation.

Packet doc: ``docs/plans/v2/sdk3-python-sdk-3-migration.md`` §4 (round 3).
"""

from __future__ import annotations

import asyncio
import functools
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
    run,
    unique_database,
)
from loremaster.scout import CommandSubscriber, _open_command_connection
from loremaster.store._txn import (
    SurrealConnectionError,
    SurrealStoreError,
    TxnDomainRejectionError,
    run_query,
)
from loremaster.store.lease import SurrealLeaseStore
from surrealdb import RecordID

logger = logging.getLogger(__name__)

# Scout claim race degree (concurrency law: >= 8).
_CLAIM_RACERS = 8

# The log event scout emits for a LOST claim (an empty CAS: another instance already completed the
# command). It is scout's served operational signal for "this claim was not mine"; counting it is how
# the pin reads each racer's verdict without reaching inside the subscriber.
_LOST_CLAIM_EVENT = "command.duplicate_completion"

# A poll cadence for subscribers whose poll loop is never started (only their claim is exercised).
_UNUSED_POLL_SECONDS = 60.0


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


@pytest_asyncio.fixture()
async def owner(store_env: SurrealEnv) -> AsyncIterator[SurrealLeaseStore]:
    """One production owner on the fresh database."""
    lease_store = SurrealLeaseStore(
        url=store_env.url,
        namespace=store_env.namespace,
        database=store_env.database,
        user=store_env.user,
        password=store_env.password,
    )
    try:
        yield lease_store
    finally:
        await lease_store.close()


async def _query(owner: SurrealLeaseStore, statement: str) -> Any:
    return await run_query(
        acquire=owner._ensure_connection,
        drop=owner._drop_connection,
        url=owner._url,
        noun="sdk3 seam probe",
        label="sdk3.seam.probe",
        statement=statement,
        logger=logger,
    )


class TestTheSeamRefusesAnythingButOneStatement:
    """R2: the seam answers for ONE statement. Handed two, it must not quietly answer for the first
    (SDK 2.0's behaviour, which hid the second's result and its failure) nor return the SDK's list (which
    every caller would index, iterate and truth-test as if it were the one statement's result)."""

    @pytest.mark.parametrize(
        "statement",
        ["RETURN 1; RETURN 2", "RETURN [1]; RETURN [2]"],
        ids=["two_scalars", "two_lists"],
    )
    async def test_a_two_statement_call_raises(self, owner: SurrealLeaseStore, statement: str) -> None:
        """Two value shapes, so a seam that special-cases a list-of-lists (or a scalar) cannot pass
        by unwrapping one of them: ``[1, 2]`` and ``[[1], [2]]`` are both "a plausible single result"."""
        with pytest.raises(SurrealStoreError) as caught:
            await _query(owner, statement)
        error = caught.value
        assert not isinstance(error, SurrealConnectionError), (
            f"a two-statement call is a CALLER error, not a transport fault — raising "
            f"{type(error).__name__} would drop a healthy connection and invite a retry"
        )
        assert not isinstance(error, TxnDomainRejectionError), (
            "a two-statement call is not the ENGINE refusing a write — a domain rejection tells "
            "the caller its write was illegal, when the engine in fact ran both statements"
        )

    async def test_a_two_statement_write_is_refused_before_either_statement_runs(
        self, owner: SurrealLeaseStore
    ) -> None:
        # Declared first: on 3.x a SELECT from an undeclared table is a NotFound error, not [].
        await _query(owner, "DEFINE TABLE IF NOT EXISTS seam_probe SCHEMALESS")
        with pytest.raises(SurrealStoreError):
            await _query(owner, "CREATE seam_probe:a; CREATE seam_probe:b")
        assert await _query(owner, "SELECT VALUE id FROM seam_probe") == [], (
            "the refused two-statement call WROTE rows — it was sent and refused afterwards, so a caller "
            "told 'refused' has in fact applied both writes"
        )

    async def test_the_connection_is_kept_after_the_refusal(self, owner: SurrealLeaseStore) -> None:
        """The refusal is a seam verdict on the caller's input: the owner's connection stays healthy
        and the very next single-statement call answers its own scalar."""
        with pytest.raises(SurrealStoreError):
            await _query(owner, "RETURN 1; RETURN 2")
        assert await _query(owner, "RETURN 7") == 7


class _Ignored:
    """Scout's command handler, for subscribers whose dispatch is never run."""

    async def __call__(self, command: dict[str, Any]) -> None:
        del command


class TestScoutsCommandClaimHasExactlyOneWinner:
    """R2 rider: scout's CAS claim (``CommandSubscriber._mark`` → ``_scout_query``) reads a LOST claim as
    lost. Eight subscribers, each on its own production connection, race to mark ONE pending command
    ``done``; the store's ``WHERE status = 'pending'`` lets exactly one through. Every other racer must
    read its empty result as a lost claim (scout logs it as a duplicate completion). The measured SDK
    3.0 failure mode is the opposite reading of the SAME bytes: a won claim answers ``[[{…}]]``, which
    scout's row filter reads as no rows, and a lost one ``[[]]`` — so a build that does not select the
    one statement's result logs ALL eight as duplicates; one that selects wrongly logs none."""

    async def test_eight_racing_claims_have_one_winner_and_seven_losers(
        self, store_env: SurrealEnv, caplog: pytest.LogCaptureFixture
    ) -> None:
        admin = await connect_admin(store_env)
        connections: list[Any] = []
        try:
            await run(admin, "DEFINE TABLE IF NOT EXISTS command SCHEMALESS")
            command_id = RecordID("command", "sdk3_claim")
            await run(
                admin, "CREATE $id SET status = 'pending', created_at = time::now()", {"id": command_id}
            )
            opener = functools.partial(
                _open_command_connection,
                url=store_env.url,
                namespace=store_env.namespace,
                database=store_env.database,
                user=store_env.user,
                password=store_env.password,
            )
            subscribers = [
                CommandSubscriber(connect=opener, handler=_Ignored(), poll_interval_s=_UNUSED_POLL_SECONDS)
                for _ in range(_CLAIM_RACERS)
            ]
            connections = [await opener() for _ in subscribers]
            caplog.set_level(logging.INFO, logger="loremaster.scout")
            await asyncio.gather(
                *(
                    subscriber._mark(connection, command_id, "done")
                    for subscriber, connection in zip(subscribers, connections, strict=True)
                )
            )
            lost = [record for record in caplog.records if record.getMessage() == _LOST_CLAIM_EVENT]
            assert len(lost) == _CLAIM_RACERS - 1, (
                f"{_CLAIM_RACERS - len(lost)} of {_CLAIM_RACERS} racers read their claim as WON "
                f"({len(lost)} logged a lost claim). Exactly one claim can win a pending row; a build that "
                f"reads the SDK's per-statement list instead of the one statement's rows gets this wrong in "
                f"one direction or the other."
            )
            status = await run(admin, "SELECT VALUE status FROM $id", {"id": command_id})
            assert status == ["done"], f"premise: the claimed command is done, read {status!r}"
        finally:
            for connection in connections:
                await connection.close()
            await admin.close()
