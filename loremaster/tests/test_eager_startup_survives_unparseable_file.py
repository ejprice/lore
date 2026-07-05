"""Contract test: ``build_app_context(start_tasks=True)`` survives a poisoned tree.

RESTORATION (ledger #33 test-restoration audit): the P5-C3b indexer/reconcile
port (see ``test_indexer_chunker_fault_isolation.py``'s module docstring)
explicitly DROPPED ``TestEagerStartupSurvivesUnparseableFile`` — the
SERVER-level end-to-end test for the ORIGINAL production crash site (deploying
lore over the Odoo 15 tree: ``odoo/tests/dummy.xml`` ships comment-only content,
the XML chunker's ``ParseError`` propagated UNCAUGHT out of
``build_app_context``'s eager initial sweep, killing the container on every
restart — three retries, same file, container exit). ``build_app_context``'s
migration onto the unified SurrealDB write stack (P5) was a separate concern
from the indexer/reconcile/watcher rewiring that port covered, so the class was
dropped rather than ported blind. This file restores it against the CURRENT
Surreal composition — the same server seam ``test_cli.py`` / ``test_extension.py``
/ ``test_resilient_db.py`` drive: a real throwaway SurrealDB database via
``_surreal_harness`` (Qdrant retired from the boot path at P8a), with a
:class:`~loresigil.testing.FakeEmbedder` substituted for the network TEI call.

Fixture note — malformed XML, not a malformed ``.py``: the ORIGINAL crash
fixture is byte-for-byte reproduced here (a comment-only ``dummy.xml``) rather
than a malformed Python file, because ``lorescribe.python_ast.PythonAstChunker``
DEGRADES a ``SyntaxError`` to a sliding-window chunk fallback instead of raising
(see ``PythonAstChunker.chunk``'s docstring: "On SyntaxError, degrades to
sliding-window chunks") — a malformed ``.py`` would index SUCCESSFULLY today via
that fallback and would never exercise the chunk-exception isolation path this
test guards. The unparseable-XML fixture is the shape that still reaches it (the
``xml`` chunker has no such fallback — an unparseable document raises).

The indexer-level isolation itself (a chunker exception marks ONE file
``failed``, siblings still index, the sweep completes without crashing) is
already covered fast and thoroughly by ``test_indexer_chunker_fault_isolation.py``
against the async Surreal fakes; this file pins ONLY the ADDITIONAL server-seam
claim those unit tests cannot see — that the isolation holds all the way through
``build_app_context``'s REAL eager-startup sweep (``watcher.run_sweep`` ->
``ReconcileEngine.reconcile`` -> ``indexer.index_tier``), the exact call chain
the production crash climbed.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from _surreal_harness import drop_database, make_env, surreal_password, surreal_url, surreal_user
from loremaster.config import LoreConfig
from loremaster.server import LoreServer
from loresigil.testing import FakeEmbedder

# Production embedding dimensionality (matches the rest of the loremaster suite).
_DIM = 2048

# The namespace this test's throwaway SurrealDB database lives under (mirrors
# test_cli.py / test_extension.py's harness-isolation convention).
_SURREAL_TEST_NAMESPACE = "lore_test"

# The env-var *names* the default SurrealConfig references credentials by.
_SURREAL_USER_ENV = "SURREAL_USER"
_SURREAL_PASS_ENV = "SURREAL_PASS"

# Byte-for-byte the content of the real /odoo/odoo/tests/dummy.xml (verified
# against the production Odoo 15 source tree): one comment line + newline, no
# root element — the ORIGINAL crash fixture ("Should not be read by anyone").
_DUMMY_XML_CONTENT = "<!-- Should not be read by anyone -->\n"
_DUMMY_XML_PATH = "odoo/tests/dummy.xml"

# A healthy sibling proving the sweep completes and indexes normally around the
# poison file — a live server over a poisoned tree, not a dead container.
_HEALTHY_PY_PATH = "models/sale_margin.py"
_HEALTHY_PY_CONTENT = '''\
"""Sale-order margin helpers."""


def order_margin(price_total, cost_total):
    """The absolute margin on one order."""
    return price_total - cost_total
'''


def _write(base: Path, rel_path: str, text: str) -> None:
    """Create parents and write ``text`` under ``base / rel_path`` (UTF-8)."""
    path = base / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _build_poisoned_corpus(root: Path) -> None:
    """A live tree with ONE malformed XML file and ONE healthy Python file."""
    _write(root, _DUMMY_XML_PATH, _DUMMY_XML_CONTENT)
    _write(root, _HEALTHY_PY_PATH, _HEALTHY_PY_CONTENT)


def _slug() -> str:
    """A per-test slug -> throwaway SurrealDB database."""
    return f"test_{uuid.uuid4().hex}"


def _config(*, slug: str, live_path: Path) -> LoreConfig:
    """A validated single-live-root :class:`LoreConfig` mirroring the Odoo-deploy
    shape that surfaced the bug: python AND xml files in one live tier, wired to
    the CURRENT SurrealDB write stack (a throwaway per-test database on the dev
    server, named after the test's unique slug — the same convention
    ``test_cli.py`` / ``test_extension.py`` use).
    """
    payload: dict[str, Any] = {
        "schema_version": 1,
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://tei.example:8080",
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": _DIM,
            "truncate": False,
            "max_input_tokens": 8192,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": "LORE_TEI_KEY",
            "tokenizer": "voyage-4-nano",
        },
        "surreal": {
            "url": surreal_url(),
            "namespace": _SURREAL_TEST_NAMESPACE,
            "database": slug,
            "user_env": _SURREAL_USER_ENV,
            "password_env": _SURREAL_PASS_ENV,
        },
        "roots": [
            {
                "tier": "custom",
                "watch": "live",
                "path": str(live_path),
                "include": ["**/*.py", "**/*.xml"],
                "exclude": [],
            }
        ],
        "include": [],
        "exclude_dirs": [".git", ".venv", "__pycache__"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}, ".xml": {"chunker": "xml"}},
        "watcher": {
            "enabled": True,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9201},
    }
    return LoreConfig.model_validate(payload)


class TestEagerStartupSurvivesUnparseableFile:
    """``build_app_context(start_tasks=True)`` completes over a poisoned tree.

    This is the level the production crash happened at: the eager lifespan's
    initial sweep (``watcher.run_sweep`` -> ``ReconcileEngine.reconcile`` ->
    ``indexer.index_tier``) hit ``dummy.xml`` and the ``ParseError`` climbed all
    the way out of ``build_app_context``, killing startup. Pinning here (not
    just at the indexer's own fault-isolation level, already covered by
    ``test_indexer_chunker_fault_isolation.py``) means the regression cannot
    re-enter via a different call site on the startup/reconcile path.
    """

    async def test_eager_startup_build_completes_and_reports_the_failure(
        self, tmp_path: Path
    ) -> None:
        from loremaster.server import build_app_context

        slug = _slug()
        root = tmp_path / "live"
        _build_poisoned_corpus(root)
        config = _config(slug=slug, live_path=root)
        server = LoreServer(config)

        # The write-path SurrealDB credentials resolve by env-var NAME at
        # construction — export the dev-server's harness credentials
        # (idempotent: the same values the harness itself resolves).
        os.environ.setdefault(_SURREAL_USER_ENV, surreal_user())
        os.environ.setdefault(_SURREAL_PASS_ENV, surreal_password())

        app_context = await build_app_context(
            server=server,
            embedder=FakeEmbedder(dim=_DIM),
            manifest_path=tmp_path / "m.db",
            snapshot_root=tmp_path / "snap",
            start_tasks=True,
        )
        try:
            # The build survived AND is honest about the poison: the status
            # roll-up counts the poison file failed and the healthy file
            # indexed — a live server over a poisoned tree, not a dead
            # container.
            status = await app_context.indexer.index_status()
            assert status.files_failed == 1
            assert status.files_indexed >= 1
        finally:
            await app_context.aclose()
            await drop_database(make_env(database=slug, dim=_DIM))
