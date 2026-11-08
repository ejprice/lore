"""Packet SDK3 — the FORK S retirement pin: every connection owner's close completes over a severed socket.

Ruling: sidecar RULING-13 §FORK S, adopted as R41 (``docs/plans/v2/sdk3-rulings.md``); drop-list row #16. The
18 per-owner ``_safe_close`` wrappers (try ``close()`` / swallow ``_CONNECTION_ERRORS`` / debug log) were
retired at ``6b43b65``: SDK 3.0.0's ``close()`` is designed not to raise (idempotent, cross-loop safe, it
cancels its own reconnect and renewal tasks before ``_teardown``) and was measured not to raise over a
severed socket (40/40, both sever modes). R1's rider: a retirement pin that goes RED the day that stops
being true. Every owner's close now calls the SDK's ``close()`` with nothing in between, so an SDK
regression that makes ``close()`` raise on a dead socket propagates out of the owner's close — and every
leg below reddens, at upgrade time, instead of a crash in production.

THE PIN, per owner x sever mode (:class:`_sdk3_proxy.SeverMode` ``ABORT`` and ``CLOSE_FRAME``):

1. the owner (and any owner it composes, see X18 below) serves one call through
   :class:`_sdk3_proxy.StoreBounceProxy`, so it holds a live socket THROUGH the proxy;
2. PREMISE / positive control: ``go_down(mode)`` reports at least one severed socket per held connection,
   and every held SDK connection reports ``is_connected == False`` (the SDK itself observed the sever —
   the close below really runs over a dead socket, never a live one);
3. the owner's close completes inside a bounded wait (``asyncio.wait_for``) and raises nothing out;
4. every held connection then reports ``status == "disconnected"`` (the close reached the SDK's own
   teardown, not an early return that left a reconnect running).

THE OWNER SET is ``test_retry_seam._discover_bootstrap_owners`` — IMPORTED from its one home (through
``test_sdk3_lifecycle._owner_classes``, which resolves it to classes), never copied. It is the existing
derivation RULING-13 names ("the owner set is the one L1/L6 already derive") and that
``test_sdk3_lifecycle`` already quantifies over; consuming it adds no new scanner, so operator ruling R38
(no NEW standing source scanner) does not apply (lead ruling, 2026-11-08, FORK OWNERSET option A). A new
owner joins at collection; a control asserts the set is not silently small. The connection factory itself
records no owners (measured at ``d7c880d``), so there is no runtime registry to read.

``scout.CommandSubscriber`` HAS NO ``close()``. Owners without one are checked by their DROP PATH instead
(``_drop_connection()``, which since ``6b43b65`` calls the SDK's ``close()`` directly too): it completes
over a severed socket, raises nothing, leaves the owner holding no connection, and the dropped handle
reports ``disconnected``. The family is derived (``close`` absent on the class), so the day scout gains a
``close()`` it moves to the close family by itself and the drop-path family goes empty — RE-OPEN TRIGGER:
"scout gains a close()" (then delete the drop-path class, or keep it if another close-less owner exists).

X18 (``KeepStore`` / ``PrincipalKeyStore`` also close their composed ``PrincipalStore``): the composed
owner is found at RUNTIME (an attribute of the live owner that is itself an instance of a derived owner
class), warmed through the proxy too, severed with the outer one, and its handle must also end
``disconnected`` — so the nested close runs over a dead socket as well. BOUND: its discrimination under
the mutation is carried by ``PrincipalStore``'s OWN leg (the outer close raises first, before the nested
one runs).

MUTATION RECEIPT (the pin is GREEN on both the wrapper build and the retirement build; its discrimination
lives entirely in the mutation, which is the correct shape for a retirement, RULING-13): the SDK's
``AsyncWsSurrealConnection.close`` made to raise ``ConnectionUnavailableError`` whenever the connection is
not ``connected`` (the regression: "close over a severed socket raises") reddens EVERY leg in both
families. Conditioning on the severed state keeps the harness's own healthy admin closes unaffected, so
the reds are the owners' closes, never a fixture error. Run by ``scripts/mutation_proof.py`` on a scratch
copy, declared set from ``--collect-only``; receipt in the R41 inventory row.

BOUNDS, stated: owners are reached only as ``_construct_live_owner`` builds them (required constructor
args, no ``ensure_ready``); the close is exercised on a connection that has OBSERVED its sever (a close
racing the sever's detection, and a close during an in-progress reconnect attempt that has a half-open
socket, are not separately constructed); the proxy cannot model a peer that vanished without FIN/RST
(its own docstring).
"""

