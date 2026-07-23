"""PACKET 03 (the durable core — TEST-ONLY, no deploy).

Contract tests for ``loremaster.messages`` — the durable MESSAGE GRAPH
(packet 03: a ``message`` node plus a ``to`` delivery edge carrying per-recipient
state), against the REAL SurrealDB server and against an ADVERSARIAL in-memory
fake (``_comms_fakes.py``).

Binding sources — CITED, never re-transcribed:

* ``docs/plans/v2/03-comms-message-graph.md`` — Scope IN and the SEVEN binding
  kickoff rulings (broadcast = ALL NON-RETIRED; #105's structural guard stays
  in packet 04 while packet 03 owns its own scoped teaching error; the store
  facts; the four-way-ambiguous CAS return; renders live in ``server.py``;
  ``since=`` is packet 05's; a broadcast never delivers to its own sender).
* ``docs/reference/surrealdb-31-capabilities.md`` §1.1 (the SEQUENCE row of the
  DDL decision rule), §2 (CONTENT writes, silent-``None`` projections), §3
  (``execute_transaction``, never ``query()``), §4 (bound-``RecordID`` RELATE,
  the dangling-edge hazard on BOTH endpoints, UNIQUE-on-edge), §5 (the ONE
  retry driver, ``sequence::nextval``, gaps are REAL), §7 (the two RELATE
  syntax gotchas).
* ``REPORT-probe-pkt03-store.md`` §"CONSEQUENCES FOR THE BUILD" — the 14 items
  the engine FORCES or FORBIDS, each measured live on 3.1.5.
* ``docs/plans/v2/receipts/2026-07-19-packet03/REPORT-adversary-pkt03.md``
  §W1–W11 — the wrong-build enumeration the ``KILLS the adversary's W<n>``
  docstrings below name. W1–W5 and W8–W10 are the builds that SURVIVED the
  contract (each pinned below); W6, W7 and W11 are the report's own CONTROLS —
  already correctly killed, so no pin here is owed for them.
* ``~/.claude/plans/one-of-claude-codes-nifty-garden.md`` §"Data model" /
  §"Tool surface" — the approved field set and the send/drain/ack semantics.

THE PINNED CONTRACT — the public surface THIS FILE decides. ``loremaster.messages``
does not exist yet, so these names ARE the contract a later builder must match:

    _msg().MessageGrade = Literal["signal", "directive"]
    _msg().AckOutcome   = Literal["acked", "already_acked", "unknown_message", "not_addressed"]

    Message:                                  # pydantic, extra="forbid"
        id: str                               # bare ulid (no table prefix)
        question: bool                        # ruling 9 — this message ASKS; the
                                              # waiting state is DERIVED from it.
                                              # ORTHOGONAL to ``grade``: a signal can
                                              # ask, a directive can be no question.
        seq: int                              # native-sequence ORDERING key; GAPS ARE REAL
        session: str
        thread: str                           # defaults to ``session``
        sender_id: str
        sender_name: str
        grade: _msg().MessageGrade
        body: str                             # RAW, never sanitised in storage
        refs: list[str]
        task_id: str | None
        created_at: datetime                  # tz-aware UTC

    MessageSendResult:
        message: Message
        recipient_names: list[str]            # sorted, DEDUPED
        recipient_count: int

    InboxEntry:
        seq, message_id, grade, sender_name, thread, task_id, body, refs,
        created_at, acked_at: datetime | None, ack_note: str | None

    MessageDrainResult:
        entries: list[InboxEntry]             # the DISPLAY-CAPPED window
        total_pending: int                    # over the WHOLE set, never the window
        directive_pending: int                # ditto
        stamped_seqs: list[int]               # EXACTLY what the window carried
        peeked: bool

    MessageAckEntry:  seq: int, outcome: _msg().AckOutcome, acked_at: datetime | None
    MessageAckResult: entries, acked_count, already_acked_count

    _msg().WaitingOnAnswer:  thread: str, question_seq: int, asked_at: datetime

    AgentRefLike(Protocol): id: str; name: str
        ⚠ IMPORTED, never redefined — ONE shared home that BOTH ``briefs.py``
        and ``messages.py`` import (operator-ruled 2026-07-19, DRY law).

    MessageLedger(*, url, namespace, database, user, password):
        async ensure_ready() -> None
        async close() -> None
        async send(*, sender, session, body, grade, recipients,
                   thread=None, task_id=None, refs=None,
                   set_status=None) -> MessageSendResult
        async awaiting_answer(*, agent_id) -> _msg().WaitingOnAnswer | None
        async drain(*, agent_id, limit, peek=False) -> MessageDrainResult
        async ack(*, agent_id, seqs, note=None) -> MessageAckResult

    Exceptions: _msg().MessageLedgerError(RuntimeError);
                _msg().MessageBodyError, _msg().UnknownRecipientError, _msg().EmptyRecipientSetError,
                _msg().IllegalMessageGradeError  (all _msg().MessageLedgerError subclasses).

    Module constants: _msg().MESSAGE_GRADE_SIGNAL, _msg().MESSAGE_GRADE_DIRECTIVE,
                      _msg().MESSAGE_GRADES, _msg().MESSAGE_BODY_MAX_CHARS.

DELIBERATE DECOUPLING, inherited from ``BriefLedger`` (``briefs.py:79-89``):
this ledger NEVER imports ``loremaster.agents``. ``send`` accepts an
externally-resolved sender/recipient identity (anything with ``id``/``name``);
the DISPATCHER resolves the roster, which is where ruling 1's broadcast
semantics and ruling 7's exclude-the-sender rule are pinned
(``test_comms_tool.py``). What the ledger still owns — and what probe 1 makes
non-negotiable — is that EVERY supplied recipient id must EXIST in the
``agent`` table before a single ``RELATE`` runs: the engine validates NEITHER
endpoint, so a bogus ``out`` writes a permanent, silent delivery receipt for an
agent who does not exist, and ``->to->agent`` traversal reports the ghost as a
first-class recipient. That check is a raw SELECT over ``agent`` by id — it is
not an import of the registry module, so the decoupling holds.

Expected until the module lands: collection ERROR in THIS FILE —
``ModuleNotFoundError: No module named 'loremaster.messages'``.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast, get_args

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
from loremaster.store.surreal_schema import AGENT_TABLE, generate_agent_ddl
from render_injection_scaffold import _ROW_FORGE_PAYLOAD
from surrealdb import RecordID

# --------------------------------------------------------------------------- #
# LAZY access to everything packet 03 has yet to build.
#
# ⚠ CALL-TIME IMPORTS ON PURPOSE. A MODULE-LEVEL ``from loremaster.messages
# import ...`` makes this file UNCOLLECTABLE at clean HEAD rather than RED — and
# those are different states. A red test RUNS and fails for its own reason; an
# uncollectable module never loads, contributes ``no tests collected`` to the
# tail (the shape repo law names as the one that reads green behind a pipe), and
# — when the import sits in a SHARED module — takes unrelated suites down with
# it. This contract shipped that defect once via ``_comms_fakes.py``: six suites
# uncollectable, ~1,220 tests silently uncounted.
#
# Every pin below therefore fails on ITS OWN assertion path, naming the symbol
# it needs, instead of deleting the file from the run.
#
# (PLC0415 import-outside-top-level is an ignored house idiom in this repo.)
# --------------------------------------------------------------------------- #


def _msg() -> Any:
    """The module under contract, imported at CALL time. See above."""
    import loremaster.messages

    return loremaster.messages


def _msg_fakes() -> Any:
    """The message fake, imported at CALL time. See above."""
    import _message_fakes

    return _message_fakes


def _schema() -> Any:
    """``surreal_schema``'s packet-03 additions, read at CALL time."""
    import loremaster.store.surreal_schema

    return loremaster.store.surreal_schema


# --- identities (the design's own worked examples) --------------------------
SESSION_WAVE7 = "wave7"
SESSION_WAVE9 = "wave9"  # the CROSS-SESSION control — never a recipient of wave7 traffic

SENDER_LEAD = ("lead-id-0000", "lead")
AGENT_FIXER_B = ("fixer-b-id-01", "fixer-b")
AGENT_AUDIT_C = ("audit-c-id-02", "audit-c")
AGENT_SCOUT_D = ("scout-d-id-03", "scout-d")

BODY_SIGNAL = "wave 3 landed green; receipts in REPORT-fixer-b.md"
BODY_DIRECTIVE = "STOP and re-run the gate before committing — see finding #142"

_TIMESTAMP_TOLERANCE = timedelta(seconds=10)

# ≥8-way, per DESIGN-LAW §5 ("pin hot-row mints at ≥8-way, never 2-way") and
# the repo's existing live-race precedents (test_findings.py:148,
# test_brief_ledger.py:142). SEPARATE ledger instances on SEPARATE live
# connections — N coroutines on ONE socket do not contend the way N
# connections do (REPORT-recon-pkt03 §F.4).
_CONCURRENT_SENDERS = 8
_CONCURRENT_SENDERS_AT_SCALE = (16,)
_CONCURRENT_ACKERS = 16


@dataclass(frozen=True)
class _AgentRef:
    """A minimal local stand-in satisfying ``AgentRefLike`` (``id`` + ``name``)
    — deliberately NOT importing ``loremaster.agents.Agent``, so this file stays
    collectible independently of the sibling registry module (the same
    decoupling ``test_brief_ledger.py`` keeps).
    """

    id: str
    name: str


def _ref(pair: tuple[str, str]) -> _AgentRef:
    return _AgentRef(id=pair[0], name=pair[1])


def _assert_recent_utc(stamp: datetime, *, not_before: datetime, not_after: datetime) -> None:
    assert stamp.tzinfo is not None, "timestamp must be timezone-aware (fleet-comparable), not naive"
    assert not_before - _TIMESTAMP_TOLERANCE <= stamp <= not_after + _TIMESTAMP_TOLERANCE


# A factory that builds one more ready ``MessageLedger`` on the SAME database —
# the second (and Nth) live connection the concurrency pins need.
MessageLedgerFactory = Callable[[], Awaitable[Any]]


async def _seed_agents(ledger: Any, refs: list[_AgentRef], *, session: str) -> None:
    """Make every ``ref`` resolvable to the ledger's recipient-existence check.

    Against the REAL backend that means a real row in the ``agent`` table
    (written with ``CONTENT`` — ``session`` is a PROTECTED variable name, store
    reference §2 — via the agent slice's own DDL); against the fake it means an
    entry in its ``agents`` map. Both are "this agent registered", stated in
    each backend's own terms.
    """
    fake = getattr(ledger, "db", None)
    if isinstance(fake, _msg_fakes().FakeMessageDatabase):
        for ref in refs:
            cast(Any, ledger).register_agent(agent_id=ref.id, name=ref.name)
        return
    await cast(Any, ledger)._query(generate_agent_ddl())
    now = datetime.now(UTC)
    for ref in refs:
        await cast(Any, ledger)._query(
            f"UPSERT type::record('{AGENT_TABLE}', $id) CONTENT $content",
            {
                "id": ref.id,
                "content": {
                    "name": ref.name,
                    "session": session,
                    "role": "builder",
                    "status": "active",
                    "registered_at": now,
                    "heartbeat_at": now,
                },
            },
        )


@pytest_asyncio.fixture(params=["real", "fake"])
async def message_ledger_factory(
    request: pytest.FixtureRequest,
) -> AsyncIterator[MessageLedgerFactory]:
    """Clones ``brief_ledger_factory``'s shape (see ``test_task_ledger.py:252-264``
    for the pytest-asyncio 1.4 ``Runner``-reentrancy rationale for NOT depending
    on ``surreal_env``).
    """
    created: list[Any] = []

    if request.param == "real":
        env: SurrealEnv = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        setup_connection = await connect_admin(env)
        await setup_connection.close()

        async def make() -> Any:
            ledger = _msg().MessageLedger(
                url=env.url,
                namespace=env.namespace,
                database=env.database,
                user=env.user,
                password=env.password,
            )
            await ledger.ensure_ready()
            created.append(ledger)
            return ledger
    else:
        shared_db = _msg_fakes().FakeMessageDatabase()

        async def make() -> Any:
            fake_ledger = _msg_fakes().FakeMessageLedger(db=shared_db)
            await fake_ledger.ensure_ready()
            typed_ledger = cast("Any", fake_ledger)
            created.append(typed_ledger)
            return typed_ledger

    try:
        yield make
    finally:
        for ledger in created:
            await ledger.close()
        if request.param == "real":
            await drop_database(env)


@pytest_asyncio.fixture()
async def message_ledger(message_ledger_factory: MessageLedgerFactory) -> Any:
    """One ready ledger on a fresh unique database, with the standard four
    identities already registered (the common per-test case).
    """
    ledger = await message_ledger_factory()
    await _seed_agents(
        ledger,
        [_ref(SENDER_LEAD), _ref(AGENT_FIXER_B), _ref(AGENT_AUDIT_C), _ref(AGENT_SCOUT_D)],
        session=SESSION_WAVE7,
    )
    return ledger


def _is_real(ledger: Any) -> bool:
    return not isinstance(getattr(ledger, "db", None), _msg_fakes().FakeMessageDatabase)


# =========================================================================== #
# Section A — the value objects and the closed vocabularies
# =========================================================================== #


