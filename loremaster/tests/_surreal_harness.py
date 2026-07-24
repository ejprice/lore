"""Shared real-SurrealDB test harness for the P2 store-layer contract tests.

House style (mirrors ``conftest.py`` / ``test_qdrant_store.py``): the store tests
run against the **real** SurrealDB server, not an embedded/in-memory engine —
the whole point of P2 is server-side dialect behaviour (HNSW filtered recall,
BM25 FULLTEXT with the ``code_ident`` analyzer, native ``search::rrf`` fusion,
snapshot-isolated transactions). None of that is meaningful against a fake.

Connection topology is env-driven (``LORE_TEST_SURREAL_URL`` /
``LORE_TEST_SURREAL_USER`` / ``LORE_TEST_SURREAL_PASS``) with the spike defaults
(``ws://127.0.0.1:18000/rpc``, ``root`` / ``spikeroot``) so a CI box can retarget
without editing tests. An unreachable server is a LOUD failure (the fixture
raises), never a silent skip — a green suite must mean the contract really held
against the engine.

Isolation: every test/fixture gets a UNIQUE throwaway database under the
``lore_test`` namespace (``test_<pid>_<uuid4>``), and teardown issues
``REMOVE DATABASE IF EXISTS`` on it via a FRESH admin connection (independent of
whatever connection the test used, which a resilience test may have deliberately
broken). Nothing leaks; a reused PID later harmlessly reaps any prior orphan.

Import isolation: at MODULE level this imports ONLY the ``surrealdb`` SDK and the
pre-existing ``loremaster.index.records`` helpers, so it always imports cleanly.
35 test files import this harness, so a module-level import of code still being
built would turn one mid-TDD breakage into a COLLECTION error across all of them.
(A SMALLER, DIFFERENT population — 21 test files — calls ``connect_admin``; those two
numbers are not interchangeable, and committed prose conflated them until fff1382.
Both are pinned against an AST derivation in ``test_surreal_harness.py``, so this
sentence cannot rot.) The new-code imports (``SurrealStore`` / ``generate_ddl`` /
``Candidate``) live in the individual test files, so such a collection error stays
confined to them.

That isolation is why the store's shared retry seam (``loremaster.store._txn``) is
reached by IN-FUNCTION import only — never at module level (operator RULING 1,
2026-07-20). The harness owns NO CONFLICT-RETRY policy of its own: no conflict
budget, no backoff, no copy of the engine's conflict marker. (:func:`call_until_recovered`
does own an attempt bound, and correctly so — it is a lifecycle RECOVERY probe for
degradation/recovery tests, a different concern from conflict retry, and it must NOT
route through ``_txn``.) ``connect_admin`` bootstraps its session through
``_txn.bootstrap_session``; teardown's ``use()`` and its ``REMOVE DATABASE`` both go
through :func:`_run_under_store_retry_seam`, this module's single classify-and-signal
site over ``_txn.retry_on_conflict``. Moving a constant in the seam moves this harness
with it — pinned by mutation in ``test_surreal_harness.py`` (finding #150).

------------------------------------------------------------------------------
HOW TO RESOLVE THE ``blindreader-150 F*`` / ``audit-150 R*`` CITATIONS IN THIS FILE.

They are review-pass identifiers from finding **#150**'s review wave. The reports they
name were ARCHIVED at ``7d2ff44`` and resolve, section-exactly, under
``docs/plans/v2/receipts/2026-07-20-150/`` — ``REPORT-blindreader-150.md`` for the ``F*``
ids, and ``REPORT-audit-150-cold.md`` for EVERY ``audit-150 R*`` id below (#152).

Naming that one file is not pedantry: the archive holds TWO ``audit-150`` reports, and
both define an R4 AND an R5 meaning entirely different things — so a citation that says
only ``audit-150`` is ambiguous, and this block is what disambiguates it. The durable
address for the CLAIMS remains the ledger row **#150** (**#151** for the one defect
deliberately left open). Every citation below states its own substance inline; none of
them is a pointer a reader must follow in order to act.
"""

