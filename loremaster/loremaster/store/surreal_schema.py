"""Pure, config-driven DDL generator for lore's unified SurrealDB store.

:func:`generate_ddl` emits the full SurrealDB schema for a per-project database:
the ``code_ident`` analyzer, the SCHEMAFULL tables (``chunk`` / ``file`` /
``file_text`` / ``meta`` / ``snapshot`` / ``snapshot_entry`` / ``finding`` /
``trace`` / ``command`` / ``memory``), and the HNSW vector, BM25 FULLTEXT, and
plain composite indexes that back hybrid retrieval. It is a *pure* function of
its arguments — the embedding width is threaded from the configured ``dim`` into
every HNSW index rather than baked in, so one generator serves every project and
every embedder width.

Every statement is idempotent, so a second application against an already-migrated
database is a safe no-op — which is exactly what lets :meth:`SurrealStore.ensure_ready`
run it unconditionally at startup. Tables, indexes, and the analyzer are ``IF NOT
EXISTS`` (a definition, once created, is never re-applied to an existing one — see
:func:`_hnsw_index` / :func:`_analyzer_statement` for why re-applying THOSE would be
unsafe). Fields are ``DEFINE FIELD OVERWRITE`` (finding #107 — ``IF NOT EXISTS`` on a
field is a no-op against an EXISTING field, so a definition change never migrates a
live store): applying the *same* field definition twice stays a safe no-op, and
applying a *changed* one now actually migrates the store instead of silently
skipping it. See :func:`_define_field`.

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
# The single-row counter table backing the finding ledger's race-safe consecutive
# ``number`` mint: :class:`~loremaster.findings.FindingLedger` UPSERTs its one
# ``singleton`` row (``next += 1``) inside the SAME transaction as the finding
# CREATE, so two concurrent reporters contend on ONE row and the shared
# optimistic-concurrency retry serialises them into gapless consecutive numbers.
FINDING_COUNTER_TABLE = "finding_counter"
# The fixed record id of that single counter row (``finding_counter:singleton``).
FINDING_COUNTER_SINGLETON_ID = "singleton"
TRACE_TABLE = "trace"
COMMAND_TABLE = "command"
TASK_TABLE = "task"
# The task DAG's native ``TYPE RELATION`` edge (``task->blocks->task``), minted by
# packet 04b-1 and ``ENFORCED`` from birth (operator ruling R3). Direction is
# escalation **E-1**'s: ``RELATE $blocker->blocks->$blocked_task``, so ``in`` is the
# BLOCKER and ``out`` is the task that waits. It is a pure MIRROR of
# ``task.blocked_by`` — it carries no edge-local field, because the column holds no
# per-dependency metadata and an edge field would make the edge carry state the column
# cannot (which is what makes the edge ≡ column invariant statable at all).
BLOCKS_RELATION = "blocks"

# The PKT-28 C1 agent-comms tables (the durable, fleet-visible AGENT REGISTRY
# and BRIEF LEDGER — :mod:`loremaster.agents` / :mod:`loremaster.briefs`).
# ``agent`` is a node table (one row per registered agent identity, keyed by a
# deterministic ``uuid5(session, name)`` record id); ``brief`` is a node table
# (one row per published brief VERSION, keyed by a deterministic
# ``uuid5(name, version)`` record id); ``briefed`` is the native ``TYPE
# RELATION`` edge (``agent->briefed->brief``) recording which agent has acked
# which brief version. Single source of truth shared by
# :mod:`loremaster.agents` / :mod:`loremaster.briefs` and their contract tests.
AGENT_TABLE = "agent"
BRIEF_TABLE = "brief"
BRIEFED_RELATION = "briefed"
# The brief ledger's race-safe consecutive VERSION mint's counter table.
# UNLIKE ``finding_counter`` (a single ``singleton`` row — one global
# sequence), this table holds ONE row PER BRIEF NAME (``brief_counter:⟨name⟩``,
# e.g. ``brief_counter:project``): :class:`~loremaster.briefs.BriefLedger`
# UPSERTs the row for the ``name`` being published (``next = (next ?? 0) + 1``),
# so publishers of DIFFERENT names contend on DIFFERENT rows and never
# serialise against each other — strictly better than a singleton, and the
# same counter-row PRIMITIVE :meth:`~loremaster.findings.FindingLedger.report`
# uses, cloned in mechanism, not merely in shape.
BRIEF_COUNTER_TABLE = "brief_counter"

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

# The packet-48 human-identity table (:mod:`loremaster.principals`). ``principal``
# is a node table — one row per person who authenticates (Google OAuth ``sub`` / an
# API-key name, surfaced at runtime as ``AccessToken.client_id`` and stored in
# ``principal.subject``). It is a THIRD, distinct identity vocabulary — NEVER
# conflated with the ledger-actor strings (``finding``/``task`` ``created_by``) or
# the comms ``agent`` registry (see the :mod:`loremaster.principals` docstring and
# the one-column-one-identity-vocabulary law near ``server._TRACE_DECLARED_KEYS``).
# Single source of truth shared by :mod:`loremaster.principals` and its tests.
PRINCIPAL_TABLE = "principal"

# The ``principal_key`` table (packet 49) — one row per per-user API key, owned by
# exactly one :data:`PRINCIPAL_TABLE` via a required ``record<principal>`` link.
# Shared by :mod:`loremaster.principal_keys` and its tests.
#
# Named as a module constant so the store module and ``PrincipalStore.delete``'s
# cascade can import the table name without a literal drifting across modules. The
# field specs / emitters below (introduced as RED stubs by contract-49-1, 2026-08-20)
# are now fully built and folded into :func:`generate_ddl`.
PRINCIPAL_KEY_TABLE = "principal_key"

# The bare-``SCHEMAFULL``-placeholder tables (no field-level probe) the plan
# requires to exist. This tuple is now EMPTY: every table that was ever a
# placeholder has graduated to a real field-level slice —
# ``snapshot``/``snapshot_entry``/``command`` in P5-C1b (see
# ``_snapshot_statements`` / ``_snapshot_entry_statements`` /
# ``_command_statements``), ``trace`` in P8a and packet 03b (its full column set,
# ``_trace_statements``), ``meta`` in P3 (the ``SurrealManifest`` port), and
# ``finding`` in P8b — the FINDING ledger row (``_finding_statements``, its
# ``finding_counter`` sibling, and :mod:`loremaster.findings`), moved forward from
# the old P9 placeholder scope. The tuple is kept (empty) as the extension seam for
# any FUTURE bare-placeholder table the plan may need before it grows fields.
_STRUCTURAL_TABLES: tuple[str, ...] = ()

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

# Default for the audited ``memory.importance`` column — the SCHEMA-level prior a
# row written without an explicit importance falls back to. The P7 backend always
# supplies a by-kind importance (see ``memory.backend.IMPORTANCE_DEFAULTS_BY_KIND``),
# so this uniform prior only ever backs a hand-written / legacy row.
_MEMORY_DEFAULT_IMPORTANCE = 0.8

# --- P7 ``memory`` table wire vocabulary (Spectron-derived, snake_case) -------
#
# Obsolete P2 memory columns the P7 migration DROPS. All three were REQUIRED
# (non-``option``) in P2, and a SCHEMAFULL table coerces a MISSING required field
# to an error (verified live), so a lingering P2 column would make the table
# reject every P7 backend write that omits it. They are therefore removed rather
# than left to drift:
#   * ``trust`` — a P2 *float* (the wrong shape; trust is a two-value enum) now
#     rides INSIDE the ``source`` object.
#   * ``provenance`` — the P2 provenance object, renamed to ``source``.
#   * ``refs`` — the P2 versioned-ref array, folded into the flat ``labels`` list
#     (a ``lore_ref=<key>[@version]`` label) the backend parses back on recall.
# Emitted ``REMOVE FIELD IF EXISTS`` so a fresh test DB (no such fields) is a
# harmless no-op while the live zero-row table migrates cleanly.
_OBSOLETE_MEMORY_FIELDS: tuple[str, ...] = ("refs", "trust", "provenance")

# The ``memory`` table's fields as ``(name, type_expr, constraint)`` triples — the
# single source of truth ``_memory_statements`` emits one ``DEFINE FIELD`` per.
# Every RETAINED P2 column (``note_text``/``kind``/``embedding``/``created_at``/
# ``valid_until``/``importance``/``expires_at``) keeps its EXACT P2 definition
# text, so re-applying it via ``_define_field``'s ``OVERWRITE`` (finding #107) is
# a no-op re-write, never a drift; the rest are genuinely NEW, additive columns.
# Every column whose MEANING changed vs P2 is REMOVED above (never redefined in
# place) — the removal expresses the change explicitly, rather than leaning on
# ``_define_field`` to migrate a stale definition in place.
_MEMORY_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
    ("note_text", _CHUNK_STRING_TYPE, ""),
    ("kind", _CHUNK_STRING_TYPE, ""),
    # All flat labels (including ``lore_ref=`` chunk refs); defaulted so a
    # label-less write may omit it.
    ("labels", "array<string>", "DEFAULT []"),
    # The provenance object (``kind``/``ref``/``trust``) — FLEXIBLE so it
    # round-trips intact, replacing the P2 ``provenance`` column.
    ("source", "object FLEXIBLE", ""),
    ("importance", "float", f"DEFAULT {_MEMORY_DEFAULT_IMPORTANCE}"),
    ("memory_category", "option<string>", ""),
    # When the row became live; defaulted so a hand-written probe row need not
    # compute it. The backend sets it explicitly to the creation instant.
    ("valid_from", "datetime", "DEFAULT time::now()"),
    # When the row stopped being live (superseded/invalidated); the recall path
    # filters on it, and the ``memory_valid_until`` index backs that filter.
    ("valid_until", "option<datetime>", ""),
    ("supersedes", "option<string>", ""),
    ("superseded_by", "option<string>", ""),
    ("expires_at", "option<datetime>", ""),
    ("created_at", "datetime", ""),
    ("embedding", "array<float>", ""),
)

# The memory column the BM25 FULLTEXT index is built on — the SINGLE source of
# truth the backend's hybrid BM25 arm imports so its ``@@`` predicate always
# targets exactly the FULLTEXT-indexed field (mirrors :data:`CHUNK_FULLTEXT_FIELDS`).
MEMORY_FULLTEXT_FIELDS: tuple[str, ...] = ("note_text",)

# The memory columns the HNSW vector index and the temporal-validity index are
# built on.
_MEMORY_VECTOR_FIELD = "embedding"
_MEMORY_VALID_UNTIL_FIELD = "valid_until"

# The closed status domain a ``command`` row moves through: enqueued
# (``pending``), successfully applied (``done``), or terminally failed
# (``failed``). An out-of-domain status is rejected by the field ASSERT, just
# like :data:`FILE_STATES` guards ``file.state``.
_COMMAND_STATUS_PENDING = "pending"
_COMMAND_STATUS_DONE = "done"
_COMMAND_STATUS_FAILED = "failed"
_COMMAND_STATUSES = (_COMMAND_STATUS_PENDING, _COMMAND_STATUS_DONE, _COMMAND_STATUS_FAILED)

# --- P7 ``task`` table (the durable, fleet-visible orchestration ledger) ------
#
# The closed six-status vocabulary a ``task`` row moves through — the exact set
# ``loremaster.tasks`` (the ledger's value objects + state machine) is built
# from. An out-of-domain status is rejected by the field ASSERT, mirroring how
# :data:`_COMMAND_STATUSES` guards ``command.status`` and :data:`FILE_STATES`
# guards ``file.state``. Tasks are NOT searched semantically, so — unlike
# ``memory`` — the table carries no embedding/HNSW/FULLTEXT column, only a plain
# index on ``status`` backing the fleet-visible status filter.
_TASK_STATUS_OPEN = "open"
_TASK_STATUS_CLAIMED = "claimed"
_TASK_STATUS_IN_PROGRESS = "in_progress"
_TASK_STATUS_DONE = "done"
_TASK_STATUS_BLOCKED = "blocked"
_TASK_STATUS_WONTFIX = "wontfix"
_TASK_STATUSES = (
    _TASK_STATUS_OPEN,
    _TASK_STATUS_CLAIMED,
    _TASK_STATUS_IN_PROGRESS,
    _TASK_STATUS_DONE,
    _TASK_STATUS_BLOCKED,
    _TASK_STATUS_WONTFIX,
)

# The ``ASSERT`` domain clause for ``task.status`` — built once from the closed
# vocabulary above so the six statuses are named a single time.
_TASK_STATUS_ALLOWED = ", ".join(f"'{status}'" for status in _TASK_STATUSES)

# The ``task`` table's fields as ``(name, type_expr, constraint)`` triples — the
# single source of truth :func:`_task_statements` emits one ``DEFINE FIELD`` per,
# mirroring :data:`_MEMORY_FIELD_SPECS`. ``owner``/``claimed_at``/``superseded_by``
# are ``option`` (a fresh task is unowned/unclaimed/not-superseded, decoding back
# to ``None``); ``blocked_by`` defaults to ``[]`` so a dependency-free task may
# omit it; ``provenance`` is ``FLEXIBLE`` so the free-form who/when audit blob
# round-trips intact; ``status`` carries the closed-domain ASSERT. PKT-06 §1/§4
# ADDS three ``option`` columns (ADDED fields, never REMOVE+DEFINE — the §5
# two-step table-recreate law is NOT triggered, no HNSW/fingerprint on this
# table): ``updated_at`` (the rollup's leg-1 fleet-activity stamp, stamped
# ``time::now()`` by claim/transition/supersede-of-old, NEVER at create — a
# legacy row decodes it back to ``None``) and ``summary``/``report_path`` (the
# done-transition's completion record — ``summary`` mandatory, ``report_path``
# optional, both enforced ledger-side in :meth:`~loremaster.tasks.TaskLedger.
# _validate_done_summary`, never by a schema ASSERT here, since the cap/single-
# line rules need EXACT teaching error text the ledger owns).
_TASK_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
    ("subject", _CHUNK_STRING_TYPE, ""),
    ("description", _CHUNK_STRING_TYPE, ""),
    ("status", _CHUNK_STRING_TYPE, f"ASSERT $value IN [{_TASK_STATUS_ALLOWED}]"),
    ("owner", "option<string>", ""),
    ("claimed_at", "option<datetime>", ""),
    ("blocked_by", "array<string>", "DEFAULT []"),
    ("provenance", "object FLEXIBLE", ""),
    ("superseded_by", "option<string>", ""),
    ("created_at", "datetime", ""),
    ("updated_at", "option<datetime>", ""),
    ("summary", "option<string>", ""),
    ("report_path", "option<string>", ""),
)

# The ``task`` column the plain status index is built on (the fleet-visible
# ``query_tasks(status=...)`` filter).
_TASK_STATUS_FIELD = "status"

# --- P8b ``finding`` table (lore's durable, fleet-visible FINDING ledger) ------
#
# The closed FOUR-status review vocabulary a ``finding`` row moves through — the
# exact set :mod:`loremaster.findings` (the ledger's value objects + state machine)
# is built from. An out-of-domain status is rejected by the field ASSERT, mirroring
# how :data:`_TASK_STATUSES` guards ``task.status``. Findings are addressed by a
# stable ``number`` and filtered by exact state, never retrieved semantically, so —
# unlike ``memory`` — the table carries no embedding/HNSW/FULLTEXT column.
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

# The ``ASSERT`` domain clause for ``finding.status`` — built once from the closed
# vocabulary above so the four statuses are named a single time (mirrors
# :data:`_TASK_STATUS_ALLOWED`).
_FINDING_STATUS_ALLOWED = ", ".join(f"'{status}'" for status in _FINDING_STATUSES)

# The trim-aware non-empty ASSERT the finding ledger's required free-text columns
# carry — the SAME clause ``command.kind`` uses: it rejects a whitespace-only value
# (which names no real finding) as loudly as the exact empty string, while the
# plain (non-``option``) type rejects an entirely missing one.
_NON_EMPTY_STRING_ASSERT = "ASSERT string::len(string::trim($value)) > 0"

# The ``finding`` table's fields as ``(name, type_expr, constraint)`` triples — the
# single source of truth :func:`_finding_statements` emits one ``DEFINE FIELD`` per,
# mirroring :data:`_TASK_FIELD_SPECS`. ``number`` is a plain ``int`` carrying a
# separate UNIQUE index (the stable, human-addressable id — never two ``#5``s);
# ``kind``/``subject``/``created_by``/``area``/``category`` are required,
# non-empty (the trim-aware ASSERT — an empty area/category names no real tool
# surface, audit-findings #2); ``status`` defaults to ``open`` and carries the
# closed-domain ASSERT; ``body`` is a plain string (a finding may carry an empty
# body — the subject alone can name it); ``created_at`` self-stamps via
# ``DEFAULT time::now()``; ``supersedes`` is a REAL optional record link to the
# finding this one reframes (never a bare id string — so the chain walk can
# dot-traverse it); ``provenance`` is ``FLEXIBLE`` so the who/when audit blob
# round-trips intact.
_FINDING_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
    ("number", "int", ""),
    ("kind", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),
    (
        "status",
        _CHUNK_STRING_TYPE,
        f"DEFAULT '{_FINDING_STATUS_OPEN}' ASSERT $value IN [{_FINDING_STATUS_ALLOWED}]",
    ),
    ("subject", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),
    ("body", _CHUNK_STRING_TYPE, ""),
    ("area", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),
    ("category", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),
    ("created_by", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),
    ("created_at", "datetime", "DEFAULT time::now()"),
    ("supersedes", f"option<record<{FINDING_TABLE}>>", ""),
    ("provenance", "object FLEXIBLE", ""),
)

# The ``finding`` columns the UNIQUE (``number``) and the plain (``status``) indexes
# are built on. The UNIQUE index makes the number a real, collision-free stable id
# AND is the backstop the race-safe mint relies on; the ``status`` index backs the
# fleet-visible ``query(status=...)`` filter (mirrors the ``task`` status index).
_FINDING_NUMBER_FIELD = "number"
_FINDING_STATUS_FIELD = "status"

# The ``principal`` table's closed domains — principal-SPECIFIC vocabularies, NEVER
# the ``agent`` tuples (R3). ``agent`` already carries columns named ``role`` and
# ``status`` with DIFFERENT domains (``agent.role`` a free non-empty string;
# ``agent.status ∈ {active, idle, input_required, retired}``); ``principal``'s are
# NARROWER closed sets. ``status`` gates admission (``active``/``suspended``);
# ``role`` is the AUTHZ domain (``role → AccessToken.scopes``) — ``member`` is
# least-privilege, ``admin`` the explicit elevation. The ``status``/``role`` ASSERTs
# derive from these tuples at CALL TIME in :func:`_principal_statements` (the
# :func:`_floor_measurement_statements` idiom), never frozen into a module constant,
# so a mutation of a tuple moves the emitted ASSERT — the derivation is
# mutation-provable.
_PRINCIPAL_STATUS_ACTIVE = "active"
_PRINCIPAL_STATUS_SUSPENDED = "suspended"
_PRINCIPAL_STATUSES = (_PRINCIPAL_STATUS_ACTIVE, _PRINCIPAL_STATUS_SUSPENDED)

_PRINCIPAL_ROLE_MEMBER = "member"
_PRINCIPAL_ROLE_ADMIN = "admin"
_PRINCIPAL_ROLES = (_PRINCIPAL_ROLE_MEMBER, _PRINCIPAL_ROLE_ADMIN)

# The ``principal`` table's NON-DOMAIN fields as ``(name, type_expr, constraint)``
# triples (the ``finding`` idiom, fine here — these fields carry no closed
# vocabulary to mutate). ``status``/``role`` are NOT here: they are emitted at CALL
# TIME in :func:`_principal_statements` from the tuples above (see the note there).
# ``email`` is the REQUIRED, non-empty human admission key (UNIQUE index). ``subject``
# is ``option<string>`` (Model B — a pre-created-by-email row carries NONE until
# packet 39 fills the OAuth subject on first login) carrying the SAME non-empty
# ASSERT, which an ``option<>`` field SKIPS on NONE but FIRES on a present empty
# string (UNIQUE index). ``display_name``/``expires_at`` are optional presentation/
# lifecycle columns; ``created_at`` self-stamps via ``DEFAULT time::now()`` (the
# store OMITS it on write so the engine stamps it). Field ORDER is DDL-irrelevant.
_PRINCIPAL_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
    ("email", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),
    ("subject", "option<string>", _NON_EMPTY_STRING_ASSERT),
    ("display_name", "option<string>", ""),
    ("expires_at", "option<datetime>", ""),
    ("created_at", "datetime", "DEFAULT time::now()"),
)

# The ``finding_counter`` table's single ``next`` int column, defaulted to 0 so the
# FIRST ``UPSERT ... SET next += 1`` on the newly-created singleton row yields 1.
_FINDING_COUNTER_NEXT_FIELD = "next"

# --- PKT-28 C1 ``agent`` / ``brief`` / ``briefed`` tables (lore's durable,
# fleet-visible AGENT REGISTRY + BRIEF LEDGER) --------------------------------
#
# Binding spec: ``docs/design/2026-07-12-pkt28-c1-semantics.md`` §0. Both the
# ``agent.name``/``agent.session`` charset and the ``brief.name`` charset share
# ONE identifier pattern (a load-bearing injection guard: derived ids get
# inlined as literals into C3's live WHERE clauses) — verified LIVE against
# spike-surreal 3.1.5 (see ``REPORT-c1-contract-schema.md``): the SurrealQL
# ``ASSERT`` must use the FUNCTION form ``string::matches($value, '<pattern>')``;
# the operator form (``$value =~ /pattern/``) is a 3.1.5 PARSE ERROR.
_IDENTIFIER_CHARSET_PATTERN = r"^[a-z0-9][a-z0-9_-]{0,63}$"
_IDENTIFIER_CHARSET_ASSERT = f"ASSERT string::matches($value, '{_IDENTIFIER_CHARSET_PATTERN}')"

# The closed FOUR-status agent lifecycle vocabulary (design doc §0/§3) —
# ``orphaned``/STALE is DERIVED at render time from ``heartbeat_at`` age and is
# deliberately EXCLUDED from this domain: it must never be a legal stored value.
_AGENT_STATUS_ACTIVE = "active"
_AGENT_STATUS_IDLE = "idle"
_AGENT_STATUS_INPUT_REQUIRED = "input_required"
_AGENT_STATUS_RETIRED = "retired"
_AGENT_STATUSES = (
    _AGENT_STATUS_ACTIVE,
    _AGENT_STATUS_IDLE,
    _AGENT_STATUS_INPUT_REQUIRED,
    _AGENT_STATUS_RETIRED,
)
_AGENT_STATUS_ALLOWED = ", ".join(f"'{status}'" for status in _AGENT_STATUSES)

# The ``agent`` table's fields as ``(name, type_expr, constraint)`` triples —
# mirrors :data:`_TASK_FIELD_SPECS`. ``name``/``session`` share the identifier
# charset ASSERT; ``role`` carries the shared non-empty ASSERT
# (:data:`_NON_EMPTY_STRING_ASSERT`); ``status`` carries the closed four-value
# domain; ``model``/``spawned_by``/``task_id``/``last_note`` are ``option``
# (a fresh/partial registration may omit them); ``checkpoint`` is
# ``option<object> FLEXIBLE`` — the C1 build-time probe verified live that
# FLEXIBLE must trail OUTSIDE the angle brackets on 3.1.5 (``option<object
# FLEXIBLE>`` is a parse error); the column ships in C1 with NO action reading
# or writing it yet (checkpoint workflow is C5). ``registered_at``/
# ``heartbeat_at`` are PLAIN (non-option, no DEFAULT) datetimes — the design
# doc's own table gives neither a DEFAULT (unlike ``brief.created_at``), and
# every writer (register / the dispatcher's uniform touch) always stamps both
# explicitly, mirroring ``task.created_at``/``task.claimed_at``'s
# ledger-stamped idiom rather than ``finding.created_at``'s engine-stamped one.
_AGENT_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
    ("name", _CHUNK_STRING_TYPE, _IDENTIFIER_CHARSET_ASSERT),
    ("session", _CHUNK_STRING_TYPE, _IDENTIFIER_CHARSET_ASSERT),
    ("role", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),
    ("model", "option<string>", ""),
    ("status", _CHUNK_STRING_TYPE, f"ASSERT $value IN [{_AGENT_STATUS_ALLOWED}]"),
    ("spawned_by", "option<string>", ""),
    ("task_id", "option<string>", ""),
    ("checkpoint", "option<object>", "FLEXIBLE"),
    ("last_note", "option<string>", ""),
    ("registered_at", "datetime", ""),
    ("heartbeat_at", "datetime", ""),
    # #304 (packet 05a-iii): the status-declaration timestamp. ``option<datetime>``
    # with NO ASSERT — store reference §1.4: a NEW field on the production-POPULATED
    # ``agent`` table must be ``option<>`` (a required/asserted field poisons every
    # existing row's next UPDATE; an option no-assert field cannot). Emitted through
    # ``_define_field`` ⇒ ``DEFINE FIELD OVERWRITE`` (§1.1, the only clause that lands
    # a changed definition; ``IF NOT EXISTS`` is the #107 silent no-op).
    ("status_set_at", "option<datetime>", ""),
    # W1a (packet 06a, #360/#257): the cadence SELF-DECLARATION. An agent's
    # ``register(cadence=...)`` turns its silence into a self-set contract the
    # fleet renders as ``overdue`` (design §B.7). ``option<string>`` with NO
    # ASSERT — store reference §1.4: a NEW field on the production-POPULATED
    # ``agent`` table MUST be ``option<>`` (a required/asserted field poisons
    # every existing row's next UPDATE, and a DEFAULT does not rescue a legacy
    # row); a cadence is free-form agent text validated (if at all) at the app
    # layer, never by a store ASSERT. The ``status_set_at`` (#304) precedent
    # EXACTLY. Emitted through ``_define_field`` ⇒ ``DEFINE FIELD OVERWRITE``
    # (§1.1, the only clause that lands a changed definition).
    ("declared_cadence", "option<string>", ""),
)

# The ``agent`` columns the two indexes are built on: ``(session, status)``
# (the plan's own index — a fleet scoped-by-session status scan) plus a
# STANDALONE index on ``name`` (design doc §0 D7 — the bare-name resolution
# SELECT in §0.3 filters by ``name`` alone; without it every comms call not
# carrying ``session=`` would table-scan). Both non-unique: ``name`` alone is
# NOT unique (the same name may legitimately exist in two different sessions;
# ``(session, name)`` uniqueness is enforced by the deterministic uuid5 id,
# not an index).
_AGENT_SESSION_STATUS_INDEX_FIELDS = ("session", "status")
_AGENT_NAME_INDEX_FIELDS = ("name",)

# The closed THREE-value ``briefed.via`` vocabulary (design doc §0/§5, v7 —
# finding #98): a ``register``-time auto-ack, an ``explicit`` ``brief_ack``
# call, or the publisher's own ``publish``-time self-ack (written by
# ``BriefLedger.publish`` in the SAME transaction as the brief CREATE — §5.1
# step 2, never a render carve-out). First-write-wins on an idempotent re-ack
# (the ledger never overwrites an existing edge's ``via``).
_BRIEFED_VIA_REGISTER = "register"
_BRIEFED_VIA_EXPLICIT = "explicit"
_BRIEFED_VIA_PUBLISH = "publish"
_BRIEFED_VIA_VALUES = (_BRIEFED_VIA_REGISTER, _BRIEFED_VIA_EXPLICIT, _BRIEFED_VIA_PUBLISH)
_BRIEFED_VIA_ALLOWED = ", ".join(f"'{via}'" for via in _BRIEFED_VIA_VALUES)

# The ``brief`` table's fields as ``(name, type_expr, constraint)`` triples.
# ``name`` shares the SAME identifier charset ASSERT as ``agent.name`` (design
# doc §0: "same class as agent.name" — brief names are protocol vocabulary
# ('project', 'base', wave names) rendered and queried by literal, same
# injection posture); ``version`` is a plain ``int``; ``body``/``created_by``
# carry the shared non-empty ASSERT (a blank standing instruction or a blank
# publisher identity names nothing); ``note`` is ``option<string>``;
# ``created_at`` self-stamps via ``DEFAULT time::now()`` (the findings idiom —
# design doc §0, explicit).
_BRIEF_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
    ("name", _CHUNK_STRING_TYPE, _IDENTIFIER_CHARSET_ASSERT),
    ("version", "int", ""),
    ("body", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),
    ("created_by", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),
    ("note", "option<string>", ""),
    ("created_at", "datetime", "DEFAULT time::now()"),
)

# The ``brief`` UNIQUE(name, version) index — the publish backstop (design doc
# §5.1): two racing publishers computing the SAME (name, version) candidate
# (and therefore the SAME deterministic id) can never both land a row.
_BRIEF_NAME_VERSION_INDEX_FIELDS = ("name", "version")

# The ``brief_counter`` table's single ``next`` int column per row, defaulted
# to 0 so the FIRST ``UPSERT ... SET next = (next ?? 0) + 1`` on a brand-new
# per-name row yields 1 — mirrors ``_FINDING_COUNTER_NEXT_FIELD`` exactly; only
# the table's per-NAME keying (see :data:`BRIEF_COUNTER_TABLE`) differs.
_BRIEF_COUNTER_NEXT_FIELD = "next"

# The ``briefed`` edge table's fields as ``(name, type_expr, constraint)``
# triples — ``in``/``out`` are auto-defined by ``TYPE RELATION`` and are NEVER
# hand-declared here (mirrors ``refers``/``answers_to``). ``at`` carries
# ``DEFAULT time::now()`` — a genuinely-instantaneous "this ack/register
# happened now" stamp with no ledger-side reason to compute it itself (the
# design doc is silent on this DEFAULT; resolved by analogy to
# ``brief.created_at`` since a register/ack call always writes this edge in
# the same instant it decides to write it — see ``REPORT-c1-contract-schema.md``
# contract decision 2).
_BRIEFED_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
    ("via", _CHUNK_STRING_TYPE, f"ASSERT $value IN [{_BRIEFED_VIA_ALLOWED}]"),
    ("at", "datetime", "DEFAULT time::now()"),
)

# The ``briefed`` UNIQUE(in, out) index — the idempotent-re-ack backstop
# (design doc §0/§5.4): versions are DISTINCT ``brief`` records, so a single
# UNIQUE pair per (agent, brief-version) is sufficient to make a duplicate
# RELATE of the same pair a no-op rather than a second edge. This is the
# FIRST relation table in the codebase to declare a UNIQUE(in, out) index (no
# ``refers``/``answers_to`` precedent) — legal on SurrealDB ≥3.1.0 (bug #7061
# fixed; independently probed safe, see ``REPORT-probe-7061-c1.md``).
_BRIEFED_IN_OUT_INDEX_FIELDS = ("in", "out")

# --- packet 03 ``message`` node + ``to`` delivery edge + ``message_seq`` --------
#
# The durable comms MESSAGE GRAPH (:mod:`loremaster.messages`, packet 03a — this
# packet lands only the SCHEMA it stands on). ``message`` is a node table (one
# row per sent message, id ``ulid()`` at write time — an ORDERING concern, not a
# DDL one); ``to`` is the native ``TYPE RELATION`` delivery edge
# (``message->to->agent``) carrying per-recipient CAS state. Single source of
# truth shared by :mod:`loremaster.messages` and its contract tests.
MESSAGE_TABLE = "message"
TO_RELATION = "to"

# The native sequence backing ``message.seq``. Store reference §1.1 (SEQUENCE
# row) / §5: ``seq`` is a monotonic ORDERING key minted by
# ``sequence::nextval("message_seq")`` — GAPS ARE REAL (an aborted txn burns a
# number), so it is never a count nor a gapless handle. The DDL is
# ``DEFINE SEQUENCE IF NOT EXISTS`` (never a BARE ``DEFINE SEQUENCE``, which
# RAISES on the re-apply ``ensure_ready()`` performs every boot → a boot-time
# crash, the INDEX failure mode of §1.1) and carries NO ``BATCH``/``START``
# clause — the day either is added, a changed clause never migrates onto an
# existing store (#146, the silent-no-op residual §1.1 records for SEQUENCE; its
# named re-open trigger is exactly that change).
MESSAGE_SEQUENCE_NAME = "message_seq"

# The closed TWO-value ``message.grade`` domain — a message is exactly one of
# these (design ruling 9: ``grade`` is ORTHOGONAL to whether a message is a
# ``question``). An out-of-domain grade is rejected by the field ASSERT, mirroring
# how :data:`_AGENT_STATUSES` guards ``agent.status``.
_MESSAGE_GRADE_SIGNAL = "signal"
_MESSAGE_GRADE_DIRECTIVE = "directive"
_MESSAGE_GRADES = (_MESSAGE_GRADE_SIGNAL, _MESSAGE_GRADE_DIRECTIVE)
_MESSAGE_GRADE_ALLOWED = ", ".join(f"'{grade}'" for grade in _MESSAGE_GRADES)

# The store-enforced ``message.body`` length bound. This is the BACKSTOP, not the
# primary guard: :mod:`loremaster.messages` (packet 03a) owns the app-level
# teaching reject, and imports THIS constant so the two bounds can never drift —
# a body over the bound that bypasses the ledger fails LOUDLY at the store rather
# than landing unbounded (ONE source of truth for the policy value, per the DRY
# law — 03a must import, never re-declare the value).
MESSAGE_BODY_MAX_CHARS = 4000

# The POINTER-class length bound (DD-3.a), applied to EACH ``refs`` entry, to
# ``thread`` and to ``task_id``. ONE constant for one class of field: all three
# are pointers/labels, and three separate constants would be three things to
# drift. Derivation of 256: the longest legitimate house pointer is a receipts
# path plus a section cite (~80-100 chars), so 256 is that with headroom — and it
# refuses content-smuggling outright, because a body-sized "ref" is a BODY wearing
# a pointer's name. Without it the body cap is theatre: five unbounded refs per
# row void the render arithmetic the cap exists to protect.
MESSAGE_POINTER_MAX_CHARS = 256
# The ``refs`` COUNT bound (DD-3.b). The drain render already caps the DISPLAY at
# five with a counted remainder; this bounds STORAGE. 20 admits any real pointer
# batch and refuses a thousand-entry list. Both constants are strikeable; the
# mechanism — bounded pointers, REJECT never truncate — is the ruling.
MESSAGE_REFS_MAX_COUNT = 20

# The ``message`` node table's fields as ``(name, type_expr, constraint)`` triples
# — the single source of truth :func:`_message_statements` emits one ``DEFINE
# FIELD`` per, mirroring :data:`_AGENT_FIELD_SPECS`. ``seq`` is the native-sequence
# ORDERING key; ``sender`` is a real ``record<agent>`` link (a delivery reader can
# dot-traverse ``in.sender.name``); ``grade`` carries the closed two-value domain;
# ``body`` carries the length-bound backstop ASSERT; ``refs`` defaults to ``[]`` so
# a ref-less send may omit it; ``task_id`` is ``option``; ``question`` (design
# ruling 9 — the message ASKS; the waiting state is DERIVED from it, never stored
# on the agent) is a ``bool`` DEFAULTing to ``false`` so an ordinary send that
# omits it is correctly NOT a question, while ``bool`` (never ``option<bool>``)
# keeps the value object's ``question: bool`` non-optional; ``created_at`` is
# ledger-stamped (the ``agent``/``task`` idiom, not the engine-stamped
# ``finding``/``brief`` one) since the derived ``asked_at`` a render ages is
# exactly this column read back. NOTE (verified against the 03a contract): there
# is NO ``asked_at`` COLUMN — ``WaitingOnAnswer.asked_at`` IS the question's own
# ``created_at`` (``test_asked_at_IS_the_questions_own_created_at``), derived at
# read time, not stored.
_MESSAGE_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
    ("seq", "int", ""),
    ("session", _CHUNK_STRING_TYPE, ""),
    # REQUIRED and non-``option`` — a load-bearing dependency, not a default.
    # ``awaiting_answer``'s bounded deliveries read is a semantics-identical
    # SUPERSET only because every message HAS a thread: a stored NONE would be
    # silently dropped by the ``IN`` clause and the asker would read "waiting"
    # forever. Flipping this to ``option<string>`` is a silent semantic change,
    # which is why a schema pin holds it (DD-2.b).
    ("thread", _CHUNK_STRING_TYPE, f"ASSERT string::len($value) <= {MESSAGE_POINTER_MAX_CHARS}"),
    ("sender", f"record<{AGENT_TABLE}>", ""),
    ("grade", _CHUNK_STRING_TYPE, f"ASSERT $value IN [{_MESSAGE_GRADE_ALLOWED}]"),
    ("body", _CHUNK_STRING_TYPE, f"ASSERT string::len($value) <= {MESSAGE_BODY_MAX_CHARS}"),
    (
        "refs",
        "array<string>",
        f"DEFAULT [] ASSERT array::len($value) <= {MESSAGE_REFS_MAX_COUNT}",
    ),
    # ⚠ THE ELEMENT ROW, and it is why the pair exists. ``TYPE array<T>``
    # IMPLICITLY DEFINES ``<field>.*``, so this is ALWAYS a re-definition — the
    # store reference's §1.1 OVERWRITE-for-fields rule applies to it with no
    # exception, and ``_define_field`` supplies exactly that (a bare definition
    # raises "The field 'refs.*' already exists"). The element path is what buys
    # the per-entry ERROR: a rejection names ``refs.*`` and the offending value,
    # where a whole-array closure assert dumps the entire array instead.
    (
        "refs[*]",
        _CHUNK_STRING_TYPE,
        f"ASSERT string::len($value) <= {MESSAGE_POINTER_MAX_CHARS}",
    ),
    # ⚠ BARE asserts on the two pointer labels — NO ``$value = NONE OR`` guard.
    # An ``option<>`` field's ASSERT is NOT evaluated when the value is absent, so
    # the guard is pure cruft that would teach the next author it is required.
    # ``thread`` takes the same bound but NO charset: it is a topic LABEL, not an
    # identity, it is a bound param at every site, and the surface's own taught
    # ``q:<topic>`` form contains a ``:`` the identity charset forbids — applying
    # that charset would reject this packet's own teaching.
    ("task_id", "option<string>", f"ASSERT string::len($value) <= {MESSAGE_POINTER_MAX_CHARS}"),
    ("question", "bool", "DEFAULT false"),
    ("created_at", "datetime", ""),
)

# The ``to`` delivery-edge table's edge-local fields as ``(name, type_expr,
# constraint)`` triples — ``in``/``out`` are auto-defined by ``TYPE RELATION`` and
# are NEVER hand-declared here (mirrors ``briefed``/``refers``/``answers_to``).
# ``seen_at``/``acked_at`` are ``option<datetime>`` so ``WHERE ... IS NONE`` is a
# real write-once CAS guard (design ruling 4 — a non-``option`` column with a
# DEFAULT would make every edge look already-stamped); ``ack_note`` is
# ``option<string>``; ``session``/``created_at`` are the per-delivery scope +
# stamp the fan-out RELATE sets.
_TO_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
    ("session", _CHUNK_STRING_TYPE, ""),
    ("created_at", "datetime", ""),
    ("seen_at", "option<datetime>", ""),
    ("acked_at", "option<datetime>", ""),
    # ``note`` is message-grade PROSE recorded on the edges an ack actually won —
    # not a pointer — so it takes the BODY constant, not the pointer one, at both
    # layers exactly as ``body`` does. Bare assert: NONE is not evaluated.
    ("ack_note", "option<string>", f"ASSERT string::len($value) <= {MESSAGE_BODY_MAX_CHARS}"),
)

# The ``to`` UNIQUE(in, out) index — one delivery edge per (message, recipient)
# pair. Store reference §4: SAFE on our floor (the #7061 cascade hazard is settled
# ABSENT); re-probed on 3.2.1 (packet-03 entry check) — a duplicate pair RAISES a
# LOUD ``InternalError`` (the #349 duplicate-edge fix did NOT make it a silent
# dedupe), so a fan-out that may repeat a recipient MUST dedupe before the RELATE
# loop (03a) — the index is a correctness backstop, not a de-duplicator.
_TO_IN_OUT_INDEX_FIELDS = ("in", "out")
# The drain index: "unread" = a recipient's unstamped ``to`` edges. Without it the
# drain SELECT table-scans every delivery edge in the store on every comms call.
_TO_DRAIN_INDEX_FIELDS = ("out", "seen_at")

# --- ``trace`` table (lore's per-tool-invocation OBSERVABILITY row) -----------
#
# ``trace`` is the row the ONE tracing seam writes on EVERY served tool call
# (packet 03b T1: a ``FastMCP`` subclass overriding ``call_tool``). The field
# NAMES are public constants (not bare literals) so the store's ``record_trace``
# CONTENT keys and this DDL read from ONE source of truth and can never drift —
# the same discipline :data:`CHUNK_COLUMNS` keeps for ``chunk``.
#
# The table carries no HNSW/FULLTEXT index — a trace is an append-only
# observability event, never retrieved semantically — but it DOES carry the
# ``(agent, ordinal)`` plain index packet 06's per-agent decay curve reads
# (T2.1: an index on a POPULATED table BUILDS, blocking, at the first
# ``ensure_ready`` carrying it, and this table is empty exactly once — now).
TRACE_TOOL_FIELD = "tool"
TRACE_PARAMS_HASH_FIELD = "params_hash"
TRACE_HIT_COUNT_FIELD = "hit_count"
TRACE_LATENCY_MS_FIELD = "latency_ms"
TRACE_SESSION_FIELD = "session"
TRACE_TS_FIELD = "ts"
TRACE_TOKEN_COST_FIELD = "token_cost"
TRACE_MODEL_FIELD = "model"
# Packet 03b's enrichment columns (T2). Every one is ``option<>``: the generic
# seam cannot know a value for every tool, and the store reference's §1.4 rule
# for a NEW field on a possibly-populated table is ``option<>`` (a required one
# poisons every existing row and a DEFAULT does not rescue it).
TRACE_AGENT_FIELD = "agent"
TRACE_ACTION_FIELD = "action"
TRACE_TRANSPORT_SESSION_FIELD = "transport_session"
TRACE_ORDINAL_FIELD = "ordinal"
TRACE_OK_FIELD = "ok"

# The native sequence backing :data:`TRACE_ORDINAL_FIELD` (T3). ONE GLOBAL
# sequence, not one per agent: per-agent order is derivable by filtering, while
# the global INTERLEAVING — which a per-agent counter destroys — is exactly what
# "drains against surrounding tool calls" needs. It rides the SHARED
# :func:`_define_sequence` emitter rather than a hand-rolled counter row, which
# would be a THIRD mint policy competing with ``finding_counter``/
# ``brief_counter`` (#102's clone defect). GAPS ARE REAL (an aborted transaction
# burns a number) — the ordinal is an ORDERING key, never a count.
TRACE_SEQUENCE_NAME = "trace_seq"

# The bound on every CALLER-CONTROLLED string on the trace write path (wave 3 /
# blind D4). ``tool`` is the raw dispatched name and the three declared-identity
# columns are raw argument values — all four reach the row verbatim, and the
# write sits in a ``finally``, so an UNKNOWN tool name persists too (the dispatch
# fails INSIDE the funnel, after the row is written). Without a bound, one client
# calling a 100 KB "tool name" writes a full-size row per call, and on a quiet
# instance that name ranks inside the served per-tool aggregate.
#
# ⚠ The POLICY differs from the message pointers deliberately, and the difference
# is the point: a message pointer is REJECTED because only the caller can supply
# the real one. A trace row is telemetry ABOUT a call — refusing it would let a
# caller suppress its own measurement, and losing the row corrupts the denominator
# packet 06 reads. So the writer TRUNCATES to this bound and the row still lands;
# a truncated group key is still a usable group key, an absent row is not. The
# store ASSERT is the backstop for any writer that skips the truncation.
TRACE_IDENTITY_MAX_CHARS = 256

# The packet-06 read index (T2.1): filter ``agent``, order by ``ordinal``.
# PLAIN, never UNIQUE — two rows legitimately share an agent.
TRACE_AGENT_ORDINAL_INDEX_FIELDS = (TRACE_AGENT_FIELD, TRACE_ORDINAL_FIELD)

# The ``trace`` table's fields as ``(name, type_expr, constraint)`` triples — the
# single source of truth :func:`_trace_statements` emits one ``DEFINE FIELD`` per,
# mirroring :data:`_TASK_FIELD_SPECS`. ``latency_ms`` is ``number`` (not ``int``)
# so a sub-millisecond fractional latency survives intact; ``ts`` self-stamps via
# ``DEFAULT time::now()`` — the SAME idiom ``snapshot.created_at`` /
# ``command.created_at`` use — so the writer never computes the ingestion instant
# itself; ``token_cost`` / ``model`` stay ``option`` so a writer may omit them and
# store NONE cleanly.
#
# ``hit_count`` and ``session`` are ``option<>`` (packet 03b T2, WIDENED from
# ``int``/``string``): the all-tools seam cannot know a hit count for an
# arbitrary tool — supplying ``0`` would make ``trace_aggregates`` LIE rather
# than admit an absence — and only a call that DECLARES a fleet session has one.
# ``agent``/``action``/``transport_session`` record what the CALL DECLARED, never
# what the server inferred (MP9): a guessed identity in a measurement instrument
# poisons the curve it exists to produce, invisibly.
#
# ``ok`` semantics, VERBATIM per the ESC-1 ruling because a boolean's meaning is
# not guessable from its name and packet 06 filters on it: True iff the dispatch
# RETURNED a result; False on any raise, cancellation included. The mechanism is
# a SUCCESS LATCH (``ok`` starts False and is latched True only after the
# dispatch returns), never an ``except``-arm flag — a failure-class name-list is
# what ``CancelledError`` walks straight past, and a timed-out drain counted as a
# performed one corrupts the very numerator 06 decides on.
_TRACE_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
    (
        TRACE_TOOL_FIELD,
        _CHUNK_STRING_TYPE,
        f"ASSERT string::len($value) <= {TRACE_IDENTITY_MAX_CHARS}",
    ),
    (TRACE_PARAMS_HASH_FIELD, _CHUNK_STRING_TYPE, ""),
    (TRACE_HIT_COUNT_FIELD, "option<int>", ""),
    (TRACE_LATENCY_MS_FIELD, "number", ""),
    (
        TRACE_SESSION_FIELD,
        "option<string>",
        f"ASSERT string::len($value) <= {TRACE_IDENTITY_MAX_CHARS}",
    ),
    (TRACE_TS_FIELD, "datetime", "DEFAULT time::now()"),
    (TRACE_TOKEN_COST_FIELD, "option<int>", ""),
    (TRACE_MODEL_FIELD, "option<string>", ""),
    (
        TRACE_AGENT_FIELD,
        "option<string>",
        f"ASSERT string::len($value) <= {TRACE_IDENTITY_MAX_CHARS}",
    ),
    (
        TRACE_ACTION_FIELD,
        "option<string>",
        f"ASSERT string::len($value) <= {TRACE_IDENTITY_MAX_CHARS}",
    ),
    (
        TRACE_TRANSPORT_SESSION_FIELD,
        "option<string>",
        f"ASSERT string::len($value) <= {TRACE_IDENTITY_MAX_CHARS}",
    ),
    (TRACE_ORDINAL_FIELD, "option<int>", ""),
    (TRACE_OK_FIELD, "option<bool>", ""),
)

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


def _define_relation_table(
    name: str, in_table: str, out_table: str, *, enforced: bool = False
) -> str:
    """A SCHEMAFULL native ``TYPE RELATION`` ``DEFINE TABLE`` — ``OVERWRITE``, endpoint-typed.

    A ``TYPE RELATION`` table is a first-class edge table: SurrealDB auto-defines
    its ``in``/``out`` endpoint columns, and native graph traversal
    (``->refers->name`` / ``name<-refers<-code_node``) walks it directly.

    ``in_table``/``out_table`` emit the ``IN``/``OUT`` endpoint typing — WITHOUT
    them a relation table accepts an endpoint of ANY table, silently, which store
    reference §4 records as forfeiting the only endpoint validation the engine
    offers. ``enforced=True`` adds the ``ENFORCED`` clause (store reference §4
    "Shape to ship"): it validates that BOTH endpoints reference EXISTING records
    and is the only thing that closes the ``INSERT RELATION`` door no app-level
    check can reach.

    ``OVERWRITE``, NOT ``IF NOT EXISTS`` (store reference §1.1, the RELATION-TABLE
    row): a changed relation clause (``IN``/``OUT``/``ENFORCED``) under
    ``IF NOT EXISTS`` is a MEASURED SILENT NO-OP on an existing edge table — the
    DDL returns OK, the stored definition is untouched, and the guard never reaches
    a live store (#107's shape, invisible to every virgin-DB fixture). ``OVERWRITE``
    is the only clause that lands it, and — unlike ``DEFINE INDEX OVERWRITE`` — it
    does NOT rebuild: it preserves the edge's fields, indexes and rows (§1.5's
    probed ``DEFINE TABLE OVERWRITE`` safety proof). Re-probed on 3.2.1 (packet-03
    entry check): the flip lands ``ENFORCED``+``IN``/``OUT`` on an existing untyped
    edge table.
    """
    enforced_clause = " ENFORCED" if enforced else ""
    return (
        f"DEFINE TABLE OVERWRITE {name} TYPE RELATION "
        f"IN {in_table} OUT {out_table}{enforced_clause} SCHEMAFULL"
    )


def _define_sequence(name: str) -> str:
    """A native ``DEFINE SEQUENCE`` statement (idempotent via ``IF NOT EXISTS``).

    Store reference §1.1 (SEQUENCE row) / §5: ``IF NOT EXISTS``, never a BARE
    ``DEFINE SEQUENCE`` — a bare one RAISES *"the sequence already exists"* on the
    re-apply :meth:`ensure_ready` performs every boot, a boot-time crash (the same
    failure mode flipping INDEX to ``OVERWRITE`` would cause). No ``BATCH``/``START``
    clause is emitted: a changed one never migrates onto an existing store (#146),
    and the default ``BATCH 1000 START 0`` is what ``message.seq`` wants. Verified
    (packet-03 entry check, 3.2.1): re-applying the DDL does NOT reset the counter.
    """
    return f"DEFINE SEQUENCE IF NOT EXISTS {name}"


def _define_schemaless_table(name: str) -> str:
    """A SCHEMALESS ``DEFINE TABLE`` statement (idempotent).

    The ``name`` table (its sole SCHEMALESS user) is always constructible from
    the name a referencing file wrote (``name:<dst-string>``), UPSERTed
    idempotently; its one defined column, ``value``, is added by
    :func:`_name_statements` (SCHEMALESS still permits a defined field).
    """
    return f"DEFINE TABLE IF NOT EXISTS {name} SCHEMALESS"


def _define_field(table: str, name: str, type_expr: str, *, constraint: str = "") -> str:
    """A ``DEFINE FIELD`` statement for ``table.name`` — ``OVERWRITE``, not idempotent-skip.

    Finding #107 (the 100% ``brief_publish`` production outage): ``DEFINE FIELD IF
    NOT EXISTS`` is a NO-OP against an ALREADY-EXISTING field, so a definition
    change (a widened ``ASSERT``, a narrowed one, a type change) never migrates a
    live store — it only ever lands on a fresh one. Every test used a throwaway
    virgin database, so no gate could see this. ``OVERWRITE`` (the vendor's own
    documented mechanism for this — see the module docstring) always re-applies the
    CURRENT definition, so an existing store converges on every ``ensure_ready()``
    call, exactly like a fresh one. Applying the *same* definition twice is still a
    safe no-op (SurrealDB just re-writes an identical definition); what changes is
    that applying a *different* definition twice now actually migrates. A TYPE or
    narrowing change still converges the SCHEMA without rewriting existing DATA —
    an old row that violates the new definition is left intact but write-poisoned
    (any future UPDATE of it is rejected) rather than silently corrupted or
    dropped; see ``REPORT-c1f-contract-migration.md`` §4 for the measured matrix.

    ``_define_index`` / ``_define_table`` / ``_analyzer_statement`` deliberately
    stay ``IF NOT EXISTS`` — do NOT apply this same flip to them.
    ``DEFINE INDEX OVERWRITE`` re-validates/rebuilds a populated HNSW index and
    RAISES on a dimension change (a silent no-op today would become a boot-time
    crash); an analyzer ``OVERWRITE`` lands a new tokenizer/filter definition
    without re-tokenising an already-built FULLTEXT index (a silent recall-quality
    bug, not a migration).

    Args:
        table: The owning table.
        name: The field name.
        type_expr: The SurrealDB type expression (e.g. ``string``,
            ``option<datetime>``, ``object FLEXIBLE``, ``array<float>``).
        constraint: An optional trailing clause (e.g. an ``ASSERT`` or
            ``DEFAULT``), appended verbatim after the type.
    """
    suffix = f" {constraint}" if constraint else ""
    return f"DEFINE FIELD OVERWRITE {name} ON {table} TYPE {type_expr}{suffix}"


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


def _remove_field(table: str, name: str) -> str:
    """A ``REMOVE FIELD IF EXISTS`` statement (idempotent; no-op when absent).

    Used by the P7 ``memory`` migration to DROP the obsolete P2 columns
    (:data:`_OBSOLETE_MEMORY_FIELDS`): a lingering REQUIRED P2 field would make
    the SCHEMAFULL table reject every P7 write that omits it, and ``OVERWRITE``
    cannot express a removal.
    """
    return f"REMOVE FIELD IF EXISTS {name} ON {table}"


def _memory_statements(dim: int, analyzer_name: str) -> list[str]:
    """The ``memory`` table: the P7 wire vocabulary + HNSW + FULLTEXT + a valid_until index.

    Emits, in order: the SCHEMAFULL table; the ``REMOVE FIELD IF EXISTS`` for each
    obsolete P2 column (:data:`_OBSOLETE_MEMORY_FIELDS`); one ``DEFINE FIELD`` per
    :data:`_MEMORY_FIELD_SPECS` entry (retained P2 columns keep their exact P2
    definition text, new columns are additive — see that constant);
    the HNSW vector index at the configured ``dim``; the BM25 FULLTEXT index on
    :data:`MEMORY_FULLTEXT_FIELDS`; and the temporal-validity index the recall
    path's live/superseded filter uses.
    """
    statements: list[str] = [_define_table(MEMORY_TABLE)]
    statements += [_remove_field(MEMORY_TABLE, name) for name in _OBSOLETE_MEMORY_FIELDS]
    statements += [
        _define_field(MEMORY_TABLE, name, type_expr, constraint=constraint)
        for name, type_expr, constraint in _MEMORY_FIELD_SPECS
    ]
    statements.append(_hnsw_index(MEMORY_TABLE, _MEMORY_VECTOR_FIELD, dim))
    statements += [
        _fulltext_index(MEMORY_TABLE, field, analyzer_name) for field in MEMORY_FULLTEXT_FIELDS
    ]
    statements.append(
        _plain_index(MEMORY_TABLE, f"{MEMORY_TABLE}_valid_until", (_MEMORY_VALID_UNTIL_FIELD,))
    )
    return statements


def _trace_statements() -> list[str]:
    """The ``trace`` observability table: its columns, its sequence, its index.

    Emits, in order: the SCHEMAFULL table; one ``DEFINE FIELD`` per
    :data:`_TRACE_FIELD_SPECS` entry (``ts`` carrying the ``DEFAULT time::now()``
    self-stamp, so the writer never computes the ingestion instant itself); the
    ``DEFINE SEQUENCE IF NOT EXISTS trace_seq`` backing the ordinal
    (:func:`_define_sequence` — the SHARED emitter, never a hand-rolled counter
    row); and the plain ``(agent, ordinal)`` index packet 06's per-agent curve
    reads. Mirrors :func:`_task_statements`. UNLIKE ``chunk`` / ``memory`` the
    table carries no HNSW/FULLTEXT index — a trace is an append-only
    observability event, never retrieved semantically.
    """
    statements: list[str] = [_define_table(TRACE_TABLE)]
    statements += [
        _define_field(TRACE_TABLE, name, type_expr, constraint=constraint)
        for name, type_expr, constraint in _TRACE_FIELD_SPECS
    ]
    statements.append(_define_sequence(TRACE_SEQUENCE_NAME))
    statements.append(
        _plain_index(
            TRACE_TABLE, f"{TRACE_TABLE}_agent_ordinal", TRACE_AGENT_ORDINAL_INDEX_FIELDS
        )
    )
    # The ``ts`` index, shipped in the SAME free window and for the same reason
    # one column over: the trace table is empty exactly once — now — and after
    # this deploy it grows on EVERY tool call, so an index added later BUILDS,
    # blocking, at every store's next boot. Unlike the deliberately-withheld
    # ``transport_session`` index, BOTH its consumers are named and designed: the
    # windowed aggregate read below it, and the eventual retention sweep a later
    # packet lands once it has read the curve these rows exist to produce.
    statements.append(_plain_index(TRACE_TABLE, f"{TRACE_TABLE}_ts", (TRACE_TS_FIELD,)))
    return statements


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
    ``chunk_hashes`` is a ``FLEXIBLE`` array of ``{identity, sub_ordinal, hash}``
    objects — the per-chunk identity/digest a snapshot-diff scan needs to detect
    a changed chunk without re-reading its whole body. ``sub_ordinal`` is the
    WITHIN-FILE disambiguator (P8b/F1): lorescribe's natural key is
    ``(identity, sub_ordinal)``, since a windowed long function / split markdown
    section emits several chunks that SHARE one ``identity`` and differ only by
    ``sub_ordinal`` — a ledger storing ``{identity, hash}`` alone collapses those
    siblings last-write-wins and silently masks a within-window drift, so it is a
    first-class nested field here, not left to the FLEXIBLE bag. Live-verified
    dialect quirk (3.1.5): a bare ``array<object> FLEXIBLE`` outer type still
    enforces strict per-index nested-field paths (``chunk_hashes[1].hash`` etc.)
    unless the known keys are ALSO given their own bracket-wildcard
    (``chunk_hashes[*].<key>``) field definitions — with those present,
    ``FLEXIBLE`` on the outer field still tolerates any additional, undeclared
    key an object may carry. Corollary of the non-``option`` ``[*].sub_ordinal``
    typing (live-verified): every NEW ``chunk_hashes`` write must carry
    ``sub_ordinal`` on every element; a pre-F1 (old-schema) row that lacks it
    survives untouched because a ``DEFINE FIELD`` (``OVERWRITE`` since finding
    #107 — see :func:`_define_field`) changes what FUTURE writes must satisfy,
    never a retroactive scan/rewrite of rows already stored — the diff reader
    degrades honestly on those legacy rows. The plain (non-UNIQUE) index on
    ``snapshot`` backs a purge/diff
    scan by parent; it must stay non-unique since many entries legitimately share
    one snapshot.
    """
    return [
        _define_table(SNAPSHOT_ENTRY_TABLE),
        _define_field(SNAPSHOT_ENTRY_TABLE, "snapshot", f"record<{SNAPSHOT_TABLE}>"),
        _define_field(SNAPSHOT_ENTRY_TABLE, "tier", "string"),
        _define_field(SNAPSHOT_ENTRY_TABLE, "file_path", "string"),
        _define_field(SNAPSHOT_ENTRY_TABLE, "sha512", "string"),
        _define_field(SNAPSHOT_ENTRY_TABLE, "chunk_hashes", "array<object> FLEXIBLE"),
        _define_field(SNAPSHOT_ENTRY_TABLE, "chunk_hashes[*].identity", "string"),
        _define_field(SNAPSHOT_ENTRY_TABLE, "chunk_hashes[*].sub_ordinal", "int"),
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


def _task_statements() -> list[str]:
    """The ``task`` table: the six-status wire vocabulary + a plain status index.

    Emits, in order: the SCHEMAFULL table; one ``DEFINE FIELD`` per
    :data:`_TASK_FIELD_SPECS` entry (``status`` carrying the closed-domain
    ASSERT, the ``option`` unowned/unclaimed/not-superseded columns, the
    ``DEFAULT []`` ``blocked_by`` dependency list, and the ``FLEXIBLE``
    ``provenance`` audit blob); and the plain index on ``status`` backing the
    fleet-visible ``query_tasks(status=...)`` filter. UNLIKE ``chunk`` /
    ``memory`` the table carries no HNSW/FULLTEXT index — a task is coordinated
    by exact state, never retrieved semantically.

    Packet 04b-1 appends the :data:`BLOCKS_RELATION` edge table
    (``task->blocks->task``, ``ENFORCED`` from birth — operator ruling R3). THIS
    SLICE IS NOW ORDER-DEPENDENT ON ITSELF, exactly as the brief slice became
    order-dependent on the AGENT slice when 04a flipped ``briefed``: the relation
    clause names ``task`` as BOTH endpoints, so its ``DEFINE TABLE`` must be emitted
    AFTER the ``task`` table's own. It is emitted HERE, and only here, because
    ``generate_ddl()`` composes the task slice but NOT the comms/graph generators —
    so this is the one site feeding both :func:`generate_task_ddl` and
    :func:`generate_ddl`, and declaring the edge anywhere else would leave one path
    defining it and the other auto-creating it ``TYPE ANY`` on first RELATE (§5),
    silently discarding the ``IN``/``OUT`` guard.

    The edge carries NO ``DEFINE FIELD`` and NO index. No edge field: it is a pure
    mirror of ``blocked_by`` (see :data:`BLOCKS_RELATION`). No ``UNIQUE(in, out)``:
    §4 records that the index makes a duplicate a LOUD ERR, and
    :meth:`~loremaster.tasks.TaskLedger.ensure_ready`'s backfill re-runs at EVERY
    boot — it de-duplicates against the store's own edge set instead, which is the
    only reading that also survives edges written by a normal ``create_task``
    between two boots.
    """
    statements: list[str] = [_define_table(TASK_TABLE)]
    statements += [
        _define_field(TASK_TABLE, name, type_expr, constraint=constraint)
        for name, type_expr, constraint in _TASK_FIELD_SPECS
    ]
    statements.append(
        _plain_index(TASK_TABLE, f"{TASK_TABLE}_{_TASK_STATUS_FIELD}", (_TASK_STATUS_FIELD,))
    )
    statements.append(
        _define_relation_table(BLOCKS_RELATION, TASK_TABLE, TASK_TABLE, enforced=True)
    )
    return statements


def _finding_statements() -> list[str]:
    """The ``finding`` table: the field set + a UNIQUE number index + a status index.

    Emits, in order: the SCHEMAFULL table; one ``DEFINE FIELD`` per
    :data:`_FINDING_FIELD_SPECS` entry (``number`` the stable id, the required
    non-empty ``kind``/``subject``/``created_by``, the closed-domain ``status``, the
    ``DEFAULT time::now()`` ``created_at``, the optional ``supersedes`` record link,
    and the ``FLEXIBLE`` ``provenance`` blob); the UNIQUE index on ``number`` (the
    stable, human-addressable id — never two of the same, AND the backstop the
    race-safe mint leans on); and the plain index on ``status`` backing the
    fleet-visible ``query(status=...)`` filter. UNLIKE ``chunk`` / ``memory`` the
    table carries no HNSW/FULLTEXT index — a finding is addressed by number and
    filtered by exact state, never retrieved semantically.
    """
    statements: list[str] = [_define_table(FINDING_TABLE)]
    statements += [
        _define_field(FINDING_TABLE, name, type_expr, constraint=constraint)
        for name, type_expr, constraint in _FINDING_FIELD_SPECS
    ]
    statements.append(
        _unique_index(FINDING_TABLE, f"{FINDING_TABLE}_{_FINDING_NUMBER_FIELD}", (_FINDING_NUMBER_FIELD,))
    )
    statements.append(
        _plain_index(FINDING_TABLE, f"{FINDING_TABLE}_{_FINDING_STATUS_FIELD}", (_FINDING_STATUS_FIELD,))
    )
    return statements


def _finding_counter_statements() -> list[str]:
    """The ``finding_counter`` table: the single ``next`` int column defaulting to 0.

    Backs the finding ledger's race-safe consecutive ``number`` mint. Its ONE
    ``singleton`` row is UPSERTed (``next += 1 RETURN AFTER``) inside the SAME
    transaction as the finding CREATE, so two concurrent reporters contend on this
    ONE row and the shared optimistic-concurrency retry serialises them into gapless
    consecutive numbers (the UNIQUE index on ``finding.number`` is the backstop).
    ``DEFAULT 0`` means the FIRST bump on the freshly-created singleton yields 1.
    """
    return [
        _define_table(FINDING_COUNTER_TABLE),
        _define_field(
            FINDING_COUNTER_TABLE, _FINDING_COUNTER_NEXT_FIELD, "int", constraint="DEFAULT 0"
        ),
    ]


def _principal_statements() -> list[str]:
    """The ``principal`` table: the field set + the two UNIQUE indexes (spec §3/§4).

    Emits, in order: the SCHEMAFULL table; one ``DEFINE FIELD`` per
    :data:`_PRINCIPAL_FIELD_SPECS` entry (the five non-domain fields) followed by
    the ``status`` and ``role`` field-defs; the UNIQUE index on ``email`` (the human
    admission key) and the UNIQUE index on ``subject`` (the runtime OAuth identity).
    The ``subject`` index is a PLAIN UNIQUE over an ``option<string>`` column, which
    admits any number of NONE rows while rejecting a duplicate non-NONE subject —
    exactly the Model-B pre-create semantics (probe-settled on 3.2.4; store
    reference §2/§4). UNLIKE ``finding``/``task`` the table carries no ``status``
    index: a ``principal`` table is bounded by the number of humans, so ``list``
    full-scans for free (a status index is a free ``IF NOT EXISTS`` add later).

    ⚠ The ``status``/``role`` ASSERTs are derived HERE, at CALL time, from
    :data:`_PRINCIPAL_STATUSES` / :data:`_PRINCIPAL_ROLES` — the
    :func:`_floor_measurement_statements` idiom, NOT the frozen import-time
    ``finding`` idiom. A join constant frozen at import cannot move when a mutation
    pin monkeypatches the vocabulary tuple, so the derivation would be un-provable;
    deriving it here makes a tuple change move the emitted ASSERT.
    """
    status_allowed = ", ".join(f"'{status}'" for status in _PRINCIPAL_STATUSES)
    role_allowed = ", ".join(f"'{role}'" for role in _PRINCIPAL_ROLES)
    domain_specs: tuple[tuple[str, str, str], ...] = (
        (
            "status",
            _CHUNK_STRING_TYPE,
            f"DEFAULT '{_PRINCIPAL_STATUS_ACTIVE}' ASSERT $value IN [{status_allowed}]",
        ),
        (
            "role",
            _CHUNK_STRING_TYPE,
            f"DEFAULT '{_PRINCIPAL_ROLE_MEMBER}' ASSERT $value IN [{role_allowed}]",
        ),
    )
    statements: list[str] = [_define_table(PRINCIPAL_TABLE)]
    statements += [
        _define_field(PRINCIPAL_TABLE, name, type_expr, constraint=constraint)
        for name, type_expr, constraint in (*_PRINCIPAL_FIELD_SPECS, *domain_specs)
    ]
    statements.append(_unique_index(PRINCIPAL_TABLE, f"{PRINCIPAL_TABLE}_email", ("email",)))
    statements.append(_unique_index(PRINCIPAL_TABLE, f"{PRINCIPAL_TABLE}_subject", ("subject",)))
    return statements


def _agent_statements() -> list[str]:
    """The ``agent`` table: the field set + the ``(session, status)`` and ``name`` indexes.

    Emits, in order: the SCHEMAFULL table; one ``DEFINE FIELD`` per
    :data:`_AGENT_FIELD_SPECS` entry (the shared identifier charset ASSERT on
    ``name``/``session``, the shared non-empty ASSERT on ``role``, the closed
    four-value ``status`` domain, the ``option`` optional columns, and the
    ``option<object> FLEXIBLE`` ``checkpoint`` blob); the non-unique index on
    ``(session, status)``; and the non-unique index on ``name`` alone (design
    doc §0 D7 — backs the bare-name resolution SELECT). UNLIKE ``chunk`` /
    ``memory`` the table carries no HNSW/FULLTEXT index — an agent is resolved
    by exact identity, never retrieved semantically.
    """
    statements: list[str] = [_define_table(AGENT_TABLE)]
    statements += [
        _define_field(AGENT_TABLE, name, type_expr, constraint=constraint)
        for name, type_expr, constraint in _AGENT_FIELD_SPECS
    ]
    statements.append(
        _plain_index(
            AGENT_TABLE, f"{AGENT_TABLE}_session_status", _AGENT_SESSION_STATUS_INDEX_FIELDS
        )
    )
    statements.append(
        _plain_index(AGENT_TABLE, f"{AGENT_TABLE}_name", _AGENT_NAME_INDEX_FIELDS)
    )
    return statements


def _brief_statements() -> list[str]:
    """The ``brief`` table: the field set + the UNIQUE ``(name, version)`` index.

    Emits, in order: the SCHEMAFULL table; one ``DEFINE FIELD`` per
    :data:`_BRIEF_FIELD_SPECS` entry (the shared identifier charset ASSERT on
    ``name``, the shared non-empty ASSERT on ``body``/``created_by``, the
    ``option<string>`` ``note``, and the ``DEFAULT time::now()``
    ``created_at``); and the UNIQUE index on ``(name, version)`` — the publish
    mint's backstop (design doc §5.1). UNLIKE ``chunk`` / ``memory`` the table
    carries no HNSW/FULLTEXT index — a brief is addressed by (name, version),
    never retrieved semantically.
    """
    statements: list[str] = [_define_table(BRIEF_TABLE)]
    statements += [
        _define_field(BRIEF_TABLE, name, type_expr, constraint=constraint)
        for name, type_expr, constraint in _BRIEF_FIELD_SPECS
    ]
    statements.append(
        _unique_index(BRIEF_TABLE, f"{BRIEF_TABLE}_name_version", _BRIEF_NAME_VERSION_INDEX_FIELDS)
    )
    return statements


def _briefed_statements() -> list[str]:
    """The ``briefed`` relation edge table: fields + the UNIQUE ``(in, out)`` index.

    ``ENFORCED`` since packet 04a (#105): ``DEFINE TABLE OVERWRITE briefed TYPE
    RELATION IN agent OUT brief ENFORCED SCHEMAFULL``. The clause validates that
    BOTH endpoints reference EXISTING records and guards the TABLE — including
    the ``INSERT RELATION`` door an app-level check on one verb can never reach
    (store reference §4). It is the STRUCTURAL half only: the engine reports ONE
    bad endpoint, as untyped prose, after the write is attempted, and the seam's
    error hygiene withholds even that — so
    :func:`loremaster.agent_existence.reject_unknown_agents` stays the layer that
    TEACHES. Neither is redundant; do not delete one for the other.
    ⚠ This clause lands on an EXISTING table in every long-lived store, which is
    why :func:`_define_relation_table` emits ``OVERWRITE``: ``IF NOT EXISTS``
    would be a MEASURED silent no-op and the guard would never reach production
    (#107's shape, invisible to every virgin-DB fixture).
    ⚠ Consequence: this slice is now ORDER-DEPENDENT on
    :func:`generate_agent_ddl` — an ``IN agent`` edge needs the ``agent`` table
    to exist. Every consumer already applies the agent slice first
    (``server.py``: ``agent_registry`` -> ``brief_ledger`` -> ``message_ledger``),
    exactly as ``_message_statements`` records for ``to``.

    Mirrors ``_refers_statements``/``_answers_to_statements``'s shape: define
    the relation table (:func:`_define_relation_table` — ``in``/``out`` are
    auto-defined, never hand-declared), emit the edge-local metadata fields
    from :data:`_BRIEFED_FIELD_SPECS` (``via`` closed-THREE-value ASSERT —
    ``register``/``explicit``/``publish``, finding #98 — ``at``
    ``DEFAULT time::now()``), then the UNIQUE index on ``(in, out)`` — the
    idempotent-re-ack backstop (design doc §0/§5.4). UNLIKE ``refers``/
    ``answers_to`` this is the first relation table to declare a UNIQUE
    endpoint-pair index (no precedent to clone verbatim; see the module's own
    field-spec comment for the live-probed safety confirmation).
    """
    statements: list[str] = [
        _define_relation_table(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, enforced=True)
    ]
    statements += [
        _define_field(BRIEFED_RELATION, name, type_expr, constraint=constraint)
        for name, type_expr, constraint in _BRIEFED_FIELD_SPECS
    ]
    statements.append(
        _unique_index(BRIEFED_RELATION, f"{BRIEFED_RELATION}_in_out", _BRIEFED_IN_OUT_INDEX_FIELDS)
    )
    return statements


def _brief_counter_statements() -> list[str]:
    """The ``brief_counter`` table: one ``next`` int column PER BRIEF NAME, defaulting to 0.

    Backs the brief ledger's race-safe consecutive VERSION mint (design doc
    §5.1, ``BriefLedger._mint_version``). UNLIKE ``finding_counter``'s single
    ``singleton`` row (one global sequence), this table holds ONE row PER
    brief NAME (``brief_counter:⟨name⟩``), so publishers of DIFFERENT names
    UPSERT DIFFERENT rows and never contend with each other — publishers of
    the SAME name contend on the same row and the engine serialises them into
    gapless consecutive numbers (the ``brief`` table's UNIQUE(name, version)
    index is the backstop, never the mechanism). ``DEFAULT 0`` means the
    FIRST bump on a brand-new per-name row yields 1, matching the mint's own
    ``next ?? 0`` coalesce — declaring the table changes nothing observable
    (previously auto-created SCHEMALESS by the engine on first write; see
    ``REPORT-c1-builder-mint.md`` §2.2), it only makes the table's existence
    explicit alongside its ``brief``/``briefed`` siblings.
    """
    return [
        _define_table(BRIEF_COUNTER_TABLE),
        _define_field(
            BRIEF_COUNTER_TABLE, _BRIEF_COUNTER_NEXT_FIELD, "int", constraint="DEFAULT 0"
        ),
    ]


def _message_statements() -> list[str]:
    """The ``message`` node + the ``message_seq`` sequence + the ``to`` delivery edge.

    Emits, in order: the SCHEMAFULL ``message`` node table and one ``DEFINE FIELD``
    per :data:`_MESSAGE_FIELD_SPECS` entry (the closed ``grade`` domain, the
    length-bound ``body`` backstop, the ``record<agent>`` ``sender``, the
    ruling-9 ``question`` bool); the native ``DEFINE SEQUENCE`` backing
    ``message.seq`` (:func:`_define_sequence`); the two R3(1) hot-path indexes
    over ``(seq)`` and ``(sender, question)``; then the ``to`` relation edge —
    ``DEFINE TABLE OVERWRITE to TYPE RELATION IN message OUT agent ENFORCED
    SCHEMAFULL`` (:func:`_define_relation_table` with ``enforced=True``; ``in``/
    ``out`` auto-defined, never hand-declared) — its edge-local CAS fields
    (:data:`_TO_FIELD_SPECS`), the UNIQUE(in, out) index (one edge per
    message-recipient pair), and the plain (out, seen_at) drain index.

    The ``message`` NODE table stays ``IF NOT EXISTS`` (its clauses never change);
    the ``to`` RELATION table is ``OVERWRITE`` (a changed IN/OUT/ENFORCED clause is
    a silent no-op under IF NOT EXISTS — store reference §1.1). Applied AFTER
    :func:`generate_agent_ddl` in every consumer, so ``agent`` exists for the edge's
    ``OUT agent``/``sender``'s ``record<agent>``. UNLIKE ``chunk``/``memory`` the
    slice carries no HNSW/FULLTEXT index — a message is coordinated by sequence and
    delivery edge, never retrieved semantically.
    """
    statements: list[str] = [_define_table(MESSAGE_TABLE)]
    statements += [
        _define_field(MESSAGE_TABLE, name, type_expr, constraint=constraint)
        for name, type_expr, constraint in _MESSAGE_FIELD_SPECS
    ]
    statements.append(_define_sequence(MESSAGE_SEQUENCE_NAME))
    # The two R3(1) hot-path indexes, shipped INSIDE the free window (03a-2 delta
    # row 1): production carries ZERO ``message`` rows until packet 03b deploys,
    # so these builds are free exactly once and the window closes at that deploy.
    # ``IF NOT EXISTS`` per store reference §1.1's INDEX row (an INDEX OVERWRITE
    # re-builds over every row and can hard-fail ``ensure_ready`` at boot).
    #   · (seq) serves ``ack``'s ``WHERE seq IN $seqs`` resolution. PLAIN, not
    #     UNIQUE — a deliberate, strikeable divergence from the approved design
    #     (a UNIQUE index would REJECT a second row per seq rather than merely
    #     failing to speed a read); re-open trigger: the day anything depends on
    #     seq being unique rather than merely monotonic.
    #   · (sender, question) serves ``awaiting_answer``'s questions read. The
    #     ORDER is load-bearing: ``sender`` is the selective prefix, while
    #     ``question`` is a boolean that halves the table at best.
    statements.append(_plain_index(MESSAGE_TABLE, f"{MESSAGE_TABLE}_seq", ("seq",)))
    statements.append(
        _plain_index(
            MESSAGE_TABLE, f"{MESSAGE_TABLE}_sender_question", ("sender", "question")
        )
    )
    statements.append(
        _define_relation_table(TO_RELATION, MESSAGE_TABLE, AGENT_TABLE, enforced=True)
    )
    statements += [
        _define_field(TO_RELATION, name, type_expr, constraint=constraint)
        for name, type_expr, constraint in _TO_FIELD_SPECS
    ]
    statements.append(
        _unique_index(TO_RELATION, f"{TO_RELATION}_in_out", _TO_IN_OUT_INDEX_FIELDS)
    )
    statements.append(
        _plain_index(TO_RELATION, f"{TO_RELATION}_out_seen_at", _TO_DRAIN_INDEX_FIELDS)
    )
    return statements


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
    statements: list[str] = [
        _define_relation_table(REFERS_RELATION, CODE_NODE_TABLE, NAME_TABLE)
    ]
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
    statements: list[str] = [
        _define_relation_table(ANSWERS_TO_RELATION, CODE_NODE_TABLE, NAME_TABLE)
    ]
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
    hardcoded default. Every statement is idempotent (``IF NOT EXISTS`` for tables/
    indexes/the analyzer, ``OVERWRITE`` for fields — see :func:`_define_field`), so
    applying the result twice is a safe no-op.

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
    statements += _task_statements()
    statements += _finding_statements()
    statements += _finding_counter_statements()
    statements += _principal_statements()
    statements += _principal_key_statements()
    # packet 60 — the Keep substrate. ``keep`` AFTER ``principal`` (its ``keeper``
    # record<principal> link target), and ``member_of`` AFTER both ``principal`` and
    # ``keep`` (its ENFORCED ``IN principal OUT keep`` endpoints must both exist first
    # — the ``briefed`` → ``agent`` fold-order precedent).
    statements += _keep_statements()
    statements += _member_of_statements()
    # Any residual bare-``SCHEMAFULL`` placeholder tables (currently none — every
    # table has graduated to a field-level slice; see :data:`_STRUCTURAL_TABLES`).
    statements += [_define_table(table) for table in _STRUCTURAL_TABLES]
    return ";\n".join(statements) + ";\n"


def generate_manifest_ddl() -> str:
    """Generate just the ``file`` + ``meta`` table DDL — the manifest's schema.

    Unlike :func:`generate_ddl`, this slice carries no HNSW/FULLTEXT indexes
    and needs no embedding width or analyzer, since neither ``file`` nor
    ``meta`` carries a vector or free-text column. This lets
    ``SurrealManifest`` — which owns no embedder configuration of its own,
    unlike :class:`~loremaster.store.surreal.SurrealStore` — apply its own
    schema slice independently. Every statement is idempotent (``IF NOT EXISTS``
    for the table, ``OVERWRITE`` for its fields — see :func:`_define_field`), so
    applying the result twice (or applying :func:`generate_ddl` first, in
    either order) is a safe no-op.

    Returns:
        A newline-separated, semicolon-terminated DDL string ready to hand to
        a single SurrealDB ``query()`` call.
    """
    statements: list[str] = _file_statements() + _meta_statements()
    return ";\n".join(statements) + ";\n"


def generate_memory_ddl(*, dim: int, analyzer_name: str = DEFAULT_ANALYZER_NAME) -> str:
    """Generate just the ``memory`` table DDL — the P7 memory backend's schema slice.

    Mirrors :func:`generate_manifest_ddl` / :func:`generate_graph_ddl`: a schema
    SLICE the :class:`~loremaster.memory.local.LocalMemoryBackend` applies on its
    OWN connection at :meth:`ensure_ready`, independent of the full
    :func:`generate_ddl`. UNLIKE the manifest / graph slices it DOES need the
    embedding ``dim`` and the analyzer, because the ``memory`` table carries an
    HNSW vector index and a BM25 FULLTEXT index. The ``code_ident`` analyzer the
    FULLTEXT index references is emitted here too, so the slice is self-contained
    on a fresh per-project database. Every statement is idempotent (``IF NOT
    EXISTS`` for the table, ``OVERWRITE`` for retained/new fields, ``REMOVE FIELD
    IF EXISTS`` for the obsolete ones — see :func:`_define_field`), so applying it
    twice — or alongside :func:`generate_ddl`, in either order — is a safe no-op.

    Args:
        dim: The embedding width, wired into the ``memory`` HNSW ``DIMENSION`` clause.
        analyzer_name: The code-identifier analyzer name the FULLTEXT index
            references; defaults to :data:`DEFAULT_ANALYZER_NAME`.

    Returns:
        A newline-separated, semicolon-terminated DDL string ready to hand to a
        single SurrealDB ``query()`` call (or wrap in one ``BEGIN … COMMIT``).
    """
    statements: list[str] = [_analyzer_statement(analyzer_name)]
    statements += _memory_statements(dim, analyzer_name)
    return ";\n".join(statements) + ";\n"


def generate_task_ddl() -> str:
    """Generate just the ``task`` table DDL — the P7 task ledger's schema slice.

    Mirrors :func:`generate_manifest_ddl` / :func:`generate_graph_ddl`: a schema
    SLICE the :class:`~loremaster.tasks.TaskLedger` applies on its OWN
    connection at :meth:`ensure_ready`, independent of the full
    :func:`generate_ddl`. UNLIKE the ``memory`` slice it needs NEITHER the
    embedding ``dim`` NOR the analyzer, because the ``task`` table carries no
    HNSW vector or BM25 FULLTEXT index (tasks are coordinated by exact state,
    never retrieved semantically). Every statement is idempotent (``IF NOT
    EXISTS`` for the table, ``OVERWRITE`` for its fields — see
    :func:`_define_field`), so applying it twice — or alongside
    :func:`generate_ddl`, in either order — is a safe no-op.

    Returns:
        A newline-separated, semicolon-terminated DDL string ready to hand to a
        single SurrealDB ``query()`` call (or wrap in one ``BEGIN … COMMIT``).
    """
    statements: list[str] = _task_statements()
    return ";\n".join(statements) + ";\n"


def generate_finding_ddl() -> str:
    """Generate just the ``finding`` + ``finding_counter`` DDL — the P8b finding
    ledger's schema slice.

    Mirrors :func:`generate_task_ddl`: a schema SLICE the
    :class:`~loremaster.findings.FindingLedger` applies on its OWN connection at
    :meth:`ensure_ready`, independent of the full :func:`generate_ddl`. Like the
    task slice it needs NEITHER the embedding ``dim`` NOR the analyzer, because the
    ``finding`` table carries no HNSW vector or BM25 FULLTEXT index (findings are
    addressed by number and filtered by exact state, never retrieved semantically).
    Includes the ``finding_counter`` sibling table that backs the race-safe number
    mint. Every statement is idempotent (``IF NOT EXISTS`` for the tables,
    ``OVERWRITE`` for fields — see :func:`_define_field`), so applying it twice —
    or alongside :func:`generate_ddl`, in either order — is a safe no-op.

    Returns:
        A newline-separated, semicolon-terminated DDL string ready to hand to a
        single SurrealDB ``query()`` call (or wrap in one ``BEGIN … COMMIT``).
    """
    statements: list[str] = _finding_statements() + _finding_counter_statements()
    return ";\n".join(statements) + ";\n"


def generate_principal_ddl() -> str:
    """Generate just the ``principal`` table DDL — packet 48's human-identity slice.

    Mirrors :func:`generate_finding_ddl`: a schema SLICE
    :class:`~loremaster.principals.PrincipalStore` applies on its OWN connection at
    :meth:`ensure_ready`, independent of the full :func:`generate_ddl` (into which
    ``principal`` is ALSO folded — Variant A — so the primary
    ``write_store.ensure_ready()`` creates the table the moment packet 48 ships,
    without wiring a ``PrincipalStore`` into ``build_app_context``). Needs NEITHER
    the embedding ``dim`` NOR the analyzer — a principal is addressed by ``email``
    and ``subject``, never retrieved semantically. Every statement is idempotent
    (``IF NOT EXISTS`` for the table/indexes, ``OVERWRITE`` for its fields — see
    :func:`_define_field`), so applying it twice — or alongside :func:`generate_ddl`,
    in either order — is a safe no-op.

    Returns:
        A newline-separated, semicolon-terminated DDL string ready to hand to a
        single SurrealDB ``query()`` call (or wrap in one ``BEGIN … COMMIT``).
    """
    return ";\n".join(_principal_statements()) + ";\n"


# --------------------------------------------------------------------------- #
# ``principal_key`` (packet 49) — per-user API keys owned by a ``principal``.
#
# Introduced as RED STUBS by contract-49-1 (2026-08-20) — emitting NOTHING so every
# packet-49 schema pin failed BEHAVIOURALLY (never an ImportError) — and GREENED by the
# wave builder per the packet-49 design §F7. The slice now built:
#   * ``_PRINCIPAL_KEY_FIELD_SPECS`` — hash / name / created_at / expires_at /
#     revoked_at (with ``principal: record<principal>`` and both UNIQUE indexes
#     emitted in ``_principal_key_statements``), routed through the shared
#     ``_define_table`` / ``_define_field`` / ``_unique_index`` emitters;
#   * ``_principal_key_statements`` folded into ``generate_ddl`` immediately AFTER
#     ``_principal_statements()`` (so the PRIMARY store gains the table on ship —
#     the #131 dirty-store class the fold pin guards);
#   * ``generate_principal_key_ddl`` exposed for ``PrincipalKeyStore.ensure_ready``.
# --------------------------------------------------------------------------- #

# The ``principal_key`` table's fields as ``(name, type_expr, constraint)`` triples
# (packet 49; the ``finding``/``principal`` idiom — these fields carry no closed
# vocabulary to mutate). ``hash`` is the REQUIRED, non-empty SHA-512 hex of the
# ``<name>:<secret>`` credential (UNIQUE index — the O(1) lookup + dedup backstop);
# ``name`` is the REQUIRED, non-empty key label (part of the UNIQUE(principal, name)
# composite). ``principal`` is a REQUIRED ``record<principal>`` owner link — §1.4's
# "new field on a POPULATED table must be option<>" does NOT apply: ``principal_key``
# is a brand-new empty table, so every key has an owner at mint (an ownerless key is a
# credential belonging to nobody). ``created_at`` self-stamps via ``DEFAULT
# time::now()`` (the store OMITS it on write). ``expires_at``/``revoked_at`` are
# ``option<datetime>`` with NO DEFAULT — the ``to.seen_at``/``acked_at`` "IS NONE is
# live" idiom: ``WHERE revoked_at IS NONE`` is the "active" predicate, and a DEFAULT
# would make every key look already-stamped (revoked/expired) the instant it is minted.
_PRINCIPAL_KEY_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
    ("hash", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),
    ("name", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),
    ("principal", f"record<{PRINCIPAL_TABLE}>", ""),
    ("created_at", "datetime", "DEFAULT time::now()"),
    ("expires_at", "option<datetime>", ""),
    ("revoked_at", "option<datetime>", ""),
)


def _principal_key_statements() -> list[str]:
    """The ``principal_key`` table: the field set + its two UNIQUE indexes (packet 49).

    Emits, in order: the SCHEMAFULL table; one ``DEFINE FIELD`` per
    :data:`_PRINCIPAL_KEY_FIELD_SPECS` entry (routed through the shared
    :func:`_define_field` — the #107 ``OVERWRITE`` policy, proven shared by the
    schema mutation pin); the UNIQUE index on ``hash`` (the credential lookup +
    dedup backstop — ``WHERE hash = $h`` over a preimage-resistant digest, O(1) with
    uniform timing and no name-existence oracle) and the UNIQUE composite index on
    ``(principal, name)`` (per-principal label uniqueness — two humans may each name
    a key ``laptop``; ``revoke-key --email e --name laptop`` is deterministic WITHIN
    a principal). A record-link column (``principal``) is indexable, so the composite
    is a plain UNIQUE over two REQUIRED columns (§1.8 N/A — neither index spans an
    ``option<>`` column).

    ``principal_key.principal`` is ``record<{PRINCIPAL_TABLE}>``, so this slice is
    folded into :func:`generate_ddl` immediately AFTER :func:`_principal_statements`
    (the ``briefed`` → ``agent`` precedent — the link's target table defined first).
    Every statement is idempotent (``IF NOT EXISTS`` for the table/indexes,
    ``OVERWRITE`` for its fields — see :func:`_define_field`), so applying it twice —
    on the boot re-run :meth:`ensure_ready` performs — is a safe no-op.
    """
    statements: list[str] = [_define_table(PRINCIPAL_KEY_TABLE)]
    statements += [
        _define_field(PRINCIPAL_KEY_TABLE, name, type_expr, constraint=constraint)
        for name, type_expr, constraint in _PRINCIPAL_KEY_FIELD_SPECS
    ]
    statements.append(
        _unique_index(PRINCIPAL_KEY_TABLE, f"{PRINCIPAL_KEY_TABLE}_hash", ("hash",))
    )
    statements.append(
        _unique_index(
            PRINCIPAL_KEY_TABLE, f"{PRINCIPAL_KEY_TABLE}_principal_name", ("principal", "name")
        )
    )
    return statements


def generate_principal_key_ddl() -> str:
    """Generate just the ``principal_key`` table DDL — packet 49's per-user API-key
    slice that :meth:`~loremaster.principal_keys.PrincipalKeyStore.ensure_ready`
    applies on its OWN connection.

    Mirrors :func:`generate_principal_ddl`: the ``principal_key`` table is ALSO
    folded into :func:`generate_ddl` (immediately after ``principal`` — its link
    target), so the primary ``write_store.ensure_ready()`` creates the table the
    moment packet 49 ships. Needs NEITHER the embedding ``dim`` NOR the analyzer — a
    key is addressed by its ``hash``, never retrieved semantically. Every statement
    is idempotent (``IF NOT EXISTS`` for the table/indexes, ``OVERWRITE`` for its
    fields — see :func:`_define_field`), so applying it twice — or alongside
    :func:`generate_ddl`, in either order — is a safe no-op.

    Returns:
        A newline-separated, semicolon-terminated DDL string ready to hand to a
        single SurrealDB ``query()`` call (or wrap in one ``BEGIN … COMMIT``).
    """
    return ";\n".join(_principal_key_statements()) + ";\n"


# --------------------------------------------------------------------------- #
# ``keep`` + ``member_of`` (packet 60) — the Keep substrate: a collaboration
# space (``keep``) owned by exactly one keeper (a ``record<principal>`` FIELD
# LINK — design sidecar Fork A) whose household membership is the many-to-many
# ``member_of`` RELATION edge (``principal --member_of--> keep``, ENFORCED +
# UNIQUE(in, out) — Fork F).
#
# Introduced as RED STUBS by contract-60-w1 (2026-08-22) — ``_keep_statements`` /
# ``_member_of_statements`` emitting ``[]`` and ``generate_keep_ddl`` emitting ``""``
# so every packet-60 schema pin failed BEHAVIOURALLY (never an ImportError, never an
# uncollectable module — finding #133; the same idiom the packet-49 principal_key
# slice shipped under) — and GREENED by the wave-1 builder per the design sidecar
# (``docs/design/2026-08-22-packet60-keep-substrate-rulings.md`` Forks B/C/D/F + the
# Emission plan) and store law §1.1 (fields ``OVERWRITE``; the ``keep`` table +
# ``keeper`` index + ``member_of`` UNIQUE index ``IF NOT EXISTS``; the ``member_of``
# RELATION table ``OVERWRITE … ENFORCED``). The two assemblers + ``generate_keep_ddl``
# now emit the real slice, folded into ``generate_ddl``.
#
# The CONSTANTS and FIELD SPECS below are REAL and mutation-provable: the mutation
# pins monkeypatch ``_KEEP_TYPES`` / ``_KEEP_RANKS`` and the exact-domain pins read
# them, and ``_enforced_relations_scaffold.KNOWN_RELATION_EDGES`` imports
# ``MEMBER_OF_RELATION`` / ``KEEP_TABLE`` / ``generate_keep_ddl``.
# See ``docs/plans/v2/receipts/…/REPORT-contract-60-w1.md``.
# --------------------------------------------------------------------------- #

KEEP_TABLE = "keep"
MEMBER_OF_RELATION = "member_of"

# The ``keep.type`` closed domain — the collaboration flavour (design Fork B). NO
# DEFAULT: ``type`` is the essential discriminator, so every create must CHOOSE it;
# a silent default would mislabel keeps. Derived into the ASSERT at CALL TIME in
# :func:`_keep_statements` (the :func:`_principal_statements` idiom), NEVER frozen
# into a module constant, so a mutation of this tuple moves the emitted ASSERT (the
# derivation is mutation-provable). The domain WIDENS safely (a new collaboration
# flavour is a new ``type``); NARROWING it write-poisons existing rows (store
# reference §1.4) — same trigger discipline as ``rank``.
_KEEP_TYPES = ("project", "team", "session", "dm")

# The ``member_of.rank`` closed domain — the per-Keep collaboration rank (design
# Fork C). FLAT today: one value, ``'contributor'`` (the plain collaborator who may
# write, distinct from the GLOBAL ``principal.role`` vocabulary — never reuse
# ``'member'``). DEFAULT ``'contributor'``. Derived at CALL TIME in
# :func:`_member_of_statements` from this tuple (mutation-provable). ⚠ The domain is
# designed to WIDEN (viewer/steward/keeper land in 61+); a widening that RETAINS
# ``'contributor'`` is a pure widen (store reference §1.4 — rows intact, still
# writable). NARROWING or REMOVING ``'contributor'`` is the poison direction, a data
# migration, never a bare tuple edit.
_KEEP_RANK_CONTRIBUTOR = "contributor"
_KEEP_RANKS = (_KEEP_RANK_CONTRIBUTOR,)

# The ``keep`` table's NON-DOMAIN fields as ``(name, type_expr, constraint)`` triples
# (the ``principal`` idiom — these fields carry no closed vocabulary to mutate;
# ``type`` is NOT here, it is emitted at CALL TIME from :data:`_KEEP_TYPES`).
# ``keeper`` is the REQUIRED ``record<principal>`` owner link — §1.4's "new field on a
# POPULATED table must be option<>" does NOT apply: ``keep`` is a brand-new empty
# table, so a required (non-``option``) field is legal at birth (design greenfield
# note; the ``principal_key.principal`` precedent). ``name`` is an OPTIONAL human
# label carrying the SAME non-empty ASSERT ``principal.subject`` uses — an
# ``option<>`` field SKIPS the ASSERT on NONE (so a ``dm`` keep with no label is
# legal, and multiple NONE coexist — §1.8) but FIRES on a present empty string.
# ``created_at`` self-stamps via ``DEFAULT time::now()`` (the store OMITS it on
# write). Field ORDER is DDL-irrelevant.
_KEEP_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
    ("keeper", f"record<{PRINCIPAL_TABLE}>", ""),
    ("name", "option<string>", _NON_EMPTY_STRING_ASSERT),
    ("created_at", "datetime", "DEFAULT time::now()"),
)

