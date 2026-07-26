"""Contract — packet 11-i-a, the floor-calibration + lease SCHEMA (B4).

Written by `contract-11ia-1` (2026-07-26). The builder builds FROM this.

WHAT THIS FILE DECIDES (the interface freeze 11-i-b cites) —
``loremaster.store.surreal_schema``::

    FLOOR_MEASUREMENT_TABLE = "floor_measurement"   # append-only history
    FLOOR_HEAD_TABLE        = "floor_head"          # one HOT row per head id
    LEASE_TABLE             = "lease"
    LEASE_SINGLETON_ID      = "singleton"
    generate_floor_calibration_ddl() -> str
    generate_lease_ddl() -> str

⚠ THE DDL DECISION RULE IS NOT NEGOTIABLE AND IT IS PINNED MECHANICALLY, not
trusted to a reviewer (store reference §1.1, finding #107 — a 100% production
outage whose answer was already written in that file):

    plain TABLE -> IF NOT EXISTS   ·   FIELD -> OVERWRITE
    INDEX       -> IF NOT EXISTS   ·   ALTER is a trap, not the migration verb

``DEFINE FIELD IF NOT EXISTS`` is a SILENT NO-OP on an existing field, so a
changed definition never migrates a live store — and every test in this repo
mints a VIRGIN database, which is *structurally* why 1040 tests, a cold audit
and a contract-adversary all passed #107. The clause pins below are the only
instrument a virgin-DB suite has; ``TestTheSchemaMigratesAnEXISTINGStore`` is
the other half, and it is the one that would actually have caught the outage.

⚠ AND THE INVERSIONS ARE PINNED AS A KNOWN BOUND. If this slice ever grows a
``TYPE RELATION`` table the FIELD/TABLE rule INVERTS for it (§1.1's RELATION
row: ``IF NOT EXISTS`` is a silent no-op on an existing edge table), and a
``DEFINE SEQUENCE`` carries #146's un-migratable ``BATCH``/``START`` residual.
``test_this_slice_contains_neither_a_relation_table_nor_a_sequence`` goes RED
the day either appears, carrying that instruction — so the next engineer meets
the bound DELIBERATELY instead of rediscovering it from an outage.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

import pytest
from _surreal_harness import (
    SurrealConnection,
    SurrealEnv,
    admin_db,  # noqa: F401 - re-exported pytest fixture
    run,
)
from loremaster.store import surreal_schema
from loremaster.store.surreal_schema import (
    FLOOR_HEAD_TABLE,
    FLOOR_MEASUREMENT_TABLE,
    FLOOR_NON_ADOPTION_CAUSES,
    FLOOR_STATES,
    LEASE_SINGLETON_ID,
    LEASE_TABLE,
    generate_floor_calibration_ddl,
    generate_lease_ddl,
)

_DEFINE_TABLE = re.compile(r"^\s*DEFINE\s+TABLE\b", re.IGNORECASE)
_DEFINE_FIELD = re.compile(r"^\s*DEFINE\s+FIELD\b", re.IGNORECASE)
_DEFINE_INDEX = re.compile(r"^\s*DEFINE\s+INDEX\b", re.IGNORECASE)

# The retired state name, spelled out in full so a bare, anchor-free sweep can
# find this line (repo rename law: sweep patterns carry no structural anchor,
# because prose mentions carry none either).
RETIRED_STATE_NAME = "stale_remeasuring"

_PACKAGE_ROOT = Path(surreal_schema.__file__).resolve().parents[1]
_TESTS_ROOT = Path(__file__).resolve().parent
# <repo>/loremaster/loremaster/store/surreal_schema.py -> parents[3] is <repo>
_REPO_ROOT = Path(surreal_schema.__file__).resolve().parents[3]


def _statements(ddl: str) -> list[str]:
    """The DDL's individual statements, as the transaction will see them."""
    return [line.strip() for line in ddl.split(";") if line.strip()]


def _both_slices() -> list[str]:
    return _statements(generate_floor_calibration_ddl()) + _statements(generate_lease_ddl())