from __future__ import annotations

import asyncio
import dataclasses
import logging
from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
from _sdk3_proxy import SeverMode, StoreBounceProxy
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    unique_database,
)
from test_retry_seam import _MIN_KNOWN_BOOTSTRAP_OWNERS
from test_sdk3_lifecycle import _construct_live_owner, _owner_classes, _probe_call, _settled

logger = logging.getLogger(__name__)

# How long an owner's close (or drop) may take over a severed socket before it counts as a hang. SDK 3.0.0's
# close cancels its tasks and tears the socket down without a network round trip; measured well under 1 s.
_CLOSE_BOUND_SECONDS = 5.0

# How long the premise waits for the SDK to observe the sever (its reader sees EOF / the close frame).
_SEVER_OBSERVED_BOUND_SECONDS = 3.0

# The SDK's own name for a connection whose teardown finished (``ConnectionStatus``).
_DISCONNECTED_STATUS = "disconnected"

_SEVER_MODES = [SeverMode.ABORT, SeverMode.CLOSE_FRAME]


# ``test_sdk3_lifecycle._owner_classes`` is ``_discover_bootstrap_owners()`` resolved to classes.
_OWNER_CLASSES = _owner_classes()
_OWNER_TYPES = tuple(owner_class for _, owner_class in _OWNER_CLASSES)


def _has_close(owner_class: type) -> bool:
    """Whether the owner exposes a public ``close()`` (else it is checked by its drop path)."""
    return callable(getattr(owner_class, "close", None))


_CLOSE_OWNERS = [pytest.param(cls, id=name) for name, cls in _OWNER_CLASSES if _has_close(cls)]
_DROP_PATH_OWNERS = [pytest.param(cls, id=name) for name, cls in _OWNER_CLASSES if not _has_close(cls)]


@pytest_asyncio.fixture()
async def store_env() -> AsyncIterator[SurrealEnv]:
    """A fresh database on the TEST store, created DIRECTLY (not through the proxy)."""
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup_connection = await connect_admin(env)
    await setup_connection.close()
    try:
        yield env
    finally:
        await drop_database(env)


@pytest_asyncio.fixture()
async def proxy(store_env: SurrealEnv) -> AsyncIterator[StoreBounceProxy]:
    """A started proxy in front of the TEST store; closed (every socket severed) at teardown."""
    bounce_proxy = StoreBounceProxy(upstream_url=store_env.url)
    await bounce_proxy.start()
    try:
        yield bounce_proxy
    finally:
        await bounce_proxy.close()


@pytest.fixture()
def proxied_env(store_env: SurrealEnv, proxy: StoreBounceProxy) -> SurrealEnv:
    """``store_env`` with its URL pointed through the proxy."""
    return dataclasses.replace(store_env, url=proxy.url)


def _composed_owners(owner: Any) -> list[Any]:
    """The live owners ``owner`` composes (X18), found at runtime among its attributes."""
    return [value for value in vars(owner).values() if isinstance(value, _OWNER_TYPES) and value is not owner]


