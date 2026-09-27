brief-base v17 read · brief project v7 read · store reference read FIRST (`docs/reference/surrealdb-31-capabilities.md` §0 banner, §1, §3 incl. the #497 RETURN-in-transaction entry)

# REPORT — adversary-64b (contract-adversary for packet 64b-i: `lore_findings` governed retrofit — substrate + write side + migrate)

## SUMMARY BLOCK
- **State: done.** Deviations: (D-1) I did not write an independent full reference build: 64b-i's production
  surface is ~2000 diff lines. I used the author's §HELD Part C as the reference, graded it as a SUSPECT (it fails
  MP-1 and contradicts am-7's FK-7 shape), and built a CORRECTED reference only where a pin needed a correct-build control
  (MP-1). (D-2) The forks were RULED mid-pass (am-7 `6e42ed1`); recorded in §AM7, not graded. (D-3) My first
  baseline and first screen were killed by my own watchdog; the instruments were fixed (§INSTRUMENTS P0 1–2) and
  both re-run.
- **Graded:** `d8ea4ba` · **HEAD-at-report:** `c383edd` · DIFFERENT (5 behind; docs only: 58 am-8, 64 am-7, lead
  and sidecar reports; zero code/test/script lines changed. Every verdict rests on files byte-identical at both).
- **VERDICT: CONTRACT INSUFFICIENT.** 14 MISSING PIN · 4 SAT DEFECT · 2 NEW DOOR · the rest NOT A DEFECT.
- **P1 headline: 10 wrong builds + the author's own reference SURVIVE.** WB1 set_scope oracle · WB2 visible-deny
  hidden by id · WB3 classifier authorizes READ · WB4 stale-capability cache · WB10 identity step's 2nd registry
  read · WB17 supersedes-by-id unfiltered · WB19 annotate drops `actor_agent` · WB21 private identity compare ·
  WB22b `--table finding` also migrates memory · WB23 `scope=` ignored on 7 verbs. **Combined full suite:
  171 failed / 12079 passed, node-for-node identical to the reference** (§A). The reference itself serves an
  existence oracle plus a FALSE "concurrent change" message on set_scope (MP-1). Killed: CTL1, WB5, WB6, WB9,
  WB13, WB22.
- **SAT (HEAD + §HELD verbatim): NOT 0-attributable.** S-1 the fold deletes `_governed_contract_64` while
  `test_mcp_server.py:2297` imports it (17 errors). S-2/S-3 G9 grows 63c a28's ∀-legs pins onto the finding leg
  and they RED (FORK-1 pre-count `backfilled`; A2 not fail-closed). S-4 58-r2's `cas_runtime` driver goes stale.
  The author's receipt was on `e6e17d8`, which predates those contracts.
- **FK-9 (TYPE_CHECKING ownership):** sound for OWNERSHIP, unsound as a typecheck CONTRACT. A coherent wrong-shape
  build is mypy-IDENTICAL to the reference; declared ⊂ exercised (7 keyword surfaces undeclared); the Any aliases
  have no self-destruct → MP-9.
- **QUANTIFIER (P1b) / REACH (P1c):** §P1b (19 rows, 9 guarded, every one with a receipt) · §P1c (13 rows;
  EMPIRICAL R5/R6/R10/R11/R12/R13, construction-inspected R1–R4/R7–R9).
- **Packages considered:** K1–K7 (§PKG) — fastmcp/pydantic validation REUSE, `lorerunes.is_blank` REUSE,
  stdlib dataclass/AsyncMock/commonprefix REUSE, `classify_zero_row_cas` bespoke (a 1-function bridge),
  `mutation_proof.py` keep_with_trigger. No P-PKG finding.
- **Odoo-20 portability:** n/a — no Odoo seam touched (0 seams · 0 non-stable · 0 rulings).
- **Reuse ledger:** none. I added no production symbol; the scratch pins import only the contract's own substrate.
- **decisions-needed:** (1) MP-7: does stamp_owner's capability-verify read count against R8? (the reference does
  2 agent reads per governed write; am-7 says ONCE). (2) MP-12: admin `set_scope` stores ANY string (dangling
  keep, `banana`, hostile text): "admin any" = any row or any string? (3) The DUAL L5 order (authorize before
  edge validation): a one-line adjudication.
- **Receipt pointers:** §A (missing pins + pairs) · §SAT · §FK9 · §P1b · §P1c · §DUAL · §AM7 · §P3/§P5/§P6 ·
  §P4/P7 · §INSTRUMENTS (all drivers, specs, pins, probes verbatim). Lore friction filed: #511.

---

## §P6b-1 — DUAL stage 1: my OWN enumeration of the replaced behaviour (written BEFORE opening the author's §9)

Source read at `c9e5eb8` (== `d8ea4ba` for every code file): `server.py::AppContext.findings`,
`_with_comms_footer` / `_comms_traffic_line` / `_resolved_comms_traffic_line`, `_agent_param_description`,
`_require_finding_arg`; `findings.py::FindingLedger.report` / `_transition` / `annotate` /
`_guarded_append_fragment` / `_resolve_or_raise`. Lore-first was not usable for this span-read (the
enumeration needs whole bodies); `sed` over the named files, said so.

**Dispatcher (`AppContext.findings`)**
- D1 `_validate_comms_identities(agent, session)` is the FIRST statement (charset link 1b).
- D2 `items` is a foreign param for every non-batch action (teaching `ValueError`).
- D3 `created_by` REQUIRED + non-blank on `report` (`_require_finding_arg`), `actor` REQUIRED + non-blank on the
  six status/batch verbs.
- D4 `body` optional (→ `""`); `kind` defaults `friction`.
- D5 unknown action → `ValueError` listing `_FINDING_ACTIONS` IN TUPLE ORDER (the served list).
- D6 single-item domain errors (`FindingNotFoundError`/`IllegalTransitionError`/`FindingChainCycleError`) surface
  unchanged; the batches catch per item, render per item, and ABORT the rest on a transport fault.
- D7 `_render_finding_transition` names the CALLER-SUPPLIED actor ("transitioned to X by <actor>").
- D8 the footer: ONE exit; `writes < 1` ⇒ no footer AND no registry read; `agent=` supplied ⇒ R8(1) resolve +
  LOUD teaching on unknown/ambiguous; omitted ⇒ R8(2) first-supplied attribution `(actor, created_by)`,
  charset-gated before any read, third-person render; at most ONE registry read per call.
- D9 `agent=` description carries the "disclosed exception … matched, never authenticated" sentence.

**Ledger (`FindingLedger`)**
- L1 `report`: area/category blank → `ValueError` BEFORE any I/O; kind/subject/created_by have NO ledger guard
  (the store ASSERT was their only backstop).
- L2 `report(supersedes=X)`: X resolved UNFILTERED (nonexistent ⇒ `FindingNotFoundError`); X never mutated;
  a real `type::record` link on the successor.
- L3 `report`: number minted in the SAME txn via the counter UPSERT (gapless under contention; UNIQUE backstop).
- L4 `report`: id = uuid4 hex; `provenance = {created_by, created_at, events: []}`; status `open`; a post-create
  re-read (vanished ⇒ `FindingLedgerError`).
- L5 `_transition`: edge validated BEFORE any write (typed error naming both states; row untouched).
- L6 `_transition`: CAS `WHERE status = $expected_from` + THROW-on-zero-rows; event appended SERVER-SIDE.
- L7 lost race: re-read fresh; vanished ⇒ NotFound; fresh edge illegal ⇒ the fresh-state `IllegalTransitionError`;
  fresh edge legal ⇒ "lost a concurrent transition race" — NEVER success, even when the winner reached the same
  target.
- L8 `SurrealConnectionError` / `TxnContentionExhaustedError` pass through untouched (never re-read) — BOTH verbs.
- L9 event shape: `{actor, action: transition, to, at, note?}` — `note` key present ONLY when not None.
- L10 `annotate`: note blank ⇒ `ValueError` before I/O; legal in EVERY status; event has NO `to`; status unchanged;
  zero-row ⇒ vanished → NotFound, else the ORIGINAL store error re-raised.
- L11 per-field provenance: `created_by` column + `provenance.created_by` = the caller's free text (not
  necessarily an agent name); `events[].actor` = the caller's free text.

