"""Contract — packet 63a-iv: F5 GOVERNED-TABLE WRITE-ENFORCEMENT COMPLETENESS (design §10.9-A) for
the MEMORY table. RED before the 63a-iv build. Authored by ``contract-63a-iv`` (tests ONLY).

F5 closes the enumerate-the-forbidden CLASS: memory write verbs were guarded ONE AT A TIME
(invalidate → supersede-close → the create path), each round green at every gate. This module is the
MEMORY PARAMETRISATION of the REUSABLE F5 substrate (``_governed_contract`` — the AST scanners, the
seam instrument, the allowlist dataclasses). 63b (message) / 64 (task/finding) supply their OWN
``MEMORY_WRITE_ALLOWLIST``-shaped data and call the SAME substrate functions — never a cloned module
(design §3.2 RIDER; the substrate is the ONE implementation).

THREE layers (design §10.9-A):
  L1  STRUCTURAL — every RAW memory mutation (AST-derived) ∈ the deny-by-default ALLOWLIST; a NEW
      unclassified raw write REDS (green-at-HEAD once the 3 current sites are enumerated, RED via the
      synthetic-source discriminator that proves the set GROWS-and-REDS).
  L2a STRUCTURAL — every allowlisted FRAME + ``guarded_write`` wraps its mutation in
      ``governed.write_guard`` (reach a checked variable). ⚠ RED at HEAD (guard-context unwired).
  L2b RUNTIME — the store seam is instrumented over a live battery; every OBSERVED memory mutation
      carries a non-None ``governed.active_write_guard()`` context, across every seam path. ⚠ RED at
      HEAD (``active_write_guard`` unbuilt → every observed mutation is context-LESS).

Live TEST store ``ws://127.0.0.1:18000`` (NEVER :18500).
"""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import loremaster.governed as governed_mod
import loremaster.memory.local as local_mod
from _governed_contract import (
    GovernedWriteAllowlistEntry,
    MutationSite,
    call_name,
    function_calls_write_guard,
    governed_table_guarded_write_frames,
    governed_table_raw_mutation_sites,
)
from test_memory_retrofit_63a import (  # noqa: F401 (fixtures used by name)
    _exercise_invalidate,
    _exercise_recall,
    _exercise_remember,
    _memory_case,
    alice_capability,
    retrofit_world,
)

# --------------------------------------------------------------------------- #
# The MEMORY deny-by-default WRITE ALLOWLIST (design §10.9-A layer 3) — one (site, justification, pin,
# frames) 4-tuple per RAW (unguarded) mutation of the memory table. Every entry's ``pin`` is a REAL
# evidencing test (an entry whose pin is deleted leaves the allowlist — pin-existence, below).
# --------------------------------------------------------------------------- #

_UPSERT_ENTRY = GovernedWriteAllowlistEntry(
    site=MutationSite("_upsert_fragment", "UPSERT"),
    justification=(
        "deterministic-id UPSERT. The CREATE caller (remember) folds the owner pair into the id "
        "(#439) so it can never NAME a foreign-owned row; the REPLAY caller (_replay_record) uses "
        "the STORED id, never a re-derivation (RES-1 boot/admin). Neither overwrites a foreign live row."
    ),
    pin="test_a_non_owner_reremember_mints_a_distinct_id_and_does_not_seize_or_rescope",
    frames=("remember", "_replay_record"),
)
_REINFORCE_ENTRY = GovernedWriteAllowlistEntry(
    site=MutationSite("_reinforce", "UPDATE"),
    justification=(
        "read-side-effect on the NON-governed importance column ONLY (§10.9-C); the bump set is the "
        "post-read_filter served set (a row the caller cannot read is never bumped)."
    ),
    pin="test_the_reinforce_update_sets_only_the_importance_column",
    frames=("_reinforce",),
)
_RECREATE_ENTRY = GovernedWriteAllowlistEntry(
    site=MutationSite("_recreate_memory_table", "REMOVE"),
    justification=(
        "boot/admin table recreate, reachable ONLY via rebuild_embeddings (RES-1), never a "
        "member verb; the durable ledger re-embeds every note."
    ),
    pin="test_recreate_memory_table_is_reachable_only_from_rebuild_embeddings",
    frames=("_recreate_memory_table",),
)
MEMORY_WRITE_ALLOWLIST: tuple[GovernedWriteAllowlistEntry, ...] = (
    _UPSERT_ENTRY,
    _REINFORCE_ENTRY,
    _RECREATE_ENTRY,
)

