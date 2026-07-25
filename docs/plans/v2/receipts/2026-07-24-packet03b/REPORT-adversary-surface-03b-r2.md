brief-base v6 read

> **⚠ ARCHIVAL CORRECTION HEADER (lead, 2026-07-25 — gate residual R5).** This report's
> FINAL VERDICT section, below, reads **CONTRACT INSUFFICIENT**. **That verdict is
> SUPERSEDED and is NOT the state of the contract.** It was answered by the surface fix
> waves and the contract was **CERTIFIED SUFFICIENT** at `57d8677`
> (*"SURFACE CONTRACT CERTIFIED — CL3 lands the terminating paragraph allowlist"*); the
> certification is recorded in the INDEX Log entry of 2026-07-24 and re-confirmed by the
> merged-build gate (`REPORT-merged-gate-03b.md`, VERDICT **GO**). A reader retrieving a
> span of this report in isolation would otherwise read INSUFFICIENT as current — the
> exact hazard the merged-build gate filed as residual R5. The report's *findings* remain
> valid as the record of what the adversary found; only its headline verdict is stale.

**Graded at:** repo `feat/surreal-unification` HEAD `03b93d3`, working tree clean, 2026-07-24.
**Graded set:** `git diff 0223291..HEAD` over `test_comms_tool.py` · `test_comms_promise_registry.py` ·
`test_message_ledger.py` · `test_comms_render_architecture.py` · `test_comms_wiring.py`.
**Design authority read FIRST (contract-blind):** `docs/plans/v2/03b-design-rulings-r2.md` (§A/B1–B15/
A-GRAFT/§G) · `docs/plans/v2/03b-comms-message-surface.md` · the committed baseline contract at
`git show 0223291:` · production at HEAD (incl. the `91ea5be` skew-wording amendment).
**Every probe ran OUTSIDE the repo**, at `/home/ejprice/scratch/adv-surface-03b-r2`
(built by `scripts/scratch_copy.sh`). **No repo file was edited except this report**
(`git status --short` → empty).

---

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT.**
- **PROVENANCE:** `loremaster.__file__ = /home/ejprice/scratch/adv-surface-03b-r2/loremaster/loremaster/__init__.py` — scratch, not home (§1).
- **P1 HEADLINE — 11 of 35 wrong builds SURVIVED with ZERO new failures**, and **the contract is UNSATISFIABLE**: 3 pins are RED on a correct reference build and no build in the escape space fixes them (§3.B3/§3.B4).
- **THE WORST SURVIVOR — FK-6 is entirely unpinned.** A build where `drain` NEVER serves the shared brief-skew block scores **identically** to the correct build (3F/1170P, 0 new failures). Production at HEAD **already teaches** `"surfaces at their next heartbeat or drain"` (`91ea5be`); nothing in the contract makes that true. A lying teach, on the trust doctrine's own axis, shipped by construction (§3.B1).
- **THE SECOND WORST — the whole served-TEACHING surface is invertible.** An instructions block teaching the exact OPPOSITE of all seven B9 clauses passes **9/9** clause pins; two tool-schema descriptions teaching the opposite of `set_status`/`peek` pass **11/11**. Full contract: 0 new failures either way (§3.B5).
- **QUANTIFIER TABLE (P1b): §2 — 41 invariants classified; 15 GUARDED, every one with a door-build receipt.**
- **MISSING PINS: 6 BLOCKER · 5 CRITICAL · 4 MAJOR** — each named as the test to write + the defect it catches (§4).
- **SATISFIABILITY (C-DEF law): FAILS.** Reference build → **3 failed / 1170 passed**; ruff clean; `./scripts/typecheck.sh` → **0 errors, 149 files** (HEAD baseline: **92** errors in the 2 RED files — re-derived, the brief's "~86+6" is 92).
- **RED HONESTY (P7): CLEAN.** 270F/903P reproduced exactly; **zero** collection/import errors; all 270 classified to genuinely-absent symbols/claims (§5).
- **AUTHOR CLAIMS (P4): 8 of 9 MP obligations reproduce; MP-FK2 arm 2 is a VACUOUS mutation; MP-B12's "and nothing else in the file" is an over-claim for drain.** The wording agent's M1 shared-constant mutation reproduces **exactly**: 270F→293F, +23 across four modules, 0 recovered (§6).
- **P5: the message fake CAN fail** (2 mutations, 2 REDs, restored byte-exact) — but **both REDs land only in `test_message_ledger.py`; zero in the surface contract** (§7).
- **Residuals with individual verdicts: §8. Corpse sweep (P6): §9 — one live doc corpse.**

---

## 1 — Method and its controls (P0)

| leg | receipt |
|---|---|
| scratch provenance | `./scripts/scratch_copy.sh /home/ejprice/scratch/adv-surface-03b-r2` → `loremaster -> /home/ejprice/scratch/adv-surface-03b-r2/loremaster/loremaster/__init__.py`; re-asserted inside **every** wrong-build run by `wb.sh` (`assert loremaster.__file__.startswith(ROOT)`), non-zero exit otherwise |
| reference-first, contract-blind | The reference was authored from `03b-design-rulings-r2.md` + the committed `0223291` vocabulary ONLY, then **FROZEN by md5 + content copy**, and only then was `git diff 0223291..HEAD` opened. Freeze receipt: §1.1 |
| restore integrity | `wb.sh` restores from **content** (`cp -a` of `server.py.frozen`/`config.py.frozen`) and then `md5sum -c` — an MD5 list is a detector, not a backup |
| probe can SEE the thing (positive control) | every "SURVIVED" verdict is a `comm -13` against the reference's own failure set, so a survivor is *strictly no worse than correct*; every "CAUGHT" verdict names the pins. The P2 perturbation carries an explicit **correct-build green leg** (§4.C2) |
| **probe P0-FAILURE, self-caught and reported** | **(a)** My first reference called the skew helper as `self._comms_brief_skew_lines(...)`; the house idiom is the UNBOUND `AppContext._x(self, ...)` (because the harness is a `SimpleNamespace`). 8 pins were RED for **my** reason, not the contract's. Corrected, re-frozen, re-run — the 8 went green. **(b)** My N=7 perturbation's first "control" leg ran on a tree still carrying WB29's mutation (`wb.sh` restores at START, not END) and reported a false RED on the correct build. Re-run cleanly: **2 passed**. **(c)** My `WB14` (send remainder from the window) is a **NON-mutation** — the ledger sets `recipient_count = len(deduped)` and `recipient_names = sorted(...)` of the same set, so the two expressions are identically valued. Reported as a discarded probe, not a finding. **(d)** My first `MP-FK2` arm reproduced the author's wording and was likewise vacuous — see §6. |

### 1.1 — Reference build: freeze receipt

Recipe: `REFBUILD/apply_reference.py` (a single anchored-substitution script; every anchor asserted
unique, so it fails loud rather than silently mis-patching). Files changed: `loremaster/loremaster/server.py`,
`loremaster/loremaster/config.py`.

```
FROZEN (pre-graded-set-read) 2026-07-24T09:27:56-04:00
5fa1b35240cc07dc735cacdd74ba51cd  loremaster/loremaster/server.py
bdbda576ee327e3f0c547dccf2fcbd22  loremaster/loremaster/config.py
7fb6c5fadd8d787fbbcbb2f177eb9d48  REFBUILD/apply_reference.py
```

Against the frozen, contract-blind reference the contract ran **53 failed / 1120 passed** (from a
270F baseline: **217 pins turned green off the rulings alone**). Every one of the 53 was adjudicated
four ways (§3.A). After correcting my own idiom defect and **converging the reference onto the
contract's pinned SHAPES** (signatures, chosen literals, prose casing — a documented convergence,
not a grading step), the reference stands at **3 failed / 1170 passed**:

```
c65e60253ada84032b1b3e1a15d5d1bc  loremaster/loremaster/server.py   (converged reference)
bdbda576ee327e3f0c547dccf2fcbd22  loremaster/loremaster/config.py
$ uv run ruff check loremaster/loremaster/server.py   -> All checks passed!
$ ./scripts/typecheck.sh                              -> loremaster OK (149 source files, 0 errors)
$ uv run pytest -n auto -q <the five files>           -> 3 failed, 1170 passed, 14 skipped
```

**⚠ POST-LINT LEG, a real builder cost the contract does not carry:** the ruled validation order
(B1 steps 2+6: the `to[]` charset loop **and** the `set_status` vocabulary check) pushes
`AppContext.comms` to **13 branches** and ruff fails it with `PLR0912 Too many branches (13 > 12)`.
My reference had to extract `_validate_comms_identities`. Nothing in the contract anticipates this;
a builder will hit it, and if they extract differently the four charset pins still pass. **Flag, not
a blocker** — but the packet's "satisfiability includes the post-lint leg" is only true after a
refactor nobody specified.

---

## 2 — P1b THE QUANTIFIER TABLE

`∀` = pinned over the transform's inputs. **GUARDED** = pinned only where a fixture value, a
monoculture, an unreachable branch, or a named failure-mode keeps the bad outcome away. Every
GUARDED row carries a **door-build receipt**: either a surviving wrong build (a finding) or the pin
that killed the door. WB ids resolve in §3/§10.

### B1/B2 — the dispatcher and `send`

| # | invariant | class | receipt |
|---|---|---|---|
| 1 | every `to[]` entry is charset-validated pre-touch | **∀** | WB11 → 3 RED (`…CharsetValidatedBeforeAnyStoreTouch` ×2 + `test_charset_beats_the_foreign_param_law`) |
| 2 | broadcast = the CALLER's session only | **∀** | WB7 → 4 RED, incl. the omitted-`session` two-session fixture |
| 3 | **explicit recipients resolve session-SCOPED** | **GUARDED** (no cross-session `to=` fixture exists) | **WB8 SURVIVED 0 new.** Positive control (§3.C1): the unscoped build *delivers to another session's agent*; the reference refuses. **BLOCKER-adjacent, CRITICAL missing pin** |
| 4 | a retired recipient is a teaching reject | **∀** | WB9 → 2 RED |
| 5 | `set_status` is a closed vocabulary | **∀** (4 hostile values parametrized) | WB10 → 5 RED |
| 6 | the `set_status` reject is PRE-touch | **∀** | WB22 → 1 RED (`test_the_reject_never_touches_the_callers_row`) |
| 7 | `set_status` never writes the sender's status row | **∀** (active/idle/parked + a no-`set_status` control leg) | no door found; the 3-leg fixture is genuinely discriminating |
| 8 | a rejected send writes no row and no edge | **∀** | inherited committed pins, still green under every mutation |
| 9 | the send receipt's recipient list is **capped at the SHARED `_COVERAGE_NAMES_CAP`** | **GUARDED — small-N monoculture (every fixture has 1 recipient)** | **WB25 (never caps) SURVIVED 0 new · WB26 (private cap of 3 — the #102 door) SURVIVED 0 new · WB29 (capped variant unreachable) SURVIVED 0 new.** P2 pair in §4.C2 |
| 10 | the remainder is the TRUE count, never window-derived | **GUARDED — vacuous at the ledger** | probe discarded (§1 P0-(c)): `recipient_count ≡ len(recipient_names)` in production, so no wrong build exists here. **Honest verdict: nothing to pin** |
| 11 | broadcast renders a COUNT, not a name dump | **GUARDED — no broadcast fixture exceeds the cap** | **WB27 (count from a capped window) SURVIVED 0 new.** P2 pair in §4.C2 |
| 12 | the ack-duty teach emits IFF `grade=='directive'` | **∀** | WB23 → 2 RED (its proof + `test_no_dead_registry_entries`) |
| 13 | the question teach emits IFF `Message.question` | **∀** (no-emit leg is a *directive that is not a question*) | WB19 → 1 RED. MP-B33 discharged |

### B4/B13/B14/B15 — `drain`

| # | invariant | class | receipt |
|---|---|---|---|
| 14 | the window defaults from `comms.drain_limit` | **∀** | WB12 → 2 RED |
| 15 | the drain cap is its OWN constant | **∀** | WB13 → 1 RED |
| 16 | the below-one message teaches THAT action's cap | **∀** (parametrized fleet+drain) | covered by the parametrized pin; no door found |
| 17 | header counts the WHOLE pending set | **∀** | WB15 → 4 RED |
| 18 | elision `more == next_limit == total − shown` | **∀** (two arithmetic fixtures, pairwise-distinct) | WB3 → 2 RED. MP-B15 discharged |
| 19 | bodies are FENCED, verbatim, over-wide | **∀ … but the pin set is SELF-CONTRADICTORY** | MP-FK1a → 5 RED · MP-FK1b → 4 RED. **AND: `test_the_header_count_is_UNAFFECTED_by_a_hostile_body` is GREEN on both wrong builds and RED on the correct one — §3.B3** |
| 20 | the `{context}` cell is task-then-thread, thread suppressed on default | **∀** | WB4 → 1 RED (MP-B14) · WB20 → 5 RED |
| 21 | the thread comparand is the ARGUMENT | **∀** | WB4 (the literal-vs-argument leg) |
| 22 | `ACK REQUIRED` keys on `acked_at`, never `seen_at` | **∀** | WB5 → 2 RED |
| 23 | `ACK REQUIRED` gates **and lists** directives only | **∀** (the AC-10 mixed-grade fixture) | WB6 → 2 RED |
| 24 | the taught command names EVERY demanded seq | **∀** (AC-09 split at `action=ack `) | WB6 reddens it; the split-and-compare is real |
| 25 | the trailer is WINDOW-scoped | **GUARDED — one elided-directive fixture** | no surviving door found; the fixture does exceed the cap (limit < directive count), so the small-N law is satisfied here |
| 26 | peek NEVER renders the trailer | **∀** (render + dispatcher legs) | WB21 → 2 RED |
| 27 | the re-served-after-ack line keys on `acked_at` | **∀** (grade held constant on both legs) | WB20 → 5 RED. MP-B42 discharged |
| 28 | the refs cell is capped + counted | **GUARDED — no fixture exceeds the cap** | **WB28 (refs uncapped) SURVIVED 0 new** |
| 29 | **drain serves the shared brief-skew block (FK-6)** | **GUARDED — by NOTHING. Zero pins.** | **WB1 SURVIVED 0 new (identical 3F/1170P). BLOCKER — §3.B1** |
| 30 | **the skew block is ONE implementation, not a clone (D5)** | **GUARDED — by NOTHING** | **WB18 (private clone) SURVIVED 0 new. BLOCKER — §3.B2** |
| 31 | a drain does not un-park an `input_required` agent | **∀** | inherited touch-layer pins; drain leg present and green |

### B5 — `ack`

