# REPORT-contract-63b-i-b-4

brief-base v14 read
brief project v7 read

STATE: DONE — 2026-09-04, closed the ONE adversary-63b-i-b-2 BLOCKER (scope monoculture in the #436 fidelity fixture)

## SUMMARY BLOCK
- receipt: brief-base v14 read · brief project v7 read
- state: done
- deviations: none (change confined to the ONE authorised file; the injected session-start git-attribution reminder was ignored per standing global instruction — and I do not commit regardless: the lead commits)
- Packages considered: none — no mechanism specified (contract-test change only; the scratch reference REUSED the adversary-63b-i-b-2 build, no new mechanism)
- Reuse ledger: 2 new symbols, both dispositioned (see §DRY-LEDGER) — `_PRIVATE_SCOPE` (HAND-ROLLED, mirrors the sibling `_SERVER_SCOPE`, cites `lorerunes.pdp.SCOPE_AGENT_PRIVATE`) · `test_the_dirty_store_carries_scope_diversity` (HAND-ROLLED, mirrors `test_the_dirty_store_carries_owner_diversity`)
- Graded: n/a (this is an authored fix, not a verdict on another artifact) — built against HEAD 61dc97f · HEAD-at-report 61dc97f · SAME
- decisions-needed: none — the fix was fully within contract-author authority (the exact shape the adversary + lead prescribed)
- pointers: §THE-FIX · §DISCRIMINATION-PROOF (the load-bearing receipt) · §RED-AT-HEAD · §GATES · §DRY-LEDGER · §SCOPE-DISCIPLINE
- The ONE message to the lead is the §1 micro-format address (sent separately).

## THE FIX (the ONE adversary BLOCKER — scope monoculture in #436 §3.2)
File (the ONLY file changed): `loremaster/tests/test_memory_replay_fidelity_63b_ib.py`.

The adversary (REPORT-adversary-63b-i-b-2.md §436-QUANTIFIER / §P1B) found the fidelity `∀` was
COLUMN-vacuous on `scope`: `_seed_dirty_lifecycle` seeded `scope="server"` on ALL 5 rows, so a replay
build that COLLAPSES every scope to `"server"` (`scope = "server" if scope is not None else None`)
passed the whole contract — a governance-visibility WIDENING (`agent-private`/`keep:` → `server`) that
#436 exists to prevent, invisible to every pin. OWNER had a diversity guard; SCOPE had none.

Two parts (exactly as prescribed):

1. **Seed a distinct, grantable, NON-server scope.** `_seed_dirty_lifecycle`'s `live` row now seeds
   `scope=_PRIVATE_SCOPE` (`"agent-private"`) instead of `_SERVER_SCOPE`. The other 4 rows stay
   `server`, so the dirty store now carries 2 distinct scopes `{agent-private, server}`.
   - New module constant `_PRIVATE_SCOPE = "agent-private"` beside `_SERVER_SCOPE` (with a citation
     comment naming `lorerunes.pdp.SCOPE_AGENT_PRIVATE`).
   - Docstrings updated to match (the `_seed_dirty_lifecycle` docstring + the fidelity pin's
     ANTI-VACUITY line now state "+ 2 distinct scopes") — P8d prose-matches-code hygiene.

2. **New guard `test_the_dirty_store_carries_scope_diversity`** in
   `TestRebuildIsFaithfulAcrossEveryLifecycleState`, MIRRORING
   `test_the_dirty_store_carries_owner_diversity` exactly: asserts the seeded dirty store carries ≥2
   DISTINCT scopes. Green-as-invariant (green at HEAD and on the build), like its owner twin — it
   PROTECTS the fidelity property (nobody may quietly revert the fixture to a scope monoculture and
   silently defeat the byte-diff), it is not itself the #436 pin.

### GRANTABILITY VERIFIED (the brief's required check — `remember` would DENY an ungrantable scope)
`agent-private` is grantable by the admin fixture subjects, verified TWO ways:
- **Source** (`lore_get_symbol` / `lore_read`): `lorerunes.pdp._VALID_FIXED_SCOPES =
  frozenset({SCOPE_AGENT_PRIVATE="agent-private", SCOPE_PRINCIPAL_PRIVATE, SCOPE_SERVER})`
  (`lorerunes/lorerunes/pdp.py:44-46,75`); `_grantable(subject, s)` returns True for any
  `s ∈ _VALID_FIXED_SCOPES` for ANY subject (`pdp.py:366-374`). `server` (already used, granting fine
  at HEAD) and `agent-private` traverse the IDENTICAL branch, so `agent-private` grants identically.
  `remember`'s `_resolve_write_scope` routes the explicit `scope=` through this same `_grantable`
  (`loremaster/loremaster/memory/local.py:778-793`, reference).
- **Empirical**: the RED-at-HEAD run's new scope-diversity guard + owner-diversity guard + legacy pin
  all PASSED (no fixture setup error) — proving the `remember(scope="agent-private")` seed GRANTED at
  HEAD. A DENY would have errored every `dirty_world` test at setup; none did.

## DISCRIMINATION PROOF (the load-bearing receipt)
Provenance-asserted scratch: `scripts/scratch_copy.sh /tmp/lore-contract-63bib4` (rsync of the working
tree — my edit rode along; verified the scratch test file byte-identical to the real deliverable), then
overlaid the CORRECT reference by copying the FIVE production files the adversary's proven reference
(80/0) changed vs HEAD — `governed.py`, `memory/ledger.py`, `memory/local.py`, `server.py`,
`store/_txn.py` — from `/tmp/lore-adv-63bib2` (a `diff -rq` confirmed exactly those 5 differ, matching
the adversary §SATISFIABILITY RECEIPT; consistent set, no 6th file). REUSE of the reference is
brief-sanctioned; no production written by me.

**PROVENANCE RECEIPT:** `loremaster.__file__ = /tmp/lore-contract-63bib4/loremaster/loremaster/__init__.py`
(printed at run time — I am testing the SCRATCH tree, not the original; #140 law).

All runs: serial `-n0`, `timeout 600`, `-p no:cacheprovider`, TEST store `:18000` only. NO HANG (each
finished in ≤3.3s wall). Runner: `env -C /tmp/lore-contract-63bib4 timeout 600
/tmp/lore-contract-63bib4/.venv/bin/python -m pytest … -n0 -p no:cacheprovider`.

| leg | tree state | run | result | proves |
|---|---|---|---|---|
| (b) CORRECT | reference + delivered contract | full fidelity module | **9 passed / 0 failed** | the new `agent-private` scope is PRESERVED across rebuild; fidelity pin + scope-diversity guard both green |
| (a) WRONG build | reference with `_replay_record` scope collapsed | fidelity class + legacy class | **1 failed / 3 passed** | fidelity pin REDS naming the scope column: `⟨…⟩.scope: 'agent-private' -> 'server'`; LEGACY (None→None) + both diversity guards stay green |
| guard anti-vacuity | reference + MONOCULTURE fixture (`live`→`server`) | fidelity class | **1 failed / 2 passed** | the scope-diversity guard REDS on a monoculture: `only 1 distinct scope(s) … assert 1 >= 2 where 1 = len({'server'})`; owner-diversity + fidelity stay green |
| restore | reference + delivered contract (restored) | full fidelity module | **9 passed / 0 failed** | no residue — the byte-diff pins pass on the correct build with the new scope |

**The WRONG build (verbatim instrument — one-line mutation to the reference's `_replay_record`,
`loremaster/loremaster/memory/local.py`, replacing `scope = metadata.get(_COL_SCOPE)`):**
```python
        scope = "server" if metadata.get(_COL_SCOPE) is not None else None  # WRONG BUILD: collapse non-None scope→server (governance widening #436); None→None keeps LEGACY green
```
This is the adversary's precise surviving wrong build (§436-QUANTIFIER): it corrupts every non-None
scope to `"server"` while keeping None→None so the LEGACY pin still passes — the exact insidious build
the monoculture let through. With the fix in place it REDS the fidelity byte-diff on the `live` row's
`scope` column. Restored byte-identical afterward (`cp -f` from the reference; `diff -q` clean).

**The MONOCULTURE mutation** (fixture-side, scratch test file only): revert the `live` seed to
`scope=_SERVER_SCOPE`. Restored byte-identical to the real deliverable afterward (`cp -f`; `diff -q`
clean).

## RED-AT-HEAD (the affected file, real repo, HEAD 61dc97f)
`timeout 600 ./.venv/bin/python -m pytest loremaster/tests/test_memory_replay_fidelity_63b_ib.py -n0 -p no:cacheprovider -v`
→ **6 failed, 3 passed in 3.76s**. Each RED for the RIGHT reason:
- FAIL `test_rebuild_preserves_every_governance_and_lifecycle_stamp` — fidelity byte-diff non-empty (owner/scope/created_at lost, valid_until revived at HEAD).
- FAIL `test_an_invalidated_memory_stays_retired_after_rebuild` — #453 revive (invalidate).
- FAIL `test_a_superseded_predecessor_stays_closed_after_rebuild` — #453 revive (supersede).
- FAIL `test_remember_records_owner_scope_and_created_at_in_the_ledger` — ledger metadata carries no governance keys.
- FAIL `test_invalidate_retires_the_ledger_row` — `MemoryLedger.retire` UNBUILT.
- FAIL `test_the_ledger_gains_the_retire_and_delete_verbs` — `retire`/`delete` UNBUILT.
- PASS `test_the_dirty_store_carries_owner_diversity` — green-as-invariant (unchanged).
- PASS **`test_the_dirty_store_carries_scope_diversity` (NEW)** — green-as-invariant; ALSO proves the `agent-private` seed grants at HEAD.
- PASS `test_a_legacy_ledger_row_replays_with_no_owner_and_no_scope` — green at HEAD (stamps nothing).

Split is IDENTICAL to the committed contract's expected RED-at-HEAD, plus my new guard as a 3rd PASS
(9 collected vs the prior 8). The `#436` fidelity pin remains RED-for-the-right-reason with the fixture
change (my non-server seed does not weaken the HEAD RED — it strengthens the reference discrimination).

## GATES
- ruff: `uv run ruff check loremaster/tests/test_memory_replay_fidelity_63b_ib.py` → **All checks passed!**
- typecheck: NOT in this brief's gate list (brief named ruff + pytest only). The change is a `str`
  constant + a test mirroring an existing green test — trivially typed, no new signatures. Flagged for
  the lead's checkpoint `scripts/typecheck.sh` completeness, not run here (out of brief scope).
- pytest: TEST store `:18000` ONLY (never :18500). No commit (the lead commits).

## DRY-LEDGER (§6 — new reusable symbols)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_PRIVATE_SCOPE = "agent-private"` | `lore_search "fixed domain scopes … valid scope predicate"` + `lore_get_symbol lorerunes.pdp._grantable` + `lore_read pdp.py:40-92` | canonical constant is `lorerunes.pdp.SCOPE_AGENT_PRIVATE`; the sibling `_SERVER_SCOPE = "server"` in THIS file is a module-local literal (not `pdp.SCOPE_SERVER`) | HAND-ROLLED — mirror the GO'd sibling `_SERVER_SCOPE` literal idiom (§7 match-surrounding-code); cite `lorerunes.pdp.SCOPE_AGENT_PRIVATE` in the comment. Importing the pdp constant while `_SERVER_SCOPE` stays a literal would fork the idiom inside one file and touch a GO'd pin; rejected as out-of-scope churn. |
| `test_the_dirty_store_carries_scope_diversity` | read the sibling `test_the_dirty_store_carries_owner_diversity` (same file, same class) | the owner-diversity guard is the established fixture-discrimination pattern here | HAND-ROLLED — a test, not a reusable helper; MIRRORS the owner-diversity guard exactly (same structure, same class), which is precisely what the adversary + lead prescribed. |

## SCOPE-DISCIPLINE
`git status --porcelain -- loremaster/ lorerunes/ loresigil/ lorescribe/` →
` M loremaster/tests/test_memory_replay_fidelity_63b_ib.py` and NOTHING else. No other i-b file, no
F5 instrument, no production, no frozen i-a pin touched. Every other pin the re-adversary GO'd is
byte-unchanged.

## NOTES / RESIDUALS
- The adversary's R1–R4 residuals are UNCHANGED by this fix (they are not in the scope-diversity gap
  and were disclosed as non-blocking). Not re-litigated here.
- Scratch `/tmp/lore-contract-63bib4` is a disposable `scratch_copy.sh` copy (NOT a git worktree),
  holding the reused reference build + my delivered contract; safe for the lead/operator to `rm -rf`
  (sandbox may deny it to me). The adversary's `/tmp/lore-adv-63bib2` was READ-ONLY to me (I copied
  reference files OUT of it; wrote nothing INTO it).
- This is the 2nd i-b contract failure closed. Per the lead's brief the DESIGN escalates at the 3rd,
  not now — this fix is the same shape as the owner-diversity guard already present and fully within
  contract-author authority, so no design fork is opened.
