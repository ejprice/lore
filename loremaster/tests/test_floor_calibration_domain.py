"""Contract — packet 11-i-a, the PURE domain of floor calibration.

Written by `contract-11ia-1` (2026-07-26) against the ruled design; the builder
builds FROM this. No production implementation exists yet: every pin below is
RED with a ``NotImplementedError`` or an empty closed-set tuple, which is the
honest contract state.

WHAT THIS FILE DECIDES (the interface freeze 11-i-b cites):

    loremaster.store.surreal_schema:
        FLOOR_STATES: tuple[str, ...]                # 8, closed, exact
        FLOOR_NON_ADOPTION_CAUSES: tuple[str, ...]   # 5, closed, exact

    loremaster.floor_calibration.domain:
        FLOOR_HEAD_ALWAYS_SERIALISED_AXES: tuple[str, ...]
        FLOOR_HEAD_DEFAULTED_AXES: Mapping[str, str]
        MIN_ANSWERED_PROBES / MIN_IDENTIFIER_PROBES / MIN_ABSENT_SAMPLES
        head_identity(axes: Mapping[str, str]) -> str
        corpus_content_digest(rows: Iterable[Mapping[str, Any]]) -> str

⚠ WHY THE CLOSED SETS ARE PINNED AGAINST AN EXPLICIT LITERAL rather than
against "whatever the code says": these are SERVED state domains in 11-ii, and
this repo's #4 lesson is that a state set nothing pins acquires members nobody
decided. The pin's job is to make an addition or a removal a diff a reviewer
sees, which is exactly what a derived assertion cannot do.

⚠ AND WHY THE RETIRED NAME GETS ITS OWN PIN: F4.1 RENAMES
``stale_remeasuring`` to ``invalidated_remeasuring``. Repo rename law says a
suite can be green BECAUSE it still asserts the corpse, so the corpse is
asserted ABSENT here, with a bare pattern, and swept across the tree in
``test_floor_calibration_schema.py``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import orjson
import pytest
from loremaster.floor_calibration import domain as floor_domain
from loremaster.floor_calibration.domain import (
    FLOOR_HEAD_ALWAYS_SERIALISED_AXES,
    FLOOR_HEAD_DEFAULTED_AXES,
    MIN_ABSENT_SAMPLES,
    MIN_ANSWERED_PROBES,
    MIN_IDENTIFIER_PROBES,
    corpus_content_digest,
    corpus_meets_validity_floors,
    head_identity,
)
from loremaster.index.records import sha512_hex
from loremaster.store.surreal_schema import (
    FLOOR_NON_ADOPTION_CAUSES,
    FLOOR_STATES,
)

# --- the ruled literals ------------------------------------------------------

# §7's state table, with F4.1's rename applied. EIGHT, each distinct.
EXPECTED_FLOOR_STATES = (
    "unmeasured",
    "measuring",
    "measured",
    "measured_not_adopted",
    "invalidated_remeasuring",
    "measurement_failed",
    "insufficient_corpus",
    "disabled",
)

# F5's enum. FIVE, each distinct.
EXPECTED_NON_ADOPTION_CAUSES = (
    "head_retained_overlap",
    "catch_bar_unmet",
    "substrate_indiscriminate",
    "interval_degenerate",
    "stability_gate_unmet",
)

# F4.1's retired name, written out in full ON PURPOSE: repo rename law sweeps
# with BARE, anchor-free patterns, and a name spelled obliquely to "avoid a
# false hit" is a name the sweep cannot find.
RETIRED_STATE_NAME = "stale_remeasuring"

# The two axes F6 says ALWAYS serialize, and the one reserved at a default.
EXPECTED_ALWAYS_SERIALISED_AXES = ("scope", "statistic")
EXPECTED_DEFAULTED_AXES = {"query_shape": "any"}

# A representative axis mapping used throughout.
POOLED = {"scope": "pooled", "statistic": "cosine_floor"}


def _reference_head_preimage(serialised: dict[str, str]) -> bytes:
    """THE pre-image, under operator ruling O1: ``orjson.dumps`` with
    ``OPT_SORT_KEYS``.

    One line, in the test, on purpose — a golden digest with no visible
    derivation is a number nobody can check, and F6 records that changing this
    encoding after the table ships is a record-identity MIGRATION, not a
    refactor.

    ⚠ WHY THIS REPLACED A HAND-ROLLED ``\x00`` JOIN, because the reasoning is
    the point and not the diff: the bespoke encoding needed a NUL-refusal guard,
    a distinctness matrix built to defeat separator-naive joins, AND an
    escalation to rule which of two readings mints the identity. JSON admits one
    reading. The ambiguity was manufactured by the hand-roll (adversary P-PKG
    rows 8/9 — the two identity encodings had no package row at all, in the
    packet whose governing law is packages-over-hand-rolling).
    """
    return orjson.dumps(serialised, option=orjson.OPT_SORT_KEYS)


class TestTheStateSetIsClosedAndExact:
    """#4's lesson: a state domain nothing pins acquires members nobody ruled."""

    def test_the_state_set_is_exactly_the_ruled_eight(self) -> None:
        assert tuple(FLOOR_STATES) == EXPECTED_FLOOR_STATES, (
            "FLOOR_STATES is not the ruled §7/F4 set. A state added or removed "
            "here changes what 11-ii serves — say so in a diff a reviewer sees, "
            "never by editing the code and letting the pin follow."
        )

    def test_every_state_string_is_distinct(self) -> None:
        # The non-emptiness clause is not decoration: `len(set(())) == len(())`
        # is TRUE, so a distinctness pin over an empty domain is vacuously green.
        assert FLOOR_STATES, "FLOOR_STATES is empty — this pin would be vacuous"
        assert len(set(FLOOR_STATES)) == len(FLOOR_STATES), (
            f"duplicate state strings in FLOOR_STATES: {FLOOR_STATES}"
        )

    def test_the_retired_state_name_is_absent(self) -> None:
        """F4.1's rename. A suite can be green BECAUSE it still asserts the corpse."""
        assert FLOOR_STATES, "FLOOR_STATES is empty — absence proves nothing"
        assert RETIRED_STATE_NAME not in FLOOR_STATES, (
            f"{RETIRED_STATE_NAME!r} was RENAMED to 'invalidated_remeasuring' by F4.1 — "
            "the old name asserts AGEING, the surviving predicate is KNOWN-INVALID."
        )

    def test_the_states_are_a_tuple_not_a_mutable_set(self) -> None:
        """A closed domain that a caller can mutate at runtime is not closed.

        The non-emptiness clause is the SIXTH such guard, added after the
        adversary found this pin green over ``()`` — `isinstance((), tuple)` is
        true, so it certified nothing about the stub state.
        """
        assert FLOOR_STATES, "FLOOR_STATES is empty — this pin would be vacuous"
        assert isinstance(FLOOR_STATES, tuple)


