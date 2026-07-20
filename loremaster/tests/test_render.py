"""Contract tests for the PKT-28 Phase 0 render-safety seam.

Spec: phase0-render-safety-ruling.md (v2, post-audit) — §ENFORCEMENT (the
failure matrix), §BUILD-NOW items 1-3/9, §C1-C5-AUTHORING, §D1.4. Cold audit:
REPORT-phase0-audit-1.md.

NOTE — THE BINDING SPEC IS UNRECOVERABLE. That ruling lived only at a
per-session ``/tmp`` scratch path; it was never in the repo and is gone from
disk entirely (verified: no copy anywhere on this host, nothing tracked). Every
``§`` reference to it in this module and in its two siblings
(``test_render_seam_pins.py``, ``test_render_mypy_layer.py``) therefore resolves
to NOTHING. The tests below encode most of what the ruling required, but they
are not a substitute for it: treat the §-citations as unverified provenance, and
re-derive from the tests rather than assuming an authority behind them.

**CORRECTED (fix-wave, post cold-audit NO-GO):** the v1 docstring here claimed
rows 1-4 (raw str value / f-string return / hostile LiteralString template /
join-demotion) were "mypy-only — this module cannot drive a real mypy failure
from inside pytest". That claim was FALSE, and it is exactly why row 3 shipped
unverified: `typing.LiteralString` is parsed by mypy 2.1.0 but never actually
enforced (PEP 675 checking is a pyright-only feature; mypy erases the
annotation to plain `str` — audit §PROBE-A, working exploit
`scratchpad/audit1/row3_exploit.py`). This module absolutely CAN drive a real
mypy failure from inside pytest, via `subprocess` — see
`test_render_mypy_layer.py`, which shells out to the repo's own `mypy` against
committed fixture files and pins EXACTLY which rows mypy catches (1, 2, 4 —
verified error codes) and which it does not (3 — verified silent, by design,
until a future mypy ships PEP 675). Rows 1/2/4 are mypy's job and are pinned
there, not re-derived here. Row 3 (the template slot) and row 8 (a
newline-bearing `SafeLine`/separator) are NOT mypy's job at all — they are
guarded by `test_render_seam_pins.py`'s AST template-literal pin plus THIS
module's runtime no-newline contract tests below
(`TestRenderLineAndJoinNoNewlineGuard`), which mypy cannot express. Row 5 (an
`Any`-typed leak) is exercised here via the per-value `isinstance` assert
inside `render_line`. Row 6 (the AST mint-pin, hardened against the audit's
three bypass shapes) and the dispatch-table completeness helper live in
`test_render_seam_pins.py`, not here.
"""

from __future__ import annotations

from typing import Any, cast

import pytest
from loremaster.render import (
    Rendered,
    RenderSafetyError,
    render_compose,
    render_fenced,
    render_join,
    render_line,
)
from loremaster.sanitise import (
    FENCE_CHAR,
    MIN_FENCE_WIDTH,
    SafeLine,
    max_backtick_run,
    safe_str,
    sanitise_line,
)
from render_injection_scaffold import (
    _INJECTION_THREAT_CHARS,
    _ROW_FORGE_PAYLOAD,
    assert_render_injection_safe,
)

# --------------------------------------------------------------------------- #
# D1.4's known, documented gap (ruling §D1.4): three codepoints
# CONTROL_CHAR_PATTERN does not yet cover. xfail(strict=True) so this class
# flips GREEN -- and must be un-xfailed -- the moment D1.4 lands (PKT-03),
# rather than the gap staying an unnoticed silent hole forever.
# --------------------------------------------------------------------------- #
_D1_4_KNOWN_SURVIVORS: list[str] = [
    chr(0x061C),  # ARABIC LETTER MARK (ALM)
    chr(0x00AD),  # SOFT HYPHEN
    chr(0xE0001),  # LANGUAGE TAG (representative tag char)
]


