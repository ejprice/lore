"""CONTRACT — the ``PermissionResolver`` extension seam (design §4, "Extension seam").

Operator directive, as the design records it: **seam only now, the Odoo resolver at
supersede.** ``resolve_auth`` is ~265 lines in odoo-code; none of it lands here. What
lands is the shape it will plug into, plus proof that the shape can actually do
something — because *"a seam only ever exercised as identity is a seam nobody knows is
broken"* (design §4's own rider, and the repo's "can the fake actually FAIL" law).

------------------------------------------------------------------------------
THE SURFACE

* ``AuthContext`` — a frozen value object: ``subject``, ``email``, ``provenance``
  (``"api_key"`` | ``"google"``), ``permitted`` (``frozenset[str] | None``, where
  ``None`` means UNFILTERED).
* ``PermissionResolver`` — ``async def resolve(context: AuthContext) -> AuthContext``.
* ``PassThroughPermissionResolver`` — the shipping default; returns its input.
* ``auth_context_from_access_token`` — the derivation at tool dispatch, from the SDK's
  ``get_access_token()``.

------------------------------------------------------------------------------
THE WRONG BUILDS THESE PINS DISCRIMINATE AGAINST

* **A seam that is never consulted.** A resolver injected and ignored passes every
  pass-through pin (the default returns its input, so identity is indistinguishable
  from "not called"). The NON-pass-through fake below is what makes the difference
  observable.
* **A seam whose ``permitted`` is decorative.** A resolver that narrows the set and
  changes nothing is a filter nobody knows is broken until the Odoo resolver lands on
  it and quietly grants everyone everything.
* **``permitted=frozenset()`` read as falsy.** An EMPTY set means *"nothing is
  permitted"*, and ``None`` means *"unfiltered"*. A build that writes
  ``if context.permitted:`` collapses those two into "unfiltered" — the F4 fail-open
  shape, reproduced one layer up. Pinned explicitly.
"""

from __future__ import annotations

import time
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
    API_KEY_NAME_LOCAL_AGENT,
    API_KEY_VALUE_LAN_CLIENT,
    API_KEY_VALUE_LOCAL_AGENT,
    GOOGLE_ACCESS_TOKEN_LIFETIME_S,
    GOOGLE_CLIENT_ID,
    GOOGLE_ISSUER,
    OPERATOR_EMAIL,
    OPERATOR_SUBJECT,
    base_config_payload,
    google_access_token,
    hosted_auth_block,
    slug,
    write_roster,
)
from mcp.server.auth.provider import AccessToken

# A read tool that a hosted principal is otherwise entitled to call — so when the fake
# resolver removes it, the refusal can only have come from the seam.
FILTERED_READ_TOOL = "lore_recall"
PERMITTED_READ_TOOL = "lore_search"


@pytest.fixture(autouse=True)
def _api_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Export the api-key env vars the hosted auth block references."""
    monkeypatch.setenv(API_KEY_ENV_LOCAL_AGENT, API_KEY_VALUE_LOCAL_AGENT)
    monkeypatch.setenv(API_KEY_ENV_LAN_CLIENT, API_KEY_VALUE_LAN_CLIENT)


def google_access(email: str = OPERATOR_EMAIL) -> AccessToken:
    """A hosted Google principal as ``LoreTokenVerifier`` mints one."""
    from lorerunes import SCOPE_READ
    return AccessToken(
        token=google_access_token("seam"),
        client_id=GOOGLE_CLIENT_ID,
        scopes=[SCOPE_READ],
        expires_at=int(time.time()) + GOOGLE_ACCESS_TOKEN_LIFETIME_S,
        subject=OPERATOR_SUBJECT,
        claims={"iss": GOOGLE_ISSUER, "email": email},
    )


def api_key_access() -> AccessToken:
    """A local api-key principal as ``LoreTokenVerifier`` mints one."""
    from lorerunes import SCOPE_READ, SCOPE_WRITE
    return AccessToken(
        token=API_KEY_VALUE_LOCAL_AGENT,
        client_id=f"api_key:{API_KEY_NAME_LOCAL_AGENT}",
        scopes=[SCOPE_READ, SCOPE_WRITE],
        subject=API_KEY_NAME_LOCAL_AGENT,
    )


class TestAuthContextDerivation:
    """The value object the resolver receives, derived from the SDK's access token."""

    def test_a_google_token_derives_a_google_provenance_context(self) -> None:
        from loremaster.auth import auth_context_from_access_token

        context = auth_context_from_access_token(google_access())
        assert context is not None
        assert context.provenance == "google"
        assert context.subject == OPERATOR_SUBJECT
        assert context.email == OPERATOR_EMAIL
        assert context.permitted is None, (
            "an unfiltered context is None, never an empty set — the two mean opposite "
            "things and collapsing them is a fail-open"
        )

    def test_an_api_key_token_derives_an_api_key_provenance_context(self) -> None:
        # TWO provenances, so a build that hardcodes one is caught. The provenance is
        # what a future resolver keys on to decide whether to filter at all.
        from loremaster.auth import auth_context_from_access_token

        context = auth_context_from_access_token(api_key_access())
        assert context is not None
        assert context.provenance == "api_key"
        assert context.subject == API_KEY_NAME_LOCAL_AGENT
        assert context.email is None

    def test_no_token_derives_no_context(self) -> None:
        # The LOOPBACK posture: no principal, so no context to resolve, and the seam
        # must not invent one (an invented context is an identity nobody authenticated).
        from loremaster.auth import auth_context_from_access_token

        assert auth_context_from_access_token(None) is None

    def test_the_context_is_frozen(self) -> None:
        # It crosses a plug-in boundary; a third-party resolver must not be able to
        # mutate the caller's copy in place instead of returning a new one.
        from loremaster.auth import auth_context_from_access_token

        context = auth_context_from_access_token(google_access())
        with pytest.raises((AttributeError, TypeError)):
            setattr(context, "subject", "someone-else")