from __future__ import annotations

import os
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

import pytest_asyncio
from loremaster.index.records import Record, point_id, sha512_hex
from surrealdb import (
    AsyncEmbeddedSurrealConnection,
    AsyncHttpSurrealConnection,
    AsyncSurreal,
    AsyncWsSurrealConnection,
)

# ``AsyncSurreal`` is a factory that returns one of these concrete connection
# classes by URL scheme; this alias is exactly its return union so raw-SDK helpers
# type-check under mypy-strict.
SurrealConnection = (
    AsyncEmbeddedSurrealConnection | AsyncHttpSurrealConnection | AsyncWsSurrealConnection
)

# --- env-driven topology (defaults are the P0-spike container) --------------
_ENV_URL = "LORE_TEST_SURREAL_URL"
_ENV_USER = "LORE_TEST_SURREAL_USER"
_ENV_PASS = "LORE_TEST_SURREAL_PASS"

DEFAULT_URL = "ws://127.0.0.1:18000/rpc"
DEFAULT_USER = "root"
DEFAULT_PASS = "spikeroot"

# The shared throwaway namespace; every test DB is created and reaped under it.
TEST_NAMESPACE = "lore_test"

# The real production embedding width (read from this repo's own ``lore.yaml``:
# ``embedding.dim: 2048``) — the store fixtures embed at this scale so vectors
# reflect the real distribution the store will see, not a convenience width.
PRODUCTION_DIM = 2048

# A deliberately NON-production width for the config-driven-DDL test: proves the
# generator threads the configured ``dim`` through the HNSW index rather than
# baking in the production default.
NONDEFAULT_DIM = 512

# The analyzer name the P0 spike verified on 3.0.5, re-verified with no dialect
# deltas on 3.1.5 (the documented floor going forward — TOKENIZERS
# blank,class,camel,punct FILTERS lowercase,ascii).
ANALYZER_NAME = "code_ident"

# Project/tier identity components fed into the SHARED point-id scheme
# (``records.point_id``) — the same source of truth production uses, so a test
# key can never drift from a real one (clause 5).
SLUG = "demo"
TIER_A = "custom"
TIER_B = "community"

# The canonical event names this module's two seam call sites are attributed under in
# ``_txn``'s exhaustion log record. These are IDENTITY, not policy — the seam gates
# ``engine_error``/``url`` on the presence of a label, so an unlabelled call raises a
# message pointing an operator at a log record that holds nothing (#151, blindreader-150 F1).
# Shape follows the store seams' own ``_SEAM_REJECTION_EVENTS`` convention.
_TEARDOWN_SELECT_DATABASE_LABEL = "harness.teardown.select_database"
_TEARDOWN_REMOVE_DATABASE_LABEL = "harness.teardown.remove_database"


def surreal_url() -> str:
    """The SurrealDB RPC URL (env override, else the spike default)."""
    return os.environ.get(_ENV_URL, DEFAULT_URL)


def surreal_user() -> str:
    """The root user (env override, else the spike default)."""
    return os.environ.get(_ENV_USER, DEFAULT_USER)


def surreal_password() -> str:
    """The root password (env override, else the spike default)."""
    return os.environ.get(_ENV_PASS, DEFAULT_PASS)


def unique_database() -> str:
    """A per-test database name unique to this process (``test_<pid>_<uuid4>``).

    The ``<pid>`` prefix means a concurrent pytest process on the SAME server
    never collides on, or reaps, this database — the same concurrency-safety the
    Qdrant conftest gets from its per-process collection prefix.
    """
    return f"test_{os.getpid()}_{uuid.uuid4().hex}"


@dataclass(frozen=True)
class SurrealEnv:
    """The immutable connection topology handed to a store under test.

    Attributes:
        url: The SurrealDB RPC URL.
        user: The root username.
        password: The root password.
        namespace: The (shared) test namespace.
        database: The UNIQUE per-test database.
        dim: The embedding width the store/schema is configured for.
    """

    url: str
    user: str
    password: str
    namespace: str
    database: str
    dim: int


