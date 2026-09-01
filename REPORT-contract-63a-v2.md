# REPORT-contract-63a-v2 — fold R1 self-containment pin + R2 #138 docstring bound (RED contract revision)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- receipt: brief-base v14 read · brief project v7 read
- state: **done** (two step-6 riders folded as pins; RED-for-the-right-reason where RED; gates green)
- deviations: (1) added ONE test-infra helper `exempt_entry_is_self_contained` to `_governed_contract.py`
  (brief-permitted: "ONLY if R1 needs a new helper, reuse `function_calls_named`" — it does); no base
  pin or 63a-iv coverage touched. (2) R2 is RED-until-built and goes GREEN only by editing the
  `classify_tree_observed_write` DOCSTRING in `_governed_contract.py` — the **builder's writable set
  must include that file** (see §DECISIONS).
- Packages considered: none — no new production mechanism specified. R1's helper is a pure predicate
  reusing the in-tree `function_calls_named` (stdlib `ast`); R2 is a `__doc__` substring assertion. No
  package replaces an AST scan or a docstring check. `Packages considered: none — no mechanism specified`.
- Reuse ledger: 1 new symbol (`exempt_entry_is_self_contained`) — §DRY (HAND-ROLLED, REUSES `function_calls_named`).
- Graded: n/a — contract author, not a verdict-rendering audit. (HEAD authored at `3aea565`; committed at the SHA below.)
- decisions-needed: **ONE** — R2 GREEN requires the builder to edit a docstring in `_governed_contract.py`;
  the builder's brief must grant that file (or the lead may prefer I write it now as a GREEN invariant). §DECISIONS.
- receipt POINTERS: R1 shape+invariant-vs-hook → §R1; R1 mutation-proof → §R1 / test
  `test_the_self_containment_check_reds_a_non_self_contained_exempt_entry`; R2 → §R2; count → §COUNT;
  satisfiability → §SAT; gates → §GATES; DRY → §DRY.

---

## §R1 — the EXEMPT-ENTRY SELF-CONTAINMENT VALIDITY pin (primary; a discriminating pin)

**Shape (fixed by the adversary spec — NOT softened).** For each `TreeWriteAllowlistEntry` whose
`exempt_name is not None`, assert the entry's L1-derived literal site == its seam-call site: the
function enclosing the raw mutation literal (`entry.site.function`) ALSO calls the store seam
(`run_query`/`execute_transaction`) in `entry.site.file`. Fail-CLOSED if it does not. Built with the
EXISTING `function_calls_named` (design §3.2 ONE-IMPLEMENTATION; 63b/64 reuse the predicate).

**Symbols folded:**
- Helper `_governed_contract.exempt_entry_is_self_contained(entry, *, source) -> bool` — the pure
  predicate (reuses `function_calls_named`; source-parametrised so the live pin reads the real file
  and the mutation-proof passes a synthetic source).
- Live pin `TestEveryExemptAllowlistEntryIsSelfContained::test_every_exempt_allowlist_entry_is_self_contained`
  — iterates `MEMORY_TREE_ALLOWLIST`'s exempt entries, anti-vacuity asserts ≥1 exists, asserts each self-contained.
- Discrimination mutation-proof `…::test_the_self_containment_check_reds_a_non_self_contained_exempt_entry`.

**GREEN-as-invariant vs RED-until-hook → R1 is a TEST-INFRA INVARIANT (GREEN at fold).** VERIFIED
(not assumed): `principals.py::_migrate_memory_scope` (the sole exempt entry, token `"migrate-governed"`)
holds BOTH the raw UPDATE literal `f"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE"`
(principals.py:1187) AND its `run_query` seam call (principals.py:1181) in ONE symbol → self-contained
→ the live pin is GREEN. It needs **no production hook**: the premise is a property of the ALLOWLIST
(test data), so its enforcement is a validity invariant, not a RED-until-built production gap. The
adversary's REACH-ATTACK finding is that self-containment was a HIDDEN CONSTANT (true for the one
current entry, unchecked ∀); R1 makes it a CHECKED VARIABLE.

