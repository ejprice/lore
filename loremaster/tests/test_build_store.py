"""Contract pins for the packet 48 Wave 48-A ``build_store(config)`` extraction.

Spec: ``docs/design/2026-08-20-packet48-principals-substrate.md`` §1 (Fork 1 —
NARROW extraction) + §8 checklist items 1–4 (Half 1). Execute verbatim.

WHAT IS BEING EXTRACTED
    Three production functions construct a byte-identical
    ``SurrealStore(url, namespace, database, dim, user, password)`` after the
    identical credential/db recipe (``resolve_config_value(surreal.user_env)`` +
    ``resolve_secret(surreal.password_env)`` + ``effective_surreal_database``):

        * ``loremaster.server.build_app_context``   (local ``write_store`` — READIED)
        * ``loremaster.index.cli._run``             (local ``store``       — READIED)
        * ``loremaster.scout.Scout.from_config``    (local ``store``   — NOT readied)

    48-A introduces ``build_store(config) -> SurrealStore`` (in
    ``loremaster/store/surreal.py`` — no config↔store.surreal import cycle, verified)
    that owns exactly that recipe + construction, returns an UN-READIED store, and
    parses NO url credentials (the inline-credential rejection lives upstream in
    ``config._reject_url_userinfo`` — R4). All three sites route through it; the
    caller keeps its readiness decision (R5: the server site builds under the native
    fastmcp lifespan chain ``build_mcp_server`` -> ``_lifespan`` ->
    ``_eager_build_or_operator_safe_error`` -> ``_eager_build_with_retry`` ->
    ``_build_context`` -> ``build_app_context`` — the deleted ``_EagerStartupLifespan``
    is never referenced).

WHY THESE PINS ARE RED NOW (contract-first)
    ``build_store`` does not exist yet, so:
      * every pin that needs it calls ``_require_build_store()`` first, which
        ``pytest.fail``s cleanly while the factory is absent (a dynamic ``getattr``,
        NOT a top-level import — so this file stays collection- and mypy-clean, the
        sibling ``test_comms_wiring`` norm, rather than reddening the typecheck gate);
      * the structural routing pins are RED because each caller currently constructs
        ``SurrealStore(...)`` INLINE and calls no ``build_store(...)``.
    Two pins are labelled STANDING GUARDS and are GREEN NOW by design — they pin the
    upstream R4 rejection and the deleted R5 symbol that make ``build_store`` correct;
    each reddens only if that surrounding invariant regresses.

HOW THEY DISCRIMINATE A CORRECT BUILD FROM A WRONG ONE
    * RESOLUTION pins run the REAL caller (or ``build_store`` itself) and read the
      actual ``SurrealStore`` it constructs — captured for the two readied callers by
      a class-level ``SurrealStore.ensure_ready`` sentinel that records ``self`` and
      aborts before any socket, and for Scout by reading ``scout._store`` directly.
      They assert the store carries the config-resolved values. At BUILD time
      ``scripts/mutation_proof.py`` mutates ``build_store``'s resolved ``database``
      inside ``build_store`` ONLY; every routed caller's resolution pin reddens, an
      inlined caller stays GREEN, and the both-ways diff catches the inliner
      (routing-is-not-sharing). EVERY resolved field (url / namespace / database / dim /
      user / password) carries a DISTINCTIVE sentinel value, so a build that HARDCODES a
      common value (namespace="lore_test", dim=2048, the spike url) instead of resolving
      it fails the resolution pins (adversary MP-2 — fixture monoculture).
    * STRUCTURAL ROUTING pins (AST over the caller's own source) assert the caller
      calls ``build_store(...)`` and no longer constructs ``SurrealStore(...)`` inline
      — the static routing-is-not-sharing catch the FIXTURES-MUST-DISCRIMINATE law
      demands, independent of the build-time mutation proof.

Fully OFFLINE — the sentinel aborts before any ``ws://`` connection, so no live
store is required (a live round-trip is Half-2's job, not 48-A's).

DECLARED expected-RED set for ``scripts/mutation_proof.py --expect-red`` (mutate
``build_store``'s resolved ``database``):
    loremaster/tests/test_build_store.py::test_build_store_resolves_all_six_config_values
    loremaster/tests/test_build_store.py::test_build_app_context_store_is_resolved_and_readied
    loremaster/tests/test_build_store.py::test_index_cli_run_store_is_resolved_and_readied
    loremaster/tests/test_build_store.py::test_scout_from_config_store_is_resolved_and_unreadied

This file is independently collectible — it imports NOTHING from the sibling test tree
(the house independent-collectibility property), only production modules + stdlib.

REVISION r2 (adversary delta): MP-1 — the R4 pin is now AST-based so it no longer
false-reddens on a correct build's docstring/config-field references; MP-2 — namespace,
dim, and url now carry distinctive sentinels alongside db/user/password. Satisfiability
re-proven 0-failed against a correct reference build_store (incl. the design's ruled
docstring) — see REPORT-contract-48a.md §"Revision r2".
"""

