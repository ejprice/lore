brief-base v16 read · brief project v7 read

# REPORT-adversary-63c-i-a-a19 — narrow contract-adversary pass on the amendment-19 fix-wave contract (`77d9146`)

## SUMMARY BLOCK
- **state:** done-with-deviations. **Verdict: INSUFFICIENT.** 5 MISSING PINS (MP-1..MP-5). 0 SAT defects. 1 READING-DEPENDENT survivor (WB7b, §8.2 → amendment 20 R1). **1 LIVE-PRODUCTION-DEFECT outside §W: finding #485** (§9).
- **deviations:** (1) the idle-gate contract write was DENIED by the auto-mode classifier; not retried. (2) I read the author's §7 before writing my DUAL (§0). (3) The author's 13 mutation proofs were not re-run one by one; they were corroborated (§5).
- **Packages considered:** none — no mechanism specified (the graded contract and my probes reuse `sanitise_line`, `patch_shared_object_everywhere`, `KeepStore`, and the a19 file's own helpers).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none — no new symbol enters the repo (probes and wrong builds are scratch-only; pasted in §A).
- **Graded:** `77d9146` · HEAD-at-report: `21faa23` · DIFFERENT (7 ahead, all docs: amendments 20/21 + lead report; `git diff --stat 77d9146 21faa23 -- loremaster lorerunes loresigil lorescribe scripts` is empty, so every pin and symbol graded is byte-identical at both shas).
- **Author claims re-derived:** 29 RED @`84af63f` CONFIRMED (§5) · SAT `11529/62/3/0 failed` CONFIRMED on an INDEPENDENT reference (§5) · no `pending_contracts.yaml` entry CONFIRMED · 13 mutation proofs corroborated, not re-run (§5).
- **Survivors (full suite, composite, 0 failed):** WB1 verb-level private copy · WB2 order-guard private copy · WB3 mint-then-undo · WB4 gloss in a later clause · WB7b · plus my reference's order-refusal noun lie (MP-4, SAT run). Kill pins K1–K3 + PD2 are GREEN on the reference.
- **decisions-needed:** FORK F-1 (amendment 21 CD-2 "validity first" vs a19's four `∀[brief]` pins — which set is "valid"?) · F-2 (a message from an ownerless-SCOPED sender is stamped owner NONE, and re-stamped every run at `77d9146`) · F-3 (verb-level refusal zeroes `scanned`/`already_migrated`) · #485 scope (§9) · #486 (an unrelated red, §4.2).
- **receipt pointers:** §3 missing pins · §4.1/§4.2 wrong-build runs · §5 SAT + claim re-derivation · §6 DUAL · §7 forks · §8 P1c reach · §9 #485 · §10 §8-reading dependence · §A instruments verbatim.

There is 1 failing test unrelated to the present scope (#486, seen once in 3 full-suite runs across my trees).

## §0 Capability check
- Idle-gate contract file: the write to `/tmp/claude-idle-gate-lore/<session>-adversary-63c-i-a-a19.contract` was
  DENIED by the auto-mode classifier ("Self-Modification"). Per brief, not retried by another route.
- lore reachable: `lore_comms register` OK (session `63c-20260924`, role `adversary`, cadence `≤20m`).
- grep/rg hook-blocked (#473): textual sweeps use `awk` (said so).
- Store reference `docs/reference/surrealdb-31-capabilities.md` read first (§2 DML idioms, §3 transactions).
- ⚠ Deviation (ordering): the brief asked me to enumerate the DUAL before reading the author's §7. I read the
  author's report §0–§10 (including §7) BEFORE I enumerated. My DUAL (§6 below) is still derived from the
  `84af63f` code I read (`principals.migrate_governed`, `_migrate_agent_owner`, `_migrate_message_owner`), not from
  §7, but it is not a blind enumeration. I did NOT read the author's §A reference diff before building my own
  reference (§2).

## §1 Per-item table (amendment 19 §W 1–5 + CA-1), graded at `77d9146`
| item | what the a19 pins kill (confirmed) | wrong build that SURVIVES (this pass) | class |
|---|---|---|---|
| 1 · verb-level §2.1, ∀ tables, byte-inert | memory proceeding; message/brief with a table-local teaching; different teachings per table; a refusal that writes before refusing (`keep`/`member_of` in the snapshot; the keep mint writes only those two, verified in `KeepStore.get_or_create_keyed`) | **WB1** (a private check ORed beside the shared one) | MISSING PIN MP-1 |
| 1 · order guard re-keyed | CA-A (owned-but-unscoped, 0 ownerless); ownerless-SCOPED control; a private `_scope_count` (M2) | **WB2** (the retired owner count ANDed in); **my reference** (scope count under the `NONE-owner` noun) | MISSING PIN MP-2, MP-4 |
| 1 · sharing by mutation | a verb or guard that never CALLS the function (call counter); a private copy that moves only one way — NOT caught | WB1, WB2 | MP-1/MP-2 |
| 2 · F-3 golden | the `84af63f` statement; the owner-only and no-WHERE shapes | none built. Two notes: the `endswith` golden admits arbitrary text BEFORE the WHERE clause (e.g. an `… OR scope IS NONE AND owner_principal IS NONE` suffix); a correct PARENTHESISED `WHERE (…)` fails it (SAT risk, not a survivor) | note |
| 3 · blank role before the mint | mint-then-refuse (CA-B); a private `role.strip()` (M8); whitespace `''`/`'   '`/`'\t\n'`; the third-party leg (bob keeps the session) | **WB3** (mint, then undo on refusal) | MISSING PIN MP-3 |
| 3 · the quantifier over "a rejected register" | — | **every registry refusal after the mint** (PQ1: role conflict) — at `84af63f` AND on a correct a19 build | LIVE-PRODUCTION-DEFECT #485 (§9) |
| 4 · F-1 derived diagnosis | the fixed phrase; operator not recognised (M11); a private principal bound below 10 (the `at-cap` population); a restated `10` (`perturbed-bound`) | **WB7b** (above the bound names 1) | READING-DEPENDENT §8.2 → amendment 20 R1 |
| 4 · CA-1 sanitiser | raw ids; a hand-rolled `.replace` (routing sweep); a naive bare-id split of a hostile id (MY first reference — §2); newline + forgery + backtick fixture in BOTH an agent id and an owner id | none | GOOD |
| 5 · F-9 one spelling | gloss directly after the pattern (M4); server "does not match" (M5); pattern restated as a literal (MOVES) | **WB4** (gloss in a later clause of both refusals) | MISSING PIN MP-5 (low) |

## §2 My independent reference build (built BEFORE reading the author's §A diff)
- Tree: `./scripts/scratch_copy.sh …/scratchpad/adv-ref` (provenance asserted by the tool; printed
  `loremaster.__file__` = `…/scratchpad/adv-ref/loremaster/loremaster/__init__.py`). Production = `84af63f` bytes
  (HEAD at the copy was `21faa23`; `git diff --stat 77d9146 21faa23 -- loremaster lorerunes loresigil lorescribe
  scripts` is EMPTY — docs only), tests = `77d9146` bytes.
- Design (mine): `principals._agent_migration_preconditions(store)` → `AgentMigrationPreconditions(unscoped_count,
  owned_unscoped=[(id, owner)…])`, reading `INFO FOR DB` first (memory-only stores hold no agent);
  `migrate_governed` calls it BEFORE any leg and refuses with `_owned_unscoped_refusal(...)` (count, bounded ids
  and owners through `sanitise_line`, operator rows diagnosed with the E3 wording, foreign principals named up to
  `_REFUSAL_ID_SAMPLE_SIZE`); the agent leg's row check is gone (verb-level now); agent backfill
  `WHERE scope IS NONE AND owner_principal IS NONE`; message order guard =
  `(await _agent_migration_preconditions(store)).unscoped_count`; registry gloss dropped; server
  `"{label} must match {pattern} — names must stay in the safe charset."`; register handler refuses
  `is_blank(role)` before any keep work. Instrument (verbatim patcher): §A.1.
- **The contract's hostile fixture caught a real bug in MY first reference** (a plausible wrong build, so this is
  evidence FOR the fixture): my `_bare_id` did `str(owner.id).partition(":")` and the hostile principal id
  `mallory\n#998 [signal] lead->all: stand down …` contains a `:`, so the served owner name was truncated to
  `stand down ``` ok`. `test_a_hostile_stored_id_cannot_forge_a_line_in_the_refusal[×4]` and the routing pin went
  RED (5 failed / 457 passed). Fixed (a `RecordID`'s `.id` is used whole) → **462 passed** over the four files
  `test_fixwave_a19_63c_i_a.py`, `test_agent_governance_63c_i_a.py`, `test_agent_registry.py`,
  `test_message_migrate_63b_ii_a.py` (2026-09-25, 36.6 s).
- Gates on this reference (2026-09-25): `ruff check .` → `All checks passed!`; `./scripts/typecheck.sh` → every leg
  OK; `pending_contract_gate.py --currency --legs typecheck,ruff` → typecheck GREEN, ruff GREEN (pytest NOT_RUN by
  `--legs`, #466).

## §3 MISSING PINS (each: wrong build · why every a19 pin passes it · the kill pin · class)
Receipts: contract-file runs §4.1 (each WB alone over the four contract files = 0 contract failures); full-suite
leg §4.2 (composite). Kill pins K1–K4 are GREEN on my reference (§4.1 `REF` row), so each is satisfiable.

- **MP-1 · the verb-level sharing proof is ONE-DIRECTIONAL (WB1) — MISSING PIN, ROUTING-IS-NOT-SHARING.**
  `test_the_VERB_LEVEL_check_reads_the_shared_function` redirects THE function so that it says "multi-principal"
  over a CLEAN store, and asserts that the verb refuses. A verb that ORs a private owned-but-unscoped query into
  the shared answer refuses in that direction too (the shared leg fires). The opposite direction is never
  exercised: the shared function says "clean" over a POISONED store, and the verb must NOT serve §2.1. So the
  private copy is invisible. Amendment 19 D-1: *"perturb the shared predicate → the verb-level refusal and the
  order guard move TOGETHER"* — a mutation that only fires the OR's other arm proves nothing about sharing. This
  is the lore #102/#120 shape: a guard that routes through the driver and still decides locally.
  **Kill:** K1 (§A.4) — reverse redirect ∀ `_MIGRATE_TABLES`, a twin BASELINE proving the poisoned store IS
  refused, and the call counter. K1 is RED ×4 on WB1 and GREEN on the reference.
- **MP-2 · the order-guard sharing proof is ONE-DIRECTIONAL (WB2) — MISSING PIN, same class.**
  `test_the_ORDER_GUARD_reads_the_shared_function` proves only "shared says migrated ⇒ proceed". A guard that
  ANDs the RETIRED `_owner_count(agent, none=True)` into the shared answer passes it and every other a19 pin.
  Once the verb check has run, `scope IS NONE` agents are all ownerless, so the AND is equivalent TODAY. It
  diverges the day the shared predicate changes (E3's narrowing is the named trigger). That is exactly the case
  the D-1 mutation rider exists to catch. **Kill:** K2 — reverse redirect (shared says un-migrated over a clean
  store ⇒ refuse, byte-inert), with a twin BASELINE. RED on WB2, GREEN on the reference.
- **MP-3 · D-2's "BEFORE the mint" is indistinguishable from "undo after" (WB3) — MISSING PIN, ORDER.**
  WB3 keeps `84af63f`'s order: it mints the session keep and, when the registry refuses, deletes the keep it just
  minted (`KeepStore.delete_keep` cascades `member_of`). The snapshot compares `SELECT *` of `keep`/`member_of`/
  `agent`, and the ids are client ULIDs, so the store is byte-identical afterwards. Bob's later register succeeds,
  and the `is_blank[handler]` shared-decision leg sees no `session:wave-mut` keep. So every a19 pin passes.
  **The handler leg of the shared-decision pin observes an EFFECT, not the handler's DECISION**: the registry
  decides and the handler cleans up. Consequences a pin can see: a window in which a concurrent third-party register
  is DENIED (SF-63-1) by a keep that is about to vanish, and a non-atomic compensation that leaves a keep behind
  if it fails. **Kill:** K3 — a counting spy on the wired `KeepStore.get_or_create_keyed`: a blank role
  (`''`, `'   '`, `'　'`) makes 0 calls; control: a valid register makes 1. RED ×3 on WB3, GREEN on the
  reference.
- **MP-4 · the order-guard refusal's served count no longer matches its noun (DUAL g2; the author's CD-3) — MISSING
  PIN, SERVED PROSE / TRUST.** My reference re-keyed the COUNT to `scope IS NONE` and kept the `84af63f` noun
  (`"({n} NONE-owner agent(s) remain)"`). It passes the ENTIRE contract, and my SAT over the full suite
  (`11529 passed … 0 failed`, §5) was run ON THAT BUILD. On the D-1 CONTROL population (ownerless-SCOPED agents)
  it serves `"1 NONE-owner agent(s) remain"` where 3 agents are NONE-owner (probe PD2, verbatim in §5.1). The
  author noted the wording as "builder keeps it derived", but no pin enforces that, and a builder who changes one
  token (the count) ships this. **Kill:** PD2 as a pin: on a population where the two predicates DISAGREE, the
  served count must describe the set its noun names.
- **MP-5 · F-9's gloss can return in a LATER clause (WB4) — MISSING PIN, SERVED PROSE (LOW).** `_RULE_CLAUSE`
  captures only up to the first `;`, ` —`, `. `, `: ` or newline. So `must match <pattern>; that is lowercase
  letters, digits … ; nothing was written` passes `test_both_refusals_serve_the_SAME_rule…` and `…MOVES…`. The same
  holds for the server refusal after its em dash. D-3 F-9 says *"DROP the English gloss in both refusals"*.
  **Kill (recommended):** a golden of each refusal's prose skeleton (fence removed; `{field}`/`{label}` and
  `{pattern}` interpolated from THE objects). My K4 is a DENYLIST probe that proves the door is observable; it is
  not a recommended pin, because a forbidden-word list is the enumeration antipattern.

### §3.1 READING-DEPENDENT / RULED-AFTER survivors (not charged to `77d9146`; each has a ruling that lands the pin)
- **WB7b · §8.2 reading.** Above the bound, the refusal names ONE foreign principal instead of `min(bound, n)`, and
  its prose states no named-count. It passes R-Q5-1 (`1 <= named <= id_bound`) and every other a19 pin. It survives
  BECAUSE of reading §8.2 as committed ("at least one, at most the bound"). Amendment 20 R1 (exact
  `min(bound, distinct)` under the constant's perturbation) is its pin. ⚠ Fixture note: the first variant, WB7
  (prose "first 1 named"), was killed only INCIDENTALLY, by R-Q5-1's integer-truth check (`the refusal states [1]
  — not a TRUE count…`), not by a naming assertion. That is a fixture-reason kill, which is why WB7b exists.
  Separately, the author's "a smaller bound still passes" is FALSE for a smaller private LITERAL: `at-cap` seeds
  10 distinct foreign owners, all of whom must be named, so any literal below 10 fails. The live door is a
  shape-dependent sample, which WB7b shows.
- **§8.4 (operator unresolvable AND owned-but-unscoped).** Both references classify every owner as "other" when the
  operator is unresolved. That is unpinned by construction at `77d9146`; amendment 20 R2 rules it (name both
  refusals; owners unclassified). Not built — the reference already IS that build.
- **CD-1 (message backfill WHERE) / CD-2 (validity first).** Both references carry the `84af63f` behaviour, and both
  pass `77d9146`. Amendment 21 rules them. See FORK F-1 (§7) for the `brief` conflict CD-2 creates.

## §4 Wrong builds (each = my reference + ONE defect; driver verbatim §A.2, runner §A.3, probes §A.4)
Declared BEFORE any run (in `run_wb.sh`'s header): every WB passes ALL contract tests over the four files and fails
exactly its kill probe. A build counts as a SURVIVOR only after the full-suite leg (§4.2).

| WB | defect (routing / order / prose) | spec clause it violates | kill probe |
|---|---|---|---|
| WB1 | verb-level check CALLS THE shared function but ALSO consults a private owned-but-unscoped query (independent `INFO FOR DB` + `SELECT`) and refuses on either | a19 D-1 "ONE implementation … the verb-level check and the order guard both CALL it … sharing proven by MUTATION"; ROUTING IS NOT SHARING | K1 (reverse redirect: shared says clean on a poisoned store ⇒ no §2.1 teaching) |
| WB2 | order guard CALLS THE shared function but ANDs the retired `_owner_count(agent, none=True)` into the decision | D-1 "`_owner_count`'s agent use is retired"; same | K2 (reverse redirect: shared says un-migrated on a clean store ⇒ refuse) |
| WB3 | handler keeps the `84af63f` order (mint first) and, when the registry refuses, DELETES the keep it just minted (`delete_keep`, `member_of` cascades) | a19 D-2 "the handler refuses a blank role BEFORE `get_or_create_keyed`" | K3 (a spy on `get_or_create_keyed`: 0 calls for a blank role; control: 1 call for a valid register) |
| WB4 | the English gloss re-added in a LATER clause of both refusals (`must match <pattern>; that is lowercase letters…` / `must match <pattern> — lowercase letters…`) | a19 D-3 F-9 "DROP the English gloss in both refusals" | K4 (a DENYLIST probe — labelled; the recommended pin is a golden, §3) |
| WB7 | above the bound, names exactly ONE foreign principal (not `min(bound, n)`) | reading §8.2; amendment 20 R1 | none of mine — amendment 20 R1 is the ruled pin |

## §4.1 Wrong builds over the contract files (each alone; `run_wb.sh`; 474 collected = 462 contract + 12 probes)
Provenance for every row: `PROVENANCE …/scratchpad/adv-wb/loremaster/loremaster/__init__.py` (printed per run in
each `wb_*.log`). Contract-file failures = the failures OUTSIDE `test_adversary_a19_probes.py`.
| build | tail | contract-file failures | probe failures | reading |
|---|---|---|---|---|
| REF | `3 failed, 471 passed` | **0** | PD1, PD2, PQ1 (the spec probes; K1–K4 GREEN ⇒ satisfiable) | control |
| WB1 | `7 failed, 467 passed` | **0** | K1 ×4 + the 3 spec probes | SURVIVES the contract |
| WB2 | `4 failed, 470 passed` | **0** | K2 + 3 | SURVIVES |
| WB3 | `6 failed, 468 passed` | **0** | K3 ×3 (`''`, `'   '`, `'　'`) + 3 | SURVIVES |
| WB4 | `4 failed, 470 passed` | **0** | K4 + 3 | SURVIVES |
| WB7 | `5 failed, 469 passed` | R-Q5-1 `[above-cap]`, `[perturbed-bound]` (integer-truth: "states [1]") | 3 | KILLED — for a fixture reason (§3.1) |
| WB7b | `3 failed, 471 passed` | **0** | 3 | SURVIVES (§8.2 reading) |
Every patch asserts that its replacement landed exactly once (#194). Each kill probe goes RED only on its own build,
which is the evidence that each mutation is LIVE.

## §4.2 Full-suite leg (composite WB1+WB2+WB3+WB4+WB7b, lint-clean: ruff `All checks passed!`, typecheck every leg OK)
- Run #1 (2026-09-25, alone, `-n 12`, `free` avail 54 GB): `1 failed, 11528 passed, 62 skipped, 3 xfailed … in
  584.62s` · EXIT=1. The ONE failure: `test_memory_replay_fidelity_63b_ib.py::TestTheReplayCloseIsPairGuarded::
  test_a_cross_owner_replay_close_is_skipped_with_a_warning` — `surrealdb.errors.QueryError: … Transaction
  conflict: Resource busy. This transaction can be retried`, raised at `surrealdb/connections/utils_mixin.py:24`.
  It is NOT an a19 pin, and it is NOT on any path the composite diff (§A.5) touches. The file passed `12 passed`
  ×3 in isolation on the SAME composite tree. **I do not call it flaky**: an un-retried "can be retried" marker
  reaching a test means some call site bypasses the retry seam, and its calling frame is unidentified. Filed as
  finding **#486**.
- Run #2: same tree (md5 principals `a4bdb00a…` / agents `6c915049…` / server `be3c2582…`, unchanged), alone, `-n 12`: **`11529 passed, 62 skipped, 3 xfailed, 7 warnings in 554.63s (0:09:14)` · EXIT=0 · 0 failed.** **WB1, WB2, WB3, WB4 and WB7b SURVIVE THE FULL SUITE.** (Run #1's single red was the unrelated #486 site.)

## §5 SAT — the contract is satisfiable by an INDEPENDENT build
- **My reference, full suite ALONE `-n 12`, lint-clean (2026-09-25):**
  `11529 passed, 62 skipped, 3 xfailed, 7 warnings in 552.69s (0:09:12)` · `EXIT=0` · **0 failed.**
  Pre-checks: no other pytest in the process table, `free` avail 54 GB, `spike-surreal.service` active. The
  watchdog (15 GB, 10 s poll) wrote no FIRED line. ⚠ Its own exit line never landed either: the watchdog subshell
  was still sleeping when the runner script exited. So its liveness at the end is INFERRED, not observed. The run
  completed with 0 kills, so no firing is possible.
- This is **the author's exact count** (their `11529 passed, 62 skipped, 3 xfailed`), reproduced on a DIFFERENT
  build: same functions, independently written, and different refusal prose and order-refusal noun. The author's
  SAT claim is **CONFIRMED**.
- **Required-green enumeration, checked BEFORE judging any pin** (each GREEN on my reference, inside the SAT
  count):
  (1) single-principal stores proceed on every `--table`: `test_PRESERVED_…[memory|brief]`,
  `test_PRESERVED_a_legacy_unscoped_agent…`, the ii-a message suite, the 63a memory suites;
  (2) memory-only stores with no `agent` table: 63a/63b-ia memory suites (I hit the same `INFO FOR DB` requirement
  the author did, independently);
  (3) the existing 63c-i-a contract: R-Q5-1 ×6 including the integer-truth / birth-value / `by hand` legs,
  R-Q5-2/3, idempotent, only-the-legacy, the exempt token;
  (4) the amendment 13/14 refusal-count rules: every integer in my prose is a true count of a set the fixture seeds.
  My first WB7 is the positive control that the rule still bites;
  (5) both helper shapes: the `is_blank` legs `register` / `fake` / `handler` and the F5 exempt-token golden.
- **RED at `84af63f` (the author's claim), re-derived on the MAIN tree** (production `84af63f`, tests `77d9146`),
  with the author's exact node selection: **`29 failed, 21 passed in 13.77s`**. Every failure is an
  `AssertionError`/`pytest.fail` whose text names its defect, with 0 `TypeError`/`ImportError`/`AttributeError`.
  Distribution: R-Q5-1 F-1 fixed phrase ×6 · shared function missing ×5 · blank-role wrote keep ×3 · CA-1 ×5 ·
  ∀-tables memory/message/brief ×3 · SAME-teaching · CA-A · CONTROL · F-3 golden · F-9 ×2 · `is_blank[handler]`.
  **CONFIRMED.**
- **Typecheck/ruff on the main tree with the new pins** (`pending_contract_gate.py --currency --legs typecheck,ruff`):
  typecheck GREEN, ruff GREEN, so no `pending_contracts.yaml` entry is needed. **CONFIRMED.**
- **13 mutation proofs:** NOT re-run individually (declared). Corroborated independently. My first-reference bug
  (§2) independently re-derived the CA-1 fixture's discrimination (the M6/M7 class). WB7 re-derived R-Q5-1's
  integer leg. The four survivors are exactly the proofs' blind side: every a19 mutation is ONE-DIRECTIONAL, or
  observes an effect rather than a decision.
- **SAT defects found: none at `77d9146`.** Forward SAT risk: FORK F-1 (CD-2 vs `∀[brief]`), and the F-3 golden
  rejecting a parenthesised WHERE.

### §5.1 Spec probes on my reference, verbatim (2026-09-25; single-process, `-s`)
```
PD1 first=MigrateGovernedResult(table='message', scanned=1, backfilled=1, already_migrated=0, refused=False, reason=None)
PD1 rows=[{'id': RecordID(table_name=message, record_id='m1'), 'owner_agent': RecordID(table_name=agent, record_id='ownerless_scoped'), 'owner_principal': None, 'scope': 'keep:01M3DN682H0AGCSSZGS3MQ70NZ'}]
PD1 second=MigrateGovernedResult(table='message', scanned=1, backfilled=1, already_migrated=0, refused=False, reason=None)
PD2 reason="cannot migrate `message` rows before the `agent` table is migrated (1 NONE-owner agent(s) remain) — a message's owner_principal is read from sender.owner_principal, NONE for every un-migrated agent (§2.6 agent-first ORDER); run migrate-governed for `agent` first"
```
PD1: the backfilled message carries `owner_principal` NONE, and the second run reports `backfilled=1` again (the
owner-keyed message WHERE re-selects it). Amendment 21 CD-1's scope-keyed WHERE ends the re-stamp but not the NONE
owner (FORK F-2). PD2: 1 NONE-scope agent is served as "1 NONE-owner agent(s)" while 3 agents are NONE-owner (MP-4).

## §6 DUAL — what the OLD per-table code did, per `--table` (enumerated from `84af63f` source), diffed with the author's §7
Source read: `principals.migrate_governed`, `_migrate_memory_scope`, `_migrate_agent_owner`,
`_migrate_message_owner`, `_dispatch_migrate_governed` at `84af63f`. Items the author's §7 does NOT carry are marked **NEW**.

| # | old behaviour at `84af63f` | fate under a19 | in author §7? | adjudication |
|---|---|---|---|---|
| m1 | memory: operator-ambiguity refusal first, no store write | preserved on single-principal stores; on a multi-principal store the §2.1 refusal now wins | partly (§8.4) | amendment 20 §8.4 now rules "name BOTH" — not pinned in `77d9146` (READING/RULED-AFTER) |
| m2 | memory: mints the project keep even when 0 rows are unmigrated | preserved | no | no pin needed (idempotent CAS) |
| m3 | memory: no agent precondition | changed deliberately (D-1) | yes | pinned (∀`[memory]`) |
| m4 | memory on a store with NO `agent` table | preserved | yes | SAT-only (no dedicated pin; 63a suites cover it) |
| a1 | agent: operator-ambiguity refusal BEFORE the row precondition | **order inverted** (verb check first) | §8.4 only | amendment 20 §8.4 ruled; unpinned at `77d9146` |
| a2 | agent refusal carried TRUE receipts `scanned=unmigrated+already`, `already_migrated=already` | **NEW — changed**: both the author's and my reference return `scanned=0, already_migrated=0` on the verb-level refusal | **no** | spec-silent. NOT served by the CLI (`_dispatch_migrate_governed` prints only `reason` on refusal), so LOW; but `MigrateGovernedResult` is a typed receipt whose `scanned=0` over a non-empty table is a count that does not describe its set (TRUST law). Operator/sidecar: either rule "refusal receipts are 0 by definition" in the model docstring, or keep true counts. |
| a3 | agent backfill `WHERE scope IS NONE` | changed (F-3) | yes | pinned (golden) |
| g1 | message order guard keyed on `owner_principal IS NONE` | re-keyed to `scope IS NONE` | yes | pinned (CA-A + CONTROL + sharing) — but ONE-DIRECTION sharing (§4 MP-1/MP-2) |
| g2 | order refusal text: `"({n} NONE-owner agent(s) remain)"` — its count and noun AGREED because the count WAS the NONE-owner count | **NEW — the noun/count agreement is lost** unless the text is re-worded: the count is now NONE-scope, and ownerless-SCOPED agents (the a19 CONTROL population) are NONE-owner but not counted | author §9 CD-3 (unpinned) | **MISSING PIN** MP-4 (§4): my reference kept the old noun and passes the whole contract |
| g3 | message: the old owner-keyed guard GUARANTEED every sender had an owner before the backfill, so `owner_principal = sender.owner_principal` never stamped NONE for a live sender | **NEW — virtue lost**: with the scope-keyed guard, a message from an ownerless-SCOPED sender proceeds and is stamped `owner_principal` NONE; with the (unchanged at a19) owner-keyed message WHERE, it is re-counted and re-stamped on every run | **no** | spec-silent → sidecar ruling; interacts with amendment 21 CD-1 (probe PD1, §5) |
| b1 | unsupported table (`brief`, typos): "does not support … at packet 63b" with ZERO store I/O | multi-principal stores: §2.1 teaching (D-1 names `brief`); every table now costs the precondition read | yes (CD-2) | amendment 21 CD-2 rules validity-first — **conflicts with a19's ∀`[brief]` pin** unless `brief` counts as "valid" (FORK F-1, §7) |

## §7 Forks (a sentence with two readings that produce different code — brief-base §2)
- **F-1 · amendment 21 CD-2 vs amendment 19 D-1 on `brief`.** D-1: "`--table agent|memory|message|brief` each refuse
  with the SAME teaching" — pinned at `77d9146` by ∀`[brief]`, SAME-teaching, VERB-sharing`[brief]`,
  CA-1`[brief]`. CD-2: "table validity is checked FIRST … an unsupported table on a multi-principal store → the
  'not supported' teaching, ZERO store reads". `brief` IS unsupported at i-a ("does not support … brief lands 63c").
  Reading A: "valid" = the governed-table set {agent, memory, message, brief} (then `brief` still gets §2.1 on a
  multi-principal store, and only non-governed names get zero-read "not supported"). Reading B: "valid" =
  the SUPPORTED set {agent, memory, message} (then `brief` answers "not supported" and FOUR a19 pins go RED on a
  correct CD-2 build). **Recommend A** (it keeps D-1's explicit list true and still answers typos honestly); the
  a19a addendum must say which, or its builder is trapped between two pins.
- **F-2 · the ownerless-SCOPED sender (DUAL g3, probe PD1).** D-1's CONTROL population makes the order guard pass
  a store where an agent is scoped but ownerless. What the message leg then stamps for THAT sender's messages
  (`owner_principal` NONE) is spec-silent at a19; amendment 21 CD-1's WHERE change fixes the re-stamp loop but not
  the NONE owner. Sidecar: is a NONE-owner, project-scoped message the intended outcome, or must the order guard
  (or the message leg) also require the sender to be OWNED?
- **F-3 · refusal receipts (DUAL a2).** Zeroed `scanned`/`already_migrated` on the verb-level refusal: rule it.

## §8 P1c REACH — for every ∀ pin: is the set DERIVED, and does a test go RED when it grows?
| ∀ pin | set it ranges over | derived or hand-list | RED when the set grows? | verdict |
|---|---|---|---|---|
| ∀-tables refusal / SAME teaching / VERB sharing / CA-1 property | `_MIGRATE_TABLES` = the ruling's 4 | hand-list (stated in-line: `--table` has no `choices`) | no | ACCEPTABLE as a stated bound at `77d9146`, BUT amendment 21 CD-2 creates a production "supported/valid set" named by the not-supported refusal — once it exists the ∀ pins must DERIVE from it (the pin's own re-open trigger fires with the addendum) |
| byte-inert store | `_BYTE_INERT_TABLES` = 4 governed + `keep`, `member_of`, `principal` | hand-list | no | covers today's writers (verified: `KeepStore.get_or_create_keyed` writes only `keep` + a `member_of` RELATE, client ULID ids). A derived set (`INFO FOR DB` tables at snapshot time) costs one query and closes the class; recommended |
| blank-role byte-inert | `_KEEP_TABLES` = `keep`, `member_of`, `agent` | hand-list | no | same; and see MP-3 — byte-identity cannot distinguish refuse-before from undo-after |
| blank-role decision consumers | `_BLANK_ROLE_DECISION_CONSUMERS` = register, fake, handler | hand-list | no | the `handler` leg OBSERVES an effect (no keep left), not the handler's DECISION — see MP-3 |
| CA-1 routing | module-level bindings of THE `sanitise_line` object | DERIVED (identity sweep + `expect_in`) | yes | GOOD |
| F-9 one spelling | registry refusal + server refusal | hand-list of 2 sites | no | awk sweep (the text-search tool is hook-blocked, #473) of production uses of `AGENT_NAME_PATTERN.pattern`: `agents.py` refusal, `server.py` refusal, `server.py` tool-description `Field` (not a refusal), `surreal_schema.py` DDL ASSERT (not prose). The 2 are complete at `84af63f`; a third refusal site would not be caught |
| F-3 golden | the agent leg's statement | one leg | no | amendment 21's rider (every leg's golden carries `scope IS NONE`) is the fix; ruled after `77d9146` |
| R-Q5-1 populations | 6 named populations | hand-list (appropriate — fixtures) | n/a | GOOD: `at-cap` (10 distinct foreign owners, all must be named) kills any private principal bound below the constant; `perturbed-bound` kills a restated `10` |

## §9 LIVE-PRODUCTION-DEFECT — ⚠ FLAGGED LOUDLY (outside §W; the operator owns scope)
**Finding #485 (filed 2026-09-25).** **PQ1 · a credentialed register refused by a registry rule OTHER than blank role still mints the session keep, claims
its keeper, and then DENIES a third party.** This is D-2's own class (#97 plus the SF-63-1 third-party consequence),
on a branch D-2 does not touch. The QUANTIFIER LAW applies: D-2 derived "refuse before the mint" over ONE registry
refusal (blank role) and stated it over "a rejected register".
- Construction (probe PQ1, §A.4): an OWNERLESS agent `shared-name` already exists in session `wave5` (a
  tokenless or pre-63b register; no keep is minted). alice (credentialed) registers `shared-name` in `wave5` with a
  DIFFERENT role. The handler runs `get_or_create_keyed(session:wave5)` → alice becomes keeper → the registry
  raises `AgentIdentityConflictError`.
- Reproduced at PRISTINE `84af63f` production bytes (`git show 84af63f:…` into the scratch tree, 2026-09-25) and on
  my a19 reference. Served, verbatim:
  `refusal = agent 'shared-name' is already registered with role ```builder``` (you sent ```scout```) — names are never reused; …`
  `keeps_after = [{… 'key': 'session:wave5', 'keeper': RecordID(principal, <alice>), 'type': 'session'}]`
  `bob = GovernedDenied: session 'wave5' is kept by another principal — you are not householded in it; …`
- The same shape applies to every refusal the registry can raise after the mint (role/spawned_by write-once
  conflict, `RetiredAgentError`, the provenance-pair check). I probed only the role conflict.
- Recommended shape (for the operator, not decided here): the handler validates everything the registry can
  refuse WITHOUT a store write BEFORE the mint, and a refusal that needs the row (conflict / retired) either reads
  the row before the mint, or the mint and the agent write share one transaction.

## §10 §8-reading dependence (does a wrong build survive BECAUSE of a reading?)
| reading (author §8) | ruled | survivor that depends on it |
|---|---|---|
| §8.1 operator-only store still refused; E3 diagnosis | amendment 20: CONFIRMED | none — the `operator-owned` population pins both the refusal and the diagnosis; my reference's E3 wording passes |
| §8.2 principal-naming bound = `_REFUSAL_ID_SAMPLE_SIZE`, "≥1, ≤bound" above it | amendment 20: CONFIRMED + rider R1 (exact `min`) | **WB7b survives BECAUSE of §8.2 as committed**; R1 kills it. A private SMALLER literal does NOT survive (`at-cap`) — the author's own note overstated the door |
| §8.3 exact name + `StoreHandle`, return shape free | amendment 20: CONFIRMED | WB1/WB2 do not depend on it — they CALL the exactly-named function. They survive because the redirect is one-directional, so a type-agnostic redirect in BOTH directions (K1/K2) kills them without constraining the return shape |
| §8.4 operator unresolvable + owned-but-unscoped: unpinned | amendment 20: RULED (name both; owners unclassified) | both references (mine and the author's) classify owners as "other" — survives by construction at `77d9146`; R2 is its pin |

## §A Instruments (verbatim — the scratch trees are disposable by design)

### §A.1 Reference build patcher (`adv_ref_patch.py`; applied to a `scratch_copy.sh` tree of `84af63f` production, then `ruff check --fix` sorted one lazy import)
```python
"""adversary-63c-i-a-a19 — independent reference fix build for amendment 19 §W items 1-5 (+CA-1).

Applied to a scratch_copy.sh tree at 84af63f production. Each replacement asserts it landed exactly once.
Usage: python adv_ref_patch.py <scratch-root>
"""

import pathlib
import sys

ROOT = pathlib.Path(sys.argv[1])


def patch(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{rel}: expected exactly one match, found {count}: {old[:80]!r}"
    path.write_text(text.replace(old, new))


P = "loremaster/loremaster/principals.py"

patch(P, "from loremaster.sanitise import safe_str\n", "from loremaster.sanitise import safe_str, sanitise_line\n")

# item 1: verb-level store precondition, before any leg
patch(
    P,
    """    from loremaster.governed import MigrateGovernedResult

    if table == MEMORY_TABLE:
        return await _migrate_memory_scope(store, keep_store, principal_store)""",
    """    from loremaster.governed import MigrateGovernedResult

    preconditions = await _agent_migration_preconditions(store)
    if preconditions.owned_unscoped:
        operator = await resolve_operator_principal(principal_store)
        return MigrateGovernedResult(
            table=table,
            scanned=0,
            backfilled=0,
            already_migrated=0,
            refused=True,
            reason=_owned_unscoped_refusal(preconditions, operator),
        )
    if table == MEMORY_TABLE:
        return await _migrate_memory_scope(store, keep_store, principal_store)""",
)

# the shared function + the derived diagnosis
patch(
    P,
    "_REFUSAL_ID_SAMPLE_SIZE = 10\n",
    '''_REFUSAL_ID_SAMPLE_SIZE = 10


class AgentMigrationPreconditions(BaseModel):
    """THE agent-migration state (amendment 19 D-1), read once by the verb and the order guard."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    unscoped_count: int
    owned_unscoped: list[tuple[Any, Any]]


async def _agent_migration_preconditions(store: StoreHandle) -> AgentMigrationPreconditions:
    """The ONE shared predicate: the NONE-scope agent count and every owned-but-unscoped (id, owner)."""
    info = await run_query(
        acquire=store.acquire,
        drop=store.drop,
        url=store.url,
        noun="governed agent table probe",
        label="governed.agent_probe.rejected",
        statement="INFO FOR DB",
        params={},
        logger=logger,
    )
    tables = info.get("tables", {}) if isinstance(info, dict) else {}
    if AGENT_TABLE not in tables:
        return AgentMigrationPreconditions(unscoped_count=0, owned_unscoped=[])
    unscoped_count = await _scope_count(store, AGENT_TABLE, none=True)
    rows = await run_query(
        acquire=store.acquire,
        drop=store.drop,
        url=store.url,
        noun="governed agent row precondition",
        label="governed.agent_precondition.rejected",
        statement=(
            f"SELECT id, owner_principal FROM {AGENT_TABLE} "
            "WHERE scope IS NONE AND owner_principal IS NOT NONE"
        ),
        params={},
        logger=logger,
    )
    owned = sorted(
        ((row.get("id"), row.get("owner_principal")) for row in (rows or []) if isinstance(row, dict)),
        key=lambda pair: str(pair[0]),
    )
    return AgentMigrationPreconditions(unscoped_count=unscoped_count, owned_unscoped=owned)


def _bare_id(value: Any) -> str:
    if hasattr(value, "id"):  # a RecordID: its id is already bare (and may itself contain ':')
        return str(value.id)
    text = str(value)
    return text.partition(":")[2] or text


def _owned_unscoped_refusal(preconditions: AgentMigrationPreconditions, operator: Any) -> str:
    """The derived §2.1 refusal (F-1 + CA-1): count, bounded sanitised ids, owners classified."""
    offending = preconditions.owned_unscoped
    offending_count = len(offending)
    shown = [sanitise_line(str(row_id)) for row_id, _owner in offending[:_REFUSAL_ID_SAMPLE_SIZE]]
    operator_bare = _bare_id(operator.id) if operator is not None else None
    operator_rows = sum(1 for _row, owner in offending if _bare_id(owner) == operator_bare)
    foreign = sorted({_bare_id(owner) for _row, owner in offending if _bare_id(owner) != operator_bare})
    parts = [f"{offending_count} agent row(s) carry an owner but no scope (§2.1)."]
    if operator_rows:
        parts.append(
            f"{operator_rows} of them are owned by the operator — registered by a pkt-62–63b image; "
            "see amendment-1 E3."
        )
    if foreign:
        named = [sanitise_line(owner) for owner in foreign[:_REFUSAL_ID_SAMPLE_SIZE]]
        parts.append(
            f"{offending_count - operator_rows} are owned by {len(foreign)} other principal(s) "
            f"(first {len(named)} named: {', '.join(named)})."
        )
    parts.append(
        f"First {len(shown)} of {offending_count} ids shown: {', '.join(shown)}. Adjudicate these rows "
        "by hand before migrating ANY governed table; no row was stamped"
    )
    return " ".join(parts)
''',
)

# agent leg: the row precondition moved to the verb; F-3 self-guarding WHERE
patch(
    P,
    """    owned_unscoped_rows = await run_query(
        acquire=store.acquire,
        drop=store.drop,
        url=store.url,
        noun="governed agent row precondition",
        label="governed.agent_precondition.rejected",
        statement=(
            f"SELECT VALUE id FROM {AGENT_TABLE} "
            "WHERE scope IS NONE AND owner_principal IS NOT NONE"
        ),
        params={},
        logger=logger,
    )
    owned_unscoped_ids = sorted(str(row_id) for row_id in (owned_unscoped_rows or []))
    if owned_unscoped_ids:""",
    """    owned_unscoped_ids: list[str] = []
    if owned_unscoped_ids:""",
)
patch(P, 'owner_agent = id, scope = $scope WHERE scope IS NONE"', 'owner_agent = id, scope = $scope WHERE scope IS NONE AND owner_principal IS NONE"')

# message order guard: THE shared function
patch(
    P,
    "    unmigrated_agents = await _owner_count(store, AGENT_TABLE, none=True)\n",
    "    unmigrated_agents = (await _agent_migration_preconditions(store)).unscoped_count\n",
)

# item 5: gloss dropped (registry) + server spelling
A = "loremaster/loremaster/agents.py"
patch(
    A,
    """f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern} (lowercase "
                    f"letters, digits, '_' or '-', starting with a letter or digit); nothing was "
                    f"written""",
    """f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern}; nothing was "
                    f"written""",
)
SV = "loremaster/loremaster/server.py"
patch(SV, '"{label} does not match {pattern} — names must stay in "', '"{label} must match {pattern} — names must stay in "')

# item 3: handler refuses a blank role BEFORE the keep mint, through the shared is_blank
patch(
    SV,
    """        session_keep_bare: str | None = None
        if principal is not None:
            principal_bare = str(principal.id).split(":", 1)[-1]""",
    """        session_keep_bare: str | None = None
        from lorerunes import is_blank  # noqa: PLC0415 - house lazy-import idiom

        from loremaster.agents import InvalidAgentIdentityError  # noqa: PLC0415

        if is_blank(role):
            raise InvalidAgentIdentityError(
                "agent role must not be blank; nothing was written — register again with a "
                "role (e.g. 'builder')"
            )
        if principal is not None:
            principal_bare = str(principal.id).split(":", 1)[-1]""",
)
print("patched")
```

### §A.2 Wrong-build driver (`adv_wrong_builds.py`; each build = the reference bytes in `ref-prod/` + the named defects)
```python
"""adversary-63c-i-a-a19 — wrong builds against the a19 contract (77d9146).

Each wrong build = the adversary's REFERENCE build (adv_ref_patch.py over 84af63f) + ONE defect.
Usage: python adv_wrong_builds.py <tree> <ref-prod-dir> <WB-id>[,<WB-id>...]   (restores reference first)
Every replacement asserts it landed exactly once (#194: evidence the mutation landed).
"""

import pathlib
import shutil
import sys

TREE = pathlib.Path(sys.argv[1])
REF = pathlib.Path(sys.argv[2])
BUILDS = sys.argv[3].split(",") if len(sys.argv) > 3 else []
PKG = TREE / "loremaster" / "loremaster"
P, A, SV = "principals.py", "agents.py", "server.py"

for name in (P, A, SV):  # restore the reference bytes
    shutil.copyfile(REF / name, PKG / name)


def patch(name: str, old: str, new: str) -> None:
    path = PKG / name
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{name}: expected exactly one match, found {count}: {old[:90]!r}"
    path.write_text(text.replace(old, new))


def wb1() -> None:
    """ROUTING-NOT-SHARING at the verb: the verb-level check calls THE shared function but ALSO ORs in a
    private owned-but-unscoped query (the decision re-derived privately beside the shared one)."""
    patch(
        P,
        """    preconditions = await _agent_migration_preconditions(store)
    if preconditions.owned_unscoped:""",
        """    preconditions = await _agent_migration_preconditions(store)
    if not preconditions.owned_unscoped:
        private_info = await run_query(
            acquire=store.acquire, drop=store.drop, url=store.url, noun="private agent probe",
            label="governed.private_probe.rejected", statement="INFO FOR DB", params={}, logger=logger,
        )
        if AGENT_TABLE in (private_info.get("tables", {}) if isinstance(private_info, dict) else {}):
            private_rows = await run_query(
                acquire=store.acquire, drop=store.drop, url=store.url, noun="private agent precondition",
                label="governed.private_precondition.rejected",
                statement=(
                    f"SELECT id, owner_principal FROM {AGENT_TABLE} "
                    "WHERE scope IS NONE AND owner_principal IS NOT NONE"
                ),
                params={}, logger=logger,
            )
            if private_rows:
                preconditions = AgentMigrationPreconditions(
                    unscoped_count=preconditions.unscoped_count,
                    owned_unscoped=sorted(
                        ((row["id"], row["owner_principal"]) for row in private_rows),
                        key=lambda pair: str(pair[0]),
                    ),
                )
    if preconditions.owned_unscoped:""",
    )


def wb2() -> None:
    """ROUTING-NOT-SHARING at the order guard: it calls THE shared function but ANDs a private owner-keyed
    count (the retired _owner_count agent use) into the decision."""
    patch(
        P,
        "    unmigrated_agents = (await _agent_migration_preconditions(store)).unscoped_count\n",
        "    unmigrated_agents = (await _agent_migration_preconditions(store)).unscoped_count\n"
        "    if not await _owner_count(store, AGENT_TABLE, none=True):\n"
        "        unmigrated_agents = 0\n",
    )


def wb3() -> None:
    """D-2 by COMPENSATION: the handler has NO pre-mint blank-role check; it mints the session keep as at
    84af63f and, when the registry refuses, DELETES the keep it just minted (member_of cascades)."""
    patch(
        SV,
        """        if is_blank(role):
            raise InvalidAgentIdentityError(
                "agent role must not be blank; nothing was written — register again with a "
                "role (e.g. 'builder')"
            )
""",
        "",
    )
    patch(
        SV,
        "            session_keep = await keep_store.get_or_create_keyed(\n",
        "            pre_existing_keep = await keep_store.get_by_key(f\"session:{session}\")\n"
        "            session_keep = await keep_store.get_or_create_keyed(\n",
    )
    patch(
        SV,
        """        result = await self.agent_registry.register(
            agent,
            session=session,
            role=role,
            model=model,
            spawned_by=spawned_by,
            task_id=task_id,
            cadence=cadence,
            owner_principal_id=principal_bare,
            session_keep_id=session_keep_bare,
        )""",
        """        try:
            result = await self.agent_registry.register(
                agent,
                session=session,
                role=role,
                model=model,
                spawned_by=spawned_by,
                task_id=task_id,
                cadence=cadence,
                owner_principal_id=principal_bare,
                session_keep_id=session_keep_bare,
            )
        except InvalidAgentIdentityError:
            if session_keep is not None and pre_existing_keep is None and self._keep_store is not None:
                await self._keep_store.delete_keep(keep_id=str(session_keep.id))
            raise""",
    )


def wb4() -> None:
    """F-9 re-added in a LATER clause of both refusals (the rule clause itself is the bare pattern)."""
    patch(
        A,
        'f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern}; nothing was "',
        'f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern}; that is lowercase letters, digits, '
        "'_' or '-', starting with a letter or digit; nothing was \"",
    )
    patch(
        SV,
        '"{label} must match {pattern} — names must stay in "\n                            "the safe charset.',
        '"{label} must match {pattern} — lowercase letters, digits, \'_\' or \'-\', starting with a "\n'
        '                            "letter or digit; names must stay in the safe charset.',
    )


def wb7() -> None:
    """§8.2 door: above the bound the refusal names exactly ONE other principal (not min(bound, n))."""
    patch(
        P,
        "        named = [sanitise_line(owner) for owner in foreign[:_REFUSAL_ID_SAMPLE_SIZE]]\n",
        "        named = [sanitise_line(owner) for owner in foreign[:_REFUSAL_ID_SAMPLE_SIZE]]\n"
        "        if len(foreign) > _REFUSAL_ID_SAMPLE_SIZE:\n"
        "            named = named[:1]\n",
    )


def wb7b() -> None:
    """WB7 WITHOUT a stated named-count: above the bound names ONE principal, prose '(named: X)'."""
    wb7()
    patch(
        P,
        'f"(first {len(named)} named: {\', \'.join(named)})."',
        'f"(named: {\', \'.join(named)})."',
    )


def wb8() -> None:
    """§8.4 door: operator unresolvable → every owner classified 'other' (the reference already does
    this: operator None ⇒ operator_bare None). NO-OP marker build: kept for the table, never run."""


for build in BUILDS:
    {"WB1": wb1, "WB2": wb2, "WB3": wb3, "WB4": wb4, "WB7": wb7, "WB7b": wb7b}[build]()
print(f"applied: {BUILDS or 'reference only'}")
```

### §A.3 Runners (`run_wb.sh` — contract files + probes; `run_suite.sh` — full suite ALONE `-n 12` + 15 GB PID watchdog)
```bash
#!/usr/bin/env bash
# adversary-63c-i-a-a19 — run ONE wrong build (or the reference) over the a19 contract files + the probe file.
# usage: run_wb.sh <WB-ids comma-separated | REF> <logname>
# DECLARED EXPECTATION (written before any run): every WB passes ALL contract tests (0 failed among the
# contract files) and fails exactly its kill probe; REF fails only the spec probes PD1/PD2/PQ1 that
# encode behaviour NOT required by 77d9146 (they record what the reference does).
set -u
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/1a4b0fa1-51cf-4cd4-a554-3cfe55e75f59/scratchpad
T=$S/adv-wb
builds=$1; log=$S/$2
if [ "$builds" = REF ]; then python3 $S/adv_wrong_builds.py $T $S/ref-prod > "$log" 2>&1
else python3 $S/adv_wrong_builds.py $T $S/ref-prod "$builds" > "$log" 2>&1; fi || { echo "PATCH FAILED" >> "$log"; exit 3; }
cp $S/test_adversary_a19_probes.py $T/loremaster/tests/test_adversary_a19_probes.py
cd $T || exit 9
uv run python -c "import loremaster; print('PROVENANCE', loremaster.__file__)" >> "$log" 2>&1
timeout 1200 uv run pytest -n 8 -q -p no:cacheprovider --tb=line -rfE \
  loremaster/tests/test_fixwave_a19_63c_i_a.py loremaster/tests/test_agent_governance_63c_i_a.py \
  loremaster/tests/test_agent_registry.py loremaster/tests/test_message_migrate_63b_ii_a.py \
  loremaster/tests/test_adversary_a19_probes.py >> "$log" 2>&1
echo "EXIT=$?" >> "$log"

# ---- run_suite.sh
#!/usr/bin/env bash
# usage: run_suite.sh <tree> <logfile>  — full suite ALONE -n 12, PID watchdog at 15 GB (polls 10 s)
tree=$1; log=$2
cd "$tree" || exit 9
uv run pytest -n 12 -q -p no:cacheprovider --tb=line > "$log" 2>&1 &
pid=$!
( while kill -0 $pid 2>/dev/null; do
    avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
    if [ "$avail" -lt 15 ]; then echo "WATCHDOG FIRED avail=${avail}G killing $pid" >> "$log.watchdog"; kill $pid; pkill -P $pid; fi
    sleep 10
  done; echo "watchdog: pytest $pid exited" >> "$log.watchdog" ) &
wait $pid; rc=$?
echo "EXIT=$rc" >> "$log"
```

### §A.4 Probe / kill-pin file (`test_adversary_a19_probes.py`, copied into the scratch tree only)
```python
"""adversary-63c-i-a-a19 — candidate kill pins + spec probes (SCRATCH ONLY; never committed by me).

K1 — the verb-level check moves with THE shared function in the REVERSE direction (shared says clean on a
     poisoned store ⇒ the verb does not serve the §2.1 teaching). Kills WB1.
K2 — the order guard moves in the REVERSE direction (shared says un-migrated on a clean store ⇒ refuse).
     Kills WB2.
K3 — a blank-role register never CALLS get_or_create_keyed (refuse BEFORE the mint, not undo after). Kills WB3.
K4 — PROBE (a denylist, labelled as such — the recommended pin is a golden, see the report): neither
     identity refusal restates the rule in English anywhere outside the fence. Kills WB4.
PD1 — DUAL probe: a legacy message whose sender is OWNERLESS but SCOPED (the a19 CONTROL population) —
      what does the message leg stamp, and is a re-run idempotent?
PQ1 — D-2 QUANTIFIER probe: a credentialed register refused by a registry rule OTHER than blank role
      (write-once role conflict on a pre-existing ownerless agent) — does it leave the session keep minted?
"""

from __future__ import annotations

import re
from typing import Any

import pytest
from _governed_contract import (
    AGENT_TABLE,
    MEMORY_TABLE,
    MESSAGE_TABLE,
    credentialed_app_context,
    seed_agent_governed,
    seed_agent_legacy,
    seed_message_legacy,
)
from _surreal_harness import run
from lorerunes.pdp import keep_scope
from test_fixwave_a19_63c_i_a import (
    _BRIEF_TABLE,
    _DIM,
    _MIGRATE_TABLES,
    _governed_world,
    _redirect_the_shared_preconditions,
    _registry_refusal,
    _seed_clean_single_principal_store,
    _seed_multi_principal_store,
    _server_refusal,
    _snapshot,
)

from loremaster.agents import AGENT_NAME_PATTERN, AgentRegistryError


@pytest.mark.parametrize("table", _MIGRATE_TABLES)
async def test_K1_verb_level_moves_in_reverse(monkeypatch: pytest.MonkeyPatch, table: str) -> None:
    async with _governed_world() as twin, _governed_world() as world, _governed_world() as clean:
        await _seed_multi_principal_store(twin)
        baseline = await twin.migrate(table)
        assert "by hand" in str(baseline.reason or "").lower(), f"BASELINE must be refused: {baseline!r}"
        await _seed_multi_principal_store(world)
        await _seed_clean_single_principal_store(clean)
        calls = _redirect_the_shared_preconditions(monkeypatch, clean.handle)
        result = await world.migrate(table)
        assert calls["count"] >= 1
        assert "by hand" not in str(result.reason or "").lower(), (
            f"--table {table}: THE shared function says the store is clean, yet the verb still served the "
            f"§2.1 teaching — it decides with a PRIVATE copy beside the shared one: {result!r}"
        )


async def test_K2_order_guard_moves_in_reverse(monkeypatch: pytest.MonkeyPatch) -> None:
    async with _governed_world() as twin, _governed_world() as world, _governed_world() as unmigrated:
        for target in (twin, world):
            await _seed_clean_single_principal_store(target)
        baseline = await twin.migrate(MESSAGE_TABLE)
        assert baseline.refused is False, f"BASELINE: the clean twin must proceed: {baseline!r}"
        await seed_agent_legacy(unmigrated.connection, row_id="legacy_0", name="legacy-0", session="s1")
        calls = _redirect_the_shared_preconditions(monkeypatch, unmigrated.handle)
        before = await _snapshot(world.connection)
        result = await world.migrate(MESSAGE_TABLE)
        assert calls["count"] >= 1
        assert result.refused is True and before == await _snapshot(world.connection), (
            "THE shared function reports an un-migrated agent, yet the order guard let the message leg "
            f"proceed — it ANDs a private count into the decision: {result!r}"
        )


@pytest.mark.parametrize("blank_role", ["", "   ", "　"])
async def test_K3_blank_role_never_reaches_the_mint(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any, blank_role: str
) -> None:
    async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM) as world:
        ctx = world["ctx"]
        world["holder"]["email"] = world["emails"]["alice"]
        keep_store = ctx._keep_store
        real = keep_store.get_or_create_keyed
        calls = {"count": 0}

        async def counting(*args: Any, **kwargs: Any) -> Any:
            calls["count"] += 1
            return await real(*args, **kwargs)

        monkeypatch.setattr(keep_store, "get_or_create_keyed", counting)
        await ctx.comms(action="register", agent="control", session="wave-ok", role="builder")
        assert calls["count"] == 1, "CONTROL: the spy must see a valid register's mint"
        with pytest.raises(AgentRegistryError):
            await ctx.comms(action="register", agent="blank-role", session="wave9", role=blank_role)
        assert calls["count"] == 1, (
            "D-2: a blank-role register reached get_or_create_keyed — it must be refused BEFORE the mint, "
            "not undone after it"
        )


def _prose_outside_fence(message: str) -> str:
    return message.split("The rejected value was:", 1)[0]


async def test_K4_PROBE_no_english_restatement_of_the_rule() -> None:
    for source, message in (
        ("registry", await _registry_refusal("Not A Name!")),
        ("server", _server_refusal("Not A Name!")),
    ):
        prose = _prose_outside_fence(message).replace(AGENT_NAME_PATTERN.pattern, "<PATTERN>")
        assert not re.search(r"lowercase|letters?\b|digits?\b|starting with", prose, re.IGNORECASE), (
            f"F-9: the {source} refusal restates the rule in English outside the rule clause: {prose!r}"
        )


async def test_PD1_ownerless_scoped_sender_message() -> None:
    async with _governed_world() as world:
        scope = keep_scope("sessionkeeppd1")
        await seed_agent_governed(
            world.connection, row_id="ownerless_scoped", name="ownerless-scoped", session="s1",
            owner_principal=None, owner_agent=None, scope=scope,
        )
        await seed_message_legacy(world.connection, sender_id="ownerless_scoped", session="s1", seq=1, row_id="m1")
        first = await world.migrate(MESSAGE_TABLE)
        rows_after_first = await run(world.connection, "SELECT id, owner_principal, owner_agent, scope FROM message")
        second = await world.migrate(MESSAGE_TABLE)
        print(f"\nPD1 first={first!r}\nPD1 rows={rows_after_first!r}\nPD1 second={second!r}")
        assert first.refused is False
        assert second.backfilled == 0, (
            f"PD1: the message leg is NOT idempotent for an ownerless-scoped sender — it re-stamps: {second!r}"
        )
        assert rows_after_first[0].get("owner_principal") is not None, (
            f"PD1: a backfilled message carries owner_principal NONE (its sender is ownerless): {rows_after_first!r}"
        )


async def test_PQ1_role_conflict_register_leaves_no_keep(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    async with credentialed_app_context(
        monkeypatch, tmp_path, principals={"alice": "member", "bob": "member"}, dim=_DIM
    ) as world:
        ctx, admin_conn = world["ctx"], world["admin_conn"]
        # a pre-existing OWNERLESS agent (a tokenless / pre-63b register) — no session keep minted
        await ctx.agent_registry.register("shared-name", session="wave5", role="builder")
        keeps_before = await run(admin_conn, "SELECT * FROM keep ORDER BY id")
        world["holder"]["email"] = world["emails"]["alice"]
        with pytest.raises(AgentRegistryError) as caught:
            await ctx.comms(action="register", agent="shared-name", session="wave5", role="scout")
        keeps_after = await run(admin_conn, "SELECT * FROM keep ORDER BY id")
        print(f"\nPQ1 refusal={caught.value!s}\nPQ1 keeps_after={keeps_after!r}")
        world["holder"]["email"] = world["emails"]["bob"]
        bob_outcome = "ok"
        try:
            await ctx.comms(action="register", agent="bobs-agent", session="wave5", role="builder")
        except Exception as error:  # noqa: BLE001 - probe records the outcome
            bob_outcome = f"{type(error).__name__}: {error}"
        print(f"PQ1 bob={bob_outcome}")
        assert keeps_after == keeps_before, (
            f"#97: a REFUSED register (role conflict) minted the session keep and claimed its keeper: "
            f"{keeps_after!r}; bob afterwards: {bob_outcome}"
        )


async def test_PD2_order_refusal_count_matches_its_noun() -> None:
    """CD-3 door: the order-guard refusal's served count must describe the set its NOUN names. Population:
    ONE legacy (ownerless, unscoped) agent + TWO ownerless-SCOPED agents ⇒ 1 un-migrated (NONE-scope) agent,
    3 NONE-owner agents. A refusal saying '1 NONE-owner agent(s) remain' names a set of 3 with a count of 1."""
    async with _governed_world() as world:
        await seed_agent_legacy(world.connection, row_id="legacy_0", name="legacy-0", session="s1")
        for index in range(2):
            await seed_agent_governed(
                world.connection, row_id=f"ownerless_scoped_{index}", name=f"ownerless-scoped-{index}",
                session="s1", owner_principal=None, owner_agent=None, scope=keep_scope("sessionkeeppd2"),
            )
        await seed_message_legacy(world.connection, sender_id="legacy_0", session="s1", seq=1, row_id="m1")
        result = await world.migrate(MESSAGE_TABLE)
        reason = str(result.reason or "")
        print(f"\nPD2 reason={reason!r}")
        assert result.refused is True
        assert not re.search(r"\b1 NONE-owner agent", reason), (
            f"the order refusal serves a NONE-SCOPE count (1) under the NONE-OWNER noun (3 such agents): {reason!r}"
        )
```

### §A.5 Composite full-suite build = reference + WB1,WB2,WB3,WB4,WB7b, AFTER lint cleanups (unused `is_blank` import removed by `ruff --fix`; three string re-wraps). md5: principals `a4bdb00a…`, agents `6c915049…`, server `be3c2582…`
```diff
--- ref-prod/principals.py	2026-09-25 21:17:38.888877625 -0400
+++ adv-wb/loremaster/loremaster/principals.py	2026-09-25 21:32:26.307888594 -0400
@@ -1090,6 +1090,29 @@
     from loremaster.governed import MigrateGovernedResult
 
     preconditions = await _agent_migration_preconditions(store)
+    if not preconditions.owned_unscoped:
+        private_info = await run_query(
+            acquire=store.acquire, drop=store.drop, url=store.url, noun="private agent probe",
+            label="governed.private_probe.rejected", statement="INFO FOR DB", params={}, logger=logger,
+        )
+        if AGENT_TABLE in (private_info.get("tables", {}) if isinstance(private_info, dict) else {}):
+            private_rows = await run_query(
+                acquire=store.acquire, drop=store.drop, url=store.url, noun="private agent precondition",
+                label="governed.private_precondition.rejected",
+                statement=(
+                    f"SELECT id, owner_principal FROM {AGENT_TABLE} "
+                    "WHERE scope IS NONE AND owner_principal IS NOT NONE"
+                ),
+                params={}, logger=logger,
+            )
+            if private_rows:
+                preconditions = AgentMigrationPreconditions(
+                    unscoped_count=preconditions.unscoped_count,
+                    owned_unscoped=sorted(
+                        ((row["id"], row["owner_principal"]) for row in private_rows),
+                        key=lambda pair: str(pair[0]),
+                    ),
+                )
     if preconditions.owned_unscoped:
         operator = await resolve_operator_principal(principal_store)
         return MigrateGovernedResult(
@@ -1350,9 +1373,11 @@
         )
     if foreign:
         named = [sanitise_line(owner) for owner in foreign[:_REFUSAL_ID_SAMPLE_SIZE]]
+        if len(foreign) > _REFUSAL_ID_SAMPLE_SIZE:
+            named = named[:1]
         parts.append(
             f"{offending_count - operator_rows} are owned by {len(foreign)} other principal(s) "
-            f"(first {len(named)} named: {', '.join(named)})."
+            f"(named: {', '.join(named)})."
         )
     parts.append(
         f"First {len(shown)} of {offending_count} ids shown: {', '.join(shown)}. Adjudicate these rows "
@@ -1493,6 +1518,8 @@
 
     # §2.6 agent-first: refuse while ANY agent is still NONE-owner (count>0, never only count==1).
     unmigrated_agents = (await _agent_migration_preconditions(store)).unscoped_count
+    if not await _owner_count(store, AGENT_TABLE, none=True):
+        unmigrated_agents = 0
     if unmigrated_agents > 0:
         return MigrateGovernedResult(
             table=MESSAGE_TABLE,
--- ref-prod/agents.py	2026-09-25 21:17:38.888877625 -0400
+++ adv-wb/loremaster/loremaster/agents.py	2026-09-25 21:32:40.806264453 -0400
@@ -699,7 +699,8 @@
         for field_name, value in (("name", name), ("session", session)):
             if not is_legal_identifier(value):
                 raise InvalidAgentIdentityError(
-                    f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern}; nothing was "
+                    f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern}; that is lowercase "
+                    f"letters, digits, '_' or '-', starting with a letter or digit; nothing was "
                     f"written — register again with a legal {field_name}. The rejected value "
                     f"was:\n{render_fenced(value)}"
                 )
--- ref-prod/server.py	2026-09-25 21:17:39.048881774 -0400
+++ adv-wb/loremaster/loremaster/server.py	2026-09-25 21:33:21.324314896 -0400
@@ -6573,8 +6573,9 @@
                 str(
                     render_compose(
                         render_line(
-                            "{label} must match {pattern} — names must stay in "
-                            "the safe charset. The rejected value was:",
+                            "{label} must match {pattern} — lowercase letters, digits, '_' or '-', "
+                            "starting with a letter or digit; names must stay in the safe charset. "
+                            "The rejected value was:",
                             label=sanitise_line(label),
                             pattern=sanitise_line(AGENT_NAME_PATTERN.pattern),
                         ),
@@ -6718,13 +6719,7 @@
         # keep the SF-63-1 gate below checks.
         session_keep_bare: str | None = None
         from loremaster.agents import InvalidAgentIdentityError  # noqa: PLC0415
-        from lorerunes import is_blank  # noqa: PLC0415 - house lazy-import idiom
 
-        if is_blank(role):
-            raise InvalidAgentIdentityError(
-                "agent role must not be blank; nothing was written — register again with a "
-                "role (e.g. 'builder')"
-            )
         if principal is not None:
             principal_bare = str(principal.id).split(":", 1)[-1]
             keep_store = self._keep_store
@@ -6735,6 +6730,7 @@
             # SF-63-1 — get-or-create the session keep, kept by THIS registrant's principal (the
             # first registrant with a principal keeps it; the keeper's own later agents join it — the
             # idempotent CAS on the UNIQUE keep.key, store-ref §1.8).
+            pre_existing_keep = await keep_store.get_by_key(f"session:{session}")
             session_keep = await keep_store.get_or_create_keyed(
                 key=f"session:{session}", type="session", keeper_email=principal.email, name=session
             )
@@ -6753,17 +6749,22 @@
                     "into this session"
                 )
             kept_by_me = session_keep.keeper_id == principal_bare
-        result = await self.agent_registry.register(
-            agent,
-            session=session,
-            role=role,
-            model=model,
-            spawned_by=spawned_by,
-            task_id=task_id,
-            cadence=cadence,
-            owner_principal_id=principal_bare,
-            session_keep_id=session_keep_bare,
-        )
+        try:
+            result = await self.agent_registry.register(
+                agent,
+                session=session,
+                role=role,
+                model=model,
+                spawned_by=spawned_by,
+                task_id=task_id,
+                cadence=cadence,
+                owner_principal_id=principal_bare,
+                session_keep_id=session_keep_bare,
+            )
+        except InvalidAgentIdentityError:
+            if session_keep is not None and pre_existing_keep is None and self._keep_store is not None:
+                await self._keep_store.delete_keep(keep_id=str(session_keep.id))
+            raise
         now = datetime.now(UTC)
         registered_age_s = int((now - result.agent.registered_at).total_seconds())
         brief: Brief | None
```

## VERDICT
**INSUFFICIENT.** The a19 contract is SATISFIABLE: an independent reference goes `11529 passed, 0 failed` (the author's
exact count). It kills everything its own mutations named, and its hostile CA-1 fixture caught a real bug in my
first reference. But five wrong builds pass the FULL suite:
- **MP-1 / MP-2 · ROUTING IS NOT SHARING.** Both sharing proofs are one-directional, so a private copy beside THE
  shared function survives. That is D-1's own mutation rider, half-built. Kill: K1/K2, the reverse redirect.
- **MP-3 · ORDER.** D-2 says "before the mint". The pins observe only "no keep remains", so mint-then-undo passes.
  Kill: K3, a `get_or_create_keyed` call spy.
- **MP-4 · SERVED PROSE.** The re-keyed order guard can serve a scope count under the `NONE-owner` noun. My own
  reference did, and passed everything. Kill: PD2 as a pin.
- **MP-5 · PROSE (low).** The F-9 gloss can return in a later clause. Kill: a skeleton golden.
Class breakdown: MISSING PIN ×5 · SAT DEFECT ×0 · READING-DEPENDENT ×1 (WB7b → amendment 20 R1; §8.4 → R2) ·
LIVE-PRODUCTION-DEFECT ×1, **#485**: a credentialed register refused AFTER the mint (role conflict) keeps the
session keep and DENIES a third party, at `84af63f` and after a correct D-2 fix.
Forks for the sidecar before the a19a addendum: F-1 (CD-2 vs `∀[brief]`), F-2 (the ownerless-scoped sender),
F-3 (zeroed refusal receipts).
