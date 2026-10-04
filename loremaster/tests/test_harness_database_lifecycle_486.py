"""Contract — every database a test creates is minted by ``unique_database()`` and does not
outlive the session that created it (lore #486, item 2: "the test-DB leak", operator
2026-09-26: "Fold into #486 cycle").

THE MEASURED DEFECT (contract-486 report §Measurements, 2026-09-26 at ``e039c64``, TEST store
``ws://127.0.0.1:18000``): the shared ``lore_test`` namespace held **2186** databases shaped
``test_<hex32>`` — names minted by 25 hand-rolled ``f"test_{uuid.uuid4().hex}"`` recipes
outside the harness, most of them project SLUGS that production turns into the database name
(``LoreConfig.effective_surreal_database`` = ``surreal.database or project.slug``) — plus
**456** shaped ``test_<pid>_<hex32>`` (the harness's own recipe), **454 of them belonging to
DEAD pids**. Harness-minted databases leak too: 21 of 124 ``unique_database()`` call sites
never reach a reap in their own function, and nothing reaps an orphan (the harness docstring's
"a reused PID later harmlessly reaps any prior orphan" describes no mechanism that exists).

THE PROPERTY, stated over the STATE rather than over the call sites (CLAUDE.md "fix the CLASS":
enforce at the state, pins generated, a hand-list of doors is the thing this repo has seven
receipts against):

    ∀ database D that a test process creates in the test namespace:
        D was minted by ``_surreal_harness.unique_database()`` IN THAT PROCESS, and
        D no longer exists once that process's pytest session has finished.

Why RUNTIME legs carry it and the AST leg is only a lint: whether a minted NAME ever becomes a
DATABASE is a runtime fact — ``test_build_store``'s slug is never dialed (sentinel URL), while
``test_mcp_server``'s becomes a real database through production code the test never names. And
the engine creates a database on a bare ``use()`` (MEASURED 2026-09-26 on 3.2.4: ``use(ns, <fresh>)``
alone materialises it; negative control absent; positive control ``DEFINE DATABASE`` present), so
there is no DDL statement to scan for. A leak is a property of executed code only — a path that
never runs creates nothing — so a runtime leg's reach equals the property's domain.

THE LEGS:

* :class:`TestTheTestDatabaseNamingRecipeExistsOnce` — the LINT (AST, generated over every
  workspace member's ``tests/``): the ``test_…`` naming recipe exists ONCE, in
  ``unique_database()``. Keyed on a literal prefix, therefore defeatable, and labelled so; it
  catches clones that have not dialed YET. The runtime legs are the invariant.
* :class:`TestAForeignDatabaseNameFailsTheSessionThatUsedIt` — RUNTIME, end to end: a real
  pytest session whose test dials a database NOT minted by ``unique_database()`` must FAIL,
  naming it — including a PERFECT FORGERY of the harness's own ``test_<pid>_<hex32>`` shape, so
  a build that checks the name's SHAPE (a regex) instead of its PROVENANCE cannot pass.
* :class:`TestALeakedDatabaseIsReapedAndReported` — RUNTIME, end to end: a real pytest session
  whose test mints, dials and never drops a database must leave NO such database behind, must
  FAIL, and must name the database and the test that leaked it — under ``-n 0`` AND under xdist
  (the standard runner is ``-n``; a pin only at ``-n 0`` would certify the one mode in which a
  worker's report is easiest to see). The reaper must never touch another process's database.
* :class:`TestAMidSessionReapNeverSwallowsALeak` — RUNTIME, end to end (contract-486-r2, from
  refactor-486 §F2): every leak is reported however many times the reaper was called
  mid-session on the same worker; a removal nobody reports is the false clear.
* :class:`TestTheReaperRemovesExactlyWhatThisProcessLeaked` — the reaper function itself.
* :class:`TestTheSessionEndReapNeverCostsPytestItsVerdict` — RUNTIME, end to end (contract-486-r3,
  #534): a session that opened nothing keeps pytest's verdict and summary whatever the TEST store's
  state; one that opened a database and lost the store at session end says so in a named line.
* :class:`TestTheHarnessDocstringClaimsNoReaperItLacks` — the retired false claim.

HOW THE END-TO-END LEGS RUN A SESSION: a subprocess ``python -m pytest`` over a generated test
file in ``tmp_path``, loading THIS suite's ``conftest.py`` as a plugin (``-p conftest`` with
``PYTHONPATH`` = this directory, the same import wiring ``conftest.py`` itself installs), with no
ini (``-c os.devnull``). Measured at HEAD (2026-09-26): ~3.3s per inner session; the suite's
autouse fixtures are live inside it. So the mechanism the builder chooses (an autouse fixture, a
``_sdk_guard._CALL_HOOKS`` observer, a session-finish hook, ``atexit``…) is exercised through
the SAME wiring a real run uses — the contract pins the OUTCOME, not the mechanism — PROVIDED it
is armed from ``loremaster/tests/conftest.py`` or from importing ``_surreal_harness`` (the report's
§Stub expectations).

SAFETY: TEST store only. Every database these pins create is removed in a ``finally`` by the
outer test, whether or not the build under test reaped it, so a RED run leaks nothing.
"""

from __future__ import annotations

import ast
import contextlib
import json
import os
import re
import signal
import socket
import subprocess
import sys
import textwrap
import threading
import tomllib
import urllib.parse
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import _surreal_harness
import pytest
from _surreal_harness import (
    PRODUCTION_DIM,
    connect_admin,
    drop_database,
    make_env,
    run,
    surreal_url,
    unique_database,
)
from loremaster.governed import map_of
from loremaster.store._txn import SurrealStoreError
from loremaster.testing.loopback import LoopbackPort

# --------------------------------------------------------------------------------------------
# Shared constants
# --------------------------------------------------------------------------------------------

_TESTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_DIR.parent.parent

# The production store's port. Every leg here refuses to run against it (CLAUDE.md: never
# point a test at :18500).
_PRODUCTION_STORE_PORT = ":18500"

# The inner session's wall-clock bound. Measured ~3.3s at -n 0 on this host; xdist start-up adds
# a few seconds. Generous so a loaded box never turns a slow session into a false RED.
_INNER_SESSION_TIMEOUT_SECONDS = 240

# The env var through which an inner test tells the outer test which databases it created.
_RECORD_ENV = "LORE_486_INNER_RECORD"

# The xdist worker count for the xdist leg: >1 so the leaking test runs in a WORKER process
# whose report must cross back to the controller — the path a -n 0 leg never exercises.
_XDIST_WORKERS = 2

# The inner leaking test's function name — asserted in the session's output, because a leak
# report that names only a database id leaves the operator unable to find the test that leaked.
_LEAKING_TEST_NAME = "test_mints_dials_and_never_drops_its_database"


# What the census read is called in ``map_of``'s raised message.
_CENSUS_NOUN = "test-namespace census"

# ``INFO FOR NS`` answers from which the present set cannot be read: not a dict, the ``databases``
# key missing, or ``databases`` not a map. Shared by the reaper's fail-loud leg and the census
# oracle's fail-closed control, so both are quantified over ONE domain.
_UNREADABLE_NAMESPACE_ANSWERS = [
    pytest.param(None, id="not-a-dict-none"),
    pytest.param([], id="not-a-dict-list"),
    pytest.param("INFO FOR NS", id="not-a-dict-string"),
    pytest.param({"accesses": {}, "users": {}}, id="databases-key-missing"),
    pytest.param({"accesses": {}, "databases": [], "users": {}}, id="databases-a-list"),
    pytest.param({"accesses": {}, "databases": "test_x", "users": {}}, id="databases-a-string"),
    pytest.param({"accesses": {}, "databases": None, "users": {}}, id="databases-none"),
]


def _refuse_the_production_store() -> None:
    url = surreal_url()
    assert _PRODUCTION_STORE_PORT not in url, (
        f"the harness url {url!r} points at the PRODUCTION store; these pins create and remove "
        f"databases and must only ever run against the test store"
    )


# --------------------------------------------------------------------------------------------
# Store census — the reader is itself a minted, dropped database (M1: a bare use() creates one)
# --------------------------------------------------------------------------------------------


