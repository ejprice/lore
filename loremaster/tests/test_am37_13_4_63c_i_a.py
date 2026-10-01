"""Packet 63c-i-a, amendment 37 §13.4 (``86d18ba``) + erratum §13.4.1 (``175077a``) — test side.

Written by ``fixup-tests-63c-i-a-2`` (round 7, 2026-10-01) over the fix6 final candidate (patch md5
``30a13c8a``).
"RED at 30a13c8a" below is scoped to that build.

§13.3 item 4 moved the report validator INTO ``report_unmigrated_governed_rows`` against the MIGRATE leg
set, so the
S2 restore's read-back (which reads every governed table — incl. ``finding`` / ``task``) raised. Ruling:
two verbs,
two DERIVED domains — REPORT = the governed set ``governed.governed_tables()`` (derived in PRODUCTION from
the DDL
generators), MIGRATE = the leg set ``_MIGRATE_VALID_TABLES`` (a strict subset); ONE validator;
``SliceDeriver``
(in ``scripts/``, never packaged) CONSUMES the production accessor — no production module may import
``scripts``.
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path
from typing import Any

import loremaster.governed as governed_module
import pytest
from _enforced_relations_scaffold import MIGRATION_DIM, emitted_schema_ddl
from _governed_contract import apply_ddl, store_handle
from _surreal_harness import connect_admin, drop_database, make_env, unique_database

from loremaster import principals as p_module

_PACKAGE = Path(p_module.__file__).resolve().parent
_REPOSITORY = _PACKAGE.parent.parent
_SCRIPTS = _REPOSITORY / "scripts"
_FORBIDDEN_IMPORT_ROOTS = frozenset({"scripts", "restore_prod_dump"})
_OUTSIDE_BOTH_DOMAINS = "principal"


def _governed_tables_accessor() -> Any:
    accessor = getattr(governed_module, "governed_tables", None)
    if accessor is None:
        pytest.fail(
            "am-37 §13.4.1: `loremaster.governed.governed_tables()` (production, derived) does not exist"
        )
    return accessor


def _report_domain() -> list[str]:
    """``governed_tables()`` at COLLECTION, sorted — a missing accessor reds BY NAME, never shrinks to
    nothing."""
    accessor = getattr(governed_module, "governed_tables", None)
    if accessor is None:
        return ["<governed.governed_tables() does not exist>"]
    try:
        return sorted(accessor())
    except Exception as error:  # noqa: BLE001 - a broken derivation must RED by name
        return [f"<governed_tables() raised {error!r}>"]


def _restore_module() -> Any:
    """``scripts/restore_prod_dump.py`` (not a workspace member) — imported by path, test side only."""
    if str(_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS))
    return importlib.import_module("restore_prod_dump")


async def _minted_full_ddl_world() -> Any:
    """A minted TEST-store database (``:18000``) carrying the EMITTED schema DDL — every governed table
    defined."""
    env = make_env(database=unique_database(), dim=MIGRATION_DIM)
    connection = await connect_admin(env)
    await apply_ddl(connection, emitted_schema_ddl(), url=env.url)
    return env, connection


# =========================================================================== #
# 1 + 2 — the REPORT domain is the governed set; MIGRATE ⊆ REPORT
# =========================================================================== #


class TestTheReportDomainIsTheGovernedSet:
    @pytest.mark.parametrize("table", _report_domain())
    async def test_the_report_count_accepts_every_governed_table(self, table: str) -> None:
        """RED at 30a13c8a: no ``governed_tables()``; and the report refuses ``finding`` / ``task``."""
        assert not table.startswith("<"), table
        env, connection = await _minted_full_ddl_world()
        try:
            handle, _calls = store_handle(connection, url=env.url)
            count = await governed_module.report_unmigrated_governed_rows(handle, table)
            assert isinstance(count, int) and count >= 0, (table, count)
        finally:
            await connection.close()
            await drop_database(env)

    async def test_CONTROL_a_table_outside_both_domains_is_refused_with_zero_io(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from loremaster.store._txn import StoreHandle  # noqa: PLC0415

        calls: list[str] = []

        async def spy(**kwargs: Any) -> Any:
            calls.append(str(kwargs.get("statement")))
            return [{"count": 0}]

        async def never(*_args: Any) -> Any:
            calls.append("connection")
            raise AssertionError("no connection for an invalid table")

        monkeypatch.setattr(governed_module, "run_query", spy)
        with pytest.raises(Exception) as refused:  # noqa: PT011 - the validator's class is the builder's
            await governed_module.report_unmigrated_governed_rows(
                StoreHandle(acquire=never, drop=never, url="ws://unit"), _OUTSIDE_BOTH_DOMAINS
            )
        assert calls == [], calls
        assert _OUTSIDE_BOTH_DOMAINS in str(refused.value), str(refused.value)

    def test_the_control_sample_lies_outside_both_domains(self) -> None:
        domain = set(_governed_tables_accessor()())
        assert _OUTSIDE_BOTH_DOMAINS not in domain | set(p_module._MIGRATE_VALID_TABLES)  # noqa: SLF001

    def test_the_migrate_leg_set_is_contained_in_the_report_domain(self) -> None:
        """§13.4 pin 2: a leg for a non-governed table is a defect."""
        missing = set(p_module._MIGRATE_VALID_TABLES) - set(_governed_tables_accessor()())  # noqa: SLF001
        assert not missing, f"migrate legs over non-governed tables: {sorted(missing)}"


# =========================================================================== #
# 3 — the S2 restore read-back over every governed table
# =========================================================================== #


class TestTheRestoreReadBackServesEveryGovernedTable:
    async def test_read_back_completes_with_one_scope_none_count_per_governed_table(self) -> None:
        """RED at 30a13c8a: the read-back raises on ``finding`` / ``task`` (the §13.3 item 4 regression). The
        ``unmigrated`` map is exactly what feeds the receipt's ``scope NONE`` column — one entry per table."""
        restore = _restore_module()
        governed = [
            table.name for table in restore.SliceDeriver().governed_slice().tables if table.governed_node
        ]
        env, connection = await _minted_full_ddl_world()
        await connection.close()
        try:
            counts, unmigrated = await restore._read_back(
                restore.StoreCredentials.for_test_store(), env.database, governed, governed
            )
        finally:
            await drop_database(env)
        assert set(unmigrated) == set(governed), (sorted(unmigrated), sorted(governed))
        assert all(isinstance(value, int) for value in unmigrated.values()), unmigrated
        assert set(counts) == set(governed), sorted(counts)


