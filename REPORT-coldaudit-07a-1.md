brief-base v14 read · brief project v7 read

# REPORT — coldaudit-07a-1 — packet 07a COLD AUDIT (store recovery + degradation)

## SUMMARY BLOCK
- receipt: brief-base v14 read · brief project v7 read
- state: **done** — every GO leg re-derived live from HEAD `6fdeabe`; builder ≠ grader, nothing relayed.
- **VERDICT: NO-GO** — narrowly, on ONE blocking defect in a DOC (not the code): `RULING-fork-a.md:33`
  still carries the ACTIVE "Ruled: A1. Ship:" instruction **"Resolve #164/#250 as fixed-by-05a-ii"**, which
  the same file's own correction block (line 28) forbids. The `edbd72a` correction struck the diagnostic
  narrative but missed the parallel actionable bullet — an INCOMPLETE root-cause correction, the exact
  NO-GO condition the brief names. #164/#250 are still `acknowledged` (unresolved), so a clean GO → the
  lead proceeds straight to close-out → the stale line would write the false cause into the resolved outage
  findings (adversary F2 / Trust-Doctrine harm). **The fix is ONE doc line; the CODE is GREEN — see below.**
- **Everything else re-verified GREEN:** #128 fix correct/complete (13/13 GREEN in my fresh run, except-order
  right, contention wording byte-exact, plain-store-error does NOT claim retryable); #127 tripwire
  mutation-proven BY ME (3rd caller reddens + names it); #164/#250 drill exercises the real `SurrealStore`
  path, self-heals 20/20 live, negative control wedges live when I disabled self-heal; KeyError-branch guards
  mutation-proven BY ME (revert store catch → 2 RED); timeline holds (9d29111=2026-07-14 predates
  #164/#250; f5aec32=2026-08-10 after); production diff is `server.py`-only; ruff clean; server.py 0 mypy.
- deviation 1 (secondary finding, NON-blocking): `scripts/probe_store_recovery_07a.py` ALWAYS exits 1 (even
  on a clean PASS) — `sys.exit(asyncio.run(main()))` raises `SystemExit(0)` INSIDE `try/except BaseException`,
  which catches it and re-exits 1. The PASS/FAIL *text* is correct and discriminating; the *exit code* the
  author's `scenario_negative_control` docstring promises ("0 = the negative control held") is defeated by
  the wrapper. If the deploy-smoke gates on `$?`, it can't tell PASS from FAIL. Recommend fixing before it
  is wired as an automated gate. §7.
- Packages considered: **none — no mechanism specified** (this is an audit; I authored no production code).
- Reuse ledger: **none** — no production symbols authored; scratch-only mutation instruments (verbatim §8).
- Graded: `6fdeabe` · HEAD-at-report: `6fdeabe` · SAME. (Prod diff `a1ac479..6fdeabe -- loremaster/loremaster/`
  = `server.py` only; the blocking defect is in `docs/…/RULING-fork-a.md`, present at HEAD.)
- decisions-needed: **the NO-GO fix is the lead's** — update `RULING-fork-a.md:33` to match its own line-28
  correction ("does-not-reproduce-at-HEAD; root cause undiagnosed"), then it is an immediate GO with NO
  re-run of code/tests/gates required (they are all verified below).
- receipt POINTERS: #128 code+wording §1 · #128 tests re-run §2 · #127 tripwire mutation §3 · #164/#250 drill
  + neg-control (live) §4 · KeyError-branch mutation §4.3 · timeline/scope §4.4 · production scope §5 ·
  gates §6 · probe exit-code defect §7 · scratch instruments §8 · **the NO-GO defect §0**.

---

## 0. THE BLOCKING DEFECT — `RULING-fork-a.md:33` (NO-GO)

The brief's NO-GO list names: *"the root-cause correction is incomplete (some doc still says
'fixed-by-05a-ii')."* It is.

`docs/plans/v2/receipts/2026-08-17-packet07a/RULING-fork-a.md` structure at HEAD `6fdeabe`:
- **line 15–28** — a correction blockquote added by `edbd72a` (adversary F2): *"⚠ CORRECTED … the root-cause
  attribution below was FACTUALLY WRONG and is struck … Close-out must resolve #164/#250 as 'does not
  reproduce at HEAD; … root cause of the original wedge undiagnosed' — **never as "fixed by 05a-ii."**"*
- **line 33** — UNCHANGED by `edbd72a`, an ACTIVE bullet under **"Ruled: A1. Ship:"**:
  `- Resolve #164/#250 as **fixed-by-05a-ii**, with a named re-open trigger (below).`

