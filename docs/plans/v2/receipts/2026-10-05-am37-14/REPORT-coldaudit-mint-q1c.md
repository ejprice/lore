brief-base v18 read · brief project v7 read

# REPORT — coldaudit-mint-q1c: cold REFUTE audit of the am-37 §15.3 + §15.4 (Q1c) build

## SUMMARY
- **Verdict: GO-with-residuals.** Measured 2026-10-05, 15:24–16:04Z. The build conforms to §15.3 and §15.4.
  - All 4 of my mutations reddened their declared sets; 0 survivors.
  - The full suite gives **CURRENCY PASS**: typecheck 83 owned, ruff GREEN, pytest 530 owned (packet-58 / packet-64b-i), RED_ORPHANED 0.
  - The 530 failure ids are **identical** at HEAD and on the build.
  - Two LOW residuals are spec-level and pre-existing. Neither was introduced by this build.
- Deviations: **D-1.** The full suite ran **twice**. My first run forwarded `--junitxml`, which overrode the gate's own junit path, and the gate refused with "BROKEN INSTRUMENT … no measurement" (exit 2). I re-ran it exactly as briefed. That run's junit (13416/530/70) is the census source, and it was taken on the same build bytes.
- Packages considered: none — no mechanism specified (audit only).
- Odoo-20 portability: n/a — no Odoo seam touched.
- Reuse ledger: none (no symbols written).
- Graded: working tree over `7125e67` (patch md5 `e00b0537…`, byte-identical to `git diff`) · HEAD-at-report: `7125e67` · SAME.
- Decisions-needed:
  - **R-1** (whether to namespace the allowlist key): lead/sidecar, optional.
  - **R-2** (whether detail kinds under an allowlisted top kind need per-detail adjudication): lead/sidecar, optional.
- Pointers: census §1 · conformance §2 · mutations §3 · full suite §4 · findings §5 · md5s §6.

## §1 Contract-blind census (built before reading the contract or reports)
Instrument: `census.py` (pasted verbatim below). It parses every shape with the SDK's own `parse_query_error` and drives it through the REAL single-statement seam (`q1b._through_the_seam`, i.e. `_raise_attempt_failure`). It then evaluates `proven_no_key` on the build and compares the result with the Q1b deny-list logic, reconstructed from the patch's `-` lines. `loremaster.__file__` = the real tree.

Domain: `ErrorKind ∪ KIND_TO_CLASS` top kinds, `Query:{QueryDetailKind}`, every non-Query `*DetailKind` under its top kind, the §15.3 unenumerated cells, and namespace-collision probes.

| shape (top:detail) | raised as | typed kind | build | Q1b |
|---|---|---|---|---|
| Validation / Thrown / AlreadyExists / NotFound / Configuration (bare and every SDK detail) | TxnDomainRejectionError, unspecified | top kind | PROVEN | PROVEN |
| Query:NotExecuted | TxnDomainRejectionError | NotExecuted | PROVEN | PROVEN |
| Internal, Serialization(:*), Query (bare), Query:TimedOut, Query:Cancelled | TxnDomainRejectionError | as named | unknown | unknown |
| NotAllowed(:*), Connection(:*) | SurrealConnectionError (transport) | — | unknown | unknown |
| **Transaction, Query:Aborted, FutureKind, Query:FutureDetailKind** (and the synthetic top `Auth:*`) | TxnDomainRejectionError | as named | **unknown** | PROVEN ← the R-1 fix |
| kind-less unspecified; bare SurrealStoreError; ValueError | — | None | unknown | unknown |
| Query:Validation, Query:NotFound, top `NotExecuted` (collision probes) | TxnDomainRejectionError | Validation / NotFound / NotExecuted | PROVEN | PROVEN → **R-1** |