async def _databases_in_the_test_namespace() -> set[str]:
    """Every database name in the test namespace, read through a MINTED reader database that is
    dropped afterwards — because on this engine the reader's own ``use()`` creates a database
    (measured; this contract's first census leaked one by exactly that mechanism).

    FAIL-CLOSED (contract-486-r2 round 2c): the answer is read through production's ONE
    ``INFO FOR …`` reader, ``loremaster.governed.map_of``, with ``databases`` required. A
    wrong-shaped answer raises ``SurrealStoreError``; it never reads as an empty namespace, which
    would make every "the leak is gone from the store" assertion pass vacuously — a false clear
    inside the instrument (:class:`TestTheCensusOracleFailsClosed`)."""
    reader_env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    connection = await connect_admin(reader_env)
    try:
        info = await run(connection, "INFO FOR NS")
    finally:
        await connection.close()
        await drop_database(reader_env)
    databases = map_of(info, noun=_CENSUS_NOUN, required=("databases",))["databases"]
    return set(databases) - {reader_env.database}


async def _remove_if_present(*databases: str) -> None:
    """Belt and braces: remove ``databases`` whether or not the build under test reaped them, so
    a RED run of these pins leaks nothing onto the shared test store.

    ⚠ Removed from a connection selected on a MINTED reader database, with ``REMOVE DATABASE``
    naming each target — NEVER by ``use()``-ing the target. The targets were minted by the INNER
    session's process, not this one, and this contract's own mint-provenance leg correctly
    fails a test that opens a database its process did not mint (caught by this contract's
    satisfiability run, 2026-09-26: ``drop_database`` on an inner name ERRORED all six outer
    tests at teardown).
    """
    if not databases:
        return
    reader_env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    connection = await connect_admin(reader_env)
    try:
        for database in databases:
            await run(connection, f"REMOVE DATABASE IF EXISTS {database}")
    finally:
        await connection.close()
        await drop_database(reader_env)


# --------------------------------------------------------------------------------------------
# The inner pytest session
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class _InnerSession:
    """What one inner pytest session did."""

    returncode: int
    output: str
    created: tuple[str, ...]
    # The created-names record file; an inner test may write further records beside it.
    record_path: Path

    def describe(self) -> str:
        tail = "\n".join(self.output.splitlines()[-40:])
        return f"returncode={self.returncode} created={list(self.created)}\n--- output tail ---\n{tail}"


class _InnerSessionHung(Exception):
    """An inner session that did not END within its bound; its process group was killed."""

    def __init__(self, *, output: str, created: tuple[str, ...], timeout_seconds: float) -> None:
        super().__init__(f"inner session did not end within {timeout_seconds}s")
        self.output = output
        self.created = created
        self.timeout_seconds = timeout_seconds


def _run_inner_session(
    tmp_path: Path,
    test_source: str,
    *,
    workers: int | None = None,
    extra_environment: dict[str, str] | None = None,
    timeout_seconds: float = _INNER_SESSION_TIMEOUT_SECONDS,
) -> _InnerSession:
    """Run ``test_source`` as its own pytest session under THIS suite's conftest.

    ``PYTHONPATH`` carries this tests directory (the same wiring ``conftest.py`` installs for the
    in-tree run), ``-p conftest`` loads the suite's conftest as a plugin (so every autouse fixture
    and hook the builder adds there is live), ``-c os.devnull`` keeps the repo's ini — and its
    ``testpaths`` — out of the inner run.

    ``extra_environment`` is applied LAST, so a leg can retarget the inner session's TEST store
    (``LORE_TEST_SURREAL_URL``) without touching the outer one (contract-486-r3, #534).
    ``timeout_seconds`` lets a leg whose failure mode is a HANG fail in bounded time: the session's
    whole process group is killed and :class:`_InnerSessionHung` raised (with what it recorded), which
    the caller turns into a named failure.
    """
    session_dir = tmp_path / f"inner_{unique_database()}"
    session_dir.mkdir()
    test_file = session_dir / "test_inner_486.py"
    test_file.write_text(textwrap.dedent(test_source), encoding="utf-8")
    record = session_dir / "created.json"
    record.write_text("[]", encoding="utf-8")

    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, [str(_TESTS_DIR), environment.get("PYTHONPATH", "")])
    )
    environment[_RECORD_ENV] = str(record)
    # The inner run must not inherit the OUTER session's xdist worker identity.
    for inherited in ("PYTEST_XDIST_WORKER", "PYTEST_XDIST_WORKER_COUNT", "PYTEST_CURRENT_TEST"):
        environment.pop(inherited, None)
    environment.update(extra_environment or {})

    command = [
        sys.executable,
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "-q",
        "-rA",
        "-c",
        os.devnull,
        "--rootdir",
        str(session_dir),
        "-o",
        "asyncio_mode=auto",
        "-p",
        "conftest",
        str(test_file),
    ]
    if workers is not None:
        command += ["-n", str(workers)]
    # Its own process group, so a HUNG session is killed WHOLE — xdist workers included — and
    # never outlives the outer test holding a TEST-store connection (contract-486-r3 round 3b).
    process = subprocess.Popen(  # noqa: S603 - a fixed argv of this interpreter + pytest
        command,
        cwd=session_dir,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
        raise _InnerSessionHung(
            output=stdout + stderr,
            created=tuple(json.loads(record.read_text(encoding="utf-8"))),
            timeout_seconds=timeout_seconds,
        ) from None
    created = tuple(json.loads(record.read_text(encoding="utf-8")))
    return _InnerSession(
        returncode=process.returncode,
        output=stdout + stderr,
        created=created,
        record_path=record,
    )


# The inner tests' shared preamble: record every database the test is about to dial BEFORE it
# dials it, so the outer test can always clean up — even if the inner test dies mid-way.
_INNER_PREAMBLE = f'''
import json
import os
import uuid

from _surreal_harness import PRODUCTION_DIM, connect_admin, drop_database, make_env, unique_database


def _record(database: str) -> None:
    path = os.environ["{_RECORD_ENV}"]
    with open(path, encoding="utf-8") as handle:
        names = json.load(handle)
    names.append(database)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(names, handle)
'''


# --------------------------------------------------------------------------------------------
# LEG 1 — the naming recipe exists ONCE (AST lint, generated over the workspace test trees)
# --------------------------------------------------------------------------------------------

# The one function allowed to build a ``test_…`` name from a runtime value: the harness's mint.
_THE_ONE_MINT = ("_surreal_harness.py", "unique_database")

# DOCUMENTED EXCEPTIONS — ``"<file name>::<function>" -> reason``. EMPTY at contract time: no
# fixed-name or foreign-shaped mint in the test trees has a reason to exist (report §M4). A future
# entry needs a sentence a reviewer can read, in a diff a reviewer can see.
_DOCUMENTED_EXCEPTIONS: dict[str, str] = {}

# The recipe's literal prefix — RESTATED here, not read: the harness keeps no prefix constant
# (``unique_database`` inlines ``f"test_{os.getpid()}_…"``). The restatement cannot drift
# silently: if the mint stops starting with it, the lint stops finding the mint and
# ``test_the_lint_sees_the_one_mint`` goes RED.
_RECIPE_PREFIX = "test_"


def _workspace_test_roots() -> list[Path]:
    """Every workspace member's ``tests/`` directory — DERIVED from ``[tool.uv.workspace]``, so a
    new member is scanned the day it is registered (the ``_SCANNED_MEMBERS`` lesson)."""
    pyproject = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    members = pyproject["tool"]["uv"]["workspace"]["members"]
    return [_REPO_ROOT / member / "tests" for member in members if (_REPO_ROOT / member / "tests").is_dir()]


def _leading_literal(node: ast.AST) -> str:
    """The literal text a string-building expression STARTS with ('' if it starts computed)."""
    if isinstance(node, ast.JoinedStr):
        first = node.values[0] if node.values else None
        return first.value if isinstance(first, ast.Constant) and isinstance(first.value, str) else ""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add | ast.Mod):
        return _leading_literal(node.left)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "format":
        return _leading_literal(node.func.value)
    return ""


def _builds_a_string(node: ast.AST | None) -> bool:
    return (
        isinstance(node, ast.JoinedStr)
        or (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add | ast.Mod))
        or (
            isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "format"
        )
    )


@dataclass(frozen=True)
class _RecipeSite:
    file: str
    function: str
    line: int
    text: str

    @property
    def key(self) -> str:
        return f"{self.file}::{self.function}"

    def __str__(self) -> str:
        return f"{self.file}:{self.line} in {self.function}() :: {self.text}"


