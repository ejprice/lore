# REPORT — delta-adversary-asub-6 (contract-adversary, A-SUB delta: §12.8 skip-coverage → L1 RUNTIME `report.escapes`)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK (read first)

- **State:** done. Read-only adversary; wrote ONLY this report. All probes in a FRESH
  `/tmp/asub6-delta-a` (my own `scratch_copy.sh`, provenance-asserted, my OWN independent guard).
  MAIN repo touched ZERO files (git status = the 2 pre-existing edits, before and after).
- **VERDICT: A-SUB (§12.8) — CONTRACT INSUFFICIENT.** 1 BLOCKER (an **in-scope PARSE** survives the
  revised, runtime-sourced pin) + 1 coupled TRUST defect (a false-clear docstring claiming closure).
  This is NOT a reopen of the accepted #349 NON-parsing bound — the survivor **calls `ast.parse` 117×**
  and produces 117 ASTs; it is squarely in the operator's IN-SCOPE-parse set.
- **P1 HEADLINE — a routed-but-private whole-workspace `ast.parse(path.read_bytes())` survives the
  whole revised contract, per-file verdict GREEN, byte-for-byte the same as a correct routed build.**
  The L1 chokepoint IS spelling-agnostic (it recorded all 117 escapes) — but the NEW members-spanned
  DISCRIMINATOR drops every one of them, because a **bytes (or transformed) source cannot be resolved
  to a `.member`**, so `.member=""` for all 117, so `_whole_workspace_escape_sites` returns ∅. The
  six-defeats reach gap RECURRED ONE LEVEL DOWN: from the static source-name hand-list (delta-asub-5)
  to the discriminator's source-text member-attribution.
- **QUANTIFIER TABLE (P1b):** §5a. The load-bearing invariant "no `_ASUB_PARSE_SKIP` file parses the
  workspace UNROUTED, any spelling" is **claimed ∀-over-spellings; ACTUALLY guarded to spellings whose
  source the `.member` resolution can attribute (str, byte-identical to a workspace file).** Receipt:
  bytes/transformed survivor GREEN + text-source control RED (§2).
- **REACH TABLE (P1c):** §5b. `test_no_skip_set_file_parses_the_tree_unrouted` — reach of the
  member-attribution is a **hidden constant** (exact source-text/filename resolution), coverage of that
  attribution is **NOT a checked variable**, and `_whole_workspace_escape_sites` observes a **PROXY**
  (`.member`) that is silently empty for non-str/transformed sources → BLIND. Legs: EMPIRICAL
  (independent guard, driven survivors + 3 controls).
- **MISSING PIN (the test that should exist + the defect it catches):** §6. A positive control that
  drives a whole-workspace `ast.parse(read_bytes())` / `read_text()+normalize` scan in a skip file under
  the armed guard and asserts the pin **REDDENS** — currently GREEN. Defect: an unattributable in-scope
  whole-workspace parse (`member=""`) is silently dropped by `_whole_workspace_escape_sites` (fail-OPEN),
  so a skip file parsing the workspace unrouted via a bytes/transformed source passes the checked variable.