class TestPassThroughResolverIsTheShippingDefault:
    """The default changes nothing — and the pin proves it changes NOTHING, field by field."""

    async def test_it_returns_an_equal_context(self) -> None:
        from loremaster.auth import PassThroughPermissionResolver, auth_context_from_access_token

        original = auth_context_from_access_token(google_access())
        assert original is not None
        resolved = await PassThroughPermissionResolver().resolve(original)
        assert resolved == original

    async def test_it_leaves_permitted_unfiltered(self) -> None:
        from loremaster.auth import PassThroughPermissionResolver, auth_context_from_access_token

        original = auth_context_from_access_token(api_key_access())
        assert original is not None
        assert (await PassThroughPermissionResolver().resolve(original)).permitted is None

    def test_it_satisfies_the_resolver_protocol(self) -> None:
        import inspect

        from loremaster.auth import PassThroughPermissionResolver

        resolve = PassThroughPermissionResolver.resolve
        assert inspect.iscoroutinefunction(resolve), (
            "the seam is async because the Odoo resolver will do I/O (it calls Odoo). "
            "A sync default would force the whole seam to be re-shaped at supersede."
        )


class _AllowOnlyResolver:
    """A NON-pass-through resolver — the proof the seam can actually filter.

    Design §4's rider verbatim: *"the pass-through resolver's pin includes one
    NON-pass-through fake resolver in the contract, so the seam is proven ABLE to
    filter"*. A fake that cannot fail grades nothing.
    """

    def __init__(self, permitted: frozenset[str]) -> None:
        self.permitted = permitted
        self.calls: list[str] = []

    async def resolve(self, context: Any) -> Any:
        """Narrow ``context.permitted`` to this resolver's allow-set."""
        import dataclasses

        self.calls.append(context.subject)
        return dataclasses.replace(context, permitted=self.permitted)


def hosted_server(tmp_path: Path, resolver: Any) -> Any:
    """Build the hosted server with ``resolver`` injected at the seam."""
    from loremaster.config import LoreConfig
    from loremaster.server import LoreServer, build_mcp_server

    roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
    payload = base_config_payload(slug(), tmp_path / "live")
    payload["auth"] = hosted_auth_block(roster)
    config = LoreConfig.model_validate(payload)
    return build_mcp_server(LoreServer(config), permission_resolver=resolver)


