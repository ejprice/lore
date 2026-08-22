"""Contract — packet 60 wave 2, the ``lore-adm`` keep CLI verbs.

Written by ``contract-60-w2`` (2026-08-22). The builder builds FROM this; it writes NO
production code. STUB surfaces exist in ``principals.py`` (``build_keep_store`` and the
four ``_cmd_*`` keep handlers raise ``NotImplementedError``; the parser entries and the
``_dispatch_keep`` wiring are REAL), so every behavioural pin fails BEHAVIOURALLY at the
stub — never an ImportError. *Every "RED at stub" claim below is scoped to the tree with
``build_keep_store`` / the keep handlers raising ``NotImplementedError``.*

THE FOUR VERBS (design ``docs/design/2026-08-22-packet60-keep-substrate-rulings.md`` §6),
flat subcommands on the EXISTING ``lore-adm`` parser (``loremaster.principals:main``):

    create-keep --type {project,team,session,dm} [--name <label>] --keeper <email>
    add-household    --keep <id> --member <email>
    remove-household --keep <id> --member <email>
    set-rank         --keep <id> --member <email> --rank <rank>

DESIGN rulings pinned here:
    * Fork B — the per-``type`` ``--name`` rule (app layer, NOT a parser rule — argparse
      cannot express conditional-required): ``project``/``team`` REQUIRE ``--name``,
      ``session`` ALLOWS it, ``dm`` is nameless. Pinned BOTH ways so a build that ignores
      the rule (or requires ``--name`` for all types) reddens.
    * Fork D — ``create-keep`` auto-adds the keeper to the household (proven via the
      printed id feeding ``add-household`` + the household containing the keeper).
    * Fork F — ``add-household`` IDEMPOTENT (a re-add is a benign no-op leaving ONE edge);
      ``remove-household`` REFUSES the keeper (loud, exit 1, keeper unchanged); ``set-rank``
      trivial today (only ``contributor`` is legal).

WAVE-1 SUBSTRATE (committed ``efccdc8``): ``loremaster.keeps.KeepStore`` is fully built.
This wave wires the CLI to it — a ``build_keep_store`` factory (sibling of
``build_principal_store``) and a ``_dispatch_keep`` that readies the ``principal`` table
(the ``member_of`` edge's ENFORCED ``IN`` endpoint) BEFORE the keep slice.

CREDS-FREE (packet-49 LEAD RULING #6, memory ``Packet 49 CONTRACT-AMBIGUITY RULINGS`` §6):
the keep verbs resolve ONLY the surreal block via ``load_surreal_only_config`` (shared
``_dispatch``), never ``load_config``'s eager Anthropic key. The source-scan pins
(``load_config`` absence, no ``--execute``/dry-run string) live in ``test_principals_cli.py``
and already cover this file's edits to ``principals.py`` — not duplicated here.

LIVE store: ws://127.0.0.1:18000 (NEVER :18500). Each test uses a per-test unique database,
reaped on exit. NO skip marker — an unreachable store is a LOUD failure, not a skip.
"""

from __future__ import annotations

import argparse
import ast
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
from loremaster.config import LoreConfig, resolve_config_value, resolve_secret
from loremaster.keeps import KeepStore
from loremaster.principals import PrincipalStore
from loremaster.store.surreal_schema import _KEEP_RANK_CONTRIBUTOR, _KEEP_TYPES, KEEP_TABLE

from loremaster import principals as p_module

# Dedicated env-var NAMEs the fixture config references (never the values baked in) — kept
# distinct from ``test_principals_cli.py``'s so the two suites never share monkeypatch state.
_USER_ENV = "LORE_KEEP_CLI_TEST_SURREAL_USER"
_PASS_ENV = "LORE_KEEP_CLI_TEST_SURREAL_PASS"
_ANTHROPIC_ENV = "LORE_KEEP_CLI_TEST_ANTHROPIC"

_KEEPER = "keeper@example.com"
_MEMBER = "member@example.com"
_MEMBER2 = "member2@example.com"
_UNKNOWN = "nobody@example.com"

_KEEP_VERBS = ("create-keep", "add-household", "remove-household", "set-rank")

# The per-``type`` ``--name`` policy (Fork B + FR-2 Q1) as the test's OWN name-policy map —
# the CHECKED VARIABLE the coverage pin (``test_every_keep_type_has_a_declared_name_policy``)
# holds against the schema's ``_KEEP_TYPES`` domain. A keep type added to ``_KEEP_TYPES``
# WITHOUT a policy decision here reds that pin (fail-closed coverage — reach law #344/#345),
# instead of silently going unpinned. Every per-``type`` parametrized case DERIVES its type
# list from this map (below), so the map is the single source of truth: a new entry flows into
# the matching require/allow/forbid test automatically, never a hand-list drifting from the
# schema.
_NAME_REQUIRED = "require"  # project/team: ``--name`` is MANDATORY (a bare create is rejected)
_NAME_ALLOWED = "allow"  # session: ``--name`` is OPTIONAL (nameless OK, named OK)
_NAME_FORBIDDEN = "forbid"  # dm: a keep with no name concept — a stray ``--name`` is rejected

_NAME_POLICY_BY_TYPE: dict[str, str] = {
    "project": _NAME_REQUIRED,
    "team": _NAME_REQUIRED,
    "session": _NAME_ALLOWED,
    "dm": _NAME_FORBIDDEN,
}

# Derived type lists — each a PROJECTION of the policy map, never a hand-list. ``sorted`` for a
# stable parametrize id order.
_NAME_REQUIRING_TYPES = sorted(t for t, policy in _NAME_POLICY_BY_TYPE.items() if policy == _NAME_REQUIRED)
_NAMELESS_OK_TYPES = sorted(
    t for t, policy in _NAME_POLICY_BY_TYPE.items() if policy in (_NAME_ALLOWED, _NAME_FORBIDDEN)
)
_NAME_ACCEPTED_TYPES = sorted(
    t for t, policy in _NAME_POLICY_BY_TYPE.items() if policy in (_NAME_REQUIRED, _NAME_ALLOWED)
)


