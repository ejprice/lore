# REPORT-contract-62w2d — packet 62 Wave 2 CONTRACT REVISER (composite-index delta fix)

- `brief-base v14 read`
- `brief project v7 read`
- store reference read (cited, not re-transcribed): `docs/reference/surrealdb-31-capabilities.md`
  §1.1 (INDEX stays `IF NOT EXISTS`, never `OVERWRITE`), §1.8 (UNIQUE over `option<string>` =
  multiple-NONE + unique-non-NONE — the single-field `capability_hash` shape), §4 (a composite
  index serves its LEADING column, which is why every behavioural pin stays green on the composite
  wrong-build — the hole the adversary found).

## CAPABILITY CHECK (tool honesty §4)
Everything the brief demanded was reachable: the writable file
`loremaster/tests/test_agent_capability.py` is present and editable; `uv run pytest -n auto`,
`bash scripts/typecheck.sh`, `uv run ruff check` all ran; lore loaded via `ToolSearch "+lore"`;
registered on `lore_comms` (session `packet62`, role `contract-author`, cadence ≤1h). This is a
tests-only regex revision — no live store, no scratch tree, no subagents required. No impossibilities.

---

## SUMMARY BLOCK
- **STATE: done-with-deviations** — applied the EXACT adversary-proven one-line regex fix to
  `_index_statement_over`; the composite-index loosening hole is closed while the correct
  single-field build stays satisfiable. Gates green; RED count unchanged.
- **Deviation 1 (disclosed, prominent):** I also updated the DOCSTRING of `_index_statement_over`
  (not just the one regex line) — the old docstring literally described the `\b` behavior and
  asserted "`\s*$` would never match `… FIELDS <field> UNIQUE`", which the new pattern makes FALSE.
  Shipping a docstring that contradicts the code one line below it is the repo's #1 defect class
  (natural-language surface diverging from code); the update is a regression my in-scope change
  directly causes. NO pin/behavior changed. Revert the docstring hunk if you want regex-line-only.
- **Deviation 2 (brief inaccuracy, no code impact):** the brief's verify row
  `DEFINE INDEX ... FIELDS owner_principal → MATCH (plain single-field positive control)` is WRONG
  for `field=capability_hash` — a different field's index correctly does NOT match a
  `capability_hash`-parameterized pattern (NO MATCH, same under old and new). The real "plain
  single-field positive control" is `FIELDS capability_hash` (no UNIQUE) → MATCH. My table below
  uses the accurate cases; the fix is unaffected.
- **Packages considered:** none — no mechanism specified (tests-only regex revision).
- **Reuse ledger:** none — no new reusable symbol introduced (a single regex-literal change inside
  an existing helper).
- **Graded:** `9a18c34` (working tree = HEAD `9a18c34` + this ONE uncommitted regex/docstring edit;
  the lead commits) · HEAD-at-report `9a18c34` · **SAME**.
- **Decisions-needed:** none — this is the contract-author one-line regex fix the adversary
  pre-committed to (not an operator fork). Deviation 1 is a yes/no on keeping the docstring hunk.
- **Receipt pointers:** the fix → `_index_statement_over` in `test_agent_capability.py` · regex
  proof → §"Regex proof table" below · RED count → §"pytest RED count" below.

---

## THE ONE FIX — the exact diff

`loremaster/tests/test_agent_capability.py`, helper `_index_statement_over` (the regex line):

```diff
-        and re.search(rf"FIELDS\s+{field}\b", statement, re.IGNORECASE)
+        and re.search(rf"FIELDS\s+{field}(\s+UNIQUE)?\s*$", statement, re.IGNORECASE)
```

The old `\b` is a zero-width boundary between `capability_hash` (word char) and a following `,`
(non-word), so it matched a COMPOSITE `… FIELDS capability_hash, owner_principal UNIQUE`. The new
form anchors the field to end-of-statement with an OPTIONAL trailing ` UNIQUE`
(`(\s+UNIQUE)?\s*$`): the field must be the WHOLE, SOLE field list. The docstring above the line was
updated to describe this accurately (Deviation 1). This is the exact alternative the ORIGINAL 62w2
adversary handed over and the 62w2b delta adversary re-proved.

---

## Regex proof table (accurate — all cases against the NEW pattern, `field=capability_hash`)

