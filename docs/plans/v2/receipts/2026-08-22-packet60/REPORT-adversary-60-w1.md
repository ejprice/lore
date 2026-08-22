# REPORT-adversary-60-w1 — packet 60 wave 1 CONTRACT ADVERSARY (the Keep substrate)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **VERDICT: CONTRACT INSUFFICIENT** — one concrete missing pin (a surviving wrong build, proven). Otherwise a strong contract: every other wrong build I tried was caught.
- **P1 headline:** 8 core wrong builds ALL caught (atomicity · keeper-lockout · keeper-auto-add · ENFORCED-flip-on-dirty-store · rank-drop-ASSERT · frozen-literal-ASSERT · widened-domain · reach/new-edge · type-monoculture). **ONE wrong build SURVIVED:** a store-law §2 `SELECT *` + bracket `get_keep` (and `list_keeps_for_keeper`) that **KeyErrors on every nameless `dm` keep** passes the full store suite **26/26**, proven broken with a positive control (`get_keep(dm) → KeyError: 'name'`).
- **Capability check:** full — lore tools loaded (keyword form), spike TEST store `ws://127.0.0.1:18000` up, scratch provenance-asserted. All demands satisfiable.
- **Graded:** contract at `f0ebbf4` · HEAD-at-report `f0ebbf4` · **SAME**. (The keep slice + tests are uncommitted working-tree changes on `f0ebbf4`; `git status` confirms `surreal_schema.py`/`_enforced_relations_scaffold.py`/`test_enforced_relations.py` modified + `keeps.py`/`test_keeps_*.py` new.)
- **Scratch provenance receipt:** `loremaster.__file__ = /tmp/adversary-60-scratch/loremaster/loremaster/__init__.py` (via `./scripts/scratch_copy.sh`; re-confirmed by `uv run python -c "import loremaster"`). Every wrong build was mutated + run IN that tree, never the repo.
- **SATISFIABILITY:** ✅ **152 passed / 0 failed** on the reference build, **ruff clean** on both mutated production files. **No C-DEF.**
- **Packages considered:** none new — reference build reuses the shared `_txn` seams (`execute_transaction`/`run_query`) + installed `surrealdb` + `ulid` (the `messages.py` `str(ULID())` precedent). My P-PKG table agrees with the author's "none — no mechanism specified"; nothing package-replaceable is hand-rolled.
- **P6b:** N/A — greenfield slice + stub→build; **no production code is deleted/replaced**. The one "replace" (exact-set pin `_five_`→`_six_known_edges`) preserves its virtue (set-equality still catches drift — proven, attack 7).
- **Pointers:** §Satisfiability · §Attack table · §THE MISSING PIN · §P1b quantifier table · §P1c reach table · §Fixture verdicts · §Residuals · §Verdict.

---

## §Satisfiability receipt (the reference build)

Built the contract's §Satisfiability plan verbatim in scratch: `_keep_statements` = `_define_table` + `_define_field`×specs + call-time `type` ASSERT (NO DEFAULT) + `_plain_index(keep_keeper)`; `_member_of_statements` = `_define_relation_table(enforced=True)` + `_define_field(since)` + call-time `rank` (`DEFAULT 'contributor' ASSERT …`) + `_unique_index(in,out)`; `generate_keep_ddl` = `";\n".join(...)+";\n"`; `KeepStore` CRUD = ULID id, keeper resolved via the composed `PrincipalStore.get_by_email`, CREATE + keeper `RELATE` in ONE `execute_transaction`, check-first-idempotent add, keeper-lockout remove, plain-table reads.

```
152 passed in 7.52s      # pytest -n auto over test_keeps_schema.py + test_keeps_store.py + test_enforced_relations.py, live spike :18000
All checks passed!       # ruff check keeps.py surreal_schema.py  (harder leg: no orphaned-import cleanup needed)
```

Every RED-at-stub pin's failure is a MISSING statement/method, never a contradiction. **Confirmed: no pin is unsatisfiable (no C-DEF).** The author's satisfiability claim holds.

