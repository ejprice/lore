"""Test-only twin of ``lore_deploy._read_config_field`` that answers by MEANING.

``_read_config_field(config_path, expr)`` evaluates a Python expression over the
schema-validated ``LoreConfig`` bound to ``c``, in a loremaster subprocess, and returns
the printed value. Tests used to replace it with stubs that answered by SPELLING
(``"port" in expr`` -> a port), which coupled production to how its expressions are
written: an equivalent rewrite (``__import__`` in an expression, two reads merged into
one) broke tests while behaviour stayed identical (#165 cold audit, T8).

:class:`ConfigReaderFake` instead holds a real config DOCUMENT and evaluates ``expr``
against a real ``LoreConfig`` built by production's own snippet
(:func:`lore_deploy._schema_load_snippet`), in-process. So:

* the construction is production's, not a copy: a change to the snippet (new imports,
  a different validation entry point) reaches the fake unchanged;
* the expression's value is the value its MEANING has over the declared config, however
  production spells it;
* the return is ``print``'s output stripped, exactly as the real reader returns the
  subprocess's stripped stdout (multi-argument ``print`` included);
* any failure — a document that fails validation, an expression that raises or does not
  compile — raises ``RuntimeError`` naming the expression, as the real reader does on a
  non-zero exit.

Known bound, deliberate: the fake answers from the document it was GIVEN and never reads
``config_path`` (tests keep a placeholder ``lore.yaml`` there for the pre-flight presence
check). A production build that read the wrong config file would therefore not be caught
by a test using this fake; ``test_lore_deploy.TestConfigReaderFakeOracle`` pins the fake
against the real subprocess reader over the same file. Every call is recorded in
:attr:`ConfigReaderFake.calls` with the path it was given.

Lives in ``scripts/`` (not a ``test_*`` module) so both skill test trees import it the
way they import ``lore_deploy``: pytest's ``-m`` run from ``scripts/`` puts this directory
on ``sys.path``, and ``tests/`` inserts it explicitly.
"""

from __future__ import annotations

import contextlib
import copy
import io
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import lore_deploy
import pytest
import yaml

# The static tiers this repo's own ``lore.yaml`` declared (recorded 2026-10-31 at
# 6f0f09f): real tier names, including a pair where one is a prefix-sharing sibling of
# another (``surrealdb-docs`` / ``surrealql-tests``), so a fixture never uses a
# convenience name that a token-matching bug could not tell apart.
RECORDED_STATIC_TIERS: tuple[str, ...] = ("surrealdb-docs", "surrealql-tests", "spectron-docs")

# The DEFAULT ``surreal.url``: the scaffold's ``ws://host:port/rpc`` SHAPE on a
# deliberately DEAD endpoint (loopback port 9, the discard service, which nothing on a dev
# host serves), never the scaffold's real value. 18500 is the PRODUCTION lore-surreal
# store and repo law forbids pointing tests at it. Because this fake answers ``surreal.url``
# with a real URL (the old stubs answered junk), any test that leaves ``_probe_surreal``
# unstubbed would really ``GET /health`` this endpoint, so a dead one makes that probe
# fail closed (connection refused) instead of touching production. A test that needs a
# prod-shaped value passes ``surreal_url=`` explicitly.
DEAD_SURREAL_URL = "ws://127.0.0.1:9/rpc"
# The MCP mount path every scaffolded config serves.
RECORDED_SERVER_PATH = "/mcp"
RECORDED_SERVER_HOST = "127.0.0.1"


