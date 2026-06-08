"""CONTRACT: the lore MCP server advertises its OWN (build-time-baked) version.

The defect this contract pins: ``build_mcp_server`` constructs the
``FastMCP`` with NO ``version=``, so FastMCP's low-level server leaves
``_mcp_server.version`` as ``None``. The MCP SDK then falls back to
``importlib.metadata.version("mcp")`` in
``create_initialization_options()`` — meaning the server's advertised
``serverInfo.version`` is the **MCP SDK's** version (e.g. "1.27.2"), NOT
lore's. A connecting host therefore cannot tell which lore build it is
talking to.

The fix has two halves, both pinned here from the *requirement* (never
reverse-engineered from any implementation):

1.  A module-level version resolver ``server._resolve_version()`` and a
    module constant ``server.__version__`` with this PRECEDENCE:
      a. env ``LORE_VERSION`` set and non-empty  → return it verbatim
         (the value baked into the container image at build time wins);
      b. else                                    → ``importlib.metadata.version("loremaster")``;
      c. else (``PackageNotFoundError``)         → ``"unknown"``.
    An EMPTY ``LORE_VERSION=""`` must fall THROUGH to (b), not be returned.

2.  ``build_mcp_server`` constructs the FastMCP so the server ADVERTISES
    that version: the built server's advertised ``serverInfo.version``
    equals ``server.__version__`` and is NOT the MCP SDK version.

HOW FASTMCP EXPOSES THE VERSION (verified by reading the installed
``mcp.server.fastmcp.server.FastMCP`` and ``mcp.server.lowlevel.server``):

* FastMCP's ``__init__`` does NOT accept a ``version=`` kwarg and does
  NOT forward one to its low-level server — so the version is carried by
  the **low-level** server it wraps: ``mcp._mcp_server.version``
  (``str | None``, default ``None``).
* ``serverInfo.version`` (what the host sees on ``initialize``) is
  produced by ``mcp._mcp_server.create_initialization_options()`` as
  ``self.version if self.version else pkg_version("mcp")`` — so a
  ``None`` version silently advertises the MCP SDK version. This is the
  observable seam the contract asserts on: the
  ``.create_initialization_options().server_version`` field, which is
  the real ``serverInfo.version`` wire value, not an internal-only
  attribute.

These tests are written BLIND to the (not-yet-written) implementation:
they reference the named surface (``server._resolve_version``,
``server.__version__``, the ``version=`` flow into FastMCP) so the RED
failures are crisp, and they assert OBSERVABLE behavior (precedence
branches; the wire ``server_version`` field) rather than restating any
formula.
"""

from __future__ import annotations

import importlib
import importlib.metadata
from pathlib import Path
from typing import Any

import loremaster.server as server_module
import pytest
from loremaster.config import LoreConfig
from loremaster.server import LoreServer, build_mcp_server

# --------------------------------------------------------------------------- #
# Shared domain conventions — sourced from the SAME place production reads them
# (clause 5). These are NOT hand-copied magic literals: the env var name is the
# build-time contract baked into the container image, and the distribution name
# is the one `importlib.metadata` resolves for the installed `loremaster` wheel.
# --------------------------------------------------------------------------- #

# The env var the container build bakes the `git describe` output into. The
# resolver MUST read THIS name (the producer↔consumer seam between the image
# build step and the running server).
LORE_VERSION_ENV = "LORE_VERSION"

# The installed distribution name `importlib.metadata.version(...)` resolves for
# the fallback branch. Production resolves the SAME name; a test that hardcoded a
# different string would silently diverge.
LOREMASTER_DIST_NAME = "loremaster"

# The MCP SDK's own distribution — the value the buggy default advertises. The
# independence assertions below prove the server does NOT advertise this.
MCP_SDK_DIST_NAME = "mcp"

# The sentinel the fallback branch returns when the package is not installed.
UNKNOWN_VERSION = "unknown"

# A realistic build-time-baked value: `git describe --tags --always --dirty`
# emits exactly this shape (tag + commits-since + short-sha, optionally
# `-dirty`). This is the *real distribution* of what LORE_VERSION holds in a
# production image — not a clean synthetic like "1.0".
REALISTIC_BAKED_VERSION = "v0.3.1-7-gdeadbee-dirty"

# A second realistic baked value used by the end-to-end env→FastMCP flow test,
# distinct from any tag in the repo so a match cannot be a coincidence.
SENTINEL_BAKED_VERSION = "v9.9.9-test"


# --------------------------------------------------------------------------- #
# Fixtures — built via the SAME production path the rest of the suite uses
# (`build_mcp_server(LoreServer(config))` — see test_mcp_server.py). FastMCP
# construction is lazy: the lifespan (Qdrant/embedder) only runs at serve time,
# so building the server needs no live backend.
# --------------------------------------------------------------------------- #


