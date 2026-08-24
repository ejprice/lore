"""Contract — packet 62 Wave 2: the DERIVED REACH pin + the anti-injection / PDP-invariance /
retired-prose STRUCTURAL pins (store-free).

Author: ``contract-62w2`` (Opus 4.8 CONTRACT author — tests ONLY, no production code).
Sibling of ``test_agent_capability.py`` (mechanism) and ``test_agent_capability_seams.py``
(shared seams).

SPEC: ``docs/design/2026-08-24-packet62-agent-identity-rulings.md`` — FORK 4 (R4.1–R4.3: the
anti-injection invariant as a DERIVED reach pin across the 62↔63 boundary), the WAVE-2 ADDENDUM
W2.1 (only the VERIFIED capability moves owner_agent; a display ``agent=`` never does) / W2.4
(``agent_of`` stays None), the roll-up "§5 single-brain untouched" (the PDP is unchanged; the
61 live oracle still holds), and removed-behavior items I1/I2 (the 48 non-wiring guard docstring).

REACH LAW (CLAUDE.md §"THE ASKABLE FORM" / #344/#345): a guard certifies only the sites it
covers, and its reach must be a CHECKED VARIABLE, not a hidden constant. The governed surface is
DERIVED from ``partition_tools_by_population`` over the LIVE registry (never a hand-list); a NEW
governed tool that neither routes through the owner-stamp seam nor is adjudicated-pending REDS
the coverage pin (RED_ORPHANED). This MIRRORS the prior-art growth pin
``test_tool_population_61b.py::test_every_live_tool_is_reviewed_into_a_population`` — the
derived-set-difference idiom, not a reinvention.

⚠ DESIGN NOTE (flagged to the lead — the "per-tool RED_ADJUDICATED" realisation). Fork 4 asks
for per-tool legs "RED_ADJUDICATED for tools 63/64 has not retrofitted". At 62 HEAD NO governed
tool routes through the owner-stamp seam yet (63/64 wire each), so this is realised as a SINGLE
coverage-as-checked-variable pin: a production adjudication mapping
``_GOVERNED_TOOLS_PENDING_OWNER_STAMP`` (governed-tool → the trigger "packet 63/64 retrofits it")
whose KEYS must EQUAL the derived governed set. It SELF-DESTRUCTS entry-by-entry as 63/64 route
each tool (each deletes its entry AND adds a per-tool routing pin — 63/64's job); a new governed
tool grows the derived set and REDS the equality (orphan), a stale entry reds it (ghost). The
adjudication (owner+trigger, R4.2) is machine-checked (non-empty trigger per entry). If the lead
prefers a literal per-tool xfail leg wired into ``scripts/gates.yaml`` currency instead, this ONE
pin moves — the reach-law INVARIANT (coverage is a checked variable) is identical either way.

RED-until-built symbols are referenced through GUARDS so COLLECTION never collapses.
Store-free: ``build_mcp_server`` + ``mcp.list_tools()`` touch NO SurrealDB (registration only).
"""

from __future__ import annotations

import inspect
from typing import Any

import loremaster.principals as principals_mod
import loremaster.server as server_mod
from fastmcp.server.auth import AccessToken
from loremaster.server import partition_tools_by_population
from loremaster.token_verifier import agent_of

# The prior-art store-free tool builder (test_tool_population_61b uses it the same way).
from test_mutating_set_derivation import _build_tools

from lorerunes import Subject, authorize, authorize_filter

_COMMS_TOOL = "lore_comms"
# The columns a caller must NEVER be able to set as an authz input (§3.2.2 / W2.1): the owner is
# SERVER-derived, and the capability is verified, never a display argument.
_FORBIDDEN_CALLER_AUTHZ_INPUTS = {"owner_principal", "owner_agent", "capability_hash"}


async def _live_tool_names(tmp_path: Any) -> frozenset[str]:
    tools = await _build_tools(tmp_path)
    return frozenset(tool.name for tool in tools)


async def _governed(tmp_path: Any) -> frozenset[str]:
    tools = await _build_tools(tmp_path)
    _shared_read, governed = partition_tools_by_population(tools)
    return governed


