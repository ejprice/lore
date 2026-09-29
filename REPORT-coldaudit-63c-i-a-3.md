brief-base v18 read · brief project v7 read

# REPORT-coldaudit-63c-i-a-3 — cold REFUTE audit of the 63c-i-a final fix build (patch `956e4136…`)

## SUMMARY BLOCK
- **state:** done-with-deviations · **verdict: NO-GO for patch `956e4136` as-is** — it does not meet the spec as it stands after am-37 §5/§6 (4 MAJOR, all spec/served-surface, none a logic defect in the ladder); the build's CORE (F-11, KF, FK-B1, the prior NO-GO's two defects, currency, 20× concurrency) holds with controls. **Condition for the post-audit fix round: F-C11 (§5's prescribed spelling reddens a contract pin) must be settled BEFORE that round builds** (§VERDICT)
- **Graded:** HEAD `3e0553f` + patch `956e4136b403d061cf60603c53def3ef` (verified in the copy: `git diff --binary HEAD | md5sum`).
  HEAD-at-report: `db86ee0`. `3e0553f..db86ee0` is docs-only (lead reports, the blind-reader-3 report, am-37 §5 `ac60acd`
  and §6 `ea87b3c`). **am-37 §5 and §6 landed AFTER the patch and change the spec it is graded against** (§0).
- **deviations:** (1) FOCUS 7 (real prod-dump restore) NOT RUN — `scripts/restore_prod_dump.py` was
  permission-DENIED ("Modify Shared Resources"), not retried or worked around; operator decision (§7). (2) A plain
  source read of `keeps.py` / `principals.py` in my own scratch copy was denied by the same classifier, not worked around;
  the one finding that depended on it is graded PLAUSIBLE (§3 F-C7). (3) The concurrency driver is a28c's `cc18fd08…`
  with ONE changed line (the pytest invocation gains `uv run --with pytest-timeout … --timeout=300`, the per-run rule);
  its id set is byte-identical (§5).
- **Packages considered:** none — no mechanism specified; the probes reuse the SDK's own `parse_query_error` / `QueryDetailKind`.
- **Odoo-20 portability:** n/a.
- **Reuse ledger:** none (no production symbol introduced; probes are scratch instruments, §A).
- **Findings:** 0 BLOCKER · 4 MAJOR (F-C1 §5 delta absent · F-C2 `table_defined` · F-C3 mixed-owner label · F-C11 §5 spelling reddens a pin) · 7 MINOR (F-C4…F-C10) (§3). F-C1/F-C2/F-C3 are already FIX-IN-ROUND items of am-37 §5/§6
  (derived independently BEFORE I read §6 — §3 column "in am-37 §6?"); **F-C11 is NEW and gates the fix round.**
- **Confirmed (with controls):** F-11 live both ways, connection KEPT on the SAME client, hygienic message, own log
  event per path, transport control still drops; sharing by 3 mutations (call-site revert / `VALIDATION`→transport /
  helper body — both paths move). KF + 19 garbage-text-correct-kind cells with controls: every typed decision decides
  by kind; the only engine-text reader is `_classify_engine_error`, kind-gated per am-37 §1. FK-B1: the ONE mapping is
  behaviourally guarded (bypass → 52 reds, 8/8 declared); pin 1 is prose-satisfied (prose deletion → exactly it reds).
  D-2's ONE template proven shared by mutation over all three renderers. Focus-4 exact-set member diffs EMPTY both ways.
  20/20 consecutive GREEN (26 tests each: RS-2 8-way × 20, RS-5, keeps 8-way, `test_txn_contention.py`). F-1 fixed for the right reason: removing the pre-`preflight` gate reddens exactly the 2 declared pins (0 unexpected). Full suite (currency) **PASS, 0 RED_ORPHANED**, typecheck/pytest reds owned by 58 / 64b-i only, ruff GREEN.
- **decisions-needed:** (a) commit mechanics — the patch does NOT apply onto the main tree's working copy
  (`scripts/pending_contracts.yaml` conflicts with #486's uncommitted WIP); it applies cleanly with `--cached` (§1.3).
  (b) FOCUS 7 needs an operator grant (or an operator-run restore) — the #107-class dirty-store leg is unexecuted again
  (coldaudit-2 §5 hit the same wall). (c) The new MINORs not in am-37 §6 (§3 rows marked NEW) — route or accept. (d) **F-C11 fork, BEFORE the fix round
  builds:** the `==` spelling (pin-compatible) vs an allowlist row for typed-kind membership (a contract edit) — sidecar.
- **receipt pointers:** §1 gates (currency verbatim) · §2 FK-B1 · §3 findings · §4 KF/F-11 receipts · §5 concurrency ·
  §6 prior NO-GO · §7 dirty store · §8 served English · §9 DUAL · §10 residuals · §A instruments.

## §0 Capability check / what moved under me
- lore: registered `coldaudit-63c-i-a-3` (63c-20260924, auditor, ≤20m). `lore_index()` 21:50Z: root `/workspace` =
  the MAIN tree @ `db86ee0`, last_sync 92 s — it never indexes my scratch copies, so EVERY structural answer about the
  BUILD came from AST/awk over the copy (fallback said here; nothing to file — by design the index follows the main tree).
- grep/rg hook-blocked (#473; the hook also fires on the WORD inside a heredoc) → awk everywhere.
- **Spec drift during the audit:** `ac60acd` (am-37 §5: D-4 accepted; **D-5 → builder requirement `_CASCADE_KINDS =
  {NOT_EXECUTED, CANCELLED}`, "patch delta before commit"**) and `ea87b3c` (am-37 §6: blind-reader-3 triage, 8
  FIX-IN-ROUND). Both post-date the patch. "Later wins" ⇒ the graded patch cannot be committed as-is under the current
  spec, independent of anything I found.
- Instrument: `./scripts/scratch_copy.sh <sp>/audit` → `git reset --hard 3e0553f && git clean -fd` (status empty) →
  `git apply` → md5 `956e4136…` ✅ → `loremaster.__file__` = `<sp>/audit/loremaster/loremaster/__init__.py`. A second
  copy `<sp>/mut` (same recipe, same md5, `cp -a` content backup of `loremaster/loremaster` to `<sp>/mutbak`) carried
  every mutation; each mutation asserted its anchor occurred EXACTLY once (landing evidence) and was restored from the
  content backup with a byte-equality check (`filecmp.cmp(shallow=False)`); final md5 of `mut` re-verified `956e4136…`.

## §1 Gates — THE ONE full suite (the currency gate), in the `audit` copy
Admission: process table clear of any other full lore suite (contract-58-r4 ran TARGETED sets only — its command lines
name explicit files); `spike-surreal.service` active; MemAvailable gated ≥ 23 GiB by a waiter
(`run_full.sh`, §A) — admitted **21:39:32Z at 23 GiB**, md5 re-verified at admission.
Command: `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python scripts/pending_contract_gate.py --currency -- --maxprocesses=12`

Verbatim (the gate's own render; the pytest line's owner prose is long and is reproduced in full):
```
Running as unit: run-p2198490-i106979551.scope; invocation ID: 0e96aa472f4d4807ab58a84d173a0c5d
========================================================================
GATE CURRENCY — is every CLAIMED gate green, or owned?
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    RED_ADJUDICATED — 78 residual(s), owned by: packet-58-contract (owner: packet 58 (supersede re-anchor + task guarded-append shell + finding 130 + amendments 1-8) — the 58 builder, serial after 63c-i-a; trigger: the packet-58 build lands TaskLedger.max_reanchor_dependents, loremaster.tasks.SupersedeResult, TaskLedger._guarded_append_fragment, TaskLedger._reanchor_stragglers, loremaster.tasks.StragglerHealPackerError, loremaster.store._txn._ROLLBACK_LOG_TIERS and loremaster.store._txn.TxnCasLostError — then every file below stops erroring, this entry self-destructs and must be deleted with the build. ⚠ Two r3 leg families discharge on OTHER work, named so nobody reads their red as 58's — the TxnUniqueViolationError legs of test_reanchor_58_r3_tiers.py need 63c-i-a's am-33 build (serial BEFORE 58); the three test_reanchor_58_r3_cas_seam.py population rows for listed handlers outside 58 (floor_calibration record_measurement, keeps get_or_create_keyed, agents register) need a CAS_SEAM_DRIVERS entry in their OWNERS' test modules — the lead's routing (am-7 §3 item 2; REPORT-contract-58-r3.md FK-r3-4)) · packet-64b-i-contract (owner: packet 64b-i (the governed retrofit of lore_findings — substrate + write side + migrate) — the 64b-i builder; trigger: the 64b-i build + its §HELD (REPORT-contract-64b-r2.md, parts A/A2/B/C) land every symbol below (resource_from_row, classify_zero_row_cas, GovernedInvisible, GuardedPlan.guard/compose, authorize_guarded number=/projection=/target_scope=, guarded_write params=/target_scope=, FindingLedger.handle/audit_store/set_scope/report_system, the FK-1 `title`/`subject=` signatures, lorerunes.pdp.scope_shape_ok, server.GovernedVerbSpec/_requires_capability/_RETIRED_IDENTITY_ARGS_TEACHING, AppContext._resolve_identity + findings capability=/scope=, principals._migrate_finding_scope, the keep seam's principal_id= (list_keeps_for_member / resolve_visible_keeps), _finding_fakes.arm_finding_identity/armed_agent_row + the fake's subject=) and every file registered below goes GREEN — then this entry self-destructs and is deleted with the build (⚠ deleting it turns test_findings_closeout_64b's MP-9 alias pin RED until the contract's Any reach-arounds are rewritten as typed calls — packet-64 amendment 10 FK-r2-10 — NO close-out bound exists; the rewrite + this entry's deletion are ONE sequenced close-out commit INSIDE the 64b-i build wave, before its currency run))
  ruff         GREEN
  pytest       RED_ADJUDICATED — 504 residual(s), owned by: packet-58-contract (owner: packet 58 (supersede re-anchor + task guarded-append shell + finding 130 + amendments 1-8) — the 58 builder, serial after 63c-i-a; trigger: the packet-58 build lands TaskLedger.max_reanchor_dependents, loremaster.tasks.SupersedeResult, TaskLedger._guarded_append_fragment, TaskLedger._reanchor_stragglers, loremaster.tasks.StragglerHealPackerError, loremaster.store._txn._ROLLBACK_LOG_TIERS and loremaster.store._txn.TxnCasLostError — then every file below stops erroring, this entry self-destructs and must be deleted with the build. ⚠ Two r3 leg families discharge on OTHER work, named so nobody reads their red as 58's — the TxnUniqueViolationError legs of test_reanchor_58_r3_tiers.py need 63c-i-a's am-33 build (serial BEFORE 58); the three test_reanchor_58_r3_cas_seam.py population rows for listed handlers outside 58 (floor_calibration record_measurement, keeps get_or_create_keyed, agents register) need a CAS_SEAM_DRIVERS entry in their OWNERS' test modules — the lead's routing (am-7 §3 item 2; REPORT-contract-58-r3.md FK-r3-4)) · packet-64b-i-contract (owner: packet 64b-i (the governed retrofit of lore_findings — substrate + write side + migrate) — the 64b-i builder; trigger: the 64b-i build + its §HELD (REPORT-contract-64b-r2.md, parts A/A2/B/C) land every symbol below (resource_from_row, classify_zero_row_cas, GovernedInvisible, GuardedPlan.guard/compose, authorize_guarded number=/projection=/target_scope=, guarded_write params=/target_scope=, FindingLedger.handle/audit_store/set_scope/report_system, the FK-1 `title`/`subject=` signatures, lorerunes.pdp.scope_shape_ok, server.GovernedVerbSpec/_requires_capability/_RETIRED_IDENTITY_ARGS_TEACHING, AppContext._resolve_identity + findings capability=/scope=, principals._migrate_finding_scope, the keep seam's principal_id= (list_keeps_for_member / resolve_visible_keeps), _finding_fakes.arm_finding_identity/armed_agent_row + the fake's subject=) and every file registered below goes GREEN — then this entry self-destructs and is deleted with the build (⚠ deleting it turns test_findings_closeout_64b's MP-9 alias pin RED until the contract's Any reach-arounds are rewritten as typed calls — packet-64 amendment 10 FK-r2-10 — NO close-out bound exists; the rewrite + this entry's deletion are ONE sequenced close-out commit INSIDE the 64b-i build wave, before its currency run))
CURRENCY   : PASS — every claimed gate is GREEN or OWNED
  (this is NOT the deploy receipt: it answers 'is every gate owned', never 'may this ship')
EXIT=0 2026-09-29T21:57:48Z
```
- **0 RED_ORPHANED.** RED_ADJUDICATED owners, exhaustively: typecheck → `packet-58-contract` only (78); pytest →
  `packet-58-contract` · `packet-64b-i-contract` (504 in all). **No `packet-63c-i-a-*` entry exists** (the patch deletes
  it); the string `63c-i-a` appears 4× in the log, all INSIDE 58's owner prose (its r3 legs' discharge note). ruff GREEN.
- **No cap kill** (exit 0, 21:39:32Z → 21:57:48Z, 18m16s, `--maxprocesses=12`, one scope `MemoryMax=16G`). No #486
  escape surfaced as an unowned red.
- ⚠ **Bound, stated:** the gate prints NO passed-count and keeps its junit in a temp dir it deletes
  (`/var/tmp/tmp320jcs_i/` — gone at 21:58Z), so this receipt carries the partition, not a passed/failed tally. I did
  not re-run the full suite to get one (ONE full suite per packet). And RED_ADJUDICATED is FILE-granular: a
  build-caused red inside a 58/64b-owned file would be masked (am-37 §2's accepted F-15 class). Mitigation actually
  run: my targeted control over a28/a28b/a28c/`test_surreal_store` = **688 passed / 0 failed** (§2), and the builder's
  first-failure-line comparison of its 331 owned reds (not re-derived by me).

### §1.3 Commit mechanics (read-only checks against the MAIN tree)
- `git apply --check <patch>` in the main tree → **`error: patch failed: scripts/pending_contracts.yaml:264` /
  `patch does not apply`** — #486's uncommitted WIP edits the same region.
- `git apply --check --exclude=scripts/pending_contracts.yaml <patch>` → exit 0 (the §HELD `test_surreal_harness.py`
  hunk applies on top of #486's WIP).
- `git apply --check --cached <patch>` → exit 0 (index-only apply against HEAD is clean).
- ⇒ the lead must commit via the index (and hand-merge the yaml block deletion into #486's WIP) or the fix round must
  re-base its patch on the then-current tree. Not a code defect; a landing hazard (a naive apply fails loudly, a
  `--reject`/manual merge could silently keep the retired registry block alive → a masked `RED_ORPHANED`).

## §2 FK-B1 — CODE or PROSE? (brief focus 1)
**Verdict: the PROPERTY ("every domain raise on the ladder builds through `_domain_rejection_error`") is guarded by
BEHAVIOURAL pins; pin 1 (`test_both_domain_raise_sites_build_their_rejection_via_the_one_mapping_helper`) is pure
decoration — it fails a prose deletion and passes a real bypass. Reading A is sound; pin 1's re-key on am-37 §W row 4
stands. No MAJOR.**
- **(a) mutation `helper_bypasses_mapping`** (`_raise_attempt_failure` raises `TxnDomainRejectionError(msg)` directly —
  md5 `5a72a8e3…` → `7e15e189…`). Declared BEFORE the run from `--collect-only` (688 collected over a28 / a28b / a28c /
  `test_surreal_store`; declared file md5 `3ea3c31b…`, 8 ids: a28b am32_1_3_ab `[record-id-collision|unique-index-
  collision]-run_query`, a28b am32_1_3_c `[Record-*]` ×2, a28c am35_2_4 `run_query` ×2, a28 RS5 ×2). Control run
  (unmutated) **688 passed / 0 failed**; mutant **636 passed / 52 failed**. **Declared ∩ reddened 8/8; declared-but-
  GREEN 0; unexpected 44** — all `run_query` legs of the same class property (a28c KB `unique-echoes-*-run_query`,
  am36_1_2 echo matrix `*-run_query` ×36, KA `[run_query]`, a28b K7, a28c FK_r3_4 `[agents.py::register]`). Pin 1
  stayed GREEN under the bypass. Restored, cmp-equal.
- **(b) mutation `delete_run_query_prose`** (the 4-line comment in `run_query` deleted, code untouched — md5 →
  `9298097f…`). Declared: exactly pin 1. `test_surreal_store.py`: **187 passed / 1 failed; declared 1/1, unexpected 0.**
  Restored, cmp-equal.
- **(c) the `last_conflict_cause` comment (pin 2) — TRUE of the code, with one over-generalisation.** AST over the
  build: `RetryableConflictSignal` raise sites = `_raise_attempt_failure` (chained `from error`, NOT lexically in a
  handler), `_run_verified_transaction._attempt` (bare — the named exception), and the three `bootstrap_session`
  closures (in `except`). `_raise_attempt_failure` has exactly TWO call sites, both lexically inside an `except`
  (`run_query._attempt`, `_txn_query_raw`). So "called ONLY from one [handler], with the caught exception as its
  `error` argument, and it chains `from error` itself" is TRUE. The clause "The single-statement seams … raise it
  through `_raise_attempt_failure`" over-reaches: `scout._scout_query_once` and `inbox_awaiter`'s three `_attempt`s raise
  the signal from their OWN handlers (via the shared `is_retryable_conflict_error` — sharing, not a ladder copy: they
  deliberately propagate everything else raw). MINOR prose (F-C9).

## §3 Findings
| # | sev | finding | receipt | in am-37 §6? |
|---|---|---|---|---|
| F-C1 | **MAJOR (spec)** | The graded patch does not implement am-37 §5's builder requirement (`_CASCADE_KINDS = {NOT_EXECUTED, CANCELLED}`): the degenerate all-cascade list `[Cancelled, NotExecuted-COMMIT]` selects index 0 — a FALSE root cause, served as "statement 1 of N was rejected", contradicting `_domain_root_cause`'s own docstring ("degrades to the LAST entry"). | §4.2 cells D-5: patch → `(False, 0)`; patch + the §5 delta (in `mut`) → `(False, 1)`; non-degenerate measured shape `[NotExec, offender, Cancelled, NotExec]` → 1 on both; `TimedOut` → 0 (substantive) on both. Delta over the FK-B1 set (688): **687 passed / 1 failed** — the one red is F-C11 | yes — §5 (F-6) |
| F-C2 | **MAJOR (spec)** | `MigrateGovernedResult.table_defined` defaults to `True`; every refusal / not-supported path AFTER `INFO FOR DB` keeps the default, so a refusal serves `table_defined=True` for a target INFO FOR DB measured ABSENT — violating am-36 FK-4 ("`False`/`True` where `INFO FOR DB` ran"). No renderer reads it on a refusal today (the CLI checks `refused` first), so the harm is a false typed field, not false prose. | §8 leg 1, live :18000: `memory` UNDEFINED → `refused=True table_defined=True`; CONTROL `memory` defined → `True`. One-line derivation (`table_defined=table in preconditions.defined_tables` at the final assembly) → UNDEFINED `False`, control `True` (scratch, restored). | yes — M-2 (their fix: no default + ONE assembly point — agree, it closes the CLASS) |
| F-C3 | **MAJOR (served English, Leg 1)** | The `mixed` owner sentence labels the TOTAL as "other principal(s)": `"… AND by other principal(s): 4 distinct owner(s) (first 3 named: …)"` where the others number 3 (the operator is inside the 4). A consumer reading "other principals: 4" is wrong by one. | §8 leg 2, live: direct SELECT `distinct_owners=4` = served `distinct_owner_principals=4`; the named others are 3. | yes — F-9 |
| F-C11 | **MAJOR (fix-round STOP)** | am-37 §5's prescribed spelling `_detail_kind(failed.typed) in _CASCADE_KINDS` reddens the a28c text-reader exact-set pin (`unlisted: ['_is_domain_cascade_notice']`); §5 checked only by-name references. An `==` spelling over the SDK constants passes (33/33) and still fixes the degenerate case. | `mut`: §5 spelling → FK-B1 set 687 passed / 1 failed (that pin, `AssertionError … not allowlisted: ['_is_domain_cascade_notice'] … compare it with ==`); `==` spelling → pin class 33 passed, `probe_kf` D-5 degenerate → `(False, 1)`, FAILS `[]`; both restored cmp-equal | **NEW** (contradicts §5's "the rename is free") |
| F-C4 | MINOR | Stored ids render through `sanitise_line` (newline flattened — no forged row line), but a raw triple-backtick run survives into the refusal reason, in BOTH the owner list and `_id_sample`. Pre-existing at HEAD (same sanitiser, same sites). | §8 leg 3: `newline_in_reason=False`; reason contains `principal:⟨h - #999 FORGED row \`x\` \`\`\`⟩`. | **NEW** |
| F-C5 | MINOR (landing) | The patch does not apply onto the main tree (yaml vs #486 WIP) — §1.3. | §1.3 | **NEW** |
| F-C6 | MINOR (test hygiene) | FK-B1 pin 1 is decoration (fails on prose deletion, passes on a real bypass) — already routed to am-37 §W row 4. | §2 (a)(b) | ruled (§5 FK-B1 concur) |
| F-C7 | MINOR, **PLAUSIBLE** | `KeepStore.get_or_create_keyed`'s docstring still says `Raises: KeepStoreError: … OR the store rejected the create`, but the narrowed CAS (`except TxnUniqueViolationError:` only) lets every other domain rejection of the CREATE propagate as `TxnDomainRejectionError`. Read from the patch's diff context only; a direct re-read was permission-denied (§0), so not confirmed against the full body. | patch hunk `keeps.py @@ -560`: the Raises line is unchanged context; hunk `@@ -614`: the old `except SurrealStoreError:` handler replaced by `except TxnUniqueViolationError:` | **NEW** |
| F-C8 | MINOR | `_failed_statements` now calls `parse_query_error` on every ERR dict carrying `kind`: a malformed `cause` (parsed by `parse_rpc_error`) would raise an arbitrary SDK exception out of the verdict path instead of a classified rollback. Engine-shaped, unobserved on 3.2.4. | SDK `errors.py::parse_query_error` (read, installed 2.0.0) | adjacent to F-14 (residual) |
| F-C9 | MINOR (prose) | the `last_conflict_cause` comment over-generalises "the single-statement seams" (§2 c). | §2 (c) | **NEW** |
| F-C10 | MINOR (pre-existing) | fate-1 `SurrealConnectionError` messages still interpolate `{error}` — for a transport error that is SDK/socket text (and, under a transport-kind `ServerError`, engine text). Unchanged by the patch; noted because F-11 made the DOMAIN branch hygienic and the transport branch was not re-examined. | §4.1 revert leg shows the old echo shape | **NEW** (pre-existing) |

Class lifts (Fix-the-CLASS rule 1): F-C2 → *every result field is DERIVED from the measurement on every path; no field
carries a measured-looking default* (domain: `dataclasses.fields(MigrateGovernedResult)` × every construction site;
M-2's no-default fix enforces it at the type). F-C3 → *every served integer's label names the set it counts* (Leg-1
scope diff). F-C1 → *the cascade set is adjudicated over the SDK's `QueryDetailKind` members* (§W row 4's generated
pin). F-C4 → *a stored id rendered into served prose passes ONE sanitiser that neutralises newlines AND fence runs*.

## §4 KF / F-11 receipts (with controls)
### §4.1 F-11 live (`probe_f11.py`, §A; spike-surreal 3.2.4, minted DB `coldaudit63c/f11_*`, removed + proven gone)
REAL connection objects; after each failure the SAME client object runs `RETURN 1`; the statement embeds
`SECRET_c0ld4ud1t_VALUE`; log records captured.
```
BUILD (audit copy)
[run_query] parse-error: TxnDomainRejectionError drops=0 secret_in_message=False message="SurrealDB probe query rejected against 'ws://127.0.0.1:18000/rpc' (query too complex — reduce or shorten the search terms); see the server log for the full engine detail"
[run_query] parse-error: log events(>=WARNING)=[('probe.seam', 'probe.rejected')]
[run_query] parse-error: same-client next call -> 1 (KEPT)
[run_query] throw-echo: TxnDomainRejectionError drops=0 secret_in_message=False message="… (unspecified rejection); see the server log …"
[run_query] CONTROL closed-socket: SurrealConnectionError drops=1
[execute_transaction] parse-error: TxnDomainRejectionError drops=0 secret_in_message=False message="SurrealDB transaction rejected against 'ws://127.0.0.1:18000/rpc' (query too complex — reduce or shorten the search terms); see the server log for the full engine detail"
[execute_transaction] parse-error: log events(>=WARNING)=[('loremaster.store._txn', 'store.transaction.rejected')]
[execute_transaction] parse-error: same-client next call -> 1 (KEPT)
[execute_transaction] throw-echo: TxnDomainRejectionError drops=0 … 'statement 2 of 3 was rejected (unspecified rejection)…'
[execute_transaction] CONTROL closed-socket: SurrealConnectionError drops=1
teardown: db still listed = False
```
The echoed "…can be retried" THROW is served `unspecified rejection` on the first attempt on both paths (no ~2 s retry storm).
**Sharing by MUTATION** (`mut` copy, restored cmp-equal after each; md5 `5a72a8e3…` = backup):
| mutation | run_query parse-error | execute_transaction parse-error |
|---|---|---|
| none (build) | TxnDomainRejectionError, drops=0, "(query too complex …)" | same |
| `revert_txn_call_site` (am-37 §3.4 control: `_txn_query_raw` back to drop + raise) | unchanged | **SurrealConnectionError drops=1**, message echoes the engine text `Parse error: Exceeded expression recursion depth limit --> [2:1033] …` |
| `validation_is_transport` (`ErrorKind.VALIDATION` into `_CONNECTION_ERROR_KINDS`) | **SurrealConnectionError drops=1** | **SurrealConnectionError drops=1** |
| `helper_label_unspecified` (helper body: `error_class = _ERROR_CLASS_UNSPECIFIED`) | **(unspecified rejection)** | **(unspecified rejection)** |
Limit of my own instrument, stated: the drop spy RECORDS drops but does not close the socket, so "same-client next
call" proves KEPT only in combination with `drops=0` (in the revert leg the spy recorded the drop yet the client still
answered — that leg's KEPT line is an artefact of the spy, not of the code).
**`server.py`'s "ABORTED — store connection lost; retry these"** (both sites in the findings batch verb): reachable only
from `except SurrealConnectionError`. A parse error now raises `TxnDomainRejectionError` (MRO: TxnDomainRejectionError →
SurrealStoreError → RuntimeError; `issubclass(…, SurrealConnectionError) = False` for it and both subclasses), caught by
the handler's `except SurrealStoreError` → per-item `FAILED — <hygienic label>` and the batch CONTINUES on the healthy
connection. The false ABORTED teaching is unreachable for a parse error. ✅

### §4.2 KF + garbage-text-correct-kind cells (`probe_kf.py`, §A; store-free; exit 0)
Garbage = `"zq xv plmf 0x7e wok"` (no engine words). Every cell has a CONTROL that would pass a text-deciding build.
```
PASS txn-retry garbage-text + TransactionConflict: (True, 0)            PASS txn-retry CONTROL garbage-text no details: False
PASS txn-retry HOSTILE 'can be retried' text, kind Internal: False
PASS rq-retry garbage-text + TransactionConflict: True                   PASS rq-retry CONTROL garbage-text NotExecuted: False
PASS rq-retry HOSTILE text 'can be retried' kind Thrown: False
PASS cascade garbage-text NotExecuted around substantive -> root 1       PASS cascade CONTROL same text, no details -> root 0
PASS KF adversary reworded -> root 1                                     PASS KF adversary reworded -> governed class
PASS record garbage-text + Record details -> unique                      PASS record CONTROL Table details -> unspecified
PASS record HOSTILE record text, kind Query -> unspecified               PASS txn record garbage-text -> TxnUniqueViolationError
PASS allowlist: kind {Query, NotFound, NotAllowed, Serialization, Configuration} hostile text -> unspecified (×5)
D-4 empty-text substantive + COMMIT notice -> root (False, 0) label unspecified rejection
D-5 degenerate all-cascade [Cancelled, NotExecuted] -> root (False, 0)   (patch)   | (False, 1) with the am-37 §5 delta
D-5 measured shape [NotExec, offender, Cancelled, NotExec] -> root (False, 1)      (both)
TimedOut + COMMIT -> root (False, 0)                                     (both — substantive, as §5 rules)
```
**Text census (`text_census.py`, AST, spelling-blind over `Compare(In/NotIn/str-Eq)` + str/regex method calls):** the
engine-text tests in `_txn` are ALL inside `_classify_engine_error` (l.701–713: the governed prefix gated on
`untyped or kind == THROWN`; U-prefix/ASSERT/coercion gated on `untyped or kind == INTERNAL`; recursion gated on
`untyped or kind == VALIDATION`). The other hits read OUR statement envelope (`_normalise_statement`,
`_assert_envelope_integrity`), param keys (`compose`) or `error.kind` membership (`is_connection_error`). No decision
reads engine text outside the am-37 §1 allowlist. The contract's own derivation (`_engine_text_readers()`) returns the
same four functions = its allowlist (§4.3).
**D-4 verdict** (spec-silent at build time, ACCEPTED by am-37 §5): severity **none/MINOR** — the empty-text substantive
entry is now selected and classified by its kind (`unspecified rejection`, loud); the only change is which entry the
rollback LOG names. Recommendation: accept (as ruled). **D-5 verdict:** see F-C1 — MAJOR by spec (a served false root
cause on a degenerate, unobserved shape); the §5 delta fixes it (§4.2) — but its prescribed spelling reddens a pin (F-C11).

### §4.3 Focus 4 — exact-set pins, MEMBER diff (not colour), computed by calling each pin's own derivation at the build
```
GUARDED-CAS doors  found-only: []  expected-only: []  |found|= 6
TYPED-CAS catches  found: ['agents.py::register::1', 'keeps.py::get_or_create_keyed::1']  expected: [same]
TEXT READERS found: ['_assert_envelope_integrity', '_classify_engine_error', 'compose', 'is_connection_error']  allowlist: [same]  unlisted: []
FATES evidence-less: [8 rows]  pinned UNLOGGED: [the same 8 rows]
```
Every member diff EMPTY both ways; no second door found late (am-37 §2 rider 1). Colour at the build: **GREEN, derived** — `test_retry_seam.py` (door index), `test_fixwave_a28c_63c_i_a.py` (text-reader exact set), `test_exhaustion_fates.py` (fates) and a28/a28b are named by NEITHER registry entry (`scripts/pending_contracts.yaml` in the copy: 58 owns l.92–145, 64b-i owns l.176–256 — none of these paths), so any red in them would be RED_ORPHANED; the gate returned 0 orphaned ⇒ every one is GREEN at the build.

## §5 Concurrency — 20 consecutive (store-ref §5)
`systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 bash conc20_audit.sh <mut> 20 26` (26 collected by
`--collect-only` first; the `mut` copy re-verified md5 `956e4136…` before and after), 21:57:49Z → 22:01:51Z, run AFTER
the full suite (MemAvailable 24 GiB):
```
run 1: exit=0 :: 26 passed in 12.39s     run 11: exit=0 :: 26 passed in 10.92s
run 2: exit=0 :: 26 passed in 12.38s     run 12: exit=0 :: 26 passed in 11.00s
run 3: exit=0 :: 26 passed in 11.39s     run 13: exit=0 :: 26 passed in 10.66s
run 4: exit=0 :: 26 passed in 11.19s     run 14: exit=0 :: 26 passed in 11.85s
run 5: exit=0 :: 26 passed in 11.47s     run 15: exit=0 :: 26 passed in 10.94s
run 6: exit=0 :: 26 passed in 10.87s     run 16: exit=0 :: 26 passed in 10.74s
run 7: exit=0 :: 26 passed in 11.05s     run 17: exit=0 :: 26 passed in 10.90s
run 8: exit=0 :: 26 passed in 11.00s     run 18: exit=0 :: 26 passed in 10.58s
run 9: exit=0 :: 26 passed in 10.50s     run 19: exit=0 :: 26 passed in 10.00s
run 10: exit=0 :: 26 passed in 10.59s    run 20: exit=0 :: 26 passed in 11.10s
ALL 20 CONSECUTIVE GREEN
```
Driver diff vs a28c's `cc18fd08…` (one line): `.venv/bin/python -m pytest -q -p no:cacheprovider -n 4 -rfE` →
`uv run --with pytest-timeout pytest --timeout=300 -q -p no:cacheprovider -n 4 -rfE`; the four ids are unchanged.

## §6 The prior NO-GO's defects (`REPORT-coldaudit-63c-i-a-2.md`)
- **F-2 BLOCKER (race compensation strands winners) — FIXED by removal, for the right reason.** The compensation
  (`delete_keep` on a refused register, the ALSO-line, `comms.register.compensation_failed`) and its plumbing
  (`minted_by_this_call`, `_MINTED_BY_THIS_CALL`) are deleted (am-28 §F-1); awk over `loremaster/loremaster`: no
  `delete_keep` call in the register handler, `minted_by_this_call` 0 hits. The winners' keep can no longer be deleted
  by a loser. Stress: RS-2 8-way × 20 rounds in the 20× run (§5).
- **F-1 MAJOR (preflight before SF-63-1 leaks role / spawned_by / retired to a foreign principal) — FIXED.** The register
  handler now runs a READ-ONLY gate on an EXISTING session keep (`get_by_key` → `_sf_63_1_gate`) BEFORE `preflight`,
  then the mint, then the gate AGAIN on the keep the mint returned. **Control by mutation** (`f1` in `mut`: the
  pre-preflight gate replaced by `pass`; declared from `--collect-only` BEFORE the run — md5 `fa928567…`, 2 ids:
  `test_RS3_every_foreign_probe_is_the_same_denial_with_zero_registry_reads`,
  `test_the_handler_ORDER_is_gate_then_preflight_then_mint_then_register`; expected GREEN: the CONTROLS and POST_MINT
  legs): mutant `test_fixwave_a28_63c_i_a.py` **91 passed / 2 failed of 93**
(control, same file inside the 688-test control run: all passed); **declared ∩ reddened 2/2; unexpected 0;** the
CONTROLS leg (a householded member proceeds, the keeper is still taught) and the POST_MINT re-check stayed GREEN.
Restored cmp-equal; `mut` md5 back to `956e4136…`. ✅ The leak pins see the gate, and only the gate.
- **am-27/28 items:** F-3/F-4 (INFO FOR DB / non-list reads fail closed) — present in the diff (`_governed_select`,
  `_agent_migration_preconditions` raise `SurrealStoreError`); their CLI escape is am-37 §6 F-12 (FIX-IN-ROUND).
  F-5 (`#4b` on any delete exception) — moot (the delete is gone). A4 docstring — the a28 pin (full suite).

## §7 FOCUS 7 — a REAL dirty store (#107 class): NOT RUN (blocked)
`uv run python scripts/restore_prod_dump.py --dump /backups/lore/lore-prod-20260803T141930Z.surql` was DENIED by the
permission layer ("Modify Shared Resources"). Not retried, not worked around. coldaudit-2 §5 hit the same wall, so the
real-dump leg is unexecuted in both of the last two audits. What partially stands in for it (NOT a substitute):
my served-English probe (§8) writes legacy-shaped `agent` rows (owner, no scope; hostile ids) into a minted DB under a
SCHEMALESS table BEFORE running `migrate_governed`, and compares every served count to a direct SELECT (4/4/4 exact).
**Decision needed (operator):** grant the restore (it binds :18000 only, mints and reaps `test_dump_*`), or run it and
hand the auditor the `LORE_PROD_DUMP_DB=` name.

## §8 Served English / the consumer law (`probe_served.py`, `probe_d2.py`, §A; live :18000, minted DBs, removed)
- **Leg 1 (`table_defined`)** — F-C2.
- **Counts vs direct SELECT** (legacy agents a1/a2/a3/hostile; principals p1 admin, p2, p3):
  `[direct SELECT] unscoped=4 owned_unscoped=4 distinct_owners=4` ↔ served `unscoped_agents=4
  owned_but_unscoped_agents=4 scoped_but_ownerless_agents=0 dangling_sender_messages=None owned_but_unscoped_messages=None
  scoped_but_ownerless_messages=None distinct_owner_principals=4 owner_classification='mixed' total_principals=3
  admin_principals=1`. Every integer TRUE; the three message counts are `None` because the message read never ran
  (target `memory`) — FK-a holds.
- **Reason verbatim:** `'4 agent row(s) carry an owner but no scope (§2.1). They are owned by the operator — registered
  by a pkt-62–63b image; see amendment-1 E3 — AND by other principal(s): 4 distinct owner(s) (first 3 named:
  principal:p2, principal:p3, principal:⟨h - #999 FORGED row `x` ```⟩). First 4 of 4 ids shown: agent:a1, agent:a2,
  agent:a3, agent:⟨h - #999 FORGED row `x` ```⟩. (The store holds 4 agent row(s) with no scope in total.) Adjudicate
  these rows by hand before migrating ANY governed table; no row was stamped'` → F-C3, F-C4.
- **D-2 — the ONE `_operator_unresolved_sentence` template, shared by MUTATION.** Principals: 2 admins + 1 member
  (unresolvable). Three renderers: the verb-level refusal (owned-unscoped rows), the `memory` leg's refusal (no problem
  rows), and the out-of-verb fallback (`_operator_unresolved` called directly). Pristine: all three `(3 principals, 2
  admins)`, the leg's typed fields `3 2`. Mutation (the template's two slots swapped, md5 `405b8bb4…` → `0a3ec1f5…`): all
  three render `(2 principals, 3 admins)`; the typed fields stay `3 2`. Restored cmp-equal. ✅ ONE template, three callers.

## §9 The DUAL — my enumeration FIRST (from the diff, before opening the builder's §DUAL), then the diff
Mine (M1–M24):
| # | removed / replaced | builder row | my adjudication |
|---|---|---|---|
| M1 | retry decision: "can be retried" text → typed `TransactionConflict`, both paths (incl. bootstrap closures, scout, inbox_awaiter via the shared predicate) | 1 | preserved-with-pin (garbage-text cells §4.2) |
| M2 | cascade text markers → typed `NotExecuted` only | 2 | **§5 delta owed** (F-C1) |
| M3 | empty-text skip in `_domain_root_cause` | 2a | accepted (am-37 §5) |
| M4 | classifier: flat text ladder over any kind → kind-gated; governed marker anywhere → anchored at the THROW prefix | 3 | preserved-with-pin (am-35 §2 / am-37 §1) |
| M5 | `run_query` inline ladder → `_raise_attempt_failure` | 4 | preserved (F-11 mutations §4.1) |
| M6 | `_txn_query_raw`: every error → drop + transport, echoing `{error}` | 5 | dropped-deliberately am-37 §3 (live §4.1) |
| M7 | `_domain_rejection_error` gains the unique mapping (subclass — old `except`s still catch) | — (in §1) | ruled am-32/33 |
| M8 | NEW failure surface: `parse_query_error` per failed statement | — | **F-C8** (MINOR) |
| M9 | keeps CAS: `except SurrealStoreError` (minus transport/exhaustion) → `except TxnUniqueViolationError` | 6 | ruled; docstring drift F-C7 (PLAUSIBLE) |
| M10 | `minted_by_this_call` + flag deleted | 7 | dropped-deliberately am-28 |
| M11 | compensation + ALSO-line + log deleted | 8 | dropped-deliberately am-28 (am-37 §6 F-16 residual) |
| M12 | handler order → gate(read-only) → preflight → mint → gate | 9 | ruled am-28 §F-2 (control §6) |
| M13 | `keep_store is None` refusal moved BEFORE `preflight` | — | improvement (no registry read without a keep store) — not listed by the builder |
| M14 | `AgentRegistry.register` CREATE collision → re-read + recursive re-register | 10 | ruled am-29/32; recursion bound is am-37 §6 F-13 residual |
| M15 | memory/agent `backfilled` pre-count → UPDATE's own return | 11 | ruled |
| M16 | `_governed_select` non-list / `INFO FOR DB` non-dict → raise | 12 | ruled; CLI escape am-37 §6 F-12 |
| M17 | message backfill gains the sender-soundness clause | 13 | ruled F-7; silent-fate hole am-37 §6 F-10 |
| M18 | message ORDER refusal folded into `_message_leg_refusal` | 14 | ruled |
| M19 | `_owned_unscoped_part`: per-owner ROW counts ("N of them are owned by the operator", "M are owned by K others") dropped | 15 | ruled am-31/34 — but the new mixed sentence mislabels its total (F-C3) |
| M20 | unresolved-operator sentence: counts from the ONE resolution record, not a re-listing | 16 | ruled FK-8 (mutation §8) |
| M21 | verb-level refusal gains the message problem parts + "(The store holds N agent row(s) with no scope in total.)" | — | ruled am-32 §2.1; count TRUE (§8) — not listed as a replacement by the builder |
| M22 | undefined `--table` target: the leg no longer runs; typed "not defined" answer + CLI line | — (§1 only) | ruled am-34 F-5 |
| M23 | `table_defined` on the invalid-table refusal → `None` | 17 | ruled — **but every OTHER refusal keeps the `True` default** (F-C2), which the builder's row does not mention |
| M24 | `_verb_level_refusal` resolves the operator a SECOND time (after `_measured_counts`) | — | cost only; both resolutions write the same record |
**Diff:** the builder's 17 rows ⊂ mine except its 2b (Cancelled) = my M2. Mine NOT in the builder's inventory: M8,
M13, M21, M22 (as a replaced behaviour), M24, and M23's other-refusal half (the defect).

## §10 RESIDUALS (each with its own verdict)
| # | residual | verdict |
|---|---|---|
| R-1 | Focus 7 real-dump leg unexecuted (permission) | OPEN — operator decision (§7) |
| R-2 | FK-B1 pin 1 decoration | routed — am-37 §W row 4 (AST re-key) |
| R-3 | F-C4 backtick run through `sanitise_line` (pre-existing) | route to the sanitiser owner (finding #34's promotion) |
| R-4 | F-C5 landing hazard (yaml vs #486 WIP) | lead — at commit time |
| R-5 | F-C7 keeps `Raises:` docstring (PLAUSIBLE) | fix-round candidate — re-read by the fix round's auditor |
| R-6 | F-C8 `parse_query_error` exception surface | residual with am-37 §6 F-14 (same trigger: a malformed/kindless entry observed) |
| R-7 | F-C9 `last_conflict_cause` over-generalisation | fix-round prose (one clause) |
| R-8 | F-C10 transport message echoes `{error}` (pre-existing) | route — needs its own ruling (is a transport-kind ServerError's text hygienic?) |
| R-9 | my F-11 drop spy does not close the socket (§4.1) | instrument bound, stated; the claim rests on `drops=0` |
| R-10 | the full suite ran while contract-58-r4 ran targeted sets and while my own targeted mutation runs ran (never another FULL suite) | stated; any red is re-attributed in §1 |

## §A Instruments (in `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/fab8f141-ab2b-43bd-8415-ed272fcec1ea/scratchpad/`)
`run_full.sh` (admission-gated currency launcher) · `queue.sh` (post-suite targeted queue) · `probe_f11.py` ·
`probe_kf.py` · `probe_served.py` · `probe_d2.py` · `text_census.py` · `mutate.py` / `mutfile.py` (exact-anchor,
count==1, cmp restore) · `junit_diff.py` (declared set diffed both ways) · `conc20_audit.sh` (a28c `cc18fd08…` + the
timeout line) · declared sets `fkb1_declared_red_a.txt` (md5 `3ea3c31b…`), `fkb1_declared_red_b.txt`,
`f1_declared_red.txt` (md5 `fa928567…`), `d5_declared_red.txt` (empty: the delta must redden NOTHING).
⚠ The scratchpad is session-local; the lead should copy what it wants to keep into the receipts dir at close-out.

## VERDICT
**NO-GO for `3e0553f` + patch `956e4136…` as-is.** Not because the ladder is wrong — every piece of the core
this packet exists to build held under construction, with controls: F-11 (one ladder, live both ways, three sharing
mutations), the typed decisions (19 garbage-text cells + KF), FK-B1's ONE mapping (52-red bypass), the prior NO-GO's
F-2/F-1 (removal + a 2/2 gate-control mutation), 20/20 concurrency, CURRENCY PASS with 0 RED_ORPHANED. It is NO-GO
because the spec moved after the patch was cut, and the patch does not meet it:
1. **F-C1** — am-37 §5's "patch delta before commit" (`_CASCADE_KINDS`) is absent (degenerate root cause is false).
2. **F-C2** — am-36 FK-4 violated: `table_defined=True` served for a target `INFO FOR DB` measured absent (live).
3. **F-C3** — the mixed-owner sentence labels its total as "other principal(s)" (live, one over).
4. **F-C11 (NEW, for the fix round, a STOP by am-37 §6's own rule):** §5's prescribed SPELLING
   `_detail_kind(failed.typed) in _CASCADE_KINDS` reddens `test_fixwave_a28c_63c_i_a.py::TestTheEngineTextReadersAre…
   ::test_am36_1_2_3_the_only_engine_text_reader_is_the_classifier` (`unlisted: ['_is_domain_cascade_notice']`) — §5's
   "no pin mutates `_CASCADE_KIND` by name (awk: zero hits)" checked NAMES, not the spelling-derivation pin. Verified
   both ways in `mut`: the `in` spelling → 687/1 over the FK-B1 set (only that pin); an `==` spelling over the SDK's two
   constants (`kind == QueryDetailKind.NOT_EXECUTED or kind == QueryDetailKind.CANCELLED`) → the pin class 33/33 GREEN
   and the degenerate cell → LAST. Fork for the sidecar/lead before the fix round builds: (a) the `==` spelling
   (pin-compatible, no contract edit; the constant becomes a documented tuple beside it), or (b) an allowlist row for
   typed-kind membership (a contract edit — the same shape `is_connection_error` already holds). **CLASS:** a ruling that
   prescribes a code SPELLING must be checked against every pin that derives over spellings, not only a by-name sweep —
   the instrument lesson's name-keyed check, inside the ruling.
Items 1–3 are already FIX-IN-ROUND in am-37 §5/§6 (derived independently here before reading §6); F-C11 and the
MINORs marked NEW are not. The post-audit fix round's cold audit should re-run: the KF/garbage-text probe, the F-11
probe + three mutations, `probe_served.py` (legs 1–3), the D-2 mutation, and the a28c text-reader pin. Focus 7 (the real
dirty store) remains unexecuted pending an operator grant.
