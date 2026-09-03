brief-base v14 read

# REPORT — fix5-keepstore (packet 63a fix wave, finding #452)

## Summary block
- Receipt: `brief-base v14 read`
- State: done
- Deviations: fixed a stale in-file count comment ("6 write verbs" → "7") caused directly by my in-scope addition — same file, disclosed below (§Changed).
- Packages considered: none — no mechanism specified (test-data reconciliation only).
- Reuse ledger: 1 new dict entry, modeled EXACTLY on the sibling `create_keep` invocation (no new reusable symbol). See §Changed.
- Graded: n/a — this is a builder fix, not a verdict over another artifact.
- Decisions-needed: none.
- Receipt pointers: RED-before §RED-before · GREEN-after §GREEN-after · edit `loremaster/tests/test_engine_rejection_seam.py` `_KEEP_INVOCATIONS` (`get_or_create_keyed` entry) · routed-write-path evidence §Evidence.

## Capability check
Brief demanded: read brief-base + CLAUDE.md; load lore MCP; reproduce two RED node ids; read the
test contract; add a `get_or_create_keyed` invocation entry; confirm GREEN; write this report.
All satisfiable with my toolset (Bash/pytest, lore MCP, Read/Edit). lore MCP loaded via
`ToolSearch "+lore"`. No fallback to grep for structure questions (used `lore_get_symbol` for the
three production defs cited below).

## Mission
Finding #452: `get_or_create_keyed` was added to the KeepStore routed write-path set in 63a but
NOT to the fault-injection map, reddening two derived-invariant pins in
`loremaster/tests/test_engine_rejection_seam.py::TestTheRoutedSetIsDerivedAndComplete` at `[keep]`.

## RED-before (at HEAD `278f524`, before my edit)
Ran the two target node ids (`-n auto`):
```
E  AssertionError: KeepStore's routed set (methods calling ['wrap_store_rejection']) has drifted
   from the fault-injection map ... routed=[...'get_or_create_keyed'...] mapped=[...(no get_or_create_keyed)...]
   Extra items in the left set: 'get_or_create_keyed'          (test:622, invocation_map[keep])
E  AssertionError: KeepStore's routed set [...'get_or_create_keyed'...] != the known wrapping verbs
   [...(no get_or_create_keyed)...]  Extra items in the left set: 'get_or_create_keyed'  (test:632, known_wrapping_verbs[keep])
FAILED ...test_the_routed_set_equals_the_invocation_map[keep]
FAILED ...test_the_routed_set_equals_the_known_wrapping_verbs[keep]
2 failed in 4.53s
```
The DERIVED routed set (`_methods_routing_through_seam`, an AST walk of `KeepStore` for methods
referencing `wrap_store_rejection`) already contained `get_or_create_keyed` (the 63a production
method wraps its whole body — finding #400), but `_KEEP_INVOCATIONS` (whose keys are also
`expected_wrappers = frozenset(_KEEP_INVOCATIONS)`) did not. Reach law → RED.

⚠ The `| tail` pipeline reported "exited with code 0" for this run — that is the pipe's status,
NOT pytest's. The authoritative signal is the `2 failed` count in the tail (piped-test hazard,
per CLAUDE.md). Both node ids genuinely failed.

