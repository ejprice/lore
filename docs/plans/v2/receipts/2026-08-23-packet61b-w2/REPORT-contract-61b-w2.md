# REPORT-contract-61b-w2 — the visible-Keeps resolver + coverage-as-checked-variable (RED contract)

brief-base v14 read · brief project v7 read

**REVISED 2026-08-23** — sidecar D1/D2 applied, then 3 adversary fixes (A/B/C) applied.
Change log: D1 → `list_keeps_for_member` BORN-WRAPPED; D2 → H-a two-derived-sets + default-GOVERNED
+ reds-until-reviewed growth pin; (A) bare-id pin; (B) born-wrap widened to the WHOLE method
(resolution + SELECT); (C) growth-pin anti-vacuity guard.

## SUMMARY BLOCK
- **state:** done — RED contract written + verified RED at HEAD `1048138`; sidecar D1/D2 + adversary A/B/C applied; satisfiability re-proven against a known-correct build (§Satisfiability).
- **capability check:** brief fully satisfiable (lore tools loaded, test store `ws://127.0.0.1:18000` up, scratch_copy.sh available). No gaps.
- **deviations:**
  1. Fork F EXPLAIN pin EXPLAINs the query the METHOD ACTUALLY ISSUES (captured), not a fixed hand-issued query.
  2. `list_keeps_for_member` BORN-WRAPPED (D1) around the WHOLE method (resolution + SELECT — adversary B): any raw `SurrealStoreError` from EITHER surfaces as `KeepStoreError` at the KeepStore boundary. 4 D1/B wrap pins.
  3. bare-id pin (adversary A): `list_keeps_for_member` returns BARE keep ids.
  4. H-a two derived sets + default-GOVERNED + growth pin (D2) with an anti-vacuity guard (adversary C).
  5. `verify`/`index` classified shared_read to green the growth-pin seed (D2 named 7 corpus tools; the live registry has 9 corpus reads) — flagged, §Fork H-a.
  6. Added `from surrealdb import RecordID` + one entry (`list_keeps_for_member`) to `_KEEPSTORE_READ_METHODS` in the EXISTING `test_keeps_store.py` (disclosed, in-scope).
- **Packages considered:** none — no mechanism specified (contract/tests only; reference impl REUSES `lorerunes.pdp.keep_scope`, `loremaster.store._txn.wrap_store_rejection`, and mirrors `partition_tools_by_posture`).
- **Reuse ledger:** none new in the CONTRACT (tests only). Reference-impl reuse in §Satisfiability (all REUSED, zero new reusable symbols).
- **Graded:** authored/revised at `1048138` · HEAD-at-report `1048138` · SAME.
- **decisions-needed (1 gate decision + 2 ledger notes; the 2 design forks are sidecar-RULED):**
  1. **[GATE] mypy red-at-HEAD:** the no-stub RED contract leaves **16 adjudicated forward-reference mypy errors** at HEAD (symbols the w2 builder lands). Built state fully mypy-clean, no orphaned ignores. Recommend: adjudicate in `scripts/pending_contracts.yaml` (owner=61b-w2 builder, trigger=w2 build lands the symbols) OR proceed to adversary→build (auto-clears on GREEN). §Satisfiability/mypy.
  2. **[LEDGER] Fork H-c deferral** (verb-routing pin → pkt 63, named trigger). §Fork H-c.
  3. **[LEDGER/FLAG] verify+index classification** — classified shared_read (corpus reads, no owner+scope); move to `_REVIEWED_GOVERNED_TOOLS` if you prefer over-gating. §Fork H-a.
- **receipt pointers:** RED §RED · satisfiability §Satisfiability · forks §Fork F / §Fork H-a · adversary fixes §Adversary · H-b already shipped §Fork H-b · scratch path §Handoff.

