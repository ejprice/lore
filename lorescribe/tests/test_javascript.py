"""Contract tests for ``lorescribe.javascript.JavascriptChunker`` and ``JsProfile``.

``JavascriptChunker`` is a concrete :class:`~lorescribe.base.Chunker` that splits
``.js`` source into embeddable :class:`~lorescribe.models.Chunk` objects. It is
deliberately **domain-agnostic**: the generic core detects only *generic*
JavaScript structure and contains ZERO framework- or product-specific
knowledge. Domain logic plugs in via the pluggable :data:`JsProfile` hook,
exactly like the XML chunker's ``SchemaProfile``.

The contract pinned here:

* ``handles(path)`` claims ``.js`` files case-insensitively and rejects every
  other extension (and extension-less paths). Routing is by extension only —
  whether a ``.js`` file is minified is decided inside ``chunk``, so a
  ``.min.js`` path is still *handled*.

* ``chunk(source, ctx)`` returns ``[]`` for an empty/whitespace-only file and
  for a minified file (a ``.min.js`` path, OR content whose average line length
  is so large it is clearly machine-generated). Minified bundles are dead weight
  for retrieval and would blow the token cap.

* Generic structure detection only:
    - top-level ``function NAME(...) { ... }`` -> ``chunk_type == "js_function"``,
      ``identity == "NAME"``.
    - top-level ``class NAME { ... }`` (and ``export``/``export default`` forms)
      -> ``chunk_type == "js_class"``, ``identity == "NAME"``.
    - top-level ``export`` declarations (``export function``/``export class``/
      ``export const NAME``/``export default``) name the unit from the exported
      symbol; an anonymous ``export default`` yields a ``js_module`` chunk.
    - the unstructured remainder (top-level statements that belong to no
      function/class/export) -> ``window#N`` line windows, ``chunk_type ==
      "window"``.
  Multiple units get DISTINCT identities — collapsing them would collapse their
  downstream point-IDs.

* A unit (or window) too large to embed under ``ctx.max_input_tokens`` is split
  into line windows that always advance; EVERY emitted chunk's
  ``embedding_text`` stays at or below the cap (the embedder rejects, never
  truncates). The no-wedge invariant is load-bearing: a file that is a SINGLE
  over-cap unstructured line must still EMIT (windowed), never return ``[]``.

* The :data:`JsProfile` hook mirrors XML's ``SchemaProfile``: a callable
  ``__call__(block, ctx) -> ProfileResult | None``. For each candidate block the
  chunker consults registered profiles in order; the first non-``None`` result
  claims the block (its ``chunk_type``/``extra_metadata`` win, ``skip=True``
  drops it); otherwise the generic default applies. This is the seam where a
  domain profile (e.g. an Odoo ``odoo.define``/widget profile) plugs in LATER,
  in another package — never inside lorescribe.

All fixtures are GENERIC JavaScript (no framework/domain content). Expected
identities and counts are derived independently from the source text. The token
cap and counter come from the shared conftest (the real voyage-4 hard cap and a
faithful behavioural counter), so an off-by-scale bug cannot pass inertly.
"""

from __future__ import annotations

import pytest
from lorescribe.javascript import JavascriptChunker, JsBlock
from lorescribe.models import ChunkContext, ProfileResult

from .conftest import (
    VOYAGE4_MAX_INPUT_TOKENS,
    approx_token_count,
)

SAMPLE_SLUG: str = "firehawk-handbook"


def _ctx(file_path: str, max_input_tokens: int = VOYAGE4_MAX_INPUT_TOKENS) -> ChunkContext:
    """Build a ChunkContext with the shared behavioural token counter.

    ``max_input_tokens`` is parameterised so the oversize-splitting contract can
    inject a deliberately small cap without touching the shared conftest value.
    """
    return ChunkContext(
        slug=SAMPLE_SLUG,
        file_path=file_path,
        count_tokens=approx_token_count,
        max_input_tokens=max_input_tokens,
    )


# ---------------------------------------------------------------------------
# Generic JavaScript fixtures (zero framework/domain content)
# ---------------------------------------------------------------------------