_(stage 2 — the diff against the author's §9 — is §DUAL below.)_

## §PKG — P-PKG: my OWN package table (built BEFORE reading the author's `Packages considered:` line), then the diff

Mechanisms the contract SPECIFIES (pins demand them) — derived from the pins, not the author's list:

| # | mechanism | candidate library | what I READ | verdict |
|---|---|---|---|---|
| K1 | refusing a retired served param with a field-naming error | pydantic (FastMCP's own arg validation) | the reference `AppContext.findings` signature (no `created_by`/`actor`) + the identity pin `test_a_retired_argument_is_refused_by_the_mcp_layer_naming_the_field` driving `tool.run({...})` | **REUSE** (the MCP layer's own `ValidationError`) — matches the author |
| K2 | blankness of a text column | `lorerunes.is_blank` (in-house shared home) | reference `FindingLedger._require_non_blank`; `test_report_uses_the_shared_blankness_predicate` (AST) | **REUSE in-house** — matches |
| K3 | typed per-verb flags | stdlib `dataclasses` (`@dataclass(frozen=True, kw_only=True)`) | reference `server.GovernedVerbSpec` | **REUSE stdlib** — matches (not called out by the author; no package decision to make) |
| K4 | zero-row CAS classification | none (a policy over this repo's PDP; no library models "re-authorize the fresh row") | reference `governed.classify_zero_row_cas` | **bespoke, correctly** — a 1-function bridge over `pdp.authorize` + `run_query` (minimal surface) |
| K5 | mutation-proof driver | `mutmut` / `cosmic-ray` (general mutation testers) | the author's pasted `mutation_proof.py` usage (targeted, hand-declared mutations + declared-RED diff both ways) | **keep_with_trigger** — the house instrument does a thing the generic tools do not (declared-set-diff vs `--collect-only`); trigger: a need for UNdirected mutation sweeps |
| K6 | spies that record args | stdlib `unittest.mock.AsyncMock(wraps=)` | `test_comms_footer._footer_harness` | **REUSE stdlib** — matches |
| K7 | "longest shared description prefix" | stdlib `os.path.commonprefix` | the converted `test_all_three_tools_share_ONE_agent_description` | **REUSE stdlib** — matches |

**Diff vs the author** (`Packages considered: fastmcp validation (read + probed, I-1) → REUSE. No other mechanism
specified.`): K1 agrees, and its I-1 probe is pasted. K2–K7 are unmentioned by the author. None is a hand-roll a
library would replace, and K4 is a legitimate bespoke bridge. **No P-PKG finding.** One nuance: amendment 2 §4 asked
whether FastMCP exposes an input-validation HOOK (to attach the teaching sentence to the refusal). The author's I-1
shows only that the default refusal names the field. It does not read the installed FastMCP source for a hook. The
amendment assigns that read to the BUILDER (`Packages considered:` row), so this is **NOT A DEFECT** in the contract.
It is still an open question the builder must answer by reading the installed source.

## §PORT — P-PORT
`Odoo-20 portability: n/a — no Odoo seam touched` (lore is not an Odoo codebase; the contract pins no Odoo model,
field, view, ACL or ORM path). Author's line agrees. 0 seams · 0 non-stable · 0 rulings.

## §FK9 — THE TYPE_CHECKING-OWNERSHIP VERDICT (the brief's priority flag; #461 shape)

**Mechanism under attack.** Each new file declares its ruled-but-unbuilt symbols in an `if TYPE_CHECKING:` block,
and `scripts/pending_contracts.yaml` bound `packet-64b-i-contract` owns the resulting mypy lines. At RUNTIME every
pin reaches those symbols through `vars(module).get(...)`, `getattr(...)` or an explicit `x: Any = governed.…`
alias. All three are typed `Any`.

**(a) Can a pin be green-for-the-wrong-reason BECAUSE of an Any alias? — at RUNTIME no; at the TYPECHECK gate YES.**
- Runtime: every Any-routed call is still EXECUTED by a pin, so a wrong signature raises `TypeError` and reds.
  I found no pin whose green depends on an Any alias.
- Typecheck, EMPIRICAL: in scratch copy `fk9` (= HEAD + §HELD), I built a coherent WRONG-SHAPE build: renamed
  `classify_zero_row_cas(ledger_verdict=)` → `verdict=` and `authorize_guarded(projection=)` → `columns=`, and moved
  every production caller with it (diff: `fk9_wrongshape.diff`, 2 files, 7+/7−). `uv run mypy loremaster` then
  gave: **per-file error counts IDENTICAL to the unmodified reference** (`29 errors in 13 files`; `diff` of the
  per-file tables → identical). **Zero lines in the 8 contract files.** The typecheck gate cannot tell the ruled
  signature from a wrong one.
- POSITIVE CONTROL (the probe can see): renaming `FindingLedger.report(caller=)` → `identity_subject=` coherently
  surfaced `loremaster/tests/test_findings_schema_64b.py:60: error: Unexpected keyword argument "caller" for
  "report" of "FindingLedger" [call-arg]`. That is the ONE declaration written as a typed CALL
  (`_ruled_64b_i_report_takes_the_caller`). So typed declarations do carry shape. The name-only tuples
  (`_RULED_64B_I = (FindingLedger.set_scope, classify_zero_row_cas, …)`) carry existence only.

**(b) Does the declared symbol set equal what the pins exercise? — NO: declared ⊂ exercised.** I DERIVED the
exercised set (`derive_symbols.py`, §INSTRUMENTS): every attribute and identifier-shaped string the 8 files name,
resolved against the touched production owners in BOTH trees, keeping REF − BASE:
- New NAMES (all declared ✓): `governed.{classify_zero_row_cas, resource_from_row}`,
  `server.{GovernedVerbSpec, _RETIRED_IDENTITY_ARGS_TEACHING, _requires_capability}`,
  `principals._migrate_finding_scope`, `FindingLedger.{audit_store, handle, set_scope}`,
  `GuardedPlan.{compose, guard}`, `AppContext._resolve_identity`.
- New KEYWORD surfaces the pins drive, **NONE declared**: `authorize_guarded(projection=, target_scope=)`,
  `guarded_write(params=, target_scope=)`, `FindingLedger.report(scope=)`, `FindingLedger.annotate(caller=)`,
  `AppContext.findings(capability=, scope=)` (and `report(caller=)`, which IS declared, typed). Plus
  `ReportResult.scope` (read by the reference's render). These are exactly the Any-routed calls, and several
  (FK-4's `target_scope=`/`params=`) are author-CHOSEN shapes that a builder reading the bound's
  `reopen_trigger` would never see.

**(c) Is the self-destruct real? — for NAMES yes; for SHAPES no, by construction.** The gate's legs 3/4
(`scripts/pending_contract_gate.py::_compute_liveness` / `transcript_self_destruct_findings`) fire per SYMBOL when
a name resolves or stops erroring. A build that lands `FindingLedger.set_scope` as ANY attribute (even
`set_scope = None`) discharges that line. The (a) leg shows the wrong-shape build is mypy-identical to the
reference, so the typecheck half of the bound discharges on a wrong shape. What still catches the shape is the
pytest half. That half is partitioned by FILE (#461, stated in the author's §10): while ANY symbol of a file's
entry is missing, the bound adjudicates EVERY pytest red in that file. That includes the two converted 4000- and
13000-line suites, `test_mcp_server.py` and `test_comms_footer.py`.
- Net: self-destruct forces the entry to shrink as names land, and once a file's last symbol lands, leg 2 forces
  deletion and the file's reds surface. So the protection holds **if the builder deletes entries as told**. It
  is weakest mid-build, when one unbuilt symbol keeps a whole file's reds adjudicated.

**(d) Does it weaken the typecheck gate for the rest of the file? — YES, PERMANENTLY, as written.** The Any aliases
(`authorize_guarded: Any = governed.authorize_guarded` at `test_governed_substrate_64b.py`
`TestAuthorizeGuardedProjectsTheLedgersColumnsInOneRead`; `guarded_write: Any = …` in `TestSetScopeBranchIsExercised`;
`table: Any = vars(server)["_FINDING_ACTIONS"]` ×6 in the identity file; `vars(module).get` everywhere) have no
self-destruct. Nothing requires the builder to replace them with typed calls when the symbols land. After the
build, every one of those call sites stays statically unchecked forever, including against FUTURE signature
drift of production code the contract pins.

**VERDICT FK-9: the shape is sound for OWNERSHIP (every red is owned and the names self-destruct) and UNSOUND
as a typecheck CONTRACT (it certifies existence, not signatures).** One missing pin, cheap and demonstrated by the
positive control: **MP-9** (§A). Class and siblings are there.

## §SAT — satisfiability on the RIGHT base (HEAD + §HELD verbatim), with my own baseline on the same box

**Trees** (all `./scripts/scratch_copy.sh` copies; provenance printed by the tool at creation):
- `ref` = HEAD `c9e5eb8` (== `d8ea4ba` for every code and test file; only docs moved in between) + §HELD A→A2→B→C,
  applied verbatim and committed in scratch as `e2f4504`. `loremaster.__file__` =
  `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/5b857dd0-ba19-43fb-bcd2-fb90d71794d3/scratchpad/ref/loremaster/loremaster/__init__.py`;
  `lorerunes.__file__` = `…/scratchpad/ref/lorerunes/lorerunes/__init__.py`.
- `base` = the same HEAD, no §HELD. The uncommitted 63c a28b working-tree edits (3 modified test files +
  `test_fixwave_a28b_63c_i_a.py`) were REMOVED in both copies (`git checkout -- .` + `rm` of the untracked files).
  Both copies grade COMMITTED state only.

**§HELD integrity.** The four parts extracted from `REPORT-contract-64b.md` hash to the author's stated prefixes
(`985d950ec5e98a66` A · `de6c224b88ffe950` A2 · `62a34ec2cd1ecf72` B · `3a6f992297184558` C).
`git apply --check` of all four JOINTLY: **OK on clean HEAD `c9e5eb8`**. On the LIVE shared tree (HEAD + 63c's
uncommitted a28b fold) it FAILS: `error: patch failed: loremaster/tests/test_retry_seam.py:6780` (part B only;
A, A2 and C check clean there).

**Contract files on the reference** (the 6 new files + the 2 converted suites, `-n 12`):
`1062 passed, 1 skipped, 17 errors`. Every error is `ModuleNotFoundError: No module named '_governed_contract_64'`
at `test_mcp_server.py:2297` (fixture `finding_context`) → **S-1**. With that one import repointed in scratch
(commit `71276f6`), the no-op control CTL0 over the same 8 files gives **`1079 passed, 1 skipped, 0 failed`**.

**Full suite on the reference** (`-n 12`, `run.sh` v1): `171 failed, 12079 passed, 63 skipped, 3 xfailed`.
Adjudicated by node id against a TARGETED baseline at HEAD: every file holding a reference red, run on `base`
(`-n 4`: `164 failed, 465 passed, 1 skipped`, rc 1, no watchdog). **164 of the 171 reds are red at HEAD too**
(58-r2's and 63c-a28's committed RED contracts, which the 64b-i reference does not build). **7 are NOT red at
HEAD:**

| # | node (reference red, green or absent at HEAD) | why it reds on HEAD + §HELD | verdict |
|---|---|---|---|
| 1 | `test_governed_routing_63a.py::TestTheReverseRoutingDirection64b::test_an_enforced_or_observed_verb_is_routed` | the 63b comms legs are enforced and not routed (#487) | **DESIGNED** (author's §HELD step 7). NOT A DEFECT |
| 2–4 | `test_fixwave_a28_63c_i_a.py::…::test_A2_an_unexpected_INFO_FOR_DB_shape_raises_byte_inert[finding-{keyless-dict,list,str}]` | these nodes do NOT EXIST at HEAD. §HELD part B (G9) adds `finding` to a19's `_MIGRATE_TABLES`; a28 imports that tuple, so its A2 fail-closed pin now drives the finding leg. The leg proceeds on a forged `INFO FOR DB` answer: `Failed: DID NOT RAISE <class 'loremaster.store._txn.SurrealStoreError'>` | **SAT DEFECT S-3** |
| 5 | `test_fixwave_a28_63c_i_a.py::TestBackfilledIsMeasuredOnEveryLeg63cIAa28::test_FORK1_backfilled_equals_the_rows_the_run_changed[_migrate_finding_scope]` | absent at HEAD (collect-only: HEAD derives `{agent, memory, message}`, the reference `{agent, finding, memory, message}`). Reds `governed leg '_migrate_finding_scope' has no FORK-1 population`. Underneath, the reference returns `backfilled=unmigrated`, a PRE-count, which am-27 FORK-1 forbids ("a served count must be the rows the UPDATE STAMPED, measured, ∀ legs") | **SAT DEFECT S-2** (+ missing pin MP-5) |
| 6–7 | `test_reanchor_58_r2_cas_runtime.py::TestExhaustedContentionPropagatesUNREADFromEveryCASVerb::…[findings.py::annotate]` / `[findings.py::_transition]` | GREEN at HEAD. The reference merges both doors into `findings.py::_run_guarded`, so 58-r2's committed driver table goes stale: `AssertionError: findings.py::annotate's driver is stale: not a derived CAS verb` (and `_transition`) | **SAT DEFECT S-4** |

**The author's SAT receipt was measured on `e6e17d8`, before 58-r2's and 63c-a28's contracts were committed.
It is STALE against HEAD. "0 attributable reds" does not hold on the right base.**

**Forward collisions** (what changes when 63c-i-a's a28b fold, am-32/33, and 58's r3 land). Derived by
`git apply --check` on the live tree and by the node-id diff above, not read off the author's list:
- `test_retry_seam.py`: collides NOW with the uncommitted a28b edits (the error above). The author listed it
  (§HELD step 11). Per 58 am-7 (`01565f9`), a28b lands ONE scanner keyed on the import-resolved caught class. Part
  B's static G2 hunks are then meaningless and must be re-derived as the author says.
- **`test_reanchor_58_r2_cas_runtime.py`: NOT in the author's list (S-4).** Its static driver table names the two
  finding doors §HELD deletes. 58's r3 (am-8: "CAS population enforced at the driver seam") will re-key that
  population, and the finding entries must move to `_run_guarded` in whichever wave lands last.
- **`test_fixwave_a28_63c_i_a.py`: NOT in the author's list (S-2, S-3).** G9's own re-open trigger ("a fifth
  governed leg") fired in a28 as well as a19/a19a. The a28b fold edits this very file (it is modified
  uncommitted in the shared tree now).
- `test_mcp_server.py` / `test_comms_footer.py` (author step 6) and the a19/a19a G9 hunks (step 9): as the author
  says. `git apply --check` of B's a19a hunk still passes on the live tree today.
- `_governed_contract.py` fold (step 4) and the A1 known-set (step 2): as the author says.
- **Also:** 64 amendment 7 (`6e42ed1`, landed AFTER the graded commit) renames the ledger title parameter to
  `title` and the identity kwarg to `subject=`. Every §HELD hunk that calls `report(..., caller=…)` and
  `_finding_fakes.arm_finding_identity`'s signature change with it (§AM7).

## §DUAL — P6b stage 2: my enumeration (§P6b-1) DIFFED against the author's §9

Stage 2 was run only after §P6b-1 was written and saved (see the file's first section). Row by row:

| my item | author's §9 row | verdict |
|---|---|---|
| D1 charset link-1b first | — (unchanged in the reference) | preserved; the reference keeps it FIRST. No row needed. **NOT A DEFECT** |
| D2 `items` foreign-param | — | preserved. **NOT A DEFECT** |
| D3 `created_by`/`actor` required at the tool | R1/R2 | matched |
| D4 body optional / kind default | — | preserved. **NOT A DEFECT** |
| D5 unknown-action list in tuple order | G5b (`set_scope` in dispatch order) | matched (dict order = served list) |
| D6 single-item errors surface; batches catch/abort | R12 (batch render) | matched in substance |
| D7 single-item transition render names the CALLER's actor | R12 covers the BATCH render only | **DUAL GAP (minor):** the single-item `_render_finding_transition(…, acting_name)` render has no §9 row, and no pin asserts its `by <name>` names the capability's agent (`TestProvenanceIsDerivedFromTheCapability` asserts the STORED event, not the served line). → folded into **MP-6** |
| **D8 R8(1): a finding WRITE with a supplied-but-unresolvable/ambiguous `agent=` SUCCEEDED and served a LOUD teaching footer** | **absent** (R3 covers only R8(2), the fallback) | **DUAL GAP:** the behaviour becomes a WHOLE-CALL `GovernedDenied` (`_resolve_identity`'s self-consistency check). The NEW world is pinned (`test_a_foreign_agent_name_is_denied_and_writes_nothing`). The OLD one was never pinned for findings: the footer suite's R8(1) typo/ambiguity legs (`test_the_teaching_names_a_REMEDY…`, `test_an_AMBIGUOUS_agent_is_taught…`) drive `lore_tasks` only. Consequence for the served surface: a fleet habit of passing a typo'd `agent=` on `lore_findings` goes from "write lands + teaching" to "write refused". That is a served-behaviour change, and it needs its §9 row (adjudicated: dropped-deliberately per am-2 §1 item 1). **Inventory row missing — NOT a missing pin** |
| D9 `agent=` description's "disclosed exception" sentence | R3 + the prose sweep | matched |
| L1 blank area/category refused pre-I/O; kind/subject/created_by unguarded | R4 | matched |
| **L2 `report(supersedes=X)` resolved UNFILTERED** | **absent** | **DUAL GAP:** changed to resolve through the caller's read filter. Pinned by NUMBER (`test_a_supersede_of_an_invisible_finding_is_byte_identical_to_a_nonexistent_one`), NOT by id → **MP-3** (WB17). Inventory row missing |
| L3 counter mint in the same txn | — (reference unchanged) | preserved |
| L4 uuid4 id, provenance shape, post-create re-read | — | preserved (+ `actor_agent` additive; new `ReportResult.scope`) |
| L5 edge validated BEFORE any write | — | CHANGED ORDER, no row: the reference authorizes first, then validates the edge. An unauthorized caller on an illegal edge now gets `GovernedDenied`, not `IllegalTransitionError`. Arguably correct (authorization before state disclosure); spec-silent on order. **Row missing; escalate the order as a one-line adjudication** |
| L6/L7 CAS + lost race (never success) | R6 | matched |
| L8 transport / exhausted-contention passthrough | R6/G2 | matched |
| L9 event shape, `note` only when not None | — | preserved; `actor_agent` added — see MP-6 for its reach |
| L10 annotate: blank note pre-I/O, any status, vanished → NotFound else re-raise | R7 | matched |
| L11 per-field provenance = caller free text | R1/R2 + am-2 §3 | matched |
| — | R9 (memory `_default_project_scope` moved) | author-only; I did not enumerate memory, because my stage-1 read was the findings surface. Fine |
| — | R10 / R14′ / R15 / R16 | author-only rows; each grounded in the diff (checked in `C.diff`). NOT A DEFECT |
| **(found in C.diff while grading R10)** `_migrate_memory_scope` now ALSO refuses owned-but-unscoped memory rows (via `_prepare_unowned_legacy_backfill`) | **absent** (R10 says "PRESERVED") | **DUAL GAP:** a NEW refusal path on memory's migrate. It is FK-2's substance, now RULED by am-7 §3 (derived set = {memory, finding}), so the behaviour is intended, but §9 must carry the row ("memory migrate gains the half-pair refusal"), and R10's "PRESERVED" is inaccurate for the memory leg |
| **(C.diff)** `migrate_governed`'s unsupported-table refusal prose changed (names `finding` as supported, "task lands at 64a") | absent | prose change on a served refusal; the P8d prose class. Row missing; no pin moves. **Minor** |

**Author rows I cannot ground in the code:** none. Every R-row maps to a hunk in `C.diff` or `B.diff`.

## §A — MISSING PINS (each with its CLASS, siblings, the wrong build it kills, and the P2 pair receipt)

Instruments (pasted verbatim in §INSTRUMENTS): `wrongbuild.py` (asserts every edit LANDED before a run),
`screen.sh` v2 (only rc 0/1 are verdicts), `run.sh` v2 (watchdog + rc in their own files),
`pairs.sh`, the specs file `wb_specs.json`, and the pins themselves (`test_adv64b_missing_pins.py`).
**Screen scope:** the 6 new contract files (156 tests), `-n 6`, on a `scratch_copy.sh` copy of the reference.
**Controls:** CTL0 (comment-only edit) over all 8 files → `1079 passed, 1 skipped, 0 failed` (the contract passes
the reference once S-1 is patched). CTL1 (the transition shell drops `plan.guard()`) → **KILLED** by
`test_a_rescope_between_the_gate_and_the_cas_is_a_governed_conflict` +
`test_the_executed_update_carries_the_plans_guard_and_bound`, so the screen can see a real break.
**Pairs:** every pin below was run GREEN on the reference (`fk9` = HEAD + §HELD: `12 passed, 1 failed`, the one
red being MP-1 on the reference itself, see MP-1) and RED on its wrong build (`pairs.sh`, restore byte-clean).

### MP-1 — `set_scope` on an INVISIBLE or NONEXISTENT row: the REFERENCE is itself the wrong build that survives
- **Test that should exist:** `set_scope` by id AND by number on (i) a row the caller cannot READ and (ii) an
  address that does not exist → `FindingNotFoundError`, byte-identical after address normalisation; row unchanged.
- **Defect it catches, measured on the author's own reference:** a NONEXISTENT id → `GovernedConflict: the guarded
  SET_SCOPE on finding:no_such_finding_id matched ZERO rows — a concurrent scope/owner change landed between the
  read and the guarded mutation`. An INVISIBLE id → `FindingNotFoundError`. That is an existence ORACLE (the two
  answers differ), and the served explanation is FALSE (nothing changed; nothing existed). Also, WB1 (drop the
  not-found mapping after a deny) → `GovernedDenied: member … may not SET_SCOPE finding:mp1_… — the row's
  owner/scope excludes it` (the oracle in the other direction). **SURVIVED the contract (155 passed).**
- **Pair:** reference RED (above) · WB1 RED · CORRECTED reference (set_scope resolves an id through the read
  filter, 2 lines) **GREEN — `168 passed, 1 skipped`** over the 13 pins + the 155 contract tests.
- **CLASS:** *∀ governed WRITE verb × ∀ address form (id, number) × {invisible, nonexistent}: the served bytes are
  identical.* The domain is the spec dict's True set (derived) × {id, number}.
  **SIBLINGS TRIED:** acknowledge/resolve/wontfix/annotate × {id, number} (the contract drives these: GREEN);
  `report(supersedes=)` × id (MP-3); set_scope × {id, number} (this). **SIBLINGS NOT TRIED:** the batch items (they
  route through the single-item verbs, so covered transitively; not driven with an invisible item).
  am-7 §4 now RULES this generated sweep ("pinned ∀ write verbs × {by id, by number} (generated)").

### MP-2 — a VISIBLE-but-unwritable row addressed by ID must be `GovernedDenied`, never a false not-found
- **Test:** `ag-a2` (alice's sibling, who can READ ag-a1's principal-private row) × {acknowledge, annotate,
  set_scope} BY ID → `GovernedDenied` (not a `FindingNotFoundError`); row unchanged.
- **Wrong build WB2** (`_authorize_write`: an id-addressed deny is always served as not-found): **SURVIVED
  (155 passed)**. Its served text, `no finding addressed by mp2_…`, is a falsehood a `get` of the same id
  contradicts.
- **Pair:** reference GREEN (3/3) · WB2 RED (2 of 3 params: `FindingNotFoundError: no finding addressed by
  ```mp2_436f71f63ed1```` for acknowledge and annotate; set_scope has its own mapping, so it stays GREEN).
- **CLASS:** *the visible-deny direction of FK-6, ∀ write verbs × ∀ address forms.* The contract's
  `_WRITE_CASES` sibling row is driven by NUMBER only. **SIBLINGS TRIED:** acknowledge, annotate, set_scope by id.
  **NOT TRIED:** resolve/wontfix by id (same `_transition` path as acknowledge).

### MP-3 — `report(supersedes=<invisible ID>)` ≡ nonexistent (the contract drives a NUMBER only)
- **Test:** bob supersedes alice's keep:A finding BY ID → the same bytes as superseding `no_such_finding_id`; no row.
- **Wrong build WB17** (supersedes resolved unfiltered for a str address — "ids are unguessable"): **SURVIVED
  (155 passed)**. It mints a successor LINKED to a row the reporter cannot see, which leaks existence and
  creates a cross-scope link.
- **Pair:** reference GREEN · WB17 RED (`Failed: DID NOT RAISE <class 'loremaster.findings.FindingNotFoundError'>`).
- **CLASS:** MP-1's class (∀ reads-inside-a-write × ∀ address forms). **SIBLINGS TRIED:** number (contract), id
  (this). **NOT TRIED:** none remaining for supersedes.

### MP-4 — the zero-row classifier must authorize the PASSED action; every DENY construction in the contract makes the row INVISIBLE, so READ-vs-WRITE is never discriminated
- **Test:** ag-a2 resolves ag-a1's keep:AB row; between the gate and the CAS the row is re-scoped to
  `principal-private` (still READABLE by the sibling, no longer WRITABLE) → `GovernedConflict`; status unchanged.
- **Wrong build WB3** (`classify_zero_row_cas` asks `authorize(subject, READ, …)`): **SURVIVED (155 passed)**,
  because all three contract constructions (substrate `rescoped` → keep:B for alice; governance TOCTOU and
  annotate → keep:A for bob) move the row out of READ reach too. On WB3 the served error is a falsehood:
  `IllegalTransitionError: lost a concurrent transition race … the status moved to 'acknowledged' before this
  'acknowledged' -> resolved transition could apply`. Nothing moved; the status is the same.
- **Pair:** reference GREEN · WB3 RED (that message).
- **CLASS:** *fixture discrimination: a ∀-action predicate evaluated only where READ and WRITE agree* (P2, the
  "arithmetic alignment" axis). **SIBLINGS TRIED:** WRITE with a readable-unwritable fresh row. **NOT TRIED:**
  SET_SCOPE / DELETE through the classifier (64b-i routes SET_SCOPE via `guarded_write`, not the classifier).

### MP-5 — LIFECYCLE: a revoked household member is refused on its NEXT call (no Subject outlives its call)
- **Test:** bob acknowledges an AB row (CONTROL: allowed); alice's keep-AB household drops bob
  (`KeepStore.remove_household_member`); bob's next acknowledge on another AB row → denied (not-found or
  `GovernedDenied`); row unchanged.
- **Wrong build WB4** (`_resolve_identity` memoises the `Subject` per capability, a plausible performance cache):
  **SURVIVED (155 passed)**, because no contract pin revokes anything between two calls.
- **Pair:** reference GREEN · WB4 RED (`DID NOT RAISE any of (GovernedDenied, FindingNotFoundError)`).
- **CLASS:** *every authorization input (keep membership, capability, agent status, principal status) is read
  per call; a degradation between calls takes effect on the next call* (the global lifecycle law).
  **SIBLINGS TRIED:** household removal. **NOT TRIED:** capability expiry, agent retire, principal disable. All
  ride the same `_resolve_subject`, so one generated lifecycle sweep over those four covers them.

### MP-6 — am-2 §3 `events[].actor_agent`, ∀ appended events (the contract pins it on `resolve` only)
- **Test:** × {acknowledge, wontfix, annotate}: the last event's `actor` is the derived name AND `actor_agent`
  is the agent RecordID; the single-item served transition line names the derived actor (D7).
- **Wrong build WB19** (annotate's event dict omits `actor_agent`; it is built separately from `_transition`'s):
  **SURVIVED (155 passed)**.
- **Pair:** reference GREEN (3/3) · WB19 RED on annotate (`{'action': 'annotate', 'actor': 'ag-b2', 'at': …,
  'note': 'n'}`, no `actor_agent`).
- **CLASS:** *per-field provenance ∀ event producers* — the producer set is the event-appending verbs (derive from
  the ledger's append-shell callers). **SIBLINGS TRIED:** acknowledge, wontfix, annotate. **NOT TRIED:** the batch
  items (route through `_transition`, covered transitively).

### MP-7 — R8's one-registry-read ceiling measured at the STORE seam on the REAL identity path
- **Test (restated after my own P0 catch):** count every statement touching the `agent` table during one governed
  write, with the REAL `_resolve_identity` (not the `_finding_fakes` arm); assert ≤ the RULED count.
- **Wrong build WB10** (the identity step adds a "still resolvable by name?" `get_agent`): **SURVIVED the 6 files
  AND `test_comms_footer.py` (`413 passed`)**. FK-8's 16 legs arm-replace `_resolve_identity`, and their spy wraps
  only `get_agent`, so the identity step's own reads are outside the pin's reach.
- **Pair:** my first MP-7 (method-name spies) was GREEN on the reference and RED on WB10
  (`{'_select_row': 2, 'get_agent': 1}`). **But that instrument had the same hidden-constant reach I am faulting.**
  The store-seam probe (`test_adv64b_r8_seam.py`, §INSTRUMENTS) measured the REFERENCE at **TWO agent-row
  reads per governed write**: `SELECT id, status, capability_expires_at, owner_principal AS owner_id, …`
  (stamp_owner's capability verify) and `SELECT * FROM type::record('agent', $id)` (`_resolve_identity`). am-7
  FK-8 states the path "resolves the agent row ONCE", and that is measured false.
- **CLASS:** *a budget pin's reach is a method name, not the seam* (P1c). **SIBLINGS TRIED:** get_agent,
  _select_row, the store seam. **NOT TRIED:** the task/claim dispatchers (64a).
- **RULING NEEDED (escalate):** does stamp_owner's capability-verify read count against R8's ceiling? If yes, the
  reference breaches R8 on every governed write (2 reads), and one projected read can serve both. If no, the pin's
  expected count is 2 and must say why.

### MP-8 — kickoff §6 rider (iv): EXACTLY ONE production identity-compare site (unimplemented)
- **Test:** AST over `server.py`: the comparisons `agent != own_row.name` / `session != own_row.session` occur at
  ONE site (am-2 §1 item 2 narrowed the compared set, it did not drop the rider).
- **Wrong build WB21** (the dispatcher passes `agent=None, session=None` to `_resolve_identity` and hand-rolls its
  OWN compare, a private copy wearing the shared name): **SURVIVED (155 passed)**. The contract's only structural
  pin, `test_the_dispatcher_routes_identity_through_the_one_helper`, checks the CALL SITE, which is
  routing-not-sharing.
- **Pair:** reference GREEN · WB21 RED (4 sites listed at lines 3793/3795/3897/3902).
- **CLASS:** *ROUTING IS NOT SHARING, for the identity policy.* **SIBLINGS NOT TRIED:** the `comms`/`tasks`/
  `claim_task` dispatchers (the rider's own domain; 63c/64a).

### MP-9 — FK-9: the TYPE_CHECKING declarations must carry the RULED SIGNATURE, not just the name
- **Test:** each ruled symbol is declared as a typed CALL with its ruled parameters (the idiom
  `_ruled_64b_i_report_takes_the_caller` already uses), plus a builder constraint to replace the runtime `Any`
  aliases with typed calls when the symbols land.
- **Defect it catches:** a builder landing a ruled NAME with a different SIGNATURE. Measured: the coherent
  wrong-shape build (`classify_zero_row_cas(verdict=)`, `authorize_guarded(columns=)`) is **mypy-identical to the
  reference** (29 errors / 13 files, none in the contract files), so the typecheck half of the bound discharges
  on it. Positive control: the one typed declaration reddens on a renamed kwarg.
- **CLASS:** *a declaration certifies existence, not the contract.* **SIBLINGS TRIED:** attribute refs (15),
  typed call (1). **NOT TRIED:** the converted suites' declared symbols (`acknowledge.caller`, `resolve.caller`).

### MP-10 — the finding migrate's `backfilled` must be MEASURED (am-27 FORK-1, ∀ legs) — see S-2
- **Test that should exist:** the a28 FORK-1 population for the finding leg (a28's own red says "add one"),
  carried in §HELD as a shared-test edit, plus a 64b-local twin.
- **Defect:** the reference returns `backfilled=unmigrated` (a pre-UPDATE count). The contract's F1-c
  (`backfilled == 3` on a quiescent store) cannot tell a pre-count from a measured count. The a28 pin can, and
  it reds on the reference.
- **CLASS:** *a served count describes the set the statement changed* (the TRUST doctrine's first clause).
  **SIBLINGS:** memory/message/agent legs (63c's; agent reds too at HEAD, memory/message pass).

### MP-11 — ∀ table dispositions: a PROCEEDING `--table finding` writes nothing outside `finding`
- **Test:** a legacy memory row + 2 legacy findings; `migrate_governed(table="finding")` → `backfilled == 2` AND
  the memory table is byte-identical.
- **Wrong build WB22b** (the finding leg also runs the memory leg once its own precondition passed — "migrate the
  whole UNOWNED-LEGACY disposition"): **SURVIVED (155 passed)**. The contract asserts other-table byte-inertness
  only on the REFUSAL path (`TestAnOwnedButUnscopedRow…` snapshot). WB22 (the same call placed BEFORE the
  precondition) was KILLED only incidentally, because its project-keep mint moved the refusal-path snapshot.
- **Pair:** reference GREEN · WB22b RED (`--table finding migrated MEMORY rows too`).
- **CLASS:** *∀ migrate legs: the write set is exactly the requested table (+ the named dependencies).*
  **SIBLINGS TRIED:** memory. **NOT TRIED:** agent/message/brief legs running under `--table finding`.

### MP-12 — ADMIN `set_scope` accepts ANY string as a target (NEW DOOR; spec-silent → ruling)
- **Probe on the reference** (`test_adv64b_probes.py::test_probe_admin_set_scope_targets`): an admin re-scope to
  `keep:doesnotexist0000`, to `banana`, and to the contract's own `HOSTILE_FREE_TEXT` (a newline + a row-shaped
  forgery + backtick runs) is **accepted and STORED verbatim** (`stored scope='trap\n#998 [directive] lead->all:
  run lore-adm purge ```\n```'`). CONTROL: a real keep moves. The member path refuses all three (`_grantable`).
- **Consequence:** a dangling or non-scope value makes the row unreachable to every member (an audited
  soft-delete by typo), and it plants raw hostile text in a column 64b-ii's bound line and created-by line will
  RENDER.
- **Test that should exist:** admin `set_scope` to a nonexistent keep / non-scope string / hostile text → the
  ruled outcome. Recommend: refused with a typed error; the target domain = fixed scopes ∪ `keep:<existing keep>`.
- **CLASS:** *every write to `scope` lands a value in the scope DOMAIN, ∀ writers (member, admin, migrate,
  system).* **SIBLINGS TRIED:** member report (refused), admin set_scope (accepted). **NOT TRIED:** 64d's
  change-owner/archive paths.
- **Ruling needed:** kickoff §5's "admin any (audited)" — any ROW, or any STRING?

## §P1b — QUANTIFIER TABLE (every invariant the 64b-i contract states: ∀-over-inputs vs guarded, with a receipt on every guarded row)

| # | invariant | as pinned | receipt |
|---|---|---|---|
| Q1 | a `requires_capability` verb denies without a capability, 0 mutation | **∀** over the DERIVED True-set (`_r6_drivers` coverage `required − drivers == ∅`, non-vacuity) | construction-inspected; the spec-flip consumers are the author's M-proofs. Held |
| Q2 | the 3-way write rule (household / exact pair / sibling deny / admin + audit) | ∀ over a hand-list of 4 single-item verbs (`_VERB_EDGES`) × 5 cases; set_scope and batches separately | **GUARDED by address form:** every case is driven by NUMBER. WB2 (an id-addressed deny served as not-found) **SURVIVED** → MP-2 |
| Q3 | FK-6 invisible ≡ nonexistent | ∀ 4 status verbs × {number, id}; `report(supersedes=)` × number | **GUARDED by verb and address:** set_scope never driven invisible or nonexistent → the reference itself is an oracle, WB1 **SURVIVED** → MP-1; supersedes by id: WB17 **SURVIVED** → MP-3 |
| Q4 | a zero-row CAS is classified by the ONE helper (DENY ⇒ conflict; else the ledger verdict) | 3 constructions + 4 substrate legs | **GUARDED by fixture:** every DENY construction makes the row invisible as well as unwritable. WB3 (authorize READ) **SURVIVED** → MP-4 |
| Q5 | authorization is per call (no stale Subject) | not stated | **NOT PINNED:** WB4 (cached Subject) **SURVIVED** → MP-5 |
| Q6 | provenance derived: `created_by`/`actor` = own name, `actor_agent` = agent id | report + resolve only | **GUARDED by verb:** WB19 (annotate drops `actor_agent`) **SURVIVED** → MP-6 |
| Q7 | report scope: default project; explicit ∈ grantable; hostile refused | ∀ 5 scope kinds (member) + hostile × {report, set_scope} (member) | ∀ for MEMBERS. **ADMIN unpinned:** the probe shows an admin stores any string → MP-12 (spec-silent) |
| Q8 | a supersede successor's scope is not inherited | AB predecessor vs project default (discriminating) | WB5 **KILLED** by `test_a_supersede_mints_a_row_in_the_superseders_scope_never_the_predecessors` |
| Q9 | migrate: legacy → project scope, NONE owner; the created_by guess door; idempotent; the golden WHERE | F1-c/f/g/h with discriminating fixtures | WB6 **KILLED** (golden pin); WB9 **KILLED** ([finding]+[memory] trap); WB13 **KILLED** (3 pins) |
| Q10 | migrate writes ONLY its table | on the REFUSAL path only (snapshot) | **GUARDED by path:** WB22b (proceed-path extra memory leg) **SURVIVED** → MP-11 |
| Q11 | migrate `backfilled` is the rows changed | `== 3` on a quiescent store | **GUARDED by fixture** (count ≡ changed there); 63c's a28 FORK-1 pin reds on the reference → MP-10 / S-2 |
| Q12 | R8: ≤1 registry read per call on every path | the footer's `get_agent` with the identity step ARMED away (16 legs) | **GUARDED by reach:** WB10 **SURVIVED** the 6 files + `test_comms_footer.py` (413 passed); the store seam shows 2 agent reads on the reference → MP-7 (+ ruling) |
| Q13 | ONE identity-compare site | the call site only | **GUARDED (routing ≠ sharing):** WB21 **SURVIVED** → MP-8 |
| Q14 | best-effort batches, per item | 3-item mixed batch × {resolve_many, acknowledge_many} | construction-inspected; the author's M-proofs. Held |
| Q15 | the guard is AND-bound at the top level (#417) | acknowledge's executed statement | CTL1 (guard dropped) **KILLED** by it and by the TOCTOU leg. Held |
| Q16 | the retired args are refused at the MCP layer naming the field; the exact served schema | exact-set allowlist | construction-inspected. Held |
| Q17 | read verbs refuse `capability=` (interim) | 3 verbs + CONTROL | construction-inspected. Held |
| Q18 | the F5 L1 whole-tree raw-site allowlist | ∀ DERIVED sites, both directions, non-vacuity | construction-inspected. Held (see P1c) |
| Q19 | the F5 L2 runtime observer: every observed write classifies | ∀ OBSERVED writes, over a HAND-LIST of 7 driven calls | **GUARDED by reach:** see P1c R2 (`acknowledge_many` is never driven) |

## §P1c — REACH TABLE (every guard / gate / scan the contract introduces or relies on)

| # | instrument | set it covers | reach | coverage checked? | effect or proxy | one source proven by mutation? | verdict / receipt · leg |
|---|---|---|---|---|---|---|---|
| R1 | F5 L1 `governed_table_raw_mutation_sites_in_tree(FINDING_TABLE)` vs `FINDING_TREE_ALLOWLIST` | every raw finding mutation site in the workspace | DERIVED (AST over the member roots) | YES, both ways (stray + ghost), non-vacuity asserted | proxy (a static site), paired with L2 | shared allowlist; author M-proofs | **SAFE** · construction-inspection |
| R2 | F5 L2 `observe_governed_table_writes` in `test_every_driven_write_verb_is_observed_and_classifies` | every finding write a governed verb performs | **HAND-LIST** of 7 literal calls; `expected` = 6 labels | coverage is checked against ITS OWN hand-list, not the spec dict's True set; `acknowledge_many` never driven | effect (observed writes) | — | **MISSING PIN (reach):** drive `∀ verb in required` (derived) with a driver table whose completeness is asserted (the R6 idiom), as `TestEveryCapabilityRequiredWriteVerbDeniesWithoutOne` already does · construction-inspection (the L1 scan backstops raw sites, so no wrong build was run) |
| R3 | R6 no-capability deny | ∀ True verbs | DERIVED from the spec dict | YES (`required − drivers == ∅`, non-vacuous) | effect (row unchanged) | — | **SAFE** |
| R4 | the verb partition `FINDING_WRITE_VERBS`/`READ_VERBS` | `_FINDING_ACTIONS` | hand-list | YES, exact equality both ways | — | **TWO hand-lists for ONE partition:** `test_comms_footer.FINDING_WRITE_ACTIONS` duplicates it, is checked on MEMBERSHIP only, and is not tied to the spec's `requires_capability` flag | **MISSING PIN (one source):** the footer's write/read split = the spec dict's True/False split (am-7 FK-8 rider now RULES "derived from the spec dict") · construction-inspection |
| R5 | FK-8 R8 ceiling (16 legs) | every registry read of a governed findings write | `get_agent` spy ONLY; identity step arm-replaced | no | proxy (one method name) | — | **MISSING PIN** → MP-7 · EMPIRICAL (WB10 survived; the store-seam probe measured 2 reads on the reference) |
| R6 | `test_the_dispatcher_routes_identity_through_the_one_helper` | the identity compare policy | the call site | — | proxy (the call) | **NO**: routing ≠ sharing | **MISSING PIN** → MP-8 · EMPIRICAL (WB21 survived) |
| R7 | `_R8_PROSE` sweep over `server.py` | stale R8(2) prose | a FORBIDDEN list of 4 tokens | no | text | — | **Spec-prescribed** (am-2 §4 mandates the bare-token sweep). Its known bound is a paraphrase. The schema exact-set pin (allowlist the safe) is the real guard for PARAMS; prose has no allowlist form. NOT A DEFECT, noted |
| R8 | `Resource(` only inside `resource_from_row` (#414/#415) | production `Resource` constructions | AST over production | allowlist of 1 | proxy (a site) | — | **SAFE** · construction-inspection |
| R9 | the #420 routing legs + the REVERSE pin (A3, shared) | enforced/observed verbs | derived from the handler (A3 v2, gated on an `action` param) | both directions | the marker | — | **SAFE** for 64b-i; the reverse pin is RED by design (#487) · SAT row 1 |
| R10 | the migrate golden-WHERE pin | the executed backfill statement | the executed statement (observed) | 1 statement | effect | — | **SAFE** · EMPIRICAL (WB6 KILLED) |
| R11 | the migrate byte-inert snapshot | other tables | `_BYTE_INERT_TABLES` = {finding, memory, agent, keep, member_of, principal}, a hand-list missing message/brief/to | refusal path only | effect | — | **MISSING PIN (path + reach)** → MP-11 · EMPIRICAL (WB22b survived) |
| R12 | the currency gate over bound `packet-64b-i-contract` | the 8 files' reds + 15+4 declared symbols | pytest: per FILE; typecheck: per symbol NAME | self-destruct legs 2–4 | name-existence proxy | — | **MISSING PIN (shape)** → MP-9 · EMPIRICAL (the mypy-identical wrong shape) |
| R13 | 63c's a28 ∀-legs pins (FORK-1, A2), relied on via G9 | ∀ governed migrate legs | DERIVED from the production legs / `_MIGRATE_TABLES` | yes | effect | — | **The instrument works, and it CATCHES the reference** (S-2, S-3). §HELD did not adjudicate it · EMPIRICAL |

**Legs run:** EMPIRICAL for R5, R6, R10, R11, R12, R13 (wrong builds or measured probes). CONSTRUCTION-INSPECTION
for R1, R2, R3, R4, R7, R8, R9.

## §P4/P7 — the author's claims, re-run (never relayed)
- **RED@HEAD** (P7): `base` (clean HEAD), the 6 new files, `-n 6`: **`119 failed, 36 passed, 1 skipped`**, exactly the
  author's §4 count. Reason census (`^E` lines): 31 × `UNBUILT … AppContext.findings has no capability=`, 15 ×
  `UNBUILT … report takes no caller=`, 7 × the migrate leg unsupported, 5+5+2 × `resource_from_row` /
  `classify_zero_row_cas` absent, 4 × `guarded_write` has no `target_scope=`, 3 × no `compose()`, 10 × the DD-3.c
  ASSERTs still on the store (right reason), 10 × the old DDL's engine rejection of raw blanks (the RIGHT reason
  for Leg A's baseline). **Four are NOT teaching messages:** 2 × `RuntimeError: No active context found` and 2 ×
  `RuntimeError: Failed to resolve dependency 'context' for findings`. These are the retired-arg MCP-layer legs:
  at HEAD the arg is still accepted, so the call dies on context resolution, not on a refusal. They are RED for the
  right underlying reason (not refused), but the served message does not say so. **Minor**: wrap the leg so an
  accepted retired arg fails with "UNBUILT: `created_by` is still in the served schema".
- **SAT**: see §SAT. "0 attributable" does NOT reproduce on HEAD (4 attributable defects).
- **Mutation proofs 19/19**: not re-run individually. My CTL1 is an independent re-derivation of the guard's
  mutation class (KILLED by the same two pins the author's M-proofs name), and my 14 wrong builds are
  independent of the author's 19.
- **FK-8 "the reference fixed the footer"**: confirmed for the FOOTER (0 `get_agent`). Not true of the identity
  path as a whole (MP-7).

## §AM7 — BOUNDARY: packet-64 amendment 7 (`6e42ed1`) landed AFTER the graded commit and rules the forks

The brief said "FK-1/2/6/7/8 pending: note, don't grade". They were RULED during this pass (`6e42ed1`,
`c383edd`). I do NOT grade `d8ea4ba` against rulings it could not have seen. I list, for the author's next
revision, the am-7 riders the graded contract does not yet carry. Each is a mechanical delta:
- **FK-1:** `subject=` is the ONE identity kwarg ∀ ledgers; the title becomes `title` at the Python seam. It moves
  `LEDGER_IDENTITY_KWARG`, the typed declaration in `test_findings_schema_64b.py` (`caller=`), every §HELD hunk
  calling `report(..., caller=…)`, and `_finding_fakes`. It also needs the new pins "no ledger signature carries
  `caller`" and "the kwarg equals memory's, derived by `inspect.signature`".
- **FK-2:** the half-pair domain is DERIVED from the migrate goldens (`owner_principal IS NONE`), not the hand
  pair `_UNOWNED_LEGACY_TABLES = (finding, memory)`; completeness both ways against `LegacyMapping`.
- **FK-6:** invisibility DERIVED from the ONE pre-read (`GovernedInvisible(GovernedDenied)`); `authorize_guarded`
  takes `row_id=` OR `number=`; the round-trip count is pinned ∀ write verbs × {id, number} (generated). The
  reference's `_visible_or_raise`-after-deny is a SECOND read, and `set_scope`/`report(supersedes=)`'s id paths
  are exactly MP-1/MP-3's doors. **am-7's generated sweep is MP-1 + MP-2 + MP-3's class**. My receipts show why it
  is needed: the reference, WB1, WB2 and WB17 all survive the graded contract.
- **FK-7:** `report_system` via `governed_exempt("calibration-drift", statement=…)`, an F5 exempt entry with a
  golden + effect predicate, one-producer reach, a LOUD non-fatal unprovisioned-keep path (pin: exactly one ERROR
  record, zero rows; CONTROL: provisioned → one row). The reference's `report_system` uses the LABEL
  `write_guard("finding_report_system")` and silently writes scope NONE when the keep is absent. Both contradict
  am-7.
- **FK-8:** the 16-leg verb axis DERIVED from the spec dict (R4 above).
- **FK-3:** a generated `None` (vanished) leg ∀ CAS verbs, and no verdict callable may raise a bare `KeyError`/
  `TypeError` on `None`.
- **FK-4:** `SET_SCOPE` with `target_scope=None` → a typed `ValueError` before any read (the reference's
  `guarded_write` default is `None` → the member branch is NoRows).
- am-7 §4 also FILES a memory sibling (content-derived memory ids + `GovernedDenied` on invisible = an
  oracle), assigned to the memory owner. Recorded, not graded.

## §P3 — branch reachability (the reference's NEW branches; the test that fails if each is deleted)
| branch (reference) | pin that reds if deleted |
|---|---|
| `findings()`: `capability` on a non-governed verb → foreign-param refusal | identity `test_a_capability_on_a_read_verb_is_a_foreign_param_teaching_refusal` |
| `findings()`: `scope` on a verb other than report/set_scope → refusal | **none found** (no pin drives `scope=` on e.g. `resolve`). Deleting it makes `scope` accepted-and-IGNORED on 7 verbs, the silent lie am-3 D-1b forbids for `capability`. **MISSING PIN (minor)**, same class as the capability interim pin |
| `_authorize_write`: GovernedDenied → visible check → NotFound | governance `_drive_invisible_cases` (by id) |
| `_authorize_write`: `plan.pre_read_row is None` → NotFound (nonexistent id) | governance `_drive_invisible_cases` `missing_by_id` |
| `set_scope`: GovernedDenied → visible check | **none** (MP-1) |
| `_run_guarded`: `refusal is None` → re-raise (annotate still writable after a zero-row) | **none found**: reachable only when the guard is false but `pdp.authorize` on the fresh row is true (a guard/PDP disagreement). Unreachable through the real entry point unless the guard's params go stale; say so rather than pin |
| `_lost_transition_verdict`: fresh edge legal → "lost a concurrent race" | governance `test_a_concurrent_status_winner…` reaches the ILLEGAL fresh-edge branch; the LEGAL fresh-edge branch is reached only on WB3 (MP-4's wrong-build text). **Unpinned on the correct build** (pre-existing at HEAD; noted) |
| `report_system` (FK-7) | G5a calibration fake only (FK-7 unruled at `d8ea4ba`; am-7 now rules it) |
| `_prepare_unowned_legacy_backfill`: `operator is None` → refusal | the 63b operator-ambiguity pins (shared) |
| `_prepare_unowned_legacy_backfill`: `offending` → refusal | migrate `test_the_trap_refuses…` (WB9 KILLED) |
| `_migrate_finding_scope`: `unmigrated == 0` early return | migrate `test_the_migrate_is_idempotent` (second run) |

## §P5 — can the doubles FAIL?
- `_finding_fakes.FakeFindingLedger` (the §HELD B shape): `report/acknowledge/resolve/wontfix/annotate/set_scope`
  ACCEPT `caller=` and IGNORE it; `set_scope` lands ANY target. **Its governance axis cannot fail, by
  construction.** Mitigated: every governance pin in the contract drives the REAL ledger through `finding_world`,
  and the fake serves only the footer and mcp_server render legs, which are not about authorization. **BOUND,
  unstated in the fake:** its docstring should say "governance is NOT modelled; do not pin authorization on the
  fake". Recommend one line plus a pin that no `test_findings_*_64b.py` imports `_finding_fakes`.
- `arm_finding_identity` REPLACES `_resolve_identity` (it ignores `agent`/`session`, by design, docstring-stated).
  So no footer-suite leg exercises the real identity step. That is exactly why WB10 survived (MP-7).

## §P6 — corpse sweep (BARE tokens `created_by` / `actor` / `never authenticated` / `disclosed exception`
within 6 lines of a findings dispatcher/ledger call, `awk` over the REFERENCE test tree; every hit a verdict)
- `test_mcp_server.py:2316`: a DUAL comment → **ok (comment)**.
- `test_mcp_server.py:7282`: a comms call's `created_by` (task side) → **ok (64a's surface)**.
- `test_mcp_server.py:7374/7395/7808/7811/7835/7854/7857/7880/7898/7901/7904/7966/7969/7972/8019/8022/8025/8070/8073/8076/8301`:
  LEDGER-level `finding_ledger.report(..., created_by="me")` on the FAKE ledger → **ok, "ledger-param, stands"**
  (am-2 §4). ⚠ am-7 FK-1 renames the positional TITLE only, so these keep working.
- `test_mcp_server.py:8306` `actor=value` → the M-4 render-site leg → **ok (render, not the dispatcher)**.
- `test_comms_footer.py:3941/4284`: `_seed_open_finding` / a fake-ledger report `created_by=` → **ok (ledger-param)**.
- `test_txn_contention.py:634/781` `created_by=_ACTOR` on the ledger (G3) → **ok (ledger-param)**.
- `_governed_contract.py:2389` `RETIRED_FINDING_IDENTITY_ARGS` → **ok (the retirement constant)**; `:2735` a
  docstring → **ok**.
- `test_findings_identity_64b.py:7/71/198/203/279`: docstrings describing the retirement → **ok**; `:351`
  `event.get("actor")` → **ok (the stored event key, not the served param)**.
- **No corpse found** (no green assertion pins the OLD served behaviour).

### MP-13 — `scope=` on a verb that takes none is accepted-and-IGNORED (the refusal branch is unpinned)
- **Test:** `lore_findings action=resolve|acknowledge|wontfix|annotate|query|get|chain_head … scope=<anything>`
  → the strict-param teaching refusal (`_comms_foreign_param_error`, owners = report/set_scope), with nothing
  written. Mirrors the contract's own `capability=` interim pin.
- **Wrong build WB23** (the branch deleted): **SURVIVED** the 6 files + `test_link5_render_containment.py` +
  `test_mcp_server.py` (`981 passed, 1 skipped`). NOT full-suite: WB23 is not in the combined run. No other file
  drives `scope=` on `lore_findings`, since it is new in 64b-i.
- **CLASS:** *∀ served param × ∀ verb that does not consume it → refused, never ignored* (am-3 D-1b's rule,
  stated for `capability`). **SIBLINGS TRIED:** `scope`. **NOT TRIED:** `note` on report, `items` (already pinned
  at HEAD), `status`/`kind`/`area` on write verbs (pre-existing surface; ask whether that is in 64b's scope).

### FULL-SUITE receipt for every survivor (the brief's rule)
COMBINED build = WB1 + WB2 + WB3 + WB4 + WB10 + WB17 + WB19 + WB21 + WB22b (10 edits, `combined.diff`, landing
asserted) on a `scratch_copy.sh` copy of the reference, full suite `-n 12`, `run.sh` v2: **`171 failed, 12079
passed, 63 skipped, 3 xfailed in 1350.16s`**, rc 1, no watchdog file. **The red set is node-for-node IDENTICAL to
the reference's 171** (`comm` both ways: 0 new, 0 removed). No test in the repository sees any of the nine.
(Bound: a combined run can in principle mask one build with another. The nine edits touch disjoint code paths,
and each was ALSO run alone against the 6 new files, so the individual 6-file receipts stand.)

---

## §INSTRUMENTS — pasted verbatim (scratch is disposable; these are the deliverable)

Self-caught P0 defects in MY instruments, both fixed before any verdict relied on them:
1. `run.sh` v1 appended its WATCHDOG line to the pytest log, and pytest's own `>` (O_TRUNC) stdout fd then
   OVERWROTE it. A killed run read like a clean one, with no receipt (the first baseline and the first WB1 screen
   were both killed at MemAvailable < 15 GB, while a concurrent mypy ran). v2 writes `.watchdog` and `.rc` files.
2. `screen.sh` v1 reported that killed WB1 run (rc 98) as "SURVIVES", a false survivor. v2: only rc 0/1 are
   verdicts; anything else is INVALID.
3. MP-7 v1 counted registry METHOD names, the same hidden-constant reach it was meant to fault. Replaced by the
   store-seam probe, which measured the reference at 2 agent reads.

#### `run.sh`
```bash
#!/usr/bin/env bash
# adversary-64b runner v2: run.sh <workdir> <logfile> <pytest args...>
# Runs `uv run pytest <args>` in <workdir> with a watchdog that kills THIS pytest's process TREE (by PID, never
# by pattern — #228) when host MemAvailable < 15 GB. Exit = pytest's; 98 = watchdog fired.
# v2 (self-caught P0 defect): v1 appended the WATCHDOG line to the pytest log, and pytest's own (O_TRUNC, not
# O_APPEND) stdout fd then OVERWROTE it — the kill receipt vanished and a killed run read as a clean one. The
# watchdog receipt and the exit code now live in their OWN files: <logfile>.watchdog and <logfile>.rc.
set -u
workdir="$1"; logfile="$2"; shift 2
rm -f "$logfile.watchdog" "$logfile.rc"
cd "$workdir" || exit 2
setsid uv run pytest "$@" >"$logfile" 2>&1 &
pid=$!
kill_tree() { local p=$1; for c in $(ps -o pid= --ppid "$p"); do kill_tree "$c"; done; kill -9 "$p" 2>/dev/null; }
while kill -0 "$pid" 2>/dev/null; do
    avail_kb=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
    if (( avail_kb < 15*1024*1024 )); then
        echo "WATCHDOG: MemAvailable ${avail_kb} kB < 15 GB — killed tree of $pid at $(date -Is)" >"$logfile.watchdog"
        kill_tree "$pid"; wait "$pid" 2>/dev/null; echo 98 >"$logfile.rc"; exit 98
    fi
    sleep 5
done
wait "$pid"; rc=$?
echo "$rc" >"$logfile.rc"
exit "$rc"
```

#### `screen.sh`
```bash
#!/usr/bin/env bash
# screen.sh <spec.json> <name>... — adversary-64b wrong-build screen (v2).
# For each wrong build: apply in $SC/wb (wrongbuild.py ASSERTS it landed), run the contract's 8 files (+ $EXTRA),
# record the FAILED node ids, restore the committed reference (git checkout) and assert the restore is clean.
# v2 (self-caught P0 defect): v1 reported a watchdog-KILLED run (rc=98) as "SURVIVES" — a false survivor. Now
# only rc=0 (all passed ⇒ SURVIVES) and rc=1 (≥1 failed ⇒ KILLED, with the ids) are verdicts; ANY other rc
# (98 watchdog, 2 interrupted, 3/4/5 internal/usage/no-tests) is INVALID and must be re-run.
set -u
SC=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/5b857dd0-ba19-43fb-bcd2-fb90d71794d3/scratchpad
TREE="${TREE:-$SC/wb}"
spec="$1"; shift
mkdir -p "$SC/wbruns"
FILES="$(cat "$SC/${FILELIST:-contract_files.txt}") ${EXTRA:-}"
for name in "$@"; do
    log="$SC/wbruns/$name.log"
    if ! python3 "$SC/wrongbuild.py" "$TREE" "$spec" "$name" >"$log.landing" 2>&1; then
        echo "$name: NOT LANDED — $(cat "$log.landing")"; continue
    fi
    "$SC/run.sh" "$TREE" "$log" -q -n "${WORKERS:-8}" -p no:cacheprovider -rf $FILES
    rc=$(cat "$log.rc" 2>/dev/null || echo missing)
    git -C "$TREE" checkout -q -- .
    dirty=$(git -C "$TREE" status --short --untracked-files=no | wc -l)
    summary=$(awk '/ passed| failed/' "$log" | tail -1)
    fails=$(awk '/^FAILED /{print $2}' "$log" | sort -u | tr '\n' ' ')
    case "$rc" in
        0) verdict="SURVIVES (0 failed)" ;;
        1) verdict="KILLED by: $fails" ;;
        *) verdict="INVALID RUN (rc=$rc $(cat "$log.watchdog" 2>/dev/null)) — re-run" ;;
    esac
    echo "$name: rc=$rc restore_dirty=$dirty | $summary | $verdict"
done
```

#### `wrongbuild.py`
```python
#!/usr/bin/env python3
"""adversary-64b wrong-build driver.

usage: wrongbuild.py <tree> <spec.json> <name>
spec.json: {"<name>": [{"file": rel, "old": str, "new": str, "count": 1}, ...], ...}

Applies every edit of <name> to <tree> (a committed scratch git tree), asserting each OLD occurs EXACTLY
`count` times BEFORE the edit and that the file's bytes CHANGED after (evidence the mutation LANDED — #194),
then prints `git diff --stat` as the landing receipt. Restore is `git -C <tree> checkout -- .` (the tree's
committed state IS the reference build). Exit 1 on any non-landing edit (nothing is left half-applied:
every file is restored before exiting).
"""
import json
import subprocess
import sys
from pathlib import Path

tree, spec_path, name = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
edits = json.loads(spec_path.read_text())[name]
originals: dict[Path, str] = {}
try:
    for edit in edits:
        path = tree / edit["file"]
        text = path.read_text()
        originals.setdefault(path, text)
        found = text.count(edit["old"])
        if found != edit.get("count", 1):
            raise SystemExit(f"NOT LANDED: {edit['file']}: old occurs {found}x, expected {edit.get('count', 1)}")
        new_text = text.replace(edit["old"], edit["new"])
        if new_text == text:
            raise SystemExit(f"NOT LANDED: {edit['file']}: replacement changed nothing")
        path.write_text(new_text)
except SystemExit:
    for path, text in originals.items():
        path.write_text(text)
    raise
print(subprocess.run(["git", "-C", str(tree), "diff", "--stat"], capture_output=True, text=True).stdout)
```

#### `pairs.sh`
```bash
#!/usr/bin/env bash
# pairs.sh <tree> <WB-spec-name> <pytest -k expression> — the RED leg of a P2 pair: apply the wrong build (landing
# asserted), drop in the scratch missing-pin file, run ONLY the named pin, restore the tree byte-clean.
set -u
SC=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/5b857dd0-ba19-43fb-bcd2-fb90d71794d3/scratchpad
tree="$1"; wb="$2"; expr="$3"
python3 "$SC/wrongbuild.py" "$tree" "$SC/wb_specs.json" "$wb" >/dev/null || { echo "$wb: NOT LANDED"; exit 1; }
cp "$SC/test_adv64b_missing_pins.py" "$tree/loremaster/tests/"
out=$(cd "$tree" && timeout 900 uv run pytest -q -p no:cacheprovider --tb=line -k "$expr" loremaster/tests/test_adv64b_missing_pins.py 2>&1)
rc=$?
git -C "$tree" checkout -q -- .; rm -f "$tree/loremaster/tests/test_adv64b_missing_pins.py"
echo "== $wb × [$expr] rc=$rc dirty=$(git -C "$tree" status --short | wc -l)"
echo "$out" | awk '/^E |^\/.*(Error|assert)|passed|failed/' | cut -c1-260 | head -6
```

#### `derive_symbols.py`
```python
"""adversary-64b FK-9 (b): DERIVE the new production symbols the 64b-i pins exercise; diff vs the declared set.

Run with a tree's interpreter: <tree>/.venv/bin/python derive_symbols.py <tree> <out.json>
Candidates = every identifier a test file NAMES (Attribute.attr + identifier-shaped str constants).
Owners = the production modules/classes the retrofit touches. Output: for each owner, the candidate names
that RESOLVE on it in this tree. Run on BASE (HEAD) and REF (HEAD+HELD); the difference REF−BASE, restricted
to names the tests name, IS the pin-required new-symbol set (derived — never read off the author's list).
"""
import ast
import importlib
import json
import re
import sys
from pathlib import Path

tree = Path(sys.argv[1])
sys.path.insert(0, str(tree / "loremaster" / "tests"))
FILES = [
    "test_findings_enforcement_64b.py", "test_findings_governance_64b.py", "test_findings_identity_64b.py",
    "test_findings_migrate_64b.py", "test_findings_schema_64b.py", "test_governed_substrate_64b.py",
    "test_mcp_server.py", "test_comms_footer.py",
]
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
names: set[str] = set()
for name in FILES:
    source = (Path(sys.argv[3]) / name).read_text()  # the CONTRACT's files (HEAD's committed copies)
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and IDENT.match(node.value):
            names.add(node.value)
        elif isinstance(node, ast.keyword) and node.arg:
            names.add(f"kw:{node.arg}")

OWNERS = {
    "loremaster.governed": None, "loremaster.server": None, "loremaster.findings": None,
    "loremaster.principals": None, "lorerunes.pdp": None, "loremaster.store.surreal_schema": None,
    "loremaster.audit": None,
}
CLASSES = {
    "FindingLedger": ("loremaster.findings", "FindingLedger"),
    "GuardedPlan": ("loremaster.governed", "GuardedPlan"),
    "AppContext": ("loremaster.server", "AppContext"),
    "ReportResult": ("loremaster.findings", "ReportResult"),
    "MigrateGovernedResult": ("loremaster.governed", "MigrateGovernedResult"),
}
out: dict[str, list[str]] = {}
import inspect
for module_name in OWNERS:
    module = importlib.import_module(module_name)
    out[module_name] = sorted(n for n in names if not n.startswith("kw:") and n in vars(module))
for label, (module_name, cls_name) in CLASSES.items():
    cls = getattr(importlib.import_module(module_name), cls_name)
    attrs = set(dir(cls)) | set(getattr(cls, "model_fields", {}) or {})
    out[label] = sorted(n for n in names if not n.startswith("kw:") and n in attrs)
# keyword parameters the tests pass, that a touched callable ACCEPTS in this tree
kw_owners = {
    "FindingLedger.report": ("loremaster.findings", "FindingLedger", "report"),
    "FindingLedger.acknowledge": ("loremaster.findings", "FindingLedger", "acknowledge"),
    "FindingLedger.resolve": ("loremaster.findings", "FindingLedger", "resolve"),
    "FindingLedger.annotate": ("loremaster.findings", "FindingLedger", "annotate"),
    "governed.authorize_guarded": ("loremaster.governed", None, "authorize_guarded"),
    "governed.guarded_write": ("loremaster.governed", None, "guarded_write"),
    "AppContext.findings": ("loremaster.server", "AppContext", "findings"),
}
for label, (module_name, cls_name, fn) in kw_owners.items():
    owner = importlib.import_module(module_name)
    if cls_name:
        owner = getattr(owner, cls_name)
    params = set(inspect.signature(getattr(owner, fn)).parameters)
    out[f"kw:{label}"] = sorted(n[3:] for n in names if n.startswith("kw:") and n[3:] in params)
Path(sys.argv[2]).write_text(json.dumps(out, indent=1))
```

#### `test_adv64b_missing_pins.py`
```python
"""adversary-64b — the MISSING PINS as runnable scratch tests (never committed to the repo; pasted verbatim in the
report §A). Each is proven as a PAIR: GREEN on the reference (HEAD + §HELD) and RED on its wrong build. Built
ONLY from names the contract's own substrate already exports (``_governed_contract`` after the §HELD fold)."""

from __future__ import annotations

import ast
import inspect
import re
from pathlib import Path
from typing import Any

import pytest
from _governed_contract import bare, finding_world, new_row_id, run
from surrealdb import RecordID
from test_findings_governance_64b import _inject_after_gate

from loremaster import governed, principals, server
from loremaster.findings import FindingNotFoundError, IllegalTransitionError

_MISSING_ID = "no_such_finding_id"


def _same_bytes(invisible: BaseException, missing: BaseException, row_id: str) -> None:
    left = str(invisible).replace(row_id, "<ID>")
    right = str(missing).replace(_MISSING_ID, "<ID>")
    assert left == right, f"invisible vs nonexistent differ (existence oracle): {left!r} vs {right!r}"


# MP-1 (WB1) — FK-6 ∀ WRITE verbs × ∀ address forms: set_scope was the one write verb never driven invisible.
async def test_MP1_set_scope_on_an_invisible_row_is_not_found_byte_identical_by_id_and_number(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    async with finding_world(monkeypatch, tmp_path) as world:
        row_id = await world.seed(row_id=new_row_id("mp1"), number=7801, owner="ag-a1", scope_key="A")
        before = await world.row(row_id)
        for address, missing_address in ((row_id, _MISSING_ID), (7801, 7899)):
            with pytest.raises(FindingNotFoundError) as invisible:
                await world.findings("ag-b1", action="set_scope", id_or_number=address, scope=world.scopes["B"])
            with pytest.raises(FindingNotFoundError) as missing:
                await world.findings(
                    "ag-b1", action="set_scope", id_or_number=missing_address, scope=world.scopes["B"]
                )
            if isinstance(address, str):
                _same_bytes(invisible.value, missing.value, row_id)
            else:
                assert str(invisible.value).replace("7801", "<N>") == str(missing.value).replace("7899", "<N>")
        assert await world.row(row_id) == before


# MP-2 (WB2) — the OTHER direction, ∀ address forms: a VISIBLE-but-unwritable row is a GovernedDenied, never a
# not-found that contradicts `get` (the sibling agent can READ ag-a1's principal-private row).
@pytest.mark.parametrize("verb", ["acknowledge", "annotate", "set_scope"])
async def test_MP2_a_visible_but_unwritable_row_by_ID_is_denied_never_not_found(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, verb: str
) -> None:
    async with finding_world(monkeypatch, tmp_path) as world:
        row_id = await world.seed(
            row_id=new_row_id("mp2"), number=7811, owner="ag-a1", scope_key="principal-private"
        )
        before = await world.row(row_id)
        extra: dict[str, Any] = {"note": "n"} if verb == "annotate" else {}
        if verb == "set_scope":
            extra = {"scope": "server"}
        with pytest.raises(governed.GovernedDenied) as denied:
            await world.findings("ag-a2", action=verb, id_or_number=row_id, **extra)
        assert not isinstance(denied.value, FindingNotFoundError)
        assert await world.row(row_id) == before


# MP-3 (WB17) — report(supersedes=) through the read filter ∀ address forms (the contract drives a NUMBER only).
async def test_MP3_supersedes_an_invisible_ID_is_not_found_byte_identical_and_writes_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    async with finding_world(monkeypatch, tmp_path) as world:
        hidden = await world.seed(row_id=new_row_id("mp3"), number=7821, owner="ag-a1", scope_key="A")
        kwargs = {"action": "report", "subject": "s", "body": "", "area": "a", "category": "c"}
        with pytest.raises(FindingNotFoundError) as invisible:
            await world.findings("ag-b1", supersedes=hidden, **kwargs)
        with pytest.raises(FindingNotFoundError) as missing:
            await world.findings("ag-b1", supersedes=_MISSING_ID, **kwargs)
        _same_bytes(invisible.value, missing.value, hidden)
        assert len(await run(world.admin_conn, "SELECT VALUE id FROM finding")) == 1, "a successor linked it"


# MP-4 (WB3) — the zero-row classifier's DENY branch is keyed on the PASSED action: a fresh row the subject can
# still READ but no longer WRITE (re-scoped to its principal's private scope) is a GovernedConflict, never the
# ledger's "lost a concurrent race … status moved to <same status>" (a false statement: nothing moved).
async def test_MP4_rescoped_to_readable_but_unwritable_is_a_governed_conflict(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    async with finding_world(monkeypatch, tmp_path) as world:
        row_id = await world.seed(
            row_id=new_row_id("mp4"), number=7831, owner="ag-a1", scope_key="AB", status="acknowledged"
        )
        _inject_after_gate(
            monkeypatch,
            world,
            "UPDATE type::record('finding', $id) SET scope = 'principal-private'",
            {"id": row_id},
        )
        with pytest.raises(governed.GovernedConflict):
            await world.findings("ag-a2", action="resolve", id_or_number=7831)
        assert (await world.row(row_id))["status"] == "acknowledged"


# MP-5 (WB4) — LIFECYCLE: a household revocation takes effect on the NEXT call (no Subject outlives its call).
async def test_MP5_a_revoked_household_member_is_refused_on_its_next_write(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    async with finding_world(monkeypatch, tmp_path) as world:
        first = await world.seed(row_id=new_row_id("mp5"), number=7841, owner="ag-a1", scope_key="AB")
        second = await world.seed(row_id=new_row_id("mp5"), number=7842, owner="ag-a1", scope_key="AB")
        await world.findings("ag-b1", action="acknowledge", id_or_number=7841)  # CONTROL: bob is householded
        assert (await world.row(first))["status"] == "acknowledged"
        keep_store = world.ctx._keep_store  # noqa: SLF001
        await keep_store.remove_household_member(
            keep_id=world.scopes["AB"].partition(":")[2], member_email=world.emails["bob"]
        )
        before = await world.row(second)
        with pytest.raises((governed.GovernedDenied, FindingNotFoundError)):
            await world.findings("ag-b1", action="acknowledge", id_or_number=7842)
        assert await world.row(second) == before, "a REVOKED member's write landed (a stale Subject authorized it)"


# MP-6 (WB19) — am-2 §3 ∀ appended events: every event-appending verb stamps `actor_agent` (the contract pins it
# on `resolve` only; `annotate` builds its own event dict).
@pytest.mark.parametrize(
    ("verb", "seed_status", "extra"),
    [("acknowledge", "open", {}), ("wontfix", "open", {}), ("annotate", "resolved", {"note": "n"})],
)
async def test_MP6_every_appended_event_carries_the_actor_agent_link(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, verb: str, seed_status: str, extra: dict[str, Any]
) -> None:
    async with finding_world(monkeypatch, tmp_path) as world:
        row_id = await world.seed(
            row_id=new_row_id("mp6"), number=7851, owner="ag-a1", scope_key="AB", status=seed_status
        )
        rendered = await world.findings("ag-b2", action=verb, id_or_number=7851, **extra)
        event = ((await world.row(row_id))["provenance"] or {})["events"][-1]
        assert event.get("actor") == "ag-b2", event
        assert str(event.get("actor_agent")) == str(RecordID("agent", world.agent_ids["ag-b2"])), event
        if verb != "annotate":
            assert "ag-b2" in rendered, f"the served transition line does not name the derived actor: {rendered!r}"


# MP-7 (WB10) — R8 on the REAL identity path: ONE agent-row read per governed write, counted at the store seam
# (every statement touching the `agent` table), not at one registry method name.
async def test_MP7_a_governed_write_reads_the_agent_row_at_most_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from loremaster.store import _txn  # noqa: PLC0415
    from _governed_contract import patch_shared_object_everywhere  # noqa: PLC0415

    async with finding_world(monkeypatch, tmp_path) as world:
        registry = world.ctx.agent_registry
        calls = {"get_agent": 0, "_select_row": 0}
        for name in list(calls):
            real = getattr(registry, name)

            def _wrap(real: Any = real, name: str = name) -> Any:
                async def _spy(*args: Any, **kwargs: Any) -> Any:
                    calls[name] += 1
                    return await real(*args, **kwargs)

                return _spy

            monkeypatch.setattr(registry, name, _wrap())
        await world.findings("ag-a1", action="report", subject="s", body="", area="a", category="c")
        assert calls["get_agent"] + calls["_select_row"] <= 1, calls


# MP-8 (WB21) — kickoff §6 rider (iv), as amended (am-2 §1 item 2): EXACTLY ONE production comparison of a
# supplied agent=/session= against the capability's own row — a second compare is a private copy.
def test_MP8_exactly_one_identity_compare_site_in_production() -> None:
    tree = ast.parse(Path(server.__file__).read_text(encoding="utf-8"))
    sites = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and any(isinstance(op, ast.NotEq) for op in node.ops):
            text = ast.unparse(node)
            if re.search(r"\b(agent|session)\b\s*!=\s*own_row\.(name|session)", text):
                sites.append((node.lineno, text))
    assert len(sites) == 2, f"expected ONE agent= and ONE session= compare (one site): {sites}"
    assert len({line // 25 for line, _ in sites}) == 1, f"the compares are not in one site: {sites}"


# MP-11 (WB22b) — ∀ table dispositions: a PROCEEDING --table finding writes NOTHING outside `finding` (+ the
# project-keep mint). The contract asserts byte-inertness of the OTHER tables on the REFUSAL path only.
async def test_MP11_migrate_finding_leaves_every_other_governed_table_byte_identical() -> None:
    from test_findings_migrate_64b import _migrate_world, _seed_legacy, _upgrade_finding_schema  # noqa: PLC0415
    from _governed_contract import frozen_asserted_finding_ddl, seed_memory_legacy  # noqa: PLC0415

    async with _migrate_world(frozen_asserted_finding_ddl()) as world:
        await seed_memory_legacy(world.connection, row_id="legacy_memory", dim=8)
        await _seed_legacy(world, 2)
        await _upgrade_finding_schema(world)
        before = await run(world.connection, "SELECT * FROM memory ORDER BY id")
        result = await world.migrate()
        assert not result.refused and result.backfilled == 2, result
        assert await run(world.connection, "SELECT * FROM memory ORDER BY id") == before, (
            "--table finding migrated MEMORY rows too"
        )
```

#### `test_adv64b_probes.py`
```python
"""adversary-64b PROBES on the reference build (scratch only — never in the repo). Each probe asks what the
REFERENCE does on a door the contract does not drive; the verdict is recorded, not asserted as a spec."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from _governed_contract import HOSTILE_FREE_TEXT, finding_world, new_row_id, run

from loremaster import governed


async def _try(world: Any, acting: str, **kwargs: Any) -> str:
    try:
        return f"OK: {await world.findings(acting, **kwargs)!r}"
    except Exception as error:  # noqa: BLE001 - a probe records whatever happens
        return f"{type(error).__name__}: {error}"


async def test_probe_admin_set_scope_targets(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """P-ADMIN-SCOPE: what an ADMIN set_scope lands for a nonexistent keep, a hostile string, and a
    non-scope string. CONTROL: a real keep lands (the probe can see a successful move)."""
    async with finding_world(monkeypatch, tmp_path) as world:
        targets = {
            "CONTROL-real-keep": world.scopes["AB"],
            "nonexistent-keep": "keep:doesnotexist0000",
            "hostile": HOSTILE_FREE_TEXT,
            "not-a-scope": "banana",
        }
        for index, (label, target) in enumerate(targets.items()):
            number = 7700 + index
            row_id = await world.seed(
                row_id=new_row_id("adm"), number=number, owner="ag-b1", scope_key="principal-private"
            )
            outcome = await _try(world, "ag-c1", action="set_scope", id_or_number=number, scope=target)
            landed = (await world.row(row_id))["scope"]
            print(f"PROBE admin set_scope [{label}] target={target!r} -> {outcome[:160]!r} | stored scope={landed!r}")


async def test_probe_member_report_explicit_scope_strings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """P-MEMBER-FIXED: which FIXED scopes a member may name on report (server / principal-private /
    agent-private) — the contract parametrises server + principal-private only."""
    async with finding_world(monkeypatch, tmp_path) as world:
        for target in ("agent-private", "server", "principal-private", "keep:doesnotexist0000"):
            outcome = await _try(world, "ag-a1", action="report", subject=f"s-{target}", body="", area="a",
                                 category="c", scope=target)
            print(f"PROBE member report scope={target!r} -> {outcome[:160]!r}")
        print("PROBE stored:", await run(world.admin_conn, "SELECT subject, scope FROM finding ORDER BY subject"))
```

#### `test_adv64b_r8_seam.py`
```python
"""adversary-64b probe: R8 measured at the STORE seam — every statement that touches the `agent` table during ONE
governed findings write (identity step + footer), whatever registry/stamp method issued it."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from _governed_contract import finding_world, patch_shared_object_everywhere

from loremaster.store import _txn

_AGENT = re.compile(r"\bagent\b")


async def test_probe_agent_statements_per_governed_write(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    async with finding_world(monkeypatch, tmp_path) as world:
        seen: list[str] = []
        for name in ("run_query", "execute_read_transaction", "execute_transaction"):
            real = getattr(_txn, name)

            def _wrap(real: Any = real, name: str = name) -> Any:
                async def _spy(*args: Any, **kwargs: Any) -> Any:
                    text = str(kwargs.get("statement", args[0] if args else ""))
                    if _AGENT.search(text):
                        seen.append(f"{name}: {' '.join(text.split())[:150]}")
                    return await real(*args, **kwargs)
                return _spy
            patch_shared_object_everywhere(monkeypatch, name, real, _wrap(), expect_in=("loremaster.store._txn",))
        world.act_as("ag-a1")  # warm nothing; the call below is measured
        seen.clear()
        await world.findings("ag-a1", action="report", subject="s", body="", area="a", category="c")
        for line in seen:
            print("AGENT-STMT", line)
        print("AGENT-STMT-COUNT", len(seen))
```

#### `wb_specs.json` (every wrong build, the controls, and the MP-1 fix — exact old/new strings)
```json
{
 "WB1_set_scope_oracle": [
  {
   "file": "loremaster/loremaster/findings.py",
   "old": "        except governed.GovernedDenied:\n            await self._visible_or_raise(finding_id, identity)\n            raise\n",
   "new": "        except governed.GovernedDenied:\n            raise\n"
  }
 ],
 "WB2_visible_deny_by_id_overhidden": [
  {
   "file": "loremaster/loremaster/findings.py",
   "old": "            # invisible \u21d2 not-found; visible \u21d2 the deny stands\n            await self._visible_or_raise(finding_id, caller)\n            raise\n",
   "new": "            # invisible \u21d2 not-found; visible \u21d2 the deny stands\n            if isinstance(id_or_number, str):\n                raise FindingNotFoundError(f\"no finding addressed by {render_attributed(id_or_number)}\") from None\n            await self._visible_or_raise(finding_id, caller)\n            raise\n"
  }
 ],
 "WB3_classifier_authorizes_READ": [
  {
   "file": "loremaster/loremaster/governed.py",
   "old": "    if not pdp.authorize(subject, action, resource_from_row(fresh)).allowed:\n        raise GovernedConflict(",
   "new": "    if not pdp.authorize(subject, pdp.Action.READ, resource_from_row(fresh)).allowed:\n        raise GovernedConflict("
  }
 ],
 "WB4_stale_capability_cache": [
  {
   "file": "loremaster/loremaster/server.py",
   "old": "        subject = await self._resolve_subject(capability)\n        registry = self.agent_registry\n",
   "new": "        subject = _ADV_SUBJECT_CACHE.get(capability) or await self._resolve_subject(capability)\n        _ADV_SUBJECT_CACHE[capability] = subject\n        registry = self.agent_registry\n"
  },
  {
   "file": "loremaster/loremaster/server.py",
   "old": "def _requires_capability(table: dict[str, Any], action: str) -> bool:\n",
   "new": "_ADV_SUBJECT_CACHE: dict[Any, Any] = {}\n\n\ndef _requires_capability(table: dict[str, Any], action: str) -> bool:\n"
  }
 ],
 "WB5_supersede_inherits_scope": [
  {
   "file": "loremaster/loremaster/findings.py",
   "old": "            target = await self._visible_or_raise(supersedes, identity)\n            supersedes_id = self._bare_id(target.get(_ID_KEY))\n",
   "new": "            target = await self._visible_or_raise(supersedes, identity)\n            supersedes_id = self._bare_id(target.get(_ID_KEY))\n            if scope is None and target.get(\"scope\"):\n                resolved_scope = str(target.get(\"scope\"))\n"
  }
 ],
 "WB6_migrate_where_not_self_guarding": [
  {
   "file": "loremaster/loremaster/principals.py",
   "old": "        f\"UPDATE {FINDING_TABLE} SET scope = $scope WHERE scope IS NONE AND owner_principal IS NONE\"",
   "new": "        f\"UPDATE {FINDING_TABLE} SET scope = $scope WHERE scope IS NONE\""
  }
 ],
 "WB9_half_pair_not_refused": [
  {
   "file": "loremaster/loremaster/principals.py",
   "old": "    if offending:\n",
   "new": "    if offending and False:\n"
  }
 ],
 "WB10_identity_step_spends_a_second_registry_read": [
  {
   "file": "loremaster/loremaster/server.py",
   "old": "        own_row = registry._row_to_agent(row)  # noqa: SLF001\n",
   "new": "        own_row = registry._row_to_agent(row)  # noqa: SLF001\n        await registry.get_agent(own_row.name, session=own_row.session)  # adv: 'still resolvable by name?'\n"
  }
 ],
 "WB13_half_pair_refuses_the_migrated_state_too": [
  {
   "file": "loremaster/loremaster/principals.py",
   "old": "statement=f\"SELECT VALUE id FROM {table} WHERE scope IS NONE AND owner_principal IS NOT NONE\",",
   "new": "statement=f\"SELECT VALUE id FROM {table} WHERE (scope IS NONE) != (owner_principal IS NONE)\","
  }
 ],
 "WB17_supersedes_by_id_resolved_unfiltered": [
  {
   "file": "loremaster/loremaster/findings.py",
   "old": "            target = await self._visible_or_raise(supersedes, identity)\n",
   "new": "            target = await (\n                self._resolve_or_raise(supersedes)\n                if isinstance(supersedes, str)\n                else self._visible_or_raise(supersedes, identity)\n            )\n"
  }
 ],
 "WB19_annotate_event_drops_actor_agent": [
  {
   "file": "loremaster/loremaster/findings.py",
   "old": "            _PROV_NOTE: note,\n            \"actor_agent\": str(RecordID(\"agent\", identity.agent_id)),\n",
   "new": "            _PROV_NOTE: note,\n"
  }
 ],
 "CTL0_noop_comment_edit": [
  {
   "file": "loremaster/loremaster/findings.py",
   "old": "    # -- the governed seams (64b-i) ----------------------------------------------------------------------\n",
   "new": "    # -- the governed seams (64b-i) ---------------------------------------------------------------------- (adv no-op)\n"
  }
 ],
 "CTL1_transition_shell_drops_the_guard": [
  {
   "file": "loremaster/loremaster/findings.py",
   "old": "        fragment = self._transition_fragment(finding_id, target, current, event, guard=plan.guard())\n",
   "new": "        fragment = self._transition_fragment(finding_id, target, current, event)\n"
  }
 ],
 "WB21_dispatcher_hand_rolls_a_second_identity_compare": [
  {
   "file": "loremaster/loremaster/server.py",
   "old": "            identity, own_row = await self._resolve_identity(capability, agent=agent, session=session)\n",
   "new": "            identity, own_row = await self._resolve_identity(capability, agent=None, session=None)\n            from loremaster.governed import GovernedDenied as _AdvDenied  # noqa: PLC0415\n            if agent is not None and agent != own_row.name:  # adv: a PRIVATE copy of the compare\n                raise _AdvDenied(\"agent= must name the agent your capability proves\")\n            if session is not None and session != own_row.session:\n                raise _AdvDenied(\"session= must name your capability's session\")\n"
  }
 ],
 "WB22_finding_leg_also_migrates_memory": [
  {
   "file": "loremaster/loremaster/principals.py",
   "old": "    from loremaster.governed import MigrateGovernedResult, governed_exempt\n\n    operator = await resolve_operator_principal(principal_store)  # the ONE ambiguity rule (63b pin)\n    prepared = await _prepare_unowned_legacy_backfill(\n        store, keep_store, principal_store, FINDING_TABLE, operator\n    )\n",
   "new": "    from loremaster.governed import MigrateGovernedResult, governed_exempt\n\n    await _migrate_memory_scope(store, keep_store, principal_store)  # adv: 'the whole UNOWNED-LEGACY disposition'\n    operator = await resolve_operator_principal(principal_store)  # the ONE ambiguity rule (63b pin)\n    prepared = await _prepare_unowned_legacy_backfill(\n        store, keep_store, principal_store, FINDING_TABLE, operator\n    )\n"
  }
 ],
 "WB22b_finding_leg_migrates_memory_after_its_precondition": [
  {
   "file": "loremaster/loremaster/principals.py",
   "old": "    if isinstance(prepared, MigrateGovernedResult):\n        return prepared\n    project_scope, unmigrated, already = prepared\n    if unmigrated == 0:\n        return MigrateGovernedResult(\n            table=FINDING_TABLE,\n",
   "new": "    if isinstance(prepared, MigrateGovernedResult):\n        return prepared\n    project_scope, unmigrated, already = prepared\n    await _migrate_memory_scope(store, keep_store, principal_store)  # adv: the whole disposition, AFTER the precondition\n    if unmigrated == 0:\n        return MigrateGovernedResult(\n            table=FINDING_TABLE,\n"
  }
 ],
 "COMBINED_SURVIVORS": [
  {
   "file": "loremaster/loremaster/findings.py",
   "old": "        except governed.GovernedDenied:\n            await self._visible_or_raise(finding_id, identity)\n            raise\n",
   "new": "        except governed.GovernedDenied:\n            raise\n"
  },
  {
   "file": "loremaster/loremaster/findings.py",
   "old": "            # invisible \u21d2 not-found; visible \u21d2 the deny stands\n            await self._visible_or_raise(finding_id, caller)\n            raise\n",
   "new": "            # invisible \u21d2 not-found; visible \u21d2 the deny stands\n            if isinstance(id_or_number, str):\n                raise FindingNotFoundError(f\"no finding addressed by {render_attributed(id_or_number)}\") from None\n            await self._visible_or_raise(finding_id, caller)\n            raise\n"
  },
  {
   "file": "loremaster/loremaster/governed.py",
   "old": "    if not pdp.authorize(subject, action, resource_from_row(fresh)).allowed:\n        raise GovernedConflict(",
   "new": "    if not pdp.authorize(subject, pdp.Action.READ, resource_from_row(fresh)).allowed:\n        raise GovernedConflict("
  },
  {
   "file": "loremaster/loremaster/server.py",
   "old": "        subject = await self._resolve_subject(capability)\n        registry = self.agent_registry\n",
   "new": "        subject = _ADV_SUBJECT_CACHE.get(capability) or await self._resolve_subject(capability)\n        _ADV_SUBJECT_CACHE[capability] = subject\n        registry = self.agent_registry\n"
  },
  {
   "file": "loremaster/loremaster/server.py",
   "old": "def _requires_capability(table: dict[str, Any], action: str) -> bool:\n",
   "new": "_ADV_SUBJECT_CACHE: dict[Any, Any] = {}\n\n\ndef _requires_capability(table: dict[str, Any], action: str) -> bool:\n"
  },
  {
   "file": "loremaster/loremaster/server.py",
   "old": "        own_row = registry._row_to_agent(row)  # noqa: SLF001\n",
   "new": "        own_row = registry._row_to_agent(row)  # noqa: SLF001\n        await registry.get_agent(own_row.name, session=own_row.session)  # adv: 'still resolvable by name?'\n"
  },
  {
   "file": "loremaster/loremaster/findings.py",
   "old": "            target = await self._visible_or_raise(supersedes, identity)\n",
   "new": "            target = await (\n                self._resolve_or_raise(supersedes)\n                if isinstance(supersedes, str)\n                else self._visible_or_raise(supersedes, identity)\n            )\n"
  },
  {
   "file": "loremaster/loremaster/findings.py",
   "old": "            _PROV_NOTE: note,\n            \"actor_agent\": str(RecordID(\"agent\", identity.agent_id)),\n",
   "new": "            _PROV_NOTE: note,\n"
  },
  {
   "file": "loremaster/loremaster/server.py",
   "old": "            identity, own_row = await self._resolve_identity(capability, agent=agent, session=session)\n",
   "new": "            identity, own_row = await self._resolve_identity(capability, agent=None, session=None)\n            from loremaster.governed import GovernedDenied as _AdvDenied  # noqa: PLC0415\n            if agent is not None and agent != own_row.name:  # adv: a PRIVATE copy of the compare\n                raise _AdvDenied(\"agent= must name the agent your capability proves\")\n            if session is not None and session != own_row.session:\n                raise _AdvDenied(\"session= must name your capability's session\")\n"
  },
  {
   "file": "loremaster/loremaster/principals.py",
   "old": "    if isinstance(prepared, MigrateGovernedResult):\n        return prepared\n    project_scope, unmigrated, already = prepared\n    if unmigrated == 0:\n        return MigrateGovernedResult(\n            table=FINDING_TABLE,\n",
   "new": "    if isinstance(prepared, MigrateGovernedResult):\n        return prepared\n    project_scope, unmigrated, already = prepared\n    await _migrate_memory_scope(store, keep_store, principal_store)  # adv: the whole disposition, AFTER the precondition\n    if unmigrated == 0:\n        return MigrateGovernedResult(\n            table=FINDING_TABLE,\n"
  }
 ],
 "FIX_MP1_set_scope_resolves_through_the_filter": [
  {
   "file": "loremaster/loremaster/findings.py",
   "old": "        identity = self._require_identity(caller)\n        if isinstance(id_or_number, int) and not isinstance(id_or_number, bool):\n            finding_id = self._bare_id((await self._visible_or_raise(id_or_number, identity)).get(_ID_KEY))\n        else:\n            finding_id = str(id_or_number)\n        try:\n            await governed.guarded_write(\n",
   "new": "        identity = self._require_identity(caller)\n        if isinstance(id_or_number, int) and not isinstance(id_or_number, bool):\n            finding_id = self._bare_id((await self._visible_or_raise(id_or_number, identity)).get(_ID_KEY))\n        else:  # adv FIX: an id resolves through the read filter too (invisible \u2261 nonexistent)\n            finding_id = self._bare_id((await self._visible_or_raise(id_or_number, identity)).get(_ID_KEY))\n        try:\n            await governed.guarded_write(\n"
  }
 ],
 "WB23_scope_accepted_and_ignored_on_other_verbs": [
  {
   "file": "loremaster/loremaster/server.py",
   "old": "        if scope is not None and action not in (_FINDING_ACTION_REPORT, _FINDING_ACTION_SET_SCOPE):\n",
   "new": "        if False and scope is not None and action not in (_FINDING_ACTION_REPORT, _FINDING_ACTION_SET_SCOPE):\n"
  }
 ]
}```

#### `fk9_wrongshape.diff` (FK-9 (a): the mypy-identical wrong-shape build)
```diff
diff --git a/loremaster/loremaster/findings.py b/loremaster/loremaster/findings.py
index d9df641..0ec2393 100644
--- a/loremaster/loremaster/findings.py
+++ b/loremaster/loremaster/findings.py
@@ -1170,7 +1170,7 @@ class FindingLedger:
         audit iff required, in ONE transaction; a zero-row rollback is classified by the ONE helper."""
         identity = self._require_identity(caller)
         finding_id, plan = await self._authorize_write(
-            id_or_number, identity, pdp.Action.WRITE, projection=(_COL_STATUS, _COL_PROVENANCE)
+            id_or_number, identity, pdp.Action.WRITE, columns=(_COL_STATUS, _COL_PROVENANCE)
         )
         current = str((plan.pre_read_row or {}).get(_COL_STATUS))
         self._validate_transition(finding_id, current, target)
@@ -1223,7 +1223,7 @@ class FindingLedger:
                     row_id=finding_id,
                     subject=identity,
                     action=pdp.Action.WRITE,
-                    ledger_verdict=verdict,
+                    verdict=verdict,
                 )
                 if refusal is None:  # the pre-64b behaviour: nothing to classify — the store error stands
                     raise
diff --git a/loremaster/loremaster/governed.py b/loremaster/loremaster/governed.py
index 02181a4..b5e7d93 100644
--- a/loremaster/loremaster/governed.py
+++ b/loremaster/loremaster/governed.py
@@ -479,7 +479,7 @@ async def authorize_guarded(
     row_id: str,
     audit: Any,
     store: StoreHandle,
-    projection: tuple[str, ...] = (),
+    columns: tuple[str, ...] = (),
     target_scope: str | None = None,
 ) -> GuardedPlan:
     """The PYTHON authorization leg split out of :func:`guarded_write` (design §2.2 step 1).
@@ -500,7 +500,7 @@ async def authorize_guarded(
         url=store.url,
         noun="governed pre-read",
         label="governed.pre_read.rejected",
-        statement=f"SELECT {', '.join(_pre_read_columns(projection))} FROM type::record('{table}', $gw_id)",
+        statement=f"SELECT {', '.join(_pre_read_columns(columns))} FROM type::record('{table}', $gw_id)",
         params={"gw_id": row_id},
         logger=logger,
     )
@@ -678,7 +678,7 @@ async def classify_zero_row_cas[VerdictT](
     row_id: str,
     subject: Subject,
     action: Action,
-    ledger_verdict: Callable[[dict[str, Any] | None], VerdictT],
+    verdict: Callable[[dict[str, Any] | None], VerdictT],
 ) -> VerdictT:
     """THE one zero-row CAS classifier (#407; 64b kickoff §4.3 item 4). After a guarded CAS matched zero
     rows (the store rolled the transaction back): re-read the FRESH row through the injected driver; if the
@@ -699,13 +699,13 @@ async def classify_zero_row_cas[VerdictT](
     rows = result if isinstance(result, list) else []
     fresh = rows[0] if rows and isinstance(rows[0], dict) else None
     if fresh is None:
-        return ledger_verdict(None)
+        return verdict(None)
     if not pdp.authorize(subject, action, resource_from_row(fresh)).allowed:
         raise GovernedConflict(
             f"the guarded {action.value} on {table}:{row_id} matched ZERO rows — its owner/scope changed "
             "between the authorization and the write (a concurrent re-scope or re-own); nothing was written"
         )
-    return ledger_verdict(fresh)
+    return verdict(fresh)
 
 
 def _bare(record_id: Any) -> str:
```

## §FIXTURES — which fixtures cannot tell right from wrong (with the perturbation and its correct-build control)
| fixture | blind to | perturbation | wrong build stays green? | correct build green? |
|---|---|---|---|---|
| every zero-row DENY construction (substrate `rescoped`→keep:B for alice; governance TOCTOU + annotate → keep:A for bob) | READ-vs-WRITE in the classifier | re-scope to `principal-private` for alice's SIBLING (readable, unwritable) → MP-4 | WB3: green on the contract, RED on MP-4 | reference GREEN on MP-4 |
| `_WRITE_CASES` / `_INVISIBLE_CASES` address forms | id vs number on the visible-deny row; set_scope and supersedes invisible | address by ID; drive set_scope/supersedes invisible → MP-1/2/3 | WB1/WB2/WB17 green on the contract, RED on MP-1/2/3 | reference GREEN on MP-2/3; MP-1 GREEN only on the CORRECTED reference (168 passed) |
| migrate F1-c `backfilled == 3` on a quiescent store | pre-count vs measured count | 63c a28's FORK-1 population (count ≠ changed) | the REFERENCE (pre-count) is green on F1-c, RED on a28 FORK-1 | — (no corrected leg built; the author owes the measured count) |
| migrate worlds with no legacy memory row on the PROCEED path | cross-table writes | a legacy memory row + a proceeding `--table finding` → MP-11 | WB22b green on the contract, RED on MP-11 | reference GREEN |
| `finding_world` calls, one per capability | a Subject cached across calls | revoke bob's household between two calls → MP-5 | WB4 green on the contract, RED on MP-5 | reference GREEN |
| the footer harness `arm_finding_identity` | the REAL identity step's reads | real AppContext + a store-seam count → MP-7 | WB10 green on 413 footer+contract tests | reference measured at 2 agent reads (ruling needed) |

## §RESIDUALS — every item, an individual verdict
1. **S-1** fold/import mismatch (`test_mcp_server.py:2297`) — SAT DEFECT; one-line fix in §HELD (A2 must repoint
   the converted suite's import too).
2. **S-2** a28 FORK-1 `[_migrate_finding_scope]` — SAT DEFECT + MP-10.
3. **S-3** a28 A2 `[finding-*]` ×3: the finding leg is not fail-closed on a forged `INFO FOR DB` — SAT DEFECT. The
   64b build must route the finding leg through the same precondition read as 63c's legs.
4. **S-4** 58-r2 `cas_runtime` `[findings.py::annotate|_transition]` stale — SAT DEFECT; add it to §HELD's
   re-verification list beside step 11.
5. Live-tree collision on `test_retry_seam.py` (part B) — already anticipated by the author (step 11). NOT A
   DEFECT; re-measured today on the live tree.
6. DUAL rows missing from §9 (D8 R8(1) typo'd `agent=` → whole-call deny; L2 supersedes filtered; L5 order; the
   memory migrate's new half-pair refusal; the `migrate_governed` unsupported-table prose) — inventory gaps; add
   rows. The L5 order needs a one-line adjudication (decisions-needed 3).
7. P3 `_run_guarded` `refusal is None → raise` — reachable only on a guard/PDP disagreement; unreachable through
   the real entry point. NOT A DEFECT; say so in the code comment.
8. P3 `_lost_transition_verdict`'s legal-fresh-edge branch — unpinned on a correct build (pre-existing at HEAD);
   reachable only on a WB3-shaped classifier. Noted.
9. P5 the fake ledger's governance axis cannot fail — BOUND; state it in the fake's docstring + pin that no 64b
   governance file imports `_finding_fakes`.
10. RED@HEAD: 4 retired-arg legs red on a `RuntimeError` (context resolution) rather than a teaching message — minor.
11. #461 file-partition: bound `packet-64b-i-contract` adjudicates EVERY pytest red in `test_mcp_server.py` /
    `test_comms_footer.py` while any of their 4 declared symbols is missing. The author states the bound; its re-open
    trigger ("the day either file gains an unrelated red") has NO instrument measuring it. A trigger nobody measures
    is a hope. The fix belongs to the GATE (node-id ownership), not to this contract → FLAG to the gate owner.
12. MP-12 admin `set_scope` domain — NEW DOOR, ruling needed (decisions-needed 2).
13. MP-7 R8 on the identity path — ruling needed (decisions-needed 1).
14. am-7 riders the graded contract does not carry (§AM7) — the author's next revision; not graded.
15. Lore friction: `lore_search` served a bare store-uuid error once (retry succeeded) — filed **#511**.
16. The reference's `report_system` (FK-7) writes scope NONE silently when the project keep is absent and uses a
    LABEL, not the ruled exempt. It contradicts am-7 §1 and is not part of the graded contract (FK-7 was unruled at
    `d8ea4ba`). Noted for the author.

## VERDICT

**CONTRACT INSUFFICIENT.**

Ten wrong builds survive the 156-test contract, and so does the author's own reference. Nine of them, run together,
survive the ENTIRE suite (171/12079, node-identical to the reference). The tenth, WB23, survives the 981 tests
that could see it. Each missing pin in §A is a test
the author can write now, and each is proven as a pair here: RED on its wrong build, GREEN on the reference (MP-1 on
a corrected reference). The satisfiability receipt does not reproduce on the right base (4 attributable SAT
defects). The FK-9 ownership shape is sound for ownership, but it certifies names, not signatures (MP-9).
Classes, not instances: MP-1/2/3 are ONE generated sweep (∀ write verb × ∀ address × {invisible, nonexistent,
visible-denied}), which am-7 §4 has now ruled. MP-5 is ONE lifecycle sweep over the per-call authorization inputs.
MP-6 is ONE sweep over the event producers. MP-7/MP-8/R2/R4 are ONE reach rule: count at the seam, derive from the
spec dict.
