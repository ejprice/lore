"""CONTRACT — ``lorerunes.normalize_email``: ONE answer to *"are these the same person?"*.

Packet 39 (design ``docs/design/2026-07-31-packet39-google-oauth.md`` §5) puts the
email normaliser in ``lorerunes`` because two call sites must not be able to disagree:

* the ROSTER PARSER normalises each allowlist line at parse time (R12), and
* the VERIFIER normalises the email Google reports at verification time.

If those two answers ever diverge, an operator who wrote ``JHarrington@Example.com``
in the roster silently stops matching the person Google reports as
``jharrington@example.com`` — a fail-CLOSED divergence that looks like "the allowlist
is broken" and gets debugged by widening the allowlist, which is a fail-OPEN fix. So
the predicate has one home and one behaviour.

RULED SEMANTICS (design §5): ``NFKC → casefold → strip``.

WHAT THIS CONTRACT PINS, and the wrong build each pin discriminates against:

* **Case folding admits real-world capitalisation** — a build that only ``lower()``s
  passes ASCII fixtures and fails on ``ß``/``İ``; ``casefold`` is a stronger, ruled
  fold and the Turkish/German fixtures below force it.
* **NFKC does NOT conflate homographs.** A Cyrillic ``е`` (U+0435) is not a Latin
  ``e``; a build that "normalises harder" (e.g. NFKD + strip-combining, or a
  confusables fold) would admit ``еjprice@firehawktransam.org`` — a spoofed identity
  that Google would never issue but that an operator might paste into the roster from
  a phishing mail. The non-match is pinned as a SECURITY property, not a curiosity.
* **NFKC DOES fold compatibility forms** — fullwidth ``＠``/``ａ`` and the ligature
  ``ﬁ`` are real IME/paste artefacts in an operator-curated file. A build that skips
  NFKC entirely passes every ASCII fixture in this file and fails only on the day an
  operator pastes from a Japanese keyboard.
* **Whitespace is stripped, interior content is NOT touched.** A roster line arrives
  with a trailing newline; a build that ``replace(" ", "")`` instead of ``strip()``
  would silently mangle an address containing a (quoted, legal) space.
* **The function is a CLASSIFIER-NORMALISER, never a rewriter of identity.** Gmail
  dot- and plus-aliasing are deliberately NOT stripped (design §5, a documented
  bound): ``ejprice+lore@gmail.com`` and ``ejprice@gmail.com`` are DIFFERENT roster
  entries. A build that "helpfully" canonicalises gmail aliases silently admits every
  plus-alias of every listed gmail address — an allowlist widening nobody authorised.

All values below are production-shaped: real firehawktransam.org / pricepaper.com
addresses of the shape this roster will actually carry (design R2/R12), not ``a@b``.
"""

from __future__ import annotations

import unicodedata

import pytest

# ⚠ ``lorerunes`` SYMBOLS ARE IMPORTED INSIDE EACH TEST, NOT AT MODULE LEVEL.
# This contract is written before the implementation exists, so a module-level import
# would turn every pin in this file into ONE collection error — and a collection error
# yields NO node ids, which is exactly what ``scripts/mutation_proof.py`` needs to
# declare its expected-RED set from ``--collect-only``. Function-local imports keep the
# module collectible and make each pin fail on its own terms.


# --------------------------------------------------------------------------- #
# Production-realistic fixture values. These are the SHAPES the roster and the
# Google tokeninfo response actually carry (design §2/R12): a firehawk address the
# operator owns, a pricepaper address from the co-tenant org (R2 — the shared OAuth
# client means both orgs' identities reach the same tokeninfo response).
# --------------------------------------------------------------------------- #
OPERATOR_EMAIL = "ejprice@firehawktransam.org"
SECOND_PRINCIPAL_EMAIL = "dana.whitfield@pricepaper.com"

# The same identity as it is plausibly TYPED by an operator into a flat file, or
# reported by a Google Workspace tokeninfo response: mixed case + a trailing newline
# from the editor.
OPERATOR_EMAIL_AS_TYPED = "  EJPrice@FireHawkTransAm.ORG\n"

# A Cyrillic homograph of the operator's address: the leading ``е`` is U+0435
# CYRILLIC SMALL LETTER IE, not U+0065. Visually identical in most fonts.
CYRILLIC_HOMOGRAPH_EMAIL = "еjprice@firehawktransam.org"

# Compatibility (NFKC-foldable) forms an IME or a paste can genuinely produce:
# FULLWIDTH COMMERCIAL AT (U+FF20) and FULLWIDTH LATIN SMALL LETTER A (U+FF41).
FULLWIDTH_AT_EMAIL = "dana.whitfield＠pricepaper.com"
FULLWIDTH_LETTER_EMAIL = "dａna.whitfield@pricepaper.com"


