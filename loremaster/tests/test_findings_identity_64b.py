"""Contract — packet 64b-i: IDENTITY on ``lore_findings`` — the F5 retirement (amendment 2, OF-2 = RETIRE AT
65), derived provenance, ``agent=``/``session=`` as self-consistency checks, the F7 typed flags for the
WRITE verbs, and the R6 deny-without-a-capability driver. Authored by ``contract-64b`` (Opus 5.5 —
contract tests ONLY).

RULINGS (cited, never re-transcribed): kickoff ``e5fa7f9`` §6 as amended by amendment 2 ``2ea52fe`` §1–§4
(``created_by``/``actor`` LEAVE ``lore_findings``' served schema; the MCP layer's own extra-input refusal
names the field; ONE shared teaching constant ``_RETIRED_IDENTITY_ARGS_TEACHING`` rides the description;
provenance := the Subject's own agent row's ``name`` + ``events[].actor_agent`` := the agent RecordID;
the R8(2) footer fallback + its two served sentences are DELETED; the identity-compare site compares
``agent=``/``session=`` only). Kickoff §8 (F7): ``_FINDING_ACTIONS`` becomes ``dict[str,
GovernedVerbSpec]``; the flag flips WITH the enforcing handler.

HELD BACK (lead ruling on #17026 → sidecar-64 Task 5, D-1b): whether the three READ verbs
(``query``/``get``/``chain_head``) flip ``requires_capability`` in 64b-i or 64b-ii. NOTHING here pins
their flag in either direction; the R6 driver covers exactly the WRITE partition.

MEASURED (2026-09-26, fastmcp as installed — the probe is pasted in REPORT §INSTRUMENTS): the registered
``lore_findings`` ``Tool.run(arguments)`` validates arguments BEFORE dependency resolution — an argument
outside the schema raises ``pydantic.ValidationError`` "Unexpected keyword argument" NAMING the field,
and the handler is never reached; a valid argument set proceeds to dependency resolution (which, outside a
request, fails on ``context`` — a DIFFERENT error, the positive control's discriminator).

Live TEST store ``:18000`` (NEVER :18500) for the behavioural legs; reaped.
"""

from __future__ import annotations

import ast
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from _governed_contract import _credentialed_config, function_calls_named
from _governed_contract_64 import (
    FINDING_READ_VERBS,
    FINDING_WRITE_VERBS,
    RETIRED_FINDING_IDENTITY_ARGS,
    FindingWorld,
    finding_world,
    new_row_id,
)
from _surreal_harness import run
from fastmcp.exceptions import ValidationError as FastMcpValidationError
from pydantic import ValidationError
from surrealdb import RecordID

from loremaster import governed, server

if TYPE_CHECKING:
    from loremaster.server import (
        _RETIRED_IDENTITY_ARGS_TEACHING,
        GovernedVerbSpec,
        _requires_capability,
    )

    # 64b-i's RULED, not-yet-built symbols this file pins — named STATICALLY for the typecheck gate. Until the
    # build lands them each is a mypy error OWNED by `scripts/pending_contracts.yaml` bound
    # `packet-64b-i-contract`, which self-destructs (delete the entry) once they exist (lead #17055, #461).
    # Runtime-inert: never executed, so every pin still REDs at HEAD on its own teaching message.
    _RULED_64B_I: tuple[object, ...] = (
        GovernedVerbSpec,  # F7 (kickoff §13)
        _requires_capability,  # the ONE reader of a spec's flag
        _RETIRED_IDENTITY_ARGS_TEACHING,  # am-2 §2 (the ONE retirement sentence)
        server.AppContext._resolve_identity,  # Q4a (kickoff §13)
    )

#: The EXACT post-retirement served parameter set of ``lore_findings`` (amendment 2 §4 "the schema pin —
#: allowlist the safe"): HEAD's set − {created_by, actor} + {capability, scope}. ``scope`` is the explicit
#: scope of a ``report`` and the target of ``set_scope`` (kickoff §5 table). 64d-i will add
#: ``include_archived`` (amendment 1 §3.3) — THAT wave edits this constant.
FINDINGS_SERVED_PARAMS = frozenset(
    {
        "action",
        "id_or_number",
        "subject",
        "body",
        "area",
        "category",
        "kind",
        "note",
        "status",
        "limit",
        "supersedes",
        "items",
        "agent",
        "session",
        "capability",
        "scope",
    }
)

