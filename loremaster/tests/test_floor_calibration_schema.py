"""Contract — packet 11-i-a, the floor-calibration + lease SCHEMA (B4).

Written by `contract-11ia-1` (2026-07-26). The builder builds FROM this.

WHAT THIS FILE DECIDES (the interface freeze 11-i-b cites) —
``loremaster.store.surreal_schema``::

    FLOOR_MEASUREMENT_TABLE = "floor_measurement"   # append-only history
    FLOOR_HEAD_TABLE        = "floor_head"          # one HOT row per head id
    LEASE_TABLE             = "lease"
    LEASE_SINGLETON_ID      = "singleton"
    generate_floor_calibration_ddl() -> str
    generate_lease_ddl() -> str

⚠ THE DDL DECISION RULE IS NOT NEGOTIABLE AND IT IS PINNED MECHANICALLY, not
trusted to a reviewer (store reference §1.1, finding #107 — a 100% production
outage whose answer was already written in that file):

    plain TABLE -> IF NOT EXISTS   ·   FIELD -> OVERWRITE
    INDEX       -> IF NOT EXISTS   ·   ALTER is a trap, not the migration verb

``DEFINE FIELD IF NOT EXISTS`` is a SILENT NO-OP on an existing field, so a
changed definition never migrates a live store — and every test in this repo
mints a VIRGIN database, which is *structurally* why 1040 tests, a cold audit
and a contract-adversary all passed #107. The clause pins below are the only
instrument a virgin-DB suite has; ``TestTheSchemaMigratesAnEXISTINGStore`` is
the other half, and it is the one that would actually have caught the outage.

⚠ AND THE INVERSIONS ARE PINNED AS A KNOWN BOUND. If this slice ever grows a
``TYPE RELATION`` table the FIELD/TABLE rule INVERTS for it (§1.1's RELATION
row: ``IF NOT EXISTS`` is a silent no-op on an existing edge table), and a
``DEFINE SEQUENCE`` carries #146's un-migratable ``BATCH``/``START`` residual.
``test_this_slice_contains_neither_a_relation_table_nor_a_sequence`` goes RED
the day either appears, carrying that instruction — so the next engineer meets
the bound DELIBERATELY instead of rediscovering it from an outage.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

import pytest
from _surreal_harness import (
    SurrealConnection,
    SurrealEnv,
    admin_db,  # noqa: F401 - re-exported pytest fixture
    run,
)
from loremaster.store import surreal_schema
from loremaster.store.surreal_schema import (
    FLOOR_HEAD_TABLE,
    FLOOR_MEASUREMENT_TABLE,
    FLOOR_NON_ADOPTION_CAUSES,
    FLOOR_STATES,
    LEASE_SINGLETON_ID,
    LEASE_TABLE,
    generate_floor_calibration_ddl,
    generate_lease_ddl,
)
from markdown_it import MarkdownIt

_DEFINE_TABLE = re.compile(r"^\s*DEFINE\s+TABLE\b", re.IGNORECASE)
_DEFINE_FIELD = re.compile(r"^\s*DEFINE\s+FIELD\b", re.IGNORECASE)
_DEFINE_INDEX = re.compile(r"^\s*DEFINE\s+INDEX\b", re.IGNORECASE)

# The retired state name, spelled out in full so a bare, anchor-free sweep can
# find this line (repo rename law: sweep patterns carry no structural anchor,
# because prose mentions carry none either).
RETIRED_STATE_NAME = "stale_remeasuring"

# What Addendum F §F4 renamed it TO. Load-bearing for the marker rule below, not
# decoration: a retirement notice that does not say what to use INSTEAD is half a
# notice, and the reader it exists for is an agent that landed on the corpse via
# search. Bound to the ruled set by
# ``test_the_RETIRED_state_is_absent_from_the_ruled_set_and_its_replacement_present``
# so this stays a DERIVED name rather than a literal nobody rechecks.
REPLACEMENT_STATE_NAME = "invalidated_remeasuring"

# ⚠ THE BLOCK UNIT IS PARSED BY ``markdown-it-py``, NOT BY A HAND-ROLLED REGEX
# (packages over hand-rolling — operator directive; the swap is `f052c6d`). The
# hand-rolled splitter this replaced produced IDENTICAL spans on all six real hit
# sites, which is what justified adopting the package rather than defending the
# copy: measured before the recommendation, not asserted after it.
#
# ``commonmark`` + ``table``, deliberately NOT the ``gfm-like`` preset — that one
# enables ``linkify``, whose backing package is not installed, and
# ``MarkdownIt("gfm-like").parse()`` raises ModuleNotFoundError on any document.
_MARKDOWN = MarkdownIt("commonmark").enable("table")

# The token types that delimit the span a retrieval chunk carries — which is the
# whole reason a marker must sit near its corpse (#160: a chunk arrives without
# its header). A table ROW is one of them on purpose: §7's state table is what
# 11-ii reads to build its served state projection, so one row retrieved alone
# must carry its own correction and a marked row must not launder its neighbours.
_BLOCK_TOKENS = frozenset(
    {
        "list_item_open",
        "tr_open",
        "paragraph_open",
        "heading_open",
        "blockquote_open",
        "fence",
        "code_block",
        "html_block",
    }
)

# ALLOWLIST THE SAFE (repo law: the forbidden set is unbounded, the safe set is
# small and enumerable). These are the words that say "this name is a corpse",
# not an attempt to enumerate the ways prose can teach one. A marker spelled some
# other way fails CLOSED — RED, with the convention quoted in the message — which
# is the correct direction for an allowlist.
_RETIREMENT_WORD = re.compile(
    r"\b(?:amend(?:ed|s)|renam(?:ed|es)|retir(?:ed|es)|supersed(?:ed|es)|deprecat(?:ed|es))\b",
    re.IGNORECASE,
)


def _narrowest_block_spans(text: str) -> dict[int, tuple[int, int]]:
    """1-based line number -> the ``(start, end)`` of the SMALLEST block holding it.

    Smallest, not outermost: a bullet nested in a list is covered by both its own
    ``list_item_open`` and the enclosing ``bullet_list_open``, and taking the
    enclosing one would let a marker excuse every sibling bullet in the list.
    Narrowing is what keeps the excuse tight.
    """
    spans: dict[int, tuple[int, int]] = {}
    for token in _MARKDOWN.parse(text):
        if token.map is None or token.type not in _BLOCK_TOKENS:
            continue
        start, end = token.map[0] + 1, token.map[1]  # markdown-it: 0-based, end-exclusive
        for number in range(start, end + 1):
            held = spans.get(number)
            if held is None or (end - start) < (held[1] - held[0]):
                spans[number] = (start, end)
    return spans


def unmarked_retired_name_lines(relative_path: str, text: str) -> list[str]:
    """Lines of ``text`` carrying the retired name whose block does NOT retire it.

    THE PROPERTY: a line may carry ``stale_remeasuring`` only if the markdown
    block it sits in also (a) uses a retirement word and (b) names
    ``invalidated_remeasuring``. Both factors are present at every real marker in
    the tree; requiring both keeps a block that merely *mentions* a rename from
    laundering a teaching, and keeps the notice useful to the agent that landed
    on it.

    Two-factor, block-scoped, and it is the ONE implementation — the tree pin and
    every discrimination control below call this same function, so a control that
    passes is evidence about the code the pin runs.
    """
    if RETIRED_STATE_NAME not in text:
        return []  # nothing to adjudicate; also spares every unrelated doc a parse
    lines = text.splitlines()
    spans = _narrowest_block_spans(text)
    offenders: list[str] = []
    for number, line in enumerate(lines, 1):
        if RETIRED_STATE_NAME not in line:
            continue
        # A line no block token covers (a table's delimiter row, a stray
        # continuation) is its OWN block: the strictest reading, so an unparsed
        # shape fails CLOSED rather than inheriting a neighbour's marker.
        start, end = spans.get(number, (number, number))
        body = "\n".join(lines[start - 1 : end])
        if _RETIREMENT_WORD.search(body) and REPLACEMENT_STATE_NAME in body:
            continue
        offenders.append(f"{relative_path}:{number}: {line.strip()}")
    return offenders


_PACKAGE_ROOT = Path(surreal_schema.__file__).resolve().parents[1]
_TESTS_ROOT = Path(__file__).resolve().parent
# <repo>/loremaster/loremaster/store/surreal_schema.py -> parents[3] is <repo>
_REPO_ROOT = Path(surreal_schema.__file__).resolve().parents[3]


def _statements(ddl: str) -> list[str]:
    """The DDL's individual statements, as the transaction will see them."""
    return [line.strip() for line in ddl.split(";") if line.strip()]


