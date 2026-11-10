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

## Adversary round 1 (adversary-parked-1, graded 54c7595): INSUFFICIENT — lead rulings for the ONE fix round
The operator's lean pipeline allows one adversary round, so this fix round is not re-graded; the cold
audit inherits every residual below.
| # | Finding | Ruling |
|---|---|---|
| A1 | W15 survives: a node under an active AND a non-active bound is deselected | Add the adversary's proven D5 pin. The parked set is computed in ONE place, a `PendingContractRegistry` method, so D5 lives with the model. |
| A2 | W12 survives: `active: null` accepted | Add the D6 pin. |
| A3 | W21 survives: "involved" read from collected files | Add the D3 pin: involvement comes from the deselected items only. |
| A4 | W22 survives: registry read from the cwd | Add the D1 pin (run from a subdirectory; the rootdir's registry still rules). |
| A5 | W23 survives: broken-registry warning lost under xdist | Add the S5-under-xdist pin: one warning line from the controller, via `workeroutput`. |
| A6 | D4 advice unpinned | Tighten `scripts/test_pending_contract_gate_f6.py::test_D2_a_CLASS_scoped_run_judges_only_what_it_SELECTED` to require `--collect-only --run-parked`. |
| A7 | Satisfiability blocker: a correct build reddens `test_gated_ground.py`'s two live-tree pins (every node of three registered files is parked, so its collector sees them as ungated); `--run-parked` in that collector breaks 130 of its tests (flag unknown in foreign trees) | Fork (a): the hook registers as a plugin named `lore-parked-contracts`; `-p no:lore-parked-contracts` disables it and is harmless in a tree without it. Every repo tool that launches pytest to MEASURE the tree passes it: `scripts/gated_ground.py`'s collector and `scripts/concurrent_wire_acceptance.py`'s `--collect-only`. Pin: with `-p no:lore-parked-contracts` a wholly parked file collects every node; and the existing `test_gated_ground.py` suite stays green on the build. Tools that RUN a contract (`mutation_proof.py`, `wrong_builds.py`, `c3_wrongbuild_driver.py`) fail loud on a parked contract, not silently: callers pass `--run-parked`; not changed here. |
| A8 | `-k` and parking both exclude a node: who owns it in the S2 count | The hook runs after other deselection (`trylast`) and counts only the items it removes itself; consistent with the pinned `test_summary_count_excludes_nodes_deselected_by_other_means`. |
| A9 | The contract's own reds are not registered | The author registers them in `scripts/pending_contracts.yaml` as one new bound `parked-deselection-contract` (no `active` key — HEAD rejects it); the builder deletes the entry with the fix, per the registry's self-destruct rule. |
| A10 | W24 survives (model validates, ids/`active` read from raw YAML): no visible effect today | Residual: the cold audit runs mutation M2 (`active` default True) on the real build; every deselection pin must redden. |
| A11 | Second worker-report copy: `loremaster/tests/conftest.py` already ships #486's leak report through `workeroutput` / `pytest_testnodedown` | The builder extracts ONE helper both use, or escalates with a reason; it does not write a second copy. |
| A12 | The author's package survey is in no committed artifact | The author adds it to this file in the fix round. |
