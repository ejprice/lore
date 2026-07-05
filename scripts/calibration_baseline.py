"""Deterministic generator for the pinned token-calibration ``baseline.json``.

Loads the frozen calibration corpus (``loremaster.calibration``), counts each file's tokens
via the wire-shape-pinned :class:`AsyncClaudeTokenCounter` (Claude) and the pinned
:class:`VoyageTokenCounter` (Voyage), and writes the committed, generation-anchored baseline.

The baseline is EXACT and generation-anchored: ``count_tokens`` is deterministic and
byte-identical across the current model generation, so this is run ONCE against
``claude-sonnet-5`` and the resulting counts stand for any current-generation model.

Key acquisition mirrors ``scripts/token_survey.py``: ``ANTHROPIC_API_KEY`` from the
environment, else parsed from ``--env-file``. Unix philosophy: quiet on success (one summary
line to stdout), loud on failure (a message to stderr and a non-zero exit).

Usage::

    uv run python scripts/calibration_baseline.py --env-file /path/to/.env
    uv run python scripts/calibration_baseline.py --out /tmp/baseline.json --no-voyage
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path
from typing import Any, Protocol

from loremaster.calibration.baseline import (
    BASELINE_FILENAME,
    BASELINE_MODEL,
    CORPUS_PACKAGE,
    GENERATION_NOTE,
    GENERATOR_REL_PATH,
    SCHEMA_VERSION,
    load_corpus,
    save_baseline,
    sha256_hex,
    validate_baseline,
)
from loremaster.calibration.baseline import (
    dumps_canonical as canonical_json,
)
from loremaster.calibration.counting import (
    ANTHROPIC_COUNT_TOKENS_URL,
    DEFAULT_ENV_FILE,
    AsyncClaudeTokenCounter,
    load_api_key,
)
from loresigil.tokens import VoyageTokenCounter

__all__ = ["build_baseline", "canonical_json", "main", "parse_args"]


class _SupportsAsyncCount(Protocol):
    async def count(self, text: str) -> int: ...

    async def aclose(self) -> None: ...


class _SupportsCount(Protocol):
    def count(self, text: str) -> int: ...


async def build_baseline(
    corpus: Mapping[str, bytes],
    claude_counter: _SupportsAsyncCount,
    voyage_counter: _SupportsCount | None,
    *,
    model: str,
    endpoint: str,
    generated_at: str,
) -> dict[str, Any]:
    """Build the baseline document from ``corpus`` — pure given its inputs.

    Files are processed in sorted filename order and the result is fully determined by
    (corpus bytes, the counters' outputs, ``model``, ``endpoint``, ``generated_at``), so two
    runs with the same inputs produce byte-identical JSON modulo ``generated_at``.
    """
    files: dict[str, Any] = {}
    claude_total = 0
    voyage_total = 0
    for name in sorted(corpus):
        data = corpus[name]
        text = data.decode("utf-8")
        claude_tokens = await claude_counter.count(text)
        voyage_tokens = None if voyage_counter is None else voyage_counter.count(text)
        files[name] = {
            "claude_tokens": claude_tokens,
            "voyage_tokens": voyage_tokens,
            "sha256": sha256_hex(data),
        }
        claude_total += claude_tokens
        if voyage_tokens is not None:
            voyage_total += voyage_tokens
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "generator": GENERATOR_REL_PATH,
        "model": model,
        "generation_note": GENERATION_NOTE,
        "endpoint": endpoint,
        "files": files,
        "claude_total": claude_total,
        "voyage_total": None if voyage_counter is None else voyage_total,
    }


def _default_out_path() -> Path:
    """The committed baseline's on-disk location (the calibration package dir)."""
    package_dir = Path(str(resources.files(CORPUS_PACKAGE)))
    return package_dir / BASELINE_FILENAME


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the pinned token-calibration baseline.")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output path for baseline.json (default: the calibration package location)",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=DEFAULT_ENV_FILE,
        help="env file to source ANTHROPIC_API_KEY from when not already exported",
    )
    parser.add_argument("--model", default=BASELINE_MODEL, help="model to count against")
    parser.add_argument(
        "--no-voyage",
        action="store_true",
        help="skip Voyage counts (write null voyage_tokens / voyage_total)",
    )
    return parser.parse_args(argv)


async def _generate(
    corpus: Mapping[str, bytes],
    api_key: str,
    model: str,
    voyage_counter: _SupportsCount | None,
    generated_at: str,
) -> dict[str, Any]:
    counter = AsyncClaudeTokenCounter(api_key, model=model)
    try:
        return await build_baseline(
            corpus,
            counter,
            voyage_counter,
            model=model,
            endpoint=ANTHROPIC_COUNT_TOKENS_URL,
            generated_at=generated_at,
        )
    finally:
        await counter.aclose()


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    out_path = args.out or _default_out_path()

    corpus = load_corpus()
    if not corpus:
        print("calibration_baseline: corpus is empty — nothing to count", file=sys.stderr)
        return 1

    try:
        api_key = load_api_key(args.env_file)
    except RuntimeError as exc:
        print(f"calibration_baseline: {exc}", file=sys.stderr)
        return 1

    voyage_counter = None if args.no_voyage else VoyageTokenCounter()
    generated_at = datetime.now(UTC).isoformat()

    baseline = asyncio.run(_generate(corpus, api_key, args.model, voyage_counter, generated_at))
    validate_baseline(baseline)
    save_baseline(baseline, out_path)

    voyage_summary = "null" if baseline["voyage_total"] is None else str(baseline["voyage_total"])
    print(
        f"calibration_baseline: wrote {out_path} — {len(baseline['files'])} files, "
        f"claude_total={baseline['claude_total']} voyage_total={voyage_summary}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