def make_env(*, database: str, dim: int) -> SurrealEnv:
    """Build a :class:`SurrealEnv` for ``database`` at embedding width ``dim``."""
    return SurrealEnv(
        url=surreal_url(),
        user=surreal_user(),
        password=surreal_password(),
        namespace=TEST_NAMESPACE,
        database=database,
        dim=dim,
    )


async def run(
    connection: SurrealConnection,
    statement: str,
    params: dict[str, Any] | None = None,
) -> Any:
    """Execute one statement and hand back the raw result.

    Launders the SDK's wide ``Value`` return union into ``Any`` so the schema
    tests can index/``.get`` results without a cascade of union-narrowing noise —
    the same pattern ``conftest.kz_query``/``kz_row`` use for the Kùzu union.
    """
    return await connection.query(statement, params)


async def call_until_recovered[T](
    op: Callable[[], Awaitable[T]],
    healable_errors: tuple[type[BaseException], ...],
    *,
    attempts: int = 4,
    label: str = "component",
) -> T:
    """Call ``op`` until it succeeds, swallowing ``healable_errors``.

    The shared mid-life-connection-drop recovery probe both the store and the
    manifest lifecycle tests use (degradation -> recovery, CLAUDE.md): proves
    a self-healing component is NOT permanently wedged after a transient
    connection failure — a healthy component heals within a few calls
    (whether it retries transparently or surfaces one transient error then
    reconnects), while a genuinely wedged component raises on EVERY attempt
    and this exhausts, surfacing an ``AssertionError`` — the RED a missing
    lifecycle test would otherwise miss.

    Args:
        op: The zero-argument operation to retry.
        healable_errors: The exception types a transient, self-healing
            failure may surface as. Caller-supplied (rather than hardcoded
            here) because which types count as "healable" is specific to the
            component under test (e.g. the store's vs. the manifest's own
            typed connection-error wrapper).
        attempts: The number of calls to attempt before giving up.
        label: The component name used in the exhaustion message (e.g.
            ``"store"`` / ``"manifest"``).

    Returns:
        ``op``'s successful return value.

    Raises:
        AssertionError: ``op`` failed on every attempt — the component never
            recovered.
    """
    last: BaseException | None = None
    for _ in range(attempts):
        try:
            return await op()
        except healable_errors as error:
            last = error
    raise AssertionError(f"{label} never recovered within {attempts} calls: {last!r}")


def _seam_default_deadline_seconds() -> float:
    """The seam's LIVE default wall-clock retry budget, read at CALL time.

    Never a module-level ``from … import``: that would freeze the value at import and
    the composed budget below would then be a private copy of a number rather than the
    seam's own (and RULING 1 forbids the module-level store import anyway).
    """
    from loremaster.store import _txn

    return float(_txn._TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS)


