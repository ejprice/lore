"""Regression tests: the scaffolded lore.yaml must be VALID against LoreConfig.

The scaffold's template drifted from the config contract — it emitted a stale
``qdrant:`` block (rejected by the strict ``extra="forbid"`` model) and no
``anthropic:`` block (REQUIRED since P8c), so a freshly scaffolded lore.yaml
failed validation and fresh-project onboarding was broken. These tests scaffold
into a tmp dir and round-trip the result through the REAL
``loremaster.config.load_config`` to pin the emitted template to the live schema.

Run from this directory (the scripts dir is on sys.path via ``-m``)::

    uv run python -m pytest test_scaffold_config.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import lore_deploy
import pytest
from loremaster.config import load_config


@pytest.fixture(autouse=True)
def _dummy_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    """Give the template's env-var names dummy values for the round-trip.

    ``load_config`` resolves ``anthropic.api_key_env`` EAGERLY, so the round-trip
    needs ``ANTHROPIC_API_KEY`` set; the surreal/TEI keys are resolved lazily by
    their own consumers, but we set them too so the test never depends on the
    ambient shell for any secret the scaffolded template references.
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy-anthropic-key")
    monkeypatch.setenv("SURREAL_USER", "root")
    monkeypatch.setenv("SURREAL_PASS", "root")
    monkeypatch.setenv("LORE_TEI_KEY", "dummy-tei-key")


def _scaffold(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Scaffold a lore.yaml into ``tmp_path`` and return its path.

    Points the scaffold's internal schema-validation subprocess at the test
    interpreter (which can import loremaster), so the check is hermetic w.r.t. the
    worktree layout instead of depending on a fixed ``.venv`` path.
    """
    monkeypatch.setattr(lore_deploy, "_loremaster_python", lambda: sys.executable)
    project = tmp_path / "acme_widgets"
    project.mkdir()
    config_path = project / "lore.yaml"
    lore_deploy._scaffold_lore_yaml(project, config_path)
    return config_path


def test_scaffolded_config_round_trips_through_load_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The emitted lore.yaml parses through the REAL LoreConfig, end to end."""
    config_path = _scaffold(tmp_path, monkeypatch)
    config = load_config(config_path)
    assert config.project.slug == "acme_widgets"


def test_scaffold_emits_no_qdrant_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The retired ``qdrant:`` block must never be emitted (strict model rejects it)."""
    config_path = _scaffold(tmp_path, monkeypatch)
    assert "qdrant" not in config_path.read_text(encoding="utf-8")


def test_scaffold_emits_required_anthropic_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The REQUIRED anthropic block is present with the right env-var NAME."""
    config_path = _scaffold(tmp_path, monkeypatch)
    config = load_config(config_path)
    assert config.anthropic.api_key_env == "ANTHROPIC_API_KEY"
    assert config.anthropic.yardstick_model == "claude-sonnet-5"


def test_scaffold_emits_surreal_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The surreal block is present with the live env-var-name conventions."""
    config_path = _scaffold(tmp_path, monkeypatch)
    config = load_config(config_path)
    assert config.surreal.user_env == "SURREAL_USER"
    assert config.surreal.password_env == "SURREAL_PASS"
    # database omitted → derives from the slug via effective_surreal_database.
    assert config.surreal.database is None
    assert config.effective_surreal_database == "acme_widgets"
