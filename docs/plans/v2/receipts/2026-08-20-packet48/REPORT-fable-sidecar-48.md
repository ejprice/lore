# REPORT — fable-sidecar-48 (packet 48 design sidecar)

`brief-base v14 read` · `brief project v7 read`

> **UPDATE 2026-08-20 (supersedes the F1 line below):** the operator resolved **F1 → Model
> B** (admin pre-creates by email; 39 fills the OAuth subject on first login). The design doc
> §3/§4/§5/§8 were re-ruled: `subject` is now **`option<string>` UNIQUE** (probe-settled,
> `scripts/probe_unique_nullable_48.py`), `create`'s `subject` is optional (email-only
> creation), and a NEW **`set_subject(email, subject)`** fill-on-login primitive is ruled IN
> (unconditional email-keyed UPDATE; the fill-once guard is 39's orchestration — F1b). F1 is
> no longer an open flag. The forks below read as first ruled; the design doc is current.

## Summary block
- **State:** done (deliverable shipped; now standing by for follow-ups across packet 48).
- **Deliverable:** `docs/design/2026-08-20-packet48-principals-substrate.md` — the ruled
  design doc IS the deliverable (brief redirected the report to it; this REPORT is the
  standard-addressed pointer per brief-base §1). All 6 kickoff forks ruled, contract-ready.
- **Deviations:** (1) idle-gate contract filename did not match the hook's
  `<session-id>-<name>.contract` pattern (I lacked the session-id), so the gate fell to its
  `REPORT-<name>.md` default and nudged; resolved by writing this report + nulling the
  contract. No work impact.
- **Packages considered:** none — no new mechanism. Every 48 mechanism reuses INTERNAL lore
  seams (`SurrealStore`, `store._txn.run_query` / `execute_transaction` / `bootstrap_session`
  / `retry_on_conflict`, the `_define_*` DDL helpers, the `FindingLedger` owner idiom). This
  is store-layer machinery the fastmcp framework never covered — no package to prefer.
- **Reuse ledger:** the design SPECIFIES reuse rather than introducing symbols; the DRY
  ledger for the code 48 will write lives in the design doc §5 (7 rows, all REUSED/idiom).
  No new reusable symbol introduced BY THIS DOC.
- **Graded:** N/A — a design ruling, not a verdict on another agent's artifact.
- **Decisions needed (for lead/operator):** one borderline-operator flag — F1, the
  subject required-vs-optional question = the 39/49 provisioning model. Ruled REQUIRED for
  48 (low-regret; required→optional is the safe widening direction), non-blocking. Lead's
  call whether to have the operator confirm the provisioning model before packet 39.
- **Receipt pointers:** rulings + rationale + exact `_PRINCIPAL_FIELD_SPECS` / `build_store`
  signature / `PrincipalStore` method signatures → the design doc (§0 summary table, §1–§6
  per-fork, §8 contract-author checklist). Ground-truth facts → lore memories
  `221fce15…` (build_store 3 sites) and `0e2e4d06…` (Variant A schema idiom). Lead status →
  `lore_comms` #5045 (thread `pkt48-design`).

## What was ruled (headlines — detail in the design doc)
1. **Fork 1 — extraction scope: NARROW.** `build_store(config) -> SurrealStore` (un-readied)
   over the 3 byte-identical sites (`server.build_app_context` write_store /
   `index.cli._run` / `scout.Scout.from_config`). R4 (no URL-credential parsing) + R5
   (lifespan → `_eager_build_with_retry` → `build_app_context` chain) pinned. Broad
   (~10 cred/db re-resolvers incl. `AppContext._await_live_connect`) deferred.
2. **Fork 2 — DDL idiom: Variant A confirmed.** `_PRINCIPAL_FIELD_SPECS` +
   `_principal_statements()` folded into global `generate_ddl()` + standalone
   `generate_principal_ddl()` owned by `PrincipalStore.ensure_ready` via
   `execute_transaction`. The fold is what creates the table in prod without wiring the store
   into `build_app_context`; the shared-DB future is a documented 2-line seam (not built).
3. **Forks 3/4 — field set + `subject`.** Exact spec tuple; NEW
   `_PRINCIPAL_STATUS_ALLOWED`/`_PRINCIPAL_ROLE_ALLOWED` (R3). `email`/`subject`
   required-non-empty + UNIQUE; `display_name`/`expires_at` `option<>`; `status ∈
   {active,suspended}` DEFAULT active; `role ∈ {member,admin}` DEFAULT member (my ruling);
   `created_at` DEFAULT `time::now()`. `subject` UNIQUE+REQUIRED anchored on
   `AccessToken.client_id`. No status index (YAGNI).
4. **Fork 5 — CRUD.** `PrincipalStore.create/get_by_subject/get_by_email/list/set_status` +
   pydantic `Principal` value object, all routing through the existing store seams — NO new
   query/retry seam (#102/#120). Store-law §2 read/write idioms specified (explicit
   projections, CONTENT-with-omit-to-default, `.get()` for option columns).
5. **Fork 6 — module docstring standing-law clause.** Exact wording: principal = the third
   (human) vocabulary; ledger-actor strings not retro-fitted; the `agent` table's role/status
   named as the sibling vocabulary NOT to conflate; cite the law by `_TRACE_DECLARED_KEYS`
   anchor, not a line number.

## Flags (design doc §7)
- **F1** (borderline-operator): subject required-vs-optional = 39/49 provisioning model.
  Ruled required for 48; non-blocking; surfaced for operator/39 confirmation.
- **F2** role DEFAULT member — my ruling (one-line reversible).
- **F3** no status index — deliberate YAGNI (re-open: hundreds of principals / hot filter).
- **F4** shared-DB future — documented un-built seam.
- **F5** broad extraction — deferred refactor (concrete address: the ~10 re-resolvers).
- **F6** contract-author sweep: the `generate_ddl()` fold may collide with an exact-DDL /
  table-inventory pin — a required co-edit, not a defect.

## Status
Idle, standing by as the long-running packet-48 design sidecar. Follow-ups reach me via
SendMessage; my design doc is the durable artifact the lead ground-truths.
