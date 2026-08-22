# SUPERSEDED — the flat-file roster (R12) is replaced by the 48/49 principal substrate
# (re-cut design §9 R12). Archived from lorerunes/tests/ on 2026-08-22 by contract-39-w1
# (E1c): this tests the never-built roster parser/admission predicate; kept as a resolving
# address so the retirement is met deliberately, not rediscovered from a red test.
"""CONTRACT — ``lorerunes`` roster parser + admission predicate (packet 39, R7 + R12).

The roster is an operator-curated flat file of individually-allowlisted Google
identities, living OUTSIDE the repo and OUTSIDE the image and bind-mounted read-only
(design ``docs/design/2026-07-31-packet39-google-oauth.md`` §3-R12). This module pins
the two pure, stdlib-only pieces that live in ``lorerunes`` so the parser and the
runtime admission check cannot answer *"is this person allowed?"* differently:

* ``parse_roster(text) -> RosterParse`` — every non-structural line is either
  EMITTED as a normalised entry, MERGED onto an existing entry and REPORTED, or the
  WHOLE roster is REJECTED with a ``RosterParseError`` naming the line.
* ``is_admitted(email, roster) -> bool`` — the bare predicate, which must fail closed
  on an empty roster even when handed one directly (design §5: *"the defense survives
  a future refactor that bypasses the parser"*).

------------------------------------------------------------------------------
THE TWO INHERITED DEFECTS THIS CONTRACT EXISTS TO MAKE UNBUILDABLE

**F4 — the inherited fail-open.** odoo-code's verifier guards its allowlist with
``if settings.allowed_email_domains:``, so an EMPTY list skips the check entirely and
admits every verified Google account on earth. On lore's public endpoint that is a
total compromise. Every degenerate roster shape below (empty, whitespace-only,
comments-only, zero valid entries) is pinned to admit NOBODY — and the predicate is
pinned SEPARATELY from the parser, because a build can get one leg right and the
other wrong.

**R7 — the domain-shaped entry.** lore has no domain rule; an entry like
``firehawktransam.org`` is always an operator ERROR. Silently matching nothing would
teach the operator that their config "worked". A malformed line therefore refuses the
WHOLE roster — never a silently-shorter list.

------------------------------------------------------------------------------
INPUT ACCOUNTING (totality). ``parse_roster`` is a collection transform, so a shared
helper — :func:`assert_every_roster_line_is_accounted_for`, applied to EVERY
successful parse in this module — asserts each caller-supplied line has exactly one
fate. All three fates are FORCED by a fixture: emission (the ordinary case), MERGE
(two lines that normalise to one entry — outputs strictly fewer than inputs), and
rejection (each ``RosterParseError`` case). A ∀-helper evaluated only where the merge
branch cannot fire is a fixture-reason pass wearing a universal quantifier.

The invariant is quantified over INPUT LINES and is NOT conditioned on the failure
mode that prompted the work: it does not say *"when a line is domain-shaped, report"*
— it says *every* line has an accounted fate, whatever is wrong with it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:  # annotations only — resolved by mypy, never imported at runtime
    from lorerunes import RosterParse, RosterParseError


# ⚠ ``lorerunes`` SYMBOLS ARE IMPORTED INSIDE EACH FUNCTION, NOT AT MODULE LEVEL.
# This contract is written before the implementation exists, so a module-level import
# would collapse every pin in this file into ONE collection error — and a collection
# error yields NO node ids, which is exactly what ``scripts/mutation_proof.py`` needs
# in order to declare its expected-RED set from ``--collect-only``. Function-local
# imports keep the module collectible and let each pin fail on its own terms.


# --------------------------------------------------------------------------- #
# Production-realistic fixture values (design §2/R2/R12). These are the SHAPES the
# operator-curated roster actually carries: individually-listed addresses across the
# two orgs that share the reused OAuth client, plus the comment/blank structure a
# hand-edited flat file accumulates.
# --------------------------------------------------------------------------- #
OPERATOR_EMAIL = "ejprice@firehawktransam.org"
SECOND_PRINCIPAL_EMAIL = "dana.whitfield@pricepaper.com"
THIRD_PRINCIPAL_EMAIL = "marcus.olabode@firehawktransam.org"

# The roster as an operator would actually write it: a header comment, a section
# comment, blank separators, one line with stray indentation, one capitalised.
REALISTIC_ROSTER_TEXT = f"""\
# lore hosted-read allowlist — one Google identity per line.
# Revoking: delete the line. Takes effect on the next verification (no restart).

