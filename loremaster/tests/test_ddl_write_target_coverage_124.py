"""#124 — every table production writes to is DEFINEd before first write.

Contract by contract-author-07, packet 07, 2026-08-17. Discovery: ddl-coverage-scout-07
(map inline in ``REPORT-contract-author-07.md`` §7). Fork rulings: operator ratifies (§7).

THE INVARIANT (#124, resolved-open 2026-07-14; store reference §5's conclusion):
    every table production code WRITES to is emitted by some ``generate_*_ddl`` first.
Two MEASURED reasons this is load-bearing, not tidiness: (1) concurrent first-write to an
UNDECLARED table STORMS with retryable conflicts (#124/#144); (2) an undeclared EDGE table
auto-creates ``TYPE ANY``, silently discarding the ``IN``/``OUT`` guard — the ONLY endpoint
validation the engine offers (store reference §4/§5). Production's exposure is NIL today
(bootstrap DEFINEs every table); this pin turns that CONVENTION into an INVARIANT.

⚠ FORMULATION — right-sized to the CONSTANT level, deliberately (reach-attack STOP-rule).
The discovery proved production write targets are, without exception, a ``*_TABLE`` /
``*_RELATION`` string CONSTANT interpolated into the write's f-string (``type::record(
'{AGENT_TABLE}', …)`` / ``UPSERT {META_TABLE} …`` / ``RELATE $a->{TO_RELATION}->$b``). So the
realistic #124 regression is: *someone adds a new table constant + writes through it, and
forgets the ``generate_*_ddl``.* This pin catches THAT — every ``*_TABLE``/``*_RELATION``
constant's value must be in the derived declared set — WITHOUT a brittle SurrealQL string
scanner (which would false-match prose/docstrings mentioning a verb and is exactly the
reach-attack antipattern the repo has the most receipts against). Both sides are DERIVED
(reach = a checked variable): constants from ``vars(surreal_schema)``, declared tables from
every ``generate_*_ddl``.

GREEN AT HEAD, on purpose — this is #124's REGRESSION-PREVENTION instrument (production
already holds the property), not a RED missing-guard. Its discriminating power is the
POSITIVE CONTROL (a planted undeclared constant reddens the invariant).

STATED BOUND (WHEN-YOU-CANNOT-CLOSE-A-HOLE-PIN-IT), for the contract-adversary's REACH
ATTACK: this covers the table-CONSTANT write idiom (the sole production idiom, discovery
§B.2). A hypothetical production write with a LITERAL table name (``CREATE foo:1 …`` — not a
constant) would be invisible to a constant-level pin. RE-OPEN TRIGGER: the day any production
write targets a table by literal name rather than a constant — at which point the target
should become a constant (the house idiom) OR this pin gains a string-level write-site scan.

⚠ FORK 1 (drafted to the discovery's recommended reading; operator ratifies — §7): extension
entity tables are scoped OUT. An extension applies its OWN DDL (not any ``generate_*_ddl``),
its tables are NOT ``surreal_schema`` constants (they are runtime, from
``IngestBackend.entity_tables()``), and the #124 property for that path is ALREADY enforced
at RUNTIME by ``extension.ExtensionLifecycleNotReadyError`` (#375). A constant-level pin
scopes them out BY CONSTRUCTION — they own no ``*_TABLE`` constant here.
"""

from __future__ import annotations

import inspect
import re
from collections.abc import Callable

from _enforced_relations_scaffold import statements
from loremaster.store import surreal_schema

# A tiny embedding width for the generators that build HNSW indexes — this pin reads the
# DEFINE-TABLE text, never recall quality.
_MIGRATION_DIM = 8

_DEFINE_TABLE_RE = re.compile(r"^DEFINE TABLE (?:OVERWRITE |IF NOT EXISTS )?(?P<name>\S+)")


def _ddl_generators() -> dict[str, Callable[..., str]]:
    """Every ``generate_*_ddl`` in ``surreal_schema`` — DERIVED from the module (INSTRUMENT
    0: reach is a checked variable), so a new generator, or a table a new generator emits, is
    covered the day it is written.

    Deliberately NOT ``_enforced_relations_scaffold.ALL_DDL_GENERATORS`` — the discovery
    proved that hand-list is MISSING ``generate_lease_ddl`` + ``generate_floor_calibration_
    ddl`` (harmless for its relation-only sweep, a silent hole for a full-table set). Deriving
    makes that omission unrepresentable.
    """
    return {
        name: fn
        for name, fn in inspect.getmembers(surreal_schema, inspect.isfunction)
        if name.startswith("generate_") and name.endswith("_ddl")
    }


def _emit(generator: Callable[..., str]) -> str:
    """Call a generator, passing ``dim`` only if it accepts one (some build HNSW indexes)."""
    if "dim" in inspect.signature(generator).parameters:
        return generator(dim=_MIGRATION_DIM)
    return generator()


def _declared_tables() -> set[str]:
    """Every table name any ``generate_*_ddl`` emits a ``DEFINE TABLE`` for."""
    declared: set[str] = set()
    for generator in _ddl_generators().values():
        for statement in statements(_emit(generator)):
            match = _DEFINE_TABLE_RE.match(statement)
            if match is not None:
                declared.add(match.group("name"))
    return declared


def _table_constants() -> dict[str, str]:
    """``{constant_NAME: value}`` for every ``*_TABLE`` / ``*_RELATION`` str constant
    ``surreal_schema`` exports — the vocabulary every production write interpolates.
    """
    return {
        name: value
        for name, value in vars(surreal_schema).items()
        if isinstance(value, str) and (name.endswith("_TABLE") or name.endswith("_RELATION"))
    }


