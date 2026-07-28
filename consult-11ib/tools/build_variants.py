"""Derive every non-honest package from `honest/` — the shipped control legs AND the attack set.

**PROVENANCE.** The `W*` builders are `adversary-exhibit-11ib-1`'s (2026-07-28); they are the
instrument that found the ten missing keys, and they lived only in
`/home/ejprice/scratch-adversary-11ib/`, an unrecoverable address. Committed here so a future
adversary does not re-derive them. `exhibit-11ib-1` added `build_degraded`, `build_appendix` and
`build_w7`, and re-pointed four mutations at strings the fix wave rewrote.

Two output families, and the difference matters:

- **CONTROL LEGS (`degraded/`, `appendix/`)** are SHIPPED beside `honest/`. They are handed to
  informants. `degraded` samples "bounds absent"; `appendix` samples "bounds present but in one
  canonical section" — the middle point of RAISED-A1's three-point fork, which the battery could
  not previously sample.
- **ATTACK PACKAGES (`wrong/W1..W7`)** are NEVER handed to an informant. They are the adversary's
  wrong builds, and their only job is to be scored by `grade.py`: a battery that scores them the
  same as `honest` is not measuring anything.

Deriving all of them mechanically, rather than hand-editing, is what keeps them in sync with an
`honest/` package that is still changing. Every edit is ASSERTED to land: an edit that silently
no-ops would make the next step print a score that reads as a finding when nothing was mutated
(the #194 class), so `sub` raises rather than returning.

Usage:
    python build_variants.py --variants <honest-dir> <package-root>
    python build_variants.py --wrong    <honest-dir> <output-root>
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

BANNER = "> **SYNTHETIC EXHIBIT — no value in this document is a measurement**"


def fresh_copy(honest: Path, destination: Path) -> Path:
    """A byte copy of the honest package at ``destination``, replacing whatever was there."""
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(honest, destination)
    return destination


def sub(package: Path, filename: str, old: str, new: str) -> None:
    """Replace ``old`` with ``new`` in a package file, ASSERTING the edit landed."""
    path = package / filename
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"MUTATION DID NOT LAND: {package.name}/{filename}: {old[:70]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def cut(package: Path, filename: str, old: str) -> str:
    """Delete a block, ASSERTING it was there, and return it for relocation."""
    sub(package, filename, old, "")
    return old


def append(package: Path, filename: str, text: str) -> None:
    path = package / filename
    path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")


# =======================================================================================
# THE SHIPPED CONTROL LEGS
# =======================================================================================

#: Every in-claim bound block in the honest package, as ``(filename, exact text)``. One list,
#: consumed by BOTH control legs — `degraded` deletes them, `appendix` relocates them — so the
#: two legs can never disagree about what counts as a bound.
BOUND_BLOCKS: tuple[tuple[str, str], ...] = (
    (
        "01-summary.md",
        "**Measured population — read this before quoting anything below.** Every rate on this page is\n"
        "computed over the SURVEY's query set (1740 queries across six groups, `02`). It is not a\n"
        "sample of live production traffic, and nothing in this package supports a statement about\n"
        "what fraction of live queries would fire the absence verdict. Packet 35 is the instrument\n"
        "that would measure that; it has not run.\n\n",
    ),
    (
        "01-summary.md",
        "Both acceptance rates are properties of the survey's labeled sets. Neither is an estimate of\n"
        "how often the absence verdict would fire in production — that population was not sampled here\n"
        "(packet 35).\n\n",
    ),
    (
        "01-summary.md",
        "⚠ **That scalar is DIMENSIONLESS and it is not a quality delta.** The two floors are thresholds\n"
        "in two different embedding geometries; the package carries an `embedding_schema_fingerprint` for\n"
        "the portable instrument and none for the legacy one, so the two scales cannot be checked for\n"
        "coincidence. It may not be re-expressed as an improvement, a regression or a percentage —\n"
        "`02`'s bound (iii) states this in full, beside the tables it governs. What `02` does carry is\n"
        "the per-percentile and per-group SHAPE of the paired difference, which this single number\n"
        "averages away.\n\n",
    ),
    (
        "03-anchor-rates.md",
        "These rates are properties of the survey's query mix. A different query mix — production\n"
        "traffic, for one — would produce different anchor rates and therefore a different rate of\n"
        "absence verdicts, and this package does not measure that mix.\n",
    ),
)

#: Bound (i) and (ii), which live together in `06` and move together.
BOUND_06 = (
    "> **Bound (i) — this measures the SURVEY's query mix, not live traffic.** The 964\n"
    "> `verdict_not_fired_queries` above are the survey's own six groups in the survey's own\n"
    "> proportions. **This package\n"
    "> cannot tell you what fraction of live production queries would fire the absence verdict, or\n"
    "> what fraction of live shown hits would be over-flagged**, and no number here may be\n"
    "> re-expressed as such a fraction: the query mix that produced these rates was constructed, not\n"
    "> sampled from traffic. Packet 35 is the instrument that would measure the live population. It\n"
    "> has not run.\n>\n"
    "> **Bound (ii) — shown-k slice only.** Every number on this page covers ranks 1–10. The\n"
    "> instrument captures `k' = 30` hits per query; ranks 11–30 are excluded here by design,\n"
    "> because they were never shown to a caller and cannot be over-flagged.\n\n"
)


def build_degraded(honest: Path, root: Path) -> Path:
    """The authored control: bounds REMOVED, acceptance values REMOVED, determinism collapsed."""
    package = fresh_copy(honest, root / "degraded")
    for filename, block in BOUND_BLOCKS:
        cut(package, filename, block)
    cut(package, "06-per-hit-decomposition.md", BOUND_06)
    _cut_block(package, "02-per-group-distributions.md", "> **Bound (iii)", "\n\nBoth instruments")
    _cut_block(package, "01-summary.md", "> **Bound (iv)", "\n\n## Validity floors")
    # Acceptance legs as bare verdicts: the receipt tables ARE the values, so they go too.
    _cut_block(package, "01-summary.md", "## `choose_cosine_floor` selection receipts",
               "\n\n## Pre-registered acceptance")
    sub(package, "01-summary.md",
        "## Pre-registered acceptance — both legs, with their values",
        "## Pre-registered acceptance")
    sub(package, "01-summary.md",
        "| leg | bar | measured | verdict |\n|---|---|---|---|\n"
        "| **(1)** `F_portable` false-fire rate against the legacy labeled real union | **≤ 5%** "
        "(`0.05`) | `11 / 357` = **`0.030812`** | **PASS** |\n"
        "| **(2)** legacy nonsense catch at `F_portable` | **≥ 60%** (`0.60`) | `321 / 345` = "
        "**`0.930435`** | **PASS** |",
        "| leg | verdict |\n|---|---|\n"
        "| **(1)** `F_portable` false-fire rate against the legacy labeled real union | **PASS** |\n"
        "| **(2)** legacy nonsense catch at `F_portable` | **PASS** |")
    # The determinism verdict, collapsed to the bare word.
    _cut_block(package, "07-determinism-and-run-receipt.md",
               "### Pre-conditions, asserted rather than assumed",
               "\n\n## The run's provenance receipt")
    sub(package, "07-determinism-and-run-receipt.md",
        "## Leg B — end-to-end reproduction (the verb run twice on the live corpus)\n",
        "## Leg B — end-to-end reproduction (the verb run twice on the live corpus)\n\n"
        "The verb was run twice on the live corpus. Both runs' settled-index start/end checks\n"
        "passed.\n\n**Determinism: deterministic.**\n")
    sub(package, "07-determinism-and-run-receipt.md",
        "| `determinism_leg` | `within_ci_by_construction` |", "| determinism | `deterministic` |")
    sub(package, "07-determinism-and-run-receipt.md", "| probe-embed cache hits | `0` |\n", "")
    sub(package, "00-README.md",
        "| `01-summary.md` | both floors, their selection receipts, the two pre-registered acceptance "
        "legs, the run's measured population, and the acceptance's independence bound |",
        "| `01-summary.md` | both floors and the two pre-registered acceptance verdicts |")
    _cut_block(package, "00-README.md", "## The bounds, and where each one lives", "\n\n## Terms used")
    return package


def build_appendix(honest: Path, root: Path) -> Path:
    """RAISED-A1 reading 1: every bound present, but in ONE canonical section.

    Nothing is deleted — every bound sentence survives verbatim in `09-bounds.md`. The ONLY
    change is placement, which is exactly the variable A1 asks about and the variable the
    original two-package battery could not sample.
    """
    package = fresh_copy(honest, root / "appendix")
    relocated: list[str] = []
    for filename, block in BOUND_BLOCKS:
        relocated.append(cut(package, filename, block).strip())
    relocated.append(cut(package, "06-per-hit-decomposition.md", BOUND_06).strip())
    relocated.append(_cut_block(package, "02-per-group-distributions.md",
                                "> **Bound (iii)", "\n\nBoth instruments").strip())
    relocated.append(_cut_block(package, "01-summary.md",
                                "> **Bound (iv)", "\n\n## Validity floors").strip())
    (package / "09-bounds.md").write_text(
        f"{BANNER}\n\n# 09 — Bounds\n\n"
        "Every bound that governs any number in this package, collected in one place.\n\n"
        + "\n\n---\n\n".join(relocated)
        + "\n",
        encoding="utf-8",
    )
    sub(package, "00-README.md",
        "| `08-drop-diagnostics.md` | probe drops by cause, and the validity floors |",
        "| `08-drop-diagnostics.md` | probe drops by cause, and the validity floors |\n"
        "| `09-bounds.md` | every bound that governs any number in this package |")
    _cut_block(package, "00-README.md", "## The bounds, and where each one lives", "\n\n## Terms used")
    return package


def _cut_block(package: Path, filename: str, start_marker: str, end_marker: str) -> str:
    """Delete from ``start_marker`` up to (not including) ``end_marker``; assert both exist."""
    path = package / filename
    text = path.read_text(encoding="utf-8")
    if start_marker not in text or end_marker not in text:
        raise SystemExit(f"BLOCK CUT DID NOT LAND: {package.name}/{filename}: {start_marker[:50]!r}")
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    path.write_text(text[:start] + text[end:].lstrip("\n"), encoding="utf-8")
    return text[start:end]


# =======================================================================================
# THE ATTACK SET — never handed to an informant
# =======================================================================================


def build_w1(honest: Path, root: Path) -> Path:
    """Every keyed byte honest; DISHONEST everywhere the battery does not look."""
    package = fresh_copy(honest, root / "W1-dishonest-outside-the-keys")
    sub(package, "06-per-hit-decomposition.md",
        "> **Bound (ii) — shown-k slice only.** Every number on this page covers ranks 1–10. The\n"
        "> instrument captures `k' = 30` hits per query; ranks 11–30 are excluded here by design,\n"
        "> because they were never shown to a caller and cannot be over-flagged.",
        "Every number on this page covers the full `k' = 30` capture, so the over-flag rates are\n"
        "complete: no hit the instrument saw is excluded from the decomposition.")
    sub(package, "02-per-group-distributions.md",
        "⚠ n = 15 is the pre-registered identifier pool (the first 15 identities in ascending\n"
        "`sha512_hex(identity)` order). At n = 15, `p5` and `p95` are single order statistics: they move\n"
        "by a whole sample under one insertion. Read them as edges, not as estimates.",
        "n = 15 is the pre-registered identifier pool (the first 15 identities in ascending\n"
        "`sha512_hex(identity)` order). The pool is stable: its percentiles are insensitive to corpus\n"
        "insertion, so these edges may be read as estimates like any other group's.")
    sub(package, "05-adopted-row-provenance.md",
        "It is\n  free text; nothing in 11-i renders it.",
        "It is\n  free text and 11-ii renders it verbatim to the consumer, so it needs no sanitiser seam.")
    append(package, "07-determinism-and-run-receipt.md",
           "\n### Instrument comparability\n\nBoth instruments' response-best cosines were captured "
           "under the same embedding schema, so a\ncosine from one is directly comparable with a "
           "cosine from the other and `Δ` may be read as a retrieval-quality change.\n")
    sub(package, "01-summary.md", "State `measured`; the head was adopted.",
        "State `measured`; the head was adopted and is LIVE — lore's readers resolve this floor\n"
        "today, so the absence verdict above is already in production.")
    return package


def build_w2(honest: Path, root: Path) -> Path:
    """Every number coherent; the METHOD underneath is nonsense."""
    package = fresh_copy(honest, root / "W2-coherent-numbers-nonsense-method")
    sub(package, "01-summary.md",
        "One dual-instrument run over one corpus snapshot. Both instruments captured response-best\n"
        "cosines for every query in the run's query set; each instrument's own labeled sets drove its\n"
        "own floor selection.",
        "One dual-instrument run over one corpus snapshot. `F_portable` was selected by SWEEPING the\n"
        "floor ladder and keeping the value that MAXIMISED the catch rate on `legacy-nonsense`;\n"
        "acceptance leg (2) then grades that same floor on that same `legacy-nonsense` set. The\n"
        "labels on the real union were assigned by taking the portable instrument's own rank-1 hit\n"
        "as ground truth.")
    sub(package, "08-drop-diagnostics.md",
        "Every drop below is dropped\nAND counted — no probe is silently discarded, and no dropped "
        "probe contributes a synthetic\n`0.0`.",
        "The pool of 456 is taken AFTER probes that failed for any other reason were removed, so the\n"
        "three causes below are the only ones the rate can express.")
    sub(package, "07-determinism-and-run-receipt.md",
        "| (ii) decision agreement between the two floors over the L1 R-PACKAGE gate population (this "
        "run: all 1740 queries) | `≥ 0.98` |",
        "| (ii) decision agreement between the two floors, computed over the same 1740 queries "
        "that selected both floors, with the F2 gap `0.010101` itself fitted to these two runs "
        "| `≥ 0.98` |")
    return package


def build_w3(honest: Path, root: Path) -> Path:
    """Fabricated + truncated `per-query-rows.jsonl`."""
    package = fresh_copy(honest, root / "W3-fabricated-jsonl")
    path = package / "per-query-rows.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    banner, first_row = lines[0], json.loads(lines[1])
    first_row["response_best_cosine"] = 0.62  # plausible magnitude -> violates the sentinel rule
    first_row["absence_verdict_fired"] = True  # fired on a query far above the floor
    for hit in first_row["hits"]:
        hit["shown"] = True  # 30 shown hits, contradicting SURVEY_K = 10 and bound (ii)
    del first_row["hits"][7:]  # a k' = 30 capture that carries 7 hits
    path.write_text(banner + "\n" + json.dumps(first_row) + "\n", encoding="utf-8")
    return package


def build_w4(honest: Path, root: Path) -> Path:
    """FLAT: every keyed answer folded into the summary, the rest gutted."""
    package = fresh_copy(honest, root / "W4-flat")
    summary = package / "01-summary.md"
    parts = [summary.read_text(encoding="utf-8")]
    for name in ("02-per-group-distributions.md", "03-anchor-rates.md",
                 "06-per-hit-decomposition.md", "07-determinism-and-run-receipt.md",
                 "08-drop-diagnostics.md"):
        path = package / name
        parts.append("\n\n---\n\n" + path.read_text(encoding="utf-8"))
        path.write_text(f"{BANNER}\n\n# {name}\n\nFolded into `01-summary.md`. Nothing is carried "
                        "here.\n", encoding="utf-8")
    summary.write_text("".join(parts), encoding="utf-8")
    return package


def build_w5(honest: Path, root: Path) -> Path:
    """Legible ONLY to a reader who already holds 11-i-b's context."""
    package = fresh_copy(honest, root / "W5-context-dependent")
    sub(package, "06-per-hit-decomposition.md",
        "## Why the decomposition is split this way\n\n"
        "A floor that over-flags the best hit is refusing on results the caller would have found useful;\n"
        "a floor that over-flags only mid-list hits is refusing on tail results the caller was going to\n"
        "ignore. The two failure modes carry different costs and the aggregate rate hides which one is\n"
        "happening, so the aggregate is never reported here without the split.",
        "## Split rationale\n\nPer D4 / the #180 rider. See C6(f).")
    sub(package, "08-drop-diagnostics.md",
        "**Why the match key is stated.** The 12 `sibling_chunk_same_file_only` drops are exactly the\n"
        "probes a file-path match key would have scored as self-retrieval HITS. Under path matching this\n"
        "run would have reported `33 / 456` = `0.072368` instead of `0.098684` — a drop rate understated\n"
        "by a quarter, against a 20% gate. Self-retrieval is CHUNK-scoped; the hold-out exclusion is\n"
        "FILE-scoped; the two scopes differ by design and are not interchangeable.",
        "Match key per C13. Path-key counterfactual: `33 / 456` = `0.072368`.")
    sub(package, "02-per-group-distributions.md",
        "**Derived from the columns above, and the reason the headline scalar in `01` is not sufficient:**\n"
        "the paired difference from legacy to portable is not a constant. It differs across percentiles "
        "WITHIN a\n"
        "group (`human-implementation-vocabulary`: `−0.030303` at p5, `+0.151515` at p95), it differs\n"
        "across groups at the same percentile (median Δ ranges `+0.030303` to `+0.111111`), it **changes\n"
        "sign** in `legacy-nonsense` above the median, and the p5–p95 width changes by a different amount\n"
        "in every group — including one negative. A scalar offset would show one number in every cell of\n"
        "the Δ rows and zero in every width-Δ cell. This is a distribution-shape difference, not an offset.",
        "Δ is non-constant across percentiles, groups and widths; sign-changing in G6. Not an offset.")
    sub(package, "07-determinism-and-run-receipt.md",
        "**The exact-skip scheduler may not rest on byte-reproduction of a measurement.** This run\n"
        "demonstrates that two runs over a byte-identical corpus produce different derived payloads, so:",
        "Per C10 / E5, the L1 scheduler's obligations:")
    # The fix wave gave `honest` a glossary; a context-dependent package would not ship one.
    _cut_block(package, "00-README.md", "## Terms used in this package",
               "\n\n## How the sentinel values are built")
    return package


