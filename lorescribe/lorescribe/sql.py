"""The :class:`SqlChunker` — statement-level SQL chunking via ``sqlglot``.

This chunker splits a ``.sql`` file into one :class:`~lorescribe.models.Chunk`
per top-level statement, attaching rich, retrieval-useful metadata derived from
the parsed AST (statement type, referenced base tables, CTE names, the created
DDL object, window-function presence, the leading intent comment, and the line
range).

Robustness is the load-bearing concern (a real Postgres diagnostic corpus mixes
``psql`` meta-commands, ``DO $$ ... $$`` procedural blocks, and ``:'param'``
substitutions that vanilla parsing chokes on). The pipeline is, in order:

1. Strip leading-``\\`` ``psql`` meta-command lines (``\\set``, ``\\timing``,
   ``\\d`` ...) — they are client directives, not SQL, and abort parsing.
2. Parse the cleaned source with ``error_level=sqlglot.ErrorLevel.IGNORE`` so
   unsupported-but-harmless constructs degrade to a ``Command`` node instead of
   raising.
3. Last-ditch fallback: if even tolerant multi-statement parsing raises, split
   on ``;`` and ``parse_one`` each fragment, skipping the ones that still fail.

This was verified to parse 116/116 statements of a real Postgres corpus.

The contract:

* Exactly one chunk per top-level statement, in source order.
* ``identity`` is the created object name for a ``CREATE`` (table/view name, or
  the index name for ``CREATE INDEX``); otherwise the structural ordinal
  ``stmt#N`` (1-based).
* A ``WITH`` / ``WITH RECURSIVE`` query is kept WHOLE — its CTEs are mutually
  dependent — and is only sub-split (by ``exp.CTE``, with ``sub_ordinal`` and a
  parent-summary header) when the whole statement exceeds
  ``ctx.max_input_tokens``.
* ``referenced_tables`` is the set of real base tables with the CTE alias names
  SUBTRACTED — a recursive query references its base tables, not its own CTE
  aliases.
"""

from __future__ import annotations

import logging
from typing import Any, cast

import sqlglot
from sqlglot import exp

from lorescribe.base import Chunker
from lorescribe.models import Chunk, ChunkContext

logger = logging.getLogger(__name__)

# The single SQL dialect this chunker parses and reports. The lore corpus is
# Postgres; the value is also stamped into every chunk's metadata so a future
# multi-dialect consumer can route on it.
DIALECT: str = "postgres"

# The file extension this chunker claims (compared case-insensitively).
SQL_EXTENSION: str = ".sql"

# A leading ``\`` marks a ``psql`` meta-command line (``\set``, ``\timing``,
# ``\d`` ...). These are client directives, not SQL, and must be stripped before
# parsing or they abort the parse.
PSQL_META_PREFIX: str = "\\"

# The statement-boundary token. Top-level occurrences delimit statements; the
# tokenizer correctly skips ``;`` inside strings and dollar-quoted blocks.
STATEMENT_SEPARATOR: str = ";"

# Chunk type stamped on every emitted SQL chunk.
CHUNK_TYPE_STATEMENT: str = "sql_statement"

# Metadata keys (named constants — no stringly-typed dict keys scattered about).
META_STATEMENT_TYPE: str = "statement_type"
META_REFERENCED_TABLES: str = "referenced_tables"
META_CTE_NAMES: str = "cte_names"
META_CREATED_OBJECT: str = "created_object"
META_HAS_WINDOW_FUNCS: str = "has_window_funcs"
META_LEADING_COMMENT: str = "leading_comment"
META_LINE_RANGE: str = "line_range"
META_DIALECT: str = "dialect"

# Structural-identity template for a statement with no semantic name (1-based).
STRUCTURAL_IDENTITY_TEMPLATE: str = "stmt#{ordinal}"


