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
"""

from __future__ import annotations

import ast
import tomllib
from dataclasses import dataclass
from pathlib import Path

from _logging_fixtures import _workspace_root, assert_scan_reached_every_member, parse_production_trees

# Every callable reached through these modules opens (or configures) a listener.
_LISTENER_NAMESPACES = ("socketserver", "http.server", "uvicorn", "wsgiref.simple_server")
# The one ``socket`` module function that binds (``socket.socket`` itself binds nothing until ``.bind``).
_LISTENER_FUNCTIONS = ("socket.create_server",)
# asyncio's listener verbs — matched on ANY receiver (a loop, the asyncio module, an alias).
_LISTENER_METHODS = frozenset({"create_server", "create_unix_server", "start_server", "start_unix_server"})
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
        return f"{ast.unparse(func)}(…) — an asyncio listener"
    qualified = _resolved_callee(call, aliases)
    if qualified is None:
        return None
    if qualified in _LISTENER_FUNCTIONS or any(
        _is_in_namespace(qualified, ns) for ns in _LISTENER_NAMESPACES
    ):
        return f"{qualified}(…) — a listener outside loremaster.testing.loopback"
    return None


class _SiteCollector(ast.NodeVisitor):
    """Walk a module keeping the enclosing ``Class.function`` qualname for every listener call."""

    def __init__(self, path: str, aliases: dict[str, str]) -> None:
        self.path = path
        self.aliases = aliases
        self.scope: list[str] = []
        self.sites: list[ListenerSite] = []

    def _visit_scope(self, node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    visit_ClassDef = _visit_scope  # noqa: N815 — ast.NodeVisitor dispatch name
    visit_FunctionDef = _visit_scope  # noqa: N815
    visit_AsyncFunctionDef = _visit_scope  # noqa: N815

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802 — ast.NodeVisitor dispatch name
        primitive = _listener_primitive(node, self.aliases)
        if primitive is not None:
            function = ".".join(self.scope) or "<module>"
            self.sites.append(ListenerSite(self.path, node.lineno, function, primitive))
        self.generic_visit(node)


def listener_sites(tree: ast.Module, path: str) -> list[ListenerSite]:
    """Every raw listener-opening call in ``tree`` (exemptions NOT applied)."""
    collector = _SiteCollector(path, _import_aliases(tree))
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
