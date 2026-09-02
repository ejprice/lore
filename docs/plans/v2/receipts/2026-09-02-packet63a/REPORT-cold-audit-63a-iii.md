# REPORT-cold-audit-63a-iii — COLD-AUDIT (fresh-context REFUTE) of the 63a-iii NO-GO fix

- `brief-base v14 read`
- `brief project v7 read`
- store reference consulted: `docs/reference/surrealdb-31-capabilities.md` — §2 (record<> links /
  CONTENT REPLACES the whole row / `option<string>` vs `type::record()` / explicit projection reads a
  NONE column back as None), §3 (execute_read_transaction / BEGIN…COMMIT atomicity). Cited, not
  re-transcribed.

## SUMMARY BLOCK

- receipt: `brief-base v14 read` · `brief project v7 read`
- **state: done — VERDICT: NO-GO.** The prior NO-GO (F1 supersede-close + RES-2 fail-open) is
  genuinely CLOSED — verified by live construction — and every gate re-runs GREEN with matching
  counts. **But the write-verb enumeration the brief demanded found the THIRD bypass:** the
  `remember` **create-path UPSERT** overwrites a content-colliding FOREIGN-owned row (re-owns /
  re-scopes / revives it) **bypassing `guarded_write`**, because `derive_memory_id` folds in NO owner.
  Constructed live (cross-principal, intra-principal-live-today, and revive). Same class as F1, green
  at every gate — the exact "find the third if it exists" the brief anticipated.
- deviations from a clean audit: none — I edited no tree; all constructions live in a
  provenance-asserted scratch copy (`loremaster.__file__ = /tmp/audit63aiii-x1/loremaster/loremaster/__init__.py`),
  pasted verbatim in §REPRO.
- **Packages considered:** none — no mechanism specified (a cold audit builds no shipped code; the
  constructions reuse the shipped `test_memory_retrofit_63a` harness verbatim).
- **Reuse ledger:** none — I authored no shipped symbol (the repro reuses shipped fixtures + one
  local `_bare_s` stringify helper; test-scratch trivia, discarded with the scratch tree, pasted in §REPRO).