The document contradicts itself: the correction block forbids exactly what the actionable Ship bullet still
commands. I confirmed `edbd72a`'s diff touched only the diagnostic paragraph + added the blockquote and left
the "Ruled: A1. Ship:" list untouched (§4.4). The contract author already flagged this to the lead
(`REPORT-contract-07a-1.md` §13 / line 409: *"RULING-fork-a.md itself asserts 'fixed-by-05a-ii' — the lead
has been notified to correct the ruling's claim"*), and the lead's own `edbd72a` commit message says the
correction exists *"rather than left to poison the findings close-out"* — so the intent was a FULL
correction; line 33 slipped through.

**Why it blocks (not a pedantic nit):** `#164` and `#250` are BOTH still `acknowledged` (I queried them —
§4.5), i.e. the false cause has NOT yet landed in a resolved record. The brief says a clean GO → the lead
goes *straight to deploy + close-out with no intermediate review*. Close-out is where #164/#250 get
resolved, and the operator ruling is the authority the contract doc cites for that resolution (contract §8).
A lead anchoring on the ruling's actionable "Ship:" list hits line 33 and writes "fixed-by-05a-ii" into a
resolved outage finding — the precise Trust-Doctrine harm adversary F2 raised and the correction exists to
prevent. This is `THE RIDER IS PART OF THE RULING` / `A DIAGNOSIS IS NOT AN INSTRUMENT`: the correction
fixed the prose that *describes* the cause but not the instruction that *commands* the resolution.

**Required fix (one line, lead-owned):** edit `RULING-fork-a.md:33` to strike "fixed-by-05a-ii" and read,
e.g., `- Resolve #164/#250 as **does-not-reproduce-at-HEAD (both transport-fault branches guarded +
mutation-proven; root cause of the July wedge UNDIAGNOSED)**, with a named re-open trigger (below).` —
matching line 28 and contract-doc §B (lines 114–116), which are already correct. No code/test/gate re-run is
implicated; all of those are verified GREEN below.

---

## 1. #128 fix — correct, complete, byte-exact (code read at HEAD)

`loremaster/loremaster/server.py::AppContext._resolve_or_acknowledge_many` (read live, lines 3915–3963).
The per-item `except` chain, IN ORDER:
1. `except SurrealConnectionError:` → `aborted = True` + `ABORTED — store connection lost; retry these`.
2. `except TxnContentionExhaustedError:` → `FAILED — store contention, safe to retry this item` **(byte-exact
   to the ruled line)** + `continue`.
3. `except SurrealStoreError as error:` → `FAILED — {_sanitise_line(str(error))}` + `continue` — **does NOT**
   use the "safe to retry" wording.
4. `except (_FindingNotFoundError, _FindingIllegalTransitionError, ValueError) as error:` → generic FAILED.

Error hierarchy (`store/_txn.py`): `SurrealStoreError(RuntimeError)` @116; `SurrealConnectionError` @120 and
`TxnContentionExhaustedError` @156 are SIBLINGS under it. So the order is load-bearing and correct:
`SurrealConnectionError` (abort-all) MUST precede its `SurrealStoreError` base; `TxnContentionExhaustedError`
MUST precede its `SurrealStoreError` base to keep the distinct wording. The live file matches exactly. ✓

---

## 2. #128 tests — re-run fresh by me (not relayed)

`uv run pytest "loremaster/tests/test_mcp_server.py::TestResolveManyAcknowledgeManyDispatch" -q -p no:cacheprovider`:
```
13 passed in 17.66s
```
I read the 3 target pins (`test_mcp_server.py:7763/7816/7865`) + the injector `_LedgerRaisingOnSecondCall`
(@7562). They are strongly discriminating, not vacuous:
- contention pin asserts `lines[2] == "- #{n} FAILED — store contention, safe to retry this item"` (byte-exact)
  AND `lines[3]` = the NEXT item still succeeds (the CONTINUE discriminator — a build that aborts fails here).
- plain-store-error pin asserts `"safe to retry this item" not in lines[2]` AND `len(lines) == 4` (unfractured)
  — catches a wrong build that catches the `SurrealStoreError` base and labels everything retryable.
- acknowledge pin re-runs the same fault on `acknowledge_many` — the verb-parity discriminator.
The injector genuinely raises on the 2nd call and genuinely delegates the rest (`__getattr__` → inner
ledger). ✓

---

## 3. #127 tripwire — mutation-proven BY ME

`uv run pytest "loremaster/tests/test_scout.py::TestScoutEnsureConnectionSoleDriverTripwire" -q` → `2 passed`.
The scan (`_command_subscriber_ensure_connection_callers`, test_scout.py:1729) parses the AST of the ACTUAL
imported `loremaster.scout.__file__`, scoped to the `CommandSubscriber` class; a not-vacuously-green
self-guard asserts `{run, process_pending_once} <= callers` first, then the equality pin asserts
`== {run, process_pending_once}`.

**My mutation** (scratch copy `/tmp/ca07a-scratch1`, provenance asserted —
`loremaster.scout.__file__ = /tmp/ca07a-scratch1/loremaster/loremaster/scout.py`): I inserted a 3rd caller
`async def _coldaudit_third_caller_probe(self): await self._ensure_connection()` into `CommandSubscriber`.
Result:
```
1 failed, 1 passed
E  AssertionError: CommandSubscriber._ensure_connection now has caller set
   ['_coldaudit_third_caller_probe', 'process_pending_once', 'run'], not {process_pending_once, run}. …
```
The equality pin RED and **names the new caller**; the self-guard stayed GREEN. Restored. ✓

---

## 4. #164/#250 adjudication — honest (every leg reproduced by me)

### 4.1 The probe exercises the REAL `SurrealStore` path (GO 3a)
`scripts/probe_store_recovery_07a.py`: `_query_once` calls `store._query(statement)` on a real
`SurrealStore` (@95–101); `_make_store` builds a real `SurrealStore` (@84–92). The bare `AsyncSurreal` is
used ONLY in `_wait_server_back` (@122) to separate "server is back" from "held store healed" — correct. ✓

### 4.2 Drill + negative control — reproduced LIVE against spike-surreal (:18000) (GO 3b)
`uv run python scripts/probe_store_recovery_07a.py drill` (my run, HEAD tree, TEST store only):
```
SUMMARY: 20/20 recovered without a container restart; heal-index set=[1]; wedged bounces=[]
==> PASS — 20/20 self-healed
…
NEGATIVE CONTROL — self-heal DISABLED (_drop_connection no-op):
  with self-heal disabled: heal-index=None (None = wedged, as REQUIRED)
==> PASS — the drill DETECTS a wedge; its 20/20 above is a real signal.
```
So the held store self-heals 20/20 after a full server bounce (#164/#250 does NOT reproduce at HEAD), AND
the drill genuinely discriminates a wedge (not vacuously green). ✓
(⚠ the process EXIT code was 1 despite both legs passing — a defect in the script's `__main__` wrapper, §7 —
but the PASS/FAIL TEXT, which is what establishes the claim, is correct.)

### 4.3 KeyError-branch guards — mutation-proven BY ME (GO 3c)
`TestQuerySeamSdkKeyErrorClassification` + `TestTxnSdkKeyErrorClassification` exist in
`loremaster/tests/test_surreal_store.py` (@2058, @2129). I reverted the store's KeyError catch in the
scratch copy (both `run_query._attempt` @1208 and `_txn_query_raw` @1491:
`except (*_CONNECTION_ERRORS, KeyError)` → `except _CONNECTION_ERRORS`, and dropping the
`isinstance(error, KeyError)` guard) — the adversary's Exp A. Result:
```
2 failed in 1.23s
FAILED …TestQuerySeamSdkKeyErrorClassification::…surfaces_as_connection_error_and_heals
FAILED …TestTxnSdkKeyErrorClassification::…surfaces_as_connection_error_and_drops
   E  KeyError: '3fae6a02-…' (raw KeyError now propagates untyped)
```
So the two cited classes ARE mutation-provably tied to the KeyError branch; the re-anchored regression
trigger (contract §B) is honest. Provenance asserted: reverted file =
`/tmp/ca07a-scratch1/loremaster/loremaster/store/_txn.py`. ✓

### 4.4 Timeline + constant-scope (GO 3d)
- `git show -s --format=%cI 9d29111` → **2026-07-14** (the "ONE retry seam" commit — already catches
  `(*_CONNECTION_ERRORS, KeyError)`), 8 days before #164 (07-22), 13 before #250 (07-27). ✓
- `f5aec32` (05a-ii's `_SDK_AWAIT_BOUNDARY_ERRORS`) → **2026-08-10**, AFTER both findings. ✓
- `_SDK_AWAIT_BOUNDARY_ERRORS` is read ONLY by `inbox_awaiter.py` + `scout.py`; `run_query`/`_txn_query_raw`
  use the literal tuple, never the constant (grep confirmed). So "05a-ii fixed the store wedge" is
  chronologically impossible — F2 is correct, and this is exactly why line 33 (§0) is false.
- `edbd72a` diff on the ruling: struck the root-cause paragraph + added the correction blockquote; the
  "Ruled: A1. Ship:" list (incl. line 33) is UNCHANGED — the incomplete correction.

### 4.5 Finding states
`#164` = **acknowledged**, `#250` = **acknowledged** (both queried live). Neither resolved yet ⇒ the false
cause has not yet landed, but WILL at close-out if line 33 stands.

---

## 5. Production scope — `server.py` only (GO 4)
`git diff a1ac479..6fdeabe -- loremaster/loremaster/` = `server.py` (+21/-1): the import widening +
the two `except` clauses, nothing else. Full-range file stat: only `server.py` (prod), `test_mcp_server.py`
/ `test_scout.py` (tests), `probe_store_recovery_07a.py` (script), and docs/reports. **Nothing in
`store/_txn.py`, `store/surreal.py`, or `scout.py` changed.** ✓

---

## 6. Gates
- **ruff:** `uv run ruff check .` → `All checks passed!` ✓
- **typecheck (`scripts/typecheck.sh`):** loremaster leg `Found 102 errors in 8 files` — IDENTICAL to the
  builder's claimed baseline; **`server.py` = 0 errors** (my own `grep -c` → 0). Every errored file is
  auth/posture/roster/permission test infra (`PostureConfigError`, `resolve_posture`, `lorerunes.Posture`,
  `SCOPE_READ`, …), all registered in `scripts/pending_contracts.yaml`; `gates.yaml` marks `typecheck`
  `adjudicated_by: pending-contracts`. So RED_ADJUDICATED, unchanged, none in any file 07a touched. ✓
- **full suite (`uv run pytest -n auto -p no:cacheprovider -q --continue-on-collection-errors`, my run,
  236s):** `451 failed, 9878 passed, 51 skipped, 3 xfailed, 135 errors` — **byte-identical to the builder's
  claimed baseline** (451 failed / 135 errors). ZERO new failures from 07a; the `TestResolveManyAcknowledge
  ManyDispatch` class is in the 9878 passed (§2). The 135 errors are the `test_message_ledger` [real]-variant
  errors (the `store/_txn.py` multi-statement `.query()` teardown guard, #124/#144 territory) — exactly what
  finding **#384** captures. My run corroborates #384's counts independently. ✓

---

## 7. Secondary finding (NON-blocking) — probe exit code is always 1
`scripts/probe_store_recovery_07a.py` `__main__` (L334–339):
```python
try:
    sys.exit(asyncio.run(main()))
except BaseException:      # <-- SystemExit IS a BaseException
    traceback.print_exc()
    sys.exit(1)
```
`sys.exit(main())` raises `SystemExit(0)` on a clean PASS; the bare `except BaseException` catches it and
re-exits 1. Confirmed in isolation (`ISOLATED_EXIT=1` for a `main()` returning 0). So a PASS, a FAIL, and a
crash ALL exit 1 — the exit code cannot discriminate, defeating the author's own contract
(`scenario_negative_control` docstring: "0 = the negative control held"). The PASS/FAIL **text** is correct,
so the load-bearing claims stand; but if the deploy-smoke is gated on `$?`, it is a false gate. Recommend
`raise SystemExit(asyncio.run(main()))` or narrowing to `except Exception`. Out of my writable set — flagged.

---

## 8. Scratch instruments (verbatim; brief-base §1)
Scratch tree: `./scripts/scratch_copy.sh /tmp/ca07a-scratch1` — provenance asserted (imports resolve inside
the copy; receipt in §3/§4.3). Real repo `git status` CLEAN throughout (all mutation in scratch).
- **#127 3rd-caller mutation:** inserted into `CommandSubscriber` (before `class Scout`):
  ```python
  async def _coldaudit_third_caller_probe(self) -> None:
      await self._ensure_connection()
  ```
- **KeyError-catch revert (Exp A), on scratch `store/_txn.py`:**
  ```python
  # run_query._attempt @1207-1209:
  except _CONNECTION_ERRORS as error:      # was: except (*_CONNECTION_ERRORS, KeyError) as error:
      if is_connection_error(error):       # was: if isinstance(error, KeyError) or is_connection_error(error):
  # _txn_query_raw @1491:
  except _CONNECTION_ERRORS as error:      # was: except (*_CONNECTION_ERRORS, KeyError) as error:
  ```
Scratch tree `/tmp/ca07a-scratch1` left in place pending the lead's word — keep for re-runs or discard.

---

## VERDICT: NO-GO
Single blocker: **`RULING-fork-a.md:33`** still actively instructs "Resolve #164/#250 as fixed-by-05a-ii" —
an incomplete root-cause correction, the exact NO-GO condition the brief names, and a live trap for the
close-out (#164/#250 unresolved). Fix = ONE doc line (§0). Everything the fix does NOT touch — the #128 code,
its tests, the #127 tripwire, the #164/#250 drill + KeyError guards, the production scope, ruff, and mypy —
is re-verified GREEN by me. Once line 33 is corrected, this is an immediate GO with no code/test/gate re-run.
Secondary (non-blocking): the probe's always-1 exit code (§7) — fix before wiring it as an automated gate.