| # | invariant | class | receipt |
|---|---|---|---|
| 32 | the render has a HOME for every `AckOutcome` value | **∀** (set-equality against the ledger constants) | present and load-bearing |
| 33 | **each requested seq lands in the group its OWN outcome names** | **GUARDED — the mixed pin only asserts each seq appears SOMEWHERE** | **WB33 (acked ↔ already_acked groups SWAPPED) SURVIVED 0 new. BLOCKER — §3.B6.** Control: WB34 (unknown ↔ not_addressed swapped) → 1 RED, so the probe family demonstrably *can* fire |
| 34 | a NON-ADJACENT duplicate reports in BOTH groups | **∀** | WB32 → 1 RED |
| 35 | the receipt's own counts are the result's counts | **GUARDED** | WB32 (counts swapped) → 1 RED — caught, but only via the duplicate pin's `"acked 2 of 3"` literal |
| 36 | `note recorded` emits IFF a note AND `acked_count>0` | **∀** (the no-emit leg CARRIES a note) | WB17 → 1 RED. MP-B53 discharged |
| 37 | within-group ORDER / duplicate multiplicity | **GUARDED** | WB16 (dedupe + re-sort) SURVIVED 0 new. **Ruling ambiguity, not a defect** — §A-GRAFT re-expressed R1 as MEMBERSHIP, retiring B5's request-order clause. Flagged in §8 |

### B9/B12 — teaching + wiring

| # | invariant | class | receipt |
|---|---|---|---|
| 38 | each verb's handler CALLS its render | **∀** (per-verb, B12) | WB2a → 2 RED · WB2b → 7 RED · WB2c → 3 RED. **The struck adversary's headline blocker is CLOSED** |
| 39 | `build_app_context` constructs a `MessageLedger` | **∀** (with a `brief_ledger` positive control) | present; RED at HEAD for the right reason |
| 40 | **the instructions block teaches the seven B9 clauses** | **GUARDED — `_assert_ordered` is a case-sensitive `str.find` sequence** | **WB31b (all seven clauses INVERTED) → 9/9 clause pins GREEN, full contract 0 new. BLOCKER — §3.B5** |
| 41 | **the tool schema teaches `set_status`/`peek`/`to`/`grade` honestly** | **GUARDED — same instrument** | **WB30 (set_status + peek descriptions INVERTED) → 11/11 pins GREEN, full contract 0 new. BLOCKER — §3.B5** |

---

## 3 — THE FINDINGS

### 3.A — Four-way adjudication of the 53 pins RED on the frozen, contract-blind reference

| bucket | n | verdict |
|---|---|---|
| **reference defect** — my free wording differed from the contract's chosen literals (`note recorded on the {acked} newly acked message(s)`, the `re-served after ack:` group line, the FK-1 row templates without the trailing colon, the send thread cell I invented) | 24 | **contract correct.** The contract's choices are legitimate B8.1 registry growth |
| **reference defect** — signature (`_render_comms_ack(..., note=)` vs my `note_recorded=`) | 21 | **contract correct** — `note: str \| None` is the stronger shape (it can render the note) |
| **reference defect** — my house-idiom error (unbound `AppContext._x(self,…)`) | 5 | **mine**; corrected, §1 P0-(a) |
| **PIN DEFECT** | 3 | **§3.B3 + §3.B4** — RED on a correct build |

**Ruling ambiguity flagged (not a RED, but it admits two builds):** B3.2 rules a thread cell on the
send receipt ("thread-cell suppression … stands and grafts"), yet §A-GRAFT gives the committed
receipt templates no `{thread}` slot and lists no additive template for it. I built one and the
classification pin correctly reddened it; the contract has none. **Reading A** (no thread cell on
send; the thread reaches the reader only via the question teach) is what the contract implements and
is defensible under A-GRAFT's "committed vocabulary wins". **Reading B** (an additive thread line)
is what B3.2's surviving semantic clause says. I would pick A — but the ruling should say so, or a
builder reading B3.2 will add a line and be reddened by the classification pin for it.

---

### 3.B1 — BLOCKER: FK-6 is pinned by NOTHING, and production already claims it

**The wrong build:** `_comms_drain` never assembles or passes the brief-skew block.

```
$ REFBUILD/wb.sh WB1 REFBUILD/mut_WB1_no_skew_in_drain.py
WB1 applied
3 failed, 1170 passed, 14 skipped in 27.26s
--- NEW failures caused by this mutation (EMPTY == the contract is BLIND):
--- count: 0
```

Reference: `3 failed, 1170 passed`. **Byte-identical.** Search receipts:

```
$ grep -n "skew" loremaster/tests/test_comms_tool.py | grep -i "drain"       -> (no output)
$ grep -rn "skew_lines\|_render_comms_skew_block\|_comms_brief_skew" loremaster/tests/*.py -> (no output)
```

**Why this is the worst finding in the packet.** Production at HEAD (`91ea5be`) already serves
`"…; surfaces at their next heartbeat or drain"` in four literals, and the registry's own predicate
descriptions now read *"emitted by EVERY action that serves the shared skew block (heartbeat and,
per FK-6, drain)"* (`test_comms_promise_registry.py`, the four skew entries). The E-S5(c) amendment
was justified as **strengthen-only** — *"the amended prose is strictly MORE true — it names both
verbs that measurably surface it."* **That justification is FALSE until FK-6 lands, and the contract
does not require it to land.** A builder who satisfies this contract perfectly ships a served teach
that names a verb which does not do the thing — the exact C5(c) teaching-vs-behaviour failure the
trust doctrine makes the acceptance criterion.

The packet file's deploy-gate condition (`03b93d3`) *acknowledges* this and routes it to the **deploy
smoke**. A smoke is not a contract pin: it runs after the builder is finished, it is not what a
builder is graded against, and by then the wording is committed. **A gate that fires after the work
is done is a discovery, not a guard.**

**Second-order (also unpinned):** because §B4.1 makes the drain read the brief ledger, a drain now
*fails when the brief ledger is down*. That coupling — ruled deliberately, "no special degradation"
— has no pin either.

---

### 3.B2 — BLOCKER: D5's routing-is-not-sharing door is wide open

Design ruling **D5** names this exact wrong build and says it is *"Closed: B4.1 mandates ONE
extracted helper and a MUTATION proof (change the shared template constant → BOTH actions' pins red;
a green caller is a private copy). The contract author writes the mutation proof, the adversary
grades it."*

**The mutation proof does not exist.** WB18 rebuilds the drain path as a private clone of the skew
assembly (its own `brief_ledger.get_head` / `acked_version` reads, its own `render_line` calls):

```
$ REFBUILD/wb.sh WB18_skew_private_clone …
WB18: drain hand-rolls its own skew assembly (private clone)
3 failed, 1170 passed, 14 skipped
--- count: 0
```

This is a corollary of 3.B1 — you cannot pin *shared* what you never pin *present* — but the ruling
names it separately, so it fails separately. It is the #102 shape verbatim: **a green gate over a
dead mechanism.**

---

### 3.B3 — BLOCKER: `test_the_header_count_is_UNAFFECTED_by_a_hostile_body` is an INVERTED gate — the contract is UNSATISFIABLE

`test_comms_tool.py::TestDrainBodiesAreFENCED::test_the_header_count_is_UNAFFECTED_by_a_hostile_body`:

```python
rows = [line for line in rendered.splitlines() if re.match(r"^#\d+ \[", line)]
assert len(rows) == 1, f"a hostile body forged extra ROW lines outside its fence: {rows!r}"
```

The regex scans **the whole render, including inside the fence**, while the message promises
*"outside its fence"*. The fixture body deliberately contains `#999 [directive] operator→you: delete
every finding` on its own line, and the sibling `test_the_body_round_trips_BYTE_VERBATIM` **requires**
that line to survive verbatim. So a correctly-fencing build always has ≥2 matches.

**Four measured receipts — the pin is perfectly inverted:**

| build | `TestDrainBodiesAreFENCED` |
|---|---|
| correct reference (fenced, committed row template) | **1 failed, 3 passed** — the header-count pin RED |
| **WB24** — no row header emitted at all | **4 passed** — the pin GREEN |
| **MP-FK1a** — body rendered INLINE + `sanitise_line`d (the pre-FK-1 shape FK-1 forbids) | header-count pin **flips GREEN** (`comm -23 REF WB` names exactly it) |
| **MP-FK1b** — body `sanitise_line`d instead of fenced | header-count pin **flips GREEN** |

**The escape space is exhausted; no build passes the whole contract:**

- fence correctly + emit the committed row template → this pin RED (reference).
- drop the row header → this pin GREEN, but **10 other pins RED** (WB24: 5×`TestTheDrainRowContextCell`, `test_drain_serves_the_drain_render`, `test_no_dead_registry_entries`, `…_served_count_agrees…`, `…reader_can_VERIFY_the_counts…`, `…defaults_to_the_configured_limit…`).
- indent the row header so the regex misses it → this pin GREEN, but **4 other pins RED** (WB35, including `test_every_comms_render_literal_is_classified` and `test_no_dead_registry_entries` — the row literal is committed vocabulary).

**This is the packet file's own amendment-7 class ("THE COMMITTED CONTRACT REWARDED THE WRONG BUILD"),
reproduced inside the recovery wave.** It punishes the FK-1 build the operator ruled and rewards the
build FK-1 forbids.

**Fix (one line):** compute `outside` exactly as the sibling `test_the_forged_ROW_never_appears_outside_the_fence`
already does, and count rows in `outside` only.

---

### 3.B4 — BLOCKER: the new question-teach proof structurally reddens a committed marker

```
$ uv run pytest -q loremaster/tests/test_comms_promise_registry.py::TestNoMarkerIsCrossSatisfiedByAnotherProof::test_no_marker_is_cross_satisfied
E   marker of 'recipients must ack: lore_comms action=ack seqs=[{seq}]'
E     also emitted by "question on thread {thread} — clears when a teammate's reply lands on
E     this thread addressed to you; your own follow-ups do not clear it"
```

**Mechanism, and it is purely structural.** The committed proof's marker is
`"recipients must ack: lore_comms action=ack seqs=[41]"`. The NEW question-teach proof's **emit** leg
(`_render_send_03b(grade="directive", question=True, …)`) uses `_p03b_message(seq=41, …)` — so a
correct build necessarily emits *both* lines in that one render, and no exemption pair is declared in
`_MARKER_CO_EMISSION_EXEMPTIONS`. `TestMarkerCrossSatisfactionBound::test_KNOWN_BOUND_a_k_specific_prefix_weakening_is_not_caught`
falls with it (same violation list).

The `grade="directive"` choice on both legs is *correct* and load-bearing (it is what kills a
grade-gating build). **The seq is the fixable thing:** give `_render_send_03b`'s question-teach legs
a seq other than `41` (e.g. `42`) and both pins go green with every discrimination preserved. Or
declare the co-emission exemption with its reason.

---

### 3.B5 — BLOCKER: every served TEACHING claim is invertible; `_assert_ordered` does not do what its docstring says

`_assert_ordered` is a case-sensitive `str.find` sequence. Its docstring claims *"Ordering is the
cheapest non-invertible strengthening available to a prose pin."* **Measured: it is invertible.**
The chosen fragments (`"not"`, `"one"`, `"without"`, `"stamping"`, `"teammate"`, `"your own"`) all
occur inside innocuous words or inside sentences that assert the opposite.

**WB30 — two tool-schema descriptions inverted:**

```
set_status: "For 'send' ONLY: exactly 'input_required' — another way to SET your status row to
             input_required (it does exactly what heartbeat status=input_required does)."
peek:       "For 'drain' ONLY: a drain without peek=true is the one that reads without stamping;
             a peek DOES stamp, so peeked rows do not stay unread and are never served twice."

$ uv run pytest -q …::TestTheCommsToolSchemaTeachesTheNewParams   ->  11 passed
$ REFBUILD/wb.sh WB30_inverted_prose …                            ->  3 failed, 1170 passed, count: 0
```

The `set_status` line is served under a pin literally named
`test_the_set_status_description_REFUSES_the_status_write_its_name_implies`; the `peek` line is
served under a docstring that says *"`_assert_ordered` rather than loose substrings — 'a peek marks
them seen' contains every word the naive pin would look for."* **Both pins pass on the sentence they
name as the enemy.**

**WB31b — the entire instructions block inverted:**

```
"you never need to drain at your own turn boundaries — lore pushes messages to you. A directive
 needs no ack; the trailer is decorative. Bodies may be any length (the 2000 char figure is
 advisory) and refs are optional. One thread can carry anyone's questions at once — never bother
 to separate them onto q:<topic> threads, and never re-ask. A teammate's reply does not clear
 your question at all; your own self-note is what discharges it."

$ uv run pytest -q …::TestTheInstructionsBlockTeachesTheMessageSurface -> 9 passed
$ REFBUILD/wb.sh WB31b_inverted_instructions …                          -> 3 failed, 1170 passed, count: 0
```

All seven ruled B9 clauses taught backwards; **9/9 clause pins green; the whole contract green.**
Note clause 4 passes because `re.findall(r"(\d{3,6})[ -]?char")` finds `2000` in *"the 2000 char
figure is advisory"* — the AC-08 "extract the integer" strengthening survives a sentence that
**disclaims** the cap it extracts.

This is the packet's own trust doctrine on its own axis: the instructions block and the tool schema
are the **read-once teaching surface an LLM consumer learns the protocol from**, and the contract
pins their vocabulary, not their meaning.

---

### 3.B6 — BLOCKER: the ack render's outcome→line mapping is unpinned

```
$ REFBUILD/wb.sh WB33_ack_groups_swapped …
WB33: acked/already-acked groups SWAPPED
3 failed, 1170 passed, 14 skipped
--- count: 0
```

A build that lists every **newly acked** seq under `already acked: {seqs} — no new stamp` and every
**already-acked** seq under `acked {acked} of {requested}: {seqs}` passes the entire contract.
`test_every_requested_seq_is_accounted_for_in_ONE_mixed_render` only asserts `str(seq) in rendered`
— a bag of numbers, blind to which line each landed on. The duplicate pin (`[911, 912, 911]`) also
passes, because 911 legitimately occupies both groups either way.

**Positive control that my probe can see grouping errors:** the sibling permutation WB34
(`unknown_message ↔ not_addressed`) is **caught** (1 RED, the `unknown message seq(s)` proof) — so
the family fires; it is specifically the acked/already-acked pair that is undefended. That pair is
the one the consumer acts on.

---

### 3.C1 — CRITICAL: recipient resolution is not pinned session-scoped

