# REPORT-adversary-62w1 — CONTRACT-ADVERSARY grade, packet 62 Wave 1 (`agent.owner_principal` owns-edge store foundation)

- `brief-base v14 read`
- `brief project v7 read`
- store reference read: `docs/reference/surrealdb-31-capabilities.md` — §1.1 (FIELD `OVERWRITE` / INDEX `IF NOT EXISTS`), §1.4 (new field on a POPULATED table must be `option<>`), §1.6 (dirty-store blind spot), §1.5 (OVERWRITE-index rebuild is HNSW-specific), §2 (`record<t>` links do NOT auto-clean; protected `session` var; `SELECT *` omits NONE `option<>`), §4 (traversal not index-served). Cited, never re-transcribed.

## CAPABILITY CHECK (tool honesty §4)
Everything the brief demanded was reachable: `scripts/scratch_copy.sh` ran and asserted provenance; the spike-surreal test store `ws://127.0.0.1:18000` was OPEN; lore tools loaded via `ToolSearch "+lore"`; pytest ran in the scratch tree. **One friction, worked around:** bare `rm -rf /tmp/…` is sandbox-denied here — I used a fresh scratch path (`/tmp/adv62w1`) instead of pre-cleaning. No mission impact.

---

## SUMMARY BLOCK

- **VERDICT: CONTRACT SUFFICIENT.**
- **P1 headline — NO wrong build survives.** 10 wrong builds constructed in scratch + 1 receding-derivation perturbation; each is caught by ≥1 on-point pin, each reds for the RIGHT reason (differentiated failures, no spurious import/collection reds). Reference (correct) build = **50 passed, 0 failed** (satisfiability receipt, C-DEF clean).
- **Quantifier table (P1b):** every invariant is ∀-over-inputs or forced-fate — the DANGLE is ∀-over-3-fates (refuse/cascade/null each forced) AND ∀-owned-agents (N=2); non-unique is N=2; §1.4 poison is forced live. No unguarded-door survivor. Table in §P1b.
- **Reach table (P1c):** `_all_schema_ddl` reach is DERIVED (a NEW `generate_*_ddl` slice reds the exact-set pin — empirical), coverage is a CHECKED variable (a receding derivation reds BOTH the exact-set pin and the reach control — empirical), observes the EMITTED DDL (effect not proxy), and the field is one-implementation-proven by mutation. Table in §P1c.
- **MISSING PINS: none.** No pin I can name would catch a wrong build the contract currently waves through.
- **Fixture discrimination:** all load-bearing fixtures discriminate (N=2 many-agents + N=2 dangle; two-principal; required-vs-option; legacy-row-written-under-OLD-DDL). Details §P2.
- **RED honesty (P7):** the author's 14-failed/36-passed RED reproduced EXACTLY at the contract base; all 14 red BEHAVIOURALLY (not on collection). §P7.
- **Corpse sweep (P6):** clean — no test still asserts the OLD 2/3-link set or the retired `..._is_the_ONLY_record_principal_link` name. §P6.
- **Residuals (individual verdicts, none blocking):** (R1) `test_the_agent_slice_is_safely_re_appliable`'s docstring over-claims it reddens an OVERWRITE index — empirically it does NOT (an OVERWRITE *plain* scalar index does not crash on re-apply; only HNSW dim-changes do, §1.5); the OFFLINE pin catches OVERWRITE, so coverage is real, but the live control's docstring names a discrimination it lacks. (R2) the dangle pins assert observable outcome (survive + stale link), not "delete never touches agent" — a build that touches agent benignly would pass (not a plausible/spec-violating build). (R3) report prose says the new file has "16 tests"; it has 17 (the declared-RED node LIST of 13 is correct). (R4) reach bound: `_all_schema_ddl` covers `generate_*_ddl` surfaces only — currently vacuous (verified: no `record<principal>` DDL is applied outside a `generate_*_ddl`). All four are notes, not missing pins.
- **Packages considered:** none — no mechanism specified (the contract is TESTS only; the field routes through the existing in-house `_define_field`/`_plain_index` emitters, no library choice). I built my own package table before opening the author's; both are empty for the same reason. Nothing to diff.
- **Reuse ledger:** none — I introduced no reusable production symbol. My two instruments (`av.py` wrong-build harness, `regex_probe_62.py`) are adversary scratch tooling, pasted verbatim in §Instruments so they survive the disposable scratch tree (brief-base §1).
- **Graded:** the contract is now **committed at HEAD `87d11d6`** (`test(62): wave-1 contract (RED)`), byte-identical to the working-tree bytes I graded (working tree clean vs HEAD; same mtimes). HEAD advanced DURING my run: `9a9ca4a` → `de781b7` (docs: the "three existing / fourth" link-count correction) → `87d11d6` (this contract). The graded **production** code (`surreal_schema.py`, `principals.py`) is **byte-identical `29e15f2..87d11d6`** (verified `git diff --name-only` → none) — nothing I graded moved. **Graded == HEAD `87d11d6`, SAME.**
- **Decisions-needed:** none. Residual R1 (docstring correction) is the author's cheap fix; it does not gate the build.