Re-runnable instrument (pasted verbatim; no repo imports needed):

```python
import re
field = "capability_hash"
OLD = rf"FIELDS\s+{field}\b"                 # the round-1 form (the hole)
NEW = rf"FIELDS\s+{field}(\s+UNIQUE)?\s*$"   # the fix
def m(pat, s): return bool(re.search(pat, s, re.IGNORECASE))
```

| index statement (`DEFINE INDEX … ON agent`) | OLD `\b` | NEW `(\s+UNIQUE)?\s*$` | verdict |
|---|---|---|---|
| `FIELDS capability_hash UNIQUE` (correct single-field UNIQUE) | True | **True** | MATCH — satisfiable, C-DEF stays closed |
| `FIELDS capability_hash` (plain single-field, non-unique) | True | **True** | MATCH — plain single-field positive control |
| `FIELDS capability_hash, owner_principal UNIQUE` (COMPOSITE) | True | **False** | NO MATCH — **the hole, now closed** |
| `FIELDS capability_hash_extra` (`_extra`) | False | **False** | NO MATCH — exact-token preserved |
| `FIELDS owner_principal` (a DIFFERENT field) | False | **False** | NO MATCH — a foreign field is not this field's index (brief said MATCH; that is inaccurate — see Deviation 2) |

The load-bearing row is the COMPOSITE: `True → False`. Both positive controls (correct UNIQUE,
plain single) stay MATCH, so the correct single-field build remains satisfiable (the 3 index pins
still go GREEN on it — corroborated by the 62w2b adversary's 64/64 satisfiability leg on the correct
single-field reference build). `_extra` and a foreign field stay NO MATCH.

---

## pytest RED count (`uv run pytest -n auto loremaster/tests/test_agent_capability.py`)

```
33 failed, 3 passed in 6.66s
```

**UNCHANGED from round 1** — the 62w2b adversary reported `per-file RED: test_agent_capability.py
33`, and it is still 33. The regex change does NOT alter the HEAD RED count, and this is
mechanically why: at HEAD `generate_agent_ddl()` emits NO capability_hash index (unbuilt), so
`_index_statement_over(...)` returns `None` regardless of the pattern. Confirmed the 3 index pins
are RED for the *unbuilt* reason (`assert None is not None`), not a pattern effect:

```
FAILED …TestTheCapabilityHashUniqueIndex::test_the_capability_hash_index_is_emitted
FAILED …TestTheCapabilityHashUniqueIndex::test_the_capability_hash_index_is_UNIQUE
FAILED …TestTheCapabilityHashUniqueIndex::test_the_capability_hash_index_is_IF_NOT_EXISTS_never_OVERWRITE
   assert None is not None  # unbuilt
```

The regex fix only changes discrimination when a `capability_hash` index EXISTS on a build — i.e.
it rejects the composite wrong-build while still accepting the correct single-field build. That is
the adversary's whole finding, and it is not observable at HEAD (nothing built), only against the
two reference builds the adversary constructs. The ownerless-deny pin (FIX 2) and every other pin
are untouched and remain in the 33.

## Gates
- `uv run pytest -n auto loremaster/tests/test_agent_capability.py` → **33 failed, 3 passed** (RED
  unchanged; the 3 green are the HEAD-green pins: 2 migration pins OLD==NEW + the static `Agent`
  model no-leak guard).
- `uv run ruff check loremaster/tests/test_agent_capability.py` → **All checks passed!**
- `bash scripts/typecheck.sh` → all 7 members OK (`lorerunes/lorescribe/loresigil/loremaster/
  skills/docs·eval/scripts` + shellcheck).

## KEPT UNCHANGED (as briefed)
Every other pin is byte-untouched: the round-1 ownerless-deny pin (FIX 2), the binding /
no-leak / DRY-mutation trio, mint-once, no-cache, ESC-3, reach, stamp_owner, resolve_agent,
the field DDL pins, migration pins, uniform-deny/no-oracle. Only `_index_statement_over`'s regex
literal (+ its now-accurate docstring, Deviation 1) changed.

## VERDICT
The composite-index loosening hole the 62w2b adversary found is closed with the exact one-line
regex it proved. Correct single-field build stays satisfiable; composite + `_extra` + foreign-field
rejected; RED count unchanged at 33; ruff + typecheck clean. Ready for re-grade / commit.