# --------------------------------------------------------------------------- #
# LEG 1 — the DERIVED reach pin (R4.1–R4.3). Coverage as a CHECKED variable over
# the governed surface; the adjudication self-destructs as 63/64 route each tool.
# --------------------------------------------------------------------------- #
class TestTheGovernedSurfaceReachPin:
    """R4.1 — every governed tool is EITHER routed through the owner-stamp seam OR adjudicated
    as pending (owner+trigger). At 62: all pending. The set difference reds when the governed set
    GROWS but the covered set does not."""

    async def test_the_governed_set_is_non_empty(self, tmp_path: Any) -> None:
        """⚠ ANTI-VACUITY (INSTRUMENT-0): a reach pin over an EMPTY derived set passes vacuously —
        the switched-off-scanner class. The governed set must be non-empty and re-derived each run
        from the LIVE registry. GREEN at HEAD (the coordination tools exist)."""
        governed = await _governed(tmp_path)
        assert governed, (
            "partition_tools_by_population returned an EMPTY governed set — the reach pin would "
            "pass vacuously; the live registry must carry governed coordination tools"
        )

    async def test_every_governed_tool_is_pending_owner_stamp_and_adjudicated(
        self, tmp_path: Any
    ) -> None:
        """⚠ RED at HEAD — the wave-2 adjudication mapping ``_GOVERNED_TOOLS_PENDING_OWNER_STAMP``
        is unbuilt. COVERAGE-AS-A-CHECKED-VARIABLE: its KEYS must EQUAL the DERIVED governed set
        (no orphan governed tool, no ghost entry), and every value is a non-empty adjudication
        TRIGGER (owner+trigger, R4.2). REDDENS: a NEW governed tool not added to the mapping
        (RED_ORPHANED), a stale entry (ghost), or a blank trigger (an un-adjudicated red)."""
        adjudication = getattr(server_mod, "_GOVERNED_TOOLS_PENDING_OWNER_STAMP", None)
        assert isinstance(adjudication, dict), (
            "loremaster.server._GOVERNED_TOOLS_PENDING_OWNER_STAMP (a dict governed-tool -> trigger) "
            "is unbuilt — the derived reach pin's adjudication record (R4.1/R4.2, Fork 4)"
        )
        governed = await _governed(tmp_path)
        assert governed == frozenset(adjudication), (
            f"the governed set (DERIVED from partition_tools_by_population) must EQUAL the pending "
            f"owner-stamp adjudication keys — orphan (new governed tool unadjudicated): "
            f"{sorted(governed - frozenset(adjudication))!r}; ghost (stale entry): "
            f"{sorted(frozenset(adjudication) - governed)!r}"
        )
        blank = [tool for tool, trigger in adjudication.items() if not (trigger and str(trigger).strip())]
        assert not blank, (
            f"every pending governed tool must carry a non-empty adjudication TRIGGER (owner+trigger, "
            f"R4.2 — 'a trigger nobody measures is a hope'); blank: {blank!r}"
        )

    async def test_a_synthetic_new_governed_tool_would_red_the_coverage(self, tmp_path: Any) -> None:
        """⚠ THE REACH-LAW MUTATION (green-discriminator; green at HEAD once built): PROVE the
        coverage pin actually reds when the governed set GROWS. A synthetic governed tool name (in
        neither the shared-read allowlist nor the adjudication) must be classed ``governed`` by
        ``partition_tools_by_population`` (fail-closed default) AND be absent from the adjudication
        keys — so the equality above WOULD red for it. This is the 'coverage is a checked variable'
        proof (INSTRUMENT-0), not a trust-me."""
        adjudication = getattr(server_mod, "_GOVERNED_TOOLS_PENDING_OWNER_STAMP", None)
        assert isinstance(adjudication, dict), "unbuilt (see the coverage pin)"
        synthetic = "lore_probe_synth_governed_62w2"
        _shared, governed_synth = partition_tools_by_population([_NamedTool(synthetic)])
        assert synthetic in governed_synth, (
            "a new/unreviewed tool must default to GOVERNED (fail-closed) — else the reach pin "
            "cannot see a new governed tool"
        )
        assert synthetic not in adjudication, (
            "the synthetic new governed tool is (correctly) not adjudicated — so the coverage "
            "equality reds for it, proving the pin catches a governed-set that GROWS"
        )