def _config(slug: str, live_path: Path) -> LoreConfig:
    """A minimal-but-valid LoreConfig, mirroring test_mcp_server.py's builder.

    Reused across cases so every built server starts from the same
    production-validated config shape (clause 1/5 — no ad-hoc fixture).
    """
    payload: dict[str, Any] = {
        "schema_version": 1,
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://localhost:8080",
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": 2048,
            "truncate": False,
            "max_input_tokens": 8192,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": "LORE_TEI_KEY",
            "tokenizer": "voyage-4-nano",
        },
        "qdrant": {
            "url": "http://127.0.0.1:16333",
            "api_key_env": "QDRANT__SERVICE__API_KEY",
        },
        "roots": [
            {
                "tier": "custom",
                "watch": "live",
                "path": str(live_path),
                "include": ["**/*.py"],
            }
        ],
        "include": [],
        "exclude_dirs": [".git"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": True,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9233},
    }
    return LoreConfig.model_validate(payload)


def _advertised_version(mcp: Any) -> str:
    """The wire ``serverInfo.version`` the host sees on ``initialize``.

    This reaches through FastMCP to its low-level server's
    ``create_initialization_options()`` — the SAME call the SDK makes when a
    client connects — and returns the ``server_version`` field. Asserting on
    this (rather than an internal attribute) pins the OBSERVABLE wire value at
    the real producer→consumer seam.
    """
    init_options = mcp._mcp_server.create_initialization_options()
    return str(init_options.server_version)


@pytest.fixture()
def built_server(tmp_path: Path) -> Any:
    """A FastMCP built via the production path, no live backend required."""
    config = _config(f"test_{tmp_path.name}", tmp_path / "live")
    return build_mcp_server(LoreServer(config))


