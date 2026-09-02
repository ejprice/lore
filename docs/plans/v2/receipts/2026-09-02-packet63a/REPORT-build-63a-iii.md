# REPORT-build-63a-iii — BUILD (GREEN) for the 63a cold-audit NO-GO fix (F1 + RES-2)

- `brief-base v14 read`
- `brief project v7 read`
- store reference consulted: `docs/reference/surrealdb-31-capabilities.md` — §2 (the `superseded_by`
  = `option<string>` landmine → a STRING literal, never `type::record()`; CONTENT/projection),
  §3 (`execute_read_transaction` / `BEGIN…COMMIT` atomicity). Cited, never re-transcribed.

## SUMMARY BLOCK

- receipt: `brief-base v14 read` · `brief project v7 read`
- **state: done.** The 4 RED contract pins (HEAD `3fea29a`) are GREEN by PRODUCTION CODE ONLY (2
  files: `governed.py`, `memory/local.py`); no frozen pin was edited. Atomicity decided as option (b)
  (authorize-close-first) with the no-orphan property verified. Both mutation proofs run + restored
  byte-exact.
- deviations: none to the plan. ATOMICITY: I chose option (b) as the brief strongly preferred —
  detail + no-orphan proof in §ATOMICITY.
- **Packages considered:** none — no mechanism specified. The fix WIRES existing symbols
  (`governed.guarded_write`, `loremaster.audit.AuditStore.append_fragment`, `time::now()`); no new
  library. `AuditStore` used purely as its designed compose-time `append_fragment` builder.
- **Reuse ledger:** 1 new production symbol (`LocalMemoryBackend.audit_store`), dispositioned → §REUSE.
- **Graded:** N/A — I am the builder; I render no verdict on another artifact. (Built against the RED
  contract at HEAD `3fea29a`; the fix is COMMITTED as `b0453c7` — the SHA the cold-auditor should
  re-grade.)
- **decisions-needed:** ONE fork escalated to lead-63 → §FORKS: the **production audit-DDL gap** — the
  memory DB has no `audit` table in production (no `AuditStore` is wired at the composition root), so
  the RES-2 fix is behaviourally correct + pin-proven but a production admin-bypass close (latent —
  unreachable in the single-principal fleet) would land its audit CREATE in an auto-created schemaless
  table. Latent, named re-open trigger inside. Plus 2 non-blocking notes (a cheap permanent no-orphan
  pin; the `_governed_contract._build_audit_store` DRY follow-up the contract already flagged).
- receipt POINTERS: fix→pin map → §FIXES; atomicity choice + no-orphan proof → §ATOMICITY; AuditStore
  wiring → §AUDIT-WIRING; RED→GREEN + gate tails → §GATES; mutation proofs → §MUTATION; forks → §FORKS.

---

## §FIXES — the two production changes → the 4 RED pins

**Change 1 — `governed.py::guarded_write` (RES-2 substrate refuse).** After the Python gate computes
`requires_audit`, and BEFORE the mutation is composed or run, added:
```python
if requires_audit and audit is None:
    raise GovernedAuditUnavailable(… "refusing to run it UNAUDITED (RES-2 / §9 erase-the-trail)" …)
```
and simplified the later compose guard `if requires_audit and audit is not None:` → `if requires_audit:`
(the raise-check makes `requires_audit ⇒ audit is not None` an invariant, so the compose is no longer
gated on `audit is not None` — the silent-skip is GONE, not merely guarded).
- → GREEN: `test_governed_substrate_63a.py::TestGuardedWriteRefusesAnUnauditedBypass::`
  `test_an_admin_bypass_with_no_audit_store_refuses_and_does_not_mutate` (raises
  `GovernedAuditUnavailable`, row unchanged).
- Discriminator (stays GREEN both worlds): `…test_a_non_bypass_write_with_no_audit_store_still_succeeds`
  (requires_audit=False → no raise → the member own-row write lands with `audit=None`).
- The `TestGuardedWriteComposesAudit` +1 / rejected-rollback pins stay GREEN (real store passed → the
  compose is unchanged for `audit is not None`).