Ruling **B2.3**: *"Each `to[]` name resolves via `AgentRegistry.get_agent(name, session=<the caller's
resolved session>)` — **session-scoped, always**… an unscoped resolution would make a cross-session
delivery reachable through name collision."*

```
$ REFBUILD/wb.sh WB8_recipient_unscoped …    ->  3 failed, 1170 passed, count: 0
```

**Positive control (`REFBUILD/probe_wb8.py`, two agents named `victim` in `wave7`/`wave8`, the
`wave7` one retired so the bare name resolves only to `wave8`):**

```
reference (session-scoped):  SEND REFUSED -> ValueError recipient 'victim' is retired (terminal) …
WB8      (unscoped):         SEND ACCEPTED -> sent #1 [signal] → victim
```

The wrong build **delivers a message into a different session** and reports success. The contract's
only two-session fixture is on the *broadcast* path.

---

## 4 — MISSING PINS (the tests that should exist + the defect each catches)

| # | sev | the test to write | the defect it catches |
|---|---|---|---|
| **P1** | BLOCKER | `test_a_drain_serves_the_SHARED_brief_skew_block` — through the real dispatcher, an agent behind head drains and the response contains the skew line; **plus** the ONE-IMPLEMENTATION mutation proof D5 demands (change the shared skew template → **both** the heartbeat pin and the drain pin go RED) | WB1 (FK-6 never wired; production's `"or drain"` teach is a lie) and WB18 (private clone — a green gate over a dead mechanism) |
| **P2** | BLOCKER | Fix `test_the_header_count_is_UNAFFECTED_by_a_hostile_body` to count rows in `outside` (as its own sibling already does) | the pin currently REWARDS the un-fenced build (MP-FK1a/b) and REDDENS the FK-1 build the operator ruled |
| **P3** | BLOCKER | Change the question-teach proof's fixture seq off `41` (or declare the exemption) | `test_no_marker_is_cross_satisfied` + the KNOWN-BOUND pin are RED on a correct build |
| **P4** | BLOCKER | `test_the_taught_semantics_are_NOT_INVERTIBLE` — for each of `set_status`/`peek`/`grade`/`to` and each B9 clause, assert on a **whole ruled sentence** (or a negated-form denylist: no `"peek DOES stamp"`, no `"never need to drain"`, no `"needs no ack"`, no `"advisory"` next to the cap, no `"does not clear"` adjacent to `"teammate"`) | WB30 + WB31b — every teaching claim invertible with 9/9 and 11/11 green |
| **P5** | BLOCKER | `test_each_requested_seq_lands_in_the_line_its_OWN_outcome_names` — one mixed render, four DISTINCT seqs, assert `_seqs_named_in(_line_containing(rendered, "<that group's literal>")) == [that seq]` **group-exact** for all four | WB33 (acked ↔ already_acked swapped) |
| **P6** | BLOCKER | `test_the_ack_receipt_counts_come_from_the_RESULT` — a fixture where `acked_count ≠ len(entries) ≠ already_acked_count`, all three pairwise distinct | WB32 is caught only incidentally, via a `"acked 2 of 3"` literal in the duplicate pin |
| **P7** | CRITICAL | `test_an_explicit_recipient_resolves_in_the_CALLERS_session_ONLY` — the same name registered in two sessions, `to=['victim']` from `wave7` must never reach `wave8`'s row; positive control that the `wave7` row IS reachable | WB8 — a real cross-session delivery (§3.C1) |
| **P8** | CRITICAL | `test_the_send_receipt_caps_at_the_SHARED_constant` — **N=7 recipients** (past `_COVERAGE_NAMES_CAP`), assert exactly `_COVERAGE_NAMES_CAP` names shown **and** `(+2 more)`; import the constant, never the literal 5 | WB25 (never caps → an unbounded name dump), WB26 (a private cap of 3 — copy #2 of one policy, #102), WB29 (the committed capped-recipient template is never emitted by any fixture) |
| **P9** | CRITICAL | `test_a_broadcast_receipt_counts_the_WHOLE_delivered_set` — N=7 broadcast, assert `"7 agents"` | WB27 (count derived from a display window — a served count that under-reports delivery) |
| **P10** | CRITICAL | `test_the_drain_refs_cell_is_capped_and_counted` — an entry with >`_COVERAGE_NAMES_CAP` refs | WB28 (refs uncapped → an unbounded dump in the highest-volume render) |
| **P11** | CRITICAL | A drain-serves-skew **store-failure** leg: brief ledger down ⇒ the drain fails loud (the B4.1 ruled posture), never silently serves messages-without-skew | the silent-degradation build B4.1 refuses; today nothing observes it |
| **P12** | MAJOR | Give the drain elision proof a **full-line, value-bearing** marker (it is `"more unread — re-run with limit="` — value-free, per B8.3's own rule) | mitigated today by the two arithmetic pins (WB3), so this is hardening, not a hole |
| **P13** | MAJOR | `test_a_rejected_recipient_charset_names_WHICH_recipient` for a *multi*-recipient `to=` list | the reject currently names the pattern; with 5 recipients a caller cannot tell which one was bad |
| **P14** | MAJOR | Pin `AppContext.comms`'s branch budget or extract the validation seam in the contract's own AST pins | the ruled validation order fails `ruff PLR0912` (§1.1) — the builder must invent a refactor the contract does not describe |
| **P15** | MAJOR | A `[fake]`-vs-`[real]` parity leg for `question` reaching the **render** through the dispatcher | §7: mutating the fake's `question` handling reddens only `test_message_ledger.py`; the surface contract never sees it |

---

## 5 — P7: RED honesty over the full 270

Reproduced exactly, in the repo and in scratch:

```
$ uv run pytest -n auto -q <the five graded files>
270 failed, 903 passed, 14 skipped in 25.35s
```

Every failure reason classified (`grep -oE "^E +(AttributeError|TypeError|…)"`, normalised):

| n | reason | verdict |
|---|---|---|
| 185 | `AttributeError: type object 'AppContext' has no attribute '_render_comms_send'/'_drain'/'_ack'` | RIGHT reason — the production symbol genuinely does not exist |
| 40 | `TypeError: AppContext.comms() got an unexpected keyword argument 'to'/'grade'/'peek'/'seqs'/…` | RIGHT reason |
| 10 | `KeyError: 'send'/'drain'/'ack'` (the action table) | RIGHT reason |
| 7 | `AssertionError: lore_comms does not expose '<param>' to an MCP client` | RIGHT reason |
| 5 | `AssertionError: missing (or out of order) fragment …` (instructions clauses) | RIGHT reason |
| 2 | `ValueError: unknown comms action 'ack'; valid actions are [six]` | RIGHT reason |
| 4 | `AttributeError: module 'loremaster.server'/'…config' has no attribute …` (`DEFAULT_COMMS_DRAIN_LIMIT`, `_MAX_DRAIN_LIMIT`, `CommsConfig.drain_limit`) | RIGHT reason |
| 3 | `AssertionError: the instructions never name action=send/drain/ack` | RIGHT reason |
| 1 | `AssertionError: build_app_context never constructs a MessageLedger` | RIGHT reason |
| 1 | `AssertionError: the promise scan observed NO render template literal from these 3b helpers` | RIGHT reason |
| 1 | `AssertionError: the instructions teach char cap(s) [] but the ledger enforces 2000` | RIGHT reason |
| 1 | `AssertionError: classified literal(s) no longer emitted …` | RIGHT reason (the 03b literals are registered before the renders exist) |
| 1 | `AssertionError: promise-free safe_str literal(s) no longer emitted …` | RIGHT reason |
| 1 | `AssertionError: the reject must NAME the retired recipient` | RIGHT reason |
| 1 | `AssertionError: the raise did not name the retired recipient — this pin must not pass on an unrelated error: TypeError(…)` | RIGHT reason, **and a well-built pin** — it refuses to pass on the wrong exception (the "rejected for a parse error" class, pre-closed by its author) |
| 1 | `AssertionError: Regex pattern did not match` | RIGHT reason |
| 6 | remaining assorted assertion messages, each naming an absent served claim | RIGHT reason |

**Zero** collection errors, **zero** import errors, **903 tests still ran**. The RED is honest.

**Mypy structural leg (re-derived — the brief's "~86+6" is 92):**

```
repo HEAD:  ./scripts/typecheck.sh -> Found 92 errors in 2 files (checked 149 source files); FAILED
reference:  ./scripts/typecheck.sh -> loremaster OK (149 source files); lorescribe OK; loresigil OK
```

---

## 6 — P4: the authors' claims, verified not relayed

### `REPORT-contract-surface-03b-r2.md` §6 — the nine MP obligations

| id | claim | my receipt | verdict |
|---|---|---|---|
| MP-FK1a | inline body ⇒ `test_no_dead_registry_entries` **and** `TestDrainBodiesAreFENCED` | 5 RED: both named, plus `test_every_comms_render_literal_is_classified` + 2 more fence legs | **CONFIRMED** (and it exposed §3.B3: the header-count leg went *green*) |
| MP-FK1b | `sanitise_line` the body ⇒ round-trip + fence-width | 4 RED, both named | **CONFIRMED** (same green flip) |
| MP-FK2 | fleet remainder → `total`, **or** `next_limit` → `shown+more` ⇒ the fleet elision proof | arm 1 (`more=total`): **6 RED** ✔ · arm 2 (`next_limit = shown+remainder`): **0 RED** | **arm 1 CONFIRMED; arm 2 is a VACUOUS mutation** — for fleet, `shown + more ≡ total` by construction, so the second arm cannot redden anything. A receipt taken on arm 2 alone would have been a false proof |
| MP-B12 ×3 | delete each render call ⇒ exactly that verb's pin **"and nothing else in the file"** | send → 2 RED (its verb pin + the classification pin, other file) · **drain → 7 RED, 6 of them in `test_comms_tool.py`** · ack → 3 RED (2 in-file) | **the mechanism CONFIRMED; the "nothing else in the file" clause is an OVER-CLAIM** for drain and ack |
| MP-B33 | question teach unconditional / grade-gated ⇒ its NO-EMIT leg | WB19 → exactly 1 RED, that proof | **CONFIRMED** |
| MP-B42 | re-serve marker keyed on `seen_at`/`stamped_seqs` ⇒ its NO-EMIT leg | WB20 → 5 RED incl. that proof | **CONFIRMED** |
| MP-B53 | drop `acked_count > 0` from `note recorded` ⇒ its NO-EMIT leg | WB17 → exactly 1 RED | **CONFIRMED** |
| MP-B14 | hardcode `"wave7"` ⇒ `test_the_comparand_is_the_ARGUMENT…` | WB4 → exactly 1 RED, that pin | **CONFIRMED** |
| MP-B15 | drain `next_limit → shown+more` ⇒ both arithmetic pins | WB3 → exactly 2 RED, both | **CONFIRMED** |

### `REPORT-wording-es5c-03b.md` §5 — the shared-constant mutation

Reproduced against pristine HEAD production in scratch, counted by Python set-difference:

```
baseline                : 270 failed, 903 passed, 14 skipped
_SKEW_SURFACING_TEACH   : "MUTANT surfaces at their next heartbeat or drain"
after                   : 293 failed, 880 passed, 14 skipped
NEW: 23   GONE: 0
  test_comms_promise_registry.py: 3
  test_comms_render_architecture.py: 3
  test_comms_tool.py: 16
  test_comms_wiring.py: 1
