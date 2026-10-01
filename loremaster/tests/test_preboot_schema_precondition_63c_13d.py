"""Contract — packet 63c-i-a, amendment 37 §13 class D (D-2): the PRE-BOOT schema teaching precondition.

Spec: ``docs/design/2026-09-29-packet63c-amendment-37.md`` §13 "D. The pre-boot schema teaching
precondition". Authored by ``sub-63c13-d-1`` (Opus contract author; TESTS ONLY). Live TEST store
``ws://127.0.0.1:18000`` via ``_surreal_harness`` (NEVER :18500); every minted database is reaped.

PROPERTY (§13 D): *every precondition a leg's write needs is measured and TAUGHT before the first write.*
A dump restored with no server boot has the governed TABLE (``INFO FOR DB`` passes) but not the governed
COLUMNS, so a leg's backfill ``UPDATE`` is an opaque engine rejection (and, before it, the leg's
idempotent project-keep mint already wrote). The #107 fixture law: every other migrate pin mints a
full-DDL virgin DB, so none can see this state — these pins build the DIRTY store by construction:
full DDL, then ``REMOVE FIELD <col> ON TABLE <table>`` for ONE column.

DOMAIN (derived, drift-proof, §13 D): ∀ migrate leg × the columns that leg's OWN backfill ``UPDATE … SET``
assigns. The legs are DERIVED from production, not listed: a leg is a function in ``principals.py`` that
opens ``governed_exempt("migrate-governed", statement=<name>)`` (the production marker of a migrate
write — the F5 exemption whose golden IS the executed statement); ``<name>`` is resolved to its
function-local assignment BY AST and evaluated against the module's own globals, so the parsed text is
the SAME source the write executes (§1.9 item 1 keeps that statement function-local, so AST is the only
route to it — said out loud per the brief). The ``SET`` columns are parsed from that text by a
paren-depth-aware splitter; a COMPLETENESS leg diffs them against an independent bare-pattern read.

Store behaviour these pins rest on — PROBED 2026-09-30 on the 3.2.x test store by this author (the store
reference ``docs/reference/surrealdb-31-capabilities.md`` has no REMOVE FIELD row), instrument pasted in
the author's report: ``REMOVE FIELD scope ON TABLE memory`` answers ``None``; ``INFO FOR TABLE memory``
then omits ``scope`` from ``fields`` while keeping its siblings; ``INFO FOR TABLE <undefined>`` answers
EMPTY maps (no error); an ``UPDATE memory SET scope = … WHERE scope IS NONE`` over ZERO rows answers
``[]`` silently and over ONE row RAISES ``Found field 'scope', but no such field exists`` (SCHEMAFULL).
Hence every dirty case SEEDS one legacy row, so the base's failure is a real rejection, not a silent no-op.

The refusal text (§13 D, verbatim shape): *"the `<table>` table has no `<c1>, <c2>` column(s) — this
store's schema predates the governed columns; boot the new image once (its DDL defines them), then re-run
migrate-governed"*. Assertions use ``in`` over stderr (another agent adds a stderr log handler + cause
lines to the CLI, §13 A — no exact-bytes or line-count pin here). The column list is parsed out of the
sentence. am-37 §13.1 item 3 (commit ``d6cdd0b``) RULED the D-fork: ONE backtick span PER column
(`` `owner_principal`, `scope` ``) — each column is an identifier; one span around a comma list would teach a
single false identifier. The parser REQUIRES that form.
"""

from __future__ import annotations

import ast
import asyncio
import inspect
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
import yaml
from _governed_contract import (
    apply_ddl,
    build_principal_and_keep_stores,
    seed_agent_governed,
    seed_agent_legacy,
    seed_memory_legacy,
    seed_message_legacy,
    store_handle,
)
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    run,
    surreal_password,
    surreal_url,
    surreal_user,
    unique_database,
)
from loremaster.keeps import KeepStore
from loremaster.store import _txn, surreal_schema

from loremaster import principals

_USER_ENV = "LORE_PREBOOT_13D_SURREAL_USER"
_PASS_ENV = "LORE_PREBOOT_13D_SURREAL_PASS"
_ANTHROPIC_ENV = "LORE_PREBOOT_13D_ANTHROPIC"
_OPERATOR_EMAIL = "operator@example.com"
_SENDER_ID = "sender_13d"
_FIXTURE_SCOPE = "keep:fixture_13d"
_MIGRATE_MARKER = "migrate-governed"
_WRITE_VERBS = ("UPDATE", "CREATE", "INSERT", "UPSERT", "DELETE", "RELATE", "DEFINE", "REMOVE", "ALTER")
_REFUSAL_COLUMNS = re.compile(r"the `(?P<table>\w+)` table has no (?P<cols>.+?) column\(s\)")
_REFUSAL_TEACHING = "this store's schema predates the governed columns"


