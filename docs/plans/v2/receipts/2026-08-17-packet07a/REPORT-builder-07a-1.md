brief-base v14 read · brief project v7 read

# REPORT — builder-07a-1 — packet 07a GREEN phase (#128 per-item batch degradation)

## SUMMARY BLOCK
- receipt: brief-base v14 read · brief project v7 read
- state: **done** — #128 fix built, RED→GREEN proven (3 pins + full class 13 passed), ruff clean, `server.py` 0 mypy errors, full regression = **zero new failures vs a baseline-proven pre-existing set**, committed `43c4ab3` (server.py only).
- deviation 1: the working tree also carries `contract-07a-1`'s parallel citation revisions (contract doc, its report, the probe transcript, `probe_store_recovery_07a.py`) — EXPECTED per my brief. My commit stages **only** `loremaster/loremaster/server.py`.
- deviation 2 (pre-existing, NOT mine): `scripts/typecheck.sh` is RED with 102 errors — ALL in the auth/posture pending contract (see §4). This is a **RED_ADJUDICATED** gate (`gates.yaml`: `typecheck` → `adjudicated_by: pending-contracts`; every errored file/symbol is registered in `scripts/pending_contracts.yaml`), doing its job. `server.py` has **0** mypy errors. My change adds none.
- deviation 3 (trailer): my brief specified `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>` (matching recent commits), so the commit carries that string — but this agent runs on **Opus 4.8** (`opus48-worker`). Followed the brief literally (highest precedence + repo consistency); flag so the lead can amend to model-accurate attribution if that was the intent.
- committed: **`43c4ab3`** — `fix(07a): #128 per-item batch degradation …`, `server.py` only (+21 -1), one concern. Pre-commit hooks ran clean (no `--no-verify`).
- Packages considered: **none — no new mechanism.** The fix reuses the EXISTING per-item best-effort loop (`_resolve_or_acknowledge_many`), the EXISTING `loremaster.search._sanitise_line` sanitiser, and the EXISTING `loremaster.store._txn` exception hierarchy (`SurrealStoreError`, `TxnContentionExhaustedError`). No package decision arises.
- Reuse ledger: **none — no new reusable symbols introduced.** Two inline `except` clauses added to an existing method; sanitisation reuses `_sanitise_line` (already imported at server.py:213), matching the domain-trio clause immediately below.
- Graded: (builder, not a verdict-rendering report) · HEAD-at-report: `edbd72a` · work performed at HEAD `edbd72a`.
- decisions-needed: **none.** The fix shape, wording, and except-order were all ruled + adversary-cleared before I started; I reproduced the adversary's reference build for real.
- receipt POINTERS: the diff §1 · RED receipt §2 · GREEN receipt §3 · gates (ruff/mypy) §4 · full suite §5 · wording match §6 · except-order safety §7.

---

## 1. The change (diff)

`loremaster/loremaster/server.py` — TWO edits, both inside/above `AppContext._resolve_or_acknowledge_many` (the `_FINDING_BATCH_VERB` per-item loop):

**Edit A — import** (line ~216): widened the existing `_txn` import to add the two error types the seam must now distinguish.
```python
-from loremaster.store._txn import SurrealConnectionError
+from loremaster.store._txn import (
+    SurrealConnectionError,
+    SurrealStoreError,
+    TxnContentionExhaustedError,
+)
```

**Edit B — two new `except` clauses**, inserted AFTER `except SurrealConnectionError:` (abort-all) and BEFORE the domain-trio clause. Order is load-bearing: `SurrealConnectionError` (a `SurrealStoreError` subclass, abort-all) must be caught first; `TxnContentionExhaustedError` (also a `SurrealStoreError` subclass) must be caught before its `SurrealStoreError` superclass so it keeps its distinct wording.
```python
             except SurrealConnectionError:
                 aborted = True
                 outcome_lines.append(
                     f"- {ref_label} ABORTED — store connection lost; retry these"
                 )
                 continue
+            except TxnContentionExhaustedError:
+                # A healthy connection that lost a write-write race after exhausting
+                # its retry budget — the OPPOSITE of a dead socket, so CONTINUE (the
+                # next row can well succeed) and label it retryable. Caught before its
+                # ``SurrealStoreError`` superclass so it keeps this distinct wording.
+                outcome_lines.append(
+                    f"- {ref_label} FAILED — store contention, safe to retry this item"
+                )
+                continue
+            except SurrealStoreError as error:
+                # Any other non-connection store rejection: per-item FAILED, CONTINUE
+                # (connection is healthy). Caught AFTER SurrealConnectionError (a sibling
+                # subclass that must still abort-all) — order load-bearing. NOT labelled
+                # "safe to retry": a plain store rejection is not known-retryable.
+                outcome_lines.append(f"- {ref_label} FAILED — {_sanitise_line(str(error))}")
+                continue
             except (_FindingNotFoundError, _FindingIllegalTransitionError, ValueError) as error:
```

