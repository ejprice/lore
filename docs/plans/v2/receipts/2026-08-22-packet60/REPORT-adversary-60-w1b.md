# REPORT-adversary-60-w1b — packet 60 wave 1 CONTRACT ADVERSARY (focused re-pass)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **VERDICT: CONTRACT SUFFICIENT.** The one missing pin (adversary-60-w1 attack 9 — the store-§2
  `SELECT *` nameless-keep read-back) is CLOSED by 2 additive pins; gap independently re-verified
  closed, no new gap, no weakening, reference build satisfiable → proceed to builder.
- **P1 headline (independent):** on my OWN reference build, the attack-9 wrong build (`SELECT *` +
  bracket `row["name"]`) now goes RED on BOTH new pins (`KeyError: 'name'`) while all 3 NAMED
  controls stay GREEN. I built + mutated + ran this myself; did not copy the reviser's log.
- **SATISFIABILITY:** ✅ **154 passed / 0 failed** on my independent reference build (adversary's
  152 + the 2 new pins). No C-DEF — every RED-at-stub pin is a missing method, never a contradiction.
- **REACH (the important check):** `Keep.name` (the sole `option<string>`) is the ONLY store-§2
  `SELECT *`-omits-NONE trap in the whole slice. All THREE Keep-returning paths are pinned for
  `name=None`: `create_keep`'s return (`test_create_keep_of_type_dm`), `get_keep` (new pin),
  `list_keeps_for_keeper` (new pin). `Membership` is EMPIRICALLY exempt — `rank` (DEFAULT) + `since`
  (DEFAULT) are never NONE; a `SELECT *` + bracket mutation of every Membership read verb stayed
  **9 passed**. No unpinned read verb carries the trap. NO new surviving wrong build.
- **Spot-check of prior 8 (revision touched only test_keeps_store.py):** atomicity → RED;
  ENFORCED-flip → RED×3; exact-set edge (shadow edge) → RED×2. All still caught.
- **P1b quantifier:** the one previously-GUARDED-and-open row is now **∀** — the `name=NONE` door is
  guarded for both read paths + create's return. Every other invariant unchanged from adversary-60-w1.
- **P1c reach:** unchanged — every guard DERIVED, coverage a checked variable, effect (not proxy)
  observed. Attack 9 was a MISSING PIN (unguarded read-path input), now closed; my REACH probe adds
  the empirical Membership-exempt leg.
- **Capability check:** full — lore tools loaded (keyword form), spike TEST store
  `ws://127.0.0.1:18000` up (NEVER :18500), `scratch_copy.sh` provenance-asserted. All demands met.
- **Packages considered:** none — the 2 additive pins specify no mechanism; my reference build reuses
  the shared `_txn` seams (`execute_transaction`/`run_query`) + installed `surrealdb`/`ulid` (the
  `messages.py` `str(ULID())` + `RecordID(...)` precedent). Agrees with "none — no mechanism specified".
- **Graded:** `b9e6335` · HEAD-at-report `b9e6335` · **SAME**. (The keep slice — `keeps.py`,
  `test_keeps_*.py`, the `surreal_schema.py` keep slice, the enforced-relations scaffold — is
  uncommitted working-tree on `b9e6335`; `git status` confirms. adversary-60-w1 graded at `f0ebbf4`;
  the only commit since is `b9e6335`, the D-2 `test_blocks_edge.py` comment-only ref fix.)
- **Scratch provenance receipt:** `loremaster.__file__ = /tmp/adv60w1b-scr/loremaster/loremaster/__init__.py`
  (via `./scripts/scratch_copy.sh`; re-asserted `startswith('/tmp/adv60w1b-scr')` immediately before
  every mutated run). Every build/mutation ran IN that tree, never the repo.
- **Residual (non-blocking, already resolved):** adversary-60-w1's §D-2 residual was itself wrong —
  see §Residuals.
- **Pointers:** §Independent reference build · §Attack-9 re-run · §REACH · §Spot-check · §No-new-gap
  · §Residuals · §Verdict.

---

## §Independent reference build (satisfiability)

I built the contract's §Satisfiability plan MYSELF in a provenance-asserted scratch copy (NOT the
reviser's) — reading the real DDL helpers (`_define_table`/`_define_field`/`_define_relation_table`/
`_plain_index`/`_unique_index`) and the `PrincipalStore`/`messages.py` idioms (`CONTENT`,
`type::record`, explicit projection, `RecordID`, `str(ULID())`, one `execute_transaction`):

