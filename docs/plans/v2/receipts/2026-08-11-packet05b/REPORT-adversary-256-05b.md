brief-base v11 read
brief project v7 read

# REPORT-adversary-256-05b — CONTRACT ADVERSARY for #256 (`lore_findings annotate`)

Model attestation: **claude-opus-4-8** (Opus 4.8), pinned by `opus48-worker` frontmatter (attested).
Role: CONTRACT ADVERSARY, posture REFUTE. I did NOT edit repo code or tests — every probe lived in
an absolute scratch tree.

## SUMMARY BLOCK
- receipt: `brief-base v11 read` · `brief project v7 read`
- **VERDICT (round 2, delta re-grade of the REVISED contract): CONTRACT SUFFICIENT.** All four
  round-1 findings (F1–F4) + R3 are empirically fixed; no blocker survived the revision. Two
  LOW-severity residuals remain on the R3 reuse pin (aliased-import false-RED, cosmetic-call
  false-GREEN) and one very-minor F4 substring note — notes, not blockers. **See §DELTA RE-GRADE.**
- **VERDICT (round 1, historical): CONTRACT INSUFFICIENT** — 2 satisfiability blockers + 2 missing
  pins. The behavioural core (pins 1–6, S1–S3) was STRONG; the gaps were (a) not satisfiable against
  the full suite and (b) the author-flagged share-vs-clone hole. All now closed (§DELTA RE-GRADE).
- **P1 headline — did a wrong build survive?** YES, three ways: (1) a byte-identical **CLONE** of the
  guarded-append shell passes the ENTIRE contract (35 ledger + 7 served pins) — FLAG 2, confirmed;
  (2) a **`writes=0`** annotate (never footers) passes all 6 served pins; (3) the CORRECT reference
  build **reddens 2 existing pins** the author never ran (satisfiability blocker). All other wrong
  builds I tried were caught.
- Capability check: full tool access; test store (spike-surreal :18000) up; `scratch_copy.sh` used
  (provenance asserted). No blocking gaps.
