# REPORT-builder-62w1 — packet 62 Wave 1 BUILD (`agent.owner_principal` owns-edge store foundation)

- `brief-base v14 read`
- `brief project v7 read`
- store reference read: `docs/reference/surrealdb-31-capabilities.md` — §1.1 (FIELD
  `OVERWRITE` / INDEX `IF NOT EXISTS` never `OVERWRITE` — an OVERWRITE index on boot is a
  crash), §1.4 (a NEW field on a POPULATED table MUST be `option<>`), §1.5 (the OVERWRITE-index
  boot-crash is HNSW-dim-specific, NOT plain scalar — R1), §1.6 (dirty-store blind spot), §2
  (`record<t>` links do NOT auto-clean → the tolerated dangle), §4 (traversal not index-served →
  scalar owner stays an INDEXED FIELD). Cited, never re-transcribed.

## CAPABILITY CHECK (tool honesty §4)
Everything the brief demanded was reachable: spike-surreal test store `ws://127.0.0.1:18000`
was OPEN (systemd unit `active`); `scripts/scratch_copy.sh` ran and asserted provenance; lore
tools loaded via `ToolSearch "+lore"`; pytest/ruff/typecheck ran. No impossibilities.

---

## SUMMARY BLOCK
- **State:** done-with-deviations. Contract GREEN (50/0), all three load-bearing mutation
  proofs confirmed, no regression across the touched suites.
