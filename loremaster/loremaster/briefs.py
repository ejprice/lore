"""The durable, versioned BRIEF LEDGER (PKT-28 C1 agent-comms — seam S2).

:class:`BriefLedger` is the standing-instruction primitive every
``lore_comms`` brief action rides: race-safe max+1 versioning
(:meth:`~BriefLedger.publish`), head/exact-version reads
(:meth:`~BriefLedger.get_head` / :meth:`~BriefLedger.get_version`), the
idempotent ack edge (:meth:`~BriefLedger.ack`), and the coverage/skew query
(:meth:`~BriefLedger.coverage`). It rides the SAME store machinery the rest of
the layer uses (:mod:`loremaster.tasks`/:mod:`loremaster.findings`):

* one lazily-opened, signed-in WS connection, self-healed on a mid-life
  transport failure, reusing the shared error-classification seam in
  :mod:`loremaster.store._txn` — a transport fault surfaces as
  :class:`~loremaster.store._txn.SurrealConnectionError`, a domain rejection as
  :class:`~loremaster.store._txn.SurrealStoreError`, never a raw engine string;
* :func:`~loremaster.store._txn.execute_transaction` /
  :func:`~loremaster.store._txn.compose` apply the ``brief`` + ``briefed``
  schema slice (:func:`~loremaster.store.surreal_schema.generate_brief_ddl`) at
  :meth:`~BriefLedger.ensure_ready` and every atomic publish write, verifying
  EVERY statement's status.

Binding spec: ``docs/design/2026-07-12-pkt28-c1-semantics.md`` §0, §5, §7-§8.
The public surface below is the contract test's own pinned API
(``REPORT-c1-contract-ledgers.md`` §"Exact public API surface") — this module
implements it, never redefines it:

    Brief:                                  # a value object (pydantic model)
        id: str                             # opaque hex — uuid5(name:version)
        name: str
        version: int
        body: str                           # RAW, never sanitised in storage
        created_by: str
        note: str | None
        created_at: datetime                # tz-aware UTC

    BriefPublishResult:
        brief: Brief
        first_version: bool

    BriefAckResult:
        name: str
        version: int                        # the version the caller targeted
        head_version: int                   # head AT THE TIME of this ack
        already_acked: bool                 # True on an idempotent re-ack no-op
        via: Literal["register", "explicit"]

    BriefBehindEntry:
        agent_name: str
        acked_version: int | None           # None = unbriefed

    BriefCoverage:
        name: str
        head_version: int
        total_agents: int
        current_count: int                  # agents AT head
        behind: list[BriefBehindEntry]      # NOT capped here — capping is a render (S3) concern

    AgentRefLike(Protocol):                 # the roster item coverage() accepts
        id: str
        name: str

    BriefLedger(*, url, namespace, database, user, password):
        async ensure_ready() -> None
        async close() -> None
        async publish(name, body, *, created_by, note=None) -> BriefPublishResult
        async get_head(name) -> Brief
        async get_version(name, version) -> Brief
        async known_names() -> list[str]
        async ack(*, agent_id, agent_name, name, version, via) -> BriefAckResult
        async acked_version(*, agent_id, name) -> int | None
        async acked_versions_for_ids(agent_ids, *, name) -> dict[str, int]
        async coverage(name, *, active_agents) -> BriefCoverage

    Exceptions: BriefLedgerError(RuntimeError);
                UnknownBriefError(BriefLedgerError);
                UnknownBriefVersionError(BriefLedgerError).

Deliberate design decoupling (``REPORT-c1-contract-ledgers.md`` contract
decision 1): :meth:`~BriefLedger.coverage`/:meth:`~BriefLedger.ack` accept an
externally-resolved agent identity (``agent_id``/``agent_name``, or an
``AgentRefLike`` roster) rather than querying the ``agent`` table directly —
mirrors :meth:`~loremaster.tasks.TaskLedger.create_many`'s "the ledger stays
key-agnostic" idiom. This module NEVER imports :mod:`loremaster.agents`; the
caller (S3's dispatcher, backed by ``AgentRegistry.fleet()``) resolves the
roster.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal, Protocol, cast
from uuid import NAMESPACE_URL, uuid4, uuid5

from pydantic import BaseModel, ConfigDict
from surrealdb import AsyncSurreal, RecordID

from loremaster.store._txn import (
    _CONNECTION_ERRORS,
    _ERROR_CLASS_RETRYABLE_CONFLICT,
    _MAX_TXN_CONFLICT_ATTEMPTS,
    _SERVER_LOG_HINT,
    SurrealConnectionError,
    SurrealStoreError,
    TxnFragment,
    _classify_engine_error,
    _SurrealConnection,
    compose,
    execute_transaction,
    is_connection_error,
)
from loremaster.store.surreal_schema import (
    AGENT_TABLE,
    BRIEF_COUNTER_TABLE,
    BRIEF_TABLE,
    BRIEFED_RELATION,
    generate_brief_ddl,
)

logger = logging.getLogger(__name__)

# The ``briefed.via`` wire vocabulary this contract decides — a ``Literal``
# alias so :class:`BriefAckResult.via` is typed against the closed two-value
# set (mirrors ``loremaster.agents.AgentStatus``).
BriefAckVia = Literal["register", "explicit"]

# Protocol vocabulary (design doc §4) — NOT tunables: C4's brief-base v3
# hardcodes the same words, so these stay module constants, never config.
BRIEF_NAME_PROJECT = "project"
BRIEF_NAME_BASE = "base"

# The teaching-error known-names cap (design doc §4/§7; v4 audit D2 fix):
# ``_unknown_brief_error``'s "some briefs published" clause dumped an
# UNBOUNDED, uncounted ``', '.join(known)`` — the same context-blowout class
# the render caps exist to prevent elsewhere. Lives HERE, not in server.py
# (despite the spec table's literal "(server.py)" placement), because
# server.py imports FROM briefs.py — the reverse would be a circular import —
# and this file already pins that the ledger's own raised message embeds the
# known names directly (see ``TestGetHeadAndVersionMisses``), so there is no
# "extra query" a server-side enrichment split would avoid.
_KNOWN_BRIEFS_CAP = 10

# The publish-retry mechanism's module constants (design doc §4/§5.1) — a
# concurrency-MECHANISM tuning knob, the exact class ``findings.py`` keeps as
# module constants (``_REPORT_MINT_*``); operators tune behaviour via config,
# never retry mechanics. Budget 4 (not findings' 12): publish contention is
# lead-shaped (rare, at most a handful of concurrent publishers), unlike the
# N-way finding mint.
_BRIEF_PUBLISH_MAX_ATTEMPTS = 4
_BRIEF_PUBLISH_BACKOFF_SECONDS = 0.01
_BRIEF_PUBLISH_JITTER_SLOTS = 4
_BRIEF_PUBLISH_JITTER_SECONDS = 0.001

# The mint's TOTAL engine-attempt ceiling — the design doc's OWN stated worst
# case, verbatim (§5.1: "the worst case is attempts × shared-txn-retries = 4×5
# transaction attempts, bounded"). Every OTHER ledger write reaches that product
# implicitly: it rides :func:`~loremaster.store._txn.execute_transaction`, whose
# internal loop already absorbs :data:`_MAX_TXN_CONFLICT_ATTEMPTS` retryable
# conflicts per app-level attempt. The version mint CANNOT ride it —
# ``execute_transaction`` returns ``None`` by design, and the mint's whole
# purpose is to RETURN the version it minted — so it runs on the single-statement
# ``_query`` seam and must therefore absorb the engine-level conflict budget
# ITSELF. Composed from the two shared constants rather than a fresh magic
# number, so it can never drift from the seam it is standing in for. Measured
# (see ``REPORT-c1-builder-mint.md``): at the contract's 8-way contention a bare
# 4-attempt budget exhausts its last attempt roughly 1 mint in 240 — this
# product carries a ~5× margin instead.
_BRIEF_MINT_MAX_ATTEMPTS = _BRIEF_PUBLISH_MAX_ATTEMPTS * _MAX_TXN_CONFLICT_ATTEMPTS

# The per-name version counter's table and column. The ``brief`` table's
# UNIQUE(name, version) index remains the BACKSTOP under this mint (belt and
# braces), never its mechanism. ``BRIEF_COUNTER_TABLE`` is DECLARED in
# ``generate_brief_ddl()`` (:func:`~loremaster.store.surreal_schema._brief_counter_statements`)
# alongside ``brief``/``briefed`` — imported, never redefined, so this module
# can never drift from the DDL it applies at :meth:`BriefLedger.ensure_ready`.
_COL_NEXT = "next"

# The ``brief`` / ``briefed`` table columns the ledger reads/writes. Named
# once each so a rename is a single edit (mirrors ``loremaster.tasks``'s
# ``_COL_*`` idiom).
_COL_NAME = "name"
_COL_VERSION = "version"
_COL_BODY = "body"
_COL_CREATED_BY = "created_by"
_COL_NOTE = "note"
_COL_CREATED_AT = "created_at"
_COL_VIA = "via"
_COL_AT = "at"
_COL_EDGE_IN = "in"
_COL_EDGE_OUT = "out"

# The signin credential keys the SDK expects, and the record-id table separator.
_SIGNIN_USER_KEY = "username"
_SIGNIN_PASS_KEY = "password"
_TABLE_SEPARATOR = ":"
_ID_KEY = "id"

# Bound-parameter names for the single-row lookups/writes below.
_ROW_ID_PARAM = "id"
_NAME_LOOKUP_PARAM = "name"
_MINT_NAME_PARAM = "mint_name"
_MINT_VERSION_PARAM = "mint_version"
_PUB_ID_PARAM = "pub_id"
_PUB_NAME_PARAM = "pub_name"
_PUB_VERSION_PARAM = "pub_version"
_PUB_BODY_PARAM = "pub_body"
_PUB_CREATED_BY_PARAM = "pub_created_by"
_PUB_NOTE_PARAM = "pub_note"
_ACK_FROM_PARAM = "ack_from"
_ACK_TO_PARAM = "ack_to"
_ACK_VIA_PARAM = "ack_via"
_ACK_AT_PARAM = "ack_at"
_EDGE_IN_PARAM = "edge_in"
_EDGE_OUT_PARAM = "edge_out"
_ACKED_IN_PARAM = "acked_in"
_COVERAGE_ROSTER_PARAM = "coverage_roster_ids"


class AgentRefLike(Protocol):
    """The structural shape :meth:`BriefLedger.coverage` accepts per roster item.

    Matches an :class:`~loremaster.agents.Agent` STRUCTURALLY, never
    nominally — this module never imports :mod:`loremaster.agents` (see the
    module docstring's decoupling note). Declared as READ-ONLY properties
    (rather than plain mutable attributes) so a frozen/immutable duck-typed
    caller-supplied stand-in (e.g. a contract test's ``@dataclass(frozen=True)``
    roster item) structurally satisfies this Protocol — mypy treats a plain
    attribute Protocol member as requiring a SETTABLE variable, which a frozen
    dataclass field is not; ``coverage`` only ever READS ``.id``/``.name``, so
    the narrower read-only shape is the correct (and more permissive) contract.
    """

    @property
    def id(self) -> str: ...

    @property
    def name(self) -> str: ...


@dataclass(frozen=True)
class _BareAgentRef:
    """Minimal :class:`AgentRefLike` wrapping a bare agent id.

    :meth:`BriefLedger.acked_versions_for_ids` callers (the ``fleet`` action)
    hold only ids, no separate display name, at that call site — ``name``
    aliases ``id`` since :meth:`BriefLedger._acked_versions_for_roster` never
    reads it (only ``coverage``'s ``behind`` sort does, and this type never
    reaches that path).
    """

    id: str

    @property
    def name(self) -> str:
        return self.id


class Brief(BaseModel):
    """A single published brief VERSION in the durable brief ledger.

    Attributes:
        id: The brief's OPAQUE, hashable string id — a deterministic
            ``uuid5(name, version)`` hex digest, never a raw SurrealDB
            ``RecordID``.
        name: The brief's name (protocol vocabulary, e.g. ``"project"``).
        version: The 1-based, gapless version number within ``name``.
        body: The RAW brief text — never sanitised in storage; sanitisation
            is a render-time concern (design doc §5.2).
        created_by: The identity that published this version.
        note: An optional free-text publish note, or ``None``.
        created_at: The tz-aware UTC timestamp this version was published.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    version: int
    body: str
    created_by: str
    note: str | None = None
    created_at: datetime


class BriefPublishResult(BaseModel):
    """The outcome of a :meth:`BriefLedger.publish` call.

    Attributes:
        brief: The freshly-published version.
        first_version: ``True`` when this call minted v1 of ``name``.
    """

    model_config = ConfigDict(extra="forbid")

    brief: Brief
    first_version: bool


class BriefAckResult(BaseModel):
    """The outcome of a :meth:`BriefLedger.ack` call.

    Attributes:
        name: The brief name acked.
        version: The version the caller targeted.
        head_version: The head version AT THE TIME of this ack.
        already_acked: ``True`` on an idempotent re-ack no-op (the same
            (agent, name@version) pair was already acked).
        via: How the FIRST ack of this pair was recorded — first-write-wins,
            so a re-ack via a different route never overwrites it.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    version: int
    head_version: int
    already_acked: bool
    via: BriefAckVia


class BriefBehindEntry(BaseModel):
    """One agent's coverage standing inside a :class:`BriefCoverage` listing.

    Attributes:
        agent_name: The behind (or unbriefed) agent's name.
        acked_version: The max version this agent has acked, or ``None`` when
            it has never acked any version of this brief name (unbriefed).
    """

    model_config = ConfigDict(extra="forbid")

    agent_name: str
    acked_version: int | None


class BriefCoverage(BaseModel):
    """The coverage/skew standing for one brief name across a roster.

    Attributes:
        name: The brief name.
        head_version: The current head version.
        total_agents: The size of the roster this coverage was computed over.
        current_count: How many roster agents are AT head.
        behind: Every roster agent NOT at head (behind or unbriefed) — NOT
            capped here; capping is a render (S3) concern.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    head_version: int
    total_agents: int
    current_count: int
    behind: list[BriefBehindEntry]


class BriefLedgerError(RuntimeError):
    """Base class for every error :class:`BriefLedger` raises."""


class UnknownBriefError(BriefLedgerError):
    """Raised when a brief ``name`` has no published version at all."""


class UnknownBriefVersionError(BriefLedgerError):
    """Raised when a brief ``name`` exists but not at the requested ``version``."""


class BriefLedger:
    """Durable, versioned brief ledger over a single SurrealDB database.

    Owns BOTH the ``brief`` node table and the ``briefed`` relation edge
    (mirrors :class:`~loremaster.findings.FindingLedger` bundling ``finding``
    + ``finding_counter``). Mints deterministic ``uuid5(name, version)`` ids,
    a race-safe max+1 version mint under the shared hot-row law, and rides the
    shared :mod:`loremaster.store._txn` error-classification seam so every
    failure surfaces as a typed store error.

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

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
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
                await connection.query(f"DEFINE NAMESPACE IF NOT EXISTS {self._namespace}")
                await connection.use(self._namespace, self._database)
                await connection.query(f"DEFINE DATABASE IF NOT EXISTS {self._database}")
            except _CONNECTION_ERRORS as error:
                await self._safe_close(connection)
                raise SurrealConnectionError(
                    f"could not connect to SurrealDB at {self._url!r} "
                    f"(namespace={self._namespace!r}, database={self._database!r}): {error}"
                ) from error
            self._connection = connection
            logger.debug(
                "brief.connected",
                extra={"namespace": self._namespace, "database": self._database},
            )
            return connection

    async def ensure_ready(self) -> None:
        """Connect and apply the brief + briefed schema slice — idempotent.

        Applies :func:`~loremaster.store.surreal_schema.generate_brief_ddl`
        inside ONE ``BEGIN … COMMIT`` via
        :func:`~loremaster.store._txn.execute_transaction`.

        Raises:
            SurrealConnectionError: The server is unreachable or the socket died.
            SurrealStoreError: A DDL statement was rejected by the engine.
        """
        await self._ensure_connection()
        ddl = generate_brief_ddl()
        await execute_transaction(
            f"BEGIN;\n{ddl}COMMIT;\n",
            {},
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )
        logger.debug("brief.schema.ready", extra={"database": self._database})

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
            logger.debug("brief.close.already_closed")

    async def _query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        """Run a single statement on the (lazily opened) connection, self-healing.

        Mirrors :meth:`~loremaster.agents.AgentRegistry._query` /
        :meth:`~loremaster.tasks.TaskLedger._query` exactly.
        """
        connection = await self._ensure_connection()
        try:
            return await connection.query(statement, params or {})
        except (*_CONNECTION_ERRORS, KeyError) as error:
            if isinstance(error, KeyError) or is_connection_error(error):
                await self._drop_connection(connection)
                raise SurrealConnectionError(
                    f"SurrealDB brief query failed against {self._url!r}: {error}"
                ) from error
            error_class = _classify_engine_error(error)
            logger.error(
                "brief.query.rejected",
                extra={"url": self._url, "error_class": error_class, "engine_error": str(error)},
            )
            raise SurrealStoreError(
                f"SurrealDB brief query rejected against {self._url!r} ({error_class}); "
                f"{_SERVER_LOG_HINT}"
            ) from error

    async def _apply(self, fragments: list[TxnFragment]) -> None:
        """Compose ``fragments`` into ONE transaction and run it atomically.

        Mirrors :meth:`~loremaster.tasks.TaskLedger._apply`.
        """
        statement_text, merged_params = compose(*fragments)
        await execute_transaction(
            statement_text,
            merged_params,
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )

    # -- id ---------------------------------------------------------------------

    @staticmethod
    def _brief_id(name: str, version: int) -> str:
        """The design doc's pinned id recipe: ``uuid5(name, version)`` hex."""
        return uuid5(NAMESPACE_URL, f"lore://brief/{name}/{version}").hex

    # -- publish ------------------------------------------------------------

    async def publish(
        self, name: str, body: str, *, created_by: str, note: str | None = None
    ) -> BriefPublishResult:
        """Publish a new version of ``name`` under the max+1 hot-row law (§5.1).

        Concurrent publishes of the SAME name are NOT an error: each racer first
        mints its OWN version atomically off the per-name ``brief_counter`` hot
        row (:meth:`_mint_version`), so no two racers ever hold the same version
        — and therefore never race to CREATE the same deterministic
        ``uuid5(name, version)`` id at all. The CREATE that follows is
        collision-FREE by construction, and the ``brief`` table's
        UNIQUE(name, version) index stands behind it as the backstop (§5.1's
        second guard), never as the mechanism.

        This is :meth:`~loremaster.findings.FindingLedger._apply_mint`'s
        counter-row UPSERT, cloned in MECHANISM and not merely in shape: the
        engine — not a re-read — is what hands out distinct consecutive numbers,
        so contention costs a retry on the counter, never a lost publish. The
        single deviation from findings is forced by the pinned id recipe
        (``uuid5(name, version)``, §0): findings mints its number INSIDE the same
        transaction as the row CREATE because a finding's id does not depend on
        it, whereas a brief's id DOES — Python cannot address the row until it
        knows the version — so the mint is its own statement and the CREATE
        follows it. :meth:`_release_version` closes the gap that split opens.

        Args:
            name: The brief name to publish under.
            body: The RAW brief text (stored verbatim; blank bodies are
                rejected by the schema's non-empty ASSERT, not here).
            created_by: The identity publishing this version.
            note: An optional free-text publish note.

        Returns:
            The :class:`BriefPublishResult` of this call.

        Raises:
            SurrealConnectionError: A transport fault.
            SurrealStoreError: The engine rejected the write (e.g. the blank-body
                ASSERT). Such a rejection is NEVER retried — only a classified
                retryable conflict on the counter row is (:meth:`_mint_version`).
        """
        version = await self._mint_version(name)
        brief_id = self._brief_id(name, version)
        fragment = self._publish_fragment(brief_id, name, version, body, created_by, note)
        try:
            await self._apply([fragment])
        except SurrealStoreError:
            # The version is minted but its row was REJECTED (a blank body, a bad
            # ``created_by`` — a caller error, deterministic, and never a race).
            # Hand the number back so a rejected publish does not burn a version,
            # then let the rejection propagate UNTOUCHED and LOUD.
            await self._release_version(name, version)
            raise
        row = await self._select_row(brief_id)
        if row is None:
            raise BriefLedgerError(f"brief {brief_id!r} vanished immediately after it was created")
        return BriefPublishResult(brief=self._row_to_brief(row), first_version=version == 1)

    async def _mint_version(self, name: str) -> int:
        """Atomically mint the next version of ``name`` off its counter hot row.

        ONE statement: ``UPSERT brief_counter:⟨name⟩ SET next = (next ?? 0) + 1
        RETURN AFTER``. Every concurrent publisher of ``name`` contends on this
        ONE row, and the engine serialises them into distinct, gapless,
        consecutive numbers — the same race-safe primitive
        :meth:`~loremaster.findings.FindingLedger._apply_mint` rides. The
        ``?? 0`` coalesce and the DDL's declared ``DEFAULT 0`` (see
        :data:`~loremaster.store.surreal_schema.BRIEF_COUNTER_TABLE`) BOTH make
        the FIRST bump on a brand-new per-name row yield 1 — belt and braces,
        matching ``finding_counter``'s own ``DEFAULT 0``. Publishers of
        DIFFERENT names touch DIFFERENT counter rows and so never contend with
        each other.

        The engine's answer to a genuine collision here is a RETRYABLE conflict
        ("this transaction can be retried" — the shared seam's classified
        :data:`~loremaster.store._txn._ERROR_CLASS_RETRYABLE_CONFLICT` label),
        and re-running the bump is always safe: a conflicted UPSERT committed
        NOTHING, so the retry re-reads the winner's settled counter and takes the
        NEXT number. That label — and ONLY that label — is retried, the
        ``_apply_mint`` posture verbatim: a transport fault and EVERY other
        rejection (an ASSERT violation, a coercion failure, a malformed body)
        propagate on the FIRST occurrence, because retrying them would never
        succeed and swallowing them would turn a loud failure into a silent wrong
        answer.

        Returns:
            The version this publisher — and no other — now owns.

        Raises:
            SurrealConnectionError: A transport fault — never retried here.
            SurrealStoreError: A non-conflict rejection (raised immediately), or
                sustained contention that exhausted :data:`_BRIEF_MINT_MAX_ATTEMPTS`.
        """
        # The jitter slot must be unique per RACER, so colliding publishers wake
        # on DIFFERENT ticks and do not re-collide in lockstep. It therefore
        # CANNOT be derived from the brief id the way findings derives its slot
        # from ``finding_id``: a finding id is unique per reporter, but
        # ``uuid5(name, version)`` is by construction IDENTICAL for every racer
        # contending for the same version — deriving the slot from it would hand
        # every racer the same sleep and de-synchronise nothing (the exact defect
        # this mint replaces). A per-publish nonce restores the property findings
        # gets for free.
        jitter_slot = int(uuid4().hex[:4], 16) % _BRIEF_PUBLISH_JITTER_SLOTS
        bump = (
            f"UPSERT type::record('{BRIEF_COUNTER_TABLE}', ${_MINT_NAME_PARAM}) "
            f"SET {_COL_NEXT} = ({_COL_NEXT} ?? 0) + 1 RETURN AFTER"
        )
        for attempt in range(_BRIEF_MINT_MAX_ATTEMPTS):
            try:
                rows = self._as_rows(await self._query(bump, {_MINT_NAME_PARAM: name}))
            except SurrealConnectionError:
                # A genuine transport fault — never a lost race; propagate untouched.
                raise
            except SurrealStoreError as error:
                last_attempt = attempt >= _BRIEF_MINT_MAX_ATTEMPTS - 1
                if last_attempt or _ERROR_CLASS_RETRYABLE_CONFLICT not in str(error):
                    raise
                backoff = _BRIEF_PUBLISH_BACKOFF_SECONDS * (attempt + 1)
                jitter = jitter_slot * _BRIEF_PUBLISH_JITTER_SECONDS
                await asyncio.sleep(backoff + jitter)
                continue
            if not rows or _COL_NEXT not in rows[0]:
                raise BriefLedgerError(
                    f"the version counter for brief {name!r} returned no minted version"
                )
            return int(rows[0][_COL_NEXT])
        # Unreachable: the final iteration always returns or raises above.
        raise BriefLedgerError(
            f"failed to mint a version for brief {name!r} after {_BRIEF_MINT_MAX_ATTEMPTS} attempts"
        )

    async def _release_version(self, name: str, version: int) -> None:
        """Hand a minted-but-unused ``version`` back, so a REJECTED publish
        burns no version number (versions stay gapless).

        The compensating half of the mint/CREATE split :meth:`publish` is forced
        into by the version-dependent id recipe. Guarded and therefore race-safe:
        the decrement applies ONLY while the counter still stands at the number
        this publisher minted (``WHERE next = $version``), so a racer that has
        already taken the NEXT number makes this a no-op rather than a
        double-hand-out — the guard, not luck, is what keeps two publishers from
        ever holding the same version.

        BEST-EFFORT by design: this runs on a path where the caller's publish has
        ALREADY failed and is about to raise. A failure to hand the number back
        is logged and swallowed so it can never mask the REAL rejection the
        caller must see (the worst case is a skipped version number — cosmetic —
        never a lost or duplicated one). A transport fault is swallowed for the
        same reason; the original error still propagates.
        """
        try:
            await self._query(
                f"UPDATE type::record('{BRIEF_COUNTER_TABLE}', ${_MINT_NAME_PARAM}) "
                f"SET {_COL_NEXT} -= 1 WHERE {_COL_NEXT} = ${_MINT_VERSION_PARAM}",
                {_MINT_NAME_PARAM: name, _MINT_VERSION_PARAM: version},
            )
        except SurrealStoreError:
            logger.warning(
                "brief.publish.version_not_released",
                extra={"brief_name": name, "version": version},
            )

    @staticmethod
    def _publish_fragment(
        brief_id: str,
        name: str,
        version: int,
        body: str,
        created_by: str,
        note: str | None,
    ) -> TxnFragment:
        """The single-statement CREATE fragment for one publish attempt.

        ``created_at`` is deliberately OMITTED from the CONTENT object so the
        schema's own ``DEFAULT time::now()`` stamps it (mirrors
        ``test_surreal_schema.py``'s snapshot-metadata-omission idiom).
        """
        content_fields = [
            f"{_COL_NAME}: ${_PUB_NAME_PARAM}",
            f"{_COL_VERSION}: ${_PUB_VERSION_PARAM}",
            f"{_COL_BODY}: ${_PUB_BODY_PARAM}",
            f"{_COL_CREATED_BY}: ${_PUB_CREATED_BY_PARAM}",
        ]
        params: dict[str, Any] = {
            _PUB_ID_PARAM: brief_id,
            _PUB_NAME_PARAM: name,
            _PUB_VERSION_PARAM: version,
            _PUB_BODY_PARAM: body,
            _PUB_CREATED_BY_PARAM: created_by,
        }
        if note is not None:
            content_fields.append(f"{_COL_NOTE}: ${_PUB_NOTE_PARAM}")
            params[_PUB_NOTE_PARAM] = note
        else:
            content_fields.append(f"{_COL_NOTE}: NONE")
        create = (
            f"CREATE type::record('{BRIEF_TABLE}', ${_PUB_ID_PARAM}) "
            f"CONTENT {{ {', '.join(content_fields)} }}"
        )
        return TxnFragment(statements=[create], params=params)

    # -- read -------------------------------------------------------------

    async def get_head(self, name: str) -> Brief:
        """Fetch the head (max-version) row of ``name``.

        Raises:
            UnknownBriefError: ``name`` has no published version.
        """
        rows = self._as_rows(
            await self._query(
                f"SELECT * FROM {BRIEF_TABLE} WHERE {_COL_NAME} = ${_NAME_LOOKUP_PARAM} "
                f"ORDER BY {_COL_VERSION} DESC LIMIT 1",
                {_NAME_LOOKUP_PARAM: name},
            )
        )
        if not rows:
            raise await self._unknown_brief_error(name)
        return self._row_to_brief(rows[0])

    async def get_version(self, name: str, version: int) -> Brief:
        """Fetch an exact ``(name, version)`` row.

        Raises:
            UnknownBriefError: ``name`` has no published version at all.
            UnknownBriefVersionError: ``name`` exists but not at ``version``;
                names the real head.
        """
        versions = self._as_rows(
            await self._query(
                f"SELECT * FROM {BRIEF_TABLE} WHERE {_COL_NAME} = ${_NAME_LOOKUP_PARAM}",
                {_NAME_LOOKUP_PARAM: name},
            )
        )
        if not versions:
            raise await self._unknown_brief_error(name)
        for row in versions:
            if int(row[_COL_VERSION]) == version:
                return self._row_to_brief(row)
        head_version = max(int(row[_COL_VERSION]) for row in versions)
        raise UnknownBriefVersionError(f"brief {name!r} has no v{version} — head is v{head_version}")

    async def known_names(self) -> list[str]:
        """Every distinct published brief name, sorted."""
        rows = self._as_rows(await self._query(f"SELECT {_COL_NAME} FROM {BRIEF_TABLE}"))
        return sorted({str(row[_COL_NAME]) for row in rows})

    async def _unknown_brief_error(self, name: str) -> UnknownBriefError:
        """Build the teaching :class:`UnknownBriefError` for ``name`` (§5.4/§7).

        The "some briefs published" branch caps + counts the known-names
        clause at :data:`_KNOWN_BRIEFS_CAP` (v4 audit D2 fix) — sorted,
        sliced, with a ``(+K more)`` counter appended ONLY when the
        remainder is > 0. The "no briefs published yet" branch is
        untouched — there is no list to cap.
        """
        known = await self.known_names()
        if not known:
            return UnknownBriefError(
                f"no briefs published yet — lore_comms action=brief_publish creates {name!r} v1"
            )
        shown = known[:_KNOWN_BRIEFS_CAP]
        remainder = len(known) - len(shown)
        names_text = ", ".join(shown)
        if remainder > 0:
            names_text = f"{names_text} (+{remainder} more)"
        return UnknownBriefError(f"unknown brief {name!r}; known briefs: {names_text}")

    # -- ack ---------------------------------------------------------------

    async def ack(
        self,
        *,
        agent_id: str,
        agent_name: str,
        name: str,
        version: int,
        via: str,
    ) -> BriefAckResult:
        """Record that ``agent_id`` has read ``name`` at ``version`` (§5.4).

        Legal for ANY existing version, not just head — the ledger records the
        truth of what the agent actually read; forcing head-only acks would
        falsify the ledger. Idempotent: re-acking an already-acked
        (agent, name@version) pair is a no-op via the ``briefed``
        UNIQUE(in, out) index, reported back as ``already_acked=True`` with
        the FIRST-recorded ``via`` (first-write-wins).

        Args:
            agent_id: The acking agent's opaque id (caller-resolved — this
                ledger never queries the ``agent`` table itself).
            agent_name: The acking agent's name (carried through only for
                symmetry with the caller's roster; not stored on the edge).
            name: The brief name.
            version: The version being acked.
            via: How this ack is being recorded (``"register"`` or
                ``"explicit"``) — a raw ``str`` (mirrors
                ``AgentRegistry.touch(status: str | None)``); an out-of-domain
                value is refused by the schema's own ASSERT.

        Returns:
            The :class:`BriefAckResult` of this call.

        Raises:
            UnknownBriefError: ``name`` has no published version at all.
            UnknownBriefVersionError: ``name`` exists but not at ``version``.
        """
        del agent_name  # carried for API symmetry; not persisted on the edge.
        versions = self._as_rows(
            await self._query(
                f"SELECT * FROM {BRIEF_TABLE} WHERE {_COL_NAME} = ${_NAME_LOOKUP_PARAM}",
                {_NAME_LOOKUP_PARAM: name},
            )
        )
        if not versions:
            raise await self._unknown_brief_error(name)
        target = next((row for row in versions if int(row[_COL_VERSION]) == version), None)
        head_version = max(int(row[_COL_VERSION]) for row in versions)
        if target is None:
            raise UnknownBriefVersionError(f"brief {name!r} has no v{version} — head is v{head_version}")
        brief_id = self._bare_id(target[_ID_KEY])
        already_acked, recorded_via = await self._relate_briefed(
            agent_id=agent_id, brief_id=brief_id, via=via
        )
        return BriefAckResult(
            name=name,
            version=version,
            head_version=head_version,
            already_acked=already_acked,
            via=cast(BriefAckVia, recorded_via),
        )

    async def _relate_briefed(self, *, agent_id: str, brief_id: str, via: str) -> tuple[bool, str]:
        """RELATE one ``agent->briefed->brief`` edge, idempotent on UNIQUE(in, out).

        Live 3.1.5 gotcha (verified this session, see
        ``REPORT-c1-contract-schema.md``): ``RELATE type::record(...)->edge->
        type::record(...)`` is a PARSE ERROR. The working shape — cloned from
        ``loremaster.graph_surreal``'s ``_edge_statement``/``_node_statements``
        — is ``RELATE $from->edge->$to SET ...`` with ``$from``/``$to`` bound
        as SDK :class:`~surrealdb.RecordID` objects, never a ``type::record()``
        call at the RELATE endpoint position.

        A UNIQUE(in, out) rejection is treated as the idempotent-re-ack
        SIGNAL, not a genuine failure: the existing edge's ``via`` is read
        back and reported as ``already_acked=True``. Any OTHER rejection (e.g.
        an out-of-domain ``via`` hitting the schema ASSERT on a genuinely NEW
        pair) re-raises, since :meth:`_select_briefed_edge` then finds no
        existing edge to attribute the failure to.

        Returns:
            ``(already_acked, via)`` — ``via`` is the FIRST-recorded value on
            an idempotent no-op, else the value just written.
        """
        from_record = RecordID(AGENT_TABLE, agent_id)
        to_record = RecordID(BRIEF_TABLE, brief_id)
        try:
            await self._query(
                f"RELATE ${_ACK_FROM_PARAM}->{BRIEFED_RELATION}->${_ACK_TO_PARAM} SET "
                f"{_COL_VIA} = ${_ACK_VIA_PARAM}, {_COL_AT} = ${_ACK_AT_PARAM}",
                {
                    _ACK_FROM_PARAM: from_record,
                    _ACK_TO_PARAM: to_record,
                    _ACK_VIA_PARAM: via,
                    _ACK_AT_PARAM: datetime.now(UTC),
                },
            )
            return False, via
        except SurrealStoreError:
            existing_via = await self._select_briefed_edge(agent_id=agent_id, brief_id=brief_id)
            if existing_via is None:
                # Genuinely NOT a duplicate (e.g. an out-of-domain ``via`` on a
                # brand-new pair) — the original rejection stands.
                raise
            return True, existing_via

    async def _select_briefed_edge(self, *, agent_id: str, brief_id: str) -> str | None:
        """Return the stored ``via`` of the ``(agent_id, brief_id)`` edge, or ``None``."""
        rows = self._as_rows(
            await self._query(
                f"SELECT * FROM {BRIEFED_RELATION} WHERE {_COL_EDGE_IN} = ${_EDGE_IN_PARAM} "
                f"AND {_COL_EDGE_OUT} = ${_EDGE_OUT_PARAM} LIMIT 1",
                {
                    _EDGE_IN_PARAM: RecordID(AGENT_TABLE, agent_id),
                    _EDGE_OUT_PARAM: RecordID(BRIEF_TABLE, brief_id),
                },
            )
        )
        if not rows:
            return None
        return str(rows[0].get(_COL_VIA))

    async def acked_version(self, *, agent_id: str, name: str) -> int | None:
        """The max version of ``name`` this agent has acked, or ``None`` (unbriefed)."""
        edge_rows = self._as_rows(
            await self._query(
                f"SELECT {_COL_EDGE_OUT} FROM {BRIEFED_RELATION} WHERE {_COL_EDGE_IN} = ${_ACKED_IN_PARAM}",
                {_ACKED_IN_PARAM: RecordID(AGENT_TABLE, agent_id)},
            )
        )
        acked_brief_ids = {
            self._bare_id(row[_COL_EDGE_OUT]) for row in edge_rows if _COL_EDGE_OUT in row
        }
        if not acked_brief_ids:
            return None
        version_rows = self._as_rows(
            await self._query(
                f"SELECT * FROM {BRIEF_TABLE} WHERE {_COL_NAME} = ${_NAME_LOOKUP_PARAM}",
                {_NAME_LOOKUP_PARAM: name},
            )
        )
        versions = [
            int(row[_COL_VERSION])
            for row in version_rows
            if self._bare_id(row[_ID_KEY]) in acked_brief_ids
        ]
        return max(versions) if versions else None

    async def coverage(self, name: str, *, active_agents: Sequence[AgentRefLike]) -> BriefCoverage:
        """The coverage/skew standing for ``name`` across ``active_agents`` (§5.3).

        Args:
            name: The brief name.
            active_agents: The caller-resolved roster to check coverage over
                (this ledger never queries the ``agent`` table itself).

        Returns:
            The :class:`BriefCoverage` partitioning the roster into
            at-head (``current_count``) and behind/unbriefed (``behind``,
            sorted by agent name — a deterministic, non-roster-order sort).

        Raises:
            UnknownBriefError: ``name`` has no published version at all.

        Note:
            Issues exactly two store queries regardless of roster size (F3,
            ``REPORT-c1-audit-fixwave.md``): the ``versions`` lookup above,
            then ONE grouped ``briefed`` edge query for the whole roster
            (skipped when the roster is empty) — never a per-member
            :meth:`acked_version` call.
        """
        versions = self._as_rows(
            await self._query(
                f"SELECT * FROM {BRIEF_TABLE} WHERE {_COL_NAME} = ${_NAME_LOOKUP_PARAM}",
                {_NAME_LOOKUP_PARAM: name},
            )
        )
        if not versions:
            raise await self._unknown_brief_error(name)
        version_by_brief_id = {
            self._bare_id(row[_ID_KEY]): int(row[_COL_VERSION]) for row in versions
        }
        head_version = max(version_by_brief_id.values())
        roster = list(active_agents)
        acked_version_by_agent_id = await self._acked_versions_for_roster(
            roster, version_by_brief_id=version_by_brief_id
        )
        behind: list[BriefBehindEntry] = []
        current = 0
        for ref in roster:
            acked = acked_version_by_agent_id.get(ref.id)
            if acked == head_version:
                current += 1
            else:
                behind.append(BriefBehindEntry(agent_name=ref.name, acked_version=acked))
        behind.sort(key=lambda entry: entry.agent_name)
        return BriefCoverage(
            name=name,
            head_version=head_version,
            total_agents=len(roster),
            current_count=current,
            behind=behind,
        )

    async def acked_versions_for_ids(
        self, agent_ids: Sequence[str], *, name: str
    ) -> dict[str, int]:
        """The max acked version of ``name`` per agent id (finding #94).

        Self-contained public sibling of :meth:`_acked_versions_for_roster`:
        that helper requires a pre-computed ``version_by_brief_id`` a caller
        holding only bare ids (the ``fleet`` action's roster) does not
        already have in hand, so this resolves it itself and then reuses the
        SAME grouped-edge query — never a second, parallel grouped query.

        Mirrors :meth:`_acked_versions_for_roster`'s absent-key-means-
        unbriefed convention exactly: an id absent from the returned mapping
        is unbriefed for ``name``. An unpublished ``name`` returns ``{}``
        rather than raising :class:`UnknownBriefError` — this is a bulk
        status read (the ``fleet`` action's per-row lookup), not a skew
        computation the way :meth:`coverage` is.

        Bounded query count: an empty ``agent_ids`` short-circuits before
        any query. Otherwise exactly two — the ``name`` version lookup, then
        one grouped ``briefed`` edge query over ``agent_ids`` — independent
        of ``len(agent_ids)``, never one :meth:`acked_version` call per id.
        """
        if not agent_ids:
            return {}
        versions = self._as_rows(
            await self._query(
                f"SELECT * FROM {BRIEF_TABLE} WHERE {_COL_NAME} = ${_NAME_LOOKUP_PARAM}",
                {_NAME_LOOKUP_PARAM: name},
            )
        )
        if not versions:
            return {}
        version_by_brief_id = {
            self._bare_id(row[_ID_KEY]): int(row[_COL_VERSION]) for row in versions
        }
        roster = [_BareAgentRef(agent_id) for agent_id in agent_ids]
        return await self._acked_versions_for_roster(
            roster, version_by_brief_id=version_by_brief_id
        )

    async def _acked_versions_for_roster(
        self, roster: Sequence[AgentRefLike], *, version_by_brief_id: dict[str, int]
    ) -> dict[str, int]:
        """The max acked version of THIS brief name, per roster agent id.

        ONE grouped query over every ``briefed`` edge whose ``in`` is in the
        roster (an empty roster issues no query at all), joined in memory
        against ``version_by_brief_id`` — replaces the O(N) per-member
        :meth:`acked_version` loop that made ``coverage()`` scale with roster
        size. An agent absent from the returned mapping is unbriefed for this
        name (the caller reads that as ``acked_version=None``).
        """
        if not roster:
            return {}
        roster_ids = [RecordID(AGENT_TABLE, ref.id) for ref in roster]
        edge_rows = self._as_rows(
            await self._query(
                f"SELECT {_COL_EDGE_IN}, {_COL_EDGE_OUT} FROM {BRIEFED_RELATION} "
                f"WHERE {_COL_EDGE_IN} IN ${_COVERAGE_ROSTER_PARAM}",
                {_COVERAGE_ROSTER_PARAM: roster_ids},
            )
        )
        acked_version_by_agent_id: dict[str, int] = {}
        for row in edge_rows:
            if _COL_EDGE_IN not in row or _COL_EDGE_OUT not in row:
                continue
            brief_version = version_by_brief_id.get(self._bare_id(row[_COL_EDGE_OUT]))
            if brief_version is None:
                continue  # a briefed edge to a DIFFERENT brief name — irrelevant here
            agent_id = self._bare_id(row[_COL_EDGE_IN])
            current_max = acked_version_by_agent_id.get(agent_id)
            if current_max is None or brief_version > current_max:
                acked_version_by_agent_id[agent_id] = brief_version
        return acked_version_by_agent_id

    # -- result narrowing / mapping -------------------------------------------

    async def _select_row(self, brief_id: str) -> dict[str, Any] | None:
        """Return the raw ``brief`` row dict for ``brief_id``, or ``None`` if absent."""
        rows = self._as_rows(
            await self._query(
                f"SELECT * FROM type::record('{BRIEF_TABLE}', ${_ROW_ID_PARAM})",
                {_ROW_ID_PARAM: brief_id},
            )
        )
        return rows[0] if rows else None

    @staticmethod
    def _as_rows(result: Any) -> list[dict[str, Any]]:
        """Narrow a ``SELECT`` result to its list of dict rows."""
        if not isinstance(result, list):
            return []
        return [row for row in result if isinstance(row, dict)]

    def _row_to_brief(self, row: dict[str, Any]) -> Brief:
        """Map a raw ``brief`` row into a FRESH :class:`Brief` value object."""
        return Brief(
            id=self._bare_id(row.get(_ID_KEY)),
            name=str(row.get(_COL_NAME, "")),
            version=int(row.get(_COL_VERSION, 0)),
            body=str(row.get(_COL_BODY, "")),
            created_by=str(row.get(_COL_CREATED_BY, "")),
            note=row.get(_COL_NOTE),
            created_at=self._require_aware_utc(row.get(_COL_CREATED_AT)),
        )

    def _require_aware_utc(self, value: Any) -> datetime:
        """Normalise a REQUIRED datetime column to tz-aware UTC, refusing a bad value.

        Raises:
            SurrealStoreError: The value is missing or cannot be read as a datetime.
        """
        coerced = self._to_aware_utc(value)
        if coerced is None:
            raise SurrealStoreError(
                f"brief row column {_COL_CREATED_AT!r} is missing or not a datetime "
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
        """Return the BARE brief id — no ``brief:`` record-table prefix."""
        if isinstance(raw, RecordID):
            return str(raw.id)
        text = str(raw)
        if _TABLE_SEPARATOR in text:
            return text.split(_TABLE_SEPARATOR, 1)[1]
        return text
