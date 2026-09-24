# Packet 63c — ruling amendment 5 (sidecar-63c-2, 2026-09-24): r3 forks FORK-A / FORK-B / FORK-C

Amends amendment-4 §MP-D point 1 (`2c30150`) and amendment-3 F-2 (`e6bedd1`). Rules the forks in
`REPORT-contract-63c-i-a-r3.md` §FORKS (uncommitted at repo root at ruling time; read in place at HEAD
`8915faa`, r3a `11cbfb2` committed, r3b in the working tree). Directive: `REPORT-lead-63c.md@8915faa`
"LEAD DIRECTIVE TO sidecar-63c-2 — TASK 5"; lore's MCP is still disconnected — this pass is `Read`/`sed`/
`awk`/`git diff`, said so per the dogfood protocol; the committed doc is the receipt.

Two of the three forks trace to MY text: FORK-A to an amendment-4 parenthetical that pointed opposite its
own sentence, FORK-C to an amendment-3 claim I reasoned instead of measured. Both are corrected here, in
§E, and stand as errata against my earlier docs (never rewritten).

## FORK-A — the ⊇ pin's direction: reading (c) PIN-THE-MISS, RATIFIED (amendment-4 MP-D point 1 corrected)
- **What I wrote and why it forked:** *"a pin that this derived set ⊇ `ALL_DDL_GENERATORS` (RED the day
  the scaffold's hand-list and the module disagree — today it names the two unswept emitters)"*. The
  literal `derived ⊇ hand-list` is GREEN today and names nothing; the parenthetical wants
  `hand-list ⊇ derived`, which is RED on a CORRECT build — unsatisfiable for the SAT receipt and
  RED_ORPHANED under currency (the gap is the scaffold's, not 63c's). I wrote a pin and its opposite in one
  sentence. The author was right to stop.
- **Ruling:** reading (c), as implemented — assert the composition-aware gap set is EXACTLY
  `{generate_lease_ddl, generate_floor_calibration_ddl}` (a generator is "unswept" iff its emitted
  statements ⊄ the union of the hand-list's emissions, so the three emitters `generate_ddl` composes count
  as covered), with the KNOWN BOUND message (*"if you closed it deliberately, delete this set and say
  so"*). GREEN today; RED when the gap GROWS (a third unswept emitter) or CLOSES (forcing the deliberate
  deletion). This is CLAUDE.md's "pin the miss" verbatim, and it is the ONLY reading that is both
  satisfiable and load-bearing.
- **The (a) leg (`derived ⊇ hand-list`)** is vacuous-by-import: the scaffold imports every hand-listed
  generator by name, so a generator the module lost is an `ImportError` before any pin runs. The author
  may keep it (it is free) but its docstring must not claim it detects anything the import does not.
- **Decision point for the bound (the deferral law):** owner = the scaffold finding the lead files when
  lore returns (amendment-4 §E); trigger = that finding's fix (the scaffold derives its own set via
  `schema_ddl_generators()`), whose commit deletes this exact-set pin and says so. Until then the two
  names live in the pin's source, read on every edit, not in a run log nobody reads.

## FORK-B — the generator-discovery lift + the two folds + `_rebind_everywhere`: RATIFIED, with ONE rider
- **Ratified:** lifting `schema_ddl_generators()` / `emit_schema_ddl()` / `emitted_schema_ddl()` into
  `_enforced_relations_scaffold.py` and re-pointing `test_ddl_write_target_coverage_124._ddl_generators` +
  `_emit` and `test_principal_keys_schema._all_schema_ddl` to delegate is ONE IMPLEMENTATION working as
  written (*"escalate, don't write copy #2"* — the author escalated AND had the address); writing item 7's
  derivation inside `_governed_contract` would have been copy #3. In the writable set, found in-session,
  proven by mutation (GD1/GD2: perturb the shared derivation → every consumer's pins red; the GD1 extra red
  was a third consumer moving — the safe direction). Extending the pre-existing identity-alone loop in
  `_logging_fixtures._rebind_everywhere` into the ONE binding-finder both instruments call (IM3) is the
  same law: a fourth copy no amendment named, found and folded rather than cloned.
- **Rider — one semantic NARROWING the fold introduced, restore it (read from the diff, not the report):**
  both retired copies passed `dim` whenever the parameter EXISTED (`"dim" in
  inspect.signature(generator).parameters`); the lifted `emit_schema_ddl` passes it only when the
  parameter is REQUIRED (`default is empty`). Identical today (`generate_ddl` and `generate_memory_ddl`
  both take a required `dim`), but a future `dim: int = 8` would be emitted at its default and
  `test_principal_keys_schema`'s `NONDEFAULT_DIM` — whose whole point is proving the width is THREADED —
  would silently stop threading. Restore "pass `dim` whenever present"; keep fail-closed for any OTHER
  required parameter (that part is an improvement over both copies and stays). State the DUAL row.
