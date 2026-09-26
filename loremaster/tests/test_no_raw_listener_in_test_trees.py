"""Contract (finding #466, defect-class invariant) — no test tree opens a listener except through the ONE
helper, ``loremaster.testing.loopback``.

Session ``297217bd`` (lead-63c-2), tdd-light. Author: ``contract-466`` (TESTS ONLY).

THE CLASS THIS PINS
-------------------
#466's race lived in FOUR hand-rolled copies of one policy ("get a port for a throwaway server"), each
spelled ``bind(:0) → read port → close → hand the number to a server that binds it again``. Fixing the
four copies fixes #466 once; this pin keeps the fix: the fifth copy (a new stub server, a new wire
harness, a spike script beside the tests) reddens the day it lands, NAMED ``file:line (function)``.

THREAT MODEL — written down so the verdicts follow mechanically (CLAUDE.md, "A GATE NEEDS A THREAT
MODEL")
---------------------------------------------------------------------------------------------------
This gate catches the **HONEST DEVELOPER** who copies the ``_free_port`` idiom, stands up a stdlib
``HTTPServer`` stub, or starts a ``uvicorn`` harness directly. It is **NOT** a boundary against deliberate
evasion. So: *"an honest listener goes unnoticed"* is a defect; *"a contrived spelling gets through"* is
LEDGERED, not paid for in false positives — a gate that refuses honest code gets switched off.

WHAT COUNTS AS OPENING A LISTENER (receiver-blind where it can be)
-----------------------------------------------------------------
* **any ``.bind(address)``** — exactly one positional argument, no keywords: the socket-address shape,
  on ANY receiver (a fixture's socket, ``self._sock``, an aliased module). ``inspect.Signature.bind(None,
  **fields)`` / ``logger.bind(key=value)`` carry keywords and are spared.
* **any call into a listener namespace** — every callable reached through ``socketserver``,
  ``http.server``, ``uvicorn`` or ``wsgiref.simple_server``, however imported or aliased, plus
  ``socket.create_server``. Namespace-wide, not a list of three class names.
* **any asyncio listener verb** on any receiver — ``create_server`` / ``create_unix_server`` /
  ``start_server`` / ``start_unix_server`` (``loop.create_server``, ``asyncio.start_server``, …).

The SAFE set is small and enumerable, so it is the allowlist: the helper (which lives OUTSIDE every test
tree, in ``loremaster/loremaster/testing/``), plus :data:`_EXEMPT_SITES` — evidence-backed
``(file, function)`` pairs with a reason and a re-open trigger, each held live by a dead-entry pin.

REACH IS A CHECKED VARIABLE
---------------------------
The file set is DERIVED: every ``*.py`` under every ``[tool.pytest.ini_options] testpaths`` root (the
test trees pytest itself runs), read INDEPENDENTLY of the parser from ``pyproject.toml``. Trees come from
the ONE shared parser (``_logging_fixtures.parse_production_trees``, extended with
``include_testpaths=True`` so ``docs/eval`` is reached — today it is not). A testpaths root the parser
does not reach is RED, named; so is an empty scan; so is a tree that never adopted the helper.

KNOWN BOUND (pinned, :class:`TestKnownBoundLibraryInternalListeners`): a listener opened INSIDE a
dependency the test calls (``LoreServer(config).run()`` with nothing patched binds ``config.server.port``)
is invisible to any AST scan of our source. Re-open trigger: the first measured occurrence, at which
point the answer is a runtime tripwire on ``socket.socket.bind`` (the CLAUDE.md RUNTIME rung), not a
longer name list.

⚠ Present-tense dating: the RED set named in each docstring is dated to HEAD ``1206233``. After the
helper lands and the three test files + the spike are migrated, the offender set is EMPTY — the pin
doing its job.

DELTA d1 (author ``contract-466-d1``; REPORT-refactor-466.md §2 C1/C3)
----------------------------------------------------------------------
* **C1** — ``_CONTRACT_FILES`` gets the dead-entry pin ``_EXEMPT_SITES`` already had: every entry must be a
  file the scan actually reads, or a rename silently lets the renamed contract file vouch for its tree.
* **C3** — aiohttp is INSTALLED and its listeners (``web.run_app`` / ``web.TCPSite`` / ``UnixSite`` /
  ``test_utils.TestServer``, and ``test_utils.unused_port`` — #466's own bind→close→number race, shipped
  inside a dependency) are honest-developer doors the namespace deny-list cannot see. Pinned by planted
  spellings with honest aiohttp CLIENT/handler look-alikes as the over-breadth control.
* **C3 reach** — the deny-list's blind spot is a hidden constant ("which server libraries exist"), so it
  is DERIVED: every installed distribution that a test tree IMPORTS and whose own source calls a
  listener verb is server-capable, and must carry a planted spelling the detector flags. The day a test
  first imports a new server library, this reddens and names it. Bound: see
  :class:`TestTheServerCapableDependenciesAreDerived`.

LEAD PIN (c) (author ``refactor-466-d1``, Phase 5 — a documented deviation from test-first: the ruling
post-dated the contract; proven able to fail by mutation, REPORT-refactor-466-d1.md §Pins-c)
------------------------------------------------------------------------------------------------------
* **A pytest-plugin port fixture is a listener door no call-keyed scan sees.** pytest-asyncio's
  ``unused_tcp_port`` / ``unused_udp_port`` (+ ``_factory``) and anyio's ``free_tcp_port`` /
  ``free_udp_port`` (+ ``_factory``) are #466's bind→close→number race, requested by NAME — a function
  parameter, ``request.getfixturevalue("…")`` or ``pytest.mark.usefixtures("…")``. The detector flags
  such a request. **Allowlist the safe:** the forbidden set is every fixture an installed ``pytest11``
  plugin DEFINES (derived by importing each entry point) MINUS :data:`_SAFE_PLUGIN_FIXTURES`, so a new
  plugin's fixture is refused until someone classifies it — never silently allowed.
"""

from __future__ import annotations

import ast
import functools
import inspect
import sysconfig
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

import pytest
from _logging_fixtures import _workspace_root, assert_scan_reached_every_member, parse_production_trees

