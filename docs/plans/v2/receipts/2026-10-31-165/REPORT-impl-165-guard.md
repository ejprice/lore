brief-base v24 read · brief project v7 read (lore_comms register, session fix-165-2026-10-31)

# REPORT-impl-165-guard

## Summary (HEAD `4e615b5`, measured 2026-10-31)
- **State:** done-with-deviations (one: a mypy fix after the first gate batch; see Deviations).
- **Built:** new repo-root `conftest.py` (the only file written besides this report). `ProductionStoreGuard` wraps `socket.socket.connect` / `connect_ex`; a loopback `:18500` attempt is refused (`ConnectionRefusedError` / `ECONNREFUSED`) and recorded; every pytest report (collect report; setup / call / teardown) drains the record and fails itself naming the node + every attempt.
- **Gates** (full table §Gates): contract **31 passed / 0 failed** · skill suite **202 passed** · `--co` **14098 collected, EXIT=0** (= lead baseline) · store smoke `test_txn_contention.py` **22 passed** · currency `--legs typecheck,ruff` **RED_ORPHANED 0** (typecheck RED_ADJUDICATED, ruff GREEN) · `ruff check conftest.py` clean · `mypy conftest.py` clean after fix. Post-fix re-run: §Gates R2.
- **Deviations:** (1) first `mypy conftest.py` = 2 errors (wrapper `sock` annotated `socket.socket`, typeshed types the method on `_socket.socket`; ignore code mismatch). Fixed by annotating `sock: Any` with a WHY comment; annotation-only, so G2–G4 ran on behaviourally identical code; G1/ruff/currency re-run on the final text (§Gates R2). (2) Mechanism differs from the reference guard on purpose (§Decisions D1).
- **Packages considered:** run-time socket blocking → `pytest-socket` → `bespoke` for the port gap; NOT re-read by me — the brief excludes it on the contract author's read (host filter, no recorder; MEDIUM per that report) and I found nothing doing the port job. Loopback test → stdlib `ipaddress` → `replace` (used). Hook mechanics → pytest's own `wrapper=True` hookimpls (`pytest_runtest_makereport`, `pytest_make_collect_report`, pytest 9.0.3 installed, read live) → `replace`.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 2 rule-deciding symbols + named trivia, all dispositioned (§Reuse / DRY ledger).
- **Graded:** n/a (builder).
- **Decisions needed:**
  1. D1/D2 behaviour beyond the contract (§Decisions): per-report drain (charges module/session-fixture attempts to the test that ran the fixture; the reference DISCARDED them via `clear()` at setup), collect-report charging, and xfail/skip → FAILED. No contract pin covers these three; keep (my pick) or strip? If kept, they want pins (I may not write tests).
  2. `scripts/typecheck.sh` `MEMBERS` does not include the root `conftest.py` (known residual per brief) — exact edit in §Noticed.
- **Fan-out:** haiku 6 · sonnet 0 · peak 5.
- **Pointers:** §Gates · §Decisions · §Reuse / DRY ledger · §Noticed · §conftest.py (verbatim)

## Routing table (written before the first sweep, 2026-10-31)

| step | tier | who | reason |
|---|---|---|---|
| R1. read contract `test_prod_store_guard.py` | 3 | self | the spec I build against; every line matters |
| R2. reuse sweep: existing socket guard / port constant / conftest hooks across members | 1 (parallel batch) | self, ONE batch (lore_search ×2 + a literal grep for `18500` with coverage line) | small set (3 queries), I read all output, feeds the chokepoint decision directly |
| B. write root `conftest.py` | 3 | self | implementation |
| G1. contract run | 1 | haiku-runner | test run |
| G2. skill suite run | 1 | haiku-runner | test run |
| G3. collect-only blast check | 1 | haiku-runner | test run |
| G4. loremaster store smoke | 1 | haiku-runner (pick of file = self, tier 3: needs judgement on which file hits the store) | test run |
| G5. currency typecheck+ruff, ruff conftest.py, mypy conftest.py | 1 | haiku-runner ×1 (sequential commands, one runner) | lint/type gate |

G1–G5 are independent once the conftest exists → spawned in ONE message.

## Reuse / DRY ledger (sweep run 2026-10-31 at `4e615b5`)

