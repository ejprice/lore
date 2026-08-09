"""INSTRUMENT E (finding #289) — the trailing-newline malformed-input matrix, as a CLASS invariant.

This is a MIXED-COLOUR contract on purpose (stated up front so a reader is not surprised):

  * PART 1 — the #289 INSTANCE, mutation-proven. These pins are GREEN at HEAD ``e1dfa14`` (the
    ``.fullmatch`` fix landed in packet 44) and go RED on the named wrong build. They exist because
    the instance shipped GREEN through a 171-pin contract with NO trailing-newline case anywhere in
    ``Exemption``'s malformed-row matrix (see ``test_gated_ground.py`` ::
    ``TestTheExemptionTableIsAnAllowlistOfTheSafe.test_a_malformed_row_is_rejected_by_the_tables_own_validation``
    — its cases are ``""`` / ``"188"`` / ``"see the ledger"``, none carrying ``\\n``, so ``.match``
    and ``.fullmatch`` agree on all of them). A fix without a discriminating pin (finding #289 body,
    "TWO GENERALISATIONS", item 1).

  * PART 2 — the CLASS helper ``scripts/_newline_matrix.py::newline_forgery_variants``, which DOES
    NOT EXIST at ``e1dfa14`` (RED — imported dynamically so the typecheck gate stays green while
    pytest is red). It turns "a contract's malformed-input matrix must carry a trailing-newline case
    for EVERY field it interpolates into served text" from a REMEMBERED PROPERTY (a diagnosis is not
    an instrument — CLAUDE.md) into a reusable ENUMERATION a contract author CALLS, so the ``\\n``
    case for a declared field cannot be silently omitted.

THE DEFECT #289 NAMES, in one sentence. ``gated_ground.Exemption`` BARE-interpolates ``finding``
into a served failure message (``_validate_reopen_trigger``: ``…does not cite {self.finding}``). Its
validator compiles ``^#\\d+$`` and validated with ``.match`` — and Python's ``$`` matches immediately
before a TRAILING NEWLINE, so ``.match("#188\\n")`` is a match while ``.fullmatch("#188\\n")`` is
``None``. A row with ``finding == "#188\\n"`` was constructible, and it injects a line into every
message that renders it — the same forgery class the contract already pinned for PATHS, reappearing
through a field whose malformed matrix had no ``\\n`` case.

THE HONEST BOUND (design doc §INSTRUMENT E — MEASURED, not argued). WHICH fields a validator
"interpolates into served text" as a FORGEABLE slot is a JUDGEMENT, not a name-blind-derivable
property: a field rendered with ``!r`` (repr) escapes a newline and is SAFE; a field interpolated
bare is a DOOR. In ``Exemption`` only ``finding`` is a bare door — ``root`` / ``reason`` /
``reopen_trigger`` are all ``!r``. So the helper does NOT decide the field set: it enumerates the
``\\n`` case for WHATEVER fields the author declares, making a forgotten case impossible while
leaving the field-classification where the judgement actually is. (This is INSTRUMENT B's stance one
surface over: derive the inventory so a wrong judgement SURFACES as a missing/undriven case; do not
pretend to remove the judgement.)

THE KILLED WRONG BUILD (named for the builder to add to ``scripts/wrong_builds.py`` — OUTSIDE this
contract author's writable set):

    WB22_finding_number_validated_with_match
      anchor:      ``if not _FINDING_NUMBER.fullmatch(self.finding):``
      replacement: ``if not _FINDING_NUMBER.match(self.finding):``

    On that build ``Exemption(finding="#188\\n", …)`` CONSTRUCTS (the newline slips past ``.match``),
    so ``test_a_finding_number_with_a_trailing_newline_is_rejected`` below FAILS — the pin doing its
    job. The fixture there is built so the ONLY thing between "constructs" and "rejected" is the
    ``fullmatch``-vs-``match`` decision (see its comment).

WHY THIS CONTRACT LIVES IN ``scripts/`` and is gated on both axes. ``scripts`` is a ``testpaths``
entry AND a ``scripts/typecheck.sh`` MEMBERS root (ruling F1), so this file and the helper it pins
are covered by pytest AND mypy from birth — and ``gated_ground.py``'s own LEG A / LEG B quantify
over both.

How to run:  uv run pytest scripts/test_trailing_newline_matrix.py -n auto -q
"""