# =========================================================================== #
# §13.4.1 — ONE source of truth in production; scripts/ consumes it, never the reverse
# =========================================================================== #


class TestTheSliceDeriverConsumesTheProductionAccessor:
    def test_the_slice_deriver_governed_nodes_equal_governed_tables(self) -> None:
        """RED at 30a13c8a (no accessor). The transitional receipt + the guard against re-deriving in the
        script."""
        restore = _restore_module()
        nodes = {
            table.name for table in restore.SliceDeriver().governed_slice().tables if table.governed_node
        }
        assert nodes == set(_governed_tables_accessor()()), (
            sorted(nodes),
            sorted(_governed_tables_accessor()()),
        )


def _forbidden_imports(tree: ast.AST) -> list[tuple[int, str]]:
    """``(lineno, name)`` ∀ ``Import`` / ``ImportFrom`` at ANY depth whose module path names ``scripts`` or
    ``restore_prod_dump`` as ANY dotted segment (bare-name match; any alias)."""
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Import | ast.ImportFrom):
            continue
        names = (
            [alias.name for alias in node.names]
            if isinstance(node, ast.Import)
            else [node.module or ""] + [f"{node.module or ''}.{alias.name}" for alias in node.names]
        )
        found.extend((node.lineno, name) for name in names if _FORBIDDEN_IMPORT_ROOTS & set(name.split(".")))
    return found


def _production_modules() -> list[str]:
    return sorted(str(path.relative_to(_PACKAGE)) for path in _PACKAGE.rglob("*.py"))


