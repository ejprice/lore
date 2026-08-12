# REPORT — contract-honesty-06a (packet 06a, W1 + W3 RED contract)

brief-base v12 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done (through TWO fix waves 2026-08-11) — **21 pins** (adversary fix wave added F-ECHO/F-GLYPH; post-build fix wave added 2 heartbeat pins + fixed 2 collisions). At HEAD `cca4b49` it was 15 RED (right reason) + 4 GREEN; against the **built** working tree it is fully GREEN (24 + 4 passed). FULL-surface satisfiability **139 passed** (reference build). All 3 post-build items mutation-proven. **Read §FIX WAVE then §CONTRACT FIX WAVE first — they supersede the F-ECHO-adjacent claims, the #257 token-count, the DRY/is_blank line, and the F3 status below.**
- **Deviations:**
  - Fleet overdue/STALE-retirement pins are pinned through the **LIVE `_comms_fleet` handler**, not the pure `_render_comms_fleet_row`, so they don't couple to that method's `stale_after_s` param (which the retirement removes). Rationale in body §Seam choice.
  - W3 `#257` floor pins are **REAL-ledger only** (the fake `FakeBriefLedger` reimplements `publish`; grading production is the point). Fixture-fidelity flag in §Forks.
  - The R1 "cadence description states the payoff" requirement IS pinned (`test_cadence_param_...states_the_overdue_payoff`), in `test_mcp_server.py` per the brief's "register pins" routing.
- **Packages considered:** none new for the CONTRACT. Reference build only: `lorerunes.is_blank` (READ its source — `not value or not value.strip()`) was evaluated for the #257 blank leg but **DROPPED in the fix wave** (F-DRY: moot — blank is double-guarded, so the reuse is unverifiable and redundant; verdict `keep_with_trigger` → the trigger fired, no predicate used). No duration-string parser exists in-repo; the surrealdb SDK `Duration.parse` (READ vendor doc) does NOT accept the `≤`-prefixed cadence form → the reference build hand-rolls a ~6-line parser (`bespoke`, reference-only; the real builder owns the production choice).
- **Reuse ledger:** 3 new test symbols, all dispositioned (see §DRY ledger) — `_field_statement` REUSED; `_FleetCtx` + `_fleet_row` HAND-ROLLED (trivial harness, cross-file originals lack cadence/heartbeat-backdate).
- **Graded:** n/a — this is a contract, not an audit. Contract is RED at HEAD `cca4b49`; satisfiability reference build graded GREEN (16/16) at scratch provenance `/home/ejprice/pkt06a-scratch/loremaster/loremaster/__init__.py`.
- **Decisions needed (forks — most RESOLVED in the fix wave):**
  1. ~~**`single-token` reading** (F1)~~ **RESOLVED (operator ruled 3): `_MIN_BRIEF_BODY_TOKENS = 3`.** Reject <3 tokens; the two-token pin flipped to REJECT, a three-word ACCEPT added.
  2. **Old-world STALE tests** (F2): builder-owned, OUTSIDE my writable set — 4 assertions in `test_comms_register_notice.py`, 1 registry entry in `test_comms_promise_registry.py`, **plus** (fix wave) the promise-registry MUST also *classify the new `overdue` literal* (§FIX WAVE F-REGISTRY). Full list in §Old-world inventory + §FIX WAVE.
  3. ~~**`heartbeat` cadence** (F3)~~ **RESOLVED (post-build fix wave): the builder built it; now PINNED** (`TestHeartbeatPersistsDeclaredCadence`, mutation-proven both directions). See §CONTRACT FIX WAVE.
  4. **Fake-ledger #257 fidelity** (F4): still open — builder decision.
  5. ~~**`is_blank` reuse** (F-DRY)~~ **RESOLVED (fix wave): DROPPED** — the mandate is moot/unverifiable for this floor (double-guarded blank). No blankness predicate used or hand-rolled.
