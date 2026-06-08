"""Contract tests for ``loremaster.index.records`` under the C1 tiered key.

C1 makes ``tier`` a **first-class KEY dimension**. A module-relative
``file_path`` is not globally unique across tiers (a ``custom`` override and the
``community`` original can share one path), so the point-ID must fold ``tier``
into its natural key, and the payload must carry ``tier``. Otherwise one tier
silently overwrites another's point.

The chosen, documented key string is::

    "{slug}:{tier}:{file_path}:{chunk_type}:{identity}:{sub_ordinal}:{key_version}"

(tier immediately after slug — the project→tier→file ownership ordering). The
``KEY_VERSION`` is bumped from the parked foundation's ``1`` to ``2`` because
this is a breaking re-key of an existing scheme (greenfield, no migration).

These tests pin:

* ``point_id`` is a **deterministic** UUID5 over the tiered natural key, and is
  *sensitive* to every component — crucially, to ``tier`` (the C1 collision).
* The id matches the exact documented key string (drift guard).
* ``sha512_hex`` matches the canonical NIST test vector for ``"abc"``.
* ``chunk_to_record`` stamps ``tier`` into the payload, carries every structural
  field, and merges the chunk's own metadata on top.
* **REAL CORPUS:** a real source file is chunked via lorescribe's
  ``ChunkerRegistry.dispatch_file``; the resulting chunks, recorded under two
  different tiers with an otherwise-identical natural key, produce DISTINCT
  point-IDs and distinct ``tier`` payloads. This is exactly the collision the
  amendment audit caught.
"""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Any

from loremaster.index.records import (
    KEY_VERSION,
    Record,
    chunk_to_record,
    point_id,
    sha512_hex,
)
from lorescribe.models import Chunk, ChunkContext
from lorescribe.python_ast import PythonAstChunker
from lorescribe.registry import ChunkerRegistry
from loresigil.tokens import VoyageTokenCounter

# Canonical NIST SHA-512 test vector for the ASCII string "abc".
_SHA512_ABC = (
    "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a"
    "2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f"
)

# A fixed tiered natural key reused across point_id tests.
_SLUG = "demo"
_TIER_A = "custom"
_TIER_B = "community"
_FILE = "src/pkg/mod.py"
_CHUNK_TYPE = "python_symbol"
_IDENTITY = "pkg.mod.Foo.bar"
_SUB_ORDINAL = 0

# A real source file that exists in this monorepo — chunked for the real-corpus
# collision test (not a synthetic mock).
_REAL_FILE = (
    Path(__file__).resolve().parents[2] / "loresigil" / "loresigil" / "tokens.py"
)


def _make_chunk(**overrides: Any) -> Chunk:
    """Build a representative chunk with sensible defaults, overridable per test."""
    base: dict[str, Any] = {
        "chunk_type": _CHUNK_TYPE,
        "source_text": "def bar(self): ...",
        "identity": _IDENTITY,
        "sub_ordinal": _SUB_ORDINAL,
        "line_start": 10,
        "line_end": 12,
        "metadata": {"language": "python"},
        "metadata_header": "pkg.mod.Foo",
    }
    base.update(overrides)
    return Chunk(**base)


def _chunk_real_file() -> list[Chunk]:
    """Chunk a real ``.py`` file through lorescribe's registry (no mocks)."""
    registry = ChunkerRegistry()
    registry.register("python_ast", PythonAstChunker(), [".py"])
    counter = VoyageTokenCounter()
    ctx = ChunkContext(
        slug=_SLUG,
        file_path=str(_REAL_FILE),
        count_tokens=counter.count,
        max_input_tokens=8192,
    )
    source = _REAL_FILE.read_text(encoding="utf-8")
    return registry.dispatch_file(str(_REAL_FILE), source, ctx)


