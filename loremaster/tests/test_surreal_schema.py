"""Contract tests for ``loremaster.store.surreal_schema`` against the REAL server.

``surreal_schema.generate_ddl`` is a PURE, config-driven function: given the
configured embedding width it emits the SurrealDB DDL for lore's unified store
(SCHEMAFULL tables + the HNSW / BM25-FULLTEXT / composite indexes + the
``code_ident`` analyzer). These tests pin it two ways:

* **String-level (offline):** the generated DDL threads the *configured* ``dim``
  into every HNSW index and never leaks a different width — the anti-hardcode
  guard. The expected width comes from the argument the test passed, never from
  re-reading the implementation.
* **Behavioural (real 3.0.5 server):** the DDL APPLIES cleanly, applies again
  IDEMPOTENTLY (``IF NOT EXISTS`` semantics), yields the specified tables /
  indexes / analyzer as observed via ``INFO FOR DB`` / ``INFO FOR TABLE``, a
  probe row round-trips per field-specified table, the ``code_ident`` analyzer
  splits identifiers the way the P0 spike verified, and an HNSW index built at
  width *D* accepts a *D*-vector but LOUDLY rejects a wrong-width one.

Expected until P2 lands: collection ERROR in THIS FILE — ``ModuleNotFoundError:
loremaster.store.surreal_schema`` (the module does not exist yet).
"""

from __future__ import annotations

import re
from typing import Any

import pytest
from _surreal_harness import (
    ANALYZER_NAME,
    NONDEFAULT_DIM,
    PRODUCTION_DIM,
    TIER_A,
    SurrealConnection,
    SurrealEnv,
    admin_db,  # noqa: F401 - re-exported pytest fixture
    chunk_record,
    run,
)
from loremaster.index.records import sha512_hex
from loremaster.store.surreal_schema import generate_ddl

# The tables the approved P2 plan requires (the INDEPENDENT source — the plan,
# not the generator's output). ``chunk``/``file``/``file_text``/``memory`` carry
# field-level probes below; the rest are asserted present.
EXPECTED_TABLES = frozenset(
    {
        "chunk",
        "file",
        "file_text",
        "meta",
        "snapshot",
        "snapshot_entry",
        "finding",
        "trace",
        "command",
        "memory",
    }
)

# A realistic file the probes key on (Odoo-style domain path).
_PROBE_FILE = "models/purchase_order.py"


def _one(result: Any) -> dict[str, Any]:
    """Narrow a ``SELECT``'s list result to its single row (probe round-trips)."""
    assert isinstance(result, list) and len(result) == 1, f"expected one row, got {result!r}"
    row = result[0]
    assert isinstance(row, dict)
    return row


async def _create_chunk(
    connection: SurrealConnection,
    *,
    chunk_id: str,
    embedding: list[float],
) -> None:
    """CREATE a fully-populated ``chunk`` row (all SCHEMAFULL required fields set)."""
    record = chunk_record(
        tier=TIER_A, file_path=_PROBE_FILE, identity="PurchaseOrder.action_confirm"
    )
    await run(
        connection,
        "CREATE type::record('chunk', $id) SET "
        "tier=$tier, file_path=$file_path, chunk_type=$chunk_type, identity=$identity, "
        "sub_ordinal=$sub_ordinal, content_hash=$content_hash, mtime_ns=$mtime_ns, "
        "line_start=$line_start, line_end=$line_end, source_text=$source_text, "
        "ident_text=$ident_text, metadata=$metadata, embedding=$embedding",
        {"id": chunk_id, "embedding": embedding, **record.payload},
    )


class TestConfiguredDimension:
    """The HNSW width is the CONFIGURED ``dim``, never a hardcoded default (offline)."""

    def test_generated_ddl_carries_the_configured_width_only(self) -> None:
        # Generate at two realistic widths — the non-production 512 and the real
        # production 2048 — and prove each DDL carries ITS OWN width and never the
        # other. A generator that hardcoded either value fails one direction.
        ddl_small = generate_ddl(dim=NONDEFAULT_DIM)
        ddl_prod = generate_ddl(dim=PRODUCTION_DIM)

        assert re.search(rf"DIMENSION\s+{NONDEFAULT_DIM}\b", ddl_small)
        # The production default must NOT leak into a 512-configured schema.
        assert not re.search(rf"DIMENSION\s+{PRODUCTION_DIM}\b", ddl_small)

        assert re.search(rf"DIMENSION\s+{PRODUCTION_DIM}\b", ddl_prod)
        assert not re.search(rf"DIMENSION\s+{NONDEFAULT_DIM}\b", ddl_prod)

        # Two different configs must not produce byte-identical DDL.
        assert ddl_small != ddl_prod

    def test_both_hnsw_tables_use_the_configured_width(self) -> None:
        # chunk AND memory each define an HNSW index; BOTH must be at the config
        # width (a generator that wired the arg into only one is a latent bug).
        ddl = generate_ddl(dim=NONDEFAULT_DIM)
        hnsw_widths = re.findall(r"DIMENSION\s+(\d+)", ddl)
        assert len(hnsw_widths) >= 2  # chunk + memory
        assert set(hnsw_widths) == {str(NONDEFAULT_DIM)}