**Error hierarchy confirmed** (`_txn.py`): `SurrealStoreError(RuntimeError)` is the base (L116); `SurrealConnectionError(SurrealStoreError)` (L120) and `TxnContentionExhaustedError(SurrealStoreError)` (L156) are siblings under it. The clause ordering respects Python's first-match-wins MRO.

This is exactly the shape the contract author proved satisfiable and the adversary cleared as the REF build (`REPORT-adversary-07a-1.md` §RR: REF → `3 passed`; W1/W2/W6 each caught). I reproduced it for real and kept it.

---

## 2. RED receipt (before the fix, at HEAD edbd72a + the concurrent RED contract)

`uv run pytest "loremaster/tests/test_mcp_server.py::TestResolveManyAcknowledgeManyDispatch" -q`:
```
3 failed, 10 passed in 17.01s
FAILED ...::test_a_contended_item_FAILS_per_item_without_aborting_the_rest
FAILED ...::test_a_plain_store_error_item_FAILS_per_item_without_aborting_the_rest
FAILED ...::test_acknowledge_many_also_degrades_per_item_on_contention
```
RED **for the right reason**: the injected `TxnContentionExhaustedError` / `SurrealStoreError` propagates out of `_resolve_or_acknowledge_many` (traceback: `findings` server.py:3750 → `_resolve_or_acknowledge_many` server.py:3924 → `raise self._error`) and RAISES the whole `findings()` batch call — the exact #128 defect, not an import/fixture error. The 10 co-resident pins (incl. the existing `test_connection_loss_aborts_remaining_as_render_not_raise` and `test_an_illegal_item_fails_without_aborting_the_rest`) were already GREEN.

(Note: the first RED run errored 21× on `ConnectionRefusedError ('127.0.0.1', 18000)` — the spike-surreal TEST store was momentarily down; `systemctl --user is-active spike-surreal.service` → `active`, container came back up, re-ran clean. Not a test defect.)

---

## 3. GREEN receipt (after the fix)

`uv run pytest "loremaster/tests/test_mcp_server.py::TestResolveManyAcknowledgeManyDispatch" -q`:
```
13 passed in 17.77s
```
All 13: the 3 target #128 pins now GREEN, and every pre-existing pin in the class (abort-on-connection-loss, illegal-item-continues, hostile-ref sanitiser, empty/over-cap validation, duplicate-refs, all-succeed, acknowledge-verb) still GREEN. The except-order change did not regress the connection-abort behaviour.

---

## 4. Gates

- **ruff:** `uv run ruff check .` → `All checks passed!` (clean, whole repo).
- **mypy (`scripts/typecheck.sh`):** RED — `Found 102 errors in 8 files` (loremaster leg) + lorerunes leg. **`server.py`: 0 errors** (`grep -c 'loremaster/loremaster/server.py.*error'` → 0). Every errored file is auth/posture/roster/permission/lorerunes test infra referencing yet-unbuilt symbols (`loremaster.config.PostureConfigError`, `resolve_posture`, `lorerunes.Posture`, `SCOPE_READ`, …). These are the **auth/posture pending contract** — registered file-by-file, symbol-by-symbol in `scripts/pending_contracts.yaml`, and `gates.yaml` marks the `typecheck` gate `adjudicated_by: pending-contracts`. So this red is **RED_ADJUDICATED**, an owned bound (packet 39/45 territory), exactly the state CLAUDE.md's gate-currency law describes as "doing its job." A `server.py`-only diff cannot introduce errors in those unrelated modules; it introduces none. (The `pending_contract_gate.py --currency` tool timed out at 2 min because it re-runs the full mypy set; I classified via the manifests directly instead.)

---

## 5. Full regression (`uv run pytest -n auto`)

`uv run pytest -n auto -p no:cacheprovider -q --continue-on-collection-errors` (whole repo, 3:49):
```
451 failed, 9878 passed, 51 skipped, 3 xfailed, 8 warnings, 135 errors in 229.19s
```
**My 3 #128 pins are in the 9878 passed** (the whole `TestResolveManyAcknowledgeManyDispatch` class passes — §3). **Every one of the 451 failures + 135 errors is PRE-EXISTING**, reconciled exactly:

