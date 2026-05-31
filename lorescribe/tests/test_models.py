"""Contract tests for ``lorescribe.models``.

These pin the data shapes that every concrete chunker must emit and that the
downstream consumer (loremaster) relies on. The load-bearing guarantees:

* Every :class:`Chunk` carries a **non-empty** ``identity`` and a
  ``sub_ordinal``. loremaster derives a *deterministic* point-ID/chunk-key
  from ``(slug, file_path, chunk_type, identity, sub_ordinal, key_version)``;
  if ``identity`` were ever empty or two sibling chunks shared the same
  ``(identity, sub_ordinal)``, their keys would collide and one chunk would
  silently overwrite the other in the vector store. The model layer is the
  place that promise is enforced.

* ``embedding_text`` is the exact string handed to the embedder. The header
  seam (``metadata_header`` present vs. absent) must produce *exactly* the
  documented string — a stray leading newline or a dropped header corrupts
  retrieval context for every chunk, so it is pinned to the byte.
"""

from __future__ import annotations

from typing import Any

import pytest
from lorescribe.models import Chunk, ChunkContext, ProfileResult
from pydantic import ValidationError

from .conftest import (
    SAMPLE_FILE_PATH,
    SAMPLE_SLUG,
    VOYAGE4_MAX_INPUT_TOKENS,
    approx_token_count,
)

# A representative chunk of real-world handbook prose (Markdown source), the
# kind of text a chunker actually splits out of a document.
SAMPLE_SOURCE_TEXT: str = (
    "Overtime is paid at 1.5x the regular rate for hours worked beyond 40 in "
    "a workweek. The workweek begins Sunday at 00:00 and ends Saturday at 23:59."
)
# A metadata header is the breadcrumb trail a chunker prepends so the embedder
# has document context (heading path, section). Realistic, human-readable.
SAMPLE_METADATA_HEADER: str = "Employee Handbook > Compensation > Overtime"

# Identity is the within-file natural key the chunker assigns (e.g. a heading
# slug, a function qualname, a table name) — never empty in production.
SAMPLE_IDENTITY: str = "compensation/overtime"


def _make_chunk(**overrides: Any) -> Chunk:
    """Build a valid :class:`Chunk`, overriding fields per-test.

    Centralises the realistic baseline so each test states only the one field
    whose contract it is exercising.
    """
    base: dict[str, Any] = {
        "chunk_type": "markdown_section",
        "source_text": SAMPLE_SOURCE_TEXT,
        "identity": SAMPLE_IDENTITY,
        "line_start": 12,
        "line_end": 14,
    }
    base.update(overrides)
    return Chunk(**base)


class TestChunkIdentityRequiredAndNonEmpty:
    """``Chunk.identity`` is required and must reject the empty string.

    A weak implementation that defaults ``identity`` to ``""`` or marks it
    ``Optional`` would silently let sibling chunks share a blank natural key,
    collapsing their downstream point-IDs. These tests fail such an impl.
    """

    def test_chunk_construction_succeeds_with_nonempty_identity(self) -> None:
        # Arrange / Act
        chunk = _make_chunk(identity=SAMPLE_IDENTITY)
        # Assert
        assert chunk.identity == SAMPLE_IDENTITY

    def test_missing_identity_raises_validation_error(self) -> None:
        # Arrange: every required field EXCEPT identity.
        payload: dict[str, Any] = {
            "chunk_type": "markdown_section",
            "source_text": SAMPLE_SOURCE_TEXT,
            "line_start": 12,
            "line_end": 14,
        }
        # Act / Assert: identity has no default, so omission is a hard error.
        with pytest.raises(ValidationError):
            Chunk(**payload)

    def test_empty_string_identity_is_rejected(self) -> None:
        # Act / Assert: an explicit empty string must fail validation — it is
        # the exact value a lazy default would inject.
        with pytest.raises(ValidationError):
            _make_chunk(identity="")

    def test_whitespace_only_identity_is_rejected(self) -> None:
        # Act / Assert: a single space is "non-empty" by len() but is not a
        # usable natural key; it must be rejected like the empty string.
        with pytest.raises(ValidationError):
            _make_chunk(identity="   ")

    def test_surrounding_whitespace_in_identity_is_stripped(self) -> None:
        # Arrange: a chunker (or upstream config) hands an otherwise-valid
        # natural key with stray surrounding whitespace — the kind of thing a
        # trailing newline in a heading slug or an indented YAML scalar yields.
        padded_identity = f"  {SAMPLE_IDENTITY}  "
        # Act: construction must SUCCEED (the value is a real key) and STORE the
        # normalised form.
        chunk = _make_chunk(identity=padded_identity)
        # Assert: independent expected value — the requirement is that
        # "  payroll  " and "payroll" must derive the SAME deterministic
        # point-ID, so the stored identity must equal the trimmed key, byte for
        # byte. A validator that merely rejects all-whitespace but PRESERVES
        # surrounding whitespace on valid values (the current permissive
        # behaviour) returns the padded string here and fails this assertion.
        assert chunk.identity == SAMPLE_IDENTITY


