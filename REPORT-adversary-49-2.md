# REPORT — adversary-49-2 (packet 49 CONTRACT ADVERSARY, r2 DELTA re-grade)

`brief-base v14 read` · `brief project v7 read`

**CAPABILITY CHECK (brief-base §4):** every demand met — read the 4 packet-49 test files +
design + spec + store-ref, lore tools loaded (`ToolSearch "+lore"`), comms/task ledgers
reachable, built BOTH a correct reference and 13 wrong builds in a `scratch_copy.sh` copy,
ran scoped pytest against spike-surreal `:18000`, produced this findings list. No gap.
**Model:** I cannot self-read my model; the brief asserts `claude-opus-4-8` and I proceeded on
that basis (report it as such). Role spec `~/.claude/agents/contract-adversary.md` READ +
EXECUTED (P0/P1/P1b/P1c/P2/P3/P6b/P7). **I do not spawn subagents; did the work directly.**

---

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT** — 1 blocking finding (a REVISION-INTRODUCED gap, the
  packet-03b class the brief told me to hunt). All 5 r1 fixes (F1–F5) + R1 CLOSE what r1 found.
  **R2's fix is correct in intent but INCOMPLETE and ships a NEW defect.**
- **P1 headline:** on the 4-file contract, **NO wrong build survives** — my correct reference
  is **111 passed / 0 failed** and all **13/13** wrong builds are CAUGHT. But a correct build is
  **NOT 0-failed on the FULL gate**: it fails **≥2 `test_retry_seam.py` pins** (receipts below),
  so the satisfiability receipt is only true under the r1/author's 4-file scoping.
- **FINDING 1 (BLOCKER — contract-completeness / builder-trap, from R2):** pin 17c (strengthened
  per r1-R2 to require `PrincipalKeyStore` be DISCOVERED by `test_retry_seam._discover_query_seams()`)
  pulls the new seam into EVERY `_QUERY_SEAMS` parametrization in `test_retry_seam.py` — whose
  HAND-WRITTEN maps `_SEAM_REJECTION_EVENTS` / `_SEAM_REJECTION_NOUNS` have **no `PrincipalKeyStore`
  entry**. A CORRECT build therefore fails: (a) `TestTheSeamsRejectionLogSurvivesTheCollapse::test_every_seam_still_logs_its_OWN_canonical_rejection_event`
  (map-completeness: *"seams with NO entry in the canonical list: ['PrincipalKeyStore']"*), and
  (b) `TestTheExhaustionRecordIsATTRIBUTABLE::test_the_exhaustion_record_names_the_seam...[PrincipalKeyStore]`
  (`KeyError` at line 7082, `_SEAM_REJECTION_EVENTS[seam.__name__]`). The packet-49 contract AND
  design F7 are SILENT on this registration obligation, and **pin-17c's own comment actively
  misleads** — it says *"no new registration needed (`_CTOR_VALUES` already carries the std ctor
  params)"*, true of `_CTOR_VALUES` but FALSE of the two rejection maps. `PrincipalKeyStore` appears
  0 times in `test_retry_seam.py`. See §FINDING 1 for the fix.
- **Fix-closure (F1–F5/R1/R2): all CLOSE (13/13 wrong builds caught)** — table in §FIX-CLOSURE.
- **Revision-sweep (packet 03b): F2 over-match CLEAN · F3 error-swallow CLEAN · R1 probe NON-VACUOUS
  · R2 → FINDING 1.** §REVISION-SWEEP.
- **Quantifier table (P1b):** every deny invariant ∀-over-inputs with an independent fixture +
  positive control; the one hand-enumerated invariant (uniform-deny 5 modes) is adequate for its
  named modes. §P1b.
- **Reach table (P1c):** the F2 regex now has REAL reach (a synthetic + a real new link both fire);
  pin 17c's reach is DERIVED (AST scan) and coverage-checked — but its delegation to `test_retry_seam`
  is what surfaces FINDING 1; the sanitiser AST-scan is single-call (the per-render mutation-proofs
  backstop it, now for BOTH `list` and `list-keys`). §P1c.
- **Residuals:** (R-a) verify's natural 10-return shape trips **PLR0911** (enabled repo-wide) — a
  builder-ergonomics nit, NOT a C-DEF (collapse the deny-returns or a scoped `# noqa`); (R-b) the
  contract-49-1 report carries INTERNALLY INCONSISTENT RED counts (SUMMARY 59F/38P/31E/128 vs
  receipts+message 54F/36P/30E/120) — the SUMMARY count reconciles with my measurement, the other is
  stale; documentation only. §RESIDUALS.
