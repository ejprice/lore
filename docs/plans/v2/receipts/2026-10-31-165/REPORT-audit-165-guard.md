brief-base v24 read
brief project v7 read

# REPORT — audit-165-guard (tdd-light Phase 5 REFACTOR+AUDIT, #165 production-store guard)

## SUMMARY (2026-10-31, closed 15:40 EDT, inside the 90-min deadline; every brief item attempted, none NOT TRIED)
- **State: done-with-deviations. Verdict:**
  - **GO for the guard code.** All 41 contract pins and 212 skill tests pass on the fixed build; the mutations held (M1, M2 on re-run, M4); sharing is proven (M5).
  - **NO-GO for packet close.** The full suite has 2 reds attributable to the guard build: `gated_ground` LEG B, which needs D-2, outside my writable set. The contract also has a measured flake (C6) and leaves my fixes unpinned (D-3).
- **Deviations:**
  - (1) I widened guard BEHAVIOUR, not only nits, under the brief's residual-(a) licence, closing the whole class: aliases, plus the **HIGH B7 `0.0.0.0`/`::` open door**, plus bytes hosts.
  - (2) The B3 failure text now reads "were made while <node> ran its <when> phase".
- **Findings:**
  - BUILD: B1 DRY copy of `lorerunes.posture.host_is_loopback` (FIXED, routed) · B2 alias door (FIXED) · **B7 HIGH `0.0.0.0`/`::` reach production (FIXED)** · B3 verdict over-claims its author (FIXED).
  - CONTRACT (ROUTED, not patched): C1 hostname branch unpinned · C2 port literal drift · C3 refusal pinned only indirectly · C4 `::1` unpinned · C5 no `0.0.0.0` door · **C6 xdist leg flaky, 2/20 at HEAD and 3/20 final**.
- **Residuals:** (a) CLOSED as a class (§2/§3; probe HEAD `FAIL (5)` → edit `PASS`). (b) KNOWN BOUND with re-open trigger: xdist drops a worker's late exit status (`worker_workerfinished` reads only `== 2`), so a closure would be half (§2).
- **Typecheck rider:** scratch red leg prints `typecheck: conftest.py FAILED` (conftest.py:271 assignment); real tree prints `typecheck: conftest.py OK` (§4).
- **Mutation, declared vs observed:**
  - M1: 3/3 exact.
  - M2: 3 declared; the first run went 4 red (the extra was the C6 flake); the re-run was 3/3 exact.
  - M3: ∅ declared, 41 passed (gap proof).
  - M4: 1/1 exact.
  - M5 sharing: 27 red.
  - `loremaster.__file__` resolved inside the scratch copy (§6).
- **Full suite:** `533 failed, 13505 passed, 67 skipped, 3 xfailed in 767.52s`. vs the 530 baseline: NEW 3 (2 gated_ground LEG B, attributable; 1 C6 flake), GONE 0. **0 guard verdicts, 0 tests touching :18500** (§7).
- **Gates:** contract 41 passed · skill 212 passed · typecheck `conftest.py OK` (other reds adjudicated) · currency RED_ORPHANED 0 · ruff conftest clean. The brief's literal ruff command lints the `.sh` as Python: 96 errors at this tree, 93 at HEAD (§8).
- **Packages considered:** `pytest-socket`: not re-litigated (impl + ruling excluded it: host filter, no recorder). stdlib `socket.getaddrinfo` / `ipaddress.is_unspecified` → used.
- **Odoo-20 portability:** n/a (no Odoo seam touched).
- **Reuse ledger:** 3 new symbols, all dispositioned. `_reaches_loopback` REUSED `host_is_loopback` (§5).
- **Graded:** c99210b · HEAD-at-report: c99210b · SAME (my edits are uncommitted on top: `conftest.py` md5 `f31db77b`, `scripts/typecheck.sh` md5 `21669bd9`).
- **Findings filed:** #566 (gated_ground LEG B ancestor conftest) · #567 (contract xdist flake C6).
- **Decisions needed:** D-1 lowercase in the shared predicate? (recommend no) · **D-2 gated_ground LEG B: ancestor conftest rule (packet blocker)** · D-3 contract pins C1/C2/C3/C5/C6. Pointers: §1 findings, §2 residuals, §3 fixes + probe, §6 mutations, §7 suite, §9 decisions.
- **Fan-out:** haiku 12 (10 runners + 2 workers) · sonnet 0 · peak 4. All tier-3 work (review, verdicts, attributions) was done by me.

## Capability check
- Demanded: lore tools, Agent (haiku-runner/haiku-worker), Bash, Edit/Write in writable set, scratch_copy.sh, mutation_proof.py, flock/systemd-run. All available (lore loaded via ToolSearch, registered on lore_comms session fix-165-2026-10-31).
- Idle-gate contract written as `/tmp/claude-idle-gate-lore/unknown-audit-165-guard.contract` — my harness session id is not visible to me, so I used the `unknown-` prefix sibling agents used.
- Operator grant for audit+fix quoted in brief with date (2026-09-27, "Keep it") → brief-base §2 ROLE BOUNDARY exception satisfied. No BRIEF CONFLICT.

