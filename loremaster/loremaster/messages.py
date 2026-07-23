"""The durable, store-and-forward MESSAGE LEDGER (packet 03a — the comms graph).

:class:`MessageLedger` is the primitive every ``lore_comms`` send/inbox action
rides: an atomic, all-or-nothing fan-out (:meth:`~MessageLedger.send`) that mints
a native-sequence ordering key, writes ONE ``message`` node, and RELATEs ONE
``message->to->agent`` delivery edge per recipient — plus the windowed inbox
read (:meth:`~MessageLedger.drain`). It rides the SAME store machinery the rest
of the layer uses (:mod:`loremaster.briefs`/:mod:`loremaster.tasks`):

* one lazily-opened, signed-in WS connection, self-healed on a mid-life transport
  failure, reusing the shared error-classification seam in
  :mod:`loremaster.store._txn` — a transport fault surfaces as
  :class:`~loremaster.store._txn.SurrealConnectionError`, a domain rejection as
  :class:`~loremaster.store._txn.SurrealStoreError`, never a raw engine string;
* :func:`~loremaster.store._txn.execute_transaction` /
  :func:`~loremaster.store._txn.compose` apply the ``message`` + ``to`` +
  ``message_seq`` schema slice
  (:func:`~loremaster.store.surreal_schema.generate_message_ddl`) at
  :meth:`~MessageLedger.ensure_ready` and compose the atomic ``send`` write,
  verifying EVERY statement.

Binding sources — CITED, never re-transcribed:
``docs/plans/v2/03a-1-comms-ledger-send.md`` / ``03a-comms-message-ledger.md``
(Scope IN/OUT, the rulings) · ``docs/reference/surrealdb-31-capabilities.md`` §1.1
(the SEQUENCE row), §2 (CONTENT writes / silent-``None`` projections), §3
(``execute_transaction`` never ``query()``), §4 (bound-``RecordID`` RELATE, the
dangling-edge hazard on BOTH endpoints, ``ENFORCED``, UNIQUE-on-edge ⇒ dedupe
before the loop), §5 (the ONE retry driver, ``sequence::nextval``, gaps are REAL),
§7 (RELATE syntax). The public surface below is the contract test's own pinned
API (``loremaster/tests/test_message_ledger.py``) — this module implements it,
never redefines it.

DELIBERATE DECOUPLING, inherited from :class:`~loremaster.briefs.BriefLedger`
(``briefs.py`` module docstring): this ledger NEVER imports
:mod:`loremaster.agents`. ``send`` accepts an externally-resolved sender/recipient
identity (anything satisfying :class:`~loremaster.agent_ref.AgentRefLike`); the
DISPATCHER resolves the roster, which is where broadcast semantics and the
exclude-the-sender rule live (``test_comms_tool.py``). What the ledger still owns
— because the engine validates NEITHER RELATE endpoint (store reference §4,
finding #105) — is that EVERY supplied recipient id must EXIST in the ``agent``
table before a single ``RELATE`` runs: a raw SELECT over ``agent`` by id, NOT an
import of the registry module, so the decoupling holds.

⚠ SCOPE (03a-1, the SEND path): :meth:`~MessageLedger.ack` and
:meth:`~MessageLedger.awaiting_answer` are packet 03a-2 (the CONSUME path) — they
land here as :class:`NotImplementedError` stubs so the module imports and the full
type surface exists, and their contract pins stay RED for 03a-2. NOTE:
:meth:`~MessageLedger.drain` is IMPLEMENTED here (not stubbed) because the 03a-1
SEND contract verifies delivery THROUGH ``drain(peek=True)`` — stubbing it makes
the assigned SEND pins unsatisfiable (see ``REPORT-builder-03a1.md``).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict
from surrealdb import AsyncSurreal, RecordID
from ulid import ULID

from loremaster.agent_ref import AgentRefLike
from loremaster.store._txn import (
    _CONNECTION_ERRORS,
    SurrealConnectionError,
    SurrealStoreError,
    TxnContentionExhaustedError,
    TxnFragment,
    _SurrealConnection,
    bootstrap_session,
    compose,
    execute_transaction,
    run_query,
)
from loremaster.store.surreal_schema import (
    _MESSAGE_GRADE_DIRECTIVE,
    _MESSAGE_GRADE_SIGNAL,
    AGENT_TABLE,
    MESSAGE_SEQUENCE_NAME,
    MESSAGE_TABLE,
    TO_RELATION,
    generate_message_ddl,
)
from loremaster.store.surreal_schema import (
    MESSAGE_BODY_MAX_CHARS as MESSAGE_BODY_MAX_CHARS,  # noqa: PLC0414 (re-export; landmine #4: never redefined)
)

logger = logging.getLogger(__name__)

# --- closed vocabularies -----------------------------------------------------

# The two-value ``message.grade`` domain. The Literal is a typing-only restatement
# (a ``Literal`` cannot reference runtime values); the RUNTIME constants come from
# the schema slice's own domain so the ledger's app-level check and the store's
# ASSERT can never spell the vocabulary differently (DRY — ONE source for the
# policy value, matching :data:`MESSAGE_BODY_MAX_CHARS`, and mirroring
# ``_comms_fakes``'s import of ``briefs._KNOWN_BRIEFS_CAP``). The contract pins the
# Literal and the constants agree (``test_grade_is_a_closed_two_value_domain``).
MessageGrade = Literal["signal", "directive"]
MESSAGE_GRADE_SIGNAL = _MESSAGE_GRADE_SIGNAL
MESSAGE_GRADE_DIRECTIVE = _MESSAGE_GRADE_DIRECTIVE
MESSAGE_GRADES: frozenset[str] = frozenset({MESSAGE_GRADE_SIGNAL, MESSAGE_GRADE_DIRECTIVE})

# The FOUR conditions the raw guarded ``UPDATE`` (the ack CAS) collapses into one
# byte-identical empty return (ruling 4 / store reference §4). ``ack`` (03a-2)
# resolves the fourth with the shared retry driver and disambiguates the other
# three; the vocabulary carries them separately so no build can silently accept a
# forged edge id as an idempotent re-ack.
AckOutcome = Literal["acked", "already_acked", "unknown_message", "not_addressed"]

# ``set_status`` marks a send as the question whose thread the derived waiting
# state reads (ruling 9); ONLY this value asks a question — any other status is an
# ordinary touch, so ``question`` is keyed on the VALUE, never on presence.
_STATUS_INPUT_REQUIRED = "input_required"

# The signin credential keys the SDK expects, and the record-id table separator.
_SIGNIN_USER_KEY = "username"
_SIGNIN_PASS_KEY = "password"
_TABLE_SEPARATOR = ":"
_ID_KEY = "id"


# --- value objects (pydantic, extra="forbid" on the wire) --------------------


class Message(BaseModel):
    """A single sent message node in the durable message graph.

    Attributes:
        id: The message's BARE opaque id — never a table-prefixed ``RecordID``.
        question: ``True`` when this message ASKS (``set_status='input_required'``
            at send). ORTHOGONAL to ``grade`` — a signal can ask, a directive need
            not. The derived waiting state reads THIS, never ``grade`` (ruling 9).
        seq: The native-sequence ORDERING key. GAPS ARE REAL (an aborted
            transaction burns a number, store reference §5) — never a count.
        session: The session this message was sent in.
        thread: The conversation thread — defaults to ``session`` at send.
        sender_id: The sending agent's opaque row id.
        sender_name: The sending agent's display name.
        grade: One of :data:`MESSAGE_GRADES`.
        body: The RAW message body — never sanitised in storage (sanitisation is
            a render concern, packet 03b); stored stripped of surrounding
            whitespace.
        refs: The message's pointer list (reports/findings it references).
        task_id: The task this message concerns, or ``None``.
        created_at: The tz-aware UTC timestamp this message was sent
            (ledger-stamped, the ``agent``/``task`` idiom).
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    question: bool
    seq: int
    session: str
    thread: str
    sender_id: str
    sender_name: str
    grade: MessageGrade
    body: str
    refs: list[str]
    task_id: str | None = None
    created_at: datetime


