brief-base v11 read
brief project v7 read

# REPORT-contract-256-05b — CONTRACT for #256 (`lore_findings` `annotate`)

Model attestation: **claude-opus-4-8** (Opus 4.8), pinned by the `opus48-worker` frontmatter.
Role: CONTRACT author (RED tests only). I did NOT touch production code.

## SUMMARY BLOCK
- receipt: `brief-base v11 read` · `brief project v7 read`
- state: **done, ADVERSARY-REVISED** — LEDGER contract (7 pins) + SERVED contract (3 pins) +
  adversary round 1 (F1 satisfiability fix, F2 share-vs-clone mutation pin, F3 write⇒footer, F4
  discoverability, R3 is_blank reuse). All RED at HEAD; satisfiability proven 0-failed against a
  known-correct reference build over the FULL affected suite (findings + mcp_server + comms_footer +
  task_read_surface); load-bearing pins mutation-proven; ZERO-NEW confirmed (pytest + mypy).
- deviations: none to the (twice-widened) writable set. Files edited: `test_findings.py` +
  `_finding_fakes.py` (ledger); `test_mcp_server.py` (served); and — per the adversary's F1 (the C-DEF
  class) — `test_task_read_surface.py` + `test_comms_footer.py` (two existing pins a correct build
  reddens; both are test-side constants the builder cannot reach). The fake edit is REQUIRED, not
  optional: the parity fixture runs every test against BOTH backends and the builder's writable set is
  production `findings.py`/`server.py` only, so the contract author must supply the fake's independent
  `annotate`. Disclosed per scope law.
- Packages considered: **`lorerunes.is_blank` — REUSE** (verdict `replace` of a hand-rolled blank
  check). READ: `lorerunes/lorerunes/blankness.py` source — `is_blank(value) = not value or not
  value.strip()`, the ONE shared "what counts as blank?" predicate `report` already uses. Pin 6
  pins the blank/None-rejection BEHAVIOUR; the reference build calls `is_blank` (do NOT hand-roll —
  the builder must too). No third-party mechanism specified.
- Graded: **n/a** — this is a CONTRACT (RED tests), not a verdict on another artifact. Authored
  against HEAD `299e69a`; all cited production symbols verified present at `299e69a`.
- decisions-needed / FLAGS for the lead (details in §Flags):
  1. **CLOSED (lead directive).** Served surface contracted — `action=annotate` dispatch + render
     pinned in `test_mcp_server.py` (§Served surface), incl. the #104 twin.
  2. **CLOSED (adversary F2).** The share-vs-clone hole is now a CHECKED variable: a mutation pin
     (`test_mutating_the_shared_shell_reddens_both_annotate_and_transition`) injects a sentinel into
     `FindingLedger._guarded_append_fragment` and asserts it reaches BOTH annotate's AND a transition's
     SQL — a byte-identical clone reddens. It DICTATES the shared symbol the builder must route through.
  - none open. (Adversary round 1 fully absorbed — F1–F4 + R3; §Adversary revision.)
- receipt pointers: ledger pins→tests = `loremaster/tests/test_findings.py::TestAnnotate` /
  `TestConcurrentAnnotate` / `TestAnnotateRidesTheGuardedAppendSeam` /
  `TestAnnotateHostileNoteIsContained`; served pins→tests =
  `loremaster/tests/test_mcp_server.py::TestToolBehaviourEndToEnd::test_findings_annotate_*` (§Served
  surface); fake = `loremaster/tests/_finding_fakes.py::FakeFindingLedger.annotate`;
  reference build (pasted) = §Reference build; mutation proofs = §Mutation proofs; store law =
  `docs/reference/surrealdb-31-capabilities.md` §2 (server-side array append / silent-no-op enemy),
  §5 (hot-row ≥8-way overlapping lifetimes); render seam = `loremaster.render.render_attributed`.

---

## What the contract pins (design §Q1's 7 pins → tests)