# --------------------------------------------------------------------------- #
# The DERIVED domain: migrate legs × their backfill statement's SET columns.
# --------------------------------------------------------------------------- #


def _is_migrate_exempt(call: ast.expr) -> ast.Name | None:
    """``governed_exempt("migrate-governed", statement=<Name>)`` → the ``<Name>`` node, else ``None``."""
    if not isinstance(call, ast.Call):
        return None
    func = call.func
    name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
    if name != "governed_exempt":
        return None
    if not (call.args and isinstance(call.args[0], ast.Constant) and call.args[0].value == _MIGRATE_MARKER):
        return None
    for keyword in call.keywords:
        if keyword.arg == "statement" and isinstance(keyword.value, ast.Name):
            return keyword.value
    return None


def _render_statement(node: ast.expr, namespace: dict[str, Any]) -> str:
    """The statement's text from its OWN literal parts — a str Constant, an f-string's parts, ``+``
    concatenation, or a bare module-global ``str`` Name — read by ``ast``, NEVER evaluated. am-37 §9 / 58
    am-9 §3: the tree holds exactly ONE resolver (the one ``_catch_sites`` owns); an evaluator of statement
    expressions here would be a second one by SHAPE (``test_retry_seam.py::…test_am34_5…``). An unsupported
    part fails LOUD (extend this reader), never a silent mis-render."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        rendered: list[str] = []
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                rendered.append(part.value)
            elif isinstance(part, ast.FormattedValue) and part.conversion == -1 and part.format_spec is None:
                rendered.append(_render_statement(part.value, namespace))
            else:
                raise AssertionError(f"unsupported f-string part in a leg statement: {ast.dump(part)}")
        return "".join(rendered)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _render_statement(node.left, namespace) + _render_statement(node.right, namespace)
    if isinstance(node, ast.Name):
        value = namespace.get(node.id)
        assert isinstance(value, str), f"`{node.id}` is not a module-global str constant: {value!r}"
        return value
    raise AssertionError(f"unsupported leg-statement node (extend the reader, never eval): {ast.dump(node)}")


def _leg_statements() -> dict[str, tuple[str, str]]:
    """``{table: (leg function name, backfill statement text)}`` — DERIVED by AST of ``principals.py``.

    A leg = a function holding a ``with governed_exempt("migrate-governed", statement=<name>)``; the
    statement text is ``<name>``'s function-local assignment, evaluated against the module globals (the
    same f-string the write executes). The table is the statement's ``UPDATE <table>`` target."""
    source_path = Path(inspect.getsourcefile(principals) or "")
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    module_globals = vars(principals)
    legs: dict[str, tuple[str, str]] = {}
    for function in ast.walk(tree):
        if not isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for node in ast.walk(function):
            if not isinstance(node, ast.With | ast.AsyncWith):
                continue
            for item in node.items:
                bound = _is_migrate_exempt(item.context_expr)
                if bound is None:
                    continue
                assignments = [
                    assign
                    for assign in ast.walk(function)
                    if isinstance(assign, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == bound.id for t in assign.targets)
                ]
                assert len(assignments) == 1, (
                    f"{function.name}: the migrate-governed exemption's statement `{bound.id}` must have "
                    f"exactly ONE function-local assignment (§1.9 item 1), found {len(assignments)}"
                )
                text = _render_statement(assignments[0].value, module_globals)
                match = re.match(r"\s*UPDATE\s+(\w+)\s+SET\s", text)
                assert match, (
                    f"{function.name}: the migrate statement is not an `UPDATE <table> SET`: {text!r}"
                )
                table = match.group(1)
                assert table not in legs, (
                    f"two migrate legs write `{table}`: {legs[table][0]}, {function.name}"
                )
                legs[table] = (function.name, text)
    return legs


def _set_clause(statement: str) -> str:
    """The text between the top-level ``SET`` and the top-level ``WHERE`` (or end of statement)."""
    after_set = re.split(r"\sSET\s", statement, maxsplit=1)[1]
    return re.split(r"\sWHERE\s", after_set, maxsplit=1)[0]


