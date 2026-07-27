# REPORT-investigate-hardkill-reaper

brief-base v7 read

**state:** done-with-deviations
**deviations:**
1. **I contaminated the test store, 64 databases' worth, before I understood the engine.** My
   first census called `connection.use(ns, "__probe_no_such_db__")` to page through namespaces.
   On SurrealDB ≥3.0 in regular (non-strict) mode **`USE` CREATES a missing namespace/database**
   — so I minted `__probe_no_such_db__` in all 64 namespaces. Disclosed in full in §7, with the
   exact cleanup statements. I removed nothing (the brief forbids it).
2. **Q3 required creating databases** (the brief's Q3 sanctions constructing a sparse control
   namespace). I created a new namespace `q3probe_ns` (118 databases) and 15 `q3cost_*`
   databases inside `lore_test`. All names are enumerated in §7.
3. **Two of my own probes were WRONG and I caught both** — a SIGINT result that was an artefact
   of bash `SIG_IGN`, and a production probe that read the wrong statement's result. Both are
   written up in §4.1 and §5 rather than quietly corrected, because the corrected answers
   *reverse* the naive ones.

**Packages considered:**
- *SIGTERM-safe teardown* → **`_pytest` / `pytest-xdist`**: READ — grepped both installed trees
  for `SIGTERM|signal.signal`, **zero hits**; neither installs any SIGTERM handling. `atexit`
  (stdlib): READ + MEASURED — does **not** run under default SIGTERM or SIGKILL (§4.2), so it
  cannot serve. Verdict **`bespoke`** — ~5 lines of stdlib `signal`, minimal-surface gap-fill
  (packages-over-hand-rolling, side 2: the package demonstrably does not do the job).
- *Orphan-database janitor* → **`psutil`** (pid-liveness reaping): `absent`, and REJECTED on
  merit not availability — 291 of the orphans carry **no pid at all** (§1) and pids are reused
  across boots, so pid-liveness is unsound as a safety predicate. Verdict **`bespoke`** *(and
  NOT RECOMMENDED — see Q6)*.

**decisions-needed:**
- Cleanup authorisation for the 197 databases + 1 namespace I created (§7). I deleted nothing.
- Whether to fix the **23 hand-rolled clones of `unique_database()` across 22 test modules** (§1.3)
  — a `#102` ONE-IMPLEMENTATION violation that drops the pid entirely in 22 sites and **fakes it**
  in the 23rd (a MAC-derived constant, `24043` on this box, on 11 live orphans). It destroys the
  only ownership signal a reaper could use. Outside what I was asked; the operator's call.
- `spike-surreal`'s resident set is **13.4 GB** on a 9.9 MB store (§3.4). Measured NOT
  attributable to the orphan catalog. Unexplained; surfaced, not investigated.

---

## SUMMARY BLOCK

| Q | Answer (measured 2026-07-26, ~18:37–19:05 EDT, spike-surreal `ws://127.0.0.1:18000`) |
|---|---|
| **Q1** | **555 CONFIRMED** in `lore_test` — but only **254 look like `test_<pid>_<uuid4>`** (11 of those carry a **fake** pid); **291 are `test_<uuid4>` with NO pid**, from **23 hand-rolled clones of the mint**. Plus **63 orphan NAMESPACES** #240 never mentioned. §1 |
| **Q2** | **Nothing on the store dates a database** — 23 of 25 sampled orphans carry no timestamp, 9 are entirely empty. Coarse bound only: ≈**26/day** mean since 2026-07-05. §2 |
| **Q3** | **Essentially free.** ~331 bytes/db disk; `INFO FOR NS` 0.23 ms → 1.73 ms (sparse vs 556-db control); **zero** effect on connect, `use`, `DEFINE DATABASE`, or RSS. §3 |
| **Q4** | **Ctrl-C is SAFE** (teardown runs). **Default SIGTERM and SIGKILL orphan**, in every shape incl. xdist. Surprise: killing the xdist *controller* is safe — surviving workers reap on EOF. §4 |
| **Q5** | **Production is CLEAN** — 2 namespaces, 3 databases, **0 test-shaped**; positive control saw 565 on the test store. Bonus: a real **credential barrier** blocks the harness defaults at :18500. §5 |
| **Q6** | **Recommend a SIGTERM handler in the test harness — NOT a reaper.** Measured to close the dominant orphan source with **zero** risk of deleting a live database. §6 |

**RECOMMENDATION (one):** install a `SIGTERM` handler in the harness/conftest that routes SIGTERM
into the already-working Ctrl-C unwinding path, **plus a pin recording the accepted bound**
(SIGKILL is uncatchable; the existing litter is accepted at its measured cost). Reject the
age-based sweep and the systemd timer *for now*: the measured cost of the litter is ~nil, while a
reaper's failure mode — deleting a live database out from under a running test — is real and was
**observed live during this very investigation** (§4.4).

