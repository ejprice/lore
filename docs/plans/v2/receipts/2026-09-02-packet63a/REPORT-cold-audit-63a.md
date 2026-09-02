# REPORT-cold-audit-63a — COLD-AUDIT (fresh-context REFUTE) of packet-63a wave 63a

- `brief-base v14 read`
- `brief project v7 read`
- store reference consulted: `docs/reference/surrealdb-31-capabilities.md` — §2 (record<> links /
  CONTENT / explicit projection reads NONE), §3 (execute_read_transaction / BEGIN…COMMIT), §4 (record
  links do not auto-clean). Cited, not re-transcribed.

## SUMMARY BLOCK

- receipt: `brief-base v14 read` · `brief project v7 read`
- **state: done — VERDICT: NO-GO.** All gates re-run GREEN and reproduce the build's counts, but a
  cold REFUTE pass CONSTRUCTED (live, not reasoned) a **cross-principal WRITE-isolation break** green
  at every gate: `lore_remember(supersedes=<foreign row>)` retires another principal's memory note,
  bypassing `guarded_write` — the exact "wrong build that survives" the FIRST adversary named as
  MISSING PIN 2's supersede leg, which the final contract dropped.
- deviations from a clean audit: none — I edited no tree; the one repro lives in a provenance-asserted
  scratch copy (pasted verbatim in §F1).
- **Packages considered:** none — no mechanism specified (a cold audit builds no shipped code; the one
  repro reuses the shipped test harness).
- **Reuse ledger:** none — I authored no shipped symbol (the repro reuses `test_memory_retrofit_63a`'s
  fixtures verbatim).
- **Graded:** `dd5c9b2` · HEAD-at-report: `dd5c9b2` · SAME.
- decisions-needed: **F1 is a confirmed authorization bypass contradicting an explicit ruling (§2.5).**
  Whether to ship-with-a-named-bound (single-principal fleet TODAY) or fix-in-63a-iii is the operator's
  scope call — but the wave as it stands does not meet its own §9 memory-isolation acceptance target.
- receipt POINTERS: verdict + repro → §F1; gate re-runs → §GATES; per-focus → §FOCUS; residuals → §RES.

---

## §GATES — every gate re-run on the TEST store `ws://127.0.0.1:18000` (NEVER :18500)

A green claim carries a passed-COUNT. All commands: `uv run pytest -p no:cacheprovider -n auto -q`.

