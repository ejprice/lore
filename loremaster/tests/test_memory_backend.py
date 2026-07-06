"""CONTRACT tests for the P7 ``MemoryBackend`` seam over SurrealDB.

The v2 unification replaces the Qdrant-only ``MemoryStore`` with a
``MemoryBackend`` protocol whose local implementation
(:class:`~loremaster.memory.local.LocalMemoryBackend`) speaks the
Spectron-derived, snake_case memory wire vocabulary over the per-project
SurrealDB database. This module pins the OBSERVABLE contract of that seam,
written BLIND to the (not-yet-written) implementation — behavioural
expectations come from the P7 requirement, never from any code under test.

Two new modules the STUB phase will create, imported here as the contract:

* ``loremaster.memory.backend`` — the wire models + the ``MemoryBackend``
  protocol + the plan-pinned constants:
    - ``MemorySource`` (``kind: str``; ``ref: str | None``; ``trust`` — a
      Literal enum ``{"authoritative","experiential"}``, default
      ``"experiential"``. The P2 schema's *float* trust column was wrong and is
      being migrated; this pins the enum.)
    - ``RecalledMemory`` / ``RecalledRef`` — the summarised recall value objects
      (never raw Surreal rows). ``RecalledRef`` keeps the store's
      ``chunk_key`` / ``key_version`` field names + a per-ref ``drifted`` flag.
    - ``MemoryNotFoundError`` — the typed not-found raised by ``invalidate`` and
      by ``remember(supersedes=<unknown>)``.
    - ``IMPORTANCE_DEFAULTS_BY_KIND`` / ``ONGOING_DEFAULT_TTL`` /
      ``REINFORCEMENT_STEP`` — the plan-pinned defaults.
* ``loremaster.memory.local`` — ``LocalMemoryBackend`` (async).

IDENTITY BACKWARD-COMPAT: memory ids stay ``uuid5``-content-derived exactly as
the v0.3 ledger mints them —
``uuid5(NAMESPACE_URL, f"memory:{note_text}:{refs_stamp}")`` where ``refs_stamp``
is the sorted, ``,``-joined ``chunk_key@key_version`` stamp of the memory's
``lore_ref`` labels (empty when it carries none). This is reconstructed
INDEPENDENTLY below (mirroring ``test_memory_durability.expected_memory_id``) so
the ledger replay re-mints identical ids — the seam that keeps a restore an
in-place overwrite, never a duplicate.

HERMETIC HARNESS: a real per-test SurrealDB database (``_surreal_harness`` — a
unique throwaway db under the ``lore_test`` namespace, reaped on exit), the
shipped deterministic :class:`~loresigil.testing.FakeEmbedder` at the production
dim, a ``tmp_path`` :class:`~loremaster.memory.ledger.MemoryLedger`, and a
controllable dict-backed chunk-existence oracle. EVERY backend is built through
the ONE ``make_backend`` factory fixture (never inline) so a later fake-parity
wave can parametrise it to also run this suite against a ``FakeMemoryBackend``.

RED posture at this phase: collection ERROR — ``ModuleNotFoundError`` for
``loremaster.memory.backend`` / ``loremaster.memory.local`` (they do not exist
yet). That is the coordinated, expected failure.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest
import pytest_asyncio

# The adversarial in-memory fake-vs-real parity double (see its module
# docstring for the deliberate adversarial behaviours).
from _memory_fakes import FakeMemoryBackend

# The shared real-SurrealDB harness. ``make_backend``'s "real" branch calls
# ``make_env``/``connect_admin``/``drop_database`` directly (mirroring
# ``test_task_ledger.py``'s ``task_ledger_factory``) rather than depending on
# the ``surreal_env`` pytest fixture — pytest-asyncio 1.4's function-scoped
# ``Runner`` is shared by every async fixture a test uses, and resolving one
# async fixture from INSIDE another async fixture's own body re-enters that
# Runner (``RuntimeError: Runner.run() cannot be called from a running event
# loop``, verified live in that sibling module). Calling the exact same
# underlying helpers ``surreal_env`` itself calls gets the identical
# isolated-throwaway-database guarantee without touching pytest's fixture
# graph — and, crucially, lets the "fake" branch skip SurrealDB entirely.
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    unique_database,
)

# Shared domain conventions from THE SAME source of truth as production (clause
# 5): the default keying-scheme version a bare ``lore_ref`` label carries.
from loremaster.extension import DEFAULT_KEY_VERSION

# --- THE CONTRACT UNDER TEST (does not exist yet — collection RED lives here) --
from loremaster.memory.backend import (
    IMPORTANCE_DEFAULTS_BY_KIND,  # noqa: F401 - contract anchor (independence: NOT asserted against)
    ONGOING_DEFAULT_TTL,  # noqa: F401 - contract anchor (independence: NOT asserted against)
    REINFORCEMENT_STEP,  # noqa: F401 - contract anchor (independence: NOT asserted against)
    MemoryBackend,  # noqa: F401 - the protocol the local backend must satisfy
    MemoryNotFoundError,
    MemoryRef,
    MemorySource,
    RecalledMemory,
    RecalledRef,  # noqa: F401 - contract anchor for the recalled-ref shape
    derive_memory_id,
    derive_refs_stamp,
    refs_from_stamp,
)

# The EXISTING durable ledger (reused, not redesigned — the FP-06 source of
# truth the backend write-throughs to and replays from).
from loremaster.memory.ledger import MemoryLedger

# ``_MAX_LEXICAL_QUERY_CHARS`` / ``_MAX_QUERY_TOKENS`` imported directly (finding
# #69's own tests pin the recall path's derived clamps, mirroring
# ``test_surreal_store.py``'s identical import of the chunk store's twins).
from loremaster.memory.local import (
    _MAX_LEXICAL_QUERY_CHARS,
    _MAX_QUERY_TOKENS,
    LocalMemoryBackend,
)

# The shared error-classification vocabulary the ``_query`` seam raises (the same
# transport-vs-domain split ``store._txn`` establishes) — imported here to pin the
# single-statement seam's classified posture directly.
from loremaster.store._txn import (
    _ERROR_CLASS_QUERY_TOO_COMPLEX,
    SurrealConnectionError,
    SurrealStoreError,
    _classify_engine_error,
    _SurrealConnection,
)
from loremaster.store.query_text import truncate_at_word_boundary
from loremaster.store.surreal_schema import MEMORY_TABLE
from loresigil.base import EmbedResult
from loresigil.testing import FakeEmbedder
from pydantic import ValidationError
from surrealdb.errors import ErrorKind, ServerError

# ===========================================================================
# INDEPENDENT ORACLES — expected values from the P7 REQUIREMENT, not the impl.
# These are hand-written from the plan so a WRONG constant in the implementation
# goes RED (asserting against the impl's own ``IMPORTANCE_DEFAULTS_BY_KIND`` etc.
# would be tautological — a wrong number would pass). The imported constants
# above are anchors only; the assertions below use these independent literals.
# ===========================================================================

# Per-kind default importance (P7 plan). Independent of the impl's table.
REQUIRED_IMPORTANCE_BY_KIND: dict[str, float] = {
    "decision": 0.9,
    "gotcha": 0.8,
    "ongoing": 0.7,
    "uncertainty": 0.6,
    "fact": 0.5,
}

# The reinforcement bump applied to a recalled memory's importance (P7 plan).
REQUIRED_REINFORCEMENT_STEP = 0.05

# The default TTL applied to an ``ongoing`` memory saved without an explicit
# ``expires_at`` (P7 plan: 7 days, relative to creation).
REQUIRED_ONGOING_TTL = timedelta(days=7)

# The full memory-kind vocabulary (P7 plan, Spectron-derived, snake_case).
MEMORY_KINDS: tuple[str, ...] = ("fact", "decision", "gotcha", "uncertainty", "ongoing")

# ===========================================================================
# The deterministic-id convention, reconstructed INDEPENDENTLY
# (mirrors test_memory_durability.py so a restore re-mints identical ids). The
# id folds in ONLY the ``lore_ref`` labels; other labels never affect it.
# ===========================================================================
_ID_PREFIX = "memory"
_ID_SEPARATOR = ":"
_REF_FIELD_SEPARATOR = "@"
_REF_JOIN = ","
_LORE_REF_LABEL_PREFIX = "lore_ref="


def lore_ref_label(chunk_key: str, key_version: int | None = None) -> str:
    """Build a flat ``lore_ref=`` label string — the wire form a memory carries.

    A memory's chunk references ride its ``labels`` list as flat strings:
    ``"lore_ref=<chunk_key>"`` (version omitted → defaults to
    :data:`~loremaster.extension.DEFAULT_KEY_VERSION`) or the versioned
    ``"lore_ref=<chunk_key>@<key_version>"``. This is the producer side of the
    label → refs_stamp → id seam.
    """
    if key_version is None:
        return f"{_LORE_REF_LABEL_PREFIX}{chunk_key}"
    return f"{_LORE_REF_LABEL_PREFIX}{chunk_key}{_REF_FIELD_SEPARATOR}{key_version}"


def expected_refs_stamp(lore_refs: list[tuple[str, int]]) -> str:
    """The order-insensitive refs stamp folded into a memory's deterministic id.

    Each ref becomes ``chunk_key@key_version``, the set is sorted, and joined by
    ``,``. An empty ref list stamps the empty string. Independent reconstruction
    of the documented convention — NOT read back from the code under test.
    """
    stamped = sorted(
        f"{chunk_key}{_REF_FIELD_SEPARATOR}{key_version}"
        for chunk_key, key_version in lore_refs
    )
    return _REF_JOIN.join(stamped)


def expected_memory_id(note_text: str, lore_refs: list[tuple[str, int]] | None = None) -> str:
    """The deterministic ``uuid5`` id for a memory, computed from the convention.

    ``uuid5(NAMESPACE_URL, "memory:{note_text}:{refs_stamp}")``. Independent
    oracle for the dedup/overwrite/backward-compat invariants.
    """
    refs_stamp = expected_refs_stamp(list(lore_refs or ()))
    name = _ID_SEPARATOR.join((_ID_PREFIX, note_text, refs_stamp))
    return str(uuid.uuid5(uuid.NAMESPACE_URL, name))


# --- Pinned LITERAL uuid5 ids (belt-and-braces on the convention) -----------
# The note text + chunk key the literals were computed for. If either the id
# scheme or these literals drift, the pin below breaks loudly — the point.
PG_NOTE = (
    "PG 18 mounts the data volume at /var/lib/postgresql, not "
    "/var/lib/postgresql/data, or pg_ctlcluster errors at startup."
)
PINNED_CHUNK_KEY = "loremaster:loremaster/memory/store.py:symbol:MemoryStore:0"

_LITERAL_ID_NO_REFS = "e2bc45a8-8fda-54f1-af83-8a8d1a6b46e6"
_LITERAL_ID_REF_V1 = "7f7e4e9a-d085-5b08-8d2d-12dc695fbdce"
_LITERAL_ID_REF_V3 = "e48db6b6-3dd4-572a-843b-8203fcd3d58b"

# ===========================================================================
# Production-representative memory prose — the ACTUAL range/shape of operator
# notes that land in this store (deploy gotchas, model decisions, host facts),
# one per kind. NOT foo/bar/x=1.
# ===========================================================================
KIND_NOTES: dict[str, str] = {
    "fact": (
        "The lore container runs the baked localhost/lore:latest image, not the "
        "mounted source; a loremaster fix needs an image rebuild + recreate."
    ),
    "decision": (
        "We chose voyage-4-large for large repos and voyage-3-nano for small "
        "ones; accuracy always beats cost in the embedder A/B."
    ),
    "gotcha": (
        "SELinux bind mounts need :Z (-v /host:/container:Z) or the container "
        "sees Permission denied on files it clearly owns."
    ),
    "uncertainty": (
        "Unclear whether voyage-context-4 improves code recall; the lore A/B was "
        "inconclusive at 146 chunks."
    ),
    "ongoing": (
        "Migrating the project-memory backend from Qdrant to SurrealDB under P7 "
        "of the lore v2 plan."
    ),
}

# Realistic chunk keys for the drift oracle — the point-id shape lore mints
# (``<slug>:<path>:symbol:<Ident>:<ordinal>``). One still exists on disk; one was
# deleted by a refactor (the drift case).
EXISTING_CHUNK_KEY = "loremaster:loremaster/memory/local.py:symbol:LocalMemoryBackend:0"
MISSING_CHUNK_KEY = "loremaster:loremaster/memory/store.py:symbol:LegacyCorrection:0"

# A port with nothing listening — the "SurrealDB is down" adversary for the
# write-through-durability seam (mirrors test_surreal_store.py's _DEAD_URL).
_DEAD_URL = "ws://127.0.0.1:19555/rpc"

# A generous recall cap for the small test corpora: big enough to return every
# stored memory (so a recall can double as a full-table read for counting),
# never so small it truncates an intended result.
_READ_ALL = 100

# A comfortable wall-clock margin for the live/expiry-window assertions: far
# larger than any test's processing time, far smaller than the TTL under test.
_CLOCK_MARGIN = timedelta(hours=1)

# Factory type the ``make_backend`` fixture yields.
BackendFactory = Callable[..., Awaitable[LocalMemoryBackend]]


class FakeChunkOracle:
    """A controllable, dict-backed async BATCH chunk-existence oracle (the drift input).

    The backend is constructed with an async ``existing_chunks(chunk_keys) ->
    set[str]`` oracle: given the collection of a recall's ref chunk-keys, it
    returns the SUBSET that still exist. A key in ``existing`` is present (a live
    ``lore_ref`` → ``drifted=False``); any other key is absent from the returned
    set (the referenced chunk was deleted → ``drifted=True``). ONE call resolves
    drift for EVERY ref in a recall.

    Records :attr:`calls` (how many times it was invoked) and :attr:`last_keys`
    (the keys of the most recent call) so a test can PROVE a recall resolves all
    its refs in a single batched call rather than one lookup per ref.
    """

    def __init__(self, existing: set[str] | None = None) -> None:
        self._existing = set(existing or ())
        self.calls = 0
        self.last_keys: set[str] = set()

    async def __call__(self, chunk_keys: Sequence[str]) -> set[str]:
        self.calls += 1
        self.last_keys = set(chunk_keys)
        return {chunk_key for chunk_key in chunk_keys if chunk_key in self._existing}


class CountingEmbedder(FakeEmbedder):
    """A :class:`FakeEmbedder` that tallies document-side embed calls.

    The spy oracle for the boot-path divergence guard (mirrors
    ``test_memory_durability.CountingEmbedder``): a ``restore_from_ledger`` that
    needlessly re-embeds every memory on every boot is a real bug, and the only
    way to prove "embedded nothing" is to watch the embedder. Subclasses the
    shipped fake so determinism / normalization / dim are unchanged; it only
    counts. ``recall`` embeds query-side (:meth:`embed_query`, uncounted), so the
    tally reflects ONLY the document embeds a save/restore performs.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.documents_embedded = 0

    async def embed_documents(self, texts: list[str]) -> EmbedResult:
        self.documents_embedded += len(texts)
        return await super().embed_documents(texts)