**RE-OPEN TRIGGER for building the janitor:** any one of — `INFO FOR NS` on `lore_test` exceeds
**50 ms** (≈10× today's 1.73 ms, i.e. roughly 15–20k databases); OR a `spike-surreal` restart is
measured to be slowed by the catalog (NOT measured — §8); OR anyone needs to enumerate test
databases interactively and the population makes that impractical. On trigger, build the
**two-snapshot janitor** in §6.4 — the only design I found that is provably safe without any
per-database timestamp.

---

## 1. Q1 — the census, re-derived

Root credentials for the test store are **`root` / `spikeroot`** (the `_surreal_harness` defaults),
**not** the `SURREAL_USER`/`SURREAL_PASS` in the quadlet's `EnvironmentFile` — those are denied at
:18000. That mismatch is load-bearing and reappears as a safety property in §5.2.

### 1.1 Counts

`INFO FOR ROOT` → **64 namespaces** (65 after I created `q3probe_ns`).

`INFO FOR NS` under `lore_test`, 2026-07-26 18:38 EDT, shape-classified:

| shape | count | note |
|---|---:|---|
| `test_<pid>_<uuid4hex>` | **254** | 172 distinct "pids" — but **11 carry a MAC-derived fake pid**, §1.3 |
| `test_<uuid4hex>` (**no pid**) | **291** | a *second*, hand-rolled mint — §1.3 |
| `audit_<pid>_<uuid4hex>` | 2 | an audit wave's own harness clone |
| `smoke03b_probe_<hex8>` | 3 | packet-03b smoke |
| unmatched | 5 | `lore_test`, `main`, `m9495n5`, `m9495n50`, `x` — verdicts in §1.2 |
| **pre-existing total** | **555** | **exactly #240's figure, independently re-derived** |

Reproduce (read-only; select an EXISTING database so `use` cannot create one):

```python
c = AsyncSurreal("ws://127.0.0.1:18000/rpc")
await c.signin({"username": "root", "password": "spikeroot"})
raw = await c.query_raw("USE NS lore_test; INFO FOR NS;")   # NOT query() — see §5.1
databases = sorted(raw["result"][1]["result"]["databases"])
```

### 1.2 Every unmatched name gets its own verdict
("all remaining hits are X" is banned output — CLAUDE.md.)

| name | verdict |
|---|---|
| `lore_test` | a database named after the namespace; non-test-shaped; **leave** |
| `main` | SurrealDB's conventional default database name; **leave** |
| `m9495n5`, `m9495n50` | hand-typed probe names from an earlier session; orphan litter, **but not harness-minted** |
| `x` | a one-character hand-typed probe database; orphan litter |
| `__probe_no_such_db__` | **MINE** — see deviation 1 / §7 |

### 1.3 The finding #240 did not have: TWO populations, and the pid field is decorative

CLAUDE.md and `unique_database()`'s docstring both rest the `-n auto` safety argument on the pid
prefix: *"a concurrent pytest process on the SAME server never collides on, or reaps, this
database."* **That guarantee is stated over a set 291 members of which do not carry a pid — and
some of the ones that appear to are lying.**

⚠ **I got this count wrong first and caught it, which is itself the finding.** My initial pass used
a partially-anchored grep and reported **nine** modules. The **bare, anchor-free** sweep — the one
CLAUDE.md mandates precisely because prose and format-strings carry no structural anchors — returns
**22 modules / 23 sites**. Derivation, verbatim and re-runnable:

```
$ grep -rnE 'f"test(_bulk)?_\{uuid' loremaster/tests/*.py | wc -l
23
$ grep -rlE 'f"test(_bulk)?_\{uuid' loremaster/tests/*.py | wc -l
22
```

The 22 (all under `loremaster/tests/`, the symbol is `_slug` in every case except
`test_extension`, whose two sites are methods): `test_cli`, `test_comms_wiring`,
`test_eager_startup`, `test_eager_startup_survives_unparseable_file`, `test_extension`
(**2 sites**), `test_graph_wiring`, `test_impact`, `test_indexer`, `test_indexer_bulk_sweep`
(`test_bulk_` prefix), `test_indexer_chunker_fault_isolation`, `test_indexer_contextualized`,
`test_map`, `test_mcp_server`, `test_memory_cutover`, `test_reconcile`, `test_resilient_db`,
`test_schema_rebuild`, `test_search`, `test_startup_divergence_reconcile`,
`test_static_snapshot_reacquire`, `test_watcher`, `test_workspace_status`. Against **one**
canonical mint, `_surreal_harness.unique_database`.

**And one of them fakes the pid.** `test_startup_divergence_reconcile._slug` mints
`f"test_{uuid.getnode() % 100000}_{uuid.uuid4().hex}"` — a **MAC-address-derived constant** wearing
the pid slot. Its own docstring shows the reasoning that got it there: *"A uuid4-based slug is
unique enough that it also serves directly as a collision-free per-test Surreal database name …
**so no separate `unique_database()` call is needed**."* The author knew the shared mint existed and
argued past it — and the `getnode()` prefix is documented nowhere as not-a-pid. On this box:

```
$ python -c "import uuid; print(uuid.getnode()%100000)"
24043
$ grep -c "test_24043_" <the lore_test name list>
11
```

So **11 of the 254 databases I classified as `test_<pid>_<uuid4>` carry no pid at all** — they carry
`24043`, a value that is *identical on every run on this machine, forever*, and that will collide
with a real process the moment the kernel hands out pid 24043.

Grep fallback declared (tool honesty, brief-base §4): I used grep, not lore's graph, for all of
this. It is case (2), a non-symbol textual seam — the duplicated thing is a *string format*, not a
called symbol — and case (1), exhaustiveness where one missed site changes the conclusion.
`lore_impact` on `unique_database` cannot see a clone that never calls it, and indeed would report
a small consumer set while 23 sites route around it.

Four consequences, in ascending order of importance:
1. A straight `#102` **ONE IMPLEMENTATION** violation — 23 sites needing one policy, cloned rather
   than called, while `unique_database()` sits imported in the same package.
2. Collision safety survives (uuid4 alone suffices), so **no test is broken today**. That is exactly
   why no gate sees it, and why it has been free to spread to 22 files.
3. **It destroys the only ownership signal.** For 291 databases there is no way — even in principle
   — to ask "which process owns this?".
4. **Worse than absent: the signal is misleading where it exists.** A reaper keyed on pid liveness
   would treat `test_24043_*` as owned by a dead process (usually true, occasionally catastrophically
   false) and is blind to 291 more. **Pid-liveness reaping is unsound.** This is what forces the
   Q6 design away from any age/ownership heuristic derived from the name.

### 1.4 The namespace-level litter #240 did not count

63 of the 64 namespaces are themselves orphan probe litter: `bl_<hex8>` ×21, `vb_<hex8>` ×30
(each holding one `vd_<hex8>` database), plus `adv5`, `blindreader`, `blindreader2`, `diagns`,
`docsprobe`, `lore_probe`, `lore_probe_seq`, `lore_proof_c1e`, `probe`, `probe210`, `probe_ns`,
`main`. Only `lore_test` is the harness's own. Store-wide pre-existing total: **617 databases**
across 64 namespaces. A reaper scoped to `lore_test` would leave every one of these behind.

---

## 2. Q2 — is it growing, and how fast? (mostly: **I cannot tell, and here is why**)

### 2.1 Nothing on the store dates a database — measured, not assumed

`INFO FOR NS` returns only DDL text (`DEFINE DATABASE <name>`); there is no creation timestamp in
the catalog. I sampled **25 orphans** (seeded random, from the 18:38 name list), ran `INFO FOR DB`
on each and tried `created_at` / `trace_ts` / `updated_at` / `at` / `ts` / `mtime_ns` against every
table:

- **2 of 25** yielded a timestamp, both via `chunk.mtime_ns` (the harness's `chunk_record` stamps
  `time.time_ns()` at construction) → **2026-07-16**.
- **9 of 25 were completely EMPTY** (0 tables) — created by `connect_admin`/`bootstrap_session`
  and abandoned before any DDL ran. These carry *zero* dating information, by construction.
- The remaining 14 had schema but no rows in any timestamped table.

The table-shape histogram identifies which suite minted them (12/16/17-table shapes = the full
store schema; `hot`, `agent`, `brief`, `briefed` = comms/mint suites), but not *when*.

### 2.2 PID ordering does not rescue it

`pid_max = 4194304`; boot was 2026-07-25 09:03; the live pid counter during this session was
≈3.32 M. Orphan pids span **24043 … 4145553** — wider than one boot epoch. **110** databases carry
a pid *above* the current counter and so provably predate this boot; the other 144 pid-bearing
databases are undecidable; and **291 carry no pid at all**. Useless as a clock.

### 2.3 The only rate I can honestly state

RocksDB `IDENTITY` (written once at store creation) has mtime **2026-07-05 20:57**, and it is the
oldest file in `/home/ejprice/.local/state/lore/spike-surreal-data`. 555 orphans over ~20.9 days
⇒ **≈26.5 orphans/day, mean.** *Caveats, stated because this number will be inherited:* it assumes
the store began empty and was never rebuilt, it is a **mean over a period containing bursty
multi-agent packets** (two pids alone account for 62 databases), and it says nothing about the
current rate. **I did not measure an instantaneous rate.**

One negative datum that *is* precise: across the ~26 minutes of this session, a sibling agent ran
repeated `pytest` mutation proofs against this store (§4.4) and the net orphan count from those
runs was **zero** — one straggler was even reaped. Normal runs do not litter. **Only kills do.**

### 2.4 The cheapest way to START measuring — two options, both verified

**(i) Zero repo change — a dated name-set snapshot.** One `INFO FOR NS` written to a dated file.
Diffing two snapshots gives both the exact rate *and*, for every future database, an arrival date.
This is also the safety mechanism in §6.4, so it is not throwaway work.

**(ii) One-line change — make the database self-dating.** SurrealDB supports
`DEFINE DATABASE [OVERWRITE|IF NOT EXISTS] @name [STRICT] [COMMENT @string]`, and I **verified on
this engine (3.2.1) that the COMMENT round-trips through `INFO FOR NS`** rather than trusting the
docs (repo law: the docs are a source, not an oracle — §6 of the store reference exists because
they have lied before):

```
stored DDL: "DEFINE DATABASE q3comment_3330177_3b0025ee95814aabb7c2378de25f660e COMMENT '2026-07-26T22:59:00Z'"
carries the stamp: True
```

So `bootstrap_session` could stamp every test database with its mint time for the cost of one
f-string, and *every* age question — dating, reaping, forensics — becomes a single `INFO FOR NS`.

---

## 3. Q3 — does it cost anything? (**measured: no**, with a control)

Design: the *same* operations against a **crowded** namespace (`lore_test`, 556 databases) and a
**sparse control** namespace (`q3probe_ns`, 1 database), 15 reps each. A single-leg timing would be
unfalsifiable.

### 3.1 Latency

| operation | SPARSE (1 db) | CROWDED (556 dbs) | verdict |
|---|---|---|---|
| `INFO FOR NS` | median **0.23 ms** | median **1.73 ms** | **the only real effect: +1.50 ms** |
| `DEFINE DATABASE` | median 3.98 ms | median 3.85 ms | no effect |
| `use()` on an open session | median 3.85 ms | median 4.97 ms | within noise (ranges overlap) |
| connect + signin + `use` | median 22.96 ms | median 22.99 ms | **no effect** |

`INFO FOR NS` scales at ≈2.7 µs/database. 10,000 orphans would cost ≈27 ms. The per-test setup
path — the one that runs thousands of times under `-n auto` — is **untouched**.

### 3.2 Disk

`du -sb` around the creation of 32 databases: 79,155,137 → 79,165,724 bytes = **+10,587 bytes**,
i.e. **≈331 bytes/database**. The 555 orphans therefore occupy ≈**184 KB**. The whole test store is
9.9 MB on disk (76 MB apparent).

### 3.3 Memory — attributed with a control, and the answer is "not the orphans"

Two phases of equal duration (20 s), because a sibling agent was hammering the store and ambient
drift would otherwise be read as signal:

```
phase A CONTROL   (20s,   0 creates)          : 13754.9 MB -> 13756.8 MB  drift= +2.0 MB
phase B TREATMENT (20s, 100 creates in 0.5s)  : 13756.8 MB -> 13752.6 MB  drift= -4.3 MB
create-attributable delta (B - A) = -6.2 MB for 100 databases
```

The treatment delta is *negative* — i.e. below ambient noise. **Catalog size is not what holds the
memory.**

### 3.4 …but the memory number itself deserves the operator's eye (out of scope, surfaced)

`spike-surreal` (pid 9923) `VmRSS` = **13.4 GB**, `VmHWM` = **14.9 GB**, on a **9.9 MB** store.
Production `lore-surreal` (pid 9921) `VmRSS` = **18.3 GB** on a 1.7 GB store. `podman stats`
reports 14.67 GB / 20.02 GB (cgroup `memory.current`, which includes page cache — the `VmRSS`
figures above are the real footprint). §3.3 proves this is *not* the orphan catalog. I did not
investigate further; it was not my brief. **Flagging it: 13.4 GB resident for a 9.9 MB test store
is not obviously right.**

---

## 4. Q4 — where teardown is, and exactly which kills defeat it

### 4.1 ⚠ First, the probe I got wrong — because the corrected answer is the opposite one

My first signal matrix reported *"SIGINT skips teardown"*. **It was an artefact.** Bash sets
`SIGINT`/`SIGQUIT` to `SIG_IGN` for an asynchronous (`&`) job started from a **non-interactive**
shell, so `kill -INT` was swallowed; what my probe actually measured was the `SIGKILL` it sent
3 s later as cleanup. The verification leg exposed it — the run printed `1 passed in 120.01s`,
`EXIT_CODE=0`, with the reap marker present. **The probe passed for the wrong reason and would
have shipped a false headline.** Fix: `set -m` (monitor mode) restores default dispositions and
gives each job its own process group, so `kill -INT -$pgid` is a faithful Ctrl-C. Every number
below is from the corrected (v2) runs.

### 4.2 The matrix (controls first)

Instrument: a `pytest_asyncio` async-generator fixture of exactly the harness's shape
(`_surreal_harness.surreal_env`) whose "database" is a marker file — so the experiment costs the
store nothing and a missed teardown is directly visible. A leftover `.live` with no `.reaped` **is**
the orphan condition. A second file repeats it with a *sync* fixture + `atexit` + an optional
`SIGTERM` handler.

| case | teardown ran | orphan left |
|---|---|---|
| **CONTROL** — async fixture, no signal | yes | no |
| **CONTROL** — async fixture, no signal, `-n 2` | yes | no |
| **CONTROL** — sync fixture, no signal | yes (+ `atexit` ran) | no |
| async, **SIGINT** → pid | **yes** | no |
| async, **SIGINT** → process group (a real Ctrl-C) | **yes** | no |
| async, **SIGINT** → group, `-n 2` | **yes** | no |
| async, **SIGTERM** (default disposition) | **NO** | **YES** |
| async, **SIGTERM** → xdist controller, `-n 2` | **NO** | **YES** |
| async, **SIGKILL** | **NO** | **YES** |
| async, **SIGKILL** → group, `-n 2` | **NO** | **YES** |
| sync, **SIGINT** → group | yes (+ `atexit` ran) | no |
| sync, **SIGTERM** default | **NO** (`atexit` did **not** run) | **YES** |
| sync, **SIGTERM** *with a handler installed* | **yes** (+ `atexit` ran) | no |
| sync, **SIGKILL** | **NO** | **YES** |

### 4.3 xdist, specifically — including one genuinely surprising result

Two tests, `-n 2`, both workers holding a database:

| case | reaped | orphans left |
|---|---:|---:|
| **SIGKILL → the workers** (controller lives) | 0 | **2** |
| **SIGTERM → the workers** (controller lives) | 0 | **2** |
| **SIGKILL → the controller** (workers survive) | **2** | **0** |

Killing the **controller** is safe: the workers detect the execnet channel EOF and shut down
*gracefully*, running teardown. (This cannot be an artefact of my own cleanup kill — that cleanup
is `SIGKILL`, which by definition runs no finalizer.) The database is held by the **worker**, so
what matters is which process dies.

### 4.4 The answer, stated plainly

**Teardown is defeated by exactly two things: default-disposition `SIGTERM`, and `SIGKILL`,
delivered to whichever process holds the database** (the worker, under `-n auto`). Ctrl-C is safe.
An orphan run leaks up to *N-workers* databases, plus any session-scoped ones.

Real-world sources of the defeating signals, in rough order of likelihood on this box: an agent
harness's `TaskStop` / a background-job timeout; the `timeout(1)` command; an IDE/CI "stop" button;
container or systemd session shutdown; the OOM killer (always `SIGKILL`). **Note that these are
all SIGTERM except the OOM killer** — which is why §6's recommendation is worth its five lines.

Teardown seams, for the record (all reap correctly; the orphans are *not* missing-teardown bugs):
`_surreal_harness.drop_database` (via `surreal_env` / `admin_db` `finally` blocks), and the
`_pending_surreal_slugs` autouse fixtures in `test_comms_wiring.py`, `test_memory_cutover.py`,
`test_workspace_status.py`. `conftest.py` has **no** session-scoped or `atexit` reaper — confirming
#240's core claim: **there is no reaper for the kill path anywhere.**

### 4.5 One live-fire observation that matters more than the matrix

Mid-investigation I found `INFO FOR NS` returning a **flapping set** — 556 vs 557 databases across
consecutive reads, with names appearing and vanishing. It was not engine non-determinism: a
**sibling agent was running `pytest` mutation proofs against this same store from a separate
checkout** (`/home/ejprice/scratch-fix11ia`, via `scripts/mutation_proof.py`), each short run
minting and reaping `test_<pid>_<uuid4>` databases seconds apart. The flapping names' pids sat just
below `/proc/sys/kernel/ns_last_pid`, i.e. very recently allocated and already exited.

**This is the Q6 hazard, observed live rather than imagined:** at any moment, databases on this
store may be owned by a *different process, in a different tree, that this repo knows nothing
about.* Any reaper design must survive it.

---

## 5. Q5 — production (**strictly read-only; clean**)

### 5.1 ⚠ The second probe I got wrong — and how the control caught it

My first production probe reported *"NS lore: 0 databases"* for every namespace. That is not
credible (lore-lore is live and serving from database `lore`). Cause: the SDK's
`AsyncWsSurrealConnection.query()` returns **only the first statement's result**
(`return response["result"][0]["result"]`), so my `USE NS x; INFO FOR NS;` chain handed back the
`USE`'s `NONE`, and `.get("databases", {})` on that rendered as an empty catalog. **An empty result
read as "no test databases found" — a clean negative for entirely the wrong reason.** Fixed with
`query_raw(...)["result"][1]["result"]`, and paired with a positive control.

### 5.2 The result

Statements issued against `ws://127.0.0.1:18500/rpc`: `INFO FOR ROOT`, then `USE NS <name>;
INFO FOR NS;` per namespace. **No `DEFINE`, no `REMOVE`, no `SELECT`, no `CREATE`, no `UPDATE`.**
The script never names a namespace or database that `INFO FOR ROOT` had not already proved exists
— necessary, because `USE` on this engine *creates* what is missing (§1, and my own deviation 1).

```
INFO FOR ROOT -> 2 namespace(s): ['lore', 'main']
  namespaces matching a TEST shape: NONE
  NS lore: 2 database(s) -> ['demand_intelligence', 'lore']   TEST-shaped: NONE
  NS main: 1 database(s) -> ['main']                          TEST-shaped: NONE

VERDICT: 0 test-shaped database(s) on PRODUCTION.
CONTROL (spike-surreal :18000 NS lore_test): 571 databases, 565 test-shaped -- the probe CAN see them.
```

**Production is clean. Nothing has ever pointed a test at :18500.**

### 5.3 Bonus finding — a credential barrier exists, and nothing documents it

The harness's built-in defaults (`_surreal_harness.DEFAULT_USER` / `DEFAULT_PASS` = `root` /
`spikeroot`) are **rejected by production**:

```
harness DEFAULT credentials (root/spikeroot) tried against both stores:
  TEST spike-surreal (CONTROL: must pass)  ws://127.0.0.1:18000/rpc: AUTHENTICATED
  PRODUCTION lore-surreal                  ws://127.0.0.1:18500/rpc: DENIED (NotAllowedError)
```

(Signin only; the connection was closed without issuing a statement. The control proves the client
works, so `DENIED` is a real barrier and not a broken probe.)

So a mis-set `LORE_TEST_SURREAL_URL` alone **cannot** let the suite create-and-remove databases on
production — it would also need `LORE_TEST_SURREAL_PASS`. This is a genuine safety property that
CLAUDE.md's *"never point tests at :18500"* rule does not mention, and it is worth writing down
before someone "helpfully" unifies the two stores' credentials and silently removes it. (The
quadlets share one `EnvironmentFile`, so the barrier exists only because the test store's root user
was baked in at creation and the env's `lore` user never took effect there — i.e. it is **accidental,
not designed.** That makes it exactly the kind of protection that vanishes in a routine cleanup.)

---

## 6. Q6 — the proposal (**do not implement; this is a recommendation**)

### 6.1 The four options, weighed against what was measured

**(a) Age-based sweep at harness session start.** *Cost:* real. There is no age signal today
(§2.1), so it must first build one. It runs **inside** pytest, where under `-n auto` all N workers
would race to sweep — needing a lock the harness does not have. *Cannot catch:* anything, if the
suite is never run again; and it leaves all 63 orphan namespaces (§1.4). *Misfire:* **deletes a
live database out from under a concurrent run** — not hypothetical, observed in §4.4. **Reject.**

