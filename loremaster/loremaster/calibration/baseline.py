"""Calibration corpus loading, sha256 integrity, and the ``baseline.json`` schema.

The frozen ``corpus/`` (``*.txt`` — Python-shaped spans as ``*.py.txt``) and the committed
``baseline.json`` are shipped as package data and loaded via :mod:`importlib.resources`, so
they resolve identically from a source checkout and from the baked production wheel.

The load-bearing guard for the boot calibration engine is
:func:`verify_corpus_integrity`: before it compares live token counts against the baseline,
it proves the on-disk corpus bytes still hash to the sha256s the baseline was generated
from. A single content change invalidates the baseline — the sha256s and this check are the
enforcement of the frozen-corpus invariant, not a comment.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

#: Bump only on a breaking change to the baseline schema.
SCHEMA_VERSION: int = 1
GENERATOR_REL_PATH: str = "scripts/calibration_baseline.py"
#: The model the committed baseline was generated against (see :data:`GENERATION_NOTE`).
BASELINE_MODEL: str = "claude-sonnet-5"
GENERATION_NOTE: str = (
    "YARDSTICK-FINAL 2026-07-04: counts byte-identical across "
    "claude-sonnet-5/claude-opus-4-8/claude-fable-5; baseline is generation-anchored"
)
#: The package that carries the corpus dir + baseline.json as package data.
CORPUS_PACKAGE: str = "loremaster.calibration"
CORPUS_DIR_NAME: str = "corpus"
BASELINE_FILENAME: str = "baseline.json"
#: Every corpus file ends in this suffix (keeps them out of pytest/ruff/mypy collection
#: and out of the lore index — no ``*.py`` / ``*.md`` glob matches ``*.txt``).
CORPUS_SUFFIX: str = ".txt"

_SHA256_HEX_LEN: int = 64
_REQUIRED_TOP_LEVEL_KEYS: tuple[str, ...] = (
    "schema_version",
    "generated_at",
    "generator",
    "model",
    "generation_note",
    "endpoint",
    "files",
    "claude_total",
    "voyage_total",
)
_REQUIRED_FILE_KEYS: tuple[str, ...] = ("claude_tokens", "voyage_tokens", "sha256")


def sha256_hex(data: bytes) -> str:
    """Return the lowercase hex sha256 digest of ``data``."""
    return hashlib.sha256(data).hexdigest()


def dumps_canonical(baseline: Mapping[str, Any]) -> str:
    """Serialize a baseline to canonical, byte-stable JSON.

    Sorted keys + fixed indent make the output deterministic for a given content, so the
    committed ``baseline.json`` only ever changes when the counts change — never on
    incidental key-order churn.
    """
    return json.dumps(dict(baseline), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _corpus_root() -> resources.abc.Traversable:
    return resources.files(CORPUS_PACKAGE).joinpath(CORPUS_DIR_NAME)


def load_corpus() -> dict[str, bytes]:
    """Load every frozen ``*.txt`` corpus file as raw bytes, keyed by filename, sorted.

    Uses :mod:`importlib.resources` so it works from a source checkout and from the baked
    wheel alike.
    """
    root = _corpus_root()
    loaded: dict[str, bytes] = {}
    for entry in root.iterdir():
        if entry.is_file() and entry.name.endswith(CORPUS_SUFFIX):
            loaded[entry.name] = entry.read_bytes()
    return {name: loaded[name] for name in sorted(loaded)}


def load_baseline(path: Path | None = None) -> dict[str, Any]:
    """Load a baseline JSON document.

    Args:
        path: An explicit path to read. When ``None`` (the default), the committed
            ``baseline.json`` is read from package data via :mod:`importlib.resources`.

    Raises:
        ValueError: If the document is not a JSON object.
    """
    if path is None:
        text = resources.files(CORPUS_PACKAGE).joinpath(BASELINE_FILENAME).read_text(encoding="utf-8")
    else:
        text = Path(path).read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("baseline document must be a JSON object")
    return data


def save_baseline(baseline: Mapping[str, Any], path: Path) -> None:
    """Write ``baseline`` to ``path`` as canonical JSON (see :func:`dumps_canonical`)."""
    Path(path).write_text(dumps_canonical(baseline), encoding="utf-8")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _is_plain_int(value: object) -> bool:
    # ``bool`` is an ``int`` subclass — a stray ``True`` must not pass as a token count.
    return isinstance(value, int) and not isinstance(value, bool)


def validate_baseline(obj: object) -> dict[str, Any]:
    """Validate a baseline against the schema, returning it unchanged on success.

    Checks structure, ``schema_version``, per-file entry shape, sha256 hex length, and the
    ``claude_total`` / ``voyage_total`` cross-sums (a total that disagrees with its files is
    a corrupted artifact, not a valid baseline).

    Raises:
        ValueError: On any schema violation, with a message naming the offending field.
    """
    _require(isinstance(obj, Mapping), "baseline must be a mapping")
    assert isinstance(obj, Mapping)  # for the type checker
    for key in _REQUIRED_TOP_LEVEL_KEYS:
        _require(key in obj, f"baseline missing required key: {key!r}")
    _require(
        obj["schema_version"] == SCHEMA_VERSION,
        f"unsupported schema_version {obj['schema_version']!r}; expected {SCHEMA_VERSION}",
    )
    files = obj["files"]
    _require(isinstance(files, Mapping) and bool(files), "baseline 'files' must be a non-empty mapping")

    claude_sum = 0
    voyage_sum = 0
    any_voyage_null = False
    for name, entry in files.items():
        _require(isinstance(entry, Mapping), f"file entry {name!r} must be a mapping")
        for field in _REQUIRED_FILE_KEYS:
            _require(field in entry, f"file entry {name!r} missing {field!r}")
        _require(_is_plain_int(entry["claude_tokens"]), f"file {name!r} claude_tokens must be an int")
        claude_sum += int(entry["claude_tokens"])
        voyage_tokens = entry["voyage_tokens"]
        if voyage_tokens is None:
            any_voyage_null = True
        elif _is_plain_int(voyage_tokens):
            voyage_sum += int(voyage_tokens)
        else:
            raise ValueError(f"file {name!r} voyage_tokens must be an int or null")
        sha = entry["sha256"]
        _require(
            isinstance(sha, str) and len(sha) == _SHA256_HEX_LEN,
            f"file {name!r} sha256 must be a {_SHA256_HEX_LEN}-char hex string",
        )

    _require(
        obj["claude_total"] == claude_sum,
        f"claude_total {obj['claude_total']!r} does not equal the sum of file counts ({claude_sum})",
    )
    expected_voyage_total = None if any_voyage_null else voyage_sum
    _require(
        obj["voyage_total"] == expected_voyage_total,
        f"voyage_total {obj['voyage_total']!r} inconsistent with files (expected {expected_voyage_total!r})",
    )
    return obj if isinstance(obj, dict) else dict(obj)


@dataclass(frozen=True)
class IntegrityResult:
    """The outcome of checking the on-disk corpus against a baseline's sha256s.

    Attributes:
        matched: Files present in both, whose current bytes hash to the baseline sha256.
        mismatched: Files present in both, whose bytes have DRIFTED from the baseline.
        missing: Files the baseline references but the corpus no longer contains.
        unexpected: Files present in the corpus that the baseline does not know about.
    """

    matched: tuple[str, ...]
    mismatched: tuple[str, ...]
    missing: tuple[str, ...]
    unexpected: tuple[str, ...]

    @property
    def ok(self) -> bool:
        """True iff every corpus file matches its baseline sha256 with no missing/extra."""
        return not (self.mismatched or self.missing or self.unexpected)


def verify_corpus_integrity(
    baseline: Mapping[str, Any], corpus: Mapping[str, bytes] | None = None
) -> IntegrityResult:
    """Check the on-disk corpus against a baseline's per-file sha256s.

    Args:
        baseline: A baseline document (its ``files`` map carries the expected sha256s).
        corpus: The corpus bytes to check; defaults to :func:`load_corpus`.

    Returns:
        An :class:`IntegrityResult` classifying every file — the engine reads ``.ok``
        before trusting a count comparison.
    """
    corpus = load_corpus() if corpus is None else corpus
    files: Mapping[str, Any] = baseline.get("files", {})
    baseline_names = set(files)
    corpus_names = set(corpus)

    matched: list[str] = []
    mismatched: list[str] = []
    for name in sorted(baseline_names & corpus_names):
        expected_sha = files[name].get("sha256")
        actual_sha = sha256_hex(corpus[name])
        (matched if expected_sha == actual_sha else mismatched).append(name)

    missing = sorted(baseline_names - corpus_names)
    unexpected = sorted(corpus_names - baseline_names)
    return IntegrityResult(tuple(matched), tuple(mismatched), tuple(missing), tuple(unexpected))
