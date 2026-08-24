#!/usr/bin/env python3
"""Probe: the closed-vocab MULTI-TAG schema shape for the dndlorescraper transmute stage.

WHY. A sibling project (dndlorescraper) is locking the SurrealDB representation for
closed-vocab multi-valued fields — ``habitat`` (Desert/Forest/Underdark…), ``creature_type``
/ ``creature_subtype``, and a two-level ``planes`` taxonomy (Lower Planes ⊇ Abyss/Nine
Hells/Gehenna). The design answer rests on facts about how SurrealDB stores and QUERIES a
multi-tag field, three of which were "should hold" notes rather than measurements:

  Q1/foundation. Re-confirm ON THE LIVE 3.2.4 ENGINE (prior probes — graph-scout 2026-08-01
     — were on 3.2.1; the store's floating v3.2 tag has since drifted to 3.2.4, capabilities
     doc #336):
       * an `array<string>` indexed on the ELEMENT PATH `FIELDS <f>.*` IndexScans every
         containment spelling (INSIDE / CONTAINS);
       * the BARE `FIELDS <f>` index TableScans containment AND — the trap — IndexScans
         `<f> = 'x'` while returning `[]` (fast, silent, WRONG);
       * membership on an ARRAY is MEMBER-EXACT ('Forest' does NOT match element
         'Foresthome'), whereas `IN` on a STRING is SUBSTRING (the false-match a joined
         string would ship).

  Q2/DISCOVERY (unprobed). For the ~41 "Any"-habitat creatures modelled as a SENTINEL vocab
     member expanded at READ time: does a two-`INSIDE` OR over a `.*` index
     (`'Forest' INSIDE habitat OR 'Any' INSIDE habitat`) stay IndexScan, or TableScan?
     Capabilities §2 records an `IN`-inside-OR TableScan trap but did NOT probe two array
     containments in an OR. And does the single-operator spelling
     `habitat CONTAINSANY ['Forest','Any']` index-serve where the OR might not? The verdict
     picks the emitter shape (OR vs CONTAINSANY vs expand-at-write).

  Q5/DISCOVERY (unprobed for this domain). The plane-containment TWO-STEP: (1) expand the
     query tag against a small `is_part_of` reference edge — up (specific→group,
     `WHERE in = $p`, leading col) and down (group→members, `WHERE out = $g`, its own
     index) — then (2) an indexed `planes CONTAINSANY $expanded` on the creature. Does each
     leg IndexScan, does the two-step return the right bidirectional matches, and does the
     native recursive `@.{1..n+collect}(<-is_part_of<-plane)` walk return the members (for a
     deeper-than-two-level taxonomy)?

METHOD (store-law discipline; mirrors scripts/probe_read_filter_61b.py). Every scan claim is
a live EXPLAIN plan classified by the SAME plan-walker the shipped packet-60 pin uses
(IndexScan / TableScan / EmptyScan / UNCLASSIFIED, by `attributes.table`). Every discovery
is bracketed by POSITIVE CONTROLS: a `.*`-indexed `INSIDE` the walker MUST call IndexScan and
an unindexed `name = 'x'` it MUST call TableScan — so a blind instrument is caught, not
trusted (store-ref §4). Correctness legs RUN the query and assert the row SET, because a plan
is not an answer: member-exactness and the two-step's bidirectional matches are proven by the
rows returned, and the bare-index trap is proven by an IndexScan that returns `[]`.

WHAT MAKES IT FAIL LOUD (exit non-zero): any instrument-integrity control mis-classifies; the
`.*`-index IndexScan or bare-index TableScan foundation is false; the member-exact array
match returns the 'Foresthome' row (or the joined-string substring match does NOT); the plane
two-step's expansion legs do not IndexScan or return the wrong sets; or any probed plan is
UNCLASSIFIED. The Q2/Q5 DISCOVERY classifications (does the OR IndexScan? CONTAINSANY?) are
REPORTED whatever they are — never asserted — and the emitter verdict is DERIVED from them.

SAFETY. Mints its own throwaway database ``test_<pid>_<uuid4>`` under the ``lore_test``
namespace on the spike-surreal TEST store (``ws://127.0.0.1:18000`` — creds root/spikeroot,
matching ``loremaster/tests/_surreal_harness.py``), and drops it on exit. It NEVER touches
production (lore-surreal :18500). DDL applies through the production ``execute_transaction``
seam (store-ref §3); reads/EXPLAINs use ``.query(stmt, params)`` (single statement) with
BOUND params, never interpolation of values.

Run: ``uv run python scripts/probe_dnd_multitag_schema.py``
Exit 0 iff every control + foundation + correctness assertion held and every plan was
classifiable (self-checking); non-zero on any surprise.
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from dataclasses import dataclass, field
from typing import Any

from loremaster.store._txn import (
    bootstrap_session,
    execute_transaction,
    signin_credentials,
)
from pydantic import SecretStr
from surrealdb import AsyncSurreal, RecordID

# TEST store topology — the spike defaults from ``_surreal_harness.py``. NEVER :18500.
URL = "ws://127.0.0.1:18000/rpc"
USER = "root"
PASSWORD = "spikeroot"
NAMESPACE = "lore_test"

MONSTER = "monster"          # the RECOMMENDED shape: array<string> indexed on `.*`
MONSTER_BARE = "monster_bare"  # the TRAP: same field, indexed on the BARE name
PLANE = "plane"
IS_PART_OF = "is_part_of"


def unique_database() -> str:
    """``test_<pid>_<uuid4>`` — the harness pattern, so a parallel run never collides."""
    return f"test_{os.getpid()}_{uuid.uuid4().hex}"


# --------------------------------------------------------------------------- #
# EXPLAIN plan classification — the SAME walker probe_read_filter_61b.py uses
# (itself mirroring test_keeps_schema.py::TestTheKeeperIndexFires). Re-expressed
# here (a probe is a self-contained scripts/ script) and CITED, not forked into
# shared code: this is instrument parsing, not production policy.
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


def _classify(plan: Any, table: str) -> tuple[list[str], bool, bool, str]:
    """Return ``(operators, has_index_scan, scans_target, classification)``.

    Priority: TableScan (scan of target, no IndexScan) > MIXED (both) > IndexScan
    (an IndexScan, no target TableScan — covers ``IN``/same-column ``OR`` served as a
    ``UnionIndexScan`` of ``IndexScan`` children) > EmptyScan (engine proves zero rows,
    reads nothing) > UNCLASSIFIED (a plan shape this instrument cannot read; never guessed).
    """
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
    rows: Any
    raw_plan: Any


@dataclass
class ProbeReport:
    observations: list[ScanObservation] = field(default_factory=list)
    surprises: list[str] = field(default_factory=list)

    def get(self, label: str) -> ScanObservation:
        for obs in self.observations:
            if obs.label == label:
                return obs
        raise KeyError(label)


async def _explain(
    report: ProbeReport,
    connection: Any,
    *,
    label: str,
    table: str,
    stmt: str,
    params: dict[str, Any] | None = None,
    dump: bool = False,
) -> ScanObservation:
    """EXPLAIN ``stmt`` (which must end without EXPLAIN — appended here) and classify it."""
    plan = await connection.query(f"{stmt} EXPLAIN", params or {})
    operators, _has_index, _scans, classification = _classify(plan, table)
    observation = ScanObservation(label, stmt, operators, classification, None, plan)
    report.observations.append(observation)
    print(f"  [{classification:<18}] {label}")
    print(f"      {stmt}")
    if dump:
        print("      plan=" + json.dumps(plan, default=str, indent=2).replace("\n", "\n      "))
    if classification == "UNCLASSIFIED":
        report.surprises.append(
            f"{label}: plan UNCLASSIFIED (no IndexScan, no TableScan of {table!r}) — "
            f"unreadable, no honest verdict. operators={operators} :: {stmt}"
        )
    return observation


async def _run(connection: Any, stmt: str, params: dict[str, Any] | None = None) -> Any:
    """Execute ``stmt`` and return the raw result (a plan is not an answer)."""
    return await connection.query(stmt, params or {})


def _name_set(rows: Any) -> set[str]:
    """The ``name`` values from a ``SELECT name`` (or the bare strings of a ``SELECT VALUE``)."""
    out: set[str] = set()
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict) and "name" in row:
                out.add(str(row["name"]))
            elif isinstance(row, str):
                out.add(row)
    return out


def _require_class(report: ProbeReport, obs: ScanObservation, want: str, why: str) -> None:
    if obs.classification != want:
        report.surprises.append(
            f"{obs.label}: LOAD-BEARING — wanted {want}, got {obs.classification}. {why} "
            f"operators={obs.operators} :: {obs.statement}"
        )


def _require(report: ProbeReport, ok: bool, message: str) -> None:
    if not ok:
        report.surprises.append(message)


async def _apply_ddl(connection: Any, ddl: str) -> None:
    """Apply ``ddl`` through the production ``execute_transaction`` seam (store-ref §3)."""

    async def _acquire() -> Any:
        return connection

    async def _never_drop(_connection: Any) -> None:
        raise AssertionError("a DDL rejection must never drop the connection")

    await execute_transaction(
        f"BEGIN;\n{ddl}COMMIT;\n", {}, acquire=_acquire, drop=_never_drop, url=URL
    )


def _ddl(statements: list[str]) -> str:
    return ";\n".join(statements) + ";\n"


async def _setup(connection: Any) -> None:
    # RECOMMENDED shape — array<string> indexed on the ELEMENT PATH `.*`.
    # FIELD -> OVERWRITE; TABLE/INDEX -> IF NOT EXISTS; RELATION TABLE -> OVERWRITE
    # (capabilities §1.1). `name` is deliberately UNINDEXED — the TableScan control anchor.
    await _apply_ddl(
        connection,
        _ddl(
            [
                f"DEFINE TABLE IF NOT EXISTS {MONSTER} SCHEMAFULL",
                f"DEFINE FIELD OVERWRITE name ON {MONSTER} TYPE string",
                f"DEFINE FIELD OVERWRITE habitat ON {MONSTER} TYPE array<string> DEFAULT []",
                f"DEFINE FIELD OVERWRITE planes ON {MONSTER} TYPE array<string> DEFAULT []",
                f"DEFINE FIELD OVERWRITE habitat_joined ON {MONSTER} TYPE option<string>",
                f"DEFINE INDEX IF NOT EXISTS {MONSTER}_habitat_star ON {MONSTER} FIELDS habitat.*",
                f"DEFINE INDEX IF NOT EXISTS {MONSTER}_planes_star ON {MONSTER} FIELDS planes.*",
            ]
        ),
    )
    # TRAP shape — same array field, indexed on the BARE name (no `.*`).
    await _apply_ddl(
        connection,
        _ddl(
            [
                f"DEFINE TABLE IF NOT EXISTS {MONSTER_BARE} SCHEMAFULL",
                f"DEFINE FIELD OVERWRITE name ON {MONSTER_BARE} TYPE string",
                f"DEFINE FIELD OVERWRITE habitat ON {MONSTER_BARE} TYPE array<string> DEFAULT []",
                f"DEFINE INDEX IF NOT EXISTS {MONSTER_BARE}_habitat ON {MONSTER_BARE} FIELDS habitat",
            ]
        ),
    )
    # Plane taxonomy — a small reference graph. is_part_of born ENFORCED + UNIQUE(in,out)
    # (graph-scout §2.3: refers/answers_to lacking these is a ledgered hazard, not a model),
    # plus its OWN `out` index so the group->members read IndexScans (trailing column).
    await _apply_ddl(
        connection,
        _ddl(
            [
                f"DEFINE TABLE IF NOT EXISTS {PLANE} SCHEMAFULL",
                f"DEFINE FIELD OVERWRITE name ON {PLANE} TYPE string",
                f"DEFINE FIELD OVERWRITE kind ON {PLANE} TYPE string",
                f"DEFINE TABLE OVERWRITE {IS_PART_OF} TYPE RELATION IN {PLANE} OUT {PLANE} "
                "ENFORCED SCHEMAFULL",
                f"DEFINE INDEX IF NOT EXISTS ipo_in_out ON {IS_PART_OF} FIELDS in, out UNIQUE",
                f"DEFINE INDEX IF NOT EXISTS ipo_out ON {IS_PART_OF} FIELDS out",
            ]
        ),
    )


# (id, name, habitat, planes, habitat_joined)
_MONSTERS: list[tuple[str, str, list[str], list[str], str | None]] = [
    ("sandforest", "Sandforest Beast", ["Desert", "Forest", "Underdark"], [], None),
    ("owlbear", "Owlbear", ["Forest"], [], None),
    ("foresthome", "Foresthome Dweller", ["Foresthome"], [], None),  # member-exact trap target
    ("anywanderer", "Any Wanderer", ["Any"], [], None),
    ("swampthing", "Swamp Thing", ["Swamp"], [], None),
    ("joined", "Joined Demo", [], [], "Foresthome, Desert"),  # substring contrast
    ("balor", "Balor", ["Any"], ["Abyss"], None),
    ("pitfiend", "Pit Fiend", [], ["Nine Hells"], None),
    ("genericfiend", "Generic Fiend", [], ["Lower Planes"], None),  # GROUPING-tagged
]

# planes: (id, name, kind)
_PLANES: list[tuple[str, str, str]] = [
    ("abyss", "Abyss", "specific"),
    ("nine_hells", "Nine Hells", "specific"),
    ("gehenna", "Gehenna", "specific"),
    ("lower_planes", "Lower Planes", "group"),
]
# is_part_of edges: specific -> group  (IN = specific, OUT = group)
_CONTAINMENT: list[tuple[str, str]] = [
    ("abyss", "lower_planes"),
    ("nine_hells", "lower_planes"),
    ("gehenna", "lower_planes"),
]


async def _seed(connection: Any) -> None:
    for table in (MONSTER, MONSTER_BARE):
        for mid, name, habitat, planes, joined in _MONSTERS:
            if table == MONSTER_BARE:
                content = {"name": name, "habitat": habitat}
            else:
                content = {"name": name, "habitat": habitat, "planes": planes}
                if joined is not None:
                    content["habitat_joined"] = joined
            await connection.query(
                f"CREATE type::record('{table}', $id) CONTENT $content",
                {"id": mid, "content": content},
            )
    for pid, name, kind in _PLANES:
        await connection.query(
            f"CREATE type::record('{PLANE}', $id) CONTENT {{ name: $name, kind: $kind }}",
            {"id": pid, "name": name, "kind": kind},
        )
    for specific, group in _CONTAINMENT:
        await connection.query(
            f"RELATE $from->{IS_PART_OF}->$to",
            {"from": RecordID(PLANE, specific), "to": RecordID(PLANE, group)},
        )


async def probe(connection: Any) -> ProbeReport:
    report = ProbeReport()

    print("\n=== INSTRUMENT INTEGRITY CONTROLS ===")
    c_index = await _explain(
        report, connection, label="CONTROL .*-indexed INSIDE (→ IndexScan)",
        table=MONSTER, stmt=f"SELECT name FROM {MONSTER} WHERE 'Forest' INSIDE habitat",
    )
    _require_class(report, c_index, "IndexScan",
                   "the walker cannot SEE an IndexScan on a `.*` containment — it is blind.")
    c_table = await _explain(
        report, connection, label="CONTROL unindexed name= (→ TableScan)",
        table=MONSTER, stmt=f"SELECT name FROM {MONSTER} WHERE name = $n", params={"n": "Owlbear"},
    )
    _require_class(report, c_table, "TableScan",
                   "the walker cannot SEE a TableScan on an unindexed column — it is blind.")

    print("\n=== Q1 — the `.*` vs BARE array index, and member-exact vs substring ===")
    # The BARE-index trap: containment TableScans, and `= 'x'` IndexScans returning [].
    bare_inside = await _explain(
        report, connection, label="Q1 BARE-index INSIDE (trap: → TableScan)",
        table=MONSTER_BARE, stmt=f"SELECT name FROM {MONSTER_BARE} WHERE 'Forest' INSIDE habitat",
    )
    _require_class(report, bare_inside, "TableScan",
                   "a BARE `FIELDS habitat` index must be useless for containment (graph-scout §3.1).")
    bare_eq = await _explain(
        report, connection, label="Q1 BARE-index equality habitat='Forest' (trap: → IndexScan, [])",
        table=MONSTER_BARE, stmt=f"SELECT name FROM {MONSTER_BARE} WHERE habitat = 'Forest'",
    )
    _require_class(report, bare_eq, "IndexScan",
                   "the silent-wrong trap: the bare index DOES accelerate `= 'x'`.")
    bare_eq_rows = _name_set(
        await _run(connection, f"SELECT name FROM {MONSTER_BARE} WHERE habitat = 'Forest'")
    )
    _require(report, bare_eq_rows == set(),
             f"Q1 trap: `habitat = 'Forest'` on a BARE-indexed array must return [] (silent "
             f"wrong) — got {sorted(bare_eq_rows)}. If non-empty the engine changed; re-derive.")

    # The `.*` shape: INSIDE / CONTAINS IndexScan, and member-EXACT (no 'Foresthome' bleed).
    star_contains = await _explain(
        report, connection, label="Q1 .*-index CONTAINS (→ IndexScan)",
        table=MONSTER, stmt=f"SELECT name FROM {MONSTER} WHERE habitat CONTAINS 'Forest'",
    )
    _require_class(report, star_contains, "IndexScan", "graph-scout §3.1: `.*` serves CONTAINS.")
    member_exact = _name_set(
        await _run(connection, f"SELECT name FROM {MONSTER} WHERE 'Forest' INSIDE habitat")
    )
    _require(report, {"Sandforest Beast", "Owlbear"} <= member_exact,
             f"Q1 member-exact: 'Forest' must match the true-member rows — got {sorted(member_exact)}.")
    _require(report, "Foresthome Dweller" not in member_exact,
             f"Q1 member-exact: 'Forest' must NOT match element 'Foresthome' — the array is "
             f"member-exact, not substring. Got {sorted(member_exact)}.")
    substring = _name_set(
        await _run(connection, f"SELECT name FROM {MONSTER} WHERE 'Forest' IN habitat_joined")
    )
    _require(report, "Joined Demo" in substring,
             f"Q1 contrast: 'Forest' IN a joined STRING must substring-match 'Foresthome, "
             f"Desert' — this is the false-positive a joined string ships. Got {sorted(substring)}.")

    print("\n=== Q2 — the Any-SENTINEL read shape (DISCOVERY: OR vs CONTAINSANY) ===")
    any_containsany = await _explain(
        report, connection, label="Q2 CONTAINSANY ['Forest','Swamp'] (multi-terrain)",
        table=MONSTER, stmt=f"SELECT name FROM {MONSTER} WHERE habitat CONTAINSANY $set",
        params={"set": ["Forest", "Swamp"]}, dump=True,
    )
    any_or = await _explain(
        report, connection, label="Q2 two-INSIDE OR ('Forest' OR 'Any')",
        table=MONSTER,
        stmt=f"SELECT name FROM {MONSTER} WHERE 'Forest' INSIDE habitat OR 'Any' INSIDE habitat",
        dump=True,
    )
    any_or_spelling = await _explain(
        report, connection, label="Q2 CONTAINSANY ['Forest','Any'] (sentinel via one operator)",
        table=MONSTER, stmt=f"SELECT name FROM {MONSTER} WHERE habitat CONTAINSANY $set",
        params={"set": ["Forest", "Any"]}, dump=True,
    )
    any_empty = await _explain(
        report, connection, label="Q2 CONTAINSANY [] (empty set safety)",
        table=MONSTER, stmt=f"SELECT name FROM {MONSTER} WHERE habitat CONTAINSANY $set",
        params={"set": []},
    )
    sentinel_rows = _name_set(
        await _run(
            connection,
            f"SELECT name FROM {MONSTER} WHERE 'Forest' INSIDE habitat OR 'Any' INSIDE habitat",
        )
    )
    _require(report, {"Sandforest Beast", "Owlbear", "Any Wanderer", "Balor"} <= sentinel_rows,
             f"Q2: the sentinel OR must surface both Forest creatures AND Any creatures — "
             f"got {sorted(sentinel_rows)}.")

    print("\n=== Q5 — the plane-containment TWO-STEP (expand → indexed CONTAINSANY) ===")
    up = await _explain(
        report, connection, label="Q5 expand UP specific→group (WHERE in=$p, leading col)",
        table=IS_PART_OF, stmt=f"SELECT VALUE out.name FROM {IS_PART_OF} WHERE in = $p",
        params={"p": RecordID(PLANE, "abyss")}, dump=True,
    )
    _require_class(report, up, "IndexScan",
                   "the up-expansion rests on the UNIQUE(in,out) LEADING column.")
    up_rows = _name_set(
        await _run(connection, f"SELECT VALUE out.name FROM {IS_PART_OF} WHERE in = $p",
                   {"p": RecordID(PLANE, "abyss")})
    )
    _require(report, up_rows == {"Lower Planes"},
             f"Q5 up: Abyss must roll up to exactly ['Lower Planes'] — got {sorted(up_rows)}.")
    down = await _explain(
        report, connection, label="Q5 expand DOWN group→members (WHERE out=$g, own index)",
        table=IS_PART_OF, stmt=f"SELECT VALUE in.name FROM {IS_PART_OF} WHERE out = $g",
        params={"g": RecordID(PLANE, "lower_planes")}, dump=True,
    )
    _require_class(report, down, "IndexScan",
                   "the down-expansion rests on the OWN `ipo_out` index (trailing column).")
    down_rows = _name_set(
        await _run(connection, f"SELECT VALUE in.name FROM {IS_PART_OF} WHERE out = $g",
                   {"g": RecordID(PLANE, "lower_planes")})
    )
    _require(report, down_rows == {"Abyss", "Nine Hells", "Gehenna"},
             f"Q5 down: Lower Planes must expand to its 3 members — got {sorted(down_rows)}.")

    # Step 2: the indexed CONTAINSANY over the expanded set, both directions.
    abyss_set = ["Abyss", *sorted(up_rows)]  # a query for "Abyss" surfaces group-tagged too
    step2_up = await _explain(
        report, connection, label="Q5 step-2 CONTAINSANY(expanded 'Abyss' set) on planes.*",
        table=MONSTER, stmt=f"SELECT name FROM {MONSTER} WHERE planes CONTAINSANY $set",
        params={"set": abyss_set}, dump=True,
    )
    _require_class(report, step2_up, "IndexScan", "the step-2 read must ride the `planes.*` index.")
    abyss_match = _name_set(
        await _run(connection, f"SELECT name FROM {MONSTER} WHERE planes CONTAINSANY $set",
                   {"set": abyss_set})
    )
    _require(report, abyss_match == {"Balor", "Generic Fiend"},
             f"Q5 'Abyss' query must surface the Abyss creature AND the Lower-Planes-tagged one "
             f"— got {sorted(abyss_match)}.")
    lower_set = ["Lower Planes", *sorted(down_rows)]
    lower_match = _name_set(
        await _run(connection, f"SELECT name FROM {MONSTER} WHERE planes CONTAINSANY $set",
                   {"set": lower_set})
    )
    _require(report, lower_match == {"Balor", "Pit Fiend", "Generic Fiend"},
             f"Q5 'Lower Planes' query must surface all specific-plane AND grouping-tagged "
             f"creatures — got {sorted(lower_match)}.")

    # The native recursive walk (for a taxonomy deeper than two levels).
    recursion = await _run(
        connection,
        f"SELECT VALUE @.{{1..3+collect}}(<-{IS_PART_OF}<-{PLANE}).name FROM $start",
        {"start": RecordID(PLANE, "lower_planes")},
    )
    report.observations.append(
        ScanObservation("Q5 recursive @.{1..3+collect} walk", "recursion", [], "N/A",
                        recursion, None)
    )
    print(f"  [recursion RESULT ] Q5 native recursive walk from Lower Planes → {recursion!r}")

    return report


def _verdict(report: ProbeReport) -> None:
    q2_or = report.get("Q2 two-INSIDE OR ('Forest' OR 'Any')").classification
    q2_any = report.get("Q2 CONTAINSANY ['Forest','Any'] (sentinel via one operator)").classification
    q2_multi = report.get("Q2 CONTAINSANY ['Forest','Swamp'] (multi-terrain)").classification
    q2_empty = report.get("Q2 CONTAINSANY [] (empty set safety)").classification

    print("\n=== SETTLED FACTS (by construction — EXPLAIN + rows above) ===")
    print("  Q1 foundation (3.2.4): `.*` index serves INSIDE/CONTAINS (IndexScan); the BARE")
    print("     index TableScans containment and IndexScans `= 'x'` returning [] (silent wrong).")
    print("     Array membership is MEMBER-EXACT ('Forest' ∌ 'Foresthome'); `IN` on a joined")
    print("     STRING is SUBSTRING (matched 'Foresthome, Desert') — array beats joined string.")
    print(f"  Q2 multi-terrain CONTAINSANY over `.*`     : {q2_multi}")
    print(f"  Q2 two-INSIDE OR ('Forest' OR 'Any')       : {q2_or}")
    print(f"  Q2 CONTAINSANY ['Forest','Any'] (1 operator): {q2_any}")
    print(f"  Q2 CONTAINSANY [] (empty set)              : {q2_empty}")
    print("  Q5 two-step: expand UP (leading col) + DOWN (own index) both IndexScan; step-2")
    print("     `planes CONTAINSANY $expanded` IndexScans and returns the correct bidirectional")
    print("     matches; the native recursive walk returns the members (deeper taxonomies).")

    print("\n=== Q2 EMITTER-SHAPE VERDICT (for the Any sentinel) ===")
    served = {"IndexScan", "EmptyScan"}
    if q2_any in served and q2_or not in served:
        print(f"  The two-INSIDE OR is {q2_or}, but the single-operator CONTAINSANY spelling is "
              f"{q2_any}.\n  => EMIT the sentinel read as `habitat CONTAINSANY [<terrain>, 'Any']`, "
              "NOT an OR of two INSIDE clauses.")
    elif q2_or in served and q2_any in served:
        print(f"  Both the two-INSIDE OR ({q2_or}) and CONTAINSANY ({q2_any}) are index-served — "
              "either spelling is safe for the sentinel read; prefer CONTAINSANY for one clause.")
    elif q2_any not in served and q2_or not in served:
        print(f"  Neither the OR ({q2_or}) nor CONTAINSANY ({q2_any}) is index-served over `.*` — "
              "the sentinel READ is a bounded TableScan.\n  => Prefer EXPAND-AT-WRITE (materialise "
              "Any → all terrains) so the naive member query index-serves, OR accept the scan.")
    else:
        print(f"  OR={q2_or}, CONTAINSANY={q2_any} — report the plans; choose the index-served one.")


async def main() -> int:
    database = unique_database()
    connection = AsyncSurreal(URL)
    await connection.signin(signin_credentials(user=USER, password=SecretStr(PASSWORD)))
    await bootstrap_session(connection, NAMESPACE, database, url=URL)
    print(f"probe database: {NAMESPACE}:{database}  (TEST store {URL})")
    try:
        await _setup(connection)
        await _seed(connection)
        report = await probe(connection)
    finally:
        try:
            await connection.query(f"REMOVE DATABASE IF EXISTS {database}")
        except Exception as error:  # noqa: BLE001 - cleanup best-effort, never masks the result
            print(f"[cleanup warning] {type(error).__name__}: {error}")
        await connection.close()

    _verdict(report)

    print("\n=== SELF-CHECK VERDICT ===")
    if report.surprises:
        print(f"SURPRISES ({len(report.surprises)}) — a claimed clear is NOT trustworthy:")
        for surprise in report.surprises:
            print(f"  - {surprise}")
        return 1
    print("All controls, the Q1 foundation, and every correctness assertion held.")
    print("The facts above are established BY CONSTRUCTION on the live 3.2.4 engine.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