# pytest exposes no public "is this object a fixture definition" predicate; this private one is what its own
# collector uses. Bound: a pytest release that moves it is an ImportError at collection — loud, not silent.
from _pytest.fixtures import getfixturemarker
from packaging.utils import canonicalize_name  # PEP 503 names; packaging is a hard dependency of pytest

# Every callable reached through these modules opens (or configures) a listener.
_LISTENER_NAMESPACES = ("socketserver", "http.server", "uvicorn", "wsgiref.simple_server")
# The one ``socket`` module function that binds (``socket.socket`` itself binds nothing until ``.bind``).
_LISTENER_FUNCTIONS = ("socket.create_server",)
# asyncio's and anyio's listener verbs — matched on ANY receiver (a loop, the module, an alias).
_LISTENER_METHODS = frozenset(
    {
        "create_server",
        "create_unix_server",
        "start_server",
        "start_unix_server",
        "create_tcp_listener",
        "create_unix_listener",
    }
)
# Libraries that are mostly CLIENTS, so a whole-namespace entry would refuse honest code: only these
# leaf names open a listener. Matched at ANY depth under the library, because aiohttp re-exports them
# (``aiohttp.web.TCPSite`` is defined as ``aiohttp.web_runner.TCPSite``) and either spelling is honest.
# ``unused_port`` is #466's own bind→read→close race, shipped inside aiohttp.
_LISTENER_NAMES_BY_LIBRARY: dict[str, frozenset[str]] = {
    "aiohttp": frozenset({"run_app", "TCPSite", "UnixSite", "TestServer", "unused_port"}),
}
# The helper's public names — an adoption is a CALL to one of these.
_HELPER_ENTRY_POINTS = frozenset({"LoopbackPort", "serve_asgi", "serve_http"})
# Files this contract itself adds; adoption must be observed OUTSIDE them (they cannot vouch for a tree).
_CONTRACT_FILES = frozenset(
    {
        "loremaster/tests/test_loopback_serving.py",
        "skills/lore-deploy/tests/test_loopback_home.py",
    }
)
# The two test trees #466's copies lived in — each must be SEEN adopting the helper.
_ADOPTING_TREES = ("loremaster/tests", "skills/lore-deploy/tests")
# A conservative floor far below the real count (314 *.py under testpaths at 1206233).
_TEST_TREE_FILE_FLOOR = 150

# d1/C3 reach — the INDEPENDENT oracle for "this dependency can open a listener": a call, anywhere in its
# own source, to one of these verbs (asyncio's four + anyio's two). Deliberately NOT the detector's
# ``_LISTENER_METHODS`` — deriving reach from the thing whose reach it checks would be derived == derived.
_DEPENDENCY_LISTENER_VERBS = frozenset(
    {
        "create_server",
        "create_unix_server",
        "start_server",
        "start_unix_server",
        "create_tcp_listener",
        "create_unix_listener",
    }
)
# d1/C3 reach — every server-capable distribution a test tree imports → an honest listener spelling of
# it that the detector MUST flag. Keys are canonical distribution names (PEP 503). The derived set must
# EQUAL these keys: a missing key is a server library the guard has never been shown; an extra key is a
# dead entry. Derived at 43b8d16: {anyio, uvicorn} (d1 report §C3, measured).
_PLANTED_BY_SERVER_DISTRIBUTION: dict[str, str] = {
    "uvicorn": "import uvicorn\ndef serve(app, port):\n    uvicorn.run(app, host='127.0.0.1', port=port)\n",
    "anyio": (
        "import anyio\n"
        "async def serve(port):\n"
        "    await anyio.create_tcp_listener(local_host='127.0.0.1', local_port=port)\n"
    ),
}

# Lead pin (c): the pytest-plugin fixtures that are SAFE to request (they open nothing and hand out no port),
# each with its reason. EVERY OTHER fixture an installed pytest11 plugin defines is forbidden in the test
# trees — the forbidden set is derived (:func:`_forbidden_plugin_fixtures`), never listed. Classified by
# reading the installed sources (pytest-asyncio 1.4.0, anyio 4.13.0, pytest-xdist 3.8.0), 2026-09-26.
_SAFE_PLUGIN_FIXTURES: dict[str, str] = {
    "anyio_backend": "anyio: names the async backend to run on — opens nothing",
    "anyio_backend_name": "anyio: the backend's name — opens nothing",
    "anyio_backend_options": "anyio: the backend's options — opens nothing",
    "event_loop_policy": "pytest-asyncio: the event-loop policy — opens nothing",
    "_asyncio_loop_factory": "pytest-asyncio: private loop factory — opens nothing",
    "_function_scoped_runner": "pytest-asyncio: private per-scope asyncio runner — opens nothing",
    "_class_scoped_runner": "pytest-asyncio: private per-scope asyncio runner — opens nothing",
    "_module_scoped_runner": "pytest-asyncio: private per-scope asyncio runner — opens nothing",
    "_package_scoped_runner": "pytest-asyncio: private per-scope asyncio runner — opens nothing",
    "_session_scoped_runner": "pytest-asyncio: private per-scope asyncio runner — opens nothing",
    "worker_id": "pytest-xdist: this worker's id string — opens nothing",
    "testrun_uid": "pytest-xdist: the run's uid string — opens nothing",
}
# Lead pin (c): the fixtures the ruling NAMED — the derivation must reach them (non-vacuity). Not the
# forbidden set (that is derived); only proof the derivation sees the plugin the ruling was about.
_RULED_PORT_FIXTURES = frozenset(
    {"unused_tcp_port", "unused_tcp_port_factory", "unused_udp_port", "unused_udp_port_factory"}
)

# (repo-relative file, enclosing function qualname) → evidence-backed reason + re-open trigger.
_EXEMPT_SITES: dict[tuple[str, str], str] = {
    ("skills/lore-deploy/scripts/lore_deploy.py", "_free_port"): (
        "PRODUCTION deploy code that lives in a testpaths root, not a test: it picks the HOST port podman "
        "will publish (`-p <port>:…`), and podman — another process — must bind it, so it cannot hold "
        "the socket. It is the same close→rebind race in production and is surfaced in the #466 contract "
        "report as a separate finding. Re-open trigger: two `lore-deploy start` runs racing on one host."
    ),
    ("loremaster/tests/test_loopback_serving.py", "_attempt_raw_bind"): (
        "The helper's OWN contract must build a squatter socket to prove the port is HELD "
        "(EADDRINUSE while the LoopbackPort is open). Re-open trigger: never — this is the one place "
        "a raw bind is the instrument, not the defect."
    ),
}


