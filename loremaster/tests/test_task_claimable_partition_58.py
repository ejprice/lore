"""Contract for packet **58**, Scope IN 4 — **#130**: the SERVED claimable set agrees with the claim CAS.

*Every claim in this file is scoped to the tree at ``1206233`` (branch ``feat/surreal-unification``),
2026-09-26, authored by ``contract-58``.  "RED at HEAD" means RED at that commit.*

Spec: ``docs/plans/v2/58-supersede-reanchor.md`` Scope IN 4; kickoff rulings
``docs/design/2026-09-26-packet58-kickoff-rulings.md`` @ ``c8d3241`` §5 — reading **B** (the author's
recorded choice): a SUPERSEDED row matches **no** ``status=`` filter (its stored status is stale by
construction — supersede never touches ``status``) and is **excluded from both** ``blocked=False`` and
``blocked=True`` (*"it is neither, it is superseded"*); an UNFILTERED ``query`` and ``get`` still serve
it, decorated ``[superseded → id]`` (finding #7's virtue, preserved).  ``status=superseded`` stays
"no tasks matched" (#130 shape (b) is 57's, not 58's).  (c): the claim-LOSS render ALREADY names
supersession at HEAD — PINNED here, not built; after 58 the ``superseded_blockers`` branch is reachable
only for LEGACY strands (rows superseded before 58 deployed — real on ``:18500``), seeded raw.

⚠ SPEC-SILENT, NOT PINNED: an ``owner=``-only query (no ``status=``/``blocked=``) over a superseded
row that has an owner — §5 names ``status=`` filters and the ``blocked`` partition only.  Flagged in
``REPORT-contract-58.md`` for a ruling.

Both directions of #130's own invariant, each ∀ over a DERIVED set with checked coverage:
*everything served as claimable IS claimable* (drive a claim at every served row) AND *nothing the CAS
refuses is served as claimable* — plus completeness (the genuinely claimable rows ARE served), which
kills the over-excluding build.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest_asyncio
from _reanchor_58_support import (
    CLAIMANT,
    OTHER_CLAIMANT,
    create,
    drive_to,
    ledger58,
    raw_relate,
    raw_seed_row,
    successor_of,
    supersede,
)
from _surreal_harness import SurrealEnv
from loremaster.tasks import (
    STATUS_BLOCKED,
    STATUS_DONE,
    STATUS_OPEN,
    TASK_STATUSES,
    TaskLedger,
)
from test_blocks_edge import _tool_seam

if TYPE_CHECKING:
    from loremaster.tasks import SupersedeResult
    # ⚠ DUAL (packet 58 contract r2, contract-58-r2 — lead directive #17055, the #461 shape): packet 58's
    # RULED, not-yet-built symbol, named STATICALLY for the typecheck gate.  Until the build lands it this
    # is a mypy error OWNED by `scripts/pending_contracts.yaml` bound `packet-58-contract`, which owns this
    # file's packet-58 pytest REDs too and self-destructs with the build.  Runtime-inert: no pin changed.
    _RULED_58: tuple[object, ...] = (SupersedeResult,)

__all__ = ["ledger58"]


@dataclass
class Partition:
    ledger: TaskLedger
    claimable: set[str]
    superseded_open: str
    superseded_blocked: str
    superseded_blocked_status: str
    blocked: str
    owned: str
    refused: set[str]


@pytest_asyncio.fixture()
async def partition(ledger58: tuple[TaskLedger, SurrealEnv]) -> Partition:
    """≥3 refusal causes + 2 genuinely claimable rows (kickoff §5 rider fixture)."""
    ledger, _env = ledger58
    done_blocker = await create(ledger, "a finished blocker")
    await drive_to(ledger, done_blocker, STATUS_DONE)
    open_blocker = await create(ledger, "an open blocker")
    claimable_plain = await create(ledger, "claimable, no dependencies")
    claimable_resolved = await create(ledger, "claimable, its only blocker is done", [done_blocker])
    # Refusal cause 1 — SUPERSEDED, stored status 'open', no blockers (HEAD serves it under
    # status=open AND blocked=False).
    superseded_open = await create(ledger, "reframed while open")
    await supersede(ledger, superseded_open)
    # Refusal cause 1b — SUPERSEDED with an OPEN blocker (HEAD serves it under blocked=True), and a
    # second one moved to 'blocked' before reframing (HEAD serves it under status=blocked).
    superseded_blocked = await create(ledger, "reframed while waiting", [open_blocker])
    await supersede(ledger, superseded_blocked)
    superseded_blocked_status = await create(ledger, "reframed while in status blocked")
    await drive_to(ledger, superseded_blocked_status, STATUS_BLOCKED)
    await supersede(ledger, superseded_blocked_status)
    # Refusal cause 2 — BLOCKED on an open row.
    blocked = await create(ledger, "blocked on an open row", [open_blocker])
    # Refusal cause 3 — OWNED.
    owned = await create(ledger, "held by someone else")
    assert (await ledger.claim_task(owned, OTHER_CLAIMANT)).claimed
    return Partition(
        ledger=ledger,
        claimable={claimable_plain, claimable_resolved},
        superseded_open=superseded_open,
        superseded_blocked=superseded_blocked,
        superseded_blocked_status=superseded_blocked_status,
        blocked=blocked,
        owned=owned,
        refused={superseded_open, superseded_blocked, superseded_blocked_status, blocked, owned},
    )


def _superseded(p: Partition) -> set[str]:
    return {p.superseded_open, p.superseded_blocked, p.superseded_blocked_status}


class TestASupersededRowMatchesNoStatusFilter:
    """RED at HEAD (``status=open`` / ``status=blocked`` serve superseded rows)."""

    async def test_no_status_filter_serves_a_superseded_row(self, partition: Partition) -> None:
        served_under: dict[str, set[str]] = {}
        for status in sorted(TASK_STATUSES):
            served = {t.id for t in await partition.ledger.query_tasks(status=status)}
            leaked = served & _superseded(partition)
            if leaked:
                served_under[status] = leaked
        assert not served_under, (
            f"superseded rows served under a status label: {served_under}. #130 (reading B): a "
            f"superseded row's stored status is stale by construction — serving it as "
            f"'{STATUS_OPEN}' is the lie #130 measured"
        )

    async def test_the_status_sweep_covered_every_status(self, partition: Partition) -> None:
        """Coverage is CHECKED (P1c): the sweep above ranges over ``TASK_STATUSES`` — derived from the
        ledger's own vocabulary — and that vocabulary must still include the two statuses HEAD leaks
        superseded rows under, else the sweep silently stops observing the defect."""
        assert {STATUS_OPEN, STATUS_BLOCKED} <= set(TASK_STATUSES)


class TestASupersededRowIsInNeitherPartition:
    """RED at HEAD."""

    async def test_blocked_False_excludes_superseded_rows(self, partition: Partition) -> None:
        served = {t.id for t in await partition.ledger.query_tasks(blocked=False)}
        assert not served & _superseded(partition), sorted(served & _superseded(partition))

    async def test_blocked_True_excludes_superseded_rows(self, partition: Partition) -> None:
        served = {t.id for t in await partition.ledger.query_tasks(blocked=True)}
        assert not served & _superseded(partition), (
            f"kickoff §5: a superseded row is NEITHER blocked nor unblocked; served under "
            f"blocked=True: {sorted(served & _superseded(partition))}"
        )

    async def test_the_unfiltered_query_and_get_STILL_serve_it_with_the_chain(
        self, partition: Partition
    ) -> None:
        """GREEN at HEAD — preserved-with-pin (finding #7: the chain stays visible)."""
        unfiltered = {t.id: t for t in await partition.ledger.query_tasks()}
        for task_id in _superseded(partition):
            assert task_id in unfiltered and unfiltered[task_id].superseded_by is not None
            assert (await partition.ledger.get_task(task_id)).superseded_by is not None
        rendered = await _tool_seam(partition.ledger).tasks(action="query")
        for task_id in _superseded(partition):
            successor = (await partition.ledger.get_task(task_id)).superseded_by
            assert f"[superseded → {successor}]" in rendered, (
                f"the unfiltered query render no longer marks {task_id} as superseded"
            )


class TestEverythingServedAsClaimableIsClaimableAndViceVersa:
    """RED at HEAD (direction 1: a superseded row is served and its claim LOSES)."""

    async def test_every_row_served_as_claimable_is_WON_by_a_claim(self, partition: Partition) -> None:
        served = [
            t for t in await partition.ledger.query_tasks(status=STATUS_OPEN, blocked=False)
            if t.owner is None
        ]
        attempted = 0
        losses = []
        for task in served:
            attempted += 1
            if not (await partition.ledger.claim_task(task.id, CLAIMANT)).claimed:
                losses.append(task.id)
        assert attempted == len(served) and attempted >= len(partition.claimable), (
            f"coverage: {attempted} claims for {len(served)} served rows"
        )
        assert not losses, (
            f"query_tasks(status=open, blocked=False) served {sorted(losses)} as claimable and the "
            f"claim CAS REFUSED them — #130: the served partition and the CAS disagree"
        )

    async def test_nothing_the_CAS_refuses_is_served_as_claimable(self, partition: Partition) -> None:
        served = {
            t.id for t in await partition.ledger.query_tasks(status=STATUS_OPEN, blocked=False)
        }
        assert not served & partition.refused, sorted(served & partition.refused)
        # CONTROL: each refused row really IS refused by the CAS (else the pin above proves nothing).
        for task_id in partition.refused:
            assert not (await partition.ledger.claim_task(task_id, CLAIMANT)).claimed, task_id

    async def test_every_genuinely_claimable_row_IS_served(self, partition: Partition) -> None:
        """Completeness — kills the over-excluding build (e.g. dropping every row that ever had a
        blocker, or every row with provenance events)."""
        served = {
            t.id for t in await partition.ledger.query_tasks(status=STATUS_OPEN, blocked=False)
        }
        assert partition.claimable <= served, sorted(partition.claimable - served)


class TestTheClaimLossRenderNamesSupersession:
    """GREEN at HEAD — kickoff §5(c) VERIFIED PRESENT at ``f4511ef`` and re-read at ``1206233``
    (``AppContext._render_claim_result``); PINNED so neither branch is "cleaned up" as dead."""

    async def test_a_claim_of_a_SUPERSEDED_task_names_its_successor(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        ledger, _env = ledger58
        task_id = await create(ledger, "reframed")
        successor = successor_of(await supersede(ledger, task_id))
        rendered = str(await _tool_seam(ledger).claim_task(task_id, CLAIMANT))
        assert f"superseded by {successor}" in rendered, rendered

    async def test_a_LEGACY_strand_still_names_the_superseded_blocker_and_its_successor(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        """After 58 a strand can no longer be PRODUCED by the verbs (re-anchor), so the
        ``superseded_blockers`` branch is reachable only through rows superseded before 58 deployed —
        seeded RAW here (the only door), exactly the shape ``:18500`` still holds."""
        ledger, _env = ledger58
        successor = await create(ledger, "the successor the legacy blocker moved to")
        legacy_blocker = "legacy58blocker0000000000000000"
        await raw_seed_row(ledger, legacy_blocker, blocked_by=[], superseded_by=successor)
        stranded = "legacy58stranded000000000000000"
        await raw_seed_row(ledger, stranded, blocked_by=[legacy_blocker])
        await raw_relate(ledger, legacy_blocker, stranded)
        result = await ledger.claim_task(stranded, CLAIMANT)
        assert not result.claimed and result.superseded_blockers == {legacy_blocker: successor}
        rendered = str(await _tool_seam(ledger).claim_task(stranded, CLAIMANT))
        assert legacy_blocker in rendered and successor in rendered and "SUPERSEDED" in rendered, rendered
