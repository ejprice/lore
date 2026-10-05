brief-base v18 read
- **Deviations:** none to the edits. The currency command exits 1 because `pytest` is NOT_RUN under `--legs` (see Currency below). Capability: grep on the main checkout is blocked by a hook, so I used lore, Read and awk instead (no structure question was routed around).
- **Packages considered:** none. No mechanism was specified. **Odoo-20 portability:** n/a, no Odoo seam was touched. **Reuse ledger:** none.
- **Graded:** n/a (author). Measured 2026-10-05 against the working tree at HEAD `f7ecbce` plus the uncommitted q1b build (`_txn.py` md5 `86f9a898…`).
- **Decisions needed:** F-1 and F-2 below.

**Hunks** (diffed against the pre-edit `cp` backups; each is one line):
1. `test_fixwave_a28c_63c_i_a.py::…::test_am35_2_4_mutating_the_mapping_helper_moves_every_identity_leg`: `def _base_only(error_class: str, message: str, *, kind: str | None = None) -> Any:`
2. `test_mint_kind_carveout_q1b.py::_proven_no_key`: `predicate = _txn_module.proven_no_key`, replacing `getattr(...)  # noqa: B009`. No import went unused, because `_txn_module` and `Callable` are still referenced. Ruff is GREEN.

**Runs** (all through the WAITING gate: MemAvailable ≥ 20 GiB, no other pytest by process name, `MemoryMax=16G`, `-n 8 --timeout=300`):
- Both files: **502 passed in 51.12s**, exit 0. This includes all 4 `test_am35_2_4…` cells: `{record-id,unique-index}-collision × {run_query,execute_transaction}`.
- **Mutation** (`scripts/mutation_proof.py`). The two RED ids were declared before the run: the `[record-id-collision-run_query]` and `[unique-index-collision-run_query]` cells.
  - The mutation replaced `_raise_attempt_failure`'s `raise _domain_rejection_error(...)` with an inline clone of the helper's 3-way class branch. That is a bypass that still builds the correct class, so the CONTROL leg stays green and the RED has to come from the mutation leg.
  - Result: **PROOF HELD.** Exactly the declared set went RED (`2 failed, 2 passed`), failing at `assert calls` ("the patched mapping helper was never called"). The two `execute_transaction` cells stayed green as predicted, because they raise from `_run_verified_transaction`'s separate site.
  - The tool restored `_txn.py` byte-exact (`86f9a898fa486ad7e7c8b32080e8134c`, the same as my backup).
  - The brief's literal suggestion (build `TxnDomainRejectionError(...)` directly) would have gone RED on the CONTROL leg instead, which proves less.

**Currency** (`--currency --legs typecheck,ruff`):
- typecheck is **RED_ADJUDICATED**: 83 residuals, all owned by packet-58-contract and packet-64b-i-contract. The STOP-2 `no-any-return` is no longer among the unowned ones.
- ruff is **GREEN**.
- **RED_ORPHANED is 0 over the legs that ran.** But the tool prints `pytest NOT_RUN … ORPHAN` and `CURRENCY: FAIL`, exit 1. So `--legs typecheck,ruff` does not return a clean result, even though CLAUDE.md sanctions it as the per-round check. This is friction in the tool; see F-3.

**Flags:**
- **F-1 (role boundary, lead to rule):** `test_mint_kind_carveout_q1b.py` was already modified versus HEAD before I edited it. Its `if TYPE_CHECKING: from loremaster.store._txn import proven_no_key` owner-anchor block and the `TYPE_CHECKING` import were removed. The likely author is implement-mint-q1, and an implementer editing tests is a forbidden transfer (brief-base §2). I left it as I found it.
- **F-2:** `_proven_no_key`'s docstring still reads "STUB EXPECTATION … RED by AttributeError". With the direct read it is still true pre-build, but stale post-build. I did not edit it because the brief allowed exactly two edits.
- **F-3:** `pending_contract_gate.py --legs` should report a deselected leg as deselected, not as ORPHAN/FAIL. As things stand, every per-round currency check exits 1.

**Final md5s:** `test_fixwave_a28c_63c_i_a.py` `48e51b1ecde3ffa1df705049af4e90dd` · `test_mint_kind_carveout_q1b.py` `c7cd0b34ed32423df6e3c3223ea45496`
- **State:** done