@dataclass(frozen=True)
class ListenerSite:
    """One raw listener-opening call: where it is, which function holds it, and what it is."""

    path: str
    lineno: int
    function: str
    primitive: str

    def render(self) -> str:
        return f"{self.path}:{self.lineno} ({self.function}) — {self.primitive}"


def _import_aliases(tree: ast.Module) -> dict[str, str]:
    """Local name → the dotted module path it stands for, from every import in ``tree``.

    ``import http.server`` binds ``http``→``http``; ``import uvicorn as u`` binds ``u``→``uvicorn``;
    ``from http.server import HTTPServer as H`` binds ``H``→``http.server.HTTPServer``.
    """
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    aliases[alias.asname] = alias.name
                else:
                    head = alias.name.split(".", 1)[0]
                    aliases[head] = head
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return aliases


def _dotted(node: ast.expr) -> list[str] | None:
    """``a.b.c`` → ``["a", "b", "c"]``; ``None`` when the chain does not bottom out in a bare name."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return list(reversed(parts))


def _resolved_callee(call: ast.Call, aliases: dict[str, str]) -> str | None:
    """The call's callee as a fully-qualified dotted name, when its head is an imported name."""
    parts = _dotted(call.func)
    if not parts or parts[0] not in aliases:
        return None
    return ".".join([aliases[parts[0]], *parts[1:]])


def _is_in_namespace(qualified: str, namespace: str) -> bool:
    return qualified == namespace or qualified.startswith(f"{namespace}.")


def _listener_primitive(call: ast.Call, aliases: dict[str, str]) -> str | None:
    """Name the listener primitive ``call`` is, or ``None`` if it opens no listener."""
    func = call.func
    if (
        isinstance(func, ast.Attribute)
        and func.attr == "bind"
        and len(call.args) == 1
        and not isinstance(call.args[0], ast.Starred)
        and not call.keywords
    ):
        return f"{ast.unparse(func)}(<address>) — a raw socket bind"
    if isinstance(func, ast.Attribute) and func.attr in _LISTENER_METHODS:
        return f"{ast.unparse(func)}(…) — an asyncio/anyio listener"
    qualified = _resolved_callee(call, aliases)
    if qualified is None:
        return None
    if (
        qualified in _LISTENER_FUNCTIONS
        or any(_is_in_namespace(qualified, ns) for ns in _LISTENER_NAMESPACES)
        or _is_library_listener(qualified)
    ):
        return f"{qualified}(…) — a listener outside loremaster.testing.loopback"
    return None


def _is_library_listener(qualified: str) -> bool:
    """True iff ``qualified`` is one of :data:`_LISTENER_NAMES_BY_LIBRARY`'s listener leaves, reached
    through any submodule of its library."""
    leaf = qualified.rsplit(".", 1)[-1]
    return any(
        _is_in_namespace(qualified, library) and leaf in names
        for library, names in _LISTENER_NAMES_BY_LIBRARY.items()
    )


@functools.cache
def _installed_plugin_fixtures() -> dict[str, str]:
    """Fixture name → ``"<distribution>:<plugin module>"`` for every fixture an installed plugin defines.

    DERIVED from the ``pytest11`` entry points (how pytest itself discovers plugins), by loading each plugin
    and reading the fixture definitions in its namespace — independent of which plugins THIS invocation
    enabled (``-p no:xdist`` must not shrink the set). Bound: a plugin that registers fixtures on an object
    at ``pytest_configure`` time is not in a module namespace — the live-session leg
    (:meth:`TestPluginPortFixturesAreForbidden.test_the_running_session_registers_no_plugin_fixture_the_derivation_missed`)
    covers that door.
    """
    fixtures: dict[str, str] = {}
    for entry_point in metadata.entry_points(group="pytest11"):
        plugin = entry_point.load()
        distribution = entry_point.dist.name if entry_point.dist is not None else "?"
        for attribute, candidate in vars(plugin).items():
            marker = getfixturemarker(candidate)
            if marker is not None:
                fixtures[marker.name or attribute] = f"{distribution}:{entry_point.value}"
    return fixtures


def _forbidden_plugin_fixtures() -> frozenset[str]:
    """Every installed plugin fixture NOT on the safe allowlist — requesting one is flagged."""
    return frozenset(set(_installed_plugin_fixtures()) - set(_SAFE_PLUGIN_FIXTURES))


# How a test tree REQUESTS a fixture by name without calling anything that opens a listener.
_FIXTURE_LOOKUP_VERBS = frozenset({"getfixturevalue", "usefixtures"})


def _plugin_fixture_primitive(name: str, how: str) -> str:
    """The site description for a request of the forbidden plugin fixture ``name``."""
    return (
        f"requests pytest-plugin fixture {name!r} ({how}) — not on _SAFE_PLUGIN_FIXTURES; the plugin port "
        "fixtures (unused_tcp_port*, free_tcp_port*, …) hand back a NUMBER from #466's bind→close race"
    )


