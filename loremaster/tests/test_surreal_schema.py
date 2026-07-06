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
    FINDING_COUNTER_TABLE,
    FINDING_TABLE,
    SNAPSHOT_ENTRY_TABLE,
    SNAPSHOT_TABLE,
    TRACE_TABLE,
    generate_ddl,
    generate_finding_ddl,
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
        "task",
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


def _snapshot_entry_chunk_hashes() -> list[dict[str, str | int]]:
    """Realistic ``chunk_hashes``: per-chunk identity + ``sub_ordinal`` + sha512,
    the shape a snapshot-diff scan needs to detect a changed chunk (and tell
    same-identity WINDOW siblings apart) without re-reading its full body.

    ``sub_ordinal`` is the within-file disambiguator lorescribe stamps on every
    chunk (0 for the sole/first window; 1, 2, … for the later windows of a long
    function or split markdown section): ``(identity, sub_ordinal)`` — never
    ``identity`` alone — is the natural key, so a snapshot that dropped it would
    collapse siblings last-write-wins. Two DISTINCT single-window identities
    here, each carrying its own ``sub_ordinal`` 0.
    """
    return [
        {
            "identity": "PurchaseOrder.action_confirm",
            "sub_ordinal": 0,
            "hash": sha512_hex(_ACTION_CONFIRM_BODY),
        },
        {
            "identity": "PurchaseOrder.button_confirm",
            "sub_ordinal": 0,
            "hash": sha512_hex(_BUTTON_CONFIRM_BODY),
        },
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
    chunk_hashes: list[dict[str, str | int]],
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
            "CREATE type::record('memory', $id) SET note_text=$note_text, labels=$labels, "
            "kind=$kind, source=$source, embedding=$embedding, created_at=time::now()",
            {
                "id": "m1",
                "note_text": note,
                "labels": [],
                "kind": "correction",
                # P7 wire shape: ``trust`` is a two-value enum riding INSIDE the
                # ``source`` object (the P2 top-level float ``trust`` column was
                # wrong and has been migrated away), and ``provenance`` is renamed
                # to ``source``; the obsolete ``refs`` column is folded into
                # ``labels``.
                "source": {"kind": "operator", "ref": "chat:abc123", "trust": "authoritative"},
                "embedding": [0.3] * env.dim,
            },
        )
        row = _one(await run(connection, "SELECT * FROM type::record('memory', 'm1')"))
        assert row["note_text"] == note
        assert row["kind"] == "correction"
        assert row["source"]["trust"] == "authoritative"
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

    def test_snapshot_entry_chunk_hashes_carries_the_sub_ordinal_disambiguator(self) -> None:
        # F1: lorescribe emits same-``identity`` sibling chunks disambiguated only
        # by ``sub_ordinal`` (windowed long functions / split markdown sections).
        # A ledger that stored only ``{identity, hash}`` collapses those siblings
        # last-write-wins, silently masking a within-window drift, so the
        # bracket-wildcard field set must carry ``sub_ordinal`` (int) alongside
        # ``identity`` / ``hash`` — the SAME idiom, so the FLEXIBLE outer still
        # tolerates any extra key while this nested path is typed.
        ddl = generate_ddl(dim=NONDEFAULT_DIM)
        sub_ordinal = _field_statement(ddl, SNAPSHOT_ENTRY_TABLE, "chunk_hashes[*].sub_ordinal")
        assert "TYPE int" in sub_ordinal

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


# --- P8a: ``trace`` observability-row field-level fixtures --------------------
#
# The plan pins ``trace`` as lore's OBSERVABILITY row: six core columns capturing
# one served tool invocation (``tool``/``params_hash``/``hit_count``/
# ``latency_ms``/``session``/``ts``) plus the two audited optional accounting
# columns (``token_cost``/``model``) already landed in P2. P8a promotes ``trace``
# from that token_cost/model-ONLY table to the full six-core-field definition.
# The fixtures below are realistic lore-domain values (a real tool name, a real
# SHA-512 params digest, a real fleet session id), never convenience placeholders.
_TRACE_TOOL = "lore_search"
_TRACE_PARAMS_HASH = sha512_hex("query=PurchaseOrder.action_confirm&k=8&tier=custom")
_TRACE_HIT_COUNT = 8
# Deliberately FRACTIONAL: the plan types ``latency_ms`` as ``number`` (not
# ``int``), so a real sub-millisecond-resolution latency must round-trip intact —
# an ``int`` column would silently truncate it.
_TRACE_LATENCY_MS = 42.5
_TRACE_SESSION = "orchestrator-session-7f3a"
_TRACE_TOKEN_COST = 1536
_TRACE_MODEL = "voyage-4-large"


