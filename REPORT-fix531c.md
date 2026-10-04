brief-base v18 read

- **State:** done.
- **Deviations:**
  - I did not `register` or `heartbeat` on `lore_comms`. The brief named one native line as the only message, and the deadline was 30 minutes.
  - The idle-gate contract file was written to `/tmp/claude-idle-gate-lore/fix531c.contract`. The session-id prefix was unknown, so the file name is the agent name only.
- **Packages considered:** `shlex.join` (stdlib), REUSED from `28395e0`. No new mechanism.
- **Odoo-20 portability:** n/a, no Odoo seam touched.
- **Reuse ledger:** 1 new symbol, `PrincipalKeyStore._revoke_command`. It EXTENDS `28395e0`'s inline construction by lifting it into a helper that both sites call. See §4.
- **Graded:** n/a, no verdict on someone else's artifact.
- **Decisions needed:** §5 item 1 is a same-class sibling that this fix does not cover. Operator call.
- **Receipt pointers:** commit `b90bd4b` · §2 runs · §3 gates · §4 sharing proof · §5 residuals.

## 1. Change (`b90bd4b`, two files)
- `loremaster/loremaster/principal_keys.py`:
  - New `PrincipalKeyStore._revoke_command(*, email, name) -> str`. It returns `shlex.join([_CLI_PROG, "revoke-key", "--email", email, "--name", name])` and is the ONE construction of the command.
  - `mint`'s wrong-shape remedy (`28395e0`) now calls the helper.
  - `mint`'s `if not rows:` branch still raises `PrincipalKeyStoreError`. Its new text:
    `key {name!r} for principal {email!r}: the mint answered no row, so the key may have been stored but its secret was never shown — revoke it (`<command>`) if `list-keys` shows it, then mint a new key`.
- `loremaster/tests/test_am37_13_3_63c_i_a.py`, class `TestALandedThenFaultedMintNamesTheRevokeRemedy`:
  - Extracted helpers: `_assert_served_revoke_parses`, which parses the first backticked command through the real `p_module.build_parser()`, and `_store_whose_create_answers`, which is `28395e0`'s fake: `_query` asserts the statement is a CREATE and counts landing (#194).
  - The existing wrong-shape test now calls `_assert_served_revoke_parses`. Its assertions are unchanged.
  - New `test_a_create_answering_no_row_names_the_same_revoke_repair`, with plain and needs-quoting cases. It asserts:
    - `PrincipalKeyStoreError` is raised and the CREATE landed once;
    - the key name and the exact `shlex.join` revoke command are in the text;
    - "never shown", "list-keys" and "mint a new" are in the text;
    - the command parses as `revoke-key` with that email and name.
  - New `test_both_mint_faults_take_the_revoke_command_from_the_one_helper`, with wrong-shape and no-row cases. See §4.

## 2. Runs (all measured 2026-10-04)
Every run waited for MemAvailable ≥ 20 GiB (25.3–26.7 GiB) with no lore pytest alive; the only other pytest was mobile-pricepaper-smoke. Each ran under `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300 -q -p no:cacheprovider`. Target set: `tests/test_am37_13_3_63c_i_a.py tests/test_principal_keys_store.py tests/test_principals_cli.py`. #486's uncommitted WIP in other test files was present for every run and never staged.

| run | tree | result |
|---|---|---|
| baseline | HEAD `ba0b661` | **351 passed** in 16.71s, exit 0 |
| RED | new pins, production unchanged (`-k TestALandedThenFaultedMintNamesTheRevokeRemedy`) | **4 failed, 8 passed**, exit 1 |
| GREEN | after the production edit | **355 passed** in 16.85s, exit 0 |
| GREEN (final) | after the E501 fixes | **355 passed** in 18.32s, exit 0 |

The RED `E` lines show the reason for each failure:
- 2× `the revoke remedy for 'laptop'|'work laptop' is missing: key … vanished immediately after it was created`;
- 2× `AttributeError: <class 'loremaster.principal_keys.PrincipalKeyStore'> has no attribute '_revoke_command'`.

355 − 351 = 4 new tests, with 0 newly failing.

## 3. Gates
- `uv run ruff check .`: `All checks passed!`. Two of my own E501 lines were fixed before the commit.
- `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff`:
  - typecheck: `RED_ADJUDICATED` (83 residuals, owned by packet-58 and packet-64b-i). Neither touched file appears in `scripts/pending_contracts.yaml`, so none of the 83 is mine.
  - ruff: `GREEN`.
  - pytest: `NOT_RUN`. The `CURRENCY: FAIL — claimed but never run: pytest` line is known (#533).
  - **RED_ORPHANED: 0.**

## 4. Sharing proof (ONE IMPLEMENTATION)
- **Instrument.** `test_both_mint_faults_take_the_revoke_command_from_the_one_helper` monkeypatches `PrincipalKeyStore._revoke_command` to return a sentinel. Each fault site must then serve `` `SENTINEL-531c revoke command` ``, must not contain `revoke-key`, and must call the helper exactly once with `(email, name)`.
- **Mutation control.** I backed up `principal_keys.py` with `cp -a` to my scratchpad, then inlined a private `shlex.join([...])` copy into the no-row branch. An awk print confirmed the mutation landed.
  - Result: **1 failed, 11 passed**. Exactly the declared `…one_helper[no-row]` reddened.
  - I restored the file from the backup, and `cmp` reported `RESTORED-BYTE-EXACT`.
  - The mutation was made in the real tree, so there is no provenance question.

## 5. Residuals (surfaced, not acted on)
1. **Same class, still open: the `_row_to_key(rows[0])` fault after a landed CREATE.**
   - *Lifted property:* every `mint` fault raised after the CREATE may have committed names the revoke repair.
   - *Siblings tried:* wrong shape (`28395e0`) and no row (`b90bd4b`).
   - *Siblings not tried:*
     - a row missing `created_at` (raises `PrincipalKeyStoreError`) or missing `id`/`principal`/`name` (bare `KeyError`) in `_row_to_key`. The key landed, the secret was never shown, and there is no remedy.
     - a transport fault raised from `_query` after the engine committed, which passes through `wrap_store_rejection` untouched. Whether it landed is unknown.

   A state-level fix would be one `try` around everything after the CREATE in `mint` that attaches `_revoke_command`. Operator call; I stayed within the brief's scope.
2. The sweep for "vanished immediately" also found the same wording in `findings.py`, `messages.py`, `principals.py` (create), `agents.py` (×3) and `briefs.py`. None of those leaves an unshown secret, so the default "verify" stance applies. These are flagged, not changed.