def _naming_recipe_sites(source: str, file_name: str) -> list[_RecipeSite]:
    """Every OUTERMOST string-building expression in ``source`` that starts with the recipe's
    literal prefix and computes part of the name with a CALL (``uuid.uuid4()``, ``os.getpid()``,
    ``uuid.getnode()``, ``secrets.token_hex()`` … — any call, so no list of random sources)."""
    tree = ast.parse(source)
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    sites: list[_RecipeSite] = []
    for node in ast.walk(tree):
        if not _builds_a_string(node) or _builds_a_string(parents.get(node)):
            continue
        if not _leading_literal(node).startswith(_RECIPE_PREFIX):
            continue
        if not any(isinstance(inner, ast.Call) for inner in ast.walk(node) if inner is not node):
            continue
        cursor = parents.get(node)
        while cursor is not None and not isinstance(cursor, ast.FunctionDef | ast.AsyncFunctionDef):
            cursor = parents.get(cursor)
        sites.append(
            _RecipeSite(
                file=file_name,
                function=cursor.name if cursor is not None else "<module>",
                line=getattr(node, "lineno", 0),
                text=ast.unparse(node)[:90],
            )
        )
    return sites


def _all_recipe_sites() -> list[_RecipeSite]:
    sites: list[_RecipeSite] = []
    for root in _workspace_test_roots():
        for path in sorted(root.rglob("*.py")):
            sites.extend(_naming_recipe_sites(path.read_text(encoding="utf-8"), path.name))
    return sites


class TestTheTestDatabaseNamingRecipeExistsOnce:
    """ONE IMPLEMENTATION for the test-database name: the recipe lives in ``unique_database()``.

    A LINT (keyed on the recipe's literal prefix, so a clone spelled ``f"db_{uuid4().hex}"``
    walks past it) — which is why the runtime legs below carry the invariant. Its job is the
    clone that has not dialed YET: ``test_build_store``'s slug never reaches a store today and
    will the day someone points its config at one.
    """

    def test_no_test_tree_builds_a_test_name_outside_unique_database(self) -> None:
        """RED at HEAD ``e039c64`` (2026-09-26): 25 clones in 24 files (contract-486 report §M4)."""
        clones = [
            site
            for site in _all_recipe_sites()
            if (site.file, site.function) != _THE_ONE_MINT and site.key not in _DOCUMENTED_EXCEPTIONS
        ]
        assert not clones, (
            f"{len(clones)} test-tree site(s) build a `{_RECIPE_PREFIX}…` name from a runtime value "
            f"outside `_surreal_harness.unique_database()`:\n  "
            + "\n  ".join(str(site) for site in clones)
            + "\n\nA project SLUG is a database name whenever `surreal.database` is unset "
            "(`LoreConfig.effective_surreal_database`), so each of these is a database nothing "
            "reaps the day its test dials the store — 2186 of them were sitting in `lore_test` on "
            "2026-09-26. Mint with `unique_database()` (its names satisfy `SLUG_PATTERN`)."
        )

    def test_the_lint_sees_the_one_mint(self) -> None:
        """NON-VACUITY: the scan must find the harness's own recipe — a scan that found nothing
        (a parse change, a moved root, an empty member list) would pass the pin above."""
        assert any((site.file, site.function) == _THE_ONE_MINT for site in _all_recipe_sites()), (
            "the recipe lint does not see `unique_database()`'s own recipe — it is blind, and its "
            "'no clones' verdict above is worthless"
        )

    def test_every_documented_exception_still_names_a_real_site(self) -> None:
        """An exception whose site is gone is a stale allowance waiting to bless a new clone."""
        live = {site.key for site in _all_recipe_sites()}
        stale = sorted(set(_DOCUMENTED_EXCEPTIONS) - live)
        assert not stale, f"documented exceptions naming no current site: {stale}"

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param("def _slug():\n    return f'test_{uuid.uuid4().hex}'\n", id="fstring"),
            pytest.param("def _slug():\n    return 'test_' + uuid.uuid4().hex\n", id="concat"),
            pytest.param("def _slug():\n    return 'test_{}'.format(uuid.uuid4().hex)\n", id="format"),
            pytest.param("def _slug():\n    return 'test_%s' % uuid.uuid4().hex\n", id="percent"),
            pytest.param(
                "def _slug():\n    return f'test_{uuid.getnode() % 100000}_{uuid.uuid4().hex}'\n",
                id="getnode-pid-lookalike",
            ),
            pytest.param(
                "def _slug():\n    return f'test_{os.getpid()}_{secrets.token_hex(16)}'\n",
                id="perfect-shape-forgery",
            ),
        ],
    )
    def test_the_lint_FIRES_on_every_clone_spelling(self, source: str) -> None:
        """POSITIVE CONTROL."""
        assert _naming_recipe_sites(source, "synthetic.py"), f"the lint missed a clone: {source!r}"

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param("def f():\n    return f'cyc_{uuid.uuid4().hex}'\n", id="task-id-not-a-db-name"),
            pytest.param("def f(name):\n    return f'test_{name}'\n", id="no-runtime-call"),
            pytest.param("def f():\n    return unique_database()\n", id="calls-the-mint"),
            pytest.param("def f(slug):\n    return f'lore_{slug}'\n", id="other-prefix"),
        ],
    )
    def test_the_lint_stays_QUIET_on_non_clones(self, source: str) -> None:
        """NEGATIVE CONTROL — a lint that flagged every uuid f-string would force 30+ task-id
        helpers red for nothing (a gate that insults honest code gets switched off)."""
        assert not _naming_recipe_sites(source, "synthetic.py")


# --------------------------------------------------------------------------------------------
# LEG 2 — RUNTIME: a database not minted by THIS process's unique_database() fails its session
# --------------------------------------------------------------------------------------------

_INNER_FOREIGN_NAME_TEST = (
    _INNER_PREAMBLE
    + """

async def test_dials_a_database_it_did_not_mint():
    database = {forged_name}
    _record(database)
    env = make_env(database=database, dim=PRODUCTION_DIM)
    connection = await connect_admin(env)
    await connection.close()
    await drop_database(env)
"""
)

_INNER_MINTED_NAME_TEST = (
    _INNER_PREAMBLE
    + """

async def test_dials_a_database_it_minted():
    database = unique_database()
    _record(database)
    env = make_env(database=database, dim=PRODUCTION_DIM)
    connection = await connect_admin(env)
    await connection.close()
    await drop_database(env)
"""
)


class TestAForeignDatabaseNameFailsTheSessionThatUsedIt:
    """The mint half of the property, at RUNTIME and end to end (report §Contract, leg 2).

    Quantified over what the engine is ASKED to open, not over how the name was spelled: the
    engine creates a database on a bare ``use()``, so every database a test creates passes the
    connection's session selection — the one door the runtime check must watch.
    """

    @pytest.mark.parametrize(
        "forged_name",
        [
            # The 2186-strong population (measured 2026-09-26): the hand-rolled `test_<hex32>` slug.
            pytest.param('"test_" + uuid.uuid4().hex', id="bare-hex-slug"),
            # A PERFECT FORGERY of the harness's own shape, minted by hand in the SAME process
            # (same pid). A build that checks the name's SHAPE — a `test_<pid>_<hex32>` regex, or
            # "carries my pid" — passes this; only PROVENANCE ("did unique_database() mint it
            # here?") can fail it. That is the #102 shape: a clone passing as the real thing.
            pytest.param('f"test_{os.getpid()}_{uuid.uuid4().hex}"', id="forged-harness-shape-same-pid"),
        ],
    )
    async def test_dialing_an_unminted_database_fails_the_session_and_names_it(
        self, tmp_path: Path, forged_name: str
    ) -> None:
        """RED at HEAD: nothing checks provenance; the inner session passes (rc 0)."""
        _refuse_the_production_store()
        session = _run_inner_session(tmp_path, _INNER_FOREIGN_NAME_TEST.replace("{forged_name}", forged_name))
        try:
            assert len(session.created) == 1, f"the inner test never dialed: {session.describe()}"
            (database,) = session.created
            assert session.returncode != 0, (
                f"a pytest session whose test dialed a database NOT minted by "
                f"`unique_database()` ({database}) PASSED. Nothing ties that database to this "
                f"process, so nothing will ever reap it if the test forgets to — the source of the "
                f"2186 `test_<hex32>` databases in `lore_test` (measured 2026-09-26).\n{session.describe()}"
            )
            assert database in session.output, (
                f"the session failed but its output never names the offending database "
                f"({database}) — an operator cannot find the site.\n{session.describe()}"
            )
        finally:
            await _remove_if_present(*session.created)

    async def test_CONTROL_dialing_a_minted_database_passes(self, tmp_path: Path) -> None:
        """POSITIVE CONTROL (GREEN at HEAD by design): the same flow through ``unique_database()``
        passes — so the leg above fails for PROVENANCE, not because the inner wiring is broken."""
        _refuse_the_production_store()
        session = _run_inner_session(tmp_path, _INNER_MINTED_NAME_TEST)
        try:
            assert len(session.created) == 1, f"the control never dialed: {session.describe()}"
            assert session.returncode == 0, (
                f"a CLEAN session (minted, dialed, dropped) failed — the check is refusing honest "
                f"code, or the inner wiring is broken.\n{session.describe()}"
            )
        finally:
            await _remove_if_present(*session.created)