async def _run_under_store_retry_seam[T](
    operation: Callable[[], Awaitable[T]],
    *,
    label: str,
    url: str,
    deadline_seconds: float | None = None,
) -> T:
    """Run ``operation`` under the store package's ONE retry driver (finding #150).

    This module's SINGLE classify-and-signal site. Both teardown operations that can
    hit the engine's retryable write-write conflict — selecting the database
    (``use()``) and removing it — call THIS; neither clones the shape, because two
    call sites needing the same policy is a function they call, never a pattern they
    copy. ``connect_admin`` needs no helper at all:
    :func:`~loremaster.store._txn.bootstrap_session` already IS the shared,
    budget-composing form of exactly this over its three statements.

    Detection stays with the caller by the seam's own design (see
    ``retry_on_conflict``'s docstring: "detection stays with the caller that owns the
    wire shape"), so this classifies what it catches through the seam's ONE
    classifier and raises the seam's signal. It owns no conflict budget, no backoff
    and no marker of its own — move any of those in ``_txn`` and this moves with it
    (pinned by mutation in ``test_surreal_harness.py``).

    The ``_txn`` import is IN-FUNCTION deliberately (RULING 1) — see the module
    docstring's import-isolation note.

    Args:
        operation: The zero-argument async operation to run. Must be safe to re-run
            from scratch: true for both callers here, since a conflicted
            single-statement DDL commits nothing.
        label: This call site's canonical event name, carried into the seam's
            exhaustion log record. REQUIRED, not optional: the seam gates
            ``engine_error``/``url`` on ``label is not None``
            (``_txn.retry_on_conflict``), so a call that omits it raises a message
            pointing the operator at a server log record that does NOT contain what
            the engine said. There is no call site here that should be anonymous.
        url: The RPC URL this operation runs against, logged beside ``label``.
        deadline_seconds: What is LEFT of the CALLER's one wall-clock budget, so a
            caller driving several operations composes ONE budget across them rather
            than handing each a fresh copy (``_txn.bootstrap_session``'s
            ``_remaining_budget`` is the same shape; its docstring: "three equal
            deadlines would be three independent budgets wearing a parameter").
            ``None`` lets the seam resolve its own default — correct only for a
            caller that drives exactly ONE operation.

    Returns:
        ``operation``'s successful return value.

    Raises:
        TxnContentionExhaustedError: The conflict outlived the SEAM's budget. Every
            other exception propagates untouched, unretried.
    """
    from loremaster.store._txn import (
        _CONNECTION_ERRORS,
        RetryableConflictSignal,
        is_retryable_conflict_error,
        retry_on_conflict,
    )

    async def _attempt() -> T:
        try:
            return await operation()
        except _CONNECTION_ERRORS as error:
            if is_retryable_conflict_error(error):
                raise RetryableConflictSignal() from error
            raise

    return await retry_on_conflict(
        _attempt, deadline_seconds=deadline_seconds, label=label, url=url
    )


async def connect_admin(env: SurrealEnv) -> SurrealConnection:
    """Open a raw signed-in SDK connection bound to ``env``'s namespace + database.

    Ensures the namespace and database exist so a later ``REMOVE DATABASE`` always
    has a target. Used by the schema tests (which apply generated DDL directly,
    independently of :class:`SurrealStore`) and by teardown.

    The three-statement session bootstrap is the store package's shared
    :func:`~loremaster.store._txn.bootstrap_session` — the same one every production
    ``_ensure_connection`` uses. It used to be three BARE, UNRETRIED ``await``\\ s
    here, which is precisely the defect that seam was built to close on the
    production side (probed live, 16-way concurrent: 6.2%-34.4% of virgin
    first-connects lost). Every ``[real]`` fixture in this suite opens one of these,
    and the standing runner is ``-n auto``, so the hole was a stochastic
    setup-failure rate across the whole suite (finding #150).
    """
    connection = AsyncSurreal(env.url)
    credentials: dict[str, Any] = {"username": env.user, "password": env.password}
    await connection.signin(credentials)

    from loremaster.store._txn import bootstrap_session

    try:
        await bootstrap_session(connection, env.namespace, env.database, url=env.url)
    except BaseException:
        # The caller never receives this connection, so nobody else can close it. The
        # bootstrap now RETRIES a conflict for up to the seam's budget while holding
        # the socket, so a contended-and-exhausted connect used to leak one socket per
        # failure against the shared dev server (audit-150 R5 / blindreader-150 F10, one
        # function over from `drop_database`'s identical leak).
        await connection.close()
        raise
    return connection


class _RemovableDatabaseConnection(Protocol):
    """Structural seam: only the ``query`` call :func:`_remove_database_with_retry`
    needs.

    A :class:`typing.Protocol` (rather than the concrete ``SurrealConnection``
    union) so a test can pin the retry behaviour with a lightweight fake
    connection, without constructing a real SDK connection object.
    """

    async def query(self, statement: str, /) -> Any: ...


