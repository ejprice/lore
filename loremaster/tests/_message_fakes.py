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
than merely remembered: its consumers are exactly the packet-03 contract files
(``test_message_ledger.py``, ``test_comms_tool.py``) — never the shared
``_comms_fakes.py`` seam, so a not-yet-existing ``loremaster.messages`` can never
take an unrelated suite down with it.

The adversarial properties are documented at the class below; they mirror
``_comms_fakes.py``'s rather than re-deriving them.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import cast

from loremaster.agent_existence import format_unknown_agent_refusal
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
    MessageActivityWindow,
    MessageBodyError,
    MessageDrainResult,
    MessageGrade,
    MessageLedger,
    MessageSendResult,
    PendingTraffic,
    StoredMessage,
    UnknownRecipientError,
    UnknownSenderError,
    WaitingOnAnswer,
)
from loremaster.render import render_attributed

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
#    BEFORE any edge is written. ⚠ CORRECTED 2026-07-27: this note used to say
#    "the engine validates NEITHER endpoint" — TRUE when probe 1 ran, FALSE
#    since ``to`` gained ``ENFORCED`` in `df59f76`. The engine now refuses a
#    dangling ``out``; what it CANNOT do is teach, because it reports ONE bad
#    endpoint as untyped prose only AFTER the write, and the store seam's error
#    hygiene withholds even that (:mod:`loremaster.agent_existence` module
#    docstring). The app-level check remains the only layer that names EVERY bad
#    id BEFORE anything is written — which is exactly what this fake models, so
#    a suite riding it sees production's teaching failure, not the engine's.


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

        0-BASED, mirroring ``sequence::nextval`` under the default ``START 0``
        (store reference §5): returns the value that WOULD have been minted, then
        advances — so a fresh ledger's first burn is 0, exactly as its first send
        would have been (F2 parity).
        """
        burned = self.db.next_seq
        self.db.next_seq += 1
        return burned

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
            # #190 parity: production contains the caller value through
            # ``render_attributed`` (never a bare ``!r`` — control-char
            # sanitisation is same-line-forgery-blind). A ``{grade!r}`` clone here
            # was the exact drift class #190 names: a surface pin over this oracle
            # could never see production's actual wording.
            raise IllegalMessageGradeError(
                f"{render_attributed(grade)} is not a legal message grade; legal grades: "
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
        # ⚠ CALLS the production validator rather than cloning its rules. The
        # body/grade checks above are historical CLONES, and that pattern is
        # exactly how this oracle's `EmptyRecipientSetError` prose drifted away
        # from production's (finding #190) — a divergence no surface pin can see,
        # because every surface pin rides the fake. Routing the NEW policy through
        # the real staticmethod makes that class impossible here: there is one
        # implementation, and the fake cannot disagree with it about what is legal.
        MessageLedger._reject_oversize_pointers(
            thread=thread, task_id=task_id, refs=list(refs) if refs is not None else []
        )
        if not recipients:
            # #190 parity: the LEDGER's OWN wording, not the dispatcher's. The
            # fake used to serve "no other non-retired agent is registered" (the
            # dispatcher's framing), so no surface pin could ever observe
            # production's "is a caller error, not a broadcast" — the exact D4
            # blind spot #190 names.
            raise EmptyRecipientSetError(
                f"a send needs at least one recipient — the ledger never resolves a roster "
                f"(broadcast is the dispatcher's concern), so an empty recipient set in "
                f"session {session!r} is a caller error, not a broadcast"
            )
        # EVERY recipient is checked BEFORE any edge is written (probe 1 /
        # consequence #2: a partially-validated fan-out is N-1 good edges plus
        # one permanent, silent dangling receipt).
        # ⚠ The TEXT is production's own, CALLED not cloned (2026-07-27, cold audit
        # F3). This fake used to hand-write "unknown recipient(s): <names> — every
        # recipient must register before it can be sent to": no ids, a different
        # prefix, a different tail. Every pin over it was a name-substring check that
        # both strings satisfied, so a fake teaching a contract production does not
        # serve was invisible — finding #190's shape, which comment #5 above and the
        # ``_reject_oversize_pointers`` call two blocks up already name. Identities are
        # collected first-wins per ID exactly as
        # ``agent_existence.reject_unknown_agents`` collects them: two agents may share
        # a display name, so a name-keyed set silently merges two bad recipients into
        # one refusal line.
        # #190 / #247 parity, in PRODUCTION ORDER: the SENDER is validated BEFORE
        # the recipients (a message FROM a ghost is the worse fault, reported first
        # and on its own class). Raised via the SHARED refusal formatter, so this
        # is byte-identical to production's
        # ``reject_unknown_rows(agent_identities([sender]), error=UnknownSenderError)``.
        # The fake used to skip this door entirely — it raised NOTHING where
        # production raises, the parity gap #190's invariant exists to catch.
        if sender.id not in self.db.agents:
            raise UnknownSenderError(format_unknown_agent_refusal({sender.id: sender.name}))
        unknown: dict[str, str] = {}
        for ref in recipients:
            if ref.id not in self.db.agents:
                unknown.setdefault(ref.id, ref.name)
        if unknown:
            raise UnknownRecipientError(format_unknown_agent_refusal(unknown))
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
        # 0-BASED, mirroring production's ``sequence::nextval`` under the default
        # ``START 0`` (store reference §5; PROBED real_first_seq=0). A 1-based fake
        # was finding #190's shape one field over — every ``since=`` behavioural
        # pin rides this oracle, so a 1-based origin made ``since=0`` a benign
        # before-the-first sentinel on the fake while a strict-correct build lost
        # seq 0 on the 0-based real store (F1/F2). Assign THEN advance.
        seq = self.db.next_seq
        self.db.next_seq += 1
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

    async def pending_traffic(self, *, agent_id: str) -> PendingTraffic:
        """R4's two counts, computed INDEPENDENTLY of production.

        ⚠ **This deliberately does NOT delegate to
        :meth:`~loremaster.messages.MessageLedger.pending_traffic`, and that
        independence is the whole point of the fake leg.** A double that called
        production would launder a wrong production statement: whatever
        predicate production used, the fake would agree with it by
        construction, and SECTION D's two backends would stop being two
        opinions. The counts are re-derived here from the edge state directly,
        so a production build that drops R4's ``grade = 'directive'`` conjunct
        disagrees with this double and the ``"fake"`` leg reddens.

        The predicates mirror R4 as WRITTEN, not as production spells it:
        ``unread`` is an unstamped edge (any grade); ``unacked_directives`` is
        an unacked edge on a directive, **with no clause about ``seen_at``** —
        so an unseen directive counts in BOTH and a seen, unacked signal in
        NEITHER.
        """
        await asyncio.sleep(0)
        edges = [
            (self.db.messages[message_id], edge)
            for (message_id, edge_agent_id), edge in self.db.edges.items()
            if edge_agent_id == agent_id
        ]
        return PendingTraffic(
            unread=sum(1 for _message, edge in edges if edge.seen_at is None),
            unacked_directives=sum(
                1
                for message, edge in edges
                if edge.acked_at is None and message.grade == MESSAGE_GRADE_DIRECTIVE
            ),
        )

    def _inbox_entry(self, message: Message, agent_id: str) -> InboxEntry:
        """One drained row for ``agent_id`` — the ONE construction BOTH the plain
        window and the ``since=`` recovery read use, so the builder's later R1
        ``question=message.question`` passthrough is a single-line change here, not
        two copies that could drift."""
        edge = self.db.edges[(message.id, agent_id)]
        return InboxEntry(
            seq=message.seq,
            message_id=message.id,
            grade=message.grade,
            sender_name=message.sender_name,
            thread=message.thread,
            task_id=message.task_id,
            body=message.body,
            refs=list(message.refs),
            created_at=message.created_at,
            acked_at=edge.acked_at,
            ack_note=edge.ack_note,
            question=message.question,
        )

    def _delivered_after(self, agent_id: str, since: int) -> list[Message]:
        """DD-4.c recovery set: every message with an edge to ``agent_id`` whose
        seq is STRICTLY greater than ``since`` (SEEN or unseen), oldest-first."""
        return sorted(
            (
                self.db.messages[message_id]
                for (message_id, edge_agent_id) in self.db.edges
                if edge_agent_id == agent_id
                and self.db.messages[message_id].seq > since
            ),
            key=lambda message: message.seq,
        )

    async def drain(
        self, *, agent_id: str, limit: int, peek: bool = False, since: int | None = None
    ) -> MessageDrainResult:
        await asyncio.sleep(0)
        if since is not None:
            # DD-4.c RECOVERY READ: rows keyed by seq (``seq > since``, STRICT),
            # SEEN or unseen, oldest-first, bounded at ``limit`` — and NON-stamping,
            # because a recovery read must not consume the unseen rows a plain drain
            # still owns (``stamped_seqs`` is empty). This is the fake's INDEPENDENT
            # LEG-B reference; it does not delegate to production.
            recovered = self._delivered_after(agent_id, since)
            window = recovered[:limit]
            return MessageDrainResult(
                entries=[self._inbox_entry(message, agent_id) for message in window],
                total_pending=len(recovered),
                directive_pending=sum(
                    1 for message in recovered if message.grade == MESSAGE_GRADE_DIRECTIVE
                ),
                stamped_seqs=[],
                peeked=bool(peek),
            )
        pending = sorted(self._pending(agent_id), key=lambda message: message.seq)
        total_pending = len(pending)
        directive_pending = sum(
            1 for message in pending if message.grade == MESSAGE_GRADE_DIRECTIVE
        )
        window = pending[:limit]
        entries = [self._inbox_entry(message, agent_id) for message in window]
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
        # Same discipline as the pointer bounds in ``send``: CALL the policy, do
        # not clone it (see the note there and finding #190).
        MessageLedger._reject_oversize_note(note)
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

        An ANSWER satisfies FOUR conjuncts: DELIVERED TO this agent, ON the
        question's own thread, created AFTER it (``seq``), and sent by ANOTHER
        AGENT (ruling R2, ``docs/plans/v2/03a-2-consume-path-design-rulings.md``
        §R2 — a self-note is information, never INPUT, and the waiting state
        means "this agent needs input"; an explicit self-addressed send remains
        fully DELIVERABLE per kickoff ruling 7, it simply cannot discharge its
        own sender's debt). Computed exactly as ``orphaned`` is derived from
        ``heartbeat_at`` — nothing is stamped, so nothing can be lost, and no
        caller has to REMEMBER to clear it.

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
                candidate.thread == question.thread
                and candidate.seq > question.seq
                and candidate.sender_id != agent_id
                for candidate in delivered_to_me
            )
            if not answered:
                return WaitingOnAnswer(
                    thread=question.thread,
                    question_seq=question.seq,
                    asked_at=question.created_at,
                )
        return None

    # -- read compositions (packet 05a-iii, #322 DOUBLE-face parity) -----------
    # story's task-arc read and the rollup's messages-activity leg. Mirror the
    # real ledger's ``messages_for_task`` / ``message_activity_since`` EXACTLY —
    # same signatures, same ordering, same EXCLUSIVE ``created_at`` cursor, same
    # HONEST (uncapped) ``total``, same ValueError on a non-positive ``limit`` —
    # so a surface pin riding this fake sees production's read contract, not a
    # friendlier one. Re-derived INDEPENDENTLY over ``self.db`` (never a
    # delegation to production's query), so the fake can still FAIL a wrong build.

    async def messages_for_task(self, *, task_id: str) -> list[StoredMessage]:
        """Every message anchored to ``task_id``, OLDEST-FIRST by ``seq`` — the
        read ``story`` composes a task's message arc over (mirrors the real
        ledger; empty when none carry this ``task_id``).

        NONE-tolerant like the store's ``WHERE task_id = $task_id``: a message
        whose ``task_id`` reads NONE (``NONE = $task_id`` is false for a concrete
        id) is EXCLUDED by the predicate, never an error — so a partial stub is
        skipped exactly as the store skips a NONE row (see ``message_activity_since``).
        """
        await asyncio.sleep(0)
        matching = [
            message
            for message in self.db.messages.values()
            if getattr(message, "task_id", None) == task_id
        ]
        matching.sort(key=lambda message: message.seq)
        return [self._to_stored_message(message) for message in matching]

    async def message_activity_since(
        self, since: datetime, *, limit: int
    ) -> MessageActivityWindow:
        """Messages CREATED strictly after ``since``, oldest-first by
        ``created_at``, capped at ``limit``, with an HONEST (uncapped) ``total``.

        Mirrors the real ledger, including its ValueError on a bad ``limit`` and
        its EXCLUSIVE cursor. The filter models the STORE's ``WHERE created_at >
        $since`` faithfully, NONE-handling included: the real method's docstring
        relies on ``NONE > $since`` being FALSY (a legacy/absent ``created_at`` is
        excluded by the WHERE itself, per ``docs/reference/surrealdb-31-capabilities.md``
        §"a missing SELECT projection reads None"), so a message without a real
        ``created_at`` is EXCLUDED here rather than crashing the read — this oracle
        refuses a malformed row the same way production's WHERE would, instead of
        being friendlier than the store. ``total`` counts every match, not just the
        capped window.
        """
        await asyncio.sleep(0)
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"limit must be a positive integer, got {limit!r}")
        matching = [
            message
            for message in self.db.messages.values()
            if isinstance(getattr(message, "created_at", None), datetime)
            and message.created_at > since
        ]
        matching.sort(key=lambda message: message.created_at)
        return MessageActivityWindow(
            rows=[self._to_stored_message(message) for message in matching[:limit]],
            total=len(matching),
        )

    @staticmethod
    def _to_stored_message(message: Message) -> StoredMessage:
        """Project a stored ``Message`` into the ``StoredMessage`` read shape —
        the fake's stand-in for ``MessageLedger._row_to_stored_message``."""
        return StoredMessage(
            seq=message.seq,
            sender_name=message.sender_name,
            grade=message.grade,
            body=message.body,
            refs=list(message.refs),
            question=message.question,
            thread=message.thread,
            task_id=message.task_id,
            created_at=message.created_at,
        )