class TestTheCauseEnumIsClosedAndExact:
    """F5. Five typed non-adoption causes, and the two-degeneracy split."""

    def test_the_cause_enum_is_exactly_the_ruled_five(self) -> None:
        assert tuple(FLOOR_NON_ADOPTION_CAUSES) == EXPECTED_NON_ADOPTION_CAUSES

    def test_every_cause_string_is_distinct(self) -> None:
        assert FLOOR_NON_ADOPTION_CAUSES, "the cause enum is empty — this pin would be vacuous"
        assert len(set(FLOOR_NON_ADOPTION_CAUSES)) == len(FLOOR_NON_ADOPTION_CAUSES)

    def test_the_two_degeneracies_are_separate_values(self) -> None:
        """RULED (F5), and it is the one clause a "simplification" would collapse.

        ``substrate_indiscriminate`` is a CORPUS property and earns the served
        sentence "semantic search discriminates poorly here". ``interval_degenerate``
        is an INSTRUMENT property and can occur on a perfectly discriminating
        corpus. Serving the second as the first is a confident corpus claim
        licensed by an instrument artifact — the confident-wrong class the
        client consult prices at session authority.
        """
        corpus_property, instrument_property = (
            "substrate_indiscriminate",
            "interval_degenerate",
        )
        assert corpus_property in FLOOR_NON_ADOPTION_CAUSES
        assert instrument_property in FLOOR_NON_ADOPTION_CAUSES
        assert corpus_property != instrument_property

    def test_no_cause_string_collides_with_a_state_string(self) -> None:
        """Two closed domains stored in two columns; a shared literal makes a
        mis-assignment invisible to every reader and to the store's ASSERTs."""
        assert FLOOR_STATES and FLOOR_NON_ADOPTION_CAUSES, (
            "one of the two domains is empty — a disjointness pin over an empty set "
            "is the emptiest kind of green"
        )
        assert not set(FLOOR_STATES) & set(FLOOR_NON_ADOPTION_CAUSES)