class TestTheDdlDecisionRuleIsEnforcedMechanically:
    """Store reference §1.1. Each pin names the failure it prevents, because a
    clause is invisible in review and catastrophic in production.
    """

    def test_every_table_definition_is_IF_NOT_EXISTS(self) -> None:
        offenders = [
            statement
            for statement in _both_slices()
            if _DEFINE_TABLE.match(statement) and "IF NOT EXISTS" not in statement.upper()
        ]
        assert not offenders, (
            f"plain TABLE definitions must be `IF NOT EXISTS` (§1.1): {offenders}"
        )

    def test_every_field_definition_is_OVERWRITE(self) -> None:
        """#107, verbatim: ``IF NOT EXISTS`` on an existing field returns OK and
        silently keeps the OLD definition, so a widened ASSERT never reaches a
        live store. Only ``OVERWRITE`` migrates."""
        offenders = [
            statement
            for statement in _both_slices()
            if _DEFINE_FIELD.match(statement) and "OVERWRITE" not in statement.upper()
        ]
        assert not offenders, (
            f"every FIELD definition must be `DEFINE FIELD OVERWRITE` (#107): {offenders}"
        )

    def test_no_field_definition_uses_IF_NOT_EXISTS(self) -> None:
        """The same rule from the other side — a build that emitted BOTH clauses
        would pass the pin above."""
        offenders = [
            statement
            for statement in _both_slices()
            if _DEFINE_FIELD.match(statement) and "IF NOT EXISTS" in statement.upper()
        ]
        assert not offenders, offenders

    def test_every_index_definition_is_IF_NOT_EXISTS_and_never_OVERWRITE(self) -> None:
        """Flipping an index to ``OVERWRITE`` converts a silent no-op into a
        BOOT-TIME CRASH: a define REBUILDS, blocking, over every existing row."""
        for statement in _both_slices():
            if not _DEFINE_INDEX.match(statement):
                continue
            assert "IF NOT EXISTS" in statement.upper(), statement
            assert "OVERWRITE" not in statement.upper(), statement

    def test_the_word_ALTER_appears_in_no_statement(self) -> None:
        """§1.3: ``ALTER`` cannot CREATE a field, and ``ALTER … IF EXISTS`` on a
        missing one silently no-ops — adopting it re-commits #107 from the other
        side, on the fresh-DB path this slice runs on every new deployment."""
        offenders = [
            statement for statement in _both_slices() if re.search(r"\bALTER\b", statement, re.I)
        ]
        assert not offenders, offenders

    def test_this_slice_contains_neither_a_relation_table_nor_a_sequence(self) -> None:
        """⚠ A PINNED KNOWN BOUND (not a prohibition).

        If you are reading this because it went RED, you added a ``TYPE
        RELATION`` table or a ``DEFINE SEQUENCE`` to this slice. STOP and re-read
        store reference §1 first: for a RELATION table the TABLE clause INVERTS
        to ``OVERWRITE`` (``IF NOT EXISTS`` is a measured silent no-op on an
        existing edge table — #107's shape, invisible to every virgin-DB
        fixture), and a SEQUENCE carries #146's residual (a changed
        ``BATCH``/``START`` never migrates). Then update this pin deliberately,
        in a diff a reviewer can see.
        """
        for statement in _both_slices():
            assert "TYPE RELATION" not in statement.upper(), statement
            assert not re.search(r"\bDEFINE\s+SEQUENCE\b", statement, re.I), statement

    def test_each_generator_returns_the_house_terminated_shape(self) -> None:
        """Every other ``generate_*_ddl`` returns ``";\\n".join(...) + ";\\n"``.
        A slice that did not would break the caller's ``BEGIN … COMMIT`` wrap."""
        for ddl in (generate_floor_calibration_ddl(), generate_lease_ddl()):
            assert ddl.endswith(";\n")
            assert _statements(ddl)

    def test_the_generators_emit_something_for_every_planned_table(self) -> None:
        """CONTROL: a generator returning "" would make every clause pin above
        VACUOUSLY green — the signature failure of a mechanical gate.

        ⚠ IT DEMANDS FIELDS, NOT JUST TABLE NAMES (adversary F1c). Checking that
        three table names appear as substrings is satisfied by a slice emitting
        three ``DEFINE TABLE``s and ZERO ``DEFINE FIELD``s — and then
        ``test_every_field_definition_is_OVERWRITE`` is itself vacuously green,
        which is the control failing at the one job it has.
        """
        for table in (FLOOR_MEASUREMENT_TABLE, FLOOR_HEAD_TABLE, LEASE_TABLE):
            fields = [
                statement
                for statement in _both_slices()
                if _DEFINE_FIELD.match(statement) and f" ON {table} " in f"{statement} "
            ]
            assert fields, f"the slice for {table!r} emits no DEFINE FIELD at all"

    def test_the_new_slices_ROUTE_THROUGH_the_shared_ddl_emitters(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ONE IMPLEMENTATION, proven by MUTATION (adversary residual 8).

        The clause pins enforce today's POLICY, but nothing required the new
        slices to CALL ``_define_field``/``_define_table`` — so a future change
        to the shared emitter would silently not reach them. Perturb the shared
        emitter; the emitted DDL must move.
        """
        original = surreal_schema._define_field
        monkeypatch.setattr(
            surreal_schema,
            "_define_field",
            lambda *args, **kwargs: f"{original(*args, **kwargs)} COMMENT 'mutation-probe'",
        )
        assert "mutation-probe" in generate_floor_calibration_ddl(), (
            "the floor slice does not route through surreal_schema._define_field"
        )
        assert "mutation-probe" in generate_lease_ddl(), (
            "the lease slice does not route through surreal_schema._define_field"
        )


class TestTheClosedDomainsAreDerivedIntoTheDdl:
    """ONE IMPLEMENTATION, proven by MUTATION rather than by reading the source.

    The state and cause ASSERTs must be GENERATED FROM
    ``FLOOR_STATES`` / ``FLOOR_NON_ADOPTION_CAUSES``, not hand-typed beside
    them. A hand-typed list passes every "the assert mentions 'measured'" pin
    and drifts the first time a state is added — the exact prose-beside-code
    class this repo has shipped ten instances of.
    """

    def test_changing_the_state_tuple_changes_the_emitted_ASSERT(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        before = generate_floor_calibration_ddl()
        monkeypatch.setattr(
            surreal_schema, "FLOOR_STATES", (*FLOOR_STATES, "mutation_probe_state")
        )
        after = generate_floor_calibration_ddl()
        assert after != before, (
            "adding a state changed no emitted DDL — the state ASSERT is a hand-typed "
            "twin of FLOOR_STATES rather than a derivation of it"
        )
        assert "mutation_probe_state" in after

    def test_changing_the_cause_tuple_changes_the_emitted_ASSERT(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        before = generate_floor_calibration_ddl()
        monkeypatch.setattr(
            surreal_schema,
            "FLOOR_NON_ADOPTION_CAUSES",
            (*FLOOR_NON_ADOPTION_CAUSES, "mutation_probe_cause"),
        )
        after = generate_floor_calibration_ddl()
        assert after != before
        assert "mutation_probe_cause" in after

    def test_every_ruled_state_reaches_the_ddl(self) -> None:
        floor = generate_floor_calibration_ddl()
        missing = [state for state in FLOOR_STATES if state not in floor]
        assert not missing, missing


class TestTheRetiredStateNameIsGoneFromTheTree:
    """Repo rename law. F4.1 renamed ``stale_remeasuring`` to
    ``invalidated_remeasuring``; the sweep uses a BARE, anchor-free pattern
    because prose mentions carry no structural anchor, and three of four audited
    green-at-gate defects lived in exactly such surfaces.

    ⚠ **O4 — THE SWEEP'S OWN REACH WAS THE BLIND SPOT.** Until 2026-07-26 the
    scan globbed ``*.py`` only, so it could not see FOUR LIVE design-doc lines
    that still teach the retired name — including §7's state TABLE, which is the
    design of record 11-ii implements its served state projection from. An
    instrument that carries the very blind spot it exists to police is worse
    than no instrument, because its green is read as coverage.

    **The choice this fix wave made, stated rather than implied:** WIDEN the
    reach to the live design + plan-of-record docs, and carry the four known
    lines in a NAMED, DATED QUARANTINE with the edit each needs. That is the
    repo's PIN-THE-MISS pattern rather than a scope statement: the sweep is
    GREEN today, goes RED the moment a FIFTH live doc acquires the corpse, and
    goes RED AGAIN the day one of the four is fixed (its quarantine entry stops
    matching and must be deleted). A bound that is pinned is a bound the next
    engineer meets deliberately, and one that cannot be silently "fixed" either.

    **The two exclusions are reasoned, not convenient:**
    - ``docs/plans/v2/receipts/`` — ARCHIVE LAW. Those files are byte-faithful
      evidence of runs that happened; editing one is falsification, not a
      refactor, so they can never be swept.
    - ``2026-07-25-floor-calibration-addendum-F.md`` — the AMENDING doc. F4.1
      lives there; a rename doc must name what it retires or it cannot say what
      it did.
    """

    #: The live docs the sweep reaches. Receipts are excluded by archive law.
    SWEPT_DOC_GLOBS = ("docs/design/*.md", "docs/plans/v2/*.md", "docs/reference/*.md")

    #: Docs that legitimately name the corpse, with the reason.
    ALLOWED_DOCS = {
        "2026-07-25-floor-calibration-addendum-F.md": "the amending doc — F4.1 names what it retires",
    }

    #: ⚠ QUARANTINE — known-stale LIVE lines, dated 2026-07-26, found by the
    #: contract adversary. Each is (path, the exact edit owed). They are OUTSIDE
    #: this agent's writable set (docs belong to the lead), so they are pinned
    #: rather than fixed, and the pin below goes RED when one is repaired.
    KNOWN_STALE_DOC_LINES = {
        "docs/design/2026-07-24-floor-calibration.md": (
            "3 lines (≈336, ≈418, ≈659) teach the retired name as CURRENT behaviour; "
            "≈418 is §7's state TABLE row, which 11-ii reads to build its served "
            "state projection. Owed edit: rename to `invalidated_remeasuring` and "
            "re-predicate to F4.1's 'known-invalid', not 'ageing'."
        ),
    }

    @staticmethod
    def _hits(root: Path) -> list[str]:
        found: list[str] = []
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if RETIRED_STATE_NAME in line:
                    found.append(f"{path}:{number}: {line.strip()}")
        return found

    @classmethod
    def _doc_hits(cls) -> dict[str, list[str]]:
        """Every LIVE doc line carrying the corpse, keyed by repo-relative path."""
        by_path: dict[str, list[str]] = {}
        for glob in cls.SWEPT_DOC_GLOBS:
            for path in sorted(_REPO_ROOT.glob(glob)):
                if path.name in cls.ALLOWED_DOCS:
                    continue
                relative = path.relative_to(_REPO_ROOT).as_posix()
                for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    if RETIRED_STATE_NAME in line:
                        by_path.setdefault(relative, []).append(f"{relative}:{number}: {line.strip()}")
        return by_path

    def test_no_production_module_mentions_the_retired_name(self) -> None:
        assert not self._hits(_PACKAGE_ROOT), self._hits(_PACKAGE_ROOT)

    def test_the_only_test_mentions_are_the_two_pins_that_assert_its_ABSENCE(self) -> None:
        """"All remaining hits are X" is banned output — so every residual hit
        is named, individually, with its file and line."""
        allowed = {
            (_TESTS_ROOT / "test_floor_calibration_domain.py").name,
            (_TESTS_ROOT / "test_floor_calibration_schema.py").name,
        }
        residual = [
            hit for hit in self._hits(_TESTS_ROOT) if Path(hit.split(":")[0]).name not in allowed
        ]
        assert not residual, residual

    def test_the_doc_sweep_can_actually_see_a_hit(self) -> None:
        """CONTROL. A widened sweep that matched nothing would make the two pins
        below silently green — and this sweep's whole finding was that a scan
        can be blind to the surface that matters."""
        assert self._doc_hits(), (
            "the widened doc sweep found NOTHING — either every quarantined line "
            "was fixed (delete the quarantine) or the globs are broken"
        )

    def test_no_UNQUARANTINED_live_doc_teaches_the_retired_name(self) -> None:
        """The pin that fires on a FIFTH instance."""
        unquarantined = {
            path: hits
            for path, hits in self._doc_hits().items()
            if path not in self.KNOWN_STALE_DOC_LINES
        }
        assert not unquarantined, (
            f"live design/plan docs teach the RETIRED state name and are not "
            f"quarantined: {unquarantined}. Rename to 'invalidated_remeasuring' "
            f"(F4.1) or add a dated quarantine entry with the edit owed."
        )

    def test_every_QUARANTINED_doc_is_still_stale(self) -> None:
        """⚠ THE HALF THAT MAKES A QUARANTINE A PIN RATHER THAN A SHRUG.

        If a quarantined file no longer carries the corpse, somebody FIXED it —
        good — and the entry is now a lie about the tree. Delete it. A quarantine
        nobody prunes is how a bound gets silently inherited forever.
        """
        hits = self._doc_hits()
        repaired = [path for path in self.KNOWN_STALE_DOC_LINES if path not in hits]
        assert not repaired, (
            f"quarantined doc(s) no longer carry the retired name: {repaired}. "
            f"They were fixed — delete their KNOWN_STALE_DOC_LINES entries."
        )


class TestTheSchemaAppliesToTheLiveEngine:
    """The generated DDL against the real 3.2.1 engine."""

    async def test_the_floor_slice_creates_both_tables(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _ = admin_db
        await run(connection, generate_floor_calibration_ddl())
        info = await run(connection, "INFO FOR DB")
        tables = set(info.get("tables", {}))
        assert {FLOOR_MEASUREMENT_TABLE, FLOOR_HEAD_TABLE} <= tables

    async def test_the_lease_slice_creates_its_table(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _ = admin_db
        await run(connection, generate_lease_ddl())
        assert LEASE_TABLE in set((await run(connection, "INFO FOR DB")).get("tables", {}))

    async def test_both_slices_are_safely_re_appliable(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """``ensure_ready`` re-applies the DDL on EVERY boot. A statement that
        raises on re-application is a boot-time crash, not a style issue."""
        connection, _ = admin_db
        for _ in range(2):
            await run(connection, generate_floor_calibration_ddl())
            await run(connection, generate_lease_ddl())

    async def test_an_UNKNOWN_state_string_is_rejected_by_the_store(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """The ledger's own validation is the ergonomic layer; THIS is the
        backstop for any writer that skips it."""
        connection, _ = admin_db
        await run(connection, generate_floor_calibration_ddl())
        with pytest.raises(Exception):  # noqa: B017 - any engine rejection is the pin
            await run(
                connection,
                f"CREATE type::record('{FLOOR_MEASUREMENT_TABLE}', 'bad') "
                f"CONTENT {{ state: 'not_a_real_state' }}",
            )

    async def test_an_UNKNOWN_non_adoption_cause_is_rejected_by_the_store(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _ = admin_db
        await run(connection, generate_floor_calibration_ddl())
        with pytest.raises(Exception):  # noqa: B017
            await run(
                connection,
                f"CREATE type::record('{FLOOR_MEASUREMENT_TABLE}', 'bad2') "
                f"CONTENT {{ state: 'measured_not_adopted', "
                f"non_adoption_cause: 'not_a_real_cause' }}",
            )

    async def test_the_lease_holder_column_accepts_NONE(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """``release_if_held`` sets the holder to NONE (decision 23). A required
        (non-``option``) holder column makes graceful release impossible — and
        store reference §1.4 records that a required NEW field also poisons every
        existing row, which a DEFAULT does NOT rescue."""
        connection, _ = admin_db
        await run(connection, generate_lease_ddl())
        await run(
            connection,
            f"UPSERT type::record('{LEASE_TABLE}', '{LEASE_SINGLETON_ID}') "
            f"CONTENT {{ holder_identity: NONE, revision: 0, fence_epoch: 0 }}",
        )
        rows = await run(
            connection,
            f"SELECT holder_identity, revision, fence_epoch FROM "
            f"type::record('{LEASE_TABLE}', '{LEASE_SINGLETON_ID}')",
        )
        assert rows and rows[0]["holder_identity"] is None

    async def test_the_lease_record_columns_accept_the_LIBRARYS_STRING_shapes(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """⚠ MEASURED, and it is a trap a ``datetime`` column walks straight
        into: ``kubernetes.leaderelection`` writes
        ``LeaderElectionRecord(identity, str(lease_duration), str(now), str(now))``
        — all four fields are STRINGS, and the times are NAIVE local datetimes
        (``datetime.datetime.fromtimestamp(time.time())``). A ``datetime``-typed
        ``renew_time`` rejects every renewal the library ever makes.
        """
        connection, _ = admin_db
        await run(connection, generate_lease_ddl())
        await run(
            connection,
            f"UPSERT type::record('{LEASE_TABLE}', '{LEASE_SINGLETON_ID}') "
            f"CONTENT {{ holder_identity: 'pod-a', lease_duration: '15', "
            f"acquire_time: '2026-07-26 15:18:30.327624', "
            f"renew_time: '2026-07-26 15:18:30.327665', revision: 0, fence_epoch: 0 }}",
        )
        rows = await run(
            connection,
            f"SELECT lease_duration, acquire_time, renew_time FROM "
            f"type::record('{LEASE_TABLE}', '{LEASE_SINGLETON_ID}')",
        )
        assert rows and rows[0]["lease_duration"] == "15"


class TestTheSchemaMigratesAnEXISTINGStore:
    """⚠ THE ONE PIN A VIRGIN-DB SUITE STRUCTURALLY CANNOT HAVE (§1.6).

    Every fixture in this repo mints a throwaway database, so no test had ever
    applied a schema change to an EXISTING store — which is why #107 passed
    1040 tests, a cold audit and a contract-adversary, and was caught only by
    the deploy smoke, after the outage.

    Shape (mirrors ``TestSchemaMigrationAgainstAnExistingStore``): apply a
    NARROWER definition -> insert a row the CURRENT schema allows but the narrow
    one forbids -> re-apply the real DDL -> assert the current constraint took
    effect AND the pre-existing row survived.
    """

    async def test_a_narrowed_state_assert_MIGRATES_back_to_the_full_set(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _ = admin_db
        await run(connection, generate_floor_calibration_ddl())

        # Stand in for an OLDER deployed schema: a state set missing one member.
        narrowed = ", ".join(f"'{state}'" for state in FLOOR_STATES if state != "disabled")
        await run(
            connection,
            f"DEFINE FIELD OVERWRITE state ON {FLOOR_MEASUREMENT_TABLE} "
            f"TYPE string ASSERT $value IN [{narrowed}]",
        )
        await run(
            connection,
            f"CREATE type::record('{FLOOR_MEASUREMENT_TABLE}', 'legacy') "
            f"CONTENT {{ state: 'measured' }}",
        )
        with pytest.raises(Exception):  # noqa: B017 - the narrow schema is really in force
            await run(
                connection,
                f"CREATE type::record('{FLOOR_MEASUREMENT_TABLE}', 'blocked') "
                f"CONTENT {{ state: 'disabled' }}",
            )

        # Re-apply the REAL slice, exactly as ``ensure_ready`` does at boot.
        await run(connection, generate_floor_calibration_ddl())

        # The widened definition LANDED (this is the #107 assertion) …
        await run(
            connection,
            f"CREATE type::record('{FLOOR_MEASUREMENT_TABLE}', 'now_allowed') "
            f"CONTENT {{ state: 'disabled' }}",
        )
        # … and the pre-existing row is intact, not rewritten and not dropped.
        rows = await run(
            connection,
            f"SELECT state FROM type::record('{FLOOR_MEASUREMENT_TABLE}', 'legacy')",
        )
        assert rows and rows[0]["state"] == "measured"


    async def test_the_LEASE_slice_migrates_a_NARROWED_field_on_an_existing_store(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """⚠ M14 — the lease slice had NO live migration leg at all.

        The clause pins give the rule ∀ reach over both slices (they caught a
        lease slice emitting ``DEFINE FIELD IF NOT EXISTS``), but a clause pin
        reads TEXT; only a dirty store proves the text does what it claims. And
        the lease row is the one row a long-lived deployment NEVER recreates —
        every fixture in this repo mints a virgin database, which is structurally
        why #107 passed 1040 tests and a cold audit.

        ``holder_identity`` is the field under test on purpose: decision 23
        requires it to accept NONE, so a narrowing that forbade NONE would break
        ``release_if_held`` on exactly the stores that already have a lease row.
        """
        connection, _ = admin_db
        await run(connection, generate_lease_ddl())

        # Stand in for an OLDER deployed schema: a REQUIRED holder column.
        await run(
            connection,
            f"DEFINE FIELD OVERWRITE holder_identity ON {LEASE_TABLE} TYPE string",
        )
        await run(
            connection,
            f"UPSERT type::record('{LEASE_TABLE}', '{LEASE_SINGLETON_ID}') "
            f"CONTENT {{ holder_identity: 'pod-legacy', revision: 0, fence_epoch: 0 }}",
        )
        with pytest.raises(Exception):  # noqa: B017 - the narrow schema is really in force
            await run(
                connection,
                f"UPDATE type::record('{LEASE_TABLE}', '{LEASE_SINGLETON_ID}') "
                f"SET holder_identity = NONE",
            )

        await run(connection, generate_lease_ddl())  # what ensure_ready does at boot

        # The widened definition LANDED …
        await run(
            connection,
            f"UPDATE type::record('{LEASE_TABLE}', '{LEASE_SINGLETON_ID}') "
            f"SET holder_identity = NONE",
        )
        # … and the pre-existing row survived rather than being recreated.
        rows = await run(
            connection,
            f"SELECT revision, fence_epoch FROM "
            f"type::record('{LEASE_TABLE}', '{LEASE_SINGLETON_ID}')",
        )
        assert rows and rows[0]["revision"] == 0

    async def test_the_FLOOR_HEAD_slice_migrates_a_NARROWED_field_on_an_existing_store(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """⚠ M14, second table. The head row is the OTHER row a live deployment
        never recreates — it is the adopted pointer, minted once per identity and
        UPSERTed forever after."""
        connection, _ = admin_db
        await run(connection, generate_floor_calibration_ddl())

        narrowed_scope = "'pooled'"
        await run(
            connection,
            f"DEFINE FIELD OVERWRITE scope ON {FLOOR_HEAD_TABLE} "
            f"TYPE string ASSERT $value IN [{narrowed_scope}]",
        )
        await run(
            connection,
            f"CREATE type::record('{FLOOR_HEAD_TABLE}', 'legacy_head') "
            f"CONTENT {{ scope: 'pooled' }}",
        )
        with pytest.raises(Exception):  # noqa: B017
            await run(
                connection,
                f"CREATE type::record('{FLOOR_HEAD_TABLE}', 'blocked_head') "
                f"CONTENT {{ scope: 'tier:lore' }}",
            )

        await run(connection, generate_floor_calibration_ddl())

        await run(
            connection,
            f"CREATE type::record('{FLOOR_HEAD_TABLE}', 'now_allowed_head') "
            f"CONTENT {{ scope: 'tier:lore' }}",
        )
        rows = await run(
            connection,
            f"SELECT scope FROM type::record('{FLOOR_HEAD_TABLE}', 'legacy_head')",
        )
        assert rows and rows[0]["scope"] == "pooled"


class TestNoMultiStatementDdlRidesABareQuery:
    """Store reference §3: the SDK's ``query()`` validates statement[0] ONLY, so
    a multi-statement DDL string sent through it can fail its third statement,
    roll the whole thing back, and raise NOTHING. This bit us as silent partial
    SCHEMA in all three ``ensure_ready`` paths.

    Keyed on the SAFE set: the two new modules may call ``execute_transaction``
    and ``run_query``; what they may not do is hand a multi-statement string to a
    connection directly.
    """

    @staticmethod
    def _module_sources() -> dict[str, str]:
        import loremaster.floor_calibration.store as floor_store  # noqa: PLC0415
        import loremaster.store.lease as lease_module  # noqa: PLC0415

        sources: dict[str, str] = {}
        for module in (floor_store, lease_module):
            path = module.__file__
            assert path is not None, f"{module.__name__} has no __file__ to scan"
            sources[module.__name__] = Path(path).read_text(encoding="utf-8")
        return sources

    def test_neither_module_calls_query_on_a_connection_directly(self) -> None:
        for name, source in self._module_sources().items():
            calls = [
                node
                for node in ast.walk(ast.parse(source))
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"query", "query_raw"}
                and not (isinstance(node.func.value, ast.Name) and node.func.value.id == "self")
            ]
            assert not calls, (
                f"{name} calls the SDK's query()/query_raw() directly; every statement "
                f"must ride `_txn.run_query` or `_txn.execute_transaction`"
            )

    def test_the_ddl_scan_can_actually_see_a_call(self) -> None:
        """CONTROL on the AST walk above — an analyser that matched nothing would
        make the pin silently green against any build."""
        source = "async def f(c):\n    await c.query('SELECT 1')\n"
        found: list[Any] = [
            node
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "query"
        ]
        assert len(found) == 1
