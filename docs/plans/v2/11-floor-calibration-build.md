# 11 — Per-corpus floor calibration · BUILD (findings #83, #87, #161) (formerly PKT-02)
size ~0.25 wu (re-sized 2026-07-14; split at kickoff if the ruled design grows it to ≥0.30) · wave L · depends: packet 10 ruled
law: DESIGN-LAW §3, §5 (store idioms), §6, §12 · DEPLOY: yes (both containers)

## Mission
Build the packet 10 design: per-instance floor measurement persisted in that instance's
store (CalibrationEngine pattern — the token-calibration engine from P8c is the
in-repo precedent), served/surfaced via lore_index, with automatic drift-triggered
re-measurement + adoption. Resolve findings #83, #87 and **#161**.

**#161 is the LIVE INSTANCE of the #83 gap, and it closes with this packet.** A wave's
report archives grew the indexed corpus past the 10% tolerance; lore flagged its own
floor `state: "stale"` and — because disarm-and-wait is all that exists — nothing acted
on the self-declaration. The automatic re-measure + adopt built here IS the fix.
⚠ **Do NOT pin #161's recorded file counts as an acceptance number.** The corpus is a
moving target as lore is built (its 214→353 was already superseded by the vendor-tier
onboarding), so a count-match proves nothing: the exit condition is that the MECHANISM
re-measures and adopts on drift, whatever the count is that day. #161 also parks a
design fork — whether ONE floor over a mixed code+receipts corpus is even the right
model (it asks to be read with #160) — and that fork belongs to packet 10's ruling, not
to this build; if 10 did not settle it, surface it rather than deciding here.

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
**FIRST READ (repo store law): `docs/reference/surrealdb-31-capabilities.md`** — this
packet touches the store/schema/DDL or store-reading code; #107 was a 100% production
outage whose answer was ALREADY in that file. Cite it, never re-transcribe.
- packet 10 ruling recorded; suite snapshot green at current HEAD; spike-surreal up.
- `lore_findings` → **#4** (calibration integrity-state string collision, pre-P8d):
  if still open, it lives in the engine this packet touches — fold its fix in.
- `lore_findings` → **#161** open: read it for the live symptom, NOT for its numbers.

## Exit
TDD per repo law; hostile fixtures for any new render of stored text; cold audit;
deploy BOTH; smoke: a non-lore corpus (DI) measures its own floor or renders its
honest interim state; #83 + #87 + **#161** resolved with notes (#161's note records
that the mechanism, not a count, is what closed it); INDEX row + Log.
