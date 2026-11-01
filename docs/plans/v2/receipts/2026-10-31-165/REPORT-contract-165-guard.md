# REPORT-contract-165-guard

brief-base v24 read · brief project v7 read (lore_comms register, session fix-165-2026-10-31)

## Summary
- **State:** done-with-deviations.
- **Deviations:**
  1. The contract does not use the `pytester` fixture. It runs inner sessions with `subprocess` and parses junit XML. Reasons: pytester's in-process mode would run inner tests in the OUTER process, which is forbidden. Its subprocess mode cannot enter a network namespace without `pytester.run`, which is just subprocess anyway. And it is function-scoped, so each outer test would cost an inner run. As a side effect the file needs no `-p pytester`, so it also passes under the root `testpaths` run and the in-image conformance run. The RED command therefore dropped `-p pytester`.
  2. The scratch copy (step D1) was first DENIED by the permission layer on its `rm -rf` prefix. I re-ran it without the `rm`, and it went through, EXIT=0.
  3. Runs used: 5 (RED ×2, satisfiability ×2, plus ruff). The extra two have one reason. Satisfiability run 1 exposed a defect in MY contract: junit writes a second `<testcase>` when a test's call fails AND its teardown errors, and my parser asserted uniqueness, so a correct build got 30 setup errors. Fixed by merging duplicates, worst outcome first. RED was re-run to show the fix changed nothing at HEAD.
