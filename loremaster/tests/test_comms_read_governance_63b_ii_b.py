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
from _governed_contract import (
    build_principal_and_keep_stores,
    member,
    seed_message_legacy,
    session_keep_id_for,
)
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
                "recip",
                session="wave7",
                role="builder",
                owner_principal_id=my_pid,
                session_keep_id=await session_keep_id_for(
                    keep_store, principal_store, owner_principal_id=my_pid, session="wave7"
                ),  # r2 (A3): the owner travels WITH THE session keep
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
        decode_reached = False
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
            decode_reached = True  # the forced decode failure propagated — the decode WAS reached.
        # POSITIVE CONTROL (Finding 5) — the forced decode MUST have been reached, or this pin passes
        # VACUOUSLY: an OVER-filtering build (the inverse of the drain-filter hazard) that serves NOTHING
        # never calls `_row_to_inbox_entry`, raises no ValueError, and the `seen_at IS NONE` check below
        # is trivially true because nothing was ever served or stamped. This asserts the instrument fired
        # (the visible message was served and its decode attempted) so a no-rows-served build cannot
        # green this pin. NOT reached at HEAD (the TypeError guard `pytest.fail`s first).
        assert decode_reached, (
            "the forced decode failure never raised — the drain served NO row to decode, so this pin "
            "cannot prove decode-before-stamp; it would pass VACUOUSLY for an over-filtering build that "
            "serves nothing (Finding 5). The read_filter must serve the visible message, then the "
            "monkeypatched decode fires on it."
        )
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