- **schema:** `_keep_statements` (SCHEMAFULL keep table + `_KEEP_FIELD_SPECS` fields routed through
  `_define_field` → OVERWRITE + call-time `type` ASSERT from `_KEEP_TYPES`, NO DEFAULT + non-unique
  `keeper` index); `_member_of_statements` (`_define_relation_table(..., enforced=True)` → `OVERWRITE
  … ENFORCED` + `since` + call-time `rank` DEFAULT/ASSERT from `_KEEP_RANKS` + UNIQUE(in,out));
  `generate_keep_ddl = ";\n".join(...) + ";\n"`.
- **CRUD:** ULID id; keeper resolved via the COMPOSED `PrincipalStore.get_by_email`; CREATE + keeper
  `RELATE` in ONE `execute_transaction`; **read verbs use an EXPLICIT projection + `row.get("name")`**
  (`_KEEP_READ_PROJECTION = "id, keeper, type, name, created_at"`); `create_keep` builds its return
  DIRECTLY (attack-9 shape — so mutating the read verbs leaves `create_keep` untouched).

```
154 passed in 7.71s   # pytest -n auto  test_keeps_schema.py test_keeps_store.py test_enforced_relations.py
                      #   live spike :18000, HARNESS_SLUG=general
```

The instrument that applies this build is committed as a pasted code fence below (the scratch tree is
disposable by design). Reference-build patcher: `/tmp/adv60w1b_build.py` (reads the pristine repo
stubs, patches, writes to scratch; lambda repls to survive re's escape processing). Its essence:

```python
# schema: fill the 3 RED-STUB functions
def _keep_statements():
    type_allowed = ", ".join(f"'{v}'" for v in _KEEP_TYPES)
    type_spec = ("type", "string", f"ASSERT $value IN [{type_allowed}]")
    st = [_define_table(KEEP_TABLE)]
    st += [_define_field(KEEP_TABLE, n, t, constraint=c) for n, t, c in (*_KEEP_FIELD_SPECS, type_spec)]
    st.append(_plain_index(KEEP_TABLE, f"{KEEP_TABLE}_keeper", ("keeper",)))
    return st
def _member_of_statements():
    rank_allowed = ", ".join(f"'{v}'" for v in _KEEP_RANKS)
    rank_spec = ("rank", "string", f"DEFAULT '{_KEEP_RANK_CONTRIBUTOR}' ASSERT $value IN [{rank_allowed}]")
    st = [_define_relation_table(MEMBER_OF_RELATION, PRINCIPAL_TABLE, KEEP_TABLE, enforced=True)]
    st += [_define_field(MEMBER_OF_RELATION, n, t, constraint=c) for n, t, c in (*_MEMBER_OF_FIELD_SPECS, rank_spec)]
    st.append(_unique_index(MEMBER_OF_RELATION, f"{MEMBER_OF_RELATION}_in_out", ("in", "out")))
    return st
def generate_keep_ddl():
    return ";\n".join(_keep_statements() + _member_of_statements()) + ";\n"
# get_keep / list_keeps_for_keeper: SELECT {_KEEP_READ_PROJECTION} ...  ->  _row_to_keep uses row.get("name")
```

---

## §Attack-9 re-run (the core re-verification — my own build+mutation)

**Mutation** (3 one-line edits on my reference `keeps.py`): `get_keep` and `list_keeps_for_keeper`
projection `SELECT {_KEEP_READ_PROJECTION}` → `SELECT *`; `_row_to_keep` name mapping
`self._optional_str(row.get("name"))` → `row["name"]` (bracket).

Ran the 2 new pins + 3 named controls (live spike):
```
2 failed, 3 passed in 1.73s
FAILED  TestGetKeep::test_get_keep_reads_back_a_NAMELESS_keep              -> KeyError: 'name'
FAILED  TestListKeepsForKeeper::test_list_keeps_for_keeper_lists_a_NAMELESS_keep -> KeyError: 'name'
PASSED  TestGetKeep::test_get_keep_reads_back_a_created_keep              (named control)
PASSED  TestListKeepsForKeeper::test_list_keeps_for_keeper_returns_their_keeps (named control)
PASSED  TestCreateKeep::test_create_keep_of_type_dm_produces_a_dm_keep    (create's own return)
```
The KeyError traceback shows the `SELECT *` row dict for the `dm` keep, with the store §2 omission
made visible — **there is no `name` key at all**:
```
row = {'created_at': datetime(...), 'id': RecordID(keep,...), 'keeper': RecordID(principal,...), 'type': 'dm'}
>   name=row["name"]
E   KeyError: 'name'
```
Restoring the reference build (re-run the patcher) → 154 pass again. The 3 named controls staying
GREEN is the discriminating fact: the wrong build is broken SPECIFICALLY for the always-nameless `dm`
type, and `create_keep(dm)`'s own return is unaffected — exactly why attack 9 survived the original
contract, and exactly what the 2 read-path pins now close. **Gap independently confirmed closed.**

---

## §REACH — every Keep/Membership-returning read verb × the store-§2 SELECT*+bracket trap

The trap fires ONLY on an `option<>` column left NONE (`SELECT *` omits the key → `row["col"]`
KeyErrors). I enumerated the value objects' fields from the schema:

| value object | fields | any NONE-omittable (`option<>` unset) column? |
|---|---|---|
| `Keep` | `keeper` (required link), **`name` (`option<string>`)**, `type` (required, ASSERT), `created_at` (DEFAULT) | **YES — `name` only** |
| `Membership` | `in`/`out` (auto, always present), `rank` (DEFAULT `contributor`), `since` (DEFAULT `time::now()`) | **NO — every field always present** |

Read verbs that surface each object (via a FRESH store read):

| verb | returns | nameless/NONE coverage |
|---|---|---|
| `create_keep` (its own return) | `Keep` | `test_create_keep_of_type_dm_produces_a_dm_keep` asserts `name is None` |
| `get_keep` | `Keep \| None` | **`test_get_keep_reads_back_a_NAMELESS_keep` (NEW)** + named control |
| `list_keeps_for_keeper` | `list[Keep]` | **`test_list_keeps_for_keeper_lists_a_NAMELESS_keep` (NEW)** + named control |
| `add_household_member` / `set_rank` / `_read_membership` | `Membership` | exempt (no NONE column) |
| `list_household` | `list[Membership]` | exempt (no NONE column) |
| `remove_household_member` | `None` | no object |

**Empirical exemption proof (not just asserted):** I mutated EVERY Membership read verb
(`list_household`, `add_household_member`, `set_rank`, `remove_household_member` /
`_read_membership` / `_row_to_membership`) to `SELECT *` + bracket `row["rank"]`/`row["since"]` and ran
the household/membership pins:
```
9 passed in 2.65s   # TestListHousehold TestAddHouseholdMember TestSetRank TestRemoveHouseholdMember
```
GREEN under `SELECT *` + bracket ⇒ `Membership` genuinely carries NO NONE-omittable column ⇒ there is
NO unpinned store-§2 trap on any Membership-returning verb. **The trap reaches EXACTLY `Keep.name`, and
all three Keep-returning paths are pinned. No new surviving wrong build in another read verb.**

---

## §Spot-check — prior 8 wrong builds still caught (revision only added 2 test methods)

| prior attack | mutation | pins | result |
|---|---|---|---|
| 1 — atomicity | `create_keep` CREATE + RELATE as two SEPARATE `_query` (non-atomic); ghost-keeper monkeypatch ⇒ RELATE refused, CREATE already committed | `test_create_keep_is_ATOMIC_a_failed_keeper_edge_leaves_NO_keep_row` | **RED** (1 failed — orphan keep) |
| 4a — ENFORCED-flip | `member_of` emitted `enforced=False` | offline `…is_OVERWRITE_and_ENFORCED…` + `TestTheMemberOfEdgeIsGuardedFromBirth[both paths]` | **RED×3** (1 passed = IN/OUT pin, unaffected) |
| 7 — exact-set edge | added undeclared un-enforced `member_of_shadow` edge to the generator | `test_EVERY_relation_table_the_schema_emits_is_ENFORCED` + `test_the_relation_edge_set_is_EXACTLY_the_six_known_edges` | **RED×2** (reach is DERIVED — a NEW edge is caught) |

All three unaffected by the revision, as expected (it only added 2 methods to `test_keeps_store.py`).

---

## §No new gap / no weakening (the 2 additive pins)

- **Additive:** satisfiability went 152 → **154**; no existing pin's behaviour changed. The 2 pins
  reuse the file's `keep_env` fixture, `_KEEPER_EMAIL`, `Keep`/`KeepStore` API — no new production
  symbols, no new mechanism. The named controls (`test_get_keep_reads_back_a_created_keep`,
  `test_list_keeps_for_keeper_returns_their_keeps`) are unchanged and still pass.
- **Non-vacuous:** each new pin pairs the `name is None` assertion with a NAMED positive control read
  back through the SAME verb, so it is not vacuously true of a verb that always returns `name=None`
  (the `SELECT *`+bracket mutation reddens the nameless leg while the named control leg stays green —
  proven above).
- **Discriminating (P2):** the list pin keys results in `by_id` and asserts `nameless.id in by_id`
  AND `by_id[nameless.id].name is None` AND `named.id in by_id` AND `by_id[named.id].name == "named
  one"` — no `len()==sum()` trap, and `name ∈ {present, NONE}` is a genuine two-value discrimination
  on the branchable field. A silent-drop build (`except KeyError: continue`) is caught by
  `nameless.id in by_id`; a `name=""` build is caught by `is None`.
- **RED-honesty (P7):** on the REAL-repo stub both new pins fail BEHAVIOURALLY —
  `NotImplementedError: packet-60 wave-1 builder fills create_keep` at `keeps.py:370` — never an
  ImportError/collection error. They green only when the builder lands the correct read shape.

---

## §Residuals (each with an individual verdict)

- **adversary-60-w1's §D-2 residual was ITSELF inaccurate (now resolved, non-blocking).**
  adversary-60-w1 claimed contract-60-w1's §D-2 note (that `test_blocks_edge.py` carried stale
  `_five_known_edges` refs needing a five→six fix) was "simply wrong / the tree is cleaner than the
  report claims," asserting `git show f0ebbf4:…test_blocks_edge.py` already read `_six` at L211.
  **`git show b9e6335` refutes that:** its diff shows L211 was `_five_known_edges` at `f0ebbf4` (the
  parent), changed to `_six` — i.e. the D-2 note was CORRECT and the fix WAS needed. It is now
  committed at `b9e6335` (`fixer-60-blocks-refs`, comment/docstring-only, 4 lines, no test-behaviour
  change; `test_blocks_edge.py 220 passed`, ruff clean). **Verdict:** a re-derive-the-inherited-claim
  miss in the prior residual, fully resolved and NON-BLOCKING for the keep contract. Surfaced so the
  lead does not inherit "D-2 was wrong" as fact.