def _both_slices() -> list[str]:
    return _statements(generate_floor_calibration_ddl()) + _statements(generate_lease_ddl())


class TestTheDdlDecisionRuleIsEnforcedMechanically:
    """Store reference §1.1. Each pin names the failure it prevents, because a
    clause is invisible in review and catastrophic in production.
    """

    def test_every_table_definition_is_IF_NOT_EXISTS(self) -> None:
        offenders = [
            statement
            for statement in _both_slices()
            if _DEFINE_TABLE.match(statement) and "IF NOT EXISTS" not in statement.upper()
        ]
        assert not offenders, (
            f"plain TABLE definitions must be `IF NOT EXISTS` (§1.1): {offenders}"
        )

    def test_every_field_definition_is_OVERWRITE(self) -> None:
        """#107, verbatim: ``IF NOT EXISTS`` on an existing field returns OK and
        silently keeps the OLD definition, so a widened ASSERT never reaches a
        live store. Only ``OVERWRITE`` migrates."""
        offenders = [
            statement
            for statement in _both_slices()
            if _DEFINE_FIELD.match(statement) and "OVERWRITE" not in statement.upper()
        ]
        assert not offenders, (
            f"every FIELD definition must be `DEFINE FIELD OVERWRITE` (#107): {offenders}"
        )

    def test_no_field_definition_uses_IF_NOT_EXISTS(self) -> None:
        """The same rule from the other side — a build that emitted BOTH clauses
        would pass the pin above."""
        offenders = [
            statement
            for statement in _both_slices()
            if _DEFINE_FIELD.match(statement) and "IF NOT EXISTS" in statement.upper()
        ]
        assert not offenders, offenders

    def test_every_index_definition_is_IF_NOT_EXISTS_and_never_OVERWRITE(self) -> None:
        """Flipping an index to ``OVERWRITE`` converts a silent no-op into a
        BOOT-TIME CRASH: a define REBUILDS, blocking, over every existing row."""
        for statement in _both_slices():
            if not _DEFINE_INDEX.match(statement):
                continue
            assert "IF NOT EXISTS" in statement.upper(), statement
            assert "OVERWRITE" not in statement.upper(), statement

    def test_the_word_ALTER_appears_in_no_statement(self) -> None:
        """§1.3: ``ALTER`` cannot CREATE a field, and ``ALTER … IF EXISTS`` on a
        missing one silently no-ops — adopting it re-commits #107 from the other
        side, on the fresh-DB path this slice runs on every new deployment."""
        offenders = [
            statement for statement in _both_slices() if re.search(r"\bALTER\b", statement, re.I)
        ]
        assert not offenders, offenders

    def test_this_slice_contains_neither_a_relation_table_nor_a_sequence(self) -> None:
        """⚠ A PINNED KNOWN BOUND (not a prohibition).

        If you are reading this because it went RED, you added a ``TYPE
        RELATION`` table or a ``DEFINE SEQUENCE`` to this slice. STOP and re-read
        store reference §1 first: for a RELATION table the TABLE clause INVERTS
        to ``OVERWRITE`` (``IF NOT EXISTS`` is a measured silent no-op on an
        existing edge table — #107's shape, invisible to every virgin-DB
        fixture), and a SEQUENCE carries #146's residual (a changed
        ``BATCH``/``START`` never migrates). Then update this pin deliberately,
        in a diff a reviewer can see.
        """
        for statement in _both_slices():
            assert "TYPE RELATION" not in statement.upper(), statement
            assert not re.search(r"\bDEFINE\s+SEQUENCE\b", statement, re.I), statement

    def test_each_generator_returns_the_house_terminated_shape(self) -> None:
        """Every other ``generate_*_ddl`` returns ``";\\n".join(...) + ";\\n"``.
        A slice that did not would break the caller's ``BEGIN … COMMIT`` wrap."""
        for ddl in (generate_floor_calibration_ddl(), generate_lease_ddl()):
            assert ddl.endswith(";\n")
            assert _statements(ddl)

    def test_the_generators_emit_something_for_every_planned_table(self) -> None:
        """CONTROL: a generator returning "" would make every clause pin above
        VACUOUSLY green — the signature failure of a mechanical gate.

        ⚠ IT DEMANDS FIELDS, NOT JUST TABLE NAMES (adversary F1c). Checking that
        three table names appear as substrings is satisfied by a slice emitting
        three ``DEFINE TABLE``s and ZERO ``DEFINE FIELD``s — and then
        ``test_every_field_definition_is_OVERWRITE`` is itself vacuously green,
        which is the control failing at the one job it has.
        """
        for table in (FLOOR_MEASUREMENT_TABLE, FLOOR_HEAD_TABLE, LEASE_TABLE):
            fields = [
                statement
                for statement in _both_slices()
                if _DEFINE_FIELD.match(statement) and f" ON {table} " in f"{statement} "
            ]
            assert fields, f"the slice for {table!r} emits no DEFINE FIELD at all"

    def test_the_new_slices_ROUTE_THROUGH_the_shared_ddl_emitters(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ONE IMPLEMENTATION, proven by MUTATION (adversary residual 8).

        The clause pins enforce today's POLICY, but nothing required the new
        slices to CALL ``_define_field``/``_define_table`` — so a future change
        to the shared emitter would silently not reach them. Perturb the shared
        emitter; the emitted DDL must move.
        """
        original = surreal_schema._define_field
        monkeypatch.setattr(
            surreal_schema,
            "_define_field",
            lambda *args, **kwargs: f"{original(*args, **kwargs)} COMMENT 'mutation-probe'",
        )
        assert "mutation-probe" in generate_floor_calibration_ddl(), (
            "the floor slice does not route through surreal_schema._define_field"
        )
        assert "mutation-probe" in generate_lease_ddl(), (
            "the lease slice does not route through surreal_schema._define_field"
        )


class TestTheClosedDomainsAreDerivedIntoTheDdl:
    """ONE IMPLEMENTATION, proven by MUTATION rather than by reading the source.

    The state and cause ASSERTs must be GENERATED FROM
    ``FLOOR_STATES`` / ``FLOOR_NON_ADOPTION_CAUSES``, not hand-typed beside
    them. A hand-typed list passes every "the assert mentions 'measured'" pin
    and drifts the first time a state is added — the exact prose-beside-code
    class this repo has shipped ten instances of.
    """

    def test_changing_the_state_tuple_changes_the_emitted_ASSERT(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        before = generate_floor_calibration_ddl()
        monkeypatch.setattr(
            surreal_schema, "FLOOR_STATES", (*FLOOR_STATES, "mutation_probe_state")
        )
        after = generate_floor_calibration_ddl()
        assert after != before, (
            "adding a state changed no emitted DDL — the state ASSERT is a hand-typed "
            "twin of FLOOR_STATES rather than a derivation of it"
        )
        assert "mutation_probe_state" in after

    def test_changing_the_cause_tuple_changes_the_emitted_ASSERT(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        before = generate_floor_calibration_ddl()
        monkeypatch.setattr(
            surreal_schema,
            "FLOOR_NON_ADOPTION_CAUSES",
            (*FLOOR_NON_ADOPTION_CAUSES, "mutation_probe_cause"),
        )
        after = generate_floor_calibration_ddl()
        assert after != before
        assert "mutation_probe_cause" in after

    def test_every_ruled_state_reaches_the_ddl(self) -> None:
        floor = generate_floor_calibration_ddl()
        missing = [state for state in FLOOR_STATES if state not in floor]
        assert not missing, missing

    def test_the_RETIRED_state_is_absent_from_the_ruled_set_and_its_replacement_present(
        self,
    ) -> None:
        """Addendum F §F4, pinned against the ruled set rather than asserted beside it.

        This is what keeps ``REPLACEMENT_STATE_NAME`` a DERIVED name: the doc
        sweep admits a retirement notice only if it names that string, so a
        literal nobody rechecks would let the sweep demand a name the ruled set
        no longer carries. If F4 is ever itself superseded, this goes RED at the
        constant instead of quietly mis-teaching every future amendment.
        """
        assert RETIRED_STATE_NAME not in FLOOR_STATES, (
            f"{RETIRED_STATE_NAME!r} is in the ruled state set, but Addendum F §F4 RETIRED it"
        )
        assert REPLACEMENT_STATE_NAME in FLOOR_STATES, (
            f"{REPLACEMENT_STATE_NAME!r} is not in FLOOR_STATES={FLOOR_STATES!r} — §F4 renamed "
            f"{RETIRED_STATE_NAME!r} to it AND re-predicated it to leg 1 (vector-identity "
            f"invalidation) only"
        )


class TestTheRetiredStateNameIsGoneFromTheTree:
    """Repo rename law. F4.1 renamed ``stale_remeasuring`` to
    ``invalidated_remeasuring``; the sweep uses a BARE, anchor-free pattern
    because prose mentions carry no structural anchor, and three of four audited
    green-at-gate defects lived in exactly such surfaces.

    ⚠ **O4 — THE SWEEP'S OWN REACH WAS THE BLIND SPOT.** Until 2026-07-26 the
    scan globbed ``*.py`` only, so it could not see FOUR LIVE design-doc lines
    that still teach the retired name — including §7's state TABLE, which is the
    design of record 11-ii implements its served state projection from. An
    instrument that carries the very blind spot it exists to police is worse
    than no instrument, because its green is read as coverage.

    ⚠ **AND THEN THE FIX FOR O4 WAS ITSELF THE HOLE (2026-07-26, second pass).**
    Those lines were carried in a named QUARANTINE, whose pin claimed to go RED
    the day one was repaired. They WERE repaired (``790989f``) and the pin stayed
    GREEN — because the repair deliberately KEEPS the retired string inside a
    dated amendment notice, so an agent searching for the corpse lands on the
    notice explaining it IS one. **The sweep could not tell a RETIREMENT MARKER
    from a TEACHING**, and while a file sat quarantined it was exempt from the
    teaching pin entirely, so a genuinely NEW stale line in it was invisible. A
    quarantine wearing a pin's clothing.

    **THE PROPERTY THAT REPLACED IT** — ``unmarked_retired_name_lines``: a line
    may carry the retired name only if its markdown BLOCK also uses a retirement
    word AND names the replacement. That ALLOWLISTS THE SAFE instead of trying to
    enumerate how prose can teach a name (repo law: the forbidden set is
    unbounded, the safe set is small). The quarantine is GONE — every live doc,
    including the amended one, is now swept the same way, and a newly-added
    teaching line in it goes RED like any other file's.

    ⚠ **THE MARKER IS BLOCK-SCOPED, NOT LINE-SCOPED, AND THE TREE FORCED THAT.**
    Of the three surviving mentions in the design doc, only §7's table row
    carries its marker on the same line; the other two sit on the line AFTER
    ``⚠ **AMENDED by Addendum F §F4 — cited, not re-derived.**``. A same-line
    rule would have been RED against a correctly-amended tree. The block is also
    the right unit on its own merits: it is what a retrieval chunk carries, and
    #160 is precisely that a chunk arrives without its header.

    ⚠ **KNOWN BOUND, pinned rather than hidden:** a NEW stale line added INSIDE
    an already-marked block is still excused. Block units are small (a table row,
    a bullet) and every marked block in the tree is an amendment notice, so this
    needs an author to write a teaching *inside* a notice that says the name is
    retired — not an honest-developer mistake (threat model: this gate catches
    the honest author, not a determined one). **Re-open trigger:** if a marked
    block ever grows beyond its notice, or a second corpse needs the same
    treatment, replace this with a tripwire on the total marked-mention count.

    ⚠ **THERE IS NO PER-FILE EXEMPTION LEFT.** An earlier revision excused the
    AMENDING doc wholesale, on the reasoning that a rename doc must be allowed to
    name what it retires. The marker rule exists *precisely* so it can — so the
    exemption was buying nothing and costing the same blindness the quarantine
    did: a brand-new teaching line in the amending doc would have been invisible.
    Measuring it (rather than eyeballing it) found TWO lines short of the rule,
    both missing the replacement name; ``f052c6d`` fixed them and the whole-file
    exemption went with them. Every live doc is now swept identically.

    The ONE remaining exclusion is ``docs/plans/v2/receipts/``, and it is
    structural rather than a judgement call: ARCHIVE LAW. Those files are
    byte-faithful evidence of runs that happened, so editing one is falsification,
    not a refactor. The 2026-07-26 banner in
    ``receipts/2026-07-24-packet11i/CONTRACT-FREEZE-DECISIONS.md`` is the
    archive-safe form of the same marker — a notice beside the quote, satisfying
    both factors — so the convention is consistent across swept and unswept docs
    even though only the former are enforced.
    """

    #: The live docs the sweep reaches. Receipts are excluded by archive law.
    SWEPT_DOC_GLOBS = ("docs/design/*.md", "docs/plans/v2/*.md", "docs/reference/*.md")

    @staticmethod
    def _hits(root: Path) -> list[str]:
        found: list[str] = []
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if RETIRED_STATE_NAME in line:
                    found.append(f"{path}:{number}: {line.strip()}")
        return found

    @classmethod
    def _swept_docs(cls) -> dict[str, str]:
        """Repo-relative path -> text, for every LIVE doc the sweep reaches."""
        texts: dict[str, str] = {}
        for glob in cls.SWEPT_DOC_GLOBS:
            for path in sorted(_REPO_ROOT.glob(glob)):
                texts[path.relative_to(_REPO_ROOT).as_posix()] = path.read_text(encoding="utf-8")
        return texts

    @classmethod
    def _doc_hits(cls) -> dict[str, list[str]]:
        """Every LIVE doc line carrying the corpse, keyed by repo-relative path."""
        by_path: dict[str, list[str]] = {}
        for relative, text in cls._swept_docs().items():
            for number, line in enumerate(text.splitlines(), 1):
                if RETIRED_STATE_NAME in line:
                    by_path.setdefault(relative, []).append(f"{relative}:{number}: {line.strip()}")
        return by_path

    @classmethod
    def _unmarked_doc_hits(cls) -> dict[str, list[str]]:
        """The subset of ``_doc_hits`` whose block does NOT retire the name."""
        by_path: dict[str, list[str]] = {}
        for relative, text in cls._swept_docs().items():
            unmarked = unmarked_retired_name_lines(relative, text)
            if unmarked:
                by_path[relative] = unmarked
        return by_path

    def test_no_production_module_mentions_the_retired_name(self) -> None:
        assert not self._hits(_PACKAGE_ROOT), self._hits(_PACKAGE_ROOT)

    def test_the_only_test_mentions_are_the_two_pins_that_assert_its_ABSENCE(self) -> None:
        """"All remaining hits are X" is banned output — so every residual hit
        is named, individually, with its file and line."""
        allowed = {
            (_TESTS_ROOT / "test_floor_calibration_domain.py").name,
            (_TESTS_ROOT / "test_floor_calibration_schema.py").name,
        }
        residual = [
            hit for hit in self._hits(_TESTS_ROOT) if Path(hit.split(":")[0]).name not in allowed
        ]
        assert not residual, residual

    def test_the_doc_sweep_can_actually_see_a_hit(self) -> None:
        """CONTROL. A widened sweep that matched nothing would make the two pins
        below silently green — and this sweep's whole finding was that a scan
        can be blind to the surface that matters."""
        assert self._doc_hits(), (
            "the widened doc sweep found NOTHING — either every quarantined line "
            "was fixed (delete the quarantine) or the globs are broken"
        )

    def test_no_live_doc_carries_the_retired_name_outside_a_RETIREMENT_MARKER(self) -> None:
        """THE PIN. Every live doc, every line — no exemptions, no quarantine.

        A hit is admitted ONLY by its own markdown block retiring the name, so
        this fires on a brand-new teaching line in an already-amended file, which
        the quarantine it replaced could not see.
        """
        unmarked = self._unmarked_doc_hits()
        assert not unmarked, (
            f"live doc line(s) carry the RETIRED state name {RETIRED_STATE_NAME!r} without a "
            f"retirement marker: {unmarked}\n"
            f"Fix by EITHER renaming to {REPLACEMENT_STATE_NAME!r} (Addendum F §F4 — which also "
            f"RE-PREDICATED it to leg 1 only, so check the surrounding claim is still true), OR, "
            f"if the mention is deliberately preserving the corpse for a searcher, marking it: the "
            f"same markdown block (bullet, table row, paragraph) must use a retirement word "
            f"(amended/renamed/retired/superseded/deprecated) AND name {REPLACEMENT_STATE_NAME!r}. "
            f"Worked example in the tree: the '⚠ **AMENDED by Addendum F §F4 — cited, not "
            f"re-derived.**' notices in docs/design/2026-07-24-floor-calibration.md."
        )


class TestTheRetirementMarkerRuleDiscriminates:
    """⚠ THE CONTROLS. ``unmarked_retired_name_lines`` ADMITS lines — an allowlist
    that admits everything is not a gate, and this repo has a receipt of a probe
    that passed for the wrong reason (it rejected on a PARSE ERROR, not the check
    it named). So every leg below is interrogated with *"what wrong build would
    this still pass?"*, and each names the wrong build it kills.

    Every leg calls the SAME function the tree pin calls, so a green control is
    evidence about the code that actually runs.
    """

    def test_an_UNMARKED_teaching_line_is_REJECTED(self) -> None:
        """NON-VACUITY. Kills: a function that returns [] for everything —
        under which every other leg here, and the tree pin, is silently green."""
        text = f"# States\n\nThe instance sits in `{RETIRED_STATE_NAME}` until the corpus settles.\n"
        assert unmarked_retired_name_lines("d.md", text) == [
            f"d.md:3: The instance sits in `{RETIRED_STATE_NAME}` until the corpus settles."
        ]

    def test_a_doc_with_no_mention_at_all_is_ACCEPTED(self) -> None:
        """The good-input leg: the probe is not simply rejecting everything."""
        assert unmarked_retired_name_lines("d.md", "# States\n\nAll instances are `measured`.\n") == []

    def test_a_marker_on_the_SAME_line_is_ACCEPTED(self) -> None:
        """Models §7's amended table row. A REAL GFM table (header + delimiter),
        not two bare pipe lines — under a real parser those are one paragraph, and
        a fixture that is not the shape it claims proves nothing about the shape
        it claims."""
        text = (
            "| state | verdict |\n"
            "|---|---|\n"
            f"| `{REPLACEMENT_STATE_NAME}` (known-invalid) — **renamed by Addendum F §F4**; "
            f"was `{RETIRED_STATE_NAME}` | disarmed |\n"
        )
        assert unmarked_retired_name_lines("d.md", text) == []

    def test_a_marker_EARLIER_IN_THE_SAME_BLOCK_is_ACCEPTED(self) -> None:
        """⚠ THE LEG THAT DECIDED THE DESIGN. Kills: a same-LINE rule — which is
        the obvious reading of "the line must carry a marker", and which would be
        RED against a correctly-amended tree, because two of the three real
        markers open a notice whose quoted corpse lands on the NEXT line.
        """
        text = (
            "- *Quiescence over clocks:* the trigger defers while the index is unsettled.\n"
            "  ⚠ **AMENDED by Addendum F §F4 — cited, not re-derived.** This bullet ended\n"
            f'  *"a churning corpus renders `{RETIRED_STATE_NAME}` honestly until it settles."*\n'
            f"  The state is now **`{REPLACEMENT_STATE_NAME}`**, predicate leg 1 ONLY.\n"
        )
        assert unmarked_retired_name_lines("d.md", text) == []

    def test_a_NEW_teaching_bullet_touching_a_marked_block_is_REJECTED(self) -> None:
        """⚠ THE HOLE THE QUARANTINE HAD, AS A FIXTURE. Kills: any FILE-scoped or
        blank-line-scoped marker check. The offending bullet is adjacent to the
        notice with NO blank line between them, so a build that scoped the marker
        to the file, or to the contiguous run of non-blank lines, admits it — and
        that is exactly "a genuinely new stale line is invisible".
        """
        text = (
            "- *Quiescence:* the trigger defers while the index is unsettled.\n"
            f"  ⚠ **AMENDED by §F4.** was `{RETIRED_STATE_NAME}`, now `{REPLACEMENT_STATE_NAME}`.\n"
            f"- *Flap bound:* the floor stays `{RETIRED_STATE_NAME}` while the run is queued.\n"
        )
        assert unmarked_retired_name_lines("d.md", text) == [
            f"d.md:3: - *Flap bound:* the floor stays `{RETIRED_STATE_NAME}` while the run is queued."
        ]

    def test_a_NEW_teaching_TABLE_ROW_touching_a_marked_row_is_REJECTED(self) -> None:
        """Kills: treating a whole markdown TABLE as one block. §7's state table
        is what 11-ii reads to build its served state projection, so a stale row
        re-added beside the amended one is the highest-cost regression available —
        and one marked row must not launder its neighbours.
        """
        text = (
            "| state | floor served? |\n"
            "|---|---|\n"
            f"| `{REPLACEMENT_STATE_NAME}` — **renamed by §F4**; was `{RETIRED_STATE_NAME}` | no |\n"
            f"| `{RETIRED_STATE_NAME}` (leg fired; run queued/in flight) | no |\n"
        )
        assert unmarked_retired_name_lines("d.md", text) == [
            f"d.md:4: | `{RETIRED_STATE_NAME}` (leg fired; run queued/in flight) | no |"
        ]

    def test_a_retirement_word_WITHOUT_the_replacement_is_REJECTED(self) -> None:
        """A DIFFERENTLY-broken input, rejected for a DIFFERENT reason than the
        non-vacuity leg: factor (a) present, factor (b) missing. Kills: a
        one-factor build keyed on the retirement word alone, which would admit
        any teaching that happens to share a block with the word "renamed".
        """
        text = f"- The `{RETIRED_STATE_NAME}` row was **renamed** by Addendum F §F4.\n"
        assert unmarked_retired_name_lines("d.md", text) == [
            f"d.md:1: - The `{RETIRED_STATE_NAME}` row was **renamed** by Addendum F §F4."
        ]

    def test_the_replacement_name_WITHOUT_a_retirement_word_is_REJECTED(self) -> None:
        """The other single factor: (b) present, (a) missing. Kills: a build keyed
        on the replacement name alone — under which a line teaching BOTH states as
        live and current reads as a retirement notice.
        """
        text = f"- `{RETIRED_STATE_NAME}` and `{REPLACEMENT_STATE_NAME}` are both queued states.\n"
        assert unmarked_retired_name_lines("d.md", text) == [
            f"d.md:1: - `{RETIRED_STATE_NAME}` and `{REPLACEMENT_STATE_NAME}` are both queued states."
        ]

    def test_every_REAL_hit_line_is_MAPPED_so_the_fallback_is_not_load_bearing(self) -> None:
        """⚠ COVERAGE AS A CHECKED VARIABLE, not an assumption (repo law: a gate is
        an invariant only over the code it actually RUNS).

        The parser swap introduced a line class the hand-rolled splitter did not
        have: lines markdown-it consumes WITHOUT emitting a mapped token — thematic
        breaks and table delimiter rows, 180 of them across the swept docs. For
        those, ``unmarked_retired_name_lines`` falls back to "the line is its own
        block", which fails CLOSED. None can carry arbitrary text, so no real hit
        reaches that branch today — and THAT is the thing worth pinning: if a hit
        line ever lands unmapped, the fallback stops being dormant insurance and
        starts deciding verdicts, which is a change nobody would otherwise see.
        """
        unmapped: list[str] = []
        for relative, text in TestTheRetiredStateNameIsGoneFromTheTree._swept_docs().items():
            if RETIRED_STATE_NAME not in text:
                continue
            spans = _narrowest_block_spans(text)
            unmapped.extend(
                f"{relative}:{number}"
                for number, line in enumerate(text.splitlines(), 1)
                if RETIRED_STATE_NAME in line and number not in spans
            )
        assert not unmapped, (
            f"line(s) carrying the retired name are not covered by any markdown block token, so "
            f"their verdict now comes from the fail-closed FALLBACK rather than from a parsed "
            f"block: {unmapped}. That is safe (it rejects) but it is no longer the reviewed path — "
            f"add the token type to _BLOCK_TOKENS or confirm the fallback is what you want."
        )

    def test_the_REAL_docs_pass_BECAUSE_of_their_markers_not_by_accident(self) -> None:
        """⚠ THE LEG THAT BINDS THE SYNTHETIC CONVENTION TO THE ACTUAL TREE.

        Synthetic fixtures prove the parser; they cannot prove the tree's green is
        EARNED. So mutate the real doc text in memory — strip factor (a), then
        factor (b) — and require every real hit to become an offender both times.
        A tree that stayed green under either strip would be passing because the
        scan cannot see those lines, which is the O4 blind spot returning.
        """
        hits = TestTheRetiredStateNameIsGoneFromTheTree._doc_hits()
        assert hits, "no live doc carries the retired name — this control has nothing to prove"
        for relative, text in TestTheRetiredStateNameIsGoneFromTheTree._swept_docs().items():
            expected = len(hits.get(relative, []))
            if not expected:
                continue
            without_word = _RETIREMENT_WORD.sub("", text)
            assert len(unmarked_retired_name_lines(relative, without_word)) == expected, (
                f"{relative}: stripping every retirement word left some hit still admitted — "
                f"its block is being excused by something other than factor (a)"
            )
            without_name = text.replace(REPLACEMENT_STATE_NAME, "")
            assert len(unmarked_retired_name_lines(relative, without_name)) == expected, (
                f"{relative}: stripping the replacement name left some hit still admitted — "
                f"its block is being excused by something other than factor (b)"
            )


class TestTheSchemaAppliesToTheLiveEngine:
    """The generated DDL against the real 3.2.1 engine."""

    async def test_the_floor_slice_creates_both_tables(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _ = admin_db
        await run(connection, generate_floor_calibration_ddl())
        info = await run(connection, "INFO FOR DB")
        tables = set(info.get("tables", {}))
        assert {FLOOR_MEASUREMENT_TABLE, FLOOR_HEAD_TABLE} <= tables

    async def test_the_lease_slice_creates_its_table(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _ = admin_db
        await run(connection, generate_lease_ddl())
        assert LEASE_TABLE in set((await run(connection, "INFO FOR DB")).get("tables", {}))

    async def test_both_slices_are_safely_re_appliable(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """``ensure_ready`` re-applies the DDL on EVERY boot. A statement that
        raises on re-application is a boot-time crash, not a style issue."""
        connection, _ = admin_db
        for _ in range(2):
            await run(connection, generate_floor_calibration_ddl())
            await run(connection, generate_lease_ddl())

    async def test_an_UNKNOWN_state_string_is_rejected_by_the_store(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """The ledger's own validation is the ergonomic layer; THIS is the
        backstop for any writer that skips it."""
        connection, _ = admin_db
        await run(connection, generate_floor_calibration_ddl())
        with pytest.raises(Exception):  # noqa: B017 - any engine rejection is the pin
            await run(
                connection,
                f"CREATE type::record('{FLOOR_MEASUREMENT_TABLE}', 'bad') "
                f"CONTENT {{ state: 'not_a_real_state' }}",
            )

    async def test_an_UNKNOWN_non_adoption_cause_is_rejected_by_the_store(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _ = admin_db
        await run(connection, generate_floor_calibration_ddl())
        with pytest.raises(Exception):  # noqa: B017
            await run(
                connection,
                f"CREATE type::record('{FLOOR_MEASUREMENT_TABLE}', 'bad2') "
                f"CONTENT {{ state: 'measured_not_adopted', "
                f"non_adoption_cause: 'not_a_real_cause' }}",
            )

    async def test_the_lease_holder_column_accepts_NONE(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """``release_if_held`` sets the holder to NONE (decision 23). A required
        (non-``option``) holder column makes graceful release impossible — and
        store reference §1.4 records that a required NEW field also poisons every
        existing row, which a DEFAULT does NOT rescue."""
        connection, _ = admin_db
        await run(connection, generate_lease_ddl())
        await run(
            connection,
            f"UPSERT type::record('{LEASE_TABLE}', '{LEASE_SINGLETON_ID}') "
            f"CONTENT {{ holder_identity: NONE, revision: 0, fence_epoch: 0 }}",
        )
        rows = await run(
            connection,
            f"SELECT holder_identity, revision, fence_epoch FROM "
            f"type::record('{LEASE_TABLE}', '{LEASE_SINGLETON_ID}')",
        )
        assert rows and rows[0]["holder_identity"] is None

    async def test_the_lease_record_columns_accept_the_LIBRARYS_STRING_shapes(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """⚠ MEASURED, and it is a trap a ``datetime`` column walks straight
        into: ``kubernetes.leaderelection`` writes
        ``LeaderElectionRecord(identity, str(lease_duration), str(now), str(now))``
        — all four fields are STRINGS, and the times are NAIVE local datetimes
        (``datetime.datetime.fromtimestamp(time.time())``). A ``datetime``-typed
        ``renew_time`` rejects every renewal the library ever makes.
        """
        connection, _ = admin_db
        await run(connection, generate_lease_ddl())
        await run(
            connection,
            f"UPSERT type::record('{LEASE_TABLE}', '{LEASE_SINGLETON_ID}') "
            f"CONTENT {{ holder_identity: 'pod-a', lease_duration: '15', "
            f"acquire_time: '2026-07-26 15:18:30.327624', "
            f"renew_time: '2026-07-26 15:18:30.327665', revision: 0, fence_epoch: 0 }}",
        )
        rows = await run(
            connection,
            f"SELECT lease_duration, acquire_time, renew_time FROM "
            f"type::record('{LEASE_TABLE}', '{LEASE_SINGLETON_ID}')",
        )
        assert rows and rows[0]["lease_duration"] == "15"


class TestTheSchemaMigratesAnEXISTINGStore:
    """⚠ THE ONE PIN A VIRGIN-DB SUITE STRUCTURALLY CANNOT HAVE (§1.6).

    Every fixture in this repo mints a throwaway database, so no test had ever
    applied a schema change to an EXISTING store — which is why #107 passed
    1040 tests, a cold audit and a contract-adversary, and was caught only by
    the deploy smoke, after the outage.

    Shape (mirrors ``TestSchemaMigrationAgainstAnExistingStore``): apply a
    NARROWER definition -> insert a row the CURRENT schema allows but the narrow
    one forbids -> re-apply the real DDL -> assert the current constraint took
    effect AND the pre-existing row survived.
    """

    async def test_a_narrowed_state_assert_MIGRATES_back_to_the_full_set(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _ = admin_db
        await run(connection, generate_floor_calibration_ddl())

        # Stand in for an OLDER deployed schema: a state set missing one member.
        narrowed = ", ".join(f"'{state}'" for state in FLOOR_STATES if state != "disabled")
        await run(
            connection,
            f"DEFINE FIELD OVERWRITE state ON {FLOOR_MEASUREMENT_TABLE} "
            f"TYPE string ASSERT $value IN [{narrowed}]",
        )
        await run(
            connection,
            f"CREATE type::record('{FLOOR_MEASUREMENT_TABLE}', 'legacy') "
            f"CONTENT {{ state: 'measured' }}",
        )
        with pytest.raises(Exception):  # noqa: B017 - the narrow schema is really in force
            await run(
                connection,
                f"CREATE type::record('{FLOOR_MEASUREMENT_TABLE}', 'blocked') "
                f"CONTENT {{ state: 'disabled' }}",
            )

        # Re-apply the REAL slice, exactly as ``ensure_ready`` does at boot.
        await run(connection, generate_floor_calibration_ddl())

        # The widened definition LANDED (this is the #107 assertion) …
        await run(
            connection,
            f"CREATE type::record('{FLOOR_MEASUREMENT_TABLE}', 'now_allowed') "
            f"CONTENT {{ state: 'disabled' }}",
        )
        # … and the pre-existing row is intact, not rewritten and not dropped.
        rows = await run(
            connection,
            f"SELECT state FROM type::record('{FLOOR_MEASUREMENT_TABLE}', 'legacy')",
        )
        assert rows and rows[0]["state"] == "measured"


    async def test_the_LEASE_slice_migrates_a_NARROWED_field_on_an_existing_store(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """⚠ M14 — the lease slice had NO live migration leg at all.

        The clause pins give the rule ∀ reach over both slices (they caught a
        lease slice emitting ``DEFINE FIELD IF NOT EXISTS``), but a clause pin
        reads TEXT; only a dirty store proves the text does what it claims. And
        the lease row is the one row a long-lived deployment NEVER recreates —
        every fixture in this repo mints a virgin database, which is structurally
        why #107 passed 1040 tests and a cold audit.

        ``holder_identity`` is the field under test on purpose: decision 23
        requires it to accept NONE, so a narrowing that forbade NONE would break
        ``release_if_held`` on exactly the stores that already have a lease row.
        """
        connection, _ = admin_db
        await run(connection, generate_lease_ddl())

        # Stand in for an OLDER deployed schema: a REQUIRED holder column.
        await run(
            connection,
            f"DEFINE FIELD OVERWRITE holder_identity ON {LEASE_TABLE} TYPE string",
        )
        await run(
            connection,
            f"UPSERT type::record('{LEASE_TABLE}', '{LEASE_SINGLETON_ID}') "
            f"CONTENT {{ holder_identity: 'pod-legacy', revision: 0, fence_epoch: 0 }}",
        )
        with pytest.raises(Exception):  # noqa: B017 - the narrow schema is really in force
            await run(
                connection,
                f"UPDATE type::record('{LEASE_TABLE}', '{LEASE_SINGLETON_ID}') "
                f"SET holder_identity = NONE",
            )

        await run(connection, generate_lease_ddl())  # what ensure_ready does at boot

        # The widened definition LANDED …
        await run(
            connection,
            f"UPDATE type::record('{LEASE_TABLE}', '{LEASE_SINGLETON_ID}') "
            f"SET holder_identity = NONE",
        )
        # … and the pre-existing row survived rather than being recreated.
        rows = await run(
            connection,
            f"SELECT revision, fence_epoch FROM "
            f"type::record('{LEASE_TABLE}', '{LEASE_SINGLETON_ID}')",
        )
        assert rows and rows[0]["revision"] == 0

    async def test_the_FLOOR_HEAD_slice_migrates_a_NARROWED_field_on_an_existing_store(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """⚠ M14, second table. The head row is the OTHER row a live deployment
        never recreates — it is the adopted pointer, minted once per identity and
        UPSERTed forever after."""
        connection, _ = admin_db
        await run(connection, generate_floor_calibration_ddl())

        narrowed_scope = "'pooled'"
        await run(
            connection,
            f"DEFINE FIELD OVERWRITE scope ON {FLOOR_HEAD_TABLE} "
            f"TYPE string ASSERT $value IN [{narrowed_scope}]",
        )
        await run(
            connection,
            f"CREATE type::record('{FLOOR_HEAD_TABLE}', 'legacy_head') "
            f"CONTENT {{ scope: 'pooled' }}",
        )
        with pytest.raises(Exception):  # noqa: B017
            await run(
                connection,
                f"CREATE type::record('{FLOOR_HEAD_TABLE}', 'blocked_head') "
                f"CONTENT {{ scope: 'tier:lore' }}",
            )

        await run(connection, generate_floor_calibration_ddl())

        await run(
            connection,
            f"CREATE type::record('{FLOOR_HEAD_TABLE}', 'now_allowed_head') "
            f"CONTENT {{ scope: 'tier:lore' }}",
        )
        rows = await run(
            connection,
            f"SELECT scope FROM type::record('{FLOOR_HEAD_TABLE}', 'legacy_head')",
        )
        assert rows and rows[0]["scope"] == "pooled"


class TestNoMultiStatementDdlRidesABareQuery:
    """Store reference §3: the SDK's ``query()`` validates statement[0] ONLY, so
    a multi-statement DDL string sent through it can fail its third statement,
    roll the whole thing back, and raise NOTHING. This bit us as silent partial
    SCHEMA in all three ``ensure_ready`` paths.

    Keyed on the SAFE set: the two new modules may call ``execute_transaction``
    and ``run_query``; what they may not do is hand a multi-statement string to a
    connection directly.
    """

    @staticmethod
    def _module_sources() -> dict[str, str]:
        import loremaster.floor_calibration.store as floor_store  # noqa: PLC0415
        import loremaster.store.lease as lease_module  # noqa: PLC0415

        sources: dict[str, str] = {}
        for module in (floor_store, lease_module):
            path = module.__file__
            assert path is not None, f"{module.__name__} has no __file__ to scan"
            sources[module.__name__] = Path(path).read_text(encoding="utf-8")
        return sources

    def test_neither_module_calls_query_on_a_connection_directly(self) -> None:
        for name, source in self._module_sources().items():
            calls = [
                node
                for node in ast.walk(ast.parse(source))
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"query", "query_raw"}
                and not (isinstance(node.func.value, ast.Name) and node.func.value.id == "self")
            ]
            assert not calls, (
                f"{name} calls the SDK's query()/query_raw() directly; every statement "
                f"must ride `_txn.run_query` or `_txn.execute_transaction`"
            )

    def test_the_ddl_scan_can_actually_see_a_call(self) -> None:
        """CONTROL on the AST walk above — an analyser that matched nothing would
        make the pin silently green against any build."""
        source = "async def f(c):\n    await c.query('SELECT 1')\n"
        found: list[Any] = [
            node
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "query"
        ]
        assert len(found) == 1
