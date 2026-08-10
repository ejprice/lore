# REPORT — delta-adversary-asub-5 (contract-adversary, FINAL A-SUB delta: §12.7 skip→checked-variable + #349 pinned bound)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK (read first)

- **State:** done. Read-only adversary; wrote ONLY this report. All probes in `/tmp/asub3-scr-a`
  (disposable scratch); MAIN repo touched ZERO files (git status = only the 3 pre-existing edits).
- **VERDICT: A-SUB (F4/§12.7) — CONTRACT INSUFFICIENT.** 1 BLOCKER (an **in-scope PARSE** survives)
  + 1 coupled TRUST defect (a false-clear cross-reference to #349). This is NOT a reopen of the
  accepted #349 non-parsing bound — the survivor **calls `ast.parse`** (test_backoff_seam.py:780).
- **P1 HEADLINE — a routed-but-private IN-SCOPE parse survives the whole revised contract, 49 passed /
  4 skipped, byte-identical to a correct build.** backoff routes an unconsumed `parse_production_trees`
  decoy while its REAL scan parses the whole workspace privately via a **split-leg** (`_production_python_files()`→`production_sources()` + `ast.parse` at line 780). This is the delta-adversary-asub-4
  BLOCKER, STILL OPEN for the split-leg / rglob / os.walk-**parse** spellings.
- **Why (the reach gap, measured):** `test_no_skip_set_file_parses_the_tree_unrouted` reuses the STATIC
  `_all_workspace_parse_sites` (parse-primitive **+ a whole-workspace SOURCE NAME** in ONE function).
  That vocab is a 3-name hand-list (`production_sources`/`workspace_roots`/`parse_production_trees`), so
  it enforces routing for exactly **one spelling**. At HEAD, **3 of the 4 skip files parse unrouted**
  (backoff split-leg, secret_typing split-leg+rglob, comms_footer rglob `_scan`) and the pin flags **NONE
  of them** — only secret_leak's single-function `_production_function_names`.
- **The reviser's "correct/migrated reference build" IS the survivor for backoff** — its skip-coverage
  GREEN is by BLINDNESS, not correctness (`_all_workspace_parse_sites()=={parse_production_trees}` because
  backoff's split-leg parse is invisible, not because backoff routes).
- **TRUST DEFECT:** the skip-coverage docstring says the split-leg/os.walk-**parse** tail *"is the #349
  pinned bound (`TestAsubNonParsingTreeWalkKnownBound349`)."* #349 pins **NON-parsing** walks; an in-scope
  PARSE in a disguised spelling is neither caught nor honestly pinned → a false clear (a reader acting
  without checking believes the hole is a deliberately-pinned bound; it isn't).
- **#349 pin honesty (ask 4): the pin ITSELF is HONEST** — passes with a real positive control (the
  PARSING rglob variant IS flagged), anti-triviality (`walk`∈calls ∧ no parse primitive), reddens if L2
  broadens, carries the 3 re-open triggers. NOT vacuous. The problem is the skip-coverage docstring's
  cross-reference TO it, not the pin.
- **CLOSURE IS REUSE, NOT ROUND-6:** the design §12.7.2 offered TWO impls (`_all_workspace_parse_sites`
  **OR** the runtime compile-chokepoint observation). The reviser picked the static one. I PROVED the
  already-built L1 guard RECORDS backoff's escape (`test_backoff_seam.py:780`), so a skip-coverage pin
  driving each skip file under the armed guard closes the split-leg/rglob/os.walk-parse survivor by REUSE.
- **MISSING PIN:** either (A, close) route the skip-coverage checked-variable through L1's RUNTIME
  observation; or (B, pin honestly) an explicit operator ruling + a `KNOWN_BOUND` pin distinct from #349
  for the in-scope disguised-spelling parse + a docstring correction. Currently the contract does NEITHER.
- **Satisfiability (ask 1):** migrated build → 4 skip-coverage pins + #349 = **5 passed**; HEAD →
  `test_no_skip_set_file_parses_the_tree_unrouted` **RED-for-right-reason** naming secret_leak. No C-DEF
  (no spurious RED). But the reference build's *correctness* for backoff is false (see above).
- **Packages considered:** none — stdlib `ast`/`sys` + `_pytest.monkeypatch` only; all reuse of the
  contract's own functions + the built L1 guard. No external library supplies a "whole-workspace-parse
  vs single-file-parse discriminator." Verdict: bespoke-minimal (agrees the design's §12.5).
- **Graded:** working-tree `test_ast_reach_helpers.py` (uncommitted) atop `481b1c1` · HEAD-at-report
  `481b1c1` · SAME (HEAD moved 2fe81ba→481b1c1 mid-run, a docs-only commit to instrument **G**; it did
  NOT touch my grading target — re-run static probe identical).
- **Provenance (#140):** reference build `loremaster.__file__ = /tmp/asub3-scr-a/loremaster/loremaster/__init__.py`
  (asserted inside scratch). Every mutation `cp -a`-backed + restored byte-exact (backoff.ORIG cmp clean).
- **Decisions-needed:** (1) the missing pin above (close-via-reuse vs honest-pinned-bound — an operator
  scope call, because only the NON-parsing walk has been ruled out of scope, not the disguised-spelling
  PARSE); (2) I CONCUR with reviser DECISION-NEEDED #1 (backoff DOES parse — the design's example was
  wrong); reviser DECISION-NEEDED #2 honestly flagged this residual but its disposition ("operator
  implicitly accepts") is NOT established.
- **Receipt pointers:** §1 satisfiability · §2 the P1 survivor · §3 the reach gap at HEAD · §4 the
  runtime-closure proof · §5 tables · §6 the missing pin · §7 #349 honesty · §8 provenance.

---

## §0 — Capability check
Full tool access; scratch reference build `/tmp/asub3-scr-a` present, provenance-asserted, all helpers
built (`parse_production_trees`, `assert_scan_reached_every_member`, `install_parse_guard`,
`_rebind_everywhere`), 5 adopters "migrated" (backoff/secret_typing/comms_footer as decoy+private per
delta-asub-4). No brief demand unmet. lore/grep fallback: work was AST + runtime construction in the
scratch + direct source reads (cited by symbol); no lore structure-query needed, so none to flag.

## §1 — SATISFIABILITY (ask 1) — the pins are satisfiable; the "correct build" is not correct for backoff

**Migrated reference build — the 4 skip-coverage pins + the #349 pin GREEN:**
```
$ ./.venv/bin/python -m pytest \
    test_ast_reach_helpers.py::TestTheParseSkipSetIsACheckedVariable \
    test_ast_reach_helpers.py::TestAsubNonParsingTreeWalkKnownBound349 -q -p no:xdist
5 passed in 0.89s
```
**HEAD (2fe81ba/481b1c1, un-migrated) — the skip-coverage pin RED-for-right-reason:**
```
FAILED ...TestTheParseSkipSetIsACheckedVariable::test_no_skip_set_file_parses_the_tree_unrouted
  AssertionError: these _ASUB_PARSE_SKIP files DIRECTLY parse the whole workspace UN-ROUTED ...:
      ['test_secret_leak_vectors.py::_production_function_names']
```
No C-DEF (no pin spuriously RED on the reference build). **BUT** the reference build is a survivor for
backoff (§2), so its skip-coverage GREEN is by blindness — a genuinely-correct build (backoff's real
scan routed) would ALSO be GREEN, so the pin is satisfiable either way; it simply does not DISCRIMINATE
the survivor from correct.

## §2 — THE BLOCKER (P1): an in-scope split-leg PARSE survives the whole contract

The scratch backoff (delta-asub-4's tree, unchanged) is the routing-not-sharing survivor:
```
loremaster/tests/test_backoff_seam.py
  159 def _production_python_files() -> list[Path]:      # SOURCE helper (nullary)
  179     return [path for _label, path in production_sources()]      # whole workspace
  771 def test_no_production_module_outside_the_allowlist_exponentiates_by_a_variable(self):
  775     for path in _production_python_files():
  780         tree = ast.parse(path.read_text(encoding="utf-8"))   # <-- PRIVATE whole-workspace PARSE
  981 def _asub_reference_trees():                        # the DECOY — routes, UNCONSUMED
        return parse_production_trees(include_scripts=True, include_skills=False)
```
`ast.parse` at line 780 → this is an **IN-SCOPE parse** (calls the parser), NOT the accepted non-parsing
os.walk tail. Running the **revised** contract against it:
```
$ ./.venv/bin/python -m pytest loremaster/tests/test_ast_reach_helpers.py -q -p no:xdist
49 passed, 4 skipped in 36.55s
```
Byte-identical verdict to a correct build. The skip-coverage checked-variable is GREEN on it:
```
# contract's own functions on the survivor build:
_all_workspace_parse_sites()          == {'_logging_fixtures.py::parse_production_trees'}
offending (fname in _ASUB_PARSE_SKIP) == []           # => test_no_skip_set_file_parses_the_tree_unrouted GREEN
_whole_tree_parse_offenders_in(backoff) == []         # L2 blind (split-leg: source in a separate fn)
```
Every layer is blind to backoff's line-780 parse: the rider SKIPS backoff (no nullary WS-tree fixture →
`assert backoff in _ASUB_PARSE_SKIP` → `pytest.skip`); the skip-coverage pin is GREEN (split-leg ∉ ALL-set);
L1's escape INVARIANT filters the method by return value (it returns None); L2 needs 3-legs-in-one-function
(split-leg evades); used-ness is satisfied by the decoy.

## §3 — THE REACH GAP, visible at HEAD (not only in a contrived build)

At HEAD **all four** `_ASUB_PARSE_SKIP` files parse the whole workspace UNROUTED (un-migrated), in four
spellings; the pin flags **one**:

| skip file | its real whole-workspace parse @ HEAD | spelling | in `_all_workspace_parse_sites`? | flagged? |
|---|---|---|---|---|
| test_secret_leak_vectors.py | `_production_function_names` (`production_sources()`+`ast.parse` in ONE fn) | single-function | **YES** | **YES** ✓ |
| test_backoff_seam.py | `test_no_production_module_...` ← `_production_python_files()`→`production_sources()` | split-leg | no | **no** |
| test_secret_typing.py | `_python_sources()` (`_SCANNED_MEMBERS`×rglob) fed to many `ast.parse` | split-leg + rglob | no | **no** |
| test_comms_footer.py | `_scan` (`_workspace_scan_roots`×`(root/member).rglob` + parse) | rglob-over-members | no | **no** |

`_all_workspace_parse_sites()` @ HEAD returns **only** `test_secret_leak_vectors.py::_production_function_names`
(measured — §Full-probe #1). So the pin's enforcement of the skip reason *"routes its parse; no fixture"*
holds for **1 of 4** skip files. The other three are trusted, not enforced.

**The discriminator is the SPELLING, not the property** — proven with a perturbation (P0, §5b): the SAME
backoff, given a *single-function* unrouted parse, reddens the pin; given its *split-leg* parse, does not.
Both parse the whole workspace unrouted; both are in-scope. This is the six-defeats shape one level down
(a guard keyed on a source-name hand-list, defeated by the spelling that hides the name).

## §4 — CLOSURE IS REUSE, NOT ROUND-6 (the runtime-observation proof)

The design §12.7.2 offered `_all_workspace_parse_sites` **OR** *"the runtime `compile`-chokepoint
observation."* The already-built L1 guard SEES what the static ALL-set cannot:
```
# arm install_parse_guard, drive backoff's _drivable_scan_candidates, inspect RAW report.escapes:
report.escapes naming test_backoff_seam.py:
   test_backoff_seam.py:780 in test_no_production_module_outside_the_allowlist_...()   <-- the survivor
   test_backoff_seam.py:885 in test_KNOWN_BOUND_a_multiplicative_backoff_evades_the_perimeter()  (synthetic, benign)
   test_backoff_seam.py:951 in test_the_shared_policy_is_backed_by_tenacity_not_a_hand_roll()     (single file, benign)
```
So a skip-coverage pin built on the runtime observation would catch the split-leg (line 780), the os.walk+
parse build, and comms_footer's rglob `_scan` — all by REUSE of the L1 guard, **no round-6 source-following
scanner**. ⚠ Honest caveat for whoever builds it: lines 885/951 are legitimate single-file/synthetic
parses, so the pin must discriminate a WHOLE-WORKSPACE escape (a site whose compiles span ≥2 members) from
a single-file one — the same `_is_workspace_tree_result`/`_members_spanned_by_keys` discrimination the
contract already performs; it is more than "any escape from a skip file." That non-triviality is the ONE
point that partially defends the reviser's caution — but the current static pin does not even attempt it.

## §5 — TABLES

### §5a — P1b QUANTIFIER TABLE (∀-over-inputs vs guarded)

| invariant | ∀ or guarded | receipt |
|---|---|---|
| **no `_ASUB_PARSE_SKIP` file parses the workspace UNROUTED (every "routes its parse" reason enforced)** | **claimed ∀ over skip files × spellings; ACTUALLY guarded to the single-function whole-workspace-SOURCE-NAME spelling** | **BLOCKER** — backoff split-leg survivor 49/4skip; @HEAD 1 of 4 flagged; injected single-function parse → RED (P0). Guarded by SPELLING, not by the property. |
| a fixtureless adopter cannot skip SILENTLY (rider `assert adopter in _ASUB_PARSE_SKIP` before `pytest.skip`) | ∀ over `_MIGRATION_SET` | SOUND — a new fixtureless adopter absent from the skip set reddens the rider (construction; the assert precedes the skip). Closes the "silent skip", but does NOT verify the disguised-spelling parse. |
| the skip allowlist carries no dead entries (file exists ∧ ∈ `_MIGRATION_SET` ∧ no nullary WS-tree fixture) | ∀ over `_ASUB_PARSE_SKIP` | SOUND — ran GREEN on scratch; self-cleaning (a skip file that gains a fixture goes dead). |
| the skip set is non-empty ∧ scoped to `_MIGRATION_SET` | anti-vacuity | SOUND (ran GREEN). |
| the #349 NON-parsing-walk bound is pinned (reddens if L2 broadens) | guarded to the synthetic non-parsing walk | SOUND as pin-the-miss (ran: passes + its positive control fires) — but its docstring is (correctly) about NON-parsing walks; the skip-coverage docstring's cross-reference OVER-reaches it (trust defect). |
| L1 / L2 / ALL-set / rider(anchored) / assert_scan_reached_every_member / comms-footer binding | unchanged from prior passes | not re-graded — out of the §12.7 delta scope; carried adversary-SOUND (delta-asub-3/-4/-b). |

### §5b — P1c REACH TABLE (per §12.7 instrument)

| instrument | reach set | DERIVED / hand-list | coverage a checked var | effect vs proxy | one-source (mutation) | verdict | legs |
|---|---|---|---|---|---|---|---|
| `test_no_skip_set_file_parses_the_tree_unrouted` | `_all_workspace_parse_sites()` ∩ `_ASUB_PARSE_SKIP` | parse-primitive DERIVED, but **whole-workspace SOURCE = a 3-name hand-list** (`_WHOLE_WORKSPACE_SOURCE_CALL_NAMES`) | anti-vacuity present (all_sites non-empty) | **PROXY** — "source-name in one function" proxies "parses the workspace"; split-leg/rglob/os.walk defeat it | n/a | **BLIND to disguised-spelling in-scope PARSE (BLOCKER)** | EMPIRICAL (survivor 49/4skip; @HEAD 1/4; P0 perturbation; runtime guard drive) |
| rider skip-gate (`assert adopter in _ASUB_PARSE_SKIP`) | `_MIGRATION_SET` fixtureless adopters | DERIVED (`_workspace_tree_fixtures` empty) | YES — a new fixtureless adopter reddens | STATIC | n/a | SOUND for "no silent skip"; does NOT prove no private parse | construction-inspection + rider ran (backoff skips) |
| `test_the_parse_skip_allowlist_carries_no_dead_entries` | `_ASUB_PARSE_SKIP` entries | DERIVED (exists ∧ member ∧ no fixture) | self-cleaning | STATIC | n/a | SOUND | EMPIRICAL (ran GREEN) |
| `test_the_skip_set_is_non_empty_and_scoped...` | `_ASUB_PARSE_SKIP` ⊆ `_MIGRATION_SET` | DERIVED | anti-vacuity | STATIC | n/a | SOUND | EMPIRICAL |
| `TestAsubNonParsingTreeWalkKnownBound349` | synthetic non-parsing os.walk + a parsing positive control | DERIVED (call-name analysis) | positive control fires | STATIC | n/a | SOUND & HONEST **as a non-parsing-walk pin**; does NOT cover in-scope parses (the misattribution is elsewhere) | EMPIRICAL (ran: pass + control) |

**Legs:** EMPIRICAL for every A-SUB row — the reference build, the survivor run (49/4skip), the @HEAD
reach table, the P0 single-function perturbation (RED, restored byte-exact), and the armed-guard drive of
backoff's candidates. Every negative paired with a positive control (single-function parse → RED; #349
positive control → the parsing variant IS flagged; runtime guard → it records line 780).

## §6 — THE MISSING PIN (the test that should exist + the defect it catches)

**BLOCKER — the skip-coverage checked-variable must see an in-scope PARSE in ANY spelling, OR the
disguised-spelling parse must be honestly pinned as a bound with an explicit operator ruling.** Two paths:

- **PIN A (close it, reuse — favoured by "REUSE > REINVENT, no new scanner"):** extend
  `test_no_skip_set_file_parses_the_tree_unrouted` to ALSO observe the RUNTIME `compile` chokepoint —
  arm `install_parse_guard`, drive each `_ASUB_PARSE_SKIP` file's `_drivable_scan_candidates`, and RED if
  any produces a **whole-workspace** private-parse escape (a site whose compiles span ≥2 declared members,
  with no `parse_production_trees` frame) from that file. *Catches:* backoff's `test_no_production_module_...`
  (guard records `test_backoff_seam.py:780`), the os.walk+parse build, comms_footer's rglob `_scan`. Reuses
  the built L1 guard; needs the whole-workspace-vs-single-file discriminator (§4 caveat).
- **PIN B (pin it honestly — favoured by the operator's "prefer a pinned bound"):** if the operator rules
  the disguised-spelling in-scope PARSE accepted-as-bound, add a `test_asub_disguised_spelling_parse_is_a_KNOWN_BOUND`
  (pin-the-miss, #137/#138 idiom) that classifies it as an **IN-SCOPE parse the static checked-variable
  misses — DISTINCT from #349's non-parsing bound** — with its own re-open trigger, AND correct the
  skip-coverage docstring's false *"is the #349 pinned bound"* attribution.

*Why the current contract misses it:* the checked-variable keys on a 3-name whole-workspace-source vocab
in-one-function; split-leg factors the source into a nullary helper, rglob/os.walk use names not in the
vocab. No instrument requires the REAL skip-file scan to route or be observed.

*Defect it catches:* a routed-but-private in-scope whole-workspace PARSE in a skip file (the
delta-adversary-asub-4 BLOCKER) — currently survives the full contract 49/4skip.

## §7 — #349 PIN HONESTY (ask 4) — the pin is honest; the CROSS-REFERENCE to it is the false clear

`TestAsubNonParsingTreeWalkKnownBound349.test_asub_nonparsing_tree_walk_is_a_KNOWN_BOUND_349` (ran: `1 passed`):
- **anti-triviality:** asserts the fixture IS a walk (`walk`∈call-names) AND genuinely non-parsing (no parse
  primitive → structurally invisible to L1's `compile` chokepoint). ✓
- **the bound:** L2 (`_whole_tree_parse_offenders_in`) does NOT flag the non-parsing walk. ✓
- **positive control (non-vacuity):** the PARSING rglob variant IS flagged (`==['_scan']`), so the bound is
  "non-parsing", not "the detector never fires". ✓
- **re-open triggers:** real drift / threat-model change / CI+root-audit #285; KNOWN-BOUND #349 message;
  "delete this pin if you close it deliberately." ✓
**Verdict: the #349 pin is a REAL deliberate-bound pin, not a vacuous pass.** The false clear is the
skip-coverage docstring citing #349 as covering the split-leg/os.walk-**parse** tail — #349 covers
NON-parsing walks only, so an in-scope PARSE in a disguised spelling is neither caught nor pinned by it.

## §8 — Reviser decisions (ask 2 concurrence) + provenance

- **DECISION-NEEDED #1 (backoff example reason factually wrong): I CONCUR.** backoff DOES parse the whole
  workspace (line 780). The design §12.7.2's *"does not parse the tree"* example and §12.7.4's characterisation
  of backoff as "non-parsing os.walk" are both FACTUALLY WRONG (backoff calls `ast.parse`). The reviser's
  corrected reasons are honest for a *correct* build. ⚠ Downstream consequence the correction did NOT close:
  if backoff PARSES, it is IN scope, so the design's resolution "backoff is out of scope (non-parsing)" is
  void, and the in-scope parse must be caught or honestly pinned — it is neither (§2).
- **DECISION-NEEDED #2 (single-function reach bound): honestly flagged, disposition NOT established.** The
  reviser correctly stated the split-leg/os.walk reach bound. But its claim that "the operator's ruling
  implicitly accepts" it conflates two rulings: the operator ruled the **NON-parsing walk** out of scope
  (#349); the operator has NOT ruled on an in-scope PARSE in a disguised spelling. That is the escalation
  this report surfaces.
- **Provenance (#140):** `loremaster.__file__ = /tmp/asub3-scr-a/loremaster/loremaster/__init__.py`
  (asserted `is_relative_to('/tmp/asub3-scr-a')`). Every mutation `cp -a`-backed (`/tmp/backoff_asub5.ORIG`)
  and restored byte-exact (`cmp` clean). MAIN repo `git status` = only the 3 pre-existing edits
  (`test_ast_reach_helpers.py`, `scripts/test_wave_gate.py`, and the now-committed design doc), before and
  after. `/tmp/asub3-scr-a` is delta-asub-3's disposable `scratch_copy.sh` tree; recommend the lead discard it.

---

## Full probe record (commands + real output)

1. **@HEAD static reach** — `_all_workspace_parse_sites()` = `{test_secret_leak_vectors.py::_production_function_names}`;
   `_whole_tree_parse_offenders_in`: anchored=`[_parse_production_trees]`, backoff=`[]`, secret_typing=`[the 2
   lorerunes single-pkg scans]`, secret_leak=`[_production_function_names]`, comms_footer=`[_scan]`.
   (`/tmp/asub5_static_probe.py`.)
2. **Scratch provenance + state** — `loremaster.__file__` inside scratch; helpers all built; adopters
   "migrated" (backoff=decoy+private split-leg, confirmed by grep of lines 159/179/775/780/981).
3. **Survivor static** (`/tmp/asub5_scratch_probe.py`) — on the migrated build `_all_workspace_parse_sites()`
   = `{parse_production_trees}`, offending = `[]` → skip-coverage GREEN, while backoff parses privately.
4. **Survivor full contract** — `pytest test_ast_reach_helpers.py -q -p no:xdist` → `49 passed, 4 skipped`.
5. **Runtime-closure proof** (`/tmp/asub5_runtime_fix.py`) — armed `install_parse_guard`, drove backoff's
   `_drivable_scan_candidates`; `report.escapes` names `test_backoff_seam.py:780` (+ benign 885/951).
6. **P0 perturbation** — injected a single-function `production_sources()`+`ast.parse` into backoff →
   `test_no_skip_set_file_parses_the_tree_unrouted` FAILED naming `test_backoff_seam.py::_asub_evil_single_function_parse`;
   restored byte-exact (`cmp` clean).
7. **Satisfiability** — migrated build: `TestTheParseSkipSetIsACheckedVariable` + `...KnownBound349` = `5 passed`;
   @HEAD skip-coverage pin FAILED naming `test_secret_leak_vectors.py::_production_function_names`.
8. **#349 pin** — `TestAsubNonParsingTreeWalkKnownBound349` → `1 passed` (with its parsing positive control).

## Verdict

**A-SUB (F4/§12.7): CONTRACT INSUFFICIENT.** The skip→checked-variable and #349 pin are individually
well-built, and the #349 non-parsing-walk bound is honestly pinned. But the skip-coverage checked-variable
reuses the STATIC `_all_workspace_parse_sites` (a 3-name whole-workspace-source vocab in one function), so
it enforces the "routes its parse" reason for exactly one spelling: a routed-but-private **in-scope PARSE**
in a split-leg / rglob-over-members / os.walk+`ast.parse` spelling survives the whole contract (49 passed /
4 skipped, byte-identical to correct), and at HEAD only 1 of the 4 un-migrated skip files is flagged. This
is the delta-adversary-asub-4 BLOCKER still open **for the parsing spellings** — NOT the accepted #349
non-parsing tail (the survivor calls `ast.parse` at test_backoff_seam.py:780). The contract papers over it
by attributing the hole to the #349 pin, which pins only non-parsing walks — a false clear. Close it by
routing the checked-variable through L1's already-built runtime observation (REUSE, proven to record line
780), OR pin it honestly as an in-scope bound distinct from #349 with an explicit operator ruling and a
docstring correction. It currently does neither.