class MessageSendResult(BaseModel):
    """The outcome of a :meth:`MessageLedger.send` call.

    Attributes:
        message: The freshly-sent message node.
        recipient_names: The DEDUPED recipient display names, SORTED — a stable,
            argument-order-independent receipt.
        recipient_count: How many distinct recipients received a delivery edge.
    """

    model_config = ConfigDict(extra="forbid")

    message: Message
    recipient_names: list[str]
    recipient_count: int


class InboxEntry(BaseModel):
    """One drained delivery: a message as its recipient sees it, plus that
    recipient's own per-edge ack state.

    Attributes:
        seq: The message's ordering key.
        message_id: The message's BARE id (round-trips :attr:`Message.id`).
        grade: The message grade.
        sender_name: The sending agent's display name.
        thread: The conversation thread.
        task_id: The task this message concerns, or ``None``.
        body: The RAW message body.
        refs: The message's pointer list.
        created_at: When the message was sent (tz-aware UTC).
        acked_at: When THIS recipient acked it, or ``None`` if unacked.
        ack_note: The note THIS recipient left when acking, or ``None``.
    """

    model_config = ConfigDict(extra="forbid")

    seq: int
    message_id: str
    grade: MessageGrade
    sender_name: str
    thread: str
    task_id: str | None = None
    body: str
    refs: list[str]
    created_at: datetime
    acked_at: datetime | None = None
    ack_note: str | None = None


