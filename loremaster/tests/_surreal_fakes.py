"""Fast in-memory async fakes mirroring the P2–P4 SurrealDB port surface.

These are the UNIT-test doubles for P5-C3b: the Indexer / ReconcileEngine /
LiveWatcher are rewired off the sync SQLite-manifest + Kùzu-graph + upsert-then-
delete store calls onto the **async** Surreal contract with the C2 composed
atomic per-file transaction. The ported unit tests inject these fakes so the
rewired call sites are exercised at millisecond speed, without a live SurrealDB
server (the store-level atomicity itself is live-covered by
``test_surreal_apply.py``; a lean set of live integration tests lives in
``test_indexer_surreal_integration.py``).

Faithfulness to the REAL port signatures (the whole point — a fake that lies
about the contract certifies a bug):

* Every method the rewired callers ``await`` is ``async def`` here, with the
  SAME name/signature as :class:`~loremaster.store.surreal.SurrealStore`,
  :class:`~loremaster.index.surreal_manifest.SurrealManifest`, and
  :class:`~loremaster.graph_surreal.SurrealCodeGraph`. The PURE fragment
  builders (``replace_file_fragment`` / ``file_text_fragment`` /
  ``replace_fragment`` / ``build_file_graph_fragment`` / the delete/purge
  counterparts) and ``reset_resolution_cache`` / the ``*_module_name`` static
  helpers stay SYNC, exactly as the real ports keep them.
* :meth:`FakeSurrealStore.apply` composes the fragments into ONE atomic
  transaction: it enforces the SAME param-collision guard
  (:class:`~loremaster.store._txn.TxnParamCollisionError`), the SAME empty guard
  (``ValueError``) and the SAME hard statement-count cap
  (:data:`~loremaster.store._txn.TXN_STATEMENT_HARD_CAP`, raising
  :class:`~loremaster.store.surreal.SurrealStoreError`) the real
  ``compose``/``apply`` do — and applies every producer's effect all-or-nothing,
  so a mid-transaction failure rolls the WHOLE thing back (the atomicity the
  four rewired surfaces depend on).
* The code-graph fake REUSES the REAL astroid derivation
  (:class:`~loremaster.graph_surreal._AstroidDerivation`) — the SAME
  ``_derive_nodes`` / ``_derive_edges`` production runs — so a node qualified
  name or an ``imports`` edge dst can never diverge from what the live graph
  would produce. Only the storage + query layer is a simple in-memory shim.

The three fakes SHARE one :class:`_FakeSurrealDatabase` (the way the real ports
share one SurrealDB database over three connections), so a manifest/graph/chunk
fragment applied through the store's ``apply`` is visible on the sibling fake's
read methods — exactly the cross-connection visibility the atomic apply relies
on. Build them together with :func:`fake_surreal_trio`.

RED against current code: the pre-P5-C3b Indexer / ReconcileEngine / LiveWatcher
call the manifest/graph methods SYNCHRONOUSLY (no ``await``) and use the old
``store.upsert`` / ``store.delete_points`` ordering. Against these async fakes a
sync ``self._manifest.get(...)`` returns a coroutine whose ``.state`` attribute
does not exist (``AttributeError``), a sync ``for row in self._manifest.
files_for_tier(...)`` iterates a coroutine (``TypeError``), and an unawaited
``self._manifest.delete(...)`` never mutates the store — every one a behavioural
RED that the rewiring turns green.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loremaster.graph import (
    _REFERENCE_KINDS,
    EDGE_IMPORTS,
    KIND_MODULE,
    CodeGraph,
    GraphNode,
    ReferenceSummary,
    _EdgeSpec,
    _NodeSpec,
)
from loremaster.graph_surreal import GRAPH_FRAGMENT_PARAM_PREFIX, _AstroidDerivation
from loremaster.index.manifest import FileRow
from loremaster.index.records import Record
from loremaster.index.surreal_manifest import (
    MANIFEST_FRAGMENT_PARAM_PREFIX,
    STATE_INDEXED,
)
from loremaster.store._txn import TXN_STATEMENT_HARD_CAP, TxnParamCollisionError
from loremaster.store.surreal import (
    CHUNK_FRAGMENT_PARAM_PREFIX,
    FILE_TEXT_FRAGMENT_PARAM_PREFIX,
    FILE_TEXT_MAX_BYTES,
    SurrealStoreError,
    VectorDimensionError,
)
from lorescribe.models import Chunk

# The producer tags every fake fragment carries so a ported test can assert the
# COMPOSITION of one atomic apply (e.g. "index_file composed exactly the chunk +
# file_text + manifest + graph fragments"). These name the four producers the
# per-file transaction spans — the C2 vocabulary, not free-form strings.
PRODUCER_CHUNK = "chunk"
PRODUCER_FILE_TEXT = "file_text"
PRODUCER_MANIFEST = "manifest"
PRODUCER_GRAPH = "graph"


@dataclass
class FakeFragment:
    """A composable transaction fragment (the fake analogue of ``TxnFragment``).

    Mirrors :class:`~loremaster.store._txn.TxnFragment`'s ROLE — an ordered slice
    of a larger atomic transaction carrying no ``BEGIN``/``COMMIT`` of its own —
    but additionally carries the in-memory ``effect`` closure the fake store's
    :meth:`FakeSurrealStore.apply` runs against the shared database, and a
    ``producer`` tag so a test can pin which producers a composed apply spanned.

    Attributes:
        producer: One of the ``PRODUCER_*`` tags naming the producing surface.
        statements: The statement list — its LENGTH matters (the hard-cap guard
            counts total statements across fragments, exactly as ``compose``
            does), its text is illustrative only.
        params: The producer-namespaced bound params (the collision guard unions
            these across fragments, exactly as ``compose`` does).
        effect: Applies this fragment's mutation to the shared database.
    """

    producer: str
    statements: list[str]
    params: dict[str, Any]
    effect: Callable[[_FakeSurrealDatabase], None]


# ---------------------------------------------------------------------------
# The shared in-memory database the three fakes read/write (one SurrealDB db).
# ---------------------------------------------------------------------------


@dataclass
class _StoredChunk:
    """One persisted chunk row (payload + vector), keyed by its point id."""

    tier: str
    file_path: str
    payload: dict[str, Any]
    vector: list[float]


@dataclass
class _GraphSlice:
    """One file's derived code-graph slice: its nodes + reference edges."""

    module: str
    nodes: list[_NodeSpec]
    edges: list[_EdgeSpec]