class TestADrainServesOnlyTheVisibleMessage:
    """B2 / Finding 2 (§4.B) — the DRAIN read_filter FILTERING: the pin the whole wave turns on, and
    the DUAL of P7 (``TestAnAckOfAnInvisibleSeqIsUnknownMessage``) for the drain verb. A
    ``drain(subject=)`` SERVES the messages the Subject may see and EXCLUDES the invisible one; the
    excluded edge is NEITHER served NOR stamped (§4.3 "an invisible message is neither served nor
    stamped").

    Without this pin, a WRONG build whose ``drain(subject=)`` resolves the Subject (satisfying R6's
    deny-without-capability and rendering the P4 bound line) but does NOT splice the read_filter into
    its SELECT — serving ALL of the agent's ``to`` edges, invisible ones included — passes P1 / P4 /
    F-1 with no pin (verified: every other drain fixture holds only VISIBLE messages). That is exactly
    the §6 served-COUNT-over-the-served-SET / F4 "no argument moves the visible set beyond the Subject's
    authz" attack.

    RED at HEAD via the missing ``subject`` arg (the ii-b read-filtered drain is unbuilt). On the ii-b
    build the visible seq is served, the invisible seq is neither served nor stamped, and the CONTROL
    proves the exclusion is the read_filter (a principal mismatch), NOT deadness: the FOREIGN principal
    (the invisible message's OWNER), draining the SAME agent's inbox, DOES see it.
    """

    @staticmethod
    async def _drain(ledger: Any, agent_id: str, subject: Any) -> Any:
        try:
            return await ledger.drain(agent_id=agent_id, limit=10, peek=False, subject=subject)
        except TypeError as error:
            if "subject" in str(error):
                pytest.fail(
                    "RED-at-HEAD (right reason): MessageLedger.drain does not accept a `subject` "
                    f"argument — the §4.B read-filtered drain is unbuilt, so it cannot exclude an "
                    f"invisible message from the served set. engine/py: {error}"
                )
            raise

    async def test_a_drain_serves_only_the_visible_message(self, read_gov_world: Any) -> None:
        """⚠ RED at HEAD (missing subject arg). Drain as MY Subject → the VISIBLE (server-scope) seq is
        served and the INVISIBLE seq (a foreign principal's principal-private, addressed to me by a `to`
        edge) is NOT, and the invisible edge's ``seen_at`` stays NONE (§4.3). A build that resolves the
        Subject (R6/P4) but forgets to splice the read_filter into the SELECT serves BOTH → this reds."""
        ledger, recipient_bare, subject, visible_seq, invisible_seq, connection, _env = read_gov_world
        result = await self._drain(ledger, recipient_bare, subject)
        served = {entry.seq for entry in result.entries}
        assert visible_seq in served, (
            f"the VISIBLE (server-scope) message was NOT served by a drain of MY inbox — the read_filter "
            f"excludes everything, not just the invisible one (see the CONTROL). served={sorted(served)!r}"
        )
        assert invisible_seq not in served, (
            f"the INVISIBLE message (a FOREIGN principal's principal-private, addressed to me by a `to` "
            f"edge) was SERVED — the drain did not splice the read_filter into its SELECT, so it serves "
            f"ALL the agent's edges regardless of the Subject's authz (§6 count-over-set / F4). "
            f"served={sorted(served)!r}"
        )
        edge = await run(
            connection,
            f"SELECT seen_at FROM {_TO_RELATION} WHERE out = $agent AND in.seq = $seq",
            {"agent": RecordID(_AGENT_TABLE, recipient_bare), "seq": invisible_seq},
        )
        rows = edge if isinstance(edge, list) else []
        assert rows and all(row.get("seen_at") is None for row in rows), (
            f"the INVISIBLE edge was STAMPED by the drain — an invisible message is neither served nor "
            f"stamped (§4.3). edges={rows!r}"
        )

    async def test_CONTROL_a_foreign_subject_sees_the_invisible_message(
        self, read_gov_world: Any
    ) -> None:
        """The discriminating control (a probe needs a control): the SAME invisible message IS drainable
        when the read_filter PERMITS it — a Subject whose PRINCIPAL is the message's OWNER (the foreign
        principal), draining the SAME agent's inbox, serves it. This proves the exclusion in the pin
        above is the read_filter (a principal mismatch), NOT a dead/undrainable edge. RED at HEAD via
        the missing subject arg."""
        ledger, recipient_bare, _subject, _visible_seq, invisible_seq, connection, _env = read_gov_world
        owner_row = _one_row(
            await run(
                connection,
                f"SELECT owner_principal FROM {_MESSAGE_TABLE} WHERE seq = $seq",
                {"seq": invisible_seq},
            )
        )
        foreign_pid = _bare(owner_row["owner_principal"])
        foreign_subject = member(foreign_pid, recipient_bare, frozenset())
        result = await self._drain(ledger, recipient_bare, foreign_subject)
        served = {entry.seq for entry in result.entries}
        assert invisible_seq in served, (
            f"the invisible message is NOT drainable even by its OWNER principal — then the exclusion in "
            f"the pin above could be deadness, not the read_filter. The fixture message must be a live, "
            f"drainable edge that only MY read_filter excludes. served={sorted(served)!r}"
        )


# --------------------------------------------------------------------------- #
# P4 (§9.1) + P6 (§9.4) — the served-RESPONSE bound-line pins, driven through a REAL credentialed
# AppContext (the F-DUP harness). The bound line's distinctive marker is "visible via <N> keep(s)".
# --------------------------------------------------------------------------- #

_BOUND_MARKER = "visible via"


def _assert_bound_once(rendered: str, *, verb: str) -> None:
    """P4 (§9.1 R7) — the Subject-scope bound line appears EXACTLY once in a served READ response: on
    the TOP-LEVEL render, never cloned into a per-row / per-message / per-fate SUB-render. ONE
    IMPLEMENTATION — every carrier (drain/await/story/ack) calls this shared once-per-response POLICY
    rather than cloning the count (§9.1 requires the count PER VERB). count 0 = the handler resolved no
    Subject / the render omits the bound (RED at HEAD); count > 1 = a sub-render clones it (the wrong
    build the structural presence pin P5 cannot see)."""
    count = rendered.count(_BOUND_MARKER)
    assert count == 1, (
        f"the {verb} response must carry the Subject-scope bound line ({_BOUND_MARKER!r}) EXACTLY once "
        f"(§9.1 R7/P4: first line of the TOP-LEVEL render; sub-renders never carry it). count={count} — "
        f"0 means the handler resolved no Subject / the render omits the bound; >1 means a sub-render "
        f"clones it (the wrong build P5 cannot see). rendered:\n{rendered}"
    )


