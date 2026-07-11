"""The shared render-sanitisation seam (finding #34); imported tree-wide so no
renderer re-hand-rolls or skips the launder.
"""

from __future__ import annotations

import re

# item 10: the CommonMark backtick fence character, and the standard minimum fence
# width. The wrapper fence must be a backtick run LONGER than any run inside the
# source (so a ``` embedded in the source cannot close the fence early), bounded
# below by the three-backtick CommonMark minimum.
FENCE_CHAR = "`"
MIN_FENCE_WIDTH = 3

# item 10 (audit followup): the render-sanitiser's hostile-char class — C0
# controls (incl. TAB, LF, CR, the ANSI/OSC introducer ESC ``\x1b`` and its BEL
# terminator ``\x07``), DEL, and the C1 controls, PLUS several Unicode
# sub-ranges that are not control characters but are equally capable of
# corrupting a rendered citation/memory line: the bidi override (U+202A-202E)
# and isolate (U+2066-2069) formatting characters plus the bidi mark pair
# U+200E LEFT-TO-RIGHT MARK / U+200F RIGHT-TO-LEFT MARK (can visually rewrite
# the line in a bidi-aware terminal/UI); zero-width characters (U+200B ZERO
# WIDTH SPACE, U+200C ZERO WIDTH NON-JOINER, U+200D ZERO WIDTH JOINER,
# U+2060 WORD JOINER, U+FEFF ZERO WIDTH NO-BREAK SPACE/BOM, which can hide
# characters inside it); and U+2028 LINE SEPARATOR / U+2029 PARAGRAPH
# SEPARATOR (real line breaks to a bidi-aware terminal or browser-rendered UI
# even though neither is ``\n``, so left uncollapsed they could fracture a
# single rendered line into a fake second one). A run of any of these
# collapses to a single space so a hostile identity/path/memory text stays
# one logical, visually-honest line and cannot smuggle terminal-framing, a
# fake second citation, or a hidden/reordered payload into a rendered field.
# U+200B-200F is one contiguous run (ZWS/ZWNJ/ZWJ/LRM/RLM); U+2060 sits
# outside the isolate block (U+2066-2069) so it stays a standalone codepoint
# rather than widening that range to cover unrelated invisible operators.
CONTROL_CHAR_PATTERN = re.compile(
    r"[\x00-\x1f\x7f-\x9f\u200b-\u200f\u2028-\u2029\u202a-\u202e\u2060\u2066-\u2069\ufeff]+"
)
# item 10: matches a run of consecutive backticks, for sizing the wrapper fence.
BACKTICK_RUN_PATTERN = re.compile(r"`+")


def sanitise_line(text: str) -> str:
    """Collapse control chars / newlines in a NON-fenced rendered field (item 10).

    Any run of hostile characters (:data:`CONTROL_CHAR_PATTERN` — C0/C1
    controls, DEL, incl. an ANSI/OSC ``ESC`` introducer and a newline, PLUS bidi
    override/isolate/mark, zero-width (incl. ZWNJ/ZWJ/WORD JOINER), and
    line/paragraph separator characters)
    becomes a single space, and leading/trailing whitespace is stripped, so the
    field renders as a single logical, visually-honest line that cannot break
    the citation line it sits on, escape a fence, or smuggle a hidden/reordered
    payload. Source *bodies* are NOT run through this — they stay verbatim
    inside a backtick fence.
    """
    return CONTROL_CHAR_PATTERN.sub(" ", text).strip()


def max_backtick_run(text: str) -> int:
    """The length of the longest run of consecutive backticks anywhere in ``text``."""
    return max((len(run) for run in BACKTICK_RUN_PATTERN.findall(text)), default=0)
