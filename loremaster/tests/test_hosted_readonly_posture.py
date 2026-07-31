"""CONTRACT — the hosted read-only posture, DERIVED from the registered annotations (R8, #291).

Design ``docs/design/2026-07-31-packet39-google-oauth.md`` §7 + §9 group 6.

**The rule:** a tool is hosted-callable **iff** its registered
``ToolAnnotations.readOnlyHint is True``. Everything else — including
``annotations is None`` — is refused for a principal without ``lore:write``.
Deny-by-default, so an unclassified NEW tool is **born refused**.

------------------------------------------------------------------------------
FINDING #291 — WHY THE DERIVATION REPLACES A LIST, AND WHAT REPLACES THE LIST

``test_mcp_server.py`` carries ``_MUTATING_TOOLS = {"lore_remember", "lore_index",
"lore_findings", "lore_comms"}`` — a hand-list beside production's typed
``ToolAnnotations``, and **it has already drifted**: ``lore_claim_task`` and
``lore_tasks`` are annotated ``readOnlyHint=False`` in production via
``_TASK_TOOL_ANNOTATIONS`` and are absent from that set. The pin using it iterates the
list, so an omission is INVISIBLE — a subset check can never see what is missing.
That is the repo's own ONE-IMPLEMENTATION failure living inside a gate.

The fix is two-sided, and both sides are needed:

1. **Coverage is DERIVED.** :func:`mutating_tool_names` computes the set from
   ``await mcp.list_tools()``. There is no second source of truth to drift.
2. **The spec anchor is BEHAVIOUR, named once.** A purely derived expectation is a
   tautology — flip an annotation and the "expectation" flips with it. So every
   mutating tool also gets a NAMED behavioural fixture, and
   :data:`EXPECTED_MUTATING_TOOLS` is asserted EQUAL to the derived set (not a subset
   — equality is precisely what #291's pin lacked). Ask the design's own question:
   *"if someone flipped ``lore_remember``'s annotation to read-only, which pin reds?"*
   Answer: its behaviour fixture, by name, plus the equality pin.

⚠ ``test_mcp_server.py``'s ``_MUTATING_TOOLS`` is OUTSIDE this contract's writable set.
Deleting it (design §7: *"the hand-list is DELETED, not corrected"*) is a builder task;
the exact edit is named in ``REPORT-contract-39-auth-1.md``.

------------------------------------------------------------------------------
THE ∀-PROPERTY (design §9, "Posture ∀")

    Every registered tool is classified (``readOnlyHint`` explicitly set), and in
    ``HOSTED_OAUTH`` every non-read-only tool is refused for every non-write
    principal — no tool unclassified, no principal-shape untested.

Three principal shapes are fixtured (google token, api key, no token) and at least two
distinct values within each shape, because a build that branches on one email or one
key name would otherwise pass the entire group.
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

# ⚠ ``lorerunes`` SYMBOLS ARE IMPORTED INSIDE EACH FUNCTION, NOT AT MODULE LEVEL.
# This contract is written before the implementation exists, so a module-level import
# would collapse every pin in this file into ONE collection error — and a collection
# error yields NO node ids, which is exactly what ``scripts/mutation_proof.py`` needs
# in order to declare its expected-RED set from ``--collect-only``. Function-local
# imports keep the module collectible and let each pin fail on its own terms.
from _auth_fixtures import (
    API_KEY_ENV_LAN_CLIENT,
    API_KEY_ENV_LOCAL_AGENT,
    API_KEY_NAME_LAN_CLIENT,
    API_KEY_NAME_LOCAL_AGENT,
    API_KEY_VALUE_LAN_CLIENT,
    API_KEY_VALUE_LOCAL_AGENT,
    GOOGLE_ACCESS_TOKEN_LIFETIME_S,
    GOOGLE_CLIENT_ID,
    GOOGLE_ISSUER,
    OPERATOR_EMAIL,
    OPERATOR_SUBJECT,
    SECOND_PRINCIPAL_EMAIL,
    SECOND_PRINCIPAL_SUBJECT,
    base_config_payload,
    google_access_token,
    hosted_auth_block,
    lan_bearer_auth_block,
    slug,
    write_roster,
)
from mcp.server.auth.middleware.auth_context import auth_context_var
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken
from mcp.types import ToolAnnotations

# The BEHAVIOURAL anchor (design §7). Each name here gets its own refusal fixture, so a
# wrongly-flipped annotation reds a pin BY NAME rather than being blessed by a derived
# expectation. Derived from reading production's six ``ToolAnnotations`` constants and
# their registration sites at packet-39 time: ``_SAVE_MEMORY_ANNOTATIONS``,
# ``_INDEX_ANNOTATIONS``, ``_TASK_TOOL_ANNOTATIONS`` (×2 tools),
# ``_FINDINGS_TOOL_ANNOTATIONS`` and ``_COMMS_TOOL_ANNOTATIONS`` all set
# ``readOnlyHint=False``.
EXPECTED_MUTATING_TOOLS = frozenset(
    {
        "lore_remember",
        "lore_index",
        "lore_findings",
        "lore_comms",
        # ⚠ THE TWO #291 OMITTED. Their presence here is the fix.
        "lore_claim_task",
        "lore_tasks",
    }
)

# The read surface that must REMAIN available to a hosted principal — the whole point
# of admitting them at all. Also the control set: a build that refused everything would
# pass every refusal pin below.
EXPECTED_READ_ONLY_TOOLS = frozenset(
    {
        "lore_search",
        "lore_get_symbol",
        "lore_verify",
        "lore_recall",
        "lore_dead_code",
        "lore_impact",
        "lore_map",
        "lore_read",
        "lore_diff",
    }
)

# A tool name that does not exist, used to prove the guard refuses by ANNOTATION rather
# than by membership of any list of known names.
UNANNOTATED_PROBE_TOOL = "lore_probe_unannotated"

# The whole registered surface. The section pins scan for tool names inside a rendered
# clause, so they need the universe to scan FOR — derived from the two named sets rather
# than re-listed, so a tool cannot be added to one and forgotten here.
ALL_TOOL_NAMES = EXPECTED_READ_ONLY_TOOLS | EXPECTED_MUTATING_TOOLS


def google_principal(*, email: str, subject: str) -> AccessToken:
    """A hosted Google principal exactly as ``LoreTokenVerifier`` mints one (R10)."""
    from lorerunes import SCOPE_READ
    return AccessToken(
        token=google_access_token("posture"),
        client_id=GOOGLE_CLIENT_ID,
        scopes=[SCOPE_READ],
        expires_at=int(time.time()) + GOOGLE_ACCESS_TOKEN_LIFETIME_S,
        subject=subject,
        claims={"iss": GOOGLE_ISSUER, "email": email},
    )


def api_key_principal(*, name: str) -> AccessToken:
    """A local/LAN api-key principal, which retains the FULL surface (design §1)."""
    from lorerunes import SCOPE_READ, SCOPE_WRITE
    return AccessToken(
        token=API_KEY_VALUE_LOCAL_AGENT if name == API_KEY_NAME_LOCAL_AGENT else API_KEY_VALUE_LAN_CLIENT,
        client_id=f"api_key:{name}",
        scopes=[SCOPE_READ, SCOPE_WRITE],
        subject=name,
    )


# The principal LABELS are module-level literals (so ``--collect-only`` yields stable
# node ids); the AccessToken values are built lazily, because minting one needs the
# ``lorerunes`` scope constants this contract is written before.
GOOGLE_PRINCIPAL_LABELS = ("operator", "colleague")
API_KEY_PRINCIPAL_LABELS = ("local-agent", "lan-client")


def google_principals(label: str) -> AccessToken:
    """The Google principal registered under ``label`` (two distinct identities)."""
    if label == "operator":
        return google_principal(email=OPERATOR_EMAIL, subject=OPERATOR_SUBJECT)
    return google_principal(email=SECOND_PRINCIPAL_EMAIL, subject=SECOND_PRINCIPAL_SUBJECT)


def api_key_principals(label: str) -> AccessToken:
    """The api-key principal registered under ``label`` (two distinct key names)."""
    if label == "local-agent":
        return api_key_principal(name=API_KEY_NAME_LOCAL_AGENT)
    return api_key_principal(name=API_KEY_NAME_LAN_CLIENT)


@contextlib.contextmanager
def as_principal(token: AccessToken | None) -> Iterator[None]:
    """Install ``token`` as the request's authenticated principal (or none at all)."""
    reset = auth_context_var.set(AuthenticatedUser(token) if token is not None else None)
    try:
        yield
    finally:
        auth_context_var.reset(reset)