## Evidence — `get_or_create_keyed` IS a routed KeepStore write path
Read the production def via `lore_get_symbol loremaster.keeps.KeepStore.get_or_create_keyed`
(`loremaster/loremaster/keeps.py:521-612`):
- The ENTIRE verb body is inside one `with wrap_store_rejection(KeepStoreError, f"could not
  get-or-create ...")` (finding #400) — so it references the Layer-2 seam and the AST derivation
  correctly classifies it as routed.
- It WRITES: on a key-miss it CAS-CREATEs a keep + RELATEs the keeper edge via
  `execute_transaction`, re-reading the winner on a UNIQUE conflict (hot-row mint).
- Injection point: its first op is `existing = await self.get_by_key(key)`, and
  `get_by_key` → `self._query` → `run_query` (`loremaster.keeps.KeepStore._query`,
  `keeps.py:323-341`, delegating to the shared `loremaster.store._txn.run_query`). The
  fault injectors (`_inject_store_error`, `test_transport_faults_propagate_untouched`) patch
  `run_query`/`execute_transaction` on `case.module` (= `keeps_module`), so the initial key
  READ raises the injected fault and the surrounding `wrap_store_rejection` translates a
  `SurrealStoreError` to `KeepStoreError` / passes a transport fault through — identical to the
  sibling write verbs. The method docstring states verbatim: "the injection hits the initial key
  READ first."

## Changed
`loremaster/tests/test_engine_rejection_seam.py`, `_KEEP_INVOCATIONS` (the `keep` case's
fault-injection map; `expected_wrappers` is `frozenset(_KEEP_INVOCATIONS)`, and `_CASE_METHODS`
is derived from `case.invocations`, so this ONE addition reconciles both coverage pins AND
extends the mutation/behaviour ∀-tests):

1. Added one entry, placed right after its closest sibling `create_keep` (both mint keeps),
   modeled EXACTLY on `create_keep`'s shape (same kwargs `keeper_email=_KEEPER_EMAIL`,
   `type="project"`, `name="wrap"`, plus the required natural `key`) — no new pattern invented
   (ONE-IMPLEMENTATION):
   ```python
   "get_or_create_keyed": lambda s: s.get_or_create_keyed(
       key="project:wrap", type="project", keeper_email=_KEEPER_EMAIL, name="wrap"
   ),
   ```
   (Values are cosmetic: every consumer of the invocation map runs it UNDER fault injection or a
   patched seam — the lambda never executes against a healthy store, and the initial read raises
   before the server-side type ASSERT is reached.)
2. DEVIATION (caused-in-scope, same file): the adjacent `list_keeps_for_member` comment read
   "Unlike the 6 write verbs above" — adding `get_or_create_keyed` above it makes 7. Updated
   "6" → "7" so the natural-language surface stays consistent with the code (CLAUDE.md
   rename/reshape §"natural-language surfaces whose consistency with code no gate checks").

## GREEN-after (after my edit)
Focused re-run of exactly the two originally-RED node ids (`-n auto`):
```
..                                                                       [100%]
2 passed in 4.58s
```
Full scoped file (per brief — also exercises the new `[keep-get_or_create_keyed]` mutation +
behaviour ∀ variants that expanding `_CASE_METHODS` created):
```
..................................................................       [100%]
66 passed in 6.97s
```
Both pins reddened for the RIGHT reason at HEAD and go green ONLY because the map now matches the
derived production truth — a real reconciliation, not a weakened assertion. No assertion body was
edited, nothing suppressed, and the DERIVATION (`_methods_routing_through_seam`) and
`expected_wrappers` were left untouched; only the fault-injection data (`_KEEP_INVOCATIONS`) grew
to cover the new routed path.

## Reuse ledger
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_KEEP_INVOCATIONS["get_or_create_keyed"]` (dict entry, not a reusable symbol) | `lore_get_symbol loremaster.keeps.KeepStore.get_or_create_keyed` / `.get_by_key` / `._query` | the production def + seam path (routes through `wrap_store_rejection`; first op `get_by_key`→`_query`→`run_query`) | HAND-ROLLED as a copy of the sibling `create_keep` invocation shape — the file's established per-store idiom; no shared helper exists or is warranted for a one-line test lambda |

## Gates NOT run (per brief — lead's job)
Did NOT run ruff, typecheck, the currency gate, or the full suite. Did NOT stage/commit/mutate git
state. Writable set respected: only `loremaster/tests/test_engine_rejection_seam.py` (the map +
one caused-in-scope comment, both in-file) and this report were touched.