class _SiteCollector(ast.NodeVisitor):
    """Walk a module keeping the enclosing ``Class.function`` qualname for every listener call, and for every
    request of a forbidden pytest-plugin fixture (a parameter, ``getfixturevalue`` or ``usefixtures``)."""

    def __init__(self, path: str, aliases: dict[str, str], forbidden_fixtures: frozenset[str]) -> None:
        self.path = path
        self.aliases = aliases
        self.forbidden_fixtures = forbidden_fixtures
        self.scope: list[str] = []
        self.sites: list[ListenerSite] = []

    def _add(self, lineno: int, primitive: str) -> None:
        self.sites.append(ListenerSite(self.path, lineno, ".".join(self.scope) or "<module>", primitive))

    def _visit_scope(self, node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.scope.append(node.name)
        if not isinstance(node, ast.ClassDef):
            arguments = node.args
            for parameter in [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs]:
                if parameter.arg in self.forbidden_fixtures:
                    self._add(parameter.lineno, _plugin_fixture_primitive(parameter.arg, "a parameter"))
        self.generic_visit(node)
        self.scope.pop()

    visit_ClassDef = _visit_scope  # noqa: N815 — ast.NodeVisitor dispatch name
    visit_FunctionDef = _visit_scope  # noqa: N815
    visit_AsyncFunctionDef = _visit_scope  # noqa: N815

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802 — ast.NodeVisitor dispatch name
        primitive = _listener_primitive(node, self.aliases)
        if primitive is not None:
            self._add(node.lineno, primitive)
        if isinstance(node.func, ast.Attribute) and node.func.attr in _FIXTURE_LOOKUP_VERBS:
            for argument in node.args:
                if isinstance(argument, ast.Constant) and argument.value in self.forbidden_fixtures:
                    self._add(node.lineno, _plugin_fixture_primitive(argument.value, f"{node.func.attr}()"))
        self.generic_visit(node)


def listener_sites(tree: ast.Module, path: str) -> list[ListenerSite]:
    """Every raw listener-opening call and forbidden plugin-fixture request in ``tree`` (exemptions NOT
    applied)."""
    collector = _SiteCollector(path, _import_aliases(tree), _forbidden_plugin_fixtures())
    collector.visit(tree)
    return collector.sites


def _declared_testpaths() -> tuple[str, ...]:
    """``[tool.pytest.ini_options] testpaths`` — the INDEPENDENT oracle for "every test tree"."""
    manifest = tomllib.loads((_workspace_root() / "pyproject.toml").read_text(encoding="utf-8"))
    return tuple(manifest["tool"]["pytest"]["ini_options"]["testpaths"])


def _under(path: str, root: str) -> bool:
    return path == root or path.startswith(f"{root.rstrip('/')}/")


def _test_tree_scan() -> dict[str, ast.Module]:
    """The parsed test trees: the ONE shared parser (members + member tests + scripts + skills + every
    testpaths root), reach-checked, then filtered to files under a declared testpaths root."""
    trees = parse_production_trees(
        include_scripts=True, include_skills=True, include_tests=True, include_testpaths=True
    )
    assert_scan_reached_every_member(trees, extra_roots=("scripts", "skills", "docs"))
    testpaths = _declared_testpaths()
    return {path: tree for path, tree in trees.items() if any(_under(path, root) for root in testpaths)}


def _all_sites(trees: dict[str, ast.Module]) -> list[ListenerSite]:
    return [site for path, tree in sorted(trees.items()) for site in listener_sites(tree, path)]


def _helper_calls_by_file(trees: dict[str, ast.Module]) -> dict[str, int]:
    """How many calls to the helper's entry points each file makes (bare or attribute spelling)."""
    counts: dict[str, int] = {}
    for path, tree in trees.items():
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", None)
            if name in _HELPER_ENTRY_POINTS:
                counts[path] = counts.get(path, 0) + 1
    return counts


class TestNoRawListenerInAnyTestTree:
    """⛔ THE INVARIANT. RED at ``1206233`` on (declared, expected): ``test_migration_wire._free_port`` /
    ``._serve`` · ``test_port_probe._free_port`` / ``._start_stub_server`` · ``test_workspace_probe.
    _dead_port`` / ``._StubMCPServer.__init__`` · ``scripts/fastmcp_migration_spike._free_port`` /
    ``.serve``. GREEN once each routes through ``loremaster.testing.loopback`` (the spike: see the
    contract report's adjudication)."""

    def test_no_test_tree_opens_a_listener_outside_the_helper(self) -> None:
        offenders = [
            site.render()
            for site in _all_sites(_test_tree_scan())
            if (site.path, site.function) not in _EXEMPT_SITES
        ]
        assert not offenders, (
            "these sites open a listener OUTSIDE `loremaster.testing.loopback` (finding #466 — a bound "
            "port read and CLOSED is a port another pytest session can take before your server rebinds "
            "it). Use `LoopbackPort()` (a held port; un-listened = a refusing 'dead' port), "
            "`serve_asgi(app)` or `serve_http(handler)`:\n  " + "\n  ".join(offenders)
        )

    def test_every_exemption_still_matches_a_live_site(self) -> None:
        # Dead-entry pin: an exemption with no live site silently exempts the next listener in that spot.
        live = {(site.path, site.function) for site in _all_sites(_test_tree_scan())}
        dead = sorted(
            f"{path}::{function}" for path, function in _EXEMPT_SITES if (path, function) not in live
        )
        assert dead == [], f"these _EXEMPT_SITES entries match no live listener site — delete them: {dead}"


class TestTheScanReachesEveryTestTree:
    """REACH as a checked variable: every declared testpaths root is SCANNED, the scan is not empty, and
    both trees #466 lived in are SEEN adopting the helper (so the invariant is guarding real adopters)."""

    def test_every_declared_testpaths_root_is_scanned(self) -> None:
        # RED at 1206233: ``docs/eval`` is a testpaths root the shared parser does not reach.
        scanned = _test_tree_scan()
        unreached = [
            root for root in _declared_testpaths() if not any(_under(path, root) for path in scanned)
        ]
        assert unreached == [], (
            "these `[tool.pytest.ini_options] testpaths` roots are NOT scanned — every listener in them "
            f"is silently exempt from #466's guard: {unreached}. Extend "
            "`_logging_fixtures.parse_production_trees(include_testpaths=True)` to parse every "
            "testpaths root."
        )

    def test_the_scan_is_not_vacuous(self) -> None:
        scanned = _test_tree_scan()
        assert len(scanned) >= _TEST_TREE_FILE_FLOOR, (
            f"only {len(scanned)} test-tree files scanned (floor {_TEST_TREE_FILE_FLOOR}) — the parser did "
            "not reach the test trees, so a green invariant certifies nothing"
        )
        assert _all_sites(scanned), (
            "the scan found ZERO listener sites anywhere (not even the exempted ones) — the detector is "
            "broken, not the tree clean"
        )

    def test_both_trees_adopt_the_helper(self) -> None:
        # RED until the three test files migrate: the adoption must be OBSERVED in each tree, outside the
        # contract's own files (which cannot vouch for a tree they were written to exercise).
        calls = _helper_calls_by_file(_test_tree_scan())
        missing = [
            tree
            for tree in _ADOPTING_TREES
            if not any(_under(path, tree) and path not in _CONTRACT_FILES for path in calls)
        ]
        assert missing == [], (
            f"no file in {missing} calls LoopbackPort / serve_asgi / serve_http — the #466 copies there "
            "were not migrated onto the helper"
        )


class TestTheDetectorDiscriminates:
    """A probe needs a positive control (PKT-28 C1): every honest listener spelling is FLAGGED with its
    line; the honest non-listener look-alikes are NOT."""

    _PLANTED = (
        "import socket\n"  # 1
        "import socket as sk\n"  # 2
        "import asyncio\n"  # 3
        "import http.server\n"  # 4
        "import socketserver\n"  # 5
        "import uvicorn\n"  # 6
        "from http.server import HTTPServer as Stub\n"  # 7
        "from uvicorn import Config\n"  # 8
        "from socket import create_server\n"  # 9
        "from wsgiref.simple_server import make_server\n"  # 10
        "def free_port():\n"  # 11
        "    sock = socket.socket()\n"  # 12 — no listener yet
        "    sock.bind(('127.0.0.1', 0))\n"  # 13 ← raw bind (the #466 copy)
        "    sk.socket().bind(ADDRESS)\n"  # 14 ← raw bind on an aliased receiver
        "def servers(app, port, loop, handler):\n"  # 15
        "    http.server.HTTPServer(('127.0.0.1', port), handler)\n"  # 16 ← namespace
        "    Stub(('127.0.0.1', port), handler)\n"  # 17 ← aliased from-import
        "    socketserver.TCPServer(('127.0.0.1', port), handler)\n"  # 18
        "    uvicorn.Server(uvicorn.Config(app, port=port)).run()\n"  # 19 ← Server, Config, and .run
        "    Config(app, port=port)\n"  # 20
        "    create_server(('127.0.0.1', 0))\n"  # 21
        "    make_server('127.0.0.1', port, app)\n"  # 22
        "    loop.create_server(handler, '127.0.0.1', port)\n"  # 23 ← receiver-blind asyncio verb
        "    asyncio.start_server(handler, '127.0.0.1', port)\n"  # 24
    )
    _FLAGGED_LINES = [13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24]

    _HONEST = (
        "import inspect, socket, structlog, uvicorn\n"
        "def not_listeners(sig, fields, log, host, port, handler):\n"
        "    sig.bind(None, **fields)\n"  # inspect.Signature.bind — keywords
        "    log.bind(request_id='r-1')\n"  # structlog — keywords only
        "    socket.create_connection((host, port), timeout=1)\n"  # a CLIENT
        "    socket.socket().connect((host, port))\n"  # a CLIENT
        "    LoopbackPort()\n"  # the helper
        "    serve_asgi(handler, startup_timeout_s=15)\n"
        "    serve_http(handler)\n"
        "class Handler(http.server.BaseHTTPRequestHandler):\n"  # a base class reference, not a call
        "    server_class = uvicorn.Server\n"  # a reference, not a call
    )

    def test_every_planted_listener_spelling_is_flagged_on_its_line(self) -> None:
        flagged = sorted({site.lineno for site in listener_sites(ast.parse(self._PLANTED), "PLANTED.py")})
        assert flagged == self._FLAGGED_LINES, (
            f"flagged lines {flagged} != expected {self._FLAGGED_LINES} — a blind leg lets that listener "
            "spelling back into the test trees"
        )

    def test_honest_non_listeners_are_not_flagged(self) -> None:
        sites = listener_sites(ast.parse(self._HONEST), "HONEST.py")
        assert sites == [], (
            "the detector flagged a non-listener (Signature.bind / structlog bind / a client connect / "
            f"the helper / a class reference) — over-broad, and it will be switched off: "
            f"{[site.render() for site in sites]}"
        )

    def test_a_site_names_its_file_line_and_enclosing_function(self) -> None:
        source = (
            "import socket\nclass Stub:\n    def __init__(self):\n        socket.socket().bind(('', 0))\n"
        )
        (site,) = listener_sites(ast.parse(source), "skills/x/tests/test_y.py")
        assert site.render().startswith("skills/x/tests/test_y.py:4 (Stub.__init__)"), site.render()

    def test_a_planted_bind_in_a_real_source_file_is_caught(self, tmp_path: Path) -> None:
        # Positive control through a real FILE (not only a string): the read → parse → scan path works
        # on disk, and names the planted file and line.
        planted = tmp_path / "test_planted_listener.py"
        planted.write_text(
            "import socket\n\ndef _free_port():\n"
            "    probe = socket.socket()\n    probe.bind(('127.0.0.1', 0))\n",
            encoding="utf-8",
        )
        sites = listener_sites(ast.parse(planted.read_text(encoding="utf-8")), planted.name)
        assert [(site.path, site.lineno, site.function) for site in sites] == [
            ("test_planted_listener.py", 5, "_free_port")
        ]

    def test_the_exemption_is_keyed_by_function_not_by_file(self) -> None:
        # A NEW listener in an exempted FILE (another function) is still an offender: an exemption keyed by
        # file would silently cover whatever lands there next.
        source = (
            "import socket\n"
            "def _free_port(base):\n"
            "    socket.socket().bind(('', base))\n"
            "def another():\n"
            "    socket.socket().bind(('', 0))\n"
        )
        path = "skills/lore-deploy/scripts/lore_deploy.py"
        offenders = [
            site
            for site in listener_sites(ast.parse(source), path)
            if (site.path, site.function) not in _EXEMPT_SITES
        ]
        assert [(site.function, site.lineno) for site in offenders] == [("another", 5)]


class TestKnownBoundLibraryInternalListeners:
    """⚠ KNOWN BOUND (#466 contract, pinned so it is met deliberately): a listener opened INSIDE a
    dependency the test calls is invisible to an AST scan of our source. ``LoreServer(config).run()``
    binds ``config.server.port`` when nothing is patched (``test_mcp_server.TestRunAndMain`` patches
    ``uvicorn.Server.serve`` first, so it binds nothing today). If you made the detector see this door
    deliberately, delete this pin and say so. Re-open trigger: the first measured occurrence → a
    runtime tripwire on ``socket.socket.bind``, not a longer name list."""

    def test_a_production_entry_point_that_binds_is_not_seen(self) -> None:
        source = (
            "from loremaster.server import LoreServer\ndef test_run(config):\n    LoreServer(config).run()\n"
        )
        assert listener_sites(ast.parse(source), "KNOWN_BOUND.py") == [], (
            "this is a KNOWN BOUND (#466 contract): the detector now flags a production entry point that "
            "binds internally. If that was deliberate, delete this pin and record it."
        )


# ============================================================================================= #
# DELTA d1 — C1: _CONTRACT_FILES is held live, like _EXEMPT_SITES.
# ============================================================================================= #
def _stale_entries(entries: Iterable[str], scanned_paths: Iterable[str]) -> list[str]:
    """The entries that name NO file the scan read — each one excludes nothing, silently."""
    scanned = set(scanned_paths)
    return sorted(entry for entry in entries if entry not in scanned)


class TestTheContractFileExclusionIsLive:
    """C1 (REPORT-refactor-466.md §2): ``test_both_trees_adopt_the_helper`` excludes ``_CONTRACT_FILES`` so
    the contract cannot vouch for a tree. Rename a contract file and its stale entry excludes nothing —
    the renamed file then counts as its tree's adopter, and the adoption pin stays GREEN even if every
    real adopter regressed. Green at birth by design (no entry is stale at 43b8d16); it is proven by
    mutation (d1 report §C1) and by the planted control below."""

    def test_every_contract_file_entry_is_a_scanned_test_tree_file(self) -> None:
        stale = _stale_entries(_CONTRACT_FILES, _test_tree_scan())
        assert stale == [], (
            f"these _CONTRACT_FILES entries name no scanned test-tree file — renamed or moved? A stale "
            f"entry lets the contract's own file vouch for its tree. Update them: {stale}"
        )

    def test_positive_control_a_planted_stale_entry_is_reported(self) -> None:
        # The SAME function the live pin uses, fed a known-stale entry: without this, a checker that
        # returns [] for everything would make the live pin green forever.
        scanned = {
            "loremaster/tests/test_loopback_serving.py",
            "skills/lore-deploy/tests/test_loopback_home.py",
        }
        renamed = "loremaster/tests/test_loopback_serving_renamed.py"
        assert _stale_entries(set(scanned) | {renamed}, scanned) == [renamed]
        assert _stale_entries(scanned, scanned) == []


# ============================================================================================= #
# DELTA d1 — C3: aiohttp's listeners are seen; its clients and handlers are not.
# ============================================================================================= #
class TestTheDetectorSeesAiohttpListeners:
    """C3 (REPORT-refactor-466.md §2): aiohttp is installed (measured 2026-09-26) and absent from the
    listener namespaces. An honest ``web.run_app(app, port=…)`` or ``TCPSite`` in a test opens a listener
    with no ``.bind`` and no asyncio verb in OUR source, so the guard is blind to it — in-model by the
    guard's own threat model. ``unused_port()`` is #466's race itself (bind → read → CLOSE → hand back a
    number), shipped by aiohttp. RED at 43b8d16: no line below is flagged."""

    _PLANTED = (
        "import aiohttp\n"  # 1
        "from aiohttp import web\n"  # 2
        "from aiohttp.test_utils import TestServer, unused_port\n"  # 3
        "async def servers(app, runner, port, path):\n"  # 4
        "    web.run_app(app, host='127.0.0.1', port=port)\n"  # 5 ← the one-call server
        "    web.TCPSite(runner, '127.0.0.1', port)\n"  # 6 ← the runner/site server
        "    aiohttp.web.UnixSite(runner, path)\n"  # 7 ← fully-qualified spelling
        "    TestServer(app, port=port)\n"  # 8 ← aiohttp's own test server
        "    unused_port()\n"  # 9 ← the close→rebind race, from a dependency
    )
    _FLAGGED_LINES = [5, 6, 7, 8, 9]

    # aiohttp is mostly a CLIENT library; flagging its client or its handler vocabulary would refuse
    # honest code, and a gate that refuses honest code gets switched off. (``AppRunner`` / ``SockSite``
    # are deliberately in NEITHER list: a runner opens nothing until a site starts, and a SockSite needs
    # a socket whose bind is already flagged — the contract does not rule on them.)
    _HONEST = (
        "import aiohttp\n"
        "from aiohttp import web\n"
        "async def clients_and_handlers(url, payload):\n"
        "    async with aiohttp.ClientSession() as session:\n"
        "        await session.get(url)\n"
        "    web.Application()\n"
        "    web.Response(text='ok')\n"
        "    web.json_response(payload)\n"
    )

    def test_every_planted_aiohttp_listener_is_flagged_on_its_line(self) -> None:
        flagged = sorted({site.lineno for site in listener_sites(ast.parse(self._PLANTED), "PLANTED.py")})
        assert flagged == self._FLAGGED_LINES, (
            f"flagged lines {flagged} != expected {self._FLAGGED_LINES} — aiohttp listeners get back into "
            "the test trees through the unflagged lines"
        )

    def test_honest_aiohttp_clients_and_handlers_are_not_flagged(self) -> None:
        sites = listener_sites(ast.parse(self._HONEST), "HONEST.py")
        assert sites == [], (
            "the detector flagged an aiohttp CLIENT or HANDLER call — over-broad (a whole-namespace "
            f"`aiohttp` entry?): {[site.render() for site in sites]}"
        )


# ============================================================================================= #
# DELTA d1 — C3 reach: which server libraries exist is DERIVED, not remembered.
# ============================================================================================= #
def _imported_top_level_modules(trees: dict[str, ast.Module]) -> set[str]:
    """Every absolute top-level module any of ``trees`` imports — read off :func:`_import_aliases`, the
    SAME import resolution the detector uses, so the two cannot disagree about what a file imports."""
    return {dotted.split(".", 1)[0] for tree in trees.values() for dotted in _import_aliases(tree).values()}


def _calls_a_listener_verb(source: bytes) -> bool:
    """True iff ``source`` calls one of :data:`_DEPENDENCY_LISTENER_VERBS` (on any receiver).

    A bytes pre-filter first (measured: 9488 installed ``*.py``, 19 contain a verb token), so only the
    candidates are parsed; then an AST check, so a verb in a comment or a string does not count.
    """
    if not any(verb.encode("ascii") in source for verb in _DEPENDENCY_LISTENER_VERBS):
        return False
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in _DEPENDENCY_LISTENER_VERBS
        for node in ast.walk(tree)
    )