class TestNoProductionModuleImportsScripts:
    @pytest.mark.parametrize("module", _production_modules())
    def test_the_module_never_imports_scripts(self, module: str) -> None:
        """§13.4.1: ``scripts/`` is not packaged — a production import of it is an ``ImportError`` in the
        image
        only (#131/#139). GREEN at 30a13c8a; reds BY MODULE the day one appears."""
        tree = ast.parse((_PACKAGE / module).read_text(encoding="utf-8"))
        assert not _forbidden_imports(tree), (
            f"{module}: production imports scripts/: {_forbidden_imports(tree)}"
        )

    def test_POSITIVE_CONTROL_a_function_local_import_is_caught(self) -> None:
        synthetic = ast.parse(
            "def governed_tables():\n"
            "    from scripts.restore_prod_dump import SliceDeriver\n"
            "    import scripts.restore_prod_dump as rpd\n"
            "    from restore_prod_dump import SliceDeriver as S\n"
            "    return set()\n"
        )
        # every one of the three forbidden statements is caught (from X import Y names both X and X.Y)
        caught = {line for line, _name in _forbidden_imports(synthetic)}
        assert caught == {2, 3, 4}, _forbidden_imports(synthetic)

    def test_the_module_population_is_not_vacuous(self) -> None:
        assert "governed.py" in _production_modules() and len(_production_modules()) >= 20


# =========================================================================== #
# §13.4.2 (``d0502c0``) — governed set = DDL-derived ∪ a DECLARED pending set that SELF-DESTRUCTS
# =========================================================================== #


def _pending_entries() -> Any:
    entries = getattr(governed_module, "PENDING_GOVERNED_TABLES", None)
    if entries is None:
        pytest.fail("am-37 §13.4.2: `loremaster.governed.PENDING_GOVERNED_TABLES` does not exist")
    return entries


def _ddl_governed_tables() -> frozenset[str]:
    accessor = getattr(governed_module, "ddl_governed_tables", None)
    if accessor is None:
        pytest.fail("am-37 §13.4.2: `loremaster.governed.ddl_governed_tables()` does not exist")
    if hasattr(accessor, "cache_clear"):
        accessor.cache_clear()
    return frozenset(accessor())


def _pending_population() -> list[str]:
    entries = getattr(governed_module, "PENDING_GOVERNED_TABLES", None)
    return sorted(entries) if entries is not None else ["<governed.PENDING_GOVERNED_TABLES does not exist>"]


_TRIO = ("owner_principal", "owner_agent", "scope")


