# REPORT-adversary-62w2b — packet 62 Wave 2 CONTRACT-ADVERSARY (FOCUSED DELTA re-grade)

- `brief-base v14 read`
- `brief project v7 read`
- store reference read: `docs/reference/surrealdb-31-capabilities.md` — §1.1 (INDEX stays
  `IF NOT EXISTS`, never `OVERWRITE`), §1.8 (UNIQUE over `option<string>` = multiple-NONE +
  unique-non-NONE — the single-field shape `capability_hash` needs), §4 (composite index is
  leading-column only). Cited, not re-transcribed.

## CAPABILITY CHECK (tool honesty §4)
Everything the brief demanded was reachable: `scripts/scratch_copy.sh` produced a
provenance-asserted scratch copy at `/tmp/adv62w2b`; spike-surreal test store
`ws://127.0.0.1:18000` (systemd, never :18500) up and every live pin ran; lore loaded via
`ToolSearch "+lore"`; registered on `lore_comms` (session `packet62`, role
`contract-adversary`); pytest ran. Role spec (`contract-adversary.md`) forbids spawning
subagents — I did the work directly. No impossibilities.

**Tree provenance receipt (#140):** `loremaster.__file__` =
`/tmp/adv62w2b/loremaster/loremaster/__init__.py` — asserted by `scratch_copy.sh` AND re-printed
live under `uv run python` (a bare `python3 -c` shows `None`: system python, no venv — a
red herring, called out here so it is not mistaken for a poisoned copy). Every pytest run below
is `cd /tmp/adv62w2b && uv run pytest`, grading the SCRATCH tree.

---

## SUMMARY BLOCK
- **VERDICT: CONTRACT INSUFFICIENT** — FIX 1 (`\s*$`→`\b`) closed the C-DEF but OPENED a NEW
  hole: a COMPOSITE/multi-field UNIQUE index passes ALL THREE single-field index pins. This is
  exactly the "a just-closed-the-pins revision ships a new wrong-build" pattern the delta exists
  to catch. FIX 2 is sound. One cheap missing pin / one-line regex fix.
- **Graded:** `9a18c34` (the wave-2 fix commit `test(62): wave-2 contract fixes — adversary round
  1`) · HEAD-at-report `9a18c34` · **SAME**. (`6b180f0` = the pre-fix contract the prior adversary
  graded; `9a18c34` = the reviser's committed fix, = HEAD.)
- **P1 headline — a wrong build survives the WHOLE contract:** the reference build with a
  COMPOSITE unique index `… FIELDS capability_hash, owner_principal UNIQUE` passes **64/64** across
  the 3 files. `capability_hash` is NOT unique alone (uniqueness is over the pair), so the
  collision backstop `test_the_capability_hash_index_is_UNIQUE` PROMISES ("a duplicate capability
  hash across agents is rejected") is FALSE, yet the pin passes. Reproduced with full positive
  controls.
- **MISSING PIN (FIX-1 loosening) — the exact fix:** `_index_statement_over`'s `\b` matches
  `capability_hash` before a comma. Change `rf"FIELDS\s+{field}\b"` →
  `rf"FIELDS\s+{field}(\s+UNIQUE)?\s*$"` (proven: correct single-field & non-unique MATCH;
  composite & `_extra` REJECTED). This is the alternative the *original* 62w2 adversary already
  handed over ("or `…(\s+UNIQUE)?\s*$`") — the reviser picked `\b`, which reopened the composite
  door the prior `\s*$` had shut. Optionally add a dedicated single-field pin
  (`test_the_capability_hash_index_is_over_capability_hash_ALONE`).
- **FIX 1 satisfiability CONFIRMED (measured, not relayed):** the CORRECT single-field reference
  build → the 3 C-DEF index pins go GREEN; full 3-file suite **64 passed / 0 failed** (was 60/3 at
  `6b180f0`). The C-DEF is genuinely closed for the correct build.
- **FIX 2 CONFIRMED sound (measured):** ownerless pin REDs the None-permissive two-idiom wrong
  build (ownerless cap resolved under bob's token → agent id `11750d63…`), PASSES on the correct
  build (part of the 64/64), and the OWNED binding pin stays GREEN on the wrong build — proving
  the ownerless pin is the SOLE guard (owned-only monoculture confirmed). Not itself a C-DEF.
- **No regression (measured wrong-builds):** binding-skip → binding pin RED; leak-onto-row → BOTH
  no-leak pins RED; private-parse-clone → agents-identity pin RED (routing-mutation + principal-keys
  pins correctly stay green — per-consumer isolation); reach-orphan → coverage pin RED; mint-once
  GREEN on correct. All discriminate — the two fixes disturbed nothing.
- **RED honesty (derived both ways):** 53 declared == 53 actual RED-at-HEAD `9a18c34`; zero
  node-id diff in either direction; the new ownerless pin is present in the actual RED set.
- **Reuse ledger:** none — I authored no production symbol for the repo (a scratch reference
  build only, discarded).
- **Packages considered:** none — no mechanism specified (this is a grade of a tests-only
  revision; the mechanism package survey stands from `REPORT-adversary-62w2.md` P-PKG, trusted per
  brief).
- **Graded (prior legs trusted per brief):** the 18-build security sweep, the P1b quantifier
  table, the P1c reach table and the P-PKG diff from `REPORT-adversary-62w2.md` are NOT redone
  (brief: "trust that sweep; do not redo it"). My delta confirms they were not disturbed via the
  representative wrong-builds above.
- **Decisions-needed:** none — the fix is a contract-author one-line regex change, not an
  operator fork.

---

## THE FINDING — FIX 1's `\b` opened a composite-index loosening hole (BLOCKER)

**Root cause.** `test_agent_capability.py::_index_statement_over` now matches the field at a word
boundary:
```python
and re.search(rf"FIELDS\s+{field}\b", statement, re.IGNORECASE)   # FIX 1
```
`\b` is a zero-width boundary between `capability_hash` (`h`, a word char) and a following `,`
(non-word). So it matches a COMPOSITE index `… FIELDS capability_hash, owner_principal UNIQUE`
just as it matches the correct `… FIELDS capability_hash UNIQUE`. The prior `\s*$` anchor
REJECTED the composite (it did not end at the field) — but it ALSO rejected the correct build
(the C-DEF). The fix swapped one defect for another.

**Offline probe matrix** (`test_adv_composite_probe.py`, pasted verbatim below; runs the REAL
`TestTheCapabilityHashUniqueIndex` pins against each crafted index under a patched
`generate_agent_ddl`). `allPASS=True` means all 3 index pins pass:
```
CORRECT_single_unique         allPASS=True   {emitted:PASS, UNIQUE:PASS, IF_NOT_EXISTS:PASS}   <- intended
COMPOSITE_multifield_unique   allPASS=True   {emitted:PASS, UNIQUE:PASS, IF_NOT_EXISTS:PASS}   <- THE HOLE
NONUNIQUE_single              allPASS=False  {emitted:PASS, UNIQUE:RED,  IF_NOT_EXISTS:PASS}   <- PC
OVERWRITE_single_unique       allPASS=False  {emitted:PASS, UNIQUE:PASS, IF_NOT_EXISTS:RED}    <- PC
WRONGFIELD_unique             allPASS=False  {emitted:RED,  UNIQUE:RED,  IF_NOT_EXISTS:RED}    <- PC
EXTRA_token_unique            allPASS=False  {emitted:RED,  UNIQUE:RED,  IF_NOT_EXISTS:RED}    <- PC (capability_hash_extra)
```
`re FIELDS capability_hash\b matches composite? -> True`. Every positive control fires (correct
passes all 3; the four known-wrong shapes each red the RIGHT pin), so the probe demonstrably SEES
both a pass and a red — it is not passing for the wrong reason (P0).

**DEFINITIVE P1 — the composite build survives the ENTIRE contract.** I set the reference build's
`_unique_index` to `("capability_hash", "owner_principal")` and ran all 3 files:
```
emitted index: DEFINE INDEX IF NOT EXISTS agent_capability_hash ON agent FIELDS capability_hash, owner_principal UNIQUE
64 passed in 11.62s
```
So a plausible wrong build (wrong arity to the shared `_unique_index` emitter — e.g. a builder
scoping uniqueness "per owner") passes the WHOLE contract. No live pin checks single-field-ness:
the verify lookup is `WHERE capability_hash = $h`, which index-serves via the composite's LEADING
column (store §4), so every behavioural pin is green too.

**Severity — honest.** Real-world exploitability is LOW: `capability_hash = sha512_hex(name:secret)`
over a 256-bit `token_urlsafe(32)` secret, so genuine hash collisions never occur and the built
system would behave correctly in practice. The DEFECT is that the CONTRACT fails to enforce the
invariant it names — `test_the_capability_hash_index_is_UNIQUE`'s own message promises "a duplicate
capability hash across agents is rejected (the collision backstop)", and the composite build
falsifies that message while passing the pin. This is the FIXTURES-MUST-DISCRIMINATE /
"a failure message that promises a check the assertion does not perform" class (CLAUDE.md), AND it
is a *newly-introduced* one — which is precisely what a delta re-grade exists to catch. Per the
brief's pre-commitment ("composite passes ⇒ INSUFFICIENT with the exact pin"), the verdict is
INSUFFICIENT.

**The exact fix (proven, `uv run`):**
```
Proposed:  FIELDS\s+capability_hash(\s+UNIQUE)?\s*$
  correct_single_unique  match=True    <- satisfiable (the C-DEF stays closed)
  nonunique_single       match=True    <- returns the statement, so the UNIQUE pin reds on absence of UNIQUE
  composite_unique       match=False   <- composite correctly rejected (emitted pin reds)
  extra_token            match=False   <- exact-token preserved (capability_hash_extra)
```
This closes the composite hole AND keeps the correct single-field UNIQUE satisfiable — the one-line
change the original adversary already proposed. (A dedicated single-field pin asserting the index's
`FIELDS` clause is EXACTLY `capability_hash` would be belt-and-braces, but the regex fix alone
suffices.)

---

## SATISFIABILITY RECEIPT (FIX 1) — the correct build reaches 64/64

Reference build authored in `/tmp/adv62w2b` off HEAD `9a18c34` (provenance-asserted; reproduces the
prior adversary's build shape). Correct SINGLE-field UNIQUE index:
```
64 passed in 12.71s   # 53 formerly-RED now green + 11 controls, across the 3 wave-2 files
```
Was **60/3** at `6b180f0` (the 3 = the C-DEF index pins). So the `\s*$`→`\b` change greened exactly
those 3 for the correct single-field build, and FIX 2's new ownerless pin greens on the correct
build too → 64/64. The C-DEF is genuinely closed for the intended build (no false-green: the pins
stay RED at HEAD because the field/index are absent — verified in the RED-honesty section).

The reference build's edits (the satisfiability instrument, for reproduction):
- `lorerunes/lorerunes/credential.py` — `parse_credential(presented) -> (name, secret) | None`
  (`is_blank` → `partition(":")` → blank-half reject); re-exported in `lorerunes/__init__.py`.
- `loremaster/store/surreal_schema.py` — `("capability_hash","option<string>","")` +
  `("capability_expires_at","option<datetime>","")` appended to `_AGENT_FIELD_SPECS`;
  `_unique_index(AGENT_TABLE, f"{AGENT_TABLE}_capability_hash", ("capability_hash",))` in
  `_agent_statements`.
- `loremaster/agents.py` — `AgentRegisterResult.capability: str|None=None`; `register` gains
  `owner_principal_id` kw, create-branch mints `secrets.token_urlsafe(32)`, stores
  `capability_hash=sha512_hex(name:secret)` + `owner_principal` (RecordID) + `capability_expires_at=None`,
  returns the raw credential ONCE (re-register mints nothing); `verify_capability` mirrors
  `PrincipalKeyStore.verify` (one `now`, shared `parse_credential`, UNIQUE-hash SELECT with
  `owner_principal.{email,status,expires_at}` traversal, 4 early denies + optional expiry, uniform
  None, rides `self._query`); imports shared `parse_credential`.
- `loremaster/principal_keys.py` — verify re-routed through the shared `parse_credential`.
- `loremaster/owner_stamp.py` — `stamp_owner(access_token, agent_capability, *, registry)`
  (fail-closed; routes owner_agent through `registry.verify_capability`), re-exported at
  `loremaster.stamp_owner`.
- `loremaster/server.py` — `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` = the 6 derived governed tools →
  triggers.
- `loremaster/principals.py` — module docstring acknowledges the `owns` edge (I1) while keeping
  "conflated"/"never wire" (I2).

---

## FIX 2 — the ownerless-deny pin DISCRIMINATES (measured)

Wrong build: the two-idiom None-permissive verify (cond 3 `if owner_email is not None and … : deny`
AND cond 4 `if owner_status is not None and … : deny` — a NONE owner matches any principal):
```
FAILED …TestVerifyCapabilityAdmission::test_an_ownerless_agents_capability_is_denied
    assert '11750d6367015600b887a34892a2f936' is None   # ownerless cap resolved under a FOREIGN token
PASSED …::test_the_binding_denies_a_valid_capability_under_a_DIFFERENT_principals_token   # owned still denies
PASSED …::test_a_valid_capability_under_its_owners_token_resolves_the_agent                # positive control
```
So: the ownerless pin REDs the exact confused-deputy build the prior adversary reproduced; the
OWNED binding pin stays GREEN on that same wrong build (it cannot see the ownerless door — the
owner-PRESENCE monoculture the fix exists to close); and on the CORRECT build the ownerless pin is
part of the 64/64. FIX 2 forces the deny it was written to force, and it is NOT a C-DEF (it greens
on a correct build).

---

## NO REGRESSION — the trio + reach + mint-once still discriminate

| wrong build (in the reference tree) | pin run | result |
|---|---|---|
| binding-skip (cond-3 mismatch check removed) | `test_the_binding_denies…DIFFERENT_principals_token` | **RED** ✓ |
| leak (raw credential persisted onto the row via last_note) | `test_the_raw_secret_is_never_persisted…` + `…never_appears_in_a_rendered_agent` | **RED×2** ✓ |
| private parse clone in `agents` (not the shared object) | `test_agents_references_the_lorerunes_parse` | **RED** ✓ (routing-mutation + principal-keys pins stayed GREEN — per-consumer isolation) |
| reach-orphan (governed tool dropped from adjudication) | `test_every_governed_tool_is_pending_owner_stamp_and_adjudicated` | **RED** ✓ |
| — (correct build) | `test_re_register_does_not_rotate_a_live_secret` (mint-once) | GREEN ✓ |

The fixes are isolated to `test_agent_capability.py` (a regex + one new pin); these confirm the
trio (binding / no-leak / DRY-mutation), the reach coverage pin and mint-once still discriminate —
undisturbed.

---

## RED HONESTY — declared 53 == actual RED-at-HEAD (derived both ways)

At HEAD `9a18c34`, `uv run pytest <the 3 files>`: **53 failed, 11 passed** (0 collection errors).
Mechanically parsed the reviser's declared-RED set (53 node ids) from `REPORT-contract-62w2c.md`
and diffed against the actual FAILED node set:
```
in ACTUAL-RED but NOT declared:  (empty)
declared but NOT actual-RED:     (empty)
new ownerless pin present in ACTUAL red set: 1
per-file RED: test_agent_capability.py 33 · _reach.py 3 · _seams.py 17
```
Exact match both directions; the declared set the lead feeds to `mutation_proof.py` /
`pending_contracts.yaml` is accurate.

---

## The composite probe (the instrument, pasted verbatim so the claim is re-runnable)

```python
# /tmp/adv62w2b/loremaster/tests/test_adv_composite_probe.py (excerpt — the load-bearing legs)
import test_agent_capability as t
from loremaster.store import surreal_schema

_BASE = surreal_schema.generate_agent_ddl()
_FIELD = "DEFINE FIELD OVERWRITE capability_hash ON agent TYPE option<string>"

def _ddl_with_index(index_stmt):
    return _BASE.rstrip().rstrip(";") + ";\n" + _FIELD + ";\n" + index_stmt + ";\n"

def _verdicts(monkeypatch, index_stmt):
    monkeypatch.setattr(surreal_schema, "generate_agent_ddl", lambda: _ddl_with_index(index_stmt))
    inst = t.TestTheCapabilityHashUniqueIndex()
    out = {}
    for pin in ("test_the_capability_hash_index_is_emitted",
                "test_the_capability_hash_index_is_UNIQUE",
                "test_the_capability_hash_index_is_IF_NOT_EXISTS_never_OVERWRITE"):
        try:
            getattr(inst, pin)(); out[pin] = "PASS"
        except AssertionError:
            out[pin] = "RED"
    return out

# COMPOSITE = "DEFINE INDEX IF NOT EXISTS agent_capability_hash ON agent FIELDS capability_hash, owner_principal UNIQUE"
# _verdicts(mp, COMPOSITE) -> all PASS  (the hole)
# _verdicts(mp, CORRECT_single_unique) -> all PASS  (positive control)
# NONUNIQUE -> UNIQUE pin RED; OVERWRITE -> IF_NOT_EXISTS pin RED; WRONGFIELD/EXTRA -> emitted pin RED
```

Scratch tree `/tmp/adv62w2b` is disposable (scratch_copy.sh); nothing committed — this report is
the durable record. Provenance receipt (uv run): `loremaster.__file__` = `/tmp/adv62w2b/loremaster/loremaster/__init__.py`.

## VERDICT: CONTRACT INSUFFICIENT
One newly-introduced missing pin, a contract-author fix (not an operator fork):
- **FIX 1's `\b` opened a composite-index loosening hole** — a multi-field UNIQUE index
  `… FIELDS capability_hash, owner_principal UNIQUE` passes all 3 single-field index pins and the
  whole 64-pin contract, while the `is_UNIQUE` pin's own message ("a duplicate capability hash
  across agents is rejected") is falsified. **Fix:** `_index_statement_over`'s
  `rf"FIELDS\s+{field}\b"` → `rf"FIELDS\s+{field}(\s+UNIQUE)?\s*$"` (proven to keep the correct
  single-field satisfiable while rejecting composite + `_extra`).

Everything else in the delta is CONFIRMED GOOD (measured, not relayed): FIX 1's satisfiability leg
(64/64 on the correct single-field build, was 60/3), FIX 2's ownerless deny (discriminates the
None-permissive build, greens on correct, owned-monoculture confirmed), no regression on the trio /
reach / mint-once, and RED honesty (53 == 53, zero diff). Fix the one regex and this contract is
strong.
