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

This module imports ONLY the ``surrealdb`` SDK and the pre-existing
``loremaster.index.records`` helpers (both of which already exist), so it always
imports cleanly. The new-code imports (``SurrealStore`` / ``generate_ddl`` /
``Candidate``) live in the individual test files, so a P2-not-yet-implemented
collection error stays confined to those new test files.
"""

from __future__ import annotations

import os
import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

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

# The analyzer name the P0 spike verified on 3.0.5 (TOKENIZERS
# blank,class,camel,punct FILTERS lowercase,ascii).
ANALYZER_NAME = "code_ident"

# Project/tier identity components fed into the SHARED point-id scheme
# (``records.point_id``) — the same source of truth production uses, so a test
# key can never drift from a real one (clause 5).
SLUG = "demo"
TIER_A = "custom"
TIER_B = "community"


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


async def connect_admin(env: SurrealEnv) -> SurrealConnection:
    """Open a raw signed-in SDK connection bound to ``env``'s namespace + database.

    Ensures the namespace and database exist so a later ``REMOVE DATABASE`` always
    has a target. Used by the schema tests (which apply generated DDL directly,
    independently of :class:`SurrealStore`) and by teardown.
    """
    connection = AsyncSurreal(env.url)
    credentials: dict[str, Any] = {"username": env.user, "password": env.password}
    await connection.signin(credentials)
    await connection.query(f"DEFINE NAMESPACE IF NOT EXISTS {env.namespace}")
    await connection.use(env.namespace, env.database)
    await connection.query(f"DEFINE DATABASE IF NOT EXISTS {env.database}")
    return connection


async def drop_database(env: SurrealEnv) -> None:
    """Reap ``env``'s database via a FRESH admin connection (teardown-safe).

    Deliberately does NOT reuse the test's connection — a resilience test may have
    pointed its store at a dead port or closed the socket — so teardown always
    runs against a healthy admin connection and never leaks the database.
    """
    connection = AsyncSurreal(env.url)
    credentials: dict[str, Any] = {"username": env.user, "password": env.password}
    await connection.signin(credentials)
    await connection.use(env.namespace, env.database)
    await connection.query(f"REMOVE DATABASE IF EXISTS {env.database}")
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