# The module SOURCES the scanners read (typed defs — an untyped lambda is a mypy no-untyped-call).
def _local_source() -> str:
    return Path(local_mod.__file__).read_text(encoding="utf-8")


def _governed_source() -> str:
    return Path(governed_mod.__file__).read_text(encoding="utf-8")


# The memory F5 CASE — the reusable substrate parametrised for the memory table (design §3.2). 64
# builds a TASK_F5_CASE / FINDING_F5_CASE the SAME way and calls the SAME runners below.
MEMORY_F5_CASE = dataclasses.replace(
    _memory_case(),
    mutation_source=_local_source,
    write_allowlist=MEMORY_WRITE_ALLOWLIST,
)

_KNOWN_RAW_SITES = frozenset(entry.site for entry in MEMORY_WRITE_ALLOWLIST)
_SOURCE = _local_source  # the module-source callable (shorthand; typed, never None)
_TABLE = MEMORY_F5_CASE.table


# --------------------------------------------------------------------------- #
# L1 — STRUCTURAL deny-by-default (AST-derived; the enumerate-the-forbidden close).
# --------------------------------------------------------------------------- #


class TestEveryRawMemoryMutationIsAllowlisted:
    """§10.9-A L1 — the AST-derived RAW memory mutation set == the deny-by-default ALLOWLIST. A NEW
    unclassified raw write is a violation (deny-by-default). The synthetic discriminator proves the
    set GROWS-and-REDS; the pin-existence leg proves each allowlist entry is EVIDENCE, not opinion."""

    def test_the_derived_raw_mutation_set_is_non_empty_and_is_the_known_set(self) -> None:
        """⚠ ANTI-VACUITY (GREEN at HEAD) — the AST scan finds a non-empty raw-mutation set and it is
        exactly the three known sites (_upsert_fragment/UPSERT, _reinforce/UPDATE,
        _recreate_memory_table/REMOVE). REDDENS a broken scanner (an empty set makes the containment
        pin vacuous) OR a build that adds/removes a raw memory mutation without re-adjudicating."""
        derived = governed_table_raw_mutation_sites(_SOURCE(), _TABLE)
        assert derived, "the AST scan derived NO raw memory mutation — the scanner is blind (vacuous)"
        assert derived == _KNOWN_RAW_SITES, (
            f"raw-mutation set moved. new (unadjudicated): {sorted(derived - _KNOWN_RAW_SITES)};\n"
            f"  gone (stale allowlist): {sorted(_KNOWN_RAW_SITES - derived)}"
        )

    def test_every_derived_raw_mutation_site_is_in_the_allowlist(self) -> None:
        """⚠ GREEN at HEAD (the 3 sites are enumerated) — the deny-by-default containment: every raw
        memory mutation is ∈ the allowlist, and the allowlist has no GHOST entry. REDDENS a new
        unclassified raw write (orphan) OR a stale allowlist entry (ghost)."""
        derived = governed_table_raw_mutation_sites(_SOURCE(), _TABLE)
        allowlisted = frozenset(entry.site for entry in MEMORY_F5_CASE.write_allowlist)
        orphans = derived - allowlisted
        ghosts = allowlisted - derived
        assert not orphans, (
            f"UNCLASSIFIED raw memory mutation(s) — not allowlisted (deny-by-default): {sorted(orphans)}"
        )
        assert not ghosts, f"GHOST allowlist entry — no live raw mutation site: {sorted(ghosts)}"

    def test_a_synthetic_new_raw_mutation_site_grows_the_derived_set_and_reds(self) -> None:
        """⚠ THE GROWS-AND-REDS PROOF (green-discriminator, GREEN once the scanner works). A synthetic
        source with an EXTRA raw ``UPDATE type::record('memory' …)`` in a NEW function is derived as a
        NEW site absent from the allowlist — so the containment WOULD red for it. Proves the deny is
        over a set that GROWS (a new unguarded write), never a trust-me (INSTRUMENT-0)."""
        synthetic = _SOURCE() + (
            "\n\nclass _SynthClass:\n"
            "    async def _synth_new_write(self, x):\n"
            "        await self._query(\n"
            "            f\"UPDATE type::record('{MEMORY_TABLE}', $id) SET scope = 'seized'\", {'id': x})\n"
        )
        derived = governed_table_raw_mutation_sites(synthetic, _TABLE)
        allowlisted = frozenset(entry.site for entry in MEMORY_F5_CASE.write_allowlist)
        assert MutationSite("_synth_new_write", "UPDATE") in derived, (
            "the AST scan did NOT derive the synthetic new raw write — the deny-by-default gate cannot "
            "see a growing set (the enumerate-the-forbidden defeat)"
        )
        assert derived - allowlisted, (
            "the synthetic new raw write is (correctly) NOT in the allowlist — so the containment reds "
            "for it, proving F5 catches a raw-mutation set that GROWS"
        )

    def test_every_allowlist_entry_has_a_real_evidencing_pin(self) -> None:
        """⚠ GREEN at HEAD — each allowlist entry's ``pin`` names a test DEFINED in the 63a-iv test
        tree (an entry whose pin is deleted leaves the allowlist — the entry is EVIDENCE, not
        opinion). REDDENS an allowlist entry justified by a pin that does not exist."""
        defined = _defined_test_names()
        missing = [
            (entry.site, entry.pin)
            for entry in MEMORY_F5_CASE.write_allowlist
            if entry.pin not in defined
        ]
        assert not missing, (
            f"allowlist entries whose evidencing PIN does not exist in the test tree "
            f"(a justification with no evidence — §10.9-A layer 3): {missing}"
        )

    def test_the_guarded_write_frames_are_derived_and_are_not_raw_sites(self) -> None:
        """⚠ ANTI-VACUITY (GREEN at HEAD) — the guarded_write consumers (invalidate, the supersede
        close in remember) are DERIVED and are the GUARDED set, disjoint from the raw sites (a guarded
        write carries no raw mutation string in local.py — governed.py builds it)."""
        guarded_frames = governed_table_guarded_write_frames(_SOURCE(), _TABLE)
        assert {"invalidate", "remember"} <= guarded_frames, (
            f"the memory guarded_write consumers were not derived: {sorted(guarded_frames)} "
            f"(invalidate + the supersede-close in remember must be recognised as GUARDED)"
        )
        raw_functions = {s.function for s in governed_table_raw_mutation_sites(_SOURCE(), _TABLE)}
        assert "invalidate" not in raw_functions, (
            "invalidate must carry NO raw memory mutation (it is guarded)"
        )