def _server_capable_imported_distributions(trees: dict[str, ast.Module]) -> set[str]:
    """Canonical names of the installed distributions that (a) provide a module some test tree imports
    and (b) call a listener verb somewhere in their own source."""
    providers = metadata.packages_distributions()
    names = {
        distribution
        for module in _imported_top_level_modules(trees)
        for distribution in providers.get(module, [])
    }
    capable: set[str] = set()
    for name in names:
        distribution = metadata.distribution(name)
        for file in distribution.files or []:
            if file.suffix != ".py":
                continue
            try:
                source = Path(str(distribution.locate_file(file))).read_bytes()
            except OSError:
                continue
            if _calls_a_listener_verb(source):
                capable.add(canonicalize_name(name))
                break
    return capable


class TestTheServerCapableDependenciesAreDerived:
    """C3 reach, made a CHECKED variable (CLAUDE.md INSTRUMENT 0: "is the set DERIVED from production
    truth, and does a test go RED when the derived set GROWS?"). The deny-list names a few namespaces; the
    set of server libraries the tests can reach is derived here from what the test trees IMPORT and what
    those distributions' own source DOES. Each must carry a planted spelling the detector flags.

    KNOWN BOUNDS (named, so they are met deliberately): (1) a dependency whose server is built from a raw
    ``.bind`` + ``.listen`` (socketserver-style — werkzeug's ``run_simple`` shape) is not derived: the verb
    oracle keys on the asyncio/anyio verbs, and a ``.bind`` oracle is drowned in ``Signature.bind`` noise
    (measured: sklearn, scipy, mypy …). Re-open trigger: the first such library imported by a test. (2) a
    library a test does not import yet is not derived until it is — aiohttp is covered proactively by
    :class:`TestTheDetectorSeesAiohttpListeners` because the audit named it; websockets (installed,
    verb-capable, not imported at 43b8d16) is left to this pin. (3) a PYTEST FIXTURE that picks a port
    (pytest-asyncio's ``unused_tcp_port``) is a parameter name, not a call — no call-keyed scan sees it
    (d1 report, surfaced for a ruling)."""

    def test_the_derived_server_capable_set_equals_the_planted_map(self) -> None:
        derived = _server_capable_imported_distributions(_test_tree_scan())
        assert derived, (
            "no server-capable distribution derived — uvicorn is imported by the test trees and calls "
            "create_server, so the derivation is broken, not the world empty"
        )
        planted = set(_PLANTED_BY_SERVER_DISTRIBUTION)
        unshown = sorted(derived - planted)
        dead = sorted(planted - derived)
        assert unshown == [] and dead == [], (
            f"server-capable distributions imported by a test tree with NO planted spelling: {unshown} — "
            "add one to _PLANTED_BY_SERVER_DISTRIBUTION and make the detector flag it; dead entries "
            f"(no longer derived — delete them): {dead}"
        )

    @pytest.mark.parametrize("distribution", sorted(_PLANTED_BY_SERVER_DISTRIBUTION))
    def test_the_planted_spelling_of_each_server_capable_dependency_is_flagged(
        self, distribution: str
    ) -> None:
        source = _PLANTED_BY_SERVER_DISTRIBUTION[distribution]
        sites = listener_sites(ast.parse(source), f"PLANTED_{distribution}.py")
        assert sites, (
            f"the detector does not see {distribution}'s listener — a test using it opens a port the "
            f"#466 guard cannot see:\n{source}"
        )

    def test_honest_anyio_clients_are_not_flagged(self) -> None:
        # anyio is imported by the test trees for task groups and clients; only its LISTENERS are doors.
        source = (
            "import anyio\n"
            "async def client(host, port):\n"
            "    await anyio.connect_tcp(host, port)\n"
            "    async with anyio.create_task_group() as group:\n"
            "        group.start_soon(anyio.sleep, 0)\n"
        )
        sites = listener_sites(ast.parse(source), "HONEST_anyio.py")
        assert sites == [], f"anyio client/task-group calls were flagged: {[site.render() for site in sites]}"

    def test_positive_control_the_verb_oracle_sees_a_verb_and_ignores_prose(self) -> None:
        assert _calls_a_listener_verb(b"async def f(loop):\n    await loop.create_server(p, sock=s)\n")
        assert not _calls_a_listener_verb(b"# we never call create_server here\nX = 'start_server'\n")
        assert not _calls_a_listener_verb(b"import socket\nsocket.create_connection(('h', 1))\n")