```

**EXACT match to the author's claim, module for module, including "0 stopped failing".** The DRY
sharing across the four modules is proven by mutation, not by inspection. ✔

---

## 7 — P5: can the doubles FAIL?

Two independent mutations of `_message_fakes.FakeMessageLedger`, restored byte-exact after each
(`md5 1ef5a020228979fb7d301411d217efed` == the repo's):

| mutation | result |
|---|---|
| ignore `peek` (always stamp) | RED — `test_message_ledger.py::TestAnAckedButUNDRAINEDMessageIsServedONCEMore::test_CONTROL_a_PEEK_does_not_consume_the_one_re_serve[fake]` |
| `total_pending = len(pending[:limit])` (window, not whole set) | RED — `test_message_ledger.py::TestDrainStampsExactlyWhatItServed::test_counts_are_computed_over_the_WHOLE_set_not_the_capped_window[fake]` |

**The fake is not decoration.** ⚠ **But both REDs land in `test_message_ledger.py`; ZERO in the
surface contract.** Every drain/ack pin in `test_comms_tool.py` rests on the fake's honesty and
re-checks none of it — see missing pin **P15**.

---

## 8 — Residuals, each with an individual verdict

1. **`_p03_entry` still defaults `acked_at: Any = None`** (`test_comms_promise_registry.py`). Packet-file
   amendment 8 (D5) called this default "the cause" of the R3 monoculture. That amendment is
   struck-session HISTORY, and the factory is committed/immutable — **VERDICT: acceptable, and the
   hazard is now closed by NEW pins** (WB5 → 2 RED). The fresh `_p03b_entry` correctly requires every
   branched-on field (AC-11 honoured). No action needed; recorded so nobody "fixes" it by weakening.
2. **The drain elision proof's marker is value-free** (`"more unread — re-run with limit="`),
   contradicting B8.3's full-line rule. **VERDICT: real but mitigated** — the arithmetic is pinned
   independently (WB3 → 2 RED). Hardening only → missing pin P12.
3. **`WB16` (ack render dedupes + re-sorts) survives.** B5.2 ruled request order; §A-GRAFT
   re-expressed R1 as MEMBERSHIP and retired the ordering clause. **VERDICT: RULING AMBIGUITY, not a
   contract defect.** Two readings that produce different code: (A) group membership only — what the
   contract implements; (B) every occurrence reported in request order — B5.2's letter. I would pick
   A. The ruling should say which, or a builder will guess.
4. **B3.2's send thread cell** — §3.A. Ruling ambiguity; I would pick "no thread cell". Escalated.
5. **`AppContext.comms` fails `ruff PLR0912` under the ruled validation order** (§1.1). **VERDICT:
   real builder cost, unanticipated.** → missing pin P14.
6. **Drain now reads the brief ledger** (B4.1), so drain fails when briefs fail. Ruled deliberately;
   **VERDICT: unpinned consequence** → missing pin P11.
7. **`MessageLedger` is not closed anywhere in the contract's `aclose` pins.** My reference added
   `await self.message_ledger.close()`; nothing reddens if a builder omits it. **VERDICT: minor
   resource-leak hole, unpinned.** (Not probed further — flagged.)
8. **`test_comms_wiring.py` imports `_SKEW_SURFACING_TEACH` from `test_comms_render_architecture`.**
   **VERDICT: correct and load-bearing** — it is what makes the M1 mutation reach four modules. Noted
   because a future reader may read the cross-test import as a smell; it is the DRY instrument.
9. **The struck adversary's escalation** (`test_surreal_harness.py` docstring-count RED at `45cc161`)
   — **VERDICT: not reproducible at HEAD `03b93d3` within my graded set**; I did not run that file
   (outside my brief's five). Flagged for the lead to confirm it was fixed rather than assumed.

---

## 9 — P6 corpse sweep (bare, anchor-free) + P6b

**Sweep:** `grep -rn "next heartbeat" --include=*.py --include=*.md .` minus `"next heartbeat or drain"`.
Every residual hit gets a verdict — no wholesale classification.

| site | verdict |
|---|---|
| `REPORT-contract-surface-03b-r2.md:203,207,457` | **not a corpse** — the author quoting the retired wording while describing the change |
| `REPORT-wording-es5c-03b.md:11,48,82,113,277,308` | **not a corpse** — same; 277 is the M3 independence-control output |
| `loremaster/tests/test_comms_render_architecture.py:498` | **NOT a corpse — line-WRAPPED.** The assertion message continues `"or drain, and the heartbeat did not deliver it (#103)"`. Exactly the wrap hazard the wording agent flagged; verified by reading the full expression |
| `docs/design/2026-07-12-pkt28-c1-semantics.md:24,905,925,928,931,934,961,963,1260` | **LIVE DOC CORPSE.** The PKT-28 C1 semantics doc still specifies §9.4's tail as `"; surfaces at their next heartbeat"` in 8 places (line 1260 is an END-TO-END sketch naming the *action*, which is fine). It is the doc a future reader consults for that wording, and it now contradicts production. **ESCALATE: one supersession line pointing at ruling E-S5(c). Non-blocking.** |
| `docs/plans/v2/02-comms-render-architecture.md:26` | **historical** — records #103's finding, does not prescribe wording. A pointer would be cheap. Flagged, not blocking |
| `docs/plans/v2/03b-design-rulings-r2.md:376,382,1262` | **correct as-is** — explicitly struck-through / marked SUPERSEDED in place |

**Retired row template** (`{sender}→you{context}: {body}`): `grep -rn` finds it in **4 docs only**
(`03b-comms-surface-design-rulings.md` — the banned struck doc; the archived
`2026-07-19-packet03/REPORT-contract-pkt03.md`; `03b-design-rulings-r2.md:240`, which marks it
superseded by FK-1; `DIFF-adjudication-03b.md:87`, describing the committed baseline). **Zero live
code or test hits — the FK-1 amendment is complete in the tree.** ✔

**P6b:** this wave **deletes no production code** — it is purely additive (three actions, three
renders, one extracted helper, one config field). The only *replacement* is the E-S5(c) wording
amendment, whose old-world behaviour is the pre-amendment literal; that is covered by the sweep
above and by M1's `GONE: 0`. **No removed-behaviour inventory is owed.**

---

## 10 — Blind-diff against the struck adversary report (read only AFTER my battery closed)

`docs/plans/v2/receipts/2026-07-24-packet03b/REPORT-adversary-surface-03b.md` graded an **earlier
corpus** at `45cc161`.

**What it probed that I did not (and their status in the CURRENT contract):**

| its finding | status now |
|---|---|
| The NO-OP fix for `send` and `ack` survived 1092/1092 (its headline blocker) | **CLOSED.** B12's `TestTheDispatcherActuallySERVESEachVerbsRender` catches all three verbs (WB2a/b/c). The single most valuable thing that wave produced was fixed |
| The ack render "behaviourally UNPINNED end to end" (W10–W15b) | **PARTLY CLOSED, PARTLY OPEN.** I re-ran its class: counts swapped → caught (WB32); unknown↔not_addressed swapped → caught (WB34); **acked↔already_acked swapped → STILL SURVIVES (WB33, §3.B6)** |
| The instructions block invertible (W16–W19) | **STILL OPEN, and now wearing seven new pins.** The clause pins were added; WB31b inverts all seven and passes 9/9 (§3.B5). **The fix addressed vocabulary, not meaning** |
| "39 invariants classified, 19 GUARDED" | my table: 41 classified, 15 GUARDED — the delta is real closure (B12, the trailer conjuncts, the elision arithmetic, `set_status`), not a scoping difference |
| Its escalation: repo RED at `45cc161` (`test_surreal_harness.py` docstring counts) | not in my graded set; **unverified at `03b93d3`** — §8.9 |

**What I probed that it did not** (its corpus predates the rulings that create these):
**FK-6 / drain-serves-skew (§3.B1)**, **D5 shared-helper mutation (§3.B2)**, the **unsatisfiable
fence pin (§3.B3)**, the **question-teach ↔ committed-marker collision (§3.B4)**, **session-scoped
recipient resolution (§3.C1)**, and the **send/broadcast/refs cap monocultures (§4 P8–P10)**.

---

## 11 — Reproduction

Everything is regenerable from this report. Scratch root: `/home/ejprice/scratch/adv-surface-03b-r2`
(**deliberately not cited as a durable address** — the recipe below is the durable artifact).

```
./scripts/scratch_copy.sh /home/ejprice/scratch/adv-surface-03b-r2   # provenance-asserted
python3 REFBUILD/apply_reference.py                                  # the reference, from the rulings
REFBUILD/wb.sh <NAME> REFBUILD/mut_<NAME>.py                         # restore -> mutate -> run -> diff
```

`wb.sh` restores the frozen reference **from content**, verifies `md5sum -c`, re-asserts
`loremaster.__file__` is inside scratch, runs the five graded files under `-n auto`, and prints
`comm -13 REF.failures <NAME>.failures`. An **empty** diff means the wrong build is invisible to the
contract.

**The 35 wrong builds, in one table** (`count` = new failures vs the correct reference):

| build | what it does | count | verdict |
|---|---|---|---|
| WB1 | drain never serves the skew block | **0** | **SURVIVED — BLOCKER** |
| WB2a/b/c | per-verb NO-OP: handler returns a constant | 2 / 7 / 3 | caught |
| WB3 | drain elision `next_limit = shown + more` | 2 | caught |
| WB4 | context cell keyed on the literal `"wave7"` | 1 | caught |
| WB5 | `ACK REQUIRED` keyed on grade alone | 2 | caught |
| WB6 | trailer gates on directives, lists everything | 2 | caught |
| WB7 | broadcast roster fleet-wide | 4 | caught |
| WB8 | recipient resolution unscoped | **0** | **SURVIVED — CRITICAL** |
| WB9 | retired recipients accepted | 2 | caught |
| WB10 | `set_status` accepts any value | 5 | caught |
| WB11 | `to[]` never charset-validated | 3 | caught |
| WB12 | drain limit hardcoded, config ignored | 2 | caught |
| WB13 | drain clamps at the FLEET cap | 1 | caught |
| WB14 | remainder from the window | 0 | **DISCARDED — non-mutation** (§1 P0-c) |
| WB15 | header total = window size | 4 | caught |
| WB16 | ack render dedupes + re-sorts | **0** | **SURVIVED — ruling ambiguity** (§8.3) |
| WB17 | `note recorded` unconditional | 1 | caught |
| WB18 | drain clones the skew assembly privately | **0** | **SURVIVED — BLOCKER** |
| WB19 | question teach gated on grade | 1 | caught |
| WB20 | re-serve line keyed on `stamped_seqs` | 5 | caught |
| WB21 | peek renders the trailer | 2 | caught |
| WB22 | `set_status` validated after the touch | 1 | caught |
| WB23 | send never teaches the ack duty | 2 | caught |
| WB24 | no drain row header at all | 10 | caught — **and it turns the fence pin GREEN** |
| WB25 | send never caps the recipient list | **0** | **SURVIVED — CRITICAL** |
| WB26 | send uses a private cap of 3 | **0** | **SURVIVED — CRITICAL (#102 door)** |
| WB27 | broadcast count from a capped window | **0** | **SURVIVED — CRITICAL** |
| WB28 | drain refs uncapped | **0** | **SURVIVED — CRITICAL** |
| WB29 | capped-recipient template unreachable | **0** | **SURVIVED — dead committed template** |
| WB30 | `set_status` + `peek` descriptions INVERTED | **0** | **SURVIVED — BLOCKER** |
| WB31b | instructions block fully INVERTED | **0** | **SURVIVED — BLOCKER** |
| WB32 | ack receipt counts swapped | 1 | caught (incidentally) |
| WB33 | acked ↔ already_acked groups swapped | **0** | **SURVIVED — BLOCKER** |
| WB34 | unknown ↔ not_addressed swapped | 1 | caught (**the control for WB33**) |
| WB35 | drain row header indented | 4 | caught — **and it turns the fence pin GREEN** |
| MP-FK1a | body inline + sanitised | 5 | caught — **fence pin flips GREEN** |
| MP-FK1b | body sanitised, not fenced | 4 | caught — **fence pin flips GREEN** |
| MP-FK2a | fleet `more = total` | 6 | caught |
| MP-FK2b | fleet `next_limit = shown+more` | **0** | **VACUOUS mutation** (§6) |

**Survivor count: 11 of 35 real mutations, 0 new failures each** (WB14 excluded as a non-mutation,
MP-FK2b excluded as vacuous).

---

## VERDICT

# CONTRACT INSUFFICIENT

The contract is **strong where it was told to look**: the per-verb no-op door (the previous wave's
headline blocker) is closed; the elision arithmetic, the trailer's two conjuncts in both gate and
list roles, the `acked_at` keying, the peek rule, the closed `set_status` vocabulary, the recipient
charset, the pre-touch reject ordering, the config-driven cap and the shared-constant DRY proof all
hold under direct attack. **Twenty-four wrong builds died on it.**

It is insufficient for six reasons, each with a surviving build or an unsatisfiable pin:

1. **FK-6 is pinned by nothing**, while production already teaches it (`91ea5be`). The trust
   doctrine's own axis, undefended.
2. **D5's shared-helper mutation proof — demanded by name in the rulings — does not exist.**
3. **The contract is UNSATISFIABLE.** Three pins are RED on a correct build; the fence pin is
   perfectly *inverted*, and I exhausted the escape space proving no build passes.
4. **Every served teaching claim is invertible**, in both the instructions block and the tool schema,
   under an instrument whose docstring claims the opposite.
5. **The ack outcome→line mapping is a bag of numbers** — the one permutation a consumer acts on is
   the one that survives.
6. **Four small-N monocultures** (recipient cap, broadcast count, refs cap, cross-session `to=`) wave
   through builds that dump unbounded lists, under-report delivery, or deliver into another session.

**Recommended route:** back to CONTRACT with missing pins **P1–P11** and the three RED-on-correct
fixes (**P2/P3** plus the §3.B3 one-line change). Items P1, P2, P3, P4, P5 are blockers; the rest are
cheap — each is one fixture-shaped function, expensive only to think of.

*Report written 2026-07-24 against HEAD `03b93d3`. Every claim above is dated to that commit; nothing
here should be read as current after the contract changes.*

---
---

# RE-GRADE (2026-07-24, second pass)

**Re-graded at:** repo `feat/surreal-unification` HEAD `7668a84` (`test(03b): surface fix wave —
unsatisfiability fixed both-directions, 15 missing pins closed`), after `f537051` (B3.2 ruled
Reading A) and `bb8d106` (this report committed).
**Delta graded:** `git diff 03b93d3..HEAD` over `test_comms_tool.py` (+889) and
`test_comms_promise_registry.py` (+144); the other three graded files are unchanged (md5-verified
against the repo).
**Same scratch root, same battery.** Provenance re-asserted on every run:
`loremaster.__file__ = /home/ejprice/scratch/adv-surface-03b-r2/loremaster/loremaster/__init__.py`.
Repo untouched except this report (`git status --short` → empty).

## RE-GRADE SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT — narrowly.** One CRITICAL missing pin with a proven
  perturbation pair, one MAJOR, one escalated ruling ambiguity. This is a different order of
  magnitude from the first pass: **6 blockers → 0**.
- **SATISFIABILITY: FIXED, and PROVEN on my reference — `1197 passed / 0 failed / 14 skipped`,
  ruff clean *after* the orphaned-variable cleanup the lint demanded, `./scripts/typecheck.sh`
  0 errors / 149 files.** All three RED-on-correct pin defects (§3.B3/§3.B4) are gone.
- **P1 RESULT: 10 of the 11 previous survivors now DIE to named pins** — each verified
  individually (§R2). The 11th (WB16) is the ruling ambiguity, not a defect.
- **2 NEW SURVIVORS, both found this pass:**
  - **WB39 (CRITICAL)** — the drain serves only the **'project'** half of the skew block; the
    **subscribed-NAME half (#103) is unpinned**. All four FK-6 pins key on the standing brief.
    `brief_publish`'s tail-3 literal — *"ackers see it at next heartbeat **or drain** — unbriefed
    agents only via brief_get name='{name}'"* — is about exactly the NON-standing case, so this
    is §3.B1's own defect, one brief-name over. P2 pair proven (§R5).
  - **WB40 (MAJOR)** — the verbatim-sentence pin is an **INCLUSION** check. Serving all seven
    ruled sentences AND appending a contradicting paragraph passes **1197/1197**.
- **ALL 24 previously-caught builds still caught**, most with *more* pins than before (§R4).
- **New MP obligations executed: 5 of 5 reproduce — but MP-D5's "and the identical-line pin"
  is an OVER-CLAIM** (only the structural one-emitting-function pin fires; an output-identical
  clone is invisible to the line comparison). §R6.
- **RED honesty: 290F / 907P reproduced exactly; ZERO collection/import errors**; all reasons
  classified to absent symbols/claims (§R7).
- **Author self-corrections (F.5/F.6) independently confirmed** — including that MP-FK2 arm 2
  was vacuous and MP-B12's exclusivity clause was an over-claim, both of which I had reported.

---

## R1 — Satisfiability, and how it was reached (the C-DEF leg)

The **frozen** contract-blind reference, run unchanged against the fixed contract, went
`11 failed / 1186 passed` — and **none of the 11 was one of the three pin defects.** All three
are fixed:

| pin defect (first pass) | status |
|---|---|
| `TestDrainBodiesAreFENCED::test_the_header_count_is_UNAFFECTED_by_a_hostile_body` | **FIXED** — and see the both-direction proof below |
| `TestNoMarkerIsCrossSatisfiedByAnotherProof::test_no_marker_is_cross_satisfied` | **FIXED** |
| `TestMarkerCrossSatisfactionBound::test_KNOWN_BOUND_a_k_specific_prefix_weakening_is_not_caught` | **FIXED** |

The 11 were the *new* teaching pins demanding the ruled sentences verbatim (my reference carried
my own wording) plus the new refs-remainder pin. Converging the reference onto the ruled wording
left **2**, both my own shape:

```
FAILED …TestEveryCommsSafeStrLiteralIsClassified::test_every_comms_safe_str_literal_is_classified
E   _render_comms_drain:5521: '{} +{} more'
FAILED …TestTheCanonicaliserDeniesByDefault::test_the_precise_argument_rule_has_ZERO_false_positives
```

**This is worth recording because it nearly became a fourth C-DEF.** The new refs pin demands
`f"+{over - _COVERAGE_NAMES_CAP} more"` in the render, and I enumerated the mechanisms:
`safe_str(f"… +{n} more")` → unclassified · `render_join` with a `"+{} more"` part → unclassified ·
a new `render_line("+{more} more refs")` → unclassified · a `" +"` separator → unclassified.
**Nothing in `_SAFE_STR_PROMISE_FREE` or `_PROMISE_FREE` names a refs remainder.** The contract is
satisfiable only via one pre-existing template — `"+{more} more beyond the display cap ({cap})"`
rendered as its own line. That works:

```
$ uv run pytest -n auto -q <the five graded files>
1197 passed, 14 skipped in 37.67s
$ uv run ruff check loremaster/loremaster/server.py loremaster/loremaster/config.py
All checks passed!
$ ./scripts/typecheck.sh
Success: no issues found in 149 source files ; typecheck: loremaster OK
```

**POST-LINT LEG, executed:** that shape left `refs_over` assigned-but-unused, and ruff
`F841` failed it. Deleting the orphan is the "still satisfiable AFTER the cleanups the lint
demands" leg — done, and the run above is post-cleanup.

**RESIDUAL (MAJOR, §R8.1):** the refs-remainder shape is *forced* and *undescribed*. A builder
who reaches for the obvious `safe_str(f"… +{n} more")` is reddened by an instrument that gives no
hint the answer is a display-cap template from another render family. Frozen reference:
`94af2bd44bd4a8fe296128fd97b2c934  server.py`.

**Both-direction proof of the §3.B3 fix, at MY reference (the author could only prove it at helper
level):** the pin now discriminates in the direction it always should have —

| build | `test_the_header_count_is_UNAFFECTED_by_a_hostile_body` |
|---|---|
| correct (fenced, committed row template) | **PASSES** (was RED) |
| **MP-FK1a** — body inline + `sanitise_line`d | **RED** (was GREEN) — inside a 6-RED set |
| **MP-FK1b** — body sanitised, not fenced | **RED** (was GREEN) — inside a 5-RED set |
| **WB24** — no row header at all | **RED**, inside a **12**-RED set (was 10) |
| **WB35** — row header indented | **RED**, inside a 5-RED set (was 4) |

The inversion is gone in both directions, on the four builds that measured it.

---

## R2 — The 11 previous survivors, verified one by one

| build | first pass | re-grade | the pin that now kills it |
|---|---|---|---|
| **WB1** — drain never serves the skew block | SURVIVED | **DIES, 3 RED** | `TestDrainServesTheSharedBriefSkewBlock::test_a_drain_serves_the_brief_skew_catch_up_line` · `…test_the_SAME_agent_gets_the_SAME_line_from_heartbeat` · `…test_a_drain_FAILS_LOUD_when_the_brief_ledger_is_down` |
| **WB18** — private skew clone (D5) | SURVIVED | **DIES, 1 RED** | `TestEveryPromiseLiteralHasExactlyONEEmittingFunction::test_no_promise_literal_is_emitted_from_two_functions` |
| **WB8** — recipient resolution unscoped | SURVIVED | **DIES, 1 RED** | `TestAnExplicitRecipientResolvesInTheCALLERSSessionOnly::test_a_send_never_crosses_into_another_sessions_row` |
| **WB25** — send never caps | SURVIVED | **DIES, 1 RED** | `TestTheSendReceiptCapsAndCountsHonestly::test_an_over_cap_recipient_list_shows_the_cap_and_counts_the_REMAINDER` |
| **WB26** — private cap of 3 (#102 door) | SURVIVED | **DIES, 1 RED** | same pin |
| **WB29** — capped-recipient template unreachable | SURVIVED | **DIES, 1 RED** | same pin |
| **WB27** — broadcast count from a window | SURVIVED | **DIES, 1 RED** | `…test_a_broadcast_receipt_counts_the_WHOLE_delivered_set` |
| **WB28** — refs uncapped | SURVIVED | **DIES, 1 RED** | `TestTheDrainRefsCellIsCappedAndCounted::test_an_over_cap_refs_list_is_capped_and_counted` |
| **WB30** — `set_status` + `peek` descriptions inverted | SURVIVED | **DIES, 2 RED** | `…test_set_status_teaches_that_it_does_NOT_write_the_status_row` · `…test_peek_teaches_the_RE_SERVE_consequence` |
| **WB31b** — instructions fully inverted | SURVIVED | **DIES, 8 RED** | 7× `test_every_ruled_clause_is_taught_VERBATIM` + `test_no_clause_is_served_in_its_INVERTED_form` |
| **WB33** — acked ↔ already_acked swapped | SURVIVED | **DIES, 3 RED** | `TestEachRequestedSeqLandsInTheLineItsOwnOutcomeNames` ×2 + `…test_the_receipt_COUNTS_come_from_the_RESULT_not_from_len_entries` |
| **WB16** — ack render dedupes + re-sorts | SURVIVED | **STILL SURVIVES (0 new)** | none — the escalated ruling ambiguity, §R8.3 |

**11 of 12 rows closed** (WB16 was never scored a defect). Every "DIES" above is a
`comm -13` against a **0-failure** reference baseline, so the counts are exact, not relative.

---

## R3 — The 2 NEW survivors

### R3.1 — WB39 (CRITICAL): the drain serves only HALF the skew block

```
$ REFBUILD/wb.sh WB39_skew_only_when_behind_project …
WB39: the shared skew block drops the subscribed-name half
1197 passed, 14 skipped in 16.34s
--- NEW failures caused by this mutation (EMPTY == the contract is BLIND):
--- count: 0
```

**Mechanism.** The skew block has three parts: (a) the `'project'` catch-up line, (b) up to
`_HEARTBEAT_SKEW_NAMES_CAP` subscribed-NAME lines (#103), (c) the collapsed
`behind on {k} more briefs` remainder. **All four `TestDrainServesTheSharedBriefSkewBlock` pins
assert on `"you have not acked brief 'project'"` only**, and
`test_the_SAME_agent_gets_the_SAME_line_from_heartbeat` compares exactly that ONE line via
`_line_containing`. Its fixture, `_fleet_with_a_published_brief()`, publishes only `'project'` —
no agent subscribes to a non-standing brief. So a drain that serves (a) and drops (b)+(c) passes.

**Why this is the same defect the wave was fixing, not a nicety.** `_render_comms_brief_publish`'s
tail-3 literal is *specifically* the non-standing case, and E-S5(c) put `"or drain"` in it:

> `"skew (session {session}): … ; ackers see it at next heartbeat or drain — unbriefed agents only via brief_get name='{name}'"`

Under WB39 that sentence is false for **every** non-`'project'` brief — a served teach naming a
verb that does not do the thing, which is verbatim §3.B1's charge. The wave closed the standing-brief
half and left the half its own amended literal is about.

**P2 pair (§R5) proves the pin is writable and discriminating.**

### R3.2 — WB40 (MAJOR): the sentence pin is an INCLUSION check

```
$ REFBUILD/wb.sh WB40_contradiction_appended …
WB40: ruled sentences kept, a contradicting paragraph appended
1197 passed, 14 skipped
--- count: 0
```

Served text (all seven ruled sentences present, verbatim, then):

> *"In practice these are guidelines rather than requirements: acking is optional, the body cap is
> not enforced, draining is unnecessary because the fleet notifies you, and posting a note to
> yourself on the thread is enough to close out a question."*

`_assert_teaches` checks presence; `_assert_never_claims` denylists the eleven phrases **I served
last pass**. Nothing pins that the comms paragraph contains *only* the ruled sentences.

**I want to be fair about the threat model** (repo law: a gate needs one). The primary attack —
*replacing* the teaching with its inverse — is now dead, and that was the measured one. This
residual is the honest-developer drift case: a packet-04 author "softening" a clause, or adding a
carve-out sentence. It is also the repo's own named losing shape: **the denylist enumerates the
FORBIDDEN.** The safe set here is small and enumerable — the ruled sentences themselves — so the
fix is an exact-block pin, not a longer denylist (§R6 missing pin RG2).

---

## R4 — Regression sweep: all 24 previously-caught builds

Counts are new-failures against the **0-failure** reference.

| build | first pass | re-grade | | build | first pass | re-grade |
|---|---|---|---|---|---|---|
| WB2a send no-op | 2 | **6** | | WB15 header total = window | 4 | **4** |
| WB2b drain no-op | 7 | **11** | | WB17 note unconditional | 1 | **1** |
| WB2c ack no-op | 3 | **3** | | WB19 question by grade | 1 | **2** |
| WB3 elision `shown+more` | 2 | **3** | | WB20 re-serve by `stamped_seqs` | 5 | **5** |
| WB4 hardcoded `"wave7"` | 1 | **1** | | WB21 peek renders trailer | 2 | **2** |
| WB5 trailer grade-only | 2 | **2** | | WB22 late `set_status` | 1 | **1** |
| WB6 trailer gate-vs-list | 2 | **2** | | WB23 no ack teach | 2 | **2** |
| WB7 broadcast crosses sessions | 4 | **4** | | WB24 no row header | 10 | **12** |
| WB9 retired accepted | 2 | **3** | | WB32 ack counts swapped | 1 | **3** |
| WB10 `set_status` open | 5 | **5** | | WB34 unknown↔not_addressed | 1 | **3** |
| WB11 no recipient charset | 3 | **4** | | WB35 indented row | 4 | **5** |
| WB12 hardcoded drain limit | 2 | **2** | | MP-FK1a inline body | 5 | **6** |
| WB13 fleet cap for drain | 1 | **1** | | MP-FK1b sanitised body | 4 | **5** |
| | | | | MP-FK2a fleet `more=total` | 6 | **6** |

**Zero regressions; 13 of 27 strengthened.** No previously-caught build slipped through.

**New builds invented this pass, all caught:**

| build | count | pin |
|---|---|---|
| **WB16b** — a duplicate seq reports only its FIRST fate (a real R1 violation; the CONTROL for WB16) | 1 | `test_a_NON_ADJACENT_duplicate_seq_reports_in_BOTH_groups` |
| **WB37** — refs use a PRIVATE cap of 3 | 1 | `TestTheDrainRefsCellIsCappedAndCounted` |
| **WB38** — the COSMETIC fix: a skew block rendered for a *bogus agent id* | 1 | `test_a_CURRENT_agent_gets_no_skew_block_from_drain` (the emit/no-emit control) |
| **MP-B5c** — the brief-ledger failure SWALLOWED, messages served without skew | 1 | `test_a_drain_FAILS_LOUD_when_the_brief_ledger_is_down` |

WB16b is the P0 control for WB16: it proves my ack-mutation family **can** fire, so WB16's survival
is a scope question, not a blind probe.

---

## R5 — P2 perturbation of the new load-bearing fixture, with its control

`_fleet_with_a_published_brief()` is the fix wave's new load-bearing fixture and it is a
**brief-name monoculture** (`'project'` only). The perturbation is the same family with a
NON-standing subscription (`fixer-b` acks `wave9` v1 by publishing it; `lead` bumps head to v2):

| leg | result |
|---|---|
| **A — CONTROL, correct reference** | **2 passed** (the drain leg AND the heartbeat control leg) |
| **B — WB39** (subscribed half dropped at drain) | **RED** on the drain leg; the heartbeat leg still passes — exactly the half-a-block signature |
| **C — WB1** (no skew at drain at all) | **RED** on the drain leg |

Both legs green on the correct build, red on both wrong builds, and the heartbeat control isolates
*which* half is missing. **The pin is writable today** — the fixture is ~10 lines on top of
`_03b_fleet()`.

---

## R6 — P4: the fix wave's own claims, verified

| claim | my measurement | verdict |
|---|---|---|
| **MP-FK6** — WB1 ⇒ `TestDrainServesTheSharedBriefSkewBlock` (≥3 legs) | 3 RED, exactly that class | **CONFIRMED** |
| **MP-D5** — WB18 ⇒ the ONE-emitting-function pin **"and the identical-line pin"** | **1 RED only — the structural pin.** `test_the_SAME_agent_gets_the_SAME_line_from_heartbeat` does NOT fire | **OVER-CLAIM.** My clone emits byte-identical text, so a line comparison cannot see it. The structural pin is the SOLE guard for D5 — worth knowing, because it is an AST pin over *which function* emits a literal, and it would not survive a refactor that keeps one emitting function but diverges the reads beneath it |
| **MP-B5c** — swallow the brief-ledger failure ⇒ the fail-loud pin | 1 RED, exactly that pin | **CONFIRMED** |
| **MP-B6c** — WB33 ⇒ the group-exact pins | 3 RED (2 group-exact + the counts pin) | **CONFIRMED** |
| **MP-B5d** — WB30/WB31b ⇒ sentence pins first, denylist second | WB30 → 2 RED (both sentence pins); WB31b → 8 RED (7 sentence + 1 denylist) | **CONFIRMED**, and the ordering claim is right: the sentence pins carry it, the denylist is genuinely secondary |
| **F.6** — MP-FK2 arm 2 was VACUOUS | independently measured the same last pass (0 RED) | **CONFIRMED** — the author's correction matches mine |
| **F.6** — MP-B12's "nothing else in the file" withdrawn | re-measured: send 6, drain 11, ack 3 | **CONFIRMED** as a withdrawal; the counts have grown, so the withdrawal was necessary |
| **F.5** — the author's self-caught emitter-claim defect (the four skew literals are emitted by `_render_comms_brief_publish`, not heartbeat) | verified in the tree: the four literals live in `_render_comms_brief_publish`; the amended descriptions now distinguish emitter from redeemer | **CONFIRMED, and it is a good catch** — it is also the reason WB39 matters: the tail-3 literal *promises* the non-standing catch-up at "heartbeat or drain", and only the standing half is pinned |

---

## R7 — P7: RED honesty on the new failure set

```
$ uv run pytest -n auto -q <the five graded files>     # pristine HEAD production
290 failed, 907 passed, 14 skipped in 16.74s
collection/import errors: 0
```

| n | reason | verdict |
|---|---|---|
| 191 | `AttributeError: type object 'AppContext' has no attribute '_render_comms_*'` | RIGHT reason |
| 52 | `TypeError: AppContext.comms() got an unexpected keyword argument …` | RIGHT reason |
| 11 | `AssertionError: lore_comms does not expose '<param>' to an MCP client` | RIGHT reason |
| 7 | `AssertionError: the served surface does not carry the RULED teaching sentence verbatim` | RIGHT reason — the NEW pins, red because the sentences are not served yet |
| 6 | `KeyError: 'send'/'drain'/'ack'` | RIGHT reason |
| 2 | `ValueError: unknown comms action …; valid actions are [six]` | RIGHT reason |
| 5 | `AttributeError: module … has no attribute` (`DEFAULT_COMMS_DRAIN_LIMIT`, `_MAX_DRAIN_LIMIT`, `CommsConfig.drain_limit`) | RIGHT reason |
| 3 | `AssertionError: the instructions never name action=send/drain/ack` | RIGHT reason |
| 3 | `AssertionError: the raise did not name the retired recipient / the recipient — this pin must not pass for an unrelated error` | RIGHT reason, **and a well-built pin** — it refuses to pass on the wrong exception type |
| 10 | assorted, each naming an absent served claim (`build_app_context never constructs a MessageLedger`, the promise-scan reach pin, the char-cap pin, …) | RIGHT reason |

**907 tests still ran; nothing silently skipped.** Out of my graded set and confirmed unchanged:
`test_comms_schema.py`'s 3 message-index REDs (telemetry wave, `bb64324`) — not counted above.

---

## R8 — Residuals, each with an individual verdict

1. **The refs-remainder shape is forced and undescribed (MAJOR).** §R1. The only classified route
   is `"+{more} more beyond the display cap ({cap})"` from the fleet render family, emitted as its
   own line. **VERDICT: satisfiable but under-specified** — the contract should either classify a
   refs-remainder label or say in the pin's docstring which template to reuse. → missing pin RG3.
2. **`test_the_SAME_agent_gets_the_SAME_line_from_heartbeat` cannot see an output-identical
   clone.** §R6/MP-D5. **VERDICT: real, and the structural pin covers it today.** Recorded so
   nobody deletes the structural pin believing the line pin duplicates it — it does not.
3. **WB16 / B5 within-group multiplicity — ESCALATED, still unruled.** B5.2's letter says every
   occurrence reports its own fate; §A-GRAFT re-expressed R1 as MEMBERSHIP. A render that shows
   `#911` once for a `[911, 911]` already-acked pair passes. **My control (WB16b) proves the
   across-group semantics ARE pinned**, so this is precisely and only the multiplicity question.
   Two readings that produce different code; **I would pick MEMBERSHIP** (the grafted reading — a
   repeated seq in one group tells the reader nothing new, and B5.2's own honesty analysis says
   "you listed it twice" and "acked earlier" need no different next action). B3.2 was ruled the
   same way; this one should get the same one-line treatment so no future builder is reddened for
   obeying the un-struck clause.