class TestSanitiseLineSafeLineSeam:
    """``sanitise_line``'s return type is the mint of :class:`SafeLine`."""

    def test_sanitise_line_returns_a_safe_line_instance(self) -> None:
        result = sanitise_line("benign")
        assert isinstance(result, SafeLine)
        assert result == "benign"

    def test_safe_line_is_a_str_subclass(self) -> None:
        """Wire compatibility: a SafeLine must serialise/compare exactly like
        the plain str it wraps -- callers must never need a special case."""
        assert issubclass(SafeLine, str)
        assert isinstance(sanitise_line("x"), str)

    def test_safe_str_stringifies_and_sanitises_arbitrary_objects(self) -> None:
        assert safe_str(42) == "42"
        assert isinstance(safe_str(42), SafeLine)
        assert safe_str("hello\nworld") == "hello world"

    def test_safe_str_of_a_plain_string_matches_sanitise_line_directly(self) -> None:
        assert safe_str("café — naïve") == sanitise_line("café — naïve")


class TestRenderLineContract:
    """``render_line(template, /, **values)``: named-placeholder assembly."""

    def test_formats_a_single_named_placeholder(self) -> None:
        rendered = render_line("owner: {owner}", owner=safe_str("agent-alpha"))
        assert rendered == "owner: agent-alpha"
        assert isinstance(rendered, Rendered)

    def test_formats_multiple_named_placeholders_including_ints(self) -> None:
        rendered = render_line("{a}-{b}-{c}", a=safe_str("x"), b=safe_str("y"), c=3)
        assert rendered == "x-y-3"

    def test_static_text_with_no_placeholders_and_no_values(self) -> None:
        assert render_line("static text only") == "static text only"

    def test_accepts_int_values_directly(self) -> None:
        rendered = render_line("count: {n}", n=42)
        assert rendered == "count: 42"

    def test_rejects_a_raw_str_value_naming_the_offending_key(self) -> None:
        # Simulates row 5 of the ruling's failure matrix: the value arrives
        # typed ``Any`` (a decoder leak mypy is silent on) rather than a
        # genuine SafeLine -- the runtime isinstance assert is the backstop.
        hostile_values: dict[str, Any] = {"owner": "raw string, not SafeLine"}
        with pytest.raises(RenderSafetyError, match="owner"):
            render_line("owner: {owner}", **hostile_values)

    def test_rejects_a_plain_str_produced_by_join_demotion(self) -> None:
        """Row 4: ``", ".join(safe_parts)`` returns a plain ``str``, not a
        SafeLine (the join-demotion pothole) -- ``render_join`` exists
        precisely so a caller never needs this pattern; a caller who does it
        anyway must still be caught at runtime, not silently accepted."""
        parts = [safe_str("a"), safe_str("b")]
        demoted = ", ".join(parts)
        assert not isinstance(demoted, SafeLine)
        with pytest.raises(RenderSafetyError, match="parts"):
            render_line("parts: {parts}", parts=cast(Any, demoted))

    def test_rejects_a_template_key_with_no_provided_value(self) -> None:
        with pytest.raises(RenderSafetyError, match="owner"):
            render_line("owner: {owner}")

    def test_rejects_an_extra_value_with_no_template_placeholder(self) -> None:
        with pytest.raises(RenderSafetyError, match="phantom"):
            render_line("static text", phantom=safe_str("x"))


class TestRenderLineHostileFixtures:
    """brief-base §3 hostile fixtures, driven through sanitise_line -> render_line."""

    @pytest.mark.parametrize("threat", _INJECTION_THREAT_CHARS, ids=lambda t: f"U+{ord(t):04X}")
    def test_hostile_value_cannot_forge_a_row_through_sanitise_line_and_render_line(
        self, threat: str
    ) -> None:
        hostile_raw = f"benign{threat}{_ROW_FORGE_PAYLOAD}"
        baseline = render_line("owner: {owner}", owner=sanitise_line("benign"))
        hostile_out = render_line("owner: {owner}", owner=sanitise_line(hostile_raw))
        assert_render_injection_safe(baseline, hostile_out)