# --------------------------------------------------------------------------------------------
# LEG 3 — RUNTIME: no minted database outlives its session; the leak is loud and attributed
# --------------------------------------------------------------------------------------------

_INNER_LEAKING_TEST = (
    _INNER_PREAMBLE
    + f"""

async def {_LEAKING_TEST_NAME}():
    database = unique_database()
    _record(database)
    connection = await connect_admin(make_env(database=database, dim=PRODUCTION_DIM))
    await connection.close()
    # ...and never drops it: the 21-of-124 shape (2026-09-26, contract-486 report §M5).
"""
)


class TestALeakedDatabaseIsReapedAndReported:
    """The lifetime half of the property: ∀ D minted in a session, D is gone when it ends.

    Stated over the STATE (what is left in the namespace), never over the call sites — so it
    covers the 21 unreaped ``unique_database()`` sites (measured 2026-09-26), the slug-derived
    databases production creates on a test's behalf, and whatever site is written next, without
    listing any of them.

    And LOUD: a reaped leak is still a defect in the test that leaked it, so the session FAILS
    and names both the database and the test. Silent reaping would hide the next 21.

    Bounded, honestly: a session KILLED before it finishes (SIGKILL, a watchdog, an OOM) never
    reaches its own end, so these legs cannot cover it — that is the 454-dead-pid population
    (measured 2026-09-26), and reaping ANOTHER process's databases is a design fork routed to the
    operator (report decision D2), deliberately NOT pinned here.
    """

    @pytest.mark.parametrize(
        "workers",
        [pytest.param(None, id="n0"), pytest.param(_XDIST_WORKERS, id=f"xdist-n{_XDIST_WORKERS}")],
    )
    async def test_a_leaked_database_is_gone_after_its_session_and_the_session_says_so(
        self, tmp_path: Path, workers: int | None
    ) -> None:
        """RED at HEAD: nothing reaps; the leaked database survives and the session passes.

        The CROSS-SESSION leg rides the same run: a database minted by THIS (outer) process is
        live while the inner session ends, and must SURVIVE it. A reaper that removes by prefix
        (``test_*``), by shape, or by "not mine and not in my registry" would destroy a
        concurrent pytest session's live database — on the shared store every agent uses.
        """
        _refuse_the_production_store()
        outer_env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        outer_connection = await connect_admin(outer_env)
        await outer_connection.close()
        session: _InnerSession | None = None
        try:
            session = _run_inner_session(tmp_path, _INNER_LEAKING_TEST, workers=workers)
            assert len(session.created) == 1, f"the inner test never dialed: {session.describe()}"
            (leaked,) = session.created
            present = await _databases_in_the_test_namespace()

            assert leaked not in present, (
                f"the database `{leaked}` — minted by `unique_database()`, dialed, never dropped — "
                f"OUTLIVED the pytest session that created it. This is how `lore_test` came to hold "
                f"454 harness-shaped databases of dead processes (measured 2026-09-26).\n{session.describe()}"
            )
            assert outer_env.database in present, (
                f"the inner session's reaper removed `{outer_env.database}`, a database ANOTHER live "
                f"process minted. A reaper must remove only what its own process minted — on the "
                f"shared test store every agent's suite runs against.\n{session.describe()}"
            )
            assert session.returncode != 0, (
                f"the leak was reaped SILENTLY (the session passed). A reaped leak is still a test "
                f"that forgot its teardown; hiding it hides the next one.\n{session.describe()}"
            )
            assert leaked in session.output and _LEAKING_TEST_NAME in session.output, (
                f"the leak report must name BOTH the database (`{leaked}`) and the test that leaked "
                f"it (`{_LEAKING_TEST_NAME}`) — a bare database id cannot be traced to a site"
                f"{' (under xdist the WORKER must get this back to the controller)' if workers else ''}."
                f"\n{session.describe()}"
            )
        finally:
            if session is not None:
                await _remove_if_present(*session.created)
            await drop_database(outer_env)

    async def test_CONTROL_a_clean_session_passes_and_leaves_nothing(self, tmp_path: Path) -> None:
        """NEGATIVE CONTROL (GREEN at HEAD by design): mint, dial, DROP — the session passes and
        its database is gone. A leak check that failed every session would pass the leg above."""
        _refuse_the_production_store()
        session = _run_inner_session(tmp_path, _INNER_MINTED_NAME_TEST)
        try:
            assert session.returncode == 0, f"a clean session failed:\n{session.describe()}"
            (database,) = session.created
            assert database not in await _databases_in_the_test_namespace()
        finally:
            await _remove_if_present(*session.created)


# --------------------------------------------------------------------------------------------
# LEG 3b — RUNTIME: a mid-session reaper call never swallows a leak (contract-486-r2, F2)
# --------------------------------------------------------------------------------------------

# The inner session's tests, in collection (= execution) order. Two LEAKERS, each followed by a
# test that calls the reaper mid-session. The second leaker sits BETWEEN the two reaper calls so
# that "only the last reap is remembered", "each reap call overwrites the last" and "only what the
# session-end reap itself finds is reported" each lose a DIFFERENT leaker — one leaker before a
# single reap call cannot tell those builds apart (FIXTURES MUST DISCRIMINATE).
_FIRST_LEAKER_NAME = "test_a_leaks_before_the_first_reaper_call"
_FIRST_REAPER_CALLER_NAME = "test_b_calls_the_reaper_mid_session"
_SECOND_LEAKER_NAME = "test_c_leaks_between_the_two_reaper_calls"
_SECOND_REAPER_CALLER_NAME = "test_d_calls_the_reaper_again"

_LEAKERS = (_FIRST_LEAKER_NAME, _SECOND_LEAKER_NAME)


def _inner_leaker(test_name: str) -> str:
    return f"""

async def {test_name}():
    database = unique_database()
    _record(database)
    connection = await connect_admin(make_env(database=database, dim=PRODUCTION_DIM))
    await connection.close()
    # ...and never drops it.
"""


def _inner_reaper_caller(test_name: str) -> str:
    # The shape of TestTheReaperRemovesExactlyWhatThisProcessLeaked's own reaper test: a test, on
    # the same worker as earlier tests, that calls the session-end reaper in the middle of the run.
    return f"""

async def {test_name}():
    from _surreal_harness import reap_minted_databases

    await reap_minted_databases()
"""


_INNER_LEAKS_AROUND_MID_SESSION_REAPS = (
    _INNER_PREAMBLE
    + _inner_leaker(_FIRST_LEAKER_NAME)
    + _inner_reaper_caller(_FIRST_REAPER_CALLER_NAME)
    + _inner_leaker(_SECOND_LEAKER_NAME)
    + _inner_reaper_caller(_SECOND_REAPER_CALLER_NAME)
)

# CONTROL: the same two leakers with no mid-session reaper call — the path leg 3 already pins.
_INNER_LEAKS_WITHOUT_A_MID_SESSION_REAP = (
    _INNER_PREAMBLE + _inner_leaker(_FIRST_LEAKER_NAME) + _inner_leaker(_SECOND_LEAKER_NAME)
)


def _assert_every_leak_was_reaped_and_reported(session: _InnerSession, present: set[str]) -> None:
    """∀ leaker: its database is gone, the session failed, and ONE output line names both that
    database and that leaker — so the report attributes each leak to the test that made it, not
    to the test that happened to be running when something removed it."""
    assert len(session.created) == len(_LEAKERS), (
        f"expected one database per leaker {list(_LEAKERS)}; the inner tests did not all dial:\n"
        f"{session.describe()}"
    )
    survivors = [database for database in session.created if database in present]
    assert not survivors, f"leaked databases OUTLIVED their session: {survivors}\n{session.describe()}"
    assert session.returncode != 0, (
        f"the session PASSED although {len(_LEAKERS)} of its tests leaked a database — a false "
        f"clear: the leaks were removed, and nobody was told.\n{session.describe()}"
    )
    lines = session.output.splitlines()
    # The inner preamble records in execution order, so created[i] belongs to _LEAKERS[i].
    for leaker, database in zip(_LEAKERS, session.created, strict=True):
        attributing = [line for line in lines if database in line and leaker in line]
        assert attributing, (
            f"no output line names the leaked database `{database}` together with the test that "
            f"leaked it (`{leaker}`). Every leak must be reported, whatever removed it and "
            f"whenever.\n{session.describe()}"
        )


