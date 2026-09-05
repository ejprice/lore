# REPORT-adversary-63b-i-b

brief-base v14 read
brief project v7 read

STATE: STARTED — contract-adversary for packet 63b wave i-b (memory fidelity: #441 atomicity + #436/#453 replay + #437 render).

## SUMMARY BLOCK (stub — filled at completion)
- receipt: brief-base v14 read · brief project v7 read
- state: in_progress
- Graded: 6f64649 · HEAD-at-report: 6f64649 · SAME
- verdict: PENDING
- §2.5-completeness determination: PENDING
- Packages considered: PENDING
- decisions-needed: PENDING
- pointers: PENDING

## Progress log
- Registered lore_comms (session packet63b, role adversary, model claude-opus-4-8, cadence ≤12m).
- idle-gate contract written.
- Read: role spec (contract-adversary.md); design §1/§2/§2.5/§3/§4/§5.1/§1.9; all 5 target test modules;
  the i-a DATA edit diff (6f64649).

## KEY OBSERVATIONS (pre-empirical — to VERIFY by build)
1. ⚠ CANDIDATE FINDING (§2.5 axis, HIGH): the rescope pin
   `test_a_rescope_on_the_composed_transaction_conflicts_and_rolls_back` asserts
   `"governed_conflict" in str(conflict.value)` on the exception raised by `execute_transaction` (STORE
   layer). But §2.5 rules the raised message is a FIXED label `_ERROR_CLASS_GOVERNED_CONFLICT` =
   "governed conflict — ..." (SPACE, no underscore) — NOT the raw "governed_conflict:" marker. If the
   §2.5-correct build raises the fixed label, `"governed_conflict" in str(...)` is FALSE → the pin is
   UNSATISFIABLE on a correct §2.5 build (a C-DEF). The contract was graded/satisfiability-checked at
   b2f9b0e (BEFORE the §2.5 addendum at 9a42ef4) under the author's OWN Reading-A wording. MUST VERIFY.
2. CANDIDATE (task 2, §2.5 unit pin): no `_txn`-classification UNIT pin
   (test_surreal_store.py::TestDomainRejectionErrorType extension). Determine if the OUTCOME pins catch
   a wrong `_txn` classification. Related to (1).
3. CANDIDATE (task 3 render coverage, P1c REACH): render-bound coverage pin
   `test_the_recall_render_takes_the_subject_and_calls_render_subject_bound` hardcodes the ONE render
   name `_render_recalled_memories` — NOT derived from `partition_tools_by_population` as §3.3 pin (ii)
   specifies. Reach is a hidden constant. Assess severity given i-b has only one governed read render.
## CONFIRMED FINDING F1 (§2.5 axis — BLOCKER / C-DEF) — the rescope pin is UNSATISFIABLE against §2.5
Scratch: `/tmp/lore-adv-63bib` (provenance asserted — `loremaster.__file__` =
`/tmp/lore-adv-63bib/loremaster/loremaster/__init__.py`). Built the §2.5-compliant `_txn`
classification (marker branch → fixed label `_ERROR_CLASS_GOVERNED_CONFLICT` = "governed conflict — …",
`_domain_rejection_error` → `TxnGovernedConflictError` at the `execute_transaction` raise site).
Probe `loremaster/tests/test_adv_probe_txn_marker.py` reproduces the rescope pin's exact
`execute_transaction` call + assertion, with a HEAD-shape control. Result (2 passed):
```
[PROBE] type=TxnGovernedConflictError
[PROBE] message='...was rejected (governed conflict — the guarded row moved between authorization
        and the write; re-authorize and re-issue); see the server log...'
[PROBE] pin-assert  'governed_conflict' in msg = False   ← the rescope pin's assertion FAILS
[PROBE] label-space 'governed conflict' in msg = True
[PROBE] isinstance TxnGovernedConflictError   = True
[PROBE] rider-ii bans: 'probe_pred' in msg = False · 'memory' in msg = False   (hygiene holds)
[PROBE] successor rolled back (no row) = True
[CONTROL] type=SurrealStoreError · message='...(unspecified rejection)...'
[CONTROL] 'governed_conflict' in msg = False · 'governed conflict' in msg = False   (discriminates)
```
`test_a_rescope_on_the_composed_transaction_conflicts_and_rolls_back` asserts
`"governed_conflict" in str(conflict.value)` (UNDERSCORE). §2.5 rules the raised message is the FIXED
label "governed conflict" (SPACE) and rider ii FORBIDS the raw marker/suffix in the message. So a
§2.5-compliant build can NEVER satisfy this pin — the ONLY way to make "governed_conflict" (underscore)
appear is to leak the raw THROW text, which violates §2.5 hygiene. The pin traps the builder: red at
HEAD (unbuilt seam), red on the correct §2.5 build. The contract author's 70/0 satisfiability (graded
b2f9b0e, BEFORE the §2.5 addendum 9a42ef4) used their own Reading-A label — NOT §2.5's ruled fixed label.

- Next: wrong-build matrix (#441 behavioural, #436, #437, F5); QUANTIFIER attack on #436;
  satisfiability of the fidelity+render halves.
