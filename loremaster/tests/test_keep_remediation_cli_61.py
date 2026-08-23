"""Contract — packet 61a-w1, the ``lore-adm`` delete-refusal + keep-remediation CLI verbs.

Written by ``contract-61a-w1`` (2026-08-23). The builder builds FROM this; it writes NO
production code. *Every "RED at HEAD" claim is scoped to the tree at ``84d20a3``: the two new
verbs do not parse (``build_parser`` has no ``set-keeper`` / ``delete-keep``) and
``lore-adm delete`` of a keeper SUCCEEDS (no refusal), so each behavioural pin reddens.*

SPEC: ``docs/design/2026-08-22-packet61-pdp-audit-rulings.md`` §FR-4. The CLI surface of the
refuse-while-keeping ruling + its two remediation verbs, flat subcommands on the EXISTING
``lore-adm`` parser (``loremaster.principals:main``):

    delete       --email <e>                        # EXISTING verb — now REFUSES a keeper (exit 1)
    set-keeper   --keep <id> --new-keeper <email>   # NEW: set a keep's keeper (KeepStore.set_keeper)
    delete-keep  --keep <id>                        # NEW: delete a keep + its member_of (delete_keep)

The refusal launders through ``_dispatch``'s EXISTING ``except PrincipalStoreError`` (the new
``PrincipalHasKeepsError`` subclasses it) to a ``lore-adm:`` stderr line + exit 1; the two new
keep verbs route through ``_dispatch_keep`` (KeepStore verbs), whose ``except KeepStoreError``
launders ``KeepNotFoundError`` / ghost refusals the same way. Every verb executes directly
(no ``--execute`` / dry-run, struck 2026-08-20); silent on success, loud on failure.

⚠ TEST-ENV-FICTION (#401 rider, standing): every stderr assertion uses ``"lore-adm:" in err``,
NEVER ``err.startswith(...)`` — in production a ``<label>.rejected`` log line (e.g.
``principal.query.rejected`` / ``keep.query.rejected``) precedes the teaching line on stderr;
pytest's caplog strips it, so ``startswith`` is green-in-suite / false-in-prod.

⚠ FROZEN INTERFACE (a contract-author decision, flagged in REPORT-contract-61a-w1.md): the
verb names ``set-keeper`` / ``delete-keep`` and their ``--keep`` / ``--new-keeper`` options
(D1 ruling, FR-4 addendum: CLI verb ``set-keeper`` + flag ``--new-keeper`` stay; the STORE
method is ``set_keeper``, renamed from ``reassign_keeper``).

CREDS-FREE (LEAD RULING #6): the keep verbs resolve ONLY the surreal block via
``load_surreal_only_config`` (shared ``_dispatch``), never the Anthropic key.

LIVE store: ws://127.0.0.1:18000 (NEVER :18500). Per-test unique database, reaped on exit.
NO skip marker — an unreachable store is a LOUD failure, not a skip.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
import yaml
from _enforced_relations_scaffold import ghost_id
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    drop_database,
    make_env,
    surreal_password,
    surreal_url,
    surreal_user,
    unique_database,
)
from loremaster.keeps import KeepStore
from loremaster.principal_keys import PrincipalKeyStore
from loremaster.principals import PrincipalStore
from loremaster.store.surreal_schema import KEEP_TABLE

from loremaster import principals as p_module

_USER_ENV = "LORE_KEEP_REMED_CLI_TEST_SURREAL_USER"
_PASS_ENV = "LORE_KEEP_REMED_CLI_TEST_SURREAL_PASS"
_ANTHROPIC_ENV = "LORE_KEEP_REMED_CLI_TEST_ANTHROPIC"

_KEEPER = "keeper@example.com"
_SUCCESSOR = "successor@example.com"
_MEMBER = "member@example.com"
_LONER = "loner@example.com"
_UNKNOWN = "nobody@example.com"

# The two NEW verbs, as constants so a countermand renames them in one place.
_SET_KEEPER = "set-keeper"
_DELETE_KEEP = "delete-keep"


@pytest.fixture(autouse=True)
def _cli_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Export the REAL spike-store creds by the env-var NAMEs the fixture config references,
    plus a dummy Anthropic key (never used by these verbs — the creds-free path)."""
    monkeypatch.setenv(_USER_ENV, surreal_user())
    monkeypatch.setenv(_PASS_ENV, surreal_password().get_secret_value())
    monkeypatch.setenv(_ANTHROPIC_ENV, "unused-by-the-keep-cli")


