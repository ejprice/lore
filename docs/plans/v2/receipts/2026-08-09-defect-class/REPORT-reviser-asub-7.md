# REPORT — reviser-asub-7 (Opus CONTRACT reviser; A-SUB accepted-bound pin-the-miss + false-clear docstring fix)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK (read first)

- **State:** done. CONTRACT TESTS ONLY — edited ONLY `loremaster/tests/test_ast_reach_helpers.py`
  (my sole writable file). No production/implementation code. No contract-adversary phase (operator, §13).
- **What I did (the 3 tasks):**
  1. **Filed finding #351** — the accepted KNOWN BOUND: a bytes/normalized-source whole-workspace
     `ast.parse` in a skip file fails the members-spanned discriminator OPEN (member=""); distinct
     from #349; names the operator's acceptance + re-open triggers.
  2. **Pin-the-miss added** — `TestAsubBytesNormalizedSourceParseIsAKnownBound351::
     test_asub_bytes_normalized_whole_workspace_parse_is_a_KNOWN_BOUND_351` (#137/#138 idiom, the
     #349-pin's positive-control discipline). Asserts the bound EXISTS + a positive control that
     the source-text resolver returns "" for a bytes/normalized source + the named re-open triggers.
  3. **Fixed the false-clear docstring** at `test_no_skip_set_file_parses_the_tree_unrouted` — states
     EXACTLY what L1 + the discriminator cover (attributable str sources), names #351 as the accepted
     bound. NOT "an in-scope PARSE in ANY spelling is CLOSED HERE."
- **Deviations (3 — beyond the single docstring the brief named, prominently disclosed):** the
  IDENTICAL false-clear ("reddens/RED, ANY spelling") appeared in THREE more prose surfaces in the
  SAME file — the `_ASUB_PARSE_SKIP` block comment, the backoff skip `reason` string, and the
  `TestTheParseSkipSetIsACheckedVariable` class docstring. Per the operator's own "honest docstring —
  state exactly what L1 covers" leg + TRUST law + the rename-sweep "every residual hit gets a
  verdict" discipline, I corrected all three (each narrows the over-claim + names #351). The class
  docstring also mis-stated the discriminator as ">=2 compiles"; fixed to ">=2 MEMBERS" (the real
  code). All prose-only; no behaviour change. See §D.
- **The bound is met DELIBERATELY (not chased):** pin reddens if closed at the discriminator
  (mutation-proven, §C); GREEN-today because it pins the ACCEPTED disposition. No fail-closed C-DEF
  risk taken. #349 pin unchanged.
- **Packages considered:** none — stdlib `ast` only; reuse of the contract's own helpers
  (`_whole_workspace_escape_sites` / `_skip_files_parsing_whole_workspace` / `_skip_budget_verdict`)
  + the synthetic-`_Escape` control idiom + the #137/#138/#349 pin-the-miss idiom. No mechanism specified.
- **Graded:** my edits sit atop the UNCOMMITTED working-tree A-SUB revision (reviser-asub-6's §12.8
  state) which is atop HEAD `3249b22` · HEAD-at-report `3249b22` · SAME. (The HEAD→worktree diff spans
  the whole uncommitted A-SUB arc; my delta = 4 prose corrections + 1 new test, 53→54 collected.)
- **Decisions-needed:** none. (The FORK delta-adversary-asub-6 surfaced — close vs pin — was RULED by
  the operator in §13: PIN. This report executes the PIN leg.)
- **Receipt pointers:** §A finding #351 · §B the pin + why GREEN-today · §C mutation proof (reddens if
  closed) + restore-byte-exact · §D the 4 prose corrections (file:symbol) · §E gates (ruff/mypy) +
  the unrelated pre-existing mypy reds.

---

## §0 — Capability check
Full tool access; lore loaded (`ToolSearch "+lore"`); registered `reviser-asub-7` (session
`2026-08-09-fix-344-345`, role contract, model claude-opus-4-8); inbox drained empty. No brief demand
unmet. Work is AST/test-helper prose + a build-independent synthetic pin — no lore structure-query
fallback to flag. Writable set honoured: ONLY `loremaster/tests/test_ast_reach_helpers.py` touched
(git working-tree change confined to it; `scripts/test_wave_gate.py` was pre-existing M at session
start — the concurrent contract-g-simple sibling's disjoint file, NOT mine).

## §A — Finding #351 (the accepted KNOWN BOUND, filed)
`lore_findings action=report` → **#351** (id `21e745a7f5ca48f7abfb7eb399143bf5`, status open). Category
`duplication`, kind `uncertainty`, area `loremaster.tests.test_ast_reach_helpers / A-SUB anti-dup`.
Body: the delta-adversary-asub-6 survivor (a routed-but-private whole-workspace
`ast.parse(read_bytes())` / `read_text()+normalize` → member="" for all 117 escapes →
`_whole_workspace_escape_sites` drops them fail-open → 0 flagged → GREEN); the operator's §13
acceptance as a bound (trivial-importance test-infra, adversarial-only, outside honest-dev threat
model); DISTINCT from #349 (non-parsing walk); the named re-open triggers (real drift / threat-model
change / CI+root-audit → a source-content member-resolver routed through design, NOT a spelling chase).

## §B — The pin-the-miss (`TestAsubBytesNormalizedSourceParseIsAKnownBound351`)
Added at end of file (after `TestAsubNonParsingTreeWalkKnownBound349`). Three legs, all
build-INDEPENDENT (synthetic `_Escape` objects on the CONTRACT's own helpers — the
`test_the_skip_coverage_discrimination_fires_and_discriminates` idiom, so NO guard build is needed →
GREEN today, pinning the ACCEPTED disposition):