class TestVocabularies:
    def test_grade_is_a_closed_two_value_domain(self) -> None:
        messages = _msg()
        both = {messages.MESSAGE_GRADE_SIGNAL, messages.MESSAGE_GRADE_DIRECTIVE}
        assert set(get_args(messages.MessageGrade)) == both
        assert messages.MESSAGE_GRADES == frozenset(both)

    def test_ack_outcome_names_all_four_conditions_the_raw_cas_collapses(self) -> None:
        """Ruling 4 / probe 4c: the raw guarded ``UPDATE`` returns a byte-identical
        empty list for already-stamped, no-such-edge, not-yours AND
        never-ran-due-to-conflict. The module must resolve the fourth with the
        shared retry driver and DISAMBIGUATE the other three — so the typed
        outcome vocabulary has to carry them separately. A build that returns a
        single ``"nothing happened"`` silently accepts FORGED edge ids.
        """
        assert set(get_args(_msg().AckOutcome)) == {
            "acked",
            "already_acked",
            "unknown_message",
            "not_addressed",
        }

    def test_body_cap_is_the_designs_two_thousand_char_pointer_bound(self) -> None:
        assert _msg().MESSAGE_BODY_MAX_CHARS == 2000

    def test_every_domain_error_is_a_message_ledger_error(self) -> None:
        for error_type in (
            _msg().MessageBodyError,
            _msg().UnknownRecipientError,
            _msg().EmptyRecipientSetError,
            _msg().IllegalMessageGradeError,
        ):
            assert issubclass(error_type, _msg().MessageLedgerError)
        assert issubclass(_msg().MessageLedgerError, RuntimeError)


# =========================================================================== #
# Section B — send: the node + the fan-out
# =========================================================================== #


class TestSendWritesTheNodeAndOneEdgePerRecipient:
    async def test_single_recipient_round_trips_every_field(
        self, message_ledger: Any
    ) -> None:
        before = datetime.now(UTC)
        result = await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=BODY_SIGNAL,
            grade=_msg().MESSAGE_GRADE_SIGNAL,
            recipients=[_ref(AGENT_FIXER_B)],
            task_id="t-1234",
            refs=["REPORT-fixer-b.md"],
        )
        after = datetime.now(UTC)
        assert result.message.session == SESSION_WAVE7
        assert result.message.sender_id == SENDER_LEAD[0]
        assert result.message.sender_name == SENDER_LEAD[1]
        assert result.message.grade == _msg().MESSAGE_GRADE_SIGNAL
        assert result.message.body == BODY_SIGNAL
        assert result.message.refs == ["REPORT-fixer-b.md"]
        assert result.message.task_id == "t-1234"
        assert result.recipient_names == [AGENT_FIXER_B[1]]
        assert result.recipient_count == 1
        _assert_recent_utc(result.message.created_at, not_before=before, not_after=after)

    async def test_the_message_id_is_BARE_with_no_table_prefix(
        self, message_ledger: Any
    ) -> None:
        """M7 — the contract's own docstring says "bare ulid (no table prefix)"
        and nothing executed that claim. A leaked ``message:`` prefix round-trips
        through every equality assertion in this file and only surfaces in
        packet 03a's renders, or in a caller that reconstructs a RecordID.

        KILLS the adversary's W5.
        """
        result = await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=BODY_SIGNAL,
            grade=_msg().MESSAGE_GRADE_SIGNAL,
            recipients=[_ref(AGENT_FIXER_B)],
        )
        assert ":" not in result.message.id, (
            f"message.id carries a table prefix ({result.message.id!r}) — the pinned "
            f"contract is a BARE id, exactly as briefs/agents mint theirs (`_bare_id`)"
        )
        assert result.message.id
        drained = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=20, peek=True)
        assert drained.entries[0].message_id == result.message.id, (
            "InboxEntry.message_id does not round-trip the id send returned"
        )

    async def test_thread_defaults_to_the_session(self, message_ledger: Any) -> None:
        """Design §Data model: ``thread`` (contextId) defaults to ``session``.
        Frontier #20 — a build defaulting to the message id, to ``"default"``, or
        to the task id fails here.
        """
        result = await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=BODY_SIGNAL,
            grade=_msg().MESSAGE_GRADE_SIGNAL,
            recipients=[_ref(AGENT_FIXER_B)],
        )
        assert result.message.thread == SESSION_WAVE7

    async def test_a_send_in_a_DIFFERENT_session_records_that_session(
        self, message_ledger: Any
    ) -> None:
        """Residual 7.5 — every other send in this file writes ``wave7``, so a
        build hardcoding the session (or reading it off the sender's row instead
        of the call) is invisible. This is the monoculture shape that cost the
        repo a blocker before.
        """
        await _seed_agents(
            message_ledger, [_ref(SENDER_LEAD), _ref(AGENT_FIXER_B)], session=SESSION_WAVE9
        )
        result = await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE9,
            body=BODY_SIGNAL,
            grade=_msg().MESSAGE_GRADE_SIGNAL,
            recipients=[_ref(AGENT_FIXER_B)],
        )
        assert result.message.session == SESSION_WAVE9
        assert result.message.thread == SESSION_WAVE9

    async def test_an_explicit_thread_is_kept(self, message_ledger: Any) -> None:
        """PARAMETER MONOCULTURE: the default-session case above cannot tell a
        working default from a build that IGNORES ``thread=`` and always writes
        the session. This leg uses a DIFFERENT value.
        """
        result = await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=BODY_SIGNAL,
            grade=_msg().MESSAGE_GRADE_SIGNAL,
            recipients=[_ref(AGENT_FIXER_B)],
            thread="task:t-1234",
        )
        assert result.message.thread == "task:t-1234"

    async def test_fan_out_reaches_every_recipient_and_only_them(
        self, message_ledger: Any
    ) -> None:
        """Frontier #5: a drain must never return a message not addressed to
        the caller. Needs ≥2 agents to discriminate — with one recipient, "all
        pending" and "my pending" are the same set.
        """
        await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=BODY_SIGNAL,
            grade=_msg().MESSAGE_GRADE_SIGNAL,
            recipients=[_ref(AGENT_FIXER_B), _ref(AGENT_AUDIT_C)],
        )
        for recipient in (AGENT_FIXER_B, AGENT_AUDIT_C):
            drained = await message_ledger.drain(agent_id=recipient[0], limit=20, peek=True)
            assert [entry.body for entry in drained.entries] == [BODY_SIGNAL]
        uninvolved = await message_ledger.drain(agent_id=AGENT_SCOUT_D[0], limit=20, peek=True)
        assert uninvolved.entries == []
        assert uninvolved.total_pending == 0

    async def test_a_sender_never_receives_its_own_message(
        self, message_ledger: Any
    ) -> None:
        """RULING 7 (LEAD-resolved 2026-07-19): a BROADCAST does not deliver to
        its own sender — pinned at the dispatcher, where the roster is resolved.
        Here at the ledger the pin is the half the ledger owns: a send whose
        recipient list does NOT contain the sender leaves the sender's own inbox
        empty (a build that unconditionally self-delivers fails).

        Its complement — an EXPLICIT ``to=[me]`` self-note, which ruling 7
        expressly ALLOWS — is pinned immediately below, so no build can satisfy
        one by breaking the other.
        """
        await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=BODY_SIGNAL,
            grade=_msg().MESSAGE_GRADE_SIGNAL,
            recipients=[_ref(AGENT_FIXER_B)],
        )
        own = await message_ledger.drain(agent_id=SENDER_LEAD[0], limit=20, peek=True)
        assert own.entries == [], "the sender must not receive a copy of its own message"

    async def test_an_EXPLICIT_self_addressed_send_IS_delivered(
        self, message_ledger: Any
    ) -> None:
        """RULING 7's second clause (LEAD-resolved 2026-07-19): ruling 7 covers
        BROADCAST only. A deliberate self-note is legitimate and must arrive.

        DISCRIMINATION: this is the pin that stops a build from "satisfying"
        the no-self-broadcast rule by filtering the sender out of EVERY
        recipient list — which would pass the test above and silently discard a
        legal message.
        """
        result = await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body="note to self: re-run the gate before the commit",
            grade=_msg().MESSAGE_GRADE_SIGNAL,
            recipients=[_ref(SENDER_LEAD)],
        )
        assert result.recipient_names == [SENDER_LEAD[1]]
        own = await message_ledger.drain(agent_id=SENDER_LEAD[0], limit=20, peek=True)
        assert [entry.seq for entry in own.entries] == [result.message.seq]

    async def test_a_repeated_recipient_is_deduped_before_the_relate_loop(
        self, message_ledger: Any
    ) -> None:
        """Frontier #17 / probe 2 / store reference §4: ``UNIQUE(in, out)`` makes
        a duplicate a LOUD engine ERR, so the fan-out must dedupe BEFORE the
        RELATE loop — the index is a correctness backstop, never a de-duplicator
        to lean on silently. The pin: the send SUCCEEDS, reports ONE recipient,
        and the recipient's inbox holds exactly ONE entry.
        """
        result = await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=BODY_SIGNAL,
            grade=_msg().MESSAGE_GRADE_SIGNAL,
            recipients=[_ref(AGENT_FIXER_B), _ref(AGENT_FIXER_B), _ref(AGENT_FIXER_B)],
        )
        assert result.recipient_count == 1
        assert result.recipient_names == [AGENT_FIXER_B[1]]
        drained = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=20, peek=True)
        assert len(drained.entries) == 1

    async def test_dedupe_keys_on_IDENTITY_not_display_name(
        self, message_ledger: Any
    ) -> None:
        """The identity that matters is the ROW ID. Two DIFFERENT agents may
        legitimately share a display name across sessions (``agent.name`` is
        non-unique by design — uniqueness is ``(session, name)`` via the uuid5
        id), so a dedupe keyed on ``name`` silently drops a real recipient.

        Every other fan-out fixture uses distinct ids AND distinct names, so
        none of them can tell the two keys apart. KILLS the adversary's W8.
        """
        twin = _AgentRef(id="fixer-b-id-99", name=AGENT_FIXER_B[1])
        await _seed_agents(message_ledger, [twin], session=SESSION_WAVE9)
        result = await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=BODY_SIGNAL,
            grade=_msg().MESSAGE_GRADE_SIGNAL,
            recipients=[_ref(AGENT_FIXER_B), twin],
        )
        assert result.recipient_count == 2, (
            "two agents sharing a display name were deduped into one — the fan-out keys "
            "on `name` instead of on the row id, so a same-named agent in another "
            "session never receives its traffic"
        )
        for agent_id in (AGENT_FIXER_B[0], twin.id):
            drained = await message_ledger.drain(agent_id=agent_id, limit=20, peek=True)
            assert [entry.seq for entry in drained.entries] == [result.message.seq]

    @pytest.mark.parametrize("recipient_count", [1, 2, 3, 4])
    async def test_EVERY_recipient_actually_RECEIVES_the_message(
        self, message_ledger: Any, recipient_count: int
    ) -> None:
        """M2 / BLOCKER-2 — THE QUANTIFIER LAW, evaluated where the branch can
        actually fire.

        The ∀ property this class names is "every recipient is delivered-an-edge
        or rejected-and-reported, never silently dropped, REGARDLESS of cause".
        It was pinned through ONE door — "recipient not registered" — and every
        fixture that FORCED an edge per recipient carried exactly TWO recipients.
        So a recipient dropped in the EMISSION PLUMBING (supply fine, receipt
        intact, ``recipient_count`` and ``recipient_names`` fully self-consistent)
        engaged nothing: PR93's defect verbatim.

        Parametrised over the COUNT rather than fixed at three, so the property
        is quantified over arity instead of spot-checked at one value where a
        wrong build might happen to be correct.

        KILLS the adversary's W9 (drops the LAST recipient when >2) and W10
        (drops the id-sorted-last when >2).
        """
        recipients = [AGENT_FIXER_B, AGENT_AUDIT_C, AGENT_SCOUT_D, SENDER_LEAD][:recipient_count]
        result = await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=BODY_DIRECTIVE,
            grade=_msg().MESSAGE_GRADE_DIRECTIVE,
            recipients=[_ref(pair) for pair in recipients],
        )
        assert result.recipient_count == recipient_count
        # The receipt is NOT the evidence — the inboxes are. A dropped recipient
        # leaves the receipt perfectly self-consistent, which is exactly why the
        # earlier fixtures could not see it.
        undelivered = []
        for pair in recipients:
            drained = await message_ledger.drain(agent_id=pair[0], limit=20, peek=True)
            if result.message.seq not in [entry.seq for entry in drained.entries]:
                undelivered.append(pair[1])
        assert not undelivered, (
            f"send reported {recipient_count} recipients and its receipt named all of them, "
            f"but {undelivered} received NOTHING — a recipient was silently dropped in the "
            f"fan-out. The receipt agreeing with itself is not delivery."
        )

    @pytest.mark.parametrize("recipient_count", [1, 2, 3, 4])
    async def test_the_receipt_COUNT_equals_the_edges_actually_written(
        self, message_ledger: Any, recipient_count: int
    ) -> None:
        """M2's raw-store half: an independent count straight off the ``to``
        table, so the pin does not depend on ``drain`` being correct either. A
        build with a broken fan-out AND a matching broken drain would satisfy
        the inbox check above; it cannot satisfy this one.
        """
        if not _is_real(message_ledger):
            pytest.skip("raw edge counts are a REAL-backend observation")
        recipients = [AGENT_FIXER_B, AGENT_AUDIT_C, AGENT_SCOUT_D, SENDER_LEAD][:recipient_count]
        result = await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=BODY_SIGNAL,
            grade=_msg().MESSAGE_GRADE_SIGNAL,
            recipients=[_ref(pair) for pair in recipients],
        )
        written = await _edge_row_count(message_ledger)
        assert written == result.recipient_count == recipient_count, (
            f"the receipt claims {result.recipient_count} recipients; the store holds "
            f"{written} delivery edges"
        )

    async def test_recipient_names_are_deterministic_not_argument_order(
        self, message_ledger: Any
    ) -> None:
        """A served list is sorted, so two callers passing the same recipients in
        different orders get the same receipt (and the render is stable).
        """
        forward = await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=BODY_SIGNAL,
            grade=_msg().MESSAGE_GRADE_SIGNAL,
            recipients=[_ref(AGENT_SCOUT_D), _ref(AGENT_AUDIT_C), _ref(AGENT_FIXER_B)],
        )
        assert forward.recipient_names == sorted(
            [AGENT_SCOUT_D[1], AGENT_AUDIT_C[1], AGENT_FIXER_B[1]]
        )


