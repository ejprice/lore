brief-base v25 read
brief project v7 read

# REPORT-storeref-66: packet 66 close-out, the store reference's SDK 3.0.0 update (2026-11-08)

## SUMMARY
- **State: done-with-deviations.** The one file edited is `docs/reference/surrealdb-31-capabilities.md`: +293 / −22 lines, uncommitted (the lead commits). Base `88b06be`.
- **The headline fact to act on:** [MEASURED 2026-11-08] `lore-lore` is still on SDK 2.0.0. It runs image `43122071…` (`localhost/lore:latest`, built 2026-08-18), whose venv holds `surrealdb 2.0.0`. The repo and its tests are on 3.0.0; the served production container is not. §0b says so as a dated fact.
- **Deviations:**
  1. I edited four places outside the brief's named sections (header line 21, §2, §5, §7 row, §9 recovery line). Each is a sentence the retired-name sweep found false or stale under SDK 3.0.0 / 3.3.5. Each fix is an in-place note that keeps the old text as history.
  2. I added the `#601` anchor entry to the finding-anchor list.
  3. §0b cites `REPORT-storeref-66.md` (this file) as archived under `docs/plans/v2/receipts/2026-11-08-sdk3/`. **The lead must archive it there**, or that citation dangles.
- **Packages considered:** none. No mechanism was specified (doc only; the probe is an instrument).
- **Odoo-20 portability:** n/a. No Odoo seam was touched.
- **Reuse ledger:** none. No product symbols were added.
- **Graded:** n/a. This is a doc author's report, not a verdict.
- **Decisions needed:**
  1. Archive this report, `probe_storeref66.py` and its log next to the other packet-66 receipts.
  2. Sweep the five residuals I flagged and did not fix: the §0 corpus tag, `lore.env` secrets in the store containers, the 3.3.5 SELECT-on-missing-table behaviour, the vendor executing-queries page, and the unarchived scout-40 / build66 / audit66 probes. Details are in §Flags.
- **Receipt pointers:** §Edited sections · §Facts added · §Facts left out · §Retired-name sweep · §Probe (instrument verbatim + log) · §Verification.

## Capability check
- Demanded: edit the one file, read the archived receipts, probe `:18000` only, use lore_comms. I have all of it. No gaps.
- Deadline: none in the brief.