def _split_top_level(clause: str) -> list[str]:
    """Split ``clause`` on commas at paren depth 0 (``type::record('principal', $owner)`` stays whole)."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for char in clause:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return parts


def _set_columns(statement: str) -> tuple[str, ...]:
    """The columns the statement's ``SET`` assigns, in statement order (the depth-aware parser)."""
    columns: list[str] = []
    for assignment in _split_top_level(_set_clause(statement)):
        column, separator, _value = assignment.partition("=")
        assert separator, f"a SET item without `=`: {assignment!r} in {statement!r}"
        columns.append(column.strip())
    return tuple(columns)


def _bare_pattern_columns(statement: str) -> frozenset[str]:
    """An INDEPENDENT read: every ``<identifier> =`` (not ``==``) before the first ``WHERE``."""
    head = statement.split(" WHERE ", 1)[0]
    return frozenset(re.findall(r"\b([A-Za-z_]\w*)\s*=(?!=)", head))


_LEGS = _leg_statements()
_LEG_COLUMN_CASES = [
    pytest.param(table, column, id=f"{table}-{column}")
    for table, (_leg, statement) in sorted(_LEGS.items())
    for column in _set_columns(statement)
]
_LEG_TABLES = [pytest.param(table, id=table) for table in sorted(_LEGS)]


class TestTheDerivedDomainIsComplete:
    """§13 D completeness leg: the domain is derived from the statement text, never a parallel list."""

    def test_every_migrated_table_has_exactly_one_derived_leg(self) -> None:
        """Every table ``migrate_governed`` actually BACKFILLS has a derived leg, and every derived leg
        writes a governed table. ``brief`` is the one valid table with no backfill yet (its leg lands at
        63c-ii, ``_not_supported``); the day it lands it gains a migrate exemption and joins this domain
        with no edit here — so the only exclusion is the production constant, never a column list."""
        valid = set(principals._MIGRATE_VALID_TABLES)  # noqa: SLF001 - the verb's own governed set
        assert _LEGS, "no migrate leg was derived — the AST derivation is broken, not the domain empty"
        assert set(_LEGS) <= valid, f"a derived leg writes a non-governed table: {sorted(set(_LEGS) - valid)}"
        legless = valid - {surreal_schema.BRIEF_TABLE} - set(_LEGS)
        assert not legless, f"a governed table has no derived migrate leg: {sorted(legless)}"

    @pytest.mark.parametrize("table", _LEG_TABLES)
    def test_the_derived_columns_are_non_empty_and_match_a_bare_pattern_read(self, table: str) -> None:
        """The depth-aware SET parse is non-empty, duplicate-free, and EQUAL to an independent
        bare-pattern read of the same statement text (two parsers, one source — diffed)."""
        leg, statement = _LEGS[table]
        columns = _set_columns(statement)
        assert columns, f"{leg}: the backfill statement assigns no column: {statement!r}"
        assert len(set(columns)) == len(columns), f"{leg}: a column is assigned twice: {columns}"
        assert frozenset(columns) == _bare_pattern_columns(statement), (
            f"{leg}: the depth-aware parse {sorted(columns)} disagrees with the bare-pattern read "
            f"{sorted(_bare_pattern_columns(statement))} of {statement!r}"
        )

    def test_the_parser_keeps_a_function_call_argument_list_whole(self) -> None:
        """Positive control for the splitter: a comma INSIDE a call is not a column separator (the agent
        leg's ``type::record('principal', $owner)``), and a WHERE clause's ``=`` is not a SET column."""
        statement = "UPDATE t SET a = f('x', $y), b = c WHERE d = 1 AND e IS NONE"
        assert _set_columns(statement) == ("a", "b")
        assert _bare_pattern_columns(statement) == frozenset({"a", "b"})


# --------------------------------------------------------------------------- #
# The live dirty-store world, driven through the REAL CLI verb.
# --------------------------------------------------------------------------- #