class TestSendValidatesEveryRecipientBeforeWritingAnyEdge:
    """Probe 1 + consequences #1/#2. The engine validates NEITHER ``in`` NOR
    ``out``: a bogus recipient id writes a permanent, silent delivery receipt
    for an agent that does not exist, and ``->to->agent`` lists the ghost as a
    first-class recipient. An application-level existence check is the ONLY
    guard, so it is a PINNED INVARIANT, not a nicety.

    THE QUANTIFIER LAW (PR93): the property pinned is ∀ recipients — EVERY
    recipient is either delivered-an-edge or rejected-and-reported, never
    silently dropped, REGARDLESS of cause — and each fate is FORCED by its own
    fixture below.
    """

    _GHOST = _AgentRef(id="ghost-id-does-not-exist", name="ghost-agent")

    async def test_an_unregistered_recipient_is_rejected_by_name(
        self, message_ledger: Any
    ) -> None:
        with pytest.raises(_msg().UnknownRecipientError) as excinfo:
            await message_ledger.send(
                sender=_ref(SENDER_LEAD),
                session=SESSION_WAVE7,
                body=BODY_SIGNAL,
                grade=_msg().MESSAGE_GRADE_SIGNAL,
                recipients=[self._GHOST],
            )
        assert self._GHOST.name in str(excinfo.value), (
            "the teaching error must NAME the unregistered recipient"
        )

    async def test_a_mixed_batch_is_all_or_nothing(self, message_ledger: Any) -> None:
        """Consequence #2: the hazard is N-1 good edges plus one dangling
        receipt. Probe 3 leg B proves mint+CREATE+N×RELATE composes atomically
        in ONE transaction, so all-or-nothing is achievable — and pinned.

        DISCRIMINATION: a build that validates recipients one at a time inside
        the RELATE loop passes the single-ghost test above and FAILS here,
        because ``fixer-b``'s edge lands before the ghost is reached.
        """
        with pytest.raises(_msg().UnknownRecipientError):
            await message_ledger.send(
                sender=_ref(SENDER_LEAD),
                session=SESSION_WAVE7,
                body=BODY_SIGNAL,
                grade=_msg().MESSAGE_GRADE_SIGNAL,
                recipients=[_ref(AGENT_FIXER_B), self._GHOST, _ref(AGENT_AUDIT_C)],
            )
        for good in (AGENT_FIXER_B, AGENT_AUDIT_C):
            drained = await message_ledger.drain(agent_id=good[0], limit=20, peek=True)
            assert drained.entries == [], (
                f"{good[1]} received a HALF-SENT message: the rejected fan-out left a "
                f"live edge behind, which is exactly the partially-validated shape "
                f"probe 1 proves the engine cannot catch"
            )

    async def test_a_rejected_send_leaves_no_message_row_at_all(
        self, message_ledger: Any
    ) -> None:
        """POSITIVE CONTROL for the pin above: prove the probe can SEE a message
        row (the good send lands and is readable), so "no row after the rejected
        send" is a real observation and not a blind assertion.
        """
        if not _is_real(message_ledger):
            pytest.skip("raw-store row count is a REAL-backend observation")
        good = await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=BODY_SIGNAL,
            grade=_msg().MESSAGE_GRADE_SIGNAL,
            recipients=[_ref(AGENT_FIXER_B)],
        )
        assert await _message_row_count(message_ledger) == 1, "control: the good send IS visible"
        with pytest.raises(_msg().UnknownRecipientError):
            await message_ledger.send(
                sender=_ref(SENDER_LEAD),
                session=SESSION_WAVE7,
                body="a body that must never land",
                grade=_msg().MESSAGE_GRADE_SIGNAL,
                recipients=[_ref(AGENT_AUDIT_C), self._GHOST],
            )
        assert await _message_row_count(message_ledger) == 1, (
            "the rejected send wrote a message row anyway"
        )
        assert await _edge_row_count(message_ledger) == 1
        assert good.recipient_count == 1

    async def test_no_dangling_edge_survives_a_send(self, message_ledger: Any) -> None:
        """The direct form of probe 1's finding: EVERY ``to`` edge's ``out``
        endpoint must resolve to a real ``agent`` row. Reference §4 — the ONLY
        way a reader can see a ghost is to project a field and check for
        ``None`` (the silent-``None``-projection trap, one level deeper).
        """
        if not _is_real(message_ledger):
            pytest.skip("dangling-endpoint detection is a REAL-backend observation")
        await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=BODY_SIGNAL,
            grade=_msg().MESSAGE_GRADE_DIRECTIVE,
            recipients=[_ref(AGENT_FIXER_B), _ref(AGENT_AUDIT_C)],
        )
        rows = await cast(Any, message_ledger)._query(
            f"SELECT out, out.name AS out_name, in.body AS in_body FROM {_schema().TO_RELATION}"
        )
        assert rows, "control: the send wrote edges this probe can see"
        ghosts = [row for row in rows if row.get("out_name") is None or row.get("in_body") is None]
        assert not ghosts, f"dangling edge(s) written — #105 live: {ghosts!r}"


class TestSendValidatesTheBody:
    @pytest.mark.parametrize("blank", ["", "   ", "\n\t "])
    async def test_a_blank_body_is_rejected(
        self, message_ledger: Any, blank: str
    ) -> None:
        with pytest.raises(_msg().MessageBodyError):
            await message_ledger.send(
                sender=_ref(SENDER_LEAD),
                session=SESSION_WAVE7,
                body=blank,
                grade=_msg().MESSAGE_GRADE_SIGNAL,
                recipients=[_ref(AGENT_FIXER_B)],
            )

    async def test_an_oversize_body_is_REJECTED_not_truncated(
        self, message_ledger: Any
    ) -> None:
        """Frontier #19. A build that TRUNCATES to the cap and sends anyway
        passes any "the stored body is ≤ cap" assertion — so the pin is that the
        call RAISES and nothing lands, plus a positive control at the boundary.
        """
        oversize = "x" * (_msg().MESSAGE_BODY_MAX_CHARS + 1)
        with pytest.raises(_msg().MessageBodyError) as excinfo:
            await message_ledger.send(
                sender=_ref(SENDER_LEAD),
                session=SESSION_WAVE7,
                body=oversize,
                grade=_msg().MESSAGE_GRADE_SIGNAL,
                recipients=[_ref(AGENT_FIXER_B)],
            )
        assert "refs" in str(excinfo.value), (
            "the reject is a TEACHING reject: messages carry POINTERS — it must name refs"
        )
        drained = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=20, peek=True)
        assert drained.entries == [], "an oversize body was truncated and DELIVERED"

    async def test_a_body_exactly_at_the_cap_is_accepted(
        self, message_ledger: Any
    ) -> None:
        """The cap-boundary POSITIVE control (0 / cap-1 / cap / cap+1 discipline):
        an off-by-one bound that rejects everything would pass the test above.
        """
        at_cap = "y" * _msg().MESSAGE_BODY_MAX_CHARS
        result = await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=at_cap,
            grade=_msg().MESSAGE_GRADE_SIGNAL,
            recipients=[_ref(AGENT_FIXER_B)],
        )
        assert len(result.message.body) == _msg().MESSAGE_BODY_MAX_CHARS

    async def test_a_hostile_body_is_stored_RAW(self, message_ledger: Any) -> None:
        """Storage is never sanitised — sanitisation is a RENDER concern
        (``sanitise.py``, packet 02's seam). What a recipient acted on must stay
        byte-inspectable. The render-side hostile battery lives in
        ``test_comms_tool.py``; this pins only that the ledger did not
        pre-mangle it.
        """
        hostile = f"line one\nline two {_ROW_FORGE_PAYLOAD}"
        result = await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=hostile,
            grade=_msg().MESSAGE_GRADE_DIRECTIVE,
            recipients=[_ref(AGENT_FIXER_B)],
        )
        assert result.message.body == hostile.strip()
        drained = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=20, peek=True)
        assert drained.entries[0].body == hostile.strip()

    async def test_an_out_of_domain_grade_is_rejected(
        self, message_ledger: Any
    ) -> None:
        with pytest.raises(_msg().IllegalMessageGradeError):
            await message_ledger.send(
                sender=_ref(SENDER_LEAD),
                session=SESSION_WAVE7,
                body=BODY_SIGNAL,
                grade="urgent",
                recipients=[_ref(AGENT_FIXER_B)],
            )

    async def test_an_empty_recipient_set_is_a_teaching_error_not_a_silent_noop(
        self, message_ledger: Any
    ) -> None:
        """A message with no delivery edge is a message that can never be read.
        Silent-anything is the cardinal failure class (DESIGN-LAW §1.4).
        """
        with pytest.raises(_msg().EmptyRecipientSetError):
            await message_ledger.send(
                sender=_ref(SENDER_LEAD),
                session=SESSION_WAVE7,
                body=BODY_SIGNAL,
                grade=_msg().MESSAGE_GRADE_SIGNAL,
                recipients=[],
            )


# =========================================================================== #
# Section C — drain: the display cap is where SILENT LOSS hides
# =========================================================================== #

_DRAIN_CAP = 5
_OVER_CAP = _DRAIN_CAP + 3  # N > cap — the fixture no comms contract had ever written


async def _send_n(
    ledger: Any,
    count: int,
    *,
    recipient: tuple[str, str] = AGENT_FIXER_B,
    grade: str | None = None,
) -> list[int]:
    grade = grade if grade is not None else _msg().MESSAGE_GRADE_SIGNAL
    seqs: list[int] = []
    for index in range(count):
        result = await ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=f"message number {index}",
            grade=grade,
            recipients=[_ref(recipient)],
        )
        seqs.append(result.message.seq)
    return seqs


