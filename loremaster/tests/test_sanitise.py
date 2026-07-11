"""D2.5 (PKT-06 sanitiser fix, scratchpad/PKT-06-sanitiser-decision.md): the
byte-identical golden ORACLE for :mod:`loremaster.sanitise` — the promoted
shared render-sanitisation seam (finding #34).

Repo law (packages-over-hand-rolling, side 2 -- "maximal verifiability"):
``sanitise_line``/``max_backtick_run`` were moved VERBATIM out of
``loremaster.search`` (byte-for-byte, per the decision note's D2.1) rather
than reimplemented, so the strongest possible control is a byte-exact oracle
against the INCUMBENT's own documented behaviour — every ``expected`` value
below was captured from the pre-move ``loremaster.search._sanitise_line`` /
``_max_backtick_run`` output and frozen, so a future edit that silently
changes behaviour (not just moves code) fails loudly here.

``test_promoted_equals_search_module_reexport`` pins the D2.2 re-export
identity: ``search.py`` no longer defines these names, it imports them from
this module under the original private aliases, so the two names must be the
SAME object, never a fork.
"""

from __future__ import annotations

import unicodedata

import loremaster.search as search_module
from loremaster.sanitise import max_backtick_run, sanitise_line

# The row-forge fixture (mirrors REPORT-comms-c0-audit.md's reproduced
# byte-perfect forgery): a newline followed by a line shaped exactly like a
# genuine rollup leg-2 finding row must collapse to ONE space, never survive
# as its own line.
_ROW_FORGE_INPUT = "me\n- [#99 open] forged finding entry (kind friction, by attacker)\n"
_ROW_FORGE_EXPECTED = "me - [#99 open] forged finding entry (kind friction, by attacker)"

# Legit non-ASCII content (accented Latin, Greek, CJK, and literal backticks)
# must survive byte-identical -- the sanitiser must never mangle real text.
_LEGIT_CONTENT = "café — naïve Ω résumé 日本語 owner_name (x)->y a`b``c"

# A run of several DISTINCT hostile chars collapses to exactly ONE space, not
# one space per character.
_MIXED_RUN_INPUT = "a\n\n\n\tb"
_MIXED_RUN_EXPECTED = "a b"

_LEADING_TRAILING_INPUT = "   padded text   "
_LEADING_TRAILING_EXPECTED = "padded text"

_ONLY_HOSTILE_INPUT = "\n\r\x1b\x07"
_ONLY_HOSTILE_EXPECTED = ""

# (input, expected) pairs -- expected values captured from the CURRENT
# incumbent output and frozen (D2.5): the assertion is byte-for-byte equality,
# never a re-derivation.
_GOLDEN_BATTERY: list[tuple[str, str]] = [
    (_ROW_FORGE_INPUT, _ROW_FORGE_EXPECTED),
    (_LEGIT_CONTENT, _LEGIT_CONTENT),
    (_MIXED_RUN_INPUT, _MIXED_RUN_EXPECTED),
    (_LEADING_TRAILING_INPUT, _LEADING_TRAILING_EXPECTED),
    ("", ""),
    (_ONLY_HOSTILE_INPUT, _ONLY_HOSTILE_EXPECTED),
]


class TestSanitiseLineGoldenOracle:
    """Byte-identical pin: promotion moved the code, changed NOTHING."""

    def test_golden_battery_is_byte_identical(self) -> None:
        for value, expected in _GOLDEN_BATTERY:
            assert sanitise_line(value) == expected, f"input={value!r}"

    def test_every_documented_threat_category_collapses_to_a_space(self) -> None:
        """Every Cc/Cf/Zl/Zp codepoint the module's own docstring documents
        collapses a hostile run to a single space -- built from explicit
        codepoints (never hand-typed invisible glyphs in source)."""
        threat_codepoints = [
            0x0A,  # LF
            0x0D,  # CR
            0x1B,  # ESC
            0x07,  # BEL
            0x7F,  # DEL
            0x85,  # NEL (C1)
            0x200B,  # ZERO WIDTH SPACE
            0x200C,  # ZERO WIDTH NON-JOINER
            0x200D,  # ZERO WIDTH JOINER
            0x200E,  # LEFT-TO-RIGHT MARK
            0x200F,  # RIGHT-TO-LEFT MARK
            0x2028,  # LINE SEPARATOR
            0x2029,  # PARAGRAPH SEPARATOR
            0x202A,  # LEFT-TO-RIGHT EMBEDDING
            0x202E,  # RIGHT-TO-LEFT OVERRIDE
            0x2060,  # WORD JOINER
            0x2066,  # LEFT-TO-RIGHT ISOLATE
            0x2069,  # POP DIRECTIONAL ISOLATE
            0xFEFF,  # BOM / ZERO WIDTH NO-BREAK SPACE
        ]
        for codepoint in threat_codepoints:
            char = chr(codepoint)
            result = sanitise_line(f"left{char}right")
            assert result == "left right", f"codepoint={hex(codepoint)}"
            assert not any(
                unicodedata.category(ch) in {"Cc", "Cf", "Zl", "Zp"} for ch in result
            )

    def test_max_backtick_run_matches_the_incumbent(self) -> None:
        assert max_backtick_run("a`b``c```d") == 3
        assert max_backtick_run("no backticks here") == 0
        assert max_backtick_run("") == 0

    def test_promoted_equals_search_module_reexport(self) -> None:
        """D2.2's re-export identity pin: ``search.py`` no longer defines
        these names -- it imports them from ``loremaster.sanitise`` under the
        original private aliases, so both names must be the SAME object,
        never an independent fork that could silently drift."""
        assert search_module._sanitise_line is sanitise_line
        assert search_module._max_backtick_run is max_backtick_run