async def _rendered_read_or_red_at_head(coro: Any, *, verb: str) -> str:
    """Await a credentialed READ ``ctx.comms(action=<verb>, …, capability=cap)`` and return its rendered
    text — or ``pytest.fail`` RED-at-HEAD if the read verb does not accept a ``capability`` param yet.

    At HEAD the READ verbs are NOT capability-required (ii-a deferred them, §4/`test_the_reads_require_
    capability_in_ii_b`), so the dispatcher's foreign-param guard REJECTS ``capability`` for a read
    (``'capability' applies only to action='send'``) BEFORE the handler runs — a legitimate RED-at-HEAD
    that reflects the unbuilt read-capability seam. On the ii-b build the read accepts the capability,
    resolves the Subject, and its render carries the bound line, so ``_assert_bound_once`` then runs."""
    try:
        return str(await coro)
    except ValueError as error:
        if "capability" in str(error):
            pytest.fail(
                f"RED-at-HEAD (right reason): the {verb} verb does not accept a `capability` param yet "
                f"— it is not capability-required until ii-b, so the dispatcher rejects it as a foreign "
                f"param ({error}). On the ii-b build the read accepts the capability, resolves the "
                f"Subject, and its render carries the Subject-scope bound line exactly once."
            )
        raise


class TestTheServedReadResponseCarriesTheBoundLineExactlyOnce:
    """P4 (§9.1 R7) — a served comms READ response carries the Subject-scope bound line EXACTLY ONCE,
    on the TOP-LEVEL render; sub-renders (the drain ROWS, the story per-message blocks, the ack per-fate
    rows) never carry it. A count, so a sub-render clone (bound-per-row) reds, and a top-level render
    omitting it reds.

    ⚠ G1 (sidecar §14.0): the once-count is pinned PER VERB — drain, await (NON-empty AND EMPTY, where
    Leg 1 matters most), story (the per-message sub-render is the clone risk), ack (per-fate rows) —
    because the structural coverage pin (P5) forces PRESENCE of ``render_subject_bound`` in the derived
    render's source but CANNOT see a sub-render CLONE. Each sibling drives the REAL handler through a
    credentialed AppContext to a MULTI-ROW response and asserts the marker appears exactly once.

    RED at HEAD (two-stage, both consistent with the unbuilt read-governance): the READ verbs are not
    capability-required yet, so the dispatcher rejects ``capability`` as a foreign param
    (``_rendered_read_or_red_at_head`` turns that into a legible ``pytest.fail``). On the ii-b build the
    read accepts the capability, resolves the Subject, and a multi-row response shows the bound ONCE
    above N rows (a sub-render clone → count > 1 → RED)."""

    async def test_a_multi_entry_drain_carries_the_bound_line_exactly_once(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """⚠ RED at HEAD. Drive a CREDENTIALED drain over TWO delivered messages and assert
        ``visible via`` appears EXACTLY once (one top-level bound, not one-per-row). At HEAD the drain
        verb is not capability-required → the dispatcher rejects ``capability`` as foreign → RED (via
        ``_rendered_read_or_red_at_head``). On the ii-b build the drain resolves the Subject and its
        render carries the bound once (count 1); a build that clones the bound into
        ``_render_comms_drain_row`` → count 3 (2 rows + 1) → RED."""
        from _governed_contract import credentialed_app_context, register_owned

        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}
        ) as world:
            ctx, holder, pids = world["ctx"], world["holder"], world["pids"]
            holder["email"] = world["emails"]["alice"]
            cap, _agent_bare = await register_owned(
                ctx, "worker_a", owner_principal_id=pids["alice"], session="s1"
            )
            # Mint the session:s1 keep the send resolves its scope by key — via the register TOOL
            # (credentialed as alice), exactly as the LANDED ii-a send tests do; register_owned only
            # mints the capability (raw registry), never the keep (idempotent re-register keeps the
            # capability valid). See REPORT §FINDING: the landed drain P4 pin omitted this.
            await ctx.comms(action="register", agent="worker_a", session="s1", role="builder")
            # TWO self-addressed sends (delivered + drainable — kickoff ruling 7), so the drain window
            # has multiple rows and a per-row bound clone would be visible as count > 1.
            for index in range(2):
                await ctx.comms(
                    action="send", agent="worker_a", session="s1", to=["worker_a"],
                    body=f"message {index}", grade="signal", capability=cap,
                )
            rendered = await _rendered_read_or_red_at_head(
                ctx.comms(action="drain", agent="worker_a", session="s1", capability=cap), verb="drain"
            )
            _assert_bound_once(rendered, verb="drain")

    async def test_a_non_empty_await_carries_the_bound_line_exactly_once(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """⚠ RED at HEAD — G1: the once-per-response bound for the AWAIT verb (NON-empty).
        await shares the drain ROW render, so a per-row clone shows as count > 1. Drive a credentialed
        await over TWO delivered messages — the real awaiter's snapshot-first returns them WITHOUT a
        ~55s wait (nothing to wait for) — and assert the bound appears exactly once. At HEAD await is
        not capability-required → the dispatcher rejects ``capability`` as foreign → RED (via
        ``_rendered_read_or_red_at_head``); on the ii-b build the await render carries the bound once."""
        from _governed_contract import credentialed_app_context, register_owned

        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}
        ) as world:
            ctx, holder, pids = world["ctx"], world["holder"], world["pids"]
            holder["email"] = world["emails"]["alice"]
            cap, _agent_bare = await register_owned(
                ctx, "worker_a", owner_principal_id=pids["alice"], session="s1"
            )
            # Mint the session:s1 keep the send resolves its scope by key — via the register TOOL
            # (credentialed as alice), exactly as the LANDED ii-a send tests do; register_owned only
            # mints the capability (raw registry), never the keep (idempotent re-register keeps the
            # capability valid). See REPORT §FINDING: the landed drain P4 pin omitted this.
            await ctx.comms(action="register", agent="worker_a", session="s1", role="builder")
            for index in range(2):
                await ctx.comms(
                    action="send", agent="worker_a", session="s1", to=["worker_a"],
                    body=f"await message {index}", grade="signal", capability=cap,
                )
            # await PEEKS (stamps nothing); the two UNSEEN messages make the snapshot non-empty, so it
            # returns at once — no real wait — over the SHARED drain-row render.
            rendered = await _rendered_read_or_red_at_head(
                ctx.comms(action="await", agent="worker_a", session="s1", capability=cap),
                verb="non-empty await",
            )
            _assert_bound_once(rendered, verb="non-empty await")

    async def test_an_empty_await_carries_the_bound_line_exactly_once(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """⚠ RED at HEAD (count 0) — G1: the once-per-response bound for the EMPTY await, where Leg 1
        matters MOST (the bound names the caller's scope even with nothing to show). Monkeypatch the
        awaiter to return an EMPTY result IMMEDIATELY (no ~55s real wait) and assert the empty-await
        render names the bound exactly once. At HEAD await is not capability-required → the dispatcher
        rejects ``capability`` as foreign → RED (via ``_rendered_read_or_red_at_head``, before the fake
        awaiter is even reached); on the ii-b build the empty render names the bound once."""
        import loremaster.server as server_mod
        from _governed_contract import credentialed_app_context, register_owned
        from loremaster.messages import MessageDrainResult

        class _EmptyAwaiter:
            """A fake InboxAwaiter (the ``test_comms_await`` idiom) returning an empty result with no
            wait — the empty-await RENDER path with no real socket."""

            def __init__(self, **_kwargs: Any) -> None:
                pass

            async def await_inbox(
                self, *, agent_id: str, limit: int, thread: str | None = None
            ) -> Any:
                return MessageDrainResult(
                    entries=[], total_pending=0, directive_pending=0, stamped_seqs=[], peeked=True
                )

        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}
        ) as world:
            ctx, holder, pids = world["ctx"], world["holder"], world["pids"]
            holder["email"] = world["emails"]["alice"]
            cap, _agent_bare = await register_owned(
                ctx, "worker_a", owner_principal_id=pids["alice"], session="s1"
            )
            # Mint the session:s1 keep the send resolves its scope by key — via the register TOOL
            # (credentialed as alice), exactly as the LANDED ii-a send tests do; register_owned only
            # mints the capability (raw registry), never the keep (idempotent re-register keeps the
            # capability valid). See REPORT §FINDING: the landed drain P4 pin omitted this.
            await ctx.comms(action="register", agent="worker_a", session="s1", role="builder")
            monkeypatch.setattr(server_mod, "InboxAwaiter", _EmptyAwaiter, raising=False)
            rendered = await _rendered_read_or_red_at_head(
                ctx.comms(action="await", agent="worker_a", session="s1", capability=cap),
                verb="empty await",
            )
            _assert_bound_once(rendered, verb="empty await")

    async def test_a_multi_message_story_carries_the_bound_line_exactly_once(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """⚠ RED at HEAD — G1: the once-per-response bound for the STORY verb. story renders
        one sub-block PER message (``_render_story_message``) — the per-message sub-render is THE clone
        risk §9.1's count exists for (the sidecar names it). Anchor a task, send TWO messages carrying
        its task_id, and assert the story bound appears exactly once above the two message sub-blocks.
        At HEAD story is not capability-required → the dispatcher rejects ``capability`` as foreign → RED
        (via ``_rendered_read_or_red_at_head``); on the ii-b build the bound is once, a per-message
        clone → count 3 → RED."""
        from _governed_contract import credentialed_app_context, register_owned

        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}
        ) as world:
            ctx, holder, pids = world["ctx"], world["holder"], world["pids"]
            holder["email"] = world["emails"]["alice"]
            cap, _agent_bare = await register_owned(
                ctx, "worker_a", owner_principal_id=pids["alice"], session="s1"
            )
            # Mint the session:s1 keep the send resolves its scope by key — via the register TOOL
            # (credentialed as alice), exactly as the LANDED ii-a send tests do; register_owned only
            # mints the capability (raw registry), never the keep (idempotent re-register keeps the
            # capability valid). See REPORT §FINDING: the landed drain P4 pin omitted this.
            await ctx.comms(action="register", agent="worker_a", session="s1", role="builder")
            task_id = await ctx.task_ledger.create_task(
                "reticulate the splines", "a two-message task arc", created_by="worker_a"
            )
            for index in range(2):
                await ctx.comms(
                    action="send", agent="worker_a", session="s1", to=["worker_a"],
                    body=f"story message {index}", grade="signal", task_id=task_id, capability=cap,
                )
            rendered = await _rendered_read_or_red_at_head(
                ctx.comms(
                    action="story", agent="worker_a", session="s1", task_id=task_id, capability=cap
                ),
                verb="multi-message story",
            )
            _assert_bound_once(rendered, verb="multi-message story")

    async def test_a_multi_seq_ack_carries_the_bound_line_exactly_once(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """⚠ RED at HEAD — G1: the once-per-response bound for the ACK verb. ack renders
        per-fate rows (``_render_comms_ack`` groups by outcome), so a per-fate clone shows as count > 1.
        Send TWO self-addressed messages, learn their seqs via the admin connection (``seq`` is a global
        ``sequence::nextval``, not guaranteed 0-based), and ack BOTH; assert the ack response carries
        the bound exactly once. At HEAD ack is not capability-required → the dispatcher rejects
        ``capability`` as foreign → RED (via ``_rendered_read_or_red_at_head``); on the ii-b build the
        bound is once, a per-fate clone → count > 1 → RED."""
        from _governed_contract import credentialed_app_context, register_owned

        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}
        ) as world:
            ctx, holder, pids, admin_conn = (
                world["ctx"], world["holder"], world["pids"], world["admin_conn"]
            )
            holder["email"] = world["emails"]["alice"]
            cap, _agent_bare = await register_owned(
                ctx, "worker_a", owner_principal_id=pids["alice"], session="s1"
            )
            # Mint the session:s1 keep the send resolves its scope by key — via the register TOOL
            # (credentialed as alice), exactly as the LANDED ii-a send tests do; register_owned only
            # mints the capability (raw registry), never the keep (idempotent re-register keeps the
            # capability valid). See REPORT §FINDING: the landed drain P4 pin omitted this.
            await ctx.comms(action="register", agent="worker_a", session="s1", role="builder")
            for index in range(2):
                await ctx.comms(
                    action="send", agent="worker_a", session="s1", to=["worker_a"],
                    body=f"ack message {index}", grade="signal", capability=cap,
                )
            seq_rows = await run(admin_conn, f"SELECT seq FROM {_MESSAGE_TABLE} ORDER BY seq ASC")
            seqs = [int(row["seq"]) for row in (seq_rows if isinstance(seq_rows, list) else [])]
            assert len(seqs) == 2, f"expected two sent messages to ack, got seqs={seqs!r}"
            rendered = await _rendered_read_or_red_at_head(
                ctx.comms(action="ack", agent="worker_a", session="s1", seqs=seqs, capability=cap),
                verb="multi-seq ack",
            )
            _assert_bound_once(rendered, verb="multi-seq ack")


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

    async def test_a_capability_bearing_rollup_serves_the_filtered_count_headed_by_the_bound(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """⚠ RED at HEAD — G2 (sidecar §14.0): the WITH-capability half of §9.4 (the tokenless leg is
        pinned above). A VERIFIED capability yields a FILTERED count — ``messages activity (k)`` where
        ``k`` = the Subject-VISIBLE count, NOT the unfiltered N+M (the Leg-1 count-describes-its-set
        property) — AND the scope bound line HEADS THE LEG (immediately above the message-activity line),
        leg-scoped — NEVER the first line of the response, which would over-claim about the UNGOVERNED
        task/finding legs (§9.4: they are ungoverned until 64).

        Seed N=2 VISIBLE messages (owned by the caller's principal via the send seam) + M=1 INVISIBLE
        (a FOREIGN principal's principal-private, raw-seeded), plus one UNGOVERNED task leg so the message
        leg is not the response head. RED at HEAD: ``_rollup`` has no ``capability=`` seam — the exact
        ``pass capability=`` the TOKENLESS leg above already teaches the caller — so the ii-b-shaped call
        raises TypeError. On the ii-b build the message leg filters to k=2 and is headed by the bound.

        ⚠ Interface note (report §Decisions): the correct-build seam is ``_rollup(..., capability=)`` —
        grounded in the LANDED tokenless leg's own ``pass capability=`` teaching (not this reviser's
        invention). A builder that resolves the capability elsewhere must expose this seam for the caller
        the tokenless leg instructs."""
        from _governed_contract import credentialed_app_context, register_owned

        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member", "foreign": "member"}
        ) as world:
            ctx, holder, pids, admin_conn = (
                world["ctx"], world["holder"], world["pids"], world["admin_conn"]
            )
            holder["email"] = world["emails"]["alice"]
            cap, agent_bare = await register_owned(
                ctx, "worker_a", owner_principal_id=pids["alice"], session="s1"
            )
            # Mint the session:s1 keep the send resolves its scope by key — via the register TOOL
            # (credentialed as alice), the LANDED ii-a idiom; register_owned mints only the capability.
            await ctx.comms(action="register", agent="worker_a", session="s1", role="builder")
            # An UNGOVERNED leg (a task) so the message leg is NOT at the response head — a build that
            # heads the RESPONSE (not the leg) with the bound then over-claims about this task leg.
            await ctx.task_ledger.create_task(
                "an ungoverned task leg", "so the message leg is not the response head",
                created_by="worker_a",
            )
            # N = 2 VISIBLE messages (owned by alice's principal via the send seam) ...
            for index in range(2):
                await ctx.comms(
                    action="send", agent="worker_a", session="s1", to=["worker_a"],
                    body=f"visible activity {index}", grade="signal", capability=cap,
                )
            # ... and M = 1 INVISIBLE message (a FOREIGN principal's principal-private) seeded raw, so
            # the WHOLE-table `message_activity_since` sees N+M but the Subject read_filter sees only N.
            await seed_message_legacy(
                admin_conn, sender_id=agent_bare, session="s1", seq=999,
                scope="principal-private", owner_principal=RecordID("principal", pids["foreign"]),
            )
            try:
                rendered = str(await ctx._rollup(since=None, limit=None, capability=cap))  # noqa: SLF001
            except TypeError as error:
                if "capability" in str(error):
                    pytest.fail(
                        "RED-at-HEAD (right reason): AppContext._rollup does not accept a `capability` "
                        "argument — the ii-b rollup capability seam (the `pass capability=` the tokenless "
                        f"leg already teaches) is unbuilt, so the message leg cannot filter. py: {error}"
                    )
                raise
            lines = rendered.splitlines()
            activity_lines = [line for line in lines if "messages activity" in line]
            assert len(activity_lines) == 1, (
                f"expected exactly one `messages activity` leg line in a capability-bearing rollup, got "
                f"{activity_lines!r}. rendered:\n{rendered}"
            )
            activity_index = lines.index(activity_lines[0])
            activity_line = activity_lines[0]
            # (1) FILTERED count: k = the Subject-VISIBLE count (2), NEVER the unfiltered N+M (3).
            assert "2" in activity_line and "3" not in activity_line, (
                f"the capability-bearing rollup message leg must serve the FILTERED count 2 (the "
                f"Subject-visible messages), NOT 3 (the unfiltered set incl. the foreign principal's "
                f"principal-private message) — a served count describes the set its label claims "
                f"(Leg 1, §9.4). leg line: {activity_line!r}\nrendered:\n{rendered}"
            )
            # (2) the bound HEADS the LEG (immediately above the activity line), never the response head.
            preceding = next(
                (lines[i] for i in range(activity_index - 1, -1, -1) if lines[i].strip()), ""
            )
            assert _BOUND_MARKER in preceding, (
                f"the Subject-scope bound line must HEAD the message leg (immediately above `messages "
                f"activity`); nearest preceding non-empty line was {preceding!r}. rendered:\n{rendered}"
            )
            assert lines and _BOUND_MARKER not in lines[0], (
                "the scope bound is the FIRST line of the response — it must be LEG-scoped (heading the "
                "message leg only), not response-scoped: the task/finding legs are ungoverned until 64, "
                f"so a response-head bound over-claims about them (§9.4). rendered:\n{rendered}"
            )
            assert rendered.count(_BOUND_MARKER) == 1, (
                f"the rollup scope bound must appear EXACTLY once (leg-scoped, not per-row/response), "
                f"got {rendered.count(_BOUND_MARKER)}. rendered:\n{rendered}"
            )
