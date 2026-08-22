# REPORT-lead-packet60 — Keep substrate (head of the 60–65 authz/Keep track)

lead-base v6 read

## SUMMARY BLOCK

| field | value | pass |
|---|---|---|
| `Verdicts acted on:` | all adversary/cold-audit verdicts acted on at their graded HEAD → SAME (each re-verified by a lead re-run before acting) | ✅ no STALE acted on |
| `Directives:` | spawn-brief front-loaded / sidecar follow-ups: native wake + `lore_comms` durable / 0 prose-duplicated | ✅ duplicated = 0 |
| `Rulings:` | 9 in the committed ruling doc (Forks A–F + FR-1/2/3) / 0 body-only | ✅ body-only = 0 |
| `Agents:` | 23 spawned / 23 ledger-retired / 0 left running | ✅ retired = spawned, left-running = 0 |
| `Uncommitted at stop:` | 0 files (tree clean) | ✅ 0 |

## Outcome

Packet 60 (Keep substrate) is **CODE COMPLETE — COMMIT-ONLY** on `feat/surreal-unification`
(deploys with packet 39 at packet 65's joint cutover; NO 60-alone deploy). 13 commits
`b9e6335..e8f2b80`. Full pipeline (contract → contract-adversary → build → cold-audit → commit)
Opus 4.8 end-to-end + a long-running Fable design sidecar; all coordination on `lore_comms`;
operator offline (design forks ruled by the sidecar within delegated authority).

Delivered: the `keep` table (typed, call-time-derived `type`/`rank` domains), the
`member_of{rank}` household edge (OVERWRITE TYPE RELATION ENFORCED + UNIQUE(in,out)), keeper
ownership, `generate_keep_ddl` folded into `generate_ddl`, the `KeepStore` CRUD class
(`loremaster/keeps.py`), and the `lore-adm` verbs create-keep/add-household/remove-household/set-rank.

Gates at completion: **800 pytest passed, typecheck 0, ruff clean**; both cold audits GO (wave-1
14/14 + wave-2 30-check live probes with positive controls).

## Commit arc

- `f0ebbf4` docs(60) sidecar Forks A–F · `b9e6335` test(60) exact-set-pin ref fix
- `efccdc8` **feat(60) W1** schema + `KeepStore` · `3077d23` docs(49) stale-prose · `899604b` docs(60) FR-1 · `ea03ea6` archive
- `e019477` **fix(60) Q2b** KeepStore wraps engine rejections (consumer-law parity) · `5b7180c` docs(60) FR-2
- `db719a0` **fix(60) FR-3** remove-household LOUD on ghost keep · `bd9032f` **feat(60) W2** lore-adm verbs · `66ed1aa` docs(60) FR-3
- `52e5bb5` docs(49) 2 more stale docstrings · `2499f7b` archive · `e8f2b80` docs(60) INDEX + Log

## The adversary/cold-audit loop earned its keep — 5 real gaps caught green-at-builder-gate

1. **Nameless-keep read-back** (adversary attack-9): a `SELECT *`+bracket `get_keep` KeyErrors on a
   `dm` (name=None) keep; passed the store suite 26/26. Closed with explicit-projection pins.
2. **KeepStore engine-error leak** (sidecar FR-2 Q2, surfaced by the wave-2 CLI): KeepStore leaked raw
   `SurrealStoreError` where PrincipalStore wraps (consumer law). Amended (Q2b) with coverage-as-checked-variable.
3. **No-op set-rank** (adversary): `_cmd_set_rank` returning 0 without calling the store passed 40/40
   (the only legal rank == the default). Closed with an error-path pin.
4. **Silent remove-on-ghost-keep** (adversary R3 → sidecar FR-3): an access-control silent-surprise;
   made LOUD + the ∀-verb nonexistent-`--keep` invariant.
5. **Degenerate + test-env-fiction pins** (cold audit R-A/R3): `"dm" ⊂ "lore-adm:"`; `startswith` on
   store-rejection paths green-in-suite/false-in-prod (#401). Tightened.

## OPERATOR-REVIEW ITEMS (durably surfaced, not escalated to the offline operator)

- **Fork A divergence:** keeper stored as an INDEXED `keep.keeper` record<principal> FIELD LINK, NOT
  the `keeps` RELATION edge the authz design §2.1/§4.4 names. Sidecar-ruled within delegated authority
  (semantically identical; the PDP resolves `$my_keeps` via `member_of` and never traverses `keeps`;
  matches the 48/49 house idiom + store-law §4). **Countermand-able on operator return** — 61–65 build
  on the field. Full reasoning: ruling doc §A.
- **Parts 2/3 scope-crossings (sidecar FR-1):** packet-49 stale-prose cleanup folded in (docs(49),
  #398); the #398 recurrence invariant deferred as a standalone hygiene item.

## OPEN FOLLOW-UPS

- **#398** — stale-STUB→greened-code recurrence invariant (**Part 3**). Ruled by the sidecar: build a
  STRUCTURAL invariant (not a forbidden-literal scan), full contract→adversary→build→cold-audit;
  placed as a standalone hygiene item, **triggered before packet 61** (task `06b195e3`). All #398
  defect INSTANCES are fixed; the invariant (prevention) is owed.
- **#400** — DRY: extract a `lorerunes` `wrap_engine_rejection()` shared by Principal + Keep stores
  (trigger: 3rd store/consumer).
- **#401** — test-env-fiction: `lore-adm` store-rejection stderr carries a `keep.query.rejected` log
  line before `lore-adm:` (CLI-wide, pre-existing; the keep tests were made honest with `in`).

Reports (23 pipeline artifacts): `docs/plans/v2/receipts/2026-08-22-packet60/`.