from __future__ import annotations

import argparse
import ast
import inspect
import textwrap
import uuid
from pathlib import Path
from typing import Any

import pytest
from loremaster.config import LoreConfig, resolve_config_value, resolve_secret
from loremaster.store.surreal import SurrealStore
from loresigil.testing import FakeEmbedder
from pydantic import ValidationError

# --------------------------------------------------------------------------- #
# Config / credential plumbing. There is NO shared LoreConfig factory in this
# repo — the house pattern is a per-file copy of the minimal-valid payload
# (documented "independent-collectibility property"); this clones
# ``test_comms_wiring._config`` (the sibling that drives ``build_app_context``
# the same way).
#
# EVERY resolved field carries a DISTINCTIVE sentinel value so that a build which
# HARDCODES a common value (e.g. namespace="lore_test", dim=2048, the spike url)
# instead of RESOLVING it from config fails the resolution pins (adversary MP-2 —
# fixture monoculture). The exact values do not matter to connectivity because the
# ensure_ready sentinel aborts before any socket; they only need to be valid config
# and distinctive: ``url`` any non-userinfo string (CredentialFreeUrl), ``namespace``
# matches SLUG_PATTERN ``^[a-z0-9][a-z0-9_]*$``, ``dim`` any PositiveInt, ``database``
# a unique per-test slug, ``user``/``password`` distinctive strings.
# --------------------------------------------------------------------------- #

_SENTINEL_URL = "ws://contract48-sentinel-host:19248/rpc"  # no userinfo → passes CredentialFreeUrl
_SENTINEL_NAMESPACE = "contract48_ns_sentinel"  # matches SLUG_PATTERN; NOT the common "lore_test"
_SENTINEL_DIM = 1493  # a distinctive PositiveInt; NOT the common production 2048
_SURREAL_USER_ENV = "SURREAL_USER"
_SURREAL_PASS_ENV = "SURREAL_PASS"
_SENTINEL_USER = "contract48-user-sentinel"
_SENTINEL_PASS = "contract48-pass-sentinel"