def _config_payload(*, database: str) -> dict[str, Any]:
    """A minimal VALID lore.yaml payload pointed at the spike store + a unique database
    (self-contained — cloned from ``test_keeps_cli``)."""
    return {
        "schema_version": 1,
        "anthropic": {"api_key_env": _ANTHROPIC_ENV},
        "project": {"slug": "keep_remed_cli_test", "root": "."},
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


class _CliEnv:
    def __init__(self, config_path: Path, env: SurrealEnv) -> None:
        self.config_path = config_path
        self.env = env

    def argv(self, *args: str) -> list[str]:
        return ["--config", str(self.config_path), *args]


@pytest_asyncio.fixture()
async def cli_env(tmp_path: Path) -> AsyncIterator[_CliEnv]:
    """A written lore.yaml pointed at a per-test unique spike-store database, reaped on exit."""
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    config_path = tmp_path / "lore.yaml"
    config_path.write_text(yaml.safe_dump(_config_payload(database=env.database)), encoding="utf-8")
    try:
        yield _CliEnv(config_path, env)
    finally:
        await drop_database(env)


async def _run_cli(argv: list[str]) -> int:
    """Invoke ``main`` OFF the test's running event loop (the ``test_keeps_cli`` idiom).

    ⚠ Also catches ``SystemExit`` and returns its code: on HEAD a NEW verb
    (``set-keeper`` / ``delete-keep``) is an unknown subcommand, so ``parse_args`` raises
    ``SystemExit(2)`` — turning that into ``rc == 2`` gives the behavioural pins a CLEAN RED
    ("the verb is unbuilt") instead of a raw ``SystemExit`` leaking through the await."""

    def _call() -> int:
        try:
            return p_module.main(argv)
        except SystemExit as exit_error:
            code = exit_error.code
            return code if isinstance(code, int) else (0 if code is None else 1)

    return await asyncio.to_thread(_call)


@asynccontextmanager
async def _keep_store_for(env: SurrealEnv) -> AsyncIterator[tuple[KeepStore, PrincipalStore]]:
    """A ready KeepStore + PrincipalStore on the test's DB, for reading the CLI's writes back
    through the STORE MAPPERS (never a raw column read). ``principal`` readied FIRST."""
    principal_store = PrincipalStore(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    keep_store = KeepStore(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    await principal_store.ensure_ready()
    await keep_store.ensure_ready()
    try:
        yield keep_store, principal_store
    finally:
        await keep_store.close()
        await principal_store.close()


async def _add(cli_env: _CliEnv, email: str) -> None:
    rc = await _run_cli(cli_env.argv("add", "--email", email))
    assert rc == 0, f"the `add` verb failed for {email!r} (rc={rc})"


async def _create_keep(
    cli_env: _CliEnv,
    capsys: pytest.CaptureFixture[str],
    *,
    keep_type: str,
    keeper: str,
    name: str | None = None,
) -> str:
    """Run ``create-keep`` and return the single printed keep id (drains capsys first)."""
    argv = ["create-keep", "--type", keep_type, "--keeper", keeper]
    if name is not None:
        argv += ["--name", name]
    capsys.readouterr()
    rc = await _run_cli(cli_env.argv(*argv))
    assert rc == 0, f"create-keep --type {keep_type} failed (rc={rc})"
    return capsys.readouterr().out.strip()


def _bare(record_id: str) -> str:
    return record_id.partition(":")[2] or record_id


# =========================================================================== #
# Parser surface (offline). RED at HEAD — the new verbs are not in build_parser yet.
# =========================================================================== #


class TestNewVerbParserSurface:
    @pytest.mark.parametrize(
        "argv",
        [
            [_SET_KEEPER, "--keep", "keep:1", "--new-keeper", _SUCCESSOR],
            [_DELETE_KEEP, "--keep", "keep:1"],
        ],
    )
    def test_each_new_verb_parses_with_its_required_args(self, argv: list[str]) -> None:
        """⚠ RED at HEAD (unknown subcommand → SystemExit). Each new verb parses with its
        required args and carries a dispatchable ``command`` marker."""
        args = p_module.build_parser().parse_args(argv)
        assert getattr(args, "command", None) == argv[0], f"no dispatchable verb marker: {vars(args)!r}"

    @pytest.mark.parametrize(
        "argv",
        [
            [_SET_KEEPER, "--new-keeper", _SUCCESSOR],  # missing --keep
            [_SET_KEEPER, "--keep", "keep:1"],  # missing --new-keeper
            [_DELETE_KEEP],  # missing --keep
        ],
    )
    def test_a_new_verb_missing_a_required_arg_exits(self, argv: list[str]) -> None:
        """A required arg is enforced at parse time (SystemExit). On HEAD the verb is unknown
        (also SystemExit) — this pin GREENS at HEAD by coincidence; the surface pins above
        carry the RED. Kept because it guards the required-arg surface for good."""
        with pytest.raises(SystemExit):
            p_module.build_parser().parse_args(argv)

    def test_the_new_verbs_are_registered_in_the_keep_handler_table(self) -> None:
        """⚠ RED at HEAD. Both verbs are KeepStore verbs — they must be in
        ``_KEEP_VERB_HANDLERS`` so ``_dispatch`` routes them to ``_dispatch_keep`` (and its
        ``KeepStoreError`` launder), NOT to the principal path. A build that wired them into
        ``_VERB_HANDLERS`` (the principal table) would mis-launder their errors."""
        handlers = getattr(p_module, "_KEEP_VERB_HANDLERS", {})
        assert _SET_KEEPER in handlers and _DELETE_KEEP in handlers, (
            f"the new keep verbs must be registered in _KEEP_VERB_HANDLERS; got {sorted(handlers)!r}"
        )


# =========================================================================== #
# `lore-adm delete` now REFUSES a keeper (exit 1). RED at HEAD (no refusal).
# =========================================================================== #


class TestDeleteVerbRefusesAKeeper:
    async def test_delete_of_a_keeper_exits_1_names_the_keep_and_deletes_nothing(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """⚠ RED at HEAD. ``lore-adm delete`` of a principal who keeps a keep exits 1 with a
        LOUD ``lore-adm:`` stderr line NAMING the kept keep id; the principal + keep survive.
        On HEAD the delete succeeds (rc 0, keeper gone, keep.keeper dangles) → reddens."""
        await _add(cli_env, _KEEPER)
        keep_id = await _create_keep(cli_env, capsys, keep_type="team", keeper=_KEEPER, name="crew")
        capsys.readouterr()
        rc = await _run_cli(cli_env.argv("delete", "--email", _KEEPER))
        assert rc == 1, "deleting a keeper must be a loud non-zero exit (PrincipalHasKeepsError laundered)"
        err = capsys.readouterr().err
        assert "lore-adm:" in err, f"the refusal must be a loud `lore-adm:` stderr line: {err!r}"
        assert _bare(keep_id) in err, f"the refusal must NAME the kept keep id {_bare(keep_id)!r}: {err!r}"
        async with _keep_store_for(cli_env.env) as (keep_store, principal_store):
            assert await principal_store.get_by_email(_KEEPER) is not None, "keeper deleted despite refusal"
            assert await keep_store.get_keep(keep_id) is not None, "the kept keep vanished despite refusal"

    async def test_delete_readies_the_keep_slice_on_the_fly_when_the_keep_table_is_absent(
        self, cli_env: _CliEnv
    ) -> None:
        """⚠ THE #131/#107 TEST-ENV-FICTION GUARD (D3 ruling, FR-4 addendum — load-bearing;
        GREEN on HEAD + fix). Ready ONLY the ``principal`` + ``principal_key`` slices
        DIRECTLY — explicitly NOT the keep slice — and create a keeps-nothing principal on
        that store. Then ``lore-adm delete`` must SUCCEED (rc 0): the fixed delete branch
        readies the keep slice ON THE FLY (principal first, member_of ENFORCED), the keep
        count is 0, and the delete proceeds. A build whose delete branch counts keeps but
        never readies the ``keep`` table CRASHES on the absent table here, where every virgin
        FULL-schema fixture stays green — the exact dirty-store blind spot (#131/§1.6): the
        suite mints a virgin DB, but a real ``lore-adm`` run may hit a DB the primary store
        never booted. This proves the no-crash / slice-ready path ONLY — the REFUSE path needs
        a real keep (``TestDeleteVerbRefusesAKeeper``), which a keep-table-less store cannot
        hold. Impl placement (delete branch vs handler) stays the builder's call."""
        # Ready ONLY principal + principal_key — the keep table does NOT exist yet.
        env = cli_env.env
        principal_store = PrincipalStore(
            url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
        )
        key_store = PrincipalKeyStore(
            url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
        )
        await principal_store.ensure_ready()
        await key_store.ensure_ready()
        await principal_store.create(email=_LONER)
        await key_store.close()
        await principal_store.close()
        # The keep table is ABSENT on this DB — the delete must ready it on the fly and proceed.
        rc = await _run_cli(cli_env.argv("delete", "--email", _LONER))
        assert rc == 0, (
            "deleting a keeps-nothing principal on a keep-table-less DB must succeed — the "
            "fixed delete branch readies the keep slice on the fly; count=0; delete proceeds (#131)"
        )
        readback = PrincipalStore(
            url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
        )
        try:
            assert await readback.get_by_email(_LONER) is None, "the loner was not deleted"
        finally:
            await readback.close()


# =========================================================================== #
# set-keeper / delete-keep behaviour (live). RED at HEAD (verbs unbuilt).
# =========================================================================== #


class TestSetKeeperVerb:
    async def test_set_keeper_reassigns_the_keeper(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """⚠ RED at HEAD. ``lore-adm set-keeper`` UPDATEs the keep's keeper to the new
        principal (rc 0, silent); the keep reads back under the successor."""
        await _add(cli_env, _KEEPER)
        await _add(cli_env, _SUCCESSOR)
        keep_id = await _create_keep(cli_env, capsys, keep_type="team", keeper=_KEEPER, name="crew")
        rc = await _run_cli(cli_env.argv(_SET_KEEPER, "--keep", keep_id, "--new-keeper", _SUCCESSOR))
        assert rc == 0, f"set-keeper failed (rc={rc})"
        async with _keep_store_for(cli_env.env) as (keep_store, principal_store):
            keep = await keep_store.get_keep(keep_id)
            successor = await principal_store.get_by_email(_SUCCESSOR)
        assert keep is not None and successor is not None
        assert keep.keeper_id == _bare(successor.id), "set-keeper did not reassign to the successor"

    async def test_set_keeper_to_a_ghost_email_is_loud_and_nonzero(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """⚠ RED at HEAD. An unknown new-keeper email is REFUSED (exit 1, ``lore-adm:``
        stderr) — the ENFORCED-flavoured guard laundered by ``_dispatch_keep``. The keep's
        keeper is UNCHANGED (paired with the success pin — discriminates ghost-refusal from
        refuse-all)."""
        await _add(cli_env, _KEEPER)
        keep_id = await _create_keep(cli_env, capsys, keep_type="team", keeper=_KEEPER, name="crew")
        capsys.readouterr()
        rc = await _run_cli(cli_env.argv(_SET_KEEPER, "--keep", keep_id, "--new-keeper", _UNKNOWN))
        assert rc == 1, "set-keeper to a ghost email must exit 1 (KeepStoreError laundered)"
        assert "lore-adm:" in capsys.readouterr().err, "ghost-keeper refusal must be a loud `lore-adm:` line"
        async with _keep_store_for(cli_env.env) as (keep_store, principal_store):
            keep = await keep_store.get_keep(keep_id)
            keeper = await principal_store.get_by_email(_KEEPER)
        assert keep is not None and keeper is not None and keep.keeper_id == _bare(keeper.id), (
            "a refused set-keeper changed keep.keeper"
        )

    async def test_set_keeper_of_a_ghost_keep_is_loud_and_nonzero(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """⚠ RED at HEAD (#403 BLOCKER). ``lore-adm set-keeper`` on a GHOST ``--keep`` (with a
        REAL ``--new-keeper``) exits 1 with a loud ``lore-adm:`` stderr line NAMING the missing
        keep — the ``KeepNotFoundError`` laundered by ``_dispatch_keep`` (D1/FR-3 ghost-keep is
        LOUD). A build that silently returns rc 0 on a typo'd keep reddens here."""
        await _add(cli_env, _SUCCESSOR)
        ghost = ghost_id(KEEP_TABLE)
        capsys.readouterr()
        rc = await _run_cli(cli_env.argv(_SET_KEEPER, "--keep", ghost, "--new-keeper", _SUCCESSOR))
        assert rc == 1, "set-keeper on a ghost keep must exit 1 (KeepNotFoundError laundered)"
        err = capsys.readouterr().err
        assert "lore-adm:" in err, f"the ghost-keep refusal must be a loud `lore-adm:` line: {err!r}"
        assert _bare(ghost) in err, f"the refusal must NAME the missing keep {_bare(ghost)!r}: {err!r}"


class TestDeleteKeepVerb:
    async def test_delete_keep_removes_the_keep(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """⚠ RED at HEAD. ``lore-adm delete-keep`` removes the keep (rc 0); ``get_keep`` reads
        None afterward and the keeper PERSON survives."""
        await _add(cli_env, _KEEPER)
        keep_id = await _create_keep(cli_env, capsys, keep_type="team", keeper=_KEEPER, name="crew")
        rc = await _run_cli(cli_env.argv(_DELETE_KEEP, "--keep", keep_id))
        assert rc == 0, f"delete-keep failed (rc={rc})"
        async with _keep_store_for(cli_env.env) as (keep_store, principal_store):
            assert await keep_store.get_keep(keep_id) is None, "delete-keep did not remove the keep"
            assert await principal_store.get_by_email(_KEEPER) is not None, "delete-keep deleted keeper"

    async def test_delete_keep_of_a_ghost_keep_is_loud_and_nonzero(
        self, cli_env: _CliEnv
    ) -> None:
        """⚠ RED at HEAD. A typo'd ``--keep`` is LOUD (exit 1, ``lore-adm:`` stderr) — the
        ``KeepNotFoundError`` laundered by ``_dispatch_keep`` (FR-3 parity: a destructive
        admin verb on a ghost id must not read as a silent success)."""
        await _add(cli_env, _KEEPER)
        # delete-keep's own _dispatch_keep readies the keep slice, so the table exists and the
        # id simply resolves to no row → KeepNotFoundError (a truly-absent table is the #131
        # concern, tested above). ghost_id mints an id guaranteed never created.
        rc = await _run_cli(cli_env.argv(_DELETE_KEEP, "--keep", ghost_id(KEEP_TABLE)))
        assert rc == 1, "delete-keep of a ghost keep must exit 1 (KeepNotFoundError laundered)"


# =========================================================================== #
# The end-to-end remediation FLOW (the whole point of §FR-4). RED at HEAD.
# =========================================================================== #


class TestTheRemediationFlow:
    async def test_reassign_then_delete_the_former_keeper(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """⚠ RED at HEAD — the §FR-4 story via the CLI. Create a keep (keeper A) → ``delete
        A`` is REFUSED → ``set-keeper`` to B → ``delete A`` now SUCCEEDS, and the keep
        survives under B (no data loss)."""
        await _add(cli_env, _KEEPER)
        await _add(cli_env, _SUCCESSOR)
        keep_id = await _create_keep(cli_env, capsys, keep_type="team", keeper=_KEEPER, name="crew")

        refused = await _run_cli(cli_env.argv("delete", "--email", _KEEPER))
        assert refused == 1, "delete of the keeper must be refused before remediation"

        reassigned = await _run_cli(cli_env.argv(_SET_KEEPER, "--keep", keep_id, "--new-keeper", _SUCCESSOR))
        assert reassigned == 0, "set-keeper must succeed"

        deleted = await _run_cli(cli_env.argv("delete", "--email", _KEEPER))
        assert deleted == 0, "after reassigning their keep, deleting the former keeper must succeed"

        async with _keep_store_for(cli_env.env) as (keep_store, principal_store):
            assert await principal_store.get_by_email(_KEEPER) is None, "the former keeper must be deleted"
            keep = await keep_store.get_keep(keep_id)
            successor = await principal_store.get_by_email(_SUCCESSOR)
        assert keep is not None and successor is not None and keep.keeper_id == _bare(successor.id), (
            "the keep must survive under its new keeper (refuse-while-keeping loses no data)"
        )

    async def test_delete_keep_then_delete_the_former_keeper(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """⚠ RED at HEAD — the delete-keep remediation via the CLI. Create a keep (keeper A) →
        ``delete A`` REFUSED → ``delete-keep`` → ``delete A`` SUCCEEDS."""
        await _add(cli_env, _KEEPER)
        keep_id = await _create_keep(cli_env, capsys, keep_type="dm", keeper=_KEEPER)

        assert await _run_cli(cli_env.argv("delete", "--email", _KEEPER)) == 1, "delete must be refused first"
        assert await _run_cli(cli_env.argv(_DELETE_KEEP, "--keep", keep_id)) == 0, "delete-keep must succeed"
        assert await _run_cli(cli_env.argv("delete", "--email", _KEEPER)) == 0, "the delete must now proceed"
        async with _keep_store_for(cli_env.env) as (keep_store, principal_store):
            assert await principal_store.get_by_email(_KEEPER) is None, "the former keeper must be deleted"
            assert await keep_store.get_keep(keep_id) is None, "the keep must be gone"
