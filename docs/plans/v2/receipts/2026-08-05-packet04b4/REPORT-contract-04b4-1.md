# REPORT-contract-04b4-1

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK
- state: **done-with-deviations** (all 7 items contracted; 3 decisions surfaced for the lead)
- **Capability check:** brief demanded lore tools + read/write test files + a scratch mutation harness + the store. All available and used. lore index FRESH at HEAD (root `/workspace`, branch `feat/surreal-unification`, git_ref `5c5ff7a`; last_sweep 177 s at read). Fallback to grep/Read ONLY for served prose in `Field(description=...)` string literals (non-symbol textual seam — dogfood §3b), said out loud.
- deviations (one line each): (1) real test dir is `loremaster/tests/`, not the brief's `loremaster/loremaster/tests/`; (2) **#310(a): did NOT clone a guard** — the shipped `TestTheCapPredicateHasONEImplementationPROVENByMutation` already covers it, mutation-proven instead (#102); (3) **#309 grammar-degrade direction fork** — built to the wave-C §2 authority, not the brief's paraphrase (⚑ below); (4) **#309 K is DERIVED, not `count()`-ed** (wave-C §2 overrules R9's "store-side count"), so #309 touches no store/DDL surface; (5) live #319 residual `lore_findings.note` found by the sweep → added a derived RED pin; (6) edited `_task_fakes.py` docstring (discharged bound); (7) scratch copy `rm` sandbox-denied — flagged.
- Packages considered: none — no mechanism specified (contract/pins only; reused the in-tree house counted-elision template + `scratch_copy.sh`).
- Graded: `5c5ff7ae585bfcc4b9a507eafbd8a569c5aa7fba` · HEAD-at-report: `5c5ff7ae585bfcc4b9a507eafbd8a569c5aa7fba` · SAME (only test files edited, uncommitted).
- decisions-needed: **(A) #309 degrade-direction fork** — brief says "existence→counted", authority says "counted→existence (future trigger)"; I built the authority reading + flagged the caller-limited leg. **(B) #310(a)** — confirm no explicit new guard wanted (existing shipped guards discriminate). **(C) live #319 `note` residual** — builder must correct a production served description (RED pin waiting).
- receipt pointers: RED/GREEN table §1 · mutation-proofs §2 · #319 sweep §3 · forks §4 · per-pin reddening mutations §5.

---

## §1 · RED / GREEN PIN TABLE

Consolidated run (`-n auto`): **6 failed, 35 passed (41 total)**. Every RED is builder-work; every GREEN is a discriminating guard (each mutation-provable — §5).

| # | Pin (class) | File | Legs | Verdict | Meaning |
|---|---|---|---|---|---|
| **#319** | `TestServedParamDescriptionsMatchTheRefusalMatrix::test_every_strict_to_action_param_description_matches_its_matrix` | test_mcp_server.py | 1 | **GREEN guard** | derived desc-vs-matrix; reddens on drift (mutation-proven §2) |
| **#319** | …`::test_the_finding_note_description_names_every_action_that_RECORDS_it` | test_mcp_server.py | 1 | **RED** | live residual — `note` desc omits `acknowledge` which records it |
| **#319** | …`::test_POSITIVE_CONTROL_the_matrix_derivation_and_parser_DISCRIMINATE` | test_mcp_server.py | 1 | GREEN | control |
| **#309** | `TestTheNoLimitReadGetsADefaultDisplayCapWithTheCountedGrammar::…serves_an_HONEST_counted_line` | test_task_read_surface.py | 3 (surplus 1/2/7) | **RED** | builder adds `_DEFAULT_TASK_QUERY_DISPLAY_CAP` + counted grammar |
| **#309** | …`::test_the_no_limit_read_AT_OR_BELOW_the_cap_serves_NO_elision_line` | test_task_read_surface.py | 1 | GREEN guard | complete answer → no phantom surplus |
| **#309** | …`::test_CALLER_limited_read_KEEPS_the_existence_grammar_not_the_counted_one` | test_task_read_surface.py | 1 | GREEN guard ⚑FORK | two-grammars-two-properties (rests on fork A) |
| **#310(b)** | `TestTransformBeforeValidateIsAPinnedKnownBound` (ordering + anchor) | test_task_read_surface.py | 2 | GREEN | narrow ordering instrument + PIN-THE-MISS anchor |
| **#322** | `TestEveryDispatchActionIsDrivableWithoutAMissingArgOrMethod` (task ∀ + finding ∀ + control) | test_comms_footer.py | 18 | GREEN guard | ∀ dispatch-fixture, both faces |
| **#324 R-2** | `TestTransitiveBlockersCycleWalkAgreesFakeVsReal` (4 lengths + drift control) | test_task_ledger.py | 5 | GREEN guard | differential fake-vs-real cycle parity |
| **#324 R-3** | `TestTheServedActionVocabulariesArePinnedByEQUALITY` (branch scan widened to findings) | test_task_read_surface.py | 6 | GREEN guard | ONE shared Eq+In scan feeds tasks+findings |
| **#324 R-4** | `TestTheCommsIdentitySeamHasNoDefaultForNameOrTo` (signature + loud-fail) | test_comms_footer.py | 2 | **RED** | builder removes `name`/`to` defaults + updates 3 call sites |