class TestDrainStampsExactlyWhatItServed:
    """THE defect this section exists to kill (frontier #6): a drain that stamps
    MORE than it served makes the elided messages invisible FOREVER — the exact
    LOSS this whole subsystem exists to remove.

    ⚠ EVERY fixture here is N > cap. A small-N fixture is STRUCTURALLY incapable
    of seeing this defect, and per the repo's own history no comms contract
    fixture had ever exceeded a display cap — which is how three of C1's five
    defects shipped.
    """

    async def test_over_cap_drain_serves_the_cap_and_stamps_only_the_cap(
        self, message_ledger: Any
    ) -> None:
        seqs = await _send_n(message_ledger, _OVER_CAP)
        drained = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=_DRAIN_CAP)
        assert len(drained.entries) == _DRAIN_CAP
        assert drained.stamped_seqs == seqs[:_DRAIN_CAP], (
            "drain must stamp EXACTLY the entries it served — no more, no fewer"
        )

    async def test_the_elided_remainder_is_still_unread_on_the_next_drain(
        self, message_ledger: Any
    ) -> None:
        """The consequence, stated as an outcome property: nothing is lost.
        A build that stamps the whole pending set returns an EMPTY second drain
        and fails here — while passing every count assertion on the first call.
        """
        seqs = await _send_n(message_ledger, _OVER_CAP)
        await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=_DRAIN_CAP)
        second = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=_DRAIN_CAP)
        assert [entry.seq for entry in second.entries] == seqs[_DRAIN_CAP:]
        assert second.total_pending == _OVER_CAP - _DRAIN_CAP

    async def test_counts_are_computed_over_the_WHOLE_set_not_the_capped_window(
        self, message_ledger: Any
    ) -> None:
        """Frontier #8 / DESIGN-LAW §1.2: a served count is computed over the
        WHOLE set its label claims to describe; display caps bound rows
        rendered, never the numbers beside them. A build computing
        ``total_pending = len(entries)`` reads ``5`` here.
        """
        await _send_n(message_ledger, _OVER_CAP)
        drained = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=_DRAIN_CAP, peek=True)
        assert drained.total_pending == _OVER_CAP
        assert len(drained.entries) == _DRAIN_CAP

    async def test_directive_pending_is_also_over_the_whole_set(
        self, message_ledger: Any
    ) -> None:
        """M3 / BLOCKER-3 — ARITHMETIC ALIGNMENT (PR93's third fixture axis).

        ⚠ THIS FIXTURE'S NUMBERS ARE LOAD-BEARING. The first version used 5
        signals + 2 directives at cap 5, which makes:
            directives in the whole set = 2
            elided remainder (7 − 5)     = 2
        — IDENTICAL. A build returning ``total_pending - len(entries)`` read 2
        and passed a test whose own failure message promised it "must count
        DIRECTIVES rather than all messages". The message was the spec the
        author believed; the assertion could not perform it.

        Now: 6 signals + 2 directives at cap 5 ⇒ elided 3 ≠ directives 2, and
        the window (5 signals) holds ZERO directives, so all three candidate
        wrong answers — 2 / 3 / 0 — are distinct.

        KILLS the adversary's W2.
        """
        await _send_n(message_ledger, 6, grade=_msg().MESSAGE_GRADE_SIGNAL)
        await _send_n(message_ledger, 2, grade=_msg().MESSAGE_GRADE_DIRECTIVE)
        drained = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=_DRAIN_CAP, peek=True)
        assert drained.total_pending == 8
        elided = drained.total_pending - len(drained.entries)
        assert elided == 3, "fixture guard: the elided remainder must DIFFER from the directives"
        assert drained.directive_pending == 2, (
            f"directive_pending must count DIRECTIVES over the WHOLE pending set. Got "
            f"{drained.directive_pending}; the elided remainder is {elided} and the served "
            f"window holds {sum(1 for e in drained.entries if e.grade == 'directive')} "
            f"directives — three distinct numbers, so this assertion can now tell them apart"
        )

    async def test_directive_pending_counts_directives_INSIDE_the_window_too(
        self, message_ledger: Any
    ) -> None:
        """M3's complement: the pin above places every directive OUTSIDE the
        served window, so a build counting only the ELIDED directives would
        still read 2. Here the directives are the OLDEST, so they land INSIDE
        the window and an elision-scoped count reads 0.
        """
        await _send_n(message_ledger, 2, grade=_msg().MESSAGE_GRADE_DIRECTIVE)
        await _send_n(message_ledger, 6, grade=_msg().MESSAGE_GRADE_SIGNAL)
        drained = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=_DRAIN_CAP, peek=True)
        assert drained.total_pending == 8
        assert drained.directive_pending == 2, (
            "the served window's own directives were not counted — directive_pending is "
            "scoped to the elided remainder rather than to the whole set"
        )

    async def test_a_limit_of_ONE_serves_and_stamps_exactly_one(
        self, message_ledger: Any
    ) -> None:
        """Residual 7.3 — the 1 end of the boundary discipline. cap and cap+1
        are well covered; limit=1 is the degenerate window where an off-by-one
        (serving 0, or serving 2) is easiest to write and hardest to notice.
        """
        seqs = await _send_n(message_ledger, _OVER_CAP)
        drained = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=1)
        assert [entry.seq for entry in drained.entries] == [seqs[0]]
        assert drained.stamped_seqs == [seqs[0]]
        assert drained.total_pending == _OVER_CAP
        remaining = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=20, peek=True)
        assert remaining.total_pending == _OVER_CAP - 1

    async def test_drain_serves_oldest_first_by_seq(self, message_ledger: Any) -> None:
        """The cap only means "the oldest N" if the order is pinned. The
        adversarial fake deliberately supplies its rows in the WRONG order, so a
        build with no explicit ORDER BY fails here rather than passing on the
        engine's incidental ordering.
        """
        seqs = await _send_n(message_ledger, _OVER_CAP)
        drained = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=_OVER_CAP, peek=True)
        assert [entry.seq for entry in drained.entries] == sorted(seqs)


class TestPeekStampsNothing:
    async def test_peek_serves_the_same_rows_but_stamps_none(
        self, message_ledger: Any
    ) -> None:
        """Frontier #7. Discrimination requires the SECOND read: a build that
        stamps under ``peek`` still returns the right rows on the FIRST call.
        """
        seqs = await _send_n(message_ledger, _OVER_CAP)
        peeked = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=_DRAIN_CAP, peek=True)
        assert [entry.seq for entry in peeked.entries] == sorted(seqs)[:_DRAIN_CAP]
        assert peeked.stamped_seqs == []
        assert peeked.peeked is True
        again = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=_OVER_CAP, peek=True)
        assert again.total_pending == _OVER_CAP, "peek stamped something"

    async def test_a_non_peek_drain_after_a_peek_still_stamps(
        self, message_ledger: Any
    ) -> None:
        """POSITIVE CONTROL: the pin above is worthless unless a NON-peek drain
        demonstrably DOES mutate state through the same code path.
        """
        await _send_n(message_ledger, 2)
        await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=20, peek=True)
        stamped = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=20)
        assert len(stamped.stamped_seqs) == 2
        assert stamped.peeked is False
        after = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=20, peek=True)
        assert after.total_pending == 0


class TestDrainIsScopedToTheCaller:
    async def test_two_recipients_drain_independently(
        self, message_ledger: Any
    ) -> None:
        """Frontier #5, the state half: one agent draining must not stamp the
        other's edges. Needs ≥2 agents on the SAME message to discriminate.
        """
        await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=BODY_DIRECTIVE,
            grade=_msg().MESSAGE_GRADE_DIRECTIVE,
            recipients=[_ref(AGENT_FIXER_B), _ref(AGENT_AUDIT_C)],
        )
        await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=20)
        mine = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=20, peek=True)
        theirs = await message_ledger.drain(agent_id=AGENT_AUDIT_C[0], limit=20, peek=True)
        assert mine.total_pending == 0
        assert theirs.total_pending == 1, (
            "fixer-b's drain stamped audit-c's delivery edge — the CAS is not scoped by owner"
        )

    async def test_a_cross_session_agent_sees_nothing(
        self, message_ledger_factory: MessageLedgerFactory
    ) -> None:
        """Frontier #3: traffic must never leak across SESSIONS. The wave9 agent
        is registered but is not a recipient, so a build that drains by session
        (or by "everything") rather than by the caller's own edges fails.
        """
        ledger = await message_ledger_factory()
        await _seed_agents(
            ledger, [_ref(SENDER_LEAD), _ref(AGENT_FIXER_B)], session=SESSION_WAVE7
        )
        await _seed_agents(ledger, [_ref(AGENT_SCOUT_D)], session=SESSION_WAVE9)
        await ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=BODY_SIGNAL,
            grade=_msg().MESSAGE_GRADE_SIGNAL,
            recipients=[_ref(AGENT_FIXER_B)],
        )
        outsider = await ledger.drain(agent_id=AGENT_SCOUT_D[0], limit=20, peek=True)
        assert outsider.entries == []
        insider = await ledger.drain(agent_id=AGENT_FIXER_B[0], limit=20, peek=True)
        assert len(insider.entries) == 1, "control: the message IS drainable by its recipient"


# =========================================================================== #
# Section D — ack: the write-once CAS and its FOUR-way-ambiguous return
# =========================================================================== #


class TestAckIsWriteOnce:
    async def test_first_ack_stamps_and_reports_acked(
        self, message_ledger: Any
    ) -> None:
        before = datetime.now(UTC)
        [seq] = await _send_n(message_ledger, 1, grade=_msg().MESSAGE_GRADE_DIRECTIVE)
        result = await message_ledger.ack(agent_id=AGENT_FIXER_B[0], seqs=[seq])
        after = datetime.now(UTC)
        assert [entry.outcome for entry in result.entries] == ["acked"]
        assert result.acked_count == 1
        stamp = result.entries[0].acked_at
        assert stamp is not None
        _assert_recent_utc(stamp, not_before=before, not_after=after)

    async def test_a_second_ack_never_overwrites_the_first_stamp(
        self, message_ledger: Any
    ) -> None:
        """Frontier #11. The second stamp must carry a DIFFERENT value or the
        pin cannot distinguish a working guard from a broken one — so this waits
        long enough that ``time::now()`` has demonstrably advanced, then asserts
        the stored stamp is BYTE-IDENTICAL to the first.
        """
        [seq] = await _send_n(message_ledger, 1, grade=_msg().MESSAGE_GRADE_DIRECTIVE)
        first = await message_ledger.ack(agent_id=AGENT_FIXER_B[0], seqs=[seq])
        original = first.entries[0].acked_at
        assert original is not None
        await asyncio.sleep(0.05)
        second = await message_ledger.ack(agent_id=AGENT_FIXER_B[0], seqs=[seq])
        assert [entry.outcome for entry in second.entries] == ["already_acked"]
        assert second.acked_count == 0
        assert second.already_acked_count == 1
        assert second.entries[0].acked_at == original, (
            "the write-once CAS did not hold — the second ack overwrote the first stamp"
        )

    async def test_the_guard_is_what_does_the_work(self, message_ledger: Any) -> None:
        """POSITIVE CONTROL, probe 4 leg C: an UNGUARDED update DOES overwrite.
        Without this, "the value did not change" could be a property of edge
        rows rather than of the ``WHERE ... IS NONE`` guard, and the pin above
        would be passing for the wrong reason.
        """
        if not _is_real(message_ledger):
            pytest.skip("the unguarded-write control is a REAL-backend observation")
        [seq] = await _send_n(message_ledger, 1, grade=_msg().MESSAGE_GRADE_DIRECTIVE)
        await message_ledger.ack(agent_id=AGENT_FIXER_B[0], seqs=[seq])
        sentinel = datetime(2099, 12, 31, tzinfo=UTC)
        await cast(Any, message_ledger)._query(
            f"UPDATE {_schema().TO_RELATION} SET acked_at = $stamp WHERE out = $out",
            {"stamp": sentinel, "out": RecordID(AGENT_TABLE, AGENT_FIXER_B[0])},
        )
        rows = await cast(Any, message_ledger)._query(
            f"SELECT acked_at FROM {_schema().TO_RELATION} WHERE out = $out",
            {"out": RecordID(AGENT_TABLE, AGENT_FIXER_B[0])},
        )
        assert rows and rows[0]["acked_at"] is not None
        assert rows[0]["acked_at"].year == 2099, (
            "an UNGUARDED update did not overwrite — write-once cannot be attributed to the guard"
        )


