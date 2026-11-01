# REPORT-contract-165-guard-r3

brief-base v24 read · brief project v7 read (lore_comms register, session fix-165-2026-10-31)

## SUMMARY (2026-10-31, 15:41–16:05 EDT, inside the 60-min deadline; no item NOT TRIED)
- **State: done.** One file edited: `skills/lore-deploy/tests/test_prod_store_guard.py` (41 → 91 outer tests).
- **Deviations:** (1) first build-leg / collect-only runs inline (critical-path debugging); (2) one runner ran two of my commands concurrently (read-only, results stand, §Noticed 6); (3) a mount namespace was ADDED to the isolation design to make the alias door hermetic (see "Hermetic alias").
- **Pins → wrong guard:** 8 destination doors × {serial scripts, serial tests, xdist} (alias, `0.0.0.0` raw+URL, `::`, `::1`, `localhost`, `LOCALHOST`, bytes) catch the spelling-decided guard (C1/C4/C5); same-destination benign twins catch an over-refusing guard; the accept ledger (`== 0` guarded ∀ doors ∀ phases, `==` door count unguarded) catches refusal leaks (C3); the port comes from the production scaffold, so a drifted guard fails every door (C2).
- **Declared vs observed (pre-audit conftest `c99210b`/`a7c0118b`):** 17 declared from `--collect-only` before any run = 17 observed, EXACT both ways, ×3 runs; every red fails "reached the production port … outcome=passed" or "stub ACCEPTED 5" — the 5 doors the pre-audit guard misses.
- **Build:** 91 passed at the committed conftest `f31db77b` (HEAD `08acd90`; HEAD moved twice during my run, `scripts/` only — conftest + skill unchanged since `308251f`).
- **C6 root cause:** CONTRACT, not guard. Per-worker module stubs with `SO_REUSEPORT` under inner `-n 2`; one worker's teardown resets the other's queued connection. Mechanism probed (10/20 RST, probe pasted). Fixed by ONE bootstrap-owned stub set per namespace. Receipts: matched load old 6/60 red vs new 0/60 (p≈0.014); quiet 0/40; final file **20/20 consecutive green** (twice).
- **Provenance:** `loremaster.__file__ = /var/tmp/claude-1000/guard-r3-scratch/loremaster/loremaster/__init__.py` (scratch via `scratch_copy.sh`, conftest md5 `a7c0118b` = `git show c99210b:conftest.py`).
- **Gates:** ruff clean · currency `--legs typecheck,ruff`: typecheck RED_ADJUDICATED (pre-existing 83, my file 0), ruff GREEN → RED_ORPHANED 0.
- **Packages considered:** stdlib `ctypes`+`mount(MS_BIND)` for resolver isolation → bespoke (4 lines; no PyPI package searched — MEDIUM); `runpy` → replace for `-m` semantics; `http.server` stub (unchanged); `pytest-socket` not re-litigated.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 1 rule-adjacent new symbol (`_production_store_port_from_scaffold`) REUSES `lore_deploy._scaffold_lore_yaml` + `_read_config_field`; the rest are test fixtures. All dispositioned (§DRY ledger).
- **Graded:** n/a (contract author; the scratch run is RED at a lead-supplied build, not a grade).
- **Forks / decisions needed:** (a) scaffold rejects hyphenated project dirs — likely real lore-deploy defect, file it? (§Noticed 1); (b) derive `TEST_STORE_PORT` the same way? (§Noticed 3, recommend no); (c) "predicted only" pins (raw `localhost`, `LOCALHOST`, `::1`, record-and-pass-through, drift) await the adversary — not graded by me (role boundary).
- **Pointers:** §What changed · §Hermetic alias · §C6 · §C6 measurements · §Pins → wrong guard · §Final gates · §Instruments · §Noticed.


## Routing table (written before any read beyond the brief + brief-base)

| step | tier | who | reason |
|---|---|---|---|
| read audit §1/§3/§6d/§9 D-3 + design report + current test file | 3 | me | inputs to contract design; judgment |
| netns probes (lo has ::1? alias resolution in netns?) | 1 (small inline batch) | me | ≤5 short commands on the critical path, output read in full |
| scratch copy (`scratch_copy.sh`) + pre-audit conftest placement | 1 | haiku-worker | rote, exact commands; runs while I design |
| write the new pins | 3 | me | contract authoring (never Haiku) |
| RED-at-HEAD/build-leg run (real tree) | 1 | haiku-runner | test run |
| scratch run vs pre-audit conftest | 1 | haiku-runner | test run; declared-vs-observed diff judged by me |
| C6 20× xdist leg | 1 | haiku-runner | test run |
| ruff + currency (typecheck,ruff) | 1 | haiku-runner | gate run |