## Routing table (written before the first sweep)
| step | tier | who | reason |
|---|---|---|---|
| Read target doc header/§0a/§3/§6.5/§6.6/§9 | 3 | me | the doc wording is the deliverable; it is served law, and an error there seals itself |
| Extract receipts per fact from builder/servicer/coldaudit/conform/adversary/rulings (~3.7k lines) | 3 (my own targeted greps, one batch at a time) | me | each fact's receipt has to be JUDGED: is it a measurement or a restated claim? A sampled draft would miss a receipt that is a ruling's claim rather than a measurement (the #107 class) |
| Retired-name grep over the target doc | 1 (small, inline) | me | about 30 patterns over one 1.3k-line file; small output that I read in full; the verdicts are doc wording, so they are mine |
| Probes on `:18000` | 3 | me | probe design and controls are judgment |
| Doc edits | 3 | me | rule/doc wording is never-Haiku |
| Verify every added claim against its cited receipt | 2 | Sonnet (`general-purpose`, model sonnet) | rule-decidable (does source X say Y?), and I check it by sampling; this is the fresh-context pass the global "never grade your own work" rule requires |

Fan-out: haiku 0 · sonnet 1 · peak 1. Test runs: none (doc-only change; the probe is an instrument, not a gate).

## Edited sections
| section | change |
|---|---|
| Header, lines 3–10 | SDK line: `surrealdb==3.0.0` exact pin, the 2.0.0 history kept, and a note that 3.0.0-changed sections carry a `(SDK 3.0.0, packet 66: …)` marker |
| Header, line ~21 | "the live 3.2.4 store" gains a note that the stores run 3.3.5 since 2026-11-07 (**out of the brief's named scope**: a stale engine sentence) |
| READ THIS FIRST, item 4 | Rule kept ("never multi-statement via `query()`; `execute_transaction`"). The SDK-2.0 mechanism is marked history, and the 3.0.0 mechanism is added |
| **§0b (new)**, placed before §0a (the file runs newest first) | 17 bullets plus one table, below |
| §2 `str(RecordID)` bullet | struck through and marked FALSE on 3.0.0, with the old claim quoted (**out of scope**) |
| §3 | statement[0] bullet marked HISTORY + a 3.0.0 note; `query_raw` still ridden ([CODE]); `_RETRYABLE_CONFLICT_KIND` deleted → `is_transaction_conflict`; the #111 "no predicate" claim marked 2.0.0, with 3.0.0 shipping both; the in-flight `KeyError` bullet marked HISTORY with 3.0.0 behaviour |
| §5 #124 paragraph | statement[0] put in past tense as 2.0.0 history (**out of scope**) |
| §6.5 | a note: the vendor sentence is false on 3.0.0 too, in a third way (query returns ALL); 2.0.0 line numbers flagged; the vendor page NOT re-checked |
| §6.6 #10 | marked SDK 2.0.0 only, plus what remains ours alone |
| §6.6 #15 (new) | SDK 3.0.0 facts that rest only on our measurement, labelled **CANDIDATES, not swept against vendor docs** |
| §7 RecordID-hashability row | 3.0.0 note: hashable (**out of scope**) |
| §9 OPS | recovery image corrected to the exact `v3.3.5` tag (re-read from the quadlet), the old `v3.2` text kept as history (**out of scope**: stale since 2026-11-07); a new #601 bullet: never `--help` in a store container, read flags from the surrealdb-docs tier, and the safe export recipe |
| Finding anchors | `<a id="601">` entry added |

## Facts added (§0b), each with its receipt
| # | fact | receipt (durable address) |
|---|---|---|
| 1 | lore-lore runs image `43122071…`, built 2026-08-18, with SDK 2.0.0; `latest` was untouched by 66 | my run 2026-11-08: `podman inspect lore-lore` → `4312207128bb…`; `podman run --rm --entrypoint /app/.venv/bin/python localhost/lore:latest -c 'importlib.metadata.version("surrealdb")'` → `surrealdb 2.0.0`. Also R19 Q1; `REPORT-conform-66.md` §Teardown (`latest` before = after `4312207128bb…`) |
| 2 | pin `surrealdb==3.0.0` in pyproject + uv.lock; image installs via `uv sync --locked --all-packages`; in-image version 3.0.0; `__version__` absent | [CODE] `loremaster/pyproject.toml:31`, `uv.lock` (`name = "surrealdb"` / `version = "3.0.0"`), `Containerfile` `RUN uv sync --locked --all-packages`; commit `9863c11`; `REPORT-conform-66.md` §Step 1/2 |
| 3 | `query()` answers one entry per statement and raises the first ERR | [CODE] SDK `builders.py::_QueryState._statement_values`; storeref-66 S1 |
| 4 | without BEGIN, statements after the failing one still apply | storeref-66 S2: `ThrownError: boom`, rows `[[1, 2]]` |
| 5 | inside BEGIN…COMMIT, query() raises the first cascade notice (`NotExecuted`), not the THROW | storeref-66 S2b; R7 W6 (same for a conflict) |
| 6 | `one_statement_result` = one entry or `SurrealStoreError` (seam rule R2/R8 F13) | [CODE] `_txn.one_statement_result`; storeref-66 S1 refusal leg; R2 (the `[[]]` 8/8 measurement) |
| 7 | harness `run()` answers the FIRST statement and fails closed on empty/non-list | [CODE] `tests/_surreal_harness.py::run`; R19 (C10 overturned in part) |
| 8 | `QueryError.is_transaction_conflict` + `QueryDetailKind.TRANSACTION_CONFLICT` in SDK 3.0.0; `_RETRYABLE_CONFLICT_KIND` deleted | [CODE] SDK `errors.py` (`TRANSACTION_CONFLICT = "TransactionConflict"`, `def is_transaction_conflict`); builder FINAL fate table row 2, `df84764` |
| 9 | outcome-unknown class, its scope, and the Q6 advice constant | [CODE] `_txn.SurrealOutcomeUnknownError` docstring, `_txn.OUTCOME_UNKNOWN_ADVICE`; R5 rider 2, R9 D1, R12 F18/F-b, R19 Q6 |
| 10 | streaming/timeout commit semantics (cancel commits nothing; `streaming=False` + timeout commits) | **R7** (scout-40-sdk3's measurement). ⚠ That scout's report sits at an unarchived scratchpad path, so the ruling text is the only durable record. Stated in the doc |
| 11 | factory: `ReconnectOptions(-1, 0.5, 2.0)`, 30 s default, 300 s overrides via `long_operation` | [CODE] `_txn.SURREAL_RECONNECT`, `SURREAL_REQUEST_TIMEOUT_SECONDS`, `ENSURE_READY_/INDEX_TRANSACTION_TIMEOUT_SECONDS`, `SURREAL_STREAMING = True`; R5 |
| 12 | `_await_reconnect` bounded only by the request timeout → `TransportTimeoutError`; in-flight → `ConnectionUnavailableError`, not re-sent | [CODE] SDK `async_ws.py::_await_reconnect`; R5 grounds |
| 13 | first connect to a down store raises `ConnectionUnavailableError` (scout keeps its ladder); no `websockets.*` class in 120 legs | `REPORT-builder-66.md` §C-row table rows #21, #9 |
| 14 | `kill()` parks until the timeout (40/40, 30 s); `with connection.timeout(2.0)`; 2.00 s vs 30.00 s; worst case 2·N; not stdlib timeout | R41 FORK T, `5e464bc`; `RULING-13.md`; `_txn.TEARDOWN_KILL_TIMEOUT_SECONDS` docstring; builder §DEFECT + deviation 2 |
| 15 | `close()` idempotent: SDK docstring; 40/40 over a severed socket; a double close raises nothing; 18 wrappers retired; pin `5fb57fc` | [CODE] SDK `async_ws.py` `close` docstring "Idempotent."; builder C-row #16; storeref-66 S6; R41 FORK S `6b43b65` |
| 16 | `PreciseDatetime` decode keeps ns; THE cursor codec pair; `parse_instant` 1–9 digits | [CODE] `_txn.served_instant_text` / `parse_served_instant`; R43 B1 `fda1411`; RULING-14 §B1; storeref-66 O2 (9 digit counts + round-trip) |
| 17 | `PreciseDatetime ==`/`<` ignore ns; use engine order / `stamp_key` | #593; R44; [CODE] `stamp_paging.stamp_key`; storeref-66 O3 (control: a different µs) |
| 18 | Python 3.14 `fromisoformat` truncates 9 → 6 silently (#590's root) | RULING-14 §Read (measured on 3.14.7); #590 body; storeref-66 O1 (control: 6 digits exact) |
| 19 | `db.batch()` reports the cancellation notice, not the THROW (#588) | `REPORT-builder-66.md` §R-9 row #14 + C-row #14; finding #588 |
| 20 | record-id text table (engine / `str()` / parse round-trip); hashable on 3.0.0 | storeref-66 S3 (engine vs record_text vs str, 6 keys), O4, O5; `d41aa47`; R7; audit `probe_record_text` (`REPORT-coldaudit-66.md` §Instruments) |
| 21 | `> $since` admits array/object/uuid/record, excludes string/number/float/bool/null/duration/NONE | R45 S6; `REPORT-coldaudit-66.md` §DELTA-2 item 4b; storeref-66 S4; #597 / R46 (`de6e116`, `d2df34c`) |
| 22 | `option<datetime>` SCHEMAFULL: NULL rejected, Python None → NONE | `REPORT-coldaudit-66.md` §DELTA-2 item 7; storeref-66 S5 (controls: string rejected, datetime accepted; `is_none=True, is_null=False`) |
| 23 | bound record-id range → RecordIdScan / Union, exact; audit CONFIRMED; RETIRE owed; owed-packet notes | `REPORT-builder-66.md` §R-9 row "#25 cand. 2"; `REPORT-coldaudit-66.md` §DELTA item 5 + residual D-4; R43 §ADDENDUM |
| 24 | `INSERT … ON DUPLICATE KEY UPDATE` parity with per-row UPSERT CONTENT; statement cap → row cap 50,000 (warn 10,000); R3's 5,113 statements | `REPORT-builder-66.md` §Progress log + §R-9 X13; `66a9979`; [CODE] `_txn.TXN_ROW_HARD_CAP`/`TXN_ROW_WARN_THRESHOLD`; R3, R4 |
| 25 | `/import` 4 GiB cap: HTTP 413 measured; vendor table; `snapshot_entry` 6.25 GB | `REPORT-conform-66.md` §Step 4b; finding #603 |
| 26 | Q4: keepalive `ping_interval=30.0` / `ping_timeout=10.0`; version gate `MINIMUM 2.0.0` / `MAXIMUM 5.0.0`, `version_check=True` | [CODE] SDK `__init__.py:358-361`, `features.py:19-20`; packet doc rows #29/#30; R19 Q4 |
| §9 | #601 rule + safe export recipe | finding #601 body; `REPORT-conform-66.md` §INCIDENT + §Step 4; [MEASURED] both quadlets load `EnvironmentFile=…/lore.env`, which defines `SURREAL_USER`/`SURREAL_PASS` (key names read with `grep -oE '^[A-Za-z_]+='`; no values printed) |
| §9 | recovery image is `v3.3.5` | [MEASURED] `lore-surreal.container`: `Image=docker.io/surrealdb/surrealdb:v3.3.5` |

## Facts left out (and why)
- **The vendor `executing-queries` page's current wording**: not re-checked. The surrealdb-docs tier search returned the multi-language `via-sdks.mdx` example, not the Python page §6.5 quotes. The doc says "NOT re-checked".
- **Whether the engine-side cross-type ordering explains the `> $since` set**: not established. The doc says so rather than guess.
- **3.3.5: `SELECT * FROM <never-created table>` raises `NotFoundError`** (seen in my run 1 at S2b, `probe_storeref66_run1.log`). It is a single observation, outside the brief's list, and I have no control for it. Left out; it's a candidate for §2/§7 if someone probes it with a control.
- **SDK 3.0.1's backtick form**: cited as R7 only. I did not probe it (3.0.1 is not installed).
- **SurrealKV/RocksDB streaming-cancel semantics**: unprobed per R7; stated as R7's bound.
- **The #29 instrument detail "SDK closes the socket ~10 s after its next ping"**: I cite the packet doc's instrument note but did not re-measure it. The doc words it as "starves the pong", and the number is not restated.

## Retired-name sweep (post-edit, bare patterns, `docs/reference/surrealdb-31-capabilities.md`)
Patterns: `_safe_close`, `TXN_STATEMENT`, `statement cap`, `statement\[0\]`, `KeyError`, `2\.0\.0`, `>=2\.0`, `_RETRYABLE_CONFLICT_KIND`, `_check_query_result`, `ConnectionClosedError`, `_ensure_connection`, `str\(RecordID\)`, `WebSocketException`, `UNHASHABLE`, `silent partial`, `swallow`, `v3\.2[^.0-9]`, `live 3\.2\.4`. Zero hits: `HARD_CAP` (except row 2 below), `_bare_id`, `_txn_conflict_backoff`, `_to_aware_utc`, `UPSERT per`, `fromisoformat`/`isoformat` (pre-edit). Final line numbers come from the last sweep (§Verification).

Verdict key: CURRENT (states 3.0.0 truth or describes the retirement) · HISTORY (marked 2.0.0 history in place) · HISTORICAL (inside a dated section; true when written; left unedited) · UNRELATED (a different `KeyError` / version / swallow).

Final line numbers, at the edited tree after the verifier corrections; each hit gets its own verdict.

| pattern | line | section | verdict |
|---|---|---|---|
| `_safe_close` | 172 | §0b close() | CURRENT (describes the retirement) |
| `TXN_STATEMENT` | 259 | §0b INSERT | CURRENT (the deletion) |
| `statement cap` | 257 | §0b INSERT | CURRENT (what retired it) |
| `statement[0]` | 42 | READ THIS FIRST #4 | HISTORY |
| `statement[0]` | 733 | §3 | HISTORY (bullet marked, 3.0.0 note follows) |
| `statement[0]` | 997 | §5 #124 | HISTORY (past tense + note) |
| `statement[0]` | 1456 | #144 anchor | HISTORICAL (finding summary, true of 2.0.0; not edited) |
| `KeyError` | 159 | §0b factory | CURRENT (arm retired) |
| `KeyError` | 644, 648 | §2 projection | UNRELATED (dict KeyError on a missing column) |
| `KeyError` | 796, 797 | §3 note | CURRENT (3.0.0 note) |
| `KeyError` | 800, 802, 804, 810 | §3 in-flight bullet | HISTORY (bullet marked) |
| `KeyError` | 1184 | §6.6 #12 | UNRELATED (`SELECT *` NONE column) |
| `2.0.0` | 9, 10 | header | HISTORY (the "before that" clause) |
| `2.0.0` | 42 | READ THIS FIRST #4 | HISTORY |
| `2.0.0` | 74, 87, 90, 111, 221 | §0b | CURRENT (dated measurement / pointers) |
| `2.0.0` | 271 | §0b Q4 | UNRELATED (`MINIMUM_VERSION = "2.0.0"`, the server-version gate) |
| `2.0.0` | 361 | §0 (dated 2026-07-22) | HISTORICAL ("our pin" was true then; not edited) |
| `2.0.0` | 655 | §2 | HISTORY |
| `2.0.0` | 733 | §3 | HISTORY |
| `2.0.0` | 783 | §3 retry bullet | HISTORICAL (an existing superseded-note) |
| `2.0.0` | 792 | §3 #111 | HISTORY + 3.0.0 note |
| `2.0.0` | 795, 799, 801, 811 | §3 in-flight | HISTORY |
| `2.0.0` | 997, 999 | §5 | HISTORY |
| `2.0.0` | 1115 | §6.5 | HISTORY (3.0.0 note follows) |
| `2.0.0` | 1122, 1124 | §6.5 note | CURRENT |
| `2.0.0` | 1167 | §6.6 #10 | HISTORY |
| `2.0.0` | 1259 | §7 row | HISTORY + 3.0.0 note |
| `>=2.0` | 8 | header | HISTORY |
| `_RETRYABLE_CONFLICT_KIND` | 122 | §0b | CURRENT (deleted) |
| `_RETRYABLE_CONFLICT_KIND` | 776 | §3 | HISTORY ("decided", + note) |
| `_check_query_result` | 734 | §3 | HISTORY |
| `ConnectionClosedError` | 802, 803, 804, 810 | §3 in-flight | HISTORY |
| `_ensure_connection` | 806 | §3 in-flight | HISTORY (the symbol still exists in 10+ production modules, so the name is not dead) |
| `str(RecordID)` | 99, 200, 203 | §0b | CURRENT |
| `str(RecordID)` | 655, 658 | §2 | CURRENT (the FALSE-on-3.0.0 correction) |
| `WebSocketException` | 158 | §0b | CURRENT (retired) |
| `UNHASHABLE` | 1259 | §7 row | HISTORY + note |
| `silent partial` | 735 | §3 | HISTORY |
| `swallow` | 1166, 1168 | §6.6 #10 | HISTORY + note |
| `swallow` | 1218 | §6.7 | UNRELATED (`/import` errors) |
| `v3.2` | 5, 16 | header | HISTORICAL (floating-tag narrative) |
| `v3.2` | 282 | §0a | CURRENT (rollback warning) |
| `v3.2` | 600 | §2 probe label | HISTORICAL (dated label) |
| `v3.2` | 1358 | §9 | HISTORY note |
| `live 3.2.4` | 23 | header | HISTORY (3.3.5 note added) |


## Flags (raised, not fixed — outside my writable set or my brief; each is a question for the lead)
1. **Production still serves SDK 2.0.0** (fact 1). The next `lore-deploy start` that rebuilds from HEAD ships SDK 3.0.0 to `:18500`'s client. Is that deploy owed in this close-out, or in packet 65?
2. **`lore.env` is shared by both store containers and carries `ANTHROPIC_API_KEY`, `LORE_TEI_KEY` and `QDRANT__SERVICE__API_KEY` as well as the Surreal credentials** (key names only were read). The store containers hold secrets they do not use, so any env echo inside them (#601's class) leaks those too. Do you want a least-privilege env file for the stores (operator/ops decision)?
3. **§0's corpus note says the `surrealdb-docs` / `surrealql-tests` tiers are "pinned at the `v3.2.0` tag"**, while the repo CLAUDE.md says they moved to 3.3 / v3.3.5 on 2026-11-07. It is not SDK-related and not in my brief, so I left it; I can fix it in one line on your word.
4. **Probe instruments behind several cited rows live only in lead scratch** (`build66/probes/`, `audit66/probe_since_type_set.py`, `audit66/probe_option_datetime_null.py`, scout-40's `scratchpad/scout40/`). The archived reports cite them but do not paste them. My probe re-measures S3/S4/S5/O1–O5 so those rows have a durable instrument; #14 / #25 / X13 / #9 / #16 / R7 do not. Archive the scratch dirs (conform report decision 2 asks the same)?
5. `REPORT-builder-66.md` C-row #9 and RULING-13 name `probe_c_proxy.py`; §0b cites the builder table, not the probe.

## Probe — instrument (verbatim) and receipts
- Command: `cd loremaster && { tree_id.sh /home/ejprice/PycharmProjects/lore; sha256sum probe_storeref66.py; timeout 120 uv run python probe_storeref66.py; echo EXIT=$?; } > probe_storeref66.log 2>&1`
- Final log `probe_storeref66.log`: `HEAD=88b06be` · `DIRTY_FILES=5` (the lead's 5 untracked receipt files; no doc edit had been made yet) · `TREE=408ecd09e2d7…` · probe sha256 `d3eb06d7b943…` · surrealdb 3.0.0 at the repo venv, Python 3.14.7, store `ws://127.0.0.1:18000/rpc` (engine `surrealdb-3.3.5` by `curl /version`) · **28 PASS, FAILS=[], EXIT=0** · throwaway DB `test_storeref66_e10e5f…` REMOVED (cleanup leg PASS).
- Earlier runs (kept beside it): `probe_storeref66_run1.log`, EXIT=1 (the S2b leg crashed on `NotFoundError` reading the rolled-back table; its `finally` still removed the DB; cleanup PASS); `probe_storeref66_run2.log`, EXIT=0 (before the O5 leg was added).
- Store safety: only `:18000`; namespace `lore_test`; each run's DB removed in `finally`. `:18500` was never contacted. No `surreal --help` anywhere.

### `probe_storeref66.py` (verbatim)
```python
"""probe_storeref66 — re-measures the SDK 3.0.0 facts the store reference §0b states (storeref-sdk3-66, 2026-11-08).

Offline legs (O*) need no store. Store legs (S*) run ONLY against the TEST store ws://127.0.0.1:18000 in one
throwaway database that is REMOVED in `finally`. Every leg prints a decisive line and a CONTROL; the script
exits non-zero if any expectation fails. Run: `cd loremaster && uv run python <this file>`.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime, timezone

import surrealdb
from surrealdb import RecordID
from surrealdb.data.types.datetime import PreciseDatetime, parse_instant

from loremaster.store._txn import (
    SurrealStoreError,
    one_statement_result,
    open_surreal_connection,
    record_text,
)

TEST_URL = "ws://127.0.0.1:18000/rpc"  # the TEST store; never :18500
TEST_USER, TEST_PASS = "root", "spikeroot"  # tests/_surreal_harness.py spike defaults
NAMESPACE = "lore_test"
DATABASE = f"test_storeref66_{uuid.uuid4().hex}"
FAILS: list[str] = []


def check(label: str, condition: bool, detail: object) -> None:
    """Print one leg's verdict; record a failure."""
    print(f"{'PASS' if condition else 'FAIL'} {label}: {detail}")
    if not condition:
        FAILS.append(label)


def offline() -> None:
    """O1–O4: stdlib/SDK datetime and RecordID facts, no store."""
    nine = "2026-11-08T18:17:45.186697518+00:00"
    parsed = datetime.fromisoformat(nine)
    check("O1 fromisoformat truncates 9->6 silently", parsed.microsecond == 186697 and parsed.isoformat() == "2026-11-08T18:17:45.186697+00:00", parsed.isoformat())
    six = "2026-11-08T18:17:45.186697+00:00"
    check("O1 control: 6 digits round-trip exact", datetime.fromisoformat(six).isoformat() == six, six)
    for digits in range(1, 10):
        text = "2026-11-08T18:17:45." + "123456789"[:digits] + "Z"
        instant = parse_instant(text)
        check(f"O2 parse_instant {digits} digit(s)", isinstance(instant, PreciseDatetime) and instant.isoformat_with_nanoseconds().startswith("2026-11-08T18:17:45." + "123456789"[:digits]), instant.isoformat_with_nanoseconds())
    round_trip = parse_instant("2026-11-08T18:17:45.186697518Z").isoformat_with_nanoseconds()
    check("O2 codec round-trip keeps ns", round_trip == "2026-11-08T18:17:45.186697518Z", round_trip)
    a = parse_instant("2026-11-08T18:17:45.186697001Z")
    b = parse_instant("2026-11-08T18:17:45.186697002Z")
    check("O3 PreciseDatetime == ignores ns", (a == b) is True and (a < b) is False, f"ns {a.nanosecond}/{b.nanosecond}: eq={a == b} lt={a < b}")
    c = parse_instant("2026-11-08T18:17:45.186698001Z")
    check("O3 control: a different microsecond compares", (a == c) is False and (a < c) is True, f"eq={a == c} lt={a < c}")
    renders = {key: str(RecordID("kt", key)) for key in ("abc", "01JABCDEFGHJKMNPQRSTVWXYZ0", "42", "a-b", 42)}
    print(f"INFO O4 SDK str(RecordID): {renders}")
    word = RecordID("kt", "abc")
    check("O5 control: a word key round-trips through str/parse", RecordID.parse(str(word)) == word, str(word))
    broken = {key: RecordID.parse(str(RecordID("kt", key))) == RecordID("kt", key) for key in ("01JABCDEFGHJKMNPQRSTVWXYZ0", "a-b", 42)}
    check("O5 str(RecordID) does NOT round-trip for digit-led / non-word / int keys", not any(broken.values()), broken)
    check("O5 RecordID is hashable on 3.0.0", len({word, RecordID("kt", "abc")}) == 1, "set of two equal ids has 1 member")


async def store() -> None:
    """S1–S6 against one throwaway database on the TEST store."""
    connection = open_surreal_connection(TEST_URL)
    await connection.signin({"username": TEST_USER, "password": TEST_PASS})
    await connection.query(f"DEFINE NAMESPACE IF NOT EXISTS {NAMESPACE}")
    await connection.use(NAMESPACE, DATABASE)
    await connection.query(f"DEFINE DATABASE IF NOT EXISTS {DATABASE}")
    try:
        # S1 result shape
        two = await connection.query("RETURN 1; RETURN 2;")
        one = await connection.query("RETURN 1;")
        check("S1 query() answers one entry per statement", two == [1, 2] and one == [1], f"two={two!r} one={one!r}")
        try:
            one_statement_result(two)
            check("S1 seam refuses a two-statement answer", False, "no raise")
        except SurrealStoreError as error:
            check("S1 seam refuses a two-statement answer", True, type(error).__name__)
        check("S1 control: seam selects a one-statement answer", one_statement_result(one) == 1, one_statement_result(one))
        # S2 a LATER statement fails, no transaction
        try:
            result = await connection.query("CREATE probe_a:1 SET v = 1; THROW 'boom'; CREATE probe_a:2 SET v = 2;")
            raised = f"NO RAISE, result={result!r}"
        except Exception as error:  # the class is the measurement
            raised = f"{type(error).__module__}.{type(error).__name__}: {error}"
        rows = await connection.query("SELECT VALUE record::id(id) FROM probe_a ORDER BY id;")
        check("S2 a later statement's failure RAISES from query()", not raised.startswith("NO RAISE"), raised)
        print(f"INFO S2 rows left (no BEGIN: each statement its own txn): {rows!r}")
        control = await connection.query("CREATE probe_b:1; CREATE probe_b:2;")
        check("S2 control: two good statements raise nothing", isinstance(control, list) and len(control) == 2, f"{len(control)} entries")
        # S2b the same inside BEGIN/COMMIT
        try:
            await connection.query("BEGIN; CREATE probe_c:1; THROW 'boom'; COMMIT;")
            raised_txn = "NO RAISE"
        except Exception as error:
            details = getattr(error, "details", None)
            raised_txn = f"{type(error).__name__} kind={getattr(error, 'kind', None)!r} details={details!r}: {error}"
        try:
            rows_txn: object = await connection.query("SELECT * FROM probe_c;")
        except Exception as error:  # 3.3.5: SELECT over a never-created table raises NotFoundError
            rows_txn = f"{type(error).__name__}: {error}"
        nothing_committed = rows_txn == [[]] or (isinstance(rows_txn, str) and rows_txn.startswith("NotFoundError"))
        check("S2b in-transaction THROW raises and nothing commits", raised_txn != "NO RAISE" and nothing_committed, f"{raised_txn} · rows={rows_txn!r}")
        # S3 engine id text vs record_text vs str(RecordID)
        keys: list[object] = ["abc", "01JABCDEFGHJKMNPQRSTVWXYZ0", "4558tc0abc", "42", "a-b", 42]
        for key in keys:
            await connection.query("CREATE $id;", {"id": RecordID("kt", key)})
            engine = one_statement_result(await connection.query("RETURN <string> $id;", {"id": RecordID("kt", key)}))
            parts = record_text(RecordID("kt", key))
            print(f"INFO S3 key={key!r}: engine={engine!r} record_text={parts!r} str={str(RecordID('kt', key))!r} equal={engine == parts}")
        # S4 `> $since` type set (SCHEMALESS table)
        await connection.query(
            "CREATE st:string SET v = '2030-01-01T00:00:00Z'; CREATE st:number SET v = 5; CREATE st:float SET v = 1.5;"
            " CREATE st:bool SET v = true; CREATE st:null SET v = NULL; CREATE st:duration SET v = 1h;"
            " CREATE st:array SET v = [1]; CREATE st:object SET v = {a: 1}; CREATE st:uuid SET v = rand::uuid();"
            " CREATE st:record SET v = kt:abc; CREATE st:after SET v = d'2030-01-01T00:00:00Z';"
            " CREATE st:before SET v = d'2000-01-01T00:00:00Z'; CREATE st:none;"
        )
        since = datetime(2020, 1, 1, tzinfo=timezone.utc)
        admitted = sorted(one_statement_result(await connection.query("SELECT VALUE record::id(id) FROM st WHERE v > $since;", {"since": since})))
        print(f"INFO S4 admitted by `v > $since` (datetime 2020-01-01): {admitted}")
        check("S4 control: datetime-after admitted, datetime-before excluded", "after" in admitted and "before" not in admitted, admitted)
        check("S4 admits exactly {array, object, record, uuid, after}", admitted == sorted(["array", "object", "record", "uuid", "after"]), admitted)
        # S5 option<datetime> on SCHEMAFULL: NULL vs Python None
        await connection.query("DEFINE TABLE sf SCHEMAFULL; DEFINE FIELD n ON sf TYPE string; DEFINE FIELD t ON sf TYPE option<datetime>;")
        outcomes: dict[str, str] = {}
        for label, statement, params in (
            ("literal NULL", "CREATE sf:null SET n = 'a', t = NULL;", None),
            ("string (control)", "CREATE sf:string SET n = 'b', t = 'x';", None),
            ("datetime (control)", "CREATE sf:dt SET n = 'c', t = $t;", {"t": since}),
            ("python None", "CREATE sf:pynone CONTENT $content;", {"content": {"n": "d", "t": None}}),
        ):
            try:
                await connection.query(statement, params) if params else await connection.query(statement)
                outcomes[label] = "accepted"
            except Exception as error:
                outcomes[label] = f"rejected ({type(error).__name__})"
        stored = one_statement_result(await connection.query("SELECT t = NONE AS is_none, t = NULL AS is_null FROM ONLY sf:pynone;"))
        print(f"INFO S5 outcomes: {outcomes}; sf:pynone stored: {stored!r}")
        check("S5 literal NULL rejected; None accepted; controls as expected", outcomes["literal NULL"].startswith("rejected") and outcomes["string (control)"].startswith("rejected") and outcomes["datetime (control)"] == "accepted" and outcomes["python None"] == "accepted" and stored.get("is_none") is True, outcomes)
    finally:
        await connection.query(f"REMOVE DATABASE IF EXISTS {DATABASE};")
        gone = await connection.query("INFO FOR NS;")
        check("cleanup: throwaway DB removed", DATABASE not in str(gone), DATABASE)
        await connection.close()
        try:
            await connection.close()
            check("S6 close() twice raises nothing", True, "ok")
        except Exception as error:
            check("S6 close() twice raises nothing", False, f"{type(error).__name__}: {error}")


def main() -> int:
    """Run every leg; non-zero on any failed expectation."""
    import importlib.metadata

    print(f"PROVENANCE python={sys.version.split()[0]} surrealdb={importlib.metadata.version('surrealdb')} at {surrealdb.__file__} store={TEST_URL} db={DATABASE}")
    offline()
    asyncio.run(store())
    print(f"FAILS={FAILS}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### `probe_storeref66.log` (verbatim)
```text
HEAD=88b06be6d80a2088df8a34f3ca43687a9e441694
DIRTY_FILES=5
TREE=408ecd09e2d7951295a1d5f3e3e277431aa2f227962acdec306ecebc273119f5
d3eb06d7b943e2d21c77e854594379ebf22de9f649bd6cf2560de776ae63a15d  /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/d68febab-e1d4-4ed2-95a0-0ded042fa32c/scratchpad/closeout66/probe_storeref66.py
PROVENANCE python=3.14.7 surrealdb=3.0.0 at /home/ejprice/PycharmProjects/lore/.venv/lib/python3.14/site-packages/surrealdb/__init__.py store=ws://127.0.0.1:18000/rpc db=test_storeref66_e10e5f4550784c4985c610ade80c1acd
PASS O1 fromisoformat truncates 9->6 silently: 2026-11-08T18:17:45.186697+00:00
PASS O1 control: 6 digits round-trip exact: 2026-11-08T18:17:45.186697+00:00
PASS O2 parse_instant 1 digit(s): 2026-11-08T18:17:45.100000000Z
PASS O2 parse_instant 2 digit(s): 2026-11-08T18:17:45.120000000Z
PASS O2 parse_instant 3 digit(s): 2026-11-08T18:17:45.123000000Z
PASS O2 parse_instant 4 digit(s): 2026-11-08T18:17:45.123400000Z
PASS O2 parse_instant 5 digit(s): 2026-11-08T18:17:45.123450000Z
PASS O2 parse_instant 6 digit(s): 2026-11-08T18:17:45.123456000Z
PASS O2 parse_instant 7 digit(s): 2026-11-08T18:17:45.123456700Z
PASS O2 parse_instant 8 digit(s): 2026-11-08T18:17:45.123456780Z
PASS O2 parse_instant 9 digit(s): 2026-11-08T18:17:45.123456789Z
PASS O2 codec round-trip keeps ns: 2026-11-08T18:17:45.186697518Z
PASS O3 PreciseDatetime == ignores ns: ns 1/2: eq=True lt=False
PASS O3 control: a different microsecond compares: eq=False lt=True
INFO O4 SDK str(RecordID): {'abc': 'kt:abc', '01JABCDEFGHJKMNPQRSTVWXYZ0': 'kt:⟨01JABCDEFGHJKMNPQRSTVWXYZ0⟩', '42': 'kt:⟨42⟩', 'a-b': 'kt:⟨a-b⟩', 42: 'kt:42'}
PASS O5 control: a word key round-trips through str/parse: kt:abc
PASS O5 str(RecordID) does NOT round-trip for digit-led / non-word / int keys: {'01JABCDEFGHJKMNPQRSTVWXYZ0': False, 'a-b': False, 42: False}
PASS O5 RecordID is hashable on 3.0.0: set of two equal ids has 1 member
PASS S1 query() answers one entry per statement: two=[1, 2] one=[1]
PASS S1 seam refuses a two-statement answer: SurrealStoreError
PASS S1 control: seam selects a one-statement answer: 1
PASS S2 a later statement's failure RAISES from query(): surrealdb.errors.ThrownError: An error occurred: boom
INFO S2 rows left (no BEGIN: each statement its own txn): [[1, 2]]
PASS S2 control: two good statements raise nothing: 2 entries
PASS S2b in-transaction THROW raises and nothing commits: QueryError kind='Query' details={'kind': 'NotExecuted'}: The query was not executed due to a failed transaction · rows="NotFoundError: The table 'probe_c' does not exist"
INFO S3 key='abc': engine='kt:abc' record_text='kt:abc' str='kt:abc' equal=True
INFO S3 key='01JABCDEFGHJKMNPQRSTVWXYZ0': engine='kt:01JABCDEFGHJKMNPQRSTVWXYZ0' record_text='kt:01JABCDEFGHJKMNPQRSTVWXYZ0' str='kt:⟨01JABCDEFGHJKMNPQRSTVWXYZ0⟩' equal=True
INFO S3 key='4558tc0abc': engine='kt:4558tc0abc' record_text='kt:4558tc0abc' str='kt:⟨4558tc0abc⟩' equal=True
INFO S3 key='42': engine='kt:`42`' record_text='kt:42' str='kt:⟨42⟩' equal=False
INFO S3 key='a-b': engine='kt:`a-b`' record_text='kt:a-b' str='kt:⟨a-b⟩' equal=False
INFO S3 key=42: engine='kt:42' record_text='kt:42' str='kt:42' equal=True
INFO S4 admitted by `v > $since` (datetime 2020-01-01): ['after', 'array', 'object', 'record', 'uuid']
PASS S4 control: datetime-after admitted, datetime-before excluded: ['after', 'array', 'object', 'record', 'uuid']
PASS S4 admits exactly {array, object, record, uuid, after}: ['after', 'array', 'object', 'record', 'uuid']
INFO S5 outcomes: {'literal NULL': 'rejected (InternalError)', 'string (control)': 'rejected (InternalError)', 'datetime (control)': 'accepted', 'python None': 'accepted'}; sf:pynone stored: {'is_none': True, 'is_null': False}
PASS S5 literal NULL rejected; None accepted; controls as expected: {'literal NULL': 'rejected (InternalError)', 'string (control)': 'rejected (InternalError)', 'datetime (control)': 'accepted', 'python None': 'accepted'}
PASS cleanup: throwaway DB removed: test_storeref66_e10e5f4550784c4985c610ade80c1acd
PASS S6 close() twice raises nothing: ok
FAILS=[]
EXIT=0
```


## Verification
- **The fresh-context verifier** (Sonnet, `general-purpose`; it read the diff plus every cited source, and checked the findings through lore). Output: `closeout66/VERIFY-storeref-66.md`: **claims_checked=80 · supported=73 · overstated=4 · unsupported=1 · wrong_source=2.**
- **I sampled 3 of its rows against text I had read myself.** All 3 hold:
  - R7's pin reason is "3.0.1 unpublished", not the `str(RecordID)` change;
  - "30 s until measured" is R5 F4b, not R19 Q2;
  - "120 legs" is in the FINAL fate table, not C-row #9.
- **All 7 non-SUPPORTED rows were fixed in the doc:**
  1. the audit GO is qualified by #598 reading (b);
  2. the conformance PASS is quoted as "PASS for the SDK-3 artifact, with named holes";
  3. this report is now "to be archived";
  4. the pin reason was corrected;
  5. the 30 s ruling is now R5 F4b;
  6. the 120-legs citation was moved;
  7. the F18 claim now says the pins were NOT counted by this reference.
- **Also fixed:**
  - the §9 env sentence is now dated, with a [MEASURED] tag;
  - I removed a `lore_search` hint I had added and never run.
- **Not re-verified after the corrections:** the verifier ran on the pre-correction diff, and the 7 fixes are mine and unverified. They narrow claims only, never widen them.
- **Deviation, idle-gate:** the hook looked for `REPORT-storeref-sdk3-66.md` (my spawn name). The brief names `REPORT-storeref-66.md` in this directory, and the brief's location wins (brief-base §1). I wrote a declared-artifact contract, but the hook did not resolve the absolute path in it.