# The ``member_of`` edge's NON-DOMAIN edge-local fields (the ``briefed`` idiom —
# ``in``/``out`` are auto-defined by TYPE RELATION and NEVER hand-declared). ``since``
# is the membership-provenance stamp, ``DEFAULT time::now()`` (mirroring ``briefed.at``).
# ``rank`` is NOT here: it is a closed vocabulary emitted at CALL TIME from
# :data:`_KEEP_RANKS` in :func:`_member_of_statements`.
_MEMBER_OF_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
    ("since", "datetime", "DEFAULT time::now()"),
)


def _keep_statements() -> list[str]:
    """The ``keep`` node table: the field set + the NON-UNIQUE ``keeper`` index.

    Emits, in order: the SCHEMAFULL ``keep`` table (:func:`_define_table` →
    ``IF NOT EXISTS``); one ``DEFINE FIELD`` per :data:`_KEEP_FIELD_SPECS` entry
    (``keeper``/``name``/``created_at``) followed by the ``type`` field-def, all
    routed through the shared :func:`_define_field` (→ ``OVERWRITE``, #107); the
    NON-UNIQUE index on ``keeper`` (:func:`_plain_index` → ``IF NOT EXISTS`` — a
    principal keeps MANY keeps) so ``WHERE keeper = $p`` is an IndexScan (design Fork A
    rider; store reference §4 "a scalar attribute filtered through a hop is
    un-indexable — keep scalars as indexed fields").

    ⚠ The ``type`` ASSERT is derived HERE, at CALL time, from :data:`_KEEP_TYPES`
    (the :func:`_principal_statements` idiom, NOT a frozen import-time constant) —
    ``NO DEFAULT`` (Fork B: ``type`` is the essential discriminator, every create must
    CHOOSE it). A join frozen at import cannot move under a mutation pin's monkeypatch
    of the tuple; deriving it here makes a tuple change move the emitted ASSERT.
    """
    type_allowed = ", ".join(f"'{keep_type}'" for keep_type in _KEEP_TYPES)
    type_spec: tuple[tuple[str, str, str], ...] = (
        ("type", _CHUNK_STRING_TYPE, f"ASSERT $value IN [{type_allowed}]"),
    )
    statements: list[str] = [_define_table(KEEP_TABLE)]
    statements += [
        _define_field(KEEP_TABLE, name, type_expr, constraint=constraint)
        for name, type_expr, constraint in (*_KEEP_FIELD_SPECS, *type_spec)
    ]
    statements.append(_plain_index(KEEP_TABLE, f"{KEEP_TABLE}_keeper", ("keeper",)))
    return statements