_SERVER_PY = Path(server.__file__)
#: The stale R8(2) prose (amendment 2 §4 — BARE, anchor-free tokens).
_R8_PROSE = ("never authenticated", "disclosed exception", "exact-match", "EXACTLY equals a registered agent")


async def _findings_tool() -> Any:
    """The REGISTERED ``lore_findings`` FastMCP tool (production ``build_mcp_server`` — registration only,
    nothing connects)."""
    from loremaster.server import LoreServer, build_mcp_server  # noqa: PLC0415

    mcp = build_mcp_server(LoreServer(_credentialed_config("identity_probe_64b", dim=8)))
    tool = await mcp.get_tool("lore_findings")
    assert tool is not None, "lore_findings is not registered"
    return tool


def _served_description_text(tool: Any) -> str:
    """The tool's description + every parameter description (what an agent learns the contract FROM)."""
    parts = [str(tool.description or "")]
    for spec in (tool.parameters.get("properties") or {}).values():
        parts.append(str(spec.get("description", "")))
    return "\n".join(parts)


# =========================================================================== #
# The verb partition + the F7 typed spec dict.
# =========================================================================== #


class TestTheFindingVerbPartitionIsExhaustive:
    """The substrate's WRITE/READ partition is a HAND-LIST whose completeness is CHECKED (INSTRUMENT-0): a
    new finding verb grows ``_FINDING_ACTIONS`` and reds here until a human classifies it."""

    def test_write_and_read_partition_the_dispatch_table_exactly(self) -> None:
        """⚠ RED at HEAD (``set_scope`` is not a finding verb yet — kickoff §5 table)."""
        actions = set(server._FINDING_ACTIONS)  # noqa: SLF001
        assert set(FINDING_WRITE_VERBS) | set(FINDING_READ_VERBS) == actions, (
            "unclassified finding verbs: "
            f"{sorted(actions - set(FINDING_WRITE_VERBS) - set(FINDING_READ_VERBS))}; "
            f"stale: {sorted((set(FINDING_WRITE_VERBS) | set(FINDING_READ_VERBS)) - actions)}"
        )
        assert not set(FINDING_WRITE_VERBS) & set(FINDING_READ_VERBS)


class TestTheFindingDispatchTableIsATypedSpecDict:
    """F7 (kickoff §8): ONE mechanism — a flags-only base ``GovernedVerbSpec(requires_capability, limit_cap)``
    that ``CommsActionSpec`` EXTENDS; ``_FINDING_ACTIONS`` maps verb → ``GovernedVerbSpec``; ONE helper
    ``_requires_capability(table, action)`` reads the flag for every dispatcher (typed applicability,
    never a name compared — PKT-28)."""

    def test_the_finding_table_is_a_dict_of_governed_verb_specs(self) -> None:
        """⚠ RED at HEAD (a plain tuple; no ``GovernedVerbSpec``)."""
        spec_type = vars(server).get("GovernedVerbSpec")
        assert spec_type is not None, "UNBUILT (kickoff §8): server.GovernedVerbSpec does not exist"
        assert issubclass(server.CommsActionSpec, spec_type), (
            "CommsActionSpec must EXTEND GovernedVerbSpec (ONE mechanism)"
        )
        table: Any = vars(server)["_FINDING_ACTIONS"]  # a tuple at HEAD, a spec dict when built
        assert isinstance(table, dict) and all(isinstance(spec, spec_type) for spec in table.values()), (
            f"_FINDING_ACTIONS must be dict[str, GovernedVerbSpec], got {type(table).__name__}"
        )

    def test_the_capability_set_is_EXACTLY_the_eight_write_verbs_in_64b_i(self) -> None:
        """⚠ RED at HEAD. Amendment 3 D-1b (Reading A): the ``requires_capability=True`` set, DERIVED from
        the spec dict, is EXACTLY the 8 write verbs in 64b-i — ``query``/``get``/``chain_head`` stay
        ``False`` until 64b-ii flips them WITH their read filter (then this literal grows to 11 — the ii-a
        ``..._is_EXACTLY_...`` precedent: the wave that flips a verb updates the literal). A True read verb
        now would deny without a capability and serve an UNFILTERED set with one (the typed lie)."""
        table: Any = vars(server)["_FINDING_ACTIONS"]  # a tuple at HEAD, a spec dict when built
        assert isinstance(table, dict), "UNBUILT (kickoff §8): _FINDING_ACTIONS is not a spec dict"
        required = {
            verb for verb, spec in table.items() if getattr(spec, "requires_capability", None) is True
        }
        assert required == set(FINDING_WRITE_VERBS), (
            f"requires_capability=True set {sorted(required)} != the 64b-i write set "
            f"{sorted(FINDING_WRITE_VERBS)} "
            "(amendment 3 D-1b)"
        )
        for verb in FINDING_READ_VERBS:
            assert getattr(table[verb], "requires_capability", None) is False, (
                f"read verb {verb!r} flipped before its filter (amendment 3 D-1b — 64b-ii)"
            )

    def test_the_one_flag_reader_agrees_with_the_spec_and_the_dispatcher_calls_it(self) -> None:
        """⚠ RED at HEAD. ``_requires_capability(table, action)`` returns the spec's own field for every
        finding verb, and ``AppContext.findings`` CALLS it (a second reader — a hand-kept verb set — would
        be the #102 seam the kickoff §8 rejects)."""
        reader = vars(server).get("_requires_capability")
        assert callable(reader), "UNBUILT (kickoff §8): server._requires_capability does not exist"
        table: Any = vars(server)["_FINDING_ACTIONS"]  # a tuple at HEAD, a spec dict when built
        for verb, spec in table.items():
            assert reader(table, verb) is getattr(spec, "requires_capability"), verb
        assert function_calls_named(
            _SERVER_PY.read_text(encoding="utf-8"), "findings", "_requires_capability"
        ), "AppContext.findings does not read the flag through server._requires_capability"


