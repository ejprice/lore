# PKT-01 — Per-corpus floor calibration · DESIGN (finding #83)
size ~0.15 wu · wave L (re-waved 2026-07-14; the 2026-07-07 "first" ruling was superseded by the comms + local-first re-sequences) · depends: none
law: DESIGN-LAW §3 (weak-match), §6 (measurement pins)

## Mission
Design (not build) per-corpus cosine-floor calibration: the weak-match floor must be
derived from the INDEXED corpus, not lore's own repo — measured per instance, persisted
in that instance's store, served via lore_index. Deliverable: a design doc + operator
ruling; PKT-02 builds it.

## Binding operator spec (2026-07-07, carried verbatim in the ruling trail of finding #83)
- The drift trigger **reruns calibration automatically** (re-measure + adopt, probe-loop
  precedent) — NOT the current disarm-and-wait.
- The design agent determines how drift is measured and the thresholds — measured, never
  guessed (DESIGN-LAW §3).
- Interim state stays honest: non-lore corpora disarm the aggregate verdict by construction.

## Open design questions (the doc must answer each with receipts)
1. Portable labeled query sets: identifier probes port as-is; answered probes can be
   self-supervised (a chunk's summary/docstring text as a query whose ground truth is
   its own chunk); the known-absent set needs a portable strategy — or the bars'
   promises change (say so explicitly if so).
2. What the pre-registered adoption rule means under AUTOMATIC recalibration (the
   original rule assumed a human-run survey).
3. Drift measurement + thresholds (the current corpus-fingerprint trigger disarms only;
   the new one re-measures — define false-fire bounds for the re-measure itself).
   Consider PKT-20's planned live per-hit cosine distributions as a drift-evidence
   input (continuous signal vs periodic survey) — design for it even if PKT-20 lands
   later.
4. Fold finding **#87**: lore_index reports cosine_floor "measured" while its own file
   counts disagree (214 vs 207) — the accounting surface must be verified at source and
   its truthfulness is part of this design's serving contract.

## Entry check
- `lore_findings` → #83 open with the analysis + rulings; #87 open.
- scripts/search_score_survey.py runs in place (needs SURREAL creds + LORE_TEI_KEY from
  the container env) — confirm it still runs against the deployed store.

## Exit
Design doc at docs/design/2026-07-XX-floor-calibration.md; the open forks presented to
the operator with recommendations (briefed in plain language, per standing feedback law);
operator ruling recorded in the doc; INDEX row flipped; PKT-02 unblocked.
