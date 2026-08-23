# REPORT — coldaudit-61b-w1 (COLD AUDIT, the PDP CORE)

brief-base v14 read
brief project v7 read
store-ref cited: §2 (IN-inside-OR TableScan trap #413; IndexScan-vs-TableScan-via-EXPLAIN),
§1.1 (DDL clause rule — read-only context, no DDL changed by this wave), §4 (record<> owner
links, RELATE endpoint non-enforcement — read-only context).

---

## ⭐ FOCUSED RE-CHECK (2026-08-23, delta at 123 pins) — VERDICT: **GO**

The builder applied the security-auditor's **#416 (MEDIUM)** fix + **SEC-F2/F3/F4** and my **R4**
residual (adopted as a fix) to the PDP core. My prior GO was on the pre-fix build (`pdp.py` md5
`0773beae…`); this re-check verifies the DELTA on the fixed build (`pdp.py` md5 `2155d764…`,
`surreal_schema.py` md5 `3079d358…`). The gates/oracle/boundaries I already GO'd stand — the
delta did not break them, and it closed the one MEDIUM latent leak the security pass found.

**Graded: `599354a` · HEAD-at-report: `599354a` · SAME** (wave still UNCOMMITTED; graded as-on-disk).

**Gates re-run, all SOLO (foreground, no contention):**
| gate | result |
|---|---|
| both contract files (`-n auto`) | **123 passed** (was 106; +17 delta pins) |
| full suite SOLO `pytest loremaster/tests -n auto` | **8595 passed, 50 skipped, 3 xfailed, 0 failed** (276s; was 8589, +6 new oracle pins) |
| `./scripts/typecheck.sh` | exit 0 |
| `uv run ruff check .` | clean, exit 0 |
| `pending_contract_gate.py --currency` | **PASS** (typecheck/ruff/pytest GREEN, exit 0) |
| charter (3) + w2 shape `test_keeps_schema` (58) + w3 fold `test_schema_fold_coverage` (29) | 90 passed |

**The 4 NEW mutation legs — re-derived INDEPENDENTLY (real-tree edit, `cp -a` backup, byte-exact
restore; both files md5-verified back to `2155d764…`/`3079d358…`):**

| leg | mutation | pin(s) that RED | result |
|---|---|---|---|
| **M7** (#416) | `ScopeInKeeps.to_surql` → UNPARENTHESISED (revert the fix) | oracle `TestCompositionSafetyNoLeakUnderAnd::test_and_owner_and_scope_in_keeps_returns_only_the_owners_rows` + pure `TestPredicateFragmentsAreSelfContained` (both structural pins) | **all RED**, **AND the single-brain oracle `test_authorize_equals_…` stayed GREEN** ✅ — proves the leak is reachable ONLY by IR composition (`And`-over-`ScopeInKeeps`), never via the shipped `authorize_filter`, so the oracle canNOT catch it and a dedicated composition-safety pin was genuinely required. This is the #416 point, reproduced. |
| **R4** | private `PRINCIPAL_TABLE = "principal"` in `surreal_schema` | oracle `test_governed_table_names_are_imported_from_lorerunes[PRINCIPAL_TABLE]` | **RED** (`assert (True and not True)`); `[AGENT_TABLE]` (untouched) stayed green — the AST import-not-assign guard discriminates ✅ |
| **F3** | drop the `Subject` empty-identity check | pure `test_subject_rejects_empty_identity[principal_id]` + `[agent_id]` | **both RED** ✅ |
| **F4** | `_AUDITED_ACTIONS` → hand-list omitting `SET_OWNER` (revert the derive) | pure `test_admin_set_owner_is_always_audited` + `test_audit_carve_out_predicate_is_norows[SET_OWNER]` + oracle `test_admin_mutating_audit_selects_zero_rows[SET_OWNER]` | **all 3 RED** ✅ — a hand-list omission both under-audits SET_OWNER AND lets admin mutate the audit trail via SET_OWNER; deriving `frozenset(Action) - {READ}` closes both by construction |

**#416 fix is COMPLETE + index-neutral (item 3):**
- Every multi-disjunct node's `to_surql` is now self-contained — `And`/`Or`/`ScopeInKeeps` all wrap
  in `(...)`. The reach-law structural pin `test_no_node_emits_an_unparenthesised_top_level_or`
  (a sound paren-depth-0 `" OR "` scanner, `_has_unparenthesised_top_level_or`) covers every
  multi-disjunct emitter + one-of-each, so a node that opts out reds.
- **INDEPENDENT EXPLAIN** of the actual emitted 2-keep member-READ predicate against the live
  3.2.4 store: fragment ends `… OR (scope = $k_… OR scope = $k_…)` (parenthesised ScopeInKeeps);
  plan = `['SelectProject','Filter','UnionIndexScan','IndexScan'×5]`, **`scans_gov(TableScan)=False`**.
  SurrealDB flattens `A OR (B OR C)` and still index-serves it → **no #413/#107 regression**. The
  security auditor's F1 index-plan tension is resolved: parenthesising is index-neutral.

**R4 re-home is SHARING, not a copy (item 4):**
- `lorerunes/__init__.py` re-exports `PRINCIPAL_TABLE`/`AGENT_TABLE`; `surreal_schema.py` does
  `from lorerunes import PRINCIPAL_TABLE as PRINCIPAL_TABLE` / `AGENT_TABLE as AGENT_TABLE`
  (explicit re-exports, SEC-R4); 7 downstream modules consume the re-export (all transitively get
  the lorerunes object). The identity/AST pins pass and the leg-R4 mutation reds on a private copy.
  `lorerunes` imports no sibling (charter pin green; leg-5b in the original audit proved a sibling
  import reds it). My prior R4 residual is now CLOSED.

**SEC-F2 (absent-owner) verified:** `Resource.owner_*` are `str | None`; `matches` handles `None`
(owner predicate = False, scope predicate still applies); the oracle carries NONE-owner rows
(r13 server, r14 agent-private) and `TestAbsentOwnerRowsAgree` proves store NULL ≡ Python None
across every subject/action. My prior F2-class coverage note is now closed by the oracle fixture.

**Nothing else regressed:** full suite 8595/0 SOLO; git `diff --stat` shows only the 3 wave files;
both mutated files restored byte-exact (md5 re-verified); no orphan processes.

**RE-CHECK VERDICT: GO.** The delta closes the one MEDIUM latent leak (#416) and three LOW
hardening items (SEC-F2/F3/F4) + my R4, each with a mutation-proven pin; the pre-fix GO gates all
still pass. The prior residuals R2 (slots) and R3 (fixed-scope-literals-bound) remain LOW/benign
and un-addressed (not raised by the security pass); R1 (leg-1 framing) and R4 are now moot.

*(The original pre-fix GO audit — full gate re-runs, the 5 original mutation legs, W1 trust-anchor
proof, boundary/charter/IN-expansion checks — is preserved below as the historical record.)*

---

## SUMMARY BLOCK
- **state:** done
- **VERDICT: GO** — every gate re-runs GREEN SOLO; all 5 brief mutation legs (+3 bonus legs)
  confirmed RED→restored byte-exact; the single-brain oracle is the REAL live 3.2.4 engine and
  is the *unique* catcher of a `to_surql`-only split; charter pin is property-derived; the D2
  re-home is sharing (identity + AST), not a copy; boundaries clean; the #413 IN-expansion plan
  pin is a real EXPLAIN.
- **deviations:** none (read-only audit; no repo file left modified — proven byte-exact).
- **Packages considered:** none — no mechanism specified (this is a verdict pass, not a build).
- **Reuse ledger:** none — no new reusable symbol introduced; my instrument is the mutation
  recipe (in-place edit + `cp -a` restore), pasted verbatim in §Mutation proof.
- **Graded:** `599354a` · HEAD-at-report: `599354a` · SAME. (Wave UNCOMMITTED; the new files
  `lorerunes/lorerunes/pdp.py` + the two contract files are untracked at this sha, graded
  as-on-disk; `surreal_schema.py`/`__init__.py`/the design doc are `M`.)
- **decisions-needed:** none.
- **receipt pointers:**
  - gate re-runs (all SOLO) — §Gates re-run
  - 5 mutation legs + 3 bonus (W1 / leg2b CONTAINS / leg6 identity) with `__file__` provenance — §Mutation proof
  - oracle-is-real / charter-derived / re-home-sharing / boundary / IN-expansion — §Targeted checks
  - RESIDUALS (4, all NON-blocking) — §Residuals

---

## Gates re-run (all foreground, SOLO — no contention)

| gate | command | result |
|---|---|---|
| pure core (91) | `pytest lorerunes/tests/test_pdp_core.py -p no:xdist` | **91 passed** in 0.08s |
| live oracle (15) | `pytest loremaster/tests/test_pdp_oracle_61b.py -p no:xdist` (TEST store :18000) | **15 passed** in 2.67s |
| both contract files (106) | `pytest <both> -n auto` | **106 passed** in 4.66s |
| full suite SOLO | `pytest loremaster/tests -n auto -q` | **8589 passed, 50 skipped, 3 xfailed, 0 failed** in 277.19s |
| typecheck | `./scripts/typecheck.sh` | **exit 0** (all 7 roots OK) |
| ruff | `uv run ruff check .` | **All checks passed!** exit 0 |
| currency | `pending_contract_gate.py --currency` | **CURRENCY: PASS** — typecheck/ruff/pytest all GREEN, exit 0 |
| w2 shape guard | `pytest test_keeps_schema.py -p no:xdist` | **58 passed** (brief said ~56; 58 collected, 0 failed) |
| w3 fold guard | `pytest test_schema_fold_coverage.py -p no:xdist` | **29 passed** |
| CHARTER pin | `pytest ...::TestLorerunesStdlibOnlyCharter -p no:xdist` | **3 passed** |

Store identity receipt: `ws://127.0.0.1:18000` (spike-surreal, systemd active) reports
`surrealdb-3.2.4+20260803.93ab219` — the oracle runs against the REAL 3.2.4 engine, never a mock.

⚠ **Process-hygiene note (not a defect, a discipline receipt):** my first attempts launched the
full suite + currency gate via `nohup … &` inside a backgrounded Bash — this DOUBLE-backgrounded,
so the harness reported "exit 0" for the *launcher shell* while three heavy `pytest -n auto` runs
(full suite + two currency-gate pytests) ran concurrently. That 3-way contention reproduced the
#405 flake exactly as store-law warns: an E/F burst at ~42% of the full run. I killed all
contending processes, DISCARDED that run, and re-ran the full suite strictly SOLO in the foreground
→ 8589/0. The green counts above are the SOLO runs. This independently validates the brief's
"run the full suite SOLO" instruction and the #405-under-load caveat.

---

## Mutation proof (re-derived INDEPENDENTLY; real-tree edit, `cp -a` content backup, byte-exact restore)

Backup: `/tmp/coldaudit61b_backup/{pdp.py,surreal_schema.py}` + `orig.md5`.
**#140 provenance receipt (both packages resolve to the REAL working tree — so a real-tree edit
IS a valid mutation proof, no scratch copy needed and no scratch-poison risk):**
```
lorerunes.__file__  = /home/ejprice/PycharmProjects/lore/lorerunes/lorerunes/__init__.py
loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/store/../__init__.py
```
Pre-mutation md5 (== live tree): `pdp.py 0773beae9a9725e01649d4b37bddd3ba` ·
`surreal_schema.py 67200391da1422ea7fb529000001ec1e`. Each leg: mutate (assert target unique) →
run the targeted pin → observe RED → `cp -a` restore → md5 re-verify. **Final md5 of both live
files == pre-mutation** (proven twice). `git diff --stat` post-audit shows ONLY the wave's 3
intended files — my mutations left zero trace.

| # | mutation (production code) | pin that must RED | result |
|---|---|---|---|
| **1** | `ScopeEq.matches` → `return True` | oracle `test_authorize_equals_the_emitted_filter_over_the_store` | **oracle RED** ✅ (also reds 7 pure `matches`-side pins — see R1) |
| **2** | `ScopeInKeeps.to_surql` → literal `scope IN $keeps` | pure `..._never_a_literal_IN` **and** oracle `..._with_TWO_keeps_indexscans_no_tablescan` | **both RED** ✅ |
| **3** | `requires_audit` member-check → `target_scope=SCOPE_SERVER` (cloned, drops grantability) | pure `test_admin_set_scope_into_a_non_grantable_keep_is_audited` | **RED** ✅; discriminator `..._grantable_keep_is_NOT_audited` still **PASSES** (pin genuinely discriminates) |
| **4** | re-introduce private `AUDIT_TABLE = "audit"` in `surreal_schema` | oracle `test_audit_table_is_imported_from_lorerunes_not_assigned_locally` | **RED** ✅ (`assert (True and not True)`) |
| **5** | `import pydantic` in `lorerunes/pdp.py` | pure charter `test_every_lorerunes_module_imports_only_stdlib_or_itself` | **RED** ✅ (`{'pdp.py': {'pydantic'}}`) |

**Bonus legs (strengthen the brief's own checks):**

| # | mutation | why | result |
|---|---|---|---|
| **W1** | `OwnerAgentEq.to_surql` → `"true"`, **matches UNCHANGED** (a `to_surql`-only split) | brief item #3 — the split-brain must red *ONLY* the oracle | **91 pure PASS, oracle RED** ✅ — the pure pins CANNOT see a `to_surql`/`matches` divergence; only the live engine can. This is the definitive trust-anchor proof (leg 1 above reds pure pins too, so it does NOT isolate the oracle — W1 does). |
| **2b** | `ScopeInKeeps.to_surql` → per-keep `scope CONTAINS $k` (no `" IN "` token) | adversary F1 — prove the plan pin's EXPLAIN check (:477) catches a non-`IN` TableScan the syntactic `" IN "` check (:466) can't | plan pin **RED at :477** with `ops=['SelectProject','TableScan']` ✅ — the plan pin is a **real EXPLAIN**, load-bearing independent of the syntactic token. F1's fix works. |
| **6** | `surreal_schema._PRINCIPAL_ROLES` → separate-but-equal `("member","admin")` | brief item #5 — D2 sharing by IDENTITY, not value | identity pin `test_principal_roles_are_the_SAME_object_as_lorerunes` **RED** ✅ |

---

## Targeted checks (brief items #3–#7)

**#3 — the single-brain oracle is REAL (the trust anchor):** ✅
- Runs against the live `surrealdb-3.2.4` engine at `ws://127.0.0.1:18000` (version probed), NEVER
  a Python mock; the per-module fixture mints a UNIQUE throwaway DB and reaps it.
- Fixture is genuinely hostile: `_all_subjects` = 5 subjects
  (alice-member{k1}, bob-member{k1}, alice-no-keeps, **alice 2-keeps{k1,k9}** — the #413
  IN-expansion exerciser, alice-admin) × 12 `_HOSTILE_ROWS` (2 principals × ≥2 agents each; every
  scope; keep rows in/out of `$my_keeps`; server rows; the empty-keeps case is a dedicated subject
  + a dedicated pin). SET_SCOPE covered grantable (k1) AND non-grantable (k9).
- W1 (above) proves a split-brain reds ONLY the oracle → the pure pins provably cannot catch it.

**#4 — the CHARTER pin is property-DERIVED (reach law #344/#345):** ✅
- `_lorerunes_modules()` = `Path(package.__file__).parent.glob("*.py")` — a package-dir GLOB, not a
  hand-list → a NEW module is scanned automatically (coverage-as-checked-variable), guarded against
  vacuity by `test_the_module_set_is_non_empty`.
- allowed set = `set(sys.stdlib_module_names) | {"lorerunes"}` — stdlib from the INTERPRETER's
  authoritative frozenset, never a hand-list. Empirically: `import pydantic` (leg 5) AND
  `import loresigil` (a sibling, leg 5b) BOTH red the pin. Belt-and-braces `pyproject dependencies == []`
  pin present.

**#5 — the D2 re-home is SHARING, not a copy:** ✅
- `surreal_schema` IMPORTS `PRINCIPAL_ROLES`/`PRINCIPAL_ROLE_MEMBER`/`AUDIT_TABLE` from `lorerunes`;
  `_PRINCIPAL_ROLES = PRINCIPAL_ROLES` (same object — identity pin), local `AUDIT_TABLE = "audit"`
  and `_PRINCIPAL_ROLE_ADMIN` removed. Sharing proven by mutation: a private tuple copy reds the
  identity pin (leg 6); a private `AUDIT_TABLE` string reds the AST import-not-assign pin (leg 4).
  `lorerunes` imports no sibling (charter pin, leg 5b).

**#6 — BOUNDARY (Fork D):** ✅ CLEAN.
- `grep` of `lorerunes/pdp.py` + `__init__.py`: zero `get_access_token`/`AccessToken`/`credential`
  (62) and zero `comms`/`memory`/`task`/`finding` write/migration (63/64) — the only hits are
  docstring mentions of "finding #413". The oracle imports only `surreal_schema` (the D2 re-home,
  61b scope) + `_txn.execute_transaction` (store-law §3), and touches only the SYNTHETIC
  `gov`/`audit`/`principal`/`agent` tables it seeds itself. `Resource.table` is a typed field; the
  #415 derive-from-id enforcement is a **forward-note (comment, NOT a pin)** in the contract header
  — 61b does not falsely claim it.

**#7 — IN-expansion correctness (#413 / store-ref §2):** ✅
- `ScopeInKeeps.to_surql` EXPANDS to per-keep `scope = $k_i` disjuncts (empty set → `false`),
  joined unparenthesised so a parent `Or` splices them flat — never a literal `scope IN $set`.
- The emitter EXPLAINs as an IndexScan (NO TableScan of `gov`) at the ≥2-keep case: the 15-green
  oracle includes `test_member_read_emitter_with_TWO_keeps_indexscans_no_tablescan`, with TWO
  positive controls (`test_positive_control_unindexed_predicate_tablescans` and
  `test_positive_control_literal_IN_inside_OR_tablescans`) proving the plan walker can SEE a
  TableScan. Leg 2b confirms the plan-level check is a real EXPLAIN, not result-only.

**Spec fidelity (design `2026-08-22-packet61-pdp-audit-rulings.md`):** the per-action policy matches
Fork C **reading 1** (exact `(principal,agent)` for both private scopes on WRITE/DELETE), Fork A
(closed IR + two total interpreters, `authorize == authorize_filter(...).matches`), Fork G
(`requires_audit = allowed ∧ admin ∧ mutating ∧ ¬member_filter(action).matches(resource)`), the D1
addendum (B2 — Resource carries `table`, `authorize` keeps §5 signature, `authorize_filter(s,a,table)`
gains table), D4(a) (owner DELETE scope-independent), D4(b) (SET_SCOPE = owner ∧ grantable target),
D2 (re-home to lorerunes), and F3 (stdlib frozen dataclasses, not pydantic; property-derived charter).
The mutating-action `==` audit-domain cross-check (`_AUDITED_ACTIONS` NOT re-homed) is a must-AGREE
across two distinct vocabularies (enum names vs the audit ASSERT string domain), correctly pinned.

---

## RESIDUALS (individual verdicts; all NON-blocking — do not gate GO)

- **R1 (report-quality nit, NOT a code defect): builder mutation leg-1 does not isolate the oracle.**
  `ScopeEq.matches → True` reds 7 PURE pins as well as the oracle, so the builder's leg-1 framing
  ("only-python rows appear; single-brain oracle caught it") slightly overstates that leg. The
  genuine "oracle is the *unique* catcher" proof is a `to_surql`-only split — I re-derived it as W1
  (91 pure GREEN, oracle RED). The oracle's load-bearing status is INDEPENDENTLY CONFIRMED; only the
  builder's choice of leg-1 mutation was weak. No action required on the code.

- **R2 (LOW hygiene, from adversary re-grade): `slots=True` documented but not independently pinned.**
  The value-object pins assert BEHAVIOUR (frozen + rejects-unknown-kwarg + validated + no-defaults),
  which a non-`slots` frozen dataclass also satisfies. The build DOES use `slots=True`; it is simply
  not guarded by its own pin. Immutability/no-extra IS pinned. Optional one-line pin.

- **R3 (LOW, contract-completeness, from adversary F4): fixed scope literals not pinned bound.**
  The contract's anti-injection pins check `alice`/`ag_a` (caller-controlled) are bound, but not the
  FIXED scope literals (`agent-private`/`principal-private`/`server`). The BUILD binds them correctly
  (`ScopeEq.to_surql` uses `_param_name`), so this is a contract gap, not a code defect. Harmless
  (module constants, not attacker-controlled).

- **R4 (LOW, drift risk — matches adversary residual; spec-scope gap, not a builder deviation):**
  the emitter hardcodes `_PRINCIPAL_TABLE = "principal"` / `_AGENT_TABLE = "agent"` in `pdp.py` — a
  SECOND copy of `surreal_schema.PRINCIPAL_TABLE`/`AGENT_TABLE`, un-cross-checked. D2 re-homed
  `PRINCIPAL_ROLES`/`AUDIT_TABLE` for exactly this one-column-one-vocabulary drift class, but the D2
  ruling named only the role domain + `AUDIT_TABLE`, so the builder correctly did not re-home the
  table names. Cannot manifest at 61b (no real governed tables; the oracle seeds matching synthetic
  tables). **Recommend:** 63/64 (which build real `Resource`s from real rows and run governed reads
  against real `principal`/`agent` tables) re-home these two constants to `lorerunes` like
  `AUDIT_TABLE`, OR add a cross-check pin — a rename of the principal/agent table would otherwise make
  the emitter's `type::record('principal', …)` silently target a non-existent table.

**Registration sites:** `registration_sites.py` STALE rows (`test_shellout_allowlist`, `test_symbols`,
`test_startup_divergence_reconcile`, `test_static_snapshot_reacquire`, `pyproject.toml missing
lorescribe`) are all PRE-EXISTING standing-worklist items unrelated to 61b — 61b adds no new workspace
member (only new public symbols within already-registered `lorerunes`, re-exported via `__init__.py`).
The `pyproject missing: lorescribe` row is the charter working as intended (deps==[]). No 61b
registration site is owed — the builder's claim holds.

## Discipline receipts
- TEST store `ws://127.0.0.1:18000` ONLY; production `:18500` never touched by any test.
- The oracle IS the live 3.2.4 engine; every negative paired with a positive control (verified).
- No repo file edited on exit — both mutated files restored byte-exact (md5 re-verified twice); no
  git state mutated; `git diff --stat` shows only the wave's 3 intended files. No orphan processes.

## Bottom line
**GO.** The contract's load-bearing instruments are all real and mutation-proven: the live-store
single-brain oracle (unique catcher of a `to_surql`-only split, W1), the property-derived stdlib
charter, the D2 sharing-by-identity + AST guards, and the #413 IN-expansion plan pin (a real EXPLAIN,
F1 fix confirmed). Boundaries to 62/63/64 are clean. The four residuals are LOW/benign and none gate
this commit; R4 is worth carrying forward as a named 63/64 cross-check.