# Several top-level function declarations — generic library code.
PLAIN_FUNCTIONS_SOURCE: str = """\
function computeTax(amount, rate) {
    return amount * rate;
}

function formatCurrency(value) {
    return "$" + value.toFixed(2);
}

function applyDiscount(price, pct) {
    return price - price * pct;
}
"""

# A top-level ES class with methods — generic OOP JS.
PLAIN_CLASS_SOURCE: str = """\
class Ledger {
    constructor() {
        this.entries = [];
    }
    add(entry) {
        this.entries.push(entry);
    }
    total() {
        return this.entries.reduce((a, b) => a + b, 0);
    }
}
"""

# An ES module mixing named exports: an exported function and an exported class.
EXPORT_MODULE_SOURCE: str = """\
import { helper } from "./helper.js";

export function parse(text) {
    return helper(text).trim();
}

export class Formatter {
    format(value) {
        return String(value);
    }
}
"""


class TestHandles:
    """``handles`` claims ``.js`` case-insensitively and nothing else."""

    def setup_method(self) -> None:
        self.chunker = JavascriptChunker()

    def test_handles_dot_js(self) -> None:
        assert self.chunker.handles("src/util.js") is True

    def test_handles_is_case_insensitive(self) -> None:
        assert self.chunker.handles("SRC/UTIL.JS") is True

    def test_min_js_is_still_handled_by_extension(self) -> None:
        # Routing is by extension; minification is decided inside chunk().
        assert self.chunker.handles("lib/jquery.min.js") is True

    def test_rejects_non_js_extensions(self) -> None:
        assert self.chunker.handles("models/sale.py") is False
        assert self.chunker.handles("README.md") is False

    def test_rejects_extensionless_path(self) -> None:
        assert self.chunker.handles("Makefile") is False


class TestSkips:
    """Empty and minified inputs produce no chunks at all."""

    def setup_method(self) -> None:
        self.chunker = JavascriptChunker()

    def test_empty_file_returns_empty(self) -> None:
        assert self.chunker.chunk("", _ctx("src/empty.js")) == []

    def test_whitespace_only_file_returns_empty(self) -> None:
        assert self.chunker.chunk("\n\n   \n\t\n", _ctx("src/blank.js")) == []

    def test_min_js_extension_skipped(self) -> None:
        # A perfectly valid (if short) JS body, but the path marks it minified.
        source = "var a=function(b){return b+1};a(2);\n"
        assert self.chunker.chunk(source, _ctx("lib/util.min.js")) == []

    def test_minified_by_long_average_line_length_skipped(self) -> None:
        # No .min.js extension, but the content is unmistakably machine-minified:
        # one enormous line. Average line length far exceeds any hand-written JS.
        minified = "var x=" + ";var y=".join(f"f{i}({i})" for i in range(400)) + ";\n"
        assert len(minified) > 2000  # guard: this really is one giant line
        result = self.chunker.chunk(minified, _ctx("src/bundle.js"))
        assert result == []


class TestTopLevelFunctions:
    """Multiple top-level functions get DISTINCT identities and a generic type."""

    def setup_method(self) -> None:
        self.chunker = JavascriptChunker()
        self.result = self.chunker.chunk(PLAIN_FUNCTIONS_SOURCE, _ctx("src/tax.js"))

    def test_emits_three_function_chunks(self) -> None:
        fn_chunks = [c for c in self.result if c.chunk_type == "js_function"]
        # Three top-level declarations in the fixture -> three function chunks.
        assert len(fn_chunks) == 3

    def test_function_identities_are_the_declared_names(self) -> None:
        fn_chunks = [c for c in self.result if c.chunk_type == "js_function"]
        identities = {c.identity for c in fn_chunks}
        # Independently derived from the fixture's `function NAME(` lines.
        assert identities == {"computeTax", "formatCurrency", "applyDiscount"}

    def test_identities_are_distinct(self) -> None:
        # The load-bearing adversarial: sibling chunks must never collapse to
        # the same natural key. (identity, sub_ordinal) pairs must be unique.
        keys = [(c.identity, c.sub_ordinal) for c in self.result]
        assert len(keys) == len(set(keys))

    def test_each_function_body_is_present(self) -> None:
        by_identity = {
            c.identity: c.source_text
            for c in self.result
            if c.chunk_type == "js_function"
        }
        assert "amount * rate" in by_identity["computeTax"]
        assert "toFixed(2)" in by_identity["formatCurrency"]
        assert "price * pct" in by_identity["applyDiscount"]