class TestTheHeadAxisRegistryIsClosed:
    """F6. The registry is closed, and ``query_shape`` is reserved NOW at ``any``."""

    def test_the_always_serialised_axes_are_exactly_scope_and_statistic(self) -> None:
        assert tuple(FLOOR_HEAD_ALWAYS_SERIALISED_AXES) == EXPECTED_ALWAYS_SERIALISED_AXES

    def test_query_shape_is_registered_now_at_default_any(self) -> None:
        """The whole point of registering it early: a future axis costs ZERO
        migration only if it is in the registry BEFORE the table ships."""
        assert dict(FLOOR_HEAD_DEFAULTED_AXES) == EXPECTED_DEFAULTED_AXES

    def test_no_axis_is_both_always_serialised_and_defaulted(self) -> None:
        assert FLOOR_HEAD_ALWAYS_SERIALISED_AXES and FLOOR_HEAD_DEFAULTED_AXES, (
            "an empty registry makes this disjointness pin vacuous"
        )
        assert not set(FLOOR_HEAD_ALWAYS_SERIALISED_AXES) & set(FLOOR_HEAD_DEFAULTED_AXES)


class TestHeadIdentityIsAFrozenFunctionOfItsAxes:
    """F6's ONE identity function. Every pin here is a property of the ID, not of
    a spelling — except the golden vector, which exists precisely to FREEZE the
    spelling, with its derivation written out three lines above it.
    """

    def test_the_golden_vector_freezes_the_encoding(self) -> None:
        """RED until the builder adopts the frozen reading. Deliberately a
        LITERAL digest as well as a derivation: a builder that "simplifies"
        ``_reference_head_preimage`` to match its own encoding still has to
        explain a changed literal, which is the migration this pin exists to
        make visible."""
        assert _reference_head_preimage(POOLED) == b'{"scope":"pooled","statistic":"cosine_floor"}'
        expected = sha512_hex(_reference_head_preimage(POOLED))
        assert expected == (
            "115284fbe56ca65fa8547f3e611bb446dcd388b80bdbb3d752a76b719e1d8555"
            "12e86b73b11b186279ed25d0a1007d84c9fb88f0b328552b66863f893521a2d8"
        ), "the in-test reference encoding drifted from the frozen id"
        assert head_identity(POOLED) == expected

    def test_the_id_is_a_lowercase_sha512_hex_digest(self) -> None:
        identity = head_identity(POOLED)
        assert len(identity) == 128
        assert identity == identity.lower()
        assert all(character in "0123456789abcdef" for character in identity)

    def test_the_id_does_not_depend_on_mapping_order(self) -> None:
        forwards = head_identity({"scope": "pooled", "statistic": "cosine_floor"})
        backwards = head_identity({"statistic": "cosine_floor", "scope": "pooled"})
        assert forwards == backwards

    def test_registering_a_new_axis_AT_ITS_DEFAULT_changes_no_existing_head_id(self) -> None:
        """F6's load-bearing consequence, stated as a mutation the caller can make.

        Supplying ``query_shape="any"`` — its registered default — must be
        BYTE-IDENTICAL to omitting it. A build that always serialises every
        registered axis passes every other pin in this class and silently
        re-mints every head the day a second axis is registered.
        """
        without = head_identity(POOLED)
        with_default = head_identity({**POOLED, "query_shape": "any"})
        assert with_default == without

    def test_a_NON_default_axis_value_mints_a_different_head(self) -> None:
        """The other half, and the reason the elision is not simply "ignore it"."""
        assert head_identity({**POOLED, "query_shape": "identifier"}) != head_identity(POOLED)

    def test_distinct_axis_mappings_mint_distinct_ids(self) -> None:
        """TWELVE mappings, chosen to defeat a separator-naive encoding — and
        computed in ONE test rather than parametrised, because a cross-parameter
        accumulator is sharded per worker under ``-n auto`` and would go
        VACUOUSLY green exactly when it mattered.

        ``{"scope": "tier:lore", "statistic": "cosine_floor"}`` vs
        ``{"scope": "tier", "statistic": "lore"}``, and the trailing-space pair,
        are the discriminating members: a build that joins on ``":"``, or that
        strips/normalises values, collapses them while every OTHER pin in this
        class still passes.
        """
        mappings: list[dict[str, str]] = [
            {"scope": "pooled", "statistic": "cosine_floor"},
            {"scope": "pooled", "statistic": "catch_rate"},
            {"scope": "tier:lore", "statistic": "cosine_floor"},
            {"scope": "tier:surrealdb-docs", "statistic": "cosine_floor"},
            {"scope": "tier:lore", "statistic": "catch_rate"},
            {"scope": "pooled", "statistic": "cosine_floor", "query_shape": "identifier"},
            {"scope": "tier:lore", "statistic": "cosine_floor", "query_shape": "identifier"},
            {"scope": "tier:lore:nested", "statistic": "cosine_floor"},
            {"scope": "tier", "statistic": "lore"},
            {"scope": "", "statistic": "cosine_floor"},
            {"scope": "pooled", "statistic": ""},
            {"scope": "pooled ", "statistic": "cosine_floor"},
            # ⚠ THE FORGERY ROW, kept after O1 retired the NUL-refusal guard.
            # Under the bespoke `\x00` join this value could splice a second
            # axis into the pre-image and a REFUSAL was the guard; under JSON,
            # NUL is escaped (`\u0000` — probed) so the forgery is impossible by
            # construction. The PROPERTY is what we depend on, so it stays
            # pinned here rather than dying with the encoding that needed it.
            {"scope": "pooled\x00statistic\x00forged", "statistic": "x"},
        ]
        identities = [head_identity(axes) for axes in mappings]
        assert len(set(identities)) == len(mappings), (
            "head id collision across the discriminating matrix: "
            f"{len(mappings)} distinct axis mappings minted "
            f"{len(set(identities))} distinct ids"
        )

    def test_a_missing_required_axis_is_REFUSED(self) -> None:
        """Not defaulted, not silently empty — refused. The required axes are what
        make a ``\\x00``-bearing value unable to forge a second axis: with both
        present, no single-axis pre-image can ever equal a two-axis one."""
        with pytest.raises(ValueError):
            head_identity({"scope": "pooled"})
        with pytest.raises(ValueError):
            head_identity({"statistic": "cosine_floor"})
        with pytest.raises(ValueError):
            head_identity({})

    def test_an_UNREGISTERED_axis_name_is_REFUSED(self) -> None:
        """The registry is CLOSED (F6). Accepting an unknown axis would mint a
        head nothing can ever resolve again, silently."""
        with pytest.raises(ValueError):
            head_identity({**POOLED, "embedder": "voyage-4-nano"})

    def test_a_NON_STRING_axis_value_is_REFUSED(self) -> None:
        """``str()``-coercing a value would make ``1`` and ``"1"`` the same head."""
        with pytest.raises((ValueError, TypeError)):
            head_identity({"scope": "pooled", "statistic": 3})  # type: ignore[dict-item]

    def test_the_non_string_refusal_is_a_ValueError_that_NAMES_the_axis(self) -> None:
        """⚠ **F6b (cold audit 11-i-a): the DOCUMENTED fate, pinned as documented.**

        The sibling above accepts ``ValueError`` OR ``TypeError`` — it was written before
        a builder existed and deliberately left the spelling open. Now that
        :func:`head_identity`'s public ``Raises:`` names ``ValueError`` (it did not, which
        is the audit finding), the promise and the pin must be the same thing: a consumer
        told to catch ``ValueError`` and handed a ``TypeError`` has an uncaught exception,
        and the loose pin cannot tell those two builds apart.

        The message must also NAME the offending axis. Not decoration: the raise this pins
        must be the registry's OWN refusal, not an incidental serializer failure from
        somewhere downstream — a build that deleted the ``isinstance`` check and let
        ``orjson`` decide would produce a DIFFERENT exception for a DIFFERENT reason, and a
        bare ``pytest.raises(ValueError)`` would happily accept a lookalike. This repo has
        the receipt for a probe that passed on a ``ParseError``.
        """
        with pytest.raises(ValueError, match="statistic") as exc_info:
            head_identity({"scope": "pooled", "statistic": 3})  # type: ignore[dict-item]
        assert "non-string" in str(exc_info.value), (
            f"the refusal does not say WHY it refused: {str(exc_info.value)!r}. A caller "
            f"reading this needs to know its value was rejected for its TYPE, not its name."
        )

        # POSITIVE CONTROL: the same mapping with a str value is ACCEPTED, so the pin above
        # is discriminating on the VALUE TYPE and not on something else about the fixture.
        assert len(head_identity({"scope": "pooled", "statistic": "3"})) == 128


