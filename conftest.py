"""Repo-wide test guard: no lore test may reach the PRODUCTION SurrealDB store.

THE RULE
--------
"Never point tests at :18500" (repo ``CLAUDE.md`` §Deploy; operator ruling 2026-10-31, packet #165,
``docs/plans/v2/receipts/2026-10-31-165/RULING-guard-forks.md``). This conftest sits at the repo root
because no workspace member carries its own pytest configuration: the root ``pyproject.toml`` is the
rootdir and configfile for every suite, so this file loads for loremaster, lorescribe, loresigil,
lorerunes, ``scripts``, ``docs/eval`` and both ``skills/lore-deploy`` trees alike, in every xdist worker.

HOW
---
1. At import, :class:`ProductionStoreGuard` wraps ``socket.socket.connect`` and
   ``socket.socket.connect_ex``. A connection on :data:`PRODUCTION_STORE_PORT` whose destination reaches
   loopback never leaves the process: ``connect`` raises :class:`ConnectionRefusedError` and
   ``connect_ex`` returns ``ECONNREFUSED``, exactly as if nothing listened there. A destination reaches
   loopback when it is a loopback address or ``localhost`` (the shared predicate
   ``lorerunes.posture.host_is_loopback``), the unspecified address (``0.0.0.0`` / ``::``, which Linux
   reroutes to loopback on connect), or a name that resolves to either (``localhost.localdomain`` via
   ``/etc/hosts``). Every other address passes through untouched. ``urllib``,
   ``socket.create_connection``, ``ssl``, asyncio and websockets all reach the socket through
   ``connect``, so one layer covers them.
2. Every refused attempt is RECORDED. Each report pytest makes (a collector's collect report; a
   test's setup, call and teardown reports) drains the record, and a non-empty drain turns that report
   into a failure naming the node and every attempt. So the test fails even when the code under test
   swallows the refusal: ``lore_deploy._probe_surreal_health`` catches every ``OSError``, and
   ``connect_ex`` never raises at all. Draining per report, rather than clearing at test setup, keeps
   an attempt made in a module- or session-scoped fixture: it is charged to the test whose setup or
   teardown ran that fixture, not discarded.

THREAT MODEL
------------
This catches the HONEST developer whose test or fixture defaults to the production URL. The #165 T8
fake did exactly that: the skill's scaffold writes ``ws://127.0.0.1:18500/rpc`` into every new
``lore.yaml``, so a fake that falls back to the scaffold's value dials production. It is NOT a security
boundary: anyone who can commit here can already ship anything.

KNOWN BOUNDS (each with its re-open trigger)
--------------------------------------------
* Subprocess and C-extension clients (``curl``, ``podman exec … surreal``, a C library opening its own
  socket) never call Python's ``socket.socket`` and are invisible to this guard. Re-open trigger: a
  test that shells out to a store client, or a C-extension store driver.
* Loopback destinations only (above). Production listens on ``127.0.0.1:18500`` only (measured:
  lore-surreal runs ``Network=host``), so a LAN address of this host on :18500 reaches nothing and
  passes. Re-open trigger: production binds a non-loopback address.
* An attempt is charged to the report pytest makes NEXT, so it names the WINDOW it happened in, not
  its author: a background thread a test started, or another plugin's hook between reports, is charged
  to whichever node reports after it. The failure text says "made while", never "attempted by".
* An attempt made after the last report is still REFUSED, so production is never reached, but it is
  charged to nothing and the run does not fail. That covers a plugin's ``pytest_sessionfinish`` or
  ``pytest_unconfigure``, an ``atexit`` handler, and a thread that outlives the session. It is not
  closed: there is no report to fail, and a session-level exit code does not cover xdist, because
  ``xdist.dsession.DSession.worker_workerfinished`` reads a worker's exit status only to detect a
  keyboard interrupt (``== 2``), so a worker's late attempt could not reach the controller's verdict.
  Every in-test shape the threat model names (a test, a fixture of any scope, a module import) reports
  before the session ends. Re-open trigger: a lore plugin, ``atexit`` hook or session-outliving thread
  that talks to a SurrealDB store.
"""

from __future__ import annotations

import errno
import importlib.util
import ipaddress
import socket
import sys
import threading
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from lorerunes.posture import host_is_loopback

# The PRODUCTION lore-surreal store's port. Source of truth: the URL the skill scaffolds into every new
# ``lore.yaml``, ``_scaffold_lore_yaml`` in ``skills/lore-deploy/scripts/lore_deploy.py``
# (``url: ws://127.0.0.1:18500/rpc``). Production code must not import a conftest, so this constant
# cites the scaffold rather than being read by it (ruling: RULING-guard-forks.md, "Port literal").
PRODUCTION_STORE_PORT = 18500

# Index of the port in an AF_INET ``(host, port)`` / AF_INET6 ``(host, port, flowinfo, scope_id)`` tuple.
_ADDRESS_HOST_INDEX = 0
_ADDRESS_PORT_INDEX = 1

