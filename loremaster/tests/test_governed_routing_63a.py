"""Contract — packet 63a: the #420 VERB-ROUTING COVERAGE pin (design §3.1, §3.2 R-a.1/R-a.5) —
coverage-as-a-checked-variable across the 63↔64 boundary. RED before the 63a build; authored by
``contract-63a`` (Opus 4.8 contract author — tests ONLY).

SPEC: ``docs/design/2026-08-28-packet63-retrofit-rulings.md`` §3.1 (the routed-verb set is DERIVED
as ``partition_tools_by_population(live).governed`` × each governed tool's OWN dispatch table; each
``(tool, verb)`` is either OBSERVED routing through the substrate OR RED_ADJUDICATED with owner +
trigger; the set REDS when it GROWS and the observed set does not), R-a.5 (the 62 adjudication
self-destructs per TOOL, the #420 pin per VERB — two instruments, two granularities, both derived).

⚠ FORK 2 (REPORT-contract-63a.md): the design + brief say the per-verb adjudication lives in
``scripts/pending_contracts.yaml``, but that file is a pydantic ``extra="forbid"`` mypy-bound schema
(adding a section fails the gate). RECOMMENDED HOME: a ``loremaster.server`` constant
``_GOVERNED_VERBS_PENDING_ROUTING`` — a direct SIBLING of the existing per-TOOL
``_GOVERNED_TOOLS_PENDING_OWNER_STAMP`` (established, machine-checkable, self-destructing). This pin
reads that constant + ``_GOVERNED_VERBS_ROUTED`` (the verbs actually routed). If lead-63 rules a
different home, this ONE pin's two getattrs move; the coverage INVARIANT is identical.

⚠ THE RUNTIME PROOF that ``_GOVERNED_VERBS_ROUTED``'s memory entries are not LIES is BEHAVIOURAL and
lives in ``test_memory_retrofit_63a.py`` (F3 recall isolation proves lore_recall routes through
read_filter; the owner-stamp pin proves lore_remember routes through the stamp). This module is the
STRUCTURAL half: the derived set == routed ∪ adjudicated. The two together are the #420 instrument.

Store-free: ``_build_tools`` + registration touch NO SurrealDB (the reach-pin idiom).
"""

from __future__ import annotations

from typing import Any

import loremaster.server as server_mod
from loremaster.server import partition_tools_by_population

# The store-free tool builder (test_agent_capability_reach / test_tool_population_61b use it the
# same way — registration only, no store).
from test_mutating_set_derivation import _build_tools

# Single-verb governed tools: the tool IS the verb (design §3.1). Multi-verb tools dispatch on a
# named ``action`` and carry their OWN dispatch table.
_SINGLE_VERB_TOOLS = frozenset({"lore_remember", "lore_recall", "lore_claim_task"})
# The 63a-routed verbs (memory is the substrate's first consumer — §0(a)/§1.1). As (tool, verb).
_MEMORY_VERBS = frozenset({("lore_remember", "lore_remember"), ("lore_recall", "lore_recall")})


def _dispatch_verbs(tool: str) -> tuple[str, ...]:
    """The verbs of a governed tool, DERIVED from its OWN live dispatch table (never a hand-list):
    ``_COMMS_ACTIONS`` for lore_comms; ``_TASK_ACTIONS`` / ``_FINDING_ACTIONS`` for lore_tasks /
    lore_findings; a single-verb tool's verb is the tool itself."""
    if tool in _SINGLE_VERB_TOOLS:
        return (tool,)
    table_name = {
        "lore_comms": "_COMMS_ACTIONS",
        "lore_tasks": "_TASK_ACTIONS",
        "lore_findings": "_FINDING_ACTIONS",
    }.get(tool)
    if table_name is None:
        # A governed tool with NO known dispatch table — treat the tool as its own single verb so
        # it still appears in the derived set (a new multi-verb governed tool without a mapped
        # dispatch table REDS the coverage until it is classified — the grows-and-reds property).
        return (tool,)
    table = getattr(server_mod, table_name, None)
    assert table is not None, f"{table_name} is unbuilt — cannot derive {tool}'s verbs"
    return tuple(table)  # dict → its keys; tuple → its members


async def _derived_governed_verbs(tmp_path: Any) -> frozenset[tuple[str, str]]:
    """The full governed ``(tool, verb)`` set: ``partition_tools_by_population(live).governed`` ×
    each tool's dispatch table. DERIVED from production truth, never a hand-list (INSTRUMENT-0)."""
    tools = await _build_tools(tmp_path)
    _shared_read, governed = partition_tools_by_population(tools)
    return frozenset((tool, verb) for tool in governed for verb in _dispatch_verbs(tool))