def now_utc() -> datetime:
    """Current wall-clock time, timezone-aware (UTC) — the recall/expiry anchor."""
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Fixtures — ONE backend factory routes every test (fake-parity ready).
# ---------------------------------------------------------------------------


@pytest.fixture()
def ledger_path(tmp_path: Path) -> str:
    """A throwaway SQLite ledger path on a tmp volume (mirrors the state-dir layout)."""
    return str(tmp_path / "lore_test.memory.db")


@pytest_asyncio.fixture()
async def embedder() -> FakeEmbedder:
    """The shipped deterministic embedder at the production dim (== the harness dim)."""
    return FakeEmbedder(dim=PRODUCTION_DIM)


@pytest_asyncio.fixture(params=["real", "fake"])
async def make_backend(
    request: pytest.FixtureRequest,
    embedder: FakeEmbedder,
    ledger_path: str,
) -> AsyncIterator[BackendFactory]:
    """Yield an async factory that builds ready backends — parametrized over
    BOTH the real SurrealDB-backed ``LocalMemoryBackend`` and the adversarial
    in-memory ``FakeMemoryBackend`` (``_memory_fakes.py``).

    THE single construction seam every test in this module routes through (no
    test builds a backend inline) — the fake-vs-real PARITY PIN: a behaviour
    the fake gets wrong, or too friendly, shows up as a real-vs-fake
    divergence rather than a fake-only green.

    The ``"real"`` branch deliberately does NOT depend on the ``surreal_env``
    pytest fixture (see the import block's comment for why) — it wires a
    backend against a per-test isolated SurrealDB database built the same way
    ``surreal_env`` builds one, the deterministic embedder, a ``tmp_path``
    ledger, and a fake chunk oracle. Overridable knobs let a test point at a
    dead URL (the durability seam), inject a specific oracle (the drift seam),
    swap in a call-counting embedder (the divergence-guard seam), share a
    ledger, or skip ``ensure_ready``.

    The ``"fake"`` branch never touches SurrealDB at all: it builds a
    :class:`~_memory_fakes.FakeMemoryBackend` honouring the SAME knobs.
    ``url=_DEAD_URL`` is the only url this suite ever passes deliberately (the
    durability seam); this fixture derives the fake's ``store_unreachable``
    flag from that comparison — a constructor flag, never a probe.

    Every built backend is closed on exit; the "real" branch also reaps its
    throwaway database.
    """
    created: list[LocalMemoryBackend] = []

    if request.param == "real":
        env: SurrealEnv = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        setup_connection = await connect_admin(env)
        await setup_connection.close()

        async def _factory(
            *,
            url: str | None = None,
            ledger: MemoryLedger | None = None,
            chunk_oracle: FakeChunkOracle | None = None,
            embedder_override: FakeEmbedder | None = None,
            ensure: bool = True,
        ) -> LocalMemoryBackend:
            active_ledger = ledger if ledger is not None else MemoryLedger(ledger_path)
            oracle = chunk_oracle if chunk_oracle is not None else FakeChunkOracle()
            backend = LocalMemoryBackend(
                url=url if url is not None else env.url,
                namespace=env.namespace,
                database=env.database,
                dim=env.dim,
                user=env.user,
                password=env.password,
                embedder=embedder_override if embedder_override is not None else embedder,
                existing_chunks=oracle,
                ledger=active_ledger,
            )
            created.append(backend)
            if ensure:
                await backend.ensure_ready()
            return backend
    else:

        async def _factory(
            *,
            url: str | None = None,
            ledger: MemoryLedger | None = None,
            chunk_oracle: FakeChunkOracle | None = None,
            embedder_override: FakeEmbedder | None = None,
            ensure: bool = True,
        ) -> LocalMemoryBackend:
            active_ledger = ledger if ledger is not None else MemoryLedger(ledger_path)
            oracle = chunk_oracle if chunk_oracle is not None else FakeChunkOracle()
            fake_backend = FakeMemoryBackend(
                embedder=embedder_override if embedder_override is not None else embedder,
                existing_chunks=oracle,
                ledger=active_ledger,
                store_unreachable=(url == _DEAD_URL),
                url=url or "",
            )
            # A FakeMemoryBackend satisfies LocalMemoryBackend's behavioural
            # contract (that IS this parity pin); it shares no base class with
            # the real backend, so the cast tells mypy what the test suite
            # proves (mirrors ``_task_fakes.py``'s ``cast(TaskLedger, ...)``).
            typed_backend = cast(LocalMemoryBackend, fake_backend)
            created.append(typed_backend)
            if ensure:
                await typed_backend.ensure_ready()
            return typed_backend

    try:
        yield _factory
    finally:
        for backend in created:
            # Teardown must tolerate a never-connected backend (the dead-URL seam
            # test builds one that never opened a socket).
            await backend.close()
        if request.param == "real":
            await drop_database(env)


@pytest_asyncio.fixture()
async def memory_backend(make_backend: BackendFactory) -> LocalMemoryBackend:
    """A ready ``LocalMemoryBackend`` over a fresh isolated db (the common case)."""
    return await make_backend()


# ---------------------------------------------------------------------------
# Reusable recall helpers (backend-mediated observability).
# ---------------------------------------------------------------------------


async def stored_by_text(
    backend: LocalMemoryBackend,
    text: str,
    *,
    include: str | None = "superseded",
    k: int = _READ_ALL,
) -> RecalledMemory | None:
    """Fetch the single stored item whose ``text`` matches (or ``None``).

    Defaults to ``include="superseded"`` so it can read a NON-live row
    (invalidated/superseded) for its audit fields. FakeEmbedder is deterministic:
    a query equal to the note text embeds to that note's vector, so the note is
    the top hit and is returned within any generous ``k``.
    """
    items = await backend.recall(text, k=k, include=include)
    matches = [item for item in items if item.text == text]
    return matches[0] if matches else None


async def count_by_text(
    backend: LocalMemoryBackend, text: str, *, include: str | None = "superseded"
) -> int:
    """Count stored rows whose ``text`` matches — the dedup/duplication oracle.

    Counting by TEXT (not id) catches the real duplication bug: a
    non-deterministic id would produce two rows with the SAME text but DIFFERENT
    ids, which counting by id would miss.
    """
    items = await backend.recall(text, k=_READ_ALL, include=include)
    return sum(1 for item in items if item.text == text)


# ===========================================================================
# Test classes
# ===========================================================================


class TestWireVocabulary:
    """The Spectron-derived wire models: ``MemorySource`` + the trust ENUM.

    Pins that ``trust`` is the Literal enum ``{"authoritative","experiential"}``
    (default ``"experiential"``), NOT the P2 schema's wrong float column — a
    float or an out-of-vocabulary string must be REJECTED, loudly.
    """

    def test_memory_source_defaults_trust_to_experiential(self) -> None:
        source = MemorySource(kind="operator")
        # An operator note is experiential unless explicitly marked authoritative.
        assert source.trust == "experiential"
        # ``ref`` is an optional provenance pointer, absent by default.
        assert source.ref is None

    def test_memory_source_accepts_authoritative_trust(self) -> None:
        source = MemorySource(kind="spec", ref="docs/plan.md#p7", trust="authoritative")
        assert source.trust == "authoritative"
        assert source.kind == "spec"
        assert source.ref == "docs/plan.md#p7"

    def test_memory_source_rejects_float_trust(self) -> None:
        # The P2 schema stored ``trust`` as a FLOAT; that was wrong. A float must
        # be a validation error now — trust is a two-value enum, not a score.
        with pytest.raises(ValidationError):
            MemorySource(kind="operator", trust=0.5)  # type: ignore[arg-type]

    def test_memory_source_rejects_unknown_trust_string(self) -> None:
        with pytest.raises(ValidationError):
            MemorySource(kind="operator", trust="trusted")  # type: ignore[arg-type]


