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

# The plain SCHEMAFULL tables the plan requires to exist but that carry no
# field-level probe in the P2 contract. ``trace`` is NOT here — it grows two
# audited optional columns below — the rest are structural placeholders whose
# fields land in a later phase.
_STRUCTURAL_TABLES = (
    META_TABLE,
    SNAPSHOT_TABLE,
    SNAPSHOT_ENTRY_TABLE,
    FINDING_TABLE,
    COMMAND_TABLE,
)

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


def _define_table(name: str) -> str:
    """A SCHEMAFULL ``DEFINE TABLE`` statement (idempotent)."""
    return f"DEFINE TABLE IF NOT EXISTS {name} SCHEMAFULL"


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
    # The remaining plan tables exist structurally; their fields land later.
    statements += [_define_table(table) for table in _STRUCTURAL_TABLES]
    return ";\n".join(statements) + ";\n"