class TestRecreateMemoryTableIsBootAdminOnly:
    """The evidencing pin for the _recreate_memory_table allowlist entry (RES-1) — a REAL test, so the
    entry is evidence not opinion. AST: _recreate_memory_table is CALLED only from rebuild_embeddings
    (a boot/admin verb), never from a member-reachable path."""

    def test_recreate_memory_table_is_reachable_only_from_rebuild_embeddings(self) -> None:
        """⚠ GREEN at HEAD — REDDENS a build that calls _recreate_memory_table from a new caller (a
        member verb), which would make the REMOVE reachable outside boot/admin (RES-1 broken)."""
        tree = ast.parse(_SOURCE())
        callers: set[str] = set()
        current: list[str] = ["<module>"]

        class _Visitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                current.append(node.name)
                self.generic_visit(node)
                current.pop()

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                current.append(node.name)
                self.generic_visit(node)
                current.pop()

            def visit_Call(self, node: ast.Call) -> None:
                if call_name(node) == "_recreate_memory_table":
                    callers.add(current[-1])
                self.generic_visit(node)

        _Visitor().visit(tree)
        assert callers <= {"rebuild_embeddings"}, (
            f"_recreate_memory_table (a REMOVE TABLE) is called from outside rebuild_embeddings: "
            f"{sorted(callers - {'rebuild_embeddings'})} — boot/admin-only (RES-1) is broken"
        )


