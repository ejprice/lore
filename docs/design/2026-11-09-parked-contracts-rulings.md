# Parked contract reds: deselected by default — rulings (2026-11-09)

- **State:** contract written (`scripts/test_parked_contracts.py`, 23 tests, RED@HEAD `99389cd`); lean pipeline.
- **Lore task:** `7f68cbcf5e274cbfabb1de0fbd182e42`.
- **Operator rulings (2026-11-09):** decision 3 — skip parked failing contract tests by default via
  `scripts/pending_contracts.yaml`; lean pipeline (one contract author, ONE adversary round, one builder,
  one cold audit).

## Spec (from the operator's ruling and the lead's brief)
- **S1.** A default run deselects every `bounds[].files[].red_nodeids` node of every bound without
  `active: true`; exact node-id membership (the gate's R31 rule).
- **S2.** One summary line names the count, the involved entry ids and `--run-parked`; pytest's native
  deselected count includes them (non-xdist runs; see D2).
- **S3.** `--run-parked` includes every parked node.
- **S4.** A bound with `active: true` is never deselected.
- **S5.** Registry absent / unreadable / invalid → nothing deselected, one warning line naming the
  problem, the hook never makes pytest exit non-zero.
- **S6.** The `pytest` gate in `scripts/gates.yaml` carries `--run-parked` (so `pending_contract_gate.py`
  and `wave_gate.py` observe every registered red).
- **S7.** `PendingBound` accepts an optional STRICT boolean `active` (default false).
- **S8.** The hook reads the registry through `PendingContractRegistry`, never a second YAML parse.
- **Lead ruling (in the brief):** naming a parked node on the command line does not exempt it.

## Lead rulings on the contract author's D1–D7
| # | Question | Ruling |
|---|---|---|
| D1 | Registry location | `<rootdir>/scripts/pending_contracts.yaml` (`config.rootpath`): node ids are rootdir-relative, so the registry naming them is the rootdir's. In this repo it equals `DEFAULT_REGISTRY_PATH`. |
| D2 | Native deselected count under xdist | Not required. pytest-xdist reports no deselected count under `-n` for any deselection (measured by the author); the S2 line carries the count. Non-xdist runs must include it natively. |
| D3 | "Involved" entries | Entries with at least one node deselected in THIS run. |
| D4 | `--collect-only` hides parked nodes | Accepted, so the gate's advice must match: every place the gate tells an author to confirm a node with `--collect-only` says `--collect-only --run-parked`. The builder changes that advice; the audit checks it. |
| D5 | A node listed under both an active and a non-active bound | `active` wins: the node runs. Needs a pin (routed to the adversary round). |
| D6 | `active: null` | `RegistryError`, like any other non-boolean. Needs a pin (routed to the adversary round). |
| D7 | Naming only parked nodes | pytest's native exit 5 (no tests ran) is accepted; not pinned. |

## Reported by the author, not part of this packet
- `pending_contract_gate.py --currency --legs typecheck,ruff` exits 1 ("CURRENCY: FAIL") because the
  pytest leg is NOT_RUN under `--legs`, so its exit code cannot serve as the per-round signal lore
  `CLAUDE.md` § Quality gates describes. Unverified by the lead; to be checked and ledgered separately.
