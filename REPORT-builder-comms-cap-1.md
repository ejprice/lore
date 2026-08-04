# REPORT-builder-comms-cap-1 — lore_comms body-cap raise 2000 → 4000 (#327)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK
- **state: done-with-deviations** — O-1..O-5 implemented per SPEC (`REPORT-design-sidecar-04b3-1.md` §COMMS-CAP). O-6 (deploy/smoke) is the LEAD's; NOT done here.
- **CAPABILITY CHECK (brief-base §4): PASS** — lore reachable (registered, #327 read); spike-surreal `:18000` reachable (TCP probe + live suite ran 1336 tests against fresh test DBs there); file writes work. No unmeetable demand. I did NOT deploy (O-6 is the lead's, correctly).
- deviations: (1) O-4 confirming pin placed in `test_comms_tool.py::TestCommsToolRegistration` (where the rendered-tool-schema machinery lives, mirroring `test_limit_declares_ge_one_in_the_tool_schema`), NOT `test_message_ledger.py` — the brief left the location conditional ("if it lives here"); putting it in the ledger test would clone server-build machinery (ONE-IMPLEMENTATION). (2) An UNGREPPABLE corpse pin — `test_comms_schema.py` live-store `body="z" * 2001` — was fixed; the `2001` literal (cap+1) contains no `"2000"` substring so the sweep missed it; **the test run caught it** (why the brief mandates running tests). (3) `surreal_schema.py:573` comment: I DROPPED the redundant `2000` literal rather than updating it to `4000` — restating the value in a comment directly above the constant contradicts its own "ONE source of truth" claim.
- **Packages considered:** none — no mechanism specified (a policy-constant value change + test pins; no library surface).
- **Graded/built against:** `931832e` (HEAD) + my uncommitted working-tree changes. O-2's DDL-derivation claim was empirically MEASURED (see body §O-2), so this line applies.
- decisions-needed (3, none blocking the build):
  1. **Doubled worst-case drain render** — at 4000, `_MAX_DRAIN_LIMIT=50` × cap = 200 KB (~50k tokens), 2× the 100 KB the cold-audit R10 already flagged as "a claim nothing measures". I updated the comment literal but did NOT touch `_MAX_DRAIN_LIMIT` (separate tunable, out of mandate). Recommend: acceptable (elision+honest-count bounds real renders; #327's own point is directives run ~2800, not 4000) — operator's call.
  2. **7 live-doc `2000` hits (all packet-03b design-ruling docs)** — left NO CHANGE per the archiving/DUAL law (rewriting falsifies what 03b ruled). Fork: (a) leave as historical [my pick] vs (b) add a supersession pointer. Lead/operator's call.
  3. **O-2 live-store migration is UNTESTABLE here** (fresh virgin DB per test, #131) → it is the lead's O-6 smoke: send a >2000-char body (e.g. 3000) through the LIVE redeployed comms and confirm it LANDS in the store.
- receipt pointers: RED→GREEN body §"RED demonstration" + §"GREEN"; O-4 mutation proof body §O-4; full O-5 sweep table body §O-5; diff = `git diff` (5 files, +37/-8); gates body §Gates.

---

## What changed (file:line → intent)

| # | site | change | O-item |
|---|---|---|---|
| O-1 | `store/surreal_schema.py` `MESSAGE_BODY_MAX_CHARS` | `2000` → `4000` (single source of truth) | O-1 |
| O-2 | `surreal_schema.py` `body`+`ack_note` ASSERTs | **NO CHANGE** — DERIVED (`f"...<= {MESSAGE_BODY_MAX_CHARS}"`); auto-follow verified | O-2 |
| O-3 | `test_message_ledger.py` pin | rename VALUE-FREE (`..._two_thousand_char_pointer_bound` → `..._pointer_bound`) + tripwire `== 2000` → `== 4000` | O-3 |
| O-4 | `test_comms_tool.py::TestCommsToolRegistration` | ADD `test_body_description_carries_the_LIVE_body_cap_constant` (rendered `body` desc ⊇ `str(cap)`) | O-4 |
| O-5a | `test_comms_schema.py:1683` offline DDL body pin | `assert "2000" in statement` → DERIVED `assert f"string::len($value) <= {cap}" in statement` (corpse caught RED) | O-5 |
| O-5b | `test_comms_schema.py:2215` live-store backstop | `body="z" * 2001` → `body="z" * (cap + 1)` (ungreppable corpse; test-run caught) | O-5 |
| O-5c | `surreal_schema.py:573`,`:581`,`server.py:1318` | prose literals: drop / reword / update | O-5 |

## RED demonstration (contract-first: the pins are LIVE wires, not the corpse)
After O-1 alone (constant → 4000), the two value-pinning tests went RED:
```
FAILED test_message_ledger.py::...::test_body_cap_is_the_designs_two_thousand_char_pointer_bound
  AssertionError: assert 4000 == 2000            # the O-3 tripwire fires — LIVE wire
FAILED test_comms_schema.py::...::test_body_carries_a_length_bound_the_store_itself_enforces
  assert '2000' in 'DEFINE FIELD OVERWRITE body ON message TYPE string ASSERT string::len($value) <= 4000'
2 failed, 468 deselected in 0.37s
```
The second RED is a **P8d corpse** (asserted the literal `"2000"` against DERIVED DDL text). Its output is ALSO the empirical proof for §O-2 below.

## §O-2 — the schema migration (the #107 class), verified SAFE + DERIVED
- `_define_field` (`surreal_schema.py:909-944`) returns `f"DEFINE FIELD OVERWRITE {name} ON {table} TYPE {type_expr}{suffix}"` — **OVERWRITE**, the #107 fix (docstring cites it). Not `IF NOT EXISTS`.
- Both ASSERTs interpolate the constant, so the RED output above shows the emitted DDL is now `... ASSERT string::len($value) <= 4000` — it DERIVES; no hand-edit of the ASSERT value (correctly untouched).
- **WIDENING is safe by construction:** every existing body ≤ 2000 ≤ 4000, so no row is write-poisoned (the opposite of #107's narrowing danger).
- **BUT the live-store migration is UNTESTABLE on this host** — every test mints a fresh virgin DB (`_surreal_harness.unique_database()`, #131), so the suite exercises the DERIVED ASSERT at 4000 on a CLEAN slate, never the long-lived-store convergence. "Only the running artifact proves the cake": the LEAD's O-6 deploy smoke MUST send a >2000-char body through the LIVE redeployed comms and confirm it LANDS. That is the load-bearing deploy receipt; it is NOT in my scope.

## §O-4 — the confirming pin, MUTATION-PROVEN (positive control)
`test_body_description_carries_the_LIVE_body_cap_constant` asserts the rendered `lore_comms` `body` param description (as an MCP client reads it) contains `str(MESSAGE_BODY_MAX_CHARS)`. It is genuinely additive — no prior pin covered the `body` PARAM description (the instructions-block cap sentence is pinned separately by `test_clause_4_the_body_cap_sentence_carries_the_LIVE_constant`, which is also DERIVED and auto-follows).
Positive control (probe-needs-a-control, PKT-28 C1):
- HEAD state (desc derived, cap 4000) → **PASS**.
- Mutated `server.py:9589` to a hardcoded `"2000 characters"` while constant = 4000 → **RED for the DRIFT reason**: `AssertionError: the lore_comms 'body' description must carry the live cap 4000 (derived from MESSAGE_BODY_MAX_CHARS, not a hardcoded literal)` — not a parse error.
- Reverted `server.py:9589` → **PASS**. `server.py` byte-restored (grep-confirmed: exactly one interpolated line, zero hardcoded `"2000 characters"`).

## §O-5 — THE BARE-2000 SWEEP (P8d: every hit file:line + INDIVIDUAL verdict; "all remaining are X" is BANNED)
Sweep method: `grep -rn "2000"` over prod + tests + scripts + docs (a NON-SYMBOL TEXTUAL SEAM + rename/deletion-exhaustiveness — **grep's honest cases** per the dogfood protocol; said out loud, no friction to file — grep was the right tool, not a lore weakness). Extended for cap-adjacent literals grep-"2000" cannot see (`200[0-9]`/`199[0-9]`).

**CODE — prod:**
- `surreal_schema.py:573` comment "…never re-declare, 2000)" → **CHANGED** (dropped redundant literal — see deviation 3).
- `surreal_schema.py:574` the constant → **CHANGED → 4000** (O-1, the change).
- `surreal_schema.py:581` comment "a 2000-char 'ref' is a BODY…" → **CHANGED** → "a body-sized 'ref'…" (drift-proof reword).
- `surreal_schema.py:620` `body` ASSERT `<= {MESSAGE_BODY_MAX_CHARS}` → **NO CHANGE — DERIVED**.
- `surreal_schema.py:666` `ack_note` ASSERT, same → **NO CHANGE — DERIVED** (the constant is SHARED by body+note; raising it lifts BOTH bounce points #327 names — ONE-IMPLEMENTATION).
- `server.py:1318` comment "50 entries with the 2000-char body cap" → **CHANGED → 4000** (illustrative arithmetic; see decision-needed 1 re: doubled worst-case).
- `server.py:1595` `f"bodies are capped at {_MESSAGE_BODY_MAX_CHARS}…"` → **NO CHANGE — DERIVED**.
- `server.py:9555` `f"…at most {_MESSAGE_BODY_MAX_CHARS}…"` (ack-note desc) → **NO CHANGE — DERIVED**.
- `server.py:9589` `f"{_MESSAGE_BODY_MAX_CHARS} characters (over-cap…"` (body desc) → **NO CHANGE — DERIVED** (mutation-proven, §O-4).
- `messages.py:112` re-export of the constant → **NO CHANGE — DERIVED** (symbol, not a literal).
- `messages.py:680,754` error strings `f"…{MESSAGE_BODY_MAX_CHARS}-char cap…"` → **NO CHANGE — DERIVED**.
- `_message_fakes.py:203` error string, same idiom → **NO CHANGE — DERIVED**.
- `scripts/comms_consumer_eval.py:859` `int(messages_module.MESSAGE_BODY_MAX_CHARS)` → **NO CHANGE — DERIVED** (reads the constant).

**CODE — tests:**
- `test_message_ledger.py:356/357` the pin → **CHANGED** (O-3 rename value-free + tripwire → 4000).
- `test_message_ledger.py:94,821,842,850,973,975,992` `_msg().MESSAGE_BODY_MAX_CHARS`(+1) → **NO CHANGE — DERIVED**.
- `test_comms_schema.py:1683` offline body DDL pin `assert "2000" in statement` → **CHANGED — DERIVED** (corpse; O-5 "reword to cite the constant").
- `test_comms_schema.py:2215` live-store `body="z" * 2001` → **CHANGED — DERIVED** `* (cap + 1)` (ungreppable corpse; caught by the test run — the CAKE pin).
- `test_comms_schema.py:1988/1994,2711` `_schema().MESSAGE_BODY_MAX_CHARS`(+1) → **NO CHANGE — DERIVED**.
- `test_comms_tool.py:7042,7048,7402` (now `:7063,:7069,:7423` after the O-4 insert) — historical NARRATIVE comments quoting an adversary's fabricated inverted text *"the 2000 char figure is advisory"* → **NO CHANGE — historical narrative** (describes a past attack; changing it falsifies the record; the LIVE pin `test_clause_4…:7400` is DERIVED via `_RULED_BODY_CAP_SENTENCE.format(cap=cap)` and auto-follows).
- `test_comms_tool.py:7186` `_RULED_BODY_CAP_SENTENCE` `"{cap}"` placeholder → **NO CHANGE — DERIVED**.
- `test_comms_tool.py:4692,7407,7445,7505,7622,7633,7829` `_msg().MESSAGE_BODY_MAX_CHARS`(+1) → **NO CHANGE — DERIVED**.
- `test_trace_telemetry.py:2131` docstring quoting the design-wave argument *"a 2000-char 'ref' is a BODY…"* about a DIFFERENT surface (trace-tool-name truncation) → **NO CHANGE — historical rationale quote**.

**CODE — substring-coincidental (verdicted individually to honor the "all remaining are X" ban):**
- `test_mcp_server.py:2817` `measured_file_count=2000` → **NO CHANGE — unrelated** (index-calibration file count).
- `test_mcp_server.py:5432,5456,5500,5514,5541,5597,5611,5636,5647,5673` `"x" * 20000` etc. → **NO CHANGE — unrelated** (`20000`, substring match; render-truncation fixtures).
- `pending_contract_gate.py:1315` `completed.stdout[-2000:]` → **NO CHANGE — unrelated** (stdout slice length).
- `lorescribe/tests/test_javascript.py:179` `len(minified) > 2000` → **NO CHANGE — unrelated** (minified-JS length guard).
- `lorescribe/tests/test_xml_generic.py:383,384,684` "~2000 tokens" → **NO CHANGE — unrelated** (XML chunk token-count comments).

**DOCS:**
- `docs/plans/v2/03b-comms-surface-design-rulings.md:282`; `03b-deferred-design-rulings.md:222,231,245,548`; `03b-design-rulings-r2.md:481,598` (7 hits) → **NO CHANGE — historical packet-03b design records** (the cap WAS 2000 at 03b; 04b-3 §COMMS-CAP supersedes to 4000; the DUAL/archiving law forbids silent rewrite of a completed packet's ruling). See decision-needed 2.
- `docs/plans/v2/receipts/**` (24 files) → **NO CHANGE — archived immutable receipts** (historical records; archiving law).

Old pin NAME sweep (`two_thousand`): zero code/test references remain post-rename; the only hits are in the SPEC (`REPORT-design-sidecar-04b3-1.md`), which correctly cites the old name to instruct the rename.

## Gates
- **Affected suites, `-n auto`:** `test_message_ledger.py` + `test_comms_schema.py` + `test_comms_tool.py` → **1336 passed, 14 skipped in 21.01s** (tests hit spike-surreal `:18000`, fresh test DBs — NOT `:18500`).
- **ruff:** `All checks passed!` (5 touched files).
- **mypy:** `Success: no issues found in 5 source files`.
- These three suites are the complete set referencing `MESSAGE_BODY_MAX_CHARS` in the test tree (grep-verified) — no other suite pins the body cap. My prod edits to `server.py`/`surreal_schema.py` are a value-widen + comments; no other suite asserts on them.

## Scope / do-not-touch honored
- Did NOT deploy (O-6 lead's). Did NOT touch git (lead commits + verifies the diff). Did NOT touch the schema ASSERTs (DERIVED). Did NOT touch `MESSAGE_POINTER_MAX_CHARS` (256, untouched — `body ≠ pointer` holds, `test_comms_schema.py:1988` green). Did NOT transition #327 (lead's, pending O-6).
- Writable set respected: `surreal_schema.py` (constant + bare-2000 comments only), `server.py` (bare-2000 comment only; O-4 mutation reverted), `test_message_ledger.py`, `test_comms_schema.py` + `test_comms_tool.py` (both carry bare-2000 literals ⇒ in the sweep-writable set), this report.

---
*Built 2026-08-04 by `builder-comms-cap-1` (Sonnet) against `931832e` (branch `feat/surreal-unification`). Spec: `REPORT-design-sidecar-04b3-1.md` §COMMS-CAP (O-1..O-5). Grep used for the bare-literal sweep + rename-exhaustiveness (its honest cases, said out loud). O-2's OVERWRITE/derivation empirically confirmed via the RED DDL output; the live-store migration is the lead's O-6 smoke.*
