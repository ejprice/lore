"""Contract — packet 49, the admin CLI (the ``lore-adm`` console script).

Written by ``contract-49-1`` (2026-08-20). The builder builds FROM this; it writes
NO production code. STUB surfaces exist (``build_parser`` returns a BARE parser;
``main`` / ``build_principal_store`` / ``build_principal_key_store`` raise
``NotImplementedError``; the ``__main__`` guard is already LAST), so every feature pin
is RED for the RIGHT reason — never an ImportError.

DESIGN (the work order): ``docs/design/2026-08-20-packet49-cli-keys.md`` §F6 (ONE CLI in
``principals.py``, ``build_parser`` + ``main(argv) -> int`` house idiom, sibling factories
``build_principal_store`` / ``build_principal_key_store``). ⚠⚠ OPERATOR RULING 2026-08-20
(the headline): the dry-run / ``--execute`` paradigm is STRUCK ENTIRELY — there is NO
``--execute`` flag and NO dry-run mode; EVERY verb executes its effect directly on
invocation; only ``list`` / ``list-keys`` are reads. This contract pins that ruling.

THE NINE VERBS (design §F6), each naming its principal by ``--email``:
    add · list · delete · suspend · unsuspend · set-expiry · mint-key · revoke-key · list-keys

LIVE store: ws://127.0.0.1:18000 (NEVER :18500). The end-to-end pins drive ``main`` against
a per-test unique database on the spike store and read it back via an admin connection.
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import importlib
import logging
import re
import tomllib
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
import yaml
from _governed_contract import build_memory_backend
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
from loremaster.config import LoreConfig, resolve_config_value, resolve_secret
from loremaster.index.records import sha512_hex
from loremaster.store._txn import SurrealConnectionError, TxnDomainRejectionError

from loremaster import principal_keys as pk_module
from loremaster import principals as p_module
from loremaster import sanitise as sanitise_module

# Dedicated env-var NAMES the fixture config references (never the values baked in).
_USER_ENV = "LORE_CLI_TEST_SURREAL_USER"
_PASS_ENV = "LORE_CLI_TEST_SURREAL_PASS"
_ANTHROPIC_ENV = "LORE_CLI_TEST_ANTHROPIC"

_EMAIL = "alice@example.com"
_EMAIL_B = "bob@example.com"

_ALL_VERBS = (
    "add", "list", "delete", "suspend", "unsuspend",
    "set-expiry", "mint-key", "revoke-key", "list-keys",
)


@pytest.fixture(autouse=True)
def _cli_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Export the REAL spike-store creds by the env-var NAMEs the fixture config
    references (so ``build_principal_store``'s ``resolve_config_value`` /
    ``resolve_secret`` succeed against ws://127.0.0.1:18000), plus a dummy Anthropic key
    (``load_config`` resolves ``anthropic.api_key_env`` eagerly, though this CLI never
    uses it)."""
    monkeypatch.setenv(_USER_ENV, surreal_user())
    monkeypatch.setenv(_PASS_ENV, surreal_password().get_secret_value())
    monkeypatch.setenv(_ANTHROPIC_ENV, "unused-by-the-principals-cli")


def _config_payload(*, database: str) -> dict[str, Any]:
    """A minimal VALID lore.yaml payload pointed at the spike store + a unique database.

    Self-contained (independent-collectibility) — cloned from ``test_build_store``'s
    payload shape. The surreal block names the spike URL / test namespace / the unique
    per-test database and references creds by env-var NAME.
    """
    return {
        "schema_version": 1,
        "anthropic": {"api_key_env": _ANTHROPIC_ENV},
        "project": {"slug": "cli_test_project", "root": "."},
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


def _make_config(database: str) -> LoreConfig:
    return LoreConfig.model_validate(_config_payload(database=database))


class _CliEnv:
    def __init__(self, config_path: Path, env: SurrealEnv) -> None:
        self.config_path = config_path
        self.env = env

    def argv(self, *args: str) -> list[str]:
        return ["--config", str(self.config_path), *args]


@pytest_asyncio.fixture()
async def cli_env(tmp_path: Path) -> Any:
    """A written lore.yaml pointed at a per-test unique spike-store database, reaped on
    exit. ``main`` builds its stores from this config; the test reads the database back
    via an admin connection."""
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    config_path = tmp_path / "lore.yaml"
    config_path.write_text(yaml.safe_dump(_config_payload(database=env.database)), encoding="utf-8")
    try:
        yield _CliEnv(config_path, env)
    finally:
        await drop_database(env)


async def _run_cli(argv: list[str]) -> int:
    """Invoke the CLI ``main`` OFF the test's running event loop (adversary FINDING 5).

    §F6's house idiom is ``main = asyncio.run(...)``; calling it directly from an
    ``async def`` test raises ``RuntimeError: asyncio.run() cannot be called from a running
    event loop``. Running it in a worker thread (which has NO loop) lets the mandated
    ``asyncio.run`` idiom work unchanged — the contract must not silently contradict its
    own design's idiom instruction."""
    return await asyncio.to_thread(p_module.main, argv)


async def _table_names(env: SurrealEnv) -> set[str]:
    """The tables that currently exist in the database (empty on a virgin DB)."""
    connection = await connect_admin(env)
    try:
        info = await run(connection, "INFO FOR DB")
    finally:
        await connection.close()
    tables = info.get("tables", {}) if isinstance(info, dict) else {}
    return set(tables)


async def _principal_emails(env: SurrealEnv) -> set[str]:
    """Every principal email currently in the database (via a fresh admin connection).

    ⚠ ADVERSARY FINDING 3: on a VIRGIN DB the ``principal`` table does not exist yet and a
    ``SELECT ... FROM principal`` RAISES on 3.2.4 — so the "empty before main" control read
    a not-yet-created table. Tolerant: return ``set()`` when the table is absent."""
    if "principal" not in await _table_names(env):
        return set()
    connection = await connect_admin(env)
    try:
        rows = await run(connection, "SELECT email FROM principal")
    finally:
        await connection.close()
    return {row["email"] for row in rows} if isinstance(rows, list) else set()


async def _db_snapshot(env: SurrealEnv) -> Any:
    """A stable snapshot of the two identity tables (for the read-only controls).

    Tolerant of an absent table (FINDING 3): a table that does not exist snapshots as
    ``"[]"`` rather than raising."""
    present = await _table_names(env)
    connection = await connect_admin(env)
    try:
        principals = (
            await run(connection, "SELECT * FROM principal ORDER BY email")
            if "principal" in present else []
        )
        keys = (
            await run(connection, "SELECT * FROM principal_key ORDER BY name")
            if "principal_key" in present else []
        )
    finally:
        await connection.close()
    return (repr(principals), repr(keys))


# --------------------------------------------------------------------------- #
# Parser surface (offline). build_parser is separately testable (design §F6).
# --------------------------------------------------------------------------- #


class TestParserSurface:
    def test_build_parser_prog_is_the_fixed_invocation(self) -> None:
        """The CLI is invoked as the ``lore-adm`` console script (operator ruling
        2026-08-20 — ``python -m loremaster.principals`` is an unwieldy admin interface),
        so the parser ``prog`` is exactly that (a structural anchor)."""
        assert p_module.build_parser().prog == "lore-adm"

    @pytest.mark.parametrize("verb", _ALL_VERBS)
    def test_every_verb_is_recognised(self, verb: str) -> None:
        """Each of the nine verbs parses (a principal-naming verb with ``--email``; the
        read verbs ``list`` has none). RED against the bare stub parser (no subcommands)."""
        parser = p_module.build_parser()
        argv = [verb] if verb == "list" else [verb, "--email", _EMAIL]
        if verb in {"revoke-key", "mint-key"}:
            argv += ["--name", "laptop"]
        if verb == "set-expiry":
            argv += ["--clear"]
        args = parser.parse_args(argv)  # must NOT SystemExit
        # argparse stores the subcommand; the exact dest is the builder's, but SOME
        # attribute must carry the verb so main can dispatch.
        assert verb in vars(args).values() or getattr(args, "command", None) == verb, (
            f"parsed args for {verb!r} carry no dispatchable verb marker: {vars(args)!r}"
        )

    @pytest.mark.parametrize("verb", _ALL_VERBS)
    def test_no_verb_accepts_an_execute_flag(self, verb: str) -> None:
        """⚠⚠ THE OPERATOR HEADLINE (2026-08-20): the ``--execute`` / dry-run paradigm is
        STRUCK. NO verb accepts ``--execute`` — parsing it is an unrecognised-argument
        error. A STANDING GUARD: green now (no such flag), RED the day someone re-adds a
        ``--execute`` flag to any verb."""
        parser = p_module.build_parser()
        base = [verb] if verb == "list" else [verb, "--email", _EMAIL]
        if verb in ("revoke-key", "mint-key"):
            base += ["--name", "laptop"]
        if verb == "set-expiry":
            base += ["--clear"]
        with pytest.raises(SystemExit):
            parser.parse_args([*base, "--execute"])

    def test_source_contains_no_execute_flag_or_dry_run(self) -> None:
        """The struck paradigm leaves NO trace: no ``--execute`` option string and no
        ``dry_run`` / ``is_total_wipe`` scaffolding in any CODE string (docstrings, which
        may explain the ruling, are excluded)."""
        source = Path(p_module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        docstrings = {
            ast.get_docstring(node, clean=False)
            for node in ast.walk(tree)
            if isinstance(node, ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
        }
        offenders = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value not in docstrings
            and re.search(r"--execute|is_total_wipe|dry[_-]run", node.value, re.I)
        ]
        assert not offenders, (
            f"the struck dry-run/--execute paradigm left a trace in a code string: {offenders!r}"
        )

    def test_unknown_verb_and_missing_required_email_exit_nonzero(self) -> None:
        parser = p_module.build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["not-a-verb"])
        with pytest.raises(SystemExit):
            parser.parse_args(["suspend"])  # missing required --email

    def test_no_dry_run_mechanism_survives_the_governed_migration_surface(self) -> None:
        """FORK-W (§10.7-W): the dry-run paradigm is STRUCK — ``migrate-governed`` always executes;
        the read-only preview is the separate ``report-unmigrated`` verb. Two legs:

        (1) RUNTIME MECHANISM — no ``dry_run`` PARAMETER on ``migrate_governed`` /
        ``_migrate_memory_scope``, no ``dry_run`` FIELD on ``MigrateGovernedResult``, and
        ``migrate-governed`` rejects a ``--dry-run`` flag. This is the robust guard: it reds the day
        a param/field/flag is re-introduced, regardless of spelling.

        (2) BARE GREP (the §10.7-W rider) — over ``governed.py`` + ``principals.py`` + the 63a test
        modules, every ``dry[_-]run`` textual hit is PROSE (a comment or a docstring documenting the
        struck paradigm), never a live code token. A comment/docstring residual is allowed and
        adjudicated in REPORT-build-63a-ii; a NEW code token (param/kwarg/flag/field/attr) reds."""
        import dataclasses
        import inspect

        from loremaster.governed import MigrateGovernedResult

        from loremaster import governed

        # (1) runtime mechanism.
        assert "dry_run" not in inspect.signature(p_module.migrate_governed).parameters, (
            "migrate_governed must not carry a dry_run parameter (the struck paradigm)"
        )
        assert "dry_run" not in inspect.signature(p_module._migrate_memory_scope).parameters, (
            "_migrate_memory_scope must not carry a dry_run parameter (the struck paradigm)"
        )
        assert "dry_run" not in {f.name for f in dataclasses.fields(MigrateGovernedResult)}, (
            "MigrateGovernedResult must not carry a dry_run field (the struck paradigm)"
        )
        parser = p_module.build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["migrate-governed", "--table", "memory", "--dry-run"])

        # (2) bare grep — every textual residual must be PROSE, never a live code token.
        tests_dir = Path(__file__).parent
        scope_files = [
            Path(governed.__file__),
            Path(p_module.__file__),
            *sorted(tests_dir.glob("test_*_63a.py")),
            tests_dir / "_governed_contract.py",
        ]
        # A LIVE code token: a def-parameter, a keyword/default/field/annotation (dry_run[:=]), an
        # attribute access (.dry_run), or a quoted CLI flag string. Prose (backticked ``dry-run``,
        # a hyphenated "dry-run mode") matches NONE of these.
        mechanism = re.compile(
            r"""def\s+\w+\([^)]*\bdry_run\b   # a function parameter
              | \bdry_run\s*[:=]              # kwarg / default / field / annotation
              | \.dry_run\b                   # an attribute access
              | ["']--?dry[_-]run["']         # a quoted CLI option string
            """,
            re.VERBOSE,
        )
        offenders: list[str] = []
        for path in scope_files:
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if line.lstrip().startswith("#"):
                    continue  # a comment is prose documenting the struck paradigm, not a mechanism
                if mechanism.search(line):
                    offenders.append(f"{path.name}:{lineno}: {line.strip()}")
        assert not offenders, (
            "a LIVE dry_run code token resurfaced (the struck paradigm) — every residual must be "
            "prose:\n" + "\n".join(offenders)
        )


