brief-base v26 read
- State: done
- Deviations: (1) I ran three read-only probes against the production container to settle the deploy and #585 questions: `podman exec lore-lore python -c …version…`, `podman inspect lore-lore`, and `podman logs --since/--until lore-lore`. (2) The currency run was wrapped in `timeout 900`. There were no edits, no git writes, no lore writes and no pytest runs.
- Packages considered: none — no mechanism specified
- Odoo-20 portability: n/a — no Odoo seam touched
- Reuse ledger: none
- Graded: e1593d7 · HEAD-at-report: e1593d7 · SAME (lore index watched root git_ref = e1593d7, last_sync 643 s, measured 2026-11-09)
- Decisions-needed: (a) 6 currency filings → keep one, close five as duplicates? (b) #575 → duplicate of #576? (c) #585 has a measured root cause → ruling on how to classify the 3.3.x memory-guard refusal.
- Receipt pointers: currency log `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/6e790ee8-67a1-4692-9da9-f68f96b17102/scratchpad/currency-subset.log` (TREE=82c9ed5a…, EXIT=1). The sweeps are pasted verbatim under §Instruments.
- ⚠ CROSS-CUTTING FACT (measured 2026-11-09): production `lore-lore` runs image `43122071` (created 2026-10-31) with **surrealdb 2.0.0**. Every "FIXED-AT-HEAD" below that relies on packet 66 (`df84764`) is fixed in SOURCE only. None of it is live until the 65-cut deploy, and it needs re-measuring after that deploy.

## Verdicts (graded at e1593d7)

**#579 — FIXED-AT-HEAD** (`58fd5df`). `scripts/pending_contract_gate.py::PendingFile.red_nodeids` adds a pytest-only expected-RED node-id claim. `PendingContractRegistry._entries_must_state_a_claim` admits an ids-only entry and refuses a node id whose path prefix is another file. The self-destruct legs are in `PendingContractGate.pytest_self_destruct_findings`. The registry uses no `red_nodeids` entry yet (0 occurrences in `scripts/pending_contracts.yaml`), so the shape exists but has not been exercised in the live registry. The round-3 `getattr`-looked-up `StringRecordId` case is now expressible as a node-id claim instead of a mypy symbol.

**#533 / #540 / #555 / #565 / #577 / #589 — STILL-OPEN, one defect class.** All six bodies describe the same defect: under `--legs`, an unselected manifested leg renders `NOT_RUN` plus ORPHAN and fails the verdict. Same subject, same mechanism, filed 2026-10-04 → 11-08. Keep #589 as the canonical row (it has the fullest body, the provenance commit `e8087b0`, and the #312-vs-subset design tension) and mark the other five DUPLICATE-OF #589.
- Mechanism at HEAD: `_currencies_for` iterates `manifest.gates`, not the selected legs. Any gate with no entry in `results` gets `VERDICT_NOT_RUN`, which is in `FAILING_VERDICTS`, and `_render_currency` sets `ok = all(...)` over every manifested gate.
- Run once, at HEAD e1593d7: `EXIT=1`. The verbatim pytest-leg lines:
  `  pytest       NOT_RUN — claimed by the manifest, never executed`
  `      ORPHAN: gate 'pytest' is CLAIMED by the manifest and was NOT RUN — a claimed-but-unrun gate is finding #312 exactly. This says NOTHING about whether it would pass.`
  `CURRENCY   : FAIL — claimed but never run: pytest`
- Side observation, not in the brief: typecheck now reads RED_ADJUDICATED with **99** residuals. Filings #540/#555/#565 measured 83. All 99 are owned (no orphan), but the count grew by 16.