class TestTopLevelClass:
    """A top-level ES class becomes one ``js_class`` chunk named after the class."""

    def setup_method(self) -> None:
        self.chunker = JavascriptChunker()
        self.result = self.chunker.chunk(PLAIN_CLASS_SOURCE, _ctx("src/ledger.js"))

    def test_emits_one_class_chunk(self) -> None:
        class_chunks = [c for c in self.result if c.chunk_type == "js_class"]
        assert len(class_chunks) == 1

    def test_class_identity_is_the_declared_name(self) -> None:
        class_chunk = next(c for c in self.result if c.chunk_type == "js_class")
        assert class_chunk.identity == "Ledger"

    def test_class_body_is_present(self) -> None:
        class_chunk = next(c for c in self.result if c.chunk_type == "js_class")
        # The whole class (constructor + methods) must be inside the chunk.
        assert "constructor()" in class_chunk.source_text
        assert "reduce((a, b)" in class_chunk.source_text
        assert class_chunk.line_start == 1


class TestExportModule:
    """ES ``export`` declarations are named from the exported symbol."""

    def setup_method(self) -> None:
        self.chunker = JavascriptChunker()
        self.result = self.chunker.chunk(EXPORT_MODULE_SOURCE, _ctx("src/text.js"))

    def test_exported_function_named_and_typed(self) -> None:
        # `export function parse(...)` -> a js_function identity "parse".
        fn = next(
            c for c in self.result
            if c.chunk_type == "js_function" and c.identity == "parse"
        )
        assert "helper(text)" in fn.source_text

    def test_exported_class_named_and_typed(self) -> None:
        # `export class Formatter {...}` -> a js_class identity "Formatter".
        cls = next(
            c for c in self.result
            if c.chunk_type == "js_class" and c.identity == "Formatter"
        )
        assert "format(value)" in cls.source_text

    def test_export_identities_distinct(self) -> None:
        keys = [(c.identity, c.sub_ordinal) for c in self.result]
        assert len(keys) == len(set(keys))


class TestExportDefaultAnonymous:
    """An anonymous ``export default`` yields a non-blank ``js_module`` chunk."""

    def setup_method(self) -> None:
        self.chunker = JavascriptChunker()
        # Anonymous default export — no symbol name to borrow.
        self.source = "export default {\n    name: 'thing',\n    value: 42,\n};\n"
        self.result = self.chunker.chunk(self.source, _ctx("src/config.js"))

    def test_yields_chunks(self) -> None:
        assert len(self.result) >= 1

    def test_module_chunk_has_non_blank_identity(self) -> None:
        # Generic core must still give a non-blank, non-"window#" identity to a
        # named module unit (here derived from the file stem).
        module = next(c for c in self.result if c.chunk_type == "js_module")
        assert module.identity.strip() != ""
        assert not module.identity.startswith("window#")


class TestUnstructuredWindows:
    """A file of bare top-level statements yields ``window#N`` chunks."""

    def setup_method(self) -> None:
        self.chunker = JavascriptChunker()
        # Top-level executable statements, no function/class/export structure.
        self.source = "\n".join(f"console.log({i});" for i in range(50)) + "\n"
        self.result = self.chunker.chunk(self.source, _ctx("src/log.js"))

    def test_yields_chunks(self) -> None:
        assert len(self.result) >= 1

    def test_window_chunk_type_and_identity_form(self) -> None:
        window_chunks = [c for c in self.result if c.chunk_type == "window"]
        assert len(window_chunks) >= 1
        for chunk in window_chunks:
            assert chunk.identity.startswith("window#")

    def test_window_identities_non_blank_and_distinct(self) -> None:
        for chunk in self.result:
            assert chunk.identity.strip() != ""
        keys = [(c.identity, c.sub_ordinal) for c in self.result]
        assert len(keys) == len(set(keys))