class TestAckDisambiguatesTheFourWayEmptyReturn:
    """Ruling 4 + probe 4c: the raw guarded ``UPDATE`` returns a byte-identical
    ``[]`` for FOUR different conditions. The fourth (never-ran-due-to-conflict)
    is killed by riding the shared retry driver; the other three are
    disambiguated by a follow-up SELECT and returned as TYPED outcomes.

    Each survivor gets its OWN pin. A contract exercising only "already
    stamped" waves through a build that silently accepts FORGED edge ids.
    """

    async def test_already_stamped(self, message_ledger: Any) -> None:
        [seq] = await _send_n(message_ledger, 1, grade=_msg().MESSAGE_GRADE_DIRECTIVE)
        await message_ledger.ack(agent_id=AGENT_FIXER_B[0], seqs=[seq])
        result = await message_ledger.ack(agent_id=AGENT_FIXER_B[0], seqs=[seq])
        assert result.entries[0].outcome == "already_acked"

    async def test_no_such_message(self, message_ledger: Any) -> None:
        await _send_n(message_ledger, 1, grade=_msg().MESSAGE_GRADE_DIRECTIVE)
        result = await message_ledger.ack(agent_id=AGENT_FIXER_B[0], seqs=[999_999])
        assert result.entries[0].outcome == "unknown_message", (
            "a seq that names no message must NOT be reported as an idempotent re-ack — "
            "that is how a forged id is silently accepted"
        )

    async def test_not_addressed_to_me(self, message_ledger: Any) -> None:
        """The NEGATIVE ownership pin (frontier #10, ruling 4's ``AND out = $me``).
        The message exists and is real — it is simply not addressed to the caller.
        """
        [seq] = await _send_n(
            message_ledger, 1, recipient=AGENT_FIXER_B, grade=_msg().MESSAGE_GRADE_DIRECTIVE
        )
        result = await message_ledger.ack(agent_id=AGENT_SCOUT_D[0], seqs=[seq])
        assert result.entries[0].outcome == "not_addressed", (
            "acking a message you were never sent must be distinguishable from acking a "
            "nonexistent one — the raw CAS collapses both to []"
        )

    async def test_acking_another_agents_edge_leaves_that_edge_UNCHANGED(
        self, message_ledger: Any
    ) -> None:
        """Frontier #10's load-bearing half: the rejection is INVISIBLE in the
        return value (probe 4c), so the pin must assert POSITIVELY on the
        victim's row. One message, two recipients; A acks; B's edge must be
        untouched.
        """
        result = await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=BODY_DIRECTIVE,
            grade=_msg().MESSAGE_GRADE_DIRECTIVE,
            recipients=[_ref(AGENT_FIXER_B), _ref(AGENT_AUDIT_C)],
        )
        seq = result.message.seq
        acked = await message_ledger.ack(agent_id=AGENT_FIXER_B[0], seqs=[seq])
        assert acked.entries[0].outcome == "acked"
        victim = await message_ledger.drain(agent_id=AGENT_AUDIT_C[0], limit=20, peek=True)
        assert len(victim.entries) == 1
        assert victim.entries[0].acked_at is None, (
            "fixer-b's ack stamped audit-c's edge — the CAS is not scoped by ownership"
        )

    async def test_ack_note_lands_on_the_edge_the_CAS_WON(
        self, message_ledger: Any
    ) -> None:
        """M8 — ``ack(note=)`` is in the design's tool table
        (``one-of-claude-codes-nifty-garden.md``: ``ack | agent, seqs[], note?``)
        and ``ack_note?`` is a declared column on the ``to`` edge. Nothing
        exercised either.

        ⚠ The adversary wondered whether this is a spec GAP. It is not — both the
        param and the column are in the approved design; the contract simply had
        no pin. Kills a build that accepts ``note`` and silently discards it.
        """
        [seq] = await _send_n(message_ledger, 1, grade=_msg().MESSAGE_GRADE_DIRECTIVE)
        await message_ledger.ack(
            agent_id=AGENT_FIXER_B[0], seqs=[seq], note="re-ran the gate; 5551/0"
        )
        drained = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=20, peek=True)
        assert drained.entries[0].ack_note == "re-ran the gate; 5551/0"

    async def test_an_ack_with_NO_note_leaves_it_unset(
        self, message_ledger: Any
    ) -> None:
        """M8's monoculture break — a build hardcoding a note string, or
        stamping a placeholder, passes the pin above."""
        [seq] = await _send_n(message_ledger, 1, grade=_msg().MESSAGE_GRADE_DIRECTIVE)
        await message_ledger.ack(agent_id=AGENT_FIXER_B[0], seqs=[seq])
        drained = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=20, peek=True)
        assert drained.entries[0].ack_note is None

    async def test_a_note_never_reaches_an_ALREADY_acked_edge(
        self, message_ledger: Any
    ) -> None:
        """The write-once door applies to the NOTE as well as the stamp — a
        second ack must not smuggle a new note through a guard that only
        protects ``acked_at``.
        """
        [seq] = await _send_n(message_ledger, 1, grade=_msg().MESSAGE_GRADE_DIRECTIVE)
        await message_ledger.ack(agent_id=AGENT_FIXER_B[0], seqs=[seq], note="first")
        await message_ledger.ack(agent_id=AGENT_FIXER_B[0], seqs=[seq], note="second")
        drained = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=20, peek=True)
        assert drained.entries[0].ack_note == "first", (
            "a second ack overwrote the note — write-once guards the stamp but not the "
            "note, so the record of what the recipient actually reported is mutable"
        )

    async def test_an_empty_seqs_list_is_an_honest_empty_result(
        self, message_ledger: Any
    ) -> None:
        """Residual 7.3 — the 0 end of the 0/1/cap−1/cap/cap+1 discipline. An
        empty request is not an error; it is nothing to do, reported honestly.
        """
        result = await message_ledger.ack(agent_id=AGENT_FIXER_B[0], seqs=[])
        assert result.entries == []
        assert result.acked_count == 0
        assert result.already_acked_count == 0

    async def test_a_mixed_batch_reports_every_seqs_own_fate(
        self, message_ledger: Any
    ) -> None:
        """THE QUANTIFIER LAW: ∀ requested seqs — every one comes back with its
        OWN outcome, never silently dropped, REGARDLESS of cause. All four fates
        are FORCED in one call, so a ∀ helper cannot pass because a branch was
        unreachable.
        """
        result = await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=BODY_DIRECTIVE,
            grade=_msg().MESSAGE_GRADE_DIRECTIVE,
            recipients=[_ref(AGENT_FIXER_B), _ref(AGENT_AUDIT_C)],
        )
        fresh = await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body="a second directive",
            grade=_msg().MESSAGE_GRADE_DIRECTIVE,
            recipients=[_ref(AGENT_FIXER_B)],
        )
        not_mine = await message_ledger.send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body="for scout-d only",
            grade=_msg().MESSAGE_GRADE_DIRECTIVE,
            recipients=[_ref(AGENT_SCOUT_D)],
        )
        await message_ledger.ack(agent_id=AGENT_FIXER_B[0], seqs=[result.message.seq])
        requested = [
            result.message.seq,  # already_acked
            fresh.message.seq,  # acked
            not_mine.message.seq,  # not_addressed
            999_999,  # unknown_message
        ]
        batch = await message_ledger.ack(agent_id=AGENT_FIXER_B[0], seqs=requested)
        assert [entry.seq for entry in batch.entries] == requested, (
            "every requested seq must be accounted for, in order — a dropped seq is the "
            "silent-loss shape the quantifier law exists to forbid"
        )
        assert [entry.outcome for entry in batch.entries] == [
            "already_acked",
            "acked",
            "not_addressed",
            "unknown_message",
        ]


class TestACasWinnerIsAlwaysReportedAcked:
    """R8 (cold audit of packet 03a-2, §7): ``_ack_entries`` tested
    ``message_id not in stored_stamps`` (→ ``not_addressed``) BEFORE
    ``message_id in won_stamps`` (→ ``acked``). So a CAS WINNER whose follow-up
    SELECT row had gone missing was reported ``not_addressed`` — *"you were never
    sent this"* about a message the very same call had just successfully stamped.
    The stamp is real and durable; only the report is a lie, which is the worst
    direction: the caller re-acks, or files the delivery as never made.

    THE INVARIANT: a CAS winner is ALWAYS reported ``acked``. It follows from what
    the two statements ARE — the follow-up SELECT drops only the
    ``acked_at IS NONE`` conjunct, so it is a strict SUPERSET of the CAS's matched
    set, and a winner missing from it is not evidence of "no edge to me", it is
    evidence the edge DISAPPEARED between two statements.

    Reachable only when that happens: a hard agent delete cascades its edges away
    (store reference §4). LATENT today because agents are RETIRED, never
    hard-deleted — the same latency clause as finding #105, and the same reason to
    pin it rather than wait: latent is not absent, and the clause dies the day
    anything hard-deletes a node.
    """

    @staticmethod
    async def _ack_with_the_edge_deleted_mid_call(
        ledger: Any, *, agent_id: str, seqs: list[int]
    ) -> Any:
        """Ack ``seqs`` with this agent's delivery edges deleted between the CAS
        and its read-back — the R8 window, forced deterministically.

        The injection is keyed on the CAS's own write-once guard
        (:data:`_ACK_CAS_GUARD_MARKER`) and the caller ASSERTS it fired, so a
        rename that stops the marker matching turns the pin RED rather than
        letting it pass on an injection that never happened.
        """
        original_query = cast(Any, ledger)._query
        fired: list[str] = []

        async def query_deleting_the_edge_after_the_cas(
            statement: str, params: Any = None
        ) -> Any:
            result = await original_query(statement, params)
            if _ACK_CAS_GUARD_MARKER in statement and not fired:
                fired.append(statement)
                await original_query(
                    f"DELETE {_schema().TO_RELATION} WHERE out = $out",
                    {"out": RecordID(AGENT_TABLE, agent_id)},
                )
            return result

        cast(Any, ledger)._query = query_deleting_the_edge_after_the_cas
        try:
            result = await ledger.ack(agent_id=agent_id, seqs=seqs)
        finally:
            cast(Any, ledger)._query = original_query
        assert fired, (
            "the fixture never matched the ack CAS, so the edge was never deleted and "
            "this pin proves nothing — the guarded UPDATE no longer carries "
            f"{_ACK_CAS_GUARD_MARKER!r}"
        )
        return result

    async def test_a_winner_whose_edge_VANISHES_mid_call_is_still_acked(
        self, message_ledger: Any
    ) -> None:
        """The pin. The CAS won and the stamp landed; the edge then vanished
        before the disambiguating read. ``not_addressed`` is the one outcome that
        cannot be true here.
        """
        if not _is_real(message_ledger):
            pytest.skip("deleting an edge between two statements is a REAL-backend fixture")
        [seq] = await _send_n(message_ledger, 1, grade=_msg().MESSAGE_GRADE_DIRECTIVE)
        result = await self._ack_with_the_edge_deleted_mid_call(
            message_ledger, agent_id=AGENT_FIXER_B[0], seqs=[seq]
        )
        assert result.entries[0].outcome == "acked", (
            f"a CAS WINNER was reported {result.entries[0].outcome!r} — the ack stamped "
            f"the edge and then told its caller it was never sent the message. The "
            f"outcome ladder tests 'no stored edge' BEFORE 'I won the CAS'; the win is "
            f"the stronger evidence and must be read first"
        )
        assert result.acked_count == 1
        assert result.entries[0].acked_at is not None, (
            "the winner reported `acked` with no stamp — a winner always carries the "
            "value it just wrote"
        )

    async def test_a_REPEATED_seq_whose_edge_vanishes_is_ALREADY_acked(
        self, message_ledger: Any
    ) -> None:
        """The same lie one notch down. Inside ONE batch the first occurrence of a
        seq wins the CAS and the rest are idempotent no-ops. With the edge gone
        before the read-back, those repeats must read ``already_acked`` — this
        call demonstrably HAS an edge to this agent (it just stamped it), so
        "you were never sent this" is false for EVERY occurrence, not only the
        first. Without this the ``won_stamps`` fallback in the ladder's
        already-acked branch is code no pin reaches.
        """
        if not _is_real(message_ledger):
            pytest.skip("deleting an edge between two statements is a REAL-backend fixture")
        [seq] = await _send_n(message_ledger, 1, grade=_msg().MESSAGE_GRADE_DIRECTIVE)
        result = await self._ack_with_the_edge_deleted_mid_call(
            message_ledger, agent_id=AGENT_FIXER_B[0], seqs=[seq, seq]
        )
        assert [entry.outcome for entry in result.entries] == ["acked", "already_acked"]
        assert result.entries[1].acked_at == result.entries[0].acked_at, (
            "the repeat reported a different stamp from the win it duplicates — every "
            "occurrence of one seq observes the SAME single `acked_at`"
        )

    async def test_a_genuinely_UNADDRESSED_seq_still_reports_not_addressed(
        self, message_ledger: Any
    ) -> None:
        """THE CONTROL. The two pins above are satisfiable by deleting
        ``not_addressed`` from the ladder entirely — so this forces the outcome
        the reordering must NOT swallow: a real message, never delivered to the
        caller, no CAS win and no stored edge. It stays distinguishable from a
        seq that names no message at all.
        """
        [seq] = await _send_n(
            message_ledger, 1, recipient=AGENT_FIXER_B, grade=_msg().MESSAGE_GRADE_DIRECTIVE
        )
        result = await message_ledger.ack(agent_id=AGENT_SCOUT_D[0], seqs=[seq, 999_999])
        assert [entry.outcome for entry in result.entries] == [
            "not_addressed",
            "unknown_message",
        ], (
            "reordering the outcome ladder to read the CAS win first must not swallow "
            "`not_addressed` — an agent with NO edge to a real message is still exactly "
            "as distinguishable from a forged seq as it was before"
        )


# =========================================================================== #
# Section E — the mint: native sequence, gaps, and live contention
# =========================================================================== #


class TestSeqIsAnOrderingKeyNotACount:
    async def test_seqs_are_strictly_increasing(self, message_ledger: Any) -> None:
        seqs = await _send_n(message_ledger, 4)
        assert seqs == sorted(seqs)
        assert len(set(seqs)) == 4

    async def test_a_gap_breaks_nothing(self, message_ledger: Any) -> None:
        """Frontier #14 / store reference §5 / probe 3 leg C: an aborted
        transaction BURNS a number, so gaps are REAL and permanent. A consumer
        that treats ``seq`` as a count, a gapless handle, or a "how many
        messages" display is wrong. Forced here by consuming a number outside
        any send, then proving the whole round-trip still works and the counts
        come from the ROW SET rather than from seq arithmetic.
        """
        first = await _send_n(message_ledger, 1)
        if _is_real(message_ledger):
            await cast(Any, message_ledger)._query(
                f'RETURN sequence::nextval("{_schema().MESSAGE_SEQUENCE_NAME}")'
            )
        else:
            cast(Any, message_ledger).burn_seq()
        second = await _send_n(message_ledger, 1)
        assert second[0] > first[0] + 1, "control: a number was genuinely burned"
        drained = await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=20, peek=True)
        assert drained.total_pending == 2, (
            "the pending count was derived from seq arithmetic rather than from the rows"
        )
        assert [entry.seq for entry in drained.entries] == [first[0], second[0]]


