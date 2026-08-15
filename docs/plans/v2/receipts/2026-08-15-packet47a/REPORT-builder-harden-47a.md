# REPORT-builder-harden-47a — BUILDER, packet-47a HARDENING wave (R2 guard + R1/R3 pins)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done-with-deviations — the 2 RED hardening pins (PIN A #375 R2 guard, PIN C #131
  R3 docs) are now GREEN; the 43 already-GREEN pins stay GREEN. **45 passed ×3** on the real
  tree (spike-surreal `:18000`).
- **Deviation 1 (in-scope regression I caused — fixed, prominent):** the guard's first form
  eagerly evaluated `self._store.registered_entity_tables()` for EVERY compose in
  `_entity_fragment`; **96 tests** using the `FakeSurrealStore` double (no such method)
  reddened. FIX: `ready_claiming_extension` takes the STORE (brief-sanctioned "or pass the
  store") and reads the registered set **LAZILY — only when a claimant exists**, so a
  no-extension compose imposes no store-surface requirement. Regression resolved (198 passed).
  §REGRESSION.
- **Deviation 2 (design refinement — FLAG for Fable/lead):** the R2 raise rides a NEW shared
  compose-path dispatch `ready_claiming_extension` that REUSES `claiming_extension`, NOT a
  signature change to `claiming_extension` itself — because the frozen **CF8** pin monkeypatches
  `claiming_extension` with a **3-arg** shim and drives all 3 sites; a 4th arg reddens a pin I
  may not edit. Purge sites (watcher/reconcile) keep calling bare `claiming_extension` (no
  readiness leg) — purge is DELETE (harmless on unready), not the CREATE corruption path.
  Fable's property is honored; the "purge sites skip readiness" refinement wants a bless. §GUARD.
- **Packages considered:** none — no library-backed mechanism specified (the guard is domain
  policy; the readiness check is stdlib set-subset over declared-vs-registered table names).
- **Reuse ledger:** 2 new production symbols, all dispositioned (§DRY): `ready_claiming_extension`
  (REUSES `claiming_extension`), `SurrealStore.registered_entity_tables` (read-side of the
  existing `register_entity_tables`). 1 flagged duplication (declared-tables union in 3 sites).
- **Graded:** N/A (builder, not a verdict-render) — base `91fc30e`; `git rev-parse HEAD` = `91fc30e`;
  SAME. My 7-file change is UNCOMMITTED on top (lead commits). Real-tree provenance receipt
  (`loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py`).
- **Decisions-needed:**
  1. **Fable/lead (bless the refinement):** readiness rides `ready_claiming_extension` (wrapping
     `claiming_extension`), and PURGE sites skip readiness. Reason: frozen CF8 forbids the
     signature change; purge is not the corruption path. §GUARD.
- Receipt pointers: guard §GUARD · mutation proofs §MUTATIONS · regression fix §REGRESSION ·
  R3 docs §R3 · test-prose verdicts §PROSE · gates §GATES · store-law §STORE-LAW.

---

## THE R2 GUARD — where the raise lives + the readiness mechanism {#GUARD}

**Fable ruled (REPORT-design-sidecar-47a.md §"R2 guard placement", BLESS A):** the raise at the
COMPOSE SINK `Indexer._entity_fragment` (which every claimed-file compose — realtime
`_compose_file_fragments` AND batch `_commit_batch_file` — funnels through), *sourced from the
shared `claiming_extension` dispatch*, with `_entity_fragment` staying a thin "ask dispatcher,
build if claimed".

**What I built (faithful to that property, satisfiable against the frozen contract):**
- **`loremaster.extension.ready_claiming_extension(extensions, tier, path, ctx, store)`** — a NEW
  shared compose-path dispatch. It REUSES `claiming_extension` for the exclusivity rule (never a
  second copy — ONE IMPLEMENTATION), then layers the readiness fail-fast: if a sole claimant
  exists AND `set(declared) ⊄ set(store.registered_entity_tables())` → raise
  `ExtensionLifecycleNotReadyError` naming the extension AND the missing table(s). `declared` is
  the order-preserving union of `claimant.ingest_backends(ctx)` → `backend.entity_tables()` — the
  SAME union `build_app_context` and `_white_box_indexer` compute (derive-don't-enumerate).
- **`Indexer._entity_fragment`** now just calls `ready_claiming_extension(self._extensions, tier,
  path, ctx, self._store)` and builds if a claimant returns — thin, as ruled.
- **`SurrealStore.registered_entity_tables()`** — new read-side accessor over `self._entity_tables`
  (the brief's "add … if none exists"; none existed).
- **The `()`-claimant never trips it:** `∅ ⊆ any set` (PIN A ()-leg, LifecycleProbe).

**Why NOT a signature change to `claiming_extension` (the frozen-pin constraint, receipts):** the
original-40 pin **CF8** (`TestClaimExclusivity::test_all_three_sites_route_through_the_shared_helper`)
does `monkeypatch.setattr(extension_module, "claiming_extension", _mutated)` where
`def _mutated(extensions, tier, path)` is 3-arg, then drives `_entity_fragment`, `watcher._purge`,
`reconcile._purge_file` expecting each to propagate a `RuntimeError` matching `"MUTATED"`. If
`_entity_fragment` called `claiming_extension(..., registered)` (4 args), the 3-arg shim raises
`TypeError` (not `RuntimeError`) → CF8 reddens — a frozen grader pin I may not edit. Wrapping
instead: `ready_claiming_extension` calls the module-global `claiming_extension` internally, so
CF8's monkeypatch still binds (verified: CF8 GREEN in the 45/45 run). This is the "shared dispatch
seam, policy in ONE place, `_entity_fragment` thin" property WITHOUT the frozen-pin collision.

**Why purge sites skip readiness (the refinement to flag):** Fable's corruption rationale is the
CREATE path — a claimed-file compose on an unready store auto-creates a SCHEMALESS table (store
§5). Watcher/reconcile PURGE is a `DELETE` — a no-op on an un-`DEFINE`d table, never corruption —
so routing purge through the readiness raise would block legitimate cleanup on an unready store (a
regression, not a safeguard). They keep the exclusivity-only `claiming_extension`. This diverges
from a literal reading of "shared with the purge sites" but matches Fable's own compose-corruption
reasoning and the "guard fires at the moment a file is CLAIMED (per-file, runtime) = the sink".

**Guard message proof (PIN A):** the extension is named `bookdomain`, its table `fake_node`; the
raised message contains both (`extension 'bookdomain' claims (custom, books/a.fake) but its declared
entity table(s) ['fake_node'] are not registered … (finding #375) … SCHEMALESS (store law §5)`).

## MUTATION PROOFS — declared-RED from `--collect-only` first, diffed both ways {#MUTATIONS}

Method: the **always-sound real-tree** path (brief-base §6) — `cp -a` CONTENT backup of the 3 prod
files (+ the fixtures file for leg 3) to `/tmp/harden47a-backup/`, mutate in place, run, restore
from backup, **md5-verify byte-exact restore**. Provenance receipt (the tree under test, PRINTED):
`loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py` (the
REAL editable tree — no scratch ambiguity, #140). No git state mutated. No worktrees.

| leg | mutation | declared-RED (pre-run) | observed | verdict |
|---|---|---|---|---|
| Guard bites | `ready_claiming_extension`: `if missing:` → `if False:` | {PIN A core} | PIN A core RED ("DID NOT RAISE"); ()-leg + pos-ctrl GREEN; 44 passed | **PASS** — the RAISE is load-bearing (routing-without-raise caught, #102/#120 class) |
| PIN B (M1) | `register_entity_tables` body → `self._entity_tables = ()` (ctor untouched) | {PIN B} | PIN B RED (rows survive `delete_by_tier`, :1720); 44 passed | **PASS** — replicates cold-audit M1; the register wiring discriminates |
| Fable P7 discrim. | fixture `FakeIngestExtension.entity_fragment`: `entity_param_prefix(self._name)` → `("fake")` (namespacing break) | {P7} | P7 RED (:650, `fake2` leg); P10a GREEN | **PASS** — P7 STILL catches namespacing THROUGH the guard (adaptation not green-seeking) |
| Fable P10a discrim. | `_compose_file_fragments`: `if False and entity_fragment is not None:` (batch/compose unwired) | {P10a} | P10a RED (:780, no `xt_fake_` params); P7 GREEN | **PASS** — P10a STILL catches the batch-unwired concern THROUGH the guard |

**Both-way diff:** at HEAD-with-my-build the FAILED set is `{}` (45 passed) — so NO original pin
trips the guard (the "confirm no other original-40 pin trips" check, in the removal direction:
removing the guard flips ONLY PIN A core). Each leg's declared-RED == observed-RED, and no
declared-red stayed green. Guard-no-op re-verified on the REFACTORED (lazy-store) code too (PIN A
core RED, ()-leg + pos-ctrl GREEN). All restores md5-byte-exact to backups.

## THE REGRESSION I CAUSED — and the minimal fix {#REGRESSION}

The guard's FIRST form passed `self._store.registered_entity_tables()` as an argument in
`_entity_fragment` — **eagerly evaluated on EVERY compose**, including the common no-extension
case. `FakeSurrealStore` (the `_surreal_fakes.py` test double, used across `test_indexer*`,
`test_graph_wiring`, `test_watcher`) has no such method → **96 failed / 102 passed**
(`AttributeError: 'FakeSurrealStore' object has no attribute 'registered_entity_tables'` at the
compose of every file). Production is unaffected (`self._store` is always a real `SurrealStore`) —
but the eager call coupled every store double to the new method.

**Minimal fix (brief-sanctioned "or pass the store"):** `ready_claiming_extension` now takes the
`store` (typed `Any`, the `ExtensionContext.store` cycle-avoidance idiom) and reads
`store.registered_entity_tables()` LAZILY — only after a claimant is found. A no-extension compose
(`claiming_extension([...], …)` → None) returns before any store access, so the fake store's
missing method is never hit. Post-fix: **198 passed** (the exact set that was 96-failed), full
contract still **45 passed**. Disclosed as the primary deviation; it is a regression my own
in-scope change directly caused (brief-base §2).

## R3 — SERVED DOCS now teach TWELVE seams (makes PIN C green) {#R3}

- `EXTENDING.md`: heading `## The eleven seams` → `## The twelve seams`; intro `property and
  eleven seams` → `property and twelve seams`; **added seam 12** to the numbered list (the ingest
  seam — `claims`/`entity_fragment`/`entity_purge_fragment`/`ingest_backends`/`resolve_edges`,
  phase-1 NODES + phase-2 `ENFORCED` edges into the same per-file `apply`; names the ready-rail +
  the loud claim-dispatch fail-fast). Numbering coherent (1–12).
- `README.md`: `(the eleven seams)` → `(the twelve seams)`.
- Verified: `grep "eleven seams"` in both served docs → EMPTY; `grep "twelve seams"` → present in
  each. PIN C GREEN.

## TEST-PROSE "eleven seams" — every hit individually verdicted (rename-sweep law) {#PROSE}

Anchor-free grep `eleven` over the two named test files (non-symbol textual seam — grep is the
honest tool, said out loud). `FakeExtension` was read: it overrides **exactly 11 of the 12** seams
(all but the ingest seam — verified by AST-listing its method defs). Each hit + one-word verdict:

| file:line | text (pre) | verdict | action taken |
|---|---|---|---|
| `_extension_helpers.py:22` | "FakeExtension — overrides every one of the eleven seams" | **FIX** | → "every one of the eleven **non-ingest** seams (all twelve except the twelfth, ingest, seam — covered by `test_ingest_entity_seam.py`)". The bare count implied a stale framework total of 11; FakeExtension covers 11 of 12, so "twelve" would be FALSE. |
| `_extension_helpers.py:224` | "An `Extension` overriding every one of the eleven seams" | **FIX** | → "eleven **non-ingest** seams" + a note the twelfth is exercised by `FakeIngestExtension`. Same reasoning. |
| `test_extension.py:4` | "AMENDMENT 1, §A1.3 — the eleven seams, refined by …" | **FIX (clarify scope)** | → "the **original** eleven seams … The twelfth, ingest, seam (packet 47a) is pinned separately in `test_ingest_entity_seam.py`." This module genuinely pins only the original 11; clarified so the count no longer reads as a stale total. |
| `test_extension.py:11` | "an ABC base class … with a `name` and the eleven seams, **each with a safe no-op/empty default**" | **FIX** | → "the **twelve** seams". A present-tense claim about the `Extension` ABC — the base now ships inert defaults for the ingest seam too (verified: `claims`→False, `entity_fragment`→None, `ingest_backends`→[]…), so "twelve … each with a safe default" is TRUE. |

These are pure docstrings; no assertion depends on them (the seam-count PIN is P2, which scans
`extension.py`, and PIN C, which scans the served docs — neither reads these). Edits are safe and
were re-run (test_extension.py + _extension_helpers-consuming suites GREEN, §GATES).

## STORE-LAW citation (the corruption the guard prevents) {#STORE-LAW}

`docs/reference/surrealdb-31-capabilities.md` §5 (auto-schema): a `CREATE` against an
un-`DEFINE`d table auto-creates it **SCHEMALESS** — no `ENFORCED`, no indexes — silently. A claimed
file composed on a store whose ingest lifecycle never readied (the `cli`/`scout` half-wiring, #375)
would `CREATE` its entity nodes into exactly such a table. The R2 guard converts that latent silent
corruption into a loud stop BEFORE `store.apply` (the guard runs during compose, before apply, by
construction). Cited, not re-transcribed.

## GATES {#GATES}
- **Contract (real tree, `91fc30e` + my edits, `-n auto`, `:18000`):** **45 passed ×3** (three
  consecutive clean runs; per-test DB isolation makes repeats independent).
- **ruff** (`uv run ruff check .`): **All checks passed!** (twice — before and after the lazy fix).
- **typecheck** (`scripts/typecheck.sh`, CANONICAL): total **191** error: lines (UNCHANGED baseline
  — the #333/pkt-39 auth/posture files, RED-adjudicated; exit 1 is that owned bound). **ZERO** in my
  3 prod files AND ZERO in my 2 touched test files → zero-new-delta. Every erroring file is a
  pre-existing auth/posture test (listed, none mine).
- **Regression (brief-named suites):**
  - `test_extension test_extension_discovery test_graph_wiring test_reconcile test_watcher
    test_indexer{,_bulk_sweep,_chunker_fault_isolation,_contextualized,_snapshot_wiring,_surreal_integration}`:
    **198 passed** (was 96-failed pre-lazy-fix).
  - `test_mcp_server test_server`: **697 passed**.

## DRY LEDGER + reuse {#DRY}

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `ready_claiming_extension` (prod) | `lore_search "readiness check claimant declared tables subset of registered fail fast guard"` | no existing readiness/dispatch helper (only the design-sidecar doc) | **HAND-ROLLED**, but REUSES `claiming_extension` for exclusivity (no clone of that policy) + reuses the `dict.fromkeys` declared-tables union idiom |
| `SurrealStore.registered_entity_tables` (prod) | (read `register_entity_tables` / `_entity_tables` directly; grep confirmed no accessor) | only `self._entity_tables` field + the `register_entity_tables` writer | **HAND-ROLLED** — the read-side twin of the existing writer; no existing accessor |

**Flagged duplication (not fixed — out of writable scope):** the declared-tables union
(`dict.fromkeys(t for backend in ext.ingest_backends(ctx) for t in backend.entity_tables())`) now
appears in **3 sites** — `build_app_context` (`server.py:9161-9169`, interleaved with
`ensure_ready()`), `_white_box_indexer` (test), and my `ready_claiming_extension`. It could be
consolidated into a shared `declared_entity_tables(extension, ctx)` helper in `extension.py`, but
`build_app_context`'s copy interleaves readying + `write_stack_readied.append` (not a pure union),
and `server.py` is outside my writable set. FLAG for a follow-up that touches `server.py`.

## LORE-vs-GREP HONESTY (dogfood protocol)
- Used lore first: `lore_get_symbol` (`claiming_extension`, `_entity_fragment`,
  `register_entity_tables`), `lore_search` (DRY reuse probes), `lore_read` was not needed (read spans
  directly since files were in my writable set).
- **Grep fallbacks, said out loud (no lore weakness — no finding filed):** (1) the rename-sweep
  `eleven seams`/`twelve seams` scan is a non-symbol TEXTUAL seam (prose/docs) — grep is the honest
  tool (CLAUDE.md case 2). (2) `claiming_extension` caller enumeration + `register_entity_tables`
  union site in `server.py`'s 12.5k-line `build_app_context` — read by grep/line-region (lore does
  not profile that function at statement granularity; same fallback the 47a + contract-harden
  builders logged). No friction filed — these are the sanctioned non-symbol/cross-cutting cases.

## HOUSEKEEPING
- Backups under `/tmp/harden47a-backup/` (mutation-proof content backups) — disposable, safe to
  `rm -rf`. No scratch worktrees created (real-tree cp -a method).
- No git state mutated (lead commits). Files changed by ME (7): `EXTENDING.md`, `README.md`,
  `loremaster/loremaster/extension.py`, `loremaster/loremaster/index/indexer.py`,
  `loremaster/loremaster/store/surreal.py`, `loremaster/tests/_extension_helpers.py`,
  `loremaster/tests/test_extension.py`. (`_ingest_entity_fixtures.py` + `test_ingest_entity_seam.py`
  remain the contract author's — I restored them byte-exact after mutation legs; net-zero from me.)
- #375 addressed by this guard (packet-51 still owns the full ingest deferral); #376 CLOSED-IN-EFFECT
  by PIN B (lead/operator may resolve the finding).