class TestPointId:
    """The deterministic, tier-sensitive point-ID derivation (C1)."""

    def test_same_inputs_yield_same_id(self) -> None:
        first = point_id(_SLUG, _TIER_A, _FILE, _CHUNK_TYPE, _IDENTITY, _SUB_ORDINAL)
        second = point_id(_SLUG, _TIER_A, _FILE, _CHUNK_TYPE, _IDENTITY, _SUB_ORDINAL)
        assert first == second

    def test_id_is_a_uuid5_over_the_documented_key_string(self) -> None:
        # Drift guard: the exact documented ordering is
        # slug:tier:file_path:chunk_type:identity:sub_ordinal:key_version.
        expected = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"{_SLUG}:{_TIER_A}:{_FILE}:{_CHUNK_TYPE}:{_IDENTITY}"
                f":{_SUB_ORDINAL}:{KEY_VERSION}",
            )
        )
        assert (
            point_id(_SLUG, _TIER_A, _FILE, _CHUNK_TYPE, _IDENTITY, _SUB_ORDINAL)
            == expected
        )

    def test_result_parses_as_a_uuid(self) -> None:
        value = point_id(_SLUG, _TIER_A, _FILE, _CHUNK_TYPE, _IDENTITY, _SUB_ORDINAL)
        assert str(uuid.UUID(value)) == value

    def test_differing_tier_yields_different_id(self) -> None:
        # THE C1 COLLISION: same (slug, file, chunk_type, identity, sub_ordinal),
        # different tier → MUST be distinct ids, or one tier overwrites another.
        a = point_id(_SLUG, _TIER_A, _FILE, _CHUNK_TYPE, _IDENTITY, _SUB_ORDINAL)
        b = point_id(_SLUG, _TIER_B, _FILE, _CHUNK_TYPE, _IDENTITY, _SUB_ORDINAL)
        assert a != b

    def test_differing_identity_yields_different_id(self) -> None:
        a = point_id(_SLUG, _TIER_A, _FILE, _CHUNK_TYPE, "pkg.mod.Foo.bar", _SUB_ORDINAL)
        b = point_id(_SLUG, _TIER_A, _FILE, _CHUNK_TYPE, "pkg.mod.Foo.baz", _SUB_ORDINAL)
        assert a != b

    def test_differing_sub_ordinal_yields_different_id(self) -> None:
        a = point_id(_SLUG, _TIER_A, _FILE, _CHUNK_TYPE, _IDENTITY, 0)
        b = point_id(_SLUG, _TIER_A, _FILE, _CHUNK_TYPE, _IDENTITY, 1)
        assert a != b

    def test_key_version_participates(self) -> None:
        a = point_id(_SLUG, _TIER_A, _FILE, _CHUNK_TYPE, _IDENTITY, _SUB_ORDINAL, key_version=2)
        b = point_id(_SLUG, _TIER_A, _FILE, _CHUNK_TYPE, _IDENTITY, _SUB_ORDINAL, key_version=3)
        assert a != b

    def test_key_version_defaults_to_module_constant(self) -> None:
        explicit = point_id(
            _SLUG, _TIER_A, _FILE, _CHUNK_TYPE, _IDENTITY, _SUB_ORDINAL, key_version=KEY_VERSION
        )
        implicit = point_id(_SLUG, _TIER_A, _FILE, _CHUNK_TYPE, _IDENTITY, _SUB_ORDINAL)
        assert explicit == implicit

    def test_baseline_key_version_is_two(self) -> None:
        # Bumped from the parked foundation's 1 — the tier addition is a breaking
        # re-key of the scheme, so the version moves to make it detectable.
        assert KEY_VERSION == 2

    def test_differing_slug_yields_different_id(self) -> None:
        a = point_id("alpha", _TIER_A, _FILE, _CHUNK_TYPE, _IDENTITY, _SUB_ORDINAL)
        b = point_id("beta", _TIER_A, _FILE, _CHUNK_TYPE, _IDENTITY, _SUB_ORDINAL)
        assert a != b

    def test_differing_file_path_yields_different_id(self) -> None:
        a = point_id(_SLUG, _TIER_A, "src/a.py", _CHUNK_TYPE, _IDENTITY, _SUB_ORDINAL)
        b = point_id(_SLUG, _TIER_A, "src/b.py", _CHUNK_TYPE, _IDENTITY, _SUB_ORDINAL)
        assert a != b


class TestSha512Hex:
    """The SHA-512 content hash helper."""

    def test_matches_known_vector_for_bytes(self) -> None:
        assert sha512_hex(b"abc") == _SHA512_ABC

    def test_accepts_str_input(self) -> None:
        assert sha512_hex("abc") == _SHA512_ABC

    def test_matches_hashlib_for_arbitrary_content(self) -> None:
        payload = b"the quick brown fox\n" * 50
        assert sha512_hex(payload) == hashlib.sha512(payload).hexdigest()


