# REPORT-fixer-60-prose

brief-base v14 read
brief project v7 read

## SUMMARY
- **State:** done — 7 stale RED-STUB-era comment sites reframed to match greened code; 1 additional same-class site FLAGGED (not fixed) per brief.
- Deviations: none to the 7-site fix. See decisions-needed for the 8th site.
- Packages considered: none — no mechanism specified (docs/comment-only edits).
- Reuse ledger: none — no new symbols.
- **Graded:** N/A — this is a fix report, not a verdict on another artifact. Base sha at edit: `b9e6335`.
- Decisions-needed:
  - **8th stale site** `loremaster/tests/_enforced_relations_scaffold.py:92-95` — same defect class (pkt60 RED-STUB prose now false), but in a file OUTSIDE the sidecar's enumerated stale-site set (keeps.py + surreal_schema.py). Per brief "do NOT silently fix beyond this set; flag it for the lead" → flagged with exact edit below, NOT fixed. **Recommend the lead apply the one-line edit and let it ride the wave-1 pkt60 commit**, else it ships stale.
  - keeps.py:351 (`_resolve_principal_id` docstring) was NOT in the brief's explicit 4-item pkt60 list, but IS the "5th pkt60" the brief's count anticipated ("5 pkt60 + 2 pkt49 = 7") and lives in an enumerated file → fixed in-set.
- Receipt pointers: ruff/typecheck/pytest tails in §Verify; per-site before→after in §Sites.

## GROUND-TRUTH (what makes each comment stale)
Confirmed live, all fully implemented + folded (via `lore_get_symbol` on disk-current index, corroborated by direct Read):
- keeps.py CRUD verbs `create_keep` / `get_keep` / `add_household_member` / `remove_household_member` / `set_rank` / `list_household` / `list_keeps_for_keeper` (keeps.py ~444-640) — NONE raise `NotImplementedError`.
- `generate_keep_ddl` (surreal_schema.py ~2102) returns `_keep_statements() + _member_of_statements()` — real DDL, not `""`.
- `_keep_statements` (~2031) emits table+fields+index; `_member_of_statements` (~2062) emits RELATION table+fields+UNIQUE index — neither returns `[]`.
- `_principal_key_statements` (~1893) emits table+fields+2 UNIQUE indexes and IS folded into `generate_ddl` (surreal_schema.py line 1722).
- keep + member_of slices folded into `generate_ddl` (lines 1727-1728).

## SITES — before → after

### PACKET 60 (5 sites — fixed; ride wave-1 pkt60 commit)

**S1. `keeps.py` module docstring (~lines 3-12)** — `⚠⚠ RED STUB … every CRUD verb raises NotImplementedError … Do NOT implement the CRUD here`.
- Ground truth: all 7 CRUD verbs implemented.
- After: historical-origin reframe — "Introduced as the STUB half … and GREENED by the wave-1 builder. Every CRUD verb below is now fully implemented … the `test_keeps_store.py` pins are GREEN." Design-model prose below (unchanged) preserved.

**S2. `keeps.py` `KeepStore.ensure_ready` docstring (~278-279)** — `⚠⚠ STUB NOTE: generate_keep_ddl currently emits "" … creates NO table — the RED-by-design state`.
- Ground truth: `generate_keep_ddl` emits real DDL.
- After: false STUB-NOTE addendum removed; the surrounding docstring already accurately describes applying `generate_keep_ddl` (table + indexes) in one BEGIN…COMMIT — left intact.

**S3. `surreal_schema.py` `generate_ddl` fold comment (~line 1726)** — trailing `⚠ Stub emits nothing today.`
- Ground truth: `_keep_statements()` + `_member_of_statements()` folded and emit real statements.
- After: stale sentence stripped; the accurate fold-order rationale (keep AFTER principal, member_of AFTER both) preserved.

**S4. `surreal_schema.py` keep-slice header block (~1959-1975)** — `⚠⚠ RED STUBS … emit [] and generate_keep_ddl emits "" … the stub emits no keep table/fields/index … folds nothing into generate_ddl … Do NOT "fix" the emptiness here — it is the contract`.
- Ground truth: all three implemented + folded.
- After: historical-origin reframe — "Introduced as RED STUBS … and GREENED by the wave-1 builder per the design sidecar … The two assemblers + generate_keep_ddl now emit the real slice, folded into generate_ddl." Still-accurate CONSTANTS/FIELD-SPECS/mutation-pin prose preserved (reworded to present tense); keep/member_of design paragraph above (unchanged) preserved.

