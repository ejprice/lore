"""Extract and hash the ANSWER SURFACE — the exact text an informant must reproduce per key.

**PROVENANCE.** Written by `adversary-exhibit-11ib-1` (2026-07-28) and committed here rather than
left in scratch: it is the instrument that turned "six wrong packages happen to score the same"
into "five wrong packages are BYTE-IDENTICAL on every surface the battery grades", which is the
difference between a coincidence and a mechanism. Extended by `exhibit-11ib-1` to the fix wave's
ten keys.

Narrower than a section: only the lines `KEY.md`'s *"Correct"* and *"Carried by"* clauses demand
be reproduced. If a wrong package's answer surface is byte-identical to the honest one, then no
informant answer can differ, and an identical score is a MECHANISM, not luck. Everything outside
this surface is ungraded by construction — which is the finding.

⚠ The hash is a DISCRIMINATION check, not a quality check. Two packages with different hashes may
still both be wrong; two with the same hash cannot be told apart by any reader, which is the only
claim made here.

Usage: python keyed_surface.py <baseline-dir> [<package-dir> ...]
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

#: ``key -> (file, line prefixes KEY.md requires the informant to reproduce)``. A package that
#: relocates content is EXPECTED to hash differently — that is the point of naming the file.
ANSWER_LINES: dict[str, tuple[str, tuple[str, ...]]] = {
    "key1 acceptance": (
        "01-summary.md",
        ("| **(1)** `F_portable` false-fire rate", "| **(2)** legacy nonsense catch"),
    ),
    "key2 shape": (
        "02-per-group-distributions.md",
        ("| **Δ** |", "p5–p95 width:", "| `human-prose` | `+0.111111`",
         "| `legacy-nonsense` | `+0.030303`"),
    ),
    "key3 determinism": (
        "07-determinism-and-run-receipt.md",
        ("## `determinism_leg = within_ci_by_construction`",
         "1. Change detection must key on `corpus_content_digest` equality",
         "4. The `bit_identical_cold` outcome is what would license"),
    ),
    "key4 drops": (
        "08-drop-diagnostics.md",
        ("| `source_chunk_absent_from_kprime`", "| `sibling_chunk_same_file_only`",
         "| `holdout_file_exclusion_applied`", "| **total self-retrieval drop** |"),
    ),
    "key5 live-traffic bound": (
        "06-per-hit-decomposition.md",
        ("> **Bound (i) — this measures the SURVEY's query mix",),
    ),
    # FIX-WAVE additions — the surfaces the five new keys grade.
    "key6 commensurability bound": (
        "02-per-group-distributions.md",
        ("> **Bound (iii) — the two instruments' cosines are NOT commensurable",),
    ),
    "key7 independence bound": (
        "01-summary.md",
        ("> **Bound (iv) — the acceptance was NOT evaluated on held-out data",),
    ),
    "key8 per-query rows": (
        # Every row, not a sentinel line: a truncated file must not hash as an intact one.
        "per-query-rows.jsonl",
        ('{"_banner"', '{"_synthetic"'),
    ),
    "key9 reconciliation inputs": (
        "03-anchor-rates.md",
        ("| `human-prose` | 12 | 8 | 4 |", "| **all** | **815** | **39** | **776** |"),
    ),
    "key10 glossary": (
        "00-README.md",
        ("| `R-PACKAGE` |", "| `#180` |", "| `F7.2` |"),
    ),
}


def answer_surface(root: Path) -> str:
    """The concatenated keyed lines, with ABSENT recorded explicitly rather than skipped."""
    chunks = []
    for label, (filename, prefixes) in ANSWER_LINES.items():
        path = root / filename
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        lines = text.splitlines()
        for prefix in prefixes:
            found = [line for line in lines if line.startswith(prefix)]
            chunks.append(f"[{label}|{prefix[:34]}] " + (" ¶ ".join(found) if found else "ABSENT"))
    return "\n".join(chunks)


if __name__ == "__main__":
    baseline = answer_surface(Path(sys.argv[1]))
    digest = hashlib.sha256(baseline.encode()).hexdigest()[:16]
    print(f"{digest}  {sys.argv[1]}  BASELINE ({len(baseline)} bytes)")
    for argument in sys.argv[2:]:
        text = answer_surface(Path(argument))
        verdict = "ANSWER SURFACE IDENTICAL" if text == baseline else "answer surface DIFFERS"
        print(f"{hashlib.sha256(text.encode()).hexdigest()[:16]}  {argument}  {verdict}")