- **Graded:** `b0453c7` · HEAD-at-report: `b0453c7` · SAME.
- **⚠ MY NO-GO RESTS SOLELY ON F-A** (brief scope (2): "are ALL memory write verbs now guarded — the
  third-verb hunt"). It is NOT held on #438 (see next line). F1 (scope 1), RES-2 (scope 3), and the
  atomicity residual (scope 4) are all CLEAN; scope (2) is NOT — the create-path is an unguarded write
  on a foreign-owned row.
- **DELTA acknowledged (lead-63 signal `#8032`, thread `packet63-cold-audit-iii`, seen this turn):**
  #438 is a design-§10.8-RULED, KNOWN 63a-iv follow-on (composition-root audit-DDL wiring lands next),
  NOT a defect for me to discover and NOT a reason to NO-GO `b0453c7` — I do NOT hold the verdict on
  it. §FORK-1 records it for focus-5 completeness (reachability confirmed; the "latent" premise is
  false if the fleet principal is admin, per §10.8) as a tracked follow-on, not a NO-GO driver.
- decisions-needed (fork for the operator): **F-A disposition** — F-A rides the INTENDED
  content-addressed dedup (identical text ⇒ one row), and its high-harm re-scope/hide variant is not
  wire-reachable today (`scope=` unwired at `server.py:4143`), so whether to fix-now, accept-a-named-bound,
  or issue a broader dedup×ownership design ruling is the operator's call — but the §9 write-isolation
  target is not met as it stands.
- receipt POINTERS: write-verb table → §WRITE-VERBS; the NO-GO finding + live repro → §F-A; F1-closed
  proof → §F1; RES-2 → §RES-2; audit-DDL gap → §FORK-1; atomicity → §ATOMICITY; reinforce → §F-B;
  gate re-runs → §GATES; residuals → §RES; the instrument verbatim → §REPRO.

---

## §GATES — every gate re-run on the TEST store `ws://127.0.0.1:18000` (NEVER :18500)

All commands `uv run pytest -p no:cacheprovider -n auto -q`. A green claim carries a passed-COUNT.

| gate | result | matches build report? |
|---|---|---|
| the 9 `test_*_63a.py` (incl. `test_wire_isolation_63a`) + corpse B/C (`test_agent_capability_seams` + `test_keeps_store`) + `test_memory_backend` + `test_memory_cutover` | **320 passed** in 18.16s | ✓ (build §GATES "320 passed") |
| `test_mcp_server.py` (full, `-rs`) | **667 passed, 0 skipped**, 3 warnings in 148.57s | ✓ (0 skipped confirmed — `-rs` printed no skip lines) |
| 60/61/62 sweep (17 modules: `test_search`, `test_principals_{cli,store,schema}`, `test_principal_keys_{schema,store}`, `test_principal_delete_cascade_61`, `test_agent_capability`, `test_agent_owns_principal_schema`, `test_audit_{schema,store}`, `test_keeps_{cli,schema}`, `test_pdp_oracle_61b`, `test_visible_keeps_61b`, `test_surreal_store`, `test_tool_population_61b`) | **766 passed** in 58.92s | ✓ (build §GATES "766 passed") |
| `uv run ruff check .` | **All checks passed!** | ✓ |
| `bash scripts/typecheck.sh` | **every member OK** (loremaster 249 src, docs/eval 51, scripts, shellcheck 7 .sh) | ✓ |

**The build is exactly as green as claimed.** This is the trap the cold audit exists for: green at
every gate, and still shipping a write-isolation bypass no pin exercises (the create-path collision).

---

## §WRITE-VERBS — the enumeration the brief demanded (every `memory/local.py` mutation of an EXISTING row)

Enumerated by grepping every SurrealQL mutation verb (`UPDATE`/`DELETE`/`UPSERT`/`REMOVE`) + every
`_apply`/`_query` write site, then tracing each to its authorization.

| # | write path | verb / seam | mutates existing foreign row? | guarded? | verdict |
|---|---|---|---|---|---|
| 1 | `remember` **create** | `_upsert_fragment` → `UPSERT type::record('memory',$id) CONTENT` via `_apply` | **YES** — `derive_memory_id(text, refs_stamp)` folds in NO owner, so a content-collision overwrites a foreign-owned row | **NO** — no `guarded_write`, no `WHERE` ownership guard | **BYPASS → F-A (NO-GO)** |
| 2 | `remember` **supersede-close** | `governed.guarded_write(Action.WRITE, audit=self.audit_store)` | yes (the old row) | **YES** ✓ | GUARDED (the 63a-iii fix — verified §F1) |
| 3 | `invalidate` | `governed.guarded_write(Action.WRITE, audit=self.audit_store)` | yes (the target row) | **YES** ✓ | GUARDED |
| 4 | `recall` → `_reinforce` | `UPDATE type::record('memory',$id) SET importance=…` via `_query` (per recalled row) | **YES** — the recalled set includes read-visible foreign-owned rows | **NO** — bare UPDATE | **BYPASS → F-B (residual; non-governed column, benign)** |
| 5 | `restore_from_ledger` / `_replay_record` | `_upsert_fragment` via `_apply` | boot/admin replay only (not member-reachable) | n/a | RES-1 (prior audit — replay drops governance stamps) |
| 6 | `rebuild_embeddings` / `_recreate_memory_table` | `REMOVE TABLE` + replay | boot/admin DDL only | n/a | RES-1 |

**Two of the four member-reachable existing-row mutations bypass the guard** (rows 1 & 4). Row 2 is
the wave's fix and is genuinely closed; row 1 is the NO-GO.

---

## §F-A — THE NO-GO FINDING (constructed live)

**`loremaster/memory/local.py::LocalMemoryBackend.remember` (the CREATE path, `_apply([self._upsert_fragment(memory_id, content)])`, ~line 678) — a member OVERWRITES another owner's memory row by re-`remember`ing its text, bypassing `guarded_write`.**

### The defect
`memory_id = derive_memory_id(text, refs_stamp)` (`memory/backend.py:174`) is
`uuid5(NAMESPACE_URL, "memory:{text}:{refs_stamp}")` — **the id is a pure function of the CONTENT; no
owner is folded in.** So two DIFFERENT owners writing the identical `(text, refs)` mint the identical
id. The create-path then does an unconditional `UPSERT … CONTENT` (`_upsert_fragment`, ~line 1338) via
`_apply` — a plain `execute_transaction`, **no `guarded_write`, no `WHERE` ownership guard**. On a
collision the UPSERT **REPLACES the whole existing row** (store-ref §2 — `CONTENT` replaces), stamping
the new owner (`content[_COL_OWNER_PRINCIPAL/_OWNER_AGENT/_SCOPE]`, ~line 675-677) over the victim's,
and resetting `valid_until`/`superseded_by`/`importance`/`labels`/`source`.

The design's model of the create is BLIND to this: §2.5 says *"a CREATE of the new one — the creator
owns it,"* and the build comment (`local.py` ~672) says *"remember is a CREATE of a NEW row (the
creator owns it), so it stamps directly."* **A content-addressed create is not always a create — on a
collision it is an UPDATE of an existing, possibly foreign-owned row**, and that update is exactly the
class §2.5/F1 rule must route through `guarded_write`. §6 point 5 (a named §9 target) explicitly
forbids *"writable-but-invisible"* rows; this lets a member WRITE a row it may not see (if it knows the
text).

### Constructed live (provenance-asserted scratch, HEAD `b0453c7`) — three constructions, all GREEN
`loremaster.__file__ = /tmp/audit63aiii-x1/loremaster/loremaster/__init__.py` (imports resolve INSIDE
the copy — #140). Full instrument in §REPRO.

1. **Cross-principal seizure + re-scope** (`TestCandidateA_CreateCollisionOverwritesForeignRow`):
   alice remembers a note (default project-keep, alice owns it). CONTROL — bob's guarded `invalidate`
   of it DENIES (the guarded door works). BYPASS — bob `remember(<alice's exact text>, scope="principal-private")`
   → the id collides → the create-UPSERT **seizes ownership to bob AND re-scopes the row to bob's
   private scope**. `after.owner_principal == bob`, `after.scope == "principal-private"`.
2. **Intra-principal — LIVE TODAY** (`TestCandidateA_IntraPrincipalLiveToday`): worker_1 (alice's
   agent) writes a `principal-private` note. worker_2 (a SECOND agent of the SAME principal) CANNOT
   `guarded_write` it (WRITE principal-private = exact `(principal, agent)`, `pdp.py:408`) — CONTROL:
   worker_2's `invalidate` DENIES — yet worker_2 READS it (READ principal-private = principal only,
   `pdp.py:397`) and SEIZES it via re-`remember`. `after.owner_agent` flips to worker_2. This is the
   same *"a sibling agent cannot guarded_write another agent's private note, yet CAN [seize] it"* edge
   the prior F1 audit named as live within one principal.
3. **Revive of a retired note** (`TestCandidateA_ReviveRetiredForeignNote`): alice remembers then
   `invalidate`s her own note (`valid_until` set). bob re-`remember`s the identical text → the
   create-UPSERT resets `valid_until` to None — **bob un-retires alice's deliberately-retired note.**

### Reachability / severity gradient (HONEST — not overstated)
- **Backend / substrate (constructed, undisputed):** the hole is in the shipped substrate's first
  consumer. §1.2 ships `remember` as part of the ONE-IMPLEMENTATION address 64 builds on; `remember(scope=)`
  is the seam 63b/64/admin tools will call with explicit scopes.
- **Over the wire TODAY:** `AppContext.remember` (`server.py:4143-4151`) passes caller-controlled
  `text` + `supersedes` but does **NOT** expose `scope=` yet, so the HIGH-harm **re-scope / hide**
  variant is not wire-reachable *today*. What IS wire-reachable today: **ownership seizure + revive**
  (text is caller-controlled; default project-keep scope). Wire harm today is therefore
  LOW-to-MODERATE (project-keep WRITE is household-based, so seizure does not lock out a household;
  revive is reversible). ⚠ Design §2.4 explicitly intends `scope=` *"on `lore_remember`"* — the moment
  it is wired, the HIGH-harm hide/re-scope becomes wire-reachable.
- **Post-65 multi-principal / hosted:** full cross-principal write-isolation break (constructed
  construction 1) — the §9 headline.

### Why this is a NO-GO (and how it differs from F1)
By the brief's own criterion — *"If ANY existing-row mutation bypasses the guard → NO-GO"* — this
qualifies: it is constructed, green at every gate, in the SAME class as F1 (a member mutates a
foreign-owned existing row without `guarded_write`), and it defeats the §9 write-isolation target the
wave names for itself. It is WEAKER than F1 in two honest respects: (a) it is spec-SILENT (§2.5 assumes
create = new row) rather than contradicting an explicit ruling, and (b) its high-harm variant is not
wire-reachable *today* (scope= unwired). As the independent instrument my verdict is **NO-GO**; the
DISPOSITION (fix-now vs. ship-with-a-named-bound-because-scope=-is-unwired vs. a broader dedup×ownership
ruling) is the operator's — exactly the structure the prior F1 audit used.

### The fix + the missing pin (for whoever lands it)
The create-path must not silently overwrite a foreign-owned row. Two shapes (a DESIGN choice — dedup
semantics — so surfaced, not prescribed): **(a)** when the deterministic id already names an EXISTING
row, route the write through `guarded_write` (or an explicit ownership check) — DENY a member
overwriting a foreign row; or **(b)** fold the owner into `derive_memory_id` so different owners never
collide (changes dedup from global to per-owner). **Missing pin:** `remember(<a foreign-owned row's
exact text+refs>)` by a non-owner → DENIES (or mints a distinct id), the foreign row UNCHANGED; positive
control: the OWNER re-remembering its own text dedups in place. No pin in the suite exercises a
create-path id COLLISION across owners — the QUANTIFIER-LAW gap, one write verb over from F1.

---

## §F1 — the prior NO-GO is genuinely CLOSED (verified by construction)

`TestF1SupersedeCloseNowDenies` (§REPRO), GREEN:
- bob `remember(supersedes=<alice's id>)` now raises `GovernedDenied`; alice's row is UNCHANGED
  (`valid_until` None, owner unchanged) AND **no orphan new row lands** (`after_count == before_count`
  — the option-(b) close-first no-orphan property, verified live).
- POSITIVE CONTROL: alice supersedes her OWN row → succeeds (`valid_until` set).

Code review confirms the mechanism: `remember`'s supersede-close now routes through
`governed.guarded_write(Action.WRITE, row_id=supersedes, audit=self.audit_store, store=self.handle)`
(`local.py:626-642`), the bare `_close_superseded_fragment` UPDATE is DELETED, and the close runs
BEFORE the ledger/new-row write. The §2 landmine is honoured (`superseded_by = '<memory_id>'` string
literal, not `type::record()`). **F1 is closed.**

---

## §RES-2 — the audit fail-open is CLOSED; no OTHER audit-skip hole in memory

- `governed.guarded_write` now RAISES `GovernedAuditUnavailable` when `requires_audit and audit is
  None`, BEFORE composing/running the mutation (`governed.py:276-281`), and the later compose guard is
  simplified to `if requires_audit:` (the silent-skip is GONE, `governed.py:305`). Verified by reading;
  build §MUTATION mutation-proved it (restore the silent-skip → refuse pin reds; discriminator stays
  green).
- **No other bypass-reachable write passes `audit=None`:** the ONLY two `guarded_write` production
  consumers are `memory/local.py::invalidate` (line 724) and the supersede-close (line 640) — BOTH
  pass `audit=self.audit_store` (grep: 2 sites, both `audit=self.audit_store`). There is no other
  `guarded_write` caller in `loremaster/loremaster/` (grep). So the substrate fail-open is closed and
  the memory consumer is wired. **RES-2 closed** — with the caveat that the audit ROW has nowhere
  DDL'd to land in production (§FORK-1).

---

## §FORK-1 — the production audit-DDL gap (#438): design-RULED "wire it now", NOT wired at `b0453c7`

**Reachability (my brief's focus):** `requires_audit` fires iff `allowed AND subject.role == admin AND
action mutating AND a member of the same identity could NOT have done it` (`pdp.py:462-466`). In the
single-principal fleet this is UNREACHABLE **only if the fleet principal is a `member`.** ⚠ **Design
§10.8 (`docs/design/2026-08-28-packet63-retrofit-rulings.md`, RULED at `b0453c7`) already refuted the
"latent" premise:** *"A bound resting on an unprovisioned role is not a bound"* — packet 65 provisions
the fleet principal and its role is not yet fixed; if it is `admin`, the §2.1 migration itself
MANUFACTURES admin-bypass acts (deleting/superseding an UNOWNED-LEGACY owner-NONE row fails every
member predicate, succeeds as admin → `requires_audit` fires) at the first post-cutover cleanup — a
SINGLE-principal reachability the build's *"post-65 multi-principal"* framing understates.

**So the disposition is NOT open — §10.8 RULED option (b): WIRE IT NOW (63a-iii/-iv).** But
`b0453c7` has **NOT** wired it: `grep -c "AuditStore|generate_audit_ddl" server.py` = **0**. The RES-2
memory-audit fix therefore composes an audit CREATE that, in production, lands in an AUTO-CREATED
SCHEMALESS `audit` table — and §10.8 point 2 shows that state POISONS its own re-opening (a later
`DEFINE TABLE IF NOT EXISTS audit SCHEMAFULL` is a silent no-op over it; #107's shape aimed at the
audit trail).

**Verdict:** NOT a NO-GO — and lead-63's DELTA (signal `#8032`, seen this turn) confirms the
disposition: #438 is a design-§10.8-RULED, KNOWN **63a-iv follow-on** (composition-root audit-DDL
wiring lands next, with three riders: composition-root pin, a schemaful-discriminating +1/ASSERT-reject
leg, and the #139 in-image assertion). The governed memory path is UNSERVED until the 65 cutover (§2.6),
so nothing bites today; the wiring MUST land before that cutover (a pre-cutover admin bypass would
auto-create a permanently-schemaless trail, §10.8 pt 2). I record it here for focus-5 completeness only
— it is a tracked follow-on, NOT part of my NO-GO. (One reachability refinement worth carrying into
63a-iv: §10.8 already shows the admin bypass is reachable INTRA-principal — a §2.1 migration cleanup of
an UNOWNED-LEGACY row by an admin principal — so the trigger is not only "multi-principal".)

---

## §ATOMICITY — option (b) close-first: SOUND for the security property, one narrow integrity residual

The build chose option (b): the guarded close runs BEFORE the ledger write + new-row UPSERT.
- **Security property (denied close → no orphan): SOUND, CONSTRUCTED.** `TestF1…_denies_and_no_orphan`
  proves `after_count == before_count` after a DENIED supersede — nothing lands.
- **The disclosed residual (authorized close succeeds, then embed/UPSERT fails): a real, narrow
  integrity window, and the build's "bounded" argument is MOSTLY but not fully sound.** `superseded_by`
  is `option<string>` (no referential dangle ✓) and the id is deterministic (a retry re-mints ✓) — BUT
  the close now runs BEFORE the ledger write (`local.py`: close @626 → ledger @647 → embed @658 →
  UPSERT @678), so a crash **between the close and the ledger write** loses the successor ENTIRELY
  (not merely "delayed" — there is no automatic retry; it needs the caller to re-issue the identical
  `remember`), leaving the old row closed with `superseded_by` → a memory that exists NOWHERE. The
  pre-fix one-txn compose was atomic here; option (b) traded that for close-first authorization. LOW
  severity (narrow crash window, recoverable by re-issue), DISCLOSED by the build — a residual, not a
  NO-GO, but the "retry re-mints" framing understates the crash-before-ledger case.

---

## §F-B — `_reinforce` writes a foreign-owned row (bare UPDATE), non-governed column (residual)

`recall` calls `self._reinforce(memories)` (`local.py:841`) on the recalled set — which includes
read-visible FOREIGN-owned rows — and `_reinforce` issues a bare `UPDATE … SET importance = math::min(…)`
(`local.py:1131`) with NO `guarded_write`. CONSTRUCTED (`TestCandidateB_ReinforceBumpsForeignRow`,
§REPRO, GREEN): with bob householded into the project keep, bob's `recall` bumps alice's foreign-owned
note's importance; alice still owns it. This is technically *"an existing-row mutation that bypasses
the guard"* — but **`importance` is a NON-governed column** (governance columns are
owner_principal/owner_agent/scope), reinforcement is an INTENDED read-side-effect (recall reinforces
what it returns), and the bump is bounded (`math::min` at the ceiling). **Residual, not a NO-GO:** it
touches no isolation-bearing column and does no data loss / ownership change. Surfaced for the operator
to rule whether reinforcement on a not-write-authorized row (e.g. an intra-principal sibling agent's
private note it can read but not `guarded_write`) needs governing, or is an accepted read-side-effect.

---

## §RES — residual table (each an individual verdict — "the rest look fine" is banned)

| # | residual | verdict |
|---|---|---|
| **RES-A1** | F-A high-harm variant (re-scope/hide) requires `scope=` exposure on `lore_remember` (design §2.4 intends it; currently unwired at `server.py:4143`) OR a 64/admin backend consumer passing an explicit scope. | **Named bound on F-A's blast radius TODAY**, not a separate defect. Re-open trigger: the commit that wires `scope=` into `AppContext.remember`, OR the first 64/admin consumer calling `backend.remember(scope=<private>)`, OR the 65 cutover — whichever first. |
| **RES-2-DDL** (§FORK-1) | The RES-2 memory audit CREATE has no DDL'd `audit` table in production (`server.py` audit refs = 0); design §10.8 RULED "wire it now (63a-iii/-iv)"; `b0453c7` does not. | **Design-ruled REQUIRED-and-PENDING.** Must land (with §10.8's 3 riders) before the 65 cutover; a pre-cutover admin bypass would auto-create a permanently-schemaless trail (§10.8 pt 2, unrepairable by IF NOT EXISTS). |
| **RES-ATOM** (§ATOMICITY) | Option-(b) authorized-close-then-crash-before-ledger loses the successor until the caller re-issues (the old row closed, `superseded_by` → a nonexistent id). | **Latent, LOW, disclosed.** Narrow crash window; recoverable by re-issuing the deterministic `remember`. The "retry re-mints" framing understates the crash-before-ledger case; worth a 63b note (compose the guarded close WITH the upsert if `guarded_write` is ever given a compose-with-caller-txn shape). |
| **RES-B** (§F-B) | `_reinforce` bumps a read-visible foreign-owned row's `importance` via a bare UPDATE (no guard). | **By-design read-side-effect on a non-governed column; benign.** Bounded (ceiling), no isolation column touched, no data loss. Operator to rule if reinforcement on a not-write-authorized row needs governing. |
| **RES-1** (inherited) | `rebuild_embeddings` / ledger replay re-mint memory rows WITHOUT governance stamps → NONE-scope (member-invisible, admin-only). | **Known bound (prior audit RES-1 / R5), fail-CLOSED + recoverable.** Not re-examined here (unchanged by `b0453c7`); named re-open trigger = first embedding-schema change after cutover. |