class TestConcurrentSendsMintDistinctSeqs:
    """The load-bearing mint pin. Races SEPARATE ledger instances on SEPARATE
    live connections — N coroutines on ONE socket do not contend the way N
    connections do (REPORT-recon-pkt03 §F.4).

    THE WRONG BUILD (frontier #13): ``seq`` minted by read-max-then-CREATE. It
    is single-threaded-correct and passes every test in section B; it collides
    here. Probe 3c measured the correct mechanism at 16-way × 20 rounds:
    320/320 committed, zero conflicts, zero duplicates.
    """

    @staticmethod
    async def _race(
        factory: MessageLedgerFactory, senders: int, *, ledger: Any | None = None
    ) -> list[int]:
        ledgers = [await factory() for _ in range(senders)]
        await _seed_agents(
            ledgers[0], [_ref(SENDER_LEAD), _ref(AGENT_FIXER_B)], session=SESSION_WAVE7
        )
        assert ledger is None or ledger is not ledgers[0]
        results = await asyncio.gather(
            *[
                ledger.send(
                    sender=_ref(SENDER_LEAD),
                    session=SESSION_WAVE7,
                    body=f"concurrent body {index}",
                    grade=_msg().MESSAGE_GRADE_SIGNAL,
                    recipients=[_ref(AGENT_FIXER_B)],
                )
                for index, ledger in enumerate(ledgers)
            ]
        )
        return sorted(result.message.seq for result in results)

    async def test_eight_concurrent_sends_all_land_on_distinct_seqs(
        self, message_ledger_factory: MessageLedgerFactory
    ) -> None:
        seqs = await self._race(message_ledger_factory, _CONCURRENT_SENDERS)
        assert len(seqs) == _CONCURRENT_SENDERS
        assert len(set(seqs)) == _CONCURRENT_SENDERS, f"duplicate seq minted: {seqs}"

    @pytest.mark.parametrize("senders", _CONCURRENT_SENDERS_AT_SCALE)
    async def test_at_scale(
        self, message_ledger_factory: MessageLedgerFactory, senders: int
    ) -> None:
        seqs = await self._race(message_ledger_factory, senders)
        assert len(set(seqs)) == senders, f"duplicate seq minted at {senders}-way: {seqs}"

    async def test_concurrent_seqs_all_exceed_the_pre_race_maximum(
        self, message_ledger_factory: MessageLedgerFactory
    ) -> None:
        """Residual 7.2 — the existing race pins assert DISTINCT, never ORDERED.
        Gaps are legal here, so the findings/briefs "consecutive" assertion is
        unavailable — but MONOTONIC still is, and without it a build minting a
        random or timestamp-derived id passes at both 8- and 16-way.
        """
        ledger = await message_ledger_factory()
        await _seed_agents(
            ledger, [_ref(SENDER_LEAD), _ref(AGENT_FIXER_B)], session=SESSION_WAVE7
        )
        [baseline] = await _send_n(ledger, 1)
        seqs = await self._race(message_ledger_factory, _CONCURRENT_SENDERS, ledger=ledger)
        assert all(seq > baseline for seq in seqs), (
            f"a concurrently-minted seq did not exceed the pre-race maximum {baseline}: "
            f"{seqs} — the mint is not a monotonic sequence"
        )

    async def test_every_concurrent_send_is_readable_by_its_recipient(
        self, message_ledger_factory: MessageLedgerFactory
    ) -> None:
        """A distinct-seq assertion alone waves through a build that mints
        correctly and then LOSES rows (store reference §5's masked-conflict
        shape — 160/160 false successes through ``query()``). The recipient's
        own inbox is the independent read.
        """
        seqs = await self._race(message_ledger_factory, _CONCURRENT_SENDERS)
        reader = await message_ledger_factory()
        drained = await reader.drain(
            agent_id=AGENT_FIXER_B[0], limit=_CONCURRENT_SENDERS * 2, peek=True
        )
        assert drained.total_pending == _CONCURRENT_SENDERS
        assert [entry.seq for entry in drained.entries] == seqs


class TestConcurrentAcksOfOneEdgeProduceExactlyOneWinner:
    """Probe 4 leg D, at 16-way: exactly one racer stamps; the rest report
    ``already_acked``; NONE reports a spurious outcome and none is lost to an
    exhausted retry.

    This is where the contention actually lives — probe 3c proved the fan-out
    itself does not contend (320/320, zero conflicts), so the CAS stamp is the
    hot path. A racer that CONFLICTS is NOT a legitimate loser: it never ran,
    and without the shared retry driver it reports "already acked" when in fact
    nothing happened.
    """

    async def test_sixteen_ackers_of_one_edge(
        self, message_ledger_factory: MessageLedgerFactory
    ) -> None:
        ledgers = [await message_ledger_factory() for _ in range(_CONCURRENT_ACKERS)]
        await _seed_agents(
            ledgers[0], [_ref(SENDER_LEAD), _ref(AGENT_FIXER_B)], session=SESSION_WAVE7
        )
        sent = await ledgers[0].send(
            sender=_ref(SENDER_LEAD),
            session=SESSION_WAVE7,
            body=BODY_DIRECTIVE,
            grade=_msg().MESSAGE_GRADE_DIRECTIVE,
            recipients=[_ref(AGENT_FIXER_B)],
        )
        seq = sent.message.seq
        results = await asyncio.gather(
            *[ledger.ack(agent_id=AGENT_FIXER_B[0], seqs=[seq]) for ledger in ledgers]
        )
        outcomes = [result.entries[0].outcome for result in results]
        assert outcomes.count("acked") == 1, (
            f"expected EXACTLY one winner at {_CONCURRENT_ACKERS}-way, got {outcomes}"
        )
        assert outcomes.count("already_acked") == _CONCURRENT_ACKERS - 1, (
            "a racer reported neither a win nor an idempotent no-op — a conflicted "
            "transaction was surfaced as a legitimate outcome instead of being retried"
        )
        stamps = {result.entries[0].acked_at for result in results}
        assert len(stamps) == 1 and None not in stamps, (
            f"every racer must observe the SAME single stamp, got {stamps!r}"
        )


# =========================================================================== #
# Section F — the seam: the module cannot escape the shared retry driver
# =========================================================================== #


class TestTheLedgerIsDiscoverableByTheSeamEnumerator:
    """``test_retry_seam.py``'s enumerators find a class OWNING an
    ``async def _query`` — that is what routes ~19 parametrized retry/marker/
    mutation pins over a new module automatically, with no registration list.

    But the enumerator is NAME-KEYED, and the repo's own catalogue of six
    instrument defeats includes exactly this one: ``scout.py`` spells its seam
    differently and is invisible to it. ``_MIN_KNOWN_SEAMS`` is a FLOOR, so a
    MessageLedger that quietly falls out of the enumeration keeps the suite
    green. This pin is the thing that notices.
    """

    def test_message_ledger_owns_a_query_seam_the_enumerator_finds(self) -> None:
        from test_retry_seam import _discover_query_seams

        discovered = {seam.__name__ for _, seam in _discover_query_seams()}
        assert _msg().MessageLedger.__name__ in discovered, (
            "MessageLedger is NOT discovered by test_retry_seam's seam enumerator — it must "
            "own an `async def _query` (the sibling ledgers' spelling). A differently-spelled "
            "seam silently drops ~19 retry/marker/mutation pins AND leaves every SDK call "
            "site it adds unwatched: the scout.py defeat, recommitted."
        )

    def test_the_constructor_is_the_standard_five_the_seam_harness_knows(self) -> None:
        """``_CTOR_VALUES`` (``test_retry_seam.py:633``) is the ONE hand-maintained
        list a new module touches. Keeping to the five standard kwargs means it
        needs no edit; a NEW required parameter fails LOUDLY there instead.
        """
        import inspect

        required = {
            name
            for name, parameter in inspect.signature(_msg().MessageLedger).parameters.items()
            if parameter.default is inspect.Parameter.empty and name != "self"
        }
        assert required == {"url", "namespace", "database", "user", "password"}


class TestTheDdlSliceIsAppliedByEnsureReady:
    """Store reference §5 / probe 5: EVERY table production writes to must be
    DECLARED before first write — concurrent first-writes against an undeclared
    table storm with retryable conflicts (22/192 first-pass success), and an
    undeclared EDGE table is auto-created ``TYPE ANY``, silently discarding the
    ``IN``/``OUT`` constraint that is the only endpoint validation the engine
    offers. The comms precedent is that the OWNING class applies its own slice.
    """

    async def test_ensure_ready_creates_the_message_and_to_tables(
        self, message_ledger: Any
    ) -> None:
        if not _is_real(message_ledger):
            pytest.skip("live DDL application is a REAL-backend observation")
        info = await cast(Any, message_ledger)._query("INFO FOR DB")
        row = info[0] if isinstance(info, list) else info
        tables = set(row.get("tables", {}))
        assert {_schema().MESSAGE_TABLE, _schema().TO_RELATION} <= tables
        assert _schema().MESSAGE_SEQUENCE_NAME in set(row.get("sequences", {})), (
            "the native sequence must be DEFINEd by the slice, not created implicitly"
        )

    async def test_ensure_ready_is_idempotent(self, message_ledger: Any) -> None:
        """Probe 3 leg D: no ``DEFINE SEQUENCE`` variant resets the counter, and a
        BARE ``DEFINE SEQUENCE`` RAISES on re-apply — a boot-time crash on every
        start after the first. Re-applying must be a clean no-op AND must not
        rewind ``seq``.
        """
        first = await _send_n(message_ledger, 1)
        await message_ledger.ensure_ready()
        second = await _send_n(message_ledger, 1)
        assert second[0] > first[0], (
            "re-applying the slice rewound the sequence — a re-issued number is the "
            "catastrophic case probe 3 leg D exists to rule out"
        )


async def _message_row_count(ledger: Any) -> int:
    rows = await cast(Any, ledger)._query(f"SELECT count() FROM {_schema().MESSAGE_TABLE} GROUP ALL")
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return 0
    return int(rows[0].get("count", 0))


async def _edge_row_count(ledger: Any) -> int:
    """The RAW ``to`` edge count — it sees ORPHAN edges (an edge whose message
    row was rolled back) that a join-based read drops silently.
    """
    rows = await cast(Any, ledger)._query(f"SELECT count() FROM {_schema().TO_RELATION} GROUP ALL")
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return 0
    return int(rows[0].get("count", 0))


# --------------------------------------------------------------------------- #
# THE WRITE WATCH — the instrument behind ``test_the_derivation_writes_NOTHING``.
#
# ⚠ WHY IT IS NOT A ROW COUNT. That pin used to read ``message`` and ``to`` row
# COUNTS: the two tables its author thought to count. That is the forbidden-set
# shape this repo has now lost to six times (CLAUDE.md §"the instrument lesson" —
# *the forbidden set is unbounded; the SAFE set is small and enumerable, so
# allowlist the safe*). Measured, cold audit of packet 03a-2 §3.2: injecting
# ``UPDATE agent SET status = 'input_required'`` into ``awaiting_answer`` —
# ruling 9's STRUCK stored state, verbatim, and a legal member of the schema's own
# closed status vocabulary — left the WHOLE ``[real]`` leg at 86 passed / 0
# failed. So did ``UPDATE agent SET last_note = …`` and ``UPDATE to SET seen_at =
# …`` (which silently marks the entire inbox seen). Only a row CREATE was caught,
# because only a row CREATE moves a row COUNT.
#
# So this allowlists the SAFE set instead, and the safe set is one word long.
# --------------------------------------------------------------------------- #

# The only statement form a pure READ needs. Everything else — any verb, any
# table, including a table nobody has thought of yet — counts as a WRITE.
# Widening this set is a deliberate act: add a form only when it provably cannot
# write, and say why beside the entry.
_READ_ONLY_STATEMENT_HEADS = frozenset({"SELECT"})

# The one marker that identifies the ack CAS among the statements ``ack`` issues:
# the write-once guard itself (``TestAckIsWriteOnce`` is the pin that makes it
# load-bearing). Used by the R8 fixture to make an edge vanish BETWEEN the CAS and
# its read-back; that fixture asserts the injection FIRED, so a marker that ever
# stops matching turns the test RED rather than silently vacuous.
_ACK_CAS_GUARD_MARKER = "acked_at IS NONE"


class _WriteWatch:
    """Records EVERY SurrealQL statement a ledger issues at its CONNECTION seam,
    classifying each against :data:`_READ_ONLY_STATEMENT_HEADS`.

    Installed by shadowing the ledger's ``_ensure_connection`` — the ONE
    acquisition every seam resolves at call time (``run_query``'s and
    ``execute_transaction``'s ``acquire=`` argument alike) — and wrapping
    ``query_raw`` on whatever connection it hands back. ``query_raw`` ALONE covers
    both store seams: the SDK's own ``query()`` is implemented as
    ``self.query_raw(...)`` ([CODE] ``surrealdb/connections/async_ws.py``), so the
    single-statement seam reaches it too, and wrapping both would double-count.
    Re-installs on a reconnect, because the wrap follows the ACQUISITION rather
    than one connection object.

    ⚠ WHO THIS GATE IS FOR — stated in the instrument, so its verdicts follow
    mechanically (CLAUDE.md, "a gate needs a threat model"). It catches the HONEST
    ENGINEER who adds a stamp to a derivation that must stay a pure read: someone
    writing ``await self._query("UPDATE …")`` or ``self._apply([...])`` the way
    the rest of the module does. It is NOT a boundary against an author
    deliberately routing around the store seam — anyone who can commit here can
    ship anything. That is why the content-snapshot leg exists beside it: that leg
    is RECEIVER-BLIND (it observes the store's state, not the call), so it still
    sees a write issued through some SDK method this never wraps.

    ⚠ ITS REACH IS A BOUND, AND THE BOUND IS CHECKED, NOT ASSUMED (CLAUDE.md: *a
    runtime gate is an invariant only over code it actually RUNS*). A statement
    issued on a connection obtained WITHOUT going through ``_ensure_connection``
    is invisible here — which is exactly why every pin using this watch asserts
    :attr:`reads` is non-empty before trusting an empty :attr:`writes`.

    Usage::

        async with _WriteWatch(ledger) as watch:
            await ledger.awaiting_answer(agent_id=...)
        assert watch.reads and watch.writes == []
    """

    def __init__(self, ledger: Any) -> None:
        self.statements: list[str] = []
        self._ledger = ledger
        self._original_ensure: Any = None
        self._restores: list[tuple[Any, Any]] = []

    @staticmethod
    def _is_read_only(statement: str) -> bool:
        """Is ``statement`` a SINGLE allowlisted read?

        Multi-statement text is refused outright rather than judged by its first
        word: the SDK's ``query()`` validates statement[0] ONLY (store reference
        §3), so a trailing write behind a leading ``SELECT`` is precisely the shape
        a head-keyed classifier must not bless.
        """
        body = statement.strip().rstrip(";").strip()
        if ";" in body:
            return False
        head = body.split(maxsplit=1)[0].upper() if body.split() else ""
        return head in _READ_ONLY_STATEMENT_HEADS

    @property
    def reads(self) -> list[str]:
        """The observed statements that ARE allowlisted reads."""
        return [statement for statement in self.statements if self._is_read_only(statement)]

    @property
    def writes(self) -> list[str]:
        """The observed statements that are NOT allowlisted reads."""
        return [statement for statement in self.statements if not self._is_read_only(statement)]

    def _instrument(self, connection: Any) -> None:
        """Wrap ``connection``'s single SDK statement entry point, once.

        The passthrough is ``*args``/``**kwargs`` rather than a re-declared
        signature: the SDK's ``query()`` forwards ``session_id``/``txn_id``
        keywords into ``query_raw``, and a wrapper that re-spells the signature
        breaks on the ones it forgot.
        """
        if any(existing is connection for existing, _ in self._restores):
            return
        original_query_raw = connection.query_raw

        async def watched_query_raw(statement: str, *args: Any, **kwargs: Any) -> Any:
            self.statements.append(statement)
            return await original_query_raw(statement, *args, **kwargs)

        connection.query_raw = watched_query_raw
        self._restores.append((connection, original_query_raw))

    async def __aenter__(self) -> _WriteWatch:
        self._original_ensure = self._ledger._ensure_connection

        async def watched_ensure_connection() -> Any:
            connection = await self._original_ensure()
            self._instrument(connection)
            return connection

        self._ledger._ensure_connection = watched_ensure_connection
        return self

    async def __aexit__(self, *_exc_info: Any) -> None:
        self._ledger._ensure_connection = self._original_ensure
        for connection, original_query_raw in self._restores:
            connection.query_raw = original_query_raw
        self._restores.clear()