**#495 / #496 / #498 / #511 — FIXED-AT-HEAD (source only; NOT deployed).** One class: the SDK 2.0.0 response-routing `KeyError(<request uuid>)` served raw. In `df84764`, `loremaster/store/_txn.py` retired the `KeyError` arm: `_SDK_AWAIT_BOUNDARY_ERRORS = _CONNECTION_ERRORS = (OSError, SurrealError)`, with a comment citing #336 and drop list #1. The SDK 3.0's typed `TransportError` is now raised by the shared fate function (the one `run_query` and `_txn_query_raw` both call) as `SurrealOutcomeUnknownError`, with the text "got no answer (outcome unknown): … — a write may have landed: verify before retrying; a read is safe to re-run". That serves #496's and #511's ask (named class, retry advice). Pins: `test_sdk3_workaround_retirement.py::TestAnInFlightDropIsATypedSdkTransportError` and `test_sdk3_connection_factory.py::…in_flight_at_a_drop` (I did not run either; they are 66's receipts). Two things stay open:
- production still serves the uuid shape (SDK 2.0.0);
- the TRIGGER is unmeasured. #498 saw 3 parallel calls fail together. Whether concurrent calls still fail as a batch under SDK 3 is UNVERIFIED. To settle it: after deploy, run ≥8 parallel `lore_search` calls and count the failures.

**#585 — STILL-OPEN; not a duplicate of the uuid class; root cause measured.** The prod log at `2026-11-08T11:59:37.751759Z` reads `store.query.rejected … "error_class": "unspecified rejection", "engine_error": "The query was not executed due to the memory threshold being reached"`. That is the 3.3.x memory guard (`SURREAL_MEMORY_THRESHOLD=12g` in the `lore-surreal.container` quadlet, set 2026-11-07). At HEAD, `_classify_engine_error` has no marker for that text; my sweep found 0 hits for "memory threshold" in code or the store reference. So the error still lands on `_ERROR_CLASS_UNSPECIFIED`, and a load-transient engine refusal is served as an unnamed domain rejection with no retry advice. The same second also logged `index.file.store_failed` (reason `store_op_failed_after_retries`), so the guard refused index writes as well, not only `lore_search`.

**#575 / #576 — #575 is a DUPLICATE-OF #576** (same reporter, filed 7 s apart; #576 is the superset with three connection paths plus the annotations). **#576: FIXED-AT-HEAD (source only; NOT deployed)** by `df84764`:
- `_txn.py::open_surreal_connection` is the one shared factory, with `SURREAL_RECONNECT = ReconnectOptions(attempts=-1, retry_delay=0.5, retry_delay_max=2.0)`.
- Fate-1 transport faults call `drop(connection)`.
- Pinned by `test_sdk3_lifecycle.py::TestAnIdleOwnerServesItsFirstCallAfterAStoreBounce::test_every_owner_answers_its_first_call_after_a_bounce`, over the derived owner set (`TestTheOwnerSetIsNotSilentlySmall`), and by `TestRecoveryLatencyAfterALongOutage`.

RULING-14's R-4/T3 bound (in the `_txn.py` fate docstring, quoted in my words) says a 30 s `TransportTimeoutError` drops the owner's SHARED connection, so an in-flight sibling is served OUTCOME UNKNOWN. That makes the fix over-broad but honest; it does not undo it. Re-open trigger: the first non-zero `TransportTimeoutError` count. Re-observed on prod SDK 2.0.0 on 2026-11-09 (annotation).

**#478 — FIXED-AT-HEAD in part (source only; NOT deployed).** Same class as #576, with a worse consequence: under SDK 2.0 it never recovered (52 min). At HEAD, the reconnect-forever factory plus `drop` covers "re-establish". `TestRecoveryLatencyAfterALongOutage` (RS2: the outage outlasts a finite budget) pins it. **The second ask stays STILL-OPEN:** "a health surface that reports store reachability, because the MCP endpoint stays UP while every call fails". I found no store-reachability health surface. That conclusion comes from code reading only; settling it needs a check of `lore_index` / the HTTP health route.

**#609 — first half DUPLICATE-OF #576; second half STILL-OPEN.**
- First half: "intermittent 1005 for minutes, one session ok while another fails". This is #576's mechanism exactly. The store owners (findings, tasks, index…) each hold their own long-lived connection, and each fails once on first use after the bounce. It was observed on the SDK 2.0.0 image; HEAD's per-owner first-call pin covers it.
- Second half: lore-surreal SIGKILLed after a 10 s SIGTERM. The quadlet `~/.config/containers/systemd/lore-surreal.container` sets no `StopTimeout=` and its `[Service]` has only `TimeoutStartSec=120`, so podman's default 10 s grace applies. That is a separate defect and should be split into its own finding.