- **TRUST defect:** the pin docstring (lines 2216-2219) states *"an in-scope PARSE in ANY spelling is
  CLOSED HERE by L1's runtime observation — never pinned."* My probe proves that is FALSE for the
  bytes/transformed spellings → a false clear (same shape as delta-asub-5's #349 cross-reference).
- **Satisfiability (ask 1):** correct routed build → GREEN (parse_production_trees sanctioned, 0
  escapes); build-independent controls → 4 passed; the text-source whole-workspace survivor → RED(over)
  (positive control fires); single-package lorerunes scan → GREEN (C-DEF correctly AVOIDED — refinement A
  verified). No C-DEF. **But** the pin does not DISCRIMINATE a bytes/transformed survivor from correct.
- **Discriminator verdict (ask 3):** members-spanned **correctly FLAGS the whole-workspace derivation
  (spans 6 members → RED)** and **correctly does NOT false-flag the single-package lorerunes scan (1
  member → GREEN)** — refinement A is right, C-DEF avoided. Budget both-ways confirmed (over/dead/OK).
  Its dependency on `.member`, however, is the reach gap above.
- **Refinement B verdict (ask 4):** source-resolution is sound for `read_text()` str sources (the
  survivor's no-filename case IS attributed) but **NON-VACUOUSLY INCOMPLETE**: it silently returns "" for
  `read_bytes()` and for any pre-parse-transformed source — and the contract logic drops those, fail-open.
- **Packages considered:** none — stdlib `ast`/`sys`/`builtins`/`pathlib` + `_pytest.monkeypatch`, all
  reuse of the contract's own helpers + an independent minimal guard. No library supplies a
  "whole-workspace-vs-single-file parse discriminator." Verdict: bespoke-minimal (agrees design §12.5).
- **Graded:** working-tree `loremaster/tests/test_ast_reach_helpers.py` (uncommitted, reviser-asub-6's
  §12.8 revision) atop HEAD `4ceac32` · HEAD-at-report `4ceac32` · SAME.
- **Decisions-needed:** the missing pin is a FORK (operator's call, like delta-asub-5's): (A) CLOSE it —
  make member-attribution robust (decode bytes; fail-CLOSED on an unattributable workspace-site escape)
  — a design question because fail-closed can re-open the single-package C-DEF for a bytes/transformed
  §7 scan; or (B) PIN it honestly — an explicit operator ruling + a KNOWN_BOUND pin distinct from #349
  for "in-scope parse whose source the resolution cannot attribute" + the docstring correction.
- **Receipt pointers:** §1 satisfiability+controls · §2 the BLOCKER survivor (probe output) · §3 why the
  contract misses it (fail-open + attribution reach) · §4 not-#349 · §5 tables · §6 missing pin · §7
  provenance/scratch · Full probe record (commands + real output).

---

## §0 — Capability check
Full tool access; lore loaded (`ToolSearch "+lore"`); registered `delta-adversary-asub-6`
(session `2026-08-09-fix-344-345`, role adversary, model claude-opus-4-8); inbox drained empty. No brief
demand unmet. Work was AST + runtime construction in a scratch copy + direct source reads cited by
symbol — no lore structure-query fallback to flag. Writable set honoured: this report only in the main
repo; all mutation lives in `/tmp/asub6-delta-a`.

## §1 — SATISFIABILITY (ask 1) — the correct build is GREEN; the controls fire; ONE C-DEF is correctly avoided
Independent guard in `/tmp/asub6-delta-a` (my own, faithful to `_install_parse_guard_fn`'s REQUIRED-API,
HARDENED member resolution = filename-when-present + source-text fallback — the strongest reasonable
builder, per reviser-asub-6 §5). Driving each scan through the CONTRACT's own helpers
(`_whole_workspace_escape_sites`, `_skip_files_parsing_whole_workspace`, `_skip_budget_verdict`):

| scan driven (in a skip file) | compiles | member values | `_whole_workspace_escape_sites` | per-file pin verdict | expected |
|---|---|---|---|---|---|
| `parse_production_trees()` (ROUTED, correct) | 113 | — (sanctioned) | 0 flagged | **GREEN** | GREEN ✓ |
| whole-workspace `read_text` parse (POSITIVE control) | 117 | 6 members | **1 flagged** | **RED(over)** | RED ✓ |
| single-package lorerunes `read_text` parse (C-DEF check) | 2 | `[lorerunes]` (1) | 0 flagged | **GREEN** | GREEN ✓ |

Build-independent control tests: `test_the_skip_coverage_discrimination_fires_and_discriminates`,
`test_the_skip_set_is_non_empty_and_scoped_to_the_migration_set`,
`test_the_parse_skip_allowlist_carries_no_dead_entries`, `TestAsubNonParsingTreeWalkKnownBound349`
→ **4 passed** (scratch, `-p no:xdist`). **No C-DEF** (nothing spuriously RED on the correct build); the
members-spanned refinement (A) is VERIFIED: the single-package scan spans ONE member → correctly
EXCLUDED, where a raw compile-count≥2 proxy would have false-flagged it (2 compiles). The discriminator
FLAGS the whole-workspace derivation (6 members) and PASSES the single-package scan — exactly the
brief's ask 3 (a) and (b).

## §2 — THE BLOCKER (P1): a whole-workspace `ast.parse(read_bytes())` survives the revised contract
Same guard, same skip file (`test_backoff_seam.py`, budget 0), same CONTRACT helpers — two more driven
scans, each an **in-scope PARSE** (calls `ast.parse`, produces ASTs):

| scan driven | compiles | member values | `_whole_workspace_escape_sites` | per-file pin verdict | expected |
|---|---|---|---|---|---|
| whole-workspace `ast.parse(path.read_bytes())` | **117** | `['']` (ALL empty) | **0 flagged** | **GREEN** | RED — **MISMATCH** |
| whole-workspace `ast.parse(read_text()+normalize)` | **117** | `['']` (ALL empty) | **0 flagged** | **GREEN** | RED — **MISMATCH** |

Both survivors are DRIVEN (`read_bytes` ∈ `_FILE_READ_CALL_NAMES` ⊆ `_REACH_SCAN_SIGNAL_CALL_NAMES`, so
`_is_scan_candidate` reaches them — 117 compiles intercepted, so the guard SAW them and per-file
anti-vacuity #136 is satisfied), and RECORDED (117 escapes each). They are not flagged for ONE reason:
**every escape carries `member=""`.** `ast.parse` accepts a `bytes` source (the survivor passes no
`filename` → `<unknown>`), so the source-text map misses it; the normalize survivor mutates the text
before parse, so it byte-mismatches the map. The CONTRACT's `_whole_workspace_escape_sites`
(lines 1019-1024) then does `if member:` and silently DROPS every empty-member escape — fail-OPEN — so
the site never reaches "spans ≥2 members" and is never flagged. Per-file verdict `_skip_budget_verdict(0, 0)`
→ `None` → GREEN.

This is delta-adversary-asub-5's BLOCKER class **still open**, one spelling deeper: not the split-leg
(that IS now caught — see §Full-probe text control), but a source the `.member` attribution cannot key.

**Realism / threat model (§12.7.1):** `ast.parse(path.read_bytes())` is a mainstream, documented idiom
(bytes lets `ast.parse` honour the file's own coding cookie — arguably MORE correct than a fixed
`read_text(encoding="utf-8")`). Normalizing line-endings / stripping a BOM before parse is equally
ordinary. Both are HONEST-DEVELOPER doors, not obfuscation — the same side of the threat-model line as
delta-asub-5's split-leg (which the design accepted as a defect to close), and the opposite side from
#137/#138/#349 (accepted clever-attacker / non-parsing bounds).

## §3 — WHY THE CONTRACT MISSES IT (the attribution reach, a hidden constant)
The §12.8 fix correctly moved OFF the static 3-name source hand-list ONTO L1's `compile` chokepoint,
which is genuinely spelling-agnostic — the guard recorded all 117 bytes-source compiles. **But the NEW
members-spanned discriminator re-introduced a hidden-constant reach one level down.** To distinguish a
whole-workspace enumeration (≥2 members) from a legit single-package scan (1 member — the §7 non-adopter
the C-DEF fix protects), the discriminator MUST attribute each compile to a member. With no `filename`
(the survivor's premise, correctly noted in §12.8.3), the only signal is the source TEXT — and that
attribution silently yields "" for:
- a **bytes** source (no str-map key matches; `ast.parse`/`compile` accept bytes);
- a **transformed** source (normalize / strip BOM / concat before parse);
- (and, structurally, any workspace-site parse whose source is not byte-identical to a stored file).

There is NO checked variable asserting that every non-sanctioned escape from a driven workspace scan got
a NON-empty member — coverage of the attribution is not measured. And `_whole_workspace_escape_sites`
fails OPEN on the ones it can't attribute (`if member:` drops them). So the discriminator certifies only
the escapes it can key; the rest are silently exempt. This is INSTRUMENT-0 / the six-defeats shape
exactly: *a guard certifies only the sites it can attribute, and its reach is a hidden constant.*

## §4 — THIS IS NOT #349 (the operator's accepted bound is untouched)
#349 = a NON-parsing tree walk (no `ast.parse`/`compile`, no AST, no chokepoint). Both survivors call
`ast.parse` 117× and produce 117 ASTs → 117 `PyCF_ONLY_AST` compiles at the chokepoint. They are
definitively IN-SCOPE per the operator ruling ("Only IN-SCOPE PARSES (produce an AST, any spelling) are
to be closed here"). `TestAsubNonParsingTreeWalkKnownBound349` remains honest and passing (§1); the
false clear is the SKIP-COVERAGE docstring's claim of closing "ANY spelling", which these spellings
falsify.

## §5 — TABLES

### §5a — P1b QUANTIFIER TABLE (∀-over-inputs vs guarded)

| invariant | ∀ or guarded | receipt |
|---|---|---|
| **no `_ASUB_PARSE_SKIP` file parses the workspace UNROUTED — every "routes its parse (budget 0)" reason enforced ∀ spellings** | **claimed ∀-over-spellings; ACTUALLY guarded to spellings whose source `.member` resolution attributes (str, byte-identical to a workspace file)** | **BLOCKER** — `read_bytes()`/normalize survivor GREEN (117 compiles, member all ""); text-source control RED(over); route GREEN; single-pkg GREEN (§1/§2). Guarded by ATTRIBUTABILITY-of-source, not by the parse property. |
| per-file ANTI-VACUITY (#136): the guard OBSERVED ≥1 compile while driving each skip file | ∀ over `_ASUB_PARSE_SKIP` | SOUND — construction: `intercepted==before → unobserved → RED`. (Note: satisfied by ANY driven compile in the file, incl. the survivor's own 117 — so it does NOT catch the survivor; it only catches a skip file whose parse is un-driven.) |
| global `require_observations`: ≥1 SANCTIONED parse across all driving | anti-vacuity (global) | SOUND but WEAK vs this survivor — `observed` is populated by the OTHER routed skip files, so a single bytes-survivor among routed peers passes (route drive → observed=1, §1). |
| single-package (1-member) scan is NOT charged as whole-workspace | ∀ over §7 non-adopter scans | SOUND — refinement A verified (lorerunes scan → 0 flagged, §1). C-DEF avoided. |
| skip set non-empty ∧ ⊆ `_MIGRATION_SET`; no dead entries | anti-vacuity / self-cleaning | SOUND (4 passed, §1). |
| #349 NON-parsing-walk bound pinned | guarded to the synthetic non-parsing walk | SOUND & HONEST as a non-parsing pin (passes + positive control); the skip-coverage docstring's "ANY spelling closed" over-claims relative to it AND to L1 (trust defect). |
| L1 escape gate / L2 lint / ALL-set / rider / comms-footer | unchanged from prior passes | not re-graded — outside the §12.8 delta; carried adversary-SOUND (delta-asub-3/-4/-5). |

### §5b — P1c REACH TABLE (§12.8 instruments)

| instrument | reach set | DERIVED / hidden-constant | coverage a checked var | effect vs proxy | one-source (mutation) | verdict | legs |
|---|---|---|---|---|---|---|---|
| `test_no_skip_set_file_parses_the_tree_unrouted` (the checked variable) | driven `_drivable_scan_candidates` × `report.escapes` **whose `.member` resolves** | driving reach DERIVED (broad `_is_scan_candidate`), but the **member-attribution reach is a HIDDEN CONSTANT** (exact source-text / filename) | **NO** — nothing asserts every non-sanctioned workspace-site escape got a non-empty member | **PROXY** — `.member` proxies "which file compiled"; silently "" for bytes/transformed source | n/a | **BLIND to an unattributable in-scope PARSE (BLOCKER)** | EMPIRICAL (independent guard; bytes+normalize survivors GREEN; text control RED; pkg control GREEN; route GREEN) |
| `_whole_workspace_escape_sites` (members-spanned discriminator) | escapes grouped by `.site`, members via `.member` | DERIVED from `.member`; **fails OPEN** (`if member:` drops empty) | no | PROXY (`.member`); empty ⇒ dropped | n/a | correct for attributable sources; **fail-open on unattributable → part of the BLOCKER** | EMPIRICAL |
| `_skip_files_parsing_whole_workspace` / `_skip_budget_verdict` | whole-workspace sites ∩ skip files; both-ways budget | DERIVED (basename ∈ skip set); budget checked over/dead/OK | self-cleaning (dead) | STATIC over escapes | n/a | SOUND (over/dead/OK verified, §Full-probe) — inherits the discriminator's blindness | EMPIRICAL |
| per-file anti-vacuity (#136) + global `require_observations` | intercepted-delta per file; observed globally | DERIVED | YES per-file | effect (a compile happened) | n/a | SOUND as blindness guards; do NOT catch THIS survivor (it is driven & the peers route) | EMPIRICAL |
| `TestAsubNonParsingTreeWalkKnownBound349` | synthetic non-parsing walk + parsing positive control | DERIVED | positive control fires | STATIC | n/a | SOUND & HONEST as a non-parsing-walk pin | EMPIRICAL (1 passed) |

**Legs:** EMPIRICAL for every A-SUB row — an independent `scratch_copy.sh` build with my OWN guard (not
the reviser's), the 3 correct-build controls (route/pkg/text) firing as expected, and the two survivors
run through the CONTRACT's own helpers. Every negative paired with a positive control (text-source
whole-workspace → RED; single-package → GREEN; routed → GREEN, observed=1), so the probe demonstrably
SEES a real whole-workspace parse and DISTINGUISHES a single-package one — the survivors slip through for
the `member=""` reason, not a broken probe (P0).

## §6 — THE MISSING PIN (the test that should exist + the defect it catches)
**BLOCKER — the skip-coverage checked variable must flag an in-scope whole-workspace PARSE whose source
the `.member` resolution cannot attribute (bytes / transformed source), OR that class must be honestly
pinned as a bound distinct from #349 with an explicit operator ruling.** A FORK (operator's call, like
delta-asub-5's):

- **PIN A (close it):** add `test_the_skip_coverage_flags_an_unattributable_source_whole_workspace_parse`
  — drive a whole-workspace `ast.parse(path.read_bytes())` (and a `read_text()+normalize`) scan in a
  skip file under the armed guard and assert the pin REDDENS. Closing it requires BOTH: (i) the guard
  attribute non-str sources (decode bytes before the source-map lookup — a bytes source of a verbatim
  workspace file decodes to the stored text) AND some fail-CLOSED handling of a genuinely-transformed
  source (an escape from a workspace `.py` SITE with an unresolved member is a whole-workspace-parse
  SUSPECT, not a silent pass); (ii) `_whole_workspace_escape_sites` stop dropping empty-member escapes
  silently. ⚠ This is a DESIGN question, not a patch: fail-closed can re-open the single-package C-DEF
  for a §7 scan that reads bytes/transforms (e.g. secret_typing's lorerunes scan), so the closure needs
  the same members-vs-attributability care the C-DEF fix needed — route it back to CONTRACT/design.
- **PIN B (pin it honestly):** if the operator rules the unattributable-source in-scope parse an
  accepted bound, add a `test_asub_unattributable_source_parse_is_a_KNOWN_BOUND` (pin-the-miss,
  #137/#138 idiom) classifying it as an IN-SCOPE parse the member-attribution misses — DISTINCT from
  #349 — with its own re-open trigger, AND correct the skip-coverage docstring (lines 2216-2219): it
  currently claims *"an in-scope PARSE in ANY spelling is CLOSED HERE … never pinned"*, which the
  bytes/transformed spellings falsify (a false clear).

*Also (cheap, independent of the fork):* the build-independent control
`test_the_skip_coverage_discrimination_fires_and_discriminates` should gain a leg for `member=""` at a
workspace site — it currently only feeds PRE-ATTRIBUTED synthetic escapes, so it is blind by
construction to the exact case that survives.

*Why the current contract misses it:* the discriminator keys whole-workspace-ness on `.member`;
`.member` is resolved from source text (no filename); a bytes/transformed source resolves to "";
`_whole_workspace_escape_sites` drops empty-member escapes (fail-open). No instrument requires the
attribution to be COMPLETE.

*Defect it catches:* a routed-but-private in-scope whole-workspace `ast.parse(read_bytes())` /
`read_text()+normalize` in a skip file — currently GREEN (per-file verdict), indistinguishable from a
correct routed build.

## §7 — Provenance (#140) + scratch
- `loremaster.__file__ = /tmp/asub6-delta-a/loremaster/loremaster/__init__.py` (asserted
  `is_relative_to('/tmp/asub6-delta-a')` at probe start — see Full-probe output line 1).
- `/tmp/asub6-delta-a` is my OWN `scripts/scratch_copy.sh` tree (provenance-asserted at creation,
  `--all-packages`). Mutations were ADDITIVE and confined to it: an independent guard appended to
  `_logging_fixtures.py`, four nullary scan candidates appended to `test_backoff_seam.py`. The MAIN repo
  `git status` = only the 2 pre-existing edits (`test_ast_reach_helpers.py`, `scripts/test_wave_gate.py`),
  before and after. Recommend the lead discard `/tmp/asub6-delta-a` (and the reviser's
  `/tmp/asub6-scratch-a`, `/tmp/asub3-scr-a`) — all under `/tmp`, disposable, no main-repo footprint.
- Probe scripts are pasted VERBATIM below (brief-base §1: an instrument establishing a load-bearing
  claim is a deliverable, not scratch).

---

## Full probe record (commands + real output)

### Probe 1 — the guard I appended to scratch `_logging_fixtures.py` (independent, faithful, HARDENED)
```python
# member resolution = filename-when-present, then source-TEXT fallback (the strongest reasonable
# builder, per reviser-asub-6 §5). Escape carries .site (caller-frame repo-rel :line in fn()),
# .primitive, .member. Sanctioned iff a parse_production_trees frame is above the compile.
def guarded_compile(source, filename="<unknown>", mode="exec", flags=0, *args, **kwargs):
    result = real_compile(source, filename, mode, flags, *args, **kwargs)
    if flags & ast.PyCF_ONLY_AST:
        report.intercepted += 1
        # ... walk frames: sanctioned if parse_production_trees above; else offender_site from
        #     the first workspace .py caller frame ...
        if sanctioned:
            report.observed.add("_logging_fixtures.py in parse_production_trees()")
        elif offender_site is not None:
            member = ""
            if filename and filename != "<unknown>":
                member = _member_of_path(filename)       # HARDENED: filename when present
            if not member and isinstance(source, str):
                member = source_member.get(source, "")   # source-text fallback (spec's form)
            report.escapes.append(_Escape(site=offender_site, primitive=primitive, member=member))
    return result
```

### Probe 2 — the four scan candidates appended to scratch `test_backoff_seam.py`
```python
def _dasub_text_scan():     # whole-workspace read_text  -> POSITIVE control (must RED)
    for label, path in production_sources(): trees[label] = ast.parse(path.read_text(encoding="utf-8"))
def _dasub_bytes_scan():    # whole-workspace read_bytes  -> in-scope PARSE (SUSPECTED SURVIVOR)
    for label, path in production_sources(): trees[label] = ast.parse(path.read_bytes())
def _dasub_normalized_scan(): # whole-workspace read_text + normalize -> in-scope PARSE (SURVIVOR)
    for label, path in production_sources(): trees[label] = ast.parse(path.read_text(...).replace("\r\n","\n")+"\n")
def _dasub_pkg_scan():      # lorerunes single-package read_text -> C-DEF check (must GREEN)
    for label, root in workspace_roots():
        if root.name != "lorerunes": continue
        for path in sorted(root.rglob("*.py")): ... ast.parse(path.read_text(encoding="utf-8"))
```

### Probe 3 — driving each through the CONTRACT's own helpers (`/tmp/asub6_delta_probe.py`)
```
[provenance] loremaster.__file__ = /tmp/asub6-delta-a/loremaster/loremaster/__init__.py
[setup] test_backoff_seam.py declared budget = 0

###### PART A: the discriminator, driven through the CONTRACT helpers ######
=== text_scan (whole-workspace read_text) — POSITIVE CONTROL ===
  compiles intercepted : 117
  escapes recorded     : 117   member values seen: ['loremaster','lorerunes','lorescribe','loresigil','scripts','skills']
  _whole_workspace_escape_sites -> 1 site(s) flagged
  attributed to test_backoff_seam.py: 1  -> budget-verdict='over'
  >>> PER-FILE PIN VERDICT: RED(over)   (expected RED)  >>> as expected
=== pkg_scan (lorerunes single-package read_text) — must stay GREEN (C-DEF check) ===
  compiles intercepted : 2
  escapes recorded     : 2   member values seen: ['lorerunes']
  _whole_workspace_escape_sites -> 0 site(s) flagged
  >>> PER-FILE PIN VERDICT: GREEN   (expected GREEN)  >>> as expected
=== parse_production_trees (ROUTED) — correct build must be GREEN ===
  compiles intercepted : 113
  escapes recorded     : 0   member values seen: []
  observed(sanctioned) : 1
  >>> PER-FILE PIN VERDICT: GREEN   (expected GREEN)  >>> as expected

###### PART B: the suspected in-scope-PARSE survivors ######
=== bytes_scan (whole-workspace read_bytes) — IN-SCOPE PARSE ===
  compiles intercepted : 117
  escapes recorded     : 117   member values seen: ['']
  _whole_workspace_escape_sites -> 0 site(s) flagged
  attributed to test_backoff_seam.py: 0  -> budget-verdict=None
  >>> PER-FILE PIN VERDICT: GREEN   (expected RED)  >>> *** MISMATCH ***
=== normalized_scan (whole-workspace read_text+normalize) — IN-SCOPE PARSE ===
  compiles intercepted : 117
  escapes recorded     : 117   member values seen: ['']
  _whole_workspace_escape_sites -> 0 site(s) flagged
  >>> PER-FILE PIN VERDICT: GREEN   (expected RED)  >>> *** MISMATCH ***

###### SUMMARY ######
  text (control, should RED)   : RED(over)
  pkg  (C-DEF, should GREEN)   : GREEN
  route(correct, should GREEN) : GREEN
  bytes(survivor?, should RED) : GREEN        <-- BLOCKER
  norm (survivor?, should RED) : GREEN        <-- BLOCKER
```

### Probe 4 — build-independent controls + #349 (scratch, real contract file)
```
$ cd /tmp/asub6-delta-a && ./.venv/bin/python -m pytest \
    ...TestTheParseSkipSetIsACheckedVariable::test_the_skip_coverage_discrimination_fires_and_discriminates \
    ...::test_the_skip_set_is_non_empty_and_scoped_to_the_migration_set \
    ...::test_the_parse_skip_allowlist_carries_no_dead_entries \
    ...TestAsubNonParsingTreeWalkKnownBound349 -q -p no:xdist
4 passed in 1.00s
```

## Verdict

**A-SUB (§12.8): CONTRACT INSUFFICIENT.** The re-sourcing to L1's runtime `report.escapes` is a real
improvement — the `compile` chokepoint is spelling-agnostic and the delta-asub-5 split-leg / text-source
survivor now REDs, refinement A (members-spanned) correctly avoids the lorerunes single-package C-DEF,
and refinement B correctly attributes the no-filename `read_text()` case. **But the new members-spanned
discriminator moved the six-defeats reach gap one level down into the `.member` attribution:** a
routed-but-private whole-workspace `ast.parse(path.read_bytes())` (or `read_text()+normalize`) — an
IN-SCOPE parse, driven, and fully recorded by the guard (117 escapes) — passes the checked variable
GREEN, because a bytes/transformed source resolves to `member=""` and `_whole_workspace_escape_sites`
silently drops empty-member escapes (fail-open). This is delta-adversary-asub-5's BLOCKER class still
open for the unattributable-source spellings — NOT the accepted #349 non-parsing tail (the survivor calls
`ast.parse` and produces ASTs). The pin's docstring compounds it with a false clear ("an in-scope PARSE
in ANY spelling is CLOSED HERE … never pinned"). Close it by making member-attribution complete +
fail-closed (a design fork — it can re-open the single-package C-DEF), OR pin it honestly as an in-scope
bound distinct from #349 with an operator ruling and a docstring correction. It currently does neither.
