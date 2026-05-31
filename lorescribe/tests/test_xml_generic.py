"""Contract tests for ``lorescribe.xml_generic.XmlChunker`` + the ``SchemaProfile`` hook.

``XmlChunker`` is the generic, namespace-aware XML chunker. It parses with
``defusedxml`` (XXE/entity-bomb safe), and is **size-tiered**: a small file
collapses to one whole-file chunk; a larger file splits into one chunk per
top-level child, recursing into oversized subtrees with a ``tag_path`` header.
Every emitted :class:`~lorescribe.models.Chunk` carries the generic XML metadata
block and a per-record identity (``id_attr or tag_path``) so sibling records of
the same tag never collapse to one downstream point-ID (the Chunk Identity
Contract — the generalization of odoo-code's ``build_chunk_key`` bug).

A pluggable ``SchemaProfile`` rides on top: a per-element callable
``__call__(element, ctx) -> ProfileResult | None``. The chunker consults each
registered profile; the first non-``None`` result wins — its ``chunk_type`` and
``extra_metadata`` merge over the generic defaults, and ``skip=True`` drops the
element entirely.

The load-bearing guarantees pinned here:

* **Security:** ``defusedxml`` *raises* on a billion-laughs entity-expansion
  bomb (it never silently expands it) while a benign document parses normally.
* **Identity distinctness:** two sibling elements of the SAME tag with different
  ``id`` attributes get DISTINCT identities — never collapsed.
* **Profile hook:** a registered profile that fires on a tag stamps a custom
  ``chunk_type`` and merges ``extra_metadata``; a profile returning ``skip``
  drops the element.
* **Namespaces:** Clark-notation ``{uri}tag`` is split into a bare localname
  plus a ``namespaces`` URI map.
* **Size tiers + token cap:** small file → one whole-file chunk; large file →
  per-child chunks; and every emitted chunk stays ``<= ctx.max_input_tokens``.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from lorescribe.base import Chunker
from lorescribe.models import Chunk, ChunkContext, ProfileResult

from .conftest import (
    SAMPLE_SLUG,
    VOYAGE4_MAX_INPUT_TOKENS,
    approx_token_count,
)

XML_FILE_PATH: str = "data/catalog.xml"

# A real, generic multi-element XML document on disk (owner directive: real
# corpus, not synthetic). ImageMagick's threshold-map file is a small document
# (~3K tokens, well under the cap) whose root carries 19 repeated ``<threshold>``
# sibling elements — exactly the shape that, by the size-tier default, collapses
# to ONE whole-file chunk. It is generic (no Odoo content) and stable on this
# host. Skipped cleanly if the package is ever run where it is absent.
REAL_GENERIC_XML_PATH: Path = Path("/etc/ImageMagick-7/thresholds.xml")


def _make_ctx(
    *,
    count_tokens: Callable[[str], int] = approx_token_count,
    max_input_tokens: int = VOYAGE4_MAX_INPUT_TOKENS,
    file_path: str = XML_FILE_PATH,
) -> ChunkContext:
    """Build a ``ChunkContext`` for the XML chunker, overriding fields per-test."""
    return ChunkContext(
        slug=SAMPLE_SLUG,
        file_path=file_path,
        count_tokens=count_tokens,
        max_input_tokens=max_input_tokens,
    )


# A compact, benign document with three same-tag siblings carrying distinct ids.
# Small enough that, under the production token cap, it is a single whole-file
# chunk — used for the security + small-file tiers.
BENIGN_XML: str = (
    "<catalog>\n"
    '  <book id="bk101"><title>TDD</title></book>\n'
    '  <book id="bk102"><title>Refactoring</title></book>\n'
    '  <book id="bk103"><title>Clean Code</title></book>\n'
    "</catalog>\n"
)

# The classic "billion laughs" XML entity-expansion bomb. A naive parser expands
# &lol9; into ~10^9 "lol" strings and exhausts memory; ``defusedxml`` must REFUSE
# to expand it and raise instead. We keep the document otherwise well-formed so
# the only thing under test is the entity-bomb defense, not a parse error.
BILLION_LAUGHS_XML: str = (
    '<?xml version="1.0"?>\n'
    "<!DOCTYPE lolz [\n"
    '  <!ENTITY lol "lol">\n'
    '  <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">\n'
    '  <!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">\n'
    '  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">\n'
    '  <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">\n'
    '  <!ENTITY lol5 "&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;">\n'
    '  <!ENTITY lol6 "&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;">\n'
    '  <!ENTITY lol7 "&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;">\n'
    '  <!ENTITY lol8 "&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;">\n'
    '  <!ENTITY lol9 "&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;">\n'
    "]>\n"
    "<lolz>&lol9;</lolz>\n"
)

# An XXE (XML eXternal Entity) attack: a SYSTEM entity pointing at a local file.
# A naive parser resolves ``&xxe;`` by READING ``/etc/passwd`` (file disclosure)
# or fetching a URL (SSRF). ``defusedxml`` must refuse the external reference and
# raise, never read the file. ``/etc/passwd`` is the canonical probe target.
XXE_EXTERNAL_ENTITY_XML: str = (
    '<?xml version="1.0"?>\n'
    '<!DOCTYPE root [\n'
    '  <!ENTITY xxe SYSTEM "file:///etc/passwd">\n'
    "]>\n"
    "<root>&xxe;</root>\n"
)


def _make_deeply_nested_xml(*, depth: int) -> str:
    """Build a single-chain document nested ``depth`` levels deep.

    The result is tiny (a few bytes per level) yet ``depth`` levels of nesting:
    ``<n><n>...x...</n></n>``. At ~1000+ levels this is well UNDER the embedder's
    token cap (so the chunker attempts no size-driven split), but naively
    serializing or recursively walking it exhausts the Python call stack —
    exactly the recursion-DoS this guards against.
    """
    return ("<n>" * depth) + "x" + ("</n>" * depth)


def _make_large_catalog(*, n_books: int, body_chars: int) -> str:
    """Build a catalog whose total size forces per-child splitting.

    Each ``<book>`` carries a distinct ``id`` and a body of ``body_chars``
    characters so the whole-file token count exceeds the cap and the chunker is
    forced down to per-top-level-child granularity. The bodies are plain text
    (no markup) so the size is predictable.
    """
    books = "".join(
        f'  <book id="bk{index:03d}"><body>{"x" * body_chars}</body></book>\n'
        for index in range(n_books)
    )
    return f"<catalog>\n{books}</catalog>\n"


class TestHandles:
    """``handles`` claims ``.xml`` (case-insensitively) and nothing else."""

    def setup_method(self) -> None:
        from lorescribe.xml_generic import XmlChunker

        self.chunker = XmlChunker()

    def test_is_a_chunker(self) -> None:
        assert isinstance(self.chunker, Chunker)

    def test_claims_xml_extension(self) -> None:
        assert self.chunker.handles("data/catalog.xml") is True

    def test_claims_uppercase_xml_extension(self) -> None:
        # Case-insensitive: a config that names ``.XML`` must still route here.
        assert self.chunker.handles("data/CATALOG.XML") is True

    def test_rejects_non_xml_extension(self) -> None:
        assert self.chunker.handles("data/notes.md") is False
        assert self.chunker.handles("data/schema.sql") is False


class TestDefusedXmlBlocksEntityBomb:
    """``defusedxml`` refuses the billion-laughs bomb; a benign doc parses fine.

    This is the security boundary: the chunker must NOT expand a malicious
    entity-bomb (which would exhaust memory). It must raise instead. An
    implementation that fell back to the stdlib ``xml.etree`` parser would
    happily expand the bomb and fail this test.
    """

    def setup_method(self) -> None:
        from lorescribe.xml_generic import XmlChunker

        self.chunker = XmlChunker()
        self.ctx = _make_ctx()

    def test_entity_bomb_raises(self) -> None:
        # Act / Assert: the bomb must be REFUSED at parse time with an exception,
        # never expanded. We assert an exception is raised (defusedxml raises
        # ``EntitiesForbidden``); we do not pin the exact class so the chunker is
        # free to wrap it, only that it does NOT return expanded content.
        with pytest.raises(Exception):  # noqa: B017 - any raise proves non-expansion
            self.chunker.chunk(BILLION_LAUGHS_XML, self.ctx)

    def test_benign_document_parses_without_raising(self) -> None:
        # Act: the very same code path must parse a benign document cleanly —
        # proving the defense does not reject all DOCTYPE-free XML wholesale.
        chunks = self.chunker.chunk(BENIGN_XML, self.ctx)
        # Assert: it produced at least one chunk (no crash, real output).
        assert len(chunks) >= 1
        assert all(isinstance(chunk, Chunk) for chunk in chunks)


class TestRecursionDosDefense:
    """A pathologically deep document cannot crash the worker with ``RecursionError``.

    [HIGH] A ~1000-deep, ~7KB document is UNDER the token cap, so no size-driven
    split is attempted — yet ``ElementTree.tostring`` (and a naive recursive
    walk) recurse in Python and blow the interpreter's call stack, killing the
    worker. The chunker must defend BOTH surfaces: a cheap pre-parse depth gate
    refuses the document before the first ``tostring`` (raising a controlled
    ``ValueError``, never a ``RecursionError``), and the recursive walk is itself
    depth-capped. A normal-depth document must still chunk correctly.
    """

    def setup_method(self) -> None:
        from lorescribe.xml_generic import XmlChunker

        self.chunker = XmlChunker()
        self.ctx = _make_ctx()

    def test_deeply_nested_under_cap_does_not_raise_recursionerror(self) -> None:
        # A ~1100-deep chain is a few KB — comfortably under the token cap, so
        # the size-tier logic attempts no split and the ONLY hazard is the
        # serialize/walk recursion. The defense must turn that into a controlled
        # outcome, NEVER a RecursionError that crashes the worker.
        from lorescribe.xml_generic import MAX_DEPTH

        deep = _make_deeply_nested_xml(depth=MAX_DEPTH + 800)
        # Sanity: the fixture really is under the token cap (so no split masks
        # the recursion surface) — this is the dangerous regime.
        assert approx_token_count(deep) <= self.ctx.max_input_tokens
        try:
            result = self.chunker.chunk(deep, self.ctx)
        except RecursionError:  # pragma: no cover - the bug we are preventing
            pytest.fail("over-deep document raised RecursionError (worker crash)")
        except ValueError:
            # A controlled refusal is graceful handling — no crash. Acceptable.
            result = None
        # Either it refused cleanly (ValueError above) or returned chunks; in no
        # case did it crash with RecursionError.
        assert result is None or isinstance(result, list)

    def test_over_deep_document_is_refused_with_valueerror(self) -> None:
        # The pre-parse depth gate must REFUSE an over-deep document explicitly
        # (a controlled ValueError), rather than letting it reach ``tostring``.
        from lorescribe.xml_generic import MAX_DEPTH

        deep = _make_deeply_nested_xml(depth=MAX_DEPTH + 50)
        with pytest.raises(ValueError, match="depth"):
            self.chunker.chunk(deep, self.ctx)

    def test_document_at_the_depth_limit_is_accepted(self) -> None:
        # A document exactly AT the limit is legitimate and must chunk — the gate
        # rejects only strictly-deeper documents (off-by-one guard).
        from lorescribe.xml_generic import MAX_DEPTH

        at_limit = _make_deeply_nested_xml(depth=MAX_DEPTH)
        chunks = self.chunker.chunk(at_limit, self.ctx)
        assert len(chunks) >= 1

    def test_normal_depth_document_still_chunks_correctly(self) -> None:
        # The defense must not regress ordinary documents: a shallow file still
        # produces its single whole-file chunk with the right identity/metadata.
        chunks = self.chunker.chunk(BENIGN_XML, self.ctx)
        assert len(chunks) == 1
        assert chunks[0].metadata["root_tag"] == "catalog"
        assert chunks[0].identity == "catalog"


class TestCollectNamespacesIsDefused:
    """``_collect_namespaces`` parses with the DEFUSED parser, not the stdlib one.

    [MEDIUM] The namespace sweep is a *second* parse of the raw source. If it
    used the stdlib ``xml.etree.ElementTree.iterparse`` it would expand an
    entity-bomb (today only "safe" by the incidental ordering of ``fromstring``
    first — fragile). Called DIRECTLY with a billion-laughs payload it must NOT
    expand: it raises (defused) or returns ``{}`` — never amplified content. A
    benign namespaced document still yields the real prefix->URI map.
    """

    def test_collect_namespaces_does_not_expand_entity_bomb(self) -> None:
        from lorescribe.xml_generic import XmlChunker

        # Call the sweep DIRECTLY (bypassing the ``fromstring`` that currently
        # masks the issue) so we pin the parser used INSIDE ``_collect_namespaces``.
        try:
            result = XmlChunker._collect_namespaces(BILLION_LAUGHS_XML)
        except Exception:
            # Defused parser raises (e.g. EntitiesForbidden) — never expands. Good.
            return
        # If it did not raise, it must NOT have expanded the bomb: an empty map
        # is the only acceptable non-raising outcome. The stdlib parser would
        # return the (default) namespace map AFTER expanding &lol9; in memory.
        assert result == {}

    def test_collect_namespaces_still_reads_real_namespaces(self) -> None:
        from lorescribe.xml_generic import XmlChunker

        ns_doc = (
            '<feed xmlns="http://www.w3.org/2005/Atom" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/">'
            "<title>x</title></feed>"
        )
        namespaces = XmlChunker._collect_namespaces(ns_doc)
        # The defused parser must still surface the declared namespace URIs.
        assert "http://www.w3.org/2005/Atom" in namespaces.values()
        assert "http://purl.org/dc/elements/1.1/" in namespaces.values()


class TestExternalEntityDefense:
    """[LOW] An XXE external-entity document is refused — no file read / SSRF.

    A ``<!ENTITY xxe SYSTEM "file:///etc/passwd">`` reference, if resolved, leaks
    a local file (or, with an ``http://`` target, performs an SSRF request). The
    chunker must REFUSE such a document — on both the ``fromstring`` path
    (``chunk``) and the ``_collect_namespaces`` sweep.
    """

    def setup_method(self) -> None:
        from lorescribe.xml_generic import XmlChunker

        self.chunker = XmlChunker()
        self.ctx = _make_ctx()

    def test_chunk_refuses_external_entity_document(self) -> None:
        # Act / Assert: resolving the external entity would read /etc/passwd; the
        # defused parser must raise instead, never returning the file's contents.
        with pytest.raises(Exception):  # noqa: B017 - any raise proves non-resolution
            self.chunker.chunk(XXE_EXTERNAL_ENTITY_XML, self.ctx)

    def test_collect_namespaces_refuses_external_entity_document(self) -> None:
        from lorescribe.xml_generic import XmlChunker

        # The second-parse path must be equally hardened: it raises or returns
        # ``{}``, never resolving the external entity.
        try:
            result = XmlChunker._collect_namespaces(XXE_EXTERNAL_ENTITY_XML)
        except Exception:
            return  # defused refusal — correct
        assert result == {}


class TestSmallFileSingleChunk:
    """A small file collapses to a single whole-file chunk rooted at the document."""

    def setup_method(self) -> None:
        from lorescribe.xml_generic import XmlChunker

        self.chunker = XmlChunker()
        self.ctx = _make_ctx()

    def test_small_file_yields_exactly_one_chunk(self) -> None:
        chunks = self.chunker.chunk(BENIGN_XML, self.ctx)
        assert len(chunks) == 1

    def test_whole_file_chunk_is_rooted_at_document_element(self) -> None:
        chunk = self.chunker.chunk(BENIGN_XML, self.ctx)[0]
        # The single chunk represents the root element ``<catalog>``.
        assert chunk.metadata["root_tag"] == "catalog"
        assert chunk.metadata["element_tag"] == "catalog"
        assert chunk.metadata["tag_path"] == "catalog"

    def test_whole_file_chunk_type_is_xml_element(self) -> None:
        chunk = self.chunker.chunk(BENIGN_XML, self.ctx)[0]
        assert chunk.chunk_type == "xml_element"

    def test_whole_file_chunk_identity_is_root_tag_path(self) -> None:
        # The root has no id|name|key|xml:id attr, so identity falls back to the
        # tag_path of the root element.
        chunk = self.chunker.chunk(BENIGN_XML, self.ctx)[0]
        assert chunk.identity == "catalog"

    def test_whole_file_chunk_stays_within_token_cap(self) -> None:
        chunk = self.chunker.chunk(BENIGN_XML, self.ctx)[0]
        assert approx_token_count(chunk.source_text) <= self.ctx.max_input_tokens


class TestLargeFilePerChildChunks:
    """A file too large for one chunk splits into one chunk per top-level child."""

    def setup_method(self) -> None:
        from lorescribe.xml_generic import XmlChunker

        self.chunker = XmlChunker()
        # Five books, each body ~8000 chars (~2000 tokens) => whole-file ~10000
        # tokens, over the 8192 cap; each individual book ~2000 tokens, under it.
        self.n_books = 5
        self.source = _make_large_catalog(n_books=self.n_books, body_chars=8000)
        self.ctx = _make_ctx()

    def test_large_file_does_not_collapse_to_one_chunk(self) -> None:
        chunks = self.chunker.chunk(self.source, self.ctx)
        # Independent expected value: the file is over the cap as a whole, so it
        # MUST split — more than one chunk.
        assert len(chunks) > 1

    def test_large_file_yields_one_chunk_per_top_level_child(self) -> None:
        chunks = self.chunker.chunk(self.source, self.ctx)
        # One chunk per <book> top-level child (none individually over the cap).
        assert len(chunks) == self.n_books

    def test_each_child_chunk_is_a_book_element(self) -> None:
        chunks = self.chunker.chunk(self.source, self.ctx)
        # Guard against a vacuous pass on an empty list.
        assert len(chunks) == self.n_books
        assert all(chunk.metadata["element_tag"] == "book" for chunk in chunks)
        # Root tag is still recorded on every chunk for breadcrumb context.
        assert all(chunk.metadata["root_tag"] == "catalog" for chunk in chunks)

    def test_every_emitted_chunk_stays_within_token_cap(self) -> None:
        chunks = self.chunker.chunk(self.source, self.ctx)
        # Guard against a vacuous pass on an empty list.
        assert len(chunks) == self.n_books
        for chunk in chunks:
            assert approx_token_count(chunk.source_text) <= self.ctx.max_input_tokens


class TestOversizedChildRecursesWithBreadcrumb:
    """The third size tier: a top-level child that is ITSELF over the cap recurses.

    When per-top-level-child splitting still leaves a child over the cap, the
    chunker must descend ANOTHER level — one chunk per that child's own children
    — and stamp a ``tag_path`` breadcrumb header so the embedder retains each
    deep element's location in the tree (module docstring, size-tier 3). Two
    regressions are pinned here, both invisible to the rest of the suite (which
    never goes deeper than one level): (a) failing to recurse would emit the
    oversized child as a single over-cap chunk; (b) recursing but omitting the
    breadcrumb would leave ``metadata_header`` empty, losing tree context.
    """

    def setup_method(self) -> None:
        from lorescribe.xml_generic import XmlChunker

        self.chunker = XmlChunker()
        self.ctx = _make_ctx()
        # One <book> whose body is split across four <chapter> children. The book
        # AS A WHOLE (~16000 tokens) is over the 8192 cap, forcing a descent past
        # the book into its chapters; each chapter (~4000 tokens) is under the cap.
        self.n_chapters = 4
        chapter_body = "z" * 16000
        chapters = "".join(
            f'<chapter id="ch{index:02d}"><body>{chapter_body}</body></chapter>'
            for index in range(self.n_chapters)
        )
        self.source = f'<catalog>\n  <book id="bk1">{chapters}</book>\n</catalog>\n'

    def test_recurses_into_oversized_child_one_chunk_per_grandchild(self) -> None:
        chunks = self.chunker.chunk(self.source, self.ctx)
        # Independent expected value: the oversized <book> cannot be a single
        # chunk, so the chunker descends to its four <chapter> grandchildren.
        assert len(chunks) == self.n_chapters
        assert all(chunk.metadata["element_tag"] == "chapter" for chunk in chunks)

    def test_recursed_chunks_record_accumulated_tag_path_and_depth(self) -> None:
        chunks = self.chunker.chunk(self.source, self.ctx)
        assert len(chunks) == self.n_chapters
        for chunk in chunks:
            # tag_path accumulates the full ancestry root->book->chapter...
            assert chunk.metadata["tag_path"] == "catalog/book/chapter"
            # ...and depth reflects two levels below the root.
            assert chunk.metadata["depth"] == 2

    def test_recursed_chunks_carry_tag_path_breadcrumb_header(self) -> None:
        chunks = self.chunker.chunk(self.source, self.ctx)
        assert len(chunks) == self.n_chapters
        for chunk in chunks:
            # The breadcrumb header (depth > 0) must carry the tag_path so the
            # embedder keeps the element's location; it must NOT be empty.
            assert chunk.metadata_header == "tag_path: catalog/book/chapter"
            # And it must flow into embedding_text ahead of the source.
            assert chunk.embedding_text.startswith("tag_path: catalog/book/chapter\n")

    def test_every_recursed_chunk_stays_within_token_cap(self) -> None:
        chunks = self.chunker.chunk(self.source, self.ctx)
        assert len(chunks) == self.n_chapters
        for chunk in chunks:
            assert approx_token_count(chunk.source_text) <= self.ctx.max_input_tokens


class TestSiblingIdentityDistinctness:
    """Same-tag siblings with different ids get DISTINCT identities — no collapse.

    This is the Chunk Identity Contract pinned directly: three ``<book>``
    elements sharing the tag but carrying ``id="bk101/102/103"`` must NOT
    collapse to one identity downstream. An implementation that keyed by tag
    alone (the odoo-code ``build_chunk_key`` sin) would assign all three the
    same identity and fail here.
    """

    def setup_method(self) -> None:
        from lorescribe.xml_generic import XmlChunker

        self.chunker = XmlChunker()
        # Force per-child splitting so each sibling becomes its own chunk: four
        # books at ~16000 chars each (~4000 tokens) total ~64000 chars
        # (~16000 tokens) — over the 8192 cap as a whole, each book under it.
        self.n_books = 4
        self.source = _make_large_catalog(n_books=self.n_books, body_chars=16000)
        self.ctx = _make_ctx()

    def test_siblings_have_distinct_identities(self) -> None:
        chunks = self.chunker.chunk(self.source, self.ctx)
        # Guard against a vacuous pass on an empty list — all siblings present.
        assert len(chunks) == self.n_books
        identities = [chunk.identity for chunk in chunks]
        # All distinct — no two siblings share an identity.
        assert len(set(identities)) == len(identities)

    def test_sibling_identities_use_their_id_attribute(self) -> None:
        chunks = self.chunker.chunk(self.source, self.ctx)
        identities = {chunk.identity for chunk in chunks}
        # Independent expected value: the id attrs we wrote into the fixture.
        expected = {f"bk{index:03d}" for index in range(self.n_books)}
        assert identities == expected

    def test_sibling_chunks_record_their_id_attr_in_metadata(self) -> None:
        chunks = self.chunker.chunk(self.source, self.ctx)
        # Guard against a vacuous pass on an empty list.
        assert len(chunks) == self.n_books
        for chunk in chunks:
            # id_attr is the first present of id|name|key|xml:id; here it's ``id``.
            assert chunk.metadata["id_attr"] == chunk.identity

    def test_idless_siblings_stay_distinct_via_sub_ordinal(self) -> None:
        # The HARD case of the Identity Contract (rule 3): same-tag siblings with
        # NO id|name|key|xml:id attribute. They legitimately share an identity
        # (the structural tag_path), so the chunker MUST disambiguate them with
        # sub_ordinal — otherwise their downstream (identity, sub_ordinal) keys
        # collide and one silently overwrites the other in the vector store.
        # An impl that leaves sub_ordinal at its default 0 for all of them fails.
        n_items = 4
        body = "y" * 16000  # each item ~4000 tokens -> file over the 8192 cap
        items = "".join(f"  <item><body>{body}</body></item>\n" for _ in range(n_items))
        source = f"<feed>\n{items}</feed>\n"
        chunks = self.chunker.chunk(source, self.ctx)
        # Guard against a vacuous pass — all four id-less items must split out.
        assert len(chunks) == n_items
        # They share the structural identity (no id attr to distinguish them)...
        assert {chunk.identity for chunk in chunks} == {"feed/item"}
        # ...so the (identity, sub_ordinal) natural keys must all be distinct.
        keys = [(chunk.identity, chunk.sub_ordinal) for chunk in chunks]
        assert len(set(keys)) == n_items


class TestGenericMetadata:
    """The generic XML metadata block is populated correctly on each chunk."""

    def setup_method(self) -> None:
        from lorescribe.xml_generic import XmlChunker

        self.chunker = XmlChunker()
        self.ctx = _make_ctx()

    def test_id_attr_follows_full_precedence_id_name_key_xmlid(self) -> None:
        # Pin the WHOLE precedence chain (id > name > key > xml:id), not just the
        # name/key fall-through. Each <param> is its own large chunk; on each one
        # the chunker must pick the HIGHEST-precedence attribute that is present:
        #   p1: id present (and name, to prove id wins OVER name)  -> "the-id"
        #   p2: no id, name present                                -> "by-name"
        #   p3: no id/name, key present                            -> "by-key"
        #   p4: only xml:id present (lowest-precedence fallback)   -> "by-xmlid"
        big_value = "x" * 40000
        source = (
            "<config>\n"
            f'  <param id="the-id" name="ignored">{big_value}</param>\n'
            f'  <param name="by-name">{big_value}</param>\n'
            f'  <param key="by-key">{big_value}</param>\n'
            f'  <param xml:id="by-xmlid">{big_value}</param>\n'
            "</config>\n"
        )
        chunks = self.chunker.chunk(source, self.ctx)
        resolved_id_attrs = {chunk.metadata["id_attr"] for chunk in chunks}
        # Independent expected set: the highest-precedence attr on each element.
        # "ignored" must NOT appear — id outranks name on the first <param>.
        assert resolved_id_attrs == {"the-id", "by-name", "by-key", "by-xmlid"}
        assert "ignored" not in resolved_id_attrs

    def test_attributes_are_captured_as_a_mapping(self) -> None:
        source = (
            "<catalog>\n"
            f'  <book id="bk1" lang="en" pages="350">{"x" * 40000}</book>\n'
            f'  <book id="bk2" lang="fr" pages="120">{"x" * 40000}</book>\n'
            "</catalog>\n"
        )
        chunks = self.chunker.chunk(source, self.ctx)
        first = next(chunk for chunk in chunks if chunk.metadata["id_attr"] == "bk1")
        # attributes is the element's attrib dict, captured verbatim.
        assert first.metadata["attributes"] == {
            "id": "bk1",
            "lang": "en",
            "pages": "350",
        }

    def test_name_attr_is_captured_when_present(self) -> None:
        source = (
            "<catalog>\n"
            f'  <book id="bk1" name="Mythical Man-Month">{"x" * 40000}</book>\n'
            f'  <book id="bk2" name="The Pragmatic Programmer">{"x" * 40000}</book>\n'
            "</catalog>\n"
        )
        chunks = self.chunker.chunk(source, self.ctx)
        first = next(chunk for chunk in chunks if chunk.metadata["id_attr"] == "bk1")
        # name_attr is the value of the ``name`` attribute specifically.
        assert first.metadata["name_attr"] == "Mythical Man-Month"

    def test_child_count_reflects_direct_children(self) -> None:
        # bk1 itself stays small (its two children are short) but the whole file
        # is pushed over the cap by two large sibling books, forcing per-child
        # splitting so bk1 surfaces as its own chunk with child_count == 2.
        source = (
            "<catalog>\n"
            '  <book id="bk1"><title>TDD</title><author>Beck</author></book>\n'
            f'  <book id="bk2">{"x" * 28000}</book>\n'
            f'  <book id="bk3">{"x" * 28000}</book>\n'
            "</catalog>\n"
        )
        chunks = self.chunker.chunk(source, self.ctx)
        first = next(chunk for chunk in chunks if chunk.metadata["id_attr"] == "bk1")
        # bk1 has two direct children (<title>, <author>).
        assert first.metadata["child_count"] == 2

    def test_depth_increases_for_nested_elements(self) -> None:
        # A small file is a single root chunk at depth 0.
        chunk = self.chunker.chunk(BENIGN_XML, self.ctx)[0]
        assert chunk.metadata["depth"] == 0

    def test_line_range_is_a_two_tuple_of_chunk_span(self) -> None:
        chunk = self.chunker.chunk(BENIGN_XML, self.ctx)[0]
        line_range = chunk.metadata["line_range"]
        # A 2-element (start, end) span, both 1-based and start <= end.
        assert len(line_range) == 2
        assert line_range[0] >= 1
        assert line_range[0] <= line_range[1]


class TestNamespaceHandling:
    """Clark-notation ``{uri}tag`` is split into a bare localname + a URI map."""

    def setup_method(self) -> None:
        from lorescribe.xml_generic import XmlChunker

        self.chunker = XmlChunker()
        self.ctx = _make_ctx()

    NS_XML: str = (
        '<feed xmlns="http://www.w3.org/2005/Atom" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        "  <title>News</title>\n"
        "</feed>\n"
    )

    def test_element_tag_is_the_bare_localname_not_clark_notation(self) -> None:
        chunk = self.chunker.chunk(self.NS_XML, self.ctx)[0]
        # element_tag must be ``feed`` — NOT ``{http://www.w3.org/2005/Atom}feed``.
        assert chunk.metadata["element_tag"] == "feed"
        assert "{" not in chunk.metadata["element_tag"]

    def test_namespaces_map_carries_the_uris(self) -> None:
        chunk = self.chunker.chunk(self.NS_XML, self.ctx)[0]
        namespaces = chunk.metadata["namespaces"]
        # The Atom default namespace URI must appear in the captured map values.
        assert "http://www.w3.org/2005/Atom" in namespaces.values()

    def test_tag_path_uses_localnames(self) -> None:
        chunk = self.chunker.chunk(self.NS_XML, self.ctx)[0]
        # No Clark notation leaks into the tag_path either.
        assert "{" not in chunk.metadata["tag_path"]


class TestSchemaProfileHook:
    """A registered ``SchemaProfile`` overrides chunk_type/metadata or skips an element.

    The hook is a per-element callable ``__call__(element, ctx) -> ProfileResult |
    None``. The chunker consults each registered profile; the first non-None wins:
    its ``chunk_type`` replaces the generic ``xml_element`` and its
    ``extra_metadata`` merges over the generic defaults. ``skip=True`` drops the
    element from the output entirely.
    """

    def setup_method(self) -> None:
        from lorescribe.xml_generic import XmlChunker

        self.XmlChunker = XmlChunker
        # Force per-child splitting so profiles fire on the <book> children:
        # three books at ~16000 chars (~4000 tokens) total ~48000 chars
        # (~12000 tokens) — over the 8192 cap as a whole, each book under it.
        self.n_books = 3
        self.source = _make_large_catalog(n_books=self.n_books, body_chars=16000)
        self.ctx = _make_ctx()

    def test_profile_overrides_chunk_type_and_merges_extra_metadata(self) -> None:
        def book_profile(element: object, ctx: ChunkContext) -> ProfileResult | None:
            # Fire only on <book> elements; localname comparison.
            tag = getattr(element, "tag", "")
            local = tag.rsplit("}", 1)[-1]
            if local == "book":
                return ProfileResult(
                    chunk_type="catalog_book",
                    extra_metadata={"schema": "catalog-v1"},
                )
            return None

        chunker = self.XmlChunker(profiles=[book_profile])
        chunks = chunker.chunk(self.source, self.ctx)
        assert len(chunks) == self.n_books
        for chunk in chunks:
            # chunk_type came from the profile, not the generic default.
            assert chunk.chunk_type == "catalog_book"
            # extra_metadata merged over the generic block (generic keys survive).
            assert chunk.metadata["schema"] == "catalog-v1"
            assert chunk.metadata["element_tag"] == "book"

    def test_profile_skip_drops_the_element(self) -> None:
        def drop_even_profile(element: object, ctx: ChunkContext) -> ProfileResult | None:
            # Skip books whose id ends in an even digit (bk000, bk002).
            element_id = element.get("id", "") if hasattr(element, "get") else ""
            if element_id and int(element_id[-1]) % 2 == 0:
                return ProfileResult(chunk_type="dropped", extra_metadata={}, skip=True)
            return None

        chunker = self.XmlChunker(profiles=[drop_even_profile])
        chunks = chunker.chunk(self.source, self.ctx)
        identities = {chunk.identity for chunk in chunks}
        # bk000 and bk002 dropped; only bk001 survives.
        assert identities == {"bk001"}

    def test_first_non_none_profile_wins(self) -> None:
        def first_profile(element: object, ctx: ChunkContext) -> ProfileResult | None:
            tag = getattr(element, "tag", "")
            if tag.rsplit("}", 1)[-1] == "book":
                return ProfileResult(chunk_type="winner", extra_metadata={"by": "first"})
            return None

        def second_profile(element: object, ctx: ChunkContext) -> ProfileResult | None:
            tag = getattr(element, "tag", "")
            if tag.rsplit("}", 1)[-1] == "book":
                return ProfileResult(chunk_type="loser", extra_metadata={"by": "second"})
            return None

        chunker = self.XmlChunker(profiles=[first_profile, second_profile])
        chunks = chunker.chunk(self.source, self.ctx)
        # Guard against a vacuous pass on an empty list.
        assert len(chunks) == self.n_books
        for chunk in chunks:
            assert chunk.chunk_type == "winner"
            assert chunk.metadata["by"] == "first"

    def test_no_profile_match_falls_back_to_generic_defaults(self) -> None:
        def never_fires(element: object, ctx: ChunkContext) -> ProfileResult | None:
            return None

        chunker = self.XmlChunker(profiles=[never_fires])
        chunks = chunker.chunk(self.source, self.ctx)
        # Guard against a vacuous pass on an empty list.
        assert len(chunks) == self.n_books
        for chunk in chunks:
            # No profile fired -> generic default chunk_type.
            assert chunk.chunk_type == "xml_element"


def _localname_of(element: object) -> str:
    """Return the bare localname of an ElementTree element (Clark-notation safe)."""
    tag = getattr(element, "tag", "")
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


class TestProfileForcesOwnChunkOnSmallFile:
    """A profile can force a claimed element to its OWN chunk in a SMALL file.

    The verified gap: ``XmlChunker._emit`` decides granularity (over_cap /
    should_descend) BEFORE any profile is consulted, so in a small file a
    profile-claimed element collapses into the single whole-file chunk. The new
    ``ProfileResult.force_own_chunk`` control must override the size-tier
    decision: a claimed element becomes its own chunk even when the whole
    document fits under the cap, while non-claimed elements keep the existing
    size-tiered behaviour and every security/identity invariant survives.

    Real corpus: ImageMagick's ``thresholds.xml`` — a genuine, generic XML file
    whose root holds 19 repeated ``<threshold>`` siblings and is small enough
    (~3K tokens) that the chunker would otherwise emit exactly ONE whole-file
    chunk for the root.
    """

    def setup_method(self) -> None:
        from lorescribe.xml_generic import XmlChunker

        self.XmlChunker = XmlChunker
        self.ctx = _make_ctx(file_path=str(REAL_GENERIC_XML_PATH))
        if not REAL_GENERIC_XML_PATH.is_file():
            pytest.skip(f"real generic XML corpus absent: {REAL_GENERIC_XML_PATH}")
        self.source = REAL_GENERIC_XML_PATH.read_text(encoding="utf-8")
        # Count the real repeated child elements straight from the parsed tree so
        # the expected value is independent of the chunker under test.
        from defusedxml.ElementTree import fromstring as _fromstring

        root = _fromstring(self.source)
        self.threshold_count = sum(1 for c in root if _localname_of(c) == "threshold")
        # Sanity: the corpus really does have repeated siblings to split out.
        assert self.threshold_count >= 2

    def _threshold_profile(self) -> Callable[[object, ChunkContext], ProfileResult | None]:
        def profile(element: object, ctx: ChunkContext) -> ProfileResult | None:
            if _localname_of(element) == "threshold":
                return ProfileResult(
                    chunk_type="threshold_map",
                    extra_metadata={"schema": "imagemagick-thresholds"},
                    force_own_chunk=True,
                )
            return None

        return profile

    def test_baseline_small_file_collapses_to_one_chunk_without_profile(self) -> None:
        # Establishes the regime: with NO profile, this real small file is a
        # single whole-file chunk (the size-tier default). If this ever became
        # multi-chunk on its own, the force_own_chunk test below would be
        # vacuous, so this guards the precondition.
        chunker = self.XmlChunker()
        chunks = chunker.chunk(self.source, self.ctx)
        assert len(chunks) == 1
        assert chunks[0].metadata["element_tag"] == "thresholds"

    def test_force_own_chunk_splits_claimed_siblings_in_small_file(self) -> None:
        # Act: a profile claims every <threshold> with force_own_chunk=True.
        chunker = self.XmlChunker(profiles=[self._threshold_profile()])
        chunks = chunker.chunk(self.source, self.ctx)
        # Assert: each claimed element is now its OWN chunk despite the small
        # file — independent expected value is the real sibling count parsed
        # above. The buggy pre-fix behaviour returns ONE whole-file chunk.
        assert len(chunks) == self.threshold_count
        for chunk in chunks:
            assert chunk.chunk_type == "threshold_map"
            assert chunk.metadata["element_tag"] == "threshold"
            # extra_metadata merged over the generic block (generic keys survive).
            assert chunk.metadata["schema"] == "imagemagick-thresholds"
            assert chunk.metadata["root_tag"] == "thresholds"

    def test_forced_siblings_keep_distinct_natural_keys(self) -> None:
        # Identity/sub_ordinal correctness must survive the forced split. The
        # <threshold> elements carry no id|name|key|xml:id attribute, so they
        # share the structural tag_path identity and MUST be disambiguated by
        # sub_ordinal — otherwise their downstream (identity, sub_ordinal) keys
        # collide and one silently overwrites another.
        chunker = self.XmlChunker(profiles=[self._threshold_profile()])
        chunks = chunker.chunk(self.source, self.ctx)
        assert len(chunks) == self.threshold_count
        keys = [(chunk.identity, chunk.sub_ordinal) for chunk in chunks]
        # All natural keys distinct — no collapse.
        assert len(set(keys)) == self.threshold_count
        # They share the structural identity (no id attr distinguishes them)...
        assert {chunk.identity for chunk in chunks} == {"thresholds/threshold"}
        # ...so sub_ordinal must run 0..n-1 in document order.
        assert sorted(chunk.sub_ordinal for chunk in chunks) == list(
            range(self.threshold_count)
        )

    def test_forced_chunks_carry_tag_path_breadcrumb_header(self) -> None:
        # A forced child is below the root (depth 1), so it must carry the
        # tag_path breadcrumb header, exactly like a size-driven child split.
        chunker = self.XmlChunker(profiles=[self._threshold_profile()])
        chunks = chunker.chunk(self.source, self.ctx)
        assert len(chunks) == self.threshold_count
        for chunk in chunks:
            assert chunk.metadata["tag_path"] == "thresholds/threshold"
            assert chunk.metadata["depth"] == 1
            assert chunk.metadata_header == "tag_path: thresholds/threshold"

    def test_unclaimed_elements_keep_size_tiered_default(self) -> None:
        # A profile that fires on a tag NOT present (or that never claims) must
        # leave the size-tier default intact: the small file stays ONE chunk.
        # This proves force_own_chunk affects ONLY claimed elements.
        def never_claims(element: object, ctx: ChunkContext) -> ProfileResult | None:
            if _localname_of(element) == "nonexistent-tag":
                return ProfileResult(
                    chunk_type="never", extra_metadata={}, force_own_chunk=True
                )
            return None

        chunker = self.XmlChunker(profiles=[never_claims])
        chunks = chunker.chunk(self.source, self.ctx)
        assert len(chunks) == 1
        assert chunks[0].metadata["element_tag"] == "thresholds"

    def test_force_own_chunk_false_does_not_split_small_file(self) -> None:
        # A profile that CLAIMS the element but with force_own_chunk left False
        # must NOT trigger a split — the size-tier default still collapses to one
        # whole-file chunk. This isolates the granularity control from the mere
        # act of claiming an element.
        def claim_without_forcing(
            element: object, ctx: ChunkContext
        ) -> ProfileResult | None:
            if _localname_of(element) == "threshold":
                return ProfileResult(chunk_type="threshold_map", extra_metadata={})
            return None

        chunker = self.XmlChunker(profiles=[claim_without_forcing])
        chunks = chunker.chunk(self.source, self.ctx)
        # The root collapses to one whole-file chunk; the profile never even sees
        # the <threshold> children because the root fits under the cap. So the
        # single chunk is the generic root, NOT a threshold_map.
        assert len(chunks) == 1
        assert chunks[0].metadata["element_tag"] == "thresholds"
