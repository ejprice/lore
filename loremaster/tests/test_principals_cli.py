"""Contract — packet 49, the admin CLI (``python -m loremaster.principals``).

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

import ast
import asyncio
import re
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
import yaml
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
        """The CLI is invoked ``python -m loremaster.principals`` (design §F6), so the
        parser ``prog`` is exactly that — GREEN against the stub (a structural anchor)."""
        assert p_module.build_parser().prog == "loremaster.principals"

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


class TestMainGuardIsLast:
    def test_main_guard_is_the_last_top_level_statement(self) -> None:
        """``principals.py`` runs as ``python -m loremaster.principals``, so anything after
        the ``__main__`` guard would not execute (main() runs first) — the def-after-guard
        NameError class. ``principals.py`` needs its OWN pin (``test_server_entrypoint`` /
        ``test_scout`` scan per file; there is no global scan)."""
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