**RED total = 6** (3× #309, 1× #319 note, 2× #324 R-4). **GREEN discriminating guards = 35.**

---

## §2 · MUTATION-PROOFS I RAN MYSELF (scratch provenance receipts)

Scratch built with `./scripts/scratch_copy.sh /home/ejprice/lore-scratch-04b4` (provenance-asserting). Both proofs printed `loremaster.__file__ = /home/ejprice/lore-scratch-04b4/loremaster/loremaster/__init__.py` — the scratch tree's OWN code ran, not the original.

- **#319 false-desc (proves my matrix pin discriminates):** mutated `lore_tasks.limit` served description `"For 'rollup' and 'query' ONLY"` → `"For 'rollup' ONLY"`. `test_every_strict_to_action_param_description_matches_its_matrix` went **RED**: `lore_tasks.limit … CLAIMS ['rollup'] but the matrix accepts ['query','rollup']`. Reverted.
- **#310 sharing-revert (proves #310(a) is covered without a new guard):** replaced `TaskLedger._validated_limit`'s `return validated_task_limit(limit)` delegation with a byte-identical PRIVATE copy (behaviour unchanged). The already-shipped `TestTheCapPredicateHasONEImplementationPROVENByMutation` went **RED in BOTH directions** — `test_the_LEDGER_routes_through_the_shared_predicate` (recorder saw `[]`) and `test_the_SEAM_routes_through_it_TOO` (`[5]` vs required `[5, 6]`). This is why I did NOT clone a #310(a) guard: cloning would duplicate policy (#102) the existing pins already enforce.

---

## §3 · #319 FULL ANCHOR-FREE SWEEP (delegated, then adjudicated)

Delegated the enumeration to `sweep-desc-04b4-1` (opus48-worker); I adjudicate its results. Full 100-row per-`(tool,param)` table (every `Field(description=...)` across all 15 served tools, no "remaining are X" collapse) lives in **`REPORT-sweep-desc-04b4-1.md`** at repo root — **lead: archive it beside this report at close-out** so the table survives (it is a sweep artifact, not a durable address yet).

- **Params swept: 100 · Graded at HEAD `5c5ff7a` (SAME) · TRUE 58 · FALSE 1 · NO-RULE 41 · UNSURE 0.**
- **The one FALSE (live #319 residual): `lore_findings.note`** (`server.py:9925-9927`) — served as *"recorded with a 'resolve' / 'wontfix' transition. Ignored by the other actions."* but the dispatcher forwards top-level `note` to `acknowledge` too (`server.py:3214`) and `FindingLedger.acknowledge` records it (`findings.py:903-923`). Went stale at the PKT-06 §3 widening. This is OUTSIDE my matrix-derived pin's class (`note` has no refusal guard), so I added a SEPARATE derived pin (`test_the_finding_note_description_names_every_action_that_RECORDS_it`, RED at HEAD) that reads the recording-action set from the dispatcher's own branches. **The acute #319 instance (`lore_tasks.limit`) is confirmed TRUE at HEAD** (corrected in `0ff05ed`).

---

## §4 · FORKS & FLAGS FOR THE LEAD (escalating, not silently resolving)

**(A) #309 degrade-direction fork — DECISION NEEDED.** The brief says *"the ESC-5 existence-line grammar degrades to the counted grammar in the SAME render."* The cited authority — wave-C sidecar §2 + §6.2 (`docs/plans/v2/receipts/2026-08-01-packet04b2-wavec/REPORT-design-sidecar-04b2-wavec-1.md`) — says the arrow runs the OTHER way: *"the COUNTED line degrades to the EXISTENCE grammar in the same edit"*, and only as a FUTURE trigger (if a later packet bounds the no-limit read in-store). The two readings produce different code: the brief's literal reading would force the CALLER-LIMITED path onto the counted grammar too, which needs a `count()` the wave-C ruling forbade and which the over-fetch-by-one path cannot honestly produce. I built the coherent, authority-backed reading: **04b4 adds the counted grammar to the NO-LIMIT path; the caller-limited path KEEPS the existence grammar; "two grammars never both live for one property" holds because grammar is a function of the caller's visible `limit` input.** The one leg that rests on this — `test_CALLER_limited_read_KEEPS_the_existence_grammar_not_the_counted_one` — is marked `⚑FORK` in-file; **if you rule the brief's literal reading, delete that leg.**

**(B) #309 K is DERIVED, not counted.** R9's parenthetical *"honest total from a store-side count"* (echoed by the brief) is explicitly OVERRULED by wave-C §2 / §6.2 item 1: the no-limit read already materialises the full set, so `K = len(materialised) − shown` and **no `count()` read may exist**. My pins assert the OBSERVABLE honest-K property (`K == true surplus`, mechanism-agnostic), so they are correct whether the builder derives or counts — but the derived path is the ruled one. Consequence: **#309 introduces no new store query / DDL** — store-law (`docs/reference/surrealdb-31-capabilities.md`, which I read; §COUNT line 86 confirms an index-backed COUNT exists but is not needed here) names no surface #309 touches.

**(C) #310(a) — no new guard, by design.** The brief's ground-truth override asked for "a thin GUARD pin asserting the shipped concrete is still present — reddens if someone reverts the sharing." That IS exactly what the already-shipped `TestTheCapPredicateHasONEImplementationPROVENByMutation` does (proven RED-on-revert in §2). Minting a second guard duplicates policy the repo forbids (#102). I recommend NOT cloning; the CLASS half (b) is the real residual and is built. Confirm if you want an explicit new guard anyway.

**(D) Live #319 `note` residual** (see §3) — a RED pin awaits a builder correcting a production served description.

**(E) Deviations:** real test dir is `loremaster/tests/` (brief said `loremaster/loremaster/tests/`); I edited `_task_fakes.py`'s `FakeTaskLedger.transitive_blockers` docstring to mark its STATED BOUND **discharged** by the new #324 R-2 parity pin (the bound's own re-open trigger — "a pin asserts on ids/truncated content through this fake" — is now met); the scratch copy `/home/ejprice/lore-scratch-04b4` could not be removed (`rm -rf` sandbox-denied) — it is a disposable `scratch_copy.sh` tree, safe to delete.

---

## §5 · PER-PIN REDDENING MUTATIONS (for the adversary + `mutation_proof.py`)

- **#319 matrix** (GREEN): change a strict-to-action `Field` description's `For '…' ONLY` clause (add/drop an action). *[PROVEN §2.]*
- **#319 note** (RED→GREEN when builder names `acknowledge`): once green, drop `'acknowledge'` from the `note` description, or add a new action that forwards `note` without naming it.
- **#319 control** (GREEN): make `_derived_strict_to_action_matrix` return `{}`, or make `_claimed_actions` match anything.
- **#309 surplus** (RED→GREEN when cap+counted-grammar ship): once green, render a constant/window K instead of `total − shown`, or drop the cap.
- **#309 below-cap** (GREEN): make the render emit a counted line on a complete answer (e.g. always `+0 more`).
- **#309 caller-limited** (GREEN ⚑): switch the caller-limited path to the counted grammar, or drop its existence line.
- **#310(b) ordering** (GREEN): move `cap + 1` above the `validated_task_limit(` call in `_task_listing`.
- **#310(b) anchor** (GREEN): remove `validated_task_limit` from `loremaster.tasks`.
- **#322 task/finding ∀** (GREEN): make `_task_action_kwargs`/`_finding_action_kwargs` return `{}` for an arg-requiring action (e.g. force `transition` → `{}`), or delete a `FakeTaskLedger` verb (e.g. `transitive_blockers`).
- **#322 control** (GREEN): make the dispatcher not raise on a missing arg.
- **#324 R-2 parity** (GREEN): make `FakeTaskLedger.transitive_blockers` diverge from the live store (e.g. drop the cycle self-reach). *[injected-drift control demonstrates this in-file.]*
- **#324 R-3 branch scan** (GREEN): delete a dispatch branch from `AppContext.tasks` OR `AppContext.findings` (e.g. remove `elif action == _FINDING_ACTION_WONTFIX`); OR regress the shared scan to `Eq`-only (findings' `in`-dispatched batch verbs falsely dead — caught by the `In` control).
- **#324 R-3 control** (GREEN): make the scan hallucinate an action, or drop `In` handling.
- **#324 R-4 signature + loud-fail** (RED→GREEN when defaults removed): once green, re-add a default to `name` or `to`.

---

## §6 · WHAT I DID NOT DO (scope honesty)
- No production edits — the cap, the counted grammar, the `note` description fix, and the `name`/`to` default removal are LEFT RED for the builder.
- No git state changes (lead commits).
- Did not run the full suite — ran the scoped set (my new/modified classes + the existing #310 guard for the mutation-proof) plus `ruff` (clean on all 5 touched files) and `scripts/typecheck.sh` (my files clean; 2 self-introduced mypy errors found and fixed).

There are pre-existing mypy failures UNRELATED to this scope: `scripts/typecheck.sh` reports errors in `loremaster/tests/test_auth_composition.py` (missing `resolve_posture` / `PostureConfigError` / `lorerunes.Posture` / `SCOPE_READ` — the packet-39 area). Do you want to examine them more closely?