**#512 — STILL-OPEN; 17 wraps at HEAD (count unchanged).** The AST sweep found 18 production `async def _ensure_connection` definitions under `loremaster/loremaster/`. scout's is a 5-line `_connect` delegate with no try, as the finding allows. The other **17** each wrap `open_surreal_connection` → `signin` → `bootstrap_session` in a try that catches exactly `TxnContentionExhaustedError` and `_CONNECTION_ERRORS`, closes the connection, and translates to `SurrealConnectionError`. Packet 66 shared the construction policy (`open_surreal_connection`) but not the disposition wrap, so the clone class #512 names is intact. The sites are agents, audit, briefs, diff, findings, floor_calibration/store, graph_surreal, index/snapshots, index/surreal_manifest, keeps, memory/local, messages, principal_keys, principals, store/lease, store/surreal and tasks.

**#548 — STILL-OPEN.** `loremaster.server._eager_build_with_retry` at HEAD still calls `logger.warning("eager startup build attempt failed; retrying", extra={"attempt": …, "max_attempts": …})` inside `except BaseException as exc`, with no `exc_info` and no exception type. The cause is still invisible until the final attempt.

**#553 — FIXED-AT-HEAD for `<slug>.db`, with a residual.**
- `<slug>.db` is NOT opened by server boot. `server.py` passes `_DEFAULT_MANIFEST_DIR / f"{slug}.db"` into `build_app_context` only as a path anchor (comment: "``manifest_path`` survives only as the anchor"). The file is now lore-deploy's own host ledger (`lore_deploy.Ledger`, RULING-572, `7d79115`), so the setup verb's existence check is deliberate, not residue.
- Residual: boot DOES open SQLite `<slug>.memory.db` through `MemoryLedger` → `open_resilient_sqlite` (`build_app_context`, "FP-06 durable write-through … until P7 moves memory"). That is a live, in-code-documented dependency. If the finding meant this file, it is STILL-OPEN as a "should this still exist" question for the operator.
- Separately: 3 `wire_test_*.memory.db` strays (dated 2026-09-26) sit in the production state dir `~/.local/state/lore/`. Some test wrote into the production state path.

**#594 — STILL-OPEN; 13 copies at HEAD** (the finding's "~12" is low by 1). The sweep found 13 production `def _as_rows` definitions across all workspace members, all in loremaster. Hashing the bodies with docstrings stripped gives 4 distinct bodies:
- 9 identical: agents, briefs, diff, findings, index/surreal_manifest, memory/local, messages, store/surreal, tasks;
- 2 identical: floor_calibration/store, store/lease;
- 2 variants with the `noun=`/`landed=` signature: principal_keys and principals, each distinct.

## Instruments (verbatim, so the counts can be re-run)
```python
# _ensure_connection wrap shape (run: python3 -I - from repo root)
import ast,pathlib
for p in sorted(pathlib.Path('loremaster/loremaster').rglob('*.py')):
    src=p.read_text(); tree=ast.parse(src)
    for f in ast.walk(tree):
        if isinstance(f,ast.AsyncFunctionDef) and f.name=='_ensure_connection':
            handlers=[ast.unparse(h.type) for t in ast.walk(f) if isinstance(t,ast.Try) for h in t.handlers]
            print(p, handlers)
```
```python
# _as_rows copies + distinct bodies (docstring-stripped)
import ast,pathlib,hashlib,collections
groups=collections.defaultdict(list)
for p in sorted(pathlib.Path('.').glob('lore*/lore*/**/*.py')):
    if '.venv' in p.parts: continue
    tree=ast.parse(p.read_text())
    for f in ast.walk(tree):
        if isinstance(f,ast.FunctionDef) and f.name=='_as_rows':
            f2=ast.parse(ast.unparse(f)).body[0]
            if f2.body and isinstance(f2.body[0],ast.Expr) and isinstance(getattr(f2.body[0],'value',None),ast.Constant): f2.body=f2.body[1:]
            groups[hashlib.sha1(ast.unparse(f2).encode()).hexdigest()[:8]].append(str(p))
print(sum(map(len,groups.values())), len(groups)); [print(h,v) for h,v in groups.items()]
```
Currency command: `{ ~/.claude/orchestration/tree_id.sh . ; uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff; echo EXIT=$?; }`. #585's prod-log probe: `podman logs --since 2026-11-08T11:50:00Z --until 2026-11-08T12:15:00Z lore-lore`, filtered in Python for `reject` / `engine_error`.