1. **THE BOUND** — 6 escapes at one whole-workspace skip-file site, ALL `member=""`:
   `_whole_workspace_escape_sites(unattributable) == set()` and
   `_skip_files_parsing_whole_workspace(...) == {}` and `_skip_budget_verdict(0,0) is None` → the site
   is NOT flagged (the fail-open). That IS the bound.
2. **POSITIVE CONTROL (anti-triviality)** — the SAME site with ATTRIBUTED members (loremaster,
   lorerunes) IS flagged (`== {ws_site}`). So the bound is precisely "member='' (unattributable
   source)", not "the discriminator never fires" — the #349-pin discipline.
3. **POSITIVE CONTROL (the bound is REAL)** — a bytes source and a normalized source are each an
   in-scope parse (`isinstance(ast.parse(...), ast.Module)`), yet the §12.8.3 source-text resolver (a
   str-keyed `{source: member}` map, per `_install_parse_guard_fn`'s REQUIRED API, modelled locally as
   `resolve_member`) returns "" for both — the member="" root — AND resolves an attributable str
   source to "loremaster" (the control's own control, so `resolve_member` is not a stub).

Carries the brief-specified message verbatim ("KNOWN BOUND #351: … if you closed this deliberately,
delete this pin and say so"), the named re-open triggers, AND (#137/#138 discipline) a stated **bound
of the pin ITSELF**: it pins the discriminator's fail-open disposition, so it reddens on a closure AT
THE DISCRIMINATOR; a closure at the GUARD (robust member-resolution) leaves this synthetic pin green →
at that closure, replace with a guard-driven pin and say so.

**GREEN-today receipt** (`uv run pytest -p no:xdist`, my pin + the 4 sibling build-independent
controls incl. #349): `5 passed in 1.14s`. File collects: `54 tests collected` (was 53; my pin adds 1).

## §C — Mutation proof: the pin REDDENS when the bound is closed (non-vacuity)
Mutated the REAL `_whole_workspace_escape_sites` to FAIL-CLOSED (an empty-member escape at a site
becomes a whole-workspace SUSPECT — the delta-adversary-asub-6 recommended closure), with a `cp -a`
content backup (#140 sound path). Ran my pin → **FAILED (RED)** at leg-1:
`AssertionError … Extra items in the left set: 'loremaster/tests/test_backoff_seam.py:780 in
_bytes_source_whole_workspace_scan()'`. Restored byte-exact (`md5 match: YES`). Re-ran → `1 passed`.
So the pin is demonstrably non-vacuous and honours the pin-the-miss contract (RED the day someone
closes it at the discriminator).

## §D — The 4 prose corrections (the false clear, everywhere it lived in this file)
The operator ruled "honest docstring — state EXACTLY what L1 covers". The false clear ("an in-scope
PARSE in ANY spelling is CLOSED HERE / reddens ANY spelling") lived in FOUR surfaces of this one file;
all four narrowed to name what L1+discriminator actually cover (attributable str sources) + the #351
bound. All prose/comment only — zero behaviour change, GREEN-today preserved. Sweep-verified: 0
residual "ANY spelling" hits, and the two remaining "not closed here" hits are the HONEST framing.

1. **`TestTheParseSkipSetIsACheckedVariable.test_no_skip_set_file_parses_the_tree_unrouted` docstring**
   (THE brief-named one) — "an in-scope PARSE in ANY spelling is CLOSED HERE … never pinned" →
   "L1 + the members-spanned discriminator CLOSE every HONEST parsing spelling whose source is
   ATTRIBUTABLE (rglob/production_sources/split-leg TEXT); TWO KNOWN BOUNDS pinned honestly: #349 +
   #351".
2. **`TestTheParseSkipSetIsACheckedVariable` class docstring** (deviation) — "a site with >=2 compiles
   … RED either way, ANY spelling" → "a site whose escapes span >=2 MEMBERS … RED for every spelling
   whose source the discriminator can ATTRIBUTE" + names #349/#351. (Also fixes the ">=2 compiles"
   mis-statement — the code requires >=2 MEMBERS.)
3. **`_ASUB_PARSE_SKIP` block comment** (deviation) — "survivor now reddens, ANY spelling" → "TEXT-source
   survivor now reddens … but a bytes/normalized source resolves to member="" and is KNOWN BOUND #351".
4. **backoff `_ParseSkip.reason` string** (deviation) — "the skip-coverage pin reddens, ANY spelling" →
   "reddens for any ATTRIBUTABLE-source spelling (rglob/production_sources/split-leg text; a
   bytes/normalized source is KNOWN BOUND #351)". (Verified no test asserts on `.reason` content.)

## §E — Gates
- **ruff:** `uv run ruff check loremaster/tests/test_ast_reach_helpers.py` → `All checks passed!`;
  `uv run ruff check .` → `All checks passed!`.
- **mypy (canonical `scripts/typecheck.sh`):** my file is **mypy-clean** — 0 errors reference
  `test_ast_reach_helpers.py`. The loremaster leg FAILS with 104 errors, ALL in 10 auth/posture
  contract files I never touched (`test_auth_composition.py`, `test_mutating_set_derivation.py`,
  `_auth_fixtures.py`, `test_auth.py`, `test_hosted_readonly_posture.py`, … — unbuilt
  `resolve_posture`/`Posture`/`partition_tools_by_posture`/`PostureConfigError`/`SCOPE_READ` symbols,
  RED-at-HEAD contract-first pins for a DIFFERENT concurrent packet). These pre-date my change (a diff
  in another file cannot be caused by editing mine) and are unrelated to A-SUB.

---

There are 104 mypy errors (across 10 auth/posture contract-test files) unrelated to our present scope.
Do you want to examine them more closely?
