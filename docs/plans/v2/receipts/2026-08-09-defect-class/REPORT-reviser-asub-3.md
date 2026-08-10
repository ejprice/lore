# REPORT — reviser-asub-3 (A-SUB CONTRACT reviser, §12 un-defeatable-by-spelling)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done-with-deviations. Applied design §12 (re-read the SHARPENED §12.3/§12.5 at HEAD
  `1a5d9b3` per the lead's correction) to `loremaster/tests/test_ast_reach_helpers.py` (TEST-ONLY,
  single-file writable set — `git status` confirms ONLY that file changed).
- **3 layers + comms binding built:** L1 RUNTIME `builtins.compile` chokepoint gate (generalises the
  named module `loremaster/tests/_sdk_guard.py`, read in full); L2 AST lint REFRAMED off the `rglob`
  spelling → parse-primitive + file-read + directory-source; L3 ∀-mutation with the `_live_adopters()`
  call-existence proxy RETIRED (reach = declared set, L1 = completeness checked-var); §12.4 comms_footer
  scan↔mode binding PINNED.
- **⚠ COVERAGE BINDS TO THE ALL-SET, NOT THE OFFENDERS SET (the lead's crux correction, applied):**
  the reach-checked-variable is `test_every_whole_workspace_parse_site_was_watched_executing` over
  `_all_workspace_parse_sites()` — the parse-primitive TRUTH, NON-EMPTY on a clean build
  (`_logging_fixtures.py::parse_production_trees` always registers), asserting each site was OBSERVED
  executing. The offenders/escapes set is used ONLY by the *escape invariant* pin (a different concern).
  **My first draft's "the offender leg IS the completeness guard" was the v5 empty-on-clean trap; that
  is REPLACED.** Discrimination proven: a routed-but-UNDRIVEN whole-workspace parse site turns the
  coverage RED and NAMES it ("watched ≠ well-formed ≠ unexamined"); the v5 offenders-based form could not.
- **rglob-lint retired:** `_has_tree_parser_clone` (`{rglob,parse,read_text}`) → `_whole_tree_parse_offenders_in`.
- **Reused symbol (named):** `test_retry_seam._sdk_guard.install` / `GuardReport.require_observations`
  / its pos-neg controls / the plain-`def`-walks-at-CALL-time lesson — generalised SDK-connection →
  `builtins.compile`. `_rebind_everywhere` reused for L3.
- **compile↔ast.parse ROUTING (load-bearing, VERIFIED):** on Python 3.14.6 `ast.parse` routes
  through a monkeypatched `builtins.compile` and the `PyCF_ONLY_AST` flag arrives → wrapping
  `builtins.compile` ALONE suffices; NO need to also wrap `ast.parse`. Probe fenced in §A; a pos-control
  pin enshrines it against regression.
- **Survivor + fresh spellings ALL die; single-package spared:** on a full reference build the survivor
  (private `production_sources`+`ast.parse` + unconsumed decoy) is caught at L1+L2+L3 while used-ness
  PASSES (decoy defeats it — proof it is the genuine survivor); alias / os.walk / comprehension /
  direct-`compile` all caught at L1; a legitimate single-package scan is NOT flagged.
- **Satisfiability:** 46/46 pass on a complete reference build (scratch `/tmp/asub3-scr-a`,
  `loremaster.__file__ = /tmp/asub3-scr-a/loremaster/loremaster/__init__.py` — #140 clean). RED at
  HEAD = 32 (every one names the missing helper/guard/migration, right reason) / 14 build-independent
  controls green. mypy + ruff clean on the contract.
- **Packages considered:** stdlib `ast`/`sys`/`inspect`/`builtins` only — no library supplies a
  "no-unsanctioned-frame-above-a-primitive" runtime gate. Verdict `bespoke (minimal)`, generalising the
  in-repo retry-seam idiom (agrees with §12.5). Read: `test_retry_seam._sdk_guard` source in full.
- **Graded:** authored against HEAD `1a5d9b3` (working tree = HEAD + reviser-asub-2's uncommitted
  comms_footer pins) · HEAD-at-report `1a5d9b3` · SAME.
- **Decisions-needed (for the adversary/operator — see §D):** (1) L3 binds to the derivation's
  key-reflection, NOT §12.3's `assert_scan_reached_every_member` both-direction diff — deviation with
  rationale; (2) the §12.4 A↔B *purpose*-swap residual stays a cold-audit hand-check (§12.4 fallback);
  (3) EXTRACT the runtime-reach guard to shared test-support (≥2 users) — builder call, flagged.
- **Receipt pointers:** §A routing probe · §B what changed (symbols) · §C satisfiability + catching
  receipts · §D deviations/bounds/flags · scratch reference build at `/tmp/asub3-scr-a` (disposable).

---

## §A — The routing verification (the load-bearing claim, VERIFIED not assumed; #107 discipline)

§12.2/§12.3 assert `ast.parse` calls `compile(src, name, mode, PyCF_ONLY_AST)`. The brief made this a
LOAD-BEARING pos-control I OWE: prove `ast.parse` routes through a wrapped `builtins.compile` on THIS
Python, else the guard must ALSO wrap `ast.parse`. Probed directly (Python **3.14.6**):

```python
import ast, builtins
observed = []
_real = builtins.compile
def wrapper(source, filename, mode, flags=0, *a, **k):
    observed.append((filename, bool(flags & ast.PyCF_ONLY_AST)))
    return _real(source, filename, mode, flags, *a, **k)
builtins.compile = wrapper
try:
    ast.parse("x = 1", filename="probe_astparse.py")          # via ast.parse
    compile("y = 2", "probe_direct.py", "exec", ast.PyCF_ONLY_AST)  # direct
finally:
    builtins.compile = _real
# RESULT (3.14.6):
#   ast.parse routed through patched builtins.compile: True
#   PyCF_ONLY_AST flag arrived for the ast.parse call:  True
#   direct compile(...,PyCF_ONLY_AST) observed:         True
#   ast.parse source uses a bare `compile(` global:     True
```

**Verdict: wrapping `builtins.compile` ALONE suffices; the guard need NOT wrap `ast.parse`.** The
contract's `test_the_routing_verification_compile_AND_ast_parse_both_register` pin enshrines this: it
asserts BOTH primitives register as escapes, so a future Python change — or a build that fumbles the
`PyCF_ONLY_AST` filter — is caught, and the "also wrap ast.parse" instruction is in the failure text.

## §B — What changed (symbols, not line numbers)

**Retired (the mis-built spelling-keyed offender):**
- `_has_tree_parser_clone` (keyed on `{rglob, parse, read_text}` co-occurrence) → **`_whole_tree_parse_offenders_in`**,
  the OLD 3-leg shape with ONLY the directory leg broadened: parse-primitive `{parse,compile}` **AND**
  file-read `{read_text,read_bytes}` **AND** directory-source `{production_sources, workspace_roots,
  rglob, glob, iglob, iterdir}`. `walk` is DELIBERATELY EXCLUDED (`ast.walk` collision — measured: it
  false-flagged every AST-scanning file). This catches the delta-adversary survivor (which moved
  `rglob` *inside* `production_sources`) and spares single-file scanners.
- `_live_adopters()` ("test files that CALL the helper") — the call-existence proxy the DECOY defeated.
  L3 reach is now `_MIGRATION_SET` with L1 as the completeness checked-variable (§12.3's "equivalent
  acceptable form").

**Added (LAYER 1 — the runtime chokepoint, the load-bearing new catch):**
- `_install_parse_guard_fn()` — lazy accessor (the `_parse_production_trees_fn` discipline) for the
  builder-built `install_parse_guard`; tolerates home `_logging_fixtures` OR `_parse_guard`; RED at
  HEAD with a NAMED failure that specifies the exact required API + the generalise-from-`_sdk_guard`
  recipe. (Fixed a bug: it now tolerates a missing `_parse_guard` module rather than crashing on
  `ModuleNotFoundError`.)
- `class TestNoPrivateParseEscapesTheSanctionedParserAtRuntime` — 5 pins: the routing pos-control (§A),
  a private-`production_sources`-scan escape-is-named pos-control, a sanctioned-parse-allowed neg
  control, the `require_observations` anti-vacuity (#136), and the REACH/completeness pin (drives every
  declared adopter's scan candidates under the armed guard; any workspace-tree scanner that escapes is
  named file:line; `require_observations` + ≥1 sanctioned adopter = anti-vacuity).
- `_is_scan_candidate` / `_drivable_scan_candidates` (BROAD finder for L1 — keys on SOURCE/READ, not the
  aliasable parse, so an aliased-parse scan is still DRIVEN and the runtime guard catches it);
  `_members_spanned_by_keys` + `_is_workspace_tree_result` (spans ≥2 members ⇒ whole-workspace, robust to
  absolute or repo-relative keys — the discriminator that catches os.walk AND spares single-package scans).

**Reframed (LAYER 2):** `TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist` + the detector
controls re-keyed to `_whole_tree_parse_offenders_in`; added `test_the_reframed_detector_fires_on_the_rglob_LESS_survivor_shape`
(the survivor's shape must fire) + `test_the_clone_detector_does_not_fire_on_a_single_file_parser` (the
false-positive that would switch the gate off). `test_ast_reach_helpers.py` self-added to the allowlist
(its meta-scanners glob the test dir — that IS the offender machinery, not a production parse).

**Fixed (LAYER 3):** `_shared_parser_derivations` → `_nullary_derivations(filename, predicate)` +
`_tree_producing_derivations` (narrow, L3) + `_drivable_scan_candidates` (broad, L1). `TestSharingProvenByMutation`
now parametrises over `_MIGRATION_SET`, key-compares ONLY workspace-tree derivations (a `(count,hits)`
scan is SKIPPED, not a crash/false-fail), and reddens on keys-unchanged-under-drop.

**§12.4 (comms_footer scan↔mode binding):** `_comms_footer_scan_modes_by_scope` +
`test_each_include_tests_mode_binds_to_a_DISTINCT_scan_scope` — each `include_tests` mode must live in a
DISTINCT scan scope (catches collapse-into-one / a dropped mode). Sound `TestCommsFooterScansMigrateBehaviourPreserving`
pins (262/90 per-mode file sets) KEPT (adversary graded sound; my reference helper satisfies them).

## §C — Satisfiability + catching receipts (scratch `/tmp/asub3-scr-a`, provenance #140 clean)

Reference build = the 3 helpers (`parse_production_trees` with `include_tests`,
`assert_scan_reached_every_member`) + the runtime `install_parse_guard`/`ParseGuardReport` (generalising
`_sdk_guard`) added to `_logging_fixtures.py`, + all 5 adopters (anchored, backoff, secret_typing,
secret_leak, comms_footer) migrated onto the helper (secret_typing's `_SCANNED_MEMBERS` retired;
comms_footer's two scans routed through the helper in distinct scopes). `loremaster.__file__ =
/tmp/asub3-scr-a/loremaster/loremaster/__init__.py`.

| receipt | result |
|---|---|
| whole contract vs complete reference build | **47 passed / 0 failed** (satisfiable; no C-DEF trap) |
| whole contract @ HEAD (real tree) | **33 failed / 14 passed** — every RED names the missing helper/guard/migration |
| ALL-set on a clean build | `_all_workspace_parse_sites()` = `['_logging_fixtures.py::parse_production_trees']` — NON-EMPTY, so the coverage CAN fire (not the v5 empty-on-clean trap) |
| SURVIVOR planted in full reference (private `production_sources`+`ast.parse` + unconsumed decoy) | escape-invariant RED · L2 offender+canonical-clone RED · L3 keys-unchanged RED; coverage PASS (survivor is WATCHED — escape pin's job, clean split); **used-ness PASSES** (decoy defeats it) |
| #120 shape (a whole-workspace parse site NOT driven — non-nullary) | escape-invariant PASS · **coverage RED, site NAMED** (the exact reach gap the v5 offenders-form could not catch) |
| fresh-spelling battery (escape invariant) | MIGRATED→PASS · SURVIVOR→CAUGHT · ALIAS(`ap=ast.parse`)→CAUGHT · os.walk(abs keys)→CAUGHT · comprehension→CAUGHT · direct-`compile`→CAUGHT · single-package→**spared (PASS)** |
| §12.4 binding logic | distinct-scope True/False→GREEN · both-in-one-scope→RED · both-True→RED |
| gates | `ruff check` clean · `mypy` clean (test-tree runner) |

The ALIAS row is the load-bearing proof of "un-defeatable-by-spelling": L2 (name-keyed) is blind to
`ap = ast.parse; ap(...)`, but L1 catches it because the guard keys on the runtime `compile` chokepoint,
and the broad `_drivable_scan_candidates` finder recognises the scan by its SOURCE (`production_sources`)
rather than the aliased parse.

## §D — Deviations, honest bounds, and flags (per scope law + THE RIDER IS PART OF THE RULING)

1. **§12.2/§12.3 "a workspace .py filename" → the CALL SITE, not the compile `filename` ARGUMENT.**
   Offenders call `ast.parse(path.read_text())` with NO filename (default `<unknown>`), so a
   filename-argument filter would MISS the survivor. The guard discriminates on the caller-frame
   `co_filename` (a workspace `.py` site). VERIFIED in scratch. This is the only robust reading; stated
   in the accessor docstring.
2. **L3 binds to the derivation's KEY-REFLECTION, not §12.3's `assert_scan_reached_every_member`
   both-direction diff (#194).** Rationale: §9.6 records that only anchored/secret_typing route coverage
   through that helper (backoff/secret_leak adopt the parser for domain scans), so binding L3 to it would
   over-constrain; and L1 already catches the private-scan survivor robustly and alias-agnostically. The
   derivation-reflects-drop mechanism was graded SOUND by the delta-adversary. **Flagged for the
   adversary/operator:** if the coverage-pin both-direction diff is wanted as well, it is a per-adopter
   addition (anchored/secret_typing only). This is a dropped §12.3 rider — surfaced, not silently taken.
3. **L1 driven-form completeness bound (stated in the pin).** It catches private WHOLE-WORKSPACE (≥2
   member) scans in NULLARY derivations reachable by a source/read signal. A private parse hidden in a
   NON-nullary test method, or reaching files by an unrecognised signal (`os.scandir`, a hardcoded path
   list), is NOT driven → the SESSION-WIDE autouse form (§12.3's primary, the builder's stronger option)
   + L2 + INSTRUMENT 0's reach-attack. **Flag:** the builder should ALSO wire the guard autouse from
   conftest (retry-seam's shape) as the complete-reach mechanism; my contract uses the sanctioned
   "(or drives the derived adopter scans)" alternative so it is self-contained.
4. **§12.4 A↔B PURPOSE-swap residual (stated in the pin, §12.4's own fallback).** The binding pin catches
   collapse / dropped-mode, but the pure A↔B purpose swap (both modes present, in two distinct scopes,
   but the prod+tests-purpose scan given `include_tests=False`) needs knowledge this file does not have.
   That specific swap is the NAMED A-SUB cold-audit hand-check, OR — the stronger fix — the builder
   routes each scan through a distinctly-named nullary helper a future pin binds to its mode.
5. **REUSE / extract-to-shared-test-support (builder call, gated on prove-by-mutation).** The
   escape-report + `require_observations` + stack-walk-for-sanctioned-frame + pos/neg-control shape is now
   a shared POLICY with **≥2 users: the SDK gate (`test_retry_seam._sdk_guard`) and the parse gate**.
   Recommend extracting ONE parametrised `(primitive, sanctioned-frame)` runtime-reach guard into shared
   test-support, proven by mutation (change the shared scaffold → BOTH gates redden), exactly like the
   `_rebind_everywhere` promotion (#3). Do NOT force it if the retry-seam guard proves tightly coupled to
   async-SDK specifics (§7 over-consolidation caution) — recommend it, prove it, or clone the SHAPE.
6. **L2 is a LINT, honestly alias-defeatable** (`ap = ast.parse`, `open().read()`, `re.compile`
   collision) — stated in its docstring; L1 is the un-defeatable half. Both ship, as `test_retry_seam`
   ships both.

**Scratch:** `/tmp/asub3-scr-a` is a `scratch_copy.sh` tree (disposable by design; carries the reference
build + a `probe_parse_guard.py`). No real-tree file other than the contract was touched. Recommend the
lead discard it after reading this report.

**lore/grep fallback:** none — I used `lore` only incidentally; the work was AST/runtime construction in
the one writable file, plus direct reads of `_sdk_guard`/`_logging_fixtures`/the adopters (cited by symbol).