class TestNormalizeEmailFoldsCase:
    """Case is not identity: the roster and Google may disagree on capitalisation."""

    def test_mixed_case_address_folds_to_lowercase(self) -> None:
        # Arrange: the operator's own address, capitalised the way a human types it.
        # Act
        from lorerunes import normalize_email
        normalised = normalize_email("EJPrice@FireHawkTransAm.ORG")
        # Assert: the expected value is the address as Google reports it — an
        # independent source (the tokeninfo ``email`` field is always lowercased by
        # Google), not a restatement of the implementation.
        assert normalised == OPERATOR_EMAIL

    def test_already_normalised_address_is_unchanged(self) -> None:
        # The positive CONTROL for the fold: a normalised address must survive
        # byte-identical, or the normaliser is mangling rather than folding.
        from lorerunes import normalize_email
        assert normalize_email(OPERATOR_EMAIL) == OPERATOR_EMAIL

    def test_uses_casefold_not_lower_for_the_german_sharp_s(self) -> None:
        # ``"ß".lower()`` is ``"ß"``; ``"ß".casefold()`` is ``"ss"``. A build that
        # reaches for ``lower()`` passes every ASCII fixture above and fails here —
        # this is the pin that distinguishes the two.
        from lorerunes import normalize_email
        assert normalize_email("Straße@example.de") == "strasse@example.de"

    def test_uses_casefold_not_lower_for_the_dotted_capital_i(self) -> None:
        # U+0130 LATIN CAPITAL LETTER I WITH DOT ABOVE casefolds to ``i`` + U+0307
        # (a combining dot), which ``lower()`` also produces on most builds — so this
        # fixture is here for the OTHER direction: it proves the normaliser does not
        # silently drop combining marks (a "normalise harder" build would).
        from lorerunes import normalize_email
        folded = normalize_email("İSTANBUL@example.com.tr")
        assert folded == "İSTANBUL@example.com.tr".casefold()
        assert "̇" in folded, (
            "the combining dot above must survive: dropping combining marks is a "
            "confusables fold, not a casefold, and it collapses distinct identities"
        )


class TestNormalizeEmailStripsWhitespaceOnly:
    """Surrounding whitespace is noise; interior content is identity."""

    def test_roster_line_with_surrounding_whitespace_and_newline_normalises(self) -> None:
        # A flat-file roster line arrives with a trailing newline and, often, leading
        # indentation. Both are editor artefacts, not identity.
        from lorerunes import normalize_email
        assert normalize_email(OPERATOR_EMAIL_AS_TYPED) == OPERATOR_EMAIL

    def test_interior_whitespace_is_preserved_not_squashed(self) -> None:
        # A build that does ``"".join(value.split())`` instead of ``.strip()`` would
        # silently rewrite this value into a DIFFERENT address. The parser rejects
        # this line later (R7 — it is malformed), but the normaliser must not be the
        # thing that hides it.
        from lorerunes import normalize_email
        assert normalize_email("  first last@example.com  ") == "first last@example.com"

    def test_non_ascii_unicode_whitespace_is_stripped(self) -> None:
        # NBSP (U+00A0) and IDEOGRAPHIC SPACE (U+3000) are what a paste from a
        # rendered web page or a CJK IME actually leaves around an address. A build
        # that hand-rolls the strip as ``value.replace(" ", "")`` — an easy way to
        # "be safe about whitespace" — leaves both in place and denies the principal
        # forever, with no diagnosis anywhere.
        from lorerunes import normalize_email
        padded = f"\u00a0\u3000{OPERATOR_EMAIL}\u00a0"
        assert padded != OPERATOR_EMAIL, "the fixture must actually carry the padding"
        assert normalize_email(padded) == OPERATOR_EMAIL


class TestNormalizeEmailAppliesNfkcCompatibilityFolding:
    """NFKC folds compatibility forms an operator can genuinely paste."""

    def test_fullwidth_at_sign_folds_to_ascii_at(self) -> None:
        # Independent oracle: the stdlib's own NFKC mapping, not our implementation.
        from lorerunes import normalize_email
        assert unicodedata.normalize("NFKC", "＠") == "@"
        assert normalize_email(FULLWIDTH_AT_EMAIL) == SECOND_PRINCIPAL_EMAIL

    def test_fullwidth_letter_folds_to_ascii_letter(self) -> None:
        from lorerunes import normalize_email
        assert unicodedata.normalize("NFKC", "ａ") == "a"
        assert normalize_email(FULLWIDTH_LETTER_EMAIL) == SECOND_PRINCIPAL_EMAIL

    def test_ligature_folds_to_its_component_letters(self) -> None:
        # U+FB01 LATIN SMALL LIGATURE FI — what some PDF copy-paste produces.
        from lorerunes import normalize_email
        assert normalize_email("ﬁnance@pricepaper.com") == "finance@pricepaper.com"