Sweep coverage: literal `18500` over `git ls-files '*.py' '*.toml' '*.yaml' '*.yml' '*.sh'` minus `docs/` → files_scanned=523; `pytester|socket.socket.connect|pytest_plugins` over `git ls-files '*.py'` → scanned=509, hits=2 (neither patches `socket.socket.connect`; one is the #466 listener scanner); `import conftest|from conftest` → 0 hits / 509. Plus two `lore_search` queries (guard mechanism; port constant / loopback predicate) — both returned only the contract report and the #486 lifecycle file. Grep fallback said out loud: these are non-symbol textual seams (a literal port, an import spelling), CLAUDE.md dogfood case (b).

| new symbol | where I looked | what it returned | disposition |
|---|---|---|---|
| `PRODUCTION_STORE_PORT` | grep `18500` (above); lore_search "named constant for production surreal store port" | `scripts/restore_prod_dump.py::PRODUCTION_PORT = 18500` (int), `loremaster/tests/test_harness_database_lifecycle_486.py::_PRODUCTION_STORE_PORT = ":18500"` (str, test-private), `scripts/probe_reanchor_58.py::PRODUCTION_PORT_MARKER`, `scripts/zero_test_store.sh PROD_PORT`; `lore_deploy._scaffold_lore_yaml` holds it only inside a template string | HAND-ROLLED, per ruling "Port literal". None is importable from the root conftest without a new dependency: the contract's `_mirror_repo` mirrors only the root `conftest.py` + `pyproject.toml` + the skill trees, so `import restore_prod_dump` (or any loremaster test helper) would be an ImportError in every inner session, and a conftest importing a `scripts/` tool would also load that tool's module-level state into every suite. Ruling forbids a new shared module. |
| `ProductionStoreGuard` (+ `targets_production`, `drain`, `install`, `charge`) | lore_search "pytest guard blocking socket connection to production store port"; read `loremaster/tests/conftest.py` + `_sdk_guard.py` | the nearest mechanism is loremaster's own "record per test, `pytest.fail` at fixture teardown" idiom (`_every_database_a_test_opens_was_minted_by_the_harness`), living in `loremaster/tests/` — not loadable from the root, and member-private | HAND-ROLLED; mechanism differs deliberately (per-report drain, see §Decisions D1). `pytest-socket` excluded by the brief and the contract report (host filter, no recorder); not re-litigated — I found nothing that does the port job. |
| `LOOPBACK_HOSTNAME`, `REFUSED_ERRNO`, door labels, `_SESSION_NODE_LABEL`, address index constants | n/a — module-private literals named per the no-hardcoded-values rule | — | HAND-ROLLED (trivia, not policy) |

Loopback decision delegated to stdlib `ipaddress.ip_address(...).is_loopback` (covers `127.0.0.0/8` and `::1`), not hand-rolled.

## Decisions (each with the alternative reading, per brief-base §2)

**D1 — per-report drain instead of the reference's "clear at setup, `pytest.fail` at teardown" fixture.**
The reference's autouse function fixture called `_attempts.clear()` at setup. Higher-scoped fixtures set up BEFORE a function-scoped autouse fixture, so a swallowed attempt in a module- or session-scoped fixture was discarded — a false clear. Likewise a session fixture's teardown runs after the last function fixture's teardown, so its attempts were never checked. The chosen mechanism wraps `pytest_runtest_makereport`: every phase's report drains what was recorded during that phase. Fixture setup/teardown of every scope runs inside some item's setup/teardown phase, so nothing is dropped. A call-phase attempt now yields `FAILED` (outcome `failed`), not a teardown `ERROR` — still accepted by the contract (`failed` or `error`).
Alternative: keep the reference fixture verbatim (contract-satisfying, house idiom of loremaster's #486 fixture). Rejected: it carries the discard defect above.

**D2 — `pytest_make_collect_report` wrapper.** An attempt at a test module's import (collection) would otherwise sit in the record until the FIRST test's setup report drained it, charging an innocent test — the mis-attribution class pin 2d forbids for runtime attempts. With the wrapper it fails that module's collection instead. Untested by the contract. Alternative: drop it (strictly "minimum code") and accept first-test mis-attribution for import-time attempts.

**D3 — skipped / xfailed reports become FAILED.** A test that dials production and then `pytest.skip`s, or is `xfail`-marked (the guard's refusal raises, so xfail would swallow it), still fails; `wasxfail` is removed so junit files it as a failure, not "xfail". A report that already failed keeps its text with the guard's verdict appended (`str(longrepr)` + verdict), so the port is named even when the test failed for another reason. Untested by the contract except the plain passed→failed and already-failed (raise) cases.

**D4 — refusal shape.** `connect` raises `ConnectionRefusedError(ECONNREFUSED, …)` (an `OSError`, as a closed port would); `connect_ex` returns `ECONNREFUSED`. Code under test sees "nothing listening", the true state a test should find; the recorder, not the exception, carries the verdict. Alternative: a non-`OSError` (e.g. `BaseException`) to escape swallowing — the contract (2b) shows that alone is insufficient, and it would crash code paths that legitimately handle a down store.

**Port constant.** `PRODUCTION_STORE_PORT = 18500`, one literal, comment cites `_scaffold_lore_yaml` (ruling "Port literal").

## Gates

| # | command (abridged; every pytest under `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0`) | result | EXIT |
|---|---|---|---|
| G1 | `cd skills/lore-deploy/scripts && uv run python -m pytest -q ../tests/test_prod_store_guard.py --timeout=300 -p no:cacheprovider -rfEs` | **31 passed in 8.65s**; 0 FAILED/ERROR/SKIPPED; ImportError 0 | 0 |
| G2 | `cd skills/lore-deploy/scripts && uv run python -m pytest -q . ../tests -n 8 --timeout=300 -p no:cacheprovider -rfEs` | **202 passed in 15.87s**; ImportError 0 | 0 |
| G3 | repo root `uv run python -m pytest --co -q -p no:cacheprovider` | **14098 tests collected in 16.96s** (= lead baseline 14098); `::` lines 14098; every "error" grep hit is a test NAME, no collection error | 0 |
| G4 | repo root `uv run python -m pytest -q loremaster/tests/test_txn_contention.py -n 4 --timeout=300 -p no:cacheprovider -rfEs` | **22 passed in 6.40s**; guard text in log: 0 | 0 |
| G5a | `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` | typecheck RED_ADJUDICATED (83 residuals, owners packet-58-contract + packet-64b-i-contract — pre-existing, none in `conftest.py`); ruff GREEN; **no RED_ORPHANED**; pytest NOT_RUN (by design of `--legs`) | 1 (the NOT_RUN pytest leg; brief's criterion is RED_ORPHANED 0) |
| G5b | `uv run ruff check conftest.py` | All checks passed! | 0 |
| G5c | `uv run mypy conftest.py` (typecheck.sh does NOT cover a root conftest — residual) | 2 errors (annotation, Deviation 1) → after fix: "Success: no issues found in 1 source file" (run inline) | 1 → 0 |

G4 pick: `test_txn_contention.py` drives `connect_admin` against the live TEST store `:18000` through websockets/asyncio — the exact socket path the guard wraps — in 12 test functions (22 collected), so a false alarm on the test store would show there. Found via lore_search (hit: harness-retry builder receipt naming it as a live `connect_admin` suite) + `grep unique_database|connect_admin`.
Receipt spot-check (me, not the runners): `tail` of g1–g4 logs shows the four count lines above verbatim; `grep -c ImportError` g2/g3 = 0/0. All runner `RAN:` lines matched my commands.

**R2 — post-fix re-run on the FINAL `conftest.py` text** (after the mypy annotation fix): G1 **31 passed in 8.34s**, EXIT=0, 0 FAILED/ERROR/SKIPPED, ImportError 0 · `ruff check conftest.py` All checks passed!, EXIT=0 · currency `--legs typecheck,ruff`: typecheck RED_ADJUDICATED (same 83, same owners), ruff GREEN, no RED_ORPHANED, EXIT=1 only for the by-design NOT_RUN pytest leg · `mypy conftest.py` Success, EXIT=0 (inline). G2–G4 ran on the pre-fix text; the diff between the two is the two wrapper parameter annotations + a comment (backup of the pre-fix text: scratchpad `conftest.pre-mypy-fix.py`), so no behavioural difference.

## Noticed (outside my writable set — flags, not edits)
1. **`scripts/typecheck.sh` does not type-check the root `conftest.py`** (`MEMBERS=(lorerunes lorescribe loresigil loremaster skills docs/eval scripts)`), so the currency typecheck leg is blind to it — a gate whose reach excludes the guard. Exact edit I would make: append `conftest.py` to `MEMBERS` (mypy accepts a file root), after checking the script's member-derivation check (its comment line `python3 -c 'import re,tomllib;…'`) does not assume every entry is a directory. Owner: lead.
2. **No contract pin for D1/D2/D3** (session/module-fixture attempts charged, not discarded; collection-time attempts charged to the collector; skip/xfail → FAILED). Each is a plausible wrong build that passes 31/31 (e.g. the reference guard itself, which discards fixture-setup attempts). If kept, they need pins — the contract author's job, not mine.
3. **Port literal pairing** (ruling residual): the scaffold (`_scaffold_lore_yaml`) and this guard carry `18500` independently; plus `scripts/restore_prod_dump.py::PRODUCTION_PORT`, `loremaster/tests/test_harness_database_lifecycle_486.py::_PRODUCTION_STORE_PORT`, `scripts/probe_reanchor_58.py::PRODUCTION_PORT_MARKER`, `scripts/zero_test_store.sh PROD_PORT`, and the defaults `scripts/search_score_survey.py::DEFAULT_SURREAL_URL`, `scripts/snapshot_gc.py::DEFAULT_URL`. Six+ copies of one production coordinate; the ruling ledgers it as residual.
4. **Existing tests the guard newly fails:** none observed in G2 (whole skill suite) and G4. The `18500` sweep found no test that dials the port (all hits are prose, URL-string assertions, or stubbed `_RPC_URL`). The full suite (Phase 5 audit) is the real measurement; NOT RUN by me per brief.
5. **Known bounds, written into the module docstring:** subprocess / C-extension clients; loopback only (re-open: production binds non-loopback); a non-`localhost` hostname passed raw to `sock.connect`; attempts after the last report (still refused, not reported).
6. The `lore_search` "pytest guard … production store port" query at default budget served 1 hit + a floor-of-one stub with 12 elided; at budget 3000, 3 hits including an unrelated `surrealdb-docs` HNSW chunk. Not filed — ranking noise, not a false clear.

## conftest.py (verbatim, final)

```python
"""Repo-wide test guard: no lore test may reach the PRODUCTION SurrealDB store.

THE RULE
--------
"Never point tests at :18500" (repo ``CLAUDE.md`` §Deploy; operator ruling 2026-10-31, packet #165,
``docs/plans/v2/receipts/2026-10-31-165/RULING-guard-forks.md``). This conftest sits at the repo root
because no workspace member carries its own pytest configuration: the root ``pyproject.toml`` is the
rootdir and configfile for every suite, so this file loads for loremaster, lorescribe, loresigil,
lorerunes, ``scripts``, ``docs/eval`` and both ``skills/lore-deploy`` trees alike, in every xdist worker.

HOW
---
1. At import, :class:`ProductionStoreGuard` wraps ``socket.socket.connect`` and
   ``socket.socket.connect_ex``. A connection to a loopback address on :data:`PRODUCTION_STORE_PORT`
   never leaves the process: ``connect`` raises :class:`ConnectionRefusedError` and ``connect_ex``
   returns ``ECONNREFUSED``, exactly as if nothing listened there. Every other address passes through
   untouched. ``urllib``, ``socket.create_connection``, asyncio and websockets all reach the socket
   through ``connect``, so one layer covers them.
2. Every refused attempt is RECORDED. Each report pytest makes (a collector's collect report; a
   test's setup, call and teardown reports) drains the record, and a non-empty drain turns that report
   into a failure naming the node and every attempt. So the test fails even when the code under test
   swallows the refusal: ``lore_deploy._probe_surreal_health`` catches every ``OSError``, and
   ``connect_ex`` never raises at all. Draining per report, rather than clearing at test setup, keeps
   an attempt made in a module- or session-scoped fixture: it is charged to the test whose setup or
   teardown ran that fixture, not discarded.

THREAT MODEL
------------
This catches the HONEST developer whose test or fixture defaults to the production URL. The #165 T8
fake did exactly that: the skill's scaffold writes ``ws://127.0.0.1:18500/rpc`` into every new
``lore.yaml``, so a fake that falls back to the scaffold's value dials production. It is NOT a security
boundary: anyone who can commit here can already ship anything.

KNOWN BOUNDS (each with its re-open trigger)
--------------------------------------------
* Subprocess and C-extension clients (``curl``, ``podman exec … surreal``, a C library opening its own
  socket) never call Python's ``socket.socket`` and are invisible to this guard. Re-open trigger: a
  test that shells out to a store client, or a C-extension store driver.
* Loopback only (``127.0.0.0/8``, ``::1``, the hostname ``localhost``). Production listens on
  ``127.0.0.1:18500`` only (measured: lore-surreal runs ``Network=host``). Re-open trigger: production
  binds a non-loopback address.
* A hostname other than ``localhost`` that resolves to loopback (e.g. this box's own name) is
  recognised only when the client resolves it before connecting, as ``create_connection``, ``urllib``,
  asyncio and websockets do; a raw ``sock.connect(("<hostname>", port))`` resolves inside the C call
  and passes. Re-open trigger: a test that connects to the store by machine hostname.
* An attempt made after the last test's teardown report (a plugin's ``pytest_sessionfinish``) is
  still refused, so production is never reached, but no report remains to fail.
"""

from __future__ import annotations

import errno
import ipaddress
import socket
import threading
from collections.abc import Generator
from typing import Any

import pytest

# The PRODUCTION lore-surreal store's port. Source of truth: the URL the skill scaffolds into every new
# ``lore.yaml``, ``_scaffold_lore_yaml`` in ``skills/lore-deploy/scripts/lore_deploy.py``
# (``url: ws://127.0.0.1:18500/rpc``). Production code must not import a conftest, so this constant
# cites the scaffold rather than being read by it (ruling: RULING-guard-forks.md, "Port literal").
PRODUCTION_STORE_PORT = 18500

# The one loopback NAME the guard recognises; numeric loopback addresses are decided by ``ipaddress``.
LOOPBACK_HOSTNAME = "localhost"

# Index of the port in an AF_INET ``(host, port)`` / AF_INET6 ``(host, port, flowinfo, scope_id)`` tuple.
_ADDRESS_HOST_INDEX = 0
_ADDRESS_PORT_INDEX = 1

# What ``connect_ex`` reports for a refused attempt: the errno a closed port answers with.
REFUSED_ERRNO = errno.ECONNREFUSED

# Labels that name which socket door an attempt came through, in the failure text.
_CONNECT_DOOR = "socket.connect"
_CONNECT_EX_DOOR = "socket.connect_ex"

# How a report with no node id (the session's own collect report) is named in the failure text.
_SESSION_NODE_LABEL = "the pytest session (outside any test)"


class ProductionStoreGuard:
    """Refuse and record every connection this process makes to the production store.

    One instance per test process (see :data:`PRODUCTION_STORE_GUARD`). The socket side
    (:meth:`install`) refuses and records; the pytest side (:meth:`charge`) turns a report into a failure
    when attempts were recorded since the previous report.
    """

    def __init__(self, production_port: int) -> None:
        """Remember the port to refuse and the socket methods this guard wraps.

        Args:
            production_port: The production store's port; connections to it on loopback are refused.
        """
        self._production_port = production_port
        self._attempts: list[str] = []
        # Background threads (a server a test started, an asyncio loop thread) may connect while the
        # main thread drains, so the record is locked.
        self._lock = threading.Lock()
        self._real_connect = socket.socket.connect
        self._real_connect_ex = socket.socket.connect_ex

    def targets_production(self, address: object) -> bool:
        """Say whether a socket address is the production store: loopback host, production port.

        Args:
            address: The address handed to ``connect`` / ``connect_ex``; a UNIX path or any shape other
                than an inet tuple is never the production store.

        Returns:
            ``True`` when the address is ``localhost`` or a loopback IP on the production port.
        """
        if not isinstance(address, tuple) or len(address) <= _ADDRESS_PORT_INDEX:
            return False
        if address[_ADDRESS_PORT_INDEX] != self._production_port:
            return False
        host = address[_ADDRESS_HOST_INDEX]
        if not isinstance(host, str):
            return False
        if host.lower() == LOOPBACK_HOSTNAME:
            return True
        try:
            return ipaddress.ip_address(host).is_loopback
        except ValueError:
            # A hostname other than localhost: not resolved here (KNOWN BOUND, module docstring).
            return False

    def _record(self, door: str, address: object) -> str:
        """Record one refused attempt and return the refusal's text.

        Args:
            door: Which socket method the attempt came through.
            address: The address it tried to reach.

        Returns:
            The text the refusal carries, naming the address and the production port.
        """
        with self._lock:
            self._attempts.append(f"{door} {address!r}")
        return (
            f"production-store guard refused {door} to {address!r}: port {self._production_port} is the "
            f"PRODUCTION lore-surreal store, and tests must never reach it (CLAUDE.md §Deploy)"
        )

    def drain(self) -> list[str]:
        """Return every attempt recorded since the last drain, and forget them.

        Returns:
            The recorded attempts, oldest first; empty when none were made.
        """
        with self._lock:
            attempts, self._attempts = self._attempts, []
        return attempts

    def install(self) -> None:
        """Wrap ``socket.socket.connect`` and ``connect_ex`` so production attempts are refused."""
        guard = self

        # ``sock`` is ``Any``: the wrapped method lives on ``socket.socket`` but typeshed types it on the
        # private C base, so any narrower annotation is a false variance error.
        def guarded_connect(sock: Any, address: Any) -> None:
            """``socket.socket.connect``, refusing (and recording) the production store."""
            if guard.targets_production(address):
                raise ConnectionRefusedError(REFUSED_ERRNO, guard._record(_CONNECT_DOOR, address))
            guard._real_connect(sock, address)

        def guarded_connect_ex(sock: Any, address: Any) -> int:
            """``socket.socket.connect_ex``, refusing (and recording) the production store."""
            if guard.targets_production(address):
                guard._record(_CONNECT_EX_DOOR, address)
                return REFUSED_ERRNO
            return guard._real_connect_ex(sock, address)

        socket.socket.connect = guarded_connect  # type: ignore[method-assign]
        socket.socket.connect_ex = guarded_connect_ex  # type: ignore[method-assign]

    def charge(self, report: pytest.CollectReport | pytest.TestReport) -> None:
        """Fail ``report`` if production was attempted since the previous report; else leave it alone.

        A report that would have passed or been skipped (``xfail`` included) becomes a failure: an
        attempt on production is never an expected outcome. A report that already failed keeps its own
        text, with the guard's appended, so the failure always names the port.

        Args:
            report: The report pytest just made for the phase in which the attempts happened.
        """
        attempts = self.drain()
        if not attempts:
            return
        node = report.nodeid or _SESSION_NODE_LABEL
        verdict = (
            f"{node} attempted the PRODUCTION SurrealDB store (loopback port {self._production_port}) "
            f"{len(attempts)} time(s); each was refused before it left the process, but tests must "
            f"never point at :{self._production_port} (CLAUDE.md §Deploy). Attempts: {'; '.join(attempts)}"
        )
        if report.failed:
            report.longrepr = f"{report.longrepr}\n\n{verdict}"
            return
        report.outcome = "failed"
        report.longrepr = verdict
        # The skipping plugin marks an xfailed test with ``wasxfail``; left in place, junit would
        # file this failure as an xfail.
        report.__dict__.pop("wasxfail", None)


PRODUCTION_STORE_GUARD = ProductionStoreGuard(PRODUCTION_STORE_PORT)
PRODUCTION_STORE_GUARD.install()


@pytest.hookimpl(wrapper=True)
def pytest_make_collect_report(
    collector: pytest.Collector,
) -> Generator[None, pytest.CollectReport, pytest.CollectReport]:
    """Charge an attempt made while collecting (e.g. at a test module's import) to that collector."""
    report = yield
    PRODUCTION_STORE_GUARD.charge(report)
    return report


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    """Charge an attempt made during a test's setup, call or teardown to that phase of that test."""
    report = yield
    PRODUCTION_STORE_GUARD.charge(report)
    return report
```