@dataclass
class _FakeSurrealDatabase:
    """The shared per-project state the store, manifest and graph fakes all use.

    One instance stands in for the single SurrealDB database the three real ports
    share, so a fragment applied through the store's ``apply`` is immediately
    visible to the sibling manifest/graph read methods (cross-connection
    visibility). All mutation flows through the small helpers below so an atomic
    ``apply`` can snapshot/restore the whole thing on a mid-transaction failure.
    """

    chunks: dict[str, _StoredChunk] = field(default_factory=dict)
    file_text: dict[tuple[str, str], dict[str, str]] = field(default_factory=dict)
    manifest_rows: dict[tuple[str, str], FileRow] = field(default_factory=dict)
    meta: dict[str, str] = field(default_factory=dict)
    graph_slices: dict[tuple[str, str], _GraphSlice] = field(default_factory=dict)

    # -- chunk helpers ----------------------------------------------------
    def replace_file_chunks(
        self, tier: str, file_path: str, rows: list[_StoredChunk]
    ) -> None:
        """Drop every existing chunk of ``(tier, file_path)`` and write ``rows``."""
        self.delete_file_chunks(tier, file_path)
        for row in rows:
            self.chunks[row.payload["__point_id"]] = row

    def delete_file_chunks(self, tier: str, file_path: str) -> None:
        """Purge every chunk of ``(tier, file_path)`` (tier-scoped)."""
        doomed = [
            pid
            for pid, chunk in self.chunks.items()
            if chunk.tier == tier and chunk.file_path == file_path
        ]
        for pid in doomed:
            del self.chunks[pid]

    def delete_tier_chunks(self, tier: str) -> None:
        """Purge every chunk in ``tier`` (the per-tier rebuild primitive)."""
        doomed = [pid for pid, chunk in self.chunks.items() if chunk.tier == tier]
        for pid in doomed:
            del self.chunks[pid]

    def identities_for(self, tier: str, file_path: str) -> set[str]:
        """The chunk identities currently stored for ``(tier, file_path)``."""
        # Built as an explicit loop (rather than a set comprehension minus
        # {None}) so mypy can see the collected type is genuinely ``set[str]``
        # — a comprehension over ``dict.get`` returns ``Any | None`` and a
        # post-hoc ``- {None}`` does not narrow that statically.
        identities: set[str] = set()
        for chunk in self.chunks.values():
            if chunk.tier != tier or chunk.file_path != file_path:
                continue
            identity = chunk.payload.get("identity")
            if identity is not None:
                identities.add(identity)
        return identities

    def file_paths(self) -> set[str]:
        """Every distinct ``file_path`` with at least one stored chunk."""
        return {chunk.file_path for chunk in self.chunks.values()}

    def snapshot(self) -> _FakeSurrealDatabase:
        """A deep copy for atomic rollback (the engine's snapshot isolation)."""
        return copy.deepcopy(self)

    def restore(self, snapshot: _FakeSurrealDatabase) -> None:
        """Roll every table back to ``snapshot`` (mid-transaction failure)."""
        self.chunks = snapshot.chunks
        self.file_text = snapshot.file_text
        self.manifest_rows = snapshot.manifest_rows
        self.meta = snapshot.meta
        self.graph_slices = snapshot.graph_slices


