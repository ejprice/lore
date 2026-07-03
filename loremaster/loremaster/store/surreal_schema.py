"""Pure, config-driven DDL generator for lore's unified SurrealDB store.

:func:`generate_ddl` emits the full SurrealDB schema for a per-project database:
the ``code_ident`` analyzer, the SCHEMAFULL tables (``chunk`` / ``file`` /
``file_text`` / ``meta`` / ``snapshot`` / ``snapshot_entry`` / ``finding`` /
``trace`` / ``command`` / ``memory``), and the HNSW vector, BM25 FULLTEXT, and
plain composite indexes that back hybrid retrieval. It is a *pure* function of
its arguments — the embedding width is threaded from the configured ``dim`` into
every HNSW index rather than baked in, so one generator serves every project and
every embedder width.

Everything is emitted ``IF NOT EXISTS`` so applying the DDL is idempotent: a
second application against an already-migrated database is a safe no-op, which is
exactly what lets :meth:`SurrealStore.ensure_ready` run it unconditionally at
startup.

Dialect note (verified against the 3.0.5 engine the store targets, and re-verified
on 3.1.5 with no deltas — 3.1.x is the documented floor going forward): the
FULLTEXT index clause is ``FULLTEXT ANALYZER <name> BM25`` (not the older
``SEARCH ANALYZER``), ``FLEXIBLE`` is written *after* ``TYPE`` on a field, and a
domain constraint is a field-level ``ASSERT $value IN [...]``.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Analyzer (the P0-spike-verified code-identifier tokenizer)
# ---------------------------------------------------------------------------

# The analyzer name the store and its FULLTEXT indexes reference. Injected as a
# parameter default so a caller can retarget it without editing this module.
DEFAULT_ANALYZER_NAME = "code_ident"

# Tokenizers that split code identifiers the way the P0 spike verified:
# ``blank`` (whitespace), ``class``/``camel`` (CamelCase + char-class shifts),
# ``punct`` (``.``/``_``/etc.). Filters lower-case and ASCII-fold every token.
_ANALYZER_TOKENIZERS = "blank,class,camel,punct"
_ANALYZER_FILTERS = "lowercase,ascii"

# ---------------------------------------------------------------------------
# HNSW vector-index parameters (distance + storage type are fixed; only the
# DIMENSION is config-driven, threaded from the ``dim`` argument).
# ---------------------------------------------------------------------------
_HNSW_DISTANCE = "COSINE"
_HNSW_STORAGE_TYPE = "F32"

# ---------------------------------------------------------------------------
# Table names (single source of truth — referenced by the store, too)
# ---------------------------------------------------------------------------
CHUNK_TABLE = "chunk"
FILE_TABLE = "file"
FILE_TEXT_TABLE = "file_text"
MEMORY_TABLE = "memory"
META_TABLE = "meta"
SNAPSHOT_TABLE = "snapshot"
SNAPSHOT_ENTRY_TABLE = "snapshot_entry"
FINDING_TABLE = "finding"
TRACE_TABLE = "trace"
COMMAND_TABLE = "command"

# The S13 "Model A" code-graph tables (the astroid-derived code graph, ported
# from KùzuDB). ``code_node`` holds graph nodes (deterministic composite record
# id ``[tier, file_path, qualified_name]``); ``name`` is the name-node indirection
# every reference lands on (carrying a queryable ``value`` for the module-prefix
# reach); ``refers`` / ``answers_to`` are native
# ``TYPE RELATION`` edge tables. Single source of truth shared by
# ``loremaster.graph_surreal`` and its contract tests.
CODE_NODE_TABLE = "code_node"
NAME_TABLE = "name"
REFERS_RELATION = "refers"
ANSWERS_TO_RELATION = "answers_to"

# The plain SCHEMAFULL tables the plan requires to exist but that carry no
# field-level probe yet. ``snapshot``/``snapshot_entry``/``command`` were
# promoted to full field-level definitions in P5-C1b (see
# ``_snapshot_statements`` / ``_snapshot_entry_statements`` /
# ``_command_statements`` below); ``finding`` stays a bare placeholder until
# P9. Neither ``trace`` nor ``meta`` are here either — ``trace`` grows two
# audited optional columns below, ``meta`` grows its ``k``/``v`` fields (P3,
# the ``SurrealManifest`` port).
_STRUCTURAL_TABLES = (FINDING_TABLE,)

# The closed domain a ``file.state`` may take — a file is exactly one of these at
# any time. An out-of-domain state is rejected by the field ASSERT, so the
# manifest can never silently store a bogus lifecycle value.
FILE_STATES = ("indexed", "dirty", "embedding", "failed")

# The searchable text fields that each carry a BM25 FULLTEXT index on ``chunk``.
# Public + the SINGLE source of truth: the store's hybrid BM25 arm imports this
# same tuple to build its ``@@`` predicate, so the fields matched can never
# drift from the fields actually indexed (a ``@@`` against a non-FULLTEXT field
# would be a latent query error).
CHUNK_FULLTEXT_FIELDS = ("ident_text", "source_text", "llm_summary")

# The chunk filter dimensions carried by the plain (non-vector, non-fulltext)
# composite index that scopes scroll/delete/hybrid filtering.
_CHUNK_FILTER_FIELDS = ("tier", "file_path")

# The SurrealDB type of a plain exact-match string column. A legitimate chunk
# FILTER dimension is exactly a plain-``string`` structural column that is not a
# free-text (FULLTEXT) field — see :data:`CHUNK_FILTER_KEYS`.
_CHUNK_STRING_TYPE = "string"

# The ``chunk`` table's fields as ``(name, type_expr)`` pairs — the SINGLE source
# of truth for the DDL (``_chunk_statements`` emits one ``DEFINE FIELD`` per
# entry) AND for the derived column / filter-key sets below. Deriving both from
# one list is what guarantees the store's filter allow-list can never drift from
# the columns the schema actually defines.
_CHUNK_FIELD_SPECS: tuple[tuple[str, str], ...] = (
    ("tier", _CHUNK_STRING_TYPE),
    ("file_path", _CHUNK_STRING_TYPE),
    ("chunk_type", _CHUNK_STRING_TYPE),
    ("identity", _CHUNK_STRING_TYPE),
    ("sub_ordinal", "int"),
    ("content_hash", _CHUNK_STRING_TYPE),
    ("mtime_ns", "int"),
    ("line_start", "int"),
    ("line_end", "int"),
    ("source_text", _CHUNK_STRING_TYPE),
    ("ident_text", _CHUNK_STRING_TYPE),
    ("llm_summary", "option<string>"),
    # FLEXIBLE lets an arbitrary nested metadata blob round-trip intact.
    ("metadata", "object FLEXIBLE"),
    ("embedding", "array<float>"),
)

# The authoritative ``chunk`` column set, DERIVED from the field specs above (not
# a hand-copied twin that could drift from the DDL).
CHUNK_COLUMNS: tuple[str, ...] = tuple(name for name, _type_expr in _CHUNK_FIELD_SPECS)

# The closed allow-list of legitimate exact-match FILTER dimensions: the plain
# ``string`` structural columns that are NOT free-text (FULLTEXT) fields. Derived
# from the field specs (never hand-copied) so adding/removing a string column in
# the schema is reflected automatically. The store validates every agent-supplied
# filter KEY against this set at its trust boundary (SurrealQL-injection defense),
# so a key can never be interpolated into a statement.
CHUNK_FILTER_KEYS: tuple[str, ...] = tuple(
    name
    for name, type_expr in _CHUNK_FIELD_SPECS
    if type_expr == _CHUNK_STRING_TYPE and name not in CHUNK_FULLTEXT_FIELDS
)

# The chunk column the HNSW vector index is built on (the embedding vector).
_CHUNK_VECTOR_FIELD = "embedding"

# Default for the audited ``memory.importance`` column (a by-kind default lands
# in a later phase; a uniform prior for now).
_MEMORY_DEFAULT_IMPORTANCE = 0.8

# The closed status domain a ``command`` row moves through: enqueued
# (``pending``), successfully applied (``done``), or terminally failed
# (``failed``). An out-of-domain status is rejected by the field ASSERT, just
# like :data:`FILE_STATES` guards ``file.state``.
_COMMAND_STATUS_PENDING = "pending"
_COMMAND_STATUS_DONE = "done"
_COMMAND_STATUS_FAILED = "failed"
_COMMAND_STATUSES = (_COMMAND_STATUS_PENDING, _COMMAND_STATUS_DONE, _COMMAND_STATUS_FAILED)

# ---------------------------------------------------------------------------
# Code-graph (S13 Model A) field specs — the single source of truth for
# ``generate_graph_ddl``. Mirrors the ``_CHUNK_FIELD_SPECS`` discipline: one
# ``(name, type_expr)`` list per table drives the ``DEFINE FIELD`` emission.
# ---------------------------------------------------------------------------

# ``code_node`` fields. ``chunk_id`` is ``option<string>`` — the synthesised
# module node has no originating chunk, so it stores ``NONE`` and decodes back to
# ``None``; a symbol node carries its chunk's identity.
_CODE_NODE_FIELD_SPECS: tuple[tuple[str, str], ...] = (
    ("kind", _CHUNK_STRING_TYPE),
    ("qualified_name", _CHUNK_STRING_TYPE),
    ("bare_name", _CHUNK_STRING_TYPE),
    ("file_path", _CHUNK_STRING_TYPE),
    ("tier", _CHUNK_STRING_TYPE),
    ("chunk_id", "option<string>"),
)

# ``refers`` (code_node → name) reference-edge fields. ``src_tier`` /
# ``src_file_path`` are the per-file purge keys a rebuild deletes by.
_REFERS_FIELD_SPECS: tuple[tuple[str, str], ...] = (
    ("kind", _CHUNK_STRING_TYPE),
    ("resolved", "bool"),
    ("src_tier", _CHUNK_STRING_TYPE),
    ("src_file_path", _CHUNK_STRING_TYPE),
)

# ``answers_to`` (code_node → name) FQN/bare fan-out edge fields — also the
# per-file purge keys.
_ANSWERS_TO_FIELD_SPECS: tuple[tuple[str, str], ...] = (
    ("tier", _CHUNK_STRING_TYPE),
    ("file_path", _CHUNK_STRING_TYPE),
)

# ``name`` fields. The name record's id-string component is ALSO carried as a
# queryable ``value`` column: 3.1.5 cannot index (nor ``string::starts_with``) a
# RecordID's string component directly, so the module-prefix reach of
# ``what_imports`` / ``blast_radius`` — find every ``name`` whose value starts with
# ``<module>.`` — needs a plain string field it can prefix-match and index.
_NAME_FIELD_SPECS: tuple[tuple[str, str], ...] = (("value", _CHUNK_STRING_TYPE),)


def _define_table(name: str) -> str:
    """A SCHEMAFULL ``DEFINE TABLE`` statement (idempotent)."""
    return f"DEFINE TABLE IF NOT EXISTS {name} SCHEMAFULL"


def _define_relation_table(name: str) -> str:
    """A SCHEMAFULL native ``TYPE RELATION`` ``DEFINE TABLE`` statement (idempotent).

    A ``TYPE RELATION`` table is a first-class edge table: SurrealDB auto-defines
    its ``in``/``out`` endpoint columns, and native graph traversal
    (``->refers->name`` / ``name<-refers<-code_node``) walks it directly.
    """
    return f"DEFINE TABLE IF NOT EXISTS {name} TYPE RELATION SCHEMAFULL"


def _define_schemaless_table(name: str) -> str:
    """A SCHEMALESS ``DEFINE TABLE`` statement (idempotent).

    The ``name`` table (its sole SCHEMALESS user) is always constructible from
    the name a referencing file wrote (``name:<dst-string>``), UPSERTed
    idempotently; its one defined column, ``value``, is added by
    :func:`_name_statements` (SCHEMALESS still permits a defined field).
    """
    return f"DEFINE TABLE IF NOT EXISTS {name} SCHEMALESS"


def _define_field(table: str, name: str, type_expr: str, *, constraint: str = "") -> str:
    """A ``DEFINE FIELD`` statement for ``table.name`` (idempotent).

    Args:
        table: The owning table.
        name: The field name.
        type_expr: The SurrealDB type expression (e.g. ``string``,
            ``option<datetime>``, ``object FLEXIBLE``, ``array<float>``).
        constraint: An optional trailing clause (e.g. an ``ASSERT`` or
            ``DEFAULT``), appended verbatim after the type.
    """
    suffix = f" {constraint}" if constraint else ""
    return f"DEFINE FIELD IF NOT EXISTS {name} ON {table} TYPE {type_expr}{suffix}"


def _hnsw_index(table: str, field: str, dim: int) -> str:
    """An HNSW vector index on ``table.field`` at the CONFIGURED width ``dim``."""
    return (
        f"DEFINE INDEX IF NOT EXISTS {table}_{field}_hnsw ON {table} "
        f"FIELDS {field} HNSW DIMENSION {dim} DIST {_HNSW_DISTANCE} TYPE {_HNSW_STORAGE_TYPE}"
    )


def _fulltext_index(table: str, field: str, analyzer_name: str) -> str:
    """A BM25 FULLTEXT index on ``table.field`` using ``analyzer_name``."""
    return (
        f"DEFINE INDEX IF NOT EXISTS {table}_{field}_ft ON {table} "
        f"FIELDS {field} FULLTEXT ANALYZER {analyzer_name} BM25"
    )


def _plain_index(table: str, name: str, fields: tuple[str, ...]) -> str:
    """A plain (non-vector, non-fulltext) index over ``fields`` on ``table``."""
    return f"DEFINE INDEX IF NOT EXISTS {name} ON {table} FIELDS {', '.join(fields)}"


def _unique_index(table: str, name: str, fields: tuple[str, ...]) -> str:
    """A UNIQUE index over ``fields`` on ``table`` (idempotent).

    Backs a key-uniqueness constraint the application layer relies on for an
    upsert-by-key pattern (e.g. ``meta.k``) rather than a composite record id.
    """
    return f"DEFINE INDEX IF NOT EXISTS {name} ON {table} FIELDS {', '.join(fields)} UNIQUE"


def _analyzer_statement(analyzer_name: str) -> str:
    """The ``DEFINE ANALYZER`` statement for the code-identifier tokenizer."""
    return (
        f"DEFINE ANALYZER IF NOT EXISTS {analyzer_name} "
        f"TOKENIZERS {_ANALYZER_TOKENIZERS} FILTERS {_ANALYZER_FILTERS}"
    )


def _chunk_statements(dim: int, analyzer_name: str) -> list[str]:
    """The ``chunk`` table: fields + HNSW + BM25 FULLTEXT + composite index.

    The fields are emitted from :data:`_CHUNK_FIELD_SPECS` (the single source of
    truth the derived column / filter-key sets also read), so the DDL and those
    sets can never disagree about which columns exist.
    """
    statements = [_define_table(CHUNK_TABLE)]
    statements += [
        _define_field(CHUNK_TABLE, name, type_expr) for name, type_expr in _CHUNK_FIELD_SPECS
    ]
    statements.append(_hnsw_index(CHUNK_TABLE, _CHUNK_VECTOR_FIELD, dim))
    statements += [
        _fulltext_index(CHUNK_TABLE, field, analyzer_name) for field in CHUNK_FULLTEXT_FIELDS
    ]
    statements.append(_plain_index(CHUNK_TABLE, f"{CHUNK_TABLE}_tier_file", _CHUNK_FILTER_FIELDS))
    return statements


def _file_statements() -> list[str]:
    """The ``file`` manifest table (state constrained to :data:`FILE_STATES`)."""
    allowed = ", ".join(f"'{state}'" for state in FILE_STATES)
    return [
        _define_table(FILE_TABLE),
        _define_field(FILE_TABLE, "sha512", "string"),
        _define_field(FILE_TABLE, "mtime_ns", "int"),
        _define_field(FILE_TABLE, "size", "int"),
        _define_field(FILE_TABLE, "n_chunks", "int"),
        _define_field(FILE_TABLE, "chunk_ids", "array<string>"),
        _define_field(FILE_TABLE, "state", "string", constraint=f"ASSERT $value IN [{allowed}]"),
        _define_field(FILE_TABLE, "updated_at", "datetime"),
    ]


def _meta_statements() -> list[str]:
    """The ``meta`` key/value table (schema-fingerprint / rebuild-status stamps).

    Ported from the SQLite manifest's ``meta(k PRIMARY KEY, v)`` table (P3, the
    ``SurrealManifest`` port). SurrealDB's per-table SCHEMAFULL record id is a
    single opaque value here (unlike ``file``'s composite ``[tier, file_path]``
    id — a meta key isn't naturally the record id's shape), so ``k`` and ``v``
    are ordinary fields and a UNIQUE index on ``k`` is what lets
    ``SurrealManifest.meta_set`` upsert idempotently by key via
    ``UPSERT meta SET k = $k, v = $v WHERE k = $k``.
    """
    return [
        _define_table(META_TABLE),
        _define_field(META_TABLE, "k", "string"),
        _define_field(META_TABLE, "v", "string"),
        _unique_index(META_TABLE, f"{META_TABLE}_k", ("k",)),
    ]


def _file_text_statements() -> list[str]:
    """The ``file_text`` verbatim-body table."""
    return [
        _define_table(FILE_TEXT_TABLE),
        _define_field(FILE_TEXT_TABLE, "text", "string"),
        _define_field(FILE_TEXT_TABLE, "sha512", "string"),
    ]


def _memory_statements(dim: int, analyzer_name: str) -> list[str]:
    """The ``memory`` table: fields + HNSW + FULLTEXT + a ``valid_until`` index."""
    return [
        _define_table(MEMORY_TABLE),
        _define_field(MEMORY_TABLE, "note_text", "string"),
        _define_field(MEMORY_TABLE, "refs", "array<string>"),
        _define_field(MEMORY_TABLE, "kind", "string"),
        _define_field(MEMORY_TABLE, "trust", "float"),
        _define_field(MEMORY_TABLE, "embedding", "array<float>"),
        _define_field(MEMORY_TABLE, "provenance", "object FLEXIBLE"),
        _define_field(MEMORY_TABLE, "created_at", "datetime"),
        # The recall path filters superseded notes on this temporal-validity bound.
        _define_field(MEMORY_TABLE, "valid_until", "option<datetime>"),
        # Audited additive columns (Spectron concept-coverage): a uniform
        # importance prior and a hard expiry, both indexless for now.
        _define_field(
            MEMORY_TABLE, "importance", "float", constraint=f"DEFAULT {_MEMORY_DEFAULT_IMPORTANCE}"
        ),
        _define_field(MEMORY_TABLE, "expires_at", "option<datetime>"),
        _hnsw_index(MEMORY_TABLE, "embedding", dim),
        _fulltext_index(MEMORY_TABLE, "note_text", analyzer_name),
        _plain_index(MEMORY_TABLE, f"{MEMORY_TABLE}_valid_until", ("valid_until",)),
    ]


def _trace_statements() -> list[str]:
    """The ``trace`` table with two audited optional accounting columns."""
    return [
        _define_table(TRACE_TABLE),
        # Audited additive columns (Spectron concept-coverage): per-trace token
        # accounting and the model that produced it, both optional.
        _define_field(TRACE_TABLE, "token_cost", "option<int>"),
        _define_field(TRACE_TABLE, "model", "option<string>"),
    ]


def _snapshot_statements() -> list[str]:
    """The ``snapshot`` table: one row per full-project index generation.

    ``git_ref``/``git_branch`` are ``option<string>`` because a non-git
    (tarball-imported) codebase never has a commit/branch to record;
    ``created_at`` self-stamps via ``DEFAULT time::now()`` so a writer never
    has to compute the timestamp itself.
    """
    return [
        _define_table(SNAPSHOT_TABLE),
        _define_field(SNAPSHOT_TABLE, "created_at", "datetime", constraint="DEFAULT time::now()"),
        _define_field(SNAPSHOT_TABLE, "git_ref", "option<string>"),
        _define_field(SNAPSHOT_TABLE, "git_branch", "option<string>"),
        _define_field(SNAPSHOT_TABLE, "files_total", "int"),
        _define_field(SNAPSHOT_TABLE, "chunks_total", "int"),
    ]


def _snapshot_entry_statements() -> list[str]:
    """The ``snapshot_entry`` table: one row per file captured by a ``snapshot``.

    ``snapshot`` is a real ``record<snapshot>`` link (not a bare id string) so
    a reader can ``FETCH``/dot-traverse straight to the parent row.
    ``chunk_hashes`` is a ``FLEXIBLE`` array of ``{identity, hash}`` objects — a
    per-chunk identity/digest pair a snapshot-diff scan needs to detect a
    changed chunk without re-reading its whole body. Live-verified dialect
    quirk (3.1.5): a bare ``array<object> FLEXIBLE`` outer type still enforces
    strict per-index nested-field paths (``chunk_hashes[1].hash`` etc.) unless
    the two known keys are ALSO given their own bracket-wildcard
    (``chunk_hashes[*].<key>``) field definitions — with those present,
    ``FLEXIBLE`` on the outer field still tolerates any additional,
    undeclared key an object may carry. The plain (non-UNIQUE) index on
    ``snapshot`` backs a purge/diff scan by parent; it must stay non-unique
    since many entries legitimately share one snapshot.
    """
    return [
        _define_table(SNAPSHOT_ENTRY_TABLE),
        _define_field(SNAPSHOT_ENTRY_TABLE, "snapshot", f"record<{SNAPSHOT_TABLE}>"),
        _define_field(SNAPSHOT_ENTRY_TABLE, "tier", "string"),
        _define_field(SNAPSHOT_ENTRY_TABLE, "file_path", "string"),
        _define_field(SNAPSHOT_ENTRY_TABLE, "sha512", "string"),
        _define_field(SNAPSHOT_ENTRY_TABLE, "chunk_hashes", "array<object> FLEXIBLE"),
        _define_field(SNAPSHOT_ENTRY_TABLE, "chunk_hashes[*].identity", "string"),
        _define_field(SNAPSHOT_ENTRY_TABLE, "chunk_hashes[*].hash", "string"),
        _plain_index(SNAPSHOT_ENTRY_TABLE, f"{SNAPSHOT_ENTRY_TABLE}_snapshot", ("snapshot",)),
    ]


def _command_statements() -> list[str]:
    """The ``command`` table: the scout-enqueued work-item queue.

    ``kind`` is a required, non-empty ``string`` — non-empty SEMANTICALLY: the
    trim-aware ``ASSERT`` rejects whitespace-only values (which name no command
    any subscriber could dispatch on) as loudly as the exact empty string,
    while the plain, non-``option`` type rejects an entirely missing one.
    ``payload`` is a ``FLEXIBLE`` object defaulting to ``{}`` so a caller
    may omit it for a payload-less command. ``status`` defaults to
    :data:`_COMMAND_STATUS_PENDING` and is constrained to
    :data:`_COMMAND_STATUSES`, mirroring how :data:`FILE_STATES` guards
    ``file.state``. The index on ``status`` backs the scout's poll-fallback
    query for outstanding work.
    """
    allowed = ", ".join(f"'{status}'" for status in _COMMAND_STATUSES)
    return [
        _define_table(COMMAND_TABLE),
        _define_field(
            COMMAND_TABLE,
            "kind",
            "string",
            constraint="ASSERT string::len(string::trim($value)) > 0",
        ),
        _define_field(COMMAND_TABLE, "payload", "object FLEXIBLE", constraint="DEFAULT {}"),
        _define_field(COMMAND_TABLE, "created_at", "datetime", constraint="DEFAULT time::now()"),
        _define_field(
            COMMAND_TABLE,
            "status",
            "string",
            constraint=f"DEFAULT '{_COMMAND_STATUS_PENDING}' ASSERT $value IN [{allowed}]",
        ),
        _define_field(COMMAND_TABLE, "processed_at", "option<datetime>"),
        _define_field(COMMAND_TABLE, "error", "option<string>"),
        _plain_index(COMMAND_TABLE, f"{COMMAND_TABLE}_status", ("status",)),
    ]


def _code_node_statements() -> list[str]:
    """The ``code_node`` table: fields + the bare/qualified/(tier,file) indexes.

    The hot lookups the query layer leans on: ``bare_name`` and
    ``qualified_name`` symbol resolution, and the composite ``(tier, file_path)``
    scope used by the file count and per-file purge.
    """
    statements: list[str] = [_define_table(CODE_NODE_TABLE)]
    statements += [
        _define_field(CODE_NODE_TABLE, name, type_expr)
        for name, type_expr in _CODE_NODE_FIELD_SPECS
    ]
    statements.append(_plain_index(CODE_NODE_TABLE, f"{CODE_NODE_TABLE}_bare_name", ("bare_name",)))
    statements.append(
        _plain_index(CODE_NODE_TABLE, f"{CODE_NODE_TABLE}_qualified_name", ("qualified_name",))
    )
    statements.append(
        _plain_index(CODE_NODE_TABLE, f"{CODE_NODE_TABLE}_tier_file", ("tier", "file_path"))
    )
    return statements


def _name_statements() -> list[str]:
    """The ``name`` table: the ``value`` string field + a prefix-capable index.

    ``name`` stays SCHEMALESS (a referencing file always constructs the record id
    ``name:<dst-string>`` from what it knows), but it now carries an explicit
    ``value`` column holding that same string. The plain index on ``value``
    mirrors ``code_node``'s ``bare_name`` / ``qualified_name`` indexes and backs
    the ``string::starts_with(value, '<module>.')`` module-prefix reach the Kùzu
    ``what_imports`` / ``_reverse_neighbours`` prefix arm depends on (3.1.5 cannot
    prefix-match a RecordID's id-string component directly).
    """
    statements: list[str] = [_define_schemaless_table(NAME_TABLE)]
    statements += [
        _define_field(NAME_TABLE, name, type_expr) for name, type_expr in _NAME_FIELD_SPECS
    ]
    statements.append(_plain_index(NAME_TABLE, f"{NAME_TABLE}_value", ("value",)))
    return statements


def _refers_statements() -> list[str]:
    """The ``refers`` relation edge table: fields + the ``src_file_path`` purge index."""
    statements: list[str] = [_define_relation_table(REFERS_RELATION)]
    statements += [
        _define_field(REFERS_RELATION, name, type_expr)
        for name, type_expr in _REFERS_FIELD_SPECS
    ]
    statements.append(
        _plain_index(REFERS_RELATION, f"{REFERS_RELATION}_src_file_path", ("src_file_path",))
    )
    return statements


def _answers_to_statements() -> list[str]:
    """The ``answers_to`` relation edge table: fields + the ``(tier, file_path)`` index."""
    statements: list[str] = [_define_relation_table(ANSWERS_TO_RELATION)]
    statements += [
        _define_field(ANSWERS_TO_RELATION, name, type_expr)
        for name, type_expr in _ANSWERS_TO_FIELD_SPECS
    ]
    statements.append(
        _plain_index(ANSWERS_TO_RELATION, f"{ANSWERS_TO_RELATION}_tier_file", ("tier", "file_path"))
    )
    return statements


def generate_ddl(*, dim: int, analyzer_name: str = DEFAULT_ANALYZER_NAME) -> str:
    """Generate the full, idempotent SurrealDB DDL for lore's unified store.

    The DDL threads the configured ``dim`` into every HNSW index (``chunk`` and
    ``memory``) so the schema always matches the embedder width — never a
    hardcoded default. Every statement is ``IF NOT EXISTS``, so applying the
    result twice is a safe no-op.

    Args:
        dim: The embedding width, wired into every HNSW ``DIMENSION`` clause.
        analyzer_name: The code-identifier analyzer name referenced by the BM25
            FULLTEXT indexes; defaults to :data:`DEFAULT_ANALYZER_NAME`.

    Returns:
        A newline-separated, semicolon-terminated DDL string ready to hand to a
        single SurrealDB ``query()`` call.
    """
    statements: list[str] = [_analyzer_statement(analyzer_name)]
    statements += _chunk_statements(dim, analyzer_name)
    statements += _file_statements()
    statements += _file_text_statements()
    statements += _memory_statements(dim, analyzer_name)
    statements += _trace_statements()
    statements += _meta_statements()
    statements += _snapshot_statements()
    statements += _snapshot_entry_statements()
    statements += _command_statements()
    # ``finding`` still has no field-level probe (P9 scope); it stays a bare
    # SCHEMAFULL placeholder.
    statements += [_define_table(table) for table in _STRUCTURAL_TABLES]
    return ";\n".join(statements) + ";\n"


def generate_manifest_ddl() -> str:
    """Generate just the ``file`` + ``meta`` table DDL — the manifest's schema.

    Unlike :func:`generate_ddl`, this slice carries no HNSW/FULLTEXT indexes
    and needs no embedding width or analyzer, since neither ``file`` nor
    ``meta`` carries a vector or free-text column. This lets
    ``SurrealManifest`` — which owns no embedder configuration of its own,
    unlike :class:`~loremaster.store.surreal.SurrealStore` — apply its own
    schema slice independently. Every statement is ``IF NOT EXISTS``, so
    applying the result twice (or applying :func:`generate_ddl` first, in
    either order) is a safe no-op.

    Returns:
        A newline-separated, semicolon-terminated DDL string ready to hand to
        a single SurrealDB ``query()`` call.
    """
    statements: list[str] = _file_statements() + _meta_statements()
    return ";\n".join(statements) + ";\n"


def generate_graph_ddl() -> str:
    """Generate the S13 Model-A code-graph schema slice — idempotent.

    Emits the four tables (:data:`CODE_NODE_TABLE`, :data:`NAME_TABLE`,
    :data:`REFERS_RELATION`, :data:`ANSWERS_TO_RELATION`), their fields, and the
    hot-lookup / per-file-purge indexes. Like :func:`generate_manifest_ddl` this
    is a schema SLICE — it carries no HNSW/FULLTEXT index and needs no embedding
    width, since the code graph stores no vectors. ``refers`` and ``answers_to``
    are native ``TYPE RELATION`` edge tables (so reverse traversal walks them
    directly); ``name`` is SCHEMALESS but carries a queryable ``value`` column
    (plus a prefix-capable index) backing the module-prefix reach. Every
    statement is
    ``IF NOT EXISTS``, so applying it twice (or alongside :func:`generate_ddl`)
    is a safe no-op.

    Returns:
        A newline-separated, semicolon-terminated DDL string ready to hand to a
        single SurrealDB ``query()`` call.
    """
    statements: list[str] = _code_node_statements()
    statements += _name_statements()
    statements += _refers_statements()
    statements += _answers_to_statements()
    return ";\n".join(statements) + ";\n"
