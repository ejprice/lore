"""The typed render-assembly seam (PKT-28 Phase 0 render-safety ruling, v2 —
amended post cold-audit NO-GO, REPORT-phase0-audit-1.md).

Spec: docs/plans/v2/PKT-28-agent-comms.md's Phase-0 render-safety ruling
(§ENFORCEMENT, §BUILD-NOW items 1-2, v2). This module is where every NEW
agent-comms render (C1-C5) is assembled — existing task/finding/rollup
renders keep their manual ``sanitise_line``/``safe_str`` wraps for now (PKT-03
retypes them onto this seam; see the ruling's §DEFERRED).

**The enforcement story (v2 — four instruments, each covering a DIFFERENT
slot; no single one covers them all).** A ``class SafeLine(str)`` alone
enforces nothing: Python's f-strings and ``str.format`` happily coerce ANY
value via ``str()``/``format()``, so ``f"{raw}"`` is never a mypy error no
matter what type ``raw`` claims to be. A v1 draft of this module claimed
``typing.LiteralString`` closed the template slot at the mypy layer; the cold
audit (docs/design/2026-07-11-render-safety-foundation-ruling.md, its v2
CHANGELOG and §PROBE-A environment facts) refuted that with a working exploit
(``scratchpad/audit1/row3_exploit.py``): mypy 2.1.0 PARSES the
``LiteralString`` annotation and then ERASES it to plain ``str`` — PEP 675
enforcement is a pyright-only feature mypy has never shipped — so a hostile,
value-derived template sailed straight through mypy, the runtime assert (it
only checked values, never the template), the AST mint-pin (no ``Rendered``
construction to catch), and ruff, all at once. v2 replaces that leg with two
real instruments:

1. **mypy strict** guards the VALUE and RETURN legs only: a raw ``str`` value
   passed to :func:`render_line`/:func:`render_join` is rejected by the
   ``SafeLine | int`` parameter type; a raw f-string returned from a comms
   render path typed ``-> Rendered`` is rejected at the ``return`` (an
   f-string is a plain ``str``, never ``Rendered``). A subprocess-mypy
   meta-test (``test_render_mypy_layer.py``) pins the exact error codes for
   both rows, and pins row 3 as mypy-SILENT, so this claim is re-verified,
   never just restated.
2. **The AST template-literal pin** (``test_render_seam_pins.py``,
   ``TestRenderLineTemplateLiteralPin``) guards the TEMPLATE/SEPARATOR slot
   that mypy cannot: it asserts every ``render_line``/``render_join`` call in
   the production package passes a literal ``ast.Constant`` string there —
   whether positional or, for ``render_join``'s ``separator``, by keyword. A
   syntactic node check, so it cannot be defeated by aliasing a type could.
   The ``LiteralString`` annotation on ``template``/``separator`` below stays
   as documentation only; it enforces nothing at mypy.
3. **The runtime control-char assert** inside :func:`render_line` and
   :func:`render_join` (below) is the backstop past the AST pin: a forged row
   requires a line break, and both functions raise :class:`RenderSafetyError`
   if any :data:`~loremaster.sanitise.CONTROL_CHAR_PATTERN`-class character
   (v3/R2 — not just ``"\\n"``: CR, U+0085 NEL, U+2028/U+2029 line/paragraph
   separators, and the rest of sanitise.py's own hostile-char class are
   EQUALLY line-fracturing, per that module's own documented threat model)
   appears in the template/separator OR in any value/part — even one
   smuggled into the template string via interpolation BEFORE the pin ever
   sees the call site (the audit's exact exploit shape, and its R2 residual
   chain with a non-``\\n`` codepoint). This makes both functions
   structurally incapable of emitting any line-breaking or control character
   at runtime; :func:`render_compose` is the only sanctioned multi-line
   joiner.
4. **The AST mint-pin** (``test_render_seam_pins.py``,
   ``TestSafeLineRenderedMintPin``) guards MINTING itself: a bare or
   module-qualified ``SafeLine(...)``/``Rendered(...)`` construction, a
   string-form or bare ``cast(...)`` naming either type, an import-alias of
   either name, or a subclass of either type — all constructed/defined
   outside ``sanitise.py``/this module — are flagged, closing routes a type
   checker cannot see (constructing a ``str`` subclass from a ``str`` is
   always legal Python).

Absolute proof is not claimed (a ``# type: ignore``, an ``Any``-typed leak, or
an exotic mint evasion outside all four instruments' scope can still defeat a
single layer) — the property actually delivered is that no single forgotten
wrap can silently ship a forged row: it must simultaneously defeat whichever
instrument(s) cover that slot (mypy for the value/return legs; the AST
template pin AND the runtime control-char assert together for the
template/separator slot; the mint-pin for a forged construction) AND the
hostile injection battery, which exercises every registered render's actual
output end-to-end.
"""