# --------------------------------------------------------------------------- #
# Part 1 — the resolver precedence (env > installed metadata > "unknown")
# --------------------------------------------------------------------------- #
class TestResolveVersionPrecedence:
    """``server._resolve_version()`` resolves the version with a fixed precedence.

    Pins all three branches of the requirement: the build-time-baked
    ``LORE_VERSION`` env wins verbatim; absent that, the installed
    ``loremaster`` package metadata; absent THAT, the literal ``"unknown"``.
    The empty-string env case (a degenerate but real container mis-bake) must
    fall through, not be returned.
    """

    def test_returns_lore_version_env_verbatim_when_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Branch (a): the value baked into the image at build time wins, returned
        # exactly as set (no normalisation, no stripping of the `v` or `-dirty`).
        monkeypatch.setenv(LORE_VERSION_ENV, REALISTIC_BAKED_VERSION)

        resolved = server_module._resolve_version()

        assert resolved == REALISTIC_BAKED_VERSION

    def test_falls_back_to_installed_metadata_when_env_unset(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Branch (b): with no LORE_VERSION, the resolver reports the installed
        # `loremaster` distribution's metadata version. Expected value comes from
        # an INDEPENDENT source — importlib.metadata read directly here — not from
        # restating the resolver's formula.
        monkeypatch.delenv(LORE_VERSION_ENV, raising=False)
        expected = importlib.metadata.version(LOREMASTER_DIST_NAME)

        resolved = server_module._resolve_version()

        assert resolved == expected
        # Sanity: the fallback is a real PEP 440-ish version, not the sentinel.
        assert resolved != UNKNOWN_VERSION

    def test_empty_env_falls_through_to_metadata_not_returned(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # An EMPTY LORE_VERSION="" (a real container mis-bake: the env is exported
        # but `git describe` produced nothing) must NOT be returned as the version.
        # It must fall THROUGH to the installed-metadata branch.
        monkeypatch.setenv(LORE_VERSION_ENV, "")
        expected = importlib.metadata.version(LOREMASTER_DIST_NAME)

        resolved = server_module._resolve_version()

        assert resolved == expected
        assert resolved != "", "empty LORE_VERSION must not be advertised as the version"

    def test_returns_unknown_when_package_not_installed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Branch (c): no env AND the package metadata is unresolvable
        # (PackageNotFoundError — e.g. run from a source tree with no installed
        # dist). The resolver degrades to the literal "unknown" rather than
        # crashing the server build.
        monkeypatch.delenv(LORE_VERSION_ENV, raising=False)

        def _raise_not_found(_name: str) -> str:
            raise importlib.metadata.PackageNotFoundError(LOREMASTER_DIST_NAME)

        # Patch the symbol on importlib.metadata so whichever import form the
        # resolver uses (`from importlib.metadata import version` or
        # `importlib.metadata.version`) is covered.
        monkeypatch.setattr(importlib.metadata, "version", _raise_not_found)

        resolved = server_module._resolve_version()

        assert resolved == UNKNOWN_VERSION

    def test_env_wins_over_installed_metadata(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Precedence proof: even WHEN the package is installed (metadata
        # resolvable), an explicit LORE_VERSION still wins. Guards against an
        # implementation that consults metadata first.
        installed = importlib.metadata.version(LOREMASTER_DIST_NAME)
        monkeypatch.setenv(LORE_VERSION_ENV, REALISTIC_BAKED_VERSION)

        resolved = server_module._resolve_version()

        assert resolved == REALISTIC_BAKED_VERSION
        # The baked value and the installed metadata are genuinely different, so
        # this is a real precedence test, not a coincidental match.
        assert REALISTIC_BAKED_VERSION != installed


# --------------------------------------------------------------------------- #
# Part 2 — the module constant
# --------------------------------------------------------------------------- #
class TestModuleVersionConstant:
    """``server.__version__`` exists and is a non-empty string equal to the resolver."""

    def test_module_exposes_version_constant(self) -> None:
        # The module advertises a public __version__ string.
        assert hasattr(server_module, "__version__")
        assert isinstance(server_module.__version__, str)
        assert server_module.__version__ != "", "__version__ must be a non-empty string"

    def test_module_version_equals_resolver_in_current_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # __version__ is the resolver's value for the AMBIENT (import-time) env.
        # Reloading under the current process env re-derives the same string, so
        # the constant is the resolver's output, not a divergent hardcode.
        monkeypatch.delenv(LORE_VERSION_ENV, raising=False)
        reloaded = importlib.reload(server_module)
        try:
            assert reloaded.__version__ == reloaded._resolve_version()
        finally:
            # Restore the module to a clean import so other tests see no env-skew.
            importlib.reload(server_module)


# --------------------------------------------------------------------------- #
# Part 3 — the built server ADVERTISES the version (the wire serverInfo.version)
# --------------------------------------------------------------------------- #
class TestBuiltServerAdvertisesVersion:
    """``build_mcp_server`` makes the FastMCP advertise lore's version on the wire.

    Asserts the OBSERVABLE ``serverInfo.version`` (the
    ``create_initialization_options().server_version`` field the host receives on
    ``initialize``), not just an internal attribute. The independence cases prove
    the advertised value FLOWS env → __version__ → FastMCP and is NOT the MCP
    SDK's own version (the current bug).
    """

    def test_built_server_advertises_module_version(self, built_server: Any) -> None:
        # The wire serverInfo.version equals the module __version__ resolved for
        # the ambient env. This is the core contract: the server tells the host
        # which lore build it is.
        assert _advertised_version(built_server) == server_module.__version__

    def test_built_server_does_not_advertise_mcp_sdk_version(
        self, built_server: Any
    ) -> None:
        # Independence / anti-regression: the current defect advertises the MCP
        # SDK's version (importlib.metadata.version("mcp")). The fixed server must
        # NOT — its advertised version is lore's, sourced independently here.
        mcp_sdk_version = importlib.metadata.version(MCP_SDK_DIST_NAME)

        advertised = _advertised_version(built_server)

        assert advertised != mcp_sdk_version, (
            f"the server must advertise lore's version, not the MCP SDK's "
            f"{mcp_sdk_version!r}"
        )

    def test_baked_env_flows_through_to_advertised_version(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # END-TO-END SEAM (clause 3): set LORE_VERSION to a sentinel BEFORE the
        # version is resolved for the built server, then prove the host-visible
        # serverInfo.version is exactly that sentinel. This exercises the real
        # handoff: image-build env  →  _resolve_version  →  FastMCP  →  wire.
        #
        # The contract requires this to hold WITHOUT import-order gymnastics: the
        # caller must make build_mcp_server resolve the version such that an env
        # set before the build is honoured (resolve-at-call-time, OR a module
        # reload picks it up). We set the env, reload so __version__ re-derives,
        # then build — and assert the sentinel reaches the wire.
        monkeypatch.setenv(LORE_VERSION_ENV, SENTINEL_BAKED_VERSION)
        reloaded = importlib.reload(server_module)
        try:
            config = _config(f"test_{tmp_path.name}", tmp_path / "live")
            mcp = reloaded.build_mcp_server(reloaded.LoreServer(config))

            assert _advertised_version(mcp) == SENTINEL_BAKED_VERSION
            # And it is genuinely the env value flowing through, not the SDK
            # default leaking back in.
            assert _advertised_version(mcp) != importlib.metadata.version(
                MCP_SDK_DIST_NAME
            )
        finally:
            # Reload clean so no env-skewed module state leaks to other tests.
            monkeypatch.delenv(LORE_VERSION_ENV, raising=False)
            importlib.reload(server_module)

    def test_advertised_version_is_a_non_empty_string(self, built_server: Any) -> None:
        # Sanity bound on the derived wire output: whatever branch produced it,
        # the advertised version is always a non-empty string (never None, which
        # would let the SDK fall back to its own version).
        advertised = _advertised_version(built_server)

        assert isinstance(advertised, str)
        assert advertised != ""