class TestBackendSurface:
    """The local backend structurally satisfies the ``MemoryBackend`` protocol."""

    async def test_local_backend_exposes_the_protocol_methods(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        # The async surface the callers depend on — a missing method is a broken
        # contract before any behavioural test even runs.
        for method in ("remember", "invalidate", "recall", "restore_from_ledger"):
            assert callable(getattr(memory_backend, method)), f"missing backend.{method}"
        # The durable ledger is reachable for restore/replay (FP-06 reuse).
        assert memory_backend.ledger is not None


class TestIdempotentIds:
    """Memory ids are ``uuid5`` content-derived and BACKWARD-COMPATIBLE.

    The ledger replay must re-mint identical ids, so the id folds in the note
    text + the sorted stamp of its ``lore_ref`` labels (default version =
    :data:`DEFAULT_KEY_VERSION`), and NOTHING else. Pins the literal uuids, the
    text↔id and label↔id seams, and the "one row" dedup.
    """

    def test_convention_reconstruction_matches_the_pinned_literals(self) -> None:
        # The independent reconstruction agrees with the hand-computed literals —
        # a guard on the convention itself before any backend is involved. The
        # default-version case uses the SHARED ``DEFAULT_KEY_VERSION`` (clause 5).
        assert expected_memory_id(PG_NOTE) == _LITERAL_ID_NO_REFS
        assert (
            expected_memory_id(PG_NOTE, [(PINNED_CHUNK_KEY, DEFAULT_KEY_VERSION)])
            == _LITERAL_ID_REF_V1
        )
        assert expected_memory_id(PG_NOTE, [(PINNED_CHUNK_KEY, 3)]) == _LITERAL_ID_REF_V3

    async def test_remember_mints_the_conventional_id_no_refs(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        returned_id = await memory_backend.remember(PG_NOTE, kind="gotcha")
        # The backend mints the SAME id the v0.3 ledger convention produces — the
        # backward-compat pin (independent oracle = the literal).
        assert returned_id == expected_memory_id(PG_NOTE) == _LITERAL_ID_NO_REFS

    async def test_bare_lore_ref_label_folds_default_version_into_the_id(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        # A bare ``lore_ref=<key>`` (no @version) must stamp DEFAULT_KEY_VERSION
        # into the id — the label→refs_stamp→id seam with the shared default.
        returned_id = await memory_backend.remember(
            PG_NOTE, kind="fact", labels=[lore_ref_label(PINNED_CHUNK_KEY)]
        )
        assert returned_id == _LITERAL_ID_REF_V1

    async def test_versioned_lore_ref_label_folds_that_version_into_the_id(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        returned_id = await memory_backend.remember(
            PG_NOTE, kind="fact", labels=[lore_ref_label(PINNED_CHUNK_KEY, 3)]
        )
        assert returned_id == _LITERAL_ID_REF_V3

    async def test_same_text_different_lore_ref_is_a_distinct_memory(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        # Same prose pointing at a DIFFERENT chunk is a genuinely different memory
        # (two corrections), never a clobber — the refs are folded into the id.
        id_a = await memory_backend.remember(
            PG_NOTE, kind="fact", labels=[lore_ref_label("mod:a.py:symbol:A:0")]
        )
        id_b = await memory_backend.remember(
            PG_NOTE, kind="fact", labels=[lore_ref_label("mod:b.py:symbol:B:0")]
        )
        assert id_a != id_b

    async def test_non_lore_ref_labels_do_not_affect_the_id(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        # A plain ``key=value`` label is metadata, NOT a chunk ref — it must not
        # change the deterministic id (else dedup silently breaks).
        id_labelled = await memory_backend.remember(
            PG_NOTE, kind="fact", labels=["team=infra", "topic=postgres"]
        )
        id_bare = await memory_backend.remember(PG_NOTE, kind="fact")
        assert id_labelled == id_bare == _LITERAL_ID_NO_REFS

    async def test_remember_twice_yields_one_row_latest_write_wins(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        # Idempotency: identical (text, lore_refs) twice → same id AND exactly one
        # stored row (count by TEXT catches a non-deterministic-id duplicate).
        first_id = await memory_backend.remember(KIND_NOTES["fact"], kind="fact")
        second_id = await memory_backend.remember(KIND_NOTES["fact"], kind="fact")
        assert first_id == second_id
        assert await count_by_text(memory_backend, KIND_NOTES["fact"]) == 1


class TestRemember:
    """``remember`` — kind defaults, the ongoing TTL, importance, source round-trip."""

    async def test_importance_defaults_by_kind(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        # Each kind's default importance == the P7 plan (INDEPENDENT literals, not
        # the impl's table). ``recall(note, k=1)`` returns ONLY that note (exact
        # cosine-1.0 hit) at its PRISTINE importance — the reinforcement bump is a
        # side effect visible only on a SUBSEQUENT recall, so this first read sees
        # the untouched default.
        for kind in MEMORY_KINDS:
            note = KIND_NOTES[kind]
            await memory_backend.remember(note, kind=kind)
            recalled = await memory_backend.recall(note, k=1)
            assert recalled, f"a {kind} memory must be recallable"
            assert recalled[0].importance == pytest.approx(REQUIRED_IMPORTANCE_BY_KIND[kind])
            # Sanity bound on the derived score (clause 4): importance ∈ [0, 1].
            assert 0.0 <= recalled[0].importance <= 1.0

    async def test_explicit_importance_overrides_the_kind_default(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        override = 0.95  # a caller-supplied weight, independent of the 0.5 fact default
        note = "This deploy gotcha is unusually critical — pin it high."
        await memory_backend.remember(note, kind="fact", importance=override)
        recalled = await memory_backend.recall(note, k=1)
        assert recalled[0].importance == pytest.approx(override)

    async def test_importance_out_of_range_is_rejected(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        # ``importance`` is a fraction in [0, 1]; a value outside that is a caller
        # error (server-side input validation). pydantic's ValidationError is a
        # subclass of ValueError, so this covers either implementation style.
        with pytest.raises(ValueError, match="(?i)importance"):
            await memory_backend.remember("too hot", kind="fact", importance=1.5)
        with pytest.raises(ValueError, match="(?i)importance"):
            await memory_backend.remember("too cold", kind="fact", importance=-0.1)

    async def test_ongoing_without_expiry_gets_the_default_ttl(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        # An ``ongoing`` memory with no explicit ``expires_at`` expires 7 days
        # after creation (P7 plan). Independent oracle: the span between the stored
        # ``created_at`` and ``expires_at`` ≈ 7 days (magnitude bound, clause 4) —
        # asserted against the requirement's timedelta, not the impl's constant.
        note = KIND_NOTES["ongoing"]
        await memory_backend.remember(note, kind="ongoing")
        recalled = await memory_backend.recall(note, k=1)
        item = recalled[0]
        assert item.expires_at is not None, "an ongoing memory gets a default TTL"
        ttl = item.expires_at - item.created_at
        # Within a comfortable margin of exactly 7 days (wall-clock processing slack).
        assert abs(ttl - REQUIRED_ONGOING_TTL) < timedelta(minutes=5)
        # And bounded well away from an order-of-magnitude error (hours, or months).
        assert timedelta(days=6) < ttl < timedelta(days=8)

    async def test_non_ongoing_kinds_default_to_no_expiry(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        # A plain fact does not silently acquire the ongoing TTL — it lives until
        # explicitly invalidated/superseded.
        note = KIND_NOTES["fact"]
        await memory_backend.remember(note, kind="fact")
        recalled = await memory_backend.recall(note, k=1)
        assert recalled[0].expires_at is None

    async def test_source_round_trips_through_the_backend(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        # The provenance seam: a caller-supplied MemorySource survives the write
        # and comes back on recall unmangled — kind, ref, AND the trust enum.
        source = MemorySource(kind="operator", ref="chat:2026-07-04", trust="authoritative")
        note = "Operator confirmed: never write through the read-only snapshot root."
        await memory_backend.remember(note, kind="decision", source=source)
        recalled = await memory_backend.recall(note, k=1)
        got = recalled[0].source
        assert got.kind == "operator"
        assert got.ref == "chat:2026-07-04"
        assert got.trust == "authoritative"


class TestSupersession:
    """``remember(supersedes=<old>)`` — the audit-trail supersession chain.

    The old row is KEPT (audit), stamped ``valid_until=now`` + ``superseded_by``;
    the new row carries ``supersedes``. Superseding an unknown id is a typed error.
    """

    async def test_superseding_keeps_the_old_row_and_wires_both_directions(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        old_note = "Default context length is 512 for TimesFM fine-tuning."
        new_note = "Correction: the official TimesFM 2.5 default context length is 64."
        old_id = await memory_backend.remember(old_note, kind="fact")
        new_id = await memory_backend.remember(new_note, kind="fact", supersedes=old_id)

        # The OLD row is retained (audit trail), no longer live, and points FORWARD
        # to its successor.
        old_row = await stored_by_text(memory_backend, old_note, include="superseded")
        assert old_row is not None, "the superseded row must be kept for audit"
        assert old_row.valid_until is not None, "a superseded row is closed at now"
        assert old_row.superseded_by == new_id

        # The NEW row is live and points BACK to what it replaced.
        new_row = await stored_by_text(memory_backend, new_note, include=None)
        assert new_row is not None, "the successor must be live"
        assert new_row.valid_until is None
        assert new_row.supersedes == old_id

    async def test_default_recall_excludes_the_superseded_old_row(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        old_note = "Backups land in /backups/odoo as directory-format dumps."
        new_note = "Backups now land as .tar.gz + .sha512 (format change 2026-04-17)."
        old_id = await memory_backend.remember(old_note, kind="fact")
        await memory_backend.remember(new_note, kind="fact", supersedes=old_id)

        # Live-only default recall must NOT surface the retired note.
        live = await memory_backend.recall(old_note, k=_READ_ALL)
        assert all(item.text != old_note for item in live)

    async def test_superseding_a_nonexistent_id_raises_not_found(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        unknown_id = str(uuid.uuid4())
        with pytest.raises(MemoryNotFoundError):
            await memory_backend.remember(
                "orphan successor", kind="fact", supersedes=unknown_id
            )


class TestInvalidateWithoutSuccessor:
    """``invalidate`` — retire a memory with NO replacement.

    Sets ``valid_until=now`` but leaves ``superseded_by`` None (no successor); the
    row is kept and distinguishable, default recall drops it, unknown id is typed.
    """

    async def test_invalidate_closes_the_row_without_a_successor(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        note = "The staging TEI endpoint is up at mbpsrv (temporary)."
        memory_id = await memory_backend.remember(note, kind="fact")

        await memory_backend.invalidate(memory_id)

        row = await stored_by_text(memory_backend, note, include="superseded")
        assert row is not None, "an invalidated row is kept, distinguishable"
        assert row.valid_until is not None, "invalidate closes the validity window"
        # No successor: this is retirement, not supersession.
        assert row.superseded_by is None

    async def test_default_recall_excludes_an_invalidated_memory(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        note = "Feature flag X is enabled in prod."
        memory_id = await memory_backend.remember(note, kind="fact")
        await memory_backend.invalidate(memory_id)

        live = await memory_backend.recall(note, k=_READ_ALL)
        assert all(item.text != note for item in live)

    async def test_invalidate_unknown_id_raises_not_found(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        with pytest.raises(MemoryNotFoundError):
            await memory_backend.invalidate(str(uuid.uuid4()))


class TestRecallFiltering:
    """``recall`` filtering — live-only default, include, as_of, labels, k, lens."""

    async def test_default_recall_returns_a_live_memory(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        note = KIND_NOTES["gotcha"]
        await memory_backend.remember(note, kind="gotcha")
        recalled = await memory_backend.recall(note, k=_READ_ALL)
        assert any(item.text == note for item in recalled)

    async def test_include_superseded_returns_the_retired_row_distinguishably(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        note = "Old convention: mount the PG volume at /var/lib/postgresql/data."
        memory_id = await memory_backend.remember(note, kind="fact")
        await memory_backend.invalidate(memory_id)

        # Default: absent. include="superseded": present AND carries its audit
        # fields so the caller can tell it apart from a live row.
        assert all(i.text != note for i in await memory_backend.recall(note, k=_READ_ALL))
        with_retired = await memory_backend.recall(note, k=_READ_ALL, include="superseded")
        retired = next(i for i in with_retired if i.text == note)
        assert retired.valid_until is not None

    async def test_expired_memory_is_dropped_from_default_recall(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        # The expires_at gate: a memory whose expiry is already in the PAST is not
        # live and must not surface on the default path.
        past = now_utc() - _CLOCK_MARGIN
        note = "Temporary: pin the harness to the 3.1.5 image for this sprint."
        await memory_backend.remember(note, kind="fact", expires_at=past)
        live = await memory_backend.recall(note, k=_READ_ALL)
        assert all(item.text != note for item in live)

    async def test_unexpired_memory_is_kept_in_default_recall(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        future = now_utc() + _CLOCK_MARGIN
        note = "Reminder: the invite waitlist decision is pending until next week."
        await memory_backend.remember(note, kind="fact", expires_at=future)
        live = await memory_backend.recall(note, k=_READ_ALL)
        assert any(item.text == note for item in live)

    async def test_as_of_recalls_a_row_live_only_within_its_window(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        # Temporal recall: a row whose window [valid_from, valid_until) CONTAINS T
        # is returned for as_of=T even though it is no longer live now. Independent
        # anchors: T is derived from the row's OWN observed timestamps, never a
        # hardcoded clock or the impl's formula.
        old_note = "Chose Qdrant for the memory store."
        new_note = "Superseded: memory store moved to SurrealDB (unification)."
        old_id = await memory_backend.remember(old_note, kind="decision")
        # A measurable window so its midpoint is strictly interior.
        await asyncio.sleep(0.05)
        await memory_backend.remember(new_note, kind="decision", supersedes=old_id)

        closed = await stored_by_text(memory_backend, old_note, include="superseded")
        assert closed is not None and closed.valid_until is not None
        midpoint = closed.valid_from + (closed.valid_until - closed.valid_from) / 2

        # Inside the window → the retired note IS returned for that instant.
        at_mid = await memory_backend.recall(old_note, k=_READ_ALL, as_of=midpoint)
        assert any(item.text == old_note for item in at_mid)

        # After the window closed → the retired note is gone; its successor stands.
        after = closed.valid_until + timedelta(seconds=1)
        at_after = await memory_backend.recall(old_note, k=_READ_ALL, as_of=after)
        assert all(item.text != old_note for item in at_after)

    async def test_labels_filter_uses_all_semantics(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        note = "Deploy note tagged for the infra team's security review."
        await memory_backend.remember(
            note, kind="gotcha", labels=["team=infra", "topic=security"]
        )

        # A subset of the row's labels matches (every requested label present).
        assert any(
            i.text == note
            for i in await memory_backend.recall(note, k=_READ_ALL, labels=["team=infra"])
        )
        # ALL requested labels present → match.
        assert any(
            i.text == note
            for i in await memory_backend.recall(
                note, k=_READ_ALL, labels=["team=infra", "topic=security"]
            )
        )
        # One requested label absent → NO match (ALL semantics, not ANY).
        assert all(
            i.text != note
            for i in await memory_backend.recall(
                note, k=_READ_ALL, labels=["team=infra", "topic=billing"]
            )
        )

    async def test_recall_respects_the_k_cap(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        for index in range(6):
            await memory_backend.remember(f"distinct deploy note number {index}", kind="fact")
        recalled = await memory_backend.recall("deploy note", k=2)
        assert len(recalled) <= 2

    async def test_recall_with_a_lens_raises_unsupported(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        # ``lens`` is NOT supported by the local backend in P7 — it must fail
        # LOUDLY (naming lens), never silently ignore the argument.
        await memory_backend.remember(KIND_NOTES["fact"], kind="fact")
        with pytest.raises(ValueError, match="(?i)lens"):
            await memory_backend.recall(KIND_NOTES["fact"], lens="odoo")

    async def test_recall_top_hit_outscores_a_distractor(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        # Ranking sanity (clause 4, distribution-based bound on the derived score):
        # the exact-text query embeds to the target's vector (cosine 1.0), so it
        # must score >= any other returned memory — independent of the metric's
        # absolute range.
        target = "Reconcile divergence at startup before serving the index."
        distractor = "The kitchen faucet drips on alternate Tuesdays."
        await memory_backend.remember(target, kind="fact")
        await memory_backend.remember(distractor, kind="fact")
        recalled = await memory_backend.recall(target, k=_READ_ALL)
        assert recalled
        top = recalled[0]
        assert top.text == target
        assert all(top.score >= item.score for item in recalled)


    async def test_kind_filter_returns_only_that_kind(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        # Two lexically CLOSE notes (same "Deploy note: the retry budget"
        # opening) so the exclusion below is genuinely the KIND filter's doing,
        # never just the ranking pushing the wrong-kind note out of the window.
        gotcha_note = "Deploy note: the retry budget bug is a real gotcha for on-call."
        fact_note = "Deploy note: the retry budget is 3 attempts by design."
        await memory_backend.remember(gotcha_note, kind="gotcha")
        await memory_backend.remember(fact_note, kind="fact")

        # ``kind`` does not exist on LocalMemoryBackend.recall's TYPED signature
        # yet (this wave's RED); routed via getattr so the RED stays behavioural
        # (a runtime TypeError) rather than a static typecheck failure -- the
        # SAME dynamic-access convention this wave's other new-param pins use.
        recalled = await getattr(memory_backend, "recall")(
            gotcha_note, k=_READ_ALL, kind="gotcha"
        )

        assert any(item.text == gotcha_note for item in recalled), (
            "kind='gotcha' must surface a live gotcha-kind memory"
        )
        assert all(item.text != fact_note for item in recalled), (
            "kind='gotcha' must exclude a live fact-kind memory even though the "
            "two notes are lexically close enough to both rank within k"
        )

    async def test_kind_filter_combines_with_labels_as_an_intersection(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        # kind="gotcha" ALONE would also match wrong_label_same_kind;
        # labels=["team=infra"] ALONE would also match wrong_kind_same_label --
        # only ``target`` (matching BOTH) may survive the intersection.
        target = "Deploy note tagged infra, a gotcha about the security review."
        wrong_kind_same_label = "Deploy note tagged infra, a plain fact about the review."
        wrong_label_same_kind = "Deploy note tagged billing, a gotcha about a different review."
        await memory_backend.remember(target, kind="gotcha", labels=["team=infra"])
        await memory_backend.remember(
            wrong_kind_same_label, kind="fact", labels=["team=infra"]
        )
        await memory_backend.remember(
            wrong_label_same_kind, kind="gotcha", labels=["team=billing"]
        )

        # Same dynamic-access rationale as above: ``kind`` is not yet on the
        # typed signature.
        recalled = await getattr(memory_backend, "recall")(
            target, k=_READ_ALL, kind="gotcha", labels=["team=infra"]
        )

        assert any(item.text == target for item in recalled), (
            "the note matching BOTH kind and labels must be returned"
        )
        assert all(item.text != wrong_kind_same_label for item in recalled), (
            "a matching label but wrong kind must be excluded (intersection, not union)"
        )
        assert all(item.text != wrong_label_same_kind for item in recalled), (
            "a matching kind but wrong label must be excluded (intersection, not union)"
        )


class TestReinforcementOnRecall:
    """Recall reinforces: a returned memory's stored importance bumps by the step.

    The bump is a SIDE EFFECT visible on a SUBSEQUENT read (the current recall
    returns the pre-bump value), it persists, and it caps at 1.0. Decay is v1.1
    (out of scope).
    """

    async def test_bump_persists_and_is_visible_on_the_next_recall(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        note = KIND_NOTES["fact"]  # default importance 0.5
        await memory_backend.remember(note, kind="fact")

        first = (await memory_backend.recall(note, k=1))[0]
        second = (await memory_backend.recall(note, k=1))[0]
        third = (await memory_backend.recall(note, k=1))[0]

        base = REQUIRED_IMPORTANCE_BY_KIND["fact"]
        step = REQUIRED_REINFORCEMENT_STEP
        # First read = pristine; each subsequent read shows the persisted bump from
        # the prior recall. Independent oracle: 0.5, 0.55, 0.60 (plan base + step).
        assert first.importance == pytest.approx(base)
        assert second.importance == pytest.approx(base + step)
        assert third.importance == pytest.approx(base + 2 * step)

    async def test_reinforcement_caps_at_one(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        note = KIND_NOTES["decision"]  # default importance 0.9
        await memory_backend.remember(note, kind="decision")

        # Recall enough times to drive it past the ceiling: 0.9 → 0.95 → 1.0 → 1.0…
        observed = [(await memory_backend.recall(note, k=1))[0].importance for _ in range(6)]

        assert max(observed) <= 1.0, "importance must never exceed 1.0"
        assert observed[-1] == pytest.approx(1.0), "reinforcement caps at 1.0"


class TestDriftDetection:
    """Recall flags a ``lore_ref`` whose chunk no longer exists — NEVER filters it.

    Each recalled ref is checked against the injected chunk-existence oracle: a
    live chunk → ``drifted=False``; a deleted chunk → ``drifted=True``. Drift is a
    FLAG, not a filter — the memory is still returned so the caller sees the stale
    correction.
    """

    async def test_existing_chunk_ref_is_not_drifted(
        self, make_backend: BackendFactory
    ) -> None:
        backend = await make_backend(chunk_oracle=FakeChunkOracle({EXISTING_CHUNK_KEY}))
        note = "This chunk still exists; the ref is live."
        await backend.remember(note, kind="fact", labels=[lore_ref_label(EXISTING_CHUNK_KEY)])
        recalled = await backend.recall(note, k=1)
        ref = recalled[0].refs[0]
        assert ref.chunk_key == EXISTING_CHUNK_KEY
        assert ref.drifted is False

    async def test_missing_chunk_ref_is_flagged_drifted_but_still_returned(
        self, make_backend: BackendFactory
    ) -> None:
        # Oracle knows the EXISTING key but NOT the missing one.
        backend = await make_backend(chunk_oracle=FakeChunkOracle({EXISTING_CHUNK_KEY}))
        note = "This correction points at a chunk a refactor deleted."
        await backend.remember(note, kind="gotcha", labels=[lore_ref_label(MISSING_CHUNK_KEY)])

        recalled = await backend.recall(note, k=_READ_ALL)
        # Drift NEVER filters — the memory is still recalled.
        item = next(i for i in recalled if i.text == note)
        assert item.refs[0].chunk_key == MISSING_CHUNK_KEY
        assert item.refs[0].drifted is True


class TestDriftBatchSemantics:
    """The per-ref drift semantics recall preserves EXACTLY across MULTIPLE
    recalled rows that SHARE a ref key — fresh / drifted / duplicate-key.

    This pins the behaviour the single-query batch drift resolution must
    reproduce ref-for-ref: a recall over N rows bearing M refs (some duplicated
    across rows) must flag each occurrence identically to the one-ref-at-a-time
    check. Behaviour-only (asserts the recalled ``drifted`` flags through the
    public recall surface), so it is green whether drift is resolved
    per-ref or in ONE batched oracle call — the invariant the refactor keeps.
    """

    _FRESH_KEY = "loremaster:loremaster/store/surreal.py:symbol:SurrealStore:0"
    _GONE_KEY = "loremaster:loremaster/store/gone.py:symbol:Removed:0"
    _GONE_KEY_2 = "loremaster:loremaster/index/gone.py:symbol:AlsoRemoved:0"

    async def test_mixed_fresh_and_drifted_refs_across_rows_sharing_a_key(
        self, make_backend: BackendFactory
    ) -> None:
        # The oracle knows ONLY the fresh key; every other ref has drifted.
        backend = await make_backend(chunk_oracle=FakeChunkOracle({self._FRESH_KEY}))
        fresh_note = "Row whose single ref still exists."
        gone_note = "Row whose single ref a refactor deleted."
        mixed_note = "Row carrying one live ref and one deleted ref."
        await backend.remember(
            fresh_note, kind="fact", labels=[lore_ref_label(self._FRESH_KEY)]
        )
        await backend.remember(
            gone_note, kind="gotcha", labels=[lore_ref_label(self._GONE_KEY)]
        )
        # The fresh key is DUPLICATED here (shared with the fresh row) — one
        # membership test per unique key must still flag each occurrence right.
        await backend.remember(
            mixed_note,
            kind="fact",
            labels=[lore_ref_label(self._FRESH_KEY), lore_ref_label(self._GONE_KEY_2)],
        )

        recalled = {item.text: item for item in await backend.recall("row ref", k=_READ_ALL)}

        # fresh: the live chunk → not drifted.
        assert [(ref.chunk_key, ref.drifted) for ref in recalled[fresh_note].refs] == [
            (self._FRESH_KEY, False)
        ]
        # drifted: the deleted chunk → flagged True, but STILL recalled.
        assert [(ref.chunk_key, ref.drifted) for ref in recalled[gone_note].refs] == [
            (self._GONE_KEY, True)
        ]
        # mixed: the shared fresh key stays not-drifted; the second key drifted.
        assert {ref.chunk_key: ref.drifted for ref in recalled[mixed_note].refs} == {
            self._FRESH_KEY: False,
            self._GONE_KEY_2: True,
        }

    async def test_recall_resolves_all_refs_in_a_single_oracle_call(
        self, make_backend: BackendFactory
    ) -> None:
        # THE batching invariant: N refs across the recalled rows → ONE oracle
        # call, carrying the UNIQUE set of ref keys (the duplicated fresh key is
        # de-duplicated to a single membership test).
        oracle = FakeChunkOracle({self._FRESH_KEY})
        backend = await make_backend(chunk_oracle=oracle)
        await backend.remember(
            "Row A — fresh ref.", kind="fact", labels=[lore_ref_label(self._FRESH_KEY)]
        )
        await backend.remember(
            "Row B — drifted ref.", kind="gotcha", labels=[lore_ref_label(self._GONE_KEY)]
        )
        await backend.remember(
            "Row C — one shared fresh ref plus one drifted ref.",
            kind="fact",
            labels=[lore_ref_label(self._FRESH_KEY), lore_ref_label(self._GONE_KEY_2)],
        )

        recalled = await backend.recall("row ref", k=_READ_ALL)

        # Every row that carries refs was still recalled (drift never filters).
        assert sum(len(item.refs) for item in recalled) == 4
        # ONE call resolved all refs — not one lookup per ref (four ref occurrences).
        assert oracle.calls == 1
        # ...and it received exactly the UNIQUE ref keys across all recalled rows.
        assert oracle.last_keys == {self._FRESH_KEY, self._GONE_KEY, self._GONE_KEY_2}


class TestRecallRefsAndLabels:
    """Recalled refs are the (chunk_key, key_version) shape the search pipeline eats.

    A bare ``lore_ref`` label yields a ref at the shared default version; a
    versioned one yields that version; non-lore_ref labels stay in ``labels`` and
    never appear as refs.
    """

    async def test_bare_lore_ref_recalls_at_the_default_key_version(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        note = "Correction with a bare (unversioned) lore_ref label."
        await memory_backend.remember(
            note, kind="fact", labels=[lore_ref_label("mod:x.py:symbol:X:0")]
        )
        ref = (await memory_backend.recall(note, k=1))[0].refs[0]
        assert ref.chunk_key == "mod:x.py:symbol:X:0"
        # The consumer side of the shared default-version convention (clause 5).
        assert ref.key_version == DEFAULT_KEY_VERSION

    async def test_versioned_lore_ref_recalls_that_key_version(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        note = "Correction with a versioned lore_ref label (post keying bump)."
        await memory_backend.remember(
            note, kind="fact", labels=[lore_ref_label("mod:x.py:symbol:X:0", 3)]
        )
        ref = (await memory_backend.recall(note, k=1))[0].refs[0]
        assert ref.key_version == 3

    async def test_non_lore_ref_labels_are_labels_not_refs(
        self, memory_backend: LocalMemoryBackend
    ) -> None:
        note = "A memory carrying both a chunk ref and a plain team label."
        await memory_backend.remember(
            note,
            kind="fact",
            labels=["team=infra", lore_ref_label("mod:x.py:symbol:X:0", 2)],
        )
        item = (await memory_backend.recall(note, k=1))[0]
        # Exactly one ref (the lore_ref), and the plain label rode ``labels`` only.
        assert len(item.refs) == 1
        assert item.refs[0].chunk_key == "mod:x.py:symbol:X:0"
        assert "team=infra" in item.labels


class TestDurabilityWriteThrough:
    """FP-06 port — the ledger row lands FIRST, surviving a Surreal failure.

    ``remember`` writes the durable ledger row before the volatile Surreal row.
    Proven by pointing the backend at a DEAD SurrealDB URL: the store write raises,
    but the ledger already kept the memory (zero loss), so a later restore can
    re-embed it.
    """

    async def test_ledger_row_persists_when_the_surreal_side_is_unreachable(
        self, make_backend: BackendFactory, ledger_path: str
    ) -> None:
        ledger = MemoryLedger(ledger_path)
        # A backend whose SurrealDB is DOWN — never even connect (ensure=False).
        backend = await make_backend(url=_DEAD_URL, ledger=ledger, ensure=False)
        note = KIND_NOTES["gotcha"]

        # The Surreal-bound write must fail (unreachable server) — we assert the
        # SIDE EFFECT, not the exact exception type (impl-defined).
        with pytest.raises(Exception):
            await backend.remember(note, kind="gotcha")

        # DURABILITY: despite the store failure, the ledger kept the memory (the
        # write-through happened FIRST), keyed on the deterministic id.
        records = ledger.all_records()
        assert any(record.text == note for record in records), (
            "write-through must persist the ledger row before the Surreal write"
        )
        assert any(record.memory_id == expected_memory_id(note) for record in records)


class TestLedgerReplay:
    """``restore_from_ledger`` replays the ledger, guarded against needless re-embed.

    Semantics pinned: restore replays the ledger rows NOT already covered by the
    store and returns the count it actually replayed. Rows lacking v2 columns
    (pre-v2 ledger, metadata without a kind) default to ``kind="fact"``,
    ``trust="experiential"``, ``valid_until=None`` (live) — the plan-pinned
    defaults. Ids overwrite in place (no duplicates on a second pass).

    The BOOT-PATH DIVERGENCE GUARD (FP-06 parity with the old store's
    ``restore_if_diverged`` no-op) is load-bearing: once the store already covers
    the ledger, a further restore must return 0 and re-embed NOTHING — otherwise
    every boot needlessly re-embeds every memory. An empty ledger is likewise a
    pure no-op. Both are spy-pinned with a document-embed-counting embedder.
    """

    # A pair of pre-v2 ledger rows: durable prose with NO v2 wire metadata — the
    # "written by an older build" case the defaults exist for.
    _LEGACY_NOTES = (
        "hostname -I is GNU inetutils here; use ip -4 -o addr show scope global.",
        "cron env is stripped — set PATH explicitly or a wrong-major psql runs.",
    )

    @staticmethod
    def _seed_legacy_rows(ledger: MemoryLedger) -> list[str]:
        """Write pre-v2 ledger rows directly (bypassing ``remember``) and return ids.

        Uses the deterministic id + empty refs_stamp so a replay re-mints in place.
        The metadata is a plain author dict — NO ``kind``/``trust``/temporal
        columns — so the replay must supply the plan-pinned defaults.
        """
        ids: list[str] = []
        for note in TestLedgerReplay._LEGACY_NOTES:
            memory_id = expected_memory_id(note)
            ledger.record(
                memory_id=memory_id,
                text=note,
                metadata={"author": "operator"},
                refs_stamp="",
            )
            ids.append(memory_id)
        return ids

    async def test_replay_lands_pre_v2_rows_with_plan_pinned_defaults(
        self, make_backend: BackendFactory, ledger_path: str
    ) -> None:
        ledger = MemoryLedger(ledger_path)
        self._seed_legacy_rows(ledger)
        backend = await make_backend(ledger=ledger)

        await backend.restore_from_ledger()

        for note in self._LEGACY_NOTES:
            # A ledger-only memory is now recallable (replayed into Surreal), LIVE
            # (valid_until None → default recall returns it), with the pre-v2
            # defaults filled in.
            recalled = await backend.recall(note, k=_READ_ALL)
            item = next((i for i in recalled if i.text == note), None)
            assert item is not None, f"replay must make {note!r} recallable"
            assert item.kind == "fact", "a row lacking a kind defaults to fact"
            assert item.source.trust == "experiential", "default trust is experiential"

    async def test_replay_is_idempotent_second_pass_does_not_duplicate(
        self, make_backend: BackendFactory, ledger_path: str
    ) -> None:
        ledger = MemoryLedger(ledger_path)
        self._seed_legacy_rows(ledger)
        backend = await make_backend(ledger=ledger)

        await backend.restore_from_ledger()
        await backend.restore_from_ledger()

        # The deterministic id is the upsert key: two replays leave one row per
        # note (never doubled) — counted by TEXT across live + superseded.
        for note in self._LEGACY_NOTES:
            assert await count_by_text(backend, note) == 1

    async def test_replay_returns_the_number_of_ledger_rows(
        self, make_backend: BackendFactory, ledger_path: str
    ) -> None:
        ledger = MemoryLedger(ledger_path)
        seeded_ids = self._seed_legacy_rows(ledger)
        backend = await make_backend(ledger=ledger)

        restored = await backend.restore_from_ledger()

        # First replay reconstructs every durable row (independent oracle: the
        # count seeded directly into the ledger). The store started empty, so
        # "rows not already covered" == every seeded row.
        assert restored == len(seeded_ids)

    async def test_second_replay_when_in_sync_returns_zero_and_embeds_nothing(
        self, make_backend: BackendFactory, ledger_path: str
    ) -> None:
        # THE DIVERGENCE GUARD (FP-06 parity): once the store covers the ledger, a
        # further restore must be a pure no-op. Spy oracle: a document-embed
        # counter that must not move across the second call (recall embeds
        # query-side only, so it does not perturb the tally).
        ledger = MemoryLedger(ledger_path)
        self._seed_legacy_rows(ledger)
        counting_embedder = CountingEmbedder(dim=PRODUCTION_DIM)
        backend = await make_backend(ledger=ledger, embedder_override=counting_embedder)

        first_restored = await backend.restore_from_ledger()
        embeds_after_first = counting_embedder.documents_embedded
        # Sanity: the first pass DID embed the rows it reconstructed.
        assert first_restored == len(self._LEGACY_NOTES)
        assert embeds_after_first >= len(self._LEGACY_NOTES)

        second_restored = await backend.restore_from_ledger()

        # Now in sync: nothing to replay, nothing to embed.
        assert second_restored == 0, "restore must not re-replay rows the store already covers"
        assert counting_embedder.documents_embedded == embeds_after_first, (
            "a no-op restore must not re-embed a single document (else every boot re-embeds all)"
        )

    async def test_empty_ledger_replay_is_a_pure_noop(
        self, make_backend: BackendFactory
    ) -> None:
        # First boot on a fresh project: the ledger has zero rows, so restore has
        # nothing to do — return 0 and embed nothing (the inert baseline). Uses
        # the factory's default fresh (empty) ledger.
        counting_embedder = CountingEmbedder(dim=PRODUCTION_DIM)
        backend = await make_backend(embedder_override=counting_embedder)

        restored = await backend.restore_from_ledger()

        assert restored == 0
        assert counting_embedder.documents_embedded == 0, "an empty-ledger restore embeds nothing"


# ===========================================================================
# P8a-2 MOVE PARITY: the pure deterministic-id helpers moved OUT of the
# Qdrant-era ``MemoryStore`` (in loremaster/memory/store.py — classmethods
# ``_refs_stamp`` / ``_refs_from_stamp`` / ``_memory_id``) and INTO
# ``loremaster.memory.backend`` as module-level functions
# (``derive_refs_stamp`` / ``refs_from_stamp`` / ``derive_memory_id``), so the
# Qdrant module can later be deleted. These pins are BYTE-EXACT: every golden
# value below was computed from the CURRENT ``MemoryStore`` classmethods and
# hard-pinned as a LITERAL, so the contract survives ``store.py``'s deletion
# (nothing here imports ``loremaster.memory.store`` — the frozen literals ARE
# the old path). ``MemoryRef`` (the versioned ``chunk_key`` + ``key_version``
# reference the stamp folds in) moved with them.
# ===========================================================================


class TestMovedMemoryIdHelpersParity:
    """Byte-exact parity pins for the id helpers moved store.py → backend.py.

    The golden stamps / ids are frozen LITERALS (computed from the pre-move
    ``MemoryStore`` classmethods), asserted against the NEW backend functions.
    Includes the edge cases the move must not perturb: empty refs, order
    insensitivity, a ``chunk_key`` that itself contains the ``@`` field
    separator, and unicode / empty note text.
    """

    # -- refs_stamp ---------------------------------------------------------

    def test_empty_refs_stamp_is_the_empty_string(self) -> None:
        # An empty ref list stamps the empty string (folds into a bare id).
        assert derive_refs_stamp([]) == ""

    def test_single_ref_stamp_carries_the_default_key_version(self) -> None:
        # A bare ref (no explicit version) stamps ``chunk_key@DEFAULT_KEY_VERSION``.
        chunk_key = "loremaster:loremaster/memory/local.py:symbol:LocalMemoryBackend:0"
        assert derive_refs_stamp([MemoryRef(chunk_key=chunk_key)]) == (
            f"{chunk_key}@{DEFAULT_KEY_VERSION}"
        )

    def test_single_ref_stamp_carries_an_explicit_key_version(self) -> None:
        assert (
            derive_refs_stamp([MemoryRef(chunk_key="pkg/mod.py:Foo.bar", key_version=3)])
            == "pkg/mod.py:Foo.bar@3"
        )

    def test_refs_stamp_is_order_insensitive(self) -> None:
        # The SAME set of refs in ANY order dedups to ONE stamp (sorted before
        # joining) — so two orderings mint the SAME memory id.
        forward = derive_refs_stamp(
            [
                MemoryRef(chunk_key="a_chunk", key_version=1),
                MemoryRef(chunk_key="b_chunk", key_version=2),
            ]
        )
        reversed_ = derive_refs_stamp(
            [
                MemoryRef(chunk_key="b_chunk", key_version=2),
                MemoryRef(chunk_key="a_chunk", key_version=1),
            ]
        )
        assert forward == reversed_ == "a_chunk@1,b_chunk@2"

    # -- refs_from_stamp (the inverse) --------------------------------------

    def test_empty_stamp_reconstructs_no_refs(self) -> None:
        assert refs_from_stamp("") == []

    def test_stamp_reconstructs_the_versioned_refs(self) -> None:
        assert refs_from_stamp("a_chunk@1,b_chunk@2") == [
            MemoryRef(chunk_key="a_chunk", key_version=1),
            MemoryRef(chunk_key="b_chunk", key_version=2),
        ]

    def test_chunk_key_containing_the_field_separator_round_trips(self) -> None:
        # ``rpartition`` splits on the LAST ``@`` so a ``chunk_key`` that itself
        # contains ``@`` (e.g. a ``user@host`` shaped key) survives the round trip.
        refs = [MemoryRef(chunk_key="user@host:path", key_version=5)]
        stamp = derive_refs_stamp(refs)
        assert stamp == "user@host:path@5"
        assert refs_from_stamp(stamp) == refs

    def test_stamp_round_trip_is_order_normalised(self) -> None:
        # from_stamp(stamp(refs)) yields the refs in the stamp's SORTED order.
        refs = [
            MemoryRef(chunk_key="z_chunk", key_version=9),
            MemoryRef(chunk_key="a_chunk", key_version=1),
        ]
        assert refs_from_stamp(derive_refs_stamp(refs)) == [
            MemoryRef(chunk_key="a_chunk", key_version=1),
            MemoryRef(chunk_key="z_chunk", key_version=9),
        ]

    # -- memory_id (deterministic uuid5) — frozen golden literals -----------

    def test_memory_id_ascii_no_stamp(self) -> None:
        assert (
            derive_memory_id("PG 18 mounts the data volume at /var/lib/postgresql", "")
            == "9907af1b-5a77-53c1-a600-c09400ba6600"
        )

    def test_memory_id_ascii_with_stamp(self) -> None:
        assert (
            derive_memory_id(
                "PG 18 mounts the data volume at /var/lib/postgresql", "a_chunk@1,b_chunk@2"
            )
            == "1bc26fcc-e469-584a-b83a-977467292bf8"
        )

    def test_memory_id_unicode_note_text_no_stamp(self) -> None:
        # A non-ASCII note (arrows, accents, emoji, CJK) hashes identically before
        # and after the move — the uuid5 name is the raw unicode string.
        assert (
            derive_memory_id("SurrealDB RecordID → str(id) everywhere; café ☕ naïve — 日本語", "")
            == "0ed95165-983e-56e2-aad4-023ba8b1ceae"
        )

    def test_memory_id_unicode_note_text_with_stamp(self) -> None:
        assert (
            derive_memory_id(
                "SurrealDB RecordID → str(id) everywhere; café ☕ naïve — 日本語",
                "a_chunk@1,b_chunk@2",
            )
            == "ff67ea31-7066-5e4c-8a9e-62d8b55d3244"
        )

    def test_memory_id_empty_note_text_no_stamp(self) -> None:
        assert derive_memory_id("", "") == "21b8f686-bdd7-5438-af5b-3dfd49cd02a5"

    def test_memory_id_empty_note_text_with_stamp(self) -> None:
        assert derive_memory_id("", "a_chunk@1,b_chunk@2") == (
            "3f735716-59d8-5843-a3ac-b4ce33870f7b"
        )

    # -- end-to-end: reproduce THIS FILE'S pre-existing independent literals --

    def test_end_to_end_reproduces_the_files_pinned_literals(self) -> None:
        # The moved functions, composed (stamp → id), reproduce the LITERAL ids
        # this module pinned INDEPENDENTLY (``_LITERAL_ID_*`` computed from the
        # documented convention, not from any code under test) — a cross-check
        # tying the moved helpers to the file's own oracle.
        assert derive_memory_id(PG_NOTE, derive_refs_stamp([])) == _LITERAL_ID_NO_REFS
        assert (
            derive_memory_id(PG_NOTE, derive_refs_stamp([MemoryRef(chunk_key=PINNED_CHUNK_KEY)]))
            == _LITERAL_ID_REF_V1
        )
        assert (
            derive_memory_id(
                PG_NOTE,
                derive_refs_stamp([MemoryRef(chunk_key=PINNED_CHUNK_KEY, key_version=3)]),
            )
            == _LITERAL_ID_REF_V3
        )

    def test_end_to_end_matches_the_independent_oracle_helpers(self) -> None:
        # The moved functions agree with this module's independent oracle
        # reconstructions (``expected_refs_stamp`` / ``expected_memory_id``) for a
        # representative memory carrying a versioned ref.
        chunk_key = "odoo:custom:models/account.py:symbol:AccountMove:0"
        ref = MemoryRef(chunk_key=chunk_key, key_version=3)
        assert derive_refs_stamp([ref]) == expected_refs_stamp([(chunk_key, 3)])
        assert derive_memory_id(PG_NOTE, derive_refs_stamp([ref])) == (
            expected_memory_id(PG_NOTE, [(chunk_key, 3)])
        )


# ===========================================================================
# P8a #7: the SINGLE-statement ``_query`` seam's classified-error posture.
#
# ``LocalMemoryBackend._query`` splits a caught error into transport (self-heal +
# ``SurrealConnectionError``) vs domain (keep the connection + ``SurrealStoreError``),
# mirroring ``SurrealStore._query``. What it did NOT do was launder the DOMAIN
# branch's message: it interpolated the raw ``{error}`` straight into the raised
# ``SurrealStoreError``. A domain ``ASSERT``/coercion rejection's engine text can
# echo a bound VALUE back verbatim (the ledger #31 leak the multi-statement
# ``execute_transaction`` path already closes), and that text flows to MCP clients
# in P8. These pins fix the seam at BOTH branches, deterministically and without a
# live server: a fake connection raises a scripted ``ServerError`` (domain- or
# transport-``kind``), the same fault-injection shape ``test_surreal_store.py``'s
# ``TestQueryMessageHygiene`` uses.
# ===========================================================================

# A synthetic ASSERT rejection carrying a value that must NEVER reach the raised
# message (mirrors ``test_surreal_store.py``'s ``_SENSITIVE_ENGINE_TEXT``).
_MEM_SENSITIVE_MARKER = "TOP-SECRET-MEMORY-BOUND-VALUE-4b8e2d"
_MEM_SENSITIVE_ENGINE_TEXT = (
    f"Found '{_MEM_SENSITIVE_MARKER}' for field `note_text`, with record "
    f"`memory:abc123`, but expected the value to fulfil the following "
    f"assertion: $value != NONE"
)
# The transport-``kind`` rejection the SDK raises when a mid-life socket drop left
# the reconnected session unauthenticated (``NotAllowed``) — a transport fault,
# never a rejection of the write we sent.
_MEM_TRANSPORT_ENGINE_TEXT = "Anonymous access to the memory query is not allowed"


@dataclass
class _RejectingConnection:
    """A fake SDK connection whose ``query`` raises a scripted error — the seam
    fault-injector for ``_query``'s classified-error posture. ``close`` is a
    tolerant no-op so a backend holding this handle still tears down cleanly.
    """

    error: BaseException

    async def query(self, statement: str, params: dict[str, Any]) -> Any:
        raise self.error

    async def close(self) -> None:
        return None


class TestQueryClassifiedErrorPosture:
    """The single-statement ``_query`` seam classifies like ``execute_transaction``
    (ledger #31): a DOMAIN rejection keeps the healthy connection and raises a
    ``SurrealStoreError`` naming a generic engine CLASS + a server-log hint, NEVER
    the raw engine text; a TRANSPORT fault self-heals (drops the handle) and raises
    ``SurrealConnectionError``. Real-only seam test — built inline with an injected
    fake connection (the fake backend exposes no ``_query`` seam to fault-inject),
    mirroring ``test_surreal_store.py``'s ``TestQueryMessageHygiene``.
    """

    @staticmethod
    def _backend_rejecting_with(error: BaseException) -> LocalMemoryBackend:
        backend = LocalMemoryBackend(
            url=_DEAD_URL,
            namespace="ns",
            database="db",
            dim=PRODUCTION_DIM,
            user="root",
            password="root",
            embedder=FakeEmbedder(dim=PRODUCTION_DIM),
            existing_chunks=FakeChunkOracle(),
        )
        backend._connection = cast("_SurrealConnection", _RejectingConnection(error=error))
        return backend

    async def test_domain_rejection_message_never_echoes_the_raw_engine_text(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        backend = self._backend_rejecting_with(
            ServerError(ErrorKind.INTERNAL, _MEM_SENSITIVE_ENGINE_TEXT)
        )
        connection_before = backend._connection
        with caplog.at_level(logging.ERROR, logger="loremaster.memory.local"):
            with pytest.raises(SurrealStoreError) as exc_info:
                await backend._query("UPDATE memory SET note_text = $t", {"t": "poison"})

        message = str(exc_info.value)
        # A domain rejection is a STORE error, not a connection error, and the
        # healthy connection is never thrown away.
        assert type(exc_info.value) is SurrealStoreError
        assert not isinstance(exc_info.value, SurrealConnectionError)
        assert backend._connection is connection_before
        # The raw engine text / the value it carries NEVER reaches the message.
        assert _MEM_SENSITIVE_ENGINE_TEXT not in message
        assert _MEM_SENSITIVE_MARKER not in message
        # It DOES carry a classified label + the server-log correlation hint.
        assert "assert violation" in message.lower()
        assert "server log" in message.lower()
        # The FULL engine detail is recoverable server-side (logged before raising).
        error_records = [record for record in caplog.records if record.levelno == logging.ERROR]
        assert error_records, "the full engine detail must be logged server-side"
        logged = " ".join(
            str(value)
            for value in (error_records[0].getMessage(), getattr(error_records[0], "engine_error", ""))
        )
        assert _MEM_SENSITIVE_MARKER in logged

    async def test_transport_failure_drops_the_handle_and_raises_connection_error(self) -> None:
        # The transport branch self-heals: a ``NotAllowed`` (mid-life socket drop
        # reconnected unauthenticated) drops the cached handle so the NEXT call
        # reconnects, and surfaces the connection type — never a raw SDK exception.
        backend = self._backend_rejecting_with(
            ServerError(ErrorKind.NOT_ALLOWED, _MEM_TRANSPORT_ENGINE_TEXT)
        )
        with pytest.raises(SurrealConnectionError):
            await backend._query("SELECT * FROM memory", {})
        assert backend._connection is None  # the dead handle was dropped (self-heal)


# ===========================================================================
# P8a #9 COVERAGE GAPS (notes-9): three pins for EXISTING behaviours that had
# no test — a refs-bearing ledger replay row, the memory trust-rejection
# fallback, and the shutdown-time connection close. These pin CURRENT behaviour
# (no production change); a RED here would expose a real defect.
# ===========================================================================


@pytest_asyncio.fixture()
async def real_backend(
    embedder: FakeEmbedder, ledger_path: str
) -> AsyncIterator[LocalMemoryBackend]:
    """A ready REAL SurrealDB-backed ``LocalMemoryBackend`` over a fresh isolated db.

    The real-only counterpart to ``memory_backend`` (which is parametrised
    fake+real): a couple of pins below exercise a path that exists ONLY on the
    real backend — a stored row whose ``source`` fails validation on recall, and
    the awaited underlying-connection close on shutdown — neither of which the
    in-memory fake models (it stores an already-valid ``MemorySource`` and holds
    no socket). Built the same way ``make_backend``'s "real" branch builds one
    (direct harness helpers, never the ``surreal_env`` fixture — see the import
    block's comment for why), and reaps its throwaway database on exit.
    """
    env: SurrealEnv = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup_connection = await connect_admin(env)
    await setup_connection.close()
    backend = LocalMemoryBackend(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        dim=env.dim,
        user=env.user,
        password=env.password,
        embedder=embedder,
        existing_chunks=FakeChunkOracle(),
        ledger=MemoryLedger(ledger_path),
    )
    await backend.ensure_ready()
    try:
        yield backend
    finally:
        await backend.close()
        await drop_database(env)


class TestRefsBearingReplay:
    """``restore_from_ledger`` reconstructs a row's chunk refs — the gap the
    existing replay suite left (every row it seeds carries an EMPTY refs_stamp and
    no ``labels`` metadata). A refs-bearing row must replay with its ``lore_ref``
    refs intact, drift-annotated on the recall that follows, and its deterministic
    id folding those refs. BOTH reconstruction sources are pinned: the v2
    ``labels`` metadata, and the pre-v2 ``refs_stamp`` (the
    ``_labels_from_refs_stamp`` path). Parametrised fake+real via ``make_backend``.
    """

    _REF_NOTE = "Correction pinned to a specific chunk, replayed from the ledger."
    _REF_CHUNK_KEY = "loremaster:loremaster/search.py:symbol:SearchTool:0"

    async def test_replay_reconstructs_refs_from_labels_metadata(
        self, make_backend: BackendFactory, ledger_path: str
    ) -> None:
        # A v2 ledger row: its metadata carries the flat ``lore_ref=`` label. The
        # replay reconstructs the ref from that label; the recall that follows
        # drift-annotates it (oracle KNOWS the key → not drifted) and the row keeps
        # its folded deterministic id.
        ledger = MemoryLedger(ledger_path)
        refs = [(self._REF_CHUNK_KEY, DEFAULT_KEY_VERSION)]
        memory_id = expected_memory_id(self._REF_NOTE, refs)
        ledger.record(
            memory_id=memory_id,
            text=self._REF_NOTE,
            metadata={"kind": "fact", "labels": [lore_ref_label(self._REF_CHUNK_KEY)]},
            refs_stamp=expected_refs_stamp(refs),
        )
        backend = await make_backend(
            ledger=ledger, chunk_oracle=FakeChunkOracle({self._REF_CHUNK_KEY})
        )

        assert await backend.restore_from_ledger() == 1

        item = next(
            i
            for i in await backend.recall(self._REF_NOTE, k=_READ_ALL)
            if i.text == self._REF_NOTE
        )
        # The refs survived the replay intact — exactly one, at the default version,
        # NOT drifted (the oracle knows the key), and the id folded the ref.
        assert len(item.refs) == 1
        assert item.refs[0].chunk_key == self._REF_CHUNK_KEY
        assert item.refs[0].key_version == DEFAULT_KEY_VERSION
        assert item.refs[0].drifted is False
        assert item.id == memory_id

    async def test_replay_reconstructs_refs_from_refs_stamp_for_a_pre_v2_row(
        self, make_backend: BackendFactory, ledger_path: str
    ) -> None:
        # A PRE-v2 ledger row: NO ``labels`` metadata, but a non-empty refs_stamp
        # carrying the EXPLICIT version. The replay must reconstruct the ``lore_ref``
        # from the refs_stamp (``_labels_from_refs_stamp``) — and, with an oracle
        # that does NOT know the key, flag it drifted (a FLAG, never a filter: the
        # row is still recalled).
        ledger = MemoryLedger(ledger_path)
        versioned_refs = [(self._REF_CHUNK_KEY, 3)]
        memory_id = expected_memory_id(self._REF_NOTE, versioned_refs)
        ledger.record(
            memory_id=memory_id,
            text=self._REF_NOTE,
            metadata={"author": "operator"},  # pre-v2: no kind, no labels
            refs_stamp=expected_refs_stamp(versioned_refs),
        )
        backend = await make_backend(ledger=ledger)  # default oracle knows nothing

        assert await backend.restore_from_ledger() == 1

        item = next(
            i
            for i in await backend.recall(self._REF_NOTE, k=_READ_ALL)
            if i.text == self._REF_NOTE
        )
        assert len(item.refs) == 1
        assert item.refs[0].chunk_key == self._REF_CHUNK_KEY
        # The explicit version rode the refs_stamp through the replay.
        assert item.refs[0].key_version == 3
        # Drift is a flag, not a filter — still recalled, but flagged.
        assert item.refs[0].drifted is True
        assert item.id == memory_id


class TestTrustGateRejection:
    """A stored ``source`` whose ``trust`` fails the two-value enum gate falls back
    to the experiential-operator default, and the memory stays USABLE — never
    dropped, never crashing recall/replay. Pins the ``ValidationError`` branch of
    ``_source_from_value`` / ``_source_from_metadata`` that no test exercised.
    """

    _NOTE = "A memory whose stored provenance was corrupted to an illegal trust."
    _ILLEGAL_TRUST_SOURCE = {"kind": "spec", "trust": "super-duper-trusted"}

    async def test_replay_of_a_row_with_a_rejected_trust_falls_back_to_experiential(
        self, make_backend: BackendFactory, ledger_path: str
    ) -> None:
        # The RECONSTRUCTION gate (BOTH backends): a ledger row whose metadata
        # ``source`` carries an out-of-vocabulary ``trust`` replays with the
        # experiential-operator default rather than propagating the bad value or
        # failing the whole replay.
        ledger = MemoryLedger(ledger_path)
        memory_id = expected_memory_id(self._NOTE)
        ledger.record(
            memory_id=memory_id,
            text=self._NOTE,
            metadata={"kind": "fact", "source": dict(self._ILLEGAL_TRUST_SOURCE)},
            refs_stamp="",
        )
        backend = await make_backend(ledger=ledger)

        assert await backend.restore_from_ledger() == 1

        item = next(
            i for i in await backend.recall(self._NOTE, k=_READ_ALL) if i.text == self._NOTE
        )
        # The trust gate rejected the illegal value; the row is still recalled,
        # carrying the experiential-operator fallback (never the bad trust).
        assert item.source.trust == "experiential"
        assert item.source.kind == "operator"

    async def test_recall_of_a_row_with_a_rejected_trust_falls_back_but_still_returns(
        self, real_backend: LocalMemoryBackend, caplog: pytest.LogCaptureFixture
    ) -> None:
        # The RECALL gate (REAL backend only — the fake stores an already-valid
        # ``MemorySource`` and never re-validates on recall): a row already in the
        # store whose ``source`` was corrupted to an illegal trust must still be
        # recalled, with the experiential fallback, and the rejection LOGGED
        # (recoverable server-side), never swallowed silently or crashing recall.
        memory_id = await real_backend.remember(self._NOTE, kind="fact")
        # Corrupt the stored provenance directly. The schema's ``source`` column is
        # ``object FLEXIBLE`` with no engine-side trust ASSERT, so the bad value
        # lands; the gate lives in the READ-side value-object validation.
        await real_backend._query(
            f"UPDATE type::record('{MEMORY_TABLE}', $id) SET source = $bad",
            {"id": memory_id, "bad": dict(self._ILLEGAL_TRUST_SOURCE)},
        )

        with caplog.at_level(logging.WARNING, logger="loremaster.memory.local"):
            recalled = await real_backend.recall(self._NOTE, k=_READ_ALL)

        item = next(i for i in recalled if i.text == self._NOTE)
        assert item.source.trust == "experiential"
        assert item.source.kind == "operator"
        # The rejection is observable server-side, not a silent swallow.
        assert any(
            "memory.source.malformed" in record.getMessage() for record in caplog.records
        ), "a rejected stored source must be logged, not silently swallowed"


@dataclass
class _CloseSpyConnection:
    """A fake SDK connection that tallies awaited ``close`` calls — the shutdown
    seam spy for :meth:`LocalMemoryBackend.close` (mirrors ``_RejectingConnection``'s
    inline-fake shape). ``query`` returns an empty result so a backend holding this
    handle stays usable before it is closed.
    """

    close_awaited: int = 0

    async def query(self, statement: str, params: dict[str, Any]) -> Any:
        return []

    async def close(self) -> None:
        self.close_awaited += 1


class TestShutdownClosesConnection:
    """``close`` AWAITS the underlying SDK connection's ``close`` and drops the
    cached handle (self-heal parity) — the shutdown seam the server's teardown
    relies on (``AppContext`` awaits ``memory_backend.close()``). Real-backend
    seam, driven with an injected spy connection (the fake holds no socket).
    """

    @staticmethod
    def _backend_with_spy(spy: _CloseSpyConnection) -> LocalMemoryBackend:
        backend = LocalMemoryBackend(
            url=_DEAD_URL,
            namespace="ns",
            database="db",
            dim=PRODUCTION_DIM,
            user="root",
            password="root",
            embedder=FakeEmbedder(dim=PRODUCTION_DIM),
            existing_chunks=FakeChunkOracle(),
        )
        backend._connection = cast("_SurrealConnection", spy)
        return backend

    async def test_close_awaits_the_underlying_connection_close(self) -> None:
        spy = _CloseSpyConnection()
        backend = self._backend_with_spy(spy)

        await backend.close()

        # The socket was genuinely released (awaited), not leaked, and the cached
        # handle dropped so any post-close call reconnects rather than reusing a
        # dead one.
        assert spy.close_awaited == 1
        assert backend._connection is None

    async def test_close_is_idempotent_and_tolerates_a_never_connected_backend(
        self,
    ) -> None:
        # A second close is a no-op (handle already dropped, no second underlying
        # close); a never-connected backend closes cleanly too — teardown must
        # never crash on either.
        spy = _CloseSpyConnection()
        backend = self._backend_with_spy(spy)
        await backend.close()
        await backend.close()
        assert spy.close_awaited == 1

        never_connected = LocalMemoryBackend(
            url=_DEAD_URL,
            namespace="ns",
            database="db",
            dim=PRODUCTION_DIM,
            user="root",
            password="root",
            embedder=FakeEmbedder(dim=PRODUCTION_DIM),
            existing_chunks=FakeChunkOracle(),
        )
        await never_connected.close()  # tolerant of a backend that never connected


# ===========================================================================
# Finding #69: ``MemoryBackend._hybrid_search`` (the recall path) copy-pasted
# finding #66/#67's OLD, independently-hand-maintained constants
# (``_MAX_QUERY_TEXT_CHARS=4096`` / ``_MAX_QUERY_TOKENS=64``, its own comment
# said "mirrors store.surreal"). Fix: SHARE the mechanism
# (``loremaster.store.query_text`` — see ``test_query_text.py``'s
# ``TestSharedMechanismPin``) rather than mint a third hand-copied twin.
#
# IMPORTANT — measured, not assumed (repo law: verify, don't assume a defect
# transfers 1:1 across a rename/reshape): the recall arm's OWN predicate shape
# differs from the chunk store's. ``MEMORY_FULLTEXT_FIELDS`` has 1 field (not
# 3), and ``LocalMemoryBackend._build_fulltext_predicate`` is CONJUNCTIVE — an
# AND-chain of single-field terms ("every query word must be present"), not
# the chunk store's disjunctive OR-chain ("any token matches"). Live-measured
# end-to-end through THIS exact statement shape
# (``scratchpad/probe_long_query_69.py``, against spike-surreal, never
# production): 114 tokens/AND-clauses OK, 115 REJECTED — not the chunk
# store's 39/40. The OLD ``_MAX_QUERY_TOKENS=64`` clamp was ALREADY (by
# coincidence, not by design) below that boundary, so the token-count
# rejection mechanism could not actually reproduce for this consumer: a live
# probe of a 200-real-unique-word (3089-char) ``recall()`` call through the
# UNMODIFIED pre-fix code succeeded in ~5ms, no rejection. The fix below still
# applies — it closes the copy-paste twin, fixes the naive ``text[:N]``
# char-slice's word-splitting defect, and future-proofs against a
# ``MEMORY_FULLTEXT_FIELDS`` width increase silently re-opening this class of
# rejection (2 fields x the OLD 64-token cap = 128 clauses, already PAST the
# measured 115 boundary) — but the tests below pin the FIX's own safety
# margin, never a "was hard-failing, now isn't" regression the live
# measurement does not support.
# ===========================================================================

# Distinct, single-token synthetic lexemes (all-lowercase ASCII letters only —
# no digits, no case changes — so the ``code_ident`` analyzer's tokenizers
# never split one into two): 200 of them, far beyond both the derived
# :data:`~loremaster.memory.local._MAX_QUERY_TOKENS` clamp (60) and the
# live-measured 115-token rejection boundary, so a query built from all of
# them exercises the worst realistic case deterministically.
_MEM_SYNTHETIC_LEXEMES = tuple(
    f"synlex{chr(97 + index // 26)}{chr(97 + index % 26)}" for index in range(200)
)

# A realistically long, multi-sentence "note being searched for" (finding
# #69's own body names this exact shape) — deliberately over 900 chars so
# BOTH the word-boundary pre-truncation AND the token clamp actually engage,
# not just one of them.
_MEM_LONG_RECALL_QUERY = (
    "What was the operator ruling on the P8d closure and how does the slate "
    "cycle get sequenced before the detection layer lands, and which commits "
    "carry the surface flip receipts we should cite when asked about it later, "
    "and can you also summarize how the client-needs consult informed the "
    "accuracy-versus-efficiency tradeoff the lead ultimately ruled on, and "
    "separately, what is the current status of the SurrealDB unification "
    "effort across the store and memory backends, including any outstanding "
    "findings from the recent slate-fixer sweep that touched the hybrid "
    "search lexical arm's query-text bounding constants and the shared "
    "clause-budget derivation module that both the chunk store and the "
    "memory recall path are now expected to import from instead of "
    "maintaining their own independently hand-copied twin of the same "
    "historically buggy constants that this very finding was filed against, "
    "and this trailing clause exists purely to push the fixture comfortably "
    "past the 900-character word-boundary truncation threshold under test."
)

# A punctuation-heavy, non-ASCII (French + Japanese) long query — proves the
# fix is content-agnostic, not tuned to plain ASCII English (mirrors
# ``test_surreal_store.py``'s ``_NON_ASCII_LONG_QUERY``).
_MEM_NON_ASCII_LONG_QUERY = (
    "Quelle était la décision de l'opérateur sur la clôture de P8d, et comment "
    "le cycle « slate » est-il séquencé avant la couche de détection ? "
    "日本語のテスト文字列もここに含まれています、質問はとても長くなりますが大丈夫です。 "
    "Encore quelques mots supplémentaires pour dépasser confortablement le seuil mesuré, "
    "et voici même davantage de texte non-ASCII pour être certain de dépasser trois cent "
    "quarante caractères — なぜなら、この境界値を確実に超える必要があるからです。"
) * 3


class TestRecallLongQueryNeverRejects:
    """A realistically long (or synthetically token-heavy) recall query must
    NEVER hard-fail ``recall`` — see the module-level finding #69 note above
    for the measured boundary this fix's constants are derived from.
    """

    async def test_query_at_the_new_token_clamp_boundary_succeeds(
        self, real_backend: LocalMemoryBackend
    ) -> None:
        query_text = " ".join(_MEM_SYNTHETIC_LEXEMES[:_MAX_QUERY_TOKENS])  # exactly at the clamp
        await real_backend.remember(text=query_text, kind="fact")
        results = await real_backend.recall(query_text, k=5)
        assert any(memory.text == query_text for memory in results)

    async def test_query_far_beyond_the_derived_clamp_is_bounded_not_rejected(
        self, real_backend: LocalMemoryBackend
    ) -> None:
        # 200 distinct real tokens — far beyond both the new 60-token clamp
        # and the char cap, so both mechanisms engage; must still succeed,
        # bounded not rejected, and the vector arm (full, untruncated text
        # embedded upstream) still finds the exact-text target.
        query_text = " ".join(_MEM_SYNTHETIC_LEXEMES)
        await real_backend.remember(text=query_text, kind="fact")
        results = await real_backend.recall(query_text, k=5)
        assert any(memory.text == query_text for memory in results)

    async def test_a_long_plain_english_recall_query_succeeds_end_to_end(
        self, real_backend: LocalMemoryBackend
    ) -> None:
        assert len(_MEM_LONG_RECALL_QUERY) > 900
        await real_backend.remember(text=_MEM_LONG_RECALL_QUERY, kind="fact")
        results = await real_backend.recall(_MEM_LONG_RECALL_QUERY, k=5)
        assert any(memory.text == _MEM_LONG_RECALL_QUERY for memory in results)

    async def test_non_ascii_punctuation_heavy_long_query_does_not_raise(
        self, real_backend: LocalMemoryBackend
    ) -> None:
        assert len(_MEM_NON_ASCII_LONG_QUERY) > 900
        # No corpus needed — the only assertion that matters is "does not raise".
        results = await real_backend.recall(_MEM_NON_ASCII_LONG_QUERY, k=5)
        assert results == []

    async def test_short_query_below_the_char_bound_is_untouched_by_truncation(
        self, real_backend: LocalMemoryBackend
    ) -> None:
        # A short, realistic query sits well under _MAX_LEXICAL_QUERY_CHARS —
        # truncation must be a complete no-op, and the token clamp must never
        # even engage — exactly the pre-fix behaviour for any query this short.
        query_text = "operator ruling P8d closure"
        assert len(query_text) < _MAX_LEXICAL_QUERY_CHARS
        assert truncate_at_word_boundary(query_text, _MAX_LEXICAL_QUERY_CHARS) == query_text
        direct_tokens = await real_backend._analyze_query(query_text)
        assert len(direct_tokens) <= _MAX_QUERY_TOKENS  # the clamp never even triggers


class TestRecursionDepthClassificationAtRecallSeam:
    """The recall path's ``_query`` seam must launder a genuine engine
    rejection through the SAME shared classifier the chunk store uses
    (:func:`~loremaster.store._txn._classify_engine_error`) — finding #69
    explicitly asked this to be VERIFIED for the recall call site, not
    assumed shared just because the import already existed.
    """

    def test_classifier_recognises_the_live_recursion_depth_rejection_text(self) -> None:
        # The EXACT raw engine text captured live against spike-surreal for
        # THIS consumer's own predicate shape (scratchpad/probe_long_query_69.py)
        # — a pure, fast unit test of the (already-shared) classifier, no live
        # server needed.
        raw_engine_text = (
            "Parse error: Exceeded expression recursion depth limit\n"
            " --> [1:3378]\n"
            "  |\n"
            "1 | ...ote_text @@ $__ft114)))], 5, 60)\n"
            "  |              ^ this expression nests or chains operators too deeply\n"
        )
        assert _classify_engine_error(raw_engine_text) == _ERROR_CLASS_QUERY_TOO_COMPLEX

    async def test_bypassing_both_clamps_still_raises_a_classified_store_error(
        self, real_backend: LocalMemoryBackend, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Force BOTH lexical-arm clamps back up past the measured-safe ceiling
        # (114) — simulating a future regression — and confirm the genuine
        # engine rejection still comes back laundered, not raw, and the
        # connection stays healthy (a domain rejection, not a transport
        # fault, mirroring ``TestQueryClassifiedErrorPosture``'s contract).
        monkeypatch.setattr("loremaster.memory.local._MAX_QUERY_TOKENS", 200)
        monkeypatch.setattr("loremaster.memory.local._MAX_LEXICAL_QUERY_CHARS", 4096)
        connection_before = real_backend._connection
        query_text = " ".join(_MEM_SYNTHETIC_LEXEMES)  # 200 real tokens, now fully unclamped
        with pytest.raises(SurrealStoreError) as exc_info:
            await real_backend.recall(query_text, k=5)
        message = str(exc_info.value)
        assert "query too complex" in message
        assert "recursion depth" not in message  # the raw engine text never echoes
        assert not isinstance(exc_info.value, SurrealConnectionError)
        assert real_backend._connection is connection_before  # healthy, never dropped
