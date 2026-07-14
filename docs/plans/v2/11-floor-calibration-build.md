# 11 — Per-corpus floor calibration · BUILD (finding #83) (formerly PKT-02)
size ~0.25 wu (re-sized 2026-07-14; split at kickoff if the ruled design grows it to ≥0.30) · wave L · depends: packet 10 ruled
law: DESIGN-LAW §3, §5 (store idioms), §6, §12 · DEPLOY: yes (both containers)

## Mission
Build the packet 10 design: per-instance floor measurement persisted in that instance's
store (CalibrationEngine pattern — the token-calibration engine from P8c is the
in-repo precedent), served/surfaced via lore_index, with automatic drift-triggered
re-measurement + adoption. Resolve findings #83 and #87.

## Scope IN
- Measurement runner (portable query-set strategy per the ruled design) + persistence
  (per-instance store rows; provenance: embedder+prompt fingerprint, date, survey stats).
- Drift trigger → automatic re-measure + adopt (replaces disarm-and-wait), with the
  ruled thresholds; every adoption logged + surfaced in lore_index.
- lore_index calibration render: honest states (measured / re-measuring / disarmed),
  file-count accounting fixed at source (#87).
- Floor bound to embedder+prompt fingerprint (DESIGN-LAW §3) — a config change
  invalidates and re-arms measurement, never serves a stale floor.

## Scope OUT (surface to operator if encountered)
- Any change to the verdict grammar/wording (advisory wording is ruled law).
- Reranker/utility-predictor confidence layers (packet 28 territory).

## Entry check
- packet 10 ruling recorded; suite snapshot green at current HEAD; spike-surreal up.
- `lore_findings` → **#4** (calibration integrity-state string collision, pre-P8d):
  if still open, it lives in the engine this packet touches — fold its fix in.

## Exit
TDD per repo law; hostile fixtures for any new render of stored text; cold audit;
deploy BOTH; smoke: a non-lore corpus (DI) measures its own floor or renders its
honest interim state; #83 + #87 resolved with notes; INDEX row + Log.