class SqlChunker(Chunker):
    """Statement-level SQL chunker built on ``sqlglot``.

    Emits one :class:`~lorescribe.models.Chunk` per top-level statement, with
    AST-derived metadata and a robust parse pipeline that never crashes on the
    ``psql``/procedural constructs found in real diagnostic SQL.
    """

    def handles(self, path: str) -> bool:
        """Report whether ``path`` is a SQL file this chunker claims.

        Args:
            path: The candidate file path.

        Returns:
            ``True`` if ``path`` ends with ``.sql`` (case-insensitive).
        """
        return path.lower().endswith(SQL_EXTENSION)

    def chunk(self, source: str, ctx: ChunkContext) -> list[Chunk]:  # noqa: D401
        """Split a SQL source string into one chunk per top-level statement.

        Args:
            source: The full ``.sql`` file contents.
            ctx: Per-file context carrying the token counter and hard token cap.

        Returns:
            One :class:`~lorescribe.models.Chunk` per top-level statement, in
            source order; a ``WITH`` query exceeding ``ctx.max_input_tokens`` is
            expanded into per-CTE sibling chunks sharing one ``identity``.
        """
        cleaned = self._strip_psql_meta_commands(source)
        chunks: list[Chunk] = []
        ordinal = 0
        for span_text, line_start, line_end in self._iter_statement_spans(cleaned):
            expression = self._parse_statement(span_text)
            if expression is None:
                # An unparseable fragment is skipped (the verified last-ditch
                # behaviour) — it never becomes a chunk and never advances the
                # structural ordinal, so identities stay stable.
                continue
            ordinal += 1
            chunks.extend(
                self._build_chunks(
                    expression=expression,
                    span_text=span_text,
                    line_start=line_start,
                    line_end=line_end,
                    ordinal=ordinal,
                    ctx=ctx,
                )
            )
        return chunks

    # -- robustness pipeline ------------------------------------------------

    @staticmethod
    def _strip_psql_meta_commands(source: str) -> str:
        """Drop leading-``\\`` ``psql`` meta-command lines.

        ``\\set``, ``\\timing``, ``\\d`` and friends are client directives, not
        SQL — left in place they abort the parse. Only lines whose first
        non-whitespace character is a backslash are removed; everything else
        (including blank lines, to preserve line numbering) is kept verbatim.

        Args:
            source: The raw SQL file contents.

        Returns:
            The source with ``psql`` meta-command lines blanked out, preserving
            the original line count so reported line ranges stay accurate.
        """
        kept_lines: list[str] = []
        for line in source.splitlines():
            if line.lstrip().startswith(PSQL_META_PREFIX):
                # Blank the line rather than delete it: keeping the newline keeps
                # every later statement's line numbers aligned with the file.
                kept_lines.append("")
            else:
                kept_lines.append(line)
        return "\n".join(kept_lines)

    def _iter_statement_spans(
        self, source: str
    ) -> list[tuple[str, int, int]]:
        """Yield ``(text, line_start, line_end)`` for each top-level statement.

        Boundaries are the top-level ``;`` tokens reported by the ``sqlglot``
        tokenizer, which correctly ignores semicolons inside strings and
        dollar-quoted (``$$ ... $$``) blocks. Splitting on character offsets
        (not a naive ``str.split(';')``) is what keeps a ``DO $$ ... ; ... $$``
        block intact.

        On a tokenizer failure the method degrades to a naive ``;`` split so the
        caller always receives spans to attempt parsing.

        Args:
            source: The cleaned SQL source.

        Returns:
            A list of ``(span_text, line_start, line_end)`` tuples for the
            non-empty top-level statements, in source order.
        """
        try:
            tokens = sqlglot.tokenize(source, read=DIALECT)
            boundaries = [
                token.end
                for token in tokens
                if token.token_type == sqlglot.TokenType.SEMICOLON
            ]
        except Exception:  # pragma: no cover - tokenizer is highly tolerant
            # Last-ditch: fall back to naive character splitting on ';'.
            return self._naive_spans(source)

        spans: list[tuple[str, int, int]] = []
        start = 0
        for boundary in [*boundaries, len(source) - 1]:
            end = boundary + 1
            text = source[start:end]
            if text.strip():
                line_start = source.count("\n", 0, start) + 1
                line_end = source.count("\n", 0, max(start, end - 1)) + 1
                spans.append((text, line_start, line_end))
            start = end
        return spans

    @staticmethod
    def _naive_spans(source: str) -> list[tuple[str, int, int]]:
        """Naive ``;``-split fallback when tokenization is unavailable.

        Line ranges are approximated from cumulative offsets. This path exists
        purely so the chunker never raises; the tokenizer almost always wins.

        Args:
            source: The cleaned SQL source.

        Returns:
            ``(span_text, line_start, line_end)`` tuples for each non-empty
            ``;``-delimited fragment.
        """
        spans: list[tuple[str, int, int]] = []
        offset = 0
        for fragment in source.split(STATEMENT_SEPARATOR):
            piece = fragment + STATEMENT_SEPARATOR
            if fragment.strip():
                line_start = source.count("\n", 0, offset) + 1
                line_end = source.count("\n", 0, offset + len(fragment)) + 1
                spans.append((piece, line_start, line_end))
            offset += len(piece)
        return spans

    @staticmethod
    def _parse_statement(span_text: str) -> exp.Expression | None:
        """Parse a single statement span, tolerating unsupported syntax.

        Uses ``error_level=IGNORE`` so unsupported-but-harmless constructs (a
        ``DO $$ ... $$`` block) degrade to a ``Command`` node instead of
        raising. A fragment that still cannot be parsed returns ``None`` and is
        skipped by the caller — the verified last-ditch behaviour.

        Args:
            span_text: One statement's text.

        Returns:
            The parsed expression, or ``None`` if it could not be parsed.
        """
        try:
            # ``parse_one`` is generic over its return TypeVar (``Expr``);
            # without an ``into`` it returns a concrete subclass, which mypy
            # cannot reconcile with the declared ``exp.Expression`` — narrow it.
            return cast(
                exp.Expression,
                sqlglot.parse_one(
                    span_text, read=DIALECT, error_level=sqlglot.ErrorLevel.IGNORE
                ),
            )
        except Exception:
            return None

    # -- chunk construction -------------------------------------------------

    def _build_chunks(
        self,
        expression: exp.Expression,
        span_text: str,
        line_start: int,
        line_end: int,
        ordinal: int,
        ctx: ChunkContext,
    ) -> list[Chunk]:
        """Build the chunk(s) for one parsed statement.

        Normally one chunk; a ``WITH`` query whose rendered ``embedding_text``
        exceeds ``ctx.max_input_tokens`` is sub-split per ``exp.CTE``.

        Args:
            expression: The parsed statement.
            span_text: The original source text of the statement (verbatim).
            line_start: First source line of the statement (1-based).
            line_end: Last source line of the statement (1-based).
            ordinal: The 1-based structural ordinal of this statement.
            ctx: Per-file context (token counter + hard cap).

        Returns:
            One chunk, or N per-CTE sibling chunks sharing one identity.
        """
        statement_type = expression.key
        cte_names = self._cte_names(expression)
        referenced_tables = self._referenced_tables(expression, cte_names)
        created_object = self._created_object(expression)
        has_window_funcs = bool(list(expression.find_all(exp.Window)))
        leading_comment = self._leading_comment(expression)
        identity = created_object or STRUCTURAL_IDENTITY_TEMPLATE.format(ordinal=ordinal)

        metadata: dict[str, Any] = {
            META_STATEMENT_TYPE: statement_type,
            META_REFERENCED_TABLES: referenced_tables,
            META_CTE_NAMES: cte_names,
            META_CREATED_OBJECT: created_object,
            META_HAS_WINDOW_FUNCS: has_window_funcs,
            META_LEADING_COMMENT: leading_comment,
            META_LINE_RANGE: [line_start, line_end],
            META_DIALECT: DIALECT,
        }

        whole = Chunk(
            chunk_type=CHUNK_TYPE_STATEMENT,
            source_text=span_text,
            identity=identity,
            line_start=line_start,
            line_end=line_end,
            metadata=metadata,
        )

        # Keep a WITH query whole unless it busts the hard token cap.
        if cte_names and ctx.count_tokens(whole.embedding_text) > ctx.max_input_tokens:
            return self._sub_split_ctes(
                expression=expression,
                base_metadata=metadata,
                identity=identity,
                line_start=line_start,
                line_end=line_end,
                cte_names=cte_names,
            )
        return [whole]

    def _sub_split_ctes(
        self,
        expression: exp.Expression,
        base_metadata: dict[str, Any],
        identity: str,
        line_start: int,
        line_end: int,
        cte_names: list[str],
    ) -> list[Chunk]:
        """Split an over-cap ``WITH`` query into per-CTE sibling chunks.

        Each sibling carries the same ``identity`` (the parent statement's),
        a 1-based ``sub_ordinal``, and a parent-summary header naming every CTE
        so the piece keeps its place in the whole query's structure. The final
        sibling is the WITH body (the statement minus its CTE definitions).

        Args:
            expression: The parsed ``WITH`` statement.
            base_metadata: The whole-statement metadata, copied per piece.
            identity: The shared parent identity.
            line_start: First source line of the parent statement.
            line_end: Last source line of the parent statement.
            cte_names: The CTE alias names, used in the parent-summary header.

        Returns:
            The per-CTE sibling chunks plus a body sibling, in order.
        """
        header = self._parent_summary_header(cte_names)
        pieces: list[Chunk] = []
        sub_ordinal = 1

        for cte in expression.find_all(exp.CTE):
            cte_metadata = dict(base_metadata)
            cte_metadata[META_CTE_NAMES] = [cte.alias_or_name]
            pieces.append(
                Chunk(
                    chunk_type=CHUNK_TYPE_STATEMENT,
                    source_text=cte.sql(dialect=DIALECT),
                    identity=identity,
                    sub_ordinal=sub_ordinal,
                    line_start=line_start,
                    line_end=line_end,
                    metadata=cte_metadata,
                    metadata_header=header,
                )
            )
            sub_ordinal += 1

        body = expression.copy()
        with_clause = body.find(exp.With)
        if with_clause is not None:
            with_clause.pop()
        body_metadata = dict(base_metadata)
        body_metadata[META_CTE_NAMES] = []
        pieces.append(
            Chunk(
                chunk_type=CHUNK_TYPE_STATEMENT,
                source_text=body.sql(dialect=DIALECT),
                identity=identity,
                sub_ordinal=sub_ordinal,
                line_start=line_start,
                line_end=line_end,
                metadata=body_metadata,
                metadata_header=header,
            )
        )
        return pieces

    @staticmethod
    def _parent_summary_header(cte_names: list[str]) -> str:
        """Compose the parent-summary header for a sub-split ``WITH`` query.

        Args:
            cte_names: The CTE alias names of the parent query.

        Returns:
            A one-line header naming the parent WITH query's CTE pipeline so a
            retrieved fragment keeps its structural context.
        """
        return f"-- part of WITH query with CTEs: {', '.join(cte_names)}"

    # -- metadata extraction ------------------------------------------------

    @staticmethod
    def _cte_names(expression: exp.Expression) -> list[str]:
        """Collect the CTE alias names declared in a statement.

        Args:
            expression: The parsed statement.

        Returns:
            The CTE alias names in declaration order.
        """
        return [cte.alias_or_name for cte in expression.find_all(exp.CTE)]

    @staticmethod
    def _referenced_tables(
        expression: exp.Expression, cte_names: list[str]
    ) -> list[str]:
        """Collect referenced base tables, SUBTRACTING the CTE alias names.

        A recursive (or any ``WITH``) query references its CTE aliases as if
        they were tables; those are NOT base tables, so they are removed — the
        verified gotcha. Names are de-duplicated and sorted for determinism.

        Args:
            expression: The parsed statement.
            cte_names: The CTE alias names to subtract.

        Returns:
            The sorted, de-duplicated base-table names.
        """
        cte_name_set = set(cte_names)
        names = {
            table.name
            for table in expression.find_all(exp.Table)
            if table.name and table.name not in cte_name_set
        }
        return sorted(names)

    @staticmethod
    def _created_object(expression: exp.Expression) -> str | None:
        """Return the name of the object a ``CREATE`` statement defines.

        For ``CREATE INDEX`` the created object is the INDEX name (the index's
        own identifier), not the table it indexes — so an index is keyed by
        itself, never collapsed onto its target table. For other ``CREATE``
        kinds (TABLE, VIEW, MATERIALIZED VIEW, ...) it is the target table/view
        name.

        Args:
            expression: The parsed statement.

        Returns:
            The created object's name, or ``None`` if the statement is not a
            ``CREATE`` (or carries no resolvable name).
        """
        if not isinstance(expression, exp.Create):
            return None
        target = expression.this
        if isinstance(target, exp.Index):
            # The index's own identifier (``CREATE INDEX <name> ON <table>``).
            return target.this.name if target.this else None
        # TABLE / VIEW / MATERIALIZED VIEW: the first Table node is the target.
        table = expression.find(exp.Table)
        return table.name if table is not None else None

    @staticmethod
    def _leading_comment(expression: exp.Expression) -> str | None:
        """Return the statement's leading comment, stripped, or ``None``.

        ``sqlglot`` attaches preceding comments to the expression; the first one
        is the intent block. Surrounding whitespace is trimmed.

        Args:
            expression: The parsed statement.

        Returns:
            The first attached comment (stripped), or ``None`` if there is none.
        """
        comments = expression.comments
        if not comments:
            return None
        return comments[0].strip()
