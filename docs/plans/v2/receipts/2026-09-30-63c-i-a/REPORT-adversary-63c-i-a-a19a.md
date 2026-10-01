brief-base v16 read · brief project v7 read

# REPORT-adversary-63c-i-a-a19a — narrow contract-adversary pass on the a19a addendum (`16d2d82`)

## SUMMARY BLOCK
- **state:** done. **Verdict: CONTRACT INSUFFICIENT** — 7 MISSING PINS (MP-A…MP-G, §3), 3 NEW DOORS needing rulings (#1, #2, #4b — §5), 1 fork-dependent pin (MP-F ⇐ FK-a). **SAT CONFIRMED** on an independent build; **all 5 a19 survivors + PQ1/#485 KILLED**.
- **P1 headline:** 12 wrong builds survive the 7 contract files AND the FULL suite (two lint/type-clean composites, each `11592 passed, 62 skipped, 3 xfailed, 0 failed`, §4.1): N3b N5 N6 N7 N11 N12 N13 N14 N17 L3 D1a D1b (+ N8, D2 on unruled doors; N16 equivalent-today). Every one is killed by a named probe that is GREEN on my reference (§A.3).
- **Class breakdown:** REACH (MP-A: the ∀-refusal-classes pin fails OPEN on the package's own factory-raise idiom, and counts CLASSES not SITES — a new post-mint refusal arrives unpinned) · RACE (MP-B: "created" never tested against a concurrent winner) · SERVED PROSE (MP-C: race refusal text) · ONE-IMPLEMENTATION (MP-D: reverse direction on blank role only) · BOUND (MP-E: new id samples never perturbed) · F-3 (MP-F, reading A) · DUAL (MP-G: a failed keep mint degrades to an ownerless register).
- **deviations:** (1) N17's first message used `{cadence!r}` and was killed by `test_link5_render_containment` — my wording, not the defect; re-worded through `render_attributed`, composite A re-run green (§4.1). (2) KP13/KP14 were added mid-matrix; REF re-run with all 28 probes = `1500 passed`. (3) The author's 23 mutation proofs were corroborated by my own independent kills of the same defects, not re-run one-by-one.
- **Packages considered:** none — no mechanism specified (my reference/probes reuse `sanitise_line`, `render_attributed`, `run_query`, `KeepStore.delete_keep`, the a19/a19a helpers; scratch-only).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none — no new symbol enters the repo (reference, wrong builds and probes are scratch-only, pasted in §A).
- **Graded:** `16d2d82` · HEAD-at-report: `3c7d1f0` · DIFFERENT (1 ahead: `3c7d1f0` is docs-only; `git diff --stat 16d2d82 HEAD -- loremaster lorerunes loresigil lorescribe scripts` is EMPTY, so every pin graded is byte-identical at both).
- **Author claims re-derived:** 63 pins ✔ · RED@`84af63f` 80 failed (52 + 28) ✔ · SAT `11592/62/3/0` ✔ (independent build) · P1c-a ✔ (my N3a/N3c red BY NAME).
- **decisions-needed:** FK-a (F-3 scope; I pick A) · FK-b/FK-c (picked, §7) · doors #1 (both half-pairs: name both?), #2 (message half-pair: refuse?), #4b (failed compensation: tell the consumer?) — §5 with recommendations.
- **receipt pointers:** §1 prior survivors · §2/§2.1 reference + SAT · §2.2 quantifier table · §3 missing pins · §4/§4.1 wrong builds + full-suite · §5 doors · §6 DUAL · §7 forks · §8 P1c · §9 residuals · §A instruments verbatim.

#486 did not appear in any of my 3 full-suite runs (SAT, composite A run 2, composite B); composite A run 1's single red was my own wording (deviation 1), not an unrelated failure.

## §0 Capability check
- Idle-gate contract file written: `/tmp/claude-idle-gate-lore/4d6979a0-821d-4faf-a3a4-d8a8b36d541b-adversary-63c-i-a-a19a.contract`
  = `{"artifact": "REPORT-adversary-63c-i-a-a19a.md"}` (session id taken from my scratchpad path; not denied this time).
- lore reachable: `lore_comms register` OK (session `63c-20260924`, role `adversary`, cadence `≤20m`); `lore_get_symbol`
  used for `AgentRegistry.register`. grep/rg are hook-blocked (#473): every textual sweep below uses `awk` (said so).
- Store reference `docs/reference/surrealdb-31-capabilities.md` read first (§1.4, §2 `SELECT *` / record links, §4
  dangling edges, §7). Production `84af63f` == HEAD `3c7d1f0` for every production tree
  (`git diff --stat 84af63f HEAD -- loremaster/loremaster lorerunes loresigil lorescribe scripts` → empty).
- Order discipline: my reference (§2) was built and run BEFORE I opened the author's §A reference or §5 DUAL.
  I read the author's report §10 door list only via my brief's summary of it.

## §2 My independent reference build (built BEFORE reading the author's §A)
- Tree: `./scripts/scratch_copy.sh <scratch>/adv-ref` (provenance asserted by the tool); printed
  `loremaster.__file__ = …/scratchpad/adv-ref/loremaster/loremaster/__init__.py`. Patcher verbatim: §A.1.
- Design (mine): validity FIRST (`_MIGRATE_VALID_TABLES` = the four; `_unsupported` serves `None` receipts, zero I/O) →
  `_agent_migration_preconditions(store, *, table=None)` returns `unscoped_count`, `owned_unscoped[(id, owner)]`,
  `ownerless_scoped[id]` and — for `table == "message"` only — `dangling_senders[(message id, sender)]`
  (`SELECT id, sender FROM message WHERE scope IS NONE AND sender.id IS NONE`) → `_verb_level_refusal` names EVERY
  problem present in one refusal (R2: operator remedy first, owners unclassified; F-2 half-applied part) → legs. The
  message leg reads the order guard and the dangling refusal from the SAME preconditions object; CD-1 WHERE; counts via
  `_scope_count`; `backfilled` = rows the UPDATE returned. F-3: EVERY refusal serves `scanned=None`,
  `already_migrated=None` (reading A, §7). Registry: `AgentRegistry.preflight(...)` holds the pair (only once a keep
  id is passed), identity, and the existing-row refusals; `register` calls it first and keeps no copy. Handler:
  `preflight` → mint → `register`; on `AgentRegistryError` after the mint, deletes the keep IFF
  `keeps.minted_by_this_call(keep)` (set by `get_or_create_keyed` only on its own winning CREATE — derived from the
  mint's return, never a pre-read).
- Gates on the reference (2026-09-26): `ruff check .` → `All checks passed!`; `./scripts/typecheck.sh` → every leg OK.
- Contract files on the reference (2026-09-26, `-n 8`): `test_fixwave_a19a_63c_i_a.py` (63 collected),
  `test_fixwave_a19_63c_i_a.py`, `test_agent_governance_63c_i_a.py`, `test_agent_registry.py`,
  `test_message_migrate_63b_ii_a.py`, `test_message_enforcement_63b_ii_a.py`, `test_comms_tool.py` →
  **`1472 passed in 92.54s`, EXIT=0**. md5 of the reference production: principals `ca984c50…`, agents `173dca1e…`,
  server `1fd3bfc8…`, keeps `31b2574b…`, governed `1a186212…`.

## §6 DUAL — my independent enumeration (written 2026-09-26 BEFORE opening the author's §5; diffed in §6.2)
### §6.1 Deletions / re-keys in the contract delta (`git diff 77d9146 16d2d82 -- loremaster`), each with the virtue it carried
| # | site (symbol) | old | new | old virtue | kept? |
|---|---|---|---|---|---|
| T1 | `test_fixwave_a19_63c_i_a.py::TestTheMessageOrderGuardIsScopeKeyed63cIAa19::test_CONTROL_…` (D-1 control) | ownerless-SCOPED agent + a governed sender ⇒ message leg proceeds, 1 backfilled | FULLY migrated store, 2 owners (operator + foreign), 2 backfilled | (a) guard silent once migrated; (b) owner-keyed vs scope-keyed discrimination in the "proceed" direction; (c) — | (a) kept, strengthened (no owner monoculture); (b) DROPPED deliberately — the population is now F-2-forbidden (am-22 §3 erratum; am-23 FK-4); stated in the docstring. Correct: a fixture on a forbidden state discriminates nothing. |
| T2 | `test_agent_governance_63c_i_a.py::…::_assert_the_derived_diagnosis` above-bound leg | `1 <= named <= bound` | `named == min(bound, n)` | never more than the bound, never none | kept (strictly stronger); R1 lands |
| T3 | `test_message_enforcement_63b_ii_a.py::_MIGRATE_MESSAGE_GOLDEN` | `… WHERE owner_principal IS NONE` | `… WHERE scope IS NONE AND owner_principal IS NONE` | one UPDATE, the same three SET columns, NONE-owner rows only | kept; the semantic NARROWING (a scoped-but-ownerless message is no longer stamped) is CD-1's deliberate change. The golden was never compared to what EXECUTED before a19a (the author's measured claim — see §6.2) |
| T4 | `_comms_fakes.py::FakeAgentRegistry.register` | inline retired / role / spawned_by refusals | extracted to `_refuse_an_existing_row_conflict`, shared with the new `preflight` | the fake refuses what the writer refuses, in the same order | kept (same order, same text). Pre-existing divergence NOT introduced here: the fake renders `{existing.role!r}` where the real writer renders `render_attributed(...)` fenced — the mirror pin compares outcome CLASS only, so this stays unpinned (§8 P5) |
| T5 | `test_comms_tool.py::_RecordingAgentRegistry.RECORDED_METHODS` | 7 methods | + `preflight` | the recorder covers the fake's whole public surface (`test_the_recorder_covers_the_whole_registry_surface` derives it) | kept (additive; the derivation would have reddened without it) |
| T6 | a19 file header comment on `_MIGRATE_TABLES` | — | comment only | — | n/a |

### §6.1b Production behaviours the a19a rulings REMOVE or REPLACE (the inventory a builder's diff must honour)
| # | old behaviour @`84af63f` | fate under a19a | pinned by |
|---|---|---|---|
| P1 | `register`: pair → identity → select → retired → role → spawned_by, all before any write | moves into `preflight`; the pair check DEFERRED on the handler's pre-mint call | `test_an_inconsistent_provenance_pair_is_refused_before_any_store_io` (pair still before store I/O on `register`); mirror pin `owner-before-the-mint` / `mixed-pair-once-minted` |
| P2 | handler: mint → foreign gate → register (mint BEFORE every registry refusal — #485) | preflight → mint → gate → register → created-only compensation | ∀-refusal fixtures (zero-mint spy), handler-order pin, race pin |
| P3 | tokenless register mints NO keep | unchanged | 63b-ii-a pins (my reference passes them) |
| P4 | message order guard owner-keyed, noun "NONE-owner agent(s)" | scope-keyed through THE shared function; noun must follow (MP-4 dissolved by F-2) | K2, a19 CA-A |
| P5 | message counts/WHERE owner-keyed | scope-keyed counts; `scope IS NONE AND owner_principal IS NONE` WHERE | CD-1 pins. ⚠ the counts and the WHERE now DISAGREE on an owned-but-unscoped message (door #2, §5) |
| P6 | agent leg's row-level refusal served MEASURED `scanned`/`already` (it counted before refusing) | the check moves to the verb, which measures nothing of the target → `None` | F-3 pin |
| P7 | the message leg's order / operator refusals and the legs' operator refusals serve `scanned=0` | spec-ambiguous (am-22 §4 "on a refusal" vs its pin "a verb-level refusal") | NOT pinned — door #3, §5 |
| P8 | `_owner_count` used by the order guard | retired from the guard; still used by nothing on the migrate path in my reference (a builder may leave it dead — lint does not flag an unused private function) | — (residual, §9) |

## §8 P1c REACH — per instrument (legs: EMPIRICAL where a wrong build is named; otherwise construction-inspection)
### §8.1 The derived ∀-refusal-classes pin (`test_every_derived_refusal_class_has_a_driven_fixture` over `_ClosureWalk`)
| axis | verdict | receipt |
|---|---|---|
| 1. set it covers | every `AgentRegistryError`-family raise in `register`'s call closure, pre-write, less the A3 pair | `_register_raise_sites` |
| 2. derived or hand-list | DERIVED from `agents.py`'s AST, BUT with three hidden constants in the walker: (a) a raise is recorded only for the shape `raise <Name>(...)`; (b) a callee is followed only as `self.X` / `cls.X` / `AgentRegistry.X` / an `agents.py` module-level function; (c) the family is the classes DEFINED in `agents.py` (this one is RULED — am-23 FK-1) | construction; (a) EMPIRICAL — WB N3b (§4) |
| 3. coverage a checked variable | YES both ways vs `_REFUSAL_FIXTURES` (missing reds by class name; stale reds) — EMPIRICAL N3a/N3c (direct shape) redden by name. ⚠ but NOT fail-closed: a raise the walker cannot CLASSIFY is dropped silently. The docstring states the bound for `raise <variable>` only; the factory shape `raise self._x_refusal(...)` — this package's own idiom (`read_file.py::_unknown_tier_error`, `readonly_guard.py::_refusal`, `store_read.py::_not_found_error`) — is unstated and invisible | N3b survives (§4) |
| 4. effect vs proxy | EFFECT — the driven pin observes the zero-mint spy, the keep tables and the third party; the CONTROL proves the spy sees a mint | contract; my REF runs |
| 5. one source by mutation | PARTIAL — the reverse ("admitting") direction is exercised for ONE class (blank role) on both `register` and the handler; a private copy of any EXISTING-ROW decision (retired / conflict) beside `preflight` survives | N13, N14 (§4) |
### §8.2 The ∀-tables WHERE rider (`test_EVERY_governed_legs_backfill_WHERE_is_scope_keyed` over `_migrate_legs`)
| axis | verdict | receipt |
|---|---|---|
| 1. set | the governed backfill legs | `_migrate_legs` |
| 2. derived | DERIVED from `principals.py`'s AST, keyed on `governed_exempt(<string CONSTANT> "migrate-governed", …)`. Hidden: a leg outside `principals.py`, or one naming the exemption through a module constant, is not derived. The production truth that ALREADY enumerates these legs is the F5 tree-write allowlist (the exempt entries carry the name + origin function) — deriving from it would remove both hidden constants | construction-inspection |
| 3. coverage checked | YES: derived − observed ≠ ∅ reds by host; every OBSERVED host is checked whether derived or not | contract |
| 4. effect vs proxy | reads the exempt TOKEN's statement, not the executed one; equality token == executed is asserted live only for the message leg (`test_the_message_backfill_EXECUTES_the_golden`). See W1 (§4) for whether a token/executed divergence on another leg is caught | EMPIRICAL — W1 |
| 5. one source | n/a (a text property, not a shared policy) | — |
### §8.3 Other instruments the a19a pins rely on
| instrument | verdict |
|---|---|
| `_invalid_table_names` (emitted schema − the four + a typo) | DERIVED from the emitted DDL corpus; non-vacuity asserted; GOOD |
| `_count_connection_acquires` + `store_handle` counter | EFFECT with a positive CONTROL (the valid table's read is seen on the handle AND the principal store); GOOD |
| `_spy_the_mint` | EFFECT with a CONTROL (valid register = 1 mint); ⚠ injects only AFTER the real mint, so a concurrent winner BEFORE this call's mint is never constructed — WB N5 (§4) |
| `_redirect_the_shared_preconditions` (ghost sharing, both directions) | EFFECT, twin baselines, call counter; GOOD |
| `_stated_integers` | membership of the TRUE count; admits extra integers (by design, am-13/14) |
| `_REFUSAL_ID_SAMPLE_SIZE` bound on the NEW lists (dangling, half-applied) | READ but never PERTURBED — the am-20 §8.2 rider's own class ("a bound that is read but never perturbed hides a restated twin") | EMPIRICAL — N11, N12 (§4) |
| fake-preflight mirror | outcome CLASS only (refused / clear); class and text of the refusal unpinned — F3 (§4) |

## §5 The author's candidate doors (§10 of `REPORT-contract-63c-i-a-a19a.md`), constructed and classified
Spec probes SP2/SP4/SP11 and kill probes KP7/KP8 are verbatim in §A.3; every run below is on MY reference
(`adv-wb` tree carrying `ref-prod/` bytes, provenance printed per run, 2026-09-26).

### Door #2 — owned-but-unscoped MESSAGE rows → **NEW DOOR (needs a ruling)** + a MISSING PIN on the count (§3 MP-D2 if D2 survives)
- **PROBED (SP2), not reasoned.** Population: two migrated senders; `m_legacy` (legacy) and `m_owned_unscoped`
  (`owner_principal = principal:<operator>`, `scope` NONE — a message-table half-pair). My reference, verbatim:
  `first = MigrateGovernedResult(table='message', scanned=2, backfilled=1, already_migrated=0, refused=False)` ·
  `second = MigrateGovernedResult(table='message', scanned=2, backfilled=0, already_migrated=1, refused=False)` ·
  rows after: `m_legacy` stamped, `m_owned_unscoped` `scope: None` · `report_unmigrated_governed_rows(message) = 1`.
  So: the row is **never stamped**, **invisible to every governed read forever**, the forgotten-backfill alarm reads
  **1 forever with no path to zero**, and the receipt's `scanned` (2) ≠ `backfilled + already` (1) on both runs —
  and the migrate reports `refused=False`, i.e. a clean cutover.
- A build that serves `backfilled = <the scope-keyed unmigrated count>` (the pre-CD-1 idiom, and the author's
  reasoned expectation) serves **`backfilled=2` then `backfilled=1` while stamping 1 then 0** — a false served count
  (wrong build D2, §4).
- Reachability: NOT through a writer — `_comms_send` stamps `scope` through `governed.resolve_write_scope(…,
  default=session_keep_scope)`, never NONE; the only other `MessageLedger.send` consumer is the governed send
  (`lore_impact`, 2026-09-26). So a raw seed or a half-applied prior run — exactly the provenance am-22 §3 gives the
  AGENT half-pair. Expected EMPTY in production (like E3).
- **Recommended behaviour (for the ruling):** apply F-2's own logic to the message table — the message leg's
  precondition (the shared function's message leg, beside FK-2's dangling check) REFUSES on owned-but-unscoped
  messages with count + bounded ids, "half-applied", byte-inert. Independently of that ruling, `backfilled` must be
  the rows the UPDATE stamped (a MEASURED count, am-22 §4's principle), never the pre-count.

### Door #3 — leg-level refusals serving `scanned=0` → **FORK (two readings) → MISSING PIN under reading A**
- am-22 §4 body: *"Ruling: on a refusal those fields are `None`"* (unqualified); its pin sentence: *"a verb-level
  refusal's receipt serves no target-table count it did not measure."* Reading A: every refusal (the ORDER refusal,
  the NEW dangling-sender refusal, the legs' operator-ambiguity refusals — none of them scanned the target either).
  Reading B: verb-level only. They produce different code. **I pick A** (CONSUMER LAW is stated as the reason, and it
  binds `scanned=0` on the order refusal exactly as it binds it on the verb's). Wrong build L3 (§4) serves `0` on the
  message leg's order + dangling + operator refusals.

### Door #1 — both half-pairs in one store: which diagnosis → **NEW DOOR (needs a ruling)**; recommend BOTH
- Pinned today: refused, byte-inert (`test_BOTH_half_pairs_together_are_refused_byte_inert`). Unpinned: the text. My
  reference names both (`… carry an owner but no scope (§2.1) … owned by 2 other principal(s) …` AND `3 agent row(s)
  carry a scope but no owner — a half-applied store …`). Wrong builds D1a (serves only the half-applied part) and D1b
  (only the owned-but-unscoped part) — §4. am-20 §8.4's own rationale (*"a refusal that names one of two problems buys
  the operator two round trips"*) rules the R2 combination; it does not rule this one. Recommended: ONE refusal
  naming both, each with its own count and bounded ids; order irrelevant (neither remedy blocks the other's diagnosis).

### Door #4 — compensation masking / failure → **two parts**
- (a) the race refusal REPLACED by the compensation's own text (wrong build N7) → **MISSING PIN (within am-22 §1)**:
  §1 already requires "the served refusal is the registry's own teaching" for every preflight-refusable class; the
  race path serves the same registry refusal one step later and nothing pins it (KP4 is the pin).
- (b) the compensation's `delete_keep` itself FAILS (SP4, delete patched to raise `KeepStoreError`): my reference
  serves the registry's teaching verbatim — `AgentIdentityConflictError: agent 'raced-agent' is already registered
  with role ```scout``` …` — and **the keep is LEFT BEHIND** (`keep_left=['session:wave-comp-fail']`), reported only
  as a server-log WARNING. The ruled BOUND names "a keep left behind" with the re-open trigger *"a failed
  compensation observed"* — but nothing the CONSUMER sees makes it observable, and that keep will DENY the next
  principal (SF-63-1), the very third-party harm #485 is about. Wrong build N8 (the delete error propagates and
  replaces the teaching) is the other plausible shape. → **NEW DOOR (needs a ruling).** Recommended: serve the
  registry's teaching AND one appended line naming the left-behind keep + its remedy (`lore-adm delete-keep …`),
  so the named re-open trigger is observable by the one reader who can act.

### The brief's "different record TABLE" ghost → **NOT A DEFECT (unconstructible), with receipt**
- SP11: seeding a legacy message whose `sender` links `principal:<id>` is REJECTED by the engine:
  `InternalError: Couldn't coerce value for field 'sender' of 'message:m_other_table': Expected 'record<agent>' but
  found 'principal:…'`; POSITIVE CONTROL in the same probe: a same-table ghost (`agent:ghost_control`) seeds fine.
  `message.sender` has been `record<agent>` since the table was created (`df59f76`, packet 03 STORE, adds
  `("sender", f"record<{AGENT_TABLE}>", "")`; the only other commit touching that spec line, `69abba0`, is the
  03b hot-path index change — `git log -S'("sender",'`), so no dirty store can hold a cross-table sender
  (store-ref §1.4 would otherwise leave one). Detection that misses it misses an empty population.

## §4 Wrong builds — each = my reference + ONE defect, over the 7 contract files + my probe file (runner §A.4)
Provenance on every run: `PROVENANCE …/scratchpad/adv-wb/loremaster/loremaster/__init__.py` (first line of each log).
Declared BEFORE any run (runner header): every build fails ≥1 contract test unless it is a survivor. Collected:
1498 (REF, 1472 contract + 26 probes), 1499/1500 once KP13/KP14 were added mid-matrix (REF re-run: **1500 passed**).
"contract" = failures outside my probe file. A survivor is a survivor only after the full-suite leg (§4.1).
| build | defect | contract fails (killing pins) | my probe fails | verdict |
|---|---|---|---|---|
| REF | — | 0 | 0 | control (every KP satisfiable) |
| WB1 | verb ORs a private owned-but-unscoped query | 4 (K1 ×4) | — | KILLED (prior survivor) |
| WB2 | order guard ANDs `_owner_count(agent)` | 1 (K2) | — | KILLED (prior survivor) |
| WB3 | handler drops `preflight`: mint, then created-only undo | 7 (∀-refusal ×6 zero-mint spy + handler-order) | — | KILLED (prior survivor) |
| WB4 | F-9 gloss in a later clause | 2 (registry skeleton golden ×2) | — | KILLED (prior survivor) |
| WB7b | above the bound names ONE principal | 2 (R-Q5-1 above-cap / perturbed-bound, R1) | — | KILLED (prior survivor) |
| N1 | `register` calls a private clone of `preflight` | 2 (register-both-directions, handler-order) | KP5 ×6, KP6 ×6 | KILLED |
| N2 | `preflight` omits spawned_by; `register` re-derives it | 2 (∀-refusal `[spawned-by-conflict]`, mirror `[spawned-by-conflict]`) | KP5, KP6 | KILLED — by the DRIVEN fixture, NOT by the derived-classes pin (the class is still raised pre-write elsewhere, so the derived set is unchanged; nothing names it "by class") |
| N3a | new `SessionClosedError` raised directly in `preflight`, no fixture | 1 — derived pin: *"register can now raise ['SessionClosedError'] BEFORE its first write, and no comms(register) fixture drives it"* | — | KILLED, BY NAME |
| N3c | same class, direct shape, in `register` AFTER `preflight` (post-mint) | 1 (derived pin, by name) | KP12 | KILLED, BY NAME |
| **N3b** | same class, same position as N3c, raised through the package's FACTORY idiom `raise self._session_closed_refusal(session)` | **0** | KP12 | **SURVIVES the contract** → MP-A |
| N4 | compensation deletes found keeps too | 1 (race `[found-pre-existing]`) | KP1 | KILLED |
| **N5** | "created" derived by a PRE-READ `get_by_key` before the mint (TOCTOU) | **0** | KP1 | **SURVIVES** → MP-B |
| **N6** | the mint's `KeepStoreError` swallowed; register proceeds OWNERLESS | **0** | KP14 | **SURVIVES** → MP-G |
| **N7** | compensation re-raises its OWN refusal text instead of the registry's | **0** | KP4 | **SURVIVES** → MP-C |
| N8 | a failed compensation's error propagates (replaces the teaching) | 0 | 0 (SP4 records it) | unruled — door #4(b), §5 |
| **N13** | `register` calls `preflight` AND keeps a private retired check | **0** | KP5 `[retired]`, KP6 `[retired]` | **SURVIVES** → MP-D |
| **N14** | handler calls `preflight` AND keeps a private retired check (`get_agent`) | **0** | KP6 `[retired]` | **SURVIVES** → MP-D |
| **N17** | a NEW raise SITE of an already-covered class (`AgentIdentityConflictError` on a cadence change) in `register` after `preflight` | **0** | KP13 | **SURVIVES** → MP-A (site-vs-class) |
| N10 | the SOUND rows stamped in a separate statement before the ghost refusal | 4 (dangling byte-identity ×3 + invariant) | — | KILLED |
| **N11** | ghost refusal's sample = private literal `10` | **0** | KP2 | **SURVIVES** → MP-E |
| **N12** | half-applied id list UNBOUNDED | **0** | KP3 | **SURVIVES** → MP-E |
| N15 | ghost check at the VERB | 6 (MESSAGE-only ×2, …) | KP2 | KILLED |
| N16 | dangling detection keyed on `sender.owner_principal IS NONE` | 0 | 0 | equivalent on every reachable population (§9) — NOT A DEFECT today |
| **L3** | message leg's order / dangling / operator refusals serve `scanned=0` | **0** | KP7a, KP7b, KP7c `[message]` | **SURVIVES** → MP-F (reading A, door #3) |
| **D1a** | both half-pairs: only the half-applied part served | **0** | KP8 | survives — door #1 (NEW DOOR) |
| **D1b** | both half-pairs: only the owned-but-unscoped part served | **0** | KP8 | survives — door #1 (NEW DOOR) |
| D2 | message `backfilled` = the scope-keyed pre-count | 0 | 0 | differs ONLY on door #2's population — rides that ruling (§5) |
| C1a | message WHERE owner-keyed | 3 | — | KILLED |
| C1b | message counts owner-keyed | 1 | — | KILLED |
| C2a | validity checked AFTER the shared read | 1 (zero-I/O) | — | KILLED |
| C2b | valid = the three supported (brief "not supported") | 7 (a19 ∀[brief] + a19a [brief]) | — | KILLED |
| R1 | principal bound a private literal | 1 (R-Q5-1 `[perturbed-bound]`) | — | KILLED |
| R2a | operator remedy AFTER the count | 4 | — | KILLED |
| R2b | owners classified "other principal(s)" when the operator is unresolved | 4 | — | KILLED |
| F3a | verb-level refusal serves `0` | 12 | — | KILLED |
| F1 | FAKE `preflight` admits everything (P5) | 6 (mirror) | — | KILLED |
| F2 | FAKE `preflight` checks the pair before the mint (P5) | 75 (every tokened fake register) | — | KILLED |
| F3 | FAKE `preflight` raises the WRONG class for a role conflict (P5) | 1 — `test_comms_tool.py::TestRegisterAction::test_role_conflict_on_reregister_propagates` (incidental; the mirror pin compares outcome CLASS only and stays green) | — | KILLED incidentally — §9 residual |
| W1 | agent leg EXECUTES a statement other than its exempt token's golden | 1 — `test_agent_governance_63c_i_a.py::…::test_the_migrate_exempt_token_carries_the_EXECUTED_three_column_statement` | — | KILLED (the ∀-WHERE rider reads the token; token == executed is pinned per leg elsewhere) |

## §3 MISSING PINS (wrong build · why every a19a pin passes it · the kill pin, verbatim in §A.3 · class)
Each kill pin is GREEN on my reference (REF: `1500 passed`, §4) and RED on its build — the pair is the evidence.
Full-suite survival of every build below: §4.1.

- **MP-A · the ∀-refusal-classes pin fails OPEN on a raise it cannot classify (N3b), and keys coverage by CLASS not SITE
  (N17) — REACH (P1c), BLOCKER-class.** The pin's own docstring promises *"a new refusal added tomorrow cannot arrive
  unpinned"* and `_REFUSAL_FIXTURES`' comment promises *"every raise SITE of a class gets its own"* variant. Two honest
  shapes defeat both: (N3b) a new `AgentRegistryError` subclass raised through the FACTORY idiom this package already
  uses (`raise self._session_closed_refusal(session)` — cf. `read_file.py::_unknown_tier_error`,
  `readonly_guard.py::_refusal`, `store_read.py::_not_found_error`): `_ClosureWalk.record` only sees
  `raise <Name>(...)`, so the class is never recorded and the derived pin stays GREEN while N3c — the SAME class at the
  SAME position in the direct shape — reddens BY NAME. (N17) a new raise SITE of an already-covered class
  (`AgentIdentityConflictError` on a re-register cadence change, in `register` after `preflight`): the derived set is
  unchanged, no fixture is demanded, and the refusal fires AFTER the mint — #485's exact shape — with only the created-
  only compensation hiding it. **Kill:** (1) fail CLOSED — every `raise` in the closure whose exception is not a
  direct family constructor is either resolved (follow the callee's `return <Family>(...)`) or on an evidence-backed
  allowlist, else the pin reds naming `file:line`; (2) coverage per SITE (the derived site list, each mapped to a
  fixture variant) — or, stronger and cheaper, the RUNTIME form: KP13's property (*∀ refused `comms(register)` ⇒ zero
  mints*) asserted by a spy armed around EVERY `comms(action="register")` the suite drives, with the covered-call
  count a checked variable. KP12 (N3b) and KP13 (N17) are the effect probes.
- **MP-B · "created" is never tested against a concurrent WINNER (N5) — ORDER/RACE, within am-22 §1.2** (*"the builder
  derives that from its return"*). A handler that derives "created" from a pre-read `get_by_key(...) is None` passes the
  race pin both ways: `_spy_the_mint` injects only AFTER the real mint, so no test lets another register win the mint
  between this call's pre-read and its mint. In that window the pre-read build deletes the WINNER's keep — the one
  another agent of the same principal just registered into. **Kill: KP1** (the spy mints the winner, then lets this
  call find it, then injects the conflicting register; the session keep must survive).
- **MP-C · the race path's served refusal is unpinned (N7) — SERVED PROSE / TRUST, within am-22 §1** (the ∀-fixture
  pin already requires "the served refusal is the registry's own teaching"; the race serves the same registry refusal
  one step later). N7 replaces it with the compensation's own text and passes (the race pin asserts only
  `pytest.raises(AgentRegistryError)`). **Kill: KP4.**
- **MP-D · ROUTING IS NOT SHARING for every class but blank role (N13, N14) — ONE-IMPLEMENTATION.** Both reverse
  ("admitting preflight") legs drive ONE class (a blank role). A `register` — or a handler — that calls `preflight`
  AND keeps a private copy of an EXISTING-ROW decision (retired here) passes all 63 pins. The a19 adversary's MP-1/MP-2
  lesson, one level down. **Kill: KP5 / KP6** — the reverse direction ∀ `_REFUSAL_CASES` (the SAME derived fixture set),
  with an admitting `preflight` that still returns the existing row so a re-register UPDATEs.
- **MP-E · the NEW refusal lists read `_REFUSAL_ID_SAMPLE_SIZE` but never PERTURB it (N11, N12) — am-20 §8.2's rider
  class** (*"a bound that is read but never perturbed hides a restated twin … one constant, one perturbation"*). The
  dangling-sender refusal (`[above-cap]` reads the constant at 10 — a private literal `10` passes) and the half-applied
  refusal (3 rows, below any bound — an UNBOUNDED list passes) each carry the id-sample policy with no perturbation leg.
  **Kill: KP2** (constant patched to 3, 5 ghosts ⇒ exactly 3 named) and **KP3** (patched to 3, 5 half-pairs ⇒ exactly 3
  named, the true 5 stated).
- **MP-F · F-3 on the LEG-level refusals (L3) — reading A of am-22 §4 (fork, §7).** The message leg's ORDER, DANGLING
  (new in this addendum) and operator refusals can serve `scanned=0, already_migrated=0` and pass. **Kill: KP7a/b/c**
  (KP7c ∀ agent/memory/message).
- **MP-G · a FAILED session-keep mint degrades to an ownerless register (N6) — DUAL / orphaned virtue of the handler
  rewrite.** At `84af63f` the mint's `KeepStoreError` propagates (no agent row). A handler rewritten around `preflight`
  + compensation (try/except is now the idiom in exactly this block) that swallows the mint error and registers
  OWNERLESS passes every a19a pin and my other probes. Old virtue, no pin: *a credentialed register never silently
  loses its owner*. **Kill: KP14** (mint patched to raise ⇒ the error surfaces and no agent row exists).

## §2.1 SAT — the contract is satisfiable by an INDEPENDENT build (the author's claim re-derived)
- **Required-green enumeration, written BEFORE judging pins** (what a correct a19a build must keep green): (1) every
  single-principal store proceeds on every governed table exactly as before — legacy agent/memory/message backfills,
  governed rows byte-identical, idempotent re-runs (63a/63b-ii-a/63c-i-a pins); (2) memory-only stores (no `agent`
  table) still migrate memory (the `INFO FOR DB` gate); (3) the existing 63c-i-a contract incl. a19 as amended, both
  helper shapes, the exempt-token/F5 legs; (4) amendments 13/14 count rules (R-Q5-1 integer truth, `perturbed-bound`);
  (5) tokenless register mints no keep; SF-63-1 foreign denial before any agent row; the comms fakes' whole surface.
  My reference was DESIGNED against that list and every item's pins are inside the full suite below.
- Tree `adv-ref` (provenance printed: `…/scratchpad/adv-ref/loremaster/loremaster/__init__.py`), production = my
  patcher (§A.1) over `84af63f` bytes, tests = `16d2d82` bytes. Lint-clean BEFORE the run (`ruff check .` → `All checks
  passed!`; `./scripts/typecheck.sh` → every leg OK), so the post-cleanup run IS this run (no cleanup edit followed).
- **Full suite, ALONE, `-n 12` (2026-09-26 00:57→01:06 local, avail 63 G at start, spike-surreal `active`, no other
  pytest on the process table, 15 G PID watchdog never fired):**
  ```
  11592 passed, 62 skipped, 3 xfailed, 9 warnings in 524.55s (0:08:44)
  EXIT=0
  ```
  **0 failed — identical to the author's `11592 / 62 / 3 / 0` (§7 of theirs), on an independently designed build.**
  #486 did not appear in this run. (Instrument: `run_suite.sh`, §A.4.)
- **Author claims re-derived:** 63 new pins (collected: 63 ✔) · RED at `84af63f` **80 failed** = 52 in the a19a file +
  20 a19 + 7 governance + 1 registry = a19's 28 (my run over the 7 contract files: `80 failed, 1392 passed`, 0
  collection errors; sampled reasons are on-defect — `preflight does not exist`, `_agent_migration_preconditions does not
  exist`, `the message leg PROCEEDED`, `scanned=0`) ✔ · SAT ✔ · the 23 mutation proofs: not re-run one-by-one;
  corroborated by my own independent kills of the same defects (WB1=M01, WB2=M02, WB3=M03, N4=M06, F3a=M09,
  C2b=M12, C2a=M13, WB4=M14, WB7b=M16, C1a=M17, C1b=M19, R2a/R2b≈M21/M22, F1≈M23), all KILLED on my reference ✔ · P1c:
  my N3a/N3c reproduce the author's P1c-a (red BY NAME, verbatim text in §4) ✔; my N3b/N17 are the two shapes their
  five probes did not try (§3 MP-A).

## §1 The prior survivors (adversary-a19 `69bf002` §3/§9) — each now KILLED, with receipts (§4 rows)
| prior survivor | a19a pin that kills it | receipt on my reference + that one defect |
|---|---|---|
| WB1 verb-level private copy | `TestSharingMovesInBothDirections::test_K1_…[agent\|memory\|message\|brief]` | 4 contract fails, K1 ×4 |
| WB2 order-guard private AND | `…::test_K2_the_order_guard_refuses_when_the_shared_function_says_unmigrated` | 1 contract fail |
| WB3 mint-then-undo | `test_a_refused_credentialed_register_…` ×6 (zero-mint spy) + `test_the_handler_decides_with_preflight_BEFORE_the_mint` | 7 contract fails |
| WB4 gloss in a later clause | `test_the_registry_refusal_skeleton_is_the_golden[name\|session]` | 2 contract fails |
| WB7b one principal above the bound | R-Q5-1 `[above-cap]`, `[perturbed-bound]` via R1's exact `min` | 2 contract fails |
| PQ1 / #485 (a registry refusal other than blank role, after the mint) | the ∀-refusal fixtures `[role-conflict\|spawned-by-conflict\|retired]` | RED at pristine `84af63f` for exactly those + blank ×3 (§2.1); GREEN on my reference |
**All five a19 survivors and PQ1 are KILLED.**

## §2.2 P1b QUANTIFIER TABLE — per invariant: ∀-over-inputs vs guarded, with receipts
| invariant | form in the contract | door attempted | result |
|---|---|---|---|
| a refused credentialed register mints no keep | GUARDED by the derived CLASS set × hand-built fixtures | a new raise SITE of a covered class (N17); a factory-shape new class (N3b) | **2 survivors** → MP-A (property form KP13 / runtime spy recommended) |
| the served refusal is the registry's own teaching | ∀ preflight fixtures only | the race path (N7) | **survivor** → MP-C |
| compensation deletes only a keep this call created | 2 fixtures (created / alice's pre-existing) | a concurrent winner between pre-read and mint (N5) | **survivor** → MP-B |
| no private copy beside `preflight` | reverse direction on ONE class | retired copies in register (N13) / handler (N14) | **2 survivors** → MP-D |
| ∀ stamped messages carry an owner | ∀ 5 populations incl. ghost, with exact stamped counts | sound rows stamped separately (N10); verb-level ghost check (N15) | killed (4; 6) |
| the ghost/half-applied id sample is THE bound | the constant READ at its value only | private literal (N11); unbounded (N12) | **2 survivors** → MP-E |
| refusal receipts serve only measured counts | verb-level refusals only | leg-level refusals (L3) | **survivor** → MP-F (reading A) |
| a failed mint never degrades a credentialed register | not stated anywhere | swallow + ownerless (N6) | **survivor** → MP-G |
| byte-inert refusals | ∀ tables × each refusal (snapshot of 7 tables) | stamping before refusing (N10) | killed |
| validity before any I/O | ∀ schema-derived invalid names + typo | validity after the read (C2a) | killed |
| the message WHERE / counts are scope-keyed | golden + live executed-statement leg + byte-identity | owner-keyed WHERE (C1a) / counts (C1b); token ≠ executed on the agent leg (W1) | killed (3; 1; 1) |
| one refusal names every problem present | R2's combination only | the half-pair combination (D1a/D1b) | survives — NEW DOOR #1 (unruled) |

### §6.2 Diff against the author's §5 (read AFTER §6.1 was written)
- Same six test-tree rows on both sides (T1 control re-key, T2 R1, T3 golden, T4 fake refactor, T5 recorder, T6 comment);
  the virtue kept/dropped verdicts agree row for row. The author's *"No pin was deleted or inverted"* — CONFIRMED by the
  diff (every change is a re-key, an addition, or a comment).
- **Mine, not theirs:** (1) T4 — the fake's conflict text `{existing.role!r}` has always differed from the writer's
  `render_attributed(...)` fence; the new mirror pin compares outcome CLASS only, so a fake raising the WRONG class
  (F3) is caught only incidentally by an older comms test, and a wrong TEXT not at all (§9). (2) The production
  inventory P5/P7/P8 (§6.1b): the scope-keyed count vs the self-guarding WHERE disagreement (door #2), the leg-level
  receipts (door #3), and `_owner_count`'s likely orphaning — the author carries (1)/(2) as §10 doors, not in the DUAL.
- **Theirs, not mine:** none.

## §7 Forks (a sentence with two readings that produce different code — brief-base §2)
- **FK-a · am-22 §4 F-3 scope.** Body: *"on a refusal those fields are `None`"*; pin sentence: *"a verb-level refusal's
  receipt …"*. Reading A — every refusal (order, dangling, the legs' operator refusals); Reading B — verb-level only.
  Different code (L3 is correct under B, wrong under A). **I pick A** (the stated reason, CONSUMER LAW, binds a `0` on
  the order refusal exactly as on the verb's); MP-F is conditional on it.
- **FK-b · am-22 §1.2 "created".** *"`get_or_create_keyed` reports created-vs-found; the builder derives that from its
  return"*. Reading A — from the mint's OWN outcome (its winning CREATE); Reading B — any way of learning whether the
  key existed (e.g. a pre-read). Only A is race-correct (N5 / KP1). **I pick A** (the text says "from its return");
  MP-B pins it.
- **FK-c · am-23 FK-1 "raised in the AST call closure".** Reading A — every raise of a family class the closure can
  reach, whatever its syntactic shape; Reading B — the `raise <Name>(...)` shape the author's walker sees. The ruling
  names no shape; the pin implements B. **A is the ruling's evident intent** (the reach must be what `register` can
  RAISE) — MP-A.

## §9 Residuals — every one with an individual verdict
| # | residual | verdict |
|---|---|---|
| R-1 | N16 (dangling keyed on the sender's OWNER) survives everything: after the verb (half-pairs refused) and the order guard (no NONE-scope agent), a NONE `sender.owner_principal` can only be a ghost, so the two predicates select the same rows today | NOT A DEFECT today; re-open trigger = am-20 §8.1's E3 narrowing (a half-pair reaching the message leg would then be mis-diagnosed "dangling"). The contract's FK-4 note already names that trigger for PD2 |
| R-2 | the fake-preflight mirror compares outcome CLASS only; a fake raising the wrong class (F3) is caught only incidentally (`test_comms_tool.py::TestRegisterAction::test_role_conflict_on_reregister_propagates`), a wrong TEXT not at all (the fake's `{role!r}` vs the writer's `render_attributed` fence predates a19a) | LOW — P5 note; a class+text leg on the mirror would close it |
| R-3 | `_owner_count` has no caller on the migrate path in my reference after CD-1 + the shared guard; lint does not flag an unused private function | LOW — builder hygiene; `lore_dead_code` after the build |
| R-4 | the ∀-WHERE rider reads the exempt TOKEN; token == executed is pinned per leg elsewhere (W1 killed by `test_the_migrate_exempt_token_carries_the_EXECUTED_three_column_statement`; message by a19a's live leg) | GOOD, by composition — a new leg must bring its own token==executed leg (the author's door #7 is the ∀ form) |
| R-5 | `_migrate_legs` derives from `principals.py` + a string-constant exemption name; the F5 tree-write allowlist is the production truth that already enumerates exempt origins | LOW — REACH; derive from the allowlist when the brief leg lands (ii) |
| R-6 | the author's door #5 (R2 renders stored ids with no hostile fixture of its own) | agree — same seam as CA-1 in both references; a hostile id in R2's population is one line; LOW |
| R-7 | the author's doors #6/#7/#9 (re-collection hazard, dead allowlist goldens, `mutation_proof.py` needs ≥1 expect-red) | agree, all process/tooling; not graded further |
| R-8 | the author's door #8 (`record::exists(sender) = false` vs my `sender.id IS NONE`) | both detect every seeded ghost on 3.2.4 (the author's M-runs; my REF runs); neither is in the store reference — a probe row there would make it citable (agree) |
| R-9 | the author's reference adds a `report_created` kwarg to `KeepStore.get_or_create_keyed`; `_comms_fakes.FakeKeepStore.get_or_create_keyed` does not accept it | NOT A DEFECT (their SAT is green: no tokened path reaches the fake keep store with that kwarg) but a builder trap worth one line in the builder brief: the K3 spy is signature-agnostic, the FAKE is not |
| R-10 | **P-PKG diff** — my own survey before theirs: the contract specifies (a) an AST raise-closure walk (stdlib `ast`; no package derives a function's reachable raise set — the author's HAND-ROLLED verdict with its lore query is right), (b) a dangling-link predicate (engine SurrealQL, not a library), (c) a created-vs-found signal (the existing `KeepStore` CAS — REUSED/EXTENDED in both references). Author: "none — no mechanism specified for production". | AGREE; no `bespoke` verdict to attack |
| R-11 | **P-PORT** | n/a — no Odoo seam (0 seams · 0 non-stable · 0 rulings, mine and theirs) |

## §4.1 Full-suite leg — the survivors survive the WHOLE suite (ALONE, `-n 12`, 15 G PID watchdog never fired, no other pytest, spike-surreal active; lint/type-clean composites)
| composite | builds | md5 (principals · agents · server) | full suite (2026-09-26) | kill probes on the same bytes |
|---|---|---|---|---|
| A (run 1) | N3b N5 N7 N13 N14 N17 D1b | — | `1 failed, 11591 passed` — `test_link5_render_containment.py::…::test_every_served_domain_error_contains_its_caller_params`: *"agents.py:860 — served domain error interpolates caller param 'cadence' OUTSIDE the containment seam"* = MY N17 wording (`{cadence!r}`), not the defect | — |
| **A (run 2)** | same; N17 re-worded through `render_attributed` (as an honest builder writes it) | `f4cee67d…` · `d9693856…` · `25155a38…` | **`11592 passed, 62 skipped, 3 xfailed, 9 warnings in 528.58s` · EXIT=0** | 7 red: KP1 (N5), KP4 (N7), KP5/KP6 `[retired]` (N13/N14), KP12 (N3b), KP13 (N17), KP8 (D1b) |
| **B** | N6 N8 N11 N12 N16 L3 D1a D2 | `8a937b27…` · `173dca1e…` · `fc772c88…` | **`11592 passed, 62 skipped, 3 xfailed, 9 warnings in 525.82s` · EXIT=0** | 7 red: KP2 (N11), KP3 (N12), KP7a/b/c (L3), KP8 (D1a), KP14 (N6) |
**12 wrong builds (+ N8/D2 on unruled doors, N16 equivalent) pass every one of the 11592 tests.** Logs:
`compA_run2.log`, `compB_run1.log`, `sat_run1.log` in my scratch (instrument `run_suite.sh`, §A.4, re-creates them).

## §A Instruments (verbatim — the scratch trees are disposable by design; every measured claim above re-runs from these)

### §A.1 Reference patcher `adv_ref_patch_a19a.py` (then `ruff check --fix` sorted one lazy import; two lines re-wrapped by hand: `minted_keep_id = cast(...)` split in `agents.py`, `minted_by_this_call`'s docstring shortened in `keeps.py`)
```python
"""adversary-63c-i-a-a19a — INDEPENDENT reference fix build for the a19 + a19a rulings (amendments 19-23).

Applied to a scratch_copy.sh tree whose production bytes are 84af63f (== HEAD 3c7d1f0 production; verified
empty `git diff --stat 84af63f HEAD -- loremaster/loremaster lorerunes loresigil lorescribe scripts`).
Built BEFORE reading the contract author's §A reference. Each replacement asserts it landed exactly once
(#194). Usage: python adv_ref_patch_a19a.py <scratch-root>
"""

import pathlib
import sys

ROOT = pathlib.Path(sys.argv[1])


def patch(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{rel}: expected exactly one match, found {count}: {old[:90]!r}"
    path.write_text(text.replace(old, new))


def replace_between(rel: str, start: str, end: str, new: str) -> None:
    """Replace [start, end) — both markers must occur exactly once, start before end."""
    path = ROOT / rel
    text = path.read_text()
    assert text.count(start) == 1, f"{rel}: start marker count {text.count(start)}: {start[:80]!r}"
    assert text.count(end) == 1, f"{rel}: end marker count {text.count(end)}: {end[:80]!r}"
    head, _, rest = text.partition(start)
    _, _, tail = rest.partition(end)
    path.write_text(head + new + end + tail)


P = "loremaster/loremaster/principals.py"
G = "loremaster/loremaster/governed.py"
A = "loremaster/loremaster/agents.py"
K = "loremaster/loremaster/keeps.py"
SV = "loremaster/loremaster/server.py"

# ---------------------------------------------------------------- F-3: receipts may be "not measured"
patch(G, "    table: str\n    scanned: int\n    backfilled: int\n    already_migrated: int\n",
      "    table: str\n    scanned: int | None\n    backfilled: int\n    already_migrated: int | None\n")

patch(P, "from loremaster.sanitise import safe_str\n", "from loremaster.sanitise import safe_str, sanitise_line\n")

# ---------------------------------------------------------------- the verb: validity FIRST, then THE shared check
replace_between(
    P,
    "    from loremaster.governed import MigrateGovernedResult\n\n    if table == MEMORY_TABLE:\n",
    "async def resolve_operator_principal(",
    '''    from loremaster.governed import MigrateGovernedResult

    # CD-2 / F-1 / FK-3: argument validity FIRST — zero store I/O for a name outside the governed set.
    if table not in _MIGRATE_VALID_TABLES:
        return _unsupported(table)
    preconditions = await _agent_migration_preconditions(store, table=table)
    refusal = await _verb_level_refusal(preconditions, principal_store)
    if refusal is not None:
        return MigrateGovernedResult(
            table=table, scanned=None, backfilled=0, already_migrated=None, refused=True, reason=refusal
        )
    if table == MEMORY_TABLE:
        return await _migrate_memory_scope(store, keep_store, principal_store)
    if table == AGENT_TABLE:
        return await _migrate_agent_owner(store, keep_store, principal_store)
    if table == MESSAGE_TABLE:
        return await _migrate_message_owner(store, keep_store, principal_store, preconditions)
    return _unsupported(table)


#: The ruled valid set (amendment 23 FK-3): the governed tables D-1 names. ``brief`` is valid (it meets the
#: §2.1 store fact) but its leg lands at 63c-ii.
_MIGRATE_VALID_TABLES = ("agent", "memory", "message", "brief")


def _unsupported(table: str) -> MigrateGovernedResult:
    from loremaster.governed import MigrateGovernedResult

    return MigrateGovernedResult(
        table=table,
        scanned=None,
        backfilled=0,
        already_migrated=None,
        refused=True,
        reason=(
            f"migrate-governed does not support table {sanitise_line(table)!r} at packet 63c-i — only "
            "`memory`, `agent` and `message` (brief lands 63c-ii, task/finding land 64); nothing was "
            "read or written"
        ),
    )


''',
)

# ---------------------------------------------------------------- the shared function + derived diagnoses
patch(
    P,
    "_REFUSAL_ID_SAMPLE_SIZE = 10\n",
    '''_REFUSAL_ID_SAMPLE_SIZE = 10


class AgentMigrationPreconditions(BaseModel):
    """THE agent-migration store state (amendment 19 D-1 / 22 F-2 / 23 FK-2), read by the verb and the
    message leg's order + dangling-sender guards."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    unscoped_count: int
    owned_unscoped: list[tuple[Any, Any]]
    ownerless_scoped: list[Any]
    dangling_senders: list[tuple[Any, Any]]


async def _agent_migration_preconditions(
    store: StoreHandle, *, table: str | None = None
) -> AgentMigrationPreconditions:
    """The ONE shared predicate set. ``table == 'message'`` adds the message leg's dangling-sender read."""
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
    unscoped_count = 0
    owned: list[tuple[Any, Any]] = []
    ownerless_scoped: list[Any] = []
    if AGENT_TABLE in tables:
        unscoped_count = await _scope_count(store, AGENT_TABLE, none=True)
        rows = await run_query(
            acquire=store.acquire,
            drop=store.drop,
            url=store.url,
            noun="governed agent row precondition",
            label="governed.agent_precondition.rejected",
            statement=(
                f"SELECT id, owner_principal, scope FROM {AGENT_TABLE} "
                "WHERE (scope IS NONE AND owner_principal IS NOT NONE) "
                "OR (scope IS NOT NONE AND owner_principal IS NONE)"
            ),
            params={},
            logger=logger,
        )
        for row in rows or []:
            if not isinstance(row, dict):
                continue
            if row.get("scope") is None:
                owned.append((row.get("id"), row.get("owner_principal")))
            else:
                ownerless_scoped.append(row.get("id"))
    dangling: list[tuple[Any, Any]] = []
    if table == MESSAGE_TABLE and MESSAGE_TABLE in tables:
        ghost_rows = await run_query(
            acquire=store.acquire,
            drop=store.drop,
            url=store.url,
            noun="governed message dangling-sender precondition",
            label="governed.message_dangling.rejected",
            statement=f"SELECT id, sender FROM {MESSAGE_TABLE} WHERE scope IS NONE AND sender.id IS NONE",
            params={},
            logger=logger,
        )
        dangling = [
            (row.get("id"), row.get("sender")) for row in (ghost_rows or []) if isinstance(row, dict)
        ]
    return AgentMigrationPreconditions(
        unscoped_count=unscoped_count,
        owned_unscoped=sorted(owned, key=lambda pair: str(pair[0])),
        ownerless_scoped=sorted(ownerless_scoped, key=str),
        dangling_senders=sorted(dangling, key=lambda pair: str(pair[0])),
    )


def _bare_id(value: Any) -> str:
    if hasattr(value, "id"):  # a RecordID: its id is already bare (and may itself contain ':')
        return str(value.id)
    text = str(value)
    return text.partition(":")[2] or text


def _shown(values: list[Any]) -> tuple[int, str]:
    shown = [sanitise_line(str(value)) for value in values[:_REFUSAL_ID_SAMPLE_SIZE]]
    return len(shown), ", ".join(shown)


def _half_applied_part(ownerless_scoped: list[Any]) -> str:
    count = len(ownerless_scoped)
    shown_count, shown = _shown(ownerless_scoped)
    return (
        f"{count} agent row(s) carry a scope but no owner — a half-applied store (one column of the "
        f"governed pair was stamped without the other). First {shown_count} of {count} ids shown: {shown}."
    )


def _owned_unscoped_part(offending: list[tuple[Any, Any]], operator: Any) -> str:
    offending_count = len(offending)
    shown_count, shown = _shown([row_id for row_id, _owner in offending])
    operator_bare = _bare_id(operator.id)
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
    parts.append(f"First {shown_count} of {offending_count} ids shown: {shown}.")
    return " ".join(parts)


def _owned_unscoped_unclassified_part(offending: list[tuple[Any, Any]]) -> str:
    offending_count = len(offending)
    shown_count, shown = _shown([row_id for row_id, _owner in offending])
    return (
        f"ALSO: {offending_count} agent row(s) carry an owner but no scope (§2.1); their owners are "
        "UNCLASSIFIED — with the operator unresolved, any of them may BE the operator. "
        f"First {shown_count} of {offending_count} ids shown: {shown}."
    )


async def _operator_remedy(principal_store: PrincipalStore) -> str:
    principals = await principal_store.list()
    admins = [principal for principal in principals if principal.role == _ROLE_ADMIN]
    return (
        f"cannot resolve THE operator principal ({len(principals)} principals, {len(admins)} admins) — "
        "provision a single operator principal (or a single admin) FIRST."
    )


async def _verb_level_refusal(
    preconditions: AgentMigrationPreconditions, principal_store: PrincipalStore
) -> str | None:
    """The verb-level store refusal: BOTH half-pairs (F-2), and R2's unresolvable operator — one refusal
    naming every problem present, operator remedy first."""
    parts: list[str] = []
    if preconditions.owned_unscoped:
        operator = await resolve_operator_principal(principal_store)
        if operator is None:
            parts.append(await _operator_remedy(principal_store))
            parts.append(_owned_unscoped_unclassified_part(preconditions.owned_unscoped))
        else:
            parts.append(_owned_unscoped_part(preconditions.owned_unscoped, operator))
    if preconditions.ownerless_scoped:
        parts.append(_half_applied_part(preconditions.ownerless_scoped))
    if not parts:
        return None
    parts.append(
        "Adjudicate these rows by hand before migrating ANY governed table; no row was stamped"
    )
    return " ".join(parts)
''',
)

# ---------------------------------------------------------------- F-3 on the legs' own refusals (reading A)
path = ROOT / P
text = path.read_text()
old = """            table=MEMORY_TABLE,
            scanned=0,
            backfilled=0,
            already_migrated=0,
            refused=True,"""
assert text.count(old) == 1
text = text.replace(old, """            table=MEMORY_TABLE,
            scanned=None,
            backfilled=0,
            already_migrated=None,
            refused=True,""")
old = """            table=AGENT_TABLE,
            scanned=0,
            backfilled=0,
            already_migrated=0,
            refused=True,"""
assert text.count(old) == 1
text = text.replace(old, """            table=AGENT_TABLE,
            scanned=None,
            backfilled=0,
            already_migrated=None,
            refused=True,""")
path.write_text(text)

# ---------------------------------------------------------------- agent leg: row precondition moved to the verb; F-3 WHERE
replace_between(
    P,
    "    # §2.1 ROW precondition (#470 / F10), BEFORE any write",
    "    project_keep = await keep_store.get_or_create_keyed(\n        key=PROJECT_KEEP_KEY, type=\"project\", keeper_email=operator.email, name=\"lore\"\n    )\n    project_scope = keep_scope(project_keep.id.partition(\":\")[2] or project_keep.id)\n    operator_id",
    "    # §2.1's row precondition is a STORE fact, checked ONCE at the verb (amendment 19 D-1).\n",
)
patch(P, 'owner_agent = id, scope = $scope WHERE scope IS NONE"',
      'owner_agent = id, scope = $scope WHERE scope IS NONE AND owner_principal IS NONE"')

# ---------------------------------------------------------------- message leg: shared order guard, dangling, CD-1
replace_between(
    P,
    "async def _migrate_message_owner(\n",
    "def build_parser() -> argparse.ArgumentParser:",
    '''async def _migrate_message_owner(
    store: StoreHandle,
    keep_store: KeepStore,
    principal_store: PrincipalStore,
    preconditions: AgentMigrationPreconditions | None = None,
) -> MigrateGovernedResult:
    """Backfill every legacy (NONE-scope, NONE-owner) ``message`` row from its SENDER + the project keep.

    ORDER (§2.6) and DANGLING-SENDER (FK-2) are read from THE shared preconditions; both refusals are
    byte-inert and measured nothing of the target table (F-3: ``None`` receipts)."""
    from lorerunes.pdp import keep_scope

    from loremaster.governed import PROJECT_KEEP_KEY, MigrateGovernedResult, governed_exempt

    if preconditions is None:
        preconditions = await _agent_migration_preconditions(store, table=MESSAGE_TABLE)
    if preconditions.unscoped_count > 0:
        return MigrateGovernedResult(
            table=MESSAGE_TABLE,
            scanned=None,
            backfilled=0,
            already_migrated=None,
            refused=True,
            reason=(
                f"cannot migrate `message` rows before the `agent` table is migrated "
                f"({preconditions.unscoped_count} un-migrated (NONE-scope) agent(s) remain) — a message's "
                "owner_principal is read from sender.owner_principal (§2.6 agent-first ORDER); run "
                "migrate-governed for `agent` first"
            ),
        )
    if preconditions.dangling_senders:
        dangling = preconditions.dangling_senders
        shown = [
            f"{sanitise_line(str(message_id))} (sender {sanitise_line(str(sender))})"
            for message_id, sender in dangling[:_REFUSAL_ID_SAMPLE_SIZE]
        ]
        return MigrateGovernedResult(
            table=MESSAGE_TABLE,
            scanned=None,
            backfilled=0,
            already_migrated=None,
            refused=True,
            reason=(
                f"{len(dangling)} legacy message(s) name a dangling sender — their `sender` link resolves "
                "to no agent row, so no owner can be derived from it. "
                f"First {len(shown)} of {len(dangling)} shown: {', '.join(shown)}. Adjudicate these "
                "messages by hand before migrating `message`; no row was stamped"
            ),
        )

    operator = await resolve_operator_principal(principal_store)
    if operator is None:
        return MigrateGovernedResult(
            table=MESSAGE_TABLE,
            scanned=None,
            backfilled=0,
            already_migrated=None,
            refused=True,
            reason=(
                f"{await _operator_remedy(principal_store)} It keeps the project keep; then migrate "
                "`message`"
            ),
        )

    project_keep = await keep_store.get_or_create_keyed(
        key=PROJECT_KEEP_KEY, type="project", keeper_email=operator.email, name="lore"
    )
    project_scope = keep_scope(project_keep.id.partition(":")[2] or project_keep.id)

    unmigrated = await _scope_count(store, MESSAGE_TABLE, none=True)
    already = await _scope_count(store, MESSAGE_TABLE, none=False)
    if unmigrated == 0:
        return MigrateGovernedResult(
            table=MESSAGE_TABLE,
            scanned=unmigrated + already,
            backfilled=0,
            already_migrated=already,
            refused=False,
        )
    backfill_statement = (
        f"UPDATE {MESSAGE_TABLE} SET owner_agent = sender, "
        "owner_principal = sender.owner_principal, scope = $scope "
        "WHERE scope IS NONE AND owner_principal IS NONE"
    )
    with governed_exempt("migrate-governed", statement=backfill_statement):
        stamped = await run_query(
            acquire=store.acquire,
            drop=store.drop,
            url=store.url,
            noun="governed message-owner backfill",
            label="governed.message_backfill.rejected",
            statement=backfill_statement,
            params={"scope": project_scope},
            logger=logger,
        )
    return MigrateGovernedResult(
        table=MESSAGE_TABLE,
        scanned=unmigrated + already,
        backfilled=len(stamped) if isinstance(stamped, list) else unmigrated,
        already_migrated=already,
        refused=False,
    )


''',
)

# ---------------------------------------------------------------- registry: F-9 gloss dropped; preflight
patch(
    A,
    """f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern} (lowercase "
                    f"letters, digits, '_' or '-', starting with a letter or digit); nothing was "
                    f"written""",
    """f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern}; nothing was "
                    f"written""",
)
patch(
    A,
    """        self._refuse_an_inconsistent_provenance_pair(owner_principal_id, session_keep_id)
        self._refuse_an_invalid_identity(name=name, session=session, role=role)
        agent_id = self._agent_id(session, name)
        existing_row = await self._select_row(agent_id)
        now = datetime.now(UTC)

        if existing_row is None:""",
    """        existing = await self.preflight(
            name,
            session=session,
            role=role,
            spawned_by=spawned_by,
            owner_principal_id=owner_principal_id,
            session_keep_id=session_keep_id,
        )
        agent_id = self._agent_id(session, name)
        now = datetime.now(UTC)

        if existing is None:""",
)
replace_between(
    A,
    "        existing = self._row_to_agent(existing_row)\n        if existing.status == STATUS_RETIRED:\n",
    "        new_model = model if model is not None else existing.model\n",
    "",
)
patch(
    A,
    """    async def register(
        self,
        name: str,
        *,
        session: str,
        role: str,""",
    """    async def preflight(
        self,
        name: str,
        *,
        session: str,
        role: str,
        spawned_by: str | None = None,
        owner_principal_id: str | None = None,
        session_keep_id: str | None | object = _KEEP_NOT_YET_MINTED,
    ) -> Agent | None:
        \"\"\"Every refusal ``register`` can raise WITHOUT a write (amendment 22 §1 / #485), reading the
        existing row by id; returns it (or ``None``). The provenance pair is checked only once the session
        keep id is known (the register handler preflights BEFORE its keep mint).\"\"\"
        if session_keep_id is not _KEEP_NOT_YET_MINTED:
            self._refuse_an_inconsistent_provenance_pair(owner_principal_id, cast("str | None", session_keep_id))
        self._refuse_an_invalid_identity(name=name, session=session, role=role)
        existing_row = await self._select_row(self._agent_id(session, name))
        if existing_row is None:
            return None
        existing = self._row_to_agent(existing_row)
        if existing.status == STATUS_RETIRED:
            raise RetiredAgentError(
                f"agent {name!r} is retired (terminal) — respawns register a fresh name"
            )
        if existing.role != role:
            raise AgentIdentityConflictError(
                f"agent {name!r} is already registered with role {render_attributed(existing.role)} "
                f"(you sent {render_attributed(role)}) — names are never reused; register a fresh name "
                f"(e.g. {name + '2'!r})"
            )
        if (
            spawned_by is not None
            and existing.spawned_by is not None
            and existing.spawned_by != spawned_by
        ):
            raise AgentIdentityConflictError(
                f"agent {name!r} is already registered with spawned_by "
                f"{render_attributed(existing.spawned_by)} (you sent "
                f"{render_attributed(spawned_by)}) — names are never "
                f"reused; register a fresh name (e.g. {name + '2'!r})"
            )
        return existing

    async def register(
        self,
        name: str,
        *,
        session: str,
        role: str,""",
)
patch(A, "logger = logging.getLogger(__name__)\n",
      "logger = logging.getLogger(__name__)\n\n#: ``preflight``'s \"the session keep is not minted yet\" marker (the handler preflights pre-mint).\n"
      "_KEEP_NOT_YET_MINTED: object = object()\n")

# ---------------------------------------------------------------- keeps: created-vs-found from the mint's own return
patch(
    K,
    """            created = await self.get_keep(keep_id)
            if created is None:  # pragma: no cover - a just-committed row must read back
                raise KeepStoreError(f"created keyed keep {keep_id!r} did not read back")
            return created
""",
    """            created = await self.get_keep(keep_id)
            if created is None:  # pragma: no cover - a just-committed row must read back
                raise KeepStoreError(f"created keyed keep {keep_id!r} did not read back")
            # #485 compensation: THIS call's CREATE won — reported on the returned object (a non-field
            # attribute: equality / dumps are field-only, so no caller comparing keeps is affected).
            object.__setattr__(created, _MINTED_BY_THIS_CALL, True)
            return created
""",
)
patch(
    K,
    "class Keep(BaseModel):\n",
    '''_MINTED_BY_THIS_CALL = "minted_by_this_call"


def minted_by_this_call(keep: object) -> bool:
    """Whether ``keep`` was CREATED by the ``get_or_create_keyed`` call that returned it (never merely found)."""
    return getattr(keep, _MINTED_BY_THIS_CALL, False) is True


class Keep(BaseModel):
''',
)

# ---------------------------------------------------------------- server: F-9 spelling; handler preflight + compensation
patch(SV, '"{label} does not match {pattern} — names must stay in "', '"{label} must match {pattern} — names must stay in "')
patch(
    SV,
    """        session_keep_bare: str | None = None
        if principal is not None:
            principal_bare = str(principal.id).split(":", 1)[-1]
            keep_store = self._keep_store""",
    """        session_keep_bare: str | None = None
        # #485 / amendment 22 §1: every refusal the registry can raise WITHOUT a write, BEFORE the mint.
        await self.agent_registry.preflight(
            agent,
            session=session,
            role=role,
            spawned_by=spawned_by,
            owner_principal_id=str(principal.id).split(":", 1)[-1] if principal is not None else None,
        )
        minted_session_keep = False
        keep_store = self._keep_store
        if principal is not None:
            principal_bare = str(principal.id).split(":", 1)[-1]""",
)
patch(
    SV,
    """            session_keep_bare = str(session_keep.id).split(":", 1)[-1]
            visible = await resolve_visible_keeps""",
    """            from loremaster.keeps import minted_by_this_call  # noqa: PLC0415

            minted_session_keep = minted_by_this_call(session_keep)
            session_keep_bare = str(session_keep.id).split(":", 1)[-1]
            visible = await resolve_visible_keeps""",
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
        )
        now = datetime.now(UTC)
        registered_age_s""",
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
        except _AgentRegistryError:
            # The race residual (amendment 22 §1.2): a conflicting register landed between preflight and
            # register. Delete the session keep ONLY if THIS call created it. BOUND: a failed
            # compensation leaves the keep; re-open trigger: a keep observed left behind.
            if minted_session_keep and keep_store is not None and session_keep is not None:
                try:
                    await keep_store.delete_keep(keep_id=session_keep.id)
                except Exception:  # noqa: BLE001 - the refusal below is the served outcome
                    logger.warning("register compensation failed to delete keep %s", session_keep.id)
            raise
        now = datetime.now(UTC)
        registered_age_s""",
)
print("patched")
```

### §A.2 Wrong-build driver `adv_wrong_builds_a19a.py` (each build = `ref-prod/` bytes + the named defects; comma lists compose; composites A/B additionally got `# noqa: PLR0915` on `_comms_register`'s def line and, for B, three lint re-wraps + `keep_scope(session_keep_bare or "")` for mypy — none behavioural)
```python
"""adversary-63c-i-a-a19a — wrong builds against the a19a contract (16d2d82).

Each build = my reference production bytes (ref-prod/, md5s in the report) + the named defect(s). Every patch
asserts it landed exactly once (#194). Usage: python adv_wrong_builds_a19a.py <tree> <WB[,WB...]|REF>
"""

import pathlib
import shutil
import sys

REF = pathlib.Path(__file__).parent / "ref-prod"
TREE = pathlib.Path(sys.argv[1])
BUILDS = sys.argv[2].split(",")
PROD = {
    "principals": "loremaster/loremaster/principals.py",
    "agents": "loremaster/loremaster/agents.py",
    "server": "loremaster/loremaster/server.py",
    "keeps": "loremaster/loremaster/keeps.py",
    "governed": "loremaster/loremaster/governed.py",
}
FAKES = "loremaster/tests/_comms_fakes.py"

for name, rel in PROD.items():
    shutil.copyfile(REF / f"{name}.py", TREE / rel)
# the fakes file is restored from git every run (P5 builds mutate it)
shutil.copyfile(REF / "_comms_fakes.py", TREE / FAKES)


def patch(key: str, old: str, new: str) -> None:
    path = TREE / (PROD[key] if key in PROD else key)
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{key}: expected exactly one match, found {count}: {old[:90]!r}"
    path.write_text(text.replace(old, new))


H_TRY = """        try:
            result = await self.agent_registry.register("""
H_EXCEPT = """            if minted_session_keep and keep_store is not None and session_keep is not None:
                try:
                    await keep_store.delete_keep(keep_id=session_keep.id)
                except Exception:  # noqa: BLE001 - the refusal below is the served outcome
                    logger.warning("register compensation failed to delete keep %s", session_keep.id)
            raise
"""
H_PREFLIGHT = """        await self.agent_registry.preflight(
            agent,
            session=session,
            role=role,
            spawned_by=spawned_by,
            owner_principal_id=str(principal.id).split(":", 1)[-1] if principal is not None else None,
        )
"""
PF_SPAWNED = """        if (
            spawned_by is not None
            and existing.spawned_by is not None
            and existing.spawned_by != spawned_by
        ):
            raise AgentIdentityConflictError(
                f"agent {name!r} is already registered with spawned_by "
                f"{render_attributed(existing.spawned_by)} (you sent "
                f"{render_attributed(spawned_by)}) — names are never "
                f"reused; register a fresh name (e.g. {name + '2'!r})"
            )
        return existing
"""
REG_CALL = """        existing = await self.preflight(
            name,
            session=session,
            role=role,
            spawned_by=spawned_by,
            owner_principal_id=owner_principal_id,
            session_keep_id=session_keep_id,
        )
"""


def build(wb: str) -> None:  # noqa: C901, PLR0912, PLR0915 - a flat catalogue
    if wb == "REF":
        return
    # ------------------------------------------------ prior survivors (adversary-a19)
    if wb == "WB1":  # verb ORs a PRIVATE owned-but-unscoped query beside the shared answer
        patch("principals",
              "    refusal = await _verb_level_refusal(preconditions, principal_store)\n",
              "    refusal = await _verb_level_refusal(preconditions, principal_store)\n"
              "    if refusal is None:\n"
              "        try:\n"
              "            private = await run_query(acquire=store.acquire, drop=store.drop, url=store.url,\n"
              "                noun='wb1', label='wb1.rejected', statement=f'SELECT VALUE id FROM {AGENT_TABLE} '\n"
              "                'WHERE scope IS NONE AND owner_principal IS NOT NONE', params={}, logger=logger)\n"
              "        except Exception:  # noqa: BLE001\n"
              "            private = []\n"
              "        if private:\n"
              "            refusal = (f'{len(private)} agent row(s) carry an owner but no scope (§2.1). Adjudicate '\n"
              "                'these rows by hand before migrating ANY governed table; no row was stamped')\n")
    elif wb == "WB2":  # order guard ANDs the retired owner count into the shared answer
        patch("principals", "    if preconditions.unscoped_count > 0:\n",
              "    if preconditions.unscoped_count > 0 and await _owner_count(store, AGENT_TABLE, none=True) > 0:\n")
    elif wb == "WB3":  # handler: no preflight — mint first, undo (created-only) on the refusal
        patch("server", H_PREFLIGHT, "")
    elif wb == "WB4":  # F-9 gloss returns in a LATER clause
        patch("agents", 'f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern}; nothing was "',
              'f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern}; that is lowercase letters, '
              "digits, '_' or '-'; nothing was \"")
    elif wb == "WB7b":  # above the bound, names ONE foreign principal
        patch("principals", "        named = [sanitise_line(owner) for owner in foreign[:_REFUSAL_ID_SAMPLE_SIZE]]\n",
              "        cut = _REFUSAL_ID_SAMPLE_SIZE if len(foreign) <= _REFUSAL_ID_SAMPLE_SIZE else 1\n"
              "        named = [sanitise_line(owner) for owner in foreign[:cut]]\n")
    # ------------------------------------------------ #485 / preflight
    elif wb == "N1":  # register does NOT call preflight — it re-derives an identical private copy
        text = (TREE / PROD["agents"]).read_text()
        start = text.index("    async def preflight(")
        end = text.index("    async def register(")
        clone = text[start:end].replace("async def preflight(", "async def _private_preflight(", 1)
        (TREE / PROD["agents"]).write_text(text[:end] + clone + text[end:])
        patch("agents", "        existing = await self.preflight(\n            name,\n            session=session,\n            role=role,\n            spawned_by=spawned_by,\n            owner_principal_id=owner_principal_id,\n            session_keep_id=session_keep_id,\n        )\n",
              "        existing = await self._private_preflight(\n            name,\n            session=session,\n            role=role,\n            spawned_by=spawned_by,\n            owner_principal_id=owner_principal_id,\n            session_keep_id=session_keep_id,\n        )\n")
    elif wb == "N2":  # preflight omits the spawned_by conflict; register re-derives it after preflight
        patch("agents", PF_SPAWNED, "        return existing\n")
        patch("agents", REG_CALL, REG_CALL +
              "        if (existing is not None and spawned_by is not None and existing.spawned_by is not None\n"
              "                and existing.spawned_by != spawned_by):\n"
              "            raise AgentIdentityConflictError(\n"
              "                f\"agent {name!r} is already registered with spawned_by \"\n"
              "                f\"{render_attributed(existing.spawned_by)} (you sent \"\n"
              "                f\"{render_attributed(spawned_by)}) — names are never \"\n"
              "                f\"reused; register a fresh name (e.g. {name + '2'!r})\"\n"
              "            )\n")
    elif wb in ("N3a", "N3b", "N3c"):  # a NEW refusal class in register's closure, no fixture
        patch("agents", "class RetiredAgentError(", "class SessionClosedError(AgentRegistryError):\n"
              "    \"\"\"WB: a new refusal.\"\"\"\n\n\nclass RetiredAgentError(")
        refuse = ("        if session.startswith(\"closed-\"):\n"
                  + ("            raise SessionClosedError(f\"session {session!r} is closed\")\n"
                     if wb in ("N3a", "N3c") else
                     "            raise self._session_closed_refusal(session)\n"))
        if wb == "N3a":  # direct shape, inside preflight
            patch("agents", "        self._refuse_an_invalid_identity(name=name, session=session, role=role)\n        existing_row = await self._select_row(self._agent_id(session, name))\n",
                  "        self._refuse_an_invalid_identity(name=name, session=session, role=role)\n" + refuse
                  + "        existing_row = await self._select_row(self._agent_id(session, name))\n")
        else:  # in register AFTER preflight, BEFORE the write (post-mint in the handler)
            patch("agents", REG_CALL, REG_CALL + refuse)
        if wb == "N3b":  # the package's own factory idiom (read_file.py / readonly_guard.py / store_read.py)
            patch("agents", "    async def preflight(",
                  "    @staticmethod\n    def _session_closed_refusal(session: str) -> SessionClosedError:\n"
                  "        return SessionClosedError(f\"session {session!r} is closed\")\n\n    async def preflight(")
    elif wb == "N4":  # compensation deletes the keep whether CREATED or merely FOUND
        patch("server", "            if minted_session_keep and keep_store is not None and session_keep is not None:\n",
              "            if keep_store is not None and session_keep is not None:\n")
    elif wb == "N5":  # created derived by a PRE-READ (TOCTOU), not from the mint's own return
        patch("server", "            session_keep = await keep_store.get_or_create_keyed(\n",
              "            pre_existing = await keep_store.get_by_key(f\"session:{session}\")\n"
              "            session_keep = await keep_store.get_or_create_keyed(\n")
        patch("server", "            minted_session_keep = minted_by_this_call(session_keep)\n",
              "            minted_session_keep = pre_existing is None and callable(minted_by_this_call)\n")
    elif wb == "N6":  # the mint's KeepStoreError is swallowed; the register proceeds OWNERLESS
        patch("server", "            session_keep = await keep_store.get_or_create_keyed(\n"
              "                key=f\"session:{session}\", type=\"session\", keeper_email=principal.email, name=session\n"
              "            )\n",
              "            from loremaster.keeps import KeepStoreError as _WbKeepError  # noqa: PLC0415\n\n"
              "            try:\n"
              "                session_keep = await keep_store.get_or_create_keyed(\n"
              "                    key=f\"session:{session}\", type=\"session\", keeper_email=principal.email, name=session\n"
              "                )\n"
              "            except _WbKeepError:\n"
              "                session_keep = None\n")
        patch("server", "            minted_session_keep = minted_by_this_call(session_keep)\n"
              "            session_keep_bare = str(session_keep.id).split(\":\", 1)[-1]\n"
              "            visible = await resolve_visible_keeps(keep_store, member_email=principal.email)\n"
              "            if keep_scope(session_keep_bare) not in visible:\n",
              "            minted_session_keep = minted_by_this_call(session_keep)\n"
              "            session_keep_bare = str(session_keep.id).split(\":\", 1)[-1] if session_keep else None\n"
              "            if session_keep is None:\n"
              "                principal_bare = None\n"
              "            visible = await resolve_visible_keeps(keep_store, member_email=principal.email)\n"
              "            if session_keep is not None and keep_scope(session_keep_bare) not in visible:\n")
        patch("server", "            kept_by_me = session_keep.keeper_id == principal_bare\n",
              "            kept_by_me = session_keep is not None and session_keep.keeper_id == principal_bare\n")
    elif wb == "N7":  # compensation MASKS the registry's teaching with its own refusal
        patch("server", H_EXCEPT, H_EXCEPT.replace(
            "            raise\n",
            "                raise _AgentRegistryError(\"register was refused after the session keep was minted; \"\n"
            "                                          \"the keep was released — retry the register\") from None\n"
            "            raise\n"))
    elif wb == "N8":  # compensation failure PROPAGATES (masks the refusal) instead of the refusal
        patch("server", H_EXCEPT, """            if minted_session_keep and keep_store is not None and session_keep is not None:
                await keep_store.delete_keep(keep_id=session_keep.id)
            raise
""")
    elif wb == "N13":  # register calls preflight AND keeps a PRIVATE copy of the retired decision
        patch("agents", REG_CALL, REG_CALL +
              "        if existing is not None and existing.status == STATUS_RETIRED:\n"
              "            raise RetiredAgentError(f\"agent {name!r} is retired (terminal) — respawns register a fresh name\")\n")
    elif wb == "N14":  # handler calls preflight AND keeps a PRIVATE retired check
        patch("server", H_PREFLIGHT, H_PREFLIGHT +
              "        from loremaster.agents import RetiredAgentError as _WbRetired  # noqa: PLC0415\n"
              "        from loremaster.agents import UnknownAgentError as _WbUnknown  # noqa: PLC0415\n\n"
              "        try:\n"
              "            _wb_prior = await self.agent_registry.get_agent(agent, session=session)\n"
              "        except _WbUnknown:\n"
              "            _wb_prior = None\n"
              "        if _wb_prior is not None and _wb_prior.status == \"retired\":\n"
              "            raise _WbRetired(f\"agent {agent!r} is retired (terminal) — respawns register a fresh name\")\n")
    # ------------------------------------------------ FK-2 dangling sender
    elif wb == "N10":  # the SOUND rows stamped in a separate statement before the ghost refusal
        patch("principals", "    if preconditions.dangling_senders:\n        dangling = preconditions.dangling_senders\n",
              "    if preconditions.dangling_senders:\n"
              "        await run_query(acquire=store.acquire, drop=store.drop, url=store.url, noun='wb', label='wb.r',\n"
              "            statement=f'UPDATE {MESSAGE_TABLE} SET owner_agent = sender, owner_principal = '\n"
              "            'sender.owner_principal, scope = $scope WHERE scope IS NONE AND sender.id IS NOT NONE',\n"
              "            params={'scope': 'keep:wbsound'}, logger=logger)\n"
              "        dangling = preconditions.dangling_senders\n")
    elif wb == "N11":  # the ghost refusal's bound is a PRIVATE literal 10
        patch("principals", "            for message_id, sender in dangling[:_REFUSAL_ID_SAMPLE_SIZE]\n",
              "            for message_id, sender in dangling[:10]\n")
    elif wb == "N12":  # the half-applied refusal's id list is UNBOUNDED
        patch("principals", "    shown_count, shown = _shown(ownerless_scoped)\n",
              "    shown_count, shown = len(ownerless_scoped), ', '.join(sanitise_line(str(v)) for v in ownerless_scoped)\n")
    elif wb == "N15":  # the ghost check at the VERB (store-class) — refuses agent/memory too
        patch("principals", "    preconditions = await _agent_migration_preconditions(store, table=table)\n",
              "    preconditions = await _agent_migration_preconditions(store, table=MESSAGE_TABLE)\n"
              "    if preconditions.dangling_senders:\n"
              "        return MigrateGovernedResult(table=table, scanned=None, backfilled=0, already_migrated=None,\n"
              "            refused=True, reason=f'{len(preconditions.dangling_senders)} legacy message(s) name a '\n"
              "            'dangling sender; adjudicate by hand')\n")
    elif wb == "N16":  # dangling detection keyed on the sender's OWNER, not the sender's existence
        patch("principals", 'WHERE scope IS NONE AND sender.id IS NONE"',
              'WHERE scope IS NONE AND sender.owner_principal IS NONE"')
    # ------------------------------------------------ F-3 / doors
    elif wb == "L3":  # leg-level refusals (order / dangling / operator) serve an UNMEASURED 0
        text = (TREE / PROD["principals"]).read_text()
        start = text.index("async def _migrate_message_owner(")
        body = text[start:].replace("            scanned=None,\n", "            scanned=0,\n").replace(
            "            already_migrated=None,\n", "            already_migrated=0,\n")
        (TREE / PROD["principals"]).write_text(text[:start] + body)
    elif wb == "D1a":  # both half-pairs: only the half-applied diagnosis is served
        patch("principals", "    if preconditions.owned_unscoped:\n        operator = await resolve_operator_principal(principal_store)\n",
              "    if preconditions.owned_unscoped and not preconditions.ownerless_scoped:\n"
              "        operator = await resolve_operator_principal(principal_store)\n")
    elif wb == "D1b":  # both half-pairs: only the owned-but-unscoped diagnosis is served
        patch("principals", "    if preconditions.ownerless_scoped:\n        parts.append(_half_applied_part(",
              "    if preconditions.ownerless_scoped and not preconditions.owned_unscoped:\n"
              "        parts.append(_half_applied_part(")
    elif wb == "D2":  # message backfilled = the scope-keyed COUNT, not the rows stamped
        patch("principals", "        backfilled=len(stamped) if isinstance(stamped, list) else unmigrated,\n",
              "        backfilled=unmigrated,\n")
    # ------------------------------------------------ CD-1 / CD-2 / R1 / R2 / F-3 obvious builds
    elif wb == "C1a":
        patch("principals", '"WHERE scope IS NONE AND owner_principal IS NONE"\n    )\n    with governed_exempt("migrate-governed", statement=backfill_statement):\n        stamped',
              '"WHERE owner_principal IS NONE"\n    )\n    with governed_exempt("migrate-governed", statement=backfill_statement):\n        stamped')
    elif wb == "C1b":
        patch("principals", "    unmigrated = await _scope_count(store, MESSAGE_TABLE, none=True)\n    already = await _scope_count(store, MESSAGE_TABLE, none=False)\n",
              "    unmigrated = await _owner_count(store, MESSAGE_TABLE, none=True)\n    already = await _owner_count(store, MESSAGE_TABLE, none=False)\n")
    elif wb == "C2a":  # validity checked AFTER the shared store read
        patch("principals", "    if table not in _MIGRATE_VALID_TABLES:\n        return _unsupported(table)\n    preconditions = await _agent_migration_preconditions(store, table=table)\n",
              "    preconditions = await _agent_migration_preconditions(store, table=table)\n    if table not in _MIGRATE_VALID_TABLES:\n        return _unsupported(table)\n")
    elif wb == "C2b":  # valid = the SUPPORTED three (brief answered not-supported first)
        patch("principals", '_MIGRATE_VALID_TABLES = ("agent", "memory", "message", "brief")', '_MIGRATE_VALID_TABLES = ("agent", "memory", "message")')
    elif wb == "R1":  # principal naming bound a private literal
        patch("principals", "        named = [sanitise_line(owner) for owner in foreign[:_REFUSAL_ID_SAMPLE_SIZE]]\n",
              "        named = [sanitise_line(owner) for owner in foreign[:10]]\n")
    elif wb == "R2a":  # operator remedy AFTER the owned-unscoped count
        patch("principals", "            parts.append(await _operator_remedy(principal_store))\n            parts.append(_owned_unscoped_unclassified_part(preconditions.owned_unscoped))\n",
              "            parts.append(_owned_unscoped_unclassified_part(preconditions.owned_unscoped))\n            parts.append(await _operator_remedy(principal_store))\n")
    elif wb == "R2b":  # owners classified 'other principal' although the operator is unresolved
        patch("principals", '"UNCLASSIFIED — with the operator unresolved, any of them may BE the operator. "',
              '"owned by other principal(s). "')
    elif wb == "F3a":  # verb-level refusal serves an unmeasured 0
        patch("principals", "            table=table, scanned=None, backfilled=0, already_migrated=None, refused=True, reason=refusal\n",
              "            table=table, scanned=0, backfilled=0, already_migrated=0, refused=True, reason=refusal\n")
    # ------------------------------------------------ P5: the FAKE's preflight
    elif wb == "F1":  # fake preflight admits everything
        patch(FAKES, "        minted = session_keep_id is not _KEEP_NOT_YET_MINTED\n",
              "        return None\n        minted = session_keep_id is not _KEEP_NOT_YET_MINTED\n")
    elif wb == "F2":  # fake preflight checks the pair even before the mint
        patch(FAKES, "        minted = session_keep_id is not _KEEP_NOT_YET_MINTED\n", "        minted = True\n")
    elif wb == "F3":  # fake preflight raises the WRONG class for a role conflict
        patch(FAKES, "        self._refuse_an_existing_row_conflict(existing, name=name, role=role, spawned_by=spawned_by)\n        return existing.model_copy(deep=True)\n",
              "        if existing.role != role:\n            raise RetiredAgentError(f\"agent {name!r} is retired\")\n"
              "        self._refuse_an_existing_row_conflict(existing, name=name, role=role, spawned_by=spawned_by)\n        return existing.model_copy(deep=True)\n")
    elif wb == "W1":  # the agent leg EXECUTES a statement other than its exempt token's golden
        patch("principals", '            noun="governed agent backfill",\n            label="governed.agent_backfill.rejected",\n            statement=backfill_statement,\n',
              '            noun="governed agent backfill",\n            label="governed.agent_backfill.rejected",\n'
              '            statement=backfill_statement.replace(" AND owner_principal IS NONE", ""),\n')
    elif wb == "N17":  # a NEW raise SITE of an already-covered class, in register AFTER preflight (post-mint)
        patch("agents", REG_CALL, REG_CALL +
              "        if (existing is not None and cadence is not None and existing.declared_cadence is not None\n"
              "                and existing.declared_cadence != cadence):\n"
              "            raise AgentIdentityConflictError(\n"
              "                f\"agent {name!r} is already registered with cadence \"\n"
              "                f\"{render_attributed(existing.declared_cadence)} (you sent {render_attributed(cadence)}) \"\n"
              "                f\"— register a fresh name\"\n"
              "            )\n")
    else:
        raise SystemExit(f"unknown build {wb}")


for wb in BUILDS:
    build(wb)
print(f"built {BUILDS}")
```

### §A.3 Kill + spec probe file `test_adversary_a19a_probes.py` (copied into the scratch tree only; never committed)
```python
"""adversary-63c-i-a-a19a — kill probes + spec probes (scratch-only; NEVER committed to the repo).

KP* = a candidate MISSING PIN: GREEN on my reference build, RED on the wrong build it names.
SP* = a spec probe: records what a build SERVES for a door the rulings leave open (prints; asserts only the
      fixture landed).
"""

from __future__ import annotations

import re
from typing import Any

import pytest
import test_fixwave_a19a_63c_i_a as a19a  # module-qualified: its Test* classes must not be re-collected
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
from loremaster.agents import AgentRegistry, AgentRegistryError
from lorerunes.pdp import keep_scope
from surrealdb import RecordID

from loremaster import agents, principals

_DIM = a19a._DIM


# --------------------------------------------------------------------------- KP1 — created-vs-found
async def test_KP1_a_keep_won_by_a_concurrent_mint_is_never_compensated(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """A concurrent register of ANOTHER of alice's agents wins the session-keep mint between the handler's
    preflight and its own mint (so this call FINDS the keep), then the race refusal fires. The keep this call
    merely found must survive (amendment 22 §1.2: created-only, derived from the mint's RETURN)."""
    async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM) as world:
        ctx, admin_conn = world["ctx"], world["admin_conn"]
        world["holder"]["email"] = world["emails"]["alice"]
        session = "wave-winner"
        keep_store = ctx._keep_store
        real = keep_store.get_or_create_keyed
        calls = {"n": 0}

        async def spy(*args: Any, **kwargs: Any) -> Any:
            calls["n"] += 1
            if calls["n"] == 1:
                await real(*args, **kwargs)  # the concurrent winner's mint
                found = await real(*args, **kwargs)  # THIS call finds it
                await ctx.agent_registry.register("raced-agent", session=session, role="scout")
                return found
            return await real(*args, **kwargs)

        monkeypatch.setattr(keep_store, "get_or_create_keyed", spy)
        with pytest.raises(AgentRegistryError):
            await ctx.comms(action="register", agent="raced-agent", session=session, role="builder")
        assert calls["n"] == 1, calls
        keys = await run(admin_conn, f"SELECT VALUE key FROM keep WHERE key = 'session:{session}'")
        assert keys == [f"session:{session}"], (
            f"the compensation deleted a session keep this call merely FOUND (a concurrent winner's): {keys!r}"
        )


# --------------------------------------------------------------------------- KP2 / KP3 — ONE bound, perturbed
async def test_KP2_the_dangling_sender_sample_reads_THE_constant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(principals, "_REFUSAL_ID_SAMPLE_SIZE", 3)
    async with a19a._governed_world() as world:
        pairs = await a19a._seed_ghost_store(world, ghosts=5)
        reason = str((await world.migrate(MESSAGE_TABLE)).reason or "")
        by_message = sum(1 for message_id, _s in pairs if a19a._names(reason, MESSAGE_TABLE, message_id))
        by_sender = sum(1 for _m, sender_id in pairs if a19a._names(reason, AGENT_TABLE, sender_id))
        assert "dangling" in reason.lower(), reason
        assert max(by_message, by_sender) == 3 and by_message <= 3 and by_sender <= 3, (
            f"patched bound 3 over 5 ghosts: named by message {by_message}, by sender {by_sender}: {reason!r}"
        )


async def test_KP3_the_half_applied_id_sample_is_bounded_by_THE_constant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(principals, "_REFUSAL_ID_SAMPLE_SIZE", 3)
    async with a19a._governed_world() as world:
        ids = [f"half_{index:03d}" for index in range(5)]
        for index, row_id in enumerate(ids):
            await seed_agent_governed(
                world.connection, row_id=row_id, name=f"half-{index}", session="hp",
                owner_principal=None, owner_agent=None, scope=keep_scope("sessionkeephp"),
            )
        reason = str((await world.migrate(AGENT_TABLE)).reason or "")
        named = sum(1 for row_id in ids if a19a._names(reason, AGENT_TABLE, row_id))
        assert "half-applied" in reason.lower() and named == 3, f"named {named} of 5 (bound 3): {reason!r}"
        assert 5 in a19a._stated_integers(reason, identifiers=[*ids, "sessionkeephp"]), reason


# --------------------------------------------------------------------------- KP4 — the race serves the registry's teaching
async def test_KP4_the_race_refusal_is_the_registrys_own_teaching(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM) as world:
        ctx = world["ctx"]
        world["holder"]["email"] = world["emails"]["alice"]
        session = "wave-race-teach"

        async def conflicting_register() -> None:
            await ctx.agent_registry.register("raced-agent", session=session, role="scout")

        a19a._spy_the_mint(monkeypatch, ctx, after_real=conflicting_register)
        with pytest.raises(AgentRegistryError) as caught:
            await ctx.comms(action="register", agent="raced-agent", session=session, role="builder")
        with pytest.raises(AgentRegistryError) as direct:
            await ctx.agent_registry.register("raced-agent", session=session, role="builder")
        assert (type(caught.value), str(caught.value)) == (type(direct.value), str(direct.value)), (
            f"served={caught.value!r} registry={direct.value!r}"
        )


# --------------------------------------------------------------------------- KP5 / KP6 — reverse direction ∀ derived classes
async def _admitting(self: Any, name: str, *, session: str, **_kwargs: Any) -> Any:
    """Admits every refusal but still returns the existing row (so a re-register UPDATEs, never re-CREATEs)."""
    row = await self._select_row(self._agent_id(session, name))
    return self._row_to_agent(row) if row is not None else None


@pytest.mark.parametrize(("class_name", "case"), a19a._REFUSAL_CASES)
async def test_KP5_register_follows_an_admitting_preflight_for_EVERY_derived_class(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any, class_name: str, case: Any
) -> None:
    async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM) as world:
        ctx = world["ctx"]
        kwargs = await case.setup(ctx)
        monkeypatch.setattr(AgentRegistry, "preflight", _admitting)
        direct = kwargs.copy()
        try:
            await ctx.agent_registry.register(
                direct.pop("agent"), session=direct.pop("session"), role=direct.pop("role"), **direct
            )
        except AgentRegistryError as error:
            pytest.fail(f"{class_name}/{case.variant}: register refused with preflight admitting — a PRIVATE "
                        f"copy of the decision: {error}")


@pytest.mark.parametrize(("class_name", "case"), a19a._REFUSAL_CASES)
async def test_KP6_the_handler_follows_an_admitting_preflight_for_EVERY_derived_class(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any, class_name: str, case: Any
) -> None:
    async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM) as world:
        ctx = world["ctx"]
        kwargs = await case.setup(ctx)
        world["holder"]["email"] = world["emails"]["alice"]
        monkeypatch.setattr(AgentRegistry, "preflight", _admitting)
        try:
            await ctx.comms(action="register", **kwargs)
        except AgentRegistryError as error:
            pytest.fail(f"{class_name}/{case.variant}: the HANDLER refused with preflight admitting — a "
                        f"PRIVATE copy of the decision: {error}")


# --------------------------------------------------------------------------- KP7 — F-3 on the LEG-level refusals (door #3)
async def test_KP7a_the_order_refusal_serves_no_unmeasured_count() -> None:
    async with a19a._governed_world() as world:
        await seed_agent_legacy(world.connection, row_id="legacy_0", name="legacy-0", session="s1")
        await seed_message_legacy(world.connection, sender_id="legacy_0", session="s1", seq=1)
        a19a._assert_no_unmeasured_count(await world.migrate(MESSAGE_TABLE), label="order refusal")


async def test_KP7b_the_dangling_refusal_serves_no_unmeasured_count() -> None:
    async with a19a._governed_world() as world:
        await a19a._seed_ghost_store(world, ghosts=1)
        a19a._assert_no_unmeasured_count(await world.migrate(MESSAGE_TABLE), label="dangling refusal")


@pytest.mark.parametrize("table", [AGENT_TABLE, MEMORY_TABLE, MESSAGE_TABLE])
async def test_KP7c_the_operator_only_refusal_serves_no_unmeasured_count(table: str) -> None:
    async with a19a._governed_world() as world:
        await world.principal_store.create(email="second-admin@example.com", role="admin")
        if table == MESSAGE_TABLE:  # the order guard must pass, so the operator refusal is the one reached
            await a19a._seed_clean_single_principal_store(world)
        else:
            await seed_agent_legacy(world.connection, row_id="legacy_0", name="legacy-0", session="s1")
        result = await world.migrate(table)
        assert "operator" in str(result.reason or "").lower(), result
        a19a._assert_no_unmeasured_count(result, label=f"operator-only refusal ({table})")


# --------------------------------------------------------------------------- KP8 — both half-pairs: BOTH named (door #1)
async def test_KP8_both_half_pairs_are_both_named() -> None:
    async with a19a._governed_world() as world:
        foreign = await a19a._seed_foreign_principals(world)
        owned_ids = [f"owned_unscoped_{index}" for index in range(2)]
        for index, owner in enumerate(foreign):
            await seed_agent_governed(
                world.connection, row_id=owned_ids[index], name=f"owned-unscoped-{index}", session="hp",
                owner_principal=owner, owner_agent=None, scope=None,
            )
        half_ids = await a19a._seed_half_applied_store(world)
        reason = str((await world.migrate(AGENT_TABLE)).reason or "")
        stated = a19a._stated_integers(reason, identifiers=[*half_ids, *owned_ids, *foreign, "sessionkeephp"])
        assert "half-applied" in reason.lower() and 3 in stated, f"the ownerless-scoped half is not named: {reason!r}"
        assert re.search(r"carry an owner but no scope", reason) and 2 in stated, (
            f"the owned-but-unscoped half is not named: {reason!r}"
        )


# --------------------------------------------------------------------------- KP12 — a new refusal reached AFTER the mint
async def test_KP12_a_session_closed_register_mints_nothing(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    """Meaningful only on N3b/N3c (they add ``SessionClosedError``); on every other build it registers."""
    async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM) as world:
        ctx = world["ctx"]
        world["holder"]["email"] = world["emails"]["alice"]
        calls = a19a._spy_the_mint(monkeypatch, ctx)
        closed = getattr(agents, "SessionClosedError", None)
        if closed is None:
            await ctx.comms(action="register", agent="x-agent", session="closed-wave", role="builder")
            return
        with pytest.raises(closed):
            await ctx.comms(action="register", agent="x-agent", session="closed-wave", role="builder")
        assert calls["count"] == 0, "a SessionClosedError register reached the keep mint (#485 shape)"


# --------------------------------------------------------------------------- KP13 — a new raise SITE of a covered class
async def test_KP13_a_register_refused_on_a_cadence_conflict_mints_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """Property form (∀ refused registers ⇒ zero mints), driven on an input no a19a fixture uses: a re-register
    with a DIFFERENT cadence. A correct build ACCEPTS it (cadence is mutable); a build that refuses it must do
    so before the mint."""
    async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM) as world:
        ctx = world["ctx"]
        await ctx.agent_registry.register("shared-name", session="wave-cad", role="builder", cadence="≤5m")
        world["holder"]["email"] = world["emails"]["alice"]
        calls = a19a._spy_the_mint(monkeypatch, ctx)
        try:
            await ctx.comms(action="register", agent="shared-name", session="wave-cad", role="builder", cadence="≤9m")
        except AgentRegistryError:
            assert calls["count"] == 0, "a refused register reached the keep mint (#485 shape, a new raise SITE)"


# --------------------------------------------------------------------------- KP14 — a failed keep mint is LOUD
async def test_KP14_a_failed_session_keep_mint_is_never_an_ownerless_register(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    from loremaster.keeps import KeepStoreError

    async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM) as world:
        ctx, admin_conn = world["ctx"], world["admin_conn"]
        world["holder"]["email"] = world["emails"]["alice"]

        async def failing_mint(*_a: Any, **_k: Any) -> Any:
            raise KeepStoreError("injected: the session keep mint failed")

        monkeypatch.setattr(ctx._keep_store, "get_or_create_keyed", failing_mint)
        with pytest.raises(KeepStoreError):
            await ctx.comms(action="register", agent="mint-fail", session="wave-mint-fail", role="builder")
        rows = await run(admin_conn, "SELECT VALUE name FROM agent WHERE session = 'wave-mint-fail'")
        assert rows == [], f"a credentialed register whose keep mint FAILED wrote an agent row: {rows!r}"


# --------------------------------------------------------------------------- SP — spec probes (door #2, door #4, table)
async def test_SP2_an_owned_but_unscoped_MESSAGE(capsys: Any) -> None:
    async with a19a._governed_world() as world:
        await a19a._seed_migrated_senders(world)
        await seed_message_legacy(world.connection, sender_id="sender_operator", session="gs", seq=1, row_id="m_legacy")
        await seed_message_legacy(
            world.connection, sender_id="sender_operator", session="gs", seq=2, row_id="m_owned_unscoped",
            owner_principal=RecordID("principal", world.operator_bare),
        )
        first = await world.migrate(MESSAGE_TABLE)
        second = await world.migrate(MESSAGE_TABLE)
        rows = await run(world.connection, "SELECT id, owner_principal, scope FROM message ORDER BY id")
        from loremaster.governed import report_unmigrated_governed_rows

        report = await report_unmigrated_governed_rows(world.handle, MESSAGE_TABLE)
        with capsys.disabled():
            print(f"\nSP2 first={first!r}\nSP2 second={second!r}\nSP2 rows={rows!r}\nSP2 report={report!r}")
        assert any(str(row["id"]).endswith("m_owned_unscoped") for row in rows)


async def test_SP4_a_FAILED_compensation(monkeypatch: pytest.MonkeyPatch, tmp_path: Any, capsys: Any) -> None:
    from loremaster.keeps import KeepStoreError

    async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM) as world:
        ctx, admin_conn = world["ctx"], world["admin_conn"]
        world["holder"]["email"] = world["emails"]["alice"]
        session = "wave-comp-fail"

        async def conflicting_register() -> None:
            await ctx.agent_registry.register("raced-agent", session=session, role="scout")

        async def failing_delete(*_a: Any, **_k: Any) -> None:
            raise KeepStoreError("injected: the compensation's delete failed")

        a19a._spy_the_mint(monkeypatch, ctx, after_real=conflicting_register)
        monkeypatch.setattr(ctx._keep_store, "delete_keep", failing_delete)
        served: Any = None
        try:
            await ctx.comms(action="register", agent="raced-agent", session=session, role="builder")
        except Exception as error:  # noqa: BLE001 - recording what is served
            served = error
        keys = await run(admin_conn, f"SELECT VALUE key FROM keep WHERE key = 'session:{session}'")
        with capsys.disabled():
            print(f"\nSP4 served={type(served).__name__}: {served}\nSP4 keep_left={keys!r}")
        assert served is not None


async def test_SP11_a_sender_link_to_another_TABLE_cannot_be_seeded(capsys: Any) -> None:
    async with a19a._governed_world() as world:
        await seed_message_legacy(world.connection, sender_id="ghost_control", session="t", seq=1, row_id="m_ok")
        outcome = "accepted"
        try:
            await seed_message_legacy(
                world.connection, sender_id="unused", session="t", seq=2, row_id="m_other_table",
                sender=RecordID("principal", world.operator_bare),
            )
        except Exception as error:  # noqa: BLE001
            outcome = f"REJECTED: {type(error).__name__}: {str(error)[:200]}"
        rows = await run(world.connection, "SELECT VALUE id FROM message ORDER BY id")
        with capsys.disabled():
            print(f"\nSP11 control-ghost-agent-sender rows={rows!r}\nSP11 other-table sender: {outcome}")
        assert any(str(row).endswith("m_ok") for row in rows), "positive control: the same-table ghost seed landed"
```

### §A.4 Runners (`run_wb.sh` — contract files + probes per build; `run_suite.sh` — full suite ALONE `-n 12` + 15 GB PID watchdog)
```bash
#!/usr/bin/env bash
# adversary-63c-i-a-a19a — run each wrong build over the 7 contract files + the probe file (declared before any run:
# every WB is expected to FAIL >=1 contract test (killed) unless listed in the report as a survivor candidate).
# usage: run_wb.sh <WB list, space-separated>
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/4d6979a0-821d-4faf-a3a4-d8a8b36d541b/scratchpad
T=$S/adv-wb
FILES="loremaster/tests/test_fixwave_a19a_63c_i_a.py loremaster/tests/test_fixwave_a19_63c_i_a.py loremaster/tests/test_agent_governance_63c_i_a.py loremaster/tests/test_agent_registry.py loremaster/tests/test_message_migrate_63b_ii_a.py loremaster/tests/test_message_enforcement_63b_ii_a.py loremaster/tests/test_comms_tool.py loremaster/tests/test_adversary_a19a_probes.py"
mkdir -p $S/wb_logs
for wb in "$@"; do
  while [ "$(free -g | awk 'NR==2{print $7}')" -lt 20 ]; do sleep 10; done
  python3 $S/adv_wrong_builds_a19a.py $T $wb > /dev/null || { echo "$wb PATCH-FAIL" >> $S/wb_summary.txt; continue; }
  cp $S/test_adversary_a19a_probes.py $T/loremaster/tests/
  ( cd $T && uv run python -c "import loremaster; print('PROVENANCE', loremaster.__file__)" && timeout 1500 uv run pytest -n 8 -q -p no:cacheprovider --tb=no -rf $FILES ) > $S/wb_logs/$wb.log 2>&1
  tail_line=$(tail -1 $S/wb_logs/$wb.log)
  contract_fails=$(awk '/^FAILED/ && !/test_adversary_a19a_probes/' $S/wb_logs/$wb.log | wc -l)
  probe_fails=$(awk '/^FAILED/ && /test_adversary_a19a_probes/{split($2,a,"::"); print a[2]}' $S/wb_logs/$wb.log | sed 's/\[.*//' | sort | uniq -c | awk '{printf "%s×%s ", $2, $1}')
  echo "$wb | $tail_line | contract_fails=$contract_fails | probe_fails=$probe_fails" >> $S/wb_summary.txt
done
python3 $S/adv_wrong_builds_a19a.py $T REF > /dev/null
echo ALLDONE >> $S/wb_summary.txt
# ---- run_suite.sh
#!/usr/bin/env bash
# usage: run_suite.sh <tree> <logfile> — full suite ALONE -n 12, PID watchdog kills pytest below 15 GB (polls 10 s)
T=$1; LOG=$2
cd $T || exit 2
{ echo "START $(date -Is) avail=$(free -g | awk 'NR==2{print $7}')G"; uv run python -c "import loremaster; print('PROVENANCE', loremaster.__file__)"; systemctl --user is-active spike-surreal.service; } > $LOG 2>&1
uv run pytest -n 12 -q -p no:cacheprovider --tb=line >> $LOG 2>&1 &
PID=$!
while kill -0 $PID 2>/dev/null; do
  if [ "$(free -g | awk 'NR==2{print $7}')" -lt 15 ]; then echo "WATCHDOG: killing $PID (avail < 15G)" >> $LOG; kill $PID; fi
  sleep 10
done
wait $PID; echo "EXIT=$?" >> $LOG; echo "END $(date -Is)" >> $LOG
```


## VERDICT
**CONTRACT INSUFFICIENT** (graded `16d2d82`, HEAD `3c7d1f0`, production byte-identical).

What the a19a addendum gets right, with receipts: it is satisfiable by an independently designed build (`11592 / 62 /
3 / 0`); its RED at `84af63f` is honest (80, on-defect); it kills all five a19 survivors and #485's PQ1; 23 of my 37
single-defect builds die in the contract files, including every obvious CD-1/CD-2/R1/R2/F-3-verb/F-2/FK-2 build and
three of the four fake-preflight builds.

What it waves through, each with a wrong build that passes all 11592 tests and a kill pin that is green on a correct
build (§A.3):
1. **MP-A (REACH, highest):** the "derived" ∀-refusal-classes pin — the instrument meant to make #485's class
   unrepresentable — fails OPEN on `raise self._x_refusal(...)` (this package's own idiom) and counts classes, not raise
   sites; a new refusal after the mint arrives unpinned both ways (N3b, N17). Fail closed + per-site coverage, or the
   runtime property (KP13) armed around every driven `comms(register)`.
2. **MP-B:** created-vs-found never raced against a concurrent winner (N5 → KP1).
3. **MP-C:** the race path's refusal text is unpinned (N7 → KP4).
4. **MP-D:** routing-is-not-sharing proven on ONE class only; existing-row decisions can be privately copied in the
   registry or the handler (N13, N14 → KP5/KP6 ∀ `_REFUSAL_CASES`).
5. **MP-E:** the two new id samples read the bound but never perturb it (N11, N12 → KP2, KP3).
6. **MP-F** (under FK-a reading A): leg-level refusals may serve an unmeasured `0` (L3 → KP7).
7. **MP-G:** a failed session-keep mint may degrade to an ownerless register (N6 → KP14) — an old virtue the handler
   rewrite can drop with no pin.

Plus three NEW DOORS for the sidecar (§5): both half-pairs' diagnosis (#1), the message-table half-pair (#2, PROBED:
never stamped, `report_unmigrated` = 1 forever, `refused=False`), and a failed compensation that leaves a keep behind
with only a log line (#4b). Not a defect: a cross-table dangling sender (unseedable — engine coercion, with a positive
control).