class _NamedTool:
    """Minimal ``.name``-carrying stand-in for an ``mcp.types.Tool`` (partition reads only .name)."""

    def __init__(self, name: str) -> None:
        self.name = name


# --------------------------------------------------------------------------- #
# LEG 2 — the caller cannot supply owner/capability as an authz argument (§3.2.2 /
# W2.1). The owner is SERVER-derived; the capability is VERIFIED — never a display
# input. Store-free (tool-schema inspection).
# --------------------------------------------------------------------------- #
class TestNoCallerControlledOwnerOrCapabilityInput:
    """W2.1 / §3.2.2 — the ``lore_comms`` tool (the surface 62 wires for the owns-mint) exposes no
    ``owner_principal``/``owner_agent``/``capability_hash`` INPUT the caller could use to assert an
    identity. A GUARD (green at HEAD + on a correct build; reds a build that leaks an owner input)."""

    async def test_lore_comms_input_schema_has_no_owner_or_hash_input(self, tmp_path: Any) -> None:
        """The confused-deputy surface §3.2.2 forbids: an authz-bearing owner argument. REDDENS a
        build that adds ``owner_principal``/``owner_agent``/``capability_hash`` as a caller input on
        lore_comms (the owner is derived from the transport credential, never asserted)."""
        tools = await _build_tools(tmp_path)
        comms = [tool for tool in tools if tool.name == _COMMS_TOOL]
        assert comms, f"{_COMMS_TOOL} is not registered — cannot check its input schema"
        # fastmcp's FunctionTool exposes the input JSON schema as ``.parameters``; the mcp.types.Tool
        # form uses ``.inputSchema`` — accept either so the guard is version-robust.
        schema = getattr(comms[0], "parameters", None) or getattr(comms[0], "inputSchema", None) or {}
        properties = set((schema.get("properties") or {}).keys())
        leaked = _FORBIDDEN_CALLER_AUTHZ_INPUTS & properties
        assert not leaked, (
            f"{_COMMS_TOOL} exposes caller authz inputs {sorted(leaked)!r} — owner is SERVER-derived "
            f"from the transport credential (§3.2.2/W2.1); a caller must not assert it"
        )


# --------------------------------------------------------------------------- #
# LEG 3 — agent_of stays None (W2.4/SF-3). The transport token carries NO agent;
# the real resolver is verify_capability (pinned in test_agent_capability.py).
# GUARD (green at HEAD + on a correct build).
# --------------------------------------------------------------------------- #
class TestAgentOfStaysNone:
    """W2.4/SF-3 — ``agent_of`` reads the (absent) token-borne agent; under the capability model
    the agent is NEVER in the transport token, so ``agent_of`` correctly stays None. REDDENS a
    build that (wrongly) stuffs an agent into the token claim."""

    def test_agent_of_returns_none_for_an_agentless_token(self) -> None:
        token = AccessToken(
            token="t", client_id="api_key:alice@example.com", scopes=["lore:read"],
            subject="alice@example.com", claims={"role": "member", "agent": None, "key_name": "k"},
        )
        assert agent_of(token) is None, (
            "agent_of must stay None under the capability model — the agent is resolved per-call by "
            "verify_capability from the presented capability, never from the transport token (W2.4)"
        )

    def test_agent_of_returns_none_for_a_claimless_token(self) -> None:
        token = AccessToken(token="t", client_id="c", scopes=["lore:read"], subject="x", claims={})
        assert agent_of(token) is None


