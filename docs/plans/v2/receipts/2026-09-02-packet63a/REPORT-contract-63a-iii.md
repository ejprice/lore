# REPORT-contract-63a-iii — CONTRACT (runnable-RED) for the 63a cold-audit NO-GO fix

- `brief-base v14 read`
- `brief project v7 read`
- store reference consulted: `docs/reference/surrealdb-31-capabilities.md` — §2 (record<> links;
  CONTENT; explicit projection reads a NONE option<> column back as None), §3
  (execute_read_transaction / BEGIN…COMMIT atomicity). Cited, never re-transcribed.

## SUMMARY BLOCK

- receipt: `brief-base v14 read` · `brief project v7 read`
- **state: done.** Four items delivered as runnable-RED / regression-gate pins; the C-DEF
  satisfiability receipt is GREEN (a reference fix built in a provenance-asserted scratch copy takes
  all four modules 52/52 with `build_memory_backend` UNCHANGED).
- deviations: **RES-3 (item 3) and the wire-isolation gate (item 4) are GREEN-at-HEAD REGRESSION
  GATES, not RED-until-built.** The brief's verify line grouped RES-3 with the RED legs, but the
  cold-audit itself rules `_table_exists` "correct now, unpinned" (§RES RES-3) and the sec-auditor
  verdict is GO for read isolation — so those two pins guard a future refactor, they do not pin an
  unbuilt fix. Measured: both GREEN at HEAD. Detail → §DEVIATIONS.
- **Packages considered:** none — no mechanism specified (contract/tests only; the one new production
  symbol is a stub exception class, no library involved).
- **Reuse ledger:** 1 new production symbol (`governed.GovernedAuditUnavailable`) + 1 new test helper
  (`_build_audit_store`), all dispositioned → §REUSE.
- **Graded:** authored against `dd5c9b2` · HEAD-at-report: `dd5c9b2` · SAME.
- decisions-needed: two FLAGS for the builder/lead (not blocking this contract) → §FORKS: (1) a denied
  supersede-close leaves an ORPHAN new row (atomicity removed-behavior); (2) a `/tmp` scratch dir I
  could not `rm` (sandbox-blocked) needs cleanup.
- receipt POINTERS: item→pin map → §ITEMS; RED/GREEN + satisfiability → §GATES; mutation-proof plan →
  §MUTATION; deviations → §DEVIATIONS; flags → §FORKS.

---

## §ITEMS — each brief item → its pin(s)