---

## What this wave contracts (grading scope)

Packet-62 **FINAL SCOPE LINE items 1 & 4 ONLY** (the store foundation): item 1 = `agent.owner_principal : option<record<principal>>` field-link + its non-unique `IF NOT EXISTS` index, `DEFINE FIELD OVERWRITE`, dirty-store migration pinned (Fork 3 / R3.4); item 4 = `PrincipalStore.delete` accounts for the new link, DANGLE-TOLERATED (R3.2 / I4), the exact-set pin discharged. Items 2/3/5/6 (register-time stamp, `stamp_owner` seam, `agent_of`, the anti-injection DERIVED reach pin over the governed surface, the docstring/prose retirement of the 48 non-wiring guard) are **LATER waves and correctly NOT contracted here** — I confirmed the contract does not overreach into them. The brief's corrected count ("three existing links / FOURTH") is right: I ground-truthed the three existing `record<principal>` emit sites — `principal_key.principal` (`surreal_schema.py:1908`), `keep.keeper` (`:2037`), `audit.actor_principal` (`:2187`) — so `agent.owner_principal` is the 4th, and the contract's 4-entry `expected` set is correct.

---

## P1 — wrong builds vs the contract (highest-value probe)

All builds run in the **provenance-asserted** scratch copy `/tmp/adv62w1` (`scratch_copy.sh`, `--all-packages`). Receipt: `loremaster.__file__ = /tmp/adv62w1/loremaster/loremaster/__init__.py` (I am testing the scratch build, not the original tree). Each variant is applied from pristine `.orig` backups by `av.py` (§Instruments). Full-contract subset = both files, `-p no:randomly`.

**POSITIVE CONTROL (satisfiability receipt / C-DEF, P0):** the reference (correct) build — add `("owner_principal", "option<record<principal>>", "")` to `_AGENT_FIELD_SPECS`, add `_plain_index(AGENT_TABLE, f"{AGENT_TABLE}_owner_principal", ("owner_principal",))` to `_agent_statements`, NO delete change — takes the contract to **`50 passed in 6.44s`**. Every declared-RED pin flips green; every control stays green. So no declared-RED pin stays red on a correct build and no pre-existing pin is contradicted (C-DEF clean).

| # | wrong build | contract result | pin(s) that caught it (on-point) |
|---|---|---|---|
| — | **reference (correct)** | **50 passed / 0 failed** | — (positive control) |
| 1 | **required** — `record<principal>` (not `option<>`) | 3 failed / 47 | offline `…is_option_wrapped_record_principal`; **live `…does_not_write_poison_the_legacy_row`** (`Couldn't coerce … Expected record<principal> but found NONE` on `agent:legacy`); live `…ownerless_reads_owner_principal_as_none` (`agent:free`) |
| 2 | **field_ifnotexists** — hand-written `DEFINE FIELD IF NOT EXISTS … option<record<principal>>`, bypassing `_define_field` | 6 failed / 44 | `…is_emitted`, `…OVERWRITE`, `…is_option_wrapped…`, `…no_default_and_no_assert`, **`…routes_through_the_shared_emitter`** (mutation), **exact-set pin** |
| 3 | **unique_index** — `_unique_index` on `owner_principal` | 3 failed / 47 | offline `…index_is_NOT_unique`; live `…a_principal_may_own_many_agents` (2nd CREATE rejected, `index … already contains principal:pshared`); live dangle-MANY |
| 4 | **overwrite_index** — `DEFINE INDEX OVERWRITE …` | 1 failed / 49 | **OFFLINE `…index_is_IF_NOT_EXISTS_never_OVERWRITE` only** — the live `…safely_re_appliable` did NOT red (see residual R1) |
| 5 | **default_on_field** — `option<record<principal>> DEFAULT NONE` | 1 failed / 49 | offline `…no_default_and_no_assert` |
| 6 | **no_index** — field, no index | 3 failed / 47 | `…index_is_emitted` (+ its two guarded clause pins) |
| 7 | **delete_refuse** — raise if principal owns agents | 2 failed / 48 | both dangle pins — `RuntimeError: refuse: principal owns agents` |
| 8 | **delete_cascade** — `DELETE agent WHERE owner_principal=…` in the txn | 2 failed / 48 | both dangle pins — `AssertionError: the owned agent row was cascade-deleted … assert []` |
| 9 | **delete_null** — `UPDATE agent SET owner_principal=NONE …` in the txn | 2 failed / 48 | both dangle pins — `AssertionError: owner_principal was cleaned/nulled … assert 'None' == 'principal:…'` |
| 10 | **reach_bogus** — a NEW `generate_bogus_ddl()` emitting `sponsor ON bogus TYPE record<principal>` | 1 failed / 49 | **exact-set pin** (`found` grew to include `('sponsor','bogus')`) |