def _member_of_statements() -> list[str]:
    """The ``member_of`` household edge: the RELATION table + fields + UNIQUE(in, out).

    Emits, in order: the ``member_of`` RELATION table
    (:func:`_define_relation_table` ``(MEMBER_OF_RELATION, PRINCIPAL_TABLE, KEEP_TABLE,
    enforced=True)`` → ``DEFINE TABLE OVERWRITE member_of TYPE RELATION IN principal
    OUT keep ENFORCED SCHEMAFULL`` — Fork F; ``OVERWRITE`` because ``IF NOT EXISTS`` is
    a MEASURED silent no-op on an existing edge table, §1.1); one ``DEFINE FIELD`` per
    :data:`_MEMBER_OF_FIELD_SPECS` entry (``since``) followed by the call-time-derived
    ``rank`` field-def (DEFAULT ``'contributor'`` + ASSERT built HERE from
    :data:`_KEEP_RANKS`, mutation-provable); and the UNIQUE index on ``(in, out)``
    (:func:`_unique_index` → ``IF NOT EXISTS`` — the ``briefed`` precedent, so a
    double-add of the same (principal, keep) pair is a loud ERR, not a second edge).

    THIS SLICE IS ORDER-DEPENDENT on both endpoint tables: ``IN principal`` needs the
    ``principal`` table and ``OUT keep`` needs the ``keep`` table, so its ``DEFINE
    TABLE`` must be emitted AFTER both — which the :func:`generate_ddl` fold order and
    :func:`generate_keep_ddl` (keep before member_of) guarantee.
    """
    rank_allowed = ", ".join(f"'{rank}'" for rank in _KEEP_RANKS)
    rank_spec: tuple[tuple[str, str, str], ...] = (
        (
            "rank",
            _CHUNK_STRING_TYPE,
            f"DEFAULT '{_KEEP_RANK_CONTRIBUTOR}' ASSERT $value IN [{rank_allowed}]",
        ),
    )
    statements: list[str] = [
        _define_relation_table(MEMBER_OF_RELATION, PRINCIPAL_TABLE, KEEP_TABLE, enforced=True)
    ]
    statements += [
        _define_field(MEMBER_OF_RELATION, name, type_expr, constraint=constraint)
        for name, type_expr, constraint in (*_MEMBER_OF_FIELD_SPECS, *rank_spec)
    ]
    statements.append(
        _unique_index(MEMBER_OF_RELATION, f"{MEMBER_OF_RELATION}_in_out", ("in", "out"))
    )
    return statements


