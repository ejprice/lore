# REPORT-fixer-60-blocks-refs

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **done-with-deviations**
- deviation 1 (prominent): fixed a THIRD stale reference the brief's two line-numbers did not name — `test_blocks_edge.py:216` `blocks-endpoints4` → `blocks-endpoints1`. Same rename-sweep class (stale pytest parametrize-id suffix). Pre-existing (stale at HEAD `f0ebbf4` too, not caused by wave-1); verified stale against `--collect-only`. Comment/docstring only.
- deviation 2 (real endpointsN staleness sits at L8881, not L8888): the brief said "~8888-8890"; the actual stale `endpointsN` was `refers-endpoints3` at **L8881**; L8890 held the `_five_known_edges`. L8888 (`blocks-endpoints1`) was already correct and left untouched.
- Packages considered: none — no mechanism specified (comment/docstring edits only)
- Reuse ledger: none (no new symbols)
- Base: edits made against HEAD `f0ebbf4` + the uncommitted wave-1 contract tree (test_enforced_relations.py / _enforced_relations_scaffold.py / surreal_schema.py). `test_blocks_edge.py` was clean at HEAD; diffstat = 4 insertions / 4 deletions (my four one-line edits, nothing else).
- decisions-needed:
  - (info) confirm you're happy I fixed the L216 pre-existing staleness rather than only flagging it (in-file, zero-risk, comment-only, verified). See §Deviation-1.
  - (surface) the commented 04b mutation-proof recipe (PROOFS 1–5, ~L8777–8900) covers only the FIVE 04b edges; it has NO `member_of` leg. That is historically correct (the recipe is §04b's, executed 2026-07-28), NOT stale — member_of's own proof belongs to packet 60 (test_keeps_schema.py). No action taken; flagging in case you want the member_of proof cross-referenced here. See §Recipe-scope.
- receipt pointers: grep sweep §Sweep; edits §Edits; ground truth §Ground-truth; verification §Verify.

## Ground-truth (`--collect-only`, LIVE working tree)
`uv run pytest loremaster/tests/test_enforced_relations.py --collect-only -q`

Exact-set pin (renamed by wave-1): `TestEveryRelationEdgeIsEnforced::test_the_relation_edge_set_is_EXACTLY_the_six_known_edges`

`test_the_edge_declares_its_IN_and_OUT_endpoint_tables` parametrize ids (source: `@pytest.mark.parametrize(("edge","endpoints"), sorted(KNOWN_RELATION_EDGES.items()))` — ALPHABETICAL, `sorted()` present at HEAD already):
- `answers_to-endpoints0`
- `blocks-endpoints1`
- `briefed-endpoints2`
- `member_of-endpoints3`  ← new (inserts between briefed and refers)
- `refers-endpoints4`     ← was `endpoints3` pre-member_of
- `to-endpoints5`         ← was `endpoints4` pre-member_of

`test_the_edge_is_declared_OVERWRITE_never_IF_NOT_EXISTS[<edge>]` — unique-string ids, NO numeric suffix; `[blocks]` unchanged by the member_of insert.

Why L216's `blocks-endpoints4` was ALREADY stale at HEAD: the parametrize `sorted()`s, so `blocks` is index 1 in both the 5-edge and 6-edge worlds. `endpoints4` never matched any collected node id under the sorted parametrize — it is a pre-existing docstring error, independent of packet 60, corrected to `endpoints1` to name the real node.

## Edits (all in `loremaster/tests/test_blocks_edge.py`, comment/docstring only)
| line | before | after | reason |
|------|--------|-------|--------|
| 211 | `` ...EXACTLY_the_five_known_edges`` — the exact-set pin.`` | `` ...EXACTLY_the_six_known_edges`` `` | fix #1 — pin renamed five→six by wave-1 |
| 216 | ``[blocks-endpoints4]`` | ``[blocks-endpoints1]`` | **deviation 1** — pre-existing stale parametrize-id suffix; blocks=index1 under sorted() |
| 8881 | `"REFERS_RELATION:refers-endpoints3"` | `"REFERS_RELATION:refers-endpoints4"` | fix #2b — member_of insert bumped refers 3→4 (recipe loop pair) |
| 8890 | `..._five_known_edges" \` | `..._six_known_edges" \` | fix #2a — pin renamed five→six |

Left CORRECT (verified, not touched): L8881 `answers_to-endpoints0` (still 0), L8888 `blocks-endpoints1` (still 1), L8889 `[blocks]` (OVERWRITE pin, no suffix).

## Sweep — every residual `five` hit, individually verdicted (bare, anchor-free grep)
`grep -niE 'five' loremaster/tests/test_blocks_edge.py` after edits:
| line | verdict | note |
|------|---------|------|
| 130 | inert-unrelated | prose: task-listing renders "five rows … nor which five" (display-cap narrative) |
| 132 | inert-unrelated | prose: "ledger holds five open tasks" (same narrative) |
| 190 | inert-unrelated | prose: §11.1 forgery table "bounded to five served surfaces" |
| 219 | inert-unrelated | prose: "break FIVE committed pins" in test_mcp_server.py |
| 222 | inert-unrelated | prose: "five were RE-AUTHORED IN PLACE" (same 5 pins) |
| 622 | inert-unrelated | prose: runtime bundle "five ledgers" |
| 960 | inert-unrelated | prose: "Five steps, cloned in shape" (5-step fixture pattern) |
| 6140 | inert-unrelated | prose: "the DAG's five" (5 fixture names) |
| 7618 | inert-unrelated | prose: "∀ over SHAPE (five of them)" (5 shape siblings) |
| 8280 | inert-unrelated | prose: forgery table "bounded to five served surfaces" (dup of L190) |
| 8779 | inert-unrelated | quoted §04b SPLIT work-item title: "…WIDENED from one edge to five" — historical, scoped to 04b, accurate |
| 8851 | inert-unrelated | prose: "…declared the same mutation for all five…" — reasoning about the 04b recipe's five edges |

No `five` hit other than the two pin-name references (L211, L8890) named a renamed corpse. All twelve residual hits are genuine unrelated counts.

`endpoints[0-9]` residual after edits: L216 `blocks-endpoints1` ✓, L8881 `refers-endpoints4`/`answers_to-endpoints0` ✓, L8888 `blocks-endpoints1` ✓ — all match `--collect-only`.
`_five_known_edges` residual: **NONE**.

## Recipe-scope (surface item, no action)
The commented mutation-proof recipe (PROOFS 1–5, ~L8777–8900) is packet 04b's, carries "EXECUTED 2026-07-28" receipts, and covers exactly the five 04b edges (blocks/briefed/to/refers/answers_to). It has no `member_of` leg. This is correct-by-scope, not stale: member_of is packet 60's edge and its proof lives with the wave-1 contract (test_keeps_schema.py). Flagged only so you can decide whether to cross-reference member_of's proof here; I did not add one (that is content, outside a comment-fix mandate).

## Verify
- `uv run ruff check loremaster/tests/test_blocks_edge.py` → **All checks passed!**
- `uv run pytest loremaster/tests/test_blocks_edge.py -n auto -q` → **220 passed in 8.73s**
- No test behavior changed (all four edits are inside comments/docstrings; diffstat 4 ins / 4 del).
- Did NOT touch the uncommitted contract files or any production code. Did NOT commit (lead commits).