def realistic_config_document(
    *,
    slug: str = "lore",
    server_port: int = lore_deploy.DEFAULT_PORT_BASE,
    server_path: str = RECORDED_SERVER_PATH,
    surreal_url: str = DEAD_SURREAL_URL,
    static_tiers: Sequence[str] = (),
) -> dict[str, Any]:
    """A schema-valid ``lore.yaml`` document, production-SHAPED (never production-sourced).

    Values were recorded from this repo's ``lore.yaml`` on 2026-10-31 (6f0f09f): one
    live root plus, on request, ``static`` roots in the real static-root shape
    (``source`` / ``version`` / ``provider``). Only the fields a deploy test branches on
    are parameters; everything else is the recorded value.

    Args:
        slug: ``project.slug``.
        server_port: ``server.port`` (an int, the unit the schema stores).
        server_path: ``server.path`` (the MCP mount, starting with ``/``).
        surreal_url: ``surreal.url`` (a ``ws(s)://host:port/rpc`` endpoint); defaults to
            :data:`DEAD_SURREAL_URL`, never the production store.
        static_tiers: Tier names to declare as ``watch: static`` roots, in order.

    Returns:
        A fresh, mutable mapping (callers may edit it before building a fake).
    """
    roots: list[dict[str, Any]] = [
        {
            "tier": slug,
            "watch": "live",
            "path": "/workspace",
            "include": ["**/*.py", "**/*.md"],
        }
    ]
    roots += [
        {
            "tier": tier,
            "watch": "static",
            "source": f"/home/lore/docker/mcp/lore-corpora/{tier}",
            "version": "3.2",
            "provider": "local_directory",
            "include": ["**/*.mdx"],
        }
        for tier in static_tiers
    ]
    return {
        "schema_version": 1,
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://mbpsrv.firehawktransam.org:8080",
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
            "query_prompt_name": "query",
            "document_prompt_name": "document",
        },
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY", "yardstick_model": "claude-sonnet-5"},
        "surreal": {
            "url": surreal_url,
            "namespace": "lore",
            "user_env": "SURREAL_USER",
            "password_env": "SURREAL_PASS",
        },
        "roots": roots,
        "include": ["**/*.py", "**/*.md"],
        "exclude_dirs": [".git", ".venv", "__pycache__", ".pytest_cache"],
        "exclude_globs": ["**/*.json", "uv.lock"],
        "chunkers": {
            ".py": {"chunker": "python_ast"},
            ".md": {"chunker": "markdown"},
            ".mdx": {"chunker": "markdown"},
        },
        "watcher": {
            "enabled": True,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": RECORDED_SERVER_HOST, "path": server_path, "port": server_port},
    }


def write_config_document(document: Mapping[str, Any], config_path: Path) -> Path:
    """Serialise ``document`` to ``config_path`` as YAML (the form the real reader parses)."""
    config_path.write_text(yaml.safe_dump(dict(document), sort_keys=False), encoding="utf-8")
    return config_path


class ConfigReaderFake:
    """In-process, meaning-based stand-in for ``lore_deploy._read_config_field``.

    Holds one config document, serialised once to a private file under ``store_dir``;
    every call execs production's ``_schema_load_snippet`` over that file followed by
    ``print(<expr>)`` and returns the captured output stripped — the real reader's
    pipeline without the subprocess. See the module docstring for the matched
    behaviours and the one deliberate bound (``config_path`` is recorded, not read).
    """

    _DOCUMENT_FILENAME = "config-reader-fake.lore.yaml"

    def __init__(self, document: Mapping[str, Any], store_dir: Path) -> None:
        store_dir.mkdir(parents=True, exist_ok=True)
        self.document: dict[str, Any] = copy.deepcopy(dict(document))
        self.document_path = write_config_document(
            self.document, store_dir / self._DOCUMENT_FILENAME
        )
        # Every (config_path, expr) the code under test asked for, in call order.
        self.calls: list[tuple[Path, str]] = []

    def __call__(self, config_path: Path, expr: str) -> str:
        """Evaluate ``expr`` over the held config; same return/raise shape as the real reader."""
        self.calls.append((config_path, expr))
        code = f"{lore_deploy._schema_load_snippet(self.document_path)};print({expr})"
        captured = io.StringIO()
        try:
            with contextlib.redirect_stdout(captured):
                # Deliberate: this mirrors the real reader's ``python -c <code>`` in-process,
                # with a fresh ``__main__``-like namespace per call.
                exec(code, {"__name__": "__main__"})
        except Exception as error:
            raise RuntimeError(
                f"failed to read {expr!r} from {config_path}: {type(error).__name__}: {error}"
            ) from error
        return captured.getvalue().strip()

    @classmethod
    def install(
        cls,
        monkeypatch: pytest.MonkeyPatch,
        store_dir: Path,
        document: Mapping[str, Any] | None = None,
        **document_fields: Any,
    ) -> ConfigReaderFake:
        """Build a fake and patch it over ``lore_deploy._read_config_field``.

        Pass a full ``document``, or keyword fields for :func:`realistic_config_document`
        (``server_port=``, ``static_tiers=``, ...), never both.
        """
        if document is not None and document_fields:
            raise TypeError("pass either a document or realistic_config_document fields, not both")
        fake = cls(document if document is not None else realistic_config_document(**document_fields),
                   store_dir)
        monkeypatch.setattr(lore_deploy, "_read_config_field", fake)
        return fake
