"""Packet SDK3 contract, round 4 — lead decision R9 D1 (operator MAY overturn): an outcome the client cannot
know is NEVER served as a definite failure.

``docs/plans/v2/sdk3-rulings.md`` R5 rider 2 ("a timed-out or in-flight-dropped WRITE is raised as 'outcome
unknown' … never as a plain failure"), R8 F14 (EVERY SDK transport failure on a request maps to
``SurrealOutcomeUnknownError``, a ``SurrealConnectionError`` subclass), R9 D1 (rider 2 covers SERVED
surfaces).

The defect D1 names, at HEAD and on the round-3 reference: ``AppContext._resolve_or_acknowledge_many`` (the
finding batch verbs ``resolve_many`` / ``acknowledge_many``) catches ``SurrealConnectionError`` and serves
"``<ref>`` ABORTED — store connection lost; retry these". Under F14 that catch receives every in-flight drop
and every timed-out reply, so a resolve whose commit MAY HAVE LANDED is served as aborted and the agent is
told
to re-apply it: a Leg-2 false clear (CLAUDE.md TRUST: a consumer acting without checking is wrong in a way the
response did not name). Prior art that already gets it right: ``principal_keys._mint_fault_note`` and
``_txn.proven_no_key`` treat transport as UNKNOWN.

Two pins:

* ``TestEveryCatchSiteThatNamesTheTransportErrorIsAdjudicated`` — the SET of sites is DERIVED, never
  hand-listed: every production catch site (THE ONE walker, ``_catch_sites.production_catch_sites`` — packet
  58's approved instrument, reused, not a new scanner) whose caught classes NAME ``SurrealConnectionError`` or
  a subclass of it and that an outcome-unknown error can reach (no earlier clause of the same ``try`` catches
  it first). A site whose handler is a bare re-raise passes the error on untouched (derived: it serves
  nothing). Every other site must be ADJUDICATED to the behaviour pin that proves its rendering — and an
  adjudication with no site, or a site with no adjudication, is RED. The set growing without the adjudication
  growing is exactly the reach failure this pin exists to catch.
* ``TestTheBatchVerbNeverServesAnUnknownOutcomeAsAborted`` — the one rendering site, by BEHAVIOUR: the item
  whose call raised ``SurrealOutcomeUnknownError`` is served as outcome-unknown with a "verify before
  retrying" instruction, never as ABORTED / "retry these".

BOUND, stated (scope fork F18 in the packet doc §R4): sites reached only through a BROAD catch
(``Exception`` / ``BaseException`` / ``SurrealStoreError`` …) are outside this derivation — 53 at the round-4
reference, 14 of them ``SurrealStoreError``-family, one of which (``briefs.BriefLedger.publish``) releases the
minted version on ANY store error ("nothing committed") — an outcome-unknown publish may have committed. And
an ``isinstance`` dispatch (``principal_keys._mint_fault_note``) is not a catch site; it is the prior art and
renders "unconfirmed" already.
"""

from __future__ import annotations

import ast
from typing import Any

import pytest
from _catch_sites import CatchSite, production_catch_sites
from loremaster.server import AppContext
from loremaster.store import _txn
from loremaster.store._txn import SurrealConnectionError
from test_mcp_server import (  # noqa: F401 - fixtures (rollup_ctx and its chain) and the autouse env
    _surreal_test_env,
    cutover_ctx,
    rollup_ctx,
)

# Every catch site that NAMES the transport error and serves something other than a bare re-raise, mapped to
# the behaviour pin (in this file) that proves what it serves for an outcome-unknown error.
_ADJUDICATED_RENDERING_SITES: dict[str, str] = {
    "server.py::_resolve_or_acknowledge_many": "TestTheBatchVerbNeverServesAnUnknownOutcomeAsAborted",
}


class _RaisingOnSecondCall:
    """The finding ledger with its SECOND ``resolve`` / ``acknowledge`` call raising ``error``.

    ``test_mcp_server._LedgerRaisingOnSecondCall`` is the shared injector, but it forwards a ``subject=``
    keyword the current ``FakeFindingLedger`` does not accept (a dormant 64b-i seam — measured 2026-11-07:
    ``TypeError: FakeFindingLedger.resolve() got an unexpected keyword argument 'subject'``), so it cannot
    drive the renderer today; this is the same double without that keyword."""

    def __init__(self, inner: Any, error: BaseException) -> None:
        self._inner = inner
        self._error = error
        self._calls: dict[str, int] = {}

    def _maybe_raise(self, verb: str) -> None:
        self._calls[verb] = self._calls.get(verb, 0) + 1
        if self._calls[verb] == 2:
            raise self._error

    async def resolve(self, id_or_number: int | str, actor: str, note: str | None = None) -> Any:
        self._maybe_raise("resolve")
        return await self._inner.resolve(id_or_number, actor, note)

    async def acknowledge(self, id_or_number: int | str, actor: str, note: str | None = None) -> Any:
        self._maybe_raise("acknowledge")
        return await self._inner.acknowledge(id_or_number, actor, note)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


def _unknown_type() -> type:
    unknown = getattr(_txn, "SurrealOutcomeUnknownError", None)
    assert isinstance(unknown, type) and issubclass(unknown, SurrealConnectionError), (
        "store._txn.SurrealOutcomeUnknownError does not exist as a SurrealConnectionError subclass "
        "(R5 rider 2)"
    )
    return unknown


