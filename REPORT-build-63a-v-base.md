# REPORT — build-63a-v-base (packet 63a-v, base F5-exempt mechanism)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **done**
- deviations: **1** — edited `loremaster/tests/_governed_contract.py` (the R2 docstring on
  `classify_tree_observed_write`), a test-substrate helper, NOT a contract pin. This is the
  deliverable brief item 4 + the R2 pin itself explicitly require ("see REPORT §DECISIONS"). See §DECISIONS.
- Packages considered: `contextvars` (stdlib) + `contextlib` (stdlib) → **bespoke** (mirror of the
  shipped `write_guard` idiom; no package provides task-local governed-write attribution frames — see §DRY).
- Reuse ledger: 3 new symbols (`governed_exempt`, `active_exempt`, `_ACTIVE_EXEMPT`), all dispositioned — §DRY.
- Graded: n/a (builder, not a verdict-rendering report). HEAD-at-report: `1e1d485` (unchanged since spawn; the lead commits).
- decisions-needed: **none**
- receipt POINTERS: 4 RED→GREEN → §FIXES; mutation proof → §MUTATION; gate counts → §GATES; DRY → §DRY.

## §CONTEXT
- HEAD at spawn: `1e1d485d86cfa79466ca190e91679a653c161276` (branch `feat/surreal-unification`).
- Task `e226f9b1b091400db1e7a15a94cf9c9b` claimed by `build-63a-v-base`.
- Investigation order (tests→contract→code): read `test_memory_enforcement_63a_v.py` (the 4 RED define
  GREEN), then `governed.py` (`write_guard`/`active_write_guard` — the idiom to mirror), the already-built
  `_governed_contract.py::{classify_tree_observed_write, observe_governed_table_writes, exempt_entry_is_self_contained}`
  (getattr-tolerant on `active_exempt` at HEAD), `principals.py::_migrate_memory_scope`, and
  `REPORT-adversary-63a-v3.md` §SAT (the reference-build shape, proven 22/0).

## §FIXES — the 4 RED mapped to production changes (contract-first)
RED baseline at `1e1d485` (before any edit): `test_memory_enforcement_63a_v.py` → **4 failed, 20 passed**
(the exact 4 target RED). The minimal fix is the adversary-63a-v3 §SAT reference build (proven 22/0), applied verbatim:

1. **`test_the_governed_exempt_mechanism_is_built`** → `loremaster/loremaster/governed.py`:
   added `_ACTIVE_EXEMPT: ContextVar[str|None]` + `active_exempt() -> str | None` +
   `@contextlib.contextmanager governed_exempt(name)`. A **verbatim mirror** of the shipped
   `write_guard`/`active_write_guard`: task-local (`contextvars`), async-safe across the `await`
   (the name stays set through the store mutation), auto-reset on exit incl. on raise
   (`token = _ACTIVE_EXEMPT.set(name)` / `finally: _ACTIVE_EXEMPT.reset(token)`).
2. **`test_migrate_memory_scope_enters_governed_exempt`** (L2a structural) →
   `loremaster/loremaster/principals.py::_migrate_memory_scope`: wrapped the backfill `run_query(...)`
   in `with governed_exempt("migrate-governed"):`; `governed_exempt` added to the existing inner
   `from loremaster.governed import PROJECT_KEEP_KEY, MigrateGovernedResult, governed_exempt`.
3. **`test_the_live_migration_write_is_attributed`** (L2b runtime, both-ways) → **falls out of 1+2**.
   The already-built observer (`observe_governed_table_writes`) samples `active_exempt()` (getattr) +
   the mutation's `_originating_prod_site()` `(file, symbol)`; the already-built
   `classify_tree_observed_write` matches `entry.exempt_name == "migrate-governed"` AND
   `(entry.site.file, entry.site.function) == ("loremaster/loremaster/principals.py",
   "_migrate_memory_scope")`. With the token now set inside the frame, the live migration write classifies. No observer/classifier edits needed.
4. **`test_classify_tree_observed_write_docstring_names_the_hand_set_label_bound`** (R2) →
   `loremaster/tests/_governed_contract.py::classify_tree_observed_write.__doc__`: added a **NAMED
   ACCEPTED BOUND** clause carrying the 3 concept tokens the pin checks — `guarded_write` (the seam a
   hand-set label bypasses), `honest` (the developer threat model, not the hostile author), `138` (the
   WHEN-YOU-CANNOT-CLOSE-A-HOLE-PIN-IT class) — plus the re-open trigger (untrusted contributor / hosted
   deployment → 63b task 571ef1a). Not the pin — the docstring the pin asserts about.