from __future__ import annotations

import string
from collections.abc import Iterable
from typing import LiteralString

from loremaster.sanitise import (
    CONTROL_CHAR_PATTERN,
    FENCE_CHAR,
    MIN_FENCE_WIDTH,
    SafeLine,
    max_backtick_run,
)

# Reused across calls: ``string.Formatter`` carries no per-call state, and
# ``.parse()`` is what we use to enumerate a template's named placeholders
# without ever calling ``.format()`` before validation has run.
_TEMPLATE_FORMATTER = string.Formatter()


class Rendered(str):
    """A ``str`` PROVEN to have been assembled ONLY via three of this
    module's four assembly verbs: :func:`render_line`, :func:`render_fenced`,
    :func:`render_compose` (the fourth verb, :func:`render_join`, mints
    :class:`~loremaster.sanitise.SafeLine`, not ``Rendered`` — see its own
    docstring) — see the module docstring's enforcement story. A
    ``pytest``-time AST scan (``test_render_seam_pins.py``,
    ``TestSafeLineRenderedMintPin``) fails if ``Rendered(...)``/
    ``cast(Rendered, ...)``, an import-alias of ``Rendered``, or a subclass
    of ``Rendered`` appears anywhere else in the production package.
    """


class RenderSafetyError(Exception):
    """Raised by :func:`render_line`/:func:`render_join` when a call would
    smuggle an unproven, mismatched, or multi-line value into a served
    render: a value that is not ``SafeLine`` or ``int`` (row 5 of the
    ruling's failure matrix — the runtime backstop for an ``Any``-typed leak
    mypy cannot see), a template placeholder with no matching value, a value
    with no matching template placeholder (a typo guard in both directions),
    or a :data:`~loremaster.sanitise.CONTROL_CHAR_PATTERN`-class character
    anywhere in the template/separator/value/part (row 8 — v3/R2, the
    runtime backstop past the AST template-literal pin; widened from a bare
    ``"\n"`` check to the full line-breaking/control-char class sanitise.py
    itself already treats as hostile). The message always names the
    offending key/site so the failure is actionable, never just "something
    was wrong".
    """


def _template_placeholder_names(template: str) -> set[str]:
    """The set of named ``{placeholder}`` identifiers inside ``template``.

    Uses ``string.Formatter().parse()`` rather than a hand-rolled regex so
    this agrees with what ``str.format`` itself considers a field (format
    specs, literal braces, etc.) without re-deriving that parser. Attribute/
    index access inside a field (``{a.b}``, ``{a[0]}``) is not a supported
    shape for this seam's named-placeholder templates, but is reduced to its
    base name defensively rather than raising here — the goal is a precise,
    named-placeholder assembly language, not a general ``str.format`` clone.
    """
    names: set[str] = set()
    for _literal_text, field_name, _format_spec, _conversion in _TEMPLATE_FORMATTER.parse(template):
        if not field_name:
            continue
        base_name = field_name.split(".")[0].split("[")[0]
        if base_name:
            names.add(base_name)
    return names