- **Bound, to be named in the helper's docstring:** membership is `inspect.isfunction` — a generator
  implemented as a callable object or `functools.partial` named `generate_*_ddl` is NOT a function and
  does not join (the old `dir()+callable` copy would have taken it). Allowlist-the-safe by the naming
  contract is the right rule; the shape bound is stated so the day someone ships a partial it is met
  deliberately.
- **Classification:** NON-GATING (test tree; verdict-neutral at HEAD by the author's measurement).

## FORK-C — amendment-3 F-2's HEAD-RED premise was FALSE; reading (b) GUARDED read, RATIFIED with riders
- **My error, measured by the author:** I claimed *"the RED population does not grow: every fake-driven
  register is already HEAD-RED on the `session_keep_id` seam."* False — a TOKENLESS `(None, None)`
  register is legal at HEAD and never touches that seam, so an unguarded call-time import reds every one
  of them: 55 → 287 over the 11 `_comms_fakes` consumers, **232 HEAD-green tests red** for the duration of
  the build. That is a reasoning claim I filed as a measurement; the askable form I skipped: *"which
  callers reach this line WITHOUT the seam I am counting on?"*
- **Ruling:** reading (b) — the fake's identity leg reads `lorerunes.is_legal_identifier` at call time
  under a guard that is inert ONLY on `ImportError` (the `is_blank` leg is unguarded: it exists at HEAD).
  Nothing the contract relies on is hidden: the F-2 mirror pin's identity legs stay RED at HEAD for a
  legible reason (the fake does not refuse), the parity matrix's hostile-name rows red the same way, and
  every real-registry MOVE pin imports the symbol directly, so a later deletion reds those first.
  Reading (a) would commit 232 signal-less reds to `feat/surreal-unification` — RED_ADJUDICATED in name,
  noise in fact — for a one-line accommodation.
- **Riders — and pin it like this:**
  1. The guard lives in ONE one-line helper on the fake (`_shared_identifier_predicate()` or the
     author's `_refuse_what_the_writer_refuses` seam), narrow `except ImportError` (never `Exception`),
     docstring naming it a HEAD-RED ACCOMMODATION with its removal trigger.
  2. **A conditional pin makes forgetting the deletion RED:** once `lorerunes.is_legal_identifier`
     exists, `_comms_fakes.py`'s source contains no `except ImportError` — GREEN at HEAD (the symbol is
     absent, the guard is legitimate), RED the moment the build lands with the guard still present.
  3. **Who deletes it, so the builder is not trapped by a red it cannot fix:** the lead's builder brief
     grants the builder exactly ONE test-tree edit — deleting that guard line in `_comms_fakes.py` in its
     REFACTOR step (a fake is substrate, not a pin; builder ≠ grader still holds). If the lead prefers the
     contract author to do it post-build, then pin 2 is RED_ADJUDICATED(owner = r3 author, trigger = build
     landed) for that window and named as such in `pending_contracts.yaml`. Recommendation: the builder.
- **Classification:** NON-GATING (fake substrate); the conditional pin lands with r3b.

## §E — errata against my earlier docs
- **Amendment-4 §MP-D point 1:** *"a pin that this derived set ⊇ `ALL_DDL_GENERATORS` (…today it names
  the two unswept emitters)"* → **"a PIN-THE-MISS: the composition-aware unswept set is EXACTLY
  `{generate_lease_ddl, generate_floor_calibration_ddl}`, deleted the day the scaffold derives its own
  set."** The literal ⊇ leg is vacuous-by-import.
- **Amendment-3 F-2:** *"The RED population does not grow"* → **"An unguarded call-time import reds every
  tokenless `(None, None)` fake register (232 HEAD-green tests, measured); the identity leg is guarded on
  `ImportError` until the symbol exists, with a conditional pin that forces the guard's deletion."**
- Pattern across both, for the next ruling I write: a sentence that names a NUMBER or a DIRECTION is a
  measurement claim; if I did not run it, the sentence says "expected", not "is".

## §W — worklist delta (against amendment-4 §W)
| # | item | change | class |
|---|---|---|---|
| 7 | population resolver | FORK-A: (c) as implemented; (a) leg optional, docstring honest. FORK-B: ratified + the `dim`-whenever-present rider + the `isfunction` bound in the docstring | NON-GATING |
| 8 | fake mirror + parity matrix | FORK-C: guarded identity leg + conditional guard-deletion pin; builder brief grants the one-line deletion | NON-GATING |
| — | builder brief | add: "delete the `ImportError` guard in `_comms_fakes.py` in REFACTOR (one line; the conditional pin reds until you do)" | lead |
