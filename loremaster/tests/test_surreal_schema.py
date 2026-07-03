"""Contract tests for ``loremaster.store.surreal_schema`` against the REAL server.

``surreal_schema.generate_ddl`` is a PURE, config-driven function: given the
configured embedding width it emits the SurrealDB DDL for lore's unified store
(SCHEMAFULL tables + the HNSW / BM25-FULLTEXT / composite indexes + the
``code_ident`` analyzer). These tests pin it two ways:

* **String-level (offline):** the generated DDL threads the *configured* ``dim``
  into every HNSW index and never leaks a different width — the anti-hardcode
  guard. The expected width comes from the argument the test passed, never from
  re-reading the implementation.
* **Behavioural (real server, 3.0.5 and 3.1.5 both verified — 3.1.x is the
  documented floor going forward):** the DDL APPLIES cleanly, applies again
  IDEMPOTENTLY (``IF NOT EXISTS`` semantics), yields the specified tables /
  indexes / analyzer as observed via ``INFO FOR DB`` / ``INFO FOR TABLE``, a
  probe row round-trips per field-specified table, the ``code_ident`` analyzer
  splits identifiers the way the P0 spike verified, and an HNSW index built at
  width *D* accepts a *D*-vector but LOUDLY rejects a wrong-width one.

Expected until P2 lands: collection ERROR in THIS FILE — ``ModuleNotFoundError:
loremaster.store.surreal_schema`` (the module does not exist yet).

P5-C1b (this addition): promotes ``snapshot`` / ``snapshot_entry`` / ``command``
from the P2 bare-``SCHEMAFULL``-placeholder tables to full field-level
definitions (``finding`` stays a placeholder — P9 scope). See
``TestStructuralTableFieldDefinitions`` (offline DDL-string pins),
``TestSnapshotRoundTrip`` / ``TestSnapshotEntryRoundTrip`` /
``TestCommandDefaultsAndConstraints`` (live behavioural pins), and the extra
idempotency probe appended to ``TestSchemaAppliesToServer``.
"""

from __future__ import annotations

import re
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
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
from loremaster.store.surreal_schema import (
    COMMAND_TABLE,
    SNAPSHOT_ENTRY_TABLE,
    SNAPSHOT_TABLE,
    generate_ddl,
)

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

# --- P5-C1b: snapshot / snapshot_entry / command field-level fixtures -------

# THIS repo's own root — used to read a REAL git ref/branch live (below) rather
# than hand-typing a hex-string look-alike.
_REPO_ROOT = Path(__file__).resolve().parents[2]


def _git_output(*args: str) -> str:
    """A value read live from THIS repo's own git metadata (never hand-typed)."""
    return subprocess.check_output(["git", *args], cwd=_REPO_ROOT, text=True).strip()


# The ACTUAL current commit/branch of this repo — grounds ``snapshot.git_ref``/
# ``git_branch`` fixtures in a real git identity (clause 1/5), not an invented
# 40-hex-char look-alike.
GIT_REF = _git_output("rev-parse", "HEAD")
GIT_BRANCH = _git_output("rev-parse", "--abbrev-ref", "HEAD")

# A generous wall-clock skew allowance for the ``DEFAULT time::now()`` sanity
# bound below — loose enough to absorb container/CI clock jitter, tight enough
# to catch "no default at all" (an unset ``option<datetime>`` reads back
# ``None``, which fails the ``isinstance`` check before the bound is even
# reached) or a wildly wrong epoch/unit.
_CLOCK_SKEW_ALLOWANCE = timedelta(seconds=30)

# A realistic multi-file snapshot scale: 118 is THIS repo's own recorded
# astroid-graph cold-build file count (project memory, from a live run) — not a
# convenience round number. ``chunks_total`` reflects a realistic multi-chunk-
# per-file ratio for Odoo-style source (~6x).
_SNAPSHOT_FILES_TOTAL = 118
_SNAPSHOT_CHUNKS_TOTAL = 734

# Realistic Odoo-domain source bodies for the two chunks a single file's
# ``chunk_hashes`` entry tracks — the actual shape ``sha512_hex`` (the SAME
# hashing helper production uses) hashes, not placeholder strings.
_ACTION_CONFIRM_BODY = (
    "def action_confirm(self):\n"
    "    for order in self:\n"
    "        order.write({'state': 'purchase'})\n"
    "    return True\n"
)
_BUTTON_CONFIRM_BODY = "def button_confirm(self):\n    return self.action_confirm()\n"