class TestOversizeSplitting:
    """A unit exceeding a small injected cap is split into bounded windows."""

    def setup_method(self) -> None:
        self.chunker = JavascriptChunker()
        # One big top-level function whose body far exceeds a tiny cap.
        body_lines = "\n".join(
            f"    var step_{i} = compute(step_{i - 1}, {i});" for i in range(1, 401)
        )
        self.source = f"function bigPipeline() {{\n{body_lines}\n}}\n"
        self.small_cap = 50
        self.ctx = _ctx("src/pipeline.js", max_input_tokens=self.small_cap)
        self.result = self.chunker.chunk(self.source, self.ctx)

    def test_produces_multiple_chunks(self) -> None:
        assert len(self.result) > 1

    def test_every_chunk_within_cap(self) -> None:
        # The hard contract: nothing exceeds the injected cap, measured with the
        # SAME counter the consumer injects (independent oracle).
        for chunk in self.result:
            assert approx_token_count(chunk.embedding_text) <= self.small_cap

    def test_window_identities_are_distinct(self) -> None:
        # When a named unit is split, no two pieces may share a
        # (identity, sub_ordinal) natural key.
        keys = [(c.identity, c.sub_ordinal) for c in self.result]
        assert len(keys) == len(set(keys)), "split windows must not collapse identities"

    def test_no_content_silently_dropped(self) -> None:
        joined = "".join(c.source_text for c in self.result)
        assert "step_1 " in joined or "step_1=" in joined or "step_1," in joined
        assert "step_399" in joined


class TestNoWedgeSingleOverCapLine:
    """A single over-cap UNSTRUCTURED line must EMIT, never return ``[]``.

    This is the bug the prior audit flagged: unstructured content that is a
    single line longer than the token cap (but short enough on AVERAGE to not be
    minified) must still be windowed/sub-split and emitted — the splitter must
    always advance and produce at least one chunk.
    """

    def setup_method(self) -> None:
        self.chunker = JavascriptChunker()

    def test_single_over_cap_line_emits(self) -> None:
        # A single statement line, no function/class/export. ~600 chars -> well
        # over a tiny token cap, but it is one line so it is NOT minified by the
        # average-line-length rule once we keep the average modest. We use a
        # genuinely single-line file here to pin the no-wedge invariant.
        line = "var data = [" + ", ".join(str(i) for i in range(150)) + "];\n"
        # Keep this under the minified threshold check is irrelevant: a single
        # line over the cap must still emit. Use a cap small enough to force it.
        ctx = _ctx("src/data.js", max_input_tokens=20)
        # Guard: the line really does exceed the cap on its own.
        assert approx_token_count(line) > 20
        result = self.chunker.chunk(line, ctx)
        assert result != [], "single over-cap unstructured line must emit, not vanish"
        assert len(result) >= 1

    def test_emitted_chunk_carries_the_content(self) -> None:
        line = "var data = [" + ", ".join(str(i) for i in range(150)) + "];\n"
        ctx = _ctx("src/data.js", max_input_tokens=20)
        result = self.chunker.chunk(line, ctx)
        joined = "".join(c.source_text for c in result)
        # No content silently dropped: head and tail of the single line survive.
        assert "var data" in joined
        assert "149" in joined

    def test_short_unstructured_file_emits_window(self) -> None:
        # A couple of bare statements (no structure) must produce window chunks,
        # never an empty list.
        source = "doThing();\ndoOther();\n"
        result = self.chunker.chunk(source, _ctx("src/bare.js"))
        assert len(result) >= 1
        assert all(c.identity.startswith("window#") for c in result)


# ---------------------------------------------------------------------------
# JsProfile hook — verified with a SYNTHETIC (non-domain) test profile
# ---------------------------------------------------------------------------


class _TaggedBlockProfile:
    """A SYNTHETIC profile: claim any block whose name starts with a marker.

    Stands in for a real domain profile (which would live in another package).
    It demonstrates the hook seam without importing or encoding any framework
    knowledge: it stamps a custom ``chunk_type`` and ``extra_metadata`` on blocks
    whose detected name begins with ``"Plugin"``.
    """

    CUSTOM_CHUNK_TYPE = "synthetic_plugin"

    def __call__(self, block: JsBlock, ctx: ChunkContext) -> ProfileResult | None:
        if block.name is not None and block.name.startswith("Plugin"):
            return ProfileResult(
                chunk_type=self.CUSTOM_CHUNK_TYPE,
                extra_metadata={"plugin_name": block.name, "slug": ctx.slug},
            )
        return None


