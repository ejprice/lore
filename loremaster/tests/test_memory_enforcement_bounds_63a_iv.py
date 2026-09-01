"""Contract — packet 63a-iv: the F5 NAMED BOUNDS (design §10.9-A; WHEN YOU CANNOT CLOSE A HOLE,
PIN IT). Authored by ``build-63a-iv`` per the wave brief (the F-2/F-3 bound-note deliverable).

The F5 enforcement instrument has two inherent, right-sized bounds the adversary named
(REPORT-adversary-63a-iv §F-2/§F-3). This module PINS the F-2 bound so it is met DELIBERATELY, with
its rationale attached, and can never be silently inherited OR silently "fixed":

- **F-2 (finding #444) — L1 is blind to a dynamically-named governed write.** The L1 AST scan
  ``governed_table_raw_mutation_sites`` matches a statement SHAPE targeting the literal table name
  ``memory`` or its interpolated module CONSTANT (``{MEMORY_TABLE}``). A raw write whose table name
  is a runtime VARIABLE (``tbl = self._which_table(); f"UPDATE type::record('{tbl}', …)"``) renders
  ``{tbl}`` and matches neither anchor, so it is never derived and deny-by-default never fires. NOT
  closed deliberately: all real memory sites use the ``MEMORY_TABLE`` constant, so widening the scan
  buys nothing and adds false-positive risk. The pin below ASSERTS the hole exists (with a positive
  control that the constant-named form IS derived), so it goes RED the day L1 is widened — the
  signal to delete it and re-adjudicate. RE-OPEN TRIGGER: any production write that constructs a
  governed table name dynamically (a non-constant table argument to a memory mutation).

(The F-3 bound — L2b runtime reach covers only the member-verb seam paths — is documented as a
NAMED BOUND on ``_governed_contract.observe_governed_table_writes`` (finding #445); it is a
coverage-shape note, not a discriminable pinnable hole, so it lives as prose there.)

Store-free (pure AST over a synthetic source string).
"""

from __future__ import annotations

from _governed_contract import (
    MEMORY_TABLE,
    MutationSite,
    governed_table_raw_mutation_sites,
)

_TABLE = MEMORY_TABLE

# A synthetic module source with TWO raw memory UPDATEs: one via the MEMORY_TABLE constant (the
# idiomatic, DERIVED shape) and one via a runtime VARIABLE table name (the F-2 blind spot).
_SYNTH_SOURCE = '''
MEMORY_TABLE = "memory"


class _Backend:
    def _which_table(self):
        return "memory"

    async def _constant_named_write(self, x):
        await self._query(
            f"UPDATE type::record('{MEMORY_TABLE}', $id) SET scope = 'seized'", {"id": x}
        )

    async def _dynamically_named_write(self, x):
        tbl = self._which_table()
        await self._query(
            f"UPDATE type::record('{tbl}', $id) SET scope = 'seized'", {"id": x}
        )
'''


class TestL1IsBlindToADynamicallyNamedGovernedWrite:
    """F-2 NAMED BOUND (finding #444). ASSERTS the L1 hole exists — a runtime-variable table name is
    NOT derived — with a POSITIVE CONTROL that the constant-named site IS derived (so the bound is a
    real blind spot, never a broken scanner). Goes RED the day L1 is widened to catch the dynamic
    form: delete this pin then and re-adjudicate (WHEN YOU CANNOT CLOSE A HOLE, PIN IT)."""

    def test_a_constant_named_raw_memory_write_is_derived(self) -> None:
        # POSITIVE CONTROL — the scan is NOT simply blind: the idiomatic constant-named write IS
        # derived, so the "not derived" assertion below is a real blind spot, not a broken scanner.
        derived = governed_table_raw_mutation_sites(_SYNTH_SOURCE, _TABLE)
        assert MutationSite("_constant_named_write", "UPDATE") in derived, (
            "the L1 scan failed to derive an idiomatic constant-named memory write — the scanner is "
            "broken, so the bound pin below would be vacuous"
        )

    def test_a_dynamically_named_raw_memory_write_is_not_derived(self) -> None:
        # THE BOUND (finding #444): a runtime-variable table name renders '{tbl}', matches neither
        # the literal 'memory' nor the MEMORY_TABLE constant hint, and is never derived — deny-by-
        # default cannot see it. If someone WIDENS L1 to catch this, this pin REDS: that is the
        # signal to delete it and re-adjudicate the bound (per WHEN YOU CANNOT CLOSE A HOLE, PIN IT).
        derived = governed_table_raw_mutation_sites(_SYNTH_SOURCE, _TABLE)
        assert MutationSite("_dynamically_named_write", "UPDATE") not in derived, (
            "L1 now DERIVES a dynamically-named governed write (finding #444's bound is CLOSED) — if "
            "you widened the scan deliberately, DELETE this pin and re-adjudicate the F-2 bound"
        )