# ============================================================================================= #
# LEAD PIN (c) — a pytest-plugin PORT FIXTURE is #466's race requested by name. Forbidden by derivation.
# ============================================================================================= #
def _is_installed_third_party(source_file: str | None) -> bool:
    """True iff ``source_file`` lives in an installed-packages dir and is not pytest's own core."""
    if source_file is None:
        return False
    resolved = Path(source_file).resolve()
    installed_roots = {Path(sysconfig.get_paths()[key]).resolve() for key in ("purelib", "platlib")}
    inside = next((root for root in installed_roots if resolved.is_relative_to(root)), None)
    return inside is not None and resolved.relative_to(inside).parts[0] not in {"_pytest", "pytest"}


class TestPluginPortFixturesAreForbidden:
    """Lead pin (c): pytest-asyncio's ``unused_tcp_port`` / ``unused_tcp_port_factory`` / ``unused_udp_port*``
    (and, found by the derivation rather than named by anyone, anyio's ``free_tcp_port*`` /
    ``free_udp_port*``) bind ``:0``, read the port and CLOSE the socket — #466's race — and a test reaches
    them by NAME, which no call-keyed scan sees. The detector flags a request (parameter · ``getfixturevalue``
    · ``usefixtures``) of any installed plugin fixture NOT on :data:`_SAFE_PLUGIN_FIXTURES`.

    REACH IS A CHECKED VARIABLE: the forbidden set is derived from the ``pytest11`` entry points; every
    member of it is shown flagged (parametrised below, so the set GROWING grows the pin); the ruled names
    must be reached (non-vacuity); every safe entry must still exist (dead-entry); and the RUNNING session's
    fixture registry is cross-checked against the static derivation (the register-at-configure door).

    KNOWN BOUNDS (named, so they are met deliberately): (1) pytest core's fixtures (``_pytest``) are trusted
    wholesale — none opens a port. Re-open trigger: a pytest release adding one. (2) A plugin loaded only by
    ``pytest_plugins = [...]`` / ``-p`` (no entry point) — e.g. ``aiohttp.pytest_plugin``'s
    ``aiohttp_unused_port`` — is seen only by the live leg, and only in a session that loaded it; measured
    2026-09-26: no conftest here declares ``pytest_plugins`` and ``addopts`` carries no ``-p``. Re-open
    trigger: the first such declaration. (3) Indirect parametrisation (``parametrize("x", …,
    indirect=True)``) names a fixture in a string no leg reads. Re-open trigger: the first indirect use of a
    plugin fixture. (4) A non-fixture helper whose parameter happens to be spelled like a forbidden fixture
    is flagged too (a false positive an honest author fixes by renaming)."""

    _PLANTED = (
        "import pytest\n"  # 1
        "def test_parameter(unused_tcp_port):\n"  # 2 ← a test parameter
        "    pass\n"  # 3
        "async def test_keyword_only(tmp_path, *, free_tcp_port_factory):\n"  # 4 ← keyword-only
        "    pass\n"  # 5
        "@pytest.fixture\n"  # 6
        "def server(unused_udp_port_factory):\n"  # 7 ← a fixture's own parameter
        "    pass\n"  # 8
        "def test_dynamic(request):\n"  # 9
        "    request.getfixturevalue('unused_udp_port')\n"  # 10 ← getfixturevalue
        "@pytest.mark.usefixtures('anyio_backend', 'free_udp_port')\n"  # 11 ← usefixtures (one of two)
        "def test_marked():\n"  # 12
        "    pass\n"  # 13
        "class TestInAClass:\n"  # 14
        "    def test_method(self, unused_tcp_port_factory):\n"  # 15 ← a method parameter
        "        pass\n"  # 16
    )
    _FLAGGED_LINES = [2, 4, 7, 10, 11, 15]

    # Safe plugin fixtures, core fixtures, and forbidden NAMES used as something other than a fixture request.
    _HONEST = (
        "import pytest\n"
        "def test_safe(tmp_path, monkeypatch, anyio_backend, worker_id, testrun_uid, event_loop_policy):\n"
        "    unused_tcp_port = 5\n"  # a local variable, not a request
        "    request.getfixturevalue('tmp_path')\n"
        "    print('unused_tcp_port')\n"  # a string outside a fixture lookup
        "@pytest.mark.usefixtures('anyio_backend')\n"
        "def test_marked_safe():\n"
        "    pass\n"
    )

    def test_every_planted_plugin_fixture_request_is_flagged_on_its_line(self) -> None:
        sites = listener_sites(ast.parse(self._PLANTED), "PLANTED_fixtures.py")
        flagged = sorted({site.lineno for site in sites})
        assert flagged == self._FLAGGED_LINES, (
            f"flagged lines {flagged} != expected {self._FLAGGED_LINES} — a plugin port fixture gets back "
            f"into the test trees through the unflagged lines: {[site.render() for site in sites]}"
        )
        # The exemption key is the ENCLOSING function, as for every other site.
        assert {site.function for site in sites if site.lineno == 15} == {"TestInAClass.test_method"}

    def test_honest_fixture_requests_are_not_flagged(self) -> None:
        sites = listener_sites(ast.parse(self._HONEST), "HONEST_fixtures.py")
        assert sites == [], f"a SAFE fixture request was flagged: {[site.render() for site in sites]}"

    @pytest.mark.parametrize("fixture_name", sorted(_forbidden_plugin_fixtures()))
    def test_each_derived_forbidden_fixture_is_flagged_when_requested(self, fixture_name: str) -> None:
        source = f"def test_uses_it({fixture_name}):\n    pass\n"
        sites = listener_sites(ast.parse(source), f"PLANTED_{fixture_name}.py")
        assert [site.lineno for site in sites] == [1], (
            f"requesting the installed plugin fixture {fixture_name!r} "
            f"({_installed_plugin_fixtures()[fixture_name]}) is not flagged"
        )

    def test_the_derivation_reaches_the_ruled_port_fixtures(self) -> None:
        unreached = sorted(_RULED_PORT_FIXTURES - _forbidden_plugin_fixtures())
        assert unreached == [], (
            f"the ruled port fixtures {unreached} are not in the derived forbidden set — the derivation no "
            f"longer sees pytest-asyncio (derived: {sorted(_installed_plugin_fixtures())}), or they were "
            "classified SAFE"
        )

    def test_every_safe_entry_is_still_a_defined_plugin_fixture(self) -> None:
        # Dead-entry pin: a safe entry naming nothing would silently allow a FUTURE fixture of that name.
        dead = sorted(set(_SAFE_PLUGIN_FIXTURES) - set(_installed_plugin_fixtures()))
        assert dead == [], f"these _SAFE_PLUGIN_FIXTURES entries name no installed plugin fixture: {dead}"

    def test_the_running_session_registers_no_plugin_fixture_the_derivation_missed(
        self, request: pytest.FixtureRequest
    ) -> None:
        # The live leg: every fixture THIS session registered from installed third-party code must be in the
        # static derivation — a plugin that registers fixtures at configure time, or one loaded by ``-p`` /
        # ``pytest_plugins``, reddens here by name. ``_arg2fixturedefs`` is private (no public registry).
        registry = request._fixturemanager._arg2fixturedefs
        live = {
            name
            for name, definitions in registry.items()
            for definition in definitions
            if _is_installed_third_party(inspect.getsourcefile(definition.func))
        }
        assert live, "no installed third-party fixture registered in this session — the live leg sees nothing"
        missed = sorted(live - set(_installed_plugin_fixtures()))
        assert missed == [], (
            "this session registered installed plugin fixtures the pytest11 derivation does not see: "
            f"{missed} — classify each (safe, or leave it forbidden) and extend the derivation"
        )