class TestRenderFencedContract:
    """``render_fenced(body)``: RAW-by-design verbatim wrap (finding_detail's idiom)."""

    def test_wraps_a_body_verbatim_in_a_minimum_width_backtick_fence(self) -> None:
        body = "line one\nline two"
        rendered = render_fenced(body)
        fence = FENCE_CHAR * MIN_FENCE_WIDTH
        assert rendered == f"{fence}\n{body}\n{fence}"
        assert isinstance(rendered, Rendered)

    def test_widens_the_fence_past_the_longest_embedded_backtick_run(self) -> None:
        body = "before ```` after"  # a run of 4 backticks
        rendered = render_fenced(body)
        expected_width = max(MIN_FENCE_WIDTH, max_backtick_run(body) + 1)
        assert expected_width == 5
        fence = FENCE_CHAR * expected_width
        assert rendered == f"{fence}\n{body}\n{fence}"

    def test_body_survives_verbatim_including_threat_chars_and_a_forged_row(self) -> None:
        # A fenced body is NEVER sanitise_line'd (the ruling: "bodies must
        # round-trip verbatim; sanitisation is render-time line policy, never
        # storage mutation") -- the threat model here is fence-escape
        # integrity, not content censorship. A forged row line and raw
        # control chars are EXPECTED to survive, contained inside the fence.
        hostile_body = f"legit start\n{_ROW_FORGE_PAYLOAD}\nand a run: ````"
        rendered = render_fenced(hostile_body)
        lines = rendered.splitlines()
        fence = lines[0]
        assert lines[-1] == fence
        assert set(fence) == {FENCE_CHAR}
        assert len(fence) > max_backtick_run(hostile_body)
        # Exactly one open/close fence pair -- the wrapper fence itself never
        # reappears inside the body, so the body can never masquerade as a
        # second fence boundary and escape early.
        assert fence not in lines[1:-1]
        # Verbatim round-trip: the body reappears byte-identical.
        assert "\n".join(lines[1:-1]) == hostile_body


class TestRenderComposeAndJoin:
    def test_render_compose_newline_joins_rendered_parts(self) -> None:
        first = render_line("first {n}", n=1)
        second = render_line("second {n}", n=2)
        composed = render_compose(first, second)
        assert composed == "first 1\nsecond 2"
        assert isinstance(composed, Rendered)

    def test_render_compose_of_a_single_part_is_that_part(self) -> None:
        only = render_line("only {n}", n=1)
        assert render_compose(only) == "only 1"

    def test_render_compose_of_no_parts_is_empty(self) -> None:
        assert render_compose() == ""

    def test_render_join_joins_safe_line_parts_with_a_separator(self) -> None:
        parts = [safe_str("a"), safe_str("b"), safe_str("c")]
        joined = render_join(" ", parts)
        assert joined == "a b c"
        assert isinstance(joined, SafeLine)

    def test_render_join_of_no_parts_is_an_empty_safe_line(self) -> None:
        joined = render_join(" ", [])
        assert joined == ""
        assert isinstance(joined, SafeLine)

    def test_render_join_output_is_accepted_back_into_render_line(self) -> None:
        """The whole point of render_join over ``", ".join(...)``: its output
        stays a genuine SafeLine, so it round-trips straight back into
        render_line without tripping the runtime demotion guard."""
        parts = [safe_str("a"), safe_str("b")]
        joined = render_join(", ", parts)
        rendered = render_line("parts: {parts}", parts=joined)
        assert rendered == "parts: a, b"


