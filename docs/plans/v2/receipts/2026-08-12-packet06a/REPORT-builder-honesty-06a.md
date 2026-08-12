# REPORT — builder-honesty-06a (packet 06a W1+W3 build)

brief-base v12 read
brief project v7 read

## SUMMARY BLOCK
- **State: done-with-deviations.** All **19 contract pins GREEN** for the right reason; every affected suite GREEN **except 2 pre-existing tests in the FROZEN `test_brief_ledger.py`** I am forbidden to edit (see §BLOCKING). Production build: schema `declared_cadence`, `register`/`heartbeat`… (register only — see F3) cadence param, fleet `overdue` verdict, ⚠STALE retired BOTH callers, #257 non-vacuity floor.
- **Deviations (prominent — the retire/floor blast radius far exceeded the brief's 2 named old-world files):**
  1. **Edited 4 files OUTSIDE the brief's named writable set** under the base §2 regression-exception (a regression my in-scope change directly causes, fixed minimally + disclosed): `_comms_fakes.py`, `test_comms_tool.py`, `test_comms_wiring.py`, `test_link5_render_containment.py`. Full inventory + rationale in §Scope-expansion.
  2. **2 FROZEN-file collisions I could NOT fix** (brief prohibits touching `test_brief_ledger.py`) → §BLOCKING, with exact recommended edits.
  3. **F3 (heartbeat cadence): BUILT** — the brief directs "register AND heartbeat (F3 symmetry)", so `heartbeat` now accepts `cadence` too (mutable-on-provided via `touch`, exactly like `note`). ⚠ **UNPINNED by the frozen contract** (it pins `register` only) — verified instead by a live round-trip smoke (§Heartbeat cadence). Recommend the lead route a heartbeat-cadence pin.
- **Packages considered:** `surrealdb.Duration.parse` for `_parse_cadence_seconds` — READ the vendor doc (lore `surrealdb-docs:reference/python/api/values/duration.mdx`): it parses `"1h30m"`/`"500ms"` but NOT the design's `≤`-prefixed cadence form (`"≤20m"`), so it does NOT do the job → `bespoke` (~4-line regex, minimal surface, closed charset). Verdict matches the contract author's independent read.
- **Reuse ledger:** 1 new reusable symbol (`_parse_cadence_seconds`), dispositioned HAND-ROLLED (see §DRY ledger). All other changes reuse existing seams (`render_attributed`, `render_line`, `_render_age`, `_heartbeat_is_stale`, the `model`/`task_id` mutable-on-provided register precedent, `BriefLedgerError` base).
- **Graded:** n/a — this is a build, not an audit/verdict.
- **Decisions needed:** §BLOCKING (2 frozen-file edits — the lead's, since the lead commits them); F3 (heartbeat cadence — optional).
- **Receipt pointers:** contract pins GREEN → §Gate receipts; 5/5 mutation proofs → §Mutation proofs; ruff clean + mypy zero-new → §Gate receipts; blast-radius suites GREEN → §Gate receipts; friction filed → lore finding #362.

## Capability check
All tools present and used: lore (registered `builder-honesty-06a`, session `pkt06-20260811`), store reference `docs/reference/surrealdb-31-capabilities.md` §1.1/§1.4 (cited below, never re-transcribed), spike-surreal `ws://127.0.0.1:18000` (`:18500` NEVER touched), ruff/mypy(`scripts/typecheck.sh`)/pytest. No missing capability blocked the mission.

## What I built (file : symbol — line-free per brief-base §1)

**W1a — schema field** (`store/surreal_schema.py::_AGENT_FIELD_SPECS`): added `("declared_cadence", "option<string>", "")`. `option<>`, NO ASSERT, emitted via `_define_field` ⇒ `DEFINE FIELD OVERWRITE`. Store reference §1.4 (a NEW field on the production-POPULATED `agent` table must be `option<>` — a required/asserted field write-poisons every legacy row's next UPDATE, and a DEFAULT does not rescue it) + §1.1 (FIELD → `OVERWRITE`; `IF NOT EXISTS` is the #107 silent no-op). Mirrors the `status_set_at` (#304) precedent exactly.

**W1b — cadence persistence** (`agents.py`): `Agent.declared_cadence: str | None = None`; `_COL_DECLARED_CADENCE` / `_REG_DECLARED_CADENCE_PARAM` constants; `AgentRegistry.register(..., cadence=None)` writes `_COL_DECLARED_CADENCE` on CREATE and is **mutable-on-provided on re-register** (exactly the `model`/`task_id` precedent — `new_declared_cadence = cadence if cadence is not None else existing.declared_cadence`); `_row_to_agent` reads `row.get(_COL_DECLARED_CADENCE)` (NONE-tolerant — a legacy row omits the column under `SELECT *`, store reference §2). All agent SELECTs are `SELECT *`, so the field round-trips everywhere.

**W1c — overdue verdict** (`server.py`): module-level `_parse_cadence_seconds` (tolerant `≤`-prefix parser → seconds, `None` on unparseable). `_render_comms_fleet_row` replaces the ⚠STALE branch with: `overdue (declared {cadence}, silent {age})` rendered ONLY when `row.declared_cadence` is set AND `_parse_cadence_seconds` returns a threshold AND `heartbeat_age_s` exceeds it — the `{cadence}` echo is `render_attributed(row.declared_cadence)` (THIS row's own typed state, #104) and `{age}` is `_render_age(heartbeat_age_s)` (its own silence). No declaration / within-cadence ⇒ `hb {age}` only, no verdict. `stale_after_s` stays in the signature (kept for the pre-06a direct-render callers across non-writable test files) but no longer gates this surface.

**W1c param** (`server.py`): `cadence: str | None` added to the `comms` dispatch method, the `@mcp.tool` `comms` wrapper (**description STATES THE PAYOFF** — ≥80 chars, names `overdue`; the R1 lesson / §B.7 shape), threaded through to `_comms_register` → `agent_registry.register(cadence=...)`, and added to `_COMMS_ACTIONS["register"].params` (so it is foreign-param-guarded like every other register param).

**W1b/F3 — heartbeat cadence (brief directive "register AND heartbeat")** (`agents.py` + `server.py`): `AgentRegistry.touch(..., cadence=None)` persists `declared_cadence` **mutable-on-provided** (`new_declared_cadence = cadence if cadence is not None else agent.declared_cadence` — the exact `note` idiom, so a bare heartbeat never nulls a prior declaration); `_TOUCH_DECLARED_CADENCE_PARAM` added to the touch UPDATE. Server side: `"cadence"` added to `_COMMS_ACTIONS["heartbeat"].params`; the dispatch's uniform touch passes `touch_cadence = cadence if action == heartbeat else None` (every other registration-requiring action leaves the prior declaration intact); the tool description now reads "For 'register'/'heartbeat'". `FakeAgentRegistry.touch` mirrors it. **UNPINNED** (the frozen contract pins register only) — verified by live smoke (§Heartbeat cadence).

**W1d — ⚠STALE retired, BOTH callers** (`server.py`, §D-4): `_render_comms_fleet_row` (glyph gone, replaced by overdue) AND `_render_holder_liveness_notice` (glyph gone → `"last seen {age} ago"`, age remains, `_heartbeat_is_stale` still gates the age-vs-status display). `_heartbeat_is_stale`'s fate: **SURVIVES**, now the SOLE caller is the holder-liveness age-gating (the fleet row exited the club — see the reworked shared-predicate tests).

**W3 — #257 non-vacuity floor** (`briefs.py`): `_MIN_BRIEF_BODY_TOKENS = 3`; `BriefBodyTooThinError(BriefLedgerError)`; in `publish`, `if len(body.split()) < _MIN_BRIEF_BODY_TOKENS: raise BriefBodyTooThinError(...)` as the FIRST statement (before any store I/O — nothing minted/queried for a placeholder), with a teaching message (names body/content/placeholder/brief, ≥20 chars). NO `is_blank` import (F-DRY ruling — blank is double-guarded by the token check + the store `_NON_EMPTY_STRING_ASSERT`, so a shared blankness predicate is unverifiable-by-construction here).

## Scope-expansion (prominent deviation — the retire/floor blast radius)
The contract's §Old-world inventory named only `test_comms_register_notice.py` + `test_comms_promise_registry.py`. A **bare anchor-free grep of the whole test tree** (rename/retire law) found the real blast radius was much larger — 17 red across 5 files, plus a fake. All are DIRECT, mechanical consequences of my ruled in-scope changes (#257 floor, cadence param, ⚠STALE retire). Per base §2, a regression my in-scope change directly causes may be fixed minimally + disclosed. Files edited and why:

| file | in brief's writable set? | what / why |
|---|---|---|
| `test_comms_register_notice.py` | **yes** | STALE-holder pin flipped (glyph gone, age remains); `TestStaleThresholdIsSharedWithFleet` reworked → `TestHolderNoticeReadsTheConfigThreshold` (fleet exited the `_heartbeat_is_stale` club; premise dissolved). |
| `test_comms_promise_registry.py` | **yes** | `_PROMISE_FREE`: removed the dead ⚠STALE fleet-row template, added the `overdue` variant. |
| `_comms_fakes.py` | no (test fake) | `FakeAgentRegistry.register` + `.touch` gained `cadence` (a signature MIRROR of the real registry — without it every fake-register/heartbeat test TypeErrors). |
| `test_comms_tool.py` | no | register-params AND heartbeat-params tables += `cadence`; STALE fleet-row test repurposed to assert glyph-gone/age-remains. |
| `test_comms_wiring.py` | no | 4 short-body fixtures widened to ≥3 tokens (clear the #257 floor); the blank-body store-ASSERT test re-pointed to the brief.NAME charset ASSERT (blank is now app-rejected before the store); `TestConfigKnobStaleHeartbeatIsConsumed` reworked to the surviving consumer (holder-liveness age-gating). |
| `test_link5_render_containment.py` | no | classified the new caller door: `cadence` → `_PARAM_CLASS` (attribution), `declared_cadence` → `_manifest()` Agent DOOR, and added an over-drive OVERDUE probe shape so the new branch is a CHECKED variable (branch reach). These are containment-SAFETY pins — leaving them red would ship my new free-text door unguarded. |

Friction filed: lore **#362** (the hand-list-vs-grep gap AND the adversary's satisfiability scope missing the 2 frozen-file collisions).

## BLOCKING — 2 collisions in the FROZEN `test_brief_ledger.py` (the brief forbids me to edit it)
Both PASS at committed HEAD `cca4b49` and fail only in the working tree (one from my floor, one from the contract author's own new fixture). **The lead commits `test_brief_ledger.py`, so these are the lead's edits (or a scope grant to me).** Exact recommended edits:

1. **`TestPublishSelfAckIsWrittenInTheSameTransaction::test_a_rejected_create_rolls_back_the_edge_too_and_burns_no_version`** — caused by MY #257 floor. It `publish("")` expecting a store `SurrealStoreError` (brief.body non-empty ASSERT) to exercise the POST-MINT rollback/edge-rollback/version-release path. My floor now rejects blank APP-SIDE (`BriefBodyTooThinError`) *before* the mint, so that store ASSERT is unreachable via `publish()`.
   - **Recommended (faithful):** change the rejected-write trigger from a blank body to a store-rejected NAME that clears the floor, e.g. `_publish_as(ledger, "Bad Name!", BODY_V2, created_by="scout-c", agent_id=AGENT_SCOUT_C_ID)` (raises `SurrealStoreError` at the brief.NAME charset ASSERT — verified live in my `test_comms_wiring` rework). ⚠ Verify whether it fails at `_mint_version` (pre-mint) or the brief CREATE (post-mint) so the docstring's "burns no version via release" stays accurate; if it fails pre-mint, the assertions still all hold but the post-mint rollback isn't exercised.
   - **Minimal fallback:** keep the blank body, change `pytest.raises(SurrealStoreError)` → `pytest.raises((SurrealStoreError, BriefBodyTooThinError))`. All other assertions (no edge, no row, gapless next v2) STILL hold under the app floor (traced: the floor short-circuits before the mint, so nothing is written and the counter is untouched) — but this weakens the test to the app path.

2. **`TestEveryRealLedgerSiteSeedsItsAgentRows::test_every_function_that_builds_a_real_BriefLedger_also_seeds_agent_rows`** — NOT my code. The contract author's own new `real_brief_ledger` fixture builds a real `BriefLedger` + `make_env` without calling `_seed_agent_rows`, so the static AST sweep flags it (`unseeded == ['real_brief_ledger']`).
   - **Recommended:** add `await _seed_agent_rows(env, [])` to the `real_brief_ledger` fixture after `make_env` (its tests `publish` without `agent_id`, so no `briefed` edge is written — an empty seed satisfies the static "force new sites to seed" sweep). Or seed the standard id set.

## DRY ledger (base §6) — new reusable symbols
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `server._parse_cadence_seconds` | `lore_search "parse duration string like 20m or 2h into seconds; cadence or interval parser"` (task kf9u7dkeb) | only hit: SurrealDB SDK `Duration.parse` (parses `1h30m`/`500ms`, no `≤`-prefix); no in-repo duration parser | **HAND-ROLLED** — `Duration.parse` rejects the design's `≤20m` cadence form (READ the vendor doc), so it does not do the job; ~4-line closed-charset regex, minimal surface. `_render_age` is the inverse direction (seconds→string), not reusable. |

No other new reusable symbols: the overdue render reuses `render_attributed`/`render_line`/`render_join`/`_render_age`; the floor reuses `BriefLedgerError`; the register wiring reuses the `model`/`task_id` mutable-on-provided precedent.

## Store DDL verification (the #107 order)
1. **Store reference §1.4** (cited): NEW field on the POPULATED `agent` table MUST be `option<>` no-ASSERT. §1.1: FIELD → `OVERWRITE`.
2. **Live precedent (stronger than a fresh probe):** `status_set_at` (#304) ships this EXACT idiom (`("status_set_at","option<datetime>","")`) in production today; `declared_cadence` clones it. The live register round-trip pins (persist verbatim; a no-cadence register → None) passed against spike-surreal — the running proof.

## Mutation proofs (5/5 — each reddened its pin, then restored byte-identical)
In-place mutate-with-`cp`-backup on the uncommitted tree (base §6 law), md5-verified restore each time (baselines: schema `71334fdf…`, server `a042879d…`, briefs `fa1322b9…`):
| # | mutation (the adversary's wrong build) | target pin | result |
|---|---|---|---|
| 1 | schema `option<string>` → `string` (required field) | `test_declared_cadence_is_option_string_with_no_assert` | **1 failed** ✓ → restored |
| 2 | overdue `heartbeat_age_s > overdue_after_s` → `> 600` (hardcoded threshold) | `test_overdue_threshold_tracks_the_declared_value_not_a_constant` | **1 failed** ✓ → restored |
| 3 | echo `render_attributed(row.declared_cadence)` → `render_attributed("≤2m")` (hardcoded echo) | `test_overdue_verdict_echoes_THIS_agents_own_cadence_and_silence` | **1 failed** ✓ → restored |
| 4 | restore ⚠STALE in the HOLDER note ONLY (one-caller retire) | `TestHolderLivenessNoticeRetiresTheStaleGlyph` **and** `TestNoStaleGlyphLiteralInCommsRenders` (F-GLYPH) | **1 failed each** ✓ → restored |
| 5 | floor `len(body.split()) < _MIN_BRIEF_BODY_TOKENS` → `len(body) < 2` (char-based) | `test_a_single_real_word_is_rejected_token_not_char` | **1 failed** ✓ → restored |

## Heartbeat cadence (F3) — live smoke (the unpinned half's verification instrument)
No contract pin exists for heartbeat cadence (the frozen contract pins `register` only), so I verified it live against spike-surreal `:18000` through the REAL `AgentRegistry`. Throwaway smoke (pasted verbatim so the claim is re-runnable — base §1):
```python
await reg.register("worker", session="hbsmoke", role="builder")
assert (await reg.get_agent("worker", session="hbsmoke")).declared_cadence is None        # register → None
await reg.touch("worker", session="hbsmoke", cadence="≤5m")
assert (await reg.get_agent("worker", session="hbsmoke")).declared_cadence == "≤5m"         # heartbeat persists verbatim
await reg.touch("worker", session="hbsmoke", note="just a heartbeat")
assert (await reg.get_agent("worker", session="hbsmoke")).declared_cadence == "≤5m"         # bare heartbeat PRESERVES (not nulled)
await reg.touch("worker", session="hbsmoke", cadence="≤30m")
assert (await reg.get_agent("worker", session="hbsmoke")).declared_cadence == "≤30m"        # re-declare overwrites
```
Result: `HEARTBEAT-CADENCE SMOKE OK: None -> ≤5m (heartbeat) -> ≤5m (bare hb preserves) -> ≤30m (re-declare)`.

## Gate receipts
- **19 contract pins GREEN (right reason):** `test_comms_schema.py::…::test_declared_cadence…` (1), `test_mcp_server.py` TestRegisterPersistsDeclaredCadence(2)/TestFleetRendersOverdueVerdict(4)/TestFleetRetiresTheStaleGlyph(1)/TestHolderLivenessNoticeRetiresTheStaleGlyph(1)/TestCadenceParamDescriptionStatesThePayoff(1)/TestNoStaleGlyphLiteralInCommsRenders(1) → `11 passed`; `test_brief_ledger.py::TestBriefPublishNonVacuityFloor` → `8 passed`.
- **Full blast-radius sweep GREEN** (`-n auto`, 14 files incl. all 3 contract files, both writable old-world, the 4 regression-exception files, footer/status_age/fleet_grouping, surreal_schema/store/schema_rebuild): **2886 passed, 2 failed** — the 2 failures are exactly the FROZEN-file collisions in §BLOCKING (nothing else).
- **`test_comms_tool.py` + `test_comms_wiring.py`:** `953 passed`. **`test_link5_render_containment.py`:** `160 passed`. **`test_comms_register_notice.py` + `test_comms_promise_registry.py`:** `135 passed`.
- **Post-heartbeat re-confirmation:** after adding heartbeat cadence (which touches the shared `touch`/dispatch/register paths), re-ran all 19 contract pins + both `TestCommsActionsTable` param tables → `31 passed`; the touch/heartbeat-heavy suites (tool/wiring/status_age/mcp_server/register_notice/footer) → `1885 passed` (the one initial failure, `test_heartbeat_params` pinning the old param set, is fixed). ⚠ The §Mutation-proof md5 baselines were captured BEFORE the heartbeat additions and target the W1c/d/W3 pins in server/briefs/schema — unaffected by the heartbeat `touch` change (a separate code path).
- **`uv run ruff check .`:** `All checks passed!`
- **`scripts/typecheck.sh`:** ZERO errors in any changed file (agents/server/briefs/surreal_schema + all touched test files). The 102 `loremaster` errors are entirely the pre-existing pkt39/45/48/49 auth-WIP baseline (`test_auth*`, `test_allowlist_roster`, `lorerunes/tests/test_posture`, …) — ZERO-NEW confirmed.

## Deploy note
This work deploys (the lead deploys after build + cold audit). The schema change adds ONE `option<>` field via `OVERWRITE` — safe on the populated production `agent` table (no legacy-row poison; §1.4). No index/analyzer/relation-table DDL changed.

There are 2 failing tests in the frozen `test_brief_ledger.py` (both in §BLOCKING) blocking a fully-green commit — the lead's to resolve, since the lead owns that file. All other affected suites are green.