async def _warm_and_sever(owner: Any, proxy: StoreBounceProxy, mode: SeverMode) -> list[Any]:
    """Make ``owner`` (and what it composes) hold live sockets through the proxy, then sever them.

    Returns every SDK connection handle the owners held, after proving the premise: the proxy cut at
    least one socket per handle, and the SDK itself reports each handle no longer connected.
    """
    holders = [owner, *_composed_owners(owner)]
    for holder in holders:
        await _probe_call(holder, proxy.url)
    held = [getattr(holder, "_connection", None) for holder in holders]
    missing = [type(holder).__name__ for holder, handle in zip(holders, held, strict=True) if handle is None]
    assert not missing, (
        f"premise: after a served call these owners hold no ``_connection`` handle: {missing} — the pin "
        f"cannot show the close ran over THEIR severed socket"
    )
    handles = [handle for handle in held if handle is not None]
    assert proxy.live_pipes >= len(handles), (
        f"premise: {len(handles)} connection(s) must hold a socket THROUGH the proxy (saw {proxy.live_pipes})"
    )

    severed = await proxy.go_down(mode)
    assert severed >= len(handles), (
        f"premise (positive control): go_down({mode.value}) severed {severed} socket(s); "
        f"{len(handles)} were held"
    )
    observed = await _settled(
        lambda: not any(handle.is_connected for handle in handles), timeout=_SEVER_OBSERVED_BOUND_SECONDS
    )
    assert observed, (
        f"premise: {_SEVER_OBSERVED_BOUND_SECONDS}s after the sever the SDK still reports connected for "
        f"{[str(handle.status) for handle in handles]} — the close below would run over a LIVE socket"
    )
    return handles


async def _close_quietly(owner: Any) -> None:
    """Teardown only: release whatever a failed leg left open (a failed close IS the leg's finding)."""
    try:
        close = getattr(owner, "close", None)
        if close is not None:
            await asyncio.wait_for(close(), _CLOSE_BOUND_SECONDS)
        else:
            await asyncio.wait_for(owner._drop_connection(), _CLOSE_BOUND_SECONDS)
    except Exception:  # noqa: BLE001 - teardown must not mask the leg's own verdict
        logger.debug("sdk3.close_pin.teardown_close_failed", exc_info=True)


def _assert_torn_down(handles: list[Any], what: str) -> None:
    """Every handle reached the SDK's own teardown (no reconnect left running behind the owner)."""
    statuses = [str(handle.status) for handle in handles]
    assert all(status == _DISCONNECTED_STATUS for status in statuses), (
        f"{what} returned, but the SDK connection(s) report {statuses}, not {_DISCONNECTED_STATUS!r} — the "
        f"close did not reach the SDK's teardown"
    )


class TestTheOwnerSetIsNotSilentlySmall:
    """The reach control for both ∀-owner families below: an empty or shrunken set would make them
    vacuously green, and an owner in neither family would be silently exempt."""

    def test_the_derived_owner_set_is_at_least_the_known_floor(self) -> None:
        assert len(_OWNER_CLASSES) >= _MIN_KNOWN_BOOTSTRAP_OWNERS, (
            f"the derived owner set holds only {len(_OWNER_CLASSES)} classes "
            f"({[name for name, _ in _OWNER_CLASSES]}); test_retry_seam's floor is "
            f"{_MIN_KNOWN_BOOTSTRAP_OWNERS}"
        )

    def test_every_derived_owner_is_in_exactly_one_family(self) -> None:
        assert len(_CLOSE_OWNERS) + len(_DROP_PATH_OWNERS) == len(_OWNER_CLASSES), (
            "an owner fell outside both the close family and the drop-path family"
        )
        assert _CLOSE_OWNERS, "no derived owner has a close() — the close family would pin nothing"

    def test_the_x18_composition_is_reached(self) -> None:
        """The X18 claim in the module docstring is a REACH claim; this checks it is not vacuous.

        Owners are constructed offline (no constructor connects) and their composed owners collected
        exactly as the legs collect them. If the composition was removed deliberately, delete this
        control and the X18 paragraph together.
        """
        offline_env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        composing = {
            name: [
                type(inner).__name__ for inner in _composed_owners(_construct_live_owner(cls, offline_env))
            ]
            for name, cls in _OWNER_CLASSES
        }
        composing = {name: inner for name, inner in composing.items() if inner}
        assert composing, (
            "no derived owner composes another at runtime, so no leg exercises a nested close (X18) — "
            "the module docstring's X18 claim would be vacuous"
        )