Routing deviation: the FIRST build-leg run (and the `--collect-only` runs) ran inline, not via a haiku-runner. They were on the critical path with nothing to overlap, and I needed the full failure text to debug a new bootstrap. Every later run went to a runner.

## Capability check
- Demanded: Bash, Agent (haiku-runner/worker), lore_comms, `scratch_copy.sh`, `unshare` (user+net+mount namespaces), systemd-run cgroup cap. All available. Registered on lore_comms (fix-165-2026-10-31).
- Idle-gate contract: `/tmp/claude-idle-gate-lore/unknown-contract-165-guard-r3.contract`. My harness session id is not visible to me, so I used the `unknown-` prefix sibling agents used.
- No BRIEF CONFLICT. The discrimination proof is a run of MY contract against a lead-supplied build (the pre-audit conftest `c99210b`). That is "RED at a supplied build", not a wrong build I built. I built no wrong implementations.

## What changed (`skills/lore-deploy/tests/test_prod_store_guard.py`, written 2026-10-31 at HEAD `308251f`; the only file edited)
1. **Isolation bootstrap (`_BOOTSTRAP`)** — now:
   - unshares a MOUNT namespace too, and bind-mounts a private `/etc/hosts` and `/etc/nsswitch.conf` (`hosts: files`; the host's other lines kept);
   - starts ONE stub set for the whole inner session: production port + test-store port, each on `127.0.0.1` and `::1`;
   - runs pytest in-process (`runpy.run_module("pytest", alter_sys=True)`, `sys.path[0] = cwd`, the same as `python -m pytest`);
   - at the end, drains each production-port listener's backlog and prints `STUB-ACCEPTS production=<n>`.

   A failure to mount → exit 77 → SKIP with the reason, never an un-isolated run (same contract as the netns).
2. **Inner prelude** — only refuses to run un-isolated now; the per-module stub fixture and `allow_reuse_port` are gone (C6). The import-skip module's transient stub is gone too: the session stub answers its probe.
3. **New inner doors (C1, C4, C5)** — `test_door_raw_connect_reaching_loopback[<destination>]` over `localhost`, `LOCALHOST`, `hosts-alias`, `unspecified-ipv4` (`0.0.0.0`), `unspecified-ipv6` (`::`), `loopback-ipv6` (`::1`), `bytes-host` (`b"127.0.0.1"`), plus `test_door_urlopen_health_on_unspecified_address` (`http://0.0.0.0:P/health`, the bind-address-as-client-URL shape).
   - **Same-destination benign twins:** `test_benign_raw_connect_to_test_store_at_same_destination[<destination>]` dials every one of those destinations on the TEST-store port. The property's second half: the port decides, not the host.
4. **New outer pins:**
   - `TestProductionPortAttemptsFailTheAttemptingTest::test_every_destination_reaching_loopback_fails_and_names_the_port[door-tree]` (8 doors × 2 trees). The xdist and benign classes pick the new names up through `PROD_DOOR_TESTS` / `BENIGN_TESTS`.
   - **C3:** `TestTheRefusalHappensBeforeTheConnectionLeavesTheProcess::test_production_stub_accepts_no_connection_in_a_guarded_session[guarded_runs|xdist_run|phase_run]`. Quantified over every door and every phase at once.
   - **C3 positive controls (counter-sees-connections):** `TestControlWithoutAnyGuard::test_the_production_stub_counts_every_door_connection_without_a_guard` (accepts `==` the number of doors) and `TestPhaseControlWithoutAnyGuard::test_the_production_stub_counts_every_phase_attempt_without_a_guard` (accepts `==` the number of charged phases).
5. **C2:** the literal `PROD_STORE_PORT = 18500` is gone. The `production_store_port` fixture runs the PRODUCTION builder `lore_deploy._scaffold_lore_yaml` in a tmp project and takes the port from `surreal.url`. Every door dials that port (`InnerRun.production_port`), and failures must name it.
   - So a guard whose port drifts from the scaffold fails every door pin, with no test reading the guard's constant (a behaviour pin, not a spelling pin).
   - `SCAFFOLD_PORT_AT_WRITING = 18500` is checked against the derivation only as a parse sanity bound: a parse that silently picked another URL's port (e.g. TEI `:8080`) would re-aim every pin.
6. Unchanged: the "inner sources never spell the port" rule (the port still arrives by env). The alias name is also passed by env.

Count: 41 → **91** outer tests (collect-only, 2026-10-31).

## Hermetic alias (step 1's condition) — how it was verified
- This host's `/etc/nsswitch.conf` is `hosts: mymachines mdns_minimal [NOTFOUND=return] resolve [!UNAVAIL=return] files myhostname dns`. With `resolve` ahead of `files`, systemd-resolved answers from the HOST's `/etc/hosts`, so a hosts alias would be neither hermetic nor under the contract's control. Hence the private mount namespace with BOTH files bind-mounted.
- Probe (2026-10-31, inside `unshare(USER|NET|NS)`, bind mounts rc=0):
  - `localhost` → `['127.0.0.1','::1']`; `LOCALHOST` → same;
  - `guard-contract-store-alias.test` → `['127.0.0.1']`;
  - **`localhost.localdomain` → `Name or service not known`**: resolution provably comes from the private file, not the host's;
  - on the host, `getent hosts guard-contract-store-alias.test` → unresolvable.
  - `lo` has `::1` in the new netns (`/proc/net/if_inet6`).
  - Every one of the seven destinations CONNECTED to a stub listening on `127.0.0.1` + `::1` (bytes→127.0.0.1, `0.0.0.0`→127.0.0.1, `::`→::1).
- Host files untouched after the runs: `/etc/hosts` md5 `e4e0c593…`, `/etc/nsswitch.conf` md5 `aba073e5…`. The bind mounts live and die with the inner session's private mount namespace.
- `.test` is reserved (RFC 6761 §6.2), so no real resolver answers it. The CONTROL session's pass on `hosts-alias` is therefore itself the proof that the private hosts file resolved it, in every run.
- Bound: if a host has NO `/etc/nsswitch.conf` (some minimal images), only `/etc/hosts` is mounted, and glibc's built-in default (`dns [!UNAVAIL=return] files`) reaches `files` because DNS is unreachable in the empty netns. If that ever fails, it fails LOUD (the control leg goes red on `hosts-alias`), never silently. Also not covered: an `nscd` daemon would intercept lookups before nsswitch. There is none on this host (`/run/nscd`, `/var/run/nscd` absent); same loud-failure property.

## C6 — root cause (contract, not guard)
- **Mechanism measured, not inferred** (2026-10-31, probe pasted below). In a private netns: two `SO_REUSEPORT` listeners on one port; 20 clients connect and send a request; close listener[0] without accepting → **10/20 clients read `ECONNRESET`**. The kernel hashed half the new connections into the closed listener's accept queue.
- That is exactly the old contract's shape under the inner `-n 2`. Both xdist workers share ONE netns, and each ran the module-scoped `_isolated_stub_stores` fixture, binding its own `allow_reuse_port` stub on 18000/18500. A worker's module teardown `server_close()`s a listener holding the OTHER worker's queued benign connection → `ConnectionResetError: [Errno 104]` in `test_benign_test_store_health_answers` (audit §6d's observed signature, port 18000, which the guard never examines).
- **Fix (contract):** the stubs moved out of the per-module fixture into the bootstrap. One listener per (port, family), alive from before pytest starts until after it returns. No duplicate listener can exist, so nothing can be load-balanced or reset. `allow_reuse_port` is deleted.
- Not in the guard: the guard returns at its port check for :18000. The flake reproduces with the old contract at the pre-audit conftest (baseline loop below), so the conftest revision is irrelevant to it.