def _now_iso() -> str:
    """A timezone-aware ISO timestamp for a fake ``FileRow.updated_at``."""
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# The store fake.
# ---------------------------------------------------------------------------


class FakeSurrealStore:
    """In-memory async stand-in for :class:`~loremaster.store.surreal.SurrealStore`.

    Owns the atomic :meth:`apply` (the composed-transaction seam every rewired
    per-file update funnels through) plus the pure chunk/file_text fragment
    builders and the tier/file delete primitives. The statement-cap and
    file_text-size ceilings are read from the SAME constants production enforces,
    but are OVERRIDABLE per-instance so a unit test can drive the cap-overflow /
    oversize-file_text decisions cheaply (a small file crosses a small cap) while
    still reading the ceiling from the store — the single source of truth the
    indexer's pre-check reads (clause 5), never a hand-copied literal.
    """

    def __init__(
        self,
        *,
        dim: int,
        file_text_max_bytes: int = FILE_TEXT_MAX_BYTES,
        txn_statement_hard_cap: int = TXN_STATEMENT_HARD_CAP,
        db: _FakeSurrealDatabase | None = None,
    ) -> None:
        self._dim = dim
        self._file_text_max_bytes = file_text_max_bytes
        self._txn_statement_hard_cap = txn_statement_hard_cap
        self.db = db if db is not None else _FakeSurrealDatabase()
        # Every atomic apply's composed fragment list, in order — the telemetry a
        # ported test inspects to pin the composition of one transaction.
        self.applied_transactions: list[list[FakeFragment]] = []

    # -- ceilings the indexer reads (clause-5 single source of truth) -----

    @property
    def file_text_max_bytes(self) -> int:
        """The per-body byte ceiling the indexer's pre-check reads before it
        decides to skip the ``file_text`` fragment for an oversized file."""
        return self._file_text_max_bytes

    # -- lifecycle --------------------------------------------------------

    async def ensure_ready(self) -> None:
        """No-op (the fake has no schema to apply)."""

    async def close(self) -> None:
        """No-op (the fake holds no socket)."""

    # -- pure fragment builders (SYNC, exactly like the real store) -------

    def replace_file_fragment(
        self,
        tier: str,
        file_path: str,
        records_with_vectors: Sequence[tuple[Record, list[float]]],
    ) -> FakeFragment:
        """Build the chunk-replace fragment (validates dims at BUILD time)."""
        for record, vector in records_with_vectors:
            if len(vector) != self._dim:
                raise VectorDimensionError(
                    f"vector for chunk {record.point_id!r} has width {len(vector)}, "
                    f"expected {self._dim}"
                )
        rows = [
            _StoredChunk(
                tier=tier,
                file_path=file_path,
                payload={**record.payload, "__point_id": record.point_id},
                vector=list(vector),
            )
            for record, vector in records_with_vectors
        ]
        prefix = CHUNK_FRAGMENT_PARAM_PREFIX
        # 1 DELETE + one UPSERT per record — the real fragment's statement shape,
        # so the composed statement count the cap counts is realistic.
        statements = [f"{prefix}delete"] + [
            f"{prefix}upsert{index}" for index in range(len(rows))
        ]
        params: dict[str, Any] = {f"{prefix}tier": tier, f"{prefix}file": file_path}
        for index, row in enumerate(rows):
            params[f"{prefix}id{index}"] = row.payload["__point_id"]

        def effect(db: _FakeSurrealDatabase) -> None:
            db.replace_file_chunks(tier, file_path, rows)

        return FakeFragment(PRODUCER_CHUNK, statements, params, effect)

    def delete_file_fragment(self, tier: str, file_path: str) -> FakeFragment:
        """Build the fragment that purges every chunk of ``(tier, file_path)``."""
        prefix = CHUNK_FRAGMENT_PARAM_PREFIX
        params = {f"{prefix}tier": tier, f"{prefix}file": file_path}

        def effect(db: _FakeSurrealDatabase) -> None:
            db.delete_file_chunks(tier, file_path)

        return FakeFragment(PRODUCER_CHUNK, [f"{prefix}delete"], params, effect)

    def file_text_fragment(
        self, tier: str, file_path: str, text: str, sha512: str
    ) -> FakeFragment:
        """Build the ``file_text`` UPSERT fragment (size-capped at BUILD time)."""
        body_bytes = len(text.encode("utf-8"))
        if body_bytes > self._file_text_max_bytes:
            raise SurrealStoreError(
                f"file_text body for {file_path!r} is {body_bytes} bytes, exceeding "
                f"the {self._file_text_max_bytes}-byte cap"
            )
        prefix = FILE_TEXT_FRAGMENT_PARAM_PREFIX
        params = {f"{prefix}id": [tier, file_path], f"{prefix}content": {"text": text}}

        def effect(db: _FakeSurrealDatabase) -> None:
            db.file_text[(tier, file_path)] = {"text": text, "sha512": sha512}

        return FakeFragment(PRODUCER_FILE_TEXT, [f"{prefix}upsert"], params, effect)

    def file_text_delete_fragment(self, tier: str, file_path: str) -> FakeFragment:
        """Build the fragment that removes the ``file_text`` body of one path."""
        prefix = FILE_TEXT_FRAGMENT_PARAM_PREFIX
        params = {f"{prefix}id": [tier, file_path]}

        def effect(db: _FakeSurrealDatabase) -> None:
            db.file_text.pop((tier, file_path), None)

        return FakeFragment(PRODUCER_FILE_TEXT, [f"{prefix}delete"], params, effect)

    # -- the atomic apply (the composed-transaction heart) ----------------

    async def apply(self, fragments: Sequence[FakeFragment]) -> None:
        """Compose ``fragments`` into ONE transaction and run it atomically.

        Enforces the SAME three guards the real ``compose`` does — an empty
        transaction is a ``ValueError``, two fragments binding the same param name
        is a :class:`TxnParamCollisionError`, and a composed body over the hard
        statement cap is a :class:`SurrealStoreError` (raised at BUILD time,
        before any effect runs) — then applies every producer's effect
        all-or-nothing against the shared database, restoring the pre-apply
        snapshot if any effect raises (the engine's rollback).
        """
        fragments = list(fragments)
        if not fragments:
            raise ValueError("apply() requires at least one fragment")
        merged: dict[str, Any] = {}
        statement_count = 0
        for fragment in fragments:
            statement_count += len(fragment.statements)
            for key in fragment.params:
                if key in merged:
                    raise TxnParamCollisionError(
                        f"parameter {key!r} bound by more than one fragment"
                    )
                merged[key] = fragment.params[key]
        if statement_count > self._txn_statement_hard_cap:
            raise SurrealStoreError(
                f"composed transaction has {statement_count} statements, exceeding "
                f"the hard cap of {self._txn_statement_hard_cap}"
            )
        snapshot = self.db.snapshot()
        try:
            for fragment in fragments:
                fragment.effect(self.db)
        except Exception:
            self.db.restore(snapshot)
            raise
        self.applied_transactions.append(fragments)

    # -- non-composed writes (static rebuild / direct purge) --------------

    async def upsert(
        self, records_with_vectors: Sequence[tuple[Record, list[float]]]
    ) -> None:
        """Upsert ``(record, vector)`` pairs by point id (dim-validated)."""
        for record, vector in records_with_vectors:
            if len(vector) != self._dim:
                raise VectorDimensionError(
                    f"vector for chunk {record.point_id!r} has width {len(vector)}"
                )
        for record, vector in records_with_vectors:
            self.db.chunks[record.point_id] = _StoredChunk(
                tier=record.payload["tier"],
                file_path=record.payload["file_path"],
                payload={**record.payload, "__point_id": record.point_id},
                vector=list(vector),
            )

    async def delete_points(self, ids: Sequence[str]) -> None:
        """Purge exactly the named point ids."""
        for pid in ids:
            self.db.chunks.pop(pid, None)

    async def delete_by_file(self, tier: str, file_path: str) -> None:
        """Purge every chunk matching ``(tier, file_path)``."""
        self.db.delete_file_chunks(tier, file_path)

    async def delete_by_tier(self, tier: str) -> None:
        """Purge every chunk in ``tier`` (the per-tier rebuild primitive)."""
        self.db.delete_tier_chunks(tier)

    async def count(self, tier: str | None = None) -> int:
        """The live chunk count — total or tier-scoped."""
        if tier is None:
            return len(self.db.chunks)
        return sum(1 for chunk in self.db.chunks.values() if chunk.tier == tier)

    # -- inspection helpers (test-only, not part of the production API) ---

    def identities_for(self, tier: str, file_path: str) -> set[str]:
        """The chunk identities stored for ``(tier, file_path)`` (test oracle)."""
        return self.db.identities_for(tier, file_path)

    def stored_file_paths(self) -> set[str]:
        """Every ``file_path`` with at least one stored chunk (test oracle)."""
        return self.db.file_paths()

    def point_ids_for(self, tier: str) -> set[str]:
        """The point ids stored under ``tier`` (test oracle for a selective rebuild)."""
        return {
            pid for pid, chunk in self.db.chunks.items() if chunk.tier == tier
        }

    def stored_vector_for(
        self, tier: str, file_path: str, identity: str
    ) -> list[float] | None:
        """The VECTOR actually stored for one chunk (test oracle for context-
        sensitivity — the fake has no HNSW cosine search, so a vector-correctness
        assertion compares the stored vector directly against an independent
        embed of the same chunk)."""
        for chunk in self.db.chunks.values():
            if (
                chunk.tier == tier
                and chunk.file_path == file_path
                and chunk.payload.get("identity") == identity
            ):
                return chunk.vector
        return None

    def file_text_of(self, tier: str, file_path: str) -> dict[str, str] | None:
        """The stored ``file_text`` row for ``(tier, file_path)`` (test oracle)."""
        return self.db.file_text.get((tier, file_path))


