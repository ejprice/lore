# REPORT-adversary-63c-i-a-r4a — contract-adversary NARROW delta pass on the r4a addendum (`e80a854..bf77fb9`)

brief-base v16 read · brief project v7 read

## SUMMARY BLOCK
- **state:** done-with-deviations · **VERDICT: CONTRACT INSUFFICIENT** — 1 NEW-CLASS survivor (RS1srv, a new SEAM of the GATING row), 1 SAME-CLASS survivor with no pinned bound and a false "any fallback" claim (FXh), 1 satisfiability hazard in an r4a row (SH1); SAME-CLASS bounds G3, PX2w; C2 RULED (am-10); TWR = the KB-2 bound working. **No LIVE-PRODUCTION-DEFECT** (MEDIUM — §5).
- **Graded:** `bf77fb9` · HEAD-at-report: `1705ea3` · DIFFERENT (2 ahead: `5b94961` amendment 10, `1705ea3` lead report — docs only; `git diff --stat bf77fb9 1705ea3 -- loremaster lorerunes lorescribe loresigil scripts` EMPTY).
- **deviations:** DV-A my stray `git stash` in the lane mid-PX2w (restored; verdict VOID, re-run clean) · my C-3 probe's first draft was blind (role mismatch; caught by its own record, fixed, re-run) · P-PKG: the author's one-line package verdict was seen (summary block) before my table · declare-then-diff driver for multi-edit builds, `mutation_proof.py` for the single-anchor proof.
- **Packages considered:** stdlib `ast`/`re`, `pytest.MonkeyPatch`, in-house `module_level_bindings_of` (REUSE) — diff vs author: agreement (§9). **Odoo-20 portability:** n/a — no Odoo seam touched (0 = author's 0). **Reuse ledger:** none — no repo symbols added; scratch instruments pasted §A.
- **P1 (§4):** **floor 7/7 KILLED** exactly on declared r4a pins (RS1, FX2, G1, G2, FXg, FXf, PX2) + RS1FX2 (parity reds on its ABSOLUTE leg) + R5/R5b (killed by packet 07 with r4's premise pin deleted). **Six builds survive the FULL suite** (COMBO `11459 passed`, 0 failed): **FXh, RS1srv, C2, G3, PX2w, TWR** — each proven live by a kill-pin pair.
- **SAT (§2, own reference incl. all four builder edits, ruff clean):** 25 files `2978 passed, 19 skipped`; **FULL SUITE ALONE `-n 12`: `11459 passed, 62 skipped, 3 xfailed` — 0 failed** (= author). TWR full-suite survival (= author's §SAT-B) reproduced inside COMBO. **RED@HEAD (§1):** 0 turned · 13 new right-reason reds · 19 new green · 1 gone — author CONFIRMED. **Currency (§7):** unbuilt 20 RED_ADJUDICATED; built 11/11 SELF-DESTRUCT, 0 real mypy errors, ruff GREEN — author CONFIRMED; #461 no wrong discharge.
- **MISSING PINS (§6):** **MP-A1** FXh — shape-pin clause (iii): no call-time re-read of the predicate off a module object (FXh: `getattr` + non-silent private fallback, no `try`) · SAME-CLASS · **MP-A2** SH1 — row 5's phrase leg reads the TOTAL in "first 3 of 18 ids shown" and REFUSES a correct derived build; strip the full count (or drop the `N … shown` alternative) · contract defect (satisfiability) · **MP-A3** RS1srv — end-to-end ownership-INVARIANCE pin through `comms(action="register")` for a householded joiner (passes at HEAD + on a correct build; no served denial) · NEW-CLASS (seam) — sidecar rules r4b vs i-b.
- **P1b (§5b):** 9 invariants — Q2, Q3, Q5, Q8 ∀ (receipts); Q1, Q4, Q6, Q7 GUARDED with surviving door-builds (RS1srv/C2, G3, FXh, PX2w+SH1); Q9 guarded BY RULING (TWR). **P1c (§6a):** 7 instruments — shared helper and legal corpus one-source PROOF HELD by mutation; MISSING: I-1 proxy axis (FXh), I-5 tool seam (RS1srv), I-4 over-fires (SH1).
- **C-2 / C-3 (§5):** C2 built — survives the full suite, construction-only (RULED). C-3 RUN at HEAD `1705ea3` AND on my reference: the joiner's re-register of the keeper's agent is **NOT refused earlier** (`re-registered keeper-a`); ownership survives in both; RS1srv reds only the probe.
- **decisions-needed:** sidecar rules MP-A3 (r4b data-invariance pin now vs i-b refusal later — the i-a builder edits `_comms_register` in this wave) · MP-A1 (close with clause (iii) — fits am-10 C-5's r4b-if-any — or pin FXh as a KNOWN BOUND and narrow both "any spelling / any fallback" sentences) · MP-A2 (fix the phrase leg before the builder, or name the phrasing in the builder brief).
- **Receipt pointers:** §0 capability · §1 RED · §2 SAT · §3 DUAL · §4.1 floor · §4.2/§4.2b new builds · §4.5 full-suite leg · §5 C-2/C-3 · §5b P1b · §6 MISSING PINS · §6a P1c · §7 currency · §8 residuals · §9 P-PKG · §10 P-PORT · §11 corpses · §A instruments · VERDICT.

## 0. Capability check (brief-base §4) — measured 2026-09-25
- Reachable: lore MCP (`register` OK, session `63c-20260924`), `git`, `uv run pytest/ruff`, `scripts/scratch_copy.sh`,
  test store `ws://127.0.0.1:18000`. Never touched `:18500`; never called the TEI embedder.
- grep/rg are hook-blocked (#473): every textual sweep here is `awk` (said once, applies throughout).
- Store reference `docs/reference/surrealdb-31-capabilities.md` read first (§0 banner + section map; r4a touches no DDL).
- Scratch root (my session scratchpad; the brief names no location — instruments are PASTED in §A so nothing asserted
  lives only there): `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bab26354-cc66-4f18-b92e-6d27fa6ff922/scratchpad`.
  Lane `ref` via `scratch_copy.sh` (rc=0, provenance asserted by the tool); branch `adv4a-ref` @ `ff812c0` (lane-local).
  `loremaster.__file__ = …/scratchpad/ref/loremaster/loremaster/__init__.py`;
  `lorerunes.__file__ = …/scratchpad/ref/lorerunes/lorerunes/__init__.py`;
  `_comms_fakes.__file__ = …/scratchpad/ref/loremaster/tests/_comms_fakes.py`.

## 3. DUAL — my independent enumeration of r4a's deletions / re-keys (written from `git diff e80a854..bf77fb9` BEFORE opening the author's §DUAL), then the diff
| # | deleted / re-keyed (my enumeration) | virtue it carried | my verdict (pre-§DUAL) |
|---|---|---|---|
| E1 | `test_message_enforcement_63b_ii_a.py::…::test_KNOWN_BOUND_premise_no_generator_emits_a_relation_the_ENFORCED_sweep_cannot_see` DELETED | (a) ∀ **derived** generators (`schema_ddl_generators()`, no hand-list): relations emitted − relations swept = ∅; (b) anti-vacuity (swept sees ≥ 1 relation); (c) keyed `(edge, endpoints)` (the R5b blind spot) | (a) now carried by TWO coupled pins: packet-07 `…::test_this_slice_contains_neither_a_relation_table_nor_a_sequence` over `_both_slices()` — a **2-generator hand-list** (`generate_floor_calibration_ddl`, `generate_lease_ddl`) — and the FORK-A exact-set pin, which pins the DERIVED unswept set `== {lease, floor_calibration}`. Under the builder-cannot-edit-tests model the pair is equivalent to (a): a relation in a THIRD generator either is byte-covered by the sweep or makes that generator unswept → FORK-A reds. Verdict: PRESERVED by coupling (a reach built from a derived set pinned equal to a hand-list — construction-inspected, §6a row I-6). (b) moot with its reader. (c) the deletion REMOVES the weaker key. |
| E2 | `test_the_fake_and_the_real_writer_agree_on_the_RE_REGISTER_door`: `if alpha / else refused` absolute → per-sequence table `_RE_REGISTER_EXPECTED_REAL` | the `else` branch gave EVERY non-alpha sequence the REFUSED expectation | values for the three r4 sequences carried byte-for-byte (checked by reading: alpha → `("re-registered", None, True, None)`; mixed pairs → `("refused","alice_pid",True,keep:K)`); a sequence missing from the table is a `KeyError` (RED), not a silent default. PRESERVED. |
| E3 | effect pin `…never_silently_skips…`: `monkeypatch.delattr(lorerunes, …)` → delattr at EVERY `lorerunes*` binding found by identity | removal of the PACKAGE attribute | the package attribute is among the identity-found bindings (the pin fetches `shared_predicate` FROM it), so the old removal ⊂ the new. PRESERVED. |
| E4 | SKIP-gate mutation leg / accept-control / hostile-corpus control: param lists extended (`dict.fromkeys` dedupe) | r4's values | additive; no value lost (dedupe only collapses exact duplicates). |
| E5 | `_HOSTILE_IDENTIFIERS` + `"fixer.b"` (appended LAST) | every index-derived param id | ids unchanged (append-last); every corpus consumer now carries the dotted twin — SAT-checked by my full-suite run (§2). |
| E6 | failure texts (R-4, KB-4), docstrings (KB-3, R-2 header, R-3, `_comms_fakes.py`), `pending_contracts.yaml` comment | prose | no assertion changed; R-2's header NARROWS a claim (truth fix). |

**Diff vs the author's §DUAL (D1–D4, read after the table above):** D1 = my E1 · D2 = my E3 · D4 = my E2 · D3 (the
r4 E1 erratum + presence-pin restoration) is a restoration, not a deletion — I list its residual door as FXh (§4.2).
My E4/E5/E6 = the author's "additive only" / "prose only" paragraph. **No deletion I found is missing from theirs; no
item of theirs is ungrounded.** One refinement to D1(a): the author calls the packet-07 pins "strictly stronger"; they
are stronger on the PREDICATE (any `TYPE RELATION`, not only an unseen edge) but their REACH is a hand-list
(`_both_slices()`), made equivalent to the deleted pin's derived reach only by the FORK-A exact-set coupling — stated in
§6a row I-6, not a missing pin.

## 9. P-PKG — my table (built from the r4a diff), then the diff against the author's line
⚠ Ordering deviation, disclosed: the author's `Packages considered:` line sits in its SUMMARY BLOCK, which I read while
locating §DUAL; my table below was nonetheless derived from the diff hunks, not from that line.
| mechanism r4a specifies | candidates | what I READ | verdict |
|---|---|---|---|
| import-SHAPE scanner (`_fake_predicate_import_violations`) | stdlib `ast` (`ast.walk`, `ast.Try`/`ast.TryStar`, `ImportFrom.level`); libcst/semgrep (not installed; a `Try`/`ImportFrom` walk needs neither); ruff (no custom-rule API) | the pin's source at `bf77fb9`; `ast.TryStar` exists on 3.11+ (the pin guards with `getattr(ast, "TryStar", None)`) | **bespoke — justified** (stdlib AST, one consumer) |
| "predicate absent" at every binding | in-house `_logging_fixtures.module_level_bindings_of` | its source (lore_get_symbol, `_logging_fixtures.py`) | **REUSE** — correct; its stated KNOWN BOUND (module namespaces only) is irrelevant here (the fake reads a module global) |
| prose-integer detector (PX2 leg) | stdlib `re` | pin source | stdlib — fine |
| constant/predicate removal | `pytest.MonkeyPatch.setattr/delattr` | installed pytest API | package — used |
**Diff:** agreement on every verdict (author: "none — no mechanism specified (tests only); stdlib ast/re +
MonkeyPatch.delattr; module_level_bindings_of REUSED"). No `bespoke` rests on an unread API. DRY spot-check: two lore
searches (`"test helper: is a module name inside a given package…"`, `"AST scan for try/except wrapping an import…"`,
tier `lore`) returned no reusable import-shape helper — the author's HAND-ROLLED disposition for `_is_lorerunes_module` /
`_is_lorerunes_import` / `_fake_predicate_import_violations` is corroborated.

## 10. P-PORT
`Odoo-20 portability: n/a — no Odoo seam touched` — my own enumeration over the r4a diff (4 test files + 1 fake + yaml):
0 Odoo models/fields/methods/views/ACLs/ORM paths. Author's line matches (0 = 0).

## 11. P6 — corpse sweep (awk, BARE patterns `premise_no_generator|ENFORCED_sweep_cannot_see|emits_a_relation_the`, every `git ls-files` path; measured 2026-09-25 at `1705ea3`)
6 hits, each: `REPORT-adversary-63c-i-a-r4.md:77` history (r4 floor table) · `:688` history (r4's pasted instrument) ·
`REPORT-contract-63c-i-a-r4.md:81` history · `:253` history · `REPORT-contract-63c-i-a-r4a.md:82` the §DUAL row (correct) ·
`loremaster/tests/test_message_enforcement_63b_ii_a.py:448` the in-place DUAL comment (correct). **No live code, test,
design doc or yaml cites the deleted pin as current.**

## 7. `scripts/pending_contracts.yaml` (r4a edit: the `_comms_fakes.py` entry's COMMENT names the shape pin; no count/symbol changed)
- **Unbuilt world (main checkout, `1705ea3` tests = `bf77fb9` tests):** `pending_contract_gate.py --currency --legs
  typecheck,ruff` → `typecheck RED_ADJUDICATED — 20 residual(s), owned by: packet-63c-i-a-contract-r2 ·
  packet-63c-i-a-contract-r3` · `ruff GREEN` · `pytest NOT_RUN` (by design, #466; rc=1 is that NOT_RUN). **= the
  author's 20.** The claim "r4a adds no mypy error because every new `lorerunes.is_legal_identifier` read goes through
  `getattr`" checked by reading: the effect pin (`getattr(lorerunes, "is_legal_identifier", None)`) and the shape pin
  (`getattr(lorerunes, _PREDICATE_NAME, None)`) — both `getattr`; the RS1 pin reaches `register(session_keep_id=…)`
  through the existing `_real_re_register_outcome`, whose file is already registered under `register.session_keep_id`.

## 4. P1 — wrong builds (lane `ref` @ `adv4a-ref` = `ff812c0`, my reference; tests = `bf77fb9`'s)
Method: `run_lane_r4a.sh` (§A.3) — per build: reset lane (0 dirty paths asserted), resolve the DECLARED expected-RED
ids from `collected_adv4a.txt` (collect-only over the 25 files of `files5.txt` — adversary-r4's 24 ∪
`test_floor_calibration_schema.py` — **2997 ids**, taken on `adv4a-ref` BEFORE any wrong-build run), apply the build
via `my_wbs_r4a.py` (§A.2 — exactly-once anchors; a build that leaves the lane clean aborts), assert
`loremaster.__file__` inside the lane, run the 25 files `-n 8` (ONE pytest session at a time, 12 GiB PID watchdog —
never fired), diff observed-RED vs declared BOTH ways from junit. Measured 2026-09-25.
**Reference tail on the same 25 files: `2978 passed, 19 skipped` — 0 failed (= the author's §ROWS reference tail).**

### 4.1 The floor (adversary-r4's survivors RS1, FX2, G1, G2, FXg, FXf, PX2) — ALL KILLED, each EXACTLY on its declared r4a pin (0 unexpected reds, 0 declared-still-green)
| build | the door | tail (25 files) | killed by (junit message head) |
|---|---|---|---|
| **RS1** | REAL writer re-stamps a STAMPED row from the caller's pair (householded-joiner takeover) | `2 failed, 2976 passed, 19 skipped` | `…never_re_stamps_a_stamped_row_from_a_DIFFERENT_householded_principal` (*"changed the governed triple: ('re-registered', 'bob_pid', True, 'keep:sessionkeep7')"*) + `…RE_REGISTER_door[consistent-then-householded-joiner-pair]` (parity: real=bob, fake=alice) |
| **FX2** | the FAKE re-stamps (real correct) | `1 failed, 2977 passed, 19 skipped` | `…RE_REGISTER_door[consistent-then-householded-joiner-pair]` (parity: real=alice, fake=bob) |
| **RS1FX2** | BOTH re-stamp — `fake == real` holds | `2 failed, 2976 passed, 19 skipped` | the parity row reds on its **ABSOLUTE** leg (*"the REAL writer's RE-register outcome for 'consistent-then-householded-joiner-pair' is not the ruled one: ('re-registered', 'bob_pid', …)"*) + the RS1 pin — **the row carries the absolute real-side expectation, as amendment-9 MP-R4-6 requires (checked, brief focus 2)** |
| **G1** | SKIP gate + private `or len(attribution) > 32` | `2 failed, 2976 passed, 19 skipped` | `…SKIP_gate_moves_…[a×64]` BASELINE + `…never_looks_up_any_value_of_the_hostile_corpus` CONTROL (the witness loop) |
| **G2** | SKIP gate + reworded dotted disjunct | `1 failed, 2977 passed, 19 skipped` | `…never_looks_up_any_value_of_the_hostile_corpus`: `{'fixer.b': ['fixer.b']}` (KB-1's corpus entry) |
| **FXg** | guard KEPT, `try` imports from `lorerunes.identifiers` | `2 failed, 2976 passed, 19 skipped` | effect pin (reach = every `lorerunes*` binding) + shape pin |
| **FXf** | guard KEPT with a NON-silent private-regex fallback | `1 failed, 2977 passed, 19 skipped` | shape pin only (the effect pin is blind by construction — the two-pins-two-properties split, measured) |
| **PX2** | the refusal prose restates `(first 10 ids shown)` | `1 failed, 2977 passed, 19 skipped` | `R_Q5_1[perturbed-bound]` birth-value leg (*"restates the BIRTH sample size 10 while the slice follows the PATCHED constant 3"*) |

A kill in the 25-file subset is a kill in the full suite (the red test is a member of it), so no floor build needs its
own full-suite leg. **r4 floor: 7/7 KILLED. The author's "14/14 PROOF HELD" is corroborated on the 7 floor builds + RS1FX2
by an independently written reference and driver.**

### 4.2 NEW wrong builds against r4a's rows (declared BEFORE the run; tails over the 25 files, 2997 ids)
| build | row attacked | the door | tail (25 files) | kill-pin pair (`kp_pairs_r4a.sh`, §A.4; REF = `4 passed`) |
|---|---|---|---|---|
| **FXh** | row 4 shape pin + row 3 effect pin | module-top `from lorerunes import is_blank, is_legal_identifier` KEPT (clause (i) ✓), NO `try` anywhere (clause (ii) ✓); the helper re-reads `getattr(lorerunes, "is_legal_identifier", None)` at call time and, if absent, returns a PRIVATE regex (`[a-z0-9][a-z0-9_-]{0,63}`) — FXf's non-silent fallback with X3d's `getattr` instead of a `try` | **`2978 passed, 19 skipped`** — **SURVIVES** (declared `[]`) | KP-FXh (no `getattr`/attribute re-read of the predicate in `_comms_fakes.py`): REF green, **FXh red** (*"line 281: getattr(lorerunes, 'is_legal_identifier', None)"*) |
| FXhS | P0 control for FXh | the same shape with a SILENT fallback (`None`) | `1 failed, 2977 passed` — declared `[effect pin]` ✓ | the effect pin SEES the `getattr` path; FXh survives ONLY because its fallback refuses (non-silent) |
| **G3** | row 2 legal corpus | SKIP gate + private `or attribution.endswith(("-", "_"))` — a narrowing on an axis NO witness carries (`a-b`, `a_b` put the separator in the MIDDLE) | **`2978 passed, 19 skipped`** — **SURVIVES** (declared `[]`) | KP-G3 (`"a-"`, `"a_"` looked up once): REF green, **G3 red** (*"a- assert [] == ['a-']"*) |
| **C2** | row 1 (C-2 axis) | REAL writer AND fake re-stamp owner+scope when the caller's KEEP differs from the stamped one (`(alice,K) → (alice,K2)`) | **`2978 passed, 19 skipped`** — **SURVIVES** (declared `[]`) | KP-C2 (amendment-10 C-2's row shape, absolute): REF green, **C2 red** (*"real=('re-registered', 'alice_pid', True, 'keep:sessionkeep8')"*) |
| **RS1srv** | row 1 (C-3 seam) | the TOOL `_comms_register` re-stamps `owner_principal` to the caller after a successful re-register (the registry stays correct) | **`2978 passed, 19 skipped`** — **SURVIVES** (declared `[]`) | the C-3 probe (§5): REF green, **RS1srv red** (*"TAKEOVER at the tool seam: owner_principal … -> …"*) |
| **PX2w** | row 5 PX2 leg | the refusal restates the bound IN WORDS: `(first ten ids shown)` | first pass VOID (see deviation DV-A); re-run in lane pass 2 — §4.2b | no runnable kill-pin (a number-word detector is a new instrument; not built — brief: no instruments beyond the checks) |
| **SH1** | row 5 PX2 leg — **SATISFIABILITY** control | a **CORRECT** build: prose derived from the constant at CALL time, `f"(first {_REFUSAL_ID_SAMPLE_SIZE} of {len(owned_unscoped_ids)} ids shown)"` | **`1 failed, 2977 passed`** — `R_Q5_1[perturbed-bound]` RED (declared ✓): *"the refusal states a sample size [3, 18] that is not the PATCHED bound 3 … '18 agent row(s) carry an owner but no scope (agent:owned_trap_000, …) — a multi-principal or half-applied store (first 3 of 18 ids shown); …'"* | — **the phrase leg reads the TOTAL in "of 18 ids shown" as a sample size: a false RED on correct, derived prose** |

**DV-A (my own error, disclosed):** during PX2w's first lane run I executed a stray `git stash` loop in the lane,
which stashed PX2w's mutation mid-run; restored within seconds by `git stash pop` (stash list empty after). That
run's verdict is VOID and is not used anywhere; PX2w was re-run from a clean reset in lane pass 2.
**P0 on my own C-3 probe:** its first draft re-registered the keeper's agent with `role="auditor"` and was refused by
the identity-conflict (role) rule BEFORE the re-register path, so RS1srv read green — the probe was BLIND. Caught by
reading the recorded measurement (`AgentIdentityConflictError … you sent auditor`); fixed to the same role; re-run:
REF green, RS1srv red. The earlier RS1srv "4 passed" is void.

## 5. C-2 / C-3 — CONSTRUCTED and MEASURED (brief focus 6; amendment 10 landed mid-run at `5b94961` and ruled both by READING — these are the RUN receipts)
- **C-2 (RS1 with a DIFFERENT keep) — build `C2`**: REAL writer + fake re-stamp owner+scope when the caller's keep ≠ the
  stamped keep. **Survives the 25 contract files (`2978 passed`)**; full-suite leg §4.5. KP-C2 (amendment-10's own row shape,
  `(alice,K) → (alice,K2)` → `("re-registered","alice_pid",True,keep:K)`, real AND fake) is GREEN on my reference and RED on
  C2. Reachability: amendment-10's reading (the keep is `session:{session}`, UNIQUE-keyed, so a tool re-register always
  carries the same keep) is consistent with `_comms_register`'s source at `1705ea3` (`get_or_create_keyed(key=
  f"session:{session}", …)`) — I did not construct a tool-path door to K2. **CLASS: RULED (amendment-10 C-2 → r4b-if-any,
  else i-b)**; a construction-only door, not live.
- **C-3 (end-to-end `lore_comms register` by a householded joiner) — a MEASUREMENT, run, not read**
  (`test_adv_r4a_c3_probe.py`, §A.5, through `AppContext.comms(action="register")` on the credentialed harness, test store
  only). Same scenario at HEAD `1705ea3` (unbuilt) and on my reference: alice registers `keeper-a` in `shared`; bob is
  added to the household; carol (foreign) and bob (joiner) each call register with `agent="keeper-a"`, same role.
  | | foreign (carol) | joiner (bob) on alice's agent | owner/owner_agent/scope after |
  |---|---|---|---|
  | **HEAD `1705ea3`** | `RAISED GovernedDenied: session 'shared' is kept by another principal …` | **`RETURNED: re-registered keeper-a …`** | unchanged (owner = alice; `owner_agent`/`scope` NONE — the unbuilt world stamps neither) |
  | **my reference** | same denial | **`RETURNED: re-registered keeper-a …`** | unchanged (owner = alice, `owner_agent` = self, `scope` = keep:K) |
  **Neither HEAD nor the reference refuses earlier**: SF-63-1 admits the householded joiner, and the registry's
  re-register path accepts him (status/heartbeat/model/task_id/cadence take his values — amendment-10's description,
  now measured for the success leg; the metadata columns were not projected by my probe). Ownership survives in both
  (the RS1 row's property holds end to end on a correct build). P0: the foreign leg proves the probe sees a refusal;
  bob's own fresh agent (`joiner-b`, owner = bob) proves it sees a joiner's write; **RS1srv** (the TOOL re-stamping the
  owner after a successful re-register — the registry left correct) turns the probe RED (*"TAKEOVER at the tool seam"*)
  while **surviving the 25 contract files** (`2978 passed`). **CLASS: RS1srv = NEW-CLASS at a new SEAM of the GATING row's
  own stated door** (amendment-9 MP-R4-1 names the door as "reachable through `_comms_register`", then pins it at the
  registry seam only — THE QUANTIFIER LAW, derived at one seam, stated over the tool call). Amendment 10 routes the
  end-to-end REFUSAL pin to i-b; that pin (row byte-identical after a joiner's re-register) would kill RS1srv. See MP-A3.
- **LIVE-PRODUCTION?** Not claimed. At HEAD code, in a credentialed test world, a householded joiner DOES re-register
  another principal's agent (a within-household liveness/metadata write; ownership untouched). Whether the RUNNING image
  has credentialed principals on agents (amendment 10: "no principals on agents in the running image") is UNVERIFIED by
  me — I never touch `:18500`. Confidence the door is not live today: MEDIUM (rests on the sidecar's statement).

### 4.2b Lane pass 2 (declared BEFORE this pass; same driver, same 2997-id universe)
| build | tail (25 files) | verdict |
|---|---|---|
| **PX2w** (clean re-run) | `2978 passed, 19 skipped` | **SURVIVES** (declared `[]`) — the birth-value leg is ∀ over DIGIT spellings only |
| **R5** (un-ENFORCED `holds(lease→task)` in the lease slice) | `2 failed, 2976 passed` | KILLED exactly by `test_floor_calibration_schema.py::…::test_every_table_definition_is_IF_NOT_EXISTS` + `…::test_this_slice_contains_neither_a_relation_table_nor_a_sequence` — **with r4's premise pin GONE** |
| **R5b** (the swept `to` re-defined without ENFORCED in the lease slice) | `2 failed, 2976 passed` | KILLED exactly by the same two packet-07 pins — the R-1 DUAL holds (brief focus 2, "deletion of r4's premise pin") |
| **TWR** (KB-2 reworded twin) | `2978 passed, 19 skipped` | SURVIVES — as the pinned bound says it must (full-suite leg §4.5) |

**Lint on the survivors** (`uv run ruff check .` on each build): FXh, G3, RS1srv, PX2w → `All checks passed!`; C2 and SH1 →
E501 only (the line length of MY build's inserted lines — a wrap-only fix; not a lint catch of the door).

## 2. SATISFIABILITY — my OWN reference (`my_ref_build_r4.py` + `my_ref_leg_r4a.py`, §A.1)
- **Instrument:** adversary-r4's `my_ref_build_r4.py` VERBATIM (md5 `3e419c7544454d632b8bbd0c460111e2`, copied from its surviving
  scratch; text in `REPORT-adversary-63c-i-a-r4.md` §A.1 @ `86379a4`) — it already carries the lint cleanups and the
  `_IDENTIFIER_CHARSET_PATTERN = AGENT_NAME_PATTERN.pattern` rebind — plus MY r4a leg, written WITHOUT opening the author's
  `make_ref_r4a.py`: (1) the fake's call-time read deleted and `from lorerunes import is_blank, is_legal_identifier` at MODULE
  TOP; (3) a WHY comment on `_REFUSAL_ID_SAMPLE_SIZE`; (4) the "from ANY caller, including a different householded principal"
  sentence at the CREATE-only stamp. So all four builder grants are in it. Lane `ref`, branch `adv4a-ref` @ `ff812c0`.
- Provenance: `loremaster.__file__ = …/scratchpad/ref/loremaster/loremaster/__init__.py`; `lorerunes.is_legal_identifier`:
  `"fixer-b"` True, `"fixer-b\n"` False, `"fixer.b"` False; `_comms_fakes.is_legal_identifier is lorerunes.is_legal_identifier`
  → True (module-top binding of THE object).
- **Lint AFTER the cleanups (the exact tree that ran):** `uv run ruff check .` → `All checks passed!`.
- **25 contract files, `-n 8`, alone:** `2978 passed, 19 skipped, 4 warnings in 311.21s` — 0 failed (= author).
- **FULL SUITE ALONE `-n 12` (2026-09-25 06:55:21–07:05:32 EDT; launched at 24 GiB under the FORK-MEM grant, lowest 17 GiB;
  process table clean at launch; watchdog never fired): `11459 passed, 62 skipped, 3 xfailed, 7 warnings in 605.49s` — 0
  failed, 0 errors, exit 0.** **= the author's §SAT count exactly, on an independently written r4a leg.**

## 6. MISSING PINS / CONTRACT DEFECTS — each: the test that should exist · the defect it catches · the wrong build · receipt · CLASS
- **MP-A1 · FXh — the shape pin's "any fallback" claim is false: a guard WITHOUT `try` keeps a non-silent private fallback.**
  *Test that should exist:* clause (iii) of `_fake_predicate_import_violations` (or a sibling pin): in `_comms_fakes.py`,
  **no expression re-reads `is_legal_identifier` off a module object** — no `ast.Attribute(attr="is_legal_identifier")`, no
  `getattr`/`hasattr` call naming it — so the module-top import is the ONLY route to the predicate (allowlist the safe, as
  the ruling asks); plus an FXh-shaped entry in `test_the_fake_import_shape_scanner_names_every_guard_POSITIVE_CONTROL`.
  Runnable shape: KP-FXh (§A.4). *Defect it catches:* the HEAD-RED guard outliving its premise in a `try`-free spelling
  whose fallback REFUSES (so the effect pin is blind by construction) — a private copy of the identity rule living in the
  test tree, outside the text pin's reach. *Wrong build:* FXh (§4.2). *Receipts:* 25 files `2978 passed`; **full suite §4.5**;
  KP-FXh REF green / FXh red; FXhS (silent twin) red on the effect pin (P0). *Prose defect riding it:* the shape pin's
  docstring (*"the HEAD-RED guard cannot outlive its premise in ANY spelling, silent or not"*) and amendment-9 MP-R4-5
  (*"That one shape subsumes … FXf (any fallback — the try is the tell)"*) both over-claim; FXh falsifies both.
  **CLASS: SAME-CLASS** (the fake-guard family of the identity class — FXf's door, X3d's spelling). Under the STOP-rule it is
  owed AT LEAST a pinned KNOWN BOUND with the docstring narrowed; the one-clause closure is cheaper than the bound and
  fits amendment-10 C-5's "r4b-if-any" widening, which does NOT cover it (C-5's safe shape is still "no `Try` … + module-top
  import" — FXh satisfies both).
- **MP-A2 · SH1 — row 5's phrase leg REFUSES a correct build (satisfiability hazard).**
  *Test that should exist / change:* in `R_Q5_1[perturbed-bound]`'s PX2 leg, remove every occurrence of the FULL count
  (`\b{trap_count}\b`) from `residue` before the sample-size phrase leg — or drop the `(\d+)\s+(?:\w+\s+)?(?:ids?\s+)?shown`
  alternative (amendment-10 C-4 already calls the phrase leg a convenience; the birth-value leg does the killing, measured:
  PX2 dies on the birth-value leg, §4.1). *Defect:* a builder writing the natural, CORRECT, derived prose
  `f"(first {_REFUSAL_ID_SAMPLE_SIZE} of {len(owned_unscoped_ids)} ids shown)"` — the author's own suggested
  `f"first {sample_size} ids shown"` plus three words — is RED: *"the refusal states a sample size [3, 18] that is not the
  PATCHED bound 3"* (the phrase regex reads the TOTAL in "of 18 ids shown"). The builder may not edit the test, so it is
  trapped into dropping correct prose. *Receipt:* SH1 lane `1 failed, 2977 passed` (§4.2). **CLASS: contract defect of an
  r4a row (C-DEF / satisfiability class; precedent: r4's MP2DEF → amendment-9 R-4)** — fix before the builder, or the
  builder brief names the phrasing to avoid.
- **MP-A3 · RS1srv — the GATING row's door, pinned at ONE seam.** *Test that should exist:* end-to-end through
  `AppContext.comms(action="register")` on the credentialed harness: the keeper registers; a joiner is householded; the
  joiner re-registers the keeper's agent WITH THE SAME ROLE → `owner_principal`, `owner_agent`, `scope` byte-identical
  (controls: a foreign principal is denied; the joiner's fresh name is created owned by the joiner). Runnable shape: the C-3
  probe (§A.5) minus its recording. **It passes at HEAD and on a correct build** (§5) — it asserts DATA invariance only, NOT
  amendment-10's served denial, so it does not cross the i-a/i-b line. *Defect:* the tool re-stamping ownership after a
  successful re-register (the registry left correct) — an ownership TAKEOVER through the ordinary tool call amendment-9
  MP-R4-1 names as the door, in the very function (`_comms_register`) the i-a builder edits to pass `session_keep_id`.
  *Wrong build:* RS1srv. *Receipts:* 25 files `2978 passed`; **full suite §4.5**; probe REF green / RS1srv red.
  **CLASS: NEW-CLASS (a new SEAM)** — the sidecar rules: amendment 10 routes the end-to-end REFUSAL pin to i-b (which would
  also kill RS1srv); the open question is only the window between the i-a build and i-b. Recommendation: the
  data-invariance pin rides r4b (one test; the harness and probe exist); the refusal stays i-b.

**SAME-CLASS / RULED survivors (bounds — no new pin demanded by me):**
- **G3** (narrowing on an axis no witness carries — trailing `-`/`_`): SAME-CLASS; amendment-9 R-2 already narrowed the header
  to "any axis a legal witness carries", so the bound is STATED in the instrument but not pinned. Cheapest closure: add
  `"a-"`/`"a_"` (and an all-digit `"00"`) to `_LEGAL_IDENTIFIER_WITNESSES` in amendment-10 C-1's union (ii). KP-G3 REF green /
  G3 red (§A.4).
- **PX2w** (the bound restated in WORDS): SAME-CLASS (amendment-10 C-4's accepted phrase bound). Prose defect: the pin
  docstring and amendment-10 C-4 call the birth-value leg "the ∀ half" — it is ∀ over DIGIT spellings only. One-sentence
  docstring correction; no pin.
- **C2** (different keep): RULED — amendment-10 C-2 (r4b-if-any, else i-b); KP-C2 is that row, REF green / C2 red.
- **TWR** (KB-2): the pinned bound working — survives the full suite, its control green on it (§4.5).

### 4.5 FULL-SUITE leg for every contract survivor (alone, `-n 12`, `run_full_r4a.sh` §A.6 — ≥23 GiB launch gate, process table clean, 12 GiB PID watchdog never fired, provenance printed)
Survivors of the 25 files combined — their anchors are pairwise disjoint (FXh: the fake's helper body · C2: the fake's
re-register branch + `agents.py` re-register branch · TWR: `agents.py` class header + imports · G3: the server SKIP gate ·
RS1srv: `_comms_register` after the registry call · PX2w: the refusal text), so a red in one cannot be masked by another:
- **COMBO = FXh + G3 + C2 + RS1srv + PX2w + TWR** (2026-09-25 07:05:47–07:16:18 EDT; 24 GiB at launch, lowest 17 GiB; 4 dirty
  paths = the six builds composed): **`11459 passed, 62 skipped, 3 xfailed, 7 warnings in 624.52s` — 0 failed, exit 0.
  All six survive the FULL suite.** (Same count as SAT: none of them is observed anywhere in the tree.)
- A survivor's liveness is proven by its kill-pin pair (§4.2): each build's mutation is RED under a probe that
  exercises it, so "survives" is not "dead code".

## 5b. P1b — QUANTIFIER TABLE (the invariants r4a pins or re-shapes; each GUARDED row carries its receipt)
| # | invariant | classification | receipt |
|---|---|---|---|
| Q1 | a re-register leaves `owner_principal`/`owner_agent`/`scope` untouched, ∀ callers (ruling §2.2 row 2) | **GUARDED by SEAM + by AXIS**: ∀ over the principal axis at the REGISTRY seam (4 sequences) | door-builds: **RS1srv** (tool seam) survives the full suite → MP-A3 (NEW-CLASS); **C2** (keep axis) survives → RULED am-10 C-2. Killed: RS1, RS1FX2 |
| Q2 | the fake mirrors the writer on re-register (parity + ABSOLUTE real side) | ∀ over the 4 sequences | RS1FX2 (both re-stamp, `fake == real`) KILLED on the absolute leg; FX2 KILLED. Keep axis → C2 (both sides) survives (as Q1) |
| Q3 | the SKIP gate never looks up a value that cannot be an identity (WIDENING) | ∀ over `_HOSTILE_IDENTIFIERS` (14 shapes incl. `"fixer.b"`) | G2 KILLED (`{'fixer.b': ['fixer.b']}`); reworded classes outside the corpus are the KB-2 bound's twin at the gate (not built separately) |
| Q4 | the SKIP gate looks up every legal identity exactly once (NARROWING) | **GUARDED by the witnesses' axes** (length 1, digit-lead, mid `_`, mid `-`, cap) | **G3** (trailing separator) survives the full suite → SAME-CLASS (R-2 states the bound); G1 KILLED on the cap witness |
| Q5 | the gate follows the SHARED decision (REPLACING) | ∀ over the (now 7) legal attributions | unchanged r4 instrument; X1 (r4 floor) killed at r4 — not re-run here (r4a only ADDED params to this leg) |
| Q6 | the fake's HEAD-RED guard cannot outlive its premise | **GUARDED by SPELLING**: shape pin (a `try` / no module-top import) ∪ effect pin (a SILENT skip) | **FXh** (no `try`, non-silent `getattr` fallback) survives the full suite → MP-A1 (SAME-CLASS). Killed: FXg, FXf, FXhS |
| Q7 | served refusal prose follows the constant | **GUARDED by SPELLING** (digit integers; three phrasings) — and OVER-FIRES | **PX2w** (words) survives the full suite → SAME-CLASS; **SH1** (a correct build) is REFUSED → MP-A2. Killed: PX2 |
| Q8 | no unswept emitter emits a relation (the FORK-A premise, now observed by packet 07) | ∀ derived generators via the FORK-A exact-set coupling | R5, R5b KILLED with r4's premise pin deleted (§4.2b) |
| Q9 | the identity charset TEXT has one spelling in production (KB-2 bound) | GUARDED by the paste threat model — BY RULING | TWR survives the full suite, its KNOWN BOUND control green on it — the bound, measured |

## 6a. P1c — REACH TABLE (every instrument r4a introduces or re-shapes; legs marked EMPIRICAL / CONSTRUCTION)
| # | instrument | reach: derived vs hand-list | coverage a checked variable? | effect vs proxy | one source (by MUTATION) | verdict |
|---|---|---|---|---|---|---|
| I-1 | shape pin `…predicate_import_is_at_module_top_and_UNGUARDED…` | ONE file (`_comms_fakes.py`) — a hand-constant, STATED (C-5, trigger named) | HEAD control (sees the guard) + 8 positive / 2 negative synthetic controls — EMPIRICAL (they ran green on REF) | SOURCE SHAPE — a proxy by design (allowlist-the-safe) | `_is_lorerunes_module` shared with I-2: **mutation PROOF HELD** (4/4 declared red, EMPIRICAL) | **MISSING on the proxy axis: FXh** (MP-A1) |
| I-2 | effect pin (predicate removed at every `lorerunes*` binding) | DERIVED by identity (`module_level_bindings_of`), anti-vacuity ≥ 1 home | anti-vacuity assert present; FXg KILLED (EMPIRICAL) | EFFECT (a hostile register on the fake) | same helper — PROOF HELD | SAFE (its stated blind spot — a non-silent fallback — is I-1's job; FXh escapes both) |
| I-3 | SKIP-gate legs over `_LEGAL_IDENTIFIER_WITNESSES` | the gate call site: ONE site by ruling (A4-bis); witnesses: ONE corpus imported by 3 consumers | the witness set is a hand-list of axes (R-2 states it) | EFFECT (registry reads via a fail-loud spy) | **corpus mutation PROOF HELD** (an illegal `"A_b"` reddens all 3 consumers, EMPIRICAL) | MISSING on uncarried axes → G3 (SAME-CLASS, stated) |
| I-4 | PX2 leg (birth value + phrases) | digit integers + 3 phrasings | — | EFFECT (served text) | the birth value is READ before patching (derived) ✓ | over-fires (SH1, MP-A2); words escape (PX2w, SAME-CLASS) |
| I-5 | RS1 pin + parity table (`_RE_REGISTER_EXPECTED_REAL`) | ONE seam (the registry) | a sequence missing from the table is a `KeyError` (fails closed) — CONSTRUCTION | EFFECT (the row read back from the store) | — | **MISSING at the tool seam: RS1srv** (MP-A3) |
| I-6 | premise coverage = packet-07 `_both_slices()` × FORK-A exact-set pin | hand-list of 2 generators, coupled to the DERIVED unswept set by the exact-set pin | FORK-A reds if the derived set grows or shrinks — CONSTRUCTION | EFFECT on emitted DDL text | — | SAFE by coupling (R5/R5b killed, EMPIRICAL) |
| I-7 | KB-2 control (`…REWORDED_or_ASSEMBLED_charset_is_NOT_named`) | 3 synthetic sources | — | the scanner's classification | — | a pinned bound working (TWR survives the full suite) |
Legs run: EMPIRICAL — I-1/I-2 shared-helper mutation, I-3 corpus mutation, FXg/FXh/FXhS/G3/RS1srv/R5/R5b builds; CONSTRUCTION —
I-5 fail-closed, I-6 coupling.

## 1. P7 — RED honesty, reproduced (lane `head` = unbuilt production at `1705ea3`, whose tests are byte-identical to `bf77fb9`'s; measured 2026-09-25)
- Run set: `files5.txt` (25 files), `-n 8`, one session at a time. Run 1 = r4a tests; run 2 = r4 tests (`git checkout e80a854 --
  loremaster/tests`, restored after: 0 dirty tracked). Script `red_at_head.sh` (§A.7) + adversary-r4's `red_diff4.py` (its labels
  read "r4"/"r3" — here r4a/r4).
- Tails: **r4a `190 failed, 2737 passed, 19 skipped, 51 errors`** · r4 `177 failed, 2719 passed, 19 skipped, 51 errors`.
- **r4-GREEN turned r4a-RED: 0 · NEW red ids: 13 · NEW green: 19 · gone: 1 (the deleted premise pin, green at HEAD) · red→green: 0**
  (2966 + 13 + 19 − 1 = 2997 ✓). The 13, each right-reason (the unbuilt seams): SKIP-gate `[a|0z|a_b|a-b|a×64]` ×5 —
  `AttributeError: module 'lorerunes' has no attribute 'is_legal_identifier'` · `…agree_on_outcome_class_and_stamps[hostile-13-
  name|session]` ×2 — `TypeError … unexpected keyword 'session_keep_id'` (the new `"fixer.b"` row) · `…refuses_a_hostile_identifier_
  before_any_store_write[fixer.b-name|session]` ×2 — `TxnDomainRejectionError` (the store ASSERT, the siblings' documented reason) ·
  `…hostile_legacy_row_is_refused_on_re_register_and_still_touches[fixer.b-name|session]` ×2 — the pin's own RED-at-HEAD message ·
  `…RE_REGISTER_door[consistent-then-householded-joiner-pair]` + `…REAL_writer_never_re_stamps_…` — `TypeError … 'session_keep_id'`.
  **The author's §RED is CONFIRMED on every count.**

## 8. Residuals (each with an individual verdict)
| # | residual | verdict |
|---|---|---|
| R-1 | HEAD moved `a8b84bc → 5b94961 → 1705ea3` during my run (amendment 10 + lead report) | docs only — `git diff --stat bf77fb9 1705ea3 -- loremaster lorerunes lorescribe loresigil scripts` is EMPTY; nothing graded moved |
| R-2 | the author's "14/14 PROOF HELD" | CORROBORATED for the 10 builds I rebuilt independently (RS1, FX2, RS1FX2, G1, G2, FXg, FXf, PX2, R5, R5b — each exact); FXf2, X3b, X3d, MP2DEF NOT rebuilt by me (X3b/X3d/MP2DEF were graded at r4; FXf2 is an author-only shape). My FXhS is a stronger X3d (module-top import kept) and reds on the effect pin as the author says X3d does |
| R-3 | parameter monoculture in r4a's new fixtures (brief focus 2) | the RS1 row and its parity row use ONE keep (`_PARITY_KEEP`) → the keep axis is exactly C2 (RULED); ONE seam → RS1srv (MP-A3). The legal corpus carries 5 axes, not the trailing-separator axis → G3 (SAME-CLASS). The PX2 perturbation uses one patched value (3, else 4) — sufficient: the birth value is read, not restated. The hostile corpus gains the dot. No further monoculture found |
| R-4 | R-A reading (ii) (brief focus 2: "can a guard evade it?") | reading (ii) opens no door I could construct beyond reading (i): FXh evades BOTH readings (its module-top import is from `lorerunes` itself). A guard hidden in a `lorerunes` production shim module is outside the test tree and adversarial-only — not built |
| R-5 | the shape pin flags ANY `try` around ANY `lorerunes*` import in the fake (e.g. `keep_scope`) | allowlist-the-safe by design; honest code in the fake has none today; the negative control `[submodule-top-import-and-an-unrelated-try]` proves a non-lorerunes `try` stays quiet. Accept |
| R-6 | C-3 metadata writes (status/heartbeat/model/task_id/cadence) by the joiner | amendment 10 describes them; my probe did not project those columns — UNMEASURED by me. RULED (i-b refusal) |
| R-7 | amendment-10 C-4's sentence "the birth-value leg is the ∀ half" | over-claims (digits only — PX2w); prose correction, rides MP-A1's docstring edit or i-b |
| R-8 | `module_level_bindings_of`'s KNOWN BOUND (module namespaces only) | irrelevant to I-2 (the fake reads a module global); accept |
| R-9 | C2 / SH1 builds fail ruff E501 | my inserted lines' length; a wrap fixes both and changes no behaviour (SH1's served string is unchanged by wrapping). Not a lint catch |
| R-10 | lore index at spawn showed `git_ref 5b94961` while my checkout read `a8b84bc` | the index was one docs commit AHEAD (amendment 10 landing); used only for unchanged-helper lookups (`module_level_bindings_of`, 2 DRY searches). No trust issue; not filed |
| R-11 | my deviations | DV-A (stray `git stash` in the lane mid-PX2w; restored; that verdict VOID and re-run) · the C-3 probe's blind first draft (caught by its own recorded measurement; fixed; re-run). Both disclosed in §4.2 |
| R-12 | adversary-r4's scratch dir survives on disk (`…/bd8e690b-…/scratchpad`) | read-only reuse (copied `my_ref_build_r4.py`, `my_wbs4.py` bodies, `red_diff4.py`); nothing written there |

## A. Instruments (pasted VERBATIM — scratch-only; my writable set is this report)
Scratch root: `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bab26354-cc66-4f18-b92e-6d27fa6ff922/scratchpad/inst`.
- `my_ref_build_r4.py` = adversary-r4's reference, md5 `3e419c7544454d632b8bbd0c460111e2`, verbatim in `REPORT-adversary-63c-i-a-r4.md` §A.1 @ `86379a4`.
- `red_diff4.py` = adversary-r4's, verbatim in `REPORT-adversary-63c-i-a-r4.md` §A.6 @ `86379a4`.

### A.2 `my_ref_leg_r4a.py`
```python
"""adversary-63c-i-a-r4a — my r4a leg on top of adversary-r4's my_ref_build_r4.py (md5 3e419c75…).

The builder's four granted edits (amendment-9 §W / builder brief): (1) the fake's HEAD-RED guard deleted AND
`is_legal_identifier` imported at MODULE TOP; (2) `_IDENTIFIER_CHARSET_PATTERN = AGENT_NAME_PATTERN.pattern`
(already in my_ref_build_r4.py's r4 leg); (3) `_REFUSAL_ID_SAMPLE_SIZE` docstring states WHY; (4) the
re-register sentence "from ANY caller, including a different householded principal". Written WITHOUT reading
the r4a author's make_ref_r4a.py. Each edit asserts its anchor occurs exactly once (#194).
Usage: uv run --no-project python my_ref_leg_r4a.py <scratch-root>   (AFTER my_ref_build_r4.py)
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


FAKES = "loremaster/tests/_comms_fakes.py"
PRINCIPALS = "loremaster/loremaster/principals.py"
AGENTS = "loremaster/loremaster/agents.py"
# (1) module-top import; the call-time read left by my_ref_build_r4.py's FORK-C leg is removed
edit(FAKES, "from lorerunes import is_blank\n", "from lorerunes import is_blank, is_legal_identifier\n")
edit(
    FAKES,
    "        from lorerunes import is_legal_identifier  # noqa: PLC0415 - call-time read (mutation-visible)\n\n"
    "        return is_legal_identifier\n",
    "        return is_legal_identifier\n",
)
# (3) the WHY docstring on the sample-size constant (a comment, not served text)
edit(
    PRINCIPALS,
    "#: The refusal names at most this many offending row ids (ruling §6 'ids, bounded'; amendment-4 MP-C).\n",
    "#: The refusal names at most this many offending row ids (ruling §6 'ids, bounded'; amendment-4 MP-C).\n"
    "#: WHY a bound at all: the refusal is read by an operator at cutover and must stay legible on a store with\n"
    "#: thousands of unscoped rows; the FULL count is always stated beside the sample, so nothing is lost.\n",
)
# (4) the re-register sentence, at the CREATE-only stamp
edit(
    AGENTS,
    '                "owner_agent": RecordID(AGENT_TABLE, agent_id),\n',
    "                # stamped on CREATE only: a re-register does NOT re-stamp owner_principal / owner_agent /\n"
    "                # scope — from ANY caller, including a different householded principal (ruling §2.2 row 2).\n"
    '                "owner_agent": RecordID(AGENT_TABLE, agent_id),\n',
)
print("adversary-r4a leg applied (module-top import + 2 docstrings)")
```

### A.3 `my_wbs_r4a.py`
```python
"""adversary-63c-i-a-r4a — wrong builds ON TOP of my reference (lane branch adv4a-ref = my_ref_build_r4.py +
my_ref_leg_r4a.py). Floor bodies (RS1/FX2/G1/G2/FXg/FXf/PX2) are adversary-r4's my_wbs4.py bodies, re-anchored
where my r4a leg moved the fake's import to module top. New builds are mine.

Usage: uv run --no-project python my_wbs_r4a.py <scratch-root> <WB-id> [--declared]
  --declared  print the DECLARED expected-RED node ids, resolved against collected_adv4a.txt (collect-only over
              the 25 files of files5.txt on adv4a-ref, taken BEFORE any wrong-build run) and exit.
Each edit asserts its anchor occurs exactly once (#194). A DECLARED set of [] predicts the build SURVIVES.
"""

import sys
from pathlib import Path

INST = Path(__file__).resolve().parent
ROOT = Path(sys.argv[1])
WB = sys.argv[2]

SERVER = "loremaster/loremaster/server.py"
AGENTS = "loremaster/loremaster/agents.py"
PRINCIPALS = "loremaster/loremaster/principals.py"
FAKES = "loremaster/tests/_comms_fakes.py"

GOV = "test_agent_governance_63c_i_a.py"
REG = "test_agent_registry.py"

SKIP_MUT = "test_the_SKIP_gate_moves_with_the_SHARED_is_legal_identifier"
SKIP_CORPUS = "test_the_SKIP_gate_never_looks_up_any_value_of_the_hostile_corpus"
FAKE_EFFECT = "test_the_fake_never_silently_skips_the_identity_decision_once_the_predicate_exists"
SHAPE = "test_the_fakes_predicate_import_is_at_module_top_and_UNGUARDED_once_the_predicate_exists"
RQ51 = "test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent"
REREG_PARITY = "test_the_fake_and_the_real_writer_agree_on_the_RE_REGISTER_door"
RS1_PIN = "test_the_REAL_writer_never_re_stamps_a_stamped_row_from_a_DIFFERENT_householded_principal"
JOINER = "consistent-then-householded-joiner-pair"
CAP = "a" * 64

# DECLARED expected-RED sets — (file fragment, [node fragments ALL required]). Written BEFORE any run.
DECLARED: dict[str, list[tuple[str, list[str]]]] = {
    # --- adversary-r4's floor: each must now be KILLED by its r4a pin ---
    "RS1": [(REG, [RS1_PIN]), (REG, [REREG_PARITY, JOINER])],
    "FX2": [(REG, [REREG_PARITY, JOINER])],
    "RS1FX2": [(REG, [RS1_PIN]), (REG, [REREG_PARITY, JOINER])],  # parity holds; the ABSOLUTE leg must red
    "G1": [(REG, [SKIP_MUT, f"[{CAP}]"]), (REG, [SKIP_CORPUS])],
    "G2": [(REG, [SKIP_CORPUS])],
    "FXg": [(REG, [FAKE_EFFECT]), (REG, [SHAPE])],
    "FXf": [(REG, [SHAPE])],
    "PX2": [(GOV, [RQ51, "perturbed-bound"])],
    # --- my new builds ---
    "FXh": [],  # module-top import KEPT; call-time getattr(lorerunes) with a NON-silent private-regex fallback, no try
    "FXhS": [(REG, [FAKE_EFFECT])],  # P0 control for FXh: same shape, SILENT fallback (None) -> effect pin must red
    "G3": [],  # SKIP gate narrows on an axis NO legal witness carries (trailing '-'/'_')
    "C2": [],  # C-2: real writer AND fake re-stamp owner+scope when the caller's KEEP differs from the stamped one
    "RS1srv": [],  # C-3 door: the TOOL (_comms_register) re-stamps owner_principal after a re-register
    "PX2w": [],  # PX2 in WORDS: "(first ten ids shown)" beside the constant-read slice
    "SH1": [(GOV, [RQ51, "perturbed-bound"])],  # CORRECT build (prose derived at call time): "(first N of M ids shown)"
    # --- added after the first lane pass (declared before THEIR run): the premise-pin deletion's DUAL + the KB-2 bound ---
    "R5": [("test_floor_calibration_schema.py", ["test_every_table_definition_is_IF_NOT_EXISTS"]),
           ("test_floor_calibration_schema.py", ["test_this_slice_contains_neither_a_relation_table_nor_a_sequence"])],
    "R5b": [("test_floor_calibration_schema.py", ["test_every_table_definition_is_IF_NOT_EXISTS"]),
            ("test_floor_calibration_schema.py", ["test_this_slice_contains_neither_a_relation_table_nor_a_sequence"])],
    "TWR": [],  # KB-2: reworded charset twin at a new production site — the pinned bound must SURVIVE
}


def edit(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{rel}: anchor occurs {count} times: {old[:80]!r}"
    path.write_text(text.replace(old, new))


if "--declared" in sys.argv:
    collected = (INST / "collected_adv4a.txt").read_text().splitlines()
    for file_fragment, node_fragments in DECLARED[WB]:
        hits = [n for n in collected if file_fragment in n and all(f in n for f in node_fragments)]
        assert hits, f"declared rule ({file_fragment}, {node_fragments}) matched NO collected node"
        for node in hits:
            print(node)
    raise SystemExit(0)

TOP_IMPORT = "from lorerunes import is_blank, is_legal_identifier\n"
HELPER_BODY = "        return is_legal_identifier\n"
GATE = "        if attribution is None or not AppContext._is_comms_charset_legal(attribution):\n"
FAKE_REREG = "        # status resets to active unconditionally (retired already excluded above).\n"
PRIVATE_RULE = 'lambda value: re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", value) is not None'


def keep_guard(import_line: str, fallback: str) -> None:
    """Restore the HEAD-RED guard shape (r4's FXg/FXf premise): top import back to is_blank only."""
    edit(FAKES, TOP_IMPORT, "from lorerunes import is_blank\n")
    edit(FAKES, HELPER_BODY,
         "        try:\n" + import_line + "        except ImportError:\n" + fallback + "        return is_legal_identifier\n")


def fake_restamp(condition: str) -> None:
    edit(FAKES, FAKE_REREG,
         f"        if {condition}:\n"
         "            self.db.scopes[agent_id] = keep_scope(session_keep_id)\n"
         "            self.db.owners[agent_id] = owner_principal_id\n" + FAKE_REREG)


def real_restamp(condition: str) -> None:
    edit(AGENTS, "        new_model = model if model is not None else existing.model\n",
         f"        if {condition}:\n"
         "            await self._query(\n"
         "                f\"UPDATE type::record('{AGENT_TABLE}', $rid) SET owner_principal = $owner, \"\n"
         "                \"scope = $scope\",\n"
         "                {\"rid\": agent_id, \"owner\": RecordID(PRINCIPAL_TABLE, owner_principal_id),\n"
         "                 \"scope\": keep_scope(session_keep_id)},\n"
         "            )\n"
         "        new_model = model if model is not None else existing.model\n")


RS1_COND = 'existing_row.get("scope") is not None and owner_principal_id is not None'
FX2_COND = "self.db.scopes.get(agent_id) is not None and session_keep_id is not None"
C2_REAL = ('existing_row.get("scope") is not None and session_keep_id is not None '
           'and str(existing_row.get("scope")) != keep_scope(session_keep_id)')
C2_FAKE = ("self.db.scopes.get(agent_id) is not None and session_keep_id is not None "
           "and self.db.scopes[agent_id] != keep_scope(session_keep_id)")

if WB == "RS1":
    real_restamp(RS1_COND)
elif WB == "FX2":
    fake_restamp(FX2_COND)
elif WB == "RS1FX2":
    real_restamp(RS1_COND)
    fake_restamp(FX2_COND)
elif WB == "G1":
    edit(SERVER, GATE,
         "        if (\n"
         "            attribution is None\n"
         "            or not AppContext._is_comms_charset_legal(attribution)\n"
         "            or len(attribution) > 32  # a 'cheap' private cap on the read budget\n"
         "        ):\n")
elif WB == "G2":
    edit(SERVER, GATE,
         "        if attribution is None or not (\n"
         "            AppContext._is_comms_charset_legal(attribution)\n"
         "            or re.fullmatch(r\"[a-z0-9]+\\.[a-z0-9]+\", attribution)  # dotted service names too\n"
         "        ):\n")
elif WB == "FXg":
    keep_guard("            from lorerunes.identifiers import is_legal_identifier  # noqa: PLC0415\n",
               "            return None\n")
elif WB == "FXf":
    keep_guard("            from lorerunes import is_legal_identifier  # noqa: PLC0415\n",
               "            import re  # noqa: PLC0415\n\n            return " + PRIVATE_RULE + "\n")
elif WB == "PX2":
    edit(PRINCIPALS, '                "half-applied store; "\n', '                "half-applied store (first 10 ids shown); "\n')
elif WB in ("FXh", "FXhS"):
    fallback = PRIVATE_RULE if WB == "FXh" else "None"
    edit(FAKES, HELPER_BODY,
         "        import re  # noqa: PLC0415\n\n"
         "        import lorerunes  # noqa: PLC0415 - call-time read: 'robust' if the predicate is ever absent\n\n"
         "        if getattr(lorerunes, \"is_legal_identifier\", None) is not None:\n"
         "            return is_legal_identifier\n"
         f"        return {fallback}\n")
elif WB == "G3":
    edit(SERVER, GATE,
         "        if (\n"
         "            attribution is None\n"
         "            or not AppContext._is_comms_charset_legal(attribution)\n"
         "            or attribution.endswith((\"-\", \"_\"))  # 'a dangling separator is never a real name'\n"
         "        ):\n")
elif WB == "C2":
    real_restamp(C2_REAL)
    fake_restamp(C2_FAKE)
elif WB == "RS1srv":
    edit(SERVER,
         "        registered_age_s = int((now - result.agent.registered_at).total_seconds())\n",
         "        registered_age_s = int((now - result.agent.registered_at).total_seconds())\n"
         "        if result.re_registered and principal_bare is not None and hasattr(self.agent_registry, \"_query\"):\n"
         "            # 'the owner follows the most recent registrant' — a TAKEOVER at the tool seam\n"
         "            await self.agent_registry._query(  # noqa: SLF001\n"
         "                \"UPDATE type::record('agent', $rid) SET owner_principal = type::record('principal', $owner)\",\n"
         "                {\"rid\": self.agent_registry._agent_id(session, agent), \"owner\": principal_bare},  # noqa: SLF001\n"
         "            )\n")
elif WB == "PX2w":
    edit(PRINCIPALS, '                "half-applied store; "\n', '                "half-applied store (first ten ids shown); "\n')
elif WB == "SH1":
    edit(PRINCIPALS, '                "half-applied store; "\n',
         '                f"half-applied store (first {_REFUSAL_ID_SAMPLE_SIZE} of {len(owned_unscoped_ids)} ids shown); "\n')
elif WB in ("R5", "R5b"):  # adversary-r4 my_wbs4.py bodies verbatim (lease slice anchors unchanged)
    relation = ('_define_relation_table("holds", LEASE_TABLE, TASK_TABLE)' if WB == "R5"
                else "_define_relation_table(TO_RELATION, MESSAGE_TABLE, AGENT_TABLE)")
    edit("loremaster/loremaster/store/surreal_schema.py",
         "        _define_field(LEASE_TABLE, LEASE_FENCE_EPOCH_COLUMN, \"int\", constraint=\"DEFAULT 0\"),\n"
         "    ]\n    return statements\n",
         "        _define_field(LEASE_TABLE, LEASE_FENCE_EPOCH_COLUMN, \"int\", constraint=\"DEFAULT 0\"),\n"
         "    ]\n"
         f"    statements.append({relation})\n"
         "    return statements\n")
elif WB == "TWR":  # adversary-r4 my_wbs4.py body verbatim
    edit(AGENTS, "class InvalidAgentIdentityError(AgentRegistryError):",
         "_LEGACY_NAME_RE = re.compile(r\"^[0-9a-z][0-9a-z_-]{0,63}$\")  # reworded class (KB-2)\n\n\n"
         "class InvalidAgentIdentityError(AgentRegistryError):")
    edit(AGENTS, "import logging\nimport secrets\n", "import logging\nimport re\nimport secrets\n")
else:
    raise SystemExit(f"unknown WB {WB}")
print(f"{WB} applied")
```

### A.4 `run_lane_r4a.sh`
```bash
#!/usr/bin/env bash
# adversary-63c-i-a-r4a lane driver (adapted from adversary-r4's run_lane4.sh): for each WB (REF = no build),
# reset LANE to adv4a-ref, resolve the DECLARED expected-RED set from collected_adv4a.txt (collect-only on
# adv4a-ref, taken BEFORE any wrong-build run), apply the build, assert provenance, run the 25 files of
# files5.txt (-n 8, ONE pytest session at a time, memory watchdog kills OUR pytest by PID < 12 GiB), diff
# observed-RED vs declared BOTH ways from junit, restore.
set -uo pipefail
INST=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bab26354-cc66-4f18-b92e-6d27fa6ff922/scratchpad/inst
LANE=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bab26354-cc66-4f18-b92e-6d27fa6ff922/scratchpad/ref
cd "$LANE" || exit 2
for WB in "$@"; do
  git checkout -q -f adv4a-ref && git clean -fdq -e REPORT-sidecar-63c.md
  [ -z "$(git status --porcelain | awk '!/REPORT-sidecar/')" ] || { echo "$WB: LANE DIRTY after reset — abort"; exit 2; }
  if [ "$WB" = REF ]; then : > "$INST/wb_${WB}.declared"; else
    uv run --no-project python "$INST/my_wbs_r4a.py" "$LANE" "$WB" --declared | sort > "$INST/wb_${WB}.declared" \
      || { echo "$WB: declaration failed"; exit 2; }
    uv run --no-project python "$INST/my_wbs_r4a.py" "$LANE" "$WB" >/dev/null || { echo "$WB: APPLY FAILED"; exit 2; }
    [ -n "$(git status --porcelain | awk '!/REPORT-sidecar/')" ] || { echo "$WB: build left the lane CLEAN"; exit 2; }
  fi
  .venv/bin/python -c "import loremaster,pathlib; assert pathlib.Path(loremaster.__file__).resolve().is_relative_to('$LANE'), loremaster.__file__" \
    || { echo "$WB: PROVENANCE FAILED"; exit 2; }
  if ps -eo comm=,args= | awk '$1 ~ /^(python|python3|pytest|uv)/ && /pytest/{f=1} END{exit !f}'; then echo "$WB: another pytest is running — abort"; exit 3; fi
  .venv/bin/python -m pytest -n 8 -q -p no:cacheprovider --junitxml="$INST/wb_${WB}.xml" $(cat "$INST/files5.txt") \
    > "$INST/wb_${WB}.log" 2>&1 &
  PID=$!; low=999
  while kill -0 "$PID" 2>/dev/null; do
    avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo); [ "$avail" -lt "$low" ] && low=$avail
    if [ "$avail" -lt 12 ]; then echo "WATCHDOG FIRED: ${avail} GiB — killing pytest PID $PID"; kill "$PID"; echo WATCHDOG > "$INST/WATCHDOG_FIRED"; fi
    sleep 5
  done
  wait "$PID"
  .venv/bin/python - "$INST/wb_${WB}.xml" > "$INST/wb_${WB}.observed" <<'PY'
import sys, xml.etree.ElementTree as ET
for case in ET.parse(sys.argv[1]).iter("testcase"):
    if case.find("failure") is not None or case.find("error") is not None:
        print(f"{case.get('classname', '')}::{case.get('name')}")
PY
  sort -o "$INST/wb_${WB}.observed" "$INST/wb_${WB}.observed"
  .venv/bin/python - "$INST/wb_${WB}.declared" "$INST/wb_${WB}.observed" <<'PY' > "$INST/wb_${WB}.diff"
import sys
declared = {l.strip() for l in open(sys.argv[1]) if l.strip()}
observed = {l.strip() for l in open(sys.argv[2]) if l.strip()}
def key(node):  # "path.py::Class::test[p]" / junit "pkg.mod.Class::test[p]" -> "Class::test[p]"; module-level -> "::test"
    parts = node.split("::")
    prefix = parts[-2] if len(parts) >= 2 else ""
    cls = "" if prefix.endswith(".py") else prefix.split(".")[-1]
    return f"{cls if cls[:1].isupper() else ''}::{parts[-1]}"
dk = {key(d): d for d in declared}
ok = {key(o): o for o in observed}
unexpected = sorted(set(ok) - set(dk)); still_green = sorted(set(dk) - set(ok))
print(f"declared={len(dk)} observed_red={len(ok)} unexpected_red={len(unexpected)} declared_still_green={len(still_green)}")
for u in unexpected: print("  UNEXPECTED RED:", ok[u])
for s in still_green: print("  DECLARED BUT GREEN:", dk[s])
PY
  echo "== $WB :: $(tail -1 "$INST/wb_${WB}.log") :: $(head -1 "$INST/wb_${WB}.diff") :: lowest ${low} GiB"
done
git checkout -q -f adv4a-ref && git clean -fdq -e REPORT-sidecar-63c.md
```

### A.5 `test_adv_r4a_killpins.py`
```python
"""adversary-63c-i-a-r4a — candidate kill-pins for the survivors (scratch only; copied into the lane's test dir).
Each is paired: GREEN on my reference (adv4a-ref), RED on its build (kp_pairs_r4a.sh)."""

from __future__ import annotations

import ast
from pathlib import Path

import test_agent_registry as registry_tests  # module import: a Test* class imported by NAME would be re-collected

_OTHER_KEEP = "sessionkeep8"


# --- KP-FXh: the fake's ONLY route to the predicate is the module-level import (allowlist the safe) --------------
def test_kp_fxh_the_fake_never_re_reads_the_predicate_off_a_lorerunes_module_object() -> None:
    import _comms_fakes

    tree = ast.parse(Path(_comms_fakes.__file__).read_text(encoding="utf-8"))
    rereads = [
        f"line {node.lineno}: {ast.unparse(node)}"
        for node in ast.walk(tree)
        if (isinstance(node, ast.Attribute) and node.attr == "is_legal_identifier")
        or (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in {"getattr", "hasattr"}
            and any(isinstance(arg, ast.Constant) and arg.value == "is_legal_identifier" for arg in node.args)
        )
    ]
    assert rereads == [], f"a call-time re-read of the predicate is a guard in waiting (FXh): {rereads}"


# --- KP-G3: a legal witness on an axis _LEGAL_IDENTIFIER_WITNESSES does not carry (trailing separator) -----------
async def test_kp_g3_the_skip_gate_looks_up_a_trailing_separator_identity() -> None:
    for witness in ("a-", "a_"):
        assert await registry_tests._traffic_line_lookups(witness) == [witness], witness


# --- KP-C2: a DIFFERENT KEEP on re-register leaves the stamps (amendment-10 C-2's registry-seam row), real + fake --
async def test_kp_c2_a_re_register_with_a_different_keep_keeps_the_stamps() -> None:
    from lorerunes.pdp import keep_scope

    harness = registry_tests.TestTheFakeRegistryMirrorsTheWriter63cIA
    first, second = ("alice_pid", registry_tests._PARITY_KEEP), ("alice_pid", _OTHER_KEEP)
    real = await harness._real_re_register_outcome(first, second)  # noqa: SLF001
    fake = await harness._fake_re_register_outcome(first, second)  # noqa: SLF001
    expected = ("re-registered", "alice_pid", True, keep_scope(registry_tests._PARITY_KEEP))
    assert real == expected, f"real={real!r}"
    assert fake == expected, f"fake={fake!r}"
```

### A.6 `test_adv_r4a_c3_probe.py`
```python
"""adversary-63c-i-a-r4a — C-3 MEASUREMENT (scratch only): the END-TO-END tool door for RS1. A householded joiner
(bob) calls `comms(action="register")` with the KEEPER's (alice's) agent name in the shared session. Records what
production does (refuse earlier? re-register? re-stamp?) and asserts the ruled ABSOLUTE outcome (ruling §2.2
row 2: owner_principal / owner_agent / scope UNTOUCHED, from ANY caller). P0 controls in the same test: a FOREIGN
principal (carol, not householded) is refused (the probe can SEE a refusal), and the joiner's OWN new agent
registers (the probe can SEE a joiner's write). Test store ws://127.0.0.1:18000 only (the harness reaps)."""

from __future__ import annotations

import json
import os
from typing import Any

from _governed_contract import credentialed_app_context
from _surreal_harness import run

from loremaster.store.surreal_schema import AGENT_TABLE

_OUT = os.environ.get("ADV_C3_OUT", "/dev/null")
_PROJECTION = f"SELECT id, owner_principal, owner_agent, scope, role FROM {AGENT_TABLE} WHERE name = $n"


def _bare(value: Any) -> str:
    text = str(getattr(value, "id", value))
    return text.split(":", 1)[-1] if ":" in text else text


async def _attempt(ctx: Any, **kwargs: Any) -> str:
    try:
        rendered = await ctx.comms(action="register", **kwargs)
    except Exception as error:  # noqa: BLE001 - a measurement records whatever surfaces
        return f"RAISED {type(error).__name__}: {str(error)[:200]}"
    return f"RETURNED: {str(rendered)[:200]}"


async def test_c3_a_householded_joiner_re_registers_the_keepers_agent(monkeypatch: Any, tmp_path: Any) -> None:
    async with credentialed_app_context(
        monkeypatch, tmp_path, principals={"alice": "member", "bob": "member", "carol": "member"}, dim=8
    ) as world:
        ctx, admin = world["ctx"], world["admin_conn"]
        world["holder"]["email"] = world["emails"]["alice"]
        await ctx.comms(action="register", agent="keeper-a", session="shared", role="builder")
        keep = await ctx._keep_store.get_by_key("session:shared")  # noqa: SLF001
        assert keep is not None
        await ctx._keep_store.add_household_member(keep_id=_bare(keep.id), member_email=world["emails"]["bob"])  # noqa: SLF001
        before = await run(admin, _PROJECTION, {"n": "keeper-a"})
        world["holder"]["email"] = world["emails"]["carol"]
        foreign = await _attempt(ctx, agent="keeper-a", session="shared", role="builder")
        after_foreign = await run(admin, _PROJECTION, {"n": "keeper-a"})
        world["holder"]["email"] = world["emails"]["bob"]
        own = await _attempt(ctx, agent="joiner-b", session="shared", role="builder")
        own_rows = await run(admin, _PROJECTION, {"n": "joiner-b"})
        # SAME role as the keeper registered with: a different role is refused by the identity-conflict rule
        # BEFORE the re-register path (measured: the first probe draft sent role="auditor" and was blind).
        joiner = await _attempt(ctx, agent="keeper-a", session="shared", role="builder")
        after = await run(admin, _PROJECTION, {"n": "keeper-a"})
        record = {
            "pids": world["pids"], "before": before, "foreign": foreign, "after_foreign": after_foreign,
            "own_new_agent": own, "own_rows": own_rows, "joiner_on_keepers_agent": joiner, "after": after,
        }
        with open(_OUT, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, default=str) + "\n")
        # P0 controls
        assert foreign.startswith("RAISED") or "not householded" in foreign, f"CONTROL: foreign not refused: {foreign}"
        assert after_foreign == before, "CONTROL: a refused foreign register mutated the row"
        assert own_rows and str(own_rows[0]["owner_principal"]) == f"principal:{world['pids']['bob']}", own_rows
        # the ruled ABSOLUTE outcome, at the TOOL seam
        assert len(after) == 1
        for column in ("owner_principal", "owner_agent", "scope"):
            assert after[0].get(column) == before[0].get(column), (
                f"TAKEOVER at the tool seam: {column} {before[0].get(column)!r} -> {after[0].get(column)!r}; joiner={joiner}"
            )
```

### A.7 `run_full_r4a.sh`
```bash
#!/usr/bin/env bash
# adversary-63c-i-a-r4a: FULL suite ALONE at -n 12 on the ref lane at adv4a-ref (+ optional WBs applied in order).
# Launch gate (lead grant FORK-MEM): MemAvailable >= 23 GiB AND no other python/pytest/uv pytest process; polls up to
# 30 min, else exits 4 ("blocked"). Watchdog kills OUR pytest by PID when MemAvailable < 12 GiB (then STOP).
# Usage: run_full_r4a.sh <label> [WB ...]
set -uo pipefail
INST=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bab26354-cc66-4f18-b92e-6d27fa6ff922/scratchpad/inst
LANE=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bab26354-cc66-4f18-b92e-6d27fa6ff922/scratchpad/ref
LABEL=$1; shift
cd "$LANE" || exit 2
git checkout -q -f adv4a-ref && git clean -fdq -e REPORT-sidecar-63c.md
for WB in "$@"; do uv run --no-project python "$INST/my_wbs_r4a.py" "$LANE" "$WB" >/dev/null || { echo "$WB apply failed"; exit 2; }; done
.venv/bin/python -c "import loremaster,pathlib; p=pathlib.Path(loremaster.__file__).resolve(); assert p.is_relative_to('$LANE'), p; print('loremaster.__file__ =', p)" || exit 2
deadline=$(( $(date +%s) + 1800 ))
while :; do
  avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
  busy=$(ps -eo comm=,args= | awk '$1 ~ /^(python|python3|pytest|uv)/ && /pytest/{n++} END{print n+0}')
  [ "$avail" -ge 23 ] && [ "$busy" -eq 0 ] && break
  [ "$(date +%s)" -ge "$deadline" ] && { echo "BLOCKED: avail=${avail} GiB busy_pytest=${busy} after 30 min"; exit 4; }
  sleep 20
done
echo "state: $(git status --porcelain | awk '!/REPORT-sidecar/' | wc -l) dirty paths; WBs: ${*:-none}; available at launch: ${avail} GiB; $(date '+%F %T')"
.venv/bin/python -m pytest -n 12 -q -p no:cacheprovider --junitxml="$INST/full_${LABEL}.xml" > "$INST/full_${LABEL}.log" 2>&1 &
PID=$!; low=999
while kill -0 "$PID" 2>/dev/null; do
  avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo); [ "$avail" -lt "$low" ] && low=$avail
  if [ "$avail" -lt 12 ]; then echo "WATCHDOG FIRED: ${avail} GiB — killing pytest PID $PID"; kill "$PID"; echo WATCHDOG > "$INST/WATCHDOG_FIRED"; fi
  sleep 5
done
wait "$PID"; rc=$?
echo "exit=$rc lowest MemAvailable during run: ${low} GiB; $(date '+%F %T')"
tail -1 "$INST/full_${LABEL}.log"
.venv/bin/python - "$INST/full_${LABEL}.xml" <<'PY'
import sys, xml.etree.ElementTree as ET
for case in ET.parse(sys.argv[1]).iter("testcase"):
    if case.find("failure") is not None or case.find("error") is not None:
        print("RED:", f"{case.get('classname','')}::{case.get('name')}")
PY
git checkout -q -f adv4a-ref && git clean -fdq -e REPORT-sidecar-63c.md
```

### A.8 `red_at_head.sh`
```bash
#!/usr/bin/env bash
# RED@HEAD re-derivation: lane head (unbuilt production at 1705ea3). Run 1 = r4a tests (as checked out); run 2 = r4
# tests (git checkout e80a854 -- loremaster/tests); restore; diff with adversary-r4's red_diff4.py. One session at a time.
set -uo pipefail
INST=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bab26354-cc66-4f18-b92e-6d27fa6ff922/scratchpad/inst
LANE=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bab26354-cc66-4f18-b92e-6d27fa6ff922/scratchpad/head
cd "$LANE" || exit 2
.venv/bin/python -c "import loremaster,pathlib; p=pathlib.Path(loremaster.__file__).resolve(); assert p.is_relative_to('$LANE'); print(p)"
.venv/bin/python -m pytest -n 8 -q -p no:cacheprovider --junitxml="$INST/red_r4a.xml" $(cat "$INST/files5.txt") > "$INST/red_r4a.log" 2>&1
echo "r4a tests: $(tail -1 "$INST/red_r4a.log")"
git checkout e80a854 -- loremaster/tests
.venv/bin/python -m pytest -n 8 -q -p no:cacheprovider --junitxml="$INST/red_r4.xml" $(cat "$INST/files5.txt") > "$INST/red_r4.log" 2>&1
echo "r4 tests:  $(tail -1 "$INST/red_r4.log")"
git checkout HEAD -- loremaster/tests
echo "dirty tracked after restore: $(git status --porcelain | awk '!/^\?\?/' | wc -l)"
.venv/bin/python "$INST/red_diff4.py" "$INST/red_r4a.xml" "$INST/red_r4.xml"
```

### A.9 `kp_pairs_r4a.sh`
```bash
#!/usr/bin/env bash
# kill-pin pairs: for each build (REF = the reference), reset the lane to adv4a-ref, apply the build, copy the
# kill-pins + the C-3 probe in, run ONLY those two files (-n 4, one session), print the tail + the red ids.
set -uo pipefail
INST=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bab26354-cc66-4f18-b92e-6d27fa6ff922/scratchpad/inst
LANE=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bab26354-cc66-4f18-b92e-6d27fa6ff922/scratchpad/ref
cd "$LANE" || exit 2
for WB in "$@"; do
  git checkout -q -f adv4a-ref && git clean -fdq -e REPORT-sidecar-63c.md
  [ "$WB" = REF ] || uv run --no-project python "$INST/my_wbs_r4a.py" "$LANE" "$WB" >/dev/null || { echo "$WB apply failed"; exit 2; }
  cp "$INST/test_adv_r4a_killpins.py" "$INST/test_adv_r4a_c3_probe.py" loremaster/tests/
  ADV_C3_OUT="$INST/c3_${WB}.jsonl" .venv/bin/python -m pytest -n 4 -q -p no:cacheprovider --junitxml="$INST/kp_${WB}.xml" \
    loremaster/tests/test_adv_r4a_killpins.py loremaster/tests/test_adv_r4a_c3_probe.py > "$INST/kp_${WB}.log" 2>&1
  echo "== $WB :: $(tail -1 "$INST/kp_${WB}.log")"
  .venv/bin/python - "$INST/kp_${WB}.xml" <<'PY'
import sys, xml.etree.ElementTree as ET
for c in ET.parse(sys.argv[1]).iter("testcase"):
    f = c.find("failure") if c.find("failure") is not None else c.find("error")
    if f is not None:
        print("   RED:", c.get("name"), "::", (f.get("message") or "").replace("\n", " ")[:260])
PY
done
git checkout -q -f adv4a-ref && git clean -fdq -e REPORT-sidecar-63c.md
```

### A.10 one-off commands (verbatim)
```bash
# lanes: ./scripts/scratch_copy.sh $S/ref ; ./scripts/scratch_copy.sh $S/head      (both rc=0, provenance asserted by the tool)
# ref:   cd $S/ref && git checkout -b adv4a-ref && uv run --no-project python inst/my_ref_build_r4.py $S/ref \
#          && uv run --no-project python inst/my_ref_leg_r4a.py $S/ref && uv run ruff check . && git commit (ff812c0, lane-local)
# files5.txt = adversary-r4's files4.txt (24) + loremaster/tests/test_floor_calibration_schema.py
# universe (BEFORE any wrong build): uv run pytest --collect-only -q -p no:cacheprovider $(cat files5.txt) | awk '/::/' > collected_adv4a.txt   # 2997
# lane 1: run_lane_r4a.sh REF RS1 FX2 RS1FX2 G1 G2 FXg FXf PX2 FXh FXhS G3 C2 RS1srv PX2w SH1
# lane 2: run_lane_r4a.sh PX2w R5 R5b TWR        (R5/R5b/TWR declarations added to my_wbs_r4a.py before this pass)
# kill-pin pairs: kp_pairs_r4a.sh REF FXh FXhS G3 C2 RS1srv ; (after the probe role fix) kp_pairs_r4a.sh REF RS1srv
# C-3 at HEAD: cd $S/head && cp inst/test_adv_r4a_c3_probe.py loremaster/tests/ && ADV_C3_OUT=inst/c3_HEAD.jsonl \
#   .venv/bin/python -m pytest -q -p no:xdist loremaster/tests/test_adv_r4a_c3_probe.py ; rm the copy
# full suites: run_full_r4a.sh SAT ; run_full_r4a.sh COMBO FXh G3 C2 RS1srv PX2w TWR
# currency: uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff   (main checkout; lane ref @ adv4a-ref)
# one-source (shared helper), lane ref @ adv4a-ref:
#   scripts/mutation_proof.py --file loremaster/tests/test_agent_registry.py --anchor '    return module_name is not None and (' \
#     --replacement '    return False and (' --expect-red <the 4 ids of mp_shared_home.declared, from collected_adv4a.txt> \
#     -- .venv/bin/python -m pytest -q -p no:cacheprovider -p no:xdist loremaster/tests/test_agent_registry.py \
#        -k 'never_silently_skips or predicate_import_is_at_module_top or import_shape_scanner'      -> PROOF HELD, restored byte-exact
# one-source (legal corpus): cp -a test_comms_schema.py backup; '"a_b",' -> '"A_b",'; collect-only | awk '/A_b/' (+ the corpus-control id)
#   = DECLARED (3 ids) BEFORE the run; pytest -p no:xdist test_agent_registry.py -k 'SKIP_gate or accepts_a_valid_identifier' -> 3 failed;
#   both-ways comm diff empty; restored from the content backup, md5 re-checked
# RED@HEAD: red_at_head.sh
# corpse sweep: git ls-files | while read f; do awk -v F="$f" '/premise_no_generator|ENFORCED_sweep_cannot_see|emits_a_relation_the/ {print F":"FNR}' "$f"; done
```

## VERDICT
**CONTRACT INSUFFICIENT** (graded `bf77fb9`, measured 2026-09-25; HEAD-at-report `1705ea3`, docs-only ahead).

The r4a addendum does what amendment 9 asked of it — the r4 floor is 7/7 dead on its declared pins, RS1's row carries
the absolute real side (RS1FX2 proves it), the premise-pin deletion is covered by packet 07 over the full suite, the
contract is satisfiable (`11459 passed` on an independent reference) and every author count reproduces. It is
insufficient on three concrete pins:
1. **MP-A3 · NEW-CLASS** — the GATING takeover door is pinned at the registry seam only; a tool-seam re-stamp (RS1srv)
   survives the full suite. The test that should exist: an end-to-end ownership-invariance pin for a householded
   joiner's re-register through `AppContext.comms(action="register")` (green at HEAD and on a correct build).
2. **MP-A1 · SAME-CLASS** — FXh (a `try`-free guard with a non-silent private fallback) survives the full suite and
   falsifies the shape pin's "ANY spelling" and amendment-9's "any fallback" claims. The test that should exist: clause
   (iii) — no call-time re-read of `is_legal_identifier` off a module object in `_comms_fakes.py` — or, at minimum, a
   pinned KNOWN BOUND with both sentences narrowed.
3. **MP-A2 · satisfiability** — row 5's phrase leg refuses the correct prose `(first N of M ids shown)`. Change: strip
   the full count from the residue before the phrase leg (or drop the `N … shown` alternative).
SAME-CLASS bounds (no new pin demanded): G3 (fold `"a-"`/`"a_"`/`"00"` into am-10 C-1's union), PX2w (docstring
narrowing). RULED: C2 (am-10 C-2). Working as designed: TWR. **No LIVE-PRODUCTION-DEFECT.**