def render_line(template: LiteralString, /, **values: SafeLine | int) -> Rendered:
    """Assemble ONE rendered line from a literal template + named, proven-safe
    values (the ruling's §ENFORCEMENT rows 1, 3, 5, 8 — v2).

    ``template`` carries a :class:`~typing.LiteralString` annotation as
    DOCUMENTATION ONLY — mypy 2.1.0 parses that annotation and then erases it
    to plain ``str``, so it enforces NOTHING at the call site (audit
    §PROBE-A: PEP 675 checking is a pyright-only feature mypy has never
    shipped). The real guards on this slot are (1) the AST template-literal
    pin (``test_render_seam_pins.py``'s ``TestRenderLineTemplateLiteralPin``),
    which asserts every call in the production package passes a literal
    ``ast.Constant`` string here, and (2) the runtime check below: any
    :data:`~loremaster.sanitise.CONTROL_CHAR_PATTERN`-class character
    anywhere in ``template`` raises :class:`RenderSafetyError` immediately
    (v3/R2 — widened from a bare ``"\n"`` check: CR, U+0085 NEL,
    U+2028/U+2029 line/paragraph separators, and the rest of sanitise.py's
    own hostile-char class are EQUALLY line-fracturing, per that module's
    own documented threat model) — which also stops a template built by
    interpolating agent-controlled text at a call site the AST pin can't see
    (the cold audit's row-3 exploit shape, and its R2 residual chain: a
    control character arrives embedded IN the template string itself, before
    ``render_line`` ever inspects the argument node).

    Every value must be a :class:`~loremaster.sanitise.SafeLine` or an
    ``int`` (``bool`` is accepted too: it is an ``int`` subclass in Python,
    and no served render needs to reject it specially); this IS enforced by
    mypy at the parameter type, with a runtime ``isinstance`` assert as the
    backstop for a value that arrives typed ``Any`` (e.g. a decoder leak
    mypy is silent on — row 5). Every ``SafeLine`` value is ALSO checked for
    an embedded CONTROL_CHAR_PATTERN-class character at runtime (row 8) —
    the backstop past ``sanitise_line``/``safe_str`` themselves (which never
    produce one) for a value that arrived that way by some other path — so
    ``render_line`` is structurally incapable of emitting any line-breaking
    or control character; :func:`render_compose` is the only sanctioned
    newline-joiner.

    The value keys must EXACTLY cover the template's placeholders: a
    placeholder with no value, or a value with no placeholder, is a
    :class:`RenderSafetyError` naming the offending key(s) — a typo guard in
    both directions, not just a missing-value guard.
    """
    if CONTROL_CHAR_PATTERN.search(template):
        raise RenderSafetyError(
            f"render_line template {template!r} contains a line-breaking or "
            f"control character (sanitise.py's CONTROL_CHAR_PATTERN class) — "
            f"render_line is structurally single-line; use render_compose "
            f"to join multiple already-Rendered lines instead"
        )
    template_keys = _template_placeholder_names(template)
    provided_keys = set(values.keys())

    missing_keys = template_keys - provided_keys
    if missing_keys:
        raise RenderSafetyError(
            f"render_line template {template!r} is missing a value for "
            f"placeholder(s) {sorted(missing_keys)!r}"
        )
    extra_keys = provided_keys - template_keys
    if extra_keys:
        raise RenderSafetyError(
            f"render_line received value(s) for {sorted(extra_keys)!r} with "
            f"no matching placeholder in template {template!r}"
        )
    for key, value in values.items():
        if not isinstance(value, SafeLine | int):
            raise RenderSafetyError(
                f"render_line value for {key!r} is not a SafeLine or int "
                f"(got {type(value).__name__}) — forgot a sanitise_line/"
                f"safe_str wrap, or is this a plain str produced by "
                f"', '.join(...) (use render_join instead)?"
            )
        if isinstance(value, str) and CONTROL_CHAR_PATTERN.search(value):
            raise RenderSafetyError(
                f"render_line value for {key!r} contains a line-breaking or "
                f"control character (sanitise.py's CONTROL_CHAR_PATTERN "
                f"class) — render_line is structurally single-line; a "
                f"multi-line value can only reach a served render through "
                f"render_fenced (a verbatim body) or render_compose "
                f"(already-Rendered lines)"
            )
    return Rendered(template.format(**values))