class TestCorpusContentDigest:
    """C10's exact-skip datum. 11-i-a owns the row 11-ii will compare against;
    absent it, 11-ii's scheduler falls back to counts — the edit-blindness that
    is this design's original sin.

    ⚠ NO GOLDEN VECTOR HERE, deliberately, and the asymmetry with
    ``head_identity`` is the point: a re-encoded head id is a RECORD-IDENTITY
    migration (F6), while a re-encoded corpus digest merely forces one extra
    measurement. So the digest's ENCODING is the builder's, and only its
    DISCRIMINATION is pinned.
    """

    @staticmethod
    def _row(point_id: str, content_hash: str) -> dict[str, str]:
        return {"point_id": point_id, "content_hash": content_hash}

    def test_an_empty_corpus_yields_a_defined_digest(self) -> None:
        """A fresh instance has zero chunks; that must be a value, not a crash."""
        assert isinstance(corpus_content_digest([]), str)
        assert len(corpus_content_digest([])) == 128

    def test_the_same_walk_yields_the_same_digest(self) -> None:
        rows = [self._row("a", "h1"), self._row("b", "h2")]
        assert corpus_content_digest(rows) == corpus_content_digest(list(rows))

    def test_an_EDITED_chunk_changes_the_digest(self) -> None:
        before = [self._row("a", "h1"), self._row("b", "h2")]
        after = [self._row("a", "h1"), self._row("b", "h2-EDITED")]
        assert corpus_content_digest(before) != corpus_content_digest(after)

    def test_an_ADDED_chunk_changes_the_digest(self) -> None:
        before = [self._row("a", "h1")]
        assert corpus_content_digest(before) != corpus_content_digest(
            [*before, self._row("b", "h2")]
        )

    def test_a_REMOVED_chunk_changes_the_digest(self) -> None:
        before = [self._row("a", "h1"), self._row("b", "h2")]
        assert corpus_content_digest(before) != corpus_content_digest([self._row("a", "h1")])

    def test_a_REORDERED_walk_changes_the_digest(self) -> None:
        """The ascending-id order is a GUARANTEE the store makes (C8), and this
        pin is what makes that guarantee load-bearing rather than decorative: an
        order-insensitive digest would mask a store that stopped ordering."""
        rows = [self._row("a", "h1"), self._row("b", "h2")]
        assert corpus_content_digest(rows) != corpus_content_digest(list(reversed(rows)))

    def test_a_BOUNDARY_SHIFT_between_the_two_fields_changes_the_digest(self) -> None:
        """⚠ THE PIN THAT REFUTES C10'S LITERAL WORDING.

        C10 says the digest is over the "concatenation" of ``(point_id ‖
        content_hash)``. A BARE concatenation of two variable-length strings is
        forgeable: ``("ab", "c")`` and ``("a", "bc")`` produce identical bytes,
        so a corpus edit that moves one character across the boundary would be
        INVISIBLE to the exact-skip scheduler — a skipped re-measure on a
        changed corpus, which is the exact failure the datum exists to prevent.
        """
        assert corpus_content_digest([self._row("ab", "c")]) != corpus_content_digest(
            [self._row("a", "bc")]
        )

    def test_RELOCATION_alone_changes_the_digest(self) -> None:
        """⚠ M2 — THE DOOR THE ADVERSARY WALKED THROUGH (W5), measured.

        Two corpora with IDENTICAL content hashes and DIFFERENT ``point_id``s:
        a renamed symbol, or a moved file. C10's contract is *"equal ⇔ zero
        chunks added, removed, or edited ⇔ skip"*, so membership churn with
        unchanged content MUST move the digest — otherwise 11-ii's exact-skip
        skips a re-measure on a corpus that moved, and every other digest pin
        in this class stays green because each of them varies ``content_hash``
        and NONE of them varies ``point_id`` alone.

        A build that reads ``point_id`` and discards it produced a byte-identical
        digest across this fixture (`4e712e37…` before and after); the reference
        build did not (`ea57143a…` → `73ddebb9…`).
        """
        before = [self._row("pkg/old.py::Thing.method", "h1"), self._row("pkg/b.py::X", "h2")]
        after = [self._row("pkg/new.py::Thing.method", "h1"), self._row("pkg/c.py::X", "h2")]
        assert [row["content_hash"] for row in before] == [row["content_hash"] for row in after], (
            "the fixture must hold every content hash FIXED — otherwise a "
            "content-only digest would pass it and it would prove nothing"
        )
        assert corpus_content_digest(before) != corpus_content_digest(after)

    def test_a_row_missing_a_required_field_RAISES(self) -> None:
        """Never a silent empty-string substitution: that would make a corpus
        with an unset ``content_hash`` digest-identical to one without the row."""
        with pytest.raises(KeyError):
            corpus_content_digest([{"point_id": "a"}])
        with pytest.raises(KeyError):
            corpus_content_digest([{"content_hash": "h"}])