- **Receipt pointers:**
  - RED tails: body §RED receipts.
  - ∀-vs-guarded table: body §Quantifier table.
  - Satisfiability: body §Satisfiability receipt (provenance + 16/16 + ruff-cleanup leg + mypy resolves).
  - Mutation-proof plan: body §Mutation-proof plan.
  - Store DDL verification (#107 order): body §Store DDL verification.
  - Reference-build diff (durable): body §Reference build.
  - Writable files: `loremaster/tests/test_comms_schema.py`, `loremaster/tests/test_mcp_server.py`, `loremaster/tests/test_brief_ledger.py`.

## Capability check
All tools present and used: lore (registered `contract-honesty-06a`, session `pkt06-20260811`), the store reference, the spike-surreal test store (`ws://127.0.0.1:18000` — `:18500` NEVER touched), `scripts/scratch_copy.sh`, ruff/mypy/pytest. No missing capability blocked the mission.

## What I built — three concerns, separate pin groups (committable independently)

Work order: `docs/plans/v2/design/2026-08-11-packet06-drill-and-obedience.md` §B.7 / §D-1 / §D-4 / §D-2, and `docs/plans/v2/06-comms-protocol-drill.md` §KICKOFF operator rulings 2 & 3 (2026-08-11).

**W1a — schema field** (`test_comms_schema.py::TestAgentDdlOffline::test_declared_cadence_is_option_string_with_no_assert`): `declared_cadence` on `agent` is `option<string>` via `DEFINE FIELD OVERWRITE`, **no ASSERT** — mirrors the `status_set_at` (#304) precedent (`("status_set_at","option<datetime>","")` at `_AGENT_FIELD_SPECS`) EXACTLY. Offline pin via the house `_field_statement` (already fails unless `OVERWRITE`, carrying the #107 guard).

**W1b — register cadence round-trip** (`test_mcp_server.py::TestRegisterPersistsDeclaredCadence`, 2 pins): `register(cadence="≤2m")` persists `declared_cadence` **verbatim**; register without cadence → `None`. Live `AgentRegistry` on spike-surreal.

**W1c — overdue verdict** (`test_mcp_server.py::TestFleetRendersOverdueVerdict`, 3 pins): `overdue (declared {cadence}, silent {age})` renders ONLY when a cadence is declared AND `heartbeat_age` exceeds it (derived from typed state, #104). Includes the parameter-value **monoculture** guard (same age, `≤2m` fires / `≤20m` silent — the threshold must track the declared VALUE).

**W1d — STALE glyph retired, BOTH callers** (§D-4): `test_mcp_server.py::TestFleetRetiresTheStaleGlyph` (fleet row, live, no-declaration corpse at 1300s) + `TestHolderLivenessNoticeRetiresTheStaleGlyph` (pure `_render_holder_liveness_notice`). Glyph GONE, age REMAINS, at >600s.

**W1e — cadence description payoff (R1 lesson)** (`test_mcp_server.py::TestCadenceParamDescriptionStatesThePayoff`): the served `cadence` param description is substantial (≥80 chars) and names its payoff (`overdue`).

**W3 — #257 non-vacuity floor** (`test_brief_ledger.py::TestBriefPublishNonVacuityFloor`, 8 pins after the fix wave): reject blank / whitespace / `x` / `z` / `hello` / two-token (`proceed now`) with a typed teaching error, nothing stored; accept ≥3-token bodies (three-word + multi-word). Floor = `len(body.split()) < _MIN_BRIEF_BODY_TOKENS` (=3). See §FIX WAVE (supersedes the earlier "7 pins / two-token minimum / single-token" wording).

## Seam choice — why the fleet pins go through the live handler
`_render_comms_fleet_row` currently reads `stale_after_s`; retiring STALE removes its only use of that param, so the builder will likely drop it from the signature. Pinning the row render directly would force the param to survive (a contract accidentally pinning an implementation detail). Pinning through `_comms_fleet` (the handler passes whatever the row needs) makes the pins **robust to that signature change** — proven in the satisfiability run, where the reference build's row still takes `stale_after_s` but the pins never reference it. The holder-liveness surface stays a pure render because its `stale_after_s` is load-bearing (it gates the age display, which "age remains" preserves).

## RED receipts (at HEAD `cca4b49`, `-p no:xdist`)
Two runs (non-live + live). **12 RED (for the right reason) + 4 GREEN (positive-control / regression pins).**

Non-live (`test_comms_schema` + `test_mcp_server` pure/schema pins):
```
FAILED tests/test_comms_schema.py::...::test_declared_cadence_is_option_string_with_no_assert
    AssertionError: no DEFINE FIELD statement found for agent.declared_cadence in generated DDL
FAILED tests/test_mcp_server.py::TestHolderLivenessNoticeRetiresTheStaleGlyph::...
    AssertionError: ... 'note: task ```t-123``` is held by ```holder-y``` (```in_progress```;
      ⚠ STALE, last seen 21m ago) — registering the association anyway'   # glyph present, age present
FAILED tests/test_mcp_server.py::TestCadenceParamDescriptionStatesThePayoff::...
    AssertionError: register's optional 'cadence' param must surface in the lore_comms tool schema
3 failed
```
Live (spike-surreal :18000):
```
FAILED ...TestRegisterPersistsDeclaredCadence::test_register_with_cadence_persists_it_verbatim   # TypeError: register() got unexpected kwarg 'cadence'
FAILED ...TestRegisterPersistsDeclaredCadence::test_register_without_cadence_leaves_it_none       # AttributeError: 'Agent' has no attribute 'declared_cadence'
FAILED ...TestFleetRendersOverdueVerdict::test_overdue_fires_when_silence_exceeds_...             # register cadence unbuilt
FAILED ...TestFleetRendersOverdueVerdict::test_no_overdue_when_silence_is_below_...
FAILED ...TestFleetRendersOverdueVerdict::test_overdue_threshold_tracks_the_declared_value_...
FAILED ...TestFleetRetiresTheStaleGlyph::test_no_declaration_never_overdue_and_no_stale_glyph_past_600s
    AssertionError: ... '- worker [active ⚠ STALE] hb 21m · role ```builder```'     # clean assertion RED
FAILED ...TestBriefPublishNonVacuityFloor::test_single_char_x_is_rejected_and_nothing_is_stored   # DID NOT RAISE (publish('x') succeeds today)
FAILED ...TestBriefPublishNonVacuityFloor::test_a_different_single_token_is_rejected_not_hardcoded_x
FAILED ...TestBriefPublishNonVacuityFloor::test_a_single_real_word_is_rejected_token_not_char
9 failed, 4 passed
```
The **4 GREEN at HEAD are intentional positive controls / regression guards** (not defects): `#257` blank + whitespace (already rejected by the store `_NON_EMPTY_STRING_ASSERT` = `string::len(string::trim($value)) > 0`), and the valid multi-word + two-word bodies (which publish today — proving the floor won't over-reject). Collection is clean (1041 collected; no ImportError). All 21 pre-existing tests in the touched classes still pass (no regression).

## Quantifier table (∀-vs-guarded — one row per load-bearing invariant)
| # | Invariant (property) | ∀ or guarded | Fixture forcing each fate | Wrong build killed |
|---|---|---|---|---|
| W1a | `declared_cadence` is `option<string>`, OVERWRITE, no ASSERT | guarded (offline DDL) | the generated agent DDL statement | required/asserted field (write-poison); `IF NOT EXISTS` (#107 no-op) |
| W1b | cadence persists verbatim / absent→None | 2 fates forced | `register(cadence="≤2m")` vs `register()` | a build that drops, normalises, or defaults cadence wrongly |
| W1c | overdue ⟺ declared ∧ age>cadence | 3 fates forced | declared<age (fires) / declared>age (silent) / **same age, ≤2m vs ≤20m** (monoculture) | hardcoded threshold; cadence-ignoring build (fails the monoculture leg) |
| W1c | no declaration ⇒ never overdue ∀ age | forced at 1300s | undeclared agent, 21m silent | a build that overdues by age instead of by declaration |
| W1d | no `⚠ STALE` at ANY age, both callers | forced past 600s (1300s) | fleet corpse + holder corpse | a below-threshold fixture would pass a still-STALE build vacuously — dodged |
| W1d | age REMAINS after glyph retired | forced | age-token regex `\d+[smhd]` present | a build that drops the age with the glyph |
| W1e | cadence desc states the payoff | guarded | served `inputSchema` description contains `overdue`, ≥80 chars | a terse desc (the R1-measured failure mode) |
| W3 | reject blank/ws/single-token; accept ≥2 tokens | all fates forced | `""`,`"   "`,`"x"`,`"z"`,`"hello"` (reject) · `"proceed now"`,multi-word (accept) | no floor; hardcoded `=="x"`; **char-based `len<2`** (killed by `hello`); over-broad (killed by the accept legs) |
| W3 | rejection is typed/teaching, not a silent drop | forced | message ≥20 chars + teaching keyword; `get_head` raises `UnknownBriefError` after reject | a silent-drop or opaque-error build |

## Satisfiability receipt (the C-DEF class)
Reference build in a provenance-asserted scratch copy (`./scripts/scratch_copy.sh /home/ejprice/pkt06a-scratch`):
```
PROVENANCE loremaster.__file__ = /home/ejprice/pkt06a-scratch/loremaster/loremaster/__init__.py
```
- **All 16 pins pass** against the reference build (`16 passed`).
- **Still satisfiable after the ruff cleanups the change demands.** Ruff flagged exactly two: import-organize (auto-fixed) and `PLR2004` magic-`2` (prod-only per repo config) → extracted `_MIN_BRIEF_BODY_TOKENS = 2`. After both cleanups: `ruff check` **All checks passed** and the pins **still `16 passed`**.
- **Type-level RED resolves:** the 4 `Agent has no attribute declared_cadence` mypy errors present at HEAD are **0** against the reference build (the field now exists). At HEAD these are the type-level equivalent of the runtime RED and resolve on the same build step. (The register calls use `**extra` unpacking, so only the attribute reads type-error, never the `cadence=` kwarg.)

No C-DEF trap: the contract is not self-contradictory and is satisfiable both raw and post-lint.

## Mutation-proof plan (per load-bearing pin — the break that reddens it)
For the builder / cold audit to demonstrate each pin fails against a broken build:
- **W1a:** change the spec to `("declared_cadence","string",...)` (drop `option<`) or `IF NOT EXISTS` → schema pin RED.
- **W1b:** make `register` ignore `cadence` (don't write `_COL_DECLARED_CADENCE`) → persist pin RED; hardcode `declared_cadence="x"` in `_row_to_agent` → absent→None pin RED.
- **W1c overdue:** invert the comparison (`age < cadence`) → fires/silent pins swap RED; hardcode `overdue_after_s = 600` (ignore the value) → **monoculture** pin RED (both rows same verdict).
- **W1c no-decl:** overdue on age alone when `declared_cadence is None` → no-declaration pin RED.
- **W1d:** restore `⚠ STALE` in either render → that caller's pin RED; drop the age in the stale branch → age-remains leg RED.
- **W1e:** shorten the cadence description to a terse label (drop `overdue`) → description pin RED.
- **W3:** remove the floor → x/z/hello pins RED; change `< _MIN_BRIEF_BODY_TOKENS` to `len(body) < 2` (char-based) → **`hello` pin RED** (the token-vs-char discriminator); over-tighten to `< 3` → two-word-minimum pin RED.
- ~~**DRY (builder-owned):** mutate `lorerunes.is_blank` … the blank/whitespace #257 pins must RED …~~ **STRUCK (FIX WAVE, F-DRY).** The adversary PROVED this mutation is VACUOUS: blank is double-guarded (the store `_NON_EMPTY_STRING_ASSERT` + the token check both reject it), so `is_blank → False` leaves the blank pins GREEN regardless — a false-clear instrument. Per repo law ("scaffolding that can lie is worse than none"), this line is withdrawn and `is_blank` is DROPPED from the floor. See §FIX WAVE / §F-DRY.

## DRY ledger (brief-base §6) — new reusable symbols I introduce
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_field_statement(ddl, table, field)` | (in-file) `test_comms_schema._field_statement` | the house DDL-statement parser (fails unless `DEFINE FIELD OVERWRITE`, #107 guard) | **REUSED** `test_comms_schema._field_statement` |
| `_FleetCtx` (live comms harness) | `lore_search "live AgentRegistry fleet render harness"` → `test_comms_status_age._LiveCtx` | a heavier cross-file harness lacking a `cadence` register param and a heartbeat backdater | **HAND-ROLLED** (trivial test glue; the "duplicating trivia is cheap" side; `_LiveCtx` cannot be reused as-is) |
| `_fleet_row(rendered, name)` | same file as `_LiveCtx` | an identical private helper exists in `test_comms_status_age` | **HAND-ROLLED** (trivial 3-line splitter; cross-file, not exported) |

**Production-side reuse — RESOLVED (FIX WAVE, F-DRY): the `is_blank` reuse mandate is MOOT for this floor, so no blankness predicate is used.** The adversary proved (a) reuse is unenforceable-by-construction here — blank is double-guarded (store ASSERT + the ≥3-token check both reject it), so no `is_blank` mutation can redden a blank pin; and (b) `is_blank` is redundant — `len(body.split()) < 3` already rejects blank/whitespace/short. The floor is the SINGLE token-count check; the blank/whitespace reject pins stand, subsumed. The operator/lead ruled DROP. Nothing is hand-rolled either — no blankness predicate is needed. (This retires the operator-ruling-2 "reuse the lorerunes predicate" clause for this specific floor, as adjudicated in the fix wave.)

## Store DDL verification (the #107 order)
1. **Store reference §1.4** (cited, not re-transcribed): a NEW field on the POPULATED `agent` table MUST be `option<>` with no ASSERT (a required/asserted field write-poisons every legacy row's next UPDATE; a DEFAULT does not rescue it). §1.1: FIELD → `OVERWRITE`.
2. **`lore_search(tier="surrealql-tests")`**: `DEFINE FIELD ... TYPE option<string>` is valid, CI-verified syntax (`tests/language/idiom/define_field_dot_star_2.surql`).
3. **Live precedent (stronger than a fresh probe):** `status_set_at` (#304) ships this EXACT idiom (`("status_set_at","option<datetime>","")`) in production today. The round-trip pin (register persists cadence; a legacy no-cadence row survives) is the live proof; it passed against the reference build.

## Old-world inventory — tests certifying the RETIRED glyph (rename/retire law)
These OUTSIDE-my-writable-set tests assert `⚠ STALE`/`STALE` **presence** and will go RED when the builder retires the glyph. Each needs an individual verdict from the builder (bare-grep, anchor-free sweep — this is the full set on the fleet-row + holder surfaces):
- `test_comms_register_notice.py::TestHolderLivenessRenderSet::test_stale_holder_renders_STALE_with_age` — `assert "STALE" in notice` → **FLIP** to `not in`; KEEP `"last seen"` + the minutes token (age remains). Becomes a clean retirement pin.
- `test_comms_register_notice.py::TestStaleThresholdIsSharedWithFleet::test_both_surfaces_flip_at_one_threshold` — `assert "STALE" in {notice,fleet}` (×2) — **premise dissolves**: the fleet row no longer renders STALE at all (see below). Rework or delete.
- `test_comms_register_notice.py::TestStaleThresholdIsSharedWithFleet::test_both_surfaces_share_the_EXTRACTED_predicate` — monkeypatches `_heartbeat_is_stale` and asserts BOTH surfaces reflect it (`assert "STALE" in ...` ×2). **Obsolete**: the fleet row exits the `_heartbeat_is_stale` club entirely.
- `test_comms_promise_registry.py:354` — `_TEMPLATE_REGISTRY` entry `"- {name} [{status} ⚠ STALE] hb {age} · {cells}"` → **DEAD** once the STALE branch is deleted; `test_no_dead_registry_entries` will RED. Remove the entry (and add the new `overdue` template if the registry pins it).

**Design consequence to surface (not a fork, a flag):** retiring STALE from the fleet row **dissolves the #262 "both surfaces share one staleness predicate" coupling** — the fleet row no longer has a staleness verdict, so `_heartbeat_is_stale` survives only for the holder-liveness age-gating. The builder must decide `_heartbeat_is_stale`'s fate and rework the two shared-predicate tests accordingly.

## Forks (escalating is the success state)
- **F1 — `single-token` reading (RESOLVED with a pick, flagged).** Operator ruling 2 says "reject blank / whitespace-only / **single-token**"; my brief W3 says "single non-whitespace **token**"; the positive case is "a valid **multi-word** body passes." I read this as **≥2 whitespace-delimited tokens required**, so a single real word (`hello`) is REJECTED (pinned in `test_a_single_real_word_is_rejected_token_not_char`). The alternative reading is single-**character** (reject only `len<2`), under which `hello` PASSES. If the operator meant single-char, that ONE pin flips. **RECOMMEND: token** (the ruling's literal word). Note the mild consequence: a legitimate single-token body (a bare URL) is rejected; the ruling said "no pin-the-miss test", so I did not pin that bound — flagged as an observation only.
- **F2 — old-world STALE tests** (see §Old-world inventory): 5 sites the builder must update, outside my writable set. Not a decision, but the lead should route them into the builder's brief.
- **F3 — `heartbeat` cadence:** design §B.7 says "and *optionally* `heartbeat`". I pinned `register` only (definite). RECOMMEND the builder add `heartbeat` cadence for symmetry; if the operator wants it required, add a heartbeat round-trip pin.
- **F4 — fake-ledger #257 fidelity:** the floor lives in production `BriefLedger.publish`; the pins are real-only. Should `FakeBriefLedger` mirror the floor (double-fidelity)? Builder/design decision.

## Reference build (durable artifact — the scratch is disposable)
A known-correct minimal implementation that makes all 16 pins green (captured here so it survives the scratch copy). NOT the deliverable — the real builder owns production choices (e.g. the cadence parser and the `heartbeat`/re-register wiring I left minimal):
- `agents.py`: `_COL_DECLARED_CADENCE="declared_cadence"`; `Agent.declared_cadence: str | None = None`; `register(..., cadence=None)` → CREATE content `_COL_DECLARED_CADENCE: cadence`; `_row_to_agent(... declared_cadence=row.get(_COL_DECLARED_CADENCE))`. (Re-register UPDATE left unchanged — not exercised by the pins; the real build should handle mutable-on-provided like `model`/`task_id`.)
- `surreal_schema.py`: `("declared_cadence", "option<string>", "")` in `_AGENT_FIELD_SPECS`.
- `server.py`: module-level `_parse_cadence_seconds` (tolerant of a `≤` prefix); `_render_comms_fleet_row` replaces the STALE branch with the overdue branch (reads `row.declared_cadence`, compares `heartbeat_age_s`); `_render_holder_liveness_notice` drops `⚠ STALE ` (keeps `last seen {age} ago`); `cadence` added to the `comms` tool signature (payoff `Field(description=...)`) and to `_COMMS_ACTIONS[register].params`.
- `briefs.py`: `from lorerunes import is_blank`; `_MIN_BRIEF_BODY_TOKENS = 2`; `BriefBodyTooThinError`; the floor `if is_blank(body) or len(body.split()) < _MIN_BRIEF_BODY_TOKENS: raise BriefBodyTooThinError(...)` before the mint.

## Disposal
Scratch reference build at `/home/ejprice/pkt06a-scratch` (git-untracked, `scratch_copy.sh` provenance-asserted). Disposable by design; the diff above is the durable record. **Awaiting operator/lead call: keep it for the builder, or `rm -rf` it.** No git state touched (the lead commits).

---

## §FIX WAVE (2026-08-11) — adversary INSUFFICIENT → resolved

`adversary-honesty-06a` returned INSUFFICIENT (1 BLOCKER + 3 improvements; 11/12 wrong builds reddened). All items applied in my writable set (`test_comms_schema.py`, `test_mcp_server.py`, `test_brief_ledger.py`) + the reference build. Revised contract: **19 pins, 15 RED (right reason) + 4 GREEN (positive controls)** at HEAD `cca4b49`.

### F-ECHO (BLOCKER) — fixed
The overdue verdict's ECHOED cadence was a value monoculture: every overdue-rendering fixture declared `≤2m`, so a build reading `row.declared_cadence` for the *threshold* but HARDCODING the *displayed* cadence to `≤2m` passed all 4 W1c/W1d pins while shipping a false self-set contract (an agent declaring `≤1h` renders `declared ≤2m` — the #104/Consumer-Law trust defect §B.7 exists to prevent).
- **Added** `TestFleetRendersOverdueVerdict::test_overdue_verdict_echoes_THIS_agents_own_cadence_and_silence`: two agents, DIFFERENT cadences (`≤7m`/`≤3m`) AND DIFFERENT ages (20m/15m), BOTH overdue → each row must echo its OWN cadence and its OWN silence. Tokens `7m/3m/20m/15m` are mutually non-substring, so each uniquely fingerprints its row; a constant/swapped echo cannot satisfy both.
- **F-SILENT-AGE folded in**: the same pin asserts each row's `silent {age}` is its own (different ages make it discriminate — the adversary's suggested same-age pin could not).
- Kills the adversary's `WB-HARDCODED-ECHO` (`cadence=safe_str("≤2m")`) → `"7m" in slow_row` fails.

### F1 (operator ruling) — applied: `_MIN_BRIEF_BODY_TOKENS = 3`
Reject <3 whitespace tokens. `test_the_two_word_minimum_publishes` → **flipped** to `test_a_two_token_body_is_rejected` (RED at HEAD: `"proceed now"` publishes today); **added** `test_a_three_word_body_publishes` (`"proceed with caution"`, GREEN at HEAD — the accept boundary). `hello` (1 token) stays rejected. Teach message + module note updated; the single-token-vs-char D-fork is now moot (operator ruled 3).

### F-DRY — RULED = DROP `is_blank` + STRIKE the vacuous line
Adjudicated as the lead ruled: (a) the §Mutation-proof-plan `is_blank` line is **STRUCK** above (it was a false-clear — blank is double-guarded, so `is_blank → False` never reddens a blank pin); (b) the reference-build floor is now the SINGLE check `len(body.split()) < _MIN_BRIEF_BODY_TOKENS` (the `from lorerunes import is_blank` import DROPPED); (c) the blank/whitespace reject pins STAND (subsumed by the token check + the store `_NON_EMPTY_STRING_ASSERT`). No blankness predicate is used or hand-rolled. DRY-ledger production-reuse note updated above.

### F-REGISTRY — satisfiability re-run over the FULL touched surface (honest count)
My original "16 pass" was scope-true, not build-true: the reference build's render changes reddened **2 pins outside the 16** (`test_every_comms_render_literal_is_classified` — the new `overdue` literal unclassified; `test_no_dead_registry_entries` — the dead STALE entry). Resolved in the reference build by editing `test_comms_promise_registry.py`'s `_PROMISE_FREE`: **added** `"- {name} [{status}] overdue (declared {cadence}, silent {age}) · {cells}"`, **removed** the dead `"- {name} [{status} ⚠ STALE] hb {age} · {cells}"`. (The holder-liveness `"last seen {age} ago"` change is NOT scanned — no registry edit needed; empirically confirmed.)
- **Honest full-surface satisfiability receipt** (provenance `loremaster.__file__ = /home/ejprice/pkt06a-scratch/loremaster/loremaster/__init__.py`):
  ```
  19 contract pins + test_comms_promise_registry.py  ->  139 passed
  ruff check (briefs, server, agents, surreal_schema, + all 4 test files)  ->  All checks passed
  ```
  Still satisfiable after the ruff cleanups the change forces (import-organize + the PLR2004 `_MIN_BRIEF_BODY_TOKENS` constant, already in place).
- **Builder obligation (added to F2 / old-world):** the builder MUST make the same `_PROMISE_FREE` edits and RUN `test_comms_promise_registry.py`; the C-DEF satisfiability leg is over the FULL touched surface, not the 19.

### F-GLYPH — class-closing invariant added (fails closed)
There was no SEMANTIC ban on `⚠ STALE` in comms render literals — a re-introduction (the #262 class: the glyph was re-propagated into a NEW render *after* #259 ruled it retired) was caught only as an unclassified literal a dev can classify past.
- **Added** `TestNoStaleGlyphLiteralInCommsRenders::test_no_stale_glyph_literal_in_any_server_string` (in `test_mcp_server.py`): an AST scan of `server.py` string literals (docstrings excluded — prose is never served) that FAILS if any contains `⚠ STALE`, and **FAILS CLOSED** (asserts `scanned > 0`, so a walk that visits nothing is a failure, never a vacuous pass). RED at HEAD (offenders = the 2 render templates). REACH BOUND stated in the docstring: covers `server.py` (where all comms renders live); re-open trigger = a comms render moving to another module.

### Revised RED receipt (HEAD `cca4b49`)
```
15 failed, 4 passed
  RED: schema(1) · register(2) · overdue+F-ECHO(4) · fleet-STALE-retire(1) · holder-retire(1)
       · cadence-desc(1) · F-GLYPH scan(1) · #257 x/z/hello/two-token(4)
  GREEN (positive controls): #257 blank · whitespace · multi-word · three-word
```
Revised contract returns to the adversary (standing law: contract → adversary → build).

---

## §CONTRACT FIX WAVE (2026-08-11, post-build) — 2 test collisions + F3 heartbeat gap

The builder landed production (working tree, uncommitted), which surfaced 2 collisions in `test_brief_ledger.py` (lead-granted scope to edit) + the F3 heartbeat-cadence gap. All fixed and GREEN against the BUILT tree; each mutation-proven.

### FIX #2 (mechanical) — `real_brief_ledger` fixture must seed
My new fixture builds a real `BriefLedger` + `make_env` without `_seed_agent_rows`, so the `TestEveryRealLedgerSiteSeedsItsAgentRows` AST sweep flagged it (`unseeded == ['real_brief_ledger']`). **Fixed:** added `await _seed_agent_rows(env, [])` after `make_env` (its tests publish without `agent_id`, so an empty seed satisfies the "force new sites to seed" sweep). Self-proving: the sweep IS the guard — the collision itself demonstrated it discriminates (removing the seed re-reddens it).

### FIX #1 (REMOVED-BEHAVIOR ADJUDICATION) — the #257 floor changed reachability
`test_a_rejected_create_rolls_back_the_edge_too_and_burns_no_version` used `publish("")` (blank body) to trigger a STORE `SurrealStoreError` at the CREATE and exercise the POST-mint rollback (edge-rollback + version-release + gaplessness). The #257 floor now rejects a blank/short body **PRE-mint** (`BriefBodyTooThinError`), which never reaches the mint/CREATE — the rollback path became unreachable via a blank body.
- **Adjudication (dual-of-rename law):** I did NOT weaken to the app path. The builder's suggested bad-NAME trigger was **rejected** — a bad name mints off a DIFFERENT `brief_counter` row, so the version-release/gapless coverage (which needs the SAME name's counter minted-then-released) would be silently LOST. Instead the trigger is a **blank `created_by`** (valid ≥3-token body, valid seeded agent_id): it clears the floor and the mint, then fails the `brief.created_by` non-empty ASSERT at the CREATE (POST-mint), **under the same name** — preserving edge-rollback + no-row + version-release + gaplessness.
- **Mutation-proof that it is genuinely POST-mint** (a PRE-mint failure would silently lose the rollback coverage — the exact hazard the lead flagged): in a fresh scratch of the built tree, broke `_release_version` to a no-op →
  ```
  test_a_rejected_create_rolls_back_the_edge_too_and_burns_no_version
    ->  RED at `assert recovered.brief.version == 2`
  ```
  The gapless assertion reddened, which can ONLY happen if the trigger minted a version (POST-mint) that the broken release failed to hand back → the next publish got v3. A pre-mint failure would never bump the counter and would leave this GREEN. Reachability confirmed; restored after.

### F3 — heartbeat-cadence pin (was unguarded)
The builder wired `cadence` on `AgentRegistry.touch` (heartbeat) too, mutable-on-provided (the `note` idiom), but my contract pinned `register` only. **Added** `TestHeartbeatPersistsDeclaredCadence` (2 pins) in `test_mcp_server.py`: (a) `touch(cadence="≤5m")` persists `declared_cadence`; (b) a bare `touch()` after a prior declaration PRESERVES it (never nulls). Both mutation-proven, each direction independently:
```
touch: new_declared_cadence = agent.declared_cadence  (ignore param)  -> test_heartbeat_with_cadence_persists_it  RED, bare pin GREEN
touch: new_declared_cadence = cadence                 (null on bare)  -> test_a_bare_heartbeat_does_not_null_...   RED, persist pin GREEN
```
Each pin reddens for its OWN property and no other — they discriminate independently.

### GREEN receipts (built working tree, `-p no:xdist`)
```
TestPublishSelfAckIsWrittenInTheSameTransaction + TestEveryRealLedgerSiteSeedsItsAgentRows
  + TestBriefPublishNonVacuityFloor + TestHeartbeatPersistsDeclaredCadence
  + TestRegisterPersistsDeclaredCadence + TestFleetRendersOverdueVerdict
  + TestFleetRetiresTheStaleGlyph + TestHolderLivenessNoticeRetiresTheStaleGlyph
  + TestNoStaleGlyphLiteralInCommsRenders + TestCadenceParamDescriptionStatesThePayoff  ->  24 passed
test_declared_cadence... (schema) + TestEveryCommsRenderLiteralIsClassified               ->  4 passed
ruff check (test_brief_ledger, test_mcp_server)                                           ->  All checks passed
```
The whole contract is now GREEN against the built tree (the build matches the contract), and the promise-registry classification (F-REGISTRY) is resolved on the builder's side. Revised contract returns to the adversary (standing law).

### R1 (cold audit, LOW) — dispatch→registry cadence wiring pinned
The round-trip pins test `AgentRegistry` DIRECTLY, leaving the SERVED path (`comms(action=register/heartbeat, cadence=...)` → dispatch hop → `registry.register/touch`) unpinned — a refactor dropping the `cadence` kwarg in the dispatch hop would silently stop cadence persisting via the tool. **Added** `TestCadenceWiredThroughTheDispatch` (the cold auditor's Appendix C pin, verbatim) in `test_mcp_server.py`, exercising cadence end-to-end through `AppContext.comms` for BOTH register and heartbeat (reusing the `test_comms_wiring` dispatch harness). GREEN on the built tree (2 passed; 10 passed with the cadence+overdue pins). **Mutation-proven "reddens it and ONLY it":** dropping `cadence` in BOTH dispatch hops (register `_comms_register`→`register(cadence=None)`; heartbeat dispatcher→`touch(cadence=None)`) reddened both dispatch pins (declared_cadence → None) while all 4 direct round-trip pins stayed GREEN — the served-path gap the round-trip pins cannot see.

### Scratch disposal
Two scratch copies exist (git-untracked, provenance-asserted, disposable): `/home/ejprice/pkt06a-scratch` (original reference build), `/home/ejprice/pkt06a-fixwave-scratch` (built-tree copy used for the mutation-proofs). **Awaiting operator/lead call: keep for the builder or `rm -rf` both.**