def generate_keep_ddl() -> str:
    """Generate just the ``keep`` + ``member_of`` DDL — the Keep substrate's schema slice.

    Returns ``";\\n".join(_keep_statements() + _member_of_statements()) + ";\\n"`` — the
    ``keep`` table + its ``keeper`` index THEN the ``member_of`` edge + its UNIQUE index
    (keep before member_of: the edge's ``OUT keep`` endpoint must be defined first), a
    schema SLICE a :class:`~loremaster.keeps.KeepStore` applies on its OWN connection
    (mirroring :func:`generate_principal_ddl`). ``keep`` + ``member_of`` are ALSO folded
    into the global :func:`generate_ddl` (Variant A — so the primary
    ``write_store.ensure_ready()`` creates the tables the moment packet 60 ships), and
    the edge is emitted IDENTICALLY by both paths (they share these two assemblers).
    """
    return ";\n".join(_keep_statements() + _member_of_statements()) + ";\n"


def generate_agent_ddl() -> str:
    """Generate just the ``agent`` table DDL — the PKT-28 C1 agent registry's
    schema slice.

    Mirrors :func:`generate_task_ddl`: a schema SLICE
    :class:`~loremaster.agents.AgentRegistry` applies on its OWN connection at
    :meth:`ensure_ready`, independent of the full :func:`generate_ddl`. Needs
    NEITHER the embedding ``dim`` NOR the analyzer — an agent is resolved by
    exact identity, never retrieved semantically. Every statement is idempotent
    (``IF NOT EXISTS`` for the table, ``OVERWRITE`` for its fields — see
    :func:`_define_field`), so applying it twice — or alongside
    :func:`generate_ddl`, in either order — is a safe no-op.

    Returns:
        A newline-separated, semicolon-terminated DDL string ready to hand to a
        single SurrealDB ``query()`` call (or wrap in one ``BEGIN … COMMIT``).
    """
    statements: list[str] = _agent_statements()
    return ";\n".join(statements) + ";\n"