---

## §REPRO — the instrument, verbatim (brief-base §1: an instrument establishing a load-bearing claim is a deliverable)

Run in the provenance-asserted scratch copy (`scripts/scratch_copy.sh /tmp/audit63aiii-x1`,
`loremaster.__file__ = /tmp/audit63aiii-x1/loremaster/loremaster/__init__.py`) at HEAD `b0453c7` →
**`6 passed in 5.06s`**. Reuses the SHIPPED `test_memory_retrofit_63a` fixtures/seam verbatim.

```python
# loremaster/tests/test_zz_coldaudit63aiii_repro.py  (scratch; pasted per brief-base §1)
from typing import Any
import pytest
from loremaster import governed
from _surreal_harness import run
from test_memory_retrofit_63a import (  # SHIPPED fixtures/helpers, reused verbatim
    _EMAIL_ALICE, _EMAIL_BOB, _bare, _exercise_invalidate, _exercise_recall,
    _exercise_remember, _minted_credential, _one, alice_capability, bob_capability, retrofit_world,
)

def _bare_s(value: Any) -> str:
    """Bare id of a str OR a RecordID (the admin SELECT returns RecordID objects)."""
    text = str(value)
    return text.partition(":")[2] or text

async def _read_governed(admin_conn: Any, memory_id: str) -> dict[str, Any]:
    return _one(await run(admin_conn,
        "SELECT owner_principal, owner_agent, scope, valid_until, importance "
        "FROM type::record('memory', $id)", {"id": _bare_s(memory_id)}))

class TestF1SupersedeCloseNowDenies:
    async def test_bob_supersede_close_of_alice_row_denies_and_no_orphan(
        self, retrofit_world: Any, alice_capability: Any, bob_capability: Any) -> None:
        backend, _p, _k, admin_conn, _env, _keep = retrofit_world
        alice_id = await _exercise_remember(
            backend, text="F1 alice note bob must not retire", capability=alice_capability)
        before_count = _one(await run(admin_conn, "SELECT count() FROM memory GROUP ALL"))["count"]
        before = await _read_governed(admin_conn, alice_id)
        assert before["valid_until"] is None
        with pytest.raises(governed.GovernedDenied):   # THE FIX: bob's supersede-close DENIES
            await _exercise_remember(backend, text="F1 bob hostile replacement",
                capability=bob_capability, supersedes=alice_id)
        after = await _read_governed(admin_conn, alice_id)
        after_count = _one(await run(admin_conn, "SELECT count() FROM memory GROUP ALL"))["count"]
        assert after["valid_until"] is None, "alice's row was retired (F1 NOT closed)"
        assert str(after["owner_principal"]) == str(before["owner_principal"])
        assert after_count == before_count, "a DENIED supersede created an orphan new row"

    async def test_owner_can_supersede_own_row(self, retrofit_world: Any, alice_capability: Any) -> None:
        backend, _p, _k, admin_conn, _env, _keep = retrofit_world  # POSITIVE CONTROL
        old_id = await _exercise_remember(backend, text="F1 alice own note", capability=alice_capability)
        await _exercise_remember(backend, text="F1 alice replacement",
            capability=alice_capability, supersedes=old_id)
        after = await _read_governed(admin_conn, old_id)
        assert after["valid_until"] is not None

class TestCandidateA_CreateCollisionOverwritesForeignRow:
    async def test_bob_reremember_seizes_and_rescopes_alices_row(
        self, retrofit_world: Any, alice_capability: Any, bob_capability: Any) -> None:
        backend, principal_store, _k, admin_conn, _env, _keep = retrofit_world
        alice = await principal_store.get_by_email(_EMAIL_ALICE)
        bob = await principal_store.get_by_email(_EMAIL_BOB)
        alice_pid = _bare_s(alice.id); bob_pid = _bare_s(bob.id)
        colliding_text = "candidate A collision text — same for alice and bob"
        alice_id = await _exercise_remember(backend, text=colliding_text, capability=alice_capability)
        before = await _read_governed(admin_conn, alice_id)
        assert _bare_s(before["owner_principal"]) == alice_pid, "setup: alice must own her note"
        alice_scope = before["scope"]
        with pytest.raises(governed.GovernedDenied):   # CONTROL: guarded invalidate door DENIES
            await _exercise_invalidate(backend, memory_id=alice_id, capability=bob_capability)
        control = await _read_governed(admin_conn, alice_id)
        assert _bare_s(control["owner_principal"]) == alice_pid, "guarded door leaked"
        bob_id = await _exercise_remember(         # THE BYPASS
            backend, text=colliding_text, capability=bob_capability, scope="principal-private")
        assert _bare_s(bob_id) == _bare_s(alice_id), "PREMISE: the content-addressed id must collide"
        after = await _read_governed(admin_conn, alice_id)
        assert _bare_s(after["owner_principal"]) == bob_pid, (
            f"create-path did NOT overwrite: owner still {after['owner_principal']!r}")
        assert after["scope"] == "principal-private" and after["scope"] != alice_scope, (
            f"create-path did NOT re-scope: scope still {after['scope']!r} (was {alice_scope!r})")

class TestCandidateA_IntraPrincipalLiveToday:
    async def test_sibling_agent_seizes_a_principal_private_note_it_cannot_write(
        self, retrofit_world: Any, alice_capability: Any) -> None:
        backend, principal_store, _k, admin_conn, _env, _keep = retrofit_world
        alice = await principal_store.get_by_email(_EMAIL_ALICE); alice_pid = _bare_s(alice.id)
        text = "alice principal-private note only worker_1 may write"
        worker1_id = await _exercise_remember(
            backend, text=text, capability=alice_capability, scope="principal-private")
        owner1 = _bare_s((await _read_governed(admin_conn, worker1_id))["owner_agent"])
        async with _minted_credential(
            retrofit_world, email=_EMAIL_ALICE, agent_name="alice_worker_2") as worker2:
            with pytest.raises(governed.GovernedDenied):   # CONTROL: sibling cannot guarded_write
                await _exercise_invalidate(backend, memory_id=worker1_id, capability=worker2)
            worker2_new = await _exercise_remember(         # BYPASS: seize via re-remember
                backend, text=text, capability=worker2, scope="principal-private")
            assert _bare_s(worker2_new) == _bare_s(worker1_id)
        after = await _read_governed(admin_conn, worker1_id)
        assert _bare_s(after["owner_principal"]) == alice_pid
        owner2 = _bare_s(after["owner_agent"])
        assert owner2 != owner1, (
            f"create-collision did NOT re-own to the sibling agent (owner_agent still {owner1!r})")

class TestCandidateA_ReviveRetiredForeignNote:
    async def test_bob_revives_alices_retired_note(
        self, retrofit_world: Any, alice_capability: Any, bob_capability: Any) -> None:
        backend, _p, _k, admin_conn, _env, _keep = retrofit_world
        text = "alice note alice will retire then bob revives"
        alice_id = await _exercise_remember(backend, text=text, capability=alice_capability)
        await _exercise_invalidate(backend, memory_id=alice_id, capability=alice_capability)
        retired = await _read_governed(admin_conn, alice_id)
        assert retired["valid_until"] is not None, "setup: alice's note must be retired"
        bob_id = await _exercise_remember(backend, text=text, capability=bob_capability)
        assert _bare_s(bob_id) == _bare_s(alice_id)
        revived = await _read_governed(admin_conn, alice_id)
        assert revived["valid_until"] is None, "create-collision did NOT revive the retired note"

class TestCandidateB_ReinforceBumpsForeignRow:
    async def test_bob_recall_reinforces_alices_foreign_row(
        self, retrofit_world: Any, alice_capability: Any, bob_capability: Any) -> None:
        backend, _p, keep_store, admin_conn, _env, project_keep = retrofit_world
        await keep_store.add_household_member(
            keep_id=str(project_keep.id), member_email=_EMAIL_BOB)
        alice_id = await _exercise_remember(
            backend, text="candidate B reinforce topic zulu marker", capability=alice_capability)
        i0 = float((await _read_governed(admin_conn, alice_id))["importance"])
        hits = await _exercise_recall(
            backend, query="candidate B reinforce topic zulu marker", capability=bob_capability)
        assert any(_bare_s(h.id) == _bare_s(alice_id) for h in hits)
        after = await _read_governed(admin_conn, alice_id)
        assert float(after["importance"]) > i0, "reinforce did NOT bump alice's foreign row"
```