# ---------------------------------------------------------------------------
# The manifest fake.
# ---------------------------------------------------------------------------


class FakeSurrealManifest:
    """In-memory async stand-in for :class:`~loremaster.index.surreal_manifest.
    SurrealManifest` — every CRUD/meta method is ``async``, the two fragment
    builders (``replace_fragment`` / ``delete_fragment``) stay SYNC.
    """

    def __init__(self, *, db: _FakeSurrealDatabase) -> None:
        self.db = db

    async def ensure_ready(self) -> None:
        """No-op."""

    async def close(self) -> None:
        """No-op."""

    def _make_row(
        self,
        *,
        tier: str,
        file_path: str,
        sha512: str,
        mtime_ns: int,
        size: int,
        n_chunks: int,
        chunk_ids: list[str],
        state: str,
    ) -> FileRow:
        return FileRow(
            tier=tier,
            file_path=file_path,
            sha512=sha512,
            mtime_ns=mtime_ns,
            size=size,
            n_chunks=n_chunks,
            chunk_ids=list(chunk_ids),
            state=state,
            updated_at=_now_iso(),
        )

    # -- reads ------------------------------------------------------------

    async def get(self, tier: str, file_path: str) -> FileRow | None:
        return self.db.manifest_rows.get((tier, file_path))

    async def all_files(self) -> list[FileRow]:
        return [self.db.manifest_rows[key] for key in sorted(self.db.manifest_rows)]

    async def files_for_tier(self, tier: str) -> list[FileRow]:
        return [
            self.db.manifest_rows[key]
            for key in sorted(self.db.manifest_rows)
            if key[0] == tier
        ]

    async def needs_reindex(
        self, tier: str, file_path: str, mtime_ns: int, size: int
    ) -> bool:
        row = self.db.manifest_rows.get((tier, file_path))
        if row is None:
            return True
        if row.state != STATE_INDEXED:
            return True
        return row.mtime_ns != mtime_ns or row.size != size

    async def indexed_file_count(
        self, tier: str | None = None, suffix: str | None = None
    ) -> int:
        count = 0
        for (row_tier, file_path), row in self.db.manifest_rows.items():
            if row.state != STATE_INDEXED:
                continue
            if tier is not None and row_tier != tier:
                continue
            if suffix is not None and not file_path.endswith(suffix):
                continue
            count += 1
        return count

    async def expected_chunks(self, tier: str | None = None) -> int:
        total = 0
        for (row_tier, _file_path), row in self.db.manifest_rows.items():
            if row.state != STATE_INDEXED:
                continue
            if tier is not None and row_tier != tier:
                continue
            total += row.n_chunks
        return total

    async def meta_get(self, key: str) -> str | None:
        return self.db.meta.get(key)

    # -- writes -----------------------------------------------------------

    async def upsert(
        self,
        *,
        tier: str,
        file_path: str,
        sha512: str,
        mtime_ns: int,
        size: int,
        n_chunks: int,
        chunk_ids: list[str],
        state: str,
    ) -> None:
        self.db.manifest_rows[(tier, file_path)] = self._make_row(
            tier=tier, file_path=file_path, sha512=sha512, mtime_ns=mtime_ns,
            size=size, n_chunks=n_chunks, chunk_ids=chunk_ids, state=state,
        )

    async def replace(
        self,
        *,
        tier: str,
        file_path: str,
        sha512: str,
        mtime_ns: int,
        size: int,
        n_chunks: int,
        chunk_ids: list[str],
        state: str,
    ) -> None:
        await self.upsert(
            tier=tier, file_path=file_path, sha512=sha512, mtime_ns=mtime_ns,
            size=size, n_chunks=n_chunks, chunk_ids=chunk_ids, state=state,
        )

    async def set_state(self, tier: str, file_path: str, state: str) -> None:
        row = self.db.manifest_rows.get((tier, file_path))
        if row is None:
            return
        self.db.manifest_rows[(tier, file_path)] = self._make_row(
            tier=tier, file_path=file_path, sha512=row.sha512, mtime_ns=row.mtime_ns,
            size=row.size, n_chunks=row.n_chunks, chunk_ids=row.chunk_ids, state=state,
        )

    async def delete(self, tier: str, file_path: str) -> None:
        self.db.manifest_rows.pop((tier, file_path), None)

    async def meta_set(self, key: str, value: str) -> None:
        self.db.meta[key] = value

    async def meta_delete(self, key: str) -> None:
        self.db.meta.pop(key, None)

    async def reset_tier(self, tier: str) -> None:
        for (row_tier, file_path), row in list(self.db.manifest_rows.items()):
            if row_tier == tier:
                await self.set_state(tier, file_path, "dirty")

    # -- pure fragment builders (SYNC, exactly like the real manifest) ----

    def replace_fragment(
        self,
        *,
        tier: str,
        file_path: str,
        sha512: str,
        mtime_ns: int,
        size: int,
        n_chunks: int,
        chunk_ids: list[str],
        state: str,
    ) -> FakeFragment:
        """Build the manifest-replace fragment (a DELETE then a CREATE)."""
        prefix = MANIFEST_FRAGMENT_PARAM_PREFIX
        params = {
            f"{prefix}id": [tier, file_path],
            f"{prefix}sha512": sha512,
            f"{prefix}state": state,
        }
        row = self._make_row(
            tier=tier, file_path=file_path, sha512=sha512, mtime_ns=mtime_ns,
            size=size, n_chunks=n_chunks, chunk_ids=list(chunk_ids), state=state,
        )

        def effect(db: _FakeSurrealDatabase) -> None:
            db.manifest_rows[(tier, file_path)] = row

        return FakeFragment(
            PRODUCER_MANIFEST, [f"{prefix}delete", f"{prefix}create"], params, effect
        )

    def delete_fragment(self, tier: str, file_path: str) -> FakeFragment:
        """Build the fragment that deletes the ``(tier, file_path)`` manifest row."""
        prefix = MANIFEST_FRAGMENT_PARAM_PREFIX
        params = {f"{prefix}id": [tier, file_path]}

        def effect(db: _FakeSurrealDatabase) -> None:
            db.manifest_rows.pop((tier, file_path), None)

        return FakeFragment(PRODUCER_MANIFEST, [f"{prefix}delete"], params, effect)