async def _create_trace(
    connection: SurrealConnection,
    *,
    trace_id: str,
    tool: str = _TRACE_TOOL,
    params_hash: str = _TRACE_PARAMS_HASH,
    hit_count: int = _TRACE_HIT_COUNT,
    latency_ms: float = _TRACE_LATENCY_MS,
    session: str = _TRACE_SESSION,
    token_cost: int | None = None,
    model: str | None = None,
) -> None:
    """CREATE a ``trace`` row, omitting any optional field the caller left unset.

    Omitting ``ts`` from the CONTENT entirely (never emitted here) exercises the
    schema's own ``DEFAULT time::now()`` — the server-side timestamp generation the
    plan pins — and omitting ``token_cost``/``model`` when unset exercises the
    ``option`` columns' clean-NONE storage, exactly as an async ``record_trace``
    writer would.

    Uses ``CONTENT $content`` (a single bound object), NOT ``SET session =
    $session``: ``session`` is a SurrealDB PROTECTED variable name, so a top-level
    bound param called ``$session`` is rejected outright (``'session' is a
    protected variable and cannot be set``). As an object KEY inside ``$content``
    it is perfectly legal — the same reason ``record_trace`` builds a CONTENT
    object rather than a SET clause.
    """
    content: dict[str, Any] = {
        "tool": tool,
        "params_hash": params_hash,
        "hit_count": hit_count,
        "latency_ms": latency_ms,
        "session": session,
    }
    if token_cost is not None:
        content["token_cost"] = token_cost
    if model is not None:
        content["model"] = model
    await run(
        connection,
        "CREATE type::record('trace', $id) CONTENT $content",
        {"id": trace_id, "content": content},
    )


class TestTraceTableFieldDefinitions:
    """P8a: ``trace`` carries its six core observability fields plus the two
    audited optional accounting columns — no longer the token_cost/model-ONLY
    placeholder P2 landed (offline, string-level assertions on the generator's
    own output — no server needed).
    """

    def test_trace_core_scalar_fields_are_defined(self) -> None:
        ddl = generate_ddl(dim=NONDEFAULT_DIM)
        assert "TYPE string" in _field_statement(ddl, TRACE_TABLE, "tool")
        assert "TYPE string" in _field_statement(ddl, TRACE_TABLE, "params_hash")
        assert "TYPE int" in _field_statement(ddl, TRACE_TABLE, "hit_count")
        # ``number`` (not ``int``): a fractional latency must survive — see the
        # ``_TRACE_LATENCY_MS`` fixture rationale.
        assert "TYPE number" in _field_statement(ddl, TRACE_TABLE, "latency_ms")
        assert "TYPE string" in _field_statement(ddl, TRACE_TABLE, "session")

    def test_trace_ts_is_a_server_defaulted_datetime(self) -> None:
        # The observability timestamp self-stamps via ``DEFAULT time::now()`` —
        # the SAME idiom ``snapshot.created_at`` / ``command.created_at`` use — so
        # the async writer never has to compute the ingestion instant itself.
        ddl = generate_ddl(dim=NONDEFAULT_DIM)
        ts = _field_statement(ddl, TRACE_TABLE, "ts")
        assert "TYPE datetime" in ts
        assert "DEFAULT" in ts and "time::now()" in ts

    def test_trace_optional_accounting_columns_are_defined(self) -> None:
        # The two audited additive columns (Spectron concept-coverage) stay
        # ``option`` so an async writer may omit them and store NONE cleanly.
        ddl = generate_ddl(dim=NONDEFAULT_DIM)
        assert "option<int>" in _field_statement(ddl, TRACE_TABLE, "token_cost")
        assert "option<string>" in _field_statement(ddl, TRACE_TABLE, "model")