- **`set_rank` still cannot be discriminated from a no-op today** — design-ruled (Fork F rider: the
  real test lands with the rank widening in 61+). Unchanged from adversary-60-w1. **Verdict:**
  acceptable, named re-open trigger. Not a missing pin.
- **`name` whitespace-only ASSERT is inherited, not keep-pinned** — `name` reuses the shared
  `_NON_EMPTY_STRING_ASSERT` (trim-aware) directly in `_KEEP_FIELD_SPECS`, so trim-awareness is
  structural. Unchanged from adversary-60-w1. **Verdict:** acceptable.

---

## §Probe record (commands + real output)

All in `/tmp/adv60w1b-scr` (`loremaster.__file__ = /tmp/adv60w1b-scr/loremaster/loremaster/__init__.py`),
`HARNESS_SLUG=general`, live spike `:18000`. Reference restored between every mutation by re-running
`/tmp/adv60w1b_build.py` (reads pristine repo stubs → patches → writes scratch).

- **Satisfiability:** `pytest -n auto test_keeps_schema.py test_keeps_store.py test_enforced_relations.py`
  → `154 passed in 7.71s`.
- **Attack-9 mutation:** 2 `SELECT *` + 1 bracket `row["name"]` → 2 new pins + 3 named controls →
  `2 failed, 3 passed`; both fails `KeyError: 'name'` (row dict lacks `name` key for the `dm` keep).