# ---------------------------------------------------------------------------
# The code-graph fake (reuses the REAL astroid derivation).
# ---------------------------------------------------------------------------


class FakeSurrealCodeGraph:
    """In-memory async stand-in for :class:`~loremaster.graph_surreal.
    SurrealCodeGraph`.

    The DERIVATION is the real thing — a :class:`~loremaster.graph_surreal.
    _AstroidDerivation` runs the SAME ``_derive_nodes`` / ``_derive_edges``
    production uses — so a node qualified name or an ``imports`` edge dst can
    never drift from the live graph. Only the storage (a per-file slice in the
    shared db) and the query layer (``what_imports`` / ``blast_radius`` /
    ``tests_for`` walking that slice in memory) are the fake's own shim.
    ``build_file_graph_fragment`` / ``purge_file_fragment`` stay SYNC (the pure
    builders); ``reset_resolution_cache`` and the ``*_module_name`` helpers stay
    SYNC exactly as the real graph keeps them.
    """

    def __init__(
        self,
        *,
        db: _FakeSurrealDatabase,
        tier_roots: Mapping[str, str | Path] | None = None,
        project_roots: Sequence[str | Path] | None = None,
    ) -> None:
        self.db = db
        self._derivation = _AstroidDerivation(
            tier_roots=tier_roots, project_roots=project_roots
        )
        self.reset_calls = 0

    # -- lifecycle / naming (SYNC helpers unchanged from the real graph) --

    async def ensure_ready(self) -> None:
        """No-op."""

    async def close(self) -> None:
        """No-op."""

    def reset_resolution_cache(self) -> None:
        """SYNC sweep-boundary reset (records the call for the sweep test)."""
        self.reset_calls += 1
        self._derivation.reset_resolution_cache()

    @staticmethod
    def module_qualified_name(file_path: str) -> str:
        return CodeGraph.module_qualified_name(file_path)

    @staticmethod
    def importable_module_name(base: Path, file_path: str) -> str:
        return CodeGraph.importable_module_name(base, file_path)

    # -- pure fragment builders (SYNC, real derivation at build time) -----

    def build_file_graph_fragment(
        self,
        tier: str,
        file_path: str,
        chunks: Sequence[Chunk],
        *,
        module_name: str | None = None,
    ) -> FakeFragment:
        """Derive ``(tier, file_path)``'s slice and build its replace fragment."""
        module = (
            module_name
            if module_name is not None
            else CodeGraph.module_qualified_name(file_path)
        )
        nodes = self._derivation._derive_nodes(module, list(chunks))
        edges = self._derivation._derive_edges(
            module, list(chunks), tier=tier, file_path=file_path
        )
        prefix = GRAPH_FRAGMENT_PARAM_PREFIX
        # purge(3) + one UPSERT per distinct name + CREATE/answers_to per node +
        # RELATE per edge — the real fragment's statement shape (so the cap counts
        # a realistic number for a graph-heavy file).
        names: set[str] = set()
        for node in nodes:
            names.add(node.qualified_name)
            names.add(CodeGraph._bare_name(node.qualified_name))
        for edge in edges:
            names.add(edge.dst)
        statements = (
            [f"{prefix}purge{i}" for i in range(3)]
            + [f"{prefix}name{i}" for i in range(len(names))]
            + [f"{prefix}node{i}_{s}" for i in range(len(nodes)) for s in range(3)]
            + [f"{prefix}edge{i}" for i in range(len(edges))]
        )
        params = {f"{prefix}tier": tier, f"{prefix}file": file_path}
        slice_ = _GraphSlice(module=module, nodes=list(nodes), edges=list(edges))

        def effect(db: _FakeSurrealDatabase) -> None:
            db.graph_slices[(tier, file_path)] = slice_

        return FakeFragment(PRODUCER_GRAPH, statements, params, effect)

    def purge_file_fragment(self, tier: str, file_path: str) -> FakeFragment:
        """Build the fragment that purges one file's whole graph slice."""
        prefix = GRAPH_FRAGMENT_PARAM_PREFIX
        params = {f"{prefix}tier": tier, f"{prefix}file": file_path}

        def effect(db: _FakeSurrealDatabase) -> None:
            db.graph_slices.pop((tier, file_path), None)

        return FakeFragment(
            PRODUCER_GRAPH, [f"{prefix}purge{i}" for i in range(3)], params, effect
        )

    # -- standalone build/delete (used by direct callers, not the atomic path) --

    async def build_file_graph(
        self,
        tier: str,
        file_path: str,
        chunks: Sequence[Chunk],
        *,
        module_name: str | None = None,
    ) -> None:
        fragment = self.build_file_graph_fragment(
            tier, file_path, chunks, module_name=module_name
        )
        fragment.effect(self.db)

    async def delete_file_graph(self, tier: str, file_path: str) -> None:
        self.db.graph_slices.pop((tier, file_path), None)

    # -- reconcile surface ------------------------------------------------

    async def indexed_file_count(self) -> int:
        return len(self.db.graph_slices)

    # -- queries (in-memory walk of the derived slices) -------------------

    def _all_nodes(self) -> list[tuple[str, str, _NodeSpec]]:
        return [
            (tier, file_path, node)
            for (tier, file_path), slice_ in self.db.graph_slices.items()
            for node in slice_.nodes
        ]

    def _graph_node(self, tier: str, file_path: str, node: _NodeSpec) -> GraphNode:
        return GraphNode(
            id=f"{tier}:{file_path}:{node.qualified_name}",
            kind=node.kind,
            qualified_name=node.qualified_name,
            file_path=file_path,
            chunk_id=node.chunk_id,
            tier=tier,
        )

    def _matches(self, dst: str, target: str) -> bool:
        """Whether an edge dst matches ``target`` by fqn, bare, or module prefix."""
        bare = CodeGraph._bare_name(target)
        if dst == target or CodeGraph._bare_name(dst) == bare:
            return True
        # A module target reaches every symbol resolved under ``<module>.``.
        return dst.startswith(f"{target}.")

    async def what_imports(self, target: str) -> list[GraphNode]:
        """The MODULE nodes that import ``target`` (by fqn / bare / module reach)."""
        found: dict[str, GraphNode] = {}
        for (tier, file_path), slice_ in self.db.graph_slices.items():
            imports_target = any(
                edge.kind == EDGE_IMPORTS and self._matches(edge.dst, target)
                for edge in slice_.edges
            )
            if not imports_target:
                continue
            for node in slice_.nodes:
                if node.kind == KIND_MODULE:
                    graph_node = self._graph_node(tier, file_path, node)
                    found[graph_node.id] = graph_node
        return list(found.values())

    async def _reverse_neighbours(self, frontier: set[str]) -> list[GraphNode]:
        found: dict[str, GraphNode] = {}
        for (tier, file_path), slice_ in self.db.graph_slices.items():
            hits = any(
                self._matches(edge.dst, name)
                for edge in slice_.edges
                for name in frontier
            )
            if not hits:
                continue
            for node in slice_.nodes:
                graph_node = self._graph_node(tier, file_path, node)
                found[graph_node.qualified_name] = graph_node
        return list(found.values())

    async def blast_radius(
        self, target: str, depth: int, max_results: int
    ) -> list[GraphNode]:
        """The bounded reverse-reference transitive closure from ``target``."""
        if depth < 0 or max_results <= 0:
            return []
        frontier = {target}
        found: dict[str, GraphNode] = {}
        visited = {target}
        for _hop in range(depth):
            if not frontier or len(found) >= max_results:
                break
            next_frontier: set[str] = set()
            for node in await self._reverse_neighbours(frontier):
                if node.qualified_name == target or node.qualified_name in found:
                    continue
                found[node.qualified_name] = node
                if node.qualified_name not in visited:
                    visited.add(node.qualified_name)
                    next_frontier.add(node.qualified_name)
                if len(found) >= max_results:
                    break
            frontier = next_frontier
        return list(found.values())[:max_results]

    async def tests_for(self, symbol_or_file: str) -> list[GraphNode]:
        """The test-path nodes that reference ``symbol_or_file`` (any kind)."""
        target_bare = CodeGraph._bare_name(symbol_or_file)
        related: dict[str, GraphNode] = {}
        for (tier, file_path), slice_ in self.db.graph_slices.items():
            if not CodeGraph._is_test_path(file_path):
                continue
            references = any(
                self._matches(edge.dst, symbol_or_file)
                or CodeGraph._bare_name(edge.dst) == target_bare
                for edge in slice_.edges
            )
            heuristic = any(
                CodeGraph._bare_name(node.qualified_name) == f"test_{target_bare}"
                for node in slice_.nodes
            )
            if references or heuristic:
                for node in slice_.nodes:
                    graph_node = self._graph_node(tier, file_path, node)
                    related[graph_node.id] = graph_node
        return list(related.values())

    async def references(self, name: str) -> ReferenceSummary:
        """The reference profile of ``name`` split production vs test."""
        bare = CodeGraph._bare_name(name)
        production: set[str] = set()
        test: set[str] = set()
        referencing: list[GraphNode] = []
        for (tier, file_path), slice_ in self.db.graph_slices.items():
            for edge in slice_.edges:
                if edge.kind not in _REFERENCE_KINDS:
                    continue
                if not (edge.dst == name or CodeGraph._bare_name(edge.dst) == bare):
                    continue
                if edge.src == name:
                    continue  # self-reference excluded
                bucket = test if CodeGraph._is_test_path(file_path) else production
                bucket.add(edge.src)
                for node in slice_.nodes:
                    if node.qualified_name == edge.src:
                        referencing.append(self._graph_node(tier, file_path, node))
        return ReferenceSummary(
            qualified_name=name,
            production_references=len(production),
            test_references=len(test),
            referencing=referencing,
        )

    # -- inspection helpers (test-only) -----------------------------------

    def qnames_for(self, tier: str, file_path: str) -> set[str]:
        """The qualified names the slice holds for ``(tier, file_path)``."""
        slice_ = self.db.graph_slices.get((tier, file_path))
        return {node.qualified_name for node in slice_.nodes} if slice_ else set()

    def all_qnames(self) -> set[str]:
        """Every qualified name across every slice."""
        return {node.qualified_name for _t, _f, node in self._all_nodes()}

    def module_node_count(self) -> int:
        """The number of ``module`` nodes across every slice."""
        return sum(
            1 for _t, _f, node in self._all_nodes() if node.kind == KIND_MODULE
        )

    def tier_function_qnames(self, tier: str) -> set[str]:
        """The function-node qualified names scoped to ``tier``."""
        from loremaster.graph import KIND_FUNCTION

        return {
            node.qualified_name
            for node_tier, _f, node in self._all_nodes()
            if node_tier == tier and node.kind == KIND_FUNCTION
        }


