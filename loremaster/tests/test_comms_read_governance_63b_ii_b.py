"""Contract — packet 63b wave ii-b: the READ-side governance behavioural pins.

Design ``docs/design/2026-09-11-packet63b-ii-b-drain-update-ruling.md`` §9.5 (P7 — invisible-seq ack)
+ §13.2 (F-1 — the drain decodes-before-it-stamps rider). Authored by ``contract-63b-ii-b`` (Opus 4.8
contract author; CONTRACT TESTS ONLY — no production). Live TEST store ``ws://127.0.0.1:18000``
(NEVER :18500).

RED-AT-HEAD: the ii-b ``drain`` / ``ack`` take NO Subject/read_filter argument (the §4.B/§9.5
read-governance is unbuilt), so the ii-b-shaped call raises ``TypeError`` → a legible ``pytest.fail``.
On the ii-b build the read verbs resolve + filter by the Subject: an addressed-but-INVISIBLE seq is
``unknown_message`` (never a false ``already_acked(acked_at=None)``), and the one-txn drain does not
leave a decode-failing row STAMPED-AND-LOST.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
import pytest_asyncio
from _governed_contract import build_principal_and_keep_stores, member, seed_message_legacy
from _surreal_harness import connect_admin, drop_database, make_env, run, unique_database
from loremaster.agents import AgentRegistry
from loremaster.messages import MessageLedger
from loremaster.store import surreal_schema
from surrealdb import RecordID

_AGENT_TABLE = "agent"
_MESSAGE_TABLE = surreal_schema.MESSAGE_TABLE
_TO_RELATION = surreal_schema.TO_RELATION
_DIM = 8


def _bare(value: Any) -> str:
    text = str(getattr(value, "id", value))
    return text.split(":", 1)[-1] if ":" in text else text


async def _relate_edge(connection: Any, *, message_id: str, agent_bare: str) -> None:
    """RELATE one ``message->to->agent`` delivery edge, ``seen_at``/``acked_at`` NONE (endpoints must
    exist — the ``to`` edge is ENFORCED)."""
    await run(
        connection,
        f"RELATE $message->{_TO_RELATION}->$agent SET session = 'wave7', created_at = $now",
        {
            "message": RecordID(_MESSAGE_TABLE, message_id),
            "agent": RecordID(_AGENT_TABLE, agent_bare),
            "now": datetime.now(UTC),
        },
    )


@pytest_asyncio.fixture()
async def read_gov_world() -> Any:
    """A store with the REAL message/to schema, TWO principals (mine + a foreign one), ONE recipient
    agent (mine), and TWO messages addressed to me: a VISIBLE one (server scope) and an INVISIBLE one
    (the FOREIGN principal's principal-private — addressed to me by a `to` edge, but excluded by my
    read_filter). Yields ``(ledger, recipient_bare, subject, visible_seq, invisible_seq, connection,
    env)``. Reaped (NEVER :18500)."""
    env = make_env(database=unique_database(), dim=_DIM)
    principal_store, keep_store = await build_principal_and_keep_stores(env)
    connection = await connect_admin(env)
    registry = AgentRegistry(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    ledger = MessageLedger(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    try:
        await run(connection, surreal_schema.generate_agent_ddl())
        await run(connection, surreal_schema.generate_message_ddl())
        mine = await principal_store.create(email="mine@example.com", role="member")
        foreign = await principal_store.create(email="foreign@example.com", role="member")
        my_pid, foreign_pid = _bare(mine.id), _bare(foreign.id)
        recipient = (
            await registry.register(
                "recip", session="wave7", role="builder", owner_principal_id=my_pid
            )
        ).agent
        recipient_bare = _bare(recipient.id)
        # a VISIBLE message (server scope — any member sees it) addressed to me.
        visible_seq = 0
        visible_id = await seed_message_legacy(
            connection, sender_id=recipient_bare, session="wave7", seq=visible_seq, scope="server"
        )
        await _relate_edge(connection, message_id=visible_id, agent_bare=recipient_bare)
        # an INVISIBLE message: the FOREIGN principal's principal-private — addressed to me by a `to`
        # edge, but my read_filter EXCLUDES it (owner_principal != my principal).
        invisible_seq = 1
        invisible_id = await seed_message_legacy(
            connection, sender_id=recipient_bare, session="wave7", seq=invisible_seq,
            scope="principal-private", owner_principal=RecordID("principal", foreign_pid),
        )
        await _relate_edge(connection, message_id=invisible_id, agent_bare=recipient_bare)
        subject = member(my_pid, recipient_bare, frozenset())
        yield ledger, recipient_bare, subject, visible_seq, invisible_seq, connection, env
    finally:
        await ledger.close()
        await registry.close()
        await connection.close()
        await keep_store.close()
        await principal_store.close()
        await drop_database(env)


class TestAnAckOfAnInvisibleSeqIsUnknownMessage:
    """P7 (§9.5) — an ack over an addressed-but-INVISIBLE seq resolves THROUGH the read_filter, so it
    is (to this Subject) indistinguishable from a nonexistent message: fate ``unknown_message``, NOTHING
    stamped, never the false ``already_acked(acked_at=None)`` HEAD's ``_ack_entries`` ladder would give
    a naive build. Consistent with §4.3 ("an invisible message is neither served nor stamped") and it
    leaks no existence.

    RED at HEAD: ``ack`` takes no Subject/read_filter arg (the seq→message resolution is unfiltered) →
    the ii-b-shaped call raises TypeError → RED. On the ii-b build the invisible seq is unknown_message.
    A wrong build that filters only the CAS/read-back (not the resolution) gives
    ``already_acked(acked_at=None)`` → this pin's ``outcome == unknown_message`` RED."""

    @staticmethod
    async def _ack(ledger: Any, agent_id: str, seqs: list[int], subject: Any) -> Any:
        try:
            return await ledger.ack(agent_id=agent_id, seqs=seqs, subject=subject)
        except TypeError as error:
            pytest.fail(
                "RED-at-HEAD (right reason): MessageLedger.ack does not accept a `subject` argument — "
                "the §9.5 read-filtered seq resolution is unbuilt, so an invisible seq cannot be "
                f"distinguished from a nonexistent one. engine/py: {error}"
            )

    async def test_an_invisible_seq_is_unknown_message_and_stamps_nothing(
        self, read_gov_world: Any
    ) -> None:
        """⚠ RED at HEAD (missing subject arg). Ack the INVISIBLE seq → fate ``unknown_message``,
        ``acked_count == 0``, and the invisible edge's ``acked_at`` stays NONE (F5 zero delta). The
        QUANTIFIER leg: exactly one fate for the requested seq."""
        ledger, recipient_bare, subject, _visible_seq, invisible_seq, connection, _env = read_gov_world
        result = await self._ack(ledger, recipient_bare, [invisible_seq], subject)
        assert len(result.entries) == 1 and result.entries[0].seq == invisible_seq, (
            f"the ∀-request fate walk dropped/duplicated the requested seq: {result.entries!r}"
        )
        assert result.entries[0].outcome == "unknown_message", (
            f"an ack of an INVISIBLE seq must be `unknown_message` (§9.5 α — resolve seqs THROUGH the "
            f"read_filter), NOT `already_acked(acked_at=None)` (the naive HEAD ladder) nor `acked` (an "
            f"unfiltered ack). got outcome={result.entries[0].outcome!r} "
            f"acked_at={result.entries[0].acked_at!r}"
        )
        assert result.acked_count == 0, f"an invisible-seq ack stamped something: {result!r}"
        edge = await run(
            connection,
            f"SELECT acked_at FROM {_TO_RELATION} WHERE out = $agent AND in.seq = $seq",
            {"agent": RecordID(_AGENT_TABLE, recipient_bare), "seq": invisible_seq},
        )
        rows = edge if isinstance(edge, list) else []
        assert rows and all(row.get("acked_at") is None for row in rows), (
            f"the invisible edge was STAMPED by the ack (F5 would see a `to` delta) — an invisible "
            f"message is neither served nor stamped (§4.3): {rows!r}"
        )

    async def test_CONTROL_a_visible_seq_is_acked(self, read_gov_world: Any) -> None:
        """The discriminating control: a VISIBLE seq acked by the SAME subject → ``acked`` + stamped.
        Without it, `unknown_message` above could be a subject that sees NOTHING (a broken read_filter)
        rather than the invisible-vs-visible discrimination. RED at HEAD via the missing subject arg."""
        ledger, recipient_bare, subject, visible_seq, _invisible_seq, connection, _env = read_gov_world
        result = await TestAnAckOfAnInvisibleSeqIsUnknownMessage._ack(
            ledger, recipient_bare, [visible_seq], subject
        )
        assert result.entries[0].outcome == "acked" and result.acked_count == 1, (
            f"a VISIBLE seq must ack (proves the read_filter is not simply excluding everything): {result!r}"
        )
        edge = await run(
            connection,
            f"SELECT acked_at FROM {_TO_RELATION} WHERE out = $agent AND in.seq = $seq",
            {"agent": RecordID(_AGENT_TABLE, recipient_bare), "seq": visible_seq},
        )
        assert _one_row(edge).get("acked_at") is not None, "the visible edge was not stamped by ack"