# =========================================================================== #
# Amendment 2 — the retired args leave the served schema; the refusal names the field.
# =========================================================================== #


class TestTheRetiredIdentityArgsLeaveTheServedSchema:
    """Amendment 2 §0/§4: ``created_by``/``actor`` are REMOVED from ``lore_findings``' served schema (never
    advertised-but-refused — a schema teaches by existence); a caller still passing one meets the MCP
    layer's own refusal NAMING the field, and the handler is never reached."""

    async def test_the_served_parameter_set_is_exactly_the_post_retirement_set(self) -> None:
        """⚠ RED at HEAD (``created_by``/``actor`` served; ``capability``/``scope`` absent). Allowlist the
        safe: a retired name reappearing, or any other drift, reds by name."""
        tool = await _findings_tool()
        served = frozenset(tool.parameters.get("properties") or {})
        assert served == FINDINGS_SERVED_PARAMS, (
            f"extra: {sorted(served - FINDINGS_SERVED_PARAMS)}; "
            f"missing: {sorted(FINDINGS_SERVED_PARAMS - served)}"
        )
        assert tool.parameters.get("additionalProperties") is False, (
            "the schema must refuse foreign arguments"
        )

    @pytest.mark.parametrize("retired", RETIRED_FINDING_IDENTITY_ARGS)
    async def test_a_retired_argument_is_refused_by_the_mcp_layer_naming_the_field(
        self, retired: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at HEAD (the name is a valid parameter — "DID NOT RAISE"). The refusal is the MCP layer's own
        argument validation (FastMCP re-raises pydantic's as its own ``ValidationError`` class — both
        accepted), NAMES the field, and fires BEFORE the handler (a spy on ``_app_context`` sees zero calls).
        POSITIVE CONTROL: the SAME argument set without the retired name passes validation (it proceeds to
        dependency resolution, which fails outside a request with a NON-validation error — the
        discriminator). The base deliberately carries no ``capability`` so HEAD fails on the retired name
        itself, never on the not-yet-added ``capability``."""
        reached: list[Any] = []
        monkeypatch.setattr(server, "_app_context", reached.append)
        tool = await _findings_tool()
        base = {"action": "resolve", "id_or_number": 7, "note": "closing"}
        with pytest.raises((ValidationError, FastMcpValidationError)) as refusal:
            await tool.run({**base, retired: "someone-else"})
        assert retired in str(refusal.value), f"the refusal must NAME `{retired}`: {refusal.value}"
        assert reached == [], (
            "the handler was reached — the retired argument was not refused at the MCP layer"
        )
        try:
            await tool.run(base)
        except (ValidationError, FastMcpValidationError) as error:  # pragma: no cover - the control's failure
            pytest.fail(f"CONTROL: the argument set WITHOUT `{retired}` failed validation: {error}")
        except Exception:  # noqa: BLE001, S110 - dependency resolution outside a request: validation PASSED
            pass

    async def test_the_shared_teaching_constant_rides_the_description_and_is_spelled_once(self) -> None:
        """⚠ RED at HEAD. ONE constant ``_RETIRED_IDENTITY_ARGS_TEACHING`` (amendment 2 §2), the LAST
        sentence of the served description (asserted by IDENTITY — the constant's own text, never a second
        literal), and its opening words appear ONCE in ``server.py`` (a second spelling reds)."""
        teaching = vars(server).get("_RETIRED_IDENTITY_ARGS_TEACHING")
        assert isinstance(teaching, str) and teaching, (
            "UNBUILT (amendment 2 §2): no _RETIRED_IDENTITY_ARGS_TEACHING"
        )
        tool = await _findings_tool()
        assert str(tool.description).rstrip().endswith(teaching.rstrip()), (
            "the lore_findings description must END with the shared retirement sentence"
        )
        opening = teaching.split(":", 1)[0]
        assert _SERVER_PY.read_text(encoding="utf-8").count(opening) == 1, (
            f"the retirement teaching's opening {opening!r} is spelled more than once in server.py "
            "— ONE constant"
        )

    async def test_the_served_prose_teaches_no_retired_arg_and_no_R8_fallback(self) -> None:
        """⚠ RED at HEAD. The P8d sweep, on what an agent READS: with the ONE teaching sentence removed, the
        description + every parameter description of ``lore_findings`` names neither retired arg and
        carries none of the R8(2) exact-match prose (BARE, anchor-free tokens — amendment 2 §4)."""
        tool = await _findings_tool()
        text = _served_description_text(tool)
        teaching = vars(server).get("_RETIRED_IDENTITY_ARGS_TEACHING")
        if isinstance(teaching, str) and teaching:
            text = text.replace(teaching, "")
        hits = [token for token in (*RETIRED_FINDING_IDENTITY_ARGS, *_R8_PROSE) if token in text]
        assert not hits, f"lore_findings' served prose still teaches {hits}"


class TestTheFooterFallbackIsDeletedForFindings:
    """Amendment 2 §1 item 6: the R8(2) ``attributions=`` fallback is DELETED for ``lore_findings`` — no
    caller value exists to match; the footer's agent is the Subject's own row."""

    def test_the_findings_dispatcher_passes_no_attributions_to_the_footer(self) -> None:
        """⚠ RED at HEAD (``attributions=(actor, created_by)``)."""
        tree = ast.parse(_SERVER_PY.read_text(encoding="utf-8"))
        findings = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == "findings"
            and any(isinstance(arg, ast.arg) and arg.arg == "self" for arg in node.args.args)
        )
        footer_calls = [
            node
            for node in ast.walk(findings)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "_with_comms_footer"
        ]
        assert footer_calls, "the findings dispatcher no longer appends the pending-traffic footer"
        for call in footer_calls:
            assert all(keyword.arg != "attributions" for keyword in call.keywords), (
                "the findings footer still carries the R8(2) attributions= fallback (amendment 2 §1 item 6)"
            )


# =========================================================================== #
# Behavioural — derived provenance, the self-consistency checks, R6.
# =========================================================================== #


def _events(row: dict[str, Any]) -> list[dict[str, Any]]:
    provenance = row.get("provenance") or {}
    return list(provenance.get("events") or [])


class TestProvenanceIsDerivedFromTheCapability:
    """Amendment 2 §3: ``finding.created_by`` / ``provenance.created_by`` / ``events[].actor`` :=
    ``own_row.name``; ``events[].actor_agent`` := the agent RecordID. Two agents of TWO principals (no
    monoculture — a build that stamps a constant or the first-registered agent reds)."""

    async def test_report_stamps_the_capabilitys_agent_name(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD (no ``capability=``). ag-a1 and ag-b2 each report; each row names ITS reporter."""
        async with finding_world(monkeypatch, tmp_path) as world:
            for agent in ("ag-a1", "ag-b2"):
                await world.findings(
                    agent,
                    action="report",
                    subject=f"filed by {agent}",
                    body="b",
                    area="lore_search",
                    category="capability_gap",
                )
            rows = await run(
                world.admin_conn,
                "SELECT number, subject, created_by, provenance FROM finding ORDER BY number",
            )
            by_subject = {row["subject"]: row for row in rows}
            for agent in ("ag-a1", "ag-b2"):
                row = by_subject[f"filed by {agent}"]
                assert row["created_by"] == agent and row["provenance"]["created_by"] == agent, row

    async def test_a_status_edge_records_the_actor_name_and_the_actor_agent_link(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD. Bob's ag-b1 resolves alice's ``keep:AB`` finding: the appended event's ``actor`` is
        ``ag-b1`` and its ``actor_agent`` is ag-b1's RecordID (the id is unambiguous across sessions; the
        name is not)."""
        async with finding_world(monkeypatch, tmp_path) as world:
            row_id = new_row_id("prov")
            await world.seed(row_id=row_id, number=1001, owner="ag-a1", scope_key="AB")
            await world.findings("ag-b1", action="resolve", id_or_number=1001, note="fixed")
            event = _events(await world.row(row_id))[-1]
            assert event.get("actor") == "ag-b1", event
            assert str(event.get("actor_agent")) == str(RecordID("agent", world.agent_ids["ag-b1"])), event


class TestAgentAndSessionAreSelfConsistencyChecks:
    """Kickoff §6 item 1 / amendment 2 §1 item 1 (63c Q4a's shape, extended by call set): identity comes
    from ``capability=``; a supplied ``agent=``/``session=`` must equal the capability's OWN agent row,
    else ONE teaching ``GovernedDenied`` and ZERO rows written; omitted ⇒ derived. The compare lives in
    ONE place (``AppContext._resolve_identity`` — LIFTED/CALLED per the kickoff §13 step 3)."""

    async def test_a_foreign_agent_name_is_denied_and_writes_nothing(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD. alice's ag-a1 capability with ``agent='ag-b1'`` (bob's) ⇒ deny, 0 findings."""
        async with finding_world(monkeypatch, tmp_path) as world:
            with pytest.raises(governed.GovernedDenied):
                await world.findings(
                    "ag-a1", action="report", subject="forged", body="", area="a", category="c", agent="ag-b1"
                )
            assert await run(world.admin_conn, "SELECT VALUE id FROM finding") == []

    async def test_a_foreign_session_is_denied(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """⚠ RED at HEAD. ag-a1's capability with ag-a1's name but bob's SESSION ⇒ deny."""
        async with finding_world(monkeypatch, tmp_path) as world:
            with pytest.raises(governed.GovernedDenied):
                await world.findings(
                    "ag-a1",
                    action="report",
                    subject="forged",
                    body="",
                    area="a",
                    category="c",
                    agent="ag-a1",
                    session="s64-bob-one",
                )

    async def test_the_matching_agent_and_session_and_the_omitted_pair_are_accepted(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD. POSITIVE CONTROL: the capability's own name + session, and nothing at all, both
        write (so the denials above are the MISMATCH, not the parameter's presence)."""
        async with finding_world(monkeypatch, tmp_path) as world:
            await world.findings(
                "ag-a2",
                action="report",
                subject="own",
                body="",
                area="a",
                category="c",
                agent="ag-a2",
                session="s64-alice-two",
            )
            await world.findings("ag-a2", action="report", subject="omitted", body="", area="a", category="c")
            assert len(await run(world.admin_conn, "SELECT VALUE id FROM finding")) == 2

    def test_the_dispatcher_routes_identity_through_the_one_helper(self) -> None:
        """⚠ RED at HEAD. ``AppContext.findings`` calls ``_resolve_identity`` (the ONE compare site); it
        does not hand-roll a name compare (kickoff §6 rider iv, as amended: ``agent=``/``session=`` only)."""
        source = _SERVER_PY.read_text(encoding="utf-8")
        assert function_calls_named(source, "findings", "_resolve_identity"), (
            "AppContext.findings does not route identity through AppContext._resolve_identity"
        )


def _r6_drivers(world: FindingWorld) -> dict[str, Callable[[], Awaitable[Any]]]:
    """verb → a well-formed call with NO capability (the ambient token is VALID — the deny is the missing
    capability). Keyed by verb so the coverage assertion diffs it against the DERIVED True-set."""
    ctx = world.ctx

    def _call(**kwargs: Any) -> Callable[[], Awaitable[Any]]:
        return lambda: ctx.findings(**kwargs)

    return {
        "report": _call(action="report", subject="s", body="", area="a", category="c"),
        "acknowledge": _call(action="acknowledge", id_or_number=1001),
        "resolve": _call(action="resolve", id_or_number=1001),
        "wontfix": _call(action="wontfix", id_or_number=1001),
        "annotate": _call(action="annotate", id_or_number=1001, note="n"),
        "resolve_many": _call(action="resolve_many", items=[{"id_or_number": 1001}]),
        "acknowledge_many": _call(action="acknowledge_many", items=[{"id_or_number": 1001}]),
        "set_scope": _call(action="set_scope", id_or_number=1001, scope="principal-private"),
    }


class TestEveryCapabilityRequiredWriteVerbDeniesWithoutOne:
    """R6 (kickoff §8 rider i; amendment 3 D-1b — the table asserts EXACTLY the 8 True verbs in 64b-i, 11 in
    64b-ii): ∀ verb whose spec says ``requires_capability=True`` (DERIVED), a well-formed call with NO
    capability under a VALID token ⇒
    ``GovernedDenied``, and the finding row is untouched. COVERAGE CHECKED: a True write verb without a
    driver row reds (a flipped-but-undriven verb is a blind spot). The shared R6 table in
    ``test_comms_capability_63b_ii_a.py`` gains these rows in the HELD patch."""

    async def test_every_true_write_verb_denies_without_a_capability(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD (the table is a tuple — the True-set is empty → the non-vacuity leg reds)."""
        table: Any = vars(server)["_FINDING_ACTIONS"]  # a tuple at HEAD, a spec dict when built
        required = {
            verb
            for verb, spec in (table.items() if isinstance(table, dict) else ())
            if getattr(spec, "requires_capability", False)
        }
        assert required, (
            "no finding WRITE verb requires a capability — R6's ∀ would be vacuous (kickoff §8 unbuilt)"
        )
        async with finding_world(monkeypatch, tmp_path) as world:
            drivers = _r6_drivers(world)
            uncovered = required - drivers.keys()
            assert not uncovered, (
                f"requires_capability write verbs with NO R6 driver row: {sorted(uncovered)}"
            )
            row_id = new_row_id("r6")
            await world.seed(row_id=row_id, number=1001, owner="ag-a1", scope_key="AB")
            before = await world.row(row_id)
            world.holder["email"] = world.emails["alice"]
            for verb in sorted(required):
                with pytest.raises(governed.GovernedDenied):
                    await drivers[verb]()
            assert await world.row(row_id) == before, "an identity-less write verb mutated the finding"
            assert len(await run(world.admin_conn, "SELECT VALUE id FROM finding")) == 1


# =========================================================================== #
# Amendment 3 D-1b — the 64b-i INTERIM for the three read verbs.
# =========================================================================== #


class TestTheReadVerbsRefuseACapabilityUntilTheirFilterLands:
    """Amendment 3 D-1b: the ``capability=`` PARAMETER lands on the tool in 64b-i, but for
    ``query``/``get``/``chain_head`` it is a FOREIGN param — a supplied value is REFUSED with the
    strict-param teaching (the ``_comms_foreign_param_error`` idiom by CALL, never a second spelling),
    NEVER accepted-and-ignored (the silent lie) and NEVER resolved-and-unused (a spy on
    ``AppContext._resolve_subject`` sees 0 calls). 64b-ii INVERTS these pins (DELETE-WITH-REPLACEMENT by
    the R6 deny-without-capability rows)."""

    @pytest.mark.parametrize("verb", FINDING_READ_VERBS)
    async def test_a_capability_on_a_read_verb_is_a_foreign_param_teaching_refusal(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, verb: str
    ) -> None:
        """⚠ RED at HEAD (``capability=`` is not a parameter — the guard asserts the signature first)."""
        async with finding_world(monkeypatch, tmp_path) as world:
            await world.seed(row_id=new_row_id("rd"), number=1101, owner="ag-a1", scope_key="AB")
            resolved: list[Any] = []
            real = server.AppContext._resolve_subject  # noqa: SLF001

            async def _spy(self: Any, capability: Any) -> Any:
                resolved.append(capability)
                return await real(self, capability)

            monkeypatch.setattr(server.AppContext, "_resolve_subject", _spy)
            kwargs: dict[str, Any] = {"action": verb}
            if verb != "query":
                kwargs["id_or_number"] = 1101
            with pytest.raises(ValueError, match="capability") as refusal:
                await world.findings("ag-a1", **kwargs)
            text = str(refusal.value)
            assert "applies only to" in text and verb in text, (
                "the refusal must TEACH (the strict-param shape: which actions own `capability`, omit it "
                "for "
                f"{verb!r}): {text!r}"
            )
            assert any(write in text for write in FINDING_WRITE_VERBS), text
            assert resolved == [], "a read verb RESOLVED the capability it then refused (resolved-and-unused)"

    @pytest.mark.parametrize("verb", FINDING_READ_VERBS)
    async def test_CONTROL_a_read_verb_without_a_capability_still_serves(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, verb: str
    ) -> None:
        """GREEN at HEAD AND after the 64b-i build (a DISCRIMINATOR): the reads are UNCHANGED in 64b-i — no
        capability, no deny. A build that flips a read verb early (Reading B) reds here."""
        async with finding_world(monkeypatch, tmp_path) as world:
            await world.seed(row_id=new_row_id("rd"), number=1102, owner="ag-a1", scope_key="AB")
            world.holder["email"] = world.emails["alice"]
            kwargs: dict[str, Any] = {"action": verb}
            if verb != "query":
                kwargs["id_or_number"] = 1102
            rendered = str(await world.ctx.findings(**kwargs))
            assert "1102" in rendered, rendered

    def test_the_finding_dispatcher_builds_the_refusal_through_the_shared_idiom(self) -> None:
        """⚠ RED at HEAD. BY CALL — the finding dispatcher calls ``_comms_foreign_param_error`` (never a
        second spelling of the strict-param teaching)."""
        assert function_calls_named(
            _SERVER_PY.read_text(encoding="utf-8"), "findings", "_comms_foreign_param_error"
        ), "AppContext.findings does not build its foreign-param refusal through _comms_foreign_param_error"


def _routing_markers() -> set[tuple[str, str]]:
    """Every ``@observes_routing(tool, verb)`` marker in the test tree — THE derivation the routing suite
    owns (``test_governed_routing_63a._behaviourally_observed_verbs``), called, never cloned (the #420
    structural half has ONE scanner)."""
    from test_governed_routing_63a import _behaviourally_observed_verbs  # noqa: PLC0415

    return set(_behaviourally_observed_verbs())


class TestTheFindingRoutingLegsAreHonestBothWays:
    """#420 per verb, BOTH directions for ``lore_findings`` (kickoff §8 rider ii; amendment 3 D-1b): the 8
    write legs are ROUTED and each carries an ``@observes_routing`` marker on a behavioural pin; the 3 read
    legs stay PENDING with a live (non-blank) trigger, UNMARKED, and ``requires_capability=False`` — a
    marker or a True on a pending leg is a leg claiming a routing that has not landed. (The GENERAL reverse
    pin over every tool lives in ``test_governed_routing_63a.py`` — the HELD patch.)"""

    def test_every_write_leg_is_routed_and_observed(self) -> None:
        """⚠ RED at HEAD (the write legs are pending; ``set_scope`` is not a verb)."""
        routed = set(vars(server)["_GOVERNED_VERBS_ROUTED"])
        pending = dict(vars(server)["_GOVERNED_VERBS_PENDING_ROUTING"])
        markers = _routing_markers()
        problems = []
        for verb in FINDING_WRITE_VERBS:
            leg = ("lore_findings", verb)
            if leg not in routed:
                problems.append(f"{verb}: not in _GOVERNED_VERBS_ROUTED")
            if leg in pending:
                problems.append(f"{verb}: still pending")
            if leg not in markers:
                problems.append(f"{verb}: no @observes_routing marker in the test tree")
        assert not problems, problems

    def test_every_read_leg_stays_pending_unmarked_and_false(self) -> None:
        """GREEN at HEAD AND after the 64b-i build; RED the day a read leg is marked/flipped/routed ahead of
        its filter (64b-ii inverts it)."""
        routed = set(vars(server)["_GOVERNED_VERBS_ROUTED"])
        pending = dict(vars(server)["_GOVERNED_VERBS_PENDING_ROUTING"])
        markers = _routing_markers()
        table: Any = vars(server)["_FINDING_ACTIONS"]
        for verb in FINDING_READ_VERBS:
            leg = ("lore_findings", verb)
            assert leg in pending and str(pending[leg]).strip(), f"{verb}: not pending with a live trigger"
            assert leg not in routed, f"{verb}: routed before its filter"
            assert leg not in markers, (
                f"{verb}: an @observes_routing marker claims a routing that has not landed"
            )
            if isinstance(table, dict):
                assert getattr(table[verb], "requires_capability", None) is False, verb