async def _database_snapshot(ledger: Any) -> dict[str, list[str]]:
    """EVERY table's full content, keyed by table name.

    The table set is enumerated from ``INFO FOR DB`` at read time — never from a
    hand-written list — so a write to a table nobody thought to count still moves
    the snapshot, and an auto-created table (store reference §5: an undeclared
    write auto-creates its table) appears as a brand-new key.

    This is the leg that closes the allowlist's OWN door: a write SMUGGLED INSIDE
    a read — ``SELECT * FROM (UPDATE agent SET status = 'x')`` — is ACCEPTED by
    the engine and DOES write [PROBED 2026-07-23, spike-surreal 3.2.1], so a
    head-keyed classifier alone would be the next name-list to fall.
    """
    info = await cast(Any, ledger)._query("INFO FOR DB")
    tables = sorted(info.get("tables", {})) if isinstance(info, dict) else []
    snapshot: dict[str, list[str]] = {}
    for table in tables:
        rows = await cast(Any, ledger)._query("SELECT * FROM type::table($table)", {"table": table})
        snapshot[table] = sorted(repr(row) for row in rows) if isinstance(rows, list) else [repr(rows)]
    return snapshot


# =========================================================================== #
# Section G — RULING 9: the WAITING state is DERIVED, never stored
#
# Resolves a direct contradiction between the approved design ("drain by a
# parked agent flips it back to active") and shipped code (``agents.py``:
# ``touch`` auto-flips ONLY idle->active; ``input_required`` never auto-flips).
# BOTH are struck. An agent is awaiting-input **iff it has a question thread
# with no answer on it**, computed at read time exactly as ``orphaned`` is
# already derived from ``heartbeat_at``.
#
# What that buys, mechanically: nothing is stamped, so nothing can be lost; no
# caller has to REMEMBER to clear it; and there is no un-park verb to forget to
# call. What it costs is recorded as a KNOWN BOUND at the end of this section.
#
# ``set_status='input_required'`` on ``send`` therefore does NOT store a waiting
# state — it MARKS THAT MESSAGE as the question whose thread the derivation
# reads.
# =========================================================================== #


class TestSetStatusMarksTheQuestionItDoesNotStoreAState:
    async def test_send_with_set_status_marks_the_message_as_a_question(
        self, message_ledger: Any
    ) -> None:
        result = await message_ledger.send(
            sender=_ref(AGENT_FIXER_B),
            session=SESSION_WAVE7,
            body="which fixture value should the cap boundary use?",
            grade=_msg().MESSAGE_GRADE_DIRECTIVE,
            recipients=[_ref(SENDER_LEAD)],
            thread="q:cap-boundary",
            set_status="input_required",
        )
        assert result.message.question is True

    async def test_an_ordinary_send_is_NOT_a_question(
        self, message_ledger: Any
    ) -> None:
        """PARAMETER MONOCULTURE: the pin above cannot tell "marks questions"
        from "marks everything". This is the other value.
        """
        result = await message_ledger.send(
            sender=_ref(AGENT_FIXER_B),
            session=SESSION_WAVE7,
            body=BODY_SIGNAL,
            grade=_msg().MESSAGE_GRADE_DIRECTIVE,
            recipients=[_ref(SENDER_LEAD)],
        )
        assert result.message.question is False

    @pytest.mark.parametrize("other_status", ["idle", "active"])
    async def test_a_DIFFERENT_set_status_value_does_NOT_mark_a_question(
        self, message_ledger: Any, other_status: str
    ) -> None:
        """M5 / PARAMETER MONOCULTURE — every other ``set_status`` call site in
        this file passes ``'input_required'``, so a build reading
        ``question = (set_status is not None)`` passes all of them.

        KILLS the adversary's W3.
        """
        result = await message_ledger.send(
            sender=_ref(AGENT_FIXER_B),
            session=SESSION_WAVE7,
            body=BODY_SIGNAL,
            grade=_msg().MESSAGE_GRADE_SIGNAL,
            recipients=[_ref(SENDER_LEAD)],
            set_status=other_status,
        )
        assert result.message.question is False, (
            f"set_status={other_status!r} marked the message as a QUESTION — only "
            f"'input_required' asks one; a build keyed on 'is set_status present' parks "
            f"the sender on an ordinary status touch"
        )

    async def test_a_question_still_delivers_normally(
        self, message_ledger: Any
    ) -> None:
        """A question is a MESSAGE first. A build that treats ``set_status`` as
        a status-only side channel and skips the fan-out loses the question.
        """
        result = await message_ledger.send(
            sender=_ref(AGENT_FIXER_B),
            session=SESSION_WAVE7,
            body="blocked: which fixture value?",
            grade=_msg().MESSAGE_GRADE_DIRECTIVE,
            recipients=[_ref(SENDER_LEAD)],
            thread="q:cap-boundary",
            set_status="input_required",
        )
        drained = await message_ledger.drain(agent_id=SENDER_LEAD[0], limit=20, peek=True)
        assert [entry.seq for entry in drained.entries] == [result.message.seq]


async def _ask(
    ledger: Any,
    *,
    thread: str,
    asker: tuple[str, str] = AGENT_FIXER_B,
    grade: str | None = None,
) -> int:
    """Send a QUESTION. ``grade`` is a PARAMETER on purpose — ``question`` and
    ``grade`` are ORTHOGONAL, and a helper that hardcoded ``directive`` here
    would correlate them in every fixture in this file (the adversary's W1).
    """
    grade = grade if grade is not None else _msg().MESSAGE_GRADE_DIRECTIVE
    result = await ledger.send(
        sender=_ref(asker),
        session=SESSION_WAVE7,
        body=f"question on {thread}",
        grade=grade,
        recipients=[_ref(SENDER_LEAD)],
        thread=thread,
        set_status="input_required",
    )
    return result.message.seq


async def _answer(
    ledger: Any,
    *,
    thread: str,
    to: tuple[str, str] = AGENT_FIXER_B,
    grade: str | None = None,
) -> int:
    """Send an ANSWER — ``grade`` parametrised for the same reason as ``_ask``."""
    grade = grade if grade is not None else _msg().MESSAGE_GRADE_SIGNAL
    result = await ledger.send(
        sender=_ref(SENDER_LEAD),
        session=SESSION_WAVE7,
        body=f"answer on {thread}",
        grade=grade,
        recipients=[_ref(to)],
        thread=thread,
    )
    return result.message.seq