## Routing table (written before the first sweep — brief-base §3)
| step | tier | who | reason |
|---|---|---|---|
| Cold read of conftest.py + contract + rulings, judgment of quality/coverage | 3 | self | audit verdicts; an error here seals itself |
| Prior-art / reuse searches (lore_search, ~4 queries) | 1-batch | self, one parallel batch | small, output read in full, feeds my verdict |
| Contract gate, skill-suite gate, typecheck, ruff, currency runs | 1 | haiku-runner | test runs; I read RAN: + count line |
| Make scratch copy (`scratch_copy.sh`) | 1 | haiku-worker | one exact command, provenance line returned |
| Typecheck rider (inject type error in scratch conftest, run scratch typecheck) | 1 | haiku-worker | exact edit + exact command; I read output |
| Mutation runs (`mutation_proof.py`) | 1 run / 3 verdict | haiku-runner runs, self judges | declared set fixed by me from --collect-only before run |
| Full suite (once, flock'd, -n 12) | 1 | haiku-runner (background) | long log; I read count line |
| Full-suite set diff vs 530 baseline | 1-batch | self (one `comm` command) | tiny output; attribution of new reds is mine (tier 3) |

## 1. Cold review — findings written BEFORE any edit (graded at `c99210b`, 2026-10-31)

Baseline receipt: contract at HEAD `c99210b` → `41 passed in 20.51s` (haiku-runner; RAN line checked; log `/var/tmp/claude-1000/audit-guard-contract-head.log`).

### Build (`conftest.py`)
| id | sev | where | finding | route |
|---|---|---|---|---|
| B1 | medium (DRY/policy) | `conftest.py::ProductionStoreGuard.targets_production` | **Copy #2 of the loopback policy.** `lorerunes.posture.host_is_loopback` (lorerunes = CLAUDE.md's designated home for shared policy) already decides "is this host loopback": literal `localhost` or `ipaddress.ip_address(host).is_loopback`, fail-closed on `ValueError`. The guard re-implements it inline. Found by `lore_search("is loopback address predicate / localhost host check helper")` → `[SOURCE:lorerunes/lorerunes/posture.py:56]`. The impl's reuse ledger did not list it: its two queries were about the port and the guard mechanism. The one difference: the guard lowercases (`host.lower()`), and `host_is_loopback` is case-sensitive. A guard must fail toward matching, because `getaddrinfo` resolves `LOCALHOST` → 127.0.0.1 (probed). | FIX in place: route to `host_is_loopback(host.lower())`. Do NOT extend `host_is_loopback` to lowercase: that would flip `derive_posture` for a bind host `LOCALHOST` (today refused, fail-closed), which is a STOP-and-ask per §6. Raised as decision D-1. |
| B2 | medium (residual a, live on this box) | `targets_production` | A raw `sock.connect(("localhost.localdomain", 18500))` passes: `/etc/hosts` maps it to 127.0.0.1 (probed: `getaddrinfo` → `['127.0.0.1']`). This is real, not hypothetical. | FIX in place (residual a, below). |
| B3 | low (served-prose over-claim) | `charge` verdict text | The verdict says `"{node} attempted the PRODUCTION SurrealDB store"`. The guard only knows the attempt happened in that report's WINDOW. A background thread started by an earlier test, or another plugin's hook running between reports, gets charged to whichever node reports next, and the text then names an innocent node as the attempter. Trust law: a render must not over-claim. | FIX in place: word the verdict as "made while `<node>` ran its `<when>` phase" (`CollectReport.when == "collect"`, probed). |
| B7 | **HIGH** (open door to production) | `targets_production` | **`0.0.0.0` and `::` reach production and the guard passes them.** Linux routes a `connect()` to the unspecified address to loopback. Probed in a private netns (instrument pasted in §3): with a listener on `127.0.0.1:18555`, `connect_ex(('0.0.0.0', 18555))` → `0 CONNECTED peer=('127.0.0.1', 18555)`; `::` → `::1` likewise. `ipaddress.ip_address('0.0.0.0').is_loopback` is `False`, so `ws://0.0.0.0:18500/rpc` — a BIND address reused as a client URL, the honest-developer shape the threat model names — dials production unrecorded. Same CLASS as residual (a): the guard decides by SPELLING, the kernel by ROUTING. | FIX in place as part of the residual-(a) class closure: a destination is production-bound when it is loopback (shared `host_is_loopback`), unspecified (kernel reroutes to loopback), or a name resolving to either. DISCLOSED as a behaviour-widening deviation; contract pin ROUTED (C5). |
| B4 | info | `targets_production` | IPv4-mapped `::ffff:127.0.0.1` → `is_loopback True` on 3.14 (probed); `requires-python >=3.14`, so it is covered. `127.0.1.1` (this box's `ean`) is also refused on :18500 although production binds 127.0.0.1 only. That is over-match, harmless, and per ruling F2 (127/8). | none |
| B5 | info | `install` | Not idempotent: a second import of the module would double-wrap. Benign, because the outer wrapper records and refuses before the inner one runs. No real double-load path found. | none |
| B6 | info | module | No uvloop in the venv (probed `find_spec("uvloop") is None`). uvloop would be a C-level connect path invisible to the guard. It is covered in general by the existing C-extension KNOWN BOUND. | none |

### Contract (`test_prod_store_guard.py`) — test-smell rejection list
| id | sev | smell | finding | route |
|---|---|---|---|---|
| C1 | **medium** | unrepresentative fixture | **The `localhost` HOSTNAME branch of the guard is unpinned.** Every door passes an IP literal to `connect`: urlopen and `create_connection` resolve `localhost` first. No test does a raw `sock.connect(("localhost", PORT))`, the most plausible honest raw-socket door. Prediction: deleting the `LOOPBACK_HOSTNAME` branch keeps 41/41 green. Proven by run M3 (§6). | ROUTE to contract author: add a raw-socket door by hostname (`localhost`, plus an `/etc/hosts` alias if B2's closure is kept). |
| C2 | medium | drift-prone hardcoded convention | `PROD_STORE_PORT = 18500` (contract) and `PRODUCTION_STORE_PORT = 18500` (conftest) are two literals. Each cites the scaffold, and NOTHING checks either against it. If the scaffold or the quadlet moves, both drift together and the suite stays green while guarding a dead port. CLAUDE.md "any hand-list gets a test that it matches its source of truth". | ROUTE: a pin that `PRODUCTION_STORE_PORT` equals the port in `lore_deploy._scaffold_lore_yaml`'s URL. Better: also check the `lore-surreal` quadlet's bind, which is the real source of truth. |
| C3 | low-medium | magnitude/absence guard (refusal) | "Never leaves the process" (refusal, not just recording) is pinned ONLY indirectly, by `test_no_node_whose_phases_made_no_attempt_is_charged` through `test_skip_fixture_second_user`'s cached-skip expectation. Prediction: a record-only guard (attempt recorded, connection allowed through to the stub) reddens exactly that one pin. Proven by run M4 (§6). And `connect_ex`-only pass-through (record but connect for real) is caught by NO pin: the connect_ex door asserts only the failure, never that the stub saw no connection. | ROUTE: the stub counts accepted connections; guarded runs assert zero. |
| C4 | low | unrepresentative fixture | `::1` and other 127/8 addresses are claimed in the guard docstring and never exercised. Production binds 127.0.0.1 only, so no production route is unguarded by this; it is an unpinned claim. | ROUTE (low): one `::1` door, or drop the claim. |
| C5 | **medium-HIGH** | unrepresentative fixture | No door targets `0.0.0.0` / `::` (B7), so a guard that misses the kernel's unspecified→loopback reroute passes 41/41 (it is the build at HEAD). | ROUTE: a door `urlopen(f"http://0.0.0.0:{PORT}/health")` (the stub on 127.0.0.1 answers it unguarded — control leg free). |
| — | n/a | tautology | none found: every pin reads observed inner outcomes, and both control legs exist and pass. | — |
| — | n/a | no magnitude guard | n/a (no derived number) | — |
| — | n/a | forward-run-as-validation | n/a: pure logic, fixed spec. The data-driven scoring clause does not apply; green tests suffice. | — |

### "What broken state of this guard would still serve a green run?"
1. Guard without the hostname branch → green (C1, proven M3).
2. Guard that records but does not refuse `connect_ex` → green (C3).
3. Guard that refuses but whose wrappers are installed only on `socket.socket` while some client subclasses it with its own `connect`, e.g. `ssl.SSLSocket.connect`. Checked by reading: `SSLSocket.connect` → `self._real_connect` → `super().connect(addr)` → the patched method. Covered. (HIGH: read CPython 3.14 `ssl.py` `SSLSocket._real_connect`/`connect`, `super().connect(addr)`.)
4. A port drift (C2) → green.

## 6. Mutation proof — DECLARED sets (written 2026-10-31 BEFORE any mutation run; ids from `--collect-only` in the scratch copy, written cwd-relative `../tests/…` per #560)
P = `../tests/test_prod_store_guard.py::TestEveryAttemptFailsTheNodeWhosePhaseMadeIt::`
- **M1** drop the `pytest_make_collect_report` wrapper → declared RED: `P test_attempt_fails_the_node_whose_phase_made_it[module import (collection)]`, `P …[module import followed by a module-level skip]`, `P test_no_node_whose_phases_made_no_attempt_is_charged` (the accumulated import attempts land on `test_import_door_module_test`'s setup).
- **M2** `charge` flips only `passed` reports (skipped and xfailed reports are left alone) → declared RED: `P …[attempt followed by pytest.skip]`, `P …[attempt in an xfail-marked test]`, `P …[module import followed by a module-level skip]`.
- **M3** (gap proof for C1/C5) an IP-literal-only guard (no `localhost`, no resolution, no unspecified address) → declared RED: **∅**: predicted 41 passed. Run plain, not through `mutation_proof.py`, because the tool requires ≥1 `--expect-red`.
- **M4** (C3) the `connect` wrapper records but does not refuse → declared RED: `P test_no_node_whose_phases_made_no_attempt_is_charged` ONLY (via `test_skip_fixture_second_user` expecting the cached skip).

## 2. Residual decisions
- **(a) hostname alias → CLOSED in `conftest.py`**, together with its whole class. The guard decided by SPELLING while the kernel decides by ROUTING. A production-port destination is now refused when its host:
  - is loopback (shared `lorerunes.posture.host_is_loopback`, lowered);
  - is the unspecified address (B7: `0.0.0.0` / `::`, which Linux reroutes to loopback);
  - is a name that resolves to either (`_resolves_to_loopback` via `getaddrinfo`, called only for port-18500 connections);
  - or is an ASCII `bytes`/`bytearray` spelling of any of these (`_host_text`).

  Behaviour receipt: §3 probe, HEAD `PROBE FAIL (5)` vs edit `PROBE PASS`. Why close rather than bound: the alias is live on this box (`localhost.localdomain` → 127.0.0.1), and `0.0.0.0` is the honest "bind address reused as a client URL" door. Closing costs one `getaddrinfo` on production-port connections only. ⚠ It is UNPINNED by the contract (C1/C5): a deletion would stay green, and M3 proves it. The pin is routed to the contract author.
- **(b) attempt after the last report → KNOWN BOUND, sharpened in the docstring with a re-open trigger.** Why not closed:
  - A post-`unconfigure`/`atexit` attempt has no channel to the exit code at all.
  - A `pytest_sessionfinish` exit-status override would cover serial runs only. `xdist.dsession.DSession.worker_workerfinished` reads `workeroutput["exitstatus"]` only for `== 2` (read 2026-10-31 in the installed xdist), so a worker's late attempt never reaches the controller's verdict. That would be a half-closure, which is worse than a stated bound.
  - Every in-test shape the threat model names (test body, fixture of any scope, module import) reports before the session ends, and the contract pins all of them.
  - The refusal still holds, so production is never reached.

  Re-open trigger: a lore plugin, `atexit` hook or session-outliving thread that talks to a SurrealDB store. Sibling, also bounded in the docstring: a background thread's attempt is charged to the NEXT report's node. That is why the verdict now says "made while", not "attempted" (B3).

## 3. Fixes applied in place (all in `conftest.py` unless noted; final md5 `f31db77bc3756975c572208cb5f83f4d`)
| finding | change |
|---|---|
| B1 | `_reaches_loopback` routes the loopback decision to `lorerunes.posture.host_is_loopback(host.lower())`. `LOOPBACK_HOSTNAME` deleted (its literal lives in lorerunes). `host_is_loopback` was NOT extended (decision D-1). |
| B2 / B7 / bytes | `_reaches_loopback` adds `ipaddress…is_unspecified`. New `_resolves_to_loopback(host, port)` (getaddrinfo, fail-closed-to-pass on `OSError`/`ValueError`, because the real connect fails the same way). New `_host_text` (str / ASCII bytes). `targets_production` is now 3 returns, which also fixes ruff PLR0911, introduced and then fixed within this edit. |
| B3 | Verdict: `"N attempt(s) on the PRODUCTION SurrealDB store (loopback port P) were made while <node> ran its <when> phase; …"` (`report.when` exists on both report types; `CollectReport.when == "collect"`, probed). |
| (b) | KNOWN BOUNDS rewritten: loopback-destination bound, window-not-author bound, after-last-report bound with the measured xdist reason and a re-open trigger. HOW §1 lists the destination rule and `ssl`. |
| gate reach | `scripts/typecheck.sh`: `conftest.py` appended to `MEMBERS`, with a comment bullet (FILE root; loads into every session; `gated_ground` LEG A reported it ungated). The derivation one-liner still makes sense: it prints `['skills', 'docs/eval', 'scripts', 'conftest.py']`, exactly the bulleted non-members. |

Not changed, deliberately: the `except (OSError, ValueError)` parens. `ruff format` (not a manifested gate) wants the PEP 758 paren-less form. The repo has 55 parenthesised multi-excepts and 0 paren-less ones, so I kept the house idiom.

### Behaviour-receipt instrument (pasted verbatim per brief-base §1; run as `HOST_NETNS=$(readlink /proc/self/ns/net) LAN_NAME=ean.firehawktransam.org unshare -rn .venv/bin/python <probe> <conftest>`)
Receipt, 2026-10-31: HEAD conftest (`a7c0118b…`) → `BAD` on localhost.localdomain, 0.0.0.0, ::, b"127.0.0.1", bytearray alias → `PROBE FAIL (5)`. Edited conftest (`f31db77b…`) → `PROBE PASS` (14/14). The controls (non-production port via 127.0.0.1 / 0.0.0.0 / alias → CONNECTED, unrecorded; LAN name and unresolvable name on :18500 → unrecorded) pass in both, so the probe can see both directions.
```python
"""Behaviour receipt for the guard's destination rule. Run ONLY inside `unshare -rn` (asserted)."""
import importlib.util, os, socket, subprocess, sys
assert os.readlink("/proc/self/ns/net") != os.environ["HOST_NETNS"], "NOT isolated — refusing to run"
subprocess.run(["ip", "link", "set", "lo", "up"], check=True)
spec = importlib.util.spec_from_file_location("guard_under_probe", sys.argv[1])
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)  # installs the guard
guard = module.PRODUCTION_STORE_GUARD
PROD = module.PRODUCTION_STORE_PORT
STUB = 18555
stub = socket.create_server(("127.0.0.1", STUB)); stub6 = socket.create_server(("::1", STUB), family=socket.AF_INET6)
cases = [
    ("prod 127.0.0.1", socket.AF_INET, ("127.0.0.1", PROD), True),
    ("prod localhost (raw)", socket.AF_INET, ("localhost", PROD), True),
    ("prod LOCALHOST (raw)", socket.AF_INET, ("LOCALHOST", PROD), True),
    ("prod localhost.localdomain (raw, /etc/hosts alias)", socket.AF_INET, ("localhost.localdomain", PROD), True),
    ("prod 0.0.0.0", socket.AF_INET, ("0.0.0.0", PROD), True),
    ("prod :: (v6)", socket.AF_INET6, ("::", PROD, 0, 0), True),
    ("prod ::ffff:127.0.0.1 (v6 mapped)", socket.AF_INET6, ("::ffff:127.0.0.1", PROD, 0, 0), True),
    ('prod b"127.0.0.1" (bytes host)', socket.AF_INET, (b"127.0.0.1", PROD), True),
    ("prod bytearray localhost.localdomain", socket.AF_INET, (bytearray(b"localhost.localdomain"), PROD), True),
    ("prod LAN name (resolves non-loopback)", socket.AF_INET, (os.environ["LAN_NAME"], PROD), False),
    ("prod unresolvable name", socket.AF_INET, ("no-such-host.invalid", PROD), False),
    ("stub 127.0.0.1 (other port)", socket.AF_INET, ("127.0.0.1", STUB), False),
    ("stub 0.0.0.0 (other port)", socket.AF_INET, ("0.0.0.0", STUB), False),
    ("stub localhost.localdomain (other port)", socket.AF_INET, ("localhost.localdomain", STUB), False),
]
bad = 0
for label, family, address, expect_refused in cases:
    with socket.socket(family, socket.SOCK_STREAM) as sock:
        sock.settimeout(2)
        try:
            sock.connect(address); outcome = "CONNECTED"
        except OSError as exc:
            outcome = f"{type(exc).__name__}"
    recorded = bool(guard.drain())
    ok = recorded == expect_refused
    bad += not ok
    print(f"{'ok ' if ok else 'BAD'} recorded={recorded!s:5} expected={expect_refused!s:5} outcome={outcome:24} {label}")
print("PROBE", "PASS" if not bad else f"FAIL ({bad})")
```
Companion probe for B7 (kernel reroute, isolated netns):
```python
import socket, subprocess, os
# Runs inside `unshare -rn`: nothing here can reach the host's production store.
assert os.readlink("/proc/self/ns/net") != os.environ["HOST_NETNS"], "NOT isolated"
subprocess.run(["ip", "link", "set", "lo", "up"], check=True)
PORT = 18555  # an arbitrary stub port, never the production port
for fam, bind_host, dest in [(socket.AF_INET, "127.0.0.1", "0.0.0.0"), (socket.AF_INET6, "::1", "::")]:
    srv = socket.socket(fam, socket.SOCK_STREAM); srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((bind_host, PORT)); srv.listen()
    cli = socket.socket(fam, socket.SOCK_STREAM); cli.settimeout(2)
    rc = cli.connect_ex((dest, PORT))
    print(f"listener {bind_host}:{PORT}  connect_ex({dest!r}) -> {rc} ({os.strerror(rc) if rc else 'CONNECTED'}) peer={cli.getpeername() if rc == 0 else None}")
    cli.close(); srv.close()
```
Output: `listener 127.0.0.1:18555  connect_ex('0.0.0.0') -> 0 (CONNECTED) peer=('127.0.0.1', 18555)` · `listener ::1:18555  connect_ex('::') -> 0 (CONNECTED) peer=('::1', 18555, 0, 0)`.

## 4. Typecheck rider (binding)
- **Red leg (scratch `/var/tmp/claude-1000/audit-guard-scratch`, provenance asserted by `scratch_copy.sh`):** appended `_TYPECHECK_RIDER_PROBE: int = "not an int"` to the copy's `conftest.py` and ran the copy's `scripts/typecheck.sh` → `RED_RUN_EXIT=1`, `conftest.py:271: error: Incompatible types in assignment (expression has type "str", variable has type "int")  [assignment]`, **`typecheck: conftest.py FAILED`**. Restored from a content backup, md5 `9405e1fa…` before = after. (haiku-worker. I read its typecheck lines and log grep. The run was on an intermediate conftest revision; the leg's mechanism is independent of the file body.)
- **Green leg (real tree):** `bash scripts/typecheck.sh` → **`typecheck: conftest.py OK`**. The other lines: `lorerunes/lorescribe/loresigil/skills/docs/eval OK`, `loremaster FAILED`, `scripts FAILED`, `shellcheck OK (7 tracked .sh)`. The two FAILED legs are pre-existing and RED_ADJUDICATED (83 residuals owned by packet-58-contract / packet-64b-i-contract per the currency gate), not orphaned. Re-run on the final conftest: §8.

## 5. DRY ledger (brief-base §6) — my new symbols, plus the prior-art question for the build's
| new symbol | where I looked | what it returned | disposition |
|---|---|---|---|
| `_reaches_loopback` | `lore_search("is loopback address predicate / localhost host check helper")` | `lorerunes/lorerunes/posture.py::host_is_loopback` (the shared bind-host predicate) | **REUSED `lorerunes.posture.host_is_loopback`** for the loopback decision. The wrapper adds only the destination-specific rules: case-lowering, because the resolver is case-insensitive, and `is_unspecified`, because the kernel reroutes it. `is_unspecified` must NOT go into `host_is_loopback`: a `0.0.0.0` BIND is the opposite of loopback for `derive_posture`. |
| `_resolves_to_loopback` | same search + `lore_search("pytest hook that wraps socket connect …")` | no resolver-to-loopback helper. The second query returned only the impl report. | HAND-ROLLED: stdlib `getaddrinfo` + the shared predicate. Nothing to reuse. |
| `_host_text` | same | none | HAND-ROLLED (trivia: str/bytes normalisation of a socket address element, not policy) |
| build's `PRODUCTION_STORE_PORT` | impl ledger re-checked + `lore_search("production store port 18500 constant")` | `scripts/restore_prod_dump.py::PRODUCTION_PORT`, the loremaster test-private string, `DEFAULT_SURREAL_URL` in a survey script (cold-audit receipt) | agree with impl: HAND-ROLLED per the ruling. Drift pin routed as C2. |
| build's `ProductionStoreGuard` | impl ledger + my second query | nothing does the per-report recorder job | agree: HAND-ROLLED |
| build's inline loopback check | — | **impl ledger MISSED `host_is_loopback`** | fixed (B1) |
| `scripts/typecheck.sh` entry | `gated_ground.typecheck_roots` docstring ("a root may be a directory or a single file") + `test_a_single_file_member_is_a_legal_typecheck_root_that_covers_itself` | file roots are a supported, pinned shape | REUSED the existing file-root mechanism |

### 6b. Mutation results (scratch `/var/tmp/claude-1000/audit-guard-scratch`; `loremaster.__file__ = /var/tmp/claude-1000/audit-guard-scratch/loremaster/loremaster/__init__.py`; conftest md5 `f31db77b…` before and after every run; instrument `/var/tmp/claude-1000/audit-guard-mut/run_mutations.sh`, log `run_mutations.log` beside it. Run by a haiku-runner; I read its RAN line, verdicts and counts.)
| mutation | declared RED | observed | verdict |
|---|---|---|---|
| M1 drop collect-report wrapper | 3 (§6) | `3 failed, 38 passed` = declared, exactly | **PROOF HELD** (M1_EXIT=0) |
| M2 flip only `passed` | 3 (§6) | `4 failed, 37 passed`: the declared 3 **+ `TestGuardIsLiveInEveryXdistWorker::test_benign_tests_still_pass_under_xdist[test_benign_test_store_health_answers]`** with `ConnectionResetError: [Errno 104]` on the TEST-store stub (port 18000, which the guard never touches) | **PROOF FAILED as run (M2_EXIT=4)**. The extra red is not attributable to the mutation: M2 changes only skipped/xfailed reports, and the xdist door modules have none. Adjudication by re-run + flake measurement: §6c |
| M3 IP-literal-only guard | ∅ | `41 passed` (mutation landed: grep shows `return ipaddress.ip_address(host).is_loopback` at line 200) | **GAP CONFIRMED.** The contract cannot tell the build from a guard that misses `localhost` raw connects, `/etc/hosts` aliases, `0.0.0.0`/`::` and bytes hosts (C1 + C5) |
| M4 connect records, does not refuse | 1 | `1 failed, 40 passed` = declared, exactly | **PROOF HELD** (M4_EXIT=0). Refusal of `connect` is pinned by ONE indirect pin, as predicted (C3) |

### 6c. M2 adjudication + sharing proof (instrument `/var/tmp/claude-1000/audit-guard-mut/run_extra.sh`, log `run_extra.log`; `lorerunes.posture.__file__` inside the scratch; md5s restored byte-exact)
- **M2 re-run, same declared set → `3 failed, 38 passed`, PROOF HELD exactly (M2R_EXIT=0).** The first run's extra red was the TEST-store stub resetting a connection under the inner `-n 2` session, unrelated to the mutation. Flake-rate measurement on the UNMUTATED real tree: §6d.
- **M5: sharing by mutation (brief-base §6).** `lorerunes.posture.host_is_loopback`'s IP branch mutated to `return False and …` → guard contract **`27 failed, 14 passed`** (M5_PYTEST_EXIT=1). Changing the shared predicate breaks the guard, so B1's routing is real sharing, not a private copy wearing the name. (Plain run, observed set not pre-declared, and labelled so. The proof property is "the caller breaks", and 27 > 0 shows it.)

### 6d. NEW CONTRACT DEFECT C6: the xdist leg is FLAKY (measured 2026-10-31, independent of the guard)
- Instruments: `/var/tmp/claude-1000/audit-guard-mut/xdist_loop.sh` (real tree, final conftest) and `xdist_loop_head.sh` (scratch, HEAD conftest `a7c0118b`, md5 restored to `f31db77b` after). Each runs `-k TestGuardIsLiveInEveryXdistWorker` 20× in a row.
- **Final conftest: 3/20 red. HEAD conftest: 2/20 red.** Every red is `TestGuardIsLiveInEveryXdistWorker::test_benign_tests_still_pass_under_xdist[test_benign_test_store_health_answers]` with `ConnectionResetError: [Errno 104]` from the TEST-store stub on port 18000. The guard never sees that port: `targets_production` returns at the port check.
- Mechanism (MEDIUM: inferred from the code, not separately probed). `_INNER_PRELUDE`'s `_StubServer` sets `allow_reuse_port = True`. Under the inner `-n 2`, both xdist workers inherit ONE private netns and each binds its own stub on 18000 and 18500. The kernel load-balances new connections across both SO_REUSEPORT listeners, so when one worker's module fixture `server_close()`s, connections queued on its listener are reset, and the other worker's benign test reads RST.
- Consequence: the contract's "41 passed" is not stable. A builder or auditor hitting this would see an unexplained red in a benign pin, the exact "flaky" downgrade CLAUDE.md forbids. It also contaminated mutation M2's first run.
- ROUTE (contract author): drop `allow_reuse_port`, or start ONE stub per namespace in the bootstrap rather than per worker, or give each worker distinct ports. Prove it by 20 consecutive green runs (CLAUDE.md: a single green never clears a concurrency test).

## 7. Packet FULL SUITE, run once (2026-10-31, final conftest `f31db77b` + final typecheck.sh `21669bd9`, uncommitted on top of `c99210b`)
- Command (repo root, haiku-runner, RAN line checked): `flock /tmp/lore-full-suite.lock systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q -n 12 -p no:cacheprovider -rfE > /var/tmp/claude-1000/audit-guard-full-suite.log 2>&1` → EXIT=1.
- **Count line: `533 failed, 13505 passed, 67 skipped, 3 xfailed, 8 warnings in 767.52s (0:12:47)`.** No `Killed`, no 137. The 19 `ERROR ` lines are captured log records (`ERROR loremaster.store._txn:_txn.py:1157 store.transaction.rolled_back`), not pytest errors.
- **Set diff vs the 530-id baseline** (`/var/tmp/claude-1000/a165-full-failed-ids.txt`). Both sides are normalised to the baseline's own id form, cut at the first whitespace. A first naive pass showed 14 spurious NEW/GONE pairs: parametrised ids containing whitespace that the baseline had truncated. **NEW = 3, GONE = 0** (530 + 3 = 533 ✓):
  1. `scripts/test_gated_ground.py::TestTheRealRepositoryIsFullyGated::test_no_committed_python_is_ungated_on_either_axis`: **ATTRIBUTABLE to the guard build** (`8d8b2fa` added a tracked root `conftest.py`). The failure text names ONLY `conftest.py` LEG B (execution). LEG A (types) was the other half, and my `MEMBERS` entry closed it (verified: before my edit `ungated_ground` listed both axes, after it only EXECUTION).
  2. `scripts/test_gated_ground.py::TestTheExemptionTableIsAnAllowlistOfTheSafe::test_the_table_lands_EMPTY_and_the_emptiness_is_a_fact_about_the_TREE`: same cause, same finding.
  3. `skills/lore-deploy/tests/test_prod_store_guard.py::TestGuardIsLiveInEveryXdistWorker::test_benign_tests_still_pass_under_xdist[test_benign_test_store_health_answers]`: **the C6 flake** (measured 2/20 at HEAD's conftest, 3/20 at the final one: §6d). This is a contract defect, not the guard.
- **Guard verdicts in the whole run: 0** (`grep -c "PRODUCTION SurrealDB store"` = 0; `grep -c 18500` = 0). No lore test touches production through Python sockets. (Bounded by the guard's own KNOWN BOUNDS: subprocess/C clients are invisible.)

## 8. Gates (final tree; every command captured its own exit; read verdicts, not exits, per #565)
| gate | command | result |
|---|---|---|
| contract | `cd skills/lore-deploy/scripts && … pytest -q ../tests/test_prod_store_guard.py --timeout=300 -p no:cacheprovider -rfEs` (inline, final conftest) | **41 passed in 17.44s**, EXIT=0 |
| skill suite | `… pytest -q . ../tests -n 8 --timeout=300 -p no:cacheprovider -rfEs` (haiku-runner, final conftest) | **212 passed in 24.78s**, SKILL_EXIT=0 (202 + 10 ✓) |
| typecheck | `bash scripts/typecheck.sh` | `conftest.py OK` · lorerunes/lorescribe/loresigil/skills/docs/eval OK · `loremaster FAILED` · `scripts FAILED` · `shellcheck OK (7 tracked .sh)`. TC_EXIT=1 from pre-existing, adjudicated reds |
| currency | `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` | typecheck **RED_ADJUDICATED** (83 residuals, packet-58-contract / packet-64b-i-contract) · ruff **GREEN** · pytest NOT_RUN (#565 by design) → **RED_ORPHANED 0** |
| ruff (file) | `uv run ruff check conftest.py` | All checks passed (EXIT=0) |
| ruff (brief's literal) | `uv run ruff check conftest.py scripts/typecheck.sh` | EXIT=1, **96 errors, all in `scripts/typecheck.sh`**: given an explicit path, ruff parses the bash file as Python. HEAD's `typecheck.sh` scores 93 the same way. Brief premise "ruff ignores .sh" holds only for directory discovery. Not a defect of this change. |
| full suite | §7 | 533 failed / 13505 passed. NEW 3 (2 attributable, gated_ground LEG B; 1 contract flake C6), GONE 0 |
| mutation | §6 | M1 HELD · M2 HELD on re-run (first run hit C6) · M3 gap confirmed · M4 HELD · M5 sharing proven |

## 9. Decisions needed (fork → my recommendation)
- **D-1 (B1, STOP-and-ask per §6):** should `lorerunes.posture.host_is_loopback` itself lowercase? Doing so would flip `derive_posture` for a bind host spelled `LOCALHOST`, which is refused today (fail-closed). → **Recommend: NO**, leave the shared predicate as is. The guard lowers at its own call site, because the guard's safe direction is the opposite of posture's. Raised because it is a change to existing callers' behaviour, which is not mine to make.
- **D-2 (packet blocker, attributable reds):** `scripts/gated_ground.py::_execution_fate` counts a conftest as execution-covered only if it lies UNDER a testpath. pytest also loads every conftest on the ANCESTOR chain from rootdir to each collection root, and the same module's collector-fingerprint docstring already says so ("pytest walks rootdir → the collection target loading every `conftest.py` on the way"). So the root conftest is a false positive, and both live pins stay red until one of these happens. → **Recommend (a):** a scripts/ builder extends `_execution_fate` so a conftest whose directory is an ancestor of a testpath (within rootdir) is COVERED, with a behaviour pin, and proves it by mutation. **(b)** An exemption row needs an operator ruling, and the table's own law argues against it. Outside my writable set: flagged, not edited.
- **D-3 (rider for my closures):** the residual-(a) class closure (aliases, `0.0.0.0`/`::`, bytes hosts) and the B3 wording are UNPINNED. M3 proves a deletion stays green. → **Route to the contract author:** pins C1 + C5 (raw `localhost`, `/etc/hosts` alias, `0.0.0.0`, `::`, `b"127.0.0.1"` doors; each passes unguarded against the stub, so the control leg is free). Plus C2 (port drift), C3 (stub counts zero connections), C6 (the flake). Until then, these closures are deletable with every gate green.

## 10. Noticed
- **Blast radius of B1:** the root conftest now imports `lorerunes.posture` in every pytest session, so a syntax error mid-edit in `lorerunes/posture.py` stops every suite at conftest import, not just lorerunes'. Judged acceptable: lorerunes is stdlib-only, and loremaster imports it everywhere anyway. Stated so the trade is visible.
- `lore_impact` / `lore_index` were not used. My scope was two files, and their covering set is the contract plus the skill suite, both run, plus the full suite. Grep fell back for three non-symbol seams: the `typecheck.sh` parsers (`gated_ground.py`, `pending_contract_gate.py`), the `except` idiom count, and the failing-id diff (CLAUDE.md dogfood case b). The `typecheck.sh` parser search was the useful one: it found the gated_ground interaction.
- The impl report's reuse ledger missed `host_is_loopback` because both its queries were about the port and the mechanism, never about the loopback decision. A ledger built per symbol misses the rules a symbol contains. Worth a line in the reuse-scout brief: query each RULE the new code decides, not just each symbol it adds.
- The 14 spurious NEW/GONE pairs in the first diff: the baseline file stores ids truncated at the first whitespace. Any later diff against `/var/tmp/claude-1000/a165-full-failed-ids.txt` must normalise the same way (`awk '{print $1}'`) or it will report phantom regressions.
- First contract haiku-runner (pre-final conftest) reported `ERROR: file or directory not found: ../tests/test_prod_store_guard.py` for a path that exists; discarded and re-run inline (41 passed). Cause not established (probably a cwd mismatch in the runner).
