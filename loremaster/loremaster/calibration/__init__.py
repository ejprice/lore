"""Token-count calibration probe (P8c).

A PINNED, generation-anchored calibration artifact: a frozen text ``corpus`` of
stratified content shapes, an async Claude token counter whose ``count_tokens``
request shape is byte-identical to ``scripts/token_survey.py``'s reference counter,
and a committed ``baseline.json`` of exact per-file token counts + sha256 integrity
hashes. A boot calibration engine probes the corpus at startup and compares the live
counts against the baseline to detect token-count drift across model generations.
"""

from __future__ import annotations

from loremaster.calibration.baseline import (
    BASELINE_FILENAME,
    BASELINE_MODEL,
    CORPUS_DIR_NAME,
    CORPUS_SUFFIX,
    GENERATION_NOTE,
    GENERATOR_REL_PATH,
    SCHEMA_VERSION,
    IntegrityResult,
    load_baseline,
    load_corpus,
    save_baseline,
    sha256_hex,
    validate_baseline,
    verify_corpus_integrity,
)
from loremaster.calibration.counting import AsyncClaudeTokenCounter, load_api_key

__all__ = [
    "AsyncClaudeTokenCounter",
    "BASELINE_FILENAME",
    "BASELINE_MODEL",
    "CORPUS_DIR_NAME",
    "CORPUS_SUFFIX",
    "GENERATION_NOTE",
    "GENERATOR_REL_PATH",
    "IntegrityResult",
    "SCHEMA_VERSION",
    "load_api_key",
    "load_baseline",
    "load_corpus",
    "save_baseline",
    "sha256_hex",
    "validate_baseline",
    "verify_corpus_integrity",
]