# --------------------------------------------------------------------------- #
# __main__-guard-last — its OWN AST pin (clone test_server_entrypoint; per-file,
# there is no global scan). GREEN by construction (the stub places the guard last);
# a def/binding placed AFTER the guard reddens it.
# --------------------------------------------------------------------------- #


def _is_main_guard(node: ast.stmt) -> bool:
    if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
        return False
    left = node.test.left
    return isinstance(left, ast.Name) and left.id == "__name__"


class TestReportUnmigratedVerb:
    """packet 63a-ii (§10.7-W): ``lore-adm report-unmigrated --table <t>`` is the read-only PREVIEW
    verb the struck dry-run paradigm no longer fills — it counts a governed table's un-migrated
    (NONE-scope) rows WITHOUT writing (``report_unmigrated_governed_rows`` over an injected
    StoreHandle, R4). A READ, the class the operator's ruling allows (like ``list``/``list-keys``)."""

    def test_the_parser_accepts_report_unmigrated(self) -> None:
        parser = p_module.build_parser()
        namespace = parser.parse_args(["report-unmigrated", "--table", "memory"])
        assert namespace.command == "report-unmigrated" and namespace.table == "memory", namespace

    async def test_report_unmigrated_counts_over_a_provisioned_table(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Provision the governed memory table (its ensure_ready wires the scope column + index);
        # empty ⇒ zero NONE-scope rows. Exercises the dispatch happy path end to end.
        backend = await build_memory_backend(cli_env.env)
        await backend.close()
        rc = await _run_cli(cli_env.argv("report-unmigrated", "--table", "memory"))
        out = capsys.readouterr().out
        assert rc == 0, f"report-unmigrated must succeed over a provisioned table; out={out!r}"
        assert "unmigrated=0" in out, f"the READ verb must print the NONE-scope count; out={out!r}"

    async def test_report_unmigrated_on_an_absent_table_fails_loud_not_a_traceback(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # No memory table provisioned: the READ must fail LOUD (exit 1 + a stderr line), never a
        # traceback (Unix philosophy — loud on failure; the missing-table rejection is caught).
        rc = await _run_cli(cli_env.argv("report-unmigrated", "--table", "memory"))
        assert rc == 1, "report-unmigrated over an absent governed table must exit non-zero"
        assert p_module._CLI_PROG in capsys.readouterr().err, (
            "a failure must be a stderr line, not a crash"
        )


class TestMainGuardIsLast:
    def test_main_guard_is_the_last_top_level_statement(self) -> None:
        """Under the ``python -m loremaster.principals`` FALLBACK the ``__main__`` guard runs
        inline, so anything after it would not execute (main() runs first) — the
        def-after-guard NameError class. (The primary ``lore-adm`` console script calls
        main() after import and is unaffected, but the fallback must stay sound.)
        ``principals.py`` needs its OWN pin (``test_server_entrypoint`` / ``test_scout`` scan
        per file; there is no global scan)."""
        source = Path(p_module.__file__).read_text(encoding="utf-8")
        body = ast.parse(source).body
        guards = [i for i, node in enumerate(body) if _is_main_guard(node)]
        assert guards, "principals.py has no `if __name__ == '__main__'` guard"
        assert guards[-1] == len(body) - 1, (
            "the `__main__` guard must be the LAST top-level statement in principals.py; a "
            "def/binding after it will not execute under `python -m loremaster.principals`"
        )


# --------------------------------------------------------------------------- #
# The sibling store factories (design §F6): build_principal_store /
# build_principal_key_store read the SAME config accessors build_store does (minus
# dim). RED now (both raise NotImplementedError).
# --------------------------------------------------------------------------- #


def _assert_identity_store_resolved(store: Any, config: LoreConfig) -> None:
    """The identity store carries the config-resolved coordinates (no dim — an identity
    store is never embedded). Reads the ctor-stored private attributes (the PrincipalStore
    named storage)."""
    assert store._url == config.surreal.url
    assert store._namespace == config.surreal.namespace
    assert store._database == config.effective_surreal_database
    assert store._user == resolve_config_value(config.surreal.user_env)
    assert (
        store._password.get_secret_value()
        == resolve_secret(config.surreal.password_env).get_secret_value()
    )


class TestSiblingStoreFactories:
    def test_build_principal_store_resolves_config_coordinates(self) -> None:
        config = _make_config(unique_database())
        store = p_module.build_principal_store(config)
        assert isinstance(store, p_module.PrincipalStore)
        _assert_identity_store_resolved(store, config)

    def test_build_principal_key_store_resolves_config_coordinates(self) -> None:
        config = _make_config(unique_database())
        store = pk_module.build_principal_key_store(config)
        assert isinstance(store, pk_module.PrincipalKeyStore)
        _assert_identity_store_resolved(store, config)

    def test_both_factories_resolve_the_same_database_accessor_as_each_other(self) -> None:
        """DRY (design §F6): both factories read ``config.effective_surreal_database`` —
        NOT a hand-rolled db-resolution that could drift. A build that hardcoded or
        differently-derived the db in one factory would diverge here."""
        config = _make_config(unique_database())
        principal_store = p_module.build_principal_store(config)
        key_store = pk_module.build_principal_key_store(config)
        assert principal_store._database == key_store._database == config.effective_surreal_database

    def test_the_cli_module_routes_through_both_factories(self) -> None:
        """DRY routing (design §F6): the CLI obtains its stores from the sibling factories,
        never a hand-rolled ``PrincipalStore(...)`` / ``PrincipalKeyStore(...)`` recipe
        cloned at the call site. Scans ``principals.py`` for a CALL to each factory
        (excluding the factories' OWN definitions). RED now — ``main`` is a raising stub."""
        source = Path(p_module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        factory_defs = {"build_principal_store", "build_principal_key_store"}
        # A factory's OWN body constructs a PrincipalStore/PrincipalKeyStore CLASS (not a
        # call to the factory function), so scanning for factory-NAME calls finds only the
        # CLI's usage — no exclusion needed.
        called: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                name = (
                    fn.id if isinstance(fn, ast.Name)
                    else fn.attr if isinstance(fn, ast.Attribute)
                    else None
                )
                if name in factory_defs:
                    called.add(name)
        assert factory_defs <= called, (
            f"the CLI must build its stores via the sibling factories {factory_defs} — "
            f"found calls to {called}. A hand-rolled store construction at the CLI site is a "
            f"clone of the build_store recipe (design §F6 DRY)."
        )


# --------------------------------------------------------------------------- #
# Creds-free config resolution (LEAD RULING #6): the admin CLI resolves ONLY the
# surreal block and MUST NOT require the Anthropic embedding key. It uses the
# comms_cli pattern (surreal-only parse), NOT index/cli.py's eager `load_config`
# (which resolves `anthropic.api_key_env` at boot). Rationale: an admin op failing
# because an embedding key is unset is a bad failure mode.
# --------------------------------------------------------------------------- #


class TestCredsFreeConfigResolution:
    async def test_the_cli_runs_with_no_anthropic_key_set(
        self, cli_env: _CliEnv, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ LEAD RULING #6: with the Anthropic env var UNSET, a CLI verb still succeeds —
        proving the CLI resolves the surreal block creds-free (the comms_cli pattern) and
        never eagerly resolves the embedding key. A build using ``load_config`` (which
        resolves ``anthropic.api_key_env`` eagerly) would raise a ``KeyError`` on the unset
        var and fail here — which is exactly the bad failure mode this pin forbids."""
        monkeypatch.delenv(_ANTHROPIC_ENV, raising=False)  # the autouse fixture set it; remove it
        rc = await _run_cli(cli_env.argv("add", "--email", _EMAIL))
        assert rc == 0
        assert _EMAIL in await _principal_emails(cli_env.env), (
            "the CLI must run and mutate the store with NO Anthropic key set — resolve the "
            "surreal block creds-free (comms_cli pattern), never load_config's eager anthropic"
        )

    def test_the_cli_does_not_call_load_config(self) -> None:
        """Belt-and-braces (LEAD RULING #6): the CLI must NOT call ``load_config`` (which
        eagerly resolves the Anthropic key). Source scan of ``principals.py`` — it parses
        the surreal block via ``LoreConfig.model_validate`` / a surreal-only load instead.
        RED now (the CLI is a stub with no config loading yet)."""
        source = Path(p_module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        called = {
            node.func.id if isinstance(node.func, ast.Name)
            else node.func.attr if isinstance(node.func, ast.Attribute)
            else None
            for node in ast.walk(tree) if isinstance(node, ast.Call)
        }
        assert "load_config" not in called, (
            "the CLI must NOT use load_config (it eagerly resolves anthropic.api_key_env, "
            "coupling an admin op to an embedding key) — resolve the surreal block creds-free "
            "(LEAD RULING #6). (The behavioural pin above independently proves the CLI DOES "
            "load config — it reaches the configured database — so this is not vacuously green.)"
        )


# --------------------------------------------------------------------------- #
# Verbs execute DIRECTLY (the operator headline) — end-to-end main() against the
# live spike store. RED now (main raises NotImplementedError).
# --------------------------------------------------------------------------- #


class TestVerbsExecuteDirectly:
    async def test_add_creates_a_principal_on_invocation(self, cli_env: _CliEnv) -> None:
        """``add`` executes DIRECTLY — a single invocation creates the principal in the
        CONFIGURED database (no ``--execute`` step). This also proves the CLI wired its
        store from config (it reached the database the fixture named)."""
        assert await _principal_emails(cli_env.env) == set()  # empty before
        rc = await _run_cli(cli_env.argv("add", "--email", _EMAIL))
        assert rc == 0
        assert _EMAIL in await _principal_emails(cli_env.env)  # created by the ONE call

    async def test_delete_removes_the_principal_and_cascades_on_invocation(
        self, cli_env: _CliEnv
    ) -> None:
        """``delete`` executes DIRECTLY and HARD-deletes (design §F2) — after one
        invocation the principal is gone."""
        await _run_cli(cli_env.argv("add", "--email", _EMAIL))
        assert _EMAIL in await _principal_emails(cli_env.env)
        rc = await _run_cli(cli_env.argv("delete", "--email", _EMAIL))
        assert rc == 0
        assert _EMAIL not in await _principal_emails(cli_env.env)

    async def test_suspend_sets_status_on_invocation(self, cli_env: _CliEnv) -> None:
        """``suspend`` executes DIRECTLY — after one invocation the principal's status is
        ``suspended`` (read back from the store)."""
        await _run_cli(cli_env.argv("add", "--email", _EMAIL))
        rc = await _run_cli(cli_env.argv("suspend", "--email", _EMAIL))
        assert rc == 0
        connection = await connect_admin(cli_env.env)
        try:
            row = (await run(connection, "SELECT status FROM principal WHERE email = $e", {"e": _EMAIL}))[0]
        finally:
            await connection.close()
        assert row["status"] == "suspended"

    async def test_list_is_a_read_leaving_state_byte_identical(self, cli_env: _CliEnv) -> None:
        """CONTROL: ``list`` is a READ — after it the database is byte-identical (so the
        "state changed" probes above demonstrably distinguish a mutating verb from a
        read)."""
        await _run_cli(cli_env.argv("add", "--email", _EMAIL))
        before = await _db_snapshot(cli_env.env)
        rc = await _run_cli(cli_env.argv("list"))
        assert rc == 0
        assert await _db_snapshot(cli_env.env) == before, "`list` must not mutate the store"

    async def test_mint_key_prints_the_secret_exactly_once_and_it_verifies(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """``mint-key`` executes directly and prints the ``<name>:<secret>`` credential
        EXACTLY ONCE (design §F4). The printed credential VERIFIES against the store —
        proving the CLI's hash (``sha512_hex(name:secret)``) agrees with ``verify``. A
        second ``mint-key`` (different name) mints a NEW key and NEVER re-prints the first
        secret (the raw secret is unrecoverable after mint)."""
        await _run_cli(cli_env.argv("add", "--email", _EMAIL))
        rc = await _run_cli(cli_env.argv("mint-key", "--email", _EMAIL, "--name", "laptop"))
        assert rc == 0
        first_out = capsys.readouterr().out
        credential_lines = [ln for ln in first_out.splitlines() if re.fullmatch(r"laptop:\S+", ln.strip())]
        assert len(credential_lines) == 1, (
            f"mint-key must print exactly ONE `<name>:<secret>` line; got {credential_lines!r}"
        )
        first_credential = credential_lines[0].strip()

        # The printed credential VERIFIES (CLI mint ↔ store verify agree on the hash).
        key_store = pk_module.build_principal_key_store(_make_config(cli_env.env.database))
        try:
            await key_store.ensure_ready()
            verification = await key_store.verify(first_credential)
            assert verification is not None and verification.principal.email == _EMAIL
        finally:
            await key_store.close()

        # A second mint-key (different name) mints a NEW key, never re-printing the first.
        first_secret = first_credential.split(":", 1)[1]
        rc = await _run_cli(cli_env.argv("mint-key", "--email", _EMAIL, "--name", "ci"))
        assert rc == 0
        second_out = capsys.readouterr().out
        assert first_secret not in second_out, "mint-key re-printed the FIRST secret — it is unrecoverable"
        second_lines = [ln for ln in second_out.splitlines() if re.fullmatch(r"ci:\S+", ln.strip())]
        assert len(second_lines) == 1

    async def test_mint_key_stores_only_the_hash_never_the_raw_secret(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
    ) -> None:
        """⚠ ADVERSARY R1: the STORE-level pin 2 is architecturally vacuous — ``mint`` takes
        an ALREADY-hashed secret, so the raw never reaches the store. Probe the layer where
        the raw EXISTS: the CLI ``mint-key`` path generates the raw secret, hashes it, stores
        the hash. Assert the stored ``principal_key`` row holds the sha512 hash and NOWHERE
        the raw secret, and the raw secret appears in NO log record. POSITIVE CONTROL: the
        hash IS present (so the probe can see stored content)."""
        await _run_cli(cli_env.argv("add", "--email", _EMAIL))
        with caplog.at_level("DEBUG"):
            rc = await _run_cli(cli_env.argv("mint-key", "--email", _EMAIL, "--name", "laptop"))
        assert rc == 0
        credential = next(
            ln.strip() for ln in capsys.readouterr().out.splitlines()
            if re.fullmatch(r"laptop:\S+", ln.strip())
        )
        secret = credential.split(":", 1)[1]
        connection = await connect_admin(cli_env.env)
        try:
            rows = await run(connection, "SELECT * FROM principal_key")
        finally:
            await connection.close()
        blob = repr(rows)
        assert secret not in blob, (
            f"the RAW secret was found in the stored principal_key row — the CLI must store "
            f"ONLY the sha512 hash of `<name>:<secret>`, never the raw secret; row={rows!r}"
        )
        assert sha512_hex(credential) in blob, (
            "POSITIVE CONTROL failed: the sha512 hash of the credential is NOT in the row — "
            "the probe cannot see stored content, so its negative result is worthless"
        )
        for record in caplog.records:
            assert secret not in record.getMessage(), (
                "the raw secret leaked into a log record — the CLI must never log the credential"
            )

    async def test_revoke_key_denies_the_credential_on_invocation(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """``revoke-key`` executes DIRECTLY — after one invocation the credential no longer
        verifies. Mints via the CLI, captures the credential, revokes via the CLI, then
        confirms denial through the store."""
        await _run_cli(cli_env.argv("add", "--email", _EMAIL))
        await _run_cli(cli_env.argv("mint-key", "--email", _EMAIL, "--name", "laptop"))
        credential = next(
            ln.strip() for ln in capsys.readouterr().out.splitlines()
            if re.fullmatch(r"laptop:\S+", ln.strip())
        )
        rc = await _run_cli(cli_env.argv("revoke-key", "--email", _EMAIL, "--name", "laptop"))
        assert rc == 0
        key_store = pk_module.build_principal_key_store(_make_config(cli_env.env.database))
        try:
            await key_store.ensure_ready()
            assert await key_store.verify(credential) is None  # denied after the ONE revoke call
        finally:
            await key_store.close()

    async def test_the_raw_secret_is_never_printed_by_a_non_mint_verb(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Only ``mint-key`` ever emits a secret. ``list-keys`` shows key metadata (names,
        flags) but NEVER a secret (it is unrecoverable). Mints, drains the mint output,
        then asserts ``list-keys`` output carries the key NAME but not the secret."""
        await _run_cli(cli_env.argv("add", "--email", _EMAIL))
        await _run_cli(cli_env.argv("mint-key", "--email", _EMAIL, "--name", "laptop"))
        secret = next(
            ln.strip().split(":", 1)[1] for ln in capsys.readouterr().out.splitlines()
            if re.fullmatch(r"laptop:\S+", ln.strip())
        )
        rc = await _run_cli(cli_env.argv("list-keys", "--email", _EMAIL))
        assert rc == 0
        listing = capsys.readouterr().out
        assert "laptop" in listing, "list-keys must show the key name"
        assert secret not in listing, "list-keys must NEVER print the raw secret (it is unrecoverable)"


# --------------------------------------------------------------------------- #
# Pin #19 (LEAD-SURFACED, repo P8d "rendered stored free text" law) — the CLI's
# `list`/`list-keys` render STORED FREE TEXT (principal email/display_name, key name).
# Any NEW render of stored free text routes through the shared sanitiser seam and a
# hostile value must NOT forge output structure.
#
# ⚠ RESOLVED — Fable ruled F8 = YES (terminal render IS in scope; committed 075a1bd);
# LEAD RULING #4 (2026-08-20). No longer pending. Pin the CANONICAL LINE sanitiser
# `loremaster.sanitise.sanitise_line` / `safe_str` (finding #34 — `_sanitise_line` is
# now just an alias). Pin the LINE sanitiser, NOT the fence machinery
# (`max_backtick_run`/`fence_width`), per design §F8.
# --------------------------------------------------------------------------- #

# A hostile display_name: a real content head, then a survived-newline that fractures
# the render into an extra line AND smuggles a byte-identical phantom principal row,
# plus a backtick run (the P8d hostile-fixture shape: newlines + row-shaped forgery +
# backtick runs).
_FORGED_ROW = "evil@attacker.com  admin  active"
_HOSTILE_DISPLAY_NAME = f"Mallory\n{_FORGED_ROW}\n``` `"

# ADVERSARY FINDING 4: the `list-keys` KEY-NAME hostile fixture (§F8 names key `name` as a
# must-launder field). A key name with a survived newline forges a phantom key row.
_FORGED_KEY_ROW = "phantom-key   revoked-but-shown-active"
_HOSTILE_KEY_NAME = f"laptop\n{_FORGED_KEY_ROW}\n``` `"


class TestRenderSafety:
    async def test_hostile_display_name_does_not_forge_a_row_in_list(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A principal whose ``display_name`` embeds a newline + a fake principal-row +
        backtick runs must NOT, when ``list`` renders it, produce a STANDALONE line equal
        to the forged row — the stored newline must be neutralised (the canonical LINE
        sanitiser ``loremaster.sanitise.sanitise_line`` collapses controls to a space). A
        build that rendered ``display_name`` verbatim would let the crafted value forge a
        phantom row. The real content head still appears (rendered, just made honest)."""
        await _run_cli(cli_env.argv("add", "--email", _EMAIL, "--display-name", _HOSTILE_DISPLAY_NAME))
        rc = await _run_cli(cli_env.argv("list"))
        assert rc == 0
        listing = capsys.readouterr().out
        output_lines = [ln.strip() for ln in listing.splitlines()]
        assert _FORGED_ROW not in output_lines, (
            "the hostile display_name's survived newline forged a standalone phantom row in "
            "`list` output — stored free text must route through the canonical sanitiser seam "
            "(loremaster.sanitise.sanitise_line/safe_str), which collapses newlines to a space"
        )
        assert "Mallory" in listing, "the display_name's real content must still render"

    def test_the_render_path_routes_through_the_shared_sanitiser_seam(self) -> None:
        """DRY / P8d (LEAD RULING #4): the CLI's stored-free-text render routes through the
        SHARED CANONICAL LINE sanitiser (``sanitise_line`` / ``safe_str`` — finding #34),
        never a private re-implementation and never the fence machinery. Source scan of
        ``principals.py`` for a call to the seam. RED now (the CLI is a stub)."""
        source = Path(p_module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        seam_names = {"sanitise_line", "safe_str"}
        called = {
            node.func.id if isinstance(node.func, ast.Name)
            else node.func.attr if isinstance(node.func, ast.Attribute)
            else None
            for node in ast.walk(tree) if isinstance(node, ast.Call)
        }
        assert seam_names & called, (
            "the CLI renders stored free text (principal display_name/email, key name) but "
            "calls no shared canonical sanitiser seam (loremaster.sanitise.sanitise_line / "
            "safe_str) — P8d law / LEAD RULING #4"
        )

    async def test_render_routes_through_the_shared_sanitiser_by_mutation(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ MUTATION-PROOF of sharing (LEAD RULING #4 — "keep the mutation-proof sharing"):
        perturb the CANONICAL ``sanitise_line`` seam and require the ``list`` render to
        reflect it. Covers every import style: patching ``loremaster.sanitise.sanitise_line``
        catches ``safe_str`` (which calls the module-global at runtime) AND
        ``import loremaster.sanitise``; patching ``principals.sanitise_line`` (raising=False)
        catches ``from loremaster.sanitise import sanitise_line``. A PRIVATE cloned sanitiser
        would show no marker → RED (the #102-class clone this catches)."""
        marker = "XSANITISERWASHEREX"
        original = sanitise_module.sanitise_line

        def _marked(text: str) -> Any:
            return f"{original(text)}{marker}"

        monkeypatch.setattr(sanitise_module, "sanitise_line", _marked)
        monkeypatch.setattr(p_module, "sanitise_line", _marked, raising=False)

        await _run_cli(cli_env.argv("add", "--email", _EMAIL, "--display-name", "RenderProbe"))
        rc = await _run_cli(cli_env.argv("list"))
        assert rc == 0
        listing = capsys.readouterr().out
        assert marker in listing, (
            "the CLI `list` render does not route stored free text through the shared "
            "canonical sanitiser (loremaster.sanitise.sanitise_line/safe_str) — a private "
            "sanitiser clone is a #102-class defect (LEAD RULING #4)"
        )

    async def test_hostile_key_name_does_not_forge_a_row_in_list_keys(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """⚠ ADVERSARY FINDING 4: §F8 names the key ``name`` as a must-launder field, but
        the ``list`` pins above exercise ONLY ``display_name`` — a ``list-keys`` build that
        renders ``key.name`` VERBATIM (or via a private clone) shipped green. A key minted
        with a hostile NAME (newline + fake key-row + backtick runs) must NOT forge a
        standalone phantom key row in ``list-keys`` output."""
        await _run_cli(cli_env.argv("add", "--email", _EMAIL))
        await _run_cli(cli_env.argv("mint-key", "--email", _EMAIL, "--name", _HOSTILE_KEY_NAME))
        capsys.readouterr()  # drain the mint secret line
        rc = await _run_cli(cli_env.argv("list-keys", "--email", _EMAIL))
        assert rc == 0
        output_lines = [ln.strip() for ln in capsys.readouterr().out.splitlines()]
        assert _FORGED_KEY_ROW not in output_lines, (
            "the hostile key NAME's survived newline forged a standalone phantom key row in "
            "`list-keys` output — the key name must route through the shared sanitiser seam "
            "(loremaster.sanitise.sanitise_line/safe_str)"
        )

    async def test_list_keys_render_routes_through_the_shared_sanitiser_by_mutation(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ ADVERSARY R3/F4: a PER-RENDER mutation-proof for ``list-keys`` (the ``list``
        mutation-proof above does NOT cover it, and the AST source-scan passes on ANY single
        sanitise call). Patch the canonical seam; the ``list-keys`` render must reflect the
        marker — a ``list-keys`` that renders the key name verbatim / via a private clone
        shows no marker → RED."""
        marker = "XSANITISERWASHEREX"
        original = sanitise_module.sanitise_line

        def _marked(text: str) -> Any:
            return f"{original(text)}{marker}"

        monkeypatch.setattr(sanitise_module, "sanitise_line", _marked)
        monkeypatch.setattr(p_module, "sanitise_line", _marked, raising=False)

        await _run_cli(cli_env.argv("add", "--email", _EMAIL))
        await _run_cli(cli_env.argv("mint-key", "--email", _EMAIL, "--name", "renderprobe"))
        capsys.readouterr()  # drain the mint output
        rc = await _run_cli(cli_env.argv("list-keys", "--email", _EMAIL))
        assert rc == 0
        assert marker in capsys.readouterr().out, (
            "the CLI `list-keys` render does not route the key name through the shared "
            "canonical sanitiser (sanitise_line/safe_str) — a private clone or verbatim "
            "render is a #102-class defect (adversary FINDING 4 / R3)"
        )


# --------------------------------------------------------------------------- #
# R2 (OPERATOR RULING — add --role, 2026-08-20, delta re-audit): the `add` verb can
# mint an admin. This is an ADDITIVE class (it does NOT modify any existing frozen
# pin). `--role` is a closed choice {member, admin}; omitted → the store DEFAULT
# (member, least-privilege). The admin + member pins DISCRIMINATE: a build that
# ignored --role (always member) fails the admin pin; a build that always minted admin
# fails the member pin.
# --------------------------------------------------------------------------- #


async def _role_of(cli_env: _CliEnv, email: str) -> str | None:
    """The stored role for ``email`` — read THROUGH the store mapper (``get_by_email``),
    so a mis-mapped role is caught, not just a raw column read."""
    store = p_module.build_principal_store(_make_config(cli_env.env.database))
    try:
        await store.ensure_ready()
        principal = await store.get_by_email(email)
    finally:
        await store.close()
    return None if principal is None else principal.role


class TestAddRole:
    async def test_add_role_admin_mints_an_admin(self, cli_env: _CliEnv) -> None:
        """`add --email e --role admin` executes directly and the principal reads back
        with ``role == 'admin'``. RED before the verb learns ``--role`` (argparse rejects
        the unknown flag → SystemExit)."""
        rc = await _run_cli(cli_env.argv("add", "--email", _EMAIL, "--role", "admin"))
        assert rc == 0
        assert await _role_of(cli_env, _EMAIL) == "admin"

    async def test_bare_add_defaults_to_member(self, cli_env: _CliEnv) -> None:
        """The DISCRIMINATING control: a bare ``add`` (no ``--role``) takes the store
        DEFAULT ``member`` (least-privilege). A build that hardcoded ``admin`` — or minted
        the wrong default — fails HERE while the admin pin above passes."""
        rc = await _run_cli(cli_env.argv("add", "--email", _EMAIL_B))
        assert rc == 0
        assert await _role_of(cli_env, _EMAIL_B) == "member"

    def test_add_role_rejects_an_out_of_domain_value(self) -> None:
        """``--role`` is a CLOSED argparse choice {member, admin}: a bogus value is a
        parse-time SystemExit, never a value reaching the store."""
        parser = p_module.build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["add", "--email", _EMAIL, "--role", "bogus"])


# --------------------------------------------------------------------------- #
# Console-script entry point (operator ruling 2026-08-20): the admin CLI is invoked
# as ``lore-adm``, a proper console script — NOT ``python -m loremaster.principals``
# (unwieldy in ``podman exec``, exposes the internal module path). Pin BOTH that
# pyproject WIRES the entry point AND that its declared target RESOLVES to a callable:
# an entry point naming a nonexistent target ships a ``lore-adm`` that ImportErrors on
# first run — green source but a broken installed console script.
# --------------------------------------------------------------------------- #


class TestConsoleScriptEntryPoint:
    def test_lore_adm_entry_point_resolves_to_a_real_callable(self) -> None:
        """``pyproject [project.scripts]`` wires ``lore-adm`` to ``loremaster.principals:main``,
        and that DECLARED target imports to a callable — resolved exactly as the console-script
        machinery would (import the module, getattr the attr). RED if the entry point is
        absent/mis-wired, or if the target string names a nonexistent module/attribute (a
        broken ``lore-adm`` that would ImportError on first invocation)."""
        pyproject_path = Path(p_module.__file__).resolve().parents[1] / "pyproject.toml"
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        target = data.get("project", {}).get("scripts", {}).get("lore-adm")
        assert target == "loremaster.principals:main", (
            "pyproject [project.scripts] must wire `lore-adm` to `loremaster.principals:main`; "
            f"got {target!r}"
        )
        module_name, _, attribute = target.partition(":")
        entry_point = getattr(importlib.import_module(module_name), attribute)
        assert callable(entry_point), (
            f"the console-script target {target!r} must resolve to a callable; got {entry_point!r}"
        )


# --------------------------------------------------------------------------- #
# 63c amendment 37 §11 (R2-1, commit ``1708a4c``) — ONE lore-adm fault handler, at
# ``_dispatch``. PROPERTY (§11 item 1): *every lore-adm verb translates every store or domain
# fault into ``f"{_CLI_PROG}: {error}"`` on stderr + exit 1 — never a traceback, never a
# success.* The DOMAIN is ``build_parser()``'s subparser choices, DERIVED at collection (never a
# list), so a verb added to the parser joins the sweep BY NAME; each verb's minimal argv is
# DERIVED from its own subparser (required options, required mutually-exclusive groups,
# positionals), so there is no argv table that could fall behind the parser.
#
# ONE injection point every verb reaches (§11 item 4): every store factory lore-adm calls
# (``build_principal_store`` / ``build_keep_store``, plus ``build_principal_key_store`` so the
# sweep never reaches a real socket) returns a fake whose ``ensure_ready`` raises the fault.
# ``ensure_ready`` precedes every verb handler on every route, so the fault is raised before any
# verb-specific code runs, and the stderr line must carry the INJECTED text (proof the fate is the
# injected fault's, not a config or argv failure).
#
# RED at fix3 r2 (patch md5 ``f5897681``, over HEAD ``0b0011b``): the principal/key branch of
# ``_dispatch`` and ``_dispatch_keep`` catch ``SurrealConnectionError`` but not the rest of
# ``SurrealStoreError``, so a ``TxnDomainRejectionError`` escapes ``main`` as a traceback. GREEN
# only for ``migrate-governed`` / ``report-unmigrated`` (their own tuples already catch the base).
# --------------------------------------------------------------------------- #

_FAULT_TEXT = "(assert violation); see the server log"
_SWEEP_DATABASE = "lore_adm_fault_sweep_never_connected"


def _subparsers_action(
    parser: argparse.ArgumentParser,
) -> argparse._SubParsersAction[argparse.ArgumentParser]:  # noqa: SLF001 - argparse has no public accessor
    """The parser's ONE subcommand action — the verb domain's source of truth."""
    actions = [
        action
        for action in parser._actions  # noqa: SLF001 - argparse has no public accessor
        if isinstance(action, argparse._SubParsersAction)  # noqa: SLF001
    ]
    assert len(actions) == 1, f"lore-adm must declare exactly one subcommand action: {actions!r}"
    return actions[0]


def _derived_verbs() -> list[str]:
    """∀ verb ∈ ``build_parser()``'s subparser choices — DERIVED, never a list."""
    return sorted(_subparsers_action(p_module.build_parser()).choices)


#: Options whose VALID domain production validates before any I/O (am-37 §13 C: ``--table`` against
#: ``_MIGRATE_VALID_TABLES``). The minimal VALID argv takes a member of that production domain — a placeholder
#: would be refused by the validator before the injected fault is reached, and the sweep would prove nothing.
_VALIDATED_OPTION_DOMAINS: dict[str, str] = {"table": "_MIGRATE_VALID_TABLES"}


def _option_argv(action: argparse.Action) -> list[str]:
    """The minimal VALID argv satisfying one option: the flag alone for a zero-arg flag; else the flag and
    its first declared choice, or the first member of a production-validated domain, or a placeholder the
    verb never reads (the injected fault fires first)."""
    flag = action.option_strings[0]
    if action.nargs == 0:
        return [flag]
    if action.choices:
        value = str(next(iter(action.choices)))
    elif action.dest in _VALIDATED_OPTION_DOMAINS:
        value = str(getattr(p_module, _VALIDATED_OPTION_DOMAINS[action.dest])[0])
    else:
        value = "x@example.com"
    return [flag, value]


def _minimal_argv(verb: str) -> list[str]:
    """The minimal VALID argv for ``verb``, DERIVED from its own subparser: every required option,
    one member of every required mutually-exclusive group, every mandatory positional."""
    subparser = _subparsers_action(p_module.build_parser()).choices[verb]
    groups = subparser._mutually_exclusive_groups  # noqa: SLF001 - argparse has no public accessor
    grouped = {id(action) for group in groups for action in group._group_actions}  # noqa: SLF001
    argv = [verb]
    for action in subparser._actions:  # noqa: SLF001 - argparse has no public accessor
        if isinstance(action, argparse._HelpAction) or id(action) in grouped:  # noqa: SLF001
            continue
        if not action.option_strings:
            if action.nargs not in ("?", "*"):
                argv.append(str(next(iter(action.choices))) if action.choices else "x")
        elif action.required:
            argv += _option_argv(action)
    for group in groups:
        if group.required:
            argv += _option_argv(group._group_actions[0])  # noqa: SLF001
    return argv


class _ScriptedStore:
    """The one fake every lore-adm store factory returns: ``ensure_ready`` raises a fresh fault
    from ``fault`` (or readies when ``fault`` is None); ``list`` serves an empty store; every call
    is recorded so the pin can prove the injection was REACHED and every built store CLOSED."""

    def __init__(self, name: str, fault: Any, calls: list[str]) -> None:
        self._name = name
        self._fault = fault
        self._calls = calls
        calls.append(f"{name}.built")

    async def ensure_ready(self) -> None:
        self._calls.append(f"{self._name}.ensure_ready")
        if self._fault is not None:
            raise self._fault(_FAULT_TEXT)

    async def list(self) -> list[Any]:
        return []

    async def close(self) -> None:
        self._calls.append(f"{self._name}.close")


def _run_verb_against(
    verb: str,
    fault: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> tuple[str, str, str, list[str]]:
    """Invoke ``main`` for ``verb`` with every store factory scripted. Returns
    ``(outcome, stdout, stderr, calls)`` where ``outcome`` is ``"rc=<n>"``, or
    ``"ESCAPED <Class>: <text>"`` when the fault left ``main`` as a traceback, or
    ``"ARGV <code>"`` when the DERIVED argv failed to parse (a harness defect, named as such)."""
    calls: list[str] = []
    monkeypatch.setattr(
        p_module, "build_principal_store", lambda _c: _ScriptedStore("principal", fault, calls)
    )
    monkeypatch.setattr(p_module, "build_keep_store", lambda _c: _ScriptedStore("keep", fault, calls))
    monkeypatch.setattr(
        pk_module, "build_principal_key_store", lambda _c: _ScriptedStore("key", fault, calls)
    )
    config_path = tmp_path / "lore.yaml"
    payload = _config_payload(database=_SWEEP_DATABASE)
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    argv = ["--config", str(config_path), *_minimal_argv(verb)]
    try:
        outcome = f"rc={p_module.main(argv)}"
    except SystemExit as error:
        outcome = f"ARGV {error.code}"
    except Exception as error:  # noqa: BLE001 - an escaping fault IS the traceback fate this pin catches
        outcome = f"ESCAPED {type(error).__name__}: {error}"
    captured = capsys.readouterr()
    return outcome, captured.out, captured.err, calls


def _assert_laundered(verb: str, outcome: str, out: str, err: str, calls: list[str]) -> None:
    assert not outcome.startswith("ARGV"), (
        f"{verb}: the DERIVED minimal argv failed to parse ({outcome}) — a harness defect, not a verdict; "
        f"extend `_minimal_argv` for this verb's parser shape. stderr={err!r}"
    )
    assert any(call.endswith(".ensure_ready") for call in calls), (
        f"{verb}: the injected fault was never REACHED (no ensure_ready call) — the pin proves nothing: "
        f"{calls}"
    )
    assert outcome == "rc=1", (
        f"{verb}: a store/domain fault must be `{p_module._CLI_PROG}: <error>` on stderr + exit 1 — never a "
        f"traceback, never a success (63c am-37 §11 item 1); got {outcome!r}"
    )
    first_line = err.splitlines()[0] if err else ""
    assert first_line.startswith(f"{p_module._CLI_PROG}: ") and _FAULT_TEXT in first_line, (
        f"{verb}: stderr's first line must be the laundered INJECTED fault; stderr={err!r}"
    )
    assert out == "", f"{verb}: a failed verb must print nothing to stdout; stdout={out!r}"
    assert "Traceback" not in out + err, f"{verb}: a traceback reached the operator: {out + err!r}"
    built = sorted(call.removesuffix(".built") for call in calls if call.endswith(".built"))
    closed = sorted(call.removesuffix(".close") for call in calls if call.endswith(".close"))
    assert built == closed, (
        f"{verb}: every store the verb built must be closed on the fault path "
        f"(built {built}, closed {closed})"
    )


class TestEveryLoreAdmVerbLaundersAStoreFault:
    """63c am-37 §11 item 4 — the GENERATED completeness pin over the DERIVED verb set."""

    @pytest.mark.parametrize("verb", _derived_verbs())
    def test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1(
        self, verb: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """RED at fix3 r2 for every principal/key verb and every keep verb (the fault escapes as a
        traceback); GREEN once the one handler at ``_dispatch`` catches ``SurrealStoreError``."""
        outcome, out, err, calls = _run_verb_against(
            verb, TxnDomainRejectionError, tmp_path, monkeypatch, capsys
        )
        _assert_laundered(verb, outcome, out, err, calls)

    @pytest.mark.parametrize("verb", _derived_verbs())
    def test_CONTROL_a_transport_fault_takes_the_same_fate(
        self, verb: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """POSITIVE CONTROL: the already-laundered class, through the SAME harness, the SAME argv,
        the SAME injection point, takes the same fate — GREEN at fix3 r2 AND after. So the domain-
        rejection pin's RED is about the fault CLASS, never about the fixture."""
        outcome, out, err, calls = _run_verb_against(
            verb, SurrealConnectionError, tmp_path, monkeypatch, capsys
        )
        _assert_laundered(verb, outcome, out, err, calls)

    def test_CONTROL_a_succeeding_verb_exits_0_with_empty_stderr(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """NEGATIVE CONTROL: the same harness with NO fault does not manufacture a failure — ``list``
        over an empty store readies, runs, exits 0, and prints nothing (Unix: silent on success)."""
        outcome, out, err, calls = _run_verb_against("list", None, tmp_path, monkeypatch, capsys)
        assert outcome == "rc=0", (
            f"a faultless verb must succeed through the harness; got {outcome!r} {err!r}"
        )
        assert err == "" and out == "", f"a faultless empty `list` prints nothing: out={out!r} err={err!r}"
        assert "principal.ensure_ready" in calls, f"the success path must have readied the store: {calls}"

    def test_the_derived_verb_set_is_not_vacuous(self) -> None:
        """The derivation must reach every verb the dispatcher routes (both handler tables and the
        two named branches) — a derivation that shrank would silently shrink the sweep."""
        routed = {
            *p_module._VERB_HANDLERS,  # noqa: SLF001
            *p_module._KEEP_VERB_HANDLERS,  # noqa: SLF001
            "migrate-governed",
            "report-unmigrated",
        }
        missing = routed - set(_derived_verbs())
        assert not missing, f"the derived verb set misses routed verbs: {sorted(missing)}"


# --------------------------------------------------------------------------- #
# 63c amendment 37 §13 A (commit ``ce2b4bd``) — the lore-adm error line TEACHES THE CAUSE, and the
# served pointer RESOLVES. PROPERTY: *every served pointer resolves to a surface the consumer can open,
# and a fault line names its cause.*
#   * the fault classes are the §11 tuple, DERIVED from ``_dispatch``'s one ``except`` (never a list);
#   * the pointer: the seam's rejection message says "see the server log"; in lore-adm the server log IS
#     stderr (``main()`` installs a stderr handler on the ``loremaster`` logger rendering the seam's
#     ``extra`` values), so the ``engine_error`` text the seam logs must reach the operator's stderr.
# RED at fix5 (``5f2d7c43``): the handler prints ``{error}`` alone (the cause is hidden in ``__cause__``)
# and no handler renders the seam's log record into stderr.
# --------------------------------------------------------------------------- #

_CAUSE_TEXT = "unique violation — an index entry for this value already exists (cause-line probe)"
_ENGINE_TEXT = "Database index `principal_email` already contains 'engine-text-probe@example.com'"
_OUTER_TEXT = "could not ready the store (outer-line probe)"
_REJECTION_LABEL = "principal.query.rejected"
_SEAM_LOGGER = "loremaster.principals"
_TXN_SOURCE = Path(p_module.__file__).resolve().parent / "store" / "_txn.py"
_RAISE_LADDER = "_raise_attempt_failure"


def _handler_fault_names() -> list[str]:
    """The §11 tuple, DERIVED: the element names of ``_dispatch``'s ONE tuple-typed ``except``."""
    tree = ast.parse(Path(p_module.__file__).read_text(encoding="utf-8"))
    dispatch = next(
        node for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef) and node.name == "_dispatch"
    )
    handlers = [
        handler
        for handler in ast.walk(dispatch)
        if isinstance(handler, ast.ExceptHandler) and isinstance(handler.type, ast.Tuple)
    ]
    assert len(handlers) == 1, f"_dispatch must own exactly ONE tuple except (am-37 §11): {len(handlers)}"
    handler_type = handlers[0].type
    assert isinstance(handler_type, ast.Tuple)
    return [ast.unparse(element) for element in handler_type.elts]


def _resolve_fault_class(name: str) -> type[Exception]:
    """Resolve a tuple member through the ``from … import`` that binds it in ``principals.py`` (else the
    module's own namespace, else builtins)."""
    tree = ast.parse(Path(p_module.__file__).read_text(encoding="utf-8"))
    bound_in = {
        alias.asname or alias.name: node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
        for alias in node.names
    }
    import builtins  # noqa: PLC0415 - the one fallback namespace

    module = importlib.import_module(bound_in[name]) if name in bound_in else p_module
    resolved = getattr(module, name, None) or getattr(builtins, name)
    assert isinstance(resolved, type) and issubclass(resolved, Exception), name
    return resolved


def _seam_extra_keys() -> list[str]:
    """The ``extra`` keys the seam's rejection record carries — DERIVED from the ``logger.error(label,
    extra={...})`` call in :func:`loremaster.store._txn._raise_attempt_failure`."""
    tree = ast.parse(_TXN_SOURCE.read_text(encoding="utf-8"))
    ladder = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == _RAISE_LADDER
    )
    for call in ast.walk(ladder):
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == "error":
            for keyword in call.keywords:
                if keyword.arg == "extra" and isinstance(keyword.value, ast.Dict):
                    return [
                        str(key.value) for key in keyword.value.keys if isinstance(key, ast.Constant)
                    ]
    raise AssertionError(f"no logger.error(extra=...) found in {_RAISE_LADDER}")


def _chained_fault(fault_class: type[Exception]) -> Any:
    """A fault factory: ``fault_class(_OUTER_TEXT)`` with ``__cause__`` = a typed store rejection."""

    def factory(_text: str) -> Exception:
        error = fault_class(_OUTER_TEXT)
        error.__cause__ = TxnDomainRejectionError(_CAUSE_TEXT)
        return error

    return factory


def _seam_rejection(_text: str) -> Exception:
    """Emit the seam's own rejection record (label + the DERIVED extra keys) on a ``loremaster`` logger,
    then return the seam's own raised error — what a real engine rejection produces at ``ensure_ready``."""
    from loremaster.store import _txn  # noqa: PLC0415 - the seam's private constructor + hint

    values = {"url": "ws://unit", "error_class": _txn._ERROR_CLASS_UNSPECIFIED, "engine_error": _ENGINE_TEXT}
    extra = {key: values[key] for key in _seam_extra_keys()}
    logging.getLogger(_SEAM_LOGGER).error(_REJECTION_LABEL, extra=extra)
    error = _txn._domain_rejection_error(
        extra["error_class"],
        f"SurrealDB principal query rejected against 'ws://unit' ({extra['error_class']}); "
        f"{_txn._SERVER_LOG_HINT}",
    )
    error.__cause__ = RuntimeError(_ENGINE_TEXT)
    return error


class TestTheLoreAdmFaultLineTeachesItsCause:
    """63c am-37 §13 A — the GENERATED pin over the §11 tuple × the DERIVED verb set."""

    @pytest.mark.parametrize("fault_name", _handler_fault_names())
    @pytest.mark.parametrize("verb", _derived_verbs())
    def test_the_cause_of_every_laundered_fault_is_printed(
        self,
        verb: str,
        fault_name: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        fault = _chained_fault(_resolve_fault_class(fault_name))
        outcome, out, err, calls = _run_verb_against(verb, fault, tmp_path, monkeypatch, capsys)
        assert outcome == "rc=1", f"{verb}/{fault_name}: {outcome!r} err={err!r}"
        assert "Traceback" not in out + err, f"{verb}/{fault_name}: a traceback reached the operator: {err!r}"
        lines = err.splitlines()
        outer = [index for index, line in enumerate(lines) if line.startswith(f"{p_module._CLI_PROG}: ")]
        assert outer and _OUTER_TEXT in lines[outer[0]], (
            f"{verb}/{fault_name}: the `lore-adm: <error>` line must be unchanged; stderr={err!r}"
        )
        caused = [line for line in lines[outer[0] + 1 :] if "caused by" in line and _CAUSE_TEXT in line]
        assert caused, (
            f"{verb}/{fault_name}: the cause (`__cause__`) must be printed on a `caused by` line after the "
            f"lore-adm line (am-37 §13 A ii); stderr={err!r}"
        )
        assert any(call.endswith(".ensure_ready") for call in calls), f"injection never reached: {calls}"

    @pytest.mark.parametrize("verb", _derived_verbs())
    def test_the_server_log_pointer_resolves_to_stderr(
        self, verb: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A raw domain rejection: the lore-adm line says "see the server log"; the seam's ``engine_error``
        (and ``error_class``) must be ON stderr, so the pointer resolves (am-37 §13 A i)."""
        from loremaster.store import _txn  # noqa: PLC0415

        outcome, out, err, _calls = _run_verb_against(verb, _seam_rejection, tmp_path, monkeypatch, capsys)
        assert outcome == "rc=1" and "Traceback" not in out + err, f"{verb}: {outcome!r} {err!r}"
        assert _txn._SERVER_LOG_HINT in err, f"{verb}: the lore-adm line must still carry the hint: {err!r}"
        # The RECORD itself must reach stderr — its label line carrying the ``engine_error`` / ``error_class``
        # extras. Checking the engine text anywhere on stderr would be satisfied by the `caused by` line
        # alone (A ii), so it could not see A (i) missing (mutation-proven 2026-09-30, M-A2 v2).
        record_lines = [line for line in err.splitlines() if _REJECTION_LABEL in line]
        assert record_lines, (
            f"{verb}: `{_txn._SERVER_LOG_HINT}` points at nothing — the seam's log record never reached "
            f"stderr; stderr={err!r}"
        )
        assert _ENGINE_TEXT in record_lines[0] and _txn._ERROR_CLASS_UNSPECIFIED in record_lines[0], (
            f"{verb}: the log record must render its engine_error and error_class extras: {record_lines[0]!r}"
        )

    def test_repeated_invocations_do_not_duplicate_the_log_line(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """LIFECYCLE: ``main()`` installing a handler per call must not accumulate — each invocation's stderr
        carries the seam's log RECORD (its label line) exactly ONCE (a leaked handler would print it twice, or
        write to a previous call's dead stream). The label is counted, not the engine text: the engine text
        legitimately appears twice — on the log record AND on the `caused by` line."""
        for _attempt in range(2):
            _outcome, _out, err, _calls = _run_verb_against(
                "list", _seam_rejection, tmp_path, monkeypatch, capsys
            )
            assert err.count(_REJECTION_LABEL) == 1, f"the log record must appear once per call: {err!r}"
            assert "Logging error" not in err, f"a leaked handler wrote to a dead stream: {err!r}"

    def test_the_seam_extra_keys_the_cli_renders_are_derived_and_non_vacuous(self) -> None:
        keys = _seam_extra_keys()
        assert {"error_class", "engine_error"} <= set(keys), keys


# F-13: no wrap context over-claims a cause the handler now prints itself.
_WRAP_SEAM = "wrap_store_rejection"
_OVER_CLAIM = "already"


def _wrap_contexts() -> list[str]:
    """``<file>::<function>`` ∀ ``wrap_store_rejection(<error>, <context>)`` call in the package, DERIVED."""
    package = Path(p_module.__file__).resolve().parent
    sites: list[str] = []
    for path in sorted(package.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for function in ast.walk(tree):
            if not isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            for call in ast.walk(function):
                is_wrap = isinstance(call, ast.Call) and getattr(call.func, "id", None) == _WRAP_SEAM
                if is_wrap and isinstance(call, ast.Call) and len(call.args) > 1:
                    sites.append(f"{path.relative_to(package)}::{function.name}::{call.lineno}")
    return sites


def _context_text(site: str) -> str:
    package = Path(p_module.__file__).resolve().parent
    file_name, _function, line = site.split("::")
    tree = ast.parse((package / file_name).read_text(encoding="utf-8"))
    call = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and getattr(node.func, "id", None) == _WRAP_SEAM
        and node.lineno == int(line)
    )
    context = call.args[1]
    if isinstance(context, ast.JoinedStr):
        return "".join(str(part.value) for part in context.values if isinstance(part, ast.Constant))
    return ast.unparse(context)


class TestNoWrapContextOverClaimsItsCause:
    """63c am-37 §13 A (F-13): the wrap contexts are NEUTRAL ("could not create principal …") — the typed
    cause prints itself on the `caused by` line, so no context may assert a cause ("already exists" /
    "already bound"). RED at fix5 on exactly PrincipalStore.create, PrincipalStore.set_subject and
    PrincipalKeyStore.mint."""

    @pytest.mark.parametrize("site", _wrap_contexts())
    def test_the_wrap_context_names_the_operation_not_a_guessed_cause(self, site: str) -> None:
        text = _context_text(site)
        assert _OVER_CLAIM not in text, f"{site}: the wrap context over-claims its cause: {text!r}"

    def test_the_context_sweep_is_not_vacuous(self) -> None:
        assert len(_wrap_contexts()) >= 10, _wrap_contexts()


# --------------------------------------------------------------------------- #
# 63c amendment 37 §13 C (commit ``ce2b4bd``) — honest labels.
#   * F-4: the result field, the receipt KEY and the stderr sentence are RENAMED to what the count measures:
#     ``messages_left_unmigrated`` (rows still un-migrated AFTER the backfill — a superset of
#     "unsound sender");
#     the retired name survives in NO served source (bare-pattern scan of the package).
#   * N-3 / F-15: ``--table`` help for EVERY verb that takes ``--table`` (DERIVED from the parser) is derived
#     from ``_MIGRATE_VALID_TABLES``; an invalid ``--table`` is refused BEFORE any I/O (zero store calls).
# RED at fix5 (``5f2d7c43``): the old name everywhere; help says "63a supports: memory"; report-unmigrated
# never validates and migrate-governed validates only after readying its stores.
# --------------------------------------------------------------------------- #

_RENAMED_FIELD = "messages_left_unmigrated"
_RETIRED_FIELD = "unsound_sender_messages"
_LEFTOVER_SENTENCE = "remain un-migrated after the backfill"
_INVALID_TABLE = "not_a_governed_table"


class _HandleStore(_ScriptedStore):
    """A scripted store that can also back a driver ``StoreHandle`` (the migrate verb builds one)."""

    _url = "ws://unit"

    async def _ensure_connection(self) -> None:
        self._calls.append(f"{self._name}._ensure_connection")

    async def _drop_connection(self, _connection: Any) -> None:
        self._calls.append(f"{self._name}._drop_connection")


def _table_verbs() -> list[str]:
    """∀ verb whose subparser takes ``--table`` — DERIVED from ``build_parser()``."""
    choices = _subparsers_action(p_module.build_parser()).choices
    return sorted(
        verb
        for verb, subparser in choices.items()
        if any("--table" in action.option_strings for action in subparser._actions)  # noqa: SLF001
    )


class TestHonestLabels:
    """63c am-37 §13 C."""

    def test_the_result_field_is_named_for_what_it_measures(self) -> None:
        from dataclasses import fields  # noqa: PLC0415

        from loremaster.governed import MigrateGovernedResult  # noqa: PLC0415

        names = {item.name for item in fields(MigrateGovernedResult)}
        assert _RENAMED_FIELD in names and _RETIRED_FIELD not in names, sorted(names)

    def test_the_retired_name_survives_in_no_served_source(self) -> None:
        package = Path(p_module.__file__).resolve().parent
        hits = [
            f"{path.relative_to(package)}:{number}"
            for path in sorted(package.rglob("*.py"))
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
            if _RETIRED_FIELD in line
        ]
        assert not hits, f"the retired label `{_RETIRED_FIELD}` is still served/taught at: {hits}"

    @pytest.mark.parametrize("leftover", [0, 3])
    def test_the_receipt_key_and_the_stderr_sentence_carry_the_new_name(
        self,
        leftover: int,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from loremaster.governed import MigrateGovernedResult  # noqa: PLC0415

        result_class: Any = MigrateGovernedResult
        forged = result_class(
            table="message",
            scanned=5,
            backfilled=5 - leftover,
            already_migrated=0,
            refused=False,
            table_defined=True,
            **{_RENAMED_FIELD: leftover},
        )

        async def _forged_migrate(**_kwargs: Any) -> Any:
            return forged

        calls: list[str] = []
        monkeypatch.setattr(
            p_module, "build_principal_store", lambda _c: _HandleStore("principal", None, calls)
        )
        monkeypatch.setattr(p_module, "build_keep_store", lambda _c: _HandleStore("keep", None, calls))
        monkeypatch.setattr(p_module, "migrate_governed", _forged_migrate)
        config_path = tmp_path / "lore.yaml"
        config_path.write_text(yaml.safe_dump(_config_payload(database=_SWEEP_DATABASE)), encoding="utf-8")
        rc = p_module.main(["--config", str(config_path), "migrate-governed", "--table", "message"])
        captured = capsys.readouterr()
        assert rc == 0, (rc, captured.err)
        assert f"{_RENAMED_FIELD}={leftover}" in captured.out, captured.out
        assert _RETIRED_FIELD not in captured.out + captured.err, captured
        assert (_LEFTOVER_SENTENCE in captured.err) is (leftover > 0), (
            f"the stderr sentence is DERIVED from the field, iff > 0: {captured.err!r}"
        )

    @pytest.mark.parametrize("verb", _table_verbs())
    def test_the_table_help_is_derived_from_the_valid_set(self, verb: str) -> None:
        subparser = _subparsers_action(p_module.build_parser()).choices[verb]
        (table_action,) = [a for a in subparser._actions if "--table" in a.option_strings]  # noqa: SLF001
        expected = ", ".join(p_module._MIGRATE_VALID_TABLES)  # noqa: SLF001
        assert expected in (table_action.help or ""), (
            f"{verb}: --table help must name the valid set {expected!r}: {table_action.help!r}"
        )

    @pytest.mark.parametrize("verb", _table_verbs())
    def test_an_invalid_table_is_refused_before_any_store_call(
        self, verb: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        calls: list[str] = []
        monkeypatch.setattr(
            p_module, "build_principal_store", lambda _c: _HandleStore("principal", None, calls)
        )
        monkeypatch.setattr(p_module, "build_keep_store", lambda _c: _HandleStore("keep", None, calls))
        monkeypatch.setattr(
            pk_module, "build_principal_key_store", lambda _c: _HandleStore("key", None, calls)
        )
        config_path = tmp_path / "lore.yaml"
        config_path.write_text(yaml.safe_dump(_config_payload(database=_SWEEP_DATABASE)), encoding="utf-8")
        try:
            outcome = f"rc={p_module.main(['--config', str(config_path), verb, '--table', _INVALID_TABLE])}"
        except SystemExit as error:
            outcome = f"SystemExit {error.code}"
        except Exception as error:  # noqa: BLE001 - an escaping fault is a finding, named
            outcome = f"ESCAPED {type(error).__name__}: {error}"
        err = capsys.readouterr().err
        io_calls = [call for call in calls if not call.endswith((".built", ".close"))]
        assert not io_calls, (
            f"{verb}: an invalid --table reached the store ({io_calls}) — "
            "validate BEFORE any I/O"
        )
        assert outcome in ("rc=1", "SystemExit 2"), f"{verb}: an invalid --table must be refused: {outcome!r}"
        assert _INVALID_TABLE in err, f"{verb}: the refusal must name the rejected table: {err!r}"

    def test_the_table_verb_population_is_derived_and_not_vacuous(self) -> None:
        assert {"migrate-governed", "report-unmigrated"} <= set(_table_verbs()), _table_verbs()