@pytest.fixture(autouse=True)
def _cli_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Export the REAL spike-store creds by the env-var NAMEs the fixture config references
    (so ``build_keep_store``'s ``resolve_config_value`` / ``resolve_secret`` succeed against
    ws://127.0.0.1:18000), plus a dummy Anthropic key (``load_config`` would resolve
    ``anthropic.api_key_env`` eagerly, though this CLI never uses it — the creds-free pin
    deletes it)."""
    monkeypatch.setenv(_USER_ENV, surreal_user())
    monkeypatch.setenv(_PASS_ENV, surreal_password().get_secret_value())
    monkeypatch.setenv(_ANTHROPIC_ENV, "unused-by-the-keep-cli")


def _config_payload(*, database: str) -> dict[str, Any]:
    """A minimal VALID lore.yaml payload pointed at the spike store + a unique database.

    Self-contained (independent-collectibility) — cloned from ``test_principals_cli`` /
    ``test_build_store``. The surreal block names the spike URL / test namespace / the unique
    per-test database and references creds by env-var NAME."""
    return {
        "schema_version": 1,
        "anthropic": {"api_key_env": _ANTHROPIC_ENV},
        "project": {"slug": "keep_cli_test_project", "root": "."},
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
async def cli_env(tmp_path: Path) -> AsyncIterator[_CliEnv]:
    """A written lore.yaml pointed at a per-test unique spike-store database, reaped on exit.
    ``main`` builds its stores from this config; the test reads the database back via a
    freshly-built ``KeepStore`` (:func:`_keep_store_for`)."""
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    config_path = tmp_path / "lore.yaml"
    config_path.write_text(yaml.safe_dump(_config_payload(database=env.database)), encoding="utf-8")
    try:
        yield _CliEnv(config_path, env)
    finally:
        await drop_database(env)


async def _run_cli(argv: list[str]) -> int:
    """Invoke the CLI ``main`` OFF the test's running event loop (the ``test_principals_cli``
    idiom). §F6's house idiom is ``main = asyncio.run(...)``; calling it directly from an
    ``async def`` test raises ``RuntimeError: asyncio.run() cannot be called from a running
    event loop``. A worker thread (which has NO loop) lets the mandated ``asyncio.run`` idiom
    work unchanged."""
    import asyncio

    return await asyncio.to_thread(p_module.main, argv)


@asynccontextmanager
async def _keep_store_for(env: SurrealEnv) -> AsyncIterator[tuple[KeepStore, PrincipalStore]]:
    """A ready :class:`KeepStore` + :class:`PrincipalStore` on the test's database, for reading
    the CLI's writes back through the STORE MAPPERS (never a raw column read — so a mis-mapped
    row is caught). The ``principal`` table is readied FIRST (it is ``member_of``'s ENFORCED
    ``IN`` endpoint and ``keep``'s ``keeper`` link target), then the keep slice — the wave-1
    ``keep_env`` ordering. Both stores are reaped on exit. Constructs the stores directly from
    the ``SurrealEnv`` (not ``build_keep_store``) so the reader works independently of the
    factory the contract is also pinning."""
    principal_store = PrincipalStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    keep_store = KeepStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    await principal_store.ensure_ready()  # the member_of ENFORCED endpoint FIRST
    await keep_store.ensure_ready()  # keep + member_of
    try:
        yield keep_store, principal_store
    finally:
        await keep_store.close()
        await principal_store.close()


async def _add(cli_env: _CliEnv, email: str) -> None:
    """Create a principal via the (already-built) ``add`` verb — the keeper/member emails
    every keep verb resolves must exist first."""
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
    """Run ``create-keep`` and return the single printed keep id. Drains ``capsys`` first so
    the returned line is create-keep's output alone; asserts rc==0 (a rejected create is the
    caller's concern, tested separately)."""
    argv = ["create-keep", "--type", keep_type, "--keeper", keeper]
    if name is not None:
        argv += ["--name", name]
    capsys.readouterr()  # drain any prior (silent) verb output
    rc = await _run_cli(cli_env.argv(*argv))
    assert rc == 0, f"create-keep --type {keep_type} failed (rc={rc})"
    return capsys.readouterr().out.strip()


# =========================================================================== #
# Parser surface (offline). The parser entries are REAL in the stub, so these pass at the
# stub; each DISCRIMINATES (a dropped/wrong arg reddens it) and guards the surface for good.
# =========================================================================== #


class TestKeepParserSurface:
    @pytest.mark.parametrize("verb", _KEEP_VERBS)
    def test_every_keep_verb_is_recognised(self, verb: str) -> None:
        """Each keep verb parses with its required args (create-keep with NO ``--name`` —
        proving ``--name`` is OPTIONAL at parse; the per-``type`` rule is behavioural). The
        parsed args carry a dispatchable verb marker."""
        parser = p_module.build_parser()
        if verb == "create-keep":
            argv = ["create-keep", "--type", "project", "--keeper", _KEEPER]
        elif verb == "set-rank":
            argv = ["set-rank", "--keep", "keep:1", "--member", _MEMBER, "--rank", _KEEP_RANK_CONTRIBUTOR]
        else:
            argv = [verb, "--keep", "keep:1", "--member", _MEMBER]
        args = parser.parse_args(argv)  # must NOT SystemExit
        assert getattr(args, "command", None) == verb or verb in vars(args).values(), (
            f"parsed args for {verb!r} carry no dispatchable verb marker: {vars(args)!r}"
        )

    @pytest.mark.parametrize("keep_type", list(_KEEP_TYPES))
    def test_create_keep_accepts_every_schema_type(self, keep_type: str) -> None:
        """``--type`` accepts EVERY value in the schema's ``_KEEP_TYPES`` domain — a build
        that hardcoded a subset of the four flavours reddens on the missing one."""
        args = p_module.build_parser().parse_args(["create-keep", "--type", keep_type, "--keeper", _KEEPER])
        assert args.type == keep_type

    def test_create_keep_rejects_an_out_of_domain_type(self) -> None:
        """``--type`` is a CLOSED argparse choice — a bogus value is a parse-time SystemExit,
        never a value reaching the store. (Discriminates an open ``--type`` with no ``choices``.)"""
        with pytest.raises(SystemExit):
            p_module.build_parser().parse_args(["create-keep", "--type", "workspace", "--keeper", _KEEPER])

    @pytest.mark.parametrize(
        "argv",
        [
            ["create-keep", "--keeper", _KEEPER],  # missing --type
            ["create-keep", "--type", "project"],  # missing --keeper
            ["add-household", "--member", _MEMBER],  # missing --keep
            ["add-household", "--keep", "keep:1"],  # missing --member
            ["remove-household", "--member", _MEMBER],  # missing --keep
            ["remove-household", "--keep", "keep:1"],  # missing --member
            ["set-rank", "--keep", "keep:1", "--member", _MEMBER],  # missing --rank
            ["set-rank", "--keep", "keep:1", "--rank", "contributor"],  # missing --member
            ["set-rank", "--member", _MEMBER, "--rank", "contributor"],  # missing --keep
        ],
    )
    def test_a_keep_verb_missing_a_required_arg_exits(self, argv: list[str]) -> None:
        with pytest.raises(SystemExit):
            p_module.build_parser().parse_args(argv)


# =========================================================================== #
# build_keep_store factory + DRY routing. RED at stub (build_keep_store raises); the AST
# routing pin passes at stub (the stub _dispatch_keep already calls the factory).
# =========================================================================== #


class TestBuildKeepStoreFactory:
    def test_build_keep_store_resolves_config_coordinates(self) -> None:
        """``build_keep_store`` reads the SAME coordinate accessors as
        ``build_principal_store`` (url / namespace / effective database / user / password),
        MINUS ``dim``. RED at stub (raises NotImplementedError). A build resolving the wrong
        database (or a different accessor) reddens here."""
        config = _make_config(unique_database())
        store = p_module.build_keep_store(config)
        assert isinstance(store, KeepStore)
        assert store._url == config.surreal.url
        assert store._namespace == config.surreal.namespace
        assert store._database == config.effective_surreal_database
        assert store._user == resolve_config_value(config.surreal.user_env)
        assert (
            store._password.get_secret_value()
            == resolve_secret(config.surreal.password_env).get_secret_value()
        )

    def test_the_cli_routes_through_build_keep_store(self) -> None:
        """DRY (design §6): the keep dispatch obtains its store via the ``build_keep_store``
        sibling factory, never a hand-rolled ``KeepStore(...)`` recipe cloned at the call
        site. Source scan of ``principals.py`` for a CALL to ``build_keep_store`` (its own
        ``def`` is not a call)."""
        source = Path(p_module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        called: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                name = (
                    fn.id
                    if isinstance(fn, ast.Name)
                    else fn.attr
                    if isinstance(fn, ast.Attribute)
                    else None
                )
                if name is not None:
                    called.add(name)
        assert "build_keep_store" in called, (
            "the keep CLI must obtain its store via build_keep_store (the sibling factory), "
            "never a hand-rolled KeepStore(...) at the call site (design §6 DRY)"
        )


# =========================================================================== #
# Creds-free config resolution (LEAD RULING #6): the keep CLI resolves ONLY the surreal
# block and MUST NOT require the Anthropic key. RED at stub (build_keep_store raises).
# =========================================================================== #


class TestKeepCliCredsFree:
    async def test_the_keep_cli_runs_with_no_anthropic_key_set(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ LEAD RULING #6: with the Anthropic env var UNSET, a keep verb still succeeds —
        proving the keep CLI resolves the surreal block creds-free (shared
        ``load_surreal_only_config``) and never eagerly resolves the embedding key. A build
        coupling an admin op to an embedding key (``load_config``) would raise on the unset
        var and fail here."""
        monkeypatch.delenv(_ANTHROPIC_ENV, raising=False)  # the autouse fixture set it; remove it
        await _add(cli_env, _KEEPER)
        keep_id = await _create_keep(cli_env, capsys, keep_type="project", keeper=_KEEPER, name="creds")
        async with _keep_store_for(cli_env.env) as (keep_store, _principal_store):
            keep = await keep_store.get_keep(keep_id)
        assert keep is not None, (
            "the keep CLI must run + mutate the store with NO Anthropic key set — resolve the "
            "surreal block creds-free (LEAD RULING #6)"
        )


# =========================================================================== #
# create-keep PRINTS the keep id (the mint-key-prints-credential precedent). RED at stub.
# =========================================================================== #


class TestCreateKeepPrintsId:
    async def test_create_keep_prints_a_resolvable_keep_id(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """``create-keep`` executes DIRECTLY, creating the keep AND printing its id as the ONE
        line it emits (so the operator can address the keep). The printed id RESOLVES via a
        FRESH store read (``get_keep``), carries the right type/name, and its ``keeper`` is the
        creator. A build that prints nothing, prints the wrong id, or creates the wrong
        type/keeper reddens. The EXACTLY-ONE-LINE assertion also keeps create-keep from
        echoing any (un-sanitised) free text alongside the id."""
        await _add(cli_env, _KEEPER)
        capsys.readouterr()  # drain the (silent) add
        rc = await _run_cli(
            cli_env.argv("create-keep", "--type", "project", "--keeper", _KEEPER, "--name", "Q3 launch")
        )
        assert rc == 0
        out_lines = [ln.strip() for ln in capsys.readouterr().out.splitlines() if ln.strip()]
        assert len(out_lines) == 1, (
            f"create-keep must print EXACTLY ONE line — the keep id (nothing else): {out_lines!r}"
        )
        keep_id = out_lines[0]
        async with _keep_store_for(cli_env.env) as (keep_store, principal_store):
            keep = await keep_store.get_keep(keep_id)
            keeper = await principal_store.get_by_email(_KEEPER)
        assert keep is not None, f"create-keep printed {keep_id!r} but it does not resolve to a keep"
        assert keep.type == "project"
        assert keep.name == "Q3 launch"
        assert keeper is not None and keep.keeper_id in keeper.id, (
            "the printed keep's keeper is not the resolved creator (Fork A)"
        )

    async def test_the_printed_keep_id_feeds_add_household(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """POSITIVE CONTROL for the printed id + Fork D: the id create-keep prints is a usable
        handle — feeding it to ``add-household`` adds the member, and the household holds the
        auto-added keeper + the new member (2 distinct)."""
        await _add(cli_env, _KEEPER)
        await _add(cli_env, _MEMBER)
        keep_id = await _create_keep(cli_env, capsys, keep_type="project", keeper=_KEEPER, name="feed")
        rc = await _run_cli(cli_env.argv("add-household", "--keep", keep_id, "--member", _MEMBER))
        assert rc == 0
        async with _keep_store_for(cli_env.env) as (keep_store, principal_store):
            household = await keep_store.list_household(keep_id)
            member = await principal_store.get_by_email(_MEMBER)
        member_ids = {m.member_id for m in household}
        assert len(member_ids) == 2, f"expected keeper (auto) + 1 member = 2 distinct: {household!r}"
        assert member is not None and any(m.member_id in member.id for m in household), (
            "the member added via the printed keep id is not in the household"
        )


# =========================================================================== #
# The verbs execute DIRECTLY (end-to-end main() against the live store). RED at stub.
# =========================================================================== #


class TestKeepVerbsExecuteDirectly:
    async def test_add_household_adds_the_member_at_contributor(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        await _add(cli_env, _KEEPER)
        await _add(cli_env, _MEMBER)
        keep_id = await _create_keep(cli_env, capsys, keep_type="team", keeper=_KEEPER, name="crew")
        rc = await _run_cli(cli_env.argv("add-household", "--keep", keep_id, "--member", _MEMBER))
        assert rc == 0
        async with _keep_store_for(cli_env.env) as (keep_store, principal_store):
            household = await keep_store.list_household(keep_id)
            member = await principal_store.get_by_email(_MEMBER)
        assert member is not None and any(m.member_id in member.id for m in household)
        assert len({m.member_id for m in household}) == 2, (
            f"keeper (auto) + 1 member = 2 distinct members: {household!r}"
        )
        assert all(m.rank == _KEEP_RANK_CONTRIBUTOR for m in household), "flat rank today (Fork C)"

    async def test_add_household_two_different_members_both_land(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """≥2 DISTINCT members (+ the auto keeper), so the idempotency pin's 'exactly one edge'
        is not merely 'the store only ever writes one edge' — ``len()`` and the real count
        differ here (small-N discrimination, the wave-1 QUANTIFIER-LAW lesson)."""
        await _add(cli_env, _KEEPER)
        await _add(cli_env, _MEMBER)
        await _add(cli_env, _MEMBER2)
        keep_id = await _create_keep(cli_env, capsys, keep_type="project", keeper=_KEEPER, name="two")
        assert await _run_cli(cli_env.argv("add-household", "--keep", keep_id, "--member", _MEMBER)) == 0
        assert await _run_cli(cli_env.argv("add-household", "--keep", keep_id, "--member", _MEMBER2)) == 0
        async with _keep_store_for(cli_env.env) as (keep_store, _principal_store):
            household = await keep_store.list_household(keep_id)
        assert len({m.member_id for m in household}) == 3, (
            f"keeper + 2 members = 3 distinct members: {household!r}"
        )

    async def test_add_household_is_idempotent_a_re_add_is_a_benign_no_op(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """⚠ Fork F: a re-add of an existing member is a BENIGN no-op — rc==0 (NOT an error to
        the operator) leaving EXACTLY ONE edge (NOT two). A build that let the UNIQUE(in,out)
        ERR escape (rc!=0) or wrote a second edge reddens."""
        await _add(cli_env, _KEEPER)
        await _add(cli_env, _MEMBER)
        keep_id = await _create_keep(cli_env, capsys, keep_type="project", keeper=_KEEPER, name="idem")
        assert await _run_cli(cli_env.argv("add-household", "--keep", keep_id, "--member", _MEMBER)) == 0
        # The re-add must NOT raise / must return 0.
        assert await _run_cli(cli_env.argv("add-household", "--keep", keep_id, "--member", _MEMBER)) == 0
        async with _keep_store_for(cli_env.env) as (keep_store, principal_store):
            household = await keep_store.list_household(keep_id)
            member = await principal_store.get_by_email(_MEMBER)
        assert member is not None
        member_edges = [m for m in household if m.member_id in member.id]
        assert len(member_edges) == 1, (
            f"a re-add wrote a SECOND member_of edge (or raised) — it must be a benign no-op "
            f"leaving exactly one edge: {member_edges!r}"
        )

    async def test_remove_household_removes_a_non_keeper_member(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        await _add(cli_env, _KEEPER)
        await _add(cli_env, _MEMBER)
        keep_id = await _create_keep(cli_env, capsys, keep_type="team", keeper=_KEEPER, name="crew")
        await _run_cli(cli_env.argv("add-household", "--keep", keep_id, "--member", _MEMBER))
        rc = await _run_cli(cli_env.argv("remove-household", "--keep", keep_id, "--member", _MEMBER))
        assert rc == 0
        async with _keep_store_for(cli_env.env) as (keep_store, principal_store):
            household = await keep_store.list_household(keep_id)
            member = await principal_store.get_by_email(_MEMBER)
            keeper = await principal_store.get_by_email(_KEEPER)
        assert member is not None and not any(m.member_id in member.id for m in household), (
            f"the removed member is still in the household: {household!r}"
        )
        # POSITIVE CONTROL: the keeper (a different member) is untouched by the removal.
        assert keeper is not None and any(m.member_id in keeper.id for m in household), (
            "remove-household removed more than the named member"
        )

    async def test_remove_household_refuses_to_remove_the_keeper(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """⚠ Fork F rider (load-bearing): removing the keeper would lock them out of writing
        their own keep (undoing Fork D). ``remove-household`` REFUSES it — a loud stderr line
        (the ``lore-adm:`` launder) + exit 1, and the keeper is STILL in the household (the
        refusal changed nothing). A build that removed the keeper (or exited 0) reddens."""
        await _add(cli_env, _KEEPER)
        keep_id = await _create_keep(cli_env, capsys, keep_type="project", keeper=_KEEPER, name="locked")
        rc = await _run_cli(cli_env.argv("remove-household", "--keep", keep_id, "--member", _KEEPER))
        assert rc == 1, "removing the keeper must be a loud non-zero exit (KeeperLockoutError laundered)"
        err = capsys.readouterr().err
        assert err.startswith(f"{p_module._CLI_PROG}:"), (
            f"the refusal must be a loud `lore-adm:` stderr line, not swallowed: {err!r}"
        )
        async with _keep_store_for(cli_env.env) as (keep_store, principal_store):
            household = await keep_store.list_household(keep_id)
            keeper = await principal_store.get_by_email(_KEEPER)
        assert keeper is not None and any(m.member_id in keeper.id for m in household), (
            "the keeper was removed from the household despite the refusal"
        )

    async def test_set_rank_to_contributor_runs(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Fork F rider: ``set-rank`` UPDATEs the edge's ``rank``. TRIVIAL today — the only
        legal value is ``contributor`` — so this exercises the seam (rc==0, rank persisted)
        without gating 60 on multi-rank behaviour (the real test lands with the rank widening)."""
        await _add(cli_env, _KEEPER)
        await _add(cli_env, _MEMBER)
        keep_id = await _create_keep(cli_env, capsys, keep_type="project", keeper=_KEEPER, name="rank")
        await _run_cli(cli_env.argv("add-household", "--keep", keep_id, "--member", _MEMBER))
        rc = await _run_cli(
            cli_env.argv("set-rank", "--keep", keep_id, "--member", _MEMBER, "--rank", _KEEP_RANK_CONTRIBUTOR)
        )
        assert rc == 0
        async with _keep_store_for(cli_env.env) as (keep_store, principal_store):
            household = await keep_store.list_household(keep_id)
            member = await principal_store.get_by_email(_MEMBER)
        assert member is not None
        member_edges = [m for m in household if m.member_id in member.id]
        assert len(member_edges) == 1 and member_edges[0].rank == _KEEP_RANK_CONTRIBUTOR


# =========================================================================== #
# set-rank error path — the BLOCKER pin (adversary-60-w2). set-rank is the sole write verb
# whose only legal rank (``contributor``) EQUALS the default, so a NO-OP ``_cmd_set_rank``
# (``return 0``, never calling the store) is indistinguishable from a correct one and passes
# the whole contract — UNLESS an error-path pin forces it to ROUTE to the store. RED at stub.
# =========================================================================== #


class TestAdversarySetRankErrorPath:
    async def test_set_rank_with_an_unruled_rank_is_loud_and_nonzero(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """⚠ BLOCKER (adversary-60-w2): ``set-rank --rank <unruled>`` on a REAL household
        member is a loud non-zero exit. The member is added FIRST so the store's UPDATE MATCHES
        a row and the closed ``rank`` ASSERT fires (a bogus rank on a NON-member would no-match,
        not reject — so the fixture must discriminate a real reject from a silent no-op); the
        engine rejection is WRAPPED as ``KeepStoreError`` (FR-2 Q2b) and laundered by
        ``_dispatch_keep`` to a ``lore-adm:`` stderr line + exit 1.

        This is the pin a NO-OP ``_cmd_set_rank`` (``return 0``) cannot pass: a handler that
        never calls ``KeepStore.set_rank`` returns 0 here, reddening ``rc == 1``. It restores the
        loud-on-failure symmetry every OTHER write verb already has (create-keep unknown keeper,
        add-household ghost keep, remove-household keeper lockout). ⚠ Consistent with the design
        (Fork F / sidecar): this proves the verb is not a silent no-op — it does NOT gate 60 on
        multi-rank BEHAVIOUR (only ``contributor`` is legal today)."""
        await _add(cli_env, _KEEPER)
        await _add(cli_env, _MEMBER)
        keep_id = await _create_keep(cli_env, capsys, keep_type="project", keeper=_KEEPER, name="rank")
        await _run_cli(cli_env.argv("add-household", "--keep", keep_id, "--member", _MEMBER))
        capsys.readouterr()  # drain create/add output so `err` is set-rank's alone
        rc = await _run_cli(
            cli_env.argv("set-rank", "--keep", keep_id, "--member", _MEMBER, "--rank", "overlord")
        )
        assert rc == 1, (
            "set-rank with an unruled rank must be a loud non-zero exit (the store's rank ASSERT "
            "rejects → KeepStoreError laundered) — a no-op handler that never calls the store "
            "returns 0 and reds here"
        )
        err = capsys.readouterr().err
        # ⚠ R3 (TEST-ENV-IS-A-FICTION, finding #401): substring, NOT ``startswith``. This is a
        # genuine STORE rejection (the rank ASSERT refuses ``overlord``), so the ``keep query``
        # seam logs a ``keep.query.rejected`` line to stderr (via ``logging.lastResort``) BEFORE
        # the ``lore-adm:`` teaching line — real prod stderr does NOT start with the prog prefix.
        # pytest strips that log line, so ``startswith`` is green in-suite but pins a prod-false
        # property. ``"lore-adm:" in err`` is honest on both the dirty (prod) and clean (suite) line.
        assert f"{p_module._CLI_PROG}:" in err, (
            f"the store rejection must be laundered to a `lore-adm:` stderr line: {err!r}"
        )

    async def test_set_rank_with_the_legal_rank_still_succeeds(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """POSITIVE CONTROL for the reject pin above: the ONE legal rank (``contributor``) on a
        real household member succeeds (rc==0) — so the reject is specifically about the UNRULED
        rank, not set-rank being broken for every input. (The steady-state persistence check is
        ``TestKeepVerbsExecuteDirectly::test_set_rank_to_contributor_runs``; this control keeps
        the adversary class self-contained.)"""
        await _add(cli_env, _KEEPER)
        await _add(cli_env, _MEMBER)
        keep_id = await _create_keep(cli_env, capsys, keep_type="project", keeper=_KEEPER, name="rank2")
        await _run_cli(cli_env.argv("add-household", "--keep", keep_id, "--member", _MEMBER))
        rc = await _run_cli(
            cli_env.argv("set-rank", "--keep", keep_id, "--member", _MEMBER, "--rank", _KEEP_RANK_CONTRIBUTOR)
        )
        assert rc == 0


# =========================================================================== #
# The per-type --name rule (Fork B, app layer). Pinned BOTH ways. RED at stub.
# =========================================================================== #


class TestCreateKeepPerTypeNameRule:
    def test_every_keep_type_has_a_declared_name_policy(self) -> None:
        """⚠ R1 (adversary residual, reach law #344/#345): the per-``type`` ``--name`` policy is
        a CHECKED VARIABLE, not a hand-list. The policy map (:data:`_NAME_POLICY_BY_TYPE`) must
        cover EXACTLY the schema's ``_KEEP_TYPES`` domain — so a NEW keep type added to
        ``_KEEP_TYPES`` WITHOUT a require/allow/forbid decision reds THIS pin (fails CLOSED)
        instead of parse-accepting via ``test_create_keep_accepts_every_schema_type`` while its
        ``--name`` policy silently goes unpinned. Because the per-type parametrized cases derive
        their type lists FROM this map, a new declared entry also flows into the matching
        require/allow/forbid test automatically (coverage-as-checked-variable, DERIVED from
        production truth — never a hardcoded list of 4).

        Mutation-proof both directions: a type dropped from the map (observed set shrinks) OR a
        new ``_KEEP_TYPES`` member with no map entry (production set grows) reds the equality; a
        typo'd policy value reds the second assertion."""
        assert set(_NAME_POLICY_BY_TYPE) == set(_KEEP_TYPES), (
            "the per-type --name-policy map must cover EXACTLY the schema's _KEEP_TYPES domain — "
            "a new keep type needs a require/allow/forbid decision (fail-closed coverage): "
            f"map={sorted(_NAME_POLICY_BY_TYPE)} vs _KEEP_TYPES={sorted(_KEEP_TYPES)}"
        )
        assert set(_NAME_POLICY_BY_TYPE.values()) <= {_NAME_REQUIRED, _NAME_ALLOWED, _NAME_FORBIDDEN}, (
            f"every declared name-policy must be one of require/allow/forbid: {_NAME_POLICY_BY_TYPE!r}"
        )

    @pytest.mark.parametrize("keep_type", _NAME_REQUIRING_TYPES)
    async def test_create_keep_without_name_is_rejected_for_name_requiring_types(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str], keep_type: str
    ) -> None:
        """Fork B: ``project``/``team`` REQUIRE ``--name`` — a bare create is a loud non-zero
        exit and creates NO keep. A build that ignored the per-type rule creates the keep
        (rc==0) and reddens on the exit + no-keep assertions.

        ⚠ R2 (adversary residual, sidecar symmetry): asserts ``rc == 1`` (a dispatch-level
        laundered ``ValueError`` — NOT a parser-level exit 2) AND a TEACHING stderr line that
        names the missing ``--name`` option AND the offending type — SYMMETRIC with the
        ``dm --name`` reject (``test_create_keep_dm_with_a_name_is_rejected``). A build
        rejecting with an empty/cryptic message (or at exit 2) reddens on the stderr checks.

        Discrimination — a build that:
          * IGNORES the per-type rule (creates the keep, rc==0) reds on ``rc == 1`` AND 'no
            keep created';
          * rejects at the PARSER level (exit 2) reds on ``rc == 1``;
          * rejects SILENTLY (no stderr) reds on the ``lore-adm:`` prefix check;
          * rejects with a NON-teaching message reds on the ``name``/type content check."""
        await _add(cli_env, _KEEPER)
        capsys.readouterr()  # drain the (silent) add
        rc = await _run_cli(cli_env.argv("create-keep", "--type", keep_type, "--keeper", _KEEPER))
        assert rc == 1, (
            f"create-keep --type {keep_type} without --name must be a loud dispatch-level reject "
            f"(exit 1, a laundered ValueError) — NOT a silent success, NOT a parser-level exit 2 "
            f"(Fork B)"
        )
        err = capsys.readouterr().err
        assert err.startswith(f"{p_module._CLI_PROG}:"), (
            f"the missing-name rejection must be a loud `lore-adm:` stderr line, not swallowed: {err!r}"
        )
        lowered = err.lower()
        assert "name" in lowered and keep_type in lowered, (
            f"the rejection must TEACH the model why (name the missing --name option AND the type "
            f"{keep_type!r}): {err!r}"
        )
        async with _keep_store_for(cli_env.env) as (keep_store, _principal_store):
            keeps = await keep_store.list_keeps_for_keeper(_KEEPER)
        assert keeps == [], f"a rejected create-keep created a keep anyway: {keeps!r}"

    @pytest.mark.parametrize("keep_type", _NAMELESS_OK_TYPES)
    async def test_create_keep_without_name_works_for_name_optional_types(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str], keep_type: str
    ) -> None:
        """Fork B / E: ``session`` allows a nameless keep; a ``dm`` keep is ALWAYS nameless.
        A bare create SUCCEEDS and round-trips ``name=None``. A build that required ``--name``
        for all types reddens here (``_create_keep`` asserts rc==0)."""
        await _add(cli_env, _KEEPER)
        keep_id = await _create_keep(cli_env, capsys, keep_type=keep_type, keeper=_KEEPER)
        async with _keep_store_for(cli_env.env) as (keep_store, _principal_store):
            keep = await keep_store.get_keep(keep_id)
        assert keep is not None
        assert keep.type == keep_type
        assert keep.name is None, f"a nameless {keep_type} keep must round-trip name=None"

    @pytest.mark.parametrize("keep_type", _NAME_ACCEPTED_TYPES)
    async def test_create_keep_with_name_works(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str], keep_type: str
    ) -> None:
        """POSITIVE CONTROL for the rejection above: with ``--name`` supplied, project/team/
        session all create — so the rejection is specifically about the MISSING name, not the
        type."""
        await _add(cli_env, _KEEPER)
        keep_id = await _create_keep(cli_env, capsys, keep_type=keep_type, keeper=_KEEPER, name="named space")
        async with _keep_store_for(cli_env.env) as (keep_store, _principal_store):
            keep = await keep_store.get_keep(keep_id)
        assert keep is not None and keep.type == keep_type and keep.name == "named space"

    async def test_create_keep_dm_with_a_name_is_rejected(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """⚠ FR-2 Q1 (sidecar ruling, OVERRIDING the wave-2 author's ignore-and-store-None
        recommendation): ``create-keep --type dm --name X`` is REJECTED (exit 1) with a TEACHING
        stderr line and writes NO keep. A ``dm`` keep is identified by its two members and has no
        name concept, so a stray ``--name`` is ALWAYS a mistake — caught LOUD, never silently
        dropped (a silent drop is a surprise the operator traces later). This is the symmetric
        completion of the project/team-WITHOUT-name reject above: a CLI-INPUT-VALIDATION check at
        DISPATCH level, BEFORE any store write (a laundered ``ValueError`` → exit 1), NOT a store
        ASSERT — ``keep.name`` stays ``option<string>``.

        Discrimination — a build that:
          * IGNORES ``--name`` for dm (stores None, creates the keep, rc==0) reds on ``rc == 1``
            AND on 'no keep created';
          * rejects at the PARSER level (exit 2) reds on ``rc == 1`` (the ruling is dispatch-level,
            exit 1 — NOT an argparse choice);
          * rejects SILENTLY (no stderr) reds on the ``lore-adm:`` prefix check;
          * rejects with a NON-teaching message reds on the ``name``/``dm`` content check."""
        await _add(cli_env, _KEEPER)
        capsys.readouterr()  # drain the (silent) add
        rc = await _run_cli(
            cli_env.argv("create-keep", "--type", "dm", "--keeper", _KEEPER, "--name", "not allowed")
        )
        assert rc == 1, (
            "create-keep --type dm --name must be a loud dispatch-level reject (exit 1, a laundered "
            "ValueError) — NOT a silent store of name=None, NOT a parser-level exit 2 (FR-2 Q1)"
        )
        err = capsys.readouterr().err
        prog_prefix = f"{p_module._CLI_PROG}: "  # the launder prefix `lore-adm: ` (f"{_CLI_PROG}: {error}")
        assert err.startswith(prog_prefix), (
            f"the dm --name rejection must be a loud `lore-adm:` stderr line, not swallowed: {err!r}"
        )
        # ⚠ R-A (FIXTURES-MUST-DISCRIMINATE): check the message BODY, not the whole line.
        # ``"dm"`` is a SUBSTRING of the ``lore-adm:`` prefix (…a-``dm``…), so ``"dm" in err``
        # is satisfied by the prefix for ANY message — a degenerate content check that passes
        # even when the body never names the type. Strip the prefix first so the check proves
        # the BODY teaches the offending type.
        body = err[len(prog_prefix):].lower()
        assert "name" in body and "dm" in body, (
            f"the rejection must TEACH the model why (name the offending --name option AND the "
            f"type dm) in the message BODY, not merely the `lore-adm:` prefix: {err!r}"
        )
        async with _keep_store_for(cli_env.env) as (keep_store, _principal_store):
            keeps = await keep_store.list_keeps_for_keeper(_KEEPER)
        assert keeps == [], (
            f"a rejected `dm --name` create-keep created a keep anyway (no partial state — the "
            f"check precedes the store write): {keeps!r}"
        )


# =========================================================================== #
# Error paths — loud on failure (a `lore-adm:` stderr line + exit 1). RED at stub for the
# live pins; the missing-config pin passes at stub (shared _require_config).
# =========================================================================== #


class TestKeepVerbErrorPaths:
    async def test_create_keep_with_an_unknown_keeper_is_loud_and_nonzero(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A keeper email that resolves to no principal is a loud failure: the composed
        ``PrincipalStore.get_by_email`` returns None (``_dispatch_keep`` readied the empty
        principal table first) → ``KeepStoreError`` → laundered to ``f"{_CLI_PROG}: {error}"``
        on stderr + exit 1. A build that crashed (uncaught) or succeeded silently reddens."""
        rc = await _run_cli(
            cli_env.argv("create-keep", "--type", "project", "--keeper", _UNKNOWN, "--name", "x")
        )
        assert rc == 1
        err = capsys.readouterr().err
        assert err.startswith(f"{p_module._CLI_PROG}:"), (
            f"the domain error must be laundered to a `lore-adm:` stderr line: {err!r}"
        )

    async def test_add_household_to_a_nonexistent_keep_is_loud_and_nonzero(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A typo'd ``--keep`` (a ghost keep id) is refused by the ENFORCED ``member_of`` edge
        (the ghost OUT endpoint does not exist — store ref §4) → after FR-2 Q2b, ``KeepStore``
        WRAPS that engine rejection as ``KeepStoreError``, which ``_dispatch_keep`` catches
        (symmetric with ``_dispatch`` catching ``PrincipalStoreError``) → laundered to a
        ``lore-adm:`` stderr line + exit 1, NOT an uncaught crash. Doubles as a CLI-level guard
        that the Q2b wrap happened: ``_dispatch_keep`` no longer catches raw ``SurrealStoreError``
        (FR-2 D1), so a ``KeepStore`` that leaked the raw engine error would escape and crash
        instead of exiting 1."""
        await _add(cli_env, _KEEPER)
        await _add(cli_env, _MEMBER)
        capsys.readouterr()
        ghost_keep = f"{KEEP_TABLE}:{ghost_id('nonexistent_keep')}"
        rc = await _run_cli(cli_env.argv("add-household", "--keep", ghost_keep, "--member", _MEMBER))
        assert rc == 1, "add-household to a nonexistent keep must exit 1 (loud), not crash"
        err = capsys.readouterr().err
        # ⚠ R3 (TEST-ENV-IS-A-FICTION, finding #401): substring, NOT ``startswith``. The ghost
        # keep is refused by the ENFORCED ``member_of`` edge — a genuine STORE rejection, so the
        # ``keep query`` seam logs a ``keep.query.rejected`` line to stderr (``logging.lastResort``)
        # BEFORE the ``lore-adm:`` teaching line. Real prod stderr does not start with the prog
        # prefix; pytest strips the log line, so ``startswith`` is green in-suite yet prod-false.
        assert f"{p_module._CLI_PROG}:" in err, (
            f"the store rejection must be laundered to a `lore-adm:` stderr line: {err!r}"
        )

    def test_a_keep_verb_without_config_is_a_loud_systemexit(self) -> None:
        """``--config`` is REQUIRED (the shared ``_require_config`` guard) — a keep verb with
        no ``--config`` is a loud ``SystemExit``, never a silent default store."""
        with pytest.raises(SystemExit):
            p_module.main(["create-keep", "--type", "project", "--keeper", _KEEPER, "--name", "x"])


# =========================================================================== #
# FR-3 ∀-OVER-VERBS INVARIANT — a nonexistent --keep is LOUD (exit 1 + a `lore-adm:` stderr
# line) for EVERY keep-consuming verb (the sidecar's explicit quantifier/reach rider).
# R3 (adversary-60-w2 residual) was exactly the asymmetry a per-verb pin missed:
# remove-household was the lone SILENT verb on a ghost keep (rc 0 → a false "access removed").
# After FR-3 all three keep-ID-consuming verbs are loud: add-household via ENFORCED (the ghost
# RELATE is refused), set-rank via the no-match ``KeepNotFoundError``, remove-household via the
# new keep-existence check. The verb SET is DERIVED from the real parser (production truth —
# reach law #344/#345), never a hand-list, so a NEW keep verb taking --keep reddens the
# coverage pin if it is not also made loud-on-ghost.
# =========================================================================== #

# A GHOST keep id (never created) — shared by every ∀-verb invocation so the coverage map's
# argv is stable. Fresh uuid4 (ghost_id) so it cannot collide with a real keep.
_GHOST_KEEP = f"{KEEP_TABLE}:{ghost_id('forall_ghost_keep')}"

# The loud-on-ghost invocation per keep-consuming verb — the OBSERVED set the coverage pin holds
# against the DERIVED parser set. A new keep verb taking --keep grows the derived set but not this
# map → the coverage pin reds (coverage-as-checked-variable). Every --member is a REAL seeded
# principal (below), so the loudness is about the GHOST KEEP, not an unresolvable --member.
_KEEP_VERB_GHOST_KEEP_ARGV: dict[str, list[str]] = {
    "add-household": ["add-household", "--keep", _GHOST_KEEP, "--member", _MEMBER],
    "remove-household": ["remove-household", "--keep", _GHOST_KEEP, "--member", _MEMBER],
    "set-rank": ["set-rank", "--keep", _GHOST_KEEP, "--member", _MEMBER, "--rank", _KEEP_RANK_CONTRIBUTOR],
}


def _derive_keep_verbs_taking_keep() -> set[str]:
    """DERIVE, from the REAL ``lore-adm`` parser (production truth — reach law #344/#345), the set
    of subcommands that consume a ``--keep`` argument.

    A STRUCTURAL property (an option-string scan of each subparser), never a hand-list: today it
    is EXACTLY {add-household, remove-household, set-rank}, because ``create-keep`` addresses its
    keeper by ``--keeper`` (not ``--keep``) and every principal verb by ``--email``, so *"has a
    ``--keep`` option"* uniquely identifies the keep-ID-consuming verbs. A NEW keep verb that takes
    ``--keep`` grows this derived set; if it is not also added to
    :data:`_KEEP_VERB_GHOST_KEEP_ARGV`, the coverage pin below reds — the observed loud-on-ghost
    set cannot silently lag the parser.

    ⚠ Bound (reach-law honesty): this covers verbs that take ``--keep`` as a named option. A future
    keep verb that names a keep by a DIFFERENT flag (e.g. ``--keep-id``) or positionally escapes
    this scan — re-open trigger: the first keep verb whose keep argument is not spelled ``--keep``.
    """
    parser = p_module.build_parser()
    subparsers_action = next(
        action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
    )
    return {
        name
        for name, subparser in subparsers_action.choices.items()
        if any("--keep" in action.option_strings for action in subparser._actions)
    }


class TestANonexistentKeepIsLoudForEveryKeepConsumingVerb:
    """FR-3 ∀-over-verbs invariant + its reach (coverage-as-checked-variable)."""

    def test_the_derived_keep_verb_set_matches_the_ghost_keep_coverage_map(self) -> None:
        """REACH PIN (#344/#345): the ``--keep``-consuming verb set is DERIVED from the real parser
        (not a hand-list) and must equal the loud-on-ghost coverage map — so a NEW keep verb taking
        ``--keep`` grows the derived set, fails this equality, and forces a coverage entry (the
        observed set cannot silently lag the parser; R3 was exactly a per-verb pin that did not
        cover ``remove``). Positive control: the derivation EXCLUDES ``create-keep`` (it takes
        ``--keeper``, not ``--keep``) — a scan that returned every keep verb would fail here."""
        derived = _derive_keep_verbs_taking_keep()
        assert derived, "the parser introspection found no --keep-consuming verb — the scan broke"
        assert derived == set(_KEEP_VERB_GHOST_KEEP_ARGV), (
            "the DERIVED keep-verb set (subcommands taking --keep) has drifted from the "
            "loud-on-ghost coverage map — a NEW keep-consuming verb must be added to "
            "_KEEP_VERB_GHOST_KEEP_ARGV (reach law #344/#345). "
            f"derived={sorted(derived)} mapped={sorted(_KEEP_VERB_GHOST_KEEP_ARGV)}"
        )
        assert "create-keep" not in derived, (
            "create-keep addresses its keeper by --keeper, not --keep — the derivation "
            "misclassified it as keep-ID-consuming"
        )

    @pytest.mark.parametrize("verb", sorted(_KEEP_VERB_GHOST_KEEP_ARGV))
    async def test_a_nonexistent_keep_is_a_loud_exit_1(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str], verb: str
    ) -> None:
        """⚠ FR-3 ∀-OVER-VERBS INVARIANT: a nonexistent ``--keep`` is LOUD (exit 1 + a
        ``lore-adm:`` stderr line) for EVERY keep-consuming verb — add-household (ENFORCED refuses
        the ghost RELATE → wrapped ``KeepStoreError``, FR-2 Q2b), set-rank (no-match →
        ``KeepNotFoundError``), remove-household (the NEW FR-3 keep-existence check). Pinned
        ∀-over-the-verbs, NOT re-conditioned on the single verb (``remove``) that prompted it —
        R3's lesson (the quantifier/reach law). The ``--member`` is a REAL seeded principal, so the
        loudness is about the ghost KEEP, not an unresolvable ``--member`` (fixtures discriminate).

        RED at the CLI stub (``build_keep_store`` / the keep handlers raise ``NotImplementedError``,
        which ``_dispatch_keep`` does NOT catch → it propagates, so the call errors rather than
        returning 1 — no false green). For ``remove-household`` specifically it is ALSO RED against
        a ``keeps.py`` without the FR-3 amend (a silent rc 0). The steady-state positive control —
        these verbs SUCCEED on a REAL keep — is ``TestKeepVerbsExecuteDirectly`` /
        ``TestCreateKeepPrintsId::test_the_printed_keep_id_feeds_add_household``."""
        await _add(cli_env, _KEEPER)
        await _add(cli_env, _MEMBER)
        capsys.readouterr()  # drain the (silent) adds so `err` is the keep verb's alone
        argv = _KEEP_VERB_GHOST_KEEP_ARGV[verb]
        rc = await _run_cli(cli_env.argv(*argv))
        assert rc == 1, (
            f"{verb} with a nonexistent --keep must be a loud exit 1 (FR-3 ∀-verb invariant), "
            f"not a silent success/crash: rc={rc}"
        )
        err = capsys.readouterr().err
        # ⚠ R3 (TEST-ENV-IS-A-FICTION, finding #401): substring, NOT ``startswith`` — this pin is
        # ∀-over-verbs, and its ``add-household`` param is a genuine STORE rejection (the ENFORCED
        # ``member_of`` edge refuses the ghost RELATE), so the seam logs a ``keep.query.rejected``
        # line to stderr (``logging.lastResort``) BEFORE the ``lore-adm:`` teaching line in prod.
        # pytest strips that log line, so ``startswith`` is green in-suite but pins a prod-false
        # property for at least the add-household param. ``in`` is honest across all three verbs.
        assert f"{p_module._CLI_PROG}:" in err, (
            f"{verb}'s ghost-keep rejection must be a loud `lore-adm:` stderr line, not swallowed: "
            f"{err!r}"
        )