## Adversary fixes (A/B/C — REPORT-adversary-61b-w2.md)
- **(A) bare-id pin:** `test_returns_BARE_keep_ids_not_record_id_strings` — a `keep:xyz`-returning build (full record id, not the bare id) reds; Fork F ruled bare ids (the resolver adds the `keep:` prefix). +1 Fork F pin.
- **(B) born-wrap widened to the WHOLE method:** the reference impl now wraps resolution AND the SELECT in one `wrap_store_rejection`, so a raw `SurrealStoreError` from the EMAIL-RESOLUTION read (`get_by_email`, unwrapped #406 read-gap, out of scope) also surfaces as `KeepStoreError` at the KeepStore boundary (never a raw escape into authz). New pin `test_born_wrapped_RESOLUTION_rejection_becomes_KeepStoreError` injects at the composed `PrincipalStore._query` → RED against a SELECT-only-wrapped build. +1 Fork F pin.
- **(C) growth-pin anti-vacuity:** `assert live_names` in `test_every_live_tool_is_reviewed_into_a_population` — a broken registry enumeration (0 tools → 0 unreviewed → falsely green) reds instead.

## Files written (writable set: `loremaster/tests/*` + this report)
- `loremaster/tests/test_keeps_store.py` — `TestListKeepsForMember` (Fork F, **12 pins**: results/discrimination/routing/EXPLAIN + bare-id (A) + 4 born-wrapped (D1/B: SELECT-inject + 2 transport params + resolution-inject)) + `_explain_operators`/`_explain_scans_table` walkers; `_KEEPSTORE_READ_METHODS` +`list_keeps_for_member`; `RecordID` import.
- `loremaster/tests/test_visible_keeps_61b.py` — NEW (Fork B/D resolver, **6 pins**).
- `loremaster/tests/test_tool_population_61b.py` — NEW (Fork H-a classification, **10 pins**, D2 two-set + growth pin + (C) anti-vacuity).

## Declared RED node sets (verified RED at HEAD `1048138` — §RED)
- `test_keeps_store.py::TestListKeepsForMember` — **12 nodes**, RED via `AttributeError: 'KeepStore' object has no attribute 'list_keeps_for_member'`.
- `test_visible_keeps_61b.py` — **6 nodes**, RED via collection `ModuleNotFoundError: loremaster.visible_keeps`.
- `test_tool_population_61b.py` — **10 nodes**, RED via collection `ImportError: cannot import name '_REVIEWED_GOVERNED_TOOLS' from 'loremaster.server'`.
- **Total: 28 RED nodes** (GREEN set = the same 28, proven in §Satisfiability).

---

## Fork F — `KeepStore.list_keeps_for_member` (12 pins) — D1 born-wrapped (whole-method) + bare ids
The symmetric twin of `list_keeps_for_keeper`: reads `member_of` AS A PLAIN TABLE
(`SELECT out FROM member_of WHERE in = $member`, RecordID-bound) — never an arrow traversal
(store-ref §4). Returns the BARE keep ids whose household the member is in.
- **Results/discrimination (5):** ≥2 keeps (small-N); member-of-none → `[]`; excludes a keep the member isn't in (+ keeper-auto-add positive control); no cross-member bleed; unknown email → `KeepStoreError` (never `[]`).
- **bare ids (1, adversary A):** returns BARE keep ids (no `keep:` prefix) — a `keep:xyz`-returning build reds (the METHOD's own contract; the resolver adds the prefix via `keep_scope`).
- **Routing/plan (2):** captures the method's actual statement (ONE `_query` seam, LEADING column `in`, no arrow); **EXPLAIN pin** EXPLAINs the CAPTURED query → IndexScan on the existing `UNIQUE(in, out)` leading column (no new index), TRAILING `WHERE out=$keep` TableScan positive control (store-ref §2 / #413).
- **D1/B born-wrapped (4):** raw `SurrealStoreError` from the SELECT → `KeepStoreError`; raw `SurrealStoreError` from the **RESOLUTION read** (composed `PrincipalStore._query`) → `KeepStoreError` (whole-method wrap — adversary B); transport faults (`SurrealConnectionError`/`TxnContentionExhaustedError`) PASS THROUGH untouched (2 params, the catch-all discriminator).

**D1 RULING (sidecar) + adversary B (whole-method):** `list_keeps_for_member` is BORN-WRAPPED
because it FEEDS the PDP (`resolve_visible_keeps` → `Subject.visible_keep_ids`), so NO raw
`SurrealStoreError` may escape it into the AUTHORIZATION path — from resolution OR the SELECT. The
reference impl wraps the WHOLE body (the `set_keeper`/`remove_household_member` whole-verb idiom).
The unwrapped mirror (`list_keeps_for_keeper` + `get_keep`/`list_household`/`_read_membership`) and
`PrincipalStore.get_by_email`'s own unwrapped read are the pre-existing **#406-class read-gap the
lead is ledgering — NOT the standard to mirror, out of w2 scope**; this fix stops
`list_keeps_for_member` LEAKING a raw error into authz, catching it at the KeepStore boundary.
(The born-wrapped read stays a READ — no mutating statement literal — so it is not swept into the
write-wrap coverage set and remains in `_KEEPSTORE_READ_METHODS`; its wrap is pinned directly.)

## Fork B/D — `resolve_visible_keeps` (6 pins) — unchanged
Thin `loremaster` shell (`loremaster/loremaster/visible_keeps.py`): maps Fork-F keep ids →
`keep:<id>` scopes → the `Subject.visible_keep_ids` frozenset.
- **Mapping-home RESOLVED:** REUSES the shipped `lorerunes.pdp.keep_scope` (one spelling; no new helper; no `registration_sites.py` owed).
- pins: frozenset of `keep:<id>` scopes (≥2 keeps); every scope valid + non-double-prefixed; member-of-none → `frozenset()`; unknown email → `KeepStoreError`; **prove-by-mutation** (monkeypatch `lorerunes.pdp.KEEP_SCOPE_PREFIX` → a hand-rolled `f"keep:{k}"` clone reds); **end-to-end** (feeds a `Subject`; PDP READ-authorizes in-keep, denies out-of-keep, server positive control).
- **Home flag:** NEW module `loremaster.visible_keeps`; only the import path couples to placement — low-stakes.

## Fork H-a — tool-population classification (10 pins) — D2 two derived sets + default-GOVERNED
`partition_tools_by_population(tools) -> (shared_read, governed)` in `loremaster.server`, plus TWO
reviewed sets checked OVER the live registry:
- **`_SHARED_READ_CORPUS_TOOLS`** (open allowlist, 9 corpus reads: search/read/get_symbol/impact/map/dead_code/diff + verify/index).
- **`_REVIEWED_GOVERNED_TOOLS`** (6 coordination: comms/recall/remember/tasks/claim_task/findings) — the REVIEW-completeness marker for the growth pin; **NOT** a runtime blocklist (runtime defaults governed, so never fail-open).
- **RUNTIME DEFAULT = GOVERNED (fail-closed).** D2 security asymmetry: governed-mistaken-as-shared_read = cross-principal LEAK (catastrophic); shared_read-mistaken-as-governed = broken functionality (loud/safe).
- **pins (10):** runtime totality/no-NEITHER; default-governed (synthetic → governed, never shared_read); **GROWTH PIN** (every LIVE tool in `SHARED_READ ∪ REVIEWED_GOVERNED`; a tool in neither reds; GREEN at the 61 seed) + **(C) anti-vacuity** (`assert live_names` — an empty registry reds, not passes); **growth mutation-proof** (a synthetic new tool is unreviewed AND runtime defaults it governed); §1 semantics discriminating representatives; two reviewed sets disjoint; no-ghost in EITHER set; allowlist never exempts the whole surface; one-home structural (all 3 symbols in `loremaster.server`).

**D2 RULING (sidecar):** reconciles my original H-a contradiction (allowlist-the-safe vs
"synthetic-unclassified reds") to "reds-until-REVIEWED, default-GOVERNED" — the growth-detecting
red WITHOUT a fail-open governed blocklist (runtime defaults governed; `_REVIEWED_GOVERNED_TOOLS`
is a review marker only).

**⚠ Classification note (flagged):** D2 named 7 corpus tools; the live registry carries 9 corpus
reads — `lore_verify` (claim-check) and `lore_index` (freshness/health) also carry no owner+scope.
I classified BOTH shared_read so the growth-pin seed is GREEN (15 live tools reviewed: 9 shared_read
+ 6 governed). Move them to `_REVIEWED_GOVERNED_TOOLS` if you prefer over-gating; either keeps the
seed green, and the representative-fixture pins don't depend on the choice.

**FORWARD-NOTE (ledger, D2):** 63/64 → per-tool POPULATION ANNOTATION (the pure reach form,
mirroring `ToolAnnotations.readOnlyHint`); the two-set + growth-pin is the right-sized 61 SEED.

## Fork H-b — IR-node interpreter exhaustiveness: ALREADY SHIPPED (no new pin)
Already pinned in `lorerunes/tests/test_pdp_core.py` (`test_every_node_has_a_working_to_surql`,
`test_every_node_has_a_working_matches`, the `__subclasses__` derivation + `test_no_concrete_subclasses`
anti-vacuity guard; structural via ABC abstractmethods). 61b-w2 adds nothing here.

## Fork H-c — DEFERRAL to ledger (NOT a pin here)
Per-governed-VERB routing pin DEFERRED to packet 63, named trigger: *"the first governed-tool
retrofit (pkt 63) MUST add the verb-routing coverage pin, DERIVED from the
`partition_tools_by_population` governed set seeded at 61 — a governed verb that bypasses the PDP
reds it."* **Lead: please ledger** (owner=pkt 63 contract, trigger=first governed-tool PDP retrofit).

## RED — verification at HEAD `1048138`
- New files collect-ERROR (RED): `ModuleNotFoundError: loremaster.visible_keeps`;
  `ImportError: cannot import name '_REVIEWED_GOVERNED_TOOLS' from 'loremaster.server'`.
- Fork F class: **12 failed** — all `AttributeError: 'KeepStore' object has no attribute 'list_keeps_for_member'`. `test_keeps_store.py` collects fully — no existing collection broken.
- Total **28 RED nodes** = the 28 GREEN in §Satisfiability.

## Satisfiability — a known-correct build greens all 28 (C-DEF law)
Reference impl in a provenance-asserting scratch (`./scripts/scratch_copy.sh /var/tmp/scratch-61b-w2`).
**Provenance receipt:** `loremaster.__file__ = /var/tmp/scratch-61b-w2/loremaster/loremaster/__init__.py`
(INSIDE the scratch — #140 closed). Reference impl (3 pieces, all REUSE, zero new reusable symbols):
- `KeepStore.list_keeps_for_member` — mirrors `list_keeps_for_keeper`; the WHOLE body
  (resolution + `SELECT out FROM member_of WHERE in = $member`, RecordID-bound) wrapped via
  `wrap_store_rejection(KeepStoreError, …)` (D1/B); returns `[_record_id_part(str(row["out"]))]` (bare).
- `loremaster/loremaster/visible_keeps.py::resolve_visible_keeps` — REUSES `lorerunes.pdp.keep_scope`.
- `loremaster.server.{_SHARED_READ_CORPUS_TOOLS, _REVIEWED_GOVERNED_TOOLS, partition_tools_by_population}` — mirrors `partition_tools_by_posture` (default-governed).
Results (final files):
- **pytest: 28 passed, 0 failed** (the 28 declared RED nodes) — incl. growth-pin seed GREEN, born-wrapped SELECT+resolution+transport pins, bare-id pin, anti-vacuity guard.
- **ruff: clean** on all 6 touched files.
- **mypy (`scripts/typecheck.sh`, canonical): CLEAN — exit 0, all legs OK, no orphaned ignores.**

### mypy at HEAD (the RED-contract gate decision)
`scripts/typecheck.sh` on the REAL tree at HEAD reports **16 forward-reference errors**, ALL in my
3 test files, all "symbol the builder lands": 1× `import-untyped` (`loremaster.visible_keeps`), 12×
`attr-defined` (`KeepStore.list_keeps_for_member` call sites), 3× `attr-defined` (the 3 server
symbols). NO `# type: ignore` — a forward-ref suppression orphans on GREEN (the C-DEF "still clean
after the build" leg). Clean forward-refs mypy-clear on GREEN. **ADJUDICATED red (gate law) —
the lead's call:** register `pending_contracts.yaml` (owner=61b-w2 builder, trigger=w2 build lands
the symbols), or proceed to adversary→build (auto-clears, proven above).

## Handoff
- **Scratch tree** `/var/tmp/scratch-61b-w2` (disposable `scratch_copy.sh` copy, NOT a git worktree)
  carries the revised reference impl. Safe to `rm -rf` (I was permission-blocked from removing it).
  Built-state mypy log: `/var/tmp/scratch-61b-w2-mypy5.log`.
- Next: the lead re-runs the **focused adversary**. The A/B/C gaps are closed: bare-id pinned;
  whole-method born-wrap (resolution + SELECT) pinned; growth-pin anti-vacuity guarded.