# --------------------------------------------------------------------------- #
# LEG 4 — the PDP single brain is UNTOUCHED (§5). 62 changes WHO constructs a
# Subject, not the PDP. GUARD: authorize/authorize_filter signatures + the Subject
# shape are stable; the load-bearing instrument is the 61 live oracle
# (test_pdp_oracle_61b.py), which stays GREEN (not rewritten here).
# --------------------------------------------------------------------------- #
class TestThePdpSingleBrainIsUnchanged:
    """§5 roll-up — 62 constructs a Subject from a credential; it does NOT touch the PDP. These
    guards red a 62 build that alters the authorize / authorize_filter API or the Subject shape
    (the 61 oracle would then no longer hold with a 62-constructed Subject)."""

    def test_authorize_signature_is_unchanged(self) -> None:
        params = list(inspect.signature(authorize).parameters.values())
        positional = [p.name for p in params if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
        assert positional == ["subject", "action", "resource"], (
            f"authorize's positional params changed: {positional!r} — 62 must not touch the PDP (§5)"
        )
        assert "target_scope" in inspect.signature(authorize).parameters

    def test_authorize_filter_signature_is_unchanged(self) -> None:
        params = list(inspect.signature(authorize_filter).parameters.values())
        positional = [p.name for p in params if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
        assert positional == ["subject", "action", "table"], (
            f"authorize_filter's positional params changed: {positional!r} — 62 must not touch the PDP"
        )
        assert "target_scope" in inspect.signature(authorize_filter).parameters

    def test_subject_shape_is_unchanged(self) -> None:
        """The 62-constructed Subject is the SAME 4-field, no-defaults dataclass the 61 oracle
        builds (test_pdp_oracle_61b.py). REDDENS a 62 build that adds/removes/defaults a field."""
        fields = inspect.signature(Subject).parameters
        assert list(fields) == ["principal_id", "agent_id", "role", "visible_keep_ids"], list(fields)
        assert all(p.default is inspect.Parameter.empty for p in fields.values()), (
            "Subject must keep NO field defaults (PKT-28 C1 — every call CHOOSES)"
        )


# --------------------------------------------------------------------------- #
# LEG 5 — retired-prose / removed-behavior (item 6, I1/I2). The 48 non-wiring guard
# docstring is UPDATED: principal and agent NODES are now RELATED by the owns edge
# (I1), while their vocabularies stay DISTINCT and role/status stay un-wired (I2).
# The bare-pattern sweep for a retired NON-LINK assertion in the test tree came back
# CLEAN (no such test/prose exists — see REPORT-contract-62w2.md); the pinnable part
# is the docstring acknowledgement below.
# --------------------------------------------------------------------------- #
class TestTheNonWiringGuardDocstringIsUpdated:
    """I1/I2 (P8d rendered-prose law — a rename's natural-language surface is where green-at-gate
    defects hide). The ``principals.py`` module docstring must ACKNOWLEDGE the owns edge (I1) while
    PRESERVING the distinct-vocabulary law (I2)."""

    def test_the_module_docstring_acknowledges_the_owns_edge(self) -> None:
        """⚠ RED at HEAD — the STANDING-LAW block frames principal and agent as purely DISTINCT
        with no acknowledgement of the new link, so a reader concludes they are unrelated (FALSE
        after 62). The builder updates it to name the ``owner_principal`` owns edge (I1). REDDENS
        the stale-prose HEAD state."""
        doc = principals_mod.__doc__ or ""
        assert "owner_principal" in doc or "owns" in doc.lower(), (
            "the principals.py module docstring does not acknowledge the packet-62 owns edge "
            "(agent.owner_principal) — the STANDING-LAW block still reads as if principal and agent "
            "are entirely unrelated (I1; P8d stale-prose class)"
        )

    def test_the_distinct_vocabulary_law_is_preserved(self) -> None:
        """⚠ GUARD (green at HEAD + on a correct build). I2 STAYS: the edge links NODES; it does
        NOT merge the role/status closed domains. REDDENS a build that nukes the whole standing-law
        block while adding the owns-edge acknowledgement (the removed-behaviour dual — the new
        world must not silently drop the old world's virtue)."""
        doc = (principals_mod.__doc__ or "").lower()
        assert "conflated" in doc or "never wire" in doc, (
            "the principals.py module docstring dropped the distinct-vocabulary / never-wire-"
            "role-status law (I2 must be PRESERVED — the owns edge links nodes, it does not merge "
            "the principal/agent role+status vocabularies)"
        )