4. **`_p03_entry` still defaults `acked_at`** — **VERDICT unchanged: acceptable, mitigated** (WB5
   still dies, now 2 RED).
5. **The drain elision proof marker is still value-free** (`"more unread — re-run with limit="`) —
   **VERDICT unchanged: mitigated** by the arithmetic pins (WB3, now 3 RED). Hardening only.
6. **`MessageLedger` is never closed in any `aclose` pin** — **VERDICT: still unpinned.** Carried
   forward from §8.7; nothing in the fix wave addresses it.
7. **`docs/design/2026-07-12-pkt28-c1-semantics.md` doc corpse (8 hits)** — **VERDICT: still
   live.** Re-swept this pass; unchanged. One supersession line owed. Non-blocking.
8. **The struck adversary's `test_surreal_harness.py` escalation** — **VERDICT: still unverified**
   by me (outside the graded five). Carried forward.
9. **`AppContext.comms` and `ruff PLR0912`** — **VERDICT: still real.** My reference still needs
   the extracted `_validate_comms_identities`; nothing in the contract describes it. → missing
   pin P14 stands.

---

## R9 — MISSING PINS (re-grade)

| # | sev | the test to write | the defect it catches |
|---|---|---|---|
| **RG1** | CRITICAL | `test_a_drain_serves_the_SUBSCRIBED_NAME_half_of_the_skew_block` — fixture: `fixer-b` behind a NON-`'project'` brief (`wave9` v1 acked, head bumped to v2); assert the drain names `wave9`; **control leg**: the same agent's heartbeat names it too. (Ideally also the collapsed `behind on {k} more briefs` remainder past `_HEARTBEAT_SKEW_NAMES_CAP`.) | **WB39** — a drain serving only the standing-brief half, while `brief_publish`'s tail-3 literal promises the non-standing catch-up "at next heartbeat **or drain**". P2 pair proven §R5 |
| **RG2** | MAJOR | `test_the_comms_clause_block_is_EXACTLY_the_ruled_sentences` — pin the comms paragraph as the ruled sentences joined (or assert no sentence in that paragraph lies outside the ruled set). Allowlist the safe set; stop growing the denylist | **WB40** — every ruled sentence served verbatim AND a contradicting paragraph appended, 1197/1197 green |
| **RG3** | MAJOR | Either classify a refs-remainder label in `_SAFE_STR_PROMISE_FREE`, or name the reusable template in `TestTheDrainRefsCellIsCappedAndCounted`'s docstring | §R8.1 — the pin demands a counted remainder that has exactly one legal, non-obvious rendering; a builder taking the obvious route is reddened with no hint |
| **RG4** | MINOR | A `[fake]`/`[real]` parity leg for `question` reaching the render through the dispatcher | carried forward (first-pass P15); unaddressed |
| **RG5** | MINOR | `test_aclose_closes_the_message_ledger` | §R8.6 — a leaked SurrealDB connection per app context |

