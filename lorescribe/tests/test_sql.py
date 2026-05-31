"""Contract tests for :class:`lorescribe.sql.SqlChunker`.

These tests pin the SQL chunker's behaviour against realistic Postgres
fixtures, with particular weight on the adversarial robustness cases that a
naive ``sqlglot.parse`` chokes on:

* ``psql`` meta-commands (``\\set``), ``:'param'`` substitutions, and a
  ``DO $$ ... $$`` procedural block must NOT crash and must yield chunks.
* A ``WITH RECURSIVE`` query's ``referenced_tables`` excludes its CTE alias
  names (the base tables only — the verified gotcha).
* Many ``CREATE TABLE`` / ``CREATE INDEX`` statements get distinct identities
  via the created object name.
* The leading intent comment is captured into metadata.
* A ``WITH`` query that exceeds an injected ``max_input_tokens`` is sub-split
  into per-CTE sibling chunks carrying ``sub_ordinal``.

Fixtures use the production token cap from ``conftest`` and the same injected
counter the framework wires through ``ChunkContext``.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from lorescribe.models import Chunk, ChunkContext
from lorescribe.sql import SqlChunker

from .conftest import (
    SAMPLE_SLUG,
    VOYAGE4_MAX_INPUT_TOKENS,
)

SQL_FILE_PATH: str = "validation/diagnostics/demand_snapshot.sql"


def _make_ctx(
    count_tokens: Callable[[str], int],
    max_input_tokens: int = VOYAGE4_MAX_INPUT_TOKENS,
) -> ChunkContext:
    """Build a ``ChunkContext`` for a SQL file with the given token budget."""
    return ChunkContext(
        slug=SAMPLE_SLUG,
        file_path=SQL_FILE_PATH,
        count_tokens=count_tokens,
        max_input_tokens=max_input_tokens,
    )


@pytest.fixture
def chunker() -> SqlChunker:
    """A fresh ``SqlChunker`` per test."""
    return SqlChunker()


@pytest.fixture
def ctx(count_tokens: Callable[[str], int]) -> ChunkContext:
    """A ``ChunkContext`` at the production 8192-token cap."""
    return _make_ctx(count_tokens)


# --- Realistic Postgres fixtures -------------------------------------------

ADVERSARIAL_PSQL: str = (
    "\\set ON_ERROR_STOP on\n"
    "\\timing on\n"
    "-- diagnostic: rebuild the demand snapshot for a target date\n"
    "SELECT :'target_date' AS run_date;\n"
    "DO $$\n"
    "BEGIN\n"
    "  IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'demand_weekly') THEN\n"
    "    RAISE NOTICE 'missing demand_weekly';\n"
    "  END IF;\n"
    "END\n"
    "$$;\n"
    "CREATE TABLE demand_snapshot (id int, qty int);\n"
)

WITH_RECURSIVE: str = (
    "WITH RECURSIVE ancestors AS (\n"
    "  SELECT id, parent_id FROM product_category WHERE id = 5\n"
    "  UNION ALL\n"
    "  SELECT c.id, c.parent_id\n"
    "    FROM product_category c\n"
    "    JOIN ancestors a ON c.parent_id = a.id\n"
    ")\n"
    "SELECT a.id, pt.name\n"
    "  FROM ancestors a\n"
    "  JOIN product_template pt ON pt.categ_id = a.id;\n"
)

MANY_DDL: str = (
    "CREATE TABLE demand_weekly (id int, qty int);\n"
    "CREATE TABLE demand_monthly (id int, qty int);\n"
    "CREATE INDEX idx_demand_weekly_id ON demand_weekly (id);\n"
    "CREATE INDEX idx_demand_monthly_id ON demand_monthly (id);\n"
)

LEADING_COMMENT_SQL: str = (
    "-- intent: rolling 36-week demand curve, champion routing\n"
    "CREATE VIEW v_demand_curve AS SELECT id, qty FROM moves;\n"
)

WINDOW_FUNC_SQL: str = (
    "SELECT id, row_number() OVER (PARTITION BY categ ORDER BY ts) AS rn\n"
    "  FROM stock_move;\n"
)

# A multi-CTE WITH query whose CTEs are independently sizeable. Used with a
# deliberately tiny injected ``max_input_tokens`` to force the per-CTE sub-split.
MULTI_CTE_SQL: str = (
    "WITH\n"
    "  base AS (SELECT id, qty FROM stock_move WHERE qty > 0),\n"
    "  agg AS (SELECT id, sum(qty) AS total FROM base GROUP BY id),\n"
    "  ranked AS (\n"
    "    SELECT id, total, row_number() OVER (ORDER BY total DESC) AS rn FROM agg\n"
    "  )\n"
    "SELECT * FROM ranked WHERE rn <= 10;\n"
)

# A procedural ``DO $$ ... $$`` block containing MULTIPLE internal ``;``
# statements. The dollar-quoted body must be treated as one opaque statement:
# a naive ``str.split(';')`` would shred it into ~5 fragments. The two internal
# statements below are checked for verbatim presence in the single emitted
# chunk's source.
DO_BLOCK_INTERNAL_SEMICOLONS: str = (
    "DO $$\n"
    "BEGIN\n"
    "  RAISE NOTICE 'x';\n"
    "  IF 1 = 1 THEN\n"
    "    PERFORM 1;\n"
    "  END IF;\n"
    "END\n"
    "$$;\n"
)

# A file whose MIDDLE statement (``)))``) is unparseable. The good statements
# on either side must be the only chunks, and the skipped fragment must not
# consume a structural ordinal — so the surviving identities are stmt#1, stmt#2
# (contiguous), NOT stmt#1, stmt#3.
SKIP_UNPARSEABLE_MIDDLE: str = "SELECT 1; ))) ; SELECT 2;\n"


class TestHandles:
    """``handles`` claims ``.sql`` case-insensitively and nothing else."""

    def test_handles_sql_extension(self, chunker: SqlChunker) -> None:
        assert chunker.handles("validation/q.sql") is True

    def test_handles_is_case_insensitive(self, chunker: SqlChunker) -> None:
        assert chunker.handles("MIGRATION.SQL") is True

    def test_rejects_non_sql(self, chunker: SqlChunker) -> None:
        assert chunker.handles("models/account.py") is False
        assert chunker.handles("notes.md") is False


class TestOneChunkPerStatement:
    """Top-level statements map one-to-one onto chunks."""

    def test_each_statement_is_a_chunk(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        result = chunker.chunk(MANY_DDL, ctx)
        assert isinstance(result, list)
        assert all(isinstance(c, Chunk) for c in result)
        # Four DDL statements -> four chunks.
        assert len(result) == 4

    def test_chunk_type_is_sql_statement(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        result = chunker.chunk(LEADING_COMMENT_SQL, ctx)
        assert result[0].chunk_type == "sql_statement"

    def test_dialect_is_postgres(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        result = chunker.chunk(LEADING_COMMENT_SQL, ctx)
        assert result[0].metadata["dialect"] == "postgres"

    def test_empty_source_yields_no_chunks(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        assert chunker.chunk("   \n\n", ctx) == []


class TestAdversarialRobustness:
    """psql meta-commands + ``:'param'`` + a ``DO $$`` block must not crash."""

    def test_does_not_crash_and_yields_chunks(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        result = chunker.chunk(ADVERSARIAL_PSQL, ctx)
        # The pipeline survives and produces real chunks.
        assert len(result) >= 1

    def test_meta_command_lines_are_not_chunks(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        result = chunker.chunk(ADVERSARIAL_PSQL, ctx)
        # No chunk's source is a bare ``\set``/``\timing`` directive.
        for c in result:
            assert not c.source_text.lstrip().startswith("\\")

    def test_param_select_and_create_both_present(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        result = chunker.chunk(ADVERSARIAL_PSQL, ctx)
        types = {c.metadata["statement_type"] for c in result}
        # The ``SELECT :'target_date'`` and the ``CREATE TABLE`` both parse.
        assert "select" in types
        assert "create" in types

    def test_create_in_adversarial_file_has_created_object_identity(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        result = chunker.chunk(ADVERSARIAL_PSQL, ctx)
        created = {c.metadata["created_object"] for c in result}
        assert "demand_snapshot" in created

    def test_do_block_dollar_quote_kept_as_single_chunk(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        # A DO $$ ... $$ body holds MULTIPLE internal ';' statements. The whole
        # dollar-quoted block is one opaque statement: a naive str.split(';')
        # would shred it into ~5 fragments. Pin the integrity directly — exactly
        # one chunk, and BOTH internal statements present verbatim in its source.
        result = chunker.chunk(DO_BLOCK_INTERNAL_SEMICOLONS, ctx)
        assert len(result) == 1
        source_text = result[0].source_text
        assert "RAISE NOTICE 'x';" in source_text
        assert "END IF;" in source_text


class TestReferencedTablesSubtractsCtes:
    """A ``WITH RECURSIVE`` query reports base tables, not its CTE aliases."""

    def test_cte_name_is_recorded(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        result = chunker.chunk(WITH_RECURSIVE, ctx)
        assert "ancestors" in result[0].metadata["cte_names"]

    def test_referenced_tables_excludes_cte_name(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        result = chunker.chunk(WITH_RECURSIVE, ctx)
        referenced = set(result[0].metadata["referenced_tables"])
        # The CTE alias must be subtracted out...
        assert "ancestors" not in referenced
        # ...while the real base tables remain.
        assert "product_category" in referenced
        assert "product_template" in referenced

    def test_recursive_query_kept_whole(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        # Under the production cap the recursive query is a single chunk.
        result = chunker.chunk(WITH_RECURSIVE, ctx)
        assert len(result) == 1
        assert result[0].sub_ordinal == 0


class TestDistinctIdentities:
    """Many CREATEs get distinct identities from their created object."""

    def test_create_table_identities(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        result = chunker.chunk(MANY_DDL, ctx)
        identities = [c.identity for c in result]
        # All four are distinct and semantic (no two collapse).
        assert len(set(identities)) == 4

    def test_create_table_uses_table_name(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        result = chunker.chunk(MANY_DDL, ctx)
        assert result[0].identity == "demand_weekly"
        assert result[1].identity == "demand_monthly"

    def test_create_index_uses_index_name(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        result = chunker.chunk(MANY_DDL, ctx)
        # The created object for CREATE INDEX is the INDEX name, not its table.
        assert result[2].identity == "idx_demand_weekly_id"
        assert result[3].identity == "idx_demand_monthly_id"

    def test_non_ddl_uses_structural_ordinal(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        sql = "SELECT 1;\nSELECT 2;\n"
        result = chunker.chunk(sql, ctx)
        # No semantic name -> 1-based structural ordinal.
        assert result[0].identity == "stmt#1"
        assert result[1].identity == "stmt#2"

    def test_skipped_unparseable_statement_does_not_advance_ordinal(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        # The middle fragment ``)))`` is unparseable and must be dropped WITHOUT
        # consuming a structural ordinal. The surviving identities are therefore
        # contiguous (stmt#1, stmt#2) — NOT stmt#1, stmt#3, which would leak the
        # skipped fragment into the ordinal sequence.
        result = chunker.chunk(SKIP_UNPARSEABLE_MIDDLE, ctx)
        assert [c.identity for c in result] == ["stmt#1", "stmt#2"]


class TestLeadingComment:
    """The leading intent comment is captured into metadata."""

    def test_leading_comment_captured(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        result = chunker.chunk(LEADING_COMMENT_SQL, ctx)
        comment = result[0].metadata["leading_comment"]
        assert comment is not None
        assert "rolling 36-week demand curve" in comment

    def test_no_comment_is_none(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        result = chunker.chunk("SELECT 1;\n", ctx)
        assert result[0].metadata["leading_comment"] is None


class TestWindowFuncs:
    """``has_window_funcs`` reflects OVER(...) presence."""

    def test_window_func_detected(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        result = chunker.chunk(WINDOW_FUNC_SQL, ctx)
        assert result[0].metadata["has_window_funcs"] is True

    def test_no_window_func(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        result = chunker.chunk("SELECT id FROM stock_move;\n", ctx)
        assert result[0].metadata["has_window_funcs"] is False


class TestLineRange:
    """Each chunk reports the source lines it spans."""

    def test_line_range_metadata_and_fields_agree(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        result = chunker.chunk(LEADING_COMMENT_SQL, ctx)
        chunk = result[0]
        # The leading comment is on line 1, the CREATE VIEW on line 2.
        assert chunk.line_start == 1
        assert chunk.line_end == 2
        assert list(chunk.metadata["line_range"]) == [1, 2]


class TestCteSubSplit:
    """A WITH query over the token cap sub-splits per-CTE with sub_ordinal."""

    def test_whole_query_when_under_cap(
        self, chunker: SqlChunker, ctx: ChunkContext
    ) -> None:
        # Under the production cap the multi-CTE query stays whole.
        result = chunker.chunk(MULTI_CTE_SQL, ctx)
        assert len(result) == 1
        assert result[0].sub_ordinal == 0

    def test_sub_splits_when_over_injected_cap(
        self, chunker: SqlChunker, count_tokens: Callable[[str], int]
    ) -> None:
        # Inject a tiny cap so the multi-CTE query MUST sub-split.
        tiny_ctx = _make_ctx(count_tokens, max_input_tokens=20)
        result = chunker.chunk(MULTI_CTE_SQL, tiny_ctx)
        # Three CTEs -> at least the three CTE pieces (plus an optional body).
        assert len(result) >= 3

    def test_sub_split_pieces_carry_sub_ordinal(
        self, chunker: SqlChunker, count_tokens: Callable[[str], int]
    ) -> None:
        tiny_ctx = _make_ctx(count_tokens, max_input_tokens=20)
        result = chunker.chunk(MULTI_CTE_SQL, tiny_ctx)
        sub_ordinals = [c.sub_ordinal for c in result]
        # Sibling pieces are distinct and 1-based (not all zero).
        assert sub_ordinals == sorted(sub_ordinals)
        assert len(set(sub_ordinals)) == len(sub_ordinals)
        assert min(sub_ordinals) >= 1

    def test_sub_split_pieces_share_one_identity(
        self, chunker: SqlChunker, count_tokens: Callable[[str], int]
    ) -> None:
        tiny_ctx = _make_ctx(count_tokens, max_input_tokens=20)
        result = chunker.chunk(MULTI_CTE_SQL, tiny_ctx)
        # All siblings derive from the same parent statement -> one identity,
        # disambiguated only by sub_ordinal.
        assert len({c.identity for c in result}) == 1

    def test_sub_split_pieces_have_parent_summary_header(
        self, chunker: SqlChunker, count_tokens: Callable[[str], int]
    ) -> None:
        tiny_ctx = _make_ctx(count_tokens, max_input_tokens=20)
        result = chunker.chunk(MULTI_CTE_SQL, tiny_ctx)
        # The parent-summary header rides in embedding_text via metadata_header.
        for c in result:
            assert c.metadata_header != ""
            # Each CTE name appears in some piece's header context.
        headers = " ".join(c.metadata_header for c in result)
        for cte_name in ("base", "agg", "ranked"):
            assert cte_name in headers
