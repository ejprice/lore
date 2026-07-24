brief-base v6 read

## SUMMARY BLOCK
- state: done — design doc written, committed on `pkt10-floor-calibration-design`; standing by for follow-ups
- deliverable: `docs/design/2026-07-24-floor-calibration.md` (house format; §Recommendation R1–R8; six forks)
- deviations: (1) packet-10 entry check "confirm search_score_survey.py still runs against the deployed store" NOT executed — the script's own default coordinate is `ws://127.0.0.1:18500/rpc` (production), which this brief forbids; script read end-to-end instead, stated plainly in doc §1.5. (2) No `.venv` built; nothing executed from the worktree → no `loremaster.__file__` receipt exists or is claimed.
- decisions-needed: operator ruling on forks F1–F6 (doc §Forks; F1/F2/F4 are the load-bearing three)
- receipt pointers: live measurement → doc §1.1 (lore_index 2026-07-24, corpus 2935, stale on FINGERPRINT leg); source receipts → doc §1.2–§1.4 (symbols: `SearchPipeline._to_result`, `_cosine_absence_verdict`, `apply_cosine_floor_drift_check`, `Indexer.index_status`); prior-art bars → doc §1.5
- out-of-scope surfaced: items S1–S4 below (S1 is finding-worthy; your call whether I file it)

## Provenance (what I measured vs read vs did not run)
- MEASURED 2026-07-24: one `lore_index()` status read against the deployed lore-lore
  instance (serving `/workspace` = `feat/surreal-unification` @ `7f23223`, the exact
  commit this worktree forked from). Receipt verbatim in doc §1.1. Note: floor is stale
  on the **fingerprint** leg today (embedding schema `b4dd657…` → `f6e2ee34…`, v2) —
  stronger than #161's count-leg record; the floor was measured in a retired embedding
  space. files_indexed=2935 (INDEX's "2764 by design" already superseded — re-derived,
  not inherited, per the brief's numbers law; no count is pinned anywhere in the design).
- READ (worktree `/home/ejprice/PycharmProjects/lore-pkt10` @ `7f23223` only; main tree
  untouched incl. its untracked lore.yaml): packet 10 + 11 specs, both prior-art design
  docs, DESIGN-LAW §3/§5/§6, `search.py` calibration spans, `server.py`
  `_build_index_status`, `indexer.index_status`, `calibration/engine.py` state/drift
  surface, `search_score_survey.py` end-to-end (groups, bars, `choose_cosine_floor`,
  store coordinates).
- READ (store, via lore_findings get): #83, #87, #161, #160, #74, #75, #4. lore_search/
  lore_read not used for load-bearing content (worktree files read directly; #125 noted).
- DID NOT RUN: the survey script (see deviations), any test, any deploy. Nothing needed
  provenance assertion because nothing was executed.

## Key source-verified facts the design turns on
1. **Per-hit weak flag has NO drift gate** (`SearchPipeline._to_result`; confirmed by
   `_cosine_absence_verdict`'s docstring: only the aggregate disarms). Combined with
   today's fingerprint-leg staleness: per-hit warnings are being served against a floor
   from a retired embedding space, right now, on lore's own instance (doc §1.2). Design
   response: F4 (disarm per-hit on fingerprint-leg staleness only).
2. **The current drift trigger is edit-blind**: legs are fingerprint + file COUNT ±10%;
   #74's own rot mechanism was an EDIT (count unchanged) — the trigger cannot detect the
   mechanism that motivated it (doc §1.3). Design response: churn leg at chunk
   granularity (R4).
3. **#87 answered at source**: `files_indexed` = manifest rows `state==STATE_INDEXED`
   across all tiers; 214→207 (−3.3%) is inside the 10% tolerance → `measured`/`note:null`
   is per design — #87's possibility (1). Render is honest-but-unexplained; fixed in the
   serving contract (always render shift-vs-tolerance; runner stamps its own snapshot,
   retiring the "nearest proxy" stamp admitted in search.py's comment). Doc §1.4/§6.
4. **Q5 answered first, as briefed**: measure stratified, adopt pooled, pre-register the
   per-tier upgrade (R8) — and the design is invariant to every #160 outcome, which
   dissolves #161's "settle #160 first" ordering (doc §2; fork F2 since that reverses
   #161's explicit ask).
5. **Portable known-absent set**: hold-out (leave-source-file-out) scoring of the
   self-supervised probes — absent-by-construction, residual error runs in the
   conservative direction (catch understated). The fixed nonsense set does not port
   (its absences are lore-relative). Doc §3, forks F3/F5.

## Entry-check results
- #83 acknowledged, #87 acknowledged, #161 open, #160 acknowledged — all as expected.
- Survey script: read, not executed (deviation 1). The portable runner in the design
  retires its hardcoded production coordinate anyway (per-instance runs by construction).

## Out-of-scope items surfaced (operator owns scope; none decided here)
- **S1 (finding-worthy):** every NON-lore deployment serves per-hit weak-match warnings
  against lore's baked-in 0.50649 today — no drift gate on that surface, no calibration
  claim on that corpus. #83's "no instance serves a WRONG verdict" covers the aggregate
  only. The design closes it (R6/R7), but it is a live mislabeling surface NOW on the DI
  instance. Want me to file it, or does the lead?
- **S2:** packet 11's entry check says "fold #4's fix if still open" — #4 is RESOLVED
  (P8d W3, `integrity_failed` shipped). Entry check already satisfied; suggest packet 11
  carry only an exact-set distinctness pin for the NEW state strings (doc §6.4).
- **S3:** INDEX prose "corpus now 2764 files by design" vs 2935 measured today — expected
  movement, receipt only, no action proposed.
- **S4:** the two REPORT-*-03b.md files sitting at this worktree's root (inherited from
  the fork point, another packet's uncommitted-at-fork state? they are tracked at
  `7f23223`) — not mine, not touched; noting so their presence isn't attributed to this
  packet.

## Standing by
Long-running sidecar per brief; follow-ups via SendMessage. Design doc + this report are
committed on `pkt10-floor-calibration-design`; idle-between-questions is expected.
