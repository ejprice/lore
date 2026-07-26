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

import pytest
from loremaster.floor_calibration.domain import (
    FLOOR_HEAD_ALWAYS_SERIALISED_AXES,
    FLOOR_HEAD_DEFAULTED_AXES,
    MIN_ABSENT_SAMPLES,
    MIN_ANSWERED_PROBES,
    MIN_IDENTIFIER_PROBES,
    corpus_content_digest,
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


def _reference_head_preimage(serialised: dict[str, str]) -> str:
    """THE FROZEN READING of F6's "sorted ``(axis_name, value)`` pairs joined by
    ``\\x00``": flatten each pair in order and join every element with ``\\x00``.

    Three lines, in the test, on purpose — a golden digest with no visible
    derivation is a number nobody can check, and F6 records that changing this
    encoding after the table ships is a record-identity MIGRATION, not a
    refactor. (The alternative reading — an intra-pair separator distinct from
    the inter-pair one — is escalated in the contract report; it produces a
    different frozen id and must be settled before the table ships.)
    """
    flattened: list[str] = []
    for name, value in sorted(serialised.items()):
        flattened.extend((name, value))
    return "\x00".join(flattened)


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
        """A closed domain that a caller can mutate at runtime is not closed."""
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
        expected = sha512_hex(_reference_head_preimage(POOLED))
        assert expected == (
            "c52fce03d1fb6186eb0953bb8c7892e49dde62a39f43988d7de07995052882b9"
            "0ab917367531c271d9644375cea7ed51e671ef0c94d21a984d2da80edaf148cf"
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

    def test_a_value_carrying_the_PREIMAGE_SEPARATOR_is_REFUSED(self) -> None:
        """A hostile fixture, and the reason the guard is a refusal rather than
        an escape: a value able to contain the separator can splice a forged
        axis into the pre-image. Refusing is checkable; escaping is one more
        encoding nobody pins."""
        with pytest.raises(ValueError):
            head_identity({"scope": "pooled\x00statistic\x00forged", "statistic": "x"})

    def test_a_NON_STRING_axis_value_is_REFUSED(self) -> None:
        """``str()``-coercing a value would make ``1`` and ``"1"`` the same head."""
        with pytest.raises((ValueError, TypeError)):
            head_identity({"scope": "pooled", "statistic": 3})  # type: ignore[dict-item]


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

    def test_a_row_missing_a_required_field_RAISES(self) -> None:
        """Never a silent empty-string substitution: that would make a corpus
        with an unset ``content_hash`` digest-identical to one without the row."""
        with pytest.raises(KeyError):
            corpus_content_digest([{"point_id": "a"}])
        with pytest.raises(KeyError):
            corpus_content_digest([{"content_hash": "h"}])


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