@pytest.fixture(autouse=True)
def _surreal_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Export distinctive SurrealDB credentials by the env-var NAMEs the config
    references, so ``build_store``'s ``resolve_config_value`` / ``resolve_secret``
    succeed (they KeyError on an unset var) and a build that hardcodes a credential
    instead of resolving it is discriminated.
    """
    monkeypatch.setenv(_SURREAL_USER_ENV, _SENTINEL_USER)
    monkeypatch.setenv(_SURREAL_PASS_ENV, _SENTINEL_PASS)


def _slug() -> str:
    """A unique per-test project slug — also the derived ``effective_surreal_database``
    (``surreal.database`` is left unset), so ``database`` cannot be hardcoded green."""
    return f"test_{uuid.uuid4().hex}"


def _config_payload(slug: str) -> dict[str, Any]:
    """The minimal valid config payload with DISTINCTIVE sentinel values for every
    resolved field (never connected — the ensure_ready sentinel aborts first).

    Cloned from ``test_comms_wiring._config`` (the blessed per-file pattern). ``surreal``
    carries no ``database`` (derives from ``slug``); creds are referenced by env NAME.
    """
    return {
        "schema_version": 1,
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://localhost:8080",
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": _SENTINEL_DIM,
            "truncate": False,
            "max_input_tokens": 8192,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": "LORE_TEI_KEY",
            "tokenizer": "voyage-4-nano",
        },
        "surreal": {
            "url": _SENTINEL_URL,
            "namespace": _SENTINEL_NAMESPACE,
            "user_env": _SURREAL_USER_ENV,
            "password_env": _SURREAL_PASS_ENV,
        },
        "roots": [],
        "include": [],
        "exclude_dirs": [".git"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": False,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9248},
    }


def _make_config() -> tuple[LoreConfig, str]:
    """A validated config + its slug (the slug names manifest/snapshot temp paths)."""
    slug = _slug()
    return LoreConfig.model_validate(_config_payload(slug)), slug


def _require_build_store() -> Any:
    """RED-now gate: ``build_store`` is extracted by packet 48-A into
    ``loremaster/store/surreal.py``. Until it lands this fails the pin CLEANLY —
    never a collection-time ImportError and never a mypy ``attr-defined`` red (the
    dynamic ``getattr`` keeps this file typecheck- and collection-clean, the sibling
    ``test_comms_wiring`` norm). After 48-A it returns the real factory so the
    behavioral assertions run. If the builder places ``build_store`` elsewhere than
    ``store.surreal`` (design §1 recommends surreal.py; fallback factory.py only on a
    config↔surreal cycle, verified ABSENT), update this one resolver.
    """
    import loremaster.store.surreal as surreal_module

    build_store = getattr(surreal_module, "build_store", None)
    if build_store is None:
        pytest.fail("build_store not yet extracted (packet 48-A) — contract is RED until it lands")
    return build_store


# --------------------------------------------------------------------------- #
# Store-capture harness (offline). Patch the class-level
# ``SurrealStore.ensure_ready`` to RECORD the store instance and ABORT before any
# ``_ensure_connection`` socket — so the two readied callers hand us the exact
# store they built (via ``build_store`` after the extraction) with no live I/O.
# --------------------------------------------------------------------------- #


class _EnsureReadyAborted(Exception):
    """Raised by the patched ``ensure_ready`` to capture the store + abort readiness."""


def _install_ensure_ready_capture(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    captured: dict[str, Any] = {}

    async def _capture(self: SurrealStore) -> None:
        captured["store"] = self
        captured["ensure_ready_called"] = True
        raise _EnsureReadyAborted

    monkeypatch.setattr(SurrealStore, "ensure_ready", _capture)
    return captured


def _assert_store_resolved(store: SurrealStore, config: LoreConfig) -> None:
    """The store carries every value ``build_store`` resolves from ``config``.

    Reads the ctor-stored private attributes (the design's named storage). The
    ``database`` leg is the mutation-proof anchor (a unique slug); the credential
    legs discriminate a hardcoded credential from a resolved one (sentinels).
    """
    assert store._url == config.surreal.url
    assert store._namespace == config.surreal.namespace
    assert store._database == config.effective_surreal_database
    assert store._dim == config.embedding.dim
    assert store._user == resolve_config_value(config.surreal.user_env)
    assert (
        store._password.get_secret_value()
        == resolve_secret(config.surreal.password_env).get_secret_value()
    )


def _direct_call_names(func: Any) -> set[str]:
    """The bare names of every direct Call in a function's OWN source (AST).

    ``foo(...)`` -> ``foo``; ``obj.foo(...)`` -> ``foo``. Used to prove a caller
    routes the write store through ``build_store(...)`` and constructs no inline
    ``SurrealStore(...)``. Robust to comments / type hints / import style (unlike a
    substring scan) and to line drift.
    """
    src = textwrap.dedent(inspect.getsource(func))
    tree = ast.parse(src)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name):
                names.add(fn.id)
            elif isinstance(fn, ast.Attribute):
                names.add(fn.attr)
    return names


# --------------------------------------------------------------------------- #
# Intrinsic ``build_store`` pins (RED now: _require_build_store() fails until 48-A).
# --------------------------------------------------------------------------- #


def test_build_store_resolves_all_six_config_values() -> None:
    """``build_store(config)`` resolves url / namespace / database / dim / user /
    password from config — the intrinsic anchor of the resolution mutation proof."""
    build_store = _require_build_store()
    config, _slug_unused = _make_config()
    store = build_store(config)
    _assert_store_resolved(store, config)


def test_build_store_returns_unreadied_store() -> None:
    """``build_store`` returns a store on which ``ensure_ready`` has NOT been called
    (readiness is the caller's decision — design §1 readiness contract). Behavioral
    tell: the factory is synchronous and the returned store is unconnected."""
    build_store = _require_build_store()
    assert not inspect.iscoroutinefunction(build_store), (
        "build_store must be a synchronous factory returning an UN-READIED store; "
        "an async/self-readying build would connect here"
    )
    config, _slug_unused = _make_config()
    store = build_store(config)
    assert store._connection is None, "build_store must not ready (connect) the store"


def test_build_store_body_has_no_url_credential_parsing() -> None:
    """R4 regression guard: ``build_store`` reads ``config.surreal.url`` verbatim and
    parses NO inline credentials — that rejection lives upstream in
    ``config._reject_url_userinfo`` (see the anchor pin below). A build that
    re-implements credential handling in the factory reddens this.

    AST-based, deliberately, so it inspects the factory's CODE — NOT its docstring
    prose (the design's ruled docstring legitimately NAMES ``config._reject_url_userinfo``,
    so a substring scan of ``inspect.getsource`` would false-redden on a correct build,
    adversary MP-1) and NOT the legitimate config fields (``config.surreal.password_env``
    is the AST attribute ``password_env``, NOT ``password`` — so a bare ``.password``
    substring, which the correct build's ``password_env`` reference contains, is never
    matched here).
    """
    build_store = _require_build_store()
    tree = ast.parse(textwrap.dedent(inspect.getsource(build_store)))
    calls = _direct_call_names(build_store)
    for banned_call in ("urlparse", "urlsplit", "_reject_url_userinfo"):
        assert banned_call not in calls, (
            f"build_store must not parse/reject URL credentials itself ({banned_call}()); "
            "that rejection lives upstream in config._reject_url_userinfo."
        )
    accessed_attrs = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    for banned_attr in ("username", "password", "userinfo"):
        assert banned_attr not in accessed_attrs, (
            f"build_store must not access a parsed URL's .{banned_attr}; it passes "
            "config.surreal.url through untouched (credential rejection is upstream)."
        )


# --------------------------------------------------------------------------- #
# Caller RESOLUTION + READINESS pins (the three-site sharing / mutation proof).
# Each runs the REAL caller and observes the SurrealStore it actually constructs.
# RED now via the _require_build_store() gate; behavioral + mutation-provable after.
# --------------------------------------------------------------------------- #


async def test_build_app_context_store_is_resolved_and_readied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Server site (R5): the write store ``build_app_context`` builds carries
    ``build_store``'s resolution AND is READIED. Reached through the current native
    lifespan chain — references no deleted ``_EagerStartupLifespan``."""
    from loremaster.server import LoreServer, build_app_context

    _require_build_store()  # RED-now gate: fails until build_store is extracted (48-A)
    config, slug = _make_config()
    captured = _install_ensure_ready_capture(monkeypatch)
    with pytest.raises(_EnsureReadyAborted):
        await build_app_context(
            server=LoreServer(config),
            embedder=FakeEmbedder(dim=config.embedding.dim),
            manifest_path=tmp_path / f"{slug}-m.db",
            snapshot_root=tmp_path / f"{slug}-snap",
            start_tasks=False,
        )
    _assert_store_resolved(captured["store"], config)
    assert captured.get("ensure_ready_called") is True  # READIED (build_app_context readies)


async def test_index_cli_run_store_is_resolved_and_readied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``index.cli._run`` builds its store via ``build_store`` and READIES it. The
    embedder factory is patched (blessed ``fake_embedder_cli`` pattern) so ``_run``
    reaches the store line without a TEI key / probe."""
    from loremaster.index import cli as index_cli

    _require_build_store()  # RED-now gate: fails until build_store is extracted (48-A)
    config, _slug_unused = _make_config()
    monkeypatch.setattr(
        index_cli,
        "make_embedder_from_config",
        lambda _cfg: FakeEmbedder(dim=config.embedding.dim),
    )
    captured = _install_ensure_ready_capture(monkeypatch)
    args = argparse.Namespace(snapshot_root=str(tmp_path / "snap"), tier=None)
    with pytest.raises(_EnsureReadyAborted):
        await index_cli._run(config, args)
    _assert_store_resolved(captured["store"], config)
    assert captured.get("ensure_ready_called") is True  # READIED (_run readies)


async def test_scout_from_config_store_is_resolved_and_unreadied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``Scout.from_config`` builds its store via ``build_store`` but does NOT ready
    it (readiness is ``Scout.start``'s job). The capture patch PROVES ``ensure_ready``
    is never called, and the store is left unconnected — the behavioral readiness
    difference, not a flag."""
    from loremaster.scout import Scout

    _require_build_store()  # RED-now gate: fails until build_store is extracted (48-A)
    config, _slug_unused = _make_config()
    captured = _install_ensure_ready_capture(monkeypatch)
    scout = Scout.from_config(
        config,
        snapshot_root=tmp_path / "snap",
        embedder=FakeEmbedder(dim=config.embedding.dim),
    )
    store = scout._store
    _assert_store_resolved(store, config)
    assert "ensure_ready_called" not in captured, "Scout.from_config must NOT ready the store"
    assert store._connection is None, "Scout.from_config must leave the store unconnected"


# --------------------------------------------------------------------------- #
# Structural ROUTING pins (the static routing-is-not-sharing catch). RED now:
# each caller currently constructs SurrealStore(...) inline and calls no
# build_store(...). AST-based — robust to comments / import style / line drift.
# --------------------------------------------------------------------------- #


def test_build_app_context_routes_write_store_through_build_store() -> None:
    from loremaster.server import build_app_context

    calls = _direct_call_names(build_app_context)
    assert "build_store" in calls, "build_app_context must obtain its write store from build_store(...)"
    assert "SurrealStore" not in calls, (
        "build_app_context must NOT construct SurrealStore(...) inline (routing-is-not-sharing)"
    )


def test_index_cli_run_routes_store_through_build_store() -> None:
    from loremaster.index.cli import _run

    calls = _direct_call_names(_run)
    assert "build_store" in calls, "index.cli._run must obtain its store from build_store(...)"
    assert "SurrealStore" not in calls, (
        "index.cli._run must NOT construct SurrealStore(...) inline (routing-is-not-sharing)"
    )


def test_scout_from_config_routes_store_through_build_store() -> None:
    from loremaster.scout import Scout

    calls = _direct_call_names(Scout.from_config)
    assert "build_store" in calls, "Scout.from_config must obtain its store from build_store(...)"
    assert "SurrealStore" not in calls, (
        "Scout.from_config must NOT construct SurrealStore(...) inline (routing-is-not-sharing)"
    )


# --------------------------------------------------------------------------- #
# Standing guards for the surrounding R4/R5 invariants (GREEN NOW by design —
# they redden only if the upstream rejection / deleted symbol regresses).
# --------------------------------------------------------------------------- #


def test_config_load_rejects_inline_url_credentials() -> None:
    """R4 UPSTREAM ANCHOR (green now): an inline-credential ``surreal.url`` is rejected
    at config LOAD by ``config._reject_url_userinfo`` — which is WHY ``build_store``
    needs no credential parsing of its own. Reddens if that rejection is removed."""
    payload = _config_payload(_slug())
    payload["surreal"]["url"] = "ws://user:pass@127.0.0.1:18000/rpc"
    with pytest.raises(ValidationError):
        LoreConfig.model_validate(payload)


def test_eager_startup_lifespan_symbol_stays_deleted() -> None:
    """R5 REGRESSION GUARD (green now): the ~150-LOC per-session lifespan apparatus
    was deleted (design §1 R5). The server-site store now builds via the native
    fastmcp lifespan chain build_mcp_server -> _lifespan ->
    _eager_build_or_operator_safe_error -> _eager_build_with_retry -> _build_context
    -> build_app_context. Reddens if ``_EagerStartupLifespan`` is resurrected."""
    import loremaster.server as server_mod

    assert not hasattr(server_mod, "_EagerStartupLifespan"), (
        "the deleted per-session lifespan apparatus must stay deleted (design §1 R5)"
    )
    # The current chain's symbols exist; the server-site store-builder is build_app_context.
    for name in ("build_mcp_server", "_eager_build_with_retry", "build_app_context"):
        assert hasattr(server_mod, name), f"server-site lifespan chain symbol missing: {name}"