class TestChunkRejectsUnknownFields:
    """``Chunk``, ``ChunkContext`` and ``ProfileResult`` reject unknown kwargs.

    A typo'd field name (``metadata_headr=``, ``bogus=``) that silently
    vanishes is the worst kind of bug here: the model still constructs, the
    intended value is dropped, and a deterministic point-ID is derived from
    partial data with no error at all. The contract is ``extra="forbid"`` — an
    unknown kwarg raises :class:`pydantic.ValidationError`. Pydantic's
    *default* (``extra="ignore"``) accepts and drops the bogus field, which
    these tests forbid.
    """

    def test_chunk_rejects_unknown_keyword_argument(self) -> None:
        # Arrange: every required Chunk field plus one bogus extra. ``bogus``
        # stands in for a real-world typo of a field that feeds point-ID
        # derivation.
        payload: dict[str, Any] = {
            "chunk_type": "markdown_section",
            "source_text": SAMPLE_SOURCE_TEXT,
            "identity": SAMPLE_IDENTITY,
            "line_start": 12,
            "line_end": 14,
            "bogus": 1,
        }
        # Act / Assert: the unknown ``bogus`` kwarg must fail loud, not be
        # silently ignored. A model left on pydantic's default extra="ignore"
        # constructs successfully here and fails this test.
        with pytest.raises(ValidationError):
            Chunk(**payload)

    def test_chunk_rejects_misspelled_real_field(self) -> None:
        # Arrange: the canonical hazard — ``metadata_headr`` instead of
        # ``metadata_header``. With extra="ignore" the breadcrumb silently never
        # gets set and embedding_text loses its context with zero signal.
        payload: dict[str, Any] = {
            "chunk_type": "markdown_section",
            "source_text": SAMPLE_SOURCE_TEXT,
            "identity": SAMPLE_IDENTITY,
            "line_start": 12,
            "line_end": 14,
            "metadata_headr": SAMPLE_METADATA_HEADER,  # typo of metadata_header
        }
        # Act / Assert
        with pytest.raises(ValidationError):
            Chunk(**payload)

    def test_chunk_context_rejects_unknown_keyword_argument(self) -> None:
        # Act / Assert: the same forbid-extra contract on the per-file context.
        # Splat a dict (matching the Chunk negative test) so the deliberately
        # invalid ``bogus`` kwarg is supplied dynamically — the runtime
        # ValidationError is what we assert; the static pydantic plugin must not
        # short-circuit our intentional bad input.
        payload: dict[str, Any] = {
            "slug": SAMPLE_SLUG,
            "file_path": SAMPLE_FILE_PATH,
            "count_tokens": approx_token_count,
            "max_input_tokens": VOYAGE4_MAX_INPUT_TOKENS,
            "bogus": 1,
        }
        with pytest.raises(ValidationError):
            ChunkContext(**payload)

    def test_profile_result_rejects_unknown_keyword_argument(self) -> None:
        # Act / Assert: and on the XML profile hook's return shape.
        payload: dict[str, Any] = {
            "chunk_type": "xml_element",
            "extra_metadata": {"schema": "docbook"},
            "bogus": 1,
        }
        with pytest.raises(ValidationError):
            ProfileResult(**payload)