class TestTheDrainDecodesBeforeItStamps:
    """F-1 (§13.2) — the ii-b §4.B one-txn drain must NOT leave a decode-failing served row
    STAMPED-AND-LOST: it either decodes BEFORE it stamps, or decodes per-row with a rejected row NOT
    stamped and rendered as a named fate. With R19 a junk grade cannot exist, so ``grade`` is moot, but
    the ORDERING property is GENERAL (any future decode-failing column) — this pins it by forcing a
    decode failure and asserting the edge is NOT stamped.

    RED at HEAD via the missing subject arg (the ii-b one-txn drain is unbuilt). On the ii-b build, if
    the one-txn shape STAMPS inside the transaction and DECODES in Python after commit, a decode failure
    leaves the row ``seen_at`` forever while the entry never reaches the agent — this pin catches that.
    """

    async def test_a_decode_failure_does_not_leave_the_row_stamped(
        self, read_gov_world: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at HEAD (missing subject arg). Force ``_row_to_inbox_entry`` to raise on the served
        row, drive the ii-b drain, and assert the delivery edge is NOT stamped (``seen_at IS NONE``) —
        a decode failure must not consume the delivery. On a one-txn build that stamps-then-decodes the
        edge is already stamped → RED (the §13.2 stamped-and-lost hazard)."""
        ledger, recipient_bare, subject, _visible_seq, _invisible_seq, connection, _env = read_gov_world

        def _boom(_self: Any, _row: dict[str, Any]) -> Any:
            raise ValueError("forced decode failure (F-1): a served row must not be stamped-and-lost")

        monkeypatch.setattr(MessageLedger, "_row_to_inbox_entry", _boom)
        try:
            await ledger.drain(agent_id=recipient_bare, limit=10, peek=False, subject=subject)
        except TypeError as error:
            if "subject" in str(error):
                pytest.fail(
                    "RED-at-HEAD (right reason): MessageLedger.drain does not accept a `subject` "
                    f"argument — the §4.B one-txn read is unbuilt. engine/py: {error}"
                )
            raise
        except ValueError:
            pass  # the forced decode failure propagated — expected; the edge must be unstamped below.
        rows = await run(
            connection,
            f"SELECT seen_at FROM {_TO_RELATION} WHERE out = $agent",
            {"agent": RecordID(_AGENT_TABLE, recipient_bare)},
        )
        listed = rows if isinstance(rows, list) else []
        assert listed and all(row.get("seen_at") is None for row in listed), (
            f"a served row whose DECODE failed was left STAMPED — the ii-b one-txn drain stamped "
            f"inside the txn and decoded after commit (STAMPED-AND-LOST, §13.2). It must decode BEFORE "
            f"it stamps, or stamp per-row with the rejected row NOT stamped. edges={listed!r}"
        )


def _one_row(result: Any) -> dict[str, Any]:
    rows = result if isinstance(result, list) else []
    assert rows, f"expected at least one row, got {result!r}"
    row = rows[0]
    assert isinstance(row, dict), f"expected a dict row, got {row!r}"
    return row


# --------------------------------------------------------------------------- #
# P4 (§9.1) + P6 (§9.4) — the served-RESPONSE bound-line pins, driven through a REAL credentialed
# AppContext (the F-DUP harness). The bound line's distinctive marker is "visible via <N> keep(s)".
# --------------------------------------------------------------------------- #

_BOUND_MARKER = "visible via"


class TestTheServedReadResponseCarriesTheBoundLineExactlyOnce:
    """P4 (§9.1 R7) — a served comms READ response carries the Subject-scope bound line EXACTLY ONCE,
    on the TOP-LEVEL render; sub-renders (the drain ROWS) never carry it. A count, so a sub-render
    clone (bound-per-row) reds, and a top-level render omitting it reds.

    RED at HEAD: the read handlers do not resolve a Subject and their renders do not carry the bound →
    the marker count is 0. On the ii-b build a multi-entry drain shows the bound ONCE above N rows."""

    async def test_a_multi_entry_drain_carries_the_bound_line_exactly_once(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """⚠ RED at HEAD (count 0). Drive a CREDENTIALED drain over TWO delivered messages and assert
        ``visible via`` appears EXACTLY once (one top-level bound, not one-per-row). At HEAD the drain
        handler ignores the capability and its render carries no bound → count 0 → RED. A build that
        clones the bound into ``_render_comms_drain_row`` → count 3 (2 rows + 1) → RED."""
        from _governed_contract import credentialed_app_context, register_owned

        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}
        ) as world:
            ctx, holder, pids = world["ctx"], world["holder"], world["pids"]
            holder["email"] = world["emails"]["alice"]
            cap, _agent_bare = await register_owned(
                ctx, "worker_a", owner_principal_id=pids["alice"], session="s1"
            )
            # TWO self-addressed sends (delivered + drainable — kickoff ruling 7), so the drain window
            # has multiple rows and a per-row bound clone would be visible as count > 1.
            for index in range(2):
                await ctx.comms(
                    action="send", agent="worker_a", session="s1", to=["worker_a"],
                    body=f"message {index}", grade="signal", capability=cap,
                )
            rendered = str(
                await ctx.comms(action="drain", agent="worker_a", session="s1", capability=cap)
            )
            count = rendered.count(_BOUND_MARKER)
            assert count == 1, (
                f"the drain response must carry the Subject-scope bound line ({_BOUND_MARKER!r}) EXACTLY "
                f"once (§9.1 R7/P4: first line of the TOP-LEVEL render; the drain ROWS never carry it). "
                f"count={count} — 0 means the handler resolved no Subject / the render omits the bound "
                f"(RED at HEAD); >1 means a sub-render clones it. rendered:\n{rendered}"
            )


class TestTheRollupMessageLegNamesTheCapabilityBound:
    """P6 (§9.4) — the rollup's MESSAGE leg. TOKENLESS: the leg is ONE bound line
    ``messages: identity required — pass capability=`` — NO count, NO rows (a count is an existence
    leak, 63-rulings §4.3). With a verified capability (ii-b): a FILTERED count + the scope bound line
    heads the LEG (leg-scoped, not response-scoped — the task/finding legs are ungoverned until 64).

    RED at HEAD: ``_rollup`` renders the message-activity leg UNCONDITIONALLY (unfiltered, no bound) and
    ``lore_tasks`` has no ``capability=`` seam → the tokenless render carries no ``identity required``
    line. On the ii-b build the tokenless message leg names the bound."""

    async def test_the_tokenless_rollup_message_leg_names_the_identity_bound(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """⚠ RED at HEAD — a TOKENLESS rollup's message leg is the single bound line
        ``messages: identity required — pass capability=`` (no count, no rows). At HEAD ``_rollup``
        renders a message-activity section (or omits it), never this named bound → RED. Driven through
        the real ``_rollup`` handler on a credentialed AppContext (tokenless = no capability resolved)."""
        from _governed_contract import credentialed_app_context

        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}
        ) as world:
            ctx = world["ctx"]
            world["holder"]["email"] = world["emails"]["alice"]
            rendered = str(await ctx._rollup(since=None, limit=None))  # noqa: SLF001 - handler surface
            assert "messages: identity required" in rendered, (
                "the TOKENLESS rollup message leg must be the named bound `messages: identity required "
                "— pass capability=` (§9.4: no count, no rows — a count is an existence leak). At HEAD "
                f"the leg renders unfiltered activity (or is omitted), never the bound. rendered:\n{rendered}"
            )
            # a count beside the bound is the existence leak §9.4 forbids on the tokenless leg.
            assert "messages activity" not in rendered, (
                "the TOKENLESS rollup served a `messages activity (N)` count/rows — that is the "
                "existence leak §9.4 replaces with the identity-required bound line"
            )
