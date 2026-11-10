brief-base v27 read
brief project v7 read

State: done
Deviations: none
Packages considered: none — no mechanism specified (a deletion of a branch)
Odoo-20 portability: n/a — no Odoo seam touched
Reuse ledger: none (no new symbols)
Decisions-needed: one — see FLAG-1 (registry entry for the #615 pin must now be deleted; not in my writable set)
Pointers: ## Gate receipts · ## Removed-behavior inventory · ## PROSE-RESIDUALS · ## FLAGS

Routing: test runs inline (cgroup-capped shell, small, I read the count line myself); no sweeps large enough to fan out. Fan-out: haiku 0 · sonnet 0 · peak 0.

## Change
`scripts/pending_contract_gate.py::PendingContractGate.partition_pytest` — removed `file_level = any(not entry.red_nodeids …)`; a failure is EXPECTED iff some entry for its file lists its node id. Docstring rewritten to state per-node-only adjudication.

`partition_mypy` read (unchanged): adjudicates by `entry.admits(error)` over `entries_for(error.path)`; no reference to `red_nodeids`. The typecheck leg (`missing_symbols`) is separate and untouched.

## Failing test
`scripts/test_pending_contract_gate_f6.py::test_615_an_entry_with_no_red_nodeids_owns_NO_pytest_red` — RED at base (per brief: 1 failed / 108 passed); after: 109 passed, 0 failed (both gate test files, node-id total unchanged from author's fallback-removed reference count of 109).

## Gate receipts
| gate | command | log | EXIT | count | TREE |
|---|---|---|---|---|---|
| gate tests | `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run pytest scripts/test_pending_contract_gate.py scripts/test_pending_contract_gate_f6.py -q -n 4 -p no:cacheprovider` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/fix615/pytest.log | 0 | 109 passed | 6ee81a6e…7e817 |
| verify-registry | `uv run python scripts/pending_contract_gate.py --verify-registry` | …/fix615/registry.log | 0 | self-destruct: 19 import-checked absent · 46 UNCHECKED | 6ee81a6e…7e817 |
| currency typecheck,ruff | `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` | …/fix615/currency.log | 1 | typecheck RED_ADJUDICATED (84), ruff GREEN, pytest NOT_RUN (only reason for EXIT=1: `--legs` excludes the manifest's pytest gate; RED_ORPHANED count 0) | 6ee81a6e…7e817 |
| ruff | `uv run ruff check scripts/pending_contract_gate.py` | stdout only | 0 | All checks passed! | — |

Caveat: the currency EXIT=1 is the NOT_RUN claim of the pytest gate under `--legs typecheck,ruff`; I did not measure EXIT at base to confirm that is its baseline value (LOW-MEDIUM confidence it is the normal shape). The tree has DIRTY_FILES=3: mine, `scripts/probe_hub_txn_58.py` (not mine, someone else's edit), and untracked `REPORT-adversary-58-r5.md`.

## Removed-behavior inventory
| item | verdict |
|---|---|
| file-level fallback in `partition_pytest` (an entry with no `red_nodeids` made every pytest failure in its file EXPECTED) | dropped-deliberately — amendment 15 §10.2 / #615: typing claim never becomes pytest ownership; premise ("last file-level entry converts") met by r5.1 steps 1/3(a). No other behavior touched. |

## DRY ledger
No new symbols. (Deletion only.)

## PROSE-RESIDUALS (sweep: grep for `file-level|file level|per file|per-file|whole file|any entry|pytest red` over the gate, pending_contracts.yaml, gates.yaml — a non-symbol textual seam; hits: 12)
- scripts/pending_contract_gate.py `partition_pytest` docstring — described old fallback → FIXED.
- gate.py ~38 "narrowed per file AND per symbol" — about mypy safe set → unrelated, kept.
- gate.py ~44 "per-file, per-code allowance" — unsymboled mypy codes → unrelated, kept.
- gate.py ~684, ~733, ~1683-1684 — unsymboled/derive docs → unrelated, kept.
- gate.py ~1260 comment "EXPECTED iff ANY entry registered for the path admits it" — in `partition_mypy` → correct, kept.
- pending_contracts.yaml 43-44 "per-file missing_symbols / unsymboled_codes" — typecheck → unrelated, kept.
- pending_contracts.yaml 94 "this bound OWNS every packet-58 pytest RED" — true via listed node ids → kept.
- pending_contracts.yaml 422-423 (comment above the #615 pin entry) "RED until a builder removes the file-level fallback" → now STALE; goes away with the entry (FLAG-1). Entries are not mine to edit.
- gates.yaml — no hits.
- Test file f6 header lines 34-35 and ~122 ("file-level owner of its pytest reds today") — test file, not editable; line 34-35 reads "contract-ahead" about #615 and is now stale; line ~122 is a rationale string in a fixture → flagged to lead, not edited.

## FLAGS
- FLAG-1: `scripts/pending_contracts.yaml` lines ~421-426 register the #615 pin as an adjudicated red (`red_nodeids: …test_615_an_entry_with_no_red_nodeids_owns_NO_pytest_red`). It is green now, so a full/pytest currency run will emit `SELF-DESTRUCT: adjudicated red … is green — delete it with the fix.` Exact edit: delete those lines (the comment at 421-423, the `- path: scripts/test_pending_contract_gate_f6.py` entry and its one `red_nodeids` id). I did not run the pytest leg of currency (full-suite) and did not edit entries per brief.
- FLAG-2: `scripts/probe_hub_txn_58.py` shows as modified in the tree; not mine.