**(b) `pytest` session finalizer / `atexit`.** **Measured dead on arrival:** `atexit` did not run
under default SIGTERM or SIGKILL (§4.2). On the paths where it *does* run (normal exit, Ctrl-C) the
existing per-test `finally` already reaps, so it adds exactly nothing. **Reject as written —**
but see 6.3 for the variant of it that *does* work.

**(c) systemd timer alongside the quadlets.** *Cost:* a new `.timer` + `.service`, i.e. real ops
surface whose whole job is deleting data. *Advantages:* runs out-of-process (no xdist race), works
even if the suite is never run again, and can reap orphan namespaces too. *Misfire:* same
live-database hazard, and worse — it fires unattended. **Defer** (it is the §6.4 design, held
behind the re-open trigger).

**(d) Nothing, with a pin.** *Cost:* zero. And the measured cost of the litter is ≈331 bytes/db,
+1.5 ms on one introspection call, and no memory (§3). On the numbers alone, **(d) is defensible**.
Its weakness is that it accepts the *guarantee* gap silently, which is the half of #240 the brief
correctly calls the interesting one.

### 6.2 Recommendation

**Install a `SIGTERM` handler in the test harness (conftest), and pin the residual bound.** This is
(b)-corrected fused with (d).

Measured, in the **real async fixture shape**, with a negative control:

