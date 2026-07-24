brief-base v6 read

## SUMMARY BLOCK
- state: done — design doc + Addenda A/B committed on `pkt10-floor-calibration-design`; operator's 2026-07-24 architecture ruling incorporated; standing by
- deliverable: `docs/design/2026-07-24-floor-calibration.md` — §Recommendation R1–R8 (the WHAT) + Addendum B §B7 (the build order) + §B6 (fork dispositions)
- ruling status: F1/F2/F4/F5/F6 DECIDED BY DELEGATION (doc §B6); **F3 (verdict wording) is the one surviving operator fork**, default = unchanged iff R2 lab validation passes
- decisions-needed: F3; and packet-11 SPLIT confirmation at kickoff (§B8 — re-estimate crosses 0.30; recommended 11-i dark machinery / 11-ii cutover)
- deviations: (1) survey script read end-to-end, NOT executed (its default coordinate is prod :18500 — brief forbids; doc §1.5, now moot for the durable path per the ruling); (2) nothing executed from the worktree → no provenance receipt exists or is claimed
- receipt pointers: ruling verified at the store (memory `f464cfda…`, kind=decision, re-read before citing) → doc §B0; live measurement → §1.1; source receipts → §1.2–§1.4 + A1/A2; thrash/cost story → §B2; 11a/11b composition → §B3; DDL mechanism → §B4 (capabilities §1.1–1.3/§1.5 cited); CalibrationEngine verdict → §B5
- findings: #179 filed by me (foreign-instance per-hit surface — the ruling closes it by construction, resolution rides packet 11); #176/#177 answered in Addendum A

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

## UPDATE 2026-07-24 (post lead round-trip — #176/#177 answered, #179 filed)
- **#179 filed by me** (lead-directed): the foreign-instance per-hit surface — non-lore
  deployments serve per-hit weak-match judgements against lore's 0.50649 with no
  validity claim on the host corpus. Scoped around #176 (lore's-own-instance drift-gate
  gap) and #83 (aggregate leg); links both. Code-path claim only; no DI render read —
  stated in the row.
- **#176 second-order fact CHANGES the design (Addendum A1):** re-derived at `7f23223`
  — `apply_cosine_floor_drift_check` has exactly one production caller
  (`AppContext._build_index_status`) and `disarmed_by_drift` defaults False, so a
  process that never serves `lore_index()` keeps the aggregate verdict armed against a
  drifted floor (fail-OPEN default; my own §1.1 read warmed prod's cache). My committed
  §7 inherited a milder copy ("refreshed on status reads"). Amended: event-driven
  evaluation at indexer chokepoints + boot + adoptions; `lore_index` becomes a pure
  read; unevaluated ⇒ disarmed. F4's recommendation unchanged, rationale strengthened.
- **#177 answered (Addendum A2):** the survey's query surface is read-only BY
  CONSTRUCTION and documented (S4b audit finding #2 in `survey()`'s docstring — never
  calls `ensure_ready()`, which is a schema-DDL write txn; store calls are `scroll` +
  `hybrid_search` only). Not literally write-free at the wire: lazy connect →
  `_txn.bootstrap_session` transmits `DEFINE NAMESPACE IF NOT EXISTS` / `use()` /
  `DEFINE DATABASE IF NOT EXISTS`. No-ops against the existing prod ns/db (#107
  semantics); the live hazard is a MISTYPED coordinate silently materializing an empty
  ns/db on the prod endpoint. Suggest #177's row gain that one line.

## UPDATE 2026-07-24 (second round — operator architecture ruling incorporated, Addendum B)
- Ruling verified against the durable store record (memory id `f464cfda…`, kind=decision;
  found at rank 2 on a reworded recall — my first recall query missed it in top-3,
  retried rather than trusting the inbox alone). Verbatim matches the lead's relay; the
  record itself additionally notes #179 closes by construction and #177's durable-path
  retirement — both honored in the addendum.
- Addendum B delivers the remediation half: B1 execution home (AppContext async engine
  task at A1's chokepoints; packet-30 dependency REJECTED with reasons — wave F,
  loresage-coupled, calibration needs no LLM); B2 thrash/cost (constant-bounded per-run
  cost — fixed-N probes, O(probes) not O(corpus); runs only at boot/post-sweep with
  in-flight zero; coalescing single-flight; discard→requeue-to-next-sweep as the
  clock-free debounce; ≤1 run per sweep cycle; no cost gate, citing the #171 §13
  precedent); B3 composition with 11a/11b (change-class keying post-11b, the #168 false
  invalidation dies; churn counted at the ONE shared embed wrapper; pre-11b raw
  fingerprint accepted as a bounded interim); B4 DDL per capabilities §1.1–1.3/§1.5 +
  hot rows via `_txn.retry_on_conflict` only; B5 CalibrationEngine = sibling engine,
  shared seams reused (findings Protocol, construction seam, closed-state discipline),
  wholesale reuse rejected AT SOURCE (token-ratio loop vs cosine survey); B6 fork
  dispositions; B7 build order; B8 sizing → SPLIT recommendation.
- Numbers law held: no corpus count pinned anywhere in Addendum B; cost claims are
  structural (fixed-N) with the adoption row named as the authority.

## Standing by
Long-running sidecar per brief; follow-ups via SendMessage. Design doc (Addenda A+B)
and this report are committed on `pkt10-floor-calibration-design`;
idle-between-questions is expected.