# A sibling file in the same probe directory — the second row a purge/diff
# scan over ONE snapshot needs to distinguish from ``_PROBE_FILE``.
_SIBLING_FILE = "models/purchase_order_line.py"

# The command-status domain the REQUIREMENT pins — kept as LOCAL test constants
# (never imported from the not-yet-implemented schema, since this IS the
# contract under test, not an existing convention to read).
COMMAND_STATUS_PENDING = "pending"
COMMAND_STATUS_DONE = "done"
COMMAND_STATUS_FAILED = "failed"
COMMAND_STATUSES = (COMMAND_STATUS_PENDING, COMMAND_STATUS_DONE, COMMAND_STATUS_FAILED)
COMMAND_STATUS_INVALID = "bogus"

# A realistic command a scout would enqueue: reindex one changed file.
_COMMAND_KIND_REINDEX_FILE = "reindex_file"
_COMMAND_PAYLOAD: dict[str, Any] = {
    "tier": TIER_A,
    "file_path": _PROBE_FILE,
    "reason": {"trigger": "watcher", "mtime_ns": 1_719_800_000_000_000_000},
}


def _snapshot_entry_chunk_hashes() -> list[dict[str, str]]:
    """Realistic ``chunk_hashes``: per-chunk identity + sha512, the shape a
    snapshot-diff scan needs to detect a changed chunk without re-reading its
    full body.
    """
    return [
        {"identity": "PurchaseOrder.action_confirm", "hash": sha512_hex(_ACTION_CONFIRM_BODY)},
        {"identity": "PurchaseOrder.button_confirm", "hash": sha512_hex(_BUTTON_CONFIRM_BODY)},
    ]


def _as_utc(value: datetime) -> datetime:
    """Normalise a possibly-naive ``datetime`` to UTC for a skew-bound comparison."""
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _field_statement(ddl: str, table: str, field: str) -> str:
    """Return the single ``DEFINE FIELD ... ON <table> ...`` statement for
    ``field`` on ``table``, isolated from the rest of the DDL string so a
    per-field assertion can't be fooled by a substring match against some
    OTHER field or table (e.g. ``status`` also appearing in an unrelated
    clause).

    Raises:
        AssertionError: No matching ``DEFINE FIELD`` statement was found.
    """
    marker = f"DEFINE FIELD IF NOT EXISTS {field} ON {table} "
    for statement in ddl.split(";\n"):
        if statement.strip().startswith(marker):
            return statement
    raise AssertionError(f"no DEFINE FIELD statement found for {table}.{field} in generated DDL")


def _index_statements(ddl: str, table: str, *, fields_pattern: str) -> list[str]:
    """All ``DEFINE INDEX ... ON <table> ...`` statements whose ``FIELDS``
    clause matches ``fields_pattern`` (a regex fragment, e.g. ``r"snapshot\\b"``).
    """
    return [
        statement
        for statement in ddl.split(";\n")
        if statement.strip().startswith("DEFINE INDEX IF NOT EXISTS")
        and f"ON {table} " in statement
        and re.search(rf"FIELDS\s+{fields_pattern}", statement)
    ]


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


async def _create_snapshot(
    connection: SurrealConnection,
    *,
    snapshot_id: str,
    git_ref: str | None = None,
    git_branch: str | None = None,
    files_total: int = _SNAPSHOT_FILES_TOTAL,
    chunks_total: int = _SNAPSHOT_CHUNKS_TOTAL,
) -> None:
    """CREATE a ``snapshot`` row.

    Omits ``git_ref``/``git_branch`` from the SET clause entirely when ``None``
    — mirroring how a non-git-repo caller would never emit them, rather than
    explicitly writing a NONE — so the "absent for non-git repos" contract is
    exercised at the same seam a real writer hits.
    """
    fields: dict[str, Any] = {"files_total": files_total, "chunks_total": chunks_total}
    if git_ref is not None:
        fields["git_ref"] = git_ref
    if git_branch is not None:
        fields["git_branch"] = git_branch
    set_clause = ", ".join(f"{name} = ${name}" for name in fields)
    await run(
        connection,
        f"CREATE type::record('snapshot', $id) SET {set_clause}",
        {"id": snapshot_id, **fields},
    )