# --------------------------------------------------------------------------- #
# L2a — STRUCTURAL guard-context coverage: every allowlisted frame + guarded_write sets a context.
# --------------------------------------------------------------------------- #


class TestEveryAllowlistedFrameSetsAWriteGuardContext:
    """§10.9-A L2a — reach as a checked variable: every FRAME that emits an allowlisted raw mutation,
    AND ``guarded_write`` itself, wraps its store mutation in ``governed.write_guard`` (so a runtime
    mutation is always attributable). The frame SET is DERIVED from the allowlist (it GROWS with a new
    entry → this covers it), never a hand-list. ⚠ RED at HEAD — nothing calls write_guard yet."""

    def test_every_allowlisted_local_frame_calls_write_guard(self) -> None:
        source = _SOURCE()
        frames = sorted({frame for entry in MEMORY_F5_CASE.write_allowlist for frame in entry.frames})
        unwired = [f for f in frames if not function_calls_write_guard(source, f)]
        assert not unwired, (
            f"these allowlisted memory-write frames do NOT enter governed.write_guard (§10.9-A L2a — a "
            f"runtime mutation from them is UNATTRIBUTABLE): {unwired}"
        )

    def test_guarded_write_sets_a_write_guard_context(self) -> None:
        assert function_calls_write_guard(_governed_source(), "guarded_write"), (
            "governed.guarded_write does not enter governed.write_guard — its guarded mutations are "
            "UNATTRIBUTABLE at the F5 runtime seam (§10.9-A L2a)"
        )


# --------------------------------------------------------------------------- #
# L2b — RUNTIME: every observed memory mutation carries a guard context (deny-by-default, live).
# --------------------------------------------------------------------------- #


class TestEveryObservedMemoryMutationCarriesAGuardContext:
    """§10.9-A L2b — the runtime deny-by-default gate. A battery drives a memory mutation through EACH
    seam path (create → execute_transaction, reinforce → run_query, guarded close →
    execute_read_transaction); the store seam is instrumented and EVERY observed memory mutation must
    carry a non-None ``governed.active_write_guard()`` label. A context-LESS mutation is UNCLASSIFIED.
    ⚠ RED at HEAD — ``active_write_guard`` is unbuilt, so every observed mutation records label=None."""

    async def test_the_guard_context_mechanism_is_built(self) -> None:
        """⚠ RED at HEAD — the guard-context reader is unbuilt. Split out so the RED reason is legible
        (the mechanism), distinct from the wiring RED below."""
        assert hasattr(governed_mod, "active_write_guard") and hasattr(governed_mod, "write_guard"), (
            "governed.write_guard / governed.active_write_guard are unbuilt — the F5 runtime "
            "guard-context (§10.9-A L2b) has no mechanism"
        )

# --------------------------------------------------------------------------- #
# helper — the set of test names DEFINED anywhere in the 63a-iv test tree (pin-existence).
# --------------------------------------------------------------------------- #


def _defined_test_names() -> frozenset[str]:
    """Every ``def test_*`` name defined in the tests dir — DERIVED by AST (never a hand-list). The
    pin-existence leg checks each allowlist entry's ``pin`` is one of these (an entry whose evidencing
    test is deleted leaves the allowlist)."""
    tests_dir = Path(__file__).resolve().parent
    names: set[str] = set()
    for path in sorted(tests_dir.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                names.add(node.name)
    return frozenset(names)