- **Graded: d09f0d6 · HEAD-at-report: d09f0d6 · SAME (0 behind).**
- **Packages considered:** none — I specified no shipped mechanism; my reference REUSES the existing
  `loremaster.index.records.sha512_hex`, `lorerunes.is_blank`, `loremaster.store._txn.{run_query,
  execute_transaction,bootstrap_session,signin_credentials}`, `loremaster.sanitise.{sanitise_line,
  safe_str}`, `secrets.token_urlsafe`, `argparse` (all stdlib/in-tree; no library-replaceable
  mechanism marked bespoke). `Packages considered: none — no NEW mechanism specified`.
- **Reuse ledger:** none — I authored no shipped symbols. The reference build + the two probe
  instruments live only in `/tmp` (disposable); all three are PASTED VERBATIM in §APPENDICES so the
  measurement is re-runnable (brief-base §1).
- **pointers:** satisfiability receipt §SATISFIABILITY · fix-closure §FIX-CLOSURE · FINDING 1
  repro §FINDING 1 · reference-build script §APPENDIX-A · wrong-build mutator §APPENDIX-B ·
  driver §APPENDIX-C.

## The ONE message to lead

`STATE: done · REPORT: REPORT-adversary-49-2.md · CONTRACT INSUFFICIENT — F1–F5/R1 CLOSE, but R2's pin-17c strengthening pulls PrincipalKeyStore into test_retry_seam's discovered-seam suite whose hand-written _SEAM_REJECTION_{EVENTS,NOUNS} maps lack it → a CORRECT build fails 2 retry_seam pins; contract/design silent, pin-17c comment says "no new registration needed" (false). 4-file satisfiability 111/0; needs a packet-49-owned registration pin + FULL-suite satisfiability`

---

## PROVENANCE (brief-base §6 / #140 — prove which tree)

All builds ran in a `scratch_copy.sh`-minted copy, provenance ASSERTED before and after:

```
scratch tool: ./scripts/scratch_copy.sh /tmp/adv49_2_ref   (exit 0)
loremaster.__file__ = /tmp/adv49_2_ref/loremaster/loremaster/__init__.py   (INSIDE scratch — re-checked at report time)
```

Live store: spike-surreal `ws://127.0.0.1:18000` (systemd `active`; NEVER `:18500`). The 4-file
run is scoped STRICTLY to the packet-49 files; the branch's ~446 pre-existing packet-39 RED is out
of scope and never conflated. FINDING 1's retry-seam evidence is IN SCOPE by the P1c rule (a guard
the contract RELIES on is graded), not a scope creep.

---

## FINDING 1 (BLOCKER) — R2's strengthening ships an unregistered seam: a correct build fails ≥2 retry-seam pins

**What r1-R2 asked for, and what the revision did:** r1 flagged pin 17c as existence-only (`hasattr(_query)`
proves nothing rides `run_query`). The revision STRENGTHENED it to also assert
`"PrincipalKeyStore" in {c.__name__ for _,c in test_retry_seam._discover_query_seams()}`
(`test_principal_keys_store.py::TestSharingProvenByMutation::test_principal_key_store_query_seam_is_covered_by_the_retry_suite`).
That is a GOOD strengthening — it forces the builder to give `PrincipalKeyStore` a real
`async def _query`, and discovery then makes the shared retry pins parametrize over it. **But
discovery has a cost the contract never states.**

**The defect:** `test_retry_seam.py` carries two HAND-WRITTEN, class-name-keyed maps that its pins
index directly:
- `_SEAM_REJECTION_EVENTS` (line ~6030) — the canonical `*.query.rejected` log event per seam.
- `_SEAM_REJECTION_NOUNS` (line ~6068) — the raised-message noun per seam.

