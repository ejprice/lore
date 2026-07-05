"""Regression tests: ``_read_config_field`` reads config FIELD values, no secret needed.

``_read_config_field`` is used across ``setup`` / ``start`` / ``status`` to read
plain config field VALUES (slug, server port, embedding base_url, and the *name*
of a secret's env-var — never a resolved secret VALUE). It must NOT require any
secret to be resolvable: reading the server port should not depend on
``ANTHROPIC_API_KEY`` being exported. The helper previously ran
``loremaster.config.load_config``, which resolves ``anthropic.api_key_env``
EAGERLY, so on a host where ``ANTHROPIC_API_KEY`` is unset (this one) every
``_read_config_field`` call — and thus ``lore-deploy status`` / ``start`` — broke.
These tests pin the helper to a schema-only read.

Run from this directory (the scripts dir is on sys.path via ``-m``)::

    uv run python -m pytest test_read_config_field.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import lore_deploy
import pytest


def _scaffold_valid_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Scaffold a schema-valid lore.yaml (needs no secret) and return its path."""
    monkeypatch.setattr(lore_deploy, "_loremaster_python", lambda: sys.executable)
    project = tmp_path / "acme_widgets"
    project.mkdir()
    config_path = project / "lore.yaml"
    lore_deploy._scaffold_lore_yaml(project, config_path)
    return config_path


def test_read_config_field_reads_port_without_anthropic_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reading a plain field (server.port) must work with ANTHROPIC_API_KEY absent."""
    config_path = _scaffold_valid_config(tmp_path, monkeypatch)
    # The key is genuinely absent from this host's session env; delete it
    # defensively so the test is deterministic regardless of the ambient env.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    port = lore_deploy._read_config_field(config_path, "c.server.port")
    assert port.isdigit(), f"expected a numeric server port, got {port!r}"


def test_read_config_field_reads_slug_without_anthropic_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reading project.slug must not require a resolved Anthropic secret."""
    config_path = _scaffold_valid_config(tmp_path, monkeypatch)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    slug = lore_deploy._read_config_field(config_path, "c.project.slug")
    assert slug == "acme_widgets"


def test_read_config_field_reads_secret_env_var_name_not_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The helper returns the NAME of a secret's env-var, never a resolved secret.

    Pins the reasoning behind the schema-only switch: every caller reads the
    env-var *name* (e.g. ``embedding.api_key_env == 'LORE_TEI_KEY'``), so no secret
    VALUE is ever needed — requiring one to read the name was the bug.
    """
    config_path = _scaffold_valid_config(tmp_path, monkeypatch)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    name = lore_deploy._read_config_field(config_path, "c.embedding.api_key_env")
    assert name == "LORE_TEI_KEY"
