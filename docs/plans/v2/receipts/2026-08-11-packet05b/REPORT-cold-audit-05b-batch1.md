# REPORT-cold-audit-05b-batch1

brief-base v11 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done — one CONFIRMED blocker on the #256 workstream; idle-gate v2 clean.
- **Verdicts:** **#256 annotate → NO-GO** (fixable) · **idle-gate v2 → GO**.
- Deviations (mine): none — read-only audit; I edited no code/tests, mutated no git state.
- **Packages considered:** none — no mechanism specified (this is an audit). The audited
  #256 change REUSES `lorerunes.is_blank` (existing shared predicate) and the existing
  `_apply`/txn-retry driver; idle-gate reuses `jq` (existing dep). No new package needed.
- **Graded:** working-tree diff atop `299e69a` · HEAD-at-report: `299e69a` · SAME (the diff
  is UNCOMMITTED; I graded HEAD + the uncommitted diff, the artifact the lead will commit).
- **Decisions-needed:** none — the NO-GO fix is small and fully characterized (below).
- Receipt pointers:
  - Blocker: §BLOCKER-256 + `loremaster/tests/test_retry_seam.py::TestNoGuardedCasHandlerReinterpretsExhaustedContention::test_the_door_enumeration_matches_the_canonical_set`
  - Currency gate: §Gates (RED_ORPHANED on pytest)
  - Fix proof: §BLOCKER-256 "Proven remediation" (in-memory scanner re-run)
  - Probes 1–6: §Probes

---

## GATES RE-RUN (my independent instrument — not the builders' numbers)

