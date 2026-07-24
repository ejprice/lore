brief-base v6 read

# REPORT — contract-surface-03b (packet 03b surface contract, delta rows A–E + six authorized amendments)

## SUMMARY BLOCK

- **State: done-with-escalations.** Contract authored, committed (`3b8866a`, `3c6f704`), RED on purpose.
- **Satisfiability receipt: 871 passed / 0 failed** against a REFERENCE BUILD of S4/S5 in an isolated scratch copy — but ONLY after one fix I am **not authorized to make** (D1 below). Provenance receipt: `loremaster.__file__ = /home/ejprice/scratch-03b-refbuild/loremaster/loremaster/__init__.py`.
- **Mutation receipt: 17/17 load-bearing pins PROVEN RED** against that reference build; R3/S4.1/S4.2/#145 legs also show the COMMITTED pins staying GREEN under the same mutation — the evidence each amendment was necessary.
- **D1 — BLOCKING ESCALATION (seventh amendment, NOT made):** the committed fleet-elision marker is cross-satisfied by the drain render **under S4.2's CORRECT arithmetic**. MEASURED both ways: correct build → **2 failed**; wrong (fleet) arithmetic → **2 passed**. The committed contract currently **rewards the wrong build**. Recommended fix in §Escalations.
- **D2 — ESCALATION:** S4.2's context-cell branch 3 (`thread == session → empty`) needs a `session` the ruled signature does not carry. Two branches pinned, branch 3 deliberately UNPINNED.
- **D3 — deviation:** S3 part 2's ∀-ban, executed **verbatim**, is RED on the CORRECT build (`" "`, the committed join separator). Implemented as the precise placeholder-only ban instead; measured, documented in-code.
- **D4 — deviation:** `question` is now a REQUIRED kwarg on `_p03_message`/`_render_send`/`_message`, and `message` on `_send_result` (repo law: no default on a branched-on parameter). Committed call sites updated mechanically.
- **`_message_fakes.py` (the ORACLE) was NOT touched.** No oracle change; no two-suite satisfiability receipt owed.
- Counts (before → after): promise_registry **11F/85P → 14F/104P** · comms_tool **149F/554P → 198F/555P** · message_ledger **180P/12s → 180P/12s** (unchanged) · mypy **36 → 45** (all forward refs to the unbuilt surface; `test_message_ledger.py` **2 → 0** ✅) · ruff **clean** · neighbouring comms suites **330 passed, no regression**.
- Receipts: §Satisfiability · §Mutation battery · §Escalations · §Per-row work.

---

## 1. Escalations (the operator/lead owns these; I made none of them)

### D1 — BLOCKING. A committed pin that penalises the correct build and rewards the wrong one.

**The finding.** `_PROOF_LIST`'s fleet-elision proof carries the marker `"— re-run with limit=5"`
(`f"{_EM_DASH} re-run with limit=5"`; fixture `rows=[a,b], total_active=5, limit=2`). S4.2 rules the
drain elision's arithmetic as `next_limit = more = total_pending − shown`. The committed drain-elision
proof fixture is `entries=[61,62], total_pending=7, limit=2` → `more = 5` → the drain renders
`+5 more unread — re-run with limit=5`, **which contains the fleet marker verbatim**.

`TestNoMarkerIsCrossSatisfiedByAnotherProof::test_no_marker_is_cross_satisfied` therefore goes RED, and
`TestMarkerCrossSatisfactionBound::test_KNOWN_BOUND_a_k_specific_prefix_weakening_is_not_caught` goes
RED with it (it asserts the violation list is empty).

**MEASURED, both legs, in the scratch reference build (2026-07-24):**

| leg | drain arithmetic | result |
|---|---|---|
| A | `next_limit = more` — **S4.2's ruled, CORRECT form** | **2 failed** |
| B | `next_limit = shown + more` — fleet's form, the DISHONEST re-ask | **2 passed** |