{OPERATOR_EMAIL}

# Price Paper co-tenants (shared OAuth client — see design R2)
  {SECOND_PRINCIPAL_EMAIL}
{THIRD_PRINCIPAL_EMAIL.upper()}
"""

REALISTIC_ROSTER_EXPECTED_ENTRIES = frozenset(
    {OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL, THIRD_PRINCIPAL_EMAIL}
)

# An address nobody put in the roster — the unlisted-principal probe. A real,
# well-formed Google identity; the point is that being verified by Google is not
# being admitted by lore.
UNLISTED_EMAIL = "someone.else@gmail.com"

# --------------------------------------------------------------------------- #
# R7 — the five malformed shapes the ruling names, each a REAL operator mistake:
# a bare domain (believing a domain rule exists), an ``@``-prefixed domain (copied
# from a mail-filter syntax), a local part with no domain (a truncated paste), a
# whitespace-only line that is not blank (a stray tab), and a double-@ typo.
# --------------------------------------------------------------------------- #
DOMAIN_SHAPED_LINE = "firehawktransam.org"
AT_PREFIXED_DOMAIN_LINE = "@firehawktransam.org"
LOCAL_PART_ONLY_LINE = "ejprice@"
DOMAIN_ONLY_AFTER_AT_LINE = "@"
DOUBLE_AT_LINE = "ejprice@firehawk@transam.org"

MALFORMED_LINES = (
    DOMAIN_SHAPED_LINE,
    AT_PREFIXED_DOMAIN_LINE,
    LOCAL_PART_ONLY_LINE,
    DOMAIN_ONLY_AFTER_AT_LINE,
    DOUBLE_AT_LINE,
)

# The teaching the refusal must carry (R7, verbatim intent): the operator must learn
# that lore has NO domain rule, not merely that "line 3 is bad".
NO_DOMAIN_RULE_TEACHING = "domain"

# --------------------------------------------------------------------------- #
# HOSTILE FIXTURE — the roster is operator-supplied STORED FREE TEXT that gets
# rendered into an ERROR log record when it is refused. A line shaped like lore's own
# structured output, carrying a backtick fence run and control characters, must not be
# renderable as real structure. Single-line-only, benign fixtures are the documented
# way this defect class ships green.
# --------------------------------------------------------------------------- #
FORGED_STRUCTURE_LINE = (
    "``` admin@evil.example  event=roster.loaded entries=42 status=ok ```"
)
CONTROL_CHARACTER_LINE = "ejprice\x1b[31m@firehawktransam.org\tspoofed"


def assert_every_roster_line_is_accounted_for(text: str, parsed: RosterParse) -> None:
    """∀ caller-supplied line: exactly ONE accounted fate (emitted | merged | rejected).

    Applied to EVERY successful parse in this module, not to one bespoke test — the
    quantifier law's instrument. A rejection ends the parse for the whole roster, so a
    successful parse must account for every line as either emitted or merged; the
    rejected fate is forced separately by :func:`assert_roster_refusal_names_the_line`.

    Args:
        text: The roster text handed to :func:`parse_roster`.
        parsed: The successful parse result to audit.

    Raises:
        AssertionError: If any candidate line has zero fates or more than one, or if
            the emitted+merged count does not conserve the candidate-line count.
    """
    from lorerunes import normalize_email
    candidates: list[tuple[int, str]] = [
        (number, line)
        for number, line in enumerate(text.splitlines(), start=1)
        if line.strip() and not line.strip().startswith("#")
    ]
    assert candidates, (
        "the accounting helper was handed a roster with NO candidate lines — a "
        "∀-assertion over an empty set is vacuous, which is the exact "
        "fixture-reason pass this helper exists to prevent"
    )

    merged_by_line_number = {merge.line_number: merge for merge in parsed.merged}
    for number, line in candidates:
        normalised = normalize_email(line)
        was_emitted = normalised in parsed.entries and number not in merged_by_line_number
        was_merged = number in merged_by_line_number
        fates = [name for name, held in (("emitted", was_emitted), ("merged", was_merged)) if held]
        assert len(fates) == 1, (
            f"roster line {number} ({line!r}) has fates {fates} — every input line "
            f"must have EXACTLY ONE accounted fate (emitted / merged-and-reported / "
            f"rejected-and-reported). Zero fates means the line vanished silently."
        )
        if was_merged:
            merge = merged_by_line_number[number]
            assert merge.line == line, (
                f"the merge report for line {number} must carry the line VERBATIM so "
                f"the operator can find it; got {merge.line!r} for {line!r}"
            )
            assert merge.entry in parsed.entries, (
                f"line {number} merged onto entry {merge.entry!r}, which is not in "
                f"the emitted set — a merge must land ON something"
            )

    assert len(parsed.entries) + len(parsed.merged) == len(candidates), (
        f"input accounting broken: {len(candidates)} candidate lines produced "
        f"{len(parsed.entries)} entries + {len(parsed.merged)} merge reports. Every "
        f"line must be conserved into exactly one of the two fates."
    )


def assert_roster_refusal_names_the_line(
    excinfo: pytest.ExceptionInfo[RosterParseError], line: str, line_number: int
) -> None:
    """A refusal must be diagnosable: it names the line, its number, and the rule.

    Args:
        excinfo: The captured :class:`RosterParseError`.
        line: The offending line, verbatim as it appeared in the file.
        line_number: Its 1-based position, so the operator can go straight to it.
    """
    error = excinfo.value
    assert error.line == line, (
        f"the refusal must carry the offending line VERBATIM (got {error.line!r}, "
        f"expected {line!r}) — a paraphrased line cannot be found in the file"
    )
    assert error.line_number == line_number, (
        f"the refusal must carry the 1-based line number (got {error.line_number}, "
        f"expected {line_number})"
    )
    message = str(error)
    assert repr(line) in message, (
        "the offending line must be rendered UNAMBIGUOUSLY into the message (its "
        "repr), so an operator-supplied line shaped like lore's own output cannot be "
        f"read as message structure. Message was: {message!r}"
    )
    assert NO_DOMAIN_RULE_TEACHING in message.lower(), (
        "the refusal must TEACH that lore has no domain rule and each address is "
        f"listed individually — otherwise the operator retypes the same mistake. "
        f"Message was: {message!r}"
    )


class TestParseRosterHappyPath:
    """A realistic, hand-edited roster parses to exactly its normalised addresses."""

    def test_realistic_roster_parses_to_its_three_principals(self) -> None:
        # Arrange / Act
        from lorerunes import parse_roster
        parsed = parse_roster(REALISTIC_ROSTER_TEXT)
        # Assert — the expected set comes from the fixture's declared principals, not
        # from re-running the parser's own logic.
        assert parsed.entries == REALISTIC_ROSTER_EXPECTED_ENTRIES
        assert_every_roster_line_is_accounted_for(REALISTIC_ROSTER_TEXT, parsed)

    def test_comment_and_blank_lines_produce_no_entries(self) -> None:
        # The structure lines are not principals. A build that treats ``#`` lines as
        # addresses would admit a comment-shaped string — and, worse, would make the
        # comments-only roster below look non-empty and therefore fail-open.
        from lorerunes import parse_roster
        parsed = parse_roster(REALISTIC_ROSTER_TEXT)
        assert not any(entry.startswith("#") for entry in parsed.entries)
        assert len(parsed.entries) == len(REALISTIC_ROSTER_EXPECTED_ENTRIES)

    def test_an_indented_line_is_admitted_after_normalisation(self) -> None:
        # The second principal's line carries leading whitespace in the fixture.
        from lorerunes import parse_roster
        parsed = parse_roster(REALISTIC_ROSTER_TEXT)
        assert SECOND_PRINCIPAL_EMAIL in parsed.entries

    def test_an_uppercase_line_is_admitted_after_normalisation(self) -> None:
        # The third principal's line is upper-cased in the fixture; Google will report
        # it lowercase. The roster must not care.
        from lorerunes import parse_roster
        parsed = parse_roster(REALISTIC_ROSTER_TEXT)
        assert THIRD_PRINCIPAL_EMAIL in parsed.entries

    def test_a_single_entry_roster_is_valid(self) -> None:
        # The boundary the operator's FIRST roster will actually have: exactly one
        # principal. N=1 is where ``len()`` and ``sum()`` stop being distinguishable,
        # so it is pinned alongside the N=3 case rather than instead of it.
        from lorerunes import parse_roster
        text = f"{OPERATOR_EMAIL}\n"
        parsed = parse_roster(text)
        assert parsed.entries == frozenset({OPERATOR_EMAIL})
        assert_every_roster_line_is_accounted_for(text, parsed)

    def test_a_roster_without_a_trailing_newline_still_parses_its_last_line(self) -> None:
        # A hand-edited file frequently lacks the final newline. A build that splits
        # on ``"\n"`` and drops the tail would silently LOSE the last principal —
        # exactly the silent-shortening R12 forbids.
        from lorerunes import parse_roster
        text = f"{OPERATOR_EMAIL}\n{SECOND_PRINCIPAL_EMAIL}"
        parsed = parse_roster(text)
        assert parsed.entries == frozenset({OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL})
        assert_every_roster_line_is_accounted_for(text, parsed)

    def test_crlf_line_endings_parse_identically(self) -> None:
        # The roster may be edited on, or copied from, a Windows host. A stray ``\r``
        # left on the address would make every entry unmatched — a total, silent
        # denial that looks like "the allowlist is broken".
        from lorerunes import parse_roster
        text = f"{OPERATOR_EMAIL}\r\n{SECOND_PRINCIPAL_EMAIL}\r\n"
        parsed = parse_roster(text)
        assert parsed.entries == frozenset({OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL})


class TestParseRosterMergeFate:
    """FORCED merge fate: two input lines, one emitted entry, and the merge REPORTED."""

    def test_two_lines_normalising_to_one_entry_produce_one_entry_and_one_report(
        self,
    ) -> None:
        # This is the fixture that FORCES the merge branch — outputs strictly fewer
        # than inputs. Without it the accounting helper above is a ∀ evaluated only
        # where the branch cannot fire.
        from lorerunes import parse_roster
        text = f"{OPERATOR_EMAIL}\nEJPrice@FireHawkTransAm.ORG\n"
        parsed = parse_roster(text)
        assert parsed.entries == frozenset({OPERATOR_EMAIL})
        assert len(parsed.merged) == 1, (
            "a duplicate line must be MERGED AND REPORTED, never silently dropped — "
            "the operator needs to know their roster has a redundant line"
        )
        assert parsed.merged[0].line_number == 2
        assert parsed.merged[0].entry == OPERATOR_EMAIL
        assert_every_roster_line_is_accounted_for(text, parsed)

    def test_the_merge_report_is_absent_when_no_line_merges(self) -> None:
        # The CONTROL for the merge pin: a roster with no duplicates reports no
        # merges. Without this, a build that reports EVERY line as merged would pass
        # the pin above.
        from lorerunes import parse_roster
        parsed = parse_roster(REALISTIC_ROSTER_TEXT)
        assert parsed.merged == ()

    def test_a_whitespace_only_duplicate_also_merges_rather_than_vanishing(self) -> None:
        # A second merge shape, so the branch is not pinned by one value: the same
        # address indented differently.
        from lorerunes import parse_roster
        text = f"{SECOND_PRINCIPAL_EMAIL}\n   {SECOND_PRINCIPAL_EMAIL}   \n"
        parsed = parse_roster(text)
        assert parsed.entries == frozenset({SECOND_PRINCIPAL_EMAIL})
        assert len(parsed.merged) == 1
        assert_every_roster_line_is_accounted_for(text, parsed)


class TestParseRosterRejectsMalformedLinesWholesale:
    """R7 — a malformed line refuses the WHOLE roster, never a shorter list."""

    @pytest.mark.parametrize("malformed", MALFORMED_LINES)
    def test_each_malformed_shape_refuses_the_parse(self, malformed: str) -> None:
        from lorerunes import RosterParseError, parse_roster
        with pytest.raises(RosterParseError) as excinfo:
            parse_roster(f"{malformed}\n")
        assert_roster_refusal_names_the_line(excinfo, malformed, 1)

    @pytest.mark.parametrize("malformed", MALFORMED_LINES)
    def test_one_malformed_line_invalidates_the_valid_lines_around_it(
        self, malformed: str
    ) -> None:
        # THE pin that kills the silently-shorter-list build: two perfectly good
        # principals surrounding one bad line. A parser that skips the bad line
        # returns a two-entry roster and every other test in this file still passes —
        # and the operator never learns their third principal is not admitted.
        from lorerunes import RosterParseError, parse_roster
        text = f"{OPERATOR_EMAIL}\n{malformed}\n{SECOND_PRINCIPAL_EMAIL}\n"
        with pytest.raises(RosterParseError) as excinfo:
            parse_roster(text)
        assert_roster_refusal_names_the_line(excinfo, malformed, 2)

    def test_the_refusal_reports_the_FIRST_malformed_line(self) -> None:
        # Deterministic diagnosis: with two bad lines the operator is pointed at the
        # first, fixes it, re-runs, and is pointed at the second. A refusal naming an
        # arbitrary one of the two is a debugging trap.
        from lorerunes import RosterParseError, parse_roster
        text = f"{DOMAIN_SHAPED_LINE}\n{OPERATOR_EMAIL}\n{DOUBLE_AT_LINE}\n"
        with pytest.raises(RosterParseError) as excinfo:
            parse_roster(text)
        assert_roster_refusal_names_the_line(excinfo, DOMAIN_SHAPED_LINE, 1)

    def test_a_valid_roster_is_accepted_so_the_refusal_probe_can_discriminate(
        self,
    ) -> None:
        # The POSITIVE CONTROL for every refusal pin above: a good roster is accepted.
        # "The bad input was rejected" is worthless until the good input is shown
        # accepted — otherwise a parser that refuses EVERYTHING passes all of them.
        from lorerunes import parse_roster
        parsed = parse_roster(REALISTIC_ROSTER_TEXT)
        assert parsed.entries == REALISTIC_ROSTER_EXPECTED_ENTRIES


class TestParseRosterRefusalRendersHostileTextUnambiguously:
    """Operator-supplied text is rendered into an error/log record — it may not forge."""

    def test_a_line_shaped_like_lore_own_output_cannot_be_read_as_structure(
        self,
    ) -> None:
        # The forgery: a roster line carrying a backtick FENCE RUN and a key=value
        # payload shaped exactly like a structured status line. Rendered raw into an
        # error message (and thence a log record a machine parses) it would close the
        # message's own fence and inject a fake "roster loaded, 42 entries, ok" event
        # — teaching an operator the opposite of the truth.
        from lorerunes import RosterParseError, parse_roster
        with pytest.raises(RosterParseError) as excinfo:
            parse_roster(f"{FORGED_STRUCTURE_LINE}\n")
        message = str(excinfo.value)
        assert repr(FORGED_STRUCTURE_LINE) in message, (
            "the hostile line must be rendered via repr (or an equivalently "
            "unambiguous quoting) so its backtick run and key=value payload cannot "
            "terminate or forge the message's own structure"
        )
        assert "\n" not in message, (
            "the refusal message must stay ONE record: a multi-line message lets an "
            "operator-supplied payload occupy a line of its own and be parsed as a "
            "separate event"
        )

    def test_control_characters_are_escaped_not_emitted_raw(self) -> None:
        # ANSI escapes and tabs in operator text reach a terminal and a log pipeline.
        # ``repr`` escapes both; a raw f-string interpolation does not.
        from lorerunes import RosterParseError, parse_roster
        with pytest.raises(RosterParseError) as excinfo:
            parse_roster(f"{CONTROL_CHARACTER_LINE}\n")
        message = str(excinfo.value)
        assert "\x1b" not in message, (
            "a raw ESC from operator-supplied text must never reach the rendered "
            "message — it can rewrite a terminal's display of the surrounding record"
        )
        assert repr(CONTROL_CHARACTER_LINE) in message


class TestParseRosterDegenerateShapesYieldNoEntries:
    """F4 — every empty-ish roster produces an EMPTY entry set, never a skipped check."""

    @pytest.mark.parametrize(
        "text",
        [
            "",
            "\n",
            "   \n\t\n",
            "# every principal was revoked on 2026-07-31\n",
            "# header only\n\n# and a second comment\n",
        ],
        ids=["empty", "one-newline", "whitespace-only", "one-comment", "comments-only"],
    )
    def test_degenerate_roster_parses_to_the_empty_set(self, text: str) -> None:
        # These MUST parse (they are not malformed) and MUST yield nothing. The
        # fail-closed decision belongs to the callers, which is why the predicate
        # below is pinned separately.
        from lorerunes import parse_roster
        parsed = parse_roster(text)
        assert parsed.entries == frozenset()
        assert parsed.merged == ()


class TestIsAdmittedFailsClosed:
    """The bare predicate, pinned independently of the parser (design §5, F4)."""

    def test_a_listed_principal_is_admitted(self) -> None:
        # The POSITIVE control: without it, a predicate that returns False for
        # everything passes every negative pin below.
        from lorerunes import is_admitted
        assert is_admitted(OPERATOR_EMAIL, REALISTIC_ROSTER_EXPECTED_ENTRIES) is True

    def test_an_unlisted_principal_is_denied(self) -> None:
        from lorerunes import is_admitted
        assert is_admitted(UNLISTED_EMAIL, REALISTIC_ROSTER_EXPECTED_ENTRIES) is False

    def test_an_empty_roster_denies_every_principal(self) -> None:
        # F4, at the leg a refactor is most likely to bypass. odoo-code's shape —
        # ``if allowlist: check(...)`` — returns "allowed" here. This pin makes that
        # build impossible even if the parser is bypassed entirely.
        from lorerunes import is_admitted
        for email in (OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL, UNLISTED_EMAIL):
            assert is_admitted(email, frozenset()) is False, (
                f"an EMPTY roster must deny {email!r} — an empty allowlist that "
                f"skips the check is the inherited fail-open (F4), and on lore's "
                f"public endpoint it admits every verified Google account on earth"
            )

    def test_a_blank_presented_email_is_denied_even_against_a_populated_roster(
        self,
    ) -> None:
        # A tokeninfo response with a missing/blank ``email`` must not match anything.
        # A build that normalises "" and finds "" in a roster built from a stray blank
        # line would admit an anonymous token.
        from lorerunes import is_admitted
        for blank in ("", "   ", "\n"):
            assert is_admitted(blank, REALISTIC_ROSTER_EXPECTED_ENTRIES) is False

    def test_admission_normalises_the_presented_email(self) -> None:
        # The SEAM: Google reports lowercase, the roster line was typed capitalised
        # (or vice versa). One normaliser, both sides — proved here at the predicate
        # and again at the verifier, so a build that normalises only one side reds.
        from lorerunes import is_admitted, normalize_email
        assert is_admitted("EJPrice@FireHawkTransAm.ORG", frozenset({OPERATOR_EMAIL})) is True
        roster_from_a_capitalised_line = frozenset({normalize_email("EJPrice@FIREHAWKTRANSAM.org")})
        assert is_admitted(OPERATOR_EMAIL, roster_from_a_capitalised_line) is True

    def test_admission_does_not_substring_match(self) -> None:
        # Exact membership, never ``in``/``endswith``. A build that matched the domain
        # suffix would resurrect the domain rule R7 exists to forbid, and admit every
        # address at an allowlisted principal's employer.
        from lorerunes import is_admitted
        assert is_admitted("evil@firehawktransam.org", frozenset({OPERATOR_EMAIL})) is False
        assert is_admitted("ejprice@firehawktransam.org.evil.example", frozenset({OPERATOR_EMAIL})) is False
        assert is_admitted("xejprice@firehawktransam.org", frozenset({OPERATOR_EMAIL})) is False

    def test_a_domain_shaped_probe_is_denied_by_the_predicate_itself(self) -> None:
        # R7's rider: the predicate leg must survive a refactor that bypasses the
        # parser. Even handed a domain-shaped roster set directly, the predicate must
        # not admit a domain-shaped probe or any address at that domain.
        from lorerunes import is_admitted
        domain_shaped_roster = frozenset({DOMAIN_SHAPED_LINE})
        assert is_admitted(DOMAIN_SHAPED_LINE, domain_shaped_roster) is False
        assert is_admitted(OPERATOR_EMAIL, domain_shaped_roster) is False

    def test_a_homograph_of_a_listed_principal_is_denied(self) -> None:
        # SECURITY, at the admission seam rather than the normaliser: a Cyrillic-е
        # lookalike of a listed address must not be admitted.
        from lorerunes import is_admitted
        cyrillic_lookalike = "еjprice@firehawktransam.org"
        assert is_admitted(cyrillic_lookalike, frozenset({OPERATOR_EMAIL})) is False