class TestChunkEmbeddingTextSeam:
    """``embedding_text`` composes ``metadata_header`` and ``source_text`` exactly.

    This is the seam where chunk data crosses into the embedder. The composed
    string must match the spec to the byte: header present -> ``"<h>\\n<s>"``;
    header absent -> ``"<s>"`` with NO leading newline.
    """

    def test_embedding_text_prepends_header_with_single_newline(self) -> None:
        # Arrange
        chunk = _make_chunk(metadata_header=SAMPLE_METADATA_HEADER)
        # Assert: independent expected value — hand-composed from the spec,
        # not read back from the implementation.
        expected = f"{SAMPLE_METADATA_HEADER}\n{SAMPLE_SOURCE_TEXT}"
        assert chunk.embedding_text == expected

    def test_embedding_text_is_bare_source_when_header_empty(self) -> None:
        # Arrange: default metadata_header is "".
        chunk = _make_chunk()
        # Assert: exactly the source text — NO leading "\n". An impl that
        # always prepends a newline fails here.
        assert chunk.embedding_text == SAMPLE_SOURCE_TEXT

    def test_embedding_text_has_no_leading_newline_when_header_empty(self) -> None:
        # Arrange
        chunk = _make_chunk(metadata_header="")
        # Assert: explicit guard against the "always prepend \n" bug class.
        assert not chunk.embedding_text.startswith("\n")

    def test_embedding_text_separator_is_exactly_one_newline(self) -> None:
        # Arrange
        chunk = _make_chunk(metadata_header=SAMPLE_METADATA_HEADER)
        # Assert: exactly one '\n' joins header and source (header & source
        # here contain none), guarding double-newline / wrong-separator bugs.
        assert chunk.embedding_text.count("\n") == 1


class TestChunkSiblingDistinctness:
    """Two chunks identical except ``sub_ordinal`` are distinct; default is 0.

    ``sub_ordinal`` is what keeps sibling chunks (same heading split into N
    pieces) from collapsing to one point-ID downstream.
    """

    def test_sub_ordinal_defaults_to_zero(self) -> None:
        # Arrange / Act
        chunk = _make_chunk()
        # Assert
        assert chunk.sub_ordinal == 0

    def test_siblings_differing_only_in_sub_ordinal_are_distinct(self) -> None:
        # Arrange: same identity, same everything, different sub_ordinal —
        # the canonical "one heading, two splits" case.
        first = _make_chunk(sub_ordinal=0)
        second = _make_chunk(sub_ordinal=1)
        # Assert: both representable and not equal — they must not collapse.
        assert first != second
        assert (first.identity, first.sub_ordinal) != (second.identity, second.sub_ordinal)


class TestChunkFieldDefaultsAndShapes:
    """Default values and return types of the non-identity fields."""

    def test_metadata_defaults_to_empty_dict(self) -> None:
        chunk = _make_chunk()
        assert chunk.metadata == {}

    def test_metadata_header_defaults_to_empty_string(self) -> None:
        chunk = _make_chunk()
        assert chunk.metadata_header == ""

    def test_default_metadata_is_not_shared_between_instances(self) -> None:
        # Guard the classic mutable-default aliasing bug: mutating one chunk's
        # metadata must not leak into a sibling's.
        first = _make_chunk()
        second = _make_chunk()
        first.metadata["edited"] = True
        assert second.metadata == {}

    def test_metadata_round_trips_arbitrary_values(self) -> None:
        # Arrange: realistic metadata a chunker attaches (heading path, lang).
        metadata: dict[str, Any] = {
            "heading_path": ["Compensation", "Overtime"],
            "language": "en",
            "table_of_origin": None,
        }
        # Act
        chunk = _make_chunk(metadata=metadata)
        # Assert
        assert chunk.metadata == metadata

    def test_line_span_is_preserved(self) -> None:
        # line_start/line_end let loremaster cite source location; pure passthrough.
        chunk = _make_chunk(line_start=12, line_end=14)
        assert (chunk.line_start, chunk.line_end) == (12, 14)