class TestThePendingSetSelfDestructs:
    @pytest.mark.parametrize("member", _pending_population())
    def test_a_pending_table_has_no_ddl_triple_yet(self, member: str) -> None:
        """RED at 30a13c8a (no package set). The day a packet lands a pending table's triple, this reds BY
        MEMBER until the entry is deleted — the declared set can only shrink (§13.4.2 SELF-DESTRUCT)."""
        assert not member.startswith("<"), member
        assert member not in _ddl_governed_tables(), (
            f"`{member}` now carries the governed triple in its DDL — "
            "delete its PENDING_GOVERNED_TABLES entry"
        )

    def test_CONTROL_a_synthetic_generator_defining_the_triple_on_a_pending_name_is_seen(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The pin can fire: a ``generate_*_ddl`` defining the triple on a pending name joins the
        DDL-derived set
        (so the derivation reads the GENERATORS, not a list)."""
        from loremaster.store import surreal_schema  # noqa: PLC0415

        pick = sorted(_pending_entries())[0]

        def generate_r7b_selfdestruct_probe_ddl() -> str:
            return "\n".join(
                f"DEFINE FIELD {column} ON TABLE {pick} TYPE option<string>;" for column in _TRIO
            )

        monkeypatch.setattr(
            surreal_schema,
            "generate_r7b_selfdestruct_probe_ddl",
            generate_r7b_selfdestruct_probe_ddl,
            raising=False,
        )
        try:
            assert pick in _ddl_governed_tables(), f"a synthetic triple on `{pick}` was not derived"
        finally:
            monkeypatch.undo()
            _ddl_governed_tables()

    def test_the_report_domain_is_exactly_ddl_plus_pending(self) -> None:
        union = _ddl_governed_tables() | frozenset(_pending_entries())
        assert set(_governed_tables_accessor()()) == union, (
            sorted(_governed_tables_accessor()()),
            sorted(union),
        )

    def test_the_migrate_legs_are_ddl_derived_tables(self) -> None:
        """§13.4.2 tightened containment, READING (i) (the ruled rationale, "a LEG for a PENDING table is
        a defect —
        its columns do not exist"): the DERIVED leg set (test_preboot…::_LEGS, the tables a migrate leg
        actually writes) ⊆ the DDL-derived set. NOT the literal _MIGRATE_VALID_TABLES ⊆ ddl: that set also
        holds brief, which has no leg (the verb refuses it as not-yet-migrated) and no triple — the literal
        form reds on every correct build (flagged in REPORT-fixup-tests-63c-i-a-2 §ROUND 7b, R7b-1)."""
        import test_preboot_schema_precondition_63c_13d as preboot  # noqa: PLC0415

        missing = set(preboot._LEGS) - _ddl_governed_tables()  # noqa: SLF001
        assert not missing, f"migrate legs over tables without the DDL triple: {sorted(missing)}"



class TestThePendingEntriesAreDeclaredHonestly:
    @pytest.mark.parametrize("member", _pending_population())
    def test_each_entry_carries_a_reason_and_an_owning_packet(self, member: str) -> None:
        assert not member.startswith("<"), member
        entry = _pending_entries()[member]
        for field in ("reason", "owning_packet"):
            value = getattr(entry, field, None)
            assert isinstance(value, str) and value.strip(), (
                f"`{member}`: `{field}` must be a non-blank str: {entry!r}"
            )

    def test_the_restore_script_consumes_the_package_set(self) -> None:
        """RED at 30a13c8a: the script carries its own ``PENDING_GOVERNED_TABLES``. No module-level
        definition in
        the script (AST), and any name it exposes IS the package's object (identity)."""
        tree = ast.parse((_SCRIPTS / "restore_prod_dump.py").read_text(encoding="utf-8"))
        local = [
            node.lineno
            for node in tree.body
            if isinstance(node, ast.Assign | ast.AnnAssign)
            and any(
                isinstance(target, ast.Name) and target.id == "PENDING_GOVERNED_TABLES"
                for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
            )
        ]
        assert not local, (
            f"scripts/restore_prod_dump.py defines its own PENDING_GOVERNED_TABLES at line(s) {local}"
        )
        restore = _restore_module()
        if hasattr(restore, "PENDING_GOVERNED_TABLES"):
            assert restore.PENDING_GOVERNED_TABLES is _pending_entries()


async def _seed_pending_rows(env: Any) -> None:
    """One legacy row each in ``finding`` / ``task`` (no governed column exists, so every row reads scope
    NONE)."""
    from datetime import UTC, datetime  # noqa: PLC0415

    from _governed_contract_64 import seed_finding_legacy  # noqa: PLC0415
    from _surreal_harness import run  # noqa: PLC0415

    connection = await connect_admin(env)
    try:
        await seed_finding_legacy(connection, row_id="r7b_pending", number=1)
        await run(
            connection,
            "CREATE type::record('task', 'r7b_pending') CONTENT $content",
            {
                "content": {
                    "subject": "r7b pending probe",
                    "description": "a legacy task row",
                    "status": "open",
                    "provenance": {},
                    "created_at": datetime.now(UTC),
                }
            },
        )
    finally:
        await connection.close()


class TestTheReadBackServesThePendingRemedy:
    async def test_the_pending_tables_report_their_packet_never_a_migrate_verb(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """§13.4.2 rider, end to end through the REAL ``_read_back``: ``finding`` / ``task`` each render
        the remedy
        derived from their entry (*"has no governed columns yet (<reason>; packet <N>)"*), never
        `migrate-governed`."""
        import logging  # noqa: PLC0415

        restore = _restore_module()
        governed = [
            table.name for table in restore.SliceDeriver().governed_slice().tables if table.governed_node
        ]
        env, connection = await _minted_full_ddl_world()
        await connection.close()
        await _seed_pending_rows(env)
        try:
            with caplog.at_level(logging.WARNING, logger=governed_module.__name__):
                _counts, unmigrated = await restore._read_back(
                    restore.StoreCredentials.for_test_store(), env.database, governed, governed
                )
        finally:
            await drop_database(env)
        entries = _pending_entries()
        for table in ("finding", "task"):
            assert unmigrated.get(table, 0) >= 1, (table, unmigrated)
            lines = [
                r.getMessage()
                for r in caplog.records
                if f" {table} row(s)" in r.getMessage() or f"`{table}`" in r.getMessage()
            ]
            assert any(
                "no governed columns yet" in line and f"packet {entries[table].owning_packet}" in line
                for line in lines
            ), f"{table}: the pending remedy line is missing: {lines!r}"
            assert not any(f"migrate-governed --table {table}" in line for line in lines), lines