def generate_brief_ddl() -> str:
    """Generate the ``brief`` + ``briefed`` + ``brief_counter`` DDL — the PKT-28
    C1 brief ledger's schema slice.

    Mirrors :func:`generate_finding_ddl` bundling ``finding`` +
    ``finding_counter``: :class:`~loremaster.briefs.BriefLedger` owns the
    ``brief`` node table, the ``briefed`` relation edge, AND the
    ``brief_counter`` version-mint table (:func:`_brief_counter_statements` —
    per-NAME rows, unlike ``finding_counter``'s singleton), applying this
    combined slice on its OWN connection at :meth:`ensure_ready`, independent
    of the full :func:`generate_ddl`. Needs NEITHER the embedding ``dim`` NOR
    the analyzer — a brief is addressed by (name, version), never retrieved
    semantically. Every statement is idempotent (``IF NOT EXISTS`` for the
    tables, ``OVERWRITE`` for fields — see :func:`_define_field`), so applying
    it twice — or alongside :func:`generate_ddl`, in either order — is a safe
    no-op.

    Returns:
        A newline-separated, semicolon-terminated DDL string ready to hand to a
        single SurrealDB ``query()`` call (or wrap in one ``BEGIN … COMMIT``).
    """
    statements: list[str] = _brief_statements() + _briefed_statements() + _brief_counter_statements()
    return ";\n".join(statements) + ";\n"