async def _create_snapshot_entry(
    connection: SurrealConnection,
    *,
    entry_id: str,
    snapshot_id: str,
    tier: str,
    file_path: str,
    sha512: str,
    chunk_hashes: list[dict[str, str]],
) -> None:
    """CREATE a ``snapshot_entry`` row linked to its parent via ``type::record``."""
    await run(
        connection,
        "CREATE type::record('snapshot_entry', $id) SET "
        "snapshot = type::record('snapshot', $snapshot_id), tier = $tier, "
        "file_path = $file_path, sha512 = $sha512, chunk_hashes = $chunk_hashes",
        {
            "id": entry_id,
            "snapshot_id": snapshot_id,
            "tier": tier,
            "file_path": file_path,
            "sha512": sha512,
            "chunk_hashes": chunk_hashes,
        },
    )


async def _create_command(
    connection: SurrealConnection,
    *,
    command_id: str,
    kind: str,
    payload: dict[str, Any] | None = None,
    status: str | None = None,
    error: str | None = None,
) -> None:
    """CREATE a ``command`` row.

    Omits any field the caller left unset so the schema's own DEFAULTs
    (``status``/``created_at``/``payload``) are exercised rather than shadowed
    by an explicit value on every call.
    """
    fields: dict[str, Any] = {"kind": kind}
    set_parts = ["kind = $kind"]
    if payload is not None:
        fields["payload"] = payload
        set_parts.append("payload = $payload")
    if status is not None:
        fields["status"] = status
        set_parts.append("status = $status")
    if error is not None:
        fields["error"] = error
        set_parts.append("error = $error")
    await run(
        connection,
        f"CREATE type::record('command', $id) SET {', '.join(set_parts)}",
        {"id": command_id, **fields},
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
    """The generated DDL applies to the live engine (3.1.x floor) and is idempotent."""

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

    async def test_ddl_is_idempotent_for_structural_tables(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        # Mirrors ``test_ddl_is_idempotent`` above but for the newly-promoted
        # snapshot/snapshot_entry/command tables: applying the DDL twice must
        # still leave them usable — a probe row round-trips on each.
        connection, env = admin_db
        ddl = generate_ddl(dim=env.dim)
        await run(connection, ddl)
        await run(connection, ddl)  # second application — must be a safe no-op

        await _create_snapshot(
            connection,
            snapshot_id="idem_snap",
            git_ref=GIT_REF,
            git_branch=GIT_BRANCH,
            files_total=_SNAPSHOT_FILES_TOTAL,
            chunks_total=_SNAPSHOT_CHUNKS_TOTAL,
        )
        await _create_snapshot_entry(
            connection,
            entry_id="idem_entry",
            snapshot_id="idem_snap",
            tier=TIER_A,
            file_path=_PROBE_FILE,
            sha512=sha512_hex("idempotent snapshot_entry probe body"),
            chunk_hashes=_snapshot_entry_chunk_hashes(),
        )
        await _create_command(
            connection, command_id="idem_cmd", kind=_COMMAND_KIND_REINDEX_FILE, payload=_COMMAND_PAYLOAD
        )

        snapshot_row = _one(await run(connection, "SELECT * FROM type::record('snapshot', 'idem_snap')"))
        entry_row = _one(
            await run(connection, "SELECT * FROM type::record('snapshot_entry', 'idem_entry')")
        )
        command_row = _one(await run(connection, "SELECT * FROM type::record('command', 'idem_cmd')"))
        assert snapshot_row["git_ref"] == GIT_REF
        assert entry_row["chunk_hashes"] == _snapshot_entry_chunk_hashes()
        assert command_row["status"] == COMMAND_STATUS_PENDING


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


class TestStructuralTableFieldDefinitions:
    """P5-C1b: ``snapshot``/``snapshot_entry``/``command`` carry real fields, not
    the placeholder bare-``SCHEMAFULL`` tables landed in P2 (offline,
    string-level assertions on the generator's own output — no server needed).
    """

    def test_snapshot_fields_are_defined(self) -> None:
        ddl = generate_ddl(dim=NONDEFAULT_DIM)

        created_at = _field_statement(ddl, SNAPSHOT_TABLE, "created_at")
        assert "TYPE datetime" in created_at
        assert "DEFAULT" in created_at and "time::now()" in created_at

        assert "option<string>" in _field_statement(ddl, SNAPSHOT_TABLE, "git_ref")
        assert "option<string>" in _field_statement(ddl, SNAPSHOT_TABLE, "git_branch")
        assert "TYPE int" in _field_statement(ddl, SNAPSHOT_TABLE, "files_total")
        assert "TYPE int" in _field_statement(ddl, SNAPSHOT_TABLE, "chunks_total")

    def test_snapshot_entry_fields_and_link_are_defined(self) -> None:
        ddl = generate_ddl(dim=NONDEFAULT_DIM)

        link = _field_statement(ddl, SNAPSHOT_ENTRY_TABLE, "snapshot")
        # A REAL record link to the parent table — not a bare string copy of
        # the id, which would silently break dot-traversal / FETCH.
        assert f"record<{SNAPSHOT_TABLE}>" in link

        for field in ("tier", "file_path", "sha512"):
            assert "string" in _field_statement(ddl, SNAPSHOT_ENTRY_TABLE, field)

        chunk_hashes = _field_statement(ddl, SNAPSHOT_ENTRY_TABLE, "chunk_hashes")
        assert "FLEXIBLE" in chunk_hashes

    def test_snapshot_entry_has_nonunique_snapshot_index(self) -> None:
        ddl = generate_ddl(dim=NONDEFAULT_DIM)
        matches = _index_statements(ddl, SNAPSHOT_ENTRY_TABLE, fields_pattern=r"snapshot\b")
        assert matches, "expected a DEFINE INDEX on snapshot_entry.snapshot"
        # A purge/diff scan by parent must never be blocked by a wrongly-UNIQUE
        # index — two entries legitimately share one snapshot.
        assert not any("UNIQUE" in statement for statement in matches)

    def test_command_fields_are_defined(self) -> None:
        ddl = generate_ddl(dim=NONDEFAULT_DIM)

        kind = _field_statement(ddl, COMMAND_TABLE, "kind")
        assert "TYPE string" in kind
        # Non-optional typing alone rejects a MISSING kind but not an EMPTY
        # one — the empty-string rejection needs a real ASSERT.
        assert "ASSERT" in kind

        payload = _field_statement(ddl, COMMAND_TABLE, "payload")
        assert "FLEXIBLE" in payload
        assert "DEFAULT" in payload and "{}" in payload

        created_at = _field_statement(ddl, COMMAND_TABLE, "created_at")
        assert "TYPE datetime" in created_at
        assert "DEFAULT" in created_at and "time::now()" in created_at

        assert "option<datetime>" in _field_statement(ddl, COMMAND_TABLE, "processed_at")
        assert "option<string>" in _field_statement(ddl, COMMAND_TABLE, "error")

    def test_command_status_domain_is_constrained(self) -> None:
        ddl = generate_ddl(dim=NONDEFAULT_DIM)
        status = _field_statement(ddl, COMMAND_TABLE, "status")
        assert "TYPE string" in status
        assert "DEFAULT" in status and f"'{COMMAND_STATUS_PENDING}'" in status
        assert "ASSERT" in status
        for value in COMMAND_STATUSES:
            assert f"'{value}'" in status

    def test_command_has_status_index(self) -> None:
        ddl = generate_ddl(dim=NONDEFAULT_DIM)
        matches = _index_statements(ddl, COMMAND_TABLE, fields_pattern=r"status\b")
        assert matches, "expected a DEFINE INDEX on command.status (the scout's poll-fallback query)"


class TestSnapshotRoundTrip:
    """The ``snapshot`` table: full field round-trip, non-git-repo absence, the
    ``created_at`` DEFAULT, and real SCHEMAFULL enforcement.
    """

    async def test_snapshot_probe_round_trips_with_git_metadata(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        await _create_snapshot(
            connection,
            snapshot_id="snap_git",
            git_ref=GIT_REF,
            git_branch=GIT_BRANCH,
            files_total=_SNAPSHOT_FILES_TOTAL,
            chunks_total=_SNAPSHOT_CHUNKS_TOTAL,
        )
        row = _one(await run(connection, "SELECT * FROM type::record('snapshot', 'snap_git')"))
        assert row["git_ref"] == GIT_REF
        assert row["git_branch"] == GIT_BRANCH
        assert row["files_total"] == _SNAPSHOT_FILES_TOTAL
        assert row["chunks_total"] == _SNAPSHOT_CHUNKS_TOTAL

    async def test_snapshot_git_fields_absent_for_non_git_repo(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        # A tarball-imported (non-git) codebase never has a commit/branch — the
        # writer simply never emits these two fields at all.
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        await _create_snapshot(connection, snapshot_id="snap_nogit", files_total=3, chunks_total=9)
        row = _one(await run(connection, "SELECT * FROM type::record('snapshot', 'snap_nogit')"))
        assert row.get("git_ref") is None
        assert row.get("git_branch") is None

    async def test_snapshot_created_at_is_auto_populated(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        before = datetime.now(UTC)
        await _create_snapshot(connection, snapshot_id="snap_ts", files_total=1, chunks_total=1)
        after = datetime.now(UTC)
        row = _one(await run(connection, "SELECT * FROM type::record('snapshot', 'snap_ts')"))
        created_at = row["created_at"]
        assert isinstance(created_at, datetime)
        # Sanity BOUND, not exact equality: the engine's own clock stamped
        # something inside this test's wall-clock window (loose skew allowance
        # for container jitter) — catches "no DEFAULT at all" (None fails the
        # isinstance check above) and "wrong epoch/unit" alike.
        assert before - _CLOCK_SKEW_ALLOWANCE <= _as_utc(created_at) <= after + _CLOCK_SKEW_ALLOWANCE

    async def test_snapshot_rejects_undeclared_field(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        # Proves ``snapshot`` is a REAL SCHEMAFULL table, not a bare placeholder
        # that happens to accept anything written at it.
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        with pytest.raises(Exception):  # noqa: B017 - engine SCHEMAFULL rejection surface
            await run(
                connection,
                "CREATE type::record('snapshot', $id) SET files_total = $files_total, "
                "chunks_total = $chunks_total, rogue_field = $rogue_field",
                {
                    "id": "rogue",
                    "files_total": 1,
                    "chunks_total": 1,
                    "rogue_field": "not in the schema",
                },
            )


class TestSnapshotEntryRoundTrip:
    """The ``snapshot_entry`` table: FLEXIBLE ``chunk_hashes`` fidelity, the
    parent record link resolving to real data, and the non-unique
    parent-scoped index backing a purge/diff scan.
    """

    async def test_snapshot_entry_round_trips_chunk_hashes_and_resolves_parent_link(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        await _create_snapshot(
            connection,
            snapshot_id="snap_entry_parent",
            git_ref=GIT_REF,
            git_branch=GIT_BRANCH,
            files_total=_SNAPSHOT_FILES_TOTAL,
            chunks_total=_SNAPSHOT_CHUNKS_TOTAL,
        )
        chunk_hashes = _snapshot_entry_chunk_hashes()
        digest = sha512_hex(_ACTION_CONFIRM_BODY + _BUTTON_CONFIRM_BODY)
        await _create_snapshot_entry(
            connection,
            entry_id="entry_one",
            snapshot_id="snap_entry_parent",
            tier=TIER_A,
            file_path=_PROBE_FILE,
            sha512=digest,
            chunk_hashes=chunk_hashes,
        )
        row = _one(await run(connection, "SELECT * FROM type::record('snapshot_entry', 'entry_one')"))
        assert row["tier"] == TIER_A
        assert row["file_path"] == _PROBE_FILE
        assert row["sha512"] == digest
        # Round-trip fidelity of the FLEXIBLE array-of-object column: both
        # keys, both entries, in the order written — not just "an object
        # survived".
        assert row["chunk_hashes"] == chunk_hashes

        # The link must resolve to the ACTUAL parent row — hop through it and
        # read the parent's OWN data, rather than trusting an opaque id string.
        parent = _one(await run(connection, "SELECT * FROM $ref", {"ref": row["snapshot"]}))
        assert parent["files_total"] == _SNAPSHOT_FILES_TOTAL
        assert parent["git_ref"] == GIT_REF

    async def test_snapshot_entry_index_permits_multiple_entries_and_scans_by_parent(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        await _create_snapshot(
            connection,
            snapshot_id="snap_multi",
            files_total=_SNAPSHOT_FILES_TOTAL,
            chunks_total=_SNAPSHOT_CHUNKS_TOTAL,
        )
        chunk_hashes = _snapshot_entry_chunk_hashes()
        await _create_snapshot_entry(
            connection,
            entry_id="multi_a",
            snapshot_id="snap_multi",
            tier=TIER_A,
            file_path=_PROBE_FILE,
            sha512=sha512_hex(_ACTION_CONFIRM_BODY),
            chunk_hashes=chunk_hashes,
        )
        # A SECOND row under the SAME parent must succeed — a wrongly-UNIQUE
        # index on ``snapshot`` alone would reject this.
        await _create_snapshot_entry(
            connection,
            entry_id="multi_b",
            snapshot_id="snap_multi",
            tier=TIER_A,
            file_path=_SIBLING_FILE,
            sha512=sha512_hex(_BUTTON_CONFIRM_BODY),
            chunk_hashes=chunk_hashes,
        )
        rows = await run(
            connection,
            "SELECT file_path FROM snapshot_entry WHERE snapshot = type::record('snapshot', $sid)",
            {"sid": "snap_multi"},
        )
        file_paths = {row["file_path"] for row in rows}
        assert file_paths == {_PROBE_FILE, _SIBLING_FILE}


class TestCommandDefaultsAndConstraints:
    """The ``command`` table: defaults (status/created_at/payload), the closed
    status domain, and the required, non-empty ``kind``.
    """

    async def test_command_created_with_defaults_has_pending_status_and_auto_timestamp(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        before = datetime.now(UTC)
        await _create_command(
            connection, command_id="cmd_defaults", kind=_COMMAND_KIND_REINDEX_FILE, payload=_COMMAND_PAYLOAD
        )
        after = datetime.now(UTC)
        row = _one(await run(connection, "SELECT * FROM type::record('command', 'cmd_defaults')"))
        assert row["kind"] == _COMMAND_KIND_REINDEX_FILE
        assert row["status"] == COMMAND_STATUS_PENDING
        assert isinstance(row["created_at"], datetime)
        assert before - _CLOCK_SKEW_ALLOWANCE <= _as_utc(row["created_at"]) <= after + _CLOCK_SKEW_ALLOWANCE
        assert row.get("processed_at") is None
        assert row.get("error") is None

    async def test_command_payload_defaults_to_empty_object_when_omitted(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        await _create_command(connection, command_id="cmd_no_payload", kind=_COMMAND_KIND_REINDEX_FILE)
        row = _one(await run(connection, "SELECT * FROM type::record('command', 'cmd_no_payload')"))
        assert row["payload"] == {}

    async def test_command_payload_round_trips_nested_structure(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        await _create_command(
            connection, command_id="cmd_nested", kind=_COMMAND_KIND_REINDEX_FILE, payload=_COMMAND_PAYLOAD
        )
        row = _one(await run(connection, "SELECT * FROM type::record('command', 'cmd_nested')"))
        assert row["payload"] == _COMMAND_PAYLOAD

    @pytest.mark.parametrize("status", COMMAND_STATUSES)
    async def test_command_accepts_each_valid_status(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        status: str,
    ) -> None:
        # Positive control alongside the negative test below: an overly-strict
        # ASSERT (e.g. one that only accepts the DEFAULT) would silently pass
        # the negative test while breaking every real status transition.
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        command_id = f"cmd_status_{status}"
        await _create_command(
            connection, command_id=command_id, kind=_COMMAND_KIND_REINDEX_FILE, status=status
        )
        row = _one(await run(connection, f"SELECT * FROM type::record('command', '{command_id}')"))
        assert row["status"] == status

    async def test_command_rejects_unknown_status(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_command(
                connection,
                command_id="cmd_bad_status",
                kind=_COMMAND_KIND_REINDEX_FILE,
                status=COMMAND_STATUS_INVALID,
            )

    async def test_command_rejects_empty_kind(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_command(connection, command_id="cmd_empty_kind", kind="")

    @pytest.mark.parametrize("whitespace_kind", [" ", "   ", "\t"])
    async def test_command_rejects_whitespace_only_kind(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        whitespace_kind: str,
    ) -> None:
        # C1-audit finding #2: "required, non-empty" is meant SEMANTICALLY — a
        # kind of ' '/'   '/'\t' names no command any subscriber could
        # dispatch on, so the ASSERT must reject it as loudly as the exact
        # empty string (trim-aware, not a bare `!= ''` comparison).
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_command(
                connection, command_id="cmd_whitespace_kind", kind=whitespace_kind
            )

    async def test_command_rejects_missing_kind(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        # ``kind`` is a plain (non-``option``) ``string`` with no DEFAULT — a
        # CREATE that never sets it at all must be rejected just as loudly as
        # an explicit empty string.
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        with pytest.raises(Exception):  # noqa: B017 - engine required-field rejection surface
            await run(
                connection,
                "CREATE type::record('command', $id) SET payload = $payload",
                {"id": "cmd_missing_kind", "payload": _COMMAND_PAYLOAD},
            )