def _names_the_transport_error(site: CatchSite) -> bool:
    return any(isinstance(cls, type) and issubclass(cls, SurrealConnectionError) for cls in site.caught)


def _is_bare_reraise(site: CatchSite) -> bool:
    body = site.handler.body if site.handler is not None else []
    return len(body) == 1 and isinstance(body[0], ast.Raise) and body[0].exc is None


def _sites_an_unknown_outcome_reaches() -> list[CatchSite]:
    unknown = _unknown_type()
    return [
        site
        for site in production_catch_sites()
        if _names_the_transport_error(site)
        and any(issubclass(unknown, cls) for cls in site.caught)
        and not any(issubclass(unknown, cls) for cls in site.earlier)
    ]


class TestEveryCatchSiteThatNamesTheTransportErrorIsAdjudicated:
    """R9 D1, the reach half: ∀ derived sites, either a bare re-raise or adjudicated to a behaviour pin."""

    def test_the_derivation_is_not_vacuous(self) -> None:
        sites = _sites_an_unknown_outcome_reaches()
        assert len(sites) >= len(_ADJUDICATED_RENDERING_SITES) + 1, (
            f"the derived set holds {len(sites)} sites ({[site.key for site in sites]}) — the walker or the "
            f"class resolution is broken, and every verdict below would pass vacuously"
        )

    def test_every_rendering_site_is_adjudicated_and_every_adjudication_has_its_site(self) -> None:
        rendering = {site.key for site in _sites_an_unknown_outcome_reaches() if not _is_bare_reraise(site)}
        unadjudicated = sorted(rendering - set(_ADJUDICATED_RENDERING_SITES))
        assert not unadjudicated, (
            f"catch sites that NAME SurrealConnectionError, are reachable by SurrealOutcomeUnknownError, and "
            f"serve something other than a bare re-raise, with no behaviour pin proving they never serve an "
            f"unknown outcome as a definite failure (R9 D1): {unadjudicated}. Pin the site's rendering by "
            f"behaviour, then adjudicate it here."
        )
        stale = sorted(set(_ADJUDICATED_RENDERING_SITES) - rendering)
        assert not stale, (
            f"adjudicated sites that no longer exist as derived rendering sites: {stale}; delete the row "
            f"with "
            f"the site (or the site moved, and its pin with it)"
        )


class TestTheBatchVerbNeverServesAnUnknownOutcomeAsAborted:
    """R9 D1, the behaviour half — ``lore_findings action=resolve_many``. Item 2 of 3 raises
    ``SurrealOutcomeUnknownError`` (its write was SENT; no reply came). Its served line must say the outcome
    is unknown and tell the agent to VERIFY before retrying — never ABORTED, never "retry these" (the
    instruction to re-apply a write that may have committed). Item 1 is unaffected. Hostile-input control:
    the ref label is rendered sanitised by the existing batch pins (``test_mcp_server``); here only the
    outcome WORDS are pinned, so a build may word the line freely as long as it names the outcome honestly.
    A plain ``SurrealConnectionError`` (nothing sent — e.g. a refused connect) keeps the existing ABORTED
    pin in ``test_mcp_server`` (``test_connection_loss_aborts_remaining_as_render_not_raise``)."""

    @pytest.mark.parametrize("action", ["resolve_many", "acknowledge_many"])
    async def test_the_item_whose_outcome_is_unknown_is_served_as_unknown(
        self, rollup_ctx: AppContext, action: str  # noqa: F811 - the fixture imported above
    ) -> None:
        unknown = _unknown_type()
        findings = [
            await rollup_ctx.finding_ledger.report(f"s{index}", "b", area="a", category="c", created_by="me")
            for index in range(3)
        ]
        setattr(
            rollup_ctx,
            "finding_ledger",
            _RaisingOnSecondCall(
                rollup_ctx.finding_ledger,
                unknown("SurrealDB transaction against 'ws://x' got no reply (outcome unknown)"),
            ),
        )
        # The derived catch site itself (the served renderer behind ``lore_findings action=resolve_many`` /
        # ``acknowledge_many``) — called directly: the tool's identity arming is a separate (64b-i) seam.
        rendered, _writes = await rollup_ctx._resolve_or_acknowledge_many(
            action=action,
            items=[{"id_or_number": finding.number} for finding in findings],
            actor="slate-lead",
        )
        lines = rendered.splitlines()
        second: Any = next((line for line in lines if line.startswith(f"- #{findings[1].number} ")), None)
        assert second is not None, f"the batch rendered no line for item 2: {rendered!r}"
        lowered = second.lower()
        assert "aborted" not in lowered and "retry these" not in lowered, (
            f"an item whose write may have COMMITTED is served as {second!r}: R9 D1 / R5 rider 2: an unknown "
            f"outcome is never a definite failure, and the agent must not be told to re-apply it"
        )
        assert "outcome unknown" in lowered and "verify" in lowered, (
            f"the item whose call raised SurrealOutcomeUnknownError is served as {second!r}; it must name "
            f"the "
            f"outcome as unknown and tell the agent to verify before retrying"
        )
        assert any(line.startswith(f"- #{findings[0].number} ") and "FAILED" not in line for line in lines), (
            f"item 1 (applied before the fault) is not served as applied: {rendered!r}"
        )