def render_fenced(body: str) -> Rendered:
    """Wrap ``body`` VERBATIM inside a backtick fence (the pre-existing
    ``_render_finding_detail`` idiom, server.py — see the ruling's
    §C1-C5-AUTHORING rule 3).

    ``body`` is deliberately RAW, never ``sanitise_line``'d: a fenced body
    (a brief/message body) must round-trip byte-identical, and sanitisation
    is render-time LINE policy, not storage-mutation policy. The fence itself
    is sized ``max(MIN_FENCE_WIDTH, max_backtick_run(body) + 1)`` — strictly
    longer than any backtick run already inside ``body`` — so an embedded
    fence-shaped run of backticks can never close the fence early and let the
    rest of the body escape as un-fenced, forgeable text.
    """
    fence = FENCE_CHAR * max(MIN_FENCE_WIDTH, max_backtick_run(body) + 1)
    return Rendered(f"{fence}\n{body}\n{fence}")


def render_compose(*parts: Rendered) -> Rendered:
    """Newline-join already-``Rendered`` parts into one composite render.

    Only accepts :class:`Rendered` parts — each must already have been
    assembled via :func:`render_line`/:func:`render_fenced`/this function, so
    composing never itself becomes a bypass route for an unproven ``str``.
    """
    return Rendered("\n".join(parts))


def render_join(separator: LiteralString, parts: Iterable[SafeLine]) -> SafeLine:
    """Join ``SafeLine`` parts with ``separator``, staying a ``SafeLine``.

    Exists precisely so a caller never needs ``", ".join(safe_parts)`` — that
    idiom's result is a plain ``str`` (the "join-demotion" pothole: ``join``
    is not seam-aware, so it demotes every input back to an unproven type)
    even when every part joined was itself already safe.

    ``separator`` carries the same documentation-only ``LiteralString``
    annotation as :func:`render_line`'s ``template`` — mypy does not enforce
    it (audit §PROBE-A); the AST template-literal pin
    (``test_render_seam_pins.py``) is the real guard here, checked whether
    ``separator`` is passed positionally or by keyword. Any
    :data:`~loremaster.sanitise.CONTROL_CHAR_PATTERN`-class character in
    ``separator`` OR in any part raises :class:`RenderSafetyError` at
    runtime (v3/R2, ruling §ENFORCEMENT row 8 — widened from a bare
    ``"\n"`` check: CR, U+0085 NEL, U+2028/U+2029 line/paragraph separators,
    and the rest of sanitise.py's own hostile-char class are EQUALLY
    line-fracturing, per that module's own documented threat model): a
    line-breaking separator (or a line-breaking part) would mint a
    multi-line ``SafeLine`` that would then sail straight past
    :func:`render_line`'s per-value check and emit extra lines — rejecting
    it here holds ``SafeLine``'s one-logical-line invariant BY CONSTRUCTION
    at every mint, not just at ``sanitise_line``/``safe_str``.
    """
    if CONTROL_CHAR_PATTERN.search(separator):
        raise RenderSafetyError(
            f"render_join separator {separator!r} contains a line-breaking "
            f"or control character (sanitise.py's CONTROL_CHAR_PATTERN "
            f"class) — such a separator would mint a multi-line SafeLine, "
            f"defeating the one-line invariant every SafeLine mint "
            f"otherwise holds"
        )
    materialised_parts = list(parts)
    for part in materialised_parts:
        if CONTROL_CHAR_PATTERN.search(part):
            raise RenderSafetyError(
                f"render_join part {part!r} contains a line-breaking or "
                f"control character (sanitise.py's CONTROL_CHAR_PATTERN "
                f"class) — every SafeLine must stay one logical line; "
                f"sanitise_line/safe_str already collapse these, so a part "
                f"carrying one here means it arrived by some other path"
            )
    return SafeLine(separator.join(materialised_parts))
