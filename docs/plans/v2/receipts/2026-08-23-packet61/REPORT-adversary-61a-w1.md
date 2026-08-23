brief-base v14 read
brief project v7 read

# REPORT — adversary-61a-w1 (contract adversary, packet 61a-w1, finding #402 / §FR-4)

> **⚠ RE-GRADE OUTCOME (2026-08-23, rev 2): CONTRACT SUFFICIENT.** The author landed the #403
> BLOCKER fix (2 new `set_keeper` ghost-keep pins, store + CLI) + the N=3 quantifier bump. I
> re-graded the delta (§RE-GRADE below): the 2 new pins RED the wrong build and pass a correct
> check-first build; the phantom-upsert path is closed by the engine (probed); the N=3 pin catches
> a `[:2]` slice-cap; the full revised contract is satisfiable (33/33) and 23 RED still RED@HEAD.
> **The SUMMARY BLOCK + probe record below are the ORIGINAL (rev 1) INSUFFICIENT pass, kept as the
> record of how the blocker was found.** The current verdict is SUFFICIENT.

## SUMMARY BLOCK (rev 1 — the original INSUFFICIENT pass; superseded by §RE-GRADE)
- **VERDICT (rev 1): CONTRACT INSUFFICIENT** — one BLOCKER (a wrong build passes the whole contract).
  **Superseded by rev 2: SUFFICIENT** (§RE-GRADE) once the blocker fix landed.
- state: **done-with-deviations** (verdict rendered; one missing pin, empirically reproduced).
- **P1 headline — a wrong build survived the contract:** a `KeepStore.set_keeper` that omits
  the ghost-keep guard passes the **entire contract 31/31 GREEN**, yet on a ghost keep it
  **silently returns `None`** (no `KeepNotFoundError`); the CLI `lore-adm set-keeper --keep
  <typo>` reads as rc 0. Dropped D1 rider (*"a ghost keep is LOUD"*) — pinned for `delete-keep`,
  forgotten for `set-keeper`. Finding **#403**. All OTHER wrong builds I tried were caught.
- deviations: the scratch reference build is a deliberately-rough throwaway (satisfiability
  proven behaviourally; ruff/mypy harder-leg taken from the author's receipt + structural
  reasoning, not re-run on my rough copy — see §Satisfiability).
- Packages considered: none — no mechanism specified; probes/tests reuse the installed
  `surrealdb` SDK already in-tree.