class TestAMidSessionReapNeverSwallowsALeak:
    """The lifetime property's REPORT half, quantified over every leak in the session:

        ∀ database D leaked by a test: D is reported (named with its leaking test) and the
        session fails — REGARDLESS of whether, or how many times, ``reap_minted_databases()``
        was called mid-session on the same worker before the session ended.

    Why it needs its own leg (refactor-486 §F2, constructed 2026-10-04 on the #486 working tree
    over ``a489e8e``: control rc=1 with 1 report line, probe rc=0 with 0): the reaper is a public
    function any test can call — this contract's own
    :meth:`TestTheReaperRemovesExactlyWhatThisProcessLeaked.test_the_reaper_removes_a_leaked_database_and_spares_a_dropped_one`
    does — and if a removal it performs is never reported, every earlier leak on that worker is
    removed SILENTLY and the session passes. Leg 3 cannot see this: its session has no such call.

    The pin is on the OUTCOME (the session's verdict, its output, the store), not on who
    records what — no mechanism is prescribed. Run at ``-n 0`` and on ONE xdist worker (both
    keep every inner test on the same process, which is the case the defect needs; ``-n 1``
    adds the worker→controller crossing).
    """

    @pytest.mark.parametrize(
        "workers",
        [pytest.param(None, id="n0"), pytest.param(1, id="xdist-n1")],
    )
    async def test_leaks_before_and_between_mid_session_reaper_calls_are_all_reported(
        self, tmp_path: Path, workers: int | None
    ) -> None:
        """RED on the #486 working tree as of contract-486-r2 (2026-10-04): the mid-session
        reaper removes both leaks unreported; the session passes (rc 0) with no report line."""
        _refuse_the_production_store()
        session: _InnerSession | None = None
        try:
            session = _run_inner_session(tmp_path, _INNER_LEAKS_AROUND_MID_SESSION_REAPS, workers=workers)
            _assert_every_leak_was_reaped_and_reported(session, await _databases_in_the_test_namespace())
        finally:
            if session is not None:
                await _remove_if_present(*session.created)

    async def test_CONTROL_the_same_leaks_with_no_mid_session_reap_are_all_reported(
        self, tmp_path: Path
    ) -> None:
        """CONTROL (GREEN on the #486 working tree): the identical leakers and the identical
        assertion, minus the reaper calls — so the leg above fails because of the mid-session
        reap, not because the assertion or the inner wiring is broken."""
        _refuse_the_production_store()
        session: _InnerSession | None = None
        try:
            session = _run_inner_session(tmp_path, _INNER_LEAKS_WITHOUT_A_MID_SESSION_REAP)
            _assert_every_leak_was_reaped_and_reported(session, await _databases_in_the_test_namespace())
        finally:
            if session is not None:
                await _remove_if_present(*session.created)


# --------------------------------------------------------------------------------------------
# LEG 4 — the reaper function itself (in-process, live store)
# --------------------------------------------------------------------------------------------


class TestTheReaperRemovesExactlyWhatThisProcessLeaked:
    """``_surreal_harness.reap_minted_databases()`` — the session-end leg's engine, pinned alone
    so a failure of the end-to-end legs has a precise neighbour to read.

    Interface (report §Stub expectations): ``unique_database()`` records each name it mints in
    ``_surreal_harness._MINTED_DATABASES`` (a ``dict`` of name -> ``(minted_by, reaped)``:
    ``minted_by`` is the minting test's node id, read from ``PYTEST_CURRENT_TEST`` at mint time,
    and ``reaped`` turns True once the reaper removes the database as a leak — lead ruling
    D-r2b-1); ``await reap_minted_databases()`` removes every recorded database still present in
    the test namespace, marks each one reaped, and returns the names it removed.
    """

    async def test_unique_database_records_the_name_and_the_minting_test(self) -> None:
        """RED at HEAD: there is no record of what this process minted."""
        registry = getattr(_surreal_harness, "_MINTED_DATABASES", None)
        assert isinstance(registry, dict), (
            "`_surreal_harness._MINTED_DATABASES` (dict: name -> (minting test node id, reaped)) is "
            "missing — "
            "without a per-process record, nothing can tell this process's databases from another "
            "live session's"
        )
        database = unique_database()
        assert database in registry
        minted_by = str(registry[database])
        assert "test_unique_database_records_the_name_and_the_minting_test" in minted_by, (
            f"the record attributes `{database}` to {minted_by!r}, not to the test that minted it — "
            f"a leak report built on it could not name the leaking test"
        )

    async def test_the_reaper_removes_a_leaked_database_and_spares_a_dropped_one(
        self, tmp_path: Path
    ) -> None:
        """RED at HEAD (``90d908f`` era): ``reap_minted_databases`` did not exist.

        Re-keyed by contract-486-r2 round 2b (operator-lead ruling D-r2-1, 2026-10-04): the
        deliberate leak and the reaper call run INSIDE an inner session. Every leaked database is
        reported, with no exemption (:class:`TestAMidSessionReapNeverSwallowsALeak`), so a test
        that leaks on purpose in the OUTER session would fail every suite run that includes it.

        Pinned here: the reaper's RETURN (the leaked name in, the dropped name out), the STORE
        (both gone afterwards), and the inner session's OUTCOME as far as it is this leg's
        business: the inner test itself PASSED, and no output line names the DROPPED database
        (a report naming a clean test is noise nobody reads). Whether the inner session fails
        because its leak is reported is the F2 leg's property, deliberately not re-pinned here.
        """
        _refuse_the_production_store()
        session = _run_inner_session(tmp_path, _INNER_REAPER_DIRECT_TEST)
        try:
            assert len(session.created) == len(_REAPER_DIRECT_ROLES), (
                f"the inner reaper test did not mint and dial both databases:\n{session.describe()}"
            )
            leaked, dropped = session.created
            reaped_record = Path(f"{session.record_path}{_REAPED_RECORD_SUFFIX}")
            assert reaped_record.exists(), (
                f"the inner reaper test never recorded what the reaper returned — it failed before or "
                f"inside `reap_minted_databases()`:\n{session.describe()}"
            )
            reaped = set(json.loads(reaped_record.read_text(encoding="utf-8")))

            assert leaked in reaped, (
                f"the reaper did not report removing `{leaked}` (minted, dialed, never dropped); "
                f"reaped={sorted(reaped)}\n{session.describe()}"
            )
            assert dropped not in reaped, (
                f"the reaper reported `{dropped}` as a LEAK although its test dropped it — a report "
                f"that names clean tests is noise nobody reads\n{session.describe()}"
            )
            present = await _databases_in_the_test_namespace()
            assert leaked not in present and dropped not in present, (
                f"after the reaper ran, the namespace still holds "
                f"{sorted({leaked, dropped} & present)}\n{session.describe()}"
            )
            assert f"PASSED test_inner_486.py::{_REAPER_DIRECT_TEST_NAME}" in session.output, (
                f"the inner reaper test did not pass:\n{session.describe()}"
            )
            assert not [line for line in session.output.splitlines() if dropped in line], (
                f"the session's output names the DROPPED database `{dropped}` — its test tore it "
                f"down, so no report may name it.\n{session.describe()}"
            )
        finally:
            await _remove_if_present(*session.created)


# The roles of the two databases the inner reaper test mints, in the order it records them.
_REAPER_DIRECT_ROLES = ("leaked", "dropped")
_REAPER_DIRECT_TEST_NAME = "test_the_reaper_removes_the_leaked_one_and_spares_the_dropped_one"
# Where the inner test writes what the reaper RETURNED: beside the created-names record.
_REAPED_RECORD_SUFFIX = ".reaped.json"

_INNER_REAPER_DIRECT_TEST = (
    _INNER_PREAMBLE
    + f"""

async def {_REAPER_DIRECT_TEST_NAME}():
    from _surreal_harness import reap_minted_databases

    leaked_env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    dropped_env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    for env in (leaked_env, dropped_env):
        _record(env.database)
        connection = await connect_admin(env)
        await connection.close()
    await drop_database(dropped_env)

    reaped = sorted(await reap_minted_databases())

    with open(os.environ["{_RECORD_ENV}"] + "{_REAPED_RECORD_SUFFIX}", "w", encoding="utf-8") as handle:
        json.dump(reaped, handle)
"""
)