class _DropTestBlocksProfile:
    """A SYNTHETIC profile that drops any block whose name ends with ``_test``."""

    def __call__(self, block: JsBlock, ctx: ChunkContext) -> ProfileResult | None:
        if block.name is not None and block.name.endswith("_test"):
            return ProfileResult(chunk_type="dropped", extra_metadata={}, skip=True)
        return None


class _AlwaysFirstProfile:
    """A SYNTHETIC profile that claims EVERY block (to test ordering precedence)."""

    def __call__(self, block: JsBlock, ctx: ChunkContext) -> ProfileResult | None:
        return ProfileResult(chunk_type="first_wins", extra_metadata={})


PROFILE_SOURCE: str = """\
function PluginAlpha(opts) {
    return opts.value;
}

function regularHelper(x) {
    return x + 1;
}

function scratch_test() {
    return 0;
}
"""


class TestJsProfileHook:
    """The ``JsProfile`` hook mirrors XML's ``SchemaProfile`` exactly."""

    def test_profile_customises_chunk_type_and_metadata(self) -> None:
        chunker = JavascriptChunker(profiles=[_TaggedBlockProfile()])
        result = chunker.chunk(PROFILE_SOURCE, _ctx("src/plugins.js"))
        # The block named PluginAlpha is claimed by the synthetic profile.
        claimed = next(c for c in result if c.identity == "PluginAlpha")
        assert claimed.chunk_type == _TaggedBlockProfile.CUSTOM_CHUNK_TYPE
        assert claimed.metadata["plugin_name"] == "PluginAlpha"
        assert claimed.metadata["slug"] == SAMPLE_SLUG

    def test_unclaimed_blocks_fall_through_to_generic(self) -> None:
        chunker = JavascriptChunker(profiles=[_TaggedBlockProfile()])
        result = chunker.chunk(PROFILE_SOURCE, _ctx("src/plugins.js"))
        # regularHelper is not claimed -> generic js_function.
        helper = next(c for c in result if c.identity == "regularHelper")
        assert helper.chunk_type == "js_function"

    def test_profile_skip_drops_the_block(self) -> None:
        chunker = JavascriptChunker(profiles=[_DropTestBlocksProfile()])
        result = chunker.chunk(PROFILE_SOURCE, _ctx("src/plugins.js"))
        identities = {c.identity for c in result}
        # scratch_test is dropped; the others survive.
        assert "scratch_test" not in identities
        assert "PluginAlpha" in identities
        assert "regularHelper" in identities

    def test_first_non_none_profile_wins(self) -> None:
        # Ordering precedence: the first profile that returns non-None claims the
        # block, exactly like SchemaProfile. _AlwaysFirstProfile precedes the
        # tagged profile, so even PluginAlpha is stamped "first_wins".
        chunker = JavascriptChunker(
            profiles=[_AlwaysFirstProfile(), _TaggedBlockProfile()]
        )
        result = chunker.chunk(PROFILE_SOURCE, _ctx("src/plugins.js"))
        assert all(c.chunk_type == "first_wins" for c in result)

    def test_no_profiles_is_pure_generic(self) -> None:
        # Default construction (no profiles) = pure generic behaviour.
        chunker = JavascriptChunker()
        result = chunker.chunk(PROFILE_SOURCE, _ctx("src/plugins.js"))
        types = {c.chunk_type for c in result}
        assert types <= {"js_function", "js_class", "js_module", "window"}
        # No synthetic types leaked in.
        assert "synthetic_plugin" not in types
        assert "first_wins" not in types

    def test_profile_receives_a_jsblock_with_name_and_source(self) -> None:
        # Pin the block contract handed to a profile: it must expose at least the
        # detected name and the block's own source text.
        seen: list[JsBlock] = []

        def recorder(block: JsBlock, ctx: ChunkContext) -> ProfileResult | None:
            seen.append(block)
            return None

        chunker = JavascriptChunker(profiles=[recorder])
        chunker.chunk(PLAIN_FUNCTIONS_SOURCE, _ctx("src/tax.js"))
        names = {b.name for b in seen}
        assert {"computeTax", "formatCurrency", "applyDiscount"} <= names
        by_name = {b.name: b.source_text for b in seen if b.name is not None}
        assert "amount * rate" in by_name["computeTax"]