async def call_and_capture(mcp: Any, tool_name: str) -> BaseException | None:
    """Call ``tool_name`` and return whatever it raised, or ``None`` if it returned.

    ``pytest.raises(Exception)`` is the wrong instrument for a "was NOT refused" pin:
    it fails when nothing is raised, so a build that made a tool succeed would red a
    pin that has nothing to say about success. This captures instead of demanding.
    """
    try:
        await mcp.call_tool(tool_name, {})
    except BaseException as exception:  # noqa: BLE001 - the pin classifies, never swallows
        return exception
    return None


async def mutating_tool_names(mcp: Any) -> frozenset[str]:
    """The DERIVED refused set: ``{tool : annotations.readOnlyHint is not True}``.

    Deny-by-default — ``annotations is None`` counts as mutating, so a tool registered
    without annotations is born refused rather than silently hosted-callable. This is
    the derivation that replaces #291's hand-list.

    ⚠ CALL THIS UNAUTHENTICATED. Under R13 the lookup is posture-SCOPED: with a hosted
    principal ambient, ``list_tools`` returns only the read ladder, so this would derive
    the empty set and every ∀ over it would be vacuous. Every call site here runs outside
    an ``as_principal`` block deliberately.
    """
    tools = await mcp.list_tools()
    return frozenset(
        tool.name
        for tool in tools
        if tool.annotations is None or tool.annotations.readOnlyHint is not True
    )


