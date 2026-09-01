#!/usr/bin/env python3
"""Probe: are ``array<object>`` "value + optional qualifier" fields VIABLE and
INDEX-SERVED for the D&D creature-defense columns on ``stat_block`` (the monster
table) — damage_resistances / immunities / vulnerabilities, condition_immunities?

THE DESIGN QUESTION. A defense entry is usually a bare vocab token (Fire, Cold,
Bludgeoning), but real values carry a CAVEAT that MUST travel with the type so a
downstream LLM can never read "immune to Bludgeoning" while missing "…only
nonmagical":

    damage_immunities: [
        { type: "Bludgeoning", condition: "from nonmagical attacks not made with silvered weapons" },
        { type: "Fire" }        # no condition = unconditional
    ]

KNOWN-GOOD BASELINE (already settled on this store; store-ref §"Indexing an ARRAY
column"): for ``array<string>`` multi-tag fields, ``DEFINE INDEX … FIELDS <f>.*``
(element path) serves membership (``'x' INSIDE <f>`` / ``<f> CONTAINS 'x'``) as an
IndexScan, while a BARE ``FIELDS <f>`` (no ``.*``) silently mis-serves ``<f> = 'x'``
as a fast, empty IndexScan — the documented silent-``[]`` trap. This probe holds the
OBJECT analogue to that same bar (correct rows AND an index proven used by EXPLAIN),
and reproduces the string baseline + its trap as positive controls so the delta is
measured on ONE engine in ONE run.

METHOD (store-law discipline — §2 IndexScan-vs-TableScan-via-EXPLAIN + the C1 rule "a
probe NEEDS a positive control"). Every scan claim is a live EXPLAIN plan on the REAL
3.2.4 spike engine, classified by the SAME plan-walker the shipped packet-60 pin and
``probe_read_filter_63.py`` use (``operator == 'IndexScan'`` / ``'TableScan'`` with
``attributes.table``) — MIRRORED and CITED, not forked (instrument parsing, not
production policy). Latency (Q6) is wall-clock over ~700 rows, warmup-dropped, median
of repeats — measured, never guessed.

WHAT IT COVERS (the operator's 7 questions):
  Q1 store+full-return : typed ``array<object>`` schema accepted; SELECT * returns the
                          whole object array, conditions included (+ FLEXIBLE / plain
                          non-FLEXIBLE variants advised).
  Q2 type membership   : the winning spelling for "immune to Fire (any form)" over the
                          object array + whether ``FIELDS <f>.*.type`` is USED (EXPLAIN)
                          + the bare-index silent-trap analogue.
  Q3 unconditional     : "unconditionally immune to Bludgeoning" (type present, condition
                          absent) — is condition-absence filterable / index-served?
  Q4 conditional flag  : "any conditional immunity" (any element with a condition).
  Q5 baseline delta    : the same membership over an ``array<string>`` copy, plans side
                          by side.
  Q6 scale             : ~700 rows — which queries TableScan, and is that latency OK?
  Q7 idiom             : array<object> vs a related edge table (a confirming edge probe).

SAFETY. Mints its own throwaway database ``test_<pid>_<uuid4>`` under the ``lore_test``
namespace on the spike-surreal TEST store (``ws://127.0.0.1:18000`` — creds
root/spikeroot, matching ``loremaster/tests/_surreal_harness.py`` and the packet-63
probe), and drops it on exit. It NEVER touches production (lore-surreal :18500).

Run: ``uv run python scripts/probe_dnd_defense_objects.py``
Exit 0 iff every control held, every load-bearing membership query returned the
DISCRIMINATING correct rows, and every REQUIRED plan classified as expected; non-zero
on any surprise (a claimed clear is then NOT trustworthy).
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from loremaster.store._txn import bootstrap_session, signin_credentials
from pydantic import SecretStr
from surrealdb import AsyncSurreal, RecordID

# TEST store topology — the spike defaults from ``_surreal_harness.py``. NEVER :18500.
URL = "ws://127.0.0.1:18000/rpc"
USER = "root"
PASSWORD = "spikeroot"
NAMESPACE = "lore_test"
TABLE = "stat_block"

TOTAL_ROWS = 700  # ~660 real + headroom; the operator's stated scale


def unique_database() -> str:
    """``test_<pid>_<uuid4>`` — the harness pattern, so a parallel run never collides."""
    return f"test_{os.getpid()}_{uuid.uuid4().hex}"


# --------------------------------------------------------------------------- #
# EXPLAIN plan classification — MIRRORED from ``probe_read_filter_63.py`` (itself
# re-expressing ``test_keeps_schema.py``), CITED not forked.
# --------------------------------------------------------------------------- #


def _operators(plan: Any) -> list[str]:
    """Every ``operator``/``operation`` string anywhere in the EXPLAIN plan tree."""
    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key in ("operator", "operation"):
                op = node.get(key)
                if isinstance(op, str):
                    found.append(op)
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(plan)
    return found


def _scans_table(plan: Any, table: str) -> bool:
    """True iff the plan carries a ``TableScan`` node targeting ``table``."""
    found = False

    def walk(node: Any) -> None:
        nonlocal found
        if isinstance(node, dict):
            attributes = node.get("attributes")
            if (
                node.get("operator") == "TableScan"
                and isinstance(attributes, dict)
                and attributes.get("table") == table
            ):
                found = True
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(plan)
    return found


def _index_names(plan: Any) -> list[str]:
    """Every index name referenced anywhere in the plan (best-effort, for the report)."""
    names: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key in ("index", "index_name"):
                value = node.get(key)
                if isinstance(value, str):
                    names.append(value)
            attributes = node.get("attributes")
            if isinstance(attributes, dict):
                for key in ("index", "index_name"):
                    value = attributes.get(key)
                    if isinstance(value, str):
                        names.append(value)
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(plan)
    return names


def _classify(plan: Any, table: str) -> tuple[list[str], bool, bool, str]:
    operators = _operators(plan)
    has_index_scan = "IndexScan" in operators
    scans_target = _scans_table(plan, table)
    if scans_target and not has_index_scan:
        classification = "TableScan"
    elif scans_target and has_index_scan:
        classification = "MIXED(index+table)"
    elif has_index_scan:
        classification = "IndexScan"
    elif "EmptyScan" in operators:
        classification = "EmptyScan"
    else:
        classification = "UNCLASSIFIED"
    return operators, has_index_scan, scans_target, classification


@dataclass
class ScanObservation:
    label: str
    statement: str
    operators: list[str]
    classification: str
    index_names: list[str]
    raw_plan: Any


@dataclass
class ProbeReport:
    observations: list[ScanObservation] = field(default_factory=list)
    surprises: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def get(self, label: str) -> ScanObservation:
        for obs in self.observations:
            if obs.label == label:
                return obs
        raise KeyError(label)


async def explain(
    report: ProbeReport,
    connection: Any,
    *,
    label: str,
    where: str,
    select: str = "id",
    params: dict[str, Any] | None = None,
    table: str = TABLE,
    dump: bool = False,
    report_only: bool = False,
) -> ScanObservation:
    statement = f"SELECT {select} FROM {table} WHERE {where} EXPLAIN"
    plan = await connection.query(statement, params or {})
    operators, _has_index, _scans, classification = _classify(plan, table)
    observation = ScanObservation(
        label=label,
        statement=statement,
        operators=operators,
        classification=classification,
        index_names=_index_names(plan),
        raw_plan=plan,
    )
    report.observations.append(observation)
    idx = f"  index={observation.index_names}" if observation.index_names else ""
    print(f"  [{classification:<18}] {label}{idx}")
    print(f"      {statement}")
    print(f"      operators={operators}")
    if dump:
        print("      plan=" + json.dumps(plan, default=str, indent=2).replace("\n", "\n      "))
    if classification == "UNCLASSIFIED" and not report_only:
        report.surprises.append(
            f"{label}: plan UNCLASSIFIED — no honest verdict possible. "
            f"operators={operators} :: {statement}"
        )
    return observation


def _require(report: ProbeReport, obs: ScanObservation, want: str, why: str) -> None:
    if obs.classification != want:
        report.surprises.append(
            f"{obs.label}: EXPECTED {want}, got {obs.classification}. {why} "
            f"operators={obs.operators} :: {obs.statement}"
        )


def _rows(result: Any) -> set[str]:
    if not isinstance(result, list):
        return set()
    return {str(row["id"]) for row in result if isinstance(row, dict) and "id" in row}


def _expect_rows(
    report: ProbeReport, label: str, got: set[str], *, must_include: set[str], must_exclude: set[str]
) -> None:
    def q(ids: set[str]) -> set[str]:
        # KNOWN rows are stored as ``<TABLE>:sb_<key>`` — callers pass the bare key.
        return {f"{TABLE}:sb_{i}" for i in ids}

    inc, exc = q(must_include), q(must_exclude)
    missing = inc - got
    leaked = exc & got
    print(f"  {label}: returned {sorted(got)}")
    if missing:
        report.surprises.append(f"{label}: MISSING required rows {sorted(missing)} (got {sorted(got)}).")
    if leaked:
        report.surprises.append(f"{label}: LEAKED forbidden rows {sorted(leaked)} (got {sorted(got)}).")


async def _q(connection: Any, statement: str, params: dict[str, Any] | None = None) -> Any:
    return await connection.query(statement, params or {})


async def _try_ddl(connection: Any, label: str, ddl: str, report: ProbeReport) -> bool:
    """Apply ONE DDL statement, reporting acceptance/rejection (single-statement so
    ``.query()``'s statement[0]-only validation actually validates it)."""
    try:
        await connection.query(ddl)
        print(f"  [ACCEPTED] {label}: {ddl}")
        return True
    except Exception as error:  # noqa: BLE001 — we are probing what the engine rejects
        print(f"  [REJECTED] {label}: {ddl}\n             -> {type(error).__name__}: {error}")
        report.notes.append(f"{label} REJECTED: {error}")
        return False


# --------------------------------------------------------------------------- #
# SCHEMA — the typed ``array<object>`` shape (primary), plus the trap/baseline columns.
# --------------------------------------------------------------------------- #

# Semantic damage vocab used by the KNOWN rows (kept disjoint from filler tokens so the
# discriminating assertions are exact).
# filler rows carry ONLY this + optionally Fire — never Bludgeoning/Cold/Acid/Necrotic/Poison
FILLER_TOKEN = "Radiant"


async def setup_schema(connection: Any, report: ProbeReport) -> None:
    print("\n=== SCHEMA — typed array<object> (primary), bare-index trap col, string baseline ===")
    # Q1: the idiomatic SCHEMAFULL shape — declare the element keys so the store enforces
    # the object's shape AND the element-path index can build. OVERWRITE for fields
    # (store-ref §1.1); IF NOT EXISTS for indexes/tables (§1.1/§1.5).
    stmts = [
        f"DEFINE TABLE IF NOT EXISTS {TABLE} SCHEMAFULL",
        f"DEFINE FIELD OVERWRITE name ON {TABLE} TYPE string",
        f"DEFINE FIELD OVERWRITE cr ON {TABLE} TYPE float",
        # --- primary: typed array<object>, element index on .*.type ---
        f"DEFINE FIELD OVERWRITE damage_immunities ON {TABLE} TYPE option<array<object>>",
        f"DEFINE FIELD OVERWRITE damage_immunities[*].type ON {TABLE} TYPE string",
        f"DEFINE FIELD OVERWRITE damage_immunities[*].condition ON {TABLE} TYPE option<string>",
        # --- trap column: same typed shape, but a BARE index (no .*.type) ---
        f"DEFINE FIELD OVERWRITE di_bare ON {TABLE} TYPE option<array<object>>",
        f"DEFINE FIELD OVERWRITE di_bare[*].type ON {TABLE} TYPE string",
        f"DEFINE FIELD OVERWRITE di_bare[*].condition ON {TABLE} TYPE option<string>",
        # --- string baseline (known-good) + its documented bare-index trap column ---
        f"DEFINE FIELD OVERWRITE di_flat ON {TABLE} TYPE option<array<string>>",
        f"DEFINE FIELD OVERWRITE flat_bare ON {TABLE} TYPE option<array<string>>",
    ]
    for i, ddl in enumerate(stmts):
        ok = await _try_ddl(connection, f"field[{i}]", ddl, report)
        if not ok and "[*]" not in ddl:
            report.surprises.append(f"Base schema DDL rejected: {ddl}")

    print("\n=== INDEXES ===")
    indexes = [
        ("sb_name (control, scalar UNIQUE)",
         f"DEFINE INDEX IF NOT EXISTS sb_name ON {TABLE} FIELDS name UNIQUE"),
        ("di_type ELEMENT PATH (the object candidate)",
         f"DEFINE INDEX IF NOT EXISTS di_type ON {TABLE} FIELDS damage_immunities[*].type"),
        ("di_bare_idx BARE object array (the trap)",
         f"DEFINE INDEX IF NOT EXISTS di_bare_idx ON {TABLE} FIELDS di_bare"),
        ("di_flat_idx ELEMENT PATH string (known-good baseline)",
         f"DEFINE INDEX IF NOT EXISTS di_flat_idx ON {TABLE} FIELDS di_flat[*]"),
        ("flat_bare_idx BARE string array (documented string trap)",
         f"DEFINE INDEX IF NOT EXISTS flat_bare_idx ON {TABLE} FIELDS flat_bare"),
    ]
    for label, ddl in indexes:
        await _try_ddl(connection, label, ddl, report)


# --------------------------------------------------------------------------- #
# SEEDING
# --------------------------------------------------------------------------- #

# KNOWN rows — chosen to DISCRIMINATE (C1 "what wrong build would still pass this?"):
#   rakshasa: cond Bludgeoning + UNCOND Fire   -> in B(Fire), out C1(uncond Bludg), in C2(any cond)
#   golem   : uncond Fire + uncond Poison      -> in B(Fire), out C1, out C2
#   demon   : UNCOND Bludgeoning + uncond Cold -> out B(Fire), IN C1, out C2
#   wraith  : cond Bludgeoning + uncond Necrotic-> out B(Fire), out C1, in C2
#   nofire  : uncond Acid                      -> out of all three
KNOWN = {
    "rakshasa": [
        {"type": "Bludgeoning", "condition": "from nonmagical attacks not made with silvered weapons"},
        {"type": "Fire"},
    ],
    "golem": [{"type": "Fire"}, {"type": "Poison"}],
    "demon": [{"type": "Bludgeoning"}, {"type": "Cold"}],
    "wraith": [{"type": "Bludgeoning", "condition": "from nonmagical attacks"}, {"type": "Necrotic"}],
    "nofire": [{"type": "Acid"}],
}


def _flat(objs: list[dict[str, str]]) -> list[str]:
    return [o["type"] for o in objs]


async def _create_row(
    connection: Any, row_id: str, name: str, cr: float, immunities: list[dict[str, str]]
) -> None:
    await connection.query(
        f"CREATE type::record('{TABLE}', $id) CONTENT {{ "
        f"name: $name, cr: $cr, "
        f"damage_immunities: $imm, di_bare: $imm, "
        f"di_flat: $flat, flat_bare: $flat }}",
        {"id": row_id, "name": name, "cr": cr, "imm": immunities, "flat": _flat(immunities)},
    )


async def seed(connection: Any) -> None:
    print(f"\n=== SEEDING {TOTAL_ROWS} rows ({len(KNOWN)} known + filler) ===")
    for i, (key, imm) in enumerate(KNOWN.items()):
        await _create_row(connection, f"sb_{key}", f"Known {key.title()}", float(i + 1), imm)
    # Filler: unconditional, never Bludgeoning/Cold/Acid/Necrotic/Poison; ~12% carry Fire
    # so the Fire index has realistic (non-degenerate) cardinality, the rest carry only
    # a filler token. All filler is UNCONDITIONAL (keeps C2 exact) and never Bludgeoning
    # (keeps C1 exact).
    n_filler = TOTAL_ROWS - len(KNOWN)
    for i in range(n_filler):
        has_fire = (i % 8 == 0)
        imm = [{"type": "Fire"}, {"type": FILLER_TOKEN}] if has_fire else [{"type": FILLER_TOKEN}]
        await _create_row(connection, f"f_{i}", f"Filler {i}", 1.0, imm)
    count = await _q(connection, f"SELECT count() AS n FROM {TABLE} GROUP ALL")
    print(f"  total rows: {count}")


# --------------------------------------------------------------------------- #
# LATENCY
# --------------------------------------------------------------------------- #


async def _time_query(connection: Any, statement: str, params: dict[str, Any], repeats: int = 7) -> float:
    """Median wall-clock ms over ``repeats`` runs, dropping the first (warmup)."""
    samples: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter()
        await connection.query(statement, params)
        samples.append((time.perf_counter() - start) * 1000.0)
    body = sorted(samples[1:])
    return body[len(body) // 2]


# --------------------------------------------------------------------------- #
# PROBES
# --------------------------------------------------------------------------- #


async def _probe_q1(connection: Any, report: ProbeReport) -> None:
    """Q1 — store + full return, and how an absent condition is represented."""
    print("\n=== Q1 — STORE + FULL RETURN (the canonical Rakshasa row) ===")
    raw = await _q(connection, f"SELECT * FROM type::record('{TABLE}', 'sb_rakshasa')")
    row = raw[0] if isinstance(raw, list) and raw else raw
    di = row.get("damage_immunities") if isinstance(row, dict) else None
    print(f"  stored damage_immunities = {json.dumps(di, default=str)}")
    if not (isinstance(di, list) and len(di) == 2):
        report.surprises.append(f"Q1: SELECT * did not return a 2-element object array (got {di!r}).")
        return
    blud = next((o for o in di if o.get("type") == "Bludgeoning"), None)
    fire = next((o for o in di if o.get("type") == "Fire"), None)
    if not blud or "silvered" not in str(blud.get("condition", "")):
        report.surprises.append(f"Q1: Bludgeoning condition did not survive the round trip: {blud!r}")
    # How is the missing condition represented on the Fire element? (drives Q3 spelling)
    present = "PRESENT" if fire and "condition" in fire else "ABSENT"
    report.notes.append(
        f"Q1 Fire element under SELECT *: {json.dumps(fire, default=str)} (condition key {present})")
    print(f"  -> Fire element: {json.dumps(fire, default=str)} (condition key {present})")


async def _probe_controls(connection: Any, report: ProbeReport) -> None:
    """Instrument-integrity: the walker must classify a known index and table scan."""
    print("\n=== CONTROLS (walker must classify these as stated) ===")
    c_idx = await explain(report, connection, label="CTRL name= (scalar index → IndexScan)",
                          where="name = $n", params={"n": "Known Rakshasa"})
    _require(report, c_idx, "IndexScan", "sb_name UNIQUE must IndexScan or the walker is blind.")
    c_tab = await explain(report, connection, label="CTRL cr= (unindexed → TableScan)",
                          where="cr = $c", params={"c": 1.0})
    _require(report, c_tab, "TableScan", "walker cannot see a TableScan on unindexed cr — blind.")


async def _probe_q5_baseline(connection: Any, report: ProbeReport) -> None:
    """Q5 — the known-good array<string> bar + the documented bare-index silent-[] trap."""
    print("\n=== Q5 — array<string> BASELINE (known-good) + the documented bare-index string trap ===")
    b_inside = await explain(report, connection, label="BASE di_flat: 'Fire' INSIDE di_flat (element idx)",
                             where="'Fire' INSIDE di_flat", dump=True)
    _require(report, b_inside, "IndexScan", "string element-path index must serve INSIDE (baseline).")
    b_contains = await explain(report, connection,
                               label="BASE di_flat: di_flat CONTAINS 'Fire' (element idx)",
                               where="di_flat CONTAINS 'Fire'")
    _require(report, b_contains, "IndexScan", "string element-path index must serve CONTAINS (baseline).")
    # The documented silent trap: BARE index + equality → IndexScan returning [].
    trap_eq = await explain(report, connection, label="TRAP flat_bare = 'Fire' (bare idx → fast + WRONG)",
                            where="flat_bare = 'Fire'", dump=True)
    trap_eq_rows = _rows(await _q(connection, f"SELECT id FROM {TABLE} WHERE flat_bare = 'Fire'"))
    print(f"  TRAP flat_bare = 'Fire' returned {len(trap_eq_rows)} rows "
          "(documented silent-[] if 0 + IndexScan)")
    if trap_eq.classification == "IndexScan" and not trap_eq_rows:
        report.notes.append("Q5 TRAP REPRODUCED: bare string index + `= 'Fire'` IndexScans and returns "
                            "[] (fast, silent, wrong) — the baseline trap the object shape must avoid.")
    await explain(report, connection, label="TRAP 'Fire' INSIDE flat_bare (bare idx → TableScan)",
                  where="'Fire' INSIDE flat_bare")


async def _probe_q2(connection: Any, report: ProbeReport) -> None:
    """Q2 — type membership over the object array + whether di_type is used + the object trap."""
    print("\n=== Q2 — TYPE MEMBERSHIP over array<object> (immune to Fire, any form) ===")
    fire_expect = {"rakshasa", "golem"}  # KNOWN rows with Fire; filler-Fire also legitimately matches
    fire_forbid = {"demon", "wraith", "nofire"}
    candidates = [
        ("Q2a di_type: 'Fire' INSIDE damage_immunities[*].type",
         "'Fire' INSIDE damage_immunities[*].type"),
        ("Q2b di_type: damage_immunities[*].type CONTAINS 'Fire'",
         "damage_immunities[*].type CONTAINS 'Fire'"),
        ("Q2c di_type: 'Fire' IN damage_immunities[*].type",
         "'Fire' IN damage_immunities[*].type"),
        ("Q2d di_type: ...[*].type CONTAINSANY ['Fire','Cold']",
         "damage_immunities[*].type CONTAINSANY ['Fire','Cold']"),
    ]
    q2_index_served = []
    for label, where in candidates:
        obs = await explain(report, connection, label=label, where=where, dump=True)
        try:
            got = _rows(await _q(connection, f"SELECT id FROM {TABLE} WHERE {where}"))
        except Exception as error:  # noqa: BLE001
            print(f"  [QUERY ERROR] {label}: {type(error).__name__}: {error}")
            report.notes.append(f"{label} QUERY ERROR: {error}")
            continue
        # CONTAINSANY includes Cold (demon) — assert per-spelling.
        if "CONTAINSANY" in where:
            _expect_rows(report, label, got, must_include={"rakshasa", "golem", "demon"},
                         must_exclude={"nofire"})
        else:
            _expect_rows(report, label, got, must_include=fire_expect, must_exclude=fire_forbid)
        if obs.classification == "IndexScan":
            q2_index_served.append(label)
    if not q2_index_served:
        report.surprises.append(
            "Q2: NO type-membership spelling over damage_immunities[*].type was IndexScan-served by "
            "the di_type element-path index — the object shape would TableScan the primary filter."
        )
    else:
        report.notes.append(f"Q2 index-served spellings: {q2_index_served}")

    # The object bare-index trap analogue: bare index on di_bare + membership.
    print("\n=== Q2 (trap) — BARE index on the object array (di_bare) ===")
    await explain(report, connection, label="TRAP di_bare: di_bare[*].type CONTAINS 'Fire' (bare idx)",
                  where="di_bare[*].type CONTAINS 'Fire'", dump=True)
    # Does a bare object-array index serve any silent-wrong equality? Probe the closest analogue.
    for where in ("di_bare[*].type = 'Fire'", "di_bare = 'Fire'"):
        try:
            obs = await explain(report, connection, label=f"TRAP di_bare probe: {where}", where=where,
                                report_only=True)
            got = _rows(await _q(connection, f"SELECT id FROM {TABLE} WHERE {where}"))
            print(f"      -> {len(got)} rows")
            if obs.classification == "IndexScan" and not got:
                report.notes.append(
                    f"Q2 OBJECT TRAP: `{where}` IndexScans and returns [] (silent-wrong analogue).")
        except Exception as error:  # noqa: BLE001
            print(f"      [QUERY ERROR] {where}: {type(error).__name__}: {error}")


async def _probe_condition_filter(
    connection: Any,
    report: ProbeReport,
    *,
    title: str,
    forms: list[tuple[str, str]],
    must_include: set[str],
    must_exclude: set[str],
    fail_message: str,
    note_prefix: str,
) -> None:
    """Shared Q3/Q4 driver: try each array-filter spelling, pick the first that
    DISCRIMINATES (includes every must_include id, excludes every must_exclude id)."""
    print(f"\n=== {title} ===")
    winner = None
    for label, where in forms:
        try:
            obs = await explain(report, connection, label=label, where=where, report_only=True)
            got = _rows(await _q(connection, f"SELECT id FROM {TABLE} WHERE {where}"))
            print(f"      -> rows {sorted(got)}")
            ids = {g.split(":")[1].removeprefix("sb_") for g in got}
            if must_include <= ids and not (must_exclude & ids) and winner is None:
                winner = (label, where, obs.classification, got)
        except Exception as error:  # noqa: BLE001
            print(f"      [QUERY ERROR] {label}: {type(error).__name__}: {error}")
            report.notes.append(f"{label} QUERY ERROR: {error}")
    if winner is None:
        report.surprises.append(fail_message)
        return
    label, where, cls, got = winner
    _expect_rows(report, f"{label} (winner)", got, must_include=must_include, must_exclude=must_exclude)
    report.notes.append(f"{note_prefix} winning form: `{where}` [{cls}] -> {sorted(got)}")


async def _probe_q3(connection: Any, report: ProbeReport) -> None:
    """Q3 — unconditional immunity (type present, condition absent)."""
    forms = [
        ("Q3a array-filter condition IS NONE",
         "count(damage_immunities[WHERE type = 'Bludgeoning' AND condition IS NONE]) > 0"),
        ("Q3b array-filter condition = NONE",
         "count(damage_immunities[WHERE type = 'Bludgeoning' AND condition = NONE]) > 0"),
        ("Q3c array-filter !condition",
         "count(damage_immunities[WHERE type = 'Bludgeoning' AND !condition]) > 0"),
    ]
    await _probe_condition_filter(
        connection, report,
        title="Q3 — UNCONDITIONAL immunity (type='Bludgeoning' AND no condition)",
        forms=forms, must_include={"demon"},
        must_exclude={"rakshasa", "wraith", "golem", "nofire"},
        fail_message=("Q3: no array-filter spelling correctly isolated UNCONDITIONAL Bludgeoning "
                     "(demon in, rakshasa/wraith out). Condition-absence may not be filterable."),
        note_prefix="Q3")


async def _probe_q4(connection: Any, report: ProbeReport) -> None:
    """Q4 — any conditional immunity (any element with a condition present)."""
    forms = [
        ("Q4a condition IS NOT NONE", "count(damage_immunities[WHERE condition IS NOT NONE]) > 0"),
        ("Q4b condition != NONE", "count(damage_immunities[WHERE condition != NONE]) > 0"),
    ]
    await _probe_condition_filter(
        connection, report,
        title="Q4 — ANY CONDITIONAL immunity (element with a condition present)",
        forms=forms, must_include={"rakshasa", "wraith"},
        must_exclude={"demon", "golem", "nofire"},
        fail_message="Q4: no spelling isolated ANY-CONDITIONAL (rakshasa+wraith in, others out).",
        note_prefix="Q4")


async def _probe_q6(connection: Any, report: ProbeReport) -> None:
    """Q6 — wall-clock latency at scale (index-served membership vs the array-filter TableScans)."""
    print(f"\n=== Q6 — LATENCY at {TOTAL_ROWS} rows (median ms, warmup dropped) ===")
    q3_stmt = (f"SELECT id FROM {TABLE} WHERE "
               "count(damage_immunities[WHERE type='Bludgeoning' AND condition IS NONE])>0")
    q4_stmt = (f"SELECT id FROM {TABLE} WHERE "
               "count(damage_immunities[WHERE condition IS NOT NONE])>0")
    timings = {
        "object membership INSIDE [*].type (di_type)": await _time_query(
            connection, f"SELECT id FROM {TABLE} WHERE 'Fire' INSIDE damage_immunities[*].type", {}),
        "string baseline INSIDE di_flat[*]": await _time_query(
            connection, f"SELECT id FROM {TABLE} WHERE 'Fire' INSIDE di_flat", {}),
        "Q3 unconditional array-filter": await _time_query(connection, q3_stmt, {}),
        "Q4 any-conditional array-filter": await _time_query(connection, q4_stmt, {}),
    }
    for name, ms in timings.items():
        print(f"  {ms:8.2f} ms   {name}")
    report.notes.append("Q6 latencies (ms): " + "; ".join(f"{k}={v:.2f}" for k, v in timings.items()))


async def _probe_q7(connection: Any, report: ProbeReport) -> None:
    """Q7 — the edge-table alternative (plain-table read is indexed; a traversal never is)."""
    print("\n=== Q7 — EDGE-TABLE alternative (immune_to edge; plain-table read vs traversal) ===")
    await _try_ddl(connection, "damage_type table",
                   "DEFINE TABLE IF NOT EXISTS damage_type SCHEMALESS", report)
    await _try_ddl(connection, "immune_to edge",
                   "DEFINE TABLE IF NOT EXISTS immune_to TYPE RELATION IN stat_block OUT damage_type", report)
    await _try_ddl(connection, "immune_to.condition field",
                   "DEFINE FIELD OVERWRITE condition ON immune_to TYPE option<string>", report)
    await _try_ddl(connection, "immune_to out index",
                   "DEFINE INDEX IF NOT EXISTS immune_to_out ON immune_to FIELDS out", report)
    await _q(connection, "CREATE type::record('damage_type','fire') CONTENT { name: 'Fire' }")
    await _q(connection, "CREATE type::record('damage_type','bludgeoning') CONTENT { name: 'Bludgeoning' }")
    # relate the known rows (bound RecordIDs — store-ref §4)
    for key, objs in KNOWN.items():
        for o in objs:
            dt = o["type"].lower()
            if dt not in ("fire", "bludgeoning"):
                continue
            await connection.query(
                "RELATE $from->immune_to->$to SET condition = $cond",
                {"from": RecordID(TABLE, f"sb_{key}"), "to": RecordID("damage_type", dt),
                 "cond": o.get("condition")},
            )
    # plain-table read of the edge (store-ref §4: index an edge, read it AS A PLAIN TABLE)
    edge_plain = await explain(
        report, connection, table="immune_to",
        label="Q7 edge plain-table read: SELECT in FROM immune_to WHERE out=damage_type:fire",
        select="in", where="out = type::record('damage_type','fire')", dump=True)
    edge_rows = _rows(
        await _q(connection, "SELECT in FROM immune_to WHERE out = type::record('damage_type','fire')"))
    print(f"  edge plain-read matched {len(edge_rows) if edge_rows else 'see raw'} edges "
          "(in-nodes are the immune monsters)")
    report.notes.append(f"Q7 edge plain-table read classified {edge_plain.classification} "
                       f"(index={edge_plain.index_names}); a traversal from a start node is always a "
                       "GraphEdgeScan (store-ref §4), so the edge idiom only indexes via the plain read.")


async def probe(connection: Any, report: ProbeReport) -> None:
    """Run every question group in order (Q5 baseline before Q2 so the bar is set first)."""
    await _probe_q1(connection, report)
    await _probe_controls(connection, report)
    await _probe_q5_baseline(connection, report)
    await _probe_q2(connection, report)
    await _probe_q3(connection, report)
    await _probe_q4(connection, report)
    await _probe_q6(connection, report)
    await _probe_q7(connection, report)


# --------------------------------------------------------------------------- #
# VERDICT
# --------------------------------------------------------------------------- #


def verdict(report: ProbeReport, version: str) -> None:
    print("\n" + "=" * 78)
    print(f"SPIKE ENGINE UNDER TEST: {version}")
    print("=" * 78)
    print("\n=== NOTES (findings the design leans on) ===")
    for note in report.notes:
        print(f"  • {note}")
    print("\n=== SELF-CHECK VERDICT ===")
    if report.surprises:
        print(f"SURPRISES ({len(report.surprises)}) — a claimed clear is NOT trustworthy:")
        for s in report.surprises:
            print(f"  - {s}")
    else:
        print("All controls held; every load-bearing membership query returned the discriminating")
        print("correct rows; every required plan classified as expected.")


async def main() -> int:
    database = unique_database()
    connection = AsyncSurreal(URL)
    await connection.signin(signin_credentials(user=USER, password=SecretStr(PASSWORD)))
    await bootstrap_session(connection, NAMESPACE, database, url=URL)
    try:
        version = await connection.version()
    except Exception as error:  # noqa: BLE001
        version = f"<version() failed: {error}>"
    print(f"probe database: {NAMESPACE}:{database}  (TEST store {URL})  engine={version}")

    report = ProbeReport()
    try:
        await setup_schema(connection, report)
        await seed(connection)
        await probe(connection, report)
    finally:
        try:
            await connection.query(f"REMOVE DATABASE IF EXISTS {database}")
        except Exception as error:  # noqa: BLE001
            print(f"[cleanup warning] {type(error).__name__}: {error}")
        await connection.close()

    verdict(report, str(version))
    return 1 if report.surprises else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