async def _remove_database_with_retry(
    connection: _RemovableDatabaseConnection,
    database: str,
    *,
    url: str,
    deadline_seconds: float | None = None,
) -> None:
    """Run ``REMOVE DATABASE IF EXISTS`` under the store seam's retry policy.

    Teardown races background RocksDB/index maintenance work on the shared dev
    server, which intermittently rolls the ``REMOVE`` back with
    ``surrealdb.errors.QueryError: ... This transaction can be retried`` — an
    ENGINE-FLAGGED retryable conflict, not a real problem with the database being
    removed (confirmed live: it hit ~30-50% of standalone store-suite runs, on a
    different random test's teardown each time).

    The budget, the backoff and the conflict classification are ALL the seam's —
    see :func:`_run_under_store_retry_seam`. Any other error propagates immediately,
    unretried: teardown must never silently swallow a real problem.

    Args:
        connection: The signed-in, database-selected connection to run the REMOVE on.
        database: The database to remove.
        url: The RPC URL, for the seam's exhaustion log attribution.
        deadline_seconds: What is LEFT of the CALLER's one teardown budget — see
            :func:`_run_under_store_retry_seam`.
    """

    async def _remove() -> None:
        await connection.query(f"REMOVE DATABASE IF EXISTS {database}")

    await _run_under_store_retry_seam(
        _remove,
        label=_TEARDOWN_REMOVE_DATABASE_LABEL,
        url=url,
        deadline_seconds=deadline_seconds,
    )


async def drop_database(env: SurrealEnv) -> None:
    """Reap ``env``'s database via a FRESH admin connection (teardown-safe).

    Deliberately does NOT reuse the test's connection — a resilience test may have
    pointed its store at a dead port or closed the socket — so teardown always
    runs against a healthy admin connection and never leaks the database.

    BOTH engine operations here are retried on the engine's retryable conflict
    through the shared store seam: selecting the database (which was a bare,
    unretried ``await`` until finding #150 — the same hole as the bootstrap's, one
    function over) and the ``REMOVE DATABASE`` itself.

    Those two operations share ONE wall-clock budget, exactly as
    :func:`~loremaster.store._txn.bootstrap_session` composes one across its three
    (see its docstring: "three equal deadlines would be three independent budgets
    wearing a parameter"). Handing each call a fresh copy of the seam's default made
    teardown's real bound DOUBLE its designed one — measured at **3.812s** against a
    designed 2.0s (blindreader-150 F2 / audit-150 R4), on a path that runs for EVERY
    ``[real]`` test under the standing ``-n auto`` runner. Composing cannot starve
    either operation of retries: the seam's attempt FLOOR guarantees each its
    attempts regardless of wall time.
    """
    connection = AsyncSurreal(env.url)
    credentials: dict[str, Any] = {"username": env.user, "password": env.password}
    await connection.signin(credentials)

    started = time.monotonic()
    budget = _seam_default_deadline_seconds()

    def _remaining_budget() -> float:
        """What is LEFT of teardown's ONE wall-clock budget, never negative."""
        return max(0.0, budget - (time.monotonic() - started))

    async def _select_database() -> None:
        await connection.use(env.namespace, env.database)

    try:
        await _run_under_store_retry_seam(
            _select_database,
            label=_TEARDOWN_SELECT_DATABASE_LABEL,
            url=env.url,
            deadline_seconds=_remaining_budget(),
        )
        await _remove_database_with_retry(
            connection,
            env.database,
            url=env.url,
            deadline_seconds=_remaining_budget(),
        )
    finally:
        # `close()` used to be reachable ONLY on the success path, so every failure
        # leaked the socket — pre-existing, but the window widened from ~0.1s to the
        # seam's full budget once these two operations started retrying (audit-150 R5
        # / blindreader-150 F10).
        await connection.close()