Both were extended for `PrincipalStore` by packet 48-B and for two seams by packet 11-i-a — the maps'
OWN comments (lines 6035–6048) document that adding a seam REQUIRES a hand-written entry and name the
two catastrophic wrong instincts a trapped builder has (*"invent a bespoke seam so the classes fall OUT
of the AST enumeration — finding #120 — or call the reds 'pre-existing' and ship"*). **`PrincipalKeyStore`
has no entry in either map (0 mentions in the whole file).** So once the builder lands `_query`
(pin 17c forces it), discovery yields 15 seams and:

```
# on my CORRECT reference build (111/0 on the 4 files), the FULL gate is NOT clean:

$ pytest test_retry_seam.py::...::test_every_seam_still_logs_its_OWN_canonical_rejection_event
  loremaster.principal_keys:_txn.py:1227 principal_key.query.rejected   # my build emits it correctly...
  AssertionError (line 6234)  ->  observed.keys() has PrincipalKeyStore; _SEAM_REJECTION_EVENTS.keys() does not
  1 failed

$ pytest "test_retry_seam.py::...::test_the_exhaustion_record_names_the_seam...[PrincipalKeyStore]"
  KeyError at line 7082:  _SEAM_REJECTION_EVENTS[seam.__name__]   (seam.__name__ == "PrincipalKeyStore")
  1 failed   (28 other PrincipalKeyStore-param retry pins PASS — the seam genuinely rides run_query)
```

**Why the contract's satisfiability receipt missed it:** the r1 adversary AND the author both ran
satisfiability scoped to the 4 packet-49 files. Scoped there, a correct build IS 0-failed (I reproduce
111/0). The defect only appears when the FULL gate runs — which the builder MUST keep green ("no
regression"). The contract-49-1 report even asserts *"no regression (retry_seam 605 green)"* — true at
STUB time (the stub deliberately omits `_query`, measured 14 seams), FALSE the moment the builder adds
it. **This is the C-DEF class exactly: "the adversary's reference build goes 0-failed against this
contract, INCLUDING after any lint-demanded cleanup, before any builder sees it" — it does not, on the
gate the builder actually runs.**

**The trap is real, not theoretical:** a builder scoped to the 4 packet-49 files, reading pin-17c's
comment *"no new registration needed"*, will not have touched `test_retry_seam.py`, will be surprised by
2 reds in a foreign file, and lands in exactly the fork the map comments warn about.

**The missing pin / fix (name the test that should exist + the defect it catches):**
1. **Add a packet-49-OWNED pin** in `test_principal_keys_store.py` (beside pin 17c) that asserts
   `"PrincipalKeyStore" in test_retry_seam._SEAM_REJECTION_EVENTS` **and** `... in _SEAM_REJECTION_NOUNS`.
   Defect it catches: *the builder implements the `_query` seam (pin 17c green) but forgets the canonical
   rejection-event/noun registration, so an operator-facing log event ships unregistered and 2 retry-seam
   pins go red.* This pulls the obligation INTO the packet-49 contract and forces the builder to it,
   instead of leaving it to a full-suite red in a file outside the packet-49 writable set.
2. **Instruct the builder (design/contract)** to register the canonical values, following the
   `PrincipalStore` precedent: `_SEAM_REJECTION_EVENTS["PrincipalKeyStore"] = "principal_key.query.rejected"`
   and `_SEAM_REJECTION_NOUNS["PrincipalKeyStore"] = "principal_key query"` (a domain-naming noun keeps
   the monoculture pin happy). `test_retry_seam.py` is a test file the builder maintains — this is the
   sanctioned resolution, but it must be NAMED.
3. **Correct pin-17c's misleading comment** — replace *"no new registration needed"* with *"`_CTOR_VALUES`
   needs nothing, but the two `_SEAM_REJECTION_*` maps in test_retry_seam.py DO need a PrincipalKeyStore
   entry (see the packet-49 registration pin)"*.
4. **Run the satisfiability receipt over the FULL suite (or at least `test_retry_seam.py`)**, not just the
   4 files — this defect is invisible to a 4-file-scoped receipt by construction.

Severity note for right-sizing: this is a **contract-completeness / builder-trap** blocker, NOT an
"unsatisfiable-in-isolation" C-DEF. The 4-file contract is internally satisfiable (111/0). But a
builder following it exactly cannot land packet 49 green, and the contract both omits the obligation
and (via pin-17c's comment) tells the builder it does not exist. That is a fix-wave INSUFFICIENT.

---

## SATISFIABILITY RECEIPT (leg 1 — required)

I built the CORRECT reference (the emitter slice + fold; `PrincipalKeyStore.ensure_ready/mint/list_for/
revoke/verify/_query` + connection idiom + internal `PrincipalStore` for the shared mapper;
`PrincipalStore.set_expires/delete`; the CLI `build_parser` 9 verbs + `main`/`_dispatch` + both
factories + the `sanitise_line`/`safe_str` render). Full script in §APPENDIX-A.

**Against the revised contract AS WRITTEN (4 packet-49 files), 0 failed — INCLUDING the NEW F4/R1/R2
pins the r1 adversary never built against:**

```
$ cd /tmp/adv49_2_ref && uv run pytest \
    test_principal_keys_schema.py test_principal_keys_store.py test_principals_cli.py \
    test_principals_store.py::TestSetExpires test_principals_store.py::TestDelete -q -n auto
  111 passed in 6.52s
loremaster.__file__ = /tmp/adv49_2_ref/loremaster/loremaster/__init__.py
```

**Still 0-failed AFTER ruff --fix (the harder C-DEF leg — orphaned-import / import-sort cleanup):**

```
$ uv run ruff check --fix <the 3 reference files>    # 6 of 7 fixed (my reference's own redundancy)
$ uv run pytest <the same 5 selectors> -q -n auto
  111 passed in 6.46s
```

The 1 remaining ruff error is **PLR0911** on `verify` (10 returns > 6) — my reference's structure, and a
builder-ergonomics residual, NOT a contract trap (see §RESIDUALS R-a). Every pin is satisfiable by a
valid build; the contract does not pin return-count.

⚠ But this receipt is TRUE ONLY under 4-file scoping — see FINDING 1: the FULL gate is not 0-failed.

---

## FIX-CLOSURE (leg 2) — 13/13 wrong builds CAUGHT

Each wrong build restores the correct reference, applies ONE exact-string mutation, runs its target pin,
and classifies CAUGHT (pin FAILS) vs WAVED-THROUGH. Mutator §APPENDIX-B, driver §APPENDIX-C.

| # | wrong build (the ORIGINAL defect the fix targets) | target pin | result |
|---|---|---|---|
| F1 | constant-identity verify (#206 collapse) — after the distinct-secret fixture fix | `TestPerPrincipalIdentity206` | **CAUGHT** (1 failed) |
| F2 | a NEW `record<principal>` link added to the DDL — the reach the `\b` bug destroyed | `test_principal_key_is_the_ONLY_record_principal_link` | **CAUGHT** (1 failed) |
| F3 | `add` is a NO-OP (rc=0, nothing created) — the tolerant helper must still catch it | `test_add_creates_a_principal_on_invocation` | **CAUGHT** (1 failed) |
| F4a | `list-keys` renders `key.name` VERBATIM (r1's WAVED-THROUGH build) | `test_hostile_key_name_does_not_forge_a_row_in_list_keys` | **CAUGHT** (1 failed) |
| F4b | `list-keys` uses a PRIVATE launder clone (newline-strip, no shared seam) | `test_list_keys_render_routes_through_the_shared_sanitiser_by_mutation` | **CAUGHT** (1 failed) |
| F5 | *(the mandated `asyncio.run` `main`)* — closed structurally: `_run_cli` off-loops it; all 8 CLI e2e pins pass in the 111/0 (a sync-in-async `main` would `RuntimeError`) | 8 CLI e2e pins | **CLOSED** (0 failed) |
| R1 | CLI `mint-key` stores the RAW secret as the hash | `test_mint_key_stores_only_the_hash_never_the_raw_secret` | **CAUGHT** (1 failed) |
| R2 | `PrincipalKeyStore` has NO `async def _query` seam (inline queries) | pin 17c (`...query_seam_is_covered_by_the_retry_suite`) | **CAUGHT** (1 failed) — but see FINDING 1 |
| + | `list` renders `display_name` VERBATIM (F4 sibling) | `test_hostile_display_name_does_not_forge_a_row_in_list` | **CAUGHT** |
| + | `set_expires` clears by OMISSION (leaves old value) | `test_set_expires_clears_to_none_via_explicit_SET` | **CAUGHT** |
| + | `delete` via two `_query` DELETEs, not one `execute_transaction` | `test_delete_runs_the_cascade_in_ONE_transaction` | **CAUGHT** |
| + | verify uses a PRIVATE blank check (all 3 `is_blank` sites cloned) | `test_verify_routes_blank_check_through_the_shared_is_blank` | **CAUGHT** |
| + | verify CLONES the principal mapper (inline `Principal(...)`, bypasses `_row_to_principal`) | `test_verify_maps_the_principal_through_the_shared_mapper` | **CAUGHT** |
| + | slice built but NOT folded into `generate_ddl` (#131 class) | `test_principal_key_is_FOLDED_into_the_global_generate_ddl` | **CAUGHT** |
| + | CLI uses `load_config` (eager anthropic) | `test_the_cli_runs_with_no_anthropic_key_set` | **CAUGHT** |

**P0 controls fired (my instruments can lie the same way — 4 of my first-pass mutations WAVED-THROUGH,
all 4 were MY bugs, not contract defects, caught by the pass/fail control):** (i) WBF2/WBnofold wrote
the schema mutation to `loremaster/surreal_schema.py` while the real file is `store/surreal_schema.py`
— fixed the path, both then CAUGHT; (ii) WBblank replaced only 1 of 3 `is_blank` sites (the pin
correctly still saw the other two — proving pin 17a fires on ANY residual `is_blank` use) — replaced
all 3, then CAUGHT; (iii) WBloadconfig's anchor went stale after `ruff --fix` reformatted the imports —
re-anchored, then CAUGHT. Every "WAVED-THROUGH" was chased to a MUTATION error before trusting it.

---

## REVISION-SWEEP (leg 3 — packet 03b: did the revision ship NEW defects?)

| revision concern (from the brief) | probe | verdict |
|---|---|---|
| **F2 over-match** — does broadened `TYPE\b[^;]*?record<principal>(?![\w<])` falsely match a legit non-owner line? | ran the regex on `record<principal_group>`, `record<principals>`, `option<string>`, and the real `generate_ddl` | **CLEAN** — 0 false matches; real DDL yields exactly `{('principal','principal_key')}`; the `(?![\w<])` correctly rejects `record<principals>`/`record<principal_group>` |
| **F3 error-swallow** — does the table-absent tolerance in `_principal_emails`/`_db_snapshot` mask a real store error? | built an `add`-NO-OP; ran `test_add` | **CLEAN** — CAUGHT. The tolerance only short-circuits on an ABSENT table (returning empty), so it can cause a spurious FAIL (over-strict), never a spurious PASS |
| **R1 vacuous-probe** — can the CLI-level leak probe actually SEE a leak? | WBR1 (store the raw secret) | **NON-VACUOUS** — CAUGHT; the positive control (stored hash present) is real (it passes in the 111/0 on the correct build) |
| **R2 existence-only** — is the strengthening real, or two-sources? | see FINDING 1 | **FINDING 1** — the strengthening is real (a hand-rolled seam is caught) but INCOMPLETE: discovery creates an unregistered-seam obligation the contract omits |

## P1b — QUANTIFIER TABLE (verify's deny invariants)

Every deny condition is ∀-over-inputs with an INDEPENDENT fixture forcing exactly that condition +
the `test_all_clear_key_is_allowed_the_positive_control` positive control (so no deny is vacuous).
Empirically confirmed by the wrong-build battery (dropping each check reddens ONLY its own pin).

| invariant | ∀ or guarded | receipt |
|---|---|---|
| key.revoked_at IS NONE | ∀ | reference passes; a build ignoring revoke reddens `test_revoked_key_is_denied_on_the_next_verify` |
| key.expires_at check | ∀ | independent fixture `test_expired_key_is_denied_principal_fine` (principal fine) |
| principal.status == active | ∀ | independent fixture `test_suspended_principal_denies_a_live_key` (unsuspend re-allows) |
| principal.expires_at check | ∀ | independent fixture `test_expired_principal_denies_a_live_key` (live key) |
| revocation beats cache (R12) | ∀ | `test_revoked_key_is_denied_on_the_next_verify` re-verifies the SAME credential post-revoke |
| per-principal identity (#206) | ∀ (≥2 principals, 1 w/ 2 keys) | WB206 (constant identity) CAUGHT — fixture DISCRIMINATES |
| hash the WHOLE `name:secret` | ∀ | `test_verify_hashes_the_WHOLE_wire_string` (a different name → different hash → deny) |
| blank/malformed denied | ∀ (8 parametrized cases) | `TestBlankAndMalformedDenied` covers empty/ws/`:secret`/`name:`/`nocolon`/`: `/` :secret` |
| uniform deny / no oracle | **guarded** (5 hand-enumerated modes) | `test_every_denial_mode_returns_the_same_None` — adequate for the 5 named modes; a 6th mode would need its own fixture (F1's distinct-secret fix keeps all 5 minting on a correct build — I re-ran it in the 111/0) |
| raw secret never logged | ∀ | `test_the_raw_secret_never_appears_in_a_log_record` (my reference logs only laundered reasons) |
| set-expiry clears via explicit SET NONE | ∀ | WBclear (clear-by-omission) CAUGHT |

No vacuous-∀ hole among the deny conditions. Only guarded invariant is uniform-deny (5 enumerated modes) —
acceptable, same as r1.

## P1c — REACH TABLE (every guard/scan the contract introduces or relies on)

| guard / scan | reach DERIVED vs hand-list | coverage a checked var? | effect vs proxy | one-source (mutation-proven)? | verdict |
|---|---|---|---|---|---|
| `_RECORD_PRINCIPAL` regex over `generate_ddl` (pin 14) | DERIVED (full DDL) | yes — a new link makes `found != expected` (WBF2 CAUGHT) | effect | n/a | **SAFE** (F2 fixed; reach is real, over-match clean) |
| `test_the_forward_scope_regex_has_nonzero_reach` (positive control) | DERIVED (synthetic real+option link) | yes | effect | n/a | **SAFE** — fires for required AND `option<record<principal>>` |
| `test_the_slice_ROUTES_THROUGH_the_shared_ddl_emitters` | mutation of `_define_field` | yes (mutation) | effect | yes | SAFE (backstopped by clause pins for table/index) |
| pin 17c — `PrincipalKeyStore._query` DISCOVERED by `_discover_query_seams()` | DERIVED (AST scan of the package) | yes — WBR2 (no `_query`) CAUGHT | effect (membership) | delegates to `test_retry_seam` | **RELIED-ON GUARD → FINDING 1**: discovery is real, but the delegate's HAND-WRITTEN `_SEAM_REJECTION_*` maps are a hand-list the contract never registers into |
| `test_the_render_path_routes_through_the_shared_sanitiser_seam` (AST) | `principals.py`, `{sanitise_line, safe_str}` | partial — passes on ANY single sanitise call | proxy (call presence) | mutation-proofs backstop | ACCEPTABLE — the per-render mutation-proofs now cover BOTH `list` (WBlist/WBF... CAUGHT) AND `list-keys` (WBF4a/WBF4b CAUGHT), closing r1's R3 |
| `test_render_routes_through_the_shared_sanitiser_by_mutation` (`list`) | patches `sanitise_module.sanitise_line` + `p_module.sanitise_line` | yes (mutation) | effect | yes | SAFE |
| `test_list_keys_render_routes_through_the_shared_sanitiser_by_mutation` | same, for `list-keys` | yes (mutation) | effect | yes | SAFE (the NEW per-render proof — closes r1 FINDING 4/R3) |
| `test_source_contains_no_execute_flag_or_dry_run` / `test_no_verb_accepts_an_execute_flag` | `principals.py` single-module / `_ALL_VERBS` (9) | yes over the file / partial | effect | n/a | ACCEPTABLE (design fixes 9 verbs; source-scan backstops `--execute`) |
| `test_the_cli_does_not_call_load_config` (AST) + `test_the_cli_runs_with_no_anthropic_key_set` (behavioural) | `principals.py` | yes; behavioural pin proves it DOES load config | effect | n/a | SAFE (WBloadconfig CAUGHT) |
| pin 17c `test_principal_key_store_query_seam...` retry-suite delegation | DERIVED discovery, but the delegate's REGISTRATION maps are HAND-LIST | **NO** — no packet-49 pin checks the seam is REGISTERED in `_SEAM_REJECTION_*` | proxy (discovery ≠ registration) | two sources | **MISSING PIN — FINDING 1** |

Legs run: FINDING 1 EMPIRICAL (2 retry-seam pins reproduced RED on the reference); F2 over-match
EMPIRICAL (regex probe); pin-17c discovery EMPIRICAL (WBR2 + the discovered-seam list); the sanitiser
mutation-proofs EMPIRICAL (WBF4a/WBF4b/WBlist); the rest by the wrong-build battery.

## P3 — BRANCH REACHABILITY / P6 — CORPSE SWEEP / P6b — DELETED CODE

- **P3:** every verify deny-branch has a reddening fixture (see P1b); every CLI verb has an e2e or
  parser pin; the delete cascade's WHERE-scope has `test_delete_only_touches_the_named_principals_keys`.
  No unreachable pinned branch found.
- **P6 (corpses):** the packet is ADDITIVE — the stubs raise `NotImplementedError` / return `""`/`[]`,
  with NO retired behaviour. No test asserts an OLD behaviour. No corpse.
- **P6b (deleted/replaced code):** N/A — independent enumeration of the diff is purely new symbols
  (`principal_keys.py`, `set_expires`/`delete`, the emitter slice, the CLI). The replaced stubs have no
  observable behaviour to preserve. Confirmed against the design (additive scope) and the stubs at
  d09f0d6.

## P7 — RED HONESTY

Reproduced the contract's RED against the STUB in scratch (scoped to my 4-file selection): **59 failed,
21 passed, 31 errors, 111 collected** — all behavioural (fixture `NotImplementedError` → errors,
empty-DDL/missing-verb → failures); **no ImportError, no collection error**. My scoped passed-count (21)
reconciles the author's report SUMMARY (38) exactly: I ran only `TestSetExpires`+`TestDelete` from the
store file, not its 17 unchanged 48-B tests (21 + 17 = 38). See §RESIDUALS R-b on the report's count
inconsistency.

## RESIDUALS

- **R-a (builder-ergonomics, not a defect): PLR0911 on `verify`.** A faithful uniform-deny `verify` has
  ~10 early returns; PLR0911 (threshold 6) is enabled repo-wide (`select=["...","PL"]`, only
  PLC0415/PLR0913/PLR2004 ignored). NOT a C-DEF — the contract pins deny BEHAVIOUR, not return-count; a
  builder collapses the deny branches (`if any((...)): return None`) or adds a scoped `# noqa: PLR0911`.
  Worth a one-line note in the design so the builder isn't surprised.
- **R-b (documentation only): the contract-49-1 report's RED counts are internally inconsistent.** Its
  SUMMARY BLOCK says `59F/38P/31E (128 collected)`; its "Verification receipts" tail AND its one-line
  message say `54F/36P/30E (120 collected)`. The SUMMARY count reconciles with my re-measured RED (the
  128 = full store file incl. 17 unchanged 48-B); the 120 is a stale pre-revision figure. No behavioural
  impact — but per "re-derive every inherited number", the lead should trust the 128 line.
- **R1/R2/R3/R4 (r1's residuals) status:** R1 (store-level leak vacuous) → CLOSED by the new CLI-level
  probe (WBR1 CAUGHT, positive control real). R2 (existence-only) → strengthened, but see FINDING 1.
  R3 (sanitiser AST reach) → CLOSED by the per-render mutation-proofs now covering `list` AND `list-keys`.
  R4 (no timing-oracle pin) → still ACCEPTABLE (uniform hash-index lookup; no action).

---

## VERDICT

**CONTRACT INSUFFICIENT.** One blocking finding, plus two non-blocking residuals.

1. **FINDING 1 (BLOCKER)** — register `PrincipalKeyStore` in `test_retry_seam.py`'s
   `_SEAM_REJECTION_EVENTS`/`_SEAM_REJECTION_NOUNS` (with a packet-49-owned pin FORCING it), correct
   pin-17c's misleading *"no new registration needed"* comment, and run the satisfiability receipt over
   the FULL suite. *A correct build fails ≥2 retry-seam pins today; the contract omits the obligation
   and its own comment denies it exists.*
2. **R-a** — note the PLR0911 ergonomics for `verify` in the design (not blocking).
3. **R-b** — the lead should trust the report SUMMARY's 128-collected RED count, not the stale 120.

The contract is OTHERWISE STRONG: all 5 r1 fixes (F1–F5) + R1 close what they targeted, the F2 regex now
has real reach with no over-match, F3's tolerance masks nothing, the sanitiser sharing is mutation-proven
for BOTH renders, the deny conditions are each ∀-pinned with a positive control, and 13/13 wrong builds are
CAUGHT on the 4-file contract. The single blocker is the packet-03b class the brief predicted: **a fix that
"just implements what the adversary asked" (R2: make the seam discovered) shipped a downstream obligation the
contract does not cover** — findable only by running the FULL gate against a correct build, which the 4-file
satisfiability receipt is scoped to miss.

---

## APPENDIX-A — the reference-build script (the satisfiability instrument; run at `/tmp/adv49_2_build_reference.py`)

Applies a known-correct packet-49 implementation onto the scratch tree via idempotent exact-string
replacements over the 3 stub files. Reference `verify` (the four re-checks; routes blank through the
shared `is_blank`, maps the principal via an internal `PrincipalStore.get_by_email`→`_row_to_principal`,
no cache), `delete` (children-first cascade in ONE `execute_transaction`, returns N), the emitter slice
folded into `generate_ddl`, the 9-verb CLI rendering through `sanitise_line`/`safe_str`, and `main` using
the mandated `asyncio.run` idiom. Key excerpts:

```python
# surreal_schema.py — the folded slice
_PRINCIPAL_KEY_FIELD_SPECS = (
    ("hash", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),
    ("name", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),
    ("principal", f"record<{PRINCIPAL_TABLE}>", ""),
    ("created_at", "datetime", "DEFAULT time::now()"),
    ("expires_at", "option<datetime>", ""),
    ("revoked_at", "option<datetime>", ""),
)
def _principal_key_statements():
    s = [_define_table(PRINCIPAL_KEY_TABLE)]
    s += [_define_field(PRINCIPAL_KEY_TABLE, n, t, constraint=c) for n, t, c in _PRINCIPAL_KEY_FIELD_SPECS]
    s.append(_unique_index(PRINCIPAL_KEY_TABLE, f"{PRINCIPAL_KEY_TABLE}_hash", ("hash",)))
    s.append(_unique_index(PRINCIPAL_KEY_TABLE, f"{PRINCIPAL_KEY_TABLE}_principal_name", ("principal", "name")))
    return s
def generate_principal_key_ddl(): return ";\n".join(_principal_key_statements()) + ";\n"
# generate_ddl: statements += _principal_statements(); statements += _principal_key_statements()

# principal_keys.py — verify (deny returns collapsed by the builder to avoid PLR0911; shown expanded)
async def verify(self, presented):
    if is_blank(presented): return None
    if ":" not in presented: return None
    name, secret = presented.split(":", 1)
    if is_blank(name) or is_blank(secret): return None
    key_rows = self._as_rows(await self._query(
        "SELECT name, revoked_at, expires_at, principal.email AS p_email "
        f"FROM {PRINCIPAL_KEY_TABLE} WHERE hash = $h", {"h": sha512_hex(presented)}))
    if not key_rows: return None
    key_row = key_rows[0]; now = datetime.now(UTC)
    if PrincipalStore._to_aware_utc(key_row.get("revoked_at")) is not None: return None
    ke = PrincipalStore._to_aware_utc(key_row.get("expires_at"))
    if ke is not None and ke <= now: return None
    principal = await self._principals.get_by_email(str(key_row.get("p_email")))
    if principal is None or principal.status != "active": return None
    if principal.expires_at is not None and principal.expires_at <= now: return None
    return KeyVerification(principal=principal, key_name=str(key_row.get("name")))
# _query rides the SHARED run_query with noun="principal_key query", label="principal_key.query.rejected"
```

The full script (all exact-string patches for the 3 files) is at `/tmp/adv49_2_build_reference.py`; it is
disposable scratch, so the load-bearing excerpts are pasted here per brief-base §1. Provenance:
`loremaster.__file__ = /tmp/adv49_2_ref/loremaster/loremaster/__init__.py`.

## APPENDIX-B — the wrong-build mutator (`/tmp/adv49_2_mutate.py`)

13 named mutations, each an exact-string replace over a pristine snapshot (`/tmp/adv49_2_snap`). The four
representative ones:

```python
# WB206 constant identity: get_by_email(str(key_row["p_email"])) -> get_by_email("alice@example.com")
# WBF2   new link:         add ("owner2", "record<principal>", "") to _PRINCIPAL_KEY_FIELD_SPECS
# WBF4a  list-keys verbatim: print(f"{sanitise_line(k.name)}\t{flag}") -> print(f"{k.name}\t{flag}")
# WBR1   raw secret store:  secret_hash=sha512_hex(wire) -> secret_hash=secret
```

## APPENDIX-C — the driver (`/tmp/adv49_2_driver.sh`)

For each WB: restore snapshot → `python mutate.py WB` → `pytest <target-node>` → classify CAUGHT
(`grep 'failed|error'`) vs WAVED-THROUGH (`grep '^N passed'`) → restore. Final battery (all 13 CAUGHT
after the P0-control-caught instrument fixes):

```
[CAUGHT] WB206  WBF2  WBF4a  WBF4b  WBR1  WBR2  WBlist  WBclear  WBdeltxn  WBblank  WBmapper  WBnofold  WBloadconfig
```

The FINDING-1 retry-seam evidence (separate from the driver):
```
$ pytest test_retry_seam.py -k PrincipalKeyStore    ->  1 failed, 28 passed
  (the fail: test_the_exhaustion_record_names_the_seam...[PrincipalKeyStore], KeyError _SEAM_REJECTION_EVENTS)
$ pytest test_retry_seam.py::...::test_every_seam_still_logs_its_OWN_canonical_rejection_event  ->  1 failed
  (observed.keys() has PrincipalKeyStore; _SEAM_REJECTION_EVENTS.keys() does not)
```