**Q-1 seam (brief landmine #10) — CONFIRMED.** The atomicity injection seam (`monkeypatch keep_store._principals.get_by_email`) holds on the reference build: `test_create_keep_is_ATOMIC…` is GREEN in the 152, because the reference `create_keep` resolves the keeper through the composed `PrincipalStore.get_by_email` (via `_resolve_principal_id`). The seam the author declared is correct; **no move needed.**

---

## §Attack table (P1 — I built each wrong build in scratch and ran the pins)

| # | Wrong build (mutation) | Pin that should catch it | Result |
|---|---|---|---|
| 1 | `create_keep` does CREATE then keeper-RELATE as **two separate `_query`** (non-atomic) | `test_create_keep_is_ATOMIC_a_failed_keeper_edge_leaves_NO_keep_row` | **CAUGHT** — orphan keep (`1 == 0`) |
| 2 | `remove_household_member` with **no keeper special-case** (just DELETE) | `test_remove_household_REFUSES_to_remove_the_KEEPER` | **CAUGHT** — `DID NOT RAISE KeeperLockoutError` |
| 3 | `create_keep` writes `keep.keeper` but **forgets the household RELATE** | `test_create_keep_AUTO_ADDS_the_keeper_to_the_household_at_contributor` | **CAUGHT** — `household=[]`, `0 == 1` |
| 4a | `member_of` migrated with **`IF NOT EXISTS`** (the #107 silent-no-op — ENFORCED in the string, never LANDS) | `TestTheMemberOfEnforcedFlipMigratesADirtyStore::test_the_guard_is_LIVE…DIRTY_store` | **CAUGHT** — `DID NOT RAISE` (guard never landed); positive control (real endpoint accepted) GREEN |
| 4b | `rank` "widened" by **DROPPING the ASSERT** | `TestTheRankDomainWidensSafelyOnADirtyStore::test_POSITIVE_CONTROL_…WIDER_not_GONE` + live `test_an_unruled_rank_is_rejected` | **CAUGHT** — both RED (`overlord` accepted) |
| 5a | `type` ASSERT **hand-frozen as a literal** (not derived from `_KEEP_TYPES`) | `test_changing_the_KEEP_TYPES_tuple_changes_the_emitted_ASSERT` | **CAUGHT** — DDL unchanged under monkeypatch |
| 5b | `_KEEP_TYPES` **widened** (`+'workspace'`) — QUANTIFIER LAW | `test_the_ruled_type_domain_is_EXACTLY_the_closed_set` (offline ∀) + live `test_a_plausible_but_unruled_type_is_rejected_by_the_store` | **CAUGHT** — both RED |
| 6 | **No keeper index** | `TestTheKeeperIndexFires::test_WHERE_keeper_uses_the_index_not_a_keep_tablescan` + offline `test_the_keeper_index_is_IF_NOT_EXISTS_and_NON_unique` | **CAUGHT** — index-built guard fires + offline pin RED |
| 7 | A **new, undeclared, un-enforced** relation edge (`member_of_shadow`) added to a generator | `test_the_relation_edge_set_is_EXACTLY_the_six_known_edges` + `test_EVERY_relation_table_the_schema_emits_is_ENFORCED` | **CAUGHT** — both RED (reach is DERIVED, coverage checked) |
| 8 | `create_keep` **ignores `type`, hardcodes `'project'`** (parameter monoculture) | `test_create_keep_of_type_dm_produces_a_dm_keep` | **CAUGHT** — `'project' == 'dm'` |
| **9** | **`get_keep` = `SELECT *` + `row["name"]` (bracket)** AND `create_keep` builds its return directly (store-law §2 trap) | — **NONE** — | **⛔ SURVIVED — 26/26 pass; proven broken (KeyError on dm keeps)** |

Attacks 1–8 are the brief's landmines #1–#8; #4 covers both the ENFORCED-flip and rank-widening dirty-store legs. Every dirty-store fixture was verified NON-VACUOUS (see below). Reproductions (real output) are pasted in §Probe record.

---

## §THE MISSING PIN (the P1 blocker — attack 9)

**Wrong build that survives:** a `get_keep` (and, identically, `list_keeps_for_keeper`) that reads with `SELECT *` and maps `name` with **bracket access** `row["name"]`, combined with a `create_keep` that builds its returned `Keep` **directly** (reading only `created_at` back) instead of routing through `get_keep`. Both halves are plausible, correct-shaped choices — the satisfiability plan mandates neither an explicit projection nor a `get_keep` read-back inside `create_keep`.

**Why it is broken (store-law §2, verbatim):** *"`SELECT *` … OMITS a `NONE`-valued column ENTIRELY, so `row["col"]` raises `KeyError`."* A `dm` keep is **always nameless** (`name=None` — design Fork E; the store's whole reason for `name` being `option<>`). So `get_keep(<a dm keep>)` does `SELECT *` → the row has no `name` key → `row["name"]` → **`KeyError`**. `get_keep` is 100% broken for `dm` keeps — a first-class type.

**Positive control (proving the wrong build is genuinely broken, not accidentally correct):**
```
create_keep(dm) OK -> id= keep:01M0MZMKEP7QR616VMWR49XGER name= None
get_keep(dm) RAISED KeyError: 'name'   <-- THE UNPINNED BUG (store §2 SELECT* trap)
```
…yet `uv run pytest test_keeps_store.py` → **`26 passed`**. The contract waves it through.

**Root cause — a coverage gap, not a fixture-value gap:** NO test reads a `name=None` keep back through a Keep-returning verb *independently of `create_keep`'s own return value*. `test_get_keep_reads_back_a_created_keep` uses a **named** keep; `test_list_keeps_for_keeper_*` list only **named** keeps; and `test_create_keep_of_type_dm_produces_a_dm_keep` asserts `keep.name is None` on the object `create_keep` **returns** — which a direct-build `create_keep` produces correctly without ever reading `name` back. So the `name=None` input to the read path is unguarded (this is the P1b quantifier row below).

**The pin that should exist (cheap — one or two asserts):**
> **`test_get_keep_reads_back_a_NAMELESS_keep`** — create a `dm` keep (or any `create_keep(..., name=None)`), then call `get_keep(that_keep.id)` **directly** and assert it returns a `Keep` with `name is None` (not a raise). A `SELECT *`+bracket build goes RED here. Mirror it for `list_keeps_for_keeper` — list a keeper who owns a nameless keep and assert the nameless keep appears with `name is None`.

This is the **"a diagnosis is not an instrument"** class (CLAUDE.md, PKT-28 C1): the `get_keep` docstring literally says *"explicit projection — never `SELECT *`, store law §2"*, but the contract ships that as **prose, not a pin**. Store-§ traps that shipped green are this repo's most expensive class (#107, #131). RIGOR-over-speed on a serving read surface says pin it before the builder starts.

---

## §P1b — QUANTIFIER TABLE (every invariant: ∀-over-inputs vs guarded)

| Invariant | ∀ or guarded | Receipt |
|---|---|---|
| Every emitted keep/member_of FIELD is `OVERWRITE` | **∀** over emitted `DEFINE FIELD`s (`test_every_keep_field_definition_is_OVERWRITE` + dual `test_no_field_definition_uses_IF_NOT_EXISTS`) | a single IF-NOT-EXISTS field REDs (offline, both directions pinned) |
| `keep.type` domain == EXACTLY `{project,team,session,dm}` | **∀** (offline exact-set + live plausible-unruled) | attack 5b — widening caught offline AND live |
| `member_of.rank` domain == EXACTLY `{contributor}` | **∀** (offline exact-set + live unruled) | attack 4b — drop-ASSERT + unruled caught |
| Every emitted relation edge is `ENFORCED` | **∀** over `every_emitted_relation_table()` (test_enforced_relations ∀ sweep) | attack 7 — new un-enforced edge caught |
| `member_of` guard LANDS on a dirty store | behavioural ∀-over-store-state (BASELINE/LIVE/positive-control/survives/idempotent legs) | attack 4a — IF-NOT-EXISTS non-landing caught |
| create_keep atomicity (both-or-neither) | **guarded** by the two write doors: CREATE-failure (unruled type) + RELATE-failure (ghost keeper). Those ARE the only two write statements, so the guard is complete. | attacks 1 (RELATE door) + `test_a_REJECTED…` (CREATE door) |
| keeper auto-added to household at `contributor` | ∀ (single property, both legs in one test) | attack 3 |
| remove refuses the keeper | guarded (keeper case) + positive control (non-keeper removal) | attack 2 |
| add_household idempotent (exactly one edge, no raise) | guarded (re-add case) + positive control (two different members) | (raise-on-re-add and second-edge both RED by construction of the UNIQUE backstop) |
| **Keep read-back is correct ∀ `name ∈ {present, NONE}`** | **⛔ GUARDED — and the `name=NONE` door is UNGUARDED for the READ path.** Only `name=present` is read back via `get_keep`/`list_keeps`; `name=NONE` reaches the read path solely through `create_keep`'s return. | **attack 9 — surviving wrong build (§THE MISSING PIN)** |

One guarded row carries a **surviving wrong build** rather than a killing door-build — that is the INSUFFICIENT trigger.

---

## §P1c — REACH TABLE (every guard the contract introduces/relies on)

| Guard | Reach DERIVED or hand-list? | Coverage a checked variable? | Effect or proxy? | One source / mutation-proven? | Legs run |
|---|---|---|---|---|---|
| ∀ ENFORCED / OVERWRITE / IN-OUT sweep (`every_emitted_relation_table` over `ALL_DDL_GENERATORS`) | **DERIVED** — reads emitted DDL TEXT, not a name list | **YES** — `test_the_relation_edge_set_is_EXACTLY_the_six_known_edges` REDs when the emitted set grows but the declared set doesn't | **effect** — behavioural dirty-store RELATE + offline text | one emitter (`_member_of_statements`); `test_BOTH_paths_emit_the_IDENTICAL_member_of_statement` proves slice≡full | **empirical** — attack 7 added a 7th edge → both pins RED |
| keeper-index EXPLAIN pin | reach = the `keeper=$p` predicate | **YES** — asserts the index is BUILT first (else invalid) + positive control (unindexed `type=` IS a keep TableScan) | **effect** — EXPLAIN plan operators | single index emitter | **empirical** — attack 6 (no index → RED); positive control fires on reference build (in the 152) |
| mutation-derivation pins (`_KEEP_TYPES`/`_KEEP_RANKS` monkeypatch) | reach = the ASSERT derivation | **YES** — a frozen literal → DDL doesn't move → RED | **effect** — emitted DDL diff | tuple is the single source | **empirical** — attack 5a |
| exact-set edge pin | **DERIVED** — set-equality emitted-vs-declared | **YES** | effect (emitted text) | `KNOWN_RELATION_EDGES` + `DEFERRED_TO_PACKET_43` allowlist (deny-by-default safe-set) | **empirical** — attack 7 |
| `_query` shared-retry reach (`test_retry_seam.py` scan) | reach = a method named EXACTLY `_query`; `test_the_store_exposes_a__query_seam_named_exactly_query` pins the name | checked (a differently-named seam escapes) | — | routes through shared `run_query` (not re-cloned) | construction-inspection (the shared-retry mutation lives in `test_retry_seam.py`, out of my file set) |

**No reach miss.** Every guard's reach is DERIVED (or a name-pinned method), coverage is a checked variable, effect (not proxy) is observed. The attack-9 gap is NOT a reach-of-a-guard failure — it is a **missing pin** (an unguarded input to the read path), reported above.

---

## §Fixture verdicts (P2 — "what WRONG build would this still pass?")

- **Small-N: adequate.** Household pins use keeper + 2 members = **3 distinct** (`test_add_two_DIFFERENT_members_positive_control`, `test_list_household_returns_every_member`); `list_keeps` uses 2 keeps; the nameless-coexistence pin uses 2 `dm` keeps. `len()`≠`sum()` traps are avoided.
- **Parameter monoculture: adequate for `type`.** `type="project"` is the common value, but `type="dm"` is pinned distinctly (`test_create_keep_of_type_dm…`) and all four types are iterated (`test_every_ruled_type_is_accepted_positive_control`). **Perturbation-proven:** attack 8 (hardcode `'project'`) → the `dm` pin REDs. `rank` has one legal value today (a store invariant, Fork C) so there is no branch to monoculture.
- **Dirty-store fixtures NON-VACUOUS (verified by reading + reference-build green):**
  - ENFORCED-flip: `_dirty_old_world` applies `old_world_ddl` (un-enforced, DERIVED from the production emitter) → seeds a live IN principal → verifies the OUT keep genuinely does NOT exist → RELATEs the dangling edge **under the OLD DDL**, THEN migrates. `TestTheOldMemberOfWorldIsGenuinelyOlder` guards old≠today. The **pre-existing-dangling-edge-SURVIVES** leg (ENFORCED is not retroactive) is present and GREEN.
  - rank-widening: the legacy `member_of` row is written **under today's 1-value DDL** (`_member_of_row_under_todays_ddl`), THEN `_KEEP_RANKS` is widened + re-applied — avoiding the store-§1.4 fixture trap (a row created after the migration fills defaults at CREATE and measures nothing). `'steward'` is accepted only AFTER the widen (so the migration is non-vacuous), and the WIDER-not-GONE positive control rejects `'overlord'`.
- **Over-reach into packet 63 (Fork E): ABSENT — verified.** Anchor-free grep found **no** executable pin asserting a 2-member cap, DM auto-creation-on-send, or `lore_comms` coupling. Every "2-member"/"cap" hit is a docstring *disclaiming* over-reach or a fixture discrimination count (keeper+2=3). Nothing to report (the brief said a member-cap pin would be a defect — there is none).

---

## §Residuals (each with an individual verdict)

- **`set_rank` cannot be discriminated from a no-op today — but this is DESIGN-RULED, not a defect.** `test_set_rank_to_contributor_returns_the_membership` sets `rank='contributor'`, which is also the DEFAULT the member already carries, so a `set_rank` that never touches the store would pass. Fork F rider explicitly rules this trivial ("do NOT gate 60 on multi-rank `set_rank`; the real test lands with the rank widening"). **Verdict: acceptable** — a design-ruled bound with a named re-open trigger (the rank widening in 61+). Not a missing pin.
- **Contract report §D-2 is FACTUALLY INACCURATE (benign).** It claims two stale `test_the_relation_edge_set_is_EXACTLY_the_five_known_edges` references remain in `test_blocks_edge.py` (lines 211, 8888–8890) needing `five→six` edits. **Git shows the opposite:** `test_blocks_edge.py` is UNMODIFIED at `f0ebbf4` and `git show HEAD:…test_blocks_edge.py` already reads `_six_known_edges` at lines 211 and 8890. The corpse sweep (bare, anchor-free) found **zero** `_five_known_edges` anywhere in the test tree. **Verdict: no defect** — the tree is cleaner than the report claims; the report's deviation note is simply wrong. Worth the lead knowing so it isn't chased.
- **`name` trim-aware non-empty ASSERT is inherited, not keep-pinned.** `test_empty_string_name_rejected…` pins `name=""` but not whitespace-only. However `name` reuses the shared module constant `_NON_EMPTY_STRING_ASSERT` (`= "ASSERT string::len(string::trim($value)) > 0"`) directly in the REAL `_KEEP_FIELD_SPECS`, so trim-awareness is structural (a builder can't break it without changing the shared constant, which reddens principal tests). **Verdict: acceptable** — not a missing pin.

---

## §Probe record (commands + real output)

All in `/tmp/adversary-60-scratch` (provenance `loremaster.__file__ = /tmp/adversary-60-scratch/loremaster/loremaster/__init__.py`), `HARNESS_SLUG=general`, live spike `:18000`. Reference production files backed up at `/tmp/adv60-ref-{keeps,schema}.py`; each attack = mutate → run targeted pins → restore.

- **Satisfiability:** `pytest -n auto test_keeps_schema.py test_keeps_store.py test_enforced_relations.py` → `152 passed in 7.52s`; `ruff check keeps.py surreal_schema.py` → `All checks passed!`
- **Attack 1:** non-atomic create_keep → `test_create_keep_is_ATOMIC…` → `AssertionError: … left a keep row behind … assert 1 == 0`.
- **Attack 2:** no keeper guard → `test_remove_household_REFUSES_to_remove_the_KEEPER` → `Failed: DID NOT RAISE KeeperLockoutError`.
- **Attack 3:** forgot keeper RELATE → `test_create_keep_AUTO_ADDS…` → `AssertionError: … household=[] … assert 0 == 1`.
- **Attack 4a:** `IF NOT EXISTS` member_of → `test_the_guard_is_LIVE…DIRTY_store` → `Failed: DID NOT RAISE`; positive-control (`REAL endpoint still accepted`) → passed.
- **Attack 4b:** dropped rank ASSERT → `test_POSITIVE_CONTROL_…WIDER_not_GONE` + `test_an_unruled_rank_is_rejected` → both `DID NOT RAISE`.
- **Attack 5a:** frozen literal type ASSERT → `test_changing_the_KEEP_TYPES_tuple_changes_the_emitted_ASSERT` → `AssertionError: adding a keep type changed no emitted DDL`.
- **Attack 5b:** `_KEEP_TYPES += 'workspace'` → `test_the_ruled_type_domain_is_EXACTLY_the_closed_set` + `test_a_plausible_but_unruled_type_is_rejected_by_the_store` → both RED.
- **Attack 6:** no keeper index → `test_WHERE_keeper_uses_the_index…` + `test_the_keeper_index_is_IF_NOT_EXISTS_and_NON_unique` → both RED (`emits no index on keep.keeper`).
- **Attack 7:** `member_of_shadow` edge → `test_the_relation_edge_set_is_EXACTLY_the_six_known_edges` + `test_EVERY_relation_table_the_schema_emits_is_ENFORCED` → both RED.
- **Attack 8:** hardcoded `type='project'` → `test_create_keep_of_type_dm_produces_a_dm_keep` → `assert 'project' == 'dm'`.
- **Attack 9 (SURVIVES):** `SELECT *`+bracket `get_keep` + direct-build `create_keep` → `pytest test_keeps_store.py` → `26 passed`; standalone probe → `get_keep(dm) RAISED KeyError: 'name'`.

---

## §Verdict

**CONTRACT INSUFFICIENT.** The contract is strong — 8 independent wrong builds caught, the QUANTIFIER LAW pinned both offline and live, the reach fully DERIVED and coverage-checked, dirty-store migrations non-vacuous, no over-reach into packet 63. **One missing pin routes it back to the author:**

> **Add `test_get_keep_reads_back_a_NAMELESS_keep` (and the `list_keeps_for_keeper` mirror):** read a `name=None`/`dm` keep back through the Keep-returning verb **directly** (not via `create_keep`'s return) and assert `name is None`, not a raise. It catches the store-law §2 `SELECT *`+bracket read that ships `get_keep` 100%-broken for the always-nameless `dm` type — the exact "prose-not-a-pin" gap the `get_keep` docstring's own §2 warning describes but does not enforce.

Everything else is either GREEN-on-the-reference-build or an acceptable, design-ruled residual (§Residuals). Once the nameless-keep read-back pin lands, I expect this contract to be SUFFICIENT.
