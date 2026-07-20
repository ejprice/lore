"""ADVERSARIAL in-memory fake for the packet-03 MESSAGE GRAPH ledger.

⚠ THIS FILE IS SEPARATE FROM ``_comms_fakes.py`` ON PURPOSE, and the reason is a
DEFECT THIS CONTRACT SHIPPED AND HAD TO FIX.

``_comms_fakes.py`` is a SHARED fixture module with seven consumers. The message
fake was originally appended there, which gave it a module-level
``from loremaster.messages import ...`` — a module that does not exist until
packet 03 lands. At clean HEAD that import error propagated to every consumer
and made SIX pre-existing suites **UNCOLLECTABLE** (not red — uncollectable),
including ``test_brief_ledger.py`` and ``test_agent_registry.py``, which have
nothing to do with packet 03. Roughly 1,220 tests stopped being collected, and
the tail read ``no tests collected`` — the shape repo law names as the one that
reads green behind a pipe.

**RED and UNCOLLECTABLE are different states.** A red test runs and fails for its
own reason; an uncollectable module never loads and takes unrelated suites down
with it.

Neither the author's satisfiability run nor the contract-adversary's could see
it: both graded in scratch copies containing the REFERENCE IMPLEMENTATION, where
``loremaster.messages`` exists and collection succeeds. That is finding **#133**
verbatim — *a satisfiability receipt that skips the PRE-EXISTING suites the
change's seam touches is not a receipt.*

Living in its own module makes the regression STRUCTURALLY IMPOSSIBLE rather
than merely remembered: only ``test_message_ledger.py`` imports this file, so
the blast radius of the not-yet-existing module is the one new contract file,
which is where contract-first wants it.

The adversarial properties are documented at the class below; they mirror
``_comms_fakes.py``'s rather than re-deriving them.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import cast

from loremaster.briefs import AgentRefLike
from loremaster.messages import (
    MESSAGE_BODY_MAX_CHARS,
    MESSAGE_GRADE_DIRECTIVE,
    MESSAGE_GRADES,
    EmptyRecipientSetError,
    IllegalMessageGradeError,
    InboxEntry,
    Message,
    MessageAckEntry,
    MessageAckResult,
    MessageBodyError,
    MessageDrainResult,
    MessageGrade,
    MessageSendResult,
    UnknownRecipientError,
    WaitingOnAnswer,
)

STATUS_INPUT_REQUIRED = "input_required"


def _utc_now() -> datetime:
    """A tz-aware UTC timestamp — every stamped time in this fake uses this."""
    return datetime.now(UTC)

# ---------------------------------------------------------------------------
# MessageLedger fake (packet 03 — the message graph)
# ---------------------------------------------------------------------------
#
# Adversarial properties, mirroring the two fakes above rather than re-deriving
# them:
#
# 1. :meth:`FakeMessageLedger.drain` sources its rows from a DETERMINISTIC
#    NON-INSERTION order (the pending list is sorted DESCENDING by message id
#    before the real seq-ascending sort is applied) — a build that leans on
#    "the order I sent them in" breaks here exactly as it would against a real
#    ``SELECT`` with no incidental ordering guarantee.
# 2. Every public ``async`` method opens with ``await asyncio.sleep(0)``.
# 3. The seq mint is an atomic no-``await`` span (models ``sequence::nextval``'s
#    server-side atomicity — probe 3c, 320/320 distinct at 16-way), and the
#    message row + its N delivery edges are written in ONE further no-``await``
#    span, because production composes mint + CREATE + N×RELATE inside ONE
#    ``execute_transaction`` (probe 3 leg B). A fake that yielded between the
#    row and the edges would model the partially-sent build the atomicity pins
#    exist to catch.
# 4. The write-once CAS stamps are modelled EXACTLY as
#    ``UPDATE ... WHERE <field> IS NONE``: a second stamp with a LATER value is
#    a no-op, and at the raw-store level that no-op is INDISTINGUISHABLE from
#    "no such edge" and "not your edge" (probe 4c) — so the disambiguation the
#    module owes its caller must be real here too, not inherited from a richer
#    fake return.
# 5. Recipient existence is checked against :attr:`FakeMessageDatabase.agents`
#    BEFORE any edge is written (probe 1: the engine validates NEITHER endpoint
#    — a bogus ``out`` silently writes a permanent delivery receipt for an
#    agent who does not exist, and ``->to->agent`` traversal reports the ghost
#    as a first-class recipient).


@dataclass(frozen=True)
class FakeDeliveryEdge:
    """One ``message->to->agent`` delivery edge's state, by value."""

    session: str
    created_at: datetime
    seen_at: datetime | None = None
    acked_at: datetime | None = None
    ack_note: str | None = None