| bucket | count | classification |
|---|---|---|
| auth/posture pending contract (10 files: `test_auth_composition`, `test_google_token_verifier`, `test_posture`, `test_hosted_readonly_posture`, `test_allowlist_roster`, `test_roster_parser`, `test_auth`, `test_email_normalisation`, `test_auth_identity_seam`, `test_permission_resolver_seam`) | 446 failed | **RED_ADJUDICATED** — the pending contract registered in `scripts/pending_contracts.yaml` (§4). Includes the `HostedToolRefusedError`/`PermissionFilteredToolError` ImportErrors (pending server.py symbols — NOT removed by me). |
| outlier failures: `test_secret_typing` (2), `test_surreal_harness` (1), `test_comms_footer` (1), `test_ast_reach_helpers` (1) | 5 failed | pre-existing (see baseline proof below) |
| outlier errors: `test_message_ledger` (130), `test_comms_footer` (5) | 135 errors | pre-existing — an autouse teardown guard (`conftest.py:212` `_no_sdk_call_escapes_the_retry_driver`) tripping on a multi-statement bare `.query()` at `store/_txn.py:1207 in _attempt()` (#124/#144), on `[real]` live-store variants. A **store-layer** path, disjoint from my findings-batch change. |
| **total** | **451 failed + 135 errors** | reconciles: 446+5 = 451 failed; 130+5 = 135 errors |

**Baseline proof (receipts, not assertion).** Because 140 of these (the two outlier buckets) are NOT in the pending-contract registry, I proved they pre-date my change: backed up my `server.py` (`cp -a` → `/tmp/server.py.mine`), restored HEAD's (`git show HEAD:…server.py > …server.py`; provenance asserted `diff -q` == HEAD), ran the 5 outlier files, then restored mine byte-exact (`diff -q` == `/tmp/server.py.mine`). Baseline result:
```
5 failed, 660 passed, 21 skipped, 135 errors in 24.27s
```
**Byte-identical** to the outliers' counts in the full run (5 failed, 135 errors) — so they are present WITHOUT my change. My change introduces **zero** new failures. (This is the sanctioned content-backup mutation-proof pattern; no git state was staged/committed/reverted — the working file was swapped and restored, and `git diff --stat` confirmed my 22-line change back in place.)

⚠ **FLAG for the operator/lead (scope law — surfaced, not chased):** the 140 outlier failures/errors (`test_message_ledger` 130E, `test_comms_footer` 1F+5E, `test_secret_typing` 2F, `test_surreal_harness` 1F, `test_ast_reach_helpers` 1F) are pre-existing at HEAD `edbd72a` but are **NOT** covered by the auth/posture pending-contract registry. The 135 errors are the `store/_txn.py:1207` multi-statement `.query()` guard firing on `[real]` live-store tests (#124/#144 territory). These are outside packet 07a's scope and outside my writable set; I did not investigate their root cause. They may be a store-version artifact (spike-surreal drifted to 3.2.4, #336) or a genuine unregistered regression — worth a look.

---

## 6. Exact wording match (operator-ruled line)

Ruled line (`RULING-fork-a.md`, contract §A): `FAILED — store contention, safe to retry this item`.
My code emits `f"- {ref_label} FAILED — store contention, safe to retry this item"` (`ref_label` renders `#{number}` for a numeric ref). The pins assert `lines[2] == f"- #{contended.number} FAILED — store contention, safe to retry this item"` on BOTH `resolve_many` and `acknowledge_many` and both are GREEN — byte-exact match. The plain-`SurrealStoreError` clause emits the generic `FAILED — {_sanitise_line(str(error))}`, and its pin asserts `"safe to retry this item" not in lines[2]` (GREEN) — the "safe to retry" claim is reserved for contention only.

---

## 7. Except-order safety (adversary W6)

The adversary's W6 mutation (`REPORT-adversary-07a-1.md` §RR/§FD) proved that inserting the store-error clauses BEFORE `except SurrealConnectionError` reddens `test_connection_loss_aborts_remaining_as_render_not_raise` (`SurrealConnectionError` would be swallowed by the `SurrealStoreError` base → the connection-loss case would no longer abort-all). My insertion is strictly AFTER that clause; the pin stays GREEN (in the 13-passed run §3), confirming I did not reproduce W6.

---

## 8. What ends here / next
This ends the GREEN phase for #128. Production change is `server.py`-only, committed as one concern at **`43c4ab3`**. The working tree still carries `contract-07a-1`'s parallel citation revisions (contract doc / its report / probe transcript / `probe_store_recovery_07a.py`) — untouched by me — and this untracked report. Next per this repo's cycle: an independent cold-audit agent re-verifies (builder ≠ grader). I did NOT deploy.

**Handoff flags for the lead:**
1. The 140 non-pending-contract pre-existing failures/errors (§5 ⚠) — outside 07a scope, surfaced not chased.
2. The co-author trailer says "Claude Sonnet 5" per the brief; this agent is Opus 4.8 (deviation 3).
