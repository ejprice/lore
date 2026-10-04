brief-base v18 read

**state:** done-with-deviations · **build commit:** `9c88779` (base `ae269dc`) · measured 2026-10-04
- **Deviations:**
  - (1) The final targeted run started at MemAvailable **16.0 GiB**, below the brief's 20 GiB floor. My gate printed the value but did not block. No other lore pytest was alive. It ran inside its 16G cgroup with no kill, and every earlier run started at 26+ GiB.
  - (2) The conditional note's `list-keys` command is `shlex.join`ed. The spec template has a bare `{email}`. The bytes are identical for any email that needs no quoting (§3 fork B).
- **Packages considered:** PEP 678 `BaseException.add_note` (stdlib, Python ≥3.11, used by `traceback.format_exception`). Verdict `replace`: it is the spec-named mechanism. Nothing was hand-rolled.
- **Odoo-20 portability:** n/a (no Odoo seam touched).
- **Reuse ledger:** 2 new symbols, both dispositioned (§6).
- **Graded:** n/a (builder report, not a verdict on someone else's artifact).
- **decisions-needed:** none blocking. Residuals R1–R3 in §5 are surfaced for the operator.
- **Pointers:** §1 change · §2 runs (RED/GREEN, before/after) · §3 forks · §4 mutation + sweep + gates · §5 residuals · §6 DRY ledger.

**Capability check:** every demand was met. I made one tool choice: no lore structure query was needed, because the spec named every file and symbol. I read them with awk/sed (grep/rg are hook-blocked, #473). I located 58's classifier by importing `test_exhaustion_fates` and running it, not by searching. No friction to file.

## 1. Change (`9c88779`, 4 files)
- **`principal_keys.py::PrincipalKeyStore.mint`:**
  - `answered = False`, then ONE `try` whose first statement is `with wrap_store_rejection(...): result = await self._query(...)`, followed by `answered = True`, `_as_rows(..., landed=True)`, the no-row raise and `return self._row_to_key(rows[0])`.
  - ONE handler: `except BaseException as error: note = self._mint_fault_note(...); if note is not None: error.add_note(note); raise`. The `try` is `mint`'s last statement.
- **`PrincipalKeyStore._mint_fault_note`** (new classmethod) builds both §13.5 item 5 wordings from `_revoke_command`, which is kept as the ONE helper:
  - `answered` → CERTAIN.
  - otherwise `isinstance(error, SurrealConnectionError)` → CONDITIONAL.
  - otherwise `None`. This is an allowlist of one class.
- **No-row raise:** `PrincipalKeyStoreError(f"key {name!r} for principal {email!r}: the mint answered no row")`, with no remedy.
- **Fold:**
  - `remedy=` is gone from `rows_of`, `_shape_fault` and `PrincipalKeyStore._as_rows`, along with `_LANDED_DEFAULT_REMEDY` and the `{remedy}` slot.
  - **`git diff 28395e0^ -- loremaster/loremaster/governed.py` is 0 lines**, so governed.py is byte-identical to its state before `28395e0`, and the landed text is byte-identical to that state's default.
  - `_as_rows` itself is kept, because other callers predate `28395e0`. Only its parameter was removed (fork C).
- **`principals.py::_fault_line`:** after the message and before the cause lines, one `f"{_NOTE_LINE_PREFIX}{scrub_text(note)}"` per `__notes__` entry, with `_NOTE_LINE_PREFIX = " ↳ "`.
- **58 STOP check:** run directly on the build, `test_exhaustion_fates.derived_fate(<mint site, line 441>)` gives **`passthrough`** (`in_domain=True`). There is no STOP and no fates row.

## 2. Runs (all `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300`)
- **Targeted set:** `test_am37_13_3_63c_i_a.py test_principal_keys_store.py test_principals_cli.py test_fail_closed_shapes_63c_13b.py test_exhaustion_fates.py test_engine_rejection_seam.py`.
- **BEFORE** (HEAD `ae269dc`, before any edit): `1 failed, 588 passed`.
- **AFTER** (`9c88779` tree): `1 failed, 618 passed`. That is +30 new pins and **0 newly failing**.
- **The one failure is identical in both runs:**
  - `test_exhaustion_fates.py::TestTheRegistryIsTheAdjudicationBothWays::test_every_row_names_a_ruled_classification_an_owner_and_evidence_that_HOLDS`, on `store/lease.py::get/create/release_if_held` `logs-error-class`.
  - The assertion line has the same md5 (`59d44e13…`) before and after.
  - It is owned by packet 58 (`_RULED_58`). It is not about mint.
- **RED** (test side first, production unedited): `25 failed, 114 passed` in `test_am37_13_3_63c_i_a.py`, each for the right reason:
  - `AttributeError: … has no attribute '__notes__'` on SurrealStoreError, PrincipalKeyStoreError, KeyError, TypeError and SurrealConnectionError;
  - `'remedy' in signature(...)` for rows_of, `_shape_fault` and `_as_rows`;
  - the template still carries the `remedy` field;
  - the window `Try` is absent, and 0 add_note handlers exist;
  - the `↳` line is missing.
  - On HEAD the pre-commit no-note pins and the live-UNIQUE pin PASS. That is correct: nothing noted them before.
- **GREEN:** `139 passed` for the file.
- **New pins (spec §13.5 item 6):**
  - **(a)** `TestTheMintWindowNotesTheRevokeRepair`. Pre-commit domain = the GENERATED store taxonomy (SurrealStoreError plus every `loremaster.store._txn` subclass, with a not-vacuous floor naming the six) plus `RuntimeError` and `asyncio.CancelledError` as allowlist controls. The "class unchanged" oracle is `wrap_store_rejection` itself. Post-commit covers 5 answer shapes × 2 email/name pairs, then each required column dropped (GENERATED from the full row; `KeyError` for id/principal/name with the note checked in `traceback.format_exception`, `PrincipalKeyStoreError` for created_at), then a `TypeError` defect. Also: a clean-mint control, ONE-helper sharing by monkeypatch, and every backticked command parsed through the real `lore-adm` parser.
  - **(b)** `TestALiveUniqueCollisionCarriesNoRevokeAdvice`. A minted `:18000` DB (`unique_database()`, dropped in `finally`), duplicate `(principal, name)` → `PrincipalKeyStoreError` caused by `TxnDomainRejectionError`. No link has notes, and no `revoke-key` appears in `_fault_line` + `traceback.format_exception` (fork D).
  - **(c)** `TestTheMintHasOneNoteHandlerOverTheWholeWindow`. Exactly one add_note handler: `BaseException`, last statement a bare `raise`, and that raise its only exit. The `Try` is `mint.body[-1]`. No `_query` lies before it, its first statement holds the one `_query`, and its last statement is a `Return`.
  - **(d)** `TestTheFaultLineRendersNotes`. Two notes (one carrying a 128-hex run, scrubbed) render between the message and the cause, with a no-notes control.
- **STOP-DUAL re-keys:**
  - `_LANDED_TEMPLATE` is back to the fixed text;
  - `test_the_template_has_exactly_one_remedy_slot` → `test_the_template_has_no_remedy_slot`;
  - the passed-remedy and remedy-without-landed pins → `test_no_reader_takes_a_remedy_any_more[rows_of|_shape_fault|_as_rows]`;
  - the `28395e0`/`b90bd4b` mint-message pins (`TestALandedThenFaultedMintNamesTheRevokeRemedy`) are replaced by (a): the remedy is asserted in `__notes__`, and its absence from the message is asserted.
  - A test-tree sweep for `_LANDED_DEFAULT_REMEDY|remedy=|vanished immediately|never shown, so revoke|may have been stored` finds only the two new DUAL-pin lines.

## 3. Forks (written down; my pick stated)
- **A. Where `wrap_store_rejection` sits.** Two readings:
  - (i) the wrap stays around the CREATE call alone, inside the `try`;
  - (ii) it encloses the whole `try`, literally "outside".
  - (ii) would CHANGE behaviour. The wrap catches every `SurrealStoreError` (`catch=(SurrealStoreError,)`), and `rows_of`'s post-commit shape fault IS a `SurrealStoreError`, so it would be retranslated into "could not mint key …", which is a false not-landed claim.
  - **Picked (i).** It honours "unchanged in behaviour". The handler then sees the wrap's translated `PrincipalKeyStoreError` for a pre-commit domain rejection, so classification uses the `answered` flag plus `isinstance(SurrealConnectionError)` (the wrap passes that class through untouched).
- **B. `list-keys` quoting:** I used `shlex.join([_CLI_PROG, "list-keys", "--email", email])` instead of the spec's literal `{email}`, for consistency with the shell-quoted revoke command. The output is identical for unquoted emails.
- **C. "DELETE … `PrincipalKeyStore._as_rows`":** I read it as deleting its `remedy=` parameter. The method predates `28395e0` and other callers use it.
- **D. Item 6 (b) "stderr":** I asserted over everything lore-adm can print for the error, its `_fault_line` and the full traceback. I did not use a CLI subprocess against the live store.

## 4. Mutation · `remedy` sweep · gates
- **Mutation** (`scripts/mutation_proof.py`, real tree, `cp -a` backup first): `error.add_note(note)` → `pass`, with 19 node ids declared from `--collect-only` before the run.
  - Result: **`PROOF HELD — the declared RED set fired EXACTLY`** (19 failed, 120 passed), diffed both ways.
  - The tool reported "tree restored byte-exact (md5 27d06f08…)", and `cmp` against the backup confirmed it: `RESTORED-BYTE-EXACT`.
- **Bare `remedy` sweep** (awk, case-insensitive, every `.py` under `loremaster/loremaster/`), with a verdict per hit. **None touch the deleted machinery.**
  - `config.py:489` prose, migration message → unrelated
  - `governed.py:973,1007,1012,1014,1020` `report_unmigrated_governed_rows`' derived remedy (§13.3 item 6) → unrelated
  - `messages.py:83,912` `AGENT_ROW_REMEDY` import/use → unrelated
  - `principals.py:1431,1606,1860,2400` docstring/comment prose → unrelated
  - `agent_existence.py:71,73,110,144,145,155,178,288,306,345,383` the unknown-identity family's `remedy` parameter and `AGENT_ROW_REMEDY` → unrelated
  - `tasks.py:308,2308` `_BLOCKER_REMEDY` → unrelated
  - `server.py:6361,6399` docstring prose → unrelated
- **`uv run ruff check .`:** `All checks passed!`
- **`pending_contract_gate.py --currency --legs typecheck,ruff`:**
  - The first run showed 6 typecheck RED_ORPHANED, all in my test file: two unused `type: ignore` and the `**dict` kwargs to the store constructors. I fixed them.
  - Re-run: `typecheck RED_ADJUDICATED — 83 residual(s), owned by: packet-58-contract`, `ruff GREEN`, **RED_ORPHANED 0** for typecheck/ruff.
  - `pytest NOT_RUN` is the known #533.

## 5. Residuals (surfaced, not acted on)
- **R1 — cancellation during the CREATE await.** An `asyncio.CancelledError` or `KeyboardInterrupt` that interrupts the await leaves the outcome as unknown as a transport fault does, yet gets NO note. The spec allowlists exactly one class, and I pinned it as specced (`CancelledError` → no note). Operator question: should `CancelledError` join the conditional class?
- **R2 — newline in a key name.** `shlex.join` keeps a literal newline inside its quotes, so `_fault_line` would print the note across two lines. One line could then look like a separate fault line. The same holds today for messages and cause lines, so this is not new to notes. The trigger is any render hardening of `_fault_line`.
- **R3 — `mint`'s docstring `Raises:`** does not mention the note. This is prose only.

## 6. DRY ledger
| new symbol | lookup | result | disposition |
|---|---|---|---|
| `PrincipalKeyStore._mint_fault_note` | read `principal_keys.py` around `mint` / `_revoke_command` (spec-named home) | `_revoke_command` exists; no note builder | **EXTENDED** `_revoke_command`'s home: the new builder calls it, so both wordings take the command from the ONE helper (pinned by monkeypatch) |
| `principals._NOTE_LINE_PREFIX` | read beside `_CAUSE_LINE_PREFIX` | no note prefix existed | **HAND-ROLLED** sibling constant, same idiom |