def _config_payload(*, database: str) -> dict[str, Any]:
    """A minimal VALID lore.yaml pointed at the TEST store + a unique database (the
    ``test_principals_cli._config_payload`` shape; self-contained for independent collectibility)."""
    return {
        "schema_version": 1,
        "anthropic": {"api_key_env": _ANTHROPIC_ENV},
        "project": {"slug": "preboot_13d_project", "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://localhost:8080",
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": PRODUCTION_DIM,
            "truncate": False,
            "max_input_tokens": 8192,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": "LORE_TEI_KEY",
            "tokenizer": "voyage-4-nano",
        },
        "surreal": {
            "url": surreal_url(),
            "namespace": "lore_test",
            "database": database,
            "user_env": _USER_ENV,
            "password_env": _PASS_ENV,
        },
        "roots": [],
        "include": [],
        "exclude_dirs": [".git"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": False,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9248},
    }


@pytest.fixture(autouse=True)
def _cli_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """The TEST-store creds by the env-var names the config references, plus a dummy Anthropic key."""
    monkeypatch.setenv(_USER_ENV, surreal_user())
    monkeypatch.setenv(_PASS_ENV, surreal_password().get_secret_value())
    monkeypatch.setenv(_ANTHROPIC_ENV, "sk-dummy-preboot-13d")


class _World:
    def __init__(self, env: SurrealEnv, config_path: Path, operator_bare: str) -> None:
        self.env = env
        self.config_path = config_path
        self.operator_bare = operator_bare


@pytest_asyncio.fixture()
async def world(tmp_path: Path) -> Any:
    """A minted TEST database with the FULL governed DDL (agent, message, memory), the principal/keep
    DDL, and ONE operator principal. Reaped on exit (NEVER :18500)."""
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    assert ":18500" not in env.url, env.url
    config_path = tmp_path / "lore.yaml"
    config_path.write_text(yaml.safe_dump(_config_payload(database=env.database)), encoding="utf-8")
    try:
        principal_store, keep_store = await build_principal_and_keep_stores(env)
        try:
            await principal_store.create(email=_OPERATOR_EMAIL, role="member")
            operator = (await principal_store.list())[0]
        finally:
            await keep_store.close()
            await principal_store.close()
        connection = await connect_admin(env)
        try:
            await apply_ddl(connection, surreal_schema.generate_agent_ddl(), url=env.url)
            await apply_ddl(connection, surreal_schema.generate_message_ddl(), url=env.url)
            await apply_ddl(connection, surreal_schema.generate_memory_ddl(dim=PRODUCTION_DIM), url=env.url)
        finally:
            await connection.close()
        yield _World(env, config_path, str(operator.id).partition(":")[2] or str(operator.id))
    finally:
        await drop_database(env)


async def _seed_one_legacy_row(world: _World, table: str) -> None:
    """ONE legacy (NONE-governed) row of ``table`` — so the leg has something to stamp (a zero-row UPDATE
    on a removed column is a SILENT no-op, probed; one row makes the base's failure a real rejection).
    The message leg also gets ONE MIGRATED sender agent (agent-first ORDER satisfied)."""
    connection = await connect_admin(world.env)
    try:
        if table == surreal_schema.MEMORY_TABLE:
            await seed_memory_legacy(connection, row_id="legacy_13d", dim=PRODUCTION_DIM)
        elif table == surreal_schema.AGENT_TABLE:
            await seed_agent_legacy(connection, row_id="legacy_13d", name="legacy_13d", session="s1")
        elif table == surreal_schema.MESSAGE_TABLE:
            await seed_agent_governed(
                connection,
                row_id=_SENDER_ID,
                name=_SENDER_ID,
                session="s1",
                owner_principal=world.operator_bare,
                owner_agent=_SENDER_ID,
                scope=_FIXTURE_SCOPE,
            )
            await seed_message_legacy(connection, sender_id=_SENDER_ID, session="s1", seq=0)
        else:  # pragma: no cover - a NEW derived leg needs a seeder; fail loud, never skip
            raise AssertionError(f"no legacy-row seeder for the derived migrate leg `{table}` — add one")
    finally:
        await connection.close()


async def _remove_field(world: _World, table: str, column: str) -> None:
    connection = await connect_admin(world.env)
    try:
        await run(connection, f"REMOVE FIELD {column} ON TABLE {table}")
        info = await run(connection, f"INFO FOR TABLE {table}")
        assert column not in info["fields"], f"setup: REMOVE FIELD {column} ON {table} did not land: {info!r}"
    finally:
        await connection.close()


async def _snapshot(world: _World, table: str) -> tuple[list[Any], list[Any]]:
    """The target table's rows and the keep table's rows — the byte-inert receipt."""
    connection = await connect_admin(world.env)
    try:
        rows = await run(connection, f"SELECT * FROM {table} ORDER BY id")
        keeps = await run(connection, "SELECT * FROM keep ORDER BY id")
    finally:
        await connection.close()
    return repr(rows).splitlines(), repr(keeps).splitlines()


class _WriteSpy:
    """Records every statement the verb sends through ``principals.run_query`` and every keep mint."""

    def __init__(self) -> None:
        self.statements: list[str] = []
        self.keep_mints: list[dict[str, Any]] = []

    @property
    def writes(self) -> list[str]:
        written = [s for s in self.statements if s.lstrip().upper().startswith(_WRITE_VERBS)]
        return written + [f"KeepStore.get_or_create_keyed({kwargs!r})" for kwargs in self.keep_mints]


@pytest.fixture()
def write_spy(monkeypatch: pytest.MonkeyPatch) -> Iterator[_WriteSpy]:
    spy = _WriteSpy()
    real_run_query = _txn.run_query  # the SAME object principals binds (its import)
    real_mint = KeepStore.get_or_create_keyed

    async def _recording_run_query(*args: Any, **kwargs: Any) -> Any:
        spy.statements.append(str(kwargs.get("statement", args[0] if args else "")))
        return await real_run_query(*args, **kwargs)

    async def _recording_mint(self: KeepStore, *args: Any, **kwargs: Any) -> Any:
        spy.keep_mints.append(dict(kwargs))
        return await real_mint(self, *args, **kwargs)

    monkeypatch.setattr(principals, "run_query", _recording_run_query)
    monkeypatch.setattr(KeepStore, "get_or_create_keyed", _recording_mint)
    yield spy


async def _run_verb(world: _World, table: str) -> int:
    """``lore-adm migrate-governed --table <table>`` through the REAL ``main`` (off the test loop — the
    ``asyncio.run`` idiom, ``test_principals_cli._run_cli``)."""
    argv = ["--config", str(world.config_path), "migrate-governed", "--table", table]
    return await asyncio.to_thread(principals.main, argv)


_ONE_SPAN_PER_COLUMN = re.compile(r"`\w+`(?:, `\w+`)*")


def _refusal_columns(stderr: str) -> tuple[str, frozenset[str]]:
    """``(table, columns)`` parsed from the §13 D refusal sentence; the column list MUST be one backtick span
    per column (am-37 §13.1 item 3)."""
    match = _REFUSAL_COLUMNS.search(stderr)
    assert match, f"the §13 D teaching refusal is ABSENT — stderr was:\n{stderr}"
    columns_text = match.group("cols")
    assert _ONE_SPAN_PER_COLUMN.fullmatch(columns_text), (
        f"the refusal must quote each column in its OWN backtick span (§13.1 item 3): {columns_text!r}"
    )
    names = frozenset(part.strip().strip("`") for part in columns_text.split(","))
    return match.group("table"), names


class TestADirtyStoreRefusesWithTheTeachingBeforeAnyWrite:
    """§13 D pins (generated ∀ leg × its derived columns): one column removed → exit 1, the refusal
    names EXACTLY that column of THAT table and teaches the boot remedy, and NOTHING was written."""

    @pytest.mark.parametrize(("table", "column"), _LEG_COLUMN_CASES)
    async def test_one_removed_column_is_refused_and_named_with_zero_writes(
        self, world: _World, write_spy: _WriteSpy, capsys: pytest.CaptureFixture[str], table: str, column: str
    ) -> None:
        await _seed_one_legacy_row(world, table)
        await _remove_field(world, table, column)
        before = await _snapshot(world, table)
        capsys.readouterr()

        code = await _run_verb(world, table)
        captured = capsys.readouterr()

        refused_table, refused_columns = _refusal_columns(captured.err)
        assert (refused_table, refused_columns) == (table, frozenset({column})), (
            f"the refusal must name exactly `{table}`.`{column}`, named `{refused_table}` "
            f"{sorted(refused_columns)} — stderr:\n{captured.err}"
        )
        assert _REFUSAL_TEACHING in captured.err and "boot the new image once" in captured.err, captured.err
        assert code == 1, f"a pre-boot schema refusal exits 1, got {code}; stderr:\n{captured.err}"
        assert "Traceback" not in captured.err, captured.err
        assert write_spy.writes == [], f"the refusal must precede EVERY write; observed: {write_spy.writes}"
        assert await _snapshot(world, table) == before, "the store changed under a refusal (byte-inert)"


class TestAFullSchemaStoreProceeds:
    """§13 D positive control: every derived column present → the leg runs and stamps its legacy row
    (the precondition does not refuse a healthy store)."""

    @pytest.mark.parametrize("table", _LEG_TABLES)
    async def test_all_columns_present_the_leg_stamps(
        self, world: _World, write_spy: _WriteSpy, capsys: pytest.CaptureFixture[str], table: str
    ) -> None:
        await _seed_one_legacy_row(world, table)
        capsys.readouterr()

        code = await _run_verb(world, table)
        captured = capsys.readouterr()

        assert code == 0, f"a full-schema store must migrate, got exit {code}; stderr:\n{captured.err}"
        assert _REFUSAL_TEACHING not in captured.err, captured.err
        assert "backfilled=1" in captured.out, captured.out
        _leg, statement = _LEGS[table]
        assert statement in write_spy.statements, (
            "the derived backfill statement did not run (derivation drift)"
        )


class TestThePreconditionFactRidesThePreconditionsModel:
    """§13 D chokepoint: ``_agent_migration_preconditions`` carries ``defined_fields`` = the ``--table``'s
    ``INFO FOR TABLE`` field names, beside ``defined_tables``."""

    @pytest.mark.parametrize(("table", "column"), _LEG_COLUMN_CASES)
    async def test_defined_fields_measures_the_removed_column(
        self, world: _World, table: str, column: str
    ) -> None:
        connection = await connect_admin(world.env)
        try:
            handle, _calls = store_handle(connection, url=world.env.url)
            # The ruled, not-yet-built field is read through an ``Any`` alias (the #461 typed reach-around),
            # so the production RED is a test failure, never an unadjudicated mypy error.
            healthy: Any = await principals._agent_migration_preconditions(handle, table=table)  # noqa: SLF001
            assert set(_set_columns(_LEGS[table][1])) <= set(healthy.defined_fields), healthy.defined_fields
            await run(connection, f"REMOVE FIELD {column} ON TABLE {table}")
            dirty: Any = await principals._agent_migration_preconditions(handle, table=table)  # noqa: SLF001
        finally:
            await connection.close()
        assert isinstance(dirty.defined_fields, frozenset), type(dirty.defined_fields)
        assert column not in dirty.defined_fields
        assert set(healthy.defined_fields) - set(dirty.defined_fields) == {column}



async def _remove_every_field(world: _World, table: str) -> frozenset[str]:
    """Remove EVERY field ``INFO FOR TABLE`` lists on ``table`` (the table itself stays defined). Returns the
    removed set, asserted landed."""
    connection = await connect_admin(world.env)
    try:
        info = await run(connection, f"INFO FOR TABLE {table}")
        fields = frozenset(info["fields"])
        for field_name in sorted(fields):
            await run(connection, f"REMOVE FIELD {field_name} ON TABLE {table}")
        after = await run(connection, f"INFO FOR TABLE {table}")
        assert not after["fields"], f"setup: fields survived REMOVE FIELD on {table}: {after!r}"
    finally:
        await connection.close()
    return fields


class TestTheRequiredColumnSetIsTheLegsOwnSetClause:
    """am-37 §13.1 item 5 — the ONE-DERIVATION pin, ∀ leg: with EVERY field of the leg's table removed, the
    refusal names the precondition's WHOLE required column set, and it must EQUAL the columns the leg's own
    ``UPDATE … SET`` statement assigns (parsed from the SAME statement constant the leg executes). A hand
    column map and a derivation are indistinguishable by any positive test; they diverge the day a leg's SET
    gains or loses a column — this pin reds that day, permanently."""

    @pytest.mark.parametrize("table", _LEG_TABLES)
    async def test_the_refused_column_set_equals_the_set_clause(
        self, world: _World, write_spy: _WriteSpy, capsys: pytest.CaptureFixture[str], table: str
    ) -> None:
        await _seed_one_legacy_row(world, table)
        removed = await _remove_every_field(world, table)
        capsys.readouterr()

        code = await _run_verb(world, table)
        captured = capsys.readouterr()

        set_columns = frozenset(_set_columns(_LEGS[table][1]))
        assert set_columns <= removed, (
            f"setup: the SET columns were not all removable fields: {sorted(set_columns - removed)}"
        )
        refused_table, refused_columns = _refusal_columns(captured.err)
        assert refused_table == table and refused_columns == set_columns, (
            f"the precondition's required set {sorted(refused_columns)} must EQUAL the leg's own SET clause "
            f"{sorted(set_columns)} (am-37 §13.1 item 5 — derived, never a hand map); stderr:\n{captured.err}"
        )
        assert code == 1 and write_spy.writes == [], (code, write_spy.writes)