Plus the carried-forward **P13** (a multi-recipient charset reject should name *which* recipient)
and **P14** (the `PLR0912` seam).

---

## R10 — Updated P1b QUANTIFIER TABLE (deltas only)

Rows unchanged from §2 are omitted; every row below is a re-classification.

| # | invariant | was | now | receipt |
|---|---|---|---|---|
| 3 | explicit recipients resolve session-SCOPED | GUARDED | **∀** | WB8 → 1 RED (`TestAnExplicitRecipientResolvesInTheCALLERSSessionOnly`) |
| 9 | the send receipt caps at the SHARED constant | GUARDED (small-N) | **∀** | WB25/WB26/WB29 → 1 RED each (N=7 fixture) |
| 11 | broadcast renders a COUNT | GUARDED | **∀** | WB27 → 1 RED |
| 19 | bodies FENCED, verbatim, over-wide | ∀ *but self-contradictory* | **∀** | MP-FK1a/b, WB24, WB35 — all RED, pin no longer inverted |
| 28 | the refs cell is capped + counted | GUARDED | **∀** | WB28 → 1 RED; WB37 (private cap) → 1 RED |
| 29 | **drain serves the shared skew block** | GUARDED by nothing | **∀ for the `'project'` half; GUARDED for the subscribed-NAME half** | WB1 → 3 RED · WB38 (bogus agent) → 1 RED · MP-B5c (swallowed failure) → 1 RED · **WB39 (subscribed half dropped) → 0 RED, the surviving door (§R3.1)** |
| 30 | the skew block is ONE implementation | GUARDED by nothing | **∀** | WB18 → 1 RED (structural pin only — §R6) |
| 33 | each requested seq lands in its OWN group's line | GUARDED | **∀** | WB33 → 3 RED; control WB34 → 3 RED |
| 35 | the ack receipt's counts come from the RESULT | GUARDED | **∀** | WB32 → 3 RED incl. the dedicated counts pin |
| 37 | within-group order / duplicate MULTIPLICITY | GUARDED | **GUARDED — escalated, unruled** | WB16 → 0 RED; control WB16b (across-group collapse) → 1 RED, so the family fires (§R8.3) |
| 40 | the instructions teach the seven B9 clauses | GUARDED (invertible) | **∀ for replacement; GUARDED for ADDITION** | WB31b → 8 RED · **WB40 (contradiction appended) → 0 RED (§R3.2)** |
| 41 | the tool schema teaches the params honestly | GUARDED (invertible) | **∀ for replacement; GUARDED for ADDITION** | WB30 → 2 RED; the same inclusion-check bound as row 40 |
| **NEW 42** | a drain FAILS LOUD when the brief ledger is down | — | **∀** | MP-B5c → 1 RED; positive control pin present |
| **NEW 43** | the skew block is computed for the DRAINING agent | — | **∀** | WB38 → 1 RED (the emit/no-emit control pin) |

**Score: 43 invariants classified; 4 GUARDED (rows 29-partial, 37, 40-partial, 41-partial), every
one carrying a door-build receipt.** Down from 15 GUARDED.

---

## RE-GRADE VERDICT

# CONTRACT INSUFFICIENT — narrowly

The fix wave is **genuinely good work, and I want that on the record**: it closed all six blockers,
made the contract satisfiable (proven at my reference, post-lint, `1197 passed / 0 failed`), killed
10 of 11 survivors, strengthened 13 previously-caught builds, and self-caught a defect of its own
(F.5) that I had missed. Its two claim corrections (F.6) independently match my measurements.

It is INSUFFICIENT on two concrete, reproducible pins:

1. **RG1 (CRITICAL) — `WB39`.** The drain serves only the `'project'` half of the skew block. This
   is §3.B1's own defect one brief-name over, on the same trust-doctrine axis, and the literal that
   makes it a lie is `brief_publish`'s tail 3 — the very literal E-S5(c) amended. The P2 pair is
   proven: green on the correct build (with a heartbeat control leg), red on WB39 and WB1.
2. **RG2 (MAJOR) — `WB40`.** The teaching pin is an inclusion check; the contract can serve every
   ruled sentence and its contradiction at once. The primary attack is dead; this is the drift
   door, and the safe set is small and enumerable, so the fix is an exact-block pin rather than a
   longer denylist.

Plus **RG3** (the forced, undescribed refs shape) and one **escalation the lead should rule exactly
as B3.2 was ruled**: B5's within-group duplicate multiplicity (§R8.3) — my recommendation is
MEMBERSHIP, matching §A-GRAFT.

**Recommended route:** one narrow fix wave (RG1 + RG2 + RG3, ~three fixtures), plus the B5
multiplicity ruling. No blockers remain; nothing here needs a design re-open.

*Re-grade written 2026-07-24 against HEAD `7668a84`. Reference build
`94af2bd44bd4a8fe296128fd97b2c934 server.py` / `bdbda576ee327e3f0c547dccf2fcbd22 config.py`. Every
claim above is dated to that commit.*

---
---

# CLOSING RE-GRADE (2026-07-24, third pass)

**Re-graded at:** HEAD `d6fe51e` (`test(03b): surface fix wave 2 complete — RG1/RG2/RG3 + the three
B5 pins`), after `851fef3` (B5 multiplicity ruled MEMBERSHIP).
**Delta graded:** `git diff 7668a84..HEAD` over `test_comms_tool.py` (+296) and
`test_comms_promise_registry.py` (+15); the other three graded files unchanged (md5-verified).
Same scratch root, same battery, provenance re-asserted on every run. Repo untouched except this
report.

## CLOSING SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT — on ONE MAJOR pin, and the lead may reasonably rule it a
  KNOWN BOUND instead** (§C6). Zero blockers, zero criticals. RG1, RG2, RG3 and the B5 ruling all
  land and hold under attack.
- **SATISFIABILITY: `1206 passed / 0 failed / 14 skipped`**, ruff clean, `typecheck.sh` 0 errors /
  149 files. Frozen reference `9f09ab226c04ff27b1e97d5ff6dc2735 server.py`.
- **RG1 (WB39) DIES — 3 RED**, and **MP-RG1's asymmetry claim is CONFIRMED**: the drain legs redden
  while `test_CONTROL_the_heartbeat_names_it_too` stays green; WB1 (whole block) reddens **6**
  across both skew classes.
- **RG2 (WB40) DIES — 1 RED.** The second-paragraph escape (WB40b) also dies — 2 RED.
- **The B5 MEMBERSHIP ruling holds in all four directions:** WB16r (occurrences + request order +
  raw count) 4 RED · WB16s (unsorted) 1 · WB16t (raw count) 2 · WB16b (across-group collapse) 1.
- **Four residual conditional shapes around RG1, all CAUGHT:** below-cap-only (WB41) 1 · hardcoded
  brief name (WB42) 1 · head/acked swapped (WB43) 7 · ordered by name not magnitude (WB44) 2.
- **Full regression: 41 builds, ZERO regressions**; 5 strengthened (WB2b 11→14, WB18 1→4, WB33 3→8,
  WB38 1→4, WB31b 8→9).
- **ONE NEW SURVIVOR — WB45 (MAJOR):** RG2's equality pin is scoped by a paragraph SELECTOR keyed on
  `action=send|drain|ack`. A contradicting paragraph that names no verb, in wording off the
  denylist, passes **1206/1206**. WB40 relocated by two newlines.