def unit_vector(axis: int, dim: int, magnitude: float = 1.0) -> list[float]:
    """A ``dim``-length vector that is ``magnitude`` on ``axis`` and 0 elsewhere.

    Distinct axes are orthogonal (cosine distance 1.0); the same axis is identical
    (cosine distance 0.0). This lets a test place a chunk's vector *deliberately*
    near or far from a query in the real ``dim``-wide space without hand-tuning
    2048 floats — the near/far relationship is exact and independent of the
    store's internal maths.
    """
    vector = [0.0] * dim
    vector[axis] = magnitude
    return vector


# Realistic code identifiers/text — the actual range/shape of what lore indexes
# (Odoo-style domain code), NOT ``foo``/``x=1``. ``ident_text`` carries the
# identifier tokens the ``code_ident`` analyzer splits for BM25; ``source_text``
# is the verbatim body a citation renders.
_SOURCE_TEXT = (
    "def action_confirm(self):\n"
    "    for order in self:\n"
    "        order.write({'state': 'purchase'})\n"
    "    return True\n"
)


def chunk_record(
    *,
    tier: str,
    file_path: str,
    identity: str,
    chunk_type: str = "python_symbol",
    sub_ordinal: int = 0,
    ident_text: str = "PurchaseOrder action_confirm",
    source_text: str = _SOURCE_TEXT,
    llm_summary: str | None = None,
    metadata: dict[str, Any] | None = None,
    slug: str = SLUG,
) -> Record:
    """Build a chunk :class:`Record` whose id comes from the SHARED point-id scheme.

    The point id is minted by the production ``records.point_id`` (the single
    source of truth for the tiered UUID5 key), so a test id is byte-identical to
    what the indexer would produce — the store's job is to persist it as the
    chunk's record id and round-trip it back as the neutral candidate ``key``.
    ``content_hash`` is a real SHA-512 over the source text (128 hex chars), the
    same digest staleness detection uses.
    """
    payload: dict[str, Any] = {
        "tier": tier,
        "file_path": file_path,
        "chunk_type": chunk_type,
        "identity": identity,
        "sub_ordinal": sub_ordinal,
        "content_hash": sha512_hex(source_text),
        "mtime_ns": time.time_ns(),
        "line_start": 1,
        "line_end": source_text.count("\n") + 1,
        "source_text": source_text,
        "ident_text": ident_text,
        "metadata": dict(metadata or {}),
    }
    if llm_summary is not None:
        payload["llm_summary"] = llm_summary
    return Record(
        point_id=point_id(slug, tier, file_path, chunk_type, identity, sub_ordinal),
        embedding_text=ident_text,
        payload=payload,
    )


@pytest_asyncio.fixture()
async def surreal_env() -> AsyncIterator[SurrealEnv]:
    """Yield a :class:`SurrealEnv` on a fresh unique database at the production dim.

    Owns the database lifecycle: the DB is created on entry and reaped on exit via
    a fresh admin connection (``REMOVE DATABASE IF EXISTS``), so no test leaks a
    database on the shared server regardless of how the test's own connection
    ended up.
    """
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    # Materialise the namespace + database up front so teardown has a target even
    # if the test never wrote anything (or the store failed to connect).
    setup_connection = await connect_admin(env)
    await setup_connection.close()
    try:
        yield env
    finally:
        await drop_database(env)


@pytest_asyncio.fixture()
async def admin_db() -> AsyncIterator[tuple[SurrealConnection, SurrealEnv]]:
    """Yield ``(raw_connection, env)`` on a fresh unique database, reaped on exit.

    The schema tests use this to apply generated DDL and introspect the result
    (``INFO FOR DB`` / ``INFO FOR TABLE``) directly — ``surreal_schema`` is a pure
    function, testable without a :class:`SurrealStore` at all.
    """
    env = make_env(database=unique_database(), dim=NONDEFAULT_DIM)
    connection = await connect_admin(env)
    try:
        yield connection, env
    finally:
        await connection.close()
        await drop_database(env)
