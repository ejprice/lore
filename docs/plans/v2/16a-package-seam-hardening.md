# 16a — Package-seam hardening: loresigil client + index watcher
size ~0.15 wu · wave L (parallel-safe) · depends: none · DEPLOY: yes if a served behaviour
changes, else receipts-only
law: packages-over-hand-rolling (repo CLAUDE.md), DESIGN-LAW §1 (honest surfaces)

**Provenance: MINTED by the operator-directed findings sweep of 2026-07-26** (INDEX Log) to
home three 11-i-scout findings no existing packet owns — 16 is store-units-only ("any
lore-code change" is its Scope OUT), 09 is served-surface residues, 11a/11b are the
reconciler. **Operator may strike or re-home this packet at its kickoff.**

## Mission
Close three supporting-seam findings from the 11-i package scouts: silent embedding-quality
loss in the splitter, a retry that disobeys the server, and a dependency fork that breaks
silently.

## Scope IN (each item = its finding resolved with a receipt)
- **#205** — `loresigil.resilient.split_to_fit` reportedly over-splits by ~60% (32 pieces
  where 20 fit): silent embedding-quality loss via diluted mean-pooling. **VERIFY FIRST** —
  the "reportedly" is an inherited number, so re-derive it with a COMMITTED measurement
  script (repo law: a figure you didn't measure is a rumor), then fix the split math with a
  pin holding piece-count on the measured fixture. ⚠ If the fix changes what gets EMBEDDED,
  say so loudly — embedding-input changes interact with the schema fingerprint (11a/11b) and
  the floor (DESIGN-LAW §3); coordinate, don't surprise.
- **#223** — `Retry-After` is CAPPED at `RETRY_MAX_DELAY_S`: a server saying 120s is retried
  at 30s — lore deliberately retries sooner than instructed. Honour the server's value
  (bounded by an explicit sanity ceiling, with a LOUD log line when clamping) — never
  silently. Rides the #207-consolidated `loresigil/backoff.py` policy, ONE implementation.
- **#209** — ~370 LOC subclasses watchdog's PRIVATE internals under an UNBOUNDED
  `watchdog>=6.0`, and the forked code exists to detect inotify overflow — so breakage is
  SILENT index staleness. Two steps: (a) NOW — bound the dependency + an import-canary pin
  that reddens the day the private surface moves (pin the miss); (b) adjudicate un-forking
  per the packages rule (does upstream now expose what the fork needed?) with receipts
  either way.

## Scope OUT (surface to operator if encountered)
- Any served-render change (09 / 11-ii territory). Any embedder model/prompt change
  (invalidates the floor — DESIGN-LAW §3). The `_txn` tenacity question (#202 — watch list,
  deliberately not churned).

## Entry check
`lore_findings` → #205, #223, #209 unresolved. Suite green at HEAD. Re-derive #205's
over-split number BEFORE writing any fix (if the measurement refutes it, resolve the
finding with the receipt and STOP that item).

## Exit
TDD per repo law; contract-adversary before builder; cold audit. Measurements committed as
scripts, not prose. Findings resolved with receipts; INDEX row + Log.