def generate_message_ddl() -> str:
    """Generate the packet-03 ``message`` + ``to`` + ``message_seq`` DDL — the
    durable comms MESSAGE GRAPH's schema slice.

    Mirrors :func:`generate_agent_ddl`: a schema SLICE
    :class:`~loremaster.messages.MessageLedger` (packet 03a) applies on its OWN
    connection at :meth:`ensure_ready`, AFTER :func:`generate_agent_ddl` (the
    ``to`` edge's ``OUT agent`` and ``message.sender``'s ``record<agent>`` both
    reference the ``agent`` table). Needs NEITHER the embedding ``dim`` NOR the
    analyzer — a message is coordinated by sequence and delivery edge, never
    retrieved semantically.

    NOT fully idempotent-by-no-op like the other slices: the ``message`` node
    table, its indexes and the sequence are ``IF NOT EXISTS`` (safe re-apply), and
    the ``to`` relation table is ``OVERWRITE`` — a FULL REPLACE that re-lands the
    same definition on every :meth:`ensure_ready`, which is exactly what makes a
    changed IN/OUT/ENFORCED clause converge on an existing store rather than
    silently no-op (store reference §1.1). Re-applying the UNCHANGED slice is still
    a safe no-op that neither raises nor resets the sequence (verified 3.2.1).

    Returns:
        A newline-separated, semicolon-terminated DDL string ready to hand to a
        single SurrealDB ``query()`` call (or wrap in one ``BEGIN … COMMIT``).
    """
    statements: list[str] = _message_statements()
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
    statement is idempotent (``IF NOT EXISTS`` for the tables/indexes,
    ``OVERWRITE`` for fields — see :func:`_define_field`), so applying it twice
    (or alongside :func:`generate_ddl`) is a safe no-op.

    Returns:
        A newline-separated, semicolon-terminated DDL string ready to hand to a
        single SurrealDB ``query()`` call.
    """
    statements: list[str] = _code_node_statements()
    statements += _name_statements()
    statements += _refers_statements()
    statements += _answers_to_statements()
    return ";\n".join(statements) + ";\n"


# =============================================================================
# ⚠ PACKET 11-i-a — floor calibration + the leader-election lease.
#
# The NAMES, SIGNATURES and closed-domain tuples were FROZEN by the contract
# author (`contract-11ia-1`) and are the interface 11-i-b cites; the emitters
# below were built by `builder-11ia-1` against that contract. Both closed tuples
# are pinned as EXACT SETS against an explicit expected literal in
# ``test_floor_calibration_domain.py``, so adding or removing a member is a diff
# a reviewer sees rather than a silent change to what 11-ii serves.
#
# Design of record: `docs/design/2026-07-24-floor-calibration.md` §7 + Addendum
# B (B4 schema/migration) · `docs/design/2026-07-25-floor-calibration-addendum-F.md`
# F4/F5/F6 · `docs/design/2026-07-25-floor-calibration-addendum-F-r2.md` R10.2 ·
# `docs/plans/v2/receipts/2026-07-24-packet11i/RULINGS-2026-07-25.md`.
#
# DDL DECISION RULE (store reference §1.1, NON-NEGOTIABLE): plain TABLE →
# ``IF NOT EXISTS``; FIELD → ``OVERWRITE``; INDEX → ``IF NOT EXISTS``; ``ALTER``
# is a trap, not the migration verb (§1.3). None of these tables is a RELATION
# and none carries a SEQUENCE, so the two inversions the packet's entry check
# warns about (§1.1's RELATION row, #146's SEQUENCE residual) do not apply —
# and if either is ever added, §1 is re-read FIRST.
# =============================================================================

# The append-only measurement table: one row per completed calibration run per
# head. History is the F6 tuning record and takes no field-migration pressure.
FLOOR_MEASUREMENT_TABLE = "floor_measurement"

# The head pointer table: ONE row per :func:`head_identity` value, carrying the
# adopted measurement link and the monotonic ``revision`` every adopting run
# contends on. THE HOT ROW (B4) — ``_txn.retry_on_conflict`` is the ONE driver.
FLOOR_HEAD_TABLE = "floor_head"

# The single leader-election lease row (R10.2). Deployment-global: F6's axes do
# not apply, so the id is a fixed singleton.
LEASE_TABLE = "lease"
LEASE_SINGLETON_ID = "singleton"

# The CLOSED, exactly-pinned engine state set (§7 + F4.1's rename). Every value
# distinct, and the name F4.1 retired must appear nowhere in production — the
# retired literal itself is NOT written here, because the corpse sweep in
# ``test_floor_calibration_schema.py`` scans production source with a bare,
# anchor-free pattern and a comment naming the corpse makes that pin RED.
FLOOR_STATES: tuple[str, ...] = (
    "unmeasured",
    "measuring",
    "measured",
    "measured_not_adopted",
    "invalidated_remeasuring",
    "measurement_failed",
    "insufficient_corpus",
    "disabled",
)

# The CLOSED, exactly-pinned non-adoption cause enum (F5). The two degeneracies
# — ``substrate_indiscriminate`` (a CORPUS property) and ``interval_degenerate``
# (an INSTRUMENT property) — are DISTINCT VALUES BY RULING: collapsing them
# would let an instrument artifact be served as a confident corpus claim.
FLOOR_NON_ADOPTION_CAUSES: tuple[str, ...] = (
    "head_retained_overlap",
    "catch_bar_unmet",
    "substrate_indiscriminate",
    "interval_degenerate",
    "stability_gate_unmet",
)

# The ``floor_measurement`` column NAMES, in write order — the SINGLE source of
# truth for the ledger's projected history read as well as for the DDL. Only the
# NAMES live here; the TYPES and the closed-domain ``ASSERT``s are emitted inside
# :func:`_floor_measurement_statements`, which reads :data:`FLOOR_STATES` /
# :data:`FLOOR_NON_ADOPTION_CAUSES` AT CALL TIME so the assert is a DERIVATION of
# the ruled domains rather than a hand-typed twin of them.
FLOOR_MEASUREMENT_COLUMNS: tuple[str, ...] = (
    "head_identity",
    "head_revision",
    "state",
    "non_adoption_cause",
    "note",
    "floor",
    "ci_low",
    "ci_high",
    "adopted_n",
    "instrument_version",
    "corpus_content_digest",
    "embedding_schema_fingerprint",
    "trigger",
    "created_at",
)

# The measurement column carrying the head this row measured (F6/O7) and the head
# revision an ADOPTING commit minted for it. The revision is written INSIDE the
# commit transaction (see ``FloorCalibrationStore.record_measurement``) precisely
# so the receipt can be read back from an IMMUTABLE row instead of re-reading the
# hot head row, which a concurrent racer may already have advanced.
FLOOR_MEASUREMENT_HEAD_IDENTITY_COLUMN = "head_identity"
FLOOR_MEASUREMENT_HEAD_REVISION_COLUMN = "head_revision"
# The append-only history's ordering column — ``measurement_history`` reads
# newest-first off it, and the index below is what keeps that read off a table
# scan as the history grows.
FLOOR_MEASUREMENT_CREATED_AT_COLUMN = "created_at"

# The ``floor_head`` columns that are NOT axis columns. The axis columns
# themselves are DERIVED from the head-identity registry — see
# :func:`_floor_head_statements`.
FLOOR_HEAD_REVISION_COLUMN = "revision"
FLOOR_HEAD_MEASUREMENT_COLUMN = "measurement"
FLOOR_HEAD_ADOPTED_AT_COLUMN = "adopted_at"
FLOOR_HEAD_AXES_COLUMN = "axes"

# The ``lease`` row's columns: the library's four record fields (ALL STRINGS —
# ``kubernetes.leaderelection`` writes ``str(now)``, so a ``datetime`` column
# would reject every renewal it ever makes) plus our two store-minted counters.
LEASE_HOLDER_IDENTITY_COLUMN = "holder_identity"
LEASE_REVISION_COLUMN = "revision"
LEASE_FENCE_EPOCH_COLUMN = "fence_epoch"
_LEASE_RECORD_STRING_COLUMNS: tuple[str, ...] = (
    LEASE_HOLDER_IDENTITY_COLUMN,
    "lease_duration",
    "acquire_time",
    "renew_time",
)


def _floor_measurement_statements() -> list[str]:
    """The append-only ``floor_measurement`` table: fields + the history index.

    ⚠ **EVERY COLUMN BUT ``head_identity``, ``state`` AND ``created_at`` IS
    ``option<>``**, and that is forced rather than chosen: store reference §1.4
    requires a NEW field on a possibly-populated table to be ``option<>`` (a
    required one poisons every existing row, and a ``DEFAULT`` does NOT rescue
    it), and ``TestTheSchemaMigratesAnEXISTINGStore`` stands in for an older
    deployment by creating a row that carries only the REQUIRED columns.

    ⚠ **``head_identity`` IS REQUIRED — RULING O7 (2026-07-26), and the trade was
    stated before it was taken.** The history is APPEND-ONLY, so a measurement row
    that cannot name its own scope is unattributable FOREVER: no later read can
    recover which axes it measured, and both the head mint and the exact-skip
    scheduler are keyed on exactly that. There is no state in which a row
    legitimately lacks a head — the axes are INPUTS, fixed before a measurement
    begins, so even ``measurement_failed`` and ``insufficient_corpus`` rows know
    their scope at creation time. The §1.4 objection does not apply here because
    this table has never been deployed; O7's re-open trigger is a genuine legacy
    corpus found with head-less rows in it, which is a DATA migration with a
    stated backfill, not a loosened column. Pinned by
    ``test_a_measurement_row_with_NO_head_identity_is_REFUSED`` (with a positive
    control) in ``test_floor_calibration_schema.py``. The ledger's own derivation
    in :meth:`~loremaster.floor_calibration.store.FloorCalibrationStore.record_measurement`
    stays the ergonomic layer; this column is the backstop for a raw writer.

    The ``ASSERT``s on ``state`` / ``non_adoption_cause`` are generated FROM
    :data:`FLOOR_STATES` / :data:`FLOOR_NON_ADOPTION_CAUSES` at call time, never
    typed beside them — a hand-typed twin drifts the first time a state is added
    and no gate can see prose disagreeing with code.
    """
    allowed_states = ", ".join(f"'{state}'" for state in FLOOR_STATES)
    allowed_causes = ", ".join(f"'{cause}'" for cause in FLOOR_NON_ADOPTION_CAUSES)
    # ``(name, type_expr, constraint)`` — the ORDER matches
    # :data:`FLOOR_MEASUREMENT_COLUMNS`, which is what the ledger projects.
    specs: tuple[tuple[str, str, str], ...] = (
        # REQUIRED (ruling O7) — see the docstring. Not ``option<>``, and not
        # ``DEFAULT``-rescued either: a default would FABRICATE an identity, which
        # is the opposite of what the ruling is for.
        (FLOOR_MEASUREMENT_HEAD_IDENTITY_COLUMN, "string", ""),
        (FLOOR_MEASUREMENT_HEAD_REVISION_COLUMN, "option<int>", ""),
        ("state", "string", f"ASSERT $value IN [{allowed_states}]"),
        # A BARE assert: an ``option<>`` field's ASSERT is not evaluated when the
        # value is NONE (store reference §7), so a ``$value = NONE OR`` guard
        # would be cruft that teaches the next author it is required.
        ("non_adoption_cause", "option<string>", f"ASSERT $value IN [{allowed_causes}]"),
        ("note", "option<string>", ""),
        ("floor", "option<float>", ""),
        ("ci_low", "option<float>", ""),
        ("ci_high", "option<float>", ""),
        ("adopted_n", "option<int>", ""),
        ("instrument_version", "option<string>", ""),
        ("corpus_content_digest", "option<string>", ""),
        ("embedding_schema_fingerprint", "option<string>", ""),
        ("trigger", "option<string>", ""),
        (FLOOR_MEASUREMENT_CREATED_AT_COLUMN, "datetime", "DEFAULT time::now()"),
    )
    statements: list[str] = [_define_table(FLOOR_MEASUREMENT_TABLE)]
    statements += [
        _define_field(FLOOR_MEASUREMENT_TABLE, name, type_expr, constraint=constraint)
        for name, type_expr, constraint in specs
    ]
    statements.append(
        _plain_index(
            FLOOR_MEASUREMENT_TABLE,
            f"{FLOOR_MEASUREMENT_TABLE}_head_created",
            (FLOOR_MEASUREMENT_HEAD_IDENTITY_COLUMN, FLOOR_MEASUREMENT_CREATED_AT_COLUMN),
        )
    )
    return statements


def _floor_head_statements() -> list[str]:
    """The ``floor_head`` pointer table: ONE HOT ROW per head identity.

    The axis columns are DERIVED from
    :data:`~loremaster.floor_calibration.domain.FLOOR_HEAD_ALWAYS_SERIALISED_AXES`
    — imported inside the function so this schema module stays an import-time
    LEAF (every store module imports it; nothing it emits may drag the domain
    package in at import time). Registering a new always-serialised axis
    therefore adds its column here and its bound value at the ledger's write in
    ONE change, instead of leaving a column list to drift.

    ⚠ **THE AXIS COLUMNS ARE ``option<string>`` — INCLUDING ``scope``** — for the
    §1.4 reason ``floor_measurement``'s columns are, and that is what lets
    ``M14``'s head leg stand in for an older deployment with a ``scope``-only row.

    ⚠ **``revision`` IS THE ONE REQUIRED COLUMN HERE: ``int DEFAULT 0``, NOT
    ``option<>``** — it is the monotonic counter every adopting run contends on
    (the hot row, B4), and a head whose revision could be NONE is a head no
    contender can compare against. **Store reference §1.4 applies to it in full,
    and a ``DEFAULT`` does NOT rescue an existing row that lacks the field.**
    Measured 2026-07-26 on the 3.2.1 test store, with a control: a ``floor_head``
    row written before this column existed SURVIVES the migration and stays
    readable, but an ``UPDATE`` that does not itself set ``revision`` is
    REJECTED (*"Couldn't coerce value for field `revision` … Expected `int` but
    found `NONE`"*) — and the SAME statement is accepted once the column is
    populated, so the refusal is the missing column and not the write. Nothing
    breaks today for exactly one reason: **every production write to this table
    is the mint, and the mint sets it** (``revision = (revision ?? 0) + 1`` in
    ``FloorCalibrationStore._head_mint_statement`` — the ``??`` is what covers a
    legacy row, not the ``DEFAULT``). A future writer that touches a head row
    WITHOUT setting ``revision`` re-opens this; keep the mint the only writer, or
    backfill.

    (This docstring previously claimed the opposite in both directions —
    "everything except ``scope`` is optional" — while ``scope`` was optional and
    ``revision`` was not. Cold audit 11-i-a F2.)
    """
    from loremaster.floor_calibration.domain import (  # noqa: PLC0415 - see the docstring
        FLOOR_HEAD_ALWAYS_SERIALISED_AXES,
    )

    statements: list[str] = [_define_table(FLOOR_HEAD_TABLE)]
    statements += [
        # ``option<string>``, not ``string``: M14's migration leg writes a head row
        # carrying ONE axis column, and §1.4 forbids a required NEW field on a
        # table that may already hold rows. The LEDGER always writes every axis
        # (its head id is a pure function of them), so an absent axis column can
        # only come from a raw writer.
        _define_field(FLOOR_HEAD_TABLE, axis, "option<string>")
        for axis in FLOOR_HEAD_ALWAYS_SERIALISED_AXES
    ]
    statements += [
        _define_field(FLOOR_HEAD_TABLE, FLOOR_HEAD_REVISION_COLUMN, "int", constraint="DEFAULT 0"),
        _define_field(
            FLOOR_HEAD_TABLE,
            FLOOR_HEAD_MEASUREMENT_COLUMN,
            f"option<record<{FLOOR_MEASUREMENT_TABLE}>>",
        ),
        _define_field(FLOOR_HEAD_TABLE, FLOOR_HEAD_ADOPTED_AT_COLUMN, "option<datetime>"),
        # The FULL axis mapping the id was minted from — the authority a reader
        # resolves ``AdoptedHead.axes`` from, including any registered axis that
        # is NOT an always-serialised column. ``FLEXIBLE`` is TRAILING (§7).
        _define_field(FLOOR_HEAD_TABLE, FLOOR_HEAD_AXES_COLUMN, "option<object> FLEXIBLE"),
    ]
    return statements


def _lease_statements() -> list[str]:
    """The single leader-election ``lease`` row's table (R10.2).

    ⚠ **ALL FOUR OF THE LIBRARY'S RECORD FIELDS ARE ``option<string>``.**
    ``kubernetes.leaderelection`` writes ``LeaderElectionRecord(identity,
    str(lease_duration), str(now), str(now))`` — four STRINGS, the times NAIVE
    local ``datetime.fromtimestamp`` renders — so a ``datetime``-typed
    ``renew_time`` rejects every renewal the library ever makes. ``option<>`` on
    ``holder_identity`` is ruled decision 23: ``release_if_held`` clears the
    holder to NONE, and a required column makes graceful handoff impossible
    (§1.4: a ``DEFAULT`` does not rescue it either).

    ``revision`` is the optimistic-concurrency token (the ``resourceVersion``
    role) and ``fence_epoch`` is §R2's fencing token; both are minted STORE-SIDE
    in the same UPDATE, so no reader can observe a half-applied pair.
    """
    statements: list[str] = [_define_table(LEASE_TABLE)]
    statements += [
        _define_field(LEASE_TABLE, column, "option<string>")
        for column in _LEASE_RECORD_STRING_COLUMNS
    ]
    statements += [
        _define_field(LEASE_TABLE, LEASE_REVISION_COLUMN, "int", constraint="DEFAULT 0"),
        _define_field(LEASE_TABLE, LEASE_FENCE_EPOCH_COLUMN, "int", constraint="DEFAULT 0"),
    ]
    return statements


def generate_floor_calibration_ddl() -> str:
    """The ``floor_measurement`` + ``floor_head`` slice (B4).

    Returns:
        A newline-separated, semicolon-terminated DDL string, in the same shape
        every other ``generate_*_ddl`` returns, ready to wrap in ONE
        ``BEGIN … COMMIT`` and run through ``execute_transaction`` (NEVER a bare
        multi-statement ``query()`` — store reference §3 validates statement[0]
        only).
    """
    statements: list[str] = _floor_measurement_statements()
    statements += _floor_head_statements()
    return ";\n".join(statements) + ";\n"


def generate_lease_ddl() -> str:
    """The single ``lease`` row's slice (R10.2).

    Returns:
        A newline-separated, semicolon-terminated DDL string.
    """
    return ";\n".join(_lease_statements()) + ";\n"