- **Deviation 1 (docstring precision, item 4 / #423):** the brief's shorthand grouped the
  four `record<principal>` links as "TWO cascade (principal_key, keep), TWO dangle". I wrote
  the docstring with the ACCURATE dispositions instead — `keep.keeper` is REFUSE-WHILE-KEEPING,
  not cascade (the existing prose already drew that distinction, and the code refuses, it does
  not cascade keeps). Enumerated: `principal_key.principal` = children-first CASCADE;
  `keep.keeper` = REFUSE-WHILE-KEEPING; `audit.actor_principal` + `agent.owner_principal` =
  DANGLE-TOLERATED. Also kept the forward-reference to 63/64's *governed-row* `owner_principal`
  as a DIFFERENT future link (cascade-or-refuse), per the contract author's note #3.
- **Deviation 2 (in-scope consistency fix):** updated the `_agent_statements` docstring (it
  enumerated "the `(session, status)` and `name` indexes" — stale once I added the third). This
  is the CLAUDE.md rename/reshape law (keep NL surfaces consistent with code); `surreal_schema.py`
  is in my writable set.
- **Out-of-scope pre-existing gate breakage (FLAGGED, NOT fixed — filed #424):** `uv run ruff
  check .` is RED at HEAD `87d11d6` with 4× F841 in `scripts/probe_dnd_multitag_schema.py`
  (lines 434/439/445/450), introduced by commit `c6d2cd0`. My 3 changed files are ruff-clean.
  Filed as finding #424; lead/owner to adjudicate. Did not touch it (outside writable set).
- **Packages considered:** none — no mechanism specified. The field/index route through the
  EXISTING in-house `_define_field` / `_plain_index` emitters (no new dependency, no hand-roll),
  proven by the contract's `…routes_through_the_shared_emitter` mutation pin (GREEN).
- **Reuse ledger:** 1 new module symbol (`_AGENT_OWNER_PRINCIPAL_INDEX_FIELDS`), dispositioned
  below; no new reusable helper/policy.
- **Graded:** n/a — builder deliverable, no verdict rendered on another agent's artifact. Built
  at HEAD `87d11d6` (`git rev-parse HEAD` = `87d11d6` at report time; the working tree carries
  only my 3-file diff).
- **Decisions-needed:** none open. Deviations 1 & 2 are corrections resolved within scope;
  #424 is a flag for the lead.
- **Receipt pointers:** production diff §"What changed"; RED→GREEN + gate counts §"Gates";
  mutation proofs + `loremaster.__file__` receipt §"Mutation proofs"; emitted DDL §"Gates".

---

## What changed (writable set only)

**`loremaster/loremaster/store/surreal_schema.py`** (production — item 1):
- `_AGENT_FIELD_SPECS`: appended `("owner_principal", "option<record<principal>>", "")` after
  `declared_cadence`, with the §1.4 / Fork 3 / R3.4 rationale comment (mirroring the existing
  `status_set_at` #304 and `declared_cadence` W1a precedents — same `option<>`-on-populated-table
  shape). Routes through `_define_field` ⇒ `DEFINE FIELD OVERWRITE` (§1.1).
- Added module constant `_AGENT_OWNER_PRINCIPAL_INDEX_FIELDS = ("owner_principal",)` next to the
  two existing index-field constants (file idiom: each index's fields get a named constant).
- `_agent_statements()`: appended the non-unique plain index via
  `_plain_index(AGENT_TABLE, f"{AGENT_TABLE}_owner_principal", _AGENT_OWNER_PRINCIPAL_INDEX_FIELDS)`
  ⇒ `DEFINE INDEX IF NOT EXISTS agent_owner_principal ON agent FIELDS owner_principal` (§1.1 — never
  OVERWRITE an index). Updated its docstring to enumerate the third index (Deviation 2).

**`loremaster/loremaster/principals.py`** (item 4 — DOCSTRING ONLY, delete logic UNCHANGED):
- `PrincipalStore.delete` CASCADE FORWARD-SCOPE paragraph: corrected the "TWO links" undercount
  (#423, stale since 61a-w4) to enumerate all FOUR with accurate dispositions (Deviation 1). No
  code change — DANGLE = do nothing to `agent`, so the delete's acts-on set stays
  `principal_key` (cascade) + `keep` (refuse); `audit` + `agent` dangle.

**`loremaster/tests/test_agent_owns_principal_schema.py`** (R1 — DOCSTRING ONLY, brief-authorized):
- `test_the_agent_slice_is_safely_re_appliable`: corrected the docstring's FALSE over-claim
  ("REDDENS a build whose owner_principal INDEX is OVERWRITE"). Empirically a plain scalar
  OVERWRITE index re-applies cleanly (the boot-crash is HNSW-dim-specific, §1.5) — so this live
  control cannot see it; the OFFLINE `…index_is_IF_NOT_EXISTS_never_OVERWRITE` pin is the guard.
  The assertion body (`for _ in range(2): await _apply_agent_ddl(connection)`) is UNTOUCHED
  (git diff confirms docstring-only).

---

## Gates (passed-COUNTs, run at HEAD `87d11d6`, spike-surreal `ws://127.0.0.1:18000`)

- **Contract (RED→GREEN):** `pytest tests/test_agent_owns_principal_schema.py
  tests/test_principal_keys_schema.py -p no:randomly -q` → **`50 passed in 5.73s`** (byte-matching
  the adversary's reference build; the author's 14-failed/36-passed RED at base flips to 50/0 —
  all 14 declared-RED pins GREEN, all 6 controls held).
- **Plausibly-touched suites** (`-n auto`): `test_agent_registry.py`, `test_comms_schema.py`,
  `test_schema_fold_coverage.py`, `test_surreal_schema.py`, `test_principal_delete_cascade_61.py`,
  `test_audit_schema.py`, `test_keeps_schema.py`, `test_principals_schema.py` →
  **`660 passed in 23.32s`**. No regression (the field-add is invisible to `AgentRegistry`'s
  `extra="forbid"` `Agent` model — `SELECT *` omits the NONE `option<>` column, §2; schema-fold
  slice-fn count unchanged — `owner_principal` is a field within `_agent_statements`, not a new
  slice fn).
- **`bash scripts/typecheck.sh`** → all members OK (`typecheck: loremaster OK`, 236 source files;
  all 7 workspace/skill/scripts legs OK; shellcheck OK).
- **`uv run ruff check .`** → my 3 changed files: **`All checks passed!`**. Repo-wide: 4 F841
  errors, ALL pre-existing in `scripts/probe_dnd_multitag_schema.py` (untouched, not in my
  `git status -M` set) — see the out-of-scope flag above + finding #424.
- **Emitted DDL receipt** (`generate_agent_ddl()`, live introspection):
  ```
  DEFINE FIELD OVERWRITE owner_principal ON agent TYPE option<record<principal>>
  DEFINE INDEX IF NOT EXISTS agent_owner_principal ON agent FIELDS owner_principal
  ```

---

## Mutation proofs (load-bearing pins, per the riders + CLAUDE.md #140)

All run in the **provenance-asserted** scratch copy `/tmp/b62w1` (`scratch_copy.sh --all-packages`).
**Tree-identity receipt:** `loremaster.__file__ = /tmp/b62w1/loremaster/loremaster/__init__.py`
(I mutated/tested the SCRATCH build, not the original tree). Each mutation applied from a `.bak`,
run, then restored; final scratch re-run = **50 passed** (restoration clean, no residual `.bak`).

| # | mutation | pin(s) that redded | signature |
|---|---|---|---|
| 1 | field `option<record<principal>>` → `record<principal>` (required) | `…does_not_write_poison_the_legacy_row` (§1.4 control), `…is_option_wrapped_record_principal`, `…ownerless_reads_owner_principal_as_none` → **3 failed** | live `Couldn't coerce … Expected record<principal> but found NONE` on `agent:free` (the exact #107/#131 shape) |
| 2 | owner index `_plain_index` → hand-written `DEFINE INDEX OVERWRITE …` | `…index_is_IF_NOT_EXISTS_never_OVERWRITE` → **1 failed**; live `…safely_re_appliable` **stayed GREEN** | `assert 'IF NOT EXISTS' in 'DEFINE INDEX OVERWRITE AGENT_OWNER_PRINCIPAL …'`. The green live control empirically **corroborates R1** (a plain-scalar OVERWRITE index does not crash on re-apply, §1.5 — only the offline pin catches it) |
| 3 | delete injects `DELETE agent WHERE owner_principal=…` into the txn (cascade) | both `TestPrincipalDeleteDanglesTheOwnedAgentBackLink` pins → **2 failed** | `both agents … must DANGLE …, got 0` — agent rows cascade-deleted |

---

## Reuse ledger (brief-base §6)

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_AGENT_OWNER_PRINCIPAL_INDEX_FIELDS` (module constant, surreal_schema.py) | read the adjacent `_AGENT_SESSION_STATUS_INDEX_FIELDS` / `_AGENT_NAME_INDEX_FIELDS` constants + `lore_get_symbol _agent_statements` | the file's OWN established idiom: every `agent` index's field tuple is a named module constant referenced once in `_agent_statements` | **HAND-ROLLED** to match the immediate file idiom (a single-field index-fields constant, exactly like `_AGENT_NAME_INDEX_FIELDS = ("name",)`). Not a shared policy — a per-table index-fields tuple. |

No new helper / retry / classifier / validator / sanitiser / policy. The field + index reuse
the existing `_define_field` / `_plain_index` emitters (the ONE-implementation seam; sharing
proven by the contract's `…routes_through_the_shared_emitter` mutation pin, GREEN on the build).

---

## Notes for the cold audit + lead

1. **Item 4 needs NO delete code change** — DANGLE = the delete does nothing to `agent` (its
   acts-on set stays `principal_key` cascade + `keep` refuse). The only item-4 change is the
   #423 docstring. Confirmed live by mutation 3: injecting a cascade is what reddens the dangle
   pins; the shipped (unchanged) delete keeps them GREEN.
2. **Deviation 1 (docstring dispositions) is a precision refinement of the brief's shorthand,
   not a semantic disagreement.** The pinned behaviour (dangle-tolerated for agent + audit) is
   exactly as ruled; I only wrote `keep.keeper` as refuse-while-keeping (its true disposition)
   rather than folding it under "cascade". If the lead wants the brief's literal 2/2 grouping,
   it's a one-line docstring tweak.
3. **Finding #424 (ruff red at HEAD)** is a genuine repo gate breakage outside this packet.
   Flagged, not fixed — awaiting lead/owner adjudication.

There are 4 failing ruff checks unrelated to our present scope (all in
`scripts/probe_dnd_multitag_schema.py`, finding #424). Do you want to examine them more closely?