class TestChunkContext:
    """``ChunkContext`` carries the slug, file path, token-counter, and cap.

    The token counter is a *real injected callable* (from the embedder side),
    and ``max_input_tokens`` is the embedder's hard cap. The seam tested here
    is "the context holds a callable that actually computes a count".
    """

    def test_holds_slug_and_file_path(self) -> None:
        ctx = ChunkContext(
            slug=SAMPLE_SLUG,
            file_path=SAMPLE_FILE_PATH,
            count_tokens=approx_token_count,
            max_input_tokens=VOYAGE4_MAX_INPUT_TOKENS,
        )
        assert ctx.slug == SAMPLE_SLUG
        assert ctx.file_path == SAMPLE_FILE_PATH

    def test_count_tokens_is_a_real_callable(self) -> None:
        # Arrange
        ctx = ChunkContext(
            slug=SAMPLE_SLUG,
            file_path=SAMPLE_FILE_PATH,
            count_tokens=approx_token_count,
            max_input_tokens=VOYAGE4_MAX_INPUT_TOKENS,
        )
        # Act: invoke through the stored callable on real prose.
        token_count = ctx.count_tokens(SAMPLE_SOURCE_TEXT)
        # Assert: it returns the SAME thing the injected counter would — proves
        # the context stored the genuine callable, not a sentinel/None.
        assert token_count == approx_token_count(SAMPLE_SOURCE_TEXT)

    def test_max_input_tokens_carries_the_embedder_cap(self) -> None:
        # The cap must survive as the consumer set it; chunkers gate on it.
        ctx = ChunkContext(
            slug=SAMPLE_SLUG,
            file_path=SAMPLE_FILE_PATH,
            count_tokens=approx_token_count,
            max_input_tokens=VOYAGE4_MAX_INPUT_TOKENS,
        )
        assert ctx.max_input_tokens == VOYAGE4_MAX_INPUT_TOKENS


class TestProfileResult:
    """``ProfileResult`` is the XML SchemaProfile hook's return shape."""

    def test_carries_chunk_type_and_extra_metadata(self) -> None:
        extra: dict[str, Any] = {"schema": "docbook", "root": "article"}
        result = ProfileResult(chunk_type="xml_element", extra_metadata=extra)
        assert result.chunk_type == "xml_element"
        assert result.extra_metadata == extra

    def test_skip_defaults_to_false(self) -> None:
        result = ProfileResult(chunk_type="xml_element", extra_metadata={})
        assert result.skip is False

    def test_skip_can_be_set_true(self) -> None:
        # A profile may decide a document should be skipped entirely.
        result = ProfileResult(chunk_type="xml_element", extra_metadata={}, skip=True)
        assert result.skip is True

    def test_force_own_chunk_defaults_to_false(self) -> None:
        # A profile that does not opt in must NOT alter the size-tiered default:
        # the granularity control is off unless explicitly requested.
        result = ProfileResult(chunk_type="xml_element", extra_metadata={})
        assert result.force_own_chunk is False

    def test_force_own_chunk_can_be_set_true(self) -> None:
        # The new granularity control: a profile can demand a claimed element be
        # emitted as its OWN chunk regardless of the size-tier decision.
        result = ProfileResult(
            chunk_type="threshold_map", extra_metadata={}, force_own_chunk=True
        )
        assert result.force_own_chunk is True