class TestTheSeamIsConsultedAtDispatchAndCanFilter:
    """The seam is WIRED, not merely defined (routing is not sharing)."""

    async def test_the_injected_resolver_is_called_on_every_tool_dispatch(
        self, tmp_path: Path
    ) -> None:
        # A resolver that is injected and never called passes every pass-through pin,
        # because the default's identity behaviour is indistinguishable from silence.
        # The call log is what makes the wiring observable.
        from test_hosted_readonly_posture import as_principal, call_and_capture

        resolver = _AllowOnlyResolver(frozenset({PERMITTED_READ_TOOL, FILTERED_READ_TOOL}))
        mcp = hosted_server(tmp_path, resolver)
        with as_principal(google_access()):
            await call_and_capture(mcp, PERMITTED_READ_TOOL)
        assert resolver.calls == [OPERATOR_SUBJECT], (
            f"the injected PermissionResolver was consulted {len(resolver.calls)} "
            f"time(s) for one dispatch; the seam is not wired into tool dispatch"
        )

    async def test_a_tool_outside_the_resolved_permitted_set_is_refused(
        self, tmp_path: Path
    ) -> None:
        # THE PROOF THE FAKE CAN FAIL. Both tools are read-only, so the posture guard
        # permits both; the ONLY thing that can distinguish them is the resolver's
        # narrowed set.
        from loremaster.server import PermissionFilteredToolError
        from test_hosted_readonly_posture import as_principal, call_and_capture

        resolver = _AllowOnlyResolver(frozenset({PERMITTED_READ_TOOL}))
        mcp = hosted_server(tmp_path, resolver)
        with as_principal(google_access()):
            outcome = await call_and_capture(mcp, FILTERED_READ_TOOL)
        assert isinstance(outcome, PermissionFilteredToolError), (
            f"{FILTERED_READ_TOOL} was removed from the resolved permitted set and "
            f"must be refused; got {outcome!r}. A seam whose output is ignored is a "
            f"filter nobody knows is broken until the Odoo resolver lands on it."
        )

    async def test_a_tool_inside_the_resolved_permitted_set_is_not_refused(
        self, tmp_path: Path
    ) -> None:
        # The CONTROL, and it is the whole reason the pin above means anything: with
        # the SAME resolver, a permitted tool must NOT be refused. Without this, a
        # build that refused every tool would pass the filter pin.
        from loremaster.server import PermissionFilteredToolError
        from test_hosted_readonly_posture import as_principal, call_and_capture

        resolver = _AllowOnlyResolver(frozenset({PERMITTED_READ_TOOL}))
        mcp = hosted_server(tmp_path, resolver)
        with as_principal(google_access()):
            outcome = await call_and_capture(mcp, PERMITTED_READ_TOOL)
        assert not isinstance(outcome, PermissionFilteredToolError)

    async def test_an_empty_permitted_set_permits_NOTHING(self, tmp_path: Path) -> None:
        # ``frozenset()`` means "nothing permitted"; ``None`` means "unfiltered". A
        # build that writes ``if context.permitted:`` reads the empty set as falsy and
        # grants EVERYTHING — the F4 fail-open shape reproduced one layer up, in the
        # seam the Odoo ACL resolver will plug into.
        from loremaster.server import PermissionFilteredToolError
        from test_hosted_readonly_posture import as_principal, call_and_capture

        resolver = _AllowOnlyResolver(frozenset())
        mcp = hosted_server(tmp_path, resolver)
        with as_principal(google_access()):
            outcome = await call_and_capture(mcp, PERMITTED_READ_TOOL)
        assert isinstance(outcome, PermissionFilteredToolError), (
            "an EMPTY permitted set must permit nothing. Reading it as falsy — i.e. "
            "as 'unfiltered' — is the fail-open this seam must never inherit."
        )

    async def test_the_default_build_uses_the_pass_through_resolver(
        self, tmp_path: Path
    ) -> None:
        # No resolver injected ⇒ the shipping default, and nothing is filtered. This is
        # what "seam only, no behaviour change" MEANS, asserted rather than assumed.
        from loremaster.config import LoreConfig
        from loremaster.server import (
            LoreServer,
            PermissionFilteredToolError,
            build_mcp_server,
        )
        from test_hosted_readonly_posture import as_principal, call_and_capture

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["auth"] = hosted_auth_block(roster)
        mcp = build_mcp_server(LoreServer(LoreConfig.model_validate(payload)))
        with as_principal(google_access()):
            for tool_name in (PERMITTED_READ_TOOL, FILTERED_READ_TOOL):
                outcome = await call_and_capture(mcp, tool_name)
                assert not isinstance(outcome, PermissionFilteredToolError)

    async def test_the_refusal_is_a_structured_tool_error(self) -> None:
        from loremaster.server import PermissionFilteredToolError
        from mcp.server.fastmcp.exceptions import ToolError

        assert issubclass(PermissionFilteredToolError, ToolError)

    async def test_the_posture_guard_and_the_resolver_are_distinguishable(
        self, tmp_path: Path
    ) -> None:
        # Two refusals, two causes, two types. A consumer that is refused needs to know
        # whether the whole posture forbids the tool (never retry) or their own
        # permissions do (an operator can grant it) — collapsing them into one error
        # teaches the wrong remedy.
        from loremaster.server import HostedToolRefusedError, PermissionFilteredToolError
        from test_hosted_readonly_posture import as_principal, call_and_capture

        resolver = _AllowOnlyResolver(frozenset({PERMITTED_READ_TOOL}))
        mcp = hosted_server(tmp_path, resolver)
        with as_principal(google_access()):
            posture_refusal = await call_and_capture(mcp, "lore_remember")
            filter_refusal = await call_and_capture(mcp, FILTERED_READ_TOOL)
        assert isinstance(posture_refusal, HostedToolRefusedError)
        assert isinstance(filter_refusal, PermissionFilteredToolError)
        assert not isinstance(filter_refusal, HostedToolRefusedError)