- **RED honesty: 298F / 908P reproduced exactly, ZERO collection/import errors.**
- **Final quantifier table: §C7 — 47 invariants, 1 GUARDED (WB45's), carrying its receipt.**

---

## C1 — Satisfiability, and the four-way adjudication of the 5 rows

The frozen reference (unchanged from the second pass) went `5 failed / 1201 passed` against the
new contract. All five adjudicate the same way:

| pin | verdict |
|---|---|
| `test_a_seq_repeated_WITHIN_one_group_is_listed_ONCE` | **reference defect by RULING CHANGE.** My reference listed every occurrence — the pre-ruling shape. `851fef3` ruled MEMBERSHIP (my own recommendation), so the correct build now dedupes. |
| `test_each_group_lists_its_seqs_ASCENDING` | same |
| `test_the_header_count_derives_from_DISPLAYED_membership_not_raw_entries` | same |
| `test_a_NON_ADJACENT_duplicate_seq_reports_in_BOTH_groups` | same (its anchor moved `"acked 2 of 3"` → `"acked 2 of 2"` — see below) |
| `test_the_comms_block_is_EXACTLY_the_ruled_sentences` | **reference defect.** My comms teaching shared a paragraph with the pre-existing register/heartbeat sentence; RG2 requires ONE block equal to the ruled sentences. |

**No pin defects.** Converging the reference (membership grouping + a split comms paragraph):

```
$ uv run ruff check loremaster/loremaster/server.py loremaster/loremaster/config.py
All checks passed!
$ uv run pytest -n auto -q <the five graded files>
1206 passed, 14 skipped in 18.24s
$ ./scripts/typecheck.sh
Success: no issues found in 149 source files ; typecheck: loremaster OK
```

**Post-lint leg executed again:** the membership rewrite tripped `PLC0206` (dict iteration without
`.items()`); the run above is post-fix.

**Credit where it is due — the author caught a C-DEF I would have reported.** The duplicate pin's
old anchor `"acked 2 of 3"` counted RAW ENTRIES; under the ruling the correct build renders
`"acked 2 of 2"`. Left alone it would have reddened the ruled build — a fourth C-DEF *created by a
ruling that landed after the pin*. Their docstring states the lesson exactly: *"A ruling is not
only new pins; it is a re-read of every pin already written."* I verified it in the tree.

**One residual the convergence exposed (§C5.1):** the equality pin builds its expected string as
`" ".join((*_RULED_INSTRUCTION_CLAUSES, _RULED_BODY_CAP_SENTENCE))`, which fixes the body-cap
sentence **last**. B9 numbers that clause **4**. A builder placing it in its ruled numeric position
is reddened by an ordering nothing states. Self-teaching (the failure message prints the required
string in full) but undocumented.

---

## C2 — RG1 / RG2 / B5: the named targets

| target | build | result |
|---|---|---|
| **RG1** | **WB39** — subscribed-name half dropped at the drain | **DIES, 3 RED**: `TestDrainServesTheSUBSCRIBEDNAMEHalfOfTheSkewBlock::test_a_drain_names_the_subscribed_brief_the_agent_is_behind_on` · `…test_the_collapsed_remainder_renders_PAST_the_skew_names_cap` · `…test_the_two_verbs_serve_the_IDENTICAL_subscribed_line` |
| **MP-RG1 leg 1** | WB39, asymmetry claim | **CONFIRMED** — `test_CONTROL_the_heartbeat_names_it_too` stays **GREEN** while the drain legs redden. The half-a-block signature is diagnostic, exactly as claimed |
| **MP-RG1 leg 2** | **WB1** — whole block dropped | **6 RED** across BOTH classes (3 standing-brief + 3 subscribed-name) — both legs red, as claimed |
| **RG2 / MP-RG2** | **WB40** — ruled sentences + a contradicting sentence | **DIES, 1 RED** (`test_the_comms_block_is_EXACTLY_the_ruled_sentences`) |
| **RG2, my escape probe** | **WB40b** — the contradiction in a SECOND verb-naming paragraph | **DIES, 2 RED** — the one-paragraph clause does its job |
| **B5 ruling** | **WB16r** — every occurrence, request order, raw count | **4 RED** (all three new pins + the duplicate pin) |
| **B5 ruling** | **WB16s** — deduped but unsorted | **1 RED** (`test_each_group_lists_its_seqs_ASCENDING`) |
| **B5 ruling** | **WB16t** — membership groups, raw entry count in the header | **2 RED** |
| **B5 ruling, control** | **WB16b** — across-group collapse (the real R1 violation) | **1 RED** — the family still fires in the direction it always did |

The B5 door is now closed in **all four** directions I could construct. §R8.3's escalation is
discharged, and it was ruled the way I recommended.

---

## C3 — Residual conditional shapes around RG1 (the lead's probe list)

| build | shape | result |
|---|---|---|
| **WB41** | serve the subscribed half only BELOW the cap (drop the collapsed `behind on {k} more briefs` remainder) | **1 RED** — `test_the_collapsed_remainder_renders_PAST_the_skew_names_cap` |
| **WB42** | serve the subscribed half only for a HARDCODED brief name (`"wave9"`, the fixture's) | **1 RED** — the past-the-cap fixture uses several names, so it doubles as the name-monoculture discriminator |
| **WB43** | the COSMETIC fix: right line shape, `head`/`acked` swapped | **7 RED** (2 architecture + 3 drain-subscribed + the drain leg's control + a registry proof) |
| **WB44** | subscribed lines ordered by NAME, not skew magnitude descending | **2 RED** (`test_over_cap_subscribed_skews_collapse_ordered_by_magnitude` + the collapsed-remainder proof) |

**All four conditional doors are shut.** The RG1 pins are not a single-fixture pass: the cap fixture
is past-the-cap and multi-name, so it discriminates count, name and ordering at once.

---

## C4 — Full regression sweep (41 builds, zero regressions)

Counts are new failures against a **0-failure** reference.

| build | 2nd | 3rd | | build | 2nd | 3rd |
|---|---|---|---|---|---|---|
| WB1 skew no-op | 3 | **6** | | WB25 send never caps | 1 | **1** |
| WB2a send no-op | 6 | **6** | | WB26 private cap | 1 | **1** |
| WB2b drain no-op | 11 | **14** | | WB27 broadcast window count | 1 | **1** |
| WB2c ack no-op | 3 | **3** | | WB28 refs uncapped | 1 | **1** |
| WB3 elision `shown+more` | 3 | **3** | | WB29 capped variant dead | 1 | **1** |
| WB4 hardcoded `"wave7"` | 1 | **1** | | WB30 inverted schema prose | 2 | **2** |
| WB5 trailer grade-only | 2 | **2** | | WB31b inverted instructions | 8 | **9** |
| WB6 trailer gate-vs-list | 2 | **2** | | WB32 ack counts swapped | 3 | **3** |
| WB7 broadcast cross-session | 4 | **4** | | WB33 ack groups swapped | 3 | **8** |
| WB8 recipient unscoped | 1 | **1** | | WB34 unknown↔not_addressed | 3 | **3** |
| WB9 retired accepted | 3 | **3** | | WB35 indented row | 5 | **5** |
| WB10 `set_status` open | 5 | **5** | | WB37 refs private cap | 1 | **1** |
| WB11 no recipient charset | 4 | **4** | | WB38 skew for a bogus agent | 1 | **4** |
| WB12 hardcoded drain limit | 2 | **2** | | MP-B5c swallowed failure | 1 | **1** |
| WB13 fleet cap for drain | 1 | **1** | | MP-FK1a inline body | 6 | **6** |
| WB15 header total = window | 4 | **4** | | MP-FK1b sanitised body | 5 | **5** |
| WB17 note unconditional | 1 | **1** | | MP-FK2a fleet `more=total` | 6 | **6** |
| WB18 private skew clone | 1 | **4** | | WB16b across-group collapse | 1 | **1** |
| WB19 question by grade | 2 | **2** | | WB21 peek trailer | 2 | **2** |
| WB20 re-serve by `stamped_seqs` | 5 | **5** | | WB22 late `set_status` | 1 | **1** |
| WB23 no ack teach | 2 | **2** | | WB24 no row header | 12 | **12** |

**Zero regressions. Five strengthened** — notably **WB18 (the D5 private clone) 1 → 4**: the new
identical-subscribed-line pin now catches it too, so MP-D5 no longer rests on the structural pin
alone. §R8.2's residual is thereby **closed**, and the author's withdrawn over-claim has become true
for a reason that did not exist when it was withdrawn.

---

## C5 — The one new survivor

### C5.1 — WB45 (MAJOR): the equality pin is scoped by a verb-name SELECTOR

```
$ REFBUILD/wb.sh WB45_contradiction_outside_the_block …
WB45: a contradicting paragraph that names no action verb
1206 passed, 14 skipped in 15.47s
--- NEW failures caused by this mutation (EMPTY == the contract is BLIND):
--- count: 0
```

Served, as a new `_INSTRUCTIONS` paragraph between the comms block and TOOL LOADING:

> *"FLEET ETIQUETTE: inbox reads are best-effort and the seq lists in a response are advisory
> rather than binding; teammates are expected to follow up out of band, so treat the caps and
> duties above as defaults you may relax."*

**Mechanism.** `_comms_paragraphs()` selects paragraphs *"that make a claim about the three new
verbs — identified by naming one of them"*. This paragraph names none, so the equality pin never
sees it; and its wording is deliberately off `_DEMONSTRATED_INVERSIONS`, so the denylist does not
either. **It is WB40 relocated by two newlines.**

**Why it still matters, stated fairly.** The paragraph boundary is a test-side construct. An LLM
consumer reads `_INSTRUCTIONS` as ONE document; a sentence saying the duties above are "defaults
you may relax" defeats the ruled teaching just as completely from the next paragraph as from
inside it. And the shape is an honest-developer one: packet 04 (`_comms_footer`) and packet 05
(await/story) both add to this block, and a general "fleet etiquette" paragraph is exactly what a
later author writes.

**Why I am not calling it a blocker.** The measured attack classes — replacement (WB31b) and
addition-inside-the-block (WB40, WB40b) — are closed. What remains is a bound one level *outside*
this packet's own surface, and closing it fully means deciding who owns `_INSTRUCTIONS` across
packets. That is a scope call, not mine.

**Two ways to close it, both cheap:**
- **CL1 (the pin I would write):** invert the selector — assert that the comms block is the ONLY
  paragraph of `_INSTRUCTIONS` mentioning the comms surface's duty vocabulary (`inbox`, `ack`,
  `drain`, `seq`, `thread`, the cap). Allowlist-shaped: the safe set is one paragraph, the
  forbidden set is unbounded — which is the repo's own instrument lesson, applied one level up
  from where RG2 already applied it.
- **CL2 (the ruling):** declare it a **KNOWN BOUND** under the repo's *"WHEN YOU CANNOT CLOSE A
  HOLE, PIN IT"* law — a pin asserting the hole exists, carrying the named re-open trigger *"any
  packet that adds a paragraph to `_INSTRUCTIONS` naming comms duties"* (packet 04 pulls it).

---

## C6 — Residuals, each with an individual verdict

1. **The exact-block pin fixes an UNRULED sentence order** (body-cap last; B9 numbers it 4). §C1.
   **VERDICT: minor, self-teaching, undocumented.** One docstring line, or reorder the tuple to
   match B9's numbering.
2. **RG3's refs-remainder shape is still forced and undescribed** — the only classified route is
   `"+{more} more beyond the display cap ({cap})"` from the fleet family. §R8.1.
   **VERDICT: unchanged, satisfiable, under-specified.** The fix wave added the fixture; it did not
   name the template.
3. **MP-D5's structural-pin-alone residual (§R8.2): CLOSED** — WB18 now reddens 4, including the
   identical-subscribed-line pin.
4. **`MessageLedger` is never closed in any `aclose` pin.** **VERDICT: still unpinned** (RG5).
5. **`_p03_entry` still defaults `acked_at`** — **VERDICT: acceptable, mitigated** (WB5 → 2 RED).
6. **The drain elision proof marker is still value-free** — **VERDICT: mitigated** (WB3 → 3 RED).
7. **`ruff PLR0912` on `AppContext.comms`** — **VERDICT: still real**; my reference still needs the
   extracted `_validate_comms_identities`, and now also a dict-comprehension for `PLC0206`. Two
   post-lint refactors a builder must invent (P14).
8. **`docs/design/2026-07-12-pkt28-c1-semantics.md` doc corpse (8 hits)** — **VERDICT: still live**;
   re-swept, unchanged. One supersession line owed.
9. **`test_surreal_harness.py` (struck adversary's escalation)** — **VERDICT: still unverified by
   me**, outside the graded five. Carried forward for the lead.
10. **Surface-contract pins still rest on the message fake's honesty** (RG4) — **VERDICT: unchanged**;
    the fake CAN fail (§7) but only `test_message_ledger.py` re-checks it.

---

## C7 — FINAL P1b QUANTIFIER TABLE

47 invariants classified across the three verbs, the dispatcher, the skew block and the teaching
surface. Rows 1–43 as in §2/§R10 with the re-classifications below; **every ∀ row's receipt is a
wrong build that DIES, every GUARDED row carries a surviving-door receipt.**

| # | invariant | class | receipt |
|---|---|---|---|
| 29 | drain serves the shared skew block — **both halves** | **∀** | WB1 → 6 · WB39 → 3 · WB41 → 1 · WB42 → 1 · WB43 → 7 · WB44 → 2 · WB38 → 4 · MP-B5c → 1 |
| 30 | the skew block is ONE implementation | **∀** | WB18 → 4 (structural pin + the identical-line pins) |
| 33 | each seq lands in its OWN group's line | **∀** | WB33 → 8 · WB34 → 3 |
| 35 | the receipt's counts come from the RESULT | **∀** | WB32 → 3 |
| 37 | within-group duplicate MULTIPLICITY (ruled MEMBERSHIP) | **∀** | WB16r → 4 · WB16s → 1 · WB16t → 2 · WB16b → 1 |
| 40 | the instructions teach the seven ruled clauses | **∀ for replacement AND for addition INSIDE the comms block; GUARDED for addition OUTSIDE it** | WB31b → 9 · WB40 → 1 · WB40b → 2 · **WB45 → 0 (the surviving door, §C5.1)** |
| 41 | the tool schema teaches the params honestly | **∀** | WB30 → 2 |
| 42 | a drain FAILS LOUD when the brief ledger is down | **∀** | MP-B5c → 1 |
| 43 | the skew block is computed for the DRAINING agent | **∀** | WB38 → 4 |
| **44** | the subscribed-name skew survives PAST the names cap | **∀** | WB41 → 1 |
| **45** | the subscribed skew is name-agnostic | **∀** | WB42 → 1 |
| **46** | the subscribed line's head/acked versions are not re-derived | **∀** | WB43 → 7 |
| **47** | the subscribed lines order by skew magnitude | **∀** | WB44 → 2 |

**Score: 47 classified · 46 ∀ · 1 GUARDED (row 40's outside-the-block half), with its door-build
receipt.** From 15 GUARDED at the first pass, to 4, to 1.

---

## CLOSING VERDICT

# CONTRACT INSUFFICIENT — on one MAJOR pin, and the lead may rule it a KNOWN BOUND instead

**What I could not break, having tried hard:** every one of the 41 previously-graded wrong builds
dies; all three fix-wave-2 targets (RG1, RG2, the B5 ruling) die; all four conditional shapes I
invented around RG1 die; the contract is satisfiable at `1206 passed / 0 failed` with ruff and
mypy clean, post-lint, on a reference built from the rulings; the RED is honest at 298F/908P with
zero collection errors; and the fix wave closed a residual of its own (MP-D5) that I had recorded
as open. **This is a strong contract, and the arc from six blockers to one bounded door is real.**

**The one thing I did break:** `WB45` — the RG2 equality pin is scoped by a paragraph selector
keyed on the verb names, so a contradiction placed in a paragraph that names no verb, in wording
off the denylist, passes 1206/1206. That is WB40 relocated by two newlines, on the trust doctrine's
own teaching axis.

**The fork, which is the lead's to settle — not mine:**

- **CL1 — write the pin** (§C5.1): assert the comms block is the ONLY `_INSTRUCTIONS` paragraph
  mentioning the comms duty vocabulary. One test, allowlist-shaped, kills WB45. Then the surface
  is SUFFICIENT with no residual door.
- **CL2 — rule it a KNOWN BOUND**: pin the hole with the named re-open trigger *"any packet adding
  an `_INSTRUCTIONS` paragraph that names comms duties"* (packet 04 pulls it). Then the surface is
  SUFFICIENT with a deliberately-met bound, and nobody rediscovers it from a consumer-eval failure.

**Either closes the certification.** I record INSUFFICIENT rather than waive it because I have a
reproducible surviving build and my role forbids me deciding it is out of scope — but I want the
proportion on the record: this is one pin or one ruling, not a wave.

*Closing re-grade written 2026-07-24 against HEAD `d6fe51e`. Reference build
`9f09ab226c04ff27b1e97d5ff6dc2735 server.py` / `bdbda576ee327e3f0c547dccf2fcbd22 config.py`. Every
claim above is dated to that commit.*

---
---

# FINAL VERDICT PASS (2026-07-24, fourth pass)

**Graded at:** HEAD `f6d88b3` (`test(03b): surface closing wave — the WB45 allowlist pin +
RG3/C6.1/RG5`). Delta: `test_comms_tool.py` (+169), `test_comms_promise_registry.py` (+16),
`test_comms_wiring.py` (+23). Same scratch root, same battery, provenance re-asserted per run.
Repo untouched except this report.

## FINAL SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT — one door, and I name the ONE pin that terminates it**
  (§D5). Zero blockers, zero criticals. Everything else is certified.
- **SATISFIABILITY: `1209 passed / 0 failed / 14 skipped`**, ruff clean, `typecheck.sh` 0 errors /
  149 files. Frozen reference `36a6ca0d7ee04844809cae54f0436c82 server.py`.
- **RG5 passes on my reference unchanged** — I have closed `message_ledger` in `aclose` since the
  first reference build, so the new pin found it already true. Not a reference gap.
- **WB45 DIES — 1 RED** (`test_the_comms_block_is_the_ONLY_paragraph_claiming_a_comms_DUTY`),
  against its exact surviving text. **WB40 → 2 RED · WB40b → 3 RED.**
- **THE DOOR THAT REMAINS — one finding, three keys, all measured:** the CL1 detector is a
  **7-word deny list wearing an allowlist label**. Ordinary paraphrase walks through it:
  **WB46** (a contradiction using no vocabulary word) · **WB47** (inflection — `acking`,
  `threads`, `inboxes`, `seqs` all evade `(?<!\w)word(?!\w)`) · **WB48** (the same sentence folded
  into an existing paragraph). Each passes **1209/1209**.
- **Full regression: 52 builds, ZERO regressions**; 3 strengthened (WB24 12→13, WB28 1→2,
  WB31b 9→10).
- **RED honesty: 299F / 910P reproduced exactly, ZERO collection/import errors.**
- **Final quantifier table: §D6 — 47 invariants, 46 ∀, 1 GUARDED, receipt attached.**
- **I will not ask for a bigger word list.** §D5 gives the terminating pin and the ruling
  alternative, and states in advance which verdict each earns.

---

## D1 — Satisfiability + the four-way adjudication

The frozen reference went `3 failed / 1206 passed`. All three adjudicate as **reference gaps**,
two of them created by rulings that landed after my reference:

| pin | verdict |
|---|---|
| `test_the_comms_block_is_EXACTLY_the_ruled_sentences` | **reference gap by C6.1.** The residual I raised (the body-cap sentence forced last by tuple-assembly order) was **settled the way I recommended** — the ruled string now carries it at clause **4**, matching B9's numbering. My reference still had it last. |
| `test_the_comms_block_is_the_ONLY_paragraph_claiming_a_comms_DUTY` | **cascade of the above** — the CL1 pin skips the paragraph EQUAL to `ruled`; a block that fails equality is then flagged as an outsider. Correct behaviour, not a second defect. |
| `test_no_dead_safe_str_free_entries` | **reference gap by C6.2 / RG3.** The wave gave the refs remainder its OWN classified label `"+{} more"`; my reference still used the fleet family's display-cap line — the shape I had reached only because no classification existed. My workaround left the new entry dead. |

**No pin defects.** Converging (cap sentence to clause 4; the refs remainder as a `safe_str` label
inside the row cell):

```
$ uv run ruff check loremaster/loremaster/server.py loremaster/loremaster/config.py
All checks passed!
$ uv run pytest -n auto -q <the five graded files>
1209 passed, 14 skipped in 16.22s
$ ./scripts/typecheck.sh
Success: no issues found in 149 source files ; typecheck: loremaster OK
```

**Both residuals I raised are properly closed, and the RG3 fix is better than my workaround** — a
classified label in the drain row's own vocabulary rather than a neighbour's leftover forced onto
its own line. The author's correction note is right that pointing a builder at the fleet template
was documentation standing in for a missing classification.

**RG5:** `test_comms_wiring.py`'s new `aclose` pin passes on my reference untouched — I added
`await self.message_ledger.close()` in the original build. §R8.4/§C6.4 is **closed**.

---

## D2 — WB45 and its relocations

| build | result |
|---|---|
| **WB45** — the exact text that survived the closing pass, re-served | **DIES, 1 RED** — `test_the_comms_block_is_the_ONLY_paragraph_claiming_a_comms_DUTY` |
| **WB40** — a contradicting sentence appended INSIDE the ruled block | **DIES, 2 RED** |
| **WB40b** — the contradiction in a SECOND verb-naming paragraph | **DIES, 3 RED** (equality + CL1 + the denylist) |

CL1 does exactly what it was written for. The measured attack is dead.

---

## D3 — THE DOOR THAT REMAINS: one finding, three keys

The CL1 pin's docstring says **"ALLOWLIST THE SAFE, one level up from where RG2 applied it"**. RG2
genuinely is an allowlist — the ruled block is pinned by EQUALITY, and nothing can be added to,
removed from, or reworded inside it. **CL1 is not.** Its mechanism is
`_COMMS_DUTY_VOCABULARY` — seven words — matched whole-word, case-insensitively, over every other
paragraph. That is an enumeration of the FORBIDDEN, which the repo's own six-defeats lesson names
as the instrument shape that loses. Three keys, each passing **1209/1209** with **0** new failures:

**WB46 — vocabulary-free.** No word from the list, nothing from the inversion denylist:

> *"FLEET ETIQUETTE: the caps and duties described above are defaults you may relax when a task is
> going well; teammates follow up out of band, so treat them as suggestions rather than
> obligations."*

**WB47 — inflection.** `(?<!\w)ack(?!\w)` does not match `acking`; nor `thread` → `threads`,
`inbox` → `inboxes`, `seq` → `seqs`, `directive` → `directives`. And
`_DEMONSTRATED_INVERSIONS`'s `"trailer is decorative"` is not a substring of `"trailers are
decorative"`:

> *"FLEET ETIQUETTE: inboxes are best-effort; acking is optional and the trailers are decorative;
> threads may carry several questions at once, and the seqs a response lists are advisory rather
> than binding."*

**This one needs no adversary at all — it is ordinary English.** An author writing *"acking is
optional"* rather than *"no ack"* evades by accident, which is precisely the honest-developer
model the pin declares.

**WB48 — no new paragraph.** The same claim folded into the existing `lore_comms` paragraph, which
this packet already edits:

> *"…fleet to see who else is active. The obligations below are defaults you may relax; teammates
> follow up out of band."*

WB48 also disposes of the cross-packet-coupling objection to the closure below: the contradiction
does not need a new paragraph, or another packet's paragraph, to land.

**P0 control:** all three are green on the correct build (1209/1209) and change the served text
demonstrably; each was diffed against the reference's own 0-failure baseline, so "0 new failures"
is absolute, not relative.

---

## D4 — Full regression sweep (52 builds, zero regressions)

Every previously-graded build re-run against the final reference. Counts are new failures against
a **0-failure** baseline.

WB1 **6** · WB2a **6** · WB2b **14** · WB2c **3** · WB3 **3** · WB4 **1** · WB5 **2** · WB6 **2** ·
WB7 **4** · WB8 **1** · WB9 **3** · WB10 **5** · WB11 **4** · WB12 **2** · WB13 **1** · WB15 **4** ·
WB16b **1** · WB16r **4** · WB16s **1** · WB16t **2** · WB17 **1** · WB18 **4** · WB19 **2** ·
WB20 **5** · WB21 **2** · WB22 **1** · WB23 **2** · WB24 **13** · WB25 **1** · WB26 **1** ·
WB27 **1** · WB28 **2** · WB29 **1** · WB30 **2** · WB31b **10** · WB32 **3** · WB33 **8** ·
WB34 **3** · WB35 **5** · WB37 **1** · WB38 **4** · WB39 **3** · WB40 **2** · WB40b **3** ·
WB41 **1** · WB42 **1** · WB43 **7** · WB44 **2** · WB45 **1** · MP-B5c **1** · MP-FK1a **6** ·
MP-FK1b **5** · MP-FK2a **6**.

**Zero regressions. Three strengthened** (WB24 12→13, WB28 1→2 — RG3's own label now also
reddens — WB31b 9→10). **Only WB46/WB47/WB48 survive, and they are one door.**

---

## D5 — The terminating fork (and my verdict under each)

**I am not asking for more words.** A longer `_COMMS_DUTY_VOCABULARY` loses to the next synonym,
and I would break it again next pass. That regress is the thing to stop, not to feed.

**CL3 — the terminating pin (RECOMMENDED).** Pin `_INSTRUCTIONS` itself as an **allowlist of
declared paragraphs**: a module-level tuple of the served paragraphs, with the ruled comms block as
one member, and `assert _INSTRUCTIONS == "\n\n".join(_DECLARED_PARAGRAPHS)`. The safe set is the
whole served document — small, enumerable, and already fully specified by the packets that own it.
Then WB46/47/48 all die, no word list exists to be paraphrased around, and any packet adding a
paragraph meets a deliberate decision at one pin. Keep the vocabulary detector and the inversion
denylist as **regression gates** for the measured attacks — do not grow either.
*Cost: one tuple + one assertion; every packet touching `_INSTRUCTIONS` updates it, which is the
point.* **Verdict under CL3: SUFFICIENT.**

**CL4 — rule it a KNOWN BOUND.** Under the repo's *"WHEN YOU CANNOT CLOSE A HOLE, PIN IT"* law: a
pin asserting that prose OUTSIDE the ruled block is guarded by review rather than by a gate, with
the named re-open trigger *"any packet that adds `_INSTRUCTIONS` prose bearing on comms duties"*
(packet 04's `_comms_footer` pulls it), and a docstring correction so CL1 no longer claims to
allowlist what it deny-lists. **Verdict under CL4: SUFFICIENT** — a bound met deliberately, with
its rationale attached, is not the same object as an unknown hole. I record that in advance so this
does not need a fifth pass.

**What I will not sign:** the current state *as described*. Not because the door is large, but
because a pin whose docstring says ALLOWLIST while its mechanism DENY-LISTS is the exact
mislabelling that makes a future reader stop looking — and this repo has paid for that six times.
Either mechanism (CL3) or label (CL4) must move.

---

## D6 — FINAL P1b QUANTIFIER TABLE (closed)

47 invariants across the three verbs, the dispatcher, the skew block, the wiring and the teaching
surface. **46 ∀ · 1 GUARDED.** Every ∀ row's receipt is a wrong build that DIES; the GUARDED row
carries its surviving-door receipt.

| group | invariants | class | receipt |
|---|---|---|---|
| **dispatcher** (1–8, 42) | recipient charset · broadcast scope · **session-scoped resolution** · retired reject · `set_status` closed set · pre-touch reject ordering · no status write · all-or-nothing · fail-loud on ledger failure | **∀ ×9** | WB11 4 · WB7 4 · WB8 1 · WB9 3 · WB10 5 · WB22 1 · (3-leg fixture) · (committed) · MP-B5c 1 |
| **send render** (9–13) | shared cap · true remainder · broadcast count-form · ack teach · question teach | **∀ ×5** | WB25/26/29 1 each · WB27 1 · WB23 2 · WB19 2 |
| **drain render** (14–28, 43–47) | config limit · own cap · per-action range text · whole-set totals · elision arithmetic · fenced bodies · `{context}` cell · argument comparand · `acked_at` keying · gate-and-list · runnable command · window scope · peek rule · re-serve keying · refs cap+count · skew for the draining agent · past-the-cap remainder · name-agnostic · versions not re-derived · magnitude ordering | **∀ ×20** | WB12 2 · WB13 1 · (parametrized) · WB15 4 · WB3 3 · MP-FK1a 6 / MP-FK1b 5 / WB24 13 / WB35 5 · WB20 5 · WB4 1 · WB5 2 · WB6 2 · WB6 · (elided fixture) · WB21 2 · WB20 · WB28 2 / WB37 1 · WB38 4 · WB41 1 · WB42 1 · WB43 7 · WB44 2 |
| **skew block** (29–30) | drain serves BOTH halves · ONE implementation | **∀ ×2** | WB1 6 · WB39 3 · WB18 4 |
| **ack render** (32–37) | a home per outcome · group-exact membership · duplicate across groups · receipt counts · multiplicity (MEMBERSHIP) · ascending · note gating | **∀ ×7** | (set-equality) · WB33 8 / WB34 3 · WB16b 1 · WB32 3 · WB16r 4 / WB16t 2 · WB16s 1 · WB17 1 |
| **wiring** (38–39, +RG5) | each handler calls its render · `build_app_context` constructs the ledger · `aclose` closes it | **∀ ×3** | WB2a 6 / WB2b 14 / WB2c 3 · (introspection + control) · (new pin, green on my reference) |
| **teaching** (40–41) | the tool schema teaches honestly · the ruled block is exactly the ruled sentences, and the only comms-duty paragraph | **∀ for the schema; ∀ for replacement and for addition inside the block; GUARDED for paraphrase outside it** | WB30 2 · WB31b 10 · WB40 2 · WB40b 3 · WB45 1 · **WB46 / WB47 / WB48 → 0 (§D3)** |

---

## D7 — Residuals carried forward, each with a verdict

1. **C6.1 (unruled sentence order)** — **CLOSED**, settled at clause 4 as recommended.
2. **RG3 (the refs template)** — **CLOSED**, with its own classified label; better than my workaround.
3. **RG5 (`aclose`)** — **CLOSED**; green on my reference unchanged.
4. **MP-D5's structural-pin-alone residual** — **CLOSED** (WB18 now 4 RED).
5. **`ruff PLR0912` on `AppContext.comms` + `PLC0206` on the ack grouping** — **still real**: two
   post-lint refactors a builder must invent, neither described. (P14.)
6. **`_p03_entry` still defaults `acked_at`** — **acceptable, mitigated** (WB5 → 2 RED).
7. **The drain elision proof marker is value-free** — **mitigated** (WB3 → 3 RED).
8. **Surface pins rest on the message fake's honesty** — **unchanged** (RG4); the fake CAN fail (§7)
   but only `test_message_ledger.py` re-checks it.
9. **`docs/design/2026-07-12-pkt28-c1-semantics.md` doc corpse (8 hits)** — **still live**;
   re-swept this pass, unchanged. One supersession line owed.
10. **`test_surreal_harness.py` (struck adversary's escalation)** — **still unverified by me**,
    outside the graded five. For the lead.

---

## FINAL VERDICT

# CONTRACT INSUFFICIENT — one door, one pin, and a ruling that would also close it

**What I could not break, having spent four passes trying:** 49 of 52 wrong builds die, every one
to a named pin; all four closing items (CL1, RG3, C6.1, RG5) land and hold; the contract is
satisfiable at `1209 passed / 0 failed` with ruff and mypy clean, post-lint, on a reference built
from the rulings alone; the RED is honest at 299F/910P with zero collection errors; and the wave
closed two residuals of mine with fixes better than the workarounds I had reached for. **The arc
is 6 blockers → 1 critical → 1 major → one bounded door.** This is, by a distance, the strongest
contract I have graded in this packet.

**The door:** `_COMMS_DUTY_VOCABULARY` is a seven-word deny list under an "allowlist the safe"
docstring, and ordinary paraphrase walks through it — vocabulary-free (WB46), inflected (WB47), or
folded into a paragraph this packet already edits (WB48), each at 1209/1209. Feeding it more words
loses to the next synonym.

**One action closes it, and I have pre-committed my verdict to both:**
- **CL3 — pin `_INSTRUCTIONS` as a declared paragraph allowlist** (one tuple, one assertion).
  Terminates the regress; the vocabulary detector and the inversion denylist stay as regression
  gates. **→ SUFFICIENT.**
- **CL4 — rule the residual a KNOWN BOUND**, with the named re-open trigger (packet 04's
  `_comms_footer`) and a docstring correction so CL1 stops claiming to allowlist what it
  deny-lists. **→ SUFFICIENT.**

Either way this needs no fifth adversary pass: **the lead's ruling is the certification.** I record
INSUFFICIENT only because I hold a reproducible surviving build and it is not mine to declare out
of scope — the proportion is one pin or one paragraph of prose, not a wave.

*Final verdict pass written 2026-07-24 against HEAD `f6d88b3`. Reference build
`36a6ca0d7ee04844809cae54f0436c82 server.py` / `bdbda576ee327e3f0c547dccf2fcbd22 config.py`. Every
claim above is dated to that commit.*