**Frontier answers (the lead's floor, all empirical):**
- **(a) Can a required build green the migration not-poison control?** **NO.** Variant 1 reds `…does_not_write_poison_the_legacy_row` live with the exact §1.4 signature (`Expected record<principal> but found NONE`), plus the ownerless-CREATE pin and the offline option-wrapped pin. A sneakier `required + DEFAULT` build is ALSO caught offline (`…no_default…` + `…option_wrapped…`) — §1.4: a DEFAULT does not rescue an existing row.
- **(b) Does the DANGLE test discriminate refuse / cascade / null?** **YES — all three, each with a distinct on-point failure** (variants 7/8/9 above). It is a genuine 3-way discriminator, not a one-fate guard.
- **(c) Is `_all_schema_ddl`'s reach a genuine derivation or a hand-list?** **Genuine derivation.** Variant 10 (a brand-new `generate_*_ddl` slice) reds the exact-set pin with NO edit to the guard — a new site joins the scanned set by the `generate_*_ddl` naming property. And the reach RECEDING is caught too (see §P1c empirical leg).
- **(d) The regex on hostile spellings.** Offline probe (§Instruments `regex_probe_62.py`): `record<principals>` → not matched (correct — different table); `record<agent>` → not matched (correct); `option<record<principal>>` and `array<record<principal>>` and whitespace-runs → matched (correct); the only would-be link the regex misses is `record< principal >` with spaces INSIDE the angle brackets — which `_define_field` never emits (it interpolates a literal, space-free type string), so it is unrepresentable in the scanned corpus. Honest on every realistic spelling.
- **(e) OVERWRITE-index boot-crash.** Caught — but by the OFFLINE pin only (variant 4). See residual R1: the LIVE re-appliability control's docstring over-claims.
- **(f) C-DEF / satisfiability.** Clean — reference build 50/0 (above).

---

## P1b — QUANTIFIER TABLE (every invariant classified; every guarded row carries a receipt)

| invariant | ∀-over-inputs vs guarded | receipt |
|---|---|---|
| owner_principal field emitted | direct existence (the RED-carrier for the clause pins) | variants 2/6 red the emit/guard pins |
| field is `option<record<principal>>` | direct shape | variant 1 reds it (offline + live poison + ownerless) |
| field is `OVERWRITE` (#107) | direct shape | variant 2 reds it |
| field carries NO DEFAULT / NO ASSERT | direct shape | variant 5 reds `…no_default_and_no_assert` |
| field ROUTES through `_define_field` | **mutation-proven** (∀ emitted owner-field statements carry the perturbation marker) | variant 2 (hand-written field) reds `…routes_through_the_shared_emitter` |
| index emitted / IF NOT EXISTS / NOT unique | direct shape | variants 6 / 4 / 3 each red |
| live: owned agent stores+reads the link | direct behavioural (RED-carrier) | reference greens |
| live: ownerless agent reads None (option<> discriminator) | guarded → **forced by fixture** (an ownerless CREATE) | variant 1 (required) reds it |
| live: a principal owns MANY agents (non-unique) | **∀ (N=2)** — a monoculture N=1 could not see UNIQUE | variant 3 reds it (2nd CREATE rejected) |
| migration: legacy row survives + reads None | dirty-store (legacy row written under OLD DDL) | required could red the apply/read |
| migration: field-add does NOT write-poison | **§1.4 discriminator, ∀-any-UPDATE** (one unrelated-column UPDATE forces it) | variant 1 reds live (coerce NONE) |
| migration: new owned agent writable | RED-carrier | reference greens |
| **DANGLE: delete succeeds ∧ agent survives ∧ link stale** | **∀-over-FATES** (refuse/cascade/null all forced), N=1 | variants 7/8/9 each red |
| **DANGLE ∀ owned agents** | **∀ (N=2)** — a build dangling the first but dropping the rest reds | variants 8/9 red at N=2 |
| exact-set of `record<principal>` links == the 4 | tripwire / coverage-check | variant 10 (grow) + receded-derivation (shrink) red it |
| reach control: corpus covers standalone slices | INSTRUMENT-0 coverage tripwire | receded-derivation reds it |

**No invariant is conditioned on the failure mode that prompted the work** (the PR93 hazard). The DANGLE is pinned as the OUTCOME property over ALL three wrong fates, not just the one recommended fate; non-unique and the ∀-dangle use N=2, not N=1.

---

## P1c — REACH TABLE (per instrument; empirical legs marked)

| instrument | reach DERIVED? | coverage a CHECKED variable? | effect vs proxy | one-source / mutation-proven | verdict |
|---|---|---|---|---|---|
| `_all_schema_ddl` + `_RECORD_PRINCIPAL` → exact-set pin | **YES** — iterates `dir(surreal_schema)` for the `generate_*_ddl` PROPERTY, not a hand-list (**empirical:** variant 10 new slice reds it) | **YES** — reds when `found` GROWS (variant 10) AND when the derivation RECEDES off a covered slice (**empirical:** §leg below) | **effect** — scans the EMITTED DDL text | the link is one-implementation via `_define_field` (mutation-proven, variant 2) | **safe** |
| `test_the_scanned_corpus_covers_the_standalone_comms_slices` (reach control) | spot-check of 3 named tables (agent/principal_key/audit) — a hand-list, NOT `observed==derived` | guards the derivation against RECEDING off the standalone agent slice (**empirical:** §leg below) | **effect** — checks the actual corpus string | n/a | **adequate** — belt-and-braces atop the exact-set pin, which IS the coverage-check for any receding reach that drops a KNOWN link |
| `…routes_through_the_shared_emitter` (owner field) | DERIVED — perturbs the shared `_define_field` | reds if the field stops routing (**empirical:** variant 2) | effect | THE mutation proof for one-implementation | **safe** |

**Empirical reach-recession leg (proves neither instrument is theater):** with the reference build applied, I perturbed the CONTRACT's `_all_schema_ddl` in a scratch copy of the test file to silently drop `generate_agent_ddl` from the derived corpus. Result: **BOTH** `test_the_scanned_corpus_covers_the_standalone_comms_slices` (reach control) **AND** `test_the_record_principal_link_set_matches_the_cascade_adjudication` (exact-set pin) went RED; the synthetic-only `…regex_has_nonzero_reach` control stayed green (it operates on a fixture, not the corpus). So a receding derivation is caught two ways.

**Stated bound (residual R4, currently vacuous):** the derived reach is "every `generate_*_ddl` surface", which equals "every table applied to the store" only while every table's DDL is emitted by a `generate_*_ddl`. I verified this holds today: `grep 'DEFINE FIELD' … | grep record<principal>` finds NO `record<principal>` DDL applied outside `surreal_schema`'s `generate_*_ddl` functions. A future link added via a differently-named runtime DDL path would be invisible to the exact-set pin — an honest bound, not a live gap. This is the reach law's honest-bound requirement satisfied, not violated.

**Legs run:** the exact-set pin and its two guards are IN-TREE, so they got the full wrong-build / receding-derivation empirical treatment (not construction-inspection).

---

## P2 — fixture discrimination

- **Many-agents (N=2), dangle-MANY (N=2):** a monoculture N=1 makes UNIQUE-vs-non-unique and dangle-all-vs-dangle-first invisible; the N=2 fixtures discriminate (variants 3/8/9 red at N=2). Verified.
- **Two-principal is not needed here** (this wave has no cross-principal isolation surface — that is R2.2, a later wave). N/A.
- **Legacy row written under the OLD DDL:** the migration fixtures write the legacy agent via `_agent_ddl_without_owner_principal()` (the real slice minus the owner statements) BEFORE applying the current slice — exactly the store-ref §1.4 trap-avoidance (a legacy row written AFTER the migration would be filled at CREATE and see no poison). Correct.
- **required-vs-option monoculture:** the ownerless-CREATE fixture (`owner_bare_id=None`) and the owned-CREATE fixture together force the option<> branch; variant 1 (required) reds the ownerless one. Discriminates.
- **Perturbation control:** my own wrong-build harness is validated by the reference build passing 50/0 (a probe that could not distinguish right from wrong would pass everything) AND by each wrong build reddening a DIFFERENT, on-point pin (not all reddening for one spurious reason). P0 satisfied.

---

## P6 — corpse sweep (bare, anchor-free patterns)

- `is_the_ONLY` / `the ONLY record<principal>`: two hits — `test_comms_tool.py:7570` (an UNRELATED comms-block paragraph test) and the revised pin's OWN historical docstring note (`test_principal_keys_schema.py:504`, explaining the rename). **Neither is an assertion of the old link set.** No corpse.
- Other test files mentioning `record<principal>` (`test_audit_schema.py`, `test_keeps_schema.py`, `test_keeps_store.py`, `test_oauth_identity_seam.py`, `test_keep_remediation_store_61.py`): each pins its OWN table's link individually — none asserts a global exact-SET, so none reds on adding the 4th link. Verified `grep 'expected = {'` returns only the revised pin.
- `test_principal_delete_cascade_61.py`: asserts per-fixture `cascaded == 2` (keys) / `member_of == 2` — counts about principal_key/member_of, untouched by the agent link (the delete does not touch agent). Stays green. No corpse.

The single global exact-set pin was updated in place (expected 3 → 4); the OLD 3-link state is verified RED at the base (P7). No suite is green because it still asserts the corpse.

---

## P7 — RED honesty (reproduced at the contract base)

`cd /tmp/adv62w1/loremaster && uv run python -m pytest tests/test_agent_owns_principal_schema.py tests/test_principal_keys_schema.py -p no:randomly -q` on the UNBUILT scratch (agent slice has zero `owner_principal`):

```
14 failed, 36 passed in 6.08s
```

The 14 failing node ids match the author's declared expected-RED set EXACTLY (13 in the new file + `test_the_record_principal_link_set_matches_the_cascade_adjudication`). Every failure is BEHAVIOURAL, not a collection error: the offline pins on `_owner_field_statement() is None` ("unbuilt"); the live pins on the engine rejecting a SCHEMAFULL CREATE of an undeclared column; the exact-set pin on `found` (the 3 real links) missing `('owner_principal','agent')`. Collect-only counts (verified, not relayed): new file **17 tests** (report prose says "16" — residual R3), keys file **33 tests**.

---

## Residuals — individual verdicts

- **R1 — `test_the_agent_slice_is_safely_re_appliable` docstring over-claim (recommend the author fix the prose).** Its docstring says it "REDDENS a build whose owner_principal INDEX is OVERWRITE." Empirically (variant 4) it does NOT — a `DEFINE INDEX OVERWRITE` over a *plain scalar* index re-applies cleanly (no rebuild-crash; that failure mode is HNSW-dim-specific, store-ref §1.5). The OFFLINE pin `test_the_owner_principal_index_is_IF_NOT_EXISTS_never_OVERWRITE` DOES catch the OVERWRITE index, so **no wrong build survives** — this is a docstring-accuracy defect (a control naming a discrimination it lacks), not a coverage hole. Cheap fix: correct the docstring to credit the offline pin, or drop the OVERWRITE claim from the live control's prose. **Not blocking.**
- **R2 — the dangle pins assert the observable OUTCOME, not "delete never touches agent."** They assert (delete returns / succeeds) ∧ (agent row survives) ∧ (owner_principal unchanged). A build that on principal-delete touched the agent benignly (e.g. stamped `last_note`) while preserving row + link would pass. That is neither a plausible builder error nor a violation of the pinned observable properties (R3.2 requires the rows survive with the stale link, which such a build satisfies). **Note only — the pinned properties are the right ones.**
- **R3 — report prose "16 tests"** for the new file; collect-only shows **17**. The declared-RED node LIST (13) is correct and fully reproduced. Trivial.
- **R4 — reach bound (stated, currently vacuous):** covered in §P1c. A `record<principal>` link applied via a non-`generate_*_ddl` runtime DDL path would escape the exact-set pin; no such path exists today (verified). Acceptable stated bound.

None of R1–R4 is a MISSING PIN (no wrong build survives on account of any of them), so none moves the verdict off SUFFICIENT.

---

## Instruments (pasted verbatim — scratch trees are disposable, brief-base §1)

**`regex_probe_62.py`** (offline `_RECORD_PRINCIPAL` reach on hostile spellings; frontier d):
```python
import re
_RECORD_PRINCIPAL = re.compile(
    r"\bFIELD\s+(?:OVERWRITE\s+)?(?P<field>\w+)\s+ON\s+(?P<table>\w+)\s+TYPE\b[^;]*?record<principal>(?![\w<])",
    re.IGNORECASE,
)
def links(ddl):
    return sorted((m.group("field"), m.group("table")) for m in _RECORD_PRINCIPAL.finditer(ddl))
# cases → observed:
#   'DEFINE FIELD OVERWRITE principal ON principal_key TYPE record<principal>;'        -> [('principal','principal_key')]
#   '… owner ON memory TYPE option<record<principal>>;'                                -> [('owner','memory')]
#   '… p ON t TYPE record<principals>;'                                                -> []   (longer name, correctly excluded)
#   '… sender ON message TYPE record<agent>;'                                          -> []   (different target)
#   '… owner ON agent TYPE record< principal >;' (spaces inside angle brackets)        -> []   (never emitted by _define_field)
#   '… owners ON t TYPE array<record<principal>>;'                                     -> [('owners','t')]  (caught)
```

**`av.py`** (wrong-build harness; rewrites the two production files from pristine `.orig` per variant, always from pristine so variants never compound). Anchors: `_AGENT_FIELD_SPECS`' `("last_note", …)` line; `_agent_statements`' `_plain_index(… _name …)` append; `PrincipalStore.delete`'s `BEGIN;\n DELETE {PRINCIPAL_KEY_TABLE}` txn head and its `count_rows = self._as_rows(` line. Variant edits, verbatim:
```
reference        : _AGENT_FIELD_SPECS += ("owner_principal","option<record<principal>>","")
                   _agent_statements  += _plain_index(AGENT_TABLE,"{AGENT_TABLE}_owner_principal",("owner_principal",))
                   PrincipalStore.delete UNCHANGED
required         : field type "record<principal>" (no option<>); index plain
field_ifnotexists: hand-write 'DEFINE FIELD IF NOT EXISTS owner_principal ON {AGENT_TABLE} TYPE option<record<principal>>'
                   appended directly in _agent_statements (NOT via _define_field, NOT in _AGENT_FIELD_SPECS); index plain
unique_index     : reference field; index via _unique_index(...)
overwrite_index  : reference field; hand-write 'DEFINE INDEX OVERWRITE {AGENT_TABLE}_owner_principal ON {AGENT_TABLE} FIELDS owner_principal'
default_on_field : field ("owner_principal","option<record<principal>>","DEFAULT NONE"); index plain
no_index         : reference field; NO index append
delete_refuse    : reference field+index; inject before count_rows — SELECT count() FROM agent WHERE owner_principal=type::record('{PRINCIPAL_TABLE}',$pid) GROUP ALL; if >0 raise RuntimeError('refuse: principal owns agents')
delete_cascade   : reference field+index; inject "DELETE agent WHERE owner_principal=type::record('{PRINCIPAL_TABLE}',$pid);" into the BEGIN..COMMIT txn
delete_null      : reference field+index; inject "UPDATE agent SET owner_principal=NONE WHERE owner_principal=type::record('{PRINCIPAL_TABLE}',$pid);" into the txn
reach_bogus      : reference field+index; append a new module fn generate_bogus_ddl() returning
                   "DEFINE TABLE IF NOT EXISTS bogus SCHEMAFULL;\n DEFINE FIELD OVERWRITE sponsor ON bogus TYPE record<principal>;\n"
```
Reproduction: `./scripts/scratch_copy.sh /abs/dest` → in `dest/loremaster/loremaster/store/` back up `surreal_schema.py`→`.orig` and `../principals.py`→`.orig` → `python3 av.py <variant>` → `cd dest/loremaster && uv run python -m pytest tests/test_agent_owns_principal_schema.py tests/test_principal_keys_schema.py -p no:randomly -q`.

---

## VERDICT: CONTRACT SUFFICIENT

I built ten wrong implementations plus a receding-derivation perturbation and could not make any of them pass the contract; every one is caught by an on-point pin that reds for the right reason, and the reference build takes the contract to 50/0 (a clean satisfiability receipt). The DANGLE test discriminates all three wrong fates; the §1.4 not-poison control reds a required field live; the reach is a genuine derivation whose coverage reds on both growth and recession. The residuals (chiefly a live control's docstring over-claiming a discrimination the offline pin actually provides) are notes for the author, not holes a builder could ship through. This is a strong contract.