class TestColllidingIdentitiesStayDistinct:
    """Same-named top-level units must NOT collapse to one downstream point-ID.

    The load-bearing identity invariant (models.py): ``(identity, sub_ordinal)``
    is the within-file natural key, and ``sub_ordinal`` exists precisely to
    disambiguate sibling chunks that share an ``identity``. The XML chunker
    enforces this globally via ``_assign_sub_ordinals``; the JS chunker must do
    the same. Two top-level units that happen to share a name — duplicate
    function names in a concatenated/legacy non-module script, or multiple
    anonymous ``export default`` units all falling back to the file stem — must
    get distinct ``(identity, sub_ordinal)`` keys, or one chunk silently
    overwrites the other downstream.
    """

    def setup_method(self) -> None:
        self.chunker = JavascriptChunker()

    def test_duplicate_function_names_get_distinct_keys(self) -> None:
        # Legal in a concatenated/global non-module script; both are top-level.
        source = "function dup() { return 1; }\nfunction dup() { return 2; }\n"
        result = self.chunker.chunk(source, _ctx("src/concat.js"))
        identities = [c.identity for c in result]
        assert identities.count("dup") == 2, "both same-named units must be emitted"
        keys = [(c.identity, c.sub_ordinal) for c in result]
        assert len(keys) == len(set(keys)), "colliding identities must not share a natural key"

    def test_multiple_anonymous_defaults_get_distinct_keys(self) -> None:
        # Both anonymous default exports fall back to the SAME file stem; their
        # natural keys must still be distinct.
        source = "export default { a: 1 };\nexport default { b: 2 };\n"
        result = self.chunker.chunk(source, _ctx("src/config.js"))
        keys = [(c.identity, c.sub_ordinal) for c in result]
        assert len(keys) == len(set(keys)), "stem-named anon defaults must not collide"


class TestChunkInvariants:
    """Cross-cutting invariants every emitted chunk must satisfy."""

    @pytest.mark.parametrize(
        ("source", "path"),
        [
            (PLAIN_FUNCTIONS_SOURCE, "src/tax.js"),
            (PLAIN_CLASS_SOURCE, "src/ledger.js"),
            (EXPORT_MODULE_SOURCE, "src/text.js"),
        ],
    )
    def test_line_bounds_are_sane(self, source: str, path: str) -> None:
        chunker = JavascriptChunker()
        for chunk in chunker.chunk(source, _ctx(path)):
            assert chunk.line_start >= 1
            assert chunk.line_end >= chunk.line_start
            assert chunk.line_end <= source.count("\n") + 1

    @pytest.mark.parametrize(
        ("source", "path"),
        [
            (PLAIN_FUNCTIONS_SOURCE, "src/tax.js"),
            (PLAIN_CLASS_SOURCE, "src/ledger.js"),
            (EXPORT_MODULE_SOURCE, "src/text.js"),
        ],
    )
    def test_all_chunks_within_default_cap(self, source: str, path: str) -> None:
        chunker = JavascriptChunker()
        ctx = _ctx(path)
        for chunk in chunker.chunk(source, ctx):
            assert approx_token_count(chunk.embedding_text) <= ctx.max_input_tokens

    def test_no_odoo_content_in_module(self) -> None:
        # Owner's hard rule: ZERO Odoo/domain content in the generic chunker.
        # Match framework names as WHOLE WORDS (or as the literal @odoo-module
        # marker) so the check is precise — a naive substring search would
        # false-positive on innocent English like "kn-owl-edge".
        import re as _re

        import lorescribe.javascript as module

        source = module.__file__ or ""
        assert source, "module file path must resolve"
        with open(source, encoding="utf-8") as handle:
            text = handle.read().lower()
        for forbidden in ("odoo", "amd", "publicwidget", "owl"):
            assert _re.search(rf"\b{forbidden}\b", text) is None, (
                f"generic chunker must not mention {forbidden!r}"
            )
        assert "@odoo-module" not in text, "generic chunker must not mention the @odoo-module marker"