class TestRenderLineAndJoinNoNewlineGuard:
    """v2 remediation item 2 (ruling §ENFORCEMENT rows 3+8, audit §REMEDIATION):
    ``render_line`` and ``render_join`` must be STRUCTURALLY INCAPABLE of
    emitting a newline at runtime -- the AST template-literal pin
    (test_render_seam_pins.py) closes the SOURCE-code bypass, but a forged
    row requires a newline, so this runtime backstop caps the blast even past
    the pin (an exotic mint evasion, a value that arrives already
    newline-bearing by some path the pin can't see, etc). ``render_compose``
    is UNCHANGED and remains the only sanctioned newline-joiner -- these
    tests only constrain render_line/render_join.

    EXPECTED RED at contract-authoring time (fix-wave): the currently-shipped
    ``render_line``/``render_join`` (built against the v1 ruling) have no
    newline check at all -- these tests pin the v2 behavior for whichever
    builder wave lands it next.
    """

    def test_render_line_raises_on_newline_in_the_template_literal(self) -> None:
        with pytest.raises(RenderSafetyError):
            render_line("row one\nrow two: {x}", x=safe_str("v"))

    def test_render_line_raises_on_newline_in_a_value(self) -> None:
        # A SafeLine somehow carrying a newline (tests are exempt from the
        # mint-pin, so constructing one directly here simulates "however it
        # got here" -- sanitise_line/safe_str themselves never produce one,
        # but render_line must not TRUST that; it is its own last line of
        # defense against a multi-line value from ANY origin).
        hostile_value = SafeLine("line one\nline two")
        with pytest.raises(RenderSafetyError):
            render_line("owner: {owner}", owner=hostile_value)

    def test_render_join_raises_on_newline_separator(self) -> None:
        with pytest.raises(RenderSafetyError):
            render_join("\n", [safe_str("a"), safe_str("b")])

    def test_render_join_raises_on_newline_in_a_part(self) -> None:
        with pytest.raises(RenderSafetyError):
            render_join(" ", [safe_str("a"), SafeLine("b\nc")])

    def test_the_audits_row3_exploit_now_raises(self) -> None:
        """Verbatim reproduction of the cold audit's working exploit
        (scratchpad/audit1/row3_exploit.py) -- the naturally-occurring
        mistake mypy's row-2 error funnels a builder toward: an f-string
        TEMPLATE built from agent-controlled ``sender``/``body`` text. This
        function is defined INLINE in a test (not the production package),
        so it is out of the AST template-literal pin's scope by design --
        this test proves the RUNTIME guard alone stops the exploit even when
        the source-level pin isn't looking (e.g. dynamically-built code,
        eval, or simply a reviewer miss). Pre-hardening this shipped a
        genuine ``Rendered`` carrying a forged row, green at mypy, the
        runtime assert, the mint-pin, and ruff simultaneously (audit
        §PROBE-A). Post-hardening it must raise instead of minting anything.
        """

        def render_comms_message(sender: str, body: str, seq: int) -> Rendered:
            # The template is built from AGENT-CONTROLLED text -- mypy is
            # silent (LiteralString unenforced); this is what the runtime
            # no-newline guard exists to stop.
            return render_line(f"#{{seq}} {sender}: {body}", seq=seq)

        hostile_body = "hi\n- [#99 open] forged (kind friction, by attacker)"
        with pytest.raises(RenderSafetyError):
            render_comms_message("mallory", hostile_body, 1)