- Packages considered: **`lorerunes.is_blank` — the contract pins blank-REJECTION BEHAVIOUR, not
  REUSE** (READ `lorerunes/lorerunes/blankness.py` — `is_blank(v)=not v or not v.strip()`). My
  reference build hand-rolled `not note.strip()` and passed pin 6 → the DRY reuse is unpinned
  (residual R3, low severity). No third-party mechanism specified. Verdict on the survey: `keep` (the
  author's `replace`/reuse recommendation is right; only the PIN is missing).
- Graded: **299e69a** · HEAD-at-report: **299e69a** · SAME. Contract tests uncommitted in the
  working tree; production `findings.py`/`server.py` untouched at HEAD (annotate absent — verified).
- decisions-needed (for the lead):
  1. **F1 (BLOCKER):** the contract must extend to `test_comms_footer.py` + `test_task_read_surface.py`
     (test-side; builder can't reach them). Author's satisfiability receipt was scoped to 2 files and
     missed 2 breaks. Send back to CONTRACT.
  2. **F2 (FLAG 2):** add the share-vs-clone mutation pin (spec below). The author correctly flagged
     this could not be pinned by their structural test — it CAN, with a mutation proof.
- receipt pointers: FLAG-2 clone survival = §P1-attack-5 + probe pasted in §Instrument;
  satisfiability breaks = §F1 (both REDs reproduced); wrong-build receipts = §P1 table; quantifier
  table = §P1b; reach table = §P1c; scratch tree `/tmp/lore-256-adv` (disposable),
  `loremaster.__file__ → /tmp/lore-256-adv/loremaster/loremaster/__init__.py` (asserted).

---

## DELTA RE-GRADE (round 2 — revised contract, 5 test files) — Graded @ 299e69a (SAME)
Fresh scratch `/tmp/lore-256-adv2` (provenance asserted: `loremaster.__file__ →
/tmp/lore-256-adv2/loremaster/loremaster/__init__.py`). I rebuilt my known-correct reference
independently (this time using `is_blank` for R3 + naming `annotate` in the served tool description
for F4) and re-ran every attack against the REVISED pins.

| Round-1 finding | Revised pin | Attack re-run | Result |
|---|---|---|---|
| **F1** satisfiability | `_EXPECTED_FINDING_ACTIONS += annotate` (dispatch order) · `FINDING_WRITE_ACTIONS += annotate` + `_finding_action_kwargs` annotate branch (id+actor+note) | full affected suite on the CORRECT ref build | **FIXED** — `test_findings + test_task_read_surface + test_comms_footer` = **536 passed / 0 failed**; `test_mcp_server` = **652 passed / 0 failed**. No residual C-DEF. |
| **F2** share-vs-clone | `test_mutating_the_shared_shell_reddens_both_annotate_and_transition` (adapted from my §Instrument, with a positive control) | rebuilt the **CLONE** (`_annotate_fragment`) vs the revised contract | **FIXED** — clone → mutation pin **RED** ("annotate did NOT route through the shared `_guarded_append_fragment` … sentinel reached only the transition"); the OTHER 35 annotate pins stay GREEN (mutation pin is the sole discriminator); ref build (shares) passes it. |
| **F3** write⇒footer | annotate now in `FINDING_WRITE_ACTIONS`, driven by the note-bearing kwargs | `writes=0` annotate | **FIXED** — `test_EVERY_findings_WRITE_action_footers[annotate-caller0/1]` **RED** ("action='annotate' WROTE, traffic pends … yet no footer was served"). |
| **F4** discoverability | `test_findings_description_teaches_the_annotate_action` | removed `annotate` from the SERVED tool description only (dispatch + note-param intact) | **FIXED** — teaches pin **RED**; keyed on `tools["lore_findings"].description` (the served action menu), NOT the docstring/note-param (proven: removing it from *only* the tool description reddens it). |
| **R3** DRY reuse (was a round-1 residual) | `test_annotate_reuses_the_shared_blankness_predicate_not_a_hand_rolled_clone` (AST) | hand-rolled `not note.strip()` (no is_blank) | **CAUGHT** — realistic hand-roll → RED. Handles bare + module-qualified (`lorerunes.is_blank`) reuse without false-RED. |

**NEW-HOLES probe (packet-03b lesson — did the revision introduce a survivor?)** — no BLOCKER survived.
Residuals found (all LOW severity — honest-developer threat model, per CLAUDE.md "a gate needs a
threat model"):
- **R3-a (proxy-not-effect, false-GREEN):** a build that calls `is_blank(note or "")` *cosmetically*
  and discards the result while the ACTUAL guard is hand-rolled `not note.strip()` **PASSES R3**
  (reproduced: 1 passed). R3 observes CALL-PRESENCE (a proxy), not that `is_blank`'s result gates the
  write (the effect). Bites only a *deliberately* evasive build, not an honest one — out of R3's
  threat model. Note, not a blocker.
- **R3-b (aliased-import false-RED):** a legit `from lorerunes import is_blank as _blank; _blank(note)`
  **fails R3** (reproduced: 1 failed). Qualified reuse (`lorerunes.is_blank`) is fine; only *aliasing*
  false-reds. The house idiom is bare `is_blank` (config.py), so an honest builder matching the idiom
  passes; a builder who aliases is falsely trapped (trivially fixed by not aliasing).
- **F4 substring note (very minor):** the teaches pin is a substring check (`"annotate" in
  description`), matching the house idiom of its sibling `test_findings_description_teaches_the_actions`.
  A description containing "annotated"/"annotation" for an unrelated reason would false-pass; none does
  today. Cosmetic; no action needed.
- **F2 robustness:** I could construct no build that passes the mutation pin while cloning "where it
  matters" — to pass, annotate's composed fragment MUST be the (patched) shell's output flowing to
  `_apply`, which IS sharing the whole append+THROW shell; a build that discards the shell's output
  reddens the pin, and one that strips the THROW reddens the structural pin. The positive control
  (`sentinel in transition_sql` first) means the probe cannot go blind.

**Verdict on the delta: SUFFICIENT.** The four fixes are real and discriminating (each door-built and
reddened); the residuals are low-severity notes on a formerly-residual pin (R3) and a cosmetic F4
substring, none of which bites an honest builder. Right-sizing rigor to importance (CLAUDE.md), these
do not warrant another CONTRACT round — the author MAY tighten R3 to observe the effect (e.g. assert
the guard's *test* is `is_blank(...)`, or accept an aliased name) if cheap, but it is optional.

---

## MISSING PINS — ROUND 1 (historical; all CLOSED in round 2, see §DELTA RE-GRADE)

### F1 — SATISFIABILITY BLOCKER: a correct build reddens 2 existing pins the author never ran
**The defect:** adding `annotate` to production `_FINDING_ACTIONS` (which the builder MUST do) reddens
two EXISTING pins that live in files OUTSIDE the author's satisfiability run (`test_findings.py` +
`test_mcp_server.py` only). Both fixes are **test-side constants the builder cannot reach** (declared
writable set = production `findings.py`/`server.py`). So the contract as delivered is **not
satisfiable against the full suite** — the builder is trapped exactly like the documented C-DEF class
("a pre-existing pin the reshape structurally contradicts"). *"I verified it" was a claim about a
SCOPE, not a fact.*

Reproductions (on my known-correct reference build, in scratch):
```
test_comms_footer.py::TestTheFooterRidesTheOUTCOMENotTheVERB::
  test_the_declared_action_PARTITION_covers_the_dispatchers_OWN_action_set
  E  AssertionError: lore_findings's declared action partition does not equal the dispatcher's
     own action set. ... in production, undeclared: ['annotate']            (1 failed, 244 passed)

test_task_read_surface.py::TestTheServedActionVocabulariesArePinnedByEQUALITY::
  test_the_FINDING_actions_are_EXACTLY_the_declared_set
  E  AssertionError: lore_findings serves (...,'wontfix','annotate','resolve_many',...);
     this contract declares (...,'wontfix','resolve_many','acknowledge_many')  (1 failed, 97 passed)
```
**The tests that should exist / change (author owns these files):**
1. `test_task_read_surface.py::_EXPECTED_FINDING_ACTIONS` — add `"annotate"` (in dispatch order,
   after `wontfix`). Its own pin docstring states a new action *"owes a Leg-1 scope-diff row, an entry
   in the parameter-refusal matrix and its own leg-2 constructions"* — pin 7 is the Leg-2 construction;
   the scope-diff/refusal rows should be confirmed present.
2. `test_comms_footer.py::FINDING_WRITE_ACTIONS` — add `"annotate"` (it MUTATES). **AND**
   `_finding_action_kwargs` needs an `annotate` branch supplying `{"id_or_number": seeded.id,
   "actor": ..., "note": "a real note"}` — annotate REQUIRES a non-blank note, so without this the
   parametrized `@parametrize("action", FINDING_WRITE_ACTIONS)` footer leg drives annotate with no
   `id_or_number`/`note` and dies on `_require_finding_ref`/note-required (the exact C-DEF-2 pattern
   already annotated at `test_comms_footer.py:3942`).

### F2 — FLAG 2 (the author's own flag): share-vs-clone is NOT a checked variable → a CLONE survives
**Confirmed empirically.** I built an annotate that composes its own **byte-identical** guarded-append
fragment (`_annotate_fragment`) instead of sharing `_transition_fragment`'s shell. It passed the
**ENTIRE** contract: 35 ledger pins + 7 served/recorder pins, 0 failed. `TestAnnotateRidesTheGuarded
AppendSeam` matches SQL TEXT, so a clone is invisible to it — routing-is-not-sharing, exactly #102/#120.

The definitive discriminator is a **mutation of the ONE shared shell**, which the contract lacks. My
probe (pasted in §Instrument) builds it and demonstrates it works, with a positive control:
```
CLONE build : sentinel in TRANSITION sql=True, in ANNOTATE sql=False  → VERDICT: CLONE
SHARE build : sentinel in TRANSITION sql=True, in ANNOTATE sql=True   → VERDICT: SHARED
```
**The test that should exist** (contract author writes it; it dictates the shared symbol the builder
must create): in `test_findings.py`, a real-backend pin that monkeypatches the concrete shared shell
(`FindingLedger._guarded_append_fragment`, the name the reference build extracts) to inject a sentinel
into its composed statement, then — via the SAME `_apply` spy `TestAnnotateRidesTheGuardedAppendSeam`
already uses — asserts the sentinel appears in **BOTH** annotate's and a transition's captured SQL. A
build where annotate clones the shell reddens (sentinel only in transition). This makes "one
implementation" a CHECKED variable rather than a hand-list, and forces the builder to route annotate
through the shared shell. (P1c leg 5 — sharing proven by mutation, not by call-site inspection.)

### F3 — MISSING PIN: annotate is a WRITE but the contract never pins that it FOOTERS
**The defect (W5 class):** the #256 contract nowhere asserts annotate footers the pending-traffic line
when traffic pends. A `writes=0` annotate passes all 6 served pins. Reproduction: patched the dispatch
branch to `writes=0` → `pytest -k test_findings_annotate_` → **6 passed**. This is only caught by
`test_comms_footer.py`'s "every write footers" leg — which is part of F1's fix. **The test that should
exist:** once annotate joins `FINDING_WRITE_ACTIONS` (F1), the existing parametrized "wrote ⇒ footer"
leg covers it; confirm it drives an annotate call (needs the note-bearing kwargs from F1). Without F1,
this property is unpinned.

### F4 — MISSING PIN: the served surface does not TEACH annotate (CONSUMER-LAW / discoverability)
**The defect:** on a fully-passing reference build, the `lore_findings` **tool description** and the
**`action` param description** do NOT mention `annotate` (only the `note` param does, forced by the
recorder pin). #256's entire purpose is to make the cheap correction the OBVIOUS move — an agent
scanning the action menu cannot discover it, so it will keep using `supersede` or leave stale bodies.
Reproduction (reference build, `test_mcp_server.py` = 651 passed):
```
TOOL DESC   mentions 'annotate': False
ACTION-PARAM mentions 'annotate': False    (action menu lists report/query/get/.../acknowledge_many)
```
**The test that should exist:** mirror `test_findings_description_teaches_the_actions` (and
`test_tasks_description_teaches_the_actions`) — assert `"annotate"` appears in the served `lore_findings`
tool description and/or the `action`-param description. (This is a served-surface trust gap the builder
must fix in the description prose; it is invisible today because the existing teaches-the-actions pin
only checks report/query/resolve|acknowledge.)

---

## P1b — QUANTIFIER TABLE (every invariant: ∀-over-inputs vs guarded, with a receipt)

| Invariant | Classification | Receipt (door-build) |
|---|---|---|
| Pin 1 status UNCHANGED | **∀ over {open, ack, resolved, wontfix}** | status-flip build (route via `_transition`) → all 4 `[real-*]` RED (open flips; ack/resolved/wontfix `IllegalTransitionError`). |
| Pin 2 no state-machine loosening | positive control (targeted: ack→ack) | widened `LEGAL_TRANSITIONS` self-edge → pin 2 `[real]` RED (`DID NOT RAISE`), pins 1+3 stayed GREEN (isolated — pin 2 catches what 1/3 miss). |
| Pin 3 event shape / no `to` | ∀ over the appended event (single) | fabricated `to` field → pin 3 `[real]` RED + structural RED (`'to' not in event`). |
| Pin 4 zero events lost | **∀-over-outcome under 8-way overlapping contention** | client-side read-modify-write → pin 4 `[real]` RED (11/40 landed, 29 lost). Fixture genuinely overlaps: a serialized fixture drops ZERO — the 29-drop PROVES the overlap. Structural pin ALSO catches RMW offline. |
| Pin 5 not-found on absent target | guarded, ∀ over {unknown number, unknown id} | reuses `_resolve_or_raise` (raises `FindingNotFoundError`); vanished-mid-write raise is pinned STRUCTURALLY (THROW required) — see R1. |
| Pin 6 blank/None note rejected | **∀ over {"", " ", "\t", "\n", None} + positive control** | `not note` build → `[real- ]`,`[real-\t]`,`[real-\n]` RED; `not note.strip()` w/o None guard → `[real-None]` RED (AttributeError≠ValueError). |
| Pin 7 hostile note contained | single hostile fixture (guarded) | passes on reference (note flows through the existing `render_attributed` seam). Low builder-error discrimination — see R2. |
| Mission: SHARE the shell | **NOT ∀, NOT mutation-proven → HOLE** | CLONE survives the whole contract (F2). |

## P1c — REACH TABLE (every guard the contract introduces or relies on)

| Instrument | Reach DERIVED or hand-list? | Coverage a CHECKED variable? | Effect or proxy? | One-source-proven-by-mutation? | Verdict |
|---|---|---|---|---|---|
| `TestAnnotateRidesTheGuardedAppendSeam` (new, structural SQL) | annotate + 1 transition (fixed) | share-vs-clone NOT checked | observes composed SQL as **TEXT** (a clone passes) | **NO** — no mutation of the shared shell | **MISSING PIN (F2)**, empirical |
| recorder pin `..._names_every_action_that_RECORDS_it` (existing, relied on) | **DERIVED** from `AppContext.findings` branches referencing `note` | YES (a new note-forwarding action auto-joins) | served `note`-param description | n/a | SAFE — annotate auto-joins (but only the note param → F4) |
| partition pin `..._PARTITION_covers_..._OWN_action_set` (existing, relied on) | **DERIVED** (`WRITE ∪ READ == _FINDING_ACTIONS`) | YES (reddens on the new action — it DID) | the action set | n/a | instrument SAFE; **contract failed to FEED it → F1** |
| equality pin `..._FINDING_actions_are_EXACTLY_..` (existing) | hand-list `_EXPECTED_FINDING_ACTIONS` | equality (reddens on any add — it DID) | the action tuple | n/a | **contract did not update it → F1** |
| write-footer leg over `FINDING_WRITE_ACTIONS` (existing) | hand-list tuple | annotate ABSENT → uncovered | footer effect | n/a | **F3** (rides F1's fix) |

Legs run: **empirical** for the two new-instrument rows (wrong builds in scratch, store-backed) and
for all three existing-pin rows (reproduced each RED on the reference build). Construction-inspection
for the recorder-pin derivation.

## Fixture-discrimination verdicts (P2)
- **Status (pin 1): DISCRIMINATES** — parametrized over all 4 statuses; no monoculture. Perturbation:
  the status-flip build reddens on every value; a correct build passes on every value.
- **Concurrency degree (pin 4): DISCRIMINATES and is genuinely concurrent** — 8×5=40 (≥8-way, store
  law §5). Proven overlapping by the RMW 29-drop (a serialized fixture cannot drop). Correct build
  lands all 40; RMW drops. The `set(landed)==expected` + `len==40` pair rejects loss AND duplication.
- **Blank note (pin 6): DISCRIMINATES on BOTH axes** — whitespace fixtures kill `not note`; the `None`
  fixture kills `not note.strip()`-without-None-guard; the padded positive control rejects
  over-rejection.
- **Note/actor value: adequate** — pin 3 asserts exact `note`/`actor` echoes; no build branches on
  their value, so no monoculture risk.
- No fixture found that discriminates only at its own values.

## Reproduced RED / satisfiability / corpse-sweep
- **RED-at-HEAD honest (P7):** ledger `[real]` params fail with the NAMED assertion
  `#256: FindingLedger.annotate is not implemented …` (behavioural, not a collection/import error).
  Served: 6 failed (S1, S2, S3×4) via the unknown-action path. Confirmed on unmodified production.
- **Satisfiability (P4, reproduced, reference build in scratch):** `test_findings.py` **188 passed**;
  `test_mcp_server.py` **651 passed**; new classes **35 passed**; served+recorder+teaches **9 passed**.
  BUT `test_comms_footer.py` **1 failed** / `test_task_read_surface.py` **1 failed** (F1). So the
  author's "0-failed" is true only over the 2 files they ran.
- **Corpse sweep (P6):** the new tests assert the NEW world only; no pre-existing test pins a retired
  annotate behaviour (annotate is net-new). The one hazard — old-world tests certifying a corpse — does
  not apply (nothing was deleted/renamed). No corpse hits.
- **Fakes can fail (P5):** the `[fake]` params redden under the same wrong builds where the fake shares
  the property (e.g. pin 6 whitespace on the fake), and the fake is an INDEPENDENT reimplementation
  (never imports production). The fake's `not note.strip()` mirrors the reject-before-yield discipline.

## Residuals (individual verdicts — not blockers)
- **R1 — vanished-row raise:** pinned STRUCTURALLY (structural pin requires `IF array::len(...) THROW`;
  an unguarded annotate → structural RED, reproduced) but NOT exercised behaviourally. ACCEPTABLE:
  findings are never hard-deleted (belt-and-braces, per the design). Verdict: keep as-is; note only.
- **R2 — pin 7 discrimination:** it proves the note FLOWS THROUGH the existing `render_attributed`
  seam and is a good regression guard, but it cannot catch a *builder* error because the render is
  existing code outside the builder's change. Not a gap; low discriminating power vs builder mistakes.
- **R3 — DRY reuse of `lorerunes.is_blank`:** pin 6 pins blank-rejection BEHAVIOUR, not that annotate
  CALLS `is_blank`. A hand-rolled `not note.strip()` clone passes (my reference used it). Low severity
  (blankness is a stable predicate), but per ONE-IMPLEMENTATION the builder should call `is_blank`
  (the author's reference does). Optional pin; flag, not blocker.
- **R4 — actor not validated at the ledger:** the ledger's `annotate(actor)` does not reject a blank
  actor (mirrors `_transition`); the SERVED boundary rejects it via `_require_finding_arg(actor)`.
  Consistent with existing transition verbs. Note only.

---

## Full probe record

### Provenance receipt (#140 law)
`scratch_copy.sh /tmp/lore-256-adv` — asserted `loremaster.__file__ →
/tmp/lore-256-adv/loremaster/loremaster/__init__.py` (imports resolve INSIDE the copy). Every run
below is against that isolated tree; the repo's production files were never modified. My probe printed
`loremaster.__file__ = /tmp/lore-256-adv/loremaster/loremaster/findings.py` as the live receipt.

### Reference build (known-correct, built in scratch) — the oracle
`findings.py`: extract `_guarded_append_fragment(finding_id, event, *, status_target=None,
expected_from=None)`; `_transition_fragment` delegates to it; `annotate(id_or_number, actor, note)`
guards blank/None → `_resolve_or_raise` → `_apply([_guarded_append_fragment(finding_id, event)])` →
re-select. `server.py`: `_FINDING_ACTION_ANNOTATE`, its `_FINDING_ACTIONS` entry, a dispatch branch
rendering via `_render_finding_detail` (NOT `_render_finding_transition`) with `writes=1`, and the
`note`-param description widened to name `annotate`. (This matches the author's §Reference build; I
built it independently to grade the contract, not to ship it.)

### P1 wrong builds — what the contract WAVED THROUGH vs CAUGHT
| # | Wrong build | Result | Pins that fired |
|---|---|---|---|
| 1 | route annotate through `_transition` (status flip) | CAUGHT | pin 1 all 4 `[real-*]` RED |
| 2 | widen `LEGAL_TRANSITIONS` self-edge (loosen) | CAUGHT | pin 2 `[real]` RED; 1+3 green (isolated) |
| 3 | client-side read-modify-write of whole `provenance` | CAUGHT | pin 4 RED (29 lost) + structural RED |
| 4a | fabricate a `to`/status field on the event | CAUGHT | pin 3 RED + structural RED |
| 4b | render response via `_render_finding_transition` | CAUGHT | S1 + S2 RED (`transitioned to open`) |
| 5 | **byte-identical CLONE of the guarded shell** | **SURVIVED** | none (F2) — 35+7 pins GREEN |
| 6 | `writes=0` (never footers) | **SURVIVED** | none in #256 contract (F3) |
| 6b | `not note` blank guard (accepts whitespace) | CAUGHT | pin 6 `[ ]`,`[\t]`,`[\n]` RED |
| 6c | `not note.strip()` w/o None guard | CAUGHT | pin 6 `[None]` RED |
| 6d | unguarded append (no THROW) | CAUGHT | structural pin RED (silent-no-op enemy) |
| — | correct reference build vs FULL suite | **2 REDs** | F1 (comms_footer + task_read_surface) |

### Instrument — the share-vs-clone mutation proof (pasted verbatim; disposable scratch)
`/tmp/lore-256-adv/_adv_share_mutation_probe.py`. Run: `cd /tmp/lore-256-adv && HARNESS_SLUG=general
uv run python _adv_share_mutation_probe.py`. Reports CLONE on the clone build, SHARED on the reference
build (positive control). This is the proof the contract must adopt as a pin (F2).

```python
"""Adversary probe: the SHARE-vs-CLONE mutation proof the #256 contract LACKS.

Mutate the ONE shared shell (`_guarded_append_fragment`) to inject a sentinel token,
then capture (via the same `_apply` spy the structural pin uses) the composed SQL of
BOTH annotate and a transition. If annotate SHARES the shell, the sentinel lands in
BOTH. If annotate is a byte-identical CLONE, the sentinel lands in the transition ONLY
-- exposing the clone the contract's text-matching pin cannot see.
"""
import asyncio, sys
from typing import Any
import loremaster.findings as findings
from loremaster.findings import FindingLedger
sys.path.insert(0, "loremaster/tests")
from _surreal_harness import connect_admin, drop_database, make_env, unique_database
PRODUCTION_DIM = 1024

async def main() -> None:
    print(f"loremaster.__file__ = {findings.__file__}")
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup = await connect_admin(env); await setup.close()
    ledger = FindingLedger(url=env.url, namespace=env.namespace, database=env.database,
                           user=env.user, password=env.password)
    try:
        await ledger.ensure_ready()
        a = await ledger.report("seam A", "b", kind="friction", area="x", category="c", created_by="me")
        t = await ledger.report("seam B", "b", kind="friction", area="x", category="c", created_by="me")
        SENTINEL = "SHARED_SHELL_SENTINEL_MARKER"
        original = FindingLedger._guarded_append_fragment  # already the plain function
        def mutated(finding_id: str, event: dict[str, Any], **kwargs: Any) -> Any:
            frag = original(finding_id, event, **kwargs)
            frag.statements[0] = frag.statements[0] + f" /* {SENTINEL} */"
            return frag
        FindingLedger._guarded_append_fragment = staticmethod(mutated)
        captured: list[list[Any]] = []
        async def capture(fragments: list[Any]) -> None:
            captured.append(list(fragments))
        ledger._apply = capture
        await ledger.annotate(a.number, "me", "a real note")
        await ledger.acknowledge(t.number, "me")
        annotate_sql = " ".join(s for frag in captured[0] for s in frag.statements)
        transition_sql = " ".join(s for frag in captured[1] for s in frag.statements)
        in_annotate, in_transition = SENTINEL in annotate_sql, SENTINEL in transition_sql
        print(f"sentinel in TRANSITION sql : {in_transition}")
        print(f"sentinel in ANNOTATE   sql : {in_annotate}")
        if in_transition and in_annotate:
            print("VERDICT: SHARED  — mutating the one shell reddened BOTH paths.")
        elif in_transition and not in_annotate:
            print("VERDICT: CLONE   — mutating the shared shell reached ONLY the transition; "
                  "annotate is a private copy wearing the shared name.")
        else:
            print("VERDICT: UNEXPECTED — sentinel did not reach the transition path.")
    finally:
        if "original" in locals():
            FindingLedger._guarded_append_fragment = staticmethod(original)
        await ledger.close(); await drop_database(env)
asyncio.run(main())
```

### Verdict
**ROUND 1: CONTRACT INSUFFICIENT** (F1–F4 above). **ROUND 2 (delta re-grade of the revised contract):
CONTRACT SUFFICIENT** — all four findings + R3 empirically fixed (§DELTA RE-GRADE), each door-built
and reddened on the wrong build while the correct reference is 0-failed over the full affected suite
(1188 tests). No blocker survived the revision; the only residuals are LOW-severity notes on the R3
reuse pin (aliased false-RED, cosmetic false-GREEN) and a cosmetic F4 substring — the author MAY
tighten them but need not. **SUFFICIENT releases the builder.**