class MessageDrainResult(BaseModel):
    """The outcome of a :meth:`MessageLedger.drain` call.

    Attributes:
        entries: The DISPLAY-CAPPED window (oldest-first by ``seq``).
        total_pending: The count over the WHOLE pending set, never the window.
        directive_pending: The directive count over the WHOLE pending set.
        stamped_seqs: EXACTLY the seqs the served window stamped seen — empty
            under ``peek``.
        peeked: Whether this drain was a ``peek`` (stamped nothing).
    """

    model_config = ConfigDict(extra="forbid")

    entries: list[InboxEntry]
    total_pending: int
    directive_pending: int
    stamped_seqs: list[int]
    peeked: bool


class MessageAckEntry(BaseModel):
    """One requested seq's ack fate (packet 03a-2).

    Attributes:
        seq: The requested seq.
        outcome: One of :data:`AckOutcome`.
        acked_at: The winning ack's stamp for ``acked``/``already_acked``, else
            ``None``.
    """

    model_config = ConfigDict(extra="forbid")

    seq: int
    outcome: AckOutcome
    acked_at: datetime | None = None


class MessageAckResult(BaseModel):
    """The outcome of a :meth:`MessageLedger.ack` call (packet 03a-2).

    Attributes:
        entries: Every requested seq's fate, in request order.
        acked_count: How many seqs this call stamped (won the CAS on).
        already_acked_count: How many were already acked (idempotent no-ops).
    """

    model_config = ConfigDict(extra="forbid")

    entries: list[MessageAckEntry]
    acked_count: int
    already_acked_count: int


class WaitingOnAnswer(BaseModel):
    """The derived waiting state of an agent that asked an unanswered question
    (ruling 9 — DERIVED at read time, never stored).

    Attributes:
        thread: The question's thread.
        question_seq: The question message's ordering key.
        asked_at: The question's own ``created_at`` (a render ages it).
    """

    model_config = ConfigDict(extra="forbid")

    thread: str
    question_seq: int
    asked_at: datetime


# --- errors ------------------------------------------------------------------


class MessageLedgerError(RuntimeError):
    """Base class for every error :class:`MessageLedger` raises."""


class MessageBodyError(MessageLedgerError):
    """Raised when a message body is blank or over :data:`MESSAGE_BODY_MAX_CHARS`."""


class UnknownRecipientError(MessageLedgerError):
    """Raised when a recipient id names no registered ``agent`` row."""


class EmptyRecipientSetError(MessageLedgerError):
    """Raised when a send names no recipient — a message with no delivery edge can
    never be read; the ledger never resolves a broadcast roster (the dispatcher
    does)."""


class IllegalMessageGradeError(MessageLedgerError):
    """Raised when a send's ``grade`` is outside :data:`MESSAGE_GRADES`."""


