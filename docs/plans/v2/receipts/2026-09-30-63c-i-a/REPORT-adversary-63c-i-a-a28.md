brief-base v16 read · brief project v7 read

# REPORT-adversary-63c-i-a-a28 — narrow adversary delta on the 63c-i-a fix-pass contract a28 (`d334042`)

## SUMMARY BLOCK
- **state:** done-with-deviations (DV-1…DV-5, §0)
- **VERDICT: CONTRACT INSUFFICIENT** — **11 of 18 non-degenerate wrong builds pass all 140 contract pins** (W2, W3a, W3b, W3c, W4c, W7, W14, W15, W15b, W18, W19); the full suite catches 3 of them (W15 by the retry-seam scanner; W3a / W3b only INCIDENTALLY — the comms fakes lack `resolve_holder` / `_query`; W3c, the same read through a method the fakes implement, survives the suite). **Union 3 — W2 + W3c + W19 + W7 + W15b + W18 applied together — passes the FULL suite with a red set identical to my correct reference's (238 = 238)** (§1b). Every survivor is killed by a pasted probe (§A.2), 4 of them by ONE generated pin (K9). Classes: **MISSING PIN ×5** (MP-1 HIGH · MP-2/MP-3 MEDIUM · MP-4/MP-5 LOW) · **NEW DOOR ×1** (FK-ADV-1: the RS-5 classifier vs the SDK's typed `AlreadyExistsError` — a design fork) · **SAT DEFECT ×3** (am-31 fold F-1/F-2/F-3, lead-directed #17070) + 2 contract items (F-5, FK-ADV-2) · **NOT A DEFECT ×3** (W4c, W15, the DUAL D2 sliver). SAT on my independent register-half build: **0 reference-only reds, the identical 45 fixed** (§7).
- **P1 headline:** the §F-1/§F-2/RS-5 invariants are pinned for the failure mode that was debugged (role-conflict race; a keepless foreign principal; the unique-id conflict) — the same bad outcomes walk through unguarded doors: compensation on a different refusal class (W2), a registry read the spy does not wrap (W3a/W3b), a gate keyed on "caller sees no keep" (W19), a catch-all with no existence re-read that RECURSES on a genuine rejection (W7), text-keyed / transport-swallowing classification (W14, W15b), a second copy of the re-register path (W18).
- **Packages considered:** `surrealdb` 2.0.0 `AlreadyExistsError` — READ installed `surrealdb/errors.py` + LIVE probe: the agent CREATE conflict's `__cause__` IS `AlreadyExistsError(kind=AlreadyExists, details.kind=Record, record_id=agent:…)`; the ONE driver flattens it to `TxnDomainRejectionError(unspecified)` → `replace_with_adapter` (a DESIGN fork, §3) · stdlib `unittest.mock.AsyncMock(wraps=)` for the counting spies — `replace` optional (trivia) · pytest-repeat — not installed; `keep_with_trigger` n/a. Author's line reads "none — no mechanism specified" while §10 item 3 specifies one: **P-PKG diff = 1 miss** (§3).
- **Odoo-20 portability:** n/a — no Odoo seam touched (my enumeration: 0 seams; author: n/a — agree)
- **Reuse ledger:** 0 production symbols; scratch-only test helpers (K-probes) — DRY ledger §A.4
- **Graded:** `d334042` · HEAD-at-report: `388c604` · DIFFERENT (19 ahead): the graded test files and the 63c production files are byte-identical `d334042`→HEAD (`git diff --stat` empty for both); HEAD adds am-31 (`4a8ea02`, graded per #17070 as fold items only) + unrelated #466 / lead-report commits.
- **decisions-needed:** (1) am-29's RS-5 "catch by CLASS, else STOP" — the SDK already types the conflict (`AlreadyExistsError`) but the driver erases it; accept `TxnDomainRejectionError`+existence re-read (the contract's §10 item 3 reading) or add a typed `TxnAlreadyExists…` in the ONE driver? (§3, FK-ADV-1) · (2) am-31 vs am-30 on the message leg's refusal: am-31's control says the AGENT fields are `None` there, a28 pins them MEASURED (`_RS1_COUNTS`, `P_message`) (§6, FK-ADV-2)
- **Receipt pointers:** §1 P1 wrong builds · §2 P1b quantifier table · §3 P-PKG diff · §4 P1c reach table · §5 DUAL (P6b) + corpse sweep (P6) · §6 am-31 fold items · §7 SAT · §8 RED honesty (P7) · §9 residuals · §A instruments verbatim


## §0 Capability check + deviations (brief-base §4)
- All demanded tools present: lore_comms (registered `adversary-63c-i-a-a28` / `63c-20260924` / adversary / ≤20m; heartbeats; directive **#17070 acked**), lore_findings, Bash/Read/Write. **`lore_search` FAILED** (no response for 300 s, client abort) on my one DRY query → filed **#502**; fallback: awk over `loremaster/loremaster/*.py` for `except (SurrealStoreError|TxnDomainRejectionError)` (said here, per the dogfood protocol). grep/rg hook-blocked (#473) — awk throughout.
- **DV-1 (reference independence, partial by design):** my reference's REGISTER half (`server.py` / `agents.py` / `keeps.py` — everything items (a)–(c) grade) is MY OWN build (`myref.py`, §A.1), written before I read the author's register hunks (I never read them). The MIGRATE half (`governed.py` / `principals.py` — am-26/27/30 + A2/A5, outside my narrow grade) is the author's §A.3 hunks applied verbatim (patch md5 `0abdf6d8…` re-derived from the report = the author's claim). So the SAT receipt is independent for the graded surface only.
- **DV-2 (W16 degenerate):** W16's replacement emitted a quoting SyntaxError (collection error on BOTH trees; both drivers reported MISMATCH/no-tail, never a pass). Re-declared as W16b (declared after seeing only the collection error, before any W16b outcome — timestamp `declared6_at`).
- **DV-3 (trees):** the main checkout moved under me (am-31, #466 commits, a foreign uncommitted `testing/loopback.py` edit). The `ref` tree (wrong-build batches) predates the loopback edit; the `probe` tree (kill probes + SAT reference) and `base2` (SAT baseline = `probe` with the five production files `git checkout`-ed to HEAD, each `git diff --quiet 169925f` ✓) share it. SAT compares `probe` vs `base2` only — ONE tree both ways.
- **DV-5 (watchdog reading — two readings of the brief's "15 GB PID watchdog"):** (a) kill my tree when host MemAvailable < 15 GB (the author's `guarded.sh`); (b) kill my tree when ITS OWN RSS exceeds 15 GB. Other tenants held this host at 11–27 GB available (production + test SurrealDB 17.7 + 9.9 GB RSS, several Postgres clusters), so under (a) my first baseline full suite was SIGTERMed (EXIT=143) mid-run. I ran every full suite under (b) plus a 4 GB host-floor safety (`guarded_tree2.sh`, §A.8, positive control shown: a 3-level tree killed, 0 survivors). Picked (b); flagging (a) vs (b) for the lead.
- **DV-4 (prediction misses, disclosed):** W1 +1 extra red (RS-5 handler: two racing deletes raise `KeepNotFoundError` into a caller — the author's M01 note), W9 +7 extra reds and KP13 declared-but-green. None changes a verdict; every declared set was written before its run (timestamps §A.3).

## §3 P-PKG — my table first, then the diff against the author's
Built from the contract + am-28/29 BEFORE opening the author's survey line (which I had seen only as the one-line
summary "none — no mechanism specified").
| mechanism the contract specifies | library evaluated | what I READ | verdict |
|---|---|---|---|
| RS-5: classify the agent CREATE's unique-id conflict (a28 §10 item 3: catch `TxnDomainRejectionError`, require the re-read row to exist) | `surrealdb` 2.0.0 typed errors | installed `surrealdb/errors.py`: `ErrorKind.ALREADY_EXISTS`, `class AlreadyExistsError(ServerError)` with `.record_id`, `KIND_TO_CLASS["AlreadyExists"]`, `parse_rpc_error`; **LIVE probe** (§A.5, TEST store :18000, 3.2.x): the conflict's `__cause__` is `surrealdb.errors.AlreadyExistsError`, `kind='AlreadyExists'`, `details={'kind': 'Record', 'details': {'id': 'agent:5dd1…'}}`, `record_id='agent:5dd1…'`. The ONE driver's `_classify_engine_error` has no AlreadyExists branch → `(unspecified rejection)` → `TxnDomainRejectionError`, the same class an ASSERT / coercion / any other domain rejection gets. | **`replace_with_adapter`** — the typed classification EXISTS in the package and is erased one layer up. am-29 names this exact decision point ("if the driver's classification of the unique-id conflict is not already a typed rejection the registry can catch by class … STOP"). The contract resolved it silently by prescribing the broad class + an existence re-read. → **FK-ADV-1** (below). |
| RS-5: CAS "re-read on conflict, return the winner" POLICY | in-house `keeps.KeepStore.get_or_create_keyed` (the other CAS door) | read source: catches `SurrealStoreError` after an explicit `except (SurrealConnectionError, TxnContentionExhaustedError): raise`; re-reads by key | not a package — an **ONE-IMPLEMENTATION** observation: after a28 the tree carries two hand-rolled CAS classifiers that already disagree on the class (keeps: `SurrealStoreError − {transport, contention}`; RS-5: `TxnDomainRejectionError`). A typed driver class (FK-ADV-1 B) would give both one predicate. Escalated, not graded. |
| counting spies (`_count_calls`, `_spy_delete_keep`) | stdlib `unittest.mock.AsyncMock(wraps=…)` | CPython 3.14.7 `AsyncMockMixin._execute_mock_call` (`if iscoroutinefunction(self._mock_wraps): return await self._mock_wraps(...)`) + live check (`await_count == 1`, delegated result) | `replace` optional — test trivia, not policy; NOT a finding |
| 20-consecutive concurrency clearing (conc20.sh) | pytest-repeat / pytest-flakefinder | site-packages listing: neither installed (only `hypothesis`) | keep — serial whole-session re-runs are the law's semantics (store-ref §5); `--count` inside one session is a different experiment; NOT a finding |
| 8-way race rig | stdlib `asyncio.gather` | — | used as-is |
**Diff:** the author's `Packages considered: none — no mechanism specified` misses row 1 — §10 item 3 IS a mechanism specification (a classification rule), and the package that already classifies it was not read. **1 miss.** Not a defect the builder can fix: the contract will be built exactly as §10 says.

**FK-ADV-1 (decision needed, sidecar/operator):** RS-5's classifier.
- **Reading A (the contract's, §10 item 3):** `except TxnDomainRejectionError` + "the re-read row EXISTS" ⇒ conflict. Correct on today's engine; needs K2 (the non-conflict door) pinned, or W7 ships.
- **Reading B (am-29 literal + P-PKG):** the ONE driver maps the SDK's `AlreadyExistsError` (details kind `Record`) to a typed `TxnDomainRejectionError` subclass; the registry catches THAT class; the existence re-read becomes a confirmation. W7 and W14 become unrepresentable (a non-conflict rejection is not that class; no text is read). Cost: a change in `_txn` (the shared driver every seam rides) — a design decision, which is why it is escalated rather than graded.
- My pick: **B** — it is what am-29 literally asked for, and the package already does the classification. Either way K2 + K4 stay (they grade the classifier's quantifier, whichever class it keys on).

## §4 P1c — reach table (every guard/gate/scan the graded pins introduce or rely on)
Legs: E = empirical (wrong build run), C = construction-inspection.
| instrument | set it should cover | reach derived or hand-list? | coverage a checked variable? | effect or proxy? | one source, proven by mutation? | verdict |
|---|---|---|---|---|---|---|
| RS-2 `delete_keep` spy (a28 `_spy_delete_keep`) | every keep-state write on the register path | hand-list of ONE verb | no | PROXY (a verb) — complemented by RS-2's effect leg (every row's scope ∈ live keeps; one session keep) | n/a | PROXY gap, partly covered: W16b (household-EDGE delete via raw `_query`) is KILLED by the contract's effect legs (the third register is denied); W2 walks around by REFUSAL CLASS and SURVIVES (§1). Kill: K5 + K6 (derived KeepStore verb allowlist + non-SELECT `_query` watch + before⊆after state). |
| RS-2 effect leg (scope ∈ live keeps; `[scope] == session_keeps`) | every agent row of the round | derived from the store (SELECT over the session) | yes (all 5 names asserted) | EFFECT | n/a | SAFE (E: W1, M01-class killed). Non-vacuity proxy: `refusal_rounds >= 1` counts ANY refusal (pre-mint preflight refusals included), not the post-mint path; its docstring says "every round … met ≥1 refusal". Measured on my reference: a post-mint refusal in **200/200** rounds and the keep's CREATOR refused post-mint in **193/200** (§A.6) → reach adequate in practice, unchecked in code (residual R-3). |
| RS-2 reach vs the checkpoint | the checkpoint-class compensation | — | — | — | — | per-round strand rate measured on `169925f`-production: 105/200 rounds (10/10 invocations RED; min 4/20). Miss probability per invocation: pooled p=0.525 ⇒ 0.475²⁰ ≈ 3.4×10⁻⁷; at the WORST observed invocation rate (author's and mine: 4/20, p=0.2) ⇒ 0.8²⁰ ≈ 0.012. The deterministic twin (sequential leg) is RED every time. SAFE as belt + braces. |
| RS-3 registry-read spy (`_select_row` / `preflight` / `register` + `get_or_create_keyed`) | every read of any agent row before the gate | **hand-list** of 3 registry methods | no | proxy (method names) | n/a | **MISSING PIN (E):** W3a (`resolve_holder` → `_select_rows_by_name`), W3b (raw `agent_registry._query`) and W3c (`get_agent` without a session) pass RS-3 + the whole contract; W3c also passes the fake-based comms suites (the only suite files sensitive to a pre-gate registry call — unions 1/2). Kill: K1 (spy the registry's ONE seam `AgentRegistry._query` — every registry read rides `run_query` through it) with a positive control. Bound stated: a read on ANOTHER connection (e.g. a governed select in `principals`) is outside K1 too. |
| RS-3 byte-identity over 4 probes | every fact the registry could serve a foreign caller | hand-list of preflight's row refusals (role, spawned_by, retired) + absent | n/a | EFFECT (served class+text) | n/a | SAFE on its axis; its FIXTURE is a monoculture: the foreign principal holds NO keep of her own → **W19** (gate keyed on "caller sees no keep at all") SURVIVES the contract. Kill: K8 (same probes by a principal who keeps another session). |
| RS-3 "tables byte-identical" | every write a denial could make | 3 tables (agent / keep / member_of) | no | PROXY (before/after snapshot) — a transient write-then-undo is invisible | n/a | **MISSING PIN (E):** W4c (create_keep + delete_keep on the deny path) passes. Kill: K6 foreign leg (keep-store write-verb allowlist). Low plausibility — see §1. |
| ORDER recorder (first `get_by_key`, `preflight`, `mint`, `register`) | the handler's call order | hand-list of 4 events | both sessions (fresh + existing) | proxy (call order) — M03 (dummy read, then the checkpoint order) passes it; RS-3 kills that | n/a | SAFE in combination (E: W9 killed by ORDER + a19a runtime + 6 refusal fixtures). |
| POST-MINT re-check pin | the keep-minted-meanwhile race | one construction | — | EFFECT (denied, no row) | n/a | SAFE (author M06; C). |
| RS-5 handler + registry pins | every legal concurrent register | 8-way × 20, identical role (registry) / alternating roles (handler) | yes (∀ callers, ∀ rounds) | EFFECT (served outcomes + rows) | ONE implementation (am-29) — proven only for a copy that DROPS preflight (W12 killed); a copy that KEEPS preflight and skips the UPDATE is W18 — SURVIVES | **MISSING PINS (E):** the classifier's quantifier (W7 non-conflict cause → recursion; W14 text-keyed; W15b transport swallowed) — kills K2/K3/K4; the loser-equals-sequential property (W18) — kill K7. |
| `_REGISTRY_CLASSES` (a28) | the registry's teaching family | DERIVED (`vars(agents_module)`, subclass of `AgentRegistryError`) | — | — | — | SAFE (C). |
| a19a `_RegisterPropertySpy` (relied on: "refused ⇒ zero mints, or the injected race") | every driven register | driver set = the a19a fixtures (not re-graded here) | a driver bypassing the armed comms reds by name (a19a) | EFFECT (mint calls + keep snapshot) | — | relied on, not re-graded; W9 killed through it (E). |
| `test_retry_seam._discover_guarded_cas_handlers` (the guarded-CAS door scanner — relied on implicitly by the suite for the RS-5 re-read door) | every handler that re-reads after a store rejection | **keyed on `ast.Name == "SurrealStoreError"`** + a `_select*` re-read name prefix | exact set vs `_GUARDED_CAS_DOORS` | C | — | **PRE-EXISTING reach bound (E):** W15 (`except SurrealStoreError`) IS caught (`test_the_door_enumeration_matches_the_canonical_set` RED) — but W15b (`except (TxnDomainRejectionError, SurrealConnectionError)`, a Tuple handler) and the correct `except TxnDomainRejectionError` door are both invisible to it; `keeps.get_or_create_keyed`'s re-read (`get_by_key`, not `_select*`) is already an unlisted door at HEAD. Not a28's instrument; surfaced (R-5). |

## §5 DUAL (P6b) — my enumeration of the deleted pins FIRST, then the diff with the author's §3
Enumerated from the deleted code (`git show d334042` hunks) before reading §3:
| # | deleted pin | observable virtue it carried | still guarded after a28? |
|---|---|---|---|
| D1 | a19a created-only pin `[created-by-this-call]` | the race's CREATED keep is removed so a DIFFERENT principal (bob) keeps the session next | retired on purpose (am-28 §F-1) — the tokenless case is the named β bound (a28 tokenless CONTROL) |
| D2 | a19a created-only pin `[found-pre-existing]` | a FOUND keep: **keep + member_of byte-identical** after a refused race (EFFECT observation — any mutation, not only a delete) | **PARTIAL** — a28 keeps the delete_keep VERB spy (proxy) + K survives + the third register FINDS/JOINS K. Measured: a household-edge removal (W16b) IS killed by the contract — through the CALLER's own edge (the third register is denied). A mutation confined to ANOTHER member's edge, or to the keep row's other columns, is observed nowhere. |
| D3 | same | the race path mints exactly ONCE | yes — a19a runtime property race observation `mints == 1` |
| D4 | same | the refusal is an `AgentRegistryError` | yes, stronger — sequential leg: served `(type, str)` == the registry's own |
| D5 | a19b #4b | teaching survives verbatim, same class | yes — sequential leg (type+str equality) + KP4 |
| D6 | a19b #4b | ONE appended remedy line names the left-behind keep | retired on purpose (nothing deletes) |
| D7 | a19b #4b | the delete WAS attempted | inverted on purpose (never called) |
| D8 | a19b #4b | the keep IS left behind after a failed delete | yes — K survives (sequential) |
| D9 | a19b #4b (implicit) | a delete error never REPLACES the teaching (N8) | moot — no delete |
| D10 | a19b KP1 (old) | a keep this call merely FOUND survives the race refusal (exact key list) | yes, re-keyed: `len(keeps)==1` + the winner's scope == live K |
| D11 | a19a runtime race branch | "refused after a mint ⇒ injected race AND keep byte-identical" | first half kept; second half retired on purpose |
**Diff vs the author's §3 (U1–U8):** every author row grounds in the code. My D2 is the delta: the author's U1(b) says the found-keep virtue is "PRESERVED-with-pin, widened ∀ keeps (a28 `delete_keep` spy = 0)" — **an over-claim**: the old pin observed the EFFECT (keep + member_of byte-identity), the new one observes a PROXY (one verb). Widened over keeps, narrowed over mutations. Kill: K6 race legs (found keep, bob householded, ∀ refusal classes: before == after on keep+member_of, and the keep-store write allowlist). D3/D8/D9 are unlisted by the author but guarded or moot. The (d) question — "is anything the deleted pins guarded now unguarded, other than what am-28 retires on purpose?" — **only a sliver of D2's mutation axis** — a change to another householder's edge or to the keep row's non-key columns on a refused race; no plausible build does that (W16b, the plausible one, is killed). Verdict: NOT A DEFECT for (d); K6's race legs close the sliver for free if the fold lands C1.

### P6 corpse sweep (bare, anchor-free patterns: `minted_by_this_call|compensation_failed|delete-keep --keep|created-only|created_only|left behind|#4b|compensat`) over `loremaster/tests/*.py`, `scripts/*.py`, `scripts/*.yaml` at `99dbe49` — every hit:
| hit | verdict |
|---|---|
| `test_fixwave_a19a_63c_i_a.py:14-15` module docstring: "…created-only compensation for the race…" | **STALE PROSE** (test docstring still teaches the retired mechanism; not served; cosmetic) |
| a19a `:320` DUAL comment | current |
| a19a `:455-456` spy docstring DUAL | current |
| a19a `:581` "*refused ⇒ zero mints, or a compensated injected…*" | **STALE PROSE** (the property is no longer "compensated") — cosmetic |
| a19a `:588-590`, `:633-635`, `:830` DUAL comments | current |
| a19b `:21-23` module docstring DUAL | current |
| a19b `:80` `test_KP1_…_is_never_compensated` (name) | current (true under a28) |
| a19b `:603-612` DUAL block | current |
| a28 `:13`, `:106`, `:140`, `:144`, `:169`, `:216` | current (describe the removal) |
No ASSERTION anywhere pins the retired mechanism (no corpse assertion). Production still carries it at HEAD (expected — the builder deletes at GREEN): `keeps.py` `_MINTED_BY_THIS_CALL` / `minted_by_this_call` + docstrings, `server.py` compensation block + `comms.register.compensation_failed` log event. ⚠ **No pin requires `minted_by_this_call` to be DELETED** (am-28 §F-1: "dead and go") — my own reference left the function defined-but-unused and passed everything (residual R-2).

## §6 am-31 fold items (lead directive #17070: report as SAT/contract items, NOT ruling defects) — construction-inspection
| # | a28 site (`d334042`) | conflict with am-31 (`4a8ea02`) | class |
|---|---|---|---|
| F-1 | `TestTheMeasuredCountsAreTypedFields63cIAa28::test_am30_the_counts_model_has_exactly_the_ruled_fields` — `tuple(model.model_fields) == _RULED_COUNT_FIELDS` (six) + `== [None] * 6` / `list(range(6))` | am-31 adds `distinct_owner_principals` + `owner_classification` → an am-31 build is RED here | SAT DEFECT (fold) |
| F-2 | `_counts()` returns `{name: … for name in model.model_fields}` (DERIVED), but `_POPULATIONS[*]`, `_RS1_COUNTS` and `None_means_not_measured[clean-memory-proceeds]` expect SIX-key dicts → `test_am30_the_served_fields_are_the_measured_counts[P_agent\|P_message]`, `test_am30_None_means_not_measured[clean-memory-proceeds]`, and pin (2)'s ⊇ leg (reads `expected.items()`) go RED / blind on the two new fields | SAT DEFECT (fold) |
| F-3 | pin (1) `test_am30_pin1_perturbing_a_field_moves_the_reason` is **parametrised over the hand-list `_RULED_COUNT_FIELDS`**, not over `model_fields` — am-31's text "Pin (1) grows to the two new fields by `model_fields`, automatically" is FALSE for this contract; and `owner_classification` is an enum (`+ _PERTURBATION` is meaningless) → the fold must derive pin (1) over the model's INT fields and give the enum its own perturbation (e.g. swap operator↔foreign) | SAT/contract item (fold) + P1c: a hand-list wearing a derived docstring ("∀ fields … checked against the model's own `model_fields`") |
| F-4 | `_RS1_COUNTS` (every agent migrated, message-leg refusal) pins the three AGENT counts as measured `0`; `P_message` pins `owned_but_unscoped_agents: 0`, `scoped_but_ownerless_agents: 0` | am-31 FK-a28-4 control: "the message leg's own refusal … with the message fields measured and the agent fields `None`". a28 (and its §10 item 8: "the agent counts always (measured at the verb)") says the opposite. | **FK-ADV-2 — decision needed**: does am-31 mean "agent fields `None`" on a message-leg refusal although the verb MEASURED them (am-22 §4: serve "the reads the precondition DID perform")? Reading A (a28): measured 0s. Reading B (am-31 literal): `None`. The two produce different code; my pick is **A** (am-22 §4 is the older, general rule and "None = not measured" is literally false for a count the verb read) — the sidecar rules. |
| F-5 | FK-a28-4's verb-level `--table message` refusal: a28 has no pin that the MESSAGE fields are `None` there / omitted from the prose (the author wrote the pins agnostic) | am-31 rules it → a new pin is owed (am-31 §W row 2 + its control leg) | contract item (fold) |
Not graded further (outside (a)–(d)); not run against an am-31 build (none exists).

## §8 RED honesty (P7) — the author's RED @ `169925f`, reproduced
- `base2` (my `probe` tree with the five production files at HEAD ≡ `169925f`, each `git diff --quiet 169925f` ✓), the four changed files, `-n 8`: **45 failed, 118 passed** (a28 41 · a19a 2 · a19b 2) — the author's §5 count, exactly.
- Right reason, graded pins (`--tb=line`, 2026-09-26 ~16:22): RS-2 "7/20 rounds left agent rows whose scope does not resolve…"; both sequential legs "the session keep K must SURVIVE the refused register: []"; ORDER `['preflight', 'mint', 'get_by_key:session:s-order', 'register', 'preflight']`; RS-3 `AgentIdentityConflictError … role ```secretrole``` …` served to carol; RS-5 handler/registry raw-rejection failures. Each is the ruled behaviour missing, not an import/fixture error.
- RS-2 at the checkpoint, 10 invocations: 12,11,14,13,8,13,10,4,10,10 stranded rounds / 20 — **10/10 RED** (author: 6, 4; audit: 2, 8, 11).

## §1 P1 — wrong builds against the REAL contract (the 3 contract files a28 + a19a + a19b, 140 tests, on my reference + one mutation)
Driver: `wb/drive.py` (§A.3) — exactly-once anchors, content backup + md5 restore, observed FAILED ids diffed BOTH ways against a set declared before the run. Every run restored byte-exact (driver receipt).
| W | wrong build (plausible because…) | declared RED | contract result | killed by (my probe) | class |
|---|---|---|---|---|---|
| W1 | (a) guarded delete keyed on the HOUSEHOLD (`len(list_household)<=1`), "created" from the gate's pre-read — the brief's `member_of` variant | seq×2, a19a runtime, KP1, RS-2 | **6 failed** (+RS-5 handler, DV-4) | contract | killed |
| **W2** | (a) compensation ONLY on `RetiredAgentError` — a guard keyed on a refusal class the fixtures never race | ∅ | **140 passed** | K5[retired], K6-class | **MISSING PIN** (P1b: ∀ refusal classes) · LOW plausibility |
| **W3a** | (b) gate first reads the registry via `resolve_holder` (result discarded) — e.g. the #262 notice hoisted | ∅ | **140 passed** | K1 — and, INCIDENTALLY, the full suite (union 2: the same 86 comms tests red with `'FakeAgentRegistry' object has no attribute 'resolve_holder'`) | **MISSING PIN** (P1c: spy reach is a hand-list) · LOW (no served leak; violates the ruled "ZERO registry reads"); suite kill is fixture-shape only — W3c is the clean witness |
| **W3b** | (b) … via a raw `agent_registry._query` | ∅ | **140 passed** | K1 — and, INCIDENTALLY, the full suite: 86 comms tests red with `AttributeError: 'FakeAgentRegistry' object has no attribute '_query'` (a fake-SHAPE kill, not a pin on the property; §1b) | contract survivor; suite-killed for a fixture reason → the property is still unpinned (W3a is the clean witness) |
| **W3c** | (b) … via `get_agent(agent)` WITHOUT a session (→ `_select_rows_by_name`), refusal swallowed — a method the comms FAKES implement (declared after unions 1/2, §1b) | ∅ | **140 passed** + the two fake-based comms files: **1090 passed** | K1 (+K8, same seam spy) | **MISSING PIN** — the clean witness for MP-4 · LOW |
| W4a | (b) the gate mints a DIFFERENT key first (`get_or_create_keyed(key="probe:…")`) | RS-3, ORDER, runtime, CONTROL | **13 failed** | contract | killed |
| W4c | (b) mints-then-deletes on the DENY path only (`create_keep` + `delete_keep`; tables byte-identical after) | ∅ | **140 passed** | K6 foreign leg | NOT A DEFECT (implausible; no surviving side effect) — but RS-3's "tables byte-identical" is a PROXY that cannot see it (§4) |
| W6 | (c) handler-level RS-5 retry; the registry still leaks | RS-5 registry | **1 failed** (exact) | contract | killed — the author's §13-6 prediction CONFIRMED |
| **W7** | (c) catch-ALL `TxnDomainRejectionError`, NO existence re-read — re-enter `register` (whose preflight "re-reads"); the most natural reading of "re-read and take the re-register path" | ∅ | **140 passed** | K2, **K9** | **MISSING PIN** (P1b: RS-5 pinned only for the CONFLICT cause) · MEDIUM — measured: a genuine non-conflict CREATE rejection is served as a raw **`RecursionError` after 928 CREATE attempts** (§A.7). Latent on today's schema (no reachable agent ASSERT), live on any dirty store / future ASSERT (#107's environment). |
| W9 | (b) ORDER gate → MINT → preflight → register (#485 regressed under the new gate) | ORDER, runtime, KP13 | **9 failed** (KP13 stayed green — DV-4) | contract | killed |
| W10 | (b) gate keyed on KEEPER identity, not the household | RS-3 CONTROLS | **1 failed** (exact) | contract | killed |
| W12 | (c) second copy: synthesise `re_registered=True` from the re-read, skipping preflight | RS-5 handler | **1 failed** (exact) — the loser of a DIFFERENT role is served "re-registered … role scout" | contract | killed |
| **W14** | (c) conflict classified by the raw engine TEXT (`'already exists' in str(e.__cause__)`) — routing-not-sharing (#102/#120) | ∅ | **140 passed** | K3, **K9** | **MISSING PIN** · MEDIUM-LOW (silently stops re-reading on an engine rewording) |
| W15 | (c) too-broad class `except SurrealStoreError` (transport = unknown outcome swallowed) | ∅ | **140 passed** | K4 — and the SUITE's `test_retry_seam::…door_enumeration…` (new unlisted CAS door) | contract survivor, SUITE kill → NOT a missing pin in the suite; see W15b |
| **W15b** | (c) W15's scanner-blind sibling: `except (TxnDomainRejectionError, SurrealConnectionError)` (a Tuple handler — the retry-seam scanner keys on `ast.Name`) | ∅ | **140 passed** (retry-seam scanner GREEN, §A.3 kill run) | K4, **K9** | **MISSING PIN** · LOW-MEDIUM (a first register whose response was lost is served "re-registered", capability `None` — the one-time credential is silently gone) |
| W16 | (a/DUAL) household-edge compensation — **degenerate** (quoting SyntaxError; DV-2) | — | collection error (driver: MISMATCH, never a pass) | — | discarded |
| W16b | W16 fixed: raw `DELETE member_of WHERE out = keep:K` on every post-mint refusal | seq×2 | **3 failed** (+RS-5 handler) | contract (the third register is DENIED) + K6 race legs | killed |
| **W18** | (c) a SECOND copy of the idempotency logic that KEEPS the decision (`preflight`) but skips the re-register UPDATE — the loser is served the winner's row | ∅ | **140 passed** | K7, **K9** | **MISSING PIN** · MEDIUM — am-29: "the loser is served exactly what the sequential loser is served … ONE implementation"; the pins check only the `re_registered` flag and the row count, so the loser's own `model` / `task_id` / `cadence` / heartbeat are dropped unseen |
| **W19** | (b) the read-only gate keyed on the caller's visible-keep set being EMPTY (`if not visible_now`) instead of membership of THIS keep; post-mint re-check left correct | ∅ | **140 passed** | **K8** | **MISSING PIN** (P2 fixture monoculture: every foreign principal in RS-3 holds NO keep) · **HIGH** — in production nearly every credentialed principal keeps a session, so W19 re-opens the F-2 leak (role / spawned_by / retirement served to a foreign caller) for almost everyone |
Author's list (§13) items, graded: 1 → §4 RS-2 reach row; 2 → W1 (killed); 3 → W3a/W3b (SURVIVE); 4 → W4a (killed) / W4c (NOT A DEFECT); 5 → the byte-identity axis holds (a per-call value in the denial would RED a correct build, not pass a wrong one; the survivors on that pin are W19's shape, not timing); 6 → W6 killed (confirmed) + W7 SURVIVES (confirmed as a real gap, now measured); 7 → not graded (outside (a)–(d)); 8 → noted, graded only as fold items (§6); 9 → not re-graded (currency is the author's registry; the proxy note stands).

## §2 P1b — QUANTIFIER TABLE (graded invariants)
| # | invariant | ∀-over-inputs or guarded? | receipt |
|---|---|---|---|
| I1 | §F-1: nothing on the register path removes or changes keep state | **GUARDED** — by the debugged cause (a ROLE-conflict race), the created keep, and the `delete_keep` VERB | door W2 (retired-only compensation) SURVIVES; door W16b (edge delete) killed by the third-register leg; door W4c (deny path) SURVIVES (NOT A DEFECT). Lifted: C1 below. |
| I2 | §F-1: the race's winner stays scoped to a LIVE keep; one session keep | ∀ over the RS-2 rig's rows (effect) | W1 / M01-class killed; checkpoint 10/10 RED; sequential twin deterministic |
| I3 | §F-1: the race serves the registry's refusal unaltered | ∀ over the two winner classes (type + text equality) | W1 killed; D5 preserved |
| I4 | §F-2: a foreign principal is denied with ZERO registry reads, byte-identical, no write | **GUARDED** — by the principal SHAPE (holds no keep) and a 3-method spy | doors W19 (HIGH), W3a, W3b SURVIVE; W4a, W10 killed. Lifted: C2 below. |
| I5 | §F-2: ORDER gate → preflight → mint → register | ∀ over {fresh, existing} session | W9 killed; M03 (dummy read) killed by RS-3 |
| I6 | §F-2: the post-mint re-check still denies a keep minted meanwhile | single construction (effect) | author M06 killed |
| I7 | am-29: a legal concurrent register is served the registry's answer, never a store error | **GUARDED** — by the cause (the unique-id conflict) | doors W7 (non-conflict cause → RecursionError), W14 (text), W15b (transport) SURVIVE; W6, W12, W15 killed (W15 by the suite scanner). Lifted: C3 below. |
| I8 | am-29: the loser gets EXACTLY what the sequential second call gets | **GUARDED** — only the `re_registered` flag + row count observed, on identical arguments | door W18 SURVIVES; W12 killed. Lifted: C3. |

### Lifted classes (CLAUDE.md "Fix the CLASS", 2026-09-26) — each missing pin below carries CLASS / SIBLINGS TRIED / NOT TRIED
- **C1 — "∀ register calls (success, ∀ refusal classes, ∀ denial), the keep store's only write is the session-keep mint, and no keep / member_of row that existed before the call is changed or removed."** Domain source of truth: `KeepStore`'s public async verbs (DERIVED by `inspect`), the SAFE set allowlisted (reads + `get_or_create_keyed`), `_query` watched for any non-SELECT; refusal causes = preflight's post-read raise sites (completeness: an AST count of the `raise` statements after `_select_row` in `AgentRegistry.preflight` must equal the parametrised cause count). Enforce at the STATE (before ⊆ after) + the write allowlist, not per door.
- **C2 — "a foreign principal's register issues ZERO agent-registry queries and is served ONE denial, ∀ probe kinds × ∀ foreign-principal shapes {holds no keep, keeps another session, householded elsewhere}."** Domain: the registry's ONE query seam (`AgentRegistry._query` — every registry read rides `run_query` through it); principal shapes enumerated. (Bound: a read on another store connection is outside it.)
- **C3 — "∀ outcomes of the agent CREATE ∈ (DERIVED `SurrealStoreError` subclasses) × {row landed, not}, the registry serves the re-register outcome WITH THIS CALL'S OWN WRITES iff it is the unique-id conflict, else the same error class unchanged after ONE CREATE."** Domain: `vars(loremaster.store._txn)` store-error classes (a new class joins the sweep unedited); `_CONFLICT_CLASS` = the FK-ADV-1 choice.

## MISSING PINS (the tests that should exist + the defect each catches) — every probe pasted VERBATIM in §A.2
| id | the test that should exist | defect it catches | CLASS | SIBLINGS TRIED | SIBLINGS NOT TRIED | severity |
|---|---|---|---|---|---|---|
| MP-1 | **K8** `TestK8AForeignPrincipalWithHerOwnKeepIsStillDenied::test_K8_foreign_probes_by_a_principal_who_keeps_another_session` — RS-3's four probes by a foreign principal who KEEPS another session; same denial, zero registry queries | W19: gate keyed on "caller sees no keep at all" re-opens the F-2 leak for every principal who keeps any session | C2 | W19, W10 (killed), W3a/W3b | a principal householded (not keeper) elsewhere; a gate keyed on keeper-of-ANY-session | **HIGH** |
| MP-2 | **K9** `TestK9EveryCreateOutcomeIsServedAsTheSequentialCallWould::test_K9_create_outcome[<derived class>-<row-landed\|no-row>]` (+ `test_K9_the_derived_error_domain_is_non_vacuous`) — ONE generated pin, 14 cases | W7 (RecursionError after 928 CREATEs), W14 (text-keyed), W15b (transport swallowed), W18 (loser's writes dropped) — all four, measured | C3 | W6, W7, W12, W14, W15, W15b, W18 | `TxnContentionExhaustedError` inside a tuple catch. ⚠ K9 ENCODES a reading: with `_CONFLICT_CLASS = TxnDomainRejectionError` (Reading A) a Reading-B build (keyed on a typed AlreadyExists class) would RED its `TxnDomainRejectionError-row-landed` case — set `_CONFLICT_CLASS` from the FK-ADV-1 ruling before landing it | **MEDIUM** |
| MP-3 | **K7** `TestK7TheRaceLoserIsServedTheSequentialSecondCall::test_K7_the_loser_writes_its_own_mutable_fields` — a deterministic identical-identity race where the loser carries its own model / task_id / cadence; + a sequential control | W18 (and any second copy of the re-register path) | C3 | W12, W18 | a copy that writes model but not cadence (K7 checks all three) | MEDIUM (K9 covers `model`; K7 adds task_id/cadence) |
| MP-4 | **K1** `TestK1TheGateReadsNoRegistryRowThroughANYDoor::test_K1_foreign_probes_issue_zero_registry_queries` — spy `AgentRegistry._query` (the seam) instead of three method names; positive control on a householded register | W3c (survives contract + suite), W3a/W3b (suite-killed only incidentally by fake shapes) — and any future door (`fleet`, `roster`, `_select_rows_by_name`) | C2 | W3a, W3b, W3c | a read on a non-registry connection (principals/governed select) | LOW |
| MP-5 | **K5** `TestK5NoRefusalClassCompensates::test_K5_every_post_mint_refusal_class_leaves_the_keep[role\|spawned_by\|retired]` + **K6** `TestK6NoRegisterPathRemovesOrWritesKeepState` (foreign leg + race legs ∀ refusal classes on a FOUND keep with another householder) | W2 (retired-only compensation — SURVIVES the contract); as hardening: W4c (deny-path transient write) and the DUAL D2 sliver (§5). W16b is already killed by the contract. | C1 | W1, W2, W4a, W4c, W16b | `set_keeper` / `set_rank` on refusal (K6's allowlist would catch — not run) | LOW (W2 implausible) — cheap |
Receipts for every row: §A.3 (declared sets + both-way diffs), kill runs `wb/KILL-*.log` summarised in §A.3.

## §9 Residuals — each with an individual verdict
| # | residual | verdict |
|---|---|---|
| R-1 | RS-2's non-vacuity assertion `refusal_rounds >= 1` counts ANY refusal (pre-mint preflight refusals included), while its docstring promises "every round … met ≥1 refusal (the race ran)" — a message/assertion gap (CLAUDE.md "a failure message that promises a check the assertion does not perform") | LOW — measured reach is fine (post-mint refusal 200/200 rounds, creator refused post-mint 193/200 on my reference, §A.6); cheap fix: count post-mint refusals (a `register` that raises after the mint) and assert `== _ROUNDS` |
| R-2 | no pin requires `keeps.minted_by_this_call` / `_MINTED_BY_THIS_CALL` to be DELETED (am-28 §F-1 "dead and go"); my reference kept it defined-but-unused and passed everything; its docstring would keep claiming "the register handler's created-only compensation reads this" | LOW (dead code + stale production prose) — a builder constraint, or a one-line AST pin "no `minted_by_this_call` in the package" |
| R-3 | am-28's β-bound "trigger before β: a keep found with a keeper and zero scoped rows after a refused register" — nothing measures it; the tokenless CONTROL builds its winner at the REGISTRY (not the handler), so it will stay green after β closes the handler door: it is not a "pin the miss" that reddens when the bound closes | surfaced (rider law: "a trigger nobody measures is a hope"); not a28's to pin unless the sidecar rules it |
| R-4 | stale test prose: `test_fixwave_a19a_63c_i_a.py` module docstring (":14-15 … created-only compensation for the race") and `:581` ("… or a compensated injected …") | cosmetic corpse (§5) |
| R-5 | the guarded-CAS scanner (`test_retry_seam._discover_guarded_cas_handlers`) keys on `ast.Name == "SurrealStoreError"` and a `_select*` re-read prefix: Tuple handlers (W15b) and `except TxnDomainRejectionError` doors are invisible, and `keeps.get_or_create_keyed` (re-reads via `get_by_key`) is already an unlisted door at HEAD | PRE-EXISTING P1c reach bound, not a28's; surfaced for the owner of #102/#120 |
| R-6 | ONE-IMPLEMENTATION: after a28 the tree holds two hand-rolled CAS classifiers that disagree on the class (keeps: `SurrealStoreError − {transport, contention}`; RS-5: `TxnDomainRejectionError`) | escalated with FK-ADV-1 (a typed driver class would give both one predicate) |
| R-7 | the author's watchdog (`guarded.sh`, their §A.2a) kills `pkill -P` (direct children) + the PID — not the whole tree; and its `>> $LOG` line can be overwritten by the run's own non-append writes (I hit both shapes: my first baseline run died with EXIT=143 and no watchdog line, DV-5) | instrument note — my `guarded_tree2.sh` (§A.8) kills every descendant and logs to `<log>.watchdog`, positive control shown |
| R-8 | #502 filed: `lore_search` no response for 300 s | friction, filed |
| R-9 | am-31 claims "Pin (1) grows to the two new fields by `model_fields`, automatically" — false for this contract (hand-listed parametrisation, §6 F-3) | fold item |

## §7 SAT — the contract on MY reference, full suite, ONE tree both ways (2026-09-26, `-n 8`, under `guarded_tree2.sh`)
- Trees: `probe` (my reference: register half = §A.1, migrate half = author's hunks; `loremaster.__file__` = `…/scratchpad/probe/loremaster/loremaster/__init__.py`, scratch_copy provenance ✓) and `base2` (= `probe` rsynced, `uv sync --all-packages`, provenance ✓ `…/scratchpad/base2/loremaster/loremaster/__init__.py`, the five production files `git checkout`-ed; each `git diff --quiet 169925f` ✓). My kill-probe files `--ignore`d in both.
- **base2 (checkpoint production): `283 failed, 11806 passed, 63 skipped, 3 xfailed` (43m46s)** · **probe (my reference): `238 failed, 11851 passed, 63 skipped, 3 xfailed` (37m25s)**. (An earlier base2 attempt was tree-killed by the host-floor reading of the watchdog, DV-5 — no counts taken from it.)
- `comm` over the sorted FAILED ids: **red on the reference only: 0** · **red at base, green on the reference: 45 — byte-identical (`cmp`) to the 45-id RED@checkpoint set of §8** (a28 41 · a19a 2 · a19b 2) · **red in both: 238**.
- The 238 shared reds, by owner: packet 58 (r1 committed `5a43aeb`, r2 `c42eeaf` + untracked/modified r2 files) — `test_supersede_reanchor_58` 44 · `test_reanchor_58_r2_rulings` 27 · `test_task_guarded_shell_58` 15 · `test_reanchor_58_r2_probes` 12 · `test_reanchor_58_r2_cas_runtime` 6 · `test_task_claimable_partition_58` 5 · `test_reanchor_58_r2_am2` 3 · `test_reanchor_58_r2_scale` 2 · `test_task_read_surface` 1 · `test_blocks_edge` 1 · `scripts/test_forgery_door_sweep.py` 3 (modified in the working tree; last commits `c42eeaf`/`5a43aeb` are 58's) = **119** · packet 64b-i (untracked) — `test_governed_substrate_64b` 26 · `test_findings_migrate_64b` 26 · `test_findings_governance_64b` 24 · `test_findings_identity_64b` 22 · `test_findings_schema_64b` 17 · `test_findings_enforcement_64b` 4 = **119**. **63c-attributable on the reference: 0.** #503 (`test_migration_wire`) did NOT appear in either run; no #486 shape seen.
- ⚠ **P0, self-caught:** my first "same failure text on both trees" check compared the `-rf` summary messages of a `--tb=no` run — 228 of 238 were EMPTY, so it was vacuous (it "passed" 238/238). Second attempt (`--tb=line -rf`) was STILL vacuous (10/238 messages): pytest truncates each `-rf` line to the terminal width (80 in a pipe), so long node ids drop their message. Third attempt with `COLUMNS=4000`: **238/238 carry a message on both trees** (the control), same 238 ids (`cmp` ✓), `238 failed, 399 passed, 2 skipped` over the 17 files on each tree. **221 messages identical after normalisation; 17 differ, each adjudicated:** 14 (packet 58: `test_supersede_reanchor_58` ×10, `test_reanchor_58_r2_rulings` ×2, `_probes` ×1, `_scale` ×1) differ only in per-run random ids / secrets (hex/base64 runs my normaliser did not mask) — same shape; 3 (packet 64b) show the am-30 migrate half in their text but fail for 64b's own unbuilt reasons on BOTH trees: `test_findings_migrate_64b::…CONTROL_without_the_trap…[finding]` (repr gains `preconditions=None`), `…trap_refuses_byte_inert…[memory]` (repr gains `preconditions=MigratePreconditionCounts(…)`; `--table memory` PROCEEDS past owned-but-unscoped rows on both), `test_governed_substrate_64b::…resource_from_row_is_the_only_production_Resource_constructor` (the same pre-existing site `governed.py::authorize_guarded`, line 493 → 513: am-30's model inserted above it). **No shared red changes shape because of the 63c build.**
- The author's claim (reference 207F / base 252F, 0 reference-only, 45 fixed): my counts differ in the SHARED set only (238 vs 207 — the tree moved: 58-r2 grew from ~86 to 119 shared reds, `test_ast_reach_helpers` / `test_secret_typing` no longer red); **0 reference-only and the identical 45 reproduce.** SAT holds for the graded surface on an INDEPENDENT register-half build.

## §1b Full-suite receipts for the survivors (union builds; the same `ref` tree content as `probe`, rsync-verified 0 diffs, provenance ✓)
- **Union 1** = W2 + W3b + W19 (server.py) + W7 + W15b + W18 (agents.py), declared 16:23:25 (`wb/combo.py`): `324 failed, 11765 passed, 63 skipped, 3 xfailed` (43m30s). vs my reference's 238: **86 extra reds, ALL `AttributeError: '<Fake|_Recording>AgentRegistry' object has no attribute '_query'`** in `test_comms_tool.py` / `test_comms_render_architecture.py` (re-run of the two files with `COLUMNS=4000`: 82 + 1 + 3 = 86 of that one shape) — W3b's raw `_query` on the fakes. No other extra red; 0 reference reds went green.
- **Union 2** = W2 + **W3a** + W19 + W7 + W15b + W18, declared 17:27:17 (`wb/combo2.py`): `324 failed, 11765 passed, 63 skipped, 3 xfailed` (18m05s) — the SAME 86 extra ids (`cmp` ✓), now all `AttributeError: '<Fake|_Recording>AgentRegistry' object has no attribute 'resolve_holder'` (82 + 1 + 3). So both unions die ONLY on the comms fakes' missing attributes — incidental, and it proves the rest of the suite is blind to W2, W19, W7, W15b, W18.
- **Union 3** = W2 + **W3c** + W19 + W7 + W15b + W18, declared 17:49:53 (`wb/combo3.py`): **`238 failed, 11851 passed, 63 skipped, 3 xfailed` (17m08s) — the red set is IDENTICAL to my correct reference's (`comm`: 0 extra, 0 fewer).** ⇒ **W2, W3c, W19, W7, W15b and W18 each pass the ENTIRE suite**, not just the contract. (Tree restored byte-exact afterwards; `cmp` vs `probe` ✓.)
- Not in a union (anchors overlap): W14 (text-keyed), W4c (deny-path write) — targeted receipts only: the 140 contract pins + `test_retry_seam.py` (674 with the kill file, §A.3g/§A.3h) green except the declared kill probe.

## §A.4 DRY ledger (scratch-only test helpers in the kill probes — none is production)
| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `_spy_registry_queries` (K1/K8) | `lore_search("shared helper … re-read the row …")` | **no response 300 s → #502**; fallback awk | HAND-ROLLED — a28's `_count_calls` wraps a named method; this wraps the ONE seam `_query` |
| `_arm_keep_write_spy`, `_KEEP_SAFE_VERBS`, `_keep_rows` (K6) | (same outage) | — | HAND-ROLLED; REUSES a28 `_spy_delete_keep` / `_session_keep_ids` / `_alice_keeps_a_session` / `_FOREIGN_PROBES` / `_outcome` / `_bare` by module import (never cloned) |
| `_forge`, `_STORE_ERROR_CLASSES`, `_CONFLICT_CLASS` (K9) | — | a28 `_forge` exists with a DIFFERENT meaning (an answer-shape forgery) | HAND-ROLLED; ⚠ a fold landing K9 inside a28 must RENAME it (name collision) |


## §A Instruments (VERBATIM — the scratch trees are disposable by design)
### §A.1 `myref.py` — MY independent reference for the REGISTER half (applied on top of the author's migrate-half hunks); resulting register-half diff md5 `f4983ab612ba22864d6bb5cc4324a04e` — md5 `7bd8478c117c8dfa78c80d9e8ddf7ef0`
```python
"""My independent reference for amendments 28 (§F-1, §F-2) + 29 (RS-5): the register half."""
import pathlib, sys
root = pathlib.Path(sys.argv[1])

def sub(path, old, new, count=1):
    p = root / path
    text = p.read_text()
    assert text.count(old) == count, (path, old[:80], text.count(old))
    p.write_text(text.replace(old, new))

server = "loremaster/loremaster/server.py"
# 1. read-only SF-63-1 gate BEFORE preflight (am-28 §F-2)
sub(server, """        await self.agent_registry.preflight(
            agent,
            session=session,
            role=role,
            spawned_by=spawned_by,
            owner_principal_id=principal_bare,
        )
        minted_session_keep = False
        keep_store = self._keep_store
""", """        keep_store = self._keep_store
        from loremaster.visible_keeps import resolve_visible_keeps  # noqa: PLC0415

        def _foreign_denial() -> governed.GovernedDenied:
            return governed.GovernedDenied(
                f"session {session!r} is kept by another principal — you are not householded in "
                "it; its keeper must run `lore-adm add-household` for you before you register "
                "into this session"
            )

        if principal is not None and keep_store is not None:
            # amendment 28 §F-2: the READ-ONLY SF-63-1 gate, BEFORE any registry read.
            existing_keep = await keep_store.get_by_key(f"session:{session}")
            if existing_keep is not None:
                existing_bare = str(existing_keep.id).split(":", 1)[-1]
                visible_now = await resolve_visible_keeps(keep_store, member_email=principal.email)
                if keep_scope(existing_bare) not in visible_now:
                    raise _foreign_denial()
        await self.agent_registry.preflight(
            agent,
            session=session,
            role=role,
            spawned_by=spawned_by,
            owner_principal_id=principal_bare,
        )
""")
sub(server, """            from loremaster.keeps import minted_by_this_call  # noqa: PLC0415
            from loremaster.visible_keeps import resolve_visible_keeps  # noqa: PLC0415

            # "created" comes from the mint's OWN return (amendment 24 FK-b) — never a pre-read,
            # which a concurrent winner would turn into a TOCTOU.
            minted_session_keep = minted_by_this_call(session_keep)
            session_keep_bare""", """            session_keep_bare""")
sub(server, """            if keep_scope(session_keep_bare) not in visible:
                raise governed.GovernedDenied(
                    f"session {session!r} is kept by another principal — you are not householded in "
                    "it; its keeper must run `lore-adm add-household` for you before you register "
                    "into this session"
                )
""", """            if keep_scope(session_keep_bare) not in visible:
                raise _foreign_denial()
""")
# 2. delete the compensation (am-28 §F-1)
old_start = "        try:\n            result = await self.agent_registry.register(\n"
p = root / server
text = p.read_text()
i = text.index(old_start)
j = text.index("            raise\n        now = datetime.now(UTC)\n", i)
block = text[i:j + len("            raise\n")]
new_block = """        result = await self.agent_registry.register(
            agent,
            session=session,
            role=role,
            model=model,
            spawned_by=spawned_by,
            task_id=task_id,
            cadence=cadence,
            owner_principal_id=principal_bare,
            session_keep_id=session_keep_bare,
        )
"""
p.write_text(text[:i] + new_block + text[j + len("            raise\n"):])

# 3. keeps.py: minted_by_this_call is dead
keeps = "loremaster/loremaster/keeps.py"
sub(keeps, """            # THIS call's CREATE won the mint — reported on the returned object, read through
            # :func:`minted_by_this_call` (the register handler's created-only compensation, #485).
            object.__setattr__(created, _MINTED_BY_THIS_CALL, True)
""", "")

# 4. agents.py RS-5 (am-29): the CREATE's unique-id rejection re-reads and takes the re-register path
agents = "loremaster/loremaster/agents.py"
sub(agents, "    TxnContentionExhaustedError,\n    _SurrealConnection,", "    TxnContentionExhaustedError,\n    TxnDomainRejectionError,\n    _SurrealConnection,")
sub(agents, """            await self._query(
                f"CREATE type::record('{AGENT_TABLE}', ${_ROW_ID_PARAM}) "
                f"CONTENT ${_ROW_CONTENT_PARAM}",
                {_ROW_ID_PARAM: agent_id, _ROW_CONTENT_PARAM: content},
            )
""", """            try:
                await self._query(
                    f"CREATE type::record('{AGENT_TABLE}', ${_ROW_ID_PARAM}) "
                    f"CONTENT ${_ROW_CONTENT_PARAM}",
                    {_ROW_ID_PARAM: agent_id, _ROW_CONTENT_PARAM: content},
                )
            except TxnDomainRejectionError:
                # amendment 29 RS-5: a concurrent identical first register won the CREATE. If the row
                # now EXISTS that IS the conflict -> the registry's own re-register path (preflight
                # decides a differing role/spawned_by). Otherwise the rejection was genuine -> raise.
                if await self._select_row(agent_id) is None:
                    raise
                return await self.register(
                    name,
                    session=session,
                    role=role,
                    model=model,
                    spawned_by=spawned_by,
                    task_id=task_id,
                    cadence=cadence,
                    owner_principal_id=owner_principal_id,
                    session_keep_id=session_keep_id,
                )
""")
print("ok")
```
### §A.2 `test_adv_a28_kill_probes.py` — K1–K9, the kill probes / candidate missing pins (28 passed on my reference, 2026-09-26 ~16:30) — md5 `6b8ec7f0ea371b11c8119f6b4c531c4e`
```python
"""adversary-63c-i-a-a28 kill probes — candidate MISSING PINS for the a28 contract (scratch only, never in the repo).

K1 (P1c, RS-3 reach): the zero-registry-reads spy counts the registry's ONE query seam (``AgentRegistry._query``),
   not a hand-list of three methods. Positive control: the same spy SEES a householded register's reads.
K2 (P1b, RS-5 quantifier): a GENUINE non-conflict CREATE rejection (no row exists after it) is re-raised as the
   store's typed rejection, after exactly ONE CREATE attempt — never re-entered, never recursed.
K3 (routing-not-sharing, RS-5): the conflict is classified by CLASS + existence, never by the engine's text:
   a conflict whose cause text is REWORDED still takes the re-register path.
K4 (RS-5 class breadth): a transport failure on the CREATE (an UNKNOWN outcome — the row may have landed) is
   never swallowed into a re-register; ``SurrealConnectionError`` propagates.
K5 (P1b, §F-1 quantifier): ∀ post-mint refusal classes (role, spawned_by, retired), the race never deletes the
   keep and the winner's scope stays live.
"""

from __future__ import annotations

from typing import Any

import pytest
import test_fixwave_a28_63c_i_a as a28
from _governed_contract import credentialed_app_context
from _surreal_harness import run
from loremaster.agents import (
    AgentIdentityConflictError,
    AgentRegistryError,
    RetiredAgentError,
)
from loremaster.governed import GovernedDenied
from loremaster.store._txn import SurrealConnectionError, TxnDomainRejectionError
from lorerunes.pdp import keep_scope

_DIM = a28._DIM


def _spy_registry_queries(monkeypatch: pytest.MonkeyPatch, registry: Any) -> list[str]:
    seen: list[str] = []
    real = registry._query

    async def counting(statement: str, params: Any = None) -> Any:
        seen.append(statement)
        return await real(statement, params)

    monkeypatch.setattr(registry, "_query", counting)
    return seen


class TestK1TheGateReadsNoRegistryRowThroughANYDoor:
    async def test_K1_foreign_probes_issue_zero_registry_queries(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member", "carol": "member", "bob": "member"}, dim=_DIM
        ) as world:
            ctx, admin_conn = world["ctx"], world["admin_conn"]
            session = "s-alice"
            await a28._alice_keeps_a_session(ctx, world, session)
            keep_bare = a28._bare((await a28._session_keep_ids(admin_conn, session))[0])
            await ctx._keep_store.add_household_member(keep_id=keep_bare, member_email=world["emails"]["bob"])
            seen = _spy_registry_queries(monkeypatch, ctx.agent_registry)
            world["holder"]["email"] = world["emails"]["carol"]
            for probe in a28._FOREIGN_PROBES.values():
                with pytest.raises(GovernedDenied):
                    await ctx.comms(action="register", session=session, **probe)
            assert seen == [], f"a foreign register read the registry before the gate denied it: {seen!r}"
            # POSITIVE CONTROL: the spy SEES registry reads on a householded register.
            world["holder"]["email"] = world["emails"]["bob"]
            await ctx.comms(action="register", agent="bobagent", session=session, role="builder")
            assert seen, "CONTROL: the _query spy saw nothing on a householded register — the probe is blind"


class TestK2AGenuineCreateRejectionIsRaisedOnce:
    async def test_K2_a_non_conflict_CREATE_rejection_is_re_raised_after_one_attempt(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM) as world:
            ctx, admin_conn = world["ctx"], world["admin_conn"]
            registry = ctx.agent_registry
            real = registry._query
            creates = {"n": 0}

            async def forging(statement: str, params: Any = None) -> Any:
                if statement.startswith("CREATE"):
                    creates["n"] += 1
                    if creates["n"] > 3:  # stop a recursing build quickly; the count is the verdict
                        raise RuntimeError("K2: CREATE re-attempted >3x — the registry re-entered on a genuine rejection")
                    raise TxnDomainRejectionError("K2 forged: a genuine NON-conflict domain rejection of the CREATE")
                return await real(statement, params)

            monkeypatch.setattr(registry, "_query", forging)
            with pytest.raises(Exception) as caught:
                await registry.register("k2agent", session="s-k2", role="builder")
            assert type(caught.value) is TxnDomainRejectionError and creates["n"] == 1, (
                f"a genuine CREATE rejection must surface as the store's typed rejection after ONE attempt: "
                f"{type(caught.value).__name__}: {caught.value} (CREATE attempts: {creates['n']})"
            )
            assert await run(admin_conn, "SELECT VALUE name FROM agent WHERE session = 's-k2'") == []
            # CONTROL: unforged, the same register succeeds.
            monkeypatch.setattr(registry, "_query", real)
            result = await registry.register("k2agent", session="s-k2", role="builder")
            assert result.re_registered is False


class TestK3TheConflictIsClassifiedByClassNotText:
    async def test_K3_a_reworded_conflict_still_takes_the_re_register_path(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM) as world:
            ctx = world["ctx"]
            registry = ctx.agent_registry
            real = registry._query
            fired = {"n": 0}

            async def winner_then_reworded_conflict(statement: str, params: Any = None) -> Any:
                if statement.startswith("CREATE") and fired["n"] == 0:
                    fired["n"] += 1
                    await real(statement, params)  # an IDENTICAL concurrent winner's CREATE lands first
                    try:
                        raise RuntimeError("K3: the engine reworded its unique-id conflict")
                    except RuntimeError as cause:
                        raise TxnDomainRejectionError("SurrealDB agent query rejected (unspecified)") from cause
                return await real(statement, params)

            monkeypatch.setattr(registry, "_query", winner_then_reworded_conflict)
            result = await registry.register("k3agent", session="s-k3", role="builder")
            assert fired["n"] == 1 and result.re_registered is True, (fired, result)


class TestK4ATransportFailureIsNeverAReRegister:
    async def test_K4_a_connection_error_on_CREATE_propagates(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM) as world:
            ctx = world["ctx"]
            registry = ctx.agent_registry
            real = registry._query
            fired = {"n": 0}

            async def commit_then_lose_the_response(statement: str, params: Any = None) -> Any:
                if statement.startswith("CREATE") and fired["n"] == 0:
                    fired["n"] += 1
                    await real(statement, params)  # the CREATE LANDED; the response is lost
                    raise SurrealConnectionError("K4 forged: socket dropped after the CREATE committed")
                return await real(statement, params)

            monkeypatch.setattr(registry, "_query", commit_then_lose_the_response)
            with pytest.raises(Exception) as caught:
                outcome = await registry.register("k4agent", session="s-k4", role="builder")
                pytest.fail(f"a transport failure was swallowed into {outcome!r} (capability={outcome.capability!r})")
            assert type(caught.value) is SurrealConnectionError, repr(caught.value)


class TestK5NoRefusalClassCompensates:
    @pytest.mark.parametrize("refusal", ["role", "spawned_by", "retired"])
    async def test_K5_every_post_mint_refusal_class_leaves_the_keep(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any, refusal: str
    ) -> None:
        async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM) as world:
            ctx, admin_conn = world["ctx"], world["admin_conn"]
            world["holder"]["email"] = world["emails"]["alice"]
            session = f"s-k5-{refusal}"
            keep_store = ctx._keep_store
            real_mint = keep_store.get_or_create_keyed
            calls = {"mint": 0}
            x_role, x_spawned = "builder", "leadx"
            winner_kwargs = {
                "role": dict(role="auditor", spawned_by=x_spawned),
                "spawned_by": dict(role=x_role, spawned_by="leadother"),
                "retired": dict(role=x_role, spawned_by=x_spawned),
            }[refusal]

            async def racing_mint(*args: Any, **kwargs: Any) -> Any:
                calls["mint"] += 1
                keep = await real_mint(*args, **kwargs)
                if calls["mint"] == 1:
                    await ctx.comms(action="register", agent="a", session=session, **winner_kwargs)
                    if refusal == "retired":
                        await ctx.agent_registry.touch("a", session=session, status="retired")
                return keep

            monkeypatch.setattr(keep_store, "get_or_create_keyed", racing_mint)
            deletes = a28._spy_delete_keep(monkeypatch, ctx)
            with pytest.raises(AgentRegistryError) as caught:
                await ctx.comms(action="register", agent="a", session=session, role=x_role, spawned_by=x_spawned)
            expected = RetiredAgentError if refusal == "retired" else AgentIdentityConflictError
            assert type(caught.value) is expected, repr(caught.value)
            keeps = await a28._session_keep_ids(admin_conn, session)
            scopes = await run(admin_conn, f"SELECT VALUE scope FROM agent WHERE session = '{session}' AND name = 'a'")
            assert len(keeps) == 1 and scopes == [keep_scope(a28._bare(keeps[0]))], (keeps, scopes)
            assert deletes["count"] == 0, deletes


# --------------------------------------------------------------------------------------------------------------
# K6 — the LIFTED property for (a)+(b): during ANY register call — foreign denial or post-mint race refusal, ∀
# refusal classes — the keep store performs NO write but the session-keep mint, and no keep / member_of row that
# existed before the call is absent or changed after it. Domain: KeepStore's public async verbs, DERIVED by
# inspection; the SAFE set is allowlisted (reads + the mint); ``_query`` is watched for any non-SELECT statement.
# --------------------------------------------------------------------------------------------------------------
import inspect  # noqa: E402

_KEEP_SAFE_VERBS = frozenset({"get_by_key", "get_keep", "list_keeps_for_member", "list_household",
                              "list_keeps_for_keeper", "get_or_create_keyed"})


def _arm_keep_write_spy(monkeypatch: pytest.MonkeyPatch, keep_store: Any) -> list[str]:
    seen: list[str] = []
    verbs = [name for name, member in inspect.getmembers(type(keep_store), inspect.iscoroutinefunction)
             if not name.startswith("_")]
    assert "delete_keep" in verbs and "get_by_key" in verbs, f"derivation broken: {verbs}"
    for name in verbs:
        real = getattr(keep_store, name)

        async def wrapped(*args: Any, __name: str = name, __real: Any = real, **kwargs: Any) -> Any:
            seen.append(__name)
            return await __real(*args, **kwargs)

        monkeypatch.setattr(keep_store, name, wrapped)
    real_query = keep_store._query

    async def watched(statement: str, params: Any = None) -> Any:
        if not statement.lstrip().upper().startswith("SELECT"):
            seen.append(f"_query:{statement.split()[0]}")
        return await real_query(statement, params)

    monkeypatch.setattr(keep_store, "_query", watched)
    return seen


async def _keep_rows(admin_conn: Any) -> list[Any]:
    return [await run(admin_conn, "SELECT * FROM keep ORDER BY id"), await run(admin_conn, "SELECT * FROM member_of ORDER BY id")]


class TestK6NoRegisterPathRemovesOrWritesKeepState:
    async def test_K6_foreign_denials_write_nothing_to_the_keep_store(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
        async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member", "carol": "member"}, dim=_DIM) as world:
            ctx = world["ctx"]
            await a28._alice_keeps_a_session(ctx, world, "s-alice")
            seen = _arm_keep_write_spy(monkeypatch, ctx._keep_store)
            world["holder"]["email"] = world["emails"]["carol"]
            for probe in a28._FOREIGN_PROBES.values():
                with pytest.raises(GovernedDenied):
                    await ctx.comms(action="register", session="s-alice", **probe)
            unsafe = [name for name in seen if name not in _KEEP_SAFE_VERBS or name == "get_or_create_keyed"]
            assert not unsafe, f"a foreign denial touched the keep store beyond reads: {unsafe}"
            # CONTROL: the spy SEES a write verb.
            world["holder"]["email"] = world["emails"]["carol"]
            await ctx.comms(action="register", agent="carols", session="s-carol", role="builder")
            assert "get_or_create_keyed" in seen, "CONTROL: the spy is blind to the mint"

    @pytest.mark.parametrize("refusal", ["role", "spawned_by", "retired"])
    async def test_K6_a_race_refusal_removes_no_keep_state(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any, refusal: str) -> None:
        async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member", "bob": "member"}, dim=_DIM) as world:
            ctx, admin_conn = world["ctx"], world["admin_conn"]
            world["holder"]["email"] = world["emails"]["alice"]
            session = f"s-k6-{refusal}"
            await ctx.comms(action="register", agent="first", session=session, role="builder")  # K pre-exists (FOUND)
            keep_bare = a28._bare((await a28._session_keep_ids(admin_conn, session))[0])
            await ctx._keep_store.add_household_member(keep_id=keep_bare, member_email=world["emails"]["bob"])
            winner_kwargs = {"role": dict(role="auditor", spawned_by="leadx"),
                             "spawned_by": dict(role="builder", spawned_by="leadother"),
                             "retired": dict(role="builder", spawned_by="leadx")}[refusal]
            real_mint = ctx._keep_store.get_or_create_keyed
            fired = {"n": 0}
            snapshot: dict[str, Any] = {}

            async def racing_mint(*args: Any, **kwargs: Any) -> Any:
                keep = await real_mint(*args, **kwargs)
                fired["n"] += 1
                if fired["n"] == 1:
                    await ctx.comms(action="register", agent="a", session=session, **winner_kwargs)
                    if refusal == "retired":
                        await ctx.agent_registry.touch("a", session=session, status="retired")
                    snapshot["before"] = await _keep_rows(admin_conn)
                return keep

            monkeypatch.setattr(ctx._keep_store, "get_or_create_keyed", racing_mint)
            seen = _arm_keep_write_spy(monkeypatch, ctx._keep_store)
            with pytest.raises(AgentRegistryError):
                await ctx.comms(action="register", agent="a", session=session, role="builder", spawned_by="leadx")
            after = await _keep_rows(admin_conn)
            assert after == snapshot["before"], "a refused register changed keep / household state"
            unsafe = [name for name in seen if name not in _KEEP_SAFE_VERBS]
            assert not unsafe, f"a refused register wrote to the keep store beyond the mint: {unsafe}"


# --------------------------------------------------------------------------------------------------------------
# K7 — the LIFTED RS-5 property: the loser of a concurrent identical first register is served EXACTLY what the
# SEQUENTIAL second call is served (amendment 29) — including its own mutable-on-provided writes (model, task_id,
# cadence). A deterministic race: the winner's complete register runs inside the loser's CREATE seam, then the
# loser's CREATE meets the REAL engine conflict. Control: the sequential second call, same arguments.
# --------------------------------------------------------------------------------------------------------------
class TestK7TheRaceLoserIsServedTheSequentialSecondCall:
    async def test_K7_the_loser_writes_its_own_mutable_fields(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
        async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM) as world:
            ctx, admin_conn = world["ctx"], world["admin_conn"]
            registry = ctx.agent_registry
            real_query = registry._query
            fired = {"n": 0}
            loser_args = dict(role="builder", model="m-loser", task_id="t-loser", cadence="≤5m")

            async def winner_first(statement: str, params: Any = None) -> Any:
                if statement.startswith("CREATE") and fired["n"] == 0:
                    fired["n"] += 1
                    await registry.register("k7agent", session="s-k7", role="builder", model="m-winner",
                                            task_id="t-winner", cadence="≤1m")
                return await real_query(statement, params)

            monkeypatch.setattr(registry, "_query", winner_first)
            raced = await registry.register("k7agent", session="s-k7", **loser_args)
            row = (await run(admin_conn, "SELECT model, task_id, declared_cadence FROM agent WHERE session = 's-k7'"))
            assert fired["n"] == 1 and raced.re_registered is True, (fired, raced)
            assert (raced.agent.model, raced.agent.task_id, raced.agent.declared_cadence) == ("m-loser", "t-loser", "≤5m"), raced.agent
            assert row == [{"model": "m-loser", "task_id": "t-loser", "declared_cadence": "≤5m"}], row
            # CONTROL: the sequential second call with the same arguments serves the same thing.
            monkeypatch.setattr(registry, "_query", real_query)
            await registry.register("k7seq", session="s-k7s", role="builder", model="m-winner", task_id="t-winner", cadence="≤1m")
            sequential = await registry.register("k7seq", session="s-k7s", **loser_args)
            assert (sequential.re_registered, sequential.agent.model, sequential.agent.task_id,
                    sequential.agent.declared_cadence) == (True, "m-loser", "t-loser", "≤5m"), sequential


# --------------------------------------------------------------------------------------------------------------
# K8 — P2 perturbation of RS-3's fixture: the foreign principal KEEPS ANOTHER SESSION of her own (so her visible
# keep set is NON-EMPTY). The four probes must still be the same GovernedDenied with zero registry queries.
# --------------------------------------------------------------------------------------------------------------
class TestK8AForeignPrincipalWithHerOwnKeepIsStillDenied:
    async def test_K8_foreign_probes_by_a_principal_who_keeps_another_session(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
        async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member", "carol": "member"}, dim=_DIM) as world:
            ctx = world["ctx"]
            await a28._alice_keeps_a_session(ctx, world, "s-alice")
            world["holder"]["email"] = world["emails"]["carol"]
            await ctx.comms(action="register", agent="carols", session="s-carol", role="builder")  # carol keeps s-carol
            seen = _spy_registry_queries(monkeypatch, ctx.agent_registry)
            served = {label: await a28._outcome(ctx.comms(action="register", session="s-alice", **probe))
                      for label, probe in a28._FOREIGN_PROBES.items()}
            assert {kind for kind, _t in served.values()} == {GovernedDenied.__name__}, served
            assert len({text for _k, text in served.values()}) == 1, served
            assert seen == [], seen


# --------------------------------------------------------------------------------------------------------------
# K9 — the LIFTED RS-5 pin, GENERATED over its domain: ∀ store-error class the agent CREATE can raise (DERIVED:
# every ``SurrealStoreError`` subclass in ``loremaster.store._txn``) × {the row LANDED before the raise, it did
# not}: the registry serves the re-register outcome (with THIS call's own writes) iff the error is the unique-id
# CONFLICT class AND the row exists; otherwise the SAME error class propagates unchanged after exactly ONE CREATE
# attempt. ``_CONFLICT_CLASS`` is the fold's choice (FK-ADV-1): Reading A = ``TxnDomainRejectionError`` (today's
# contract §10 item 3); Reading B = the typed class the driver would mint from the SDK's ``AlreadyExistsError``.
# Completeness: a NEW store-error class joins the sweep without editing this pin (the derivation), and the
# non-vacuity leg asserts the derived set is non-empty and contains both sides of the partition.
# --------------------------------------------------------------------------------------------------------------
import loremaster.store._txn as _txn_module  # noqa: E402

_CONFLICT_CLASS = TxnDomainRejectionError
_STORE_ERROR_CLASSES = sorted(
    (member for member in vars(_txn_module).values()
     if inspect.isclass(member) and issubclass(member, _txn_module.SurrealStoreError)),
    key=lambda member: member.__name__,
)


def _forge(error_class: type[Exception]) -> Exception:
    if error_class is _txn_module.TxnContentionExhaustedError:
        return error_class("K9 forged", attempts=1, elapsed_seconds=0.0)
    return error_class("K9 forged")


def test_K9_the_derived_error_domain_is_non_vacuous() -> None:
    names = {member.__name__ for member in _STORE_ERROR_CLASSES}
    assert _CONFLICT_CLASS.__name__ in names and "SurrealConnectionError" in names and len(names) >= 5, names


class TestK9EveryCreateOutcomeIsServedAsTheSequentialCallWould:
    @pytest.mark.parametrize("landed", [True, False], ids=["row-landed", "no-row"])
    @pytest.mark.parametrize("error_class", _STORE_ERROR_CLASSES, ids=lambda member: member.__name__)
    async def test_K9_create_outcome(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any,
                                     error_class: type[Exception], landed: bool) -> None:
        async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM) as world:
            registry = world["ctx"].agent_registry
            real_query = registry._query
            creates = {"n": 0}

            async def forging(statement: str, params: Any = None) -> Any:
                if statement.startswith("CREATE"):
                    creates["n"] += 1
                    if creates["n"] > 2:
                        raise RuntimeError("K9: CREATE re-attempted — the registry re-entered on a forged error")
                    if creates["n"] == 1:
                        if landed:  # an identical winner's row lands first (a DIFFERENT model, so the write shows)
                            await real_query(statement, {**(params or {}), "content": {
                                **(params or {})["content"], "model": "m-winner"}})
                        raise _forge(error_class)
                return await real_query(statement, params)

            monkeypatch.setattr(registry, "_query", forging)
            outcome: Any
            try:
                outcome = await registry.register("k9agent", session="s-k9", role="builder", model="m-self")
            except Exception as error:  # noqa: BLE001 - the pin classifies what is served
                outcome = error
            conflict = issubclass(error_class, _CONFLICT_CLASS) and landed
            if conflict:
                assert not isinstance(outcome, Exception) and outcome.re_registered is True, repr(outcome)
                assert outcome.agent.model == "m-self", f"the re-register must carry THIS call's writes: {outcome.agent!r}"
            else:
                assert type(outcome) is error_class and creates["n"] == 1, (
                    f"{error_class.__name__} (landed={landed}) must propagate unchanged after ONE CREATE: "
                    f"{type(outcome).__name__}: {outcome!r} (CREATE attempts {creates['n']})")
```
### §A.3a `wb/builds.py` — every wrong build (file / anchor / replacement) + DECLARED sets (declared_at 15:49:26, 16:03:14, 16:10:17, 16:11:09, 16:13:51, 16:16:00) — md5 `f0fc8a9b1af6e48da2aca69135aa54ee`
```python
"""Wrong builds W* (adversary-63c-i-a-a28). Each: file, anchor (must match exactly once in MY reference), replacement.
Declared RED sets are in DECLARED (written before any run)."""
A28 = "loremaster/tests/test_fixwave_a28_63c_i_a.py"
A19A = "loremaster/tests/test_fixwave_a19a_63c_i_a.py"
A19B = "loremaster/tests/test_fixwave_a19b_63c_i_a.py"
RACE = f"{A28}::TestTheRaceNeverStrandsAScope63cIAa28"
RS5 = f"{A28}::TestAConcurrentIdenticalRegisterIsIdempotent63cIAa28"
RS3 = f"{A28}::TestAForeignPrincipalLearnsNothingBeforeTheGate63cIAa28"
SEQ_H = f"{RACE}::test_the_sequential_race_keeps_the_keep_and_serves_the_teaching[handler-winner-found-the-keep]"
SEQ_T = f"{RACE}::test_the_sequential_race_keeps_the_keep_and_serves_the_teaching[tokenless-winner-control]"
RS2 = f"{RACE}::test_RS2_eight_way_registers_never_strand_a_scope"
RS5H = f"{RS5}::test_RS5_every_handler_caller_gets_a_registry_answer_never_an_engine_error"
RS5R = f"{RS5}::test_RS5_eight_identical_first_registers_all_succeed_at_the_registry"
RS3P = f"{RS3}::test_RS3_every_foreign_probe_is_the_same_denial_with_zero_registry_reads"
RS3C = f"{RS3}::test_RS3_CONTROLS_a_householded_member_proceeds_and_the_keeper_is_still_taught"
ORDER = f"{RS3}::test_the_handler_ORDER_is_gate_then_preflight_then_mint_then_register"
POSTMINT = f"{RS3}::test_the_POST_MINT_recheck_denies_a_keep_minted_meanwhile_by_another_principal"
RUNTIME = f"{A19A}::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_EVERY_driven_register_meets_the_runtime_property"
KP1 = f"{A19B}::test_KP1_a_keep_won_by_a_concurrent_mint_is_never_compensated"
KP13 = f"{A19B}::test_KP13_a_register_refused_on_a_cadence_conflict_mints_nothing"

S = "loremaster/loremaster/server.py"
G = "loremaster/loremaster/agents.py"

REGISTER_CALL = """        result = await self.agent_registry.register(
            agent,
            session=session,
            role=role,
            model=model,
            spawned_by=spawned_by,
            task_id=task_id,
            cadence=cadence,
            owner_principal_id=principal_bare,
            session_keep_id=session_keep_bare,
        )
"""

def _compensating(guard: str) -> str:
    return f"""        try:
            result = await self.agent_registry.register(
                agent,
                session=session,
                role=role,
                model=model,
                spawned_by=spawned_by,
                task_id=task_id,
                cadence=cadence,
                owner_principal_id=principal_bare,
                session_keep_id=session_keep_bare,
            )
        except _AgentRegistryError as refusal:
            if session_keep_bare is not None and keep_store is not None and existing_keep is None:
                household = await keep_store.list_household(session_keep_bare)
                if {guard}:
                    await keep_store.delete_keep(keep_id=session_keep_bare)
            raise
"""

GATE_HEAD = "        if principal is not None and keep_store is not None:\n            # amendment 28 §F-2: the READ-ONLY SF-63-1 gate, BEFORE any registry read.\n"
PREFLIGHT = """        await self.agent_registry.preflight(
            agent,
            session=session,
            role=role,
            spawned_by=spawned_by,
            owner_principal_id=principal_bare,
        )
        if principal is not None:
"""
MINT_TAIL = "            kept_by_me = session_keep.keeper_id == principal_bare\n"
EXIST_CHECK = "                if await self._select_row(agent_id) is None:\n                    raise\n"
REENTER = """                return await self.register(
                    name,
                    session=session,
                    role=role,
                    model=model,
                    spawned_by=spawned_by,
                    task_id=task_id,
                    cadence=cadence,
                    owner_principal_id=owner_principal_id,
                    session_keep_id=session_keep_id,
                )
"""
BUILDS = {
    # (a) guarded delete keyed on the HOUSEHOLD (not scoped rows); "created" from the gate's pre-read.
    "W1": (S, REGISTER_CALL, _compensating("len(household) <= 1")),
    # (a) ∀-refusal-class door: compensate ONLY on a RetiredAgentError (unguarded otherwise).
    "W2": (S, REGISTER_CALL, _compensating("type(refusal).__name__ == 'RetiredAgentError'")),
    # (b) gate reads the registry through a door the spy does not wrap: resolve_holder (result discarded).
    "W3a": (S, GATE_HEAD, "        await self.agent_registry.resolve_holder(agent)\n" + GATE_HEAD),
    # (b) ... through a raw registry _query.
    "W3b": (S, GATE_HEAD, "        await self.agent_registry._query('SELECT * FROM agent WHERE session = $s', {'s': session})\n" + GATE_HEAD),
    # (c) catch-ALL TxnDomainRejectionError, NO existence re-read (re-entry recurses on a genuine rejection).
    "W7": (G, EXIST_CHECK, ""),
    # (c) a SECOND copy of the idempotency logic: synthesise re_registered=True, skipping preflight.
    "W12": (G, REENTER, "                return AgentRegisterResult(agent=self._row_to_agent(await self._select_row(agent_id)), re_registered=True)\n"),
    # (c) classification by the RAW engine text (the cause), not by class.
    "W14": (G, EXIST_CHECK, "                if 'already exists' not in str(_rs5_error.__cause__) or await self._select_row(agent_id) is None:\n                    raise\n"),
    # (c) too-broad class: SurrealStoreError (incl. SurrealConnectionError: an UNKNOWN outcome).
    "W15": (G, "            except TxnDomainRejectionError:\n", "            except SurrealStoreError:\n"),
    # (b) ORDER: gate -> mint -> preflight -> register (the #485 regression under the new gate).
    "W9": (S, PREFLIGHT, "        if principal is not None:\n"),
    # (b) gate keyed on KEEPER identity, not the household.
    "W10": (S, "                if keep_scope(existing_bare) not in visible_now:\n", "                if existing_keep.keeper_id != principal_bare:\n"),
    # (a/DUAL) "un-household" compensation instead of delete (the found-pre-existing leg's byte-identity virtue).
    # (a/DUAL) household-EDGE compensation (raw — remove_household_member refuses the keeper, KeeperLockoutError):
    # the found-pre-existing leg's keep+member_of byte-identity virtue; the keep itself is never deleted.
    "W16": (S, REGISTER_CALL, _compensating("True").replace("await keep_store.delete_keep(keep_id=session_keep_bare)", "await keep_store._query('DELETE member_of WHERE out = type::record(\'keep\', $k)', {'k': session_keep_bare})").replace(" and existing_keep is None", "")),
}
# W14 needs the except to bind the error:
W14_EXTRA = (G, "            except TxnDomainRejectionError:\n", "            except TxnDomainRejectionError as _rs5_error:\n")
# W9 needs preflight re-inserted AFTER the mint block:
W9_EXTRA = (S, MINT_TAIL, MINT_TAIL + """        await self.agent_registry.preflight(
            agent,
            session=session,
            role=role,
            spawned_by=spawned_by,
            owner_principal_id=principal_bare,
        )
""")
DECLARED = {
    "W1": [SEQ_H, SEQ_T, RUNTIME, KP1, RS2],
    "W2": [],
    "W3a": [],
    "W3b": [],
    "W7": [],
    "W12": [RS5H],
    "W14": [],
    "W15": [],
    "W9": [ORDER, RUNTIME, KP13],
    "W10": [RS3C],
    "W16": [SEQ_H, SEQ_T],
}

# ---- second batch (declared 2026-09-26 ~16:05, before any run) ----
RS5_TRY = """            try:
                await self._query(
                    f"CREATE type::record('{AGENT_TABLE}', ${_ROW_ID_PARAM}) "
                    f"CONTENT ${_ROW_CONTENT_PARAM}",
                    {_ROW_ID_PARAM: agent_id, _ROW_CONTENT_PARAM: content},
                )
            except TxnDomainRejectionError:
"""
CONTROL = f"{A19A}::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_CONTROL_a_valid_register_mints_exactly_one_keep"
BUILDS.update({
    # (c) handler-level RS-5 retry: the registry leaks the raw rejection; the HANDLER retries register once.
    "W6": (G, RS5_TRY, """            try:
                await self._query(
                    f"CREATE type::record('{AGENT_TABLE}', ${_ROW_ID_PARAM}) "
                    f"CONTENT ${_ROW_CONTENT_PARAM}",
                    {_ROW_ID_PARAM: agent_id, _ROW_CONTENT_PARAM: content},
                )
            except KeyboardInterrupt:
"""),
    # (b) the gate mints a DIFFERENT key first (a per-principal probe keep) via the keyed mint.
    "W4a": (S, GATE_HEAD, GATE_HEAD + "            await keep_store.get_or_create_keyed(key=f\"probe:{principal_bare}\", type=\"session\", keeper_email=principal.email)\n"),
    # (b) mints-then-deletes on the DENY path only (create_keep + delete_keep; tables byte-identical after).
    "W4c": (S, "                if keep_scope(existing_bare) not in visible_now:\n                    raise _foreign_denial()\n",
            "                if keep_scope(existing_bare) not in visible_now:\n                    _probe = await keep_store.create_keep(keeper_email=principal.email, type=\"session\")\n                    await keep_store.delete_keep(keep_id=str(_probe.id).split(\":\", 1)[-1])\n                    raise _foreign_denial()\n"),
})
EXTRA = {
    "W14": [W14_EXTRA],
    "W9": [W9_EXTRA],
    "W6": [(S, REGISTER_CALL, """        from loremaster.store._txn import TxnDomainRejectionError as _Rejection  # noqa: PLC0415

        async def _register_once() -> Any:
            return await self.agent_registry.register(
                agent,
                session=session,
                role=role,
                model=model,
                spawned_by=spawned_by,
                task_id=task_id,
                cadence=cadence,
                owner_principal_id=principal_bare,
                session_keep_id=session_keep_bare,
            )

        try:
            result = await _register_once()
        except _Rejection:
            result = await _register_once()
""")],
}
DECLARED.update({
    "W6": [RS5R],
    "W4a": [RS3P, ORDER, RUNTIME, CONTROL],
    "W4c": [],
})

# ---- W15b (declared 2026-09-26 ~16:15, before any run): the scanner-blind sibling of W15 — a TUPLE catch
# naming the transport class beside the domain class (the retry-seam scanner keys on ``ast.Name ==
# "SurrealStoreError"`` and skips a Tuple handler).
BUILDS["W15b"] = (G, "            except TxnDomainRejectionError:\n",
                  "            except (TxnDomainRejectionError, SurrealConnectionError):\n")
DECLARED["W15b"] = []

# ---- W18 (declared 2026-09-26 ~16:20, before any run): a SECOND COPY of the idempotency logic that keeps the
# conflict DECISION (it calls preflight) but skips the re-register UPDATE — the loser is served the winner's
# row as ``re_registered=True``; its own model / task_id / cadence / heartbeat are silently dropped.
BUILDS["W18"] = (G, REENTER, """                existing_after_conflict = await self.preflight(
                    name,
                    session=session,
                    role=role,
                    spawned_by=spawned_by,
                    owner_principal_id=owner_principal_id,
                    session_keep_id=session_keep_id,
                )
                return AgentRegisterResult(agent=existing_after_conflict, re_registered=True)
""")
DECLARED["W18"] = []

# ---- W19 (declared 2026-09-26 ~16:25, before any run): the read-only gate keyed on the caller's visible-keep
# set being EMPTY rather than on membership of THIS session's keep (fixture monoculture: every foreign probe
# principal holds no keep of her own). The post-mint re-check is left correct (a partial wrong build).
BUILDS["W19"] = (S, "                if keep_scope(existing_bare) not in visible_now:\n",
                 "                if not visible_now:\n")
DECLARED["W19"] = []

# ---- W16b (declared 2026-09-26 ~16:20 after W16's COLLECTION error, before any W16b run): W16 with the quoting
# fixed (W16's replacement emitted `type::record('keep', $k)` inside a single-quoted literal — a SyntaxError, a
# degenerate build, not a pin gap). Household-EDGE compensation on every post-mint refusal; the keep row stays.
BUILDS["W16b"] = (S, REGISTER_CALL, _compensating("True").replace(
    "await keep_store.delete_keep(keep_id=session_keep_bare)",
    "await keep_store._query(\"DELETE member_of WHERE out = type::record('keep', $k)\", {'k': session_keep_bare})",
).replace(" and existing_keep is None", ""))
DECLARED["W16b"] = [SEQ_H, SEQ_T]

# ---- W3c (declared 2026-09-26 ~17:50, before any run, after unions 1/2 showed W3a/W3b die INCIDENTALLY on the
# comms fakes, which lack `_query` / `resolve_holder`): a pre-gate registry read through a method the FAKES DO
# implement — `get_agent(agent)` WITHOUT a session (real registry: `_resolve_row` → `_select_rows_by_name`, which
# RS-3's spy does not wrap), its refusal swallowed.
BUILDS["W3c"] = (S, GATE_HEAD, "        try:\n            await self.agent_registry.get_agent(agent)\n        except _AgentRegistryError:\n            pass\n" + GATE_HEAD)
DECLARED["W3c"] = []
```
### §A.3b `wb/drive.py` — contract driver (both-way diff, byte-exact restore) — md5 `c54c03b46c98397fa71771023015929e`
```python
"""drive.py <ref-tree> <W...>: apply each wrong build to the reference (content backup + md5), run the three contract
files, diff observed FAILED ids against DECLARED both ways, restore byte-exact. Mirrors scripts/mutation_proof.py's
contract (exactly-once anchors, both-way diff) but supports multi-anchor builds."""
import hashlib, importlib.util, pathlib, re, subprocess, sys, datetime
ref = pathlib.Path(sys.argv[1]); names = sys.argv[2:]
spec = importlib.util.spec_from_file_location("builds", pathlib.Path(__file__).parent / "builds.py")
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
extra = getattr(b, "EXTRA", {"W14": [b.W14_EXTRA], "W9": [b.W9_EXTRA]})
FILES = [b.A28, b.A19A, b.A19B, *__import__("os").environ.get("EXTRA_FILES", "").split()]
for name in names:
    edits = [b.BUILDS[name]] + extra.get(name, [])
    backups = {}
    for path, _a, _r in edits:
        f = ref / path
        backups.setdefault(path, (f.read_bytes(), hashlib.md5(f.read_bytes()).hexdigest()))
    try:
        for path, anchor, repl in edits:
            f = ref / path; text = f.read_text()
            n = text.count(anchor)
            if n != 1:
                raise SystemExit(f"{name}: anchor matched {n}x in {path} — mutation NOT landed")
            f.write_text(text.replace(anchor, repl))
        landed = all((ref / p).read_bytes() != bk for p, (bk, _m) in backups.items())
        cp = subprocess.run([str(ref / ".venv/bin/python"), "-m", "pytest", "-q", "-p", "no:cacheprovider", "-n", "8",
                             "-rf", "--tb=line", *FILES], cwd=ref, capture_output=True, text=True, timeout=3000)
        out = cp.stdout + cp.stderr
        tail = [l for l in out.splitlines() if re.search(r"\d+ (passed|failed)", l)][-1:]
        summary = out.split("short test summary info", 1)[-1] if "short test summary info" in out else ""
        observed = sorted({m.group(1) for m in re.finditer(r"^FAILED (\S+)", summary, re.M)})
        declared = sorted(b.DECLARED[name])
        unexpected = [x for x in observed if x not in declared]
        stayed_green = [x for x in declared if x not in observed]
        verdict = "EXACT" if not unexpected and not stayed_green else "MISMATCH"
        print(f"=== {name} @ {datetime.datetime.now().isoformat(timespec='seconds')} landed={landed} tail={tail} verdict={verdict}")
        print(f"  observed RED ({len(observed)}): " + "\n    ".join([""] + observed))
        print(f"  unexpected RED: {unexpected}")
        print(f"  declared but GREEN: {stayed_green}")
        (pathlib.Path(__file__).parent / f"{name}.log").write_text(out)
    finally:
        for path, (bk, md5) in backups.items():
            (ref / path).write_bytes(bk)
            assert hashlib.md5((ref / path).read_bytes()).hexdigest() == md5, f"{name}: restore of {path} NOT byte-exact"
        print(f"  restored byte-exact: {sorted(backups)}")
```
### §A.3c `wb/drive_kill.py` — kill-probe driver — md5 `f0f042defd31dd7eb7ad2dc767e38c73`
```python
"""drive_kill.py <tree> <W...>: like drive.py, but runs kill_declared.FILES and diffs against KILL_DECLARED."""
import hashlib, importlib.util, pathlib, re, subprocess, sys, datetime
here = pathlib.Path(__file__).parent
def load(n):
    s = importlib.util.spec_from_file_location(n, here / f"{n}.py"); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
b, kd = load("builds"), load("kill_declared")
tree = pathlib.Path(sys.argv[1]); extra = getattr(b, "EXTRA", {"W14": [b.W14_EXTRA], "W9": [b.W9_EXTRA]})
for name in sys.argv[2:]:
    edits = [b.BUILDS[name]] + extra.get(name, []); backups = {}
    for path, _a, _r in edits:
        backups.setdefault(path, ((tree / path).read_bytes(), hashlib.md5((tree / path).read_bytes()).hexdigest()))
    try:
        for path, anchor, repl in edits:
            t = (tree / path).read_text(); n = t.count(anchor)
            if n != 1: raise SystemExit(f"{name}: anchor matched {n}x in {path} — NOT landed")
            (tree / path).write_text(t.replace(anchor, repl))
        cp = subprocess.run([str(tree / ".venv/bin/python"), "-m", "pytest", "-q", "-p", "no:cacheprovider", "-n", "8", "-rf",
                             "--tb=line", *([kd.K] if __import__("os").environ.get("K9RUN") else kd.FILES)], cwd=tree, capture_output=True, text=True, timeout=3000)
        out = cp.stdout + cp.stderr
        tail = [l for l in out.splitlines() if re.search(r"\d+ (passed|failed)", l)][-1:]
        summary = out.split("short test summary info", 1)[-1] if "short test summary info" in out else ""
        observed = sorted({m.group(1) for m in re.finditer(r"^FAILED (\S+)", summary, re.M)})
        declared = sorted((kd.K9_DECLARED if __import__("os").environ.get("K9RUN") else kd.KILL_DECLARED)[name])
        un = [x for x in observed if x not in declared]; green = [x for x in declared if x not in observed]
        print(f"=== KILL {name} @ {datetime.datetime.now().isoformat(timespec='seconds')} tail={tail} verdict={'EXACT' if not un and not green else 'MISMATCH'}")
        print("  observed RED: " + "\n    ".join([""] + observed)); print(f"  unexpected: {un}\n  declared-but-GREEN: {green}", flush=True)
        (here / f"KILL-{name}.log").write_text(out)
    finally:
        for path, (bk, md5) in backups.items():
            (tree / path).write_bytes(bk); assert hashlib.md5((tree / path).read_bytes()).hexdigest() == md5
        print(f"  restored byte-exact: {sorted(backups)}", flush=True)
```
### §A.3d `wb/kill_declared.py` — declared kill sets (kill_declared_at 15:57:12; later batches timestamped inline) — md5 `15534f3fda5261bf0b55809dc99b7396`
```python
"""Declared RED sets for the KILL runs: each surviving wrong build applied to the probe tree, run against the kill
probes (+ any existing structural pin named). Written BEFORE the kill runs."""
K = "loremaster/tests/test_adv_a28_kill_probes.py"
K1 = f"{K}::TestK1TheGateReadsNoRegistryRowThroughANYDoor::test_K1_foreign_probes_issue_zero_registry_queries"
K2 = f"{K}::TestK2AGenuineCreateRejectionIsRaisedOnce::test_K2_a_non_conflict_CREATE_rejection_is_re_raised_after_one_attempt"
K3 = f"{K}::TestK3TheConflictIsClassifiedByClassNotText::test_K3_a_reworded_conflict_still_takes_the_re_register_path"
K4 = f"{K}::TestK4ATransportFailureIsNeverAReRegister::test_K4_a_connection_error_on_CREATE_propagates"
K5R = f"{K}::TestK5NoRefusalClassCompensates::test_K5_every_post_mint_refusal_class_leaves_the_keep[retired]"
SEAM = "loremaster/tests/test_retry_seam.py::TestNoGuardedCasHandlerReinterpretsExhaustedContention::test_the_door_enumeration_matches_the_canonical_set"
FILES = [K, "loremaster/tests/test_retry_seam.py"]
KILL_DECLARED = {
    "W2": [K5R],
    "W3a": [K1],
    "W3b": [K1],
    "W7": [K2],
    "W14": [K3],
    "W15": [K4, SEAM],
}

# ---- batch 2 (declared 2026-09-26 ~16:15, before any run) ----
K6F = f"{K}::TestK6NoRegisterPathRemovesOrWritesKeepState::test_K6_foreign_denials_write_nothing_to_the_keep_store"
K6R = [f"{K}::TestK6NoRegisterPathRemovesOrWritesKeepState::test_K6_a_race_refusal_removes_no_keep_state[{r}]"
       for r in ("role", "spawned_by", "retired")]
KILL_DECLARED.update({
    "W15b": [K4],
    "W4c": [K6F],
    "W16": [*K6R, f"{K}::TestK5NoRefusalClassCompensates::test_K5_every_post_mint_refusal_class_leaves_the_keep[role]",
            f"{K}::TestK5NoRefusalClassCompensates::test_K5_every_post_mint_refusal_class_leaves_the_keep[spawned_by]",
            f"{K}::TestK5NoRefusalClassCompensates::test_K5_every_post_mint_refusal_class_leaves_the_keep[retired]"],
})

# ---- W18 (declared 2026-09-26 ~16:20, before any run) ----
K7 = f"{K}::TestK7TheRaceLoserIsServedTheSequentialSecondCall::test_K7_the_loser_writes_its_own_mutable_fields"
KILL_DECLARED["W18"] = [K7]

# ---- W19 (declared 2026-09-26 ~16:25, before any run) ----
K8 = f"{K}::TestK8AForeignPrincipalWithHerOwnKeepIsStillDenied::test_K8_foreign_probes_by_a_principal_who_keeps_another_session"
KILL_DECLARED["W19"] = [K8]

# ---- W16b (declared 2026-09-26 ~16:20, before any W16b run; K5 NOT declared — an edge delete leaves the keep row) ----
KILL_DECLARED["W16b"] = [*K6R]

# ---- K9 (generated) runs — declared 2026-09-26 ~16:33, before any K9 kill run. FILES narrowed to the kill file. ----
K9 = f"{K}::TestK9EveryCreateOutcomeIsServedAsTheSequentialCallWould::test_K9_create_outcome"
_K9_OLD = {
    "W7": [K2, f"{K9}[TxnDomainRejectionError-no-row]", f"{K9}[TxnGovernedConflictError-no-row]"],
    "W14": [K3, f"{K9}[TxnDomainRejectionError-row-landed]", f"{K9}[TxnGovernedConflictError-row-landed]"],
    "W15b": [K4, f"{K9}[SurrealConnectionError-row-landed]"],
    "W18": [K7, f"{K9}[TxnDomainRejectionError-row-landed]", f"{K9}[TxnGovernedConflictError-row-landed]"],
}
K9_DECLARED = _K9_OLD

# ---- W3c (declared 2026-09-26 ~17:50, before any run) ----
KILL_DECLARED["W3c"] = [K1]
```
### §A.3e contract batch 1 receipt (`wb/drive_run1.out`) — md5 `6b8f311068abce32880c6c9a24c2d32c`
```text
=== W1 @ 2026-09-26T15:52:50 landed=True tail=['6 failed, 134 passed in 166.97s (0:02:46)'] verdict=MISMATCH
  observed RED (6): 
    loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_EVERY_driven_register_meets_the_runtime_property
    loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP1_a_keep_won_by_a_concurrent_mint_is_never_compensated
    loremaster/tests/test_fixwave_a28_63c_i_a.py::TestAConcurrentIdenticalRegisterIsIdempotent63cIAa28::test_RS5_every_handler_caller_gets_a_registry_answer_never_an_engine_error
    loremaster/tests/test_fixwave_a28_63c_i_a.py::TestTheRaceNeverStrandsAScope63cIAa28::test_RS2_eight_way_registers_never_strand_a_scope
    loremaster/tests/test_fixwave_a28_63c_i_a.py::TestTheRaceNeverStrandsAScope63cIAa28::test_the_sequential_race_keeps_the_keep_and_serves_the_teaching[handler-winner-found-the-keep]
    loremaster/tests/test_fixwave_a28_63c_i_a.py::TestTheRaceNeverStrandsAScope63cIAa28::test_the_sequential_race_keeps_the_keep_and_serves_the_teaching[tokenless-winner-control]
  unexpected RED: ['loremaster/tests/test_fixwave_a28_63c_i_a.py::TestAConcurrentIdenticalRegisterIsIdempotent63cIAa28::test_RS5_every_handler_caller_gets_a_registry_answer_never_an_engine_error']
  declared but GREEN: []
  restored byte-exact: ['loremaster/loremaster/server.py']
=== W2 @ 2026-09-26T15:55:42 landed=True tail=['140 passed in 169.65s (0:02:49)'] verdict=EXACT
  observed RED (0): 
  unexpected RED: []
  declared but GREEN: []
  restored byte-exact: ['loremaster/loremaster/server.py']
=== W3a @ 2026-09-26T15:58:29 landed=True tail=['140 passed in 164.34s (0:02:44)'] verdict=EXACT
  observed RED (0): 
  unexpected RED: []
  declared but GREEN: []
  restored byte-exact: ['loremaster/loremaster/server.py']
=== W3b @ 2026-09-26T16:01:28 landed=True tail=['140 passed in 175.78s (0:02:55)'] verdict=EXACT
  observed RED (0): 
  unexpected RED: []
  declared but GREEN: []
  restored byte-exact: ['loremaster/loremaster/server.py']
=== W7 @ 2026-09-26T16:04:28 landed=True tail=['140 passed in 179.03s (0:02:59)'] verdict=EXACT
  observed RED (0): 
  unexpected RED: []
  declared but GREEN: []
  restored byte-exact: ['loremaster/loremaster/agents.py']
=== W12 @ 2026-09-26T16:07:27 landed=True tail=['1 failed, 139 passed in 176.04s (0:02:56)'] verdict=EXACT
  observed RED (1): 
    loremaster/tests/test_fixwave_a28_63c_i_a.py::TestAConcurrentIdenticalRegisterIsIdempotent63cIAa28::test_RS5_every_handler_caller_gets_a_registry_answer_never_an_engine_error
  unexpected RED: []
  declared but GREEN: []
  restored byte-exact: ['loremaster/loremaster/agents.py']
=== W14 @ 2026-09-26T16:10:31 landed=True tail=['140 passed in 181.81s (0:03:01)'] verdict=EXACT
  observed RED (0): 
  unexpected RED: []
  declared but GREEN: []
  restored byte-exact: ['loremaster/loremaster/agents.py']
=== W15 @ 2026-09-26T16:13:27 landed=True tail=['140 passed in 174.60s (0:02:54)'] verdict=EXACT
  observed RED (0): 
  unexpected RED: []
  declared but GREEN: []
  restored byte-exact: ['loremaster/loremaster/agents.py']
=== W9 @ 2026-09-26T16:15:38 landed=True tail=['9 failed, 131 passed in 129.45s (0:02:09)'] verdict=MISMATCH
  observed RED (9): 
    loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_EVERY_driven_register_meets_the_runtime_property
    loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[AgentIdentityConflictError-role-conflict]
    loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[AgentIdentityConflictError-spawned-by-conflict]
    loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[InvalidAgentIdentityError-blank-empty]
    loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[InvalidAgentIdentityError-blank-ideographic]
    loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[InvalidAgentIdentityError-blank-spaces]
    loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[RetiredAgentError-retired]
    loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_the_handler_decides_with_preflight_BEFORE_the_mint
    loremaster/tests/test_fixwave_a28_63c_i_a.py::TestAForeignPrincipalLearnsNothingBeforeTheGate63cIAa28::test_the_handler_ORDER_is_gate_then_preflight_then_mint_then_register
  unexpected RED: ['loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[AgentIdentityConflictError-role-conflict]', 'loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[AgentIdentityConflictError-spawned-by-conflict]', 'loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[InvalidAgentIdentityError-blank-empty]', 'loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[InvalidAgentIdentityError-blank-ideographic]', 'loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[InvalidAgentIdentityError-blank-spaces]', 'loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[RetiredAgentError-retired]', 'loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_the_handler_decides_with_preflight_BEFORE_the_mint']
  declared but GREEN: ['loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP13_a_register_refused_on_a_cadence_conflict_mints_nothing']
  restored byte-exact: ['loremaster/loremaster/server.py']
=== W10 @ 2026-09-26T16:18:34 landed=True tail=['1 failed, 139 passed in 168.94s (0:02:48)'] verdict=EXACT
  observed RED (1): 
    loremaster/tests/test_fixwave_a28_63c_i_a.py::TestAForeignPrincipalLearnsNothingBeforeTheGate63cIAa28::test_RS3_CONTROLS_a_householded_member_proceeds_and_the_keeper_is_still_taught
  unexpected RED: []
  declared but GREEN: []
  restored byte-exact: ['loremaster/loremaster/server.py']
=== W16 @ 2026-09-26T16:18:39 landed=True tail=[] verdict=MISMATCH
  observed RED (0): 
  unexpected RED: []
  declared but GREEN: ['loremaster/tests/test_fixwave_a28_63c_i_a.py::TestTheRaceNeverStrandsAScope63cIAa28::test_the_sequential_race_keeps_the_keep_and_serves_the_teaching[handler-winner-found-the-keep]', 'loremaster/tests/test_fixwave_a28_63c_i_a.py::TestTheRaceNeverStrandsAScope63cIAa28::test_the_sequential_race_keeps_the_keep_and_serves_the_teaching[tokenless-winner-control]']
  restored byte-exact: ['loremaster/loremaster/server.py']
```
### §A.3f contract batch 2 receipt (`wb/drive_run2.out`) — md5 `e18238e9171b535f70ba8efb999360ab`
```text
=== W6 @ 2026-09-26T16:23:21 landed=True tail=['1 failed, 139 passed in 276.89s (0:04:36)'] verdict=EXACT
  observed RED (1): 
    loremaster/tests/test_fixwave_a28_63c_i_a.py::TestAConcurrentIdenticalRegisterIsIdempotent63cIAa28::test_RS5_eight_identical_first_registers_all_succeed_at_the_registry
  unexpected RED: []
  declared but GREEN: []
  restored byte-exact: ['loremaster/loremaster/agents.py', 'loremaster/loremaster/server.py']
=== W4a @ 2026-09-26T16:28:16 landed=True tail=['13 failed, 127 passed in 292.59s (0:04:52)'] verdict=MISMATCH
  observed RED (13): 
    loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_CONTROL_a_valid_register_mints_exactly_one_keep
    loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_EVERY_driven_register_meets_the_runtime_property
    loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[AgentIdentityConflictError-role-conflict]
    loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[AgentIdentityConflictError-spawned-by-conflict]
    loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[InvalidAgentIdentityError-blank-empty]
    loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[InvalidAgentIdentityError-blank-ideographic]
    loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[InvalidAgentIdentityError-blank-spaces]
    loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[RetiredAgentError-retired]
    loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_the_handler_decides_with_preflight_BEFORE_the_mint
    loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP1_a_keep_won_by_a_concurrent_mint_is_never_compensated
    loremaster/tests/test_fixwave_a28_63c_i_a.py::TestAForeignPrincipalLearnsNothingBeforeTheGate63cIAa28::test_RS3_every_foreign_probe_is_the_same_denial_with_zero_registry_reads
    loremaster/tests/test_fixwave_a28_63c_i_a.py::TestAForeignPrincipalLearnsNothingBeforeTheGate63cIAa28::test_the_handler_ORDER_is_gate_then_preflight_then_mint_then_register
    loremaster/tests/test_fixwave_a28_63c_i_a.py::TestTheRaceNeverStrandsAScope63cIAa28::test_the_sequential_race_keeps_the_keep_and_serves_the_teaching[tokenless-winner-control]
  unexpected RED: ['loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[AgentIdentityConflictError-role-conflict]', 'loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[AgentIdentityConflictError-spawned-by-conflict]', 'loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[InvalidAgentIdentityError-blank-empty]', 'loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[InvalidAgentIdentityError-blank-ideographic]', 'loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[InvalidAgentIdentityError-blank-spaces]', 'loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[RetiredAgentError-retired]', 'loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_the_handler_decides_with_preflight_BEFORE_the_mint', 'loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP1_a_keep_won_by_a_concurrent_mint_is_never_compensated', 'loremaster/tests/test_fixwave_a28_63c_i_a.py::TestTheRaceNeverStrandsAScope63cIAa28::test_the_sequential_race_keeps_the_keep_and_serves_the_teaching[tokenless-winner-control]']
  declared but GREEN: []
  restored byte-exact: ['loremaster/loremaster/server.py']
=== W4c @ 2026-09-26T16:30:54 landed=True tail=['140 passed in 156.13s (0:02:36)'] verdict=EXACT
  observed RED (0): 
  unexpected RED: []
  declared but GREEN: []
  restored byte-exact: ['loremaster/loremaster/server.py']
=== W15b @ 2026-09-26T16:33:41 landed=True tail=['140 passed in 166.07s (0:02:46)'] verdict=EXACT
  observed RED (0): 
  unexpected RED: []
  declared but GREEN: []
  restored byte-exact: ['loremaster/loremaster/agents.py']
=== W18 @ 2026-09-26T16:36:22 landed=True tail=['140 passed in 159.94s (0:02:39)'] verdict=EXACT
  observed RED (0): 
  unexpected RED: []
  declared but GREEN: []
  restored byte-exact: ['loremaster/loremaster/agents.py']
=== W19 @ 2026-09-26T16:39:06 landed=True tail=['140 passed in 162.51s (0:02:42)'] verdict=EXACT
  observed RED (0): 
  unexpected RED: []
  declared but GREEN: []
  restored byte-exact: ['loremaster/loremaster/server.py']
=== W16b @ 2026-09-26T16:41:46 landed=True tail=['3 failed, 137 passed in 159.00s (0:02:39)'] verdict=MISMATCH
  observed RED (3): 
    loremaster/tests/test_fixwave_a28_63c_i_a.py::TestAConcurrentIdenticalRegisterIsIdempotent63cIAa28::test_RS5_every_handler_caller_gets_a_registry_answer_never_an_engine_error
    loremaster/tests/test_fixwave_a28_63c_i_a.py::TestTheRaceNeverStrandsAScope63cIAa28::test_the_sequential_race_keeps_the_keep_and_serves_the_teaching[handler-winner-found-the-keep]
    loremaster/tests/test_fixwave_a28_63c_i_a.py::TestTheRaceNeverStrandsAScope63cIAa28::test_the_sequential_race_keeps_the_keep_and_serves_the_teaching[tokenless-winner-control]
  unexpected RED: ['loremaster/tests/test_fixwave_a28_63c_i_a.py::TestAConcurrentIdenticalRegisterIsIdempotent63cIAa28::test_RS5_every_handler_caller_gets_a_registry_answer_never_an_engine_error']
  declared but GREEN: []
  restored byte-exact: ['loremaster/loremaster/server.py']
```
### §A.3g kill batch 1 receipt — md5 `2f24d8e014637566789e02b302aabdb6`
```text
=== KILL W2 @ 2026-09-26T15:58:42 tail=['1 failed, 673 passed, 1 warning in 87.26s (0:01:27)'] verdict=EXACT
  observed RED: 
    loremaster/tests/test_adv_a28_kill_probes.py::TestK5NoRefusalClassCompensates::test_K5_every_post_mint_refusal_class_leaves_the_keep[retired]
  unexpected: []
  declared-but-GREEN: []
  restored byte-exact: ['loremaster/loremaster/server.py']
=== KILL W3a @ 2026-09-26T16:00:22 tail=['1 failed, 673 passed, 1 warning in 97.61s (0:01:37)'] verdict=EXACT
  observed RED: 
    loremaster/tests/test_adv_a28_kill_probes.py::TestK1TheGateReadsNoRegistryRowThroughANYDoor::test_K1_foreign_probes_issue_zero_registry_queries
  unexpected: []
  declared-but-GREEN: []
  restored byte-exact: ['loremaster/loremaster/server.py']
=== KILL W3b @ 2026-09-26T16:02:06 tail=['1 failed, 673 passed, 1 warning in 102.01s (0:01:42)'] verdict=EXACT
  observed RED: 
    loremaster/tests/test_adv_a28_kill_probes.py::TestK1TheGateReadsNoRegistryRowThroughANYDoor::test_K1_foreign_probes_issue_zero_registry_queries
  unexpected: []
  declared-but-GREEN: []
  restored byte-exact: ['loremaster/loremaster/server.py']
=== KILL W7 @ 2026-09-26T16:03:46 tail=['1 failed, 673 passed, 1 warning in 98.35s (0:01:38)'] verdict=EXACT
  observed RED: 
    loremaster/tests/test_adv_a28_kill_probes.py::TestK2AGenuineCreateRejectionIsRaisedOnce::test_K2_a_non_conflict_CREATE_rejection_is_re_raised_after_one_attempt
  unexpected: []
  declared-but-GREEN: []
  restored byte-exact: ['loremaster/loremaster/agents.py']
=== KILL W14 @ 2026-09-26T16:05:24 tail=['1 failed, 673 passed, 1 warning in 95.48s (0:01:35)'] verdict=EXACT
  observed RED: 
    loremaster/tests/test_adv_a28_kill_probes.py::TestK3TheConflictIsClassifiedByClassNotText::test_K3_a_reworded_conflict_still_takes_the_re_register_path
  unexpected: []
  declared-but-GREEN: []
  restored byte-exact: ['loremaster/loremaster/agents.py']
=== KILL W15 @ 2026-09-26T16:07:07 tail=['2 failed, 672 passed, 1 warning in 101.41s (0:01:41)'] verdict=EXACT
  observed RED: 
    loremaster/tests/test_adv_a28_kill_probes.py::TestK4ATransportFailureIsNeverAReRegister::test_K4_a_connection_error_on_CREATE_propagates
    loremaster/tests/test_retry_seam.py::TestNoGuardedCasHandlerReinterpretsExhaustedContention::test_the_door_enumeration_matches_the_canonical_set
  unexpected: []
  declared-but-GREEN: []
  restored byte-exact: ['loremaster/loremaster/agents.py']
```
### §A.3h kill batch 2 receipt (W16 = the degenerate build, DV-2) — md5 `0bab42f24af7863e83939f0806011d92`
```text
=== KILL W15b @ 2026-09-26T16:12:55 tail=['1 failed, 677 passed, 1 warning in 149.43s (0:02:29)'] verdict=EXACT
  observed RED: 
    loremaster/tests/test_adv_a28_kill_probes.py::TestK4ATransportFailureIsNeverAReRegister::test_K4_a_connection_error_on_CREATE_propagates
  unexpected: []
  declared-but-GREEN: []
  restored byte-exact: ['loremaster/loremaster/agents.py']
=== KILL W4c @ 2026-09-26T16:15:10 tail=['1 failed, 677 passed, 1 warning in 133.14s (0:02:13)'] verdict=EXACT
  observed RED: 
    loremaster/tests/test_adv_a28_kill_probes.py::TestK6NoRegisterPathRemovesOrWritesKeepState::test_K6_foreign_denials_write_nothing_to_the_keep_store
  unexpected: []
  declared-but-GREEN: []
  restored byte-exact: ['loremaster/loremaster/server.py']
=== KILL W16 @ 2026-09-26T16:15:16 tail=[] verdict=MISMATCH
  observed RED: 
  unexpected: []
  declared-but-GREEN: ['loremaster/tests/test_adv_a28_kill_probes.py::TestK5NoRefusalClassCompensates::test_K5_every_post_mint_refusal_class_leaves_the_keep[retired]', 'loremaster/tests/test_adv_a28_kill_probes.py::TestK5NoRefusalClassCompensates::test_K5_every_post_mint_refusal_class_leaves_the_keep[role]', 'loremaster/tests/test_adv_a28_kill_probes.py::TestK5NoRefusalClassCompensates::test_K5_every_post_mint_refusal_class_leaves_the_keep[spawned_by]', 'loremaster/tests/test_adv_a28_kill_probes.py::TestK6NoRegisterPathRemovesOrWritesKeepState::test_K6_a_race_refusal_removes_no_keep_state[retired]', 'loremaster/tests/test_adv_a28_kill_probes.py::TestK6NoRegisterPathRemovesOrWritesKeepState::test_K6_a_race_refusal_removes_no_keep_state[role]', 'loremaster/tests/test_adv_a28_kill_probes.py::TestK6NoRegisterPathRemovesOrWritesKeepState::test_K6_a_race_refusal_removes_no_keep_state[spawned_by]']
  restored byte-exact: ['loremaster/loremaster/server.py']
```
### §A.3i kill batch 3 receipt — md5 `05dbdb8bd1fb426467846695349a78de`
```text
=== KILL W18 @ 2026-09-26T16:19:40 tail=['1 failed, 679 passed, 1 warning in 174.38s (0:02:54)'] verdict=EXACT
  observed RED: 
    loremaster/tests/test_adv_a28_kill_probes.py::TestK7TheRaceLoserIsServedTheSequentialSecondCall::test_K7_the_loser_writes_its_own_mutable_fields
  unexpected: []
  declared-but-GREEN: []
  restored byte-exact: ['loremaster/loremaster/agents.py']
=== KILL W19 @ 2026-09-26T16:25:02 tail=['1 failed, 679 passed, 1 warning in 319.91s (0:05:19)'] verdict=EXACT
  observed RED: 
    loremaster/tests/test_adv_a28_kill_probes.py::TestK8AForeignPrincipalWithHerOwnKeepIsStillDenied::test_K8_foreign_probes_by_a_principal_who_keeps_another_session
  unexpected: []
  declared-but-GREEN: []
  restored byte-exact: ['loremaster/loremaster/server.py']
=== KILL W16b @ 2026-09-26T16:29:16 tail=['3 failed, 677 passed, 1 warning in 252.05s (0:04:12)'] verdict=EXACT
  observed RED: 
    loremaster/tests/test_adv_a28_kill_probes.py::TestK6NoRegisterPathRemovesOrWritesKeepState::test_K6_a_race_refusal_removes_no_keep_state[retired]
    loremaster/tests/test_adv_a28_kill_probes.py::TestK6NoRegisterPathRemovesOrWritesKeepState::test_K6_a_race_refusal_removes_no_keep_state[role]
    loremaster/tests/test_adv_a28_kill_probes.py::TestK6NoRegisterPathRemovesOrWritesKeepState::test_K6_a_race_refusal_removes_no_keep_state[spawned_by]
  unexpected: []
  declared-but-GREEN: []
  restored byte-exact: ['loremaster/loremaster/server.py']
```
### §A.3j K9 kill receipt (`K9RUN=1`: only the kill file) — md5 `4b25434e30d86b4fc7986d3347cc8d72`
```text
=== KILL W7 @ 2026-09-26T16:31:24 tail=['3 failed, 25 passed in 49.17s'] verdict=EXACT
  observed RED: 
    loremaster/tests/test_adv_a28_kill_probes.py::TestK2AGenuineCreateRejectionIsRaisedOnce::test_K2_a_non_conflict_CREATE_rejection_is_re_raised_after_one_attempt
    loremaster/tests/test_adv_a28_kill_probes.py::TestK9EveryCreateOutcomeIsServedAsTheSequentialCallWould::test_K9_create_outcome[TxnDomainRejectionError-no-row]
    loremaster/tests/test_adv_a28_kill_probes.py::TestK9EveryCreateOutcomeIsServedAsTheSequentialCallWould::test_K9_create_outcome[TxnGovernedConflictError-no-row]
  unexpected: []
  declared-but-GREEN: []
  restored byte-exact: ['loremaster/loremaster/agents.py']
=== KILL W14 @ 2026-09-26T16:32:13 tail=['3 failed, 25 passed in 48.20s'] verdict=EXACT
  observed RED: 
    loremaster/tests/test_adv_a28_kill_probes.py::TestK3TheConflictIsClassifiedByClassNotText::test_K3_a_reworded_conflict_still_takes_the_re_register_path
    loremaster/tests/test_adv_a28_kill_probes.py::TestK9EveryCreateOutcomeIsServedAsTheSequentialCallWould::test_K9_create_outcome[TxnDomainRejectionError-row-landed]
    loremaster/tests/test_adv_a28_kill_probes.py::TestK9EveryCreateOutcomeIsServedAsTheSequentialCallWould::test_K9_create_outcome[TxnGovernedConflictError-row-landed]
  unexpected: []
  declared-but-GREEN: []
  restored byte-exact: ['loremaster/loremaster/agents.py']
=== KILL W15b @ 2026-09-26T16:33:06 tail=['2 failed, 26 passed in 51.56s'] verdict=EXACT
  observed RED: 
    loremaster/tests/test_adv_a28_kill_probes.py::TestK4ATransportFailureIsNeverAReRegister::test_K4_a_connection_error_on_CREATE_propagates
    loremaster/tests/test_adv_a28_kill_probes.py::TestK9EveryCreateOutcomeIsServedAsTheSequentialCallWould::test_K9_create_outcome[SurrealConnectionError-row-landed]
  unexpected: []
  declared-but-GREEN: []
  restored byte-exact: ['loremaster/loremaster/agents.py']
=== KILL W18 @ 2026-09-26T16:33:52 tail=['3 failed, 25 passed in 45.44s'] verdict=EXACT
  observed RED: 
    loremaster/tests/test_adv_a28_kill_probes.py::TestK7TheRaceLoserIsServedTheSequentialSecondCall::test_K7_the_loser_writes_its_own_mutable_fields
    loremaster/tests/test_adv_a28_kill_probes.py::TestK9EveryCreateOutcomeIsServedAsTheSequentialCallWould::test_K9_create_outcome[TxnDomainRejectionError-row-landed]
    loremaster/tests/test_adv_a28_kill_probes.py::TestK9EveryCreateOutcomeIsServedAsTheSequentialCallWould::test_K9_create_outcome[TxnGovernedConflictError-row-landed]
  unexpected: []
  declared-but-GREEN: []
  restored byte-exact: ['loremaster/loremaster/agents.py']
```
### §A.3k `wb/combo.py` — the union survivor build for the full-suite receipt (declared 16:23:25) — md5 `b8c7c3abcb74b2b6beaaf66f366f664a`
```python
"""combo.py <tree> apply|restore: the UNION survivor build for the full-suite receipt (declared 2026-09-26 ~16:25,
before any run): W2 + W3b + W19 (server.py) and W7 + W15b + W18 (agents.py). Declared: NO full-suite red beyond the
reference's own red set. Content backup + md5 restore."""
import hashlib, importlib.util, json, pathlib, sys
here = pathlib.Path(__file__).parent
s = importlib.util.spec_from_file_location("b", here / "builds.py"); b = importlib.util.module_from_spec(s); s.loader.exec_module(b)
tree = pathlib.Path(sys.argv[1]); mode = sys.argv[2]; state = here / "combo_backup.json"
NAMES = ["W2", "W3b", "W19", "W7", "W15b", "W18"]
if mode == "apply":
    files = sorted({b.BUILDS[n][0] for n in NAMES})
    backup = {f: (tree / f).read_text() for f in files}
    state.write_text(json.dumps({f: [t, hashlib.md5(t.encode()).hexdigest()] for f, t in backup.items()}))
    for n in NAMES:
        path, anchor, repl = b.BUILDS[n]
        text = (tree / path).read_text(); c = text.count(anchor)
        assert c == 1, f"{n}: anchor matched {c}x in {path}"
        (tree / path).write_text(text.replace(anchor, repl))
    print("applied", NAMES, "to", files)
else:
    for f, (t, md5) in json.loads(state.read_text()).items():
        (tree / f).write_text(t); assert hashlib.md5((tree / f).read_bytes()).hexdigest() == md5
    print("restored byte-exact", list(json.loads(state.read_text())))
```
### §A.5 SDK-kind probe (the live AlreadyExistsError receipt) — md5 `1eac360feee69f927b467bb847d2c78d`
```python
"""adversary-63c-i-a-a28 PROBE (not a pin): what the unique-id CREATE conflict looks like at the SDK layer on the
live 3.2.x TEST store (:18000) — the raw error's class / kind / details under the driver's TxnDomainRejectionError."""
from __future__ import annotations
from typing import Any
import pytest
import test_fixwave_a28_63c_i_a as a28
from _governed_contract import credentialed_app_context
from loremaster.store._txn import TxnDomainRejectionError


async def test_probe_the_create_conflict_kind(monkeypatch: pytest.MonkeyPatch, tmp_path: Any, capsys: Any) -> None:
    async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=a28._DIM) as world:
        registry = world["ctx"].agent_registry
        await registry.register("kindprobe", session="s-kind", role="builder")
        async def none_row(agent_id: str) -> Any:
            return None
        monkeypatch.setattr(registry, "_select_row", none_row)  # force the second call onto the CREATE path
        with pytest.raises(TxnDomainRejectionError) as caught:
            await registry.register("kindprobe", session="s-kind", role="builder")
        cause = caught.value.__cause__
        chain = []
        while cause is not None:
            chain.append((type(cause).__module__ + "." + type(cause).__name__, getattr(cause, "kind", None),
                          getattr(cause, "details", None), getattr(cause, "record_id", None), str(cause)[:160]))
            cause = cause.__cause__
        with open("/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/0fa51319-cfaf-4808-b33f-0775da3eb0db/scratchpad/sdk_kind_probe.txt", "w") as out:
            out.write(f"raised: {type(caught.value).__name__}: {caught.value}\n")
            for link in chain:
                out.write(f"cause: {link!r}\n")
```
### §A.5b its output — md5 `0360e3d86b968b69ca3f325e7b5d1f58`
```text
raised: TxnDomainRejectionError: SurrealDB agent query rejected against 'ws://127.0.0.1:18000/rpc' (unspecified rejection); see the server log for the full engine detail
cause: ('surrealdb.errors.AlreadyExistsError', 'AlreadyExists', {'details': {'id': 'agent:5dd13170f3b15631a66006adcd9d5dd0'}, 'kind': 'Record'}, 'agent:5dd13170f3b15631a66006adcd9d5dd0', 'Database record `agent:5dd13170f3b15631a66006adcd9d5dd0` already exists')
```
### §A.6 RS-2 reach measurement (`test_adv_a28_rs2_reach.py`; 200 rounds: post-mint refusal 200/200, creator refused post-mint 193/200) — md5 `404a871a40b5e949cefe6afffecb8e90`
```python
"""adversary-63c-i-a-a28 MEASUREMENT (not a pin): the RS-2 rig's reach — per round, how many handler registers were
refused AFTER the session-keep mint (the only path the deleted compensation ran on), and whether the refused call
was the keep's CREATOR (the only caller a created-only compensation could delete from)."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import pytest
import test_fixwave_a28_63c_i_a as a28
from _governed_contract import credentialed_app_context
from loremaster.agents import AgentRegistryError

ROUNDS = int(os.environ.get("RS2_REACH_ROUNDS", "60"))
OUT = os.environ.get("RS2_REACH_OUT", "/dev/null")


async def test_measure_rs2_reach(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=a28._DIM) as world:
        ctx = world["ctx"]
        world["holder"]["email"] = world["emails"]["alice"]
        keep_store, registry = ctx._keep_store, ctx.agent_registry
        real_mint, real_register = keep_store.get_or_create_keyed, registry.register
        task_state: dict[int, dict[str, Any]] = {}

        import loremaster.keeps as keeps_module

        real_txn = keeps_module.execute_transaction

        async def txn(*args: Any, **kwargs: Any) -> Any:
            result = await real_txn(*args, **kwargs)  # returns only if THIS task's CREATE committed
            task_state[id(asyncio.current_task())] = {"created": True}
            return result

        monkeypatch.setattr(keeps_module, "execute_transaction", txn)

        async def mint(*args: Any, **kwargs: Any) -> Any:
            return await real_mint(*args, **kwargs)

        per_round: list[dict[str, int]] = []
        counters = {"post_mint_refusals": 0, "creator_refused": 0}

        async def register(*args: Any, **kwargs: Any) -> Any:
            try:
                return await real_register(*args, **kwargs)
            except AgentRegistryError:
                counters["post_mint_refusals"] += 1
                if task_state.get(id(asyncio.current_task()), {}).get("created"):
                    counters["creator_refused"] += 1
                raise

        monkeypatch.setattr(keep_store, "get_or_create_keyed", mint)
        monkeypatch.setattr(registry, "register", register)
        for round_index in range(ROUNDS):
            counters.update(post_mint_refusals=0, creator_refused=0)
            await asyncio.gather(*a28._eight_way_register_calls(ctx, f"s-reach-{round_index}"), return_exceptions=True)
            per_round.append(dict(counters))
        with open(OUT, "w") as handle:
            json.dump(per_round, handle)
```
### §A.7 W7 unbounded measurement probe — md5 `c366fd95d89eeb90481edb6c7a4bd9a3`
```python
"""adversary-63c-i-a-a28 MEASUREMENT (not a pin): under W7 (catch-all, no existence re-read), what does a caller get
from a genuine non-conflict CREATE rejection when nothing bounds the re-entry? Writes class + CREATE count."""
from __future__ import annotations
from typing import Any
import pytest
import test_fixwave_a28_63c_i_a as a28
from _governed_contract import credentialed_app_context
from loremaster.store._txn import TxnDomainRejectionError

OUT = "/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/0fa51319-cfaf-4808-b33f-0775da3eb0db/scratchpad/w7_unbounded.txt"


async def test_measure_unbounded(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=a28._DIM) as world:
        registry = world["ctx"].agent_registry
        real = registry._query
        creates = {"n": 0}

        async def forging(statement: str, params: Any = None) -> Any:
            if statement.startswith("CREATE"):
                creates["n"] += 1
                raise TxnDomainRejectionError("forged: a genuine NON-conflict domain rejection of the CREATE")
            return await real(statement, params)

        monkeypatch.setattr(registry, "_query", forging)
        try:
            await registry.register("w7agent", session="s-w7", role="builder")
            outcome = "RETURNED"
        except BaseException as error:  # noqa: BLE001
            outcome = f"{type(error).__name__}: {str(error)[:120]}"
        with open(OUT, "w") as handle:
            handle.write(f"outcome={outcome}\nCREATE attempts={creates['n']}\n")
```
### §A.7b its output (W7 applied to my reference) — md5 `a1bd5dd31c0000137eeb78ec43ebecbd`
```text
outcome=RecursionError: maximum recursion depth exceeded
CREATE attempts=928
```
### §A.8 `guarded_tree2.sh` — the PID-TREE watchdog every full suite ran under (control: `TREE_CAP_GB=0` killed a 3-level tree, 0 surviving sleeps) — md5 `739ad6baacc299f37b53df685a31493f`
```bash
#!/usr/bin/env bash
# guarded_tree2.sh <dir> <logfile> -- <command...>: run <command> in <dir> under a PID-TREE watchdog (8 s poll):
# kill the WHOLE tree (every descendant) when the tree's summed RSS exceeds ${TREE_CAP_GB:-15} GB, or when host
# MemAvailable drops below ${HOST_FLOOR_GB:-4} GB. Watchdog events go to <logfile>.watchdog (never the run's log).
DIR=$1; LOG=$2; shift 2; [ "$1" = "--" ] && shift
cd "$DIR" || exit 99
"$@" > "$LOG" 2>&1 &
PID=$!
descendants() { local c; for c in $(pgrep -P "$1"); do descendants "$c"; echo "$c"; done; }
( while kill -0 $PID 2>/dev/null; do
    TREE="$(descendants $PID) $PID"
    RSS_GB=$(ps -o rss= -p $(echo $TREE | tr ' ' ',') 2>/dev/null | awk '{s+=$1} END{print int(s/1048576)}')
    A=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
    if [ "${RSS_GB:-0}" -ge "${TREE_CAP_GB:-15}" ] || [ "$A" -lt "${HOST_FLOOR_GB:-4}" ]; then
      echo "WATCHDOG TREE-KILL tree_rss=${RSS_GB}G avail=${A}G at $(date -Is)" >> "$LOG.watchdog"; kill -TERM $TREE 2>/dev/null; fi
    sleep 8; done ) &
wait $PID; echo "EXIT=$?" >> "$LOG.watchdog"
```

### §A.3l W3c contract + fake-comms receipt (`EXTRA_FILES` = test_comms_tool + test_comms_render_architecture) — md5 `3871bdff18e79d7c08bce1cec9330fb6`
```text
=== W3c @ 2026-09-26T17:49:44 landed=True tail=['1090 passed in 201.51s (0:03:21)'] verdict=EXACT
  observed RED (0): 
  unexpected RED: []
  declared but GREEN: []
  restored byte-exact: ['loremaster/loremaster/server.py']
```
### §A.3m W3c kill receipt — md5 `d43b796540ab2a4f4e9c685e62a50b3b`
```text
=== KILL W3c @ 2026-09-26T17:48:38 tail=['2 failed, 693 passed, 1 warning in 135.81s (0:02:15)'] verdict=MISMATCH
  observed RED: 
    loremaster/tests/test_adv_a28_kill_probes.py::TestK1TheGateReadsNoRegistryRowThroughANYDoor::test_K1_foreign_probes_issue_zero_registry_queries
    loremaster/tests/test_adv_a28_kill_probes.py::TestK8AForeignPrincipalWithHerOwnKeepIsStillDenied::test_K8_foreign_probes_by_a_principal_who_keeps_another_session
  unexpected: ['loremaster/tests/test_adv_a28_kill_probes.py::TestK8AForeignPrincipalWithHerOwnKeepIsStillDenied::test_K8_foreign_probes_by_a_principal_who_keeps_another_session']
  declared-but-GREEN: []
  restored byte-exact: ['loremaster/loremaster/server.py']
```
### §A.3n `wb/combo2.py` / `wb/combo3.py` — byte-for-byte `wb/combo.py` (§A.3k) except `NAMES` (`["W2", "W3a", "W19", "W7", "W15b", "W18"]` / `["W2", "W3c", "W19", "W7", "W15b", "W18"]`), the backup filename and the docstring's declaration line (sed-derived, commands in §1b).

## VERDICT
**CONTRACT INSUFFICIENT** (graded `d334042`, narrow delta (a)–(d), 2026-09-26).
- **(a) §F-1 no-compensation pins — sound on the debugged race, guarded on its CAUSE.** RS-2 (10/10 RED at the checkpoint, miss probability ≤ 0.012 per invocation even at the worst observed strand rate) + the deterministic sequential twin kill every compensation that fires on a role-conflict race (W1, W16b, M01-class). A compensation keyed on a DIFFERENT refusal class (W2) walks through. → MP-5 (K5 + K6; class C1). LOW.
- **(b) §F-2 read-only-gate-first pins — the ORDER is pinned; the GATE PREDICATE is not.** Every foreign probe principal holds no keep of her own, so a gate that denies only principals who see NO keep (W19) passes all 140 pins AND the full suite and re-opens the F-2 leak for nearly every real principal. → **MP-1 (K8), HIGH.** The zero-registry-reads spy is a 3-method hand-list (W3a/W3b/W3c; W3c survives the full suite) → MP-4 (K1), LOW.
- **(c) am-29 RS-5 pins — pinned for the conflict CAUSE and the `re_registered` FLAG only.** A catch-all without the existence check recurses 928× into a `RecursionError` on a genuine rejection (W7); text-keyed (W14) and transport-swallowing (W15b) classifiers, and a second copy of the re-register path that drops the loser's own writes (W18), all pass the contract and (W7, W15b, W18 measured) the full suite. ONE generated pin (K9 — ∀ derived store-error classes × row landed) kills all four. → **MP-2 (K9) + MP-3 (K7), MEDIUM.** Design fork FK-ADV-1: the SDK already types this conflict (`AlreadyExistsError`) and the ONE driver erases it — am-29's own "by class, else STOP" decision point, resolved silently by the contract.
- **(d) DUAL deletions — sound.** Everything the created-only and #4b pins guarded is either retired on purpose (am-28) or still guarded, except a sliver of the found-keep byte-identity axis that no plausible build reaches (W16b, the plausible one, is killed). The author's U1(b) "widened ∀ keeps" over-claims (effect → proxy); K6 closes it for free.
- **SAT:** satisfiable by my independent register-half reference — full suite, one tree both ways: 0 reference-only reds, the identical 45 fixed, 238 shared reds adjudicated (none changes shape because of 63c). **am-31** (lead #17070): 3 SAT defects + 2 contract items for the fold (§6), incl. FK-ADV-2.
- **Fix the CLASS, not the instance:** the five missing pins are three properties — C1 (the register path's only keep-store write is the mint; no pre-existing keep state changes, ∀ refusal classes), C2 (a foreign register issues zero registry queries, ∀ probe × ∀ principal shape), C3 (∀ derived CREATE outcomes, the registry serves what the sequential call would). K9 is C3 already generated; K5/K6 and K1/K8 are C1/C2's first instances with the completeness assertions named in §2.
- Loop cost, stated per the 2026-09-26 rule: this is the a28 contract's first adversary pass (one round); the lead holds the running total.