def _undeclared_constants(constants: dict[str, str], declared: set[str]) -> dict[str, str]:
    """The ``*_TABLE``/``*_RELATION`` constants whose value is NOT in ``declared`` — the ONE
    expression the invariant AND its positive control both read (adversary-07 F3), so the
    control exercises the invariant's own comparison rather than a parallel copy of it.
    """
    return {name: value for name, value in constants.items() if value not in declared}


class TestEveryTableConstantIsDeclared:
    """#124 — the write-target-coverage invariant at the CONSTANT level, both sides DERIVED."""

    def test_the_declared_generator_reach_covers_every_generate_ddl_symbol(self) -> None:
        """Reach pin: the declared set is DERIVED from EVERY ``generate_*_ddl`` in
        ``surreal_schema``, never a hand-list. If the derivation stops seeing a known
        generator, it goes RED — reach is a checked variable. (The ``ALL_DDL_GENERATORS``
        scaffold list is missing ``lease``+``floor``; this derivation cannot be.)
        """
        derived = set(_ddl_generators())
        assert {
            "generate_ddl",
            "generate_lease_ddl",
            "generate_floor_calibration_ddl",
        } <= derived, (
            "the generator derivation lost a known generate_*_ddl — reach is no longer a "
            f"checked variable, and the lease/floor tables would silently drop out. "
            f"Derived: {sorted(derived)}"
        )
        assert len(derived) >= 11, f"expected >=11 generate_*_ddl, derived {sorted(derived)}"

    def test_every_table_constant_value_is_a_declared_table(self) -> None:
        """THE INVARIANT (GREEN at HEAD; RED the day a ``*_TABLE``/``*_RELATION`` constant
        names a table no ``generate_*_ddl`` DEFINEs). Since every production write targets a
        table via one of these constants (discovery §B.2), an undeclared constant is a write
        that would storm on first-write / lose its edge guard (#124, store ref §4-5).
        """
        declared = _declared_tables()
        undeclared = _undeclared_constants(_table_constants(), declared)
        assert not undeclared, (
            "these surreal_schema table/relation CONSTANTS name tables NO generate_*_ddl "
            "DEFINEs — a write through them targets an undeclared table (concurrent "
            "first-write STORMS with retryable conflicts; an undeclared EDGE auto-creates "
            f"TYPE ANY, discarding the IN/OUT guard — #124/store ref §4-5): {undeclared}. "
            f"Declared: {sorted(declared)}"
        )

    def test_the_constant_reach_actually_sees_the_known_write_target_constants(self) -> None:
        """Anti-vacuity: the DERIVED constant set must actually contain the load-bearing
        write-target constants (a derivation that saw NONE would make the invariant vacuously
        green). Names the endpoints of the guarded idioms (type::record / RELATE edges).
        """
        constants = set(_table_constants())
        expected = {
            "AGENT_TABLE",
            "MESSAGE_TABLE",
            "TASK_TABLE",
            "FINDING_TABLE",
            "META_TABLE",
            "SNAPSHOT_TABLE",
            "NAME_TABLE",
            "TO_RELATION",
            "BRIEFED_RELATION",
            "BLOCKS_RELATION",
        }
        missing = expected - constants
        assert not missing, (
            f"the table-constant derivation did not see known write-target constants: {missing}. "
            "Reach is not a checked variable — the invariant is vacuous for whatever it missed."
        )


class TestTheCoverageInvariantDiscriminates:
    """Controls — a pin that cannot see its own violation proves nothing (fixtures must
    discriminate). Run the REAL derivation against a planted undeclared constant.
    """

    def test_a_planted_undeclared_constant_would_redden_the_invariant(self) -> None:
        """POSITIVE CONTROL: the invariant's own comparison, run against a constant set with a
        ghost table added, MUST flag it — proving the green above is not vacuous.
        """
        declared = _declared_tables()
        planted = {**_table_constants(), "GHOST_TABLE": "ghost_undeclared_table"}
        # The invariant's OWN expression (F3 — not a parallel copy), run against a planted ghost.
        undeclared = _undeclared_constants(planted, declared)
        assert undeclared == {"GHOST_TABLE": "ghost_undeclared_table"}, (
            "the invariant's comparison did not flag a planted undeclared constant — it "
            f"cannot discriminate a #124 violation from a clean tree. Flagged: {undeclared}"
        )

    def test_the_declared_extraction_actually_parses_define_table(self) -> None:
        """CONTROL on the declared side: the DEFINE-TABLE regex must extract a real table from
        real generator output — a regex that matched nothing would make the invariant
        vacuously green (every constant 'undeclared', or the set empty).

        ⚠ NOTED BOUND (adversary-07 F4, ruled note-not-pin): a corrupted ``_declared_tables()``
        that unioned in every constant VALUE would defeat the invariant and still pass this
        control (``CHUNK_TABLE`` present, ``len >= 20`` holds). That requires sabotaging the TEST
        helper — it is NOT a production regression, and the realistic production regression (a new
        constant with no ``generate_*_ddl``) IS caught by the invariant. Left as a note, not a pin.
        """
        declared = _declared_tables()
        assert surreal_schema.CHUNK_TABLE in declared, (
            f"the DEFINE TABLE extraction missed {surreal_schema.CHUNK_TABLE!r} — the declared "
            f"set is not being parsed from generator output. Declared: {sorted(declared)}"
        )
        assert len(declared) >= 20, f"suspiciously few declared tables: {sorted(declared)}"