**Mutation-proof (REQUIRED because GREEN-as-invariant — the discrimination is proven, not assumed).**
`test_the_self_containment_check_reds_a_non_self_contained_exempt_entry` (GREEN) constructs a SYNTHETIC
fragment-builder exempt entry — literal in `_build_fragment`, seam call in `_drain` (the exact
non-self-contained future candidate design step 6 R1 names) — and asserts the predicate returns
**False**; plus a self-contained POSITIVE CONTROL (literal + seam in `_do_write`) returning **True**.
Both synthetics carry the SAME token, so a predicate that special-cased the token name — or returned a
constant — fails one of the two legs (CLAUDE.md PKT-28 "a probe needs a positive control"). This
**excludes the wrong build the adversary warned of**: a check that passes only migrate-governed but
does not red a genuine non-self-contained entry. The next-in-pipeline adversary constructing a
non-self-contained exempt entry INTO `MEMORY_TREE_ALLOWLIST` will find the live pin reds (it iterates ∀
exempt entries) — confirmed by the same predicate the mutation-proof exercises.

**What wrong build passes R1? (interrogated)** — (a) `return True` → the synthetic non-self-contained
leg reds; (b) `return False` → the positive-control leg reds; (c) `return entry.exempt_name == <X>` →
both synthetics share a token so one leg reds; (d) a live pin with no anti-vacuity → excluded by the
`assert exempt_entries` guard. None survive.

## §R2 — the #138-class HAND-SET-LABEL accepted bound, NAMED in the instrument docstring (secondary)

`classify_tree_observed_write` returns True on ANY write carrying a `write_guard` label
(`if observed.label is not None: return True`) — so a production site that hand-sets the label WITHOUT
routing through `guarded_write` is CLASSIFIED. That is an ACCEPTED bound under the gate's threat model
(the honest developer, not the hostile author — the #138 class), never closed by false positives (a
gate that reds honest code gets switched off — CLAUDE.md "A GATE NEEDS A THREAT MODEL").

**Mapped to the docstring of `classify_tree_observed_write`** (the exact site of the `label is not None`
behaviour; design offers "or `observe_governed_table_writes`" — I chose the classifier as the bound's
true home). Pin `TestTheHandSetLabelBoundIsNamedInTheInstrumentDocstring::test_classify_tree_observed_write_docstring_names_the_hand_set_label_bound`.

**RED-until-built.** At fold the docstring names NONE of the bound's concepts (grep = 0). The
**non-trapping matcher** requires only the three load-bearing concept tokens the design + CLAUDE.md
gate-law use: `guarded_write` (the mechanism a hand-set label bypasses), `honest` (the threat-model
term of art), `138` (the accepted-bound class) — never an exact phrasing. §SAT proves a faithful
docstring AND a reworded paraphrase both green it. The adversary framed R2 as "a named-bound rider,
NOT a pin"; the spawn brief instructs a PIN (spawn brief > adversary in precedence), so it is a pin.

## §COUNT — `test_memory_enforcement_63a_v.py` module-local @ commit

**4 failed, 16 passed** (was 3 failed / 14 passed at base `194f3c8`; +3 tests: R1×2 GREEN, R2×1 RED).
- 4 RED = the 3 base RED-until-built production-gap pins (`…governed_exempt_mechanism_is_built`,
  `…migrate_memory_scope_enters_governed_exempt`, `…live_migration_write_is_attributed`) **+ R2**
  (`…docstring_names_the_hand_set_label_bound`, RED-for-the-right-reason: docstring unwritten).
- 16 GREEN = the 14 base GREEN pins + R1's two legs (invariant + discrimination), explicitly verified
  PASSED by name (`TestEveryExemptAllowlistEntryIsSelfContained` → 2 passed).
- 63a-iv coverage untouched: `test_memory_enforcement_63a_iv.py` + `_bounds_63a_iv.py` → **12 passed**
  after the shared-infra edit (the added helper broke nothing).