@dataclass
class FakeMessageDatabase:
    """The shared in-memory ``message`` + ``to`` store (plus the ``agent``
    id->name mapping the recipient-existence check reads).

    ``edges`` is keyed by ``(message_id, agent_id)`` — the UNIQUE(in, out)
    idiom — so a repeated recipient inside one send collides here exactly as
    the real index makes it collide (probe 2's positive control).

    ``next_seq`` models the native ``DEFINE SEQUENCE`` counter: monotonic,
    never reset by a re-DEFINE, and NOT gapless
    (:meth:`FakeMessageLedger.burn_seq` lets a contract force a gap the way an
    aborted transaction does).
    """

    messages: dict[str, Message] = field(default_factory=dict)
    edges: dict[tuple[str, str], FakeDeliveryEdge] = field(default_factory=dict)
    agents: dict[str, str] = field(default_factory=dict)
    next_seq: int = 0


class FakeMessageLedger:
    """ADVERSARIAL in-memory stand-in for :class:`~loremaster.messages.MessageLedger`.

    Every method's PUBLIC surface (name, parameters, return type, raised
    exceptions) matches the real ledger exactly; only the storage is a plain
    in-memory dict rather than a SurrealDB connection.
    """

    def __init__(self, *, db: FakeMessageDatabase | None = None) -> None:
        self.db = db if db is not None else FakeMessageDatabase()

    # -- lifecycle ------------------------------------------------------------

    async def ensure_ready(self) -> None:
        await asyncio.sleep(0)

    async def close(self) -> None:
        await asyncio.sleep(0)

    # -- test affordances (deliberately NOT part of the production surface) ---

    def register_agent(self, *, agent_id: str, name: str) -> None:
        """Make ``agent_id`` resolvable — the fake's stand-in for a row in the
        ``agent`` table the real ledger's existence check SELECTs.
        """
        self.db.agents[agent_id] = name

    def burn_seq(self) -> int:
        """Consume a sequence number without writing a message — exactly what
        an aborted transaction does to a native sequence (probe 3 leg C).
        """
        self.db.next_seq += 1
        return self.db.next_seq

    # -- send -----------------------------------------------------------------

    async def send(
        self,
        *,
        sender: AgentRefLike,
        session: str,
        body: str,
        grade: str,
        recipients: Sequence[AgentRefLike],
        thread: str | None = None,
        task_id: str | None = None,
        refs: Sequence[str] | None = None,
        set_status: str | None = None,
    ) -> MessageSendResult:
        await asyncio.sleep(0)
        if grade not in MESSAGE_GRADES:
            raise IllegalMessageGradeError(
                f"{grade!r} is not a legal message grade; legal grades: "
                f"{', '.join(sorted(MESSAGE_GRADES))}"
            )
        trimmed = body.strip()
        if not trimmed:
            raise MessageBodyError("a message body must not be empty or whitespace-only")
        if len(trimmed) > MESSAGE_BODY_MAX_CHARS:
            raise MessageBodyError(
                f"body is {len(trimmed)} chars, over the {MESSAGE_BODY_MAX_CHARS}-char cap — "
                f"messages carry POINTERS: put the content in a report or finding and "
                f"reference it in refs"
            )
        if not recipients:
            raise EmptyRecipientSetError(
                "a send needs at least one recipient — no other non-retired agent is "
                f"registered in session {session!r}"
            )
        # EVERY recipient is checked BEFORE any edge is written (probe 1 /
        # consequence #2: a partially-validated fan-out is N-1 good edges plus
        # one permanent, silent dangling receipt).
        unknown = sorted({ref.name for ref in recipients if ref.id not in self.db.agents})
        if unknown:
            raise UnknownRecipientError(
                f"unknown recipient(s): {', '.join(unknown)} — every recipient must register "
                f"before it can be sent to"
            )
        # Dedupe BEFORE the fan-out (probe 2: UNIQUE(in, out) makes a repeated
        # recipient a LOUD engine error, never a silent de-duplication).
        deduped: list[AgentRefLike] = []
        seen_ids: set[str] = set()
        for ref in recipients:
            if ref.id in seen_ids:
                continue
            seen_ids.add(ref.id)
            deduped.append(ref)
        now = _utc_now()
        # --- the mint: an atomic no-``await`` span ---------------------------
        self.db.next_seq += 1
        seq = self.db.next_seq
        # --- end mint ---
        message_id = f"{seq:026x}"  # a monotonic, time-clustered stand-in for ulid()
        message = Message(
            id=message_id,
            seq=seq,
            session=session,
            thread=thread if thread is not None else session,
            sender_id=sender.id,
            sender_name=sender.name,
            grade=cast(MessageGrade, grade),
            body=trimmed,
            refs=list(refs) if refs is not None else [],
            task_id=task_id,
            # RULING 9: ``set_status='input_required'`` does not STORE a waiting
            # state — it marks THIS message as the question whose thread the
            # derivation reads. Nothing un-parks anyone; there is nothing to
            # un-park.
            question=set_status == STATUS_INPUT_REQUIRED,
            created_at=now,
        )
        # --- the row + EVERY delivery edge: ONE no-``await`` span ------------
        self.db.messages[message_id] = message
        for ref in deduped:
            self.db.edges[(message_id, ref.id)] = FakeDeliveryEdge(session=session, created_at=now)
        # --- end atomic span ---
        return MessageSendResult(
            message=message.model_copy(deep=True),
            recipient_names=sorted(ref.name for ref in deduped),
            recipient_count=len(deduped),
        )

    # -- drain ----------------------------------------------------------------

    def _pending(self, agent_id: str) -> list[Message]:
        """Every message carrying an UNSTAMPED (``seen_at IS NONE``) edge to
        ``agent_id`` — in a deliberately WRONG order (adversarial property 1).
        """
        pending = [
            self.db.messages[message_id]
            for (message_id, edge_agent_id), edge in self.db.edges.items()
            if edge_agent_id == agent_id and edge.seen_at is None
        ]
        pending.sort(key=lambda message: message.id, reverse=True)
        return pending

    async def drain(self, *, agent_id: str, limit: int, peek: bool = False) -> MessageDrainResult:
        await asyncio.sleep(0)
        pending = sorted(self._pending(agent_id), key=lambda message: message.seq)
        total_pending = len(pending)
        directive_pending = sum(
            1 for message in pending if message.grade == MESSAGE_GRADE_DIRECTIVE
        )
        window = pending[:limit]
        entries = [
            InboxEntry(
                seq=message.seq,
                message_id=message.id,
                grade=message.grade,
                sender_name=message.sender_name,
                thread=message.thread,
                task_id=message.task_id,
                body=message.body,
                refs=list(message.refs),
                created_at=message.created_at,
                acked_at=self.db.edges[(message.id, agent_id)].acked_at,
                ack_note=self.db.edges[(message.id, agent_id)].ack_note,
            )
            for message in window
        ]
        stamped: list[int] = []
        if not peek:
            now = _utc_now()
            # Stamps EXACTLY the rendered window — an elided message stays
            # unread (no cursor arithmetic at all).
            for message in window:
                key = (message.id, agent_id)
                edge = self.db.edges[key]
                if edge.seen_at is None:
                    self.db.edges[key] = replace(edge, seen_at=now)
                    stamped.append(message.seq)
        return MessageDrainResult(
            entries=entries,
            total_pending=total_pending,
            directive_pending=directive_pending,
            stamped_seqs=stamped,
            peeked=peek,
        )

    # -- ack ------------------------------------------------------------------

    async def ack(
        self, *, agent_id: str, seqs: Sequence[int], note: str | None = None
    ) -> MessageAckResult:
        await asyncio.sleep(0)
        by_seq = {message.seq: message for message in self.db.messages.values()}
        entries: list[MessageAckEntry] = []
        now = _utc_now()
        for seq in seqs:
            message = by_seq.get(seq)
            if message is None:
                entries.append(MessageAckEntry(seq=seq, outcome="unknown_message", acked_at=None))
                continue
            key = (message.id, agent_id)
            edge = self.db.edges.get(key)
            if edge is None:
                entries.append(MessageAckEntry(seq=seq, outcome="not_addressed", acked_at=None))
                continue
            if edge.acked_at is not None:
                # WRITE-ONCE: the existing stamp is returned UNCHANGED — a
                # second ack carrying a LATER ``now`` must never overwrite it.
                entries.append(
                    MessageAckEntry(seq=seq, outcome="already_acked", acked_at=edge.acked_at)
                )
                continue
            # ``note`` lands on the edge the CAS actually WON — never on an
            # already-acked one (that would be a second write through a
            # write-once door) and never on a message that is not ours.
            self.db.edges[key] = replace(edge, acked_at=now, ack_note=note)
            entries.append(MessageAckEntry(seq=seq, outcome="acked", acked_at=now))
        return MessageAckResult(
            entries=entries,
            acked_count=sum(1 for entry in entries if entry.outcome == "acked"),
            already_acked_count=sum(1 for entry in entries if entry.outcome == "already_acked"),
        )

    # -- the DERIVED waiting state (ruling 9) ---------------------------------

    async def awaiting_answer(self, *, agent_id: str) -> WaitingOnAnswer | None:
        """Derived, never stored: this agent is awaiting input IFF it has a
        question thread carrying no answer.

        An ANSWER is any message DELIVERED TO this agent on the question's own
        thread, created after the question. Computed exactly as ``orphaned`` is
        derived from ``heartbeat_at`` — nothing is stamped, so nothing can be
        lost, and no caller has to REMEMBER to clear it.

        An INDEPENDENT implementation over ``self.db`` (never a delegation to
        production's own query), so this fake stays able to FAIL a wrong build.
        Returns the OLDEST unanswered question — the longest-standing debt.
        """
        await asyncio.sleep(0)
        questions = sorted(
            (
                message
                for message in self.db.messages.values()
                if message.question and message.sender_id == agent_id
            ),
            key=lambda message: message.seq,
        )
        delivered_to_me = [
            self.db.messages[message_id]
            for (message_id, edge_agent_id) in self.db.edges
            if edge_agent_id == agent_id
        ]
        for question in questions:
            answered = any(
                candidate.thread == question.thread and candidate.seq > question.seq
                for candidate in delivered_to_me
            )
            if not answered:
                return WaitingOnAnswer(
                    thread=question.thread,
                    question_seq=question.seq,
                    asked_at=question.created_at,
                )
        return None