class TestSchemaAppliesToServer:
    """The generated DDL applies to the live 3.0.5 engine and is idempotent."""

    async def test_ddl_applies_and_creates_every_planned_table(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        info = await run(connection, "INFO FOR DB")
        tables = set(info.get("tables", {}))
        # Every planned table exists — the plan's set, not the generator's echo.
        assert EXPECTED_TABLES <= tables

    async def test_ddl_is_idempotent(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        # IF NOT EXISTS semantics: applying twice must not raise, and the schema
        # must still be intact afterwards (a probe row round-trips).
        connection, env = admin_db
        ddl = generate_ddl(dim=env.dim)
        await run(connection, ddl)
        await run(connection, ddl)  # second application — must be a safe no-op

        await _create_chunk(connection, chunk_id="probe", embedding=[0.1] * env.dim)
        row = _one(await run(connection, "SELECT * FROM type::record('chunk', 'probe')"))
        expected_source = chunk_record(
            tier=TIER_A, file_path=_PROBE_FILE, identity="PurchaseOrder.action_confirm"
        ).payload["source_text"]
        assert row["source_text"] == expected_source
        assert len(row["embedding"]) == env.dim


class TestAnalyzer:
    """The ``code_ident`` analyzer is defined and splits identifiers as spiked."""

    async def test_analyzer_is_defined(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        info = await run(connection, "INFO FOR DB")
        assert ANALYZER_NAME in info.get("analyzers", {})

    async def test_splits_camelcase_identifier(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        # P0-spike ground truth: PurchaseOrder -> [purchase, order].
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        tokens = await run(connection, f"RETURN search::analyze('{ANALYZER_NAME}', 'PurchaseOrder')")
        assert {"purchase", "order"} <= set(tokens)

    async def test_splits_mixed_identifier_with_trailing_digit(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        # P0-spike ground truth: getUserByID2 -> [get, user, by, id, 2].
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        tokens = await run(connection, f"RETURN search::analyze('{ANALYZER_NAME}', 'getUserByID2')")
        assert {"get", "user", "by", "id", "2"} <= set(tokens)


class TestChunkIndexes:
    """The chunk table carries the HNSW + BM25-FULLTEXT + composite indexes."""

    async def test_chunk_carries_hnsw_and_fulltext_and_composite(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        info = await run(connection, "INFO FOR TABLE chunk")
        index_ddls = list(info.get("indexes", {}).values())

        # HNSW at the configured width.
        assert any("HNSW" in ddl and f"DIMENSION {env.dim}" in ddl for ddl in index_ddls)
        # BM25 FULLTEXT on each searchable text field, using the code analyzer.
        for field in ("ident_text", "source_text", "llm_summary"):
            assert any(
                "FULLTEXT" in ddl and field in ddl and ANALYZER_NAME in ddl for ddl in index_ddls
            ), f"missing FULLTEXT index on chunk.{field}"
        # A non-vector, non-fulltext composite over the filter dimensions.
        assert any(
            "tier" in ddl and "file_path" in ddl and "HNSW" not in ddl and "FULLTEXT" not in ddl
            for ddl in index_ddls
        )


class TestMemoryIndexes:
    """The memory table carries HNSW + FULLTEXT + a valid_until index."""

    async def test_memory_carries_hnsw_fulltext_and_valid_until(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        info = await run(connection, "INFO FOR TABLE memory")
        index_ddls = list(info.get("indexes", {}).values())

        assert any("HNSW" in ddl and f"DIMENSION {env.dim}" in ddl for ddl in index_ddls)
        assert any("FULLTEXT" in ddl for ddl in index_ddls)
        # The temporal-validity index the recall path filters superseded notes on.
        assert any("valid_until" in ddl for ddl in index_ddls)


class TestProbeRoundTrips:
    """A probe row round-trips per field-specified table (chunk/file/file_text/memory)."""

    async def test_chunk_probe_round_trips(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        record = chunk_record(
            tier=TIER_A, file_path=_PROBE_FILE, identity="PurchaseOrder.action_confirm"
        )
        await _create_chunk(connection, chunk_id="c1", embedding=[0.2] * env.dim)
        row = _one(await run(connection, "SELECT * FROM type::record('chunk', 'c1')"))
        assert row["tier"] == TIER_A
        assert row["file_path"] == _PROBE_FILE
        assert row["identity"] == "PurchaseOrder.action_confirm"
        assert row["ident_text"] == record.payload["ident_text"]
        assert len(row["embedding"]) == env.dim

    async def test_file_manifest_probe_round_trips(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        digest = sha512_hex("file body")
        await run(
            connection,
            "CREATE type::record('file', $id) SET sha512=$sha512, mtime_ns=$mtime_ns, "
            "size=$size, n_chunks=$n_chunks, chunk_ids=$chunk_ids, state=$state, "
            "updated_at=time::now()",
            {
                "id": _PROBE_FILE,
                "sha512": digest,
                "mtime_ns": 1_719_800_000_000_000_000,
                "size": 4096,
                "n_chunks": 3,
                "chunk_ids": ["c1", "c2", "c3"],
                "state": "indexed",
            },
        )
        row = _one(
            await run(connection, "SELECT * FROM type::record('file', $id)", {"id": _PROBE_FILE})
        )
        assert row["sha512"] == digest
        assert row["state"] == "indexed"
        assert row["n_chunks"] == 3
        assert row["chunk_ids"] == ["c1", "c2", "c3"]

    async def test_file_state_assert_rejects_unknown_state(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        # The plan pins ``state`` constrained to indexed/dirty/embedding/failed —
        # an out-of-domain state must be LOUDLY rejected, not silently stored.
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await run(
                connection,
                "CREATE type::record('file', $id) SET sha512=$sha512, mtime_ns=0, "
                "size=0, n_chunks=0, chunk_ids=[], state=$state, updated_at=time::now()",
                {"id": "bad_state.py", "sha512": sha512_hex("x"), "state": "banana"},
            )

    async def test_file_text_probe_round_trips(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        body = "class PurchaseOrder(models.Model):\n    _name = 'purchase.order'\n"
        digest = sha512_hex(body)
        await run(
            connection,
            "CREATE type::record('file_text', $id) SET text=$text, sha512=$sha512",
            {"id": _PROBE_FILE, "text": body, "sha512": digest},
        )
        row = _one(
            await run(connection, "SELECT * FROM type::record('file_text', $id)", {"id": _PROBE_FILE})
        )
        assert row["text"] == body
        assert row["sha512"] == digest

    async def test_memory_probe_round_trips(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        note = "PurchaseOrder.action_confirm posts the vendor bill, not the picking."
        await run(
            connection,
            "CREATE type::record('memory', $id) SET note_text=$note_text, refs=$refs, "
            "kind=$kind, trust=$trust, embedding=$embedding, provenance=$provenance, "
            "created_at=time::now()",
            {
                "id": "m1",
                "note_text": note,
                "refs": [],
                "kind": "correction",
                "trust": 0.9,
                "embedding": [0.3] * env.dim,
                "provenance": {"author": "ejprice", "session": "abc123"},
            },
        )
        row = _one(await run(connection, "SELECT * FROM type::record('memory', 'm1')"))
        assert row["note_text"] == note
        assert row["kind"] == "correction"
        assert len(row["embedding"]) == env.dim


class TestHnswWidthEnforced:
    """An HNSW index built at width D accepts a D-vector, LOUDLY rejects others."""

    async def test_accepts_configured_width_rejects_wrong_width(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_ddl(dim=NONDEFAULT_DIM))
        # Exactly the configured width: accepted.
        await _create_chunk(connection, chunk_id="right", embedding=[0.1] * NONDEFAULT_DIM)
        # The production width against a 512 index: the engine rejects it loudly —
        # the wrong-scale guard the whole config-driven-dim contract exists for.
        with pytest.raises(Exception) as excinfo:  # noqa: B017 - engine dim surface
            await _create_chunk(connection, chunk_id="wrong", embedding=[0.1] * PRODUCTION_DIM)
        assert "dimension" in str(excinfo.value).lower()