## §SAT — satisfiability receipts (C-DEF: a pin RED on a correct build is a trap)
- **R1**: GREEN at fold (satisfied by the real allowlist) — no builder action, no trap possible.
- **R2**: a faithful bound clause greens the matcher (missing `[]`); a reworded paraphrase (`honest
  engineer`, `#138-class`, `routing through guarded_write`) ALSO greens it (missing `[]`) — the matcher
  is non-trapping and phrasing-robust. Receipt: the inline `uv run python` check in the session
  (transcribed in §SAT-CODE below).

### §SAT-CODE — the R2 satisfiability probe (an instrument is a deliverable — brief-base §1)
```python
faithful = ("NAMED BOUND (design step 6 R2, the #138 class): a production site that hand-sets a "
    "write_guard label WITHOUT calling guarded_write passes both F5 layers — an ACCEPTED bound "
    "under this gate's threat model (the honest developer, not the hostile author), never closed "
    "by false positives.").lower()
paraphrase = ("accepted #138-class bound: hand-setting the write_guard label without routing through "
    "guarded_write still classifies; threat model is the honest engineer, not a hostile author.").lower()
required = ["guarded_write", "honest", "138"]
assert [t for t in required if t not in faithful] == []      # GREEN
assert [t for t in required if t not in paraphrase] == []    # GREEN (phrasing-robust)
```

## §DECISIONS — the one coordination point (escalate to lead-63)
**R2 goes GREEN by editing `classify_tree_observed_write`'s docstring in `_governed_contract.py`.**
That file is TEST INFRA, not production. Two readings, my pick first:
1. **(RECOMMENDED) The builder's writable set includes `_governed_contract.py`** for the R2 docstring
   addition — consistent with the whole F5 instrument being co-built as test infra across this
   packet's waves. The pin's failure message tells the builder exactly what clause to add and where.
2. The lead may instead have ME (contract author) write the docstring now, flipping R2 to a GREEN
   invariant like R1 (removes the cross-file build dependency). I did NOT do this because the brief
   says R2 is "RED-until-built"; if the lead prefers option 2, say so and I will fold it.
No other forks or spec ambiguities. R1's assertion is the adversary's fixed spec, unsoftened.

## §DRY — reuse ledger
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `exempt_entry_is_self_contained` | `lore_search("exempt entry self-contained literal site equals seam call site validity check")` | no existing self-containment predicate (nearest: the classifier control `test_a_matching_exempt_token_classifies` + an unrelated `_BRANCH_COVERAGE_EXEMPT` earned-set) | **HAND-ROLLED**, REUSING `function_calls_named` (the channel-agnostic 'does frame call `<name>`' scan) — a pure composition, not a fork; 63b/64 exempt entries reuse it |

New test classes/methods are pins, not reusable symbols (no DRY row required).

## §GATES (@ commit)
- `test_memory_enforcement_63a_v.py` module-local: **4 failed, 16 passed** (the 4 RED are RED-until-built).
- R1 explicit: `TestEveryExemptAllowlistEntryIsSelfContained` → **2 passed**.
- 63a-iv modules (untouched coverage): **12 passed, 0 failed**.
- `uv run ruff check .` → **All checks passed!**
- `bash scripts/typecheck.sh` → **exit 0** (Success across all 7 members incl. test trees + shellcheck).

## §WRITABLE-SET
Touched: `loremaster/tests/test_memory_enforcement_63a_v.py` (import + R1/R2 pin classes),
`loremaster/tests/_governed_contract.py` (the ONE new helper `exempt_entry_is_self_contained`),
`REPORT-contract-63a-v2.md`. No production code. No base pin / 63a-iv coverage modified. NEVER pointed
a test at :18500 (the live migration pin uses `migration_world` → `ws://127.0.0.1:18000`).

## §PIPELINE
NEXT: the contract-adversary grades THIS revision (no contract revision skips the adversary), THEN the
builder. The adversary's expected confirmations: R1 reds on a constructed non-self-contained exempt
entry; R1 is not vacuous (the discrimination mutation-proof); R2 is a legible RED-until-built pin.