- **Packages considered:** run-time network blocking → `pytest-socket` (I read the installed source via `uv run --with pytest-socket`: the `--allow-hosts` help says "Only allow specified hosts through socket.socket.connect((host, port))", plus `host_from_address`, `SocketConnectBlockedError(RuntimeError)`) → `bespoke` for the PORT gap. It filters by host, not port: allowing 127.0.0.1 lets :18500 through, and blocking it breaks :18000 and the existing loopback port-probe tests. It also records nothing, so it misses an `except BaseException` swallow. MEDIUM: I read the help text and symbol names, not the full source. Inner-run isolation → `os.unshare` (stdlib, probed live) → `replace` (no `unshare(1)` / `ip(8)` dependency).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none. The file defines only test-private helpers (`_mirror_repo`, `_run_inner`, `_parse_junit`, `InnerRun`/`InnerCase`) and decides no production rule.
- **Graded:** n/a (contract author; no verdict on another artifact). HEAD at writing: `14372d1`.
- **RED (before any guard, at `14372d1`):** 18 failed / 13 passed / 31, EXIT=1, no ImportError. This matches the prediction exactly (§RED).
- **SATISFIABILITY** (reference guard at `<scratch>/skills/lore-deploy/conftest.py`): the whole skill suite `. ../tests` at `-n 8` → **202 passed, 0 failed**, EXIT=0, no ImportError/ERROR/SKIPPED (171 existing + 31 contract). So the guard false-alarms on nothing in the existing suite. `loremaster.__file__` = `/var/tmp/claude-1000/guard-scratch/loremaster/loremaster/__init__.py`. The contract file is byte-identical to the repo copy (`cmp`).
- **ruff:** RUFF_EXIT=0, "All checks passed!" (after a formatting-only fix; §Runs).
- **Chokepoint:** `skills/lore-deploy/conftest.py`. It does not exist today, and no conftest exists anywhere under `skills/` (§Chokepoint).
- **Decisions needed:**
  1. In-image conformance runs this file (`-n auto` over `testpaths`, which includes `skills/lore-deploy`). If the image forbids user namespaces, every test here SKIPS with a named reason rather than running un-isolated. Accept the skip, or require the namespace? (§Forks F1)
  2. Should the guard cover only loopback :18500, or :18500 on any host? The contract pins loopback and stays silent on other hosts. (§Forks F2)
  3. Should the guard live at the repo-root conftest instead (guarding all of lore's suites, a wider scope)? (§Chokepoint)
- **Pointers:** §Routing · §Design: isolation · §Pins · §Chokepoint · §Runs · §Pre-flight · §Realism · §Noticed

## Routing table (written before the first sweep)

| step | tier | who | reason |
|---|---|---|---|
| A. lookups: t8 plugin, t8 report §Prod-URL fix, `_probe_surreal_health`, pytest config | 1 (parallel batch) | self, ONE batch of 5 calls | small set (5 targets), output feeds the contract design directly and I read all of it |
| A'. conftest discovery `pytest --co` | 1 | self, in batch A | collect-only, ~3 lines needed (rootdir, configfile); critical path for the chokepoint |
| B. pins | 3 | self | contract design |
| C. RED run | 1 | haiku-runner | brief routes it |
| D1. scratch_copy | 1 | haiku-worker ×2 (1st DENIED on `rm -rf`) | brief routes it |
| D2. reference guard in scratch | 3 | self | reference build |
| D3. satisfiability run | 1 | haiku-runner | brief routes it |
| E. ruff | 1 | haiku-runner ×2 (pre/post fix) | brief routes it |
| extra: netns feasibility probes (`unshare -rn`, `os.unshare`) | 1 | self, inline | 2 one-line probes on the critical path of the central design decision |

Fan-out: haiku 6 · sonnet 0 · peak 3

## Design: isolation (the design point the brief said to raise first, raised and resolved)
**Problem.** With no guard (RED), an inner test that dials 127.0.0.1:18500 would reach the production store, which is up. A substitute port that the guard "also honours" would weaken pin 1 ("names :18500") and would add a test-only configuration knob to a safety guard.

**Resolution.** Every inner session runs in a private user+network namespace:
- The bootstrap `_BOOTSTRAP` calls `os.unshare(CLONE_NEWUSER|CLONE_NEWNET)`, writes the uid/gid maps, and brings `lo` up via `SIOCSIFFLAGS`. Only then does it exec pytest.
- Inside that namespace, 127.0.0.1:18500 is a STUB HTTP store that the inner module starts itself. The production store is unreachable by construction.
- Probed live 2026-10-31 at `14372d1`:
  - host netns `net:[4026531833]`, inner `net:[4026534957]`;
  - `connect_ex(("127.0.0.1", 18500))` inside the namespace = 111 (refused; nothing there).
- Two fail-closed checks:
  - the bootstrap prints `NETNS host=… inner=…` and exits 77 if the namespace is unchanged; the outer test asserts the two values differ;
  - each inner module calls `pytest.exit(returncode=99)` if its netns equals the host's.
- If the namespace cannot be built, the outer test SKIPS with the reason. It never runs un-isolated.

**Why a stub, not a dead port.** With a stub, every door test PASSES when no guard exists, so a RED can only mean the guard is absent. A dead port would make the raw-connect test fail with or without a guard, so it could not discriminate. A CONTROL session (conftests off: `--noconftest`, `-o addopts=--import-mode=importlib`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`) proves that every inner test passes unguarded. That control is green at RED and green at the reference build.

**Why the port is never written in inner sources.** Inner tests read the port from `GUARD_CONTRACT_PROD_PORT`. So `18500` in a failure's text can only come from the guard naming the attempt, never from pytest echoing a source line.

## Pins → the wrong guard each one catches

The inner sessions run over a MIRROR of the repo:
- every `conftest.py` and non-`test_*` `.py` helper on the path `<repo>/skills/lore-deploy/{scripts,tests}` is symlinked to the real file;
- the real `pyproject.toml` is symlinked too.

So the inner sessions load whatever conftest chain production has. The contract does not name a file.

| pin (outer test) | inner door | wrong guard it catches |
|---|---|---|
| 1 `test_raw_socket_connect_fails_and_names_the_port[scripts,tests]` | `socket.socket.connect(("127.0.0.1", P))` | no guard; a guard only on `urlopen` / `_probe_surreal_health` (the t8 upper layers alone); a guard whose failure omits the port |
| 2a `…swallows…[test_swallow_production_probe_surreal_health]` | REAL `lore_deploy._probe_surreal_health` (swallows `OSError`) | **raise-only guard** (the brief's named class); a guard raising an `OSError` subclass |
| 2b `…[test_swallow_any_exception_around_create_connection]` | `except BaseException: pass` | a guard that escapes swallowing by raising `pytest.fail`/`BaseException` but does not RECORD |
| 2c `…[test_swallow_by_construction_connect_ex]` | `socket.connect_ex` (never raises) | a guard patching `connect` but not `connect_ex` (a separate C method); patching `connect` alone does not reach it |
| 2d `test_failure_lands_on_the_attempting_test_not_its_neighbour` | a no-network test after the swallowers | a recorder checked in the NEXT test's setup or at session end; a guard that fails everything once tripped |
| 4 `test_urlopen_health_fails_and_names_the_port[loopback_ip, localhost]` | `urlopen("http://127.0.0.1:P/health")`, `urlopen("http://localhost:P/health")` | a URL-string guard keyed on `127.0.0.1` that misses `localhost`; no guard |
| 3 `TestOtherPortsAreUntouched` ×3 doors ×2 trees | dead port 9 → `ConnectionRefusedError` unchanged; test store :18000 via `urlopen` and via `localhost` socket | an over-broad guard (blocks all loopback, a port range, all network); a guard that rewrites exception types; compared with the no-guard CONTROL outcome |
| 5 `[scripts]` / `[tests]` parametrisation on all of the above | same modules placed under each tree | a guard in `scripts/conftest.py` or `tests/conftest.py` only (loaded for one tree) |
| xdist `TestGuardIsLiveInEveryXdistWorker` ×6 doors + 4 benign | the `tests` tree under `-n 2` | a recorder that keeps hits in controller memory and fails at `sessionfinish` (blind to workers); lore runs `-n 8` |
| control `test_every_inner_test_passes_without_a_guard` | all inner tests, conftests off | a broken fixture or stub (proves each RED is the guard's absence); a guard installed OUTSIDE conftest/addopts (sitecustomize/.pth), which would also arm the deploy CLI |

"FAIL" accepts outcome `failed` OR `error` (a teardown error) on the attempting testcase in the junit report. I read the brief's "FAIL loudly, naming the test" as "this test's verdict is not pass, and the verdict is attributed to it". The alternative reading (strictly `failed`) would force a `makereport` hook mechanism. Pick: the looser one, written down here per brief-base §2.

**Doors deliberately not pinned (scoped out, each with its reason):**
- subprocess clients (`curl`, `podman exec … surreal`): a Python-level guard cannot see them. This is a KNOWN BOUND for the implementer to pin or ledger.
- C-extension sockets: same reason.
- asyncio / websockets (`ws://…:18500/rpc`): these go through `socket.socket.connect` / `sock_connect`, so pin 1's layer covers them transitively; no separate pin.
- UDP / `sendto`: no store protocol uses it.

## Chokepoint: `skills/lore-deploy/conftest.py`
Derivation, measured 2026-10-31 at `14372d1`:
- `uv run python -m pytest --co -p no:cacheprovider . ../tests` from `skills/lore-deploy/scripts` printed `rootdir: /home/ejprice/PycharmProjects/lore` and `configfile: pyproject.toml`, and collected 171 tests (EXIT=0).
- `find skills/lore-deploy -name conftest.py` → 0 files.
- `git ls-files | grep conftest.py` → only `loremaster/tests/`, `lorescribe/tests/`, `loresigil/tests/` (1613 files listed).
- So today NO conftest loads for either skill tree.
- pytest loads every `conftest.py` in the directories from the rootdir down to each collected file's directory. `skills/lore-deploy/` is the deepest directory that is an ancestor of both `scripts/` and `tests/`.
- The root `testpaths` includes `skills/lore-deploy` (pyproject `[tool.pytest.ini_options]`), so the same conftest also loads under the full suite. It also loads under the in-image conformance run (`conformance_run.sh`: `pytest -n auto` over the mounted `/workspace`). For conformance this is MEDIUM: I read the runner's pytest line, but I did not verify that the mount carries the file.
- Alternatives:
  - `scripts/` or `tests/` alone covers one tree (pin 5 RED);
  - the repo-root `conftest.py` covers both, but it arms the guard for every lore suite. That is arguably right under the global law "never point tests at :18500", but it widens scope: an operator question (decision 3).
- The t8 plugin must NOT be ported verbatim:
  - it does `Path(os.environ["T8_GUARD_DIR"])` at import, so it raises KeyError without that env var;
  - its URL layer uses the substring test `f":{PROD_PORT}" in url`;
  - its four layers are redundant: `socket.socket.connect` already sits under `create_connection` and `urlopen`, and `connect_ex` is the one distinct door.

## Runs
| label | command (abridged) | result |
|---|---|---|
| RED at HEAD `14372d1` | `cd skills/lore-deploy/scripts && systemd-run … MemoryMax=16G … uv run python -m pytest -q ../tests/test_prod_store_guard.py --timeout=300 -p no:cacheprovider -rfEs` → `/var/tmp/claude-1000/guard-red.log` | **18 failed, 13 passed in 10.01s**, EXIT=1, no ImportError or collection error. All 18 say "reached the production port and the guard did not fail it (outcome=passed)": 6 doors × 2 trees + 6 doors under xdist. Green: control 1, neighbour ×2, benign 3×2, xdist benign 4 = 13. |
| ruff #1 | `uv run ruff check …test_prod_store_guard.py` | RUFF_EXIT=1: 8× E501, 1× PLR0402. Fixed by reformatting only (line wraps, `from xml.etree import ElementTree`). The RED run read the pre-reformat text; the fix is token-identical in logic. |
| ruff #2 | same | RUFF_EXIT=0, "All checks passed!" |
| scratch | `./scripts/scratch_copy.sh /var/tmp/claude-1000/guard-scratch` | EXIT=0; `loremaster -> /var/tmp/claude-1000/guard-scratch/loremaster/loremaster/__init__.py` (all 4 members inside the copy) |
| SAT #1 (reference guard) | `cd <scratch>/skills/lore-deploy/scripts && LORE_PYTHON=<scratch>/.venv/bin/python systemd-run … pytest -q . ../tests --timeout=300 -p no:cacheprovider -n 8 -rfEs` → `guard-sat.log` | 172 passed, 30 errors, all `AssertionError: inner test test_door_raw_socket_connect reported twice` in MY `_parse_junit` (a contract defect; deviation 3) |
| SAT #2 (after the parser fix) | same → `/var/tmp/claude-1000/guard-sat2.log` | **202 passed in 15.82s, EXIT=0**, 0 ERROR/SKIPPED/ImportError; `LOREMASTER_FILE=/var/tmp/claude-1000/guard-scratch/loremaster/loremaster/__init__.py` |
| RED #2 at `14372d1` (after the parser fix) | as RED → `/var/tmp/claude-1000/guard-red2.log` | **18 failed, 13 passed in 10.00s**, EXIT=1; by label (grep of `E` lines): `[scripts]` 6 · `[tests]` 6 · `[xdist]` 6 |

Reference guard (the satisfiability build, pasted verbatim per brief-base §1; it lived only at `/var/tmp/claude-1000/guard-ref/conftest.py` and at `<scratch>/skills/lore-deploy/conftest.py`): see §Reference guard.

## Adversarial pre-flight
- **Wrong unit/scale:** the port is an int; the address tuple carries `int` 18500, a URL carries `":18500"`. Covered by both the socket doors and the URL doors.
- **Wrong anchor (host form):** `127.0.0.1` vs `localhost` (resolves to `::1` then `127.0.0.1`). Pin 4 localhost and benign localhost:18000.
- **Sign/null/zero/boundary:** port 0/negative are not realistic connection targets → scoped out. The neighbouring port :18000 is pinned (pin 3).
- **Empty / degenerate driver:** a namespace without `lo` up would make every door fail with ENETUNREACH even unguarded → the control leg proves the stub answers. A namespace that silently did not change → NETNS receipt + inner `pytest.exit`.
- **Real-distribution tails:** the real prod URL shape `ws://127.0.0.1:18500/rpc` is a websocket over `socket.connect`, covered by pin 1's layer (not separately pinned; see doors not pinned).
- **Producer↔consumer seam:** config (scaffold URL) → `_probe_surreal` → `_probe_surreal_health` → `urlopen` → socket. Pin 2a drives the REAL production function at that seam.
- **Swallowed errors:** pins 2a–2c (`OSError`, `BaseException`, errno return).
- **Process topology:** xdist workers (pinned); subprocesses (scoped out, KNOWN BOUND).
- **Quantifier:** the invariant is stated over every test that attempts :18500, regardless of door or of whether the error escapes. It is not conditioned on the `_probe_surreal_health` swallow that prompted the work.

## Realism & independence
- ☑ Production-realistic inputs: the real prod port, the real `/health` path, the real production `_probe_surreal_health`, the real conftest chain and pyproject (symlinked), and the real xdist topology (smaller `-n`).
- ☑ Independent expected values: the expectations come from the brief's requirement, never from a guard (none existed). The control leg is a measured no-guard baseline.
- ☑ Seam coverage: pin 2a crosses lore_deploy → urllib → socket with production code.
- ☐ Magnitude bound: not applicable because no numeric output is derived.
- ☑/partial Shared conventions: PROD/TEST ports are named constants citing CLAUDE.md §Deploy and `_scaffold_lore_yaml`. Production has no importable port constant (18500 appears only inside the scaffold's template string), so the contract cannot import one. NOTICED below.
- Hostile rendered text: not applicable (nothing renders stored free text).
- Input accounting: not applicable as a transform. The closest analogue is that the parser asserts the inner junit set equals the declared inner set exactly (no test silently missing or extra).

## Forks
- **F1.** If user namespaces are unavailable (possibly in the conformance container), the file SKIPS with a named reason. Reading A: skip (my pick; a contract that cannot run safely must not run). Reading B: fail (forces the image to support it, and goes red on any host without userns). Lead/operator call.
- **F2.** Loopback-only vs any-host :18500. The reference guards loopback (`127.0.0.0/8`, `::1`, `localhost`). Nothing pins remote hosts either way.

## Noticed (outside this change)
- `REPORT-contract-165-t8.md` §Prod-URL fix: the t8 report itself records that whether any PRE-fix t8 run sent a real `GET /health` to production is UNPROVEN (its port-9 control was denied). Still open.
- 18500 has no named constant in `lore_deploy.py` (it appears only in the scaffold template). The guard implementer will introduce a second literal. Candidate: one constant both the scaffold and the guard read.
- The permission layer denied `rm -rf /var/tmp/claude-1000/guard-scratch && ./scripts/scratch_copy.sh …` for a haiku-worker; the same command without `rm` was allowed.

## Reference guard (verbatim; satisfiability build only — not the implementation)

```python
"""REFERENCE guard (satisfiability build for test_prod_store_guard.py; not the implementation).

Blocks AND records every socket connection to loopback port 18500 (the PRODUCTION
lore-surreal store) made by any test under skills/lore-deploy, and fails that test at
teardown even when the code under test swallowed the block.
"""

from __future__ import annotations

import errno
import ipaddress
import socket
from typing import Any

import pytest

PROD_STORE_PORT = 18500
_attempts: list[str] = []
_real_connect = socket.socket.connect
_real_connect_ex = socket.socket.connect_ex


def _is_prod(address: Any) -> bool:
    if not (isinstance(address, tuple) and len(address) >= 2 and address[1] == PROD_STORE_PORT):
        return False
    host = str(address[0])
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _guarded_connect(self: socket.socket, address: Any) -> Any:
    if _is_prod(address):
        _attempts.append(f"socket.connect {address!r}")
        raise OSError(f"prod_store_guard: blocked connection to PRODUCTION store {address!r} (port {PROD_STORE_PORT})")
    return _real_connect(self, address)


def _guarded_connect_ex(self: socket.socket, address: Any) -> int:
    if _is_prod(address):
        _attempts.append(f"socket.connect_ex {address!r}")
        return errno.ECONNREFUSED
    return _real_connect_ex(self, address)


socket.socket.connect = _guarded_connect  # type: ignore[method-assign]
socket.socket.connect_ex = _guarded_connect_ex  # type: ignore[method-assign]


@pytest.fixture(autouse=True)
def _fail_on_production_store_attempt(request: pytest.FixtureRequest):
    _attempts.clear()
    yield
    if _attempts:
        seen = "; ".join(_attempts)
        _attempts.clear()
        pytest.fail(f"{request.node.nodeid} attempted the PRODUCTION store (port {PROD_STORE_PORT}): {seen}", pytrace=False)
```
