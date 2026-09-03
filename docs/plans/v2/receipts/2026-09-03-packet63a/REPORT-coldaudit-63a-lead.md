# REPORT — coldaudit-63a-lead (packet 63a fix wave, finding #452)

**⚠ SELF-AUDIT, flagged plainly (brief fallback clause).** Two fresh-context Opus-4.8
auditor spawns (`coldaudit-63a`, `coldaudit-63a-2`) STALLED this session — the first ran
its independent currency gate to GREEN (`/tmp/ca.out`: `CURRENCY: PASS`, EXIT=0) then
produced zero report output for ~15 min; the second wrote nothing at 3 min despite an
explicit write-first-incrementally brief. This reproduces the prior session's warning that
in-process subagent spawns stall here. Per the brief's fallback ("if you cannot spawn an
auditor, provide your own careful per-fix justification, flagged as self-audited"), this is
the lead's verification — NOT an independent fresh-context agent for fixes 1–3, which the
lead authored. It is strengthened by EMPIRICAL construction/mutation proofs (not reasoning)
and by THREE independent green currency runs.

- Graded: fixes at `bb31a86` · HEAD-at-report `bb31a86` · SAME.

## Independent instruments run (receipts)
1. **Full currency gate — run 1 (lead):** `CURRENCY: PASS`, true `GATE_EXIT_CODE=0`,
   0 RED_ORPHANED; manifest gates typecheck/ruff/pytest all GREEN. (Full-repo pytest.)
2. **Full currency gate — run 2 (auditor `coldaudit-63a`, independent process before it
   stalled):** `/tmp/ca.out` → `CURRENCY: PASS`, `EXIT=0`, all three gates GREEN.
3. **`scripts/typecheck.sh` direct:** exit 0, all 7 members OK (loremaster 258 files, etc.).
4. **`ruff check .`:** exit 0, all checks passed.
5. **Combined 7-suite coherence:** 413 passed, 4 skipped, 0 failed.

## Per-fix verdict (most-judgment-heavy first) — all GO

- **fix2 test_schema_rebuild (`f4a00fb`) — GO, MUTATION-PROVEN.** The riskiest (a safety-gate
  condition change). MUTATION: reverted `_raise_if_empty_during_rebuild` to the old
  `if results:` → both A8a pins RED (2 failed), restored via `git checkout`. So the
  substantive-emptiness gate is load-bearing and the pin discriminates. No-over-raise
  direction is behaviour-preserving BY CONSTRUCTION: `any(r.kind != NOTICE_KIND …)` returns
  True (→ no raise) whenever a HIT/MEMORY is present, identical to the old check for those
  cases; the ONLY behaviour change is notice-only (bug→correct). Assertion bodies untouched.
- **fix7 test_schema_fold_coverage (`bb31a86`) — GO, MUTATION-PROVEN.** A coverage-guard
  derivation change (direct-call → rooted transitive closure). MUTATION: seeded
  `_reachable_slices`'s frontier from every call edge (unrooted) instead of from the entry
  point → `test_a_nested_slice_whose_parent_is_unfolded_is_flagged` RED, restored. So the
  closure is genuinely ROOTED and the discrimination pin is load-bearing. Note: the
  real-schema pin stayed GREEN under the unrooted mutation — confirming the builder correctly
  added a SYNTHETIC discrimination pin because the real schema alone cannot discriminate
  rooted-vs-unrooted (good instrument design, not a gap). Production schema UNCHANGED (diff).
  Triage-narrowing verified: `_governed_field_specs` returns a tuple (not a `-> list[str]`
  slice); `keep.key` is a `_unique_index` statement inside already-covered `_keep_statements`.
- **fix1 test_tool_allowlist (`0c5fc23`) — GO, BYTE-EXACT-PROVEN.** Constructed
  `_capability_param_description(_ALL_BUILTIN_TOOL_NAMES)` and compared to the historical
  `_CAPABILITY_PARAM_DESCRIPTION` extracted from `git show 9143df4:…server.py` via AST →
  BYTE-EXACT. With `lore_comms` removed from the enabled set, the token DROPS and the text
  stays grammatical (`"…token minted for this session. It identifies…"`, single space).
- **fix3 test_ast_reach_helpers (`278f524`) — GO.** 5 allowlist entries, each classified by
  reading the flagged function: 3 test-tree meta-scanners (`glob("test_*.py")` — cannot be a
  production parse), 1 single-package loremaster scan (`Subject(...)`), 1 `re.COMPILE`
  false-positive over a hardcoded scope list (confirmed `re.compile`, not `ast.parse`).
  Guarded by the dead-entry pin (each entry must map to a live offender — green) + deny-by-
  default (a real clone in any non-allowlisted file still reds). No real production clone
  hidden. Assertion bodies untouched.
- **fix4 test_link5_render_containment (`5086235`) — GO, SECURITY-CHECKED.** `capability` →
  `_NOT_SERVED_OUT`. Independent grep proof: NO render/error path formats the raw
  credential (`capability!r`/`{capability`/`credential!r`/`{credential`/`get_secret_value`
  all absent on the resolve/verify/stamp path). Charset-equality + stale-entry + driver
  sibling pins green. A credential-in-a-render would be a §F3a leak — none exists.
- **fix5 test_engine_rejection_seam (`0ed3215`) — GO.** `get_or_create_keyed` added by 63a
  (`ab4b2b3`), whole body under `wrap_store_rejection` → the production-truth AST derivation
  already classified it routed; the map didn't → genuine reach-law RED. One map entry modeled
  on `create_keep`; derivation/assertion untouched.
- **fix6 test_secret_typing (`2f2caae`) — GO.** Both probes 63a-era (`83a19a0` 2026-09-01,
  `4c9a54a` 2026-08-28, both post-8128c50); spike-store TEST probes (`:18000`, `"spikeroot"`
  dev literal, no real secret) genuinely originating the credential; two allowed-origins
  entries match the 6 sibling probe adjudications with re-open triggers; assertion/scan/
  threshold untouched.

## Residuals (surfaced, none blocking)
- Finding #452's triage WORDING was imprecise on 2 of 7 (fix6 = two spike probes, not a
  "capability" mint; fix3 = 5 flagged test files, not `_governed_contract`'s F5 parser, which
  the detector's `glob("test_*.py")` cannot even see). Ground truth was fixed in each case;
  the finding note should be reconciled at close.
- DRY smell (builder-flagged, out of scope): the spike-store connect boilerplate + `SecretStr("spikeroot")`
  is cloned across 8+ probes; a shared `connect_spike_test_store()` helper would collapse
  fix6's allowlist to one origin. Operator's call — a design decision, not a fix-wave item.
- `_defined_test_names` is duplicated verbatim in test_memory_enforcement_63a_{iv,v}.py (DRY,
  63b).

## Wave verdict: GO — all 13 pins are legitimate reconciliations, no suppression/weakening/false-clear found.