---

## VERDICT: **NO-GO**

The 63a-iii fix `b0453c7` **correctly and completely closes the prior NO-GO** — F1 (supersede-close)
and RES-2 (unaudited fail-open) are both verified closed by live construction, and every gate re-runs
GREEN with matching counts (320 / 667-0skipped / 766 / ruff / typecheck). **But the write-verb
enumeration the brief demanded found the THIRD bypass (F-A):** the `remember` create-path UPSERT
overwrites a content-colliding FOREIGN-owned row — re-owning, re-scoping, and reviving it — bypassing
`guarded_write`, because `derive_memory_id` folds in no owner. Constructed live (cross-principal seizure
+ re-scope, intra-principal live-today seizure of a principal-private note the sibling cannot
`guarded_write`, and revive of a retired note), green at every gate — the exact QUANTIFIER-LAW pattern
one write verb over from F1. **The NO-GO rests SOLELY on F-A** (brief scope (2), the third-verb hunt):
scopes (1) F1, (3) RES-2, and (4) atomicity are all clean, but scope (2) is not — a member can mutate a
foreign-owned row via the unguarded create path. As the independent instrument my verdict is **NO-GO**,
with the fix and the missing pin named. The F-A DISPOSITION is the operator's, not mine: F-A rides the
INTENDED content-addressed dedup and its high-harm variant is not wire-reachable today (`scope=` unwired),
so ship-with-a-named-bound is a legitimate operator option — but the §9 write-isolation target is not met
as it stands. #438/FORK-1 is NOT part of this NO-GO: per lead-63's DELTA (signal `#8032`) it is a
design-§10.8-RULED, tracked **63a-iv follow-on** (audit-DDL wiring lands next); I confirm I saw the DELTA
and do not hold the verdict on it. Residuals RES-A1 / RES-2-DDL / RES-ATOM / RES-B / RES-1 are surfaced,
not narrowed; F-A (and, as a separate tracked item, the 63a-iv audit-DDL wiring) are what the next fix
wave carries.