**Change 2 — `memory/local.py` (F1 supersede-deny + RES-2 memory audit).** Four edits:
1. `import AuditStore`.
2. New `audit_store` property — self-builds an `AuditStore` from the backend's own connection params,
   mirroring the `handle` accessor idiom (§AUDIT-WIRING). No constructor arg → `build_memory_backend`
   unchanged (contract's satisfiability receipt confirmed).
3. `remember`: the supersede-CLOSE now routes through `governed.guarded_write(Action.WRITE, row_id=
   supersedes, set_fragment="valid_until = time::now(), superseded_by = '<memory_id>'",
   audit=self.audit_store, store=self.handle)`, run BEFORE the ledger write + new-row UPSERT (option b,
   §ATOMICITY). The old `fragments.append(self._close_superseded_fragment(...))` + the now-orphaned
   `_close_superseded_fragment` static method are DELETED (the exact bare-ungoverned-UPDATE defect
   cold-audit §F1 named).
4. `invalidate`: `audit=None` → `audit=self.audit_store`.
- → GREEN: `test_memory_retrofit_63a.py::TestInvalidateRoutesThroughGuardedWrite::`
  `test_a_member_cannot_supersede_close_a_foreign_owned_row` (bob's supersede DENIES; alice's row
  untouched) + its owner positive control.
- → GREEN: `…::TestMemoryBypassCloseIsAudited::test_an_admin_bypass_invalidate_appends_exactly_one_audit_row`
  + `…_supersede_close_appends_exactly_one_audit_row` (carol/admin bypass → +1 audit row via each close
  verb); the member self-close discriminator stays +0.

**The §2 landmine, honoured:** `memory.superseded_by` is `option<string>` (`surreal_schema.py:279`) —
the close sets `superseded_by = '<memory_id>'` (a STRING literal; `memory_id` is a deterministic uuid5,
hex+dashes, safe to inline), never `type::record()` (that field-coerces and rolls the txn back — the
contract's satisfiability build hit this). `guarded_write`'s raw `set_fragment` takes no bound params of
its own, so `valid_until` self-stamps via `time::now()` (the `invalidate` idiom).

---

## §ATOMICITY — the conscious decision: option (b), AUTHORIZE THE CLOSE FIRST (§FORKS-1)

**Chosen: option (b).** The supersede-close routes through `guarded_write` (its own `BEGIN…COMMIT`)
BEFORE the durable ledger write and the new-row UPSERT. On a DENIED close (`GovernedDenied`), the method
returns before any part of the new note lands — neither a Surreal row nor a ledger row (the guarded
close is now the FIRST store touch inside the rebuild-lock, ahead of `self._ledger.record`).

**Why (b) over (a):** option (a) (accept the orphan) leaves a half-applied supersession — a new row
created while the foreign close was denied, plus a dangling note. (b) is strictly better: a member
superseding a foreign row is stopped with nothing created.

**Removed behaviour, adjudicated (removed-behavior-inventory law):** the OLD path composed
`[upsert, close]` into ONE `_apply` transaction ("a concurrent reader never observes a half-applied
supersession"). Under (b) the close and the upsert are now TWO transactions (close-first). Trade
consciously accepted: the guaranteed property MOVES from "old-and-new flip atomically" to "a denied
close creates nothing." The residual — an authorized close that succeeds, then the new-row UPSERT fails
(embed/store fault) — leaves the old row closed with `superseded_by` pointing at a not-yet-existent id.
Bounded: (i) `superseded_by` is `option<string>`, NOT a record link, so it does not dangle referentially;
(ii) the new id is deterministic, so a retry re-mints it in place; (iii) this failure path was already
non-atomic in spirit (the durable ledger write preceded the store txn). This is invisible to the frozen
suite (all pre-existing supersede tests route the admin subject on virgin DBs — the #131
fixture-hides-the-bug shape), so it will not red on its own.

**No-orphan property — VERIFIED (builder's own check, not a frozen pin; brief §ATOMICITY).** A one-time
verification (`TestNoOrphanNewRowAfterDeniedSupersede`, run + `1 passed in 1.92s`, then removed):
after bob's DENIED `remember(supersedes=<alice's id>)` → memory row count UNCHANGED (before==after),
bob's hostile text ABSENT from the table, AND alice's foreign row untouched (`valid_until`/`superseded_by`
both None). The frozen F1 pin asserts only the foreign-row-untouched half; this adds the no-orphan half.
The instrument, verbatim (per brief-base §1 — an instrument establishing a load-bearing claim is a
deliverable):
```python
# loremaster/tests/test_zz_noorphan_verify_63aiii.py  (run once, reported here, then deleted)
from typing import Any
import pytest
from loremaster import governed
from test_memory_retrofit_63a import (  # shipped fixtures/helpers, reused verbatim
    _bare, _exercise_remember, _one, alice_capability, bob_capability, retrofit_world,
)
from _surreal_harness import run

class TestNoOrphanNewRowAfterDeniedSupersede:
    async def test_a_denied_supersede_creates_no_orphan_new_row(
        self, retrofit_world: Any, alice_capability: Any, bob_capability: Any
    ) -> None:
        backend, _p, _k, admin_conn, _env, _keep = retrofit_world
        alice_id = await _exercise_remember(
            backend, text="alice note bob must not retire", capability=alice_capability)
        before = _one(await run(admin_conn, "SELECT count() FROM memory GROUP ALL"))["count"]
        hostile_text = "bob hostile replacement of alice's note (orphan probe)"
        with pytest.raises(governed.GovernedDenied):
            await _exercise_remember(
                backend, text=hostile_text, capability=bob_capability, supersedes=alice_id)
        after = _one(await run(admin_conn, "SELECT count() FROM memory GROUP ALL"))["count"]
        assert after == before, (
            f"a DENIED supersede created an ORPHAN new row (before={before} after={after}) — "
            "option (b) must authorize the close BEFORE creating the new row")
        texts = [row.get("text") for row in await run(admin_conn, "SELECT text FROM memory")]
        assert hostile_text not in texts, (
            f"bob's hostile new row landed as an orphan despite the denied close: {texts!r}")
        alice_row = _one(await run(admin_conn,
            "SELECT valid_until, superseded_by FROM type::record('memory', $id)",
            {"id": _bare(alice_id)}))
        assert alice_row["valid_until"] is None and alice_row["superseded_by"] is None, (
            "the denied supersede mutated alice's foreign row (F1 property broken)")
```

---

## §AUDIT-WIRING — the backend self-builds its AuditStore (RES-2, §10.6 rider v)

`LocalMemoryBackend.audit_store` (new property) returns
`AuditStore(url=self._url, namespace=self._namespace, database=self._database, user=self._user,
password=self._password)` — the SAME accessor idiom as `handle` (which returns a fresh `StoreHandle`
per access). **`build_memory_backend` needs NO new argument** (contract §FORKS-3, satisfiability-proven).

**Why this leaks nothing / needs no lifecycle:** `AuditStore.append_fragment` is PURE — it builds a
`TxnFragment` (a `CREATE` statement + params) and opens NO connection. `guarded_write` composes that
fragment into the guarded mutation's OWN `BEGIN…COMMIT`, executed through the memory backend's `handle`
(store.acquire). So the `audit_store` instance is used ONLY as a fragment builder; its own connection is
never opened, and a fresh instance per property access is free (an `asyncio.Lock` + stored wiring, GC'd).
The audit row therefore RIDES the close mutation's transaction — a rejected close rolls the audit back
too (the `TestGuardedWriteComposesAudit` rejected-rollback pin, unchanged and GREEN).

---

## §GATES — RED→GREEN receipts (test store `ws://127.0.0.1:18000`, never :18500)

**RED baseline at HEAD `3fea29a` (the 4 affected modules, `-n auto`):** `4 failed, 48 passed`. The 4
failures were EXACTLY the 4 target pins, right reasons:
- `TestGuardedWriteRefusesAnUnauditedBypass::…refuses_and_does_not_mutate` — `DID NOT RAISE
  GovernedAuditUnavailable`.
- `TestInvalidateRoutesThroughGuardedWrite::…supersede_close_a_foreign_owned_row` — the denied
  supersede retired alice's row (bare ungoverned UPDATE).
- `TestMemoryBypassCloseIsAudited::…invalidate…` + `…supersede_close…` — `assert 0 == 0 + 1` (no audit).

**GREEN after the fix (all `-n auto`, passed-COUNT in every tail):**

| gate | result |
|---|---|
| the 4 affected modules (substrate + retrofit + principal_delete + wire_isolation) | **52 passed** in 11.36s |
| all 9 `test_*_63a.py` + corpse B/C (`test_agent_capability_seams` + `test_keeps_store`) + `test_memory_backend` + `test_memory_cutover` | **320 passed** in 18.75s |
| 60/61/62 regression sweep (17 modules: `test_search`, `test_principals_{cli,store,schema}`, `test_principal_keys_{schema,store}`, `test_principal_delete_cascade_61`, `test_agent_capability`, `test_agent_owns_principal_schema`, `test_audit_{schema,store}`, `test_keeps_{cli,schema}`, `test_pdp_oracle_61b`, `test_visible_keeps_61b`, `test_surreal_store`, `test_tool_population_61b`) | **766 passed** in 59.41s |
| `test_mcp_server.py` (full — the composition root exercising `lore_remember`) | **667 passed, 3 warnings** in 149.98s |
| `uv run ruff check .` | **All checks passed!** |
| `bash scripts/typecheck.sh` | **every member OK** (loremaster 12 src, docs/eval 51, scripts, shellcheck 7 .sh) |

The wire-isolation gate + RES-3 fault-propagation gate STAY GREEN (inside the 52 / 320). No failing
tests outside the (now-closed) intended contract REDs.

---

## §MUTATION — the two mutation proofs (real tree, content-backed, restored byte-exact)

Both files were `cp -a`-backed to `/tmp` first (md5 captured); each mutation was an Edit, run, then the
inverse Edit; both files verified byte-exact against the backup (`diff -q` clean, md5 identical) AFTER
restore. HEAD `3fea29a` is itself the wrong build (the 4 RED baseline above), so these are the explicit
"revert MY fix on the fixed tree" proofs the brief names.

| mutation | pin(s) run | result |
|---|---|---|
| **RES-2** — remove the `requires_audit and audit is None: raise` block AND restore `if requires_audit and audit is not None:` (the HEAD silent-skip) | substrate refuse + its discriminator | refuse pin REDS (`DID NOT RAISE GovernedAuditUnavailable`); discriminator STAYS GREEN → the refusal is bypass-specific, not a blanket `audit=None` refusal |
| **F1** — replace the guarded supersede-close in `remember` with a bare ungoverned `UPDATE` via `_apply` (the HEAD §F1 defect) | supersede-deny + supersede-audit + owner control | supersede-deny REDS (bob retires alice's note, no `GovernedDenied`); supersede-audit REDS (`0 == 0+1`); owner positive control STAYS GREEN → both the guard AND the RES-2 audit are load-bearing on that path |

Backup receipts: `governed.py` md5 `4e3aa473347b8cff0cd1b77318d36138` (identical pre/post-restore);
`local.py` md5 `45e673447e4d3ae07e564f0c4444e5b0` (identical pre/post-restore). No git state was mutated
during the proofs.

---

## §REUSE — DRY ledger

| new symbol | lore/grep query run | what it returned | disposition |
|---|---|---|---|
| `LocalMemoryBackend.audit_store` (property) | `grep -rn "AuditStore\|audit_store" loremaster/loremaster/` + `lore_get_symbol LocalMemoryBackend.handle` | no pre-existing audit-store accessor on any governed backend; `handle` is the sibling connection-owner accessor the RES-2 rider-v names to mirror | **HAND-ROLLED**, mirroring the `handle` accessor idiom (the contract explicitly designed this shape — "mirror the handle accessor idiom; do NOT add a constructor arg"). Not cross-caller POLICY (it is a per-backend accessor over the backend's own params, not a duplicated decision); ONE production consumer path (`remember` close + `invalidate`). |

`GovernedAuditUnavailable` was a contract-authored stub (I added only the `raise` site, not the type).
The supersede-close `set_fragment` string / the deleted `_close_superseded_fragment` are not new symbols.
No policy was cloned — the authorization + audit-compose decisions live entirely in the shared
`governed.guarded_write` seam; `remember`/`invalidate` ROUTE through it (routing-is-not-sharing satisfied:
the classification, the deny, the audit compose are all the seam's, not hand-rolled here).

---

## §FORKS — escalations for lead-63

**FORK 1 (ESCALATE) — the production audit-DDL gap (RES-2 completeness).** The RES-2 fix wires a real
`AuditStore` as a compose-time `append_fragment` builder, and the pins prove +1 audit rows because the
audit-specific tests ready the `audit` table on the unified test DB (`_build_audit_store(env).ensure_ready()`).
**In PRODUCTION the memory DB has NO `audit` table** — no `AuditStore` is constructed/`ensure_ready`'d at
the composition root (`server.py::build_app_context`), and `generate_audit_ddl`'s own docstring says the
slice is applied by "a future AuditStore". So a production admin-bypass close would land its audit CREATE
in an auto-created SCHEMALESS `audit` table (no ASSERT constraints), or fail if the DB is strict.
- **Severity: LATENT.** The admin bypass is unreachable in the single-principal dogfood fleet (cold-audit
  RES-2: `requires_audit` needs an admin acting on a row a member could not write). The 4 pins are GREEN;
  the behavioural fix is correct.
- **The fix (for whoever lands it):** wire an `AuditStore` at the composition root and `ensure_ready()` it
  on the unified DB (applying `generate_audit_ddl`) — the natural home when the audit trail becomes
  load-bearing (64: task/finding ledgers pass a real audit store per cold-audit RES-4/RES-5). This is a
  composition-root change beyond my 2-file writable scope, so I flag rather than land it.
- **Named re-open trigger:** *the first time an admin bypass close is reachable in production* — i.e.
  post-65 multi-principal / hosted, OR when 64 wires the audit store on the unified DB, whichever first.

**NOTE 2 (non-blocking) — a permanent no-orphan pin.** The option-(b) atomicity trade (a denied
supersede creates no orphan) is verified once (§ATOMICITY) but NOT pinned (the brief scoped it as "my own
verification, not the frozen pins"). A cheap follow-up: promote `TestNoOrphanNewRowAfterDeniedSupersede`
to a committed pin so a future refactor that re-orders the close after the create reds. Recommend the
lead decide whether to fold it into this wave or 63b (per "every audit-caught defect class becomes an
invariant test" — but this is a design trade, not an audit-caught defect, so it is the lead's call).

**NOTE 3 (non-blocking, contract-inherited) — the `_build_audit_store` DRY.** Two test-local copies of
`_build_audit_store` (`test_governed_substrate_63a.py`, `test_memory_retrofit_63a.py`); the shared home is
`_governed_contract`. The contract-63a-iii author already flagged this (a fixture CONSTRUCTOR, not policy —
§6 trivia). Untouched here (test-side, out of my production-only writable scope).

## §GATE-DETAIL — the two production files changed

- `loremaster/loremaster/governed.py::guarded_write` — +the `GovernedAuditUnavailable` raise (step 2b,
  before the mutation) + the compose guard simplified to `if requires_audit:`.
- `loremaster/loremaster/memory/local.py` — +`import AuditStore`; +`audit_store` property (after
  `handle`); `remember` supersede-close routed through `guarded_write` (close-first, option b);
  `invalidate` `audit=None`→`audit=self.audit_store`; `_close_superseded_fragment` DELETED (dead after the
  re-route). `_WRITE_PARAM_PREFIX` retained (still used by `_upsert_fragment`).

There are 0 failing tests outside our present scope in every sweep I ran.
