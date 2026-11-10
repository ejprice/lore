brief-base v16 read · brief project v7 read

# REPORT — adversary-58-r2 (contract-adversary, DELTA pass: packet 58 contract r2 @ `c42eeaf`)

## SUMMARY BLOCK
- **State: done-with-deviations** — D-PROBES: the kill probes are pasted VERBATIM once, as whole files, in §INSTRUMENTS (`test_adv58r2_probes.py`, `test_adv58r2_am6_probes.py`, `test_adv58r2_probes_e.py`), and §A cites each by test name (the brief asked for them in §A; one copy avoids two drifting copies) · D-MEM: host memory pressure from other sessions — my 15 GB watchdog killed two runs (N2's first attempt, the HEAD full-suite baseline); the driver retried N2 clean, and the SAT red adjudication used a same-file HEAD baseline instead of a second full suite · D-AM6: graded amendment 6 on directive #17074 (the brief said "don't grade"; the directive supersedes).
- **VERDICT: CONTRACT INSUFFICIENT** — 7 MISSING PIN (F1 HIGH · F2 · F3 · F4 · F9 am-6 · F10 · F11) · 3 NEW DOOR / reach (F6 · F7 · F8-escape — ruled since by am-7 `01565f9`, not graded) · 2 SAT FRAGILITY (F5 · F8) · 1 P-PKG (the packer = `more_itertools.constrained_batches`) · the rest NOT A DEFECT (§RESIDUALS).
- **P1 headline — YES, wrong builds survive r2:** N3 (packer prices every row like a one-blocker row → **every boot FAILS** on ≥1250 two-blocker stragglers: `composed transaction has 10000 statements`), N4/N5 (a mixed phantom/cycle row half-healed and counted), N1 (WARNING only for the transition), N2 (claim loss warned by the ledger logger), N17 (heal hand-rolls RELATEs), N19 (over-cap row skipped silently); am-6's W6a–d all pass r2. Each: `0 of 1165` r2 red, my probe red, probe green on my reference.
- **Focus 1 — prior survivors: ALL KILLED** on an independently-written reference: WB1–WB18 (+K16, WB18), AM2L (am-2 chunk defect → PR18r2/PR19), K4/K7/K9r/K10/K11r/K17r; SD1–SD3 fixed; WB17r still only a HANG (RS-2).
- **Quantifier table (§P1b):** 19 invariants — 10 ∀ with every door-build killed (Q4 on a single fixture position, stated), 7 GUARDED with a surviving door or a SAT-red correct build (Q1 packer, Q5 phantom/cycle row, Q6 logger scope, Q7 WARNING tier, Q9 CAS population, Q10 `try`-shape, Q15 RELATE), 2 UNPINNED (Q18 over-cap rider, Q19 am-6 E11).
- **Reach table (§P1c):** `derive_cas_verbs` = a HAND-LISTED module set + a one-method shape key → MISSING PIN (EMPIRICAL: a new unguarded door in `messages.py` RED at HEAD, GREEN after §HELD — the §HELD re-key SHRINKS reach; `floor_calibration`'s fence door drop → `843 passed`; a new helper-applied verb N20 → `16 passed`); the (C) injection is EFFECT-observing and sound over what it runs; MP9, `_HealDoors`, the FAILS_LOUD sweep, the one-literal pin are SAFE (empirical kills).
- **Focus 3 — AST receipts: CONFIRMED** 24 EQUAL + PR18 re-key, author's instrument on the committed blobs with controls; plus my context leg — 142 free-name bindings identical (control: 10 differ).
- **Focus 4 — SAT: CONFIRMED** — full suite on plain HEAD + §HELD 1–3 + MY reference: `45 failed, 11899 passed, 62 skipped, 3 xfailed`; all 45 = 63c-i-a a28's owned contract-ahead reds, identical at plain HEAD (`45 failed, 95 passed`, set diff ∅) → **0 attributable**; the author's `2 failed` (part-3 collision) reproduced exactly on my reference. RED@HEAD `119 failed, 413 passed, 5 skipped` reproduced, per file identical.
- **Focus 5 — DUAL:** no Reading-A trace in the committed bytes; D15 misses the SCOPE change (F6); the §8c header + `_GUARDED_CAS_RE_READ` are corpse prose.
- Packages considered: `more_itertools.constrained_batches` (installed 11.1.0, source read + run) → **replace** the hand-rolled packer; `ast`/`logging`/`networkx` keep; `libcst` not installed, not needed (§P-PKG).
- Odoo-20 portability: n/a — no Odoo seam touched.
- Reuse ledger: none — no production symbol introduced (scratch references + test instruments only, pasted §INSTRUMENTS).
- **Graded: `c42eeaf` · HEAD-at-report: `f21a885` · DIFFERENT (23 behind)** — no 58 file / `tasks.py` / `_txn.py` / §HELD target moved; spec moved: am-6 `dcf6b0f` (graded per directive #17074) and am-7 `01565f9` (NOT graded — rules F6/F7) (§HEAD-MOVED).
- Decisions needed: (1) F5/F8 — may the (B)/(C) population require a `try` in the verb itself (no `suppress`, no extract-method), or must the instrument follow the call graph? (2) P-PKG — issue a builder constraint to use `constrained_batches` + declare `more-itertools`; (3) F3 reading (a) vs (b); (4) RS-9 esc1 owner.
- Receipts: §A (F1–F11, verbatim tails) · §PRIOR · §P1b · §P1c · §AST · §SAT · §P7 · §P6 · §DUAL · §P-PKG · §HEAD-MOVED · §RESIDUALS · §INSTRUMENTS.

## §0 Capability check / setup (2026-09-26)
- Idle-gate contract: `/tmp/claude-idle-gate-lore/f2fe3a36-cb3f-47ec-b8ed-14e14fdbedea-adversary-58-r2.contract` = `{"artifact": "REPORT-adversary-58-r2.md"}`.
- lore: `ToolSearch "+lore"` loaded 15 tools; registered `adversary-58-r2` (session `63c-20260924`, cadence ≤20m, spawned_by lead-63c-2).
- grep/rg hook-blocked (#473): every textual sweep below is `awk`/`sed` — a fallback, said out loud.
- Required first read: `docs/reference/surrealdb-31-capabilities.md` (header, §1.1, §3) + finding #497 (`RETURN` inside a composed transaction truncates it — open, docs-only).
- No worktrees, no `git stash`; scratch copies via `./scripts/scratch_copy.sh` only (provenance printed per run).
- Everything I needed was available (Bash, Read/Write, lore MCP). No capability gap.

## §AST — focus 3: the 24/25 AST receipts re-run on the COMMITTED blobs, with controls (2026-09-26)
Inputs, every one md5-verified against the value its author recorded:
- adversary-58's probe files extracted from `9f2f580:REPORT-adversary-58.md` §INSTRUMENTS: `test_adversary58_probes.py` `2cf0d5f4` · `test_adversary58_batch2.py` `1328e035` · `test_adversary58_batch3.py` `cdb99104`;
- the landed files read from the graded commit (`git show c42eeaf:loremaster/tests/test_reanchor_58_r2_{probes,scale,am2}.py`), never the working tree;
- contract-58-r2's instrument extracted from `c42eeaf:REPORT-contract-58-r2.md` §INSTRUMENTS `ast_receipt.py` → md5 `880d05f7` (= recorded).

**Author's instrument, re-run → reproduced:** `EQUAL ×24` (PRB `_boot`, `_chain`, `_seed_chain`, PR1–PR15; SC PR16, PR17; A2 `_boot`, `_stragglers`, PR19, PR20) · `MISSING ×1` `test_PR18_am2_ruled_shape_cap_plus_one_of_ONE_blocker_heals_in_two_chunks` (the am-3 §1 ERRATUM re-key → `test_PR18r2_…`). Controls, on each of the three adversary files: `controls OK: re-wrap EQUAL; one-token mutation DIFFERENT` ×3.

**My own leg — the CONTEXT half the author's instrument does not look at.** Function-level AST equality says nothing about what each free name a probe loads is BOUND to at module level (an import rebinding `create`, a redefined constant). Instrument `ast_context.py` (pasted §INSTRUMENTS): for every AST-equal function, compare the module-level binding (import source / assignment value / def) of every free name it loads.
- Result: `checked 142 free-name bindings over AST-equal functions; 0 differ`.
- Positive control: in a copy of the landed PRB file, `create` re-imported from `_task_fakes` instead of `_reanchor_58_support` → `10 differ` (every AST-equal probe that uses `create`).
- The one module whose CONTENT the bindings point at and which r2 changed, `_reanchor_58_support.py`: `git diff 5a43aeb c42eeaf` removes/modifies exactly three lines, all typing (`ApplyHook.__init__`'s `ledger: TaskLedger` → `Any`, two `type: ignore[method-assign]` dropped). No helper a landed probe calls changed behaviour.
- **Verdict: focus 3 CONFIRMED** — 24/25 AST-equal, the 25th a ruled re-key; bindings identical.

## §REF — my OWN independent reference (focus 4's third leg), 2026-09-26
- Tree `scratch/ref` = HEAD `1a67b98` (code-identical to `c42eeaf`: `git diff --stat c42eeaf 6417e8f -- loremaster lorerunes lorescribe loresigil scripts` is empty) + §HELD parts 1–3 extracted from the COMMITTED reports and md5-verified against the author's recorded values (`part1 dbba9753` from `5a43aeb:REPORT-contract-58.md` lines 173–557 · `part2 5b5f2d8f` · `part3 15f38e31` from `c42eeaf:REPORT-contract-58-r2.md`; `git apply --check` clean ×3) + adversary-58's `build_ref58.py` (md5 `5915c12e`, verbatim) + **my own** amendment-3/5 deltas `my_ref.py` (md5 `de2d2801`, pasted §INSTRUMENTS), written WITHOUT reading contract-58-r2's `build_ref58_r2.py`. Result md5: `tasks.py 5b4ecba9…` · `_txn.py ca86524a…` (reproduced byte-identically in a second scratch copy `scratch/reach`).
- My deltas: `TxnClaimLostError(TxnDomainRejectionError)` + a `claim_lost:` classifier branch through the ONE mapping helper `_domain_rejection_error`; `_log_rollback` level = DEBUG (claim_lost) / WARNING (app THROW — the engine renders `THROW 'x'` as `An error occurred: x`, PROBED 3.2.4 this session, `probes/throw_raw.py`) / ERROR (everything else, incl. a UNIQUE-index violation, probed); claim catches `TxnClaimLostError` only; order backfill → heal; ONE counter `_composed_statement_count` consumed by the accessor and the packer; the heal rebuilt: per-row fragments (one edge DELETE per superseded entry, the shell re-anchor, the row's RELATE counted with it), greedy packing by each row's BUILT count, `TxnDomainRejectionError` per chunk isolated + WARNING, every store fault propagates, a phantom or cyclic chain head skips the WHOLE row + WARNING every boot, `StragglerHealPackerError` for an over-cap row.
- **The whole scoped contract on it (13 files, 1165 collected, provenance printed): `1164 passed, 1 skipped, 1 warning in 140.80s` — 0 failed, first run.** Two independently-authored references now satisfy r2 (the author's and mine): the contract is SATISFIABLE and does not encode one author's shape by accident (except where §A F3 says it does).
- Controls on the predecessor's build alone (am-1/am-2 era, no am-3/am-5 deltas): `24 failed, 1140 passed` — every one an am-3/am-5 pin (heal packer, phantom/cycle record, typed claim DEBUG, (B)/(C), order) — so the r2 pins DO see the pre-r2 world.

## §A — MISSING PINS / NEW DOORS / SAT findings (each: class · the test that should exist · the defect · receipt verbatim)
Instrument for every build below: `wb_r2adv.py` (pasted §INSTRUMENTS) over `scratch/ref` (my reference, §REF); scope = all 13 files of the r2 contract as committed (`files58.txt`, 1165 tests) + §HELD + my probe file `test_adv58r2_probes.py` (pasted §INSTRUMENTS; **all 6 probes GREEN on my reference: `6 passed in 36.36s`** — the P0 positive control). Each anchor asserted exactly-once, each edited file asserted CHANGED, the reference md5s re-asserted after every build. "SURVIVES" = the contract is GREEN (0 of 1165 red) while the named probe is RED.

### F1 — MISSING PIN (HIGH): the heal packer is pinned only over rows naming ONE superseded blocker — a packer that prices every row like a one-blocker row passes all of r2 and FAILS EVERY BOOT at scale
- **CLASS:** am-3 §1 — *"the packer BUILDS each row's fragments"* ⇒ ∀ straggler shapes, every composed heal chunk ≤ `TXN_STATEMENT_HARD_CAP`. The domain is the set of straggler SHAPES (superseded entries per row × whether the head is already present × chunk mix); every r2 scale fixture (`RU::…SIX_blockers…`, `A2::PR18r2/PR19`, `RU::…MUTATION_padding…`, `SC::PR17`) seeds rows with exactly ONE superseded entry; the only two-entry row (PR3) is one row.
- **Wrong build N3** (`N3_packer_prices_every_row_like_a_one_blocker_row`): derive a per-row unit cost the way the accessor derives `per` — BUILD one synthetic one-blocker row through the real shell and count it — and pack every row at that unit. It follows the shell (the padding mutation moves it), so every r2 pin is satisfied.
- **Receipt:** `N3 … SURVIVES the contract (probe red) · 1 failed, 1169 passed, 1 skipped` — the 1 is my probe; its failure: `SurrealStoreError: composed transaction has 10000 statements, exceeding the hard cap of 5000 statements per transaction` — raised from `ensure_ready`, i.e. **the boot fails, and it fails again on every boot** (the heal re-builds the same chunk): lore cannot start on a store holding ≥1250 two-blocker stragglers.
- **The test that should exist:** `test_PC_stragglers_naming_TWO_superseded_blockers_at_scale_heal_in_ONE_boot` (pasted §INSTRUMENTS): 1300 raw stragglers each naming TWO superseded blockers (different heads) → one boot heals all, `count == 1300`, every heal chunk ≤ cap. GREEN on my reference.
- **SIBLINGS TRIED:** one-blocker rows at cap+1 over 1/6/10 blockers (r2's, all kill AM2L); two-blocker rows at scale (N3 — survives). **SIBLINGS NOT TRIED:** rows whose superseded entries share ONE head (one RELATE for two entries — a cheaper row; an over-pricing packer is only inefficient, not wrong); rows already naming the head (no RELATE); a population MIXING row costs so a greedy packer's chunk boundary falls mid-cost-class — the generated form of the pin is a cost-mix sweep, not one fixture.

### F2 — MISSING PIN (MEDIUM; pending am-6 may re-rule the tiers): am-3 §3's WARNING tier is pinned for ONE member — a lost TRANSITION race
- **CLASS:** am-3 §3 — *"Every OTHER THROW-rooted rollback (transition/supersede lost races, R1's straggler, the heal's chunk) logs at WARNING"* ⇒ ∀ app-THROW rollbacks except claim-lost: `store.transaction.rolled_back` at WARNING. r2 pins only the transition (`RU::…CONTROL_a_lost_TRANSITION_race_still_logs_at_WARNING`); the heal-chunk test pins the LEDGER's WARNING record, never the driver's rollback level.
- **Wrong build N1** (`N1_warning_only_for_the_transition_text`): `_log_rollback` keys WARNING on the transition's own THROW text; every other app THROW stays at ERROR.
- **Receipt:** `N1 … SURVIVES the contract (probe red) · 2 failed, 1168 passed, 1 skipped` — both reds are my probes: `test_PA1_a_lost_SUPERSEDE_race_logs_its_rollback_at_WARNING` → `AssertionError: ['ERROR']`; `test_PA2_an_R1_straggler_rollback_logs_at_WARNING` → `AssertionError: ['ERROR']`.
- **The test that should exist:** GENERATED over the ledger's THROW vocabulary (every `throw_message` a task CAS verb passes to the shell, + R1's closing guard, + the heal chunk's re-anchor THROW) — drive each to its lost-race rollback and assert exactly one `rolled_back` at WARNING. PA1/PA2 are two instances, pasted.
- ⚠ **Amendment 6 is PENDING** (FORK-3: a prefix-marker table `cas_lost:` / `reanchor_straggler:` / `heal_chunk:`, deny-by-default ERROR). Not graded; but whatever table it rules, the pin must be generated over that table's rows, not one member — this finding is the class am-6's pins must meet.
- **SIBLINGS TRIED:** transition (r2), supersede lost race + R1 straggler (PA1/PA2 — unpinned). **NOT TRIED:** the heal chunk's rollback level; findings/briefs THROWs (outside 58).

### F3 — MISSING PIN (LOW–MEDIUM): "a routine claim loss is not an alarm" is pinned only for the DRIVER's logger
- **CLASS:** am-3 §3's principle (*"A routine claim LOSS is not an error … how an alarm gets switched off"*) ⇒ ∀ lore loggers, an 8-way race's 7 losses emit nothing ≥ WARNING. r2's 8-way pin filters `r.name.startswith("loremaster.store")`; its PR10 probe checks ERROR only.
- **Wrong build N2:** `claim_task`'s typed catch body logs `logger.warning("task.claim.lost", …)`.
- **Receipt:** `N2 … SURVIVES the contract (probe red) · 1 failed, 1169 passed, 1 skipped` — my probe `test_PB_an_8_way_claim_race_raises_no_alarm_from_ANY_lore_logger` → `AssertionError: [('loremaster.tasks', 'WARNING', 'task.claim.lost'), …]` (seven of them).
- **Adjudication note:** am-3 §3's own pin sentence scopes the leg to *"a `caplog` leg at the `_txn` logger"*, so N2 is within the ruling's LETTER; it defeats the ruling's stated PURPOSE. Two readings: (a) the ruling means the driver only (N2 legal); (b) it means "no alarm" (N2 a defect). I would pick (b): widen the filter to `loremaster`. A one-token change to an existing pin.

## §P7 — RED@HEAD re-derived (2026-09-26, clean copy `scratch/head` = HEAD `6417e8f`, code-identical to `c42eeaf`; no §HELD, no build)
- The author's exact file set (every 58 file + every DUAL-edited file + `test_ast_reach_helpers.py`), `-n 6`, provenance `…/scratchpad/head/loremaster/loremaster/__init__.py`: **`119 failed, 413 passed, 5 skipped in 89.96s`** — the author's `119 failed, 413 passed, 5 skipped` REPRODUCED.
- Per file (mine): S 44 · G 15 · P 5 · `test_blocks_edge` 1 · `test_task_read_surface` 1 · D 3 · PRB 12 · SC 2 · A2 3 · RU 27 · CR 6 — **identical to the author's per-file table.**
- First exception per failure (mine): 70 `AssertionError` · 34 `AttributeError` · 13 `Failed: DID NOT RAISE` · 1 `IndexError` · 1 `ImportError` = 119. Every Attribute/Import error names an unbuilt 58 symbol (`_guarded_append_fragment`, `max_reanchor_dependents`, `.reanchored`/`.reblocked` on a `str`, `TxnClaimLostError`, `SupersedeResult`) — right reason. ⚠ **Report-arithmetic nit (not a contract defect):** the author's §RED@HEAD breakdown of "r2's 50 new reds" enumerates 24 + 11 + 6 + 4 + 1 = **46**; the count (50) is right, four reds are unclassified in the prose.

### F4 — MISSING PIN (MEDIUM): "a phantom / cyclic chain head skips the WHOLE row" is pinned only on rows naming ONE superseded blocker
- **CLASS:** am-3 §5 — *"a row whose head is a phantom is SKIPPED … excluded from `count`"* (and *"A chain that CYCLES … is treated the same way"*); BC-r2-5 *"the WHOLE row skipped (byte-identical)"* ⇒ ∀ stragglers with ≥1 unresolvable chain: the row is byte-identical after the boot and uncounted. Every r2 fixture (`RU::TestAPhantomChainHeadIsSkippedAndRECORDED`, `RU::TestASupersededByCycleIsBoundedAndRECORDED`, `PRB::PR5/PR15`) puts the bad chain on a row with NO other superseded blocker — so "skip the row" and "skip the entry" are indistinguishable there (the same small-N / single-member class as F1).
- **Wrong builds N4 / N5:** on a phantom (N4) / cyclic (N5) head, drop only THAT entry and heal the row's other superseded entries (warning still emitted).
- **Receipts:** `N4 … SURVIVES the contract (probe red) · 1 failed, 1169 passed, 1 skipped` → `test_PD1_…: AssertionError: the mixed row was half-healed`; `N5 … SURVIVES the contract (probe red) · 1 failed, 1169 passed, 1 skipped` → `test_PD2_…: AssertionError: a cyclic-chain row was half-healed`.
- **Why it matters (not cosmetic):** a half-healed row is re-anchored + noted + COUNTED while it still names an unresolvable chain — the heal's INFO `count` then over-claims "healed" (the trust law: a served count describes the whole set its label claims), and the row is rewritten under a record that says it was skipped.
- **The tests that should exist:** `test_PD1_a_MIXED_row_phantom_head_plus_healable_blocker_is_skipped_WHOLE` and `test_PD2_a_MIXED_row_cyclic_chain_plus_healable_blocker_is_skipped_WHOLE` (pasted §INSTRUMENTS; GREEN on my reference).
- **SIBLINGS TRIED:** single-blocker phantom/cycle rows (r2 — killed WB6r/WB17b); mixed phantom and mixed cycle (N4/N5 — survive). **NOT TRIED:** a row with TWO phantom-headed entries (one WARNING per entry, or per row? — am-3 §5 names `blocker_id` per record, so presumably per entry; unruled count — a question for the sidecar, not a pin I can derive).

### F5 — SAT FRAGILITY → ruling needed (MEDIUM): the (B) index keys on the `try` SHAPE, so a CORRECT claim that catches the TYPE with `contextlib.suppress` is RED on two r2 pins
- **CLASS:** am-5 (B)'s scope *"for every `try` …"* ⇒ the static index sees a caught class only inside an `ast.Try`. `contextlib.suppress(X)` IS catching X by type (it is a house idiom: `contextlib.suppress(` appears 10× in production — `inbox_awaiter.py`, `scout.py`, `server.py`), but is invisible to the index.
- **Build N6 (a CORRECT build — am-3 §3 / am-5 "any body"):** `with contextlib.suppress(TxnClaimLostError): await self._apply([...])` in place of `try/except TxnClaimLostError: pass`. Behaviourally identical: every behavioural pin, the (C) runtime injection and `RU::…catches_the_TYPE_never_the_text` stay GREEN.
- **Receipt:** `N6 … OBSERVED 2 contract red(s) · 2 failed, 1168 passed, 1 skipped` — `test_retry_seam.py::TestTheClassKeyedIndexPartitionsEveryCASHandler::test_the_TYPED_catches_match_their_canonical_set` (*"the SAFE-BY-TYPE CAS handlers changed"*) and `test_reanchor_58_r2_cas_runtime.py::TestTheRuntimeSetAndTheStaticIndexAgree` (*"(C)-driven verbs whose try/except the static index did not classify: ['tasks.py::claim_task']"*).
- **Two readings:** (a) the index is right to demand a visible `try` (reviewer visibility is its stated purpose — am-5 §2 "the reviewer-visible index"), so the builder constraint "write claim as `try/except`" is a DELIBERATE shape rule and must be written down as one (it is not: BC-r2-3 says "any body", and nothing names `suppress`); (b) the index should see `with contextlib.suppress(<names>)` around an apply seam as a catch (the same classification). I would pick (b) — (a) is am-5's rejected option (A), "bend production to an instrument's blind spot", one level up. Either way it is the operator's/sidecar's call; today a builder who reaches for the house idiom gets two unexplained reds and no builder constraint telling him why.
- **SIBLINGS TRIED:** `suppress` (N6). **NOT TRIED:** `except*` (`ast.TryStar` — also invisible to `isinstance(node, ast.Try)`); a catch in a nested helper coroutine (see F7).

### F6 — REACH REGRESSION + ORPHANED VIRTUE (P1c/P6b, HIGH for the instrument): §HELD part 2 SHRINKS the guarded-CAS door scan from the whole package to two hand-listed modules + one named door — a new unguarded door elsewhere was RED at HEAD and is GREEN after §HELD
- **CLASS:** `∀ guarded-CAS handlers in the package: exhausted contention propagates UNREAD` (test_retry_seam §8c's own stated invariant). HEAD's `_discover_guarded_cas_handlers` DERIVED its population from `_PACKAGE_ROOT.rglob("*.py")` (shape-keyed, but package-wide). §HELD's `_classified_cas_handlers` scans only functions in `derive_cas_verbs(...)`, whose module set is the hand-list `SHELL_LEDGER_MODULES = ("tasks.py", "findings.py")` ∪ the hand-list `SINGLE_STATEMENT_CAS_DOORS = ("briefs.py::_relate_briefed",)` (`_reanchor_58_support.py`). The (C) runtime family ranges over the SAME set. **No pin goes RED when a module outside those lists gains a guarded CAS** — the reach is a hidden constant (INSTRUMENT-0's defeat row, verbatim).
- **Empirical legs** (`scratch/reach` = my reference, byte-identical md5s; pytest `-p no:xdist`, AST-only tests):
  - door PROBE: an unguarded `except SurrealStoreError: return await self._select_row(row_id) is not None` around `self._apply([])`, added to `messages.py`'s ledger class.
  - NEW (§HELD) scanner + door → `test_retry_seam.py -k "TestNoGuardedCas… or TestTheClassKeyed…"`: **`14 passed`**; `test_reanchor_58_r2_cas_runtime.py::{TestTheDrivenSetIsTheDerivedSet, TestTheRuntimeSetAndTheStaticIndexAgree}`: **`2 passed`** — invisible to (B) AND (C).
  - OLD (HEAD `6417e8f`) scanner + the same door: **`FAILED …test_the_door_enumeration_matches_the_canonical_set` — `AssertionError: the set of guarded-CAS doors has changed.` — `1 failed, 5 passed`.**
  - CONTROL 1 (old scanner, no door): `6 passed` — the red above is the door's.
  - CONTROL 2 (new scanner, the SAME door placed in `tasks.py` — in scope): `FAILED …test_the_door_enumeration_matches_the_canonical_set` + `FAILED …TestTheDrivenSetIsTheDerivedSet::test_every_derived_CAS_verb_has_a_driver…` — the new instruments DO see a door inside their hand-listed scope.
- **The DUAL (P6b):** r2 §DUAL D15 adjudicates the re-key's CRITERION change (shape → class) and never its SCOPE change (package → two modules). The HEAD block comment directly above the re-keyed code (`test_retry_seam.py` §8c header, untouched by §HELD) still promises *"the population is DISCOVERED, by the property that MAKES a handler a guarded CAS — `except SurrealStoreError` whose body RE-READS state (`await self._select…`). A fifth door is pinned the day it is written, by nobody's memory."* — **after §HELD both halves of that sentence are false** (corpse prose, served to every agent who opens the file), and `_GUARDED_CAS_RE_READ = "_select"` survives as a dead constant.
- **The test that should exist:** the population DERIVED from a property of production truth, not a module list — am-5 §2's own first form: *"every `try` whose body (transitively, within the function) calls the apply seam"*, where "the apply seam" = every function that reaches `execute_transaction` / `run_query` (derivable from the AST call graph, or from the retry-seam runtime guard's own observed set). Plus a completeness pin: `SHELL_LEDGER_MODULES ∪ modules of SINGLE_STATEMENT_CAS_DOORS` == every module containing an `except` whose caught class can hold `TxnContentionExhaustedError` around a store call. Plus the corpse: rewrite §8c's header to state the new reach and its bound, delete `_GUARDED_CAS_RE_READ`.
- **SIBLINGS TRIED:** a door in `messages.py` (escapes), a door in `tasks.py` (caught). **NOT TRIED:** `memory/local.py` (has `_apply`), `governed.py`'s runner, `keeps.py:622`'s `except SurrealStoreError`.

### F7 — the live instance of F6 (NEW DOOR, pre-existing, not 58's code): `floor_calibration/store.py`'s fence CAS is a guarded-CAS door BY AMENDMENT 5'S OWN CLASS CRITERION, outside both layers — its exhaustion guard can be deleted with every instrument green
- The fence write THROWs on a moved fence (`IF array::len($fc_fence_held) = 0 { THROW … }`), and its `except SurrealStoreError as error:` handler RE-READS the lease row (`_fence_verdict` → `self._query(SELECT … FROM lease …)`) and may re-raise `FenceLostError` — a guarded-CAS door (am-5: *"an `except` clause on a guarded-CAS apply whose caught class closure contains `TxnContentionExhaustedError`"*). Its guard is a TUPLE `except (SurrealConnectionError, TxnContentionExhaustedError): raise` — correct today, and invisible to HEAD's scanner too (R5 of adversary-58: tuples unrecognised; re-read via a helper).
- **Wrong build WB-H:** drop `TxnContentionExhaustedError` from that tuple (exhausted contention then lands in the re-reading handler and, if the lease moved meanwhile, is reported as `FenceLostError` — the #102 lie). **Receipt:** `test_floor_calibration_{store,domain,schema}.py` + `test_retry_seam.py` + `test_reanchor_58_r2_cas_runtime.py`, `-n 4`: **`843 passed, 1 warning in 256.61s`** — nothing reds. Control (guard intact): `test_floor_calibration_store.py` `77 passed`.
- Not 58's code and not 58's bug; it is the concrete site proving F6's hidden constant already excludes a real door. **Owner: the lead** (a (C) driver + (B) scope for `floor_calibration`, or a pinned KNOWN BOUND with a re-open trigger).

### F8 — SAT FRAGILITY (same class as F5): an extract-method refactor of the heal's chunk apply is RED on four r2 pins — `derive_cas_verbs` keys on the literal `self._apply(...)` call SHAPE in the verb body
- **Build N7 (CORRECT — identical behaviour):** move the heal's `try: await self._apply(chunk) / except TxnDomainRejectionError: WARNING` into a helper `_apply_heal_chunk(...)`.
- **Receipt:** `N7 … OBSERVED 4 contract red(s) · 4 failed, 1166 passed, 1 skipped`: `CR::TestTheDrivenSetIsTheDerivedSet` (*"drivers for NO derived verb: ['tasks.py::_reanchor_stragglers']"*), `CR::…[tasks.py::_reanchor_stragglers]` (*"driver is stale"*), `CR::TestTheRuntimeSetAndTheStaticIndexAgree`, `RS::…test_the_TYPED_catches_match_their_canonical_set`. The heal's CAS drops out of BOTH layers' population (the verb no longer calls `_apply`; the helper calls `_apply` but does not reach the shell) — the stale-driver check is the only thing that notices, and only because the verb pre-existed.
- r2 DISCLOSES this (BC-r2-9: *"a builder that moves that `try` into a helper method changes the derived key … the exact set + the (C) registry re-keyed with it"*) — but a builder may not re-key tests, so BC-r2-9 is in effect "do not extract a method", a production-shape rule set by an instrument. Same ruling question as F5.
- **The ESCAPE this implies for a NEW verb (focus 2, "can a verb escape the derived caller set?"):** YES, by construction — a new CAS verb that applies through a helper (verb reaches the shell but does not call `_apply`; helper calls `_apply` but does not reach the shell) is in NEITHER layer's population; nothing is stale because nothing pre-existed. For `TaskLedger` specifically, `RU::TestEveryComposedGuardedWriteCameFromTheShell`'s reach check (`_apply` callers ⊆ observed) still forces SOME leg — but that pin checks write provenance, not exhausted-contention handling; the (C) property stays unverified for the new verb. For `FindingLedger` (64b's reshaping) nothing forces anything. **Two derivations of "the CAS verbs" in r2 disagree** (`derive_cas_verbs` needs `_apply` ∧ shell-reach in ONE method; `_apply_callers` needs only `_apply`, TaskLedger only) — P1c Q5's two-sources shape.
- **The test that should exist:** derive the CAS population from the CALL GRAPH, not one method's body — a verb is a CAS verb iff some call path from it reaches BOTH the shell and `_apply` (transitively, same module); and assert `derive_cas_verbs ⊇ {m : m calls _apply ∧ m reaches the shell transitively}` so the two derivations are one. A synthetic discriminator: verb→shell + verb→helper→`_apply` must be DERIVED.

## §P6 — corpse sweep (bare, anchor-free; awk over `scratch/head` = HEAD `6417e8f`, every `*.py` under `loremaster/tests`, `scripts`, `skills` — grep is hook-blocked, awk said out loud)
Retired terms of the am-1/am-2/Reading-A worlds: `straggler_chunk_failed` · `straggler_skipped` · `claim lost its compare` · `_still_claimable` · `chunk_failed` · `never fails on a heal` · `boot itself never fails` · `fail-open` · `fail_open` · `re-read inline` · `re-reads inline`. 30 hits, each with a verdict:
| hit | verdict |
|---|---|
| `scripts/test_forgery_door_sweep.py:455` (*"amendment 2's 'the boot never fails on a heal fault' is NARROWED"*) | LEGIT — r2's D12 prose quoting the retired wording in order to retire it |
| `_reanchor_58_support.py:60` (*"blocked_by was fail-open at write before 04b-1"*) | UNRELATED — 04b-1's legacy-row provenance |
| `test_blocks_edge.py:4730`, `:8514`; `test_task_read_surface.py:1357`; `test_query_tasks_bounded.py:994`; `test_task_ledger.py:793`; `scripts/esc1_write_path_cycle_closure.py:137` | UNRELATED — 04b-1 / R3 fail-open `blocked_by` history |
| `test_principal_delete_governed_63a.py:184`; `test_governed_substrate_63a.py:490`; `test_fixwave_a28_63c_i_a.py:1086`, `:1105`, `:1110`, `:1137` | UNRELATED — packet 63 governed-bypass fail-open |
| `test_ast_reach_helpers.py:2305`, `:2600`, `:2611`, `:2636` | UNRELATED — #351 escape-site discriminator's disposition |
| `test_tool_population_61b.py:22`, `:126`, `:250` | UNRELATED — 61b governed tool population |
| `scripts/test_teammate_idle_gate.py:13`, `:25`, `:55`, `:65`, `:66`, `:484`, `:506`, `:532` | UNRELATED — the idle-gate hook's fail-open-to-v1 |
| `scripts/probe_unique_nullable_48.py:249` | UNRELATED — #48 probe |
- **No 58-retired corpse in any test** (no pin asserts am-2's chunk-failed event, the untyped claim-loss text, the re-read-keyed door criterion, or `chunks == 2`). The one 58-relevant corpse is PROSE in the §HELD file, not a pin: F6 (the §8c header of `test_retry_seam.py` + the dead `_GUARDED_CAS_RE_READ`).

## §DUAL — focus 5: the undone Reading-A pins, and r2's DUAL rows re-derived
- **Reading A is gone from the committed bytes.** Sweep of every `.py` file in `git show --name-only c42eeaf` for `reading a|reading-a|inline re-read|re-read inline|re-reads inline|bc-r2-3|_select*`: the only hits are in `test_blocks_edge.py` (`:167`, `:2904`, `:4554`, `:6652`, `:6715`, `:6808`, `:6889`, `:8185`) and all name **ESC-1/ESC-4 "reading A"** (2026-07-28 rulings on the backfill) — UNRELATED to FORK-2. The §HELD re-key's door criterion does not consult a re-read (verified by F6's CONTROL 2: a door is found by its caught CLASS). BC-r2-3's "re-read inline" is struck through in the report. **No Reading-A trace survives** — CONFIRMED.
- **But the Reading-A-era shape key's PROSE survives** (not Reading A, its predecessor): §8c's header + `_GUARDED_CAS_RE_READ` — F6.
- r2's own DUAL rows (E5, E11, B21–B26, D12–D18): E5 → PR1 (WB1 killed, §PRIOR); B21/B22 → F2/F3 (the WARNING tier and the logger scope are narrower than the rows claim); B23 → F1 (the packer rows); B25 → F4 (skip-the-row); **D15 is incomplete** — it adjudicates the criterion change and not the scope change (F6); E11 → now RULED by am-6 FORK-4 (CHANGED-DELIBERATELY + pin) — r2 has no pin (F9, am-6 grading).

### F9 — AMENDMENT 6 (`dcf6b0f`, graded per lead directive #17074 — acked): r2 carries NONE of am-6's pins; all four ruled-out builds survive
r2 predates am-6, so these are the EXPECTED missing pins the directive names — recorded with receipts so the follow-up contract has its kill set ready.
- **Host:** `scratch/reach` = my reference + `my_ref_am6.py` (pasted §INSTRUMENTS: ONE `_ROLLBACK_LOG_TIERS` table in `_txn` keyed on the recognised THROW prefix, deny-by-default ERROR; the ledgers' THROW constants prefixed `cas_lost:` / `reanchor_straggler:` / `heal_chunk:`; the heal's row THROW `heal_chunk:`) — md5 `tasks.py 12917da9…` · `_txn.py 8c748e4f…` · `findings.py 48d8fd7a…`. Probe file `test_adv58r2_am6_probes.py` (pasted): 6 tier legs generated from am-6's table (incl. the unprefixed deny-by-default control) + the drop-one-entry mutation (am-6 pin iii) + E11 `[A, A, X] → [A, X']` through supersede (with the claim-wins leg and the `[A, X]` control) and through the boot heal.
- **Control `REF6_control_no_edit` (EXACT): `1179 passed, 1 skipped`** — the am-6 reference satisfies ALL of r2 and all 15 of my probes ⇒ **no r2 pin contradicts am-6** (am-6 is satisfiable on top of r2; the follow-up adds pins, it does not re-key any).
- **Also on the record:** my am-3 reference (the one r2 was graded against in §REF, `1164 passed`) FAILS am-6's deny-by-default leg and its mutation leg (`2 failed, 7 passed` on the am-6 probes) — i.e. **both existing references (mine, and by its own §REFERENCE description contract-58-r2's, which keys WARNING on the engine's `An error occurred:` prefix) are am-6 wrong builds that r2 passes.** The builder must follow am-6, not either reference.

| ruled-out build (am-6) | contract r2 | red probe(s) | the pin that should exist |
|---|---|---|---|
| **W6a** an unrecognised app THROW defaults to WARNING | **0 of 1165 red** · `2 failed, 1177 passed` | `test_P6_each_ruled_tier…[an_unprefixed_app_throw]`, `test_P6_mutation_dropping_ONE_table_entry…` | am-6 (ii) deny-by-default control: a synthetic unprefixed THROW → exactly one ERROR |
| **W6b** a SECOND tier table (a private prefix tuple in `_log_rollback`, the ruled table left defined and unused) | **0 red** · `1 failed, 1178 passed` | `test_P6_mutation_dropping_ONE_table_entry_moves_ONLY_that_tier` | am-6 (iii): drop one entry of `_ROLLBACK_LOG_TIERS` in-suite → that tier's leg goes ERROR, the others unchanged (one source, proven by mutation) |
| **W6c** the re-anchor dedupe collapses only X's copies (`[A, A, X] → [A, A, X']`; spelling PROBED on 3.2.4, `probes/xonly_dedupe.py`: `['A','A','X'] -> ['A','A','N']`, `['N','X'] -> ['N']`) | **0 red** · `2 failed, 1177 passed` | `test_P6_E11_a_legacy_duplicate_collapses_WHOLE_column…`, `test_P6_E11_through_the_boot_heal` | am-6 FORK-4's fixture, both through supersede and through the heal |
| **W6d** `governed_conflict:` left at ERROR | **0 red** · `1 failed, 1178 passed` | `test_P6_each_ruled_tier…[governed_conflict]` | am-6 (ii) governed-conflict → exactly one WARNING (r2's §HELD part 3 captures at DEBUG and asserts only server-side survival, so it cannot see the tier) |
- **Also missing (am-6 pin i):** the table's keys == the prefixes of the ledgers' THROW constants, both ways (a THROW constant with no tier → RED; a tier with no producer → RED) — no r2 test can hold it (no table exists at r2); the natural derivation is an AST sweep of the `throw_message=` arguments and the `THROW '<const>'` f-strings. Not built as a probe (its discriminating build is W6a/W6b's sibling "a ledger invents an unprefixed THROW" — the deny-by-default leg above already catches its runtime effect).
- **CLASS (all four):** the rollback tier is a function of the root cause's recognised prefix, ∀ prefixes in ONE table, ERROR otherwise. **SIBLINGS TRIED:** W6a–d. **NOT TRIED:** a table matched by substring instead of prefix (`"cas_lost:" in text` — a user-controlled row id inside a governed THROW could then select a tier); the tier chosen on the SECOND prefix of a text carrying two.

### F10 — MISSING PIN (LOW — the "rider is part of the ruling" class): am-3 §1's single over-cap row refusal is unpinned
- am-3 §1: *"A single row that alone exceeds the cap (impossible for any real row … but **pinned as a refusal**, not an infinite chunk) RAISES a typed packer error"*. No r2 test reaches that branch (P3: an unreached branch; awk sweep of the r2 files for `packer error|over-cap|single row|alone exceed|alone compos` → 0 hits).
- **Wrong build N19** (over ref6): the over-cap row is skipped silently (`continue` before the raise). **Receipt:** r2 scope on N19 `1164 passed, 1 skipped` (0 red); my probe `test_PE_a_single_straggler_that_alone_exceeds_the_cap_fails_the_boot_LOUD_and_changes_nothing` → `Failed: DID NOT RAISE`. Control on ref6: `1 passed`, printing `RAISED: StragglerHealPackerError straggler … alone composes 5101 statements, over the 5000-statement transaction cap`.
- The fixture is constructible (1700 legacy blockers superseded by one head, one row naming all 1700 — `INSERT` in two statements, 1.6 s). "Impossible for any real row" is true of the fleet today; a silent skip would be the one heal outcome with NO record at all, so the ruling's rider is worth its one test.
- **F8 addendum — the escape CONSTRUCTED (N20, over ref6, AST-only pins, `-p no:xdist`):** a 57-shaped NEW verb `assign_task` builds its fragment through `_guarded_append_fragment` and applies through a helper `_commit_assign` whose `except SurrealStoreError:` re-reads and serves "lost" (UNGUARDED — the #102 lie). `CR::TestTheDrivenSetIsTheDerivedSet` + `CR::TestTheRuntimeSetAndTheStaticIndexAgree` + `RS::TestNoGuardedCas…` + `RS::TestTheClassKeyed…` → **`16 passed`** (the door is in neither layer). The only red: `RU::TestEveryComposedGuardedWriteCameFromTheShell` → `AssertionError: reach: TaskLedger methods that call _apply = [… '_commit_assign' …]` — a DIFFERENT property's reach check (write provenance); the day 57 adds an MP9 leg for `assign_task`, that pin goes green and the unguarded door ships with (B) and (C) both green.

## §PRIOR — focus 1: every adversary-58 survivor (+ K16, WB18) and the am-2 chunk defect, KILLED on the committed bytes (2026-09-26, `scratch/ref` = my reference; `wb_r2adv.py`; scope = the 13 r2 files + probes; results `wbout/results.jsonl`)
Verbatim builds = adversary-58's `wrong_builds.py` (md5 `790e0309`, extracted from `9f2f580`), every anchor exact-once on MY reference. Heal builds whose anchors named the am-1 heal are re-expressed over my heal (`…r`, edits pasted in `wb_r2adv.py`). "Killed by" = the contract reds observed (include mode — the declared pin must be among them).
| build (predecessor MP) | the wrong behaviour | killed by (observed r2 reds) | verdict |
|---|---|---|---|
| WB1 (MP1) | every non-lost-race supersede rollback served as the R1 "retry" teaching | `PRB::PR1` | **KILLED** |
| WB2 (MP2) | K-blind cap on the legit 2-statement R1 layout | `PRB::PR2` + `RU::…AcrossFloorBoundaries[3,per,per+1]` + `SC::PR16` (5 reds) | **KILLED** |
| WB2a (control) | the legit layout alone | — (`1170 passed`, EXACT 0) | control holds — PR2/RU not over-tight |
| WB3r (MP3) | heal counts (row, blocker) pairs | `PRB::PR3` (+1) | **KILLED** |
| WB4r (MP3) | heal rewrites only the first superseded entry | `PRB::PR3` (+1) | **KILLED** |
| WB5r (MP4) | heal RELATEs head→Y even when Y names the head (doubled edge) | `PRB::PR4` | **KILLED** |
| WB6r (MP5) | no phantom-head check (RELATE to a phantom) | `RU::TestAPhantomChainHeadIsSkippedAndRECORDED` (+1) | **KILLED** (PR5 stays green — r2's D-PR5, confirmed) |
| WB7 (MP6) | #130 exclusion client-side after a LIMIT'd read | `PRB::PR6` | **KILLED** |
| WB8 (MP7) | `reblocked` only for a `done` X | `PRB::PR7` | **KILLED** |
| WB9 (MP8) | cycle check with `minted` = all pending | `PRB::PR8` + `RU::…legacy_loop_is_untouched…` | **KILLED** |
| WB12r (MP9) | a 4th hand-rolled guarded append, guard template a MODULE CONSTANT | `G::…every_guarded_append_ledger_has_ONE_producer` + `G::…one_producer_IS_the_shell` | **KILLED** — ⚠ my DECLARATION named `PR9`; PR9 scans a SYNTHETIC source and cannot red on any build — the kill is G's widened scan over the real `tasks.py` (r2 §DUAL D13). Declaration error mine, disclosed; the author's "WB12r (AST legs) 2 reds" matches |
| WB14 (MP10) | WARN threshold cloned | `PRB::PR13` | **KILLED** |
| WB15 (MP11) | literal `5000` in the accessor | `PRB::PR14` | **KILLED** |
| WB16 (MP12) | note `at` a constant | `PRB::PR12` | **KILLED** |
| K16 (MP13) | dependents' RELATEs hand-rolled in the supersede | `RU::TestEveryRELATEComesFromTheSharedFragment` | **KILLED** |
| WB18 (MP15) | `owner=` excludes superseded rows | `A2::PR20` | **KILLED** |
| WB17r (MP18) | unbounded chain follow | run did not complete in 900 s (`RUN_TIMEOUT`, group killed) | **HANG as declared** — killed only by a HANG, as in r2. ⚠ PR15/RU wrap the boot in `asyncio.wait_for(…, 60)`, but the unbounded chain-follow is a SYNCHRONOUS `while` loop (no `await`), so `wait_for` can never cancel it — the suite HANGS rather than reds (residual RS-2) |
| WB17b (MP18) | a cycle member treated as the head | `RU::TestASupersededByCycle…` | **KILLED** |
| K9r | heal logs every boot | 7 reds incl. `RU::…SIX_blockers…`, `PRB/A2::PR19`, second-boot-silent pins | **KILLED** |
| K11r | heal counts heads/chains | 8 reds incl. `PR3`, `PR18r2`, `PR19` | **KILLED** |
| K17r (SD2) | heal BEFORE backfill | `RU::…heal_READS_what_the_backfill_minted…` + `RU::…every_heal_door…RAISES[store,transport]` + MP9 + D's swallow leg | **KILLED** |
| **AM2L (am-2 chunk defect, PR18/PR19)** | am-2's literal sizing: chunks of `max_reanchor_dependents(0)` ROWS | `A2::PR18r2` + `A2::PR19` + `RU::…SIX_blockers…` + `RU::…MUTATION_padding…` + `RU::…DOMAIN_rejection…` (7) | **KILLED** |
| K4 | cycle check over the un-rewired graph | both `RU` CONTROLs + 2 r1 pins | **KILLED** |
| K7 | re-anchor through a private clone | 11 reds ((C) stale, (B) typed set, MP9, G one-producer…) | **KILLED** |
| K10 | heal stops at the first hop | 3-hop + done-head + cycle pins | **KILLED** |
| **SD1** | a build deriving the cap by BUILDING fragments must be green | my reference does exactly that (accessor builds `_supersede_transaction` per K) — `G::TestParamNamesDoNotCollide…` GREEN in `1164 passed` | **FIXED** |
| **SD2** | D12 pins an unruled order | order now RULED (am-3 §2); K17r red, my backfill→heal reference green | **FIXED** |
| **SD3** | `claim_task` as a door | am-4/am-5: not a door; my typed-catch claim green on `_GUARDED_CAS_DOORS` (five) + `_TYPED_CAS_CATCHES` | **FIXED** (but see F5: only if written as `try/except`) |
**Verdict focus 1: all 18 predecessor MISSING PINS (MP1–MP18) and all 3 SAT DEFECTS are closed on the committed bytes** — every survivor re-killed on an independently-written reference; none survives.

### The new r2-instrument builds that were KILLED (focus 2, the rest of the list)
| build | attack | killed by | verdict |
|---|---|---|---|
| N9 | claim applies through a LOCAL ALIAS (`apply = self._apply`) and swallows `(TxnClaimLostError, TxnContentionExhaustedError)` — a (C)-escape attempt | `CR[claim_task]` + `CR::TestTheDrivenSetIsTheDerivedSet` (claim leaves the derived set — stale) + cross-check + `RS` typed set | **KILLED** — escape of an EXISTING verb is caught by the stale-driver direction (F8: not so for a NEW one) |
| N10 | claim catches bare `Exception` | `CR[claim_task]` + `RU::…catches_the_TYPE…` + `RS` door set + typed set + r1's claim-loud pin | **KILLED** |
| N11 | `TxnContentionExhaustedError` RE-PARENTED under `TxnDomainRejectionError` (the heal's typed catch now holds exhaustion) | `CR[_reanchor_stragglers]` + `RS` door set + typed set | **KILLED** — the class-keyed index flips BY DERIVATION, as am-5 promised |
| N12 | DEBUG for every THROW (not just claim-lost) | `RU::…CONTROL_a_lost_TRANSITION_race_still_logs_at_WARNING` | **KILLED** |
| N15 | packer post-check lets a chunk overflow | 7 reds (PR18r2, PR19, six-blocker, padding, domain-rejection …) | **KILLED** |
| N16 | heal isolates EVERY store fault (am-2's over-broad fail-open) | `RU::…every_heal_door…RAISES[store,transport]` + `CR[_reanchor_stragglers]` + `RS` door + typed | **KILLED** |
| N8 | packer uses a PRIVATE `sum(len(...))` counter | 0 reds (`1170 passed`) | **NOT A DEFECT** — am-3 §1 admits the compose-spy form ("the builder chooses"), and a private counter is behaviourally identical under every shell mutation; the one-counter property is name-dependent and unpinnable without naming it. Recorded so nobody believes it is pinned. |
| N14 | packer closes a chunk at `>= cap` (under-fills by one row) | 0 reds | **NOT A DEFECT** — benign direction (one row less per chunk); the dangerous direction (N15) is killed |
| N18 | transition retries its CAS ONCE in the ledger on a domain rejection (a hand-rolled retry, #102) | `RU::…CONTROL_a_lost_TRANSITION_race…` (two WARNINGs) + `RS` typed set + disjointness (transition now in both partitions) | **KILLED** |

### F11 — MISSING PIN (LOW — routing-not-sharing, MP13's sibling): "every RELATE comes from `_relate_fragment`" is pinned for the SUPERSEDE only
- **CLASS:** MP13 / K16 — ∀ task write verbs that compose a `blocks` RELATE (supersede, the boot heal, `create_task`, `create_many`), every RELATE statement composed is one `_relate_fragment` produced. r2's `RU::TestEveryRELATEComesFromTheSharedFragment` drives the supersede alone; `RU::TestEveryComposedGuardedWriteCameFromTheShell` (MP9) inspects only `UPDATE`/`UPSERT` statements, never `RELATE`.
- **Wrong build N17:** the heal hand-rolls its chunk's RELATE statements (`RELATE $hrN_a->blocks->$hrN_b`, its own RecordID params) beside the shared seam. **Receipt:** `N17 … 1170 passed, 1 skipped` — **0 reds, contract AND probes** (behaviourally identical today; that is exactly the routing-not-sharing shape: the day `_relate_fragment` changes — endpoint binding, direction, a dedupe — the heal does not).
- **The test that should exist:** GENERATE MP13 over every verb that composes a RELATE (the MP9 pin's own derived `_apply`-caller set + its drivers): spy `_relate_fragment` and `compose`, assert every composed `RELATE` statement was produced by the spy. Mutation proof: change `_relate_fragment`'s param naming → every verb's pin reds.
- **SIBLINGS TRIED:** supersede (K16 — killed), heal (N17 — survives). **NOT TRIED:** `create_task`/`create_many` (pre-58 verbs; same class, same pin generation fixes all).

## §P1b — QUANTIFIER TABLE (every invariant r2 adds or re-keys; ∀-over-inputs vs guarded; receipt on every row)
| # | invariant (ruling) | class | receipt |
|---|---|---|---|
| Q1 | every heal chunk ≤ `TXN_STATEMENT_HARD_CAP` (am-3 §1, packer BUILDS each row) | **GUARDED** — only one-superseded-entry rows at scale | N3 SURVIVES (boot fails at 1300 two-blocker rows) → **F1** |
| Q2 | the packer and the accessor consume one count (am-3 §1 v) | ∀ over shell changes (padding) | AM2L/N15 killed; N8 private counter passes — NOT A DEFECT (ruling admits it) |
| Q3 | a heal STORE fault at every heal door RAISES (am-3 §2) | ∀ — doors DERIVED by fault k = 1… until a boot completes, both fault classes | N16 killed (`…RAISES[store,transport]`); K17r killed (0 armed doors) |
| Q4 | a chunk's DOMAIN rejection is isolated + WARNING + next boot heals (am-3 §2) | one fixture (victim in chunk 1 of 2) — the other chunk position untried | N15/N16/K11r kill via it; door "isolate only the first chunk" NOT tried (stated) |
| Q5 | a phantom/cyclic chain head skips the WHOLE row, recorded every boot (am-3 §5) | **GUARDED** — single-superseded-entry rows only | N4/N5 SURVIVE → **F4** |
| Q6 | a claim loss is DEBUG; 0 alarm-level records for 7 losers (am-3 §3) | ∀ losers, but **GUARDED** to the `loremaster.store` loggers | N2 SURVIVES → **F3** |
| Q7 | every OTHER THROW-rooted rollback at WARNING (am-3 §3; am-6's table) | **GUARDED** — the transition lost race only | N1 SURVIVES → **F2**; am-6 W6a/W6b/W6d SURVIVE → **F9** |
| Q8 | the ledger catches the TYPE, never the text (am-3 §3) | ∀ — the re-type is made at the ONE mapping helper | N10 killed |
| Q9 | exhausted contention propagates UNREAD from every CAS verb (am-5 C) | **GUARDED** by a hand-listed module set + a one-method shape key | messages.py door, N20 new verb, floor_calibration guard drop — all GREEN → **F6/F7/F8** |
| Q10 | every CAS handler classified by caught CLASS (am-5 B) | **GUARDED** — `ast.Try` only, derived-verb scope | N6 (correct `suppress`) RED, N7 (correct extract) RED → **F5/F8**; N11 re-parent killed |
| Q11 | refuse only a cycle through X' (am-3 §4) | ∀ (loop + explicit + inherited controls) | WB9 + K4 killed |
| Q12 | `owner=` serves a held superseded row (am-2 a) | ∀ owner/status pair (two-row discriminator) | WB18 killed |
| Q13 | accessor == composed cap ∀ K (am-3 §1 iv) | ∀ floor classes K ∈ {0,1,2,3,per,per+1} | WB2 killed, WB2a control green |
| Q14 | every composed guarded write came from the shell (MP9) | ∀ derived `_apply` callers of `TaskLedger` (observed ⊇ derived) | WB12r, K7, K17r killed |
| Q15 | every RELATE via `_relate_fragment` (MP13) | **GUARDED** — supersede only | N17 SURVIVES → **F11** |
| Q16 | heal `count` = rows; `chunks` = composed heal txns | ∀ | WB3r, K11r, K9r killed |
| Q17 | order backfill → heal (am-3 §2) | ∀ (armed-door count + same-boot read) | K17r killed |
| Q18 | a single over-cap row RAISES typed (am-3 §1 rider) | **UNPINNED** | N19 SURVIVES → **F10** |
| Q19 | E11 whole-column dedupe (am-6 FORK-4) | **UNPINNED** (r2 predates am-6) | W6c SURVIVES → **F9** |

## §P1c — REACH TABLE (every guard / scan r2 introduces or relies on)
Legs: EMPIRICAL where marked (a build or an injected site in scratch, with its control); otherwise construction-inspection.
| instrument | set it covers | derived or hand-list? | coverage checked? | effect or proxy? | one source, proven by mutation? | verdict |
|---|---|---|---|---|---|---|
| `derive_cas_verbs` (the (B)+(C) population, `_reanchor_58_support`) | CAS verbs | per-method AST derivation INSIDE a HAND-LIST of modules (`SHELL_LEDGER_MODULES`) + a named door (`SINGLE_STATEMENT_CAS_DOORS`); keyed on the verb's own `self._apply` call | registry == derived both ways ✓ (N9, N7 red) — but no pin on the MODULE list | proxy (source) | two derivations of "task CAS verbs" disagree (`derive_cas_verbs` vs RU's `_apply_callers`) — N20 | **MISSING PIN** (EMPIRICAL: messages.py door green, F6; N20 green, F8; floor_calibration F7) |
| (C) `Injection` runtime ∀ (`CR`) | the derived verbs | inherits the above | ✓ both ways | **EFFECT** (reads/retries counted after the fault) | the injection is one class used by all 7 drivers | SAFE over what it runs (EMPIRICAL: N9/N10/N11/N16 red); reach = the row above |
| (B) `_classified_cas_handlers` (§HELD) | handlers of derived verbs | derived set; handlers only in `ast.Try` | exact typed + door sets ✓; non-vacuity ✓; unresolvable → loud ✓ | proxy | the ONE classifier is used by both exact-set pins ✓ | **MISSING PIN / SAT** (EMPIRICAL: N6 correct build red, F5; scope shrink vs HEAD, F6) |
| `_GUARDED_CAS_DOORS` / `_TYPED_CAS_CATCHES` | reviewer-visible lists | hand-lists, CHECKED against the derivation ✓ | ✓ | proxy | ✓ | SAFE as lists; blind outside the derivation's reach |
| RU MP9 runtime one-producer | every composed txn of every `TaskLedger` `_apply` caller | DERIVED (AST `_apply` callers) | observed ⊇ derived ✓ (N20 reds it) | **EFFECT** | ✓ (shell spied) | SAFE for writes; `UPDATE`/`UPSERT` only — RELATEs uncovered (F11) |
| `_HealDoors` (store faults at heal doors) | `_query`/`_apply` calls after the backfill | DERIVED by fault injection k = 1… | `doors == k−1 ≥ 2` ✓ | **EFFECT** | n/a | SAFE (EMPIRICAL: N16, K17r red); bound: a store call not via those two seams |
| `ComposeSpy.heal_calls` | heal chunks | keyed on a heal NOTE (actor/action) in the params | count == logged `chunks` ✓ | EFFECT | n/a | SAFE; bound: a heal chunk carrying no note (a DELETE-only chunk) is invisible |
| `measure_heal_shape` / `predicted_chunks` | heal cost model | MEASURED on 1/2/3 one-blocker rows, linearity checked | ✓ | EFFECT | n/a | **GUARDED** to one-blocker rows → F1 |
| claim-lost one-literal AST pin | string constants of every production tree | DERIVED (`parse_production_trees`) | floor: `_txn` exactly 1 | proxy | the marker IS two literals by ruling (tasks + `_txn`), both pinned | SAFE |
| G one-producer AST scan (widened, D13) | guarded-append producers | modules `rglob` ✓, constants referenced by name ✓ | floor + discriminators ✓ | proxy (+ MP9 effect twin) | ✓ | SAFE (EMPIRICAL: WB12r red); bound: a template returned by a HELPER call |
| `_log_rollback` tier (am-3 → am-6 table) | every rollback | am-3: THROW prefix; am-6: ONE table | **no pin generated over the tiers** | EFFECT (caplog) | am-6 (iii) mutation pin absent | **MISSING PIN** (EMPIRICAL: N1, W6a–d, F2/F9) |
| FAILS_LOUD forgery-door sweep (D, unedited) | every `ensure_ready` store door | DERIVED by seam identity | ✓ | EFFECT | n/a | SAFE (K17r/N16 red) |

## §P-PKG — my own package table FIRST, then the diff against the author's line
| mechanism r2 specifies or relies on | library evaluated | what I READ | verdict |
|---|---|---|---|
| **the heal packer** (am-3 §1: greedy; close the chunk when the next row would exceed the cap; a single over-cap row RAISES) | `more_itertools.constrained_batches` (**installed**, 11.1.0, in `uv.lock` transitively via `jaraco-classes`/`jaraco-functools` — NOT a declared loremaster dependency) | the installed source (`inspect.getsource`): `reached_size = item_len + batch_size > max_size` → yield the batch, then append; `strict=True` → `ValueError('item size exceeds maximum size')` for a single item over `max_size`; ran it: `[4,4,4,8,8]`, cap 10 → `[(4,4),(4,),(8,),(8,)]`, `[4,11]` → `ValueError` | **replace** — it IS am-3 §1's packer, verbatim, including the over-cap refusal (F10's rider): `constrained_batches(built_rows, TXN_STATEMENT_HARD_CAP, get_len=<the shared counter>, strict=True)`, `ValueError` → the typed packer error. Declare `more-itertools` as a direct dependency (pre-approved: project package). |
| AST scans (derive_cas_verbs, (B) classifier, one-literal, G) | `ast` (stdlib); `libcst` | `importlib.util.find_spec("libcst")` → not installed; `ast` covers what is needed | keep (stdlib) |
| the tier table (am-6) | `logging` (stdlib) | — | keep |
| the (C) injection / `_HealDoors` / `ComposeSpy` | `unittest.mock` | its `side_effect`/`wraps` could wrap a seam but not count reads AFTER a fault across two seams | bespoke test instruments — keep |
| cycle detection (am-3 §4, unchanged r1) | `networkx` (already used by `_refuse_a_cycle` / backfill) | the existing reuse | keep (reused) |
- **DIFF vs the author's line** (*"no library provides the heal packer (arithmetic over `compose`'s own count)"*) and vs the ruling's (*"Packages considered: none (the packer is arithmetic over compose's own count)"*): **both assert a limitation without reading an installed API** — `constrained_batches` is on the venv, does exactly the greedy close-before-overflow + strict single-item refusal the ruling specifies, and the one piece that is genuinely ours is `get_len` (the shared counter). **P-PKG FINDING (MEDIUM): the packer should be `more_itertools.constrained_batches`, not hand-rolled** — BC-r2-2 / the ruling currently instruct the builder to hand-roll it. Not a contract pin (a contract cannot demand a library), but a BUILDER CONSTRAINT / ruling correction the lead should issue before the build, since a builder follows the spec as written.

## §P-PORT
`Odoo-20 portability: n/a — no Odoo seam touched` (lore repo; no Odoo model, field, view or ORM path in the contract, fixtures or my probes). Author's line: the same. Diff: none.

## §SAT — focus 4: plain HEAD + §HELD + MY independent reference, full suite, every red adjudicated against a HEAD baseline on the same tree (2026-09-26)
- **Tree** `scratch/ref` = HEAD `1a67b98` (code-identical to `c42eeaf` and to `6417e8f`) + §HELD parts 1–3 (md5-verified, §REF) + `build_ref58.py` + `my_ref.py` (am-3/am-5 reference, md5 `tasks.py 5b4ecba9…`, `_txn.py ca86524a…`). My probe file excluded (`--ignore`). Runner `sat.sh` (pasted): waits for ≥24 GB free, `-n 8` (concurrent lore sessions live — lead #17068 cap is 12), 15 GB process-TREE watchdog (`run.sh`) — attempt 1 completed, watchdog did not fire. Provenance printed: `loremaster.__file__ = …/f2fe3a36-…/scratchpad/ref/loremaster/loremaster/__init__.py`.
- **Tail: `45 failed, 11899 passed, 62 skipped, 3 xfailed, 9 warnings in 929.28s (0:15:29)`**.
- **Every red adjudicated:** all 45 are in packet 63c-i-a's contract-ahead files — `test_fixwave_a28_63c_i_a.py` ×41, `test_fixwave_a19a_63c_i_a.py` ×2, `test_fixwave_a19b_63c_i_a.py` ×2 (committed at `d334042`, AFTER the author's SAT base `43b8d16` — which is why the author never saw them). **Baseline on the same files at plain HEAD** (`scratch/head`, no §HELD, no build): `45 failed, 95 passed` — `comm` of the two red sets: **sat-only = ∅, base-only = ∅** (identical 45). All three files are registered to `packet-63c-i-a-a28-contract` in the COMMITTED `scripts/pending_contracts.yaml` (`6417e8f`). ⇒ **UNRELATED, owned, pre-existing — 0 reds attributable to the 58 contract, §HELD, or my reference.** No `test_migration_wire.py` red (lead #17076's #503 shape did not occur); no `Resource busy` line (#486 not observed).
- **The author's claim re-derived** (`2 failed, 11859 passed` → both reds the §HELD part-3 ruling-vs-pin collision): on my reference with part 3 REVERTED, `test_surreal_store.py::TestDomainRejectionErrorType` → `FAILED …governed_conflict_throw…[execute_transaction]`, `FAILED …[execute_read_transaction]`, `2 failed, 6 passed`; with part 3 (committed state) `8 passed`; plain HEAD `8 passed`. **REPRODUCED on an independent reference** — the collision is a property of am-3 §3 (any correct build moves a THROW rollback off ERROR), not of either reference. (Under am-6 the governed conflict is WARNING; part 3's DEBUG capture stays correct.)
- **Lint leg:** `ruff check` over the 13 contract files + `_reanchor_58_support.py` + `_task_fakes.py` on the built tree → `All checks passed!`. (My reference's own production lint — six E501 — is my scratch build's, not the contract's.) typecheck not re-run (the author's SAT leg reports every `typecheck.sh` leg OK on a built tree; I did not reproduce it — stated).
- **am-6 SAT:** `REF6_control_no_edit` (my reference + am-6 deltas) → the whole r2 scope + all my probes `1179 passed` — r2 is satisfiable by an am-6-faithful build (§A F9).
- **Verdict focus 4: SAT CONFIRMED — 0 attributable failures on plain HEAD + §HELD + an independent reference.**

## §RESIDUALS — every item, individual verdict
| # | item | verdict |
|---|---|---|
| RS-1 | r1's `S::TestTheHubBoundIsDERIVED::test_MUTATION_…` pads with `RETURN NONE` (#497/#501): every padded supersede in `_derive` is TRUNCATED after the stamp shell (the stamp commits; the successor CREATE never runs) — the pin measures compose-time counts, so its verdict is right | NOT A DEFECT of the verdict; the pin leaves phantom successors in its own throwaway DB. Author's F-r2-4 (use `LET $pad = NONE`) confirmed; #501 (`compose` should refuse a top-level RETURN) is the real fix |
| RS-2 | WB17r (unbounded chain follow): `asyncio.wait_for(…, 60)` in PR15/RU cannot cancel a SYNCHRONOUS loop — the suite HANGS instead of going red | LOW — the kill is real but only visible as a hung run (this repo has no CI timeout). Suggest `pytest-timeout` (a `@pytest.mark.timeout(120)` with the thread method) on those two pins, or boot in a subprocess |
| RS-3 | author's §RED@HEAD prose enumerates 46 of r2's 50 new reds (24+11+6+4+1) | report-arithmetic nit; the count (50) and total (119) reproduce |
| RS-4 | `_GUARDED_CAS_RE_READ = "_select"` left defined and unused by §HELD part 2 | corpse (F6) |
| RS-5 | `CR::TestTheRuntimeSetAndTheStaticIndexAgree` asserts `driven ⊆ classified-by-FUNCTION`, so a driven verb with no `try` at all reds (am-5 §3 says "a driven verb whose `try` the scanner did not enumerate") | NOT A DEFECT today (all 7 verbs have handlers); over-tight in the F5 direction — a verb that legitimately needs no handler would red |
| RS-6 | `derive_cas_verbs` builds `calls` keyed by bare method NAME across every class in a module — two classes with a same-named method merge | LOW, latent (tasks.py/findings.py have one ledger class each); goes wrong the day a module holds two ledgers |
| RS-7 | the am-3 §2 chunk-rejection pin has ONE fixture position (victim in chunk 1 of 2) | NOT A DEFECT — every isolation build I built was killed there (N15/N16/K11r); "isolate only the first chunk" untried, stated |
| RS-8 | `claim_task` keeps an unused `_still_claimable` helper in my/the predecessor's reference | reference hygiene only, not the contract's |
| RS-9 | `scripts/esc1_write_path_cycle_closure.py` run red since #174 (author F-r2-1, predecessor R2) | UNRELATED, pre-existing, still unowned — flagged to the lead again |
| RS-10 | author's FORK-1..4: FORK-1/2 ruled (am-4/am-5, CONFIRMED in bytes); FORK-3/4 ruled by am-6 (F9) | closed by rulings |
| RS-11 | my own P0 slips, stated: (a) a first `sed` positive control on the AST context instrument hit every line (empty anchor) — discarded, redone as a single-binding rebind (10 differ); (b) one `-k` filter deselected the CR pins I meant to run — caught (`662 deselected`), re-run separately; (c) two builds (N2, and the HEAD baseline full run) were killed by MY 15 GB watchdog under host memory pressure — the driver was then made to retry, N2 re-ran clean; the HEAD full-suite baseline was replaced by the same-file baseline in §SAT (the only reds needing adjudication); (d) WB12r's declaration named PR9 (a synthetic-source pin that cannot red on a build) — observed kill came from G | disclosed |
| RS-12 | `/tmp/_x` — one stray `cp` to `/tmp` during setup | removed immediately (`rm -f /tmp/_x`) |

## §INSTRUMENTS — pasted VERBATIM (brief-base §1; scratch root `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/f2fe3a36-cb3f-47ec-b8ed-14e14fdbedea/scratchpad/` is session-local — hence pasted)
Re-run recipe: `./scripts/scratch_copy.sh <dest>` → `git checkout -- . && git clean -fd -e .venv` → `git apply` §HELD parts 1–3 (extracted from `5a43aeb:REPORT-contract-58.md` lines 173–557 and `c42eeaf:REPORT-contract-58-r2.md` lines 177–195 / 200–450) → `build_ref58.py` (from `9f2f580:REPORT-adversary-58.md`) → `my_ref.py` (→ `my_ref_am6.py` for ref6) → commit in the copy → copy the probe files into `loremaster/tests/` → `wb_r2adv.py <copy> <out> [builds]` / `wb6.py` / `sat.sh`. `files58.txt` = the 13 scope paths listed in §A. The reach-door and N20 edits are the inline Python heredocs shown in F6/F8's receipts, reproduced at the end.

### `my_ref.py` (md5 `de2d2801b2be91bf86b23250827e5a60`)
```python
#!/usr/bin/env python3
"""adversary-58-r2's OWN amendment-3/5 reference deltas — applied OVER adversary-58's build_ref58.py
(md5 5915c12e, 9f2f580:REPORT-adversary-58.md §INSTRUMENTS) in a SCRATCH copy.  Written WITHOUT reading
contract-58-r2's build_ref58_r2.py (independence: two references, two authors).

Usage: my_ref.py <scratch-root>.  Every edit asserts its anchor occurs EXACTLY once (#194).
"""
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
TASKS = ROOT / "loremaster/loremaster/tasks.py"
TXN = ROOT / "loremaster/loremaster/store/_txn.py"


def sub(src: str, old: str, new: str) -> str:
    count = src.count(old)
    assert count == 1, f"anchor occurs {count}x: {old[:80]!r}"
    return src.replace(old, new)


# ------------------------------------------------------------------ _txn.py (am-3 §3)
txn = TXN.read_text()
txn = sub(
    txn,
    "class RetryableConflictSignal(Exception):",
    '''class TxnClaimLostError(TxnDomainRejectionError):
    """A task claim's guarded CAS matched zero rows and THREW the claim-lost marker (packet 58 am-3 §3).

    A routine outcome (the fleet's commonest contention result), served by the ledger as a
    ``ClaimResult``; logged at DEBUG by :func:`_log_rollback`.  A DOMAIN rejection — it can never hold
    exhausted contention (a sibling subtree of :class:`TxnContentionExhaustedError`).
    """


class RetryableConflictSignal(Exception):''',
)
txn = sub(
    txn,
    '_ERROR_CLASS_UNSPECIFIED = "unspecified rejection"',
    '_ERROR_CLASS_CLAIM_LOST = "claim lost — another claimant won the compare-and-set"\n'
    '_ERROR_CLASS_UNSPECIFIED = "unspecified rejection"',
)
txn = sub(
    txn,
    '_GOVERNED_CONFLICT_MARKER = "governed_conflict:"\n',
    '_GOVERNED_CONFLICT_MARKER = "governed_conflict:"\n'
    "# packet 58 am-3 §3: the claim shell's THROW prefix — the ONE copy of the marker in this module.\n"
    'CLAIM_LOST_MARKER = "claim_lost:"\n'
    "# The engine's rendering of an application THROW (probed 3.2.4: `THROW 'x'` -> 'An error occurred: x').\n"
    '_THROW_RESULT_PREFIX = "an error occurred:"\n',
)
txn = sub(
    txn,
    "    if _GOVERNED_CONFLICT_MARKER in lowered:\n        return _ERROR_CLASS_GOVERNED_CONFLICT\n",
    "    if _GOVERNED_CONFLICT_MARKER in lowered:\n        return _ERROR_CLASS_GOVERNED_CONFLICT\n"
    "    if CLAIM_LOST_MARKER in lowered:\n        return _ERROR_CLASS_CLAIM_LOST\n",
)
txn = sub(
    txn,
    "    if error_class == _ERROR_CLASS_GOVERNED_CONFLICT:\n        return TxnGovernedConflictError(message)\n",
    "    if error_class == _ERROR_CLASS_GOVERNED_CONFLICT:\n        return TxnGovernedConflictError(message)\n"
    "    if error_class == _ERROR_CLASS_CLAIM_LOST:\n        return TxnClaimLostError(message)\n",
)
txn = sub(
    txn,
    '''    contention-exhausted raise, so both carry the identical receipt shape.
    """
    logger.error(
        "store.transaction.rolled_back",''',
    '''    contention-exhausted raise, so both carry the identical receipt shape.

    Level (packet 58 am-3 §3): a claim-lost rollback DEBUG; any other APPLICATION-THROW-rooted rollback
    WARNING; everything else (engine refusals, exhausted contention) ERROR.
    """
    text = str(root_cause.raw_result).lower()
    if CLAIM_LOST_MARKER in text:
        level = logging.DEBUG
    elif text.startswith(_THROW_RESULT_PREFIX) and not _is_retryable_conflict_text(text):
        level = logging.WARNING
    else:
        level = logging.ERROR
    logger.log(
        level,
        "store.transaction.rolled_back",''',
)
assert "\nimport logging" in txn
TXN.write_text(txn)

# ------------------------------------------------------------------ tasks.py
src = TASKS.read_text()
src = sub(
    src,
    "    TxnContentionExhaustedError,\n    TxnFragment,\n",
    "    TxnClaimLostError,\n    TxnContentionExhaustedError,\n    TxnDomainRejectionError,\n    TxnFragment,\n",
)
# am-3 §3: the claim THROW carries the typed marker (ONE literal here).
src = sub(
    src,
    '_CLAIM_LOST_MESSAGE = "task claim lost its compare-and-set"',
    '_CLAIM_LOST_PREFIX = "claim_lost:"',
)
src = sub(src, "            throw_message=_CLAIM_LOST_MESSAGE,", "            throw_message=f\"{_CLAIM_LOST_PREFIX}{task_id}\",")
# ... and claim catches the TYPE (am-3 §3 / am-5: any body; the owner read after the try, as today).
src = sub(
    src,
    """        try:
            await self._apply([self._claim_fragment(task_id, owner, blocked_by, event)])
        except SurrealConnectionError:
            raise
        except TxnContentionExhaustedError:
            raise
        except SurrealStoreError:
            fresh = await self._select_row(task_id)
            if fresh is None:
                raise
            if await self._still_claimable(fresh, blocked_by):
                raise
""",
    """        try:
            await self._apply([self._claim_fragment(task_id, owner, blocked_by, event)])
        except TxnClaimLostError:
            pass  # a routine loss (am-3 §3) — the owner read below decides the verdict
""",
)
# am-3 §2: order RULED backfill -> heal.
src = sub(
    src,
    "        await self._reanchor_stragglers()\n        await self._backfill_blocks_edges()\n",
    "        await self._backfill_blocks_edges()\n        await self._reanchor_stragglers()\n",
)
# am-3 §1: ONE counting function, consumed by the accessor AND the heal packer.
src = sub(
    src,
    """            return sum(len(fragment.statements) for fragment in fragments)

        fixed = _count(0)""",
    """            return TaskLedger._composed_statement_count(fragments)

        fixed = _count(0)""",
)
src = sub(
    src,
    "    def max_reanchor_dependents(self, successor_blocked_by_count: int) -> int:",
    '''    @staticmethod
    def _composed_statement_count(fragments: Sequence[TxnFragment]) -> int:
        """The body-statement count ``compose`` checks against ``TXN_STATEMENT_HARD_CAP`` — the ONE counter."""
        return sum(len(fragment.statements) for fragment in fragments)

    def max_reanchor_dependents(self, successor_blocked_by_count: int) -> int:''',
)
# The heal, rewritten (am-3 §1/§2/§5): phantom + cycle skip-and-record, per-row fragments, greedy packer by
# the shared count, a chunk's DOMAIN rejection isolated + WARNING, every store fault propagates.
start = src.index("    async def _reanchor_stragglers(self) -> None:")
end = src.index("    @staticmethod\n    def _supersede_fragment(")
src = src[:start] + '''    async def _reanchor_stragglers(self) -> None:
        """Boot heal (am-1 R2 / am-3): re-anchor every row still naming a superseded task, in greedy
        chunks sized by the heal's OWN composed count; a store fault RAISES; a chunk's domain rejection
        is isolated + WARNING; a phantom or cyclic chain head skips the WHOLE row, recorded every boot."""
        rows = self._as_rows(
            await self._query(
                f"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_SUPERSEDED_BY} FROM {TASK_TABLE} "
                f"WHERE {_COL_SUPERSEDED_BY} IS NOT NONE"
            )
        )
        successor = {str(r.get(_ID_KEY)): str(r.get(_COL_SUPERSEDED_BY)) for r in rows}
        if not successor:
            return
        stragglers = self._as_rows(
            await self._query(
                f"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_BLOCKED_BY} FROM {TASK_TABLE} "
                f"WHERE {_COL_BLOCKED_BY} CONTAINSANY $hs_ids",
                {"hs_ids": sorted(successor)},
            )
        )
        if not stragglers:
            return

        def _walk(start: str) -> tuple[str | None, bool]:
            """(chain head, cycled?) — bounded by the chain's own length."""
            seen = {start}
            current = successor[start]
            while current in successor:
                if current in seen:
                    return None, True
                seen.add(current)
                current = successor[current]
            return current, False

        heads = {old: _walk(old) for old in successor}
        existing = set(
            await resolve_existing_rows(
                self._query, TASK_TABLE, sorted({h for h, cyc in heads.values() if h is not None})
            )
        )
        at = datetime.now(UTC).isoformat()
        built: list[tuple[str, list[TxnFragment], list[tuple[str, str]], int]] = []
        for row_index, straggler in enumerate(stragglers):
            dependent = str(straggler.get(_ID_KEY))
            columns = [str(b) for b in (straggler.get(_COL_BLOCKED_BY) or ())]
            olds = list(dict.fromkeys(b for b in columns if b in successor))
            skip = False
            for old in olds:
                head, cycled = heads[old]
                if cycled:
                    logger.warning(
                        _HEAL_CYCLE_EVENT,
                        extra={"database": self._database, "task_id": dependent, "blocker_id": old},
                    )
                    skip = True
                    break
                if head not in existing:
                    logger.warning(
                        _HEAL_PHANTOM_EVENT,
                        extra={
                            "database": self._database, "task_id": dependent,
                            "blocker_id": old, "phantom_head_id": head,
                        },
                    )
                    skip = True
                    break
            if skip:
                continue
            final = list(columns)
            pairs: list[tuple[str, str, str]] = []
            relates: list[tuple[str, str]] = []
            for old in olds:
                head = cast("str", heads[old][0])
                pairs.append((dependent, old, head))
                if head not in final and (head, dependent) not in relates:
                    relates.append((head, dependent))
                final = list(dict.fromkeys(head if b == old else b for b in final))
            fragments = [
                TxnFragment(
                    statements=[
                        f"DELETE {BLOCKS_RELATION} WHERE in = $hd{row_index}_{i}_in AND out = $hd{row_index}_out"
                        for i in range(len(olds))
                    ],
                    params={
                        f"hd{row_index}_out": RecordID(TASK_TABLE, dependent),
                        **{f"hd{row_index}_{i}_in": RecordID(TASK_TABLE, old) for i, old in enumerate(olds)},
                    },
                ),
                *self._reanchor_fragments(
                    pairs, actor=_HEAL_ACTOR, at=at, reason=_HEAL_REASON, prefix=f"h{row_index}r"
                ),
            ]
            cost = self._composed_statement_count([*fragments, self._relate_fragment(relates)])
            built.append((dependent, fragments, relates, cost))
        cap = _txn_module.TXN_STATEMENT_HARD_CAP
        chunks: list[list[tuple[str, list[TxnFragment], list[tuple[str, str]], int]]] = []
        current: list[tuple[str, list[TxnFragment], list[tuple[str, str]], int]] = []
        used = 0
        for entry in built:
            if entry[3] > cap:
                raise StragglerHealPackerError(
                    f"straggler {render_attributed(entry[0])} alone composes {entry[3]} statements, over the "
                    f"{cap}-statement transaction cap — the heal cannot pack it"
                )
            if current and used + entry[3] > cap:
                chunks.append(current)
                current, used = [], 0
            current.append(entry)
            used += entry[3]
        if current:
            chunks.append(current)
        healed = 0
        for chunk_index, chunk in enumerate(chunks):
            fragments = [f for entry in chunk for f in entry[1]]
            fragments.append(self._relate_fragment([pair for entry in chunk for pair in entry[2]]))
            try:
                await self._apply([f for f in fragments if f.statements])
            except TxnDomainRejectionError:
                logger.warning(
                    _HEAL_CHUNK_REJECTED_EVENT,
                    extra={
                        "database": self._database, "chunk": chunk_index,
                        "rows": [entry[0] for entry in chunk],
                    },
                )
                continue
            healed += len(chunk)
        if healed:
            logger.info(
                _HEAL_EVENT, extra={"database": self._database, "count": healed, "chunks": len(chunks)}
            )

''' + src[end:]
src = sub(
    src,
    '_HEAL_SKIPPED_EVENT = "task.backfill.straggler_skipped"',
    '_HEAL_PHANTOM_EVENT = "task.backfill.straggler_phantom_head"\n'
    '_HEAL_CYCLE_EVENT = "task.backfill.straggler_chain_cycle"\n'
    '_HEAL_CHUNK_REJECTED_EVENT = "task.backfill.straggler_chunk_rejected"',
)
src = sub(
    src,
    "class HubSupersedeRefusedError(TaskLedgerError):",
    '''class StragglerHealPackerError(TaskLedgerError):
    """A single straggler row composes more statements than one transaction may carry (am-3 §1)."""


class HubSupersedeRefusedError(TaskLedgerError):''',
)
TASKS.write_text(src)
print("adversary-58-r2 reference deltas applied:", TASKS, TXN)
```

### `my_ref_am6.py` (md5 `2176fb8e7ff7f0160d71a52c4c9e2f23`)
```python
#!/usr/bin/env python3
"""adversary-58-r2: the amendment-6 (dcf6b0f) deltas over my own reference (my_ref.py) — FORK-3's ONE
prefix-marker tier table in `_txn` (deny-by-default ERROR) + the ledgers' THROW constants prefixed.  FORK-4
(whole-column distinct) is already the reference's spelling.  Usage: my_ref_am6.py <scratch-root>."""
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
TASKS = ROOT / "loremaster/loremaster/tasks.py"
TXN = ROOT / "loremaster/loremaster/store/_txn.py"
FINDINGS = ROOT / "loremaster/loremaster/findings.py"


def sub(src: str, old: str, new: str) -> str:
    count = src.count(old)
    assert count == 1, f"anchor occurs {count}x: {old[:80]!r}"
    return src.replace(old, new)


txn = TXN.read_text()
txn = sub(
    txn,
    "# The engine's rendering of an application THROW",
    "# packet 58 am-6 FORK-3: the ONE app-THROW tier table — keyed on WHO decided the rollback; anything\n"
    "# unrecognised is ERROR (deny-by-default).\n"
    "_CAS_LOST_MARKER = \"cas_lost:\"\n"
    "_REANCHOR_STRAGGLER_MARKER = \"reanchor_straggler:\"\n"
    "_HEAL_CHUNK_MARKER = \"heal_chunk:\"\n"
    "_ROLLBACK_LOG_TIERS: dict[str, int] = {\n"
    "    CLAIM_LOST_MARKER: logging.DEBUG,\n"
    "    _GOVERNED_CONFLICT_MARKER: logging.WARNING,\n"
    "    _CAS_LOST_MARKER: logging.WARNING,\n"
    "    _REANCHOR_STRAGGLER_MARKER: logging.WARNING,\n"
    "    _HEAL_CHUNK_MARKER: logging.WARNING,\n"
    "}\n"
    "# The engine's rendering of an application THROW",
)
txn = sub(
    txn,
    """    text = str(root_cause.raw_result).lower()
    if CLAIM_LOST_MARKER in text:
        level = logging.DEBUG
    elif text.startswith(_THROW_RESULT_PREFIX) and not _is_retryable_conflict_text(text):
        level = logging.WARNING
    else:
        level = logging.ERROR
""",
    """    text = str(root_cause.raw_result).lower()
    thrown = text[len(_THROW_RESULT_PREFIX):].strip() if text.startswith(_THROW_RESULT_PREFIX) else ""
    level = next(
        (tier for prefix, tier in _ROLLBACK_LOG_TIERS.items() if thrown.startswith(prefix)), logging.ERROR
    )
""",
)
TXN.write_text(txn)

src = TASKS.read_text()
src = sub(src, '_REANCHOR_LOST_MESSAGE = "a dependent no longer names the superseded task"',
          '_REANCHOR_LOST_MESSAGE = "cas_lost: a dependent no longer names the superseded task"\n'
          '_HEAL_CHUNK_MESSAGE = "heal_chunk: a straggler no longer names its superseded blocker"')
src = sub(src, '_STRAGGLER_MESSAGE = "a dependent of the superseded task appeared after the dependents read"',
          '_STRAGGLER_MESSAGE = "reanchor_straggler: a dependent of the superseded task appeared after the dependents read"')
src = sub(src, '_SUPERSEDE_ALREADY_MESSAGE = "task is already superseded"',
          '_SUPERSEDE_ALREADY_MESSAGE = "cas_lost: task is already superseded"')
src = sub(src, '_TRANSITION_ALREADY_MESSAGE = "task transition lost a concurrent compare-and-set"',
          '_TRANSITION_ALREADY_MESSAGE = "cas_lost: task transition lost a concurrent compare-and-set"')
src = sub(src, '        reason: str | None = None,\n        prefix: str = "ra",\n',
          '        reason: str | None = None,\n        prefix: str = "ra",\n        throw_message: str = _REANCHOR_LOST_MESSAGE,\n')
src = sub(src, "                    throw_message=_REANCHOR_LOST_MESSAGE,\n", "                    throw_message=throw_message,\n")
src = sub(src, 'reason=_HEAL_REASON, prefix=f"h{row_index}r"\n',
          'reason=_HEAL_REASON, prefix=f"h{row_index}r",\n                    throw_message=_HEAL_CHUNK_MESSAGE,\n')
TASKS.write_text(src)

fnd = FINDINGS.read_text()
fnd = sub(fnd, '_TRANSITION_ALREADY_MESSAGE = "finding transition lost a concurrent compare-and-set"',
          '_TRANSITION_ALREADY_MESSAGE = "cas_lost: finding transition lost a concurrent compare-and-set"')
FINDINGS.write_text(fnd)
print("am-6 deltas applied")
```

### `wb_r2adv.py` (md5 `12248cdafe5bd963081c39bbd4c3ef47`)
```python
#!/usr/bin/env python3
"""adversary-58-r2 wrong-build driver — declare-then-diff, both ways.

Usage: wb_r2adv.py <scratch-root> <out-dir> [build ...]      (no builds = all, in BUILDS order)

Each build = exact-once substitutions over the reference commit in the scratch repo (every anchor asserted
to occur EXACTLY once and every edited file asserted CHANGED — the mutation LANDED, #194), then the SCOPE
(every 58 contract file + §HELD's test_retry_seam + D + the adversary probe file) is run under the
15 GB tree-kill watchdog (run.sh).  Modes:
  exact    observed contract reds == declared (both ways)
  include  declared ⊆ observed (extra reds listed, not failing)
  survive  ZERO contract reds AND the declared PROBE ids red  (a surviving wrong build = a MISSING PIN)
  observe  record the reds (a CORRECT-build shape probe: any contract red is a SAT finding)
  hang     the run must not complete within HANG_SECONDS
After each build the tree is restored with `git checkout -- .` and the reference md5s re-asserted.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
OUT = Path(sys.argv[2])
SCRATCH = Path(__file__).resolve().parent
SCOPE = [line.strip() for line in (SCRATCH / "files58.txt").read_text().splitlines() if line.strip()]
PROBES = "loremaster/tests/test_adv58r2_probes.py"
T, X = "loremaster/loremaster/tasks.py", "loremaster/loremaster/store/_txn.py"
REF_MD5 = {T: "5b4ecba9da51acb1e67e9c6ff6cf6503", X: "ca86524a70032e166bb1ce47b922e386"}
HANG_SECONDS = 900

HEAL_TRY = """            try:
                await self._apply([f for f in fragments if f.statements])
            except TxnDomainRejectionError:
"""

B: dict[str, dict] = {}


def build(name: str, mode: str, declared: list[str], *edits: tuple[str, str, str]) -> None:
    B[name] = {"mode": mode, "declared": declared, "edits": list(edits)}


# ---------------- prior survivors (adversary-58), verbatim anchors where they apply -------------------
# (the verbatim ones are loaded from adversary-58's wrong_builds.py, md5 790e0309, at run time)
VERBATIM = {
    "WB1_launder_any_rollback_as_R1": ("include", ["test_PR1_"]),
    "WB2a_legit_two_statement_R1_guard": ("exact", []),
    "WB2_cap_ignores_K_on_the_legit_layout": ("include", ["test_PR2_", "test_PR16_"]),
    "WB7_130_client_side_postfilter": ("include", ["test_PR6_"]),
    "WB8_reblocked_done_only": ("include", ["test_PR7_"]),
    "WB9_cycle_minted_all_pending": ("include", ["test_PR8_", "test_the_legacy_loop_is_untouched"]),
    "WB14_warn_threshold_cloned": ("include", ["test_PR13_"]),
    "WB15_literal_hard_cap_copy": ("include", ["test_PR14_"]),
    "WB16_note_at_constant": ("include", ["test_PR12_"]),
    "K16_dependent_relates_hand_rolled": ("include", ["TestEveryRELATEComesFromTheSharedFragment"]),
    "WB18_owner_filter_excludes_superseded": ("include", ["test_PR20_"]),
    "K4_cycle_over_unrewired_graph": ("include", ["test_CONTROL_a_successor_explicitly", "test_CONTROL_an_INHERITED"]),
    "K7_reanchor_private_clone_not_shell": ("include", []),
    "K10_heal_stops_at_first_hop": ("include", []),
}

# ---------------- prior survivors re-expressed over MY heal (their anchors named the am-1 heal) --------
build("WB3r_heal_counts_pairs", "include", ["test_PR3_"],
      (T, "            healed += len(chunk)\n", "            healed += sum(len(entry[1]) - 1 for entry in chunk)\n"))
build("WB4r_heal_first_blocker_only", "include", ["test_PR3_"],
      (T, "            olds = list(dict.fromkeys(b for b in columns if b in successor))\n",
       "            olds = list(dict.fromkeys(b for b in columns if b in successor))[:1]\n"))
build("WB5r_heal_relate_without_dedupe", "include", ["test_PR4_"],
      (T, "                if head not in final and (head, dependent) not in relates:\n", "                if True:\n"))
build("WB6r_heal_no_phantom_head_check", "include", ["TestAPhantomChainHeadIsSkippedAndRECORDED"],
      (T, "                if head not in existing:\n", "                if False:\n"))
build("WB12r_fourth_clone_module_level_guard", "include", ["test_PR9_"],
      (T, '_CLAIM_LOST_PREFIX = "claim_lost:"\n',
       '_CLAIM_LOST_PREFIX = "claim_lost:"\n_ASSIGN_GUARD_FMT = "IF array::len(${var}) == 0 {{ THROW \'{msg}\' }}"\n'),
      (T, "    async def _reanchor_stragglers(self) -> None:\n",
       '''    @staticmethod
    def _assign_fragment(task_id: str, owner: str) -> TxnFragment:
        """WB12r: a 57-shaped 4th hand-rolled guarded append whose guard lives in a module constant."""
        return TxnFragment(
            statements=[
                f"LET $asg_upd = (UPDATE type::record('{TASK_TABLE}', $asg_id) SET owner = $asg_owner, "
                f"{_COL_PROVENANCE}.{_PROV_EVENTS} += [$asg_ev])",
                _ASSIGN_GUARD_FMT.format(var="asg_upd", msg="assign lost"),
            ],
            params={"asg_id": task_id, "asg_owner": owner, "asg_ev": {}},
        )

    async def _reanchor_stragglers(self) -> None:
'''))
build("WB17r_heal_unbounded_chain_follow", "hang", [],
      (T, "                if current in seen:\n                    return None, True\n", ""))
build("WB17b_cycle_member_treated_as_head", "include", ["TestASupersededByCycleIsBoundedAndRECORDED"],
      (T, "                if current in seen:\n                    return None, True\n",
       "                if current in seen:\n                    return current, False\n"))
build("K9r_heal_logs_every_boot", "include", [],
      (T, "        if not stragglers:\n            return\n\n        def _walk", "\n        def _walk"),
      (T, "        if healed:\n            logger.info(", "        if True:\n            logger.info("))
build("K11r_heal_counts_heads", "include", [],
      (T, "            healed += len(chunk)\n",
       "            healed += len({pair[0] for entry in chunk for pair in entry[2]}) or len(chunk)\n"))
build("K17r_heal_before_backfill", "include", ["test_the_heal_READS_what_the_backfill_minted"],
      (T, "        await self._backfill_blocks_edges()\n        await self._reanchor_stragglers()\n",
       "        await self._reanchor_stragglers()\n        await self._backfill_blocks_edges()\n"))
build("AM2L_amendment2_literal_row_chunks", "include", ["test_PR18r2_", "test_PR19_"],
      (T, "            if current and used + entry[3] > cap:\n",
       "            if current and len(current) >= self.max_reanchor_dependents(0):\n"))

# ---------------- NEW wrong builds against r2's instruments (focus 2) ---------------------------------
build("N1_warning_only_for_the_transition_text", "survive", ["test_PA1_", "test_PA2_"],
      (X, "    elif text.startswith(_THROW_RESULT_PREFIX) and not _is_retryable_conflict_text(text):\n",
       "    elif \"transition lost\" in text:\n"))
build("N2_claim_loss_WARNED_by_the_ledger", "survive", ["test_PB_"],
      (T, "            pass  # a routine loss (am-3 §3) — the owner read below decides the verdict\n",
       "            logger.warning(\"task.claim.lost\", extra={\"task_id\": task_id, \"owner\": owner})\n"))
build("N3_packer_prices_every_row_like_a_one_blocker_row", "survive", ["test_PC_"],
      (T, "        cap = _txn_module.TXN_STATEMENT_HARD_CAP\n        chunks: list",
       "        cap = _txn_module.TXN_STATEMENT_HARD_CAP\n"
       "        unit = self._composed_statement_count([\n"
       "            TxnFragment(statements=[f\"DELETE {BLOCKS_RELATION} WHERE in = $u_in AND out = $u_out\"], params={}),\n"
       "            *self._reanchor_fragments([(\"u\", \"o\", \"h\")], actor=_HEAL_ACTOR, at=at, prefix=\"unit\"),\n"
       "            self._relate_fragment([(\"h\", \"u\")]),\n"
       "        ])\n"
       "        built = [(e[0], e[1], e[2], unit) for e in built]\n"
       "        chunks: list"))
build("N4_phantom_head_skips_only_its_ENTRY", "survive", ["test_PD1_"],
      (T, """                if head not in existing:
                    logger.warning(
                        _HEAL_PHANTOM_EVENT,
                        extra={
                            "database": self._database, "task_id": dependent,
                            "blocker_id": old, "phantom_head_id": head,
                        },
                    )
                    skip = True
                    break
            if skip:
                continue
""", """                if head not in existing:
                    logger.warning(
                        _HEAL_PHANTOM_EVENT,
                        extra={
                            "database": self._database, "task_id": dependent,
                            "blocker_id": old, "phantom_head_id": head,
                        },
                    )
                    olds = [o for o in olds if o != old]
                    break
            if skip or not olds:
                continue
"""))
build("N5_cyclic_chain_skips_only_its_ENTRY", "survive", ["test_PD2_"],
      (T, """                        extra={"database": self._database, "task_id": dependent, "blocker_id": old},
                    )
                    skip = True
                    break
""", """                        extra={"database": self._database, "task_id": dependent, "blocker_id": old},
                    )
                    olds = [o for o in olds if o != old]
                    break
"""),
      (T, "            if skip:\n                continue\n", "            if skip or not olds:\n                continue\n"))
build("N6_CORRECT_claim_catches_the_type_via_contextlib_suppress", "observe", [],
      (T, """        try:
            await self._apply([self._claim_fragment(task_id, owner, blocked_by, event)])
        except TxnClaimLostError:
            pass  # a routine loss (am-3 §3) — the owner read below decides the verdict
""", """        with contextlib.suppress(TxnClaimLostError):  # a routine loss (am-3 §3) — typed; the owner read decides
            await self._apply([self._claim_fragment(task_id, owner, blocked_by, event)])
"""),
      (T, "import asyncio\n", "import asyncio\nimport contextlib\n"))
build("N7_CORRECT_heal_chunk_apply_in_a_helper_method", "observe", [],
      (T, """            try:
                await self._apply([f for f in fragments if f.statements])
            except TxnDomainRejectionError:
                logger.warning(
                    _HEAL_CHUNK_REJECTED_EVENT,
                    extra={
                        "database": self._database, "chunk": chunk_index,
                        "rows": [entry[0] for entry in chunk],
                    },
                )
                continue
            healed += len(chunk)
""", """            if await self._apply_heal_chunk(chunk_index, [entry[0] for entry in chunk], fragments):
                healed += len(chunk)
"""),
      (T, "    @staticmethod\n    def _supersede_fragment(", '''    async def _apply_heal_chunk(self, chunk_index: int, rows: list[str], fragments: list[TxnFragment]) -> bool:
        """Apply ONE heal chunk; a DOMAIN rejection is isolated + WARNING (am-3 §2); a store fault raises."""
        try:
            await self._apply([f for f in fragments if f.statements])
        except TxnDomainRejectionError:
            logger.warning(
                _HEAL_CHUNK_REJECTED_EVENT,
                extra={"database": self._database, "chunk": chunk_index, "rows": rows},
            )
            return False
        return True

    @staticmethod
    def _supersede_fragment('''))
build("N8_packer_uses_a_PRIVATE_counter", "survive", [],
      (T, "            cost = self._composed_statement_count([*fragments, self._relate_fragment(relates)])\n",
       "            cost = sum(len(f.statements) for f in [*fragments, self._relate_fragment(relates)])\n"))
build("N9_claim_apply_via_local_alias_and_swallows_exhaustion", "include", [],
      (T, """        try:
            await self._apply([self._claim_fragment(task_id, owner, blocked_by, event)])
        except TxnClaimLostError:
            pass""", """        apply = self._apply
        try:
            await apply([self._claim_fragment(task_id, owner, blocked_by, event)])
        except (TxnClaimLostError, TxnContentionExhaustedError):
            pass"""))
build("N10_claim_catches_bare_Exception", "include", [],
      (T, "        except TxnClaimLostError:\n            pass  #", "        except Exception:  # noqa: BLE001\n            pass  #"))
build("N11_exhaustion_REPARENTED_under_domain_rejection", "include", [],
      (X, "class RetryableConflictSignal(Exception):",
       "TxnContentionExhaustedError.__bases__ = (TxnDomainRejectionError,)\n\n\nclass RetryableConflictSignal(Exception):"))
build("N12_DEBUG_for_EVERY_throw", "include", ["test_CONTROL_a_lost_TRANSITION_race_still_logs_at_WARNING"],
      (X, "    if CLAIM_LOST_MARKER in text:\n        level = logging.DEBUG\n",
       "    if text.startswith(_THROW_RESULT_PREFIX):\n        level = logging.DEBUG\n"))
build("N14_packer_closes_at_GE_cap", "survive", [],
      (T, "            if current and used + entry[3] > cap:\n", "            if current and used + entry[3] >= cap:\n"))
build("N15_packer_post_checks_allowing_overflow", "include", [],
      (T, "            if current and used + entry[3] > cap:\n", "            if current and used > cap:\n"))
build("N16_heal_isolates_every_store_fault", "include", ["test_every_heal_door_after_the_backfill_RAISES"],
      (T, "            except TxnDomainRejectionError:\n                logger.warning(\n                    _HEAL_CHUNK",
       "            except SurrealStoreError:\n                logger.warning(\n                    _HEAL_CHUNK"))

build("N17_heal_hand_rolls_its_RELATEs", "survive", [],
      (T, "            fragments.append(self._relate_fragment([pair for entry in chunk for pair in entry[2]]))\n",
       "            pairs_here = [pair for entry in chunk for pair in entry[2]]\n"
       "            fragments.append(TxnFragment(\n"
       "                statements=[f\"RELATE $hr{i}_a->{BLOCKS_RELATION}->$hr{i}_b\" for i in range(len(pairs_here))],\n"
       "                params={k: v for i, (a, b) in enumerate(pairs_here) for k, v in\n"
       "                        ((f\"hr{i}_a\", RecordID(TASK_TABLE, a)), (f\"hr{i}_b\", RecordID(TASK_TABLE, b)))},\n"
       "            ))\n"))
build("N18_transition_retries_its_CAS_once_in_the_ledger", "include", [],
      (T, """            await self._apply(
                [
                    self._transition_fragment(
                        task_id, status, current, event, release, summary, report_path
                    )
                ]
            )
        except SurrealConnectionError:""", """            try:
                await self._apply(
                    [self._transition_fragment(task_id, status, current, event, release, summary, report_path)]
                )
            except TxnDomainRejectionError:
                await self._apply(
                    [self._transition_fragment(task_id, status, current, event, release, summary, report_path)]
                )
        except SurrealConnectionError:"""))


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def load_verbatim() -> None:
    import runpy
    ns = runpy.run_path(str(SCRATCH / "adv/wrong_builds.py"), run_name="wb")
    for name, (mode, declared) in VERBATIM.items():
        B[name] = {"mode": mode, "declared": declared, "edits": [(T, old, new) for old, new in ns["BUILDS"][name]]}


def run(name: str) -> dict:
    spec = B[name]
    subprocess.run(["git", "checkout", "-q", "--", "."], cwd=ROOT, check=True)
    for rel, digest in REF_MD5.items():
        assert md5(ROOT / rel) == digest, f"{name}: reference not restored for {rel}"
    touched: dict[str, str] = {}
    for rel, old, new in spec["edits"]:
        path = ROOT / rel
        text = path.read_text()
        count = text.count(old)
        assert count == 1, f"{name}: anchor occurs {count}x in {rel}: {old[:80]!r}"
        touched.setdefault(rel, md5(path))
        path.write_text(text.replace(old, new))
    for rel, before in touched.items():
        assert md5(ROOT / rel) != before, f"{name}: {rel} unchanged — the mutation did not land"
    log = OUT / f"{name}.log"
    timeout = HANG_SECONDS if spec["mode"] == "hang" else 1800
    import os
    import time
    for attempt in range(4):
        while int(open("/proc/meminfo").read().split("MemAvailable:")[1].split()[0]) < 22 * 1048576:
            time.sleep(15)  # host memory is shared with other lore sessions: start only with headroom
        proc = subprocess.run(
            [str(SCRATCH / "run.sh"), str(ROOT), str(log), "-n", "6", "--tb=line", "-rfE", *SCOPE, PROBES],
            cwd=ROOT, env={**os.environ, "RUN_TIMEOUT": str(timeout)},
        )
        if proc.returncode != 98:
            break
        print(f"  {name}: watchdog fired (attempt {attempt + 1}) — retrying when memory frees", flush=True)
    rc = "HANG" if proc.returncode == 97 else proc.returncode
    if rc == 98:
        return {"build": name, "mode": spec["mode"], "tail": "WATCHDOG x4", "verdict": "NO VERDICT (memory)",
                "contract_reds": [], "probe_reds": []}
    text = log.read_text() if log.exists() else ""
    reds = sorted(set(re.findall(r"^(?:FAILED|ERROR) (\S+?)(?: - |$)", text, re.M)))
    tail = [line for line in text.splitlines() if re.search(r"\d+ (passed|failed)", line)][-1:] or [str(rc)]
    contract_reds = [r for r in reds if PROBES not in r]
    probe_reds = [r for r in reds if PROBES in r]
    declared = spec["declared"]
    hit = {d: [r for r in reds if d in r] for d in declared}
    missing = [d for d, rs in hit.items() if not rs]
    mode = spec["mode"]
    if mode == "hang":
        verdict = "HANG as declared" if rc == "HANG" else f"MISMATCH (completed rc={rc})"
    elif mode == "survive":
        verdict = ("SURVIVES the contract (probe red)" if not contract_reds and not missing
                   else f"KILLED by contract: {contract_reds}" if contract_reds else f"probe GREEN: {missing}")
    elif mode == "observe":
        verdict = f"OBSERVED {len(contract_reds)} contract red(s)"
    elif mode == "exact":
        verdict = "EXACT" if not contract_reds and not declared else ("EXACT" if not missing and len(contract_reds) == len(declared) else f"MISMATCH missing={missing}")
    else:
        verdict = "INCLUDED" if not missing and contract_reds else f"MISMATCH missing={missing} reds={len(contract_reds)}"
    subprocess.run(["git", "checkout", "-q", "--", "."], cwd=ROOT, check=True)
    for rel, digest in REF_MD5.items():
        assert md5(ROOT / rel) == digest
    return {"build": name, "mode": mode, "tail": tail[0].strip(), "verdict": verdict,
            "contract_reds": contract_reds, "probe_reds": probe_reds}


def main() -> None:
    load_verbatim()
    OUT.mkdir(parents=True, exist_ok=True)
    names = sys.argv[3:] or list(B)
    for name in names:
        result = run(name)
        with (OUT / "results.jsonl").open("a") as handle:
            handle.write(json.dumps(result) + "\n")
        print(f"{result['build']:<60} {result['verdict']:<45} {result['tail']}", flush=True)


if __name__ == "__main__":
    main()
```

### `wb6.py` (md5 `f9433e2c5cd901447fd139b3a9e25bd2`)
```python
#!/usr/bin/env python3
"""adversary-58-r2 wrong-build driver — declare-then-diff, both ways.

Usage: wb_r2adv.py <scratch-root> <out-dir> [build ...]      (no builds = all, in BUILDS order)

Each build = exact-once substitutions over the reference commit in the scratch repo (every anchor asserted
to occur EXACTLY once and every edited file asserted CHANGED — the mutation LANDED, #194), then the SCOPE
(every 58 contract file + §HELD's test_retry_seam + D + the adversary probe file) is run under the
15 GB tree-kill watchdog (run.sh).  Modes:
  exact    observed contract reds == declared (both ways)
  include  declared ⊆ observed (extra reds listed, not failing)
  survive  ZERO contract reds AND the declared PROBE ids red  (a surviving wrong build = a MISSING PIN)
  observe  record the reds (a CORRECT-build shape probe: any contract red is a SAT finding)
  hang     the run must not complete within HANG_SECONDS
After each build the tree is restored with `git checkout -- .` and the reference md5s re-asserted.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
OUT = Path(sys.argv[2])
SCRATCH = Path(__file__).resolve().parent
SCOPE = [line.strip() for line in (SCRATCH / "files58.txt").read_text().splitlines() if line.strip()]
PROBES = "loremaster/tests/test_adv58r2_am6_probes.py"
PROBES2 = "loremaster/tests/test_adv58r2_probes.py"
T, X = "loremaster/loremaster/tasks.py", "loremaster/loremaster/store/_txn.py"
REF_MD5 = {T: "12917da91e81642022e0e6a5a7bffe39", X: "8c748e4f76d89f5fa59199dfaffccd11"}
HANG_SECONDS = 900

HEAL_TRY = """            try:
                await self._apply([f for f in fragments if f.statements])
            except TxnDomainRejectionError:
"""

B: dict[str, dict] = {}


def build(name: str, mode: str, declared: list[str], *edits: tuple[str, str, str]) -> None:
    B[name] = {"mode": mode, "declared": declared, "edits": list(edits)}



VERBATIM: dict = {}
XONLY_OLD = """                        f"{_COL_BLOCKED_BY} = array::distinct(array::map({_COL_BLOCKED_BY}, "
                        f"|$b| IF $b = ${old_param} THEN ${new_param} ELSE $b END))"
"""
XONLY_NEW = """                        f"{_COL_BLOCKED_BY} = array::filter(array::map(array::map({_COL_BLOCKED_BY}, "
                        f"|$b| IF $b = ${old_param} THEN ${new_param} ELSE $b END), |$v, $i| IF $v = ${new_param} "
                        f"AND $i != array::find_index(array::map({_COL_BLOCKED_BY}, |$b| IF $b = ${old_param} "
                        f"THEN ${new_param} ELSE $b END), ${new_param}) THEN NONE ELSE $v END), |$v| $v != NONE)"
"""
build("REF6_control_no_edit", "exact", [])
build("W6a_unrecognised_app_throw_defaults_to_WARNING", "survive", ["an_unprefixed_app_throw"],
      (X, "(tier for prefix, tier in _ROLLBACK_LOG_TIERS.items() if thrown.startswith(prefix)), logging.ERROR",
       "(tier for prefix, tier in _ROLLBACK_LOG_TIERS.items() if thrown.startswith(prefix)),\n        logging.WARNING if thrown else logging.ERROR"))
build("W6b_a_SECOND_tier_table_beside_the_ruled_one", "survive", ["test_P6_mutation_dropping_ONE_table_entry"],
      (X, """    level = next(
        (tier for prefix, tier in _ROLLBACK_LOG_TIERS.items() if thrown.startswith(prefix)), logging.ERROR
    )
""", """    level = (
        logging.DEBUG if thrown.startswith(CLAIM_LOST_MARKER)
        else logging.WARNING if thrown.startswith(("governed_conflict:", "cas_lost:", "reanchor_straggler:", "heal_chunk:"))
        else logging.ERROR
    )
"""))
build("W6c_dedupe_collapses_only_X_copies", "survive", ["test_P6_E11_"], (T, XONLY_OLD, XONLY_NEW))
build("W6d_governed_conflict_left_at_ERROR", "survive", ["governed_conflict"],
      (X, "    _GOVERNED_CONFLICT_MARKER: logging.WARNING,\n", ""))


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def load_verbatim() -> None:
    import runpy
    ns = runpy.run_path(str(SCRATCH / "adv/wrong_builds.py"), run_name="wb")
    for name, (mode, declared) in VERBATIM.items():
        B[name] = {"mode": mode, "declared": declared, "edits": [(T, old, new) for old, new in ns["BUILDS"][name]]}


def run(name: str) -> dict:
    spec = B[name]
    subprocess.run(["git", "checkout", "-q", "--", "."], cwd=ROOT, check=True)
    for rel, digest in REF_MD5.items():
        assert md5(ROOT / rel) == digest, f"{name}: reference not restored for {rel}"
    touched: dict[str, str] = {}
    for rel, old, new in spec["edits"]:
        path = ROOT / rel
        text = path.read_text()
        count = text.count(old)
        assert count == 1, f"{name}: anchor occurs {count}x in {rel}: {old[:80]!r}"
        touched.setdefault(rel, md5(path))
        path.write_text(text.replace(old, new))
    for rel, before in touched.items():
        assert md5(ROOT / rel) != before, f"{name}: {rel} unchanged — the mutation did not land"
    log = OUT / f"{name}.log"
    timeout = HANG_SECONDS if spec["mode"] == "hang" else 1800
    import os
    import time
    for attempt in range(4):
        while int(open("/proc/meminfo").read().split("MemAvailable:")[1].split()[0]) < 22 * 1048576:
            time.sleep(15)  # host memory is shared with other lore sessions: start only with headroom
        proc = subprocess.run(
            [str(SCRATCH / "run.sh"), str(ROOT), str(log), "-n", "6", "--tb=line", "-rfE", *SCOPE, PROBES, PROBES2],
            cwd=ROOT, env={**os.environ, "RUN_TIMEOUT": str(timeout)},
        )
        if proc.returncode != 98:
            break
        print(f"  {name}: watchdog fired (attempt {attempt + 1}) — retrying when memory frees", flush=True)
    rc = "HANG" if proc.returncode == 97 else proc.returncode
    if rc == 98:
        return {"build": name, "mode": spec["mode"], "tail": "WATCHDOG x4", "verdict": "NO VERDICT (memory)",
                "contract_reds": [], "probe_reds": []}
    text = log.read_text() if log.exists() else ""
    reds = sorted(set(re.findall(r"^(?:FAILED|ERROR) (\S+?)(?: - |$)", text, re.M)))
    tail = [line for line in text.splitlines() if re.search(r"\d+ (passed|failed)", line)][-1:] or [str(rc)]
    contract_reds = [r for r in reds if PROBES not in r and PROBES2 not in r]
    probe_reds = [r for r in reds if PROBES in r or PROBES2 in r]
    declared = spec["declared"]
    hit = {d: [r for r in reds if d in r] for d in declared}
    missing = [d for d, rs in hit.items() if not rs]
    mode = spec["mode"]
    if mode == "hang":
        verdict = "HANG as declared" if rc == "HANG" else f"MISMATCH (completed rc={rc})"
    elif mode == "survive":
        verdict = ("SURVIVES the contract (probe red)" if not contract_reds and not missing
                   else f"KILLED by contract: {contract_reds}" if contract_reds else f"probe GREEN: {missing}")
    elif mode == "observe":
        verdict = f"OBSERVED {len(contract_reds)} contract red(s)"
    elif mode == "exact":
        verdict = "EXACT" if not contract_reds and not declared else ("EXACT" if not missing and len(contract_reds) == len(declared) else f"MISMATCH missing={missing}")
    else:
        verdict = "INCLUDED" if not missing and contract_reds else f"MISMATCH missing={missing} reds={len(contract_reds)}"
    subprocess.run(["git", "checkout", "-q", "--", "."], cwd=ROOT, check=True)
    for rel, digest in REF_MD5.items():
        assert md5(ROOT / rel) == digest
    return {"build": name, "mode": mode, "tail": tail[0].strip(), "verdict": verdict,
            "contract_reds": contract_reds, "probe_reds": probe_reds}


def main() -> None:
    load_verbatim()
    OUT.mkdir(parents=True, exist_ok=True)
    names = sys.argv[3:] or list(B)
    for name in names:
        result = run(name)
        with (OUT / "results.jsonl").open("a") as handle:
            handle.write(json.dumps(result) + "\n")
        print(f"{result['build']:<60} {result['verdict']:<45} {result['tail']}", flush=True)


if __name__ == "__main__":
    main()
```

### `run.sh` (md5 `781d16b798ab2f70f143fa147ac41e4e`)
```bash
#!/usr/bin/env bash
# run.sh <tree> <log> <pytest args...> — adversary-58-r2. Runs pytest in its OWN process group (setsid);
# a 5 s watchdog kills that group by numeric PGID (the process TREE) if MemAvailable < 15 GB (exit 98),
# or when RUN_TIMEOUT seconds elapse (exit 97, "TIMEOUT FIRED"). Prints loremaster.__file__ first.
set -u
tree=$1; log=$2; shift 2
cd "$tree" || exit 90
.venv/bin/python -c 'import loremaster,sys; print("loremaster.__file__ =", loremaster.__file__)' > "$log" 2>&1
setsid .venv/bin/python -m pytest -p no:cacheprovider -q "$@" >> "$log" 2>&1 &
pid=$!
fired=0; start=$(date +%s); limit=${RUN_TIMEOUT:-0}
while kill -0 "$pid" 2>/dev/null; do
  avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
  if [ "$avail" -lt 15 ]; then kill -KILL -- "-$pid" 2>/dev/null; fired=98; echo "WATCHDOG FIRED avail=${avail}G" >> "$log"; fi
  if [ "$limit" -gt 0 ] && [ $(( $(date +%s) - start )) -gt "$limit" ]; then kill -KILL -- "-$pid" 2>/dev/null; fired=97; echo "TIMEOUT FIRED after ${limit}s" >> "$log"; fi
  sleep 5
done
wait "$pid"; rc=$?
[ $fired != 0 ] && exit $fired
exit $rc
```

### `sat.sh` (md5 `1f963d6a3e3bcbbe932e04c54d98908e`)
```bash
#!/usr/bin/env bash
# adversary-58-r2 SAT: the FULL suite on scratch/ref (HEAD + §HELD 1–3 + my reference), my probe files ignored.
# Waits for ≥24 GB free before each attempt; retries (≤4) when run.sh's 15 GB watchdog fires (exit 98).
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/f2fe3a36-cb3f-47ec-b8ed-14e14fdbedea/scratchpad
for attempt in 1 2 3 4; do
  until [ "$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)" -ge 24 ]; do sleep 20; done
  $S/run.sh $S/ref $S/sat_full_$attempt.log -n 8 --tb=line -rfE --ignore=loremaster/tests/test_adv58r2_probes.py
  rc=$?; echo "attempt $attempt rc=$rc" >> $S/sat_attempts.log
  [ $rc -ne 98 ] && break
done
```

### `ast_context.py` (md5 `03bfe8d73693efda05018f5fc340d6af`)
```python
#!/usr/bin/env python3
"""adversary-58-r2: the CONTEXT half of an AST-equality receipt.  For every function EQUAL between an adversary
probe file and its landed file, compare the MODULE-LEVEL BINDING of every free name the function loads:
an import (module, original name) or a module assignment (ast.dump of its value).  An AST-equal function
whose free names bind differently is NOT the same probe.  Usage: ast_context.py <adv.py> <landed.py> ..."""
import ast, builtins, sys

def bindings(tree):
    out = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            for a in node.names: out[a.asname or a.name] = ("from", node.module, a.name)
        elif isinstance(node, ast.Import):
            for a in node.names: out[a.asname or a.name.split(".")[0]] = ("import", a.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Name): out[t.id] = ("assign", ast.dump(node.value) if node.value else None)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[node.name] = ("def", ast.dump(node, include_attributes=False))
        elif isinstance(node, ast.If):  # TYPE_CHECKING blocks: runtime-inert, skipped deliberately
            pass
    return out

def free_names(fn):
    local = {a.arg for a in ast.walk(fn.args) if isinstance(a, ast.arg)}
    local |= {n.id for n in ast.walk(fn) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    return {n.id for n in ast.walk(fn) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)} - local - set(dir(builtins))

args = sys.argv[1:]; bad = 0; checked = 0
for adv, landed in zip(args[::2], args[1::2]):
    ta, tl = ast.parse(open(adv).read()), ast.parse(open(landed).read())
    ba, bl = bindings(ta), bindings(tl)
    fa = {n.name: n for n in ta.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    fl = {n.name: n for n in tl.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    for name, fn in fa.items():
        if name not in fl or ast.dump(fn, include_attributes=False) != ast.dump(fl[name], include_attributes=False):
            continue
        for free in sorted(free_names(fn)):
            checked += 1
            if ba.get(free) != bl.get(free):
                bad += 1
                print(f"DIFFERENT-BINDING {landed.rsplit('/',1)[-1]}::{name} free name {free!r}: adv={ba.get(free)} landed={bl.get(free)}")
print(f"checked {checked} free-name bindings over AST-equal functions; {bad} differ")
```

### `test_adv58r2_probes.py` (md5 `55aac1879c43bbef7c08f85898041cc3`)
```python
"""adversary-58-r2 PROBES — each is a candidate MISSING PIN against contract r2 (`c42eeaf`).

Scoped 2026-09-26 to HEAD `6417e8f` + §HELD (parts 1–3) + a packet-58 reference build.  Every probe is
GREEN on the reference (the P0 positive control) and RED on the wrong build it names (§A of
REPORT-adversary-58-r2.md).  Copied into a scratch tree's `loremaster/tests/` to run.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

import pytest
from _reanchor_58_support import (
    CREATOR,
    DESCRIPTION,
    HEAL_CHAIN_CYCLE_EVENT,
    HEAL_EVENT,
    HEAL_PHANTOM_HEAD_EVENT,
    ROLLBACK_EVENT,
    ApplyHook,
    ComposeSpy,
    all_columns,
    boot,
    create,
    ledger58,
    new_ledger,
    raw,
    raw_relate,
    raw_seed_row,
    snapshot,
    supersede,
)
from _surreal_harness import SurrealEnv
from loremaster.store import _txn
from loremaster.store.surreal_schema import BLOCKS_RELATION, TASK_TABLE
from loremaster.tasks import IllegalTransitionError, TaskLedger, TaskLedgerError
from surrealdb import RecordID

__all__ = ["ledger58"]


def _levels(caplog: pytest.LogCaptureFixture, message: str) -> list[int]:
    return [r.levelno for r in caplog.records if r.getMessage() == message]


# P-A (am-3 §3, ∀ "every OTHER THROW-rooted rollback … transition/supersede lost races, R1's straggler … WARNING")
async def test_PA1_a_lost_SUPERSEDE_race_logs_its_rollback_at_WARNING(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, env = ledger58
    old = await create(ledger, "X")
    racer = new_ledger(env)
    hook = ApplyHook(ledger, lambda: supersede(racer, old))
    caplog.clear()
    try:
        with hook.installed(), caplog.at_level(logging.DEBUG), pytest.raises(IllegalTransitionError):
            await supersede(ledger, old)
    finally:
        await racer.close()
    assert hook.fired
    assert _levels(caplog, ROLLBACK_EVENT) == [logging.WARNING], [
        logging.getLevelName(level) for level in _levels(caplog, ROLLBACK_EVENT)
    ]


async def test_PA2_an_R1_straggler_rollback_logs_at_WARNING(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, env = ledger58
    old = await create(ledger, "X")
    await create(ledger, "Y", [old])
    racer = new_ledger(env)
    hook = ApplyHook(ledger, lambda: create(racer, "late Y", [old]))
    caplog.clear()
    try:
        with hook.installed(), caplog.at_level(logging.DEBUG), pytest.raises(TaskLedgerError):
            await supersede(ledger, old)
    finally:
        await racer.close()
    assert hook.fired
    assert _levels(caplog, ROLLBACK_EVENT) == [logging.WARNING], [
        logging.getLevelName(level) for level in _levels(caplog, ROLLBACK_EVENT)
    ]


# P-B (am-3 §3 principle: "a routine claim LOSS is not an error" — from ANY lore logger, not only the driver's)
async def test_PB_an_8_way_claim_race_raises_no_alarm_from_ANY_lore_logger(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, env = ledger58
    task_id = await create(ledger, "contended")
    racers = [new_ledger(env) for _ in range(8)]
    caplog.clear()
    try:
        with caplog.at_level(logging.DEBUG):
            results = await asyncio.gather(*(r.claim_task(task_id, f"racer-{i}") for i, r in enumerate(racers)))
    finally:
        for racer in racers:
            await racer.close()
    assert sum(r.claimed for r in results) == 1
    loud = [(r.name, r.levelname, r.getMessage()) for r in caplog.records
            if r.name.startswith("loremaster") and r.levelno >= logging.WARNING]
    assert not loud, loud


# P-C (am-3 §1: the packer BUILDS each row's fragments — ∀ rows, incl. a row naming TWO superseded blockers)
async def test_PC_stragglers_naming_TWO_superseded_blockers_at_scale_heal_in_ONE_boot(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, env = ledger58
    head_a, head_b = await create(ledger, "head A"), await create(ledger, "head B")
    legacy_a, legacy_b = "pcleg" + "a" * 27, "pcleg" + "b" * 27
    await raw_seed_row(ledger, legacy_a, blocked_by=[], superseded_by=head_a)
    await raw_seed_row(ledger, legacy_b, blocked_by=[], superseded_by=head_b)
    count = 1300
    now = datetime.now(UTC)
    ids = [f"pcrow{index:05d}" for index in range(count)]
    rows = [
        {"id": RecordID(TASK_TABLE, task_id),
         **TaskLedger._new_task_content(f"row {task_id}", DESCRIPTION, [legacy_a, legacy_b], CREATOR, now)}  # noqa: SLF001
        for task_id in ids
    ]
    await raw(ledger, f"INSERT INTO {TASK_TABLE} $rows", {"rows": rows})
    edges = [{"in": RecordID(TASK_TABLE, b), "out": RecordID(TASK_TABLE, t)} for t in ids for b in (legacy_a, legacy_b)]
    await raw(ledger, f"INSERT RELATION INTO {BLOCKS_RELATION} $edges", {"edges": edges})
    spy = ComposeSpy()
    caplog.clear()
    with spy.installed(), caplog.at_level(logging.DEBUG):
        await boot(env)  # a packer that under-counts a two-blocker row composes > cap: compose refuses, the BOOT fails
    columns = await all_columns(ledger)
    assert all(columns[t] == [head_a, head_b] for t in ids)
    heal = [r for r in caplog.records if r.getMessage() == HEAL_EVENT]
    assert len(heal) == 1 and getattr(heal[0], "count", None) == count
    assert all(len(s) <= _txn.TXN_STATEMENT_HARD_CAP for s, _p in spy.heal_calls())


# P-D (am-3 §5: "a row whose head is a phantom is SKIPPED" — the WHOLE row, excluded from count; ∀ rows incl. MIXED)
async def test_PD1_a_MIXED_row_phantom_head_plus_healable_blocker_is_skipped_WHOLE(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, env = ledger58
    phantom_head = "pdphantomhead" + "0" * 19
    pblocker, hblocker = "pdpblocker" + "0" * 22, "pdhblocker" + "0" * 22
    head = await create(ledger, "a real head")
    await raw_seed_row(ledger, pblocker, blocked_by=[], superseded_by=phantom_head)
    await raw_seed_row(ledger, hblocker, blocked_by=[], superseded_by=head)
    mixed = "pdmixedrow" + "0" * 22
    await raw_seed_row(ledger, mixed, blocked_by=[pblocker, hblocker])
    await raw_relate(ledger, pblocker, mixed)
    await raw_relate(ledger, hblocker, mixed)
    before = [row for row in (await snapshot(ledger))[0] if mixed in row]
    edges_before = [e for e in (await snapshot(ledger))[1] if e[1] == mixed]
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        await boot(env)
    assert [row for row in (await snapshot(ledger))[0] if mixed in row] == before, "the mixed row was half-healed"
    assert [e for e in (await snapshot(ledger))[1] if e[1] == mixed] == edges_before
    assert len([r for r in caplog.records if r.getMessage() == HEAL_PHANTOM_HEAD_EVENT]) == 1
    assert not [r for r in caplog.records if r.getMessage() == HEAL_EVENT], "a skipped row was counted"


async def test_PD2_a_MIXED_row_cyclic_chain_plus_healable_blocker_is_skipped_WHOLE(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, env = ledger58
    first, second = "pdcyca" + "0" * 26, "pdcycb" + "0" * 26
    await raw_seed_row(ledger, first, blocked_by=[], superseded_by=second)
    await raw_seed_row(ledger, second, blocked_by=[], superseded_by=first)
    head = await create(ledger, "a real head")
    hblocker = "pdhblock2" + "0" * 23
    await raw_seed_row(ledger, hblocker, blocked_by=[], superseded_by=head)
    mixed = "pdmixcyc" + "0" * 24
    await raw_seed_row(ledger, mixed, blocked_by=[first, hblocker])
    await raw_relate(ledger, first, mixed)
    await raw_relate(ledger, hblocker, mixed)
    before = await snapshot(ledger)
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        await asyncio.wait_for(boot(env), timeout=60)
    assert await snapshot(ledger) == before, "a cyclic-chain row was half-healed"
    assert len([r for r in caplog.records if r.getMessage() == HEAL_CHAIN_CYCLE_EVENT]) == 1
    assert not [r for r in caplog.records if r.getMessage() == HEAL_EVENT]


_UNUSED: Any = (IllegalTransitionError,)
```

### `test_adv58r2_am6_probes.py` (md5 `d3f96789b4888800e3bce77e42cd2781`)
```python
"""adversary-58-r2 PROBES for packet-58 amendment 6 (`dcf6b0f`) — the pins am-6 rules and r2 (`c42eeaf`)
cannot contain (r2 predates am-6).  GREEN on an am-6-faithful reference (`my_ref.py` + `my_ref_am6.py`), RED on
the ruled-out wrong builds W6a–W6d (REPORT-adversary-58-r2.md §A F6).  Scoped 2026-09-26, HEAD `6417e8f`."""

from __future__ import annotations

import logging

import pytest
from _reanchor_58_support import (
    ROLLBACK_EVENT,
    ApplyHook,
    boot,
    column,
    create,
    drive_to,
    edge_pairs,
    ledger58,
    new_ledger,
    raw,
    raw_relate,
    raw_seed_row,
    successor_of,
    supersede,
)
from _surreal_harness import SurrealEnv
from loremaster.store import _txn
from loremaster.tasks import STATUS_BLOCKED, STATUS_DONE, IllegalTransitionError, TaskLedger

__all__ = ["ledger58"]

#: am-6 FORK-3's table, TRANSCRIBED from the ruling (dcf6b0f) — the probe's oracle, not production's.
RULED_TIERS = [
    ("claim_lost:x", logging.DEBUG),
    ("governed_conflict:t:x", logging.WARNING),
    ("cas_lost: x", logging.WARNING),
    ("reanchor_straggler: x", logging.WARNING),
    ("heal_chunk: x", logging.WARNING),
    ("an unprefixed app throw", logging.ERROR),  # deny-by-default
]


async def _rollback_levels(ledger: TaskLedger, caplog: pytest.LogCaptureFixture, message: str) -> list[int]:
    caplog.clear()
    with caplog.at_level(logging.DEBUG), pytest.raises(_txn.SurrealStoreError):
        await _txn.execute_transaction(
            f"BEGIN;\nTHROW '{message}';\nCOMMIT;\n", {},
            acquire=ledger._ensure_connection, drop=ledger._drop_connection, url=ledger._url,  # noqa: SLF001
        )
    return [r.levelno for r in caplog.records if r.getMessage() == ROLLBACK_EVENT]


@pytest.mark.parametrize(("message", "tier"), RULED_TIERS, ids=[m.split(":")[0].replace(" ", "_") for m, _ in RULED_TIERS])
async def test_P6_each_ruled_tier_and_the_deny_by_default(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture, message: str, tier: int
) -> None:
    ledger, _env = ledger58
    assert await _rollback_levels(ledger, caplog, message) == [tier]


async def test_P6_mutation_dropping_ONE_table_entry_moves_ONLY_that_tier(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """am-6 pin (iii): the table is the ONE source — drop `cas_lost:` and a lost transition race logs ERROR,
    while `reanchor_straggler:` stays WARNING."""
    ledger, env = ledger58
    table = dict(_txn._ROLLBACK_LOG_TIERS)  # noqa: SLF001 - am-6 names the table
    table.pop("cas_lost:")
    monkeypatch.setattr(_txn, "_ROLLBACK_LOG_TIERS", table)
    task_id = await create(ledger, "raced")
    racer = new_ledger(env)
    hook = ApplyHook(ledger, lambda: racer.transition(task_id, STATUS_BLOCKED, actor="racer-am6"))
    caplog.clear()
    try:
        with hook.installed(), caplog.at_level(logging.DEBUG), pytest.raises(IllegalTransitionError):
            await ledger.transition(task_id, STATUS_BLOCKED, actor="worker-am6")
    finally:
        await racer.close()
    assert [r.levelno for r in caplog.records if r.getMessage() == ROLLBACK_EVENT] == [logging.ERROR]
    assert await _rollback_levels(ledger, caplog, "reanchor_straggler: x") == [logging.WARNING]


async def test_P6_E11_a_legacy_duplicate_collapses_WHOLE_column_and_the_claim_then_wins(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    """am-6 FORK-4 pin: Y raw [A, A, X] → supersede(X→X') → [A, X']; one A→Y, one X'→Y, no X→Y; the claim CAS
    on Y (A and X' done) WINS.  Control: [A, X] → [A, X']."""
    ledger, _env = ledger58
    blocker_a = await create(ledger, "A")
    old = await create(ledger, "X")
    y, control = "am6dupey" + "0" * 24, "am6ctrly" + "0" * 24
    await raw_seed_row(ledger, y, blocked_by=[blocker_a, blocker_a, old])
    await raw_seed_row(ledger, control, blocked_by=[blocker_a, old])
    for row in (y, control):
        await raw_relate(ledger, blocker_a, row)
        await raw_relate(ledger, old, row)
    successor = successor_of(await supersede(ledger, old))
    assert await column(ledger, y) == [blocker_a, successor]
    assert await column(ledger, control) == [blocker_a, successor]
    edges = [pair for pair in await edge_pairs(ledger) if pair[1] == y]
    assert sorted(edges) == sorted([(blocker_a, y), (successor, y)]), edges
    await drive_to(ledger, blocker_a, STATUS_DONE)
    await drive_to(ledger, successor, STATUS_DONE)
    assert (await ledger.claim_task(y, "claimant-am6")).claimed


async def test_P6_E11_through_the_boot_heal(ledger58: tuple[TaskLedger, SurrealEnv]) -> None:
    ledger, env = ledger58
    blocker_a = await create(ledger, "A")
    head = await create(ledger, "X'")
    legacy = "am6legacyx" + "0" * 22
    await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=head)
    y = "am6healdupe" + "0" * 21
    await raw_seed_row(ledger, y, blocked_by=[blocker_a, blocker_a, legacy])
    await raw_relate(ledger, blocker_a, y)
    await raw_relate(ledger, legacy, y)
    await boot(env)
    assert await column(ledger, y) == [blocker_a, head]


_UNUSED = (raw,)
```

### `test_adv58r2_probes_e.py` (md5 `439570bc6297ff8262190aac0ac85af9`)
```python
"""adversary-58-r2 PROBE P-E — am-3 §1's dropped rider: *"A single row that alone exceeds the cap … pinned as a
refusal, not an infinite chunk) RAISES a typed packer error (a store-class fault at boot: loud)"*.  GREEN on my
reference; RED on N19 (the over-cap row is skipped silently).  Scoped 2026-09-26, HEAD `6417e8f`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from _reanchor_58_support import CREATOR, DESCRIPTION, boot, column, create, ledger58, raw
from _surreal_harness import SurrealEnv
from loremaster.store.surreal_schema import TASK_TABLE
from loremaster.tasks import TaskLedger, TaskLedgerError
from surrealdb import RecordID

__all__ = ["ledger58"]


async def test_PE_a_single_straggler_that_alone_exceeds_the_cap_fails_the_boot_LOUD_and_changes_nothing(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, env = ledger58
    head = await create(ledger, "the head")
    now = datetime.now(UTC)
    legacy = [f"peleg{index:05d}" + "0" * 22 for index in range(1700)]
    rows = [
        {"id": RecordID(TASK_TABLE, lid),
         **TaskLedger._new_task_content(f"legacy {lid}", DESCRIPTION, [], CREATOR, now),  # noqa: SLF001
         "superseded_by": head}
        for lid in legacy
    ]
    await raw(ledger, f"INSERT INTO {TASK_TABLE} $rows", {"rows": rows})
    monster = "pemonster" + "0" * 23
    content = TaskLedger._new_task_content("monster", DESCRIPTION, legacy, CREATOR, now)  # noqa: SLF001
    await raw(ledger, f"CREATE type::record('{TASK_TABLE}', $id) CONTENT $c", {"id": monster, "c": content})
    before = await column(ledger, monster)
    assert len(before) == 1700
    with pytest.raises((TaskLedgerError, Exception)) as caught:
        await boot(env)
    assert "cap" in str(caught.value).lower() or "statement" in str(caught.value).lower(), repr(caught.value)
    print("RAISED:", type(caught.value).__name__, str(caught.value)[:160])
    assert await column(ledger, monster) == before
```

### `probes/throw_raw.py` (md5 `58a0d3ac196e67beacf88e82e3cfc70b`)
```python
"""adversary-58-r2 probe: the raw engine text of a THROW-rooted vs an index-violation vs an ASSERT rollback (3.2.x)."""
import asyncio, logging, sys
sys.path.insert(0, "loremaster/tests")
from _surreal_harness import make_env, unique_database, drop_database, PRODUCTION_DIM
from loremaster.store import _txn
from loremaster.tasks import TaskLedger

class Grab(logging.Handler):
    def __init__(self): super().__init__(logging.DEBUG); self.rows = []
    def emit(self, r): self.rows.append((r.levelname, getattr(r, "engine_result", None)))

async def main():
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    ledger = TaskLedger(url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password)
    await ledger.ensure_ready()
    grab = Grab(); logging.getLogger("loremaster").addHandler(grab); logging.getLogger("loremaster").setLevel(logging.DEBUG)
    cases = {
        "throw": "BEGIN;\nTHROW 'probe_msg:abc';\nCOMMIT;\n",
        "assert": "BEGIN;\nDEFINE FIELD OVERWRITE n ON probe58 TYPE int ASSERT $value > 0;\nCREATE probe58:a SET n = -1;\nCOMMIT;\n",
        "unique": "BEGIN;\nDEFINE INDEX IF NOT EXISTS u ON probe58u FIELDS k UNIQUE;\nCREATE probe58u:a SET k = 1;\nCREATE probe58u:b SET k = 1;\nCOMMIT;\n",
    }
    try:
        for name, text in cases.items():
            grab.rows.clear()
            try:
                await _txn.execute_transaction(text, {}, acquire=ledger._ensure_connection, drop=ledger._drop_connection, url=ledger._url)
                print(name, "NO ERROR")
            except Exception as e:
                print(name, type(e).__name__, "|", grab.rows)
    finally:
        await ledger.close(); await drop_database(env)

asyncio.run(main())
```

### `probes/closure_idx.py` (md5 `a1cfc9fbf42b434e31ba9b67d296d1bd`)
```python
"""adversary-58-r2 probe (3.2.x test store, throwaway DB): does array::filter/array::map pass an index to a closure,
and does array::find_index exist?  Needed to spell an X-ONLY dedupe (am-6 FORK-4's ruled-out build)."""
import asyncio, sys
sys.path.insert(0, "loremaster/tests")
from _surreal_harness import make_env, unique_database, drop_database, PRODUCTION_DIM
from loremaster.tasks import TaskLedger

async def main():
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    ledger = TaskLedger(url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password)
    await ledger.ensure_ready()
    try:
        for q in [
            "RETURN array::filter(['a','a','n','n','z'], |$v, $i| $i > 0)",
            "RETURN array::find_index(['a','a','n','n'], 'n')",
            "RETURN array::map(['a','a','n'], |$v, $i| $i)",
        ]:
            try:
                print(q, "=>", await ledger._query(q))
            except Exception as e:
                print(q, "=> ERR", type(e).__name__, str(e)[:150])
    finally:
        await ledger.close(); await drop_database(env)
asyncio.run(main())
```

### `probes/xonly_dedupe.py` (md5 `5d9025485873181fff04f84dffbe3d2a`)
```python
"""adversary-58-r2 probe: an X-ONLY dedupe spelling for the re-anchor rewrite (am-6 FORK-4's ruled-OUT build) —
[A, A, X] -> [A, A, X'] and [X', X] -> [X'], order kept.  Throwaway DB on the 3.2.x TEST store."""
import asyncio, sys, logging
logging.basicConfig(level=logging.ERROR, format='%(message)s')
sys.path.insert(0, "loremaster/tests")
from _surreal_harness import make_env, unique_database, drop_database, PRODUCTION_DIM
from loremaster.tasks import TaskLedger

M = "array::map(blocked_by, |$b| IF $b = $old THEN $new ELSE $b END)"
XONLY = (f"array::filter(array::map({M}, |$v, $i| IF $v = $new AND $i != array::find_index({M}, $new) "
         f"THEN NONE ELSE $v END), |$v| $v != NONE)")

async def main():
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    ledger = TaskLedger(url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password)
    await ledger.ensure_ready()
    try:
        for n, start in enumerate((["A", "A", "X"], ["N", "X"], ["X", "Z"], ["X", "X"])):
            await ledger._query("CREATE type::record('probe58x', $n) SET blocked_by = $s", {"s": start, "n": n})
            try:
                out = await ledger._query(f"UPDATE type::record('probe58x', $n) SET blocked_by = {XONLY} RETURN VALUE blocked_by", {"old": "X", "new": "N", "n": n})
            except Exception as e:
                out = f"ERR {e}"
            print(start, "->", out)
    finally:
        await ledger.close(); await drop_database(env)
asyncio.run(main())
```

### `files58.txt` (md5 `9eebf9c24adf8307df5b90ef61c57edc`)
```text
loremaster/tests/test_supersede_reanchor_58.py
loremaster/tests/test_task_guarded_shell_58.py
loremaster/tests/test_task_claimable_partition_58.py
loremaster/tests/test_reanchor_58_r2_probes.py
loremaster/tests/test_reanchor_58_r2_scale.py
loremaster/tests/test_reanchor_58_r2_am2.py
loremaster/tests/test_reanchor_58_r2_rulings.py
loremaster/tests/test_reanchor_58_r2_cas_runtime.py
loremaster/tests/test_blocks_edge.py
loremaster/tests/test_task_read_surface.py
loremaster/tests/test_retry_seam.py
loremaster/tests/test_supersede_render_58.py
scripts/test_forgery_door_sweep.py
```

### F6 reach-door probe (inserted before `async def _apply` in `messages.py`; CONTROL 2 = the same shape before `_reanchor_stragglers` in `tasks.py`, applying `self._claim_fragment(task_id, "o", [], None)`)
```python
    async def _adv58r2_door(self, row_id: str) -> bool:
        """adversary-58-r2 REACH probe: an UNGUARDED guarded-CAS door — a rollback handler that re-reads."""
        try:
            await self._apply([])
        except SurrealStoreError:
            return await self._select_row(row_id) is not None
        return True
```
The OLD scanner = `git show 6417e8f:loremaster/tests/test_retry_seam.py` copied over the §HELD version.

### F7 WB-H (`floor_calibration/store.py`)
```python
old = "        except (SurrealConnectionError, TxnContentionExhaustedError):\n            # NEITHER is a fence verdict"
new = "        except SurrealConnectionError:\n            # NEITHER is a fence verdict"
```

### F8 N20 (inserted before `_reanchor_stragglers` in `tasks.py`, over ref6)
```python
    async def assign_task(self, task_id: str, owner: str) -> bool:
        """N20: a 57-shaped NEW CAS verb — shell fragment built here, applied through a helper."""
        fragment = self._guarded_append_fragment(
            task_id, event=None, set_parts=["owner = $asg_owner"], params={"asg_owner": owner},
            where_conjuncts=["owner IS NONE"], throw_message="cas_lost: assign lost", namespace="asg",
        )
        return await self._commit_assign([fragment], task_id)

    async def _commit_assign(self, fragments: list[TxnFragment], task_id: str) -> bool:
        try:
            await self._apply(fragments)
        except SurrealStoreError:  # UNGUARDED: exhausted contention is re-read and served as "lost"
            return await self._select_row(task_id) is None
        return True
```

### F10 N19 (over ref6, `tasks.py`)
```python
old = "            if entry[3] > cap:\n                raise StragglerHealPackerError("
new = "            if entry[3] > cap:\n                continue  # N19: the over-cap row is skipped silently\n                raise StragglerHealPackerError("
```

## §HEAD-MOVED — what landed after my spawn (derived 2026-09-26 at HEAD `f21a885`, 23 commits past `c42eeaf`)
- Code moved in 12 files, **none of them a 58 file or a file 58's contract reads** (`loopback.py`, `test_loopback_serving.py`, `test_migration_wire*.py`, `test_no_raw_listener_in_test_trees.py`, `scripts/{_pytest_sessions,concurrent_wire_acceptance,gates.yaml,pending_contract_gate,wave_gate}.py`, `scripts/test_{concurrent_wire_acceptance,pytest_workers_503}.py` — #466/#503 work). My verdict rests on `tasks.py`/`_txn.py`/the 13 contract files/§HELD, byte-identical at `c42eeaf` and `f21a885`.
- **Spec moved: amendment 7 (`01565f9`, not in my brief, NOT graded)** rules the 58↔63c scanner collision: **58 am-5's *"derived shell callers"* scope is WITHDRAWN** (the domain becomes every `except` handler in the WHOLE production tree, class-resolved by import, re-read-filtered), and **`floor_calibration/store.py::record_measurement` becomes a listed guarded DOOR** — i.e. am-7 independently rules the defect my F6/F7 measured (F6's scope shrink and F7's unlisted fence door). It also re-keys am-6's `_ROLLBACK_LOG_TIERS` from THROW PREFIX to exception CLASS — F9's missing-pin CLASS stands; the pin's key follows am-7 (my probe's drop-one-entry leg pops a prefix key; under am-7 it pops a class). am-7 §1 names the `suppress`-style bound (F5) only implicitly ("every `except` handler") — F5 remains open.

## VERDICT
**CONTRACT INSUFFICIENT** (graded `c42eeaf`, against kickoff + amendments 1–5 and, per directive #17074, amendment 6).

Every prior survivor is dead and SAT holds on an independent reference, but seven wrong builds survive r2 on the committed bytes, one of which turns the heal into a permanent boot failure. The missing pins, each with the defect it catches (probe code verbatim in §INSTRUMENTS, GREEN on my reference):
1. **F1 (HIGH)** — `test_PC_stragglers_naming_TWO_superseded_blockers_at_scale_heal_in_ONE_boot` (generated form: a cost-mix sweep of straggler shapes) → catches a packer that does not build each row (N3: every boot fails).
2. **F4** — `test_PD1_…MIXED_row_phantom_head…_skipped_WHOLE` / `test_PD2_…MIXED_row_cyclic_chain…` → catches a heal that half-heals and counts a row with an unresolvable chain (N4/N5).
3. **F2** — the WARNING-tier legs GENERATED over the ledgers' THROW vocabulary (PA1 supersede lost race, PA2 R1 straggler) → catches a tier keyed on one message (N1).
4. **F3** — widen the 8-way DEBUG pin's logger filter to `loremaster` (PB) → catches a ledger-side WARNING per routine loss (N2) — pending the reading in Decisions (3).
5. **F9 (am-6, expected)** — the tier legs + deny-by-default + drop-one-entry mutation + E11 `[A, A, X] → [A, X']` (supersede and heal) → catch W6a–W6d (re-key to classes per am-7).
6. **F10** — `test_PE_a_single_straggler_that_alone_exceeds_the_cap_fails_the_boot_LOUD…` → catches a silent skip of the over-cap row (N19; am-3 §1's dropped rider).
7. **F11** — MP13 generated over every RELATE-composing verb → catches the heal's hand-rolled RELATEs (N17).

Plus, for the lead/sidecar (not builder-fixable, ruling-level): **F6/F7/F8** the (B)+(C) population's reach (now ruled by am-7 — the follow-up contract must carry am-7's whole-tree domain + completeness pin; my messages.py / N20 / floor_calibration receipts are its kill set), **F5/F8** the `try`-shape SAT fragility, and **P-PKG** (`more_itertools.constrained_batches` is the ruled packer).