class TestThePreImageEncodingIsUsedInExactlyOnePlace:
    """⚠ **THE F3 INSTRUMENT (cold audit 11-i-a) — and it MUST be structural.**

    ``domain.py`` declares the pre-image encoding "in ONE place" (``_PREIMAGE_OPTIONS``,
    operator ruling O1) and states that BOTH pre-images use it. ``corpus_content_digest``
    called ``orjson.dumps(pairs)`` with no ``option=`` at all — a second encoding site
    bypassing the named single place, which is the ONE-IMPLEMENTATION law's *routing is not
    sharing* in miniature.

    ⚠ **NO BEHAVIOURAL TEST CAN CATCH IT, and that is the whole argument for this class.**
    The corpus pre-image is a LIST of pairs; a list has no keys, so ``OPT_SORT_KEYS`` is
    byte-neutral there. Both spellings produce identical bytes and identical digests today,
    so every digest pin in :class:`TestCorpusContentDigest` stays green either way. The
    divergence only becomes visible on the day someone adds an option to
    ``_PREIMAGE_OPTIONS`` (``OPT_NON_STR_KEYS``, a future sort flag) or reshapes the
    corpus pre-image into a mapping — i.e. on the day the head id and the corpus digest
    silently stop agreeing about what encoding this module uses.

    So the invariant is over the SOURCE: every ``orjson.dumps`` call in the module passes
    ``option=_PREIMAGE_OPTIONS``, by NAME. It is an ALLOWLIST (what a call must look like),
    never a list of forbidden spellings.
    """

    @staticmethod
    def _dumps_calls() -> list[ast.Call]:
        """Every ``orjson.dumps(...)`` call in the production domain module."""
        source = Path(floor_domain.__file__).read_text(encoding="utf-8")
        return [
            node
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Call)
            and (
                (isinstance(node.func, ast.Attribute) and node.func.attr == "dumps")
                or (isinstance(node.func, ast.Name) and node.func.id == "dumps")
            )
        ]

    def test_the_scan_actually_finds_the_encoding_calls(self) -> None:
        """THE REACH CONTROL. A scan that matched nothing would certify this module
        forever, which is this repo's documented way for a mechanical gate to pass while
        proving nothing."""
        calls = self._dumps_calls()
        assert len(calls) >= 2, (
            f"the AST scan found {len(calls)} `orjson.dumps` call(s) in "
            f"{Path(floor_domain.__file__).name} — this pin was written against the TWO "
            f"pre-images O1 names (the head identity and the corpus digest). Either they "
            f"were consolidated (good — lower this floor deliberately, in a diff a reviewer "
            f"can see) or the SCANNER broke and the assertion below just went vacuously green."
        )

    def test_every_pre_image_passes_the_ONE_encoding_constant_BY_NAME(self) -> None:
        offenders: list[tuple[int, str]] = []
        for call in self._dumps_calls():
            option = next((kw for kw in call.keywords if kw.arg == "option"), None)
            if option is None:
                offenders.append((call.lineno, "no `option=` at all"))
            elif not (isinstance(option.value, ast.Name) and option.value.id == "_PREIMAGE_OPTIONS"):
                offenders.append((call.lineno, f"option={ast.unparse(option.value)}"))

        assert not offenders, (
            "an `orjson.dumps` pre-image in "
            f"{Path(floor_domain.__file__).name} does not go through `_PREIMAGE_OPTIONS`:\n  "
            + "\n  ".join(f"line {lineno}: {why}" for lineno, why in offenders)
            + "\n\nThe module declares the pre-image encoding 'in ONE place' (O1) and says "
            "BOTH pre-images use it. A call that spells the options itself — or omits them — "
            "is a SECOND encoding site wearing the shared name, and no behavioural pin can "
            "see it while the two spellings happen to agree byte-for-byte (they do today: "
            "a list has no keys to sort). Pass `option=_PREIMAGE_OPTIONS`; if a pre-image "
            "genuinely needs different options, that is a DESIGN decision about record "
            "identity — escalate it, do not write the second spelling."
        )