# A well-formed ``INFO FOR NS`` answer: measured 2026-10-04 on the 3.2.4 TEST store, a ``dict``
# with exactly the keys ``accesses``, ``databases``, ``users``, ``databases`` a ``dict`` of
# name -> definition (the probe is pasted verbatim in contract-486-r2's report §ROUND 2b, finding #486).
_WELL_FORMED_EMPTY_NAMESPACE_ANSWER: dict[str, dict[str, str]] = {
    "accesses": {},
    "databases": {},
    "users": {},
}


class TestTheReaperFailsLoudOnANamespaceAnswerItCannotRead:
    """refactor-486 F3, lifted: ∀ ``INFO FOR NS`` answer the reaper cannot read the present set
    from, the reaper RAISES — it never answers "nothing leaked". An unreadable answer read as an
    empty namespace is a false clear (Leg-2 forgery: a broken store response serving the same
    bytes as a clean one).

    Injected by replacing ``_surreal_harness.run`` for the ``INFO FOR NS`` statement only; every
    other statement passes through to the real TEST store. The leaked database is real, so the
    wrong-shaped answer is hiding an actual leak. Nothing is removed on either leg, so this
    outer test reaps nothing of its own process's mid-session (the F2 door), and it drops its
    own database in ``finally``.
    """

    @staticmethod
    def _answer_info_for_ns_with(monkeypatch: pytest.MonkeyPatch, answer: object) -> None:
        real_run = _surreal_harness.run

        async def run_answering_info_for_ns(
            connection: Any, statement: str, params: dict[str, Any] | None = None
        ) -> Any:
            if statement.strip().upper() == "INFO FOR NS":
                return answer
            return await real_run(connection, statement, params)

        monkeypatch.setattr(_surreal_harness, "run", run_answering_info_for_ns)

    @pytest.mark.parametrize("answer", _UNREADABLE_NAMESPACE_ANSWERS)
    async def test_an_unreadable_namespace_answer_makes_the_reaper_raise(
        self, monkeypatch: pytest.MonkeyPatch, answer: object
    ) -> None:
        """RED on the #486 working tree as of round 2b (2026-10-04) for every shape the reaper
        coerces to an empty set; it returns ``()``, "nothing leaked"."""
        _refuse_the_production_store()
        leaked_env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        connection = await connect_admin(leaked_env)
        await connection.close()
        try:
            self._answer_info_for_ns_with(monkeypatch, answer)
            outcome: object = None
            try:
                outcome = tuple(await _surreal_harness.reap_minted_databases())
            except Exception:  # noqa: BLE001 - ANY loud failure satisfies the property
                return
            pytest.fail(
                f"`INFO FOR NS` answered {answer!r} — a shape the present set cannot be read from — "
                f"and the reaper RETURNED {outcome!r} instead of raising. With `{leaked_env.database}` "
                f"actually leaked, that is a false 'nothing leaked'."
            )
        finally:
            monkeypatch.undo()
            await drop_database(leaked_env)

    async def test_CONTROL_a_well_formed_answer_is_read_without_raising(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CONTROL (GREEN on the #486 working tree): the same injection with a WELL-FORMED answer
        (an empty ``databases`` map) is read and returns no removals — so the leg above fails for
        the SHAPE, not because the injection or the reader connection is broken."""
        _refuse_the_production_store()
        leaked_env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        connection = await connect_admin(leaked_env)
        await connection.close()
        try:
            self._answer_info_for_ns_with(monkeypatch, _WELL_FORMED_EMPTY_NAMESPACE_ANSWER)
            reaped = tuple(await _surreal_harness.reap_minted_databases())
            assert reaped == (), f"a well-formed EMPTY namespace answer yielded removals: {reaped}"
            monkeypatch.undo()
            assert leaked_env.database in await _databases_in_the_test_namespace(), (
                "the leaked database vanished although the injected answer listed nothing — the "
                "injection did not reach the reaper's read"
            )
        finally:
            monkeypatch.undo()
            await drop_database(leaked_env)


class TestTheCensusOracleFailsClosed:
    """The contract's own store census (:func:`_databases_in_the_test_namespace`) is the ORACLE
    every "the leak is gone from the store" assertion reads. If it read an unreadable
    ``INFO FOR NS`` answer as an empty namespace, those assertions would pass vacuously — the
    same false clear :class:`TestTheReaperFailsLoudOnANamespaceAnswerItCannotRead` forbids in
    the reaper, inside the instrument (contract-486-r2 round 2c).

    Injected by replacing THIS module's ``run`` (the one the census calls) for ``INFO FOR NS``
    only; every other statement — the reader's mint, ``use()`` and drop — reaches the TEST store.
    """

    @pytest.mark.parametrize("answer", _UNREADABLE_NAMESPACE_ANSWERS)
    async def test_the_census_raises_on_an_unreadable_answer(
        self, monkeypatch: pytest.MonkeyPatch, answer: object
    ) -> None:
        _refuse_the_production_store()
        this_module = sys.modules[__name__]
        real_run = this_module.run

        async def run_answering_info_for_ns(
            connection: Any, statement: str, params: dict[str, Any] | None = None
        ) -> Any:
            if statement.strip().upper() == "INFO FOR NS":
                return answer
            return await real_run(connection, statement, params)

        monkeypatch.setattr(this_module, "run", run_answering_info_for_ns)
        with pytest.raises(SurrealStoreError, match=_CENSUS_NOUN):
            await _databases_in_the_test_namespace()

    async def test_CONTROL_the_census_returns_the_real_set_on_a_well_formed_answer(self) -> None:
        """CONTROL: unpatched, the census reads the live store's answer and returns the real set —
        a database this test minted and dialed is IN it — so the leg above fails closed on
        SHAPE, never on every answer."""
        _refuse_the_production_store()
        dialed_env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        connection = await connect_admin(dialed_env)
        await connection.close()
        try:
            present = await _databases_in_the_test_namespace()
            assert dialed_env.database in present, (
                f"the census does not list `{dialed_env.database}`, a database this test just "
                f"dialed — it reads a well-formed answer wrongly ({len(present)} names returned)"
            )
        finally:
            await drop_database(dialed_env)


# --------------------------------------------------------------------------------------------
# LEG 4b — RUNTIME: the session-end reap never costs pytest its verdict (contract-486-r3, #534)
# --------------------------------------------------------------------------------------------

# The URL path the harness dials (``DEFAULT_URL`` ends in it); an unreachable store keeps it so
# the ONLY difference from a healthy URL is the endpoint behind it.
_STORE_RPC_PATH = urllib.parse.urlsplit(surreal_url()).path

# The states of the TEST store a session may END in. "refused": a race-free dead port — a
# ``LoopbackPort`` bound and HELD but never listening (#466's helper; no specific port is ever
# bound). "silent": the same port LISTENING but never answering — a connect succeeds and the
# handshake then waits forever. Two states, because a fix keyed on the one exception the
# coldaudit happened to construct (``ConnectionRefusedError``) is the instance, not the class
# (CLAUDE.md, THE QUANTIFIER LAW): the property is "whatever the state of the TEST store".
_REFUSED_STORE = "refused"
_SILENT_STORE = "silent"
_UNREACHABLE_STORE_STATES = (_REFUSED_STORE, _SILENT_STORE)
# "muted" (round 3b, D2): the store ACCEPTS, completes the websocket handshake, then never answers
# a single request — the hang that sits past any connect-time timeout. Only constructible through
# the forwarder (it needs a real handshake), so it is a session-end state of cell (c) only.
_MUTED_STORE = "muted"
# Every state the store may be LOST into after a real open (cell c): refused, plus the two HANGS
# the lead's D2 ruling (2026-10-04) pins — "a never-ending session is worse than a failing one".
_LOST_STORE_STATES = (_REFUSED_STORE, _SILENT_STORE, _MUTED_STORE)

# A name-only session takes ~3-8s on this host (-n 0 / xdist start-up). A session that HANGS on a
# silent store is the failure; 90s bounds it well above any healthy run on a loaded box.
_UNREACHABLE_STORE_SESSION_TIMEOUT_SECONDS = 90
# Cell (c)'s outer bound: the build's own reap bound is NOT prescribed (D2), so this sits far above
# any plausible one (the SDK's websocket open timeout alone is 10s) — a session still running at
# 180s is HUNG, and that is RED.
_LOST_STORE_SESSION_TIMEOUT_SECONDS = 180

# The name-only inner session: one test mints a NAME and opens nothing — the shape of every
# fake-store test whose project slug the #486 patch converted to ``unique_database()``
# (``test_indexer`` / ``test_watcher`` / ``test_reconcile`` ``_config`` slugs, coldaudit-486 §7)
# — and one test mints nothing. Both pass; pytest must say so.
_NAME_ONLY_TEST_NAME = "test_mints_a_name_and_opens_nothing"
_NAME_ONLY_SESSION_PASSED = 2
_INNER_NAME_ONLY_SESSION = (
    _INNER_PREAMBLE
    + f"""

def {_NAME_ONLY_TEST_NAME}():
    # A NAME only — never dialed, so no database exists for it anywhere.
    assert unique_database()


def test_mints_nothing():
    assert True
"""
)

# The opened-then-lost inner session: the test OPENS a database on the live store (through the
# forwarder), never drops it, then makes the store unreachable before its session ends.
_STORE_LOST_TEST_NAME = "test_opens_a_database_then_loses_the_store"
_STORE_LOST_SESSION_PASSED = 1
_KILL_SWITCH_ENV = "LORE_486_STORE_KILL_SWITCH"
_KILLED_ACK_ENV = "LORE_486_STORE_KILLED_ACK"
_KILL_ACK_TIMEOUT_SECONDS = 10
_INNER_OPENS_THEN_LOSES_THE_STORE = (
    _INNER_PREAMBLE
    + f"""
import time
from pathlib import Path


async def {_STORE_LOST_TEST_NAME}():
    database = unique_database()
    _record(database)
    connection = await connect_admin(make_env(database=database, dim=PRODUCTION_DIM))
    await connection.close()
    # ...never drops it; then the TEST store becomes unreachable before this session ends.
    Path(os.environ["{_KILL_SWITCH_ENV}"]).touch()
    deadline = time.monotonic() + {_KILL_ACK_TIMEOUT_SECONDS}
    while not Path(os.environ["{_KILLED_ACK_ENV}"]).exists():
        assert time.monotonic() < deadline, "the store forwarder never acknowledged the kill"
        time.sleep(0.05)
"""
)

# The word the loud line must carry — the contract's term for the state, so an operator reading
# the tail can tell "the store was down" from "a test leaked" without reading code.
_UNREACHABLE_WORD = "unreachable"

# A raw Python traceback in the session's output — the shape #534 printed instead of a verdict.
_RAW_TRACEBACK_MARKER = "Traceback (most recent call last)"


def _passed_summary(count: int) -> re.Pattern[str]:
    """pytest's own summary count — ``2 passed`` — anywhere in the tail (``-q`` or ``=== … ===``)."""
    return re.compile(rf"\b{count} passed\b")


@contextlib.contextmanager
def _an_unreachable_store(state: str) -> Iterator[str]:
    """Yield a TEST-store URL in ``state`` (one of :data:`_UNREACHABLE_STORE_STATES`)."""
    with LoopbackPort() as held:
        if state == _SILENT_STORE:
            held.listen()  # accepts into the backlog; nobody ever answers
        yield f"ws://{held.host}:{held.port}{_STORE_RPC_PATH}"


class _KillableStoreForwarder:
    """A byte forwarder to the live TEST store that an inner test can KILL mid-session.

    Served FROM a held :class:`LoopbackPort` (#466: no specific port is ever bound). The inner
    test touches the kill-switch file; the forwarder drops every forwarded connection, enters its
    ``lost_state`` and touches the ack file. From that moment the ONLY TEST-store URL the inner
    process ever saw is unreachable — whatever the code under test resolves that URL from (env at
    reap time, a captured ``SurrealEnv``, a module constant). ``lost_state``:

    * ``refused`` — the listener is closed: a connect is refused.
    * ``silent`` — the listener stays open but nothing accepts: a connect completes into the
      kernel backlog and the handshake waits forever.
    * ``muted`` — connections are accepted and forwarded until the upstream's HTTP upgrade
      response has passed (the websocket handshake SUCCEEDS); every byte after it is swallowed,
      so the first request (sign-in) waits forever.

    Bound (stated): ``refused`` releases the ephemeral port; another process binding that exact
    port in the session's last seconds would turn "refused" into a foreign answer.
    """

    _POLL_SECONDS = 0.05
    _JOIN_SECONDS = 5
    _CHUNK_BYTES = 65536
    _HTTP_HEADER_END = b"\r\n\r\n"

    def __init__(self, kill_switch: Path, killed_ack: Path, *, lost_state: str = _REFUSED_STORE) -> None:
        assert lost_state in _LOST_STORE_STATES, lost_state
        upstream = urllib.parse.urlsplit(surreal_url())
        self._upstream = (upstream.hostname or "127.0.0.1", upstream.port or 80)
        self._kill_switch = kill_switch
        self._killed_ack = killed_ack
        self._lost_state = lost_state
        self._held = LoopbackPort()
        self._held.listen()
        self._held.socket.settimeout(self._POLL_SECONDS)
        self._connections: list[socket.socket] = []
        self._lock = threading.Lock()
        self._lost = False
        self._closed = threading.Event()
        self._acceptor = threading.Thread(target=self._serve_until_closed, daemon=True)
        self.url = f"ws://{self._held.host}:{self._held.port}{upstream.path}"

    def __enter__(self) -> _KillableStoreForwarder:
        self._acceptor.start()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self._closed.set()
        self._acceptor.join(timeout=self._JOIN_SECONDS)
        with self._lock:
            self._held.close()
            self._drop_connections()
        self._killed_ack.touch()

    def _serve_until_closed(self) -> None:
        while not self._closed.is_set():
            if not self._lost and self._kill_switch.exists():
                self._lose_the_store()
            if self._lost and self._lost_state != _MUTED_STORE:
                if self._closed.wait(self._POLL_SECONDS):
                    return
                continue
            try:
                client, _ = self._held.socket.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            upstream = socket.create_connection(self._upstream)
            with self._lock:
                self._connections += [client, upstream]
            muted = self._lost
            threading.Thread(target=self._pump, args=(client, upstream, False), daemon=True).start()
            threading.Thread(target=self._pump, args=(upstream, client, muted), daemon=True).start()

    def _lose_the_store(self) -> None:
        with self._lock:
            self._lost = True
            if self._lost_state == _REFUSED_STORE:
                self._held.close()
            self._drop_connections()
        self._killed_ack.touch()

    def _drop_connections(self) -> None:
        for connection in self._connections:
            with contextlib.suppress(OSError):
                connection.shutdown(socket.SHUT_RDWR)
            connection.close()
        self._connections.clear()

    @classmethod
    def _pump(cls, source: socket.socket, sink: socket.socket, muted: bool) -> None:
        handshake = b""
        with contextlib.suppress(OSError):
            while chunk := source.recv(cls._CHUNK_BYTES):
                if not muted:
                    sink.sendall(chunk)
                elif cls._HTTP_HEADER_END not in handshake:
                    # Forward the upgrade response, then swallow everything after it.
                    handshake += chunk
                    header, found, _ = handshake.partition(cls._HTTP_HEADER_END)
                    forwarded = len(handshake) - len(chunk)
                    passed = (header + found)[forwarded:] if found else chunk
                    sink.sendall(passed)
        for end in (source, sink):
            with contextlib.suppress(OSError):
                end.shutdown(socket.SHUT_RDWR)


def _run_bounded(
    tmp_path: Path,
    test_source: str,
    *,
    workers: int | None,
    store_url: str,
    timeout_seconds: float = _UNREACHABLE_STORE_SESSION_TIMEOUT_SECONDS,
    created_sink: list[str] | None = None,
    **extra: str,
) -> _InnerSession:
    """An inner session against ``store_url``; a HANG is a named failure, never an outer crash.

    Whatever the session recorded is appended to ``created_sink`` on BOTH paths, so the caller's
    ``finally`` can remove a hung session's databases too.
    """
    try:
        session = _run_inner_session(
            tmp_path,
            test_source,
            workers=workers,
            extra_environment={"LORE_TEST_SURREAL_URL": store_url, **extra},
            timeout_seconds=timeout_seconds,
        )
    except _InnerSessionHung as hung:
        if created_sink is not None:
            created_sink.extend(hung.created)
        pytest.fail(
            f"the inner session against {store_url} did not END within {hung.timeout_seconds}s — a "
            f"session-end step is waiting on a TEST store that will never answer. A session must end, "
            f"with pytest's verdict, whatever the store's state (D2: a never-ending session is worse "
            f"than a failing one).\n--- output so far ---\n{hung.output[-4000:]}"
        )
    if created_sink is not None:
        created_sink.extend(session.created)
    return session


_WORKER_MODES = [pytest.param(None, id="n0"), pytest.param(_XDIST_WORKERS, id=f"xdist-n{_XDIST_WORKERS}")]


class TestTheSessionEndReapNeverCostsPytestItsVerdict:
    """#534, lifted (coldaudit-486 §7): ∀ pytest session whose tests pass and which OPENED no test
    database, the session ends with pytest's own verdict (rc 0) and summary (``N passed``), with
    no raw traceback — WHATEVER the state of the TEST store (∀ state in
    :data:`_UNREACHABLE_STORE_STATES`, plus the live control). And a session that DID open a
    database, with the store unreachable at session end, says so LOUDLY: a non-zero rc, a line
    naming the store as unreachable and the database it could not reap, pytest's summary intact,
    no raw traceback.

    Pins OUTCOMES only — rc, pytest's summary line, the loud line, the absence of a traceback.
    Not the mechanism (which names to reap, how a failed connect is caught).

    Why it matters: a crash after green tests prints NO passed-count, which is the exact tail
    CLAUDE.md teaches agents to distrust ("a green claim requires a passed-COUNT"); every
    targeted store-free run on a host without the TEST store (packet 01a's in-image run) hit it.
    """

    @pytest.mark.parametrize("workers", _WORKER_MODES)
    @pytest.mark.parametrize("store_state", _UNREACHABLE_STORE_STATES)
    def test_a_name_only_session_keeps_pytests_verdict_with_the_store_unreachable(
        self, tmp_path: Path, store_state: str, workers: int | None
    ) -> None:
        """RED on the #486 working tree as of contract-486-r3 (2026-10-04, ``b8c3f7b``): the
        session-end reap dials the store for a name nobody opened, raises out of
        ``pytest_sessionfinish`` — rc 1, a raw traceback, no ``passed`` line (coldaudit-486 §7)."""
        with _an_unreachable_store(store_state) as store_url:
            session = _run_bounded(tmp_path, _INNER_NAME_ONLY_SESSION, workers=workers, store_url=store_url)
        _assert_pytest_kept_its_verdict(session, passed=_NAME_ONLY_SESSION_PASSED, store=store_state)

    @pytest.mark.parametrize("workers", _WORKER_MODES)
    def test_CONTROL_a_name_only_session_keeps_pytests_verdict_with_the_store_live(
        self, tmp_path: Path, workers: int | None
    ) -> None:
        """CONTROL (GREEN on the #486 working tree): the identical session against the live TEST
        store passes — so the leg above fails on the store's STATE, never on the session's shape."""
        _refuse_the_production_store()
        session = _run_bounded(tmp_path, _INNER_NAME_ONLY_SESSION, workers=workers, store_url=surreal_url())
        _assert_pytest_kept_its_verdict(session, passed=_NAME_ONLY_SESSION_PASSED, store="live")

    @pytest.mark.parametrize("workers", _WORKER_MODES)
    @pytest.mark.parametrize("lost_state", _LOST_STORE_STATES)
    async def test_an_opened_database_with_the_store_lost_at_session_end_is_reported_loudly(
        self, tmp_path: Path, lost_state: str, workers: int | None
    ) -> None:
        """RED on the #486 working tree as of contract-486-r3 (2026-10-04): the reap's connect
        error escapes ``pytest_sessionfinish`` as a raw traceback (``-n 0``) — and under xdist the
        worker's crash is SWALLOWED: rc 0, ``1 passed``, the opened database never reaped (a false
        clear). Nothing names the store as unreachable in either mode.

        Construction: the inner session's TEST store is a forwarder to the live store; the test
        opens a database through it, never drops it, then kills the forwarder and waits for the
        ack — so the session ENDS with the store unreachable after a real open.

        D2 (lead ruling, 2026-10-04): ∀ lost state — refused, AND the two hangs (``silent``: no
        accept; ``muted``: handshake completes, then nothing) — the reap COMPLETES in bounded time
        and the same loud line follows. The bound's value and mechanism are the build's; a session
        still running at :data:`_LOST_STORE_SESSION_TIMEOUT_SECONDS` is RED."""
        _refuse_the_production_store()
        kill_switch = tmp_path / "store.kill"
        killed_ack = tmp_path / "store.killed"
        created: list[str] = []
        try:
            with _KillableStoreForwarder(kill_switch, killed_ack, lost_state=lost_state) as forwarder:
                session = _run_bounded(
                    tmp_path,
                    _INNER_OPENS_THEN_LOSES_THE_STORE,
                    workers=workers,
                    store_url=forwarder.url,
                    timeout_seconds=_LOST_STORE_SESSION_TIMEOUT_SECONDS,
                    created_sink=created,
                    **{_KILL_SWITCH_ENV: str(kill_switch), _KILLED_ACK_ENV: str(killed_ack)},
                )
            assert len(session.created) == 1 and killed_ack.exists(), (
                f"CONSTRUCTION failed (not a verdict on the build): the inner test never opened a "
                f"database or never lost the store.\n{session.describe()}"
            )
            (opened,) = session.created
            assert _RAW_TRACEBACK_MARKER not in session.output, (
                f"the session-end reap crashed with a RAW traceback when the TEST store became "
                f"unreachable. Report it as a named line instead (#534).\n{session.describe()}"
            )
            assert session.returncode != 0, (
                f"the session PASSED although `{opened}` — opened and never dropped — could not be "
                f"reaped: the store being down hid a leak.\n{session.describe()}"
            )
            loud_lines = [
                line
                for line in session.output.splitlines()
                if opened in line and _UNREACHABLE_WORD in line.lower()
            ]
            assert loud_lines, (
                f"no line names BOTH the database that could not be reaped (`{opened}`) and the store "
                f"as {_UNREACHABLE_WORD!r}. An operator reading the tail must be able to tell "
                f"'the store was down' from 'a test leaked'"
                f"{' (under xdist the WORKER must get this back to the controller)' if workers else ''}."
                f"\n{session.describe()}"
            )
            assert _passed_summary(_STORE_LOST_SESSION_PASSED).search(session.output), (
                f"pytest's own summary (`{_STORE_LOST_SESSION_PASSED} passed`) is missing: the loud "
                f"line must sit BESIDE pytest's verdict, never replace it.\n{session.describe()}"
            )
        finally:
            await _remove_if_present(*created)


def _assert_pytest_kept_its_verdict(session: _InnerSession, *, passed: int, store: str) -> None:
    """The name-only session's outcome: pytest's verdict, its summary, and no raw traceback."""
    assert session.created == (), f"the name-only inner session dialed a store: {session.describe()}"
    assert _RAW_TRACEBACK_MARKER not in session.output, (
        f"a session whose tests passed and which opened NO database crashed with a raw traceback "
        f"at session end (TEST store: {store}) — #534.\n{session.describe()}"
    )
    assert session.returncode == 0, (
        f"a session whose tests passed and which opened NO database exited "
        f"{session.returncode} (TEST store: {store}). Nothing was opened, so nothing can have "
        f"leaked — the store's state is not this session's verdict.\n{session.describe()}"
    )
    assert _passed_summary(passed).search(session.output), (
        f"pytest's own summary (`{passed} passed`) is missing (TEST store: {store}) — a tail with no "
        f"passed-count is the one CLAUDE.md teaches agents to distrust.\n{session.describe()}"
    )


# --------------------------------------------------------------------------------------------
# LEG 5 — the retired false claim
# --------------------------------------------------------------------------------------------

# The sentence's distinctive phrase. A RETIRED-CLAIM pin (lint grade, keyed on a phrase): the
# mechanism it describes — reaping another process's orphan when its PID is reused — was never
# built, and building it is decision D2 (the pid slot is not unique across pid namespaces: the
# in-image conformance run, packet 01a, runs the suite in a container).
_RETIRED_CLAIM = "reused PID"


class TestTheHarnessDocstringClaimsNoReaperItLacks:
    def test_the_harness_no_longer_claims_pid_reuse_reaps_orphans(self) -> None:
        """RED at HEAD: the module docstring says "a reused PID later harmlessly reaps any prior
        orphan" — no code does that (contract-486 report §M3); 454 dead-pid orphans (2026-09-26) say so."""
        docstring = _surreal_harness.__doc__ or ""
        assert _RETIRED_CLAIM not in docstring, (
            f"`_surreal_harness`'s docstring still claims orphan reaping by PID reuse ({_RETIRED_CLAIM!r}). "
            f"No mechanism does that. State what the harness actually guarantees (session-end reap of "
            f"its own mints) and what it does not (a killed session's databases)."
        )