# What ``connect_ex`` reports for a refused attempt: the errno a closed port answers with.
REFUSED_ERRNO = errno.ECONNREFUSED

# Labels that name which socket door an attempt came through, in the failure text.
_CONNECT_DOOR = "socket.connect"
_CONNECT_EX_DOOR = "socket.connect_ex"

# How a report with no node id (the session's own collect report) is named in the failure text.
_SESSION_NODE_LABEL = "the pytest session (outside any test)"


def _reaches_loopback(host: str) -> bool:
    """Say whether connecting to the literal ``host`` lands on this machine's loopback interface.

    Args:
        host: A destination host: an IP literal or a hostname, as handed to ``connect``.

    Returns:
        ``True`` for ``localhost`` (any case) or a loopback IP, decided by the shared
        ``lorerunes.posture.host_is_loopback``, and for the unspecified address (``0.0.0.0`` / ``::``).
        ``False`` for any other literal and for every other hostname (resolution is the caller's job).
    """
    # The resolver ignores case (``LOCALHOST`` resolves like ``localhost``), and a guard must fail toward
    # refusing, so the shared predicate, which compares case-sensitively for bind hosts, sees it lowered.
    if host_is_loopback(host.lower()):
        return True
    try:
        # Linux reroutes a connect to the unspecified address to loopback (probed: ``0.0.0.0`` reaches a
        # listener on ``127.0.0.1``, ``::`` one on ``::1``). As a BIND host it is not loopback, which is
        # why this case lives here and not in the shared bind-host predicate.
        return ipaddress.ip_address(host).is_unspecified
    except ValueError:
        return False


def _host_text(host: object) -> str | None:
    """Return the host of an inet address as text, or ``None`` when it cannot name one.

    Args:
        host: The first element of the address tuple handed to ``connect``.

    Returns:
        The host as ``str``. ``connect`` also accepts an ASCII ``bytes``/``bytearray`` host
        (``(b"127.0.0.1", port)`` connects), so that is decoded. ``None`` for anything else.
    """
    if isinstance(host, str):
        return host
    if isinstance(host, bytes | bytearray):
        try:
            return host.decode("ascii")
        except UnicodeDecodeError:
            # Not ASCII: the real connect rejects it too, so it reaches nothing.
            return None
    return None


def _resolves_to_loopback(host: str, port: int) -> bool:
    """Say whether a hostname resolves to an address that reaches loopback.

    A raw ``connect(("<name>", port))`` resolves the name inside the C call, after the guard has
    looked at it. So an alias such as ``localhost.localdomain`` (``/etc/hosts``) is resolved here. Only
    production-port connections get this far, so nothing else pays for the lookup.

    Args:
        host: A host that is not itself a loopback or unspecified literal.
        port: The port being connected to, passed to the resolver as ``connect`` would.

    Returns:
        ``True`` when any resolved address reaches loopback; ``False`` when none does, or the name does
        not resolve.
    """
    try:
        resolved = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except (OSError, ValueError):
        # Unresolvable (or unencodable): the real connect fails the same way and reaches nothing.
        return False
    return any(_reaches_loopback(str(sockaddr[_ADDRESS_HOST_INDEX])) for *_, sockaddr in resolved)