class TestTraceRoundTrip:
    """The ``trace`` table (live behavioural): the six core fields round-trip, the
    ``ts`` DEFAULT auto-stamps, the optional accounting columns store NONE cleanly
    when omitted and round-trip when given, and the table enforces real SCHEMAFULL
    field discipline (an undeclared field is rejected).
    """

    async def test_trace_probe_round_trips_core_fields(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        await _create_trace(connection, trace_id="trace_core")
        row = _one(await run(connection, "SELECT * FROM type::record('trace', 'trace_core')"))
        assert row["tool"] == _TRACE_TOOL
        assert row["params_hash"] == _TRACE_PARAMS_HASH
        assert row["hit_count"] == _TRACE_HIT_COUNT
        # Fractional latency survives the ``number`` column intact (no truncation).
        assert row["latency_ms"] == _TRACE_LATENCY_MS
        assert row["session"] == _TRACE_SESSION

    async def test_trace_ts_is_auto_populated_when_omitted(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        before = datetime.now(UTC)
        await _create_trace(connection, trace_id="trace_ts")  # never sets ts
        after = datetime.now(UTC)
        row = _one(await run(connection, "SELECT * FROM type::record('trace', 'trace_ts')"))
        ts = row["ts"]
        assert isinstance(ts, datetime)
        # Sanity BOUND, not exact equality: the engine's own clock stamped
        # something inside this test's wall-clock window — catches "no DEFAULT at
        # all" (None fails the isinstance check) and "wrong epoch/unit" alike.
        assert before - _CLOCK_SKEW_ALLOWANCE <= _as_utc(ts) <= after + _CLOCK_SKEW_ALLOWANCE

    async def test_trace_optional_columns_absent_when_omitted(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        await _create_trace(connection, trace_id="trace_no_accounting")
        row = _one(
            await run(connection, "SELECT * FROM type::record('trace', 'trace_no_accounting')")
        )
        # An omitted ``option`` column reads back NONE (the SDK decodes it to
        # ``None``, whether absent from the row or explicitly None).
        assert row.get("token_cost") is None
        assert row.get("model") is None

    async def test_trace_optional_columns_round_trip_when_given(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        await _create_trace(
            connection,
            trace_id="trace_accounting",
            token_cost=_TRACE_TOKEN_COST,
            model=_TRACE_MODEL,
        )
        row = _one(
            await run(connection, "SELECT * FROM type::record('trace', 'trace_accounting')")
        )
        assert row["token_cost"] == _TRACE_TOKEN_COST
        assert row["model"] == _TRACE_MODEL

    async def test_trace_rejects_undeclared_field(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        # Proves ``trace`` is a REAL SCHEMAFULL table with declared fields, not a
        # bare placeholder that accepts anything written at it.
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        with pytest.raises(Exception):  # noqa: B017 - engine SCHEMAFULL rejection surface
            await run(
                connection,
                "CREATE type::record('trace', $id) CONTENT $content",
                {
                    "id": "trace_rogue",
                    "content": {
                        "tool": _TRACE_TOOL,
                        "params_hash": _TRACE_PARAMS_HASH,
                        "hit_count": _TRACE_HIT_COUNT,
                        "latency_ms": _TRACE_LATENCY_MS,
                        "session": _TRACE_SESSION,
                        "rogue_field": "not in the schema",
                    },
                },
            )


# --- P8b: ``finding`` ledger field-level + counter fixtures -------------------
#
# The plan (P8b, moved forward from the old P9 placeholder scope) promotes
# ``finding`` from the bare-``SCHEMAFULL`` placeholder that P2 landed to lore's
# FINDING ledger row: a stable human-addressable ``number`` (UNIQUE), the friction
# ``kind``, the four-status review vocabulary, subject/body/area/category, an audit
# ``provenance`` blob, a ``created_at`` self-stamp, and a REAL ``supersedes`` record
# link to the finding it reframes. A sibling ``finding_counter`` table backs the
# race-safe consecutive number mint (``loremaster.findings`` UPSERTs its single row
# inside the same transaction as the finding CREATE). The fixtures below are
# realistic lore-domain values (a real friction subject, a real tool area), never
# convenience placeholders.
_FINDING_STATUS_OPEN = "open"
_FINDING_STATUS_ACKNOWLEDGED = "acknowledged"
_FINDING_STATUS_RESOLVED = "resolved"
_FINDING_STATUS_WONTFIX = "wontfix"
_FINDING_STATUSES = (
    _FINDING_STATUS_OPEN,
    _FINDING_STATUS_ACKNOWLEDGED,
    _FINDING_STATUS_RESOLVED,
    _FINDING_STATUS_WONTFIX,
)
_FINDING_STATUS_INVALID = "reopened"

_FINDING_KIND = "friction"
_FINDING_SUBJECT = "tests_for reports only direct edges, missing indirect coverage"
_FINDING_BODY = (
    "lore_tests_for(symbol) returns direct test nodes but misses tests exercising "
    "the symbol transitively through a helper."
)
_FINDING_AREA = "lore_tests_for"
_FINDING_CATEGORY = "capability_gap"
_FINDING_CREATED_BY = "di-scout-session-4a1c"
_FINDING_PROVENANCE: dict[str, Any] = {
    "created_by": _FINDING_CREATED_BY,
    "created_at": "2026-07-04T00:00:00+00:00",
    "events": [],
}


async def _create_finding(
    connection: SurrealConnection,
    *,
    finding_id: str,
    number: int,
    status: str = _FINDING_STATUS_OPEN,
    kind: str = _FINDING_KIND,
    subject: str = _FINDING_SUBJECT,
    area: str = _FINDING_AREA,
    category: str = _FINDING_CATEGORY,
    created_by: str = _FINDING_CREATED_BY,
    supersedes_id: str | None = None,
    omit_created_at: bool = False,
    omit_status: bool = False,
) -> None:
    """CREATE a ``finding`` row via a CONTENT object literal.

    Omitting ``created_at`` exercises the schema's own ``DEFAULT time::now()``;
    omitting ``status`` exercises its ``DEFAULT 'open'``. ``supersedes`` is written
    as a REAL ``type::record`` link when given, or ``NONE`` when absent. Uses
    ``CONTENT`` (not ``SET``) so a future protected-key column can never break the
    write — the same discipline ``loremaster.findings`` follows. ``area`` /
    ``category`` are overridable so the trim-aware non-empty ASSERT they carry (P8b
    hardening) can be probed with an empty/whitespace value.
    """
    fields = [
        "number: $number",
        "kind: $kind",
        "subject: $subject",
        "body: $body",
        "area: $area",
        "category: $category",
        "created_by: $created_by",
        "provenance: $provenance",
    ]
    params: dict[str, Any] = {
        "id": finding_id,
        "number": number,
        "kind": kind,
        "subject": subject,
        "body": _FINDING_BODY,
        "area": area,
        "category": category,
        "created_by": created_by,
        "provenance": _FINDING_PROVENANCE,
    }
    if not omit_status:
        fields.append("status: $status")
        params["status"] = status
    if not omit_created_at:
        fields.append("created_at: $created_at")
        params["created_at"] = datetime.now(UTC)
    if supersedes_id is not None:
        fields.append("supersedes: type::record('finding', $supersedes_id)")
        params["supersedes_id"] = supersedes_id
    else:
        fields.append("supersedes: NONE")
    await run(
        connection,
        f"CREATE type::record('finding', $id) CONTENT {{ {', '.join(fields)} }}",
        params,
    )


class TestFindingTableFieldDefinitions:
    """P8b: ``finding`` carries its full field set — no longer the bare-``SCHEMAFULL``
    placeholder P2 landed (offline, string-level assertions on the generator's own
    output — no server needed).
    """

    def test_number_is_int_with_a_unique_index(self) -> None:
        ddl = generate_ddl(dim=NONDEFAULT_DIM)
        assert "TYPE int" in _field_statement(ddl, FINDING_TABLE, "number")
        # The stable human-addressable id needs a UNIQUE index (never two #5s).
        matches = _index_statements(ddl, FINDING_TABLE, fields_pattern=r"number\b")
        assert matches, "expected a DEFINE INDEX on finding.number"
        assert any("UNIQUE" in statement for statement in matches)

    def test_kind_is_a_required_non_empty_string(self) -> None:
        ddl = generate_ddl(dim=NONDEFAULT_DIM)
        kind = _field_statement(ddl, FINDING_TABLE, "kind")
        assert "TYPE string" in kind
        # Non-empty SEMANTICALLY: a trim-aware ASSERT, not a bare non-option type.
        assert "ASSERT" in kind

    def test_status_domain_is_constrained_and_defaults_open(self) -> None:
        ddl = generate_ddl(dim=NONDEFAULT_DIM)
        status = _field_statement(ddl, FINDING_TABLE, "status")
        assert "TYPE string" in status
        assert "DEFAULT" in status and f"'{_FINDING_STATUS_OPEN}'" in status
        assert "ASSERT" in status
        for value in _FINDING_STATUSES:
            assert f"'{value}'" in status

    def test_subject_and_created_by_are_required_non_empty(self) -> None:
        ddl = generate_ddl(dim=NONDEFAULT_DIM)
        assert "ASSERT" in _field_statement(ddl, FINDING_TABLE, "subject")
        assert "ASSERT" in _field_statement(ddl, FINDING_TABLE, "created_by")

    def test_body_is_a_plain_string(self) -> None:
        # ``body`` stays a plain, unconstrained string — a finding may legitimately
        # carry an empty body (the subject alone can name the finding).
        ddl = generate_ddl(dim=NONDEFAULT_DIM)
        body = _field_statement(ddl, FINDING_TABLE, "body")
        assert "TYPE string" in body
        assert "ASSERT" not in body

    def test_area_and_category_are_required_non_empty(self) -> None:
        # P8b hardening (audit-findings #2): ``area``/``category`` are the tool /
        # subsystem the finding addresses and its category — an empty one names no
        # real finding, so both carry the SAME trim-aware non-empty ASSERT
        # ``kind``/``subject``/``created_by`` already use, not a bare plain string.
        ddl = generate_ddl(dim=NONDEFAULT_DIM)
        for field in ("area", "category"):
            statement = _field_statement(ddl, FINDING_TABLE, field)
            assert "TYPE string" in statement
            assert "ASSERT" in statement
            assert "string::trim" in statement

    def test_created_at_is_a_server_defaulted_datetime(self) -> None:
        ddl = generate_ddl(dim=NONDEFAULT_DIM)
        created_at = _field_statement(ddl, FINDING_TABLE, "created_at")
        assert "TYPE datetime" in created_at
        assert "DEFAULT" in created_at and "time::now()" in created_at

    def test_supersedes_is_a_real_optional_record_link(self) -> None:
        ddl = generate_ddl(dim=NONDEFAULT_DIM)
        supersedes = _field_statement(ddl, FINDING_TABLE, "supersedes")
        # A REAL optional record link to a sibling finding — never a bare id
        # string (which would silently break dot-traversal / the chain walk).
        assert f"option<record<{FINDING_TABLE}>>" in supersedes

    def test_provenance_is_a_flexible_object(self) -> None:
        ddl = generate_ddl(dim=NONDEFAULT_DIM)
        assert "FLEXIBLE" in _field_statement(ddl, FINDING_TABLE, "provenance")

    def test_finding_counter_table_backs_the_number_mint(self) -> None:
        ddl = generate_ddl(dim=NONDEFAULT_DIM)
        assert f"DEFINE TABLE IF NOT EXISTS {FINDING_COUNTER_TABLE} SCHEMAFULL" in ddl
        next_field = _field_statement(ddl, FINDING_COUNTER_TABLE, "next")
        assert "TYPE int" in next_field
        assert "DEFAULT" in next_field and "0" in next_field


class TestFindingLedgerDdlSlice:
    """``generate_finding_ddl`` is the ledger's own schema SLICE (the analogue of
    ``generate_task_ddl``): the ``finding`` table + fields + indexes AND the
    ``finding_counter`` table, self-contained, applied by ``FindingLedger.ensure_ready``.
    """

    def test_slice_carries_finding_and_counter_tables(self) -> None:
        ddl = generate_finding_ddl()
        assert f"DEFINE TABLE IF NOT EXISTS {FINDING_TABLE} SCHEMAFULL" in ddl
        assert f"DEFINE TABLE IF NOT EXISTS {FINDING_COUNTER_TABLE} SCHEMAFULL" in ddl
        # The load-bearing fields + the UNIQUE number index are all present.
        assert "TYPE int" in _field_statement(ddl, FINDING_TABLE, "number")
        assert f"option<record<{FINDING_TABLE}>>" in _field_statement(ddl, FINDING_TABLE, "supersedes")
        assert any(
            "UNIQUE" in statement
            for statement in _index_statements(ddl, FINDING_TABLE, fields_pattern=r"number\b")
        )

    def test_slice_needs_no_embedding_width_or_analyzer(self) -> None:
        # UNLIKE the memory slice, findings carry no HNSW/FULLTEXT index — the
        # slice is a pure zero-argument function of the table shape.
        ddl = generate_finding_ddl()
        assert "HNSW" not in ddl
        assert "FULLTEXT" not in ddl


class TestFindingRoundTrip:
    """The ``finding`` table (live behavioural): a full row round-trips, the number
    UNIQUE index rejects a duplicate, the status ASSERT rejects an out-of-domain
    value, the non-empty ASSERTs reject empties, the ``supersedes`` link resolves to
    the real parent, the ``created_at``/``status`` DEFAULTs auto-populate, and the
    table enforces real SCHEMAFULL discipline.
    """

    async def test_finding_probe_round_trips(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        await _create_finding(connection, finding_id="f1", number=1)
        row = _one(await run(connection, "SELECT * FROM type::record('finding', 'f1')"))
        assert row["number"] == 1
        assert row["kind"] == _FINDING_KIND
        assert row["status"] == _FINDING_STATUS_OPEN
        assert row["subject"] == _FINDING_SUBJECT
        assert row["area"] == _FINDING_AREA
        assert row["category"] == _FINDING_CATEGORY
        assert row.get("supersedes") is None

    async def test_number_unique_index_rejects_a_duplicate(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        await _create_finding(connection, finding_id="f1", number=7)
        # A SECOND finding claiming the SAME number must be rejected loudly — the
        # UNIQUE index is the backstop the race-safe mint relies on.
        with pytest.raises(Exception):  # noqa: B017 - engine UNIQUE index rejection surface
            await _create_finding(connection, finding_id="f2", number=7)

    async def test_status_assert_rejects_unknown_value(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_finding(
                connection, finding_id="bad", number=1, status=_FINDING_STATUS_INVALID
            )

    @pytest.mark.parametrize("status", _FINDING_STATUSES)
    async def test_finding_accepts_each_valid_status(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        status: str,
    ) -> None:
        # Positive control alongside the negative test: an overly-strict ASSERT
        # (e.g. one accepting only the DEFAULT) would silently pass the negative
        # test while breaking every real transition.
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        await _create_finding(
            connection, finding_id=f"f_{status}", number=1, status=status
        )
        row = _one(await run(connection, f"SELECT * FROM type::record('finding', 'f_{status}')"))
        assert row["status"] == status

    @pytest.mark.parametrize("empty_kind", ["", " ", "\t"])
    async def test_kind_assert_rejects_empty_or_whitespace(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        empty_kind: str,
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_finding(connection, finding_id="empty_kind", number=1, kind=empty_kind)

    async def test_subject_assert_rejects_empty(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_finding(connection, finding_id="empty_subj", number=1, subject="   ")

    @pytest.mark.parametrize("empty_area", ["", " ", "\t"])
    async def test_area_assert_rejects_empty_or_whitespace(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        empty_area: str,
    ) -> None:
        # P8b hardening (audit-findings #2): an empty/whitespace-only area names no
        # real tool surface — the trim-aware ASSERT rejects it as loudly as an empty
        # subject/kind.
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_finding(connection, finding_id="empty_area", number=1, area=empty_area)

    @pytest.mark.parametrize("empty_category", ["", " ", "\t"])
    async def test_category_assert_rejects_empty_or_whitespace(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        empty_category: str,
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_finding(
                connection, finding_id="empty_cat", number=1, category=empty_category
            )

    async def test_supersedes_link_resolves_to_the_real_parent(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        await _create_finding(connection, finding_id="orig", number=1)
        await _create_finding(
            connection, finding_id="succ", number=2, supersedes_id="orig"
        )
        row = _one(await run(connection, "SELECT * FROM type::record('finding', 'succ')"))
        # The link must resolve to the ACTUAL parent row — hop through it and read
        # the parent's OWN data, rather than trusting an opaque id string.
        parent = _one(await run(connection, "SELECT * FROM $ref", {"ref": row["supersedes"]}))
        assert parent["number"] == 1
        assert parent["subject"] == _FINDING_SUBJECT

    async def test_created_at_and_status_defaults_auto_populate(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        before = datetime.now(UTC)
        await _create_finding(
            connection, finding_id="defaults", number=1, omit_created_at=True, omit_status=True
        )
        after = datetime.now(UTC)
        row = _one(await run(connection, "SELECT * FROM type::record('finding', 'defaults')"))
        created_at = row["created_at"]
        assert isinstance(created_at, datetime)
        assert before - _CLOCK_SKEW_ALLOWANCE <= _as_utc(created_at) <= after + _CLOCK_SKEW_ALLOWANCE
        # An omitted status falls back to the schema DEFAULT.
        assert row["status"] == _FINDING_STATUS_OPEN

    async def test_finding_rejects_undeclared_field(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        await run(connection, generate_ddl(dim=env.dim))
        with pytest.raises(Exception):  # noqa: B017 - engine SCHEMAFULL rejection surface
            await run(
                connection,
                "CREATE type::record('finding', $id) CONTENT { number: 1, kind: 'friction', "
                "status: 'open', subject: 's', body: 'b', area: 'a', category: 'c', "
                "created_by: 'x', rogue_field: 'not in the schema' }",
                {"id": "rogue"},
            )


class TestFindingAppliedOverBarePlaceholder:
    """The intended upgrade path: the deployed DB already carries the bare P2
    ``DEFINE TABLE finding SCHEMAFULL`` placeholder (no fields). Applying
    ``generate_ddl`` over that EXISTING empty table must add the full field set via
    ``DEFINE FIELD IF NOT EXISTS`` — never a rebuild, never a rejection.
    """

    async def test_full_field_set_lands_over_the_bare_table(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = admin_db
        # 1. Materialise ONLY the bare placeholder the deployed DB already has.
        await run(connection, f"DEFINE TABLE IF NOT EXISTS {FINDING_TABLE} SCHEMAFULL")
        info_before = await run(connection, f"INFO FOR TABLE {FINDING_TABLE}")
        assert not info_before.get("fields", {}), "precondition: the bare table has no fields yet"

        # 2. Apply the full DDL over the existing table — the DEFINE FIELD IF NOT
        # EXISTS statements upgrade it in place.
        await run(connection, generate_ddl(dim=env.dim))
        info_after = await run(connection, f"INFO FOR TABLE {FINDING_TABLE}")
        defined_fields = set(info_after.get("fields", {}))
        for expected in (
            "number", "kind", "status", "subject", "body", "area",
            "category", "created_by", "created_at", "supersedes", "provenance",
        ):
            assert expected in defined_fields, f"field {expected!r} was not added over the bare table"

        # 3. A full finding row now round-trips through the upgraded table.
        await _create_finding(connection, finding_id="upgraded", number=1)
        row = _one(await run(connection, "SELECT * FROM type::record('finding', 'upgraded')"))
        assert row["number"] == 1
        assert row["status"] == _FINDING_STATUS_OPEN