from __future__ import annotations

import importlib
import os
import sys
from typing import Any

import pytest

# ``scripts/`` is not a package; the path insert must precede the sibling import, exactly as every
# other contract in this directory does it (test_gated_ground, test_wrong_builds, …).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gated_ground as gg  # noqa: E402  (path insert must precede the import)


def _valid_exemption_kwargs() -> dict[str, object]:
    """A WELL-FORMED ``Exemption`` kwargs dict — the row every case perturbs by exactly one field.

    Kept identical in shape to ``test_gated_ground.py``'s own valid fixture, so a drift in the real
    validator's required fields reddens this contract too.
    """
    return {
        "root": "docs/consult",
        "axis": gg.GateAxis.TYPES,
        "finding": "#188",
        "reason": "standing disposition: its own work item, config half first",
        "reopen_trigger": "the #188 cleanup lands; delete this row and the leg goes live",
    }


class TestTheFindingNumberValidatorRejectsATrailingNewline:
    """PART 1 — the #289 instance, mutation-proven against WB22_finding_number_validated_with_match.

    GREEN at HEAD ``e1dfa14``; RED on the ``.match`` wrong build named in the module docstring.
    """

    def test_match_and_fullmatch_disagree_on_a_trailing_newline(self) -> None:
        """REGEX-LEVEL CONTROL — the fixture value ``"#188\\n"`` actually distinguishes the wrong
        build from the fix, at the exact seam #289 is about. Without this, the construction pin
        below could pass on BOTH builds and prove nothing (FIXTURES MUST DISCRIMINATE — CLAUDE.md).
        """
        assert gg._FINDING_NUMBER.match("#188\n") is not None  # the BUG: .match ACCEPTS it
        assert gg._FINDING_NUMBER.fullmatch("#188\n") is None  # the FIX: .fullmatch REJECTS it

    def test_a_finding_number_with_a_trailing_newline_is_rejected(self) -> None:
        kwargs = _valid_exemption_kwargs()
        kwargs["finding"] = "#188\n"
        # The re-open trigger must LITERALLY embed "#188\n" so that on the ``.match`` wrong build the
        # row CONSTRUCTS (its cite check ``finding in reopen_trigger`` then passes) and the ONLY
        # thing separating "constructs" from "rejected" is the fullmatch-vs-match decision on
        # ``finding``. On the ``.fullmatch`` build the finding check raises FIRST, before the cite
        # check is ever reached, so this embedding is irrelevant there. Without it, a ``.match``
        # build would still raise — but for the WRONG reason (cite failure), and the pin would pass
        # on both builds: the "probe fires for the wrong reason" trap (CLAUDE.md, PKT-28 C1).
        kwargs["reopen_trigger"] = "the #188\n cleanup lands; delete this row"
        with pytest.raises(gg.InvalidExemption) as excinfo:
            gg.Exemption(**kwargs)  # type: ignore[arg-type]
        # POSITIVE CONTROL on the REASON: rejected AS a bad finding number, not for something else.
        assert "not a finding number" in str(excinfo.value)

    def test_the_same_finding_number_without_the_newline_is_accepted(self) -> None:
        """NEGATIVE CONTROL — the good input constructs. Without it, a validator that rejected
        EVERY finding would pass the pin above for the wrong reason."""
        row = gg.Exemption(**_valid_exemption_kwargs())  # type: ignore[arg-type]
        assert row.finding == "#188"