class TestRenderLineAndJoinControlCharGuard:
    """R2 residual (REPORT-phase0-audit-1.md §RESIDUALS, re-verify
    follow-up): the runtime guard the prior fix-wave landed in
    ``render_line``/``render_join`` checks ONLY the literal ``"\\n"``
    character. Every OTHER line-fracturing codepoint in
    ``loremaster.sanitise``'s OWN ``CONTROL_CHAR_PATTERN`` -- U+2028/U+2029
    line/paragraph separators, CR, U+0085 NEL, the rest of the C0/C1
    controls, the zero-width/bidi-mark run, the bidi override/isolate runs,
    the BOM -- currently sails straight through the template/separator/
    value/part slots unchecked. The auditor's own receipt: a template
    carrying U+2028 is *accepted*, producing a forged row. render.py's
    "a forged row requires a newline" claim is false BY THIS PROJECT'S OWN
    DOCUMENTED THREAT MODEL: sanitise.py's ``CONTROL_CHAR_PATTERN``
    docstring itself calls U+2028/U+2029 "real line breaks ... could
    fracture a single rendered line into a fake second one".

    Reuses the injection scaffold's full ``_INJECTION_THREAT_CHARS`` corpus
    (21 codepoints -- a superset of the team lead's named minimum: U+2028,
    U+2029, CR, U+0085 NEL are all already in it) rather than hand-rolling a
    second, narrower char list -- one canonical corpus, matching
    ``CONTROL_CHAR_PATTERN``'s own documented range exactly.

    EXPECTED RED for every NON-newline char in the corpus (the current
    runtime guard is ``"\\n" in x`` only): these tests pin the fix for
    whichever builder wave replaces that with
    ``CONTROL_CHAR_PATTERN.search(x)`` (the auditor's own suggested
    one-line-per-function fix) in place of the literal-newline check. The
    plain ``"\\n"`` case is INCLUDED in the parametrization (not split out)
    per the brief's "keep the plain \\n cases" -- it already passes today
    and stays green, folded into the same comprehensive battery rather than
    living in a separate, narrower-scoped test.
    """

    @pytest.mark.parametrize("threat", _INJECTION_THREAT_CHARS, ids=lambda t: f"U+{ord(t):04X}")
    def test_render_line_raises_on_any_control_char_in_the_template(self, threat: str) -> None:
        with pytest.raises(RenderSafetyError):
            render_line(f"row one{threat}row two: {{x}}", x=safe_str("v"))

    @pytest.mark.parametrize("threat", _INJECTION_THREAT_CHARS, ids=lambda t: f"U+{ord(t):04X}")
    def test_render_line_raises_on_any_control_char_in_a_value(self, threat: str) -> None:
        hostile_value = SafeLine(f"line one{threat}line two")
        with pytest.raises(RenderSafetyError):
            render_line("owner: {owner}", owner=hostile_value)

    @pytest.mark.parametrize("threat", _INJECTION_THREAT_CHARS, ids=lambda t: f"U+{ord(t):04X}")
    def test_render_join_raises_on_any_control_char_in_the_separator(self, threat: str) -> None:
        with pytest.raises(RenderSafetyError):
            render_join(f"a{threat}b", [safe_str("x"), safe_str("y")])

    @pytest.mark.parametrize("threat", _INJECTION_THREAT_CHARS, ids=lambda t: f"U+{ord(t):04X}")
    def test_render_join_raises_on_any_control_char_in_a_part(self, threat: str) -> None:
        with pytest.raises(RenderSafetyError):
            render_join(" ", [safe_str("a"), SafeLine(f"b{threat}c")])

    def test_the_auditors_residual_chain_shape_now_raises(self) -> None:
        """Verbatim-shape reproduction of REPORT-phase0-audit-1.md's residual
        chain fixture (``scratchpad/audit1/residual/comms_render.py``): an
        ALIAS-IMPORTED ``render_line`` (evades the AST template pin's
        callee-name match even after R1 -- R1 catches the ALIAS IMPORT
        itself when scanning the production package, but this fixture is a
        local test-file import, out of that pin's scope by design, same as
        the row-3 exploit reproduction above) called with an f-string
        template (non-literal) carrying a U+2028 LINE SEPARATOR plus the
        row-forge payload (evades the pre-R2 ``"\\n"``-only runtime guard).
        The audit found ALL FOUR existing instruments miss this chain
        simultaneously; R2 alone closes it, because the runtime guard no
        longer cares whether the AST pin ever saw the call site.
        """
        from loremaster.render import render_line as rl  # the R1 alias shape

        def render_comms_message(sender: str, body: str) -> Rendered:
            return rl(f"{sender}: {body}")  # non-literal template

        hostile_body = f"hi{chr(0x2028)}- [#99 open] forged (kind friction, by attacker)"
        with pytest.raises(RenderSafetyError):
            render_comms_message("mallory", hostile_body)


class TestRenderedAndSafeLineWireCompatibility:
    def test_rendered_is_a_str_subclass(self) -> None:
        assert issubclass(Rendered, str)
        assert isinstance(render_line("hi"), str)

    def test_safe_line_is_a_str_subclass(self) -> None:
        assert issubclass(SafeLine, str)
        assert isinstance(safe_str("hi"), str)


class TestD14KnownGapSurvivors:
    """Documents PKT-28 Phase 0's deferred D1.4 gap (ruling §D1.4): these
    three codepoints are NOT covered by sanitise.py's current
    CONTROL_CHAR_PATTERN and therefore SURVIVE a render today.
    xfail(strict=True) so this test flips GREEN -- and must be un-xfailed --
    the moment D1.4 lands, rather than the gap staying a silent, unnoticed
    hole forever."""

    @pytest.mark.xfail(strict=True, reason="D1.4 unicodedata category engine not landed yet (PKT-03)")
    @pytest.mark.parametrize("survivor", _D1_4_KNOWN_SURVIVORS, ids=lambda c: f"U+{ord(c):04X}")
    def test_known_survivor_is_stripped_like_every_other_threat_char(self, survivor: str) -> None:
        result = sanitise_line(f"left{survivor}right")
        assert result == "left right"