- Reuse ledger: none — I wrote no repo symbols (scratch-only wrong/reference builds, discarded).
- **Graded: 84d20a3 · HEAD-at-report: 84d20a3 · SAME** — every RED/GREEN/wrong-build claim is
  at this sha (matches the author's `Graded:`).
- decisions-needed: none — the missing pin is concrete and satisfiable; author adds 2 pins,
  re-grade.
- receipt pointers: §P1 (wrong builds, each with the pin that caught it / the pin that should);
  §P1b quantifier table; §P1c reach table; §Satisfiability (`loremaster.__file__` receipt);
  §RED-honesty; the BLOCKER at §MISSING PIN 1.

## CAPABILITY CHECK
Brief fully satisfiable with the tools I have: lore MCP loaded; live TEST store reachable at
`ws://127.0.0.1:18000` (never :18500); `scratch_copy.sh` provenance tool worked; I built wrong
AND reference implementations in a provenance-asserted scratch. No unmet demand.

## Store reference citations (cited, never re-transcribed)
`docs/reference/surrealdb-31-capabilities.md`: §2 (`record<t>` FIELD links do NOT auto-clean /
do NOT validate existence), §4 (graph RELATION edges self-delete on endpoint delete; the #7061
cascade fix is present), §1.4 (greenfield vs populated), §1.6 (the virgin-DB blind spot that the
#131 D3 guard targets). Newly settled by construction this session (see §P1 WB11): **a `SELECT`
against an UNDECLARED table RAISES `SurrealStoreError` — it does NOT return `[]`** (the D3
"unprobed" concern; measured on spike-surreal 3.2.x).

---

## VERDICT: CONTRACT INSUFFICIENT

One BLOCKER (a wrong build that passes the whole contract), one concrete missing pin, satisfiable
by a correct build. Everything else is strong: RED-at-HEAD reproduces exactly (21/10), the
reference build goes 31/31, and seven distinct wrong builds are each caught by the right pin. Fix
the one pin and this contract is SUFFICIENT.

---

## MISSING PIN 1 — BLOCKER: `set-keeper` has no ghost-keep-loud pin (dropped D1 rider)

**The wrong build that passes:** a `KeepStore.set_keeper` that resolves the new-keeper email
(keeps the ghost-**email** guard) but **omits the ghost-KEEP guard** — no `if keep is None: raise
KeepNotFoundError`, and returns whatever `get_keep` reads back (`None` on a ghost keep). This is
the plausible build of a builder who mirrors `set_rank`/`create_keep` (which have no keep
pre-check) rather than `remove_household_member`/`delete_keep` (which do).

**Empirical (scratch, `loremaster.__file__ = /tmp/adv-61a/loremaster/loremaster/__init__.py`):**
- The wrong build passes **all four contract files, 31 passed / 0 failed** (`-n auto`).
- Direct call: `set_keeper(keep_id=ghost_id('keep'), new_keeper_email='successor@example.com')`
  → **returned `None`, raised nothing** (silent success). At the CLI this launders to **rc 0** —
  a typo'd `--keep` on an ownership-reassignment admin verb reads as *"reassigned"*.
- Positive control: the **correct** build (with `if keep is None: raise KeepNotFoundError`) raises
  `KeepNotFoundError("no keep '…' exists — cannot set its keeper")` → the proposed pin **is
  satisfiable** and laundered by `_dispatch_keep`'s `except KeepStoreError` to exit 1 + `lore-adm:`.

**Why it matters:** the D1 rider (FR-4 addendum) is verbatim: *"a ghost keep is LOUD
(`KeepNotFoundError`, D2 parity)"*. This is the FR-3 destructive/authority-verb-loud class the
design calls *"the most dangerous in an authz substrate."* The contract pins EXACTLY this for the
sibling verb `delete-keep` (store `TestDeleteKeep::test_delete_keep_of_a_ghost_keep_is_loud` + CLI
`TestDeleteKeepVerb::test_delete_keep_of_a_ghost_keep_is_loud_and_nonzero`) — the asymmetry is the
tell. **THE RIDER IS PART OF THE RULING.**

**The tests that should exist (mirror the delete-keep ghost pins):**
1. `test_keep_remediation_store_61.py::TestSetKeeper::test_set_keeper_of_a_ghost_keep_is_loud` —
   `set_keeper(keep_id=ghost_id(KEEP_TABLE), new_keeper_email=<REAL successor>)` raises
   `KeepNotFoundError`. (Use a REAL new-keeper email so the ghost-EMAIL guard doesn't fire first —
   `_resolve_principal_id` runs before the keep read in the natural build, so a ghost-email +
   ghost-keep fixture would test the wrong door.)
2. `test_keep_remediation_cli_61.py::TestSetKeeperVerb::test_set_keeper_of_a_ghost_keep_is_loud_and_nonzero`
   — `lore-adm set-keeper --keep <ghost> --new-keeper <real>` exits 1 with a `lore-adm:` stderr
   line (`"lore-adm:" in err`, never `startswith`).

Filed as **finding #403**.

---

## P1 — Wrong builds and what caught them (all in scratch; provenance asserted)

`loremaster.__file__ = /tmp/adv-61a/loremaster/loremaster/__init__.py` (proven the copy, not the
original — #140). Each wrong build = the reference build with ONE mutation; restored between runs.

| # | Wrong build | Caught? | Pin(s) that caught it (or MISSED) |
|---|---|---|---|
| WB1 | refuse only keeper-of-**exactly-1** (`if len(kept_rows)==1`) | ✅ | `…_of_MULTIPLE_keeps_names_them_ALL` RED; 3 keeper-of-1 pins pass |
| WB2 | refuse **every** delete | ✅ | (subsumed by HEAD baseline: member-only + loner + member-dim controls red a refuse-all build) |
| WB3 | name only the **first** kept keep | ✅ | `…_of_MULTIPLE_keeps_names_them_ALL` RED (2nd id absent); keeper-of-1 pins pass |
| WB4 | refuse on **membership** (`member_of WHERE in=$p`) not keepership | ✅ | 5 RED — decisively `test_a_member_only_principal_STILL_deletes_cleanly` + the two member-dim/no-dangle controls (member refused) AND the keep-id-naming pins (edge ids ≠ keep ids) |
| WB5 | cascade-DELETE the keeps then succeed | ✅ | every refuse pin's `pytest.raises` fails (build succeeds where it must refuse) — RED at HEAD demonstrates the class |
| WB6 | silent-proceed (no refuse) | ✅ | = HEAD; 21 RED |
| WB7 | `set_keeper` no-op (keep old keeper) | ✅ | store `test_set_keeper_updates…` + `test_after_set_keeper…delete` RED; CLI `test_set_keeper_reassigns…` RED; ghost pins still pass |
| WB8 | `set_keeper` skips ghost-**email** guard (writes dangling `record<principal>`) | ✅ | store + CLI ghost-email pins RED; success pin green |
| WB9 | `delete_keep` skips ghost-**keep** check | ✅ | store + CLI `delete_keep…ghost…loud` RED; success pins green |
| WB10 | `set_keeper` skips ghost-**keep** check | ❌ **BLOCKER** | **NO pin — 31/31 GREEN.** Silent `None` on a ghost keep. → MISSING PIN 1 |
| WB11 | `delete` keeper-check added but `_dispatch` does NOT ready keep slice (#131 D3) | ✅ | `test_delete_readies_the_keep_slice_on_the_fly_when_the_keep_table_is_absent` RED — **the guard is NOT theater** |

**WB11 detail (brief item 3 — the load-bearing #131 verification):** I verified the D3 guard on a
**genuinely keep-table-less** fixture (readies only `principal`+`principal_key`). The guard
**reddens** because `SELECT id FROM keep WHERE keeper=…` against an **undeclared** table **RAISES
`SurrealStoreError`** ("principal query rejected … unspecified rejection") — it does NOT return
`[]`. So the D3 ruling's explicitly-unprobed "SELECT-from-undeclared-table" behaviour is now
settled: **it raises**, which is exactly why the guard discriminates a non-slice-readying build.
Not theater. (This also means the raw `SurrealStoreError` is not laundered by `_dispatch`'s except
tuple — a note for the builder, but the guard REDs either way.)

---

## P1b — QUANTIFIER TABLE (∀-over-inputs vs guarded)

| invariant | classification | receipt |
|---|---|---|
| keeper-of-≥1 delete is REFUSED | ∀ kept-keeps, proxied at N=1 and N=2 | keeper-of-1 pins + keeper-of-MULTIPLE (N=2); WB1/WB3 red the N=2 pin. Residual: N=2 is the ∀ proxy — a `kept_ids[:2]`-style bug on N≥3 would pass (implausible; noted, not a blocker) |
| refusal NAMES all kept keeps | ∀ kept-keeps | keeper-of-MULTIPLE names BOTH; WB3 (name-first) RED |
| refused delete removes NOTHING | ∀ owned children (key, membership, keep, principal) | `test_a_refused_delete_removes_NOTHING` — fixture = keeper WITH key AND membership AND keep; all four survivors asserted |
| member-only delete PROCEEDS + cleans member_of | ∀ (member-not-keeper) | member-dim case-2 + `…STILL_deletes_cleanly` + global no-dangle control; WB2/WB4 red them |
| loner delete cascades ONLY keys, returns count | value-checked | `…loner…cascades_only_its_keys` asserts `cascaded==2` |
| keepership ≠ membership axis | discriminated (one direction suffices) | WB4 red by member-only control. NB no "keeper-but-not-member" fixture is possible (Fork-D auto-members the keeper) — the member-not-keeper direction is sufficient and present |
| set_keeper MOVES keep.keeper (no silent no-op) | ∀ | WB7 RED (FR-3 silent-no-op class) |
| set_keeper ghost-EMAIL is LOUD + changes nothing | guarded | WB8 RED; discriminated from refuse-all by the success pin |
| **set_keeper ghost-KEEP is LOUD** | **guarded — UNPINNED** | **WB10 passes 31/31 → MISSING PIN 1 (BLOCKER)** |
| delete_keep ghost-KEEP is LOUD | guarded | WB9 RED (store + CLI) |
| delete_keep removes keep + member_of; people survive | ∀ endpoints | see P1c reach note (member_of leg is engine-auto-satisfied — a BOUND, honest) |

## P1c — REACH TABLE (guards the contract introduces / relies on)

Legs: **[E]** = empirical wrong-build in scratch; **[C]** = construction-inspection.

| guard / instrument | reach DERIVED? | coverage a checked var? | effect vs proxy | one-source / mutation | verdict |
|---|---|---|---|---|---|
| exact-set `record<principal>` pin (`test_the_record_principal_link_set_matches_the_cascade_adjudication`) | ✅ DERIVED from real `generate_ddl` output via regex | ✅ **[E]** added a NEW `owner_principal record<principal>` link to `_keep_statements` → pin **RED** (grows-and-detects; the 63/64 `owner_principal` tripwire genuinely fires) | effect (scans emitted DDL) | expected-set is a 2-item adjudication hand-list, correct by design (the ADJUDICATION, not the reach) | **SAFE** |
| forward-scope regex reach control (`test_the_forward_scope_regex_has_nonzero_reach`) | n/a (instrument self-test) | ✅ proves the regex matches required AND `option<>`-wrapped links on synthetic DDL | effect | — | **SAFE** (anti-zero-reach; adversary-finding-2 already baked in) |
| #131 D3 keep-slice readiness (`test_delete_readies_the_keep_slice_on_the_fly…`) | reach = the delete path on a dirty (keep-table-less) store | ✅ **[E]** WB11: non-readying build **RED** — genuinely dirty-store fixture (readies only principal+principal_key), confirmed the keep table is truly absent | **effect** (a real `lore-adm delete` on a keep-table-less DB), not a proxy | single delete path | **SAFE — not theater** (settled: undeclared-table SELECT RAISES) |
| member dimension matrix (keeper / member-only / loner) | enumerated FR-4 three-case set | exhaustive over the ruled cases | effect (live store) | — | **SAFE** |
| delete_keep member_of-cascade assertion | — | — | **engine-auto-satisfied** | — | **BOUND (report per brief item 5)** — `_member_of_count_out==0` is satisfied by the engine's LEG-C auto-cascade for ANY build that deletes the keep node; a build that leaves member_of would first fail `get_keep is None`. Honest regression-guard, cannot independently discriminate. Not a defect. |
| `_verb()` / `getattr`-by-name RED guards (finding #133) | per-test | n/a | effect (behavioural RED, not ImportError) | — | **SAFE** (verified: RED-at-HEAD is behavioural, §RED-honesty) |

---

## P2 — Fixture discrimination
All load-bearing fixtures discriminate (proven by the WB table, which is the perturbation done on
the CODE side rather than the fixture side — each wrong build is the "plausible wrong build" a
fixture must reject, and every one except WB10 was rejected):
- keeper-of-1 vs keeper-of-2 (WB1/WB3) — the N-monoculture is broken.
- member-not-keeper is present and decisive (WB4) — the keepership/membership value axis.
- `set_keeper` success vs ghost-email (WB7/WB8) — refuse-all vs refuse-ghost discriminated.
- `_dispatch` readiness: the #131 fixture is a genuinely keep-table-less store (WB11), not a
  virgin full-schema one — the ONLY shape that can see the hazard (#131/§1.6).
Residual (not a finding): the QUANTIFIER proxy for "name ALL keeps" is N=2; a `[:2]`-style bug on
N≥3 would pass. Implausible; flagged for completeness.

## P6 / P6b — Corpse & orphaned-virtue sweeps
- **P6 (retired assertions):** the exact-set pin was RENAMED `test_principal_key_is_the_ONLY_record_principal_link` → `test_the_record_principal_link_set_matches_the_cascade_adjudication` and its expected set widened from `{principal_key}` to `{principal_key, keep.keeper}`. This is the OLD-world corpse correctly retired (the RED_ORPHANED gate → GREEN). `git grep` for the old name: only the docstring mapping-note references it (a deliberate grep-landing breadcrumb per the P8d drift class). No test still asserts the single-link corpse. **SAFE.**
- **P6b (delete/replace):** §FR-4 changes `PrincipalStore.delete` behaviour (adds refuse) but deletes no code path — the existing `principal_key` cascade + return-count are preserved and pinned (`…loner…cascades_only_its_keys` asserts `cascaded==2`, the old behaviour survives). No orphaned virtue.

## RED-honesty (P7)
At HEAD `84d20a3`, the four contract files: **21 failed / 10 passed** — EXACTLY the author's
declared node set. Failures are behavioural (feature unbuilt: `PrincipalHasKeepsError` absent, the
new verbs are unknown subcommands, `set_keeper`/`delete_keep` unbuilt, `delete` of a keeper
SUCCEEDS at rc 0) — not ImportError, not fixture/path error. The `getattr`/`_verb` finding-#133
guards deliver clean behavioural REDs as designed. Reference build → 31/31.

## Satisfiability receipt (independent)
- Built the reference implementation INDEPENDENTLY (before reading the author's, then compared):
  `PrincipalHasKeepsError`; `delete` refuse-while-keeping (`SELECT id FROM keep WHERE keeper=…`,
  names all bare ids + "reassign … or delete"); `_dispatch` readies the keep slice (D3);
  `KeepStore.set_keeper` (ghost-email + ghost-keep loud) / `delete_keep` (ghost-keep loud); CLI
  `set-keeper --new-keeper` / `delete-keep` + `_KEEP_VERB_HANDLERS` registration + parser entries.
- **`loremaster.__file__ = /tmp/adv-61a/loremaster/loremaster/__init__.py`** (provenance asserted
  by `scratch_copy.sh`, re-confirmed by import).
- **`31 passed in 5.97s` (0 failed)** across all four contract files against the reference build.
- Harder leg (ruff/mypy-after-cleanup, C-DEF class): the contract adds ONE new import to
  `principals.py` (`KEEP_TABLE`) that is USED — no orphaned-import trap; no pin conflicts with a
  lint an implementation would trigger. The author's own receipt records ruff+mypy clean on their
  reference; I confirmed behavioural satisfiability independently and did NOT re-run ruff on my
  deliberately-rough scratch reference (it would grade my hygiene, not the contract). No evidence
  of a satisfiable-only-if-lint-fails trap.

## Author-claim verification (P4)
- Declared 21 RED / 10 GREEN at HEAD → **reproduced exactly.**
- Declared satisfiability "61 passed" → that scope was 3 new files + the FULL schema file; the
  CONTRACT's own node set is 31 (3 files + the one revised class), which I ran: 31/31. Consistent,
  not a discrepancy.
- Named mutation-proof expectations → **all reproduced** (WB1/WB3/WB7/WB8/WB9/WB11), EXCEPT the
  "`delete_keep` that leaves member_of → RED" claim, which is **engine-auto-satisfied** (LEG-C
  auto-cascade) and cannot actually be built as a discriminating mutation — a BOUND, reported
  above, not a defect.

## lore-first / fallbacks
Used `lore_get_symbol` / `lore_index` / `lore_findings` / `lore_comms` / `lore_read`. One SAID-OUT-LOUD
grep fallback: `git grep` for the renamed pin name (rename-exhaustiveness, the sanctioned case) and
`grep -n` over `principals.py`/`keeps.py`/`surreal_schema.py` for CLI-dispatch and slice-emitter
structure (cross-cutting multi-question map — sanctioned case). Index was fresh at 84d20a3.

## Scratch worktree
`/tmp/adv-61a` is a disposable `scratch_copy.sh` tree (not a git worktree), restored to the clean
reference build. Holds only throwaway wrong/reference builds — nothing citable. Lead/operator may
`rm -rf /tmp/adv-61a` (and `/tmp/adv-ref-principals.py` / `/tmp/adv-ref-keeps.py`).

---

# RE-GRADE (rev 2, 2026-08-23) — #403 fix + N=3 bump

**VERDICT: CONTRACT SUFFICIENT.** Graded @ HEAD `84d20a3` (unchanged; contract is tests-only).
Focused re-grade of the delta the lead named — verified, not re-derived.

## Delta verified (diff of revised contract vs rev-1 copy)
- **Store:** NEW `TestSetKeeper::test_set_keeper_on_a_ghost_keep_is_loud` — `set_keeper(keep_id=ghost,
  new_keeper_email=<REAL>)` raises `KeepNotFoundError` AND `get_keep(ghost) is None` (no phantom).
- **CLI:** NEW `TestSetKeeperVerb::test_set_keeper_of_a_ghost_keep_is_loud_and_nonzero` — rc 1,
  `"lore-adm:" in err`, `_bare(ghost)` NAMED in err.
- **Quantifier:** `test_deleting_a_keeper_of_MULTIPLE_keeps_names_them_ALL` N=2 → **N=3** (adds
  `keep_c`, asserts a `missing` list is empty — names ALL three).
- Contract now **33 pins** (was 31).

## (a) The 2 new pins discriminate the wrong build — EMPIRICAL
`loremaster.__file__ = /tmp/adv-61a/loremaster/loremaster/__init__.py` (provenance re-asserted).

| build | store `…on_a_ghost_keep_is_loud` | CLI `…of_a_ghost_keep_is_loud_and_nonzero` | other 5 set_keeper pins |
|---|---|---|---|
| **wrong** — `set_keeper` skips the ghost-keep guard (no pre- AND no post-check → silent `None` on a ghost keep) | **RED** (`DID NOT RAISE` / rc 0) | **RED** (`assert 0 == 1`) | pass |
| **correct** — check-first (`get_keep`→`raise KeepNotFoundError` before UPDATE) | pass | pass | pass |

So the fix is properly discriminating: the wrong build passes everything EXCEPT the 2 new pins;
the correct build passes all 33. (Positive control = the full 33/33 reference run below.)

## (b) The phantom-upsert path is closed BY THE ENGINE — SETTLED BY CONSTRUCTION
Probed on the live TEST store (`ws://127.0.0.1:18000`, per-test unique DB): the exact wrong-build
statement `UPDATE type::record('keep', $ghost) SET keeper = type::record('principal', $kid)` on a
nonexistent keep returns **`[]`**, `get_keep(ghost)` reads **`None`**, and the raw `keep` count
stays **0**. **SurrealDB `UPDATE` is update-only — it does NOT upsert a specific nonexistent
record** (consistent with store §2: `UPSERT` is the insert-first verb). Consequence: the store
pin's second assertion (`get_keep(ghost) is None` — "no phantom keep upserted") is a **BOUND /
regression-guard** — it cannot fire on this engine because UPDATE never creates a phantom; the
load-bearing leg is the `pytest.raises(KeepNotFoundError)`. Honest belt-and-braces (it would catch
a future builder who reaches for `UPSERT`, or an engine change) — not a defect. This is the same
honest-bound shape as the delete_keep member_of-cascade assertion (rev-1 P1c).

## N=3 does its job — EMPIRICAL
A `kept_ids[...][:2]` slice-cap bug (which SURVIVES N=2 — the rev-1 residual I flagged) now
**REDs** the N=3 pin: `the refusal must name ALL 3 kept keeps; missing ['01M0PPDP9KN…']`. The 3
keeper-of-1 pins pass. The rev-1 QUANTIFIER residual is CLOSED.

## (c) Satisfiability re-confirmed
- **RED@HEAD (revised contract):** `23 failed / 10 passed` = 33 — matches the author's declared set.
- **Reference build (check-first `set_keeper`):** `33 passed in 6.00s` (0 failed), provenance
  asserted. The only production diffs are my reference additions (keeps.py +40, principals.py +43);
  `surreal_schema.py` clean.
- No orphaned-import / lint trap introduced by the 2 new pins (they add no imports; `ghost_id` /
  `KeepNotFoundError` / `KEEP_TABLE` were already imported in both files).

## Residuals after re-grade
- The store ghost-keep pin's "no phantom" assertion is engine-auto-satisfied (a BOUND, above) —
  honest regression-guard, not a gap.
- The delete_keep member_of-cascade assertion remains engine-auto-satisfied (rev-1 P1c) — unchanged.
- No new gaps found in the delta.

**Nothing survives the revised contract that a correct build wouldn't.** VERDICT: **SUFFICIENT** —
release the builder.

Scratch `/tmp/adv-61a` restored to the reference build (production diffs = reference only). Lead/
operator may `rm -rf /tmp/adv-61a /tmp/adv-ref-principals.py /tmp/adv-ref-keeps.py`.