class TestTheWaitingStateIsDerived:
    """The four fates of a question, each FORCED by its own fixture — no branch
    is reachable-only-in-principle.
    """

    async def test_a_SIGNAL_grade_question_DOES_make_the_sender_waiting(
        self, message_ledger: Any
    ) -> None:
        """M1 / BLOCKER-1 — THE PIN THAT FORCES THE MECHANISM TO BE READ.

        Ruling 9's column is worthless if nothing requires the derivation to
        CONSULT it. Every other fixture in this section sends its question as a
        DIRECTIVE, so ``message.question`` and ``grade == 'directive'`` were
        perfectly correlated and a build keying on ``grade`` — never reading the
        column at all — passed all 12 derivation pins, both known-bound pins and
        all three ``set_status`` pins.

        That is the #94 shape the repo has already paid for: a contract pins a
        beautiful new symbol and never requires the code to USE it.

        Here the question is a SIGNAL. A grade-keyed build reports "not
        waiting". KILLS the adversary's W1.
        """
        await _ask(message_ledger, thread="q:cap-boundary", grade=_msg().MESSAGE_GRADE_SIGNAL)
        waiting = await message_ledger.awaiting_answer(agent_id=AGENT_FIXER_B[0])
        assert waiting is not None, (
            "a SIGNAL-graded question did not park its sender — the derivation reads "
            "`grade` instead of `question`, so ruling 9's mechanism is present in the "
            "schema and DEAD in the code"
        )
        assert waiting.thread == "q:cap-boundary"

    async def test_a_DIRECTIVE_sent_without_set_status_does_NOT_make_the_sender_waiting(
        self, message_ledger: Any
    ) -> None:
        """M1's other direction — the pair is what discriminates. A directive is
        a must-ACK, not a question; conflating them parks every agent that ever
        issues an instruction.
        """
        await message_ledger.send(
            sender=_ref(AGENT_FIXER_B),
            session=SESSION_WAVE7,
            body=BODY_DIRECTIVE,
            grade=_msg().MESSAGE_GRADE_DIRECTIVE,
            recipients=[_ref(SENDER_LEAD)],
            thread="q:cap-boundary",
        )
        assert await message_ledger.awaiting_answer(agent_id=AGENT_FIXER_B[0]) is None, (
            "an ordinary DIRECTIVE parked its sender — `grade` is being read as if it "
            "were `question`; the two are ORTHOGONAL"
        )

    async def test_a_DIRECTIVE_grade_answer_clears_a_question(
        self, message_ledger: Any
    ) -> None:
        """The dual, on the ANSWER side: an answer is any message delivered to
        the asker on the thread — its GRADE is irrelevant. Without this, a build
        could require answers to be signals and silently ignore a directive
        reply.
        """
        await _ask(message_ledger, thread="q:cap-boundary")
        await _answer(message_ledger, thread="q:cap-boundary", grade=_msg().MESSAGE_GRADE_DIRECTIVE)
        assert await message_ledger.awaiting_answer(agent_id=AGENT_FIXER_B[0]) is None

    async def test_no_question_means_not_waiting(self, message_ledger: Any) -> None:
        """The BASELINE control. Without it, a build that returns ``None``
        unconditionally would pass every negative case below for free.
        """
        await message_ledger.send(
            sender=_ref(AGENT_FIXER_B),
            session=SESSION_WAVE7,
            body=BODY_SIGNAL,
            grade=_msg().MESSAGE_GRADE_SIGNAL,
            recipients=[_ref(SENDER_LEAD)],
        )
        assert await message_ledger.awaiting_answer(agent_id=AGENT_FIXER_B[0]) is None

    async def test_an_unanswered_question_makes_the_asker_waiting(
        self, message_ledger: Any
    ) -> None:
        seq = await _ask(message_ledger, thread="q:cap-boundary")
        waiting = await message_ledger.awaiting_answer(agent_id=AGENT_FIXER_B[0])
        assert isinstance(waiting, _msg().WaitingOnAnswer)
        assert waiting.thread == "q:cap-boundary"
        assert waiting.question_seq == seq

    async def test_an_answer_on_the_thread_clears_it_WITHOUT_ANY_WRITE_TO_THE_AGENT(
        self, message_ledger: Any
    ) -> None:
        """The whole point of ruling 9: the state clears because an ANSWER
        EXISTS, not because anybody remembered to un-park anyone. No verb is
        called on the asker between the two assertions.
        """
        await _ask(message_ledger, thread="q:cap-boundary")
        assert await message_ledger.awaiting_answer(agent_id=AGENT_FIXER_B[0]) is not None
        await _answer(message_ledger, thread="q:cap-boundary")
        assert await message_ledger.awaiting_answer(agent_id=AGENT_FIXER_B[0]) is None

    async def test_an_answer_on_a_DIFFERENT_thread_does_not_clear_it(
        self, message_ledger: Any
    ) -> None:
        """DISCRIMINATION: a build reading "any message delivered to the asker
        since the question" instead of "an answer ON THE QUESTION'S THREAD"
        passes the pin above and fails here. Unrelated traffic must never
        silently resolve an outstanding debt.
        """
        await _ask(message_ledger, thread="q:cap-boundary")
        await _answer(message_ledger, thread="wave7-chatter")
        waiting = await message_ledger.awaiting_answer(agent_id=AGENT_FIXER_B[0])
        assert waiting is not None
        assert waiting.thread == "q:cap-boundary"

    async def test_a_message_the_ASKER_sends_on_its_own_thread_is_not_an_answer(
        self, message_ledger: Any
    ) -> None:
        """DISCRIMINATION: an answer is a message DELIVERED TO the asker. A
        build keyed on "any message on the thread after the question" lets the
        asker answer ITSELF — a follow-up nudge would clear its own debt.
        """
        await _ask(message_ledger, thread="q:cap-boundary")
        await message_ledger.send(
            sender=_ref(AGENT_FIXER_B),
            session=SESSION_WAVE7,
            body="bumping my own question",
            grade=_msg().MESSAGE_GRADE_SIGNAL,
            recipients=[_ref(SENDER_LEAD)],
            thread="q:cap-boundary",
        )
        assert await message_ledger.awaiting_answer(agent_id=AGENT_FIXER_B[0]) is not None

    async def test_a_message_that_PREDATES_the_question_is_not_an_answer(
        self, message_ledger: Any
    ) -> None:
        """DISCRIMINATION: a build testing only "does the thread carry traffic
        to me" ignores ORDER, and prior chatter on the thread would answer a
        question asked afterwards.
        """
        await _answer(message_ledger, thread="q:cap-boundary")
        await _ask(message_ledger, thread="q:cap-boundary")
        assert await message_ledger.awaiting_answer(agent_id=AGENT_FIXER_B[0]) is not None

    async def test_another_agents_question_never_makes_ME_wait(
        self, message_ledger: Any
    ) -> None:
        await _ask(message_ledger, thread="q:cap-boundary", asker=AGENT_FIXER_B)
        assert await message_ledger.awaiting_answer(agent_id=AGENT_AUDIT_C[0]) is None

    async def test_asked_at_IS_the_questions_own_created_at(
        self, message_ledger: Any
    ) -> None:
        """M6 — ``asked_at`` is the field a render will age ("waiting 40m"). A
        build fabricating it at READ time reports every debt as brand new, which
        is the opposite of the signal it exists to carry, and every other pin in
        this section passes.

        KILLS the adversary's W4.
        """
        sent = await message_ledger.send(
            sender=_ref(AGENT_FIXER_B),
            session=SESSION_WAVE7,
            body="which fixture value?",
            grade=_msg().MESSAGE_GRADE_SIGNAL,
            recipients=[_ref(SENDER_LEAD)],
            thread="q:cap-boundary",
            set_status="input_required",
        )
        await asyncio.sleep(0.05)
        waiting = await message_ledger.awaiting_answer(agent_id=AGENT_FIXER_B[0])
        assert waiting is not None
        assert waiting.asked_at == sent.message.created_at, (
            f"asked_at is not the QUESTION's created_at — it was fabricated at read "
            f"time ({waiting.asked_at} vs {sent.message.created_at}), so a 'waiting for N "
            f"minutes' render would always read zero"
        )

    async def test_the_OLDEST_unanswered_question_is_the_one_reported(
        self, message_ledger: Any
    ) -> None:
        """Two outstanding debts: the longest-standing one is the signal worth
        surfacing. A build returning the newest reports the least urgent.
        """
        first = await _ask(message_ledger, thread="q:first")
        await _ask(message_ledger, thread="q:second")
        waiting = await message_ledger.awaiting_answer(agent_id=AGENT_FIXER_B[0])
        assert waiting is not None
        assert waiting.question_seq == first

    async def test_answering_only_ONE_of_two_questions_leaves_the_other_outstanding(
        self, message_ledger: Any
    ) -> None:
        await _ask(message_ledger, thread="q:first")
        second = await _ask(message_ledger, thread="q:second")
        await _answer(message_ledger, thread="q:first")
        waiting = await message_ledger.awaiting_answer(agent_id=AGENT_FIXER_B[0])
        assert waiting is not None
        assert waiting.question_seq == second

    async def test_the_derivation_writes_NOTHING(self, message_ledger: Any) -> None:
        """The load-bearing structural property: ``orphaned``-style derivation
        means a READ. A build that stamps an ``agent`` column (or any row) on the
        way past has reintroduced the stored state ruling 9 struck, and with it
        the lost-update and forgot-to-clear failure modes.

        WHAT THIS ASSERTS, EXACTLY — because a failure message that promises a
        check the assertion does not perform is a FALSE GATE, and this pin WAS
        one (cold audit of packet 03a-2, §3.2): it promised "an ``agent`` column
        (or any row)" and asserted ``message``/``to`` ROW COUNTS, so three real
        writes — ``UPDATE agent SET status = 'input_required'`` (ruling 9's
        struck stored state, verbatim), ``UPDATE agent SET last_note = …``, and
        ``UPDATE to SET seen_at = …`` — each passed the whole ``[real]`` leg
        86/0. The three assertions below are the whole promise, and nothing more:

        1. **Every statement is an allowlisted READ.** Not "no new rows in two
           tables" — every statement ``awaiting_answer`` issues at the connection
           seam must be a single ``SELECT`` (:data:`_READ_ONLY_STATEMENT_HEADS`).
           Any other verb, against ANY table, including one no pin enumerates,
           fails here.
        2. **Nothing in the database changed.** Every table ``INFO FOR DB`` names,
           compared by full content. This closes leg 1's own door: a write
           smuggled inside a read (``SELECT * FROM (UPDATE …)``) is accepted by
           the engine and DOES write [PROBED 2026-07-23, spike-surreal 3.2.1].
        3. **The watch actually SAW the derivation.** A runtime gate is an
           invariant only over code it RUNS, so an empty write list is trusted
           only once the watch has observed the derivation's own reads —
           otherwise a build whose statements never reach this seam passes
           vacuously.

        ⚠ KNOWN BOUND, stated rather than implied: a write that is BOTH shaped as
        a ``SELECT`` and leaves every table byte-identical, or one issued on a
        connection obtained without going through ``_ensure_connection``, is not
        seen. The instrument's positive control is
        ``test_the_write_watch_SEES_a_real_write`` below — without it, "no writes"
        would be indistinguishable from a blind instrument.
        """
        if not _is_real(message_ledger):
            pytest.skip("statement-seam and raw-content observation is a REAL-backend observation")
        await _ask(message_ledger, thread="q:cap-boundary")
        before = await _database_snapshot(message_ledger)
        async with _WriteWatch(message_ledger) as watch:
            for _ in range(3):
                await message_ledger.awaiting_answer(agent_id=AGENT_FIXER_B[0])
        after = await _database_snapshot(message_ledger)
        assert watch.reads, (
            "the write watch observed NO statement at all — it is detached from the seam "
            "the derivation actually uses, so an empty write list below would be vacuous"
        )
        assert watch.writes == [], (
            f"the derivation issued {len(watch.writes)} statement(s) that are not "
            f"allowlisted reads: {watch.writes} — ruling 9's derivation is a pure READ, "
            f"and a stamp on ANY table (an `agent` column, another agent's `to` edge, a "
            f"table this file never names) reintroduces the stored state it struck"
        )
        assert after == before, (
            "the database CONTENT changed across the derivation even though every "
            "statement looked like a read — a write was smuggled inside one (a subquery "
            "write is legal SurrealQL and does land), so the derivation is not pure"
        )

    async def test_the_write_watch_SEES_a_real_write(self, message_ledger: Any) -> None:
        """POSITIVE CONTROL for the pin above — a probe needs a control, and the
        instrument that pin depends on is itself the thing most worth doubting
        (the row-count instrument it replaced returned a clean negative for three
        real writes).

        A non-``peek`` ``drain`` genuinely stamps ``seen_at``. BOTH legs of the
        pin above must fire on it: a non-read statement at the connection seam,
        AND a moved content snapshot. If either stays silent here, the negative
        above is a blind instrument rather than a real negative.
        """
        if not _is_real(message_ledger):
            pytest.skip("statement-seam and raw-content observation is a REAL-backend observation")
        await _ask(message_ledger, thread="q:cap-boundary")
        before = await _database_snapshot(message_ledger)
        async with _WriteWatch(message_ledger) as watch:
            await message_ledger.drain(agent_id=SENDER_LEAD[0], limit=20)
        after = await _database_snapshot(message_ledger)
        assert watch.writes, (
            f"a stamping drain issued no statement the watch classified as a write — the "
            f"statement-seam leg cannot see writes at all; observed: {watch.statements}"
        )
        assert after != before, (
            "a stamping drain left the content snapshot unchanged — the snapshot leg "
            "cannot see writes at all, so its use as a gate above is theatre"
        )

    async def test_draining_does_not_change_the_derived_state(
        self, message_ledger: Any
    ) -> None:
        """RULING 9 explicitly: NOTHING un-parks an agent — least of all a
        drain, which clears the signal on NO INFORMATION ("the answer hasn't
        come" and "the answer was lost" are the same observation). A build
        carrying the struck design sentence fails here.
        """
        await _ask(message_ledger, thread="q:cap-boundary")
        await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=20)
        assert await message_ledger.awaiting_answer(agent_id=AGENT_FIXER_B[0]) is not None, (
            "a drain cleared the derived waiting state — that is the struck "
            "'drain un-parks' branch, reintroduced"
        )

    async def test_draining_the_ANSWER_does_clear_it(
        self, message_ledger: Any
    ) -> None:
        """POSITIVE CONTROL for the pin above: it must not be passing because
        the derivation is simply stuck at "waiting" forever. The same drain
        call, with an answer present, clears it.
        """
        await _ask(message_ledger, thread="q:cap-boundary")
        await _answer(message_ledger, thread="q:cap-boundary")
        await message_ledger.drain(agent_id=AGENT_FIXER_B[0], limit=20)
        assert await message_ledger.awaiting_answer(agent_id=AGENT_FIXER_B[0]) is None


class TestTheDerivedWaitingStateKnownBound:
    """PIN THE MISS (repo law: an unpinned known limitation is
    indistinguishable from an unknown one, and the next engineer either
    rediscovers it from an incident or "helpfully" closes it and re-opens a
    settled trade).

    THE BOUND, named in ruling 9 and accepted with it: an answer that arrives
    OUT-OF-BAND — an operator replying in a terminal rather than through
    ``lore_comms`` — never lands on the thread, so the derived state stays
    "waiting" until someone relays it in. That is the deliberate cost of not
    storing the state, and it is the SAFE direction of error: a false-waiting
    is visible beside a fresh ``heartbeat_at``; a false-not-waiting is
    invisible. The asymmetry is the whole argument.

    RE-OPEN TRIGGER: the day an out-of-band reply path exists that CAN write to
    the thread (an operator CLI that posts through the ledger, or packet 05's
    ``await``/``story`` gaining a relay verb), this bound must be closed —
    delete this pin and say so. Until then it is a KNOWN BOUND (#NNN, ruling 9),
    not an oversight.
    """

    async def test_KNOWN_BOUND_an_out_of_band_answer_leaves_the_state_waiting(
        self, message_ledger: Any
    ) -> None:
        await _ask(message_ledger, thread="q:cap-boundary")
        # The operator answers in a terminal. Nothing reaches the ledger. The
        # ONLY honest thing the derivation can report is the debt it can see.
        waiting = await message_ledger.awaiting_answer(agent_id=AGENT_FIXER_B[0])
        assert waiting is not None, (
            "the derived waiting state cleared with no answer on the thread — if you "
            "CLOSED this known bound deliberately (a relay path now writes out-of-band "
            "replies to the thread), delete this pin and say so"
        )

    async def test_the_bound_closes_the_moment_the_answer_IS_relayed(
        self, message_ledger: Any
    ) -> None:
        """The bound's own escape hatch, pinned so the remedy is discoverable:
        relaying the out-of-band answer through the ledger clears it normally.
        This is what "until relayed" means, executable.
        """
        await _ask(message_ledger, thread="q:cap-boundary")
        await _answer(message_ledger, thread="q:cap-boundary")
        assert await message_ledger.awaiting_answer(agent_id=AGENT_FIXER_B[0]) is None


class TestAgentRefLikeHasONEHome:
    """OPERATOR-RULED 2026-07-19 (DRY law): ``AgentRefLike`` is promoted to ONE
    shared module that BOTH ``briefs.py`` and ``messages.py`` import. Copy #2 of
    a Protocol is still copy #2, and duplication is a DESIGN decision.

    Pinned STRUCTURALLY rather than by filename, so the contract does not
    dictate where the shared home lives — only that there is exactly one.
    """

    def test_briefs_and_messages_expose_the_SAME_object(self) -> None:
        from loremaster.briefs import AgentRefLike as BriefAgentRefLike

        assert _msg().AgentRefLike is BriefAgentRefLike, (
            "briefs.AgentRefLike and messages.AgentRefLike are DIFFERENT objects — that is "
            "copy #2 of a Protocol wearing one name. Promote it to a shared module both "
            "import (operator ruling, 2026-07-19)."
        )

    def test_the_shared_home_is_neither_ledger_module(self) -> None:
        assert _msg().AgentRefLike.__module__ not in {
            "loremaster.briefs",
            "loremaster.messages",
        }, (
            f"AgentRefLike is DEFINED in {_msg().AgentRefLike.__module__} — a ledger owning "
            f"the shared Protocol makes its sibling import it, which is the coupling the "
            f"briefs decoupling law (briefs.py:79-89) exists to prevent"
        )
