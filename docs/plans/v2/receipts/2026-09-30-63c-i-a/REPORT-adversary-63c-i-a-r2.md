# REPORT-adversary-63c-i-a-r2 — contract-adversary DELTA pass on revision 2 of the 63c-i-a contract

brief-base v16 read · brief project v7 read

## SUMMARY BLOCK
- **state:** done-with-deviations · **VERDICT: CONTRACT INSUFFICIENT** (measured 2026-09-24 against `88205a4`). **7 wrong builds survive** (N1, N1c, N2, N3, N4/N4h, N5, N10); each has a kill-pin proven RED on it and GREEN on my reference (§4.2, §6). Five of them (N1c+N2+N3+N5+N10) applied TOGETHER pass the **whole tree: 11292 passed, 0 failed**.
- **Graded:** `88205a4` · HEAD-at-report: `91c6f5c` · DIFFERENT (5 ahead: amendment 3 `e6bedd1` + 4 docs/lead-report commits; `git diff --stat 88205a4 HEAD -- loremaster lorerunes lorescribe loresigil scripts skills` is EMPTY, so no pin or production symbol my verdict rests on moved). Amendment 3 is reconciled in §14; it changes no verdict.
- **deviations:** (1) wrong builds run through my own declare-then-diff lane driver, not `mutation_proof.py`, because most are multi-edit or declared-to-SURVIVE (§0). The one single-anchor build amendment 3 asks for (WB-2of3) did run through `mutation_proof.py`: PROOF HELD. (2) **lore MCP unreachable since a `lore-surreal` restart at 15:19:56** (not mine), so no ledger heartbeat after that point and no thread-`63c` pointer; finding NOT filed (§12 R-1: the lead must file it).
- **P1 / prior floor:** **11/11 prior survivors KILLED** (WB1–5, WB8–13, plus the A3-consistent WB12b; §4.1). **Satisfiability (own reference, written independently):** 18 contract files `2521 passed`; **full suite ALONE `-n 12`: `11292 passed, 62 skipped, 3 xfailed`, 0 failed**; ruff clean; typecheck clean except the r2 registry entry's 8 intended SELF-DESTRUCTs (§2, §5). **RED@HEAD reproduced exactly** (148 red / 2345 passed, all right-reason; §1).
- **MISSING PINS (§6):** **MP-A BLOCKER** (the identity decision's SKIP-policy consumer `_is_comms_charset_legal` is unpinned: N1/N1c survive; ORPHANED — in no sub-wave's A4 consumer list) · **MP-D BLOCKER** (the population resolver's endpoint reach is a spelling hand-list, not a checked variable: N4/N4h survive; fix = derive from the emitted DDL, which the tree already parses) · MP-F (re-register heals an ownerless row → scope-without-owner, invisible to the migrate forever: N10) · MP-B (A3 refusal on the create path only: N2) · MP-G (the shared patch helper false-REDs a correct aliased import, with a lying message) · MP-E (fake stamps are decoration: N5) · MP-C (P2 small-N: the ruled id bound is invisible at 2 traps: N3).
- **P1b (§7):** 15 invariants: 10 ∀-SAFE with killed door-builds; 5 GUARDED → MISSING (I10 id bound, I17a decision consumers, A3 path, MINT, I4b instrument). **P1c (§8):** 13 instruments: 3 MISSING (resolver reach; the decision-mutation pin's hand-list; the fake-mirror PROXY) plus 1 instrument defect (the patch helper's name-keyed reach); the rest SAFE; empirical vs construction legs stated per row.
- **Packages considered:** stdlib `re`/`importlib`/`ast`; `unittest.mock.patch` + `MonkeyPatch.setattr` (read live: single-target) → the bespoke sweep is justified; in-house `lorerunes.keep_scope`/`is_blank` REUSE. Diff vs the author's line: none on mechanisms (§9).
- **Odoo-20 portability:** n/a — no Odoo seam touched. **Reuse ledger:** none (I added no repo symbols; scratch instruments are pasted verbatim in §A).
- **DUAL / corpses:** my independent enumeration of the r2 diff matches the author's §DUAL rows 1–6 exactly. No re-key weakened a pin's virtue, and no re-keyed fixture collapsed into a monoculture a branch keys on (§3). Corpse sweep: every hit got its own verdict, and none is a corpse (§11). Two pieces of production prose the build will falsify are named for the builder.
- **decisions-needed:** NF-1 (A4's consumer set must include `_is_comms_charset_legal`: recommend yes) · NF-2 (may a legacy hostile-named agent re-register after the MOVE? recommend no) · fix MP-G before amendment-3 F-3's fold · the lead files R-1 (lore MCP does not recover from a store restart).
- **Receipt pointers:** §1 RED · §2 SAT · §3 DUAL diff · §4 wrong builds · §5 pending_contracts · §6 MISSING PINS · §7 P1b · §8 P1c · §9 P-PKG · §11 corpses · §12 residuals · §13 ORPHANED/forks · §14 amendment 3 · §A instruments (verbatim).

---

## 0. Capability check (brief-base §4)
- Everything demanded was reachable: lore MCP (comms/findings), `git`, `uv run pytest/ruff`, `scripts/pending_contract_gate.py`, `scripts/scratch_copy.sh`, the test store `ws://127.0.0.1:18000`.
- **grep/rg are hook-blocked (#473), also inside scratch copies.** Every textual sweep in this report is `awk` over `git ls-files` (or over scratch trees) — said here, per brief-base §4 and the brief.
- **`scripts/mutation_proof.py` fits single-anchor, single-file mutations; most of my wrong builds are multi-edit and several are declared to SURVIVE (an empty expected-RED set, which the tool's required `--expect-red` cannot express).** So the wrong builds run through my own lane driver (`run_lane.sh` + `my_wbs.py`, pasted verbatim in §A), which keeps the tool's discipline: the expected-RED set is resolved from `pytest --collect-only -q` (`collected.txt`, 2521 ids) BEFORE any wrong-build run, and the observed set is diffed BOTH ways (unexpected reds · declared-still-green). Said as a deviation from the brief's "use `scripts/mutation_proof.py`".
- Store reference `docs/reference/surrealdb-31-capabilities.md` read first (the six-fact header + §1 provenance legend). Nothing here probes a store fact it documents; the only engine facts I lean on are §1.4 (a whole-row UPDATE re-validates every field — cited by the contract's heartbeat/Leg B pins) and §3 (atomic abort).

## 1. P7 — RED honesty, reproduced (measured 2026-09-24, tests at `88205a4`, production at HEAD `0eed242` — production is byte-identical to `88205a4`'s)
- Scratch `…/scratchpad/red` via `./scripts/scratch_copy.sh`; provenance `loremaster.__file__` = `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/dc888a1c-9807-4fec-be48-0a1fc30a29b1/scratchpad/red/loremaster/loremaster/__init__.py`.
- Scope: the 17 `test_*.py` files `88205a4` touches (`git diff --name-only 0b8ce37 88205a4 -- 'loremaster/tests/test_*.py'`) + `test_comms_wiring.py` (r1's fifth contract file; 28 tests, all green at HEAD), `pytest -n 12`.
- **Tail, run twice:** `97 failed, 2373 passed, 4 warnings, 51 errors` (207.83s; again in 267.32s). 148 red. Minus the 28 wiring tests (all passed), that is **148 red / 2345 passed — the author's §RED numbers exactly** (`TOTAL red 148 · passed 2345`).
- **Classification (junit XML, every red read):** 85 × `TypeError … unexpected keyword argument 'session_keep_id'` (the author's 78 fallout + 7 contract pins) · 32 × store ASSERT still lands (`TxnDomainRejectionError … (assert violation)`: the MOVE hostile/blank pins, Leg A/B) · 4 × `module 'lorerunes' has no attribute 'is_legal_identifier' / 'AGENT_NAME_PATTERN'` · 1 × `DID NOT RAISE` (the `is_blank` mutation pin) · 26 × behavioural assertion reds, each read individually: W1-1 columns/indexes absent, `owner_agent`/`scope` read back `None`, the five-set is `['memory','message','to']`, R-Q5-1 not refused, the project keep never minted, the exempt token carrying the old owner-only `UPDATE … WHERE owner_principal IS NONE`, the tokenless spy seeing no `session_keep_id` key, the signature/fake-mirror pins naming the missing kwarg, Leg A's "RED-at-HEAD (right reason)".
- **Every red is for the right reason.** The r1 MP-2 false gate is fixed: the heartbeat leg now reds on `TxnDomainRejectionError … (assert violation)` (the seed id is `AgentRegistry._agent_id("wave7","legacy-agent")`).
- **GREEN at HEAD, each checked to be a guard/control by design (23):** `TestTheConstraintREDNamesTheTablesOwnWriter63cIA` ×3 (prose, build-independent), the valid-identifier positive controls ×4, `test_owner_principal_is_emitted_exactly_once`, `test_the_provenance_pair_is_unreachable_from_the_wire`, the R-Q5-1 CONTROL, idempotence, the frozen-capture control, BASELINE ×4, clean-row control, status-STAYS, the two frozen-DDL C-controls (migrate, touch), P-A3 + its control, and the re-export resolver pin (test substrate). None claims RED-at-HEAD in its docstring.

## 2. SATISFIABILITY — my OWN reference build (independent of the author's `ref_build_r2.py`)
- **Instrument:** `my_ref_build.py` (§A.1, verbatim). I did not read the author's `ref_build_r2.py` before writing it. The Q3/W1-1/Q5 legs reuse the PRIOR adversary's §A.1 anchors (`b46d3f2`, a different author from the contract under grade). The A2/A3/A4 legs are mine, written from `agents.py::AgentRegistry.register`, `server.py::AppContext._comms_register` / `_is_comms_charset_legal` and `lorerunes/__init__.py`. Notable choices: the decision lives in a new `lorerunes/identifiers.py` (`AGENT_NAME_PATTERN` + `is_legal_identifier`, re-exported at package level); `agents.py` re-exports the pattern object; `_is_comms_charset_legal` becomes a one-line call of `is_legal_identifier` (so BOTH server policies, refuse and skip, read the shared decision); the registry refuses the mixed pair first, then the identity/role (teaching, `render_fenced`), then `_select_row`; the stamp is `keep_scope(session_keep_id)` + `RecordID(AGENT_TABLE, agent_id)` inside the CREATE; `_comms_register` passes `session_keep_id` unconditionally.
- Provenance: `…/scratchpad/ref/loremaster/loremaster/__init__.py`, `…/scratchpad/ref/lorerunes/lorerunes/__init__.py`; `is_legal_identifier("fixer-b"), is_legal_identifier("fixer-b\n")` → `True False`.
- **Lint-demanded cleanup:** ruff flagged exactly one thing (`agents.py` F401 unused `import re`, the pattern moved out); deleted. Then `uv run ruff check .` → `All checks passed!`.
- **Contract files (17 + wiring), `-n 12`:** **`2521 passed, 4 warnings in 228.36s` — 0 failed, 0 errors.**
- **Full suite ALONE, `-n 12`** (no other pytest on the box — `ps` count 0 before launch; provenance `…/scratchpad/ref/loremaster/loremaster/__init__.py`): **`11292 passed, 62 skipped, 3 xfailed, 7 warnings in 470.38s` — 0 failed, 0 errors, exit 0.** Identical to the author's §SAT count (11292/62/3) on an independently written build. No #466 flakes appeared.
- **Combined survivors over the FULL tree** (N1c + N2 + N3 + N5 + N10 applied together on `adv2-ref`, `4 files changed, 18 insertions(+), 12 deletions(-)`, alone, `-n 12`): **`11292 passed, 62 skipped, 3 xfailed, 7 warnings in 531.13s`, exit 0** — five wrong builds at once, invisible to every test in the repository, not just the contract files.
- **Typecheck on the built world** (`pending_contract_gate.py --currency --legs typecheck,ruff` in the ref copy): typecheck's ONLY residuals are the 8 SELF-DESTRUCT findings for the r2 registry entry's 8 files ("produced NO mypy errors — the bound is discharged. DELETE its registry entry with the fix") — i.e. no real mypy error on the build; ruff GREEN. §5.

## 3. FOCUS 1 — the delta itself: DUAL / re-key / monoculture (independent enumeration FIRST, then the diff)
**Method.** I read `git diff 0b8ce37 88205a4` over every test file and `_governed_contract.py` / `_comms_fakes.py` and wrote my list of deleted/inverted/re-keyed pins BEFORE opening the author's §DUAL/§FALLOUT. Then I diffed.

| # | my enumeration (from the diff alone) | author's §DUAL/§FALLOUT row | virtue weakened? — my verdict |
|---|---|---|---|
| D1 | `test_agent_capability.py::test_register_exposes_no_display_owner_argument` DELETED → exact-signature pin + wire-disjointness pin + fake-mirror pin | §DUAL 3 | **No.** The old pin's two assertions (`owner_principal_id ∈ params`; forbidden ∩ params = ∅) are both implied by the exact set; the wire leg is NEW virtue. Residual: the wire surface is derived from `_COMMS_ACTIONS['register'].params` + `AppContext.comms`'s signature, not the served MCP tool function's — construction-inspection only (the tool funnels through `comms`). |
| D2 | `test_comms_schema.py::TestAgentRoleNonEmptyAssert` (×5 incl. the real-role control) DELETED | §DUAL 1 | **No.** Store-level virtue → Leg A[role]; writer virtue → the `is_blank` MOVE pins; the real-role store positive control → the register positive control (register layer, not store layer — acceptable: the store now accepts any role). |
| D3 | `test_memory_enforcement_63b_ia.py::test_the_derived_population_set_is_the_known_set` DELETED (fold) | §DUAL 2 | **No.** Its `NotImplementedError` guard message is lost (cosmetic: the derivation is built). |
| D4 | r1 local `_MOVE_HOSTILE_IDENTIFIERS` (7) → shared `_HOSTILE_IDENTIFIERS` (13) | §DUAL 4 | **No — checked shape by shape.** The local list's 7 classes (`"Bad Name!"` punctuation, space, `UPPER`, `colon:here`, `-lead`, `"z"*65`, `""`) are all present in the shared corpus as a class (punctuation via quote/colon/backslash). Residual R-C1 below (uppercase only at position 0). |
| D5 | r1 regex-twin pin (patched `agents.AGENT_NAME_PATTERN` with a never-matching pattern) → per-field identity-sweep patch at the `lorerunes` home + an `is AGENT_NAME_PATTERN` identity assert | §DUAL 4 | **No**; strengthened (per field). The `re.compile`-cache bound (F-5) is real and correctly stated. |
| D6 | `test_comms_footer.py::…moves_EVERY_members_refusal` retarget (single-module patch → identity sweep) | §DUAL 5 | **No weakening at the tool layer** — but it is the DECISION-vs-PATTERN seam: this pin shares the pattern OBJECT, and the only pin that shares the DECISION (`test_the_identifier_decision_is_the_SHARED_is_legal_identifier`) observes `_validate_comms_charset` alone. The server's second policy over the same decision (`_is_comms_charset_legal` → `_comms_traffic_line`, the SKIP policy) is observed by neither → **MP-A (§6)**. |
| D7 | `_ConstraintSpec`: `make_ddl` default removed, `hazard` slot added; ∀ body lifted into `_assert_no_violable_constraint` | (§ITEMS 11) | **No** — the lifted body is byte-identical to r1's inline loop except the message now interpolates `spec.hazard`. |
| D8 | heartbeat leg: seed id = the production mint; `except Exception` → `except SurrealStoreError`; E2 control added | (§ITEMS 2) | **No**; fixed. |
| D9 | R-Q5-1: `\b1\b` + scope-count proxy → 2 traps, `SELECT *` byte-inert, count-beside-noun, every id, "by hand" | (§ITEMS 6) | **No**; strengthened. Residual: the fixture's 2 traps sit below the ruled id bound → **MP-C (§6, P2 small-N)**. |
| D10 | `TestMigrateAgentOwner`: pre-owned fixture re-keyed to owner + THE session keep; `backfilled >= 1` → `== 1`; untouched-row check widened to all 3 governed columns | §DUAL 6 | **No.** The retired virtue ("an owned, unscoped row survives the migrate untouched") is RETIRED by design (§6 now refuses that shape). |
| D11 | 13 files' owner-bearing `register` fixtures gain `session_keep_id` (store-backed: `session_keep_id_for`; registry-only: `registry_level_session_keep_id`) | §FALLOUT | **No virtue weakened; one monoculture note.** Every re-keyed fixture passes the CONSISTENT pair `(owner, keep)`; the mixed shapes are exercised only by the 4 new registry-level A3 pins, on an EMPTY store (first register) → **MP-B (§6)**. `registry_level_session_keep_id` is a constant per session (`registrylevel_s1`) — harmless: those harnesses never assert scope. |
| D12 | `_comms_fakes.FakeAgentRegistry.register` gains `session_keep_id`, the A3 XOR raise, and `owner_agents`/`scopes` stamps | §ITEMS 8 | **The stamps are decoration (P5).** No test in the tree reads `db.scopes` / `db.owner_agents` (awk over `loremaster/tests/*.py`: the only hits are `_comms_fakes.py:184/186/306/307`, the writes themselves) → **MP-E (§6)**. |
| D13 | `scripts/pending_contracts.yaml` — new bound `packet-63c-i-a-contract-r2` (8 files) | §GATES | See §5 — sound; self-destructs on the built world, not before. |

**Diff of the two enumerations:** my D1–D6 + D10 = the author's §DUAL rows 1–6 exactly; D11 = §FALLOUT; D7–D9, D12–D13 are §ITEMS rows. **No DUAL row of the author's is ungrounded, and none of mine is missing from theirs.** What theirs does not say is D6's decision/pattern split and D12's decoration, both new findings below.

**Parameter monoculture in re-keyed fixtures:** none that a branch keys on. Name/session in the MOVE pins now carry DIFFERENT legal values (`fixer-b` / `wave7`) so per-field mutations discriminate (checked: `_LEGAL_NAME`/`_LEGAL_SESSION`). The stamp pins use two sessions and two principals (kills r1's one-principal/one-session monoculture).

## 4. P1 — wrong builds (the headline). FOCUS 2: the prior pass's 11 · FOCUS 3: new builds against the r2 seams
**Method.** Four provenance-checked lanes (`…/scratchpad/{wb,red,wb3,wb4}`, each `scratch_copy.sh` + my `adv2-ref` applied; production diff byte-identical to `ref` in each, checked by `diff` of `git diff`). Each wrong build is applied ON TOP of `adv2-ref` by `my_wbs.py` (exactly-once anchors); its DECLARED expected-RED set is resolved from `collected.txt` (`pytest --collect-only -q`, 2521 ids) BEFORE the run; the lane runs the 17 r2 test files + `test_comms_wiring.py` at `-n 12` with junit XML and diffs observed vs declared BOTH ways (`run_lane.sh`, §A.3). Lane provenance lines: `…/scratchpad/{wb,red,wb3,wb4}/loremaster/loremaster/__init__.py`. Measured 2026-09-24 against `88205a4`.

### 4.1 The prior pass's 11 surviving wrong builds (b46d3f2 §3) — ALL now KILLED
| WB | the door (r1) | adapted to r2 seams as | r2 result (observed vs declared) |
|---|---|---|---|
| WB1 | W1-1 twin: pkt-62 row + inline index kept, emitter filtered + deduped | same anchors | **KILLED exactly** (1/1: `test_every_governed_column_and_index_MOVES_with_a_REWRITE_of_the_shared_emitter`) |
| WB2 | backfill loses its `WHERE` | same | **KILLED** (4 red; declared 3 all fired — mixed-store, exempt-token, `TestMigrateAgentOwner` — plus 1 I did not predict: `TestResolveOperatorPrincipalIsLifted::test_the_operator_resolution_is_shared_by_mutation`; my misprediction, recorded) |
| WB3 | precondition keyed on owner only | same | **KILLED** (3 red; declared 2 fired + the same unpredicted `TestResolveOperatorPrincipalIsLifted` pin) |
| WB4 | scope = `sorted(visible)[0]` | `session_keep_id = sorted(visible)[0]`'s bare id | **KILLED exactly** (1/1: `test_scope_is_THE_session_keep_across_two_sessions`) |
| WB5 | refusal `"invalid input"` | both identity + role raises | **KILLED exactly** (30/30: 26 hostile × field + 4 blank-role) |
| WB8 | refusal names the count, not the ids | same | **KILLED exactly** (1/1: R-Q5-1) |
| WB9 | refusal never states the count | same | **KILLED exactly** (1/1: R-Q5-1) |
| WB10 | stamp owners FIRST, then `!= operator` precondition refuses | same | **KILLED exactly** (1/1: R-Q5-1's `SELECT *` byte-inert leg) |
| WB11 | `.match` instead of `fullmatch` | the registry decides with `AGENT_NAME_PATTERN.match` instead of `is_legal_identifier` | **KILLED exactly** (4/4: `[fixer-b\n-name]`, `[fixer-b\n-session]` + both `…_SHARED_is_legal_identifier` legs) |
| WB12 | session scope stamped only for the keeper | `session_keep_id` only when `kept_by_me` | **KILLED exactly** (1/1: joiner pin — here A3 also refuses the owner-without-keep) |
| WB12b | (new, the A3-consistent form of WB12) a joiner registers with NEITHER owner NOR keep | owner + keep both gated on `kept_by_me` | **KILLED exactly** (1/1: joiner pin asserts `owner_principal == bob`) |
| WB13 | blank-role check is a private `strip()` | same | **KILLED exactly** (1/1: `test_the_blank_role_rule_is_the_SHARED_is_blank`) |

**11/11 prior survivors killed** (WB6/WB7 were killed at r1 and r2 removed none of their killing pins — not re-run, same as the author; reason: no pin that killed them was deleted in §3's DUAL list).

### 4.2 New wrong builds against the r2 seams
| id | seam | the door | 18-file contract result | kill-pin pair (`test_adv_r2_killpins.py`) |
|---|---|---|---|---|
| **N1** | A4 decision | `_validate_comms_charset` → `is_legal_identifier`; `_is_comms_charset_legal` (SKIP policy) keeps `AGENT_NAME_PATTERN.fullmatch` | **SURVIVES — 2521 passed, 0 red** | KP-N1: ref GREEN · N1 RED |
| N1b | A4 decision | as N1, the skip predicate drifts to `.match` | SURVIVES the 18 files (2521/0) — **but caught outside them** by `test_anchored_pattern_seam.py` (`2 failed, 23 passed`); withdrawn | KP-N1 RED |
| **N1c** | A4 decision | as N1, the skip predicate is a private DRIFTED `re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,63}", …)` — `fixer.b` is legal to the skip gate today (probe: `True` vs ref `False`) | **SURVIVES — 2521/0**; anchored scan also green (25 passed) | KP-N1 RED |
| **N2** | A3 path | XOR refusal moved inside the CREATE branch | **SURVIVES — 2521/0** | KP-N2 ×2: ref GREEN · N2 RED ×2 |
| **N3** | §6 id bound | refusal joins ALL ids (no bound) | **SURVIVES — 2521/0** | KP-N3 (25 traps): ref GREEN · N3 RED |
| **N4** | A1 resolver reach | a new `owns(agent → memory)` relation, keyword endpoints | **SURVIVES — 2521/0** over the contract; full tree `2 failed` (relation inventory only); honest form **N4h** (`enforced=True` + inventory row) → **2591/0** | KP-N4: ref GREEN · N4 RED |
| N4ctl | control for N4 | the SAME relation, positional | **KILLED exactly** (1/1: the five-set pin) — proves the pin CAN see the relation when the resolver can | — |
| **N5** | A2 "fakes mirror the writer" | the fake stamps `'WRONG'` / `'keep:WRONG'` | **SURVIVES — 2521/0** | KP-N5: ref GREEN · N5 RED |
| N6 | A3 sides | refusal only for owner-without-keep | **KILLED exactly** (1/1: `…[keep-without-owner]`) | — |
| **N10** | §2.2 re-register mint-once | a re-register heals a NONE-scope row's `scope` + `owner_agent` (not the owner) | **SURVIVES — 2521/0** | KP-N10: ref GREEN · N10 RED |

**Kill-pin receipts (verbatim tails):** on `adv2-ref`: `7 passed in 4.70s`. On N1 / N1b / N1c: `1 failed, 6 passed` — `FAILED …test_KP_N1_the_skip_policy_predicate_moves_with_the_shared_decision`. N2: `2 failed, 5 passed` — `…test_KP_N2_…[owner-only]`, `…[keep-only]`. N3: `1 failed, 6 passed` — `…test_KP_N3_…`. N4: `1 failed, 6 passed` — `…test_KP_N4_…`. N5: `1 failed, 6 passed` — `…test_KP_N5_…`. N10: `1 failed, 6 passed` — `…test_KP_N10_…`. Each wrong build reddens ONLY its own pin (a pin that fires on every build proves nothing).

## 5. FOCUS 5 — `scripts/pending_contracts.yaml` (the 52-line r2 change)
- **The entry:** `packet-63c-i-a-contract-r2` — 8 files: `test_agent_registry.py` (an `unsymboled_codes: attr-defined count 3` allowance) + 7 files with `missing_symbols: ["register.session_keep_id"]`.
- **Owner/trigger are real.** Owner = the 63c-i-a build (named, a real sub-wave); trigger = the kwarg + the two `lorerunes` symbols landing — both concrete, both observable. Ruling cited = amendment-2 §A2/A3/A4 (exists). Measured 2026-09-24.
- **At HEAD** (scratch copy of `0eed242`, production = `88205a4`'s): `pending_contract_gate.py --currency --legs typecheck,ruff` → `typecheck RED_ADJUDICATED — 13 residual(s), owned by: packet-63c-i-a-contract-r2` · `ruff GREEN` · `CURRENCY: FAIL — claimed but never run: pytest` (the author's §GATES, reproduced).
- **On the built world** (my `adv2-ref`, same command): `typecheck RED_ORPHANED — 8 residual(s)` — ALL EIGHT are `SELF-DESTRUCT: registered file '…' (bound 'packet-63c-i-a-contract-r2') produced NO mypy errors — the bound is discharged. DELETE its registry entry with the fix.` No other mypy error exists on the build. So the entry **self-destructs exactly when (and only when) it should**; it cannot linger silently past the build.
- **#461 check (would any entry self-destruct WRONGLY?):** No. #461's misfire needs a registered file that is pytest-red but mypy-clean; every file here is mypy-red at HEAD (the kwarg / attr errors), so the no-mypy-errors leg cannot fire before the build. A PARTIAL build (kwarg lands, `lorerunes` symbols do not) fires the self-destruct for the 7 kwarg files only — correct behaviour (those claims ARE discharged), and the attr-defined allowance is count-pinned (3), so a changed count also self-destructs. The `7 UNCHECKED (owner not importable)` the author reports concerns only the symbol-liveness leg; the no-errors leg above covers the same files, so it is not a gap.
- **Verdict: sound.** One process note, not a defect: the builder must delete the entry in the build commit (the author's §SAT says so); currency will force it.

## 6. MISSING PINS — each: the test that should exist · the defect it catches · the wrong build that passes · its receipt
All receipts measured 2026-09-24 on scratch lanes built from `88205a4` tests + my `adv2-ref` (§2). "2521/0" = the 17 r2 test files + `test_comms_wiring.py`, `pytest -n 12`, **`2521 passed`** with zero failed/errors (the lane driver's junit diff, §A.3). Each kill-pin is in `test_adv_r2_killpins.py` (§A.4): on `adv2-ref` **`7 passed in 4.70s`**; on each wrong build exactly its own pin(s) FAILED and the other 6 passed (§4 table, "KP pair").

**MP-A — BLOCKER (A4 · ROUTING IS NOT SHARING, measured N-th time).**
- *Test that should exist:* the decision-mutation pin's consumer set must include EVERY server policy that reads the identity decision — at minimum `AppContext._is_comms_charset_legal` (read by `_comms_traffic_line`'s SKIP gate, Ruling 5.2) beside `_validate_comms_charset` and `register`. Receipt shape: KP-N1 — perturb `lorerunes.is_legal_identifier` (identity sweep) to reject `fixer-b` → `AppContext._is_comms_charset_legal("fixer-b") is False`. Stronger, derived form (recommended): an AST pin that NO workspace module outside `lorerunes/identifiers` calls a method on `AGENT_NAME_PATTERN` other than reading `.pattern` (allowlist the safe: `.pattern` for prose), plus the mutation pin parametrised over both server predicates.
- *Defect:* two deciders for one policy. `_is_comms_charset_legal`'s own docstring says TWO policies read it "which is exactly why the question has one home"; A4 lists `_validate_comms_charset` as the consumer and never names `_is_comms_charset_legal`, so the LITERAL reading of A4 produces N1.
- *Wrong builds that pass:* **N1** (`_validate_comms_charset` calls `is_legal_identifier`; `_is_comms_charset_legal` keeps `AGENT_NAME_PATTERN.fullmatch`) → **2521/0**, identical behaviour today, divergence latent on the next rule change. **N1c** (the skip predicate is a private drifted `re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,63}", …)`) → **2521/0**, and behaviourally different TODAY: probe `_is_comms_charset_legal("fixer.b")` → `True` on N1c, `False` on ref; the repo-wide `test_anchored_pattern_seam.py` stays green (25 passed). (N1b — the same with `.match` — is caught outside the contract by `test_anchored_pattern_seam.py`: 2 failed; withdrawn as a survivor.)
- *KP pair:* KP-N1 GREEN on ref; RED on N1, N1b, N1c (`1 failed, 6 passed` each).

**MP-D — BLOCKER (P1c: a guard whose reach is a hidden constant; A1's own seventh-defeat shape, one level down).**
- *Test that should exist:* every `_define_relation_table` call in the REAL `surreal_schema` resolves all three of its endpoint arguments (fail CLOSED on any unresolved endpoint; anti-vacuity: ≥1 call found). Receipt shape: KP-N4. Equivalent: make `_governed_relation_tables` RAISE on an unresolved endpoint instead of skipping, and extend the synthetic reach pin with a keyword-spelled and an `Attribute`-spelled endpoint that must either join or raise.
- *Defect:* a new relation over a governed table silently never joins the population, so it gets no F5 case and the "SURPRISE population reds" adjudication point never fires. r1's resolver saw one spelling, r2's sees two; the next spelling recedes again.
- *Wrong build that passes:* **N4** — `statements.append(_define_relation_table(OWNS_RELATION, in_table=AGENT_TABLE, out_table=MEMORY_TABLE))` appended to the `briefed` DDL slice (+ `OWNS_RELATION = "owns"`) → **2521/0**. *Control:* **N4ctl** — the SAME relation spelled positionally → **KILLED exactly** by `test_the_derived_population_set_grows_to_memory_message_to` (1 red, declared 1).
- *KP pair:* KP-N4 GREEN on ref (all real calls resolve), RED on N4.
- *Over the FULL tree* (alone, `-n 12`): N4 → `2 failed, 11290 passed` — caught only by `test_enforced_relations.py` (`…is_ENFORCED` and `…EXACTLY_the_six_known_edges`), the RELATION inventory, not the governed-population pin. That inventory is a forcing function the adding engineer satisfies as a matter of course, so I ran the honest form **N4h**: `enforced=True` + the new `"owns": (AGENT_TABLE, "memory")` row in `KNOWN_RELATION_EDGES` → 18 contract files + `test_enforced_relations.py`: **`2591 passed`**, 0 red. In that tree `every_emitted_relation_table()["owns"]` carries `DEFINE TABLE OVERWRITE owns TYPE RELATION IN agent OUT memory ENFORCED SCHEMAFULL` while `governed_populations()` = `['agent','briefed','memory','message','to']` — **no `owns`**. (Full tree for N4h is INFERRED green by composition: N4's only 2 full-tree reds are the two pins N4h satisfies.)
- *Recommended fix (one source of truth, P1c Q5):* the tree ALREADY derives relation endpoints spelling-proof from the emitted DDL (`_enforced_relations_scaffold.every_emitted_relation_table()`). `_governed_relation_tables` re-derives the same fact from SOURCE SPELLING — two derivations of one fact, free to disagree, and N4h is the disagreement. Derive the relation leg from the emitted DDL (`IN <t> OUT <t>`), and pin `{edge : its IN or OUT ∈ governed nodes} ⊆ governed_populations()` over `KNOWN_RELATION_EDGES`.

**MP-B — A3's rider ("raised BEFORE `_select_row`") is pinned only on the CREATE path.**
- *Test that should exist:* after a consistent first register, a RE-register of the same agent with each mixed pair raises `AgentRegistryError` and leaves the row byte-identical (`SELECT *`). Receipt shape: KP-N2 (×2 params).
- *Defect:* a server-side caller bug on the re-register path is silently absorbed; A3's ∀-writers safety claim is derived on the first-register door only (THE QUANTIFIER LAW's askable form).
- *Wrong build that passes:* **N2** — the XOR check moved inside `if existing_row is None:` → **2521/0**.
- *KP pair:* KP-N2 GREEN on ref; RED ×2 on N2. *Control:* N6 (one-sided check, `owner and not keep`) → KILLED exactly by `…refused_before_any_store_io[keep-without-owner]` — the existing pins do discriminate the XOR's two SIDES, just not its PATH.

**MP-C — P2 small-N: the ruled id BOUND (§6: "naming the count and the rows (ids, bounded)") is invisible at 2 trap rows.**
- *Test that should exist:* R-Q5-1 over MORE trap rows than any sane bound (KP-N3 uses 25): the reason names the count (`25 … rows`), names ≥1 id, names FEWER than all ids; byte-inert.
- *Defect:* an operator-facing refusal that inlines every offending id — unbounded served text on a large store; and the current pin's "every trap id named" is satisfiable only because 2 < cap — at N > cap it would RED a correct bounded build (the pin and the ruling disagree above the cap; arithmetic-alignment class).
- *Wrong build that passes:* **N3** — `', '.join(owned_unscoped_ids)` (no `[:10]`) → **2521/0**.
- *Perturbation pair (P2):* KP-N3 (the R-Q5-1 fixture perturbed 2 → 25 traps) GREEN on the correct bounded ref, RED on N3.

**MP-E — P5: the fake's "mirrors the WRITER" stamps cannot fail.**
- *Test that should exist:* a fake-parity pin — `FakeAgentRegistry.register(…, owner_principal_id=X, session_keep_id=K)` stamps `db.scopes[id] == keep_scope(K)` and `db.owner_agents[id] == id` (KP-N5); better, one parametrised matrix driven through BOTH the real registry and the fake (consistent/mixed pairs, hostile name, blank role) comparing outcome class + stamps — which also settles the author's fork F-2 by measurement.
- *Defect:* A2's "fakes mirror the writer" clause is satisfied by a signature-equality PROXY; the fake's behaviour can drift silently. No test reads `db.scopes`/`db.owner_agents` (awk: only the fake's own writes at `_comms_fakes.py` lines 186/306/307).
- *Wrong build that passes:* **N5** — the fake stamps `'WRONG'` / `'keep:WRONG'` → **2521/0**. KP-N5 RED on N5, GREEN on ref.

**MP-G — instrument defect (P0/P1c): `patch_shared_object_everywhere` keys on NAME ∧ identity, so it false-REDs a correct build and its pins' messages then lie.**
- *Fix that should exist:* key the sweep on identity alone (`for name, value in vars(module).items(): if value is original: patch`), and have each caller assert the module it expects moved; add a self-test with an aliased binding.
- *Receipt:* on `adv2-ref` with ONLY `from lorerunes import keep_scope as _format_keep_scope` (and its one use) changed — a correct build, still calling the ONE formatter — `TestTheRegistryProvenanceSeam63cIA` → `1 failed, 5 passed`: `the stamped scope did NOT move when the SHARED keep_scope formatter was perturbed — the registry formats the scope with a PRIVATE copy (A2: ONE formatter). got [{'scope': 'keep:kpmut'}]`. The same exposure holds for the `is_legal_identifier` / `is_blank` / `AGENT_NAME_PATTERN` pins (same helper; C-leg).

**MP-F — ruling §2.2's re-register row ("`owner_principal` untouched (mint-once) · `owner_agent` untouched · `scope` untouched") is pinned only for a row the FIRST register stamped.**
- *Test that should exist:* register an agent with the α pair `(None, None)` (an ownerless row, scope NONE — exactly the pre-cutover / tokenless population), then RE-register it with a consistent credentialed pair; its `owner_principal`/`owner_agent`/`scope` read back byte-identical (KP-N10). Also worth one line: the same over a `seed_agent_legacy` row.
- *Defect:* a re-register that "heals" a NONE-scope row writes `scope` (+ `owner_agent`) and NOT `owner_principal` — the REVERSE half-pair (scope without owner) that A3 made unreachable at CREATE. The migrate's `WHERE scope IS NONE` then skips that row FOREVER, so it never gets an owner. Production path: pkt-65 deploys the image, a legacy agent re-registers with a credential BEFORE `migrate-governed` runs.
- *Wrong build that passes:* **N10** — in the re-register branch, `if existing_row.get("scope") is None and session_keep_id is not None: UPDATE … SET scope = $heal_scope, owner_agent = <self>` → **2521/0**. KP-N10 RED on N10, GREEN on ref.
- The existing `test_re_register_does_not_restamp_the_governed_triple_mint_once` is the ∀ written over "rows stamped at CREATE" — the guarded door; the unguarded door is an unstamped row.

## 7. P1b — QUANTIFIER TABLE (r2's invariants; r1's I1–I18 carried where unchanged, receipts in `b46d3f2` §4)
Each "guarded" row carries a receipt: a surviving door-build, or the door-build and the pin that killed it. WB/N ids → §4/§6; instruments §A.

| # | invariant (ruling §) | pinned as | class · receipt |
|---|---|---|---|
| I3 | the governed columns + indexes come ONLY from the shared emitter (W1-1) | ∀ governed column/index under a REWRITE+RENAME of the shared emitter | **∀ — SAFE.** WB1 (filter/dedupe twin) KILLED exactly by the rewrite pin (§4). |
| I4 | register stamps scope = THE session keep ∀ sessions, ∀ registrants (A2) | two sessions; keeper + householded joiner + keeper's later agent | **∀ over the two door classes — SAFE.** WB4 (`sorted(visible)[0]`) KILLED; WB12 (keeper-only) KILLED (by the joiner pin and, under A3, by construction); WB12b (joiner ownerless) — §4. |
| I4b | the scope is formed by the ONE formatter `keep_scope` (A2) | identity-sweep mutation of `keep_scope` | **SAFE for private copies** (the author's WB-A2a); **but the instrument false-REDs a CORRECT aliased import** — MP-G (§6). |
| I7 | the backfill touches ONLY NONE-scope rows (∀ scoped rows untouched) | mixed store: 2 governed + 3 legacy, byte-identical read-back | **∀ — SAFE.** WB2 KILLED exactly (mixed + exempt token + TestMigrateAgentOwner). |
| I8 | refuse iff ∃ row (scope NONE ∧ owner NOT NONE) | trap store refuses; mixed store does NOT refuse | **∀ — SAFE.** WB3 KILLED exactly. |
| I9 | a refused migrate writes NOTHING | full `SELECT *` before == after | **∀ — SAFE (effect, not proxy).** WB10 KILLED exactly. |
| I10 | the refusal names the count AND the rows, **bounded** (§6 line 577: "naming the count and the rows (ids, bounded)") | count-beside-noun + every id, over **2** traps | **GUARDED by fixture size — MISSING.** WB8/WB9 KILLED; **N3 (unbounded id list) SURVIVES 2521/0.** The "every id named" assertion is satisfiable only because 2 < any cap; at N > cap it CONTRADICTS the ruled bound. MP-C. |
| I15 | the MOVE refuses ∀ hostile identifiers (shared corpus) | 13 shapes × 2 fields | **∀ — SAFE.** WB11 (`.match`) KILLED exactly (2 newline + 2 decision-mutation pins). |
| I16 | the MOVE refusal teaches (field · rule · remedy · fenced value) | per field, per shape | **∀ — SAFE.** WB5 (`"invalid input"`) — §4. |
| I17a | the identity DECISION is `lorerunes.is_legal_identifier` for EVERY consumer (A4, ONE IMPLEMENTATION) | decision mutation observed at `register` + `_validate_comms_charset` only | **GUARDED by a hand-list of two consumers — MISSING.** The server's SECOND policy over the same decision (`_is_comms_charset_legal`, read by `_comms_traffic_line`'s SKIP gate) is observed by no pin: **N1 (private `fullmatch` on the shared pattern) and N1c (private DRIFTED regex — admits `fixer.b` TODAY) both SURVIVE 2521/0.** MP-A. |
| I17b | the blank-role rule is `lorerunes.is_blank` | identity-sweep mutation | **SAFE.** WB13 — §4. |
| A3 | `register` refuses an inconsistent provenance pair, BEFORE `_select_row`, ∀ calls | the two mixed pairs on an EMPTY store (first register) + both consistent pairs | **GUARDED by the create path — MISSING.** N6 (one-sided check) KILLED exactly; **N2 (XOR inside the CREATE branch only) SURVIVES 2521/0** — a mixed-pair RE-register is silently accepted. MP-B. |
| MINT | re-register is mint-once ∀ rows (§2.2 row 2) | only for a row the FIRST register stamped | **GUARDED by "the row was stamped at create"** — N10 (a re-register HEALS an ownerless row's scope → scope-without-owner) — §4/§6 MP-F. |
| E2 | `touch` re-validates the whole row (heartbeat control) | frozen-DDL touch → `SurrealStoreError`, byte-identical | **∀ — SAFE by construction** (store-ref §1.4; the author's F-4: no MERGE-skips-validation build exists; I agree — not re-attempted). |
| LegB | the backfill stamps all 3 columns on the DIRTY population, idempotently | `owner_agent` read-back per violator + second run `backfilled == 0` | **∀ — SAFE** (a 2-of-3 stamp is unrepresentable under the ruled ONE statement; the exempt-token pin also demands all three `SET`s). |

## 8. P1c — REACH TABLE (every instrument r2 introduces, modifies, or leans on)
Axes: **reach** DERIVED vs name/prefix/hand-list · **coverage** a checked variable (fails closed) vs not · **effect** vs proxy · **one source** proven by mutation. Leg: E = empirical (wrong build + kill-pin pair in scratch), C = construction-inspection.

| instrument | reach | coverage checked? | effect/proxy | one-source by mutation | verdict · leg |
|---|---|---|---|---|---|
| `governed_populations()` relation leg (`_governed_relation_tables` + r2's `_schema_string_constants` ImportFrom leg) | the CALL set is AST-derived (`call_name == _define_relation_table`), but endpoint RESOLUTION is a hand-list of SPELLINGS: `Constant`, `Name`→(`Assign` \| r2 `ImportFrom`). Every other spelling — keyword endpoints (`len(call.args) < 3: continue`), `lorerunes.AGENT_TABLE` (`Attribute`), an annotated `X: Final = "t"` (`AnnAssign`), a relative import (`level != 0`), an import that fails (`except ImportError: continue`) — resolves to `None` and the relation **silently never joins** | **NO** — nothing reds when a call's endpoint is unresolved; the exact-set pin only sees what the resolver can see | effect for resolvable spellings | n/a (test substrate) | **MISSING PIN — MP-D · E.** N4 (a new `owns` relation over `AGENT_TABLE`, keyword endpoints) → **2521 passed / 0 failed**; N4ctl (the SAME relation, positional) → **KILLED exactly** by the five-set pin. Same relation, same endpoints, opposite verdicts: the reach is a spelling, not a checked variable. r1 resolved 1 spelling, r2 resolves 2 — *the reach is receding one level per round*; the fail-closed pin (KP-N4) ends the recession. Same fail-open class, C-leg only: the NODE leg keys on a function NAMED `_<t>_statements` directly calling `_governed_field_specs` — a governed slice built in a differently-named helper does not join. |
| `patch_shared_object_everywhere` (new shared test instrument; 5 pins + the footer pin) | modules in `sys.modules` whose attribute NAMED `<attribute>` IS the object — keyed on NAME ∧ identity | NO (asserts only that ≥1 module / the `lorerunes` home was patched) | effect (the pins observe behaviour moving) | it is copy #2 of `test_secret_typing._patch_everywhere` (author's F-3) | **MISSING PIN (instrument defect) — MP-G · E.** A CORRECT build that imports the shared formatter under an alias (`from lorerunes import keep_scope as _format_keep_scope`) is **RED** on `test_the_scope_is_formed_by_the_SHARED_keep_scope_formatter` with the lying message *"the registry formats the scope with a PRIVATE copy"* (got `keep:kpmut` — the real formatter's output, because the alias was never patched). Fix: key on identity ALONE (`for name, value in vars(module).items(): if value is original`). |
| `test_the_identifier_decision_is_the_SHARED_is_legal_identifier` (A4 decision-mutation pin) | a HAND-LIST of two consumers: `register`, `AppContext._validate_comms_charset` | NO | effect | proves sharing for those two only | **MISSING PIN — MP-A · E.** The server's second policy over the same decision (`_is_comms_charset_legal` → `_comms_traffic_line` SKIP gate) is not in the list: N1 and N1c survive 2521/0; KP-N1 kills both. The ruling's consumer list (A4) is itself the hand-list — see §9 fork. |
| regex-twin identity pin (retargeted) | identity sweep of `AGENT_NAME_PATTERN` + `agents.X is lorerunes.X` | per field | effect | yes (WB-A4b drifted copy, author §MUT) | SAFE for its purpose (register) · C (+ author's E) |
| footer `…moves_EVERY_members_refusal` (retargeted) | `LINK0_MEMBERS = ("lore_comms", *DISPATCHERS)` (pre-existing) | yes (survivors list) | effect | pattern object only — see MP-A | SAFE for the REFUSE policy; blind to the SKIP policy · C |
| exact-signature allowlist pin | `inspect.signature(AgentRegistry.register)` — derived | exact equality | structure (appropriate) | n/a | SAFE · C |
| wire-disjointness pin | DERIVED: `_COMMS_ACTIONS['register'].params` ∪ `AppContext.comms` params; anti-vacuity on the action set | yes | structure | n/a | SAFE · C (bound: the served MCP tool signature is not in the union; it funnels through `comms`) |
| fake-mirror pin (`FakeAgentRegistry.register` signature == real) | derived signature lists | equality | **PROXY for "the fake mirrors the WRITER"**: the fake's stamps (`db.owner_agents`/`db.scopes`) are read by NO test | n/a | **MISSING PIN — MP-E (P5) · E.** N5 (fake stamps `'WRONG'` / `'keep:WRONG'`) → 2521/0; KP-N5 kills it. |
| exempt-token observed-run pin | `observe_governed_table_writes("agent")` (pre-existing F5 observer) filtered by token name + origin | anti-vacuity (`migrate_writes` non-empty) | effect (executed statement == token statement) | n/a | SAFE · E (WB2 reds it, §4) |
| R-Q5-1 byte-inert + mixed-store pins | full `SELECT *` / governed rows by id | anti-vacuity (`governed_before` == 2; refusal asserted) | **effect** (r1's proxy fixed) | n/a | SAFE · E (WB2/WB3/WB10 killed) — but the id-bound is fixture-blind (MP-C, §7 I10) |
| `_assert_no_violable_constraint` (lifted ∀ body) + hazard-content pin | derived over each spec's OWN emitter; floor non-vacuity | yes | effect (DDL text) + served prose | r1 M1/M2 | SAFE · C |
| `pending_contracts.yaml` / `pending_contract_gate.py` (relied on) | derived from the live mypy transcript | yes (self-destruct both directions) | effect | n/a | SAFE · E (§5, both worlds run) |
| `test_anchored_pattern_seam.py` (relied on; OUTSIDE the 18 contract files) | AST over the workspace members, `$`-anchored patterns validated with `.match` | — | effect | — | catches N1b (`.match` drift: 2 failed) and WB11; **blind to N1c** (a drifted pattern under `fullmatch`) — by design, not a defect of that scan · E |

## 9. P-PKG — my table, then the diff
⚠ Honesty on order: I read the author's SUMMARY BLOCK (which carries its one-line `Packages considered: none — …`) before building this table; I built the rows below from the contract and the production source, and only then read their §DRY. The row content is mine.

| mechanism the r2 contract specifies / introduces | candidates | what I READ | verdict |
|---|---|---|---|
| the identity DECISION (`lorerunes.is_legal_identifier`) | stdlib `re.fullmatch`; pydantic `StringConstraints(pattern=)` | the installed `AGENT_NAME_PATTERN` (`agents.py`) + `_is_comms_charset_legal`'s docstring (#210: `fullmatch`, not `match`); prior adversary's pydantic reading (b46d3f2 §8: a second spelling under pydantic-core's regex) | **replace → in-house shared home** (stdlib `re`, one pattern object) — no package does "our charset" |
| the scope formatter | `lorerunes.pdp.keep_scope` (in-house) | `lorerunes/__init__.py` re-exports `keep_scope` from `pdp` | **REUSE** |
| blankness | `lorerunes.is_blank` | `lorerunes/__init__.py` (`from lorerunes.blankness import is_blank`) | **REUSE** |
| the provenance-pair refusal (A3) | none applicable (a 3-line XOR) | — | n/a |
| `patch_shared_object_everywhere` (test instrument) | `unittest.mock.patch`, `pytest.MonkeyPatch.setattr` | installed signatures, read live: `unittest.mock.patch(target, new=sentinel.DEFAULT, …)` with `_get_target` doing `target.rsplit('.', 1)` → ONE dotted target; `MonkeyPatch.setattr(self, target, name, value=<notset>, raising=True)` → ONE target | **bespoke sweep over `monkeypatch.setattr`** — justified (no package patches every binding of an object). BUT it is copy #2 of `test_secret_typing._patch_everywhere` (the author's F-3) and it has MP-G's name-keyed reach defect |
| resolver ImportFrom leg | stdlib `importlib` / `ast` | `_governed_contract._schema_string_constants` | in-house; its REACH is the defect (MP-D), not the library choice |

**Diff vs the author's:** none on production mechanisms (both: no package fits; all in-house `lorerunes` reuse + stdlib). On test instruments we agree the sweep is bespoke and a DRY copy (F-3); I add MP-G. No `bespoke` verdict above rests on an unread API.

## 10. P-PORT
`Odoo-20 portability: n/a — no Odoo seam touched` (this is the lore repo; the contract pins no Odoo model/field/view/ACL/ORM path). Author's line matches.

## 11. P6 — corpse sweep (awk, bare patterns, over `git ls-files` tests + production + docs)
Patterns: `_MOVE_HOSTILE_IDENTIFIERS`, `test_register_exposes_no_display_owner_argument`, `test_the_derived_population_set_is_the_known_set`, `TestAgentRoleNonEmptyAssert`, `test_register_charset_check_is_the_ONE_spelling`, and every `AGENT_NAME_PATTERN` / `_IDENTIFIER_CHARSET_PATTERN` line co-occurring with `setattr|patch`. Every hit, individually:
- `docs/design/2026-09-24-packet63c-amendment-2.md:61,132,174` — the spec naming the pins it retires · **OK (spec)**.
- `loremaster/tests/test_agent_capability.py:890` — DUAL comment · **OK**.
- `loremaster/tests/test_comms_schema.py:869` — DUAL comment · **OK**.
- `loremaster/tests/test_memory_enforcement_63b_ia.py:1152` — DUAL comment · **OK**.
- `loremaster/tests/test_message_enforcement_63b_ii_a.py:14-15` — module docstring history citing the deleted ia pin, annotated by the r2 line after it · **OK (dated history)**.
- `loremaster/tests/test_agent_registry.py:1211,1236,1239` — the retargeted regex-twin pin (identity sweep) · **OK**.
- `loremaster/tests/test_comms_footer.py:2037,2039` — the retargeted footer pin · **OK** (MP-A notes its reach).
- No surviving single-module `setattr(<agents|server>, "AGENT_NAME_PATTERN", …)` site anywhere in the tests → **no corpse pin patching a re-export**.
- **Production prose that the i-a BUILD will falsify (not contract-pinnable here; owned by the i-a builder, named so the cold audit does not rediscover it):** `agents.py` comment above `AGENT_NAME_PATTERN` ("enforced here … AND by the store's own ``ASSERT`` (defense-in-depth, surreal_schema)") — FALSE after Q3 drops the ASSERT; `server.py::_is_comms_charset_legal` docstring ("Both now move with ONE edit, which ``test_perturbing_the_SHARED_predicate_moves_EVERY_members_refusal`` proves by mutation") — after A4 that pin patches the pattern object, not the decision; the claim needs KP-N1 (MP-A) to be true.

## 12. Residuals (each with an individual verdict)
- **R-1 — lore MCP down after a production store restart (escalation, not a contract defect).** `lore-surreal.service` shows `Active: active (running) since Thu 2026-09-24 15:19:56 EDT` (a restart by someone else during my run; I never touched `:18500` or systemctl). Since then EVERY lore MCP call fails: `lore_comms heartbeat` ×2 and `lore_findings report` ×1 → `SurrealDB … query failed against 'ws://127.0.0.1:18500/rpc': no close frame received or sent`. `lore-lore` shows `Up 7 hours`, i.e. it was NOT recreated and its pooled connections did not recover. **Could not file it** (the ledger is behind the same connection) — **the lead must file it** (category bug, area store connection lifecycle). It also blocks my ledger pointer on thread `63c` (§13).
- R-2 — the author's `§ITEMS` row 8 says the fake "mirrors A3"; true (the XOR raise is real and reachable), but the stamps are decoration — MP-E.
- R-3 — `registry_level_session_keep_id` is a synthetic id the registry never validates as a real keep: correct for the capability harnesses (they never assert scope) · **OK**, noted so no future pin asserts scope on those harnesses.
- R-4 — uppercase appears in the shared corpus only at position 0 (`"Fixer-B"`) · **covered**: the pattern TEXT itself is pinned at `test_agent_registry.py:896` (`AGENT_NAME_PATTERN.pattern == r"^[a-z0-9][a-z0-9_-]{0,63}$"`) and `test_anchored_pattern_seam.py:333`, so a widened tail class cannot slip in. (Supersedes my §3 D4 "R-C1" note.)
- R-5 — R9 carried from amendment-2: "before any store I/O" is observed as a row count; a refuse-after-write-then-DELETE build is invisible by design · **accepted bound** (ruled), not re-litigated.
- R-6 — the exempt-token pin fixes the statement's TEXT shape (`startswith "UPDATE AGENT "`, `endswith "WHERE SCOPE IS NONE"`, `"<col> ="`); a correct build writing `WHERE scope IS NONE;` or `SET scope=$scope` fails it · **form constraint, low**; my reference satisfies it. Recommend normalising (strip a trailing `;`, collapse `\s*=\s*`) rather than widening.
- R-7 — the WB2/WB3 extra red (`TestResolveOperatorPrincipalIsLifted::test_the_operator_resolution_is_shared_by_mutation`) was not in my declaration; both builds are killed regardless · **my misprediction, recorded**.
- R-8 — the author's F-4. **(a)** no MERGE-skips-validation `touch` exists · agree (store-ref §1.4; amendment-3 E2-bis(2) concurs). **(b)** "Leg B's 2-of-3 stamp is unrepresentable" — **I first conceded this without building it; that was wrong** (amendment-3 F-4(b), landed at `e6bedd1` during my run, is right: a COLUMN-wise 2-of-3 is one statement). Built it as amendment-3 §A item 1 asks, through `scripts/mutation_proof.py` on `adv2-ref` (provenance `…/scratchpad/ref/loremaster/loremaster/__init__.py`): anchor `"owner_agent = id, scope = $scope WHERE scope IS NONE"` → `"scope = $scope WHERE scope IS NONE"` in `principals.py`; declared from `collected.txt` BEFORE the run = {`TestAgentMigrateScopeKeyed63cIA::test_R_Q5_3_every_migrated_row_reads_back_the_three_column_stamp`, `…::test_the_migrate_exempt_token_carries_the_EXECUTED_three_column_statement`, `TestTheRealAgentMigrateSurvivesLegacyViolators63cIA::test_the_real_migrate_survives_the_legacy_violators_all_stamped`}; run = the 18 files, `-n 12` → `3 failed, 2518 passed` · `tree restored byte-exact (… md5 5e02e1ce17aeb2d8ae4aba127e7a870a)` · **`PROOF HELD — the declared RED set fired EXACTLY`**, exit 0. **So amendment-3 §A item 1 resolves as a RECEIPT: no missing pin; it is not gating.**
- R-9 — N1b is killed only by a pin OUTSIDE the 18 contract files (`test_anchored_pattern_seam.py`) · **OK** — the tree catches it; noted so nobody deletes that scan believing the contract covers `.match`.
- R-10 — re-register of a legacy HOSTILE-named row: after the MOVE, `register` refuses the hostile name before `_select_row`, so a legacy violator can never re-register (it can still heartbeat via `touch`). Two readings: (a) intended — the MOVE is ∀ calls; (b) DD-3.c's "legacy violators survive ∀ writers" wants re-register too. The ruling does not say · **spec-silent → fork for the sidecar**; I would pick (a).

## 13. ORPHANED riders · open forks F-1/F-2/F-3 · new forks
- **ORPHANED — A4's "mutation of `lorerunes.is_legal_identifier` reds … every consumer" rider over the SKIP policy.** A4 enumerates the consumers per wave: i-a → `_validate_comms_charset`, `AgentRegistry.register`; ii → `BriefLedger.publish`. `AppContext._is_comms_charset_legal` (read by `_comms_traffic_line`, Ruling 5.2's charset gate) is in NO sub-wave's list, yet it is the existing ONE decision the A4 move lifts. Neither i-a, i-b nor ii owns pinning it → **ORPHANED** (MP-A is the pin; my recommendation: i-a owns it — it is the wave that moves the decision).
- **F-1 (E2 control applies the current emitter before the frozen DDL):** reading (b) is sound (the refusing ASSERT is the frozen one on every build; my reference passes the control). **No verdict impact.**
- **F-2 (does the fake mirror `is_blank`/`is_legal_identifier`?):** whichever way it is ruled, MP-E stands — the fake's EXISTING mirror (the stamps) is unobserved. A "yes" ruling should arrive with the parity matrix MP-E recommends (it then measures F-2 instead of asserting it). **Does not change INSUFFICIENT.**
- **F-3 (fold `test_secret_typing._patch_everywhere` onto `patch_shared_object_everywhere`):** recommend YES, and fold AFTER MP-G's identity-keyed fix — otherwise the fold propagates the alias blind spot into a sixth caller. **No verdict impact.**
- **New fork NF-1 (from MP-A):** does A4's consumer set include `_is_comms_charset_legal`? The literal A4 text lists only `_validate_comms_charset`, so N1 IS a literal-reading build. My reading: yes — `_is_comms_charset_legal` must itself call `is_legal_identifier` (my reference does exactly that and is 2521/0), keeping the refuse and skip policies on one decision, as its own docstring demands.
- **New fork NF-2 (R-10):** may a legacy hostile-named agent re-register after the MOVE? Spec-silent; I would pick "no" (the MOVE is ∀ calls).


## 14. Amendment 3 (`e6bedd1`, landed mid-run) — how its rulings meet this verdict
- **F-1 / E2-bis, F-5:** prose-only; consistent with my §7/§8 rows. No verdict impact.
- **F-4(b) (item 1, the only GATING-iff item):** built and held — §12 R-8. **Not gating.**
- **F-2 (fake mirrors `is_blank` + `is_legal_identifier`, mirror pin, THIRD consumer leg on the two shared-decision pins):** adopts part of MP-E's parity direction for the REFUSALS. It does **not** close MP-E's stamp leg (`db.scopes`/`db.owner_agents` still unread — N5 still passes) and it does **not** close MP-A: its "third consumer" is the FAKE; the server's SKIP-policy consumer (`_is_comms_charset_legal` → `_comms_traffic_line`) is still in no consumer list. **MP-A remains ORPHANED after amendment 3.**
- **F-3 (fold three `_patch_everywhere` copies onto the "identity-keyed" shared instrument):** the premise is half-true. `patch_shared_object_everywhere` is keyed on NAME **and** identity (`getattr(module, attribute, None) is not original → skip`), so it patches only bindings that carry the SAME NAME as the object. Amendment 3 correctly names the name-keyed copies' false-CLEAR; the shared instrument has the mirror-image false-RED (MP-G, measured: a correct aliased import is RED with a message accusing a private copy). **Recommendation: fix MP-G (identity-alone sweep over `vars(module)`) BEFORE the fold**, or the fold moves three more suites onto an instrument with an unmeasured reach. The STOP-rule's "never widen the shared instrument back to names" is correct; this is the opposite direction, widening from name ∧ identity to identity alone.
- **Net:** amendment 3 settles none of MP-A, MP-B, MP-C, MP-D, MP-F or MP-G, and settles part of MP-E. **The verdict does not change.**

## A. Instruments (pasted VERBATIM — scratch-only; my writable set is this report)

Scratch root for every path below: `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/dc888a1c-9807-4fec-be48-0a1fc30a29b1/scratchpad`. Lanes `ref`, `red`, `wb`, `wb3`, `wb4` were each made by `./scripts/scratch_copy.sh` (provenance asserted by the tool), then `my_ref_build.py` + deletion of `agents.py`'s now-unused `import re` (ruff F401), committed in the scratch copy as branch `adv2-ref`.

### A.1 `my_ref_build.py` — the independent reference build
```python
"""adversary-63c-i-a-r2 — an INDEPENDENT reference (believed-correct) 63c-i-a build.

Written from the production source + amendment-2 §A1–A4, NOT from the r2 author's ref_build_r2.py.
Base legs (Q3 drop, W1-1 routing, Q5 scope-keyed migrate + row precondition) re-use the PRIOR
adversary's §A.1 anchors (b46d3f2 — a different author than the contract under grade); the A2/A3/A4
legs are my own.

Usage: uv run --no-project python my_ref_build.py <scratch-root>
Each edit asserts its anchor occurs exactly once (a silent no-op edit is a failed setup — #194).
"""

import sys
from pathlib import Path

ROOT = Path(sys.argv[1])


def edit(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{rel}: anchor occurs {count} times: {old[:80]!r}"
    path.write_text(text.replace(old, new))


def create(rel: str, body: str) -> None:
    path = ROOT / rel
    assert not path.exists(), f"{rel} already exists"
    path.write_text(body)


SCHEMA = "loremaster/loremaster/store/surreal_schema.py"
AGENTS = "loremaster/loremaster/agents.py"
SERVER = "loremaster/loremaster/server.py"
PRINCIPALS = "loremaster/loremaster/principals.py"
RUNES_INIT = "lorerunes/lorerunes/__init__.py"

# ---- Q3: drop name/session/role ASSERTs (KEEP status) -------------------------------------------
edit(
    SCHEMA,
    '    ("name", _CHUNK_STRING_TYPE, _IDENTIFIER_CHARSET_ASSERT),\n'
    '    ("session", _CHUNK_STRING_TYPE, _IDENTIFIER_CHARSET_ASSERT),\n'
    '    ("role", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),\n    ("model"',
    '    ("name", _CHUNK_STRING_TYPE, ""),\n'
    '    ("session", _CHUNK_STRING_TYPE, ""),\n'
    '    ("role", _CHUNK_STRING_TYPE, ""),\n    ("model"',
)
# ---- W1-1: the governed triple comes only from the ONE emitter ----------------------------------
edit(SCHEMA, '    ("owner_principal", "option<record<principal>>", ""),\n    # packet 62, Fork 1', "    # packet 62, Fork 1")
edit(
    SCHEMA,
    "    statements.append(\n"
    "        _plain_index(\n"
    "            AGENT_TABLE,\n"
    '            f"{AGENT_TABLE}_owner_principal",\n'
    "            _AGENT_OWNER_PRINCIPAL_INDEX_FIELDS,\n"
    "        )\n"
    "    )\n",
    "    statements += [\n"
    "        _define_field(AGENT_TABLE, name, type_expr, constraint=constraint)\n"
    "        for name, type_expr, constraint in _governed_field_specs()\n"
    "    ]\n"
    "    statements += _governed_index_statements(AGENT_TABLE)\n",
)
edit(SCHEMA, '_AGENT_OWNER_PRINCIPAL_INDEX_FIELDS = ("owner_principal",)\n', "")

# ---- A4: the identifier DECISION + the pattern MOVE to lorerunes ---------------------------------
create(
    "lorerunes/lorerunes/identifiers.py",
    '"""The comms identity charset — ONE pattern, ONE decision (63c-i-a amendment-2 A4)."""\n\n'
    "from __future__ import annotations\n\n"
    "import re\n\n"
    'AGENT_NAME_PATTERN: re.Pattern[str] = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")\n\n\n'
    "def is_legal_identifier(value: str) -> bool:\n"
    '    """Whether ``value`` matches ``AGENT_NAME_PATTERN`` IN FULL (``fullmatch``, finding #210)."""\n'
    "    return AGENT_NAME_PATTERN.fullmatch(value) is not None\n",
)
edit(
    RUNES_INIT,
    "from lorerunes.engine_rejection import reclassify\n",
    "from lorerunes.engine_rejection import reclassify\n"
    "from lorerunes.identifiers import AGENT_NAME_PATTERN, is_legal_identifier\n",
)
edit(RUNES_INIT, "__all__ = [\n", '__all__ = [\n    "AGENT_NAME_PATTERN",\n    "is_legal_identifier",\n')
edit(
    AGENTS,
    'AGENT_NAME_PATTERN: re.Pattern[str] = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")\n',
    "AGENT_NAME_PATTERN = _RUNES_AGENT_NAME_PATTERN  # re-export (A4: the pattern lives in lorerunes)\n",
)
edit(
    AGENTS,
    "from lorerunes import parse_credential\n",
    "from lorerunes import AGENT_NAME_PATTERN as _RUNES_AGENT_NAME_PATTERN\n"
    "from lorerunes import is_blank, is_legal_identifier, keep_scope, parse_credential\n",
)
edit(AGENTS, "from loremaster.render import render_attributed\n", "from loremaster.render import render_attributed, render_fenced\n")
edit(
    SERVER,
    "        return AGENT_NAME_PATTERN.fullmatch(value) is not None\n",
    "        from lorerunes import is_legal_identifier  # noqa: PLC0415 - house lazy-import idiom\n\n"
    "        return is_legal_identifier(value)\n",
)

# ---- A4 register MOVE (teaching) + A3 XOR + A2 stamp --------------------------------------------
edit(
    AGENTS,
    "class AgentIdentityConflictError(AgentRegistryError):",
    "class InvalidAgentIdentityError(AgentRegistryError):\n"
    '    """A register argument violates the agent identity rules (63c-i-a §4.2 MOVE)."""\n\n\n'
    "class AgentIdentityConflictError(AgentRegistryError):",
)
edit(
    AGENTS,
    "        owner_principal_id: str | None = None,\n    ) -> AgentRegisterResult:",
    "        owner_principal_id: str | None = None,\n        session_keep_id: str | None = None,\n    ) -> AgentRegisterResult:",
)
edit(
    AGENTS,
    "        agent_id = self._agent_id(session, name)\n        existing_row = await self._select_row(agent_id)\n        now = datetime.now(UTC)\n",
    "        if (owner_principal_id is None) != (session_keep_id is None):\n"
    "            raise AgentRegistryError(\n"
    '                "register called with an owner but no session keep (or the reverse) — a "\n'
    '                "server-side caller bug; nothing was written"\n'
    "            )\n"
    '        for field_name, value in (("name", name), ("session", session)):\n'
    "            if not is_legal_identifier(value):\n"
    "                raise InvalidAgentIdentityError(\n"
    '                    f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern} (lowercase letters, "\n'
    "                    f\"digits, '_' or '-', 1-64 chars, starting with a letter or digit); nothing was \"\n"
    '                    f"written — register again with a legal {field_name}. The rejected value was:\\n"\n'
    '                    f"{render_fenced(value)}"\n'
    "                )\n"
    "        if is_blank(role):\n"
    "            raise InvalidAgentIdentityError(\n"
    '                "agent role must not be blank — nothing was written; register again with a role "\n'
    "                \"(e.g. 'builder')\"\n"
    "            )\n"
    "        agent_id = self._agent_id(session, name)\n        existing_row = await self._select_row(agent_id)\n        now = datetime.now(UTC)\n",
)
edit(
    AGENTS,
    "                _COL_CAPABILITY_HASH: sha512_hex(capability),\n",
    "                _COL_CAPABILITY_HASH: sha512_hex(capability),\n"
    '                "owner_agent": RecordID(AGENT_TABLE, agent_id),\n'
    '                "scope": keep_scope(session_keep_id) if session_keep_id is not None else None,\n',
)
edit(
    SERVER,
    "            cadence=cadence,\n            owner_principal_id=principal_bare,\n        )\n        now = datetime.now(UTC)\n        registered_age_s",
    "            cadence=cadence,\n            owner_principal_id=principal_bare,\n"
    "            session_keep_id=(\n"
    '                str(session_keep.id).split(":", 1)[-1] if session_keep is not None else None\n'
    "            ),\n"
    "        )\n        now = datetime.now(UTC)\n        registered_age_s",
)

# ---- Q5: scope-keyed 3-column migrate + §2.1 row precondition (prior adversary §A.1 anchors) ------
edit(
    PRINCIPALS,
    "    if table == AGENT_TABLE:\n        return await _migrate_agent_owner(store, principal_store)\n",
    "    if table == AGENT_TABLE:\n        return await _migrate_agent_owner(store, keep_store, principal_store)\n",
)
edit(
    PRINCIPALS,
    "async def _migrate_agent_owner(\n    store: StoreHandle,\n    principal_store: PrincipalStore,\n) -> MigrateGovernedResult:",
    "async def _migrate_agent_owner(\n    store: StoreHandle,\n    keep_store: KeepStore,\n    principal_store: PrincipalStore,\n) -> MigrateGovernedResult:",
)
edit(
    PRINCIPALS,
    "    from loremaster.governed import MigrateGovernedResult, governed_exempt\n\n    operator = await resolve_operator_principal(principal_store)\n",
    "    from lorerunes.pdp import keep_scope\n\n"
    "    from loremaster.governed import PROJECT_KEEP_KEY, MigrateGovernedResult, governed_exempt\n\n"
    "    operator = await resolve_operator_principal(principal_store)\n",
)
edit(
    PRINCIPALS,
    "    unmigrated = await _owner_count(store, AGENT_TABLE, none=True)\n"
    "    already = await _owner_count(store, AGENT_TABLE, none=False)\n",
    "    unmigrated = await _scope_count(store, AGENT_TABLE, none=True)\n"
    "    already = await _scope_count(store, AGENT_TABLE, none=False)\n",
)
edit(
    PRINCIPALS,
    "    operator_id = operator.id.partition(\":\")[2] or operator.id\n"
    "    backfill_statement = (\n"
    "        f\"UPDATE {AGENT_TABLE} SET owner_principal = type::record('{PRINCIPAL_TABLE}', $owner) \"\n"
    "        \"WHERE owner_principal IS NONE\"\n"
    "    )\n",
    "    owned_unscoped = await run_query(\n"
    "        acquire=store.acquire,\n"
    "        drop=store.drop,\n"
    "        url=store.url,\n"
    "        noun=\"governed agent row precondition\",\n"
    "        label=\"governed.agent_precondition.rejected\",\n"
    "        statement=(\n"
    "            f\"SELECT VALUE id FROM {AGENT_TABLE} WHERE scope IS NONE AND owner_principal IS NOT NONE\"\n"
    "        ),\n"
    "        params={},\n"
    "        logger=logger,\n"
    "    )\n"
    "    owned_unscoped_ids = [str(row) for row in (owned_unscoped or [])]\n"
    "    if owned_unscoped_ids:\n"
    "        return MigrateGovernedResult(\n"
    "            table=AGENT_TABLE,\n"
    "            scanned=unmigrated + already,\n"
    "            backfilled=0,\n"
    "            already_migrated=already,\n"
    "            refused=True,\n"
    "            reason=(\n"
    "                f\"{len(owned_unscoped_ids)} agent row(s) carry an owner but no scope \"\n"
    "                f\"({', '.join(owned_unscoped_ids[:10])}) — a multi-principal or half-applied store; \"\n"
    "                \"adjudicate these rows by hand before migrating (§2.1)\"\n"
    "            ),\n"
    "        )\n"
    "    project_keep = await keep_store.get_or_create_keyed(\n"
    "        key=PROJECT_KEEP_KEY, type=\"project\", keeper_email=operator.email, name=\"lore\"\n"
    "    )\n"
    "    project_scope = keep_scope(project_keep.id.partition(\":\")[2] or project_keep.id)\n"
    "    operator_id = operator.id.partition(\":\")[2] or operator.id\n"
    "    backfill_statement = (\n"
    "        f\"UPDATE {AGENT_TABLE} SET owner_principal = type::record('{PRINCIPAL_TABLE}', $owner), \"\n"
    "        \"owner_agent = id, scope = $scope WHERE scope IS NONE\"\n"
    "    )\n",
)
edit(
    PRINCIPALS,
    "            statement=backfill_statement,\n            params={\"owner\": operator_id},\n",
    "            statement=backfill_statement,\n            params={\"owner\": operator_id, \"scope\": project_scope},\n",
)
print("adversary-r2 reference build applied")
```

### A.2 `my_wbs.py` — wrong builds + their DECLARED expected-RED sets
```python
"""adversary-63c-i-a-r2 — wrong builds applied ON TOP of my independent reference (adv2-ref).

Usage: uv run --no-project python my_wbs.py <scratch-root> <WB-id> [--declared]
  --declared   print the DECLARED expected-RED node ids (resolved against collected.txt, which is
               `pytest --collect-only -q` output taken BEFORE any wrong-build run) and exit.
Each edit asserts its anchor occurs exactly once (a no-op mutation is a failed setup — #194).
"""

import sys
from pathlib import Path

SCR = Path("/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/dc888a1c-9807-4fec-be48-0a1fc30a29b1/scratchpad")
ROOT = Path(sys.argv[1])
WB = sys.argv[2]

SCHEMA = "loremaster/loremaster/store/surreal_schema.py"
PRINCIPALS = "loremaster/loremaster/principals.py"
SERVER = "loremaster/loremaster/server.py"
AGENTS = "loremaster/loremaster/agents.py"
FAKES = "loremaster/tests/_comms_fakes.py"

GOV = "test_agent_governance_63c_i_a.py"
REG = "test_agent_registry.py"
OWNS = "test_agent_owns_principal_schema.py"
MIG = "test_message_migrate_63b_ii_a.py"
ENF = "test_message_enforcement_63b_ii_a.py"

# DECLARED expected-RED sets — (file fragment, node fragment) rules. Written BEFORE any run.
DECLARED: dict[str, list[tuple[str, str]]] = {
    "WB1": [(OWNS, "test_every_governed_column_and_index_MOVES_with_a_REWRITE")],
    "WB2": [(GOV, "test_a_store_with_governed_and_legacy_agents_migrates_only_the_legacy"),
            (GOV, "test_the_migrate_exempt_token_carries_the_EXECUTED"),
            (MIG, "test_agent_migrate_backfills_only_none_owner_agents_to_the_operator")],
    "WB3": [(GOV, "test_a_store_with_governed_and_legacy_agents_migrates_only_the_legacy"),
            (MIG, "test_agent_migrate_backfills_only_none_owner_agents_to_the_operator")],
    "WB4": [(GOV, "test_scope_is_THE_session_keep_across_two_sessions")],
    "WB5": [(REG, "test_register_refuses_a_hostile_identifier_before_any_store_write"),
            (REG, "test_register_refuses_a_blank_role_before_any_store_write")],
    "WB8": [(GOV, "test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent")],
    "WB9": [(GOV, "test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent")],
    "WB10": [(GOV, "test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent")],
    "WB11": [(REG, "test_register_refuses_a_hostile_identifier_before_any_store_write[fixer-b\\n-"),
             (REG, "test_the_identifier_decision_is_the_SHARED_is_legal_identifier")],
    "WB12": [(GOV, "test_a_householded_joiners_agent_is_stamped_with_the_shared_session_keep")],
    "WB12b": [(GOV, "test_a_householded_joiners_agent_is_stamped_with_the_shared_session_keep")],
    "WB13": [(REG, "test_the_blank_role_rule_is_the_SHARED_is_blank")],
    # --- new wrong builds (r2 seams) --- declared EMPTY = my prediction is that they SURVIVE.
    "N1": [],   # server: two deciders (traffic-line predicate stays a private fullmatch)
    "N1b": [],  # server: the traffic-line predicate DRIFTS to .match (#210 class) on the skip policy
    "N2": [],   # registry: A3 XOR only on the CREATE branch (re-register with a mixed pair accepted)
    "N3": [],   # migrate: refusal lists ALL ids, unbounded (§6 "ids, bounded")
    "N4": [],   # schema: a NEW relation over AGENT_TABLE spelled with keyword endpoints — never joins
    "N4ctl": [(ENF, "test_the_derived_population_set_grows_to_memory_message_to")],  # positional control
    "N5": [],   # fake: FakeAgentRegistry stamps a WRONG scope/owner_agent (P5: can the fake's mirror fail?)
    "N1c": [],  # server: the traffic-line predicate is a private DRIFTED fullmatch (admits dots)
    "N10": [],  # registry: a re-register HEALS a NONE-scope row with the session scope (scope-without-owner)
    "N6": [(GOV, "test_an_inconsistent_provenance_pair_is_refused_before_any_store_io[keep-without-owner]")],  # A3 one-sided
}


def edit(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{rel}: anchor occurs {count} times: {old[:80]!r}"
    path.write_text(text.replace(old, new))


if "--declared" in sys.argv:
    collected = (SCR / "collected.txt").read_text().splitlines()
    for file_fragment, node_fragment in DECLARED[WB]:
        hits = [node for node in collected if file_fragment in node and node_fragment in node]
        assert hits, f"declared rule ({file_fragment}, {node_fragment}) matched NO collected node"
        for node in hits:
            print(node)
    raise SystemExit(0)

XOR = (
    "        if (owner_principal_id is None) != (session_keep_id is None):\n"
    "            raise AgentRegistryError(\n"
    '                "register called with an owner but no session keep (or the reverse) — a "\n'
    '                "server-side caller bug; nothing was written"\n'
    "            )\n"
)

if WB == "WB1":
    edit(SCHEMA, "    # packet 62, Fork 1 / wave 2 (W2.2, W2-R7)",
         '    ("owner_principal", "option<record<principal>>", ""),\n    # packet 62, Fork 1 / wave 2 (W2.2, W2-R7)')
    edit(SCHEMA,
         "    statements += [\n"
         "        _define_field(AGENT_TABLE, name, type_expr, constraint=constraint)\n"
         "        for name, type_expr, constraint in _governed_field_specs()\n"
         "    ]\n"
         "    statements += _governed_index_statements(AGENT_TABLE)\n",
         "    declared = {spec[0] for spec in _AGENT_FIELD_SPECS}\n"
         "    statements += [\n"
         "        _define_field(AGENT_TABLE, name, type_expr, constraint=constraint)\n"
         "        for name, type_expr, constraint in _governed_field_specs()\n"
         "        if name not in declared\n"
         "    ]\n"
         "    statements.append(_plain_index(AGENT_TABLE, f\"{AGENT_TABLE}_owner_principal\", (\"owner_principal\",)))\n"
         "    statements += _governed_index_statements(AGENT_TABLE)\n"
         "    statements = list(dict.fromkeys(statements))\n")
elif WB == "WB2":
    edit(PRINCIPALS, "\"owner_agent = id, scope = $scope WHERE scope IS NONE\"", "\"owner_agent = id, scope = $scope\"")
elif WB == "WB3":
    edit(PRINCIPALS,
         "f\"SELECT VALUE id FROM {AGENT_TABLE} WHERE scope IS NONE AND owner_principal IS NOT NONE\"",
         "f\"SELECT VALUE id FROM {AGENT_TABLE} WHERE owner_principal IS NOT NONE\"")
elif WB == "WB4":
    edit(SERVER,
         '                str(session_keep.id).split(":", 1)[-1] if session_keep is not None else None\n',
         '                sorted(visible)[0].split(":", 1)[-1] if session_keep is not None else None\n')
elif WB == "WB5":
    edit(AGENTS,
         "                raise InvalidAgentIdentityError(\n"
         '                    f"agent {field_name} must match',
         '                raise InvalidAgentIdentityError("invalid input")\n'
         "                raise InvalidAgentIdentityError(\n"
         '                    f"agent {field_name} must match')
    edit(AGENTS,
         "            raise InvalidAgentIdentityError(\n"
         '                "agent role must not be blank',
         '            raise InvalidAgentIdentityError("invalid input")\n'
         "            raise InvalidAgentIdentityError(\n"
         '                "agent role must not be blank')
elif WB == "WB8":
    edit(PRINCIPALS, "f\"({', '.join(owned_unscoped_ids[:10])}) — a multi-principal", "f\"— a multi-principal")
elif WB == "WB9":
    edit(PRINCIPALS, "f\"{len(owned_unscoped_ids)} agent row(s) carry an owner but no scope \"",
         "\"some agent rows carry an owner but no scope \"")
elif WB == "WB10":
    edit(PRINCIPALS, "    owned_unscoped = await run_query(\n",
         "    await run_query(acquire=store.acquire, drop=store.drop, url=store.url, noun='pre', label='pre',\n"
         "        statement=f\"UPDATE {AGENT_TABLE} SET owner_principal = type::record('{PRINCIPAL_TABLE}', $owner) WHERE owner_principal IS NONE\",\n"
         "        params={'owner': operator.id.partition(':')[2] or operator.id}, logger=logger)\n"
         "    owned_unscoped = await run_query(\n")
    edit(PRINCIPALS, "f\"SELECT VALUE id FROM {AGENT_TABLE} WHERE scope IS NONE AND owner_principal IS NOT NONE\"",
         "f\"SELECT VALUE id FROM {AGENT_TABLE} WHERE scope IS NONE AND owner_principal IS NOT NONE AND owner_principal != type::record('principal', $op)\"")
    edit(PRINCIPALS, "        params={},\n        logger=logger,\n    )\n    owned_unscoped_ids",
         "        params={'op': operator.id.partition(':')[2] or operator.id},\n        logger=logger,\n    )\n    owned_unscoped_ids")
elif WB == "WB11":
    edit(AGENTS, "            if not is_legal_identifier(value):\n",
         "            if not AGENT_NAME_PATTERN.match(value):\n")
elif WB == "WB12":
    # keeper-only session stamp (the r1 door); under A3 an owner without a keep now REFUSES.
    edit(SERVER,
         '                str(session_keep.id).split(":", 1)[-1] if session_keep is not None else None\n',
         '                str(session_keep.id).split(":", 1)[-1] if session_keep is not None and kept_by_me else None\n')
elif WB == "WB12b":
    # the A3-consistent form of WB12: a JOINER registers with NEITHER owner NOR keep (ownerless).
    edit(SERVER,
         "            owner_principal_id=principal_bare,\n            session_keep_id=(\n",
         "            owner_principal_id=principal_bare if kept_by_me else None,\n            session_keep_id=(\n")
    edit(SERVER,
         '                str(session_keep.id).split(":", 1)[-1] if session_keep is not None else None\n',
         '                str(session_keep.id).split(":", 1)[-1] if session_keep is not None and kept_by_me else None\n')
elif WB == "WB13":
    edit(AGENTS, "        if is_blank(role):\n", "        if not role.strip():\n")
elif WB == "N1":
    # _validate_comms_charset routes to the shared predicate; _is_comms_charset_legal (still read by
    # _comms_traffic_line's SKIP policy) keeps a PRIVATE fullmatch on the pattern — two deciders.
    edit(SERVER, "        if not AppContext._is_comms_charset_legal(value):\n            raise ValueError(\n",
         "        from lorerunes import is_legal_identifier  # noqa: PLC0415\n\n"
         "        if not is_legal_identifier(value):\n            raise ValueError(\n")
    edit(SERVER,
         "        from lorerunes import is_legal_identifier  # noqa: PLC0415 - house lazy-import idiom\n\n"
         "        return is_legal_identifier(value)\n",
         "        return AGENT_NAME_PATTERN.fullmatch(value) is not None\n")
elif WB == "N1b":
    edit(SERVER, "        if not AppContext._is_comms_charset_legal(value):\n            raise ValueError(\n",
         "        from lorerunes import is_legal_identifier  # noqa: PLC0415\n\n"
         "        if not is_legal_identifier(value):\n            raise ValueError(\n")
    edit(SERVER,
         "        from lorerunes import is_legal_identifier  # noqa: PLC0415 - house lazy-import idiom\n\n"
         "        return is_legal_identifier(value)\n",
         "        return AGENT_NAME_PATTERN.match(value) is not None\n")
elif WB == "N2":
    edit(AGENTS, XOR, "")
    edit(AGENTS, "        if existing_row is None:\n            # packet 62 W2.3",
         "        if existing_row is None:\n"
         + "\n".join(("    " + line) if line else line for line in XOR.split("\n"))
         + "            # packet 62 W2.3")
elif WB == "N3":
    edit(PRINCIPALS, "f\"({', '.join(owned_unscoped_ids[:10])}) — a multi-principal", "f\"({', '.join(owned_unscoped_ids)}) — a multi-principal")
elif WB in ("N4", "N4ctl"):
    call = (
        "_define_relation_table(OWNS_RELATION, in_table=AGENT_TABLE, out_table=MEMORY_TABLE)"
        if WB == "N4" else "_define_relation_table(OWNS_RELATION, AGENT_TABLE, MEMORY_TABLE)"
    )
    edit(SCHEMA, 'BRIEFED_RELATION = "briefed"\n', 'BRIEFED_RELATION = "briefed"\nOWNS_RELATION = "owns"\n')
    edit(SCHEMA,
         "    statements: list[str] = [\n"
         "        _define_relation_table(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, enforced=True)\n"
         "    ]\n",
         "    statements: list[str] = [\n"
         "        _define_relation_table(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, enforced=True)\n"
         "    ]\n"
         f"    statements.append({call})\n")
elif WB == "N5":
    edit(FAKES, "            self.db.owner_agents[agent_id] = agent_id\n",
         "            self.db.owner_agents[agent_id] = 'WRONG'\n")
    edit(FAKES, "            self.db.scopes[agent_id] = keep_scope(session_keep_id) if session_keep_id is not None else None\n",
         "            self.db.scopes[agent_id] = 'keep:WRONG'\n")
elif WB == "N6":
    edit(AGENTS, "        if (owner_principal_id is None) != (session_keep_id is None):\n",
         "        if owner_principal_id is not None and session_keep_id is None:\n")
elif WB == "N1c":
    edit(SERVER, "        if not AppContext._is_comms_charset_legal(value):\n            raise ValueError(\n",
         "        from lorerunes import is_legal_identifier  # noqa: PLC0415\n\n"
         "        if not is_legal_identifier(value):\n            raise ValueError(\n")
    edit(SERVER,
         "        from lorerunes import is_legal_identifier  # noqa: PLC0415 - house lazy-import idiom\n\n"
         "        return is_legal_identifier(value)\n",
         "        return re.fullmatch(r\"[a-z0-9][a-z0-9_.-]{0,63}\", value) is not None\n")
elif WB == "N10":
    edit(AGENTS, "        new_model = model if model is not None else existing.model\n",
         "        if existing_row.get(\"scope\") is None and session_keep_id is not None:\n"
         "            await self._query(\n"
         "                f\"UPDATE type::record('{AGENT_TABLE}', ${_ROW_ID_PARAM}) SET scope = $heal_scope, \"\n"
         "                f\"owner_agent = type::record('{AGENT_TABLE}', ${_ROW_ID_PARAM})\",\n"
         "                {_ROW_ID_PARAM: agent_id, \"heal_scope\": keep_scope(session_keep_id)},\n"
         "            )\n"
         "        new_model = model if model is not None else existing.model\n")
else:
    raise SystemExit(f"unknown {WB}")
print(f"{WB} applied")
```

### A.3 `run_lane.sh` — lane driver (declare → apply → run → diff both ways → restore)
```bash
#!/usr/bin/env bash
# Apply each wrong build on top of adv2-ref in LANE, run the 17 r2 contract files + comms_wiring,
# diff the observed RED set against the DECLARED set (resolved from collect-only BEFORE the run).
set -u
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/dc888a1c-9807-4fec-be48-0a1fc30a29b1/scratchpad
LANE=$1; shift
cd "$S/$LANE"
echo "[$LANE] provenance: $(uv run python -c 'import loremaster; print(loremaster.__file__)')"
for WB in "$@"; do
  git checkout -q -f adv2-ref
  uv run --no-project python "$S/my_wbs.py" "$S/$LANE" "$WB" --declared > "$S/decl_$WB.txt" || { echo "$WB: DECLARE FAILED"; continue; }
  uv run --no-project python "$S/my_wbs.py" "$S/$LANE" "$WB" || { echo "$WB: APPLY FAILED"; continue; }
  echo "== $WB landed: $(git diff --shortstat)"
  timeout 1500 uv run pytest -n 12 -q -p no:cacheprovider --tb=short --junitxml="$S/wb_$WB.xml" $(cat $S/files.txt) loremaster/tests/test_comms_wiring.py > "$S/wb_$WB.log" 2>&1
  echo "== $WB tail: $(tail -n 1 $S/wb_$WB.log)"
  uv run --no-project python - "$WB" <<'PY'
import sys, xml.etree.ElementTree as ET
S="/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/dc888a1c-9807-4fec-be48-0a1fc30a29b1/scratchpad"
wb=sys.argv[1]
declared=set(open(f"{S}/decl_{wb}.txt").read().split("\n"))-{""}
def nid(tc):
    cn=tc.get("classname"); parts=cn.split(".")
    # classname = loremaster.tests.<module>.<Class>  ->  loremaster/tests/<module>.py::<Class>::<name>
    mod_idx=next(i for i,p in enumerate(parts) if p.startswith("test_"))
    path="/".join(parts[:mod_idx+1])+".py"; rest="::".join(parts[mod_idx+1:])
    return f"{path}::{rest}::{tc.get('name')}" if rest else f"{path}::{tc.get('name')}"
root=ET.parse(f"{S}/wb_{wb}.xml").getroot()
observed={nid(tc) for tc in root.iter("testcase") if tc.find("failure") is not None or tc.find("error") is not None}
unexpected=sorted(observed-declared); still_green=sorted(declared-observed)
verdict = "SURVIVES (0 red)" if not observed else ("KILLED — declared set fired EXACTLY" if not unexpected and not still_green else "KILLED (set differs from declaration)")
print(f"== {wb} VERDICT: {verdict}; observed={len(observed)} declared={len(declared)}")
for n in unexpected: print(f"   UNEXPECTED-RED {n}")
for n in still_green: print(f"   DECLARED-STILL-GREEN {n}")
PY
done
git checkout -q -f adv2-ref
```

### A.4 `test_adv_r2_killpins.py` — the kill-pins (copied into a lane's `loremaster/tests/` only for the proof runs)
```python
"""adversary-63c-i-a-r2 — kill-pins for the wrong builds that SURVIVE the r2 contract (scratch-only).

Each pin is proven by the PAIR: GREEN on my independent reference (adv2-ref) and RED on exactly its
wrong build (my_wbs.py). Copied into <lane>/loremaster/tests/ only for the proof runs; never the repo.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

import pytest
from _comms_fakes import FakeAgentRegistry
from _governed_contract import AGENT_TABLE, patch_shared_object_everywhere, seed_agent_governed
from _surreal_harness import run
from loremaster.agents import AgentRegistry, AgentRegistryError
from loremaster.store import surreal_schema
from lorerunes.pdp import keep_scope
import test_agent_governance_63c_i_a as governance_contract
from test_agent_governance_63c_i_a import (  # noqa: F401 - pytest fixtures imported by name
    _migrate_agent,
    agent_migrate_world,
    registry_world,
)


# --- KP-N1: EVERY server consumer of the identity decision moves with lorerunes.is_legal_identifier --
def test_KP_N1_the_skip_policy_predicate_moves_with_the_shared_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``_is_comms_charset_legal`` (read by ``_comms_traffic_line``'s SKIP policy) must be the SHARED
    decision: perturb ``lorerunes.is_legal_identifier`` to reject 'fixer-b' → the predicate flips."""
    import lorerunes
    from loremaster.server import AppContext

    assert AppContext._is_comms_charset_legal("fixer-b") is True  # noqa: SLF001 - BASELINE
    shared = lorerunes.is_legal_identifier
    patch_shared_object_everywhere(
        monkeypatch, "is_legal_identifier", shared, lambda value: value != "fixer-b" and shared(value)
    )
    assert AppContext._is_comms_charset_legal("fixer-b") is False, (  # noqa: SLF001
        "the traffic-line SKIP predicate did not move with lorerunes.is_legal_identifier — a second "
        "decider wearing the shared pattern (routing is not sharing, A4)"
    )


# --- KP-N2: the A3 refusal holds on the RE-REGISTER path too (∀ calls, before _select_row) -----------
@pytest.mark.parametrize(
    ("owner", "keep"), [("alice_pid", None), (None, "sessionkeep7")], ids=["owner-only", "keep-only"]
)
async def test_KP_N2_a_mixed_pair_re_register_is_refused_and_writes_nothing(
    registry_world: Any, owner: str | None, keep: str | None
) -> None:
    registry, connection = registry_world
    await registry.register(
        "fixer-b", session="wave7", role="builder", owner_principal_id="alice_pid",
        session_keep_id="sessionkeep7",
    )
    before = await run(connection, f"SELECT * FROM {AGENT_TABLE} ORDER BY id")
    with pytest.raises(AgentRegistryError):
        await registry.register(
            "fixer-b", session="wave7", role="builder", owner_principal_id=owner, session_keep_id=keep
        )
    after = await run(connection, f"SELECT * FROM {AGENT_TABLE} ORDER BY id")
    assert after == before, "a refused (mixed-pair) RE-register still wrote the row"


# --- KP-N3 (P2 perturbation): the refusal's id list is BOUNDED (§6 "ids, bounded") ---------------
async def test_KP_N3_the_refusal_names_the_count_and_a_BOUNDED_id_list(agent_migrate_world: Any) -> None:
    principal_store, keep_store, connection, env, _operator = agent_migrate_world
    await governance_contract.TestAgentMigrateScopeKeyed63cIA._seed_clean_legacy(connection, count=1)  # noqa: SLF001
    trap_count = 25
    trap_ids = [f"trap_{index:02d}" for index in range(trap_count)]
    for index, trap_id in enumerate(trap_ids):
        await seed_agent_governed(
            connection, row_id=trap_id, name=f"trap-{index}", session="dead-session",
            owner_principal=f"other_{index}", owner_agent=None, scope=None,
        )
    before = await run(connection, f"SELECT * FROM {AGENT_TABLE} ORDER BY id")
    result = await _migrate_agent(connection, env, keep_store=keep_store, principal_store=principal_store)
    after = await run(connection, f"SELECT * FROM {AGENT_TABLE} ORDER BY id")
    assert result.refused is True and after == before
    reason = str(result.reason or "")
    assert re.search(rf"\b{trap_count}\s+(?:agent\s+)?rows?\b", reason), reason
    named = [trap_id for trap_id in trap_ids if trap_id in reason]
    assert 1 <= len(named) < trap_count, (
        f"the refusal must name the rows BOUNDED (§6 'ids, bounded'); it named {len(named)} of "
        f"{trap_count}: {reason[:300]!r}"
    )


# --- KP-N4 (P1c): the population resolver's reach is a CHECKED variable — no endpoint unresolved -----
def test_KP_N4_every_relation_emitter_call_in_the_real_schema_resolves_all_three_endpoints() -> None:
    from _governed_contract import _DEFINE_RELATION_EMITTER, _resolve_schema_table, _schema_string_constants
    from _governed_contract import call_name

    source = Path(surreal_schema.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    constants = _schema_string_constants(tree)
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and call_name(node) == _DEFINE_RELATION_EMITTER
    ]
    assert calls, "found NO relation-emitter call — the scan is broken, not clean (anti-vacuity)"
    unresolved = []
    for call in calls:
        endpoints = list(call.args[:3])
        if len(endpoints) < 3:
            unresolved.append(ast.unparse(call))
            continue
        if any(_resolve_schema_table(arg, constants) is None for arg in endpoints):
            unresolved.append(ast.unparse(call))
    assert not unresolved, (
        f"relation-emitter call(s) the population derivation CANNOT resolve (they silently never join "
        f"the governed set, whatever their endpoints): {unresolved}"
    )


# --- KP-N5 (P5): the fake's writer-mirror stamps can FAIL -----------------------------------------
async def test_KP_N5_the_fake_registry_stamps_what_the_real_writer_stamps() -> None:
    fake = FakeAgentRegistry()
    result = await fake.register(
        "fixer-b", session="wave7", role="builder", owner_principal_id="alice_pid",
        session_keep_id="sessionkeep7",
    )
    agent_id = str(result.agent.id).split(":", 1)[-1]
    assert fake.db.scopes[agent_id] == keep_scope("sessionkeep7"), fake.db.scopes
    assert fake.db.owner_agents[agent_id] == agent_id, fake.db.owner_agents


# --- KP-N10: mint-once holds for EVERY row, incl. an ownerless (α) one — re-register never stamps -----
async def test_KP_N10_a_credentialed_re_register_never_stamps_an_ownerless_rows_scope(
    registry_world: Any,
) -> None:
    registry, connection = registry_world
    first = await registry.register("fixer-b", session="wave7", role="builder")  # (None, None) — α
    bare = str(first.agent.id).split(":", 1)[-1]
    projection = f"SELECT owner_principal, owner_agent, scope FROM type::record('{AGENT_TABLE}', $id)"
    before = await run(connection, projection, {"id": bare})
    await registry.register(
        "fixer-b", session="wave7", role="builder", owner_principal_id="alice_pid",
        session_keep_id="sessionkeep7",
    )
    after = await run(connection, projection, {"id": bare})
    assert after == before, (
        f"a re-register STAMPED an ownerless row's governed columns (mint-once is CREATE-only, §2.2 "
        f"row 2; a scope-without-owner row escapes the migrate's WHERE scope IS NONE forever): "
        f"before={before!r} after={after!r}"
    )


_ = AgentRegistry  # imported for type context only
```

### A.5 one-off probes (verbatim)
```bash
# collected.txt — the declaration universe, taken BEFORE any wrong-build run (on wb @ adv2-ref):
uv run pytest -q --collect-only -p no:cacheprovider $(cat files.txt) loremaster/tests/test_comms_wiring.py | awk '/::/' > collected.txt   # 2521 ids
# kill-pin pairs (ref lane): for WB in N1 N1b N1c N2 N3 N4 N5 N10: checkout -f adv2-ref; my_wbs.py ref $WB; cp test_adv_r2_killpins.py loremaster/tests/; pytest -n 12 -q -rf loremaster/tests/test_adv_r2_killpins.py
# N1b/N1c/WB11 behaviour + the repo-wide #210 scan:
uv run python -c 'from loremaster.server import AppContext as A; print(A._is_comms_charset_legal("fixer-b\n"), A._is_comms_charset_legal("fixer.b"))'
uv run pytest -q -p no:cacheprovider loremaster/tests/test_anchored_pattern_seam.py
# MP-G alias probe (ref lane, a CORRECT build): agents.py `from lorerunes import keep_scope as _format_keep_scope` + its one use, then
uv run pytest -q -p no:cacheprovider "loremaster/tests/test_agent_governance_63c_i_a.py::TestTheRegistryProvenanceSeam63cIA"   # -> 1 failed, 5 passed
# N4h: N4 + `enforced=True` on the owns call + KNOWN_RELATION_EDGES row `"owns": (AGENT_TABLE, "memory")`, then
python -c 'from _enforced_relations_scaffold import every_emitted_relation_table; from _governed_contract import governed_populations; print(every_emitted_relation_table().get("owns")); print(sorted(governed_populations()))'
# gate currency (ref lane, at HEAD~1 then at adv2-ref):
uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff
```