**Item 1 — THE F1 PIN (MISSING PIN 2's supersede leg; QUANTIFIER-LAW fix).**
`test_memory_retrofit_63a.py::TestInvalidateRoutesThroughGuardedWrite` — EXTENDED (completing the
under-quantified pin the cold-audit §F1 named; the class is titled "invalidate/**supersede** write
path is GOVERNED" but tested only invalidate). Two new methods:
- `test_a_member_cannot_supersede_close_a_foreign_owned_row` — **RED at `dd5c9b2`**: bob
  `remember(supersedes=<alice's id>)` must raise `GovernedDenied` AND leave alice's row UNCHANGED
  (`valid_until` None, `superseded_by` unset). At HEAD the bare `_close_superseded_fragment` UPDATE
  retires alice's note (the exact live cold-audit §F1 defect). Confirmed RED-for-the-right-reason:
  `Failed: DID NOT RAISE GovernedDenied`.
- `test_an_owner_can_supersede_close_its_own_row` — POSITIVE CONTROL / discriminator (GREEN both
  worlds): alice supersedes her OWN note → `valid_until` set, `superseded_by` → the new note.
  Grounding: design §2.5 (`docs/design/2026-08-28-packet63-retrofit-rulings.md:325`) — "both route
  through guarded_write/the stamp."

**Item 2 — RES-2 (the unaudited-bypass fail-open).** TWO legs, both RED at `dd5c9b2`:
- SUBSTRATE: `test_governed_substrate_63a.py::TestGuardedWriteRefusesAnUnauditedBypass` —
  `test_an_admin_bypass_with_no_audit_store_refuses_and_does_not_mutate` (guarded_write must raise
  the new typed `governed.GovernedAuditUnavailable` when `requires_audit=True and audit is None`,
  BEFORE mutating) + `test_a_non_bypass_write_with_no_audit_store_still_succeeds` (discriminator —
  requires_audit=False path still succeeds, so the refusal is bypass-specific not a blanket
  audit=None refusal). Confirmed RED-for-the-right-reason: `Failed: DID NOT RAISE
  GovernedAuditUnavailable`.
- MEMORY: `test_memory_retrofit_63a.py::TestMemoryBypassCloseIsAudited` — an admin BYPASS close
  appends exactly +1 `audit` row, via BOTH close verbs (`..._invalidate_...` and
  `..._supersede_close_...`), plus `test_a_member_self_close_appends_no_audit_row` (discriminator:
  a non-bypass self-close appends 0). RED at HEAD (`assert 0 == 0 + 1` — invalidate passes
  audit=None; supersede is an ungoverned bare UPDATE). Grounding: §9 / design §10.6 rider ii
  (`...:843` — "a mutation without its audit row is exactly the §9 'compromised admin erases its
  trail' shape").

**Item 3 — RES-3 (SF-63-5 fault-propagation).** `test_principal_delete_governed_63a.py::
TestTableExistsProbeFaultPropagates` — a REGRESSION GATE, **GREEN at `dd5c9b2`** (see §DEVIATIONS):
- `test_a_probe_fault_propagates_and_the_owner_is_untouched` — a synthetic fault injected at the
  `INFO FOR DB` probe ONLY (every other `_query` passes through) propagates out of `delete`; the
  owner + its owned memory row survive.
- `test_a_genuinely_absent_memory_table_lets_the_delete_proceed` — POSITIVE CONTROL: an absent
  memory table reads `False` (a genuine absence, not a fault) → delete PROCEEDS. (The "present +
  owned row → refuse fires" third control is the existing `TestDeleteRefusesWhileOwningGovernedRows`.)

**Item 4 — WIRE-ISOLATION GATE.** NEW `test_wire_isolation_63a.py` — a committed adaptation of
secaudit-63a's per-call-token wire instruments (`REPORT-secaudit-63a.md` §APPENDIX). A REGRESSION
GATE, **GREEN at `dd5c9b2`** (read isolation already holds; the sec-auditor's GO). Boots a real
`AppContext`, patches `loremaster.server.get_access_token` to a SWITCHABLE token (≥2 principals × ≥2
agents), and pins cross-principal READ isolation + admin AllRows positive control + the confused-
deputy binding — the surface the shipped `governed_ctx` (one static email) structurally cannot test.

---

## §GATES — RED/GREEN receipts

**At HEAD `dd5c9b2` (the real tree, the 4 affected modules — the deliverable state):**

| module | result | new RED (right reason) |
|---|---|---|
| `test_governed_substrate_63a.py` + `test_memory_retrofit_63a.py` + `test_principal_delete_governed_63a.py` | **4 failed, 45 passed** in 11.48s | RES-2-substrate (DID NOT RAISE GovernedAuditUnavailable) · F1-supersede-deny (DID NOT RAISE GovernedDenied) · RES-2-memory-invalidate (`0 == 0+1`) · RES-2-memory-supersede (`0 == 0+1`) |
| `test_wire_isolation_63a.py` + RES-3 (`TestTableExistsProbeFaultPropagates`) | **5 passed** in 10.41s | none — GREEN regression gates (item 3 + item 4) |

The two `DID NOT RAISE` receipts (RES-2-substrate + F1-supersede) were re-derived in isolation to
confirm the RED is the pin failing to fire, not a collateral error.

**SATISFIABILITY RECEIPT (C-DEF law — 0-failed against a known-correct build).** A reference fix
built in a provenance-asserted scratch copy (`scripts/scratch_copy.sh /tmp/contract63aiii-ref`,
`loremaster.__file__ = /tmp/contract63aiii-ref/loremaster/loremaster/__init__.py`):
- all four modules → **52 passed, 0 failed** (every RED pin → GREEN; every existing pin held);
- the broader memory suites (`test_memory_backend.py` + `test_memory_cutover.py`) → **136 passed**
  against the same reference — the supersede-close re-route does not break existing supersede/recall
  behaviour at the test level.
- **The reference fix needed NO change to `build_memory_backend`** (the backend self-builds its
  `AuditStore` from its own `_url/_namespace/_database/_user/_password`, mirroring the `handle`
  accessor idiom) — so the RES-2-memory pin is NOT a C-DEF trap requiring an out-of-writable-set edit.
- **The satisfiability build CAUGHT A BUILDER LANDMINE:** `memory.superseded_by` is `option<string>`
  (`surreal_schema.py:279`), NOT a record link — a first reference attempt setting it via
  `type::record('memory', <id>)` was REJECTED (`field coercion`, statement 2 of 4 rolled back). The
  builder must set `superseded_by = '<memory_id>'` (a string literal / the old param value), not a
  RecordID, when routing the supersede-close through `guarded_write` (whose `set_fragment` takes no
  extra params). Named here so the builder does not rediscover it.

**Real-tree gates:** `uv run ruff check .` → **All checks passed!** (two import-order nits in the new
files auto-fixed). `bash scripts/typecheck.sh` → **every member OK** (incl. test trees + shellcheck).
The 60/61/62 + governed/principal-consumer regression is running at report-write time — result in
§DEVIATIONS once it lands.

---

## §MUTATION — the mutation-proof plan per new pin

The four RED pins are **already mutation-proven at HEAD**: HEAD *is* the wrong build (the F1 bypass
and the RES-2 fail-open are present), and each pin is RED there for the named reason; the
satisfiability build proves each flips GREEN on the fix. The mutation for each GREEN regression gate:

| pin | mutation that must RED it | proven |
|---|---|---|
| F1 supersede-deny | (HEAD) bare `_close_superseded_fragment` UPDATE — bob retires alice's note | RED at HEAD ✓; GREEN on ref fix ✓ |
| RES-2 substrate refuse | (HEAD) `if requires_audit and audit is not None` silent-skip; restore it on the fixed build → the refuse pin reds again | RED at HEAD ✓; GREEN on ref fix ✓ |
| RES-2 memory audit (×2) | (HEAD) `invalidate` passes `audit=None` / supersede is ungoverned → 0 audit rows | RED at HEAD ✓; GREEN on ref fix ✓ |
| RES-3 fault-propagation | wrap `_table_exists`'s `INFO FOR DB` in `except Exception: return False` → the owner is silently deleted → the pin reds (the planned mutation; the fault-injection IS the instrument) | GREEN at HEAD ✓ (mutation is the documented re-open) |
| wire-isolation | mutate `governed.read_filter` to return `("true", {})` (AllRows) → every member sees all → the isolation pin reds | GREEN at HEAD ✓ (mutation available; not run — regression gate) |

The two GREEN-gate mutations (RES-3 `except: return False`; wire `read_filter`→AllRows) are the
documented re-open triggers, not run on the real tree to avoid mutating shipped production files; the
RES-2/F1 mutations WERE run (they are HEAD itself, and the scratch reference fix is the inverse).

---

## §DEVIATIONS

**RES-3 (item 3) and the wire-isolation gate (item 4) are GREEN at HEAD, not RED-until-built.** The
brief's VERIFY line reads "the F1 + RES-2 + RES-3 legs RED-until-built, the wire-isolation gate
GREEN" — but the brief's own item-3 spec ("Closes the class: a future `except: return False`
refactor would re-open …") and the cold-audit §RES RES-3 ("Correct now, unpinned") both describe a
REGRESSION GATE, not an unbuilt fix. `_table_exists` at `dd5c9b2` already propagates (no local
try/except, `principals.py:451`), so the fault-propagation pin is GREEN at HEAD; measured GREEN.
This is a reconciliation of the brief's summary line with its detailed spec + the cold audit, not a
scope change — the pin is exactly what item 3 asks for. Stated so the lead's RED/GREEN expectation is
correct: **the RED-until-built set is F1 + RES-2 (both legs) = 4 pins; RES-3 + item-4 are GREEN
regression gates.**

**Regression result (measured `dd5c9b2`):** the 63a set + the 60/61/62 sweep + the governed/principal
consumers (`test_search`, `test_principals_{cli,store,schema}`, `test_principal_keys_{schema,store}`,
`test_principal_delete_cascade_61`, `test_agent_owns_principal_schema`, `test_audit_{schema,store}`,
`test_keeps_schema`, `test_pdp_oracle_61b`, `test_visible_keeps_61b`, the other `test_*_63a`) →
**4 failed, 579 passed** in 20.19s. The 4 failed are EXACTLY the four intended RED pins (F1 supersede-
deny, RES-2 substrate, RES-2 memory invalidate + supersede); every other suite is GREEN, so the
additive `GovernedAuditUnavailable` stub + the new tests regressed NOTHING. No failing tests outside
the intended contract REDs.

---

## §REUSE — DRY ledger

| new symbol | lore/grep query run | what it returned | disposition |
|---|---|---|---|
| `governed.GovernedAuditUnavailable` (production exception) | `grep -rnE "GovernedAudit\|audit is None\|requires_audit and audit" loremaster/` | only the `guarded_write` silent-skip line; no existing audit-unavailable error; siblings `GovernedDenied`/`GovernedConflict` are semantically distinct (a denial / a vanished row, NOT a missing sink) | HAND-ROLLED (a new typed error the RES-2 pin references; a distinct type is required to discriminate the fail-open from a per-caller denial). Stub added to `governed.py`; the `raise` is the builder's. |
| `_build_audit_store` (test helper, `test_memory_retrofit_63a.py`) | read `test_governed_substrate_63a.py` (has an identical local `_build_audit_store`) | an existing per-module local copy; the shared home would be `_governed_contract.py` — OUT of this contract's writable set | HAND-ROLLED / mirrored the existing test-local idiom (a fixture constructor, not policy — §6 trivia, not a clone-of-policy). **Flag:** a future consolidation into `_governed_contract` would DRY the two copies (cheap follow-up, needs that file in scope). |

Test-local trivia NOT ledgered (each is an established per-module idiom, duplicated across the test
tree by convention): `_bare`, `_count`, `_boot_config`, `_wire_recall` in `test_wire_isolation_63a.py`.

---

## §FORKS — flags for the builder / lead (none block this contract)

1. **ATOMICITY removed-behavior (builder decision).** The original `remember(supersedes=)` composed
   the new-row UPSERT and the old-row close into ONE transaction (`_apply([upsert, close])`) — "a
   concurrent reader never observes a half-applied supersession" (`local.py::_apply` docstring). My
   reference fix routes the close through `guarded_write` (its OWN transaction), so on a DENIED close
   (a member superseding a foreign row) the NEW row is already created while the old row is not
   retired — an ORPHAN new note. My F1 pin deliberately does NOT assert new-row rollback (it pins the
   security property — the foreign row is untouched — agnostic to the builder's transaction shape).
   **The builder should consciously choose:** accept the orphan-on-denied-close, OR preserve one-txn
   atomicity (compose the guarded close WITH the upsert). Invisible to the existing suite (all
   supersede tests route through the admin subject on virgin DBs — the #131 fixture-hides-the-bug
   shape), so it will not red on its own. Recommend the lead hand this to the builder explicitly.
2. **Scratch-dir cleanup.** `/tmp/contract63aiii-ref` (the satisfiability scratch copy) could not be
   removed — `rm -rf /tmp/contract63aiii-ref` was sandbox-DENIED three times this session. It is a
   disposable, provenance-asserted copy (NOT a git worktree), safe to `rm -rf`. Please clear it.
3. **`build_memory_backend` coupling — RESOLVED, no action.** The RES-2-memory pin was authored to be
   satisfiable WITHOUT editing the shared `_governed_contract.build_memory_backend` (out of writable
   set): the backend self-builds its `AuditStore` from its own connection params. Proven (52/52).
   Named so the builder does not reach for a new constructor arg.

## §GATE-DETAIL — the four written test files (real tree, `dd5c9b2`)

- `test_governed_substrate_63a.py` — +`GovernedAuditUnavailable` stub in `governed.py`;
  +`TestGuardedWriteRefusesAnUnauditedBypass` (1 RED refuse + 1 GREEN discriminator).
- `test_memory_retrofit_63a.py` — +2 methods on `TestInvalidateRoutesThroughGuardedWrite` (1 RED F1
  deny + 1 GREEN owner control); +`TestMemoryBypassCloseIsAudited` (2 RED audit legs + 1 GREEN
  self-close discriminator); +`_build_audit_store` helper.
- `test_principal_delete_governed_63a.py` — +`TestTableExistsProbeFaultPropagates` (2 GREEN gates:
  fault-propagation + absent-table control); +`from typing import Any`.
- `test_wire_isolation_63a.py` — NEW module (3 GREEN gates: member isolation ∀ · admin control +
  count · binding/identity-less deny).
