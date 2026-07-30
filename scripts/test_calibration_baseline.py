"""Tests for ``scripts/calibration_baseline.py`` — the deterministic baseline generator.

Covers: schema-valid output, determinism (same input -> byte-identical JSON, modulo
``generated_at``), voyage-optional counting, canonical serialization stability, and the
``main`` wiring (with the network + tokenizer stubbed out, so the test is hermetic).
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any

# The generator lives in ``scripts/`` (not a package) — make it importable. Mirrors
# ``scripts/test_token_survey.py``.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import calibration_baseline as cb  # noqa: E402  (scripts/ is not a package)
from loremaster.calibration import baseline as bl  # noqa: E402
from pydantic import SecretStr  # noqa: E402

_CORPUS = {"b.py.txt": b"def f():\n    return 1\n", "a.md.txt": b"# title\n\nprose here.\n"}
_ENDPOINT = "https://api.anthropic.com/v1/messages/count_tokens"


class _FakeClaudeCounter:
    """Deterministic async counter: token count is a fixed function of the text."""

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        self.model = _kwargs.get("model", "claude-sonnet-5")

    async def count(self, text: str) -> int:
        return len(text) + 100

    async def aclose(self) -> None:
        return None


class _FakeVoyageCounter:
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        pass

    def count(self, text: str) -> int:
        return len(text)


def _build(generated_at: str, *, with_voyage: bool = True) -> dict[str, Any]:
    voyage = _FakeVoyageCounter() if with_voyage else None
    return asyncio.run(
        cb.build_baseline(
            _CORPUS,
            _FakeClaudeCounter(),
            voyage,
            model="claude-sonnet-5",
            endpoint=_ENDPOINT,
            generated_at=generated_at,
        )
    )


class TestBuildBaseline:
    def test_output_validates_against_schema(self) -> None:
        result = _build("2026-07-04T00:00:00+00:00")
        assert bl.validate_baseline(result) is result

    def test_files_sorted_and_totals_correct(self) -> None:
        result = _build("2026-07-04T00:00:00+00:00")
        assert list(result["files"]) == sorted(_CORPUS)
        assert result["claude_total"] == sum(f["claude_tokens"] for f in result["files"].values())
        assert result["voyage_total"] == sum(f["voyage_tokens"] for f in result["files"].values())

    def test_per_file_sha256_matches_corpus_bytes(self) -> None:
        result = _build("2026-07-04T00:00:00+00:00")
        for name, data in _CORPUS.items():
            assert result["files"][name]["sha256"] == bl.sha256_hex(data)

    def test_voyage_none_when_no_voyage_counter(self) -> None:
        result = _build("2026-07-04T00:00:00+00:00", with_voyage=False)
        assert result["voyage_total"] is None
        assert all(f["voyage_tokens"] is None for f in result["files"].values())
        bl.validate_baseline(result)  # still valid

    def test_deterministic_modulo_generated_at(self) -> None:
        first = _build("2026-07-04T00:00:00+00:00")
        second = _build("2999-01-01T12:34:56+00:00")
        first["generated_at"] = "X"
        second["generated_at"] = "X"
        assert cb.canonical_json(first) == cb.canonical_json(second)


class TestCanonicalJson:
    def test_is_stable_and_sorted(self) -> None:
        result = _build("2026-07-04T00:00:00+00:00")
        first = cb.canonical_json(result)
        second = cb.canonical_json(result)
        assert first == second
        assert first.endswith("\n")
        # Round-trips.
        assert json.loads(first) == result


class TestMainWiring:
    def test_main_writes_valid_baseline_quietly(self, tmp_path: Any, monkeypatch: Any, capsys: Any) -> None:
        # Returns a SecretStr, as the real ``load_api_key`` does (#211) — a fake that
        # hands back a bare ``str`` tests a seam production does not have.
        monkeypatch.setattr(cb, "load_api_key", lambda *a, **k: SecretStr("dummy-key"))
        monkeypatch.setattr(cb, "AsyncClaudeTokenCounter", _FakeClaudeCounter)
        monkeypatch.setattr(cb, "VoyageTokenCounter", _FakeVoyageCounter)
        out = tmp_path / "baseline.json"

        exit_code = cb.main(["--out", str(out)])

        assert exit_code == 0
        data = json.loads(out.read_text(encoding="utf-8"))
        bl.validate_baseline(data)
        assert data["model"] == "claude-sonnet-5"
        assert 8 <= len(data["files"]) <= 15  # counted the real frozen corpus
        # Unix philosophy: quiet on success — at most one summary line.
        captured = capsys.readouterr()
        assert captured.out.strip().count("\n") == 0