@pytest.fixture(autouse=True)
def _api_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Export the api-key env vars the hosted/LAN auth blocks reference."""
    monkeypatch.setenv(API_KEY_ENV_LOCAL_AGENT, API_KEY_VALUE_LOCAL_AGENT)
    monkeypatch.setenv(API_KEY_ENV_LAN_CLIENT, API_KEY_VALUE_LAN_CLIENT)


def hosted_server(tmp_path: Path, *, with_extension: bool = False) -> Any:
    """A ``build_mcp_server`` result in the ``HOSTED_OAUTH`` posture.

    ⚠ ``with_extension`` EXISTS BECAUSE ITS ABSENCE WAS A DEFECT. The ∀ classification pin
    below was FALSE on a correct build the moment one extension registered, and it passed
    only because this fixture registered none — a ∀ evaluated on the one registration path
    where it holds. R14 now rules that ``_register_extension_tools`` synthesizes
    ``readOnlyHint=False``, and the fixture must be able to reach that path.

    Args:
        tmp_path: The per-test directory for the roster and live root.
        with_extension: Register one extension, so the SECOND registration path is
            covered. No default was possible on the ∀ pin itself — it is parametrised
            over both values.
    """
    from loremaster.config import LoreConfig
    from loremaster.server import LoreServer, build_mcp_server

    roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)
    payload = base_config_payload(slug(), tmp_path / "live")
    payload["auth"] = hosted_auth_block(roster)
    server = LoreServer(LoreConfig.model_validate(payload))
    if with_extension:
        from _extension_helpers import CounterExtension

        server.register_extension(CounterExtension())
    return build_mcp_server(server)


def lan_bearer_server(tmp_path: Path) -> Any:
    """A ``build_mcp_server`` result in the ``LAN_BEARER`` posture."""
    from loremaster.config import LoreConfig
    from loremaster.server import LoreServer, build_mcp_server

    payload = base_config_payload(slug(), tmp_path / "live")
    payload["auth"] = lan_bearer_auth_block()
    return build_mcp_server(LoreServer(LoreConfig.model_validate(payload)))


def loopback_server(tmp_path: Path) -> Any:
    """A ``build_mcp_server`` result in the ``LOOPBACK`` posture (today's default)."""
    from loremaster.config import LoreConfig
    from loremaster.server import LoreServer, build_mcp_server

    payload = base_config_payload(slug(), tmp_path / "live")
    return build_mcp_server(LoreServer(LoreConfig.model_validate(payload)))


class TestEveryRegisteredToolIsClassified:
    """Posture ∀, half one: no tool is unclassified — the derivation has no gaps."""

    @pytest.mark.parametrize("with_extension", [False, True], ids=["core-only", "with-extension"])
    async def test_every_registered_tool_carries_an_explicit_read_only_hint(
        self, tmp_path: Path, with_extension: bool
    ) -> None:
        # The classification IS the security boundary now, so an unset hint is not a
        # missing nicety — it is a tool whose posture nobody decided.
        #
        # ⚑ PARAMETRISED OVER THE REGISTRATION PATH, because that is where this ∀ was
        # FALSE ON A CORRECT BUILD (delta adversary §4.5). ``_register_extension_tools``
        # called ``mcp.add_tool(...)`` with no ``annotations=``, and ``ToolSpec`` has no
        # field to carry one — so an extension tool reached the served surface
        # unclassified, and this pin passed only because its fixture registered no
        # extensions. That is the quantifier law's own shape: a ∀ evaluated only where
        # the branch cannot fire. R14 rules the synthesis; this parametrisation is what
        # makes the ∀ true over BOTH paths instead of over the convenient one.
        mcp = hosted_server(tmp_path, with_extension=with_extension)
        for tool in await mcp.list_tools():
            assert tool.annotations is not None, (
                f"{tool.name} carries no ToolAnnotations. Under R8 the hosted posture "
                f"is DERIVED from readOnlyHint, so an unannotated tool is refused by "
                f"construction — but leaving it unannotated hides a decision nobody "
                f"made. Annotate it."
            )
            assert tool.annotations.readOnlyHint is not None, (
                f"{tool.name}'s readOnlyHint is unset (None). Set it explicitly True "
                f"or False."
            )

    async def test_the_derived_mutating_set_equals_the_named_behaviour_fixtures(
        self, tmp_path: Path
    ) -> None:
        # EQUALITY, not the subset check #291's pin performed. A subset check cannot
        # see an omission, which is exactly how ``lore_claim_task`` and ``lore_tasks``
        # went unguarded. If this reds because a NEW tool appeared, the fix is to add
        # its behavioural fixture below — not to widen a list and move on.
        mcp = hosted_server(tmp_path)
        derived = await mutating_tool_names(mcp)
        assert derived == EXPECTED_MUTATING_TOOLS, (
            f"the derived refused set and the named behaviour fixtures disagree. "
            f"Only derived: {sorted(derived - EXPECTED_MUTATING_TOOLS)}; only named: "
            f"{sorted(EXPECTED_MUTATING_TOOLS - derived)}. Every mutating tool needs "
            f"a NAMED refusal fixture, or a flipped annotation would silently flip "
            f"the expectation with it."
        )

    async def test_the_read_surface_is_exactly_the_named_read_only_tools(
        self, tmp_path: Path
    ) -> None:
        # The control set. Without it, a build that annotated EVERY tool
        # ``readOnlyHint=False`` would satisfy the equality pin's mutating side while
        # leaving a hosted principal with no tools at all.
        mcp = hosted_server(tmp_path)
        names = {tool.name for tool in await mcp.list_tools()}
        assert names - EXPECTED_MUTATING_TOOLS == EXPECTED_READ_ONLY_TOOLS

    async def test_the_registered_surface_is_the_same_in_every_posture(
        self, tmp_path: Path
    ) -> None:
        # Design §7: tools stay REGISTERED and LISTED in every posture; refusal happens
        # at CALL, honestly taught. A build that unregistered the mutating tools in
        # hosted posture would break ``test_mcp_server``'s exact-set pin and, worse,
        # make the served surface depend on the deployment.
        hosted = {tool.name for tool in await hosted_server(tmp_path).list_tools()}
        loopback = {tool.name for tool in await loopback_server(tmp_path).list_tools()}
        assert hosted == loopback


class TestHostedPrincipalsAreRefusedEveryMutatingTool:
    """Posture ∀, half two — one NAMED fixture per mutating tool, per principal."""

    @pytest.mark.parametrize("tool_name", sorted(EXPECTED_MUTATING_TOOLS))
    @pytest.mark.parametrize("principal", GOOGLE_PRINCIPAL_LABELS)
    async def test_a_google_principal_cannot_call_a_mutating_tool(
        self, tmp_path: Path, tool_name: str, principal: str
    ) -> None:
        # TWO principals × SIX tools. The second principal exists because a build that
        # branched on one email would otherwise pass the whole group (the
        # value-monoculture law: 37 calls at one value once passed an entire contract).
        from loremaster.server import HostedToolRefusedError

        mcp = hosted_server(tmp_path)
        with as_principal(google_principals(principal)):
            with pytest.raises(HostedToolRefusedError) as excinfo:
                await mcp.call_tool(tool_name, {})
        message = str(excinfo.value)
        assert tool_name in message, "the refusal must name the tool that was refused"

    @pytest.mark.parametrize("tool_name", sorted(EXPECTED_READ_ONLY_TOOLS))
    async def test_a_google_principal_is_NOT_refused_a_read_only_tool(
        self, tmp_path: Path, tool_name: str
    ) -> None:
        # THE CONTROL for every refusal above, and it is not optional: a guard that
        # refused everything would pass all twelve refusal pins. The read ladder must
        # remain available — that is why hosted principals are admitted at all.
        # The call still fails downstream (the heavy context is not built here), so the
        # property under contract is that it is NOT refused BY THE POSTURE GUARD.
        from loremaster.server import HostedToolRefusedError

        mcp = hosted_server(tmp_path)
        with as_principal(google_principals("operator")):
            outcome = await call_and_capture(mcp, tool_name)
        assert not isinstance(outcome, HostedToolRefusedError), (
            f"{tool_name} is read-only and must pass the posture guard for a hosted "
            f"principal; it was refused. (Any OTHER outcome is acceptable here — the "
            f"tool then runs without a built AppContext.)"
        )

    @pytest.mark.parametrize("tool_name", sorted(EXPECTED_MUTATING_TOOLS))
    @pytest.mark.parametrize("principal", API_KEY_PRINCIPAL_LABELS)
    async def test_an_api_key_principal_is_NOT_refused_a_mutating_tool(
        self, tmp_path: Path, tool_name: str, principal: str
    ) -> None:
        # Design §1's mechanical verdict: "an api-key principal can call mutating tools
        # through the hosted port" — INTENDED. Two distinct key names, so a build that
        # branched on one name is caught.
        from loremaster.server import HostedToolRefusedError

        mcp = hosted_server(tmp_path)
        with as_principal(api_key_principals(principal)):
            outcome = await call_and_capture(mcp, tool_name)
        assert not isinstance(outcome, HostedToolRefusedError), (
            f"an api-key principal ({principal}) was refused {tool_name}; api keys are "
            f"the local/LAN trust anchor and retain the FULL surface"
        )

    @pytest.mark.parametrize("tool_name", sorted(EXPECTED_MUTATING_TOOLS))
    async def test_no_token_at_all_is_not_refused(
        self, tmp_path: Path, tool_name: str
    ) -> None:
        # Design §7: "No token at all (LOOPBACK posture) ⇒ full surface, unchanged."
        # A guard that refused on a MISSING token would break every local session on
        # this box the moment it shipped.
        from loremaster.server import HostedToolRefusedError

        mcp = loopback_server(tmp_path)
        with as_principal(None):
            outcome = await call_and_capture(mcp, tool_name)
        assert not isinstance(outcome, HostedToolRefusedError)

    async def test_a_write_scope_is_what_permits_not_the_client_id_shape(
        self, tmp_path: Path
    ) -> None:
        # The guard's rule is ``lore:write`` in the token's SCOPES (design §7), not a
        # string test on ``client_id``. A build that keyed on ``client_id.startswith
        # ("api_key:")`` passes every pin above and cannot express any future principal
        # shape — and would admit anything that merely spelled its client id that way.
        from loremaster.server import HostedToolRefusedError

        from lorerunes import SCOPE_READ

        forged = AccessToken(
            token=google_access_token("forged-client-id"),
            client_id="api_key:not-really-a-key",
            scopes=[SCOPE_READ],
            subject="impostor",
            claims={"iss": GOOGLE_ISSUER, "email": OPERATOR_EMAIL},
        )
        mcp = hosted_server(tmp_path)
        with as_principal(forged):
            with pytest.raises(HostedToolRefusedError):
                await mcp.call_tool("lore_remember", {})

    async def test_a_tool_registered_with_no_annotations_is_born_refused(
        self, tmp_path: Path
    ) -> None:
        # FAIL-CLOSED BY CONSTRUCTION, and the answer to the design's askable question:
        # "if I registered a new tool right now with no annotations, which pin reds and
        # which guard refuses it?" An extension-contributed tool is exactly this case.
        from loremaster.server import HostedToolRefusedError

        mcp = hosted_server(tmp_path)

        def _probe() -> str:
            """A newly contributed tool nobody has classified yet."""
            return "ok"

        mcp.add_tool(_probe, name=UNANNOTATED_PROBE_TOOL)

        derived = await mutating_tool_names(mcp)
        assert UNANNOTATED_PROBE_TOOL in derived, (
            "an unannotated tool must land in the DERIVED refused set — deny-by-"
            "default is what makes the classification safe for tools nobody wrote a "
            "fixture for"
        )
        with as_principal(google_principals("operator")):
            with pytest.raises(HostedToolRefusedError):
                await mcp.call_tool(UNANNOTATED_PROBE_TOOL, {})

    async def test_a_newly_registered_read_only_tool_is_permitted(
        self, tmp_path: Path
    ) -> None:
        # The CONTROL for the pin above: deny-by-default must not mean deny-everything-
        # new. An extension tool that DOES declare itself read-only is hosted-callable.
        from mcp.types import ToolAnnotations

        mcp = hosted_server(tmp_path)

        def _readonly_probe() -> str:
            """A newly contributed read-only tool."""
            return "contract-probe-ok"

        mcp.add_tool(
            _readonly_probe,
            name="lore_probe_readonly",
            annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
        )
        assert "lore_probe_readonly" not in await mutating_tool_names(mcp)
        with as_principal(google_principals("operator")):
            result = await mcp.call_tool("lore_probe_readonly", {})
        assert result is not None, (
            "a read-only extension tool must be callable by a hosted principal — "
            "deny-by-default must not mean deny-everything-new"
        )


class TestARefusedToolNeverRUNS:
    """N1 / WB48 — ⚑ THE BLOCKER, and the sharpest lesson of this packet (finding #295).

    **Every refusal pin in this contract observed the EXCEPTION. None observed the
    EFFECT.** A build that dispatches the tool and refuses afterwards therefore passed all
    448 pins — including the wire pin added in the previous wave, whose response body
    carried the ``HOSTED_OAUTH`` marker **byte-identically to the correct build's** — while
    the mutating tool's body had already executed (`invocations=1` vs the reference
    build's `0`). Same exception, same bytes, opposite reality: the memory row is written
    and the caller is then politely told it may not write.

    Two wrapper placements, two waves, both green: WB30 put the guard where the wire never
    reached it; WB48 put it after ``super().call_tool``. **ORDER is not observable from a
    message**, which is why R13 stops guarding invocation at all and scopes the LOOKUP
    instead — upstream ``ToolManager.call_tool`` is ``tool = self.get_tool(name); … await
    tool.run(...)`` (read at the installed SDK), so the run's operand IS the lookup result
    and the enforcement order is a data dependency the SDK writes, not a sequence a
    builder authors.

    **The askable form, and it applies to every refusal pin anyone writes from here:**
    *"if the guard ran AFTER the thing it guards, would this pin still pass?"*

    The instrument is the CALL COUNT, never the message. ``Tool.run``-entry is the effect
    boundary UPSTREAM of argument validation, so ``arguments={}`` can no longer mask a
    body that ran — which was the adversary's exact blind spot.
    """

    def _run_entry_recorder(self, monkeypatch: pytest.MonkeyPatch) -> list[str]:
        """Wrap ``Tool.run`` at its ENTRY and record every tool that reaches it.

        Deliberately at ``Tool.run`` rather than inside each tool body: it is the one
        boundary every dispatch must cross, upstream of argument validation, so no tool
        can be "the one nobody wrote a counter for".
        """
        from mcp.server.fastmcp.tools.base import Tool

        entered: list[str] = []
        original = Tool.run

        async def _recording_run(tool_self: Any, *args: Any, **kwargs: Any) -> Any:
            entered.append(tool_self.name)
            return await original(tool_self, *args, **kwargs)

        monkeypatch.setattr(Tool, "run", _recording_run)
        return entered

    async def test_no_refused_tool_body_is_ever_entered_for_a_hosted_principal(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # THE DERIVED ∀ EFFECT PIN (design R13 rider 1). Iterates the FULL registry rather
        # than a sample, so a newly added mutating tool is covered the day it is
        # registered — no "tool nobody wrote a counter for".
        from loremaster.server import HostedToolRefusedError

        entered = self._run_entry_recorder(monkeypatch)
        mcp = hosted_server(tmp_path)
        refused = await mutating_tool_names(mcp)
        assert refused, "the ∀ must range over a non-empty set, or it proves nothing"

        for tool_name in sorted(refused):
            with as_principal(google_principals("operator")):
                outcome = await call_and_capture(mcp, tool_name)
            assert isinstance(outcome, HostedToolRefusedError), (
                f"{tool_name} was not refused for a hosted principal; got {outcome!r}"
            )

        assert entered == [], (
            f"the bodies of {entered} were ENTERED while being refused. The caller sees a "
            f"correct refusal and the side effect has already happened — the read-only "
            f"posture is cosmetic. Ask: 'if the guard ran AFTER the thing it guards, "
            f"would this pin still pass?' This one would not, which is the point."
        )

    async def test_the_recorder_CAN_see_a_body_execute(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # ⚑ THE POSITIVE CONTROL FOR THE INSTRUMENT ITSELF (design R13 rider 2), and it is
        # not optional: a recorder that never fires would make the ∀ above pass on every
        # build, including WB48. A synthetic mutating tool with NO REQUIRED ARGUMENTS —
        # so argument validation can never be the reason a body did not run — proves the
        # recorder sees real execution.
        invocations: list[int] = []

        def probe_write() -> str:
            """A mutating tool with no required arguments."""
            invocations.append(1)
            return "contract-probe-ok"

        entered = self._run_entry_recorder(monkeypatch)
        mcp = hosted_server(tmp_path)
        mcp.add_tool(
            probe_write,
            name="lore_probe_write",
            annotations=ToolAnnotations(readOnlyHint=False, openWorldHint=False),
        )
        # With NO principal (the LOOPBACK shape) the tool is permitted and must run.
        with as_principal(None):
            await call_and_capture(mcp, "lore_probe_write")
        assert invocations, "the synthetic tool's body must be reachable at all"
        assert "lore_probe_write" in entered, (
            "the Tool.run recorder did not observe a body that demonstrably executed — "
            "the instrument is blind and every ∀ effect assertion above is vacuous"
        )

    async def test_the_same_synthetic_tool_is_refused_WITHOUT_running_when_hosted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The two halves meet: the SAME no-required-arguments mutating tool the recorder
        # just watched execute must now be refused with its body untouched. This is the
        # adversary's WB48 probe, kept as a contract fixture.
        from loremaster.server import HostedToolRefusedError

        invocations: list[int] = []

        def probe_write() -> str:
            """A mutating tool with no required arguments."""
            invocations.append(1)
            return "contract-probe-ok"

        entered = self._run_entry_recorder(monkeypatch)
        mcp = hosted_server(tmp_path)
        mcp.add_tool(
            probe_write,
            name="lore_probe_write",
            annotations=ToolAnnotations(readOnlyHint=False, openWorldHint=False),
        )
        with as_principal(google_principals("operator")):
            outcome = await call_and_capture(mcp, "lore_probe_write")
        assert isinstance(outcome, HostedToolRefusedError)
        assert not invocations, (
            "the refused tool's body ran before the refusal was raised — and its "
            "arguments were valid, so the write really happened"
        )
        assert "lore_probe_write" not in entered

    async def test_a_permitted_read_tool_body_IS_entered_for_a_hosted_principal(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # THE OTHER CONTROL: a build that dispatched NOTHING would pass every pin above,
        # and the hosted read surface — the entire reason a Google principal is admitted —
        # would be dead.
        def probe_read() -> str:
            """A read-only tool with no required arguments."""
            return "contract-probe-ok"

        entered = self._run_entry_recorder(monkeypatch)
        mcp = hosted_server(tmp_path)
        mcp.add_tool(
            probe_read,
            name="lore_probe_read",
            annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
        )
        with as_principal(google_principals("operator")):
            await call_and_capture(mcp, "lore_probe_read")
        assert "lore_probe_read" in entered, (
            "a read-only tool must actually reach its body for a hosted principal"
        )


class TestTheScopedLookupIsTheEnforcementSeam:
    """R13 — the guard is a scoped LOOKUP, so a refused tool is not RETURNED at all.

    The structural half of the R13 ruling. Because upstream ``ToolManager.call_tool``
    binds ``tool = self.get_tool(name)`` and then awaits ``tool.run(...)``, a lookup that
    withholds the tool cannot be "moved after" the run — there is no run without the
    lookup's return value. That is what takes PLACEMENT out of the builder's hands, after
    two waves in which placement was the defect.
    """

    async def test_a_hosted_principal_does_not_see_refused_tools_in_list_tools(
        self, tmp_path: Path
    ) -> None:
        mcp = hosted_server(tmp_path)
        refused = await mutating_tool_names(mcp)
        with as_principal(google_principals("operator")):
            visible = {tool.name for tool in await mcp.list_tools()}
        assert not (visible & refused), (
            f"a hosted principal was offered tools it cannot call: "
            f"{sorted(visible & refused)}. Under R13 the lookup is posture-scoped, so a "
            f"refused tool is not returned — advertising it is the served surface "
            f"over-claiming, and the agent learns the contract from what is served."
        )
        assert visible == EXPECTED_READ_ONLY_TOOLS, (
            f"the hosted principal's visible surface must be exactly the read ladder; "
            f"got {sorted(visible)}"
        )

    async def test_an_unauthenticated_lookup_is_unfiltered(self, tmp_path: Path) -> None:
        # THE CONTROL, and it protects the EXISTING deployment: with no ambient principal
        # (the LOOPBACK shape, and what every registration pin in test_mcp_server.py
        # drives) the lookup must be unfiltered, or the exact-set surface pin there breaks
        # and a local single-user deploy silently loses two thirds of its tools.
        mcp = hosted_server(tmp_path)
        with as_principal(None):
            visible = {tool.name for tool in await mcp.list_tools()}
        assert visible == EXPECTED_READ_ONLY_TOOLS | EXPECTED_MUTATING_TOOLS

    async def test_an_api_key_principal_sees_the_full_surface(self, tmp_path: Path) -> None:
        # Design §1: api keys are the local/LAN trust anchor and retain the FULL surface.
        mcp = hosted_server(tmp_path)
        with as_principal(api_key_principals("local-agent")):
            visible = {tool.name for tool in await mcp.list_tools()}
        assert visible == EXPECTED_READ_ONLY_TOOLS | EXPECTED_MUTATING_TOOLS

    def test_the_composed_server_installs_a_SCOPED_tool_manager(
        self, tmp_path: Path
    ) -> None:
        # The cheap structural pin R13 asks for. It names no class of ours — only that the
        # composed manager is a SUBCLASS of the SDK's, never the SDK's own. A build that
        # reverted to the stock manager and re-added a wrapper elsewhere reds here.
        from mcp.server.fastmcp.tools.tool_manager import ToolManager

        manager = hosted_server(tmp_path)._tool_manager
        assert isinstance(manager, ToolManager)
        assert type(manager) is not ToolManager, (
            "the composed FastMCP must install the posture-scoped ToolManager subclass; "
            "it is carrying the SDK's stock manager, so enforcement has moved back out "
            "into a wrapper whose placement is a free variable again (WB30/WB48)"
        )


class TestExtensionToolsAreRefusedWholesale:
    """R14 — the core cannot audit a project-authored callable, so it must not CLAIM it."""

    async def test_an_extension_tool_is_annotated_non_read_only(
        self, tmp_path: Path
    ) -> None:
        # R14: ``_register_extension_tools`` synthesizes the annotation. Not an accident
        # of a missing ``annotations=`` — a stated design property, so it cannot be
        # "fixed" back into an unclassified tool by a tidy-up.
        mcp = hosted_server(tmp_path, with_extension=True)
        tools = {tool.name: tool for tool in await mcp.list_tools()}
        extension_tools = set(tools) - EXPECTED_READ_ONLY_TOOLS - EXPECTED_MUTATING_TOOLS
        assert extension_tools, (
            "the fixture registered no extension tool — this pin would be vacuous"
        )
        for name in sorted(extension_tools):
            annotations = tools[name].annotations
            assert annotations is not None, f"{name} carries no ToolAnnotations"
            assert annotations.readOnlyHint is False, (
                f"{name} is extension-contributed and must be annotated "
                f"readOnlyHint=False: the core cannot verify a project-authored "
                f"callable's read-onlyness, so it must not claim it (R14)"
            )

    async def test_an_extension_tool_is_refused_for_a_hosted_principal(
        self, tmp_path: Path
    ) -> None:
        from loremaster.server import HostedToolRefusedError

        mcp = hosted_server(tmp_path, with_extension=True)
        extension_tools = (
            {tool.name for tool in await mcp.list_tools()}
            - EXPECTED_READ_ONLY_TOOLS
            - EXPECTED_MUTATING_TOOLS
        )
        for name in sorted(extension_tools):
            with as_principal(google_principals("operator")):
                outcome = await call_and_capture(mcp, name)
            assert isinstance(outcome, HostedToolRefusedError)

    async def test_an_extension_tool_remains_callable_via_an_api_key(
        self, tmp_path: Path
    ) -> None:
        # THE CONTROL: refusing extensions on the HOSTED surface must not break them for
        # the local/LAN principals who are the reason extensions exist.
        from loremaster.server import HostedToolRefusedError

        mcp = hosted_server(tmp_path, with_extension=True)
        extension_tools = (
            {tool.name for tool in await mcp.list_tools()}
            - EXPECTED_READ_ONLY_TOOLS
            - EXPECTED_MUTATING_TOOLS
        )
        assert extension_tools
        for name in sorted(extension_tools):
            with as_principal(api_key_principals("local-agent")):
                outcome = await call_and_capture(mcp, name)
            assert not isinstance(outcome, HostedToolRefusedError)


class TestTheRefusalTeaches:
    """A refusal a consumer cannot act on is a dead end (the Consumer Law)."""

    def _refusal(self, tmp_path: Path) -> Any:
        return hosted_server(tmp_path)

    async def test_the_refusal_names_the_posture_from_the_enum(
        self, tmp_path: Path
    ) -> None:
        # Design §7: "the posture name (from the enum)". Prose that hardcodes the name
        # survives a rename and teaches a posture that no longer exists — the exact
        # class CLAUDE.md names as this repo's #1 green-at-gate defect.
        from loremaster.server import HostedToolRefusedError

        from lorerunes import Posture

        mcp = self._refusal(tmp_path)
        with as_principal(google_principals("operator")):
            with pytest.raises(HostedToolRefusedError) as excinfo:
                await mcp.call_tool("lore_claim_task", {})
        message = str(excinfo.value)
        assert Posture.HOSTED_OAUTH.name in message, (
            f"the refusal must name its posture, taken FROM the enum; got {message!r}"
        )

    async def test_the_refusal_points_at_the_read_surface_that_remains(
        self, tmp_path: Path
    ) -> None:
        # A consumer that is refused and told nothing routes around the MCP entirely
        # (the trust doctrine). It must learn that the read ladder is still there.
        from loremaster.server import HostedToolRefusedError

        mcp = self._refusal(tmp_path)
        with as_principal(google_principals("operator")):
            with pytest.raises(HostedToolRefusedError) as excinfo:
                await mcp.call_tool("lore_remember", {})
        message = str(excinfo.value)
        assert any(name in message for name in sorted(EXPECTED_READ_ONLY_TOOLS)), (
            f"the refusal must name at least one tool the caller CAN still use; got "
            f"{message!r}"
        )

    async def test_the_refusal_is_a_structured_tool_error_not_an_unhandled_exception(
        self, tmp_path: Path
    ) -> None:
        # Design §7: "a STRUCTURED tool error (never an unhandled exception)". The SDK
        # renders a ``ToolError`` as ``isError: true`` content the agent can read; any
        # other exception becomes an opaque transport failure.
        from loremaster.server import HostedToolRefusedError
        from mcp.server.fastmcp.exceptions import ToolError

        assert issubclass(HostedToolRefusedError, ToolError), (
            "the refusal must be a FastMCP ToolError subclass so the SDK renders it as "
            "a structured tool error rather than a transport-level failure"
        )

    async def test_the_refusal_does_not_leak_the_credential(
        self, tmp_path: Path
    ) -> None:
        # The refusal message reaches the caller AND the logs. It names the tool, the
        # posture and the read surface — never the presented token.
        from loremaster.server import HostedToolRefusedError

        principal = google_principals("operator")
        mcp = self._refusal(tmp_path)
        with as_principal(principal):
            with pytest.raises(HostedToolRefusedError) as excinfo:
                await mcp.call_tool("lore_comms", {})
        assert principal.token not in str(excinfo.value)


class TestInstructionsAreHonestAboutThePosture:
    """The Consumer Law: what is served must match what happens (design §7)."""

    def test_the_hosted_instructions_carry_the_refused_set_section(
        self, tmp_path: Path
    ) -> None:
        from loremaster.server import HOSTED_REFUSAL_SECTION_HEADING

        instructions = hosted_server(tmp_path).instructions
        assert isinstance(instructions, str)
        assert HOSTED_REFUSAL_SECTION_HEADING in instructions, (
            "an agent connecting to the hosted surface must be TOLD which tools it "
            "cannot call, or it discovers the boundary by failing calls — the exact "
            "experience that makes a consumer route around the MCP"
        )

    def test_every_refused_tool_is_named_inside_that_section(self, tmp_path: Path) -> None:
        # Generated FROM the annotations, never prose beside them: the section must
        # name every mutating tool, so a newly-annotated tool cannot be refused in
        # silence.
        from loremaster.server import HOSTED_REFUSAL_SECTION_HEADING

        instructions = hosted_server(tmp_path).instructions
        section = instructions.split(HOSTED_REFUSAL_SECTION_HEADING, 1)[1]
        for name in sorted(EXPECTED_MUTATING_TOOLS):
            assert name in section, (
                f"{name} is refused for hosted principals but is not named in the "
                f"served refused-set section; the instructions would be teaching a "
                f"capability the server does not provide"
            )

    def test_the_refused_set_section_is_DERIVED_from_the_annotations(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # M7 / WB40 — PROVE SHARING BY MUTATION, because the pin above is a tautology on
        # the stock tool set. ``test_every_refused_tool_is_named_inside_that_section``
        # compares the served section against ``EXPECTED_MUTATING_TOOLS``, and a wrong
        # build that HARDCODES those same six names into the section satisfies it
        # exactly. Design §7 requires the section be "GENERATED from the registered
        # annotations (never prose beside them)"; a hand-listed section teaches a stale
        # refused set the day a tool is added or an annotation flips.
        #
        # The instrument: change the SHARED annotation constant the read tools register
        # with, then rebuild. A derived section follows the annotations and names all
        # fifteen tools; a hand-list still names six. This is the repo's own rule —
        # *change the shared thing and every caller must change with it* — applied to a
        # served natural-language surface, which is the class no gate can otherwise see.
        import loremaster.server as server_module
        from loremaster.server import HOSTED_REFUSAL_SECTION_HEADING
        from mcp.types import ToolAnnotations

        monkeypatch.setattr(
            server_module,
            "_READ_ONLY_ANNOTATIONS",
            ToolAnnotations(readOnlyHint=False, idempotentHint=True, openWorldHint=False),
        )
        mcp = hosted_server(tmp_path)
        derived = asyncio.run(mutating_tool_names(mcp))
        assert derived > EXPECTED_MUTATING_TOOLS, (
            "the fixture must actually widen the refused set — if flipping the shared "
            "read-only annotation changed nothing, this pin is inert and the mutation "
            "did not land"
        )

        instructions = mcp.instructions or ""
        section = instructions.split(HOSTED_REFUSAL_SECTION_HEADING, 1)[1]
        missing = sorted(name for name in derived if name not in section)
        assert not missing, (
            f"the served refused-set section did not follow the annotations: {missing} "
            f"are refused but unnamed. The section is a HAND-LIST, not a derivation — "
            f"so the day a tool is added or an annotation flips, the instructions teach "
            f"a refused set that has drifted from what the server actually does."
        )

    def test_the_refused_clause_names_EXACTLY_the_refused_set(self, tmp_path: Path) -> None:
        # N2 / WB50 — ⚑ A SERVED SURFACE THAT LIES, in the direction nobody pinned.
        # Every section pin so far checked MEMBERSHIP: "is each refused tool named?".
        # A build that drops the annotation filter names ALL FIFTEEN tools as refused and
        # satisfies every one of them, because a superset has nothing missing. The served
        # paragraph then says `lore_search` is refused AND available in the same breath,
        # and under the Consumer Law the reader is a model that learns the contract from
        # what is served: it stops calling the read ladder and routes around the MCP.
        #
        # EQUALITY, both directions, against the DERIVATION rather than a literal — so the
        # render is checked against the same classification it claims to describe.
        from loremaster.server import (
            HOSTED_READ_LADDER_MARKER,
            HOSTED_REFUSAL_SECTION_HEADING,
        )

        mcp = hosted_server(tmp_path)
        refused = asyncio.run(mutating_tool_names(mcp))
        instructions = mcp.instructions or ""
        section = instructions.split(HOSTED_REFUSAL_SECTION_HEADING, 1)[1]
        refused_clause = section.split(HOSTED_READ_LADDER_MARKER, 1)[0]

        named = {name for name in ALL_TOOL_NAMES if name in refused_clause}
        assert named == refused, (
            f"the served refused-set clause does not match the derivation. Named but not "
            f"refused: {sorted(named - refused)} (the surface OVER-claims — an agent told "
            f"a read tool is refused stops using it). Refused but not named: "
            f"{sorted(refused - named)} (the surface UNDER-claims — the agent discovers "
            f"the boundary by failing calls)."
        )

    def test_the_read_ladder_clause_names_EXACTLY_the_readable_set(
        self, tmp_path: Path
    ) -> None:
        # N3 / WB50b — the same equality on the other clause. A build whose read-ladder
        # list is EMPTY serves "The read ladder remains fully available: ." and passes
        # every shipped pin, telling a hosted principal it has no surface at all. The
        # refusal's whole job is to leave the caller a next move.
        from loremaster.server import (
            HOSTED_READ_LADDER_MARKER,
            HOSTED_REFUSAL_SECTION_HEADING,
        )

        mcp = hosted_server(tmp_path)
        refused = asyncio.run(mutating_tool_names(mcp))
        readable = ALL_TOOL_NAMES - refused
        assert readable, "the derivation must leave a non-empty read ladder"

        instructions = mcp.instructions or ""
        section = instructions.split(HOSTED_REFUSAL_SECTION_HEADING, 1)[1]
        ladder_clause = section.split(HOSTED_READ_LADDER_MARKER, 1)[1]

        named = {name for name in ALL_TOOL_NAMES if name in ladder_clause}
        assert named == readable, (
            f"the served read-ladder clause does not match the derivation. Missing: "
            f"{sorted(readable - named)}; wrongly offered: {sorted(named - readable)}."
        )

    def test_the_section_is_absent_in_loopback_posture(self, tmp_path: Path) -> None:
        # A local single-user deployment has the FULL surface; telling it otherwise is
        # the same dishonesty in the other direction.
        from loremaster.server import HOSTED_REFUSAL_SECTION_HEADING

        assert HOSTED_REFUSAL_SECTION_HEADING not in loopback_server(tmp_path).instructions

    def test_the_section_is_absent_in_lan_bearer_posture(self, tmp_path: Path) -> None:
        from loremaster.server import HOSTED_REFUSAL_SECTION_HEADING

        assert HOSTED_REFUSAL_SECTION_HEADING not in lan_bearer_server(tmp_path).instructions

    def test_the_instructions_still_name_every_registered_tool_in_hosted_posture(
        self, tmp_path: Path
    ) -> None:
        # Design §7 states the existing pins must stay green: tools remain REGISTERED
        # and listed; refusal happens at call. This is that property, asserted here so
        # the hosted branch cannot quietly drop the read tools from the instructions.
        instructions = hosted_server(tmp_path).instructions
        for name in sorted(EXPECTED_READ_ONLY_TOOLS | EXPECTED_MUTATING_TOOLS):
            assert name in instructions, f"{name} is registered but not taught"