```python
"""C6 mechanism probe: two SO_REUSEPORT listeners on one port (= two xdist workers' module stubs);
one closes with connections queued in ITS accept queue; do clients hashed to it read RST?"""
import fcntl, os, socket, struct
uid, gid = os.getuid(), os.getgid()
os.unshare(os.CLONE_NEWUSER | os.CLONE_NEWNET)
open("/proc/self/setgroups","w").write("deny"); open("/proc/self/uid_map","w").write(f"0 {uid} 1"); open("/proc/self/gid_map","w").write(f"0 {gid} 1")
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); fcntl.ioctl(s, 0x8914, struct.pack("16sH14x", b"lo", 0x1|0x8|0x40)); s.close()
PORT = 18000
for reuseport in (True, False):
    listeners = []
    for _ in range(2 if reuseport else 1):
        sv = socket.socket(); sv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if reuseport: sv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sv.bind(("127.0.0.1", PORT)); sv.listen(64); listeners.append(sv)
    clients = []
    for _ in range(20):
        c = socket.create_connection(("127.0.0.1", PORT), timeout=2); c.sendall(b"GET / HTTP/1.0\r\n\r\n"); clients.append(c)
    listeners[0].close()   # worker A's module teardown: server_close() with B's clients queued on it
    resets = 0
    for c in clients:
        try: c.recv(1)
        except ConnectionResetError: resets += 1
        except TimeoutError: pass
        c.close()
    for sv in listeners[1:]: sv.close()
    print(f"listeners={len(listeners)} reuseport={reuseport}: {resets}/20 clients got ECONNRESET after listener[0] closed")
```
Output: `listeners=2 reuseport=True: 10/20 clients got ECONNRESET after listener[0] closed` · `listeners=1 reuseport=False: 20/20 …`. The second line is the single-listener case, closed with everything queued. It shows why the fix keeps the ONE listener open until pytest has returned.