**A builder who implements S4.2 correctly is punished; a builder who copies fleet's arithmetic is
rewarded.** This is the "spec/contract prescribes the bug" class (PKT-28 C1's §5.1 shape), live in the
committed contract, and it is invisible today only because `_render_comms_drain` does not exist yet.

**Recommended fix (a SEVENTH amendment — authorization required, strengthen-only):** promote the fleet
marker to the FULL rendered line, exactly as fix-wave items 1 and 3 already did three times in this
same file for the same reason:

```python
    PromiseProof(
        literal="+{more} more — re-run with limit={next_limit}",
-       marker=f"{_EM_DASH} re-run with limit=5",
+       marker=f"+3 more {_EM_DASH} re-run with limit=5",
```

**PROVEN:** with that one-line change and the correct arithmetic, the whole contract is
**871 passed / 0 failed**. Root cause fixed (a value-bearing but line-INCOMPLETE marker), not hidden.
I rejected the alternative (moving the drain fixture's numbers) — it conceals the weak marker and the
collision returns the next time two fixtures' arithmetic aligns.

### D2 — S4.2's context-cell branch 3 needs an input the ruled signature does not carry.

S4.2 rules the cell as: `task_id` present → ` (task {task_id})`; **else `thread != session`** →
` (thread {thread})`; else empty. The third branch needs the SESSION. It is not available:
`_render_comms_drain(result, *, agent_name, limit)` is the signature S4.2 itself states **and** the one
the COMMITTED drivers already pin by calling it (`_render_drain` in `test_comms_promise_registry.py`;
`_render_drain_body`/`_render_drain_sender`/`_render_drain_thread` here). Neither `MessageDrainResult`
nor `InboxEntry` carries a session either.

Two readings, neither chosen:
- **(A)** `_render_comms_drain` gains a `session` kwarg. `_render_comms_send` already takes one, so this
  is the house shape — but a REQUIRED kwarg TypeErrors every committed driver, so it needs an
  authorization to update them (mechanical: add `session="wave7"`), i.e. another amendment.
- **(B)** the branch is dropped and the thread cell always renders when `task_id is None` — which is
  what a builder will do by default, and it contradicts S4.2.

**Recommendation: (A).** I pinned branches 1 and 2 plus the SINGULARITY property; branch 3 is
**deliberately unpinned**, and the gap is written into `TestRenderCommsDrainShape`'s class docstring so
it cannot be inherited silently. My reference build implements (B) — a placeholder, not a proposal.

### D3 — Design-doc correction: S3 part 2's ∀-ban is unsatisfiable as literally written.

S3 part 2 prescribes `assert all(_has_literal_text(t) for t in _classified())`. **Executed verbatim it is
RED on the committed, correct build:** `_PROMISE_FREE` contains `" "` (the `render_join` separator),
which is whitespace-only and so fails `_has_literal_text` — while carrying NO placeholder and therefore
no value slot to smuggle a promise through. A whitespace-only SEPARATOR and a placeholder-only TEMPLATE
are different things; `_has_literal_text` conflates them because it answers a different question.

Implemented as `_is_placeholder_only` — has ≥1 format field AND nothing but whitespace outside the
fields. Bans exactly the class the bound's docstring bans, needs **no exemption list** (so there is no
exemption to rot), and is green on the correct build. Reasoning is in the helper's own docstring, and
`test_positive_control_real_templates_and_separators_are_accepted` pins the `" "` discrimination
explicitly. **Not silently taken — this is the flag.**

### D4 — Deviation: fixture factories no longer default a branched-on parameter.

Repo law is explicit ("`_brief()` defaulting to `name='project'` MANUFACTURED this blind spot"), and
the 03b send render **branches on `message.question`**. Row C cannot be proven without a fixture that
sets it, so the factory had to change; the only choice left to me was default-vs-required, and a
default would silently re-create the monoculture on the very field this packet added a branch to.

- `_p03_message(*, question: bool, ...)` — REQUIRED · 1 call site updated
- `_render_send(*, grade, question)` — REQUIRED · 2 committed lambdas updated (`question=False`, semantics unchanged)
- `_message(*, question: bool, ...)` — REQUIRED · 2 call sites updated
- `_send_result(*, message, ...)` — `message` REQUIRED (its `None → _message()` default would have had to pick a `question` on the caller's behalf) · 3 call sites updated

These are **signature** changes to committed helpers, not changes to any committed **assertion**. Every
updated call site preserves its previous rendered value exactly.

### D5 — Candidate seventh amendment I did NOT make, recommended for the fix wave.

`_p03_entry(*, seq, grade="signal", acked_at: Any = None)` defaults `acked_at` — **and that default is
R3's root cause**. R3's authorization says "add the discriminating pin", which I did; removing the
default would be a further edit. Recommend removing it (4 call sites, each gains `acked_at=None`
explicitly) so the monoculture cannot re-form the next time a proof is added.

### D6 — Scope note: the LEDGER legs of inherited delta row 8 have no home.

03a2 row 8 asks for `[fake]`/`[real]` ledger pins for R5/R6. Those belong in `test_message_ledger.py`,
which 03b's authorization freezes except for the two mypy fixes. I pinned R6's convergence at the
**dispatcher** (`TestTheDrainSurfaceConvergesOnAnAckedButUndrainedMessage`, mutation-proven), which is
the surface I own and where the render-layer claim actually lives. The ledger-level legs are unowned —
lead's disposition.

### D7 — Builder constraint discovered by the reference build (not a defect; worth carrying into the brief).

The committed `ACK REQUIRED: {seqs} — lore_comms action=ack seqs=[{seqs_csv}]` template forces a
`{seqs_csv}` value. The obvious spelling `safe_str(",".join(str(s) for s in seqs))` is **DENIED** by the
deny-by-default canonicaliser (`GeneratorExp` — `TestTheCanonicaliserDeniesByDefault` goes RED), and
`render_join(",", ...)` introduces an UNCLASSIFIED `","` separator (`", "` is the classified one).
The shape that works: `render_join(", ", [safe_str(str(seq)) for seq in seqs])`. Measured, not guessed.

### D8 — Unrelated observation.

`loremaster/tests/test_trace_telemetry.py` (the sibling author's file, untracked at my HEAD) contributes
**6 mypy errors**. Not mine, not touched, named here because it is in the global mypy-zero 03b owns.

---

## 2. Satisfiability receipt (repo law: a contract ships proven 0-failed against a known-correct build)

Isolated tree via the blessed tool (NO worktree — standing directive):

```
./scripts/scratch_copy.sh /home/ejprice/scratch-03b-refbuild
  loremaster  -> /home/ejprice/scratch-03b-refbuild/loremaster/loremaster/__init__.py
```

A REFERENCE BUILD of the S4/S5 surface was applied there ONLY (three `_COMMS_ACTIONS` entries, the three
handlers, `_render_comms_send`/`_render_comms_drain`/`_render_comms_ack`, the dispatcher's new params,
the MCP wrapper's params + description, and S5's COMMS paragraph verbatim). The real tree carries **no
production change**.

```
871 passed in 6.88s        # test_comms_promise_registry.py + test_comms_tool.py
```

That is 0-failed for the **whole** 03b contract — the 149+11 committed RED pins AND my additions —
conditional on D1's one-line marker fix. Getting there surfaced D1, D3 and D7; none of the three was
visible from the RED tree.

## 3. Mutation battery — 17/17 PROVEN

Each row: break the reference build in the exact wrong way, assert the named pin goes RED, restore,
re-assert 871/871. The "committed stay GREEN" column is the evidence an amendment was NECESSARY.

| # | mutation | pin(s) that went RED | committed pins under the same mutation |
|---|---|---|---|
| 1 | **R3** — key `ACK REQUIRED` on grade ALONE | `test_an_ACKED_directive_row_draws_NO_ack_demand` · `test_the_ack_demand_lists_ONLY_the_UNACKED_directives` · `test_the_two_trailers_partition_the_served_rows` | **25P/0F — the committed proofs pass the defect** |
| 2 | **R5** — classify `"{msg}"` as promise-free | `test_no_classified_template_is_placeholder_only` · the bound pin itself | — |
| 3 | **R6** — rename `_render_comms_send` out of prefix | `test_the_scan_reached_every_comms_render_helper_that_emits` | — |
| 4 | **R7** — question line renders `session` not `thread` | `TestSendThreadInjectionCaseIsNotVACUOUS` (2F) · `test_the_question_line_names_the_MESSAGES_thread_not_the_session` | — |
| 5 | S4.1 — emit question line only for `grade=="signal"` | `test_the_question_teach_and_the_ack_trailer_are_ORTHOGONAL` | **25P/0F — both single-variable proofs are blind to a correlation** |
| 6 | S4.1 — recipient list uses its own cap, not the shared one | `test_the_recipient_list_shares_ONE_display_cap_with_the_coverage_surface` | — |
| 7 | S4.2 — copy fleet's elision arithmetic | `test_the_elision_re_ask_is_the_REMAINDER_not_the_running_total` | — |
| 8 | S4.2 — render trailers + elision on a PEEK | the three peek pins | — |
| 9 | S4.2 — `ALREADY ACKED` only for directives | `test_an_acked_SIGNAL_row_also_draws_the_ALREADY_ACKED_trailer` | **25P/0F — the proof uses a directive on both legs** |
| 10 | S4.2 — render BOTH context cells | `test_the_context_cell_prefers_the_TASK_over_the_thread` | — |
| 11 | 03a2-R6 — suppress the `ALREADY ACKED` label | `TestTheDrainSurfaceConvergesOnAnAckedButUndrainedMessage` | — |
| 12 | **#145** — rename a reachable render helper out of prefix (def + call site) | S2 Pin B | (the dead-entry scanner also fires — measured; so this case does NOT isolate Pin B) |
| 13 | **#145, DECISIVE** — ADD an unprefixed helper serving a NEW promise, called from a comms render | S2 Pin B | **ALL THREE promise scanners 3P/3P/2P — 0F. Pin B is the only thing that sees it.** |
| 14 | S5 — teach `action=drian` | the global ∀-pin · the scoped pin | — |
| 15 | S5 — attribute `action=rollup` to `lore_comms` | the scoped pin · the three-verbs pin | **the global ∀-pin stays GREEN — `rollup` is a real verb of another tool** |
| 16 | S5 — drop the thread-debt clause | `test_the_thread_debt_rule_is_TAUGHT_not_merely_implemented` | — |
| 17 | S3 — weaken a marker into another classified template | `test_no_marker_is_a_substring_of_another_classified_template` | — |

Row 13 is the whole argument for S2 Pin B: a brand-new served promise, in an unprefixed helper the
comms surface calls, is INVISIBLE to every committed promise scanner. Row 12 was initially recorded as
NOT PROVEN because my own expectation was wrong (the dead-entry scanner fires there too); corrected
against the measurement rather than restated.

The battery script lives at `/home/ejprice/scratch-03b-refbuild/mutation_battery.py`. **It is outside my
writable set, so it is not committed** — the table above is the durable record. Recommend the lead
archive the script beside this report (brief-base §1: prefer a committed script that regenerates a
measurement).

## 4. Per-row work

### Row A (S1 instrument 2 + S2) — `test_comms_promise_registry.py`
- **R6 amendment**: `TestTheScanReachedEveryCommsRenderHelper`'s `expected` gains
  `_render_comms_send`/`_drain`/`_ack`, with the defence-in-depth relationship to
  `test_no_dead_registry_entries` stated (that guard fires on the REGISTRY, not on COVERAGE, and is
  silent for a helper with no registered literal).
- **Pin A** `TestEveryCommsRenderLivesInServerPy`: package-wide rglob; no comms-prefixed function
  outside `server.py`. Non-vacuity pin (≥20 modules walked, server.py excluded), two self-attacks (both
  prefixes), one different-reason positive control. Measured clean on today's tree.
- **Pin B** `TestEveryRenderReachableFromCommsCarriesTheScannedPrefix`: module-local call graph, walked
  transitively from every prefixed function; any reached unprefixed function calling a render verb fails
  with `file:function:line`. Non-vacuity pin (roots ≥8, both prefixes present), three self-attacks
  (one-hop, transitive, `self.x()` attribute spelling), two positive controls — including the one that
  keeps the gate usable: a reachable helper that renders NOTHING (today's `_render_age`) must stay
  green. **Measured on today's tree: 19 roots, 20 reached, 0 violations.**
- Both delegate to ONE shared walker (`_module_functions` / `_is_comms_prefixed` / `_local_callees` /
  `_emits_render_verb`); the render-verb set is the committed `_RENDER_VERB_NAMES`, not a second copy.
- `TestTheScannedPrefixSetIsTheOneTheScannersUse`: the new `_COMMS_RENDER_PREFIXES` constant and the
  committed scanners' inline spelling are proven to AGREE, derived from the constant (change it and the
  test drives the committed scanner with the new prefix). This is the available form of "prove sharing
  by mutation" without editing frozen code — noted because a silent refactor of the committed scanners
  would have been a seventh edit.
- Threat model is stated IN the instrument (honest developer, not hostile author) so the verdicts follow
  mechanically and nobody re-argues it a fourth time.

### Row B (S3) — same file
- `TestNoMarkerIsASubstringOfAnotherClassifiedTemplate` (static, vocabulary-wide) + self-attack + a
  positive control proving a marker PREFIX is not a violation.
- `TestNoClassifiedTemplateIsPlaceholderOnly` + `_is_placeholder_only`/`_placeholder_only_classified`
  (see D3), self-attacked across five shapes, positive-controlled on the separators.
- **R5 amendment**: the bound pin's ∀-assertion now performs what its docstring promises; the committed
  `"{msg}"` assertion is KEPT (strengthen-only).

### Row C (S4.1) — both files
- Registry entry + `PromiseProof` for the question-teach line, full-line marker, `grade` held constant
  across both legs so the single variable is `question`.
- `send.thread` RenderCase (**R7**), with `question=True` — the only configuration in which the send
  render emits `thread` at all — plus `TestSendThreadInjectionCaseIsNotVACUOUS`, which proves the value
  reaches the render AND that it arrives via S4.1's line specifically.
- `TestRenderCommsSendShape`: the 2×2 `question × grade` orthogonality ∀-pin (the correlation neither
  committed proof can see), the thread-vs-session value discrimination, and the shared-cap pins at
  cap+2 and exactly-cap, derived from `_COVERAGE_NAMES_CAP`.

### Row D (S4.2) — both files
- Registry entry + proof for `ALREADY ACKED: {seqs} — no action owed`; both legs use a DIRECTIVE so the
  single variable is `acked_at`, and the no-emit leg is the row that legitimately draws the sibling
  trailer, never an empty drain.
- **R3 amendment**: three pins — an acked directive draws no demand; a mixed drain lists ONLY the
  unacked seq (seqs 71/82, no shared substring); and the positive control that two unacked directives
  are BOTH listed. Trailer assertions read the TRAILER LINE via `_drain_line_containing`, which fails
  loudly on a missing/duplicated line, so "the row was dropped" can never masquerade as "the seq was
  excluded".
- Elision arithmetic (2 shown of 7 pending: `more=5`, `shown+more=7`, `limit=2` all distinct), peek
  serves no trailers/elision (each with its positive control) and still serves header + rows, and the
  context-cell precedence + singularity.
- `TestTheDrainSurfaceConvergesOnAnAckedButUndrainedMessage`: 03a2-R6 end-to-end through the real
  dispatcher — served, labelled, counted, converged — with a fixture check that `ack` really does not
  stamp `seen_at` (without which the whole test is decoration).

### Row E (S5) — `test_comms_tool.py`
- Global ∀-pin over every `action=` token in `_INSTRUCTIONS`, derived from
  `_COMMS_ACTIONS | _TASK_ACTIONS | _FINDING_ACTIONS` — never a hand-list. **Green on today's build.**
- Scoped pin over the `COMMS:` paragraph, whose scoping premise (that the paragraph names lore_comms and
  nothing else) is itself CHECKED, not assumed — plus a three-verbs coverage pin so the two ∀-pins
  cannot pass over a paragraph that teaches nothing.
- Thread-debt and self-answer teaching pins (03a2-R5 / R2).

### Amendment +6 — `test_message_ledger.py`
`cast(int, result.message.seq)` in `_ask`/`_answer`, this file's existing idiom for `ledger: Any`
erasure. **180 passed / 12 skipped, unchanged; the file's mypy count is 2 → 0.**

## 5. Tool honesty

`lore_index()` freshness was NOT consulted — this run needed no code-structure search: every file was
point-read from paths the brief supplied, and every structural question (prefix reach, call graph,
marker overlap, action tokens) was answered by EXECUTING the real scanners/AST in memory against the
real tree, which is stronger than any index read. Greps were used for test-name/class maps, template and
marker locations, and call-site enumeration — non-symbol textual seams and exhaustiveness-critical
sweeps, the honest-grep categories; saying so per the dogfood protocol. No lore friction encountered;
nothing filed.

## 6. Housekeeping

**Scratch copy `/home/ejprice/scratch-03b-refbuild` is LEFT IN PLACE** (not a worktree — the standing
NO-WORKTREES directive is honoured). It holds the reference build + `mutation_battery.py` +
`apply_refbuild.py`, currently at **871 passed / 0 failed**. It is the fastest way for the
contract-adversary or the builder to re-run either receipt. **Lead: keep, archive the two scripts, or
delete — your call.** Nothing in it is on any branch.