| case | handler fired | teardown ran | orphan |
|---|---|---|---|
| **NEGATIVE CONTROL** — async, no handler, SIGTERM → group | no | **NO** | **YES** |
| **NEGATIVE CONTROL** — async `-n 2`, no handler, SIGTERM → group | no | **NO** | **YES** |
| async, handler raises `SystemExit` | yes | **yes** | no |
| async, handler raises `KeyboardInterrupt` | yes | **yes** | no |
| async `-n 2`, handler raises `KeyboardInterrupt` | yes | **yes** | no |
| async `-n 2`, handler raises `SystemExit` | yes | **yes** | no |

Both strategies work; I would pick `KeyboardInterrupt`, because it routes SIGTERM into the
**exact path that already measurably reaps cleanly** (§4.2's SIGINT rows) rather than opening a
second unwinding path with its own behaviour to discover. Roughly:

```python
# conftest.py — SIGTERM is the ONE defeating signal we can catch. #240.
def _reap_on_sigterm(signum, frame):
    raise KeyboardInterrupt("SIGTERM: unwinding so fixture teardown reaps its database")
signal.signal(signal.SIGTERM, _reap_on_sigterm)
```

**Why this and not a reaper — the safety argument in one line:** *it never touches a database
another process owns.* It only lets the process that created a database finish removing it. The
dangerous failure mode the brief names — reaping a live database — **cannot occur**, because no
deletion decision is ever made about a foreign name. That is worth more than the ~184 KB a janitor
would recover.

**What it CANNOT catch:** `SIGKILL` (uncatchable by construction — OOM killer, `kill -9`, a
`podman kill`), and any death before the handler is installed. Those keep leaking, at the measured
rate and the measured (nil) cost. **That residue is the accepted bound and gets the pin.**

**The pin** (CLAUDE.md: *when you cannot close a hole, PIN it*; and *a diagnosis is not an
instrument*): a test asserting the handler is installed and that a SIGTERM'd run leaves no orphan
— which goes RED the day someone removes it — carrying the message *"SIGKILL orphans remain a KNOWN
BOUND (#240). If you closed it deliberately, delete this pin and say so."* The v2 matrix script in
§4.2 is that instrument's skeleton, negative control included. **Note it must ship WITH the handler,
in the same change** — this repo's own law is that a rule shipped without its instrument is a hope.

### 6.3 A rider I am *not* dropping

The recommendation above has a second clause, and per CLAUDE.md's *THE RIDER IS PART OF THE RULING*
I am stating it in the same breath rather than a paragraph later: **the handler is worthless if it
is installed after the fixture has already created the database, and it must not clobber an
existing handler.** Install it at session start (a `pytest_configure` / session-scoped autouse
fixture), assert `signal.getsignal(SIGTERM)` was `SIG_DFL` before installing, and have the pin
check the install point, not merely the end state — otherwise a future refactor moves it and every
gate stays green.

### 6.4 If the trigger fires: the two-snapshot janitor (the only design I found that is safe)

Because **no timestamp exists** (§2.1) and **pid liveness is unsound** (§1.3), the age proof has to
come from somewhere else. It can come from the janitor's own history:

1. read `INFO FOR NS` → `S_now`;
2. read the previous snapshot file `S_prev`, **with its own recorded timestamp**;
3. if `S_prev` is younger than `AGE` (say 24 h), **reap nothing** and just write `S_now` — degrade safe;
4. otherwise reap `S_now ∩ S_prev`, minus a keep-list, minus anything not matching the test shapes;
5. write `S_now` as the new snapshot.

**Why it is safe:** a name in `S_prev` has existed for at least `AGE`. For a *live* test's database
to be reaped, that single test would have to have been running for ≥24 h. It needs no timestamp,
no pid, and no cooperation from the harness — so it covers the pid-less 291 and the 63 orphan
namespaces equally. It is also the §2.4(i) measurement instrument, so the rate gets measured as a
side effect.

Two mechanical constraints it must respect, both learned the hard way this session:
- **Never `use()` a database you intend to remove.** `USE` *creates* what is missing (vendor docs,
  `use.mdx`, Since v3.0.0; and my own 64-database contamination). Select only the namespace:
  `USE NS lore_test; REMOVE DATABASE <name>;` — `REMOVE DATABASE [IF EXISTS] @name` takes a bare
  name and operates in the current namespace (`remove.mdx` syntax block). *That last point is
  docs-verified, NOT probe-verified — I ran no `REMOVE`.* Probe it before shipping.
- **`INFO FOR NS` is a moving target under concurrency** (§4.5). Read it once, act on that snapshot,
  and tolerate a `REMOVE` failing because the owner already reaped it.

---

## 7. My contamination, in full — I deleted nothing

| what | where | count |
|---|---|---|
| `__probe_no_such_db__` | one in **each of the 64** original namespaces | 64 |
| `q3cost_3330177_<hex>` | `lore_test` | 15 |
| the namespace `q3probe_ns` itself + everything in it (`q3anchor_*`, `q3cost_*`, `q3comment_*`, `q3probe_anchor_readonly_never_written`, `q3mem_*` ×100) | `q3probe_ns` | 118 |
| **total databases created** | | **197** |

Store-wide count went 617 → 814 databases, 64 → 65 namespaces. `lore_test` went 555 → 571 (555
pre-existing + 1 `__probe_no_such_db__` + 15 `q3cost_*`).

**Cleanup, when authorised** (I am not authorised, and did not run it):

```surql
-- everything I created outside lore_test, in one statement:
REMOVE NAMESPACE IF EXISTS q3probe_ns;
-- then, per namespace, the 64 use()-materialised stubs:
USE NS <each>; REMOVE DATABASE IF EXISTS __probe_no_such_db__;
-- and in lore_test, the 15 cost-probe databases (names all match ^q3cost_3330177_):
USE NS lore_test; REMOVE DATABASE IF EXISTS q3cost_3330177_<hex>;   -- x15
```

Every `q3*` name is enumerated in the probe scripts' own output files; the 64 stubs share one
literal name. All 197 are matched by the regex `^(q3(cost|anchor|comment|mem|probe)_|__probe_no_such_db__$)`.

---

## 8. WHAT I DID NOT MEASURE

Stated explicitly so nobody inherits any of it as settled.

1. **Store startup / RocksDB open time as a function of catalog size.** This is the one plausible
   remaining cost, and it is the one I could not touch: measuring it means restarting
   `spike-surreal`, and a sibling agent was running `pytest` against it throughout (§4.4). Refused.
   *To measure later:* `systemctl --user restart spike-surreal.service` with nothing else running,
   timing to first successful `signin`, before and after a bulk reap.
2. **An instantaneous growth rate.** §2.3's ≈26/day is a **mean since 2026-07-05** over a bursty
   period, not a current rate. No rate was observed directly.
3. **Whether the 555 are load-bearing.** I did not check whether any orphan is referenced by a
   config, a fixture, a doc, or a running process. I assumed none are; I did not verify it. This
   matters before any cleanup.
4. **Whether `REMOVE DATABASE` works with only the namespace selected.** Docs say yes
   (`remove.mdx`); I ran no `REMOVE` of any kind, so this is unverified on 3.2.1.
5. **The 13.4 GB RSS's actual cause** (§3.4). I proved it is *not* the orphan catalog. I did not
   find out what it *is*.
6. **Query-path performance inside a populated namespace.** I measured catalog operations
   (`INFO FOR NS`, `DEFINE`, `use`, connect). I did not measure whether SELECT/INSERT throughput
   inside one database degrades with 556 siblings. I expect not (separate keyspaces), but I did
   not test it.
7. **Any real store operation under the SIGTERM handler.** The §6.2 matrix used marker files, not
   SurrealDB. A handler firing while the process is mid-`await` on the *socket* — with a real
   `drop_database` needing a **fresh** connection during unwinding — is the case that matters and
   is the first thing the implementing agent must prove. My async legs blocked in `asyncio.sleep`,
   which is the right *shape* but not the real I/O.
8. **`test_bulk_*` orphans.** `test_indexer_bulk_sweep.py` mints that prefix; none are currently
   present, so I could not characterise them. It uses a fake store, so it probably never creates
   one — probably, not verified.
9. **The `-n auto` worker count's effect on orphans-per-kill.** I measured `-n 2` (2 orphans per
   killed pair). `nproc` on this box is **64**, so a real `-n auto` kill plausibly orphans ~64
   databases at once — I did not run it to confirm the scaling is linear.
10. **`test_startup_divergence_reconcile`'s fake-pid collision hazard.** I established that
   `uuid.getnode() % 100000 = 24043` here and that 11 orphans carry it. I did **not** test what
   happens if a live process actually holds pid 24043, nor whether the value differs on other hosts.