class ProductionStoreGuard:
    """Refuse and record every connection this process makes to the production store.

    One instance per test process (see :data:`PRODUCTION_STORE_GUARD`). The socket side
    (:meth:`install`) refuses and records; the pytest side (:meth:`charge`) turns a report into a failure
    when attempts were recorded since the previous report.
    """

    def __init__(self, production_port: int) -> None:
        """Remember the port to refuse and the socket methods this guard wraps.

        Args:
            production_port: The production store's port; connections to it on loopback are refused.
        """
        self._production_port = production_port
        self._attempts: list[str] = []
        # Background threads (a server a test started, an asyncio loop thread) may connect while the
        # main thread drains, so the record is locked.
        self._lock = threading.Lock()
        self._real_connect = socket.socket.connect
        self._real_connect_ex = socket.socket.connect_ex

    def targets_production(self, address: object) -> bool:
        """Say whether a socket address is the production store: loopback host, production port.

        Args:
            address: The address handed to ``connect`` / ``connect_ex``; a UNIX path or any shape other
                than an inet tuple is never the production store.

        Returns:
            ``True`` when the address is on the production port and its host reaches loopback.
        """
        if not isinstance(address, tuple) or len(address) <= _ADDRESS_PORT_INDEX:
            return False
        port = address[_ADDRESS_PORT_INDEX]
        host = _host_text(address[_ADDRESS_HOST_INDEX])
        if port != self._production_port or host is None:
            return False
        return _reaches_loopback(host) or _resolves_to_loopback(host, port)

    def _record(self, door: str, address: object) -> str:
        """Record one refused attempt and return the refusal's text.

        Args:
            door: Which socket method the attempt came through.
            address: The address it tried to reach.

        Returns:
            The text the refusal carries, naming the address and the production port.
        """
        with self._lock:
            self._attempts.append(f"{door} {address!r}")
        return (
            f"production-store guard refused {door} to {address!r}: port {self._production_port} is the "
            f"PRODUCTION lore-surreal store, and tests must never reach it (CLAUDE.md §Deploy)"
        )

    def drain(self) -> list[str]:
        """Return every attempt recorded since the last drain, and forget them.

        Returns:
            The recorded attempts, oldest first; empty when none were made.
        """
        with self._lock:
            attempts, self._attempts = self._attempts, []
        return attempts

    def install(self) -> None:
        """Wrap ``socket.socket.connect`` and ``connect_ex`` so production attempts are refused."""
        guard = self

        # ``sock`` is ``Any``: the wrapped method lives on ``socket.socket`` but typeshed types it on the
        # private C base, so any narrower annotation is a false variance error.
        def guarded_connect(sock: Any, address: Any) -> None:
            """``socket.socket.connect``, refusing (and recording) the production store."""
            if guard.targets_production(address):
                raise ConnectionRefusedError(REFUSED_ERRNO, guard._record(_CONNECT_DOOR, address))
            guard._real_connect(sock, address)

        def guarded_connect_ex(sock: Any, address: Any) -> int:
            """``socket.socket.connect_ex``, refusing (and recording) the production store."""
            if guard.targets_production(address):
                guard._record(_CONNECT_EX_DOOR, address)
                return REFUSED_ERRNO
            return guard._real_connect_ex(sock, address)

        socket.socket.connect = guarded_connect  # type: ignore[method-assign]
        socket.socket.connect_ex = guarded_connect_ex  # type: ignore[method-assign]

    def charge(self, report: pytest.CollectReport | pytest.TestReport) -> None:
        """Fail ``report`` if production was attempted since the previous report; else leave it alone.

        A report that would have passed or been skipped (``xfail`` included) becomes a failure: an
        attempt on production is never an expected outcome. A report that already failed keeps its own
        text, with the guard's appended, so the failure always names the port.

        Args:
            report: The report pytest just made for the phase in which the attempts happened.
        """
        attempts = self.drain()
        if not attempts:
            return
        node = report.nodeid or _SESSION_NODE_LABEL
        # "made while", not "attempted by": the guard knows the report window, not which code dialled.
        verdict = (
            f"{len(attempts)} attempt(s) on the PRODUCTION SurrealDB store (loopback port "
            f"{self._production_port}) were made while {node} ran its {report.when} phase; each was "
            f"refused before it left the process, but tests must never point at "
            f":{self._production_port} (CLAUDE.md §Deploy). Attempts: {'; '.join(attempts)}"
        )
        if report.failed:
            report.longrepr = f"{report.longrepr}\n\n{verdict}"
            return
        report.outcome = "failed"
        report.longrepr = verdict
        # The skipping plugin marks an xfailed test with ``wasxfail``; left in place, junit would
        # file this failure as an xfail.
        report.__dict__.pop("wasxfail", None)


PRODUCTION_STORE_GUARD = ProductionStoreGuard(PRODUCTION_STORE_PORT)
PRODUCTION_STORE_GUARD.install()


@pytest.hookimpl(wrapper=True)
def pytest_make_collect_report(
    collector: pytest.Collector,
) -> Generator[None, pytest.CollectReport, pytest.CollectReport]:
    """Charge an attempt made while collecting (e.g. at a test module's import) to that collector."""
    report = yield
    PRODUCTION_STORE_GUARD.charge(report)
    return report


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    """Charge an attempt made during a test's setup, call or teardown to that phase of that test."""
    report = yield
    PRODUCTION_STORE_GUARD.charge(report)
    return report


# --- parked contract reds (lead task 7f68cbcf; docs/design/2026-11-09-parked-contracts-rulings.md) ---
# The hook lives in ``scripts/_parked_contracts.py`` (it reads the gate's registry model). ``scripts/`` is not
# a package and the sandbox tests import this file by path, so the module is loaded by path too.
_PARKED_CONTRACTS_MODULE_NAME = "_parked_contracts"
_PARKED_CONTRACTS_PATH = Path(__file__).resolve().parent / "scripts" / "_parked_contracts.py"


def _load_parked_contracts() -> Any:
    """Load (once) the parked-contracts module from this repo's ``scripts/``."""
    module = sys.modules.get(_PARKED_CONTRACTS_MODULE_NAME)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(_PARKED_CONTRACTS_MODULE_NAME, _PARKED_CONTRACTS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[_PARKED_CONTRACTS_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register ``--run-parked``: run the contract reds parked in ``scripts/pending_contracts.yaml``."""
    _load_parked_contracts().add_run_parked_option(parser)


def pytest_configure(config: pytest.Config) -> None:
    """Register the parked-deselection plugin (``-p no:lore-parked-contracts`` disables it)."""
    _load_parked_contracts().register_plugin(config)