### C6 measurements (all 2026-10-31; instrument `guard-r3-c6-loop.sh` pasted in §Instruments; every red line is quoted from the logs)
| leg | tree / conftest | file | runs | red | signature of every red |
|---|---|---|---|---|---|
| quiet host, old contract | scratch / pre-audit `a7c0118b` | r2 contract (`490d4091`) | 20 | **0** | — (the flake did NOT show on a quiet host: at the audit's ~10% rate, 0/20 has P≈0.12, so this leg alone proves nothing either way) |
| quiet host, new contract | real / committed `f31db77b` | `15948105` | 40 | **0** | — |
| **matched load** (4 loops concurrently), old contract ×2 | scratch / `a7c0118b` | r2 contract | 60 | **6** (5 + 1) | all 6: `test_benign_tests_still_pass_under_xdist[test_benign_test_store_health_answers]` · `ConnectionResetError: [Errno 104]` (= audit §6d's signature) |
| **matched load**, new contract ×2 | real / `f31db77b` | `15948105` | 60 | **0** | — |
| final file, 20 consecutive (brief's receipt) | real / `f31db77b` | `858b338a` (final) | 20 | see §Final gates | |

Old 6/60 vs new 0/60 under identical conditions (one-sided Fisher exact, p ≈ 0.014 — my arithmetic, HIGH: hypergeometric P(all 6 reds in one arm) = C(60,6)/C(120,6) ≈ 0.0138). Together with the mechanism probe, this is the root cause and the fix, not a lucky streak. The guard is not implicated (the red is on the test-store port, which the guard returns on at its port check, and the flake reproduces at both the pre-audit and the committed conftest).

## Pins → the wrong guard each one catches (new pins only; the r2 pins are unchanged)
| pin (outer) | wrong guard it catches | proven against a real build? |
|---|---|---|
| `…every_destination…[hosts-alias]` | decides by spelling: never resolves names (alias reaches loopback via the resolver) | YES, RED at pre-audit conftest |
| `…[unspecified-ipv4]`, `…[test_door_urlopen_health_on_unspecified_address]` | `ip.is_loopback` only: misses `0.0.0.0` (kernel reroute; B7) | YES |
| `…[unspecified-ipv6]` | hand-listed `"0.0.0.0"` instead of `is_unspecified` | YES (pre-audit misses both) |
| `…[bytes-host]` | `isinstance(host, str)` / `ip_address(bytes)` fail-open | YES |
| `…[localhost]` (raw) | no hostname branch at all (C1; audit M3 kept 41/41 green) | predicted only: GREEN at both available builds (both refuse it); the r2 contract had NO raw-hostname door, so this closes M3's gap by construction |
| `…[LOCALHOST]` | case-sensitive `host == "localhost"` / `host_is_loopback(host)` without `.lower()` (B1's D-1 trap) | predicted only (both builds lowercase) |
| `…[loopback-ipv6]` | IPv4-only loopback check (`startswith("127.")`) (C4) | predicted only |
| `TestTheRefusal…[guarded_runs|xdist_run|phase_run]` | records but lets the connection through, on ANY path incl. `connect_ex` (C3) | YES for the record-less direction (5 accepted per session at pre-audit); the record-and-pass-through build is predicted, not built (role boundary) |
| `TestControl…counts_every_door_connection` / `TestPhaseControl…counts_every_phase_attempt` (`==`) | a blind or double-counting accept counter (positive control: makes "0 accepted" mean refusal) | GREEN at both builds — counts exact |
| benign `…same_destination[*]` (serial both trees + xdist) | a guard that refuses these destinations on EVERY port (port check misplaced/missing) | predicted only |
| C2: every door dials the scaffold-derived port | guard port drifted from production's URL | predicted only (would need a drifted build) |
"Predicted only" rows are NOT TRIED as runs, deliberately: building wrong guards to grade my own pins is the adversary's job (brief-base §2 ROLE BOUNDARY), and the lead supplied two builds, both of which these pins pass on.

## Adversarial pre-flight → case
| realistic break | covered by |
|---|---|
| wrong unit/scale of port (18500 vs a drifted value) | C2 derivation from the production scaffold + `SCAFFOLD_PORT_AT_WRITING` parse bound |
| hostname given raw to `connect` | `[localhost]` door |
| letter case | `[LOCALHOST]` |
| `/etc/hosts` alias | `[hosts-alias]` (hermetic, private resolver) |
| unspecified address v4/v6, URL and raw | `[unspecified-ipv4]`, `[unspecified-ipv6]`, urlopen `0.0.0.0` door |
| IPv6 loopback | `[loopback-ipv6]` |
| bytes host | `[bytes-host]` |
| `bytearray` host | scoped out: same branch as bytes in any plausible guard (`_host_text`-style normalisation); the audit probe covered it once. Raise if the lead wants a door. |
| IPv4-mapped `::ffff:127.0.0.1` | scoped out: `ipaddress` reports it loopback on 3.14 (audit B4), so no plausible guard misses it that `[loopback-ipv6]` doesn't also catch. Raise if wanted. |
| record-but-connect (refusal leaks) | accept-ledger pins (∀ doors, ∀ phases, serial + xdist) |
| non-loopback host on :18500 (LAN name) | spec-silent per ruling F2 (loopback only) — not pinned either way |
| producer↔consumer seam: scaffold URL → guard port | C2 (the scaffold is run, not re-typed) |
| test-side resolver leaking host state | private nsswitch + hosts; `.test` alias; host files' md5 unchanged |
| flaky shared listeners | C6 fix (single bootstrap-owned listener per (port,family)) |

## Realism & independence clauses
- ☑ Production-realistic inputs — destinations are the shapes an honest developer writes (a bind address reused as a URL, a raw `localhost`, a hosts alias); the port comes from the production scaffold, not a literal.
- ☑ Independent expected values — expectations come from the brief's property (refuse ∀ loopback-reaching destinations on the production port; zero accepts), not from the guard's code; I never read `_reaches_loopback`'s body to choose cases (I read only the audit's findings and probe output).
- ☑ Seam coverage — the scaffold→guard port seam (C2) and the resolver→kernel routing seam (aliases, unspecified) are exercised through the real kernel in a real netns, not mocks.
- ☑ Magnitude / sanity bound — accept counts: `== 0` guarded, `== len(doors)` / `== len(PHASE_CHARGED)` unguarded (exact, both directions); `SCAFFOLD_PORT_AT_WRITING` bounds the derivation.
- ☑ Shared conventions, not literals — port from the production builder; test-store port remains a CLAUDE.md-cited constant (unchanged from r2; not in scope of C2, which the audit raised for the production port only — flag: the test-store port has the same drift shape, see §Noticed).
- ☐ Hostile fixtures for rendered stored text — not applicable: the contract renders no stored free text.
- ☐ Input accounting for collection transforms — not applicable: no caller-supplied collection is transformed (the existing must/may-report coverage check already accounts every inner test).

## Removed-behaviour inventory (my own edit deletes contract machinery; adjudicated)
| removed | verdict |
|---|---|
| per-module `_isolated_stub_stores` fixture (stubs per worker per module) | dropped-deliberately: C6 root cause; replaced by bootstrap-owned stubs. Its isolation check is preserved (`_refuse_to_run_unisolated`). |
| `allow_reuse_port = True` | dropped-deliberately (C6) |
| import-skip module's transient stub | dropped-deliberately: the session stub serves the probe; the control still proves the module does not skip unguarded |
| `os.execve` of `python -m pytest` | dropped-deliberately: pytest runs in the bootstrap process so the stubs outlive it; `sys.path[0]=cwd` + `runpy(alter_sys=True)` reproduce `-m` semantics; exit code passed through (77/99 handling unchanged) |
| `PROD_STORE_PORT` / `PROD_PORT_TEXT` literals | dropped-deliberately: C2, replaced by the scaffold derivation |
No spec-silent items.

## DRY ledger (brief-base §6) — new symbols, all test-private
| new symbol | where I looked | what it returned | disposition |
|---|---|---|---|
| `_production_store_port_from_scaffold` | `lore_search("read the surreal url or port from the lore.yaml the lore-deploy scaffold writes, in a test helper")` + read of `scripts/test_scaffold_config.py` | `lore_deploy._read_config_field` (production reader, schema-validated `LoreConfig`, pinned to work without secrets by `test_read_config_field_reads_port_without_anthropic_key`); sibling test-private scaffold helpers `_scaffold` / `_scaffold_valid_config` (monkeypatch-bound, in other test modules) | **REUSED `lore_deploy._scaffold_lore_yaml` + `lore_deploy._read_config_field`** (my first draft parsed with `yaml.safe_load`; switched to the production reader before close-out). Port extraction = stdlib `urllib.parse.urlsplit(...).port`. The siblings' helpers are function-fixture-bound (monkeypatch) and live in other test modules → not importable without a shared test-helper module; not cloned (I call the production functions directly). |
| `Mirror` (dataclass) | — | test-private value holder (path + port) | HAND-ROLLED (trivia, not policy) |
| `_INNER_DESTINATIONS` / `DESTINATION_IDS` / `LOOPBACK_ALIAS` / `PRIVATE_HOSTS` / `STUB_ACCEPTS_PATTERN` / bootstrap stub classes | — | test fixtures of this contract | HAND-ROLLED (fixtures; they decide no production rule) |
⚠ The loopback DECISION is deliberately NOT reused from `lorerunes.posture.host_is_loopback`: the contract must not share the guard's predicate, or a wrong predicate would certify itself. The contract's expectation comes from the kernel (it connects through a real netns and observes where the connection lands).

## Packages considered
- name resolution isolation → no package; Linux mount namespace + `libc.mount(MS_BIND)` via stdlib `ctypes` (probed live: rc 0, alias resolves, host untouched). Verdict `bespoke` for a 4-line bind-mount: no PyPI package was evaluated (MEDIUM: I did not search for one; the stdlib path is two syscalls). Alternative `unshare(1) --mount` + `mount(8)` binaries: rejected to keep the r2 design's "no util-linux dependency" property (the image may lack them, #131 class).
- session stub server → stdlib `http.server.ThreadingHTTPServer` (unchanged from r2; I read its `get_request` hook via the subclass override and `shutdown`/`server_close` semantics by running it).
- pytest-in-process with `-m` semantics → stdlib `runpy.run_module(..., alter_sys=True)` (verified by the build leg: 91 passed, xdist workers spawn and report).
- `pytest-socket`: not re-litigated (r2 report's verdict stands: host filter, no recorder).

## Instruments (pasted verbatim per brief-base §1; also on disk at `/var/tmp/claude-1000/guard-r3-*.sh`)
`guard-r3-scratch-diff.sh` (declared-vs-observed, both directions):
```bash
#!/usr/bin/env bash
# Declared-vs-observed RED diff for the guard contract against the PRE-AUDIT conftest (c99210b) in the scratch copy.
# usage: guard-r3-scratch-diff.sh <scratch> <declared-file> <log>
set -uo pipefail
S="$1"; DECLARED="$2"; LOG="$3"
{ echo "conftest md5: $(md5sum "$S/conftest.py" | cut -d' ' -f1)"
  echo "contract md5: $(md5sum "$S/skills/lore-deploy/tests/test_prod_store_guard.py" | cut -d' ' -f1)"
  echo "loremaster.__file__: $("$S/.venv/bin/python" -c 'import loremaster; print(loremaster.__file__)')"
} > "$LOG" 2>&1
cd "$S/skills/lore-deploy/scripts" || exit 2
LORE_PYTHON="$S/.venv/bin/python" systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 \
  "$S/.venv/bin/python" -m pytest -q ../tests/test_prod_store_guard.py --timeout=300 -p no:cacheprovider -rfEs >> "$LOG" 2>&1
echo "PYTEST_EXIT=$?" >> "$LOG"
grep -E '^(FAILED|ERROR) ' "$LOG" | sed -E 's/^(FAILED|ERROR) //; s/ - .*$//' | sort -u > "$LOG.observed"
echo "DECLARED=$(wc -l < "$DECLARED") OBSERVED=$(wc -l < "$LOG.observed")" >> "$LOG"
echo "--- unexpected reds (observed, not declared):" >> "$LOG"; comm -13 "$DECLARED" "$LOG.observed" >> "$LOG"
echo "--- declared reds that stayed GREEN:" >> "$LOG"; comm -23 "$DECLARED" "$LOG.observed" >> "$LOG"
U=$(comm -13 "$DECLARED" "$LOG.observed" | wc -l); G=$(comm -23 "$DECLARED" "$LOG.observed" | wc -l)
echo "VERDICT: $([ "$U" -eq 0 ] && [ "$G" -eq 0 ] && echo EXACT || echo MISMATCH) unexpected=$U stayed_green=$G" >> "$LOG"
```
`guard-r3-c6-loop.sh` (C6 flake measurement):
```bash
#!/usr/bin/env bash
# C6 flake measurement: run the xdist leg N times in a row; count runs with any red.
# usage: guard-r3-c6-loop.sh <repo-tree> <python> <contract-file-under-tests/> <N> <log>
set -uo pipefail
TREE="$1"; PY="$2"; FILE="$3"; N="$4"; LOG="$5"
cd "$TREE/skills/lore-deploy/scripts" || exit 2
: > "$LOG"; reds=0
for i in $(seq 1 "$N"); do
  out=$(LORE_PYTHON="$PY" systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 \
        "$PY" -m pytest -q "../tests/$FILE" -k TestGuardIsLiveInEveryXdistWorker --timeout=300 -p no:cacheprovider -rfE 2>&1); rc=$?
  line=$(printf '%s\n' "$out" | grep -E '[0-9]+ (passed|failed)' | tail -1)
  echo "run $i rc=$rc $line" >> "$LOG"
  if [ "$rc" -ne 0 ]; then reds=$((reds+1)); printf '%s\n' "$out" | grep -E '^(FAILED|ERROR)|Errno' | head -5 >> "$LOG"; fi
done
echo "C6_SUMMARY: $reds/$N runs red" >> "$LOG"
```
Declared set (`/var/tmp/claude-1000/guard-r3-declared.txt`, written from `--collect-only` BEFORE any scratch run, selected by the rule "doors the audit §3 probe showed the pre-audit guard misses (alias, `0.0.0.0`, `::`, bytes, `0.0.0.0` URL) × {serial scripts, serial tests, xdist} + the accept pin on the two sessions containing those doors"):
```
../tests/test_prod_store_guard.py::TestGuardIsLiveInEveryXdistWorker::test_every_door_fails_under_xdist[test_door_raw_connect_reaching_loopback[bytes-host]]
../tests/test_prod_store_guard.py::TestGuardIsLiveInEveryXdistWorker::test_every_door_fails_under_xdist[test_door_raw_connect_reaching_loopback[hosts-alias]]
../tests/test_prod_store_guard.py::TestGuardIsLiveInEveryXdistWorker::test_every_door_fails_under_xdist[test_door_raw_connect_reaching_loopback[unspecified-ipv4]]
../tests/test_prod_store_guard.py::TestGuardIsLiveInEveryXdistWorker::test_every_door_fails_under_xdist[test_door_raw_connect_reaching_loopback[unspecified-ipv6]]
../tests/test_prod_store_guard.py::TestGuardIsLiveInEveryXdistWorker::test_every_door_fails_under_xdist[test_door_urlopen_health_on_unspecified_address]
../tests/test_prod_store_guard.py::TestProductionPortAttemptsFailTheAttemptingTest::test_every_destination_reaching_loopback_fails_and_names_the_port[test_door_raw_connect_reaching_loopback[bytes-host]-scripts]
../tests/test_prod_store_guard.py::TestProductionPortAttemptsFailTheAttemptingTest::test_every_destination_reaching_loopback_fails_and_names_the_port[test_door_raw_connect_reaching_loopback[bytes-host]-tests]
../tests/test_prod_store_guard.py::TestProductionPortAttemptsFailTheAttemptingTest::test_every_destination_reaching_loopback_fails_and_names_the_port[test_door_raw_connect_reaching_loopback[hosts-alias]-scripts]
../tests/test_prod_store_guard.py::TestProductionPortAttemptsFailTheAttemptingTest::test_every_destination_reaching_loopback_fails_and_names_the_port[test_door_raw_connect_reaching_loopback[hosts-alias]-tests]
../tests/test_prod_store_guard.py::TestProductionPortAttemptsFailTheAttemptingTest::test_every_destination_reaching_loopback_fails_and_names_the_port[test_door_raw_connect_reaching_loopback[unspecified-ipv4]-scripts]
../tests/test_prod_store_guard.py::TestProductionPortAttemptsFailTheAttemptingTest::test_every_destination_reaching_loopback_fails_and_names_the_port[test_door_raw_connect_reaching_loopback[unspecified-ipv4]-tests]
../tests/test_prod_store_guard.py::TestProductionPortAttemptsFailTheAttemptingTest::test_every_destination_reaching_loopback_fails_and_names_the_port[test_door_raw_connect_reaching_loopback[unspecified-ipv6]-scripts]
../tests/test_prod_store_guard.py::TestProductionPortAttemptsFailTheAttemptingTest::test_every_destination_reaching_loopback_fails_and_names_the_port[test_door_raw_connect_reaching_loopback[unspecified-ipv6]-tests]
../tests/test_prod_store_guard.py::TestProductionPortAttemptsFailTheAttemptingTest::test_every_destination_reaching_loopback_fails_and_names_the_port[test_door_urlopen_health_on_unspecified_address-scripts]
../tests/test_prod_store_guard.py::TestProductionPortAttemptsFailTheAttemptingTest::test_every_destination_reaching_loopback_fails_and_names_the_port[test_door_urlopen_health_on_unspecified_address-tests]
../tests/test_prod_store_guard.py::TestTheRefusalHappensBeforeTheConnectionLeavesTheProcess::test_production_stub_accepts_no_connection_in_a_guarded_session[guarded_runs]
../tests/test_prod_store_guard.py::TestTheRefusalHappensBeforeTheConnectionLeavesTheProcess::test_production_stub_accepts_no_connection_in_a_guarded_session[xdist_run]
```

## Noticed (outside this change — surfaced, not acted on)
1. **Scaffold rejects hyphenated project directories (likely real defect, lore-deploy).** `_scaffold_lore_yaml` seeds `project.slug` from `project.name` verbatim; `LoreConfig` requires `^[a-z0-9][a-z0-9_]*$`. Probed 2026-10-31: a project dir named `some-project` → `RuntimeError: scaffolded … failed schema validation: project.slug String should match pattern`. So `lore-deploy setup` on any repo whose directory contains a hyphen or capital (e.g. `odoo-custom`, `transcribe-craig`) fails at scaffold time. Not filed as a finding by me (outside my writable scope's subject); recommend the lead files it. *"Do you want this raised as a lore finding / fixed in this wave?"*
2. **HEAD moved during my run**: `308251f` → `ef56833` (`test(gated_ground): … ancestor of a testpath is execution-covered (#566)`, only `scripts/test_gated_ground.py`). It does not touch `conftest.py` (md5 `f31db77b` throughout) or my file. My final receipts are at HEAD `ef56833`.
3. **The test-store port (`TEST_STORE_PORT = 18000`) has the same drift shape C2 closed for production** (a literal citing CLAUDE.md). It matters less (a drift only makes the benign pins dial an unused port, which the stub serves anyway, so they stay meaningful), so I left it. Raise if the lead wants it derived too.
4. **The quiet-host flake rate is ~0** (old contract 0/20 on a quiet host vs 6/60 under 4-way load): the audit's 2/20, 3/20 were measured with other runs in flight. A flake of this class only shows under contention, so "20 consecutive greens" on a quiet host would not have proven anything; the matched-load comparison is the actual evidence.
5. In-image conformance (r2 fork F1): this contract now also needs a mount namespace + `MS_BIND`. Any environment that allows an unprivileged user+net namespace normally allows the mount namespace too (same capability, inside the new userns), but if one doesn't, every test SKIPS with `ISOLATION-UNAVAILABLE: OSError(…bind-mount…)` — loud, never un-isolated.
6. A haiku-runner ran two of my commands concurrently despite the brief's "in order" (the scratch diff and the old-contract baseline, both in the scratch tree, read-only). Both results stand (no shared writable state; the diff's verdict was EXACT); recorded because a runner's order deviation is otherwise invisible.

## Final gates (final contract md5 `26309830f6cbe42623973db7c758eb44`, committed conftest `f31db77b`, HEAD `08acd90`, TREE `d4eed997…`; haiku-runner, RAN lines checked against my commands)
| gate | result |
|---|---|
| build leg, real tree: `cd skills/lore-deploy/scripts && systemd-run … uv run python -m pytest -q ../tests/test_prod_store_guard.py --timeout=300 -p no:cacheprovider -rfEs` | **91 passed in 12.40s**, EXIT=0, no FAILED/ERROR/SKIPPED (log `/var/tmp/claude-1000/guard-r3-final2-build.log`) |
| C6, xdist leg 20 consecutive, real tree | **0/20 red** (each `25 passed, 66 deselected`), `guard-r3-c6-final2.log` |
| scratch, pre-audit conftest `a7c0118b`, `loremaster.__file__ = /var/tmp/claude-1000/guard-r3-scratch/loremaster/loremaster/__init__.py` | `17 failed, 74 passed` · **DECLARED=17 OBSERVED=17 · VERDICT: EXACT unexpected=0 stayed_green=0** (`guard-r3-scratch-diff-final2.log`) |
| `uv run ruff check skills/lore-deploy/tests/test_prod_store_guard.py` | All checks passed (EXIT=0) |
| `pending_contract_gate.py --currency --legs typecheck,ruff` | typecheck **RED_ADJUDICATED** (83 residuals, packet-58-contract / packet-64b-i-contract — the same 83 as the audit's §8; my file contributes 0) · ruff **GREEN** · pytest NOT_RUN (by design with `--legs`, #565) → **RED_ORPHANED 0 on the run legs**. CURRENCY_EXIT=1 comes only from the NOT_RUN pytest leg. |

**Runs used** (more than ~2, reason: the brief itself asks for the scratch proof + 20× xdist, and a mid-run type fix and a DRY fix each forced one re-run of the batch):
- build leg ×3 — 91/91/91 passed (first inline at md5 `15948105`, then `858b338a`, final `26309830`);
- scratch declared-vs-observed ×3 — EXACT each time (17/17);
- C6: quiet new 40× (0 red), quiet old 20× (0 red), matched-load old 60 (6 red) / new 60 (0 red), final 20× twice (0 red each);
- ruff ×3, currency ×3 (first found my `no-any-return` orphan → fixed).
The full suite was not run (contract round; CLAUDE.md TEST SCOPE). Targeted scope = this contract file (it is the guard's whole behaviour suite; `conftest.py` is the only production symbol it covers).

Fan-out: haiku 8 (7 runners + 1 worker) · sonnet 0 · peak 3. Kept as tier 3: contract design, door/fixture choice, the C6 root-cause read, the declared set, every verdict.