class TestEveryOwnersCloseCompletesOverASeveredSocket:
    """FORK S / R41: with the 18 ``_safe_close`` wrappers retired, the owner's close calls the SDK's
    ``close()`` directly. It must complete, bounded, raising nothing, over a socket the store dropped."""

    @pytest.mark.parametrize("mode", _SEVER_MODES, ids=lambda mode: mode.value)
    @pytest.mark.parametrize("owner_class", _CLOSE_OWNERS)
    async def test_close_completes_and_raises_nothing(
        self, owner_class: type, mode: SeverMode, proxy: StoreBounceProxy, proxied_env: SurrealEnv
    ) -> None:
        owner = _construct_live_owner(owner_class, proxied_env)
        try:
            handles = await _warm_and_sever(owner, proxy, mode)
            try:
                await asyncio.wait_for(owner.close(), _CLOSE_BOUND_SECONDS)
            except TimeoutError:
                pytest.fail(
                    f"{owner_class.__name__}.close() did not complete within {_CLOSE_BOUND_SECONDS}s over a "
                    f"socket severed by {mode.value} — a close must never park a shutdown"
                )
            except Exception as error:  # noqa: BLE001 - the raise IS the finding
                pytest.fail(
                    f"{owner_class.__name__}.close() RAISED over a socket severed by {mode.value}: "
                    f"{type(error).__name__}: {error}. Its per-owner _safe_close guard was retired (R41, "
                    f"drop-list #16) because SDK 3.0.0's close() does not raise here — this SDK does."
                )
            _assert_torn_down(handles, f"{owner_class.__name__}.close()")
        finally:
            await _close_quietly(owner)


class TestAnOwnerWithoutCloseDropsCleanlyOverASeveredSocket:
    """``scout.CommandSubscriber`` has no ``close()``; it is checked by its DROP PATH, which since
    ``6b43b65`` calls the SDK's ``close()`` directly. After the sever, the drop completes, raises nothing,
    and the subscriber holds no connection. RE-OPEN TRIGGER: "scout gains a close()" (module docstring)."""

    @pytest.mark.parametrize("mode", _SEVER_MODES, ids=lambda mode: mode.value)
    @pytest.mark.parametrize("owner_class", _DROP_PATH_OWNERS)
    async def test_drop_completes_raises_nothing_and_holds_no_connection(
        self, owner_class: type, mode: SeverMode, proxy: StoreBounceProxy, proxied_env: SurrealEnv
    ) -> None:
        owner = _construct_live_owner(owner_class, proxied_env)
        try:
            handles = await _warm_and_sever(owner, proxy, mode)
            try:
                await asyncio.wait_for(owner._drop_connection(), _CLOSE_BOUND_SECONDS)
            except TimeoutError:
                pytest.fail(
                    f"{owner_class.__name__}._drop_connection() did not complete within "
                    f"{_CLOSE_BOUND_SECONDS}s over a socket severed by {mode.value}"
                )
            except Exception as error:  # noqa: BLE001 - the raise IS the finding
                pytest.fail(
                    f"{owner_class.__name__}._drop_connection() RAISED over a socket severed by "
                    f"{mode.value}: {type(error).__name__}: {error}"
                )
            assert owner._connection is None, (
                f"{owner_class.__name__} still holds a connection after its drop path ran"
            )
            _assert_torn_down(handles, f"{owner_class.__name__}._drop_connection()")
        finally:
            await _close_quietly(owner)