- **REACH / Membership-exempt:** `SELECT *` + bracket on every Membership read verb → household suite
  → `9 passed`.
- **Spot-check A (atomicity):** non-atomic `create_keep` → atomicity pin → `1 failed`.
- **Spot-check B (ENFORCED):** `enforced=False` → `3 failed, 1 passed`.
- **Spot-check C (exact-set edge):** `member_of_shadow` un-enforced edge → `test_enforced_relations.py`
  → `2 failed, 66 passed` (ENFORCED ∀ sweep + exact-set edge pin).
- **RED-honesty (real repo stub):** 2 new pins → `2 failed`, both `NotImplementedError` at
  `keeps.py:370`.

---

## §HANDOFF
- **Scratch cleanup owed to the lead:** `rm -rf /tmp/adv60w1b-scr` was **guardrail-denied** (bare and
  compound). The scratch tree (a `scratch_copy.sh` copy, ~580M in `/tmp`, disposable by design) is
  still on disk — the lead may reap it. Also disposable: `/tmp/adv60w1b_build.py` (the pasted
  reference-build essence in §Independent reference build makes it re-derivable).
- One-shot: task `ee1a7495d8c94f6a8b37220556a0ab1a` → done; I retire and exit. The lead commits the
  full keep contract with the build once green — I do NOT commit.

## §Verdict

**CONTRACT SUFFICIENT.** adversary-60-w1's single missing pin (attack 9) is closed by two additive,
mutation-proven, non-vacuous pins. I independently: built a correct reference (154 pass, no C-DEF),
reproduced attack 9 and watched BOTH new pins redden while the 3 named controls held, and PROVED the
reach — `Keep.name` is the only store-§2 `SELECT *`-omits-NONE trap in the slice, all three
Keep-returning paths are pinned, and `Membership` is empirically exempt (no unpinned read verb carries
the trap). The prior 8 wrong builds remain caught. No new gap, no weakening. Proceed to the builder.