class TestChunkToRecord:
    """Translation of a :class:`Chunk` into a Qdrant :class:`Record` (tiered)."""

    def test_point_id_matches_records_point_id(self) -> None:
        chunk = _make_chunk()
        record = chunk_to_record(
            chunk,
            slug=_SLUG,
            tier=_TIER_A,
            file_path=_FILE,
            content_hash=_SHA512_ABC,
            mtime_ns=123,
        )
        assert record.point_id == point_id(
            _SLUG, _TIER_A, _FILE, chunk.chunk_type, chunk.identity, chunk.sub_ordinal
        )

    def test_embedding_text_is_carried_verbatim(self) -> None:
        chunk = _make_chunk()
        record = chunk_to_record(
            chunk, slug=_SLUG, tier=_TIER_A, file_path=_FILE, content_hash=_SHA512_ABC, mtime_ns=123
        )
        assert record.embedding_text == chunk.embedding_text

    def test_payload_stamps_tier(self) -> None:
        # C1: tier is a stored payload field (powers delete_by_tier + filtering).
        chunk = _make_chunk()
        record = chunk_to_record(
            chunk, slug=_SLUG, tier=_TIER_B, file_path=_FILE, content_hash=_SHA512_ABC, mtime_ns=1
        )
        assert record.payload["tier"] == _TIER_B

    def test_payload_has_all_structural_fields(self) -> None:
        chunk = _make_chunk()
        record = chunk_to_record(
            chunk, slug=_SLUG, tier=_TIER_A, file_path=_FILE, content_hash=_SHA512_ABC, mtime_ns=4567
        )
        payload = record.payload
        assert payload["chunk_type"] == chunk.chunk_type
        assert payload["identity"] == chunk.identity
        assert payload["sub_ordinal"] == chunk.sub_ordinal
        assert payload["tier"] == _TIER_A
        assert payload["file_path"] == _FILE
        assert payload["content_hash"] == _SHA512_ABC
        assert payload["mtime_ns"] == 4567
        assert payload["line_start"] == chunk.line_start
        assert payload["line_end"] == chunk.line_end
        assert payload["source_text"] == chunk.source_text

    def test_payload_merges_chunk_metadata(self) -> None:
        chunk = _make_chunk(metadata={"language": "python", "decorators": ["staticmethod"]})
        record = chunk_to_record(
            chunk, slug=_SLUG, tier=_TIER_A, file_path=_FILE, content_hash=_SHA512_ABC, mtime_ns=1
        )
        assert record.payload["language"] == "python"
        assert record.payload["decorators"] == ["staticmethod"]

    def test_empty_metadata_still_produces_all_structural_fields(self) -> None:
        chunk = _make_chunk(metadata={})
        record = chunk_to_record(
            chunk, slug=_SLUG, tier=_TIER_A, file_path=_FILE, content_hash=_SHA512_ABC, mtime_ns=1
        )
        for key in (
            "chunk_type",
            "identity",
            "sub_ordinal",
            "tier",
            "file_path",
            "content_hash",
            "mtime_ns",
            "line_start",
            "line_end",
            "source_text",
        ):
            assert key in record.payload

    def test_metadata_does_not_mutate_the_chunk(self) -> None:
        chunk = _make_chunk(metadata={"language": "python"})
        record = chunk_to_record(
            chunk, slug=_SLUG, tier=_TIER_A, file_path=_FILE, content_hash=_SHA512_ABC, mtime_ns=1
        )
        record.payload["language"] = "rust"
        assert chunk.metadata["language"] == "python"

    def test_record_exposes_three_fields(self) -> None:
        chunk = _make_chunk()
        record = chunk_to_record(
            chunk, slug=_SLUG, tier=_TIER_A, file_path=_FILE, content_hash=_SHA512_ABC, mtime_ns=1
        )
        assert isinstance(record, Record)
        assert isinstance(record.point_id, str)
        assert isinstance(record.embedding_text, str)
        assert isinstance(record.payload, dict)


class TestRealCorpusTierCollision:
    """REAL CORPUS: the C1 collision proven on chunks of an actual source file."""

    def test_real_file_chunks_under_two_tiers_have_distinct_ids(self) -> None:
        chunks = _chunk_real_file()
        assert chunks, "the real file must produce at least one chunk"

        # Record the SAME chunks under tier A and tier B with an otherwise
        # identical natural key (same slug, file_path, chunk_type, identity,
        # sub_ordinal). Pre-C1 these collided to one id; under C1 they must not.
        ids_a: set[str] = set()
        ids_b: set[str] = set()
        for chunk in chunks:
            record_a = chunk_to_record(
                chunk,
                slug=_SLUG,
                tier=_TIER_A,
                file_path=_FILE,
                content_hash=_SHA512_ABC,
                mtime_ns=1,
            )
            record_b = chunk_to_record(
                chunk,
                slug=_SLUG,
                tier=_TIER_B,
                file_path=_FILE,
                content_hash=_SHA512_ABC,
                mtime_ns=1,
            )
            assert record_a.point_id != record_b.point_id
            assert record_a.payload["tier"] == _TIER_A
            assert record_b.payload["tier"] == _TIER_B
            ids_a.add(record_a.point_id)
            ids_b.add(record_b.point_id)

        # No tier-A id collides with any tier-B id across the whole real file.
        assert ids_a.isdisjoint(ids_b)
        # And within a tier, the real chunker's identity contract keeps every
        # chunk's id unique (no sibling-collapse).
        assert len(ids_a) == len(chunks)
