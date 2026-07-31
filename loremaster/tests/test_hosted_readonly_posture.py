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


def hosted_server(tmp_path: Path) -> Any:
    """A ``build_mcp_server`` result in the ``HOSTED_OAUTH`` posture."""
    from loremaster.config import LoreConfig
    from loremaster.server import LoreServer, build_mcp_server

    roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)
    payload = base_config_payload(slug(), tmp_path / "live")
    payload["auth"] = hosted_auth_block(roster)
    return build_mcp_server(LoreServer(LoreConfig.model_validate(payload)))


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

    async def test_every_registered_tool_carries_an_explicit_read_only_hint(
        self, tmp_path: Path
    ) -> None:
        # The classification IS the security boundary now, so an unset hint is not a
        # missing nicety — it is a tool whose posture nobody decided.
        mcp = hosted_server(tmp_path)
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