class MessageLedger:
    """Durable store-and-forward message ledger over a single SurrealDB database.

    Owns BOTH the ``message`` node table and the ``to`` delivery edge (plus the
    ``message_seq`` native sequence backing ``message.seq``). Composes the mint +
    ``CREATE`` + N×``RELATE`` fan-out into ONE atomic transaction, validates every
    recipient before any edge is written, and rides the shared
    :mod:`loremaster.store._txn` error-classification/retry seam so every failure
    surfaces as a typed store error.

    Args:
        url: The SurrealDB RPC URL (e.g. ``ws://127.0.0.1:18000/rpc``).
        namespace: The namespace the database lives under.
        database: The per-project database name.
        user: The root/username to sign in with.
        password: The password to sign in with.
    """

    def __init__(
        self,
        *,
        url: str,
        namespace: str,
        database: str,
        user: str,
        password: str,
    ) -> None:
        """Store the ledger's wiring. Does not open any connection yet."""
        self._url = url
        self._namespace = namespace
        self._database = database
        self._user = user
        self._password = password
        self._connection: _SurrealConnection | None = None
        self._connect_lock = asyncio.Lock()

    # -- connection lifecycle ----------------------------------------------

    async def _ensure_connection(self) -> _SurrealConnection:
        """Return the live connection, opening + signing in on first use.

        The session bootstrap is :func:`~loremaster.store._txn.bootstrap_session`
        — the ONE shared implementation every connection owner in the package
        calls. Any bootstrap failure — a transport/auth fault OR exhausted
        contention alike — is wrapped as :class:`SurrealConnectionError` after
        closing the half-open socket (mirrors :class:`~loremaster.briefs.BriefLedger`).

        Raises:
            SurrealConnectionError: The server is unreachable, rejected auth, or
                the session bootstrap exhausted its retry budget.
        """
        if self._connection is not None:
            return self._connection
        async with self._connect_lock:
            if self._connection is not None:
                return self._connection  # type: ignore[unreachable]
            connection = AsyncSurreal(self._url)
            credentials: dict[str, Any] = {
                _SIGNIN_USER_KEY: self._user,
                _SIGNIN_PASS_KEY: self._password,
            }
            try:
                await connection.signin(credentials)
                await bootstrap_session(connection, self._namespace, self._database, url=self._url)
            except TxnContentionExhaustedError as error:
                await self._safe_close(connection)
                raise SurrealConnectionError(
                    f"could not connect to SurrealDB at {self._url!r} "
                    f"(namespace={self._namespace!r}, database={self._database!r}): "
                    f"the session bootstrap exhausted its retry budget"
                ) from error
            except _CONNECTION_ERRORS as error:
                await self._safe_close(connection)
                raise SurrealConnectionError(
                    f"could not connect to SurrealDB at {self._url!r} "
                    f"(namespace={self._namespace!r}, database={self._database!r}): {error}"
                ) from error
            self._connection = connection
            logger.debug(
                "message.connected",
                extra={"namespace": self._namespace, "database": self._database},
            )
            return connection

    async def ensure_ready(self) -> None:
        """Connect and apply the message + to + message_seq schema slice — idempotent.

        Applies :func:`~loremaster.store.surreal_schema.generate_message_ddl`
        inside ONE ``BEGIN … COMMIT`` via
        :func:`~loremaster.store._txn.execute_transaction`. The ``message`` node
        table and the ``message_seq`` sequence are ``IF NOT EXISTS`` (safe
        re-apply — a BARE ``DEFINE SEQUENCE`` would CRASH on the re-apply every
        boot performs, store reference §1.1); the ``to`` relation table is
        ``OVERWRITE`` (the only clause that re-lands a changed ``IN``/``OUT``/
        ``ENFORCED`` — ``IF NOT EXISTS`` is a silent no-op on it). Neither variant
        rewinds the sequence counter, so re-applying never re-issues a number.

        Raises:
            SurrealConnectionError: The server is unreachable or the socket died.
            SurrealStoreError: A DDL statement was rejected by the engine.
        """
        await self._ensure_connection()
        ddl = generate_message_ddl()
        await execute_transaction(
            f"BEGIN;\n{ddl}COMMIT;\n",
            {},
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )
        logger.debug("message.schema.ready", extra={"database": self._database})

    async def close(self) -> None:
        """Close the live connection (if any); tolerant of a never-connected ledger."""
        if self._connection is not None:
            await self._safe_close(self._connection)
            self._connection = None

    async def _drop_connection(self, connection: _SurrealConnection) -> None:
        """Drop the cached handle so the NEXT call reconnects (the self-heal)."""
        if self._connection is connection:
            self._connection = None
        await self._safe_close(connection)

    @staticmethod
    async def _safe_close(connection: _SurrealConnection) -> None:
        """Close ``connection``, swallowing an already-dead-socket failure."""
        try:
            await connection.close()
        except _CONNECTION_ERRORS:
            logger.debug("message.close.already_closed")

    async def _query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        """Run a single statement on the (lazily opened) connection, self-healing.

        Delegates to :func:`~loremaster.store._txn.run_query` — the ONE shared
        single-statement attempt body every seam in the package rides (classify /
        self-heal / log, including its retryable-conflict path). Spelled EXACTLY
        ``async def _query`` because ``test_retry_seam.py``'s enumerator is
        name-keyed: a differently-spelled seam silently drops ~19 retry/marker/
        mutation pins (the ``scout.py`` instrument-defeat).
        """
        return await run_query(
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
            noun="message query",
            label="message.query.rejected",
            statement=statement,
            params=params or {},
            logger=logger,
        )

    async def _apply(self, fragments: list[TxnFragment]) -> None:
        """Compose ``fragments`` into ONE transaction and run it atomically.

        Mirrors :meth:`~loremaster.briefs.BriefLedger._apply`.
        """
        statement_text, merged_params = compose(*fragments)
        await execute_transaction(
            statement_text,
            merged_params,
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )

    # -- send ---------------------------------------------------------------

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
        """Send ONE message to every recipient, atomically and all-or-nothing.

        The write is ONE ``execute_transaction`` composing the native-sequence
        mint (``sequence::nextval``), the ``message`` ``CREATE``, and one
        ``RELATE $message->to->$recipient`` per recipient (store reference §5 —
        the composition is measured conflict-free, so the fan-out does not
        contend on the mint). EVERY recipient is validated to exist in the
        ``agent`` table BEFORE any edge is written, and recipients are deduped by
        row IDENTITY before the loop (``UNIQUE(in, out)`` makes a repeated
        recipient a LOUD engine error, never a silent de-duplication). A rejected
        send leaves NO message row and NO delivery edge.

        Args:
            sender: The sending agent's externally-resolved identity (id + name).
            session: The session to send in.
            body: The RAW message body — blank is rejected, over-cap is REJECTED
                (never truncated), hostile content is stored verbatim (render-side
                sanitisation is packet 03b's concern).
            grade: One of :data:`MESSAGE_GRADES`; out-of-domain is rejected.
            recipients: The externally-resolved recipient identities; an empty set
                is a teaching error, never a broadcast (the dispatcher resolves
                rosters).
            thread: The conversation thread — defaults to ``session``.
            task_id: The task this message concerns, or ``None``.
            refs: The message's pointer list, or ``None`` (⇒ ``[]``).
            set_status: When ``'input_required'``, marks this message as the
                question whose thread the derived waiting state reads (ruling 9);
                any other value is an ordinary status touch (not a question).

        Returns:
            The :class:`MessageSendResult` of this call.

        Raises:
            IllegalMessageGradeError: ``grade`` is outside :data:`MESSAGE_GRADES`.
            MessageBodyError: ``body`` is blank or over the length cap.
            EmptyRecipientSetError: ``recipients`` is empty.
            UnknownRecipientError: A recipient id names no registered agent.
            SurrealConnectionError: A transport fault.
            SurrealStoreError: The engine rejected the write.
        """
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
                f"a send needs at least one recipient — the ledger never resolves a roster "
                f"(broadcast is the dispatcher's concern), so an empty recipient set in "
                f"session {session!r} is a caller error, not a broadcast"
            )
        await self._reject_unknown_recipients(recipients)
        deduped = self._dedupe_by_identity(recipients)
        created_at = datetime.now(UTC)
        # A BARE, client-minted ULID (26-char Crockford, colon-free) — time-sortable
        # for a future ``since=`` cursor (pkt-05); the contract pins bareness only,
        # ordering rides ``seq``. Client-side (before the fan-out) so it binds
        # directly as the RELATE ``in`` endpoint without capturing an engine-minted
        # id back out of the transaction.
        message_id = str(ULID())
        fragment = self._send_fragment(
            message_id=message_id,
            session=session,
            thread=thread if thread is not None else session,
            sender=sender,
            grade=grade,
            body=trimmed,
            refs=list(refs) if refs is not None else [],
            task_id=task_id,
            question=set_status == _STATUS_INPUT_REQUIRED,
            created_at=created_at,
            recipients=deduped,
        )
        await self._apply([fragment])
        seq = await self._read_back_seq(message_id)
        message = Message(
            id=message_id,
            question=set_status == _STATUS_INPUT_REQUIRED,
            seq=seq,
            session=session,
            thread=thread if thread is not None else session,
            sender_id=sender.id,
            sender_name=sender.name,
            grade=cast(MessageGrade, grade),
            body=trimmed,
            refs=list(refs) if refs is not None else [],
            task_id=task_id,
            created_at=created_at,
        )
        return MessageSendResult(
            message=message,
            recipient_names=sorted(ref.name for ref in deduped),
            recipient_count=len(deduped),
        )

    async def _reject_unknown_recipients(self, recipients: Sequence[AgentRefLike]) -> None:
        """Raise :class:`UnknownRecipientError` naming EVERY recipient id that is
        not a registered ``agent`` row (store reference §4 / finding #105 — the
        engine validates NEITHER RELATE endpoint, so this app-level check is the
        ONLY guard against a permanent, silent delivery receipt for a ghost).

        ONE query regardless of recipient count: a direct-record-access
        ``SELECT id FROM $ids`` returns only the ids that EXIST (a non-existent
        RecordID is silently dropped, [PROBED 2026-07-23 on spike-surreal 3.2.1]),
        so the missing ids are exactly ``requested − returned``.
        """
        distinct_ids = list(dict.fromkeys(ref.id for ref in recipients))
        rows = self._as_rows(
            await self._query(
                "SELECT id FROM $recipient_ids",
                {"recipient_ids": [RecordID(AGENT_TABLE, agent_id) for agent_id in distinct_ids]},
            )
        )
        existing_ids = {self._bare_id(row[_ID_KEY]) for row in rows if _ID_KEY in row}
        unknown = sorted({ref.name for ref in recipients if ref.id not in existing_ids})
        if unknown:
            raise UnknownRecipientError(
                f"unknown recipient(s): {', '.join(unknown)} — every recipient must be a "
                f"registered agent before it can be sent to"
            )

    @staticmethod
    def _dedupe_by_identity(recipients: Sequence[AgentRefLike]) -> list[AgentRefLike]:
        """Return ``recipients`` with duplicate ROW IDS collapsed, first-wins.

        Keyed on ``id`` (the row identity), never on ``name`` — two different
        agents may legitimately share a display name across sessions, so a
        name-keyed dedupe silently drops a real recipient. ``UNIQUE(in, out)`` is
        the correctness BACKSTOP behind this, never the de-duplicator to lean on
        silently (store reference §4).
        """
        deduped: list[AgentRefLike] = []
        seen_ids: set[str] = set()
        for ref in recipients:
            if ref.id in seen_ids:
                continue
            seen_ids.add(ref.id)
            deduped.append(ref)
        return deduped

    @staticmethod
    def _send_fragment(
        *,
        message_id: str,
        session: str,
        thread: str,
        sender: AgentRefLike,
        grade: str,
        body: str,
        refs: list[str],
        task_id: str | None,
        question: bool,
        created_at: datetime,
        recipients: Sequence[AgentRefLike],
    ) -> TxnFragment:
        """The mint + CREATE + N×RELATE fragment for one atomic send.

        ``$minted_seq`` is a transaction-scoped ``LET`` binding (the native
        sequence value), not a bound param — every other ``$name`` is a bound
        param. The ``message`` id is minted in Python (a bare ULID) so it can be
        bound as the RELATE ``in`` endpoint directly (store reference §7 — a
        RELATE endpoint is a bound ``RecordID``, never a ``type::record()`` call).
        """
        # ⚠ ``session`` is a PROTECTED variable name (store reference §2): a
        # top-level bound param named ``session`` is rejected outright ("'session'
        # is a protected variable and cannot be set", [PROBED 2026-07-23 on
        # spike-surreal 3.2.1]). The COLUMN ``session`` is fine — only the PARAM
        # name is protected — so it is bound as ``$msg_session``.
        params: dict[str, Any] = {
            "msg_id": message_id,
            "msg_rec": RecordID(MESSAGE_TABLE, message_id),
            "msg_session": session,
            "thread": thread,
            "sender_rec": RecordID(AGENT_TABLE, sender.id),
            "grade": grade,
            "body": body,
            "refs": refs,
            "task_id": task_id,
            "question": question,
            "created_at": created_at,
        }
        statements: list[str] = [
            f'LET $minted_seq = sequence::nextval("{MESSAGE_SEQUENCE_NAME}")',
            f"CREATE type::record('{MESSAGE_TABLE}', $msg_id) CONTENT "
            "{ seq: $minted_seq, session: $msg_session, thread: $thread, sender: $sender_rec, "
            "grade: $grade, body: $body, refs: $refs, task_id: $task_id, "
            "question: $question, created_at: $created_at }",
        ]
        for index, ref in enumerate(recipients):
            endpoint_param = f"recipient_{index}"
            params[endpoint_param] = RecordID(AGENT_TABLE, ref.id)
            statements.append(
                f"RELATE $msg_rec->{TO_RELATION}->${endpoint_param} SET "
                f"session = $msg_session, created_at = $created_at"
            )
        return TxnFragment(statements=statements, params=params)

    async def _read_back_seq(self, message_id: str) -> int:
        """Read the native-sequence ``seq`` the atomic send minted for ``message_id``.

        ``execute_transaction`` verifies every statement but returns nothing, and
        ``seq`` is engine-minted inside it — so it is read back by the row's OWN
        (Python-known) id, never by a scan that a concurrent send could race.
        """
        rows = self._as_rows(
            await self._query(
                f"SELECT seq FROM type::record('{MESSAGE_TABLE}', $mid)",
                {"mid": message_id},
            )
        )
        if not rows or "seq" not in rows[0]:
            raise MessageLedgerError(
                f"message {message_id!r} vanished immediately after it was created"
            )
        return int(rows[0]["seq"])

    # -- drain --------------------------------------------------------------

    async def drain(self, *, agent_id: str, limit: int, peek: bool = False) -> MessageDrainResult:
        """Serve this agent's unread inbox window and (unless ``peek``) stamp
        EXACTLY the rows served as seen.

        Pending = every message carrying an UNSTAMPED (``seen_at IS NONE``) ``to``
        edge to ``agent_id``. The window is the oldest ``limit`` by ``seq``;
        ``total_pending``/``directive_pending`` are computed over the WHOLE pending
        set, never the capped window (a display cap bounds rows rendered, never the
        numbers beside them). A non-``peek`` drain stamps ONLY the served window,
        so an elided remainder stays unread — no cursor arithmetic.

        Args:
            agent_id: The draining agent's opaque row id.
            limit: The display cap on served rows.
            peek: When ``True``, serve the same rows but stamp NOTHING.

        Returns:
            The :class:`MessageDrainResult` of this call.
        """
        agent_rec = RecordID(AGENT_TABLE, agent_id)
        rows = self._as_rows(
            await self._query(
                f"SELECT in.{_ID_KEY} AS message_id, in.seq AS seq, in.grade AS grade, "
                f"in.sender.name AS sender_name, in.thread AS thread, in.task_id AS task_id, "
                f"in.body AS body, in.refs AS refs, in.created_at AS created_at, "
                f"acked_at, ack_note "
                f"FROM {TO_RELATION} WHERE out = $agent AND seen_at IS NONE",
                {"agent": agent_rec},
            )
        )
        # The real store guarantees no incidental ordering and the adversarial fake
        # deliberately supplies rows seq-decorrelated, so the order is pinned here.
        pending = sorted(rows, key=lambda row: int(row["seq"]))
        total_pending = len(pending)
        directive_pending = sum(1 for row in pending if row.get("grade") == MESSAGE_GRADE_DIRECTIVE)
        window = pending[:limit]
        entries = [self._row_to_inbox_entry(row) for row in window]
        stamped_seqs: list[int] = []
        if not peek and window:
            window_records = [
                RecordID(MESSAGE_TABLE, self._bare_id(row["message_id"])) for row in window
            ]
            await self._query(
                f"UPDATE {TO_RELATION} SET seen_at = $seen_at "
                f"WHERE out = $agent AND in IN $message_ids AND seen_at IS NONE",
                {
                    "seen_at": datetime.now(UTC),
                    "agent": agent_rec,
                    "message_ids": window_records,
                },
            )
            stamped_seqs = [int(row["seq"]) for row in window]
        return MessageDrainResult(
            entries=entries,
            total_pending=total_pending,
            directive_pending=directive_pending,
            stamped_seqs=stamped_seqs,
            peeked=peek,
        )

    def _row_to_inbox_entry(self, row: dict[str, Any]) -> InboxEntry:
        """Map a raw drain row into a FRESH :class:`InboxEntry` value object."""
        return InboxEntry(
            seq=int(row["seq"]),
            message_id=self._bare_id(row.get("message_id")),
            grade=cast(MessageGrade, row.get("grade")),
            sender_name=str(row.get("sender_name") or ""),
            thread=str(row.get("thread") or ""),
            task_id=row.get("task_id"),
            body=str(row.get("body") or ""),
            refs=list(row.get("refs") or []),
            created_at=self._require_aware_utc(row.get("created_at")),
            acked_at=self._to_aware_utc(row.get("acked_at")),
            ack_note=row.get("ack_note"),
        )

    # -- ack / awaiting_answer (packet 03a-2 — the CONSUME path) ------------

    async def ack(
        self, *, agent_id: str, seqs: Sequence[int], note: str | None = None
    ) -> MessageAckResult:
        """Write-once CAS ack of one or more delivery edges (packet 03a-2).

        Not implemented in 03a-1 (the SEND path): the write-once CAS, its
        four-way-ambiguous return disambiguation, and the 16-way ack concurrency
        proof are packet 03a-2's target. The signature and return type exist here
        so the module's full public surface is present.
        """
        raise NotImplementedError(
            "MessageLedger.ack is packet 03a-2 (the CONSUME path); not implemented in 03a-1"
        )

    async def awaiting_answer(self, *, agent_id: str) -> WaitingOnAnswer | None:
        """The DERIVED waiting state — the oldest unanswered question this agent
        asked (packet 03a-2, ruling 9).

        Not implemented in 03a-1 (the SEND path): the read-time derivation is
        packet 03a-2's target. The signature and return type exist here so the
        module's full public surface is present.
        """
        raise NotImplementedError(
            "MessageLedger.awaiting_answer is packet 03a-2 (the derived waiting state); "
            "not implemented in 03a-1"
        )

    # -- result narrowing / mapping ----------------------------------------

    @staticmethod
    def _as_rows(result: Any) -> list[dict[str, Any]]:
        """Narrow a ``SELECT`` result to its list of dict rows."""
        if not isinstance(result, list):
            return []
        return [row for row in result if isinstance(row, dict)]

    def _require_aware_utc(self, value: Any) -> datetime:
        """Normalise a REQUIRED datetime column to tz-aware UTC, refusing a bad value.

        Raises:
            SurrealStoreError: The value is missing or is not a datetime.
        """
        coerced = self._to_aware_utc(value)
        if coerced is None:
            raise SurrealStoreError(
                f"message row datetime column is missing or not a datetime "
                f"(got {type(value).__name__})"
            )
        return coerced

    @staticmethod
    def _to_aware_utc(value: Any) -> datetime | None:
        """Coerce a stored datetime into a tz-aware UTC datetime (or ``None``)."""
        if value is None:
            return None
        if isinstance(value, datetime):
            aware = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
            return aware.astimezone(UTC)
        text = str(value).replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        aware = parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
        return aware.astimezone(UTC)

    @staticmethod
    def _bare_id(raw: Any) -> str:
        """Return the BARE id — no table prefix — from a ``RecordID`` or string."""
        if isinstance(raw, RecordID):
            return str(raw.id)
        text = str(raw)
        if _TABLE_SEPARATOR in text:
            return text.split(_TABLE_SEPARATOR, 1)[1]
        return text
