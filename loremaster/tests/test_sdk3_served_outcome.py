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

# Rendering sites whose behaviour pin lives in ``test_sdk3_outcome_reach`` (round 5, R12 F18). A fix may route
# the unknown outcome through a NAMED catch (then the site appears here) or an ``isinstance`` dispatch inside
# a
# broad handler (then it does not): the behaviour pin guards the outcome either way, so absence is not stale.
_PINNED_IN_OUTCOME_REACH: dict[str, str] = {
    "calibration/engine.py::_file_drift_finding_deduped": "TestAnUnknownDriftFilingIsServedAsUnknown",
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
        unadjudicated = sorted(rendering - set(_ADJUDICATED_RENDERING_SITES) - set(_PINNED_IN_OUTCOME_REACH))
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


# R12 F18 — the ``SurrealStoreError``-FAMILY catch sites an outcome-unknown error reaches (14 at the round-5
# reference), each adjudicated. ``("pin", "<module>::<Class>")`` names the behaviour pin proving the site
# never
# serves an unknown outcome as a definite failure; ``("verdict", "...")`` is the packet doc §ROUND 5 one-line
# verdict for a site that serves nothing an agent could act on wrongly (a read, a self-healing tick, an honest
# re-raise). A pinned site may LEAVE the derived set (a fix that shields it with an earlier
# ``except SurrealOutcomeUnknownError`` makes it unreachable) — its behaviour pin still guards it; a VERDICT
# row
# whose site is gone is stale and RED.
_FAMILY_ADJUDICATION: dict[str, tuple[str, str]] = {
    "briefs.py::publish": ("pin", "test_sdk3_outcome_reach::TestAnUnknownPublishNeverReleasesItsVersion"),
    "index/indexer.py::_index_chunks": (
        "pin",
        "test_sdk3_outcome_reach::TestAnUnknownIndexCommitIsNotServedAsFailed",
    ),
    "index/indexer.py::_commit_batch_file": (
        "pin",
        "test_sdk3_outcome_reach::TestAnUnknownIndexCommitIsNotServedAsFailed",
    ),
    "index/indexer.py::_resolve_all_extension_edges": (
        "verdict",
        "label-only: the scope lands in IndexSummary.scopes_failed, which no served surface renders; the "
        "purge-then-RELATE re-runs idempotently on the next productive sweep, so no state is wrong",
    ),
    "briefs.py::_relate_briefed": (
        "verdict",
        "re-reads the edge it wrote: if the unknown write landed it reports already_acked (true state, "
        "imprecise label); nothing is released or rolled back",
    ),
    "briefs.py::_release_version": (
        "verdict",
        "log-only (brief.publish.version_not_released, possibly false); reached only on a DEFINITE "
        "rejection once publish shields the unknown outcome",
    ),
    "floor_calibration/store.py::_fence_verdict": (
        "verdict",
        "wraps a READ and re-raises the original error: nothing written, nothing re-labelled",
    ),
    "principals.py::_dispatch": (
        "verdict",
        "lore-adm prints the error's own message (an unknown error says so); no state decision",
    ),
    "store/lease.py::get": (
        "verdict",
        "a READ: reported as the library's non-404 'lock unavailable' — the election creates nothing this "
        "tick and re-reads next tick",
    ),
    "store/lease.py::create": (
        "verdict",
        "False = 'did not win this tick' to the election library, never served; if the create landed the "
        "next get() observes this identity as holder and renews — the safe direction (no second leader)",
    ),
    "store/lease.py::update": (
        "verdict",
        "as create: a landed renew is re-observed by the next get(); False only delays leadership",
    ),
    "store/lease.py::release_if_held": (
        "verdict",
        "False leaves the lease held until it expires (one lease_duration of stalled handoff) — the safe "
        "direction; never served",
    ),
    "tasks.py::_reject_unusable_blockers": (
        "verdict",
        "a READ pre-check: 'NOTHING was created' is true (the create never ran); retry is safe",
    ),
    "tasks.py::transitive_blockers": (
        "verdict",
        "a READ: serves no answer and says retry — honest for an unknown read",
    ),
}


def _names_the_store_error_family_only(site: CatchSite) -> bool:
    """A caught class in the ``SurrealStoreError`` family ABOVE the transport error (D1 owns those)."""
    return any(
        isinstance(cls, type)
        and issubclass(cls, _txn.SurrealStoreError)
        and not issubclass(cls, SurrealConnectionError)
        for cls in site.caught
    )


def _family_sites_an_unknown_outcome_reaches() -> list[CatchSite]:
    unknown = _unknown_type()
    return [
        site
        for site in production_catch_sites()
        if _names_the_store_error_family_only(site)
        and not _names_the_transport_error(site)
        and any(issubclass(unknown, cls) for cls in site.caught)
        and not any(issubclass(unknown, cls) for cls in site.earlier)
    ]


class TestEveryStoreErrorFamilyCatchSiteIsAdjudicated:
    """R12 F18, the reach half: the SET is derived by THE ONE walker (as D1's), never hand-listed — every
    production catch site whose caught classes include a ``SurrealStoreError``-family class that
    ``SurrealOutcomeUnknownError`` subclasses (and no earlier clause of its ``try`` catches it first). Each is
    adjudicated: a behaviour pin, or a one-line verdict. A new family site with no row is RED; a verdict row
    whose site is gone is RED. (R14, operator "B", 2026-11-07: round 5's clause that each "pin" row names
    an existing test class — a test about tests — was REMOVED in round 6; the walker-derived reach checks
    stay.)"""

    def test_the_family_derivation_is_not_vacuous(self) -> None:
        sites = _family_sites_an_unknown_outcome_reaches()
        verdicts = [key for key, (kind, _why) in _FAMILY_ADJUDICATION.items() if kind == "verdict"]
        assert len(sites) >= len(verdicts), (
            f"the derived family set holds {len(sites)} sites ({[site.key for site in sites]}) — fewer than "
            f"the "
            f"{len(verdicts)} verdict rows: the walker or the class resolution is broken"
        )

    def test_every_family_site_is_adjudicated_and_no_verdict_is_stale(self) -> None:
        derived = {site.key for site in _family_sites_an_unknown_outcome_reaches()}
        unadjudicated = sorted(derived - set(_FAMILY_ADJUDICATION))
        assert not unadjudicated, (
            f"SurrealStoreError-family catch sites an outcome-unknown error reaches, with no adjudication "
            f"(R12 F18): {unadjudicated}. Pin the site's rendering by behaviour (test_sdk3_outcome_reach), "
            f"or "
            f"give it a verdict row naming why it serves nothing an agent could act on wrongly."
        )
        stale = sorted(
            key
            for key, (kind, _why) in _FAMILY_ADJUDICATION.items()
            if kind == "verdict" and key not in derived
        )
        assert not stale, f"verdict rows whose site no longer exists in the derived set: {stale}"


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
        # SDK3 contract round 7, Q6 (R19): this surface is a WRITE (resolve/acknowledge), so its advice is the
        # write half — verify — and never the read half's "safe to re-run" (re-applying a landed write).
        assert "safe to re-run" not in lowered, (
            f"a WRITE whose outcome is unknown is served as {second!r}: 'safe to re-run' is READ advice (Q6)"
        )
        assert "outcome unknown" in lowered and "verify" in lowered, (
            f"the item whose call raised SurrealOutcomeUnknownError is served as {second!r}; it must name "
            f"the "
            f"outcome as unknown and tell the agent to verify before retrying"
        )
        assert any(line.startswith(f"- #{findings[0].number} ") and "FAILED" not in line for line in lines), (
            f"item 1 (applied before the fault) is not served as applied: {rendered!r}"
        )


class TestTheUnknownOutcomeAdviceSplitsByShape:
    """SDK3 contract round 7 — R19 Q6: D1's served advice splits by shape — "a write may have landed: verify
    before retrying / a read is safe to re-run". The seam cannot tell a read from a write (F14), and no
    read-serving catch site renders its own line (``_ADJUDICATED_RENDERING_SITES``), so a read tool serves the
    seam's own ``SurrealOutcomeUnknownError`` text: that text must carry BOTH halves, and the write renderer
    (``TestTheBatchVerbNeverServesAnUnknownOutcomeAsAborted``) serves the write half only. Store-free: a
    connection whose SELECT never got its reply (the SDK's ``TransportTimeoutError``). RED at ``0d9b8c2``:
    SDK 2.0 has no transport class and HEAD no unknown fate."""

    async def test_a_read_whose_reply_never_came_tells_the_agent_it_is_safe_to_re_run(self) -> None:
        import logging  # noqa: PLC0415 - kept local: this class is the file's only logger user

        from surrealdb import errors as sdk_errors  # noqa: PLC0415 - SDK-3-only class; a module import
        # would fail the whole file's collection on SDK 2.0 instead of this one pin.

        unknown_type = getattr(_txn, "SurrealOutcomeUnknownError", None)
        assert unknown_type is not None, "store._txn.SurrealOutcomeUnknownError (F14's fate) does not exist"
        timeout_type = sdk_errors.TransportTimeoutError

        class _NoReply:
            async def query(self, *_args: Any, **_kwargs: Any) -> Any:
                raise timeout_type("no reply within the request timeout")

        connection = _NoReply()

        async def _acquire() -> Any:
            return connection

        async def _drop(_dead: Any) -> None:
            return None

        with pytest.raises(unknown_type) as caught:
            await _txn.run_query(
                acquire=_acquire,
                drop=_drop,
                url="ws://sdk3-r7-q6",
                noun="search read",
                label="sdk3.r7.q6.read",
                statement="SELECT * FROM chunk LIMIT 1",
                logger=logging.getLogger("sdk3.r7.q6"),
            )
        served = str(caught.value).lower()
        assert "outcome unknown" in served and "re-run" in served and "verify" in served, (
            f"a read whose reply never came is served as {caught.value!s}: the seam's unknown-outcome text "
            f"must name the outcome AND carry both halves of Q6's advice — a write may have landed (verify "
            f"before retrying), a read is safe to re-run — because the seam cannot tell which this was"
        )