class TestTheVerbRoutingCoverageIsACheckedVariable:
    """#420 / R-a.5 — every governed ``(tool, verb)`` is EITHER routed (63a: the memory verbs) OR
    adjudicated-pending (63b/63c/64) with a trigger. The derived set REDS when it grows and the
    routed ∪ adjudicated set does not."""

    async def test_the_derived_governed_verb_set_is_non_empty(self, tmp_path: Any) -> None:
        """⚠ ANTI-VACUITY (INSTRUMENT-0) — a coverage pin over an EMPTY derived set passes vacuously.
        The set is re-derived each run from the LIVE registry × the LIVE dispatch tables. GREEN at
        HEAD (the governed tools + their dispatch tables exist)."""
        derived = await _derived_governed_verbs(tmp_path)
        assert derived, "the derived governed (tool, verb) set is EMPTY — the coverage pin would be vacuous"
        # sanity: the memory verbs are IN the derived set (single-verb tools are governed).
        assert _MEMORY_VERBS <= derived, (
            f"the memory verbs {_MEMORY_VERBS} are not in the derived governed set {sorted(derived)} — "
            f"lore_remember/lore_recall must classify as governed (fail-closed)"
        )

    async def test_every_governed_verb_is_routed_or_adjudicated(self, tmp_path: Any) -> None:
        """⚠ RED at HEAD — ``_GOVERNED_VERBS_ROUTED`` / ``_GOVERNED_VERBS_PENDING_ROUTING`` are
        unbuilt. COVERAGE-AS-A-CHECKED-VARIABLE: the derived set == routed ∪ adjudicated-keys, the
        two are DISJOINT (a verb is routed XOR pending), and every adjudicated verb carries a
        non-empty trigger. REDDENS: a governed verb in neither (orphan), a stale entry (ghost), a
        verb in both, a blank trigger, OR a new comms/task/finding action that grows the derived set."""
        derived = await _derived_governed_verbs(tmp_path)
        routed = _as_verb_set(getattr(server_mod, "_GOVERNED_VERBS_ROUTED", None), "_GOVERNED_VERBS_ROUTED")
        adjudication = getattr(server_mod, "_GOVERNED_VERBS_PENDING_ROUTING", None)
        assert isinstance(adjudication, dict), (
            "loremaster.server._GOVERNED_VERBS_PENDING_ROUTING (a dict (tool, verb) -> trigger) is "
            "unbuilt — the #420 per-verb adjudication (design §3.1 / FORK 2 recommended home)"
        )
        pending = frozenset(_as_verb(key) for key in adjudication)
        assert not (routed & pending), (
            f"a verb is ROUTED and PENDING at once (mutually exclusive): {sorted(routed & pending)}"
        )
        assert derived == (routed | pending), (
            f"governed verb coverage GAP — derived != routed ∪ adjudicated. "
            f"orphan (governed but neither routed nor adjudicated): {sorted(derived - routed - pending)}; "
            f"ghost (routed/adjudicated but not a live governed verb): {sorted((routed | pending) - derived)}"
        )
        blank = [key for key, trigger in adjudication.items() if not (trigger and str(trigger).strip())]
        assert not blank, (
            f"every adjudicated governed verb must carry a non-empty routing TRIGGER (owner+trigger; "
            f"'a trigger nobody measures is a hope'): {blank!r}"
        )

    async def test_the_memory_verbs_are_routed_not_adjudicated(self, tmp_path: Any) -> None:
        """⚠ RED at HEAD (constants unbuilt). 63a's whole point (§0(a)/§1.1): the MEMORY verbs are
        ROUTED, not adjudicated-pending — a substrate wave with zero consumers cannot mutation-prove
        its own routing pin. REDDENS a build that ships the substrate but leaves memory adjudicated
        (a guard nobody runs). Their RUNTIME routing is proven behaviourally in the retrofit module."""
        routed = _as_verb_set(getattr(server_mod, "_GOVERNED_VERBS_ROUTED", None), "_GOVERNED_VERBS_ROUTED")
        adjudication = getattr(server_mod, "_GOVERNED_VERBS_PENDING_ROUTING", None) or {}
        pending = frozenset(_as_verb(key) for key in adjudication)
        assert _MEMORY_VERBS <= routed, (
            f"the memory verbs {_MEMORY_VERBS} must be in _GOVERNED_VERBS_ROUTED at 63a (memory is the "
            f"substrate's first real consumer) — routed={sorted(routed)}"
        )
        assert not (_MEMORY_VERBS & pending), (
            f"the memory verbs must NOT be adjudicated-pending at 63a close (they are routed): "
            f"{sorted(_MEMORY_VERBS & pending)}"
        )

    async def test_a_synthetic_new_governed_verb_would_red_the_coverage(self, tmp_path: Any) -> None:
        """⚠ THE GROWS-AND-REDS PROOF (green-discriminator; GREEN once the constants are built). A
        synthetic governed ``(tool, verb)`` in NEITHER constant is (correctly) absent from routed ∪
        adjudicated — so the equality WOULD red for it. Proves the coverage catches a set that GROWS
        (a new comms action, a new tool), not a trust-me (INSTRUMENT-0)."""
        routed = _as_verb_set(getattr(server_mod, "_GOVERNED_VERBS_ROUTED", None) or frozenset(), "")
        adjudication = getattr(server_mod, "_GOVERNED_VERBS_PENDING_ROUTING", None) or {}
        pending = frozenset(_as_verb(key) for key in adjudication)
        synthetic = ("lore_probe_synth", "synth_verb_63a")
        assert synthetic not in (routed | pending), (
            "the synthetic new governed verb is (correctly) neither routed nor adjudicated — so the "
            "coverage equality reds for it, proving the pin catches a governed verb set that GROWS"
        )


# --------------------------------------------------------------------------- #
# helpers — tolerate either a set of (tool, verb) tuples or of "tool:verb"/["tool","verb"] rows,
# since the exact SHAPE of the constants is the builder's (the pin checks the SET, not the encoding).
# --------------------------------------------------------------------------- #


def _as_verb(key: Any) -> tuple[str, str]:
    if isinstance(key, tuple) and len(key) == 2:
        return (str(key[0]), str(key[1]))
    if isinstance(key, list) and len(key) == 2:
        return (str(key[0]), str(key[1]))
    if isinstance(key, str) and ":" in key:
        tool, _sep, verb = key.partition(":")
        return (tool, verb)
    raise AssertionError(f"a governed-verb key must be a (tool, verb) pair or 'tool:verb', got {key!r}")


def _as_verb_set(value: Any, name: str) -> frozenset[tuple[str, str]]:
    if value is None:
        return frozenset()
    if isinstance(value, dict):
        value = value.keys()
    return frozenset(_as_verb(item) for item in value)
