"""DIAGNOSTIC pytest plugin — the MINIMAL repairs C3's harness needs so a correct
build can be graded, applied WITHOUT editing ``test_comms_footer.py``.

Authored 2026-08-01 by ``refbuild-c3-1`` while producing C3's satisfiability
receipt. ⚠ **A run under this plugin is NOT a satisfiability receipt for the
contract as it stands** — it is the CONSTRUCTION that distinguishes "the
contract is defective" from "the reference build is wrong", by showing which
pins go green the moment the harness stops contradicting itself. Every repair
below is a C-DEF the contract author must land IN the contract.

Use: ``pytest loremaster/tests/test_comms_footer.py -p c3_harness_repair``
(run from the repo root, which is on ``sys.path`` for ``-p`` resolution).
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest


def _registered_row(name: str, session: str) -> tuple[str, Any]:
    """A registry row whose ``id`` is the id the registry itself would mint.

    ⚠ **C-DEF 1, half two.** Registering the caller is not enough: the contract
    seeds the inbox under ``f"agent:{name}"``, while ``FakeAgentRegistry``
    mints ``uuid5(...)``. A build that resolves an identity and then counts
    ``pending_traffic(agent_id=row.id)`` therefore counts an EMPTY inbox. The
    two fakes must agree on the id, and the registry's is the real one (in
    production the ``to`` edge points at the ``agent`` row).
    """
    from loremaster.agents import STATUS_ACTIVE, Agent
    from test_comms_tool import FakeAgentRegistry

    agent_id = FakeAgentRegistry._agent_id(session, name)
    now = datetime.now(UTC)
    return agent_id, Agent(
        id=agent_id,
        name=name,
        session=session,
        role="builder",
        status=STATUS_ACTIVE,
        registered_at=now,
        heartbeat_at=now,
    )


@pytest.fixture(autouse=True)
def _repair_c3_harness(monkeypatch: pytest.MonkeyPatch) -> None:
    import test_comms_footer as c3
    from _finding_fakes import FakeFindingDatabase, FakeFindingLedger
    from _message_fakes import FakeMessageDatabase, FakeMessageLedger
    from _task_fakes import FakeTaskDatabase, FakeTaskLedger
    from test_comms_tool import FakeAgentDatabase, FakeAgentRegistry

    # ---- C-DEF 1: the harness never registers anybody in the registry -------
    def _footer_harness(
        *,
        unread: int,
        unacked: int,
        registered: tuple[str, str] | None = c3.CALLER_A,
        owner_identity: str | None = None,
        count_registry_reads: bool = False,
    ) -> Any:
        message_ledger = FakeMessageLedger(db=FakeMessageDatabase())
        registry = FakeAgentRegistry(db=FakeAgentDatabase())
        reads = {"count": 0}

        def _enrol(name: str, session: str) -> None:
            agent_id, row = _registered_row(name, session)
            registry.db.agents[agent_id] = row
            message_ledger.db.agents[agent_id] = name
            c3._seed_inbox(message_ledger, agent_id, unread=unread, unacked=unacked)

        if registered is not None:
            _enrol(*registered)
        if owner_identity is not None:
            # R8(2)'s fallback matches a REGISTERED agent name, so the owner
            # value must name a registry row too — not only a message-ledger key.
            _enrol(owner_identity, c3.CALLER_A[1])

        if count_registry_reads:
            inner = registry.get_agent

            async def _counting(*args: Any, **kwargs: Any) -> Any:
                reads["count"] += 1
                return await inner(*args, **kwargs)

            registry.get_agent = _counting  # type: ignore[method-assign]

        return SimpleNamespace(
            agent_registry=registry,
            message_ledger=message_ledger,
            task_ledger=FakeTaskLedger(db=FakeTaskDatabase()),
            finding_ledger=FakeFindingLedger(db=FakeFindingDatabase()),
            config=SimpleNamespace(
                comms=SimpleNamespace(
                    stale_heartbeat_s=600,
                    fleet_limit=20,
                    drain_limit=20,
                    brief_body_warn_chars=4000,
                )
            ),
            registry_reads=reads,
        )

    # ---- C-DEF 2: get/chain_head are driven with NO id_or_number ------------
    async def _findings_call(
        *,
        action: str,
        agent: tuple[str, str] | None,
        pending: bool,
        batch_writes: int | None = None,
    ) -> str:
        from loremaster.server import AppContext

        harness = _footer_harness(
            unread=c3.UNREAD_COUNT if pending else 0,
            unacked=c3.UNACKED_DIRECTIVE_COUNT if pending else 0,
        )
        kwargs: dict[str, Any] = {"action": action}
        if agent is not None:
            kwargs["agent"], kwargs["session"] = agent
        if batch_writes is not None:
            kwargs["items"] = await c3._batch_items(harness, writes=batch_writes)
            kwargs["actor"] = "contract-04b2-wavec-1"
        elif action in ("get", "chain_head"):
            # A read needs something to read: every correct build REFUSES a
            # missing 'id_or_number' (server._require_finding_ref), so the
            # contract's own call raises before any footer decision happens.
            seeded = await harness.finding_ledger.report(
                subject="a real subject",
                body="",
                area="test_comms_footer",
                category="contract_gap",
                created_by="contract-04b2-wavec-1",
            )
            kwargs["id_or_number"] = seeded.id
        elif action == "report":
            kwargs.update(
                subject="a real subject",
                area="test_comms_footer",
                category="contract_gap",
                created_by="contract-04b2-wavec-1",
            )
        return str(await AppContext.findings(harness, **kwargs))

    # ---- C-DEF 3: FakeTaskLedger.create does not exist ----------------------
    async def _claim_call(
        *, agent: tuple[str, str] | None, pending: bool, wins: bool
    ) -> str:
        from loremaster.server import AppContext

        harness = _footer_harness(
            unread=c3.UNREAD_COUNT if pending else 0,
            unacked=c3.UNACKED_DIRECTIVE_COUNT if pending else 0,
        )
        # ``create_task``, not ``create`` — and it returns the ID, not a Task.
        task_id = await harness.task_ledger.create_task(
            "a real subject",
            "a real description",
            created_by="contract-04b2-wavec-1",
        )
        if not wins:
            await harness.task_ledger.claim_task(task_id, "someone-else")
        kwargs: dict[str, Any] = {"task_id": task_id, "owner": "contract-04b2-wavec-1"}
        if agent is not None:
            kwargs["agent"], kwargs["session"] = agent
        return str(await AppContext.claim_task(harness, **kwargs))

    monkeypatch.setattr(c3, "_footer_harness", _footer_harness)
    monkeypatch.setattr(c3, "_findings_call", _findings_call)
    monkeypatch.setattr(c3, "_claim_call", _claim_call)