class TestTheValidityFloorsArePreRegistered:
    """F4.2 — the 30/15/30 floors, RESTORED as a predicate D0's retirement
    sentence removed. They gate VALIDITY only; adopted N is chosen solely by F1.
    Named constants rather than literals at a call site because they are
    pre-registered and adversary-attackable.
    """

    def test_the_three_floors_are_the_ruled_values(self) -> None:
        assert (MIN_ANSWERED_PROBES, MIN_IDENTIFIER_PROBES, MIN_ABSENT_SAMPLES) == (30, 15, 30)

    def test_the_identifier_floor_is_NOT_the_same_number_as_the_others(self) -> None:
        """A fixture-alignment guard on the CONSTANTS themselves: three floors
        that happen to be equal make a build reading the wrong one indetectable.
        """
        assert MIN_IDENTIFIER_PROBES != MIN_ANSWERED_PROBES


class TestTheValidityFloorsAreACTUALLYCONSUMED:
    """⚠ M13 — before this class the three floors were pinned as VALUES that
    NOTHING READ (`grep MIN_` matched only the two assertions above), so a build
    could hard-code 30/15/30 at a call site, or read the wrong one of the three,
    with every pin green. The lead's E4 ruling asserted these were "already
    pinned"; that clause was withdrawn, and this class is what makes it true.

    Boundaries are cap−1 / cap / cap+1 on EACH axis independently, which is also
    what catches an off-by-one in the comparison operator.
    """

    @staticmethod
    def _call(*, answered: int, identifier: int, absent: int) -> bool:
        return corpus_meets_validity_floors(
            answered_probes=answered, identifier_probes=identifier, absent_samples=absent
        )

    def test_a_corpus_exactly_AT_every_floor_is_sufficient(self) -> None:
        """AT the floor, not above it: F4.2 says "≥", and a ">" reads identically
        in prose while rejecting a corpus the design accepts."""
        assert self._call(
            answered=MIN_ANSWERED_PROBES,
            identifier=MIN_IDENTIFIER_PROBES,
            absent=MIN_ABSENT_SAMPLES,
        )

    def test_a_corpus_ABOVE_every_floor_is_sufficient(self) -> None:
        assert self._call(
            answered=MIN_ANSWERED_PROBES + 1,
            identifier=MIN_IDENTIFIER_PROBES + 1,
            absent=MIN_ABSENT_SAMPLES + 1,
        )

    def test_ONE_short_answered_probe_is_insufficient(self) -> None:
        assert not self._call(
            answered=MIN_ANSWERED_PROBES - 1,
            identifier=MIN_IDENTIFIER_PROBES,
            absent=MIN_ABSENT_SAMPLES,
        )

    def test_ONE_short_identifier_probe_is_insufficient(self) -> None:
        """The axis a build reading the WRONG constant gets wrong: 15 is the odd
        one out, so a build that used ``MIN_ANSWERED_PROBES`` everywhere passes
        the other two legs and fails only here."""
        assert not self._call(
            answered=MIN_ANSWERED_PROBES,
            identifier=MIN_IDENTIFIER_PROBES - 1,
            absent=MIN_ABSENT_SAMPLES,
        )

    def test_ONE_short_absent_sample_is_insufficient(self) -> None:
        assert not self._call(
            answered=MIN_ANSWERED_PROBES,
            identifier=MIN_IDENTIFIER_PROBES,
            absent=MIN_ABSENT_SAMPLES - 1,
        )

    def test_the_predicate_READS_the_constants_rather_than_re_typing_them(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PROVE SHARING BY MUTATION — the only test that distinguishes reading
        the constant from hard-coding its current value. Raise the answered floor
        and a corpus that was sufficient must stop being sufficient.
        """
        monkeypatch.setattr(floor_domain, "MIN_ANSWERED_PROBES", MIN_ANSWERED_PROBES + 50)
        assert not self._call(
            answered=MIN_ANSWERED_PROBES,
            identifier=MIN_IDENTIFIER_PROBES,
            absent=MIN_ABSENT_SAMPLES,
        ), (
            "raising MIN_ANSWERED_PROBES changed no verdict — the predicate "
            "hard-codes the floor instead of reading it"
        )