class TestTheReusableTrailingNewlineMatrix:
    """PART 2 — ``scripts/_newline_matrix.py::newline_forgery_variants`` (RED: does not exist yet).

    INTENDED SIGNATURE (the builder implements to this; the contract calls it dynamically):

        def newline_forgery_variants(
            base: Mapping[str, object],
            interpolated_fields: Sequence[str],
        ) -> list[tuple[str, dict[str, object]]]: ...

    THE PROPERTY: given the valid field values and the list of fields a validator interpolates into
    served text, produce ONE variant per field whose ONLY difference from ``base`` is a trailing
    newline on that field — so a contract author enumerates the ``\\n`` matrix by CALLING, and cannot
    silently omit a declared field's case (which is exactly how #289 shipped green).
    """

    @staticmethod
    def _variants() -> Any:
        """Dynamic import of the NOT-YET-BUILT class helper.

        ``importlib.import_module`` (not ``from _newline_matrix import …``) so mypy does not
        hard-error on a module absent at ``e1dfa14`` — the typecheck gate over ``scripts/`` must stay
        GREEN while this pytest contract is RED. At runtime the missing module raises
        ``ModuleNotFoundError`` inside each test body, which is the RED this contract owes.
        """
        return importlib.import_module("_newline_matrix").newline_forgery_variants

    def test_it_yields_exactly_one_variant_per_declared_field(self) -> None:
        variants = self._variants()({"finding": "#188", "root": "docs"}, ["finding", "root"])
        assert [field for field, _kwargs in variants] == ["finding", "root"]

    def test_each_variant_appends_a_trailing_newline_to_exactly_that_field(self) -> None:
        base = {"finding": "#188", "root": "docs"}
        by_field = {field: kwargs for field, kwargs in self._variants()(base, ["finding", "root"])}
        # the named field gains exactly a "\n"; every other field is copied through untouched
        assert by_field["finding"] == {"finding": "#188\n", "root": "docs"}
        assert by_field["root"] == {"finding": "#188", "root": "docs\n"}

    def test_it_does_not_mutate_the_base_mapping(self) -> None:
        base = {"finding": "#188", "root": "docs"}
        self._variants()(base, ["finding"])
        assert base == {"finding": "#188", "root": "docs"}

    def test_an_empty_field_list_is_refused_as_vacuous(self) -> None:
        """ANTI-VACUITY on the MATRIX itself (the #290 lesson applied here): a matrix over ZERO
        fields enumerates nothing and certifies nothing, yet a naive helper would return ``[]`` and
        every downstream ``for … in variants`` loop would pass by iterating nothing. A loud
        ``ValueError`` refusal, not a silent empty list."""
        with pytest.raises(ValueError):
            self._variants()({"finding": "#188"}, [])

    def test_a_field_absent_from_the_base_is_refused(self) -> None:
        """A field you cannot build a case for is a SILENT MISS — the helper must REFUSE loudly, not
        skip it (skipping is how a declared field ends up with no ``\\n`` case anyway). Pinned as
        ``ValueError`` — a diagnostic refusal — rather than a raw ``KeyError`` from ``base[field]``.
        """
        with pytest.raises(ValueError):
            self._variants()({"finding": "#188"}, ["reopen_trigger"])

    def test_the_matrix_drives_the_real_exemption_door_field(self) -> None:
        """INTEGRATION — the reusable form of PART 1. Feeding ``Exemption``'s ONE bare-interpolated
        door field (``finding``) through the matrix produces the ``"#188\\n"`` row, and the real
        validator REJECTS it. This is what a future contract author gets 'for free' by CALLING the
        helper instead of hand-writing the case.

        Discriminates WB22: the base re-open trigger embeds ``"#188\\n"`` so on the ``.match`` build
        the row would construct and this ``raises`` would fail.
        """
        base = _valid_exemption_kwargs()
        base["reopen_trigger"] = "the #188\n cleanup lands; delete this row"
        variants = self._variants()(base, ["finding"])
        ((_field, kwargs),) = variants
        assert kwargs["finding"] == "#188\n"
        with pytest.raises(gg.InvalidExemption):
            gg.Exemption(**kwargs)