Post-fix: `test_memory_enforcement_63a_v.py` → **24 passed, 0 failed** (all 4 RED GREEN; the +2 vs the
adversary's 22/0 are the R4 pin-the-miss pins landed since `a48c8a2`).

## §MUTATION — `governed_exempt` mutation-proof (real tree, byte-exact restore)
- `cp -a loremaster/principals.py /tmp/principals_63av_backup.py` (pre-mutation md5 `a2afd5c89b6ea26e399ad9b8575ccc2e`).
- MUTATION: unwrapped `_migrate_memory_scope` (removed `with governed_exempt("migrate-governed"):`, dedented the `run_query`).
- Result: `test_migrate_memory_scope_enters_governed_exempt` (L2a) **RED** AND
  `test_the_live_migration_write_is_attributed` (L2b) **RED** — the live migration write becomes
  UNATTRIBUTED at the F5 seam (no exempt token). Proves the wrapper + the `governed_exempt` channel are load-bearing.
- RESTORED byte-exact: `cp -a` back, md5 re-verified `a2afd5c89b6ea26e399ad9b8575ccc2e` (== pre-mutation). No residue.

## §GATES — receipts (all counts real; scoped set per brief)
| gate | command | result |
|---|---|---|
| target file | `pytest tests/test_memory_enforcement_63a_v.py` | **24 passed, 0 failed** (4.08s) |
| 63a suites + mcp | `pytest {16×test_*63a*.py} tests/test_mcp_server.py -n auto` | **818 passed, 0 failed, 0 skipped**, 3 benign ResourceWarnings (137.5s) |
| 60/61/62 regression | `pytest {6×_61/_61b}.py -n auto` | **68 passed, 0 failed** (9.3s) |
| ruff | `uv run ruff check .` | **All checks passed!** (exit 0) |
| typecheck | `bash scripts/typecheck.sh` (repo root) | **exit 0** (loremaster/skills/doc/eval/scripts/shellcheck all OK) |

- `test_mcp_server.py` ran with **0 skipped** (inside the 818). The 63a-iv suites (F5 coverage,
  ownerfold, prose-currency, reinforce, bounds) + the R4 pin-the-miss pins + the base-3 pin are all in the 818 — no regression.
- **The 2 known pre-existing fails** `test_schema_rebuild.py::TestRebuildingNoticeSeam::test_a8a_search_code_*`
  live in `test_schema_rebuild.py`, which is OUTSIDE my scoped gate set (not a 63a/mcp/61 file) and which
  none of my 3 edits touch. I did NOT run or chase them (brief instruction). My scoped run therefore has **0 failures of any kind**.
- Packet 62's owner-stamp regression is `test_425_stamp_owner_63a.py`, run green inside the 818.

## §DRY — reuse ledger for the 3 new symbols
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `governed_exempt` | `lore_search("governed exempt admin attribution context manager active_exempt")` | only hit is the symbol I just wrote (index picked it up fresh); no pre-existing exempt mechanism | **HAND-ROLLED** — the design §10.9-A CORRECTION step 4 mandates a NAMED exempt channel distinct from `write_guard` (label vs named-token+origin-match are different semantics). Mirrors the `write_guard` **primitive** (stdlib `contextvars` guard), not its policy. |
| `active_exempt` | (same search) | sibling of `active_write_guard`; no pre-existing reader | **HAND-ROLLED** — reader for the new contextvar, mirror of `active_write_guard`. |
| `_ACTIVE_EXEMPT` | (same search) | sibling of `_ACTIVE_WRITE_GUARD` | **HAND-ROLLED** — the module-private contextvar backing the above. |

**Why not REUSE `write_guard`?** The classification POLICY both channels feed is ONE function —
`classify_tree_observed_write` (label-leg OR exempt-leg) — so there is no duplicated policy. The exempt
channel deliberately carries different data (a named token + an origin `(file,symbol)` match) that
`write_guard`'s label cannot express. Mirroring the stdlib contextvars-guard idiom is the "one
contextvar-guard idiom, not a clone of policy" the brief required. This is the shape the adversary-63a-v3
§SAT reference build proved (22/0), and design §10.9-A CORRECTION step 4.

## §DECISIONS — the one writable-set note (R2 / `_governed_contract.py`)
The brief said "production code only — NEVER edit a contract pin to pass." Fix 4 (R2) required editing
`classify_tree_observed_write`'s **docstring** in `loremaster/tests/_governed_contract.py`. This is NOT
editing a contract pin: `classify_tree_observed_write` is a **substrate helper** the pin asserts ABOUT; the
pin itself (`test_classify_tree_observed_write_docstring_names_the_hand_set_label_bound`) is UNTOUCHED. The
R2 pin's own docstring instructs this ("GREEN once the builder adds the bound to
`classify_tree_observed_write`'s docstring in `_governed_contract.py`" + "⚠ COORDINATION: that file must be
in the builder's writable set (see REPORT §DECISIONS)"), and brief item 4 names the edit explicitly. Flagged
here per that instruction. No other test/substrate file was modified.

## §FILES CHANGED (3)
- `loremaster/loremaster/governed.py` — +`_ACTIVE_EXEMPT`, `active_exempt()`, `governed_exempt()` (after `write_guard`).
- `loremaster/loremaster/principals.py` — `_migrate_memory_scope`: import + wrap backfill `run_query` in `governed_exempt("migrate-governed")`.
- `loremaster/tests/_governed_contract.py` — `classify_tree_observed_write.__doc__`: +R2 named-accepted-bound clause.

## §NO-REGRESS CONFIRMATION (brief DO-NOT-REGRESS list)
All in the 818-passed sweep, GREEN: R1/R3 invariants (`TestEveryExemptAllowlistEntryIsSelfContained`,
`TestTheExemptFrameHoldsOnlyItsGuardedMutation`); the R4 pin-the-miss pins (`TestTheAcceptedF5BoundsArePinned`
— R4-a substring + R4-c verb-set bounds still EXIST, NOT closed; 63b root-fix is task 571ef1a, untouched);
the base-3 false-gate docstring (`test_migrate_memory_scope_updates_only_none_scope_rows`); the 63a-iv F5
coverage; #439/owner-fold/corpse/item-5/F-B suites. No new fork surfaced.

## §FORKS
None.