# ---------------------------------------------------------------------------
# Trio builder.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FakeSurrealTrio:
    """The three fakes sharing one database, plus that database."""

    store: FakeSurrealStore
    manifest: FakeSurrealManifest
    graph: FakeSurrealCodeGraph
    db: _FakeSurrealDatabase


def fake_surreal_trio(
    *,
    dim: int,
    tier_roots: Mapping[str, str | Path] | None = None,
    project_roots: Sequence[str | Path] | None = None,
    file_text_max_bytes: int = FILE_TEXT_MAX_BYTES,
    txn_statement_hard_cap: int = TXN_STATEMENT_HARD_CAP,
) -> FakeSurrealTrio:
    """Build store + manifest + graph fakes over ONE shared database.

    The overridable ceilings let a unit test drive the oversize-``file_text``
    skip (a small file crosses a small ``file_text_max_bytes``) and the
    cap-overflow failed-state (a small file crosses a small
    ``txn_statement_hard_cap``) cheaply — the indexer reads both from the store
    (clause 5), never a hand-copied literal.
    """
    db = _FakeSurrealDatabase()
    store = FakeSurrealStore(
        dim=dim,
        file_text_max_bytes=file_text_max_bytes,
        txn_statement_hard_cap=txn_statement_hard_cap,
        db=db,
    )
    manifest = FakeSurrealManifest(db=db)
    graph = FakeSurrealCodeGraph(
        db=db, tier_roots=tier_roots, project_roots=project_roots
    )
    return FakeSurrealTrio(store=store, manifest=manifest, graph=graph, db=db)