| Gate | Command | Result |
|---|---|---|
| idle-gate pytest | `uv run pytest scripts/test_teammate_idle_gate.py` | **23 passed** in 0.62s |
| shellcheck (hook) | via `./scripts/typecheck.sh` shell leg | **shellcheck OK (7 tracked .sh)** — covers the modified hook |
| #256 pytest (scoped) | `pytest test_findings test_mcp_server test_task_read_surface test_comms_footer -n auto` | **1188 passed, 1 skipped, 0 failed** in 147s (matches builder) |
| ruff | `uv run ruff check .` | **All checks passed!** |
| typecheck | `./scripts/typecheck.sh` | mypy **102 errors in 8 files, ALL auth-WIP** (pre-existing #333 baseline); **ZERO in any #256-touched file** → ZERO-NEW ✓ · shellcheck OK |
| currency | `uv run python scripts/pending_contract_gate.py --currency` | **FAIL — pytest RED_ORPHANED (1 residual)** ← the blocker below |

⚠ **Pipe-lie caught:** `./scripts/typecheck.sh 2>&1 | tail` reported the background task's exit
code as 0 (it was `tail`'s), but the body read `typecheck: loremaster FAILED`. I graded the
BODY, not the piped exit code (CLAUDE.md's documented `set -e`/pipe gotcha).

**mypy baseline note (re-derived, per "verify don't assume"):** brief estimated "~191 mypy
pre-existing"; I MEASURED **102** live at `299e69a`+diff (`uv run mypy loremaster`), all in 8
auth-WIP test files (`test_auth_composition`, `test_permission_resolver_seam`,
`test_hosted_readonly_posture`, `test_allowlist_roster`, `test_google_token_verifier`,
`test_auth`, `_auth_fixtures`, `test_auth_identity_seam`). The currency gate's **adjudicated**
typecheck residual count is **191**, owned by `packet-39-pending-build` (trigger: operator
decision #296 or packet 39 build start) — RED_ADJUDICATED, not orphaned. The 102-vs-191 delta
is in the safe direction and unrelated to #256; flagged as an observation, not a defect.

---

## BLOCKER-256 — #256 adds an UNREGISTERED guarded-CAS door (currency RED_ORPHANED)

**This is the P8d green-at-gate class this audit exists to catch: a structural invariant in a
file OUTSIDE the builder's scoped run + writable set.**

`findings.py::annotate` catches `except SurrealStoreError` and re-reads state
(`await self._select_row_by_id(...)`) — which is *exactly* the property that makes a handler a
"guarded-CAS door" in the whole-package AST scan `_discover_guarded_cas_handlers()`
(`test_retry_seam.py`). The invariant `test_the_door_enumeration_matches_the_canonical_set`
requires every such door be a DELIBERATE, reviewer-visible entry in the canonical
`_GUARDED_CAS_DOORS` set. The #256 build added a **fifth door** and did not register it:

```
E   doors with NO entry in the canonical set: ['findings.py::annotate']
E   assert dict_keys([...4 doors...]) == dict_keys([...4 doors...])
loremaster/tests/test_retry_seam.py:6789: AssertionError
```

- **Caused by #256, not pre-existing.** The scan's only new door is `findings.py::annotate`
  (added by the diff); `entries naming a door that no longer exists: []`. At `299e69a` without
  the diff, the scan finds exactly the 4 canonical doors → GREEN. Airtight from the failure text.
- **Why the builder's 1188-green missed it:** `test_retry_seam.py` was in neither the #256
  scoped test set nor the writable set (`findings.py`, `server.py`, `test_{findings,mcp_server,
  task_read_surface,comms_footer}.py`, `_finding_fakes.py`). Full `test_retry_seam.py` run:
  **1 failed, 561 passed** — this test is the sole failure.
- **The production code is SAFE — this is NOT a missing-guard safety bug.** annotate DOES carry
  the `except (SurrealConnectionError, TxnContentionExhaustedError): raise` guard ABOVE its
  re-read, so exhausted contention correctly propagates unread. The miss is the missing
  REGISTRATION — plus a scanner-recognition interaction (below).

### The fix has TWO required parts (proven)

The scanner computes `has_guard` only for `except` clauses whose type is a bare `ast.Name`.
annotate's guard is a **tuple** `except (SurrealConnectionError, TxnContentionExhaustedError):`
→ `handler.type` is an `ast.Tuple` → the scanner reports **`has_guard=False`** for annotate,
even though the guard is functionally present. `_transition` (the canonical peer) uses THREE
separate single-name clauses → `has_guard=True`. Measured, live:

```
line 1027 (annotate):    handler types ['Tuple', 'Name(SurrealStoreError)']              has_guard=False
line 1082 (_transition): ['Name(SurrealConnectionError)','Name(TxnContentionExhaustedError)','Name(SurrealStoreError)']  has_guard=True
```

So registering annotate ALONE would trip the *other* door test
(`test_every_door_guards_the_typed_error_ABOVE_its_rollback_handler[findings.py::annotate]`,
which is `@parametrize` over `_GUARDED_CAS_DOORS`) with a FALSE "no guard" verdict. Both parts
are needed:

1. **Production — `findings.py::annotate` (in the builder's writable set):** reshape the tuple
   guard into two separate single-name `except …: raise` clauses, matching `_transition`'s
   canonical shape. (Functionally identical; just makes the scanner see the guard.)
2. **Test — `_GUARDED_CAS_DOORS` in `test_retry_seam.py` (NOT in the #256 writable set → the
   lead must widen scope or run a follow-up):** add an entry, e.g.
   `"findings.py::annotate": "FindingNotFoundError — a row that vanished (defensive)"`.

**Proven remediation** (in-memory patch of `findings.py`, re-run of the scanner logic — no repo
mutation):

```
BEFORE fix: {'findings.py::annotate': (1027, False), 'findings.py::_transition': (1082, True)}
AFTER  fix: {'findings.py::annotate': (1029, True),  'findings.py::_transition': (1084, True)}
annotate has_guard AFTER: True   ·   all findings doors have guard AFTER: True
```

With both parts applied, `found.keys() == _GUARDED_CAS_DOORS.keys()` (5==5) and the
parametrized guard test sees `has_guard=True` → both door tests green. The behavioral test
`test_the_transactional_doors_never_re_read_after_exhaustion` is parametrized over a HARDCODED
3-door list (not `_GUARDED_CAS_DOORS`), so it does not auto-require annotate; the lead may
optionally add annotate there for behavioral coverage, but it is not needed for green.

*Alternative (NOT recommended): broaden the scanner to recognize tuple except-types. That edits
the shared invariant instrument (blast radius = all doors) and is outside #256's natural scope;
the reshape is the minimal, idiomatic fix.*

**The instrument already exists and did its job** — no new pin is owed (P8d "every defect class
becomes a repo-local invariant"); the door-enumeration test IS that invariant, and it caught this.

---

## Probes (the P8d classes builder gates miss)

**Probe 1 — shared shell is genuinely ONE implementation (independently mutation-checked).**
CLEARS. The guarded-append SQL (`provenance.events += [$event]`, the `LET $tr_updated=(UPDATE…)`
and the `THROW`) is constructed at EXACTLY ONE site: `_guarded_append_fragment`
(`findings.py:1146/1158`). `annotate` calls it directly (`:1022`); `_transition_fragment`
delegates to it (`:1179`). Not routing-is-not-sharing — the *construction* is shared, not a
driver call over cloned SQL. The contract's own F2 mutation pin
(`test_mutating_the_shared_shell_reddens_both_annotate_and_transition`, injects a sentinel into
`_guarded_append_fragment` and asserts it reaches BOTH composed SQLs) is stable 3/3.

**Probe 2 — transition refactor preserved behavior.** CLEARS. `_transition_fragment`'s signature
is unchanged; the delegation reconstructs BYTE-IDENTICAL transition SQL — SET order preserved
(status via `set_parts.insert(0, …)` → `[status, append]`), same 4 params
(`id/status/event/expected_from`), same `WHERE status = $expected_from`. All transition /
concurrency / IllegalTransition pins green (1188 scoped + the `findings.py::_transition` door
in test_retry_seam, 561 passed).

**Probe 3 — ≥8-way overlapping annotate concurrency (re-run, not a single green).** CLEARS.
`TestConcurrentAnnotate::test_concurrent_annotates_lose_no_events` = 8 racers × 5 annotates on
separate live connections = 40 events, overlapping lifetimes on the wire. Re-ran **5×: 2 passed
each** (`[real]` + `[fake]` both confirmed running, not skipped). Zero flakes. The server-side
`+= [$event]` append + shared retry driver lose no events; a client read-modify-write would.

**Probe 4 — served-English (#104), no fabricated transition.** CLEARS. annotate dispatch renders
via `_render_finding_detail` (the `get` render), never `_render_finding_transition`
(`server.py`); the appended event carries NO `to`/status key. Pinned by S2
(`test_findings_annotate_response_and_get_never_fabricate_a_transition` — "transitioned to" not
in response NOR later get) and pin 3 (`"to" not in event`) — green in the 1188 run. Tool
description teaches annotate accurately without over-claim ("status-PRESERVING note … WITHOUT
minting a new number via supersede"). Hostile-note containment pin 7 green (forgery marker stays
inside the `render_attributed` provenance delimiter).
  - *Trivial residual (not a defect):* the `note` param prose says "Ignored by the read actions
    and 'report'." — it does not also name the batch edges (`resolve_many`/`acknowledge_many`),
    which likewise ignore the top-level `note` (they use per-item notes). Cosmetic completeness;
    no gate covers it. Optional tidy.

**Probe 5 — idle-gate removed-behavior inventory (B1–B6) + the disclosed deviation.** CLEARS.
All six v1 branches are pinned and green in `TestRegressionBranchInventory`: B1 unidentifiable
payload (guard is BEFORE the contract read, so no `set -u` deref) · B2 root REPORT · B3 archived
REPORT under `receipts/*/` · B4 REPORT in any worktree · B5/B6 one-shot marker (nudge-once then
allow). v2 is a pure widening routed through the single `report_found` helper (DRY — the
worktree walk cannot drift between default/custom). Fail-open ladder complete and pinned:
absent / garbage-JSON / **missing-`artifact`-key** (the `jq -e 'has("artifact")'` gate, MP-3, is
the load-bearing discriminator — a naive `jq -r '.artifact'` reads `"null"` for both a real null
AND a missing key, silently exempting an owing agent) / empty-file → v1 default. Custom path
resolves at root + worktrees only, NO archive glob (operator reading (x), MP-2). Reach is a
CHECKED VARIABLE (`TestReachIsCheckedVariable`, INSTRUMENT-0). **Deviation RATIFIED:** the nudge
message now names the actual `${owed_path}` instead of hardcoded `REPORT-<name>.md` — an
accuracy improvement, not a dropped behavior; reads correctly for default (names REPORT-<name>),
custom (names the path), and null (never reaches the nudge → exit 0). Anti-cry-wolf softener
"continue as you were" preserved (N2). Registered in `testpaths` (`scripts` is a testpath), so
it is a real gate, not a hope with a filename.

**Probe 6 — store / DDL.** CLEARS. annotate's write is `UPDATE type::record(finding, id) SET
provenance.events += [$event]` on the ALREADY-EXISTING `provenance` field the transition path
already writes. No new `DEFINE FIELD`/table/index, no schema change → no `IF NOT EXISTS`/OVERWRITE
migration decision, no dirty-store hazard (store law §1/§2). No new relation/`RELATE`, so no
dangling-edge concern. The write rides the same `_apply` (guarded THROW-on-zero-rows CAS + txn
retry driver) as transitions.

---

## FULL RESIDUAL TABLE (the lead reads the whole table, not the summary)

| # | Sev | Workstream | Residual | Disposition |
|---|---|---|---|---|
| R1 | **BLOCKER** | #256 | `findings.py::annotate` is an unregistered guarded-CAS door → `test_retry_seam.py::…test_the_door_enumeration_matches_the_canonical_set` RED → currency **RED_ORPHANED**. | **MUST FIX before commit.** Two-part fix proven in §BLOCKER-256: (1) reshape annotate's tuple guard into separate clauses; (2) register `findings.py::annotate` in `_GUARDED_CAS_DOORS` (needs test_retry_seam.py in scope). |
| R2 | none | #256 | mypy baseline is measured **102** (auth-WIP), currency-adjudicated **191**; brief estimated "~191". | Observation only — safe direction, unrelated to #256, RED_ADJUDICATED to packet 39. Re-derive before citing. |
| R3 | trivial | #256 | `note` param prose omits the batch edges from its "ignored by" list. | Optional one-line prose tidy; no gate, no functional impact. |
| R4 | none | #256 | annotate is not in the HARDCODED 3-door behavioral list (`test_the_transactional_doors_never_re_read_after_exhaustion`). | Not required for green (that test isn't `_GUARDED_CAS_DOORS`-parametrized). Lead may add annotate for behavioral coverage of the new door — recommended but optional. |
| R5 | none | both | 8 auth-WIP test files carry 102 mypy errors + (per currency) pre-existing pytest reds. | Pre-existing #333 baseline, owned by packet 39. Outside this batch's scope; not introduced by either workstream. |

**No other whole-package structural scan is tripped by #256:** ran `test_retired_symbols`,
`test_text_hygiene`, `test_ast_reach_helpers`, `test_render_seam_pins`,
`test_comms_render_architecture`, `test_link5_render_containment`, `test_secret_typing`,
`test_anchored_pattern_seam` → **376 passed, 4 skipped**. The door-enumeration test is the sole
out-of-scope failure #256 causes.

---

## VERDICTS

- **idle-gate v2 → GO.** 23/23, shellcheck OK, B1–B6 preserved, fail-open ladder complete,
  reach a checked variable, deviation ratified, registered in `testpaths`. Independent of R1.
- **#256 annotate → NO-GO (fixable).** Core logic is correct and strongly pinned (shared shell
  is one implementation, byte-identical transition SQL, #104-safe, hostile-note contained,
  8×5 concurrency stable, no DDL hazard, zero-new mypy, ruff clean, 1188 scoped green). The
  single blocker R1 makes a required gate (currency) RED_ORPHANED; the fix is small and proven.
  Re-audit trigger: after R1's two-part fix, re-run `test_retry_seam.py` (expect 562 passed) +
  `--currency` (expect no RED_ORPHANED).

## Instrument (audit-built, pasted VERBATIM so the claim is re-runnable)

The in-memory scanner re-run proving R1's fix (run from repo root; mutates nothing on disk):

```python
import ast, pathlib
src = pathlib.Path('loremaster/loremaster/findings.py').read_text()
old = ("        except (SurrealConnectionError, TxnContentionExhaustedError):\n"
       "            # A genuine transport fault, or a conflict that outlived the retry budget\n"
       "            # — never a lost race for this WHERE-less append; propagate untouched.\n"
       "            raise\n")
new = ("        except SurrealConnectionError:\n            raise\n"
       "        except TxnContentionExhaustedError:\n"
       "            # exhausted retry budget — never a lost race for this WHERE-less append.\n"
       "            raise\n")
patched = src.replace(old, new, 1)
GUARD='TxnContentionExhaustedError'; RE_READ='_select'
def scan(source):
    tree = ast.parse(source); parents={}
    for p in ast.walk(tree):
        for c in ast.iter_child_nodes(p): parents[id(c)]=p
    def enc(n):
        cur=n
        while id(cur) in parents:
            cur=parents[id(cur)]
            if isinstance(cur,(ast.FunctionDef,ast.AsyncFunctionDef)): return cur.name
        return '<module>'
    doors={}
    for node in ast.walk(tree):
        if not isinstance(node,ast.Try): continue
        caught={h.type.id for h in node.handlers if isinstance(h.type,ast.Name)}
        for h in node.handlers:
            if not(isinstance(h.type,ast.Name) and h.type.id=='SurrealStoreError'): continue
            if not any(isinstance(c,ast.Call) and isinstance(c.func,ast.Attribute)
                       and c.func.attr.startswith(RE_READ) for c in ast.walk(h)): continue
            doors[f'findings.py::{enc(h)}']=(h.lineno, GUARD in caught)
    return doors
print("BEFORE", scan(src)); print("AFTER", scan(patched))
```