class TestNormalizeEmailDoesNotConflateHomographs:
    """SECURITY: visually identical is not identical. NFKC must not fold homographs."""

    def test_cyrillic_lookalike_does_not_normalise_to_its_latin_twin(self) -> None:
        # The attack this pin exists for: an operator pastes a homograph address from
        # a phishing mail into the roster, and a "normalise harder" build makes it
        # match the real principal Google reports — or vice versa, admitting a
        # spoofed identity. NFKC deliberately does NOT fold script confusables.
        from lorerunes import normalize_email
        assert normalize_email(CYRILLIC_HOMOGRAPH_EMAIL) != normalize_email(OPERATOR_EMAIL)

    def test_the_homograph_fixture_is_actually_a_homograph(self) -> None:
        # The CONTROL for the pin above: prove the two strings really are distinct
        # code points that look alike, so the non-match is meaningful rather than a
        # typo in the fixture. Without this, the pin above could pass because the
        # fixture is simply a different address.
        assert CYRILLIC_HOMOGRAPH_EMAIL != OPERATOR_EMAIL
        assert len(CYRILLIC_HOMOGRAPH_EMAIL) == len(OPERATOR_EMAIL)
        assert CYRILLIC_HOMOGRAPH_EMAIL[1:] == OPERATOR_EMAIL[1:]
        assert unicodedata.name(CYRILLIC_HOMOGRAPH_EMAIL[0]).startswith("CYRILLIC")
        assert unicodedata.name(OPERATOR_EMAIL[0]).startswith("LATIN")

    def test_greek_lookalike_domain_does_not_normalise_to_its_latin_twin(self) -> None:
        # A second script, so the property is pinned over more than one homograph
        # family (the value-monoculture law: one Cyrillic fixture could pass a build
        # that special-cases Cyrillic).
        from lorerunes import normalize_email
        greek_omicron_domain = "ejprice@firehawktransam.οrg"
        assert normalize_email(greek_omicron_domain) != normalize_email(OPERATOR_EMAIL)


class TestNormalizeEmailIsNotAnAliasCanonicaliser:
    """The DOCUMENTED BOUND (design §5): gmail dot/plus aliasing is NOT stripped."""

    def test_plus_alias_is_a_distinct_identity(self) -> None:
        # A build that canonicalises gmail aliases silently admits EVERY plus-alias of
        # every listed address — an allowlist widening nobody authorised. The roster
        # line must be the address Google reports, verbatim-after-normalisation.
        from lorerunes import normalize_email
        assert normalize_email("ejprice+lore@gmail.com") != normalize_email("ejprice@gmail.com")

    def test_dotted_local_part_is_a_distinct_identity(self) -> None:
        from lorerunes import normalize_email
        assert normalize_email("e.j.price@gmail.com") != normalize_email("ejprice@gmail.com")

    def test_subaddressing_on_a_workspace_domain_is_also_distinct(self) -> None:
        # Same bound on a non-gmail domain, so a build cannot special-case gmail and
        # still pass (value monoculture).
        from lorerunes import normalize_email
        assert normalize_email("ejprice+ci@firehawktransam.org") != OPERATOR_EMAIL


class TestNormalizeEmailDegenerateInputs:
    """Hostile / degenerate inputs classify cleanly rather than raising."""

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "   ",
            "\n",
            "\t  ",
        ],
    )
    def test_blank_shapes_normalise_to_the_empty_string_without_raising(
        self, value: str
    ) -> None:
        # The normaliser CLASSIFIES; the roster parser and the config validator are
        # what REFUSE. A normaliser that raised here would force every caller to
        # guard, and the guard is where the two call sites would drift apart.
        from lorerunes import normalize_email
        assert normalize_email(value) == ""

    def test_a_value_carrying_a_newline_keeps_it_for_the_parser_to_refuse(self) -> None:
        # An interior newline is a FORGERY vector for anything that renders a roster
        # line into a log record (see the roster parser contract's hostile fixture).
        # The normaliser must not silently delete it — deleting it would launder the
        # forgery into a well-formed entry.
        from lorerunes import normalize_email
        assert "\n" in normalize_email("ejprice@firehawktransam.org\nadmin@evil.example")

    def test_the_result_is_idempotent(self) -> None:
        # Normalising twice must equal normalising once, or the roster's stored form
        # and the runtime form can disagree by one application.
        from lorerunes import normalize_email
        once = normalize_email(OPERATOR_EMAIL_AS_TYPED)
        assert normalize_email(once) == once