**Delta.** The build flips exactly the unenumerated kinds from PROVEN to unknown, and nothing else. The classified half (`error_class != unspecified` → True) is byte-unchanged, as are the class half, `_typed_kind`, `wrap_store_rejection` (#400) and the classifier. **This census matches the builder report (§Q1C) and the contract.** No discrepancy.

```python
"""Census: fate of every engine-error shape through the REAL single-statement seam, build vs the Q1b deny-list.

Run from repo root: uv run python <this> (sys.path gets loremaster/tests for q1b's seam helper)."""
import asyncio, sys
sys.path.insert(0, "loremaster/tests")
import surrealdb.errors as e
import loremaster
from loremaster.store import _txn
import test_mint_kind_carveout_q1b as q1b

print("loremaster.__file__ =", loremaster.__file__)
Q1B_DENY = {"Internal", "Serialization", "Query", "TimedOut", "Cancelled"}
def q1b_fate(kind):  # HEAD logic, reconstructed from the patch's '-' lines
    return kind is not None and kind not in Q1B_DENY

def vals(c): return sorted(v for k, v in vars(c).items() if k.isupper() and isinstance(v, str))
cells = [(t, None) for t in sorted(set(vals(e.ErrorKind)) | set(e.KIND_TO_CLASS))]
cells += [("Query", d) for d in vals(e.QueryDetailKind)]
# every non-Query detail kind the SDK enumerates, on its own top-level kind
for name in dir(e):
    if name.endswith("DetailKind") and name != "QueryDetailKind":
        top = name[: -len("DetailKind")]
        for d in vals(getattr(e, name)):
            cells.append((top, d))
cells += [("Transaction", None), ("Query", "Aborted"), ("FutureKind", None), ("Query", "FutureDetailKind"),
          ("Query", "Validation"), ("Query", "NotFound"), ("NotExecuted", None)]

async def main():
    for top, det in cells:
        payload = {"kind": top, "result": f"census {top}:{det}"}
        if det: payload["details"] = {"kind": det}
        err = e.parse_query_error(payload)
        raised = await q1b._through_the_seam(err)
        cls = type(raised).__name__
        kind = getattr(raised, "kind", "-")
        ec = getattr(raised, "error_class", "-")
        build = _txn.proven_no_key(raised)
        head = (isinstance(raised, _txn.TxnDomainRejectionError) and
                (ec != "unspecified rejection" or q1b_fate(kind))) or isinstance(raised, _txn._PROVEN_NO_KEY_CLASSES)
        flag = "" if build == head else "  <-- CHANGED"
        print(f"{top+':'+str(det):34} {cls:28} kind={str(kind):14} class={ec:22} build={'PROVEN' if build else 'unknown':7} q1b={'PROVEN' if head else 'unknown'}{flag}")
    # kind-less (bare text) rejection
    r = _txn._domain_rejection_error("unspecified rejection", "x", kind=None)
    print("None (kind-less unspecified)", "build=", _txn.proven_no_key(r))
    for exc in (_txn.SurrealStoreError("x"), _txn.SurrealConnectionError("x"), ValueError("x")):
        print(type(exc).__name__, "build=", _txn.proven_no_key(exc))
asyncio.run(main())
```

## §2 Conformance
- **An allowlist, not a deny-list.** `_PROVEN_KINDS` = {VALIDATION, THROWN, ALREADY_EXISTS, NOT_FOUND, CONFIGURATION, QueryDetailKind.NOT_EXECUTED}, which is §15.3 exactly. The last line is `kind is not None and any(kind == proven …)`. `_OUTCOME_UNKNOWN_KINDS` is deleted.
- **Unenumerated kinds are unknown through the real seam and at the mint.** Census §1 plus the q1c cells, all green: `Transaction`, `Query:Aborted`, `FutureKind` and `Query:FutureDetailKind` are unknown on both the single-statement and the transactional seams. At the mint each gives the outer `PrincipalKeyStoreError`, the conditional note, and no "could not mint" (`TestAnUnenumeratedKindAtTheMint`, ×4).
- **The classified half is unchanged.** The diff touches only the kind half's return line. Recognised refusals are proven for every kind, including unenumerated ones (q1c axis cells).
  - **#400** (`wrap_store_rejection`) is untouched.
  - **The live UNIQUE pin** `test_am37_13_3_63c_i_a.py::TestALiveUniqueCollisionCarriesNoRevokeAdvice::test_a_duplicate_name_mint` PASSED against :18000 when run by node id.
- **Docstrings match the behaviour.** I checked the `_PROVEN_KINDS` comment, the `proven_no_key` docstring, and `PrincipalKeyStore.mint` `Raises:` / `_mint_fault_note`. These also close the stale prose the implementer flagged (REPORT-implement-mint-q1.md §Q1C).
- **Bare sweep** (my own; awk/python, because the grep hook blocks grep in the main checkout — fallback said aloud) for `OUTCOME_UNKNOWN|timing-proving|outcome-unknown kind|kind outside`. Every hit has a verdict:
  - `messages.py:156,1529` and `server.py:1391,1396,9037` (`_ACK_OUTCOME_UNKNOWN_MESSAGE`): different domain, **unrelated**.
  - `server.py:1162` ("a kind outside this set", memory kinds): **unrelated**.
  - `test_mint_kind_allowlist_q1c.py:8,166`: prose describing the deletion, **correct**.
  - `test_am37_13_3_63c_i_a.py:567` ("kind-less, or an outcome-unknown kind, is UNKNOWN"): **still true**. It is incomplete only by omitting the unenumerated kinds; it is not false.
- **The test-file edits change no assertion.**
  - q1b `test_every_kind_is_ruled`: both `assert` conditions are byte-identical; only the message text changed (the §15.4 rider). That text names the §15.3 doc, both dispositions and "Do not delete this pin" — **the rider is met**.
  - q1c: only the `TYPE_CHECKING` owner anchor and the now-unused `TYPE_CHECKING` import are removed.
  - `pending_contracts.yaml`: only the self-destructed `am37-15-3-q1c-mint-contract` bound is deleted.

## §3 My mutations
How they ran: `scripts/mutation_proof.py` in a `scratch_copy.sh` tree. `loremaster.__file__` = `…/scratchpad/tree/loremaster/loremaster/__init__.py`, and provenance was asserted by the script. Ids came from `--collect-only` and were declared in the driver before any run.

Targeted set: q1c, q1b, `test_mint_unknown_outcome_note_q1.py`, `test_am37_13_3_63c_i_a.py`, `test_engine_rejection_seam.py` and `test_principal_keys_store.py`.
- The derivation used `lore_impact` on `proven_no_key` and `PrincipalKeyStore.mint`. q1c and the q1 note file were added by hand, because `lore_impact` cannot see q1c's `getattr` reach.
- Baseline (build): **570 passed, 2 skipped**. The 2 skips are the pre-existing q1 pass-through skips.
- Each run used a 16G cgroup with `-n 8 --timeout=300`.

| # | mutation (in `_txn.py`) | declared | observed | verdict |
|---|---|---|---|---|
| a | add `"Transaction"` to `_PROVEN_KINDS` | 6 (allowlist-is-ruled, seam×2[Transaction], axis[UNSPECIFIED-Transaction], mint[Transaction], adding_Transaction) | 6 failed / 564 passed | **PROOF HELD exactly** |
| b | kind-less proven: `kind is None or any(…)` | 3 (axis[UNSPECIFIED-None], q1b kind_less_instance[TxnDomainRejectionError], q1b kind_less_mint[TxnDomainRejectionError]) | 3 failed / 567 passed | **PROOF HELD exactly** |
| c | revert to deny-list: `kind is not None and kind not in {INTERNAL, SERIALIZATION, QUERY, TIMED_OUT, CANCELLED}` | 21 (4 unenumerated × {seam, txn seam, mint}, axis[UNSPECIFIED-{Transaction, Aborted, FutureKind, FutureDetailKind, NotAllowed}], all 4 one-decider legs) | 21 failed / 549 passed | **PROOF HELD exactly** |
| d | drop `ErrorKind.VALIDATION` | 7 (allowlist-is-ruled, seam[Validation], axis[UNSPECIFIED-Validation], removing_Validation, q1b agree[Validation], q1b mint[Validation], q1b predicate_catch[Validation]) | 19 failed / 551 passed: all 7 declared RED, 0 declared-but-green, **+12 undeclared** | **killed**. The tool exits 4 because 12 cells went red that I had not declared — extra coverage, not a survivor. |

The 12 undeclared reds in (d):
- q1b `transactional_rejection_carries_its_kind[Validation]`;
- q1 `a_proven_fault_keeps_the_not_landed_message[TxnDomainRejectionError]` and 8 `does_not_claim…` cells;
- am37 `a_fault_during_the_CREATE_call[{plain,needs-quoting}-TxnDomainRejectionError]`.

Their typed-proven instance is Validation-keyed. After every run the tree was restored byte-exact (`9dfd8f7e…`). **0 survivors.**

## §4 Full suite (`pending_contract_gate.py --currency -- --maxprocesses=12`, 16G scope, 15:45–15:57Z)
- Preconditions: MemAvailable 57.8 GiB, and 0 lore pytest processes by `comm`.
- **Gate verdict:**
  - typecheck RED_ADJUDICATED (83, packet-58 / packet-64b-i);
  - ruff GREEN;
  - pytest RED_ADJUDICATED (**530**, packet-58-contract / packet-64b-i-contract);
  - **`CURRENCY: PASS`**, RED_ORPHANED 0.
- **Junit census (build, from the D-1 run):** **13416 passed, 530 failed, 70 skipped** (14016 cases). All 530 sit in the 32 files the registry names, and 0 are unowned.
  - Versus Q1b (13955 cases): +61 cases. I did not attribute that delta per file; the q1c file is new at `8ff4dd5`.
- **HEAD vs build on the 32 owned files.** The scratch tree's 5 files were restored to `git show HEAD:` bytes (`_txn.py` md5 `86f9a898…` = HEAD; `_PROVEN_KINDS` absent, `_OUTCOME_UNKNOWN_KINDS` present; `__pycache__` purged). Result: `530 failed, 1310 passed, 2 skipped`.
  - Diffed by node id against the build junit: **HEAD 530 · build 530 · identical 530 · HEAD-only 0 · build-only 0.**

## §5 Findings
- **R-1 (LOW, spec-level, pre-existing — not this build's diff).**
  - CLASS: *allowlist membership is tested over a namespace-FLATTENED typed kind.* `_typed_kind` keys a Query error by its detail string and any other error by its top string, and both land in one namespace.
  - Consequence: an unadjudicated Query detail whose name equals an allowlisted top kind (`Query:Validation`, `Query:NotFound`) is PROVEN, and so is a top-level `NotExecuted`. §15.3 meant "Query detail `NotExecuted`" and "top-level `Validation`…", which are namespaced.
  - SIBLINGS TRIED: Query:Validation, Query:NotFound, top NotExecuted (all PROVEN in the census). NOT TRIED: Query:{Thrown, AlreadyExists, Configuration} (same mechanism).
  - No engine serves these today, and the SDK enumerates none of them.
  - The build conforms to the spec's literal `error.kind in _PROVEN_KINDS`.
  - Fix shape if ruled: key the allowlist on `(top, detail)` pairs.
- **R-2 (LOW, spec-level, pre-existing).**
  - CLASS: *the allowlist adjudicates at TOP-kind granularity; every detail kind under an allowlisted top kind inherits "proven" without adjudication.* Examples: NotFound:{Transaction, Session, Method}, AlreadyExists:{Session, Namespace, …}.
  - The §15 table's rationale covers "NotFound (table/record)".
  - The §15.4 completeness pin enumerates only `KIND_TO_CLASS ∪ QueryDetailKind`, so a new member of `NotFoundDetailKind` etc. joins the proven set silently. That is the "bound that grows silently" which §15.4 rejected, one level down.
  - Reachability on the mint is low. The mint is a single-statement `run_query` (`PrincipalKeyStore._query`), and NotFound:Transaction is an interactive-transaction RPC detail.
  - Decision: accept as a pinned bound with a trigger (an SDK detail-kind addition), or extend the pin's domain to the `*DetailKind` enums.
- **F-3 (INFO).** Typed-proven fixtures outside q1b/q1c are a Validation monoculture (mutation d). This is harmless, because the q1b/q1c generated cells cover every allowlisted kind. No action.

No defect was found in the build itself.

## §6 md5s
| file | start (15:24Z) | end (16:03Z) |
|---|---|---|
| `loremaster/loremaster/store/_txn.py` | 9dfd8f7efa6deb942471c48916285bd4 | 9dfd8f7efa6deb942471c48916285bd4 |
| `loremaster/loremaster/principal_keys.py` | 422f4591c03514db3fdf2791d09a9925 | 422f4591c03514db3fdf2791d09a9925 |
| `loremaster/tests/test_mint_kind_carveout_q1b.py` | 84124a77ea444f80a98cce2d6485e331 | 84124a77ea444f80a98cce2d6485e331 |
| `loremaster/tests/test_mint_kind_allowlist_q1c.py` | 3a49a50ce132d1cfe549f51f2831a6d6 | 3a49a50ce132d1cfe549f51f2831a6d6 |
| `scripts/pending_contracts.yaml` | b0158ed1189ea905faf9c8d8b9f87f76 | b0158ed1189ea905faf9c8d8b9f87f76 |

`git status` at the end is the same as at the start (5 M, the same untracked files plus this report). The real tree was never mutated: every mutation ran in the scratch copy. Nothing was committed or stashed, no worktree was created, and only :18000 was used.

- **State:** done