def build_w6(honest: Path, root: Path) -> Path:
    """Degraded by CONTRADICTION, not by removal — the axis the authored control never sampled."""
    package = fresh_copy(honest, root / "W6-internally-contradictory")
    sub(package, "03-anchor-rates.md", "| `human-prose` | 12 | 8 | 4 |", "| `human-prose` | 12 | 8 | 40 |")
    sub(package, "06-per-hit-decomposition.md",
        "**`verdict_not_fired_queries`** (the absence verdict did not fire): **964** of 1740 — see `03`.",
        "**`verdict_not_fired_queries`** (the absence verdict did not fire): **1200** of 1740 — see `03`.")
    sub(package, "08-drop-diagnostics.md",
        "Surviving probes: **`answered_probes`** = `probe_manifest_pool − 45` = `456 − 45` = **411**.",
        "Surviving probes: **`answered_probes`** = `probe_manifest_pool − 45` = `456 − 45` = **400**.")
    sub(package, "07-determinism-and-run-receipt.md",
        "| `floor` | `0.456789` | `0.456801` |", "| `floor` | `0.451234` | `0.456801` |")
    return package


def build_w7(honest: Path, root: Path) -> Path:
    """The attack copy of the appendix variant, so `grade.py` can score it beside W1–W6."""
    package = build_appendix(honest, root)
    destination = root / "W7-bounds-in-appendix"
    if destination.exists():
        shutil.rmtree(destination)
    return package.rename(destination)


VARIANTS = (build_degraded, build_appendix)
WRONG = (build_w1, build_w2, build_w3, build_w4, build_w5, build_w6, build_w7)

if __name__ == "__main__":
    mode, honest_dir, output_dir = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    builders = VARIANTS if mode == "--variants" else WRONG
    for builder in builders:
        print(builder(honest_dir, output_dir))
