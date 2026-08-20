# REPORT — probe-unique-null-48

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **done**
- deviations: DDL applied via `query_raw` + explicit per-statement `status` checks (the brief's sanctioned "at minimum check every statement's status" path, store law §3), rather than wiring `execute_transaction`'s `acquire`/`drop` plumbing into a standalone probe. `query_raw` is the exact seam `execute_transaction` itself rides.
- Packages considered: `surrealdb` SDK 2.0.0 (`query_raw`) — **reused** (the project's own store SDK, already a dep); connection bootstrap **reused** `loremaster.store._txn.bootstrap_session` / `signin_credentials` (the production session seam) rather than cloning. No new mechanism specified.
- Reuse ledger: 1 potential-duplicate symbol — see DRY LEDGER below (`unique_database`, HAND-ROLLED with reason). Other script-local helpers (`run_one`/`expect`/`StatementOutcome`/`ProbeReport`) are probe-local, not reusable production symbols.
- Graded: engine `surrealdb-3.2.4` (spike-surreal, floating `v3.2` tag) · run at HEAD `9195839` · probe script new/untracked · verdict is a live engine measurement, not a code grade — SAME tree.
- decisions-needed: none (this probe RESOLVES the packet-48 `subject` schema fork; recommended schema below).
- VERDICT (crisp):
  1. **multiple-NONE under a plain UNIQUE index = ALLOWED** (constructed 4 coexisting NONE rows; count=4).
  2. **filtered / partial UNIQUE = NOT SUPPORTED** — parse error on every spelling; the engine grammar puts `WHERE` on `COUNT` indexes only.
  3. **same non-NONE subject rejected = YES**, on both `CREATE` and the Model-B `UPDATE` fill path (positive controls fired).
  - **Recommended schema for `principal.subject`: `DEFINE FIELD subject ON principal TYPE option<string>` + `DEFINE INDEX principal_subject_uniq ON principal FIELDS subject UNIQUE`.** No filtered index needed; NONE is exempt from uniqueness by construction.
- receipt POINTERS: instrument `scripts/probe_unique_nullable_48.py` (verbatim in §4, raw output §5); executable-spec §2; vendor grammar §2; live probe §3.

---

## 1. The question (packet-48 gate)

Provisioning **Model B**: admin pre-creates a principal by email BEFORE first login; the OAuth `subject` is filled later. So `principal.subject` is `option<string>`, and **multiple pre-created principals carry `subject = NONE` simultaneously**. We want `subject` UNIQUE (a real OAuth identity → ≤1 principal). Three unknowns, settled by construction:

- **Q1** Does a UNIQUE index over `option<string>` permit MULTIPLE NONE (unset) rows? *(If not, a plain `subject option<string> UNIQUE` breaks the 2nd `add <email>` — a real bug.)*
- **Q2** Is a FILTERED / PARTIAL unique index (`… UNIQUE WHERE subject != NONE`) valid on our engine?
- **Q3** Does the backstop hold: two rows with the SAME non-NONE subject rejected — on CREATE **and** on the Model-B UPDATE fill?

Method order per store law (#107): docs/specs FIRST, then CONSTRUCT the state and byte-observe. Positive controls required (trust doctrine).

---

## 2. Docs & specs read FIRST (store-law order)

**Store reference** (`docs/reference/surrealdb-31-capabilities.md`): **SILENT** on both UNIQUE-over-`option<>`-NONE and partial/filtered unique indexes (grepped the full file: no `partial`/`filtered`-index mention; the `UNIQUE` §§ cover relation-edge `UNIQUE(in,out)` and array-element index paths, not nullable-field uniqueness). So this is a genuine gap the probe fills — flagged in §6.

**The engine's own CI-verified SurrealQL spec — the executable oracle (a spec's expected-result cannot lie), pinned v3.2.0** answers Q1 directly:

`[SOURCE:surrealql-tests:tests/language/statements/create/create_on_none_values_with_unique_index.surql:1-18]`
```surql
/**
[test]
[[test.results]]   value = "NONE"                                    # the DEFINE INDEX returns NONE
[[test.results]]   value = "[{ id: foo:…, name: 'John Doe' }]"       # 1st NONE-valued row: created
[[test.results]]   value = "[{ id: foo:…, name: 'Jane Doe' }]"       # 2nd NONE-valued row: created
*/
DEFINE INDEX national_id_idx ON foo FIELDS national_id UNIQUE;
CREATE foo SET name = 'John Doe';   -- national_id omitted (NONE)
CREATE foo SET name = 'Jane Doe';   -- national_id omitted (NONE)
```
The filename is literally `create_on_none_values_with_unique_index`; both NONE-valued CREATEs succeed. **Caveat: this spec uses a SCHEMALESS table with an undeclared field — NOT our SCHEMAFULL `subject option<string>` shape** — so I confirmed our exact shape live (§3).

**Vendor grammar answers Q2** (`[SOURCE:surrealdb-docs:reference/query-language/statements/define/indexes.mdx]`, DEFINE INDEX special-clause grammar):
```
UNIQUE
| COUNT [ WHERE @condition ]
| FULLTEXT ANALYZER … | HNSW … | DISKANN …
```
`WHERE @condition` is attached to **`COUNT` only**; the `UNIQUE` clause has no `WHERE`. So a filtered/partial UNIQUE index is **not in the grammar**. (Vendor prose can lie — #107 — so I still probed the negative live; §3.) The unique-index example on the same page also documents the duplicate-rejection error text I reproduce as the Q3 control: *"Database index `…` already contains '…', with record `…`"*.

---

## 3. Live probe — CONSTRUCT + byte-observe (spike-surreal, engine 3.2.4)

`scripts/probe_unique_nullable_48.py` mints a throwaway `test_<pid>_<uuid4>` DB, applies a SCHEMAFULL table with `subject option<string>` + a plain `UNIQUE` index, constructs each state, byte-observes the per-statement engine result, and drops the DB. **Self-checking: exit 0 iff every expectation (including the positive controls) held.** Result: **exit 0**.

| Probe | Statement(s) | Result | Meaning |
|---|---|---|---|
| **Q1** | `CREATE probe:a1/a2/a3` (subject omitted) + `a4 subject = NONE` | all **OK** | 4 coexisting NONE rows; `SELECT count() … WHERE subject = NONE` → **4** |
| **Q3 control (fires)** | `b1 subject='x'` OK; `b2 subject='x'` | b2 **ERR** | *"Database index `probe_subject_uniq` already contains 'x', with record `probe:b1`"* — UNIQUE demonstrably enforcing |
| **Q3 control (distinct)** | `c1 subject='y'`, `c2 subject='z'` | both **OK** | distinct non-NONE both accepted |
| **Q2** | 3 spellings of `… UNIQUE WHERE subject != NONE` | all **PARSE ERROR** | *"Parse error: Unexpected token `WHERE`, expected Eof"* — confirms the grammar live |
| **Model-B UPDATE** | pre-create e1,e2 (NONE); `UPDATE e1 subject='oauth-sub-1'` OK; `UPDATE e2 subject='oauth-sub-1'` **ERR**; `UPDATE e2 subject='oauth-sub-2'` OK | as shown | filling a NONE subject works; the UNIQUE backstop **also fires on UPDATE** (two principals can't claim one OAuth identity); distinct fill succeeds |

**Provenance:** `INFO FOR TABLE probe` stored the index as `DEFINE INDEX probe_subject_uniq ON probe FIELDS subject UNIQUE` and the field (echo-normalised) as `TYPE none | string` — i.e. `option<string>`.

**Trust note (two legs).** Leg-1 scope: the probe answers exactly the packet-48 question — SCHEMAFULL table, `subject option<string>`, plain `UNIQUE` — on the same engine (3.2.4) production runs. Leg-2 forgery: every negative (multiple-NONE allowed; filtered-index rejected) is paired with a positive control that DID fire on a known-bad input (`b2`/`e2` rejections), so a "clear" is not a false clear from a mis-wired probe. Bound: measured on engine 3.2.4 via the floating `v3.2` tag — re-probe if the tag drifts (memory `surreal 3.2.4 floating tag`).

---

## 4. The instrument (verbatim — brief-base §1: an instrument is a deliverable)

```python
#!/usr/bin/env python3
"""Probe: a UNIQUE index over an ``option<string>`` field vs NONE (unset) values.

WHY (packet 48 — the schema of ``principal.subject``). The operator chose
provisioning **Model B**: an admin pre-creates a principal by email BEFORE first
login, and the OAuth ``subject`` is filled in later. So ``principal.subject`` is
``option<string>``, and MULTIPLE pre-created principals hold ``subject = NONE`` at
the same time. We want ``subject`` UNIQUE so a real OAuth identity maps to <=1
principal. Three things must be settled BY CONSTRUCTION (not opinion), because a
wrong answer is a real bug in the second ``add <email>``:

  Q1. Does a UNIQUE index over ``option<string>`` PERMIT MULTIPLE rows whose value
      is NONE (unset)?  If it REJECTS the 2nd NONE row, a plain
      ``subject option<string> UNIQUE`` breaks Model B.
  Q2. Is there a FILTERED / PARTIAL unique index spelling
      (``... UNIQUE WHERE subject != NONE``) that our engine accepts?
  Q3. Does the backstop we WANT still hold: two rows with the SAME NON-NONE
      subject ARE rejected?  And does that backstop also fire on the Model-B
      UPDATE path (fill a previously-NONE subject to a value another row holds)?

METHOD (store law, #107 pattern). The store reference + the engine's own
CI-verified SurrealQL spec were read FIRST (see the report); this CONSTRUCTS each
state on the live TEST store and byte-observes the engine's per-statement result.
Every negative result is paired with a POSITIVE CONTROL (the UNIQUE demonstrably
firing) so a "clear" is trustworthy.

SAFETY. Mints its own throwaway database ``test_<pid>_<uuid4>`` under the
``lore_test`` namespace on the spike-surreal TEST store
(``ws://127.0.0.1:18000`` — creds root/spikeroot, matching
``loremaster/tests/_surreal_harness.py``), and drops it on exit. It NEVER touches
production (lore-surreal :18500).

Store-law compliance (reference §3): reads/writes go through the SDK's
``query_raw`` — the all-statements call every SurrealQL statement passes through
and the one ``execute_transaction`` itself rides — with EVERY per-statement
``status`` inspected explicitly. It never uses the bare ``.query()`` seam, which
validates only ``statement[0]`` and would hide a later rejection.

Run: ``uv run python scripts/probe_unique_nullable_48.py``
Exit 0 iff every expectation held (self-checking); non-zero on any surprise.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from dataclasses import dataclass, field
from typing import Any

from loremaster.store._txn import bootstrap_session, signin_credentials
from pydantic import SecretStr
from surrealdb import AsyncSurreal

# TEST store topology — the spike defaults from ``_surreal_harness.py``. NEVER :18500.
URL = "ws://127.0.0.1:18000/rpc"
USER = "root"
PASSWORD = "spikeroot"
NAMESPACE = "lore_test"


def unique_database() -> str:
    """``test_<pid>_<uuid4>`` — the harness pattern, so a parallel run never collides."""
    return f"test_{os.getpid()}_{uuid.uuid4().hex}"


@dataclass
class StatementOutcome:
    """One statement's engine result, byte-observed via ``query_raw``."""

    statement: str
    #: True iff the engine returned status == "OK" for this single statement.
    ok: bool
    #: "OK", "ERR", or "RAISED" (an RPC/parse-level error the SDK surfaced as an exception).
    status: str
    #: The rows (on OK) or the engine's error string (on ERR/RAISED), stringified.
    detail: str


@dataclass
class ProbeReport:
    """Accumulates outcomes and the derived verdicts."""

    outcomes: list[StatementOutcome] = field(default_factory=list)
    surprises: list[str] = field(default_factory=list)


async def run_one(connection: Any, statement: str) -> StatementOutcome:
    """Execute ONE statement via ``query_raw`` and byte-observe its per-statement status.

    ``query_raw`` returns ``{"id": ..., "result": [{"status", "result", "time", ...}]}``
    and — unlike ``.query()`` — does NOT itself raise on a per-statement ERR, so a
    UNIQUE violation comes back as a readable ``status == "ERR"`` entry. A genuine
    PARSE error fails the whole RPC request and surfaces as a raised exception; we
    capture both shapes.
    """
    try:
        response = await connection.query_raw(statement)
    except Exception as error:  # noqa: BLE001 - a probe records every failure shape verbatim
        return StatementOutcome(statement, False, "RAISED", f"{type(error).__name__}: {error}")
    # A PARSE error fails the whole RPC request: query_raw returns an envelope with a
    # top-level "error" (no per-statement "result" list) rather than raising.
    if isinstance(response, dict) and isinstance(response.get("error"), dict):
        message = str(response["error"].get("message", response["error"]))
        return StatementOutcome(statement, False, "PARSE_ERR", message)
    entries = response.get("result") if isinstance(response, dict) else None
    if not isinstance(entries, list) or not entries:
        return StatementOutcome(statement, False, "MALFORMED", repr(response))
    entry = entries[0]
    status = str(entry.get("status"))
    detail = str(entry.get("result"))
    return StatementOutcome(statement, status == "OK", status, detail)


async def expect(
    report: ProbeReport,
    connection: Any,
    statement: str,
    *,
    want_ok: bool,
    why: str,
) -> StatementOutcome:
    """Run ``statement``, record it, and flag a surprise if reality != ``want_ok``."""
    outcome = await run_one(connection, statement)
    report.outcomes.append(outcome)
    verdict = "OK " if outcome.ok else f"{outcome.status}"
    marker = "  " if outcome.ok == want_ok else "!!"
    want = "OK" if want_ok else "REJECT"
    print(f"{marker} [{verdict:<6}] want={want:<6} | {statement}")
    if not outcome.ok:
        print(f"        -> {outcome.detail}")
    if outcome.ok != want_ok:
        wanted = "OK" if want_ok else "REJECT"
        report.surprises.append(
            f"{why}: wanted {wanted}, got {outcome.status} for `{statement}` :: {outcome.detail}"
        )
    return outcome


async def probe(connection: Any) -> ProbeReport:
    report = ProbeReport()

    print("\n=== SCHEMA (SCHEMAFULL table, subject option<string>, UNIQUE index) ===")
    # DDL applied statement-by-statement with every status checked (store law §3).
    for ddl in (
        "DEFINE TABLE probe SCHEMAFULL",
        "DEFINE FIELD name ON probe TYPE string",
        "DEFINE FIELD subject ON probe TYPE option<string>",
        "DEFINE INDEX probe_subject_uniq ON probe FIELDS subject UNIQUE",
    ):
        await expect(report, connection, ddl, want_ok=True, why="schema DDL must apply")

    print("\n=== Q1: MULTIPLE NONE (unset) rows under the UNIQUE index ===")
    # subject omitted => NONE for an option<string> field. Three of them.
    await expect(report, connection, "CREATE probe:a1 SET name = 'alpha'", want_ok=True, why="1st NONE row")
    await expect(
        report,
        connection,
        "CREATE probe:a2 SET name = 'beta'",
        want_ok=True,
        why="2nd NONE row (the core question)",
    )
    await expect(report, connection, "CREATE probe:a3 SET name = 'gamma'", want_ok=True, why="3rd NONE row")
    # Explicit NONE, to confirm it behaves like an omitted field.
    await expect(
        report,
        connection,
        "CREATE probe:a4 SET name = 'delta', subject = NONE",
        want_ok=True,
        why="explicit subject = NONE",
    )

    print("\n=== Q3 control: SAME non-NONE subject must be REJECTED (UNIQUE fires) ===")
    await expect(
        report,
        connection,
        "CREATE probe:b1 SET name = 'b1', subject = 'x'",
        want_ok=True,
        why="1st subject='x'",
    )
    await expect(
        report,
        connection,
        "CREATE probe:b2 SET name = 'b2', subject = 'x'",
        want_ok=False,
        why="POSITIVE CONTROL: duplicate subject='x' must be rejected",
    )

    print("\n=== Q3 control: DISTINCT non-NONE subjects must both succeed ===")
    await expect(
        report, connection, "CREATE probe:c1 SET name = 'c1', subject = 'y'", want_ok=True, why="subject='y'"
    )
    await expect(
        report, connection, "CREATE probe:c2 SET name = 'c2', subject = 'z'", want_ok=True, why="subject='z'"
    )

    print("\n=== Q2: FILTERED / PARTIAL unique index spellings (expect PARSE ERROR) ===")
    for spelling in (
        "DEFINE INDEX probe_filtered_ne ON probe FIELDS subject UNIQUE WHERE subject != NONE",
        "DEFINE INDEX probe_filtered_isnot ON probe FIELDS subject UNIQUE WHERE subject IS NOT NONE",
        "DEFINE INDEX probe_filtered_where ON probe FIELDS subject WHERE subject != NONE UNIQUE",
    ):
        await expect(
            report, connection, spelling, want_ok=False, why="filtered UNIQUE is not in the engine grammar"
        )

    print("\n=== Model B UPDATE path: fill a previously-NONE subject; backstop on UPDATE ===")
    await expect(
        report,
        connection,
        "CREATE probe:e1 SET name = 'e1'",
        want_ok=True,
        why="Model-B pre-create e1 (NONE)",
    )
    await expect(
        report,
        connection,
        "CREATE probe:e2 SET name = 'e2'",
        want_ok=True,
        why="Model-B pre-create e2 (NONE), coexisting NONE",
    )
    await expect(
        report,
        connection,
        "UPDATE probe:e1 SET subject = 'oauth-sub-1'",
        want_ok=True,
        why="fill e1's NONE subject (first login)",
    )
    await expect(
        report,
        connection,
        "UPDATE probe:e2 SET subject = 'oauth-sub-1'",
        want_ok=False,
        why="POSITIVE CONTROL: UPDATE to a duplicate non-NONE subject must be rejected",
    )
    await expect(
        report,
        connection,
        "UPDATE probe:e2 SET subject = 'oauth-sub-2'",
        want_ok=True,
        why="fill e2 with a distinct subject",
    )

    print("\n=== Provenance: stored index definition (INFO FOR TABLE probe) ===")
    info = await run_one(connection, "INFO FOR TABLE probe")
    report.outcomes.append(info)
    print(f"   INFO -> {info.detail}")

    print("\n=== Provenance: NONE rows readable + count (fail-open coexistence) ===")
    count = await run_one(connection, "SELECT count() FROM probe WHERE subject = NONE GROUP ALL")
    report.outcomes.append(count)
    print(f"   NONE-count -> {count.detail}")

    return report


async def main() -> int:
    database = unique_database()
    connection = AsyncSurreal(URL)
    await connection.signin(signin_credentials(user=USER, password=SecretStr(PASSWORD)))
    await bootstrap_session(connection, NAMESPACE, database, url=URL)
    print(f"probe database: {NAMESPACE}:{database}  (TEST store {URL})")
    try:
        report = await probe(connection)
    finally:
        try:
            await connection.query(f"REMOVE DATABASE IF EXISTS {database}")
        except Exception as error:  # noqa: BLE001
            print(f"[cleanup warning] {type(error).__name__}: {error}")
        await connection.close()

    print("\n=== VERDICT ===")
    if report.surprises:
        print(f"SURPRISES ({len(report.surprises)}) — a claimed clear is NOT trustworthy:")
        for surprise in report.surprises:
            print(f"  - {surprise}")
        return 1
    print("All expectations held:")
    print("  Q1 multiple-NONE under UNIQUE : ALLOWED (2nd & 3rd NONE + explicit NONE all created)")
    print("  Q2 filtered/partial UNIQUE     : NOT SUPPORTED (every spelling rejected)")
    print("  Q3 same non-NONE rejected      : YES, on CREATE and on the Model-B UPDATE fill path")
    print("  => Model B schema is sound with a plain `subject option<string>` + UNIQUE index.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
```

DRY LEDGER (§6):

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `unique_database()` | read `loremaster/tests/_surreal_harness.py` (`unique_database`) | the harness already defines the identical `test_<pid>_<uuid4>` minter | **HAND-ROLLED** — importing `_surreal_harness` drags `conftest`/`_sdk_guard`/`pytest_asyncio` into a standalone probe script; a 3-line self-contained copy of a trivial id format (not policy) is the right call for a probe. Connection bootstrap, by contrast, **REUSES** `bootstrap_session`/`signin_credentials` (the store's real session seam) — the part that IS policy. |
| `run_one` / `expect` / `StatementOutcome` / `ProbeReport` | n/a | — | probe-local test scaffolding, not reusable production symbols; no shared home warranted. |

## 5. Raw probe output (exit 0)

```
probe database: lore_test:test_2538672_8f251396ca9e487fa67b74e353105210  (TEST store ws://127.0.0.1:18000/rpc)

=== SCHEMA (SCHEMAFULL table, subject option<string>, UNIQUE index) ===
   [OK    ] want=OK     | DEFINE TABLE probe SCHEMAFULL
   [OK    ] want=OK     | DEFINE FIELD name ON probe TYPE string
   [OK    ] want=OK     | DEFINE FIELD subject ON probe TYPE option<string>
   [OK    ] want=OK     | DEFINE INDEX probe_subject_uniq ON probe FIELDS subject UNIQUE

=== Q1: MULTIPLE NONE (unset) rows under the UNIQUE index ===
   [OK    ] want=OK     | CREATE probe:a1 SET name = 'alpha'
   [OK    ] want=OK     | CREATE probe:a2 SET name = 'beta'
   [OK    ] want=OK     | CREATE probe:a3 SET name = 'gamma'
   [OK    ] want=OK     | CREATE probe:a4 SET name = 'delta', subject = NONE

=== Q3 control: SAME non-NONE subject must be REJECTED (UNIQUE fires) ===
   [OK    ] want=OK     | CREATE probe:b1 SET name = 'b1', subject = 'x'
   [ERR   ] want=REJECT | CREATE probe:b2 SET name = 'b2', subject = 'x'
        -> Database index `probe_subject_uniq` already contains 'x', with record `probe:b1`

=== Q3 control: DISTINCT non-NONE subjects must both succeed ===
   [OK    ] want=OK     | CREATE probe:c1 SET name = 'c1', subject = 'y'
   [OK    ] want=OK     | CREATE probe:c2 SET name = 'c2', subject = 'z'

=== Q2: FILTERED / PARTIAL unique index spellings (expect PARSE ERROR) ===
   [PARSE_ERR] want=REJECT | DEFINE INDEX probe_filtered_ne ON probe FIELDS subject UNIQUE WHERE subject != NONE
        -> Parse error: Unexpected token `WHERE`, expected Eof
 --> [1:63]
  |
1 | ...ct UNIQUE WHERE subject != NONE
  |              ^^^^^

   [PARSE_ERR] want=REJECT | DEFINE INDEX probe_filtered_isnot ON probe FIELDS subject UNIQUE WHERE subject IS NOT NONE
        -> Parse error: Unexpected token `WHERE`, expected Eof
 --> [1:66]
  |
1 | ...ct UNIQUE WHERE subject IS NOT NONE
  |              ^^^^^

   [PARSE_ERR] want=REJECT | DEFINE INDEX probe_filtered_where ON probe FIELDS subject WHERE subject != NONE UNIQUE
        -> Parse error: Unexpected token `WHERE`, expected Eof
 --> [1:59]
  |
1 | ...S subject WHERE subject != NONE UNIQUE
  |              ^^^^^


=== Model B UPDATE path: fill a previously-NONE subject; backstop on UPDATE ===
   [OK    ] want=OK     | CREATE probe:e1 SET name = 'e1'
   [OK    ] want=OK     | CREATE probe:e2 SET name = 'e2'
   [OK    ] want=OK     | UPDATE probe:e1 SET subject = 'oauth-sub-1'
   [ERR   ] want=REJECT | UPDATE probe:e2 SET subject = 'oauth-sub-1'
        -> Database index `probe_subject_uniq` already contains 'oauth-sub-1', with record `probe:e1`
   [OK    ] want=OK     | UPDATE probe:e2 SET subject = 'oauth-sub-2'

=== Provenance: stored index definition (INFO FOR TABLE probe) ===
   INFO -> {'events': {}, 'fields': {'name': 'DEFINE FIELD name ON probe TYPE string PERMISSIONS FULL', 'subject': 'DEFINE FIELD subject ON probe TYPE none | string PERMISSIONS FULL'}, 'indexes': {'probe_subject_uniq': 'DEFINE INDEX probe_subject_uniq ON probe FIELDS subject UNIQUE'}, 'lives': {}, 'tables': {}}

=== Provenance: NONE rows readable + count (fail-open coexistence) ===
   NONE-count -> [{'count': 4}]

=== VERDICT ===
All expectations held:
  Q1 multiple-NONE under UNIQUE : ALLOWED (2nd & 3rd NONE + explicit NONE all created)
  Q2 filtered/partial UNIQUE     : NOT SUPPORTED (every spelling rejected)
  Q3 same non-NONE rejected      : YES, on CREATE and on the Model-B UPDATE fill path
  => Model B schema is sound with a plain `subject option<string>` + UNIQUE index.
```

Gate: `uv run ruff check scripts/probe_unique_nullable_48.py` → **All checks passed!**

---

## 6. Recommendation for packet-48 `subject` schema + a store-reference flag

**Ship the plain shape** (no filtered index — the engine has none, and none is needed):
```surql
DEFINE FIELD subject ON principal TYPE option<string>;                 -- OVERWRITE per store §1.1 in ensure_ready
DEFINE INDEX principal_subject_uniq ON principal FIELDS subject UNIQUE; -- IF NOT EXISTS per store §1.1
```
Rationale, all measured: NONE is exempt from uniqueness (Q1), so any number of pre-created principals coexist with `subject = NONE`; a real OAuth `subject` maps to ≤1 principal because duplicates are rejected on CREATE **and** UPDATE (Q3); the Model-B "fill on first login" `UPDATE subject = <sub>` works and cannot collide two principals onto one identity.

Two consequences the schema/contract author should carry forward (not blockers, flagged per scope law):
- **Field clause = `OVERWRITE`, index clause = `IF NOT EXISTS`** (store ref §1.1) — the usual split; the probe's clause choice was `IF NOT EXISTS`-implicit-fresh, which does not exercise the migration path.
- **`option<string>` read hazards apply to `subject`** (store ref §2): under `SELECT *` a NONE `subject` key is OMITTED (use `row.get("subject")`); an ASSERT on the field is not evaluated when NONE. Any `subject` reader must not assume presence.

**FLAG — store-reference gap (outside my writable set; not edited).** `docs/reference/surrealdb-31-capabilities.md` is silent on UNIQUE-over-`option<>`-NONE and on the absence of a partial unique index. Recommend a short addition (a §1.1/§6-adjacent note) stating: *"[PROBED 2026-08-20, 3.2.4 — `scripts/probe_unique_nullable_48.py`] a plain `UNIQUE` index over `option<string>` PERMITS unlimited NONE rows (NONE is exempt) while rejecting duplicate non-NONE on CREATE and UPDATE; SurrealDB has NO filtered/partial UNIQUE index — `WHERE` attaches to `COUNT` indexes only, `UNIQUE … WHERE` is a parse error. Corroborated by the engine's own spec `create_on_none_values_with_unique_index.surql`."* I did not edit the file (writable set = probe script + this report); the lead/schema author can adopt the note. Recorded the same fact in lore memory for retrieval.

---

## 7. Follow-up — finding #389 (S6 SecretStr allowlist)

The committed probe's `SecretStr(PASSWORD)` (line 260, `PASSWORD = "spikeroot"`) tripped the S6 invariant in `test_secret_typing.py::…test_secretstr_is_minted_only_where_a_credential_ORIGINATES` (re-wrap-a-bare-str-at-a-call-site). **Confirmed the mechanism is the allowlist, not a probe change:** the probe is identical in kind to the already-allowlisted spike-store probes `probe_query_complexity_07.py` / `probe_store_error_classes_07.py` / `probe_store_recovery_07a.py` — a TEST-store probe minting the fixed `"spikeroot"` dev literal (no real secret) for `signin_credentials`/`bootstrap_session`, which genuinely require `SecretStr` (#211). Routing through `config.resolve_secret` would be wrong (that seam is for config-resolved secrets, not a fixed test literal — the sibling probes don't). RED→GREEN receipt: offender `scripts/probe_unique_nullable_48.py:260` → added `"scripts/probe_unique_nullable_48.py"` to the S6 `allowed` tuple with an ADJUDICATED evidence comment → `test_secret_typing.py` **69 passed, 0 failed** (ruff clean). #389 resolved. Writable set honored: only `loremaster/tests/test_secret_typing.py` touched (allowlist entry + comment); probe behavior unchanged.