Spec: `REPORT-fable-design-05b.md` §Q1 (annotate = ACTION, its 7 pins) + finding **#256**. Store law:
`docs/reference/surrealdb-31-capabilities.md` (cited, never re-transcribed). All new tests reach the
not-yet-existing verb through the LAZY ACCESSOR `_annotate(ledger)` (`getattr` + named assert), the
house idiom (mirrors `test_link5_render_containment.py::_fence_width`) — so a HEAD run fails
BEHAVIOURALLY with a named message, never a collection/mypy "no attribute" error.

| Pin (design §Q1) | Test(s) | The discriminating "what wrong build still passes this?" |
|---|---|---|
| **1** status UNCHANGED, every status; annotate legal in ALL statuses | `TestAnnotate::test_annotate_preserves_status_in_every_state[open/acknowledged/resolved/wontfix]` | a build routing through `_transition`/`LEGAL_TRANSITIONS` FLIPS `open`→`acknowledged` and REJECTS a terminal finding. **Mutation-proven RED** (§Mutation proofs). |
| **2** state machine NOT loosened (positive control) | `TestAnnotate::test_annotate_does_not_add_a_legal_transition_edge` | a build that added `annotate` by widening `LEGAL_TRANSITIONS` makes the paired `acknowledge`-on-`acknowledged` legal → this reddens. |
| **3** note lands + renders; NO fabricated `→ status` (#104) | `TestAnnotate::test_annotate_appends_exactly_one_well_formed_event` (+ `test_annotate_note_survives_a_later_transition`) | exactly ONE event appended LAST, `action="annotate"`, actor+note+at, **`"to"` key ABSENT**. A build cloning the transition event shape (which carries `to`) leaves the status key present. |
| **4** ≥8-way concurrent, overlapping lifetimes, ZERO lost | `TestConcurrentAnnotate::test_concurrent_annotates_lose_no_events` | 8 racers × 5 annotates = 40 events, all distinct, on ONE row. A client-side read-modify-write of the whole `provenance` LOSES events. **Mutation-proven RED: 40 expected, only 10 landed, 30 lost** (§Mutation proofs). |
| **5** no silent no-op on an absent target | `TestAnnotate::test_annotate_unknown_number_raises_not_found` + `..._unknown_id_...` | annotate on a non-existent number/id raises `FindingNotFoundError` (reuse `_resolve_or_raise`). A silent-no-op build returns a Finding instead of raising. |
| **6** `note` REQUIRED + non-blank, refused BEFORE any write | `TestAnnotate::test_annotate_rejects_blank_or_none_note["", " ", "\t", "\n", None]` + `test_annotate_accepts_a_real_note` | fixtures discriminate 3 wrong builds: `not note` accepts `" "`; `not note.strip()` without a None guard CRASHES on `None`; over-rejecting breaks `"  real  "`. All blank/None → clean `ValueError`, NO event appended; a padded-real note is ACCEPTED (positive control). |
| **7** hostile note contained in served `get` bytes (#195-adjacent) | `TestAnnotateHostileNoteIsContained::test_hostile_annotate_note_is_contained_in_served_get_bytes` | note = newlines + a row-shaped forgery directive + 2 backtick runs. The served provenance IS `render_attributed(persisted.provenance)`; a bare-f-string/repr render mints no delimiter, so the forgery leaks OUTSIDE it → the marker lands in `before` → RED. |
| **mission** SHARE the guarded-append shell, do not clone | `TestAnnotateRidesTheGuardedAppendSeam::test_annotate_and_transition_emit_the_same_guarded_append` (real-only) | captures annotate's + a transition's composed SQL via a `_apply` spy: both emit `provenance.events += [` and `IF array::len(...) THROW`; annotate emits NO `status = $` (drops SET + WHERE), the transition DOES (positive control); the bound annotate event has `action="annotate"` and no `to`. Forces the guarded shell; catches a naive/unguarded/read-modify-write/private clone. |

Pin 7 note: the render seam already contains ANY provenance content (`_render_finding_detail` →
`render_attributed(provenance)`, proven by `test_link5_render_containment.py`), so pin 7's RED-at-HEAD
comes from the LEDGER `annotate` not existing (the note never reaches provenance), not from a render
gap — it proves the annotate note flows THROUGH the proven seam, and reuses the PRODUCTION
`render_attributed` (not a cloned containment predicate).

## RED at HEAD (`299e69a`)
`test_findings.py` full file, main tree: **18 failed, 170 passed**. Every one of the 18 failures is an
annotate `real`-param (15 `TestAnnotate` real + 1 concurrency real + 1 structural real-only + 1
hostile-note real); the grep for any NON-annotate failure was EMPTY. The `fake`-param of each new test
PASSES (the fake implements the contract), which both proves the contract satisfiable on the parity
fake AND is why the RED at HEAD is the `real` params only. Named-RED message at HEAD:
`AssertionError: #256: FindingLedger.annotate is not implemented …`.

## Satisfiability receipt (known-correct reference build)
Isolated via `./scripts/scratch_copy.sh /tmp/lore-256-ref` — provenance ASSERTED:
`loremaster.__file__ → /tmp/lore-256-ref/loremaster/loremaster/__init__.py` (imports resolve INSIDE
the copy; not the original tree).
- new classes only: **35 passed, 0 failed** (`real` + `fake`).
- FULL `test_findings.py` on the reference build (`-n auto`): **188 passed, 0 failed** — proving the
  shared-shell refactor of `_transition_fragment` (§Reference build) is behaviour-preserving (every
  existing transition/concurrency test still green) AND the whole contract is satisfiable end-to-end.

## Mutation proofs (load-bearing pins discriminate)
- **Pin 4 (concurrency).** Replaced the server-side append with a client-side read-modify-write
  (read `provenance` → Python append → whole-object `SET provenance = $wprov`). `TestConcurrentAnnotate[real]`
  → **FAILED: "expected 40 annotate events, 10 landed — 30 lost under contention."** The pin sees the
  exact defect store law §5 warns of; the server-side `+= [$event]` build does not lose.
- **Pin 1 (status-preservation).** Routed annotate through `_transition(id, STATUS_ACKNOWLEDGED, …)`.
  `[real-open]` → **FAILED: "annotate changed status 'open' -> 'acknowledged'"**; `[real-resolved]` →
  **FAILED** (`IllegalTransitionError`, resolved→acknowledged illegal). Both wrong-build modes caught.

## Served surface (#256 dispatch + render) — added per the lead's widen-scope directive
#256 is a SERVED action (agents call `lore_findings action=annotate`), so the MCP dispatch + render
are contracted, not just the ledger. New pins in `loremaster/tests/test_mcp_server.py::TestToolBehaviourEndToEnd`
(mirroring the existing findings-dispatch idiom; RED at HEAD because `annotate` is not a dispatch
action — the dispatcher raises "unknown findings action"):

| Served pin | Test | RED-at-HEAD reason / discriminator |
|---|---|---|
| **S1** dispatch exists + routes → returns finding detail | `test_findings_annotate_action_routes_to_the_ledger_and_returns_detail` | HEAD: unknown action. Asserts the response carries the subject (get-render trait) + the note, and the ledger row is annotated with status UNCHANGED (`open`). |
| **S2** #104 server twin: NO fabricated "transitioned to" | `test_findings_annotate_response_and_get_never_fabricate_a_transition` | the annotate RESPONSE and a later `get` of an annotate-only finding both assert `"transitioned to" not in served`. Discriminator: wiring `action=annotate` through `_render_finding_transition` renders `"finding #N transitioned to open by …"` ⇒ RED — the exact defect flag 1 named. |
| **S3** served `note` required + non-blank (×4: `""`, `" "`, `"\t"`, `None`) | `test_findings_annotate_requires_a_nonblank_note_at_the_served_boundary` | HEAD: the unknown-action error names the ACTION, never `"note"`, so `"note" in message` fails. Reuse `_require_finding_arg(note, "note")` (rejects None + blank) at the served boundary. |

RED at HEAD (`299e69a`): **6 failed** (S1, S2, S3×4), all `test_findings_annotate_*`.
Satisfiability (reference build, server dispatch branch added — see §Reference build): full
`test_mcp_server.py` = **651 passed, 0 failed** (all existing MCP pins + the 6 new served pins green,
including the AST recorder-pin `..._names_every_action_that_RECORDS_it`, the description-teaching pins,
and the strict-to-action matrix pin — the note-param description was updated to name `annotate`).

The served render reuses `_render_finding_detail` for the annotate response (returns the detail like
`get`) — so it CANNOT fabricate a transition line AND surfaces the note, closing flag 1 by construction
without a new render of stored free text.

## Adversary revision (round 1 — F1–F4 + R3, from REPORT-adversary-256-05b.md)
The behavioural core (pins 1–6, S1–S3) graded STRONG/uncatchable; the adversary found 2 satisfiability
blockers + 2 missing pins. All absorbed:

| Fix | What was wrong | The pin now (RED at HEAD → green on ref build) |
|---|---|---|
| **F1** (C-DEF satisfiability blocker) | adding `annotate` to production `_FINDING_ACTIONS` reddens 2 EXISTING pins in files my scoped satisfiability never ran — test-side constants the builder can't reach | `test_task_read_surface.py::_EXPECTED_FINDING_ACTIONS` += `"annotate"` (dispatch order); `test_comms_footer.py::FINDING_WRITE_ACTIONS` += `"annotate"` + an `annotate` branch in `_finding_action_kwargs` (`{id_or_number, actor, note}` — annotate REQUIRES a note, the C-DEF-2 shape). |
| **F2** (share-vs-clone, my own flag 2) | a byte-identical CLONE of the guarded shell passes the ENTIRE contract | `test_mutating_the_shared_shell_reddens_both_annotate_and_transition` — mutate `FindingLedger._guarded_append_fragment`, assert the sentinel reaches BOTH annotate + a transition SQL (positive control on the transition leg). Adapted from the adversary's §Instrument. Makes "one implementation" a CHECKED variable + dictates the shared symbol. |
| **F3** (write⇒footer) | a `writes=0` annotate passes all 6 served pins | rides F1: once `annotate ∈ FINDING_WRITE_ACTIONS` with note-bearing kwargs, the existing `test_EVERY_findings_WRITE_action_footers[annotate]` leg drives it (RED at HEAD). |
| **F4** (Consumer Law / discoverability — #256's OWN purpose) | the served `lore_findings` tool description never names `annotate`, so agents can't discover the cheap correction | `test_findings_description_teaches_the_annotate_action` (mirrors `..._teaches_the_actions`). ⚠ The ref-build run CAUGHT that the description is a **separate registered string** (server.py:10672), NOT the method docstring — the builder must edit THAT string. |
| **R3** (ONE-IMPLEMENTATION, optional — taken) | pin 6 pins blank-REJECTION but not that annotate CALLS `is_blank` (a hand-rolled `not note.strip()` clone passes) | `test_annotate_reuses_the_shared_blankness_predicate_not_a_hand_rolled_clone` — AST over the source, matches any import style (`is_blank(...)` bare or qualified), so a correct module-qualified reuse is NOT a false RED; a hand-roll reddens. |

RED at HEAD (`299e69a`): F1a (equality) 1 · F1b (partition 1 + write-footer[annotate] 2 + drivable-action[annotate] 1) · F2 1 · R3 1 · F4 1.
Satisfiability re-run over the FULL affected suite on the reference build (server dispatch branch + the
F4 tool-description string + the F1-fed constants):
`test_findings.py`+`test_task_read_surface.py`+`test_comms_footer.py` = **536 passed / 1 skipped / 0
failed**; `test_mcp_server.py` = **652 passed / 0 failed**.

## ZERO-NEW gate
- pytest at HEAD, **0 non-annotate failures in every touched file** (verified by grep): `test_findings.py`
  20 annotate reds / 170 passed; `test_mcp_server.py` 7 served+F4 reds / 645 passed;
  `test_task_read_surface.py`+`test_comms_footer.py` 5 intended F1 reds / 341 passed / 1 skipped. Every
  red is an intended contract-first RED; every existing test still passes.
- mypy (`scripts/typecheck.sh`): my edited files (`test_findings.py`, `_finding_fakes.py`,
  `test_mcp_server.py`, `test_task_read_surface.py`, `test_comms_footer.py`) contribute **0** errors —
  the two failing legs are UNCHANGED pre-existing baselines I never touched (`loremaster` 102 auth/posture,
  `lorerunes` 89 Posture/SCOPE).

## Flags / forks (surfaced per scope law — lead/operator decide)
1. **CLOSED — the served surface is now contracted** (§Served surface). The builder's server-side
   obligations, now PINNED (RED at HEAD, all green on the reference build): add
   `_FINDING_ACTION_ANNOTATE = "annotate"` + the entry in `_FINDING_ACTIONS`; add the
   `AppContext.findings` dispatch branch calling `finding_ledger.annotate(_require_finding_ref(id_or_number),
   _require_finding_arg(actor,"actor"), _require_finding_arg(note,"note"))` with `writes=1`; render the
   response via **`_render_finding_detail`** (NOT `_render_finding_transition` — that fabricates a
   transition, the #104 defect S2 kills); update the served `note`-param description to name `annotate`
   (the AST recorder-pin `..._names_every_action_that_RECORDS_it` enforces this). Also (not pinned,
   builder hygiene): add `annotate` to the `FindingLedger` public-surface docstring in `findings.py`.
2. **CLOSED (adversary F2).** The mutation-SHARING proof is now a pin
   (`test_mutating_the_shared_shell_reddens_both_annotate_and_transition`), not a builder promise. It
   monkeypatches `FindingLedger._guarded_append_fragment` (the shared symbol the reference build
   extracts, which the pin DICTATES) to inject a sentinel and asserts it reaches BOTH annotate's and a
   transition's captured SQL — a byte-identical clone reddens (sentinel only in the transition). This
   forces the builder to route annotate through the ONE shared shell.
3. **Builder server-side obligations (now pinned, all green on the ref build):** add
   `_FINDING_ACTION_ANNOTATE` + its `_FINDING_ACTIONS` entry (dispatch order, after `wontfix`); the
   `AppContext.findings` dispatch branch → `finding_ledger.annotate(_require_finding_ref(id_or_number),
   _require_finding_arg(actor,"actor"), _require_finding_arg(note,"note"))`, `writes=1`, response via
   **`_render_finding_detail`** (never `_render_finding_transition` — the #104 defect S2 kills); update
   the served `note`-param description AND the **`lore_findings` tool-description STRING** (server.py
   ~10672, NOT the method docstring — F4 caught this) to name `annotate`; extract
   `_guarded_append_fragment` as the shared shell (F2); reuse `lorerunes.is_blank` (R3). Non-pinned
   hygiene: add `annotate` to the `FindingLedger` public-surface docstring.
3. **`note` signature.** Contracted REQUIRED, `str | None` (so the MCP-forwarded `None` is accepted
   and rejected with a clean `ValueError`, not a `TypeError`), blank/None → `ValueError` via
   `lorerunes.is_blank` (do NOT hand-roll). Pinned behaviourally (pin 6); typed loosely at the accessor
   so the exact signature is the builder's to declare to satisfy the behaviour.

## Reference build (the instrument — pasted verbatim per brief-base §1; scratch is disposable)
This is the known-correct build the satisfiability + mutation receipts ran against. It is NOT shipped
(the repo's `findings.py` is untouched — the builder implements independently). Edits to a scratch copy
of `loremaster/loremaster/findings.py`:

```python
# import (top, with the other package imports)
from lorerunes import is_blank

# constant (beside _ACTION_TRANSITION)
_ACTION_ANNOTATE = "annotate"

# the shared shell — _transition_fragment delegates to THIS; annotate calls it with
# status_target=None, expected_from=None (drops the SET + the WHERE predicate).
    @staticmethod
    def _guarded_append_fragment(
        finding_id: str,
        event: dict[str, Any],
        *,
        status_target: str | None = None,
        expected_from: str | None = None,
    ) -> TxnFragment:
        set_parts = [f"{_COL_PROVENANCE}.{_PROV_EVENTS} += [${_TRANSITION_EVENT_PARAM}]"]
        params: dict[str, Any] = {
            _TRANSITION_ID_PARAM: finding_id,
            _TRANSITION_EVENT_PARAM: event,
        }
        if status_target is not None:
            set_parts.insert(0, f"{_COL_STATUS} = ${_TRANSITION_STATUS_PARAM}")
            params[_TRANSITION_STATUS_PARAM] = status_target
        where_clause = ""
        if expected_from is not None:
            where_clause = f" WHERE {_COL_STATUS} = ${_TRANSITION_EXPECTED_FROM_PARAM}"
            params[_TRANSITION_EXPECTED_FROM_PARAM] = expected_from
        guarded = (
            f"LET ${_TRANSITION_UPDATED_VAR} = (UPDATE "
            f"type::record('{FINDING_TABLE}', ${_TRANSITION_ID_PARAM}) SET "
            f"{', '.join(set_parts)}{where_clause})"
        )
        guard_updated = (
            f"IF array::len(${_TRANSITION_UPDATED_VAR}) == 0 "
            f"{{ THROW '{_TRANSITION_ALREADY_MESSAGE}' }}"
        )
        return TxnFragment(statements=[guarded, guard_updated], params=params)

    @staticmethod
    def _transition_fragment(
        finding_id: str, target: str, expected_from: str, event: dict[str, Any]
    ) -> TxnFragment:
        return FindingLedger._guarded_append_fragment(
            finding_id, event, status_target=target, expected_from=expected_from
        )

    # the public verb (placed after wontfix)
    async def annotate(self, id_or_number: int | str, actor: str, note: str | None) -> Finding:
        if note is None or is_blank(note):
            raise ValueError(
                f"finding annotate note must be a non-empty, non-whitespace string, "
                f"got {note!r}"
            )
        row = await self._resolve_or_raise(id_or_number)
        finding_id = self._bare_id(row.get(_ID_KEY))
        now = datetime.now(UTC)
        event: dict[str, Any] = {
            _PROV_ACTOR: actor,
            _PROV_ACTION: _ACTION_ANNOTATE,
            _PROV_AT: now.isoformat(),
            _PROV_NOTE: note,
        }
        try:
            await self._apply([self._guarded_append_fragment(finding_id, event)])
        except (SurrealConnectionError, TxnContentionExhaustedError):
            raise
        except SurrealStoreError as error:
            # Zero-row guard: the row vanished between pre-read and UPDATE (findings are
            # never hard-deleted → belt-and-braces). Surface it; never a silent no-op.
            fresh = await self._select_row_by_id(finding_id)
            if fresh is None:
                raise FindingNotFoundError(f"no finding with id {finding_id!r}") from error
            raise
        updated = await self._select_row_by_id(finding_id)
        if updated is None:
            raise FindingNotFoundError(f"no finding with id {finding_id!r}")
        return self._row_to_finding(updated)
```

The fake's independent parity `annotate` (`_finding_fakes.py::FakeFindingLedger.annotate`) mirrors the
same properties (no legal-transition gate; None/blank guard before any yield; atomic append with no
`await` between resolve and mutate; `action="annotate"`, no `"to"` key) — an independent implementation,
never imported from production.

Served-surface reference edits (scratch `server.py`, to satisfy the 3 served pins + the existing
recorder/description pins): `_FINDING_ACTION_ANNOTATE = "annotate"` + its `_FINDING_ACTIONS` entry; the
dispatch branch (above, rendering via `_render_finding_detail`); and the `note`-param description
widened to *"…recorded with an 'acknowledge' / 'resolve' / 'wontfix' transition (optional there), and
REQUIRED for an 'annotate' …"*. Reference build results: `test_findings.py` 188 passed + 35 new green,
`test_mcp_server.py` **651 passed / 0 failed**.