**S5. `keeps.py` `_resolve_principal_id` docstring (~line 351)** — `Available to the builder's CRUD; not exercised by the stub.` *(the un-listed 5th pkt60 site; found by reading)*
- Ground truth: called by `create_keep`, `add_household_member`, `remove_household_member`, `set_rank`, `list_keeps_for_keeper`.
- After: "Called by the create/mutation/list verbs to resolve keeper/member emails to principal ids." (accurate present tense; the shared-resolver rationale above preserved).

### PACKET 49 (2 sites — fixed; separate `docs(49)` commit citing #398)

**S6. `surreal_schema.py` `PRINCIPAL_KEY_TABLE` constant note (~133-136)** — `⚠⚠ STUB (contract-49-1) — a NAME only. The field specs / emitters below are RED stubs; the builder greens them.`
- Ground truth: `_PRINCIPAL_KEY_FIELD_SPECS` + `_principal_key_statements` built + folded.
- After: naming rationale kept (accurate); RED-stub claim retired → "The field specs / emitters below (introduced as RED stubs by contract-49-1 …) are now fully built and folded into generate_ddl."

**S7. `surreal_schema.py` principal_key slice header block (~1855-1867)** — `⚠⚠ RED STUBS (contract-49-1) … These emit NOTHING … The DELIBERATE gaps the RED pins encode: the stub emits no fields/indexes and is NOT folded into generate_ddl. Do NOT "fix" them here — they are the contract`.
- Ground truth: `_principal_key_statements` (fields + 2 UNIQUE indexes) built + folded after `_principal_statements()` (line 1722).
- After: historical-origin reframe — "Introduced as RED STUBS by contract-49-1 … and GREENED by the wave builder per the packet-49 design §F7. The slice now built:" then the same accurate §F7 bullet list (field specs, fold position, `generate_principal_key_ddl`), which describes the built state.

## FLAGGED — NOT FIXED (8th site, out of enumerated file-set)

**`loremaster/tests/_enforced_relations_scaffold.py:92-95`** (packet-60 class):
```
    # packet 60 — the Keep substrate slice (``keep`` + the ``member_of`` edge). Added
    # here so the ∀ ENFORCED / OVERWRITE / IN-OUT pins sweep ``member_of`` the moment
    # the builder emits it. ⚠ RED-by-design until then: ``generate_keep_ddl`` STUBS to
    # ``""`` (contract-60-w1), so it emits no relation table yet.
```
Ground truth: `generate_keep_ddl` now emits the real `member_of` RELATION table — the "STUBS to `""` … emits no relation table yet" claim is FALSE.
Reason not fixed: this file is not among the sidecar's enumerated stale-site files (keeps.py + surreal_schema.py); the brief's rule for an additional same-class site is "list it … do NOT silently fix beyond this set; flag it for the lead."
**Exact proposed edit** (replace lines 92-95):
```
    # packet 60 — the Keep substrate slice (``keep`` + the ``member_of`` edge). Added
    # here so the ∀ ENFORCED / OVERWRITE / IN-OUT pins sweep ``member_of``.
    # ``generate_keep_ddl`` emits the real slice (contract-60-w1, greened wave-1),
    # including the ``member_of`` RELATION table.
```
(pkt60-class — should ride the wave-1 pkt60 prose commit if the lead approves.)

## NOT STALE (checked, left alone)
- `surreal_schema.py:2220` ("NAMES … FROZEN by the contract author") and `:2258` ("anchor-free pattern … makes that pin RED") — packet-11ia prose describing accurately-built state. Not stale, not in scope.

## VERIFY (receipts)
- **ruff** `keeps.py surreal_schema.py _enforced_relations_scaffold.py` → `All checks passed!` (exit 0).
- **typecheck.sh** → GREEN: `loremaster OK` (221 source files), all members OK, shellcheck OK (exit 0). Docs-only, stayed green as expected.
- **pytest -n auto** `test_keeps_schema.py test_keeps_store.py test_enforced_relations.py` → **154 passed in 7.45s** (collection intact; docs-only so unaffected — confirmed).
- **git status --short** — I touched exactly `keeps.py` (new, `??`) + `store/surreal_schema.py` (`M`), a subset of the writable set. `_enforced_relations_scaffold.py` remains `M` from wave-1 (I did NOT touch it — the flag-only decision above).

## COMMIT SPLIT (for the lead)
- **pkt60 prose (ride wave-1):** keeps.py S1/S2/S5 + surreal_schema.py S3/S4. Plus (if approved) the flagged scaffold edit.
- **pkt49 (`docs(49)` commit citing #398):** surreal_schema.py S6/S7.
- I did NOT commit (per brief).