| gate | result | matches build report? |
|---|---|---|
| the 7 `test_*_63a.py` + `test_principal_delete_governed_63a.py` | **89 passed** in 12.21s | ✓ (85 contract + 4 SF-63-5) |
| corpse B/C (`test_agent_capability_seams` + `test_keeps_store`) | **83 passed** in 8.34s | ✓ |
| `test_mcp_server.py` (full) | **667 passed, 0 skipped** in 128s | ✓ (18 re-pointed, 0 skipped) |
| `test_search` + `test_principals_{cli,store,schema}` + `test_principal_keys_{schema,store}` + `test_principal_delete_cascade_61` | **312 passed** in 11.70s | ✓ |
| 60/61/62 sweep (`test_agent_capability`, `test_agent_owns_principal_schema`, `test_audit_{schema,store}`, `test_keeps_{cli,schema}`, `test_pdp_oracle_61b`, `test_visible_keeps_61b`, `test_surreal_store`) | **444 passed** in 22.57s | ✓ (a subset of the report's 626; the CLI/principal files sit in the row above) |
| `uv run ruff check .` | **All checks passed!** | ✓ |
| `bash scripts/typecheck.sh` | **every member OK** (incl. test trees + shellcheck) | ✓ |

The build is exactly as green as claimed. **This is the trap the cold audit exists for: green at every
gate, and still shipping a defect no gate can see** (an authorization surface no pin exercises).

---

## §F1 — THE NO-GO FINDING (CONFIRMED by live construction)

**`loremaster/memory/local.py::LocalMemoryBackend.remember` (the `supersedes=` close path, line
~626-628) — a member can retire ANOTHER principal's memory note, bypassing `guarded_write`.**

### The defect
`remember(supersedes=X)` closes the old row X via `_close_superseded_fragment(X, new_id, now)`
(`local.py` `_close_superseded_fragment`, ~line 1297) — a **bare** `UPDATE type::record('memory',
$old_id) SET valid_until=…, superseded_by=…` with **NO `WHERE` guard, NO `authorize_filter`, NO
ownership check** — spliced straight into the transaction by `_apply` (a plain `execute_transaction`,
no guard). The ONLY pre-check on the superseded row is `_row_exists` (existence, not ownership). The
`invalidate` verb was correctly routed through `governed.guarded_write` (`local.py::invalidate`,
~line 666); the `remember(supersedes=)` close — a WRITE on the same kind of EXISTING, possibly
foreign-owned row — was NOT.

### Why this is a defect and not a bound
- **Design §2.5 rules it explicitly:** *"`lore_remember(supersedes=…)` is a WRITE on the old row
  (close it) + a CREATE of the new one — **both route through `guarded_write`/the stamp.**"* The build
  routed one of the two.
- **The code's OWN comment says the close must be guarded** (`local.py` ~line 619-621): *"`remember`
  is a CREATE of a NEW row (the creator owns it), so it stamps directly — it is `invalidate` (a write
  on an EXISTING, possibly foreign-owned row) that routes through guarded_write."* The supersede-close
  is *also* a write on an existing, possibly foreign-owned row, and it does not.
- **The FIRST adversary named exactly this as "the wrong build that survives"** (`REPORT-adversary-63a.md`
  §MISSING PIN 2, lines 88-92): *"`remember`-CREATE is owner-stamped (passes the stamp pin) but …
  the supersede-close issues a **bare `UPDATE/DELETE` bypassing `guarded_write`** — a member
  closes/erases ANOTHER principal's note by id. The whole contract stays green."* MISSING PIN 2
  required a pin for **both** `invalidate` AND `remember(supersedes=…)`.
- **The contract pinned only HALF of it.** `test_memory_retrofit_63a.py::
  TestInvalidateRoutesThroughGuardedWrite` is *named* "the `invalidate`/**supersede** write path is
  GOVERNED" but both its methods call only `_exercise_invalidate` — the `remember(supersedes=)` close
  is never exercised. This is the QUANTIFIER LAW (CLAUDE.md): the invariant "no member closes a foreign
  row" was pinned on **one of the two write verbs §2.5 names**, and the build satisfied the pinned verb.
  The final adversary re-grade (`REPORT-adversary-63a-3.md`) marked the contract SUFFICIENT without
  re-checking that both legs of MISSING PIN 2 were pinned — a dropped rider that WAS the gate.

### The failure scenario (CONSTRUCTED, not reasoned — provenance-asserted scratch copy)
`./scripts/scratch_copy.sh /tmp/audit63a-repro` → `loremaster.__file__ =
/tmp/audit63a-repro/loremaster/loremaster/__init__.py` (I graded the copy of HEAD `dd5c9b2`, imports
resolve INSIDE the copy — #140). The repro reuses the SHIPPED `retrofit_world` fixture (two member
principals, alice + bob; a project keep in alice's household) and its production-seam helpers.

```
alice remembers a note (owned by alice, default project-keep scope, alice's household).
CONTROL — bob (a DIFFERENT principal, not in alice's keep) tries a direct invalidate:
    → GovernedDenied (the guarded_write door works); alice's valid_until stays None.
THE BYPASS — bob calls remember(text="hostile replacement", supersedes=<alice's note id>):
    → SUCCEEDS. alice's row now has valid_until SET and superseded_by → bob's note.
```

Result: **`1 passed in 3.55s`.** Same bob, same alice note, same authorization question — the guarded
door (`invalidate`) DENIES, the unguarded door (`supersede`) ALLOWS. That contrast IS the positive
control: it is not that bob is authorized, it is that one write path checks and the other does not.

The repro (an instrument establishing a load-bearing claim — brief-base §1), verbatim:

```python
# /tmp/audit63a-repro/loremaster/tests/test_zz_supersede_bypass_repro.py
from typing import Any
import pytest
from loremaster import governed
from test_memory_retrofit_63a import (  # SHIPPED fixtures/helpers, reused verbatim
    _bare, _exercise_invalidate, _exercise_remember, _one,
    alice_capability, bob_capability, retrofit_world,
)
from _surreal_harness import run

class TestSupersedeCloseBypassesGuardedWrite:
    async def test_bob_can_retire_alices_note_via_supersede(
        self, retrofit_world: Any, alice_capability: Any, bob_capability: Any
    ) -> None:
        backend, _p, _k, admin_conn, _env, _keep = retrofit_world
        alice_memory_id = await _exercise_remember(
            backend, text="alice note bob must not touch", capability=alice_capability)
        # CONTROL: bob is DENIED a direct invalidate (the guarded door works).
        with pytest.raises(governed.GovernedDenied):
            await _exercise_invalidate(backend, memory_id=alice_memory_id, capability=bob_capability)
        before = _one(await run(admin_conn,
            "SELECT valid_until, superseded_by FROM type::record('memory', $id)",
            {"id": _bare(alice_memory_id)}))
        assert before["valid_until"] is None
        # THE BYPASS: bob supersedes alice's note. If guarded this would DENY.
        bob_new_id = await _exercise_remember(
            backend, text="bob's hostile replacement of alice's note",
            capability=bob_capability, supersedes=alice_memory_id)
        after = _one(await run(admin_conn,
            "SELECT valid_until, superseded_by FROM type::record('memory', $id)",
            {"id": _bare(alice_memory_id)}))
        assert after["valid_until"] is not None                       # bob RETIRED alice's note
        assert str(after["superseded_by"]).endswith(_bare(bob_new_id))  # …pointing at bob's note
```

### Reachable over the wire at 63a-ii
The `lore_remember` tool passes `supersedes=` straight through: `server.py::AppContext.remember`
resolves the caller's `capability` → `Subject` then calls `backend.remember(…, supersedes=supersedes,
subject=subject)` (server.py ~line 4142-4151). A capability-bearing caller supersedes ANY memory id.

### Blast radius (an honest bound, but a bound is not a fix)
- **Today (single-principal dogfood fleet):** every agent is the operator's principal, so
  cross-*principal* exploitation is not live. **But even within ONE principal it already breaks the
  WRITE policy:** the member WRITE filter for `agent-private`/`principal-private` requires the EXACT
  `(principal, agent)` owner — so a sibling agent cannot `guarded_write` another agent's private note,
  yet CAN retire it via supersede. It also corrupts the supersession chain (alice's `superseded_by`
  now points at bob's unrelated note).
- **Post-65 (multi-principal / hosted):** a full cross-principal write-isolation break — the §9
  memory-isolation headline the wave names as its acceptance target.
- **The substrate is shipped as the ONE-IMPLEMENTATION address for 64.** The hole is in the first
  consumer (`remember`), not the substrate seam (`guarded_write` is correct), but the wave's stated
  deliverable is a memory retrofit whose served surface upholds isolation, and it does not.

### The fix (for whoever lands it)
Route the supersede-close through `guarded_write` (Action.WRITE on the superseded row) exactly as
`invalidate` does, in the SAME transaction as the new-row UPSERT — and pin `remember(supersedes=
<foreign row>)` → `GovernedDenied` + row-unchanged, with an owner-supersede positive control. That is
MISSING PIN 2's supersede leg, finally built.

---

## §FOCUS — the per-focus refute findings (each ground-truthed)

**1. CORPSE-A removed-behavior DUAL — SOUND (no vacuity).** The ~102+ `test_memory_backend` /
`test_memory_cutover` / `test_schema_rebuild` sites route through a shared ADMIN subject (`_GOV_SUBJECT`,
role=admin → `read_filter` = `AllRows`, unfiltered) with `scope="server"` on writes. I independently
grepped all three files for any read of `scope`/`owner_*` in an assertion → **0 hits** (claim holds),
and sampled the recall-set assertions (importance-by-kind, presence/absence after
supersede/invalidate, `len ≤ cap`, score ordering, kind/label filters, drift markers — e.g.
`test_memory_backend.py` lines 700-1175). Admin-AllRows is behaviorally identical to the pre-retrofit
unfiltered recall for these, and NONE of the assertions depended on governance filtering (they predate
it), so every sampled assertion still catches the memory-behavior bug it was written for. Governance is
certified separately by `test_memory_retrofit_63a`. The admin path DOES mask the R5 scope-loss (see
RES-1), but the durability tests' purpose (row survives a rebuild) is still correctly exercised by admin
recall. Dual verdict: the new-world green did not drop an old-world virtue.

**2. FORK-W frozen-test edit — SOUND (weakens no pin).** `git show b3385d7 -- test_governed_migration_
63a.py` removes only the dead `_migrate_memory(dry_run=False)` param + its passthrough (default was
False; all four callers pass only `migration_world`; green gate confirms no `dry_run=True` caller) and
one `[--dry-run]` docstring line. No assertion or behavior dropped. The §10.7-W residual grep is clean:
all 8 `dry-run` hits over `governed.py`/`principals.py`/the 63a test modules are PROSE documenting the
struck paradigm; **0 live `dry_run` code tokens** (I re-ran the grep). Reading A (the ruling authorizes
the cleanup) is the correct reading; the build surfaced the fork honestly.

**3. Composition root — CORRECT.** `AppContext._resolve_subject(capability)` reads `get_access_token()`
and delegates to `governed.resolve_subject` — the R-a.2 ONE `Subject(` constructor (verified: the only
production `pdp.Subject(` is `governed.py:159`). Fail-closed → `GovernedDenied`, never `TypeError`,
confirmed at the code level along the whole chain: `capability=None` → `parse_credential(None)` →
`is_blank(None)` returns `not None` = `True` (short-circuits BEFORE `.strip()`, no AttributeError) →
`_verify_capability_owner` returns `None` → `stamp_owner` raises `OwnerStampError` → `resolve_subject`
catches → `GovernedDenied`. The D2 `message_ledger` leak fix is REAL: a SECOND, post-`write_stack_
readied` build-failure path previously closed only `agent_registry`+`brief_ledger`; 63a-ii added
`message_ledger.close()` (a pre-existing leak) + the two new stores. R6 is CLOSED (test_mcp_server
667/0-skipped over the wired path).

**4. SF-63-5 `_table_exists` fail-closed — CORRECT.** `_table_exists` has NO try/except: a `_query`
fault on `INFO FOR DB` PROPAGATES out of `delete` (the principal is NOT deleted — no silent
"0 owned rows"). A genuinely-absent memory table reads `False` (pre-retrofit store → delete proceeds);
a present table runs the `count() … WHERE owner_principal=$p GROUP ALL` refuse BEFORE any DELETE. The
happy + refuse legs are pinned + mutation-proved (build §MUTATION #3). The fault-PROPAGATION leg is
correct-by-construction but UNPINNED (RES-3).

**5. `guarded_write` audit atomicity + R4 — CORRECT for the pinned scenario; two unpinned edges
(RES-2/RES-4).** The mutation + audit compose into ONE `execute_read_transaction`; a store-REJECTED
mutation (ASSERT violation) rolls the whole `BEGIN…COMMIT` including the audit (build §MUTATION #3
reproduces `before==after`). R4 holds: `governed.py` issues no direct SDK call (the reference build's
AST-pin discrimination in adversary-63a-3 §B2). `row_count` is read back from the mutation's RETURN by
shape (mutation composed first). Two edges the atomicity pin does NOT cover — see RES-2, RES-4.

**6. Honest bounds R5 / R6 — R5 accurate (RES-1); R6 closed.** R5 confirmed: `restore_from_ledger`
skips already-present rows (`local.py` ~817 — no re-strip on a normal boot), but `rebuild_embeddings`
drops the table and replays the WHOLE ledger via `_build_content`, which does NOT stamp
`owner_principal`/`owner_agent`/`scope` (only `remember` stamps, ~622-624) → every replayed row lands
NONE-scope. Fail-CLOSED (member-invisible / admin-visible, no leak) and recoverable (`migrate-governed`
re-backfills; the boot WARNING count fires). The build's "noted for 63b/65" is honest. See RES-1.

---

## §RES — residual table (each an individual verdict — "the rest look fine" is banned)

| # | residual | verdict |
|---|---|---|
| **RES-1** | `rebuild_embeddings` (and a wipe+`restore_from_ledger`) replays ledger rows WITHOUT governance stamps → all replayed memory rows become NONE-scope (member-invisible, admin-only). `rebuild_embeddings` auto-runs on any embedding model/dim change at boot, so the next model swap silently hides the fleet's own notes from members until `migrate-governed` is re-run. | **Known bound (R5), accurately noted by the build for 63b/65.** FAIL-CLOSED (no leak) + recoverable + WARNING-counted. Not a NO-GO by itself, but higher-impact than "noted" implies because the rebuild is automatic; the 63b/65 fix (stamp on replay, or block member reads behind a re-migrate) should carry a NAMED re-open trigger = "the first embedding-schema change after the cutover." |
| **RES-2** | `guarded_write` SILENTLY skips the audit when `requires_audit=True` but `audit is None` (`governed.py` ~272: `if requires_audit and audit is not None`). `memory.invalidate` passes `audit=None`, so an ADMIN load-bearing bypass close of a foreign-owned note executes UNAUDITED — the §9 "compromised admin erases its trail" shape, fail-OPEN. | **Latent substrate fail-open.** Not reachable in the single-principal fleet (requires_audit needs admin + a row a member couldn't write). But the substrate should RAISE (or the consumer must supply an audit store) rather than proceed unaudited. Recommend: `guarded_write` refuses `requires_audit and audit is None`, and `invalidate` wires the real `AuditStore`. Compounds F1 (memory has no audit trail for admin bypasses at all right now). |
| **RES-3** | The SF-63-5 `_table_exists` fault-PROPAGATION leg (a connection fault → refuse the delete, never "0 owned rows") is correct-by-construction (no try/except) but has NO pin — a future refactor that wraps the probe in `except: return False` would re-open a silent-delete-of-an-owning-principal with every gate green. | **Correct now, unpinned.** Recommend a pin: inject an `INFO FOR DB` fault → `delete` propagates, principal untouched (positive control: absent table → delete proceeds). Cheap; closes the class. |
| **RES-4** | In `guarded_write`, an audited admin bypass whose row is concurrently DELETED between the pre-read and the guarded mutation: the mutation matches 0 rows (not an error), the composed audit CREATE still COMMITs, THEN `GovernedConflict` is raised in Python — so an audit row lands for a write that never happened. | **Latent, LOW.** Not reachable via memory at 63a (invalidate audit=None). The spec's atomicity claim (§10.6 rider ii) is narrowly about a STORE-REJECTED mutation (which rolls back), so this is unpinned rather than contradicted. Flag for 64 (task/finding ledgers pass a real audit store): "audited bypass on a vanished row records a phantom action." |
| **RES-5** | `guarded_write`'s audit `actor_email`/`actor_agent_name` are stamped with the Subject's bare `principal_id`/`agent_id` (the lorerunes Subject carries no denormalized email/name), not real email/name (`governed.py` ~277-280). | **Documented simplification, benign at 63a.** The audit forensic columns carry ids, not human strings. Named in-source; acceptable while memory has no live admin-bypass. Worth a 64 note when the audit trail becomes load-bearing. |
| **RES-6** | `LocalMemoryBackend._default_project_scope` applies the project keep scope on a default write with NO `_grantable` check, so a caller NOT householded in the project keep can create a note scoped to it (only an EXPLICIT `scope=` is grantability-checked). | **By design (§2.4/§10-N — the default is always the project keep; a fresh note stays fleet-visible), not a defect.** Recorded for completeness; the explicit-`scope=` path IS `_grantable`-validated and pinned. |

---

## VERDICT: **NO-GO**

The 63a wave is green at every builder gate and every gate re-run, but it ships a **confirmed
authorization bypass** (F1) that (a) contradicts an explicit operator ruling (§2.5 "both route through
guarded_write"), (b) violates the §9 memory-isolation acceptance target the wave names for itself, and
(c) is the precise "wrong build that survives" the first adversary predicted as MISSING PIN 2's
supersede leg — dropped by the contract, waved through by the re-grade, and unseeable by any gate
because no pin exercises `remember(supersedes=)`. It is reproduced live in §F1. Blast radius is bounded
by the single-principal fleet TODAY, so the operator MAY choose to ship with a named bound and fix in a
bounded 63a-iii / the first 63b wave — but that is a scope decision for the operator; as the independent
instrument my verdict is NO-GO, with the fix and the missing pin named. RES-1..RES-6 are surfaced (not
narrowed): RES-2 (unaudited admin bypass) and RES-3 (unpinned fail-closed probe) are the two most worth
folding into the same fix wave.
